"""Add original Java contract lessons and connect them to the existing curriculum."""

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
    linked = re.sub(
        r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>",
        escaped,
    )
    return "<p>" + linked + "</p>"


def block(value, language="java"):
    return '<pre><code class="language-' + language + '">' + html.escape(value.strip(), quote=False) + "</code></pre>"


def add(slug, title, definition, sections, source, output, cost, mistakes, related, subject, release=8):
    path = "java/" + slug
    body = paragraph(definition)
    for heading, paragraphs in sections:
        body += "<h2>" + heading + "</h2>" + "".join(paragraph(item) for item in paragraphs)
    body += "<h2>Working program</h2>" + block(source)
    if output is not None:
        body += "<h3>Output</h3>" + block(output, "text")
    body += "<h2>Cost and ownership</h2>" + paragraph(cost)
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in mistakes) + "</ul>"
    body += "<h2>Read next</h2>" + paragraph(
        ", ".join("[[" + item + "|" + lookup.get(item, {}).get("title", item.rsplit("/", 1)[-1].replace("-", " ")) + "]]" for item in related) + "."
    )
    basis = copy.deepcopy(lookup["java/casts"])
    basis.update(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
        path=path,
        title=title,
        summary=definition,
        body=body,
        subject=subject,
        category="Programming",
        tags=["java", slug],
        difficulty="Intermediate",
        sort_order=900 + len(added),
        status="published",
        featured=False,
        published_at=stamp,
        created_at=stamp,
        updated_at=stamp,
    )
    basis["data"] = {
        "subject_root": "java/java",
        "section_path": next(entry["path"] for entry in entries if entry["type"] == "subject" and entry["subject"] == subject),
        "kind": "tutorial",
        "content_format": "html",
        "reading_minutes": max(4, round(len(re.sub("<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial",
        "related": [],
        "seo_ready": True,
        "java_release": release,
        "java_version": str(release) + "+",
    }
    basis["_related_paths"] = related
    if path in lookup:
        entries[entries.index(lookup[path])] = basis
    else:
        entries.append(basis)
    lookup[path] = basis
    added.append(path)


add(
    "linkedlist-addall-alias",
    "Java LinkedList addAll: snapshot an aliased source",
    "LinkedList.addAll(index, source) inserts the source elements at a position; an aliased source makes the input change while the insertion runs.",
    [
        ("Name the source boundary", [
            "A source can be the destination itself or a live subList view backed by it. The List contract does not define the result when the source changes during addAll. A result observed on one JDK build is therefore a poor application rule. Take a snapshot before touching the destination, then insert that fixed sequence.",
            "The program copies two selected dispatch IDs before adding them after the first item. That copy also prevents a later edit to the original list from changing which IDs the operation intended to duplicate. [[java/linkedlist-sublist-view|A subList is a view]], so passing it directly would keep the alias in place."
        ]),
        ("Charge the real cost", [
            "Copying k references needs O(k) extra space. Finding the insertion point in a LinkedList costs O(min(index, n-index)) traversal; linking the k new nodes costs O(k). If the caller already owns a ListIterator at the insertion point, [[java/linkedlist-cursor|cursor-local edits]] can avoid another search, but the input still needs a stable ownership rule.",
            "The snapshot is shallow. If each element is mutable, another thread can still alter an element after the snapshot. The list controls sequence membership, not the state of each referenced object."
        ]),
    ],
    '''import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedList;
import java.util.List;

public class DispatchReplayInsertion {
    public static void main(String[] args) {
        LinkedList<String> pendingDispatches = new LinkedList<>(
            Arrays.asList("load-47", "seal-82", "handoff-15"));
        List<String> replay = new ArrayList<>(pendingDispatches.subList(0, 2));
        pendingDispatches.addAll(1, replay);
        System.out.println(pendingDispatches);
    }
}''',
    "[load-47, load-47, seal-82, seal-82, handoff-15]",
    "A defensive list snapshot costs O(k) references, followed by O(n + k) traversal and insertion in the worst case. The operation is not an atomic update visible to unsynchronized readers; see the separate locking contract before sharing the list across threads.",
    ["Do not pass the destination or its live subList as the addAll source.", "Do not call a shallow snapshot a deep copy of mutable elements.", "Do not assume an indexed LinkedList insertion has array-style O(1) positioning."],
    ["java/linkedlist", "java/linkedlist-sublist-view", "java/linkedlist-cursor", "java/synchronized-list-iteration"],
    "java-collections",
)

add(
    "hashmap-mutable-key",
    "Java HashMap mutable keys: freeze identity before insertion",
    "A HashMap key must keep the equality and hash behavior used at insertion for as long as the mapping remains stored.",
    [
        ("Separate lookup identity from editable state", [
            "An order route may change, but the route ID used to find that order should not. Mutating an object after it becomes a map key can change equals or hashCode; the Map contract leaves the resulting lookup behavior unspecified. Do not build recovery logic around a particular failed or successful get call after such a mutation.",
            "The working program uses an immutable String route ID as its key. It stores mutable status as the value and replaces that value when the route moves. This keeps lookup identity stable while allowing the operational state to change. [[java/equals-hashcode|Equality and hashing]] must follow the same stable key fields."
        ]),
        ("Prefer a copied composite key", [
            "When one field cannot identify a record, construct an immutable key from the required parts and reject null or invalid parts at construction. In Java 17+, a record is concise, but a record containing a mutable array still needs a defensive copy. [[java/record-defensive-copy|Array ownership in records]] shows why final fields alone do not freeze their contents.",
            "A mutable key used in a TreeMap has a related problem: a comparator-visible edit can invalidate the tree's ordering. The failure boundary is the key contract, not the brand of map."
        ]),
    ],
    '''import java.util.HashMap;
import java.util.Map;

public class RouteStatusIndex {
    public static void main(String[] args) {
        Map<String, String> statusByRouteId = new HashMap<>();
        String stableRouteId = "north-47";
        statusByRouteId.put(stableRouteId, "queued");
        statusByRouteId.replace(stableRouteId, "departed");
        System.out.println(statusByRouteId.get(stableRouteId));
        System.out.println(statusByRouteId.containsKey("north-48"));
    }
}''',
    "departed\nfalse",
    "HashMap lookup is expected O(1) with a sound key distribution, but a collision-heavy or hostile key set can increase work. The map retains O(n) entries. Stable keys protect correctness; they do not make updates across several maps transactional.",
    ["Do not edit a key field that participates in equals or hashCode after insertion.", "Do not treat an unmodifiable wrapper around a caller-owned mutable object as an immutable key.", "Do not confuse changing a map value with changing its key."],
    ["java/hashmap", "java/equals-hashcode", "java/record-defensive-copy", "java/treemap"],
    "java-collections",
)

add(
    "bigdecimal-scale-equality",
    "Java BigDecimal equality: value and scale are separate contracts",
    "BigDecimal.equals compares both numeric value and scale, while compareTo compares numeric value without requiring matching scale.",
    [
        ("Choose one identity policy", [
            "A charge of 47.0 and a charge of 47.00 compare as the same amount, but equals says they are different objects by value representation. HashSet follows equals and stores both; TreeSet uses natural ordering and keeps one. If the same business key passes through both structures, two counts can disagree even though neither implementation is broken.",
            "For a fixed two-decimal currency boundary, normalize exact input to scale two before using the amount as a key. setScale(2, UNNECESSARY) rejects an input that would need rounding. For tax or exchange-rate calculations, choose and document a separate rounding rule; quietly rounding at an identity boundary can merge values the business treats as distinct."
        ]),
        ("Keep representation visible", [
            "stripTrailingZeros changes representation and can produce a negative scale for values with trailing powers of ten. It is useful when numeric equivalence is the domain rule, but it is not a blanket money formatter. [[java/bigdecimal|Decimal arithmetic]] covers construction and division; [[java/treeset-comparator-collision|sorted-set collisions]] explains why comparator equality controls membership.",
            "The program starts from strings. Constructing BigDecimal from a binary floating-point double would import that double's approximation before the scale policy has a chance to act."
        ]),
    ],
    '''import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.HashSet;
import java.util.Set;
import java.util.TreeSet;

public class ChargeIdentityPolicy {
    public static void main(String[] args) {
        BigDecimal firstCharge = new BigDecimal("47.0");
        BigDecimal secondCharge = new BigDecimal("47.00");
        Set<BigDecimal> exactRepresentations = new HashSet<>();
        Set<BigDecimal> numericOrder = new TreeSet<>();
        exactRepresentations.add(firstCharge);
        exactRepresentations.add(secondCharge);
        numericOrder.add(firstCharge);
        numericOrder.add(secondCharge);
        Set<BigDecimal> fixedCurrency = new HashSet<>();
        fixedCurrency.add(firstCharge.setScale(2, RoundingMode.UNNECESSARY));
        fixedCurrency.add(secondCharge.setScale(2, RoundingMode.UNNECESSARY));
        System.out.println(exactRepresentations.size() + "/" + numericOrder.size());
        System.out.println(fixedCurrency.size());
    }
}''',
    "2/1\n1",
    "Hash-based membership is expected O(1) per operation; ordered-tree membership is O(log n). Normalization allocates a new decimal representation when needed. The fixed-scale rule belongs at the input boundary so later collections do not guess what equality means.",
    ["Do not assume compareTo returning zero implies equals returns true.", "Do not feed binary double literals into exact decimal identity rules.", "Do not use stripTrailingZeros as an unexplained currency display policy."],
    ["java/bigdecimal", "java/treeset-comparator-collision", "java/hashset", "java/comparator-contracts"],
    "java-advanced",
)

add(
    "string-split-trailing-fields",
    "Java String.split: preserve empty trailing fields in a record",
    "String.split uses a regular expression and discards trailing empty fields when called without an explicit limit.",
    [
        ("A missing field is data", [
            "A line ending in a delimiter may mean that the final field was supplied but left blank. The one-argument split method behaves like split(regex, 0), so that field disappears. For a fixed three-field import, split(regex, -1) keeps the trailing empty value and makes validation possible. The code rejects the incomplete record before it can enter the ledger.",
            "The delimiter is a regex. A literal vertical bar therefore needs escaping as \\| in the regex, represented as \\\\| in a Java string literal. [[java/regular-expressions|Regex matching]] explains this second parsing layer; [[java/strict-utf8|strict UTF-8 decoding]] belongs before any text split of input bytes."
        ]),
        ("Declare the format limit", [
            "This is an internal delimiter format with no quoted fields or escaped delimiters. If a sender can put the delimiter inside a field, split is the wrong parser. Use a format whose escaping rules are specified and a parser that implements those rules. Validate the exact field count, blank policy, and maximum record length before accepting a row.",
            "Splitting creates an array and field strings proportional to input length. For large files, process one bounded line at a time instead of reading the whole file into memory; [[java/files|streaming file reads]] covers the resource boundary."
        ]),
    ],
    '''public class ReceiptFieldBoundary {
    static String readReceiptId(String line) {
        if (line == null || line.length() > 256) throw new IllegalArgumentException("record length");
        String[] fields = line.split("\\\\|", -1);
        if (fields.length != 3 || fields[0].isEmpty() || fields[1].isEmpty() || fields[2].isEmpty())
            throw new IllegalArgumentException("three populated fields required");
        return fields[0];
    }
    public static void main(String[] args) {
        String incomplete = "receipt-47|settled|";
        System.out.println(incomplete.split("\\\\|").length);
        System.out.println(incomplete.split("\\\\|", -1).length);
        try { readReceiptId(incomplete); }
        catch (IllegalArgumentException rejected) { System.out.println("record rejected"); }
        System.out.println(readReceiptId("receipt-82|settled|check-15"));
    }
}''',
    "2\n3\nrecord rejected\nreceipt-82",
    "For a bounded line of n characters, splitting scans O(n) input and allocates O(n) total field content plus the array. The 256-character cap here is a teaching policy, not a universal protocol limit. Choose an application-specific cap before allocating for untrusted input.",
    ["Do not rely on the default split limit when an empty final field has meaning.", "Do not treat a regex delimiter as a literal string.", "Do not call a delimiter split a CSV parser when quoted fields are allowed."],
    ["java/regular-expressions", "java/strict-utf8", "java/files", "java/console-input"],
    "java",
)

add(
    "concurrentlinkedqueue-admission",
    "Java ConcurrentLinkedQueue: size is not an admission limit",
    "ConcurrentLinkedQueue is a nonblocking shared queue whose size calculation traverses elements and cannot reserve capacity for a producer.",
    [
        ("Reserve before publishing", [
            "Checking size() and then calling offer() is two separate actions. Another producer can add between them. size() itself walks the queue and may report a count that changes during the walk. If a service must limit queued work, pair the queue with an explicit permit budget or use a bounded BlockingQueue. The example reserves one of two queued slots before publication and releases it only after poll removes an item.",
            "The permit accounts for queued records, not work already removed by a consumer. That distinction matters if a worker performs long tasks after polling. For a limit on both queued and executing tasks, release the permit when processing finishes instead. [[java/blocking-queues|Bounded blocking queues]] offer a simpler admission boundary when blocking semantics fit."
        ]),
        ("Read weak snapshots honestly", [
            "A ConcurrentLinkedQueue iterator can proceed while other threads modify the queue; it is weakly consistent, not a transactional snapshot. A monitoring dashboard may sample it, but a financial reconciliation cannot use one traversal as a complete inventory without another consistency boundary. Null elements are rejected, allowing poll to use null for emptiness.",
            "The program is deliberately single-threaded so its output is reproducible. The synchronization property comes from the queue and semaphore contracts, not from a timing-dependent stress run."
        ]),
    ],
    '''import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.Semaphore;

public class DispatchAdmissionGate {
    private final ConcurrentLinkedQueue<String> pending = new ConcurrentLinkedQueue<>();
    private final Semaphore queuedSlots = new Semaphore(2);

    boolean submit(String dispatchId) {
        if (!queuedSlots.tryAcquire()) return false;
        try {
            pending.add(dispatchId);
            return true;
        } catch (RuntimeException failure) {
            queuedSlots.release();
            throw failure;
        }
    }

    String take() {
        String dispatchId = pending.poll();
        if (dispatchId != null) queuedSlots.release();
        return dispatchId;
    }

    public static void main(String[] args) {
        DispatchAdmissionGate gate = new DispatchAdmissionGate();
        System.out.println(gate.submit("load-47"));
        System.out.println(gate.submit("load-82"));
        System.out.println(gate.submit("load-15"));
        System.out.println(gate.take());
        System.out.println(gate.submit("load-15"));
    }
}''',
    "true\ntrue\nfalse\nload-47\ntrue",
    "Queue offer and poll have expected constant-time behavior; size is O(n) and unsuitable for hot-path admission. The semaphore retains a fixed permit count. This sample is an in-memory process boundary, not a durable queue: a crash loses pending IDs.",
    ["Do not use size() as a concurrent capacity check.", "Do not release a permit before the item leaves the queue.", "Do not treat a weak iterator as a complete audit snapshot."],
    ["java/blocking-queues", "java/semaphores", "java/concurrent-map", "java/executor-rejection"],
    "java-collections",
)

add(
    "blockingqueue-drain-contract",
    "Java BlockingQueue drainTo: batch size is not a transaction",
    "BlockingQueue.drainTo removes available items into another collection, with an optional maximum item count.",
    [
        ("Bound the transfer", [
            "A worker can pull up to a declared batch size with drainTo(target, maxElements) and process that in memory. It does not wait for enough items to fill the batch; it transfers what is available at the call. A producer may add more immediately after the transfer. For a worker that must wait for at least one item, use take first and then drain the remainder under a separate batch-size rule.",
            "The destination collection has to accept every transferred element. If its add operation fails, the interface does not promise that the two collections collectively retain exactly one copy of each item. Do not use drainTo as a database commit, an exactly-once handoff, or an atomic move to a failing sink."
        ]),
        ("Keep retries outside the queue operation", [
            "The example uses an ordinary ArrayList destination, then acknowledges the batch in application code. A real worker should write an idempotent result and record which IDs finished before discarding a batch after a crash. If a database is involved, [[java/jdbc-transactions|transaction ownership]] and [[java/versioned-migrations|stored schema changes]] are separate concerns.",
            "ArrayBlockingQueue has fixed capacity, so its producer admission behavior is visible. Compare [[java/concurrentlinkedqueue-admission|a nonblocking queue]] when producers must reject immediately rather than wait."
        ]),
    ],
    '''import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;

public class DispatchBatchTransfer {
    public static void main(String[] args) {
        BlockingQueue<String> pending = new ArrayBlockingQueue<>(4);
        pending.add("dispatch-47");
        pending.add("dispatch-82");
        pending.add("dispatch-15");
        List<String> batch = new ArrayList<>(2);
        int transferred = pending.drainTo(batch, 2);
        System.out.println(transferred + ":" + batch);
        System.out.println(pending.poll());
    }
}''',
    "2:[dispatch-47, dispatch-82]\ndispatch-15",
    "The transfer touches up to k items and stores O(k) references in the destination. Fixed queue capacity bounds queued references, but batch processing may allocate more state per item. Drain and downstream persistence are distinct operations with a crash window between them.",
    ["Do not assume drainTo waits until maxElements are present.", "Do not drain into a destination whose add can fail without a recovery rule.", "Do not claim exactly-once processing from an in-memory queue transfer."],
    ["java/blocking-queues", "java/concurrentlinkedqueue-admission", "java/jdbc-transactions", "java/cancellation"],
    "java-advanced",
)

add(
    "completablefuture-timeout-work",
    "Java CompletableFuture timeout: completion is not worker cancellation",
    "CompletableFuture.orTimeout completes that future exceptionally at its deadline, but it does not by itself stop work launched to complete it.",
    [
        ("Separate the caller deadline from the task", [
            "A timed-out caller can stop waiting while the producer still holds a socket, thread, or database connection. The program coordinates with latches so the worker has definitely started before the future times out. After the timeout, it releases the worker and observes that the worker still completes its own work; its later complete call cannot replace the future's timeout result.",
            "The timeout mutates the same CompletableFuture instance and is available from Java 9. A timeout on get(timeout, unit) instead limits only that wait and does not complete the future. Choose the two contracts deliberately. [[java/cancellation|Interruption and cancellation]] requires cooperation from the task and its blocking APIs."
        ]),
        ("Bound resources independently", [
            "An application needs a deadline at the I/O call, a queue admission limit, and a policy for interrupting or abandoning late work. A future timeout is a result-state rule. It is not proof that the underlying operation stopped, nor that a remote side effect did not happen. If a retry follows, give it an idempotency key rather than assuming the first call vanished.",
            "The explicit worker thread keeps this fixture small. In a service, use a named, owned executor with bounded admission and shutdown; [[java/executor-rejection|executor saturation]] covers that layer."
        ]),
    ],
    '''import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicBoolean;

public class LateRateQuote {
    public static void main(String[] args) throws Exception {
        CountDownLatch started = new CountDownLatch(1);
        CountDownLatch release = new CountDownLatch(1);
        AtomicBoolean workFinished = new AtomicBoolean();
        CompletableFuture<String> quote = new CompletableFuture<>();
        Thread worker = new Thread(() -> {
            started.countDown();
            try {
                release.await();
                workFinished.set(true);
                quote.complete("rate-47");
            } catch (InterruptedException stopped) {
                Thread.currentThread().interrupt();
                quote.completeExceptionally(stopped);
            }
        }, "rate-quote-worker");
        worker.start();
        if (!started.await(2, TimeUnit.SECONDS)) throw new IllegalStateException("worker did not start");
        quote.orTimeout(50, TimeUnit.MILLISECONDS);
        try { quote.get(2, TimeUnit.SECONDS); }
        catch (ExecutionException failure) {
            System.out.println(failure.getCause() instanceof TimeoutException);
        } finally {
            release.countDown();
            worker.join(2_000);
        }
        System.out.println(workFinished.get());
        System.out.println(quote.isCompletedExceptionally());
    }
}''',
    "true\ntrue\ntrue",
    "The timeout scheduler holds a deadline until completion, while the worker retains its own resources until it exits. The sample caps every wait, but a real I/O operation must also have its own timeout or cancellation path. One timed-out future can otherwise leave unbounded late work behind under load.",
    ["Do not assume orTimeout interrupts an already running worker.", "Do not retry a timed-out side effect without an idempotency policy.", "Do not confuse get(timeout) with a future that has completed exceptionally."],
    ["java/completable-future", "java/cancellation", "java/executor-rejection", "java/http-failure-project"],
    "java-advanced",
    11,
)

add(
    "atomic-file-publication",
    "Java Files.move: atomic publication is a filesystem contract",
    "Files.move with ATOMIC_MOVE requests one filesystem-level move that exposes a finished file at its destination or reports that atomic movement is unsupported.",
    [
        ("Stage beside the destination", [
            "Write the complete artifact to a temporary file in the destination directory, then close it before the move. Keeping source and destination on the same file store improves the chance that an atomic move is supported. The program publishes a new unique manifest path and refuses to silently copy when ATOMIC_MOVE is unavailable.",
            "The Java API leaves replacement of an existing target under ATOMIC_MOVE implementation-specific. Do not use this fixture as an unconditional overwrite recipe. Allocate a unique destination name or decide how to handle an existing target under the specific provider you deploy. [[java/versioned-migrations|Versioned publication]] is a separate way to avoid ambiguous replacement."
        ]),
        ("Visibility is not durability", [
            "An atomic rename controls what a reader can observe during the name change. It does not promise that bytes or directory metadata survive power loss; a durability requirement needs the relevant file and directory sync procedure for the platform. A non-atomic fallback also has different partial-failure behavior. If the move fails, keep or clean the staged file according to a retry rule rather than pretending the destination was published.",
            "The example reads back the complete UTF-8 manifest only after the move. [[java/files|File ownership]] and [[java/try-with-resources|resource cleanup]] cover the earlier write boundary."
        ]),
    ],
    '''import java.nio.charset.StandardCharsets;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;

public class ManifestPublication {
    public static void main(String[] args) throws Exception {
        Path directory = Files.createTempDirectory("aitrove-manifest-");
        Path staged = Files.createTempFile(directory, "staged-", ".txt");
        Path published = directory.resolve("manifest-47.txt");
        try {
            Files.write(staged, "receipt-47=accepted\\n".getBytes(StandardCharsets.UTF_8));
            try {
                Files.move(staged, published, StandardCopyOption.ATOMIC_MOVE);
            } catch (AtomicMoveNotSupportedException unsupported) {
                System.out.println("atomic move unavailable");
                return;
            }
            String manifest = new String(Files.readAllBytes(published), StandardCharsets.UTF_8);
            System.out.println(manifest.trim());
        } finally {
            Files.deleteIfExists(staged);
            Files.deleteIfExists(published);
            Files.delete(directory);
        }
    }
}''',
    None,
    "Writing and verifying an artifact of n bytes costs O(n) time and O(n) memory in this small fixture because readAllBytes loads it for checking. A streaming verifier can avoid that full read. The move cost and durability depend on the filesystem provider; no portable constant-time or crash-survival promise follows from the Java call alone.",
    ["Do not silently retry without ATOMIC_MOVE and still claim atomic publication.", "Do not assume atomic replacement of an existing target is portable.", "Do not equate atomic visibility with durable storage after a power failure."],
    ["java/files", "java/file-channels", "java/versioned-migrations", "java/try-with-resources"],
    "java-advanced",
)

for path in added:
    entry = lookup[path]
    entry["data"]["related"] = [
        {"path": related, "title": lookup[related]["title"]}
        for related in entry.pop("_related_paths")
    ]

modules = {
    "java/java": ("Delimited record boundaries", ["java/string-split-trailing-fields"]),
    "java/java-collections": (
        "Aliasing, identity and concurrent admission",
        ["java/linkedlist-addall-alias", "java/hashmap-mutable-key", "java/concurrentlinkedqueue-admission"],
    ),
    "java/advanced-java": (
        "Decimal identity, batch transfer and late work",
        ["java/bigdecimal-scale-equality", "java/blockingqueue-drain-contract", "java/completablefuture-timeout-work", "java/atomic-file-publication"],
    ),
}
for hub_path, (title, lessons) in modules.items():
    hub = lookup[hub_path]
    hub["data"]["modules"] = [item for item in hub["data"]["modules"] if item["title"] != title]
    hub["data"]["modules"].append({
        "title": title,
        "summary": "Read the contract, run the fixture, and check the failure boundary.",
        "lessons": lessons,
    })
    hub["updated_at"] = stamp

reverse = {
    "java/linkedlist": ["java/linkedlist-addall-alias"],
    "java/linkedlist-sublist-view": ["java/linkedlist-addall-alias"],
    "java/hashmap": ["java/hashmap-mutable-key"],
    "java/equals-hashcode": ["java/hashmap-mutable-key"],
    "java/bigdecimal": ["java/bigdecimal-scale-equality"],
    "java/treeset-comparator-collision": ["java/bigdecimal-scale-equality"],
    "java/regular-expressions": ["java/string-split-trailing-fields"],
    "java/files": ["java/string-split-trailing-fields", "java/atomic-file-publication"],
    "java/blocking-queues": ["java/concurrentlinkedqueue-admission", "java/blockingqueue-drain-contract"],
    "java/semaphores": ["java/concurrentlinkedqueue-admission"],
    "java/completable-future": ["java/completablefuture-timeout-work"],
    "java/cancellation": ["java/completablefuture-timeout-work"],
    "java/versioned-migrations": ["java/atomic-file-publication"],
}
for path, targets in reverse.items():
    entry = lookup[path]
    marker = "<h2>Related contract checks</h2>"
    entry["body"] = entry["body"].split(marker)[0] + marker + paragraph(
        "Continue with " + ", ".join("[[" + target + "|" + lookup[target]["title"] + "]]" for target in targets) + "."
    )
    entry["updated_at"] = stamp

FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print("Added", len(added), "Java lessons; linked from", len(reverse), "existing lessons")
