"""Add Express 5 and Node.js request-lifecycle tutorials to Web Development."""
import copy
import datetime
import html
import json
import re
import subprocess
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
by_path = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def paragraph(value):
    return "<p>" + html.escape(value) + "</p>"


def link(path):
    assert path in by_path, path
    return '<a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a>"


hub_path = "web-tech/express-request-and-process-boundaries"
hub_title = "Express Request and Process Boundaries"
topics = [
    dict(
        slug="express-middleware-order-and-request-identity",
        title="Express Middleware Order and Request Identity",
        summary="Place parsing, authentication, authorization, routing, and errors in an intentional request sequence.",
        concept="An Express application is an ordered stack of middleware and route handlers. Each handler can end the response, call next to continue, or pass an error into the error path. Registration order therefore changes behavior. Authentication identifies the caller; authorization decides whether that caller may act on a specific resource. A valid session does not automatically grant access to every permit ID. Parsing a body before applying limits or reading an untrusted forwarding header before a trusted proxy boundary can also change the security properties of every later route. The stack should make these dependencies visible. A reviewer route must never depend on a middleware that is registered after it has already sent a response.",
        case="A permit API registers its approval router before authentication. The route reads req.reviewer, finds it undefined, and falls back to a development identity left in a helper. Another route allows any signed-in reviewer to fetch case 81 because it checks only whether a session exists. A logging middleware runs after the router and misses successful requests. The repaired stack sets correlation metadata early, limits and parses JSON, authenticates before mounting the private router, and performs case-level authorization inside the repository operation. A final unmatched-route handler returns 404. The error handler sits after routes and maps failures without disclosing private details.",
        implementation="Write down each route's prerequisites and register them before the route. Validate the deployment's proxy trust settings before using forwarded host, scheme, or client IP; an attacker-supplied header is not an identity. Apply body limits and content-type checks before processing private commands. Authentication middleware should resolve a server-owned reviewer object or stop with 401. In the route, validate the case ID, ask a service to verify permission for that reviewer and case, and return a controlled 403 or 404 according to the product's disclosure rule. Keep authorization in the service as well if other callers can reach it. Register a 404 handler after routes and a four-argument error handler last. Test both matching and nonmatching paths.",
        cost="Each middleware adds request work; a session lookup and case permission query may dominate a small route. Moving a check later to save time can be safe only when no earlier handler observes or mutates protected data. Body parsing has memory cost proportional to accepted payload size, so a configured limit matters under hostile traffic. A repeated permission lookup can be batched or cached within one request, but a shared cache needs the full reviewer and permission boundary. Correlation IDs add small header and log cost while making failures traceable. Measure authentication latency, authorization query count, body rejection rate, and the number of requests that reach expensive handlers unnecessarily.",
        failure="Call the private route without a session, with an expired session, and with a valid reviewer who lacks case permission. None may enter the mutation service as an authorized write. Register a test logger after the router and observe that a successful response bypasses it, then move it before the route. Send malformed JSON and a body above the configured limit; the route must not begin its write. Send forged forwarding headers from an untrusted connection and verify they do not change identity or audit attribution. Request an unknown path and confirm 404 rather than a silent hang. Test an error thrown during permission lookup and inspect the final response.",
        drill="Build a private permit router for read and approval paths. Create a middleware sequence diagram before writing code. Add request identity and a bounded JSON parser, then mount authentication and the router. Inside each handler, parse the case ID and call a service that checks the reviewer against that case. Attach a correlation ID to logs and error output without echoing private service messages. Exercise missing identity, wrong-case access, malformed body, oversize body, and a successful request. Reorder the authentication middleware deliberately in a negative test; restore it after showing the failed invariant.",
        decision="Register middleware in prerequisite order, and authorize the exact resource at the service boundary.",
        code='''import express from 'express';
import { requireReviewer, permitService, reportError } from './services.js';

const app = express();
app.use(express.json({ limit: '47kb' }));
app.use('/api/permits', requireReviewer);
app.get('/api/permits/:caseId', async (request, response) => {
  const caseId = Number(request.params.caseId);
  if (!Number.isSafeInteger(caseId) || caseId < 1) return response.sendStatus(400);
  const permit = await permitService.findAuthorized(request.reviewer.id, caseId);
  if (!permit) return response.sendStatus(404);
  response.json({ id: permit.id, title: permit.title, status: permit.status });
});
app.use((request, response) => response.sendStatus(404));
app.use((error, request, response, next) => {
  reportError(error, request);
  if (response.headersSent) return next(error);
  response.status(500).json({ message: 'Request failed' });
});''',
        checks=["Private routes run only after authentication.", "Case-level permission is checked in the service.", "Unknown paths and route errors end in controlled responses."],
        mistakes=["Registering identity middleware after the route.", "Treating a valid session as permission for every case.", "Trusting forwarded headers without a configured proxy boundary."],
        related=["web-tech/authorization-and-tenant-boundaries", "web-tech/ingress-proxy-and-upstream-contracts"],
    ),
    dict(
        slug="express-five-async-errors-and-response-contracts",
        title="Express 5 Async Errors and Response Contracts",
        summary="Route rejected promises once and distinguish validation, conflict, and internal failures.",
        concept="Express 5 routes and middleware that return rejected promises pass those rejections to the error handler. That is different from an unreturned promise started in the background; the router cannot catch work it does not own. A response also has a one-way boundary. Before headers are sent, a centralized handler can choose a status and safe body. After streaming headers are sent, it cannot replace a partial response with a new JSON error. Client-facing errors should separate malformed input, denied access, missing resources, conflicts, and internal failures without exposing service traces. A route should send exactly one response or call next exactly once for its error path.",
        case="A permit approval handler starts an async repository update without awaiting or returning it, sends 202, and later throws when the database rejects. The caller believes the case was approved. Another handler catches an error, calls next(error), and then sends a 500 body; the centralized handler also tries to send, producing a headers-sent failure. The repaired handler awaits one operation, maps expected domain outcomes to 400, 403, 404, or 409, and leaves unexpected rejection to Express 5's error path. The final handler logs a correlation ID and returns a generic 500 only when headers remain unsent. An already streaming response is delegated for connection handling.",
        implementation="Target the actual Express major version in the application lockfile; do not assume automatic promise forwarding in an older deployment. In Express 5, an async route should await its database or service call and either send its result or throw. Do not launch a detached promise for a request-critical write. Map expected service results locally, because a domain conflict is not an internal exception. In the final error middleware, keep all four parameters so Express recognizes it, log internal context separately, and check headersSent before setting a new status. When a response stream has begun, propagate the error to the default handler or close the stream according to the transport contract. Avoid exposing stack traces, tokens, or private case titles in the client body.",
        cost="One central error mapper reduces repeated code but adds a shared dependency to every route. Logging full error objects can leak sensitive payloads and consume space under an incident; redact before writing. Returning 202 before a critical write finishes can make latency look low while moving the failure outside the request contract. Waiting for a committed result adds response time, but it gives the client an honest outcome. A streamed response saves time to first byte yet narrows recovery choices once headers have left. Measure rejected promise count, double-send attempts, partial responses, and time to confirmed mutation, not only nominal status codes.",
        failure="Force a repository rejection before the response and confirm one generic 500 with a logged correlation ID. Return a domain conflict and confirm 409 without a stack trace. Start a detached promise as a negative test and show that its rejection escapes the route; repair by awaiting it. Throw after a streamed first chunk and verify the server does not attempt a second JSON body. Call next twice in a test middleware and watch for duplicate error handling, then remove the second call. Validate that a 403 response does not reveal whether a forbidden private case exists if the API's disclosure rule forbids that information.",
        drill="Implement an approval route in an Express 5 test app with a fake service returning approved, invalid, forbidden, missing, and conflict states. Add one injected unexpected rejection. Write expected status and response body for each case before coding. Then stream a diagnostic export, fail after the first chunk, and inspect the connection behavior. Verify the four-argument error handler and headersSent path. Repeat one test with an unreturned promise to demonstrate why request-critical work must remain inside the returned async handler.",
        decision="Await request-critical work, map domain outcomes explicitly, and let one error path own unexpected failures.",
        code='''import express from 'express';
import { permitService, reportError } from './services.js';

const app = express();
app.post('/api/permits/:caseId/approve', async (request, response) => {
  const result = await permitService.approve(request.reviewer.id, request.params.caseId);
  if (result.kind === 'forbidden') return response.sendStatus(403);
  if (result.kind === 'missing') return response.sendStatus(404);
  if (result.kind === 'conflict') return response.status(409).json({ message: 'Case changed' });
  response.json({ caseId: result.caseId, status: result.status });
});
app.use((error, request, response, next) => {
  reportError(error, request);
  if (response.headersSent) return next(error);
  response.status(500).json({ message: 'Request failed' });
});''',
        checks=["A rejected async route reaches one error handler.", "Expected domain outcomes have distinct controlled statuses.", "No second body is sent after headers have left."],
        mistakes=["Starting request-critical work without awaiting or returning it.", "Calling next(error) and also writing a response.", "Assuming an older Express version forwards rejections the same way."],
        related=["web-tech/api-mutation-and-failure-contracts", "web-tech/streaming-and-large-data-interfaces"],
    ),
    dict(
        slug="node-request-budgets-abort-and-event-loop-fairness",
        title="Node Request Budgets, Abort, and Event Loop Fairness",
        summary="Bound input and work so one slow or hostile request does not stall unrelated traffic.",
        concept="Node handles many HTTP requests through an event loop that runs JavaScript callbacks. A synchronous CPU task inside one route delays callbacks for other clients. Asynchronous I/O avoids waiting on the loop, but an async function that performs a large synchronous parse or sort still blocks before it yields. A request also has several budgets: accepted body size, header and receive timeouts, database deadline, response time, and downstream cancellation. A client disconnect can signal that some read work is no longer useful; it cannot undo a database write that already committed. Budgeting must account for both honest slow clients and deliberately expensive inputs.",
        case="A permit export endpoint accepts an unbounded filter and then sorts 470,000 records in one JavaScript callback. While it runs, a second reviewer cannot load a small case detail. Another client disconnects during a slow report query, but the server continues fetching and allocating results for a response nobody will read. The repair validates and bounds the query, uses a database order and paged cursor rather than full in-memory sort, and passes an abort signal to cancelable read work when the connection closes. Approval writes remain governed by operation identity because cancellation after commit would not revert them. Request and downstream deadlines are measured separately.",
        implementation="Set server and proxy request limits deliberately and apply bounded body parsing before expensive work. Parse filter values with a length and character policy; avoid a regex whose runtime explodes on crafted input. Push indexed filtering and ordering to the database and return one bounded page. Use an AbortController for read-only downstream operations when the service supports cancellation. Check response closure before sending, and remove event listeners when the request finishes so they do not accumulate. Do not infer that an aborted client canceled a committed mutation. Offload truly CPU-heavy, bounded jobs to a worker or background queue when measured event-loop delay warrants it, with a separate job deadline and admission limit.",
        cost="A database index consumes storage and write maintenance but avoids O(n log n) application sorting for every request. A paged read limits response memory to O(page size). Worker offload adds message transfer and scheduling overhead; it is not free for small tasks. Timeout values trade completion under slow networks against resource occupancy. Abort listeners and controllers add small per-request state and must be cleaned up. Measure event-loop delay, p95 route latency, canceled-read count, database time, memory high-water mark, and the number of active long requests. A fast average can conceal one hostile request starving the loop.",
        failure="Send an oversized JSON body and confirm rejection before the service call. Request a page size of 470,000 and verify the server clamps or rejects it. Start a slow authorized read, disconnect, and confirm the downstream read is canceled where supported. Start an approval, disconnect just after commit, and verify replay with the same operation ID returns the committed result. Run one intentionally synchronous large sort in a test process while measuring latency of a small detail route; remove that sort from the request path. Force a deadline expiration and confirm no late read response is written to a closed socket.",
        drill="Build a bounded permit search route with a maximum 47-row page, a short query string, and an indexed repository method. Add a request budget that aborts a cancelable read on disconnect or deadline. Instrument event-loop delay and concurrent request count. Drive a small detail request while a large export is running, then compare latency before and after moving export work out of the route callback. Add an approval replay test to document why abort is not rollback. Record the memory budget and timeout ownership at the proxy, HTTP server, and repository layers.",
        decision="Bound input and output, keep synchronous work short, and use abort only for work that is safe to cancel.",
        code='''import express from 'express';
import { permitRepository } from './services.js';

const app = express();
app.get('/api/permits', async (request, response) => {
  const rawLimit = Number(request.query.limit ?? 47);
  if (!Number.isSafeInteger(rawLimit) || rawLimit < 1 || rawLimit > 47) {
    return response.status(400).json({ message: 'Invalid page size' });
  }
  const controller = new AbortController();
  const deadline = setTimeout(() => controller.abort(), 8_100);
  response.on('close', () => {
    if (!response.writableEnded) controller.abort();
  });
  try {
    const page = await permitRepository.searchAuthorized({
      reviewerId: request.reviewer.id, limit: rawLimit, signal: controller.signal
    });
    if (!response.destroyed) response.json(page);
  } finally {
    clearTimeout(deadline);
  }
});''',
        checks=["Unbounded input is rejected before expensive work.", "Client disconnect cancels only the read work that supports it.", "A large task does not starve unrelated small requests."],
        mistakes=["Calling an async route nonblocking while it performs a large synchronous sort.", "Treating abort as rollback for a committed write.", "Leaving per-request timers active after completion."],
        related=["web-tech/request-deadlines-retries-and-backoff", "web-tech/database-capacity-and-online-change-operations"],
    ),
    dict(
        slug="node-http-drain-readiness-and-graceful-shutdown",
        title="Node HTTP Drain, Readiness, and Graceful Shutdown",
        summary="Stop admitting new work, finish bounded requests, and close resources under a shutdown deadline.",
        concept="A process shutdown is a protocol with the load balancer and active clients, not simply a call to process.exit. On a termination signal, a service should report that it is no longer ready, stop accepting new connections, allow in-flight requests a bounded interval to finish, and close database or queue resources. Node's HTTP server close behavior varies by version, especially around idle keep-alive connections, so the runtime version belongs in the deployment contract. Upgraded sockets and background jobs may need separate drains. A hard deadline exists because a request can hang forever, but force-closing it can interrupt a write after commit and before response. Idempotent operation replay makes that ambiguity recoverable.",
        case="A new permit API release starts while an old instance handles a 1.8-second approval. The old process exits immediately on SIGTERM. The database commits, the client sees a reset connection, and the reviewer retries with a new operation ID, creating a second notification. In another deployment, the process calls server.close but a long-lived upgraded socket keeps the instance alive beyond the platform deadline. The repair marks readiness false, waits for traffic removal, stops accepting new HTTP work, drains normal requests within a 29-second budget, and separately tracks upgraded sessions. The approval endpoint uses a stable operation ID so a lost response can be replayed safely.",
        implementation="Separate readiness from liveness. A draining process can be alive but should no longer receive new routed traffic. Coordinate the load balancer's observation delay with the application's admission gate; readiness changing alone does not instantly stop packets already in flight. Call server.close once, guard repeated signals, and set a bounded force-close timer that is shorter than the platform's kill deadline. Close database pools only after in-flight handlers finish or after the hard deadline is reached. Record active requests and upgraded connections; WebSocket sessions need their own close handshake and maximum wait. Treat a failure while closing a resource as a nonzero exit condition. Exercise the exact Node version and proxy behavior used in production.",
        cost="A longer drain window preserves more requests but keeps old capacity and connections alive during a rollout. A shorter window releases resources quickly yet increases ambiguous client failures. In-flight request tracking uses O(r) state for r active requests; long-lived sockets can dominate memory even after normal HTTP admission stops. A process that waits forever can stall deployment. The force-close timer can cut off an already committed write's response, so write endpoints need replay semantics. Measure requests completed during drain, forced closes, retry outcomes, time until load balancer removal, and the overlap capacity needed during deployment.",
        failure="Send SIGTERM during a slow authorized read and verify readiness changes before connection admission closes. The read may finish inside the budget. Send SIGTERM just after an approval commits but before its response; replay with the same operation ID and verify one logical write. Send SIGTERM twice and confirm shutdown begins only once. Hold an idle keep-alive connection and an upgraded socket; neither should make the process exceed its deadline without being tracked. Force repository close to fail and verify the exit status records failure. Run the drill behind the actual proxy because local server.close behavior alone cannot prove traffic has stopped.",
        drill="Create a readiness route and a drain controller around an HTTP server. Count active requests and record when readiness turns false, when the listener closes, and when the database pool closes. Use a 29-second maximum with an earlier alert threshold. Drive one 1.8-second read, one hanging read, and one approval whose response is lost after commit. Terminate during each case and compare client-visible outcomes. Add an upgraded connection and document its separate drain. Validate the behavior under the deployed Node runtime and proxy instead of assuming every server.close version handles idle sockets identically.",
        decision="Drain under a measured deadline, then close resources; make lost mutation responses recoverable through stable operation identity.",
        code='''import express from 'express';
import { permitRepository } from './services.js';

const app = express();
let ready = true;
let draining = false;
app.get('/ready', (request, response) => response.sendStatus(ready ? 200 : 503));
const server = app.listen(4_781);

function beginDrain() {
  if (draining) return;
  draining = true;
  ready = false;
  const deadline = setTimeout(() => server.closeAllConnections(), 29_000);
  deadline.unref();
  server.close(async error => {
    clearTimeout(deadline);
    if (error) process.exitCode = 1;
    try { await permitRepository.close(); }
    catch { process.exitCode = 1; }
  });
}
process.on('SIGTERM', beginDrain);''',
        checks=["Readiness changes before new work is admitted during drain.", "Normal requests finish or are force-closed within the deadline.", "Repository resources close and lost writes can be replayed safely."],
        mistakes=["Calling process.exit immediately after SIGTERM.", "Assuming HTTP close drains upgraded sockets or all Node versions identically.", "Closing the database before in-flight handlers complete."],
        related=["web-tech/production-signals-and-incident-decisions", "web-tech/realtime-connection-and-event-delivery"],
    ),
]

assert hub_path not in by_path and len(topics) == 4
hub = copy.deepcopy(by_path["web-tech/production-signals-and-incident-decisions"])
hub.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + hub_path)), path=hub_path, title=hub_title,
           summary="Build Express 5 APIs with ordered trust checks, honest errors, bounded request work, and drain behavior.",
           sort_order=3700, created_at=stamp, updated_at=stamp, published_at=stamp)
hub["data"] = {"subject_root": "web-tech/web-technology", "section_path": hub_path, "content_format": "html",
               "seo_ready": False, "modules": [], "resource_tabs": [
                   {"title": "Web Development", "path": "web-tech/web-technology"},
                   {"title": "Projects", "path": "web-tech/web-technology/project"},
                   {"title": "Quizzes", "path": "web-tech/quizzes"}]}
entries.append(hub)
by_path[hub_path] = hub

for number, topic in enumerate(topics):
    path = "web-tech/" + topic["slug"]
    assert path not in by_path
    subprocess.run(["node", "--check", "--input-type=module"], input=topic["code"],
                   text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path["web-tech/trace-context-across-request-and-job"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                 title=topic["title"], summary=topic["summary"], sort_order=3701 + number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    related = [hub_path] + ["web-tech/" + other["slug"] for other in topics if other is not topic] + topic["related"]
    body = paragraph(topic["concept"]) + "<h2>Working case</h2>" + paragraph(topic["case"])
    body += '<h2>Implementation boundary</h2><pre><code class="language-javascript">' + html.escape(topic["code"], quote=False) + "</code></pre>" + paragraph(topic["implementation"])
    body += "<h2>Cost and boundaries</h2>" + paragraph(topic["cost"]) + "<h2>Failure trace</h2>" + paragraph(topic["failure"])
    body += "<h2>Verification</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in topic["checks"]) + "</ul>"
    body += "<h2>Practice drill</h2>" + paragraph(topic["drill"]) + "<h2>Decision note</h2>" + paragraph(topic["decision"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in topic["mistakes"]) + "</ul>"
    entry["body"] = body
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": hub_path,
                     "content_format": "html", "seo_ready": False, "kind": "tutorial",
                     "author_path": "authors/aitrove-editorial", "reading_minutes": 8, "related": related}
    entries.append(entry)
    by_path[path] = entry

for topic in topics:
    entry = by_path["web-tech/" + topic["slug"]]
    entry["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in entry["data"]["related"]) + ".</p>"
hub["data"]["modules"] = [{"title": hub_title, "summary": hub["summary"],
                           "lessons": ["web-tech/" + topic["slug"] for topic in topics]}]
hub["body"] = paragraph("An Express permit service accepts requests through an ordered middleware stack, resolves async results, spends bounded event-loop and database work, and eventually drains during deployment. These lessons trace each boundary using the same case API so a passing local route cannot hide a wrong identity, duplicate response, blocked loop, or lost committed write.")
hub["body"] += "<h2>Topics in this track</h2><ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
hub["body"] += "<h2>Prerequisite paths</h2><p>" + "; ".join(link(path) for path in ["web-tech/backend-api-systems", "web-tech/request-deadlines-retries-and-backoff", "web-tech/ingress-proxy-and-upstream-contracts"]) + ".</p>"
curriculum = by_path["web-tech/web-technology"]
curriculum["data"]["modules"].append({"title": hub_title, "summary": hub["summary"],
                                       "lessons": [hub_path] + ["web-tech/" + topic["slug"] for topic in topics]})
curriculum["body"] += "<h2>" + link(hub_path) + "</h2>" + paragraph(hub["summary"]) + "<ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
curriculum["updated_at"] = stamp
crosslinks = {
    "web-tech/backend-api-systems": [hub_path],
    "web-tech/authorization-and-tenant-boundaries": ["web-tech/express-middleware-order-and-request-identity"],
    "web-tech/api-mutation-and-failure-contracts": ["web-tech/express-five-async-errors-and-response-contracts"],
    "web-tech/request-deadlines-retries-and-backoff": ["web-tech/node-request-budgets-abort-and-event-loop-fairness"],
    "web-tech/ingress-proxy-and-upstream-contracts": ["web-tech/node-http-drain-readiness-and-graceful-shutdown"],
}
for path, targets in crosslinks.items():
    by_path[path]["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    by_path[path]["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": 1, "new_lessons": 4,
                  "prose_words": {topic["slug"]: len(re.findall(r"\b[\w'-]+\b", " ".join(str(topic[key]) for key in ("concept", "case", "implementation", "cost", "failure", "drill", "decision", "summary")))) for topic in topics}}))
