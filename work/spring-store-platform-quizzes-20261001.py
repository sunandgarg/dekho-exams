"""Add four Spring scenario-check quizzes with original explanations."""

import copy
import datetime
import html
import json
import pathlib
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "src/data/fixtures.json"
rows = json.loads(FIXTURE.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()

# prompt, correct answer, two plausible wrong answers, decision explanation
quizzes = [
    dict(slug="spring-cassandra-contracts", title="Spring Cassandra write and query contracts quiz", summary="Twelve decisions about partition keys, conditional writes, versions, TTL and paging.", lessons=["spring/cassandra-partition-key-query", "spring/cassandra-conditional-reservation", "spring/cassandra-consistency-budget", "spring/cassandra-versioned-write"], questions=[
        ("Two workers see no route claim before inserting. What enforces one winner?", "A conditional INSERT with IF NOT EXISTS", "A read-before-insert check", "A longer request timeout", "The database must arbitrate the key; two reads can both see absence."),
        ("A conditional write returns normally but was not applied. What should the API report?", "A conflict or the existing winner", "Success for the losing worker", "An empty success body", "Completion of the CQL call and application of the condition are separate results."),
        ("A claim write times out after the database might have committed. What comes next?", "Resolve the original command outcome", "Issue a new claim ID immediately", "Assume the write failed", "A timeout leaves the result unknown, so blind retries under new identities can duplicate business work."),
        ("A parcel history query requires ALLOW FILTERING. What should be reviewed first?", "The partition key and access path", "The browser page size", "The HTTP response header", "Filtering often signals a query that the table was not designed to serve."),
        ("One tenant's partition grows without limit. Which design change addresses that shape?", "Partition by a narrower key or bounded time bucket", "Increase the Java heap only", "Sort every row in the controller", "Partition shape controls distributed storage and read range; process memory does not fix it."),
        ("A Cassandra paging token is replayed with another parcel ID. What is the safe action?", "Reject it and start a query for the new parcel", "Reuse it as an offset", "Let the driver decide tenant access", "Paging state belongs to the original statement and parameters."),
        ("An expired TTL row disappears from reads. Does it instantly free disk space?", "No; cleanup depends on tombstones and compaction", "Yes, always", "Only if the Java entity has @Version", "Logical expiry and physical reclamation are different stages."),
        ("A versioned row has been changed since a worker loaded it. What should save do?", "Reject the stale write", "Merge every field automatically", "Overwrite the newer row", "The version condition detects conflict; it cannot infer the correct business merge."),
        ("Does Cassandra entity @Version protect a bulk write automatically?", "No; verify bulk semantics separately", "Yes, every batch uses it", "Only when TTL is disabled", "Spring Data documents optimistic locking on single-entity operations."),
        ("LOCAL_QUORUM cannot obtain enough responses. What should a sensitive read do?", "Follow its declared unavailable or pending contract", "Silently downgrade consistency", "Return a fabricated empty row", "A stricter consistency choice trades availability; fallback must be a product decision."),
        ("Can a consistency level replace a tenant-aware partition key?", "No, the data model still controls query access", "Yes, at quorum", "Only with a larger driver pool", "Replica agreement does not create a missing query path or authorization rule."),
        ("What test proves conditional reservation under contention?", "Two simultaneous claimants with exactly one applied result", "One sequential insert", "A repository mock returning true", "The invariant is about concurrent database decisions, not a single mocked call."),
    ]),
    dict(slug="spring-neo4j-graph-contracts", title="Spring Neo4j graph mapping and query contracts quiz", summary="Twelve decisions about graph ownership, cardinality, version conflicts and tenant lookup.", lessons=["spring/neo4j-relationship-ownership", "spring/neo4j-custom-query-cardinality", "spring/neo4j-indexed-tenant-lookup", "spring/neo4j-relationship-properties-identity"], questions=[
        ("A property-only edit loaded a partial relationship graph. What can make save unsafe?", "Missing relationships may be reconciled as removals", "Node properties become read-only", "The Cypher planner always rejects partial reads", "A partial mapped aggregate may not represent the full relationship set that save owns."),
        ("A custom query returns one shipment root on six records. What deserves inspection?", "Root mapping and row multiplication", "Only the HTTP status code", "The Java package name", "Repeated root records can produce partial or surprising mapped graph results."),
        ("A shipment has three checkpoints and two drivers. An unconstrained dual match can produce how many pairs?", "Six", "Three", "Two", "The two independent relationship sets can multiply to three times two before aggregation."),
        ("Where should tenant and shipment predicates appear for a bounded traversal?", "On the root lookup before expansion", "Only after returning every path", "Only in the browser", "An indexed root narrows the graph before relationship work grows."),
        ("What should back a tenantId plus shipmentId business key?", "A composite uniqueness constraint", "An in-memory Set in one pod", "A check-then-create query alone", "The database constraint settles concurrent duplicates across replicas."),
        ("Does an internal Neo4j node ID authorize access to a tenant?", "No", "Yes, because it is unique", "Only for reads", "Identity of a graph record is not proof of caller ownership."),
        ("Why store @RelationshipId on a relationship-properties class?", "To identify an existing edge during mapping and save", "To replace tenant authorization", "To make every edge public", "The mapper needs edge identity to reconcile property-bearing relationships."),
        ("What is a separate public assignment ID for?", "A stable business reference", "Replacing @TargetNode", "Avoiding all constraints", "The internal graph relationship ID is not the application's external contract."),
        ("A custom Cypher update skips the mapped @Version property. What can happen?", "It bypasses the expected version conflict check", "Spring adds the predicate automatically", "The write becomes read-only", "A custom mutation must include its own version rule if it competes with versioned saves."),
        ("After a stale write fails, what should the service do?", "Reload and re-evaluate the command", "Retry the stale object forever", "Remove the version field", "Conflict detection is not a business merge algorithm."),
        ("Which evidence reveals an expensive graph traversal?", "EXPLAIN or PROFILE with row expansion", "Only controller response size", "A unit mock of the repository", "The database plan shows lookup and fan-out that application mocks omit."),
        ("What proves a property-only update did not erase driver links?", "A real graph test asserting relationships after save", "A successful Java compile", "An empty HTTP response", "Persistence state after the command is the evidence for relationship preservation."),
    ]),
    dict(slug="spring-kubernetes-operations", title="Spring Kubernetes configuration and probe quiz", summary="Twelve decisions about imports, permissions, watchers, DNS and pod probes.", lessons=["spring/kubernetes-config-import-precedence", "spring/kubernetes-config-rbac", "spring/kubernetes-config-watcher-scope", "spring/kubernetes-probe-timing"], questions=[
        ("A ConfigMap import is required but unavailable. What should startup do?", "Fail under the declared required-import contract", "Invent a default silently", "Ignore the entire application configuration", "A missing required source must be visible before the pod serves traffic."),
        ("Does an imported Kubernetes property override every Boot configuration source?", "No; normal Config Data precedence still applies", "Yes, without exception", "Only when the file is XML", "The import outranks its declaring document, while other sources have their own ordering."),
        ("Which account's API permissions matter inside a pod?", "The pod's service account", "The developer's local kubeconfig", "The browser user's account", "The application client calls Kubernetes under its deployed identity."),
        ("A service reads only ConfigMaps. Should it receive secret reads by default?", "No", "Yes, every configuration starter requires all secrets", "Only on weekends", "Resource access should match the actual application dependency."),
        ("Is a watcher label filter a security boundary?", "No; RBAC is the access boundary", "Yes; it blocks API reads", "Only with a startup probe", "Filtering events does not revoke Kubernetes API permissions."),
        ("A ConfigMap change event fired. Are all live clients reconfigured?", "Not necessarily; inspect each bean's refresh behavior", "Yes, every connection restarts", "Only the HTTP port changes", "A bean that captured a value at construction can retain old state."),
        ("A service only needs a stable in-cluster Service name. What may suffice?", "Kubernetes Service DNS", "Cluster-wide DiscoveryClient permissions", "A database query per request", "DNS resolves stable service names without an application API watch."),
        ("What should liveness usually avoid depending on?", "A shared downstream database", "The local process state", "The application's ability to recover", "A shared outage should not restart every healthy replica."),
        ("What does readiness decide?", "Whether the pod should receive new traffic", "Whether the source code compiles", "Whether every external service exists", "Readiness is the routing gate for a running pod."),
        ("Why add a startup probe to a slow cold start?", "To allow initialization before liveness restarts the pod", "To disable readiness forever", "To grant API roles", "Startup timing is a separate failure window from steady-state health."),
        ("What test reveals missing production RBAC?", "Run under the intended deployment service account", "Run only with an admin kubeconfig", "Check the YAML syntax alone", "The actual pod identity determines whether cluster reads and watches succeed."),
        ("Should a watcher refresh every service for an unrelated ConfigMap edit?", "No; scope source and namespace", "Yes; broad refresh is harmless", "Only if the value is numeric", "Unrelated events waste API and application work and can cause avoidable restarts."),
    ]),
    dict(slug="spring-saml-identity", title="Spring SAML trust and session quiz", summary="Twelve decisions about registration, signatures, authorities, logout and revocation.", lessons=["spring/saml-relying-party-metadata", "spring/saml-signature-clock-boundary", "spring/saml-local-vs-single-logout", "spring/saml-session-revocation"], questions=[
        ("An assertion contains a NameID but its signature is invalid. Is the caller authenticated?", "No", "Yes, because XML parsed", "Only if the email looks valid", "Identity claims require trusted signature and protocol validation."),
        ("The ACS path changes in the app. What else must agree?", "Relying-party metadata and IdP configuration", "Only the CSS bundle", "Only the database pool", "The identity provider must post to the endpoint the service provider actually processes."),
        ("What can a large clock-skew allowance hide?", "Unsynchronized systems and acceptance of old assertions", "A slow CSS response", "An indexed tenant lookup", "Time-window validation should reflect measured drift, not bypass it."),
        ("An IdP attribute says department=dispatch. Does that alone grant admin authority?", "No; map to reviewed local permissions", "Yes, every IdP attribute is a role", "Only after local logout", "Authentication attributes are inputs to an application authorization policy."),
        ("Two IdPs emit the same subject text. What separates local account keys?", "The registration identity and tenant", "The browser width", "The current request path only", "Subjects need issuer or registration context before becoming local identities."),
        ("What does local logout end?", "This application's authenticated session", "Every IdP and service-provider session", "The user's account permanently", "A local session clear does not promise federated logout."),
        ("What must the IdP support for SAML single logout?", "Compatible SAML logout requests and responses", "Only password reset", "Only local HTTP cookies", "Single logout is a signed protocol exchange, not merely deleting an application cookie."),
        ("An IdP removes a user's role while the app session remains active. What happens automatically?", "Nothing guarantees immediate local authority refresh", "Every app request revalidates with the IdP", "All pods restart", "Login is a point-in-time event unless the application implements expiry or revocation."),
        ("A multi-pod deployment must revoke one user's sessions. What cannot work reliably alone?", "Deleting one pod's private session map", "A shared session index", "A tenant-scoped subject key", "Other replicas can retain or load sessions outside the one pod's memory."),
        ("During certificate rollover, which trust set is appropriate for a bounded overlap?", "The verified old and verified new keys", "Any certificate embedded in an assertion", "No signing checks", "The overlap must contain only reviewed credentials for that registration."),
        ("After the old signing key is retired, what should an old-key assertion do?", "Fail verification", "Succeed forever", "Become a local admin", "Retired trust must actually be removed after the overlap window."),
        ("What should a SAML protocol test exercise besides the happy path?", "Wrong audience, expired assertion and untrusted signature", "Only page colors", "Only a mocked controller", "These rejection cases prove the trust boundary, not merely XML parsing."),
    ]),
]

template = by_path["quizzes/spring-data-production"]
hub = by_path["spring/quizzes"]
for index, quiz in enumerate(quizzes):
    path = "quizzes/" + quiz["slug"]
    assert path not in by_path
    for target in quiz["lessons"]:
        assert target in by_path, target
    questions = []
    for position, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(quiz["questions"]):
        options = [correct, wrong_a, wrong_b]
        turn = position % 3
        options = options[turn:] + options[:turn]
        questions.append({"prompt": prompt, "options": options,
                          "answer": options.index(correct), "explanation": explanation})
    body = "<p>" + html.escape(quiz["summary"]) + "</p><h2>Review before answering</h2><ul>"
    body += "".join('<li><a href="/' + target + '">' + html.escape(by_path[target]["title"]) + "</a></li>"
                    for target in quiz["lessons"])
    body += "</ul><h3>Edge Cases</h3><p>Choose the outcome that preserves the documented boundary under failure, not just the path that works once.</p>"
    row = copy.deepcopy(template)
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
               path=path, title=quiz["title"], summary=quiz["summary"], body=body,
               sort_order=700 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"questions": questions, "duration_minutes": 9,
                   "subject_root": "spring/spring-boot", "section_path": "spring/quizzes",
                   "content_format": "html", "seo_ready": True}
    rows.append(row)
    by_path[path] = row
    hub["data"]["modules"].append({"title": quiz["title"], "summary": quiz["summary"], "lessons": [path]})
    hub["body"] += '<h2>' + html.escape(quiz["title"]) + '</h2><p><a href="/' + path + '">Check these decisions</a></p>'
    hub["updated_at"] = stamp
    by_path[quiz["lessons"][0]]["body"] += '<h2>Check your understanding</h2><p><a href="/' + path + '">' + html.escape(quiz["title"]) + '</a></p>'
    by_path[quiz["lessons"][0]]["updated_at"] = stamp

by_path["spring/spring-boot"]["body"] += "<h2>Store and platform practice</h2><ul>" + "".join(
    '<li><a href="/quizzes/' + quiz["slug"] + '">' + html.escape(quiz["title"]) + "</a></li>"
    for quiz in quizzes) + "</ul>"
by_path["spring/spring-boot"]["updated_at"] = stamp
FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(quizzes), "quizzes and", sum(len(q["questions"]) for q in quizzes), "questions")
