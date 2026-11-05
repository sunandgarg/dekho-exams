"""Add a Spring Boot Web Development track with original cross-curriculum lessons."""

import copy
import datetime
import html
import json
import re
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


hub_path = "web-tech/spring-boot-web-service-boundaries"
hub_title = "Spring Boot Web Service Boundaries"
topics = [
    dict(
        slug="spring-boot-security-chain-and-object-permission",
        title="Spring Boot Security Chain and Object Permission",
        summary="Authenticate at the request boundary and authorize the exact permit again at the service boundary.",
        concept="A Spring Boot web request can pass through servlet filters, route mapping, controller conversion, method security, and repository access. Those layers answer different questions. A security filter chain decides whether a request is admitted and how the caller is authenticated. A role or authority may admit a reviewer to the permit API, but it does not grant access to every permit ID. Object permission belongs near the service operation that reads or writes the record, with current assignment and tenant scope checked against the exact ID. Method security can intercept Spring-managed bean calls when enabled; a direct self-call within the same bean can bypass proxy advice. A menu that hides a case is presentation, not authorization. The response must project only approved fields after access succeeds.",
        case="Reviewer 47 may inspect permit 62; reviewer 81 has an account and the same broad reviewer role but is assigned elsewhere. A filter rule that requires the reviewer role lets both reach GET /permits/62. If the controller calls repository.findById(62) and returns an entity, reviewer 81 receives the private district note. A second version adds a method annotation to a private helper invoked from the same service instance and assumes it ran; the proxy never sees that internal call. The corrected flow authenticates the route, calls a distinct Spring-managed service method protected by method security or an explicit guard, checks assignment for permit 62, and returns a narrow PermitView. A later approval must repeat current-state permission inside the write transaction because assignment may change after the GET.",
        implementation="Declare one ordered filter-chain policy for public health and private permit routes, and test the matcher order with both anonymous and authenticated requests. Enable method security explicitly before relying on @PreAuthorize. Place authorization on a public method reached through an injected Spring bean, or perform a direct guard inside the service; do not depend on proxy interception of self-invocation. For list pages, constrain reviewer or tenant ownership in the repository query before paging rather than filtering entities in Java after a broad query. For a single record, decide whether unknown and forbidden IDs share a public response to avoid revealing existence. An authority check, a case assignment query, and a response projection should be visible as separate operations in tests and trace logs.",
        cost="A precise permission query adds a database predicate or indexed assignment existence check. Its cost is small compared with leaking another reviewer's case, but N separate checks across an unbounded list can create N extra database calls. Put list ownership in SQL and measure the actual plan. A service guard may acquire a second read if the controller already loaded the entity; pass a scoped lookup or keep the fetch and check in one service method to avoid redundant work. Method interception adds a small proxy call overhead, while a deeply nested expression can become hard to audit. Keep security logs free of case bodies and bearer tokens. Record denied route counts, denied object counts, query count, and latency for permitted versus rejected operations.",
        failure="Request the same permit as reviewer 47, reviewer 81, an anonymous caller, and a user whose assignment was revoked after the page loaded. Confirm route admission and object denial are distinguished internally while public responses follow the chosen existence policy. Invoke the service method from a controller and through a self-call test; the self-call must not be treated as protected merely because an annotation appears on it. Fetch a list of 47 cases and inspect SQL to ensure unauthorized records are excluded before pagination. Seed a private field in permit 62 and verify it never appears in the response. Exercise a future route introduced under the same URL prefix and ensure the filter matcher does not accidentally admit it without a service permission check.",
        drill="Build a permit detail endpoint for two reviewers and one private case. Configure public health access separately from reviewer routes. Enable method security and put a case-specific guard on the service method actually called by the controller. Test GET detail, list paging, and approval as both reviewers; revoke the assignment between list and approval. Compare a proxy-reached method with a self-invoked helper to make the interception boundary visible. Capture query counts and the serialized response keys. Document which layer authenticates, which layer authorizes the record, and which layer shapes the public result. Reject any implementation that treats a reviewer role as a grant to every permit.",
        decision="The filter chain establishes caller and route admission; a Spring-managed service checks current permission for the exact object.",
        code='''@Configuration
@EnableMethodSecurity
class PermitMethodSecurity { }

@Service
class PermitViewService {
  private final PermitCaseRepository permits;

  PermitViewService(PermitCaseRepository permits) {
    this.permits = permits;
  }

  @PreAuthorize("@permitAccess.canRead(authentication, #p0)")
  public PermitView read(Long permitId) {
    PermitCase permit = permits.findById(permitId).orElseThrow();
    return new PermitView(permit.getId(), permit.getTitle(), permit.getStatus());
  }
}''',
        checks=["Method security is enabled before annotations are relied upon.", "Reviewer 81 cannot read permit 62 despite holding a reviewer role.", "The public view omits private entity fields."],
        mistakes=["Treating a route role as authorization for every record.", "Expecting a same-bean self-call to pass through method-security proxy advice.", "Returning a JPA entity directly after a broad permission check."],
        related=["spring/security-filter-chain", "spring/method-security-proxy-boundary", "spring/method-authorization", "web-tech/authorization-and-tenant-boundaries"],
    ),
    dict(
        slug="spring-boot-mvc-validation-and-problem-contracts",
        title="Spring Boot MVC Validation and Problem Contracts",
        summary="Validate an approval command at the HTTP edge and return stable, bounded error information.",
        concept="Spring MVC converts a request body into an argument before a controller method runs. Bean Validation on a command DTO can reject missing or malformed fields, but it does not decide whether the caller may approve a case or whether the current case revision still matches. Keep input DTOs separate from persistence entities so clients cannot set server-owned status, reviewer ID, or audit fields through binding. An API error contract should distinguish malformed input, forbidden access, missing records, stale revisions, and unexpected server faults. ProblemDetail provides a structured error body, yet the service still needs deliberate exception mapping and safe field messages. Validation annotations are only one layer: cross-field rules, length budgets, content type, and business transition checks need explicit placement.",
        case="The approval endpoint for permit 62 accepts operation ID, expected revision 5, and reason. A browser sends an empty reason and receives a validation error. Another sends reviewerId=81 and status=approved alongside valid fields; those extra fields must not become entity state. Reviewer 47 then submits revision 5 after another reviewer already committed revision 6. The shape is valid, but the transition is stale; returning the same 400 as a blank reason makes client recovery unclear. A service maps the latter to a conflict response with a safe code and current revision hint, while a forbidden reviewer receives no private case details. An internal database failure returns a server error and a trace ID, never an exception stack in JSON.",
        implementation="Define an immutable approval command with only client-owned fields. Add field constraints for nonblank bounded text and required revision, and validate the request body at the controller boundary. Configure a central exception mapper so validation errors use a predictable field-error structure with a maximum count and safe messages. Map stale revisions, missing records, forbidden operations, and unexpected failures explicitly; keep the ProblemDetail status consistent with the HTTP status. Avoid exposing rejected raw input, database table names, or security internals in the response. A content type policy should reject unsupported payloads before binding. If a browser uses cookies, keep CSRF checks independent from field validation. Check that a client can use a stable error code rather than parsing English prose.",
        cost="DTO binding and validation cost work proportional to the fields and nested elements inspected. Bound a collection's length and nesting depth before expensive service work; a small DTO cannot protect a service that later traverses an unbounded related graph. Creating a ProblemDetail object is cheap, but collecting and serializing thousands of field errors can be expensive and can expose submitted values. Cap error counts and request body size. A distinct conflict response allows a client to refresh current state instead of retrying the same stale mutation repeatedly. Central mapping reduces inconsistent controller logic, but broad catch-all handlers can hide programming defects if they convert every exception into a client error. Measure invalid request rates, validation time, and conflict frequency.",
        failure="Send null body, wrong content type, missing operation ID, negative revision, blank reason, an overlong reason, and an extra status field. Confirm none reach the approval service with unvalidated values. Produce nested invalid collections at the body-size limit and verify the response remains bounded. Race two approvals for the same expected revision and require one committed outcome and one conflict. Submit a valid DTO as an unassigned reviewer; permission must still fail. Simulate a database outage and assert the response is a server error with no SQL string or stack trace. Check that localized human messages can change without breaking the client, which should branch on a stable machine code.",
        drill="Create a Spring MVC approval command record and a controller action for permit 62. Use validation on the command and a central mapper for input, forbidden, missing, stale, and internal failures. A request test should feed malformed bodies and assert both status and structured error code. Seed an existing revision 6 and send expected revision 5 to confirm the stale case is not misclassified as malformed input. Use a separate service test for transition permission, because annotations on a DTO do not protect case state. Review the serialized JSON and confirm no submitted status, reviewer ID, raw reason, or internal exception detail leaks into unexpected fields.",
        decision="Input shape, current-state permission, and conflict resolution are separate checks with separate client outcomes.",
        code='''record ApprovePermitCommand(
    @NotBlank String operationId,
    @Positive long expectedRevision,
    @NotBlank @Size(max = 420) String reason
) { }

@RestController
class PermitApprovalController {
  private final PermitApprovalService approvals;

  PermitApprovalController(PermitApprovalService approvals) {
    this.approvals = approvals;
  }

  @PostMapping("/permits/{permitId}/approval")
  ApprovalView approve(@PathVariable Long permitId,
                       @Valid @RequestBody ApprovePermitCommand command) {
    return approvals.approve(permitId, command);
  }
}''',
        checks=["Only client-owned command fields appear in the request type.", "A stale revision has a distinct conflict outcome from malformed input.", "Unexpected faults do not disclose internal stack or SQL details."],
        mistakes=["Binding a request directly into a JPA entity.", "Treating Bean Validation as record permission or concurrency control.", "Returning a raw exception message as a public error body."],
        related=["spring/rest-validation", "spring/mvc-validation-problem", "spring/problem-details", "web-tech/api-mutation-and-failure-contracts"],
    ),
    dict(
        slug="spring-boot-jpa-scope-fetch-and-page-cost",
        title="Spring Boot JPA Scope, Fetch, and Page Cost",
        summary="Constrain reviewer visibility in SQL, fetch displayed relations, and bound each page.",
        concept="A repository method can return entities, projections, a Page, or a Slice, each with a different amount of database and memory work. A permit queue must constrain rows to the current reviewer before pagination. Fetching a broad table and filtering in Java can leak counts, waste memory, and produce short or inconsistent pages. Lazy loading a district for every card creates extra SQL; fetching every attachment to display only its count can be worse. An entity graph or explicit join fetch can load a needed to-one relation, while a separate count projection handles large child collections. A stable sort must include a unique tie breaker. The same reviewer predicate belongs in every continuation query, regardless of what a cursor contains.",
        case="Reviewer 47 sees 47 permits. The first implementation asks for a Page of all permits and removes unassigned rows in a stream, so a page may show only three authorized cases even when more exist later. The template reads permit.getDistrict().getName() for each row and triggers many lazy queries. A second attempt fetches all attachments with each permit to eliminate the N+1, but one case carries 620 scans and dominates response memory. A corrected repository query joins the reviewer assignment in SQL, orders by creation time and ID, returns a bounded Slice, and fetches only the district shown on the card. Attachment totals come from a separate bounded aggregate or maintained count. A cursor from reviewer 81 never changes reviewer 47's SQL scope.",
        implementation="Model the reviewer assignment in the query itself, with a uniqueness rule preventing accidental duplicate parent rows. Request a fixed page width through Pageable and define a stable sort that ends with permit ID. Use Slice when the interface only needs to know whether another page exists; Page can require an additional count query for an exact total. Inspect generated SQL, not only repository method names. Use an entity graph or DTO projection for the to-one district field actually rendered. Avoid fetch-joining unbounded to-many attachments with pagination, because database and ORM behavior can defeat the intended page limit. Convert loaded entities to response DTOs while the transaction and persistence context are open, then return plain values so serialization cannot trigger unexpected database reads.",
        cost="A page width of P bounds parent materialization to roughly O(P) objects, plus the displayed to-one relations. A lazy N+1 path can issue O(P) extra queries. Fetching children can use O(A) memory for A attachments across those parents, even when the response needs only one integer per case. A Page count query may scan indexed or filtered rows and can be expensive on large datasets; a Slice avoids an exact total but may request one extra row to determine continuation. Offset paging can spend work skipping deep rows, while keyset continuation needs a matching predicate and index but loses cheap arbitrary page numbers. Measure SQL count, rows read, heap allocations, database plan, and p95 response time on skewed production-like fixtures.",
        failure="Seed 47 permits with shared creation timestamps, one permit with 620 attachments, and a reviewer with assignments to only some rows. Verify page membership and order are correct when authorization is applied in SQL. Turn off district preloading and count the extra queries; turn on broad attachment fetching and inspect allocation size. Use an out-of-scope cursor and assert it does not change the server-side reviewer predicate. Advance through multiple pages during concurrent insertion and document whether duplicates or omissions can occur under the chosen offset or keyset policy. Close the persistence context before JSON serialization and confirm the DTO still renders without lazy loads. Check the query plan against the actual indexes, not an empty local database.",
        drill="Implement a Spring Data repository query for reviewer 47's permit cards with district labels and attachment totals. Limit the first page to 47, sort by created time then ID, and return a Slice or explicit keyset result. Compare three implementations on the same skewed fixture: lazy district access, broad attachment fetch, and bounded district fetch with count projection. Record SQL count, objects allocated, and rows returned. Add a second reviewer and check scope on every page. Keep the entity-to-DTO conversion inside a service method and test JSON serialization after the persistence context closes. Write down the index required for assignment filter and sort order.",
        decision="Permission scope and page width belong in SQL; fetch plans follow the fields the response actually displays.",
        code='''interface PermitCaseRepository extends JpaRepository<PermitCase, Long> {
  @EntityGraph(attributePaths = "district")
  @Query("select p from PermitCase p join p.reviewerAssignments a " +
         "where a.reviewer.id = :reviewerId")
  Slice<PermitCase> visibleForReviewer(
      @Param("reviewerId") Long reviewerId, Pageable page);
}

Pageable firstPage = PageRequest.of(
    0, 47, Sort.by(Sort.Order.desc("createdAt"), Sort.Order.desc("id")));''',
        checks=["Reviewer permission is a SQL predicate before the page limit.", "District data is fetched without loading every attachment.", "Equal timestamps have a unique ordering tie breaker."],
        mistakes=["Filtering an already paginated broad result in Java.", "Fetch-joining a large to-many collection merely to show its count.", "Assuming a cursor itself grants access to the next page."],
        related=["spring/jpa-fetch-plans", "spring/jpa-entity-lifecycle", "spring/data-transactions", "web-tech/data-persistence"],
    ),
    dict(
        slug="spring-boot-transaction-replay-and-outbox-handoff",
        title="Spring Boot Transaction Replay and Outbox Handoff",
        summary="Commit an approval once, recover ambiguous retries, and retain notification intent after a lost enqueue.",
        concept="An approval command crosses a database transaction and a separate delivery system. The case state, operation identity, public result, and outbox intent should be committed together in the database. A unique operation ID with a command digest lets an exact retry recover the result after an HTTP response is lost; the same ID with changed input is a conflict. Current assignment and expected revision must be checked inside the transaction that writes the case, with a locking or optimistic-concurrency rule chosen for the database. A transaction-bound event listener can run after commit, which prevents a worker from seeing uncommitted state. That timing does not make a separate broker handoff atomic with the database commit. A durable outbox row and independent relay remain necessary when losing a notification is unacceptable.",
        case="Reviewer 47 approves permit 62 at revision 5. The database commits revision 6, but the browser connection drops before receiving success. The browser retries the same operation ID. Without a stored result it may create a second audit entry or send another email. Meanwhile the process crashes after commit and before its after-commit callback enqueues work. A correct service stores the command digest and result alongside the case update and a pending outbox event. The exact retry returns the saved result, a changed reason under that ID fails, and a relay discovers the pending event after restart. A competing reviewer with expected revision 5 receives a conflict rather than silently overwriting revision 6.",
        implementation="Keep the transactional service method on a Spring-managed bean reached through its proxy; a direct same-bean call can bypass @Transactional advice. Lock the case row or use an optimistic version column, and recheck current assignment and legal transition in the transaction. Put a unique constraint on operation identity scoped to the intended command domain. Store a digest of all meaningful command fields and a public result. Insert an outbox row with a stable event key before commit. After commit, a listener may wake the relay, but the relay must also scan pending rows because the wake-up can be lost. Claim rows with a lease or database-supported locking, retry under the same event identity, and mark delivered only after the provider or broker outcome is known. Ambiguous external outcomes require reconciliation or provider idempotency support.",
        cost="A short row lock serializes approvals of the same case and can increase wait time under contention; optimistic locking avoids holding an explicit lock but requires conflict handling. The unique operation and outbox records add writes and retained storage proportional to successful commands. A relay scan and lease claim add background database work, while an event hint can reduce average notification delay. Provider retries may duplicate effects if the destination does not recognize the stable event key. Keep the transaction free of network calls so a slow provider cannot hold the case lock. Measure lock wait, duplicate-key races, pending outbox age, retry count, delivery lag, and reconciliation backlog. A clean unit test cannot prove power-loss behavior, so operational drills must inspect persisted rows after process interruption.",
        failure="Race two exact requests with one operation ID and assert one case transition, one saved result, and one outbox row. Reuse the ID with a different reason and require conflict. Drop the HTTP response after commit, retry, and compare the recovered result to the first transaction. Revoke assignment just before the write and verify a stale earlier GET does not authorize it. Force rollback after changing case state but before outbox insertion and confirm neither change survives. Kill the web process after commit but before after-commit enqueue; the independent relay must find the pending row. Deliver the same outbox event twice to a test sink and inspect its idempotency or reconciliation behavior. Repeat against the actual production database type when lock semantics matter.",
        drill="Build an ApprovePermit service with permit ID, reviewer identity, operation ID, expected revision, and bounded reason. Persist case revision, operation digest and result, and outbox event in one transaction. Use a unique database constraint to resolve concurrent exact retries across processes. Add a relay that claims pending rows with a lease, sends under a stable event key, and marks completion only after a confirmed outcome. Test lost response, changed-payload replay, competing revision, rollback, lost wake-up, lease expiry, and ambiguous provider timeout. Inspect database rows and delivery history after each drill; a successful HTTP status alone is not evidence that external work completed.",
        decision="The database owns one approval and one delivery intent; after-commit callbacks only speed a relay that can recover independently.",
        code='''@Service
class PermitApprovalService {
  private final PermitRepository permits;
  private final ApprovalOperationRepository operations;
  private final ApprovalOutboxRepository outbox;

  @Transactional
  public ApprovalView approve(Long permitId, ApprovePermitCommand command) {
    PermitCase permit = permits.lockById(permitId).orElseThrow();
    ApprovalOperation prior = operations.find(permitId, command.operationId());
    if (prior != null) return prior.sameCommand(command)
        ? prior.publicResult() : conflict();
    requireCurrentReviewer(permit);
    requireRevision(permit, command.expectedRevision());
    permit.approve();
    ApprovalOperation saved = operations.saveOutcome(permit, command);
    outbox.savePending(saved.eventKey(), permit.getId());
    return saved.publicResult();
  }
}''',
        checks=["Case, operation result, and outbox intent commit together.", "An exact replay recovers the saved outcome; changed input conflicts.", "A pending row survives a lost after-commit queue hint."],
        mistakes=["Calling a @Transactional method only through same-bean self-invocation.", "Sending provider work inside the case transaction.", "Treating an after-commit listener as a durable cross-system transaction."],
        related=["spring/transaction-proxies", "spring/transaction-events", "spring/outbox-atomic-write", "spring/receipt-outbox-command", "web-tech/background-workflow-reliability"],
    ),
]


assert hub_path not in by_path and len(topics) == 4
hub = copy.deepcopy(by_path["web-tech/fastapi-contract-and-resource-boundaries"])
hub.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + hub_path)), path=hub_path, title=hub_title,
           summary="Build Spring Boot permit services with precise permission, validated contracts, bounded JPA reads, and recoverable writes.",
           sort_order=3770, created_at=stamp, updated_at=stamp, published_at=stamp)
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
    entry = copy.deepcopy(by_path["web-tech/trace-context-across-request-and-job"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                 title=topic["title"], summary=topic["summary"], sort_order=3771 + number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    related = [hub_path] + ["web-tech/" + other["slug"] for other in topics if other is not topic] + topic["related"]
    body = paragraph(topic["concept"]) + "<h2>Working case</h2>" + paragraph(topic["case"])
    body += '<h2>Implementation boundary</h2><pre><code class="language-java">' + html.escape(topic["code"], quote=False) + "</code></pre>" + paragraph(topic["implementation"])
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
hub["body"] = paragraph("Spring Boot permit requests cross route admission, controller validation, repository reads, and transactional writes. Each boundary admits a different kind of input and carries a different failure mode. The four lessons follow permit 62 across those layers, then connect to the existing Spring subject for deeper treatment of method proxies, MVC errors, JPA fetch plans, and delivery recovery.")
hub["body"] += "<h2>Topics in this track</h2><ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
hub["body"] += "<h2>Prerequisite paths</h2><p>" + "; ".join(link(path) for path in ["web-tech/backend-api-systems", "spring/spring-boot", "web-tech/data-persistence"]) + ".</p>"
curriculum = by_path["web-tech/web-technology"]
curriculum["data"]["modules"].append({"title": hub_title, "summary": hub["summary"],
                                       "lessons": [hub_path] + ["web-tech/" + topic["slug"] for topic in topics]})
curriculum["body"] += "<h2>" + link(hub_path) + "</h2>" + paragraph(hub["summary"]) + "<ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
curriculum["updated_at"] = stamp
crosslinks = {
    "web-tech/backend-api-systems": [hub_path],
    "web-tech/authorization-and-tenant-boundaries": ["web-tech/spring-boot-security-chain-and-object-permission"],
    "web-tech/api-mutation-and-failure-contracts": ["web-tech/spring-boot-mvc-validation-and-problem-contracts"],
    "web-tech/data-persistence": ["web-tech/spring-boot-jpa-scope-fetch-and-page-cost"],
    "web-tech/background-workflow-reliability": ["web-tech/spring-boot-transaction-replay-and-outbox-handoff"],
    "spring/security-filter-chain": ["web-tech/spring-boot-security-chain-and-object-permission"],
    "spring/mvc-validation-problem": ["web-tech/spring-boot-mvc-validation-and-problem-contracts"],
    "spring/jpa-fetch-plans": ["web-tech/spring-boot-jpa-scope-fetch-and-page-cost"],
    "spring/outbox-atomic-write": ["web-tech/spring-boot-transaction-replay-and-outbox-handoff"],
}
for path, targets in crosslinks.items():
    by_path[path]["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    by_path[path]["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": 1, "new_lessons": 4,
                  "prose_words": {topic["slug"]: len(re.findall(r"\b[\w'-]+\b", " ".join(str(topic[key]) for key in ("concept", "case", "implementation", "cost", "failure", "drill", "decision", "summary")))) for topic in topics}}))
