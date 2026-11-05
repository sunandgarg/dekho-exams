"""Add ten original Java concurrency lessons and one review quiz."""

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
lookup = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()

lessons = [
    dict(
        slug="concurrenthashmap-computeifabsent-counter",
        title="Java ConcurrentHashMap.computeIfAbsent: create a counter once per key",
        group="Concurrent maps and snapshots", release=11,
        definition="ConcurrentHashMap.computeIfAbsent establishes a value for one absent key atomically; a LongAdder can then absorb frequent updates to that key without replacing a boxed count on every increment.",
        details="This counter registry creates an adder only when a depot key is absent. The mapping callback only constructs the value: it does no I/O, no recursive map update, and no work that can wait for another mapping. A null result would leave the key absent, but this callback always returns an adder. The increment occurs after the mapping operation. The map therefore guarantees safe installation, while the adder owns the separate count update. Keep depot identifiers bounded or evict stale keys under an explicit retention policy; a concurrent map does not limit its own key population.",
        case="Forty-seven request workers record a new depot at the same time. They may race to reach computeIfAbsent, yet every successful call obtains the installed counter for that key and increments it. A dashboard that reads several depot sums while requests continue still observes a moving aggregate, not one transaction across depots.",
        code='''import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.LongAdder;

public class DepotArrivalCounters {
    private final ConcurrentHashMap<String, LongAdder> arrivals = new ConcurrentHashMap<>();

    public void record(String depotId) {
        arrivals.computeIfAbsent(depotId, ignoredDepot -> new LongAdder()).increment();
    }

    public long count(String depotId) {
        LongAdder counter = arrivals.get(depotId);
        return counter == null ? 0 : counter.sum();
    }
}''',
        cost="Expected key lookup is near O(1) with normal hashing, but contention and collision structure affect latency. Memory is O(K) for K retained depot keys plus adder cells created under contention. sum reads concurrent cells and is not an atomic snapshot with updates or other keys.",
        mistakes=["Do not perform remote work or update the same map inside the mapping callback.", "Do not use a LongAdder sum as an exact multi-key accounting snapshot.", "Do not let untrusted key cardinality grow without a retention rule."],
        related=["java/concurrenthashmap-compute-contention", "java/long-adder", "java/concurrent-map"]),
    dict(
        slug="concurrentskiplistmap-time-window",
        title="Java ConcurrentSkipListMap: inspect an ordered time window",
        group="Concurrent maps and snapshots", release=11,
        definition="ConcurrentSkipListMap keeps keys ordered while permitting concurrent updates. Its range views restrict keys by boundary, but a traversal during writes is not a frozen report.",
        details="The sample stores delivery events under unique sequence numbers and reads the half-open interval [firstInclusive, lastExclusive). The returned subMap is backed by the live map. Copying up to 47 entries into a list limits this method's result size but does not give an instantaneous snapshot. A separate transaction, version, or pause protocol is needed when the report must represent one exact point in time. The map rejects null keys and values. A single sequence per event prevents one event from overwriting another with the same timestamp.",
        case="A dispatch console asks for events numbered 240 through 286 while another worker inserts event 261. The range excludes event 287 by definition, but its iteration may or may not see event 261 depending on timing. The console may use that list for monitoring; it must not certify a ledger from it.",
        code='''import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ConcurrentSkipListMap;

public class DispatchSequenceWindow {
    private final ConcurrentSkipListMap<Long, String> events = new ConcurrentSkipListMap<>();

    public void record(long sequence, String eventId) {
        if (events.putIfAbsent(sequence, eventId) != null)
            throw new IllegalArgumentException("Sequence already assigned");
    }

    public List<String> read(long firstInclusive, long lastExclusive) {
        if (firstInclusive > lastExclusive) throw new IllegalArgumentException("Reversed window");
        List<String> selected = new ArrayList<>();
        for (String eventId : events.subMap(firstInclusive, true, lastExclusive, false).values()) {
            if (selected.size() == 47) throw new IllegalStateException("Window exceeds 47 events");
            selected.add(eventId);
        }
        return List.copyOf(selected);
    }
}''',
        cost="An ordered insertion or boundary lookup has expected O(log N) work for N entries. Copying R visible entries costs O(R) time and O(R) result memory, capped here at 47. The live range still retains its backing map; this sample does not bound the map's total size.",
        mistakes=["Do not treat a backed range view as an immutable copy.", "Do not use weakly consistent iteration for an exact financial snapshot.", "Do not key distinct events by a timestamp that can collide."],
        related=["java/concurrent-sorted-map", "java/concurrent-map", "java/iterators"]),
    dict(
        slug="copyonwritearraylist-listener-registry",
        title="Java CopyOnWriteArrayList: dispatch against a listener snapshot",
        group="Concurrent maps and snapshots", release=11,
        definition="CopyOnWriteArrayList publishes a fresh array when it changes. Iterators hold a snapshot, so registration changes do not disrupt an in-flight listener dispatch.",
        details="The registry fits a read-heavy system with infrequent listener changes. addIfAbsent avoids duplicate registration by equality. A dispatch gets the iterator view available when iteration begins; removing a listener during dispatch does not retract a callback already present in that snapshot. Callback failure is not rolled back and this sample deliberately lets it propagate to the caller. In a production event bus, failure isolation and delivery guarantees need their own policy.",
        case="A warehouse adds one audit listener while 47 shipment notices are being dispatched. An in-progress traversal keeps the listeners it started with. The next dispatch can see the new registration. This makes iteration predictable, but it does not promise that a removal stops an already-started callback.",
        code='''import java.util.concurrent.CopyOnWriteArrayList;
import java.util.function.Consumer;

public class ShipmentNoticeListeners {
    private final CopyOnWriteArrayList<Consumer<String>> listeners = new CopyOnWriteArrayList<>();

    public void register(Consumer<String> listener) {
        listeners.addIfAbsent(listener);
    }

    public void remove(Consumer<String> listener) {
        listeners.remove(listener);
    }

    public void dispatch(String shipmentId) {
        for (Consumer<String> listener : listeners) listener.accept(shipmentId);
    }
}''',
        cost="A mutation copies the backing array, so it costs O(L) time and extra O(L) array memory for L listeners. A dispatch visits O(L) callbacks and its iterator can retain an old array until the traversal ends. High-churn registration is the wrong workload for this structure.",
        mistakes=["Do not choose copy-on-write storage when writes dominate.", "Do not assume removal cancels callbacks already captured by an iterator.", "Do not confuse snapshot iteration with transactional callback delivery."],
        related=["java/iterators", "java/concurrent-map", "java/atomicreference-immutable-map-snapshot"]),
    dict(
        slug="atomicreference-immutable-map-snapshot",
        title="Java AtomicReference: publish one immutable map snapshot",
        group="Concurrent maps and snapshots", release=11,
        definition="An AtomicReference can publish one immutable aggregate map as a unit. Readers obtain a coherent version without coordinating each key separately.",
        details="The publisher copies the current map, changes one depot balance, then installs an immutable replacement through updateAndGet. The lambda may run more than once after contention, so it contains only pure in-memory construction; never send an invoice or write a database row there. Map.copyOf rejects null keys and values. Every snapshot returned to a reader is one published version, although the reader can become stale immediately after fetching it. This fits a small, rarely updated configuration or report map rather than a high-volume counter.",
        case="A pricing page must show one internally consistent set of 47 depot fees. A reader obtains one map reference and uses all its entries. Concurrent publication cannot change that map under the reader's feet. If fees are updated constantly, copying the whole map on each update becomes expensive.",
        code='''import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;

public class DepotFeeSnapshots {
    private final AtomicReference<Map<String, Long>> published =
        new AtomicReference<>(Map.of());

    public void setFee(String depotId, long feeCents) {
        if (feeCents < 0) throw new IllegalArgumentException("Negative fee");
        published.updateAndGet(previous -> {
            Map<String, Long> next = new HashMap<>(previous);
            next.put(depotId, feeCents);
            if (next.size() > 47) throw new IllegalStateException("Too many depots");
            return Map.copyOf(next);
        });
    }

    public Map<String, Long> snapshot() {
        return published.get();
    }
}''',
        cost="A read is O(1) to obtain a reference. Each update copies O(K) entries and allocates O(K) memory for K keys; contention can repeat that work before a successful compare-and-set. The 47-key cap keeps that cost deliberate.",
        mistakes=["Do not put side effects in an update lambda that may be retried.", "Do not mutate a previously published map after publication.", "Do not equate one immutable in-memory version with a durable database transaction."],
        related=["java/atomics", "java/concurrent-map", "java/concurrentskiplistmap-time-window"]),
    dict(
        slug="delayqueue-retry-expiry",
        title="Java DelayQueue: release retry work only after its deadline",
        group="Timed queues and handoffs", release=11,
        definition="DelayQueue makes an element available to take only after its Delayed value reports a nonpositive remaining delay. Its capacity is unbounded unless the application adds admission control.",
        details="The ticket stores a monotonic nanoTime deadline and orders itself by that deadline. The scheduler rejects negative delays and accepts at most 47 seconds for this example. poll returns null when no ticket has expired, even if the queue contains future work. Distinct tickets sharing a deadline can be removed in either order; add a sequence field when tie order matters. The class itself has no backlog cap, so a service accepting untrusted retry volume needs a separate quota before scheduling.",
        case="An order retry is due after 23 seconds. The worker calls poll after 8 seconds and receives no ticket. A missing result does not mean the queue is empty. When the deadline passes, the ticket becomes eligible; worker scheduling can still delay actual processing beyond the due time.",
        code='''import java.time.Duration;
import java.util.concurrent.DelayQueue;
import java.util.concurrent.Delayed;
import java.util.concurrent.TimeUnit;

public class OrderRetryQueue {
    private final DelayQueue<RetryTicket> retries = new DelayQueue<>();

    public void schedule(String orderId, Duration delay) {
        if (delay.isNegative() || delay.compareTo(Duration.ofSeconds(47)) > 0)
            throw new IllegalArgumentException("Delay outside policy");
        retries.offer(new RetryTicket(orderId, System.nanoTime() + delay.toNanos()));
    }

    public String pollDue() {
        RetryTicket ticket = retries.poll();
        return ticket == null ? null : ticket.orderId;
    }

    private static final class RetryTicket implements Delayed {
        private final String orderId;
        private final long deadline;
        private RetryTicket(String orderId, long deadline) {
            this.orderId = orderId;
            this.deadline = deadline;
        }
        public long getDelay(TimeUnit unit) {
            return unit.convert(deadline - System.nanoTime(), TimeUnit.NANOSECONDS);
        }
        public int compareTo(Delayed other) {
            return Long.compare(deadline, ((RetryTicket) other).deadline);
        }
    }
}''',
        cost="Insertion and eligible-head removal use heap-like O(log N) work for N tickets; checking an ineligible head is cheap. Memory is O(N), with no built-in ceiling. The short 47-second horizon keeps signed nanoTime subtraction and ordering within a practical window, but does not cap queued volume.",
        mistakes=["Do not interpret poll returning null as an empty queue.", "Do not accept unlimited retry tickets into an unbounded queue.", "Do not use wall-clock time for elapsed-delay calculations."],
        related=["java/blocking-queues", "java/synchronousqueue-handoff", "java/priorityqueue-tie-order"]),
    dict(
        slug="exchanger-two-party-buffer-swap",
        title="Java Exchanger: swap buffers at a two-party rendezvous",
        group="Timed queues and handoffs", release=11,
        definition="Exchanger pairs two threads so each hands over one object and receives the other's object. A missing partner means waiting, timeout, or interruption rather than queued delivery.",
        details="A producer and consumer can exchange ownership of same-size byte buffers after each processing stage. The timed call bounds how long this method waits for a partner. Neither side may keep mutating the buffer it hands away after a successful exchange; the recipient now owns it. The exchanger passes object references, not copies. A timeout means this method did not complete an exchange, so the caller retains its original buffer and must decide whether to retry or stop. This sample has exactly two participants by contract.",
        case="One worker fills a 47-byte parcel label buffer while another has an empty 47-byte buffer ready. They meet and swap. If the second worker fails before reaching the rendezvous, the first returns through a timeout rather than blocking forever.",
        code='''import java.util.concurrent.Exchanger;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

public class ParcelBufferSwap {
    private final Exchanger<byte[]> buffers = new Exchanger<>();

    public byte[] swap(byte[] ownedBuffer) throws InterruptedException, TimeoutException {
        if (ownedBuffer.length != 47) throw new IllegalArgumentException("Expected 47 bytes");
        byte[] received = buffers.exchange(ownedBuffer, 3, TimeUnit.SECONDS);
        if (received.length != 47) throw new IllegalStateException("Partner used wrong buffer size");
        return received;
    }
}''',
        cost="The exchange transfers references in O(1) application work and requires two live participants; scheduling and contention control actual latency. Both 47-byte arrays already exist. It is not a queue or a capacity policy for arbitrary producer volume.",
        mistakes=["Do not retain write ownership of a buffer after handing it over.", "Do not assume the partner always arrives; handle timeout and interruption.", "Do not use a two-party exchanger as a many-message backlog."],
        related=["java/synchronousqueue-handoff", "java/blocking-queues", "java/linkedtransferqueue-receipt-handoff"]),
    dict(
        slug="linkedtransferqueue-receipt-handoff",
        title="Java LinkedTransferQueue: wait until a consumer receives work",
        group="Timed queues and handoffs", release=11,
        definition="LinkedTransferQueue can hand an item directly to a waiting consumer. Its transfer operation waits until receipt, which is different from merely enqueuing an item.",
        details="tryTransfer with a timeout waits up to three seconds for a consumer to receive the receipt ID, then reports success or failure. The consumer uses take. Successful transfer proves handoff to a consumer, not completion of that consumer's business work. The underlying linked queue can grow without an application cap if regular offer is used; this sample exposes only the timed handoff operation. On a timeout, the producer must decide whether to retry, persist the work, or reject it. Interruption propagates to the caller.",
        case="A depot publisher has an urgent receipt-47 notification. A worker already waiting on take can receive it immediately. If no worker receives within three seconds, the publisher sees false and can persist the notification for later delivery instead of silently treating it as processed.",
        code='''import java.util.concurrent.LinkedTransferQueue;
import java.util.concurrent.TimeUnit;

public class ReceiptTransferLane {
    private final LinkedTransferQueue<String> handoffs = new LinkedTransferQueue<>();

    public boolean handoff(String receiptId) throws InterruptedException {
        return handoffs.tryTransfer(receiptId, 3, TimeUnit.SECONDS);
    }

    public String awaitReceipt() throws InterruptedException {
        return handoffs.take();
    }
}''',
        cost="The handoff uses constant application storage per pending producer, but waiting producers still consume thread or virtual-thread resources. The timed operation has up to three seconds of wait and scheduling overhead. This class is not a durable broker; a received item can be lost if the consumer fails before committing its work.",
        mistakes=["Do not equate consumer receipt with successful business processing.", "Do not assume this unbounded queue enforces capacity.", "Do not discard work silently when the timed transfer returns false."],
        related=["java/synchronousqueue-handoff", "java/blocking-queues", "java/exchanger-two-party-buffer-swap"]),
    dict(
        slug="longaccumulator-high-water-mark",
        title="Java LongAccumulator: track a concurrent high-water mark",
        group="Thread state and metrics", release=11,
        definition="LongAccumulator combines submitted long values with a supplied associative function. A max accumulator records an observed high-water mark under concurrent updates.",
        details="The function Long::max has Long.MIN_VALUE as its identity, so an untouched accumulator is distinguishable from a recorded zero. The sample rejects negative queue depths and returns zero before any sample. get is a metric read, not a coordination signal or a transaction with the queue whose depth was measured. Use an atomic variable when one exact compare-and-set result controls a state transition. Resetting an accumulator while writers run is a separate interval policy and can lose a clean boundary between reporting periods.",
        case="Forty-seven workers sample backlog depth while shipments arrive. The maximum sample is useful for capacity monitoring. It does not prove the queue never briefly exceeded that value between samples, nor does it freeze the current queue length.",
        code='''import java.util.concurrent.atomic.LongAccumulator;

public class BacklogHighWaterMark {
    private final LongAccumulator maximum =
        new LongAccumulator(Long::max, Long.MIN_VALUE);

    public void observe(long pendingShipments) {
        if (pendingShipments < 0) throw new IllegalArgumentException("Negative backlog");
        maximum.accumulate(pendingShipments);
    }

    public long highestObserved() {
        long observed = maximum.get();
        return observed == Long.MIN_VALUE ? 0 : observed;
    }
}''',
        cost="A single update has expected low overhead, but contention can cause internal cells and extra O(T) metric-read work for T cells. Space can grow with contention. The max reduction is associative; a side-effecting or order-dependent function would not fit this design.",
        mistakes=["Do not use a metric read as an exact queue-state invariant.", "Do not reset while writers run without a period boundary.", "Do not choose a nonassociative or side-effecting accumulation function."],
        related=["java/long-adder", "java/atomics", "java/concurrentlinkedqueue-admission"]),
    dict(
        slug="threadlocal-context-restoration",
        title="Java ThreadLocal: restore request context when a pooled thread is reused",
        group="Thread state and metrics", release=11,
        definition="ThreadLocal stores a value for each thread, not for each logical request. A worker reused for another request can retain stale context unless a scoped operation restores or removes it.",
        details="The helper saves the current tenant, sets the new tenant for one synchronous Runnable, then restores the old value in finally. If there was no previous value it removes the entry, which prevents a pooled worker from carrying a tenant into the next task. Restoring rather than blindly removing also supports nested scopes on the same thread. This mechanism does not propagate to an asynchronous task automatically; pass identity explicitly or use a context mechanism whose lifetime matches the task. The tenant string here is diagnostic context, not authorization by itself.",
        case="A worker processes depot-47 and then depot-82 on the same pool thread. A failure during the first task still executes finally. The second task cannot inherit depot-47 from this helper, and a nested call returns to its outer tenant after the inner call completes.",
        code='''public class TenantTraceScope {
    private static final ThreadLocal<String> CURRENT_TENANT = new ThreadLocal<>();

    public static void run(String tenantId, Runnable operation) {
        String previous = CURRENT_TENANT.get();
        CURRENT_TENANT.set(tenantId);
        try {
            operation.run();
        } finally {
            if (previous == null) CURRENT_TENANT.remove();
            else CURRENT_TENANT.set(previous);
        }
    }

    public static String current() {
        return CURRENT_TENANT.get();
    }
}''',
        cost="get, set, and remove are expected O(1) per thread-local operation with per-thread storage. Each live worker can retain its current value until cleared or the worker ends. The finally block runs on ordinary exceptions; a process termination is outside that guarantee.",
        mistakes=["Do not treat a thread-local tenant as a security check.", "Do not assume a child or executor task inherits the caller's context.", "Do not remove unconditionally when nested scopes must restore a previous value."],
        related=["java/scoped-values", "java/virtual-threads", "java/exceptions"]),
    dict(
        slug="locksupport-condition-loop",
        title="Java LockSupport: park only inside a checked condition loop",
        group="Thread state and metrics", release=11,
        definition="LockSupport gives each thread at most one park permit. unpark can arrive before park, and park can return for timeout, interruption, or no reported reason.",
        details="This one-waiter gate publishes its waiting thread in a volatile field before checking the volatile ready flag. signal publishes ready first, then unparks the registered waiter. The waiting loop always rechecks ready after park; a wakeup alone does not prove the state changed. The deadline limits waiting to three seconds. A pre-existing interrupt returns false without consuming the interrupt status. This low-level primitive is best reserved for synchronization implementations; a CountDownLatch is simpler for ordinary one-shot application gates.",
        case="A release signal arrives just before the worker parks. The ready flag lets the worker proceed without sleeping. A spurious wakeup while ready remains false sends it around the loop. A missing signal eventually reaches its timeout rather than blocking forever.",
        code='''import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import java.util.concurrent.locks.LockSupport;

public class OneWaiterDispatchGate {
    private final AtomicReference<Thread> waiter = new AtomicReference<>();
    private volatile boolean ready;

    public boolean await() {
        Thread current = Thread.currentThread();
        if (!waiter.compareAndSet(null, current))
            throw new IllegalStateException("Only one waiter is supported");
        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(3);
        try {
            while (!ready) {
                if (current.isInterrupted()) return false;
                long remaining = deadline - System.nanoTime();
                if (remaining <= 0) return false;
                LockSupport.parkNanos(this, remaining);
            }
            return true;
        } finally {
            waiter.compareAndSet(current, null);
        }
    }

    public void signal() {
        ready = true;
        LockSupport.unpark(waiter.get());
    }
}''',
        cost="The condition check and permit transfer use O(1) application state. Waiting consumes scheduling time until signal, interrupt, or the three-second deadline. This is a one-shot, single-waiter gate; resetting it or supporting many waiters requires more state and an explicit race policy.",
        mistakes=["Do not treat a return from park as proof that the condition holds.", "Do not assume permits accumulate beyond one.", "Do not use a one-waiter field to coordinate multiple waiting threads."],
        related=["java/countdown-latch", "java/conditions", "java/virtual-threads"]),
]

quiz_path = "quizzes/java-concurrent-state"
quiz_title = "Java concurrent state and handoff quiz"
new_paths = ["java/" + lesson["slug"] for lesson in lessons] + [quiz_path]
assert len(new_paths) == len(set(new_paths)) and not set(new_paths) & lookup.keys()
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({"java/" + lesson["slug"]: lesson["title"] for lesson in lessons})
titles[quiz_path] = quiz_title


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
    cohort = ["java/" + other["slug"] for other in lessons
              if other["group"] == lesson["group"] and other["slug"] != lesson["slug"]]
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
               difficulty="Advanced", sort_order=34800 + index * 10, status="published",
               featured=False, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "java/java", "section_path": "java/advanced-java",
                   "kind": "tutorial", "content_format": "html", "reading_minutes": max(5, round(len(re.sub("<[^>]+>", " ", body).split()) / 150)),
                   "author_path": "authors/aitrove-editorial", "related": related(connections),
                   "seo_ready": True, "java_release": lesson["release"], "java_version": str(lesson["release"]) + "+"}
    new_rows.append(row)

questions = [
    ("What may a computeIfAbsent mapping callback safely do?", "Create a value quickly without changing the same map", "Call a remote payment service", "Recursively update that key", "The callback executes within a map update boundary."),
    ("Does a ConcurrentSkipListMap range view freeze the map?", "No, it remains backed by the map", "Yes, it copies all entries", "Only when keys are long", "Concurrent iteration is not one exact report version."),
    ("What happens to a CopyOnWriteArrayList iterator after registration changes?", "It keeps the array snapshot captured at iteration", "It fails immediately", "It mutates with the new registration", "Array copies make in-flight traversal stable."),
    ("Why must an AtomicReference update lambda avoid external side effects?", "Contention can cause the lambda to run again", "The map cannot contain 47 keys", "The reader always blocks", "A failed compare-and-set can retry the calculation."),
    ("What does DelayQueue.poll returning null establish?", "No element is due yet", "The queue is necessarily empty", "Every retry was processed", "Future-due elements can still be present."),
    ("After a successful Exchanger swap, who owns the handed buffer?", "The receiving partner", "Both threads for writes", "Neither thread", "The reference is transferred rather than copied."),
    ("What does a successful LinkedTransferQueue transfer prove?", "A consumer received the item", "Business processing committed", "The message was durably stored", "Receipt is earlier than application completion."),
    ("Is LongAccumulator.get a transaction with a queue's current size?", "No, it is a metric read", "Yes, when using max", "Only after reset", "Samples and queue state have separate boundaries."),
    ("What should a nested ThreadLocal scope do on exit?", "Restore its previous value", "Always set an empty string", "Leave the inner tenant in place", "A pool thread may handle another task after the scope."),
    ("Why recheck a condition after LockSupport.parkNanos?", "A return can be spurious or caused by timeout or interruption", "unpark stores unlimited permits", "The volatile flag is immutable", "Waking does not itself establish the application's condition."),
]
quiz = copy.deepcopy(lookup["quizzes/java-io"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + quiz_path)), path=quiz_path,
            title=quiz_title, summary="Check concurrent map, snapshot, handoff, metric, and thread-scope decisions.",
            body="<p>Choose the decision supported by each Java concurrency contract.</p><h2>Read the lessons</h2>" + links(new_paths[:-1]) + "<h3>Common Mistakes</h3><p>Do not call a moving metric a transaction or a consumer handoff a completed job.</p>",
            sort_order=34950, status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"].update(content_format="html", subject_root="java/java", section_path="java/java-quizzes",
                    duration_minutes=16, seo_ready=True,
                    questions=[{"prompt": prompt,
                                "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                "answer": (-index) % 3, "explanation": explanation}
                               for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)])
new_rows.append(quiz)

for group in dict.fromkeys(lesson["group"] for lesson in lessons):
    selected = ["java/" + item["slug"] for item in lessons if item["group"] == group]
    hub = lookup["java/advanced-java"]
    hub["data"]["modules"].append({"title": group, "summary": "Define visibility, ownership, handoff, and report boundaries.", "lessons": selected})
    hub["body"] += "<h2>" + html.escape(group) + "</h2><p>Choose a structure for the actual concurrency contract.</p>" + links(selected)
    hub["updated_at"] = stamp
lookup["java/java-quizzes"]["data"]["modules"].append({"title": "Concurrent state and handoff", "summary": "Test map, queue, snapshot, and thread-scope contracts.", "lessons": [quiz_path]})
lookup["java/java-quizzes"]["body"] += "<h2>Concurrent state and handoff</h2><p>Check the new concurrency decisions.</p>" + links([quiz_path])
lookup["java/java-quizzes"]["updated_at"] = stamp
lookup["java/java"]["body"] += "<h2>Further Java concurrency topics</h2><p>Study concurrent state, timed handoffs, and per-thread cleanup.</p>" + links(new_paths)
lookup["java/java"]["updated_at"] = stamp

backlinks = {
    "java/concurrent-map": ["java/concurrenthashmap-computeifabsent-counter", "java/atomicreference-immutable-map-snapshot"],
    "java/concurrent-sorted-map": ["java/concurrentskiplistmap-time-window"],
    "java/long-adder": ["java/longaccumulator-high-water-mark", "java/concurrenthashmap-computeifabsent-counter"],
    "java/blocking-queues": ["java/delayqueue-retry-expiry", "java/linkedtransferqueue-receipt-handoff"],
    "java/synchronousqueue-handoff": ["java/exchanger-two-party-buffer-swap", "java/linkedtransferqueue-receipt-handoff"],
    "java/virtual-threads": ["java/threadlocal-context-restoration"],
    "java/countdown-latch": ["java/locksupport-condition-loop"],
    "java/iterators": ["java/copyonwritearraylist-listener-registry", "java/concurrentskiplistmap-time-window"],
}
for old_path, targets in backlinks.items():
    old = lookup[old_path]
    old["body"] += "<p><strong>Continue with:</strong> " + ", ".join(link(target) for target in targets) + ".</p>"
    old["data"]["related"] = related([item["path"] for item in old["data"].get("related", [])] + targets)
    old["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newArticles": len(lessons), "newQuizzes": 1, "newPaths": new_paths}))
