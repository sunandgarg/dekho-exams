"""Add certificate and trust operations lessons to the local DevOps preview."""

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
    "tls-chain-client-matrix",
    "TLS chain delivery: test the clients that actually connect",
    "A valid leaf certificate can still fail clients when the served intermediate chain is incomplete or incompatible.",
    "TLS verification builds a path from the server's leaf certificate through intermediate issuers to a trust anchor installed in the client. A server normally presents the leaf and required intermediates, while clients bring their own trusted roots. Different clients may have different trust stores and path-building behavior. A successful handshake from one operator laptop therefore does not prove that a container image, mobile release, Java process, or recovery-region load balancer can validate the same endpoint.",
    "A payments gateway rotates its edge certificate and receives a leaf plus an intermediate chain. The operator checks that the private key matches the leaf, that the serving proxy presents the intended chain for the requested name, and that the chosen chain reaches trust anchors in the supported client matrix. The matrix includes a clean container with the current application base image, a supported mobile build, a partner SDK, and the secondary region's health checker. Run a handshake from each class against both primary and recovery endpoints, checking expiry, name, key usage, and the exact peer chain observed. Test a deliberately omitted intermediate in a disposable listener; one client may recover by fetching or caching it, but another may fail, which is why cached success is weak evidence. Keep the intended certificate fingerprint and chain identifiers with the release record. If a new CA offers alternate chains, choose one by measured compatibility rather than assuming the shortest chain is universally accepted. Do not add the server private key to client images while distributing trust material.",
    "text",
    "Gateway chain acceptance\nServer: leaf matches deployed private key\nPresented: leaf plus intended intermediates\nName: requested host covered by SAN\nClients: container, mobile, partner, standby probe\nTrust: each client builds a path to its own anchor\nNegative test: intermediate removed on disposable listener",
    "For C client classes and E endpoints, the basic handshake matrix is O(C × E) checks; adding protocol variants and TLS versions increases it further. The cost is small compared with a partner outage but can affect CI time if every variant runs on every commit. Test full compatibility for certificate or chain changes and run a lighter expiry probe continuously. Measure handshake failures by client type, chain changes, and endpoints serving inconsistent fingerprints.",
    ["Do not validate only from a developer workstation with cached intermediates.", "Do not put a trust root in the server leaf bundle by assumption.", "Do not distribute a server private key with a client trust bundle."],
    ["devops/dns-tls-edge", "devops/certificate-renewal-path", "devops/tls-sni-routing-proof", "devops/multi-region-failover"],
)

lesson(
    "private-ca-bundle-overlap",
    "Private CA rotation: overlap trust before changing issuers",
    "A private trust-root rotation is a two-sided rollout across clients and servers.",
    "Replacing an issuer and immediately removing the old root breaks clients that have not received the new trust bundle, while deploying a new root without restricting its scope widens trust. The safe sequence distributes the new anchor to authorized clients, verifies they loaded it, issues server or workload certificates from the new chain, then retires the old anchor only after every supported peer has moved. Keep the client trust bundle separate from the server Secret that contains the private key.",
    "A warehouse scanning fleet authenticates to an internal inventory API. The platform team versions its trust bundle and rolls a temporary bundle containing both current and incoming roots to scanners, API clients, gateways, and the disaster-recovery site. Each client reports the loaded bundle generation; a configuration file update alone is not proof that a long-lived process refreshed its TLS context. The team then issues a new API leaf from the incoming CA and tests old and new clients against the same listener. Any scanner that cannot accept the new root is isolated and upgraded before the issuer switch. After the longest permitted client update window, verify no connection still relies on the old chain, remove the old root, and test that a certificate signed only by the retired root is rejected. Use different bundle names or generations so rollback is explicit. If the old CA key is compromised, the ordinary overlap schedule may be unsafe; invoke the compromise response instead and accept that some clients may need emergency updates. Track the expiry of roots and intermediates independently of leaf renewal because rotating a CA Secret may not automatically reissue every leaf.",
    "text",
    "Warehouse CA transition\nPhase 1: distribute old plus new roots to approved clients\nGate: process reports loaded bundle generation\nPhase 2: issue leaf from new chain and test both client cohorts\nPhase 3: migrate remaining clients and recovery site\nPhase 4: remove old root and reject old-only chain\nException: suspected CA-key compromise uses emergency path",
    "Trust distribution costs O(C) updates for C client deployments, but mixed versions can persist for days if edge devices connect infrequently. A dual-root interval briefly trusts both issuers, increasing the set of acceptable certificates; bound its duration and issuance authority. Measure clients on each bundle generation, handshakes still using the old chain, root and intermediate expiry, and time to remove the retired anchor. A passing server probe does not prove every client has refreshed its trust store.",
    ["Do not switch to the new issuer before clients trust its root.", "Do not mount a server key Secret into clients merely to obtain a CA certificate.", "Do not assume rotating a CA Secret automatically reissues all leaves."],
    ["devops/secret-rotation-rollout", "devops/encryption-key-rotation-recovery", "devops/mesh-identity-boundaries", "devops/certificate-renewal-path"],
)

lesson(
    "tls-name-routing-validation",
    "TLS names: verify SNI selection and peer identity independently",
    "A TLS connection must reach the intended listener and validate the peer certificate against the requested identity.",
    "SNI helps a server choose a certificate, but it is not proof that the client checked the certificate's Subject Alternative Name. A proxy can route to the right IP and still serve a default certificate, or route to a backend whose certificate names a different service. An IP-level probe, a disabled hostname check, or a test that omits SNI may miss those failures. Define the public host, internal service identity, and upstream TLS name separately when a proxy terminates and re-establishes TLS.",
    "A tax-calculation API moves behind a shared gateway. The edge should present a certificate for the customer-facing host, while the gateway validates its upstream peer against the tax service's internal name. Test both hops with the exact names and trust stores used in production. Send a request with the wrong SNI but a correct HTTP Host header; it must not accidentally reach the tax service under a default certificate. Then send correct SNI with an incorrect Host header and check routing policy. At the backend, replace the certificate with one for an unrelated service in a disposable environment and verify the gateway rejects it even though the signing CA is trusted. Review wildcard scope: a wildcard for one label should not be treated as permission for unrelated deeper names. Include IPv4, IPv6, and standby listeners because they may have different default routes. Record the observed certificate identity and upstream authority in a connection trace without logging private keys or sensitive request bodies. A TLS status code at the edge alone does not show whether the upstream hop validated its peer.",
    "text",
    "Tax API identity matrix\nEdge: requested host, SNI, served SAN, trust anchor\nGateway route: SNI and HTTP authority evaluated separately\nUpstream: expected internal name and verified SAN\nNegative: correct Host with wrong SNI\nNegative: wrong backend cert signed by trusted CA\nVariants: IPv4, IPv6, recovery listener",
    "A two-hop check needs at least two handshakes per path, with O(E × V) tests for E endpoints and V protocol or address variants. TLS termination adds proxy CPU and connection pools, but disabling upstream name checks to save investigation time removes peer authentication. Measure default-certificate hits, upstream verification failures, wrong-route requests, and certificate identity by listener. Re-test after gateway configuration changes, not only after certificate renewal.",
    ["Do not treat SNI selection as client-side hostname validation.", "Do not disable upstream name checks because the CA is private.", "Do not test only one address family or the primary listener."],
    ["devops/tls-sni-routing-proof", "devops/dual-stack-reachability-gate", "devops/proxy-protocol-peer-boundary", "devops/gateway-api-routing"],
)

lesson(
    "tls-secret-reload-connections",
    "Certificate reloads: distinguish file delivery from active TLS state",
    "A renewed Secret is useful only when every serving process begins using the new key and certificate.",
    "Kubernetes may refresh a projected Secret volume while an application keeps an old TLS context in memory. A process might reload on a signal, watch the file, accept a hot secret update, or require a restart. Existing connections often retain the security properties negotiated at their handshake until they close. A rotation plan must therefore test fresh handshakes and long-lived sessions separately, and it must know how the server behaves if certificate and key files are observed during a partial update.",
    "A dispatch gateway receives a renewed certificate in its mounted Secret. The team records the Secret generation and fingerprint, then opens a new connection to each Pod to inspect the certificate actually served. One Pod keeps the prior fingerprint because its runtime loaded the file only at startup; the deployment controller rolls that Pod with readiness and disruption limits rather than assuming volume refresh was enough. For a proxy with hot secret delivery, verify the update acknowledgement and a new handshake without forcing a restart. Keep an older streaming connection open during the change to learn whether it can continue, whether it reauthenticates, and when it is drained. If the old key is merely expiring, a bounded overlap may be acceptable; if it is compromised, old sessions and ticket-resumption behavior require a shorter containment window. Test mismatched key and certificate files in a disposable instance and require the listener to reject that state or retain last-known-good material. The release is complete only when the fraction of Pods serving the new fingerprint reaches the declared threshold and old-session policy has been met.",
    "text",
    "Dispatch TLS rotation proof\nSecret generation: new key and leaf present\nEach Pod: new handshake serves expected fingerprint\nReload path: signal, watch, hot update, or rolling restart\nExisting stream: observed drain and reauthentication behavior\nFailure test: mismatched key and leaf rejected safely\nExit: old fingerprint and session count below threshold",
    "Polling P Pods for a fresh handshake is O(P); rolling restarts consume temporary capacity and can disrupt long streams. A hot reload saves restarts but needs its own failure and acknowledgement monitoring. Track Secret-to-serving delay, Pods with stale fingerprints, active old sessions, handshake errors, and restart-induced latency. Do not equate a new Secret resource with a successful user-facing rotation.",
    ["Do not infer active certificate state from a changed Secret alone.", "Do not check only an existing TLS connection after rotation.", "Do not restart every Pod simultaneously to force a new context."],
    ["devops/certificate-renewal-path", "devops/configmap-projection-refresh-boundary", "devops/graceful-pod-shutdown", "devops/http2-goaway-drain"],
)

lesson(
    "acme-issuance-failure-budget",
    "ACME issuance: test challenge reachability without burning production orders",
    "Automated certificate issuance depends on domain-control challenges and an issuer that can accept the request.",
    "A renewal controller may be healthy while HTTP routing, DNS propagation, delegated challenge permissions, or issuer rate limits block issuance. Repeating a failed production request faster does not repair a misrouted challenge and may consume an order or validation budget. Separate certificate-expiry time, first retry time, propagation allowance, issuer backoff, and rollback margin. Use a staging or disposable issuer path for negative tests where the provider supports one.",
    "A regional storefront uses DNS-based validation for a wildcard certificate. Before renewal season, the team checks that the delegated challenge zone is writable only by its issuance identity, that TXT records become visible from independent resolvers, and that cleanup does not remove another order's record. In an isolated drill, deny the DNS write permission and verify the Certificate request shows a clear failure without creating a loop of new private keys. Then restore permission and verify one order reaches Ready. A second drill changes the challenge delegation and measures propagation delay. The team tracks issuer response codes and retry guidance rather than hard-coding a guessed rate limit, which may change by provider or account. If renewal is blocked near expiry, use a preapproved fallback certificate or endpoint plan; do not turn off TLS verification to keep traffic moving. Roll new certificates to a canary listener and check the client matrix before replacing every edge. Monitor the shortest remaining lifetime across leaf and intermediates, not only the controller's successful scheduling of a renewal attempt.",
    "text",
    "Storefront issuance budget\nExpiry: leaf and chain dates recorded\nChallenge: delegated DNS write and public visibility tested\nRetry: issuer response and backoff respected\nMargin: propagation, deployment, and rollback time reserved\nCanary: client handshake matrix passes\nFallback: approved certificate or endpoint, never no-verify",
    "For D domains and R validation vantage points, challenge verification requires at least O(D × R) lookups; large fleets also consume DNS updates and issuer requests. Retrying every second can increase load without reducing propagation time. Measure time from renewal eligibility to issued certificate, failed challenge causes, issuer throttling, and time from issue to serving. Keep separate alerts for issuance failure and deployed certificate expiry because their remediation paths differ.",
    ["Do not hammer the production issuer after a challenge routing failure.", "Do not count a Ready certificate as deployed until a canary handshake proves it.", "Do not disable peer validation as an emergency renewal workaround."],
    ["devops/certificate-renewal-path", "devops/egress-dns-contract", "devops/dns-negative-cache-cutover", "devops/alert-design"],
)

lesson(
    "certificate-revocation-dependency",
    "Certificate revocation: test the client behavior and status-service dependency",
    "A revocation decision matters only if relying clients obtain and enforce it within the required time.",
    "Revocation may use a certificate revocation list, an online status response, a short certificate lifetime, or a workload identity system's own policy. Client implementations differ in what they check and what happens when the status service is unreachable. A private CA operator cannot assume its issuance controller publishes revocation data. Define the mechanism, distribution interval, cache lifetime, failure behavior, and fastest alternative for compromised credentials before an incident.",
    "An internal document-signing API accepts client certificates from partner gateways. The security team revokes a test client certificate in a disposable CA and probes each gateway class after publication. One proxy checks a refreshed list, while another trusts its cached list until a reload; a batch client does not check revocation at all. The team records those differences and uses a short-lived identity plus explicit access-policy denial for the batch path rather than claiming immediate revocation. Simulate an unavailable status endpoint and verify whether each gateway fails closed, uses a bounded cached response, or fails open; the chosen behavior is documented against its availability objective. Do not publish the CA key or the full server Secret as a way to distribute lists. For a compromised issuer key, leaf revocation alone is not enough because the adversary may mint new leaves; move to a new trust anchor and remove the old one on an emergency schedule. Monitor the age of revocation data as well as certificate expiry. A log entry saying 'revoked' is not proof that every relying process rejects the certificate.",
    "text",
    "Partner revocation acceptance\nIssuer: mechanism and publication owner known\nGateway A: revoked client rejected after list refresh\nGateway B: cache age and reload behavior measured\nBatch path: no revocation check; identity lifetime bounded\nStatus outage: declared fail behavior observed\nIssuer compromise: trust-anchor replacement plan invoked",
    "For C client classes and S status states, a basic matrix needs O(C × S) checks. Online status requests can add network dependence or latency, while local lists consume distribution and memory; choose based on actual clients and risk. Measure rejection time after revocation, oldest cached status, clients with no check, and availability impact during status-service failure. Short certificates reduce exposure but increase issuance and reload work.",
    ["Do not equate an issuer's revocation record with client rejection.", "Do not assume an issuance controller also operates a status service.", "Do not treat revoking leaves as sufficient after issuer-key compromise."],
    ["devops/credential-incident-rotation", "devops/private-ca-bundle-overlap", "devops/mesh-identity-boundaries", "devops/circuit-breaker-recovery-probes"],
)

lesson(
    "tls-private-key-compromise-response",
    "TLS key compromise: replace authority and end stale sessions",
    "A suspected private-key leak changes the objective from routine renewal to containment of an exposed identity.",
    "Issuing a new certificate with the same compromised key does not remove the attacker's ability to impersonate the service. Generate a new key under protected control, issue a matching certificate, remove exposed copies, and determine whether the issuer or only one leaf was affected. The response also examines active connections, session resumption, access logs, and dependent clients. Revocation can support containment where clients enforce it, but its actual effect must be tested.",
    "A settlement API key appears in a public CI artifact. The incident lead freezes the affected artifact, identifies every environment where the key is mounted, and records the certificate fingerprint and first known exposure time. The team generates a new key in its approved secret boundary, issues a new leaf, distributes it to a canary listener, and verifies fresh handshakes from required clients. It then rolls all listeners, drains long-lived connections on a bounded schedule, and rotates session-ticket material if the termination layer and threat model require it. Inspect registry, CI logs, build caches, and backups for other copies without copying the key into incident notes. Revoke the old leaf where the PKI supports it, but also test a client class that lacks revocation checking and rely on key replacement plus trust or identity controls there. If the CA signing key itself is suspect, activate the root or intermediate rollover plan rather than merely replacing one leaf. The incident record includes which certificate is currently served per endpoint and when the old identity ceased to be accepted. Do not claim complete containment solely because the Kubernetes Secret changed.",
    "text",
    "Settlement key incident\nScope: leaked key fingerprint and artifact locations\nNew identity: fresh key plus issued leaf\nDeployment: canary, all listeners, standby region\nSessions: old connection and ticket behavior checked\nRevocation: enforcement tested by client class\nCleanup: CI, registry, cache, and backup copies reviewed\nExit: old identity rejected on required paths",
    "Scanning A artifacts and E endpoints is at least O(A + E) investigative work; the real duration depends on retained logs, distribution lag, and client sessions. Emergency rotation may add handshake load and brief connection churn, so size spare capacity before draining. Measure time from exposure discovery to new key serving, old fingerprint presence, stale session count, and remaining accessible copies. Keep containment proof tied to actual endpoints, not a ticket checkbox.",
    ["Do not reissue a new certificate over the exposed private key.", "Do not paste the compromised key into incident documentation.", "Do not close the incident at Secret update while old listeners remain active."],
    ["devops/credential-incident-rotation", "devops/tls-secret-reload-connections", "devops/certificate-revocation-dependency", "devops/supply-chain-verification"],
)

lesson(
    "mtls-workload-identity-rollover",
    "mTLS workload identities: test both authentication and authorization on rotation",
    "Mutual TLS proves a peer holds an issued workload credential; authorization still decides what that identity may do.",
    "Rotating a workload certificate may change its key and serial while retaining its logical service identity. A trust-domain migration can change the identity itself, requiring policy updates at every accepting peer. A green handshake does not prove the caller has the right scope, and a policy that trusts every certificate from a CA may grant far more access than intended. Test issuance, bundle delivery, name validation, authorization, expiry, and removal of the retired identity as separate gates.",
    "A pricing worker moves from one internal trust domain to another. The platform distributes the new trust bundle to the inventory API before issuing the worker a new identity. The API temporarily accepts both exact workload identities for read-only price lookup, while only the currently approved identity can submit price changes. The team verifies a positive lookup and negative write using each identity, plus a certificate from the same CA belonging to an unrelated worker. A wrong-service certificate must fail policy even if its TLS chain is valid. After workloads report the new identity and no old sessions remain, the API removes the old principal and old trust root according to the migration plan. Simulate loss of the workload identity agent: new Pods should fail in a declared way rather than starting with a stale broad credential, while already running Pods follow their configured renewal and expiry behavior. Record identity issuance time, certificate lifetime, policy generation, and peer rejection results. If the mesh proxy hides certificate details from the application, collect the evidence from the proxy and an application-path request, not only from a controller status page.",
    "text",
    "Pricing identity migration\nNew bundle distributed before new leaf issued\nExact old and new identities scoped by operation\nUnrelated same-CA identity denied\nPositive read and negative write checked end to end\nIdentity agent outage behavior observed\nOld principal and root removed after client migration",
    "For W workloads and P accepting policies, migration review can approach O(W × P) unless identity usage is indexed. Dual-policy overlap expands the accepted principal set, so keep it short and auditable. Measure certificate age, agent renewal failures, authorization denials by identity, old-identity sessions, and time until retired trust is removed. More frequent rotation reduces credential lifetime but increases issuer and control-plane load.",
    ["Do not treat a valid TLS chain as permission for every API method.", "Do not change trust domain before receiving peers accept the new bundle.", "Do not keep the retired workload principal in policy indefinitely."],
    ["devops/mesh-identity-boundaries", "devops/federated-workload-identity", "devops/private-ca-bundle-overlap", "devops/service-account-token-boundaries"],
)


titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/tls-trust-rotation-project"
quiz_path = "quizzes/devops-tls-trust-decisions"
titles[project_path] = "Project: rotate service trust and contain an exposed TLS key"
titles[quiz_path] = "DevOps TLS trust and rotation decisions"
assert all(path in titles for item in specs for path in item["related"])
assert project_path not in by_path and quiz_path not in by_path


def links(paths):
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in dict.fromkeys(paths)
    ) + "</ul>"


for heading, summary, slugs in [
    ("TLS identity and chain checks", "Verify certificate paths and names from the real client matrix.", ["tls-chain-client-matrix", "tls-name-routing-validation"]),
    ("Trust and serving rotation", "Overlap private trust and prove processes serve the new certificate.", ["private-ca-bundle-overlap", "tls-secret-reload-connections"]),
    ("Issuance and revocation", "Test challenge paths, retry budgets, and actual client rejection.", ["acme-issuance-failure-budget", "certificate-revocation-dependency"]),
    ("Compromise and workload identity", "Replace exposed keys and constrain mTLS identities during migration.", ["tls-private-key-compromise-response", "mtls-workload-identity-rollover"]),
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
               category="DevOps", difficulty="Advanced", tags=["devops", "tls"],
               sort_order=22800 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
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
               summary="Verify chain delivery, trust overlap, process reload, revocation, and emergency key replacement.",
               difficulty="Advanced", sort_order=22890,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 10,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in project_related]}
project["body"] = (
    "<p>Build a disposable internal order API with a private CA, two client implementations, a gateway, and a second listener representing the recovery region. Keep its keys and test certificates out of version control. The exercise passes only when both client classes validate the served chain and name, a new root becomes trusted before new leaves appear, every listener serves the new identity, an unrelated mTLS caller is denied, and a compromised test key ceases to be accepted on the paths under test.</p>"
    "<h2>Map names, chains, and clients</h2><p>Record the intended external hostname, internal upstream name, certificate SANs, presented intermediates, and client trust anchors. Open fresh handshakes from a clean container and a second client stack against both listeners. In a disposable test, omit an intermediate, send wrong SNI, and replace the upstream certificate with a same-CA leaf for another service. Confirm each failure appears at the correct hop. Do not count a cached laptop handshake as coverage for the container or recovery listener.</p>"
    "<h2>Overlap and rotate trust</h2><p>Create an incoming CA and distribute a versioned bundle containing current and incoming roots to the clients. Verify the process actually loaded the bundle before issuing a new server leaf. Rotate the leaf and private key, then compare the Secret fingerprint with fresh handshakes to every Pod; test whether a long-lived connection survives or must drain. Remove the old root only after clients have migrated, and prove an old-only chain is rejected. Keep client trust data separate from the Secret containing the server private key.</p>"
    "<pre><code class=\"language-text\">Trust rotation acceptance\nClean clients build the intended chain at both listeners\nWrong name and wrong upstream identity are rejected\nNew root is loaded before new leaves are served\nFresh handshakes show the new key and leaf on every Pod\nOld long-lived sessions follow the declared drain rule\nSame-CA unrelated mTLS identity is denied by policy\nRevoked test identity is rejected where checks are required\nExposed key has been replaced, not reused</code></pre>"
    "<h2>Inject issuance and revocation faults</h2><p>Use a test issuer path. Deny the challenge writer's DNS permission, observe the issuance error and retry behavior, then restore it and verify a single intended certificate is issued. Revoke a test client identity and measure when each gateway class rejects it; if a class does not check revocation, record that limitation and test the alternative short-lived or policy-denial control. Make the status service unavailable and observe the configured fail behavior. Track leaf and intermediate expiry independently.</p>"
    "<h2>Contain a synthetic key leak</h2><p>Place only a disposable key in a restricted test artifact, then treat it as exposed. Generate a fresh key, deploy its certificate through a canary and full rotation, inspect old listener fingerprints and old session counts, and remove the test artifact. If the issuer key is the one exposed, use a trust-root replacement plan instead of leaf-only revocation. Report time to new identity, client failures, status-data age, and paths that still accept the old credential. Label any untested client or production gateway behavior unverified.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not copy a server private key into a client trust bundle.</li><li>Do not assume a Secret update proves the process serves a new certificate.</li><li>Do not present a revocation record as proof every client checks it.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*project_related, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>TLS trust rotation drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("Why test a certificate from more than one client class?", ["Trust stores and path-building behavior can differ", "The server always sends a different private key", "The CA changes on every request"], "One successful local handshake does not cover every supported client."),
    ("What should a server normally present with its leaf?", ["Required intermediate certificates", "Its private root key", "Every client's trust store"], "Clients construct a path to their own trusted anchor."),
    ("What comes first in a planned private-root rotation?", ["Distribute and verify client trust for the new root", "Remove the old root from every client", "Issue new leaves before any client update"], "Clients must trust the incoming chain before the server switches."),
    ("What does correct SNI routing fail to prove?", ["That the client validated the peer SAN", "That the server selected a listener", "That a connection reached a proxy"], "Name validation is a separate client-side check."),
    ("What proves a process loaded a renewed TLS Secret?", ["A fresh handshake to that process presents the expected certificate", "Only the Secret resource version changed", "The renewal controller is Ready"], "File delivery and active TLS context are separate states."),
    ("Why probe an existing stream during rotation?", ["Old sessions may persist after new handshakes use the new key", "It always receives a new certificate midstream", "It updates the CA automatically"], "The session's lifetime affects overlap and compromise containment."),
    ("What should happen after a failed ACME challenge?", ["Fix reachability or permission and respect issuer retry guidance", "Send unlimited new production orders", "Disable TLS verification"], "Repeated orders do not fix a broken challenge path."),
    ("What does a CA revocation record alone fail to prove?", ["Every relying client has fetched and enforced it", "The issuer has a serial number", "The leaf has an expiry time"], "Client checking and cache behavior must be measured."),
    ("What changes when a leaf private key is exposed?", ["Generate a fresh key and replace the identity", "Reissue a leaf using the same key", "Only rename the Secret"], "The exposed key remains usable if it is reused."),
    ("What if an issuer signing key is suspected compromised?", ["Replace the trust chain and remove the old issuer on an emergency plan", "Revoke only one leaf", "Keep the old root indefinitely"], "An attacker may create new leaves with the compromised issuer."),
    ("Does a valid mTLS chain authorize all API operations?", ["No, policy must match the exact workload identity and operation", "Yes, every same-CA client is trusted equally", "Only if the leaf is short-lived"], "Authentication and authorization are distinct."),
    ("What is the final gate in a workload trust-domain migration?", ["Remove the retired principal and root after client migration is proven", "Keep both principals forever", "Check only the proxy's Ready status"], "Temporary overlap must end with explicit denial of old identity."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on TLS chains, trust overlap, reloads, issuance, revocation, and mTLS identity.",
            sort_order=22900, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in project_related],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Choose the next certificate operation from observed chain, name, loaded key, client behavior, and identity policy. A renewed file or a successful handshake alone does not prove all relying paths are safe.</p>"
    "<h2>Review these lessons</h2>" + links(project_related)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-gitops-operations-decisions", "quizzes/devops-cloud-authorization-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not treat issuance as deployment.</li><li>Do not treat a valid mTLS chain as broad API authorization.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>TLS trust operations check</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": path, "title": titles[path]} for path in [project_path, quiz_path])

for source, targets in {
    "devops/certificate-renewal-path": ["devops/tls-chain-client-matrix", "devops/tls-secret-reload-connections", "devops/acme-issuance-failure-budget"],
    "devops/dns-tls-edge": ["devops/tls-chain-client-matrix", "devops/tls-name-routing-validation"],
    "devops/tls-sni-routing-proof": ["devops/tls-name-routing-validation"],
    "devops/secret-rotation-rollout": ["devops/private-ca-bundle-overlap", "devops/tls-secret-reload-connections"],
    "devops/credential-incident-rotation": ["devops/tls-private-key-compromise-response", "devops/certificate-revocation-dependency"],
    "devops/mesh-identity-boundaries": ["devops/mtls-workload-identity-rollover", "devops/private-ca-bundle-overlap"],
    "devops/federated-workload-identity": ["devops/mtls-workload-identity-rollover"],
    "devops/service-traffic-contract-project": [project_path],
}.items():
    row = by_path[source]
    row["body"] += "<h2>TLS trust operations follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1, "total_records": len(rows)}))
