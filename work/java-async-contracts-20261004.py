"""Add standalone Java asynchronous-composition lessons and a draftable quiz."""
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
lookup = {item["path"]: item for item in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()

lessons = [
    dict(slug="completablefuture-thencompose-dependent-stage", title="Java thenCompose: flatten a dependent asynchronous request", group="Dependent stages", release=11,
         definition="CompletableFuture.thenCompose starts a stage that depends on a prior result and flattens its CompletionStage into one resulting future.",
         details="A receipt lookup cannot start until a shipment lookup supplies its identifier. The method accepts both operations as functions so its caller owns transport, timeout, and executor policy. thenApply would return a nested future and make completion ownership harder to reason about. If the first stage fails, the lookup function is not called; if the second fails, the composed stage fails. Neither failure automatically cancels other work.",
         case="The shipment lookup fails before it has an ID. No receipt lookup runs. If the receipt lookup never completes, the composed future also never completes unless the caller applies a deadline or completes it by another policy.",
         code='''import java.util.Objects;
import java.util.concurrent.CompletableFuture;
import java.util.function.Function;

public class ShipmentReceiptChain {
    public static CompletableFuture<String> receipt(
            CompletableFuture<Long> shipmentLookup,
            Function<Long, CompletableFuture<String>> receiptLookup) {
        Objects.requireNonNull(shipmentLookup);
        Objects.requireNonNull(receiptLookup);
        return shipmentLookup.thenCompose(receiptLookup);
    }
}''',
         cost="Registering one dependent stage uses O(1) bookkeeping. End-to-end latency is the first operation followed by the second, so these dependent calls cannot run concurrently. The transport and executor determine the actual work and memory cost.",
         mistakes=["Do not use thenApply when the callback returns another future and a flat result is required.", "Do not assume a failed first stage invokes the second request.", "Do not confuse composition with a deadline or cancellation policy."],
         related=["java/completable-future", "java/completablefuture-timeout-work", "java/completablefuture-thencombine-independent"]),
    dict(slug="completablefuture-thencombine-independent", title="Java thenCombine: join two independent results without serializing them", group="Dependent stages", release=11,
         definition="CompletableFuture.thenCombine combines the normal results of two stages after both finish; it does not impose an order on independent work.",
         details="The two futures are supplied by the caller, which can start them concurrently on a controlled executor. This method only combines their results. A failed input makes the dependent result fail, while the other input can still keep running. A null value is rejected explicitly because a missing rate cannot produce a valid quote. If one input never finishes, the combined stage needs a separate deadline policy.",
         case="The insurance service fails while the base-rate service remains busy. The combined quote cannot succeed, but combining the futures does not cancel the base-rate request or release its resource.",
         code='''import java.util.Objects;
import java.util.concurrent.CompletableFuture;

public class InsuredShipmentQuote {
    public static CompletableFuture<Long> totalCents(
            CompletableFuture<Long> baseRate,
            CompletableFuture<Long> insuranceRate) {
        Objects.requireNonNull(baseRate);
        Objects.requireNonNull(insuranceRate);
        return baseRate.thenCombine(insuranceRate, (base, insurance) -> {
            if (base == null || insurance == null || base < 0 || insurance < 0)
                throw new IllegalArgumentException("Rates must be nonnegative");
            return Math.addExact(base, insurance);
        });
    }
}''',
         cost="The combination adds O(1) local time and space. If operations truly start concurrently, latency is near the slower input rather than their sum, plus callback overhead. Each upstream call still consumes its own resources.",
         mistakes=["Do not start the second independent request inside a thenCompose callback.", "Do not assume thenCombine cancels the surviving input after failure.", "Do not ignore overflow when amounts are stored in integer cents."],
         related=["java/completablefuture-thencompose-dependent-stage", "java/completablefuture-allof-failure", "java/completable-future"]),
    dict(slug="completablefuture-applytoeither-race", title="Java applyToEither: use the first normal result of two stages", group="Race and recovery", release=11,
         definition="CompletableFuture.applyToEither applies a function when either input completes normally. It is a result race, not automatic hedging, timeout, or loser cancellation.",
         details="Two already-started replica lookups can feed this method. It rejects null results in the winning callback, then returns the first normal value that reaches that callback. Exceptional completion rules should be tested for the application's failure combinations; do not assume the other request always rescues an early failure. A service that needs guaranteed first-success behavior across failures should coordinate those results explicitly. Both replica requests can still consume bandwidth after one result is chosen.",
         case="The east replica responds normally while the west request is still blocked. The returned future can complete from east, but west remains active unless its caller cancels or times it out. An early failure must be handled under an explicit fallback policy rather than presumed harmless.",
         code='''import java.util.Objects;
import java.util.concurrent.CompletableFuture;

public class ReplicaReceiptRace {
    public static CompletableFuture<String> firstReceipt(
            CompletableFuture<String> eastReplica,
            CompletableFuture<String> westReplica) {
        Objects.requireNonNull(eastReplica);
        Objects.requireNonNull(westReplica);
        return eastReplica.applyToEither(westReplica, receipt ->
                Objects.requireNonNull(receipt, "Replica returned no receipt"));
    }
}''',
         cost="The continuation adds O(1) bookkeeping. Starting two requests can nearly double upstream resource use, even when one wins quickly; latency follows completion timing and failure handling, not a fixed bound.",
         mistakes=["Do not assume the losing request is cancelled.", "Do not describe this stage as a guaranteed first-success fallback for every failure order.", "Do not launch duplicate writes through a result race without idempotency rules."],
         related=["java/completablefuture-thencombine-independent", "java/completablefuture-cancellation-is-status", "java/completablefuture-timeout-work"]),
    dict(slug="completablefuture-exceptionallycompose-fallback", title="Java exceptionallyCompose: recover with another asynchronous stage", group="Race and recovery", release=17,
         definition="CompletableFuture.exceptionallyCompose replaces an exceptional outcome with a new CompletionStage, allowing recovery that itself finishes asynchronously.",
         details="A primary receipt lookup can fail into a secondary lookup supplied by the caller. The callback may receive a CompletionException wrapper, so classification should inspect causes under a deliberate policy. This sample only retries an unavailable primary; validation failures and cancellation remain failures. The secondary future is created only after failure. Java 17 is the declared baseline for this lesson, and the method is available there. A fallback also needs its own deadline and resource budget.",
         case="A primary read fails with a transient depot-unavailable exception. The backup read begins. If the primary fails because the receipt ID is malformed, the original failure is preserved instead of issuing a pointless backup request.",
         code='''import java.util.Objects;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.function.Supplier;

public class ReceiptReplicaFallback {
    public static class DepotUnavailable extends RuntimeException {
        public DepotUnavailable(String message) { super(message); }
    }

    public static CompletableFuture<String> recover(
            CompletableFuture<String> primary,
            Supplier<CompletableFuture<String>> backup) {
        Objects.requireNonNull(primary);
        Objects.requireNonNull(backup);
        return primary.exceptionallyCompose(failure -> {
            Throwable cause = failure instanceof CompletionException && failure.getCause() != null
                    ? failure.getCause() : failure;
            if (!(cause instanceof DepotUnavailable))
                return CompletableFuture.failedFuture(cause);
            return Objects.requireNonNull(backup.get(), "Backup stage missing");
        });
    }
}''',
         cost="Successful primary requests pay O(1) stage bookkeeping and no backup work. A qualifying failure incurs the secondary request's full latency and resource cost. A fallback that fans out repeatedly can amplify load during an outage.",
         mistakes=["Do not route cancellation or invalid input to a backup automatically.", "Do not forget that a backup stage can fail or never complete.", "Do not implement unbounded recursive recovery during an outage."],
         related=["java/completablefuture-handle-observe", "java/completablefuture-timeout-work", "java/completablefuture-applytoeither-race"]),
    dict(slug="completablefuture-join-versus-get", title="Java CompletableFuture join versus get: preserve failure and interruption contracts", group="Completion boundaries", release=11,
         definition="CompletableFuture.join waits and reports failure through unchecked CompletionException; get waits and reports failure through checked ExecutionException, and its wait is interruptible.",
         details="A blocking boundary must choose which exception and interruption contract it promises. The helper using get restores the thread's interrupt flag and rethrows InterruptedException, leaving higher layers able to stop the request. It unwraps ExecutionException once for diagnostics but preserves that checked exception. The join helper unwraps CompletionException for its caller; direct cancellation may throw CancellationException. Neither method imposes a deadline unless a timed get or another deadline is used.",
         case="A server thread is interrupted during a receipt wait. The get-based path exits and preserves the interrupt signal. Calling join at the same boundary would not give the same checked interruption path.",
         code='''import java.util.Objects;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;

public class ReceiptWaitBoundary {
    public static String interruptible(CompletableFuture<String> receipt)
            throws InterruptedException, ExecutionException {
        Objects.requireNonNull(receipt);
        try { return receipt.get(); }
        catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            throw interrupted;
        }
    }

    public static String unchecked(CompletableFuture<String> receipt) {
        Objects.requireNonNull(receipt);
        return receipt.join();
    }
}''',
         cost="Both methods take O(1) application memory while waiting, but each blocks one caller thread until completion. Waiting time is unbounded without a separate deadline; the distinction is failure and interruption behavior, not computational complexity.",
         mistakes=["Do not swallow InterruptedException or clear its signal without a policy.", "Do not treat join as a nonblocking observation method.", "Do not log only a wrapper type and lose the underlying cause."],
         related=["java/completable-future", "java/cancellation", "java/completablefuture-timeout-work"]),
    dict(slug="completablefuture-cancellation-is-status", title="Java CompletableFuture cancellation: distinguish result status from worker interruption", group="Completion boundaries", release=11,
         definition="CompletableFuture.cancel completes an unfinished future with CancellationException; it does not control the computation that might have produced that future.",
         details="The method cancels a future handed to it and reports whether this call changed its state. The mayInterruptIfRunning argument has no effect for CompletableFuture itself. A producer that owns an HTTP request, thread, or database statement needs a separate cancellation hook. Unfinished dependent stages become exceptional. Calling cancel on an already completed future does not retract its result, and canceling one stage is not a general cascade to every upstream operation.",
         case="A caller times out a receipt request and cancels its result future. A network operation started elsewhere can still complete and consume a connection. Its owner must close or cancel that operation under a separate resource policy.",
         code='''import java.util.Objects;
import java.util.concurrent.CompletableFuture;

public class ReceiptCancellationBoundary {
    public static boolean abandonResult(CompletableFuture<String> receipt) {
        Objects.requireNonNull(receipt);
        return receipt.cancel(true);
    }
}''',
         cost="Cancellation changes O(1) future state, plus completion work for dependent stages. It saves no predictable CPU or I/O by itself because producer interruption and resource cleanup are outside this future's control.",
         mistakes=["Do not assume cancel(true) interrupts the producer of a CompletableFuture.", "Do not equate an abandoned result with released sockets or database resources.", "Do not rely on cancellation to undo side effects."],
         related=["java/cancellation", "java/completablefuture-timeout-work", "java/completablefuture-join-versus-get"]),
    dict(slug="executor-invokeall-bounded-batch", title="Java ExecutorService invokeAll: wait for a bounded batch with a deadline", group="Bulk executor calls", release=11,
         definition="ExecutorService.invokeAll submits a collection of Callables and returns one Future per input after completion or a specified timeout, canceling unfinished tasks on return.",
         details="This method limits the batch to 47 receipt tasks and waits up to three seconds. It keeps result positions aligned with task positions; cancelled tasks are reported as missing, while a task that failed raises ExecutionException to its caller. Timeout cancellation is an interrupt request, not proof that a blocked I/O operation stopped. The executor remains caller-owned and must be shut down by its owner. The deadline is for invokeAll, not for work done before constructing the task list.",
         case="Forty-seven receipt checks are submitted. Three remain unfinished at the deadline and their futures are cancelled. Completed results retain input order even if task finish order differed.",
         code='''import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.concurrent.Callable;
import java.util.concurrent.CancellationException;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

public class ReceiptBatchDeadline {
    public static List<String> collect(ExecutorService executor,
            List<Callable<String>> lookups) throws InterruptedException, ExecutionException {
        Objects.requireNonNull(executor);
        Objects.requireNonNull(lookups);
        if (lookups.size() > 47) throw new IllegalArgumentException("Batch exceeds 47");
        List<Future<String>> results = executor.invokeAll(lookups, 3, TimeUnit.SECONDS);
        List<String> receipts = new ArrayList<>(results.size());
        for (Future<String> result : results) {
            try { receipts.add(result.get()); }
            catch (CancellationException timedOut) { receipts.add(null); }
        }
        return receipts;
    }
}''',
         cost="For N tasks, collecting futures and results costs O(N) application time and memory, with N capped at 47. Pool size and task duration determine execution time. The waiting phase is bounded by the invokeAll timeout, but cancellation cleanup may continue afterward.",
         mistakes=["Do not assume returned futures are in completion order.", "Do not interpret cancel as guaranteed I/O termination.", "Do not submit an unbounded collection or forget who shuts down the executor."],
         related=["java/executors", "java/cancellation", "java/executor-invokeany-first-success"]),
    dict(slug="executor-invokeany-first-success", title="Java ExecutorService invokeAny: return one successful result from competing tasks", group="Bulk executor calls", release=11,
         definition="ExecutorService.invokeAny returns one successfully completed Callable result and cancels unfinished tasks when it returns.",
         details="A bounded set of replica lookups can race under a three-second deadline. Failure of one Callable does not prevent another from succeeding. If all fail, invokeAny raises ExecutionException; if no success arrives before the deadline, it raises TimeoutException. The caller owns the executor and its queue limits. Cancellation of losers requests interruption but does not guarantee their network or database work stopped. Use only for safe duplicate reads or operations with explicit idempotency.",
         case="The east receipt replica throws, and the west replica returns a record. invokeAny returns west's value. If both throw, it raises an error instead of returning null, and unfinished tasks receive cancellation requests.",
         code='''import java.util.List;
import java.util.Objects;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

public class ReceiptReplicaSelection {
    public static String read(ExecutorService executor,
            List<Callable<String>> replicaReads)
            throws InterruptedException, ExecutionException, TimeoutException {
        Objects.requireNonNull(executor);
        Objects.requireNonNull(replicaReads);
        if (replicaReads.isEmpty() || replicaReads.size() > 3)
            throw new IllegalArgumentException("Expected one to three replicas");
        return executor.invokeAny(replicaReads, 3, TimeUnit.SECONDS);
    }
}''',
         cost="Submitting R calls uses O(R) queue and task bookkeeping, with R capped at three. Concurrent reads may reduce latency but multiply backend load. The timeout bounds waiting for a successful result, not guaranteed completion of cancelled loser cleanup.",
         mistakes=["Do not confuse the first finished task with the first successful task.", "Do not use competing non-idempotent writes as replicas.", "Do not assume a timeout means every backend task has stopped."],
         related=["java/executors", "java/executor-invokeall-bounded-batch", "java/completablefuture-applytoeither-race"]),
]

quiz_path = "quizzes/java-async-contracts"
new_paths = ["java/" + item["slug"] for item in lessons] + [quiz_path]
assert not set(new_paths) & lookup.keys()
titles = {item["path"]: item["title"] for item in entries}
titles.update({"java/" + item["slug"]: item["title"] for item in lessons})
titles[quiz_path] = "Java asynchronous contracts quiz"

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
               difficulty="Advanced", sort_order=35400 + index * 10, status="published",
               featured=False, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "java/java", "section_path": "java/advanced-java",
                   "kind": "tutorial", "content_format": "html", "reading_minutes": max(5, round(len(re.sub("<[^>]+>", " ", body).split()) / 150)),
                   "author_path": "authors/aitrove-editorial", "related": related(connections),
                   "seo_ready": True, "java_release": lesson["release"], "java_version": str(lesson["release"]) + "+"}
    new_rows.append(row)

questions = [
    ("Which method flattens a dependent asynchronous lookup?", "thenCompose", "thenApply", "thenAccept", "It returns one stage for a result that needs a prior value."),
    ("Which method combines independently started results?", "thenCombine", "thenCompose", "exceptionally", "Independent calls can start together before their results are combined."),
    ("Does applyToEither cancel the slower request?", "No, the producer needs separate cancellation", "Yes, always", "Only if its result is null", "Selecting a result does not own upstream resources."),
    ("What does exceptionallyCompose allow a failed stage to return?", "Another CompletionStage", "Only a constant value", "Only a checked exception", "The recovery operation can itself finish asynchronously."),
    ("Which wait reports InterruptedException directly?", "get", "join", "isDone", "An interruptible blocking boundary can preserve the signal."),
    ("Does CompletableFuture.cancel(true) interrupt its producer?", "No, not by itself", "Yes, unconditionally", "Only after get", "The future has no direct control over the producing computation."),
    ("What order does invokeAll preserve in its returned futures?", "Input task order", "Completion order", "Random order", "Task completion timing does not rearrange the returned list."),
    ("What does invokeAny seek?", "One successful result", "All successful results", "The first task to fail", "An early failing task need not prevent another task from succeeding."),
]
quiz = copy.deepcopy(lookup["quizzes/java-io"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Test stage composition, failure recovery, cancellation, and bulk executor boundaries.",
            body="<p>Choose the contract supported by each asynchronous operation.</p><h2>Read the lessons</h2>" + links(new_paths[:-1]) + "<h3>Common Mistakes</h3><p>Result completion is separate from task ownership and resource cleanup.</p>",
            sort_order=35550, status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"].update(content_format="html", subject_root="java/java", section_path="java/java-quizzes", duration_minutes=14, seo_ready=True,
                    questions=[{"prompt": prompt, "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                "answer": (-index) % 3, "explanation": explanation}
                               for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)])
new_rows.append(quiz)

for group in dict.fromkeys(item["group"] for item in lessons):
    selected = ["java/" + item["slug"] for item in lessons if item["group"] == group]
    hub = lookup["java/advanced-java"]
    hub["data"]["modules"].append({"title": "Async: " + group, "summary": "Track completion, failure, and resource ownership.", "lessons": selected})
    hub["body"] += "<h2>Async: " + html.escape(group) + "</h2><p>Follow the asynchronous operation's actual contract.</p>" + links(selected)
    hub["updated_at"] = stamp
lookup["java/java-quizzes"]["data"]["modules"].append({"title": "Async contracts", "summary": "Test composition, recovery, and executor behavior.", "lessons": [quiz_path]})
lookup["java/java-quizzes"]["body"] += "<h2>Async contracts</h2><p>Check the new Java asynchronous decisions.</p>" + links([quiz_path])
lookup["java/java-quizzes"]["updated_at"] = stamp
lookup["java/java"]["body"] += "<h2>Further Java asynchronous topics</h2><p>Study dependent stages, competing results, cancellation, and bulk executor calls.</p>" + links(new_paths)
lookup["java/java"]["updated_at"] = stamp

backlinks = {
    "java/completable-future": new_paths[:4],
    "java/completablefuture-allof-failure": ["java/completablefuture-thencombine-independent"],
    "java/completablefuture-handle-observe": ["java/completablefuture-exceptionallycompose-fallback"],
    "java/completablefuture-timeout-work": ["java/completablefuture-cancellation-is-status", "java/completablefuture-thencompose-dependent-stage"],
    "java/executors": ["java/executor-invokeall-bounded-batch", "java/executor-invokeany-first-success"],
    "java/cancellation": ["java/completablefuture-cancellation-is-status", "java/completablefuture-join-versus-get"],
}
for path, targets in backlinks.items():
    row = lookup[path]
    row["body"] += "<p><strong>Continue with:</strong> " + ", ".join(link(target) for target in targets) + ".</p>"
    row["data"]["related"] = related([item["path"] for item in row["data"].get("related", [])] + targets)
    row["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newArticles": len(lessons), "newQuizzes": 1, "newPaths": new_paths}))
