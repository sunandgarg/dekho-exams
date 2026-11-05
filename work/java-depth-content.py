"""Add original Java depth lessons without changing the homepage or earlier batch."""
import copy,datetime,html,json,pathlib,re,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT.parent.parent/'outputs'
baseline=ROOT/'work/java-depth/baseline.json'
if not baseline.exists():baseline.write_text((ROOT/'src/data/fixtures.json').read_text())
entries=json.loads(baseline.read_text());lookup={e['path']:e for e in entries};added=[];expanded=[];banks=[]
sections={e['subject']:e['path'] for e in entries if e['type']=='subject' and e['path'].startswith('java/')}
stamp=datetime.datetime.now(datetime.UTC).isoformat();base=copy.deepcopy(lookup['java/casts'])
def para(s):return '<p>'+html.escape(s)+'</p>'
def code(s,lang='java'):return '<pre><code class="language-'+lang+'">'+html.escape(s.strip(),quote=False)+'</code></pre>'
def put(slug,title,definition,parts,source,output,cost,mistakes,related,subject='java-advanced',release=8,dependency=None,source_file=None):
 path='java/'+slug;body=para(definition)+'<p><strong>Java '+str(release)+'+.</strong> '+({'h2':'The downloadable Maven fixture supplies H2 2.3.232.','hikari':'The downloadable Maven fixture supplies HikariCP 5.1.0 and H2 2.3.232.'}.get(dependency,'The program uses JDK classes and requires no preview flags.'))+'</p>'
 for heading,texts in parts:body+='<h2>'+html.escape(heading)+'</h2>'+''.join(para(t) for t in texts)
 body+='<h2>Working program</h2>'+code(source)+'<h3>Output</h3>'+code(output,'text')
 body+='<h2>Costs and boundaries</h2>'+''.join(para(t) for t in cost)+'<h3>Common Mistakes</h3><ul>'+''.join('<li>'+html.escape(t)+'</li>' for t in mistakes)+'</ul>'
 body+='<h2>Read next</h2><p>'+', '.join('<a href="/java/'+slug+'">'+html.escape(title)+'</a>' for slug,title in related)+'.</p>'
 e=copy.deepcopy(lookup.get(path,base));e.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),path=path,title=title,summary=definition,body=body,subject=subject,tags=['java',slug],difficulty='Intermediate',featured=False,sort_order=130+len(added),updated_at=stamp,status='published')
 e['data']={'subject_root':'java/java','section_path':sections[subject],'content_format':'html','kind':'tutorial','java_release':release,'java_version':str(release)+'+','reading_minutes':max(4,round(len(re.sub('<[^>]*>',' ',body).split())/150)),'author_path':'authors/aitrove-editorial','download_path':'/downloads/aitrove-java-source-kit.zip','related':[{'path':'java/'+s,'title':t} for s,t in related]}
 if dependency:e['data']['java_dependency']=dependency
 if source_file:e['data'].update(java_source_file=source_file,java_entrypoint='instance')
 if path in lookup:lookup[path].update(e);expanded.append(path)
 else:entries.append(e);lookup[path]=e;added.append(path)

put('access-packages','Java access boundaries: private nests and protected receivers',
'Java access control checks both the member declaration and the context of its use; inheriting a protected member does not make it publicly accessible through every receiver.',
[('Separate inheritance from access',[
'A delivery adapter extends a base class in another package. The adapter can access an inherited protected field through its own compatible receiver, but a general base-typed object does not automatically qualify. Code that worked inside the base package can therefore fail after it is moved into the adapter package.',
'Package-private access has no modifier. A child class in a different package cannot use that access as if it were protected. Public access also depends on the enclosing type being accessible; a public method on an inaccessible implementation type is not a substitute for a public interface.',
'Private members are accessible within the enclosing nest of classes. This program uses two nested classes that belong to one top-level declaration. It proves that case; it does not prove that any unrelated class in the same package can read the private field. The downloadable access-packages fixture checks the cross-package protected cases with both successful and rejected compilations.'
]),('Review the boundary before changing visibility',[
'If a consumer needs a delivery status, expose a status operation with a return contract. Publishing the mutable internal queue merely to make one compiler error disappear lets callers bypass the adapter’s invariants. A package layout is useful when it separates ownership, not when every member is made public to remove friction.'
])],'''public class NestAccessReceipt {
    static class Receipt { private final int accepted = 7; }
    static class Audit { static int read(Receipt receipt) { return receipt.accepted; } }
    public static void main(String[] args) { System.out.println(Audit.read(new Receipt())); }
}''','7',
['The field access itself is constant work. Package and access decisions are checked when code is compiled and linked; they are not collection traversal costs. The multi-file kit includes a subclass in another package and verifies that a base-typed protected receiver is rejected.'],
['Being in a subclass does not grant arbitrary cross-package protected access.','An unrelated same-package class does not share a private nest.','Visibility is not a thread-safety rule.'],[('access-control','Access modifiers'),('packages','Package layout')],subject='java')

put('grapheme-boundaries','Java grapheme boundaries: truncate display text without splitting a cluster',
'An extended grapheme cluster is a text segment used for character-boundary analysis; its UTF-16 length can be greater than one and its display width is not fixed.',
[('Choose the unit before truncating',[
'A receipt label can contain a base character followed by a combining accent. Cutting after one UTF-16 unit can leave the accent behind. A supplementary symbol uses a surrogate pair, so even counting code points does not settle every displayed-character boundary.',
'This Java 25 fixture asks the character BreakIterator for boundaries, then keeps a declared number of clusters. The returned index is still a UTF-16 offset suitable for substring. The program uses a composed-looking sequence with a combining mark and checks its first segment. It also checks a supplementary symbol followed by a letter.',
'Cluster segmentation is not text shaping. A cluster can occupy several columns, and its appearance depends on font and rendering. A label limited by pixels needs measurement in the UI, not just a server-side cluster count. Java and Unicode data versions must also be part of reproducible text-processing tests.'
]),('Own the iterator state',[
'BreakIterator holds the text being analyzed and a current position. Give an operation its own instance rather than sharing a single cursor among requests. Preserve the original label when building a shortened display string; do not overwrite the canonical stored value with a presentation limit.'
])],r'''import java.text.BreakIterator;
import java.util.Locale;
public class ReceiptLabelClusters {
    static String prefix(String text,int limit){
        if(limit<0)throw new IllegalArgumentException("Negative cluster limit");
        java.util.Objects.requireNonNull(text);
        BreakIterator boundaries=BreakIterator.getCharacterInstance(Locale.ROOT);
        boundaries.setText(text);int end=boundaries.first();
        for(int count=0;count<limit;count++){
            int next=boundaries.next();if(next==BreakIterator.DONE)return text;end=next;
        }
        return text.substring(0,end);
    }
    public static void main(String[] args){
        String label="e\u0301clair";
        System.out.println(prefix(label,1).length());
        System.out.println(prefix("\ud83d\ude00X",1).length());
        System.out.println(prefix(label,0).isEmpty());
        System.out.println(prefix(label,20).equals(label));
    }
}''','2\n2\ntrue\ntrue',
['Boundary analysis examines text; budget for work proportional to the analyzed input rather than treating a character limit as a free operation. The returned substring allocates its result. This fixture targets the Java 25 character-boundary contract; it does not establish identical segmentation on every earlier runtime or font.'],
['String.length counts UTF-16 units, not display clusters.','A cluster count is not a pixel-width limit.','Do not reuse a mutable iterator concurrently.'],[('unicode-encoding','UTF-16 and encoding'),('text-normalization','Normalization')],subject='java',release=25)

put('collation-policy','Java collation: display order and distinct stored labels',
'Collation compares natural-language strings under a locale and strength policy; comparator equality can group labels that String.equals still treats as different.',
[('Sorting is not identifier equality',[
'A customer directory can sort labels without treating every case or accent difference as a new primary position. That is a presentation decision. An account identifier still needs its own exact or normalized equality contract; using the directory comparator as a map-key rule can merge accounts that should remain distinct.',
'The program uses a French collator at primary strength. It compares two labels that differ by an accent and then shows the membership effect in TreeSet. The second set adds a UTF-16 tie-break so comparator-equivalent spellings remain separate values. The set is ordered by that combined rule, not just by the collator.',
'The locale is explicit. A default-locale comparison can change when the application moves to a machine with another language setting. Locale data can also change across JDK releases. Store stable identifiers independently of the user’s display order, and state the runtime when a test asserts a particular ordering.'
]),('Treat configuration as owned state',[
'Collator configuration includes strength and decomposition mode. Configure an instance before using it in a sorted collection, then keep that rule fixed for the collection’s lifetime. Changing a comparator’s behavior after insertion can invalidate search assumptions even if no label object changed.'
])],r'''import java.text.Collator;
import java.util.*;
public class CustomerDirectoryOrder {
    public static void main(String[] args){
        Collator french=Collator.getInstance(Locale.FRENCH);french.setStrength(Collator.PRIMARY);
        String first="cote",second="c\u00f4te";
        TreeSet<String> grouped=new TreeSet<>((a,b)->french.compare(a,b));
        grouped.add(first);grouped.add(second);
        Comparator<String> distinct=(a,b)->{int compared=french.compare(a,b);return compared!=0?compared:a.compareTo(b);};
        TreeSet<String> labels=new TreeSet<>(distinct);labels.add(first);labels.add(second);
        System.out.println(french.compare(first,second)==0);
        System.out.println(grouped.size());System.out.println(labels.size());
    }
}''','true\n1\n2',
['A comparison examines the strings under the chosen locale rules. Sorting performs O(n log n) comparisons for n labels, with text-processing costs inside each comparison. A tie-break preserves distinct spellings but does not create a universal cross-version collation order.'],
['Comparator equality can collapse TreeSet membership.','The machine’s default locale is not an explicit application policy.','Do not change comparator settings after insertion.'],[('comparator-contracts','Ordered membership'),('text-normalization','Stored text policy')],subject='java')

put('identifier-policy','Java identifier input: explicit alphabets and normalized display text',
'A machine identifier policy defines the accepted alphabet, length and equality rule before a value enters a key or path boundary.',
[('Keep display labels separate',[
'A parcel reference used in a protocol can be restricted to uppercase ASCII letters, digits and hyphens. That narrow policy rejects visually similar characters from other scripts because they are outside the declared alphabet. It is appropriate for this reference field, not a rule for every person’s name.',
'Unicode normalization does not itself solve look-alike identifiers. Two characters can look similar while remaining different after normalization. Conversely, a compatibility normalization can merge distinctions the application intended to preserve. Decide whether the field is a human label or a protocol key before applying transformations.',
'The validator rejects lowercase input instead of silently changing it. A different service can choose uppercase canonicalization, but it must apply the same rule on creation and lookup and check collisions under that rule. This example also rejects an empty value, an overlong value and separators at the ends.'
]),('Validate before publishing',[
'The function returns the accepted value without touching shared state. If validation fails, the caller has no partially registered reference to undo. That order matters when registration also writes an index, audit record or filesystem path. Accepted syntax still needs authorization and uniqueness checks in the service using it.'
])],'''public class ParcelReferencePolicy {
    static String accept(String reference){
        if(reference==null||reference.length()<3||reference.length()>24)throw new IllegalArgumentException("Reference length");
        if(reference.charAt(0)=='-'||reference.charAt(reference.length()-1)=='-')throw new IllegalArgumentException("Separator position");
        for(int i=0;i<reference.length();i++){
            char c=reference.charAt(i);if(!((c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='-'))throw new IllegalArgumentException("Reference alphabet");
        }return reference;
    }
    public static void main(String[] args){
        System.out.println(accept("PK-204"));
        for(String rejected:new String[]{"pk-204","PK\u2011204","-PK"})
            try{accept(rejected);}catch(IllegalArgumentException invalid){System.out.println("rejected");}
    }
}''','PK-204\nrejected\nrejected\nrejected',
['Validation is O(n) over at most 24 UTF-16 units and uses constant auxiliary storage. The strict alphabet is a field-specific decision. It does not prove that an accepted reference belongs to the current user, is unique, or is safe to concatenate into an arbitrary external command.'],
['Normalization is not a complete confusable-character policy.','Do not apply a protocol alphabet to international display names.','Syntax validation does not replace authorization.'],[('regular-expressions','Full-input matching'),('grapheme-boundaries','Display boundaries')],subject='java')

put('scoped-values','Java 25 scoped values: request context with a bounded lifetime',
'A ScopedValue binds a value to the current execution scope and restores the previous binding when that scope returns or throws.',
[('Pass one-way context',[
'A reporting operation needs a request identifier deep inside callbacks. Keeping an explicitly passed context object is still a valid choice. A scoped value fits when intermediate methods do not need the value but selected downstream code does. Keep its key private so unrelated code cannot read or rebind it merely because it knows a field name.',
'The binding is not a writable thread-local slot that remains until remove is called. A nested binding temporarily shadows the outer value; leaving the nested operation restores the outer binding even when the nested code throws. The program checks that path instead of assuming every callback returns normally.',
'Binding lifetime does not freeze an object. This example binds an immutable String. A mutable request object can still be changed through another reference. Ordinary newly created threads do not automatically receive this binding; structured sharing has its own API rules. No preview structured-concurrency API is used in this lesson.'
]),('Make missing context explicit',[
'Calling get outside a binding is a misuse unless the API contract permits an optional context and checks it deliberately. The operation should not silently invent a request identifier just because a caller forgot to establish its scope. The final isBound check proves cleanup after the operation.'
])],'''public class ReportRequestScope {
    private static final ScopedValue<String> REQUEST=ScopedValue.newInstance();
    public static void main(String[] args)throws Exception{
        ScopedValue.where(REQUEST,"REQ-51").call(()->{
            System.out.println(REQUEST.get());
            try{ScopedValue.where(REQUEST,"AUDIT-51").run(()->{throw new IllegalStateException("audit failed");});}
            catch(IllegalStateException failed){System.out.println(REQUEST.get());}
            Thread child=Thread.ofVirtual().start(()->System.out.println(REQUEST.isBound()));
            child.join();return null;
        });
        System.out.println(REQUEST.isBound());
    }
}''','REQ-51\nREQ-51\nfalse\nfalse',
['Binding and lookup do not traverse application collections. Lookup cost depends on the scope implementation and its cache; this program makes no nanosecond claim. Referenced context remains reachable while the binding needs it. Java 25 finalizes this API; earlier preview versions are not the baseline used here.'],
['A bounded binding does not make a mutable payload immutable.','A raw child thread does not imply scoped inheritance.','Do not expose the key as a public application-wide permission.'],[('threads','Thread ownership'),('cancellation','Completion and stopping')],release=25)

put('stream-gatherers','Java stream gatherers: batching and ordered running totals',
'A stream gatherer transforms a sequence while retaining operation state, which lets a pipeline express batching and ordered accumulation beyond a one-element map.',
[('State the output shape',[
'A dispatch pipeline batches receipt quantities into fixed windows and then computes running totals for an audit trace. Those are different transformations: one emits lists, while the other emits an accumulated value for each input. A final reduce would return only the aggregate, losing the intermediate totals.',
'windowFixed emits a smaller final window when the input does not fill the requested size. An empty input produces no windows. Validate the batch size at the configuration boundary rather than discovering an invalid size after work has been admitted. The program checks the trailing batch and the empty stream.',
'Window lists are unmodifiable membership structures. Their element objects can still be shared mutable values. This fixture uses Integer values, so that particular ownership issue is absent. A batch of mutable receipt objects would need an explicit snapshot or transfer-of-ownership rule.'
]),('Know what retained output costs',[
'The pipeline below materializes all windows with toList. An online consumer could process windows as they arrive, but returning every window retains the batch references. For running totals, the order of the input is part of the result. Do not substitute an order-dependent recurrence into an operation that assumes an interchangeable grouping rule.'
])],'''import java.util.List;
import java.util.stream.Gatherers;
public class DispatchBatchGatherers {
    public static void main(String[] args){
        List<Integer> counts=List.of(4,7,2,9,3);
        System.out.println(counts.stream().gather(Gatherers.windowFixed(2)).toList());
        System.out.println(counts.stream().gather(Gatherers.scan(()->0,Math::addExact)).toList());
        System.out.println(List.<Integer>of().stream().gather(Gatherers.windowFixed(2)).count());
    }
}''','[[4, 7], [2, 9], [3]]\n[4, 11, 13, 22, 25]\n0',
['Both transformations inspect n elements. Materializing the windows or every running total retains O(n) output. A configured large window can allocate substantial temporary storage even for a shorter stream. Gatherers are final from Java 24; this checked source targets Java 25 rather than earlier preview releases.'],
['A final partial window is valid output.','Unmodifiable windows do not deep-copy arbitrary elements.','toList still retains the complete returned result.'],[('streams','Stream operations'),('immutable-collections','Membership and element ownership')],release=25)

put('flexible-constructors','Java 25 constructor validation before superclass initialization',
'A flexible constructor body can perform permitted statements before its explicit superclass or delegated-constructor invocation while respecting early-construction restrictions.',
[('Reject before passing the value onward',[
'A shipment quantity is required by the superclass constructor. Validate and convert the incoming quantity before invoking super, so the base object receives a checked value. The validation is about the input argument; it does not read partially initialized instance state.',
'Java 25 permits this prologue under specific construction rules. It is not permission to call arbitrary instance methods before the superclass exists. Local computations and input checks should remain separate from callbacks that expect the full object invariant. Publishing this from construction still needs its own review.',
'The example uses a long input and Math.toIntExact before the base constructor. That keeps both negative quantities and values too large for the base representation out of the initialized object. The failed construction creates no application registry entry because publication is not part of this constructor.'
]),('Keep delegating paths consistent',[
'If the class has several constructors, make each path converge on the same validated invariant. Duplicated checks tend to drift when a new parameter is introduced. A constructor that accepts already validated data can be private, while the public boundary owns conversion and rejection.'
])],'''public class CheckedShipmentConstruction {
    static class Quantity { final int units;Quantity(int units){this.units=units;} }
    static class Shipment extends Quantity {
        Shipment(long requested){
            if(requested<0)throw new IllegalArgumentException("Negative shipment");
            int validated=Math.toIntExact(requested);
            super(validated);
        }
    }
    public static void main(String[] args){
        System.out.println(new Shipment(9).units);
        try{new Shipment(-1);}catch(IllegalArgumentException rejected){System.out.println("negative rejected");}
        try{new Shipment(3_000_000_000L);}catch(ArithmeticException rejected){System.out.println("range rejected");}
    }
}''','9\nnegative rejected\nrange rejected',
['Scalar validation and conversion take constant work. This language feature changes permitted constructor structure, not the arithmetic range or object-publication rules. The source requires Java 25 without preview flags; it is not a Java 8-compatible constructor.'],
['The prologue is not a fully initialized instance.','A constructor failure does not undo unrelated external side effects.','Do not claim a newer language feature compiles under an earlier release.'],[('constructors','Construction invariants'),('casts','Rejecting numeric conversions')],release=25)

put('module-imports','Java 25 module imports: source names without a deployment shortcut',
'A module import declaration makes public types in exported packages available for source-level name resolution; it does not replace module readability or deployment configuration.',
[('Import names and resolve dependencies separately',[
'The program imports the java.base module and uses several exported types without individual package imports. It remains an ordinary class-path application. Nothing in this source creates a module descriptor for the application or packages a missing external library.',
'An import can expose many simple names, so collisions need deliberate qualification. Date from java.util and Date from java.sql are different types. Importing more packages does not make those names interchangeable or choose the desired business meaning.',
'Module import declarations are a Java 25 language feature. An IDE accepting the syntax with a newer SDK does not prove that a Java 21 build target can compile it. Keep the compiler release and the application’s required runtime in the build definition.'
]),('Keep the dependency visible to reviewers',[
'For a small file, individual imports can make dependencies easier to read. A module import is useful where the module is the intended source namespace. That choice is about source organization; it is not a claim that every exported class is loaded into memory at startup.'
])],'''import module java.base;
public class ModuleImportedReceipts {
    public static void main(String[] args){
        List<String> references=List.of("R-23","R-11","R-23");
        Set<String> unique=new TreeSet<>(references);
        System.out.println(unique);
        System.out.println(LocalDate.of(2026,9,29));
    }
}''','[R-11, R-23]\n2026-09-29',
['The list and tree operations determine this program’s runtime cost. Import syntax affects source name resolution and does not promise shorter startup, a smaller artifact, or automatic library discovery. A named application module still needs its descriptor and launch configuration.'],
['An import is not a requires declaration.','Ambiguous simple names still need qualification.','The selected module must be observable under the compilation setup.'],[('java-modules','Module boundaries'),('packages','Source packages')],release=25)

put('compact-source','Java 25 compact source files: an instance main with explicit input limits',
'A compact source file omits an explicit top-level class declaration and can define an instance main method, while the source still compiles into a class.',
[('Read the instance lifecycle',[
'This file defines receipt references as instance state and prints their count from main. The launcher creates the enclosing instance before invoking that method. Removing the static modifier does not turn fields into global state or remove ordinary initialization rules.',
'The implicit source environment provides the java.base type imports used here, and IO supplies the console operation. A regular explicit class can also use an eligible instance main under the Java 25 launch rules. Neither syntax removes the need to validate external arguments or own resources.',
'Save this exact source as ShipmentSummary.java. The file name determines the implicit class name used in the compiled launch command. The source kit includes this file, its minimum release and its entrypoint mode rather than wrapping the method in another main during verification.'
]),('Choose the form for the application',[
'A compact file suits a small entrypoint. Package structure, explicit APIs and multi-file builds still matter when the program grows. Keep business operations separate from console output so tests can check return values and rejected inputs without intercepting every printed line.'
])],'''List<String> references = List.of("R-19", "R-20", "R-21");
void main() {
    IO.println(references.size());
    IO.println(references.getFirst());
}''','3\nR-19',
['The stored references occupy O(n) list membership storage for n references. This fixture has three elements and does no external input. Compact syntax changes source structure; it does not change list access contracts or provide a performance optimization. Compile and launch with Java 25.'],
['The source file name is part of the launch contract.','Instance fields are initialized before this instance main runs.','Do not compile Java 25 syntax with an earlier release target.'],[('setup','Compilation and launch'),('module-imports','Module imports')],release=25,source_file='ShipmentSummary.java')

put('virtual-thread-monitors','Java 25 virtual threads and monitors: version boundaries still matter',
'A virtual thread executes on carrier threads, and the monitor-related carrier-pinning behavior changed in JDK 24 without removing the monitor’s mutual-exclusion contract.',
[('Separate contention from carrier retention',[
'A synchronized operation still allows only one holder of a particular monitor at a time. Removing the older monitor-related pinning behavior does not make all requests inside that critical section execute concurrently. A slow operation under one shared monitor can remain an application bottleneck.',
'The Java 21 lesson is labelled for that release. Its synchronized-block pinning warning should not be generalized to every newer JDK. This Java 25 fixture checks completed increments under a monitor and uses virtual threads, but it does not infer carrier behavior from elapsed time.',
'Native or foreign calls can introduce other blocking or pinning boundaries. Runtime diagnostics and the actual call path matter. A virtual thread also does not create more database connections, CPU cores or queue capacity; downstream admission remains a separate application rule.'
]),('Wait for completion before reading shared state',[
'The program joins every worker before printing the count. The protected increment prevents lost updates, while joining supplies a completion boundary for the final read. A collection of started Thread objects alone does not prove that their operations finished successfully in a larger application.'
])],'''import java.util.*;
public class MonitoredVirtualReceipts {
    final Object monitor=new Object();int accepted;
    void accept(){synchronized(monitor){accepted++;}}
    public static void main(String[] args)throws Exception{
        MonitoredVirtualReceipts service=new MonitoredVirtualReceipts();List<Thread> workers=new ArrayList<>();
        for(int i=0;i<40;i++)workers.add(Thread.ofVirtual().start(service::accept));
        for(Thread worker:workers)worker.join();
        System.out.println(service.accepted);
    }
}''','40',
['There are n operations and n retained worker handles. The monitor serializes their increments, so virtual threads do not establish parallel speedup for that section. This program verifies the state result on Java 25; timing, native-call behavior and carrier scheduling need separate diagnostic evidence.'],
['Less monitor pinning does not remove lock contention.','A release-specific warning is not a timeless rule.','Uncaught worker failure requires explicit reporting in application code.'],[('virtual-threads','Java 21 baseline'),('locks','Mutual exclusion'),('flight-recorder','Runtime evidence')],release=25)

put('avl-deletion','Java AVL deletion: rebalance every surviving ancestor',
'AVL deletion removes a search-tree key and repairs subtree heights on the path back to the root, including rotations caused by the reduced subtree.',
[('Insertion cases are not enough',[
'A shipment index can stay balanced during insertion and become skewed after deletion. Removing a leaf changes the height seen by its parent. That parent may rotate, and the height change can continue upward. Stopping after the first repaired node can leave another ancestor outside the balance rule.',
'For a node with two children, this implementation copies its successor key and removes that successor from the right subtree. Key copying is acceptable for this integer-set model. An index storing node identities or mutable payloads needs a separate decision about identity and ownership.',
'The child balance chooses the rotation. After deletion, a heavy child can have balance zero; that case still permits a single rotation. Reusing insertion’s newly inserted-key tests would make the deletion decision depend on a key that no longer describes the surviving subtree.'
]),('Treat absent keys as a normal result',[
'Deleting an absent shipment leaves membership unchanged. The recursive path still returns the existing subtree roots, and cached heights are recomputed before they are used. The property suite compares repeated deletions with TreeSet and checks ordering, cached height and balance at every node.'
])],'''public class DeletableShipmentAvl {
    static class Node {int key,height=1;Node left,right;Node(int key){this.key=key;}}
    Node root;
    static int height(Node n){return n==null?0:n.height;}
    static int balance(Node n){return n==null?0:height(n.left)-height(n.right);}
    static void update(Node n){n.height=1+Math.max(height(n.left),height(n.right));}
    static Node right(Node n){Node next=n.left;n.left=next.right;next.right=n;update(n);update(next);return next;}
    static Node left(Node n){Node next=n.right;n.right=next.left;next.left=n;update(n);update(next);return next;}
    static Node repair(Node n){
        if(n==null)return null;update(n);
        if(balance(n)>1){if(balance(n.left)<0)n.left=left(n.left);return right(n);}
        if(balance(n)<-1){if(balance(n.right)>0)n.right=right(n.right);return left(n);}
        return n;
    }
    static Node add(Node n,int key){
        if(n==null)return new Node(key);
        if(key<n.key)n.left=add(n.left,key);else if(key>n.key)n.right=add(n.right,key);else return n;
        return repair(n);
    }
    static Node remove(Node n,int key){
        if(n==null)return null;
        if(key<n.key)n.left=remove(n.left,key);else if(key>n.key)n.right=remove(n.right,key);
        else {
            if(n.left==null)return n.right;if(n.right==null)return n.left;
            Node successor=n.right;while(successor.left!=null)successor=successor.left;
            n.key=successor.key;n.right=remove(n.right,successor.key);
        }return repair(n);
    }
    static void ordered(Node n,java.util.List<Integer> values){if(n!=null){ordered(n.left,values);values.add(n.key);ordered(n.right,values);}}
    public static void main(String[] args){
        DeletableShipmentAvl index=new DeletableShipmentAvl();
        for(int key:new int[]{40,20,60,10,30,50,70,5})index.root=add(index.root,key);
        index.root=remove(index.root,40);index.root=remove(index.root,5);index.root=remove(index.root,999);
        java.util.List<Integer> values=new java.util.ArrayList<>();ordered(index.root,values);System.out.println(values);
    }
}''','[10, 20, 30, 50, 60, 70]',
['A maintained AVL height makes lookup, insertion and deletion O(log n). Recursive stack storage is O(log n). Exporting the ordered list is O(n) and allocates n result positions. This set model does not preserve the identity of a two-child node’s former key.'],
['Repair every surviving ancestor on the return path.','Deletion must handle a heavy child with zero balance.','Key copying can be wrong for an identity-sensitive payload model.'],[('avl-tree','Insertion balance'),('binary-search-tree','Search-tree deletion')],subject='java-dsa')

put('trie-deletion','Java trie deletion: preserve shared prefixes and prune dead branches',
'Trie deletion clears a word’s terminal marker and removes only branches that contain no remaining word or descendant.',
[('A prefix is shared storage',[
'A command index stores pack and parcel. Deleting pack must not remove the shared pa path needed by parcel. A stored word can also be a prefix of another word, so clearing its terminal marker is separate from deleting the node itself.',
'The program records the path as it walks toward the word, then prunes backward after clearing the terminal marker. That avoids recursion proportional to an arbitrarily long input. The alphabet is deliberately restricted to lowercase ASCII, with a 4096-unit input budget.',
'Validation happens before mutation. An invalid final character must not cause the earlier valid prefix to disappear or create partial branches. A missing path or an unmarked prefix returns false without changing another word’s membership.'
]),('Do not invent ranking semantics',[
'This structure answers exact membership and deletion. It does not rank suggestions, define language collation or compress long single-child paths. Those features need their own stored counts or ordering rules. Node pruning is a storage operation, not a popularity score update.'
])],'''public class DeletableCommandTrie {
    static class Node {Node[] children=new Node[26];boolean terminal;}
    final Node root=new Node();
    static void validate(String word){
        if(word==null||word.isEmpty()||word.length()>4096)throw new IllegalArgumentException("Word budget");
        for(int i=0;i<word.length();i++)if(word.charAt(i)<'a'||word.charAt(i)>'z')throw new IllegalArgumentException("Alphabet");
    }
    void add(String word){validate(word);Node n=root;for(int i=0;i<word.length();i++){int slot=word.charAt(i)-'a';if(n.children[slot]==null)n.children[slot]=new Node();n=n.children[slot];}n.terminal=true;}
    boolean contains(String word){validate(word);Node n=root;for(int i=0;i<word.length();i++){n=n.children[word.charAt(i)-'a'];if(n==null)return false;}return n.terminal;}
    static boolean empty(Node n){if(n.terminal)return false;for(Node child:n.children)if(child!=null)return false;return true;}
    boolean remove(String word){
        validate(word);Node[] path=new Node[word.length()+1];path[0]=root;
        for(int i=0;i<word.length();i++){path[i+1]=path[i].children[word.charAt(i)-'a'];if(path[i+1]==null)return false;}
        if(!path[word.length()].terminal)return false;path[word.length()].terminal=false;
        for(int i=word.length();i>0&&empty(path[i]);i--)path[i-1].children[word.charAt(i-1)-'a']=null;
        return true;
    }
    public static void main(String[] args){
        DeletableCommandTrie commands=new DeletableCommandTrie();commands.add("pack");commands.add("packing");commands.add("parcel");
        System.out.println(commands.remove("pack"));System.out.println(commands.contains("packing"));
        System.out.println(commands.remove("pack"));System.out.println(commands.remove("parcel"));
    }
}''','true\ntrue\nfalse\ntrue',
['For a word of length m, validation, traversal and pruning are O(m) with a fixed 26-slot alphabet. The recorded path uses O(m) temporary references. Live nodes retain 26 child positions each, so this representation can be wasteful for sparse or much larger alphabets.'],
['Clearing a terminal marker is not permission to remove live descendants.','Validate the complete word before mutation.','A fixed ASCII trie is not a Unicode search index.'],[('trie','Prefix membership'),('identifier-policy','Alphabet boundaries')],subject='java-dsa')

put('floyd-warshall','Java Floyd–Warshall: all-pairs distances and negative-cycle rejection',
'Floyd–Warshall computes shortest-path distances between every pair of vertices by successively allowing each vertex as an intermediate point.',
[('Keep the intermediate vertex outside',[
'The recurrence asks whether a path through the current intermediate vertex improves an existing distance. That intermediate loop is the outer loop. Reordering the loops changes which already computed paths are available and can break the recurrence.',
'An absent edge uses a sentinel and is never added to a finite value. A graph with negative edges can still have finite shortest paths, but a negative cycle makes some paths unbounded below. This implementation rejects the whole result when any diagonal becomes negative rather than returning a matrix with undefined entries mixed into ordinary distances.',
'The input matrix is copied. Parallel edges must already be reduced to their minimum direct cost, and each diagonal must represent the zero-length path. The program sets each diagonal to the smaller of zero and the supplied value so a negative self-loop is preserved for cycle detection.'
]),('Bound the model before allocating',[
'The fixture accepts at most 200 vertices and finite edge magnitudes at most one million. That is a learning budget, not a claim that a 200-vertex matrix suits every graph. Sparse graphs with far more vertices usually need a different representation and shortest-path strategy.'
])],'''import java.util.Arrays;
public class DepotAllPairs {
    static final long ABSENT=Long.MAX_VALUE;
    static long[][] distances(long[][] input){
        int n=input.length;if(n>200)throw new IllegalArgumentException("Matrix budget");
        long[][] result=new long[n][n];
        for(int i=0;i<n;i++){
            if(input[i]==null||input[i].length!=n)throw new IllegalArgumentException("Square matrix required");
            for(int j=0;j<n;j++){
                long value=input[i][j];if(value!=ABSENT&&(value<-1_000_000||value>1_000_000))throw new IllegalArgumentException("Edge budget");result[i][j]=value;
            }result[i][i]=Math.min(0,result[i][i]);
        }
        for(int via=0;via<n;via++)for(int from=0;from<n;from++)for(int to=0;to<n;to++)
            if(result[from][via]!=ABSENT&&result[via][to]!=ABSENT)result[from][to]=Math.min(result[from][to],Math.addExact(result[from][via],result[via][to]));
        for(int i=0;i<n;i++)if(result[i][i]<0)throw new IllegalStateException("Negative cycle");
        return result;
    }
    public static void main(String[] args){
        long[][] edges={{0,5,ABSENT},{ABSENT,0,-2},{ABSENT,ABSENT,0}};
        System.out.println(Arrays.toString(distances(edges)[0]));System.out.println(edges[0][2]==ABSENT);
    }
}''','[0, 5, 3]\ntrue',
['Time is O(V³) and matrix storage is O(V²). A negative-cycle input can amplify intermediate distances; checked addition can reject arithmetic overflow before the final cycle check. This implementation rejects such an input rather than claiming a usable finite result.'],
['Do not add the absent sentinel to an edge weight.','The intermediate loop belongs outside the endpoint loops.','A negative cycle is different from a negative edge.'],[('bellman-ford','Single-source negative edges'),('dijkstra','Non-negative paths')],subject='java-dsa')

put('strong-components','Java strongly connected components: mutual reachability with two traversals',
'A strongly connected component groups directed-graph vertices that can each reach every other vertex in the group.',
[('Direction changes the membership rule',[
'A dependency graph can have one-way reachability without a cycle. Union-find on undirected endpoints would group that relation differently. Strong components need both directions of reachability, so this algorithm first records a finishing order and then walks the reversed graph.',
'The first pass below uses explicit DFS frames represented by each vertex’s next edge index. Marking a vertex when it is pushed prevents repeated pending entries from being mistaken for separate visits. A vertex enters the finishing list only after its outgoing edges have been considered.',
'The reversed pass visits vertices in reverse finishing order and assigns one component number per reached group. The numbers are traversal labels, not stable business identifiers. Reordering adjacency lists can change their numeric values while preserving the same component partition.'
]),('Validate every endpoint',[
'Validate the whole graph before computing the partition. An invalid edge should not leave a half-built result that a caller mistakes for a complete grouping. The property tests compare component equality with an independent transitive-reachability matrix; they do not require one particular label numbering.'
])],'''import java.util.*;
public class DependencyComponents {
    static int[] groups(int[][] edges){
        int n=edges.length;List<List<Integer>> reverse=new ArrayList<>();for(int i=0;i<n;i++)reverse.add(new ArrayList<>());
        for(int v=0;v<n;v++){if(edges[v]==null)throw new IllegalArgumentException("Missing adjacency");for(int next:edges[v]){if(next<0||next>=n)throw new IllegalArgumentException("Invalid endpoint");reverse.get(next).add(v);}}
        boolean[] seen=new boolean[n];int[] cursor=new int[n];List<Integer> finished=new ArrayList<>();ArrayDeque<Integer> stack=new ArrayDeque<>();
        for(int start=0;start<n;start++)if(!seen[start]){
            seen[start]=true;stack.push(start);
            while(!stack.isEmpty()){
                int v=stack.peek();if(cursor[v]<edges[v].length){int next=edges[v][cursor[v]++];if(!seen[next]){seen[next]=true;stack.push(next);}}
                else {stack.pop();finished.add(v);}
            }
        }
        int[] group=new int[n];Arrays.fill(group,-1);int label=0;
        for(int i=finished.size()-1;i>=0;i--){int start=finished.get(i);if(group[start]>=0)continue;group[start]=label;stack.push(start);
            while(!stack.isEmpty()){int v=stack.pop();for(int next:reverse.get(v))if(group[next]<0){group[next]=label;stack.push(next);}}
            label++;
        }return group;
    }
    public static void main(String[] args){
        int[] group=groups(new int[][]{{1},{0,2},{3},{2},{}});
        System.out.println(group[0]==group[1]);System.out.println(group[2]==group[3]);System.out.println(group[1]==group[2]);
    }
}''','true\ntrue\nfalse',
['Both passes take O(V+E). The reversed adjacency storage uses O(V+E); traversal state uses O(V). Explicit stacks avoid recursion depth proportional to the graph path, but they do not remove the memory needed for a large graph.'],
['Undirected connectivity is not strong connectivity.','Numeric component labels are not stable external IDs.','Finishing order differs from discovery order.'],[('graph-dfs','Depth-first traversal'),('topological-sort','Dependency ordering')],subject='java-dsa')

put('edit-distance','Java edit distance: two rows and a declared text unit',
'Levenshtein distance counts the minimum insertions, deletions and substitutions needed to transform one sequence into another when each operation has unit cost.',
[('State what a sequence element means',[
'This implementation treats each UTF-16 code unit as an element. That is a deliberate algorithm contract, not a claim about user-perceived characters. A text-correction feature working on grapheme clusters needs to segment first and then apply a corresponding sequence algorithm.',
'Each cell depends on a deletion, insertion or substitution from neighboring states. Only the previous row and the current row are needed for the final distance, so the implementation avoids retaining the complete matrix. It swaps the input references so the row width follows the shorter input.',
'The row reduction cannot reconstruct an edit script by itself. If the UI needs highlighted edits, retain predecessor information or use an algorithm that reconstructs the path with its own storage policy. A scalar distance alone does not identify which positions should be changed.'
]),('Use a work budget',[
'Even with two rows, the operation still performs a product of the sequence lengths. The fixture rejects more than four million cell updates. That budget keeps this tutorial program bounded; an online endpoint needs a timeout and admission policy as well as an input length rule.'
])],'''public class ReceiptLabelDistance {
    static int distance(String a,String b){
        java.util.Objects.requireNonNull(a);java.util.Objects.requireNonNull(b);
        if((long)a.length()*b.length()>4_000_000)throw new IllegalArgumentException("Distance work budget");
        if(a.length()<b.length()){String swap=a;a=b;b=swap;}
        int[] previous=new int[b.length()+1],current=new int[b.length()+1];for(int j=0;j<previous.length;j++)previous[j]=j;
        for(int i=1;i<=a.length();i++){
            current[0]=i;for(int j=1;j<=b.length();j++)current[j]=Math.min(Math.min(previous[j]+1,current[j-1]+1),previous[j-1]+(a.charAt(i-1)==b.charAt(j-1)?0:1));
            int[] swap=previous;previous=current;current=swap;
        }return previous[b.length()];
    }
    public static void main(String[] args){System.out.println(distance("parcel","parcels"));System.out.println(distance("label","table"));System.out.println(distance("","PK"));}
}''','1\n3\n2',
['Time is O(mn), and auxiliary row storage is O(min(m,n)). Empty-input handling still needs linear row initialization or traversal under this implementation. UTF-16 distance can differ from code-point or grapheme-cluster distance.'],
['Two-row storage does not automatically provide an edit script.','A smaller memory footprint does not reduce quadratic work.','Specify the text unit before interpreting the score.'],[('grapheme-boundaries','Display units'),('tabulation','State dependency order')],subject='java-dsa')

put('longest-subsequence','Java longest common subsequence: ordering without contiguity',
'A common subsequence preserves element order in two sequences without requiring those elements to occupy adjacent positions.',
[('Do not substitute substring reasoning',[
'Two versioned manifests can share an ordered sequence of reference characters even when one contains extra characters between them. A substring operation requires contiguity and answers a different question. This implementation returns a length only, making that distinction explicit.',
'On a match, the current length comes from the previous diagonal plus one. On a mismatch, it comes from the larger of skipping one position in either sequence. Before updating a cell in place, save its old value because the next position still needs that prior-row diagonal.',
'The implementation uses one row and a diagonal temporary value. That preserves the recurrence while reducing storage. It does not return the matched positions or sequence. A diff view needs a reconstruction strategy and must decide how ties are broken.'
]),('Keep comparisons literal',[
'The fixture compares UTF-16 code units exactly. It does not normalize, ignore case or apply locale collation. Those transformations change the sequence and can change the answer, so apply them only under an explicit field policy before running the algorithm.'
])],'''public class ManifestCommonOrder {
    static int length(String a,String b){
        java.util.Objects.requireNonNull(a);java.util.Objects.requireNonNull(b);
        if((long)a.length()*b.length()>4_000_000)throw new IllegalArgumentException("Subsequence work budget");
        if(a.length()<b.length()){String swap=a;a=b;b=swap;}int[] row=new int[b.length()+1];
        for(int i=0;i<a.length();i++){
            int diagonal=0;
            for(int j=1;j<row.length;j++){int old=row[j];row[j]=a.charAt(i)==b.charAt(j-1)?diagonal+1:Math.max(row[j],row[j-1]);diagonal=old;}
        }return row[b.length()];
    }
    public static void main(String[] args){System.out.println(length("PKRSL","PRL"));System.out.println(length("ABC","XYZ"));System.out.println(length("","PK"));}
}''','3\n0\n0',
['Time is O(mn); working storage is O(min(m,n)). The returned length is not a set intersection count and not a contiguous match length. The checked work budget does not turn the algorithm into a real-time service contract.'],
['Keep the previous diagonal before overwriting a row entry.','A subsequence need not be contiguous.','Length-only state cannot identify the chosen matching positions.'],[('edit-distance','Another sequence recurrence'),('kmp-search','Contiguous matching')],subject='java-dsa')

put('increasing-subsequence','Java longest increasing subsequence: tails are search state',
'The longest increasing subsequence problem asks for the maximum length of an order-preserving sequence whose successive values are strictly greater.',
[('Interpret the tails array correctly',[
'The tails array keeps the smallest known tail value for each achieved subsequence length. It is search state. Its entries can come from different subsequences, so printing that array does not reconstruct one selected solution.',
'A lower-bound search replaces the first tail greater than or equal to the incoming value. Equal values therefore do not extend the strictly increasing length. A non-decreasing problem uses a different boundary; changing that comparison changes the contract.',
'Negative values and integer extremes need no subtraction-based comparator. Direct comparisons avoid overflow when the distance between values exceeds the int range. The input remains unchanged because only the separate tails array is modified.'
]),('Choose reconstruction separately',[
'If a caller needs actual indices, store predecessor indices and which input position currently represents each tail. That extra state has a purpose: reconstructing one valid solution. Keep a deterministic tie policy if the displayed solution matters to users.'
])],'''public class ArrivalIncreasingOrder {
    static int length(int[] values){
        int[] tails=new int[values.length];int used=0;
        for(int value:values){
            int low=0,high=used;
            while(low<high){int middle=low+(high-low)/2;if(tails[middle]<value)low=middle+1;else high=middle;}
            tails[low]=value;if(low==used)used++;
        }return used;
    }
    public static void main(String[] args){System.out.println(length(new int[]{7,3,5,5,8,1,9}));System.out.println(length(new int[]{4,4,4}));System.out.println(length(new int[0]));}
}''','4\n1\n0',
['Time is O(n log n); the tails array uses O(n) storage. A simple O(n²) reference is useful for verifying small inputs independently. This implementation returns only the length and never mutates the input array.'],
['The tails array is not necessarily the selected subsequence.','Strictly increasing and non-decreasing use different equal-value handling.','Do not compare by subtracting arbitrary int values.'],[('binary-search','Boundary search'),('longest-subsequence','Sequence order')],subject='java-dsa')

put('zero-one-knapsack','Java 0/1 knapsack: reverse capacity iteration prevents reuse',
'0/1 knapsack selects each item at most once to maximize total value under a capacity limit.',
[('Use the previous item state',[
'A dispatch bag has a weight budget and a fixed collection of candidate items. The recurrence can skip an item or include it using capacity that existed before that item’s pass. Iterating capacities downward preserves that previous-item state in one array.',
'Ascending capacity iteration would let an item’s updated value feed another position during the same pass, allowing repeated use. That is a different, unbounded problem. The loop direction is therefore part of the correctness argument rather than a micro-optimization.',
'This fixture requires positive weights and non-negative values. Zero-weight items need a separate rule; the program rejects them instead of leaving their behavior accidental. Checked addition rejects a value total outside long range.'
]),('Budget the state space',[
'The program limits capacity to 100,000 and the item-capacity product to five million updates. Those bounds are for the tutorial model. Very large weights with small item counts can call for another formulation rather than allocating a row with one slot per possible capacity.'
])],'''public class DispatchBagValue {
    static long maximum(int capacity,int[] weights,long[] values){
        if(capacity<0||capacity>100_000||weights.length!=values.length||(long)capacity*weights.length>5_000_000)throw new IllegalArgumentException("Knapsack budget");
        for(int i=0;i<weights.length;i++)if(weights[i]<=0||values[i]<0)throw new IllegalArgumentException("Item contract");
        long[] best=new long[capacity+1];
        for(int i=0;i<weights.length;i++)for(int available=capacity;available>=weights[i];available--)
            best[available]=Math.max(best[available],Math.addExact(best[available-weights[i]],values[i]));
        return best[capacity];
    }
    public static void main(String[] args){System.out.println(maximum(7,new int[]{3,4,5},new long[]{8,10,12}));System.out.println(maximum(6,new int[]{3},new long[]{8}));System.out.println(maximum(0,new int[]{3},new long[]{8}));}
}''','18\n8\n0',
['Time is O(nC), storage is O(C), where C is the numeric capacity. This is pseudo-polynomial because capacity size is not the number of bits needed to encode it. The result is a value only; selected items require reconstruction state.'],
['Ascending capacity order changes the problem to allow reuse.','Reject unsupported zero-weight input explicitly.','A value total can overflow even when individual item values fit.'],[('tabulation','Dependency order'),('greedy-intervals','Objective-specific greedy choices')],subject='java-dsa')

put('fenwick-tree','Java Fenwick tree: point additions and half-open prefix sums',
'A Fenwick tree stores partial sums indexed by powers of two so a point addition and a prefix-sum query each visit logarithmically many entries.',
[('Keep external indices consistent',[
'The service exposes zero-based positions and an exclusive prefix end. Internally, the array uses one-based positions because the lowest set bit identifies the parent interval. Mixing those conventions can create an infinite update loop at zero or include the wrong endpoint.',
'An update adds a delta; it does not assign a new absolute value. Replacing a stored measurement requires knowing its prior value and computing the difference. The range query subtracts two prefix sums and accepts an empty half-open interval.',
'The fixture supports signed totals but bounds their cumulative absolute update budget to Long.MAX_VALUE / 4. That conservative rule ensures all internal partial sums and range differences remain representable. It is a declared limitation, not a promise that arbitrary long updates are safe.'
]),('Reject before changing nodes',[
'The budget and index checks run before the update walks the tree. A rejected delta therefore leaves every partial sum unchanged. Without that ordering, an overflow at a later ancestor could leave earlier nodes updated and the representation inconsistent.'
])],'''public class ReceiptFenwickTotals {
    final long[] sums;long spent;
    ReceiptFenwickTotals(int size){if(size<0||size>1_000_000)throw new IllegalArgumentException("Tree size");sums=new long[size+1];}
    void add(int index,long delta){
        if(index<0||index>=sums.length-1||delta==Long.MIN_VALUE)throw new IllegalArgumentException("Update boundary");
        long cost=Math.abs(delta),budget=Long.MAX_VALUE/4;if(cost>budget-spent)throw new IllegalArgumentException("Magnitude budget");
        spent+=cost;for(int slot=index+1;slot<sums.length;slot+=slot&-slot)sums[slot]+=delta;
    }
    long prefix(int end){if(end<0||end>=sums.length)throw new IllegalArgumentException("Prefix boundary");long total=0;for(int slot=end;slot>0;slot-=slot&-slot)total+=sums[slot];return total;}
    long range(int start,int end){if(start<0||start>end||end>=sums.length)throw new IllegalArgumentException("Range boundary");return prefix(end)-prefix(start);}
    public static void main(String[] args){ReceiptFenwickTotals totals=new ReceiptFenwickTotals(4);totals.add(0,4);totals.add(1,7);totals.add(3,-2);System.out.println(totals.prefix(2));System.out.println(totals.range(1,4));System.out.println(totals.range(2,2));}
}''','11\n5\n0',
['Point addition and prefix/range queries take O(log n); storage is O(n). This mutable structure is not synchronized. Its conservative cumulative-magnitude budget can reject later updates even when the current aggregate happens to be small after cancellations.'],
['The external prefix endpoint is exclusive.','An addition is not an absolute assignment.','Do not discover overflow after partially mutating the tree.'],[('arrays','Array boundaries'),('binary-search','Index reasoning')],subject='java-dsa')

put('multi-index-invariants','Java multi-map invariants: one lock for a reservation boundary',
'A multi-map invariant relates values stored in several structures, so thread-safe individual map operations do not automatically make the combined update atomic.',
[('Choose the publication boundary',[
'A stock map and a reservation map must agree about each accepted reservation. Decrementing stock before publishing a reservation lets a reader observe missing inventory with no corresponding owner. Publishing first exposes the opposite intermediate state.',
'This service owns both maps behind one lock. It checks quantity, availability and duplicate reference before changing either structure. The status operation acquires the same lock and returns a detached text result, preventing the caller from walking a live map outside the invariant boundary.',
'ConcurrentHashMap would make individual operations safe but would not join these two structures into a transaction. A database transaction or another protocol may be needed when ownership spans processes. This in-memory lock coordinates threads in one service instance only.'
]),('Reject without partial work',[
'The failed reservation in the program leaves stock and reservation count unchanged. No external network call is performed under the lock. If an operation must contact a supplier, decide how pending state and compensation work; holding this lock indefinitely is not an application-wide transaction solution.'
])],'''import java.util.*;
import java.util.concurrent.locks.ReentrantLock;
public class StockReservationBoundary {
    final ReentrantLock lock=new ReentrantLock();final Map<String,Integer> stock=new HashMap<>(),reserved=new HashMap<>();
    StockReservationBoundary(){stock.put("PACK",7);}
    boolean reserve(String reference,int units){
        if(reference==null||reference.isEmpty()||units<=0)throw new IllegalArgumentException("Reservation input");
        lock.lock();try{
            if(reserved.containsKey(reference)||stock.get("PACK")<units)return false;
            stock.put("PACK",stock.get("PACK")-units);reserved.put(reference,units);return true;
        }finally{lock.unlock();}
    }
    String status(){lock.lock();try{return "stock="+stock.get("PACK")+", reservations="+reserved.size();}finally{lock.unlock();}}
    public static void main(String[] args){StockReservationBoundary service=new StockReservationBoundary();System.out.println(service.reserve("R-71",8));System.out.println(service.status());System.out.println(service.reserve("R-71",3));System.out.println(service.status());}
}''','false\nstock=7, reservations=0\ntrue\nstock=4, reservations=1',
['Under normal hash distribution the map operations have expected constant lookup work, but lock waiting can dominate latency. Memory grows with retained reservations. Completed state still needs an expiry or archival rule in a long-running service. This model does not provide crash recovery or a transaction across JVMs.'],
['Readers must obey the same invariant boundary as writers.','Separate concurrent maps do not create a cross-map transaction.','Do not hold an application lock across unbounded external I/O.'],[('concurrent-map','Per-map operations'),('locks','Lock ownership'),('jdbc-transactions','Database transactions')])

put('transaction-races-interview','Java race interview: deterministic lost updates and atomic per-key changes',
'A lost update occurs when two operations read the same prior value and later overwrite one another’s computed changes.',
[('Produce the interleaving explicitly',[
'Two workers each subtract three units from a stock value of seven. The first phase waits until both workers have read seven before allowing either to write. Both then publish four. Each map call is individually safe, but one subtraction has disappeared.',
'The latches define the problematic interleaving. A sleep-based demonstration might pass or fail depending on scheduler timing and would not prove that both reads preceded both writes. The worker futures also provide a completion boundary before the result is inspected.',
'The corrected phase uses compute for each key update. That operation expresses the per-key transformation as one map operation. It still does not make a second map or an external message part of the same atomic boundary.'
]),('Explain failure and ownership',[
'An interview answer should distinguish thread-safe storage from a valid application protocol. It should also account for worker failure and shutdown. The program bounds its waits, observes future results and closes its executor; it does not leave hidden background work running after the example finishes.'
])],'''import java.util.concurrent.*;
public class LostStockUpdateTrace {
    public static void main(String[] args)throws Exception{
        ConcurrentHashMap<String,Integer> stock=new ConcurrentHashMap<>();stock.put("PACK",7);
        ExecutorService pool=Executors.newFixedThreadPool(2);CountDownLatch read=new CountDownLatch(2),publish=new CountDownLatch(1);
        try{
            Callable<Void> broken=()->{int prior=stock.get("PACK");read.countDown();if(!publish.await(2,TimeUnit.SECONDS))throw new IllegalStateException("Publish wait");stock.put("PACK",prior-3);return null;};
            Future<Void> first=pool.submit(broken),second=pool.submit(broken);
            if(!read.await(2,TimeUnit.SECONDS))throw new IllegalStateException("Read wait");publish.countDown();first.get(2,TimeUnit.SECONDS);second.get(2,TimeUnit.SECONDS);System.out.println(stock.get("PACK"));
            stock.put("PACK",7);Runnable corrected=()->stock.compute("PACK",(key,prior)->prior-3);
            Future<?> a=pool.submit(corrected),b=pool.submit(corrected);a.get(2,TimeUnit.SECONDS);b.get(2,TimeUnit.SECONDS);System.out.println(stock.get("PACK"));
        }finally{publish.countDown();pool.shutdownNow();if(!pool.awaitTermination(2,TimeUnit.SECONDS))throw new IllegalStateException("Workers alive");}
    }
}''','4\n1',
['The trace has a fixed two-worker state. Map updates have their implementation costs plus contention; the latches deliberately wait for a specified interleaving. The corrected arithmetic assumes the prior value exists and the requested subtraction is valid. A real stock rule must check availability inside the atomic operation.'],
['Thread-safe get and put do not combine into an atomic transformation.','Sleeping does not prove the intended interleaving happened.','Per-key compute cannot commit an external side effect.'],[('multi-index-invariants','Several structures'),('concurrent-map','Atomic map operations')],subject='java-interview')

put('heap-dump-workflow','Java heap diagnostics: retained objects, histograms and a controlled dump',
'A heap histogram counts objects by class, while a heap dump records object state and references needed to investigate why particular objects remain reachable.',
[('Capture a JVM you own',[
'The fixture retains fifty receipt entries through one static list. Each entry owns a small byte array. The static field is an identifiable retention path; an increasing allocation count alone would not explain why an object survives collection.',
'Run the downloaded diagnostic script against the fixture it starts, rather than attaching to an arbitrary application PID. It collects a live histogram and heap dump using that same JDK’s jcmd, verifies the fixture’s entry count, then stops the fixture and removes its temporary dump. No user process or application secret is inspected.',
'A histogram can reveal a class growing between captures, but it does not show which reference keeps a particular instance alive. A dump and reference-path analysis answer that second question. The object’s shallow byte count is also different from the memory retained by the reachable subgraph behind it.'
]),('Separate the leak hypothesis from evidence',[
'Fifty intentionally retained entries are not a leak. To diagnose a leak, relate retained state to the application’s intended lifetime, compare captures after comparable work, and identify a path that should have been released. A cache without an eviction policy is one candidate; a live queue carrying unfinished work can be legitimate.'
])],'''import java.util.*;
import java.util.concurrent.*;
public class RetainedReceiptFixture {
    static final List<Entry> retained=new ArrayList<>();
    static final class Entry {final byte[] payload=new byte[1024];}
    public static void main(String[] args)throws Exception{
        for(int i=0;i<50;i++)retained.add(new Entry());
        System.out.println("retained="+retained.size());
        if(args.length==1&&args[0].equals("--inspect")){
            System.out.println("ready");System.out.flush();new CountDownLatch(1).await(30,TimeUnit.SECONDS);
        }
    }
}''','retained=50',
['This fixture retains fifty entries plus their payloads. A histogram or dump can trigger substantial work and pauses; capture it only under an approved operational procedure for a real service. The bundled check covers controlled capture, not a complete graphical retained-size investigation or a production incident.'],
['Allocated bytes and currently retained bytes are different measurements.','A histogram does not expose every retaining reference path.','Heap dumps can contain application data; the fixture contains only synthetic bytes.'],[('jvm-memory','Reachability'),('gc-diagnostics','Collection observations'),('weak-references','Weak lifetime')],release=21)

put('jfr-incident-workflow','Java JFR incident evidence: outcome events and failure counts',
'A JFR recording captures enabled events during a defined interval, allowing an incident review to correlate operation outcomes with runtime observations.',
[('Record the operation boundary',[
'A file-import operation should report success or failure at the boundary where that result becomes known. Recording only successful imports hides failed work from the incident timeline. The custom event below records an outcome in finally, including the rejected branch.',
'Keep event fields small and intentional. Counts and phase labels can be useful without storing full input lines, credentials or user payloads. Stack traces and event thresholds also affect what the recording contains; a missing event does not prove that no operation was attempted.',
'The program owns a short recording, commits two operation events, dumps the recording and reads it back. It counts successful and failed outcomes independently. That checks the capture and consumption path instead of merely printing a recording file name.'
]),('Compare a defined interval',[
'For an incident, write down which JVM, workload and recording interval produced the artifact. CPU sampling, allocations, lock contention and application events answer different questions. A short synthetic fixture can validate event plumbing, but its counts and durations are not a production latency distribution.'
])],'''import jdk.jfr.*;
import jdk.jfr.consumer.*;
import java.nio.file.*;
@Name("in.aitrove.ImportOutcome")
class ImportOutcome extends Event {boolean success;int rows;}
public class ImportOutcomeRecording {
    static void importRows(int rows,boolean reject){
        ImportOutcome event=new ImportOutcome();event.begin();
        try{if(reject)throw new IllegalArgumentException("Rejected rows");event.rows=rows;event.success=true;}
        catch(IllegalArgumentException failed){event.success=false;}
        finally{event.end();event.commit();}
    }
    public static void main(String[] args)throws Exception{
        Path file=Files.createTempFile("aitrove-outcomes-",".jfr");
        try(Recording recording=new Recording()){
            recording.enable(ImportOutcome.class).withStackTrace();recording.start();importRows(4,false);importRows(0,true);recording.stop();recording.dump(file);
            int accepted=0,rejected=0;
            try(RecordingFile events=new RecordingFile(file)){
                while(events.hasMoreEvents()){RecordedEvent event=events.readEvent();if(event.getEventType().getName().equals("in.aitrove.ImportOutcome")){if(event.getBoolean("success"))accepted++;else rejected++;}}
            }System.out.println("accepted="+accepted+", rejected="+rejected);
        }finally{Files.deleteIfExists(file);}
    }
}''','accepted=1, rejected=1',
['Recorded volume grows with the enabled event rate and fields. Stack traces and event settings have their own cost. This fixture checks two events, not JFR overhead under production load, and the finally block cleans its own temporary file.'],
['Success-only events omit the failure side of an incident.','Thresholds and settings can suppress observations.','A synthetic recording is not a production performance conclusion.'],[('flight-recorder','Recording APIs'),('heap-dump-workflow','Retained-state evidence')],release=11)

put('database-isolation','Java JDBC isolation: uncommitted writes and separate sessions',
'Transaction isolation determines which changes a database session can observe and how concurrent operations interact; it is a database contract, not just a Java enum.',
[('Use two physical sessions',[
'The example opens writer and reader connections to the same local H2 database. The writer updates a quantity without committing. Under READ_COMMITTED, the reader’s ordinary query observes the committed value, then observes the new value after the writer commits.',
'Two logical calls through one connection would not prove this boundary because a transaction ordinarily sees its own writes. The fixture therefore owns two connections and sets their transaction modes explicitly. It also rolls back in cleanup if an uncommitted writer path remains.',
'Isolation names do not define every engine’s locking, snapshot or retry behavior. The verified output belongs to H2 2.3.232 under this workload. PostgreSQL, MySQL and another engine need their own integration tests before the application relies on a specific interleaving.'
]),('Design the complete read-modify-write rule',[
'An isolation setting alone does not make a stock reservation correct. Decide whether the operation uses a locked row, a conditional update with a checked row count, or a versioned optimistic update. Handle deadlock or serialization failure with a bounded whole-transaction retry policy where that engine requires it.'
])],'''import java.sql.*;
public class ReceiptIsolationSessions {
    static int read(Connection connection)throws SQLException{
        try(PreparedStatement query=connection.prepareStatement("SELECT units FROM stock WHERE id=1");ResultSet rows=query.executeQuery()){if(!rows.next())throw new SQLException("Missing stock");return rows.getInt(1);}
    }
    public static void main(String[] args)throws Exception{
        String url="jdbc:h2:mem:isolation_"+java.util.UUID.randomUUID();
        try(Connection writer=DriverManager.getConnection(url);Connection reader=DriverManager.getConnection(url)){
            try(Statement schema=writer.createStatement()){schema.execute("CREATE TABLE stock(id INT PRIMARY KEY, units INT)");schema.executeUpdate("INSERT INTO stock VALUES(1,7)");}
            reader.setTransactionIsolation(Connection.TRANSACTION_READ_COMMITTED);writer.setAutoCommit(false);
            try{
                try(PreparedStatement update=writer.prepareStatement("UPDATE stock SET units=? WHERE id=1")){update.setInt(1,11);if(update.executeUpdate()!=1)throw new SQLException("Missing update");}
                System.out.println(read(reader));writer.commit();System.out.println(read(reader));
            }finally{writer.rollback();}
        }
    }
}''','7\n11',
['This query touches one primary-key row. Real cost includes database scheduling, locking, I/O and round trips. The fixture verifies one visibility case in H2; it does not establish phantom-read, write-skew or distributed-transaction behavior for another database.'],
['One connection is not evidence of visibility across two sessions.','The same isolation name can have engine-specific details.','A retry must replay a complete valid transaction boundary.'],[('jdbc-transactions','Commit and rollback'),('database-project','Repository invariant')],dependency='h2')

put('connection-pool','Java connection pools: borrowed handles, rollback and admission timeout',
'A connection pool lends logical connection handles over a bounded collection of physical database connections; closing a borrowed handle ordinarily returns it to the pool.',
[('Keep the transaction with the borrower',[
'The pool below has one maximum connection and a finite acquisition timeout. A caller owns the borrowed handle only for its operation. The handle must be closed on every path so another caller can borrow capacity; closing it is different from shutting down the pool itself.',
'The fixture disables auto-commit, creates its table, starts a data change and rolls that change back. A later borrower sees zero rows. That check is about transaction cleanup, not a throughput claim. The code calls rollback explicitly rather than depending on implicit pool cleanup to define business behavior.',
'The program also holds the only connection while attempting a second borrow. The timed rejection verifies that saturation is visible as an exception, rather than an unbounded wait. A larger pool does not automatically improve database throughput; it can move contention into the server.'
]),('Budget admission and the admitted operation',[
'Connection acquisition timeout is not a statement execution timeout or a complete request deadline. A service needs a policy for each stage and a shutdown owner for the pool. Monitor active, waiting and timed-out borrowers under representative workload before choosing a production capacity.'
])],'''import com.zaxxer.hikari.*;
import java.sql.*;
public class PooledReceiptBoundary {
    public static void main(String[] args)throws Exception{
        HikariConfig config=new HikariConfig();config.setJdbcUrl("jdbc:h2:mem:pool_"+java.util.UUID.randomUUID()+";DB_CLOSE_DELAY=-1");config.setMaximumPoolSize(1);config.setMinimumIdle(0);config.setConnectionTimeout(300);config.setAutoCommit(false);
        try(HikariDataSource pool=new HikariDataSource(config)){
            try(Connection connection=pool.getConnection()){
                try(Statement sql=connection.createStatement()){sql.execute("CREATE TABLE receipts(id INT PRIMARY KEY)");}
                try(PreparedStatement insert=connection.prepareStatement("INSERT INTO receipts VALUES(?)")){insert.setInt(1,17);insert.executeUpdate();}connection.rollback();
            }
            try(Connection held=pool.getConnection()){
                try(Statement query=held.createStatement();ResultSet rows=query.executeQuery("SELECT COUNT(*) FROM receipts")){rows.next();System.out.println(rows.getInt(1));}
                try(Connection unexpected=pool.getConnection()){throw new IllegalStateException("Second borrow admitted");}
                catch(SQLTransientConnectionException saturated){System.out.println("pool timeout");}held.rollback();
            }
            try(Connection again=pool.getConnection()){System.out.println(again.isValid(1));again.rollback();}
        }
    }
}''','0\npool timeout\ntrue',
['The pool retains at most the configured physical connections, but each connection also has driver and server-side state. Saturated acquisition waits up to its configured policy, subject to scheduling. This H2 fixture checks borrow/return, rollback and saturation; it does not size a production database pool.'],
['Closing a borrowed handle is not the same as closing the pool.','Acquisition timeout does not bound the SQL statement.','Do not retain a borrowed connection while waiting for unrelated work.'],[('database-isolation','Session visibility'),('semaphores','Admission accounting')],release=17,dependency='hikari')

put('versioned-migrations','Java versioned data changes: checksums and a committed ledger',
'A versioned data migration records which data transformation was applied and rejects a changed definition for an already recorded version.',
[('Make the replay rule explicit',[
'This fixture migrates seed data, not arbitrary schema DDL. The schema is bootstrapped separately because DDL transaction behavior differs by database. The migration’s inserted row and its version/checksum record share one DML transaction.',
'A second launch with the same version and checksum is a no-op. A different checksum for an applied version is rejected before another data change. That protects the meaning of the recorded history; it does not decide how an operator should repair an already deployed mistake.',
'The checksum is derived from a declared UTF-8 migration string. A real migration tool also needs ordered discovery, locking, state validation and a recovery procedure. This program intentionally has one migration and one owner, so it does not claim to coordinate two simultaneous deployers.'
]),('Handle rollback without hiding the primary failure',[
'The migration owner commits after both writes and rolls back after failure. If rollback itself fails, attach that failure to the original exception rather than replacing the cause of the failed change. A migration that sends an external message needs a separate publication rule because a JDBC rollback cannot retract it.'
])],'''import java.sql.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
public class SeedMigrationLedger {
    static String checksum(String definition)throws Exception{
        byte[] digest=MessageDigest.getInstance("SHA-256").digest(definition.getBytes(StandardCharsets.UTF_8));StringBuilder value=new StringBuilder();for(byte part:digest)value.append(String.format("%02x",part&255));return value.toString();
    }
    static boolean apply(Connection connection,String definition)throws Exception{
        String digest=checksum(definition);connection.setAutoCommit(false);
        try{
            try(PreparedStatement query=connection.prepareStatement("SELECT checksum FROM versions WHERE version=1");ResultSet rows=query.executeQuery()){
                if(rows.next()){if(!digest.equals(rows.getString(1)))throw new IllegalStateException("Migration definition changed");connection.commit();return false;}
            }
            try(PreparedStatement seed=connection.prepareStatement("INSERT INTO labels VALUES(?,?)")){seed.setInt(1,31);seed.setString(2,"Ready");seed.executeUpdate();}
            try(PreparedStatement record=connection.prepareStatement("INSERT INTO versions VALUES(1,?)")){record.setString(1,digest);record.executeUpdate();}connection.commit();return true;
        }catch(Exception failure){try{connection.rollback();}catch(SQLException rollback){failure.addSuppressed(rollback);}throw failure;}
    }
    public static void main(String[] args)throws Exception{
        try(Connection database=DriverManager.getConnection("jdbc:h2:mem:migration_"+java.util.UUID.randomUUID())){
            try(Statement schema=database.createStatement()){schema.execute("CREATE TABLE versions(version INT PRIMARY KEY, checksum VARCHAR(64))");schema.execute("CREATE TABLE labels(id INT PRIMARY KEY, label VARCHAR(40))");}
            System.out.println(apply(database,"seed-label-31-v1"));System.out.println(apply(database,"seed-label-31-v1"));
            try{apply(database,"seed-label-31-edited");}catch(IllegalStateException changed){System.out.println(changed.getMessage());}
        }
    }
}''','true\nfalse\nMigration definition changed',
['Hashing costs O(m) for a definition of m bytes; the database operations add transaction and I/O costs. The single-version fixture is not a replacement for a migration system’s ordered history or deployment locking. Schema bootstrap is outside the shown data-migration transaction.'],
['Do not edit an applied migration and pretend its history is unchanged.','DDL and DML transaction behavior require engine-specific verification.','A version table alone does not coordinate concurrent deployers.'],[('jdbc-transactions','Transaction ownership'),('database-isolation','Engine-specific behavior')],dependency='h2')

put('http-failure-project','Java HTTP retry project: bounded attempts and one wait budget',
'An HTTP retry repeats a selected operation after a classified failure, so both replay safety and the total attempt budget belong to the client contract.',
[('Retry a repeatable operation',[
'The local server returns 503 on its first GET and 200 on its next GET. The client retries this read-only operation at most three times under one monotonic wait budget. A timeout or status does not automatically justify replaying a payment or another state-changing request.',
'Each attempt receives only the remaining budget. Starting a fresh full timeout for every attempt would let a request exceed its intended total wait. The program checks for exhaustion before sending and preserves interruption instead of treating it as another transient server failure.',
'This model retries a classified status only. It does not add random backoff, honor Retry-After or coordinate a shared rate limit. Those production policies need a representative load and service contract; a local two-response fixture cannot select them for every API.'
]),('Observe status before parsing',[
'A received 503 is an HTTP response, not necessarily a transport exception. The client checks the status before treating the body as a quote. A response body parser also needs its own size and schema limits; the tiny synthetic body here is not an untrusted-data policy.'
])],'''import com.sun.net.httpserver.HttpServer;
import java.net.*;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
public class RetriedLocalQuote {
    static String fetch(HttpClient client,URI uri,Duration budget)throws Exception{
        long deadline=System.nanoTime()+budget.toNanos();
        for(int attempt=0;attempt<3;attempt++){
            long remaining=deadline-System.nanoTime();if(remaining<=0)throw new TimeoutException("Quote budget");
            HttpRequest request=HttpRequest.newBuilder(uri).timeout(Duration.ofNanos(remaining)).GET().build();
            HttpResponse<String> response=client.send(request,HttpResponse.BodyHandlers.ofString());
            if(response.statusCode()==200)return response.body();if(response.statusCode()!=503)throw new IllegalStateException("Unexpected HTTP status");
        }throw new IllegalStateException("Attempt limit");
    }
    public static void main(String[] args)throws Exception{
        AtomicInteger calls=new AtomicInteger();HttpServer server=HttpServer.create(new InetSocketAddress(InetAddress.getLoopbackAddress(),0),0);ExecutorService handlers=Executors.newSingleThreadExecutor();server.setExecutor(handlers);
        server.createContext("/quote",exchange->{int attempt=calls.incrementAndGet();byte[] body=(attempt==1?"busy":"quote=150").getBytes(StandardCharsets.UTF_8);exchange.sendResponseHeaders(attempt==1?503:200,body.length);try(java.io.OutputStream output=exchange.getResponseBody()){output.write(body);}});server.start();
        try{
            URI uri=new URI("http",null,server.getAddress().getAddress().getHostAddress(),server.getAddress().getPort(),"/quote",null,null);
            HttpClient client=HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(1)).build();System.out.println(fetch(client,uri,Duration.ofSeconds(2)));System.out.println("attempts="+calls.get());
        }finally{server.stop(0);handlers.shutdownNow();if(!handlers.awaitTermination(2,TimeUnit.SECONDS))throw new IllegalStateException("Server worker");}
    }
}''','quote=150\nattempts=2',
['At most three sequential attempts are admitted, each with a remaining request timeout. Cleanup has a separate bounded worker wait. This fixture does not establish an end-to-end deadline for arbitrary DNS, response processing or external side effects, and it is not a server load test.'],
['A failed response is not proof that a state-changing operation never took effect.','Do not reset the entire budget for each retry.','Interruption is not a server status to retry blindly.'],[('http-project','Local response handling'),('cancellation','Shared deadlines')],subject='java-projects',release=11)

put('tls-local-project','Java HTTPS project: a trusted local certificate and a rejected hostname',
'TLS certificate trust and hostname verification are separate checks: trusting a certificate does not make it valid for every server name.',
[('Trust only this fixture’s certificate',[
'The program creates an ephemeral local PKCS12 store using the current JDK’s keytool. Its certificate has a localhost DNS subject alternative name. The server owns the private key, while the client trust store receives only that certificate. The password is a synthetic fixture value, not a service credential.',
'The first request addresses localhost and succeeds. The second addresses the numeric loopback address, which is absent from the certificate’s identities, and must fail hostname verification. The client does not install an accept-all trust manager or disable endpoint identification to make the request pass.',
'All files are created in the fixture’s temporary directory and removed on exit. The generated key is not bundled in the public source ZIP. In a deployed service, certificate issuance, rotation, trust roots and expiry handling need an operational owner; this local test does not provision a public certificate.'
]),('Verify the rejection path',[
'A successful encrypted response alone is insufficient evidence that hostname checks are enabled. Keep a negative identity test in the integration suite. Transport exceptions also need classification: a certificate failure is not a transient 503 that should be retried until it works.'
])],'''import com.sun.net.httpserver.*;
import javax.net.ssl.*;
import java.net.*;
import java.net.http.*;
import java.nio.file.*;
import java.security.KeyStore;
import java.time.Duration;
import java.util.concurrent.*;
public class LocalTlsIdentity {
    public static void main(String[] args)throws Exception{
        Path directory=Files.createTempDirectory("aitrove-tls-"),store=directory.resolve("fixture.p12"),log=directory.resolve("keytool.log");char[] password="fixture-only".toCharArray();
        HttpsServer server=null;ExecutorService handlers=Executors.newSingleThreadExecutor();
        try{
            String keytool=Path.of(System.getProperty("java.home"),"bin","keytool").toString();
            Process creation=new ProcessBuilder(keytool,"-genkeypair","-alias","server","-keyalg","RSA","-keysize","2048","-storetype","PKCS12","-keystore",store.toString(),"-storepass",new String(password),"-dname","CN=localhost","-ext","SAN=dns:localhost","-validity","2","-noprompt").redirectErrorStream(true).redirectOutput(log.toFile()).start();
            if(!creation.waitFor(10,TimeUnit.SECONDS)){creation.destroyForcibly();throw new IllegalStateException("Key creation timeout");}if(creation.exitValue()!=0)throw new IllegalStateException("Key creation failed");
            KeyStore keys=KeyStore.getInstance("PKCS12");try(java.io.InputStream input=Files.newInputStream(store)){keys.load(input,password);}
            KeyManagerFactory keyManagers=KeyManagerFactory.getInstance(KeyManagerFactory.getDefaultAlgorithm());keyManagers.init(keys,password);
            SSLContext serverContext=SSLContext.getInstance("TLS");serverContext.init(keyManagers.getKeyManagers(),null,null);
            KeyStore trusted=KeyStore.getInstance("PKCS12");trusted.load(null,null);trusted.setCertificateEntry("fixture",keys.getCertificate("server"));
            TrustManagerFactory trustManagers=TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());trustManagers.init(trusted);
            SSLContext clientContext=SSLContext.getInstance("TLS");clientContext.init(null,trustManagers.getTrustManagers(),null);
            server=HttpsServer.create(new InetSocketAddress(InetAddress.getLoopbackAddress(),0),0);server.setHttpsConfigurator(new HttpsConfigurator(serverContext));server.setExecutor(handlers);
            server.createContext("/receipt",exchange->{byte[] body="tls=verified".getBytes(java.nio.charset.StandardCharsets.UTF_8);exchange.sendResponseHeaders(200,body.length);try(java.io.OutputStream output=exchange.getResponseBody()){output.write(body);}});server.start();
            HttpClient client=HttpClient.newBuilder().sslContext(clientContext).connectTimeout(Duration.ofSeconds(2)).build();int port=server.getAddress().getPort();
            HttpRequest valid=HttpRequest.newBuilder(new URI("https",null,"localhost",port,"/receipt",null,null)).timeout(Duration.ofSeconds(3)).GET().build();
            System.out.println(client.send(valid,HttpResponse.BodyHandlers.ofString()).body());
            HttpRequest invalid=HttpRequest.newBuilder(new URI("https",null,server.getAddress().getAddress().getHostAddress(),port,"/receipt",null,null)).timeout(Duration.ofSeconds(3)).GET().build();
            try{client.send(invalid,HttpResponse.BodyHandlers.ofString());throw new IllegalStateException("Wrong hostname accepted");}
            catch(SSLHandshakeException rejected){System.out.println("hostname rejected");}
        }finally{
            if(server!=null)server.stop(0);handlers.shutdownNow();if(!handlers.awaitTermination(2,TimeUnit.SECONDS))throw new IllegalStateException("TLS worker");
            Files.deleteIfExists(store);Files.deleteIfExists(log);Files.deleteIfExists(directory);
        }
    }
}''','tls=verified\nhostname rejected',
['Key generation, handshake and server startup dominate this small integration fixture; no latency ranking is inferred. The keytool subprocess has a ten-second creation bound and requests have explicit timeouts. A real service needs public certificate lifecycle, protocol policy and engine-specific testing beyond this isolated loopback exchange.'],
['Trusted does not mean valid for every hostname.','Do not disable verification to hide a certificate-name mismatch.','Never treat the fixture password or certificate as a production credential.'],[('http-client','Client operations'),('http-failure-project','Failure classification')],subject='java-projects',release=11)

put('concurrent-import-project','Java concurrent import project: validated worker results before file publication',
'A concurrent import can compute independent row results in workers while reserving one owner for validation and publication of the final snapshot.',
[('Workers return proposed values',[
'Each worker parses one receipt row and returns an immutable result. It does not append to the published file or decrement a shared total. The owner collects every result, rejects duplicate references, and writes the snapshot only when the complete proposed set is valid.',
'This separates completed computation from publication. If one row fails, the old snapshot remains unchanged. Cancellation requests stop outstanding work, and executor termination is checked before the import operation returns. The program’s invalid-row case verifies that failure does not publish the successful row beside it.',
'The executor has two workers and a bounded pending queue. The input is also bounded by file size, row count and row length. A small queue by itself would not bound all memory if the caller eagerly materialized an unlimited file before submitting it.'
]),('Describe the deadline honestly',[
'One monotonic budget covers submission and result waiting. Reading the owned input file and final filesystem publication remain separate synchronous stages, so this fixture does not promise an end-to-end service deadline or crash-durable persistence. A regular move publishes this single-writer snapshot; it is not a distributed transaction.'
])],'''import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;
public class ConcurrentReceiptImport {
    static class Row {final String reference;final int units;Row(String reference,int units){this.reference=reference;this.units=units;}}
    static Row parse(String line){
        if(line.length()>80)throw new IllegalArgumentException("Row length");String[] fields=line.split(",",-1);
        if(fields.length!=2||!fields[0].matches("R-[0-9]{1,8}"))throw new IllegalArgumentException("Receipt row");
        int units=Integer.parseInt(fields[1]);if(units<0||units>1000)throw new IllegalArgumentException("Unit range");return new Row(fields[0],units);
    }
    static void importFile(Path input,Path output)throws Exception{
        if(Files.size(input)>16_000)throw new IllegalArgumentException("Input size");List<String> lines=Files.readAllLines(input,StandardCharsets.UTF_8);if(lines.size()>6)throw new IllegalArgumentException("Row count");
        ThreadPoolExecutor workers=new ThreadPoolExecutor(2,2,0,TimeUnit.MILLISECONDS,new ArrayBlockingQueue<>(4));List<Future<Row>> pending=new ArrayList<>();long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(2);
        try{
            for(String line:lines)pending.add(workers.submit(()->parse(line)));
            List<String> snapshot=new ArrayList<>();Set<String> references=new HashSet<>();
            for(Future<Row> future:pending){long remaining=deadline-System.nanoTime();if(remaining<=0)throw new TimeoutException("Import budget");Row row=future.get(remaining,TimeUnit.NANOSECONDS);if(!references.add(row.reference))throw new IllegalArgumentException("Duplicate receipt");snapshot.add(row.reference+","+row.units);}
            Path staged=Files.createTempFile(output.getParent(),"snapshot-",".tmp");
            try{Files.write(staged,snapshot,StandardCharsets.UTF_8);Files.move(staged,output,StandardCopyOption.REPLACE_EXISTING);}finally{Files.deleteIfExists(staged);}
        }finally{for(Future<Row> future:pending)future.cancel(true);workers.shutdownNow();if(!workers.awaitTermination(2,TimeUnit.SECONDS))throw new IllegalStateException("Import workers alive");}
    }
    public static void main(String[] args)throws Exception{
        Path directory=Files.createTempDirectory("aitrove-import-"),input=directory.resolve("input.csv"),output=directory.resolve("snapshot.csv");
        try{
            Files.write(input,Arrays.asList("R-41,4","R-42,3"),StandardCharsets.UTF_8);importFile(input,output);System.out.println("published="+Files.readAllLines(output).size());
            Files.write(input,Arrays.asList("R-43,2","invalid"),StandardCharsets.UTF_8);
            try{importFile(input,output);}catch(ExecutionException rejected){System.out.println("invalid row rejected");}
            System.out.println("preserved="+Files.readAllLines(output).size());
        }finally{Files.deleteIfExists(input);Files.deleteIfExists(output);Files.deleteIfExists(directory);}
    }
}''','published=2\ninvalid row rejected\npreserved=2',
['Parsing and materialization use O(n) row work and storage under the declared six-row fixture limit. Two workers do not guarantee a speedup for tiny input. File access assumes one owner of the temporary directory; external file mutation, crash recovery and multi-process publication need another design.'],
['Worker success is not permission to publish a partial batch.','Queue bounds do not bound an already materialized unlimited file.','A result-wait budget is not a universal filesystem deadline.'],[('manifest-project','Validated imports'),('cancellation','Stopping workers'),('reading-list-project','File publication')],subject='java-projects')

put('graph-exercises','Java graph exercises: verify reachability before trusting component labels',
'A graph property exercise checks a relation over vertices independently of the numeric labels or traversal order produced by one algorithm.',
[('Start with a small reference model',[
'For a small graph, a boolean reachability matrix is useful as a reference. It includes zero-length self-reachability, records direct edges, and closes the relation through each intermediate vertex. Mutual reachability then defines whether two vertices belong to one strong component.',
'The completed exercise asks for a cycle group, a one-way edge and an isolated vertex. It verifies both directions when claiming a shared component. Merely observing that the first vertex can reach the second is insufficient.',
'Use this reference on small inputs to check the faster adjacency-list implementation. Its cubic work is acceptable in a bounded test, not a reason to choose a dense matrix for every large sparse application graph.'
]),('Change the fixture deliberately',[
'Add a reverse edge and predict which component groups will merge before running the program. Add an invalid endpoint and require rejection before returning a result. Keep assertions that test graph meaning rather than one incidental ordering of labels.'
])],'''public class ReachabilityExercise {
    static boolean[][] closure(int[][] edges){
        int n=edges.length;if(n>100)throw new IllegalArgumentException("Exercise graph budget");boolean[][] reachable=new boolean[n][n];
        for(int i=0;i<n;i++){reachable[i][i]=true;if(edges[i]==null)throw new IllegalArgumentException("Missing adjacency");for(int to:edges[i]){if(to<0||to>=n)throw new IllegalArgumentException("Endpoint");reachable[i][to]=true;}}
        for(int via=0;via<n;via++)for(int from=0;from<n;from++)for(int to=0;to<n;to++)reachable[from][to]|=reachable[from][via]&&reachable[via][to];return reachable;
    }
    static void require(boolean expected){if(!expected)throw new AssertionError("Reachability exercise");}
    public static void main(String[] args){
        boolean[][] r=closure(new int[][]{{1},{0,2},{},{}});
        require(r[0][1]&&r[1][0]);require(r[0][2]&&!r[2][0]);require(r[3][3]&&!r[3][0]);System.out.println("checks=3");
    }
}''','checks=3',
['The reference takes O(V³) time and O(V²) memory. It is deliberately limited to small test graphs. Reachability does not contain minimum path costs, and a self-reachable vertex does not by itself prove a nonempty cycle.'],
['Mutual reachability needs both directions.','Self-reachability includes the zero-length path.','Traversal labels are not the relation being tested.'],[('strong-components','Linear traversal partition'),('floyd-warshall','Weighted all-pairs paths')],subject='java-exercises')

put('dp-exercises','Java DP exercises: exhaustive small inputs as a reference',
'An exhaustive small-input oracle enumerates every permitted choice and compares the best result with a more efficient recurrence.',
[('Make the oracle use another approach',[
'The knapsack oracle enumerates subsets instead of repeating the one-row capacity recurrence. Each bit means an item is selected once. This gives a separate route to the expected result and exposes accidental repeated use of one item.',
'The completed exercise includes an exact-fit pair, an item that is too heavy, and a single item that cannot be selected twice. The third case is especially useful because an ascending one-row update can mistakenly produce a value of sixteen instead of eight.',
'A reference still needs an input budget. Subset count doubles for every added item, so this program rejects more than twenty candidates. Checked weight and value addition also prevent overflow from silently turning an infeasible subset into a winning one.'
]),('Expand tests by contract',[
'Include duplicate weights, equal values, zero capacity and items with zero value. Reject unsupported negative values or nonpositive weights before enumeration. For a property suite, generate bounded random inputs and compare the oracle with the production recurrence rather than testing only one hand-picked result.'
])],'''public class BagSubsetOracle {
    static long maximum(int capacity,int[] weights,long[] values){
        if(capacity<0||weights.length!=values.length||weights.length>20)throw new IllegalArgumentException("Oracle budget");
        for(int i=0;i<weights.length;i++)if(weights[i]<=0||values[i]<0)throw new IllegalArgumentException("Item contract");
        long best=0;
        for(int mask=0;mask<(1<<weights.length);mask++){
            long weight=0,value=0;for(int i=0;i<weights.length;i++)if((mask&(1<<i))!=0){weight=Math.addExact(weight,weights[i]);value=Math.addExact(value,values[i]);}
            if(weight<=capacity)best=Math.max(best,value);
        }return best;
    }
    public static void main(String[] args){
        if(maximum(7,new int[]{3,4},new long[]{8,10})!=18)throw new AssertionError("Exact pair");
        if(maximum(2,new int[]{3},new long[]{8})!=0)throw new AssertionError("Heavy item");
        if(maximum(6,new int[]{3},new long[]{8})!=8)throw new AssertionError("Repeated item");System.out.println("checks=3");
    }
}''','checks=3',
['Enumeration takes O(n 2^n) time and constant scalar storage beyond the input. This is a small-input test oracle, not an optimization for large candidate sets. A correct oracle can still fail to exercise a missing boundary if the generated test inputs never contain it.'],
['Do not reuse the same recurrence as both implementation and oracle.','An exponential test helper needs a strict candidate limit.','An item bit is a single-use choice.'],[('zero-one-knapsack','Capacity recurrence'),('tabulation','State order')],subject='java-exercises')

# Add explained self-checks for the new release and algorithm contracts.
def bank(slug,title,items):
 path='quizzes/'+slug;e=copy.deepcopy(lookup['quizzes/java-modern']);qs=[]
 for index,(prompt,correct,wrong1,wrong2,explanation) in enumerate(items):
  choices=[correct,wrong1,wrong2];shift=index%3;choices=choices[shift:]+choices[:shift];qs.append({'prompt':prompt,'options':choices,'answer':choices.index(correct),'explanation':explanation})
 e.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),path=path,title=title,summary='A local self-check of '+title.lower()+', with explained answers.',body=para('This quiz checks operation contracts and failure boundaries using local multiple-choice questions.')+para('Select an answer for each question, then submit to read the explanation. Results are stored in this browser; they are not a judged code submission or an official credential.'),updated_at=stamp,sort_order=130+len(banks))
 e['data'].update(questions=qs,duration_minutes=15,content_format='html');entries.append(e);lookup[path]=e;banks.append(path)
bank('java-25','Java 25 contract quiz',[
('Is ScopedValue final in the Java 25 baseline used here?','Yes','No, it requires preview flags','Only inside a record','The checked Java 25 API does not need preview flags.'),
('What follows an exceptional exit from a nested scoped binding?','The previous binding is restored','The nested value remains globally bound','The key is permanently removed','Binding lifetime ends with the nested operation, including failure.'),
('Does binding a mutable object freeze it?','No','Yes','Only for virtual threads','Binding and object ownership are separate contracts.'),
('Does a raw newly created thread automatically receive a scoped binding?','No','Yes','Only if it is virtual','Structured sharing has separate rules; a raw child thread is not that operation.'),
('What can the last windowFixed batch contain?','Fewer values than the configured window size','Only a full batch','Always a null value','A nonempty trailing partial batch is valid output.'),
('Does an unmodifiable gathered window deep-copy its element objects?','No','Yes','Only after toList','The membership list and its referenced elements have separate ownership.'),
('What does an ordered scan preserve in its outputs?','The running accumulation after each input','Only one final total','A sorted version of the inputs','Scan emits accumulated states rather than just a final aggregate.'),
('Does a module import replace requires in a named module descriptor?','No','Yes','Only for java.base','Source name imports and module dependency declarations are different boundaries.'),
('Can an early constructor prologue assume the whole object is initialized?','No','Yes','Only when the class is public','Early-construction restrictions still govern the prologue.'),
('What determines the implicit class name for ShipmentSummary.java?','The source file name','The first field name','The first printed string','The compact file is compiled under its file-derived class name.'),
('Does an instance main eliminate field initialization?','No','Yes','Only when no arguments are used','The instance is initialized before the eligible instance main is invoked.'),
('Does removing older monitor pinning remove monitor contention?','No','Yes','Only for a fair lock','Mutual exclusion still serializes holders of the same monitor.')])
bank('java-graphs','Java graph boundary quiz',[
('Does one-way reachability prove strong-component membership?','No','Yes','Only for positive weights','Strong membership requires mutual reachability.'),
('Which order does the second strong-component pass use here?','Reverse finishing order','Increasing vertex number','Breadth-first discovery order','The first pass’s finishing order is part of this two-pass method.'),
('Are numeric component labels stable business identifiers?','No','Yes','Only for a connected graph','Adjacency order can change labels without changing the partition.'),
('Which Floyd–Warshall loop belongs outside the endpoint loops?','The intermediate vertex loop','The source vertex loop','The destination vertex loop','The recurrence expands the permitted intermediate set stage by stage.'),
('What does a negative diagonal indicate after closure?','A negative cycle','An unreachable vertex','A zero-weight direct edge','A path from a vertex back to itself has negative total cost.'),
('Should an absent-edge sentinel be added to a finite weight?','No','Yes','Only if it is Long.MAX_VALUE','Absence is a state marker, not a path cost.'),
('Does a negative edge always imply a negative cycle?','No','Yes','Only in a directed graph','A negative edge can appear on finite paths without a return cycle.'),
('Does undirected union-find directly solve strong components?','No','Yes','Only for adjacency lists','Ignoring edge direction loses the mutual directed-reachability rule.'),
('Does a reachability matrix encode minimum travel cost?','No','Yes','Only after closure','Boolean reachability and weighted distance are different outputs.'),
('What does diagonal self-reachability include in the exercise?','The zero-length path','Only a nonempty cycle','Only a direct self-edge','A vertex reaches itself without using an edge.'),
('What is the all-pairs matrix storage cost?','O(V²)','O(V)','O(E log V)','One distance is stored for every ordered vertex pair.'),
('What should an invalid graph endpoint cause before returning results?','Rejection','A default zero distance','Silent removal of every affected vertex','The endpoint contract should fail before a partial result is published.')])
bank('java-dp','Java DP and index quiz',[
('What does a longest common subsequence preserve?','Order without requiring adjacency','Only adjacency','A sorted set of values','Subsequence order differs from a contiguous substring.'),
('Does the LIS tails array necessarily reconstruct one chosen solution?','No','Yes','Only for duplicate values','Its entries track best tails for lengths and can come from different solutions.'),
('Do equal values extend the strictly increasing LIS length?','No','Yes','Only if they are positive','The lower-bound replacement rule keeps strict increase.'),
('Which capacity direction preserves single-use items in one-row 0/1 knapsack?','Descending','Ascending','Either direction','Descending updates avoid reusing the current item’s new state.'),
('Why is O(nC) knapsack pseudo-polynomial?','C is a numeric capacity rather than its encoded bit count','It uses recursion','Its answer is approximate','Input encoding length and numeric state range are different measures.'),
('Does a length-only LCS result identify the selected matching positions?','No','Yes','Only for ASCII text','Reconstruction requires additional state or another strategy.'),
('What must be retained before overwriting an LCS row entry?','Its previous-row value for the next diagonal','Only the current character','The array’s capacity','The recurrence still needs the prior diagonal after in-place updates.'),
('Does UTF-16 edit distance always equal displayed-character edit distance?','No','Yes','Only for Java 25','Segmentation changes the sequence units used by the recurrence.'),
('What does Fenwick add(index,delta) do?','Adds a difference','Sets an absolute value','Sorts the prefix','An assignment needs the previous value and its difference.'),
('What is the exposed prefix endpoint in the fixture?','Exclusive','Inclusive','Always the final position','The zero-based API returns the total over positions before end.'),
('Why validate Fenwick magnitude before mutation?','To preserve every partial sum after rejection','To sort updates','To force all deltas positive','Discovering failure after changing some nodes can corrupt the representation.'),
('What makes an exhaustive oracle practical here?','A strict small-input limit','A claim that exponential work is constant','Removing rejected inputs','Subset enumeration grows exponentially and needs a bounded candidate count.')])

def module(hub,title,summary,paths):
 h=lookup['java/'+hub];h['data']['modules'].append({'title':title,'summary':summary,'lessons':[p if p.startswith(('java/','quizzes/')) else 'java/'+p for p in paths]});h['updated_at']=stamp
module('java','Text and access boundaries','Keep display units, identifier rules and package ownership separate.',['access-packages','grapheme-boundaries','collation-policy','identifier-policy'])
module('advanced-java','Java 25 without preview flags','Use checked language and library contracts at their declared release.',['scoped-values','stream-gatherers','flexible-constructors','module-imports','compact-source','virtual-thread-monitors'])
module('advanced-java','Application coordination and evidence','Verify multi-structure ownership, retained state and operation outcomes.',['multi-index-invariants','heap-dump-workflow','jfr-incident-workflow'])
module('advanced-java','Database admission and versioned changes','Check session visibility, pool saturation and migration history.',['database-isolation','connection-pool','versioned-migrations'])
module('dsa-in-java','Deletion and range indexes','Keep surviving structures valid after changes.',['avl-deletion','trie-deletion','fenwick-tree'])
module('dsa-in-java','All-pairs and directed partitions','Distinguish weighted distances from mutual reachability.',['floyd-warshall','strong-components'])
module('dsa-in-java','Sequence and single-use recurrences','State the text unit, order and capacity direction.',['edit-distance','longest-subsequence','increasing-subsequence','zero-one-knapsack'])
module('java-projects','Failures, identities and concurrent publication','Run controlled local failures before treating success as sufficient evidence.',['http-failure-project','tls-local-project','concurrent-import-project'])
module('java-exercises','Independent graph and DP references','Check algorithms against a different small-input approach.',['graph-exercises','dp-exercises'])
module('java-interview-questions','Race interleaving review','Prove the read/write ordering and the corrected atomic boundary.',['transaction-races-interview'])
module('java-quizzes','New release, graph and DP checks','Review version and recurrence contracts with explained answers.',['quizzes/java-25','quizzes/java-graphs','quizzes/java-dp'])
module('java-examples','Local identity and retained-state fixtures','Open the canonical lessons and download their exact source.',['tls-local-project','heap-dump-workflow','compact-source'])
module('java-cheatsheet','Current release and state-boundary reading','Use the canonical version-labelled lessons as connected references.',['scoped-values','stream-gatherers','fenwick-tree'])
# Keep the older release-specific warning scoped rather than erasing its Java 21 behavior.
for path,text,related in [
 ('java/virtual-threads','The synchronized-block carrier-pinning warning in this lesson belongs to the Java 21 baseline. JDK 24 changed monitor-related pinning. The Java 25 companion lesson checks the newer boundary without claiming that lock contention disappears.','virtual-thread-monitors'),
 ('java/trie','Deletion must preserve terminal markers and shared prefixes belonging to surviving words. The deletion companion uses a bounded iterative path and checks rejection before mutation.','trie-deletion'),
 ('java/avl-tree','Deletion can reduce several ancestor heights and needs its own rotation selection, including a heavy child with zero balance. The deletion companion checks the complete surviving path.','avl-deletion')]:
 e=lookup[path];e['body']+='<h2>Continue the contract</h2>'+para(text)+'<p><a href="/java/'+related+'">Open the companion lesson</a>.</p>';e['updated_at']=stamp;expanded.append(path)
allpaths=set(lookup)
for e in entries:
 if e['path'].startswith('java/'):
  for href in re.findall(r'href="([^"]+)"',e['body']):assert href.lstrip('/').split('#')[0] in allpaths,(e['path'],href)
for h in [e for e in entries if e['type']=='subject' and e['path'].startswith('java/')]:
 paths=[p for m in h['data']['modules'] for p in m['lessons']];assert len(paths)<=100 and len(paths)==len(set(paths)),h['path']
 for p in paths:assert p in lookup,(h['path'],p)
for path in banks:
 qs=lookup[path]['data']['questions'];assert len(qs)==12 and len({q['prompt'] for q in qs})==12
(ROOT/'src/data/fixtures.json').write_text(json.dumps(entries,indent=2,ensure_ascii=False)+'\n')
report={'added':added,'expanded':expanded,'newQuizzes':banks,'newProseWords':sum(len(re.sub('<[^>]*>',' ',re.sub(r'<pre>[\s\S]*?</pre>','',lookup[p]['body'])).split()) for p in added),'newWordsIncludingCode':sum(len(re.sub('<[^>]*>',' ',lookup[p]['body']).split()) for p in added),'articles':sum(e['type']=='article' and e['path'].startswith('java/') for e in entries),'hubs':10,'quizzes':sum(e['type']=='quiz' and e.get('subject')=='java-quizzes' for e in entries),'quizQuestions':sum(len(e['data']['questions']) for e in entries if e['type']=='quiz' and e.get('subject')=='java-quizzes'),'localOnly':True}
(OUT/'java-depth-batch.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if not isinstance(v,list)}))
