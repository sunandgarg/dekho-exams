import json, html, re, uuid, pathlib, copy
ROOT=pathlib.Path(__file__).resolve().parents[1]
entries=json.loads((ROOT/'src/data/fixtures.json').read_text())
by_path={entry['path']:entry for entry in entries}
new=[]
def p(text): return '<p>'+text+'</p>'
def block(code,lang='java'):return '<pre><code class="language-'+lang+'">'+html.escape(code.strip('\n'),quote=False)+'</code></pre>'
def add(slug,title,definition,sections,program,output,cost,mistakes,related,subject='java-advanced'):
 body=p(definition)
 for heading,paragraphs in sections:
  body+='<h2>'+heading+'</h2>'+''.join(p(text) for text in paragraphs)
 body+='<h2>Working program</h2>'+block(program)+'<h3>Output</h3>'+block(output,'text')
 body+='<h2>Cost and design choices</h2>'+''.join(p(text) for text in cost)
 body+='<h3>Common Mistakes</h3><ul>'+''.join('<li>'+text+'</li>' for text in mistakes)+'</ul>'
 template=copy.deepcopy(by_path['java/arrays'])
 path='java/'+slug
 template.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),path=path,title=title,summary=definition,type='article',body=body,subject=subject,tags=['java',slug],sort_order=20+len(new),difficulty='Intermediate',updated_at='2026-09-28T10:00:00+00:00')
 section={'java':'java/java','java-advanced':'java/advanced-java','java-collections':'java/java-collections','java-dsa':'java/dsa-in-java'}[subject]
 template['data'].update(section_path=section,reading_minutes=max(3,round(len(re.sub('<[^>]+>',' ',body).split())/160)),related=[{'path':'java/'+ref,'title':label} for ref,label in related],content_format='html',java_version='8+')
 if path in by_path:
  old=by_path[path];template['id']=old['id'];template['sort_order']=old['sort_order'];old.update(template)
 else:entries.append(template);by_path[path]=template
 new.append(path)

add('hashmap','Java HashMap: keys, collisions, and update operations',
'HashMap associates keys with values through hash buckets; key equality decides whether an insertion creates a mapping or replaces an existing one.',
[('Lookup is a two-part contract',[
'Hashing narrows the search. Equality finishes it. Two keys can share a hash without being equal, so a collision does not mean one entry overwrites the other. Read <a href="/java/equals-hashcode">equals and hashCode</a> before introducing an application object as a key.',
'A receipt counter needs one entry per payment status. Updating an existing status should change its count, not append another row. A map expresses that requirement directly; a <a href="/java/arraylist">list</a> would require a search before each update.',
'HashMap does not promise iteration order. An observed order in a small test is not an API contract. Use <a href="/java/linkedhashmap">LinkedHashMap</a> for encounter order or <a href="/java/treemap">TreeMap</a> for key ordering. Sorting the display and choosing the storage structure are separate decisions.'
]),('Update without an unnecessary second lookup',[
'merge supplies the first value when a key is absent and combines it with the existing non-null value otherwise. The counter uses Integer::sum. The merge operation on a plain HashMap is not an atomic update shared safely among threads.',
'Null needs care. get returns null for both a missing mapping and an entry explicitly mapped to null; containsKey distinguishes those states. This counter never stores null, which removes that ambiguity from its caller contract.',
'The counters describe an in-memory batch. They are not an audit ledger: process exit loses them, repeated delivery increments them again, and concurrent updates need a different ownership model.'
])],'''import java.util.HashMap;
import java.util.Map;

public class ReceiptCounter {
    public static void main(String[] args) {
        Map<String, Integer> counts = new HashMap<>();
        String[] statuses = {"paid", "declined", "paid", "pending", "paid"};
        for (String status : statuses) {
            counts.merge(status, 1, Integer::sum);
        }
        System.out.println("paid=" + counts.getOrDefault("paid", 0));
        System.out.println("refunded=" + counts.getOrDefault("refunded", 0));
        System.out.println("statuses=" + counts.size());
    }
}''','paid=3\nrefunded=0\nstatuses=3',[
'For well-distributed hashes, each map update has expected constant lookup cost. With n input statuses and k distinct statuses, the batch requires expected O(n) time and O(k) stored entries. String hashing and equality themselves depend on key length, so treating arbitrarily long keys as free work would be misleading.',
'Capacity is the bucket budget, not the number of mappings already present. Growth allocates storage and moves entries. Excessive preallocation also costs memory and can make iteration expensive. Measure the actual batch size before selecting a capacity.',
'A key whose equality-relevant fields change after insertion may no longer be found by a later lookup. Store stable identifiers or immutable key objects. Resizing a map does not repair a broken key contract.'
],['Do not depend on HashMap iteration order in tests or API responses.','Do not mutate keys after inserting them.','Do not assume merge on HashMap is safe for simultaneous writers.','Do not let Integer counters wrap silently when batch totals can exceed their range.'],[('equals-hashcode','Equality and hash keys'),('hashset','Deduplication with HashSet'),('linkedhashmap','Predictable encounter order')],'java-collections')

add('hashset','Java HashSet: deduplication and equality',
'HashSet stores distinct elements using hashing and equality, with no promised iteration order.',
[('Choose what counts as the same value',[
'Deduplication is a policy. Are two receipt IDs equal when their letter case differs? Are leading spaces meaningful? Decide before inserting values. A set can enforce your chosen equality rule; it cannot infer the business meaning of an identifier.',
'This import treats trimmed receipt strings as case-sensitive identifiers. It rejects an empty identifier and counts duplicates. It does not normalise letter case, because changing a case-sensitive provider ID could incorrectly merge two receipts.',
'A HashSet permits a null element, but this pipeline does not. Restricting inputs makes downstream work easier: a reader knows every stored value is a usable identifier. For original encounter order, choose LinkedHashSet instead of sorting after each insertion.'
]),('Use the result of add',[
'add returns false when an equal element already exists. Checking contains and then calling add repeats the search and creates a wider race window if the code is later shared incorrectly between threads.',
'If the imported record is a custom type, its <a href="/java/equals-hashcode">equality and hash contract</a> determine deduplication. Object identity is often the wrong rule for a record reconstructed from a file.',
'A process-local set is not a permanent idempotency store. Separate service instances have separate sets, and restarting a process clears its history. Use a durable uniqueness constraint when accepting an ID twice would create an external side effect.'
])],'''import java.util.HashSet;
import java.util.Set;

public class ReceiptDeduplicator {
    public static void main(String[] args) {
        String[] importedIds = {" rcpt-41 ", "rcpt-82", "rcpt-41", ""};
        Set<String> acceptedIds = new HashSet<>();
        int duplicates = 0;
        int rejected = 0;
        for (String rawId : importedIds) {
            String receiptId = rawId.trim();
            if (receiptId.isEmpty()) {
                rejected++;
            } else if (!acceptedIds.add(receiptId)) {
                duplicates++;
            }
        }
        System.out.println("accepted=" + acceptedIds.size());
        System.out.println("duplicates=" + duplicates);
        System.out.println("rejected=" + rejected);
    }
}''','accepted=2\nduplicates=1\nrejected=1',[
'Processing n bounded-length IDs takes expected O(n) time with well-distributed hashes and O(k) entry storage for k distinct IDs. Trimming can allocate new strings; account for input text length when estimating a large import.',
'HashSet uses hashing storage rather than a sorted index. If the main operation is checking membership, that is a sensible fit. If the application needs nearest values, ordered ranges, or a floor entry, study <a href="/java/treemap">ordered maps</a> instead.',
'An unbounded stream of distinct IDs creates an unbounded memory requirement. A maximum batch size, retention window, or external store is a design decision the collection will not make for you.'
],['Do not assert the order of HashSet.toString().','Do not use mutable fields in an element’s hash while it is stored.','Do not claim process-local deduplication guarantees exactly-once delivery.'],[('hashmap','Counting with HashMap'),('equals-hashcode','Element equality'),('iterators','Collection iteration')],'java-collections')

add('treemap','Java TreeMap: ordered keys and range views',
'TreeMap stores mappings in key order and exposes range and nearest-key operations through the NavigableMap contract.',
[('Search an ordered domain',[
'Hashing answers exact lookup. A pricing schedule has a different question: which threshold is the greatest one not above this order quantity? floorEntry answers it directly. The keys are thresholds, not individual purchases.',
'Natural ordering works for integer thresholds. A custom comparator changes the definition of key uniqueness: keys that compare as zero occupy the same mapping even if equals says otherwise. Keep those contracts consistent unless the disagreement is intentional and documented.',
'For a case-insensitive string comparator, two differently capitalised strings can address the same mapping. This can be useful for a lookup, but it is unsuitable when the original identifiers must remain distinct. Compare the contract with <a href="/java/hashmap">HashMap</a> before replacing a storage type.'
]),('Range views share storage',[
'subMap produces a view of the parent map, not an independent snapshot. Changes through either side can be visible through the other. Copy into a new map when a reader needs a stable snapshot owned by that reader.',
'The four-argument overload makes inclusive and exclusive endpoints explicit. A threshold exactly equal to the lower bound belongs in an inclusive range; one equal to an exclusive upper bound does not.',
'floorEntry can return null. An order below the smallest configured threshold has no matching rule. The program checks that case rather than converting absence into a zero price.'
])],'''import java.util.Map;
import java.util.NavigableMap;
import java.util.TreeMap;

public class QuantityPricing {
    public static void main(String[] args) {
        NavigableMap<Integer, Integer> centsPerUnit = new TreeMap<>();
        centsPerUnit.put(1, 240);
        centsPerUnit.put(10, 220);
        centsPerUnit.put(50, 195);
        int quantity = 24;
        Map.Entry<Integer, Integer> price = centsPerUnit.floorEntry(quantity);
        if (price == null) {
            throw new IllegalArgumentException("Quantity must meet a threshold");
        }
        System.out.println("unitCents=" + price.getValue());
        System.out.println("thresholds=" + centsPerUnit.subMap(10, true, 50, false).keySet());
    }
}''','unitCents=220\nthresholds=[10]',[
'Key lookup, insertion, and removal require O(log n) tree work for n entries, assuming key comparisons have bounded cost. Returning a range view does not copy every mapping. Traversing k selected mappings still costs work proportional to those visited entries.',
'Tree nodes allocate references and metadata per entry. A sorted array can use less memory for an immutable small schedule, but insertion into that representation requires moving elements. Match the representation to the update rate.',
'Prices use integer cents here so the example isolates threshold selection. A real multi-currency pricing engine must define currency, rounding, tax, and bounds; <a href="/java/bigdecimal">BigDecimal</a> addresses decimal arithmetic, not those policy choices.'
],['Do not dereference a missing floorEntry.','Do not assume a subMap is a detached copy.','Do not insert keys that your comparator cannot compare, including null when unsupported.'],[('hashmap','Exact-key lookup'),('bigdecimal','Decimal amounts'),('sorting','Comparator rules')],'java-collections')

add('linkedhashmap','Java LinkedHashMap: encounter order and a bounded cache model',
'LinkedHashMap combines hash-based key lookup with a linked encounter order that can follow insertion or access.',
[('Order is part of the contract',[
'A plain <a href="/java/hashmap">HashMap</a> deliberately leaves ordering unspecified. LinkedHashMap maintains an order so an application can produce repeatable output or identify the least recently accessed entry.',
'Insertion order is the default. Access order requires the constructor’s third argument to be true. Reading an existing entry then moves it to the most recently accessed end. That read can change structural iteration state; it is not a harmless shared read for concurrent code.',
'The program models a two-entry cache. It overrides removeEldestEntry to remove an old entry after a new mapping exceeds the capacity. Reading account-a before inserting account-c means account-b becomes the eviction candidate.'
]),('Bounded entries are not bounded bytes',[
'A maximum entry count only bounds the number of mappings. One value might contain a large payload. Production caches need a memory budget or weighted sizing when payload sizes vary.',
'An eviction policy does not supply expiration, load coalescing, failure caching, or thread safety. This small model is useful for understanding access order. It is not a replacement for a tested cache library when a service has those requirements.',
'Cache values also need an ownership rule. A cached mutable object can be changed by any caller holding its reference. If the cached value is a configuration snapshot, prefer immutable content or return a defensive copy.'
])],'''import java.util.LinkedHashMap;
import java.util.Map;

public class AccessOrderedCache {
    public static void main(String[] args) {
        Map<String, String> cache = new LinkedHashMap<String, String>(4, 0.75f, true) {
            @Override
            protected boolean removeEldestEntry(Map.Entry<String, String> eldest) {
                return size() > 2;
            }
        };
        cache.put("account-a", "active");
        cache.put("account-b", "paused");
        cache.get("account-a");
        cache.put("account-c", "active");
        System.out.println(cache.keySet());
        System.out.println("account-b=" + cache.containsKey("account-b"));
    }
}''','[account-a, account-c]\naccount-b=false',[
'Expected hash lookup cost remains constant with good key distribution. Maintaining encounter links adds per-entry references and constant bookkeeping for an access-order move. Iterating n entries follows encounter links in O(n) time.',
'The demonstration stores two entries, giving O(1) entry-count space under this fixed limit. For a configured maximum k, storage is O(k) entries plus the memory owned by their keys and values.',
'Do not hold an iterator while repeatedly calling get on the same access-ordered map. A design that needs both traversal and updates should define a snapshot or lock strategy explicitly.'
],['Do not call this cache thread-safe.','Do not confuse containsKey with an access-order get operation.','Do not interpret an entry-count limit as a guaranteed byte limit.'],[('hashmap','Map updates'),('iterators','Mutation during iteration'),('threads','Shared state')],'java-collections')

add('priorityqueue','Java PriorityQueue: ordered removal without a sorted list',
'PriorityQueue keeps a least-priority element at its head according to natural ordering or a supplied comparator; its iterator is not a sorted traversal.',
[('Priority is a removal rule',[
'A queue of support tickets needs to pick the highest urgency first, with an older sequence number breaking ties. Define that comparator once. The program treats a smaller urgency value as more urgent and then compares the sequence.',
'The tie-breaker matters. Equal comparator results do not give a stable arrival-order guarantee. If FIFO ordering within a priority group is required, include a monotonic sequence and consider what happens when its range is exhausted.',
'Use Integer.compare, Long.compare, or comparator helpers instead of subtracting values. Subtraction can overflow and reverse an ordering decision at the edges of the numeric range.'
]),('Read through poll',[
'poll removes the current head. Repeating it produces the comparator’s removal order. A for-each loop, toString, or iterator over the queue does not promise that order.',
'The queue holds references. Changing a ticket’s priority after inserting it does not automatically repair its heap position. Keep ordering fields immutable, or remove and reinsert an updated ticket.',
'PriorityQueue rejects null elements and is not a blocking concurrent handoff mechanism. A task scheduler may need a <a href="/java/executors">worker service</a>, bounded admission, cancellation, and a clear shutdown policy in addition to selecting the next item.'
])],'''import java.util.Comparator;
import java.util.PriorityQueue;

public class SupportTicketQueue {
    static final class Ticket {
        final int urgency;
        final long sequence;
        final String id;
        Ticket(int urgency, long sequence, String id) {
            this.urgency = urgency;
            this.sequence = sequence;
            this.id = id;
        }
    }
    public static void main(String[] args) {
        Comparator<Ticket> order = Comparator.comparingInt((Ticket ticket) -> ticket.urgency)
                .thenComparingLong(ticket -> ticket.sequence);
        PriorityQueue<Ticket> tickets = new PriorityQueue<>(order);
        tickets.add(new Ticket(2, 1, "billing-17"));
        tickets.add(new Ticket(1, 2, "login-42"));
        tickets.add(new Ticket(1, 3, "login-43"));
        while (!tickets.isEmpty()) {
            System.out.println(tickets.poll().id);
        }
    }
}''','login-42\nlogin-43\nbilling-17',[
'Inserting and polling an element take O(log n) heap work for n elements, excluding comparator cost. Peeking at the head is O(1). Searching for a particular arbitrary element still requires O(n) work.',
'Each ticket is stored once, so the queue occupies O(n) element-reference storage. A stream of tickets arriving faster than they are processed will keep growing unless admission is bounded elsewhere.',
'For processing an entire immutable batch in sorted order, <a href="/java/sorting">sorting the batch once</a> may be easier to reason about. A priority queue fits repeated insertion mixed with next-item removal.'
],['Do not expect iterator order to be priority order.','Do not mutate comparator fields while an element is queued.','Do not use arithmetic subtraction as a comparator.'],[('sorting','Sorting and comparators'),('arraydeque','FIFO queues'),('executors','Worker lifecycle')],'java-collections')

add('iterators','Java Iterator and ListIterator: traversal and controlled edits',
'An Iterator advances through a collection without requiring callers to know how that collection stores elements; ListIterator adds positional editing and reverse traversal for lists.',
[('Traversal and mutation have separate rules',[
'Calling next returns the next element and changes iterator state. Calling remove then removes that returned element when the implementation supports removal. Calling remove twice without another next is not valid.',
'An enhanced for loop uses an iterator for most collections, but does not expose that iterator’s remove method. Removing through the collection inside that loop can invalidate traversal. Use an explicit iterator when the traversal itself owns removals.',
'Fail-fast exceptions help detect misuse. They are not a synchronisation protocol and are not guaranteed to detect every race. A program must be correct without relying on ConcurrentModificationException to police competing writers.'
]),('Use the cursor for a linked list',[
'A list iterator has a cursor between elements. After next, add inserts before the element that would be returned by the next next call. It does not replace the last returned element; set performs that replacement.',
'For a <a href="/java/linkedlist">LinkedList</a>, repeatedly calling get(index) during traversal can accumulate quadratic work. An iterator follows nodes instead. Locating the initial cursor still has traversal cost, even when the later local edit is cheap.',
'The cleanup program removes failed stage markers, then inserts a quality stage at a known cursor. It intentionally does not share the list with another thread. Ownership is what makes the small editing sequence easy to reason about.'
])],'''import java.util.Arrays;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.ListIterator;

public class WorkflowIterator {
    public static void main(String[] args) {
        LinkedList<String> stages = new LinkedList<>(Arrays.asList("received", "failed:scan", "packed"));
        Iterator<String> cleanup = stages.iterator();
        while (cleanup.hasNext()) {
            if (cleanup.next().startsWith("failed:")) {
                cleanup.remove();
            }
        }
        ListIterator<String> editor = stages.listIterator(1);
        editor.add("quality-check");
        System.out.println(stages);
        System.out.println(editor.next());
    }
}''','[received, quality-check, packed]\npacked',[
'Traversing n linked nodes takes O(n) time with O(1) cursor state. Removing the current linked node is constant link work. For an <a href="/java/arraylist">ArrayList</a>, iterator removal can shift later elements; many individual removals can be expensive.',
'Initial listIterator(index) positioning on a linked list traverses toward that index. Describing every iterator edit as constant total cost hides this setup expense.',
'If the goal is a separate filtered result, copying accepted values into a new list preserves the original. That uses O(k) result space for k accepted values and makes the ownership boundary explicit.'
],['Do not call remove before next or twice for the same returned element.','Do not modify the collection independently while its iterator is in use.','Do not treat fail-fast behavior as thread safety.'],[('linkedlist','Linked-node operations'),('arraylist','Array-backed lists'),('streams','Filtering into a result')],'java-collections')

add('equals-hashcode','Java equals and hashCode: stable value keys',
'equals defines whether two objects represent the same value, while hashCode supplies the hash used by hash-based collections to narrow a lookup.',
[('Make identity explicit',[
'Two objects can represent the same shipment identifier while occupying different allocations. Reference equality checks whether they are the same object. Value equality checks the domain fields you choose. Mixing those questions is a common source of duplicate keys.',
'The key below uses carrier code and tracking number together. A tracking number alone might not be globally unique. Both fields are final strings, and the constructor rejects null, so the equality decision remains stable after insertion.',
'The equals contract requires reflexivity, symmetry, transitivity, consistency, and a false result against null. Equal objects must have equal hash codes. The converse is false: unequal objects may collide, and a <a href="/java/hashmap">HashMap</a> must still compare them correctly.'
]),('Keep inheritance out of a value key',[
'An extensible value class can make symmetry difficult if a subclass adds another equality field. The example uses a final class and compares only its own declared value type. This avoids promising equality across an inheritance hierarchy.',
'Objects.hash is readable but uses a varargs array and boxing for primitive arguments. For a hot key type, a direct hash calculation may reduce allocation. Measure before replacing a clear implementation with a hand-tuned one.',
'The map inserts one ShipmentKey and retrieves with a separately constructed equal key. That is the actual behavior a parsed request or imported row needs. Testing only the same reference would miss a broken value-equality implementation.'
])],'''import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

public class ShipmentKeyLookup {
    static final class ShipmentKey {
        private final String carrier;
        private final String tracking;
        ShipmentKey(String carrier, String tracking) {
            this.carrier = Objects.requireNonNull(carrier);
            this.tracking = Objects.requireNonNull(tracking);
        }
        @Override
        public boolean equals(Object candidate) {
            if (this == candidate) return true;
            if (!(candidate instanceof ShipmentKey)) return false;
            ShipmentKey other = (ShipmentKey) candidate;
            return carrier.equals(other.carrier) && tracking.equals(other.tracking);
        }
        @Override
        public int hashCode() {
            return 31 * carrier.hashCode() + tracking.hashCode();
        }
    }
    public static void main(String[] args) {
        Map<ShipmentKey, String> state = new HashMap<>();
        state.put(new ShipmentKey("DX", "track-309"), "in-transit");
        System.out.println(state.get(new ShipmentKey("DX", "track-309")));
        System.out.println(state.size());
    }
}''','in-transit\n1',[
'Equality can require comparing all relevant key text, so its work is proportional to those text lengths in the worst case. Hash-based collection lookup is expected constant bucket work only when hashes are well distributed; that statement does not remove the cost of computing a hash or checking equality.',
'Immutable fields prevent the inserted key from drifting to a new hash. Mutating a key can leave it physically stored under its old bucket decision while future lookups compute a different one.',
'Do not place a large mutable payload in the identity contract unless that is the actual meaning of the key. A smaller stable identifier reduces both comparison work and the risk of accidental identity changes.'
],['Override hashCode whenever value equals is overridden.','Test equal but separately constructed keys, null, and unequal keys.','Do not use array identity when the intended comparison is array contents.','Do not assume final on a reference makes the referenced object immutable.'],[('hashmap','HashMap lookup'),('hashset','Set membership'),('static-final','What final guarantees')],'java')

add('pass-by-value','Java pass-by-value: references and mutation',
'Java passes argument values into method parameters; for an object argument, the copied value is a reference to that object.',
[('A copied reference still reaches one object',[
'The caller and callee can hold different variables whose values point to the same mutable list. Mutating that list through either reference changes the shared object. Reassigning the callee’s parameter only changes the callee’s local variable.',
'No caller variable is rebound by that reassignment. The parameter is not an alias for the caller’s variable slot. This distinction explains why a method can append to a list but cannot replace the caller’s list by assigning a new one to its parameter.',
'Primitive arguments are copied too. Incrementing an int parameter does not update the caller’s int. Wrapping the int in a mutable object permits shared mutation of that object, but does not change the parameter-passing rule.'
]),('Choose an ownership boundary',[
'The program deliberately combines a mutation and a local reassignment. Only the mutation survives when observed by the caller. The second addition lands in a new list that the caller never receives.',
'A method named enrich should document whether it changes its input or returns another result. If the input must remain unchanged, copy the list and return that copy. A shallow copy separates list structure, not mutable element objects.',
'Returning a result is often clearer than assigning to parameters. It makes the new owner visible at the call site and supports tests that verify both the output and the unchanged input. For more on copying costs, read <a href="/java/arraylist">array-backed list ownership</a>.'
])],'''import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class DeliveryArgumentOwnership {
    static void appendThenRebind(List<String> events) {
        events.add("packed");
        events = new ArrayList<>();
        events.add("local-only");
    }
    public static void main(String[] args) {
        List<String> deliveryEvents = new ArrayList<>(Arrays.asList("received"));
        appendThenRebind(deliveryEvents);
        System.out.println(deliveryEvents);
    }
}''','[received, packed]',[
'Copying a reference is constant work. Copying n list element references into a new ArrayList requires O(n) time and O(n) reference storage. Deep copying depends on the contents and cannot be described by the list length alone.',
'A shared reference can keep a large object reachable even when the original owner drops its own reference. Garbage collection follows reachability, not the apparent age of a local variable.',
'This example has one thread. A shared mutable reference also creates a concurrency question when threads are involved; pass-by-value does not prevent races or establish visibility.'
],['Do not call Java pass-by-reference.','Do not expect parameter reassignment to replace the caller’s object variable.','Do not describe a shallow collection copy as a copy of every element object.'],[('encapsulation','Controlling mutable state'),('arraylist','List copying'),('threads','Shared mutation')],'java')

add('static-final','Java static and final: storage, ownership, and constants',
'static associates a member with a class rather than a particular instance; final prevents reassignment of a variable or further extension of a method or class, depending on where it is applied.',
[('Separate storage from mutability',[
'A static field is shared by uses of that class in its defining class loader. An instance field belongs to one object. Neither choice automatically supplies a lock, a memory barrier, or protection from competing writers.',
'A final list reference cannot be reassigned after its permitted initialization. The list itself can still change. An immutable view blocks mutation through that view, but does not stop a separate owner from changing the backing collection.',
'The configuration below copies the caller’s list before wrapping it. The copy removes structural sharing with the caller. Because the elements are strings, element mutation is not a concern in this example; replacing strings in the original list also does not change the copied list.'
]),('Constants can outlive a rebuild',[
'A static final primitive or String initialized with a compile-time constant expression can be inlined into client bytecode. Recompiling only the library after changing that value can leave an already compiled client using the previous value.',
'Use a method or runtime configuration when a value must change without rebuilding its consumers. A timeout loaded from configuration is not the same contract as a fixed protocol constant.',
'Final classes and methods constrain inheritance. They do not imply that every field is immutable, and final alone does not turn a mutable object into a value key. Review <a href="/java/equals-hashcode">equality fields</a> separately.'
])],'''import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

public class NotificationConfiguration {
    static final int MAX_ATTEMPTS = 3;
    static final class Settings {
        private final List<String> channels;
        Settings(List<String> channels) {
            this.channels = Collections.unmodifiableList(new ArrayList<>(channels));
        }
        List<String> channels() { return channels; }
    }
    public static void main(String[] args) {
        List<String> requested = new ArrayList<>(Arrays.asList("email"));
        Settings settings = new Settings(requested);
        requested.add("sms");
        System.out.println(settings.channels());
        System.out.println(MAX_ATTEMPTS);
    }
}''','[email]\n3',[
'Creating the snapshot costs O(n) time and O(n) reference storage for n channels. Wrapping the copy with an unmodifiable view adds a small wrapper rather than another full copy.',
'A static collection remains reachable while its class and field remain reachable. Treat a growing static map as retained application memory, not as temporary request state.',
'Final field initialization has specific publication guarantees, but sharing an incompletely constructed object or mutating referenced objects still needs care. For mutable cross-thread state, define a <a href="/java/threads">synchronisation policy</a>.'
],['Do not equate final references with immutable objects.','Do not wrap a caller’s mutable list and call it a detached snapshot.','Do not use static fields as unbounded per-request storage.'],[('encapsulation','State boundaries'),('pass-by-value','Copied references'),('threads','Thread visibility')],'java')

add('polymorphism','Java polymorphism: overriding and dispatch',
'Polymorphism lets a caller invoke an instance method through a common type while the runtime object selects the overridden implementation.',
[('Dispatch follows the object',[
'A billing caller needs a fee calculation, not knowledge of each payment channel’s implementation class. The PaymentFee interface establishes that contract. The object stored in its reference determines which instance implementation runs.',
'Overloading is different. When several methods have the same name but different parameter types, the compiler selects a signature from the declared types at the call site. Overriding chooses the implementation of that selected instance method at runtime.',
'Static methods do not participate in instance overriding. Fields are also resolved differently from virtual method calls. Designing an API around a shared method contract avoids expecting field access to behave like overridden behavior.'
]),('Preserve the caller’s assumptions',[
'Both fee implementations accept nonnegative cents and reject invalid values. A substitute implementation should not silently accept a different unit or introduce surprising mutation into a calculation that callers regard as a query.',
'The cash calculation uses integer arithmetic with a minimum fee. The transfer calculation is fixed. These are teaching policies, not payment provider rates. Keeping policy values visible lets a test exercise the branch boundary.',
'Prefer an interface when implementations have unrelated storage or lifecycles. Use inheritance when the parent genuinely owns shared behavior and its invariants remain valid in every subtype. <a href="/java/interfaces">Interface contracts</a> and <a href="/java/inheritance">inheritance boundaries</a> address those decisions separately.'
])],'''public class PaymentFeeDispatch {
    interface PaymentFee {
        int feeCents(int amountCents);
    }
    static final class CashFee implements PaymentFee {
        public int feeCents(int amountCents) {
            if (amountCents < 0) throw new IllegalArgumentException("Negative amount");
            return Math.max(10, amountCents / 100);
        }
    }
    static final class TransferFee implements PaymentFee {
        public int feeCents(int amountCents) {
            if (amountCents < 0) throw new IllegalArgumentException("Negative amount");
            return 25;
        }
    }
    public static void main(String[] args) {
        PaymentFee[] policies = {new CashFee(), new TransferFee()};
        for (PaymentFee policy : policies) {
            System.out.println(policy.feeCents(1200));
        }
    }
}''','12\n25',[
'The batch makes n calls for n policies, so the visible traversal is O(n), with O(1) extra loop state. The actual calculation cost belongs to each implementation. An interface does not promise a particular algorithmic complexity unless its contract states one.',
'Dispatch and JIT optimisation are implementation concerns. Do not assume every virtual call has a fixed expensive penalty, or that an interface abstraction requires creating another object for each call.',
'If a fee calculation later needs remote I/O, separate that work from a local arithmetic contract. A caller that expects a quick pure calculation should not unknowingly inherit retries and network timeouts.'
],['Do not confuse overloading with overriding.','Use @Override when implementing an inherited method to catch signature mistakes.','Do not weaken validation or change units in a replacement implementation.'],[('interfaces','Method contracts'),('inheritance','Subtype design'),('lambdas','Function contracts')],'java')

add('enums','Java enums: finite states without ordinal storage',
'An enum defines a fixed set of named instances that can carry fields and behavior while remaining a distinct Java type.',
[('Names are safer than magic integers',[
'An order status should not be any arbitrary integer. An enum lets a method accept only the defined state type. That catches accidental mixing of status values with unrelated counts or IDs at compile time.',
'The enum below assigns an explicit external code to each state. It does not persist ordinal(), because ordinal is the declaration position. Reordering or adding constants can change that position without changing the intended business meaning.',
'valueOf expects the exact constant name and throws if the name is not present. A client-facing parser often needs stable external codes, case rules, and an unknown-value policy rather than directly exposing Java constant names.'
]),('Transitions still need validation',[
'A finite list of states does not prove every transition is valid. Moving from NEW to PAID may be allowed, while moving from CANCELLED to PAID may require a separate recovery policy.',
'The demonstration validates one transition before printing its external code. It keeps the transition policy next to the state logic so unsupported cases are visible. A real order system would also need durable transaction boundaries around state changes.',
'Enum values are single instances, but their fields could be mutable if designed that way. Avoid per-order data inside enum constants. Store an order’s data in its own object and let the enum describe only its state.'
])],'''public class OrderStateCodes {
    enum OrderState {
        NEW("new"), PAID("paid"), CANCELLED("cancelled");
        private final String externalCode;
        OrderState(String externalCode) { this.externalCode = externalCode; }
        String externalCode() { return externalCode; }
        boolean canMoveTo(OrderState next) {
            return this == NEW && (next == PAID || next == CANCELLED);
        }
    }
    public static void main(String[] args) {
        OrderState current = OrderState.NEW;
        OrderState requested = OrderState.PAID;
        if (!current.canMoveTo(requested)) {
            throw new IllegalStateException("Rejected order transition");
        }
        System.out.println(requested.externalCode());
        System.out.println(OrderState.CANCELLED.canMoveTo(OrderState.PAID));
    }
}''','paid\nfalse',[
'Comparing enum instances with == is a constant identity comparison. A small explicit transition check also has constant cost. A larger workflow might use an EnumSet or transition map, which keeps rules readable without a long branch chain.',
'The enum instances are shared, not allocated once per order. An order field holds a reference to the selected instance. Per-order payload storage belongs elsewhere.',
'Adding a new constant is an API evolution event. Consumers with exhaustive assumptions, stored external codes, or switch defaults need a deliberate compatibility plan.'
],['Do not persist ordinal as a stable business identifier.','Do not put mutable per-request data in enum fields.','Do not use an unchecked valueOf call as the entire external input validation strategy.'],[('classes-objects','Object state'),('exceptions','Input failures'),('static-final','Shared fields')],'java')

add('packages','Java packages and access control: a boundary you can compile',
'A package groups named Java types and participates in type identity and access control; importing a type shortens its name but does not grant access to it.',
[('The name includes the package',[
'com.aitrove.billing.Invoice and com.aitrove.shipping.Invoice are different types. Their simple class names match, but their fully qualified names do not. Importing one does not combine the two APIs.',
'The source declares its package on the first non-comment declaration line. javac -d chooses where compiled class files are written and creates the matching package directory structure. The runtime entry name must include the package.',
'Public exposes a top-level type outside its package. Package-private, expressed by omitting an access modifier, limits ordinary access to that package. Private members belong to the enclosing class access rules. Protected has package and subclass rules; it is not simply public for every subclass object reference.'
]),('Compile and run with the full name',[
'Save this program as BillingPackageCheck.java. From that file’s directory, run javac -d build BillingPackageCheck.java, then java -cp build com.aitrove.billing.BillingPackageCheck.',
'The program prints its declared package and validates an invoice count. The package statement does not move the source file by itself. A normal build tool keeps source directories consistent with package names to make lookup predictable.',
'Package names are not a security sandbox. They organise API access during ordinary compilation and runtime linkage. A service still needs authentication and authorisation for external requests.'
])],'''package com.aitrove.billing;

public class BillingPackageCheck {
    static int validatedCount(int invoiceCount) {
        if (invoiceCount < 0) throw new IllegalArgumentException("Negative count");
        return invoiceCount;
    }
    public static void main(String[] args) {
        System.out.println(BillingPackageCheck.class.getPackage().getName());
        System.out.println(validatedCount(4));
    }
}''','com.aitrove.billing\n4',[
'Access checks are not a collection traversal algorithm; assigning an O(n) runtime cost to an import statement would be meaningless. The business calculation shown performs a constant amount of work and uses constant local space.',
'Package-private types can keep implementation details out of a public API. That reduces the surface callers depend on and makes later refactoring less likely to break consumers.',
'For modular applications, module exports add another visibility boundary. This lesson targets ordinary Java 8 package behavior; it does not pretend package declarations alone implement the module system introduced later.'
],['Do not run a packaged class using only its simple name.','Do not assume import overrides access restrictions.','Do not place unrelated public classes in one source file with conflicting filenames.'],[('setup','Compile and run Java'),('encapsulation','API boundaries'),('static-final','Class members')],'java')

add('generics','Java generics: invariance, bounds, and type erasure',
'Generics let declarations express relationships between types so the compiler can reject incompatible values before execution.',
[('Parameterise the contract',[
'A List&lt;Invoice&gt; states what the list accepts and what its reads return. A raw List discards that relationship and moves errors toward runtime casts. Generic type checking does not validate business rules such as invoice currency or an allowed amount range.',
'List&lt;Integer&gt; is not a subtype of List&lt;Number&gt;. If it were, a caller receiving the supposed Number list could insert a Double into an Integer list. This is invariance, and it protects writes.',
'Arrays behave differently: reference arrays are covariant and perform runtime store checks. Do not apply the array assignment rule to a generic list. It describes a different safety model.'
]),('Use a bound for the direction of data',[
'A source declared as List&lt;? extends Number&gt; can provide Number values, but you cannot safely add an arbitrary Number to it. Its actual element type might be Integer. A destination declared as List&lt;? super Integer&gt; can accept Integer values, while a read can only promise Object.',
'The program transfers integers into a Number destination. The upper-bounded source supplies compatible input and the lower-bounded destination accepts the copied integers. This keeps callers flexible without resorting to raw types.',
'Most generic information is erased from ordinary runtime object types. You cannot use new T(), create a normal new List&lt;String&gt;[] array, or distinguish List&lt;String&gt; from List&lt;Integer&gt; with an instanceof test.'
])],'''import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class TypedBatchTransfer {
    static void transfer(List<? extends Integer> source, List<? super Integer> destination) {
        for (Integer shipmentCount : source) {
            destination.add(shipmentCount);
        }
    }
    public static void main(String[] args) {
        List<Integer> dailyCounts = Arrays.asList(4, 7, 2);
        List<Number> report = new ArrayList<>();
        transfer(dailyCounts, report);
        System.out.println(report);
    }
}''','[4, 7, 2]',[
'The transfer visits n source elements and appends n references. With an ArrayList destination, total append work is amortized O(n), and the destination needs O(n) additional reference storage. Generic bounds do not eliminate allocation or boxing.',
'List&lt;Integer&gt; stores references to boxed values, not an int array. For large numeric workloads, a primitive array or primitive stream can avoid some wrapper overhead.',
'Erasure does not make generic declarations useless: it places their main safety checks at compilation. Keep <a href="/java/collection-choices">collection contracts</a> typed all the way to the boundary, and validate untrusted runtime data separately.'
],['Do not use raw types to silence a type mismatch.','Do not assume a wildcard source accepts writes of its upper bound.','Do not cast a list to a different element type and call that conversion.'],[('collection-choices','Collection contracts'),('arraylist','Reference storage'),('lambdas','Generic function types')])

add('exceptions','Java exceptions: recovery boundaries and failure context',
'An exception transfers control from a failing operation to a matching handler while unwinding calls that do not handle it.',
[('Catch what the boundary can handle',[
'A parsing boundary can reject malformed input. It usually cannot repair an unrelated programming error such as an invalid internal array index. Catching Exception around an entire request obscures that difference.',
'Checked exceptions participate in compile-time handling or declaration requirements. RuntimeException subclasses are unchecked. Neither category proves that a failure is recoverable; recovery depends on what the current layer can actually do.',
'The parser translates a NumberFormatException into an IllegalArgumentException with the rejected field context and retains the original cause. That preserves useful diagnostic information without exposing the low-level parser as the public contract.'
]),('Do not turn a failure into a plausible value',[
'Returning zero after an invalid quantity can make a bad order look like a valid empty order. Reject it explicitly, or return a structured validation result when callers need to report several field errors together.',
'The program catches the expected input rejection at a small command boundary and prints a user-facing message. The message names the field but avoids logging the raw input. Sensitive request values should not be copied into every exception and log line.',
'Exceptions from cleanup also matter. <a href="/java/try-with-resources">Try-with-resources</a> keeps the primary failure and records relevant close failures as suppressed exceptions. A plain finally block can accidentally replace the original failure with its own.'
])],'''public class QuantityValidation {
    static int parseQuantity(String rawQuantity) {
        final int quantity;
        try {
            quantity = Integer.parseInt(rawQuantity);
        } catch (NumberFormatException invalidNumber) {
            throw new IllegalArgumentException("Quantity must be a whole number", invalidNumber);
        }
        if (quantity < 1 || quantity > 500) {
            throw new IllegalArgumentException("Quantity must be between 1 and 500");
        }
        return quantity;
    }
    public static void main(String[] args) {
        System.out.println(parseQuantity("12"));
        try {
            parseQuantity("many");
        } catch (IllegalArgumentException rejectedInput) {
            System.out.println(rejectedInput.getMessage());
            System.out.println(rejectedInput.getCause().getClass().getSimpleName());
        }
    }
}''','12\nQuantity must be a whole number\nNumberFormatException',[
'Parsing work depends on input length. Throwing an exception generally constructs diagnostic state and unwinds the stack; it is a poor default mechanism for a high-volume branch that is expected to fail routinely.',
'A bounded parser should reject enormous input before attempting expensive processing. An int parser still has a numeric range limit even if the business rule’s maximum is smaller.',
'Retries belong to a boundary that understands whether repeating the operation is safe. An exception alone does not prove idempotency, nor does it tell a caller whether a remote side effect already occurred.'
],['Do not swallow an exception and continue with a success-shaped value.','Do not lose the original cause when translating a failure.','Do not catch Throwable as routine input handling.','Do not retry an external operation without considering repeated side effects.'],[('try-with-resources','Cleanup failures'),('optional','Expected absence'),('executors','Failures in tasks')])

add('lambdas','Java lambdas: function contracts and captured state',
'A lambda supplies an implementation of a functional interface, which has one abstract method after inherited-method rules are applied.',
[('The target type supplies the signature',[
'A lambda does not have a standalone universal function type in Java. Its surrounding target type establishes parameter and return types. Predicate&lt;T&gt; returns a boolean, Function&lt;T,R&gt; transforms a value, and Consumer&lt;T&gt; performs an action without returning a result.',
'The program uses a Predicate&lt;String&gt; to decide which imported addresses belong to an allowed domain. It deliberately leaves full email validation outside this lesson; an endsWith check is a domain filter, not a complete email parser.',
'A method reference is another way to supply compatible behavior. String::trim refers to the existing trim operation. It does not execute the method at declaration time or automatically schedule it on another thread.'
]),('Captured locals are not mutable slots',[
'A captured local variable must be final or effectively final. The domain string is assigned once and can be captured. Reassigning that variable later would make the lambda declaration invalid.',
'A captured reference can still point to a mutable object. Keeping the local reference unchanged does not make the object thread-safe or freeze its contents. Capturing a growing list in callbacks can also retain that list longer than intended.',
'For operations that update shared state, make ownership explicit. A short lambda body can conceal a database call or mutation just as easily as a named method can. Prefer a name when the behavior’s contract deserves one.'
])],'''import java.util.Arrays;
import java.util.List;
import java.util.function.Predicate;

public class AllowedContactFilter {
    public static void main(String[] args) {
        String allowedDomain = "@aitrove.in";
        Predicate<String> allowed = address -> address.endsWith(allowedDomain);
        List<String> imported = Arrays.asList("team@aitrove.in", "external@other.test");
        for (String address : imported) {
            if (allowed.test(address)) {
                System.out.println(address);
            }
        }
    }
}''','team@aitrove.in',[
'Checking n addresses visits n inputs. The text matching cost depends on the suffix length, and this loop uses O(1) extra loop state. Creating a collected result would require space for the accepted references.',
'Lambda allocation and caching can vary with the capture and runtime implementation. Do not promise one object allocation per invocation or zero allocation without measuring the compiled application.',
'Lambdas pair well with <a href="/java/streams">stream pipelines</a>, but the function contract remains the same outside streams. A normal loop can use Predicate without introducing a pipeline at all.'
],['Do not assume a lambda runs asynchronously.','Do not mutate captured shared objects without an ownership or lock policy.','Do not use a long opaque lambda where a named operation would explain the contract.'],[('streams','Stream pipelines'),('generics','Typed function parameters'),('polymorphism','Interface dispatch')])

add('streams','Java streams: lazy pipelines and bounded results',
'A stream represents a single-use computation over values, connecting intermediate operations to a terminal operation rather than storing another collection.',
[('Execution starts at the terminal operation',[
'filter and map describe work. A terminal operation such as collect, count, or sum triggers the pipeline. Building a stream does not eagerly produce a filtered copy of its source.',
'The program calculates accepted shipment weight from a bounded in-memory batch. It removes nonpositive weights and values above the intake limit, then sums the remaining ints as longs. It does not mutate the source list.',
'mapToLong avoids an object-valued arithmetic pipeline for the total. It does not remove the Integer objects already stored in the source list. A primitive stream and a primitive source solve related but different allocation questions.'
]),('Ordering and side effects need care',[
'A stream can be consumed once. Calling a second terminal operation on the same stream instance is invalid. Obtain another stream from the source when another pass is required.',
'Side-effecting pipeline functions create dependencies that are difficult to reason about, especially under parallel execution. Keep predicates and mappings stateless and avoid modifying the source while traversal is running.',
'collect creates a result container; sorted may need to buffer values; distinct tracks seen values. Laziness does not mean every pipeline uses constant memory. A pipeline with an unbounded source needs a short-circuit or a finite termination condition.'
])],'''import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

public class ShipmentWeightReport {
    public static void main(String[] args) {
        List<Integer> weights = Arrays.asList(12, -1, 8, 42, 5);
        long acceptedTotal = weights.stream()
                .filter(weight -> weight > 0 && weight <= 30)
                .mapToLong(Integer::longValue)
                .sum();
        List<Integer> accepted = weights.stream()
                .filter(weight -> weight > 0 && weight <= 30)
                .collect(Collectors.toList());
        System.out.println("total=" + acceptedTotal);
        System.out.println(accepted);
    }
}''','total=25\n[12, 8, 5]',[
'Each of the two pipelines makes one O(n) pass over the batch. The total uses a bounded accumulator, while the collected result needs O(k) storage for k accepted elements. Combining both outputs in one pass is possible, but a small clear batch may not justify a custom collector.',
'Parallel execution is a performance choice, not a guaranteed speed improvement. Splitting, coordination, ordering requirements, and contention can dominate small inputs. Blocking I/O inside a parallel pipeline is a separate scheduling concern.',
'Java 8 Collectors.toList does not guarantee a particular list type or its mutability. If a caller requires an ArrayList, use toCollection(ArrayList::new). If the result must be immutable, apply an explicit ownership boundary.'
],['Do not reuse an already consumed stream.','Do not use peek as the required location of a business side effect.','Do not assume sorted, distinct, or collect needs only constant memory.','Do not use parallelStream as an automatic fix for slow code.'],[('lambdas','Pipeline function contracts'),('arraylist','Collected result storage'),('optional','A possibly absent result')])

add('optional','Java Optional: absence without hidden failure',
'Optional represents either one non-null value or no value, making a possibly absent return result explicit in an API.',
[('Absence is not an exception',[
'A lookup can legitimately have no configured reply address. That is different from a failed database connection. Optional can express the first outcome; it should not quietly conceal the second.',
'The program converts a nullable configured string into Optional, trims it, and rejects a blank value. Mapping a function that returns null yields an empty Optional. The caller then chooses a fallback.',
'Optional itself should not be null. Returning null from an Optional-returning method forces callers to check two absence mechanisms and defeats the contract.'
]),('Choose eager or lazy fallback intentionally',[
'orElse receives a value that Java evaluates before the call. If that value comes from an expensive method, the method runs even when the Optional already contains a value. orElseGet receives a supplier and invokes it only when a fallback is needed.',
'This distinction affects cost and side effects. A fallback that reads configuration or performs I/O should not run accidentally just because the return type looks convenient.',
'get throws when the Optional is empty. Chaining get immediately after creating the Optional replaces a null check with another failure. Prefer map, flatMap, ifPresent, or an explicit fallback according to the caller’s intended behavior.'
])],'''import java.util.Optional;

public class ReplyAddressLookup {
    static Optional<String> configuredAddress(String rawAddress) {
        return Optional.ofNullable(rawAddress)
                .map(String::trim)
                .filter(address -> !address.isEmpty());
    }
    static String fallbackAddress() {
        System.out.println("fallback evaluated");
        return "support@aitrove.in";
    }
    public static void main(String[] args) {
        System.out.println(configuredAddress(" team@aitrove.in ").orElseGet(ReplyAddressLookup::fallbackAddress));
        System.out.println(configuredAddress(" ").orElseGet(ReplyAddressLookup::fallbackAddress));
    }
}''','team@aitrove.in\nfallback evaluated\nsupport@aitrove.in',[
'The wrapper operations perform a small fixed number of steps; trimming work and possible copying depend on string length. The fallback cost is avoided for the first lookup because the supplier is not invoked.',
'Optional introduces a representation choice. It is useful for a clear return contract, but turning every object field or method parameter into Optional can add ceremony without clarifying ownership or validation.',
'A returned Optional cannot say why a value is absent unless the API defines that meaning separately. If callers need multiple failure reasons, use a result type with those reasons instead of collapsing them into empty.'
],['Do not return null instead of Optional.empty().','Do not pass null into Optional.of.','Do not call get without an established presence guarantee.','Do not hide infrastructure failures as ordinary absence.'],[('exceptions','Failure handling'),('lambdas','Suppliers and mapping'),('streams','Stream result processing')])

add('files','Java file I/O: UTF-8, streaming reads, and path ownership',
'Java NIO file APIs read and write data through Path values while letting the caller choose encoding, buffering, and resource lifetime.',
[('A path is not an open file',[
'Constructing a Path identifies a filesystem location. Opening a reader performs I/O and can fail for missing files, permissions, resource limits, or concurrent changes. Treat those failures as part of the boundary’s contract.',
'The program creates its own temporary file, writes a small UTF-8 batch, reads it with a BufferedReader, and removes the file in finally. It does not touch an existing user-selected file. The contents use a known numeric format so the parsing rule is explicit.',
'An explicit charset prevents platform defaults from changing interpretation across machines. A writer and reader must agree on the format as well as the encoding. Lines with commas, quoted fields, or embedded newlines need a parser for that format rather than an improvised split.'
]),('Keep the input size bounded',[
'readAllLines materialises the entire file. A buffered line loop can process one line at a time, but it still needs a maximum line length or bounded input policy for hostile files. Streaming does not turn unlimited input into a safe workload.',
'Here each accepted line holds an invoice number, and the loop counts records. A real importer should specify whether one invalid line aborts the batch or produces a per-line rejection report.',
'Do not let an untrusted filename directly select arbitrary storage paths. Directory containment, symlink handling, and the time between validation and opening all matter. This lesson uses a path created by the process to keep those issues outside the demonstration.'
])],'''import java.io.BufferedReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

public class Utf8InvoiceBatch {
    public static void main(String[] args) throws Exception {
        Path batch = Files.createTempFile("aitrove-invoices-", ".txt");
        try {
            Files.write(batch, Arrays.asList("1041", "1042", "1043"), StandardCharsets.UTF_8);
            int records = 0;
            try (BufferedReader reader = Files.newBufferedReader(batch, StandardCharsets.UTF_8)) {
                String line;
                while ((line = reader.readLine()) != null) {
                    Integer.parseInt(line);
                    records++;
                }
            }
            System.out.println("records=" + records);
        } finally {
            Files.deleteIfExists(batch);
        }
    }
}''','records=3',[
'The read visits B input characters, giving O(B) read and parse work for this bounded numeric format. It retains one current line and reader buffering rather than all records; working space depends on the longest line and buffer size.',
'This example writes an in-memory list first, so its fixture preparation is not a streaming writer for an enormous batch. The read pattern remains useful when the file already exists.',
'File deletion in a finally block can itself fail and mask a previous error. A production cleanup boundary should preserve the primary failure and report a failed deletion separately. <a href="/java/try-with-resources">Resource closing</a> provides suppression semantics for closeable resources.'
],['Do not rely on the default charset for a defined text format.','Do not load an unbounded file into memory without a size policy.','Do not swallow I/O errors and report an empty successful batch.'],[('try-with-resources','Closing a reader'),('exceptions','I/O failures'),('streams','Traversal costs')])

add('try-with-resources','Java try-with-resources: close order and suppressed failures',
'Try-with-resources closes AutoCloseable resources when control leaves its block, including when the block throws.',
[('Bind cleanup to the acquisition scope',[
'Files, streams, sockets, and database statements can hold resources that garbage collection does not release promptly enough. A lexical cleanup boundary states when the operation is finished with them.',
'Java 8 declares resources inside the try parentheses. If several are declared, they close in reverse declaration order. If acquiring a later resource fails, already acquired resources are still eligible for the cleanup performed by the statement.',
'The program uses a small diagnostic AutoCloseable to make both normal block failure and close failure observable. It does not need a real connection or file to explain the ordering rule.'
]),('Preserve the primary failure',[
'When the body throws and close also throws, the body’s exception remains the primary one and the close failure becomes suppressed. getSuppressed exposes it for diagnostics. A close failure with no earlier body failure can instead become the thrown exception.',
'This distinction helps identify what first broke. A log that prints only the primary message can hide the cleanup failure. A log that reports only close can hide the actual failed operation.',
'Close is not a transaction rollback. Closing a database connection, writer, or custom resource does not imply that every preceding external effect was reversed. Define transaction and durability behavior separately.'
])],'''public class ResourceFailureOrder {
    static final class BatchLease implements AutoCloseable {
        @Override
        public void close() {
            throw new IllegalStateException("lease close failed");
        }
    }
    public static void main(String[] args) {
        try (BatchLease lease = new BatchLease()) {
            throw new IllegalArgumentException("batch validation failed");
        } catch (Exception failure) {
            System.out.println(failure.getMessage());
            for (Throwable suppressed : failure.getSuppressed()) {
                System.out.println("suppressed: " + suppressed.getMessage());
            }
        }
    }
}''','batch validation failed\nsuppressed: lease close failed',[
'With r resources, cleanup invokes up to r close operations in reverse order. The actual time and memory costs belong to each resource implementation. Closing a network resource can block; O(r) method calls does not promise a small wall-clock duration.',
'The statement avoids repeatedly writing finally cleanup logic at each call site. It does not make opening a resource free or allow keeping unlimited resources alive in one scope.',
'For a custom AutoCloseable, document whether close is idempotent, whether it can fail, and whether the resource can be used afterward. Those behaviors cannot be inferred from the interface alone.'
],['Do not assume close failures are discarded.','Do not treat close as an automatic rollback of external side effects.','Do not rely on garbage collection for a prompt resource release deadline.'],[('files','Readers and files'),('exceptions','Failure context'),('executors','Explicit worker shutdown')])

add('bigdecimal','Java BigDecimal: decimal amounts and explicit rounding',
'BigDecimal represents an arbitrary-precision decimal value using an unscaled integer and a scale, with immutable arithmetic results.',
[('Start from a decimal representation',[
'For a defined decimal amount, construct from the input text or another exact decimal source. Passing a double to the constructor captures that binary floating-point value, which may differ from the decimal text the developer intended.',
'The program calculates tax from a textual subtotal and rate, rounds tax once to two places, then adds it to the subtotal. These are demonstration values. A real invoice needs a defined currency, tax policy, rounding stage, and maximum amount.',
'Immutable means add, multiply, and setScale return new values. Calling total.add(tax) without keeping its result does not update total. This differs from a mutable balance object with an increment method.'
]),('Equality includes scale',[
'equals distinguishes 2.0 and 2.00 because it compares both numeric value and scale. compareTo regards them as numerically equal. Pick the comparison that matches the application rule.',
'This affects <a href="/java/hashmap">map keys</a> and <a href="/java/hashset">set membership</a>. Normalising scale at a boundary can establish one representation, but an arbitrary normalisation may destroy meaningful formatting or precision rules.',
'Division can require a rounding decision when the exact decimal expansion does not terminate. Use an explicit scale and RoundingMode or a MathContext suitable for the operation; silently assuming every decimal division is exact will fail.'
])],'''import java.math.BigDecimal;
import java.math.RoundingMode;

public class InvoiceTaxCalculation {
    public static void main(String[] args) {
        BigDecimal subtotal = new BigDecimal("19.95");
        BigDecimal taxRate = new BigDecimal("0.18");
        BigDecimal tax = subtotal.multiply(taxRate).setScale(2, RoundingMode.HALF_UP);
        BigDecimal total = subtotal.add(tax);
        System.out.println("tax=" + tax.toPlainString());
        System.out.println("total=" + total.toPlainString());
        System.out.println(new BigDecimal("2.0").equals(new BigDecimal("2.00")));
        System.out.println(new BigDecimal("2.0").compareTo(new BigDecimal("2.00")) == 0);
    }
}''','tax=3.59\ntotal=23.54\nfalse\ntrue',[
'Arbitrary precision is not constant-cost arithmetic. Larger digit counts require more computation and storage; multiplication and division costs depend on operand sizes and the algorithms in use.',
'Limit accepted precision and scale at an input boundary. An attacker-supplied amount with an enormous digit count can create computation and memory pressure even before a business rule rejects its value.',
'Converting a final decimal amount back to double can reintroduce binary rounding. Keep the decimal representation through persistence and interchange when the format supports it.'
],['Do not construct an exact monetary input from an imprecise double by accident.','Do not ignore a returned arithmetic value.','Do not substitute equals for numeric comparison without considering scale.','Do not leave rounding policy implicit.'],[('equals-hashcode','Equality contracts'),('operators','Numeric operations'),('treemap','Ordered thresholds')])

add('date-time','Java date and time: local schedules versus instants',
'LocalDateTime describes calendar fields without a time zone; Instant identifies a point on the UTC timeline, and ZonedDateTime connects local fields to zone rules.',
[('Choose the question before the type',[
'A birthday is a date. A daily store opening time is a local time plus a schedule policy. A completed payment has a timestamp on a timeline. Storing all three as a zone-less date-time hides different meanings behind one shape.',
'The program turns a Delhi appointment into an instant using Asia/Kolkata. It prints both the local zoned appointment and its UTC instant. This is a fixed example, so a test does not depend on the current clock.',
'A zone ID names rules, not merely a permanent numeric offset. Some regions change offset across daylight-saving transitions. A local time can be invalid during a gap or ambiguous during an overlap; conversion defaults must match the appointment policy.'
]),('Keep calendar arithmetic separate',[
'Adding a calendar day and adding twenty-four elapsed hours are not always equivalent in zones with clock changes. Use Period-like calendar intent for calendar schedules and Duration-like elapsed intent for elapsed work.',
'Formatting is a presentation decision. Do not parse locale-dependent human text as your only interchange format. Choose a defined format and reject ambiguous input rather than guessing a user’s date order.',
'The java.time types used here are immutable. Share them as values, but remember a scheduled event may need its original zone and local intent stored alongside the resulting instant if future rule changes must be handled.'
])],'''import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;

public class DelhiAppointmentTime {
    public static void main(String[] args) {
        LocalDateTime appointment = LocalDateTime.of(2026, 10, 5, 9, 30);
        ZonedDateTime zoned = appointment.atZone(ZoneId.of("Asia/Kolkata"));
        Instant instant = zoned.toInstant();
        System.out.println(zoned);
        System.out.println(instant);
    }
}''','2026-10-05T09:30+05:30[Asia/Kolkata]\n2026-10-05T04:00:00Z',[
'This converts one appointment using the runtime’s time-zone data. The application performs a fixed number of operations, but internal rule lookup is not usefully described as an input-batch algorithm.',
'Time-zone data can change across runtime updates. Persist the intent needed to reproduce the business decision rather than assuming a zone-less formatted string is enough.',
'Inject a Clock for code that depends on now. Fixed-clock tests can cover expiry boundaries without sleeping and without timing-dependent failures.'
],['Do not treat LocalDateTime as a globally unique timestamp.','Do not replace a region zone with a guessed offset for long-lived schedules.','Do not assume a calendar day is always twenty-four elapsed hours.'],[('classes-objects','Immutable value objects'),('exceptions','Invalid input handling'),('executors','Scheduling ownership')])

add('threads','Java threads: visibility, atomicity, and shared counters',
'A Java thread executes an independent sequence of instructions, and shared mutable state needs ordering and visibility rules between those sequences.',
[('Increment is more than one action',[
'counter++ reads a value, computes another, and writes it back. Two threads can read the same old value and lose one increment. Declaring the field volatile makes visibility rules stronger but does not combine those three steps into an atomic increment.',
'The program protects an entire increment with the same object monitor and reads under that monitor. The monitor establishes both mutual exclusion for the operation and visibility through the corresponding synchronisation actions.',
'Thread.start begins another execution. Calling run directly does not create a thread. join waits for completion and provides the ordering needed before the main thread inspects the completed work.'
]),('Protect the invariant, not just a field',[
'For a single counter, AtomicInteger is another option. A transfer between two balances needs a larger invariant: changing one balance and the other must be coordinated as one valid operation. Separate atomic fields do not automatically supply that transaction.',
'The loop is a teaching workload, not a performance benchmark. It intentionally makes many tiny contended operations so the ownership rule is visible. In a real batch, accumulating per-thread totals and combining afterward may reduce contention.',
'Lock ordering also matters. Acquiring two locks in opposite orders across threads can deadlock. Use one documented order, minimise work under locks, and avoid hidden I/O while holding a shared application monitor.'
])],'''public class ShipmentCounterThreads {
    static final class Counter {
        private int completed;
        synchronized void increment() { completed++; }
        synchronized int value() { return completed; }
    }
    public static void main(String[] args) throws InterruptedException {
        Counter counter = new Counter();
        Runnable batch = () -> {
            for (int shipment = 0; shipment < 1000; shipment++) counter.increment();
        };
        Thread first = new Thread(batch, "shipment-first");
        Thread second = new Thread(batch, "shipment-second");
        first.start();
        second.start();
        first.join();
        second.join();
        System.out.println(counter.value());
    }
}''','2000',[
'For n total increments the program performs O(n) counter work, with a constant-sized counter and two threads. Contention and scheduling affect elapsed time; an asymptotic count does not prove parallel speedup.',
'Threads have runtime resources including stacks. Creating a thread for every unbounded request can exhaust resources. A managed <a href="/java/executors">executor</a> centralises admission and lifecycle decisions.',
'InterruptedException communicates a cancellation signal to code waiting in join. A larger application should propagate it or restore interrupt status when it cannot propagate, rather than quietly treating interruption as successful completion.'
],['Do not use volatile as a substitute for atomic compound updates.','Do not call run and expect another thread.','Do not ignore interruption without a cancellation policy.','Do not hold locks during avoidable external I/O.'],[('executors','Managing tasks'),('static-final','Shared storage'),('pass-by-value','Shared references')])

add('executors','Java ExecutorService: bounded admission and shutdown',
'ExecutorService separates task submission from worker execution and exposes completion and shutdown operations for a managed group of tasks.',
[('Bound the waiting work',[
'A fixed worker count is not necessarily a bounded backlog. Some executor factory methods use an unbounded work queue, so fast producers can keep adding retained tasks even while all workers are busy.',
'The program configures two workers and an ArrayBlockingQueue with four waiting slots. AbortPolicy rejects excess work instead of pretending the system has unlimited capacity. RejectedExecutionException belongs in the caller’s admission policy.',
'A rejected task has not been accepted by this executor. Decide whether to return a busy response, retry later, or route elsewhere. An uncontrolled immediate retry loop can worsen the overload.'
]),('Observe results and stop workers',[
'submit returns a Future. get observes the result, can throw ExecutionException for a task failure, and can be interrupted. A submitted task’s exception can go unnoticed when its Future is ignored.',
'shutdown stops acceptance of new tasks and lets accepted work finish. awaitTermination waits up to a chosen deadline. shutdownNow requests interruption and returns queued work that did not start; it cannot force arbitrary code to obey interruption.',
'The cleanup below preserves interrupt status if shutdown waiting is interrupted. The actual task is a deterministic calculation with no external effects, which keeps retry and transaction questions outside the program.'
])],'''import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.Future;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

public class BoundedInvoiceWorkers {
    public static void main(String[] args) throws Exception {
        ThreadPoolExecutor workers = new ThreadPoolExecutor(
                2, 2, 0L, TimeUnit.MILLISECONDS,
                new ArrayBlockingQueue<Runnable>(4), new ThreadPoolExecutor.AbortPolicy());
        try {
            Future<Integer> invoiceTotal = workers.submit(() -> 17 + 23);
            System.out.println(invoiceTotal.get());
        } finally {
            workers.shutdown();
            try {
                if (!workers.awaitTermination(2, TimeUnit.SECONDS)) workers.shutdownNow();
            } catch (InterruptedException cancelledWait) {
                workers.shutdownNow();
                Thread.currentThread().interrupt();
            }
        }
    }
}''','40',[
'The queue limits waiting tasks to four, with up to two running tasks under this fixed configuration. That is an entry-count bound, not a byte bound: each task can capture a large object graph.',
'Task execution cost depends on the submitted operation. This calculation is constant work. A file import or remote call may be much slower and needs timeouts, cancellation cooperation, and an overload policy suited to it.',
'Waiting for a Future inside another task on the same saturated pool can starve the work needed to complete it. Design dependencies explicitly rather than treating a worker pool as unlimited execution capacity.'
],['Do not ignore Future failures.','Do not forget shutdown in an owned executor lifecycle.','Do not assume shutdownNow forcibly terminates every running task.','Do not claim a fixed worker count also bounds every factory-created queue.'],[('threads','Visibility and locks'),('exceptions','Task failure boundaries'),('priorityqueue','Priority selection')])

add('binary-search','Java binary search: lower bounds and duplicate values',
'Binary search repeatedly narrows an ordered interval to locate a value or a boundary, relying on the input already being sorted under the same comparison rule.',
[('Define the required result',[
'A membership query can return any matching index. A report that groups duplicate values needs the first matching position. A lower-bound search returns the first position whose value is not less than the target, including the insertion position when the target is absent.',
'The program keeps a half-open interval [low, high). Initially low is zero and high is the array length. An empty array is therefore a valid input with an empty interval, and the result is zero.',
'When the middle value is below the target, all earlier values are also below it under the sorting precondition. Otherwise the middle position remains a candidate and the upper bound moves to it. This invariant is what makes narrowing correct, not merely the use of a while loop.'
]),('Avoid an overflowing midpoint',[
'low + (high - low) / 2 avoids adding two possibly large positive indices. It also makes the half-open interval arithmetic easy to check. Search bounds are positions, so the returned length value is not a readable element index.',
'Arrays.binarySearch uses a different absent-value convention: its negative result encodes the insertion point. With duplicate matching values, it does not promise the first one. Translate that return contract instead of assuming the custom lower-bound result is interchangeable.',
'Never run this algorithm over unsorted values and interpret a plausible answer as success. If the batch must be sorted first, include that sorting cost in the whole operation.'
])],'''public class ShipmentThresholdSearch {
    static int lowerBound(int[] thresholds, int target) {
        int low = 0;
        int high = thresholds.length;
        while (low < high) {
            int middle = low + (high - low) / 2;
            if (thresholds[middle] < target) low = middle + 1;
            else high = middle;
        }
        return low;
    }
    public static void main(String[] args) {
        int[] thresholds = {10, 20, 20, 35, 80};
        System.out.println(lowerBound(thresholds, 20));
        System.out.println(lowerBound(thresholds, 22));
        System.out.println(lowerBound(thresholds, 90));
        System.out.println(lowerBound(new int[0], 20));
    }
}''','1\n3\n5\n0',[
'Each iteration roughly halves the candidate interval, so an already sorted array needs O(log n) comparisons and O(1) extra state. Array indexing is O(1), which is part of this cost argument.',
'Applying index-based searching to a <a href="/java/linkedlist">linked list</a> adds traversal work at each indexed access. A logarithmic comparison count alone does not guarantee logarithmic total work on a sequential-access structure.',
'For one lookup in an unsorted small array, <a href="/java/linear-search">linear search</a> may cost less than sorting first. Binary search becomes useful when the ordering already exists or many queries share a sorted dataset.'
],['Do not read array[result] when result equals array.length.','Do not mix inclusive and exclusive bound formulas.','Do not assume a duplicate match is the first match.','Test empty input, all-smaller input, all-larger input, and duplicate runs.'],[('arrays','Array bounds'),('sorting','Sorting the input'),('linear-search','Unsorted lookup')],'java-dsa')

add('sorting','Java sorting: comparators, stability, and ownership',
'Sorting arranges values according to a comparison rule, and a comparator must provide a consistent ordering for the sort to behave correctly.',
[('Write the ordering rule as a contract',[
'A shipment report sorts by delivery zone and then by numeric sequence. Comparing only the zone leaves ties equal; adding a sequence makes the intended tie-break visible. Null values need a defined policy before the sort starts.',
'Do not subtract arbitrary integer or long fields to implement comparison. Arithmetic can overflow and violate ordering. Comparator.comparingInt and thenComparingInt avoid that trap while stating the two rules directly.',
'A comparator should be antisymmetric in sign and transitive. If the result depends on a mutable clock, changing external state, or side effects, repeated comparisons can disagree. Some sorts detect an invalid contract, but correctness must not depend on an exception catching every bad comparator.'
]),('Sorting mutates the chosen container',[
'List.sort changes the list’s order. The program sorts an ArrayList copy so the input encounter order remains available. This is a shallow copy: the Shipment objects themselves are still shared.',
'Java’s object-list sorting contract is stable, meaning entries equal under the comparator retain their earlier relative order. That does not create a business tie-breaker when the application requires one; define a sequence field for that.',
'Primitive array sorting, object-array sorting, and collection sorting have different implementation and storage details. Avoid describing every Java sort as one fixed algorithm or one fixed memory budget.'
])],'''import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;

public class ShipmentReportOrder {
    static final class Shipment {
        final int zone;
        final int sequence;
        Shipment(int zone, int sequence) { this.zone = zone; this.sequence = sequence; }
        public String toString() { return zone + ":" + sequence; }
    }
    public static void main(String[] args) {
        List<Shipment> imported = Arrays.asList(new Shipment(2, 7), new Shipment(1, 9), new Shipment(1, 3));
        List<Shipment> sorted = new ArrayList<>(imported);
        sorted.sort(Comparator.comparingInt((Shipment shipment) -> shipment.zone)
                .thenComparingInt(shipment -> shipment.sequence));
        System.out.println(sorted);
        System.out.println(imported);
    }
}''','[1:3, 1:9, 2:7]\n[2:7, 1:9, 1:3]',[
'For the comparison sort used by this list path, budget O(n log n) comparisons in the worst case and O(n) temporary reference space as a conservative upper bound. Copying the list first also requires O(n) references. Comparator cost multiplies the work if comparison itself is expensive.',
'If only the next highest-priority item is needed repeatedly while arrivals continue, a <a href="/java/priorityqueue">PriorityQueue</a> may fit better than re-sorting the entire batch after every insertion.',
'After sorting, the same comparison rule must be used for <a href="/java/binary-search">binary search</a>. A list ordered by zone and sequence is not automatically searchable by a different unrelated field.'
],['Do not mutate ordering fields while a sort is running.','Do not use subtraction as a comparator.','Do not assume sorting a shallow copy isolates mutable element state.','Do not reuse a sorted array with a search comparator that defines another order.'],[('priorityqueue','Ordered removal'),('binary-search','Searching sorted values'),('arraylist','Copying references')],'java-dsa')

add('recursion','Java recursion: base cases, stack depth, and bounded work',
'Recursion solves an operation by calling it again on a smaller subproblem, with a base case that stops further calls.',
[('Prove progress toward the base case',[
'A recursive sum over a half-open array interval stops when the interval is empty. Otherwise it splits the interval and sums its two halves. Both child intervals are smaller than their parent.',
'The program accumulates as a long even though each stored count is an int. That prevents int-sized intermediate sums from wrapping in this bounded example. It still does not make an arbitrarily enormous long sum overflow-proof.',
'An invalid split can reproduce the same interval and recurse indefinitely. A correct base case is not enough by itself; every non-base branch must move toward it. Empty input and a single-element interval are useful tests of that progress.'
]),('Stack depth is part of space cost',[
'A recursive method call needs stack state. Java does not promise general tail-call elimination, so tail-recursive source should not be described as constant-stack merely because the recursive call appears last.',
'This balanced sum has logarithmic call depth, but it still visits every element. A linear recursive sum that moves one index each time would use linear depth and could overflow the stack for a large batch.',
'For a simple sum, an iterative loop is usually easier and uses constant extra space. This recursive form is useful to understand divide-and-conquer structure before studying operations that gain more from the split.'
])],'''public class BalancedShipmentSum {
    static long sum(int[] counts, int from, int to) {
        if (from == to) return 0L;
        if (to - from == 1) return counts[from];
        int middle = from + (to - from) / 2;
        return sum(counts, from, middle) + sum(counts, middle, to);
    }
    public static void main(String[] args) {
        int[] dailyCounts = {12, 8, 0, 15, 3};
        System.out.println(sum(dailyCounts, 0, dailyCounts.length));
        System.out.println(sum(new int[0], 0, 0));
    }
}''','38\n0',[
'The recurrence performs two child traversals whose sizes sum to n, plus constant local work. Total work is O(n), not O(log n). Logarithmic split depth does not mean logarithmic total work.',
'Active recursive frames require O(log n) extra stack space for this balanced implementation. It does not allocate copied subarrays, because both branches reuse the original array with different bounds.',
'If bounds can come from a caller, validate 0 <= from <= to <= counts.length at a public boundary. The demonstration calls the helper only with valid bounds; its implementation does not hide a separate validation contract.'
],['Do not forget a base case for an empty interval.','Do not assume Java eliminates tail-recursive stack frames.','Do not confuse recursion depth with total work.','Do not copy a subarray at every split without counting that allocation cost.'],[('arrays','Half-open bounds'),('methods','Method contracts'),('binary-search','Interval narrowing')],'java-dsa')

# Extend the existing core method lesson instead of leaving its small preview as the whole lesson.
method=by_path['java/methods']
method['body']=p('A Java method defines a named operation with parameter types, a return type, and a body; callers pass argument values into a new invocation.')
method['body']+='<h2>Define what the operation promises</h2>'+p('A calculation should state its input range, units, failure behavior, and whether it changes caller-owned state. A method named totalCents that accepts an array should not silently store that array for unrelated later work.')+p('The batch below uses positive and zero invoice line values, rejects negative values, and accumulates as long. Math.addExact makes long overflow a failure rather than wrapping into a plausible total. This is a local calculation, not a payment operation.')+p('Parameter values are copied into each invocation. Copying an array reference does not copy its contents. The method only reads the array; see <a href="/java/pass-by-value">pass-by-value and shared references</a> before adding mutation.')
method['body']+='<h2>Overloading is a compile-time choice</h2>'+p('Overloaded methods share a name but have different parameter lists. Return type alone cannot distinguish two overloads with the same parameters. The compiler chooses an applicable signature from the declared argument types; runtime instance overriding is a separate <a href="/java/polymorphism">dispatch rule</a>.')+p('Varargs allows a variable-length argument list by presenting an array parameter inside the method. It can introduce an array allocation at a call site. Passing an existing compatible array supplies that array reference rather than automatically creating a detached copy.')
method['body']+='<h2>Working program</h2>'+block('''public class InvoiceMethodContract {
    static long totalCents(int[] lineAmounts) {
        if (lineAmounts == null) throw new IllegalArgumentException("Missing amounts");
        long total = 0L;
        for (int amount : lineAmounts) {
            if (amount < 0) throw new IllegalArgumentException("Negative line amount");
            total = Math.addExact(total, amount);
        }
        return total;
    }
    public static void main(String[] args) {
        System.out.println(totalCents(new int[] {1250, 0, 750}));
        System.out.println(totalCents(new int[0]));
    }
}''')+'<h3>Output</h3>'+block('2000\n0','text')
method['body']+='<h2>Cost and design choices</h2>'+p('The operation visits n line amounts in O(n) time and uses O(1) extra local state. The supplied array is not cloned. A new method frame is not equivalent to a new copy of every referenced object.')+p('A small method can still be expensive if it performs remote work or repeatedly traverses a collection. Method length is not a performance measure. Keep side effects visible in the contract and test empty, invalid, and boundary inputs.')+'<h3>Common Mistakes</h3><ul><li>Do not overload only by return type.</li><li>Do not describe a passed reference as a copied object.</li><li>Do not silently return zero for invalid input when zero is also a valid result.</li><li>Do not ignore integer range when choosing an accumulator.</li></ul>'
method['data']['reading_minutes']=4

# Replace overview modules with an explicit, linked syllabus.
core=by_path['java/java']
core['data']['modules']=[
 {'title':'Toolchain and source layout','summary':'Compile a program, identify class names, and keep package boundaries explicit.','lessons':['java/setup','java/packages']},
 {'title':'Values and control flow','summary':'Choose numeric ranges, branch deliberately, and stop loops at valid bounds.','lessons':['java/variables-types','java/operators','java/control-flow','java/basics']},
 {'title':'Arrays, strings, and method calls','summary':'Count copying costs and distinguish a reference value from an object copy.','lessons':['java/arrays','java/strings','java/methods','java/pass-by-value']},
 {'title':'Objects and contracts','summary':'Build valid objects, protect state, and define substitute behavior.','lessons':['java/classes-objects','java/constructors','java/encapsulation','java/inheritance','java/interfaces','java/polymorphism']},
 {'title':'Identity, constants, and finite states','summary':'Keep equality stable and make shared state and state transitions explicit.','lessons':['java/equals-hashcode','java/static-final','java/enums']},
]
core['body']=p('Java compiles source declarations into class files that a JVM can load and execute. This roadmap starts with that toolchain, then builds up to object contracts and collection choices.')+'<h2>Start with one complete program</h2>'+p('Read <a href="/java/setup">JDK, JVM, and the first program</a> before debugging syntax in a large project. Compile from a terminal once so a missing compiler, an incorrect classpath, and an exception inside the program do not look like the same failure.')+'<h2>Follow the dependencies</h2>'+p('Work through values and arrays before object design. Methods pass values; <a href="/java/pass-by-value">a copied object reference</a> still points to one object. That rule explains later questions about mutable lists and defensive copies.')+'<h2>Keep the operations visible</h2>'+p('After the core modules, move to <a href="/java/java-collections">Java Collections</a> for List, Map, and Deque decisions. <a href="/java/advanced-java">Advanced Java</a> covers generic bounds, failure handling, file resources, streams, and worker ownership.')+'<h3>Common Mistakes</h3>'+p('Do not treat a roadmap as a substitute for running the programs. Predict each output, change one condition, and test the failure cases. These lessons use Java 8-compatible syntax and APIs unless the page states another requirement.')
adv=by_path['java/advanced-java']
adv['data']['modules']=[
 {'title':'Types and failures','summary':'Keep type relationships checked and preserve useful failure context.','lessons':['java/generics','java/exceptions','java/optional']},
 {'title':'Functions and pipelines','summary':'Express transformations without hiding shared side effects.','lessons':['java/lambdas','java/streams']},
 {'title':'Files and resource lifetime','summary':'Read a bounded format and close resources on every exit path.','lessons':['java/files','java/try-with-resources']},
 {'title':'Decimal and time values','summary':'Define rounding, representation, local intent, and timeline identity.','lessons':['java/bigdecimal','java/date-time']},
 {'title':'Threads and worker admission','summary':'Coordinate shared state, bound waiting work, and shut down owned workers.','lessons':['java/threads','java/executors']},
]
adv['body']=p('Advanced Java work combines type contracts, resource ownership, and execution boundaries. The difficult failures often come from a mismatch between those boundaries rather than from syntax.')+'<h2>Types before casts</h2>'+p('Start with <a href="/java/generics">generics and wildcard bounds</a>, then make <a href="/java/exceptions">failure handling</a> explicit. Use <a href="/java/optional">Optional</a> for defined absence, not as a way to hide an I/O error.')+'<h2>Execution and ownership</h2>'+p('A <a href="/java/streams">stream pipeline</a> is not a collection copy, and a <a href="/java/lambdas">lambda</a> is not automatically asynchronous. Keep file handles and worker lifetimes scoped to an owner that can close them.')+'<h3>Common Mistakes</h3>'+p('Do not add concurrency before measuring the workload and choosing an admission policy. Do not describe an unbounded queue as safe because the worker count is fixed.')
collection=by_path['java/java-collections']
collection['data']['modules']=[
 {'title':'Contracts and traversal','summary':'Choose the operation family and keep mutation within a defined traversal policy.','lessons':['java/collection-choices','java/iterators']},
 {'title':'Lists and endpoints','summary':'Compare indexed access with linked traversal and endpoint operations.','lessons':['java/arraylist','java/linkedlist','java/arraydeque']},
 {'title':'Hashes and deduplication','summary':'Store mappings or unique values under a stable equality contract.','lessons':['java/hashmap','java/hashset']},
 {'title':'Order and priority','summary':'Use key order, encounter order, or removal priority intentionally.','lessons':['java/treemap','java/linkedhashmap','java/priorityqueue']},
]
collection['body']=p('Java collections expose operations such as positional access, membership, key lookup, and endpoint removal; their implementations have different traversal and storage costs.')+'<h2>Choose the question first</h2>'+p('Use a <a href="/java/arraylist">List</a> for ordered values, a <a href="/java/hashset">Set</a> for membership, a <a href="/java/hashmap">Map</a> for a key-to-value association, or a <a href="/java/arraydeque">Deque</a> for endpoint work. Map is part of the collections framework but is not a subtype of Collection.')+'<h2>Ordering is a contract</h2>'+p('<a href="/java/treemap">TreeMap</a> orders keys. <a href="/java/linkedhashmap">LinkedHashMap</a> keeps encounter order. <a href="/java/priorityqueue">PriorityQueue</a> orders removals but does not supply sorted iteration. Those guarantees answer different questions.')+'<h3>Common Mistakes</h3>'+p('Do not choose LinkedList simply because the workload inserts elements: finding an insertion position can dominate the edit. Count traversal, copying, allocation, and synchronisation needs before selecting an implementation.')
dsa=by_path['java/dsa-in-java']
dsa['data']['modules']=[{'title':'Search and ordering','summary':'Define the input precondition and count total work.','lessons':['java/linear-search','java/binary-search','java/sorting']},{'title':'Recursive decomposition','summary':'Prove progress, count all branches, and include stack space.','lessons':['java/recursion']}]
dsa['body']=p('An algorithm specifies the steps that transform an input into a result; a Java implementation must also respect numeric ranges, container access costs, and call-stack limits.')+'<h2>Count the whole operation</h2>'+p('<a href="/java/binary-search">Binary search</a> needs ordered input. Sorting an unsorted batch first is part of the cost. <a href="/java/recursion">Recursion depth</a> is not the same quantity as total work across all branches.')+'<h3>Common Mistakes</h3>'+p('Test empty input, repeated values, boundary values, and an absent result. A correct output for one small fixture does not establish correctness for every valid input.')

# Extra notes deepen shorter foundation pages with specific tradeoffs.
notes={
 'setup':('Separate three failure stages', ['A compiler error means no valid class file was produced for that compilation. A class-not-found error means the launcher could not locate the requested compiled entry point. A stack trace from main means execution started and the program failed later. Keep the command and working directory in the bug report.', 'The source filename must match a public top-level class name. Java class names are case-sensitive, so a filename accepted on one filesystem can still hide a portability problem. Run the compiled name without a .class suffix.']),
 'variables-types':('Range and initialization boundaries', ['int arithmetic can wrap without throwing. Widening the destination variable after an overflowing int calculation does not recover the lost value. Convert an operand before the calculation or use checked arithmetic when overflow should reject the operation.', 'Fields and array elements receive default values; local variables need a definite assignment before use. A default zero may also be a valid business value, so explicitly track absence instead of assuming an unassigned field will be obvious.']),
 'operators':('Promotion before assignment', ['For byte and short arithmetic, most ordinary numeric operations promote operands to int. A narrowing assignment needs an explicit conversion or a compound-assignment rule, and narrowing can lose information. The destination type does not select the intermediate expression type.', '&& and || short-circuit: the right operand may not execute. Avoid hiding required side effects there. Integer division truncates toward zero; switching the final assigned variable to double does not undo division that already happened as int arithmetic.']),
 'control-flow':('Loop invariants and exit policies', ['A loop should make progress toward a condition that can become false. Updating the wrong counter or comparing against an unchanging value can create an infinite loop even when the body appears small.', 'Use half-open index bounds for arrays: start at zero and stop before length. continue still permits a for loop’s update step, while return exits the method. Do not replace an error with break when the caller needs to know that processing stopped early.']),
 'arrays':('Aliasing, covariance, and copying', ['Arrays.copyOf creates another array but only copies references for object elements. If an element is mutable, both arrays still reach that element. A two-dimensional Java array is an array of row references, so copying the outer array also shares the original rows.', 'A reference array can be assigned to a wider reference-array type. Its actual component type still controls writes, so storing an incompatible element throws ArrayStoreException. Generic lists use a different invariance rule that catches many such assignments at compilation.']),
 'strings':('Text length is not always character count', ['String.length counts UTF-16 code units. Some Unicode characters occupy two code units, and a user-perceived character can combine several code points. Indexing and substring boundaries therefore need a defined text model when the input is not restricted to a simple identifier alphabet.', 'String is immutable, but repeated concatenation in a loop can create intermediate strings and repeated copying. Use a StringBuilder for a growing report, and limit total output size. A small one-off concatenation is a different workload.']),
 'classes-objects':('Reachability and object ownership', ['A constructor does not automatically deep-copy the values passed into it. Storing a caller’s mutable collection keeps a shared reference. If the object promises a snapshot, copy the relevant structure and state how mutable elements are handled.', 'Garbage collection reclaims unreachable objects, not objects merely labelled temporary in a method name. Static fields, listeners, and captured callbacks can keep entire object graphs reachable. Releasing a reference also does not promptly close an external file or socket.']),
 'constructors':('Keep partially built objects private', ['Do not publish this to another thread or callback before construction finishes. The observer can see an object whose invariants have not been established. Calling an overridable method from a constructor can also dispatch to subclass code before subclass initialization completes.', 'Validate related fields together. Two fields can each be individually valid while their combination is invalid, such as an end timestamp before a start timestamp. Constructor success should mean the complete object state is usable.']),
 'encapsulation':('A getter can leak ownership', ['Returning the internal mutable list gives callers a route around the object’s validation methods. An unmodifiable wrapper blocks writes through that wrapper but still reflects changes made through another reference to the backing list.', 'Choose a snapshot, read-only live view, or explicitly shared collection according to the contract. The choice affects both memory and what a reader can observe over time. Hiding fields with private does not by itself establish that contract.']),
 'inheritance':('Substitution has behavioral limits', ['A subclass inherits more than names: callers already have assumptions about the parent’s accepted inputs, results, and state changes. A child that unexpectedly rejects valid parent inputs or changes units breaks those assumptions even if the code compiles.', 'Prefer composition when the new type needs to use another object without promising that it can replace that object. Inherited mutable protected fields can make invariants harder to control because several layers can alter them.']),
 'interfaces':('Default methods still need conflict rules', ['An interface can provide a default instance method, but that does not give it per-instance field storage. If unrelated interfaces supply conflicting defaults, an implementing class may need to resolve the conflict explicitly.', 'A method signature is only part of a contract. Document null handling, ownership, side effects, and any required performance bound. Two implementations with the same signature can still behave incompatibly when those rules differ.']),
 'arraylist':('Capacity and public views', ['Capacity is backing storage; size is the number of accessible elements. ensureCapacity does not add readable elements. get(size) is still invalid even when extra capacity has already been reserved.', 'subList is a view, not a detached ArrayList. Structural edits to the parent outside the view can invalidate assumptions made by the view. Copy the sublist when a reader needs independent structure, and include that O(k) copying cost.']),
 'arraydeque':('Endpoint absence and memory retention', ['ArrayDeque rejects null elements, so poll returning null can clearly mean no element was available. It is not a blocking queue and does not wait for a producer to add another element.', 'A deque can grow to absorb a burst and may retain backing-array capacity after removals. Empty size is not proof that all storage returned to the runtime. Bound queued work according to the application’s memory budget.']),
 'collection-choices':('A contract is narrower than an implementation', ['Declare List when callers need list operations, but choose the implementation from the actual workload. A contract-compatible substitution can still change performance: repeated indexed access that is cheap on an array-backed list is expensive on linked storage.', 'Map is not a Collection subtype. Its key set, value collection, and entry set expose views of the mappings with their own mutation rules. Decide whether the caller receives a live view or a copied snapshot.']),
}
for slug,(heading,paragraphs) in notes.items():
 e=by_path['java/'+slug]; marker='<h3>Common Mistakes</h3>'
 addition='<h2>'+heading+'</h2>'+''.join(p(text) for text in paragraphs)
 if '<h2>'+heading+'</h2>' not in e['body']:
  e['body']=e['body'].replace(marker,addition+marker,1)
 e['updated_at']='2026-09-28T10:00:00+00:00'
 e['data']['reading_minutes']=max(3,round(len(re.sub('<[^>]+>',' ',e['body']).split())/160))

# Correct a previous section-slug mismatch so interview lessons appear in their rail.
by_path['java/linkedlist-interview']['subject']='java-interview'
# Module order is also the previous/next lesson order.
for hub in (core,adv,collection,dsa):
 for index,path in enumerate(path for module in hub['data']['modules'] for path in module['lessons']):
  by_path[path]['sort_order']=index+1
 hub['updated_at']='2026-09-28T10:00:00+00:00'

# Give every Java page a small set of deliberate in-text cross-references.
for entry in entries:
 if not entry['path'].startswith('java/'):continue
 entry['body']=re.sub(r'<h3>Common Mistakes</h3>', '<h3>Common Mistakes</h3>',entry['body'])
 related=entry['data'].get('related',[])
 if entry['type']=='article' and '<a href=' not in entry['body'] and related:
  refs=[ref for ref in related if ref['path'] in by_path and ref['path']!=entry['path']][:3]
  if refs:
   line='Continue with '+', '.join('<a href="/'+ref['path']+'">'+html.escape(ref['title'])+'</a>' for ref in refs)+'.'
   entry['body']=entry['body'].replace('<h3>Common Mistakes</h3>','<h2>Connected lessons</h2>'+p(line)+'<h3>Common Mistakes</h3>',1)

(ROOT/'src/data/fixtures.json').write_text(json.dumps(entries,indent=2,ensure_ascii=False)+'\n')
out=ROOT.parent.parent/'outputs'
java=[entry for entry in entries if entry['path'].startswith('java/') or entry['path'] in ('quizzes/java-basics','quizzes/java-linkedlist')]
(out/'aitrove-java-content.json').write_text(json.dumps(java,indent=2,ensure_ascii=False)+'\n')
(out/'aitrove-preview-content.json').write_text(json.dumps(entries,indent=2,ensure_ascii=False)+'\n')
(out/'java-linkedlist-tutorial.html').write_text(by_path['java/linkedlist']['body'])
report={'newLessonPages':len([path for path in new if path not in ['java/generics','java/exceptions']]),'rewrittenLessons':['java/generics','java/exceptions','java/methods'],'expandedFoundationPages':len(notes),'javaPages':len(java),'javaLessons':len([e for e in java if e['type']=='article']),'paths':new}
(out/'java-expansion-inventory.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
