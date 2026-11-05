"""Add a Django permit-service project and assessment drafts."""
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


hub_path = "web-tech/django-request-and-persistence-boundaries"
lessons = [
    "web-tech/django-middleware-session-and-object-permissions",
    "web-tech/django-queryset-shape-prefetch-and-page-cost",
    "web-tech/django-form-csrf-atomic-approval-and-on-commit",
    "web-tech/django-asgi-async-view-and-sync-orm-boundary",
]
project_path = "web-tech/django-permit-review-service-project"
quiz_path = "quizzes/web-development-django-request-persistence"
assert hub_path in by_path and all(path in by_path for path in lessons)
assert project_path not in by_path and quiz_path not in by_path

project = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: Django permit review service",
               summary="Build a permission-scoped case queue and replay-safe approval with measured ORM and async boundaries.",
               sort_order=3715, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                   "content_format": "html", "seo_ready": False, "kind": "project", "author_path": "authors/aitrove-editorial",
                   "reading_minutes": 10, "related": [hub_path] + lessons}
project["body"] = paragraph(
    "Build a permit review service with two reviewers and disjoint assignments. Reviewer 47 may inspect and approve case 62; reviewer 81 may not learn its private title by guessing the URL. The queue shows at most 47 cases per page with district and attachment summaries, ordered by creation time and ID. The approval form uses CSRF protection and a stable operation ID. One submitted command changes state once, writes an audit operation and durable notification intent in the same transaction, and survives a lost HTTP response. A separate async read endpoint may await an external jurisdiction status, but its permission-scoped database work must return fully materialized values from a synchronous service. Keep the write transaction inside one synchronous function."
)
project["body"] += "<h2>Build contract</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "Order session and authentication middleware, then authorize the exact case in every read and command service.",
    "Bound the queue to 47 parents, join only its district, prefetch only displayed attachments, and test deep continuation.",
    "Reject missing CSRF tokens and invalid operation IDs; use a database uniqueness rule for command replay.",
    "Commit the approval and outbox event together, then wake delivery after commit without treating a callback as durable storage.",
    "Bridge synchronous ORM evaluation once from the async read view and apply a deadline to its external request.",
]) + "</ul>"
checkpoint = '''function mayCommitApproval(commandId, committedIds) {
  return !committedIds.has(commandId);
}
const committedIds = new Set(["case-62-reviewer-47-command-81"]);
console.log(mayCommitApproval("case-62-reviewer-47-command-81", committedIds));
// Output: false'''
subprocess.run(["node", "--check"], input=checkpoint, text=True, capture_output=True, check=True)
project["body"] += '<h2>Implementation checkpoint</h2><pre><code class="language-javascript">' + html.escape(checkpoint, quote=False) + "</code></pre>"
project["body"] += "<h2>Cost and boundaries</h2>" + paragraph(
    "A permission-scoped lookup adds database work to each private route, and that work must occur before a protected effect. A bounded queue uses O(page size plus fetched attachments) application memory; prefetching an entire unbounded result set may remove repeated queries while exhausting memory. A high offset can still force the database to scan earlier rows, so an indexed cursor is a better fit for long feeds. Approval locks can queue when reviewers race on one case; keep remote calls outside the transaction. Retaining command IDs and outbox events uses storage proportional to the chosen replay and delivery windows. An async view still needs thread capacity for its synchronous ORM bridge and a finite budget for external I/O."
)
project["body"] += "<h2>Failure drill</h2>" + paragraph(
    "Try anonymous access, a guessed case URL, and a valid reviewer with the wrong assignment. Render 47 queue rows and count SQL statements; remove the prefetch in a negative test to expose per-row queries. Submit the approval form without a CSRF token, then race two submissions with one operation ID. Drop the successful response and replay the same ID: the case status, audit record, and outbox intent must still exist once. Roll back a transaction and confirm no notification is sent. Delay the external status endpoint and enforce its deadline. Return a lazy QuerySet from a bridged service in a negative test and show why the response serializer must not evaluate it later."
)
project["body"] += "<h2>Acceptance checks</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "Every private read and write verifies the current reviewer-to-case mapping.",
    "Queue cost remains bounded, deterministic, and measured on a realistic data set.",
    "A duplicate command returns its existing outcome without another transition or event.",
    "The async endpoint performs no lazy synchronous ORM work on the event loop.",
]) + "</ul>"
project["body"] += "<h3>Common Mistakes</h3><ul><li>Checking login while skipping case permission.</li><li>Prefetching every attachment before applying a page boundary.</li><li>Sending notification before commit or relying only on an in-process callback.</li><li>Splitting a transaction across several async ORM bridges.</li></ul>"
project["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["data"]["related"]) + ".</p>"
entries.append(project)
by_path[project_path] = project

questions = [
    ("What must precede authentication middleware when the application uses sessions?", ["Session middleware", "The permit detail view", "The final 404 handler"], 0, "Authentication depends on the session state prepared earlier in the middleware request chain."),
    ("Reviewer 81 is signed in. What permits a read of private case 62?", ["A guessed URL", "A case-specific permission mapping", "Any active login session"], 1, "The view or service must verify this reviewer's current permission for the exact case."),
    ("Why might a private view return 404 for both missing and forbidden cases?", ["To skip authentication", "To avoid an index", "To avoid disclosing that a forbidden case exists"], 2, "A common missing-resource response can prevent the route from revealing private case existence."),
    ("Which loading method suits a district foreign key shown on each row?", ["select_related", "An unbounded attachment prefetch", "A per-row query in the template"], 0, "A single-valued relation can be joined with select_related instead of queried once for every rendered case."),
    ("When should a many-valued attachment relation be prefetched?", ["Before selecting every case in the database", "After fixing a bounded page that displays attachments", "For every route whether displayed or not"], 1, "Prefetch only data the bounded response needs; otherwise the extra query and memory have no value."),
    ("What makes continuation stable when cases share a creation timestamp?", ["An arbitrary offset only", "Sorting by status alone", "A unique ID tie breaker in the order and cursor"], 2, "A deterministic composite order prevents equal timestamps from creating repeated or skipped rows."),
    ("What does a CSRF token protect in a browser approval form?", ["The browser-origin request boundary", "The reviewer's case assignment", "The database's unique command key"], 0, "CSRF checks the browser request's origin-related token and does not replace object authorization."),
    ("What stops two concurrent replays of one approval command?", ["A disabled Submit button", "A server-side unique operation key", "A longer HTTP timeout"], 1, "The database uniqueness rule is the final arbiter when simultaneous requests carry the same logical command ID."),
    ("When should the notification wake-up callback run?", ["Before case validation", "Before the transaction commits", "After a successful commit"], 2, "A post-commit callback must not announce work that the transaction later rolls back."),
    ("What should an async view do with a synchronous transactional service?", ["Call it through one sync_to_async bridge", "Split each transaction query across awaits", "Disable async safety checks"], 0, "Keep the transactional unit synchronous and bridge once so the database invariant remains together."),
    ("Why return materialized dictionaries from a bridged ORM read?", ["They bypass permission checks", "Lazy ORM work cannot escape into async serialization", "They make all database operations free"], 1, "A lazy QuerySet or model relation might query later on the event loop outside the safe bridge."),
    ("When does ASGI improve this route's capacity?", ["Whenever async appears in a function name", "When every query is synchronous", "When measured nonblocking waits can overlap under bounded load"], 2, "Async operation helps when actual I/O waits overlap; blocking work and adapted middleware still consume capacity."),
]
assert len(questions) == 12 and [sum(row[2] == index for row in questions) for index in range(3)] == [4, 4, 4]
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: Django request and persistence quiz",
            summary="Twelve explained decisions about permissions, query shape, CSRF, transactions, and async views.",
            sort_order=3716, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes",
                "content_format": "html", "seo_ready": False,
                "questions": [{"prompt": prompt, "options": options, "answer": answer, "explanation": explanation}
                              for prompt, options, answer, explanation in questions]}
quiz["body"] = paragraph(quiz["summary"] + " Choose an answer, inspect the reason, and return to the related failure drill.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in [hub_path] + lessons + [project_path]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

for index_path, heading, target, summary in [
    ("web-tech/web-technology/project", "Django permit service project", project_path, project["summary"]),
    ("web-tech/quizzes", "Django request check", quiz_path, quiz["summary"]),
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
curriculum["body"] += "<h2>Django request practice</h2><p>" + link(project_path) + "; " + link(quiz_path) + ".</p>"
curriculum["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": 1, "new_quizzes": 1, "new_questions": 12}))
