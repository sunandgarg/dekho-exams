"""Add original Java concurrency contract lessons with executable examples."""

import copy
import datetime
import html
import json
import pathlib
import re
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILE = ROOT / "src/data/fixtures.json"
entries = json.loads(FILE.read_text())
lookup = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
added = []


def paragraph(value):
    escaped = html.escape(value)
    return "<p>" + re.sub(
        r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>",
        escaped,
    ) + "</p>"


def block(value, language="java"):
    return '<pre><code class="language-' + language + '">' + html.escape(value.strip(), quote=False) + "</code></pre>"


def add(slug, title, definition, sections, source, output, cost, mistakes, related, release=8):
    path = "java/" + slug
    if path in lookup:
        raise ValueError("Existing path: " + path)
    body = paragraph(definition)
    for heading, paragraphs in sections:
        body += "<h2>" + heading + "</h2>" + "".join(paragraph(item) for item in paragraphs)
    body += "<h2>Working program</h2>" + block(source)
    body += "<h3>Output</h3>" + block(output, "text")
    body += "<h2>Cost and ownership</h2>" + paragraph(cost)
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in mistakes) + "</ul>"
    body += "<h2>Read next</h2>" + paragraph(
        ", ".join("[[" + item + "|" + lookup.get(item, {}).get("title", item.rsplit("/", 1)[-1].replace("-", " ")) + "]]" for item in related) + "."
    )
    entry = copy.deepcopy(lookup["java/casts"])
    entry.update(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
        path=path,
        title=title,
        summary=definition,
        body=body,
        subject="java-advanced",
        category="Programming",
        tags=["java", "concurrency", slug],
        difficulty="Intermediate",
        sort_order=1080 + len(added),
        status="published",
        featured=False,
        published_at=stamp,
        created_at=stamp,
        updated_at=stamp,
    )
    entry["data"] = {
        "subject_root": "java/java",
        "section_path": "java/advanced-java",
        "kind": "tutorial",
        "content_format": "html",
        "reading_minutes": max(4, round(len(re.sub("<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial",
        "related": [],
        "seo_ready": True,
        "java_release": release,
        "java_version": str(release) + "+",
    }
    entry["_related_paths"] = related
    entries.append(entry)
    lookup[path] = entry
    added.append(path)


add(
    "stampedlock-optimistic-read",
    "Java StampedLock optimistic reads: validate before publishing state",
    "A StampedLock optimistic read observes fields without holding a read lock, so the observation must be validated before it becomes a result.",
    [
        ("Treat the stamp as a version check", [
            "Copy only the primitive fields or safe references needed for the decision, then call validate. A writer can change several related fields between reads. If validation fails, retry under a read lock. The fixture forces a write between observation and validation so the failed path is visible without relying on scheduler timing.",
            "This is not a substitute for a transaction across unrelated objects. [[java/locks|Basic lock ownership]] is easier to reason about when reads are not extremely frequent; [[java/readwritelock-downgrade|read-write lock downgrading]] covers a different transition."
        ]),
        ("Keep locked sections small", [
            "StampedLock is not reentrant. Calling an unknown method while holding one of its locks can deadlock if that method tries to acquire the same lock. For mutable object graphs, a validated primitive stamp does not prove every dereference was safe; copy a stable snapshot under a read lock instead."
        ]),
    ],
    '''import java.util.concurrent.locks.StampedLock;

public class WarehouseStockSnapshot {
    public static void main(String[] args) {
        StampedLock guard = new StampedLock();
        int[] stock = {47};
        long optimistic = guard.tryOptimisticRead();
        int tentative = stock[0];
        long writer = guard.writeLock();
        try { stock[0] = 82; }
        finally { guard.unlockWrite(writer); }
        System.out.println("tentative=" + tentative);
        System.out.println("valid=" + guard.validate(optimistic));
        long reader = guard.readLock();
        try { System.out.println("current=" + stock[0]); }
        finally { guard.unlockRead(reader); }
    }
}''',
    "tentative=47\nvalid=false\ncurrent=82",
    "The optimistic attempt avoids read-lock acquisition when no writer intervenes; this fixture deliberately pays for a fallback read lock. Both paths use constant storage. Under frequent writes, failed retries may cost more than ordinary locking, so measure the actual workload.",
    ["Do not return tentative fields before validate succeeds.", "Do not treat an optimistic stamp as a held lock.", "Do not call reentrant code while holding a StampedLock mode."],
    ["java/locks", "java/readwritelock-downgrade", "java/atomics", "java/concurrency-reference"],
)


add(
    "readwritelock-downgrade",
    "Java ReentrantReadWriteLock downgrade: publish then keep a read lock",
    "A thread holding a ReentrantReadWriteLock write lock can acquire its read lock before releasing the write lock, preserving read protection across the transition.",
    [
        ("Avoid an unlocked gap", [
            "A writer may need to update a report and then inspect the committed value while excluding other writers. Acquire the read lock before releasing the write lock. If the write lock is released first, another writer may intervene before the read begins. The fixture prints the new revision while a read hold remains active.",
            "A read-to-write upgrade is different and is not generally available by simply acquiring the write lock while holding a read lock. Release and retry with a version check, or use a design with a single owner. [[java/stampedlock-optimistic-read|Optimistic reads]] offer another policy with explicit validation."
        ]),
        ("Release every hold", [
            "Each acquisition needs its own finally path. Leaking a read hold blocks future writers even after the update is complete. Keep I/O and callbacks outside the critical section when their duration is not bounded."
        ]),
    ],
    '''import java.util.concurrent.locks.ReentrantReadWriteLock;

public class PricingRevisionGate {
    public static void main(String[] args) {
        ReentrantReadWriteLock guard = new ReentrantReadWriteLock();
        int[] revision = {47};
        guard.writeLock().lock();
        try {
            revision[0] = 82;
            guard.readLock().lock();
        } finally {
            guard.writeLock().unlock();
        }
        try {
            System.out.println("revision=" + revision[0]);
            System.out.println("read holds=" + guard.getReadHoldCount());
        } finally {
            guard.readLock().unlock();
        }
        System.out.println("read holds=" + guard.getReadHoldCount());
    }
}''',
    "revision=82\nread holds=1\nread holds=0",
    "The transition adds one lock acquisition without copying the report. Throughput depends on contention and how long readers hold the lock; a long read can delay every writer. The program owns one lock and one revision cell.",
    ["Do not release the write lock before taking the read lock when a gap is forbidden.", "Do not assume a read lock can be upgraded to a write lock.", "Do not forget to release the downgraded read hold."],
    ["java/locks", "java/stampedlock-optimistic-read", "java/conditions", "java/volatile-counter-lost-update"],
)


add(
    "atomicstampedreference-aba",
    "Java AtomicStampedReference: reject a stale A-to-B-to-A update",
    "AtomicStampedReference compares both a reference and a version stamp, so a stale compare-and-set can detect an intervening change that returned to the original reference.",
    [
        ("Make history part of the condition", [
            "A worker reads READY. Another worker changes the state to PACKED and then back to READY. A reference-only comparison would see READY again and miss that history. Increment the stamp on each state transition; the original worker's stale stamp then fails. The fixture performs those transitions sequentially to make the result deterministic.",
            "This is an in-process coordination tool. It does not provide database durability or a distributed version check. [[java/atomics|Atomic primitives]] cover single-reference updates; [[java/concurrent-map|concurrent maps]] cover keyed state with different contracts."
        ]),
        ("Keep versions meaningful", [
            "A stamp can wrap after enough updates. Choose a version width and lifetime policy that fits the system, and do not treat the stamp as a cryptographic token. Compare-and-set still does not make a multi-object transaction atomic."
        ]),
    ],
    '''import java.util.concurrent.atomic.AtomicStampedReference;

public class ParcelStateVersion {
    enum State { READY, PACKED, SHIPPED }

    public static void main(String[] args) {
        AtomicStampedReference<State> parcel = new AtomicStampedReference<>(State.READY, 1);
        int staleStamp = parcel.getStamp();
        parcel.set(State.PACKED, 2);
        parcel.set(State.READY, 3);
        boolean accepted = parcel.compareAndSet(State.READY, State.SHIPPED, staleStamp, 4);
        System.out.println("accepted=" + accepted);
        System.out.println(parcel.getReference() + ":" + parcel.getStamp());
    }
}''',
    "accepted=false\nREADY:3",
    "Each operation uses constant application storage and an atomic reference update. Retries under contention can increase work; the example isolates the version condition and does not claim a latency bound.",
    ["Do not compare only the current reference when intervening transitions matter.", "Do not use set as a conditional update in a contended workflow.", "Do not treat an in-memory stamp as a durable database version."],
    ["java/atomics", "java/concurrent-map", "java/varhandles", "java/volatile-counter-lost-update"],
)


add(
    "cyclicbarrier-broken-state",
    "Java CyclicBarrier timeout: a broken generation needs a recovery rule",
    "A CyclicBarrier generation breaks when a waiting party times out, and later await calls fail until the barrier is reset or replaced.",
    [
        ("Treat timeout as group failure", [
            "A phase cannot be considered complete when one participant abandons the rendezvous. The fixture uses a zero-timeout wait with two required parties, then verifies that the barrier is broken and that a later await reports the broken state. Reset creates a new generation; it does not finish the abandoned work.",
            "[[java/countdown-latch|CountDownLatch]] is one-shot and does not have the same generation model. [[java/phaser-registration|Phaser registration]] is useful when party membership can change, but it also needs a failure policy."
        ]),
        ("Do not hide failed work with reset", [
            "Reset only after every participant has agreed how to discard or retry the old phase. A caller that simply resets and continues can mix outputs from two generations. Bound waits and retain enough phase identity to reject late results."
        ]),
    ],
    '''import java.util.concurrent.BrokenBarrierException;
import java.util.concurrent.CyclicBarrier;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

public class BatchPhaseRecovery {
    public static void main(String[] args) throws InterruptedException {
        CyclicBarrier phase = new CyclicBarrier(2);
        try { phase.await(0, TimeUnit.NANOSECONDS); }
        catch (TimeoutException expired) { System.out.println("phase timed out"); }
        catch (BrokenBarrierException unexpected) { throw new AssertionError(unexpected); }
        System.out.println("broken=" + phase.isBroken());
        try { phase.await(); }
        catch (BrokenBarrierException rejected) { System.out.println("old phase rejected"); }
        phase.reset();
        System.out.println("broken=" + phase.isBroken());
    }
}''',
    "phase timed out\nbroken=true\nold phase rejected\nbroken=false",
    "The demonstration uses constant memory. Real phases incur synchronization and waiting costs for all parties; a timeout does not reclaim unfinished tasks. Recovery must account for those tasks before a new generation begins.",
    ["Do not treat reset as completion of the failed phase.", "Do not let an unbounded await hold a worker forever without a failure policy.", "Do not merge late results from a broken generation into the next one."],
    ["java/countdown-latch", "java/phaser-registration", "java/cancellation", "java/conditions"],
)


add(
    "synchronousqueue-handoff",
    "Java SynchronousQueue: a handoff has no storage capacity",
    "SynchronousQueue transfers an element directly between a producer and a waiting consumer; it does not retain elements in an internal queue.",
    [
        ("Observe the zero-capacity contract", [
            "An immediate offer fails when no consumer is ready. A subsequent put waits until a consumer accepts the value. The fixture starts the consumer only after the failed offer, then joins it before printing the received shipment ID.",
            "This handoff can apply backpressure, but a stalled consumer can hold the producer indefinitely. Use a timed offer or cancellation where the caller has a deadline. [[java/blocking-queues|Buffered blocking queues]] decouple arrival and consumption up to their configured capacity."
        ]),
        ("Separate transfer from processing", [
            "A successful put means the consumer accepted the element; it does not prove that the consumer completed its business work. If acknowledgment matters, pair the transfer with a separate completion signal or durable result record."
        ]),
    ],
    '''import java.util.concurrent.SynchronousQueue;
import java.util.concurrent.atomic.AtomicReference;

public class ShipmentDirectHandoff {
    public static void main(String[] args) throws InterruptedException {
        SynchronousQueue<String> handoff = new SynchronousQueue<>();
        System.out.println("immediate=" + handoff.offer("lot-47"));
        AtomicReference<String> received = new AtomicReference<>();
        Thread receiver = new Thread(() -> {
            try { received.set(handoff.take()); }
            catch (InterruptedException stopped) { Thread.currentThread().interrupt(); }
        });
        receiver.start();
        handoff.put("lot-82");
        receiver.join();
        System.out.println("received=" + received.get());
    }
}''',
    "immediate=false\nreceived=lot-82",
    "The queue itself has no element capacity, although producer and consumer tasks still occupy threads or other runtime resources. Transfer can block; its latency is governed by consumer readiness, not a queue traversal cost.",
    ["Do not assume offer stores work when no consumer exists.", "Do not treat a completed put as proof that processing completed.", "Do not use unbounded waits when the request has a deadline."],
    ["java/blocking-queues", "java/blockingqueue-drain-contract", "java/cancellation", "java/concurrentlinkedqueue-admission"],
)


add(
    "volatile-counter-lost-update",
    "Java volatile counter: visible writes can still lose an update",
    "volatile makes a field's writes visible across threads but does not turn a read-modify-write expression into one atomic operation.",
    [
        ("Force the stale-read interleaving", [
            "Two workers read the same zero before either writes. A barrier holds both until those reads are complete. Each then writes one, so the final counter is one rather than two. This is a deterministic demonstration of the lost-update schedule, not a timing-sensitive stress test.",
            "For a counter, [[java/atomics|AtomicInteger]] offers an atomic increment. [[java/long-adder|LongAdder]] can reduce contention for aggregate statistics, but its sum is not an atomic transaction with other fields."
        ]),
        ("Choose the invariant", [
            "If incrementing the counter must happen with an inventory mutation, use one lock or a transactional boundary for both values. Making both fields volatile does not create a joint invariant. [[java/readwritelock-downgrade|Read-write locks]] help when a shared state needs coordinated reads and writes."
        ]),
    ],
    '''import java.util.concurrent.CyclicBarrier;

public class DispatchCounterRace {
    static class Counter { volatile int accepted; }

    public static void main(String[] args) throws InterruptedException {
        Counter counter = new Counter();
        CyclicBarrier bothRead = new CyclicBarrier(2);
        Runnable accept = () -> {
            int observed = counter.accepted;
            try { bothRead.await(); }
            catch (Exception failure) { throw new AssertionError(failure); }
            counter.accepted = observed + 1;
        };
        Thread first = new Thread(accept);
        Thread second = new Thread(accept);
        first.start();
        second.start();
        first.join();
        second.join();
        System.out.println("accepted=" + counter.accepted);
    }
}''',
    "accepted=1",
    "Each worker uses constant local storage. volatile adds visibility ordering, not a lock or atomic increment; the barrier makes the failed schedule reproducible. A real counter should use an atomic primitive or protect the full invariant under one synchronization rule.",
    ["Do not treat volatile++ as atomic.", "Do not infer correctness from a test that happened to produce the expected count.", "Do not split one invariant across independent volatile fields."],
    ["java/atomics", "java/long-adder", "java/readwritelock-downgrade", "java/concurrenthashmap-compute-contention"],
)


add(
    "concurrenthashmap-compute-contention",
    "Java ConcurrentHashMap.compute: serialize one key's remapping",
    "ConcurrentHashMap.compute applies a remapping for one key atomically, so concurrent callers can update that key without a separate get-then-put race.",
    [
        ("Keep the mapping function bounded", [
            "Two workers call compute for the same shipment key. Each sees the current value supplied by the map, and the final count is two regardless of which worker arrived first. A separate get followed by put could lose one increment.",
            "The map may block other updates to the same key while the remapping function runs. Do not perform remote I/O or recursively update the same map from inside it. [[java/concurrent-map|Concurrent map contracts]] cover key-level ownership; [[java/map-merge-removal|Map.merge]] has its own null-removal behavior."
        ]),
        ("Do not confuse key atomicity with transactions", [
            "A compute call protects one key's remapping. Updating a second map, writing a database row, or publishing an event remains outside that atomic boundary. If those effects must succeed together, use a higher-level transaction or explicit recovery protocol."
        ]),
    ],
    '''import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;

public class ShipmentAttemptTally {
    public static void main(String[] args) throws InterruptedException {
        ConcurrentHashMap<String, Integer> counts = new ConcurrentHashMap<>();
        CountDownLatch begin = new CountDownLatch(1);
        Runnable record = () -> {
            try { begin.await(); }
            catch (InterruptedException stopped) { Thread.currentThread().interrupt(); return; }
            counts.compute("lot-47", (key, previous) -> previous == null ? 1 : previous + 1);
        };
        Thread first = new Thread(record);
        Thread second = new Thread(record);
        first.start();
        second.start();
        begin.countDown();
        first.join();
        second.join();
        System.out.println("attempts=" + counts.get("lot-47"));
    }
}''',
    "attempts=2",
    "The fixture uses one map entry and two threads. A short remapping function performs constant application work per call, while contention on a hot key can serialize callers. The map does not make external effects atomic with its value.",
    ["Do not replace compute with get followed by put for a contended counter.", "Do not block on remote work inside the remapping function.", "Do not assume one-key atomicity covers a database write or a second key."],
    ["java/concurrent-map", "java/map-merge-removal", "java/volatile-counter-lost-update", "java/atomics"],
)


add(
    "lock-interruptibly",
    "Java lockInterruptibly: cancel a worker waiting for ownership",
    "Lock.lockInterruptibly lets a waiting thread stop trying to acquire a lock when it is interrupted.",
    [
        ("Keep cancellation at the wait boundary", [
            "The main thread holds a lock while a worker attempts an interruptible acquisition. It interrupts the worker before releasing ownership, so the worker exits without entering the guarded section. A latch makes the ordering visible; the final output does not depend on which core ran first.",
            "[[java/cancellation|Cancellation policy]] must also cover work after acquisition. A thread that already owns a lock cannot be made safe merely by interrupting it; its critical section needs cleanup and an explicit stop decision."
        ]),
        ("Track ownership precisely", [
            "Only unlock after acquisition succeeded. An InterruptedException from lockInterruptibly means this call did not acquire the lock. Preserve or propagate the cancellation decision at the task boundary instead of quietly retrying forever."
        ]),
    ],
    '''import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.locks.ReentrantLock;

public class InventoryLockCancellation {
    public static void main(String[] args) throws InterruptedException {
        ReentrantLock guard = new ReentrantLock();
        CountDownLatch attempting = new CountDownLatch(1);
        AtomicBoolean cancelled = new AtomicBoolean();
        guard.lock();
        Thread worker = new Thread(() -> {
            attempting.countDown();
            try {
                guard.lockInterruptibly();
                try { throw new AssertionError("unexpected ownership"); }
                finally { guard.unlock(); }
            } catch (InterruptedException stopped) {
                cancelled.set(true);
            }
        });
        try {
            worker.start();
            attempting.await();
            worker.interrupt();
            worker.join();
            System.out.println("cancelled=" + cancelled.get());
        } finally { guard.unlock(); }
    }
}''',
    "cancelled=true",
    "The coordination uses constant storage and one waiting thread. There is no finite wait bound without an interrupt or a timed tryLock; production callers should decide who owns that timeout or cancellation signal.",
    ["Do not unlock a lock that the interrupted worker never acquired.", "Do not swallow interruption and silently retry the same wait.", "Do not assume interruption repairs partially completed work after ownership begins."],
    ["java/locks", "java/cancellation", "java/thread-interrupted-clears-status", "java/conditions"],
)


add(
    "condition-await-loop",
    "Java Condition.await: recheck the predicate after every signal",
    "Condition.await releases the associated lock while waiting and must return to a predicate check before work proceeds.",
    [
        ("A signal is not the state", [
            "The producer first signals without making inventory available. The consumer wakes, sees the predicate is still false, and waits again. Only the second signal follows a real state change. This deliberate false signal tests the same loop needed for spurious wakeups and competing consumers.",
            "The condition is bound to one lock. Every predicate read and update happens under that lock, so the signal and state change have one ownership rule. [[java/conditions|Condition basics]] cover lock acquisition; [[java/blocking-queues|BlockingQueue]] is simpler when the shared state is just a queue."
        ]),
        ("Bound the wait when needed", [
            "An unbounded await can leave a worker parked forever if the producer dies. Use a timed wait with a monotonic deadline and a cancellation path for requests with service-level limits. Never treat one wakeup as proof that the business condition holds."
        ]),
    ],
    '''import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.ReentrantLock;

public class InventoryReadyCondition {
    public static void main(String[] args) throws InterruptedException {
        ReentrantLock guard = new ReentrantLock();
        Condition changed = guard.newCondition();
        CountDownLatch waiting = new CountDownLatch(1);
        CountDownLatch falseSignalSeen = new CountDownLatch(1);
        AtomicInteger wakeups = new AtomicInteger();
        boolean[] ready = {false};
        Thread consumer = new Thread(() -> {
            guard.lock();
            try {
                waiting.countDown();
                while (!ready[0]) {
                    changed.await();
                    if (wakeups.incrementAndGet() == 1) falseSignalSeen.countDown();
                }
            } catch (InterruptedException stopped) { Thread.currentThread().interrupt(); }
            finally { guard.unlock(); }
        });
        consumer.start();
        waiting.await();
        guard.lock();
        try { changed.signal(); }
        finally { guard.unlock(); }
        falseSignalSeen.await();
        guard.lock();
        try { ready[0] = true; changed.signal(); }
        finally { guard.unlock(); }
        consumer.join();
        System.out.println("wakeups=" + wakeups.get());
        System.out.println("ready=" + ready[0]);
    }
}''',
    "wakeups=2\nready=true",
    "The fixture uses one lock, one condition, and constant state. Real waiting time is unbounded unless a deadline is added. The predicate loop is necessary even when a signal is deliberate, because another consumer may change the state first.",
    ["Do not replace while with if around await.", "Do not signal without holding the associated lock when the predicate update needs the same ownership rule.", "Do not treat signal as a durable record of available work."],
    ["java/conditions", "java/locks", "java/blocking-queues", "java/lock-interruptibly"],
)


add(
    "uncaught-exception-handler",
    "Java uncaught exception handler: observe a failed raw thread",
    "A Thread.UncaughtExceptionHandler receives a Throwable that escapes a raw thread's run method.",
    [
        ("Keep failure visible", [
            "A background thread can die while the process remains alive. Attach a handler that records the failure with task identity and enough context to alert the owner. The fixture captures only the exception type so its output is stable; a real handler should log safely and trigger recovery or shutdown policy.",
            "An ExecutorService task submitted with submit stores its failure in the returned Future instead. Its uncaught handler is not the primary observation path. [[java/completion-service-order|CompletionService]] and [[java/completablefuture-handle-observe|future failure handling]] cover that other boundary."
        ]),
        ("Do not call observation recovery", [
            "A handler runs after the task has already failed. It cannot roll back external effects or guarantee that work was retried. Preserve idempotency keys and durable task state when those guarantees matter."
        ]),
    ],
    '''import java.util.concurrent.atomic.AtomicReference;

public class DispatchThreadFailure {
    public static void main(String[] args) throws InterruptedException {
        AtomicReference<String> observed = new AtomicReference<>();
        Thread worker = new Thread(() -> { throw new IllegalStateException("invalid dispatch state"); });
        worker.setUncaughtExceptionHandler((thread, failure) ->
                observed.set(failure.getClass().getSimpleName()));
        worker.start();
        worker.join();
        System.out.println("observed=" + observed.get());
    }
}''',
    "observed=IllegalStateException",
    "The handler adds constant application storage and runs once for this escaped failure. Its work should be short and itself failure-safe. Capturing an exception is not a retry protocol or a guarantee about prior side effects.",
    ["Do not assume a raw worker failure terminates the process.", "Do not expect a submit-created Future failure to reach the raw thread handler.", "Do not describe logging a failure as recovery of failed work."],
    ["java/executors", "java/completion-service-order", "java/completablefuture-handle-observe", "java/cancellation"],
)


for path in added:
    entry = lookup[path]
    entry["data"]["related"] = [
        {"path": target, "title": lookup[target]["title"]}
        for target in entry.pop("_related_paths")
    ]

hub = lookup["java/advanced-java"]
title = "Concurrency failure contracts"
hub["data"]["modules"] = [item for item in hub["data"]["modules"] if item["title"] != title]
hub["data"]["modules"].append({
    "title": title,
    "summary": "Validate optimistic reads, coordinate phase failure, and keep cancellation and task errors observable.",
    "lessons": added,
})
hub["updated_at"] = stamp

reverse = {
    "java/locks": ["java/stampedlock-optimistic-read", "java/readwritelock-downgrade", "java/lock-interruptibly"],
    "java/atomics": ["java/atomicstampedreference-aba", "java/volatile-counter-lost-update"],
    "java/concurrent-map": ["java/concurrenthashmap-compute-contention"],
    "java/conditions": ["java/condition-await-loop", "java/lock-interruptibly"],
    "java/blocking-queues": ["java/synchronousqueue-handoff"],
    "java/countdown-latch": ["java/cyclicbarrier-broken-state"],
    "java/executors": ["java/uncaught-exception-handler"],
}
for path, targets in reverse.items():
    entry = lookup[path]
    marker = "<h2>More concurrency failure contracts</h2>"
    entry["body"] = entry["body"].split(marker)[0] + marker + paragraph(
        "Continue with " + ", ".join("[[" + target + "|" + lookup[target]["title"] + "]]" for target in targets) + "."
    )
    entry["updated_at"] = stamp

FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print("Added", len(added), "Java lessons; linked from", len(reverse), "existing lessons")
