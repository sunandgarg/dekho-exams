"""Add ingress and reverse-proxy lessons to the Web Development drafts."""
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
    return '<a href="/' + html.escape(path, quote=True) + '">' + html.escape(by_path[path]["title"]) + "</a>"


hub_path = "web-tech/ingress-proxy-and-upstream-contracts"
hub_title = "Ingress Proxy and Upstream Contracts"
topics = [
    dict(
        slug="trusted-proxy-hops-and-forwarded-client-identity",
        title="Trusted Proxy Hops and Forwarded Client Identity",
        summary="Accept client address and scheme metadata only from an authenticated, known proxy path.",
        concept="A reverse proxy receives a client request and forwards a new request to an application origin. The origin's socket peer is normally the proxy, not the browser. Headers that describe an earlier client address, host, or scheme are claims; a direct caller can send similar text unless the edge replaces those fields and the origin accepts traffic only from trusted peers. A trust policy therefore starts with the network or authenticated channel between ingress and origin, then defines which hop may set each field. The application must not select the first arbitrary address in a forwarded chain as proof of identity. Address data also does not replace a session or permission check; it is primarily useful for abuse controls, regional rules, and diagnostics.",
        case="A permit portal runs behind two proxies. The public edge terminates TLS and forwards through an internal router to the app. Reviewer 47's request arrives with an address chain containing a client address and two proxy addresses. An attacker sends a direct request to a mistakenly exposed origin with a forged forwarded address that appears to be an office network. A rate limiter and a diagnostic view accept the forged value, while a redirect uses the attacker-supplied scheme. The corrected deployment blocks direct origin access, strips untrusted forwarded fields at the public edge, records the known hop chain, and derives the trusted client address only after verifying the immediate peer.",
        implementation="Document each allowed ingress path, including backup edges and health probes. Restrict origin reachability to those peers through network policy or an authenticated connection; a mere header saying edge is not authentication. At the first trusted boundary, remove client-supplied forwarding fields and write a controlled canonical representation. At later hops, append only according to a documented policy. Configure the application to trust the exact peer set and parse the chain from the trusted end, stopping at the first untrusted hop. Reject ambiguous or malformed address data rather than silently treating it as a safe office address. Use a separate verified scheme and host from ingress for secure redirects and cookie decisions. Keep user authorization on server-owned identity, not IP alone. Test direct origin access and a forged multi-hop header.",
        cost="Forwarding validation adds a small parse per request, but accurate address attribution depends on keeping the trusted peer inventory current. A broad trust range makes attacks easier; a narrow range can break a new proxy rollout until updated. Logging every address hop can increase sensitive-data retention, so record only what incident response requires. Failed parsing should not promote a claimed address into a trusted one. Measure direct-origin attempts, rejected forwarding chains, address-parse failures, and differences between edge and origin scheme or host. If a rate limit groups by client address, verify its behavior under address-sharing networks and privacy relays, where many legitimate users may appear behind one address.",
        failure="Send a direct request to the origin with a forged forwarded address and verify the network or authentication boundary rejects it. Send through the public edge with an attacker-controlled forwarding header and confirm the edge overwrites it. Add an unexpected third proxy and ensure the app does not trust every chain element by default. Misconfigure the scheme header to HTTP while the browser used HTTPS; redirects and secure cookies should fail a staging check. Rotate a proxy address without updating the allowlist and observe a controlled availability failure rather than silent trust of all origins. Check that a forged address never grants case access.",
        drill="Map the request path from reviewer 47 through edge 29 and router 62 to an application instance. Record which component sets the canonical address, scheme, and host. Inject a forged first address, a direct-origin request, and one missing hop. Define the expected rate-limit key and redirect scheme for each. Keep a separate reviewer session test so the address value cannot act as authorization. Audit logs for enough information to diagnose a rejected chain without copying full private headers into every trace.",
        decision="Only a known proxy path may supply client metadata; an address claim is never a user permission.",
        code='function trustedClientAddress(socketPeer, canonicalAddressFromEdge, trustedPeers) {\n'
             '  if (!trustedPeers.has(socketPeer)) return null;\n'
             '  return canonicalAddressFromEdge || null;\n'
             '}\n'
             'console.log(trustedClientAddress("direct-visitor", "office-47", new Set(["edge-29"])));\n'
             '// Output: null',
        checks=["Direct origin traffic cannot inject trusted forwarding metadata.", "Every hop has an explicit owner for address, scheme, and host fields.", "User permission remains session- and object-based."],
        mistakes=["Trusting any forwarded header merely because it exists.", "Accepting an unrestricted proxy address range.", "Using a client IP value as proof of account identity."],
        related=["web-tech/edge-request-normalization-and-origin-trust", "web-tech/rate-limits-and-request-budgets"],
    ),
    dict(
        slug="host-authority-routing-and-default-deny",
        title="Host Authority Routing and Default Deny",
        summary="Bind hostnames, TLS names, and application routes without sending unknown authorities to a privileged default.",
        concept="An ingress routes a request partly by its target authority: the hostname and optional port that identify the requested service. TLS may select a certificate using a name offered during the handshake, while HTTP carries the target host or authority in the request. These names can disagree, and a proxy chain can rewrite them. A default virtual host that sends every unknown name to the application can expose pages through unintended domains, poison generated links, or bypass cookie assumptions. Routing should allow the names the product owns, preserve the intended tenant or service mapping, and reject unrecognized authorities before application code builds absolute redirects or account links.",
        case="The permit portal serves a public guide and a private reviewer app from the same ingress. An old test hostname still resolves to the ingress, and a request with that host lands on the private app because the default route points there. A password reset handler builds an absolute link from the request host. The recipient receives a link under an attacker-controlled name even though the account record is valid. The corrected ingress has an explicit host allowlist and a safe default rejection. Application-generated account links use a configured canonical origin, while the router passes a server-approved host identity to the app for tenant-aware pages.",
        implementation="Inventory production, staging, legacy, and customer-owned hostnames. For each, define the certificate coverage, ingress route, backend target, cookie domain, canonical redirect, and whether absolute links may be generated. Reject unknown hosts at the first routing layer instead of letting a privileged service become the default. If HTTP host and TLS name differ, decide whether that pair is permitted before forwarding. Normalize host case and a permitted port representation while rejecting malformed or duplicate authority signals. A proxy should not pass an arbitrary browser Host through to origin code as a trusted canonical base URL. For tenant custom domains, resolve a verified domain-to-tenant mapping on the server and plan revocation. Test all expected names and an unknown name through every region.",
        cost="A host allowlist adds operational work for new domains and migrations. The cost is small at request time for a bounded lookup, but mistakes can cause outages during cutover if DNS, certificates, and route tables change at different times. A permissive default seems easier during setup and can silently serve sensitive pages on old or attacker-controlled names. Tenant-domain mappings add storage and verification state; they must be removed when ownership changes. Measure requests rejected by authority, mismatched TLS and HTTP names, redirects to unexpected hosts, and login-cookie failures after domain changes. Review account links in a mail sandbox before production release.",
        failure="Send an unknown Host with a valid TLS connection and confirm the ingress rejects it rather than serving the reviewer app. Request a known HTTP authority under a different TLS name and verify the configured policy. Supply duplicate authority fields through a test proxy and ensure they are not merged into an ambiguous route. Remove a verified custom domain from a tenant, then attempt to reach a stale backend mapping. Generate a password reset message while the incoming request uses an unexpected host; the link must use the configured canonical origin, not the untrusted request text.",
        drill="Create an allowlist for the public guide, reviewer app, API, and one verified customer domain. For each name, record certificate, route target, canonical origin, and cookie scope. Route cases 29 and 47 under the expected authorities, then probe an old staging name and an unknown name. Revoke the customer domain while DNS still points to the ingress and prove it no longer selects that tenant. Inspect one account link generated during an unknown-host request and verify its base comes from configuration.",
        decision="Unknown authorities fail at ingress; user-facing absolute links come from configured origins.",
        code='function routeForAuthority(requestHost, allowedHosts) {\n'
             '  const normalizedHost = requestHost.toLowerCase();\n'
             '  return allowedHosts.get(normalizedHost) || "reject";\n'
             '}\n'
             'console.log(routeForAuthority("old-test.permit.invalid", new Map([["portal.permit.invalid", "review-app"]])));\n'
             '// Output: reject',
        checks=["Every production hostname has a declared certificate and route.", "Unknown or revoked hosts cannot reach a privileged default app.", "Account links use configured canonical origins."],
        mistakes=["Pointing a catch-all virtual host at a private application.", "Building account links from a raw request Host.", "Assuming TLS name and HTTP authority always match."],
        related=["web-tech/dns-ttl-negative-cache-and-cutover-planning", "web-tech/tls-certificate-rotation-and-hsts-scope"],
    ),
    dict(
        slug="ingress-health-readiness-and-connection-drain",
        title="Ingress Health, Readiness, and Connection Drain",
        summary="Distinguish process liveness from traffic readiness and drain long-lived requests during rollout.",
        concept="A load balancer needs a rule for sending new requests to an application instance. Liveness answers whether the process should keep running; readiness answers whether it should receive traffic now. A process can be alive while warming critical state, migrating a local cache, or preparing to shut down. A shallow readiness probe may say healthy while an essential dependency is unusable, but a probe that flaps on a minor downstream delay can remove too many instances at once. Draining is a separate state: stop new admission, allow bounded in-flight work to finish, and close or redirect long-lived connections according to the protocol. A rollout is safe only when the health thresholds and drain deadline fit real request durations.",
        case="Six permit API replicas are replaced one at a time. A new replica reports process liveness before loading its case policy table, so the ingress sends approvals to it and gets errors. An old replica is killed immediately after it becomes unready, cutting off an export and 900 open socket clients. The revised release waits for a route-level readiness condition, marks the old replica draining, stops new ordinary traffic, gives short requests a completion window, and tells long-lived clients to reconnect through an active node. A global database pause is handled with bounded load shedding rather than making all replicas flap out of rotation simultaneously.",
        implementation="Define liveness with a cheap local signal and readiness with the minimum conditions needed to handle the routes assigned to that instance. Keep probe work bounded; a health endpoint must not itself exhaust database connections during an incident. Use consecutive success and failure thresholds to avoid oscillation, then measure detection time against the availability target. During deployment, switch the instance to draining before sending a termination signal. Stop new upgrades and ordinary admission, track active requests, finish those inside a defined grace period, and hand long-lived clients a documented reconnect path. Give exports and background jobs their own lifecycle if they cannot finish within that window. Set termination grace longer than the application drain deadline, and test with actual traffic rather than an idle node.",
        cost="Health probes consume small recurring work across every instance, and more sensitive thresholds detect failure faster while risking false removals. Long drain windows preserve requests but tie up old capacity and may slow deployments. Short windows free capacity yet increase interrupted exports and reconnect surges. A readiness check that depends on one shared service can mark the entire fleet unready during a partial outage, making recovery harder. Track healthy and draining instance counts, probe failure cause, request completion during drain, forced termination count, socket reconnect rate, and rollout error rate. Ensure capacity math includes one node leaving and one not yet ready.",
        failure="Start a replica with its HTTP port open but policy data unavailable; liveness may pass while readiness must fail. Delay one optional telemetry dependency and ensure it does not remove the serving fleet. Drain a node under 63 concurrent short requests and several long exports, then check completion and explicit interruption results. Put 900 sockets on a node, drain it, and observe that reconnects spread rather than synchronizing. Fail a shared database dependency and verify health policy does not repeatedly remove every instance while the load balancer routes to nowhere. Restart a probe process and verify hysteresis avoids rapid flapping.",
        drill="Write a state table for starting, ready, draining, and stopped replicas. Choose readiness conditions for the case-read and approval paths, failure and success thresholds, a 47-second app drain deadline, and a 62-second termination grace. Run a rolling replacement with one replica removed from six. Record the minimum healthy capacity, new-request admission, completed requests, forced closures, and reconnect load. Repeat with one optional dependency failed and one essential policy table missing.",
        decision="Health controls admission; draining preserves in-flight work within a measured deadline.",
        code='function mayReceiveNewPermitRequest(processAlive, policyLoaded, draining) {\n'
             '  return processAlive && policyLoaded && !draining;\n'
             '}\n'
             'console.log(mayReceiveNewPermitRequest(true, true, true));\n'
             '// Output: false',
        checks=["Readiness rejects traffic before essential state loads.", "Draining stops new admission before termination.", "Long-lived connections have bounded reconnect behavior."],
        mistakes=["Using an open TCP port as proof that business routes are ready.", "Terminating immediately after readiness turns off.", "Making one optional dependency remove the entire fleet."],
        related=["web-tech/presence-expiry-heartbeats-and-connection-drain", "web-tech/production-signals-and-incident-decisions"],
    ),
    dict(
        slug="proxy-body-budgets-timeouts-and-retry-ownership",
        title="Proxy Body Budgets, Timeouts, and Retry Ownership",
        summary="Align ingress limits with application deadlines and prevent ambiguous retries of side-effecting requests.",
        concept="A reverse proxy may buffer request bodies, stream them upstream, impose size and time limits, or retry a failed upstream. Each choice changes how much work the application sees and when a caller receives a response. Buffering can protect an origin from very slow senders but consumes edge memory or disk; streaming can reduce buffering while tying up an origin connection for longer. A read timeout is often measured between successful reads, not necessarily across the whole request, so a slow trickle can survive unless total time and rate are also bounded. Retries are dangerous for side-effecting requests when the proxy cannot know whether the origin committed before a connection failed. The retry owner and idempotency contract must be explicit.",
        case="A field tablet uploads a 63-megabyte inspection file through the ingress. One route accepts only 47 megabytes, but the limit exists only in the app, so the proxy buffers the entire request before the app rejects it. Another client sends a few bytes every second and occupies an origin slot. During approval, an upstream connection breaks after the database commits but before the proxy receives the response; an automatic retry creates a second notification. The revised path rejects oversized uploads at ingress, assigns a bounded streaming or buffering policy to each route, sets total deadlines, and does not replay the approval without the server's stable operation identity.",
        implementation="Classify routes by maximum body size, content type, buffering choice, upload duration, and whether a body can be replayed. Enforce coarse limits at ingress and detailed validation at the app; neither layer should assume the other is enough. For large uploads, use a private staging path and explicit integrity checks rather than sending unlimited bytes through an ordinary API transaction. Give connection, header, body, upstream, and total request phases budgets that fit inside the caller's deadline. Decide whether the proxy may retry each route before deployment. A safe informational read can often retry within a small attempt and time budget if no response bytes reached the client. A mutation needs a stable idempotency key and server-owned result; proxy retries alone cannot prove one effect. Record whether the origin received the body and whether a response had begun before failover.",
        cost="Buffering uses edge memory or disk proportional to simultaneous body volume; streaming shifts duration and backpressure to origin connections. Lower size and time limits conserve resources but can reject legitimate slow field uploads. Higher limits invite resource exhaustion and make rollout drains longer. Retries add upstream work and can worsen an incident if the fleet is overloaded. Track rejected body size, slow-upload duration, buffer utilization, origin slots held, timeout phase, retry attempts, and duplicate-effect suppression. The important measure is the full user task, including a successful recovery path when a transfer is interrupted. A 502 count by itself cannot show whether the origin committed a write.",
        failure="Send a 63-megabyte file to a route capped at 47 megabytes and confirm ingress rejects early without storing the full body. Trickle bytes slowly while keeping the socket technically active; a total deadline must end the request. Stop an upload halfway through and verify private staging cleanup. Commit an approval, then drop the origin connection before response; the proxy must not blindly replay it as a new operation. Return a partial streamed response and fail upstream: once bytes reach the client, switching servers cannot invisibly repair the stream. Load-test a retry burst while one node drains to ensure the remaining pool has capacity.",
        drill="Make a route matrix for case reads, approval writes, and inspection uploads. Give each a body cap, header deadline, body deadline, total deadline, buffering mode, and retry policy. Use a 47-megabyte upload cap and simulate a 63-megabyte request, a slow sender, and a dropped upstream after a committed approval. Record edge bytes buffered, origin work, client response, operation identity, and cleanup. Prove that retries never produce two approval audit entries and that partial responses report failure rather than fabricated completeness.",
        decision="A proxy cannot infer mutation safety from a broken connection; budget bodies and own retries explicitly.",
        code='function mayRetryUpstream(requestKind, bodyReplayable, responseStarted) {\n'
             '  return requestKind === "pure-read" && bodyReplayable && !responseStarted;\n'
             '}\n'
             'console.log(mayRetryUpstream("case-approval", true, false));\n'
             '// Output: false',
        checks=["Ingress and app both enforce route-specific body limits.", "Total deadlines stop slow trickle requests.", "Mutations cannot gain duplicate effects from automatic proxy retries."],
        mistakes=["Assuming a per-read timeout bounds the entire upload.", "Buffering an oversized body before rejecting it.", "Retrying a failed connection as proof that the origin did not commit."],
        related=["web-tech/request-deadlines-retries-and-backoff", "web-tech/file-ingestion-and-private-asset-lifecycle"],
    ),
]

assert hub_path not in by_path and len(topics) == 4
hub = copy.deepcopy(by_path["web-tech/production-signals-and-incident-decisions"])
hub.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + hub_path)), path=hub_path,
           title=hub_title, summary="Trust proxy metadata narrowly, route only known hosts, drain healthy nodes safely, and bound body and retry work.",
           sort_order=3630, created_at=stamp, updated_at=stamp, published_at=stamp)
hub["data"] = {"subject_root": "web-tech/web-technology", "section_path": hub_path, "content_format": "html", "seo_ready": False,
               "modules": [], "resource_tabs": [{"title": "Web Development", "path": "web-tech/web-technology"},
                                               {"title": "Projects", "path": "web-tech/web-technology/project"},
                                               {"title": "Quizzes", "path": "web-tech/quizzes"}]}
entries.append(hub)
by_path[hub_path] = hub

for number, topic in enumerate(topics):
    path = "web-tech/" + topic["slug"]
    assert path not in by_path
    subprocess.run(["node", "--check", "--input-type=module"], input=topic["code"], text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path["web-tech/trace-context-across-request-and-job"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path, title=topic["title"], summary=topic["summary"],
                 sort_order=3631 + number, created_at=stamp, updated_at=stamp, published_at=stamp)
    related = [hub_path] + ["web-tech/" + other["slug"] for other in topics if other is not topic] + topic["related"]
    body = paragraph(topic["concept"]) + "<h2>Working case</h2>" + paragraph(topic["case"])
    body += '<h2>Implementation boundary</h2><pre><code class="language-javascript">' + html.escape(topic["code"], quote=False) + "</code></pre>" + paragraph(topic["implementation"])
    body += "<h2>Cost and boundaries</h2>" + paragraph(topic["cost"]) + "<h2>Failure trace</h2>" + paragraph(topic["failure"])
    body += "<h2>Verification</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in topic["checks"]) + "</ul>"
    body += "<h2>Practice drill</h2>" + paragraph(topic["drill"]) + "<h2>Decision note</h2>" + paragraph(topic["decision"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in topic["mistakes"]) + "</ul>"
    entry["body"] = body
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": hub_path, "content_format": "html", "seo_ready": False,
                     "kind": "tutorial", "author_path": "authors/aitrove-editorial", "reading_minutes": 8, "related": related}
    entries.append(entry)
    by_path[path] = entry

for topic in topics:
    entry = by_path["web-tech/" + topic["slug"]]
    entry["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in entry["data"]["related"]) + ".</p>"

hub["data"]["modules"] = [{"title": hub_title, "summary": hub["summary"], "lessons": ["web-tech/" + topic["slug"] for topic in topics]}]
hub["body"] = paragraph("The ingress receives a browser request before the application does. This track follows that handoff through trusted forwarding, hostname selection, healthy upstream admission, and bounded request-body or retry behavior. A broken boundary can misroute private traffic or duplicate a write even when the application handler is correct.")
hub["body"] += "<h2>Topics in this track</h2><ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
hub["body"] += "<h2>Prerequisite paths</h2><p>" + "; ".join(link(path) for path in ["web-tech/edge-request-normalization-and-origin-trust", "web-tech/network-transport-and-domain-operations", "web-tech/request-deadlines-retries-and-backoff"]) + ".</p>"
root_entry = by_path["web-tech/web-technology"]
root_entry["data"]["modules"].append({"title": hub_title, "summary": hub["summary"], "lessons": [hub_path] + ["web-tech/" + topic["slug"] for topic in topics]})
root_entry["body"] += "<h2>" + link(hub_path) + "</h2>" + paragraph(hub["summary"]) + "<ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
root_entry["updated_at"] = stamp
crosslinks = {
    "web-tech/edge-request-normalization-and-origin-trust": [hub_path, "web-tech/trusted-proxy-hops-and-forwarded-client-identity"],
    "web-tech/tls-certificate-rotation-and-hsts-scope": ["web-tech/host-authority-routing-and-default-deny"],
    "web-tech/presence-expiry-heartbeats-and-connection-drain": ["web-tech/ingress-health-readiness-and-connection-drain"],
    "web-tech/request-deadlines-retries-and-backoff": ["web-tech/proxy-body-budgets-timeouts-and-retry-ownership"],
    "web-tech/file-ingestion-and-private-asset-lifecycle": ["web-tech/proxy-body-budgets-timeouts-and-retry-ownership"],
}
for path, targets in crosslinks.items():
    assert path in by_path, path
    by_path[path]["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    by_path[path]["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": 1, "new_lessons": 4, "prose_words": {topic["slug"]: len(re.findall(r"\b[\w'-]+\b", " ".join(str(topic[key]) for key in ("concept", "case", "implementation", "cost", "failure", "drill", "decision", "summary")))) for topic in topics}}))
