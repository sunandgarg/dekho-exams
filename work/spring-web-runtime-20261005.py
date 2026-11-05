"""Add four original Spring web runtime lessons to local preview fixtures."""

import copy
import datetime
import html
import json
import pathlib
import re
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "src/data/fixtures.json"
rows = json.loads(FIXTURE.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def prose(value):
    return re.sub(
        r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>",
        html.escape(value),
    )


lessons = [
    dict(
        slug="mvc-async-executor-capacity",
        title="Spring MVC async executor: bound Callable work before requests pile up",
        summary="Returning Callable frees the servlet request thread, but the work still needs a bounded executor and a timeout budget.",
        blocks=[
            ("Async does not erase work", "A receipt export handler can return Callable while Spring releases the initial servlet thread. The callable then runs on an AsyncTaskExecutor, and the response remains open until a second dispatch completes it. If submissions outrun workers, an unbounded queue turns latency into memory pressure. Configure the executor used by Spring MVC rather than assuming the default has production capacity. [[spring/async-boundaries|Async boundaries]] explain why a thread switch also changes context and transaction behavior."),
            ("Budget the whole request", "Set an MVC async timeout shorter than the upstream proxy deadline, and give every database or outbound call its own tighter deadline. A response timeout does not automatically stop a blocking connector; it can continue holding a worker after the client has gone. Use a bounded queue and define rejection behavior that produces a clear overload response. [[spring/bounded-executor-rejection|Executor rejection]] should be tested at capacity, not only when the system is idle."),
            ("Test saturation", "Hold all worker threads with controlled tasks, fill the queue, and submit another receipt request. Verify the request fails within its deadline rather than waiting indefinitely. Release the tasks and confirm the executor recovers. Run the same case through the load balancer to check that its timeout is later than the application timeout. A successful unit test of the callable body says nothing about servlet redispatch or queueing."),
        ],
        code="@Configuration\nclass ReceiptMvcAsyncConfig implements WebMvcConfigurer {\n    private final AsyncTaskExecutor receiptExecutor;\n\n    ReceiptMvcAsyncConfig(\n            @Qualifier(\"receiptExecutor\") AsyncTaskExecutor receiptExecutor) {\n        this.receiptExecutor = receiptExecutor;\n    }\n\n    @Override\n    public void configureAsyncSupport(AsyncSupportConfigurer support) {\n        support.setTaskExecutor(receiptExecutor);\n        support.setDefaultTimeout(4700L);\n    }\n}",
        cost="Each active callable occupies a worker and its open response holds connection state. Queue capacity bounds memory but creates explicit rejections; sizing should follow measured work duration and peak concurrent requests.",
        mistakes=["Do not confuse releasing the servlet thread with finishing the request.", "Do not leave blocking callable work on an unbounded default executor.", "Do not assume a servlet timeout cancels a database or remote call."],
        related=["spring/async-boundaries", "spring/bounded-executor-rejection", "spring/mvc-request-pipeline", "spring/restclient-timeout-budget", "spring/boot-graceful-shutdown"],
        backlink="spring/async-boundaries",
    ),
    dict(
        slug="mvc-streaming-response-disconnect",
        title="Spring MVC streaming response: stop work when the client disconnects",
        summary="A streaming response shifts output to an executor; close its cursor and end production when a write fails.",
        blocks=[
            ("Stream from a bounded source", "A receipt CSV export may contain enough rows that building one byte array would consume excessive heap. StreamingResponseBody writes chunks directly to the response, but it does not give the export unlimited time or free threads. Use the configured MVC async executor and a database cursor or paged reader with an explicit resource lifetime. [[spring/mvc-async-executor-capacity|Executor capacity]] sets the concurrency ceiling; [[spring/upload-byte-budget|upload limits]] protect the opposite direction."),
            ("Treat write failure as cancellation", "A browser that closes its download may cause a write or flush to throw IOException. Stop reading further rows and let try-with-resources close the cursor. Do not catch the exception and keep generating receipts; doing so burns database work for a socket that no longer exists. If the export is a durable business job rather than an interactive download, persist its progress and let the client fetch a completed artifact instead of holding one HTTP connection open."),
            ("Prove cleanup under a broken connection", "Start an export of 47 rows, close the client after the first chunk, and assert the cursor closes promptly while later rows are not fetched. Repeat with a slow reader and a server shutdown. Once headers or bytes have been written, an error handler often cannot replace the response with a clean JSON problem body; record the failure server-side without leaking receipt contents. [[spring/boot-graceful-shutdown|Shutdown draining]] needs an explicit deadline for these long responses."),
        ],
        code="@GetMapping(value = \"/receipts/export\", produces = \"text/csv\")\nStreamingResponseBody exportReceipts() {\n    return output -> {\n        try (ReceiptCursor cursor = receipts.openExportCursor()) {\n            while (cursor.hasNext()) {\n                output.write(cursor.nextCsvRow());\n            }\n            output.flush();\n        }\n    };\n}",
        cost="Streaming reduces peak heap from the full export size to a row and output buffer, but every active download still holds a worker, cursor and connection until completion or failure.",
        mistakes=["Do not retain an open database cursor after a client disconnect.", "Do not catch IOException and continue generating the rest of the export.", "Do not promise a structured error body after response bytes have already been sent."],
        related=["spring/mvc-async-executor-capacity", "spring/boot-graceful-shutdown", "spring/upload-byte-budget", "spring/pagination-bounds", "spring/async-boundaries"],
        backlink="spring/boot-graceful-shutdown",
    ),
    dict(
        slug="webflux-codec-memory-budget",
        title="Spring WebFlux codec memory budget: distinguish aggregation from streaming",
        summary="Set an in-memory decode ceiling for WebClient payloads and stream large responses instead of merely lifting the limit.",
        blocks=[
            ("Aggregation has a ceiling", "A WebClient call that decodes one JSON receipt document may buffer bytes before producing an object. The codec maxInMemorySize setting places a cap on that aggregation. When a partner sends a much larger body, raising the cap to match its biggest possible response multiplies memory exposure by concurrent requests. Decide whether that body is legitimate; if so, change the processing shape to a stream or file transfer rather than silently accepting an unbounded object. [[spring/webclient-response-ownership|Response ownership]] still matters when handling status branches."),
            ("Size the limit from a contract", "Measure a normal receipt response, allow bounded headroom and configure the client that calls that partner. The example caps in-memory decoding at 384 KiB for one client. A separate client for genuinely large exports may use a different strategy. This setting does not cap every byte travelling through the network and does not replace a proxy request-size limit. A stream can still accumulate unbounded data if downstream code calls collectList or joins all buffers."),
            ("Probe failure and recovery", "Return a payload just below the limit, one above it, and a chunked response that never ends. Verify a predictable failure for the oversized aggregate, a response deadline for the endless stream, and no retained connection after cancellation. Repeated oversize failures should not exhaust the connection pool. [[spring/reactive-demand|Reactive demand]] governs downstream consumption, while [[spring/webflux-cancellation|cancellation]] governs stopped work."),
        ],
        code="@Bean\nWebClient receiptPartnerClient(WebClient.Builder managedBuilder) {\n    return managedBuilder\n        .codecs(codecs -> codecs.defaultCodecs()\n            .maxInMemorySize(384 * 1024))\n        .build();\n}",
        cost="The limit bounds memory per aggregated response, not the number of concurrent responses. At 384 KiB each, 47 simultaneous decodes can still reserve substantial heap before object allocation and application processing.",
        mistakes=["Do not solve every DataBufferLimitException by setting a very large global cap.", "Do not collect an entire stream into a list and call it streaming.", "Do not treat codec memory limits as request or response deadlines."],
        related=["spring/webclient-response-ownership", "spring/reactive-demand", "spring/webflux-cancellation", "spring/restclient-read-deadline", "spring/boot-trace-client-builder"],
        backlink="spring/webclient-response-ownership",
    ),
    dict(
        slug="webclient-status-specific-decoding",
        title="Spring WebClient status-specific decoding: consume one branch and close the rest",
        summary="Use exchangeToMono when success, absence and failure have different body contracts, and keep decoding inside the exchange callback.",
        blocks=[
            ("The status chooses the body type", "A partner returns a receipt quote on success, an empty body for not-found and a problem document for other failures. retrieve is concise for a uniform success body, but exchangeToMono lets the client choose decoding based on status. The response body must be consumed or released within that exchange lifecycle; returning ClientResponse for later decoding breaks ownership. [[spring/webclient-response-ownership|Response ownership]] covers the connection consequences of this boundary."),
            ("Preserve distinct business outcomes", "A 404 for an optional quote can become Mono.empty, while a 401 or 503 must stay a failure. Do not turn every non-2xx into empty; that masks revoked credentials and partner outages as missing business data. The example delegates other failures to createError so the error body is handled by the client API. Add a separate bounded decoder when the partner's problem response needs structured fields, and keep [[spring/webflux-codec-memory-budget|codec memory limits]] in force for that error body too."),
            ("Test the release path", "Feed a success body, an empty 404 and a failing response with a body through a test server. Reuse the connection after each path, and cancel a request while it is decoding to expose leaks. A downstream retry should be limited to operations that are safe to replay; decoding an error does not make a POST idempotent. [[spring/restclient-uncertain-commit|Uncertain commit]] explains why a transport failure after a write needs a separate business key."),
        ],
        code="Mono<ReceiptQuote> quote(String receiptId) {\n    return partnerClient.get()\n        .uri(\"/quotes/{receiptId}\", receiptId)\n        .exchangeToMono(response -> {\n            if (response.statusCode().is2xxSuccessful()) {\n                return response.bodyToMono(ReceiptQuote.class);\n            }\n            if (response.statusCode().value() == 404) {\n                return Mono.empty();\n            }\n            return response.createError();\n        });\n}",
        cost="Status inspection is constant work. Body decoding and error buffering dominate memory and latency; a missing-result branch saves object allocation, but retries or repeated misses can still produce high request volume.",
        mistakes=["Do not return ClientResponse for decoding after exchangeToMono completes.", "Do not map authentication and service failures to the same empty result as a true 404.", "Do not retry a write merely because its response body could not be decoded."],
        related=["spring/webclient-response-ownership", "spring/webflux-codec-memory-budget", "spring/restclient-uncertain-commit", "spring/restclient-status-no-retry", "spring/boot-trace-client-builder"],
        backlink="spring/restclient-status-no-retry",
    ),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"spring/" + item["slug"]: item["title"] for item in lessons})
for number, item in enumerate(lessons):
    path = "spring/" + item["slug"]
    assert path not in by_path, path
    for target in item["related"]:
        assert target in titles, (path, target)
    body = "<p>" + prose(item["summary"]) + "</p>"
    for heading, content in item["blocks"]:
        body += "<h2>" + html.escape(heading) + "</h2><p>" + prose(content) + "</p>"
    body += ('<h2>Implementation contract</h2><pre><code class="language-java">'
             + html.escape(item["code"], quote=False) + "</code></pre>")
    body += "<h2>Cost and verification</h2><p>" + prose(item["cost"]) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join(
        "<li>" + prose(mistake) + "</li>" for mistake in item["mistakes"]
    ) + "</ul>"
    body += "<h2>Read next</h2><p>" + ", ".join(
        '<a href="/' + target + '">' + html.escape(titles[target]) + "</a>"
        for target in item["related"]
    ) + ".</p>"
    row = copy.deepcopy(by_path["spring/component-scan-vs-bean"])
    row.update(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
        path=path, title=item["title"], summary=item["summary"], body=body,
        subject="spring-web", tags=["spring", "spring-boot", "web-apis", item["slug"]],
        sort_order=5900 + number, published_at=stamp, created_at=stamp, updated_at=stamp,
    )
    row["data"] = {
        "subject_root": "spring/spring-boot", "section_path": "spring/web-apis",
        "kind": "tutorial", "content_format": "html", "seo_ready": True,
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial",
        "framework_version": "Spring Boot 4 / Spring Framework 7 where relevant",
        "java_version": "21 or later",
        "verification_suite": "Spring API contract review; snippets require an application-specific model",
        "related": [{"path": target, "title": titles[target]} for target in item["related"]],
    }
    rows.append(row)
    by_path[path] = row

paths = ["spring/" + item["slug"] for item in lessons]
by_path["spring/web-apis"]["data"]["modules"].append({
    "title": "Web request and client resource budgets",
    "summary": "MVC async capacity, streaming disconnects and WebClient decoding limits.",
    "lessons": paths,
})
for section in ("spring/web-apis", "spring/spring-boot"):
    entry = by_path[section]
    entry["body"] += "<h2>Web runtime contracts</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
        for path in paths
    ) + "</ul>"
    entry["updated_at"] = stamp

for item in lessons:
    source, target = item["backlink"], "spring/" + item["slug"]
    entry = by_path[source]
    entry["body"] += ('<h2>Related web contract</h2><p><a href="/' + target + '">'
                      + html.escape(titles[target]) + "</a>.</p>")
    entry["updated_at"] = stamp

FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(f"Added {len(lessons)} Spring web lessons; {len(rows)} total fixture records")
