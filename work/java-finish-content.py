"""Original remaining Java content. Only mutates the isolated local fixtures."""
import copy, html, json, pathlib, re, uuid
ROOT=pathlib.Path(__file__).resolve().parents[1]; OUT=ROOT.parent.parent/'outputs'
baseline=ROOT/'work/java-finish/baseline.json'
if not baseline.exists(): baseline.write_text((ROOT/'src/data/fixtures.json').read_text())
entries=json.loads(baseline.read_text()); lookup={e['path']:e for e in entries}
added=[]; expanded=[]; banks=[]; updated_banks=[]
sections={e['subject']:e['path'] for e in entries if e['type']=='subject' and e['path'].startswith('java/')}
base=copy.deepcopy(lookup['java/arrays'])
def prose(s): return re.sub(r'<(?!/?(?:strong|a)(?:\s|>))[^>]*>',lambda m:html.escape(m[0]),s)
def p(s): return '<p>'+prose(s)+'</p>'
def block(s,lang='java'): return '<pre><code class="language-'+lang+'">'+html.escape(s.strip(),quote=False)+'</code></pre>'
def put(slug,title,definition,parts,program,output,cost,mistakes,related,subject='java-advanced',release=8,dependency=None):
 path='java/'+slug; is_new=path not in lookup
 body=p(definition)+p('<strong>Java '+str(release)+'+.</strong> '+({'h2':'This program requires the H2 JDBC driver; the downloadable Maven project declares it.','junit':'These tests require JUnit Jupiter 5.11.0; the downloadable Maven project declares it.','jmh':'This benchmark requires JMH 1.37 and its annotation processor; the downloadable Maven project declares them.'}.get(dependency,'This is a complete program using JDK classes.')))
 for heading,texts in parts: body+='<h2>'+html.escape(heading)+'</h2>'+''.join(p(t) for t in texts)
 body+='<h2>Working program</h2>'+block(program)+'<h3>Output</h3>'+block(output,'text')
 body+='<h2>Costs and boundaries</h2>'+''.join(p(t) for t in cost)
 body+='<h3>Common Mistakes</h3><ul>'+''.join('<li>'+prose(t)+'</li>' for t in mistakes)+'</ul>'
 body+='<h2>Read next</h2><p>'+', '.join('<a href="/java/'+s+'">'+t+'</a>' for s,t in related)+'.</p>'
 e=copy.deepcopy(lookup.get(path,base));e.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),path=path,title=title,summary=definition,body=body,subject=subject,tags=['java',slug],difficulty='Intermediate',featured=False,sort_order=80+len(added),updated_at='2026-09-29T07:00:00+00:00',status='published')
 e['data']={'subject_root':'java/java','section_path':sections[subject],'content_format':'html','kind':'tutorial','java_release':release,'java_version':str(release)+'+','reading_minutes':max(4,round(len(re.sub('<[^>]+>',' ',body).split())/150)),'author_path':'authors/aitrove-editorial','related':[{'path':'java/'+s,'title':t} for s,t in related]}
 if dependency: e['data']['java_dependency']=dependency
 if is_new: entries.append(e);added.append(path)
 else: lookup[path].update(e); expanded.append(path)
 lookup[path]=e if is_new else lookup[path]

put('casts','Java casts and numeric conversion: discarded bits and checked references',
'A cast requests a conversion in a specific context; narrowing a number can discard information, while narrowing a reference can fail at runtime.',
[('Make the loss explicit',[
'A warehouse device reports quantities in a long because it accumulates readings for months. The receiving API accepts int. A direct cast does not validate that the reading fits; it keeps the low-order bits. Math.toIntExact provides the rejecting boundary required for a quantity, rather than quietly turning a large positive reading into a negative one.',
'Promotion happens before assignment. Adding two int readings uses int arithmetic even when the result is assigned to long. Convert an operand before the addition or use an exact arithmetic method. The destination type cannot repair an overflow that has already occurred.',
'Reference casts have a separate purpose. They do not create another object or convert its fields. The runtime checks whether the referenced object is compatible with the target type. Use instanceof when the permitted branch is conditional; null passes a reference cast but still fails when subsequently dereferenced.'
]),('Use casts at boundaries',[
'The program puts both failures next to their inputs. Its narrowed byte result is deliberate bit manipulation, not a business quantity. A serialization layer can need that operation; an inventory counter normally needs rejection. Naming the requirement matters more than making the compiler accept the line.'
])],r'''public class QuantityConversions {
    public static void main(String[] args) {
        long accumulated = 3_000_000_000L;
        try { Math.toIntExact(accumulated); }
        catch (ArithmeticException rejected) { System.out.println("Quantity rejected"); }
        System.out.println((byte) 260);
        int measured = Integer.MAX_VALUE;
        System.out.println((long) measured + 1);
        Object receipt = "RC-81";
        System.out.println(((String) receipt).length());
        try { Integer unused = (Integer) receipt; }
        catch (ClassCastException rejected) { System.out.println("Wrong reference type"); }
    }
}''','Quantity rejected\n4\n2147483648\n5\nWrong reference type',
['These scalar conversions require constant work and no traversal. The surrounding parser may still allocate strings or scan digits; that is a different cost. Floating-point to integer conversion has its own rules, including truncation and special values, so do not transfer the long-to-int rule to every cast.'],
['Casting after integer addition is too late to prevent that addition overflowing.','A successful cast does not make a mutable object safe to share.','Do not catch ClassCastException as ordinary collection filtering; use a typed interface.'],[('operators','Numeric operators'),('boxing','Boxing boundaries')],subject='java')

put('text-normalization','Java text normalization: equal labels and explicit comparison policy',
'Unicode normalization maps canonically equivalent character sequences to a selected normal form; it does not define a complete user-name or security policy.',
[('Separate stored text from comparison keys',[
'A customer name can arrive as a precomposed accented character or as a base character followed by a combining mark. String.equals compares their UTF-16 sequences. NFC normalization gives the application a common representation for this particular equivalence before it uses a value as a map key.',
'Keep the display value. Collapsing all case, punctuation, or accents can destroy distinctions a person expects to see. Canonical normalization is different from removing accents, and compatibility forms such as NFKC can fold extra character distinctions. Choose the form for the field, document it, and apply it on every write and lookup.',
'The program uses codePointCount only to report code points. That count is not the number of displayed characters in every script. Emoji sequences and combining marks can make one displayed unit contain several code points. A UI truncation rule needs a segmentation policy rather than a substring index guessed from the count.'
]),('Do not hide locale decisions',[
'A normalized spelling can still differ in case. Locale-sensitive sorting belongs to a separate comparison operation. Identifiers in a machine protocol usually need a restricted alphabet and a fixed comparison rule; a human directory may instead require language-specific collation. Neither follows automatically from using UTF-8.'
])],r'''import java.text.Normalizer;
public class CustomerLabelNormalization {
    public static void main(String[] args) {
        String composed = "Caf\u00e9";
        String decomposed = "Cafe\u0301";
        System.out.println(composed.equals(decomposed));
        String normalized = Normalizer.normalize(decomposed, Normalizer.Form.NFC);
        System.out.println(composed.equals(normalized));
        System.out.println(decomposed.codePointCount(0, decomposed.length()));
        System.out.println(normalized.codePointCount(0, normalized.length()));
    }
}''','false\ntrue\n5\n4',
['Normalization must inspect the input and creates an output representation. Bound accepted input size and account for allocation in bulk imports. This example verifies one canonical equivalence; it is not a comprehensive grapheme segmenter or a confusable-character detector.'],
['Do not describe code points as bytes or displayed characters.','Apply the same key policy at insertion and lookup.','Normalization does not sanitize a name for HTML, SQL or a file path.'],[('unicode-encoding','UTF-16 and UTF-8'),('strings','String comparison')],subject='java')

put('regular-expressions','Java regular expressions: full matches, searches and capture boundaries',
'Pattern compiles a regular expression, while Matcher holds the mutable state of a match attempt against one input.',
[('Define the accepted record',[
'A parcel identifier in this application has two ASCII capital letters, a hyphen, and four digits. matches() asks whether the whole input has that form. find() asks a different question: whether some region matches. Using a successful search as full validation lets surrounding junk cross the boundary.',
'The compiled Pattern can be reused. A Matcher should belong to one operation rather than a shared service field, because its cursor, region and captured groups change. Query a group only after a successful matching operation; a failed match does not supply a previous success as a safe fallback.',
'The alphabet is intentional. The program uses [0-9] because the wire format names ASCII digits, and it keeps the original spelling. More permissive Unicode or case-insensitive options need tests for the chosen format. A short identifier rule should not silently become a general international-text validator.'
]),('Keep worst-case inputs in the review',[
'Not every expression has the same runtime behavior. Nested ambiguous repetition can force extensive backtracking. Bound the input, prefer an unambiguous grammar for machine records, and test rejected long strings. Precompiling reduces repeated compilation; it does not repair the complexity of the chosen expression.'
])],r'''import java.util.regex.Pattern;
import java.util.regex.Matcher;
public class ParcelIdentifierPattern {
    private static final Pattern ID = Pattern.compile("([A-Z]{2})-([0-9]{4})");
    public static void main(String[] args) {
        Matcher exact = ID.matcher("DL-0042");
        if (exact.matches()) System.out.println(exact.group(1) + ":" + exact.group(2));
        System.out.println(ID.matcher("prefix DL-0042 suffix").matches());
        Matcher search = ID.matcher("prefix DL-0042 suffix");
        System.out.println(search.find());
    }
}''','DL:0042\nfalse\ntrue',
['This fixed-length rule has bounded work for the accepted record and rejects overlong whole inputs. Do not infer a linear-time guarantee for arbitrary Java regular expressions from this example. Pattern storage is reusable; each Matcher adds per-operation state.'],
['A successful find is not full-input validation.','A shared Matcher introduces mutable state between requests.','Escaping has two layers when a regex is written in a Java string.'],[('strings','String operations'),('exceptions','Validation failures')],subject='java')

put('copy-on-write','Java CopyOnWriteArrayList: listener snapshots and write amplification',
'CopyOnWriteArrayList replaces its backing array for updates and gives an iterator the array state present when that iterator was created.',
[('Choose a stable audience',[
'A notification dispatcher needs to visit the subscribers that existed when delivery began. A later registration should affect the next delivery, not interrupt the current traversal. Snapshot iteration fits that rule without locking the dispatch loop across every callback.',
'The snapshot freezes the sequence of references. It does not freeze the subscriber objects. If a subscriber changes its own fields, the iterator still holds that same object. Keep registration changes and listener-state coordination as separate responsibilities.',
'The write tradeoff is visible even without a timer: an update copies array storage instead of changing one slot in place. This is a plausible choice for a small listener list with rare changes, and an expensive choice for a large queue that receives a write per message.'
]),('Review the iterator contract',[
'The old cursor in the program prints the first audience; a fresh list rendering prints the changed audience. Its remove method is rejected. An algorithm designed around Iterator.remove must therefore choose another collection or collect a separate set of removals and apply them through the list after traversal.'
])],r'''import java.util.Arrays;
import java.util.Iterator;
import java.util.concurrent.CopyOnWriteArrayList;
public class SubscriberSnapshot {
    public static void main(String[] args) {
        CopyOnWriteArrayList<String> listeners = new CopyOnWriteArrayList<>(Arrays.asList("email", "audit"));
        Iterator<String> before = listeners.iterator();
        listeners.add("metrics");
        while (before.hasNext()) System.out.println(before.next());
        System.out.println(listeners);
        try { before.remove(); }
        catch (UnsupportedOperationException rejected) { System.out.println("Snapshot cannot remove"); }
    }
}''','email\naudit\n[email, audit, metrics]\nSnapshot cannot remove',
['Traversal of n listeners is O(n). Ordinary element-changing updates can copy O(n) array entries. Existing iterators can retain older arrays, so several long-lived snapshots can increase retained storage. Subscriber objects may be shared between arrays; a list copy is not a deep object copy.'],
['Do not use this as a default high-write work queue.','A snapshot can include a listener removed after its creation.','Thread-safe list operations do not make callbacks thread-safe.'],[('iterators','Iterator contracts'),('collection-views','Copies and views')],subject='java-collections')

put('concurrent-sorted-map','Java ConcurrentSkipListMap: ordered concurrent lookups and live ranges',
'ConcurrentSkipListMap maintains sorted keys while allowing concurrent access; its traversal is weakly consistent rather than a single frozen snapshot.',
[('Order is a requirement, not a bonus',[
'A dispatch board needs the next due job and a range of jobs before a cutoff. A plain concurrent hash map supplies independent keyed operations but does not supply sorted nearest-key queries. This board needs an ordered map contract.',
'A subMap is a range view backed by the original map. Removing a job through the view removes that mapping from the board. Keep a copied snapshot when a report must stay unchanged after it is handed to another component; a live range means later updates can be visible.',
'Individual concurrent operations still do not make a multi-step decision atomic. Checking a value and then removing a key can remove a newer replacement. Use a conditional remove(key, expectedValue) for that claim, and decide how the caller handles a failed claim.'
]),('Settle identity and comparison',[
'Comparator equivalence decides whether two sorted keys occupy the same position. Include the necessary tie-breaker if two jobs with the same due time must remain distinct. Null keys and values are not accepted here, so absence cannot be represented by inserting a null mapping.'
])],r'''import java.util.concurrent.ConcurrentSkipListMap;
import java.util.concurrent.ConcurrentNavigableMap;
public class DueJobBoard {
    public static void main(String[] args) {
        ConcurrentSkipListMap<Integer, String> jobs = new ConcurrentSkipListMap<>();
        jobs.put(30, "dispatch-30"); jobs.put(10, "dispatch-10"); jobs.put(20, "dispatch-20");
        System.out.println(jobs.ceilingKey(15));
        ConcurrentNavigableMap<Integer, String> early = jobs.headMap(25, false);
        System.out.println(early.keySet());
        System.out.println(jobs.remove(20, "dispatch-20"));
        System.out.println(early.keySet());
    }
}''','20\n[10, 20]\ntrue\n[10]',
['Search, insertion and removal have expected O(log n) cost. A traversal costs work proportional to the visited mappings and is not a transactional snapshot. Copying a report adds O(k) entries for a range of k keys and still shares mutable values unless copied separately.'],
['Do not treat a weakly consistent traversal as an atomic report.','A backed range is not independent storage.','A key-only removal can discard a replacement inserted by another worker.'],[('treemap','Sorted map decisions'),('concurrent-map','Concurrent hash operations')],subject='java-collections')

put('weak-references','Java weak references: reachability is not a cache eviction schedule',
'WeakReference holds a referent without keeping it strongly reachable solely through that reference.',
[('Keep lifetime separate from lookup',[
'A metadata index can need to observe an object without deciding how long it lives. A weak reference supplies that relationship. It does not promise that an object survives until the next access, and it does not supply a memory budget or a predictable eviction time.',
'Read get() once into a local variable, check that result, then use the local value. Repeating get() after a successful check creates a second observation rather than holding the first result. A local strong reference keeps the selected object available during that operation.',
'The example clears its reference explicitly. That makes the result deterministic and tests the absent branch; it is not evidence that a garbage collector runs on demand. System.gc is a request and must not be part of the business condition that makes a cache correct.'
]),('Avoid a strong route back',[
'A weak-key map can still retain a key if its strongly held value points back to that key. Draw the actual object references before assuming a weak-key structure resolves retention. ReferenceQueue is useful when cleanup needs notification, but the consumer still needs its own removal policy and resource ownership.'
])],r'''import java.lang.ref.WeakReference;
public class OptionalMetadataReference {
    public static void main(String[] args) {
        String record = new String("parcel-42");
        WeakReference<String> index = new WeakReference<>(record);
        String selected = index.get();
        System.out.println(selected != null ? selected : "absent");
        index.clear();
        System.out.println(index.get() == null);
        System.out.println(record);
    }
}''','parcel-42\ntrue\nparcel-42',
['Creating or checking one weak reference is constant-sized application work. Collector processing and reference-queue cleanup depend on the runtime and reachable object graph, so this example does not assign a fixed eviction latency. Required cached data needs a deterministic reload path and explicit capacity limits.'],
['Never require a collection to occur before the application can proceed.','Weak references do not close files or connections for you.','A strong value-to-key reference can defeat the intended weak-key lifetime.'],[('jvm-memory','Reachability and ownership'),('gc-diagnostics','Heap observations')],subject='java-collections')

put('immutable-collections','Java collection factories: rejected updates and shallow element ownership',
'List.of and List.copyOf create lists that reject structural updates; they do not recursively freeze the objects stored inside the list.',
[('Snapshot the right layer',[
'A receipt export should not gain another row when its source list changes. List.copyOf supplies a membership snapshot for that boundary. It can reuse an already suitable unmodifiable list, so code should depend on its contract rather than whether a different wrapper object was allocated.',
'The copied membership can still contain mutable row objects. Changing a field on one of those rows changes what both references see. Either publish immutable row values, copy each row, or document shared ownership. The outer list alone cannot make that choice.',
'These factories reject null entries. A nullable input from an older API therefore needs an explicit rejection or conversion step. Arrays.asList has a different contract: fixed size, but element replacement through set is allowed and is backed by the original array.'
]),('Version the boundary',[
'List.of is available from Java 9, while List.copyOf is available from Java 10. This program targets Java 11 so both calls belong to the stated toolchain. A Java 8 project can use a copied ArrayList plus Collections.unmodifiableList, with the same shallow-copy warning.'
])],r'''import java.util.ArrayList;
import java.util.List;
public class ReceiptMembershipSnapshot {
    public static void main(String[] args) {
        List<StringBuilder> drafts = new ArrayList<>();
        drafts.add(new StringBuilder("pending"));
        List<StringBuilder> exported = List.copyOf(drafts);
        drafts.add(new StringBuilder("received"));
        drafts.get(0).append(":reviewed");
        System.out.println(exported.size());
        System.out.println(exported.get(0));
        try { exported.add(new StringBuilder("late")); }
        catch (UnsupportedOperationException rejected) { System.out.println("Membership fixed"); }
        try { List.of("ready", null); }
        catch (NullPointerException rejected) { System.out.println("Null rejected"); }
    }
}''','1\npending:reviewed\nMembership fixed\nNull rejected',
['Copying a mutable input of n members takes O(n) reference work and O(n) membership storage. Element content is not copied by this operation. Do not assume a new allocation for every copyOf invocation; do assume the documented update restrictions.'],
['Unmodifiable membership is not deep immutability.','Do not treat Arrays.asList as the same API.','Null rejection must be tested before publishing imported rows.'],[('collection-views','Backed views'),('records','Value records')],subject='java-collections',release=11)

put('sequenced-collections','Java 21 sequenced collections: endpoints and reversed views',
'SequencedCollection gives an encounter-ordered collection endpoint operations and a reversed view without requiring indexed access.',
[('Name the encounter order',[
'A route trace needs a first stage and a last stage. Prior to the sequenced interfaces, that requirement was expressed differently for lists and ordered sets. The interface now names those operations for collections that have a defined encounter order.',
'Reversed means a view with the opposite order, not a detached copy. Updating a mutable original can affect the view. Make a separate copy when handing out a snapshot, and check whether the underlying collection permits an endpoint update before assuming every implementation behaves like ArrayList.',
'Order can come from insertion, access, or sorting. A sorted set may not permit an arbitrary addFirst because that would conflict with its ordering rule. Choose the implementation by the order your application needs; the shared interface does not erase implementation restrictions.'
]),('Keep the toolchain honest',[
'The example compiles for Java 21. Changing only a project label does not add these methods to Java 8 or 17. Library consumers also need a runtime that supports the compiled API usage, so version labels belong next to the program and in the build configuration.'
])],r'''import java.util.ArrayList;
import java.util.List;
import java.util.SequencedCollection;
public class ReversedRouteView {
    public static void main(String[] args) {
        SequencedCollection<String> stages = new ArrayList<>(List.of("received", "packed"));
        SequencedCollection<String> reverse = stages.reversed();
        System.out.println(stages.getFirst());
        System.out.println(reverse);
        stages.addLast("dispatched");
        System.out.println(reverse);
        System.out.println(reverse.getFirst());
    }
}''','received\n[packed, received]\n[dispatched, packed, received]\ndispatched',
['This ArrayList-backed view does not duplicate every element to reverse its traversal. Full traversal remains O(n), and endpoint insertion costs follow the underlying collection. For example, inserting at the front of an array-backed list can shift O(n) references.'],
['A reversed view is not a snapshot.','The interface does not promise that every endpoint update is supported.','Do not put Java 21 calls in a Java 8-labelled sample.'],[('collection-views','Shared view ownership'),('ordered-sets','Encounter-order choices')],subject='java-collections',release=21)

put('comparator-contracts','Java comparators: tie-breakers, overflow and sorted-key identity',
'A Comparator defines an ordering relation; sorted collections use a zero comparison to decide that two keys occupy one ordering position.',
[('Preserve distinct jobs',[
'A dispatch comparator that compares only priority merges two distinct jobs at the same priority when used in a TreeSet. Sorting a list preserves both values, but the sorted set interprets equality under the comparator as one membership slot. The same comparator can therefore have different consequences depending on its consumer.',
'Use a stable identifier as a tie-breaker when both jobs must remain. The identifier must itself have a total order and a defined duplicate policy. A changing priority field makes a mutable key dangerous after insertion; a sorted structure does not continuously rebuild its internal path when a field changes.',
'Do not compare integer priorities by subtraction. Extreme inputs can overflow and reverse the intended sign. Comparator.comparingInt, Integer.compare and explicit thenComparing steps state the policy without relying on a difference fitting in int.'
]),('Test the relation',[
'Check equal values, reverse pairs and triples when reviewing a custom comparator. Inconsistent or non-transitive results can invalidate sorted algorithms. The program deliberately compares the broken policy with an identifier-aware policy so the lost member is visible without a timing measurement.'
])],r'''import java.util.Comparator;
import java.util.TreeSet;
public class DispatchJobOrdering {
    static final class Job {
        final String id; final int priority;
        Job(String id, int priority) { this.id=id; this.priority=priority; }
    }
    public static void main(String[] args) {
        Comparator<Job> priorityOnly = Comparator.comparingInt(job -> job.priority);
        TreeSet<Job> merged = new TreeSet<>(priorityOnly);
        merged.add(new Job("D-11", 3)); merged.add(new Job("D-12", 3));
        TreeSet<Job> distinct = new TreeSet<>(priorityOnly.thenComparing(job -> job.id));
        distinct.addAll(merged); distinct.add(new Job("D-12", 3));
        System.out.println(merged.size());
        System.out.println(distinct.size());
        System.out.println(Integer.compare(Integer.MIN_VALUE, Integer.MAX_VALUE));
    }
}''','1\n2\n-1',
['Each TreeSet insertion uses O(log n) comparisons. The comparator may add string comparison work proportional to a differing prefix; O(log n) does not mean character work disappears. Membership storage is O(n).'],
['A priority tie is not necessarily object equality.','Changing a comparison field after insertion can corrupt lookup assumptions.','Subtracting two int values can overflow.'],[('ordered-sets','Set equivalence'),('sorting','Comparator sorting')],subject='java-collections')

put('class-loaders','Java class loaders: type identity, delegation and initialization',
'A Java type is identified by its binary name and defining class loader; loading a class and initializing it are separate runtime steps.',
[('Locate a type before creating an instance',[
'A plugin loader can discover a class name before deciding to run its initialization code. Class.forName with initialize=false supports that inspection step. Initializing the class later can execute static initializers, including code that allocates resources or fails.',
'The program prints when its nested configuration class initializes. Looking it up without initialization produces no configuration message; the second request triggers that work once. Keep this difference in mind when scanning classes in a build tool or application startup routine.',
'A matching binary name alone does not make types from separate defining loaders interchangeable. A plugin should share a service interface through a common parent loader. Otherwise casting a plugin instance to the host interface can fail even when both interfaces have the same printed name.'
]),('Do not retain a loader accidentally',[
'Parent delegation is a common loading strategy, not an excuse to assume every custom loader makes the same choices. A loader can also remain reachable through static registries, a thread context loader or long-lived callbacks. Unloading depends on reachability; closing a URLClassLoader closes its resources without forcing the VM to unload all of its types.'
])],r'''public class ConfigurationClassLoading {
    static class Configuration {
        static { System.out.println("Configuration initialized"); }
    }
    public static void main(String[] args) throws Exception {
        ClassLoader loader = ConfigurationClassLoading.class.getClassLoader();
        String name = "ConfigurationClassLoading$Configuration";
        Class<?> inspected = Class.forName(name, false, loader);
        System.out.println("Inspected without initialization");
        Class<?> initialized = Class.forName(name, true, loader);
        System.out.println(inspected == initialized);
        System.out.println(String.class.getClassLoader() == null);
    }
}''','Inspected without initialization\nConfiguration initialized\ntrue\ntrue',
['Repeated lookup costs depend on loader work and whether the class has already been defined. Initialization can execute arbitrary application code, so it has no universal constant-time budget. Keep scanning separate from resource acquisition and record initializer failures at the startup boundary.'],
['The same class name can identify different runtime types.','Loading without initialization does not guarantee that every subsequent reflective action avoids initialization.','Closing a loader does not force class unloading.'],[('class-initialization','Initialization triggers'),('reflection','Reflective access')])

put('java-modules','Java modules: readability, exports and reflection boundaries',
'A named Java module groups packages under a module descriptor and states which other modules it reads and which packages it exports or opens.',
[('Express the public boundary',[
'A shipping library can export its public quote package while keeping implementation packages internal. requires declares a module dependency. exports permits ordinary use of the named package; opens permits deep reflection under its specified scope. These are different access decisions.',
'The inspection program runs on the class path. Its own module is unnamed, while String belongs to the named java.base module. This explains the output without claiming that the program is already a packaged named-module application.',
'A named-module build needs a module-info.java descriptor and a module path. A complete descriptor for a small quote library might export in.aitrove.quote.api while requiring java.net.http. Keep all packages in named modules named; a default-package class belongs to a different sample structure.'
]),('Migrate deliberately',[
'Automatic modules can help a dependency participate before it has a descriptor, but their names and broad exposure still need review. Split packages, missing read edges and reflective access failures can appear after moving dependencies off the class path. Check the packaged build rather than assuming IDE completion proves the runtime module graph.'
])],r'''public class ModuleBoundaryInspection {
    public static void main(String[] args) {
        Module platform = String.class.getModule();
        Module application = ModuleBoundaryInspection.class.getModule();
        System.out.println(platform.getName());
        System.out.println(application.isNamed());
        System.out.println(platform.isExported("java.lang"));
        System.out.println(application.canRead(platform));
    }
}''','java.base\nfalse\ntrue\ntrue',
['This inspection performs a handful of metadata queries. Module resolution is a startup concern and depends on the module graph; it is not the cost of every business-method call. The example verifies the class-path boundary. A separately packaged modular application needs its own descriptor and launch tests.'],
['exports is not the same as opens.','A class-path sample does not become a named module because it uses Module APIs.','A compiler release setting does not automatically choose a module path.'],[('packages','Package ownership'),('access-control','Member access')],release=11)

put('conditions','Java conditions: protected predicates and timed waiting',
'A Condition lets a thread release its associated lock while waiting for a protected predicate to become true, then reacquire that lock before continuing.',
[('Wait for state, not a message',[
'A receiving desk waits for an inventory count greater than zero. A signal says that a state change may have occurred; it does not hand the waiting thread a reserved item. Another consumer can take that item before the awakened thread reacquires the lock.',
'Check the predicate in a while loop. The loop handles both competing consumers and spurious wakeups. The code decrements its count only while holding the same lock used by the producer. Updating the count outside that lock would separate the signal from the state that the waiting code actually observes.',
'The method accepts a remaining nanosecond budget. awaitNanos reports what remains so repeated wakeups do not restart the full wait. Lock acquisition uses lockInterruptibly, making interruption an explicit way to leave both the admission and waiting phases.'
]),('Keep cleanup outside the success assumption',[
'The finally block releases the lock after success, timeout or a waiting exception. A timed-out consumer returns false without inventing an item. Production shutdown needs another protected predicate, such as closed, and a signalAll so all waiting callers can recheck that state.'
])],r'''import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.ReentrantLock;
public class ReceivingDeskCondition {
    final ReentrantLock lock = new ReentrantLock();
    final Condition available = lock.newCondition();
    int parcels;
    void receive() {
        lock.lock();
        try { parcels++; available.signal(); }
        finally { lock.unlock(); }
    }
    boolean take(long budgetNanos) throws InterruptedException {
        lock.lockInterruptibly();
        try {
            while (parcels == 0) {
                if (budgetNanos <= 0) return false;
                budgetNanos = available.awaitNanos(budgetNanos);
            }
            parcels--; return true;
        } finally { lock.unlock(); }
    }
    public static void main(String[] args) throws Exception {
        ReceivingDeskCondition desk = new ReceivingDeskCondition();
        System.out.println(desk.take(0));
        desk.receive();
        System.out.println(desk.take(0));
        System.out.println(desk.take(0));
    }
}''','false\ntrue\nfalse',
['The protected state transition is O(1), but a waiting call can spend its budget blocked. That budget applies to condition waiting, not the earlier lock acquisition or a complete method deadline. Scheduling and lock contention are not bounded by the few arithmetic instructions. This fixture verifies timeout and state transitions without relying on thread timing; the download checks also exercise a signalled waiter.'],
['An if check cannot protect against repeated wakeups.','Use the same lock for the predicate, update and waiting operation.','Signal does not transfer ownership of an item.'],[('locks','Lock ownership'),('blocking-queues','Library queue alternatives')])

put('semaphores','Java semaphores: permit accounting and bounded access',
'A Semaphore maintains a permit count and can block or reject callers when the permitted number of simultaneous users is exhausted.',
[('Account for successful acquisition',[
'A service has two external connections available for a particular operation. A semaphore can limit admission to two callers, but it does not create or select those connections. Resource selection still needs its own protected pool data structure.',
'Release only after this caller successfully acquired a permit. A release after a failed tryAcquire adds a permit that no operation owned, expanding capacity. The example makes that branch visible: the rejected third attempt does not enter a finally block that releases anything.',
'A semaphore is not an ownership-aware mutex. Another thread can release a permit, and the object does not verify that the caller acquired it earlier. Keep ownership in the operation structure. A fair semaphore can improve admission ordering under its contract, but fairness is not a latency bound or a throughput guarantee.'
]),('Wait budgets are part of admission',[
'For request handling, use timed acquisition when callers have a deadline. A method that waits indefinitely can exhaust the server threads even though it successfully limits downstream concurrency. Interruption must also stop waiting rather than turn a cancelled request into another admitted task.'
])],r'''import java.util.concurrent.Semaphore;
public class ConnectionAdmission {
    public static void main(String[] args) {
        Semaphore permits = new Semaphore(2);
        boolean first = permits.tryAcquire();
        boolean second = permits.tryAcquire();
        System.out.println(first);
        System.out.println(second);
        System.out.println(permits.tryAcquire());
        if (first) permits.release();
        if (second) permits.release();
        System.out.println(permits.availablePermits());
    }
}''','true\ntrue\nfalse\n2',
['The object has a compact permit-accounting state, while waiting callers add scheduling and queueing work. This fixture does no external I/O and measures no downstream throughput. A caller must budget for both admission waiting and the admitted operation.'],
['Do not release after a rejected acquisition.','Permit capacity does not make a mutable connection safe to share.','A fair flag does not guarantee a task finishes by a deadline.'],[('atomics','Counter invariants'),('executors','Worker admission')])

put('scheduled-tasks','Java scheduled tasks: delay semantics and failed repetitions',
'ScheduledExecutorService submits delayed or periodic work and returns futures that expose completion, failure and cancellation.',
[('Distinguish two recurring schedules',[
'Fixed-rate scheduling uses planned start times. Fixed-delay scheduling waits for one execution to finish before counting the delay to the next. A slow task can therefore produce different behavior under the two policies even when the configured number is the same.',
'The one-shot program schedules one renewal operation, then waits for its result with a separate timeout. Scheduling a delay does not guarantee execution at an exact wall-clock instant. Busy workers, operating-system scheduling and the task itself affect actual completion.',
'An exception escaping a periodic task can suppress later executions. Store and inspect its future or define explicit failure reporting inside the task. Silently swallowing all failures turns a broken renewal into a process that appears healthy while its state stops changing.'
]),('Own the scheduler',[
'The application that creates the scheduler closes it. shutdown stops new admission; awaitTermination checks whether admitted work has finished. Long-running services also need a decision about remaining delayed tasks and shutdown deadlines instead of leaving that policy to a process exit.'
])],r'''import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
public class RenewalSchedule {
    public static void main(String[] args) throws Exception {
        ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
        try {
            ScheduledFuture<String> renewal = scheduler.schedule(() -> "renewed=R-31", 0, TimeUnit.MILLISECONDS);
            System.out.println(renewal.get(2, TimeUnit.SECONDS));
        } finally {
            scheduler.shutdownNow();
            if (!scheduler.awaitTermination(2, TimeUnit.SECONDS)) throw new IllegalStateException("Worker did not stop");
        }
    }
}''','renewed=R-31',
['A scheduled task can remain queued until its delay elapses and a worker is available. The queue and retained task inputs contribute memory proportional to admitted pending work. A scheduling API does not provide durable storage or a distributed scheduler across server instances.'],
['Delay expiration is not a completion deadline.','An uncaught periodic-task failure needs reporting.','Do not create a new scheduler for every incoming request.'],[('cancellation','Timeout and interruption'),('threads','Thread lifecycle')])

put('cancellation','Java cancellation: timed waits and cooperative interruption',
'Future.get with a timeout bounds a caller’s wait; it does not stop the task that produced the future.',
[('Separate waiting from stopping',[
'A quote request can time out while its worker continues contacting a supplier. Returning a timeout response is only the caller boundary. The application must decide whether to cancel, let the worker finish, or detach the result under a separately bounded policy.',
'cancel(true) requests interruption for a running task, but task code has to cooperate. Interruptible blocking methods can throw InterruptedException. CPU loops need their own interruption checks. A cancelled future becoming done is not proof that the worker has already released its resources.',
'The program uses a latch to confirm worker admission, then cancels a worker waiting on another latch. The worker records its exit in finally, and the main thread waits for that exit before printing the result. This makes shutdown observable rather than inferring it from isCancelled alone.'
]),('Pass one deadline through the stages',[
'If admission, database work and HTTP work each start a fresh five-second timeout, one request can spend much longer than five seconds. Track a shared deadline and pass the remaining budget at each boundary. Use a monotonic time source for elapsed budgets; a wall-clock adjustment should not extend a request.'
])],r'''import java.util.concurrent.*;
public class CooperativeQuoteCancellation {
    public static void main(String[] args) throws Exception {
        ExecutorService workers = Executors.newSingleThreadExecutor();
        CountDownLatch entered = new CountDownLatch(1), exited = new CountDownLatch(1);
        CountDownLatch neverReleased = new CountDownLatch(1);
        try {
            Future<?> task = workers.submit(() -> {
                entered.countDown();
                try { neverReleased.await(); }
                catch (InterruptedException cancelled) { Thread.currentThread().interrupt(); }
                finally { exited.countDown(); }
            });
            if (!entered.await(2, TimeUnit.SECONDS)) throw new IllegalStateException("Not admitted");
            System.out.println(task.cancel(true));
            if (!exited.await(2, TimeUnit.SECONDS)) throw new IllegalStateException("Worker did not exit");
            System.out.println(task.isCancelled());
            System.out.println("Worker exited");
        } finally {
            workers.shutdownNow();
            if (!workers.awaitTermination(2, TimeUnit.SECONDS)) throw new IllegalStateException("Pool did not stop");
        }
    }
}''','true\ntrue\nWorker exited',
['The latches use bounded waits in this program, and cleanup is checked separately from future cancellation. Real resource cleanup can require additional work, so a timeout policy must account for that phase. Cancelling a local task cannot retract a remote operation that already committed.'],
['TimeoutException does not automatically cancel the worker.','Do not discard an interrupt and resume the same waiting loop.','Future cancellation is not a remote rollback guarantee.'],[('completable-future','Completion-stage boundaries'),('executors','Executor ownership')])

put('file-channels','Java file channels: buffer positions and partial transfers',
'FileChannel moves bytes between a file and buffers whose positions and limits describe the next readable or writable region.',
[('Move the buffer between modes',[
'A manifest header uses three four-byte signed integers in big-endian order. putInt advances the position as the header is built. flip sets the limit to the written extent and resets the position so the next operation reads those bytes for output.',
'A write call can transfer fewer bytes than requested. Loop while the buffer has remaining data. Reading back has the same partial-transfer boundary; stop on end-of-file and reject a truncated header rather than parsing an incomplete buffer.',
'Byte order belongs to the file format. ByteBuffer has a default, but stating the order beside the field layout prevents a future implementation in another language from guessing. Direct buffers, mapped regions and zero-copy transfers have separate lifetime and platform tradeoffs; this small header does not need them.'
]),('Own the file and the channel',[
'The fixture creates a temporary file and removes it after channel closure. It also checks the exact number of header bytes read. Successful write completion does not promise crash durability; a persistent application needs a force and replacement policy appropriate to its filesystem.'
])],r'''import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.channels.FileChannel;
import java.nio.file.*;
public class ManifestHeaderChannel {
    public static void main(String[] args) throws Exception {
        Path file = Files.createTempFile("aitrove-header-", ".bin");
        try {
            ByteBuffer header = ByteBuffer.allocate(12).order(ByteOrder.BIG_ENDIAN);
            header.putInt(7).putInt(42).putInt(3).flip();
            try (FileChannel channel = FileChannel.open(file, StandardOpenOption.WRITE, StandardOpenOption.READ)) {
                while (header.hasRemaining()) channel.write(header);
                channel.position(0);
                ByteBuffer restored = ByteBuffer.allocate(12).order(ByteOrder.BIG_ENDIAN);
                while (restored.hasRemaining() && channel.read(restored) != -1) { }
                if (restored.position() != 12) throw new IllegalStateException("Truncated header");
                restored.flip();
                System.out.println(restored.getInt() + ":" + restored.getInt() + ":" + restored.getInt());
            }
        } finally { Files.deleteIfExists(file); }
    }
}''','7:42:3',
['This fixed header holds 12 bytes, so its application buffer is O(1). General file copying visits O(n) bytes and needs a bounded chunk buffer. Storage latency and partial transfers make the number of system calls different from the number of fields in the format.'],
['Reading a freshly filled buffer requires changing its position and limit.','One read is not a complete-record guarantee.','A closed channel does not imply a crash-durable transaction.'],[('byte-streams','Stream transfer loops'),('files','File paths and ownership')])

put('socket-boundaries','Java sockets: connection deadlines, framing and stream ownership',
'A TCP socket carries an ordered byte stream; it does not preserve application message boundaries.',
[('Declare one record boundary',[
'A line-based depot protocol ends each short record with a newline and uses UTF-8 on both sides. Without that framing rule, a receiver cannot decide whether a partial read is a complete record or the beginning of another transfer.',
'The program binds only to loopback, uses an operating-system selected port and sets connect, accept and read timeouts. It starts one local peer and waits for that peer’s future. No external service, credential or internet connection is used.',
'Read timeout and connect timeout cover different phases. Neither supplies an unlimited-input defense. This peer accepts only its tiny fixed fixture; a general server must bound record size while reading, validate every field and decide how to handle malformed or disconnected clients.'
]),('Close the owned endpoint',[
'Flushing the writer makes the newline available to the peer. The socket is closed after one exchange, and the listening endpoint closes in the outer scope. The worker executor is also shut down. A successful flush means bytes reached the stream, not that a remote business action was committed.'
])],r'''import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;
public class LocalDepotSocket {
    public static void main(String[] args) throws Exception {
        ExecutorService peer = Executors.newSingleThreadExecutor();
        try (ServerSocket server = new ServerSocket(0, 1, InetAddress.getLoopbackAddress())) {
            server.setSoTimeout(2000);
            Future<?> reply = peer.submit(() -> {
                try (Socket accepted = server.accept()) {
                    accepted.setSoTimeout(2000);
                    BufferedReader input = new BufferedReader(new InputStreamReader(accepted.getInputStream(), StandardCharsets.UTF_8));
                    PrintWriter output = new PrintWriter(new OutputStreamWriter(accepted.getOutputStream(), StandardCharsets.UTF_8), true);
                    if (!"PING".equals(input.readLine())) throw new IOException("Invalid record");
                    output.println("PONG");
                } catch (IOException failure) { throw new UncheckedIOException(failure); }
            });
            try (Socket client = new Socket()) {
                client.connect(new InetSocketAddress(InetAddress.getLoopbackAddress(), server.getLocalPort()), 2000);
                client.setSoTimeout(2000);
                PrintWriter output = new PrintWriter(new OutputStreamWriter(client.getOutputStream(), StandardCharsets.UTF_8), true);
                output.println("PING");
                BufferedReader input = new BufferedReader(new InputStreamReader(client.getInputStream(), StandardCharsets.UTF_8));
                System.out.println(input.readLine());
            }
            reply.get(2, TimeUnit.SECONDS);
        } finally {
            peer.shutdownNow();
            if (!peer.awaitTermination(2, TimeUnit.SECONDS)) throw new IllegalStateException("Peer did not stop");
        }
    }
}''','PONG',
['The exchange has a fixed payload. A real stream parser uses work proportional to received bytes and should cap both those bytes and its buffering. This sample has no TLS, authentication, retry deduplication or durable delivery; those requirements belong above the transport.'],
['A TCP read can return part of a record.','Connect timeout is not read timeout.','Do not trust a peer to send a newline within an unbounded memory budget.'],[('byte-streams','Byte ownership'),('cancellation','Request deadlines')])

put('flight-recorder','Java Flight Recorder: a bounded recording and a checked artifact',
'Java Flight Recorder collects enabled runtime and application events into a recording that can be inspected after the observed workload.',
[('Ask a workload question first',[
'A parcel importer can be slow because it allocates heavily, waits on a lock or blocks on storage. A recording helps distinguish those causes when the relevant events are enabled. A single elapsed-time number cannot tell which resource caused the delay.',
'This program records one application event carrying a parcel count. It explicitly enables the event type, commits the event, stops the recording and reads the dumped artifact. That checks the recording pipeline without claiming it profiles an actual production import.',
'Keep identifying data out of event fields unless the diagnostic policy allows it. Recording files can outlive the process and move between machines. Bound recording retention and decide who can inspect the artifact before enabling it for requests containing private business data.'
]),('Separate heap evidence from timing evidence',[
'Allocation events can help find allocation pressure. A heap dump answers retained-object questions and can be much larger. A retained heap graph, a thread dump and a recording describe different observations; choose the artifact that can answer the question rather than collecting every possible file.'
])],r'''import jdk.jfr.Event;
import jdk.jfr.Label;
import jdk.jfr.Recording;
import jdk.jfr.consumer.RecordingFile;
import java.nio.file.*;
public class ParcelFlightRecording {
    @Label("Parcel batch")
    static class BatchEvent extends Event { int parcels; }
    public static void main(String[] args) throws Exception {
        Path artifact = Files.createTempFile("aitrove-batch-", ".jfr");
        try {
            try (Recording recording = new Recording()) {
                recording.enable(BatchEvent.class).withoutThreshold();
                recording.start();
                BatchEvent event = new BatchEvent(); event.parcels = 42; event.commit();
                recording.stop(); recording.dump(artifact);
            }
            boolean found = RecordingFile.readAllEvents(artifact).stream()
                .anyMatch(event -> event.getEventType().getName().equals(BatchEvent.class.getName()) && event.getInt("parcels") == 42);
            System.out.println("Batch event found=" + found);
        } finally { Files.deleteIfExists(artifact); }
    }
}''','Batch event found=true',
['Recording overhead depends on enabled events, thresholds and workload. No overhead percentage is measured here. readAllEvents loads this tiny fixture entirely; large recordings should be inspected with a streaming reader and an explicit storage budget. A JFR-capable JDK is required.'],
['Do not publish an overhead claim without measuring the target workload.','A recording is not a heap dump.','A program that records one event is not a production load test.'],[('gc-diagnostics','Heap and collector observations'),('jvm-memory','Object retention')],release=11)

put('avl-tree','Java AVL insertion: restoring a height invariant with rotations',
'An AVL tree is a binary search tree whose left and right subtree heights differ by at most one at every node.',
[('Track the information a repair needs',[
'A shipment-ID index that receives sorted IDs makes an ordinary unbalanced search tree grow into a chain. This implementation stores a height at each node and repairs the first imbalances on the path back from an insertion.',
'A rotation changes local child links while preserving in-order key order. A left-right insertion first rotates the left child left, then rotates the parent right. Heights are recomputed from the repaired children; updating a parent before its old child is repaired can keep a stale height.',
'This is a set of int identifiers. Re-inserting an existing identifier does not create another node. A map variant would need a defined replacement policy for its value. For ordinary application code, a library sorted map or set is usually a smaller maintenance commitment than a custom tree.'
])],r'''public class ShipmentAvlIndex {
    static final class Node {
        final int id; Node left, right; int height = 1;
        Node(int id) { this.id = id; }
    }
    Node root;
    static int height(Node n) { return n == null ? 0 : n.height; }
    static void update(Node n) { n.height = 1 + Math.max(height(n.left), height(n.right)); }
    static Node right(Node n) {
        Node replacement = n.left; n.left = replacement.right; replacement.right = n;
        update(n); update(replacement); return replacement;
    }
    static Node left(Node n) {
        Node replacement = n.right; n.right = replacement.left; replacement.left = n;
        update(n); update(replacement); return replacement;
    }
    static Node insert(Node n, int id) {
        if (n == null) return new Node(id);
        if (id < n.id) n.left = insert(n.left, id);
        else if (id > n.id) n.right = insert(n.right, id);
        else return n;
        update(n);
        int balance = height(n.left) - height(n.right);
        if (balance > 1) {
            if (id > n.left.id) n.left = left(n.left);
            return right(n);
        }
        if (balance < -1) {
            if (id < n.right.id) n.right = right(n.right);
            return left(n);
        }
        return n;
    }
    void add(int id) { root = insert(root, id); }
    boolean contains(int id) {
        Node current = root;
        while (current != null) {
            if (id == current.id) return true;
            current = id < current.id ? current.left : current.right;
        }
        return false;
    }
    public static void main(String[] args) {
        ShipmentAvlIndex index = new ShipmentAvlIndex();
        for (int id : new int[]{30, 10, 20, 40, 50}) index.add(id);
        System.out.println(index.contains(20));
        System.out.println(index.contains(21));
        System.out.println(height(index.root));
    }
}''','true\nfalse\n3',
['The maintained height invariant gives O(log n) search and insertion. Insertion uses O(log n) recursion stack; the tree stores O(n) nodes. This implementation covers insertion and lookup, not deletion. Deletion needs its own rebalance cases and tests; the unbalanced BST deletion lesson cannot simply be pasted into this class.'],
['Update both affected heights after each rotation.','Do not claim AVL deletion is implemented here.','Test ascending, descending, duplicate and zig-zag insertions.'],[('binary-search-tree','BST deletion'),('treemap','Library sorted maps')],subject='java-dsa')

put('trie','Java trie: prefix lookup with a declared alphabet',
'A trie stores a path for each key prefix so exact membership and prefix membership can be tested separately.',
[('Validate before creating a path',[
'A parcel command dictionary accepts lowercase ASCII words. Each node has 26 child positions. That fixed alphabet keeps this implementation small; it is not a Unicode word dictionary.',
'The entire input is checked before insertion. If an invalid character were discovered halfway through creating nodes, a rejected command could leave partial paths that make later prefix checks succeed. The validation boundary prevents that particular mutation leak.',
'A terminal flag distinguishes a complete command from a prefix. Inserting parcel makes par a reachable path, but does not make par a stored command. An empty prefix is accepted as a query for the dictionary root; an empty command is rejected.'
])],r'''public class ParcelCommandTrie {
    static final class Node { final Node[] children = new Node[26]; boolean terminal; }
    final Node root = new Node();
    static void validate(String text, boolean allowEmpty) {
        if (text == null || (!allowEmpty && text.isEmpty())) throw new IllegalArgumentException("Missing word");
        for (int i=0; i<text.length(); i++)
            if (text.charAt(i) < 'a' || text.charAt(i) > 'z') throw new IllegalArgumentException("ASCII lowercase required");
    }
    void add(String word) {
        validate(word, false); Node current = root;
        for (int i=0; i<word.length(); i++) {
            int slot = word.charAt(i)-'a';
            if (current.children[slot] == null) current.children[slot] = new Node();
            current = current.children[slot];
        }
        current.terminal = true;
    }
    Node find(String text) {
        validate(text, true); Node current = root;
        for (int i=0; i<text.length(); i++) {
            current = current.children[text.charAt(i)-'a'];
            if (current == null) return null;
        }
        return current;
    }
    boolean contains(String word) { Node n=find(word); return n != null && n.terminal; }
    boolean hasPrefix(String prefix) { return find(prefix) != null; }
    public static void main(String[] args) {
        ParcelCommandTrie commands = new ParcelCommandTrie();
        commands.add("parcel"); commands.add("packing"); commands.add("label");
        System.out.println(commands.hasPrefix("pack"));
        System.out.println(commands.contains("pack"));
        System.out.println(commands.contains("parcel"));
        try { commands.add("Parcel"); }
        catch (IllegalArgumentException rejected) { System.out.println("Alphabet rejected"); }
    }
}''','true\nfalse\ntrue\nAlphabet rejected',
['Insertion and queries inspect O(L) characters for a key of length L. New storage is proportional to previously absent prefix nodes, each carrying 26 reference slots. A sparse child map trades that array cost for lookup and allocation costs. This model does not implement deletion or ranking of suggestions.'],
['A reachable prefix is not necessarily a stored word.','Validate the full alphabet before mutating.','Do not use a 26-slot trie for arbitrary Unicode code points.'],[('strings','Text representation'),('hashset','Exact membership alternative')],subject='java-dsa')

put('binary-heap','Java binary min-heap: sifting, fixed capacity and duplicate priorities',
'A binary min-heap keeps every parent priority no greater than its children so its root supplies a minimum value.',
[('Maintain one local relation',[
'A dispatch queue stores integer priorities. Inserting at the next array slot can violate the relation to its parent, so sift-up swaps until that relation is restored. Polling replaces the root with the last member, then sift-down chooses the smaller child.',
'The array is bounded by a constructor capacity. This implementation rejects a full queue rather than resizing or dropping a job. Equal priorities are retained as separate values, but their original arrival order is not represented; stable job order needs a sequence-number tie-breaker.',
'Heap order is weaker than complete sorting. A caller that walks this backing array does not receive sorted output. Repeated poll calls produce ascending priorities because each call repairs the root relation before the next removal.'
])],r'''import java.util.ArrayList;
import java.util.List;
import java.util.NoSuchElementException;
public class FixedDispatchHeap {
    final int[] priorities; int size;
    FixedDispatchHeap(int capacity) {
        if (capacity < 0) throw new IllegalArgumentException("Negative capacity");
        priorities = new int[capacity];
    }
    void add(int priority) {
        if (size == priorities.length) throw new IllegalStateException("Full heap");
        int position = size++; priorities[position] = priority;
        while (position > 0) {
            int parent = (position-1)/2;
            if (priorities[parent] <= priorities[position]) break;
            swap(parent, position); position = parent;
        }
    }
    void swap(int a, int b) { int old=priorities[a]; priorities[a]=priorities[b]; priorities[b]=old; }
    int poll() {
        if (size == 0) throw new NoSuchElementException("Empty heap");
        int selected=priorities[0]; priorities[0]=priorities[--size]; int position=0;
        while (position < size/2) {
            int child=2*position+1;
            if (child+1<size && priorities[child+1]<priorities[child]) child++;
            if (priorities[position]<=priorities[child]) break;
            swap(position, child); position=child;
        }
        return selected;
    }
    public static void main(String[] args) {
        FixedDispatchHeap queue = new FixedDispatchHeap(4);
        for (int priority : new int[]{7, 4, -2, 4}) queue.add(priority);
        List<Integer> removed=new ArrayList<>();
        while (queue.size>0) removed.add(queue.poll());
        System.out.println(removed);
        try { queue.poll(); }
        catch (NoSuchElementException empty) { System.out.println("Empty rejected"); }
    }
}''','[-2, 4, 4, 7]\nEmpty rejected',
['Insertion and removal sift through at most O(log n) levels. The fixed backing array occupies O(capacity) space, even when few elements are admitted. Polling all values uses O(n log n) work; the example also allocates O(n) result storage for display.'],
['The heap array is not a sorted report.','Capacity rejection is part of this method contract.','Equal priorities do not imply first-in-first-out order.'],[('priorityqueue','Library priority queues'),('heap-top-k','Keeping the largest values')],subject='java-dsa')

put('kmp-search','Java KMP substring search: reused prefix information and UTF-16 indices',
'Knuth–Morris–Pratt search uses a pattern-prefix fallback array so a mismatch can reuse earlier comparisons instead of restarting at the next text position.',
[('Keep the meaning of each index',[
'The prefix value at position i records the length of a proper pattern prefix that is also a suffix ending at i. On a mismatch, that value tells the search how much of its matched pattern can still be useful.',
'The text index never moves backward. The pattern index may fall back several times, but each successful advance creates only a bounded amount of later fallback work. That accounting gives the combined linear bound rather than merely hoping that typical inputs have few repeated prefixes.',
'This implementation compares Java char values and returns a UTF-16 index like ordinary String indexing. It does not normalize text or treat user-perceived characters as matching units. The empty pattern returns zero by the method contract; an absent nonempty pattern returns minus one.'
])],r'''public class ManifestPatternSearch {
    static int[] prefixes(String pattern) {
        int[] fallback = new int[pattern.length()]; int matched=0;
        for (int i=1; i<pattern.length(); i++) {
            while (matched>0 && pattern.charAt(i)!=pattern.charAt(matched)) matched=fallback[matched-1];
            if (pattern.charAt(i)==pattern.charAt(matched)) matched++;
            fallback[i]=matched;
        }
        return fallback;
    }
    static int find(String text, String pattern) {
        java.util.Objects.requireNonNull(text); java.util.Objects.requireNonNull(pattern);
        if (pattern.isEmpty()) return 0;
        int[] fallback=prefixes(pattern); int matched=0;
        for (int i=0; i<text.length(); i++) {
            while (matched>0 && text.charAt(i)!=pattern.charAt(matched)) matched=fallback[matched-1];
            if (text.charAt(i)==pattern.charAt(matched)) matched++;
            if (matched==pattern.length()) return i-pattern.length()+1;
        }
        return -1;
    }
    public static void main(String[] args) {
        System.out.println(find("PKPKPKOK", "PKOK"));
        System.out.println(find("dispatch", "lost"));
        System.out.println(find("dispatch", ""));
    }
}''','4\n-1\n0',
['For text length n and pattern length m, preprocessing and search use O(n+m) comparisons and O(m) auxiliary storage. Null inputs are not accepted; the implementation will fail rather than interpret null as an empty string. Repeated searches for one pattern can reuse its preprocessed state in a separate immutable matcher.'],
['The prefix must be proper; the whole prefix is not its own fallback.','A returned index is measured in UTF-16 units.','Resetting to zero on every mismatch loses the fallback information.'],[('text-normalization','Text equality policy'),('regular-expressions','Pattern grammar matching')],subject='java-dsa')

put('minimum-spanning-tree','Java Kruskal: cheapest connecting forest and disjoint-set checks',
'Kruskal’s algorithm builds a minimum-weight spanning forest by considering undirected edges in increasing weight order and accepting edges that join different components.',
[('Connect components without closing a cycle',[
'A depot network needs a set of links that connects reachable depots at minimum total link cost. This is not a shortest route from one depot to another. A cheap connecting tree can contain a longer individual route than the shortest-path solution.',
'After sorting, disjoint-set membership decides whether a candidate edge closes a cycle. A successful union reduces the component count. Self-loops and edges within an already joined component are skipped; parallel links can be considered independently.',
'A disconnected input returns a forest and a remaining component count. The program does not label that result a spanning tree. Zero and negative edge costs are allowed because cycle avoidance still supplies the relevant constraint.'
])],r'''import java.util.Arrays;
import java.util.Comparator;
public class DepotLinkForest {
    static final class Edge {
        final int from,to,cost;
        Edge(int from,int to,int cost){this.from=from;this.to=to;this.cost=cost;}
    }
    static final class Result { final long cost; final int components;
        Result(long cost,int components){this.cost=cost;this.components=components;} }
    static int root(int[] parent,int vertex){
        while(parent[vertex]!=vertex){parent[vertex]=parent[parent[vertex]];vertex=parent[vertex];}
        return vertex;
    }
    static Result connect(int vertices,Edge[] input){
        if(vertices<0)throw new IllegalArgumentException("Negative vertices");
        for(Edge edge:input)if(edge.from<0||edge.to<0||edge.from>=vertices||edge.to>=vertices)throw new IllegalArgumentException("Invalid endpoint");
        Edge[] edges=input.clone();Arrays.sort(edges,Comparator.comparingInt(edge->edge.cost));
        int[] parent=new int[vertices],sizes=new int[vertices];
        for(int v=0;v<vertices;v++){parent[v]=v;sizes[v]=1;}
        long cost=0;int components=vertices;
        for(Edge edge:edges){
            int a=root(parent,edge.from),b=root(parent,edge.to);if(a==b)continue;
            if(sizes[a]<sizes[b]){int temporary=a;a=b;b=temporary;}
            parent[b]=a;sizes[a]+=sizes[b];cost=Math.addExact(cost,edge.cost);components--;
        }
        return new Result(cost,components);
    }
    public static void main(String[] args){
        Result result=connect(4,new Edge[]{new Edge(0,1,4),new Edge(1,2,2),new Edge(2,3,3),new Edge(0,3,10)});
        System.out.println("cost="+result.cost+", components="+result.components);
        Result forest=connect(3,new Edge[]{new Edge(0,1,-2)});
        System.out.println("cost="+forest.cost+", components="+forest.components);
    }
}''','cost=9, components=1\ncost=-2, components=2',
['Sorting e edges uses O(e log e) work. Union by size and path halving add near-linear disjoint-set work across the edge scan. The copied edge array and component arrays occupy O(e+v) auxiliary storage. Checked long accumulation rejects a total that cannot be represented.'],
['A disconnected forest is not one spanning tree.','Minimum total connection cost is not a shortest-path answer.','Do not forbid negative link costs just because Dijkstra forbids negative edge weights.'],[('union-find','Disjoint-set invariants'),('dijkstra','Source distances')],subject='java-dsa')

put('bellman-ford','Java Bellman–Ford: negative edges and reachable negative cycles',
'Bellman–Ford computes single-source distances by repeatedly relaxing edges and detects a negative-weight cycle reachable from the source.',
[('Bound the number of useful edges',[
'Without a reachable negative cycle, a shortest route can be chosen without repeating a vertex, so it needs at most v-1 edges. Each pass permits another edge of improvement. If a full pass changes nothing, the distances have already reached a fixed point.',
'An additional pass checks whether another improvement remains possible. Only edges from a reachable vertex count: an unreachable negative cycle does not make distances from this source undefined.',
'The unreachable sentinel is not added to an edge weight. Doing that arithmetic can wrap into a plausible distance. The program also uses checked addition for finite distances and rejects invalid endpoints before running the relaxation loop.'
])],r'''import java.util.Arrays;
public class CreditRouteDistances {
    static final class Edge { final int from,to,weight;
        Edge(int from,int to,int weight){this.from=from;this.to=to;this.weight=weight;} }
    static long[] distances(int vertices,Edge[] edges,int source){
        if(vertices<1||source<0||source>=vertices)throw new IllegalArgumentException("Invalid source");
        for(Edge edge:edges)if(edge.from<0||edge.to<0||edge.from>=vertices||edge.to>=vertices)throw new IllegalArgumentException("Invalid edge");
        long[] result=new long[vertices];Arrays.fill(result,Long.MAX_VALUE);result[source]=0;
        for(int pass=1;pass<vertices;pass++){
            boolean changed=false;
            for(Edge edge:edges)if(result[edge.from]!=Long.MAX_VALUE){
                long candidate=Math.addExact(result[edge.from],edge.weight);
                if(candidate<result[edge.to]){result[edge.to]=candidate;changed=true;}
            }
            if(!changed)break;
        }
        for(Edge edge:edges)if(result[edge.from]!=Long.MAX_VALUE&&Math.addExact(result[edge.from],edge.weight)<result[edge.to])
            throw new IllegalStateException("Reachable negative cycle");
        return result;
    }
    public static void main(String[] args){
        Edge[] valid={new Edge(0,1,4),new Edge(0,2,7),new Edge(1,2,-2),new Edge(2,3,3)};
        System.out.println(Arrays.toString(distances(4,valid,0)));
        Edge[] cycle=Arrays.copyOf(valid,5);cycle[4]=new Edge(3,1,-6);
        try{distances(4,cycle,0);}catch(IllegalStateException rejected){System.out.println(rejected.getMessage());}
    }
}''','[0, 4, 2, 5]\nReachable negative cycle',
['Worst-case relaxation uses O(v e) work and O(v) distance storage in addition to the input edges. This implementation reports distances and failure, not the cycle vertices or reconstructed routes. Path reconstruction needs predecessor state and a carefully defined unreachable result.'],
['Do not add a weight to Long.MAX_VALUE.','The cycle must be reachable from this source to invalidate its distances.','Dijkstra is not a drop-in replacement when negative edges are permitted.'],[('dijkstra','Non-negative path costs'),('graph-bfs','Unweighted distances')],subject='java-dsa')

put('tabulation','Java bottom-up tabulation: dependency order and unreachable states',
'Bottom-up tabulation stores solutions to smaller states and evaluates them in an order that satisfies every dependency.',
[('Choose the state before writing loops',[
'A packaging calculator asks for the fewest allowed pack sizes that exactly fill an order quantity. The state is the requested quantity, and its value is the smallest pack count. State zero is reachable using zero packs; an unfilled state needs a distinct sentinel.',
'Positive pack sizes make every transition point to a smaller quantity. The ascending loop therefore visits dependencies first. A zero pack size would point back to the same state, while a negative size would invalidate both indexing and the dependency proof.',
'Greedily choosing the largest pack does not solve this general exact-fill problem. A local choice can leave a remainder that no pack can fill, or use more packs than a smaller initial choice. The recurrence compares all permitted final packs at each quantity.'
])],r'''import java.util.Arrays;
public class ExactPackTabulation {
    static int minimum(int quantity,int[] packs){
        if(quantity<0||quantity>1_000_000)throw new IllegalArgumentException("Quantity outside budget");
        for(int pack:packs)if(pack<=0)throw new IllegalArgumentException("Positive packs required");
        int absent=quantity+1;int[] best=new int[quantity+1];Arrays.fill(best,absent);best[0]=0;
        for(int amount=1;amount<=quantity;amount++)
            for(int pack:packs)if(pack<=amount&&best[amount-pack]!=absent)best[amount]=Math.min(best[amount],best[amount-pack]+1);
        return best[quantity]==absent?-1:best[quantity];
    }
    public static void main(String[] args){
        int[] packs={3,5};System.out.println(minimum(9,packs));
        System.out.println(minimum(7,packs));System.out.println(minimum(0,packs));
    }
}''','3\n-1\n0',
['For target quantity q and k pack sizes, the method uses O(q k) work and O(q) storage. The explicit maximum quantity is an application memory budget. This is pseudo-polynomial work in the numeric target, not logarithmic work in the number of digits used to encode it.'],
['Zero and negative transitions invalidate the recurrence.','Keep unreachable separate from a zero-cost solution.','A large numeric target can exceed an acceptable allocation budget.'],[('memoization','Top-down cached states'),('backtracking','Enumerated choices')],subject='java-dsa')

put('greedy-intervals','Java greedy interval selection: an exchange proof and a limited objective',
'Earliest-finish interval selection chooses a maximum number of non-overlapping unweighted intervals by accepting available intervals in finish-time order.',
[('State exactly what is optimized',[
'A loading bay can host one job at a time, and every accepted job counts equally. Sort by finish time, then accept a job whose start is at least the previous accepted finish. Intervals here are half-open, so a job ending at time 3 permits another to start at time 3.',
'The exchange argument justifies the choice. Replace the first interval of an optimal answer with the earliest-finishing available interval. It finishes no later, so the remaining selected intervals still fit. Repeat the argument on the remaining time window.',
'That proof does not optimize profit, duration or urgency. Assigning different values to jobs produces a different problem, often requiring a weighted recurrence. It also assumes one bay and fixed intervals; multiple resources need a new scheduling model.'
])],r'''import java.util.Arrays;
import java.util.Comparator;
public class LoadingBayIntervals {
    static int maximumCount(int[][] input){
        int[][] jobs=new int[input.length][2];
        for(int i=0;i<input.length;i++){
            if(input[i]==null||input[i].length!=2||input[i][0]>=input[i][1])throw new IllegalArgumentException("Invalid interval");
            jobs[i]=input[i].clone();
        }
        Arrays.sort(jobs,Comparator.comparingInt(job->job[1]));
        int finish=Integer.MIN_VALUE,accepted=0;
        for(int[] job:jobs)if(job[0]>=finish){accepted++;finish=job[1];}
        return accepted;
    }
    public static void main(String[] args){
        System.out.println(maximumCount(new int[][]{{1,4},{3,5},{0,2},{5,7},{2,3}}));
        System.out.println(maximumCount(new int[0][2]));
    }
}''','4\n0',
['Sorting n intervals takes O(n log n) work; the acceptance scan takes O(n). The defensive copy uses O(n) storage and prevents the sort from reordering caller-owned rows. Sorting endpoints by subtraction can overflow, so the comparator compares integers directly.'],
['The objective is count, not weighted value.','Half-open versus closed intervals changes the equality check.','Earliest start does not have the same exchange argument as earliest finish.'],[('sorting','Ordering policies'),('tabulation','Weighted-state reasoning')],subject='java-dsa')

put('generics-interview','Java generics interview: variance, erasure and compiler boundaries',
'Generic type arguments constrain source-level use of a type; erasure does not turn unrelated generic declarations into interchangeable compiler types.',
[('Can List<Integer> replace List<Number>?',[
'No. If that assignment were accepted, a consumer could insert a Double into storage another caller expects to contain only Integer. List<? extends Number> instead supplies a read-oriented number boundary, while List<? super Integer> permits inserting Integer values without promising that reads return Integer.',
'The copy method has an integer-producing source and an integer-accepting destination. It can copy to a List<Object> because that destination can hold integers. It does not cast the source to a raw list or claim every object already in the destination is an integer.'
]),('What survives erasure?',[
'The runtime class of ArrayList<Integer> and ArrayList<String> is the same implementation class. That observation does not disable the compiler rules for their contents. Casts inserted at use sites can fail if raw or unchecked code polluted the structure earlier.',
'A generic array allocation such as new T[length] is unavailable because the runtime array element checks would need an element type that is not generally available after erasure. Supplying a checked array factory or keeping list storage is a clearer boundary than promising an unchecked cast is safe.'
]),('What does PECS leave out?',[
'Producer-extends and consumer-super describe a direction for an API argument; they do not determine ownership, mutability or thread safety. A readable wildcard can still hold a mutable object, and a caller can still modify the underlying list through another alias.'
])],r'''import java.util.*;
public class IntegerBatchVariance {
    static void copy(List<? super Integer> target,List<? extends Integer> source){
        for(Integer amount:source)target.add(amount);
    }
    public static void main(String[] args){
        List<Integer> quantities=new ArrayList<>(Arrays.asList(7,9));
        List<? extends Number> observed=quantities;
        List<Object> exported=new ArrayList<>();copy(exported,quantities);
        System.out.println(exported);
        System.out.println(observed.get(0).intValue());
        System.out.println(quantities.getClass()==new ArrayList<String>().getClass());
    }
}''','[7, 9]\n7\ntrue',
['Copying n entries visits O(n) references and grows destination membership storage. Variance does not copy values or synchronize the source traversal. A concurrently edited ordinary source needs an ownership or locking rule before this method can provide a consistent batch.'],
['List<Integer> is not a subtype of List<Number>.','A readable wildcard does not freeze element state.','An unchecked cast relocates a potential failure; it does not prove compatibility.'],[('generics','Generic APIs'),('collection-views','Ownership after a copy')],subject='java-interview')

put('streams-interview','Java streams interview: laziness, one-use pipelines and reduction rules',
'A stream describes a one-use computation pipeline; intermediate operations are evaluated as required by a terminal operation.',
[('When does the work run?',[
'Creating this map-and-filter pipeline does not traverse the source. collect supplies the terminal demand. The inspection counter is a teaching trace for this particular collection operation; production behavior must not rely on side effects in intermediate operations.',
'A terminal operation is allowed to avoid work it does not need. For example, an implementation can compute a count from known source sizing without executing a mapping function that does not affect that count. A trace for collect is not a guarantee that every terminal will visit the same callbacks.'
]),('Can the stream be reused?',[
'No. Build a fresh stream from its source for another terminal operation. Keeping a Stream field in a repository and handing it to several consumers creates a lifecycle failure, even when the underlying collection itself is reusable.'
]),('What makes a parallel reduction correct?',[
'The identity must be neutral for the combining operation, and the accumulation must be associative under the required result semantics. Integer overflow, floating-point rounding and a non-neutral seed can change results when partitions are combined. Parallelism also does not make captured mutable state safe.',
'Encounter order and execution order differ. A terminal result can preserve encounter order while workers execute callbacks in another order. Use an explicit ordering requirement rather than a print statement to infer what a parallel pipeline guarantees.'
])],r'''import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.*;
public class StreamDemandProbe {
    public static void main(String[] args){
        AtomicInteger inspected=new AtomicInteger();
        Stream<Integer> selected=Arrays.asList(3,7,7).stream()
            .map(quantity->{inspected.incrementAndGet();return quantity;}).filter(quantity->quantity>4);
        System.out.println(inspected.get());
        System.out.println(selected.collect(Collectors.toList()));
        System.out.println(inspected.get());
        try{selected.count();}catch(IllegalStateException consumed){System.out.println("Stream already consumed");}
    }
}''','0\n[7, 7]\n3\nStream already consumed',
['This terminal traversal performs O(n) work and stores O(k) selected values. The atomic counter is instrumentation, not a recommendation for side-effect-driven stream design. Parallel execution adds splitting, scheduling and combining costs; no speedup is measured here.'],
['Do not depend on peek or map side effects for required business work.','A stream is not a reusable collection.','A non-neutral reduction identity can be applied once per partition.'],[('streams','Pipeline contracts'),('lambdas','Captured state')],subject='java-interview')

put('exceptions-interview','Java exception interview: primary failures, suppressed cleanup and catch scope',
'Exception handling defines how a failure crosses a method boundary; cleanup can add a second failure without replacing the original one.',
[('Which failure leaves try-with-resources?',[
'If the body throws and close also throws, the body failure stays primary and the close failure is suppressed. The program prints both. Reporting only the cleanup failure would hide the operation that actually failed first.',
'When the body succeeds but close fails, that cleanup failure becomes the escaping failure. Resource cleanup is therefore part of the operation boundary, not a success-only detail.'
]),('Where should an exception be caught?',[
'Catch where the caller can make a specific decision: reject an input, retry a transient operation under a budget, translate a storage failure, or abort a request. Catching every Exception inside a low-level parser and returning zero can turn corrupt data into a plausible business quantity.'
]),('Does checked mean recoverable?',[
'No. The checked distinction affects compiler obligations, not whether recovery is feasible. A runtime exception can represent an invalid request, while a checked I/O failure can leave no safe local recovery. Document the state of the operation after failure.',
'A finally return can replace a pending return or exception. Avoid returning from cleanup. Preserving the original stack and suppressed failures gives the caller evidence it can use to decide whether work completed.'
])],r'''import java.io.IOException;
public class SuppressedImportFailure {
    static final class InputHandle implements AutoCloseable {
        public void close() throws IOException { throw new IOException("close failed"); }
    }
    public static void main(String[] args){
        try(InputHandle input=new InputHandle()){
            throw new IllegalStateException("parse failed");
        }catch(Exception failure){
            System.out.println(failure.getMessage());
            System.out.println(failure.getSuppressed()[0].getMessage());
        }
    }
}''','parse failed\nclose failed',
['The failure trace has constant application-sized state in this fixture. Stack capture, logging, retries and resource cleanup can have nontrivial cost in real services; do not use repeated exception creation as a normal hot-loop branch. A bounded retry also needs an idempotency decision.'],
['Do not return from finally.','Do not discard the primary failure when cleanup also fails.','Catching a failure does not imply partial mutations were rolled back.'],[('exceptions','Exception boundaries'),('try-with-resources','Resource lifetime')],subject='java-interview')

put('jdbc-interview','Java JDBC interview: auto-commit, rollback and database-specific evidence',
'A JDBC transaction groups database changes under a connection’s transaction state; rollback concerns those changes, not every action performed by the Java process.',
[('What changes when auto-commit is disabled?',[
'With auto-commit enabled, an ordinary statement participates in the connection’s auto-commit behavior. Disabling it gives the application an explicit commit or rollback boundary. Code should set and restore required state when a pooled connection is borrowed, rather than assume the last borrower left suitable settings.'
]),('Does rollback undo an email?',[
'No. A database transaction cannot retract an external message already sent. Applications coordinating storage with external effects need a durable handoff policy, often an outbox with deduplication. A try/catch block alone does not give distributed atomicity.'
]),('What does an H2 test prove?',[
'The probe inserts one row in a local H2 database, rolls back and verifies absence. It checks this transaction path with the declared driver. It does not certify isolation, lock timing, SQL dialect or connection-pool behavior in a different production database.',
'Test concurrent conflicting transactions against the actual target engine when isolation matters. Query parameters keep values separate from statement structure; identifiers such as a table name need a different allowlist or query-building boundary.'
])],r'''import java.sql.*;
public class JdbcRollbackProbe {
    public static void main(String[] args) throws Exception {
        try(Connection connection=DriverManager.getConnection("jdbc:h2:mem:rollback_probe")){
            try(Statement schema=connection.createStatement()){schema.execute("CREATE TABLE receipts(id INT PRIMARY KEY)");}
            connection.setAutoCommit(false);
            try(PreparedStatement insert=connection.prepareStatement("INSERT INTO receipts(id) VALUES(?)")){
                insert.setInt(1,42);insert.executeUpdate();
            }
            connection.rollback();
            try(Statement query=connection.createStatement();ResultSet result=query.executeQuery("SELECT COUNT(*) FROM receipts")){
                result.next();System.out.println("rows="+result.getInt(1));
            }
        }
    }
}''','rows=0',
['The database query and transaction costs depend on the engine, indexes, storage and contention. This tiny in-memory probe is a correctness check with H2 2.3.232, not a production throughput measurement. Connections, statements and result sets are all closed by their owning scope.'],
['Rollback does not undo external side effects.','Driver-specific tests do not certify another database engine.','Do not return a pooled connection with unexplained transaction state.'],[('jdbc-transactions','Transaction failures'),('jdbc-prepared','Bound parameters')],subject='java-interview',dependency='h2')

put('jvm-interview','Java JVM interview: reachability, publication and diagnostic evidence',
'The JVM manages runtime execution and memory areas, while application references still decide which object graphs remain reachable.',
[('Can a garbage-collected application leak memory?',[
'Yes. A registry, queue, cache or listener list can retain objects that are no longer useful. They remain reachable and therefore are not garbage merely because business logic stopped needing them. Follow a retained object’s path to a root before choosing a cleanup change.'
]),('Are references and their objects the same thing?',[
'A local reference can point to a shared heap object. Reassigning that reference does not replace another caller’s reference, and mutating the object can still be visible through other aliases. The program copies a byte payload at its ownership boundary so later source mutation cannot edit the retained bytes.'
]),('Does volatile repair a compound update?',[
'No. Volatile visibility and ordering do not make read-modify-write increments indivisible. Use the operation’s actual synchronization contract, such as an atomic update or a lock that protects the whole invariant.'
]),('What evidence is needed for a performance claim?',[
'Distinguish warmup, steady-state work, allocation rate, lock waiting and storage latency. A short run can include class loading and JIT work. A retained heap investigation and a CPU profile also answer different questions. Pick a repeatable workload and report the toolchain and measurement limits.'
])],r'''import java.util.Arrays;
public class PayloadOwnershipProbe {
    static final class StoredPayload {
        private final byte[] bytes;
        StoredPayload(byte[] input){bytes=input.clone();}
        byte[] snapshot(){return bytes.clone();}
    }
    public static void main(String[] args){
        byte[] incoming={1,2};StoredPayload stored=new StoredPayload(incoming);
        incoming[0]=9;
        byte[] first=stored.snapshot();first[1]=8;
        System.out.println(Arrays.toString(stored.snapshot()));
        System.out.println(Arrays.toString(incoming));
    }
}''','[1, 2]\n[9, 2]',
['Each payload copy uses O(n) byte work and O(n) storage. That ownership choice avoids alias mutation but can be costly for large payloads; immutable slices or bounded buffers need a different contract. Exact object sizes and collector behavior depend on the JVM configuration.'],
['Do not equate useful objects with reachable objects.','A volatile counter increment can still lose updates.','Avoid fixed object-size claims without identifying the runtime layout.'],[('jvm-memory','Runtime memory'),('flight-recorder','Diagnostic recordings')],subject='java-interview')

put('modern-java-interview','Modern Java interview: records, array ownership and virtual-thread limits',
'A record supplies a declared data carrier with generated members, but a record component can still reference mutable state.',
[('Is this record deeply immutable?',[
'No. An array component stays mutable unless the constructor and accessor enforce a copy or another ownership policy. The example copies at both boundaries. One constructor copy alone still lets the generated accessor expose that owned array to callers.'
]),('What does record equality compare?',[
'Generated record equality compares its components according to their types. Arrays are reference-based objects under their ordinary equals method, so two records containing different arrays with equal contents are not automatically content-equal. Define a value representation or a deliberate equals/hashCode policy when that distinction matters.'
]),('Do virtual threads make CPU work faster?',[
'They can make blocking task concurrency easier to represent, but do not increase the number of processors or remove downstream capacity constraints. A million tasks waiting for ten database connections still need an admission and deadline policy. Thread-local retention also scales with the number of active tasks.'
]),('What does a sealed hierarchy solve?',[
'It limits permitted subtypes, supporting explicit case handling. It does not validate every constructor argument or eliminate null from callers. Keep version labels next to pattern-switch and virtual-thread examples; this ownership probe itself needs the record support supplied by Java 17.'
])],r'''public class RecordArrayOwnership {
    record ParcelCounts(int[] values){
        ParcelCounts{values=values.clone();}
        public int[] values(){return values.clone();}
    }
    public static void main(String[] args){
        int[] input={2,3};ParcelCounts recorded=new ParcelCounts(input);input[0]=9;
        System.out.println(recorded.values()[0]);
        int[] output=recorded.values();output[0]=8;
        System.out.println(recorded.values()[0]);
        System.out.println(recorded.equals(new ParcelCounts(new int[]{2,3})));
    }
}''','2\n2\nfalse',
['Constructing this record and accessing its array each use O(n) copying work. That cost is an ownership decision, not an inherent cost of all records. The program makes no timing claim about virtual threads or pattern matching.'],
['A record reference to an array is not deep immutability.','Array components need an explicit content-equality decision.','Virtual threads do not remove external connection limits.'],[('records','Record members'),('virtual-threads','Blocking-task concurrency')],subject='java-interview',release=17)

put('oop-exercises','Java OOP exercises: invariant-preserving reservations and independent snapshots',
'Object-oriented boundary exercises check whether every public operation preserves the object’s stated invariant under rejected as well as accepted inputs.',
[('Implement before reading the solution',[
'Create a stock reservation object with non-negative available and reserved counts. reserve rejects non-positive quantities and returns false when stock is insufficient. A rejected request must not change either field. Expose an independent two-number snapshot rather than the object’s internal storage.',
'Test a successful reservation, an over-capacity request, zero input and mutation of a returned snapshot. State whether invalid input throws or returns a rejected result; this solution throws for a malformed quantity and returns false for a valid request that exceeds available stock.',
'The two rejection reasons are intentionally different. A UI can ask the customer to choose a smaller amount after insufficient stock, but zero is not a valid reservation quantity. A caller should not need to inspect a partially updated object to determine which branch occurred.'
])],r'''public class ReservationBoundaryExercises {
    static final class Stock {
        private int available,reserved;
        Stock(int available){if(available<0)throw new IllegalArgumentException("Negative stock");this.available=available;}
        boolean reserve(int quantity){
            if(quantity<=0)throw new IllegalArgumentException("Positive quantity required");
            if(quantity>available)return false;
            available-=quantity;reserved+=quantity;return true;
        }
        int[] snapshot(){return new int[]{available,reserved};}
    }
    static void require(boolean condition){if(!condition)throw new AssertionError("Boundary failed");}
    public static void main(String[] args){
        Stock stock=new Stock(10);require(stock.reserve(3));
        require(!stock.reserve(20));require(stock.snapshot()[0]==7&&stock.snapshot()[1]==3);
        try{stock.reserve(0);throw new AssertionError("Zero accepted");}catch(IllegalArgumentException expected){ }
        int[] detached=stock.snapshot();detached[0]=99;require(stock.snapshot()[0]==7);
        System.out.println("4 reservation checks passed");
    }
}''','4 reservation checks passed',
['Each operation touches fixed-sized state and uses O(1) work. Each snapshot allocates a two-element array. This model is single-threaded; sharing it between workers requires protecting the full available/reserved transition, not just marking each field volatile.'],
['Reject before mutating.','A snapshot must not expose owned mutable storage.','Separate malformed requests from valid requests that cannot be fulfilled.'],[('encapsulation','Public invariants'),('locks','Coordinated updates')],subject='java-exercises')

put('exception-exercises','Java exception exercises: all-or-nothing parsing of a small batch',
'Batch parsing can return a complete validated result or fail before exposing that result; a partially filled caller-owned list breaks that boundary.',
[('Specify the rejected cases',[
'Parse an array of quantity strings into positive int values. Reject a null member, malformed number, zero or negative value. The accepted output must preserve the input order, and the input strings must remain unchanged.',
'The solution builds private output storage. It can abandon that storage on failure without editing a previously published collection. This is an application-level boundary, not a database transaction and not a promise to roll back arbitrary callbacks performed during parsing.',
'Use exception tests that fail when the operation unexpectedly succeeds. A catch block that merely prints an error can pass even when no error happened. The supplied helper throws its own AssertionError after an accepted invalid input, so the test cannot silently skip the rejection requirement.'
])],r'''import java.util.*;
public class QuantityBatchExercises {
    static List<Integer> parse(String[] lines){
        List<Integer> accepted=new ArrayList<>();
        for(String line:lines){
            if(line==null)throw new IllegalArgumentException("Missing quantity");
            int quantity=Integer.parseInt(line);
            if(quantity<=0)throw new IllegalArgumentException("Positive quantity required");
            accepted.add(quantity);
        }
        return Collections.unmodifiableList(accepted);
    }
    static void rejected(String[] lines){
        try{parse(lines);throw new AssertionError("Invalid batch accepted");}
        catch(IllegalArgumentException expected){ }
    }
    public static void main(String[] args){
        if(!parse(new String[]{"3","7"}).equals(Arrays.asList(3,7)))throw new AssertionError("Wrong order");
        rejected(new String[]{"3","bad"});rejected(new String[]{"0"});rejected(new String[]{null});
        System.out.println("4 parsing checks passed");
    }
}''','4 parsing checks passed',
['Parsing work is proportional to the total input characters, with O(n) integer-reference storage for n accepted values. Large input also needs a byte, line and record-count budget before reaching this method. The empty array yields an empty result under this contract.'],
['Do not fill caller-owned output before the batch is validated.','A rejection test must fail when invalid input is accepted.','Catching NumberFormatException does not make zero a valid business quantity.'],[('exceptions','Catch boundaries'),('manifest-project','Validated file imports')],subject='java-exercises')

put('concurrency-exercises','Java concurrency exercises: completed-task accounting and worker shutdown',
'Concurrent task exercises must verify completed work rather than treating successful submission as successful execution.',
[('Write the acceptance checks first',[
'Submit twenty tasks, each incrementing a shared counter ten times. The final count must be two hundred. Each task must complete before the counter is read, and the executor must terminate before the process is considered finished.',
'The exercise uses AtomicInteger for individual increments and Futures for task completion. The atomic counter alone does not tell the caller when all tasks are done. Waiting on every future also exposes task failures through ExecutionException instead of replacing them with an apparently successful final count.',
'This small fixed batch is deliberately bounded at its source. Executors.newFixedThreadPool uses a queue whose capacity is not a complete overload policy. A public service accepting unbounded submissions needs an explicitly bounded queue and rejection behavior, even if its worker count is small.'
])],r'''import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
public class CompletedCounterExercises {
    public static void main(String[] args) throws Exception {
        ExecutorService workers=Executors.newFixedThreadPool(4);AtomicInteger completed=new AtomicInteger();
        List<Future<?>> tasks=new ArrayList<>();
        try{
            for(int batch=0;batch<20;batch++)tasks.add(workers.submit(()->{
                for(int item=0;item<10;item++)completed.incrementAndGet();
            }));
            for(Future<?> task:tasks)task.get(2,TimeUnit.SECONDS);
            if(completed.get()!=200)throw new AssertionError("Lost work");
            System.out.println("completed="+completed.get());
        }finally{
            workers.shutdownNow();
            if(!workers.awaitTermination(2,TimeUnit.SECONDS))throw new AssertionError("Workers retained");
        }
    }
}''','completed=200',
['The workload performs 200 atomic increments and stores twenty futures. Contention can affect execution time even though the total arithmetic work is fixed. These per-future waits are test guards, not one shared request deadline; a production batch needs an overall deadline policy.'],
['A submitted future can later fail.','A shared int increment is not atomic.','A fixed worker count does not by itself bound the pending queue.'],[('atomics','Atomic updates'),('cancellation','Shared deadline policy')],subject='java-exercises')

put('reading-list-project','Java reading-list project: validated titles and explicit file persistence',
'A persisted reading list separates validated in-memory membership from the file snapshot that survives a process restart.',
[('Define the file format and save boundary',[
'This project stores one nonempty UTF-8 title per line. Titles cannot contain line breaks, and the list is capped at ten thousand entries. The format deliberately has no quoted multiline field grammar. Changing that requirement needs a new parser and compatibility decision.',
'Adding or removing a title changes only the live list. save creates a staged file and then replaces the named snapshot. Loading parses private list state before returning the restored object, so an invalid file does not expose a half-restored list to callers.',
'An ordinary move does not claim a crash-durable transaction. A production store needs a tested replacement policy, filesystem capability checks, durability requirements and concurrent-writer coordination. This program is a local single-writer project with no synchronization between processes.'
]),('Run the acceptance scenario',[
'The fixture saves two titles, loads a new object, removes one title from the new object and loads the file again. The last count stays two because removal alone is not a save. The temporary directory is cleaned up after the scenario. To retain data in a real CLI, give the application an explicitly owned persistent path instead.'
])],r'''import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
public class ReadingListPersistence {
    final List<String> titles=new ArrayList<>();
    void add(String title){
        if(title==null||title.trim().isEmpty()||title.indexOf('\n')>=0||title.indexOf('\r')>=0)throw new IllegalArgumentException("Single nonempty title required");
        if(titles.size()==10000)throw new IllegalArgumentException("Title budget exhausted");
        titles.add(title.trim());
    }
    List<String> snapshot(){return Collections.unmodifiableList(new ArrayList<>(titles));}
    void remove(int index){titles.remove(index);}
    void save(Path destination) throws Exception {
        Path absolute=destination.toAbsolutePath();Path staged=Files.createTempFile(absolute.getParent(),"reading-stage-",".txt");
        try{
            byte[] snapshot=String.join("\n",titles).getBytes(StandardCharsets.UTF_8);
            if(snapshot.length>2_000_000)throw new IllegalArgumentException("Snapshot budget exhausted");
            Files.write(staged,snapshot);
            Files.move(staged,absolute,StandardCopyOption.REPLACE_EXISTING);
        }finally{Files.deleteIfExists(staged);}
    }
    static ReadingListPersistence load(Path source) throws Exception {
        if(Files.size(source)>2_000_000)throw new IllegalArgumentException("File budget exhausted");
        ReadingListPersistence restored=new ReadingListPersistence();
        for(String title:Files.readAllLines(source,StandardCharsets.UTF_8))restored.add(title);
        return restored;
    }
    public static void main(String[] args) throws Exception {
        Path directory=Files.createTempDirectory("aitrove-reading-");Path file=directory.resolve("titles.txt");
        try{
            ReadingListPersistence original=new ReadingListPersistence();
            original.add("Concurrency notes");original.add("Collections handbook");original.save(file);
            ReadingListPersistence restored=load(file);System.out.println(restored.snapshot());
            restored.remove(0);System.out.println(restored.snapshot());System.out.println("saved="+load(file).snapshot().size());
        }finally{Files.deleteIfExists(file);Files.deleteIfExists(directory);}
    }
}''','[Concurrency notes, Collections handbook]\n[Collections handbook]\nsaved=2',
['Loading visits O(b) input bytes and stores O(n) titles. The size check is suitable for this owned, unchanged fixture; an adversarial concurrently growing file needs a streaming byte limit during reading. Saving writes O(b) content and needs staged-file storage. Concurrent updates and crash recovery remain outside this project’s contract.'],
['Removing a title does not implicitly persist it.','A pre-read file size check is not a streaming limit under concurrent modification.','The staged replacement is not advertised as crash durability.'],[('files','File operations'),('exception-exercises','Private batch state')],subject='java-projects')

put('linkedlist-project','Java task-deque project: command parsing, endpoint order and rejected work',
'A task deque accepts normal work at the tail and urgent work at the head, then removes the next pending item from the head.',
[('Make each command a small boundary',[
'The command grammar supports add, urgent, next and list. add and urgent require a nonempty task description; next and list take no argument. An unknown command or extra argument is rejected rather than silently interpreted as a task.',
'Two equal descriptions remain distinct items. This contract has no task identifiers or deduplication. Urgent work can delay earlier normal work indefinitely, so it is an ordering rule rather than a fairness guarantee.',
'The implementation depends on Deque<String> but stores a LinkedList. Swapping the implementation to ArrayDeque preserves these operations for the validated non-null input. A concurrent or durable queue needs different coordination and storage decisions.'
]),('Keep input ownership outside the queue',[
'The demonstration executes a fixed sequence so it can be compiled and checked without waiting for stdin. A CLI loop can pass each complete line to execute and decide how to display rejected inputs. It should not close a shared System.in reader merely because one command completed.'
])],r'''import java.util.Deque;
import java.util.LinkedList;
public class TaskDequeCommands {
    final Deque<String> pending=new LinkedList<>();
    String execute(String line){
        if(line==null||line.trim().isEmpty())throw new IllegalArgumentException("Missing command");
        String[] parts=line.trim().split("\\s+",2);String command=parts[0];String argument=parts.length==2?parts[1].trim():"";
        if(command.equals("add")||command.equals("urgent")){
            if(argument.isEmpty())throw new IllegalArgumentException("Missing task");
            if(command.equals("add"))pending.addLast(argument);else pending.addFirst(argument);
            return "accepted";
        }
        if(!argument.isEmpty())throw new IllegalArgumentException("Unexpected argument");
        if(command.equals("next")){String task=pending.pollFirst();return task==null?"empty":task;}
        if(command.equals("list"))return pending.toString();
        throw new IllegalArgumentException("Unknown command");
    }
    public static void main(String[] args){
        TaskDequeCommands queue=new TaskDequeCommands();
        queue.execute("add Audit stock");queue.execute("add Print label");queue.execute("urgent Verify address");
        System.out.println(queue.execute("list"));System.out.println(queue.execute("next"));
        System.out.println(queue.execute("list"));
        try{queue.execute("add");}catch(IllegalArgumentException rejected){System.out.println("Empty task rejected");}
    }
}''','[Verify address, Audit stock, Print label]\nVerify address\n[Audit stock, Print label]\nEmpty task rejected',
['Endpoint insertion and removal use O(1) linked-node work; parsing visits the command characters and list rendering visits O(n) tasks. The queue retains descriptions until removed. It is in memory only and has no bounded admission policy; the calling CLI must limit admitted work if input is not trusted to stay small.'],
['Do not promise persistence across restart.','Urgent-at-head ordering can starve normal work.','A Deque interface does not make a LinkedList thread-safe.'],[('linkedlist','LinkedList contracts'),('blocking-queues','Bounded work queues')],subject='java-projects')

put('http-project','Java HTTP client project: a real local response and status-aware handling',
'An HTTP client needs separate rules for transport failure, HTTP status, response decoding and the application value carried by a successful body.',
[('Test a response, not just a request builder',[
'This project starts a loopback-only server on an operating-system selected port, sends a GET request with the Java HTTP client and checks both a success response and a missing route. It makes no request to an external domain.',
'The request has a timeout and the client has a connect timeout. Redirects are disabled. A response with status 404 is still an HTTP response; it is not the same as an exception caused by connection failure. Only a success body should be interpreted as a quote value under the application grammar.',
'The server returns a fixed UTF-8 body and content type. The sample reads that small body as a String. An untrusted service can send a much larger body, so a production client needs a response-size limit during consumption rather than after allocating the complete String.'
]),('Choose retry semantics before adding retries',[
'Repeating a GET can be reasonable under the service contract, but retrying a state-changing request can duplicate an operation that already committed. Set an overall budget, classify failures and use the server’s idempotency contract rather than treating every timeout as evidence that nothing happened.'
])],r'''import com.sun.net.httpserver.HttpServer;
import java.net.*;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.concurrent.*;
public class LocalQuoteHttpProject {
    public static void main(String[] args) throws Exception {
        HttpServer server=HttpServer.create(new InetSocketAddress(InetAddress.getLoopbackAddress(),0),0);
        ExecutorService workers=Executors.newSingleThreadExecutor();server.setExecutor(workers);
        server.createContext("/quote",exchange->{
            byte[] body="quote=150".getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().set("Content-Type","text/plain; charset=utf-8");
            exchange.sendResponseHeaders(200,body.length);
            try(java.io.OutputStream output=exchange.getResponseBody()){output.write(body);}
            finally{exchange.close();}
        });
        server.start();
        try{
            String host=server.getAddress().getAddress().getHostAddress();int port=server.getAddress().getPort();
            HttpClient client=HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(2)).followRedirects(HttpClient.Redirect.NEVER).build();
            URI quote=new URI("http",null,host,port,"/quote",null,null);
            HttpRequest request=HttpRequest.newBuilder(quote).timeout(Duration.ofSeconds(2)).GET().build();
            HttpResponse<String> response=client.send(request,HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
            System.out.println(response.statusCode()+":"+response.body());
            URI missing=new URI("http",null,host,port,"/missing",null,null);
            System.out.println(client.send(HttpRequest.newBuilder(missing).timeout(Duration.ofSeconds(2)).build(),HttpResponse.BodyHandlers.discarding()).statusCode());
        }finally{
            server.stop(0);workers.shutdownNow();
            if(!workers.awaitTermination(2,TimeUnit.SECONDS))throw new IllegalStateException("HTTP workers retained");
        }
    }
}''','200:quote=150\n404',
['Request and response costs depend on the body sizes, peer behavior and network. This fixture tests local correctness and does not measure external latency or TLS behavior. For n body bytes, String body handling uses O(n) storage. Both the server and its owned worker pool are stopped in cleanup.'],
['A 404 response is not a transport exception.','A request timeout does not prove a remote side effect was undone.','String body handling alone does not bound untrusted response size.'],[('http-client','Client configuration'),('socket-boundaries','Transport framing')],subject='java-projects',release=11)

put('database-project','Java database project: one receipt and its aggregate in one transaction',
'A receipt repository can update a detail row and its aggregate in the same transaction so a failed detail insert does not increment the published total.',
[('State the invariant and rejection path',[
'The invariant is that the aggregate quantity equals the sum of accepted receipt quantities. Each receipt identifier is unique. Reusing an identifier is a rejected write, not a second accepted receipt with a different quantity.',
'The store method requires a manual-transaction connection owned by this project. It inserts the receipt, updates the aggregate and commits both changes. On a database failure it attempts rollback, attaches a rollback failure if one occurs, and propagates the original failure.',
'The demo uses H2 2.3.232 and in-memory tables. It verifies a duplicate rejection and the persisted total within that connection. A deployed repository also needs migrations, pool reset rules, isolation choices, durable storage and tests against its production engine.'
]),('Keep bound values out of SQL structure',[
'The identifier and quantity are parameters. Statement structure is fixed, and the aggregate row is a known schema object. Validate the application quantity before touching the connection so an invalid quantity cannot leave partial database work.'
])],r'''import java.sql.*;
public class ReceiptDatabaseProject {
    static void store(Connection connection,String id,int quantity) throws SQLException {
        if(id==null||id.isEmpty()||quantity<=0)throw new IllegalArgumentException("Invalid receipt");
        if(connection.getAutoCommit())throw new IllegalArgumentException("Manual transaction required");
        try{
            try(PreparedStatement detail=connection.prepareStatement("INSERT INTO receipts(id,quantity) VALUES(?,?)")){
                detail.setString(1,id);detail.setInt(2,quantity);detail.executeUpdate();
            }
            try(PreparedStatement total=connection.prepareStatement("UPDATE totals SET quantity=quantity+? WHERE id=1")){
                total.setInt(1,quantity);if(total.executeUpdate()!=1)throw new SQLException("Aggregate row missing");
            }
            connection.commit();
        }catch(SQLException failure){
            try{connection.rollback();}catch(SQLException rollback){failure.addSuppressed(rollback);}
            throw failure;
        }
    }
    public static void main(String[] args) throws Exception {
        try(Connection connection=DriverManager.getConnection("jdbc:h2:mem:receipt_project")){
            try(Statement schema=connection.createStatement()){
                schema.execute("CREATE TABLE receipts(id VARCHAR(80) PRIMARY KEY,quantity INT CHECK(quantity>0))");
                schema.execute("CREATE TABLE totals(id INT PRIMARY KEY,quantity INT)");
                schema.execute("INSERT INTO totals VALUES(1,0)");
            }
            connection.setAutoCommit(false);store(connection,"R-81",7);
            try{store(connection,"R-81",5);}catch(SQLIntegrityConstraintViolationException duplicate){System.out.println("Duplicate rejected");}
            try(Statement query=connection.createStatement();ResultSet total=query.executeQuery("SELECT quantity FROM totals WHERE id=1")){
                total.next();System.out.println("total="+total.getInt(1));
            }
            try(Statement query=connection.createStatement();ResultSet rows=query.executeQuery("SELECT COUNT(*) FROM receipts")){
                rows.next();System.out.println("rows="+rows.getInt(1));
            }
        }
    }
}''','Duplicate rejected\ntotal=7\nrows=1',
['The insert is supported by a primary-key index. Aggregate update cost and contention depend on the database; one aggregate row can become a serialization point under heavy writes. An in-memory H2 fixture proves neither production isolation nor crash recovery. A failed rollback means the connection must not be reused as if its state were known.'],
['Do not increment the aggregate after a rejected insert.','A manual transaction can accidentally include unrelated caller work if ownership is unclear.','Do not treat H2 success as certification of another database engine.'],[('jdbc-transactions','Commit and rollback'),('jdbc-interview','Transaction review questions')],subject='java-projects',dependency='h2')

put('streams-reference','Java stream reference: grouping, ordering and empty-result contracts',
'A stream terminal operation defines the returned result, while the source and intermediate operations define which elements can contribute to it.',
[('Choose the terminal result explicitly',[
'Use collect for a result container with a defined accumulation policy. Use a reduction when an associative combining rule and neutral identity describe the result. Use an optional result when an empty source has no selected value; do not silently replace absence with a meaningful business number.',
'The program groups first-seen statuses in a LinkedHashMap and counts their occurrences. The merge function makes duplicate-key behavior explicit. Without a merging rule, toMap can reject duplicate keys instead of returning a count.',
'Preserving first-seen output order is a requirement of this sequential collector and supplied map. It is not proof that every parallel grouping or source has the same order. If consumers need a sorted report, choose a sorted key order or sort the finished entries.'
]),('Review before publishing a pipeline',[
'Check source size, short-circuit behavior, operation state, exceptions, ownership of collected elements and the empty case. intermediate callbacks should not carry required external side effects. Closing a stream can matter when it owns a file or another resource, even though an ordinary list stream usually owns no such handle.'
])],r'''import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;
public class StatusGroupingReference {
    public static void main(String[] args){
        Map<String,Long> counts=Arrays.asList("paid","pending","paid").stream()
            .collect(Collectors.toMap(Function.identity(),status->1L,Long::sum,LinkedHashMap::new));
        System.out.println(counts);
        System.out.println(Collections.<Integer>emptyList().stream().max(Integer::compare).isPresent());
    }
}''','{paid=2, pending=1}\nfalse',
['The grouping visits n statuses and stores k distinct keys. Hash-based insertion is typically constant expected work per status, while string hashing still reads characters. This is an in-memory result, not a streaming output with bounded key cardinality.'],
['A duplicate-key policy must be chosen for toMap.','An empty maximum is absence, not automatically zero.','A file-backed stream needs an owning close scope.'],[('streams','Stream pipelines'),('streams-interview','Pipeline review questions')],subject='java-cheatsheet')

put('concurrency-reference','Java concurrency reference: admission, visibility, atomicity and completion',
'Concurrency design needs separate answers for how work is admitted, how state is shared, how an update is made indivisible and how completion is observed.',
[('Match the mechanism to the invariant',[
'A lock protects a compound transition when every participating caller follows the same lock policy. An atomic variable supplies particular indivisible operations on that variable. Volatile supplies visibility and ordering for a field; it does not supply a multi-field transaction.',
'A semaphore controls permit admission. A blocking queue carries work with a chosen capacity and waiting contract. A future reports a task result, while a timed get bounds a wait rather than automatically cancelling the task. None of these objects provides durable execution after process loss.',
'The small probe observes a completed worker through Future.get. It then rejects a submission after the owner shuts the executor down. The task result and the admission failure are different outcomes and should have different handling paths.'
]),('Use an ownership checklist',[
'Identify the creator and closer of every pool, the maximum pending work, the deadline and cancellation policy, the shared-state invariant and the behavior when shutdown races with submission. A concurrency class name cannot fill in those application decisions.'
])],r'''import java.util.concurrent.*;
public class WorkerLifecycleReference {
    public static void main(String[] args) throws Exception {
        ExecutorService owner=Executors.newSingleThreadExecutor();
        try{
            Future<Integer> task=owner.submit(()->42);
            System.out.println("result="+task.get(2,TimeUnit.SECONDS));
            owner.shutdown();
            try{owner.submit(()->43);}catch(RejectedExecutionException rejected){System.out.println("Admission closed");}
        }finally{
            owner.shutdownNow();
            if(!owner.awaitTermination(2,TimeUnit.SECONDS))throw new IllegalStateException("Owner did not close");
        }
    }
}''','result=42\nAdmission closed',
['One task is admitted and one rejection is exercised. This fixed fixture has constant-sized application state. General pool memory scales with retained queued inputs and active task state; worker count alone does not give that memory bound.'],
['Visibility is not compound atomicity.','Successful submission is not successful completion.','A pool shutdown is not remote rollback.'],[('conditions','Protected predicates'),('cancellation','Cooperative stopping')],subject='java-cheatsheet')

put('file-exercises','Java file exercises: UTF-8 round trips, missing files and cleanup',
'A file round-trip exercise verifies decoded content, failure behavior and owned-file cleanup as separate outcomes.',
[('Check values rather than a success message',[
'Write two titles as UTF-8, read them back using the same charset and compare the complete ordered result. Merely checking that a file exists can pass after writing the wrong content or an empty file.',
'The second case attempts to read a missing file and must fail. The third removes the written file and verifies absence. The exercise owns its temporary directory, so cleanup cannot accidentally delete a user’s unrelated working files.',
'Files.readAllLines is reasonable for these two short fixture records, but it materializes the input. A large import needs a streaming parser with byte, line and record-count budgets. Encoding, record grammar and I/O failure are separate validation layers.'
])],r'''import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
public class FileRoundTripExercises {
    public static void main(String[] args) throws Exception {
        Path directory=Files.createTempDirectory("aitrove-file-check-");Path file=directory.resolve("titles.txt");
        try{
            List<String> expected=Arrays.asList("Caf\u00e9 notes","Parcel handbook");
            Files.write(file,expected,StandardCharsets.UTF_8);
            if(!Files.readAllLines(file,StandardCharsets.UTF_8).equals(expected))throw new AssertionError("Round trip changed");
            try{Files.readAllLines(directory.resolve("missing.txt"),StandardCharsets.UTF_8);throw new AssertionError("Missing file accepted");}
            catch(IOException rejected){ }
            Files.delete(file);if(Files.exists(file))throw new AssertionError("File retained");
            System.out.println("3 file checks passed");
        }finally{Files.deleteIfExists(file);Files.deleteIfExists(directory);}
    }
}''','3 file checks passed',
['The round trip visits the encoded bytes and keeps the decoded lines in memory. Its test data is fixed and small. This is not a crash-recovery, concurrent-writer or permission-boundary test; those scenarios require separate fixtures and explicit ownership decisions.'],
['File existence is not content equality.','Use the intended charset on both boundaries.','Do not clean a directory the test does not exclusively own.'],[('files','File resource boundaries'),('reading-list-project','Persisted membership')],subject='java-exercises')

put('jdbc-reference','Java JDBC reference: parameters, resources and transaction ownership',
'PreparedStatement binds data values to an existing SQL structure; connection ownership determines who may commit, roll back and close the surrounding work.',
[('Choose an owner before issuing a statement',[
'A repository borrowing a connection from a larger unit of work should not independently commit that caller’s transaction. A project that exclusively owns the connection can define its own commit boundary. Document which model a method requires.',
'Close result sets and statements at the scope that consumes them. A returned lazy iterator over a ResultSet also returns a resource lifetime problem; it needs a close contract and error handling after the calling method returns.',
'The parameter probe sends a quote-containing string as one value to H2. No concatenation changes the SQL text. Parameter markers ordinarily cannot replace a table or column identifier, so user-selected identifiers require a separately validated query choice.'
]),('Review failed work explicitly',[
'On an update, check the affected-row count when the invariant expects exactly one row. On an exception, preserve both the primary error and rollback errors. Do not send a failed connection back to a pool with an assumption that its transaction state is healthy.'
])],r'''import java.sql.*;
public class BoundValueReference {
    public static void main(String[] args) throws Exception {
        try(Connection connection=DriverManager.getConnection("jdbc:h2:mem:parameter_reference");
            PreparedStatement query=connection.prepareStatement("SELECT ?")){
            query.setString(1,"customer'42");
            try(ResultSet result=query.executeQuery()){
                result.next();System.out.println(result.getString(1));
            }
        }
    }
}''',"customer'42",
['This probe checks one bound value with H2 2.3.232. It does not measure query preparation or pool throughput. General result consumption costs depend on the number and size of rows, network transfer and driver buffering.'],
['Do not concatenate values into SQL.','Parameter binding does not select arbitrary identifiers safely.','A helper must not commit a transaction owned by its caller.'],[('jdbc-prepared','Prepared statements'),('database-project','Transactional repository')],subject='java-cheatsheet',dependency='h2')

# Deepen the earlier brief foundation and LinkedList pages without replacing their programs.
expansions={
'setup':('Separate toolchain failures from program failures',[
'Check both java -version and javac -version before investigating a program. A machine can launch one installed runtime while its compiler comes from another installation. Keep the compiler release target separate from the compiler installation; javac --release 8 on a newer JDK checks the stated platform API and language boundary.',
'Compile into a dedicated output directory, then give that directory to the class path. Launch a packaged class by its full binary name, not by a source-file pathname. A missing class and an exception thrown from main occur at different stages; preserving the actual error makes that distinction visible.',
'The small program verifies compilation and launch. It does not validate an IDE’s test configuration, a dependency resolver or deployment packaging. Once the command-line build works, reproduce the same source roots, release target and runtime selection in the IDE.'
]),
'variables-types':('Choose the representation for the allowed values',[
'A quantity that can never be fractional should not become double merely because a parser accepted a decimal token. Integral ranges, overflow behavior and nullability belong to the field contract. A primitive has no null sentinel; an Integer may be absent and can fail during unboxing.',
'Local variables need a definitely assigned value before reading. Fields have initialization defaults, but a default zero is not evidence that a business value was supplied. Model missing input explicitly at the parsing boundary rather than allowing field defaults to stand in for validation.',
'Assignments to reference variables copy references. They do not duplicate a list, an array or its nested members. Declare which component owns mutation and test changes through a second alias before describing a value as a snapshot. final prevents reassignment of that variable; it does not freeze a referenced array.'
]),
'operators':('Evaluate types before trusting the final value',[
'Two int operands produce int arithmetic unless a conversion changes the operand types first. A long destination does not fix an overflow inside an earlier int addition. Use a widened operand or checked arithmetic when a rejected overflow is the business rule.',
'Integer division discards the fractional part toward zero. Floating-point division introduces its own rounding and special values; it is not an automatic substitute for decimal money. BigDecimal arithmetic still needs a declared scale and rounding policy at the operation boundary.',
'Short-circuit boolean operators can skip the right operand. That is useful for a null check followed by a dereference, but it also means a right-hand side effect might never happen. Keep required state changes out of boolean conditions, and parenthesize a compound business rule when precedence could hide its intent.'
]),
'control-flow':('State the loop invariant and exit condition',[
'A loop should keep a condition true after every completed iteration: a processed prefix is valid, a remaining counter is non-negative, or the current search interval contains every possible answer. Naming that condition gives the update and exit test something concrete to preserve.',
'A continue can skip an update when the update lives in the body. A rejected input can therefore repeat forever if the loop retries without consuming it. A break exits only its defined loop or switch scope, so nested search code needs an explicit result boundary rather than assuming every break leaves the method.',
'Test the zero-iteration case and the final legal iteration. For an array, the final valid position is length minus one. For a half-open search range, the upper boundary is excluded. Switching between these conventions halfway through a method is a common source of missed values or out-of-bounds access.'
]),
'arrays':('Distinguish membership copies from nested copies',[
'An array has fixed membership length and mutable slots. Assigning it to another variable shares those slots. clone makes another outer array, but a nested array or mutable element can still be shared. Decide whether callers need independent rows or merely independent outer membership.',
'Java multidimensional arrays are arrays of arrays. Rows can have different lengths and can be null. A loop using the first row’s length for every row invents a rectangular-shape contract that the representation itself does not guarantee.',
'Bounds checks protect access at runtime but do not make an off-by-one algorithm correct. Test empty input, one element and the final position. A copied snapshot also adds allocation and O(n) element-reference work; it should appear in the method’s space cost rather than vanish behind the word copy.'
]),
'strings':('Define equality, positions and encoding separately',[
'String.equals compares the represented character sequence; == compares whether two references point to the same object. Interning can make some reference comparisons appear to work until input comes from a parser or another allocation. Use the value contract directly.',
'String positions are UTF-16 code-unit positions. A supplementary code point can occupy two units, and several code points can form one displayed unit. A UI character limit and a protocol byte limit therefore need different measurements. Use an explicit charset when moving text across a byte boundary.',
'The String object does not change when concatenation returns another String. Repeated accumulation in a loop can create substantial copying and temporary objects; a builder makes the intended mutable assembly phase explicit. That optimization does not decide whether the final value needs normalization or a language-specific comparison rule.'
]),
'classes-objects':('Make object state valid at publication',[
'A constructor should establish the invariant that every permitted public operation can rely on. A stock object with a negative available count is already invalid before reserve is called. Reject that input rather than requiring every future operation to repair it.',
'An object can be referenced by several components. Returning its mutable internal list gives callers another mutation path around the class’s validation. Publish a copied or explicitly read-only view according to the required lifetime; a read-only live view still changes when the owner changes its backing state.',
'Instance fields belong to a particular object, while static fields belong to the loaded class. Moving state to static can accidentally merge independent accounts or requests. It also adds a shared lifetime and coordination requirement that did not exist when each request owned its own object.'
]),
'constructors':('Validate before the object escapes',[
'Constructor chaining should lead to one place that establishes the state contract. Duplicated validation in several overloads can drift until one constructor permits a state another rejects. A factory can name distinct creation policies without making callers guess which positional argument combination applies.',
'Avoid registering this with an external listener or starting a worker while construction is still in progress. Another component can then observe fields before the invariant is established. Finish creation, then let an explicit owner publish the object or start its resources.',
'Construction can allocate more than the outer object: copied collections, parsed metadata and acquired resources all contribute cost. If the constructor can fail after acquiring a resource, cleanup needs an explicit scope. A simple immutable value constructor should not quietly own a long-lived connection or executor.'
]),
'encapsulation':('Protect every mutation route',[
'Private fields are only one part of encapsulation. A public setter, returned array, live collection view or callback can still permit callers to bypass the intended invariant. Review the whole public surface and every alias it publishes.',
'Expose an operation such as reserve(quantity) when the rule spans available and reserved counts. Two unrelated setters make the caller responsible for preserving a relation it cannot update atomically. Validate before changing either field and specify the unchanged state on rejection.',
'An unmodifiable wrapper prevents updates through that wrapper but can still reflect owner updates and expose mutable elements. Independent snapshots need a copy at the correct layer. If multiple workers share the object, the class also needs one stated synchronization rule for reads and compound writes.'
]),
'inheritance':('Preserve the parent contract',[
'An override must keep the behavior callers of the parent type are entitled to use. Narrowing an accepted input range or introducing an unrelated failure can break a caller that never names the subtype. Choose inheritance for substitutable behavior, not merely for reusing a few implementation lines.',
'Instance-method dispatch uses the actual object type after overload selection has chosen a method signature. Static methods and fields do not follow that same dispatch rule. Inspect the declared receiver and argument types before explaining an overloaded call trace.',
'A base constructor that invokes an overridable method can call subtype code before subtype initialization is complete. Keep construction-time invariant setup away from that virtual dispatch. Composition often makes resource ownership and independent policy changes easier to represent than a deep inheritance chain.'
]),
'interfaces':('Describe behavior without promising an implementation',[
'An interface names the operations and behavior a caller can require. List and Deque expose different permitted actions even when LinkedList implements both. Choose the narrower contract that actually represents the caller’s requirement rather than publishing every available method.',
'A default method can share behavior but does not automatically add object state or resolve every multiple-interface conflict. A class combining conflicting defaults must choose an implementation explicitly. Static interface methods also do not become ordinary virtual instance methods.',
'Thread safety, ownership and cost still depend on the chosen implementation and its documented contract. Accepting a List parameter does not imply constant-time indexing, immutable membership or safe concurrent traversal. If an algorithm needs one of those properties, state it or change the representation.'
]),
'collection-choices':('Choose an operation and a lifetime',[
'Write the access pattern before naming a collection: endpoint queue, keyed membership, sorted nearest-key lookup or indexed editing. A container that performs one of those well can perform another poorly. Indexed traversal of a linked list can revisit the same chain for every position.',
'Then define lifetime and ownership. A copied membership snapshot differs from a backed view; both can still share mutable values. An immutable factory can reject nulls that an older caller previously stored, so migration needs data validation rather than a class-name swap.',
'Finally define concurrency and admission. A concurrent map does not bound distinct keys, and a fixed thread pool does not bound pending tasks. A service queue may need capacity, rejection, interruption and shutdown policies in addition to a FIFO order. None of these Java containers promises durable delivery after process loss.'
]),
'linkedlist-exercises':('Add boundary cases that distinguish the overloads',[
'Repeat value removal with a target that is absent and require false without changing membership. Test equal duplicates so the answer proves that only the first matching value is removed. For position removal, test zero, the last valid index and an index equal to size; these cases use a different contract.',
'For iterator cleanup, put completed jobs at the first and last positions as well as next to each other. A loop that advances twice after removal can skip adjacent matches. Keep the removal on the same iterator that supplied the current element.',
'A null member can make a polling result ambiguous with an empty queue. Use a non-null element policy for a task queue, and test the policy before insertion. These checks run as a local Java program; they do not describe an online judge or synchronized queue.'
]),
'linkedlist-interview':('Follow up on the representation choice',[
'Ask what the caller already knows at insertion time. An already-positioned iterator avoids a fresh position search, but a caller holding only a numeric index may need to traverse. A claim about link-editing cost should identify that precondition rather than call every insertion constant time.',
'Ask whether a shallow copy isolates a mutable element. It does not. The copied node sequence holds the same referenced elements, so a field change on one shared element can be seen through both lists. Snapshot membership and element ownership are separate answers.',
'Ask how to stop a worker waiting for task admission and what survives restart. Neither LinkedList nor ArrayDeque supplies a blocking wait or durable retry record. Changing an implementation without adding those contracts does not create a production service queue.'
]),
'linkedlist-examples':('Read the operation order as a state trace',[
'Write the list after each mutation before checking the final print. addFirst and addLast place values at different ends, and pollFirst removes the value that currently occupies the head. Duplicate descriptions remain separate elements because this example has no identity or deduplication rule.',
'The ListIterator editor first searches for a matching stage. Once positioned, add inserts relative to that cursor. Locating the stage can visit the whole list, so the program’s total cost includes search even though changing the nearby links requires constant work.',
'Compare a missing stage and an empty list with the printed success case. Neither should create a quality-check stage at a guessed position unless that fallback is part of the contract. A null stage also needs a stated input policy; invoking a method on a null member will not be repaired by using a linked representation.'
]),
'linkedlist-cheatsheet':('Remember which result means absence',[
'pollFirst and peekFirst return null for an empty list, while removeFirst and getFirst reject that empty state with an exception. An actual null element makes a null result ambiguous, so an application queue can choose to reject null elements even though LinkedList permits them.',
'remove(int) returns the removed element at that position. remove(Object) returns whether a first equal value was found and removed. An Integer argument can select different behavior depending on whether the call supplies a primitive int or an explicitly boxed value; read the argument type before explaining the result.',
'Iterator traversal follows links once. Repeated get(i) asks for a new location search on each call. A shallow copy also traverses values to build another membership structure without cloning arbitrary elements. Do not treat fail-fast exceptions as an access-coordination mechanism.'
]),
'linkedlist-quiz-guide':('Trace state and cost as different answers',[
'A correct final list does not automatically supply a correct complexity answer. Separate finding a position, changing adjacent links and rendering a report. A method that accepts an index can spend time locating it before doing a small link update.',
'For overload questions, write the argument’s declared type before inspecting the list values. For empty-case questions, read whether the method returns a sentinel or throws. For copy questions, draw the element references shared by the two membership structures.',
'After a wrong answer, run a minimal checked trace and explain why the other branch would require a different method or precondition. The quiz results remain in this browser; the page does not claim a server-issued qualification or a remotely judged code submission.'
]),
'quiz-preparation':('Review decisions rather than memorize output strings',[
'For a value question, identify primitive versus reference representation, evaluation order, conversion and the exact operation. For an object question, draw which references share the same mutable state. For a collection question, name the implementation as well as the interface.',
'For a concurrency question, separate admission, visibility, atomic transition and completion. A volatile read, successful submit or cancelled future does not answer every one of those questions. Read the failure and shutdown clauses before choosing an option.',
'The Java quiz hub groups foundation, object, collection, generic, stream, thread, I/O and algorithm checks. Each result is a local self-check. Review its explanation and return to the linked lesson before retrying; a correct multiple-choice answer alone does not verify that a complete program meets the same contract.'
])}
for slug,(heading,texts) in expansions.items():
 e=lookup['java/'+slug]
 e['body']+='<h2>'+html.escape(heading)+'</h2>'+''.join(p(t) for t in texts)
 e['updated_at']='2026-09-29T07:00:00+00:00';e['data']['reading_minutes']=max(4,round(len(re.sub('<[^>]+>',' ',e['body']).split())/150))
 expanded.append(e['path'])
# Replace imperative/stub opening definitions while preserving programs.
for slug,definition in {
 'setup':'A Java toolchain compiles source with javac and runs bytecode with a compatible Java runtime.',
 'quiz-preparation':'A Java self-check evaluates a specific operation contract, type rule or failure boundary through questions with explanations.'
}.items():
 e=lookup['java/'+slug];e['body']=re.sub(r'^<p>[\s\S]*?</p>',p(definition),e['body'],count=1);e['summary']=definition

def question(prompt,correct,wrong1,wrong2,explanation,index):
 options=[correct,wrong1,wrong2]; shift=index%3
 options=options[shift:]+options[:shift]
 return {'prompt':prompt,'options':options,'answer':options.index(correct),'explanation':explanation}
def bank(slug,title,rows):
 path='quizzes/java-'+slug
 e=copy.deepcopy(lookup['quizzes/java-collections'])
 e.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),path=path,title=title,summary='Check '+title.lower().replace(' quiz','')+' through contract questions and explained answers.',body=p('This self-check tests operation contracts, state ownership and failure boundaries. Results remain in this browser; no code is submitted to a server.'),tags=['java',slug],updated_at='2026-09-29T07:00:00+00:00',sort_order=10+len(banks))
 e['data']=dict(content_format='html',subject_root='java/java',section_path='java/java-quizzes',duration_minutes=18,questions=[question(*row,i) for i,row in enumerate(rows)])
 if path in lookup: lookup[path].update(e)
 else: entries.append(e);lookup[path]=e
 banks.append(path)

bank('oop','Java objects and ownership quiz',[
('A method reassigns its reference parameter. What happens to the caller’s variable?','It still holds its original reference','It is reassigned too','Its object is cloned','The parameter receives a copy of the reference value; assigning that local copy does not assign the caller’s variable.'),
('What does final prevent for a field referring to an array?','Reassigning the field after its permitted initialization','Changing every array element','Sharing the array reference','The reference field cannot be reassigned, but the referenced array can still be mutable.'),
('An object returns its internal mutable list. Which boundary is lost?','The owner’s exclusive mutation path','The ability to call methods','The list’s element order','A caller can edit that returned list without passing through the owner’s validation methods.'),
('A base constructor calls an overridable method. Which state can that method observe?','Subtype fields before subtype initialization completes','Only a fully initialized subtype','No object state','Virtual dispatch can reach subtype code while the base constructor is still running.'),
('Which operation receives runtime instance-method dispatch?','An overridden instance method','A static method hidden by another static method','A field with the same name in a subtype','Instance-method overrides use the actual receiver type; static methods and fields follow other selection rules.'),
('Two interface defaults conflict. What must the implementing class do?','Resolve the conflict explicitly','Use whichever interface appears first','Ignore both defaults automatically','The class must supply an implementation that resolves incompatible inherited defaults.'),
('What should a rejected reservation leave unchanged?','Every field participating in the reservation invariant','Only the public counter','Nothing; partial writes are unavoidable','A method promising rejection without mutation must validate before applying its compound state update.'),
('Does an unmodifiable outer list prevent mutation of an element object?','No','Yes, recursively','Only if the list is short','The wrapper constrains list operations, not arbitrary mutation of referenced objects.'),
('A record holds int[] counts with no copying. Is it deeply immutable?','No','Yes','Only on Java 21','The component reference can be final while the array contents remain mutable and exposed.'),
('Which check tests title membership by value?','String.equals','Reference ==','StringBuilder capacity','String.equals checks its represented value; reference equality can be accidentally true for interned values.'),
('A subtype rejects a previously valid parent input. What needs review?','Substitutability of the parent contract','Only its class name','Only its constructor count','A caller using the parent type is entitled to the parent’s accepted behavior.'),
('What does an outer-array clone do for nested arrays?','Copies outer membership but shares referenced rows','Deep-copies every row','Makes all rows read-only','Array clone copies outer slots; the row objects need their own ownership decision.')])

bank('generics','Java generics and call boundaries quiz',[
('Can List<Integer> be assigned to List<Number>?','No','Yes, always','Only when empty','Generic list declarations are invariant; permitting the assignment would allow incompatible values to be inserted.'),
('What can be read from List<? extends Number> without a cast?','Number','Integer specifically','Any chosen numeric subtype','The bound supplies a readable Number contract without identifying the concrete captured subtype.'),
('What is generally safe to add to List<? super Integer>?','An Integer value','A Double value','An arbitrary Object value','The list accepts Integer or its subtypes under the lower-bound contract; reads have only the general Object type.'),
('Does a readable wildcard freeze list membership through other aliases?','No','Yes','Only for Number lists','Variance constrains this source-level reference; it does not change the object’s ownership or mutability.'),
('Why is new T[10] unavailable for an ordinary erased type parameter?','The runtime array element type is not generally available','Ten is an invalid size','Arrays are always immutable','Java arrays check their runtime component type, while the erased type parameter does not generally supply that type.'),
('What can raw-list insertion cause at a later typed read?','ClassCastException','Automatic conversion to the type argument','A guaranteed compiler error at runtime','Unchecked code can pollute a generic structure, leaving a cast failure when a typed consumer retrieves the value.'),
('Overloaded calls are selected using what initial information?','Declared receiver and argument types','Only the object’s runtime subtype','The method’s printed output','Compile-time overload selection precedes runtime dispatch of an applicable overridden instance method.'),
('For List<Integer>, which call explicitly removes the first value 2?','remove(Integer.valueOf(2))','remove(2)','get(2)','The boxed argument selects the value-removal overload rather than the index-removal overload.'),
('What is the result of narrowing the int value 260 to byte?','4','260','An automatic ArithmeticException','The narrowing conversion retains the low-order bits; it does not enforce the original numeric range.'),
('Where should widening occur to avoid an int addition overflowing?','On an operand before the addition','Only on the assigned result','On the variable name','The operand types determine the arithmetic operation before the destination assignment occurs.'),
('Does a reference cast create a second object?','No','Yes','Only when successful','A reference cast checks type compatibility; it does not copy or convert the referenced object’s fields.'),
('What is null unboxing into int?','A NullPointerException','Zero','A compiler-generated missing-value flag','Unboxing calls the wrapper’s value conversion; a null wrapper cannot supply that value.')])

bank('streams','Java stream contracts quiz',[
('Creating map/filter operations ordinarily starts traversal when?','When a terminal operation demands it','At every intermediate call','Only after the stream is cloned','Intermediate operations describe a lazy computation; a terminal operation supplies demand.'),
('Can a stream be used for two separate terminal operations?','No; obtain a fresh stream','Yes; the second result is cached','Only if the first result is empty','A stream is a one-use pipeline; its collection source can usually supply a new pipeline.'),
('Must a mapping callback run for every element during count?','No, the terminal may avoid unnecessary work','Yes, for required side effects','Only when the mapper returns int','An implementation can exploit known sizing when the mapping does not affect the requested count.'),
('What does toMap need when two elements produce the same key?','A duplicate-key decision such as a merge function','An automatic last-value guarantee','A LinkedList source','The collector must resolve duplicates under an explicit policy or can reject the duplicate mapping.'),
('A maximum over an empty integer stream returns which ordinary result type?','An absent optional result','A guaranteed zero value','The smallest source value','There is no selected element; optional results represent that absence without inventing a value.'),
('Which identity is neutral for integer sum?','0','1','The number of partitions','A sum identity must leave a combined sum unchanged; a non-neutral value can be applied separately to partitions.'),
('Does parallel execution make a captured ArrayList safe for concurrent additions?','No','Yes','Only with forEach','A parallel pipeline does not change the thread-safety contract of external mutable storage.'),
('Does a preserved encounter-order result imply callbacks ran in that order?','No','Yes','Only for Strings','Execution order and the ordering of the final result are separate guarantees.'),
('What happens to mutable elements collected into a new list?','Their references can still be shared','They are deep-cloned automatically','They become record instances','Collection membership can be new without changing the ownership of the referenced element objects.'),
('When does a file-backed stream need a close owner?','Across the scope consuming that resource-backed stream','Only when it is empty','Never','Resource-backed sources can hold handles after stream creation and need an owning cleanup scope.'),
('Why is associativity required for a parallel combining rule?','Partition grouping must not change the required result','It guarantees a fixed thread count','It makes any side effect safe','Parallel reduction can group partial results differently; the combining rule must tolerate that grouping under its stated semantics.'),
('What storage grows during grouping by many distinct keys?','The result’s key membership','Only one counter regardless of keys','No storage at all','Grouping materializes state per distinct key unless a different bounded aggregation policy is defined.')])

bank('concurrency','Java concurrency and completion quiz',[
('Does volatile make count++ atomic?','No','Yes','Only with two threads','The read, addition and write are still a compound sequence; visibility does not make that sequence indivisible.'),
('What does timed Future.get bound?','The caller’s wait','All execution of the worker','The lifetime of the process','A timed wait can end while the task continues unless another stopping policy is applied.'),
('Does cancel(true) prove the worker has already released all resources?','No','Yes','Only when isCancelled is true','Cancellation requests interruption; an independent completion or exit observation is needed for cleanup.'),
('What must follow a failed Semaphore.tryAcquire?','No release for that rejected attempt','Release anyway','Double the permit count','Releasing an unacquired permit expands the accounted capacity.'),
('Why is a condition predicate checked in a loop?','Wakeups and competing consumers require rechecking protected state','signal transfers the item directly','A loop makes the lock optional','A signalled or spuriously awakened thread must reacquire the lock and verify the predicate before consuming state.'),
('Which lock should protect a condition’s predicate update?','The same associated lock used while waiting','Any different lock','No lock if signal is called','The predicate observation and state change must participate in one coordination policy.'),
('Does a fixed worker count bound an ordinary fixed pool’s pending queue?','No','Yes','Only when submit returns a Future','Worker count and pending-work capacity are separate admission limits.'),
('What does successful submit prove?','The task was admitted under that executor’s contract','The task completed successfully','The result is durable','Execution and task failure occur after admission and must be observed separately.'),
('What happens if an exception escapes an ordinary periodic scheduled task?','Later periodic executions can be suppressed','It always retries immediately','The executor must shut the JVM down','The scheduled future exposes the failure; periodic continuation is not automatic after an escaping failure.'),
('Does a concurrent map make check-then-remove a single atomic operation?','No','Yes','Only for String keys','Use a specified conditional operation when a key and expected value form one claim.'),
('What is a CopyOnWriteArrayList iterator’s membership view?','The snapshot array at iterator creation','A guaranteed latest live list','A deep copy of all listeners','The cursor retains the earlier array state while element objects can still be shared.'),
('What does shutdownNow guarantee about uncooperative code?','It does not guarantee forced task termination','It kills every worker immediately','It rolls back all remote effects','Interruption requests and returned pending tasks still require a cooperative cleanup policy.')])

bank('io','Java input, files and network quiz',[
('After nextInt, why can nextLine return an empty remainder?','The current line ending has not been consumed as another record','The file must be corrupt','Scanner changed the charset','Token parsing and whole-line parsing consume different boundaries.'),
('What unit does String.length count?','UTF-16 code units','UTF-8 bytes','Displayed graphemes','A supplementary code point can occupy two UTF-16 units and multiple code points can form one displayed unit.'),
('What does NFC normalization address?','Canonical sequence equivalence under the selected normal form','Every spoofed identifier','SQL escaping','Normalization has a text-equivalence purpose and is not a universal sanitization or security policy.'),
('Which Matcher operation asks for a full-input match?','matches','find','group','find searches for a matching region; matches applies the pattern to the full current region.'),
('When are captured groups ordinarily readable?','After a successful match operation','Before any attempt','After every failed match','A group lookup requires valid match state.'),
('What does ByteBuffer.flip do after writing into a buffer?','Sets the readable limit and resets position','Clears every stored byte','Flushes a file automatically','flip changes buffer state for reading; it is not an I/O flush operation.'),
('Does one file-channel read guarantee a complete header?','No','Yes','Only for int fields','Transfers can be partial; record parsing must verify the required bytes were obtained.'),
('What does TCP preserve?','An ordered byte stream','One application message per read','HTTP status objects','An application framing rule is needed because stream reads do not preserve message boundaries.'),
('Does connect timeout also bound every later socket read?','No','Yes','Only on loopback','Connection establishment and subsequent reads have separate timeout boundaries.'),
('Is an HTTP 404 necessarily a transport exception?','No; it can be a received HTTP response','Yes','Only when redirects are disabled','Status-aware handling is separate from connection or transport failure.'),
('What does readAllLines retain for a large file?','The materialized decoded lines','Only a fixed-size byte chunk','Only the final line','A streaming parser is needed when full materialization would exceed the accepted memory budget.'),
('Does a file move alone certify crash-durable persistence?','No','Yes','Only for UTF-8 text','Durability, atomic replacement capability and concurrent-writer behavior need explicit filesystem and application decisions.')])

bank('algorithms','Java algorithm invariants quiz',[
('What keeps AVL search height logarithmic?','A maintained subtree-height balance invariant','Sorting the final print','A volatile root field','The height difference bound must be restored during updates; sorted input alone does not balance a tree.'),
('Does a trie prefix path prove the prefix is a stored word?','No; a terminal marker is separate','Yes','Only for ASCII','Membership and prefix reachability answer different questions.'),
('Is a binary heap backing array fully sorted?','No','Yes','Only when priorities are equal','The heap invariant orders parents against children; it does not totally sort array positions.'),
('What does KMP fallback reuse?','A proper prefix that matches an already seen suffix','Every earlier text copy','The largest character value','The prefix relation avoids restarting all earlier comparisons after a mismatch.'),
('What does Kruskal return on disconnected input under the forest contract?','A minimum spanning forest','A guaranteed single tree','A shortest path from vertex zero','Disconnected components cannot be joined without edges; the result remains a forest.'),
('Which weights can Kruskal accept for connection cost?','Negative, zero and positive','Only positive','Only unit weights','The cycle constraint and sorted edge selection do not require non-negative link cost.'),
('What invalidates single-source finite distances in Bellman–Ford?','A negative cycle reachable from the source','Any unreachable negative cycle','Every negative edge','Reachable negative cycles permit further distance improvement; an unreachable cycle cannot affect this source’s routes.'),
('Why must Dijkstra’s standard method reject negative edges?','Its settled-distance argument requires non-negative extension costs','PriorityQueue rejects negative ints','All graphs require positive costs','A negative edge can undermine the greedy distance ordering used by the standard algorithm.'),
('What dependency makes ascending quantity tabulation valid?','Every positive pack leads to a smaller quantity','All packs have equal size','The result list is sorted','The recurrence can read already computed smaller states when every transition size is positive.'),
('What does earliest-finish interval selection optimize here?','Maximum unweighted accepted count','Maximum total profit','Minimum waiting time for all jobs','The exchange proof applies to the count objective, not automatically to weighted profit or another schedule objective.'),
('Can an interval beginning at the previous finish be accepted under half-open intervals?','Yes','No','Only if it has zero duration','The previous endpoint is excluded under the stated [start,end) convention.'),
('Why is get(i) for all LinkedList positions potentially quadratic?','Each index can trigger another traversal','Printing Strings is always quadratic','The size method must walk all nodes','Summing repeated position searches can revisit links many times compared with one iterator traversal.')])

# Bring the existing five banks to twelve questions each, preserving their earlier answers.
extra={
'java-basics':[
('What does int division 7 / 2 return?','3','3.5','4','Integer division discards the fractional part toward zero.'),
('Which array position is the last valid one for length n > 0?','n - 1','n','n + 1','The array positions form the half-open range from zero up to length.'),
('What does final StringBuilder prohibit?','Reassigning that variable','Calling append','Reading its length','final concerns reference assignment, not the mutability of the referred object.'),
('What happens when an Integer containing null is used as an int?','NullPointerException','Zero','A missing-value String','Unboxing cannot obtain a primitive value from a null reference.'),
('Which compares two String values?','equals','== in every case','Their variable names','Value comparison must not depend on accidental interning.'),
('What does a for-each assignment to an int loop variable change?','Only the local loop variable','The array slot automatically','Every later slot','The iteration variable receives a value; assigning it does not assign the array member.'),
('What does a failed numeric range check need to preserve?','State before the rejected operation','Only the error message','At least one partial update','A rejection-without-mutation contract needs validation before applying state changes.'),
('What does a short-circuit && skip when its left side is false?','The right expression','The left expression','Both expressions','The right operand is not evaluated when the left false value already determines the result.'),
('Does casting an already-overflowed int result to long repair it?','No','Yes','Only when assigned to final','The int operation happened before the widening conversion.'),
('Can rows of a Java int[][] have different lengths?','Yes','No','Only with reflection','The outer array stores references to row arrays, not one guaranteed rectangular block.')],
'java-linkedlist':[
('What does LinkedList.descendingIterator start with on a nonempty list?','The last element','The first element','A sorted copy','The descending iterator traverses the list from the tail toward the head; it does not sort the values.'),
('Which call reads the last element without removing it and returns null when empty?','peekLast','removeLast','pop','peekLast uses the nullable empty-result contract and leaves membership unchanged.'),
('Does replacing an element with set(index,value) ordinarily add a node?','No','Yes','Only for Strings','It replaces a stored value at the located position rather than adding membership.'),
('Can a ListIterator add after reaching a chosen position without a fresh index search?','Yes','No','Only when the list is empty','The positioned cursor identifies the local link location, though reaching that cursor position still had a cost.'),
('Does fail-fast behavior guarantee detection of every unsynchronized race?','No','Yes','Only with integer members','Detection is best-effort and cannot be the program’s coordination policy.'),
('Why can a null poll result be ambiguous in a LinkedList allowing null?','It can represent an empty result or a removed null value','Null is always forbidden','Poll always throws','The class permits null elements, so applications often choose a stricter queue element policy.')],
'java-collections':[
('What does a reversed sequenced view copy automatically?','It does not imply detached membership storage','Every mutable element','Every referenced object graph','The view reverses encounter order and can share the backing collection.'),
('What does TreeSet use to decide a single ordered membership position?','Comparator equivalence','Only hashCode','Insertion sequence alone','A zero comparison places keys in one sorted-equivalence position.'),
('Does List.copyOf recursively freeze mutable elements?','No','Yes','Only for nested lists','It restricts membership updates, while element objects retain their own mutability.')],
'java-advanced':[
('What occurs when both a try body and resource close fail?','The body failure remains primary and close is suppressed','Close always replaces the body failure','Both failures disappear','Try-with-resources preserves the primary operation failure and records suppressed cleanup failures.'),
('What does a worker’s interrupted blocking wait need?','An explicit cancellation or propagation policy','An unconditional infinite retry','A counter reset','InterruptedException communicates interruption; ignoring it can prevent cooperative shutdown.'),
('Can a local database rollback retract a previously sent external message?','No','Yes','Only with auto-commit disabled','Database transaction scope does not include arbitrary external side effects.')],
'java-modern':[
('Which continuation is required for a direct permitted subclass, explicitly or implicitly?','A final, sealed or non-sealed continuation','Only a public constructor','An automatic runtime proxy','The direct subclass is final, sealed or non-sealed, explicitly or implicitly; a record class is implicitly final.'),
('What do virtual threads fail to remove?','Downstream capacity constraints','All blocking operations','Every need for task state','Concurrency representation does not create more database connections or processors.'),
('Which stated release introduced the sequenced interfaces used here?','Java 21','Java 8','Java 11','The Java 21-labelled examples use the versioned sequenced collection APIs.')]
}
for slug,rows in extra.items():
 e=lookup['quizzes/'+slug];q=e['data']['questions']
 for row in rows:q.append(question(*row,len(q)))
 assert len(q)==12,(slug,len(q))
 e['data']['duration_minutes']=18;e['updated_at']='2026-09-29T07:00:00+00:00';updated_banks.append(e['path'])

put('test-boundaries','Java test boundaries: injected collaborators and behavior-focused checks',
'An injected collaborator lets a test supply a controlled dependency while checking the caller’s validation, result and failure contract.',
[('Replace the dependency, not the assertion',[
'A quote operation needs a supplier amount and adds a fixed fee. The test supplies a deterministic gateway, so it does not depend on network access. A second gateway throws an I/O failure, letting the test verify that failure remains visible to the caller.',
'Another check passes an invalid destination and a gateway that must never be called. That verifies validation occurs before external work. It is a behavior requirement, not an assertion about private helper names or the number of internal methods.',
'This hand-written test double needs no mocking framework. A framework can create doubles for larger APIs, but the meaningful decision is still what behavior the application promises. A stubbed collaborator also does not replace a separate integration test against the real protocol.'
])],r'''import java.io.IOException;
public class QuoteBoundaryChecks {
    interface Gateway{int amount(String destination)throws IOException;}
    static int total(String destination,Gateway gateway)throws IOException{
        if(destination==null||destination.trim().isEmpty())throw new IllegalArgumentException("Missing destination");
        int base=gateway.amount(destination);
        if(base<0)throw new IllegalArgumentException("Negative quote");
        return Math.addExact(base,10);
    }
    public static void main(String[] args)throws Exception{
        if(total("Delhi",destination->90)!=100)throw new AssertionError("Fee changed");
        try{total("",destination->{throw new AssertionError("Invalid request called gateway");});throw new AssertionError("Missing destination accepted");}
        catch(IllegalArgumentException expected){ }
        try{total("Delhi",destination->{throw new IOException("Supplier unavailable");});throw new AssertionError("Failure hidden");}
        catch(IOException expected){ }
        try{total("Delhi",destination->-1);throw new AssertionError("Negative quote accepted");}
        catch(IllegalArgumentException expected){ }
        System.out.println("4 gateway checks passed");
    }
}''','4 gateway checks passed',
['These tests do constant-sized local work; a real gateway contributes I/O, queueing and decoding costs. Controlled doubles isolate application behavior but cannot measure external latency, wire compatibility or the supplier’s own validation. Checked arithmetic preserves the overflow boundary when adding a fee.'],
['A fake success response is not a protocol integration test.','Test doubles should implement the dependency contract the caller actually uses.','Do not make tests pass merely by mirroring the private implementation.'],[('junit-tests','Executable tests'),('http-project','Local HTTP integration')])

put('parameterized-tests','Java parameterized tests: boundary cases without arithmetic overflow',
'A parameterized test applies one stated behavior to several input cases while keeping each failing case identifiable in the runner.',
[('Choose boundaries that distinguish implementations',[
'The packing function returns the number of vehicles needed for a non-negative parcel count and a positive capacity. The common expression (parcels + capacity - 1) / capacity can overflow before division. Division plus a remainder check keeps the valid maximum-int input representable.',
'The valid table includes zero, an exact multiple, one over capacity and Integer.MAX_VALUE. The invalid table verifies negative parcel count and non-positive capacity. Adding many repeated ordinary cases would not distinguish the overflowing formula from this implementation.',
'This sample uses JUnit Jupiter 5.11.0 in the downloadable Maven project. The annotation API requires the matching test dependencies and runner; copying the Java file alone into a plain javac invocation does not make it executable.'
])],r'''import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import static org.junit.jupiter.api.Assertions.*;
public class PackingBoundaryTest {
    static int vehicles(int parcels,int capacity){
        if(parcels<0||capacity<=0)throw new IllegalArgumentException("Invalid packing inputs");
        return parcels/capacity+(parcels%capacity==0?0:1);
    }
    @ParameterizedTest
    @CsvSource({"0,4,0","1,4,1","8,4,2","9,4,3","2147483647,2,1073741824"})
    void validInputs(int parcels,int capacity,int expected){assertEquals(expected,vehicles(parcels,capacity));}
    @ParameterizedTest
    @CsvSource({"-1,4","1,0","1,-4"})
    void rejectsInvalidInputs(int parcels,int capacity){assertThrows(IllegalArgumentException.class,()->vehicles(parcels,capacity));}
}''','The JUnit runner evaluates five valid cases and three rejected-input cases.',
['Each calculation is O(1) work and storage. The test table verifies specified boundaries rather than performance. JUnit assertions execute without the JVM -ea flag. A parameterized runner reports individual invocations so the maximum-int failure can be identified directly.'],
['The addition-based ceiling formula can overflow.','A Java annotation alone does not install a test runner.','Do not replace rejection checks with a print-only catch block.'],[('junit-tests','Test runner setup'),('casts','Arithmetic representation')],release=21,dependency='junit')
lookup['java/parameterized-tests']['body']=lookup['java/parameterized-tests']['body'].replace('<h3>Output</h3>','<h3>Runner contract</h3>')

put('gradle-build','Java Gradle multi-project build: source ownership and a verified application task',
'A Gradle multi-project build gives separately named projects their own source sets and connects them through explicit project dependencies.',
[('Separate the billing rule from its caller',[
'The downloadable build has a billing library and an app project. The library owns the checked quantity-times-price operation. The app depends on that library and supplies the command-line entry point. Keeping the rule in one source set avoids compiling slightly different copied formulas in several applications.',
'Both projects target the Java 21 toolchain in the supplied Gradle 8.10.2 build. The application plugin names the main class. A toolchain chooses a Java installation for compilation or execution; setting source syntax alone is not the same decision.',
'The root settings file includes both projects. The app’s implementation dependency names the billing project. The included command runs the application task and prints the same result as the standalone Java rule below. No external dependency is required by this two-project fixture.'
]),('Keep reproducibility outside IDE state',[
'Use a declared build and pinned tool version so another machine can reconstruct source roots and the dependency graph. A Gradle wrapper is convenient when included; this kit declares Gradle 8.10.2 and documents the installed-tool command rather than claiming a wrapper binary is present.',
'A dependency lock or verification policy is useful when external libraries are added. This fixture has only a local project dependency, so it makes no claim about a production dependency audit, cached repository availability or a published artifact.'
])],r'''package in.aitrove.billing;
public class BillingRule {
    public static long total(int quantity,long unitCents){
        if(quantity<0||unitCents<0)throw new IllegalArgumentException("Negative billing input");
        return Math.multiplyExact((long)quantity,unitCents);
    }
    public static void main(String[] args){System.out.println(total(3,50));}
}''','150',
['The billing calculation is O(1). Build configuration, compilation and startup have separate costs dependent on source changes and the build environment. The two-project fixture verifies dependency wiring and launch; it does not measure incremental-build performance.'],
['An IDE project layout is not a portable build declaration.','Source compatibility and toolchain selection are different settings.','Do not promise that an omitted wrapper is bundled.'],[('maven','Maven project setup'),('parameterized-tests','Boundary tests')],release=21)
lookup['java/gradle-build']['body']+='<h2>Build files and command</h2>'+p('The settings.gradle file includes billing and app. Run the application with the declared Gradle version from the extracted gradle-multi directory.')+block("rootProject.name = 'aitrove-billing'\ninclude 'billing', 'app'",'groovy')+block("plugins { id 'application' }\njava { toolchain { languageVersion = JavaLanguageVersion.of(21) } }\ndependencies { implementation project(':billing') }\napplication { mainClass = 'in.aitrove.app.Main' }",'groovy')+block('gradle :app:run --console=plain','bash')

put('jmh-benchmarks','Java JMH benchmarks: consumed results, fixtures and limited measurements',
'JMH is a benchmarking runner that controls repeated measurements, warmup and JVM forks while keeping benchmark results observable to the runner.',
[('Choose a question the fixture can answer',[
'This benchmark compares exact integer membership in a HashSet and an ArrayList for declared sizes and lookup keys. Setup constructs both structures outside the measured method. Returning the boolean result keeps the lookup result observable instead of measuring a discarded computation.',
'The parameters include a present and an absent key under the selected sizes. A missing lookup scans more of the list than an early present lookup, so one carefully chosen hit cannot establish a universal container ranking. Input distribution belongs in the report.',
'The source is compiled with JMH 1.37 and its annotation processor in the downloadable Maven project. The processor generates runner metadata. A plain Java main with a nanoTime loop does not provide the same runner or isolation.'
]),('Separate smoke verification from a useful experiment',[
'The local check uses one short warmup and measurement iteration to verify the packaged runner can run. Those numbers are not published as a performance conclusion. A useful experiment needs longer measurements, more forks, representative inputs, error estimates and stated JVM and hardware settings.',
'Dead-code elimination, constant folding, allocation and retained state can change what is measured. The thread-scoped fixture declares per-worker ownership. If the real application shares one contended structure, that is a different benchmark and needs a different state scope and operation mix.'
])],r'''package in.aitrove.bench;
import org.openjdk.jmh.annotations.*;
import java.util.*;
import java.util.concurrent.TimeUnit;
@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
public class MembershipBenchmark {
    @Param({"64","4096"}) public int size;
    @Param({"63","8192"}) public int key;
    Set<Integer> indexed;List<Integer> scanned;
    @Setup public void prepare(){
        indexed=new HashSet<>();scanned=new ArrayList<>();
        for(int value=0;value<size;value++){indexed.add(value);scanned.add(value);}
    }
    @Benchmark public boolean indexedLookup(){return indexed.contains(key);}
    @Benchmark public boolean scannedLookup(){return scanned.contains(key);}
}''','Measured scores depend on the selected parameters, JVM, machine and measurement configuration.',
['Fixture construction and retained storage are O(n) for n inserted values. A list membership scan is O(n); hash membership has expected constant lookup work under its normal assumptions. Actual nanoseconds and allocation behavior require measurement and are not supplied as universal facts here.'],
['Do not use smoke-run scores as a production ranking.','Setup work should be included or excluded according to the question, not by accident.','A returned result still needs an actual JMH-generated runner to run this class.'],release=21,dependency='jmh',related=[('collection-choices','Operation choice'),('flight-recorder','Diagnostic observations')])
lookup['java/jmh-benchmarks']['body']=lookup['java/jmh-benchmarks']['body'].replace('<h3>Output</h3>','<h3>Measurement result</h3>')
lookup['java/jmh-benchmarks']['body']+='<h2>Run the packaged runner</h2>'+block('mvn package\njava -jar target/benchmarks.jar -wi 3 -i 5 -f 3','bash')

# Keep new chapters in section curricula and add cross-links without duplicate URLs.
def module(hub,title,summary,slugs):
 e=lookup['java/'+hub]; mods=e['data']['modules']; value={'title':title,'summary':summary,'lessons':[s if s.startswith(('java/','quizzes/')) else 'java/'+s for s in slugs]}
 old=next((m for m in mods if m['title']==title),None)
 if old:old.update(value)
 else:mods.append(value)
module('java','Conversion and text boundaries','Choose value ranges, text equivalence and full-input validation.',['casts','text-normalization','regular-expressions'])
module('java-collections','Snapshots, weak lifetime and sorted coordination','Separate ordering, retained references and write costs.',['copy-on-write','concurrent-sorted-map','weak-references','immutable-collections','sequenced-collections','comparator-contracts'])
module('advanced-java','Runtime boundaries and diagnostics','Inspect loaders, modules and recording artifacts.',['class-loaders','java-modules','flight-recorder'])
module('advanced-java','Waiting, permits and task stopping','Protect predicates and own admission, deadlines and shutdown.',['conditions','semaphores','scheduled-tasks','cancellation'])
module('advanced-java','Binary files and network framing','Handle partial transfers and explicit record boundaries.',['file-channels','socket-boundaries'])
module('advanced-java','Builds, test doubles and measurements','Verify builds and checked tests before interpreting measurements.',['gradle-build','test-boundaries','parameterized-tests','jmh-benchmarks'])
module('dsa-in-java','Balanced and prefix indexes','Maintain height, prefix and heap invariants.',['avl-tree','trie','binary-heap'])
module('dsa-in-java','String search and graph cost','Distinguish substring matches, forests and negative-edge distances.',['kmp-search','minimum-spanning-tree','bellman-ford'])
module('dsa-in-java','State order and greedy proof','Choose dependency order and state the exact objective.',['tabulation','greedy-intervals'])
module('java-interview-questions','Type, pipeline and failure reasoning','Use checked traces and explicit operation contracts.',['generics-interview','streams-interview','exceptions-interview'])
module('java-interview-questions','Storage, JVM and modern values','Separate transaction scope, reachability and component ownership.',['jdbc-interview','jvm-interview','modern-java-interview'])
module('java-exercises','Objects, parsing, files and workers','Run rejection, ownership and completed-work checks.',['oop-exercises','exception-exercises','file-exercises','concurrency-exercises'])
module('java-projects','Local protocol and transactional storage','Run actual local responses and one-transaction repository changes.',['http-project','database-project'])
module('java-cheatsheet','Pipelines, coordination and database review','Review choices at the boundary where they take effect.',['streams-reference','concurrency-reference','jdbc-reference'])
module('java-quizzes','Object, type and pipeline questions','Review contract choices with explained answers.',['quizzes/java-oop','quizzes/java-generics','quizzes/java-streams'])
module('java-quizzes','Workers, input and algorithm questions','Separate state, completion, framing and proof obligations.',['quizzes/java-concurrency','quizzes/java-io','quizzes/java-algorithms'])
module('java-examples','Checked runtime and protocol programs','Open canonical lesson programs and download their source.',['class-loaders','file-channels','socket-boundaries','http-project','database-project'])

hub_intro={
'java':'Java source expresses typed operations that are compiled for a declared platform release and executed by a compatible runtime.',
'advanced-java':'Advanced Java work combines type boundaries, resource ownership, concurrency, runtime inspection and external I/O contracts.',
'java-interview-questions':'Java interview reasoning explains selected methods, shared state, operation costs and the behavior that survives a failure.',
'java-exercises':'Java exercises test a stated behavior with accepted inputs, rejected inputs and checks that fail when the behavior is violated.',
'java-examples':'A complete Java example supplies an executable source unit, its declared release, expected behavior and the limits of its model.',
'java-quizzes':'Java quizzes provide local self-checks of language rules, API contracts and algorithm invariants with explained answers.',
'java-projects':'A Java learning project connects several operation contracts into one executable application boundary with acceptance checks.',
'java-cheatsheet':'A Java reference summarizes method choices and failure boundaries while preserving implementation and version distinctions.',
'dsa-in-java':'Java data-structure and algorithm programs preserve a representation invariant or a recurrence while making their input assumptions explicit.',
'java-collections':'Java collections supply membership, ordering and traversal contracts whose ownership, costs and concurrency behavior differ by implementation.'}
for slug,definition in hub_intro.items():
 e=lookup['java/'+slug]
 e['body']=re.sub(r'^<p>[\s\S]*?</p>',p(definition),e['body'],count=1);e['summary']=definition
 e['body']+='<h2>Working through this section</h2>'+p('The curriculum below groups the canonical pages for this section. Open a lesson to see its release label, operation contract and connected topics. Examples can also be linked from another section without creating a second copy of the same page.')+p('Compile the stated program with a compatible JDK and compare its result with the displayed output. Read the rejected-input and ownership clauses before changing the input. Local self-checks and downloaded programs do not imply a server-side code judge or a production service.')
 e['updated_at']='2026-09-29T07:00:00+00:00'

for path in added+expanded:
 e=lookup[path]
 if e.get('subject') in ['java-projects'] or path in ['java/java-modules','java/gradle-build','java/jmh-benchmarks','java/parameterized-tests']:
  e['data']['download_path']='/downloads/aitrove-java-source-kit.zip'
# Validate every new and existing body link before replacing the fixtures.
allpaths={e['path'] for e in entries}
for e in entries:
 if e['path'].startswith('java/'):
  for href in re.findall(r'href="([^"]+)"',e['body']):assert href.lstrip('/').split('#')[0] in allpaths,(e['path'],href)
for hub in [e for e in entries if e['type']=='subject' and e['path'].startswith('java/')]:
 paths=[path for m in hub['data']['modules'] for path in m['lessons']]
 assert len(paths)<=100,(hub['path'],len(paths))
 assert len(paths)==len(set(paths)),('duplicate curriculum',hub['path'])
 for path in paths:assert path in allpaths,(hub['path'],path)
for e in entries:
 if e['type']=='quiz' and e.get('subject')=='java-quizzes':
  for q in e['data']['questions']:
   assert len(q['options']) in (2,3) and len(set(q['options']))==len(q['options']) and 0<=q['answer']<len(q['options']) and q['explanation'],q
(ROOT/'src/data/fixtures.json').write_text(json.dumps(entries,indent=2,ensure_ascii=False)+'\n')
report={'added':added,'expanded':expanded,'newQuizzes':banks,'expandedQuizzes':updated_banks,'newArticleWordsIncludingCode':sum(len(re.sub('<[^>]+>',' ',lookup[path]['body']).split()) for path in added),'javaArticles':sum(e['type']=='article' and e['path'].startswith('java/') for e in entries),'javaHubs':10,'javaQuizzes':sum(e['type']=='quiz' and e.get('subject')=='java-quizzes' for e in entries),'quizQuestions':sum(len(e['data']['questions']) for e in entries if e['type']=='quiz' and e.get('subject')=='java-quizzes'),'localOnly':True}
(OUT/'java-finish-batch.json').write_text(json.dumps(report,indent=2))
(OUT/'aitrove-java-finish-content.json').write_text(json.dumps([lookup[path] for path in added+expanded+banks+updated_banks]+[e for e in entries if e['type']=='subject' and e['path'].startswith('java/')],indent=2,ensure_ascii=False))
print(json.dumps({k:v for k,v in report.items() if not isinstance(v,list)}))
