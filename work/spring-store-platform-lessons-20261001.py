"""Add original Spring store, Kubernetes and SAML boundary lessons."""

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
    dict(slug="cassandra-partition-key-query", section="spring/data-transactions", title="Spring Data Cassandra partition keys: model the read before the row", summary="A Cassandra partition key decides where rows live and which reads stay bounded.", blocks=[
        ("Start with the access path", "A parcel event viewer reads one tenant's events for one parcel in descending event time. Put tenant and parcel in the partition key; place event time in the clustering columns. An entity with only an event ID as its key cannot serve this read without another table or a scan. [[spring/tenant-jdbc-predicate|Tenant predicates]] in a relational query do not repair a Cassandra table whose partition key omits tenant ownership."),
        ("Watch partition growth", "A single tenant-wide partition can grow without bound. Using the parcel ID reduces that risk, but a parcel with millions of events may still need a time bucket. Bucket size is a workload decision: smaller buckets spread storage and require more reads for a long history. State the maximum requested time window before choosing the bucket."),
        ("Verify the actual query", "Create two tenants with the same parcel identifier, then request one tenant's recent events. Confirm the generated CQL selects by the full partition key and does not use ALLOW FILTERING. Measure partition size and p95 latency under the expected event distribution."),
    ], code="@Table(\"parcel_events\")\nclass ParcelEvent {\n    @PrimaryKeyColumn(ordinal = 0, type = PrimaryKeyType.PARTITIONED)\n    String tenantId;\n    @PrimaryKeyColumn(ordinal = 1, type = PrimaryKeyType.PARTITIONED)\n    String parcelId;\n    @PrimaryKeyColumn(ordinal = 2, type = PrimaryKeyType.CLUSTERED,\n        ordering = Ordering.DESCENDING)\n    Instant recordedAt;\n    String status;\n}", lang="java", cost="Reads within one known partition avoid a cluster-wide scan, but writes and stored rows still concentrate on hot keys. A bucket spreads load at the cost of extra reads.", mistakes=["Do not add ALLOW FILTERING to hide a missing access path.", "Do not use a tenant-only partition key when one tenant can produce an unbounded event stream.", "Do not assume Cassandra can sort arbitrary columns outside clustering order."], related=["spring/tenant-jdbc-predicate", "spring/mongodb-tenant-unique-index", "spring/cassandra-paging-state"]),
    dict(slug="cassandra-ttl-tombstone-budget", section="spring/data-transactions", title="Spring Data Cassandra TTL: expiry is a storage and query cost", summary="TTL expires data logically, while tombstones and compaction shape the physical cleanup cost.", blocks=[
        ("Expiry does not erase work instantly", "A delivery telemetry row may be useful for 47 days. Assigning a TTL bounds its logical lifetime, but expired cells become tombstones until compaction can safely discard them. A wide range query across expired data can spend time scanning tombstones. [[spring/cassandra-partition-key-query|Partition design]] limits the range that query must examine."),
        ("Choose one retention contract", "Do not mix short TTLs, manual deletes and long unbounded partitions without a deletion plan. If a legal hold can extend retention, put held records in a separately modeled table; do not promise that changing a TTL later restores expired values. Use the table's default TTL or per-write options according to the actual retention rule, then inspect the resulting CQL."),
        ("Test over time", "Write a row with a short test TTL, verify it is readable before expiry and absent afterward, then run a representative range query on a data set containing expired rows. Compare read latency and tombstone warnings; a unit test of the Java entity cannot prove compaction behavior."),
    ], code="CREATE TABLE parcel_telemetry (\n    tenant_id text, parcel_id text, recorded_at timestamp, reading text,\n    PRIMARY KEY ((tenant_id, parcel_id), recorded_at)\n) WITH default_time_to_live = 4060800;", lang="cql", cost="TTL saves explicit delete traffic but creates tombstones. The query cost depends on partition shape, expiry density and compaction policy, not just row count.", mistakes=["Do not equate TTL expiry with immediate disk reclamation.", "Do not assume a later TTL increase revives an expired record.", "Do not test only point reads when production uses range reads."], related=["spring/cassandra-partition-key-query", "spring/cassandra-paging-state", "spring/batch-input-snapshot"]),
    dict(slug="cassandra-paging-state", section="spring/data-transactions", title="Spring Data Cassandra paging state: continue the same bounded query", summary="A paging state resumes a Cassandra result set; it is not a portable page number or stable snapshot.", blocks=[
        ("Keep the query fixed", "A parcel timeline endpoint returns one partition in small batches. Spring Data Cassandra can carry a driver paging state or CassandraScrollPosition into the next request. The token belongs to the original statement and its parameters. If tenant, parcel, filters or page size change, discard it and start again. [[spring/cassandra-partition-key-query|The partition key]] remains mandatory."),
        ("Treat the token as opaque", "Do not decode a paging state into an offset or expose it as proof of authorization. Bind it to the authenticated tenant and query fingerprint in your API layer, and set an expiry. Concurrent writes can affect later pages; if the product needs a fixed historical view, materialize a snapshot or choose a cutoff and test its semantics."),
        ("Probe discontinuity", "Read one page, insert an event, then request the next page. Assert the API's documented ordering and duplicate handling. Also replay a token under a different tenant and require rejection before any database call."),
    ], code="Query pageQuery = Query.query(\n    Criteria.where(\"tenant_id\").is(tenantId)\n        .and(\"parcel_id\").is(parcelId))\n    .limit(47);\n// A validated CassandraScrollPosition may be attached for continuation.", lang="java", cost="Each page limits response memory, but a client can still walk a large partition. Apply a request budget and avoid counting all rows just to display a page number.", mistakes=["Do not represent a paging state as an integer offset.", "Do not reuse a token with different query parameters.", "Do not trust a token to authorize access to a tenant's data."], related=["spring/cassandra-partition-key-query", "spring/cassandra-ttl-tombstone-budget", "spring/tenant-claim-required"]),
    dict(slug="neo4j-relationship-ownership", section="spring/data-transactions", title="Spring Data Neo4j relationships: save only the graph you own", summary="Saving a mapped graph can reconcile relationships, so partial graph views need a write boundary.", blocks=[
        ("A loaded subgraph is not the whole graph", "A shipment node links to checkpoints and drivers. A detail view loads only checkpoints, edits one property, then saves the root. Depending on its mapping and save path, missing relationships can be interpreted as removed. Use a write model that loads the relationship set it owns, or issue a focused Cypher update for a scalar change. [[spring/mongodb-versioned-document|Document saves]] have a similar stale-copy hazard, though the graph mapping rules differ."),
        ("Separate relationship direction from authority", "A relationship's direction describes storage and traversal; it does not authorize a caller. Scope every lookup to tenantId and the authenticated principal. Put a database constraint on the tenant-scoped business key so two concurrent creates cannot produce duplicate shipment nodes."),
        ("Make deletion visible in tests", "Persist a shipment with two drivers, load a projection containing one, save it, then assert both database relationships still exist if the command promised a property-only edit. Use a real Neo4j instance; mocks cannot show graph reconciliation."),
    ], code="MATCH (shipment:Shipment {tenantId: $tenantId, shipmentId: $shipmentId})\nSET shipment.status = $newStatus\nRETURN shipment.shipmentId AS shipmentId, shipment.status AS status", lang="cypher", cost="A narrow update avoids loading and mapping an unrelated relationship graph. Add an index or constraint for the tenant and business ID predicate, then inspect its query plan.", mistakes=["Do not save a partial graph as though it represented every relationship.", "Do not treat relationship direction as an authorization check.", "Do not use an internal node ID as the only public business identifier."], related=["spring/neo4j-transaction-boundary", "spring/neo4j-version-conflict", "spring/tenant-claim-required"]),
    dict(slug="neo4j-transaction-boundary", section="spring/data-transactions", title="Spring Data Neo4j transaction: keep the command inside one managed unit", summary="Neo4jClient participates in Spring transactions; an unrelated driver session can escape the command boundary.", blocks=[
        ("Choose one graph mutation", "Assigning a driver to a shipment creates or updates a relationship and writes an audit node. If both must commit together, enter through a Spring-managed @Transactional service and use Neo4jClient or repositories bound to that transaction. A raw driver session created outside it is a different unit of work. [[spring/transaction-thread-boundary|Thread switches]] do not carry an imperative transaction."),
        ("Keep remote calls outside", "Do not call a fleet API midway and tell the caller all effects rolled back if the database later fails. Commit the graph state and an outbox event together, then deliver externally. [[spring/relay-transaction-boundaries|Outbox boundaries]] make that obligation explicit."),
        ("Prove rollback", "Force the audit write to fail after the relationship update and assert neither graph change survives. Repeat through a separately obtained driver session to reveal an escape. The sketch is a service boundary; it needs repository implementations and a Neo4j-backed integration test."),
    ], code="@Transactional\npublic void assignDriver(AssignmentCommand command) {\n    shipmentGraph.assign(command.tenantId(), command.shipmentId(),\n        command.driverId());\n    assignmentAudit.record(command.assignmentId(), command.tenantId());\n}", lang="java", cost="A transaction holds a connection and locks relevant graph data. Keep the work bounded; a remote call lengthens contention and cannot join the database commit.", mistakes=["Do not assume a raw driver session joins a Spring transaction automatically.", "Do not start an async worker inside the transaction and expect it to inherit context.", "Do not include an external HTTP side effect in the rollback promise."], related=["spring/neo4j-relationship-ownership", "spring/transaction-thread-boundary", "spring/relay-transaction-boundaries"]),
    dict(slug="neo4j-version-conflict", section="spring/data-transactions", title="Spring Data Neo4j version conflicts: reject a stale graph update", summary="A mapped @Version property detects competing writes to the same node when both use the versioned mapping path.", blocks=[
        ("A last write can erase a decision", "Two dispatchers load shipment 47 at the same version. One marks it held; the other assigns it for departure. A mapped @Version property lets a stale save fail instead of replacing the newer state. That does not resolve the business conflict. Reload the node, apply the current policy, and ask the caller to retry if the decision changed."),
        ("Keep other writers honest", "A custom Cypher SET that ignores the version can bypass a mapped version check. Either route all competing writes through the versioned mapping path or include a version predicate and increment in custom queries. [[spring/neo4j-relationship-ownership|Relationship writes]] also need careful aggregate ownership; a node version is not a global lock over every related node."),
        ("Run a two-writer test", "Load two copies, commit one, then require the second save to fail. Repeat with each custom query used by the service. Assert the winning status and version remain unchanged after the rejected write."),
    ], code="@Node(\"Shipment\")\nclass Shipment {\n    @Id String shipmentId;\n    String tenantId;\n    String status;\n    @Version Long version;\n}", lang="java", cost="Version checks add conflict handling and retries. Hot shipment nodes may need a command queue or narrower state transitions instead of unlimited retry loops.", mistakes=["Do not auto-retry a stale decision without re-evaluating its preconditions.", "Do not bypass version checks in a custom Cypher update.", "Do not assume one node version protects all related nodes."], related=["spring/neo4j-relationship-ownership", "spring/jpa-optimistic-locking", "spring/mongodb-versioned-document"]),
    dict(slug="kubernetes-config-import-precedence", section="spring/production", title="Spring Cloud Kubernetes config import: make source precedence explicit", summary="A kubernetes: Config Data import reads cluster sources during startup and follows Boot's configuration ordering.", blocks=[
        ("The import is a startup contract", "A dispatch service reads a ConfigMap for route limits. With Spring Cloud Kubernetes' config starter present, spring.config.import can request kubernetes: during Config Data processing. The imported values take precedence over values in the document that declares the import. Other sources, including environment and command-line inputs, still have their own precedence. [[spring/boot-config-source-priority|Boot source order]] is the underlying rule."),
        ("Fail or degrade deliberately", "A required import should stop startup when the service cannot obtain its expected configuration. An optional import only makes sense if safe defaults exist and a deployment test checks them. A pod with no API permissions can start with a surprising fallback if the failure path is treated as optional. [[spring/boot-required-config-import|Required imports]] make missing state visible."),
        ("Test the deployed service account", "Run the pod under its real service account. Change one value in the ConfigMap, one in the base file and one in an environment variable, then assert the winning value. Repeat with the ConfigMap absent and with API access denied."),
    ], code="spring:\n  application:\n    name: dispatch-service\n  config:\n    import: \"kubernetes:\"\ndispatch:\n  max-active-routes: 47", lang="yaml", cost="Startup performs cluster API reads and can depend on API availability. Limit the requested namespaces and objects; a broad watch or read grant increases both load and access surface.", mistakes=["Do not assume the imported ConfigMap overrides every other Boot source.", "Do not mark an import optional without safe defaults and a failure test.", "Do not grant cluster-wide read permission for one namespace's configuration."], related=["spring/boot-config-source-priority", "spring/boot-required-config-import", "spring/kubernetes-config-reload-contract"]),
    dict(slug="kubernetes-config-reload-contract", section="spring/production", title="Spring Cloud Kubernetes reload: decide which changes need a restart", summary="Detecting a changed ConfigMap does not guarantee every live bean or connection has adopted the new value.", blocks=[
        ("Separate detection from application", "A route limit changes in a ConfigMap. Spring Cloud Kubernetes can detect changes and trigger a refresh, restart or shutdown strategy, depending on configuration and version. A refreshed @ConfigurationProperties bean may see a new value, but a connection pool created from the old setting may not. [[spring/cloud-config-refresh-boundary|Refresh boundaries]] need an inventory of stateful beans."),
        ("Use a rollout for hard state", "Credential rotations, TLS material and connection targets often deserve a controlled pod restart with readiness gating. If a watcher is used, grant only the resources and namespace it monitors. The default reload setting is disabled in current Spring Cloud Kubernetes documentation; do not build an operational promise around an unstated default."),
        ("Observe the change", "Patch one ConfigMap key, wait for the configured detection path, then call a behavior endpoint on every replica. Verify old requests finish, new requests use the intended value, and the pod remains ready. Also delete a key and check fallback behavior rather than assuming refresh restores its old value."),
    ], code="spring:\n  cloud:\n    kubernetes:\n      reload:\n        enabled: true\n        monitoring-config-maps: true\n        monitoring-secrets: false", lang="yaml", cost="Event watchers hold API watches; polling produces repeated reads. Restarts trade brief capacity for a clean bean graph. Choose by measured change frequency and state ownership.", mistakes=["Do not equate a watch event with a fully reconfigured application.", "Do not use live refresh for a bean that only reads configuration at construction time.", "Do not allow a rollout to drop readiness before in-flight work drains."], related=["spring/kubernetes-config-import-precedence", "spring/cloud-config-refresh-boundary", "spring/readiness-during-termination"]),
    dict(slug="kubernetes-discovery-vs-dns", section="spring/production", title="Spring Cloud Kubernetes discovery: choose API lookup or Service DNS", summary="DiscoveryClient can read Kubernetes Services, while ordinary Service DNS often needs fewer permissions.", blocks=[
        ("Use the simpler resolution contract", "A dispatch API calls a pricing service by stable Kubernetes Service name. Standard DNS already resolves that name within the cluster; no Spring Cloud Kubernetes discovery starter is required just to call it. DiscoveryClient becomes useful when the application needs service metadata, filtered instances or a Spring abstraction that inspects Kubernetes objects."),
        ("Account for permissions and churn", "API-based discovery needs appropriate service or endpoint read permissions and must cope with changing instances. DNS delegates that to Kubernetes networking. Neither choice excuses an unbounded HTTP call: set connection and response deadlines, and use [[spring/cloud-circuit-breaker|failure policy]] for unavailable downstream services."),
        ("Test from inside the namespace", "Deploy with the intended service account and namespace, resolve the Service name, then revoke API read permissions. DNS-only callers should still work. If using DiscoveryClient, assert the chosen metadata and namespace rules with multiple similarly named Services."),
    ], code="pricing:\n  service-host: pricing-service\n  connect-timeout: 2s\n  response-timeout: 5s", lang="yaml", cost="DNS calls avoid a discovery watch and extra API grants. API discovery can add metadata but costs permissions, watch traffic and more application behavior to test.", mistakes=["Do not add API-based discovery only to resolve a stable Service name.", "Do not assume a short service name resolves across namespaces without a DNS rule.", "Do not let discovery success imply the downstream request cannot time out."], related=["spring/kubernetes-config-import-precedence", "spring/dependency-readiness", "spring/cloud-circuit-breaker"]),
    dict(slug="saml-relying-party-metadata", section="spring/security", title="Spring Security SAML relying party: align registration, ACS and metadata", summary="A SAML relying-party registration binds service-provider settings to an asserting party and its trust material.", blocks=[
        ("Treat metadata as a protocol contract", "A corporate identity provider posts a response to the service provider's assertion consumer service, or ACS. Spring Security resolves a RelyingPartyRegistration to validate that exchange. Its default login processing path includes /login/saml2/sso/{registrationId}; metadata can be published per registration. The IdP and app must agree on the issuer, ACS and credentials. [[spring/trusted-forwarded-headers|Forwarded host handling]] matters when a proxy changes the public origin."),
        ("Keep tenants separate", "If two employers use different IdPs, give each a distinct registration and bind the login entry point to the tenant's trusted registration. Never let a user-supplied issuer string select an arbitrary registration. Store trust material through a reviewed rotation path and verify metadata changes before activation."),
        ("Run a real protocol test", "Import the service-provider metadata into a test IdP, complete one login, then change the ACS or issuer and assert failure. Repeat behind the production proxy so generated URLs use the public origin."),
    ], code="http.authorizeHttpRequests(requests -> requests\n    .requestMatchers(\"/saml2/metadata/**\").permitAll()\n    .anyRequest().authenticated())\n    .saml2Login(Customizer.withDefaults())\n    .saml2Metadata(Customizer.withDefaults());", lang="java", cost="Each login exchanges signed XML and creates a local authenticated session. Multi-IdP setups add registration and certificate rotation work; cache only metadata according to a defined freshness policy.", mistakes=["Do not change the login processing path without updating the ACS in metadata and the IdP.", "Do not trust an IdP solely because its issuer string looks familiar.", "Do not expose an internal proxy host in published service-provider metadata."], related=["spring/saml-signature-clock-boundary", "spring/saml-attribute-authority-mapping", "spring/trusted-forwarded-headers"]),
    dict(slug="saml-signature-clock-boundary", section="spring/security", title="Spring Security SAML validation: signatures, audience and clock window", summary="A successful XML parse is not authentication; the response and assertion must pass trust and time checks.", blocks=[
        ("Validate the complete assertion", "A response can contain a NameID and attributes yet still be untrusted. Spring Security's SAML provider uses the relying-party registration to verify credentials and protocol constraints. The asserted audience, destination and time conditions must match the intended service provider. Keep clocks synchronized, and set only the skew needed for measured drift."),
        ("Rotate trust deliberately", "When the IdP changes its signing certificate, overlap old and new verification credentials for a bounded migration if the IdP supports it. Fetching unsigned metadata over an untrusted channel and accepting whatever key appears is not a rotation policy. [[spring/saml-relying-party-metadata|The registration]] is the place where that trust decision becomes concrete."),
        ("Test rejection paths", "Use a test IdP or signed fixtures to submit an expired assertion, altered signature, wrong audience and response for another registration. All must fail before a session or authority is created. Also test a small positive skew; do not silently widen the window until failures disappear."),
    ], code="// Operational invariant, not a custom parser:\n// accepted = trusted signature && expected audience\n//     && expected destination && valid time window\n//     && matching relying-party registration", lang="java", cost="Signature verification and XML processing add CPU to login requests. Keep metadata and key lookup bounded, and rate-limit failed sign-ins without weakening validation.", mistakes=["Do not consider a parsed NameID proof of authentication.", "Do not disable signature checks to accommodate a certificate rollout.", "Do not use a large clock skew to hide unsynchronized hosts."], related=["spring/saml-relying-party-metadata", "spring/saml-attribute-authority-mapping", "spring/security-authentication-vs-denial"]),
    dict(slug="saml-attribute-authority-mapping", section="spring/security", title="Spring Security SAML attributes: map identity to local authority", summary="IdP attributes identify a principal; local authorization still needs an explicit mapping and tenant rule.", blocks=[
        ("Authentication is not permission", "A valid assertion may contain department=dispatch. That attribute is input to a local authorization decision, not a command to grant every dispatcher privilege. Spring Security's default authenticated SAML principal can carry attributes with a basic user authority; application roles need an explicit converter or lookup. [[spring/method-security-proxy-boundary|Method guards]] should check the resulting local authorities."),
        ("Use stable identifiers", "A display name and email address can change. Link the assertion's stable subject to a tenant-scoped local account, and decide how deprovisioning reaches active sessions. If two IdPs emit the same subject text, include registration identity in the key. Reject missing or multiply valued required attributes rather than guessing."),
        ("Test least privilege", "Sign in with no department, an unknown department and a department valid in another tenant. All should have no privileged access. Then sign in with a mapped dispatcher account and assert only the intended shipment command is allowed."),
    ], code="record FederatedAccountKey(String registrationId,\n                           String subject, String tenantId) {}\n// Resolve this key to a local account before granting command roles.", lang="java", cost="An account lookup adds I/O at login, not at every request if the result is stored in the session. Revocation needs a session expiry or invalidation contract.", mistakes=["Do not map every authenticated SAML user to an administrator role.", "Do not use email alone as a permanent cross-IdP account key.", "Do not accept a tenant attribute without matching the configured registration and local account."], related=["spring/saml-relying-party-metadata", "spring/method-security-proxy-boundary", "spring/tenant-claim-required"]),
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
        sort_order=5200 + number, published_at=stamp, created_at=stamp, updated_at=stamp,
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
    "spring/data-transactions": "Cassandra and Neo4j data boundaries",
    "spring/production": "Kubernetes configuration and discovery",
    "spring/security": "SAML identity and authority",
}.items():
    paths = ["spring/" + item["slug"] for item in lessons if item["section"] == section]
    hub = by_path[section]
    hub["data"]["modules"].append({
        "title": heading, "summary": "Store and platform contracts with failure cases and verification.", "lessons": paths,
    })
    hub["body"] += "<h2>" + heading + "</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
        for path in paths
    ) + "</ul>"
    hub["updated_at"] = stamp

parent = by_path["spring/spring-boot"]
parent["body"] += "<h2>Cassandra, Neo4j, Kubernetes and SAML</h2><ul>" + "".join(
    '<li><a href="/spring/' + item["slug"] + '">' + html.escape(item["title"]) + "</a></li>"
    for item in lessons
) + "</ul>"
parent["updated_at"] = stamp
for source, target in [
    ("spring/tenant-jdbc-predicate", "spring/cassandra-partition-key-query"),
    ("spring/batch-input-snapshot", "spring/cassandra-ttl-tombstone-budget"),
    ("spring/mongodb-change-stream-resume", "spring/cassandra-paging-state"),
    ("spring/mongodb-versioned-document", "spring/neo4j-version-conflict"),
    ("spring/transaction-thread-boundary", "spring/neo4j-transaction-boundary"),
    ("spring/boot-required-config-import", "spring/kubernetes-config-import-precedence"),
    ("spring/cloud-config-refresh-boundary", "spring/kubernetes-config-reload-contract"),
    ("spring/dependency-readiness", "spring/kubernetes-discovery-vs-dns"),
    ("spring/trusted-forwarded-headers", "spring/saml-relying-party-metadata"),
    ("spring/security-authentication-vs-denial", "spring/saml-signature-clock-boundary"),
    ("spring/method-security-proxy-boundary", "spring/saml-attribute-authority-mapping"),
]:
    row = by_path[source]
    row["body"] += ('<h2>Related boundary</h2><p><a href="/' + target + '">'
                    + html.escape(titles[target]) + "</a></p>")
    row["updated_at"] = stamp

FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "Spring articles; new total", sum(
    row["path"].startswith("spring/") and row["type"] == "article" for row in rows
))
