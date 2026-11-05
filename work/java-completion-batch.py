"""Original second Java batch; append to the existing curriculum without resetting it."""
import json, html, re, uuid, pathlib, copy, zipfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT.parent.parent / 'outputs'
entries = json.loads((ROOT / 'src/data/fixtures.json').read_text())
by_path = {entry['path']: entry for entry in entries}
new = []
sections_by_subject = {e['subject']: e['path'] for e in entries if e['path'].startswith('java/') and e['type'] == 'subject'}
def p(text): return '<p>' + text.replace('<Integer>', '&lt;Integer&gt;') + '</p>'
def block(code, lang='java'):
    return '<pre><code class="language-' + lang + '">' + html.escape(code.strip('\n'), quote=False) + '</code></pre>'
def add(slug, title, definition, sections, program, output, cost, mistakes, related, subject='java-advanced', release=8, dependency=None):
    body = p(definition) + p('<strong>Java ' + str(release) + '+.</strong> ' + ('The JDBC programs need the H2 driver on the runtime classpath.' if dependency == 'h2' else 'Use a JDK that supports this release.'))
    for heading, paragraphs in sections:
        body += '<h2>' + heading + '</h2>' + ''.join(p(text) for text in paragraphs)
    if program:
        body += '<h2>' + ('Test class' if dependency == 'junit' else 'Working program') + '</h2>' + block(program)
        if output is not None: body += '<h3>Output</h3>' + block(output, 'text')
    body += '<h2>Cost and design choices</h2>' + ''.join(p(text) for text in cost)
    body += '<h3>Common Mistakes</h3><ul>' + ''.join('<li>' + text + '</li>' for text in mistakes) + '</ul>'
    path = 'java/' + slug
    entry = copy.deepcopy(by_path['java/arrays'])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://aitrove.in/' + path)), path=path, title=title, summary=definition, type='article', body=body, subject=subject, tags=['java', slug], difficulty='Intermediate', featured=False, updated_at='2026-09-28T12:00:00+00:00')
    entry['data'] = dict(subject_root='java/java', section_path=sections_by_subject[subject], kind='tutorial', reading_minutes=max(3, round(len(re.sub('<[^>]+>', ' ', body).split()) / 160)), author_path='authors/aitrove-editorial', content_format='html', java_release=release, java_version=str(release)+'+', related=[{'path':'java/'+ref, 'title':label} for ref,label in related])
    if dependency: entry['data']['java_dependency'] = dependency
    if path in by_path: by_path[path].update(entry)
    else: entries.append(entry); by_path[path] = entry
    new.append(path)

add('stringbuilder', 'Java StringBuilder: bounded text assembly',
'StringBuilder stores a mutable sequence of UTF-16 code units so a caller can assemble text without replacing the complete result after every append.',
[('Build a report with one owner', [
'A batch export needs one line per accepted shipment. Give the builder to that method alone. Sharing it among workers requires a coordination rule, and changing the class to StringBuffer does not make a multi-step report transaction atomic.',
'Capacity is reserved storage; length is the amount of text currently present. Reserving a measured starting capacity can reduce growth, but reserving a megabyte for every tiny report simply transfers the cost to idle memory. This program uses a small hint and rejects reports whose final line would exceed the contract.',
'Text is not escaped merely because it came through append. If the destination is HTML, JSON, SQL, or a spreadsheet, its encoding rules remain separate. The sample accepts only integer shipment IDs and emits plain text, so it does not claim to solve those formats.'
]), ('Check before appending', [
'The line is built independently so the size check can reject it before modifying the accumulated report. That temporary allocation trades a small per-line cost for a simple failure boundary. A streaming writer is preferable when the report can exceed available memory.',
'length measures UTF-16 units, not displayed glyphs or UTF-8 bytes. A byte-based transport limit needs an encoded-byte budget. Read the <a href="/java/strings">String lesson</a> before treating text indexes as user-visible character positions.'
])], r'''public class ShipmentReport {
    static String render(int[] shipmentIds, int maxUnits) {
        StringBuilder report = new StringBuilder(Math.min(maxUnits, 64));
        for (int shipmentId : shipmentIds) {
            String line = "shipment=" + shipmentId + "\n";
            if (line.length() > maxUnits - report.length()) {
                throw new IllegalArgumentException("Report exceeds text budget");
            }
            report.append(line);
        }
        return report.toString();
    }
    public static void main(String[] args) {
        System.out.print(render(new int[]{418, 509}, 64));
    }
}''', 'shipment=418\nshipment=509', [
'For L output units, growing and copying the accumulated buffer takes amortised O(L) work under ordinary geometric growth. Converting to String also materialises a result; the builder and result can coexist during the call. Budget O(L) live storage rather than assuming append removes all allocation.',
'An insert at the start shifts existing text. Repeating that edit across a growing report can be quadratic. Append in output order, or collect fragments and join once.'
], ['Validate negative limits before allocating.', 'Do not confuse capacity with length.', 'Do not reuse a builder as shared mutable service state.'], [('strings','String ownership'),('files','Streaming file output')], 'java')

add('boxing', 'Java wrappers and boxing: nulls, identity, and allocation',
'Boxing converts a primitive value to its wrapper reference; unboxing extracts a primitive from a wrapper and fails when that reference is null.',
[('Choose a missing-value contract', [
'A sensor reading may be absent. Integer can represent that absence with null; int cannot. Once the application chooses a default, convert at a single boundary so every arithmetic expression does not need another null check.',
'The program counts only present readings and computes a long total. It does not substitute zero for missing values because that would change the average. If every reading is absent, it reports that fact rather than dividing by zero.',
'Wrapper identity is irrelevant to numeric equality. Comparing two Integer references with == tests whether the references match; cached small values can make an incorrect test appear correct. Use value equality or unbox after checking absence.'
]), ('A generic list stores references', [
'List<Integer> cannot store primitive int elements directly. Boxing fits values into the generic reference-type contract, with potential object and indirection costs. An int array is a better representation when a large fixed numeric batch does not require nulls or list operations.',
'Repeated boxing in a hot loop should be measured with a benchmark that prevents unused results from disappearing. Timing a few iterations in main includes startup effects and does not establish the cost of one boxed operation.'
])], '''public class SensorAverage {
    public static void main(String[] args) {
        Integer[] readings = {120, null, 180};
        long total = 0;
        int present = 0;
        for (Integer reading : readings) {
            if (reading != null) {
                total += reading;
                present++;
            }
        }
        if (present == 0) {
            System.out.println("No readings");
        } else {
            System.out.println("mean=" + total / present);
        }
        System.out.println("present=" + present);
    }
}''', 'mean=150\npresent=2', [
'The scan requires O(n) time and O(1) additional storage beyond the input array. The average uses integer division, so it truncates. A decimal average needs an explicit precision and rounding policy, rather than an accidental conversion after division.',
'Unboxing does not make an update atomic. Incrementing an Integer field still reads, computes, and writes. Study <a href="/java/threads">visibility and atomicity</a> before sharing such counters.'
], ['Do not unbox null.', 'Do not compare wrapper references to establish value equality.', 'Do not count absent readings as zero without defining that policy.'], [('variables-types','Numeric ranges'),('optional','Representing absence')], 'java')

add('abstract-classes', 'Java abstract classes: shared invariants and extension points',
'An abstract class can define state and implemented methods while requiring subclasses to supply selected operations; it cannot be instantiated directly.',
[('Keep the policy boundary small', [
'A dispatch request has an invariant: its destination must be usable. Validation belongs in the base constructor because every transport shares that rule. The transport-specific receipt is the extension point.',
'The final dispatch method keeps the operation sequence fixed. A subclass supplies a receipt format through an abstract method, but it cannot bypass the base validation by replacing dispatch. This is useful only when those restrictions actually belong to the abstraction.',
'Java permits one direct class superclass. If a type only needs to promise behavior, an <a href="/java/interfaces">interface</a> avoids consuming that inheritance choice. If several implementations share storage and a controlled method sequence, an abstract class can carry those requirements.'
]), ('Do not call extension points during construction', [
'The superclass constructor runs before subclass initialization completes. Calling an overridable method there can read uninitialized subclass fields. Store validated base state first and call extension points only after the object is constructed.',
'This sample returns a receipt string. It does not send a message or charge a carrier account. Real external dispatch requires failure handling and an idempotency contract; an inheritance hierarchy supplies neither.'
])], '''public class DispatchPolicies {
    static abstract class DispatchRequest {
        private final String destination;
        DispatchRequest(String destination) {
            if (destination == null || destination.trim().isEmpty()) {
                throw new IllegalArgumentException("Destination is required");
            }
            this.destination = destination;
        }
        public final String dispatch() { return receipt(destination); }
        protected abstract String receipt(String destination);
    }
    static final class WarehouseRequest extends DispatchRequest {
        WarehouseRequest(String destination) { super(destination); }
        protected String receipt(String destination) {
            return "queued:" + destination;
        }
    }
    public static void main(String[] args) {
        DispatchRequest request = new WarehouseRequest("delhi-warehouse");
        System.out.println(request.dispatch());
    }
}''', 'queued:delhi-warehouse', [
'Dispatch here performs work proportional to the destination text copied into the result. The hierarchy does not change that cost. Avoid claiming method dispatch is the bottleneck before measuring the complete operation.',
'Protected mutable fields couple every subclass to storage details. Private state plus a narrow extension contract keeps validation under one owner. Composition is often simpler when policies vary independently.'
], ['Do not call abstract or overridable methods from a constructor.', 'Do not inherit solely to reuse an unrelated helper.', 'Do not make validated state publicly mutable.'], [('inheritance','Inheritance boundaries'),('polymorphism','Runtime dispatch')], 'java')

add('nested-classes', 'Java nested classes: enclosing instances and object lifetime',
'A static nested class is a member type without an implicit enclosing instance; a non-static inner class is associated with an enclosing object.',
[('Store only the ownership you need', [
'A shipment snapshot needs an ID and a state. It does not need the entire warehouse service. Making the value type static avoids an implicit route back to an enclosing service instance.',
'A non-static inner type can access its enclosing object’s members. That can be useful for a short-lived helper, but storing the helper in a long-lived listener registry can also retain the enclosing object and its reachable state.',
'The sample copies a few immutable values into a static snapshot. Copying a reference to a mutable list would still share its elements; nested-class syntax does not supply a deep-copy operation.'
]), ('Distinguish visibility from capture', [
'A member class can be private even though a method returns a public representation such as text. Visibility determines who can name or access the type. Static determines whether each instance needs an enclosing instance. Those are different choices.',
'Local classes and lambdas may capture effectively final local variables. Capturing a reference does not freeze the referenced object. The <a href="/java/lambdas">lambda lesson</a> covers that boundary for callbacks.'
])], '''public class WarehouseSnapshot {
    private final String warehouseId;
    WarehouseSnapshot(String warehouseId) { this.warehouseId = warehouseId; }
    static final class ShipmentState {
        private final String id;
        private final String state;
        ShipmentState(String id, String state) {
            this.id = id;
            this.state = state;
        }
        String render() { return id + ":" + state; }
    }
    ShipmentState snapshot(String shipmentId) {
        return new ShipmentState(warehouseId + "/" + shipmentId, "ready");
    }
    public static void main(String[] args) {
        ShipmentState snapshot = new WarehouseSnapshot("north").snapshot("s-54");
        System.out.println(snapshot.render());
    }
}''', 'north/s-54:ready', [
'The snapshot stores two references plus ordinary object overhead. Exact byte sizes depend on the VM and reference representation; syntax alone does not determine a portable byte count.',
'A retained inner instance can keep a larger graph reachable. Assess retained memory, not just shallow object size. Clearing a service reference does not help if another live object still reaches it.'
], ['Do not assume nested means static.', 'Do not capture a service in a long-lived callback without considering lifetime.', 'Do not describe a shallow snapshot as deeply immutable.'], [('classes-objects','Object ownership'),('jvm-memory','Reachability and memory')], 'java')

add('varargs', 'Java varargs: arrays at a method boundary',
'A variable-arity parameter accepts a sequence of arguments through an array and must be the final parameter in the method declaration.',
[('The callee receives an array', [
'A call can pass individual values or an existing compatible array. In the second case, the method receives the caller’s array reference. Mutating that array changes caller-visible state, so a read-only aggregation should avoid writes.',
'The shipment counter rejects negative counts and adds with checked arithmetic. That is a clearer failure contract than accepting a wrapped total. A zero-argument call produces an empty input and a total of zero.',
'A null array is not the same as an empty array. The explicit null check preserves the chosen error message. If the signature were Integer..., a null element could also fail during unboxing.'
]), ('Keep overload resolution predictable', [
'Varargs overloads mixed with ordinary overloads and boxed types can surprise readers. Prefer one clear entry point when the inputs have the same meaning. If two operations represent different policies, give them different names.',
'Generic varargs can expose a non-reifiable array and create heap-pollution hazards. Do not suppress warnings as a substitute for proving the method never writes unsafe values or exposes its array. See <a href="/java/generics">generic invariance</a>.'
])], '''public class ShipmentTotals {
    static long total(int... shipmentCounts) {
        if (shipmentCounts == null) {
            throw new IllegalArgumentException("Counts cannot be null");
        }
        long total = 0;
        for (int count : shipmentCounts) {
            if (count < 0) throw new IllegalArgumentException("Negative count");
            total = Math.addExact(total, count);
        }
        return total;
    }
    public static void main(String[] args) {
        int[] counts = {7, 12, 4};
        System.out.println(total(counts));
        System.out.println(total());
    }
}''', '23\n0', [
'Summing n values requires O(n) time and O(1) additional working storage. A call with separate arguments may allocate an argument array. Passing an existing array avoids that new array, but it shares the reference.',
'When input arrives as a large stream, a varargs boundary requires materializing the batch. A streaming accumulator with an explicit reset and failure policy fits a different workload.'
], ['Do not assume varargs copies an existing array.', 'Do not pass null to mean no values.', 'Do not hide generic-varargs warnings without understanding the array contract.'], [('methods','Method contracts'),('arrays','Array sharing')], 'java')

add('annotations', 'Java annotations: retention and explicit processing',
'An annotation attaches structured metadata to a declaration or type use; its effect depends on a compiler, tool, or runtime reader that interprets it.',
[('Metadata is not execution', [
'A marker named Audited does not create an audit log. The program must read that marker and perform whatever action the application requires. The sample reads a service label, prints it, and stops; it deliberately contains no implicit interception machinery.',
'Retention controls how long the metadata survives. SOURCE metadata is unavailable after compilation. CLASS metadata is stored in class files but is not exposed as a runtime annotation through ordinary reflection. RUNTIME lets this program read the annotation while it runs.',
'Target limits legal placements. A type-level service marker should not accidentally be placed on a local variable and then silently ignored by a reader that only checks classes.'
]), ('Define missing metadata behavior', [
'getAnnotation may return null. Decide whether absence is allowed, defaults to another policy, or rejects registration. The sample uses an explicit unlabelled state rather than dereferencing a missing annotation.',
'Annotation values describe metadata; they cannot carry arbitrary mutable service objects. Keep operational state outside the annotation. If a value names a handler class, instantiating and validating that handler is a separate step.',
'Annotation processing during compilation and reflection at runtime are different mechanisms. A compile-time generator can create source files without the runtime retaining its marker. This lesson uses the runtime case only.'
])], r'''import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

public class ServiceLabels {
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.TYPE)
    @interface ServiceLabel { String value(); }
    @ServiceLabel("shipment-index")
    static final class ShipmentIndex { }
    public static void main(String[] args) {
        ServiceLabel label = ShipmentIndex.class.getAnnotation(ServiceLabel.class);
        System.out.println(label == null ? "unlabelled" : label.value());
    }
}''', 'shipment-index', [
'One annotation lookup does not scan every object instance. Processing a registry of n service classes still requires work for those n classes and any generated registrations. Cache a validated registry rather than repeating inspection per request.',
'The marker does not establish authorization, a transaction, or a thread-safety guarantee. Such behavior requires tested code that owns those operations.'
], ['Do not expect a marker to execute behavior by itself.', 'Do not use CLASS retention when the reader requires runtime reflection.', 'Do not assume annotation inheritance applies to every placement.'], [('reflection','Runtime inspection'),('interfaces','Explicit behavior contracts')])

add('reflection', 'Java reflection: inspect types without breaking contracts',
'Reflection reads type and member metadata at runtime and can invoke members through reflective handles instead of a direct source-level call.',
[('Inspect a narrow contract', [
'An importer needs to learn whether a plugin exposes a public identifier method. The sample requests that exact public method and invokes it on a constructed object. It does not scan private fields or infer a schema from every implementation detail.',
'getMethod searches public methods, including inherited ones. getDeclaredMethod examines declarations on the requested class and can find non-public members, but finding a member does not grant permission to invoke it.',
'On modular runtimes, access restrictions can block deep reflection. Treat an inaccessible member as a boundary to respect. Adding broad opening flags merely to preserve an accidental dependency on private fields creates a deployment requirement that callers must understand.'
]), ('Separate lookup failure from target failure', [
'A missing method is a registration error. An exception thrown by the invoked method is wrapped in InvocationTargetException; its cause is the failure from the target code. Report those cases differently so the operator can identify a contract mismatch versus a service error.',
'A direct interface method is usually easier to compile-check and test. Choose reflection when the program has a real runtime discovery requirement, not when a normal <a href="/java/interfaces">interface</a> already describes the plugin.'
])], r'''import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;

public class PluginInspection {
    public static final class ShipmentPlugin {
        public String identifier() { return "shipment-plugin"; }
    }
    public static void main(String[] args) throws ReflectiveOperationException {
        Method identifier = ShipmentPlugin.class.getMethod("identifier");
        try {
            Object result = identifier.invoke(new ShipmentPlugin());
            System.out.println(result);
        } catch (InvocationTargetException failure) {
            throw new IllegalStateException("Plugin failed", failure.getCause());
        }
    }
}''', 'shipment-plugin', [
'Lookup, argument checks, and invocation have costs that differ from a direct call. Exact overhead depends on the VM, optimization, and workload. Cache resolved metadata where appropriate and measure the full registration or request path.',
'Caching Class or Method objects indefinitely can keep associated class loaders reachable. Plugin reload systems need cache lifetime to follow plugin lifetime.'
], ['Do not treat getDeclaredMethod as an access grant.', 'Do not discard the cause of InvocationTargetException.', 'Do not rely on the unspecified order of reflected members.'], [('annotations','Runtime metadata'),('jvm-memory','Retained object graphs')])

add('jvm-memory', 'Java JVM memory: stack frames, heap objects, and reachability',
'A JVM maintains per-thread execution frames and shared areas for objects and class-related information; object lifetime follows reachability rather than a source variable’s name.',
[('A reference is not an object copy', [
'A local reference can reach the same array as a field or another local. The array stays usable while at least one live route to it remains. Returning from the method that allocated it does not necessarily make it unreachable.',
'The sample returns a snapshot of an internal byte buffer. The copy costs time and storage, but it prevents a reader from overwriting the owner’s retained array. Returning the original array would expose a second writer.',
'A stack frame holds method execution state. Do not use that statement to claim every primitive always lives on a stack or every source-level allocation becomes a distinct heap allocation: a VM can optimize representation while preserving observable behavior.'
]), ('Retained size matters', [
'A cache entry may look small while reaching a large payload, an enclosing instance, or a chain of listeners. Shallow size is the entry itself. Retained memory concerns what becomes collectible when that ownership route disappears.',
'Static collections, thread-local state, and callback registries deserve explicit bounds and removal policies. A service that accepts unlimited unique keys can retain unlimited values even when each request eventually returns.',
'Heap exhaustion and stack exhaustion have different failure paths. Deep unbounded recursion can exhaust a thread’s stack; accumulating retained payloads can exhaust heap capacity. Increasing one budget does not necessarily fix the other.'
])], r'''import java.util.Arrays;

public class PayloadOwnership {
    static final class PayloadStore {
        private final byte[] payload;
        PayloadStore(byte[] payload) { this.payload = Arrays.copyOf(payload, payload.length); }
        byte[] snapshot() { return Arrays.copyOf(payload, payload.length); }
    }
    public static void main(String[] args) {
        byte[] imported = {10, 20, 30};
        PayloadStore store = new PayloadStore(imported);
        imported[0] = 99;
        byte[] reader = store.snapshot();
        reader[1] = 88;
        System.out.println(Arrays.toString(store.snapshot()));
    }
}''', '[10, 20, 30]', [
'Copying n bytes takes O(n) work and O(n) destination storage. A snapshot isolates byte values because the elements are primitives; copying an array of mutable object references would not isolate those objects.',
'This ownership test proves a visible mutation boundary. It does not measure allocation bytes, GC pauses, or memory leaks; those require workload-specific diagnostics.'
], ['Do not assume leaving scope closes a file or socket.', 'Do not equate shallow size with retained size.', 'Do not claim exact object byte sizes without a VM-specific measurement.'], [('pass-by-value','Reference values'),('gc-diagnostics','Memory diagnostics')])

add('gc-diagnostics', 'Java garbage collection: diagnose retention before tuning',
'Garbage collection recovers storage from objects the runtime can no longer reach; it does not close application resources or guarantee a fixed pause time.',
[('Compare the same workload phases', [
'Capture a baseline after startup, run a bounded workload, allow it to reach its usual idle state, then compare the retained trend. One high heap reading during an allocation burst is different evidence from a rising floor after repeated equivalent batches.',
'The program measures currently used heap through MemoryMXBean before and after allocating a small retained buffer. The numbers vary across runs and are not a deterministic leak test. Collection, heap resizing, and other runtime work can alter them.',
'A histogram identifies common classes; it does not prove why they remain reachable. A heap dump and ownership analysis can show the retaining path. Dumps may contain application data and need an intentional storage and access policy.'
]), ('Choose a diagnostic before a collector flag', [
'For a Java 21 run, unified GC logging can show collection events and pause information. A bounded log file keeps a long-running diagnostic from consuming an unbounded disk budget. Compare latency and throughput under the same input rather than assuming fewer collections means a faster service.',
'System.gc is a request, not a contractual test barrier. Do not insert it between production requests to compensate for an unbounded cache. Reduce the retaining owner or give it an explicit capacity first.',
'A collector cannot reclaim an object still reachable through a live owner. <a href="/java/jvm-memory">Reachability</a> explains that requirement. Different collectors trade pause behavior, concurrent work, and memory headroom; no one setting removes those tradeoffs.'
])], r'''import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;

public class HeapObservation {
    private static byte[] retained;
    public static void main(String[] args) {
        MemoryMXBean memory = ManagementFactory.getMemoryMXBean();
        long before = memory.getHeapMemoryUsage().getUsed();
        retained = new byte[256 * 1024];
        long after = memory.getHeapMemoryUsage().getUsed();
        System.out.println("beforeBytes=" + before);
        System.out.println("afterBytes=" + after);
        System.out.println("retainedBytes=" + retained.length);
        retained = null;
    }
}''', None, [
'The buffer uses O(n) payload storage for n bytes. Clearing this one retaining reference permits later reclamation if no other owner exists; it does not synchronously lower the heap measurement.',
'Diagnostic capture adds work. A live heap dump or profiling session can perturb latency and may require a maintenance plan. Record the tool settings alongside the measured result.'
], ['Do not label every temporary peak a memory leak.', 'Do not use forced collection as proof of production behavior.', 'Do not tune a collector before checking an unbounded retaining structure.'], [('jvm-memory','Memory ownership'),('nested-classes','Enclosing references')], release=21)

add('jdbc-prepared', 'Java JDBC PreparedStatement: values stay outside SQL grammar',
'PreparedStatement binds typed values to SQL parameter positions so input data does not become part of the statement’s SQL grammar.',
[('Bind values, not identifiers', [
'The receipt lookup uses a fixed WHERE clause and a bound receipt ID. A quote inside an ID remains data. Concatenating that ID into the SQL string would force the input to participate in parsing.',
'A placeholder cannot stand in for a table name, column name, or arbitrary ORDER BY expression. If users choose a sorting field, map an allowed choice to a fixed SQL fragment owned by the application. Binding values does not validate unrestricted SQL fragments.',
'This program creates a disposable in-memory H2 database. Add com.h2database:h2:2.3.232 to the runtime dependencies. The program uses only JDBC types at compilation but still needs a database driver when DriverManager opens the URL.'
]), ('Keep result ownership inside the query', [
'The method returns a String rather than an open ResultSet. Nested try-with-resources closes the result and statement before returning. The caller owns the connection and decides its lifetime.',
'A missing row returns null here. The boundary is explicit; another API might use Optional. Multiple equal IDs are prevented by the primary key. Without that constraint, taking the first row would hide ambiguous data.',
'A JDBC driver and database may differ in preparation, caching, conversion, and timeout behavior. The portable claim is parameter binding; it is not a promise that every engine parses exactly once.'
])], r'''import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

public class ReceiptLookup {
    static String status(Connection connection, String receiptId) throws SQLException {
        try (PreparedStatement query = connection.prepareStatement(
                "SELECT status FROM receipts WHERE receipt_id = ?")) {
            query.setString(1, receiptId);
            try (ResultSet rows = query.executeQuery()) {
                return rows.next() ? rows.getString(1) : null;
            }
        }
    }
    public static void main(String[] args) throws SQLException {
        try (Connection connection = DriverManager.getConnection("jdbc:h2:mem:receipts")) {
            try (PreparedStatement schema = connection.prepareStatement(
                    "CREATE TABLE receipts(receipt_id VARCHAR PRIMARY KEY, status VARCHAR)")) {
                schema.executeUpdate();
            }
            try (PreparedStatement insert = connection.prepareStatement(
                    "INSERT INTO receipts VALUES (?, ?)")) {
                insert.setString(1, "rcpt-'54");
                insert.setString(2, "paid");
                insert.executeUpdate();
            }
            System.out.println(status(connection, "rcpt-'54"));
            System.out.println(status(connection, "absent"));
        }
    }
}''', 'paid\nnull', [
'Lookup cost depends on the query plan, indexes, result size, and engine. A bound parameter is not an indexing strategy. This primary key supports one-row lookup, but a portable JDBC lesson cannot assign a universal O(1) database cost.',
'Holding connections during unrelated work consumes a pool budget. Close query resources promptly and keep request deadlines, statement timeouts, and connection ownership explicit.'
], ['Do not concatenate untrusted values into SQL.', 'Do not expect a placeholder to bind a table name.', 'Do not return a ResultSet after closing its statement.'], [('try-with-resources','Resource closure'),('jdbc-transactions','Commit and rollback')], dependency='h2')

add('jdbc-transactions', 'Java JDBC transactions: atomic updates and rollback',
'A JDBC transaction groups database changes into a commit or rollback boundary on a connection with auto-commit disabled.',
[('Treat related writes as one operation', [
'A stock transfer decreases one location and increases another. If only the first write commits, the application loses inventory. The sample uses one connection and commits only after both writes report exactly one updated row.',
'The source update checks available stock in the WHERE condition. Checking stock in a separate earlier query would create a race window. A failed destination update causes rollback, which undoes the first change inside the same transaction.',
'Add com.h2database:h2:2.3.232 for this disposable test database. Real databases have their own locking and isolation details; the demonstrated invariant must be retested against the production engine.'
]), ('Give the transaction one owner', [
'The helper requires auto-commit to be off and owns the operation’s commit or rollback. Call it with a connection dedicated to this transaction. It is unsuitable inside a larger transaction whose caller expects to make the final commit decision.',
'If rollback itself fails, preserve that error as suppressed on the original failure. Losing the first failure makes diagnosis harder. A connection with uncertain transaction state should not be casually returned to a pool.',
'A database transaction does not atomically publish an email or charge an external service. Those side effects need another delivery design, such as an outbox and retry policy, beyond this two-table update.'
])], r'''import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

public class StockTransfer {
    static void transfer(Connection connection, String source, String target, int units)
            throws SQLException {
        if (units <= 0) throw new IllegalArgumentException("Units must be positive");
        if (connection.getAutoCommit()) throw new IllegalStateException("Transaction required");
        try (PreparedStatement debit = connection.prepareStatement(
                    "UPDATE stock SET units = units - ? WHERE site = ? AND units >= ?");
             PreparedStatement credit = connection.prepareStatement(
                    "UPDATE stock SET units = units + ? WHERE site = ?")) {
            debit.setInt(1, units); debit.setString(2, source); debit.setInt(3, units);
            if (debit.executeUpdate() != 1) throw new SQLException("Insufficient stock");
            credit.setInt(1, units); credit.setString(2, target);
            if (credit.executeUpdate() != 1) throw new SQLException("Unknown target");
            connection.commit();
        } catch (SQLException failure) {
            try { connection.rollback(); }
            catch (SQLException rollbackFailure) { failure.addSuppressed(rollbackFailure); }
            throw failure;
        }
    }
    public static void main(String[] args) throws SQLException {
        try (Connection connection = DriverManager.getConnection("jdbc:h2:mem:stock")) {
            try (PreparedStatement schema = connection.prepareStatement(
                    "CREATE TABLE stock(site VARCHAR PRIMARY KEY, units INT CHECK(units >= 0))")) {
                schema.executeUpdate();
            }
            try (PreparedStatement seed = connection.prepareStatement(
                    "INSERT INTO stock VALUES ('north', 10), ('south', 2)")) {
                seed.executeUpdate();
            }
            connection.setAutoCommit(false);
            transfer(connection, "north", "south", 3);
            try { transfer(connection, "north", "missing", 2); }
            catch (SQLException expected) { System.out.println("failed transfer rolled back"); }
            try (PreparedStatement query = connection.prepareStatement("SELECT site, units FROM stock ORDER BY site");
                 ResultSet rows = query.executeQuery()) {
                while (rows.next()) System.out.println(rows.getString(1) + "=" + rows.getInt(2));
            }
            connection.rollback();
        }
    }
}''', 'failed transfer rolled back\nnorth=7\nsouth=5', [
'The transaction changes two rows, but elapsed cost includes lock waits and log persistence. Deadlocks and serialization failures may require a bounded retry of the whole operation. Retrying an individual debit after a partially understood failure can duplicate work.',
'The sample uses int quantities and a constrained database column. Check large quantities and destination overflow in the actual schema. Commit success also does not eliminate later application delivery failures.'
], ['Do not commit a caller-owned larger transaction.', 'Do not ignore the update row count.', 'Do not assume rollback reverses an external HTTP call.'], [('jdbc-prepared','Bound SQL values'),('exceptions','Failure context')], dependency='h2')

add('http-client', 'Java HttpClient: request policy, deadlines, and response size',
'HttpClient sends HTTP requests using reusable client configuration while each HttpRequest describes one request’s URI, method, headers, and deadline.',
[('Reuse transport policy', [
'This program constructs a client and an HTTPS GET request without contacting the network. It prints the configured method and host so the example runs offline. Executing send is a separate operation that needs an endpoint, response policy, and integration tests.',
'A connect timeout bounds connection establishment; a request timeout concerns the request. Neither setting defines a complete retry budget for a batch. Decide the maximum elapsed operation time and stop retries when that budget is exhausted.',
'Redirects are disabled here. Forwarding credentials or following a user-provided URL deserves a deliberate host and redirect policy. Constructing a syntactically valid URI does not prove the destination is permitted.'
]), ('Choose the body handler before sending', [
'Reading a response into a String retains the full body. Large or untrusted responses require an actual size budget and a streaming consumption strategy. A Content-Length header can help planning but cannot replace enforcement.',
'A 404 or 500 response is still an HTTP response, not necessarily an IOException. Interpret status codes before treating the payload as success. On interruption, stop work or preserve the thread’s interrupt signal when translating the error.',
'Retries are a protocol decision. A repeated GET and a repeated payment POST have different consequences. An idempotency key is useful only when the receiving service implements a matching contract.'
])], r'''import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.time.Duration;

public class ShipmentRequestPolicy {
    public static void main(String[] args) {
        HttpClient client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(3))
                .followRedirects(HttpClient.Redirect.NEVER)
                .build();
        HttpRequest request = HttpRequest.newBuilder(URI.create("https://api.aitrove.in/shipments"))
                .timeout(Duration.ofSeconds(8))
                .header("Accept", "application/json")
                .GET().build();
        System.out.println(request.method() + " " + request.uri().getHost());
        System.out.println("redirects=" + client.followRedirects());
    }
}''', 'GET api.aitrove.in\nredirects=NEVER', [
'Building a request performs bounded setup for the supplied metadata. Network execution adds connection, TLS, server, and body costs; this offline program makes no throughput claim.',
'Client reuse can retain connection-related resources. Scope its lifetime to the service that owns it and apply a shutdown strategy appropriate to the target JDK. The example’s baseline is Java 11, not a promise about every later release.'
], ['Do not call a response successful solely because send returned.', 'Do not load an unlimited response into memory.', 'Do not swallow InterruptedException and continue retrying.'], [('exceptions','Failure handling'),('try-with-resources','Stream lifetime')], release=11)

add('records', 'Java records: value carriers and defensive copies',
'A record declares a fixed set of components and supplies component accessors, construction, value-based equality, hashing, and a textual representation.',
[('Validate at construction', [
'A receipt batch should always have an ID and an owned list of receipt IDs. The compact constructor rejects a blank batch ID and copies the incoming list. Its accessor returns that copied, unmodifiable list.',
'Final component references do not freeze the objects they reference. List.copyOf prevents structural changes to this copied list; it does not copy a mutable object stored as an element. String elements make the ownership rule straightforward here.',
'Records are suitable when their component list is the value contract. They are less suitable when callers should never observe internal components or when an object needs an evolving identity separate from its data.'
]), ('Equality follows the components', [
'Two instances with equal components compare equal by the generated equals implementation. For an array component, array equality remains reference equality unless you override the relevant behavior. A record does not turn an array into a value-equality list.',
'Do not store sensitive components and then casually log the generated toString. The generated representation exposes component values. Decide redaction at the logging boundary.',
'The lesson targets Java 17 even though records became permanent earlier. That baseline lets the same project use the <a href="/java/sealed-classes">sealed-type lesson</a> without preview flags.'
])], r'''import java.util.ArrayList;
import java.util.List;

public class ReceiptBatches {
    record ReceiptBatch(String id, List<String> receiptIds) {
        ReceiptBatch {
            if (id == null || id.isBlank()) throw new IllegalArgumentException("Batch ID required");
            receiptIds = List.copyOf(receiptIds);
        }
    }
    public static void main(String[] args) {
        List<String> imported = new ArrayList<>(List.of("r-41", "r-52"));
        ReceiptBatch batch = new ReceiptBatch("batch-8", imported);
        imported.clear();
        System.out.println(batch.receiptIds().size());
        System.out.println(batch.equals(new ReceiptBatch("batch-8", List.of("r-41", "r-52"))));
    }
}''', '2\ntrue', [
'Copying n list references takes O(n) time and O(n) storage. The immutable String elements are shared. Value equality for two lists can require O(n) element comparisons; a record is not guaranteed constant-time equality.',
'List.copyOf rejects null elements. If null has a domain meaning, choose a different representation and state that contract instead of silently dropping values.'
], ['Do not claim records are deeply immutable.', 'Do not assume array components use content equality.', 'Do not log every generated component representation without checking data sensitivity.'], [('equals-hashcode','Value equality'),('encapsulation','Ownership boundaries')], release=17)

add('sealed-classes', 'Java sealed types: restrict a domain’s direct variants',
'A sealed class or interface restricts which types may directly extend or implement it through a declared set of permitted variants.',
[('Model a closed decision', [
'A settlement is either accepted with an amount or rejected with a reason. Declaring that pair as permitted variants prevents unrelated implementations from entering this particular model without changing its type declaration.',
'Each permitted direct subtype must state its extension policy: final, sealed, or non-sealed. Records are final, which fits these leaf values. A non-sealed subtype deliberately reopens its branch; it is not another closed leaf.',
'Permitted types obey locality rules. In a named module they belong to the same module; in the unnamed module they belong to the same package. The sample keeps them together as nested types in one source file.'
]), ('A closed hierarchy still needs validation', [
'Knowing the set of variants does not prove an accepted amount is nonnegative or a rejection reason is useful. The record constructors validate those rules. Type closure and value validity solve different problems.',
'The Java 17 program uses instanceof with a binding variable. The <a href="/java/pattern-switch">Java 21 pattern switch</a> lesson shows exhaustive branching without a catch-all fallback that could conceal a newly added variant.'
])], r'''public class SettlementVariants {
    sealed interface Settlement permits Accepted, Rejected { }
    record Accepted(long cents) implements Settlement {
        Accepted { if (cents < 0) throw new IllegalArgumentException("Negative amount"); }
    }
    record Rejected(String reason) implements Settlement {
        Rejected {
            if (reason == null || reason.isBlank()) throw new IllegalArgumentException("Reason required");
        }
    }
    static String describe(Settlement settlement) {
        if (settlement instanceof Accepted accepted) return "accepted=" + accepted.cents();
        if (settlement instanceof Rejected rejected) return "rejected=" + rejected.reason();
        throw new IllegalArgumentException("Settlement required");
    }
    public static void main(String[] args) {
        System.out.println(describe(new Accepted(1250)));
        System.out.println(describe(new Rejected("expired")));
    }
}''', 'accepted=1250\nrejected=expired', [
'The type test selects one of a small fixed number of variants. It does not require scanning a registry. The resulting text allocation depends on its length.',
'Use an open interface for plugin implementations that independent modules must add. Closing that interface and later adding reflection-based escape routes defeats the ownership boundary.'
], ['Do not forget the extension policy of a permitted subtype.', 'Do not use non-sealed while claiming the entire branch is closed.', 'Do not confuse a permitted type with a validated value.'], [('interfaces','Open contracts'),('records','Validated value carriers')], release=17)

add('pattern-switch', 'Java 21 pattern switch: exhaustive branches and null policy',
'A pattern switch selects a branch by a reference value’s type or structure and can bind matched values for use within that branch.',
[('Keep the decision exhaustive', [
'A parcel event is either received or dispatched. The switch covers both permitted records and handles null explicitly. Adding a third permitted variant requires revisiting the decision when it is compiled.',
'The record pattern binds each component directly. This does not validate it; validation belongs at construction or at an input boundary. The sample checks positive parcel IDs in both record constructors.',
'A general type pattern placed before a more specific one can dominate it, making the later branch unreachable. Guarded cases also need an order that reflects their policy. Compiler rejection helps, but a compiling guard can still express the wrong business rule.'
]), ('Null is a separate input choice', [
'A default branch does not automatically make a pattern switch null-safe. This program uses case null to report absent input. Another application may deliberately reject null before switching.',
'Avoid a default that says success when a closed model gains a variant. Exhaustive handling exposes maintenance work at compilation instead of routing an unknown state through a convenient fallback.',
'This syntax is permanent in Java 21. It does not compile with --release 17 or --release 8; choose the matching compiler release rather than removing checks to make a build pass.'
])], r'''public class ParcelEvents {
    sealed interface ParcelEvent permits Received, Dispatched { }
    record Received(long parcelId) implements ParcelEvent {
        Received { if (parcelId <= 0) throw new IllegalArgumentException("Invalid ID"); }
    }
    record Dispatched(long parcelId, String depot) implements ParcelEvent {
        Dispatched { if (parcelId <= 0) throw new IllegalArgumentException("Invalid ID"); }
    }
    static String describe(ParcelEvent event) {
        return switch (event) {
            case null -> "absent";
            case Received(long id) -> "received=" + id;
            case Dispatched(long id, String depot) -> "dispatched=" + id + ":" + depot;
        };
    }
    public static void main(String[] args) {
        System.out.println(describe(new Dispatched(81, "south")));
        System.out.println(describe(null));
    }
}''', 'dispatched=81:south\nabsent', [
'Pattern matching does not deep-copy the components it binds. A mutable component is still the same referenced object. This program’s bound long and String keep that rule simple.',
'Branches are small; text construction dominates this example’s allocation. Do not infer a service-level speed advantage from replacing an if chain alone.'
], ['Do not assume default handles null.', 'Do not place a broad unguarded pattern ahead of its specific cases.', 'Do not use Java 21 syntax while declaring a Java 8 build target.'], [('sealed-classes','Closed variants'),('records','Record components')], release=21)

add('virtual-threads', 'Java 21 virtual threads: blocking tasks still need limits',
'A virtual thread is a Java thread scheduled by the runtime over carrier threads so many blocking tasks can be represented without one dedicated operating-system thread per task.',
[('Concurrency is not admission control', [
'The per-task executor can create a virtual thread for every submitted task. That does not give the downstream database unlimited connections or the service unlimited memory. Bound task admission and downstream access separately.',
'The sample uses three tasks and a semaphore with two permits to describe a downstream budget. A semaphore acquired inside every submitted task bounds active work but does not bound the number of waiting tasks. A large producer still needs an admission cap before submitting.',
'Each task returns a receipt label. Futures are read in submission order so output is deterministic even though execution order is not. This sample contains no remote calls and makes no throughput claim.'
]), ('Blocking and CPU work have different constraints', [
'Virtual threads can help when tasks spend time waiting. They do not add CPU cores. A CPU-bound calculation still consumes compute time, and submitting thousands of such tasks can increase contention.',
'On the Java 21 baseline, blocking while holding certain monitors or during native calls can pin a carrier. Later runtime releases can change that behavior, so do not treat a Java 21 pinning note as a timeless rule.',
'Per-thread state multiplied by many tasks can become a memory issue. Avoid storing large reusable pools inside every thread-local value. The executor in this program is owned by the method and closed before it returns.'
])], r'''import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.Semaphore;

public class ReceiptWorkers {
    public static void main(String[] args) throws Exception {
        Semaphore downstream = new Semaphore(2);
        List<Future<String>> receipts = new ArrayList<>();
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int index = 1; index <= 3; index++) {
                final int receiptId = index;
                receipts.add(executor.submit(() -> {
                    downstream.acquire();
                    try { return "receipt-" + receiptId; }
                    finally { downstream.release(); }
                }));
            }
            for (Future<String> receipt : receipts) System.out.println(receipt.get());
        }
    }
}''', 'receipt-1\nreceipt-2\nreceipt-3', [
'Storing n futures requires O(n) retained references plus task state. The semaphore bounds simultaneous access to two permits; it does not reduce retained waiting work to O(1).',
'Failure and cancellation need a policy. Future.get may report a task failure, and closing an executor waits for owned tasks. A long-lived service needs deadlines and interruption-aware operations rather than relying on a demo’s short tasks.'
], ['Do not describe virtual threads as faster CPU execution.', 'Do not pool virtual threads to imitate a platform-thread pool.', 'Do not mistake a semaphore inside tasks for a bounded submission queue.'], [('executors','Bounded worker admission'),('threads','Visibility and shared state')], release=21)

add('maven', 'Java Maven builds: compiler release and dependency scope',
'Maven builds a project from its POM, lifecycle phases, dependency coordinates, and plugin configuration rather than from an IDE’s private settings.',
[('Make the compiler contract visible', [
'Running Maven on Java 21 does not mean the artifact should require Java 21. Set maven.compiler.release to the intended target. The compiler then checks syntax and platform APIs for that release, not just bytecode format.',
'Keep application sources in src/main/java and tests in src/test/java. A clean command-line build catches missing dependencies that an IDE may have cached or supplied through a local configuration.',
'The project below deliberately targets Java 21 because the modern examples use that release. A Java 8 application should choose release 8 and omit APIs unavailable there. See <a href="/java/pattern-switch">pattern switch</a> for a feature that requires 21.'
]), ('Separate test and runtime needs', [
'JUnit belongs in test scope for this application. The H2 driver belongs at runtime because JDBC source imports standard Java types while DriverManager still needs the driver when connecting. A dependency scope is a packaging and classpath decision, not a security boundary.',
'Pin plugin and dependency versions so a review can reproduce the intended build inputs. The following versions are the tested lesson configuration, not a claim to be the newest releases. Update pins through a tested change.',
'Use mvn test for checks and mvn package for the artifact phase. A normal JAR does not automatically contain every dependency or an executable main entry. Distribution packaging is a separate requirement.'
])], None, None, [
'A first build downloads artifacts and plugins; later builds can use the local repository. Cache size and network latency affect build time, so one warm local result is not a portable build-time estimate.',
'Commit source and build definitions, not generated target output. A clean checkout should be able to reconstruct the artifact from declared inputs. Credentials belong outside the POM.'
], ['Do not depend on an undeclared IDE classpath.', 'Do not confuse the JDK running Maven with the compiler release.', 'Do not claim a normal JAR bundles all dependencies.'], [('junit-tests','Executable tests'),('jdbc-prepared','Runtime database driver')], release=21)
pom = '''<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>in.aitrove</groupId><artifactId>java-lesson-checks</artifactId><version>1.0.0</version>
  <properties><maven.compiler.release>21</maven.compiler.release><project.build.sourceEncoding>UTF-8</project.build.sourceEncoding></properties>
  <dependencies>
    <dependency><groupId>org.junit.jupiter</groupId><artifactId>junit-jupiter</artifactId><version>5.11.0</version><scope>test</scope></dependency>
    <dependency><groupId>com.h2database</groupId><artifactId>h2</artifactId><version>2.3.232</version><scope>runtime</scope></dependency>
  </dependencies>
  <build><plugins>
    <plugin><groupId>org.apache.maven.plugins</groupId><artifactId>maven-compiler-plugin</artifactId><version>3.13.0</version></plugin>
    <plugin><groupId>org.apache.maven.plugins</groupId><artifactId>maven-surefire-plugin</artifactId><version>3.5.2</version></plugin>
  </plugins></build>
</project>'''
by_path['java/maven']['body'] = by_path['java/maven']['body'].replace('<h2>Cost and design choices</h2>', '<h2>pom.xml</h2>'+block(pom,'xml')+'<h2>Run from the project directory</h2>'+block('mvn test\nmvn package','bash')+'<h2>Cost and design choices</h2>')

add('junit-tests', 'Java JUnit tests: boundary cases and observable contracts',
'A unit test calls a bounded piece of code with controlled inputs and asserts observable results or failures against its contract.',
[('Select tests from the contract', [
'A price rule subtracts a permitted discount from a nonnegative subtotal. Test zero, a full discount, a normal discount, and rejected negative or excessive discounts. Those cases distinguish policy boundaries rather than mirroring private implementation steps.',
'The test class contains a small rule so it compiles as one file. In a real project, move the rule into src/main/java and keep this class in src/test/java. Use the <a href="/java/maven">tested Maven POM</a> with JUnit Jupiter 5.11.0.',
'assertThrows verifies the failure type. Inspect the returned exception only when a message or structured field is part of the public contract. A test tied to incidental punctuation becomes noisy without protecting behavior.'
]), ('Avoid false confidence from a happy path', [
'No test here uses sleeps, a network, a clock, or a production database. That keeps the unit test’s inputs controlled. JDBC and HTTP adapters need separate integration tests to cover their real environment.',
'A branch count or coverage percentage cannot establish correctness. Ask whether an incorrect implementation could still satisfy the assertions. A price rule returning the subtotal unchanged would fail the normal-discount test.',
'Use fresh mutable state for each test. Shared state can make results depend on test execution order, concealing a failure when a developer runs only one test.'
])], r'''import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

public class PriceRuleTest {
    static long payable(long subtotal, long discount) {
        if (subtotal < 0 || discount < 0 || discount > subtotal) {
            throw new IllegalArgumentException("Invalid price inputs");
        }
        return subtotal - discount;
    }
    @Test void appliesDiscount() { assertEquals(850, payable(1000, 150)); }
    @Test void acceptsZero() { assertEquals(0, payable(0, 0)); }
    @Test void acceptsFullDiscount() { assertEquals(0, payable(1000, 1000)); }
    @Test void rejectsNegativeSubtotal() {
        assertThrows(IllegalArgumentException.class, () -> payable(-1, 0));
    }
    @Test void rejectsNegativeDiscount() {
        assertThrows(IllegalArgumentException.class, () -> payable(100, -1));
    }
    @Test void rejectsExcessDiscount() {
        assertThrows(IllegalArgumentException.class, () -> payable(100, 101));
    }
}''', None, [
'Each test evaluates a constant-time rule. The test runner still has discovery and startup costs. Keep performance benchmarks separate from correctness assertions.',
'This subtraction cannot overflow because validation restricts both operands to nonnegative values with discount no larger than subtotal. That proof is stronger than a comment claiming long can never overflow.'
], ['Do not use Java assert for checks unless the execution deliberately enables assertions.', 'Do not make tests depend on order or shared mutable fixtures.', 'Do not substitute mocked database success for a real transaction test.'], [('exceptions','Failure contracts'),('maven','Test execution configuration')], release=21, dependency='junit')

add('stack-brackets', 'Java stack algorithm: validate nested delimiters',
'A last-in-first-out stack tracks unfinished openings so each closing delimiter can be checked against the most recent unmatched opening.',
[('State the input grammar', [
'The validator accepts only six delimiter characters: parentheses, brackets, and braces. An unexpected character throws rather than silently disappearing. This is a delimiter validator, not a Java parser; a quote or comment needs a separate lexical rule.',
'For an opening token, push the required closing token. For a closing token, the stack must be nonempty and its top must match. This representation avoids a separate mapping lookup at every close.',
'If the final stack is nonempty, the input contains openings with no closing partner. An empty input is valid under this grammar. Those cases are part of the contract, not afterthoughts.'
]), ('Preserve nesting, not just counts', [
'The input ([)] has equal opening and closing counts but incorrect nesting. A pair of counters cannot detect that defect. The stack records the order of pending obligations.',
'Use <a href="/java/arraydeque">ArrayDeque</a> through the Deque contract. Its push and pop operate at the same end. Mixing push with removeLast changes the policy to a different order.'
])], r'''import java.util.ArrayDeque;
import java.util.Deque;

public class DelimiterValidator {
    static boolean valid(String delimiters) {
        Deque<Character> expected = new ArrayDeque<>();
        for (int index = 0; index < delimiters.length(); index++) {
            char token = delimiters.charAt(index);
            switch (token) {
                case '(': expected.push(')'); break;
                case '[': expected.push(']'); break;
                case '{': expected.push('}'); break;
                case ')': case ']': case '}':
                    if (expected.isEmpty() || expected.pop() != token) return false;
                    break;
                default: throw new IllegalArgumentException("Unsupported token");
            }
        }
        return expected.isEmpty();
    }
    public static void main(String[] args) {
        System.out.println(valid("{[()]}"));
        System.out.println(valid("([)]"));
        System.out.println(valid(""));
    }
}''', 'true\nfalse\ntrue', [
'Each of n tokens is examined once. Deque endpoint operations give amortised O(n) total work. The maximum outstanding nesting depth d requires O(d) stored entries, with O(n) as the worst-case bound.',
'Reject excessively long input at the entry point when memory has a fixed budget. Replacing recursion with a heap-backed stack avoids call-stack exhaustion but does not remove the storage requirement.'
], ['Do not validate nesting using counts alone.', 'Do not pop an empty stack.', 'Do not claim this handles delimiters inside arbitrary source-code strings.'], [('arraydeque','Stack storage'),('graph-dfs','Explicit traversal stack')], 'java-dsa')

add('tree-traversal', 'Java binary-tree traversal: iterative inorder',
'Inorder traversal visits a binary tree’s left subtree, then its node, then its right subtree; sorted output requires a separate binary-search-tree ordering invariant.',
[('Store the suspended path', [
'The explicit stack stores ancestors whose left subtree is being visited. Once no left child remains, pop the next node, consume it, and move into its right subtree. That replaces the suspended recursive frames with visible data.',
'The program constructs a search tree of depot IDs and prints inorder output. The traversal itself does not verify the search-tree invariant. Moving a larger ID into the left branch would produce a different order without causing an algorithm error.',
'A null root represents an empty tree. The loop exits immediately. Shared nodes or cycles are not part of this tree contract; a graph requires visited-state tracking.'
]), ('Height controls the workspace', [
'A balanced tree has a short root-to-leaf path. A chain-shaped tree can be as tall as its node count. The explicit stack handles that case without recursive Java calls, but it can still require linear storage.',
'Traversal does not balance the tree or speed up future searches. Insertion rules and rebalancing algorithms belong to separate lessons. This implementation teaches visitation order only.'
])], r'''import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;

public class DepotTree {
    static final class Node {
        final int depotId;
        Node left, right;
        Node(int depotId) { this.depotId = depotId; }
    }
    static List<Integer> inorder(Node root) {
        List<Integer> ordered = new ArrayList<>();
        Deque<Node> pending = new ArrayDeque<>();
        Node current = root;
        while (current != null || !pending.isEmpty()) {
            while (current != null) { pending.push(current); current = current.left; }
            current = pending.pop();
            ordered.add(current.depotId);
            current = current.right;
        }
        return ordered;
    }
    public static void main(String[] args) {
        Node root = new Node(40);
        root.left = new Node(20); root.right = new Node(60);
        root.left.right = new Node(30);
        System.out.println(inorder(root));
        System.out.println(inorder(null));
    }
}''', '[20, 30, 40, 60]\n[]', [
'Every node is pushed and popped once, so traversal takes O(n) work. The pending stack takes O(h) references for height h. Returning all IDs also requires O(n) result storage; do not omit that from the total allocation estimate.',
'A consumer callback could avoid storing the whole result, but it would add failure and side-effect contracts. Decide whether partial output is acceptable before switching representations.'
], ['Do not claim inorder sorts an arbitrary binary tree.', 'Do not include null in an ArrayDeque.', 'Do not assume every tree has logarithmic height.'], [('recursion','Call-stack tradeoffs'),('binary-search','Ordered search')], 'java-dsa')

add('graph-bfs', 'Java breadth-first search: shortest unweighted distances',
'Breadth-first search visits reachable vertices in layers using a queue, yielding shortest edge-count distances when every edge has equal cost.',
[('Mark a vertex when enqueuing it', [
'A delivery graph contains cycles and repeated routes. Assign a distance before adding a discovered vertex to the queue. Otherwise two parents could enqueue the same vertex before either removes it for processing.',
'The input is a directed adjacency list with integer vertex IDs from zero through length minus one. The helper rejects invalid source and neighbour IDs. An unreachable vertex retains distance -1.',
'BFS answers minimum hop count. It does not answer the fastest route when edges carry different travel times. A weighted shortest-path algorithm needs a different relaxation and ordering policy.'
]), ('Representation is part of the cost', [
'An adjacency list lets the loop examine only outgoing edges of visited vertices. An adjacency matrix would require scanning a row across all possible vertices even when few routes exist.',
'Distance is enough for hop counts. Reconstructing a path needs a predecessor array recorded when each vertex is first discovered. If several shortest paths exist, neighbour order decides which predecessor is seen first.'
])], r'''import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Deque;

public class DeliveryHops {
    static int[] distances(int[][] routes, int source) {
        if (source < 0 || source >= routes.length) throw new IllegalArgumentException("Invalid source");
        int[] distance = new int[routes.length];
        Arrays.fill(distance, -1);
        Deque<Integer> pending = new ArrayDeque<>();
        distance[source] = 0; pending.addLast(source);
        while (!pending.isEmpty()) {
            int depot = pending.removeFirst();
            for (int next : routes[depot]) {
                if (next < 0 || next >= routes.length) throw new IllegalArgumentException("Invalid route");
                if (distance[next] == -1) {
                    distance[next] = distance[depot] + 1;
                    pending.addLast(next);
                }
            }
        }
        return distance;
    }
    public static void main(String[] args) {
        int[][] routes = {{1, 2}, {3}, {3}, {0}, {}};
        System.out.println(Arrays.toString(distances(routes, 0)));
    }
}''', '[0, 1, 1, 2, -1]', [
'For V vertices and E adjacency entries, the distance-array setup plus traversal takes O(V + E) in the worst case. The queue and distance array require O(V) extra storage. Input adjacency storage is separate.',
'The helper validates neighbours as it encounters them. Unreachable invalid adjacency entries are not visited. A fully validated reusable graph should check every row once at construction.'
], ['Do not mark visited only after dequeueing.', 'Do not use DFS to claim minimum-hop distances.', 'Do not apply unweighted BFS directly to unequal travel costs.'], [('arraydeque','Queue operations'),('graph-dfs','Depth-first reachability')], 'java-dsa')

add('graph-dfs', 'Java depth-first search: cycles and explicit work stacks',
'Depth-first search explores reachable vertices through a last-in-first-out work stack or recursive calls, with visited state preventing repeated exploration of cycles.',
[('Reachability is the promised result', [
'A dependency graph asks which modules can be reached from a starting module. The sample counts them. It does not produce a topological order or prove the graph acyclic.',
'Mark a vertex before pushing it so pending work contains at most one entry per discovered vertex. The resulting visit order can differ from a recursive implementation because neighbours are scheduled together; reachability is unchanged.',
'Directed cycles are allowed. A simple visited flag skips a previously discovered vertex, but cycle detection needs more information when it must distinguish an edge into the active path from an edge into a completed branch.'
]), ('Avoid recursion for unbounded depth', [
'A long chain can exhaust a Java thread’s call stack in a recursive traversal. An explicit deque moves pending state to ordinary heap storage. It still needs a memory budget; it is not an unlimited traversal.',
'The graph is assumed structurally stable during the call. Mutating adjacency rows while traversing changes the input contract and can make results timing-dependent.'
])], r'''import java.util.ArrayDeque;
import java.util.Deque;

public class DependencyReachability {
    static int reachable(int[][] dependencies, int source) {
        if (source < 0 || source >= dependencies.length) throw new IllegalArgumentException("Invalid source");
        boolean[] discovered = new boolean[dependencies.length];
        Deque<Integer> pending = new ArrayDeque<>();
        pending.push(source); discovered[source] = true;
        int count = 0;
        while (!pending.isEmpty()) {
            int module = pending.pop(); count++;
            for (int next : dependencies[module]) {
                if (next < 0 || next >= dependencies.length) throw new IllegalArgumentException("Invalid edge");
                if (!discovered[next]) { discovered[next] = true; pending.push(next); }
            }
        }
        return count;
    }
    public static void main(String[] args) {
        int[][] dependencies = {{1}, {2}, {0, 3}, {}, {}};
        System.out.println(reachable(dependencies, 0));
    }
}''', '4', [
'Visited-state initialization and adjacency scanning require O(V + E) worst-case work and O(V) extra storage. For a sparse reachable component, edge scanning is limited to that component, while the boolean array still covers all vertices.',
'Counting reachability does not retain a full traversal result. Adding a result list or predecessor structure adds its own memory cost and output semantics.'
], ['Do not omit visited state on a cyclic graph.', 'Do not describe this count as a topological ordering.', 'Do not assume its work-stack order is identical to recursive DFS.'], [('graph-bfs','Minimum-hop traversal'),('recursion','Stack depth')], 'java-dsa')

add('merge-sort', 'Java merge sort: stable merging and one scratch buffer',
'Merge sort recursively sorts adjacent ranges and combines them through an ordered merge, with stability determined by how equal elements are selected.',
[('Use half-open ranges', [
'Each range starts at from and ends before to. A range with fewer than two values is already sorted. The midpoint splits it into disjoint left and right ranges with no omitted index.',
'Merge reads two sorted inputs and writes the smaller pending value. On equality, choosing the left element first preserves the relative order of equal keys. The integer example cannot display record identity, but the tie rule is the same for a stable record comparator.',
'Allocate scratch storage once for the whole sort. Creating fresh subarrays at every level obscures allocation cost and makes it harder to compare the implementation with a production sort.'
]), ('State mutation explicitly', [
'sort changes the caller’s array. Copy first if readers require the original order. Returning void makes the mutation visible in the signature, but the method’s documentation must still state it.',
'The sample handles empty arrays and repeated values. Null is outside its contract and fails immediately when length is accessed. A public API may prefer an explicit null check for a clearer error.'
])], r'''import java.util.Arrays;

public class ShipmentMergeSort {
    static void sort(int[] shipmentIds) {
        split(shipmentIds, new int[shipmentIds.length], 0, shipmentIds.length);
    }
    static void split(int[] values, int[] scratch, int from, int to) {
        if (to - from < 2) return;
        int middle = from + (to - from) / 2;
        split(values, scratch, from, middle); split(values, scratch, middle, to);
        int left = from, right = middle, output = from;
        while (left < middle && right < to) {
            scratch[output++] = values[left] <= values[right] ? values[left++] : values[right++];
        }
        while (left < middle) scratch[output++] = values[left++];
        while (right < to) scratch[output++] = values[right++];
        System.arraycopy(scratch, from, values, from, to - from);
    }
    public static void main(String[] args) {
        int[] shipmentIds = {42, 11, 42, 8, 30};
        sort(shipmentIds);
        System.out.println(Arrays.toString(shipmentIds));
        int[] empty = {}; sort(empty); System.out.println(Arrays.toString(empty));
    }
}''', '[8, 11, 30, 42, 42]\n[]', [
'Each level merges and copies O(n) elements; the split depth is O(log n). Total work is O(n log n), with O(n) scratch storage and O(log n) recursive frames.',
'Use the standard <a href="/java/sorting">sorting API</a> for ordinary application work unless custom requirements justify maintaining an algorithm. This version teaches the merge invariant, not a claim to beat library implementations.'
], ['Do not mix inclusive and exclusive end indexes.', 'Do not choose the right equal element while claiming stability.', 'Do not omit scratch storage from the space bound.'], [('sorting','Library sort contracts'),('recursion','Recursive decomposition')], 'java-dsa')

add('memoization', 'Java memoization: minimum package count and cached subproblems',
'Memoization stores a subproblem’s computed result so repeated requests for the same state reuse it instead of exploring its dependencies again.',
[('Define a state before caching it', [
'A shipping planner asks for the fewest packages that sum exactly to a target weight using allowed positive package sizes. The state is the remaining weight. A result of -1 means impossible; -2 means not computed.',
'For each usable size, solve the smaller remaining weight and keep the smallest successful count plus one. The zero-weight state returns zero packages. Positive sizes prove progress; a zero size would recurse into the same state forever.',
'The helper validates every size at the entry point. It also rejects negative targets. That keeps the recursive method focused on states already known to be valid.'
]), ('The cache belongs to one input policy', [
'Changing package sizes changes the meaning of every cached remaining-weight result. The sample creates a fresh cache for each call so results cannot leak across different policies.',
'This recursive implementation is useful for understanding repeated states, but large targets can exhaust the call stack. A bottom-up tabulation uses the same state relation without recursive frames.',
'The target value controls storage and work, not merely the number of digits needed to represent it. A large numeric input requires an admission limit even if parsing it is cheap.'
])], r'''import java.util.Arrays;

public class PackagePlanner {
    static int minimumPackages(int target, int[] sizes) {
        if (target < 0) throw new IllegalArgumentException("Negative target");
        for (int size : sizes) if (size <= 0) throw new IllegalArgumentException("Sizes must be positive");
        int[] cache = new int[Math.addExact(target, 1)];
        Arrays.fill(cache, -2); cache[0] = 0;
        return solve(target, sizes, cache);
    }
    static int solve(int remaining, int[] sizes, int[] cache) {
        if (cache[remaining] != -2) return cache[remaining];
        int best = Integer.MAX_VALUE;
        for (int size : sizes) {
            if (size > remaining) continue;
            int previous = solve(remaining - size, sizes, cache);
            if (previous >= 0) best = Math.min(best, previous + 1);
        }
        return cache[remaining] = best == Integer.MAX_VALUE ? -1 : best;
    }
    public static void main(String[] args) {
        System.out.println(minimumPackages(10, new int[]{3, 5}));
        System.out.println(minimumPackages(7, new int[]{3, 5}));
        System.out.println(minimumPackages(0, new int[]{3, 5}));
    }
}''', '2\n-1\n0', [
'For target W and K sizes, at most W + 1 states each inspect K sizes, giving O(WK) worst-case work. The cache uses O(W) integers. Recursive depth can also reach O(W) when size 1 is allowed.',
'A greedy choice of the largest fitting size is not correct for every package set. For sizes 1, 3, and 4 with target 6, two size-3 packages beat 4 plus two size-1 packages. A recurrence needs a proof; a plausible local choice is insufficient.'
], ['Do not use the same sentinel for impossible and uncomputed.', 'Do not admit zero or negative package sizes.', 'Do not promise this scales to arbitrary target integers.'], [('recursion','Progress and base cases'),('arrays','Cache storage')], 'java-dsa')

add('collections-exercises', 'Java collection exercises: counters, duplicates, and stable output',
'A collection exercise defines input, identity, ordering, and output rules before choosing a container or writing a loop.',
[('Task 1: count receipt states', [
'Given paid, pending, paid, declined, pending, produce the count for each state in first-seen order. Use a map whose encounter order is part of its contract. Empty input must produce an empty map, and this task rejects null or blank states.',
'Write the loop before reading the answer. A successful solution should not rely on HashMap happening to print in the desired order. Test repeated values separated by other values, not only consecutive duplicates.'
]), ('Task 2: detect duplicates without losing the rule', [
'Return the number of events beyond the first occurrence of each receipt ID. The IDs r-8, r-9, r-8, r-8 should yield two duplicates. A set records membership; it does not keep an event count unless you track that count separately.',
'Decide whether IDs are case-sensitive and whether whitespace is meaningful. This solution uses exact String equality. Normalization must be an explicit upstream rule, not a side effect introduced to make a test pass.'
]), ('Task 3: reason about the collection choice', [
'Explain why a LinkedList scanned by repeated indexed get can cost quadratic traversal. Explain why a PriorityQueue’s iterator does not give sorted output. These questions test operation contracts, not the ability to recite container names.',
'The complete answer below solves the first two tasks. Extend it with empty inputs, all-distinct inputs, and a rejected null value. The <a href="/java/linkedlist-exercises">LinkedList exercise set</a> covers endpoint behavior separately.'
])], r'''import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class ReceiptCollectionTasks {
    static Map<String, Integer> counts(List<String> states) {
        Map<String, Integer> result = new LinkedHashMap<>();
        for (String state : states) {
            if (state == null || state.trim().isEmpty()) throw new IllegalArgumentException("State required");
            result.merge(state, 1, Integer::sum);
        }
        return result;
    }
    static int duplicates(List<String> ids) {
        Set<String> seen = new HashSet<>();
        int duplicates = 0;
        for (String id : ids) {
            if (id == null) throw new IllegalArgumentException("ID required");
            if (!seen.add(id)) duplicates++;
        }
        return duplicates;
    }
    public static void main(String[] args) {
        System.out.println(counts(Arrays.asList("paid", "pending", "paid", "declined", "pending")));
        System.out.println(duplicates(Arrays.asList("r-8", "r-9", "r-8", "r-8")));
    }
}''', '{paid=2, pending=2, declined=1}\n2', [
'Each task requires expected O(n) work for bounded-length, well-distributed String keys. The map or set stores O(k) distinct keys. Hashing and equality costs still depend on text length.',
'The duplicate count is process-local and bounded by the input list. It is not a durable exactly-once guarantee for external payments. A production ingestion path needs a separate persistence contract.'
], ['Do not let accidental map iteration order satisfy the requirement.', 'Do not confuse duplicate IDs with distinct duplicated keys.', 'Do not mutate collection keys after insertion.'], [('linkedhashmap','Encounter order'),('hashset','Membership'),('priorityqueue','Removal order')], 'java-exercises')

add('object-interview', 'Java object interview questions: references, equality, and constructors',
'An object-model interview answer should distinguish reference values, object state, dispatch, and equality rather than treating them as one concept.',
[('Does assignment copy an object?', [
'No. Assigning a reference gives another variable a reference value to the same object. Mutating that object through either route can be observed through the other. Reassigning one variable changes only that variable.',
'Follow-up: what does an array copy do? It copies primitive values or element references. For a list of mutable receipt objects, copying the list structure still shares those receipt objects. State which ownership boundary is required before proposing a copy.'
]), ('Can a final reference point to mutable state?', [
'Yes. final prevents reassigning that variable after initialization; it does not freeze the referenced collection. The probe below changes a list through a final reference and prints the resulting size.',
'Follow-up: when does an unmodifiable view change? It can reflect writes performed through another reference to its backing collection. A detached structural snapshot has a different contract.'
]), ('What breaks a hash key?', [
'Changing equality-relevant state after insertion can make lookup fail or create a logically inconsistent key set. The map uses the key’s hash and equality during its operations; it does not monitor arbitrary field writes.',
'Follow-up: should two separately loaded receipts be equal? That is a domain rule, usually based on a stable identifier or immutable value components. Default Object equality uses identity. Read <a href="/java/equals-hashcode">the key contract</a>.'
]), ('Why avoid overridable constructor calls?', [
'Dispatch can enter subclass code before subclass initialization has completed. The call may observe defaults instead of established invariants. The repair is to stop exposing a partially built object, not to add a sleep.',
'Follow-up: does an abstract class enforce immutability? No. It can define a construction and method contract, but mutable references and exposed setters remain independent design choices.'
])], r'''import java.util.ArrayList;
import java.util.List;

public class ReferenceInterviewProbe {
    static void replace(List<String> receipts) { receipts = new ArrayList<>(); }
    static void append(List<String> receipts) { receipts.add("r-72"); }
    public static void main(String[] args) {
        final List<String> receipts = new ArrayList<>();
        receipts.add("r-41");
        replace(receipts);
        append(receipts);
        System.out.println(receipts);
        System.out.println(receipts.size());
    }
}''', '[r-41, r-72]\n2', [
'The reassignment creates a temporary empty list but does not replace the caller’s reference. The append mutates the shared list. This explains behavior through ownership, without a claim that Java passes objects by reference.',
'A good answer includes the observable result and the rule that causes it. Exact byte sizes and speculative VM optimizations are unnecessary for this reference question.'
], ['Do not say Java passes objects by reference.', 'Do not equate final with deep immutability.', 'Do not promise content equality from Object.equals.'], [('pass-by-value','Reference mutation'),('constructors','Initialization boundaries')], 'java-interview')

add('concurrency-interview', 'Java concurrency interview questions: visibility and atomic updates',
'A concurrency answer must separate visibility, atomicity, ordering, and task lifetime because no single keyword supplies every guarantee.',
[('Does volatile make increment atomic?', [
'No. A volatile field supplies visibility and ordering rules for its reads and writes, but count++ is a read-modify-write sequence. Two threads can compute the same next value and lose an increment.',
'A lock can protect a group of related updates. An atomic counter can protect one counter operation. Choosing the smaller tool requires a proof that the invariant really involves only that one value.'
]), ('What does thread-safe collection mean for compound work?', [
'Two individually safe calls do not automatically form one atomic operation. Checking a mapping and then putting a value can race with another writer. Use an operation whose contract covers the needed update, or protect the whole sequence.',
'If a collection returns a mutable value, thread-safe storage of its reference does not make arbitrary mutations of that value safe. Ownership still matters.'
]), ('Does a successful submit mean the task succeeded?', [
'No. Submission admits or rejects work. Future.get observes completion or reports failure. A discarded Future can conceal a task exception from the caller’s normal control flow.',
'Shutdown stops admission under the executor’s contract, but cancellation and interruption are cooperative. A task that ignores interruption can outlive the caller’s desired deadline. <a href="/java/executors">Executor ownership</a> covers the complete lifecycle.'
]), ('Do virtual threads remove backpressure?', [
'No. They change how threads are represented and scheduled, not the capacity of a downstream database or the amount of pending state the application can retain. A producer still needs an admission policy.',
'The probe uses two platform threads and an atomic counter. join waits for their completion before the final read. This deterministic result is a correctness check for these updates, not a contention benchmark.'
])], r'''import java.util.concurrent.atomic.AtomicInteger;

public class CounterInterviewProbe {
    public static void main(String[] args) throws InterruptedException {
        AtomicInteger accepted = new AtomicInteger();
        Runnable worker = () -> {
            for (int receipt = 0; receipt < 1000; receipt++) accepted.incrementAndGet();
        };
        Thread first = new Thread(worker); Thread second = new Thread(worker);
        first.start(); second.start(); first.join(); second.join();
        System.out.println(accepted.get());
    }
}''', '2000', [
'There are 2000 atomic updates. Contention and scheduling determine their elapsed time; the small fixed run cannot rank alternative counter implementations.',
'Integer counters can still overflow. Atomicity prevents lost updates, not range errors or incorrect business accounting.'
], ['Do not propose volatile alone for a compound counter update.', 'Do not discard task failures.', 'Do not treat interruption as forced termination.'], [('threads','Visibility and atomicity'),('virtual-threads','Task admission limits')], 'java-interview')

add('inventory-project', 'Java project: an in-memory stock ledger with validated mutations',
'An in-memory stock ledger owns item quantities and accepts changes only when each resulting balance remains within its declared range.',
[('Define the project boundaries', [
'The ledger supports receive, dispatch, and read-only snapshot operations. Item IDs must be nonblank, quantities must be positive, dispatch cannot create a negative balance, and arithmetic overflow rejects the operation.',
'This is a runnable single-process project. It contains no database, authentication, concurrent writers, or event history. Restarting the program loses the ledger. Those limits belong in the project definition before anyone depends on it.',
'Use a TreeMap for predictable item ordering in the snapshot. That is a display contract, not a requirement that every stock system use sorted storage.'
]), ('Reject before changing state', [
'receive computes the checked new quantity before put. dispatch checks the current quantity before subtracting. A failed mutation leaves the existing balance intact.',
'The snapshot copies the map and then wraps the copy as unmodifiable. Returning a wrapper around the original map would expose later internal changes to an earlier reader. Integers and Strings keep this snapshot structurally and element-wise safe for this use.'
]), ('Acceptance checks and next extensions', [
'Run the program to receive ten units, dispatch three, attempt an excessive dispatch, and print the unchanged balance after rejection. Then add tests for unknown items, zero units, blank IDs, and overflow.',
'A persistence extension should commit changes transactionally. A concurrent extension needs one owner or an atomic operation across the balance rule. Adding a concurrent map alone does not make read-check-write atomic.'
])], r'''import java.util.Collections;
import java.util.Map;
import java.util.TreeMap;

public class StockLedgerProject {
    static final class Ledger {
        private final Map<String, Integer> quantities = new TreeMap<>();
        private void validate(String item, int units) {
            if (item == null || item.trim().isEmpty() || units <= 0) {
                throw new IllegalArgumentException("Item and positive units required");
            }
        }
        void receive(String item, int units) {
            validate(item, units);
            int updated = Math.addExact(quantities.getOrDefault(item, 0), units);
            quantities.put(item, updated);
        }
        void dispatch(String item, int units) {
            validate(item, units);
            int available = quantities.getOrDefault(item, 0);
            if (units > available) throw new IllegalArgumentException("Insufficient stock");
            quantities.put(item, available - units);
        }
        Map<String, Integer> snapshot() {
            return Collections.unmodifiableMap(new TreeMap<>(quantities));
        }
    }
    public static void main(String[] args) {
        Ledger ledger = new Ledger();
        ledger.receive("packing-tape", 10); ledger.dispatch("packing-tape", 3);
        Map<String, Integer> saved = ledger.snapshot();
        try { ledger.dispatch("packing-tape", 8); }
        catch (IllegalArgumentException expected) { System.out.println("rejected"); }
        ledger.receive("packing-tape", 2);
        System.out.println("saved=" + saved);
        System.out.println("current=" + ledger.snapshot());
    }
}''', 'rejected\nsaved={packing-tape=7}\ncurrent={packing-tape=9}', [
'Each map lookup or update costs O(log k) comparisons for k items. The snapshot copies k entries and requires O(k) new storage. Text comparison costs depend on item ID length.',
'Snapshots have a real cost. A large high-frequency reader may need another publication design, but that change must preserve a defined ownership and consistency contract.'
], ['Do not claim the ledger survives a restart.', 'Do not return a live internal map as a snapshot.', 'Do not use unsynchronized read-check-write with concurrent callers.'], [('treemap','Ordered storage'),('junit-tests','Boundary tests'),('jdbc-transactions','Persisted atomic changes')], 'java-projects')

add('collections-cheatsheet', 'Java collections cheatsheet: operation contracts and failure cases',
'A collection choice is a choice of ordering, equality, access cost, ownership, and failure behavior rather than a preference for a class name.',
[('Lists and deques', [
'<a href="/java/arraylist">ArrayList</a> gives constant-time indexed access and amortised constant-time append. Inserting near the front shifts references. Removing by value still requires finding that value.',
'<a href="/java/linkedlist">LinkedList</a> gives constant-time endpoint edits, but finding an indexed position requires traversal. An insertion through an already positioned iterator has a different cost from an indexed insertion.',
'<a href="/java/arraydeque">ArrayDeque</a> is a common single-threaded stack or queue choice. It rejects null. poll returns null on an empty deque; remove throws. Choose the absence contract deliberately.'
]), ('Maps, sets, and ordering', [
'<a href="/java/hashmap">HashMap</a> has no encounter-order promise. <a href="/java/linkedhashmap">LinkedHashMap</a> defines encounter behavior. <a href="/java/treemap">TreeMap</a> orders by keys and provides range queries.',
'HashSet uses equality and hashing for membership. Mutating an equality-relevant field of a stored key or element breaks the lookup assumption. Tree-based keys use comparison equivalence to decide uniqueness.',
'<a href="/java/priorityqueue">PriorityQueue</a> removes according to priority, but iterating it does not sort all elements. Repeated poll changes the queue; copy it if the original must remain intact.'
]), ('Iteration and snapshots', [
'Use Iterator.remove only when that iterator’s contract supports removal. A fail-fast exception is a bug signal, not a guaranteed concurrent-change detector or a synchronization mechanism.',
'An unmodifiable view can still reflect backing-store edits. A copied collection separates the structure but may share mutable elements. State which layer is copied.',
'Thread-safe individual operations do not automatically make a check-then-act sequence safe. A compound invariant needs a compound operation or a synchronization owner.'
])], None, None, [
'Expected hashing bounds assume usable hash distribution and bounded key costs. Ordered structures include comparison work. Always count the search needed to reach an edit position.',
'This reference lists major contracts covered by the library. Specialized concurrent, blocking, weak-reference, and immutable-collection APIs remain separate study areas.'
], ['Do not infer ordering from a small sample printout.', 'Do not omit the cost of reaching an insertion point.', 'Do not claim an unmodifiable view is a detached deep copy.'], [('collection-choices','Choose by operation'),('iterators','Edit while traversing')], 'java-cheatsheet')

def quiz(slug, title, questions):
    path = 'quizzes/' + slug
    entry = copy.deepcopy(by_path['quizzes/java-basics'])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),path=path,title=title,summary='Check operation contracts and explain the failure cases.',subject='java-quizzes',body=p('This Java quiz checks API contracts, ownership, and failure cases through a local self-check; answers are not submitted to a server.'),featured=False,status='published')
    entry['data'] = {'questions':[dict(prompt=q[0],options=q[1],answer=q[2],explanation=q[3]) for q in questions], 'duration_minutes':12,'content_format':'html','subject_root':'java/java','section_path':'java/java-quizzes'}
    if path in by_path: by_path[path].update(entry)
    else: entries.append(entry);by_path[path]=entry
    new.append(path)

quiz('java-collections','Java collections contract quiz',[
 ('Which collection contract supplies key ordering and floorEntry?', ['HashMap','TreeMap','ArrayList'],1,'TreeMap implements NavigableMap and supplies key-order and nearest-key operations.'),
 ('What does PriorityQueue iteration guarantee?', ['Sorted values','Removal-priority order','No sorted traversal guarantee'],2,'Priority governs removals; its iterator is not a sorted traversal.'),
 ('What is the worst-case total traversal cost of get(i) for every index of a LinkedList?', ['O(n)','O(n log n)','O(n²)'],2,'Each indexed access can traverse nodes. Repeating it across all positions accumulates quadratic traversal.'),
 ('Which collection rejects null elements?', ['LinkedList','ArrayDeque','HashSet'],1,'ArrayDeque rejects null; its polling methods use null to represent an empty result.'),
 ('What does a TreeMap subMap ordinarily return?', ['A backed range view','An independent deep copy','An immutable serialization'],0,'The view shares mappings with the original map and restricts its key range.'),
 ('A HashMap key changes a field used by hashCode after insertion. What can happen?', ['Lookup can fail','The map automatically reindexes it','The change is rejected'],0,'The map does not monitor arbitrary key mutation and repair bucket placement.'),
 ('What does HashSet.add return for an already present equal value?', ['true','false','The old element'],1,'false reports that the set did not acquire a new distinct element.'),
 ('Does an unmodifiable list wrapper freeze another reference to its backing list?', ['Yes','No','Only for Strings'],1,'The wrapper restricts operations through itself; a writer holding the backing list can still modify it.'),
 ('Why choose LinkedHashMap for first-seen output order?', ['It defines encounter order','It sorts every key','It prevents all concurrent races'],0,'Its encounter-order contract matches that output requirement; it does not provide key sorting or general concurrency control.')])
quiz('java-advanced','Java runtime and concurrency quiz',[
 ('Does volatile make count++ atomic?', ['Yes','No','Only for int'],1,'Increment contains a read, calculation, and write. Visibility is not a compound-update guarantee.'),
 ('Which annotation retention supports ordinary runtime reflection?', ['SOURCE','CLASS','RUNTIME'],2,'RUNTIME keeps annotation metadata available to runtime annotation readers.'),
 ('What does InvocationTargetException represent?', ['The target method threw','A missing compiler','A sorted result'],0,'It wraps an exception thrown by the invoked method; inspect its cause.'),
 ('Does garbage collection promptly close a JDBC connection?', ['Yes','No','Only with System.gc'],1,'Connection lifetime requires explicit ownership and close; collection is not a prompt resource policy.'),
 ('What may a JDBC placeholder bind?', ['A value','A table name','Any SQL clause'],0,'A parameter supplies a value. SQL grammar and identifiers need an application-owned allowlist policy.'),
 ('What reverses a failed transaction’s uncommitted database writes?', ['rollback','Closing an unrelated client','Retrying only the debit'],0,'Rollback acts on the transaction connection; external effects are outside that database boundary.'),
 ('Does a returned Future prove the task completed successfully?', ['Yes','No','Only for Runnable'],1,'It represents the submitted work. Observing completion can still report failure.'),
 ('Does a semaphore acquired inside every submitted task bound queued task count?', ['Yes','No','Only on virtual threads'],1,'It bounds permit holders, while an unbounded number of tasks may still wait.'),
 ('Which evidence helps identify why an object remains live?', ['A retaining path in a heap analysis','Its variable name','An empty source method'],0,'Reachability through live owners explains retention; source naming does not.')])
quiz('java-modern','Java 17 and 21 feature quiz',[
 ('Are record components automatically deeply immutable?', ['Yes','No','Only when public'],1,'A final reference can reach mutable state. Defensive copying requires an explicit policy.'),
 ('Which baseline compiles this lesson’s record-pattern switch without preview flags?', ['8','17','21'],2,'The record-pattern switch lesson targets Java 21.'),
 ('What does non-sealed do to a permitted subtype?', ['Reopens that extension branch','Makes every subclass final','Deletes the permits list'],0,'The branch allows further ordinary extension rather than restricting all descendants.'),
 ('Does default automatically handle null in a pattern switch?', ['Yes','No','Only with records'],1,'An explicit null case or another null policy is needed.'),
 ('What does List.copyOf do with a null element?', ['Rejects it','Drops it','Converts it to text'],0,'The copied immutable list does not permit null elements.'),
 ('Do virtual threads add CPU cores?', ['Yes','No','Only in a per-task executor'],1,'They alter thread scheduling and representation; CPU capacity remains bounded by the machine.'),
 ('What does maven.compiler.release select?', ['The compiler language and platform API target','Only the Maven download server','The HTTP timeout'],0,'The release setting checks the selected language and supported platform APIs.'),
 ('How do generated record methods treat an array component for equality?', ['As array reference equality','As deep element equality','As a sorted set'],0,'An array component does not acquire element-wise equality simply by appearing in a record.'),
 ('Why avoid a catch-all default for a closed model when exhaustive handling is intended?', ['It can hide work needed for a new variant','It always causes a leak','It makes records mutable'],0,'An exhaustive switch lets the compiler reveal a newly uncovered variant.')])

# Append modules; every path must be published under its owning section.
module_additions = {
 'java/java': [('Text, wrappers, and call boundaries','Own mutable text and make missing values and argument sharing explicit.',['stringbuilder','boxing','varargs']),('Further object structures','Separate shared implementation from enclosing-instance ownership.',['abstract-classes','nested-classes'])],
 'java/advanced-java': [('Metadata and runtime inspection','State what reads metadata and respect member access.',['annotations','reflection']),('Memory and diagnostics','Inspect retaining owners before changing runtime budgets.',['jvm-memory','gc-diagnostics']),('Database and HTTP boundaries','Own query resources, commit decisions, request deadlines, and response size.',['jdbc-prepared','jdbc-transactions','http-client']),('Java 17 and 21','Use version-labelled value types, closed variants, patterns, and virtual threads.',['records','sealed-classes','pattern-switch','virtual-threads']),('Builds and executable tests','Declare compiler targets and run contract-focused assertions.',['maven','junit-tests'])],
 'java/dsa-in-java': [('Stacks, trees, and graphs','Track pending work and distinguish reachability from shortest distance.',['stack-brackets','tree-traversal','graph-bfs','graph-dfs']),('Merging and cached states','Prove progress and count work across all states.',['merge-sort','memoization'])],
 'java/java-exercises': [('Collection contracts','Solve counting and deduplication with explicit ordering.',['collections-exercises'])],
 'java/java-interview-questions': [('Object and concurrency reasoning','Explain ownership, dispatch, visibility, and task completion.',['object-interview','concurrency-interview'])],
 'java/java-projects': [('Validated application state','Run a stock ledger and test rejected mutations.',['inventory-project'])],
 'java/java-cheatsheet': [('Collection decision notes','Check ordering, ownership, costs, and failure behavior.',['collections-cheatsheet'])],
 'java/java-quizzes': [('Foundation quizzes','Start with basic types or check the LinkedList contract.', ['../quizzes/java-basics','../quizzes/java-linkedlist']),('Collections, runtime, and modern Java','Self-check answers with an explanation for each question.', ['../quizzes/java-collections','../quizzes/java-advanced','../quizzes/java-modern'])]
}
for hub_path, additions in module_additions.items():
    hub = by_path[hub_path]
    modules = hub['data'].setdefault('modules', [])
    for title, summary, slugs in additions:
        paths = [slug[3:] if slug.startswith('../') else 'java/'+slug for slug in slugs]
        modules[:] = [module for module in modules if module['title'] != title]
        modules.append(dict(title=title, summary=summary, lessons=paths))
    for index, path in enumerate(path for module in modules for path in module['lessons']):
        assert path in by_path and by_path[path]['subject'] == hub['subject'], (hub_path,path)
        by_path[path]['sort_order'] = index
    hub['updated_at'] = '2026-09-28T12:00:00+00:00'

# Link the new territory from the subject overview as well as the modules.
root = by_path['java/java']
heading = '<h2>Continue beyond the object model</h2>'
if heading not in root['body']:
    root['body'] += heading + p('Use <a href="/java/advanced-java">Advanced Java</a> for runtime inspection, database transactions, HTTP request policies, build tools, tests, and version-labelled Java 17/21 features. Practice <a href="/java/dsa-in-java">graph traversal and cached subproblems</a>, then run the <a href="/java/inventory-project">stock ledger project</a>.')
(ROOT/'src/data/fixtures.json').write_text(json.dumps(entries,indent=2,ensure_ascii=False)+'\n')
java_entries = [e for e in entries if e['path'].startswith('java/') or e['path'].startswith('quizzes/java-')]
curriculum_paths = {e['path'] for e in java_entries if e['type']=='subject'}
for hub in java_entries:
    if hub['type']=='subject': curriculum_paths.update(path for module in hub['data']['modules'] for path in module['lessons'])
assert curriculum_paths == {e['path'] for e in java_entries}, 'Every Java route must appear in the curriculum skeleton'
(OUT/'aitrove-java-content.json').write_text(json.dumps(java_entries,indent=2,ensure_ascii=False)+'\n')
(OUT/'aitrove-preview-content.json').write_text(json.dumps(entries,indent=2,ensure_ascii=False)+'\n')
(OUT/'java-completion-batch.json').write_text(json.dumps({'added':new,'javaPages':len(java_entries),'articles':sum(e['type']=='article' for e in java_entries),'hubs':sum(e['type']=='subject' for e in java_entries),'quizzes':sum(e['type']=='quiz' for e in java_entries)},indent=2)+'\n')

# Dependency-backed examples are checked together with the exact published POM.
project = ROOT/'work/java-lesson-checks'
(project/'src/main/java').mkdir(parents=True,exist_ok=True)
(project/'src/test/java').mkdir(parents=True,exist_ok=True)
(project/'pom.xml').write_text(pom+'\n')
for path in ['java/jdbc-prepared','java/jdbc-transactions','java/junit-tests']:
    entry = by_path[path]
    code = html.unescape(re.search(r'<pre><code class="language-java">([\s\S]*?)</code></pre>',entry['body'])[1])
    name = re.search(r'public class (\w+)',code)[1]
    folder = 'test' if entry['data']['java_dependency']=='junit' else 'main'
    (project/('src/'+folder+'/java')/(name+'.java')).write_text(code+'\n')
(project/'src/test/java/DatabaseLessonsTest.java').write_text('''import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;

public class DatabaseLessonsTest {
    interface CheckedRun { void run() throws Exception; }
    static String output(CheckedRun program) throws Exception {
        ByteArrayOutputStream buffer = new ByteArrayOutputStream();
        PrintStream original = System.out;
        try (PrintStream capture = new PrintStream(buffer, true, StandardCharsets.UTF_8)) {
            System.setOut(capture); program.run();
        } finally { System.setOut(original); }
        return buffer.toString(StandardCharsets.UTF_8).replace("\\r\\n", "\\n").trim();
    }
    @Test void boundQuoteRemainsData() throws Exception {
        assertEquals("paid\\nnull", output(() -> ReceiptLookup.main(new String[0])));
    }
    @Test void failedCreditRollsBackDebit() throws Exception {
        assertEquals("failed transfer rolled back\\nnorth=7\\nsouth=5", output(() -> StockTransfer.main(new String[0])));
    }
}
''')
with zipfile.ZipFile(OUT/'aitrove-java-test-project.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for file in project.rglob('*'):
        if file.is_file() and 'target' not in file.parts: archive.write(file,file.relative_to(project))
print(json.dumps({'added':len(new),'javaPages':len(java_entries)}))
