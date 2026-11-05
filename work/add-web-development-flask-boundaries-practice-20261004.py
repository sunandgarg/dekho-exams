"""Add a Flask permit-service project and explained assessment."""
import copy
import datetime
import html
import json
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
    return '<a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a>"


hub_path = "web-tech/flask-context-and-service-boundaries"
lessons = [
    "web-tech/flask-request-context-and-object-authorization",
    "web-tech/flask-sqlalchemy-session-and-query-lifetime",
    "web-tech/flask-command-validation-and-transaction-replay",
    "web-tech/flask-async-views-and-durable-background-work",
]
project_path = "web-tech/flask-permit-service-boundaries-project"
quiz_path = "quizzes/web-development-flask-context-service-boundaries"
assert hub_path in by_path and all(path in by_path for path in lessons)
assert project_path not in by_path and quiz_path not in by_path

project = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: Flask permit service boundaries",
               summary="Build a scoped Flask permit flow with bounded reads, replayable approval, and durable notification intent.",
               sort_order=3745, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                   "content_format": "html", "seo_ready": False, "kind": "project", "author_path": "authors/aitrove-editorial",
                   "reading_minutes": 10, "related": [hub_path] + lessons + ["python/flask-routing", "python/flask-keyset-list"]}
project["body"] = paragraph(
    "Build a Flask permit service around reviewer 47 and case 62. Reviewer 47 may see and approve the case; reviewer 81 must not discover its private note by guessing an ID. A detail route projects only public fields after an assignment-scoped query. A queue returns at most 47 cases with district labels and attachment totals, with timestamp and ID ordering. An approval command carries an operation ID, expected revision, and bounded reason. Browser CSRF checking, JSON shape validation, current object permission, and a short database transaction have separate jobs. The transaction stores one case transition, operation result, and outbox event. A lost HTTP response can be replayed under the same ID. A worker with its own application context claims the outbox row under a lease; a sweep finds it even when the queue hint is lost."
)
project["body"] += "<h2>Build contract</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "Use request context only at the HTTP edge and pass an explicit reviewer ID to services.",
    "Scope every private read in SQL and project only the fields shown to this reviewer.",
    "Bound each queue page, count attachments in SQL, and use a unique ordering tie breaker.",
    "Reject malformed commands, stale revisions, forbidden cases, and changed-payload replay.",
    "Commit the approval and outbox row together; recover delivery independently of the queue hint.",
]) + "</ul>"
checkpoint = '''def may_claim_event(event_id: str, delivered_ids: set[str], leased_ids: set[str]) -> bool:
    return event_id not in delivered_ids and event_id not in leased_ids

delivered_ids = {"permit-62-approved-47"}
leased_ids = {"permit-81-reviewed-29"}
print(may_claim_event("permit-62-approved-47", delivered_ids, leased_ids))'''
result = subprocess.run(["python3", "-c", checkpoint], capture_output=True, text=True, check=True)
assert result.stdout.strip() == "False"
project["body"] += '<h2>Implementation checkpoint</h2><pre><code class="language-python">' + html.escape(checkpoint, quote=False) + "</code></pre>"
project["body"] += "<h2>Cost and boundaries</h2>" + paragraph(
    "The detail route pays for an assignment predicate as well as the case lookup. A 47-row queue remains bounded only when scope and limit are in SQL; filtering after loading the full table transfers private rows and increases memory. Attachment counts cost database work but avoid loading every attachment model. An approval lock serializes conflicting writes for one permit, while unique operation records consume storage over the replay horizon. The outbox adds a write and a worker sweep, yet leaves an inspectable record when a process fails. A Flask async view still occupies a WSGI worker, so use it for concurrent awaited I/O within one request, not as a substitute for durable delivery."
)
project["body"] += "<h2>Failure drill</h2>" + paragraph(
    "Guess case 62 as reviewer 81 through detail, export, and download paths. Add a private_note fixture and assert that no response includes it. Seed 47 cases with equal created times and follow all cursor pages without duplicate IDs. Give one case 620 attachments and inspect whether the list hydrates any attachment models. Submit malformed JSON, a bool revision, a missing CSRF token, and an expired assignment. Race two requests with the same operation ID. Commit an approval, discard the response, then retry the exact command and inspect one case transition and one outbox row. Roll back before commit, kill the process after commit but before queue submission, expire a worker lease, and timeout the provider after possible acceptance."
)
project["body"] += "<h2>Acceptance checks</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "A valid session never grants another reviewer's permit access.",
    "Queue memory and row counts stay bounded while timestamp ties traverse deterministically.",
    "An exact replay returns the stored result; changed input under the same ID conflicts.",
    "A committed outbox event is recoverable after a lost wake-up or worker restart.",
]) + "</ul>"
project["body"] += "<h3>Common Mistakes</h3><ul><li>Passing Flask context proxies into services or workers.</li><li>Serializing the full ORM model after an access check.</li><li>Using process memory as the approval replay ledger.</li><li>Treating an async child task or queue hint as durable intent.</li></ul>"
project["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["data"]["related"]) + ".</p>"
entries.append(project)
by_path[project_path] = project

questions = [
    ("What does a Flask request context make available?", ["Request-local proxies while that request is active", "A permanent request object for queue workers", "Permission for every permit ID"], 0, "The request context provides proxies for current request handling; later workers need explicit inputs and their own context."),
    ("Why pass reviewer_id into a permit service?", ["To avoid database indexes", "To make identity explicit outside the HTTP context", "To let the browser choose its reviewer"], 1, "An explicit validated identity keeps service logic independent of request and g proxies and supports isolated tests."),
    ("What does a matching case ID prove?", ["The reviewer may approve", "The outbox was sent", "Only that a lookup may locate that case"], 2, "Object permission must still be checked against the current reviewer, action, and assignment."),
    ("Which query strategy bounds a reviewer queue?", ["Scope and limit in SQL before projection", "Fetch all cases then filter Python objects", "Load every attachment to count them"], 0, "The database should restrict reviewer rows and page width before private records reach the application."),
    ("Why project scalar values before the request ends?", ["To disable SQL constraints", "To avoid later lazy reads from a removed session", "To give a worker the original request proxy"], 1, "Plain values do not depend on Flask-SQLAlchemy's context-scoped session after the view returns."),
    ("What makes timestamp-ordered cursor pages deterministic?", ["A larger HTTP timeout", "A client-provided reviewer ID", "A unique ID tie breaker after the timestamp"], 2, "Equal creation timestamps need a unique secondary order so continuation has one exact position."),
    ("What must be rejected before an approval write?", ["A bool used as an integer revision", "A valid server-derived reviewer identity", "A database uniqueness constraint"], 0, "Python treats bool as a subclass of int, so a strict revision parser must reject that malformed command value."),
    ("Where is one replay outcome arbitrated under a race?", ["In a disabled browser button", "By a database uniqueness rule on the operation identity", "Inside an in-memory set on one worker"], 1, "A database constraint coordinates concurrent processes and retains the committed operation outcome."),
    ("What should a changed payload under the same operation ID do?", ["Produce a fresh approval", "Reuse the old outcome silently", "Return a conflict after comparing stored command fields"], 2, "Reusing one ID for different commands is ambiguous and must not be treated as a safe exact replay."),
    ("What is true of a Flask async view on WSGI?", ["It still occupies a worker for its request", "It guarantees every child task completes later", "It makes synchronous ORM code nonblocking"], 0, "Awaited I/O may reduce one response latency, but the WSGI worker remains tied to that request cycle."),
    ("What survives a crash after approval commit but before queue submission?", ["A scheduled asyncio task", "An outbox row committed with the approval", "The request's g object"], 1, "Transactional intent remains in the database and an independent sweep can locate it after restart."),
    ("What should a worker receive from the route?", ["The request LocalProxy", "A live ORM object and session", "A stable event ID used with a fresh app context"], 2, "Stable identifiers cross the process boundary; the worker opens its own resources and uses the same event identity on retry."),
]
assert len(questions) == 12 and [sum(row[2] == index for row in questions) for index in range(3)] == [4, 4, 4]
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: Flask context and service boundaries quiz",
            summary="Twelve explained decisions about context lifetime, scoped reads, replay, and durable delivery.",
            sort_order=3746, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes",
                "content_format": "html", "seo_ready": False,
                "questions": [{"prompt": prompt, "options": options, "answer": answer, "explanation": explanation}
                              for prompt, options, answer, explanation in questions]}
quiz["body"] = paragraph(quiz["summary"] + " Choose an answer, inspect the reason, and return to the related failure drill.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in [hub_path] + lessons + [project_path]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

for index_path, heading, target, summary in [
    ("web-tech/web-technology/project", "Flask permit service project", project_path, project["summary"]),
    ("web-tech/quizzes", "Flask boundary check", quiz_path, quiz["summary"]),
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
curriculum["body"] += "<h2>Flask service practice</h2><p>" + link(project_path) + "; " + link(quiz_path) + ".</p>"
curriculum["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": 1, "new_quizzes": 1, "new_questions": 12}))
