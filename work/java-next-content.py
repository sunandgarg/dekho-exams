"""Original Java expansion. Run against the local preview fixtures only."""
import copy, html, json, pathlib, re, uuid
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT.parent.parent / 'outputs'
entries = json.loads((ROOT/'src/data/fixtures.json').read_text())
lookup = {e['path']: e for e in entries}
added, expanded = [], []
sections = {e['subject']:e['path'] for e in entries if e['type']=='subject' and e['path'].startswith('java/')}
def paragraph(text): return '<p>'+text+'</p>'
def code(text, lang='java'): return '<pre><code class="language-'+lang+'">'+html.escape(text.strip(),quote=False)+'</code></pre>'
def lesson(slug, title, definition, parts, program, output, analysis, mistakes, related, subject='java-advanced'):
    path='java/'+slug
    body=paragraph(definition)+paragraph('<strong>Java 8+.</strong> The program uses only JDK classes and runs without a framework.')
    for heading, texts in parts: body+='<h2>'+heading+'</h2>'+''.join(paragraph(t) for t in texts)
    body+='<h2>Working program</h2>'+code(program)+'<h3>Output</h3>'+code(output,'text')
    body+='<h2>Cost and failure boundaries</h2>'+''.join(paragraph(t) for t in analysis)
    body+='<h3>Common Mistakes</h3><ul>'+''.join('<li>'+t+'</li>' for t in mistakes)+'</ul>'
    e=copy.deepcopy(lookup['java/arrays'])
    e.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),path=path,title=title,summary=definition,body=body,subject=subject,tags=['java',slug],difficulty='Intermediate',featured=False,sort_order=50+len(added),published_at='2026-09-29T06:00:00+00:00',updated_at='2026-09-29T06:00:00+00:00')
    e['data']={'subject_root':'java/java','section_path':sections[subject],'kind':'tutorial','content_format':'html','java_release':8,'java_version':'8+','reading_minutes':max(4,round(len(re.sub('<[^>]+>',' ',body).split())/150)),'author_path':'authors/aitrove-editorial','related':[{'path':'java/'+p,'title':t} for p,t in related]}
    if path in lookup: lookup[path].update(e)
    else: entries.append(e); lookup[path]=e
    added.append(path)

lesson('console-input','Java console input: Scanner tokens, lines and validation',
'Scanner splits a character source into tokens and converts those tokens to values; line-oriented input needs a separate rule for consuming line endings.',
[('Decide what one record means',[
'A depot intake screen asks for a parcel count followed by a destination line. The count is a token. The destination can contain spaces. Reading both with next() silently changes the second field into its first word; reading nextInt() followed immediately by nextLine() can instead return the rest of the count line.',
'Own the boundary. This program parses one complete count line using Integer.parseInt, then reads the complete destination line. It rejects counts outside the accepted range before creating any shipment records. A malformed number and an exhausted input are different failures, even when the interface eventually displays one validation message.',
'The fixture is a String so the example never waits for someone to type during a test. Replace it with System.in for a console application. Do not close a wrapper around System.in if another part of the process still owns that stream. The fixture scanner has an independent source and can be closed safely.'
]),('Tokens are state, not just values',[
'hasNextInt() checks the next token without consuming it. If validation fails, an input loop must consume or reject that token before trying again; otherwise it repeats forever at the same position. Locale also affects numeric parsing. A machine protocol should declare its number format rather than inherit the operator’s workstation settings.',
'Keep parsing separate from business validation. The string "-4" is a valid integer representation but an invalid parcel count for this application. That distinction makes tests smaller: parsing checks syntax and range, while the receiving method checks what counts are allowed. Read <a href="/java/exceptions">exception boundaries</a> before replacing every error with a default zero.'
])],r'''import java.util.Scanner;
public class DepotIntake {
    static int parcelCount(String line) {
        int count = Integer.parseInt(line.trim());
        if (count < 1 || count > 500) {
            throw new IllegalArgumentException("Parcel count outside 1..500");
        }
        return count;
    }
    public static void main(String[] args) {
        try (Scanner input = new Scanner("6\nPune Central Depot\n")) {
            int count = parcelCount(input.nextLine());
            String destination = input.nextLine().trim();
            if (destination.isEmpty()) throw new IllegalArgumentException("Destination required");
            System.out.println(count + " parcels -> " + destination);
        }
        try {
            parcelCount("-4");
        } catch (IllegalArgumentException rejected) {
            System.out.println("Rejected count");
        }
    }
}''','6 parcels -> Pune Central Depot\nRejected count',[
'Parsing scans the submitted count line; reading a destination scans that line too. For L input characters, budget O(L) work and storage for the strings and scanner state. Scanner performs pattern-based token processing, so a buffered reader and explicit parser may suit high-volume import work better. Measure the import, not a single interactive keystroke.',
'Integer.parseInt rejects values outside int range. A valid long value does not fit automatically. Limiting the line length before parsing also prevents an accidental multi-megabyte field from becoming routine input. Test blank lines, whitespace-only destinations, missing lines, malformed digits and the two count boundaries.'
],['Do not mix token and line reads without consuming the remainder intentionally.','Do not retry the same rejected token forever.','Do not close a shared input stream you do not own.'],[('variables-types','Primitive ranges'),('files','Buffered file input')],'java')

lesson('unicode-encoding','Java Unicode: code units, code points and UTF-8 bytes',
'A Java String indexes UTF-16 code units; Unicode code points, displayed graphemes and encoded bytes are separate quantities.',
[('Choose the unit before enforcing a limit',[
'A label containing a rocket and an accented letter can have a different length in every unit that matters to an application. A supplementary code point occupies two char positions. A base letter followed by a combining mark occupies two code points even when a reader sees one accented letter.',
'The program builds a label with one ASCII letter, one supplementary symbol and a decomposed accented letter. It reports UTF-16 length, code-point count and UTF-8 byte count independently. Those numbers answer different questions. A transport byte limit belongs after encoding; a cursor offset for String.substring belongs in UTF-16 units.',
'Do not call a code-point count a visible-character count. Grapheme segmentation needs a defined Unicode/text-processing policy. Normalizing canonically equivalent strings is also separate from changing case or removing accents. Choose normalization for the storage/search contract, then apply it consistently to both incoming data and comparisons.'
]),('Make decoding failures explicit',[
'new String(bytes, charset) is convenient when replacement of malformed input is acceptable. A strict import often needs rejection instead. CharsetDecoder can report malformed sequences rather than produce replacement characters that later collide in an identifier or hide corrupted data.',
'The program intentionally feeds an incomplete UTF-8 sequence to a reporting decoder and catches the decoding exception at the import boundary. It does not pretend that UTF-8 verification makes a label safe for HTML, a filename or a database key. Each destination has additional rules. Use <a href="/java/stringbuilder">StringBuilder</a> for assembly and <a href="/java/byte-streams">byte streams</a> for binary transport.'
])],r'''import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
public class LabelEncoding {
    public static void main(String[] args) {
        String label = "A\uD83D\uDE80e\u0301";
        System.out.println("units=" + label.length());
        System.out.println("points=" + label.codePointCount(0, label.length()));
        System.out.println("bytes=" + label.getBytes(StandardCharsets.UTF_8).length);
        try {
            StandardCharsets.UTF_8.newDecoder()
                .onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT)
                .decode(ByteBuffer.wrap(new byte[]{(byte) 0xC3}));
        } catch (CharacterCodingException rejected) {
            System.out.println("Invalid UTF-8 rejected");
        }
    }
}''','units=5\npoints=4\nbytes=8\nInvalid UTF-8 rejected',[
'Counting code points and encoding each require O(n) scans of the label. UTF-8 conversion allocates a byte array proportional to encoded size. Repeating conversion merely to recheck a limit creates unnecessary arrays; encode once at the boundary and reuse the result where ownership permits it.',
'A char-based reversal can split a surrogate pair. A code-point reversal preserves supplementary points but can still reorder combining marks away from their base. Neither is a universal user-visible reversal algorithm. Tests should include supplementary symbols, combining sequences, empty text and unpaired surrogates rather than only ASCII names.'
],['Do not use String.length() as a UTF-8 payload size.','Do not cut a string at an arbitrary char boundary and assume every symbol survives.','Do not silently repair malformed identifiers when rejection is required.'],[('strings','String equality and indexes'),('files','Explicit file encodings')],'java')

lesson('overload-resolution','Java method overloads: compile-time selection and dispatch',
'Overload resolution chooses a method signature using compile-time argument types; overriding chooses the implementation of an already selected instance method at runtime.',
[('The variable type is part of the call',[
'A formatter has separate entry points for a general object and a String label. Calling it with a variable declared Object selects the Object overload even if the value stored there happens to be a String. Changing a runtime value does not rerun overload resolution.',
'The program also passes a SpecializedReceipt through a Receipt reference. The signature is selected first, then the overridden render implementation runs on the actual receipt. That is the separate runtime decision. Keeping both decisions visible helps explain why adding an overload can change a recompiled caller without changing an existing override.',
'Prefer distinctly named methods when two overloads express different policies. formatText and formatReceipt may be clearer than a family that accidentally interprets null, a boxed number and a collection differently. The compiler can find a legal signature without proving that its semantics match the caller’s intent.'
]),('Null and numeric conversions need care',[
'An uncast null can match several reference overloads. If no single most-specific method exists, the call is ambiguous and does not compile. A cast can express the chosen signature, but it does not make dereferencing null safe. This example avoids a crash by making null handling part of each formatting method.',
'Primitive widening, boxing and variable-arity invocation participate in different applicability phases. Do not memorize one rule such as "the nearest-looking type wins." Test the exact declarations and argument types. Read <a href="/java/boxing">boxing</a> and <a href="/java/varargs">variable-arity calls</a> before designing overloaded numeric APIs.'
])],'''public class ReceiptDispatch {
    static String format(Object value) { return "object"; }
    static String format(String value) { return "text"; }
    static class Receipt {
        String render() { return "standard"; }
    }
    static class SpecializedReceipt extends Receipt {
        @Override String render() { return "priority"; }
    }
    public static void main(String[] args) {
        Object storedLabel = "paid";
        System.out.println(format(storedLabel));
        System.out.println(format((String) storedLabel));
        Receipt receipt = new SpecializedReceipt();
        System.out.println(receipt.render());
        System.out.println(format((String) null));
    }
}''','object\ntext\npriority\ntext',[
'Overload selection is a compilation decision, so no runtime scan of every overload occurs in this program. The methods return fixed strings and use O(1) additional storage. Real formatting costs depend on the selected implementation and result size; dispatch does not erase those costs.',
'A narrowing cast can fail before the method is invoked. Replacing storedLabel with an Integer would make the String cast throw ClassCastException. Tests for an overloaded API should include declared supertype variables, null expressions, primitive values, boxed values and varargs calls, not only directly typed literals.'
],['Do not confuse overload selection with virtual method dispatch.','Do not use a cast to hide an uncertain value type.','Do not add unrelated reference overloads without reviewing null calls.'],[('polymorphism','Overriding and runtime behaviour'),('methods','Method contracts')],'java')

lesson('access-control','Java access control: private state and package boundaries',
'Java access modifiers limit which source-level declarations may refer to a member; they do not replace validation or protect data after it has been returned.',
[('Expose an operation, not a writable field',[
'A warehouse wallet should not publish its balance as a writable integer. A caller could set it negative or update it without the checks required for a withdrawal. The example keeps the field private and exposes a method that validates the requested debit before modifying state.',
'The nested example fits in one runnable file, so it is not a proof of cross-package access rules. In a real package boundary, public means accessible where the enclosing type is accessible, package-private means the same package, and private confines direct access to the applicable enclosing declaration context. Protected adds subclass access rules, with restrictions on the qualifying receiver across packages.',
'Package-private is the absence of a modifier; it is not a keyword named default. A top-level class can be public or package-private, while nested declarations have more choices. Keep an implementation type package-private when clients only need an interface. That reduces the surface that later refactoring must preserve.'
]),('Returning a reference can widen the boundary',[
'A private List field stops direct field access. A public getter returning that same mutable list still allows callers to change its elements. A view or copy policy is needed for mutable state, including nested values. The <a href="/java/collection-views">collection views lesson</a> separates those choices.',
'Access is also not authentication. A public method can be called by code that can reach it; deciding whether an end user may withdraw funds belongs to an application authorization boundary. The sample is about preserving a numeric invariant inside one process. It deliberately makes no security claim about reflection, native code or untrusted code execution.'
])],'''public class WalletBoundary {
    static class WarehouseWallet {
        private int credits;
        WarehouseWallet(int initialCredits) {
            if (initialCredits < 0) throw new IllegalArgumentException("Negative balance");
            credits = initialCredits;
        }
        public boolean debit(int amount) {
            if (amount <= 0) throw new IllegalArgumentException("Positive debit required");
            if (amount > credits) return false;
            credits -= amount;
            return true;
        }
        public int balance() { return credits; }
    }
    public static void main(String[] args) {
        WarehouseWallet wallet = new WarehouseWallet(40);
        System.out.println(wallet.debit(12));
        System.out.println(wallet.debit(50));
        System.out.println("balance=" + wallet.balance());
    }
}''','true\nfalse\nbalance=28',[
'The field reads and single-threaded debit operation take O(1) work. No container copy is required because the exposed balance is a primitive value. If two workers share this instance, private does not make check-and-update atomic; use a lock or another ownership rule before sharing it.',
'Rejected withdrawals leave the old balance intact. That is a useful failure boundary: validation runs before mutation. Test zero, negative, exact-balance and excessive debits. A multi-account transfer needs a wider invariant than either account alone, so two individually valid debit/credit methods do not establish an atomic transfer.'
],['Do not equate private with thread safety.','Do not publish a mutable object and assume a private field still protects its contents.','Do not use a same-package example to infer every protected cross-package rule.'],[('encapsulation','Object invariants'),('locks','Protecting multi-step updates')],'java')

lesson('ordered-sets','Java LinkedHashSet and TreeSet: order and uniqueness',
'LinkedHashSet retains insertion order, while TreeSet stores comparator-ordered unique elements and uses that comparison to decide whether two entries belong to the same set.',
[('Pick the meaning of duplicate',[
'A dispatch screen receives warehouse codes in arrival order and must display each code once. LinkedHashSet expresses both requirements without sorting the list or maintaining a second seen-code collection. Adding the same code again does not move its first occurrence in this Java 8 example.',
'A TreeSet answers a different question: which unique entries fall in sorted order or within a requested range? The sample uses a case-insensitive comparator to show that comparison can collapse values that String.equals would consider different. "Dock-A" and "dock-a" occupy one comparator-equivalence position.',
'Decide whether that collapse is intended. A shipment comparator that compares only priority can discard distinct shipment IDs with the same priority. Add a stable tie-breaker when both entries must survive. A set is not a sorted multiset, and it does not promise to retain every object passed to add.'
]),('Mutable comparison fields break the search model',[
'If an entry changes its ordering field while inside a tree, its physical location can disagree with its new comparison value. A later contains or remove may fail to find it. Store immutable keys, or remove the entry before editing and then insert the changed value.',
'LinkedHashSet still relies on equals and hashCode. Changing a hashed key has similar lookup problems. Sorting after every display refresh is not automatically cheaper or safer than choosing a collection whose contract matches the screen. Compare <a href="/java/hashset">HashSet</a> and <a href="/java/treemap">TreeMap</a> when key/value lookup is also required.'
])],'''import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.TreeSet;
public class DockOrder {
    public static void main(String[] args) {
        LinkedHashSet<String> arrival = new LinkedHashSet<>(
            Arrays.asList("Dock-C", "Dock-A", "Dock-C", "Dock-B"));
        System.out.println(arrival);
        TreeSet<String> normalized = new TreeSet<>(String.CASE_INSENSITIVE_ORDER);
        normalized.add("Dock-A");
        normalized.add("dock-a");
        normalized.add("Dock-C");
        System.out.println("unique=" + normalized.size());
        System.out.println("next=" + normalized.ceiling("Dock-B"));
    }
}''','[Dock-C, Dock-A, Dock-B]\nunique=2\nnext=Dock-C',[
'LinkedHashSet offers expected constant-time basic hashed operations when hashes distribute suitably, with extra links for traversal order. TreeSet basic lookup, insertion and deletion have O(log n) comparison counts. Expensive comparisons multiply that cost, so comparing large text keys is not the same work as comparing small integers.',
'Both retain O(n) entries plus implementation overhead. No exact bytes-per-entry number is portable across JVM configurations. Range views remain attached to their backing sorted collection, and neither class makes compound concurrent updates safe. Review <a href="/java/collection-views">view lifetime</a> before returning a subset from a service.'
],['Do not compare only priority when equal-priority records must coexist.','Do not mutate ordering or hashed key fields while stored.','Do not expect sorted order from an insertion-ordered set.'],[('equals-hashcode','Stable key equality'),('collection-views','Views and snapshots')],'java-collections')

lesson('enum-collections','Java EnumMap and EnumSet: finite-state storage',
'EnumMap maps keys from one enum type to values, and EnumSet stores a set drawn from one enum type’s finite constants.',
[('Represent a finite domain directly',[
'A fulfillment pipeline has a known set of stages. Using enum keys prevents misspelled string labels and avoids manually treating ordinal numbers as stable business identifiers. The sample counts jobs by stage and records which stages require manual review.',
'EnumMap iteration follows declaration order, which is useful for a fixed report layout. Missing keys and keys mapped to null still need a policy: get returning null does not alone distinguish them. This program uses positive integer counts and leaves absent stages unmapped, so getOrDefault can express a zero count for an untouched stage.',
'EnumSet is useful for combinations of allowed states or permissions inside trusted application logic. It is not a replacement for a persisted permission model. Adding or reordering enum constants should not change the meaning of a database value; persist a deliberate stable code rather than the ordinal.'
]),('Copying the set does not freeze the domain',[
'EnumSet.copyOf with an EnumSet source preserves the element type even when the set is empty. Copying an arbitrary empty collection can fail because there is no element from which to infer the enum type. Use noneOf(Stage.class) when constructing an empty typed set.',
'The example keeps the map and set method-local. A shared map still needs synchronization or confinement, and publishing a mutable EnumSet gives callers an editing handle. Choose an unmodifiable wrapper or defensive copy at the boundary, then explain whether subsequent server changes should be visible to the caller.'
])],'''import java.util.EnumMap;
import java.util.EnumSet;
public class FulfillmentStates {
    enum Stage { RECEIVED, PACKED, DISPATCHED }
    public static void main(String[] args) {
        EnumMap<Stage, Integer> counts = new EnumMap<>(Stage.class);
        for (Stage stage : new Stage[]{Stage.RECEIVED, Stage.PACKED, Stage.PACKED}) {
            counts.merge(stage, 1, Integer::sum);
        }
        EnumSet<Stage> review = EnumSet.of(Stage.RECEIVED, Stage.PACKED);
        System.out.println(counts);
        System.out.println("dispatched=" + counts.getOrDefault(Stage.DISPATCHED, 0));
        EnumSet<Stage> accepted = EnumSet.copyOf(review);
        accepted.remove(Stage.RECEIVED);
        System.out.println(accepted);
    }
}''','{RECEIVED=1, PACKED=2}\ndispatched=0\n[PACKED]',[
'EnumMap is specialized for a fixed enum domain. Its storage relates to the number of declared constants, so a tiny populated map over a huge enum is not identical to a tiny generic hash map. The example has three constants and scans three submitted stages: O(r) updates for r records plus reporting work.',
'EnumSet uses a compact representation for finite membership. The exact representation can vary with the domain size and implementation; do not promise one machine word for an arbitrary enum. The defensive copy isolates subsequent membership edits, but copying a map does not recursively copy mutable mapped objects.'
],['Do not persist ordinal() as a long-lived external identifier.','Do not infer an enum type from an arbitrary empty collection.','Do not mistake a typed finite domain for concurrency control.'],[('enums','Enum state models'),('collection-views','Ownership of returned collections')],'java-collections')

lesson('collection-views','Java collection views: live wrappers, snapshots and shallow copies',
'A collection view exposes a backing collection through another interface or access policy; a snapshot copies membership but may still share the element objects.',
[('Ask which changes the caller should observe',[
'A dispatch service assembles a list of route codes and hands it to a reader. Collections.unmodifiableList(source) prevents edits through that returned wrapper, but source still owns a writable handle. If the service adds another route later, the reader sees it through the live wrapper.',
'The program returns both a live unmodifiable view and an unmodifiable snapshot built from a new ArrayList. After the source changes, their sizes differ. Neither return value lets the reader call add successfully. That tells us two separate things: whether edits are permitted and whether future source membership changes remain visible.',
'String elements are immutable in this example, so a membership snapshot is sufficient for its contract. Replace the strings with mutable Route objects and both collections still refer to those objects unless a separate element-copy policy exists. A read-only list of mutable records is not an immutable object graph.'
]),('Range views retain a relationship',[
'subList represents a range of its backing list rather than an independent list. Editing the range through supported operations changes the backing list. Structural edits through a different handle can make subsequent use of the range invalid under the list contract. Do not retain a subList across uncontrolled mutations.',
'A small view can also keep its backing list reachable. For a small long-lived selection from a large temporary list, copying the selected membership may avoid retaining unnecessary storage. That is an ownership decision, not a universal instruction to copy every collection on every call. Read <a href="/java/arraylist">ArrayList</a> and <a href="/java/iterators">iterator mutation rules</a> together.'
])],'''import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
public class RouteSnapshots {
    public static void main(String[] args) {
        List<String> routes = new ArrayList<>(Arrays.asList("North", "South"));
        List<String> live = Collections.unmodifiableList(routes);
        List<String> snapshot = Collections.unmodifiableList(new ArrayList<>(routes));
        routes.add("West");
        System.out.println("live=" + live.size());
        System.out.println("snapshot=" + snapshot.size());
        try {
            live.add("East");
        } catch (UnsupportedOperationException rejected) {
            System.out.println("Reader cannot add");
        }
    }
}''','live=3\nsnapshot=2\nReader cannot add',[
'The wrapper adds a small object without copying n elements, while the ArrayList snapshot copies n references in O(n) time and O(n) additional storage. Those references preserve the elements’ identity. Deep-copy cost depends on the reachable objects and the application’s ownership model.',
'A concurrent source needs a safe snapshot procedure. Copying a list while another thread mutates it does not create an atomic snapshot merely because the result becomes unmodifiable. Coordinate the copy or choose a collection with the required traversal semantics. Tests should mutate both source membership and a mutable element to expose the difference.'
],['Do not describe an unmodifiable live wrapper as an immutable snapshot.','Do not assume copying membership copies every element.','Do not keep a range view alive across unrelated structural edits.'],[('linkedlist','List operations'),('concurrent-map','Concurrent ownership')],'java-collections')

lesson('concurrent-map','Java ConcurrentHashMap: atomic updates and weakly consistent reads',
'ConcurrentHashMap permits concurrent access to a hash-based map and provides per-key atomic update operations; a group of separate map calls is not automatically one transaction.',
[('Replace check-then-act with one update',[
'A request counter that calls get, adds one and calls put can lose an update when two workers read the same old value. merge performs the per-key read/remap/write operation as one update, so the program does not coordinate that sequence in application code.',
'Two workers count accepted requests for one depot. Their task bodies do only map updates, and main waits for both Future results before printing the final count. Waiting matters. A log line emitted immediately after submit can observe a partially completed batch even when every individual update is safe.',
'Keep remapping functions short and free of unrelated effects. A callback that sends a message or waits for remote I/O mixes the update boundary with work that has different failure rules. Store the new map value inside the update, then perform any separately governed side effect outside it.'
]),('A safe map is not a consistent dashboard',[
'ConcurrentHashMap does not accept null keys or null values. A missing get result can therefore represent absence without colliding with a stored null. That convenience does not make a counter across several depot keys a single consistent snapshot.',
'Iterators are weakly consistent rather than ordinary fail-fast list iterators. A traversal during updates can reflect a mixture of states over time. If a report must reconcile two accounts at exactly one instant, use a larger coordination boundary instead of assuming concurrent map traversal establishes the accounting invariant. Compare <a href="/java/locks">locks</a> for multi-field state.'
])],'''import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
public class DepotRequestCounts {
    public static void main(String[] args) throws Exception {
        ConcurrentHashMap<String, Integer> counts = new ConcurrentHashMap<>();
        ExecutorService workers = Executors.newFixedThreadPool(2);
        try {
            Runnable batch = () -> {
                for (int request = 0; request < 400; request++) {
                    counts.merge("DL-01", 1, Integer::sum);
                }
            };
            Future<?> first = workers.submit(batch);
            Future<?> second = workers.submit(batch);
            first.get();
            second.get();
            System.out.println("accepted=" + counts.get("DL-01"));
        } finally {
            workers.shutdown();
        }
    }
}''','accepted=800',[
'Each batch performs r updates; expected hashed lookup work depends on hash distribution, while contention can add waiting or retry costs. Do not promise wait-free constant latency just because the map is concurrent. The stored membership uses O(k) space for k depot keys, and boxed counter replacements add allocation pressure.',
'The sample’s counts stay far below int overflow. A long-lived counter needs a range policy, rotation or a larger representation. LongAdder can reduce contention for aggregation but has different snapshot semantics. A bounded worker pool limits simultaneous workers; it does not itself bound every upstream task queue.'
],['Do not compose get and put and call the resulting increment atomic.','Do not perform slow external work inside a remapping callback.','Do not infer a multi-key transaction from per-key guarantees.'],[('hashmap','HashMap key contracts'),('executors','Worker admission')],'java-collections')

lesson('atomics','Java atomic variables: compare-and-set and one-variable invariants',
'An atomic variable supports indivisible operations on one stored value, including compare-and-set, without making every surrounding application step atomic.',
[('Reserve before admitting work',[
'A service allows at most three in-flight jobs. Reading an int and incrementing it later is not a safe reservation: several callers can all observe the same spare slot. The loop reads the current count and attempts to replace that exact observed value with the next count.',
'If another caller changes the value first, compareAndSet fails and the loop rereads state. Nothing has been reserved by that failed attempt. A successful caller must release its reservation in a finally block when its actual work ends. The program drives the gate deterministically to make the capacity and reuse behaviour easy to check.',
'This counter covers admission count only. It does not own the job’s payload, enforce request deadlines or guarantee fairness among callers. A semaphore is often a simpler fit when the requirement is just a permit count. The custom gate is shown to explain the compare-and-set boundary, not to replace every existing coordination utility.'
]),('A retry may repeat a calculation',[
'Update functions used by atomic operations can be reapplied when an update loses a race. Keep them free of effects such as charging a card, writing a receipt or incrementing another unrelated counter. Compute the candidate value without changing external state; commit the single stored value through the atomic operation.',
'Changing a separate completed counter after decrementing inFlight creates a two-variable observation window. Readers can observe those changes at different times. An immutable compound state updated through one reference, or a lock around the invariant, is needed if the two numbers must always agree. Read <a href="/java/threads">visibility and ownership</a> before treating atomics as a blanket synchronization policy.'
])],'''import java.util.concurrent.atomic.AtomicInteger;
public class AdmissionGate {
    private final AtomicInteger inFlight = new AtomicInteger();
    private final int limit;
    AdmissionGate(int limit) {
        if (limit < 1) throw new IllegalArgumentException("Positive limit required");
        this.limit = limit;
    }
    boolean reserve() {
        for (;;) {
            int observed = inFlight.get();
            if (observed >= limit) return false;
            if (inFlight.compareAndSet(observed, observed + 1)) return true;
        }
    }
    void release() {
        for (;;) {
            int observed = inFlight.get();
            if (observed == 0) throw new IllegalStateException("No reservation");
            if (inFlight.compareAndSet(observed, observed - 1)) return;
        }
    }
    public static void main(String[] args) {
        AdmissionGate gate = new AdmissionGate(3);
        System.out.println(gate.reserve());
        System.out.println(gate.reserve());
        System.out.println(gate.reserve());
        System.out.println(gate.reserve());
        gate.release();
        System.out.println(gate.reserve());
    }
}''','true\ntrue\ntrue\nfalse\ntrue',[
'The gate stores O(1) state. An uncontended call performs a small fixed amount of work, but retries under contention mean a successful call has no fixed retry bound. This sample makes no fairness or per-caller completion guarantee. Benchmark the actual contention pattern before choosing a coordination mechanism for a busy service.',
'Every success requires exactly one matching release. A double release can consume another caller’s reservation even if a zero check exists. Production code may wrap permits in scoped ownership objects rather than expose a naked release method. Validation of call discipline is separate from correctness of the atomic primitive.'
],['Do not release a reservation that was never acquired.','Do not put external side effects inside a retryable update.','Do not combine several atomic fields and assume their relationship is atomic.'],[('locks','Multi-field invariants'),('executors','Task lifecycle')])

lesson('locks','Java ReentrantLock: protect a complete state transition',
'ReentrantLock provides explicit mutual exclusion; every access participating in an invariant must follow the same lock policy.',
[('Lock the relationship between fields',[
'A stock ledger tracks available and reserved units. A reservation must check available stock, subtract from available and add to reserved as one protected transition. Locking only each field setter allows another worker to observe or act on an intermediate state.',
'The program owns one lock inside the ledger. It validates the requested quantity before locking because that check depends only on the argument. The availability decision and both field updates happen after acquisition. finally releases the lock even when a future edit adds an early return or throws an exception.',
'The snapshot method takes the same lock before reading both counters. A writer following the policy is insufficient if a reader ignores it. Returning a preformatted immutable string avoids exposing writable state. A richer API could return an immutable snapshot object with the two values instead.'
]),('Keep slow work outside the critical section',[
'Do not hold this ledger lock while calling a remote payment service. The remote call can stall, fail or re-enter application code while every unrelated ledger operation waits. Decide on a reservation state transition first, then define compensating behaviour if the external step fails.',
'Two ledgers involved in a transfer introduce another issue: acquiring their locks in inconsistent order can deadlock. A stable lock ordering or a single transfer coordinator must cover that operation. The sample intentionally has one ledger and one invariant; it does not imply that arbitrary nested locks are safe. Read <a href="/java/jdbc-transactions">database transactions</a> for persistent state boundaries.'
])],'''import java.util.concurrent.locks.ReentrantLock;
public class StockReservations {
    private final ReentrantLock lock = new ReentrantLock();
    private int available = 12;
    private int reserved;
    boolean reserve(int quantity) {
        if (quantity <= 0) throw new IllegalArgumentException("Positive quantity required");
        lock.lock();
        try {
            if (quantity > available) return false;
            available -= quantity;
            reserved += quantity;
            return true;
        } finally {
            lock.unlock();
        }
    }
    String snapshot() {
        lock.lock();
        try {
            return "available=" + available + ", reserved=" + reserved;
        } finally {
            lock.unlock();
        }
    }
    public static void main(String[] args) {
        StockReservations stock = new StockReservations();
        System.out.println(stock.reserve(5));
        System.out.println(stock.reserve(20));
        System.out.println(stock.snapshot());
    }
}''','true\nfalse\navailable=7, reserved=5',[
'The state transition itself is O(1); waiting to acquire the lock depends on contention and scheduling. A fairness setting changes acquisition policy at a potential throughput cost, but it does not guarantee the operating system will schedule a particular thread promptly. Report operation latency rather than only time spent in the arithmetic.',
'One ledger retains O(1) counters and lock state. This version does not wait for unavailable stock: it returns false. A Condition can express waiting for a state change, but waits must occur in a predicate-checking loop and need interruption and timeout policies. Those policies belong to the application contract, not to unlock alone.'
],['Always unlock in finally after successful acquisition.','Do not read protected fields through an unlocked side channel.','Do not hold a state lock during unrelated slow I/O.'],[('atomics','One-variable updates'),('blocking-queues','Bounded producer/consumer work')])

lesson('blocking-queues','Java blocking queues: bounded capacity and backpressure',
'A BlockingQueue coordinates producers and consumers, with operations that wait, time out or fail immediately when capacity or elements are unavailable.',
[('Capacity is an admission policy',[
'An import worker cannot process an unlimited stream of jobs at once. An ArrayBlockingQueue with a capacity of two limits queued membership. offer returns false when the queue is full instead of silently buffering more work. The producer must then reject, retry within a budget or slow down.',
'The program uses immediate offer and poll calls so its overload behaviour is deterministic. put and take can wait indefinitely, while timed forms bound the waiting call. Choosing between them is part of the service’s latency and shutdown contract. A queue does not automatically decide what an HTTP endpoint should return when admission fails.',
'Capacity counts elements, not bytes. Two tiny IDs are cheap; two enormous payloads may still exceed the process’s memory budget. Store a bounded reference to separately controlled payload storage when jobs can be large. Include work already being processed when estimating total in-flight memory.'
]),('Completion and shutdown are separate signals',[
'A queue becoming empty does not prove every accepted job completed. A consumer may already have removed a job and still be processing it. Track task completion separately when callers need an end-of-batch result. The <a href="/java/executors">executor lesson</a> uses Future results for that boundary.',
'Blocking queues do not allow null elements, so poll returning null can represent an empty queue. Shutdown needs an explicit protocol: interruption, a separately tracked stop condition or a sentinel value with rules for every consumer. One sentinel for several consumers can leave the others waiting forever. Catching InterruptedException and continuing unconditionally can defeat an intended stop request.'
])],'''import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
public class ImportAdmission {
    public static void main(String[] args) {
        BlockingQueue<String> jobs = new ArrayBlockingQueue<>(2);
        System.out.println(jobs.offer("manifest-41"));
        System.out.println(jobs.offer("manifest-42"));
        System.out.println(jobs.offer("manifest-43"));
        System.out.println("processing=" + jobs.poll());
        System.out.println(jobs.offer("manifest-43"));
        System.out.println("queued=" + jobs.size());
    }
}''','true\ntrue\nfalse\nprocessing=manifest-41\ntrue\nqueued=2',[
'ArrayBlockingQueue uses fixed-capacity storage, so its membership storage is O(c) for capacity c. Immediate queue operations have small fixed bookkeeping work, but coordination and contention affect elapsed time. Timed or waiting operations intentionally include waiting; treating that latency as an algorithmic constant hides the service behaviour.',
'The queue preserves FIFO element ordering, but a group of consumers can finish in a different order after taking jobs. If result order matters, attach sequence identifiers and define a reordering step. Test a full queue, an empty queue, rejected submission and shutdown while producers or consumers are waiting.'
],['Do not retry a rejected offer in a tight unbounded loop.','Do not use null as an end-of-stream element.','Do not confuse an empty queue with completed processing.'],[('arraydeque','Single-owner queues'),('concurrent-map','Concurrent result storage')],'java-collections')

lesson('completable-future','Java CompletableFuture: composition, failures and executor ownership',
'CompletableFuture represents an eventually completed result and allows dependent computations to be composed without manually nesting every callback.',
[('Compose dependencies, not waiting threads',[
'A shipment quote depends on a base rate, while the declared-insurance calculation can be obtained independently. thenCombine creates a stage that waits for both results before computing the total. It describes a dependency without making the combining expression call get on the other future.',
'thenApply maps a result into another value. thenCompose is needed when that mapping itself returns a future and the caller wants one flattened dependency chain. Returning a CompletableFuture from thenApply produces a nested result instead. Neither method automatically moves a blocking database call to a suitable executor.',
'The sample supplies an executor explicitly and owns its shutdown. Non-async continuations may run on a thread that completes the previous stage; async forms without an executor normally use the common pool. Mixing slow blocking calls into an unrelated shared pool can delay other work. Choose pool boundaries to match task behaviour.'
]),('Failure recovery should preserve the policy',[
'An exceptional completion skips ordinary value transformations until a recovery or observation stage handles it. exceptionally can substitute a result. Use that only when a fallback is valid: returning zero for a failed shipping rate lookup could accidentally turn a paid shipment into a free one.',
'The program separates a valid quote from a deliberately failed tracking lookup. The failed lookup maps to an explicit "unavailable" status. join reports failures through unchecked completion wrappers; get uses checked failure and interruption reporting. Deadline handling, cancellation of the underlying operation and cancellation of a future are separate issues. Read <a href="/java/http-client">HTTP request policies</a> before assuming a future timeout stops network work.'
])],'''import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
public class ShipmentQuoteStages {
    public static void main(String[] args) {
        ExecutorService workers = Executors.newFixedThreadPool(2);
        try {
            CompletableFuture<Integer> rate = CompletableFuture.supplyAsync(() -> 120, workers);
            CompletableFuture<Integer> insurance = CompletableFuture.supplyAsync(() -> 30, workers);
            int total = rate.thenCombine(insurance, Integer::sum).join();
            System.out.println("quote=" + total);
            CompletableFuture<String> tracking = new CompletableFuture<>();
            tracking.completeExceptionally(new IllegalStateException("Carrier unavailable"));
            System.out.println(tracking.exceptionally(failure -> "unavailable").join());
        } finally {
            workers.shutdown();
        }
    }
}''','quote=150\nunavailable',[
'This graph has a fixed number of stages, so its bookkeeping storage is O(1). A chain created per incoming request grows with the number of admitted requests and can retain captured payloads until completion. Parallel tasks can overlap, but their external work and contention still determine end-to-end latency.',
'join blocks the caller in this sample, which is acceptable at its command-line boundary. Blocking a small worker pool while waiting for tasks submitted to the same saturated pool can starve progress. Prefer composition inside the graph and wait once at the boundary that actually requires the final answer.'
],['Do not use thenApply when the returned future needs flattening.','Do not hide every failure behind a success-looking default.','Do not assume cancelling a stage interrupts the underlying operation.'],[('executors','Executor lifecycle'),('exceptions','Failure boundaries')])

lesson('byte-streams','Java byte streams: partial reads and bounded copying',
'InputStream reads bytes rather than characters, and a read into a buffer can return fewer bytes than the buffer’s capacity before reaching end of input.',
[('Copy only the bytes that were read',[
'A parcel scanner uploads a binary manifest. The transfer loop must write the count returned by read, not the entire buffer. Writing the whole buffer after a short final read appends stale bytes from an earlier iteration and corrupts the payload.',
'The program uses an in-memory input so the byte sequence is reproducible. A three-byte buffer processes a seven-byte payload in several chunks. The final chunk is shorter than the buffer; the copied bytes still match the source exactly. A real file or network stream follows the same count-based contract, although its timing and failure behaviour differ.',
'An explicit byte limit bounds accepted payload size. The sample checks the remaining budget before writing each chunk. That rejects oversize input but does not erase bytes already emitted to an external destination. Write to a temporary staging destination if publishing must happen only after the entire payload is accepted.'
]),('Bytes do not carry a text policy',[
'Wrapping a byte stream in a Reader chooses a character decoder. UTF-8 is a deliberate choice, not an intrinsic property of every input stream. The <a href="/java/unicode-encoding">encoding lesson</a> explains strict rejection of malformed sequences.',
'available() does not tell you the total file size and is not an end-of-stream test. Use read returning -1 for completion. The caller must also decide who closes the streams. This example creates both streams in main; a library copy method that receives a caller-owned destination should normally leave that destination open.'
])],'''import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.Arrays;
public class BoundedManifestCopy {
    static long copy(InputStream input, OutputStream output, long limit) throws IOException {
        if (limit < 0) throw new IllegalArgumentException("Negative limit");
        byte[] buffer = new byte[3];
        long copied = 0;
        int count;
        while ((count = input.read(buffer)) != -1) {
            if (count > limit - copied) throw new IOException("Payload too large");
            output.write(buffer, 0, count);
            copied += count;
        }
        return copied;
    }
    public static void main(String[] args) throws IOException {
        byte[] manifest = {4, 8, 15, 16, 23, 42, 50};
        try (ByteArrayInputStream input = new ByteArrayInputStream(manifest);
             ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            System.out.println("copied=" + copy(input, output, 10));
            System.out.println(Arrays.toString(output.toByteArray()));
        }
    }
}''','copied=7\n[4, 8, 15, 16, 23, 42, 50]',[
'For B bytes, copying is O(B) work. The loop buffer uses O(c) space for buffer size c; ByteArrayOutputStream in this demonstration also retains O(B) destination storage. Replacing it with a file stream avoids retaining the whole destination in Java heap, but introduces file-system and publication failure policies.',
'The budget expression compares count with limit minus copied, avoiding overflow from blindly adding before checking. Tests should include empty input, exact-limit input, a one-byte oversize input and a source that throws after returning some bytes. A successful partial write must not be reported as a completed manifest.'
],['Do not write buffer.length bytes after a short read.','Do not use available() as a total-size or completion test.','Do not promise rollback for a destination already partially written.'],[('files','File paths and ownership'),('try-with-resources','Resource closure')])

lesson('class-initialization','Java class initialization: static state and failure timing',
'Class initialization executes static field initializers and static initializer blocks before certain active uses of a class, with ordering rules distinct from object construction.',
[('A constant is not a service startup hook',[
'A compile-time constant can be inlined into a caller. Reading that constant does not necessarily initialize the declaring class. The program prints a fixed limit before accessing a non-constant configuration field; the initialization message appears only at the latter access.',
'Static field initializers and blocks execute in their source order during initialization. Calling a static method can also trigger initialization. Constructing an instance adds another sequence: class initialization first when required, then the object’s superclass and instance initialization rules.',
'Keep static initialization small and predictable. Opening sockets, reading credentials or registering remote dependencies in a static field can turn an ordinary first method call into an unexpected network operation. An explicit application startup step gives failure handling and retries a named boundary.'
]),('Loading a class is not initializing it',[
'A class can be loaded or linked before its initialization is required. Reflection APIs can request initialization or avoid it depending on the operation. Do not infer that a classpath scan has run every static block, or that a static block is safe just because startup seemed successful on one machine.',
'An exception escaping initialization can cause ExceptionInInitializerError and leave that class erroneous for subsequent active uses through that defining loader. Retrying the same method does not simply rerun a failed initializer. This is why configuration validation belongs at an explicit boundary with a defined failure policy, not inside a hidden global expression.'
])],'''public class ConfigurationStartup {
    static class Limits {
        static final int FIXED_BATCH = 20;
        static final int LOADED_BATCH = readBatch();
        static int readBatch() {
            System.out.println("Limits initialized");
            return 30;
        }
    }
    public static void main(String[] args) {
        System.out.println("fixed=" + Limits.FIXED_BATCH);
        System.out.println("loaded=" + Limits.LOADED_BATCH);
        System.out.println("again=" + Limits.LOADED_BATCH);
    }
}''','fixed=20\nLimits initialized\nloaded=30\nagain=30',[
'Initialization in this example performs O(1) work and stores two small values. Real static caches retain memory while their classes remain reachable through their loaders. Large eager data structures can increase startup time and retained memory even when a request never uses them.',
'The runtime coordinates initialization of a class, but that does not make all later operations on a mutable static object safe. A static ArrayList still needs an ownership rule. Circular dependencies among initialization routines can also expose surprising states or locking problems. Read <a href="/java/static-final">static and final ownership</a> rather than treating global fields as free shared storage.'
],['Do not assume reading an inlined constant runs a static initializer.','Do not hide slow external work inside first-use initialization.','Do not confuse initialized static state with thread-safe mutable state.'],[('constructors','Instance construction order'),('reflection','Runtime inspection')])

lesson('two-pointers','Java two pointers: pair search on sorted input',
'A two-pointer scan maintains two positions whose movement discards a provably irrelevant part of the search space.',
[('Use ordering to justify the movement',[
'A load planner needs two package weights whose sum matches a target. On ascending input, the smallest and largest remaining values define the current pair. If their sum is too small, pairing that left value with any smaller right value cannot reach the target; advancing left discards it safely.',
'If the sum is too large, pairing the current right value with any larger left value would not help. Decrementing right discards that value. The proof depends on sorted input. Reusing this loop on unsorted arrivals can skip a valid pair even though the code still runs and returns an answer-shaped result.',
'The sample returns values rather than original indexes. Sorting a copy before calling it would reorder membership and lose the direct relation to original positions unless indexes travel with the values. Decide which result the caller needs before adding a sorting step.'
]),('Protect the arithmetic and the input contract',[
'Adding two int values in int arithmetic can overflow and reverse the comparison result. The implementation promotes before addition so its long target is compared with a long sum. It still assumes the input is non-null and sorted; those are documented preconditions, not properties established by the loop.',
'left must remain less than right so one package position is not used twice. Equal weights at different positions are allowed. An empty or one-element input has no pair. Compare <a href="/java/binary-search">binary search</a> for another algorithm whose speed comes from an input-order precondition.'
])],'''import java.util.Arrays;
public class PackagePairSearch {
    static int[] pair(int[] sortedWeights, long target) {
        int left = 0;
        int right = sortedWeights.length - 1;
        while (left < right) {
            long total = (long) sortedWeights[left] + sortedWeights[right];
            if (total == target) return new int[]{sortedWeights[left], sortedWeights[right]};
            if (total < target) left++;
            else right--;
        }
        return new int[0];
    }
    public static void main(String[] args) {
        System.out.println(Arrays.toString(pair(new int[]{2, 5, 8, 11, 15}, 16)));
        System.out.println(Arrays.toString(pair(new int[]{4}, 8)));
    }
}''','[5, 11]\n[]',[
'Each iteration advances left or retreats right. Neither pointer reverses direction, so there are O(n) iterations and O(1) extra working storage, excluding the tiny returned result. Sorting an unsorted input first adds O(n log n) work and possibly copy storage; include that preprocessing in the caller’s cost.',
'The first matching pair ends the search. Enumerating every pair or counting duplicate combinations is a different contract that requires handling runs of equal values. Test duplicate weights, negative values, no match, extreme integer endpoints and the one-position case rather than assuming the first working fixture covers them.'
],['Do not use the ordering proof on unsorted input.','Do not add two int values before promoting the result.','Do not reuse a single position as both members of a pair.'],[('sorting','Sorting costs'),('sliding-window','Range scans')],'java-dsa')

lesson('sliding-window','Java sliding windows: fixed-size range totals',
'A sliding window maintains information about a contiguous range while advancing its boundaries, reusing work from the previous range.',
[('Remove the departing value before adding the next',[
'A depot reports the largest parcel total across any three consecutive hours. Recomputing every three-hour sum works, but it repeats addition of overlapping values. Maintain one running total: subtract the hour leaving the range and add the next hour entering it.',
'The program accepts a window width rather than hard-coding three. It rejects zero width and widths beyond the input length because neither describes a complete requested range. It initializes the best result from the first real window, so negative-valued data would not incorrectly produce a zero maximum.',
'A fixed-size window is not the same algorithm as a variable-size window constrained by a target sum. A shrinking rule based on increasing sums generally requires non-negative values. Negative inputs can break that monotonic argument, even though a fixed-width rolling sum remains valid.'
]),('Return enough information for the caller',[
'This API returns only the maximum total. A report that must highlight the winning hours also needs the start index, and a tie policy: first, last or all matching ranges. Store those decisions explicitly instead of trying to recover a range later from the total alone.',
'The accumulator is long, while each measurement is int. That avoids ordinary int sum overflow for a feasible int-array length. A stream with an unbounded lifetime or long measurements needs a separate overflow policy. Read <a href="/java/bigdecimal">decimal arithmetic</a> if the readings represent money with fractional units.'
])],'''public class BusiestHours {
    static long maximum(int[] hourlyParcels, int width) {
        if (width < 1 || width > hourlyParcels.length) {
            throw new IllegalArgumentException("Invalid window width");
        }
        long total = 0;
        for (int hour = 0; hour < width; hour++) total += hourlyParcels[hour];
        long best = total;
        for (int hour = width; hour < hourlyParcels.length; hour++) {
            total -= hourlyParcels[hour - width];
            total += hourlyParcels[hour];
            best = Math.max(best, total);
        }
        return best;
    }
    public static void main(String[] args) {
        System.out.println("peak=" + maximum(new int[]{4, 2, 7, 1, 6, 3}, 3));
        System.out.println("negative=" + maximum(new int[]{-8, -3, -6}, 2));
    }
}''','peak=14\nnegative=-9',[
'The initial window costs O(w), followed by O(n-w) constant-work shifts. Total time is O(n), with O(1) extra working storage. A direct recalculation approach takes O(nw) work. Both inspect the same ranges, so compare their outputs on small random arrays to catch boundary mistakes.',
'A streaming implementation cannot reread hourlyParcels[hour-width]; it needs a ring buffer or queue holding the departing values, using O(w) storage. The array version’s constant extra space depends on retaining the input. Do not reuse that claim for a streaming adaptation that stores a window.'
],['Do not start the best total at zero when all windows can be negative.','Do not accept a width that cannot form one complete range.','Do not assume every variable-window condition works with negative values.'],[('arrays','Array bounds'),('two-pointers','Movement proofs')],'java-dsa')

lesson('binary-search-tree','Java binary search trees: insertion, deletion and skew',
'A binary search tree stores keys so that every key in a node’s left subtree is smaller and every key in its right subtree is larger under the chosen ordering.',
[('The ordering invariant is recursive',[
'A shipment-ID index can descend left or right at every comparison rather than scan every stored ID. Checking only a node against its immediate children is insufficient when validating an arbitrary tree; every descendant must stay within the bounds inherited from its ancestors.',
'The sample rejects duplicate insertion by returning the existing node. Deletion has three cases. A leaf disappears; a one-child node is replaced by that child; a two-child node takes its successor key from the right subtree and then removes that successor from its old position.',
'That two-child step matters. Copying the successor key without removing its former node leaves a duplicate behind. Returning replacement roots from the recursive helpers also matters: deleting the root can change the top-level reference. The caller must retain the returned value.'
]),('An ordinary tree is not automatically balanced',[
'Ascending insertions can create a chain. Its search behaviour then resembles a linear scan, and recursive helpers can use deep call stacks. A TreeMap or TreeSet may be a better production choice when the application needs ordered lookup rather than a custom teaching tree.',
'The program owns only integer keys, so copying a successor key is enough. A key/value tree must move the associated value consistently. Mutable object keys require a rule that prevents their ordering fields from changing while stored. Read <a href="/java/ordered-sets">ordered collection contracts</a> before exposing those keys.'
])],'''import java.util.ArrayList;
import java.util.List;
public class ShipmentIdTree {
    static class Entry {
        int shipmentId;
        Entry left, right;
        Entry(int shipmentId) { this.shipmentId = shipmentId; }
    }
    static Entry insert(Entry root, int shipmentId) {
        if (root == null) return new Entry(shipmentId);
        if (shipmentId < root.shipmentId) root.left = insert(root.left, shipmentId);
        else if (shipmentId > root.shipmentId) root.right = insert(root.right, shipmentId);
        return root;
    }
    static Entry delete(Entry root, int shipmentId) {
        if (root == null) return null;
        if (shipmentId < root.shipmentId) root.left = delete(root.left, shipmentId);
        else if (shipmentId > root.shipmentId) root.right = delete(root.right, shipmentId);
        else {
            if (root.left == null) return root.right;
            if (root.right == null) return root.left;
            Entry successor = root.right;
            while (successor.left != null) successor = successor.left;
            root.shipmentId = successor.shipmentId;
            root.right = delete(root.right, successor.shipmentId);
        }
        return root;
    }
    static void ordered(Entry root, List<Integer> shipmentIds) {
        if (root == null) return;
        ordered(root.left, shipmentIds);
        shipmentIds.add(root.shipmentId);
        ordered(root.right, shipmentIds);
    }
    public static void main(String[] args) {
        Entry root = null;
        for (int id : new int[]{40, 20, 60, 50, 70}) root = insert(root, id);
        root = delete(root, 40);
        List<Integer> shipmentIds = new ArrayList<>();
        ordered(root, shipmentIds);
        System.out.println(shipmentIds);
    }
}''','[20, 50, 60, 70]',[
'Insertion and deletion each take O(h) time for height h and use O(h) recursive stack space. A balanced shape gives h around log n; this unbalanced implementation has a worst-case height of n. Stored nodes require O(n) space, and collecting all keys adds O(n) result storage.',
'The included deletion exercises a two-child root. Add tests for an absent key, a leaf, a one-child node, the only node and repeated deletion. Verify the full in-order sequence after each operation, and separately check that it contains exactly the expected membership; sorted output alone cannot detect a missing key.'
],['Retain the root returned by insertion or deletion.','Remove the successor from its original subtree after copying its key.','Do not claim logarithmic worst-case search for an unbalanced tree.'],[('tree-traversal','Tree traversal'),('treemap','Ordered map implementation')],'java-dsa')

lesson('heap-top-k','Java heaps: keep the largest k values with a small priority queue',
'A min-heap exposes its smallest retained value, allowing a top-k scan to discard the current least useful candidate without sorting the entire input.',
[('Keep only candidates that can still win',[
'A monitoring report needs the three largest queue-depth measurements. Maintain at most k values. Until the heap is full, every measurement becomes a candidate. After that, a value no larger than the smallest retained candidate cannot improve the final top-k set.',
'The program replaces the heap root only when a larger measurement arrives. It retains repeated measurements as separate samples because the report asks for values by occurrence. A report requiring distinct values needs a separate deduplication policy; replacing the heap with a set would change both membership and count.',
'PriorityQueue iteration is not sorted order. The program copies the final candidates and sorts that small result in descending order. Calling toString on the queue and labeling it a ranked report would be incorrect even if one test happened to display a useful order.'
]),('Choose behaviour for small inputs',[
'When k exceeds the input length, this implementation returns every submitted value in descending order. A non-positive k is rejected. Those choices are part of the API contract; another valid API could insist on exactly k results and reject insufficient input.',
'The sample stores int measurements. If values are records, compare a stable priority field and add a tie-breaker when report order matters. Avoid subtraction-based comparators because subtraction can overflow. Read <a href="/java/priorityqueue">PriorityQueue</a> for the standard collection’s basic contract.'
])],'''import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.PriorityQueue;
public class QueueDepthLeaders {
    static List<Integer> largest(int[] depths, int limit) {
        if (limit < 1) throw new IllegalArgumentException("Positive limit required");
        PriorityQueue<Integer> retained = new PriorityQueue<>();
        for (int depth : depths) {
            if (retained.size() < limit) retained.add(depth);
            else if (depth > retained.peek()) {
                retained.poll();
                retained.add(depth);
            }
        }
        List<Integer> ranked = new ArrayList<>(retained);
        ranked.sort(Collections.reverseOrder());
        return ranked;
    }
    public static void main(String[] args) {
        System.out.println(largest(new int[]{7, 3, 12, 8, 12, 5}, 3));
        System.out.println(largest(new int[]{4}, 3));
    }
}''','[12, 12, 8]\n[4]',[
'For n measurements and m=min(k,n) retained candidates, the scan takes O(n log(m+1)) work in the worst case for heap operations, followed by O(m log m) result sorting. Membership and returned-list storage are O(m), rather than copying and sorting all n measurements.',
'PriorityQueue growth can copy its backing array, so an individual insertion is not a hard constant allocation event. This example also boxes primitive int values into Integer objects. If the volume is high enough for those costs to matter, measure a primitive heap implementation against the simpler standard collection before adding custom storage.'
],['Do not mistake priority-queue iteration for ranked order.','Do not remove duplicate values unless distinctness is required.','Do not use subtraction as an overflow-prone comparator.'],[('sorting','Full sorting trade-offs'),('dijkstra','Heap-based distance processing')],'java-dsa')

lesson('union-find','Java union-find: connected components and path compression',
'Union-find maintains disjoint components using representative roots, supporting component merges and connectivity queries without storing a complete path between members.',
[('Connectivity is less information than a route',[
'A depot network receives links between locations and must answer whether two locations belong to the same connected group. Union-find can answer that after processing the links. It cannot return a route, a shortest distance or the edges that connect the locations; those require a graph representation.',
'The implementation stores one parent per depot and one size per component root. Merging attaches the smaller root’s tree under the larger one. During find, path compression shortens a visited chain so future lookups perform less repeated work.',
'The parent array is an implementation tree over component membership, not the physical road network. After compression, a parent link may join two depot IDs that have no direct road between them. Treating that link as a travel step would invent an edge.'
]),('Deletion changes the problem',[
'Merging links only combines groups. Removing one physical road may split a group, and this basic structure cannot undo that split correctly. Rebuild connectivity from the remaining links, or use an algorithm designed for the required update pattern.',
'Every depot ID must be within the allocated domain. The program validates IDs in find, so both connected and connect calls inherit the boundary check. A repeated connect within one group returns false and leaves the component count unchanged. Compare <a href="/java/graph-bfs">BFS</a> when an actual traversal or path is required.'
])],'''public class DepotComponents {
    private final int[] parent;
    private final int[] size;
    private int groups;
    DepotComponents(int depots) {
        if (depots < 0) throw new IllegalArgumentException("Negative depot count");
        parent = new int[depots];
        size = new int[depots];
        groups = depots;
        for (int depot = 0; depot < depots; depot++) {
            parent[depot] = depot;
            size[depot] = 1;
        }
    }
    int find(int depot) {
        if (depot < 0 || depot >= parent.length) throw new IllegalArgumentException("Unknown depot");
        while (depot != parent[depot]) {
            parent[depot] = parent[parent[depot]];
            depot = parent[depot];
        }
        return depot;
    }
    boolean connect(int first, int second) {
        int firstRoot = find(first), secondRoot = find(second);
        if (firstRoot == secondRoot) return false;
        if (size[firstRoot] < size[secondRoot]) {
            int swap = firstRoot; firstRoot = secondRoot; secondRoot = swap;
        }
        parent[secondRoot] = firstRoot;
        size[firstRoot] += size[secondRoot];
        groups--;
        return true;
    }
    public static void main(String[] args) {
        DepotComponents network = new DepotComponents(5);
        network.connect(0, 1);
        network.connect(1, 2);
        System.out.println(network.find(0) == network.find(2));
        System.out.println(network.find(0) == network.find(4));
        System.out.println("groups=" + network.groups);
        System.out.println("merged=" + network.connect(0, 2));
    }
}''','true\nfalse\ngroups=3\nmerged=false',[
'The arrays require O(v) storage and initialization for v depots. Union by size with path compression gives near-constant amortized cost, commonly expressed using the inverse Ackermann function. That is a bound across an operation sequence, not a promise that every find performs one array access.',
'Compression writes parent entries, so this implementation is not safe for concurrent callers without a coordination rule. Tests should cover isolated IDs, transitive links, repeated merges, invalid IDs and two initially separate groups joined by one later link. A component count is useful for checking that redundant links do not reduce the total.'
],['Do not read parent links as roads or shortest paths.','Do not expect basic union-find to split a component after edge deletion.','Do not decrement the component count for an already connected pair.'],[('graph-dfs','Graph reachability'),('arrays','Indexed storage')],'java-dsa')

lesson('dijkstra','Java Dijkstra: non-negative routes and stale heap entries',
'Dijkstra’s algorithm computes shortest path distances from one source in a graph whose edge weights are non-negative.',
[('Distances and pending candidates have different lifetimes',[
'A delivery planner needs the cheapest travel time from one depot to every reachable depot. The distance array stores the best known total. A priority queue orders pending candidates by that total so the smallest candidate can be examined next.',
'The program uses lazy queue updates: it inserts a new candidate when a shorter route is found instead of editing an older entry already in the heap. An old candidate can therefore remain pending after its distance has improved. The equality check against the distance array discards that stale entry before relaxing its outgoing roads.',
'Ordinary BFS minimizes edge count, not total weight. A two-road journey can be cheaper than a direct road with a large travel time. Use <a href="/java/graph-bfs">BFS</a> only when its unweighted cost model matches the problem.'
]),('Reject a cost model the proof does not support',[
'Negative road weights are rejected by the Road constructor. Allowing a negative edge invalidates the greedy finalization argument; removing the validation does not extend this implementation to refunds or negative adjustments. Choose a shortest-path algorithm that supports those weights.',
'Distances use long even though one road’s minutes use int. Before addition, the method checks whether the candidate total would overflow. Long.MAX_VALUE represents unreachable, so an exactly equal route cost is outside this representation’s finite-distance contract. A production API should expose reachability explicitly rather than print the sentinel as a valid journey.'
])],'''import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.PriorityQueue;
public class DeliveryDistances {
    static class Road {
        final int depot, minutes;
        Road(int depot, int minutes) {
            if (minutes < 0) throw new IllegalArgumentException("Negative travel time");
            this.depot = depot; this.minutes = minutes;
        }
    }
    static class Candidate {
        final int depot;
        final long minutes;
        Candidate(int depot, long minutes) { this.depot = depot; this.minutes = minutes; }
    }
    static long[] shortest(List<List<Road>> roads, int source) {
        if (source < 0 || source >= roads.size()) throw new IllegalArgumentException("Unknown source");
        long[] distance = new long[roads.size()];
        Arrays.fill(distance, Long.MAX_VALUE);
        distance[source] = 0;
        PriorityQueue<Candidate> pending = new PriorityQueue<>(Comparator.comparingLong(c -> c.minutes));
        pending.add(new Candidate(source, 0));
        while (!pending.isEmpty()) {
            Candidate current = pending.poll();
            if (current.minutes != distance[current.depot]) continue;
            for (Road road : roads.get(current.depot)) {
                if (road.depot < 0 || road.depot >= roads.size()) throw new IllegalArgumentException("Unknown destination");
                if (current.minutes > Long.MAX_VALUE - road.minutes) throw new ArithmeticException("Distance overflow");
                long improved = current.minutes + road.minutes;
                if (improved < distance[road.depot]) {
                    distance[road.depot] = improved;
                    pending.add(new Candidate(road.depot, improved));
                }
            }
        }
        return distance;
    }
    public static void main(String[] args) {
        List<List<Road>> roads = new ArrayList<>();
        for (int depot = 0; depot < 4; depot++) roads.add(new ArrayList<>());
        roads.get(0).add(new Road(1, 4)); roads.get(0).add(new Road(2, 10));
        roads.get(1).add(new Road(2, 3)); roads.get(1).add(new Road(3, 12));
        roads.get(2).add(new Road(3, 1));
        System.out.println(Arrays.toString(shortest(roads, 0)));
    }
}''','[0, 4, 7, 8]',[
'With adjacency lists and lazy candidates, the queue can retain O(e) entries for e edges. The total bound is O(v + (v+e) log(e+1)) work, with O(v+e) extra state in the worst case. This queue representation is why quoting only O(v) heap storage would be misleading.',
'The result contains distances only. Returning paths requires a predecessor array updated when a distance improves, followed by path reconstruction. Tests should include unreachable depots, zero-weight edges, parallel roads, cycles and a cheaper indirect journey that makes an older queue entry stale.'
],['Do not accept negative weights without changing the algorithm.','Do not expand stale queue candidates as if they were current best routes.','Do not mistake the unreachable sentinel for a finite distance.'],[('heap-top-k','Heap ordering and costs'),('graph-dfs','Reachability without weights')],'java-dsa')

lesson('topological-sort','Java topological sorting: prerequisites and cycle rejection',
'A topological ordering places every prerequisite before the task that depends on it in a directed acyclic graph.',
[('Make edge direction explicit',[
'A build pipeline has compile and schema-generation tasks that must finish before packaging; packaging must finish before publication. In this representation, an edge points from prerequisite to dependent. Reversing that meaning would produce an order that looks structured but starts tasks before their inputs exist.',
'The method counts incoming prerequisite edges, places zero-incoming tasks in a queue, and removes one ready task at a time. Processing it reduces the counts of its dependents. A dependent becomes ready only after its final prerequisite edge has been accounted for.',
'The sample reports indexes for a four-task fixture. An application would map those indexes to stable task IDs. A valid order is not necessarily unique. Queue insertion order controls which independent ready task appears first, so tests should check edge constraints rather than assume every valid implementation produces the same ordering.'
]),('Detect an incomplete result',[
'If the graph contains a cycle, some tasks never reach zero incoming count. Producing fewer than v tasks therefore means the method has not found a complete topological order. The sample throws instead of returning a partial prefix that a caller might mistake for a complete build plan.',
'A prerequisite cycle is not fixed by retrying the blocked tasks. The graph definition must change, or the application must use another model for mutually dependent state. Parallel edges are counted and decremented consistently here; a builder that deduplicates only one side of that accounting can introduce false readiness or false cycle reports.'
])],'''import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Queue;
public class BuildPrerequisites {
    static int[] order(int[][] dependents) {
        int[] incoming = new int[dependents.length];
        for (int[] nextTasks : dependents) {
            for (int task : nextTasks) {
                if (task < 0 || task >= incoming.length) throw new IllegalArgumentException("Unknown task");
                incoming[task]++;
            }
        }
        Queue<Integer> ready = new ArrayDeque<>();
        for (int task = 0; task < incoming.length; task++) if (incoming[task] == 0) ready.add(task);
        int[] ordered = new int[incoming.length];
        int completed = 0;
        while (!ready.isEmpty()) {
            int task = ready.remove();
            ordered[completed++] = task;
            for (int dependent : dependents[task]) {
                if (--incoming[dependent] == 0) ready.add(dependent);
            }
        }
        if (completed != incoming.length) throw new IllegalArgumentException("Prerequisite cycle");
        return ordered;
    }
    public static void main(String[] args) {
        System.out.println(Arrays.toString(order(new int[][]{{2}, {2}, {3}, {}})));
        try { order(new int[][]{{1}, {0}}); }
        catch (IllegalArgumentException rejected) { System.out.println("Cycle rejected"); }
    }
}''','[0, 1, 2, 3]\nCycle rejected',[
'Each task enters the queue once and each directed edge is counted and later visited once. Time is O(v+e), with O(v) extra counters, queue and result storage beyond the input adjacency representation. An empty graph returns an empty complete order.',
'This method produces a plan; it does not run tasks, observe task failures or coordinate workers. A concurrent build scheduler must mark a prerequisite complete only after successful execution, and decide whether dependent tasks are cancelled after failure. See <a href="/java/completable-future">completion stages</a> for dependency composition.'
],['Do not reverse prerequisite/dependent edge meaning halfway through the pipeline.','Do not report a partial order as a complete acyclic plan.','Do not assume independent tasks have one mandatory order.'],[('graph-dfs','Directed graph traversal'),('arraydeque','Ready-task queues')],'java-dsa')

lesson('backtracking','Java backtracking: subset choices and restoring state',
'Backtracking explores a search tree by making a choice, exploring the remaining choices and restoring temporary state before trying the next branch.',
[('The selected list belongs to one branch at a time',[
'A packing station must enumerate combinations of positive package weights that reach a target. At each input position, the search can include that package or skip it. The selected list records the current branch, while the result list retains completed combinations.',
'The include branch appends a weight and removes that same final element after returning. Without restoration, the skip branch inherits a choice it did not make. Completed solutions copy the selected list, because keeping the same mutable list reference would make later removals rewrite previously found solutions.',
'Each input position can be used once. Equal weights at different positions remain distinct choices, so this version can return repeated-looking value combinations. If the business asks for unique value combinations, group equal weights or add a deliberate deduplication strategy. Do not erase duplicates after the search without considering its additional memory cost.'
]),('Prune only under the stated precondition',[
'The method includes a weight only when it fits the remaining positive target. That pruning depends on strictly positive weights. A negative weight could bring an oversized partial choice back down later, and a zero changes termination and duplicate-result reasoning. The public method rejects both.',
'A target of zero has one solution: choose no packages. Reaching zero adds the copied branch and stops that branch because additional positive weights cannot preserve the target. An unreachable positive target returns an empty result list. Read <a href="/java/recursion">recursive progress</a> before adding more pruning conditions.'
])],'''import java.util.ArrayList;
import java.util.List;
public class PackingCombinations {
    static void search(int[] weights, int index, int remaining,
                       List<Integer> selected, List<List<Integer>> results) {
        if (remaining == 0) { results.add(new ArrayList<>(selected)); return; }
        if (index == weights.length) return;
        if (weights[index] <= remaining) {
            selected.add(weights[index]);
            search(weights, index + 1, remaining - weights[index], selected, results);
            selected.remove(selected.size() - 1);
        }
        search(weights, index + 1, remaining, selected, results);
    }
    static List<List<Integer>> combinations(int[] weights, int target) {
        if (target < 0) throw new IllegalArgumentException("Negative target");
        for (int weight : weights) if (weight <= 0) throw new IllegalArgumentException("Positive weights required");
        List<List<Integer>> results = new ArrayList<>();
        search(weights, 0, target, new ArrayList<>(), results);
        return results;
    }
    public static void main(String[] args) {
        System.out.println(combinations(new int[]{2, 3, 5, 7}, 10));
        System.out.println(combinations(new int[]{4, 6}, 0));
    }
}''','[[2, 3, 5], [3, 7]]\n[[]]',[
'The include/skip tree has up to O(2^n) search nodes for n packages. Copying r solutions can add O(nr) output work and storage. The call stack and mutable branch use O(n) working space. Pruning helps particular inputs, but does not establish a polynomial worst-case bound.',
'If the caller needs only whether a combination exists, enumerating every solution wastes work and memory. A boolean search can stop at the first result, or a cached-state method can reuse repeated index/remaining subproblems. The <a href="/java/memoization">memoization lesson</a> discusses the changed state and space trade-off.'
],['Restore branch state before exploring a sibling branch.','Copy a found solution before retaining it.','Do not use positive-weight pruning on an input model that allows negative values.'],[('memoization','Caching repeated states'),('two-pointers','Pair search instead of arbitrary subsets')],'java-dsa')

lesson('array-string-exercises','Java array and text exercises: stable filtering and boundary tests',
'Stable filtering retains accepted elements in their original order; the contract must define whether the input is mutated and what equality means.',
[('Separate two small tasks',[
'Task one removes adjacent duplicate shipment codes without changing the input array. Task two checks whether a text field is a palindrome under an ASCII-letter, case-insensitive policy. They use different representations and should not share a generic helper merely because both contain loops.',
'For the array task, preserve the first code in each run, not the first code seen anywhere in the array. The input [7,7,3,7] must produce [7,3,7]. A HashSet would remove the later 7 and violate the adjacent-only requirement. The implementation uses a separate output array, then trims it to the retained size.',
'For the text task, spell out normalization. This version drops every non-ASCII letter and compares lowercase letters from both ends. That policy is appropriate only for the exercise. It is not a Unicode name validator or a general rule for comparing user text. <a href="/java/unicode-encoding">Unicode units</a> need a wider contract.'
]),('Turn examples into checks that can fail',[
'A printed output is useful for reading, but a test should stop when an expected result differs. The program uses explicit checks rather than Java assert statements, which are disabled unless assertions are enabled. It covers separated duplicates, empty input, normalized matching text and a non-match.',
'Extend the fixture set before changing the implementation. Add an all-equal array, an array with no duplicates, one retained element, punctuation-only text and mixed case. Null input is rejected by ordinary dereferencing here; add a named validation exception if the public API needs clearer diagnostics.'
])],'''import java.util.Arrays;
public class IntakeBoundaryChecks {
    static int[] collapseRuns(int[] shipmentCodes) {
        int[] retained = new int[shipmentCodes.length];
        int count = 0;
        for (int code : shipmentCodes) {
            if (count == 0 || retained[count - 1] != code) retained[count++] = code;
        }
        return Arrays.copyOf(retained, count);
    }
    static boolean asciiPalindrome(String text) {
        String normalized = text.replaceAll("[^A-Za-z]", "").toLowerCase(java.util.Locale.ROOT);
        int left = 0, right = normalized.length() - 1;
        while (left < right) if (normalized.charAt(left++) != normalized.charAt(right--)) return false;
        return true;
    }
    static void require(boolean condition) {
        if (!condition) throw new IllegalStateException("Exercise check failed");
    }
    public static void main(String[] args) {
        require(Arrays.equals(collapseRuns(new int[]{7, 7, 3, 7}), new int[]{7, 3, 7}));
        require(collapseRuns(new int[0]).length == 0);
        require(asciiPalindrome("Never odd or even"));
        require(!asciiPalindrome("parcel"));
        System.out.println("4 boundary checks passed");
    }
}''','4 boundary checks passed',[
'The array scan and final trim copy take O(n) time and O(n) additional storage. An in-place compaction can use O(1) working storage but needs to return the logical retained length, since an array cannot shrink. That API changes ownership and mutation, so it should be a separate exercise rather than an unnoticed optimization.',
'The text normalization and two-ended comparison take O(m) work for m text units under this fixed simple pattern, and allocate O(m) normalized text. A direct scan could skip rejected characters without building the normalized string. Keep the same ASCII/case policy when comparing the alternatives.'
],['Do not substitute global deduplication for adjacent-run removal.','Do not use disabled assert statements as the only executable checks.','Do not claim an ASCII normalization policy handles every written language.'],[('arrays','Arrays and logical size'),('strings','Text equality'),('junit-tests','Reusable automated tests')],'java-exercises')

lesson('manifest-project','Java file project: validate a manifest before producing a summary',
'A staged file import validates an input batch before publishing derived results, so malformed records cannot quietly become accepted business state.',
[('Keep the file format deliberately small',[
'This project reads UTF-8 lines of depot code and positive parcel count separated by one comma. It is not a CSV parser: quoted commas, multiline fields and escaping are outside its format. That restriction is part of the contract, not an invitation to label split(",") a complete CSV implementation.',
'The parser checks both field count and count syntax, then aggregates counts in insertion order. Math.addExact detects overflow instead of wrapping a depot total. The method returns a result only after every non-empty record has passed. A caller cannot observe its temporary map while a later record is still being validated.',
'The program writes an independent temporary input file, imports it, prints the completed summary and removes the file in finally. The deterministic output avoids including the randomly generated file path. A production import should put temporary files in an explicitly owned directory and define cleanup after process failure too.'
]),('Bound the demonstration before calling it a service',[
'Files.readAllLines retains the whole file. This project is intended for small bounded manifests. A larger input needs buffered streaming, a line-length limit and limits on record count and distinct depot codes. Streaming alone does not bound an aggregation map if every record introduces another key.',
'If the summary must become a persistent replacement file, write it to a staging file and publish it with a file-system policy that handles unsupported atomic moves and failures. Printing to standard output is not transactional publication. The current project validates and summarizes; it makes no guarantee about a remote database or a crash-safe multi-file update.'
])],'''import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.Map;
public class ManifestImport {
    static Map<String, Integer> read(Path input) throws IOException {
        Map<String, Integer> totals = new LinkedHashMap<>();
        int lineNumber = 0;
        for (String line : Files.readAllLines(input, StandardCharsets.UTF_8)) {
            lineNumber++;
            String[] fields = line.split(",", -1);
            if (fields.length != 2 || fields[0].trim().isEmpty()) {
                throw new IllegalArgumentException("Malformed line " + lineNumber);
            }
            String depot = fields[0].trim();
            int count = Integer.parseInt(fields[1].trim());
            if (count <= 0) throw new IllegalArgumentException("Invalid count at line " + lineNumber);
            totals.merge(depot, count, Math::addExact);
        }
        return totals;
    }
    public static void main(String[] args) throws IOException {
        Path input = Files.createTempFile("aitrove-manifest-", ".txt");
        try {
            Files.write(input, Arrays.asList("DL-01,4", "PN-02,3", "DL-01,6"), StandardCharsets.UTF_8);
            System.out.println(read(input));
            Files.write(input, Arrays.asList("DL-01,4", "PN-02,-3"), StandardCharsets.UTF_8);
            try { read(input); }
            catch (IllegalArgumentException rejected) { System.out.println("Invalid batch rejected"); }
        } finally {
            Files.deleteIfExists(input);
        }
    }
}''','{DL-01=10, PN-02=3}\nInvalid batch rejected',[
'For B input text units and k distinct depot codes, parsing and expected hash-map aggregation take O(B) work, assuming ordinary hash distribution and bounded numeric fields. This readAllLines version retains O(B+k) storage; a streamed version can reduce input retention but still needs O(k) aggregation storage.',
'Test an empty file, a missing comma, an extra comma, an empty depot, an absent numeric field, overflow and a malformed record late in a batch. Verify that failed parsing produces no returned partial summary. Filesystem permission errors and malformed business records should remain distinguishable in the caller’s diagnostics.'
],['Do not call a restricted comma-separated format a general CSV parser.','Do not retain an unbounded file or unbounded number of keys without admission limits.','Do not publish a partial summary before the batch has passed validation.'],[('console-input','Parsing and business validation'),('files','File ownership'),('bigdecimal','Numeric policy')],'java-projects')

updates = {
 'basics': (
  'A Java control-flow statement selects or repeats work using typed values and boolean conditions.',
  [('Make each branch cover a deliberate boundary', [
   'A parcel routing rule might accept a count between 1 and 500. Test the value below the range, the first accepted value, the last accepted value and the value above it. Testing only a middle value cannot reveal an accidental greater-than sign where greater-than-or-equal was required.',
   'A condition can also protect a later operation. In a null check followed by a length check, short-circuit evaluation prevents dereferencing a missing reference only when the null guard is evaluated first. Reversing the expressions changes failure behaviour. Keep guards close to the operation they protect.',
   'A numeric expression is evaluated under the operand types. Assigning the result of int multiplication to long does not repair an overflow that already happened during multiplication. Promote an operand before the operation when the result needs a wider range. <a href="/java/operators">Numeric promotion</a> covers that distinction.'
  ]), ('A loop needs progress and a stopping rule', [
   'For an indexed array scan, the valid condition is index less than length. Less-than-or-equal reaches an invalid position. Incrementing the index establishes progress; removing that increment can make a correct-looking condition run forever.',
   'Nested loops multiply work when each outer iteration scans the entire inner range. Two independent scans do not: their costs add. Count the iterations that actually execute rather than labeling every pair of loops quadratic.',
   'Start with an empty input and a one-element input before large fixtures. They make stopping conditions visible. After the branch and loop basics, use <a href="/java/console-input">console input</a> to separate invalid input from valid values that fail a business rule.'
  ])]),
 'hello-world': (
  'A conventional Java command-line entry point is a public static main method that the launcher calls with a String array of command-line arguments.',
  [('Keep the source name and launched name separate', [
   'The source filename matches the public class name in this example: Hello.java contains public class Hello. javac creates Hello.class. The ordinary class launcher receives Hello without a .java or .class suffix; it searches the classpath for compiled code.',
   'A package declaration changes the launched name. A class in a package is launched by its qualified name, and the classpath must point at the root containing that package directory. Running from the wrong directory can therefore fail even when compilation succeeded.',
   'Compilation and execution are separate failure boundaries. A missing javac executable is a toolchain problem. A compiler error is a source/type problem. A class-not-found error is a launch/classpath problem. An exception after main starts is an execution problem. Do not edit the print statement to fix all four.'
  ]), ('Change one observable condition', [
   'Pass a command-line argument and inspect args.length before reading args[0]. Launching with no arguments supplies an empty array, so an unchecked first-element access fails. That small change introduces an actual input contract without requiring console parsing.',
   'System.out prints text to a stream. It does not return the printed value from main or persist a business record. A test that needs to examine computed results is easier to write when calculation is in a method and printing is kept at the boundary.',
   'Use <a href="/java/setup">the JDK setup lesson</a> for compile/run commands and <a href="/java/packages">package layout</a> for multi-file applications. This entry-point program performs constant work and allocates only its small output-related state.'
  ])]),
 'sum-exercise': (
  'An array sum folds each element into an accumulator; the chosen numeric range and empty-input result are part of its contract.',
  [('Define the range before optimizing', [
   'The existing method assumes the sum fits in int. That is a precondition, not a check implemented by ordinary addition. A pair of large positive values can wrap to a negative result. Decide whether the application should reject overflow with Math.addExact or accumulate into a wider long result.',
   'An empty array returns zero because zero is the additive identity. Null is not an empty array. Treating the two as equivalent can hide missing data, so either reject null explicitly or document an intentional default at the caller’s boundary.',
   'Negative elements are valid under this arithmetic contract. A method that silently skips them is no longer a sum. Test positive-only, negative-only, mixed-sign and zero-filled arrays before reusing the calculation for a ledger.'
  ]), ('Compare against an independent expectation', [
   'A test should compare the returned result with a known total and fail when the values differ. Printing a total and visually accepting it is too easy to miss in a larger test run. Include a case that reaches the chosen maximum boundary and a case that exceeds it under a rejecting policy.',
   'The loop visits each element once, so it performs O(n) work and uses O(1) extra storage. Sorting before summing adds work without changing the arithmetic result under exact integer addition. Converting the array to a list adds allocation unless another part of the application actually needs that representation.',
   'A parallel sum needs a defined combination rule and adds task overhead. For floating-point values, regrouping additions can change rounding results; that is a different numeric contract. See <a href="/java/bigdecimal">decimal calculations</a> when exact business rounding is required.'
  ])]),
 'linear-search': (
  'Linear search examines elements in sequence until a match is found or the complete search range has been exhausted.',
  [('Specify which match is returned', [
   'The existing method returns the first matching index. Repeated values do not change that rule. A last-match search must continue after finding an earlier occurrence, while a count-of-matches API must retain a counter rather than return an index.',
   'Minus one represents absence because valid array indexes are non-negative. Returning zero for absence would collide with a real match in the first position. An API returning an object instead needs an explicit missing-value representation, such as Optional, rather than borrowing an unrelated numeric sentinel.',
   'An empty array has no match and executes no loop iterations. A null array is outside this implementation’s input contract and fails before a scan can begin. Put validation at the boundary if callers need a named exception for missing input.'
  ]), ('Use the simple scan as a reference', [
   'For small test fixtures, a linear scan is a useful reference against which to check a more elaborate index. Compare the actual membership and first-position semantics. A faster method that returns a different duplicate occurrence is not interchangeable when the caller requires the first one.',
   'The best case inspects one element, while absence or a match at the final position requires n comparisons. Extra working storage is O(1). For repeated searches, building a hash index may reduce lookup work but adds storage and changes update costs.',
   '<a href="/java/binary-search">Binary search</a> requires sorted input and has separate duplicate-position choices. Sorting a batch only to answer one lookup may cost more than this scan; include that preprocessing rather than comparing the scan with only the binary-search loop.'
  ])]),
 'arraylist': (
  None,
  [('Capacity and ownership are separate decisions', [
   'Capacity is storage reserved for references; size is the number of elements currently in the list. new ArrayList(100) does not create one hundred usable indexed elements. Calling get(0) before adding anything still fails. Use a measured capacity hint when a batch size is known, but do not reserve enormous buffers for every small request.',
   'Growing the backing storage can copy existing references. Adding at the end is amortized constant work under ordinary growth, but one individual addition may perform a resize. Inserting or removing near the start shifts later references, so repeated front edits can produce quadratic work.',
   'An ArrayList copy retains the same element references. If Receipt objects are mutable, a caller changing one receipt can affect both lists. The <a href="/java/collection-views">view and snapshot lesson</a> distinguishes membership copies from independent object state.'
  ]), ('Choose a mutation and traversal policy', [
   'Removing by index from a List of integers is not the same overload as removing an Integer value. Make the value type explicit when the business operation asks to remove a particular numeric ID.',
   'Editing the list structurally during an ordinary enhanced-for traversal can invalidate its iterator. Use the iterator’s supported removal path, removeIf for a predicate, or a separate transformed result. Fail-fast behaviour detects mistakes on a best-effort basis; it is not a thread-safety guarantee.',
   'Use <a href="/java/arraydeque">ArrayDeque</a> for a single-owner endpoint queue and <a href="/java/blocking-queues">a bounded blocking queue</a> for producer/consumer admission. A collection choice should follow access patterns rather than its name.'
  ])]),
 'arraydeque': (
  None,
  [('An empty queue needs an explicit policy', [
   'pollFirst returns null when no element exists, while removeFirst throws. Use poll when empty is an expected state and the caller can choose another task; use a throwing operation when emptiness violates a proven application precondition.',
   'ArrayDeque does not permit null elements, which keeps the null result from poll unambiguous. A LinkedList can contain null, so copying the same interpretation to a LinkedList-backed queue without controlling elements changes the meaning of an empty-looking result.',
   'A stack uses push/pop or consistent first-end operations. A FIFO queue adds at the back and removes from the front. Mixing ends unintentionally changes processing order while every call remains individually valid.'
  ]), ('Endpoint speed does not solve shared ownership', [
   'Endpoint insertions and removals have amortized constant work; resizing can copy stored references. Searching by value or removing an occurrence can require a full scan. The deque stores O(n) references and implementation capacity, rather than one separately allocated link node for every element.',
   'ArrayDeque is not a concurrent queue. Giving it to two workers without coordination can corrupt the assumptions behind a compound empty-check and remove. A synchronized access policy must cover all participating operations, or use a concurrent collection designed for the required producer/consumer contract.',
   'Clearing pending membership does not cancel a task another worker already removed. Completion, cancellation and queue size are separate facts. See <a href="/java/blocking-queues">bounded queues</a> for admission and shutdown boundaries.'
  ])]),
 'interview-basics': (
  'A Java interview answer should separate language contracts, library guarantees and implementation-dependent behaviour before predicting an output.',
  [('Trace a contract, then state the caveat', [
   'For an equality question, ask whether the operator compares primitive values, object identity or an equals implementation. String interning can make an incorrect identity test appear to work for literals. A runtime-created value exposes the difference. Follow up by describing stable hash keys rather than reciting only an equals slogan.',
   'For a pass-by-value question, separate the copied reference from the shared object. A method can mutate the object reachable through the copied reference; assigning its parameter to another object does not replace the caller’s variable. <a href="/java/pass-by-value">The runnable reference example</a> makes both effects observable.',
   'For a collection complexity question, name the operation and its precondition. LinkedList insertion after an already positioned iterator differs from insertion at an index that first requires traversal. An answer that says all insertions are constant-time hides the lookup cost.'
  ]), ('Turn a prediction into a checked example', [
   'Write the smallest complete program that preserves the disputed condition, compile it for the stated Java release and compare the output. For concurrency, one observed output is not proof that no other interleaving exists. Explain the visibility or synchronization rule that constrains possible outcomes.',
   'A strong answer also distinguishes a guarantee from a diagnostic. ConcurrentModificationException is not a lock, and a garbage collector is not a deterministic resource closer. Use <a href="/java/try-with-resources">resource scopes</a> to close files and connections.',
   'Continue with <a href="/java/object-interview">object-contract questions</a> and <a href="/java/concurrency-interview">concurrency reasoning</a>. Predict a failure case as well as the ordinary result, then explain which change repairs the violated contract.'
  ])]),
 'syntax-reference': (
  'Java syntax expresses typed declarations, control flow and member access; a reference is useful only when its short forms retain the surrounding validity rules.',
  [('Declarations do not remove ownership rules', [
   'A primitive local stores a value, while a reference local identifies an object or holds null. final prevents reassignment of that local or field after its allowed initialization; it does not recursively freeze the referenced object. final List declarations can still permit membership edits.',
   'A method signature states parameter types and a return type. Overloads share a name with different parameter lists, while an override supplies another implementation of an inherited instance method. Return type alone does not create an overload. See <a href="/java/overload-resolution">compile-time selection</a> when a short signature list leaves ambiguity.',
   'An interface declaration specifies a type contract. Choosing it for a variable allows different implementations, but their operation costs can still differ. List.get on ArrayList and LinkedList shares a signature without sharing the same indexed-access cost.'
  ]), ('Keep failure-sensitive forms nearby', [
   'An array index must be at least zero and smaller than length. A loop using less-than-or-equal reaches a forbidden final position. An enhanced-for loop avoids explicit indexing but does not permit arbitrary structural modification of its backing collection.',
   'try-with-resources closes owned AutoCloseable values on scope exit. A catch clause handles specified failures; it should not silently convert all failures into an ordinary success result. A finally block is appropriate for releasing an acquired lock, as the <a href="/java/locks">lock example</a> shows.',
   'Version matters. Records require a newer source level than Java 8, and the pattern switch lessons in this curriculum declare Java 21. Do not paste their syntax into a Java 8 build and diagnose the parser error as a missing import. Check the page’s release label before compiling.'
  ])])
}
for slug, (definition, parts) in updates.items():
    e=lookup['java/'+slug]
    if definition: e['body']=re.sub(r'^<p>.*?</p>', paragraph(definition), e['body'], count=1)
    section=''.join('<h2>'+heading+'</h2>'+''.join(paragraph(t) for t in texts) for heading,texts in parts)
    marker='<h2>'+parts[0][0]+'</h2>'
    if marker not in e['body']:
        e['body']=e['body'].replace('<h3>Common Mistakes</h3>',section+'<h3>Common Mistakes</h3>')
    e['data']['reading_minutes']=max(4,round(len(re.sub('<[^>]+>',' ',e['body']).split())/150))
    e['updated_at']='2026-09-29T06:00:00+00:00'
    expanded.append(e['path'])

def module(hub, title, summary, slugs):
    e=lookup['java/'+hub]
    lessons=['java/'+s for s in slugs]
    mods=e['data'].setdefault('modules',[])
    old=next((m for m in mods if m['title']==title),None)
    if old: old.update(summary=summary,lessons=lessons)
    else: mods.append({'title':title,'summary':summary,'lessons':lessons})
    e['updated_at']='2026-09-29T06:00:00+00:00'
module('java','Input, encoding and call boundaries','Parse complete records, choose text units and keep type/access boundaries explicit.',['console-input','unicode-encoding','overload-resolution','access-control'])
module('java-collections','Membership order and ownership','Choose ordering, finite-domain keys, live views and snapshots.',['ordered-sets','enum-collections','collection-views'])
module('java-collections','Concurrent containers','Separate per-key updates from snapshots and bounded task admission.',['concurrent-map','blocking-queues'])
module('advanced-java','Coordinated state and completion','Protect the whole invariant and define the task completion boundary.',['atomics','locks','completable-future'])
module('advanced-java','Byte input and initialization','Bound byte transfers and separate startup effects from ordinary calls.',['byte-streams','class-initialization'])
module('dsa-in-java','Range scans and search trees','Prove pointer movement, preserve tree membership and bound retained candidates.',['two-pointers','sliding-window','binary-search-tree','heap-top-k'])
module('dsa-in-java','Connectivity, distances and dependencies','Use the graph model and edge-cost preconditions that match the result.',['union-find','dijkstra','topological-sort'])
module('dsa-in-java','Branching choices','Restore temporary state and count result storage as well as search work.',['backtracking'])
module('java-exercises','Array and text boundary checks','Check adjacent duplicates and an explicit text-normalization policy.',['array-string-exercises'])
module('java-projects','Validated file imports','Reject malformed batches before exposing a completed summary.',['manifest-project'])
# Cross-list existing runnable examples without duplicating pages or their canonical section.
module('java-examples','Input, collections and asynchronous results','Open complete programs in their relevant subject sections.',['console-input','unicode-encoding','enum-collections','completable-future','manifest-project'])

paths={e['path'] for e in entries}
for e in entries:
    if e['path'].startswith('java/'):
        for m in e['data'].get('modules',[]):
            assert all(p in paths for p in m['lessons']), (e['path'],m)
        for link in re.findall(r'href="/([^"#]+)',e['body']): assert link in paths,(e['path'],link)
(ROOT/'src/data/fixtures.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
new=[lookup[p] for p in added]
report={'added':added,'expanded':expanded,'newPages':len(added),'expandedPages':len(expanded),'newArticleWordsIncludingCode':sum(len(re.sub('<[^>]+>',' ',e['body']).split()) for e in new),'newJavaPages':len([e for e in entries if e['path'].startswith('java/')]),'newQuizzes':0,'localOnly':True}
(OUT/'java-next-content-batch.json').write_text(json.dumps(report,indent=2))
(OUT/'aitrove-java-next-content.json').write_text(json.dumps([lookup[p] for p in added+expanded]+[e for e in entries if e['type']=='subject' and e['path'].startswith('java/')],ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report))
