"""Add original Java HTTP boundary and fork/join concurrency lessons."""

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
    dict(slug="http-query-value-encoding", title="Java HTTP query values: encode data without changing URI structure", group="HTTP request and response boundaries", release=11,
         definition="A URI query contains syntax as well as data. Encode each value under the receiving endpoint's query convention before joining it to a trusted base URI; do not encode the complete URI as one value.",
         details="URLEncoder implements form encoding: a space becomes a plus sign, and other non-safe characters become percent-encoded UTF-8 bytes. That is suitable only when the endpoint decodes its query values as form data. This method requires an HTTPS collection URI with no existing query or fragment, appends exactly one named value, and rejects a null input. A different endpoint may require a different encoding contract, especially for path segments. Keep the base URI in trusted configuration and validate any host supplied by callers before sending a request.",
         case="A catalog search receives the text 'seal 47 & blue'. The ampersand must remain inside the value; otherwise a server could interpret the tail as another parameter. The method encodes the value, not the separator. It also refuses a base URI that already contains a query because blindly appending a second question mark would change the request target.",
         code='''import java.net.URI;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.Objects;

public class CatalogQueryUri {
    public static URI search(URI collection, String searchText) {
        Objects.requireNonNull(searchText, "searchText");
        if (!"https".equalsIgnoreCase(collection.getScheme())
                || collection.getHost() == null
                || collection.getRawQuery() != null
                || collection.getRawFragment() != null) {
            throw new IllegalArgumentException("Expected a bare HTTPS collection URI");
        }
        String value = URLEncoder.encode(searchText, StandardCharsets.UTF_8);
        return URI.create(collection.toASCIIString() + "?q=" + value);
    }
}''',
         cost="Encoding B UTF-8 bytes takes O(B) time and O(B) output space. The URI conversion creates another string. These costs are small beside a network call, but the endpoint should still set a length limit on accepted searches.",
         mistakes=["Do not use URLEncoder on a whole URI or on a path segment.", "Do not assume every server interprets plus as a space in a query.", "Do not append a query to a base that already has a query or fragment."],
         related=["java/http-client", "java/http-failure-project"]),
    dict(slug="http-redirect-origin-boundary", title="Java HttpClient redirects: check the next origin before resending", group="HTTP request and response boundaries", release=11,
         definition="An HTTP redirect is a new request target. A client carrying credentials or a request body needs an explicit rule for which redirect destinations are acceptable.",
         details="HttpClient can follow redirects automatically, but a controlled client can configure NEVER and inspect the Location header after a 3xx response. The code resolves a relative target and only accepts the same HTTPS scheme, host, and effective port. It returns a URI; the caller must still decide whether the response status permits replaying the original method and body. In particular, 301 and 302 automatic handling may turn POST into GET. Pin a narrower path or allowlist when the application requires it.",
         case="A shipment API returns a redirect while the caller holds an authorization token. Replaying the request against another host would cross the credential boundary. This gate rejects that move, including a downgrade to plain HTTP. A 307 or 308 response still needs a replayable request body and an idempotency decision before sending again.",
         code='''import java.net.URI;
import java.net.http.HttpClient;
import java.util.Locale;

public class ShipmentRedirectGate {
    public static HttpClient client() {
        return HttpClient.newBuilder().followRedirects(HttpClient.Redirect.NEVER).build();
    }

    public static URI sameOrigin(URI current, URI location) {
        URI next = current.resolve(location);
        String oldHost = current.getHost();
        String newHost = next.getHost();
        int oldPort = current.getPort() == -1 ? 443 : current.getPort();
        int newPort = next.getPort() == -1 ? 443 : next.getPort();
        if (!"https".equalsIgnoreCase(current.getScheme())
                || !"https".equalsIgnoreCase(next.getScheme())
                || oldHost == null || newHost == null
                || !oldHost.toLowerCase(Locale.ROOT).equals(newHost.toLowerCase(Locale.ROOT))
                || oldPort != newPort) {
            throw new IllegalArgumentException("Redirect crosses the configured origin");
        }
        return next;
    }
}''',
         cost="URI resolution and comparison take time proportional to URI length and allocate one URI. Redirect chains add network round trips; cap their count in the caller. A same-origin check does not prove that the destination path is authorized for the same token.",
         mistakes=["Do not carry credentials to an unapproved origin.", "Do not assume an automatic 301 or 302 preserves POST.", "Do not follow an unlimited chain or replay a non-repeatable body."],
         related=["java/http-client", "java/http-failure-project"]),
    dict(slug="http-connect-request-deadlines", title="Java HttpClient deadlines: separate connection and request timeouts", group="HTTP request and response boundaries", release=11,
         definition="HttpClient.connectTimeout bounds connection establishment; HttpRequest.timeout bounds the request's response wait. Neither replaces an overall business deadline that spans retries, parsing, and downstream work.",
         details="Create a reusable client with a connection timeout and a request with its own timeout. The client default for redirects is NEVER, but this example states that policy explicitly so the owner sees it beside the deadlines. A connection reused from a pool may not establish a new connection, so the connection setting is not the only timer that matters. On a timeout, classify the attempt as uncertain if the server may already have processed a mutation. The outer retry policy must subtract elapsed time from one operation budget.",
         case="A warehouse lookup allows 47 seconds end to end. Three attempts each allowed 47 seconds could exceed that budget even before the sleeps between attempts. The factory below sets per-attempt limits; its caller still needs a clock-based overall deadline and must avoid retrying a non-idempotent write without a deduplication rule.",
         code='''import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.time.Duration;

public class WarehouseHttpDeadlines {
    public static HttpClient client() {
        return HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(3))
            .followRedirects(HttpClient.Redirect.NEVER)
            .build();
    }

    public static HttpRequest lookup(URI inventoryUri) {
        if (!"https".equalsIgnoreCase(inventoryUri.getScheme())) {
            throw new IllegalArgumentException("HTTPS inventory URI required");
        }
        return HttpRequest.newBuilder(inventoryUri)
            .timeout(Duration.ofSeconds(7))
            .GET()
            .build();
    }
}''',
         cost="Builder work is O(1) relative to payload size. Reuse one client rather than rebuilding it for every call so connections can be reused. Timeouts bound waiting in specific phases; they do not cap the total cost of multiple attempts or downstream processing.",
         mistakes=["Do not multiply a full business budget across retries.", "Do not assume connectTimeout applies to a reused connection.", "Do not interpret a write timeout as proof the server made no change."],
         related=["java/http-client", "java/http-failure-project", "java/cancellation"]),
    dict(slug="http-streaming-body-size-limit", title="Java streaming HTTP bodies: close the stream and cap retained bytes", group="HTTP request and response boundaries", release=11,
         definition="BodyHandlers.ofInputStream exposes the response body as an InputStream. The application owns that stream and must consume or close it; otherwise an HTTP connection may remain occupied.",
         details="A streaming handler avoids immediately materializing the whole body, but it does not impose a size limit by itself. This decoder reads one byte beyond an application cap and rejects overflow. try-with-resources closes the stream on either path. Closing early may prevent connection reuse, which is an acceptable cost for a rejected oversized payload. This is a cap on bytes delivered to the application after any HTTP representation handling, not a claim about wire bytes or compressed expansion. A structured parser should run only after the cap and content-type checks.",
         case="An inventory response is expected to fit within 47,000 bytes. If the peer sends 47,001 bytes, the parser never receives a truncated record and the request fails. The caller can record response status and content type separately. It must not call the 47,000-byte prefix a complete inventory.",
         code='''import java.io.IOException;
import java.io.InputStream;
import java.net.http.HttpResponse;

public class InventoryBodyReader {
    public static byte[] read(HttpResponse<InputStream> response) throws IOException {
        if (response.statusCode() != 200) {
            try (InputStream discarded = response.body()) {
                throw new IOException("Unexpected inventory status: " + response.statusCode());
            }
        }
        try (InputStream body = response.body()) {
            byte[] bytes = body.readNBytes(47_001);
            if (bytes.length > 47_000) throw new IOException("Inventory body exceeds cap");
            return bytes;
        }
    }
}''',
         cost="Reading a response of N bytes below the cap is O(N) time and O(N) retained memory. The one-byte probe makes overflow detection exact at the application boundary. An early close can sacrifice pool reuse; an unbounded read risks process memory instead.",
         mistakes=["Do not forget to close the response InputStream.", "Do not treat a capped prefix as a complete document.", "Do not rely on Content-Length alone as a verified body-size limit."],
         related=["java/http-client", "java/bounded-line-reader", "java/cancellation"]),
    dict(slug="http-retry-after-budget", title="Java Retry-After: parse a bounded server delay without inventing a retry", group="HTTP request and response boundaries", release=11,
         definition="Retry-After can suggest when to send another request after a 429 or 503 response. A header value is advice, not permission to exceed the caller's deadline or replay a non-idempotent operation.",
         details="Retry-After permits delay seconds or an HTTP date. The deliberately narrow parser below accepts only non-negative decimal seconds of at most 47; longer delays are not shortened into an early retry. It returns empty for unsupported dates and malformed values, leaving the retry policy to decide a safe fallback. A header from an untrusted peer must not create an unbounded sleep. The caller also needs a maximum attempt count and a remaining time budget. If the original request changed state, it needs an idempotency key or reconciliation before retry.",
         case="A catalog service answers 503 with Retry-After 82. This parser declines that delay rather than suggesting a retry after 47 seconds. The caller with only 12 seconds left stops. If a second response has a date-form header, the parser returns no delay instead of guessing from an invalid numeric conversion.",
         code='''import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Optional;

public class CatalogRetryHint {
    public static Optional<Duration> delay(HttpResponse<?> response) {
        int status = response.statusCode();
        if (status != 429 && status != 503) return Optional.empty();
        Optional<String> header = response.headers().firstValue("Retry-After");
        if (header.isEmpty()) return Optional.empty();
        String seconds = header.get().trim();
        if (!seconds.matches("[0-9]{1,12}")) return Optional.empty();
        try {
            long delaySeconds = Long.parseLong(seconds);
            return delaySeconds <= 47 ? Optional.of(Duration.ofSeconds(delaySeconds)) : Optional.empty();
        } catch (NumberFormatException invalid) {
            return Optional.empty();
        }
    }
}''',
         cost="Parsing is O(H) in header length and uses O(H) temporary string storage. The regular-expression length cap prevents huge numeric inputs from being parsed. Sleeping consumes elapsed budget even when it consumes little CPU; the outer operation controls whether that cost is affordable.",
         mistakes=["Do not sleep longer than the remaining operation budget.", "Do not treat unsupported date syntax as zero seconds.", "Do not retry a mutation solely because the server returned 503."],
         related=["java/http-failure-project", "java/http-connect-request-deadlines", "java/optional"]),
    dict(slug="http-cookie-jar-scope", title="Java HttpClient cookies: make session storage an owned policy", group="HTTP request and response boundaries", release=11,
         definition="A CookieHandler attached to HttpClient controls which cookies are accepted and sent. Sharing a client therefore shares session state as well as connection resources.",
         details="A client created without a cookie handler does not provide an application cookie jar. If a workflow genuinely needs cookies, give that workflow its own CookieManager and client, then define its lifetime. The sample accepts cookies only from the original server according to CookiePolicy.ACCEPT_ORIGINAL_SERVER, but that rule is not a substitute for an application allowlist or secure transport. Keep credential-bearing workflows isolated; do not use one mutable cookie jar for unrelated tenants. Session teardown must clear or retire the jar according to the product's logout contract.",
         case="A back-office tool has two warehouse accounts active in the same process. Giving both accounts one client with one cookie manager could mix their login state. The factory creates one jar per account session. The owner stores the resulting client only within that session and discards it on logout, instead of putting it in a global singleton.",
         code='''import java.net.CookieManager;
import java.net.CookiePolicy;
import java.net.http.HttpClient;

public class WarehouseSessionClient {
    public static HttpClient forOneSession() {
        CookieManager sessionCookies = new CookieManager();
        sessionCookies.setCookiePolicy(CookiePolicy.ACCEPT_ORIGINAL_SERVER);
        return HttpClient.newBuilder()
            .cookieHandler(sessionCookies)
            .followRedirects(HttpClient.Redirect.NEVER)
            .build();
    }
}''',
         cost="A cookie jar retains state proportional to accepted cookies; request matching also costs work proportional to the store contents. One client per session uses more connection resources than one global client, so cap session count and retire idle sessions. Isolation is the reason to pay that cost.",
         mistakes=["Do not share one cookie jar across unrelated user sessions.", "Do not assume a client without a handler persists cookies.", "Do not call an origin cookie policy a complete authorization rule."],
         related=["java/http-client", "java/http-redirect-origin-boundary"]),
    dict(slug="forkjoin-recursive-task-threshold", title="Java RecursiveTask: split work only above a measured threshold", group="Fork/join task ownership", release=11,
         definition="RecursiveTask returns a value from a fork/join computation. A threshold keeps small ranges local so task scheduling does not cost more than the work being split.",
         details="This task sums a half-open range of shipment quantities. It splits only when the range exceeds 256 elements, forks one half, computes the other on the current worker, then joins the first. The caller owns the input array for the duration of computation; concurrent writes would break the result contract. Use long for the aggregate because many int quantities can overflow an int sum. The threshold is a workload choice, not a universal constant; measure it with representative array sizes and CPU budgets.",
         case="An intake batch holds 47,000 unit counts. A task per element would create far more scheduling work than arithmetic. Chunking at 256 keeps each leaf useful while permitting multiple workers to take independent ranges. If the batch has only 82 entries, it stays sequential.",
         code='''import java.util.concurrent.RecursiveTask;

public class ShipmentQuantitySum extends RecursiveTask<Long> {
    private final int[] quantities;
    private final int start;
    private final int end;

    public ShipmentQuantitySum(int[] quantities, int start, int end) {
        this.quantities = quantities;
        this.start = start;
        this.end = end;
    }

    @Override protected Long compute() {
        if (end - start <= 256) {
            long total = 0;
            for (int index = start; index < end; index++) total += quantities[index];
            return total;
        }
        int middle = start + (end - start) / 2;
        ShipmentQuantitySum left = new ShipmentQuantitySum(quantities, start, middle);
        left.fork();
        long rightTotal = new ShipmentQuantitySum(quantities, middle, end).compute();
        return rightTotal + left.join();
    }
}''',
         cost="Total arithmetic work is O(N). Balanced splitting gives O(log N) critical-path depth for enough workers and about O(N/256) leaf tasks, though scheduling and memory traffic can dominate cheap sums. Task and stack storage grow with the split tree and active depth.",
         mistakes=["Do not fork a task for every small element.", "Do not mutate the input while tasks are reading it.", "Do not sum a large int array into an int without an overflow policy."],
         related=["java/recursion", "java/stream-parallel-encounter-order", "java/executors"]),
    dict(slug="forkjoin-owned-pool-lifecycle", title="Java ForkJoinPool: own a custom pool and its shutdown", group="Fork/join task ownership", release=11,
         definition="ForkJoinPool executes fork/join tasks with work stealing. A custom pool gives an application an explicit parallelism setting and a shutdown owner; the common pool is shared by unrelated code.",
         details="The method creates a four-worker pool for one CPU-bound calculation, invokes a result-bearing task, then shuts the pool down. Production services normally reuse an owned pool across many batches rather than creating one per call, but its lifecycle remains explicit. Shutdown stops new submissions; awaitTermination waits for existing work and can itself time out. On interruption, preserve the signal and request immediate shutdown. The task shown in the companion lesson stays CPU-bound; blocking I/O needs a different executor or a carefully bounded ManagedBlocker.",
         case="A nightly shipment audit runs an isolated batch and then exits. It can own a pool for that batch. A long-running server should instead keep a service-owned pool and close it at service shutdown, because rebuilding workers on every HTTP request would waste resources. The four-worker setting is a starting capacity to measure, not a throughput promise.",
         code='''import java.util.concurrent.ForkJoinPool;
import java.util.concurrent.TimeUnit;

public class ShipmentBatchRunner {
    public static long sum(int[] quantities) throws InterruptedException {
        ForkJoinPool workers = new ForkJoinPool(4);
        try {
            return workers.invoke(new ShipmentQuantitySum(quantities, 0, quantities.length));
        } finally {
            workers.shutdown();
            try {
                if (!workers.awaitTermination(3, TimeUnit.SECONDS)) workers.shutdownNow();
            } catch (InterruptedException interrupted) {
                workers.shutdownNow();
                Thread.currentThread().interrupt();
                throw interrupted;
            }
        }
    }
}''',
         cost="For an N-element sum, the pool still performs O(N) arithmetic; at most four configured workers can run its tasks concurrently. Starting and tearing down workers adds fixed overhead to each call. Reusing an owned pool amortizes that cost but requires a longer-lived shutdown owner.",
         mistakes=["Do not shut down the common pool as if it belonged to one request.", "Do not create a new pool for each tiny calculation.", "Do not confuse shutdown with confirmation that every task has finished."],
         related=["java/forkjoin-recursive-task-threshold", "java/executors", "java/cancellation"]),
    dict(slug="forkjoin-managed-blocker-queue", title="Java ManagedBlocker: declare a rare blocking wait to the pool", group="Fork/join task ownership", release=11,
         definition="ForkJoinPool.ManagedBlocker describes a wait that might block a fork/join worker. The pool may compensate with another worker while that wait is in progress.",
         details="A fork/join worker that waits on a queue can starve unrelated tasks if all workers do the same. The blocker checks for a ready item without waiting, then takes an item only when necessary. The pool may activate a spare worker; this is not an unlimited capacity guarantee and does not turn arbitrary I/O into CPU work. For sustained network or disk waits, a separate bounded executor is usually easier to account for. The queue producer must also have a termination or cancellation policy so the consumer cannot wait forever.",
         case="A parallel audit occasionally waits for one receipt to arrive in a handoff queue. The wait is rare, so a ManagedBlocker can tell the pool that one worker is parked. If all 47,000 receipts require remote fetches, that workload needs an I/O concurrency limit instead of 47,000 blockers.",
         code='''import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ForkJoinPool;

public class ReceiptQueueBlocker implements ForkJoinPool.ManagedBlocker {
    private final BlockingQueue<String> receipts;
    private String receipt;

    public ReceiptQueueBlocker(BlockingQueue<String> receipts) {
        this.receipts = receipts;
    }

    @Override public boolean isReleasable() {
        return receipt != null || (receipt = receipts.poll()) != null;
    }

    @Override public boolean block() throws InterruptedException {
        if (!isReleasable()) receipt = receipts.take();
        return true;
    }

    public String await() throws InterruptedException {
        ForkJoinPool.managedBlock(this);
        return receipt;
    }
}''',
         cost="A successful poll is O(1) queue work in typical implementations; a miss can wait indefinitely unless an outer cancellation policy interrupts it. Compensation can create extra workers and memory pressure. Bound both queue size and the number of waits.",
         mistakes=["Do not expect managedBlock to create unlimited workers.", "Do not use it to hide sustained blocking I/O inside a CPU pool.", "Do not leave an unbounded take without a producer or cancellation contract."],
         related=["java/forkjoin-owned-pool-lifecycle", "java/executors", "java/cancellation"]),
    dict(slug="forkjoin-failure-and-sibling-work", title="Java fork/join failures: one failed task does not roll back sibling work", group="Fork/join task ownership", release=11,
         definition="A runtime failure from RecursiveTask.compute propagates through join or invoke. A sibling task may already have run, so failure of the result is not an atomic rollback of side effects.",
         details="Keep fork/join computations pure or confine mutations to disjoint owned ranges. The sample validates each shipment quantity before contributing to an aggregate. If one leaf fails, the caller receives a computation failure, but other leaves may have completed. No database or external mutation occurs, so discarding the final sum is safe. If a task writes outside its range, the caller needs separate reconciliation and cancellation; a thrown exception alone will not undo that work. Use an owned pool with a finite batch and record the original cause.",
         case="A batch contains 47,000 counts and one negative quantity. The validation task throws instead of returning a misleading sum. Other subranges may already have been summed. That wasted computation is acceptable; writing partial totals to a ledger from each leaf would not be, because the exception cannot retract those ledger entries.",
         code='''import java.util.concurrent.RecursiveTask;

public class ValidatedShipmentSum extends RecursiveTask<Long> {
    private final int[] quantities;
    private final int start;
    private final int end;

    public ValidatedShipmentSum(int[] quantities, int start, int end) {
        this.quantities = quantities;
        this.start = start;
        this.end = end;
    }

    @Override protected Long compute() {
        if (end - start <= 256) {
            long total = 0;
            for (int index = start; index < end; index++) {
                if (quantities[index] < 0) throw new IllegalArgumentException("Negative quantity at " + index);
                total += quantities[index];
            }
            return total;
        }
        int middle = start + (end - start) / 2;
        ValidatedShipmentSum left = new ValidatedShipmentSum(quantities, start, middle);
        left.fork();
        long rightTotal = new ValidatedShipmentSum(quantities, middle, end).compute();
        return rightTotal + left.join();
    }
}''',
         cost="A valid batch does O(N) validation and summation. An invalid item can reduce useful work, but parallel siblings may still complete, so the failure path has no fixed early-stop cost. The split threshold limits task count to roughly O(N/256) leaves.",
         mistakes=["Do not assume an exception cancels sibling work immediately.", "Do not write irreversible side effects from each leaf and expect rollback.", "Do not swallow a validation exception and publish a partial total."],
         related=["java/forkjoin-recursive-task-threshold", "java/forkjoin-owned-pool-lifecycle", "java/cancellation"]),
    dict(slug="parallel-stream-side-effect-boundary", title="Java parallel streams: reduce values instead of mutating shared results", group="Fork/join task ownership", release=17,
         definition="A parallel stream may run element operations on multiple workers. A reduction combines values through a defined operation; mutation of one shared collection from each worker creates an extra synchronization contract.",
         details="The sample maps immutable shipment rows to long quantities and sums them. Addition is associative for these non-negative bounded inputs so work can be partitioned and combined. The code validates values before reduction and does not append from parallel workers into an ArrayList. Parallelism is not free: cheap inputs, small collections, and memory-bandwidth-heavy work may run faster sequentially. A parallel stream commonly uses a shared fork/join pool, so assess interference with other process work and use an owned execution design when isolation matters.",
         case="A shipment report has 47,000 immutable rows. The audit needs one total, not a list whose order depends on worker timing. A numeric reduction expresses the result directly. If the rows may change during traversal, freeze the batch first; a stream does not create a snapshot of a mutable collection.",
         code='''import java.util.List;

public class ShipmentStreamTotal {
    public record Shipment(String receiptId, int units) {}

    public static long sum(List<Shipment> shipments) {
        return shipments.parallelStream()
            .mapToLong(shipment -> {
                if (shipment.units() < 0) {
                    throw new IllegalArgumentException("Negative units for " + shipment.receiptId());
                }
                return shipment.units();
            })
            .sum();
    }
}''',
         cost="The traversal and arithmetic are O(N) work; enough independent data can reduce elapsed CPU time, but task setup and combining add overhead. The reduction uses little application result memory, while framework tasks use additional resources. Benchmark sequential and parallel forms with real batch sizes.",
         mistakes=["Do not append to a shared ArrayList inside parallel forEach.", "Do not assume parallel is faster for a tiny or cheap pipeline.", "Do not mutate source rows while the stream traverses them."],
         related=["java/streams", "java/stream-parallel-encounter-order", "java/stream-reduce-identity", "java/forkjoin-owned-pool-lifecycle"]),
]

quiz_path = "quizzes/java-http-forkjoin"
quiz_title = "Java HTTP and fork/join decisions quiz"
new_paths = ["java/" + lesson["slug"] for lesson in lessons] + [quiz_path]
assert len(new_paths) == len(set(new_paths)) and not set(new_paths) & lookup.keys()
titles = {row["path"]: row["title"] for row in entries}
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
    cohort = ["java/" + item["slug"] for item in lessons if item["group"] == lesson["group"] and item["slug"] != lesson["slug"]]
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
               difficulty="Advanced", sort_order=34200 + index * 10, status="published",
               featured=False, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "java/java", "section_path": "java/advanced-java",
                   "kind": "tutorial", "content_format": "html", "reading_minutes": max(5, round(len(re.sub("<[^>]+>", " ", body).split()) / 150)),
                   "author_path": "authors/aitrove-editorial", "related": related(connections),
                   "seo_ready": True, "java_release": lesson["release"], "java_version": str(lesson["release"]) + "+"}
    new_rows.append(row)

questions = [
    ("When is URLEncoder appropriate for a query value?", "When the endpoint expects form-style decoding", "For every URI path", "Only after encoding the whole URI", "Form encoding maps spaces to plus signs; the endpoint's decoding contract matters."),
    ("What should a credentialed client check before a manual redirect?", "The next origin and replay policy", "Only the hostname's length", "Only whether the response has HTML", "A redirect is another request target, and the original method may not be safe to replay."),
    ("Does a request timeout replace a whole-operation deadline?", "No, retries and later work need a shared budget", "Yes, for any number of attempts", "Yes, when a connection is reused", "Per-attempt limits cannot bound repeated attempts alone."),
    ("Who closes an ofInputStream response body?", "The application consuming the body", "The URI builder", "A compiler-generated finalizer immediately", "A retained response stream occupies resources until it is consumed or closed."),
    ("How should an oversized body prefix be reported?", "As failure, not as a complete body", "As a successful truncated document", "As an empty response", "The extra byte proves the configured cap was exceeded."),
    ("What is a bounded Retry-After parser's result for unsupported date syntax?", "No parsed numeric delay", "An automatic zero-second retry", "A fixed 47-second server promise", "Date parsing needs its own validated policy; this lesson only accepts delay seconds."),
    ("What state can one HttpClient cookie manager share?", "Cookies across users of that client", "Only local stack variables", "No state because cookies are headers", "A shared jar can mix session state between unrelated accounts."),
    ("Why set a RecursiveTask threshold?", "To avoid scheduling tiny work units", "To guarantee every leaf uses a new OS process", "To make array reads atomic", "Task overhead can outweigh small arithmetic work."),
    ("Who shuts down a custom ForkJoinPool?", "Its application owner", "Each task's join call", "An unrelated user of the common pool", "A custom pool has an explicit lifecycle separate from shared process facilities."),
    ("What does ManagedBlocker guarantee?", "A way to declare a possible blocking wait", "Unlimited spare workers", "Cancellation of all queued tasks", "The pool may compensate, but capacity is still bounded."),
    ("Does one fork/join failure undo sibling side effects?", "No, siblings may already have run", "Yes, like a database rollback", "Only when arrays are large", "Join failure is a result contract, not a transaction."),
    ("What is safer than appending to one ArrayList from parallel workers?", "A value reduction with a defined combination", "Reading mutable rows during traversal", "Ignoring the result order", "Reduction avoids an unowned shared mutation contract."),
]
quiz = copy.deepcopy(lookup["quizzes/java-io"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + quiz_path)), path=quiz_path,
            title=quiz_title, summary="Check Java HTTP request boundaries and fork/join task ownership.",
            body="<p>Choose the decision supported by each API contract. These are local self-check questions.</p><h2>Read the lessons</h2>" + links(new_paths[:-1]) + "<h3>Common Mistakes</h3><p>Do not mistake a timeout, redirect, shared pool, or task exception for a complete business policy.</p>",
            sort_order=34350, status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"].update(content_format="html", subject_root="java/java", section_path="java/java-quizzes",
                    duration_minutes=18, seo_ready=True,
                    questions=[{"prompt": prompt,
                                "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                "answer": (-index) % 3, "explanation": explanation}
                               for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)])
new_rows.append(quiz)

for group in dict.fromkeys(lesson["group"] for lesson in lessons):
    selected = ["java/" + item["slug"] for item in lessons if item["group"] == group]
    hub = lookup["java/advanced-java"]
    hub["data"]["modules"].append({"title": group, "summary": "Follow the API contract through ownership, failure, and cost.", "lessons": selected})
    hub["body"] += "<h2>" + html.escape(group) + "</h2><p>Choose an explicit boundary before scaling the work.</p>" + links(selected)
    hub["updated_at"] = stamp
lookup["java/java-quizzes"]["data"]["modules"].append({"title": "HTTP and fork/join decisions", "summary": "Test request and worker ownership contracts.", "lessons": [quiz_path]})
lookup["java/java-quizzes"]["body"] += "<h2>HTTP and fork/join decisions</h2><p>Test the new request and worker boundaries.</p>" + links([quiz_path])
lookup["java/java-quizzes"]["updated_at"] = stamp
lookup["java/java"]["body"] += "<h2>Further Java network and concurrency boundaries</h2><p>Inspect request targets, response ownership, and parallel work.</p>" + links(new_paths)
lookup["java/java"]["updated_at"] = stamp

backlinks = {
    "java/http-client": ["java/http-query-value-encoding", "java/http-redirect-origin-boundary", "java/http-streaming-body-size-limit", "java/http-cookie-jar-scope"],
    "java/http-failure-project": ["java/http-connect-request-deadlines", "java/http-retry-after-budget"],
    "java/completable-future": ["java/http-connect-request-deadlines", "java/forkjoin-owned-pool-lifecycle"],
    "java/streams": ["java/parallel-stream-side-effect-boundary"],
    "java/stream-parallel-encounter-order": ["java/parallel-stream-side-effect-boundary", "java/forkjoin-recursive-task-threshold"],
    "java/executors": ["java/forkjoin-owned-pool-lifecycle", "java/forkjoin-managed-blocker-queue"],
    "java/cancellation": ["java/forkjoin-failure-and-sibling-work", "java/http-connect-request-deadlines"],
    "java/recursion": ["java/forkjoin-recursive-task-threshold"],
}
for old_path, targets in backlinks.items():
    old = lookup[old_path]
    old["body"] += "<p><strong>Continue with:</strong> " + ", ".join(link(target) for target in targets) + ".</p>"
    old["data"]["related"] = related([item["path"] for item in old["data"].get("related", [])] + targets)
    old["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newArticles": len(lessons), "newQuizzes": 1, "newPaths": new_paths}))
