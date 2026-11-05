"""Extend the local DevOps preview with network-path failure contracts."""

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
    "path-mtu-black-hole", "Path MTU: find the packet size that breaks an otherwise healthy route",
    "Diagnose large-request stalls across tunnels, overlays, and edge links.",
    "Path maximum transmission unit is the largest packet a route can carry without fragmentation or a size-related drop. An overlay, VPN, or tunnel can reduce usable payload below the host interface MTU. Small health requests may work while larger TLS records or uploads stall. Packet-size failure must be separated from application timeout, DNS, and server capacity faults; an ICMP result from one segment does not prove the entire client-to-service path is healthy.",
    "A receipt API accepts a short status request but hangs when a client uploads a 31-kilobyte attachment through a private tunnel. Capture the client path, tunnel endpoint, gateway, and backend address for the same attempt. Compare a small and a large request with identical authentication and routing. The read-only trace below can reveal a lower path MTU on a Linux host, but some middleboxes do not return useful control messages; pair it with packet capture or endpoint counters where available. Check whether the tunnel clamps TCP maximum segment size and whether ICMP needed for path discovery is blocked. Test IPv4 and IPv6 separately if both are served. Reduce packet size only as a controlled diagnostic, then fix the transport or tunnel policy and verify sustained uploads from the real client network. Record request size, retransmissions, and timeout phase so a successful ping does not close the incident.",
    "bash", "tracepath -n receipt-gateway.internal\nip -s link show dev eth0",
    "A smaller tunnel MTU may add packets, CPU, and per-packet overhead for every large transfer. A larger value can look efficient in a benchmark while silently failing on one route. Extra packet capture has privacy and storage costs, so filter to synthetic test traffic and retain only what the investigation needs. Measure upload completion rate by size, retransmissions, and effective path MTU before and after the fix. The trace command is Linux-specific and its output depends on intermediate devices.",
    ["Do not treat a short ping as proof that large application payloads work.", "Do not lower every host MTU before identifying the failing segment.", "Do not assume an IPv4 result also validates the IPv6 path."],
    ["devops/dns-tls-edge", "devops/egress-dns-contract", "devops/nat-port-allocation-pressure", "devops/synthetic-transaction-monitoring"],
)

lesson(
    "conntrack-capacity-boundary", "Connection tracking: separate host flow exhaustion from application limits",
    "Watch tracked-flow occupancy and allocation failures during bursts.",
    "Linux connection tracking stores state for network flows used by firewall and address-translation paths. A full table can reject new flows even when the application has spare workers and the load balancer reports healthy. The count and maximum describe one host's tracking capacity, not the number of useful application requests. Timeouts, UDP traffic, and NAT behavior determine how long entries remain, so a burst can outlast the traffic that created it.",
    "A receipt service starts timing out on new outbound ledger calls after a deployment doubles connection churn. On each affected Linux node, collect the read-only count and maximum below, kernel drop or insert-failure counters, active sockets, and per-destination traffic. Compare nodes carrying equal request volume; a single hot node can reach its limit first. Then determine whether the increase came from lost connection reuse, retry amplification, an egress proxy, or a scan. Restore pool reuse or pace retries before raising limits. If a larger table is justified, budget kernel memory and test it under the same burst and failure conditions. Check that new connections recover without deleting existing legitimate flows. A successful application readiness check can still miss this fault if it reuses one established connection.",
    "bash", "cat /proc/sys/net/netfilter/nf_conntrack_count\ncat /proc/sys/net/netfilter/nf_conntrack_max\nss -s",
    "Tracking more flows consumes memory and increases inspection work; lowering timeouts can interrupt legitimate idle protocols. A blanket maximum increase may hide a runaway client until the next, larger burst. Inspect the ratio of count to limit, failed inserts, memory pressure, and client-visible connection errors together. The two files exist on Linux systems with connection tracking enabled; container and namespace views may differ from the node that actually performs translation.",
    ["Do not equate open application sockets with every tracked flow.", "Do not raise the limit without finding the flow source and memory cost.", "Do not count a green readiness probe as proof that new outbound flows can be allocated."],
    ["devops/nat-port-allocation-pressure", "devops/retry-amplification-control", "devops/file-descriptor-exhaustion", "devops/load-balancer-health-semantics"],
)

lesson(
    "proxy-idle-timeout-alignment", "Proxy idle timers: stop reused sockets from failing the next request",
    "Align client pools, edge proxies, and backend idle policies by hop.",
    "An idle timeout closes a connection after a period without qualifying traffic. A client pool may still believe the socket is reusable when an intermediate proxy has closed it. The next request then sees a reset or an ambiguous failure. Idle timeout, maximum connection age, request timeout, and graceful drain are different controls; configuring one number across every hop can worsen throughput or still leave a race.",
    "A checkout client holds a pooled connection to a receipt gateway. The gateway closes idle backend sockets sooner than the client retires them, and the first request after a quiet period fails. Record each hop's idle timer, the client pool's idle eviction, maximum connection lifetime, protocol version, and retry policy. In an isolated test, send a request, wait just below and just above the suspected threshold, then send another request while logging the peer socket and any reset. Set the client's idle retirement earlier than the network hop it can observe, with a margin for scheduling and clock variance; test the exact client library because some validate a pooled socket before reuse. For a streaming response, confirm whether the proxy's timer is reset by application bytes or only by protocol traffic. Retry an idempotent read if its contract permits it, but reconcile an ambiguous mutation by operation ID before replay.",
    "text", "Receipt client pool contract\nGateway idle close: measured from gateway configuration\nClient idle eviction: shorter than gateway close, with margin\nRequest deadline: independent of socket idle lifetime\nMutating retry: reuse operation key and reconcile prior result\nVerification: first request after quiet period succeeds",
    "Short pool lifetimes increase DNS lookups, TCP and TLS handshakes, CPU, and ephemeral port churn. Long lifetimes improve reuse but extend old-endpoint exposure and increase idle-close races. A proxy may have separate client-facing and backend-facing timers, so tune the failing hop rather than the most visible one. Measure handshake rate, first-after-idle errors, request latency, and reset direction. Verify from both client and proxy logs; a backend success counter can miss a response lost at the edge.",
    ["Do not call every timeout a request deadline.", "Do not retry an ambiguous payment with a new operation key.", "Do not assume one load-balancer timer covers both sides of the proxy."],
    ["devops/connection-pool-endpoint-churn", "devops/retry-timeout-budgets", "devops/http-idempotency-replay", "devops/connection-drain-boundary"],
)

lesson(
    "forwarded-client-ip-trust", "Forwarded client IP: trust a hop, not a request header",
    "Make rate limits and audit logs use an authenticated proxy boundary.",
    "A forwarding header can carry a client address through HTTP proxies. A direct client can also send that same header unless the edge removes or replaces it. If an application accepts the leftmost address from any incoming request, an attacker can spoof identity for rate limits, allowlists, and audit records. The trustworthy input is the immediate peer and a configured chain of proxies that the service is allowed to trust.",
    "A receipt gateway uses client IP for abuse controls. Map the public edge, internal proxy, and application peer addresses, then configure the application to accept forwarded information only from the exact proxy networks it controls. At the first trusted ingress, discard an untrusted client's supplied forwarding header before writing the verified address; downstream proxies may append according to a documented chain policy. Test a direct synthetic request with a forged internal address and confirm it cannot bypass the limiter. Test through the real edge and confirm the audit record contains both the verified client address and the proxy peer. A private network alone is not enough if another tenant or workload can connect to the application port. Review proxy network changes as a security change, and keep the raw header out of authorization decisions when the chain cannot be established.",
    "text", "Receipt client-address contract\nPublic client header: untrusted input\nFirst trusted edge: replace untrusted forwarding fields\nApplication peer: must match approved proxy network\nAccepted client address: derived only through that chain\nAudit: retain verified client plus immediate peer",
    "Trusted proxy lists require upkeep as gateways move, and extra audit fields increase log volume. If the list is too narrow, legitimate users collapse into the edge address and rate limits become unfair; if it is too broad, spoofed addresses become accepted. Measure direct-to-origin attempts, requests rejected for an invalid chain, rate-limit distribution, and mismatches between edge and application logs. A correct address is useful evidence, but it is not authentication for the customer account.",
    ["Do not trust a client-supplied forwarding header on a direct connection.", "Do not use an IP address as a substitute for account authentication.", "Do not trust an entire private address range when only named proxies should connect."],
    ["devops/edge-rate-limit-fairness", "devops/gateway-api-routing", "devops/telemetry-sensitive-data-boundary", "devops/network-policy-isolation"],
)

lesson(
    "tls-sni-routing-proof", "TLS name selection: test SNI, certificate, and HTTP host together",
    "Locate certificate faults before routing rules or backend handlers.",
    "A TLS client can send a server name during the handshake so a shared listener selects the intended certificate and policy. The later HTTP authority or Host field chooses an application route. These are related names but separate protocol steps. A request can reach the correct IP and still fail before HTTP if the TLS name is absent, the wrong certificate is selected, or the certificate does not cover the requested name.",
    "A receipt portal moves to a shared edge listener. Test the exact public hostname with a normal client and inspect the certificate chain, name coverage, and expiry. Then use the diagnostic handshake below to see what the edge presents when the intended SNI is sent; compare with a no-SNI connection only to understand the listener default, not as proof of user behavior. Test the HTTP route separately after certificate validation. A synthetic check that connects to an IP with a custom Host header may omit SNI and report a misleading failure, so configure it to use the actual hostname or an explicit name-resolution override. During rotation, keep old and new names covered for the compatibility window and verify both edge locations before removing the prior certificate. Do not disable certificate verification to make a route test pass; that only hides the trust failure.",
    "bash", "openssl s_client -connect receipt-edge.internal:443 -servername receipts.internal -verify_return_error",
    "Certificate checks add handshake work, but they are cheap compared with serving traffic under the wrong identity. Multiple certificates and edge locations increase rotation coordination and monitoring scope. Record failures by TLS name, selected certificate, and edge location, as well as HTTP route result after handshake. A successful TCP connect says nothing about name validation. The command reports the presented chain, but a complete client test must also validate hostname rules and trust using the client's own TLS stack.",
    ["Do not test a named HTTPS route only by connecting to its IP without SNI.", "Do not bypass certificate verification to mask a bad edge rollout.", "Do not treat the HTTP Host field as a replacement for TLS name selection."],
    ["devops/dns-tls-edge", "devops/certificate-renewal-path", "devops/synthetic-transaction-monitoring", "devops/gateway-api-routing"],
)

lesson(
    "dual-stack-reachability-gate", "Dual-stack rollout: prove IPv4 and IPv6 reach the same service contract",
    "Test both address families through DNS, load balancer, policy, and backend.",
    "A dual-stack Service can have both IPv4 and IPv6 cluster addresses, but that does not prove an external client has both routes or that every dependency supports both families. Address selection, firewall policy, load-balancer capability, and application bind behavior can differ. A successful IPv4 check can conceal a broken IPv6 route that affects only clients preferring the newer family.",
    "A receipt API adds IPv6 access. In a test cluster that supports dual stack, declare the Service policy below and confirm the assigned addresses, EndpointSlices, and actual Pod listeners. Provision the public load balancer only after confirming its provider supports both families. From separate client networks, resolve A and AAAA records, force each family for a synthetic receipt read, and compare TLS name validation, response body, and latency. Include a network policy test and an outbound dependency check: the application may accept IPv6 inbound but still require IPv4 to reach a payment provider. Roll out DNS only after both routes pass, then track failures by family. If one family breaks, remove its advertisement or route according to the rollback plan instead of forcing clients to wait on fallback behavior that varies by implementation.",
    "yaml", "apiVersion: v1\nkind: Service\nmetadata:\n  name: receipt-api\n  namespace: checkout\nspec:\n  ipFamilyPolicy: PreferDualStack\n  ipFamilies:\n    - IPv4\n    - IPv6\n  selector:\n    app: receipt-api\n  ports:\n    - name: https\n      port: 443\n      targetPort: 8443",
    "Dual-stack adds addresses, policy rules, tests, and possibly load-balancer cost. It can reduce dependence on IPv4 address translation, but partial enablement creates a larger failure surface. A preferred dual-stack policy may fall back to one family on a cluster without support, so inspect the assigned result rather than assuming it. Measure success and latency by address family, failed connection attempts, and whether the synthetic transaction reached the same backend behavior. Keep family-specific telemetry long enough to catch uneven rollout.",
    ["Do not publish an AAAA record before testing the public IPv6 path.", "Do not assume a dual-stack Service implies a dual-stack cloud load balancer.", "Do not aggregate IPv4 and IPv6 errors into one green health number."],
    ["devops/kubernetes-service-discovery", "devops/gateway-api-routing", "devops/dns-cutover-safety", "devops/network-policy-isolation"],
)

lesson(
    "http3-udp-fallback-contract", "HTTP/3 rollout: keep a tested TCP route when UDP fails",
    "Measure protocol choice and fallback instead of counting advertised support.",
    "HTTP/3 carries HTTP semantics over QUIC on UDP. An edge can advertise an alternative service to capable clients, yet a client network may block UDP or a particular client may not attempt HTTP/3. The advertised protocol, negotiated protocol, and completed user request are separate observations. A safe rollout preserves a working HTTPS path over TCP while validating the new transport.",
    "A receipt portal enables HTTP/3 at the edge. Start with a small cohort and record the alternative-service response, actual protocol selected, handshake failures, and request success by network. Use a client that can force HTTP/3 to verify the new path, then block UDP in an isolated network and test whether that client's normal request succeeds through the existing TCP endpoint within the user latency budget. Repeat after the client has cached the alternative-service advertisement; behavior may differ from a fresh profile. Check that certificate and HTTP routing results are the same on both transports and that rate limits do not give one protocol an unintended advantage. Roll back by stopping new advertisement and keeping the TCP route healthy; cached advertisements may persist until their lifetime expires, so monitor attempted HTTP/3 connections during the drain window.",
    "text", "Receipt edge transport gate\nHTTP/3 advertised: only after UDP route passes synthetic check\nObserved protocol: log negotiated transport per request\nUDP blocked: ordinary client request still succeeds over TCP\nCached advertisement: tested through expiry window\nRollback: stop advertising; retain compatible TCP endpoint",
    "Running two transports consumes extra edge configuration, UDP capacity, and monitoring work. A faster happy-path handshake is not useful if blocked-network clients wait before fallback. Track time to first successful response, failed QUIC attempts, and completed receipt requests by protocol and client network. The fallback is client-specific and should be demonstrated with the supported clients, not assumed from a successful TCP-only probe.",
    ["Do not count an advertisement as proof that HTTP/3 was negotiated.", "Do not disable the TCP route while fallback remains part of the contract.", "Do not ignore cached alternative-service entries during rollback."],
    ["devops/http2-goaway-drain", "devops/connection-drain-boundary", "devops/synthetic-transaction-monitoring", "devops/dns-tls-edge"],
)

lesson(
    "proxy-protocol-peer-boundary", "PROXY protocol: accept client metadata only from the intended load balancer",
    "Pair source-address propagation with network and listener isolation.",
    "The PROXY protocol places connection metadata before the application protocol so a load balancer can convey the original client address. It is not an authentication scheme. A listener expecting this preface will reject ordinary clients that do not send it, while a listener exposed to untrusted senders can receive forged metadata. The proxy and backend must agree on the protocol version, listener mode, and trusted source boundary.",
    "A receipt TCP gateway needs the caller address for abuse investigation. Create a dedicated backend listener that accepts PROXY metadata only from the load balancer's known network or identity boundary; keep the direct diagnostic listener separate. Configure the load balancer to send the agreed version and verify a real request reaches the application with both reported client address and immediate peer recorded. Try a direct test connection without the preface and confirm it cannot reach a privileged request path. Also test a forged preface from an untrusted network and confirm network controls block it before the application trusts it. Change one side of the protocol setting in an isolated environment to observe the failure signature, then restore it. During load-balancer replacement, update trusted sources and audit logs together so a temporary broad allow rule does not remain after cutover.",
    "text", "Receipt PROXY listener contract\nUpstream sender: named load balancer only\nTransport: dedicated backend port and agreed PROXY version\nNetwork rule: deny all other source networks\nApplication log: original client plus immediate peer\nNegative test: direct and forged prefaces cannot bypass the boundary",
    "A separate listener and network rule add deployment and test work. The preface adds a small amount of connection data, but the material risk is an incorrect trust boundary that makes rate limits and audit records unreliable. Measure rejected direct connections, version mismatch errors, original-client coverage, and proxy peer changes. If the upstream already terminates HTTP and can set a validated forwarding header, compare the simpler route before adding another transport contract.",
    ["Do not expose a PROXY-aware listener directly to arbitrary clients.", "Do not assume the embedded client address is authenticated.", "Do not enable the protocol on only one side of a connection."],
    ["devops/forwarded-client-ip-trust", "devops/edge-rate-limit-fairness", "devops/network-policy-isolation", "devops/load-balancer-health-semantics"],
)

titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/network-path-diagnosis-project"
quiz_path = "quizzes/devops-network-path-decisions"
titles[project_path] = "Project: diagnose a failing network path from client to backend"
titles[quiz_path] = "DevOps network-path decisions"
unknown = {path for item in specs for path in item["related"] if path not in titles}
assert not unknown, unknown


def links(paths):
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in paths
    ) + "</ul>"


for heading, summary, slugs in [
    ("Packet and flow capacity", "Find size-dependent failure and exhausted node flow tables.", ["path-mtu-black-hole", "conntrack-capacity-boundary"]),
    ("Connection lifetime and identity", "Align idle timers and trust client addresses only across known proxies.", ["proxy-idle-timeout-alignment", "forwarded-client-ip-trust"]),
    ("TLS and address families", "Prove name selection and both IP families on the user path.", ["tls-sni-routing-proof", "dual-stack-reachability-gate"]),
    ("Transport fallback and source metadata", "Test UDP failure and isolate PROXY-aware listeners.", ["http3-udp-fallback-contract", "proxy-protocol-peer-boundary"]),
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
               sort_order=20600 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
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
               summary="Reproduce packet, flow, timeout, identity, TLS, IPv6, and transport failures.",
               difficulty="Advanced", sort_order=20690,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 9,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in project_related]}
project["body"] = (
    "<p>Build an isolated receipt service behind a test gateway and load balancer. Use two client networks, a Linux node where flow tracking is visible, disposable TLS names, and synthetic account data. Record the exact client address, DNS answers, negotiated protocol, TLS name and certificate, proxy peer, backend address, request size, socket age, and completed user result. Keep each fault limited to the test route; a green process probe is only one observation.</p>"
    "<h2>Break the route at distinct layers</h2><p>Send a short read and a larger attachment through a tunnel, then lower the tunnel path MTU until only the larger operation fails. Compare retransmissions with a read-only path trace. Generate short-lived outbound flows until the test node approaches its tracking limit; preserve the counters and restore client reuse before raising capacity. Keep a client socket idle past the gateway close, then send the next read and record whether the pool retries it safely. Supply a forged forwarding address on a direct request and show that the application refuses to trust it. Repeat through the approved proxy and inspect the verified address and peer fields.</p>"
    "<pre><code class=\"language-text\">Receipt route acceptance gates\nLarge upload: completes across the tunnel after MTU repair\nNew flow: succeeds under the planned connection burst\nIdle reuse: first request after a quiet period succeeds\nClient address: forged direct header cannot change identity\nTLS: intended name selects a valid certificate\nIPv4 and IPv6: same receipt result through each family\nHTTP/3: blocked UDP still leaves a working TCP request\nPROXY preface: only the named load balancer can supply it</code></pre>"
    "<h2>Prove identity and fallback</h2><p>Use the intended TLS name and inspect the certificate before testing HTTP routing. Publish an IPv6 test address only after the Service, load balancer, firewall, and backend listener pass an end-to-end check; compare with IPv4 from a separate client network. Advertise HTTP/3 to a controlled client, record the actual negotiated protocol, then block UDP and test normal client fallback over TCP, including a client with cached alternative-service state. Enable a dedicated PROXY-aware backend port and attempt both a valid load-balancer connection and an untrusted forged preface. Recheck rate limits and audit fields on each route.</p>"
    "<h2>Cost and verification</h2><p>Capture packet overhead after an MTU change, tracking-table memory, handshake rate after idle-timer changes, extra address-family and UDP test cost, and proxy rejection rate. The drill passes only when the user request completes and the source identity remains trustworthy under the planned fault. Record which client, protocol version, route, and failure phase produced every result; aggregated success counts hide asymmetric network failures.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not treat a successful small request as proof that uploads work.</li><li>Do not trust an address asserted by an arbitrary client.</li><li>Do not count protocol advertisement as a completed user request.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*project_related, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Network path diagnosis drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("Why can a short health request pass while a large upload stalls?", ["The route may have a lower usable path MTU", "The service must be fully healthy", "The DNS name cannot resolve"], "Packet size can expose a tunnel or path discovery fault."),
    ("What should accompany a near-full connection-tracking table?", ["Failed inserts and client-visible new-flow errors", "Only the application's worker count", "Only a green readiness result"], "Occupancy matters when it affects flow allocation."),
    ("What is the likely risk when a client pool outlives a proxy's idle close?", ["The next reused socket may reset", "The prior request is always duplicated", "DNS rewrites the live socket"], "The client may hold a socket that the proxy already retired."),
    ("Which forwarded address can an application trust?", ["One derived through its configured proxy chain", "Any value in a direct client's header", "The leftmost header entry regardless of peer"], "Peer trust is required before using forwarding metadata."),
    ("What happens before an HTTP Host route is evaluated?", ["The TLS handshake may select a certificate by server name", "A backend handler always responds", "Every client sends the same certificate"], "TLS identity is negotiated before HTTP routing."),
    ("What proves a dual-stack rollout serves users?", ["Separate end-to-end IPv4 and IPv6 requests", "Only a dual-stack field in a Service", "One successful IPv4 probe"], "Address allocation alone does not prove both routes."),
    ("What does an HTTP/3 advertisement fail to prove?", ["That a client negotiated HTTP/3 and completed a request", "That the edge sent a header", "That the origin has a hostname"], "Advertised and observed protocols are different measurements."),
    ("What is the fallback test for a blocked UDP network?", ["A normal client request still completes on the TCP route", "The edge emits more UDP packets", "The client receives only a timeout"], "The user result, including fallback delay, determines success."),
    ("What is required before trusting a PROXY protocol preface?", ["A listener reachable only through approved senders", "A public port accepting arbitrary prefaces", "An HTTP Host header"], "The preface carries metadata, not sender authentication."),
    ("Why inspect the immediate proxy peer as well as the reported client?", ["It proves which hop supplied identity metadata", "It replaces account authentication", "It eliminates network logging"], "The source chain is part of the trust decision."),
    ("What should be measured after shortening client idle lifetime?", ["Handshake rate and first-after-idle errors", "Only container image size", "Only the proxy certificate name"], "More connection turnover can raise CPU and port use."),
    ("What should close a size-dependent network incident?", ["A successful large user request on the original failing route", "A short ping on a different network", "A lower MTU setting without a retest"], "Verification must match the original failure path."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on packet, flow, identity, and transport boundaries.",
            sort_order=20700, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in project_related],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Trace a failed request through packet size, flow state, idle connections, proxy identity, TLS name, address family, and transport choice. Choose the observation that proves the user path, not only one healthy component.</p>"
    "<h2>Review these lessons</h2>" + links(project_related)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-service-traffic-decisions", "quizzes/devops-terraform-ownership-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not infer end-to-end health from a small probe.</li><li>Do not accept untrusted proxy metadata as client identity.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Network path check</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": path, "title": titles[path]} for path in [project_path, quiz_path])

for source, targets in {
    "devops/dns-tls-edge": ["devops/path-mtu-black-hole", "devops/tls-sni-routing-proof", "devops/http3-udp-fallback-contract"],
    "devops/nat-port-allocation-pressure": ["devops/conntrack-capacity-boundary"],
    "devops/connection-pool-endpoint-churn": ["devops/proxy-idle-timeout-alignment"],
    "devops/edge-rate-limit-fairness": ["devops/forwarded-client-ip-trust", "devops/proxy-protocol-peer-boundary"],
    "devops/kubernetes-service-discovery": ["devops/dual-stack-reachability-gate"],
    "devops/http2-goaway-drain": ["devops/http3-udp-fallback-contract"],
    "devops/network-policy-isolation": ["devops/proxy-protocol-peer-boundary"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Advanced follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1, "total_records": len(rows)}))
