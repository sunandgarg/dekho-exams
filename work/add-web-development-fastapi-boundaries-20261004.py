"""Add original FastAPI service-boundary lessons to the Web Development fixture."""
import ast
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


hub_path = "web-tech/fastapi-contract-and-resource-boundaries"
hub_title = "FastAPI Contract and Resource Boundaries"
topics = [
    dict(
        slug="fastapi-dependencies-and-object-authorization",
        title="FastAPI Dependencies and Object Authorization",
        summary="Resolve identity once, then authorize the exact resource at the service boundary.",
        concept="A FastAPI dependency is a callable that supplies a value before a path operation runs. Dependencies can compose: one reads an authenticated reviewer, another obtains a repository, and a third uses both to resolve a permitted case. This is useful for request-scoped policy and test overrides, but dependency injection is not itself authorization. A dependency that only verifies a bearer token still leaves every case ID reachable unless the resource lookup includes the reviewer. A private case lookup must be defined by server-side relationships and used by every endpoint that exposes or mutates that case. The path parameter identifies the requested object; it is never evidence of permission.",
        case="A permit API has reviewer 47 assigned to case 62 and reviewer 81 assigned elsewhere. A detail route checks the token, then fetches case 62 by primary key. Reviewer 81 can change the URL and receive private notes. A second endpoint exports a case from the same unscoped repository method. The repair makes a dependency resolve a case under the current reviewer mapping and returns the same private-resource response for missing and forbidden cases. The approval service repeats the permission test inside its write transaction. That second check matters when a background command, another route, or a changed assignment reaches the service after the initial read.",
        implementation="Use a dependency to parse and verify the caller's identity, rejecting an absent or invalid credential before private repository work. Compose it with a repository dependency and a case dependency that filters by reviewer ID and case ID together. Keep any public error detail short enough that a forbidden case title or owner cannot leak. Share the scoped lookup between detail and export routes, but do not treat a previously resolved ORM object as permanent permission for a later write. Put the current-state check in the command service as well. A test can override the identity and repository dependencies to exercise every case without bypassing the policy function itself. Make the policy callable small enough to audit.",
        cost="Dependency evaluation is request work, and a private object lookup usually adds one database round trip. A careless dependency graph can repeat expensive work or open multiple sessions per request; inspect actual query counts and the chosen cache behavior rather than assuming reuse. A scoped query with indexes on case identity and reviewer mapping should avoid loading every assignment in Python. Returning 404 for both forbidden and missing cases may simplify disclosure, but it can make support diagnostics harder; logs can retain a request identifier and private reason without copying those details to the response. Measure allowed, forbidden, anonymous, and missing paths under representative reviewer assignment counts.",
        failure="Call the detail and export endpoints with no credential, a malformed credential, reviewer 47, reviewer 81, and an unknown case. All private routes should use the same disclosure rule. Temporarily replace the scoped lookup with a raw primary-key lookup to demonstrate the guessed-ID leak, then restore it. Change a case assignment between the initial read and approval; the write must reject the stale permission. Verify that dependency overrides in tests still exercise the real policy with controlled identities and repository rows. Check that a repository exception becomes an internal response without revealing SQL, tokens, or case titles. Count session and query creation for each path.",
        drill="Implement a case detail route, an export metadata route, and an approval command for two reviewers. Write the authorization predicate once as a repository operation that accepts reviewer and case IDs. Use it in a composed dependency for reads and inside the approval transaction for writes. Add a test that guesses a valid case ID from the wrong reviewer account. Add another that revokes assignment after a detail read but before approval. Capture request IDs in server logs while returning the same short response for private missing and forbidden cases. Compare query counts before and after factoring dependencies.",
        decision="Use dependencies to assemble request context; enforce exact object permission in the scoped lookup and in every write service.",
        code='''from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from .models import PermitCase, PermitView, Reviewer
from .services import PermitRepository, current_reviewer, get_repository

router = APIRouter()


def authorized_case(
    case_id: int,
    reviewer: Annotated[Reviewer, Depends(current_reviewer)],
    repository: Annotated[PermitRepository, Depends(get_repository)],
) -> PermitCase:
    permit = repository.find_for_reviewer(reviewer.id, case_id)
    if permit is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return permit


@router.get("/permits/{case_id}", response_model=PermitView)
def read_permit(permit: Annotated[PermitCase, Depends(authorized_case)]):
    return {"id": permit.id, "title": permit.title, "status": permit.status}''',
        checks=["Authentication is resolved before private repository work.", "The repository filters by reviewer and case together.", "Every write service verifies permission again under current state."],
        mistakes=["Assuming a verified token authorizes every case ID.", "Overriding away the policy dependency in tests.", "Reusing a past read permission for a later state-changing command."],
        related=["web-tech/authorization-and-tenant-boundaries", "web-tech/django-middleware-session-and-object-permissions"],
    ),
    dict(
        slug="fastapi-input-output-models-and-error-contracts",
        title="FastAPI Input, Output, and Error Contracts",
        summary="Give commands strict input models and return only fields admitted by a public response model.",
        concept="FastAPI uses typed request models to parse and validate data at the HTTP boundary. A response model defines the outward shape and can filter fields from a returned object. These are two different contracts: an approval command may contain an operation ID and private reason, while its response may contain only case ID, public status, and revision. Validation stops malformed values before a service call, but it cannot decide whether reviewer 81 may approve case 62. A response model reduces accidental exposure, but it is safer for the service to produce a deliberate public projection as well. An error contract must distinguish bad input, missing private resources, stale revisions, and unexpected failures.",
        case="A permit approval route accepts an arbitrary JSON object and forwards it to a service. A client adds an internal field named approved_by and the service accidentally trusts it. The route then returns a full ORM object containing internal reviewer notes. A follow-up adds an input model that rejects unknown fields and bounds the operation ID and reason, plus a separate output model with only approved fields. The service still derives reviewer identity from the verified request dependency and checks the case under current permissions. A revision mismatch becomes a controlled conflict. An unexpected database exception remains an internal error without echoing the submitted reason.",
        implementation="Define one input model per command and a separate public response model. Set extra-field behavior deliberately; when the contract should reject unknown input, forbid it rather than silently accepting future-looking fields. Bound strings and integer ranges near the HTTP edge, then apply domain checks in the service. Do not accept reviewer_id, approval state, or tenant scope as trusted client attributes. Use response_model on the route and return a small dictionary or DTO that contains only intended fields. Map expected domain failures to stable status codes and short machine-readable messages. Keep validation details useful without reflecting secrets from request bodies or private database objects.",
        cost="Parsing and response validation consume CPU roughly proportional to the accepted payload and response size. A response model cannot make an unbounded database query cheap; limit rows before building a list of models. Rejecting extra fields makes contract drift visible to callers, but it can require a coordinated rollout when clients are already sending undeclared data. Rich error bodies can help debugging, yet echoing raw request fragments increases data exposure and log volume. Measure rejected input rate by field and client version before changing a contract. Use explicit response projections to reduce object serialization work and avoid lazy ORM loads after the database session closes.",
        failure="Submit a missing operation ID, a short ID, an overlong reason, an unknown approved_by field, and a wrong primitive type. None should reach the approval service. Submit a valid shape as reviewer 81 for case 62; validation must pass but authorization must fail. Return an internal note from a deliberately flawed service response and confirm the public response model does not expose it, then remove the note from the service projection too. Race a stale revision and require a controlled conflict rather than a generic 500. Trigger a database exception and verify the response omits raw SQL and the submitted private reason.",
        drill="Write approval request and public response models for a permit workflow. Seed reviewer 47, reviewer 81, and case 62. Enumerate each client-controlled field and its allowed range, then write negative HTTP tests before implementing the route. Add a service result that carries an internal audit note and ensure the outward projection excludes it. Add an optimistic revision check and map its conflict outcome. Use a list endpoint with a fixed page size to verify output validation stays bounded. Inspect generated API schema and one real JSON response for agreement on field names and nullability.",
        decision="Validate input shape at the transport edge, keep domain permission in the service, and construct a narrow public response.",
        code='''from typing import Annotated, Literal
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from .services import ApprovalService, Reviewer, approval_service, current_reviewer

router = APIRouter()


class ApprovalCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: str = Field(min_length=16, max_length=81)
    reason: str = Field(min_length=3, max_length=470)
    expected_revision: int = Field(ge=1)


class PermitPublic(BaseModel):
    id: int
    status: Literal["pending", "approved"]
    revision: int


@router.post("/permits/{case_id}/approval", response_model=PermitPublic)
def approve_permit(
    case_id: int,
    command: ApprovalCommand,
    reviewer: Annotated[Reviewer, Depends(current_reviewer)],
    service: Annotated[ApprovalService, Depends(approval_service)],
):
    result = service.approve_once(reviewer.id, case_id, command)
    return {"id": result.case_id, "status": result.status, "revision": result.revision}''',
        checks=["Unknown command fields and invalid ranges stop before mutation.", "Reviewer identity is never accepted from the body.", "The outward response contains only public fields."],
        mistakes=["Using one model for private input, database state, and public output.", "Treating schema validity as object permission.", "Returning an ORM object whose lazy fields may load after session cleanup."],
        related=["web-tech/api-contract-evolution-and-client-migration", "web-tech/api-mutation-and-failure-contracts"],
    ),
    dict(
        slug="fastapi-async-sessions-and-transaction-ownership",
        title="FastAPI Async Sessions and Transaction Ownership",
        summary="Give each request a bounded session and keep one command inside one explicit transaction.",
        concept="A database session is a unit of interaction with a database connection pool, not a global application object. A FastAPI dependency can create it and close it when its lifetime ends. The command service decides when to begin, commit, and roll back a transaction; cleanup after a response is too late to be the only definition of success. Async syntax also does not turn a synchronous database driver into nonblocking work. An async route should use an async database session and driver, or remain synchronous with a synchronous session. A returned ORM object can hold lazy relationships that try to query after the session has closed or while a response is being serialized.",
        case="Reviewer 47 approves case 62. The first implementation shares a session object across requests, so a rollback triggered by reviewer 81's failed action contaminates unrelated work. A second implementation commits in dependency teardown after returning a success response; a constraint failure occurs after the client has already seen success. The repaired API creates a session for each request, asks a service to open one transaction, verifies assignment and revision, inserts the approval and outbox row, and commits before building the response. The route returns plain values. A concurrent replay uses a unique operation key and recovers the existing result without a second transition.",
        implementation="Create an async session factory at application setup and yield one session per request through a dependency. Close it in an async context manager. In the approval service, use an explicit transaction block and keep the permission query, status check, operation insert, and outbox insert inside it. Enforce operation uniqueness at the database layer because a pre-insert existence query alone races. Return a materialized DTO after the transaction commits. Never pass a live session into a background task; that task should create its own session. If the response streams from a database cursor, choose a dependency lifetime that actually covers the stream or detach the data before sending. Test the installed framework version's dependency cleanup timing.",
        cost="One session per request can borrow one pooled connection when it executes SQL; pool capacity, transaction duration, and query plan determine throughput. A session dependency with a long response lifetime may hold scarce resources if an endpoint streams slowly. Eagerly materializing 47 summaries consumes O(page size) memory but releases the database before network delivery. A row lock reduces conflicting writes but can queue hot cases. Retained command and outbox rows grow with accepted operations; they need explicit cleanup rules after the replay window. Track connection checkout time, open transaction age, rollback rate, duplicate key conflicts, and response serialization queries, not just endpoint latency.",
        failure="Run two approvals concurrently with the same operation ID and assert one case transition and one outbox row. Force a constraint failure after the case update; no success response should be emitted and the whole transaction should roll back. Invoke an endpoint after another request's rollback and verify its session is independent. Return a lazy relationship in a negative test, close the session, and observe serialization failure; then return a DTO instead. Hold a streaming response open and inspect whether the dependency retains a connection. Cancel the client during an approval and determine whether the database committed; replay the stable operation ID to resolve ambiguity.",
        drill="Create a permit table, reviewer assignment table, operation table with a unique key, and outbox table. Implement a request-scoped async session dependency and an approval service with one transaction. Seed case 62 for reviewer 47 only. Exercise missing permission, stale revision, duplicate operation, and a forced failure after case update. Convert the service outcome into a plain public response before returning. Add a 47-row queue read and measure pool checkout and query count under concurrent requests. Compare the behavior of a fast JSON response and a deliberately slow stream before deciding where session cleanup belongs.",
        decision="Own commit and rollback inside the command service; let the dependency own only request-scoped session cleanup.",
        code='''from collections.abc import AsyncIterator
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .database import session_factory
from .services import ApprovalCommand, ApprovalOutcome, Reviewer, approve_once, current_reviewer

router = APIRouter()


async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


@router.post("/permits/{case_id}/approval")
async def approve_permit(
    case_id: int,
    command: ApprovalCommand,
    reviewer: Annotated[Reviewer, Depends(current_reviewer)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, int | str]:
    outcome: ApprovalOutcome = await approve_once(
        session, reviewer.id, case_id, command.operation_id, command.expected_revision
    )
    return {"case_id": outcome.case_id, "status": outcome.status}''',
        checks=["Every request receives its own session lifetime.", "The command service commits before the response is constructed.", "A unique operation key and durable outbox row share the transaction."],
        mistakes=["Sharing one mutable session between requests.", "Committing only in dependency teardown after a success response.", "Passing a request session into work that runs after the response."],
        related=["web-tech/data-persistence", "web-tech/django-form-csrf-atomic-approval-and-on-commit"],
    ),
    dict(
        slug="fastapi-lifespan-background-work-and-delivery-state",
        title="FastAPI Lifespan, Background Work, and Delivery State",
        summary="Own shared clients during application lifespan and record critical jobs before returning success.",
        concept="An application lifespan groups resources that should be created before requests and closed during shutdown, such as an outbound HTTP client or database engine. A background task attached to a response runs later in the same application process. That is convenient for small best-effort work, but it is not a durable queue and cannot prove that a notification survived a crash. A permit approval with a customer-visible notice needs a durable delivery intent recorded in the transaction that changed the case. The response can then return a committed operation ID while a separate dispatcher sends the message and records attempts. A local background task may wake the dispatcher, but the stored intent is the recovery source.",
        case="An approval endpoint commits case 62 and attaches send_email to a response background task. The process restarts just after sending the 200 response. The task never runs, yet the audit page claims the reviewer notification was issued. Another deployment creates a new outbound client on every request and leaves idle connections behind. The repaired service writes an outbox event with the approval, returns the operation result, and lets a worker claim the event using bounded leases and retries. A lifespan context owns one configured outbound client per process and closes it on shutdown. A background wake-up is optional; a periodic dispatcher still finds pending work after restart.",
        implementation="Create shared network clients in an async lifespan context and store them in application state or a dependency with clear ownership. Close them in the context's finalization path, including partial startup failure where relevant. Do not start migrations or slow remote probes in every request. For critical delivery, write the outbox row before the approval transaction commits; include an event ID and stable recipient snapshot or lookup policy. A dispatcher claims pending events, sends with a provider idempotency key when supported, and records success or retry state. Give each task its own database session and bound concurrency. Use response background tasks only for a best-effort wake-up or other work whose loss is acceptable.",
        cost="A shared outbound client avoids repeated connection setup, but each worker process owns its own pool, so total connections scale with process count. Lifespan startup can delay readiness; close failures can slow shutdown. An outbox adds a row and index work per approval and requires a dispatcher, retry policy, dead-letter inspection, and retention. That overhead buys a recoverable delivery state. In-process response tasks are cheap to schedule but compete with request capacity and vanish on abrupt termination. Track oldest pending event, claim age, retry count, provider result, process restart count, client pool saturation, and the gap between approval commit and notification acceptance.",
        failure="Kill the API process immediately after it returns approval success. Restart the dispatcher and confirm the stored event is still delivered once by event identity. Force a provider timeout after it accepts a message; retry under the same provider key and reconcile ambiguous delivery rather than blindly generating a new event. Crash after claiming an event and confirm its lease expires for recovery. Start the application with an invalid outbound configuration and verify readiness fails without leaked clients. Stop the server under active requests and check that the shared client closes after bounded work. Disable the optional wake-up task and ensure periodic dispatch still empties the outbox.",
        drill="Implement lifespan ownership for one outbound client and a transactional approval outbox. Use case 62, reviewer 47, and an event ID distinct from the HTTP request ID. The approval route commits the status and event together, then returns the saved operation result. Write a dispatcher that claims at most 47 pending events per pass with a finite lease and records attempts. Add fault injection at commit, response, claim, provider acceptance, and process shutdown. Report which failures replay automatically and which require operator review. Ensure a worker obtains its own session instead of reusing a request dependency after response completion.",
        decision="Use lifespan for shared process resources and durable storage for any post-response effect the product promises to deliver.",
        code='''from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import BackgroundTasks, Depends, FastAPI
from .delivery import OutboundClient, wake_dispatcher
from .services import ApprovalCommand, Reviewer, current_reviewer, record_approval_and_outbox


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = OutboundClient(timeout_seconds=5)
    app.state.outbound_client = client
    try:
        yield
    finally:
        await client.aclose()


app = FastAPI(lifespan=lifespan)


@app.post("/permits/{case_id}/approval")
async def approve_permit(
    case_id: int,
    command: ApprovalCommand,
    background_tasks: BackgroundTasks,
    reviewer: Annotated[Reviewer, Depends(current_reviewer)],
):
    outcome = await record_approval_and_outbox(reviewer.id, case_id, command)
    background_tasks.add_task(wake_dispatcher, outcome.event_id)
    return {"operation_id": outcome.operation_id, "status": outcome.status}''',
        checks=["Shared clients are closed on shutdown.", "Approval and outbox intent commit before success is returned.", "Delivery can recover even if the optional wake-up never executes."],
        mistakes=["Treating a response background task as a durable queue.", "Sharing a request session with a task after response completion.", "Creating a fresh outbound connection pool for every request."],
        related=["web-tech/background-workflow-reliability", "web-tech/outbound-email-and-delivery-state"],
    ),
]

assert hub_path not in by_path and len(topics) == 4
hub = copy.deepcopy(by_path["web-tech/django-request-and-persistence-boundaries"])
hub.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + hub_path)), path=hub_path, title=hub_title,
           summary="Build FastAPI services with explicit object permission, narrow contracts, bounded sessions, and recoverable delivery.",
           sort_order=3720, created_at=stamp, updated_at=stamp, published_at=stamp)
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
    ast.parse(topic["code"])
    entry = copy.deepcopy(by_path["web-tech/trace-context-across-request-and-job"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                 title=topic["title"], summary=topic["summary"], sort_order=3721 + number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    related = [hub_path] + ["web-tech/" + other["slug"] for other in topics if other is not topic] + topic["related"]
    body = paragraph(topic["concept"]) + "<h2>Working case</h2>" + paragraph(topic["case"])
    body += '<h2>Implementation boundary</h2><pre><code class="language-python">' + html.escape(topic["code"], quote=False) + "</code></pre>" + paragraph(topic["implementation"])
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
hub["body"] = paragraph("A FastAPI permit service accepts authenticated requests, resolves object permission, validates a narrow command shape, owns database transactions, and dispatches committed work after a response. These lessons use the same review case to show where a typed API still needs explicit policy, resource lifetime, and failure recovery.")
hub["body"] += "<h2>Topics in this track</h2><ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
hub["body"] += "<h2>Prerequisite paths</h2><p>" + "; ".join(link(path) for path in ["web-tech/backend-api-systems", "web-tech/authorization-and-tenant-boundaries", "web-tech/data-persistence"]) + ".</p>"
curriculum = by_path["web-tech/web-technology"]
curriculum["data"]["modules"].append({"title": hub_title, "summary": hub["summary"],
                                       "lessons": [hub_path] + ["web-tech/" + topic["slug"] for topic in topics]})
curriculum["body"] += "<h2>" + link(hub_path) + "</h2>" + paragraph(hub["summary"]) + "<ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
curriculum["updated_at"] = stamp
crosslinks = {
    "web-tech/backend-api-systems": [hub_path],
    "web-tech/authorization-and-tenant-boundaries": ["web-tech/fastapi-dependencies-and-object-authorization"],
    "web-tech/api-contract-evolution-and-client-migration": ["web-tech/fastapi-input-output-models-and-error-contracts"],
    "web-tech/data-persistence": ["web-tech/fastapi-async-sessions-and-transaction-ownership"],
    "web-tech/background-workflow-reliability": ["web-tech/fastapi-lifespan-background-work-and-delivery-state"],
    "web-tech/django-request-and-persistence-boundaries": [hub_path],
}
for path, targets in crosslinks.items():
    by_path[path]["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    by_path[path]["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": 1, "new_lessons": 4,
                  "prose_words": {topic["slug"]: len(re.findall(r"\b[\w'-]+\b", " ".join(str(topic[key]) for key in ("concept", "case", "implementation", "cost", "failure", "drill", "decision", "summary")))) for topic in topics}}))
