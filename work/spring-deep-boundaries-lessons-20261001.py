"""Add original Spring Cassandra, Neo4j, Kubernetes and SAML lessons."""

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
    dict(slug="cassandra-conditional-reservation", section="spring/data-transactions", title="Spring Data Cassandra conditional insert: reserve one key once", summary="An IF NOT EXISTS write can reject a competing reservation for the same Cassandra primary key.", blocks=[
        ("A read is not a reservation", "Two dispatch workers ask whether parcel P-47 already has an active route claim. Both can read no row and then write. A regular Cassandra INSERT is an upsert, so one claim can replace the other. A conditional INSERT with IF NOT EXISTS makes the database decide which write applied. Spring Data Cassandra exposes this through InsertOptions. This is a lightweight transaction, with more coordination than an ordinary write. [[spring/tenant-idempotency-key-scope|Tenant-scoped idempotency]] must still be modeled in the key."),
        ("Use the result as the decision", "Do not return success merely because the CQL request completed without a driver exception. Inspect the applied result, then return either the accepted reservation or a conflict with the existing owner. A retry after a timeout is ambiguous until the caller reads the key or repeats an idempotent command. Keep the reservation row narrow and choose a partition key that does not send every tenant's claims to one hot partition."),
        ("Race two callers", "Start both requests at the same barrier with different worker IDs. Exactly one must report an applied write; the stored row must name that winner. Then drop the response after commit and retry the same command ID to test how the API resolves an unknown outcome. A repository mock cannot establish this behavior."),
    ], code="INSERT INTO route_claims (tenant_id, parcel_id, worker_id, claim_id)\nVALUES ('north-47', 'P-47', 'worker-21', 'claim-81')\nIF NOT EXISTS;", lang="cql", cost="A conditional write coordinates replicas and costs more latency than a normal upsert. Use it for a specific uniqueness invariant, not every telemetry event.", mistakes=["Do not use read-then-insert as the uniqueness guarantee.", "Do not equate a completed conditional request with an applied mutation.", "Do not retry a timed-out claim under a new command ID without checking the first outcome."], related=["spring/cassandra-partition-key-query", "spring/cassandra-versioned-write", "spring/tenant-idempotency-key-scope"]),
    dict(slug="cassandra-consistency-budget", section="spring/data-transactions", title="Spring Data Cassandra consistency: budget availability and staleness per operation", summary="A consistency level changes how many replicas must respond; it does not repair a bad partition key or make all reads transactional.", blocks=[
        ("Pick a contract, not a global badge", "A telemetry dashboard tolerates a slightly old reading; a route claim screen must not display an unconfirmed winner as final. Spring Data Cassandra query methods can declare a consistency level, while template options can set one per operation. Pair the choice with the replication topology and the application's failure rule. [[spring/cassandra-conditional-reservation|Conditional claims]] have separate serial-consistency behavior; a normal read level is not a substitute for IF NOT EXISTS."),
        ("Document the failure case", "A stricter read can fail when too few replicas are reachable. A weaker read can return older data. Neither choice makes a multi-row workflow atomic. Decide whether the API returns an unavailable error, an explicitly stale view, or a pending state. Avoid silently falling back to a weaker level for authorization or payment decisions."),
        ("Test with one replica unavailable", "Write an event, remove a replica from the test cluster, and compare each endpoint's observed result with its promised contract. Include a timeout and retry budget. Record whether a replayed write is safe; a request's idempotency and its consistency level solve different problems."),
    ], code="@Consistency(DefaultConsistencyLevel.LOCAL_QUORUM)\n@Query(\"SELECT * FROM route_claims WHERE tenant_id = ?0 AND parcel_id = ?1\")\nOptional<RouteClaim> findClaim(String tenantId, String parcelId);", lang="java", cost="Higher replica agreement can increase latency and reduce availability during failures. Measure the actual topology instead of choosing the strongest-looking constant everywhere.", mistakes=["Do not assume LOCAL_QUORUM works as intended without the correct replication factor and datacenter layout.", "Do not silently downgrade a security-sensitive read after a timeout.", "Do not call a consistency setting a multi-row transaction."], related=["spring/cassandra-conditional-reservation", "spring/cassandra-partition-key-query", "spring/dependency-readiness"]),
    dict(slug="cassandra-versioned-write", section="spring/data-transactions", title="Spring Data Cassandra @Version: a conflict is not a merge", summary="Spring Data Cassandra uses a conditional operation to reject a stale versioned single-entity write.", blocks=[
        ("Protect the observed row", "Two planners load the same dispatch rule at version 4. One lowers the route cap; the other edits the destination zone. Without a conflict check, a full-row save may erase the first decision. @Version adds the observed version to the mutation condition and raises an optimistic-locking failure when another writer has changed it. The mechanism relies on a lightweight transaction. [[spring/cassandra-conditional-reservation|Conditional insert]] uses the same family of database coordination."),
        ("Keep the command meaningful", "After conflict, reload the rule and re-evaluate the requested change. Replaying the stale object until it saves can reinstate an old cap. Do not assume batch operations enforce the entity's version: Spring Data Cassandra documents optimistic locking for single-entity operations. For a bulk import, write an explicit reconciliation and conflict report."),
        ("Prove both writers", "Load two copies in an integration test, save one and require the second to fail. Assert the winning rule remains intact. Repeat through any custom CQL path, because a direct update that omits the version condition can bypass the application's expected boundary."),
    ], code="@Table(\"dispatch_rules\")\nclass DispatchRule {\n    @PrimaryKey String ruleId;\n    String tenantId;\n    int maxRoutes;\n    String destinationZone;\n    @Version Long version;\n}", lang="java", cost="Each versioned write pays conditional-operation latency. High contention can make retries expensive; split unrelated rules or serialize commands when they repeatedly collide.", mistakes=["Do not retry the same stale entity without re-evaluating the command.", "Do not expect batch writes to enforce entity optimistic locking.", "Do not bypass the version predicate in a custom CQL update."], related=["spring/cassandra-conditional-reservation", "spring/cassandra-consistency-budget", "spring/jpa-optimistic-locking"]),
    dict(slug="neo4j-custom-query-cardinality", section="spring/data-transactions", title="Spring Data Neo4j custom query: return one coherent root record", summary="A custom Cypher query that returns the same root on several records can produce a partial or surprising mapped graph.", blocks=[
        ("A row is a mapping unit", "A shipment has three checkpoints and two assigned drivers. A query matching both collections can yield six records before aggregation. Returning the shipment root on each record forces Spring Data Neo4j to reconcile multiple fragments of one mapped entity. The outcome may differ from the graph the caller thought it loaded. For a graph-shaped repository return, collect related values into one record per root or use a focused projection. [[spring/neo4j-relationship-ownership|Graph ownership]] also matters when that result is saved."),
        ("Avoid accidental cartesian work", "Match each relationship pattern with a bounded tenant and shipment predicate. Use a query plan to confirm the root lookup uses the intended index before expanding paths. A full graph traversal for a detail page increases both database work and Java object allocation. If the UI only needs counts, return scalar counts instead of materializing every related node."),
        ("Verify shape and cost", "Create a shipment with three checkpoints and two drivers, then assert one root, three unique checkpoints and two unique drivers. Add 47 checkpoints and inspect records produced, row expansion and query latency. A simple two-node fixture can hide the cardinality error."),
    ], code="MATCH (shipment:Shipment {tenantId: $tenantId, shipmentId: $shipmentId})\nOPTIONAL MATCH (shipment)-[:HAS_CHECKPOINT]->(checkpoint:Checkpoint)\nWITH shipment, collect(DISTINCT checkpoint) AS checkpoints\nOPTIONAL MATCH (shipment)-[:ASSIGNED_TO]->(driver:Driver)\nRETURN shipment, checkpoints, collect(DISTINCT driver) AS drivers", lang="cypher", cost="Collecting one bounded subgraph avoids duplicate root records but consumes memory proportional to returned relationships. Cap expansion or project a summary when the fan-out is large.", mistakes=["Do not return one root entity on many unrelated result records and assume mapping is free.", "Do not match two high-cardinality relationship sets before narrowing the root.", "Do not load the entire graph when the caller needs only a count."], related=["spring/neo4j-relationship-ownership", "spring/neo4j-indexed-tenant-lookup", "spring/graphql-batch-tenant-scope"]),
    dict(slug="neo4j-indexed-tenant-lookup", section="spring/data-transactions", title="Spring Data Neo4j tenant lookup: constrain before traversing", summary="A tenant-scoped graph read should select a bounded root through an index before expanding relationships.", blocks=[
        ("The traversal starts at the predicate", "A dispatch screen fetches one shipment and its latest events. Matching every Shipment node and filtering the tenant late can traverse much more graph than the response needs. Store tenantId and shipmentId on the root and back the pair with a uniqueness constraint. That enforces the business key and gives the planner an indexed entry point. [[spring/tenant-claim-required|Tenant identity]] still comes from authentication, not a caller's free-form query parameter."),
        ("Measure the plan", "Use EXPLAIN and PROFILE on the actual query and data distribution. Check for an index seek on the constrained root, row counts after each relationship expansion, and unexpected eager operations. An index does not guarantee a good plan for an unbounded variable-length path. Require a maximum hop count and output cap."),
        ("Test duplicate and cross-tenant cases", "Insert the same shipmentId under two tenants and confirm both work. Attempt a duplicate within one tenant and require rejection. Request one tenant's shipment using another tenant's principal and assert no node or relationship properties escape."),
    ], code="CREATE CONSTRAINT shipment_tenant_key IF NOT EXISTS\nFOR (shipment:Shipment)\nREQUIRE (shipment.tenantId, shipment.shipmentId) IS UNIQUE;\n\nMATCH (shipment:Shipment {tenantId: $tenantId, shipmentId: $shipmentId})\nMATCH (shipment)-[:HAS_CHECKPOINT]->(checkpoint:Checkpoint)\nRETURN checkpoint ORDER BY checkpoint.recordedAt DESC LIMIT 47;", lang="cypher", cost="The constraint costs storage and write maintenance, while avoiding scans on bounded reads. Relationship fan-out can still dominate; index the entry point and cap the expansion.", mistakes=["Do not use an internal graph ID as tenant authorization.", "Do not assume an indexed root makes an unlimited traversal cheap.", "Do not trust a tenant ID supplied by the requester without binding it to the principal."], related=["spring/neo4j-custom-query-cardinality", "spring/tenant-claim-required", "spring/mongodb-tenant-unique-index"]),
    dict(slug="neo4j-relationship-properties-identity", section="spring/data-transactions", title="Spring Data Neo4j relationship properties: preserve edge identity", summary="A relationship with its own properties needs a mapped identity so saves can distinguish existing edges from new ones.", blocks=[
        ("The edge carries data", "A driver assignment has an assignedAt time and a dispatch reason. Those belong to the ASSIGNED_TO relationship, not necessarily to either node. Spring Data Neo4j maps such data with @RelationshipProperties, a @TargetNode and a @RelationshipId field for the generated relationship identity. Without that field, the mapper cannot safely reconcile an existing property-bearing edge on save. [[spring/neo4j-relationship-ownership|Partial graph saves]] remain a separate risk."),
        ("Keep business identity separate", "The internal relationship ID is for mapping continuity, not a public assignment number. Store an assignmentId property for external references and enforce its uniqueness in a command workflow. If history requires more than one assignment to the same driver, define whether old edges remain, are ended in place, or move to event nodes."),
        ("Exercise a second save", "Create an assignment, load it, change only its reason and save it again. Assert one relationship remains and its original assignedAt value survives. Then try a partial projection that omits assignments; it must not delete the historical edges merely because the projection was incomplete."),
    ], code="@RelationshipProperties\nclass DriverAssignment {\n    @RelationshipId Long graphRelationshipId;\n    String assignmentId;\n    Instant assignedAt;\n    String reason;\n    @TargetNode Driver driver;\n}", lang="java", cost="Property-bearing edges add mapping and storage work for each relationship. Large collections can make aggregate saves expensive; use focused commands and read projections when history grows.", mistakes=["Do not omit @RelationshipId from a relationship-properties class.", "Do not expose the internal relationship ID as a stable public identifier.", "Do not save a partial aggregate that silently drops historical edges."], related=["spring/neo4j-relationship-ownership", "spring/neo4j-custom-query-cardinality", "spring/neo4j-version-conflict"]),
    dict(slug="kubernetes-config-rbac", section="spring/production", title="Spring Cloud Kubernetes permissions: scope the service account to its reads", summary="A configuration starter that reads cluster objects needs Kubernetes API permission; the workload should receive only the verbs and namespace it uses.", blocks=[
        ("Name the API dependency", "A Boot service imports a ConfigMap through Spring Cloud Kubernetes. The client runs under the pod's service account, so a missing RoleBinding can make startup or refresh fail. A broad cluster-reader grant may make the example work but grants much more than a single service needs. Use a namespaced Role for the required resource types and verbs. [[spring/kubernetes-config-import-precedence|Config import]] defines what must be read; [[spring/kubernetes-config-reload-contract|reload]] may add watch access."),
        ("Separate ConfigMaps from Secrets", "A service that reads only a ConfigMap should not get secret access by default. If secrets are needed, identify the exact consumption path and test it with the deployment service account. List and watch can expose multiple objects in a namespace, so use a dedicated namespace or a carefully tested resource-name restriction where the API operation permits it."),
        ("Prove denial is contained", "Start the deployment with get permission but no watch and observe whether startup works while reload fails as expected. Remove ConfigMap access and assert a required import stops startup. The test must run inside the intended namespace; a developer's local kubeconfig can hide a missing service-account grant."),
    ], code="kind: Role\napiVersion: rbac.authorization.k8s.io/v1\nmetadata:\n  name: dispatch-config-reader\n  namespace: dispatch\nrules:\n  - apiGroups: [\"\"]\n    resources: [\"configmaps\"]\n    verbs: [\"get\", \"list\", \"watch\"]", lang="yaml", cost="A namespaced Role limits exposure, but watches still consume API connections and events. Remove unused verbs and resources after measuring the actual client behavior.", mistakes=["Do not bind a cluster-wide reader role to one configuration consumer.", "Do not grant secret reads when the service only uses ConfigMaps.", "Do not validate permissions with a developer kubeconfig instead of the pod service account."], related=["spring/kubernetes-config-import-precedence", "spring/kubernetes-config-reload-contract", "spring/kubernetes-probe-timing"]),
    dict(slug="kubernetes-probe-timing", section="spring/production", title="Spring Boot Kubernetes probes: separate startup, readiness and liveness", summary="Startup, readiness and liveness probes answer different questions and should not share one failure rule.", blocks=[
        ("The three decisions differ", "A service takes time to warm a route cache. A startup probe can allow that initialization window without a premature restart. Readiness determines whether the pod should receive requests; liveness should report a locally unrecoverable state, not every temporary database outage. Boot Actuator exposes separate liveness and readiness health groups in Kubernetes. [[spring/liveness-readiness-separation|The availability model]] is already part of the application."),
        ("Budget timing from measurements", "Set failure thresholds from cold-start and shutdown measurements, not a copied manifest. If readiness begins before the service can serve its promised request, traffic fails. If liveness includes a shared downstream dependency, a database outage can restart every replica at once. [[spring/readiness-during-termination|Termination readiness]] needs enough time for endpoints to stop routing new work."),
        ("Run a rollout failure drill", "Start with a deliberately slow cache, disconnect the database, then roll out a new version. Confirm startup does not restart a healthy warming pod, readiness removes an unusable pod, and a downstream outage does not trigger a restart storm."),
    ], code="startupProbe:\n  httpGet: {path: /actuator/health/liveness, port: 8080}\n  periodSeconds: 5\n  failureThreshold: 24\nreadinessProbe:\n  httpGet: {path: /actuator/health/readiness, port: 8080}\n  periodSeconds: 5\nlivenessProbe:\n  httpGet: {path: /actuator/health/liveness, port: 8080}\n  periodSeconds: 10", lang="yaml", cost="Frequent probes add small HTTP work. Aggressive failure thresholds cost availability through needless restarts; generous thresholds delay detection of a truly broken pod.", mistakes=["Do not include every external dependency in liveness.", "Do not copy startup timing without measuring the coldest deployment path.", "Do not probe a management port that is inaccessible to the kubelet."], related=["spring/liveness-readiness-separation", "spring/readiness-during-termination", "spring/kubernetes-config-rbac"]),
    dict(slug="kubernetes-config-watcher-scope", section="spring/production", title="Spring Cloud Kubernetes watcher scope: filter before broadcasting refresh", summary="A configuration watcher should react only to the namespace and objects owned by the workload.", blocks=[
        ("A watch can be too broad", "A cluster has dozens of dispatch deployments. If every service watches every ConfigMap, a routine edit can produce irrelevant refresh work across replicas. Spring Cloud Kubernetes exposes reload namespace and label filters for event-based monitoring. Tie each application to its named source and test the label scheme. [[spring/kubernetes-config-rbac|RBAC]] is the access boundary; a label filter is only operational scoping."),
        ("Choose what refresh means", "Even a correctly filtered event does not ensure a pooled client adopts new credentials. Use [[spring/kubernetes-config-reload-contract|the reload contract]] to decide between property refresh and a controlled restart. Keep a per-pod configuration revision in observability so operators can see whether every replica has advanced."),
        ("Test one relevant and one irrelevant change", "Update the target ConfigMap and require exactly the intended services to adopt it. Update an unrelated ConfigMap in the same namespace and verify no refresh. Then remove a watched key and confirm the application's documented fallback or failure behavior rather than assuming old bean state disappeared."),
    ], code="spring:\n  cloud:\n    kubernetes:\n      reload:\n        enabled: true\n        mode: event\n        namespaces: [dispatch]\n        monitoring-config-maps: true\n        monitoring-secrets: false", lang="yaml", cost="A watch keeps an API connection and processes change events. Narrow scopes reduce unnecessary reloads, but verification still needs an end-to-end deployment test.", mistakes=["Do not treat a label filter as a security boundary.", "Do not refresh every replica for an unrelated namespace's edit.", "Do not claim a watcher updated a bean that only reads its value at construction."], related=["spring/kubernetes-config-rbac", "spring/kubernetes-config-reload-contract", "spring/cloud-config-refresh-boundary"]),
    dict(slug="saml-local-vs-single-logout", section="spring/security", title="Spring Security SAML logout: local session versus single logout", summary="Local logout ends this application's session; SAML single logout exchanges signed protocol messages with the asserting party.", blocks=[
        ("Decide which session ends", "A dispatcher clicks Sign out. A local logout clears this service provider's authenticated session but can leave the identity-provider session active, allowing another login without a password prompt. SAML single logout can involve the asserting party and other service providers when the IdP supports it. Spring Security supports both relying-party and asserting-party initiated flows. [[spring/oauth2-login-session|Session ownership]] still determines what the application invalidates locally."),
        ("Configure the protocol as a pair", "Single logout requires the asserting party to support it, compatible endpoints, and signing credentials on the relying party. The default SAML logout processing endpoint is /logout/saml2/slo. A changed endpoint must be reflected in both registration and IdP configuration. Keep a separate local-only endpoint if the product intentionally offers it; label its effect accurately."),
        ("Test both directions", "Run an RP-initiated logout and inspect the signed request and response. Then initiate logout at the IdP and assert the local session stops authorizing requests. Also simulate an unavailable IdP: define whether the local session is cleared, whether retry is possible, and what the user sees."),
    ], code="http.logout(local -> local.logoutUrl(\"/logout\"))\n    .saml2Logout(saml -> saml.logoutUrl(\"/saml2/logout\"));", lang="java", cost="Single logout adds signed XML exchanges, network latency and certificate maintenance. Local logout is cheaper but cannot promise termination of the IdP session.", mistakes=["Do not label local logout as logout from every federated application.", "Do not enable single logout without IdP support and signing credentials.", "Do not change the SAML logout endpoint only on the application side."], related=["spring/saml-relying-party-metadata", "spring/saml-session-revocation", "spring/oauth2-login-session"]),
    dict(slug="saml-session-revocation", section="spring/security", title="Spring SAML session revocation: closing the browser is not deprovisioning", summary="A valid local session can outlive an IdP account change unless the application has an expiry or revocation path.", blocks=[
        ("Login is a point-in-time decision", "A contractor signs in through SAML, then loses access at the IdP. Their browser still holds an application session. The service provider does not automatically revalidate every request against the IdP. Choose a session lifetime, idle timeout and emergency invalidation workflow that match the business risk. [[spring/saml-attribute-authority-mapping|Local authorities]] also need a refresh or revocation rule."),
        ("Make invalidation work across replicas", "A multi-pod deployment cannot rely on one pod's private session map if the user can be routed elsewhere. Use a shared session store or another centralized revocation mechanism, and bind the stored subject to the IdP registration and tenant. Rotate the session ID at login. [[spring/session-fixation-login|Fixation protection]] addresses a different takeover route."),
        ("Drill a real account removal", "Sign in, remove the user from a privileged group at the IdP, and call the protected endpoint before and after the chosen revocation event. Verify the documented maximum access window. Repeat while the IdP is unavailable and after one application replica restarts."),
    ], code="record FederatedSessionKey(String registrationId,\n                           String subject, String tenantId) {}\n// Index active sessions by this trusted key for targeted revocation.", lang="java", cost="A shared session store adds storage and lookup I/O. Shorter lifetimes reduce the maximum stale-access window but cause more authentication exchanges.", mistakes=["Do not assume an IdP group change instantly changes an existing local session.", "Do not key revocation by email alone across multiple IdPs.", "Do not invalidate only one pod's in-memory session in a replicated deployment."], related=["spring/saml-local-vs-single-logout", "spring/saml-attribute-authority-mapping", "spring/session-fixation-login"]),
    dict(slug="saml-certificate-rollover", section="spring/security", title="Spring SAML certificate rollover: overlap trust without accepting unknown keys", summary="An IdP signing-key change needs a bounded trust transition and a rejection test for an untrusted signature.", blocks=[
        ("A new certificate is a planned change", "The identity provider announces a signing-key rotation. The relying party verifies SAML signatures against configured trusted credentials. If the old key disappears before the app recognizes the new one, login fails; if every key from newly fetched unsigned metadata is accepted, trust can be widened without review. [[spring/saml-signature-clock-boundary|Signature validation]] remains mandatory throughout the rollout."),
        ("Stage, observe, remove", "Validate the new certificate's identity through an agreed channel, add it alongside the still-valid old key for the overlap window, and observe which key signs actual assertions. Remove the old credential after the IdP completes rotation and the maximum in-flight login window passes. Keep the registration-specific trust set separate for every IdP."),
        ("Test a forged and an old response", "A signed response using the planned new key should work during overlap; a response signed by an unrelated key must fail. After old-key removal, the old response must fail too. Run the check through the production proxy and actual metadata endpoint so an issuer or ACS mismatch is visible."),
    ], code="// Trust-store rollout invariant:\n// before: {currentKey}\n// overlap: {currentKey, nextKey}\n// after: {nextKey}\n// Never accept an assertion merely because its XML carries a key.", lang="java", cost="Overlapping trusted keys temporarily widen the accepted signing set. Bound that window, audit its start and end, and avoid a login outage from an uncoordinated cutover.", mistakes=["Do not disable signature verification during rotation.", "Do not trust an assertion's embedded certificate without registration policy.", "Do not leave a retired IdP key trusted indefinitely."], related=["spring/saml-signature-clock-boundary", "spring/saml-relying-party-metadata", "spring/saml-local-vs-single-logout"]),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"spring/" + item["slug"]: item["title"] for item in lessons})
subjects = {"spring/data-transactions": "spring-data", "spring/production": "spring-production", "spring/security": "spring-security"}
for number, item in enumerate(lessons):
    path = "spring/" + item["slug"]
    assert path not in by_path, path
    for target in item["related"]:
        assert target in titles, (path, target)
    body = "<p>" + prose(item["summary"]) + "</p>"
    for heading, content in item["blocks"]:
        body += "<h2>" + html.escape(heading) + "</h2><p>" + prose(content) + "</p>"
    body += ('<h2>Implementation sketch</h2><pre><code class="language-' + item["lang"] + '">'
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
        subject=subjects[item["section"]],
        tags=["spring", "spring-boot", item["section"].split("/")[-1], item["slug"]],
        sort_order=5300 + number, published_at=stamp, created_at=stamp, updated_at=stamp,
    )
    row["data"] = {
        "subject_root": "spring/spring-boot", "section_path": item["section"],
        "kind": "tutorial", "content_format": "html", "seo_ready": True,
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial",
        "framework_version": "Spring Boot 4 / Spring Framework 7 / current Spring Data and Spring Cloud where relevant",
        "java_version": "21 or later",
        "verification_suite": "Official API contract review; implementation sketch not compiled",
        "related": [{"path": target, "title": titles[target]} for target in item["related"]],
    }
    rows.append(row)
    by_path[path] = row

for section, heading in {
    "spring/data-transactions": "Cassandra and Neo4j write and query contracts",
    "spring/production": "Kubernetes workload permissions and probes",
    "spring/security": "SAML logout, sessions and certificate rollover",
}.items():
    paths = ["spring/" + item["slug"] for item in lessons if item["section"] == section]
    hub = by_path[section]
    hub["data"]["modules"].append({
        "title": heading, "summary": "Practical operating contracts, costs and failure drills.", "lessons": paths,
    })
    hub["body"] += "<h2>" + heading + "</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
        for path in paths
    ) + "</ul>"
    hub["updated_at"] = stamp

parent = by_path["spring/spring-boot"]
parent["body"] += "<h2>Conditional writes, graph queries, cluster access and SAML sessions</h2><ul>" + "".join(
    '<li><a href="/spring/' + item["slug"] + '">' + html.escape(item["title"]) + "</a></li>"
    for item in lessons
) + "</ul>"
parent["updated_at"] = stamp
for source, target in [
    ("spring/cassandra-partition-key-query", "spring/cassandra-conditional-reservation"),
    ("spring/cassandra-paging-state", "spring/cassandra-consistency-budget"),
    ("spring/cassandra-ttl-tombstone-budget", "spring/cassandra-versioned-write"),
    ("spring/neo4j-relationship-ownership", "spring/neo4j-custom-query-cardinality"),
    ("spring/neo4j-version-conflict", "spring/neo4j-indexed-tenant-lookup"),
    ("spring/neo4j-transaction-boundary", "spring/neo4j-relationship-properties-identity"),
    ("spring/kubernetes-config-import-precedence", "spring/kubernetes-config-rbac"),
    ("spring/liveness-readiness-separation", "spring/kubernetes-probe-timing"),
    ("spring/kubernetes-config-reload-contract", "spring/kubernetes-config-watcher-scope"),
    ("spring/saml-relying-party-metadata", "spring/saml-local-vs-single-logout"),
    ("spring/saml-attribute-authority-mapping", "spring/saml-session-revocation"),
    ("spring/saml-signature-clock-boundary", "spring/saml-certificate-rollover"),
]:
    row = by_path[source]
    row["body"] += ('<h2>Related boundary</h2><p><a href="/' + target + '">'
                    + html.escape(titles[target]) + "</a></p>")
    row["updated_at"] = stamp

FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "Spring articles; new total", sum(
    row["path"].startswith("spring/") and row["type"] == "article" for row in rows
))
