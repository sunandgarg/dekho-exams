"""Add original native Node and PHP runtime tracks to local Web drafts."""

import copy
import datetime
import html
import json
import re
import subprocess
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "src/data/fixtures.json"
entries = json.loads(FIXTURE.read_text())
by_path = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def p(value):
    return "<p>" + html.escape(value) + "</p>"


def a(path):
    assert path in by_path, path
    return '<a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a>"


def code_block(source, language):
    return '<pre><code class="language-' + language + '">' + html.escape(source, quote=False) + "</code></pre>"


tracks = [
    dict(
        hub="node-native-http-and-runtime-boundaries",
        title="Native Node HTTP and Runtime Boundaries",
        summary="Bound request bytes, response flow, CPU work, and outbound calls beneath server frameworks.",
        intro="A Node server is a set of streams and callbacks before it is an Express application. These lessons follow a municipal permit service through admission, export, analysis, and upstream calls. Each boundary has a measurable budget, a failure state, and a test that stays useful if the framework changes.",
        prereq=["web-tech/http-request-response-contract", "web-tech/express-request-and-process-boundaries", "web-tech/streaming-and-large-data-interfaces"],
        project="node-native-permit-gateway-project",
        project_title="Project: Native Node Permit Gateway",
        quiz="web-development-node-runtime-contracts",
        quiz_title="Web Development: Native Node Runtime Contracts",
        topics=[
            dict(
                slug="node-incoming-body-limits-and-abort-state", title="Node Incoming Body Limits and Abort State",
                summary="Enforce wire-byte and parse budgets before an HTTP request becomes a domain command.",
                concept="The IncomingMessage is a readable stream, not a validated JSON object. A Content-Length header is a hint supplied by the caller and may be missing or false. Count actual bytes while reading, reject bodies above the route budget, and distinguish a complete stream from a connection closed mid-body. Parse only after the admitted bytes are complete. A domain command then validates field types, ranges, and identity separately. The distinction matters: a byte limit protects memory, while schema checks protect business state. Framework body parsers hide these steps but cannot eliminate their cost.",
                case="Permit intake accepts 37 KiB of JSON because it carries inspection notes, but a client sends 47 MiB in small chunks without Content-Length. A handler that collects all chunks first can exhaust memory across concurrent requests. Another client closes the socket halfway through an approval command. Logging the unfinished bytes as a complete rejected command creates misleading audit history. The handler must stop reading at the byte budget, avoid writing a response after the socket disappears, and never call the approval service for an incomplete request. A well-formed 38 KiB body receives a deliberate size response.",
                implementation="Configure parser and proxy limits together, then enforce a route-local limit on actual chunks. A counted read should reject before concatenation when the next chunk exceeds the budget; it should also bound read time, because a tiny body can arrive indefinitely. Keep the raw buffer local to the request and discard it on error. Validate the content type, decode text once, parse JSON once, and convert it to an allowlisted command. A truncated request is a transport failure; malformed JSON is a client input failure. Return a bounded error object without echoing the supplied payload. Treat any later write as conditional on the response still being writable.",
                cost="For a body of B admitted bytes, the read and decode cost is O(B), and accumulating chunks consumes O(B) memory per concurrent request. JSON parsing can add another object graph of roughly input-proportional size, so multiply the budget by expected concurrency rather than comparing it only with host RAM. Early rejection limits worst-case bytes retained but cannot undo bytes already received by the proxy. Streaming formats can lower retained memory, yet they complicate validation and commit ordering. Record accepted sizes, oversize counts, slow-body deadlines, aborted reads, and parse failures separately; one combined bad-request metric hides attacks and ordinary client errors.",
                failure="Send an admitted JSON command in one chunk and in uneven chunks; they must produce the same typed command. Send a body exactly at the byte cap and one byte beyond it. Omit Content-Length, lie about its value, split a multibyte character across chunks, and close before the final brace. Keep a connection open while sending one byte at a time to exercise the read deadline. Repeat these cases with twenty simultaneous clients while measuring retained heap. In every rejected or aborted case, the permit table and audit log must remain unchanged. Confirm the server does not attempt a second response after a socket error.",
                drill="Implement a permit-admission endpoint with a strict body budget of 37 KiB, a short read deadline, and a typed command containing permitId, inspectionRevision, and notes. Capture a stable request ID before parsing, but do not include raw notes in logs. Feed it malformed JSON, an oversized chunked body, a partial socket close, and a valid command. Assert the downstream approval function is called once only for the valid body. Run the same cases behind a reverse proxy with a different global limit and document which layer rejects first. Add a test for ambiguous content types and for an empty body.",
                decision="Transport admission and domain validation are separate gates; neither may commit a partial command.",
                code='''async function readBoundedJson(request, maximumBytes = 37 * 1024) {
  const chunks = [];
  let receivedBytes = 0;
  for await (const chunk of request) {
    receivedBytes += chunk.length;
    if (receivedBytes > maximumBytes) throw new Error("body_too_large");
    chunks.push(chunk);
  }
  if (!request.complete) throw new Error("body_incomplete");
  return JSON.parse(Buffer.concat(chunks, receivedBytes).toString("utf8"));
}''',
                mistakes=["Trusting Content-Length instead of counting delivered bytes.", "Parsing an incomplete body as a complete command.", "Logging raw rejected JSON containing private notes."],
                checks=["A partial or oversized body never reaches the approval service.", "Exactly-at-limit and limit-plus-one inputs have different outcomes.", "Concurrent rejected requests remain within the heap budget."],
                related=["web-tech/express-middleware-order-and-request-identity", "web-tech/upload-intake-budgets-and-storage-ownership", "web-tech/abuse-resistant-public-endpoints"],
            ),
            dict(
                slug="node-response-backpressure-and-export-aborts", title="Node Response Backpressure and Export Aborts",
                summary="Couple export production to a slow response consumer and stop work when the client disconnects.",
                concept="ServerResponse is a writable stream. Its write method returning false means the producer should pause until drain, not that the bytes failed. Ignoring that signal lets a fast export query queue an unbounded amount of data behind a slow network client. A response close before finish means delivery stopped; it does not mean the export transaction should keep scanning the database. Separate a durable export job from a live streaming response. A live response can cancel work on disconnect, while a durable job needs a stable artifact and status resource that outlives any one browser connection.",
                case="A permit officer downloads 240,000 inspection rows over a weak mobile connection. The database cursor emits rows much faster than the socket sends them, and a naive loop calls response.write for each row. Resident memory climbs while only a small fraction of the file has left the server. The officer closes the tab at row 81,000, but the query keeps reading to the end. A bounded implementation fetches a batch, writes it, waits when backpressure appears, and closes the cursor when the client connection closes. If the export must survive navigation, it becomes a queued artifact request instead of an in-flight HTTP stream.",
                implementation="Create the cursor only after authorization and filters are fixed. Emit headers before body bytes, but remember that after the first byte an error cannot be converted into a clean JSON response. Preserve CSV escaping and newline rules as part of the data contract. Prefer pipeline for compatible readable and writable streams because it coordinates backpressure and failure propagation. When manually generating rows, pause on false and resume on drain; attach close, error, and abort cleanup paths. Distinguish a normal finish from a premature close in metrics. If a database page is fetched before the socket drains, cap the page size and avoid prefetching more pages until writing resumes.",
                cost="A bounded stream keeps application buffering proportional to one database batch plus stream high-water buffers, O(K), rather than O(N) rows for an N-row export. Work remains O(N) in generated bytes and row serialization. Slow clients occupy a connection and database cursor longer, so set an export duration budget and concurrency cap. The stream high-water mark is a threshold, not a hard memory ceiling across every upstream buffer. For repeated or very large downloads, materialize an object-storage artifact once and serve it with its own retention and authorization policy. Measure queued bytes, drain waits, cursor duration, canceled scans, and completed bytes.",
                failure="Use a client that reads a few bytes and pauses for several seconds; memory should settle within the selected batch budget. Abort after the header, halfway through a quoted CSV field, and immediately after the last byte. A premature close must release the cursor and count as canceled, while a normal finish counts as delivered. Inject a database error after bytes have been sent and ensure the stream ends with an incomplete-download signal in logs; do not append a JSON error to the CSV. Revoke the officer's permission before starting a second request and make it fail before any private row is sent.",
                drill="Build a CSV export endpoint for permit 447 that emits 83 rows in batches of seven. Use a deliberately slow writable client to force write to return false. Count calls to the row provider and assert it does not fetch the next batch until drain. Abort after row 19 and verify cursor cleanup. Add a background alternative that stores an artifact with owner, expiry, and revision metadata. Compare the live stream and artifact path for a second download, a midstream failure, and permission revocation. Explain which path carries the lower database load for repeat readers.",
                decision="Live streams own short-lived work; durable exports own an artifact and a status record.",
                code='''function waitForDrain(response) {
  return new Promise((resolve, reject) => {
    function cleanup() {
      response.off("drain", onDrain);
      response.off("close", onClose);
    }
    function onDrain() { cleanup(); resolve(); }
    function onClose() { cleanup(); reject(new Error("client_closed")); }
    response.once("drain", onDrain);
    response.once("close", onClose);
  });
}

async function writeExportRows(response, rows) {
  for await (const inspectionRow of rows) {
    if (response.destroyed) throw new Error("client_closed");
    const line = `${inspectionRow.permitId},${inspectionRow.revision}\\n`;
    if (!response.write(line)) await waitForDrain(response);
  }
  if (response.destroyed) throw new Error("client_closed");
  response.end();
}''',
                mistakes=["Treating write(false) as a failed write rather than a pause signal.", "Continuing a database scan after the response closes.", "Appending an error JSON document to a partial CSV."],
                checks=["A slow reader keeps queued memory bounded.", "Client close releases the database cursor.", "A completed response and a canceled response have separate metrics."],
                related=["web-tech/stream-backpressure-and-bounded-work", "web-tech/stream-cancellation-and-partial-result-contract", "web-tech/private-export-authorization-and-artifact-scope"],
            ),
            dict(
                slug="node-cpu-work-worker-pool-and-event-loop-delay", title="Node CPU Work, Worker Pools, and Event Loop Delay",
                summary="Move bounded CPU tasks off the request loop without creating an unbounded worker queue.",
                concept="An awaited promise does not make synchronous JavaScript computation nonblocking. If a request handler spends 180 milliseconds parsing a huge rule set or calculating a map, other sockets wait for its callback to finish. Worker threads can execute CPU-heavy JavaScript in parallel, but each worker has startup, memory, serialization, and scheduling costs. Native asynchronous file and network operations already have their own efficient mechanisms; adding workers for those calls usually adds overhead. A useful design defines the maximum admitted jobs, a timeout, input size, result size, and cancellation behavior before choosing the number of workers.",
                case="A permit scoring endpoint receives a polygon with 47,000 points. One client requests a score while health checks and ordinary page requests are arriving. The handler computes the geometry synchronously and event loop delay jumps past the service budget. Starting one new worker for every score avoids blocking the main loop but creates hundreds of workers under burst load, trading latency for memory collapse. A small reused worker pool with a bounded queue admits a limited number of jobs and returns a busy response when full. The caller can cancel a queued job; a running computation needs cooperative interruption or termination with a clear cost.",
                implementation="Measure the expensive section before moving it. Keep cheap validation on the request thread so a malformed input never occupies a worker. Pass a compact task payload and stable task ID to a fixed pool; copy or transfer large buffers deliberately instead of assuming shared access. Reserve concurrency based on available CPU and other workloads, not number of HTTP sockets. A canceled browser request should remove a queued job and release its slot; a running job may finish for audit or stop at checkpoints according to the business contract. A worker crash must reject its current task and be replaced under a controlled restart budget. Never accept arbitrary code or module names from the client as a worker task.",
                cost="For N input items the scoring computation may be O(N log N) or worse, depending on geometry rules; offloading does not reduce that algorithmic cost. It adds O(B) serialization or transfer preparation for B input bytes, plus a bounded queue of at most Q tasks and W worker heaps. Throughput eventually reaches the CPU limit; a larger pool can increase contention rather than useful work. Track event loop delay, worker utilization, queue wait, task duration, rejection count, result size, and crash replacement. Use a benchmark that includes mixed cheap requests, since an isolated worker benchmark misses the purpose of protecting request latency.",
                failure="Run one expensive score beside a stream of tiny health requests and compare p95 event loop delay before and after offloading. Flood the endpoint with more jobs than the queue limit; excess calls must fail quickly and must not start more workers. Close one client while its task is queued and verify its slot is removed. Crash one worker during a task and ensure the task fails with a specific state rather than hanging forever. Feed an oversized polygon and make the cheap request boundary reject it before serialization. Measure CPU and resident memory as worker count rises, then choose a pool size from the actual machine budget.",
                drill="Create a scoring task for permit 447 with 4,700 points and a result that includes the input revision. Compare a synchronous handler, one-worker-per-request handler, and a three-worker bounded pool while twenty small requests arrive. Record p95 event loop delay, queue age, and memory. Reject an input above a point cap, cancel a queued task, and simulate a worker crash. Ensure a stale result for revision 6 cannot overwrite revision 7. Write down the rule for retrying a score whose worker died after the computation completed but before its result was observed.",
                decision="Bound CPU admission before parallelizing; workers protect responsiveness but do not create capacity from nothing.",
                code='''function admitScoreTask({ points, queuedTasks, queueLimit }) {
  if (!Array.isArray(points) || points.length > 4700) return "invalid_input";
  if (queuedTasks >= queueLimit) return "busy";
  return "admitted";
}

console.log(admitScoreTask({ points: Array(47).fill(0), queuedTasks: 2, queueLimit: 3 }));''',
                mistakes=["Assuming await makes a CPU loop yield to other requests.", "Creating a new worker for every request with no queue bound.", "Reporting only worker task time while request queue wait grows."],
                checks=["Cheap requests stay responsive during admitted scoring work.", "Worker and queue counts remain within configured limits.", "Cancel and crash paths release task ownership."],
                related=["web-tech/express-request-and-process-boundaries", "web-tech/load-tests-and-capacity-budgets", "web-tech/worker-leases-retries-and-duplicate-effects"],
            ),
            dict(
                slug="node-outbound-fetch-deadlines-and-response-ownership", title="Node Outbound Fetch Deadlines and Response Ownership",
                summary="Give each upstream call a deadline, size budget, and response owner before composing an API reply.",
                concept="A server-side fetch can stall at connection establishment, headers, or body consumption. A timeout that covers only one phase does not bound total request work. The handler needs a deadline for the entire operation and a smaller budget for each upstream, plus a bounded body read. An AbortSignal can stop a fetch when the caller disconnects or the deadline expires, but cancellation is not proof that an upstream mutation never happened. For reads, decide whether stale data is acceptable; for writes, use an idempotency identity and a reconciliation path. Send one final response only after the required upstream results have a defined state.",
                case="The permit detail endpoint reads the local record and a remote inspection timetable. The timetable normally answers in 120 milliseconds, but an upstream connection now hangs after headers. A handler with no body deadline holds sockets until the caller leaves. A second attempt races the first and returns inconsistent appointment dates. The corrected endpoint sets an overall deadline, caps timetable response bytes, and can serve the local permit with an explicit timetable-unavailable field if the feature contract permits it. It does not represent an unknown upstream mutation as a failed local write. An officer retry uses the same request identity when a remote reservation may already have succeeded.",
                implementation="Build a deadline from request arrival time, not from the moment each retry starts. Pass the same cancellation signal through the outbound call and bounded body reader. Limit redirects and validate the destination and content type so a partner response cannot turn into an arbitrary internal fetch or huge HTML payload. Parse a typed response before combining it with local data. Distinguish required upstream data from optional enrichment: required failures produce a service error, while optional failures have an explicit partial-state field and telemetry. For mutation calls, persist an idempotency key before sending and query the partner's status after an ambiguous disconnect. Never automatically retry an unsafe mutation with a new identity.",
                cost="A request that fans out to F upstream calls consumes up to F connections and accumulates body buffers, so concurrency control matters even when each call has a deadline. Serial calls add latencies; parallel calls reduce wall time but raise peak load and may increase tail behavior. Bounded retries multiply traffic and must fit inside the original deadline. An allowed stale cache lowers latency at the cost of freshness and needs an owner and expiry. Track time spent waiting for headers, body read time, bytes admitted, abort reason, ambiguous mutations, and partial responses. Capacity estimates should multiply arrival rate by outstanding upstream duration, especially during an outage.",
                failure="Delay connection establishment, then delay headers, then send headers and never finish the body. The overall deadline must stop each scenario. Send a response larger than the byte cap and another with the wrong content type. Disconnect the caller while a fetch is pending; confirm the local handler releases work. Make an upstream reservation commit and then sever the connection before its acknowledgment; a retry with the same identity must reconcile rather than create a second appointment. Test optional timetable failure separately from required permit-store failure so the endpoint never silently converts a real outage to a missing permit.",
                drill="Implement a permit 447 detail endpoint with a 900-millisecond total deadline and a 64-KiB timetable response cap. Return a typed partial result only if the timetable is optional. Add a small fake upstream that delays each phase separately, sends an oversized body, and commits a reservation before disconnecting. Log phase timing without request secrets. Drive twenty concurrent calls during an upstream stall and assert the number of open outbound calls remains bounded. Explain which fields are safe to cache and how a stale entry is marked to the caller.",
                decision="The caller deadline limits resource occupancy; idempotency and reconciliation settle ambiguous effects.",
                code='''function remainingBudget(startedAt, totalMilliseconds, now = Date.now()) {
  return Math.max(0, startedAt + totalMilliseconds - now);
}

const startedAt = 1000;
console.log(remainingBudget(startedAt, 900, 1470));''',
                mistakes=["Resetting the full deadline for each retry.", "Reading an unbounded upstream body after receiving headers.", "Treating a canceled mutation as proof it never committed."],
                checks=["A stalled body cannot exceed the overall request deadline.", "Optional and required upstream failures produce different contracts.", "An ambiguous mutation reconciles under one stable identity."],
                related=["web-tech/api-mutation-and-failure-contracts", "web-tech/ingress-proxy-and-upstream-contracts", "web-tech/job-admission-idempotency-and-status-resource"],
            ),
        ],
        crosslinks={
            "web-tech/express-request-and-process-boundaries": ["node-incoming-body-limits-and-abort-state", "node-cpu-work-worker-pool-and-event-loop-delay"],
            "web-tech/streaming-and-large-data-interfaces": ["node-response-backpressure-and-export-aborts"],
            "web-tech/ingress-proxy-and-upstream-contracts": ["node-outbound-fetch-deadlines-and-response-ownership"],
        },
        questions=[
            ("What is the reliable size of an incoming Node body?", "The bytes actually read from its stream", "The Content-Length header alone", "The number of JSON fields", "A caller can omit or misstate Content-Length; counted bytes enforce the admission budget."),
            ("When may a parsed body become an approval command?", "After complete read and typed validation", "After the first JSON-looking chunk", "After opening the socket", "An incomplete stream or malformed domain fields must not reach a state-changing service."),
            ("What does response.write returning false mean?", "Pause production until drain", "The write permanently failed", "The client has committed the export", "False signals backpressure; further unchecked writes can accumulate buffered bytes."),
            ("What should a live export do when its client closes early?", "Release its cursor and record cancellation", "Keep scanning every row", "Append an error JSON object", "The live stream owns a short-lived scan and should stop it when delivery becomes impossible."),
            ("Why move a CPU task to worker threads?", "To protect event-loop responsiveness", "To make network I/O synchronous", "To eliminate its algorithmic work", "Worker execution frees the request loop to handle other callbacks; the CPU work still has a cost."),
            ("What prevents a worker burst from exhausting memory?", "A fixed pool and bounded admission queue", "One worker per HTTP socket", "Awaiting a synchronous calculation", "A fixed worker and queue budget turns overload into a controlled rejection."),
            ("What starts the total outbound deadline?", "The incoming request's admission time", "Each retry's start time", "Only the moment headers arrive", "Resetting a budget for retries can extend resource occupancy far beyond the caller's deadline."),
            ("How is an ambiguous upstream write handled?", "Reuse its identity and reconcile state", "Assume cancellation rolled it back", "Repeat with a fresh identity", "A canceled local fetch cannot establish whether the upstream committed the effect."),
            ("What is the space cost of collecting an admitted body of B bytes?", "O(B) per concurrent request", "O(1) for all concurrency", "O(B squared) by definition", "Chunk collection and parsing each retain input-proportional data, multiplied by concurrent requests."),
            ("What is an HTTP stream high-water mark?", "A buffering threshold rather than a global memory cap", "A hard process RSS ceiling", "A maximum number of database rows", "Several buffers and producers can exist beyond one stream's threshold."),
            ("Which work should normally stay off worker threads?", "Ordinary asynchronous network I/O", "Heavy JavaScript geometry scoring", "Bounded CPU parsing after measurement", "Native async I/O already avoids blocking the request loop and workers add transfer overhead."),
            ("What must an optional upstream failure return?", "An explicit partial-state contract", "A fake successful timetable", "A missing-permit response", "The caller needs to distinguish absent enrichment from a missing resource or complete success."),
        ],
    ),
    dict(
        hub="php-request-session-and-persistence-boundaries",
        title="PHP Request, Session, and Persistence Boundaries",
        summary="Control PHP input, session identity, database writes, and upload ownership under any framework.",
        intro="A PHP request begins with server-populated inputs and ends when its response and request process finish. These lessons track a permit review from typed input through session authorization, a database transaction, and private document intake. The examples use PHP directly so framework abstractions can be evaluated against the same boundaries.",
        prereq=["web-tech/session-cookie-and-csrf-boundary", "web-tech/laravel-policy-query-and-queue-boundaries", "web-tech/safe-file-upload-pipeline"],
        project="php-permit-review-intake-project",
        project_title="Project: PHP Permit Review Intake",
        quiz="web-development-php-request-contracts",
        quiz_title="Web Development: PHP Request Contracts",
        topics=[
            dict(
                slug="php-superglobal-input-and-output-trust", title="PHP Superglobal Input and Output Trust",
                summary="Convert request globals into typed commands and escape only at the output context.",
                concept="PHP populates GET, POST, COOKIE, and FILES arrays before application code runs, but their values remain caller-controlled. A field expected to be a string may arrive as an array by using bracketed form names. A missing field, empty field, and malformed field need distinct decisions. Validate method, content type, and scalar shape at the edge, then convert to a small command object. Never use an input array wholesale in database writes or templates. Output encoding is a separate boundary: HTML text, HTML attributes, URLs, JSON, and SQL each have different handling rules. A single generic sanitizer cannot replace typed input and context-specific output.",
                case="An inspector submits permitId=447 and a revision number through a form. A forged request sends permitId[]=447; code that assumes a scalar emits a warning or turns an array into an unexpected value. Another payload includes markup in a note field that is valid text but dangerous if inserted into HTML without escaping. The correct handler rejects the array-shaped ID, accepts a bounded note as data, and uses HTML escaping only when rendering the note. A value used in a database query is bound as a parameter, not escaped with HTML rules. The audit record stores the original permitted note, not the display-escaped version.",
                implementation="Start with an explicit route contract: POST only, known content type, maximum field lengths, and typed required fields. Distinguish `isset` behavior from presence with an empty value, and inspect `is_string` before calling string functions. Use integer parsing with range checks rather than loose comparisons. Build a typed associative command from accepted fields, ignoring or rejecting unexpected fields based on the endpoint contract. On output, use escaping for the exact context; `htmlspecialchars` is appropriate for HTML text or quoted attributes with the right flags and encoding, but it does not make a URL safe or parameterize SQL. Keep CSRF verification, authentication, and object authorization as separate checks.",
                cost="A bounded request with F fields and B total bytes takes O(B) work to validate strings and construct the command. Unbounded arrays or repeated keys can create more parser and application work before this handler runs, so configure web server and PHP input limits as well. Escaping at render time costs O(L) for an L-character value and may expand its byte length. Do not pre-escape persisted data: it causes double encoding and makes the same record unusable in JSON or email. Track malformed shapes, field rejection rates, and output context failures without logging confidential form content. Tests should include every supported content type and nested-field shape.",
                failure="Send a missing permitId, an empty string, a negative ID, a bracketed array, and a string with trailing letters. Confirm none become permit 447 by loose coercion. Submit a note containing ampersands, quotes, and markup, then render it in HTML text and in a JSON response; each must preserve the data while using its own encoding. Feed a URL field with an unexpected scheme and show that HTML escaping alone does not approve it. Replay the form without a CSRF token and as a user who lacks access to permit 447. Neither case should reach the write transaction.",
                drill="Build a POST-only permit note handler that admits ID 447, revision 8, and a note of at most 720 characters. Reject array-shaped scalar fields, extra-long text, and invalid revision ranges with field-specific errors. Create a command array containing only these three fields. Render the saved note in an HTML page with the correct encoding and return it separately as JSON using the JSON encoder. Add tests for nested form names, malformed UTF-8 policy, a missing CSRF token, and a valid user who lacks record-level permission. Keep the validation result independent of the template implementation.",
                decision="Request arrays are untrusted transport data; domain commands and rendered outputs are separate representations.",
                code='''<?php
function permitIdFromPost(array $post): ?int {
    if (!isset($post['permitId']) || !is_string($post['permitId'])) return null;
    $permitId = filter_var($post['permitId'], FILTER_VALIDATE_INT);
    return is_int($permitId) && $permitId > 0 ? $permitId : null;
}

echo permitIdFromPost(['permitId' => '447']) . PHP_EOL;''',
                mistakes=["Assuming a form field is always a string.", "Persisting HTML-escaped text as the canonical note.", "Using HTML escaping as SQL or URL validation."],
                checks=["Array-shaped fields never become scalar domain IDs.", "HTML and JSON output preserve the same data safely.", "CSRF and record authorization run before writes."],
                related=["web-tech/http-request-response-contract", "web-tech/session-cookie-and-csrf-boundary", "web-tech/record-level-authorization"],
            ),
            dict(
                slug="php-session-rotation-locking-and-logout", title="PHP Session Rotation, Locking, and Logout",
                summary="Treat the session cookie as an identity pointer with explicit rotation, release, and revocation.",
                concept="A PHP session ID identifies server-side state; it is not the user's authorization policy by itself. Set secure cookie attributes before session startup, reject uninitialized IDs with strict mode, rotate the ID on a privilege change, and check current user and object permissions on every sensitive request. The default file-backed session handler can hold a lock while a request runs, delaying another same-session request until session data is written and closed. This can make an unrelated API call appear slow. Read what is needed, then release the session before a long export or remote call. Logout must invalidate server state and expire the browser cookie consistently.",
                case="Officer 47 signs in and opens a large export while another tab saves a short note. The export leaves the session open during a 23-second database stream, so the note request waits behind a session lock. On a second path, a login handler keeps the pre-login session ID and allows an attacker-known ID to become authenticated. A repaired flow enables strict mode, rotates on login, stores a minimal identity, closes the session before lengthy read-only work, and rechecks authorization at the operation boundary. Logout clears server session state and the cookie, while sensitive operations check revocation state rather than assuming an old cookie disappeared immediately.",
                implementation="Configure secure, HTTP-only, and an appropriate SameSite policy on HTTPS before session_start. Strict mode matters especially when accepting an unknown cookie; verify custom handlers actually validate IDs. Rotate when authentication or privilege level changes, while designing around parallel tabs and unstable networks instead of deleting the old state blindly in every case. Store a user ID and an authorization version rather than a copied permission list that can remain stale. Call session_write_close after the required read or write to release the session lock, then avoid mutating the closed session array as if it would be saved. For logout, clear state, destroy the server record, and issue an expired cookie with the same path and domain parameters.",
                cost="With a locking handler, concurrent requests from one browser can serialize: total wait time can approach the sum of their session-open durations. Early close removes this accidental queue but requires explicit treatment of later writes. Regenerating IDs creates write and cookie traffic, and rotation on every request can race across tabs; choose privilege transitions and defined periodic renewal. A distributed session store adds network cost and needs expiration and failure behavior. Measure session lock wait, open duration, rotation failures, stale authorization versions, and logout acceptance attempts. A cookie flag reduces one class of exposure but does not replace CSRF and output encoding.",
                failure="Open a long export and send a short authenticated request with the same cookie. Measure its wait before and after the export releases the session. Sign in with an uninitialized client-provided ID and verify strict mode issues a different admitted ID. Authenticate and confirm a rotation without losing the intended server state. Revoke officer 47's role while the cookie remains valid and ensure the next sensitive request fails. Log out, replay the old cookie, and verify it cannot read the permit. Test two tabs during rotation and a network retry so users are not silently signed out by a timing race.",
                drill="Implement a small session gateway for an inspection dashboard. It stores user ID 47, an auth version, and a CSRF secret. A login transition rotates the ID; an export reads identity, closes the session, then streams rows. A permission check consults current policy before the export begins. Add a short note request in another tab and time its response with and without early session close. Clear and destroy the session on logout and expire the cookie using the original cookie attributes. Include a custom-handler test that proves strict mode rejects uninitialized IDs.",
                decision="A session carries identity state briefly; current authorization and long-running work live outside its lock.",
                code='''<?php
ini_set('session.use_strict_mode', '1');
session_set_cookie_params([
    'secure' => true, 'httponly' => true, 'samesite' => 'Lax',
]);
session_start();
$reviewerId = $_SESSION['reviewerId'] ?? null;
session_write_close();
echo is_int($reviewerId) ? $reviewerId : 'anonymous';''',
                mistakes=["Holding the session lock through a slow export.", "Keeping the same ID across a login privilege change.", "Treating cookie deletion alone as server-side revocation."],
                checks=["A short same-session request does not wait for an export.", "Unknown or old IDs cannot silently become authenticated.", "Revoked permissions fail on the next sensitive operation."],
                related=["web-tech/account-recovery-and-session-revocation", "web-tech/permission-revocation-and-active-sessions", "web-tech/laravel-route-binding-policy-and-private-resource-scope"],
            ),
            dict(
                slug="php-pdo-transaction-replay-and-query-identity", title="PHP PDO Transactions, Replay, and Query Identity",
                summary="Bind query values and keep a replay key, version check, and outbox intent in one transaction.",
                concept="PDO prepared statements bind values separately from SQL syntax, but placeholders do not stand in for table names, column names, or sort directions. Those identifiers need a fixed allowlist. A transaction groups database changes; it does not make an outbound email or payment part of the same atomic unit. A mutating request also needs a stable replay identity when a response can be lost. Persist the identity with the effect, constrain it uniquely, and return the prior result on a retry. For concurrent edits, compare the expected record revision in the update condition so an older form cannot silently overwrite a newer review.",
                case="Reviewer 47 approves permit 447 at revision 8. The database commits revision 9, but the browser connection closes before the response. The browser retries; without a replay key it creates two audit rows and two email intents. Meanwhile reviewer 81 tries to approve the same permit based on revision 8. A transaction inserts one request identity, updates the permit only if its revision matches, appends one audit event and one outbox intent, then commits. The retry reads the saved outcome. Reviewer 81 gets a conflict rather than a successful overwrite. A worker sends the email from the outbox after commit and handles duplicate delivery with its own identity.",
                implementation="Use an allowlisted SQL shape and bind user data as values. Set PDO to throw exceptions and manage begin, commit, and rollback in one service boundary. Give the replay table a unique constraint on actor, route, and request key; store a request digest to detect reuse of the same key with different input. Update with a predicate on permit ID and expected revision, then inspect affected rows. Insert the audit event and outbox row only after a successful versioned update and before commit. On an exception, roll back if the transaction is active; do not turn every database error into a safe retry. Avoid performing an HTTP call while a database transaction holds locks.",
                cost="A keyed lookup or uniqueness check is usually O(log N) with a database index, while the transaction also pays log writes and lock time for each mutation. The version predicate adds little query cost when permit ID is indexed, but conflicting writers must retry with fresh state. An outbox introduces storage and a worker scan, trading that cost for recoverable side effects. Long transactions increase lock contention and can reduce throughput. Keep replay records for a documented window; deleting them too soon permits late duplicate effects. Measure commit latency, conflict rate, replay hit rate, outbox age, and delivery attempts separately from HTTP success count.",
                failure="Send one approval with a fixed request key, sever the response after commit, then resend the exact body and key. Only one revision increment, audit event, and outbox intent may exist. Reuse that key with a different permit or decision and require a conflict. Race two reviewers with expected revision 8; only one update may succeed. Inject a database failure after the permit update but before the outbox insert, and verify rollback removes both changes. Make the email worker fail after sending but before marking done; its retry needs a stable delivery identity and a reconciliation policy rather than assuming exactly-once network delivery.",
                drill="Create SQLite tables for permits, replay keys, audit events, and outbox intents. Start permit 447 at revision 8 and status pending. Implement an approve command with actor 47, expected revision, and a caller-generated key. Run it twice with identical input, once with a changed body under the same key, and once concurrently with another actor. Query all four tables after every case. Add a test that throws before commit. The endpoint should distinguish replay, version conflict, invalid key reuse, and database failure in its response contract.",
                decision="A database transaction owns local state; durable intent and replay identity bridge uncertain network boundaries.",
                code='''<?php
$statement = $database->prepare(
    'UPDATE permits SET status = ?, revision = revision + 1 '
    . 'WHERE permit_id = ? AND revision = ?'
);
$statement->execute(['approved', 447, 8]);
if ($statement->rowCount() !== 1) {
    throw new RuntimeException('revision_conflict');
}''',
                mistakes=["Using placeholders for SQL identifiers.", "Calling an email service inside a database transaction.", "Retrying an approval with a new identity after an uncertain response."],
                checks=["A repeated command creates one local effect.", "A stale revision conflicts without an audit or outbox row.", "A transaction failure removes every partial local write."],
                related=["web-tech/idempotent-write-requests", "web-tech/background-jobs-and-outbox", "web-tech/laravel-form-request-transaction-and-approval-replay"],
            ),
            dict(
                slug="php-upload-tempfile-private-storage-and-lifecycle", title="PHP Upload Tempfiles, Private Storage, and Lifecycle",
                summary="Validate the upload error and actual bytes before moving a temporary file into private ownership.",
                concept="PHP places multipart uploads in temporary files and exposes metadata through FILES. The browser-supplied filename and content type are claims, not verified properties. First handle upload error codes and configured body limits; a request exceeding the total POST limit may leave expected fields absent rather than yielding a normal per-file error. Admit the file only after checking type from bytes, allowed dimensions or structure, size, and the caller's permission to attach it to the target record. Move it to a private, generated location, then create a database record that tracks scan status, owner, and retention. A public URL is a separate publication decision.",
                case="An inspector attaches a 4.7 MiB site plan to permit 447. The form filename is `plan.pdf`, but the bytes are an executable archive. Another upload uses a path-like filename and a third exceeds the PHP request limit, leaving FILES empty. A naive handler moves files under the original name into the web root and records attachment success before scanning. The repaired path rejects the wrong byte type and missing upload state, generates an opaque storage key, moves only an admitted temporary upload into private storage, and marks it pending until inspection and malware checks finish. A failed database insert deletes the orphaned moved file or records a compensating cleanup task.",
                implementation="Align reverse-proxy body limits, PHP post_max_size, upload_max_filesize, and application limits, then test their different failure shapes. Check UPLOAD_ERR_OK before using tmp_name, require is_uploaded_file when examining the temporary source, and use move_uploaded_file for the final move. Never derive a destination path directly from the client filename; retain a normalized display name separately. Inspect actual bytes with an appropriate decoder or file-info probe, and apply domain-specific content rules. Place the object outside the public web root or behind authenticated storage. Create a pending record before asynchronous scanning only if orphan repair is defined; make promotion to available state conditional on scan result and current authorization.",
                cost="Reading or hashing an admitted file of B bytes costs O(B) I/O; decoding a large image can require memory proportional to expanded pixels rather than compressed bytes. A temporary copy and final object may briefly coexist, so disk headroom must cover concurrent in-flight uploads. Malware scanning adds queue time and requires a pending state visible to users. Keeping every rejected file indefinitely is a storage and privacy problem; cleanup needs a retention clock. Measure post-limit failures, per-file errors, type mismatches, move failures, pending-scan age, orphan count, and private download authorization failures. Do not make synchronous scanning block all upload workers if the scanner has variable latency.",
                failure="Upload a correct small PDF, a filename with traversal characters, a renamed archive, a zero-byte file, and a multipart body over each configured limit. Observe which cases produce FILES error codes and which produce an empty request. Force move_uploaded_file to fail, then force the database insert to fail after a successful move; both must leave a recorded recoverable state or no retained file. Try downloading while the attachment is pending, after it is rejected, and as another tenant. Upload two files with the same display name and verify neither overwrites the other. Revoke permit access between admission and final publication.",
                drill="Create a private permit-attachment intake for permit 447 with a 5 MiB application cap. Generate a random storage key, preserve a safe display name, and keep accepted files unavailable until a simulated scan marks them clean. Add an orphan cleanup pass for moved bytes whose database record was never committed. Test total request limit behavior separately from UPLOAD_ERR_INI_SIZE. Attach the same name twice and verify distinct keys. Require both current record permission and clean status to issue a download. Record the lifecycle transitions pending, available, rejected, and expired.",
                decision="Temporary upload bytes become a private managed asset only after validation, ownership, and cleanup rules are established.",
                code='''<?php
function uploadReady(array $upload, int $maximumBytes): bool {
    return ($upload['error'] ?? null) === UPLOAD_ERR_OK
        && is_int($upload['size'] ?? null)
        && $upload['size'] > 0
        && $upload['size'] <= $maximumBytes
        && is_string($upload['tmp_name'] ?? null)
        && is_uploaded_file($upload['tmp_name']);
}''',
                mistakes=["Trusting the client filename or content type as proof of format.", "Moving admitted bytes directly under a public path.", "Assuming every oversized POST creates a FILES error entry."],
                checks=["Private storage keys do not derive from caller filenames.", "Pending or rejected files cannot be downloaded.", "A failed move or database write has a cleanup path."],
                related=["web-tech/safe-file-upload-pipeline", "web-tech/upload-intake-budgets-and-storage-ownership", "web-tech/tenant-scope-in-cache-and-background-work"],
            ),
        ],
        crosslinks={
            "web-tech/laravel-policy-query-and-queue-boundaries": ["php-pdo-transaction-replay-and-query-identity", "php-superglobal-input-and-output-trust"],
            "web-tech/session-cookie-and-csrf-boundary": ["php-session-rotation-locking-and-logout"],
            "web-tech/file-ingestion-and-private-asset-lifecycle": ["php-upload-tempfile-private-storage-and-lifecycle"],
        },
        questions=[
            ("What can a PHP form field unexpectedly contain?", "An array despite a scalar contract", "Only a validated string", "Only an integer", "Bracketed form names can make a supposedly scalar field arrive as an array."),
            ("Where should a saved note be escaped for HTML?", "At HTML output for its exact context", "Before it is stored as canonical data", "Only when it enters SQL", "Persisted text remains data; HTML escaping is chosen for the rendering context."),
            ("What does strict PHP session mode reject?", "Uninitialized caller-supplied session IDs", "All valid returning users", "Every cross-site request", "Strict mode prevents adoption of an ID that has no initialized server session."),
            ("Why close a read-only session before a long export?", "To release its lock for other same-session requests", "To make the export public", "To rotate the cookie each row", "A file-backed session lock may serialize requests from the same browser until it closes."),
            ("Can a PDO placeholder name a sort column?", "No; allowlist identifiers in SQL shape", "Yes; every SQL token is bindable", "Only after HTML escaping", "Prepared parameters bind values, while structural SQL identifiers need a controlled allowlist."),
            ("What protects a permit update from a stale form?", "An expected-revision predicate", "An HTML hidden field alone", "A longer session cookie", "The database update must compare the submitted revision with current state atomically."),
            ("How should a lost response after commit be retried?", "With the same replay identity", "With a new request key", "Without checking existing effects", "A stable identity lets the server return the saved outcome without duplicating writes."),
            ("What can happen when post_max_size is exceeded?", "Expected form and file fields may be absent", "The file always reports UPLOAD_ERR_OK", "The server stores an admitted file", "A request rejected at the overall body limit may not populate the normal FILES entry."),
            ("What is safe as a private upload storage key?", "A server-generated opaque key", "The original filename", "A path supplied by the browser", "The caller controls filenames; storage names must avoid collisions and path manipulation."),
            ("When may an uploaded attachment become downloadable?", "After authorization and clean-state promotion", "Immediately after it reaches a temp file", "Whenever its extension is PDF", "Temporary receipt does not establish trust, ownership, or scan completion."),
            ("Where does an outbound email belong relative to the PDO transaction?", "In a durable outbox intent committed with local state", "Inside the database lock as a network call", "Before input validation", "The database cannot atomically commit an external send; an outbox preserves intent for later delivery."),
            ("What must a logout clear?", "Server session state and the matching browser cookie", "Only visible page text", "Only a frontend variable", "Old server state and a replayable cookie must both be invalidated under the session policy."),
        ],
    ),
]


for track_number, track in enumerate(tracks):
    hub_path = "web-tech/" + track["hub"]
    assert hub_path not in by_path
    base_order = 3780 + 10 * track_number
    hub = copy.deepcopy(by_path["web-tech/fastapi-contract-and-resource-boundaries"])
    hub.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + hub_path)), path=hub_path,
               title=track["title"], summary=track["summary"], sort_order=base_order,
               created_at=stamp, updated_at=stamp, published_at=stamp)
    hub["data"] = {"subject_root": "web-tech/web-technology", "section_path": hub_path,
                   "content_format": "html", "seo_ready": False, "modules": [], "resource_tabs": [
                       {"title": "Web Development", "path": "web-tech/web-technology"},
                       {"title": "Projects", "path": "web-tech/web-technology/project"},
                       {"title": "Quizzes", "path": "web-tech/quizzes"}]}
    entries.append(hub)
    by_path[hub_path] = hub
    lesson_paths = ["web-tech/" + topic["slug"] for topic in track["topics"]]
    project_path = "web-tech/" + track["project"]
    quiz_path = "quizzes/" + track["quiz"]
    for index, topic in enumerate(track["topics"]):
        path = lesson_paths[index]
        assert path not in by_path
        if track_number == 0:
            subprocess.run(["node", "--input-type=module", "--check"], input=topic["code"], text=True, check=True, capture_output=True)
        else:
            subprocess.run(["php", "-l"], input=topic["code"], text=True, check=True, capture_output=True)
        lesson = copy.deepcopy(by_path["web-tech/trace-context-across-request-and-job"])
        lesson.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                      title=topic["title"], summary=topic["summary"], sort_order=base_order + index + 1,
                      created_at=stamp, updated_at=stamp, published_at=stamp)
        related = [hub_path] + [other for other in lesson_paths if other != path] + topic["related"]
        body = p(topic["concept"]) + "<h2>Working case</h2>" + p(topic["case"])
        body += "<h2>Implementation boundary</h2>" + code_block(topic["code"], "javascript" if track_number == 0 else "php") + p(topic["implementation"])
        body += "<h2>Cost and boundaries</h2>" + p(topic["cost"]) + "<h2>Failure trace</h2>" + p(topic["failure"])
        body += "<h2>Verification</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in topic["checks"]) + "</ul>"
        body += "<h2>Practice drill</h2>" + p(topic["drill"]) + "<h2>Decision note</h2>" + p(topic["decision"])
        body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in topic["mistakes"]) + "</ul>"
        lesson["body"] = body
        lesson["data"] = {"subject_root": "web-tech/web-technology", "section_path": hub_path,
                          "content_format": "html", "seo_ready": False, "kind": "tutorial",
                          "author_path": "authors/aitrove-editorial", "reading_minutes": 8, "related": related}
        entries.append(lesson)
        by_path[path] = lesson
    for path in lesson_paths:
        lesson = by_path[path]
        lesson["body"] += "<h2>Related lessons</h2><p>" + "; ".join(a(target) for target in lesson["data"]["related"]) + ".</p>"

    hub["data"]["modules"] = [{"title": track["title"], "summary": track["summary"], "lessons": lesson_paths}]
    hub["body"] = p(track["intro"]) + "<h2>Topics in this track</h2><ul>" + "".join(
        "<li>" + a(path) + " — " + html.escape(by_path[path]["summary"]) + "</li>" for path in lesson_paths) + "</ul>"
    hub["body"] += "<h2>Prerequisite paths</h2><p>" + "; ".join(a(path) for path in track["prereq"]) + ".</p>"
    curriculum = by_path["web-tech/web-technology"]
    curriculum["data"]["modules"].append({"title": track["title"], "summary": track["summary"], "lessons": [hub_path] + lesson_paths})
    curriculum["body"] += "<h2>" + a(hub_path) + "</h2>" + p(track["summary"]) + "<ul>" + "".join(
        "<li>" + a(path) + " — " + html.escape(by_path[path]["summary"]) + "</li>" for path in lesson_paths) + "</ul>"
    curriculum["updated_at"] = stamp
    for existing_path, slugs in track["crosslinks"].items():
        existing = by_path[existing_path]
        existing["body"] += "<h2>Runtime connections</h2><p>" + "; ".join(a("web-tech/" + slug) for slug in slugs) + ".</p>"
        existing["updated_at"] = stamp

    project = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
    project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
                   title=track["project_title"], summary=track["summary"], sort_order=base_order + 5,
                   created_at=stamp, updated_at=stamp, published_at=stamp)
    project["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                       "content_format": "html", "seo_ready": False, "kind": "project", "author_path": "authors/aitrove-editorial",
                       "reading_minutes": 10, "related": [hub_path] + lesson_paths}
    if track_number == 0:
        project["body"] = p("Build a native Node permit gateway with four routes: a bounded JSON approval command, a live CSV export, a CPU-heavy inspection score, and a timetable read. Permit 447 begins at revision 8. An oversized command, aborted body, slow reader, canceled score, worker crash, or stalled timetable must have an observable state. Every route has a byte, time, and concurrency budget. The goal is to hold cheap request latency steady when one expensive operation misbehaves; a successful happy-path response alone is not sufficient evidence.")
        requirements = ["Count actual request bytes and validate a complete typed command before mutation.", "Stop CSV production on response backpressure and release its cursor on disconnect.", "Bound worker count and queue length; reject overload without blocking the event loop.", "Carry one total deadline through outbound headers, body read, and retries.", "Reconcile an ambiguous upstream mutation under one stable identity."]
        checkpoint = '''function routeBudget(kind) {
  return { intake: 37 * 1024, export: 7, timetable: 64 * 1024 }[kind] ?? null;
}
console.log(routeBudget("intake"), routeBudget("timetable"));'''
        expected = "37888 65536"
        subprocess.run(["node", "-e", checkpoint], check=True, text=True, capture_output=True)
        project["body"] += "<h2>Build contract</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in requirements) + "</ul>"
        project["body"] += "<h2>Implementation checkpoint</h2>" + code_block(checkpoint, "javascript")
        project["body"] += "<h2>Cost and boundaries</h2>" + p("Reading B admitted body bytes uses O(B) time and retained memory. A streamed export over N rows uses O(N) total work and a bounded O(K) batch buffer when upstream fetching pauses with the response. A worker pool adds W worker heaps and at most Q queued task payloads; worker count is a capacity decision, not a function of connection count. Outbound fanout costs up to F concurrent upstream connections per request. Record the queue and byte budgets beside p95 request latency so a load test can show where the first limit is reached.")
        project["body"] += "<h2>Failure drill</h2>" + p("Run an absent or false Content-Length, a truncated JSON body, and a limit-plus-one request. Slow the CSV reader and abort after row 19. Flood the score route past its queue cap, then kill a worker mid-task. Delay the timetable after headers and make a reservation commit before its connection drops. The system must not duplicate the reservation or turn its unknown state into a clean failure. Repeat with twenty ordinary detail requests in flight and verify they retain the agreed latency budget. Inspect resource cleanup, not only returned status codes.")
    else:
        project["body"] = p("Build a PHP permit review service for permit 447. It starts at revision 8 with one reviewer session and no attachments. A typed form command saves a note, an approval transaction advances the record once under a replay key, and a private upload becomes downloadable only after validation and a clean scan. The same reviewer opens a long export in another tab. The project is complete when malformed field shapes, session races, lost responses, stale revisions, and upload failures all have named outcomes and leave consistent records.")
        requirements = ["Convert superglobal fields into a typed command before authorization or persistence.", "Rotate the session at login and release its lock before slow read-only work.", "Commit a versioned permit update, replay identity, audit event, and outbox intent together.", "Keep uploaded bytes private under server-generated names until a clean-state transition.", "Expire browser and server session state on logout and recheck current permissions."]
        checkpoint = '''<?php
$permit = ['id' => 447, 'revision' => 8, 'status' => 'pending'];
$expectedRevision = 8;
if ($permit['revision'] === $expectedRevision) {
    $permit['revision']++;
    $permit['status'] = 'approved';
}
echo $permit['revision'] . ' ' . $permit['status'];'''
        expected = "9 approved"
        project["body"] += "<h2>Build contract</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in requirements) + "</ul>"
        project["body"] += "<h2>Implementation checkpoint</h2>" + code_block(checkpoint, "php")
        project["body"] += "<h2>Cost and boundaries</h2>" + p("Validation and file inspection are linear in admitted input bytes. Index-backed replay lookup adds a small database operation to each mutation, and an outbox adds retained intent records and worker delivery. Holding a session lock through a long export can serialize same-session requests for the entire export duration. A private upload temporarily occupies both PHP temporary storage and final storage, while a scanner adds pending time. Measure lock wait, transaction duration, replay hits, outbox age, pending scan age, and orphan bytes; a fast response does not prove background effects were completed.")
        project["body"] += "<h2>Failure drill</h2>" + p("Submit an array-shaped permit ID, malformed revision, and note containing markup. Start a 23-second export and save a note in another tab; the note must not wait on a session lock. Commit approval and drop the response, then retry with the same key and with a changed body under that key. Race a stale reviewer against the version update. Upload a renamed archive, a body over post_max_size, and two files with the same display name. Force a failure after moving bytes but before the database record commits. Every retained file must be traceable to a private owner or cleanup task.")
    project["body"] += "<h2>Acceptance checks</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in requirements) + "</ul>"
    project["body"] += "<h3>Common Mistakes</h3><ul><li>Checking only successful responses instead of failed intermediate states.</li><li>Conflating a local cancellation with rollback of an external effect.</li><li>Leaving resource ownership implicit after client disconnect.</li></ul>"
    project["body"] += "<h2>Related lessons</h2><p>" + "; ".join(a(path) for path in project["data"]["related"]) + ".</p>"
    entries.append(project)
    by_path[project_path] = project
    result = subprocess.run(["node", "-e", checkpoint] if track_number == 0 else ["php"], input=None if track_number == 0 else checkpoint,
                            text=True, check=True, capture_output=True)
    assert result.stdout.strip() == expected, (project_path, result.stdout)

    balanced = []
    assert len(track["questions"]) == 12
    for index, (prompt, correct, distractor_one, distractor_two, explanation) in enumerate(track["questions"]):
        assert len(explanation) >= 70, (track["hub"], prompt)
        answer = index % 3
        options = [distractor_one, distractor_two]
        options.insert(answer, correct)
        balanced.append({"prompt": prompt, "options": options, "answer": answer, "explanation": explanation})
    quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
    quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
                title=track["quiz_title"], summary="Twelve explained runtime boundary decisions for " + track["title"] + ".",
                sort_order=base_order + 6, created_at=stamp, updated_at=stamp, published_at=stamp)
    quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes",
                    "content_format": "html", "seo_ready": False, "questions": balanced}
    quiz["body"] = p(quiz["summary"] + " Choose a decision, inspect the reason, then return to the related failure drill.")
    quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(a(path) for path in [hub_path] + lesson_paths + [project_path]) + ".</p>"
    entries.append(quiz)
    by_path[quiz_path] = quiz
    for index_path, target in [("web-tech/web-technology/project", project_path), ("web-tech/quizzes", quiz_path)]:
        index = by_path[index_path]
        index["data"]["modules"][0]["lessons"].append(target)
        index["body"] += "<h2>" + a(target) + "</h2>" + p(by_path[target]["summary"])
        index["updated_at"] = stamp
    hub["body"] += "<h2>Practice and check</h2><p>Build " + a(project_path) + " and review " + a(quiz_path) + ".</p>"
    for path in lesson_paths:
        lesson = by_path[path]
        lesson["body"] += "<h2>Apply and check</h2><p>Build " + a(project_path) + " and review " + a(quiz_path) + ".</p>"
        lesson["data"]["related"].extend([project_path, quiz_path])
    curriculum["body"] += "<h2>" + html.escape(track["title"] + " practice") + "</h2><p>" + a(project_path) + "; " + a(quiz_path) + ".</p>"

word_counts = {}
for track in tracks:
    for topic in track["topics"]:
        path = "web-tech/" + topic["slug"]
        prose = re.sub(r"<pre>.*?</pre>", " ", by_path[path]["body"], flags=re.S)
        prose = html.unescape(re.sub(r"<[^>]+>", " ", prose))
        word_counts[path] = len(re.findall(r"\b[\w'-]+\b", prose))
        assert word_counts[path] >= 480, (path, word_counts[path])

FIXTURE.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"hubs": 2, "lessons": 8, "projects": 2, "quizzes": 2, "prose_words": word_counts}))
