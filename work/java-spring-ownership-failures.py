"""Add Java ownership/failure lessons and a checked Spring rollback rule."""
from __future__ import annotations

import datetime
import html
import json
import pathlib
import re
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILE = ROOT / "src/data/fixtures.json"
rows = json.loads(FILE.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
added = []


def p(value: str) -> str:
    return "<p>" + re.sub(r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>", html.escape(value)) + "</p>"


def code(value: str, language: str = "java") -> str:
    return '<pre><code class="language-' + language + '">' + html.escape(value.strip(), quote=False) + "</code></pre>"


def put(slug, title, definition, sections, source, output, cost, mistakes, related, *, subject="java-advanced", spring=False, proof=""):
    path = ("spring/" if spring else "java/") + slug
    assert path not in by_path, path
    assert all(target in by_path for target in related), (path, related)
    hub = next(row for row in rows if row["type"] == "subject" and row["subject"] == subject)
    body = p(definition)
    for heading, parts in sections:
        body += "<h2>" + html.escape(heading) + "</h2>" + "".join(p(part) for part in parts)
    body += "<h2>" + ("Checked source" if spring else "Working program") + "</h2>" + code(source)
    if spring:
        body += "<h2>Verification boundary</h2>" + p(proof + " runs in the downloadable Spring source kit. The excerpt omits imports and test setup; the kit contains the complete source.")
    else:
        body += "<h3>Output</h3>" + code(output, "text")
    body += "<h2>Costs and boundaries</h2>" + p(cost)
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in mistakes) + "</ul>"
    body += "<h2>Read next</h2>" + p(", ".join("[[" + target + "|" + by_path[target]["title"] + "]]" for target in related) + ".")
    row = by_path["java/casts"].copy()
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), type="article",
        path=path, title=title, summary=definition, body=body,
        category="Backend Frameworks" if spring else "Programming", subject=subject,
        difficulty="Intermediate", tags=["spring", "spring-boot", slug] if spring else ["java", slug],
        status="published", featured=False, sort_order=800 + len(added),
        published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "spring/spring-boot" if spring else "java/java", "section_path": hub["path"],
        "kind": "tutorial", "content_format": "html", "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial", "seo_ready": True,
        "related": [{"path": target, "title": by_path[target]["title"]} for target in related]}
    if spring:
        row["data"].update(framework_version="Spring Boot 4.0.8 / Spring Framework 7",
            java_version="21 source-kit baseline", verification_suite=proof,
            download_path="/downloads/aitrove-spring-source-kit.zip")
    else:
        row["data"].update(java_release=8, java_version="8+")
    rows.append(row)
    by_path[path] = row
    added.append(path)


put("identityhashmap-reference-keys", "Java IdentityHashMap: reference identity is not value equality",
    "IdentityHashMap compares keys by reference identity, so equal values held by distinct objects remain separate keys.", [
    ("The same text can represent two keys", ["Two newly allocated receipt IDs both contain R-41. HashMap treats them as one key by String.equals; IdentityHashMap keeps two entries because the String objects are not the same reference. The displayed sizes make that distinction visible without relying on map iteration order.", "This map is appropriate for an object graph that needs to track exact instances, not for deduplicating business identifiers. [[java/hashmap|HashMap]] and [[java/equals-hashcode|equality contracts]] cover value-key behavior."]),
    ("Identity is an ownership decision", ["Interned strings, reused boxed values or pooled objects can make apparent identity tests change with construction details. Never use IdentityHashMap to compare user IDs, receipt codes or database keys. The key's displayed text is not its identity."])
], '''import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.Map;
public class ReceiptInstanceIndex {
    public static void main(String[] args) {
        String first = new String("R-41");
        String second = new String("R-41");
        Map<String, Integer> byValue = new HashMap<>();
        Map<String, Integer> byInstance = new IdentityHashMap<>();
        byValue.put(first, 1); byValue.put(second, 2);
        byInstance.put(first, 1); byInstance.put(second, 2);
        System.out.println("equal=" + first.equals(second) + ", same=" + (first == second));
        System.out.println("value keys=" + byValue.size() + ", instance keys=" + byInstance.size());
    }
}''', 'equal=true, same=false\nvalue keys=1, instance keys=2',
"Both maps require space for their retained entries. This fixture checks equality semantics, not comparative throughput or memory measurements. Identity keys still keep their referents reachable while the map retains them.",
["Do not index business identifiers by object identity.", "Do not infer identity from equal text or from an object's toString result.", "Do not mistake IdentityHashMap for a weak-reference map."],
["java/hashmap", "java/equals-hashcode", "java/weak-references"], subject="java-collections")

put("treeset-comparator-collision", "Java TreeSet comparator collisions: compare zero means one slot",
    "TreeSet uses comparator equality to decide whether a candidate is already present, even when the objects have different identifiers.", [
    ("A lossy comparator drops work", ["Two review jobs share priority one but have different receipt IDs. A TreeSet ordered only by priority rejects the second job. A comparator with receipt ID as a tie-breaker retains both. The program prints sizes, avoiding any dependence on a representation order for the rejected set.", "This is a data-loss boundary. If two distinct business objects may compare as zero, a sorted set is not a safe queue until the comparator defines their identity. [[java/priorityqueue-tie-order|PriorityQueue tie order]] has a different contract: a priority queue can hold equivalent-ranked jobs, but their removal order is unspecified."]),
    ("Use an ordering that matches the key model", ["A comparator must be transitive. Subtraction is a poor shortcut when integer overflow is possible. If equality and ordering describe different concepts, use a list or a map keyed by explicit ID instead of forcing both into one TreeSet."])
], '''import java.util.Comparator;
import java.util.TreeSet;
public class ReviewJobSet {
    static final class Job {
        final String receiptId; final int priority;
        Job(String receiptId, int priority) { this.receiptId = receiptId; this.priority = priority; }
    }
    public static void main(String[] args) {
        Job east = new Job("R-41", 1);
        Job west = new Job("R-42", 1);
        TreeSet<Job> lossy = new TreeSet<>(Comparator.comparingInt(job -> job.priority));
        lossy.add(east);
        System.out.println("second accepted=" + lossy.add(west));
        TreeSet<Job> complete = new TreeSet<>(Comparator.comparingInt((Job job) -> job.priority)
            .thenComparing(job -> job.receiptId));
        complete.add(east); complete.add(west);
        System.out.println("lossy=" + lossy.size() + ", complete=" + complete.size());
    }
}''', 'second accepted=false\nlossy=1, complete=2',
"TreeSet offers logarithmic add and lookup in its element count when the comparator behaves correctly. The example proves a collision, not a performance advantage over a hash-based set.",
["Do not use a partial comparator as a business identity rule.", "Do not assume object equals controls TreeSet uniqueness.", "Do not subtract priorities if overflow is possible."],
["java/ordered-sets", "java/comparator-contracts", "java/priorityqueue-tie-order"], subject="java-collections")

put("enummap-null-and-order", "Java EnumMap: declaration order and nullable values",
    "EnumMap keys are enum constants iterated in their declaration order, while null values are allowed and null keys are not.", [
    ("Ordering does not follow insertion", ["The fixture inserts REVIEW before RECEIVED. Iteration still reports RECEIVED first because the enum declaration fixes key order. A REVIEW entry with a null value remains present. containsKey distinguishes that state from an absent mapping; get alone cannot.", "The domain still needs a meaning for null. An enum state map can use an explicit marker or Optional-like result instead of an ambiguous null value. [[java/enum-collections|Enum collections]] covers when EnumMap and EnumSet fit."]),
    ("The key type is part of the instance", ["Construct the map with the enum class or from a nonempty compatible source. A null key is rejected. This local map is not synchronized and does not provide cross-thread state transitions."])
], '''import java.util.EnumMap;
import java.util.Map;
public class ReceiptStageNotes {
    enum Stage { RECEIVED, REVIEW, SENT }
    public static void main(String[] args) {
        Map<Stage, String> notes = new EnumMap<>(Stage.class);
        notes.put(Stage.REVIEW, null);
        notes.put(Stage.RECEIVED, "logged");
        for (Stage stage : notes.keySet()) System.out.println(stage);
        System.out.println("review present=" + notes.containsKey(Stage.REVIEW));
        System.out.println("review note=" + notes.get(Stage.REVIEW));
    }
}''', 'RECEIVED\nREVIEW\nreview present=true\nreview note=null',
"EnumMap is specialized for one enum key type; its order is tied to that type's declaration. The example does not establish a persisted state machine or concurrency policy.",
["Do not expect insertion order.", "Do not interpret get == null as proof of absence.", "Do not insert a null enum key."],
["java/enums", "java/enum-collections", "java/map-compute-if-absent-null"], subject="java-collections")

put("thread-interrupted-clears-status", "Java Thread.interrupted clears the current thread's signal",
    "Thread.interrupted reads and clears the current thread's interrupt status; isInterrupted reads it without clearing it.", [
    ("One call consumes the signal", ["The fixture interrupts its own thread, reads the flag without clearing it, then calls Thread.interrupted. A final isInterrupted call is false. There is no timing race or worker thread in this program.", "Code that catches InterruptedException after a blocking call commonly needs to stop or restore the flag with Thread.currentThread().interrupt(). Polling Thread.interrupted in a helper can accidentally consume a cancellation signal intended for a higher layer. [[java/cancellation|Cancellation]] covers task ownership."]),
    ("Interruption is cooperation", ["An interrupt does not forcibly roll back database work or undo partial output. Define an operation boundary at which a worker can stop, and test resource cleanup separately. [[java/executors|Executor ownership]] determines who can request cancellation."])
], '''public class InterruptionReadBoundary {
    public static void main(String[] args) {
        Thread worker = Thread.currentThread();
        worker.interrupt();
        System.out.println("before=" + worker.isInterrupted());
        System.out.println("consumed=" + Thread.interrupted());
        System.out.println("after=" + worker.isInterrupted());
    }
}''', 'before=true\nconsumed=true\nafter=false',
"These status reads are constant-time control operations. The fixture verifies flag semantics only; it does not prove cancellation latency, cleanup, or thread-pool behavior.",
["Do not call Thread.interrupted merely to inspect without clearing.", "Do not swallow InterruptedException and continue as though no cancellation was requested.", "Do not equate interruption with transaction rollback."],
["java/cancellation", "java/threads", "java/executors"])

put("completablefuture-allof-failure", "Java CompletableFuture.allOf: completion barrier, not typed results",
    "CompletableFuture.allOf returns a Void stage that completes after its input stages, and propagates exceptional completion if an input fails.", [
    ("Keep the original stages", ["One receipt lookup succeeds and another fails. Joining allOf raises CompletionException; the healthy stage still holds its value. The returned barrier does not collect both results into a typed list. Keep references to the input stages if results or per-stage diagnostics matter.", "An exceptional barrier is not a cancellation policy. The fixture uses already-completed stages and cannot show whether other running work stops. [[java/completable-future|CompletableFuture basics]] covers completion and executor ownership."]),
    ("Choose a failure policy", ["Batch requests often need either fail-fast reporting or partial results. Make that choice explicitly. Do not catch the barrier exception and report the whole batch as processed without checking each input's outcome."])
], '''import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
public class ReceiptBatchBarrier {
    public static void main(String[] args) {
        CompletableFuture<String> accepted = CompletableFuture.completedFuture("R-41");
        CompletableFuture<String> rejected = new CompletableFuture<>();
        rejected.completeExceptionally(new IllegalStateException("R-42 missing"));
        try { CompletableFuture.allOf(accepted, rejected).join(); }
        catch (CompletionException failure) {
            System.out.println("cause=" + failure.getCause().getClass().getSimpleName());
        }
        System.out.println("accepted=" + accepted.join());
        System.out.println("rejected=" + rejected.isCompletedExceptionally());
    }
}''', 'cause=IllegalStateException\naccepted=R-41\nrejected=true',
"The barrier tracks the provided stage completions; it is not a result collection or a throughput measurement. The fixture makes no threads and does not test cancellation of live tasks.",
["Do not expect allOf.join to return a list of values.", "Do not infer that a failed barrier cancelled successful or still-running stages.", "Do not mask partial failure by swallowing CompletionException."],
["java/completable-future", "java/cancellation", "java/executors"])

put("completablefuture-handle-observe", "Java CompletableFuture handle versus whenComplete: recovery is explicit",
    "CompletableFuture.whenComplete observes an outcome, while handle can produce a replacement value after success or failure.", [
    ("Logging does not repair the stage", ["The failed lookup is observed by whenComplete, which prints the exception type. Joining that observed stage still fails. handle returns a fallback review state, so its dependent stage succeeds. These synchronous callbacks run as the source completes in this fixture; no executor is involved.", "A fallback can conceal a real incident. Keep the original failure in telemetry and define when fallback is acceptable. [[java/completablefuture-allof-failure|allOf]] makes a separate batch-wide decision."]),
    ("Avoid blocking inside callbacks", ["Callbacks can execute on a completion thread. A remote retry or long blocking operation inside handle can delay other work. Use a deliberately owned executor for expensive asynchronous stages and define its shutdown path."])
], '''import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
public class ReceiptRecoveryStage {
    public static void main(String[] args) {
        CompletableFuture<String> lookup = new CompletableFuture<>();
        CompletableFuture<String> observed = lookup.whenComplete((value, failure) ->
            System.out.println("observed=" + failure.getClass().getSimpleName()));
        CompletableFuture<String> recovered = lookup.handle((value, failure) ->
            failure == null ? value : "manual review");
        lookup.completeExceptionally(new IllegalArgumentException("unknown receipt"));
        try { observed.join(); }
        catch (CompletionException failure) {
            System.out.println("still=" + failure.getCause().getClass().getSimpleName());
        }
        System.out.println("fallback=" + recovered.join());
    }
}''', 'observed=IllegalArgumentException\nstill=IllegalArgumentException\nfallback=manual review',
"This fixture checks stage outcomes but does not measure callback scheduling, retry traffic, or remote-service behavior. A fallback is an application policy, not an automatic fix for the upstream failure.",
["Do not expect whenComplete to consume the original failure.", "Do not return a generic success fallback for every exception without a policy.", "Do not block an uncontrolled completion thread with remote work."],
["java/completable-future", "java/completablefuture-allof-failure", "java/executors"])

put("files-walk-close", "Java Files.walk: close the stream that owns directory handles",
    "Files.walk returns a lazy stream over a directory tree and may hold open directory resources until the stream closes.", [
    ("The terminal operation is not cleanup", ["The program creates two temporary receipt files, walks one level, sorts their names and prints them. The stream sits inside try-with-resources; it closes even if traversal throws. A terminal collect alone does not state that directory handles were released.", "The temporary fixture removes its files afterward. A production crawler needs policies for symlinks, permission errors, maximum depth and files that change during traversal. [[java/stream-resource-lifetime|Stream ownership]] and [[java/try-with-resources|close failures]] cover related rules."]),
    ("Do not trust path text as a containment check", ["A walk over user-selected roots needs explicit authorization and symlink handling. Normalizing a path string is not sufficient protection against races or links. [[java/zip-path-validation|Archive path validation]] addresses another untrusted-path boundary."])
], '''import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.Stream;
public class ReceiptDirectoryScan {
    public static void main(String[] args) throws Exception {
        Path root = Files.createTempDirectory("aitrove-receipts-");
        Path first = root.resolve("a.txt");
        Path second = root.resolve("b.txt");
        try {
            Files.write(first, new byte[0]);
            Files.write(second, new byte[0]);
            try (Stream<Path> found = Files.walk(root, 1)) {
                List<String> names = found.filter(path -> Files.isRegularFile(path))
                    .map(path -> path.getFileName().toString()).sorted().collect(Collectors.toList());
                System.out.println(names);
            }
        } finally {
            Files.deleteIfExists(first);
            Files.deleteIfExists(second);
            Files.deleteIfExists(root);
        }
    }
}''', '[a.txt, b.txt]',
"The walk must visit the selected entries and sorting k names takes O(k log k) comparisons plus O(k) name storage. The depth-one fixture is not a benchmark for a large or changing filesystem.",
["Do not leave a Files.walk stream open after collecting its elements.", "Do not assume a live directory tree is a frozen snapshot.", "Do not treat a normalized path as protection from symlink races."],
["java/files", "java/stream-resource-lifetime", "java/try-with-resources", "java/zip-path-validation"])

put("checked-exception-rollback", "Spring transaction rollback: checked failures commit unless a rule says otherwise",
    "Spring's default declarative transaction rule rolls back on unchecked failures, while a checked exception requires an explicit rollback rule if its writes must be undone.", [
    ("Three calls, three outcomes", ["A proxied service inserts into an H2 table and throws. The unchecked failure rolls back, so the row count stays zero. A checked IOException without a rollback rule commits, even though the caller sees an exception. A second checked failure with rollbackFor = IOException.class leaves the count unchanged at one.", "That default surprises import code that throws a checked validation or I/O exception after writing. Keep the transaction boundary around the full unit of work and name the exception classes that should roll back. [[spring/transaction-proxies|Proxy traversal]] matters: a direct self-call can bypass the annotation."]),
    ("A rollback is local to one data source", ["The test uses a local H2 DataSourceTransactionManager. It does not make file publication, broker messages or remote HTTP calls atomic with the database. [[spring/transaction-events|After-commit events]] also need a durable delivery design before they can support reliable external work."])
], '''@Transactional
public void checkedFailure() throws IOException {
    jdbc.update("insert into receipt_import (receipt_id) values (?)", "R-checked");
    throw new IOException("reject import");
}
@Transactional(rollbackFor = IOException.class)
public void checkedFailureWithRule() throws IOException {
    jdbc.update("insert into receipt_import (receipt_id) values (?)", "R-explicit");
    throw new IOException("reject import");
}''', "",
"One H2 transaction manager and one proxied service establish only the stated local rollback behavior. Target-database isolation, deadlocks, migration interactions and external side effects need separate integration tests.",
["Do not assume every exception triggers rollback by default.", "Do not call an annotated method directly through this and expect proxy advice.", "Do not claim that database rollback retracts an email or broker publish."],
["spring/transactions", "spring/transaction-proxies", "spring/transaction-events", "java/exceptions"],
subject="spring-data", spring=True, proof="CheckedRollbackRuleTest.checkedExceptionCommitsByDefaultUnlessRollbackRuleIsExplicit")

labels = {"java-collections": "Identity, ordering and enum-key contracts", "java-advanced": "Cancellation, future failures and file ownership", "spring-data": "Checked-exception rollback"}
for subject in sorted({by_path[path]["subject"] for path in added}):
    hub = next(row for row in rows if row["type"] == "subject" and row["subject"] == subject)
    paths = [path for path in added if by_path[path]["subject"] == subject]
    hub["data"]["modules"].append({"title": labels[subject],
        "summary": "Run the checked fixture, then inspect its ownership and failure boundary.", "lessons": paths})
    hub["updated_at"] = stamp
    if subject == "spring-data":
        links = "<ul>" + "".join('<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>"
            for module in hub["data"]["modules"] for path in module["lessons"]) + "</ul>"
        hub["body"] = re.sub(r"(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)",
            lambda match: match[1] + links + match[2], hub["body"])

reverse = {
    "java/hashmap": ["java/identityhashmap-reference-keys"],
    "java/ordered-sets": ["java/treeset-comparator-collision"],
    "java/enum-collections": ["java/enummap-null-and-order"],
    "java/cancellation": ["java/thread-interrupted-clears-status"],
    "java/completable-future": ["java/completablefuture-allof-failure", "java/completablefuture-handle-observe"],
    "java/files": ["java/files-walk-close"],
    "spring/transactions": ["spring/checked-exception-rollback"],
    "spring/transaction-proxies": ["spring/checked-exception-rollback"],
}
for path, targets in reverse.items():
    row = by_path[path]
    marker = "<h2>Continue with ownership and failure checks</h2>"
    row["body"] = row["body"].split(marker)[0] + marker + p("Continue with " + ", ".join(
        "[[" + target + "|" + by_path[target]["title"] + "]]" for target in targets) + ".")
    row["updated_at"] = stamp

FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"added": added, "count": len(added)}))
