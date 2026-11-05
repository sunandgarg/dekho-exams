"""Add service-traffic failure contracts to the local DevOps preview."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
course = "devops/devops-tutorial"
project_hub = course + "/project"
quiz_hub = "devops/quizzes"
specs = []


def lesson(slug, title, summary, definition, operation, language, sample, cost, mistakes, related):
    path = "devops/" + slug
    assert path not in by_path, path
    specs.append(dict(path=path, title=title, summary=summary, definition=definition,
                      operation=operation, language=language, sample=sample,
                      cost=cost, mistakes=mistakes, related=related))


lesson(
    "grpc-deadline-propagation", "gRPC deadlines: spend one request budget across every downstream call",
    "Pass the caller's cancellation context through the service chain.",
    "A gRPC deadline marks the point after which the caller no longer wants a result. Without an explicit deadline, a call can wait much longer than the user request permits. A server that calls another service must pass along the remaining budget and stop work when its context is cancelled; otherwise a timed-out request can continue consuming workers, database connections, and retry capacity. The exact propagation behavior depends on the language implementation, so the application must test it.",
    "A receipt endpoint has a 430-millisecond budget for a ledger lookup. The Go function below derives a shorter context from its parent, so an earlier caller deadline still wins. The service's actual gRPC method should receive lookupContext and pass it to any further RPC instead of creating context.Background. Make the ledger response take 600 milliseconds in a test and verify that the client sees a deadline error, the server cancels its query, and no retry continues after cancellation. Then use a fast ledger response and measure how much time remains for serialization and the return trip. Count deadline expirations separately from server errors. A cancellation signal does not roll back a side effect that has already committed; pair retry policy with an idempotency rule for mutating methods.",
    "go", """package main

import (
    "context"
    "time"
)

func fetchReceiptWithinBudget(
    parentContext context.Context,
    ledgerLookup func(context.Context) (string, error),
) (string, error) {
    lookupContext, cancelLookup := context.WithTimeout(parentContext, 430*time.Millisecond)
    defer cancelLookup()
    return ledgerLookup(lookupContext)
}""",
    "A shorter deadline frees resources earlier but raises false timeouts during normal tail latency. A longer one ties up workers and may allow retries to outlive the user request. Measure the percentile of successful calls, network transit, queue time, and cancellation lag before choosing a budget. The function adds only a timer and context object per call; the material cost comes from operations that ignore cancellation. Prove cancellation reaches the database or worker rather than counting client errors alone.",
    ["Do not replace the incoming context with a new background context.", "Do not retry a mutation after its deadline without an idempotency check.", "Do not assume a cancelled RPC reverses a committed external effect."],
    ["devops/retry-timeout-budgets", "devops/retry-amplification-control", "devops/queue-consumer-reliability", "devops/http-idempotency-replay"],
)

lesson(
    "http2-goaway-drain", "HTTP/2 drain: let existing streams finish while new calls move away",
    "Coordinate readiness, graceful shutdown, and the hard termination window.",
    "An HTTP/2 connection can carry many concurrent streams. Removing a server from new routing does not instantly remove streams already accepted on that connection. During graceful shutdown the server must stop accepting new work, signal connected clients to move new streams elsewhere, and allow in-flight work to finish within a bounded period. A forceful close after the grace period can still fail long-running requests, so the shutdown window must reflect actual request durations and client retry behavior.",
    "A receipt API runs Go's standard HTTP server with HTTP/2 enabled on its TLS listener. First mark the instance unready and wait for upstream route removal. Then call Server.Shutdown with a bounded context; the Go fragment performs that application-side step, while the deployment must allow enough termination time for it to finish. Start several concurrent requests on one HTTP/2 connection, terminate the instance, and check that accepted requests complete while new requests move to other replicas. Repeat with a request longer than the shutdown budget and record its failure and retry outcome. Confirm the server process waits for Shutdown to return before exiting. Hijacked or upgraded connections need their own close path; the standard shutdown method does not wait for them. Inspect client connection reuse and error rates during the rollout, not only Pod readiness.",
    "go", """package main

import (
    "context"
    "net/http"
    "time"
)

func stopReceiptServer(receiptServer *http.Server) error {
    shutdownContext, cancelShutdown := context.WithTimeout(context.Background(), 9*time.Second)
    defer cancelShutdown()
    return receiptServer.Shutdown(shutdownContext)
}""",
    "A nine-second grace window is an example, not a universal setting. Longer windows preserve slow requests but keep old replicas consuming capacity during a rollout; shorter windows cut them off. Compare the longest accepted request and the load balancer's route-removal time with the orchestrator's termination allowance. The shutdown call is cheap; the occupied connections and overlap replicas are the real costs. A zero error count on the server can conceal a client-side reset, so verify from both ends.",
    ["Do not equate readiness failure with closure of existing HTTP/2 streams.", "Do not exit the process while graceful shutdown is still waiting.", "Do not assume upgraded or hijacked connections are covered by Server.Shutdown."],
    ["devops/connection-drain-boundary", "devops/graceful-pod-shutdown", "devops/gateway-api-routing", "devops/grpc-deadline-propagation"],
)

lesson(
    "load-balancer-health-semantics", "Load-balancer health: a green socket is not a working transaction",
    "Separate process liveness, routing readiness, and the user's completed request.",
    "A load-balancer health check decides whether one backend receives new traffic. A TCP connect proves less than an HTTP response; an HTTP response from a sidecar can still succeed when the application is broken. Readiness may deliberately fail during startup or drain. A synthetic transaction travels through more of the real route, but it is too expensive or effectful to run at every per-instance health-check interval.",
    "A checkout gateway returns a healthy TCP handshake while its receipt handler cannot reach the ledger. The load balancer continues routing because its check touches only the listener. Define a cheap per-instance readiness endpoint that confirms the process can accept a request and has its required local configuration; reserve end-to-end settlement checks for a lower-frequency synthetic monitor with disposable data. Inspect which host and path the load balancer probes, its interval and failure threshold, and whether it uses the same TLS and routing chain as clients. During a test, break the application handler while leaving the listener alive, then confirm the readiness decision changes within the planned withdrawal time and a synthetic request reports the user failure. Restore the dependency and verify successful checks are required before reentry. Avoid coupling every instance's readiness to a shared database outage if that would remove all capacity and prevent controlled recovery.",
    "bash", "kubectl -n checkout get endpointslice -l kubernetes.io/service-name=receipt-api -o wide\nkubectl -n checkout get pods -l app=receipt-api -o wide",
    "Deeper checks catch more faults but can load shared dependencies and create a correlated outage. A high failure threshold delays withdrawal; a low one can flap under brief network loss. Compare observed withdrawal and reentry times with request error rates, route membership, and the independent synthetic result. The two commands show Kubernetes service endpoints and Pods, but they do not reveal the external load balancer's health decision; collect that separately from the configured controller.",
    ["Do not treat a successful TCP connect as proof that the business route works.", "Do not turn an effectful payment request into a frequent backend health probe.", "Do not assume a Pod's Ready condition exactly matches an external load balancer's target state."],
    ["devops/kubernetes-probes", "devops/synthetic-transaction-monitoring", "devops/gateway-api-routing", "devops/connection-drain-boundary"],
)

lesson(
    "connection-pool-endpoint-churn", "Client connection pools: retire old endpoints after a DNS or rollout change",
    "Measure active sockets, resolved addresses, and retry behavior as separate state.",
    "DNS controls future address resolution, not every connection already held by a client pool. Long-lived HTTP/2 channels may continue sending streams to an old endpoint until the channel drains, fails, or is deliberately rotated. A proxy can also retain upstream connections while service discovery changes. A rollout can therefore serve mixed backend versions even after DNS and target lists look correct.",
    "A claims API moves from one internal gateway to another. Before the cutover, record the client resolver result, active connections by peer address, connection age, request version header, and in-flight work. Change the destination in an isolated environment and watch both address resolution and existing sockets. Ask the old endpoint to drain; new streams should use the replacement while accepted work finishes. If a client keeps a channel indefinitely, apply a bounded connection lifetime or an explicit pool rotation supported by its library, then test it under load. Do not restart every client blindly: a simultaneous reconnect storm can overwhelm DNS, TLS termination, and the new gateway. Track retries by operation ID so a request that was accepted before disconnect is reconciled before repetition. Confirm that the last old-version response disappears within the cutover contract, not merely that the latest lookup returns the new address.",
    "text", "Claims endpoint cutover evidence\nResolver answers: old and new addresses over time\nLive sockets: peer address, age, in-flight count\nOld endpoint: drain signalled and last stream completed\nNew endpoint: handshake and request success under load\nClient pool: rotation rule and reconnect rate bounded\nAcceptance: no unexplained old-version responses or duplicate effects",
    "Short connection lifetimes speed convergence but increase handshakes, CPU, and latency. Long lifetimes conserve work but lengthen a mixed-version window. A synchronized restart can make the new endpoint fail despite enough steady-state capacity. Measure churn, TLS handshakes, DNS queries, active streams, and business retries while shifting traffic. Tune the client library and proxy separately because each may keep its own pool.",
    ["Do not assume a short DNS TTL closes an established socket.", "Do not repeat an ambiguous write solely because the old connection reset.", "Do not rotate every client pool at once without a reconnect budget."],
    ["devops/dns-cutover-safety", "devops/connection-drain-boundary", "devops/nat-port-allocation-pressure", "devops/http-idempotency-replay"],
)

lesson(
    "http-idempotency-replay", "Idempotency keys: reconcile an accepted write before repeating it",
    "Bind one client operation to one payload and one durable result.",
    "An idempotency key lets a server recognize a repeated mutating request after the client loses its response. The key must be scoped to the caller or operation, tied to a canonical payload identity, and stored atomically with the resulting business effect. A repeated key with different input is an error. A key record that expires too early can permit a late retry to create a second effect, while a cached failure may still need a precise policy for whether the client may start a new operation.",
    "A payout client sends a settlement request and loses the response after the ledger commits. It retries with the same account-scoped operation key and the same request fingerprint. The service must return the durable prior result or the current in-progress state without creating another payout. It must reject a retry that reuses that key for a different amount. Crash the service immediately after the ledger commit but before replying, then verify the key and payout are recoverable together; if they live in separate stores, a transaction or reconciliation protocol must close the gap. Test concurrent requests carrying the same key so one owns the effect and the other waits or receives a defined conflict. Record the key retention period against maximum client retry age, broker delay, and audit needs. Include an operation ID in the response and logs, but keep raw account details out of telemetry.",
    "text", "Payout idempotency contract\nScope: merchant account plus client operation key\nFingerprint: canonical amount, currency, destination, operation type\nAtomic record: key, fingerprint, payout ID, state, durable response\nSame key and fingerprint: return prior result or defined in-progress state\nSame key and different fingerprint: reject without side effect\nExpiry: later than every supported retry and replay window",
    "Key records consume indexed storage and add contention for concurrent retries. A key held forever may outlive its useful audit period; a short retention window permits duplicate effects from late clients. The lookup is normally indexed, but lock waits and result serialization can dominate latency during a retry storm. Measure duplicate requests suppressed, mismatched-key errors, unresolved in-progress states, and payout count for each operation ID. Idempotency protects one defined operation; it does not make an entire multi-system workflow exactly once.",
    ["Do not store the key after the payout has already committed in a separate uncoordinated step.", "Do not treat the same key with a changed amount as a harmless retry.", "Do not promise safe replay after the key has been pruned."],
    ["devops/retry-amplification-control", "devops/transactional-outbox-delivery", "devops/ambiguous-cloud-create-reconcile", "devops/grpc-deadline-propagation"],
)

lesson(
    "shadow-traffic-side-effects", "Shadow traffic: test a new backend without duplicating live side effects",
    "Mirror only requests whose downstream effects are contained.",
    "A proxy can send a copy of a production request to a shadow backend while returning the primary backend's response to the client. The shadow response is not a rollback mechanism, and the mirrored request can still mutate databases, publish events, spend money, or send messages. A safe shadow environment needs separate credentials and destinations, write blocking or disposable data, and an explicit privacy boundary for copied payloads.",
    "A receipt read API is being replaced. Mirror a bounded fraction of read requests to an isolated candidate with a sanitized data snapshot. The route fragment shows the intent; it is not a complete proxy configuration. Confirm the mirror cluster exists and receives traffic, then compare status, selected response fields, latency, and errors by request ID without returning candidate output to users. Do not mirror settlement POST requests until their entire effect graph is replaced by test sinks or rejected at the candidate edge. Test a request containing a synthetic customer marker and verify it appears only in approved shadow storage. Limit shadow rate independently from primary traffic so a slow candidate does not exhaust shared egress or backend capacity. A primary request can succeed even if the shadow request fails; monitor the candidate separately. Stop the mirror if isolation, redaction, or cost gates fail.",
    "yaml", "route:\n  cluster: receipt-primary\n  request_mirror_policies:\n    - cluster: receipt-shadow",
    "Mirroring spends extra network, CPU, storage, and possibly third-party quota while providing no direct user response benefit. Sampling a small fraction reduces cost but may miss rare request shapes. A slow shadow path should not delay primary responses, but it can still compete for shared infrastructure and logging capacity. Measure primary latency before and after enabling the mirror, candidate comparison coverage, and every unexpected shadow write. Treat a successful comparison as rollout evidence, not proof that all mutating routes are safe.",
    ["Do not mirror production writes into a candidate connected to real payment or email systems.", "Do not assume the client can see or validate the shadow response.", "Do not let untrusted request headers choose an arbitrary shadow destination."],
    ["devops/progressive-delivery", "devops/canary-cohort-analysis", "devops/telemetry-sensitive-data-boundary", "devops/http-idempotency-replay"],
)

lesson(
    "versioned-edge-asset-cache", "Versioned edge assets: make long cache lifetimes safe through content identity",
    "Separate immutable assets from the short-lived document that names them.",
    "A cache can hold a static asset for a long time safely when the asset's path changes whenever its bytes change. A content-derived filename gives that identity; overwriting bytes at the same path breaks the contract. The HTML document that selects an asset version needs a much shorter freshness policy so a rollout and rollback can switch references. A purge is an operational fallback, not a replacement for correct naming.",
    "A receipt portal publishes a new JavaScript bundle. Produce a filename that includes a content digest, upload that exact object to the edge, verify its bytes and content type, then deploy the document that references it. The policy fragment distinguishes the two response classes. Keep the old digest object through the rollback window, since clients holding the previous document will still request it. Roll back by serving the previous document reference rather than replacing bytes under the new filename. Test from two edge locations and a browser profile with an old document: both asset versions should remain fetchable. If the document is cached longer than planned, users may run old code against a new API, so maintain an API compatibility window. Track missing-asset responses and document age during rollout.",
    "text", "Versioned receipt bundle: public, max-age=31536000, immutable\nReceipt document: no-cache\nRelease order: upload and verify bundle, then change document reference\nRollback: restore prior document reference; retain prior bundle",
    "Long-lived immutable assets improve cache hit rate and lower origin load, but keeping old versions costs storage. Short-lived documents create revalidation traffic and can raise origin pressure during a large launch. A purge may propagate at different speeds across edge locations. Measure cache hit ratio, old-document prevalence, missing digest objects, and compatibility failures. The digest path is a release dependency, so promotion evidence should include it alongside the application image.",
    ["Do not overwrite a content-named asset after publication.", "Do not delete the prior bundle before old documents and rollback paths expire.", "Do not set a long immutable policy on the document that chooses the bundle."],
    ["devops/artifact-promotion", "devops/api-compatibility-window", "devops/rollback-image-retention", "devops/cache-stampede-control"],
)

lesson(
    "edge-cache-privacy-fallback", "Edge cache fallback: serve stale public data without leaking private responses",
    "Set different failure policies for catalog data and account-specific state.",
    "A shared edge cache can reuse a public response during a brief origin failure when a bounded stale-if-error policy permits it. That buys availability at the price of older data. A personalized account or payout response has a different boundary: it must not be served to another user and may need no storage at all. Cache policy, key construction, authorization, and invalidation must agree; a single generic rule across every route is unsafe.",
    "A public support catalog changes a few times daily, while payout status is account-specific and can change after a settlement. Give the catalog a short fresh lifetime and a bounded stale-on-origin-error period, with a response marker that lets operators see when stale content was served. Give payout status a no-store policy and confirm the edge does not cache it even when the origin emits a 503. The fragment states two separate header contracts. In an isolated test, warm the catalog, stop the origin, and verify the catalog remains available only within the allowed stale period. Repeat with two test accounts and prove that one account never receives the other's payout body, whether the origin is healthy or down. Confirm purge and revalidation behavior for an incorrect catalog entry; serving stale public data is unacceptable if the entry is a revoked safety notice. Measure stale response age and user impact rather than counting cache hits as success.",
    "text", "Public support catalog: Cache-Control: public, max-age=45, stale-if-error=180\nAccount payout status: Cache-Control: no-store\nEdge test: origin failure serves only bounded stale catalog data\nPrivacy test: account A never receives account B response\nCorrection gate: revoked catalog item bypasses stale fallback",
    "A longer stale window lowers origin-outage errors but raises the chance of showing obsolete content. Disabling storage on private responses raises origin traffic, which must be included in capacity planning. Cache-key variants can multiply storage and still fail privacy review if an identity field is omitted. Inspect actual edge response headers, cache status, body identity, and age during fault injection; origin configuration alone is insufficient.",
    ["Do not use public cache directives for personalized payout status.", "Do not treat stale catalog delivery as valid after a safety-critical correction.", "Do not trust origin headers without verifying the edge's effective cache behavior."],
    ["devops/dns-tls-edge", "devops/cache-stampede-control", "devops/edge-rate-limit-fairness", "devops/synthetic-transaction-monitoring"],
)

titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/service-traffic-contract-project"
quiz_path = "quizzes/devops-service-traffic-decisions"
titles[project_path] = "Project: release a service through connection and cache failures"
titles[quiz_path] = "DevOps service traffic decisions"
for item in specs:
    assert all(path in titles for path in item["related"]), item["path"]


def links(paths):
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in paths
    ) + "</ul>"


for heading, summary, slugs in [
    ("Request and connection lifetime", "Carry one deadline across calls and drain multiplexed connections.", ["grpc-deadline-propagation", "http2-goaway-drain"]),
    ("Routing truth during change", "Compare health decisions with user requests and retire stale client pools.", ["load-balancer-health-semantics", "connection-pool-endpoint-churn"]),
    ("Safe traffic duplication", "Reconcile ambiguous writes and contain mirrored requests.", ["http-idempotency-replay", "shadow-traffic-side-effects"]),
    ("Edge freshness and privacy", "Pin immutable asset bytes and bound stale public responses.", ["versioned-edge-asset-cache", "edge-cache-privacy-fallback"]),
]:
    paths = ["devops/" + slug for slug in slugs]
    by_path[course]["data"]["modules"].append({"title": heading, "summary": summary, "lessons": paths})
    by_path[course]["body"] += f"<h2>{html.escape(heading)}</h2><p>{html.escape(summary)}</p>" + links(paths)
by_path[course]["updated_at"] = stamp

for index, item in enumerate(specs):
    path = item["path"]
    row = copy.deepcopy(by_path["devops/continuous-integration"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
               title=item["title"], summary=item["summary"], subject="devops",
               category="DevOps", difficulty="Advanced", tags=["devops", "operations"],
               sort_order=20200 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"kind": "tutorial", "reading_minutes": 6,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": course, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in item["related"]]}
    row["body"] = (
        f"<p>{html.escape(item['definition'])}</p><h2>Operational decision</h2>"
        f"<p>{html.escape(item['operation'])}</p>"
        f'<pre><code class="language-{item["language"]}">{html.escape(item["sample"])}</code></pre>'
        f"<h2>Cost and verification</h2><p>{html.escape(item['cost'])}</p>"
        + "<h3>Common Mistakes</h3><ul>"
        + "".join(f"<li>{html.escape(mistake)}</li>" for mistake in item["mistakes"])
        + "</ul><h2>Connected lessons</h2>" + links([course, *item["related"]])
    )
    rows.append(row)

project_related = [item["path"] for item in specs]
project = copy.deepcopy(by_path["devops/practice-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)),
               path=project_path, title=titles[project_path],
               summary="Test deadlines, draining, health checks, idempotency, mirroring, and edge cache policy.",
               difficulty="Advanced", sort_order=20290,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 9,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in project_related]}
project["body"] = (
    "<p>Use an isolated receipt API, a ledger stub that can delay or commit requests, two application replicas, a test load balancer, and an edge cache with separate public and account-specific routes. Issue synthetic requests with stable operation IDs. Before faults, record the deadline budget, active HTTP/2 streams, health-check target state, client peer addresses, payout count, mirror destinations, and effective response cache headers. Do not connect the shadow path to real payment, email, or account services.</p>"
    "<h2>Interrupt traffic safely</h2><p>Delay the ledger beyond a 430-millisecond receipt lookup budget and prove cancellation reaches the downstream call. Start concurrent HTTP/2 requests, mark one replica unready, and ask it to shut down gracefully; measure completed accepted streams, rejected new streams, and the hard termination boundary. Break the receipt handler while leaving the socket open and compare load-balancer target health with a synthetic user request. Change a gateway address, then record when the resolver, client connection pool, and last old-version response each converge. Pace pool rotation to avoid a synchronized reconnect surge.</p>"
    "<pre><code class=\"language-text\">Service traffic acceptance gates\nDeadline: downstream call stops after parent budget expires\nDrain: accepted streams complete or fail within recorded grace window\nHealth: application fault withdraws target; synthetic path reports impact\nCutover: no unexplained old-version responses after pool rotation\nRetry: one payout per operation ID after lost response\nMirror: no real side effect or private payload escape\nAssets: both current and rollback digest objects remain fetchable\nCache: stale public catalog bounded; private payout never shared</code></pre>"
    "<h2>Replay and cache with evidence</h2><p>Commit a synthetic payout, discard its client response, and retry with the same operation key; verify one ledger effect and the same durable result. Reuse that key with a changed amount and require rejection. Mirror a fraction of receipt reads to a test-only backend, then inspect its storage and outbound connections for side effects. Publish a digest-named bundle before switching the document reference, keep the old bundle through rollback, and verify both from separate edge locations. Stop the public catalog origin and test bounded stale delivery; repeat with two private test accounts to prove payout responses never cross identities or appear in a shared cache.</p>"
    "<h2>Cost and verification</h2><p>Record extra overlap replicas, handshake rate, shadow egress, idempotency record growth, old-bundle storage, and origin load from uncached private requests. The drill passes only when a lost response does not duplicate a payout, the old endpoint stops serving after the agreed window, and the effective edge policy matches the route's data sensitivity. A green listener, a successful DNS lookup, and an unchanged cache-hit ratio are not substitutes for these checks.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not equate target readiness with drained HTTP/2 streams.</li><li>Do not retry a committed payment without a durable operation key.</li><li>Do not mirror writes into real downstream systems.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*project_related, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Service traffic contract drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("What should a downstream gRPC call receive from its caller?", ["The remaining cancellation budget", "A new unlimited background context", "Only the caller's retry count"], "The downstream work must end within the original request budget."),
    ("What does an expired client deadline fail to undo?", ["A business side effect that already committed", "The returned deadline error", "The client's wait timer"], "Cancellation stops future work when honored; it does not reverse a committed effect."),
    ("What remains after a replica is marked unready?", ["Already accepted streams may still be active", "Every client socket closes instantly", "All retries become safe"], "Readiness removes new routing but does not finish work on existing connections."),
    ("What must the process do after calling graceful Server.Shutdown?", ["Wait for the call to finish or its context to expire", "Exit immediately", "Ignore upgraded connections forever"], "Exiting early can interrupt requests the shutdown was meant to preserve."),
    ("Why can a load balancer report healthy while checkout fails?", ["Its check may touch only a socket or unrelated endpoint", "Every health check is a full payment", "A DNS TTL cancels the handler"], "Probe depth determines which failures it can detect."),
    ("Why may old backends serve requests after DNS changes?", ["Clients and proxies may retain established connections", "DNS changes rewrite active sockets", "All HTTP/2 streams resolve each frame"], "Resolution applies to new connection decisions, not every live stream."),
    ("What should a repeated payout operation key produce?", ["The prior durable result without a new payout", "A second payout with a new ID", "A changed amount accepted silently"], "The key binds one payload to one effect."),
    ("How should the service treat the same key with a different amount?", ["Reject it without a side effect", "Treat it as a normal retry", "Delete the original ledger row"], "A changed payload is not the same operation."),
    ("Why is a shadow request unsafe by default for settlement?", ["Its backend can still write or send messages", "The user always receives its response", "It cannot leave the proxy"], "Mirroring duplicates request execution even if the response is ignored."),
    ("Why name a long-cached asset with its content digest?", ["Changed bytes get a new path", "It removes all storage costs", "It makes the HTML document immutable"], "A new path avoids stale bytes under an old identity."),
    ("What should happen to the previous bundle during rollback?", ["Keep it fetchable while old documents may reference it", "Delete it before publishing the new document", "Overwrite it with the new bytes"], "Clients holding old documents still need the exact old asset."),
    ("Which cache policy fits account-specific payout status?", ["No shared storage of the response", "Public stale reuse across accounts", "One cache key for every user"], "A shared cached payout body can expose another account's data."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on request budgets, draining, retries, mirroring, and cache privacy.",
            sort_order=20300, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in project_related],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Choose the boundary that keeps an accepted request, a retry, and a cached response tied to the intended user operation. Observe the result through the client route, not only the backend process.</p>"
    "<h2>Review these lessons</h2>" + links(project_related)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-observability-pipeline-decisions", "quizzes/devops-data-continuity-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not repeat an ambiguous payment with a new key.</li><li>Do not place account-specific responses in a shared cache.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Service traffic check</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": path, "title": titles[path]} for path in [project_path, quiz_path])

for source, targets in {
    "devops/retry-timeout-budgets": ["devops/grpc-deadline-propagation"],
    "devops/connection-drain-boundary": ["devops/http2-goaway-drain", "devops/connection-pool-endpoint-churn"],
    "devops/kubernetes-probes": ["devops/load-balancer-health-semantics"],
    "devops/transactional-outbox-delivery": ["devops/http-idempotency-replay"],
    "devops/progressive-delivery": ["devops/shadow-traffic-side-effects"],
    "devops/artifact-promotion": ["devops/versioned-edge-asset-cache"],
    "devops/dns-tls-edge": ["devops/edge-cache-privacy-fallback"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Advanced follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1, "total_records": len(rows)}))
