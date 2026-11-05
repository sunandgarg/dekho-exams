"""Add a FastAPI permit-service project and assessment drafts."""
import ast
import copy
import datetime
import html
import json
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
lessons = [
    "web-tech/fastapi-dependencies-and-object-authorization",
    "web-tech/fastapi-input-output-models-and-error-contracts",
    "web-tech/fastapi-async-sessions-and-transaction-ownership",
    "web-tech/fastapi-lifespan-background-work-and-delivery-state",
]
project_path = "web-tech/fastapi-permit-service-boundaries-project"
quiz_path = "quizzes/web-development-fastapi-contract-resources"
assert hub_path in by_path and all(path in by_path for path in lessons)
assert project_path not in by_path and quiz_path not in by_path

project = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: FastAPI permit service boundaries",
               summary="Build a scoped permit API with strict contracts, transactional commands, and recoverable notifications.",
               sort_order=3725, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                   "content_format": "html", "seo_ready": False, "kind": "project", "author_path": "authors/aitrove-editorial",
                   "reading_minutes": 10, "related": [hub_path] + lessons}
project["body"] = paragraph(
    "Build a FastAPI permit service for reviewer 47 and reviewer 81. Only reviewer 47 may read or approve case 62. The detail and export metadata routes resolve the case through a permission-scoped dependency. Approval accepts an operation ID, reason, and expected revision under a strict input model, while its public response returns only case ID, status, and revision. The command service uses a request-scoped async database session but owns its transaction explicitly. It records the case change, unique operation result, and notification outbox row together. A response lost after commit can be replayed under the same operation ID. The notification dispatcher has its own session and keeps working after an API process restart. A lifespan context owns one outbound client per process and closes it during shutdown."
)
project["body"] += "<h2>Build contract</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "Resolve an authenticated reviewer, then query the requested case under that reviewer's current assignment.",
    "Reject unknown or out-of-range command fields and build a deliberate public response projection.",
    "Give each request a session; commit one approval transaction before returning success.",
    "Use a unique operation key and outbox event so a lost response or process restart is recoverable.",
    "Close shared outbound resources during application shutdown and keep worker sessions separate from request sessions.",
]) + "</ul>"
checkpoint = '''def may_claim_notification(event_id: str, delivered: set[str], leased: set[str]) -> bool:
    return event_id not in delivered and event_id not in leased


delivered_events = {"permit-62-approved-47"}
leased_events = {"permit-81-reviewed-29"}
print(may_claim_notification("permit-62-approved-47", delivered_events, leased_events))
# Output: False'''
ast.parse(checkpoint)
project["body"] += '<h2>Implementation checkpoint</h2><pre><code class="language-python">' + html.escape(checkpoint, quote=False) + "</code></pre>"
project["body"] += "<h2>Cost and boundaries</h2>" + paragraph(
    "The scoped object lookup adds database work to every private route, which must happen before protected data leaves the service. Input and output model validation cost CPU proportional to the accepted payload and response; bound the queue to 47 rows before serialization. A request session may borrow a pooled connection while SQL runs, so measure checkout waits and open transaction age. Case row locks can queue concurrent approvals. The operation table and outbox grow with retained commands and events, and need a policy for retry, inspection, and expiry. One outbound client per worker saves connection setup but multiplies total remote connections by worker count. A response background task is only a wake-up; the durable row is what survives a restart."
)
project["body"] += "<h2>Failure drill</h2>" + paragraph(
    "Guess case 62 as reviewer 81 through both detail and export routes. Send an unknown approved_by field, an overlong reason, and a stale revision; none may become an authorized approval. Race two requests with one operation ID and inspect the case, operation, and outbox tables. Commit once, discard the HTTP response, and replay the same command to recover the prior result. Force a transaction failure after updating the case and confirm the outbox row also disappears. Kill the API process after a successful response but before the optional wake-up; restart the dispatcher and deliver the pending event. Verify its lease expiry and provider retry behavior under an ambiguous timeout."
)
project["body"] += "<h2>Acceptance checks</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "No read or write crosses a reviewer's current case boundary.",
    "Unknown input is rejected and no internal audit field appears in the response.",
    "Concurrent replay commits one logical approval and one outbox event.",
    "A worker can recover pending delivery after the API process stops.",
]) + "</ul>"
project["body"] += "<h3>Common Mistakes</h3><ul><li>Confusing a valid token with case permission.</li><li>Returning database objects without a public projection.</li><li>Committing after a success response has already left.</li><li>Passing a request session to a response background task.</li></ul>"
project["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["data"]["related"]) + ".</p>"
entries.append(project)
by_path[project_path] = project

questions = [
    ("What does a dependency that verifies a bearer token establish?", ["Caller identity, not permission for every case", "Permission for every case ID", "A committed database transaction"], 0, "Token verification identifies a caller; the requested case still needs its own permission check."),
    ("How should a private case lookup use reviewer 47 and case 62?", ["Fetch case 62 then trust the URL", "Filter by reviewer assignment and case ID together", "Filter only by the token's expiry"], 1, "A scoped repository lookup enforces the current reviewer-to-case relationship in the database."),
    ("Why might missing and forbidden private cases share one response?", ["To bypass authentication", "To avoid schema validation", "To avoid revealing a forbidden case's existence"], 2, "A common private-resource response can limit disclosure to callers who guess case identifiers."),
    ("What should a strict approval input model do with an unknown approved_by field?", ["Reject it", "Use it as reviewer identity", "Store it in the public response"], 0, "Rejecting unknown command fields prevents a client from inventing trusted internal attributes."),
    ("Which fields belong in a public approval response?", ["The full ORM row", "Only explicitly admitted public fields", "Raw audit notes and database connection state"], 1, "A narrow response projection and model keep private internals out of the HTTP result."),
    ("What is still needed after request shape validation succeeds?", ["No more checks", "Only JSON serialization", "Current case authorization and domain-state checks"], 2, "Valid JSON can still ask an unauthorized reviewer to perform a forbidden state change."),
    ("Where should an approval transaction commit?", ["Inside the command service before success is returned", "Only after the response is sent", "Inside a client retry loop"], 0, "The service must know whether its write committed before it reports a confirmed outcome."),
    ("What should own each request's database session?", ["One global mutable session", "A bounded request dependency", "The notification provider"], 1, "A request-scoped session avoids sharing mutable transaction state across unrelated calls."),
    ("What stops concurrent replays from inserting two approvals?", ["A disabled browser button", "A slow response", "A database uniqueness rule on the operation key"], 2, "A unique key at the database boundary arbitrates simultaneous requests with the same logical command ID."),
    ("What belongs in application lifespan?", ["Creation and cleanup of shared process resources", "A new outbound client for every request", "A private case title in a global variable"], 0, "Lifespan provides an explicit startup and shutdown owner for process-level clients and pools."),
    ("Why is a response background task insufficient for promised delivery?", ["It always runs before commit", "It can be lost when the process stops", "It authorizes the wrong reviewer"], 1, "In-process work can vanish after the response, so a durable intent must survive independently."),
    ("What should a notification worker use for database access?", ["The original request session", "A client-supplied SQL connection", "Its own bounded session"], 2, "Work that outlives the request must create and close its own database session."),
]
assert len(questions) == 12 and [sum(row[2] == index for row in questions) for index in range(3)] == [4, 4, 4]
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: FastAPI contract and resource quiz",
            summary="Twelve explained choices about dependencies, models, transactions, lifespan, and delivery.",
            sort_order=3726, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes",
                "content_format": "html", "seo_ready": False,
                "questions": [{"prompt": prompt, "options": options, "answer": answer, "explanation": explanation}
                              for prompt, options, answer, explanation in questions]}
quiz["body"] = paragraph(quiz["summary"] + " Choose an answer, inspect the reason, and return to the related failure drill.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in [hub_path] + lessons + [project_path]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

for index_path, heading, target, summary in [
    ("web-tech/web-technology/project", "FastAPI permit service project", project_path, project["summary"]),
    ("web-tech/quizzes", "FastAPI contract check", quiz_path, quiz["summary"]),
]:
    index = by_path[index_path]
    index["data"]["modules"][0]["lessons"].append(target)
    index["body"] += "<h2>" + heading + "</h2><p>" + link(target) + " — " + html.escape(summary) + "</p>"
    index["updated_at"] = stamp
hub = by_path[hub_path]
hub["body"] += "<h2>Practice and check</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + ".</p>"
hub["updated_at"] = stamp
for path in lessons:
    lesson = by_path[path]
    lesson["body"] += "<h2>Apply and check</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + ".</p>"
    lesson["data"]["related"].extend([project_path, quiz_path])
    lesson["updated_at"] = stamp
curriculum = by_path["web-tech/web-technology"]
curriculum["body"] += "<h2>FastAPI service practice</h2><p>" + link(project_path) + "; " + link(quiz_path) + ".</p>"
curriculum["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": 1, "new_quizzes": 1, "new_questions": 12}))
