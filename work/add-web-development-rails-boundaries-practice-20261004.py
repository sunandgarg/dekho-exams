"""Add a Rails permit-workflow project and explained quiz."""
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


hub_path = "web-tech/rails-request-record-and-job-boundaries"
lessons = [
    "web-tech/rails-controller-parameters-and-object-permission",
    "web-tech/rails-active-record-scope-eager-load-and-page-cost",
    "web-tech/rails-locking-transaction-and-command-replay",
    "web-tech/rails-active-job-after-commit-and-outbox-recovery",
]
project_path = "web-tech/rails-permit-review-workflow-project"
quiz_path = "quizzes/web-development-rails-request-record-job"
assert hub_path in by_path and all(path in by_path for path in lessons)
assert project_path not in by_path and quiz_path not in by_path

project = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: Rails permit review workflow",
               summary="Build a scoped Rails permit queue, one replayable approval transaction, and recoverable notification delivery.",
               sort_order=3755, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                   "content_format": "html", "seo_ready": False, "kind": "project", "author_path": "authors/aitrove-editorial",
                   "reading_minutes": 10, "related": [hub_path] + lessons}
project["body"] = paragraph(
    "Build a Rails permit workflow for reviewer 47, reviewer 81, and case 62. Reviewer 47 may inspect and approve the case; reviewer 81 cannot discover its private district note by guessing an ID. The controller derives identity from the server session, admits only the approval command fields, and uses a reviewer-scoped relation for private reads. The queue shows at most 47 cases with district labels and attachment totals, ordered by creation time and ID. An approval request carries operation ID, expected revision, and a bounded reason. A short transaction locks current case state, checks current assignment, and commits one status change, one operation result, and one outbox event. Exact retry after a lost response returns that result; changed input under the same ID conflicts. An Active Job wake-up waits for commit, while a sweep finds a pending event if queue handoff was lost."
)
project["body"] += "<h2>Build contract</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "Use authentication, browser authenticity-token checks, strong parameters, and exact case permission as separate guards.",
    "Scope the queue before limiting; preload displayed district data and avoid materializing attachment collections for counts.",
    "Lock current case state, check assignment and revision, and commit a unique operation outcome with the outbox row.",
    "Defer queue wake-up until commit and recover pending outbox rows through an independent bounded sweep.",
    "Project private responses narrowly and map missing, forbidden, stale, replay, and internal failures deliberately.",
]) + "</ul>"
checkpoint = '''def claimable?(event_id, delivered_ids, leased_ids)
  !delivered_ids.include?(event_id) && !leased_ids.include?(event_id)
end

delivered_ids = ["permit-62-approved-47"]
leased_ids = ["permit-81-reviewed-29"]
puts claimable?("permit-62-approved-47", delivered_ids, leased_ids)'''
result = subprocess.run(["ruby"], input=checkpoint, capture_output=True, text=True, check=True)
assert result.stdout.strip() == "false"
project["body"] += '<h2>Implementation checkpoint</h2><pre><code class="language-ruby">' + html.escape(checkpoint, quote=False) + "</code></pre>"
project["body"] += "<h2>Cost and boundaries</h2>" + paragraph(
    "A reviewer-scoped detail lookup pays for the assignment predicate, but avoids returning private data before permission is established. The queue should remain O(47) in parent objects for one page. Eager loading the displayed district prevents repeated queries; eager loading every attachment can still consume memory proportional to all child records. A keyset cursor reduces deep-offset scanning when the filter and order have suitable indexes, while exact numbered pages require a different cost choice. A row lock serializes competing approvals for case 62. Unique operation and outbox rows add writes and retained storage, but make lost responses and queue handoff failures inspectable. An after-commit enqueue prevents uncommitted reads; it does not replace durable intent when the queue uses separate storage."
)
project["body"] += "<h2>Failure drill</h2>" + paragraph(
    "Guess case 62 as reviewer 81 through show and export routes. Submit extra status and reviewer_id fields with a valid authenticity token, then submit a valid command with no token. Give the queue 47 timestamp ties and one case with 620 attachments; inspect query count, object allocations, and continuation order. Revoke reviewer 47's assignment after loading the page and attempt approval. Race two requests under the same operation ID, lose one HTTP response, and replay. Change the reason under that same ID and require a conflict. Raise after case update but before outbox insertion, then inspect rollback. Commit and kill the web process before enqueue; the sweep must later find the event. Expire a worker lease and retry a provider timeout under the same external event key."
)
project["body"] += "<h2>Acceptance checks</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "A valid login does not grant another reviewer's case access or permit status mass assignment.",
    "The bounded queue has no district N+1 queries and no unbounded attachment hydration.",
    "One operation ID creates one committed result and one outbox event across concurrent exact retries.",
    "A lost queue hint cannot erase notification intent committed with the approval.",
]) + "</ul>"
project["body"] += "<h3>Common Mistakes</h3><ul><li>Using strong parameters as if they authorize a record.</li><li>Fixing N+1 by loading all children for every list page.</li><li>Sending provider email from the case transaction.</li><li>Assuming post-commit enqueue is a durable outbox.</li></ul>"
project["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["data"]["related"]) + ".</p>"
entries.append(project)
by_path[project_path] = project

questions = [
    ("What do Rails strong parameters establish?", ["Which submitted fields may enter assignment", "That reviewer 81 may view case 62", "That a transaction has committed"], 0, "Strong parameters restrict mass assignment; authentication and record-specific permission remain separate checks."),
    ("What should a private show action load?", ["Any case matching an integer ID", "A case from the current reviewer's scoped relation", "All cases before filtering in Ruby"], 1, "A reviewer-scoped relation prevents a guessed ID from returning another reviewer's private record."),
    ("Why keep a narrow response projection?", ["To bypass CSRF checks", "To make queries unindexed", "To avoid serializing hidden model fields"], 2, "An authorized response can still leak private columns if it renders the whole Active Record object."),
    ("What prevents repeated district reads across 47 queue cards?", ["Preloading the displayed district association", "Loading every attachment too", "Increasing the HTTP timeout"], 0, "A bounded preload removes per-row district lookups without hydrating unrelated attachment collections."),
    ("When does pluck run its SQL query?", ["Only after rendering every template", "Immediately when pluck is called", "Only when a worker starts"], 1, "Pluck returns an array of scalar values and executes the relation, so later scope methods cannot be chained onto it."),
    ("Why append case ID to a created_at cursor order?", ["To turn off authentication", "To provide an exact total", "To distinguish cases sharing the timestamp"], 2, "The unique ID gives cursor continuation a deterministic position among equal creation times."),
    ("What belongs inside the approval transaction?", ["Current-state permission, case update, operation, and outbox write", "Provider email and browser rendering", "Only a preloaded model from an earlier GET"], 0, "The transaction should atomically store the authorized result and durable delivery intent without external effects."),
    ("What arbitrates simultaneous exact retries across app processes?", ["A disabled browser button", "A database uniqueness constraint on operation identity", "One process-local Ruby array"], 1, "A unique database key coordinates concurrent workers and permits retrieval of the committed winner's result."),
    ("What should happen when one operation ID carries a changed reason?", ["Approve again", "Return the old result without comparison", "Reject the changed-payload replay as a conflict"], 2, "A stable operation ID identifies one logical command; different fields under it are not an exact replay."),
    ("What does enqueue-after-commit prevent?", ["A worker reading a case before its transaction commits", "A crash after commit before queue handoff", "All duplicate external provider deliveries"], 0, "Deferring enqueue orders worker visibility after commit, while a separate outbox is needed for lost handoff recovery."),
    ("What remains after a post-commit crash before enqueue?", ["Only an in-memory callback", "An outbox row written with the case transaction", "A guaranteed broker message"], 1, "The committed outbox row can be found by an independent sweep even if the queue wake-up never arrived."),
    ("How should a worker retry an ambiguous provider timeout?", ["Invent a new event each attempt", "Reuse a stale request object", "Retain the same event identity for retry or reconciliation"], 2, "The provider may already have accepted the send, so stable identity reduces duplicate external effects."),
]
assert len(questions) == 12 and [sum(row[2] == index for row in questions) for index in range(3)] == [4, 4, 4]
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: Rails request, record, and job quiz",
            summary="Twelve explained decisions about Rails permission, query cost, transaction replay, and job recovery.",
            sort_order=3756, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes",
                "content_format": "html", "seo_ready": False,
                "questions": [{"prompt": prompt, "options": options, "answer": answer, "explanation": explanation}
                              for prompt, options, answer, explanation in questions]}
quiz["body"] = paragraph(quiz["summary"] + " Choose an answer, inspect the reason, and return to the related failure drill.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in [hub_path] + lessons + [project_path]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

for index_path, heading, target, summary in [
    ("web-tech/web-technology/project", "Rails permit workflow project", project_path, project["summary"]),
    ("web-tech/quizzes", "Rails workflow check", quiz_path, quiz["summary"]),
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
curriculum["body"] += "<h2>Rails workflow practice</h2><p>" + link(project_path) + "; " + link(quiz_path) + ".</p>"
curriculum["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": 1, "new_quizzes": 1, "new_questions": 12}))
