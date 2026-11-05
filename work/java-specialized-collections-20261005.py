"""Add original Java specialized-collection lessons and a review quiz."""
import copy
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
lookup = {row["path"]: row for row in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()

lessons = [
    dict(slug="bitset-length-versus-cardinality", title="Java BitSet: distinguish logical length, capacity, and set-bit count", group="Compact sets and views", release=17,
         definition="BitSet.length returns one beyond the highest set index, cardinality counts true bits, and size reports implementation storage capacity. These values answer different questions.",
         details="The method reports the highest active receipt slot and total active slots without mistaking allocated capacity for a business identifier. An empty BitSet has length zero, so the highest index is represented as -1. A sparse set with only slot 82 active has cardinality one and length 83. BitSet grows to hold high indexes, which can make a single erroneous ID expensive. Validate identifiers before calling set; BitSet is not synchronized for concurrent mutation.",
         case="The importer marks slot 82 and then clears it. Its logical length returns to zero even though its backing storage may remain allocated. Using size as the number of processed receipts would report capacity instead of work done.",
         code='''import java.util.BitSet;
import java.util.Objects;

public class ActiveReceiptSlots {
    public record Summary(int highestSlot, int activeCount) { }

    public static Summary summarize(BitSet activeSlots) {
        Objects.requireNonNull(activeSlots);
        int logicalLength = activeSlots.length();
        return new Summary(logicalLength == 0 ? -1 : logicalLength - 1,
                activeSlots.cardinality());
    }
}''',
         cost="Computing cardinality scans the words used by the bit set, taking O(W) time for W stored machine words; highest-set-bit lookup is tied to that representation. The method adds O(1) result storage. A very high index can enlarge the underlying bit vector far beyond the number of true bits.",
         mistakes=["Do not use size as the count of true bits.", "Do not return length as the highest index without subtracting one for a nonempty set.", "Do not set unvalidated huge indexes in a sparse business ID space."],
         related=["java/bitset-next-set-bit-range", "java/immutable-collections", "dsa/array-data-structure-guide"]),
    dict(slug="bitset-next-set-bit-range", title="Java BitSet nextSetBit: scan a bounded index range without walking gaps", group="Compact sets and views", release=11,
         definition="BitSet.nextSetBit finds the next true bit at or after a starting index, returning -1 when none exists. A bounded scan must still enforce its end index and result cap.",
         details="The method returns at most 47 receipt slots in a half-open interval. It validates nonnegative ordered bounds, then jumps between set bits rather than testing every possible index. The loop stops before the exclusive upper bound. Because every visited bit is strictly less than an int upper bound, incrementing that bit cannot overflow here. A cap protects output memory and prevents one request from enumerating an enormous set. The input is caller-owned and must not be mutated concurrently without synchronization.",
         case="Active slots are 3, 47, and 82. A scan of [40, 82) returns only 47. Slot 82 is outside the half-open range even though its bit is set.",
         code='''import java.util.ArrayList;
import java.util.BitSet;
import java.util.List;
import java.util.Objects;

public class ReceiptSlotWindow {
    public static List<Integer> active(BitSet slots, int fromInclusive, int toExclusive) {
        Objects.requireNonNull(slots);
        if (fromInclusive < 0 || toExclusive < fromInclusive)
            throw new IllegalArgumentException("Invalid slot range");
        List<Integer> found = new ArrayList<>();
        for (int slot = slots.nextSetBit(fromInclusive);
                slot >= 0 && slot < toExclusive;
                slot = slots.nextSetBit(slot + 1)) {
            if (found.size() == 47) throw new IllegalStateException("Too many active slots");
            found.add(slot);
        }
        return List.copyOf(found);
    }
}''',
         cost="The scan visits K set bits and searches the underlying words across the requested span, rather than performing one test per missing index. Result memory is O(K) with K capped at 47. The returned immutable list copies its elements once.",
         mistakes=["Do not include the exclusive end slot.", "Do not forget that nextSetBit returns -1 when no later bit exists.", "Do not scan an unbounded range into an unbounded output list."],
         related=["java/bitset-length-versus-cardinality", "java/localdate-exclusive-range", "dsa/array-data-structure-guide"]),
    dict(slug="enumset-complement-deny-policy", title="Java EnumSet complementOf: derive a default-deny capability set", group="Compact sets and views", release=11,
         definition="EnumSet.complementOf returns a new set containing enum constants absent from the supplied EnumSet. Its universe is the entire enum type, not just constants known to one caller.",
         details="The helper constructs a fresh denied set from an allowed capability set. Adding a new enum constant automatically puts it in denied until the policy explicitly allows it, which is appropriate for this default-deny design. The result is a separate mutable EnumSet; changing allowed later does not update the previous result. If a product instead interprets the complement as granted permissions, a newly introduced constant could become granted accidentally. The allowed set itself still requires an authorization source and review.",
         case="A release adds ARCHIVE. Existing callers allow only READ and EXPORT. The computed denied set includes ARCHIVE without changing the callers' allowlists.",
         code='''import java.util.EnumSet;
import java.util.Objects;

public class ReceiptCapabilityPolicy {
    public enum Capability { READ, EXPORT, DELETE, ARCHIVE }

    public static EnumSet<Capability> denied(EnumSet<Capability> allowed) {
        Objects.requireNonNull(allowed);
        return EnumSet.complementOf(allowed);
    }
}''',
         cost="Complement construction visits the enum universe and copies a compact bit representation, taking O(E) work in the number of enum constants under a portable cost model and O(E) result bits. The policy computation is small but should not replace explicit authorization checks at the action boundary.",
         mistakes=["Do not use a complement as granted permissions without reviewing new enum constants.", "Do not assume the returned set is a live view of allowed.", "Do not treat enum membership alone as proof that a caller is authorized."],
         related=["java/enummap-null-and-order", "java/enumset-typed-empty-source", "java/immutable-collections"]),
    dict(slug="enumset-typed-empty-source", title="Java EnumSet: retain element type when a source collection is empty", group="Compact sets and views", release=11,
         definition="EnumSet.copyOf a non-EnumSet collection needs at least one element to infer its enum type; noneOf states the element class explicitly and works for an empty source.",
         details="The helper starts with a typed empty EnumSet, then adds supplied review states. It returns an independent mutable set even when the source is empty. Duplicate states collapse by set semantics, and null elements are rejected. If the API promises an immutable result, wrap or copy it separately; returning EnumSet transfers mutation ownership to the caller. This lesson concerns type inference and collection ownership, not permission policy.",
         case="An intake has no review flags. Building EnumSet.copyOf from an ordinary empty List throws because the enum type cannot be inferred. The typed empty set returns normally.",
         code='''import java.util.Collection;
import java.util.EnumSet;
import java.util.Objects;

public class ReceiptReviewStates {
    public enum State { NEW, CHECKED, HELD, RELEASED }

    public static EnumSet<State> copy(Collection<State> states) {
        Objects.requireNonNull(states);
        EnumSet<State> result = EnumSet.noneOf(State.class);
        result.addAll(states);
        return result;
    }
}''',
         cost="Copying N source elements costs O(N) time and compact O(E) bit storage for E enum constants. It is a new set, so later mutation of the source does not change the result.",
         mistakes=["Do not call EnumSet.copyOf on an ordinary empty collection and expect type inference.", "Do not assume the returned EnumSet is immutable.", "Do not silently accept null states; EnumSet rejects them."],
         related=["java/enumset-complement-deny-policy", "java/immutable-collections", "java/list-copyof-element-alias"]),
    dict(slug="treeset-backed-range-view", title="Java NavigableSet subSet: account for a live backed range", group="Compact sets and views", release=11,
         definition="NavigableSet.subSet returns a backed view of keys in a specified range. Mutations through either view or source are visible through the other.",
         details="The method returns a half-open receipt-ID range. Its caller owns the underlying set and must keep it alive and coordinate any concurrent access; TreeSet itself is not thread-safe. Inserting an out-of-range value through the view throws IllegalArgumentException. If a stable snapshot is needed, copy the view into a new TreeSet under appropriate synchronization. Comparator order defines the meaning of from and to; this sample assumes natural long ordering. The range validates reversed endpoints before construction.",
         case="A report asks for IDs [40, 80). After the view is created, the owner adds ID 47 to the source set. The view now contains 47. Attempting to add 82 through the view fails as out of range.",
         code='''import java.util.NavigableSet;
import java.util.Objects;

public class ReceiptIdRangeView {
    public static NavigableSet<Long> between(NavigableSet<Long> receiptIds,
            long fromInclusive, long toExclusive) {
        Objects.requireNonNull(receiptIds);
        if (toExclusive < fromInclusive)
            throw new IllegalArgumentException("Reversed receipt range");
        return receiptIds.subSet(fromInclusive, true, toExclusive, false);
    }
}''',
         cost="Creating the view uses O(1) wrapper state. Tree-based lookup or insertion through it is O(log N) for N stored IDs; iterating K matching IDs is O(K) after locating the start. A stable copy costs O(K) storage and additional insertion work.",
         mistakes=["Do not treat the returned range as a snapshot.", "Do not insert outside its bounds.", "Do not mutate an unsynchronized TreeSet concurrently through source and view."],
         related=["java/navigable-map-ranges", "java/treeset-comparator-collision", "java/collections-unmodifiable-live-view"]),
    dict(slug="priorityblockingqueue-explicit-capacity", title="Java PriorityBlockingQueue: add an admission limit to an unbounded priority queue", group="Concurrent collections", release=17,
         definition="PriorityBlockingQueue orders retrieval by priority but is logically unbounded; its constructor argument is an initial capacity, not a maximum backlog.",
         details="The wrapper acquires one of 47 permits before offering a job and releases it when a worker takes that job. This bounds jobs waiting in the queue, not jobs already being processed by workers. The queue comparator orders priority descending and receipt ID ascending for a defined tie break. A failed offer releases the permit. The queue remains private so callers cannot bypass the gate with direct insertion or removal. A production service must also cap producer concurrency and define shutdown and task-failure handling.",
         case="All 47 waiting slots are filled. A new receipt job is rejected immediately even though PriorityBlockingQueue itself would otherwise accept it and grow. A worker take releases one waiting slot.",
         code='''import java.util.Comparator;
import java.util.Objects;
import java.util.concurrent.PriorityBlockingQueue;
import java.util.concurrent.Semaphore;

public class BoundedPriorityReceiptInbox {
    public record Job(int priority, long receiptId) { }
    private final Semaphore waitingSlots = new Semaphore(47);
    private final PriorityBlockingQueue<Job> jobs = new PriorityBlockingQueue<>(47,
            Comparator.comparingInt(Job::priority).reversed()
                    .thenComparingLong(Job::receiptId));

    public boolean submit(Job job) {
        Objects.requireNonNull(job);
        if (!waitingSlots.tryAcquire()) return false;
        boolean added = false;
        try {
            added = jobs.offer(job);
            return added;
        } finally {
            if (!added) waitingSlots.release();
        }
    }

    public Job take() throws InterruptedException {
        Job job = jobs.take();
        waitingSlots.release();
        return job;
    }
}''',
         cost="Insertion and removal are O(log N) heap operations for N queued jobs, capped here at 47 by the permit gate. The gate uses O(1) extra state. Worker execution and producer tasks are outside this queue bound.",
         mistakes=["Do not treat initial capacity or remainingCapacity as a backlog cap.", "Do not expose the underlying queue for bypass insertion or removal.", "Do not forget that priority service can starve low-priority jobs even with bounded storage."],
         related=["java/priorityqueue-tie-order", "java/blocking-queues", "java/linkedblockingdeque-urgent-admission"]),
    dict(slug="copyonwritearrayset-listener-snapshot", title="Java CopyOnWriteArraySet: publish against a stable listener snapshot", group="Concurrent collections", release=11,
         definition="CopyOnWriteArraySet provides snapshot iterators and copies its backing array on writes. It fits small listener registries with frequent reads and infrequent changes.",
         details="A receipt listener added during one publication is absent from that publication's iterator and can participate in the next one. Removing a listener likewise does not retroactively remove it from an iterator already obtained. Duplicate listeners are judged by equals, not object identity. Callbacks run on the publisher's thread; one slow or failing listener can delay or abort later callbacks. The sample leaves callback failure visible so the service can set an explicit isolation policy.",
         case="A listener registers an audit listener while handling receipt 47. The audit listener does not receive 47 from that in-progress publication, but it can receive receipt 82 afterward.",
         code='''import java.util.Objects;
import java.util.concurrent.CopyOnWriteArraySet;

public class ReceiptListenerRegistry {
    public interface Listener { void received(long receiptId); }
    private final CopyOnWriteArraySet<Listener> listeners = new CopyOnWriteArraySet<>();

    public boolean add(Listener listener) {
        return listeners.add(Objects.requireNonNull(listener));
    }

    public boolean remove(Listener listener) {
        return listeners.remove(listener);
    }

    public void publish(long receiptId) {
        for (Listener listener : listeners) listener.received(receiptId);
    }
}''',
         cost="Publishing to L listeners is O(L) callback dispatch without copying for each read. Adding or removing is O(L) search plus an O(L) array copy on change, with a temporary second array. This is expensive for high-churn large sets.",
         mistakes=["Do not expect a newly added listener to join an iteration already in progress.", "Do not treat callbacks as asynchronous or isolated from each other's failures.", "Do not choose copy-on-write for frequent writes and large registries without measuring allocation."],
         related=["java/copyonwritearraylist-listener-registry", "java/concurrent-map", "java/linkedblockingdeque-urgent-admission"]),
    dict(slug="linkedblockingdeque-urgent-admission", title="Java LinkedBlockingDeque: bound urgent and normal work in one queue", group="Concurrent collections", release=11,
         definition="LinkedBlockingDeque can enforce a fixed capacity while admitting work at either end. offerFirst and offerLast report a full queue without blocking.",
         details="The inbox uses 47 slots. Urgent receipts enter at the front, normal receipts at the back, and workers take from the front. Both admission paths share the same capacity. Repeated urgent arrivals can starve older normal items, so a production scheduler may need fairness or separate reserved capacity. The dequeue operation is interruptible. The wrapper owns the queue and does not expose mutating methods that could circumvent admission policy.",
         case="There are 47 waiting receipts. Both urgent and normal submission return false rather than growing memory. When a worker takes one, exactly one slot opens for either class.",
         code='''import java.util.Objects;
import java.util.concurrent.LinkedBlockingDeque;

public class ReceiptWorkDeque {
    private final LinkedBlockingDeque<String> waiting = new LinkedBlockingDeque<>(47);

    public boolean submitUrgent(String receiptId) {
        return waiting.offerFirst(Objects.requireNonNull(receiptId));
    }

    public boolean submitNormal(String receiptId) {
        return waiting.offerLast(Objects.requireNonNull(receiptId));
    }

    public String take() throws InterruptedException {
        return waiting.takeFirst();
    }
}''',
         cost="End insertion and removal are O(1) queue work aside from lock contention or blocking, with O(N) node storage capped at 47. The cap covers waiting items; worker execution and upstream request retention need separate limits.",
         mistakes=["Do not use the no-argument constructor when a real queue cap is required.", "Do not ignore false from offerFirst or offerLast.", "Do not assume urgent-first ordering guarantees fair service for normal work."],
         related=["java/blocking-queues", "java/priorityblockingqueue-explicit-capacity", "java/threadpool-caller-runs"]),
]

quiz_path = "quizzes/java-specialized-collections"
new_paths = ["java/" + lesson["slug"] for lesson in lessons] + [quiz_path]
assert len(new_paths) == len(set(new_paths)) and not set(new_paths) & lookup.keys()
titles = {row["path"]: row["title"] for row in entries}
titles.update({"java/" + lesson["slug"]: lesson["title"] for lesson in lessons})
titles[quiz_path] = "Java specialized collections quiz"

def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'

def links(paths):
    return "<ul>" + "".join("<li>" + link(path) + "</li>" for path in dict.fromkeys(paths)) + "</ul>"

def related(paths):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(paths)]

new_rows = []
for index, lesson in enumerate(lessons):
    path = "java/" + lesson["slug"]
    cohort = ["java/" + other["slug"] for other in lessons if other["group"] == lesson["group"] and other["slug"] != lesson["slug"]]
    connections = lesson["related"] + cohort + [quiz_path, "java/advanced-java"]
    body = ("<p>" + html.escape(lesson["definition"]) + "</p>"
            + "<h2>Operational contract</h2><p>" + html.escape(lesson["details"]) + "</p>"
            + "<h2>Failure case</h2><p>" + html.escape(lesson["case"]) + "</p>"
            + '<h2>Java code</h2><pre><code class="language-java">' + html.escape(lesson["code"], quote=False) + "</code></pre>"
            + "<h2>Performance and ownership cost</h2><p>" + html.escape(lesson["cost"]) + "</p>"
            + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in lesson["mistakes"]) + "</ul>"
            + "<h2>Connected lessons</h2>" + links(connections))
    row = copy.deepcopy(lookup["java/casts"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), path=path,
               title=lesson["title"], summary=lesson["definition"], body=body,
               subject="java-advanced", category="Programming", tags=["java", lesson["group"].lower(), lesson["slug"]],
               difficulty="Advanced", sort_order=35800 + index * 10, status="published",
               featured=False, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "java/java", "section_path": "java/advanced-java", "kind": "tutorial",
                   "content_format": "html", "reading_minutes": max(5, round(len(re.sub("<[^>]+>", " ", body).split()) / 150)),
                   "author_path": "authors/aitrove-editorial", "related": related(connections), "seo_ready": True,
                   "java_release": lesson["release"], "java_version": str(lesson["release"]) + "+"}
    new_rows.append(row)

questions = [
    ("Which BitSet method counts true bits?", "cardinality", "size", "length", "Capacity and highest set index are different quantities."),
    ("What ends a nextSetBit scan when no bit remains?", "A return value of -1", "A null bit", "An empty String", "Bounded scans also enforce their exclusive end."),
    ("What does complementOf include?", "Every enum constant absent from the input set", "Only values present in the input", "Only deprecated enum values", "The universe is the entire enum type."),
    ("How should an empty ordinary collection become an EnumSet?", "Start with noneOf and addAll", "Call copyOf without a type", "Cast it to EnumSet", "An ordinary empty collection does not reveal its enum element class."),
    ("What does NavigableSet.subSet return?", "A backed range view", "An independent snapshot", "A sorted array", "Changes can appear through source and view."),
    ("Does PriorityBlockingQueue initial capacity cap its backlog?", "No, add an explicit admission limit", "Yes, offer blocks at that count", "Yes, put rejects new work", "The queue is logically unbounded."),
    ("When does a listener added during copy-on-write iteration appear?", "On a later iteration", "Immediately in the current iterator", "Never", "The iterator observes its earlier snapshot."),
    ("What does a full bounded LinkedBlockingDeque offer return?", "False", "A new node beyond capacity", "The oldest item", "The offer methods report admission failure."),
]
quiz = copy.deepcopy(lookup["quizzes/java-io"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Check bit indexes, enum sets, backed views, and concurrent queue admission.",
            body="<p>Choose the contract supported by each collection.</p><h2>Read the lessons</h2>" + links(new_paths[:-1]) + "<h3>Common Mistakes</h3><p>Do not confuse an initial allocation size with a resource limit.</p>",
            sort_order=35950, status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"].update(content_format="html", subject_root="java/java", section_path="java/java-quizzes", duration_minutes=14, seo_ready=True,
                    questions=[{"prompt": prompt, "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                "answer": (-index) % 3, "explanation": explanation}
                               for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)])
new_rows.append(quiz)

for group in dict.fromkeys(lesson["group"] for lesson in lessons):
    selected = ["java/" + item["slug"] for item in lessons if item["group"] == group]
    hub = lookup["java/advanced-java"]
    hub["data"]["modules"].append({"title": "Collections: " + group, "summary": "Track collection views, capacity, and mutation ownership.", "lessons": selected})
    hub["body"] += "<h2>Collections: " + html.escape(group) + "</h2><p>Choose the data structure with its resource and view contract in mind.</p>" + links(selected)
    hub["updated_at"] = stamp
lookup["java/java-quizzes"]["data"]["modules"].append({"title": "Specialized collections", "summary": "Test bit sets, enum sets, backed views, and queues.", "lessons": [quiz_path]})
lookup["java/java-quizzes"]["body"] += "<h2>Specialized collections</h2><p>Check the new Java collection decisions.</p>" + links([quiz_path])
lookup["java/java-quizzes"]["updated_at"] = stamp
lookup["java/java"]["body"] += "<h2>Further Java collection topics</h2><p>Study compact sets, range views, and bounded concurrent admission.</p>" + links(new_paths)
lookup["java/java"]["updated_at"] = stamp

backlinks = {
    "java/immutable-collections": ["java/bitset-length-versus-cardinality", "java/enumset-typed-empty-source"],
    "java/navigable-map-ranges": ["java/treeset-backed-range-view"],
    "java/priorityqueue-tie-order": ["java/priorityblockingqueue-explicit-capacity"],
    "java/blocking-queues": ["java/priorityblockingqueue-explicit-capacity", "java/linkedblockingdeque-urgent-admission"],
    "java/copyonwritearraylist-listener-registry": ["java/copyonwritearrayset-listener-snapshot"],
}
for path, targets in backlinks.items():
    row = lookup[path]
    row["body"] += "<p><strong>Continue with:</strong> " + ", ".join(link(target) for target in targets) + ".</p>"
    row["data"]["related"] = related([item["path"] for item in row["data"].get("related", [])] + targets)
    row["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newArticles": len(lessons), "newQuizzes": 1, "newPaths": new_paths}))
