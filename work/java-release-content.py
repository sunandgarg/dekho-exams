"""Add checked Java lessons and expand existing search-intent coverage."""
import copy,datetime,html,json,pathlib,re,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT.parent.parent/'outputs'
entries=json.loads((ROOT/'work/java-release/baseline.json').read_text());lookup={e['path']:e for e in entries};added=[];expanded=[]
stamp=datetime.datetime.now(datetime.UTC).isoformat();sections={e['subject']:e['path'] for e in entries if e['type']=='subject' and e['path'].startswith('java/')}
def p(text):return '<p>'+html.escape(text)+'</p>'
def c(text,lang='java'):return '<pre><code class="language-'+lang+'">'+html.escape(text.strip(),quote=False)+'</code></pre>'
def put(slug,title,definition,parts,source,output,cost,mistakes,related,subject='java-advanced',release=8):
 path='java/'+slug;body=p(definition)+p('This program targets Java '+str(release)+' without preview flags. Use a full JDK for compiler-based examples.')
 for heading,paragraphs in parts:body+='<h2>'+html.escape(heading)+'</h2>'+''.join(p(t) for t in paragraphs)
 body+='<h2>Working program</h2>'+c(source)+'<h3>Output</h3>'+c(output,'text')+'<h2>Costs and boundaries</h2>'+''.join(p(t) for t in cost)+'<h3>Common Mistakes</h3><ul>'+''.join('<li>'+html.escape(t)+'</li>' for t in mistakes)+'</ul><h2>Read next</h2><p>'+', '.join('<a href="/java/'+s+'">'+html.escape(t)+'</a>' for s,t in related)+'.</p>'
 e=copy.deepcopy(lookup['java/casts']);e.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),path=path,title=title,summary=definition,body=body,subject=subject,tags=['java',slug],difficulty='Intermediate',featured=False,sort_order=200+len(added),published_at=stamp,updated_at=stamp,status='published')
 e['data']={'subject_root':'java/java','section_path':sections[subject],'content_format':'html','kind':'tutorial','java_release':release,'java_version':str(release)+'+','reading_minutes':max(4,round(len(re.sub('<[^>]*>',' ',body).split())/150)),'author_path':'authors/aitrove-editorial','download_path':'/downloads/aitrove-java-source-kit.zip','related':[{'path':'java/'+s,'title':t} for s,t in related]}
 entries.append(e);lookup[path]=e;added.append(path)

put('foreign-memory','Java foreign memory: arena lifetime, bounds and thread ownership',
'A memory segment is a bounded view of memory; an arena owns the lifetime and access policy of native segments allocated through it.',
[('Make allocation lifetime explicit',[
'An import operation needs a small native block for a length and a checksum. Its allocation belongs to that operation. A confined arena gives one thread access and permits deterministic release when the operation exits. Keeping a segment reference after closing the arena does not keep its allocation usable.',
'The Foreign Function and Memory API became final in Java 22. This lesson tests its Java 25 form. Ordinary arena allocation and Java-layout reads do not require preview flags; native function calls have separate linkage and access requirements that this program does not exercise. Off-heap allocation is still memory usage, even though the segment wrapper itself is a heap object.'
]),('Check layout and ownership independently',[
'An integer layout determines size, alignment and byte order. It is not a promise that any offset is valid. The program checks a valid aligned read, rejects an offset at the end of the block, and then tries reading after close. These are different failures: the first violates spatial bounds, the second violates lifetime.',
'A shared arena changes who may access a segment. It does not make every compound update atomic. A parser that writes a length and checksum separately still needs a publication rule before another thread consumes the pair. Ownership and synchronization answer different questions.'
])],'''import java.lang.foreign.Arena;
import java.lang.foreign.MemorySegment;
import java.lang.foreign.ValueLayout;
public class NativeReceiptBlock {
    public static void main(String[] args) {
        MemorySegment receipt;
        try (Arena arena = Arena.ofConfined()) {
            receipt = arena.allocate(8, 4);
            receipt.set(ValueLayout.JAVA_INT, 0, 17);
            receipt.set(ValueLayout.JAVA_INT, 4, 29);
            System.out.println(receipt.get(ValueLayout.JAVA_INT, 0));
            try { receipt.get(ValueLayout.JAVA_INT, 8); }
            catch (IndexOutOfBoundsException rejected) { System.out.println("bounds rejected"); }
        }
        try { receipt.get(ValueLayout.JAVA_INT, 0); }
        catch (IllegalStateException rejected) { System.out.println("closed rejected"); }
    }
}''','17\nbounds rejected\nclosed rejected',
['A fixed-layout access is constant work; copying a segment scales with the bytes copied. This example allocates eight native bytes plus Java wrappers. It demonstrates bounded local allocation, not native-library safety or faster parsing. A global arena has a different lifetime and is inappropriate when deterministic release is part of the request contract.'],
['Do not use a segment after its arena closes.','Do not equate shared access with atomic multi-field publication.','An offset must satisfy both bounds and layout alignment.'],[('file-channels','Buffer bounds'),('jvm-memory','Heap ownership'),('atomics','Publication rules')],release=25)

put('varhandles','Java VarHandle: atomic transitions and explicit access modes',
'A VarHandle provides typed access to a variable with selected memory-order and atomic-update operations; its access mode is part of the operation contract.',
[('A transition is narrower than a workflow',[
'A receipt begins unclaimed. One worker attempts to change its state from zero to one. compareAndSet makes that conditional transition indivisible for the selected field. A second claim against zero fails after the first succeeds, so the caller can reject duplicate work without a separate read-then-write race.',
'This is not an entire processing transaction. After the claim, a network operation can fail or the process can stop. The application still needs a recovery state and an idempotent external operation. Atomic ownership of one field does not supply either of those.'
]),('Choose the access mode deliberately',[
'Plain, opaque, acquire/release and volatile modes offer different ordering rules. Reading a state with acquire requires an appropriate publication protocol; it does not turn unrelated unsynchronized writes into a valid design by naming the mode. The program uses compareAndSet and getVolatile to show a simple atomic state change without claiming to prove every weaker-mode protocol.',
'A handle includes receiver and value types. For an instance integer field, passing a different receiver or a long value can produce a type error at invocation. The lookup also follows access-control rules. Resolve the handle once and keep the field contract visible near the state definition.'
])],'''import java.lang.invoke.MethodHandles;
import java.lang.invoke.VarHandle;
public class ClaimedReceiptState {
    private volatile int state;
    private static final VarHandle STATE;
    static {
        try { STATE = MethodHandles.lookup().findVarHandle(ClaimedReceiptState.class, "state", int.class); }
        catch (ReflectiveOperationException failure) { throw new ExceptionInInitializerError(failure); }
    }
    public static void main(String[] args) {
        ClaimedReceiptState receipt = new ClaimedReceiptState();
        System.out.println(STATE.compareAndSet(receipt, 0, 1));
        System.out.println(STATE.compareAndSet(receipt, 0, 1));
        System.out.println((int) STATE.getVolatile(receipt));
    }
}''','true\nfalse\n1',
['The example performs three bounded field operations. Under contention, the hardware and runtime determine retry and ordering costs; a CAS-based retry loop can consume work without making a system-wide latency guarantee. Use this primitive when its ownership protocol is simpler to explain than an ordinary lock, not merely because it avoids the word synchronized.'],
['Do not use plain access when the publication rule requires ordered access.','Weak CAS variants can fail without an observed value change.','One CAS does not commit several unrelated structures.'],[('atomics','Java memory model'),('atomics','Atomic values'),('multi-index-invariants','Multi-index ownership')],release=11)

put('service-discovery','Java ServiceLoader: provider configuration and lazy discovery',
'ServiceLoader discovers implementations of a service interface from provider configuration visible to a chosen class loader.',
[('Registration belongs to the provider package',[
'A report exporter depends on an interface rather than a hard-coded implementation. On the class path, the provider lists its binary class name in META-INF/services followed by the interface binary name. A named module instead has uses and provides declarations; mixing the two layouts without checking deployment can produce an empty discovery result.',
'This fixture creates only the provider configuration in a temporary directory. The implementation class is already compiled with the program. A child URLClassLoader exposes the resource and delegates the implementation class to its parent, so the contract is tested without downloading or loading an unknown plugin.'
]),('Iteration can fail',[
'Provider lookup and instantiation happen lazily. A configured class can be absent, incompatible, or unable to construct, and iteration can throw ServiceConfigurationError. Do not treat the first successfully returned provider as proof that the rest of the file is valid.',
'The fixture finds one exporter and calls its operation. Discovery does not register a priority or select the best provider for a workload. If selection depends on format, explicitly inspect a capability contract and reject ambiguous matches. ServiceLoader instances also need their own concurrency ownership; they are not general-purpose thread-safe registries.'
])],'''import java.net.URL;
import java.net.URLClassLoader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ServiceLoader;
public class ReceiptProviderDiscovery {
    public interface Exporter { String format(); }
    public static class TextExporter implements Exporter {
        public TextExporter() {}
        public String format() { return "receipt-text"; }
    }
    public static void main(String[] args) throws Exception {
        Path root = Files.createTempDirectory("receipt-provider-");
        Path services = Files.createDirectories(root.resolve("META-INF/services"));
        Path config = services.resolve(Exporter.class.getName());
        try {
            Files.write(config, (TextExporter.class.getName()+"\\n").getBytes(StandardCharsets.UTF_8));
            try (URLClassLoader loader = new URLClassLoader(new URL[]{root.toUri().toURL()}, ReceiptProviderDiscovery.class.getClassLoader())) {
                int count=0;
                for (Exporter exporter : ServiceLoader.load(Exporter.class, loader)) {
                    System.out.println(exporter.format()); count++;
                }
                System.out.println("providers="+count);
            }
        } finally {
            Files.deleteIfExists(config); Files.deleteIfExists(services);
            Files.deleteIfExists(root.resolve("META-INF")); Files.deleteIfExists(root);
        }
    }
}''','receipt-text\nproviders=1',
['Resource discovery and provider construction depend on the number of registrations and provider behavior. The program retains one provider and closes its own class loader. Closing a loader does not interrupt running plugin threads or provide a security boundary. Loading untrusted code requires a separate isolation design.'],
['Use binary names in class-path provider files, including a dollar sign for nested types.','Do not assume provider iteration order expresses application priority.','Do not suppress every ServiceConfigurationError and quietly run with a partial provider set.'],[('class-loaders','Class loader ownership'),('java-modules','Named modules'),('interfaces','Interface contracts')])

put('resource-bundles','Java ResourceBundle: locale fallback and missing message keys',
'A ResourceBundle maps stable message keys to locale-specific values and can obtain missing values from a parent bundle.',
[('Keep identifiers separate from labels',[
'A receipt screen stores a status identifier but displays a translated label. Changing the label must not change its stored key or business comparison. The base bundle supplies common keys; the French bundle overrides the ready label and inherits the unknown label from the parent.',
'This program uses class-based ListResourceBundle types compiled in one file. It deliberately selects the root locale and Locale.FRENCH rather than reading the machine default. The result is a reproducible fallback test, not a statement that every application should force French or root labels.'
]),('Missing is a visible failure',[
'An absent key throws MissingResourceException even if the bundle itself loaded successfully. That failure should be caught at the display boundary or prevented by a completeness check across supported locales. Returning the key as the label everywhere can hide translation regressions in production.',
'Bundle discovery has caching and fallback behavior. Hot-editing a resource file does not by itself prove that a running process will reload it. Properties-file encoding also changed across Java releases; a Java 8 deployment needs an explicit encoding review. This fixture avoids that issue by using class-based string values.'
])],'''import java.util.ListResourceBundle;
import java.util.Locale;
import java.util.MissingResourceException;
import java.util.ResourceBundle;
public class ReceiptMessages {
    public static class Labels extends ListResourceBundle {
        protected Object[][] getContents() { return new Object[][]{{"ready", "Ready"}, {"unknown", "Unknown"}}; }
    }
    public static class Labels_fr extends ListResourceBundle {
        protected Object[][] getContents() { return new Object[][]{{"ready", "Pret"}}; }
    }
    public static void main(String[] args) {
        ResourceBundle root = ResourceBundle.getBundle(Labels.class.getName(), Locale.ROOT);
        ResourceBundle french = ResourceBundle.getBundle(Labels.class.getName(), Locale.FRENCH);
        System.out.println(root.getString("ready"));
        System.out.println(french.getString("ready"));
        System.out.println(french.getString("unknown"));
        try { french.getString("deleted"); }
        catch (MissingResourceException rejected) { System.out.println("missing rejected"); }
    }
}''','Ready\nPret\nUnknown\nmissing rejected',
['This bounded fixture has three stored labels and one inherited lookup. A larger deployment pays for resource loading, cached bundle state and fallback lookups; missing-key handling can also add exception costs. Translation completeness and text layout are separate checks. Test labels that grow longer instead of assuming every locale fits the original button.'],
['Do not use translated labels as stored identifiers.','Loading a bundle does not establish that every requested key exists.','Do not assume the machine default locale is reproducible across deployments.'],[('collation-policy','Locale-aware ordering'),('unicode-encoding','Text encoding'),('strings','String equality')],subject='java')

put('properties-validation','Java Properties: validate configuration before changing application state',
'Properties loads textual key-value configuration; the application must still validate required keys, value types and allowed ranges.',
[('Loading is not validation',[
'A receipt importer needs a bounded batch size and an output mode. Properties can parse both lines, but it has no knowledge that batch size zero is invalid. Parse into an immutable application configuration only after checking every required value, rather than changing a running service one property at a time.',
'The fixture uses StringReader so its input is already decoded text. The byte-stream overload has a different encoding contract. Duplicate property keys replace earlier values during loading; rejecting duplicate keys requires an input parser that preserves that evidence before Properties discards it.'
]),('Reject ambiguity at the boundary',[
'The batch size must be between one and five hundred. The mode must be one of the declared strings. Unknown fields are rejected because a misspelled option should not quietly act like a default. Numeric overflow and nonnumeric input fail the whole configuration operation.',
'Properties also inherits operations that accept arbitrary objects. Inserting non-string keys or values through put can break assumptions made by getProperty and storage methods. Keep the mutable Properties instance inside the loading boundary, then pass typed fields to the importer.'
])],'''import java.io.StringReader;
import java.util.Properties;
public class ValidatedImportConfig {
    static int batch(String text) throws Exception {
        Properties values = new Properties(); values.load(new StringReader(text));
        for (String key : values.stringPropertyNames())
            if (!key.equals("batch") && !key.equals("mode")) throw new IllegalArgumentException("Unknown setting");
        String raw = values.getProperty("batch");
        if (raw == null) throw new IllegalArgumentException("Missing batch");
        int size = Integer.parseInt(raw);
        if (size < 1 || size > 500) throw new IllegalArgumentException("Batch outside bounds");
        String mode = values.getProperty("mode");
        if (!"summary".equals(mode) && !"detail".equals(mode)) throw new IllegalArgumentException("Invalid mode");
        return size;
    }
    public static void main(String[] args) throws Exception {
        System.out.println(batch("batch=80\\nmode=summary"));
        try { batch("batch=0\\nmode=detail"); }
        catch (IllegalArgumentException rejected) { System.out.println("range rejected"); }
        try { batch("batch=80\\nmode=summary\\nmod=detail"); }
        catch (IllegalArgumentException rejected) { System.out.println("unknown rejected"); }
    }
}''','80\nrange rejected\nunknown rejected',
['Loading requires work proportional to the input size, plus retained keys and values. This fixture bounds the permitted batch value but does not bound the size of an arbitrary input stream. Production loading needs a byte or character budget as well. Keep credentials out of diagnostic dumps of configuration maps.'],
['Do not treat a successful load as proof of valid application values.','Do not silently ignore misspelled configuration keys.','Properties cannot recover duplicate-key evidence after replacement.'],[('console-input','Validation exercises'),('files','Text file boundaries'),('immutable-collections','Immutable data')])

put('swing-workers','Java SwingWorker: background work and event-thread publication',
'SwingWorker runs background work separately from the Swing event dispatch thread and delivers completion callbacks to the event thread.',
[('The UI thread is an ownership boundary',[
'A desktop receipt viewer should not parse a large import inside a button listener. That listener runs on the event dispatch thread. Blocking it prevents repainting and input handling, so the window can look frozen even when the parser is making progress.',
'The background task returns a result rather than modifying a Swing label directly. done obtains the completed result and updates the model on the event thread. The fixture uses an atomic reference only to transfer its observed label back to the test thread; the Swing label itself remains event-thread-owned.'
]),('Completion and waiting are different operations',[
'Calling get on a still-running worker from the event thread recreates the blocking problem. done is different because the task has already completed; failure still needs handling because get can throw ExecutionException or InterruptedException. Preserve interruption when catching the latter.',
'This headless program verifies background execution, event-thread completion and the label value without opening a window. It is a Swing threading fixture, not a full desktop application. A real application still needs cancellation, input disabling and an explicit failure display.'
])],'''import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import javax.swing.JLabel;
import javax.swing.SwingUtilities;
import javax.swing.SwingWorker;
public class ReceiptViewerWorker {
    public static void main(String[] args) throws Exception {
        AtomicReference<String> observed = new AtomicReference<>();
        CountDownLatch completed = new CountDownLatch(1);
        SwingUtilities.invokeAndWait(() -> {
            JLabel label = new JLabel("Waiting");
            SwingWorker<Integer, Void> worker = new SwingWorker<Integer, Void>() {
                protected Integer doInBackground() {
                    if (SwingUtilities.isEventDispatchThread()) throw new IllegalStateException("Work on UI thread");
                    return 6;
                }
                protected void done() {
                    try {
                        if (!SwingUtilities.isEventDispatchThread()) throw new IllegalStateException("Completion off UI thread");
                        label.setText("Imported="+get()); observed.set(label.getText());
                    } catch (InterruptedException failure) { Thread.currentThread().interrupt(); observed.set("interrupted"); }
                    catch (Exception failure) { observed.set("failed"); }
                    finally { completed.countDown(); }
                }
            };
            worker.execute();
        });
        if (!completed.await(5, TimeUnit.SECONDS)) throw new IllegalStateException("Completion deadline");
        System.out.println(observed.get());
    }
}''','Imported=6',
['The fixture does constant background work and retains one label and one worker. Application cost follows the actual parser and its result, not SwingWorker itself. Publishing thousands of small UI updates can overwhelm the event queue; coalesce progress instead of repainting for every row. A timeout in this test bounds its wait, not the latency of every desktop operation.'],
['Do not mutate Swing components from doInBackground.','Do not wait for unfinished work on the event thread.','Cancellation needs cooperation from the background operation.'],[('cancellation','Cancellation and waiting'),('executors','Executor boundaries'),('locks','Shared state')],release=8)

put('java2d-images','Java BufferedImage: deterministic raster output without a window',
'BufferedImage stores a raster and a color model so Java code can render and inspect image pixels without displaying a desktop window.',
[('Pixel checks are narrower than screenshots',[
'A receipt preview can be generated on a server where no display is available. The program creates a small ARGB image and paints a solid status area. It tests exact pixels in that rectangle rather than relying on a screenshot tool or a font installed on the machine.',
'Text rendering has extra dependencies: font choice, metrics, antialiasing and platform rasterization can change its pixels. This program deliberately contains no text, so its acceptance check establishes geometry and color only. A production receipt renderer needs a separate layout and text test.'
]),('Release the drawing context',[
'Graphics2D holds rendering state and must be disposed after the painting operation. The image stays usable after disposal; disposing the context does not erase its pixels. A try/finally block keeps that lifecycle clear when drawing fails.',
'The program writes a PNG to memory, decodes it and checks both a painted pixel and an untouched transparent pixel. It rejects a missing encoder or failed decode rather than treating an empty byte array as a successful image. The fixture encodes its own image; it does not parse an unbounded user upload.'
])],'''import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import javax.imageio.ImageIO;
public class ReceiptStatusRaster {
    public static void main(String[] args) throws Exception {
        BufferedImage image = new BufferedImage(40, 20, BufferedImage.TYPE_INT_ARGB);
        Graphics2D paint = image.createGraphics();
        try { paint.setColor(new Color(20, 70, 100)); paint.fillRect(4, 3, 8, 6); }
        finally { paint.dispose(); }
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        if (!ImageIO.write(image, "png", bytes)) throw new IllegalStateException("Missing PNG encoder");
        BufferedImage restored = ImageIO.read(new ByteArrayInputStream(bytes.toByteArray()));
        if (restored == null) throw new IllegalStateException("PNG decode failed");
        System.out.println(restored.getWidth()+"x"+restored.getHeight());
        System.out.println(restored.getRGB(4, 3) == new Color(20, 70, 100).getRGB());
        System.out.println(restored.getRGB(0, 0) == 0);
    }
}''','40x20\ntrue\ntrue',
['An ARGB raster needs storage proportional to width times height, with additional encoder buffers. Validate dimensions before multiplication and allocation when dimensions come from outside the application. Compressed file size is not a reliable bound on decoded memory. This example owns only an 800-pixel image and does not establish upload safety or typography fidelity.'],
['Dispose every created Graphics2D context.','Do not infer decoded memory size from compressed byte count.','Pixel assertions for flat geometry do not verify text layout across platforms.'],[('operators','Bounded arithmetic'),('try-with-resources','Resource lifetime'),('file-exercises','I/O rejection exercises')],subject='java-examples')

put('annotation-processing','Java annotation processing: reject invalid declarations during compilation',
'An annotation processor inspects compiler elements during processing rounds and can reject a declaration with a compile-time diagnostic.',
[('A marker needs a consumer',[
'A source annotation records an endpoint path, but the annotation itself does not validate that path. The processor reads the annotated type and emits an error when the value does not begin with a slash. That turns a declaration rule into a compiler check rather than a comment that reviewers must remember.',
'The program supplies the processor explicitly through the JavaCompiler API. It runs processing only against in-memory source units. No provider discovery or generated-source packaging is implied; command-line builds need their own processor registration and processor-path configuration.'
]),('Respect processing rounds and diagnostics',[
'A processor can be called over multiple rounds. It should claim only annotation types that it owns, and avoid generating the same file repeatedly. This fixture does not generate files. It rejects one annotated type and accepts another, then checks the compiler task result instead of searching human-formatted diagnostic text.',
'Processing code runs with the build process privileges. A downloaded processor is executable build-time code, even if its dependency is described as tooling. Keep processor versions and inputs reviewable. A full JDK is required here because ToolProvider may not supply a compiler in a reduced runtime.'
])],'''import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
import java.net.URI;
import java.util.Collections;
import java.util.Set;
import javax.annotation.processing.AbstractProcessor;
import javax.annotation.processing.RoundEnvironment;
import javax.lang.model.SourceVersion;
import javax.lang.model.element.TypeElement;
import javax.tools.Diagnostic;
import javax.tools.DiagnosticCollector;
import javax.tools.JavaCompiler;
import javax.tools.JavaFileObject;
import javax.tools.SimpleJavaFileObject;
import javax.tools.StandardJavaFileManager;
import javax.tools.ToolProvider;
public class CompilerRouteAudit {
    @Target(ElementType.TYPE) @Retention(RetentionPolicy.SOURCE)
    public @interface Route { String value(); }
    static class RouteProcessor extends AbstractProcessor {
        public Set<String> getSupportedAnnotationTypes() { return Collections.singleton(Route.class.getCanonicalName()); }
        public SourceVersion getSupportedSourceVersion() { return SourceVersion.latestSupported(); }
        public boolean process(Set<? extends TypeElement> annotations, RoundEnvironment round) {
            for (javax.lang.model.element.Element endpoint : round.getElementsAnnotatedWith(Route.class))
                if (!endpoint.getAnnotation(Route.class).value().startsWith("/"))
                    processingEnv.getMessager().printMessage(Diagnostic.Kind.ERROR, "Route must start with a slash", endpoint);
            return true;
        }
    }
    static boolean check(String path) throws Exception {
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) throw new IllegalStateException("Full JDK required");
        String text = "@CompilerRouteAudit.Route(\\\""+path+"\\\") class ReceiptEndpoint {}";
        JavaFileObject unit = new SimpleJavaFileObject(URI.create("string:///ReceiptEndpoint.java"), JavaFileObject.Kind.SOURCE) {
            public CharSequence getCharContent(boolean ignoreErrors) { return text; }
        };
        DiagnosticCollector<JavaFileObject> diagnostics = new DiagnosticCollector<>();
        try (StandardJavaFileManager files = compiler.getStandardFileManager(diagnostics, null, null)) {
            JavaCompiler.CompilationTask task = compiler.getTask(null, files, diagnostics,
                java.util.Arrays.asList("-proc:only", "-classpath", System.getProperty("java.class.path")),
                null, Collections.singletonList(unit));
            task.setProcessors(Collections.singletonList(new RouteProcessor()));
            return task.call();
        }
    }
    public static void main(String[] args) throws Exception {
        System.out.println(check("/receipts")); System.out.println(check("receipts"));
    }
}''','true\nfalse',
['Processing work follows the number of compiler elements visited and any generated output. This processor scans its annotated types once per relevant round and generates nothing. It validates only the slash prefix; uniqueness, HTTP behavior and a complete routing grammar are separate application checks. The compiler runs inside this test process without compiling arbitrary user submissions.'],
['Declaring an annotation does not automatically run a processor.','Do not regenerate the same source file in every round.','A compile-time syntax check does not establish runtime endpoint behavior.'],[('annotations','Retention and annotation consumers'),('packages','Declaration layout'),('java-modules','Compiler and module boundaries')])

put('long-adder','Java LongAdder: striped counters and the limits of sum snapshots',
'LongAdder distributes concurrent additions across internal counters and combines their values when sum is requested.',
[('Count observations, not remaining capacity',[
'A parser can record how many rows workers accepted. Several workers increment the same metric, then the coordinator joins all workers and reports the count. A striped counter fits an observation metric because callers do not need to claim the next unique value or atomically reject a quota overrun.',
'The program waits until every writer has ended before reading the total. During concurrent updates, sum does not promise an atomic snapshot. Using it in a check-then-increment admission rule can allow more callers than the permitted capacity. An atomic transition or a semaphore is a different contract.'
]),('Reset needs an ownership rule',[
'sumThenReset is useful only when a non-atomic reset is acceptable under the application timing rule. It is not a substitute for a precisely bounded reporting interval with active writers. Resetting a live metric and publishing it as an exact count can lose the connection between requests and windows.',
'The runtime chooses its internal stripe arrangement. This fixture proves the final arithmetic result after joins, not a throughput improvement over AtomicLong on every machine. False sharing, contention, processor count and read frequency all affect a real comparison.'
])],'''import java.util.concurrent.atomic.LongAdder;
public class AcceptedRowMetric {
    public static void main(String[] args) throws Exception {
        LongAdder accepted = new LongAdder();
        Thread[] writers = new Thread[4];
        for (int index=0; index<writers.length; index++) {
            writers[index] = new Thread(() -> { for (int row=0; row<750; row++) accepted.increment(); });
            writers[index].start();
        }
        for (Thread writer : writers) writer.join();
        System.out.println(accepted.sum());
        System.out.println(accepted.sumThenReset());
        System.out.println(accepted.sum());
    }
}''','3000\n3000\n0',
['Each increment performs bounded counter work but its contention cost is runtime-dependent. sum visits internal counter state and may cost more than reading one AtomicLong. This fixture retains four worker threads and one counter. It does not publish a timing comparison or justify replacing every application counter with LongAdder.'],
['Do not use sum as an atomic quota decision while writers are active.','Do not assume reset creates an exact reporting window under concurrent updates.','The final count requires completion of all writers before observation.'],[('atomics','Atomic transitions'),('semaphores','Admission permits'),('jmh-benchmarks','Measured comparisons')])

put('zip-path-validation','Java ZIP inputs: bounded staging and rejected path traversal',
'A ZIP entry name is untrusted input; before writing it, an extractor must establish that its destination remains inside the owned output directory.',
[('Normalize a destination, not just a string prefix',[
'A receipt archive can contain a name such as ../outside.txt. Concatenating that name with an output directory can escape the intended location. Resolve the entry against the root, normalize the resulting Path, and compare path components with startsWith; a string prefix comparison can confuse sibling directories.',
'This fixture rejects absolute names, backslashes, colons, empty names, root-only destinations and paths that normalize outside the root. It stages bytes in memory and does not write them to the file system. Restricting the accepted name grammar makes the lexical policy reproducible across the operating systems used by this example.'
]),('Compressed size is not the work budget',[
'The header size may be absent or misleading. Count bytes as they are read and stop when the total uncompressed budget is exceeded. The program permits at most eight files and 64 KiB total output, and rejects duplicate normalized destinations before publication.',
'A lexical check does not settle symbolic-link races in a pre-existing directory. A production extractor needs an owned private staging directory, a policy for links and permissions, and a publication rule that cannot redirect writes between validation and creation. No general-purpose secure extraction guarantee is made by this in-memory example.'
])],'''import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import java.util.zip.ZipOutputStream;
public class ReceiptArchiveStaging {
    static Map<Path, byte[]> stage(byte[] archive) throws Exception {
        Path root = Paths.get("receipt-output").toAbsolutePath().normalize();
        Map<Path, byte[]> staged = new LinkedHashMap<>(); int total=0;
        try (ZipInputStream input = new ZipInputStream(new ByteArrayInputStream(archive))) {
            ZipEntry entry;
            while ((entry=input.getNextEntry()) != null) {
                String name=entry.getName();
                if (name.isEmpty() || name.startsWith("/") || name.contains("\\\\") || name.contains(":")) throw new IllegalArgumentException("Invalid name");
                Path target=root.resolve(name).normalize();
                if (!target.startsWith(root) || target.equals(root)) throw new IllegalArgumentException("Outside root");
                if (entry.isDirectory()) { input.closeEntry(); continue; }
                if (staged.size()==8 || staged.containsKey(target)) throw new IllegalArgumentException("File count or duplicate");
                ByteArrayOutputStream content=new ByteArrayOutputStream(); byte[] buffer=new byte[1024]; int count;
                while ((count=input.read(buffer)) != -1) {
                    if (count>65536-total) throw new IllegalArgumentException("Uncompressed budget");
                    total+=count; content.write(buffer,0,count);
                }
                staged.put(target,content.toByteArray()); input.closeEntry();
            }
        }
        return staged;
    }
    static byte[] archive(String name) throws Exception {
        ByteArrayOutputStream bytes=new ByteArrayOutputStream();
        try (ZipOutputStream output=new ZipOutputStream(bytes)) {
            output.putNextEntry(new ZipEntry(name)); output.write("R-51".getBytes(StandardCharsets.UTF_8)); output.closeEntry();
        }
        return bytes.toByteArray();
    }
    public static void main(String[] args) throws Exception {
        System.out.println(stage(archive("reports/receipt.txt")).size());
        try { stage(archive("../outside.txt")); }
        catch (IllegalArgumentException rejected) { System.out.println("traversal rejected"); }
    }
}''','1\ntraversal rejected',
['Decompression work depends on input and output bytes; staging retains at most 64 KiB of payload plus bounded path and buffer overhead. The caller must also bound compressed input before passing a byte array. This sample does not model encrypted archives, filesystem links, concurrent directory changes or crash-durable publication.'],
['Do not validate destinations using string prefixes.','Do not trust ZIP header size as the decompression budget.','Do not publish partial files before validating the complete archive.'],[('files','Path resolution'),('manifest-project','Validated file publication'),('concurrent-import-project','Staged import ownership')],subject='java-projects')

# Expand canonical pages rather than creating competing pages for the same intent.
extra={
 'java/hashmap':('<h2>Internal working: a Java 8 implementation view</h2>'+p('The Java 8 implementation stores entries in a bucket array. It spreads a key hash with a shifted portion of the hash and selects a bucket using a mask against the current power-of-two capacity. Equality is still checked inside that bucket. These are implementation details of the inspected Java 8 source, not extra promises made by the Map interface.')+p('The default load factor is 0.75. Capacity and load factor determine when growth is needed, but an initial capacity is not a fixed maximum number of mappings. During a resize, stored hash bits decide whether an entry remains at its old index or moves by the old capacity. Keys still need stable equality and hash behavior; growth cannot repair a mutated key.')+p('The inspected Java 8 source declares a treeification threshold of eight and a minimum treeification capacity of sixty-four. A collision-heavy bucket can trigger growth rather than tree conversion when the array is smaller. Treating eight colliding insertions as a portable guarantee of a tree is therefore wrong. The insertion path, current capacity and release matter.')+p('Tree bins limit many collision cases, but a blanket claim that every hostile key set gives logarithmic lookup is too broad. Equal-hash keys and their comparability affect how the implementation searches. Iteration also visits capacity and stored mappings, so allocating a huge sparse map can make scanning expensive even when lookups are usually quick. Validate adversarial keys and measure the application distribution before choosing a capacity.')),
 'java/enum-collections':('<h2>Typed copies and empty inputs</h2>'+p('EnumMap needs the key enum type to allocate its representation. A copy constructor receiving an empty ordinary Map cannot infer that type; provide the enum class explicitly, then putAll the input. EnumMap can store null values, so get alone cannot distinguish an absent mapping from a mapped null. Keep the value contract explicit.')+p('EnumSet.noneOf also needs the enum class. A snapshot copied from an existing EnumSet retains its enum type even when it is empty, but copying an empty arbitrary collection cannot infer one. Neither structure is a concurrency boundary; a compact representation does not make several state changes atomic.')),
 'java/annotations':('<h2>Separate runtime inspection from compile-time processing</h2>'+p('Runtime retention makes a marker available to reflective consumers. Source retention serves a compiler-time consumer and does not keep the annotation available for later reflection. An annotation does no work merely by existing; the consumer owns validation, generated output or execution behavior. Compile-time processing is a separate build operation that needs a declared processor and a test for accepted and rejected declarations.')),
 'java/bigdecimal':('<h2>Scale is part of equality</h2>'+p('BigDecimal values can compare numerically equal while equals returns false because their scales differ. A sorted collection whose comparator uses compareTo can therefore group values that a hash-based collection keeps distinct. Choose the equality contract before using decimal values as keys; stripping trailing zeros also changes scale and is not a universal storage policy.')+p('A string constructor preserves the decimal input supplied by the caller. Constructing from a double preserves that double value, including its binary approximation; valueOf uses a different conversion route. Division with a non-terminating decimal expansion needs a declared precision or scale and rounding rule. Do not let a display formatting choice silently become the calculation rule.'))}
for path,text in extra.items():
 e=lookup[path];marker='<h2>Working program</h2>'
 if marker not in e['body']:marker='<h3>Common Mistakes</h3>'
 e['body']=e['body'].replace(marker,text+marker,1);e['updated_at']=stamp;expanded.append(path)
mods={
 'java/advanced-java':[('Ownership and extension points',['foreign-memory','varhandles','service-discovery','properties-validation','annotation-processing','long-adder']),('Desktop event-thread boundaries',['swing-workers'])],
 'java/java':[('Localized message resources',['resource-bundles'])],
 'java/java-examples':[('Raster rendering checks',['java2d-images'])],
 'java/java-projects':[('Bounded archive staging',['zip-path-validation'])]}
for hub,modules in mods.items():
 for title,slugs in modules:lookup[hub]['data']['modules'].append({'title':title,'summary':'Check accepted input, ownership and failure behavior with the complete program.','lessons':['java/'+s for s in slugs]})
 lookup[hub]['updated_at']=stamp
for e in entries:
 if e['type']=='subject' and e['path'].startswith('java/'):
  paths=[p for m in e['data']['modules'] for p in m['lessons']];assert len(paths)<=100 and len(paths)==len(set(paths)),e['path']
(ROOT/'src/data/fixtures.json').write_text(json.dumps(entries,indent=2,ensure_ascii=False)+'\n')
report={'added':added,'expanded':expanded,'articles':sum(e['type']=='article' and e['path'].startswith('java/') for e in entries),'hubs':10,'quizzes':14,'quizQuestions':168}
(OUT/'java-release-batch.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
