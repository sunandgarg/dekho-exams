"""Add a Laravel permit-service project and assessment drafts."""
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


hub_path = "web-tech/laravel-policy-query-and-queue-boundaries"
lessons = [
    "web-tech/laravel-route-binding-policy-and-private-resource-scope",
    "web-tech/laravel-eloquent-loading-and-cursor-page-cost",
    "web-tech/laravel-form-request-transaction-and-approval-replay",
    "web-tech/laravel-after-commit-jobs-and-outbox-recovery",
]
project_path = "web-tech/laravel-permit-review-workflow-project"
quiz_path = "quizzes/web-development-laravel-policy-query-queue"
assert hub_path in by_path and all(path in by_path for path in lessons)
assert project_path not in by_path and quiz_path not in by_path

project = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: Laravel permit review workflow",
               summary="Build a policy-scoped case flow with bounded queries, replay-safe approvals, and a recoverable outbox.",
               sort_order=3735, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                   "content_format": "html", "seo_ready": False, "kind": "project", "author_path": "authors/aitrove-editorial",
                   "reading_minutes": 10, "related": [hub_path] + lessons}
project["body"] = paragraph(
    "Build a Laravel permit-review workflow for reviewer 47 and reviewer 81. Reviewer 47 may inspect and approve case 62; reviewer 81 may not discover its private title by guessing a route ID. A detail route uses model binding plus a policy and returns a deliberate resource projection. The queue contains at most 47 cases, with district labels and attachment counts, ordered by creation time and a unique ID for cursor continuation. A browser approval form carries CSRF protection, a stable operation ID, a reason, and an expected revision. Its service rechecks permission in a transaction, locks current case state, and writes one approval result and one outbox event. A lost HTTP response can be replayed under the same ID. A post-commit job wakes delivery, while a sweep recovers events if that dispatch is lost."
)
project["body"] += "<h2>Build contract</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "Authenticate the reviewer, bind the case, and authorize view and approval as separate actions.",
    "Scope the queue in SQL, eager load the displayed district, count attachments, and cap each cursor page at 47 cases.",
    "Validate browser input and current assignment; store one unique command outcome and outbox row per approval.",
    "Delay the queue wake-up until commit, then recover any pending outbox row through an independent sweep.",
    "Map missing, forbidden, stale, duplicate, and internal outcomes to controlled responses with no private notes.",
]) + "</ul>"
checkpoint = '''<?php
function mayClaimPermitEvent(string $eventId, array $deliveredIds, array $leasedIds): bool
{
    return !in_array($eventId, $deliveredIds, true)
        && !in_array($eventId, $leasedIds, true);
}

$deliveredIds = ['permit-62-approved-47'];
$leasedIds = ['permit-81-reviewed-29'];
var_export(mayClaimPermitEvent('permit-62-approved-47', $deliveredIds, $leasedIds));
// Output: false'''
subprocess.run(["php", "-l"], input=checkpoint, text=True, capture_output=True, check=True)
project["body"] += '<h2>Implementation checkpoint</h2><pre><code class="language-php">' + html.escape(checkpoint, quote=False) + "</code></pre>"
project["body"] += "<h2>Cost and boundaries</h2>" + paragraph(
    "A private detail route pays for binding and policy work before it may return data. A list policy implemented as a per-row relationship lookup can make a 47-case page issue many queries; the queue must scope by reviewer in SQL. Eager loading and attachment counts remove repeated reads but still add database work, so inspect actual rows and plans. Cursor pagination reduces deep-offset cost when order columns are indexed, at the price of numbered-page navigation. An approval lock serializes conflicting writes for one case. Operation and outbox rows use storage proportional to the replay and delivery windows. A queue worker and sweep add capacity needs, yet they make promised notifications inspectable and recoverable after a process restart."
)
project["body"] += "<h2>Failure drill</h2>" + paragraph(
    "Guess case 62 as reviewer 81 through detail and export routes. Render 47 cases and measure query count with district eager loading removed, then restore it. Seed equal creation timestamps and follow cursor pages without duplicate IDs. Submit approval without a CSRF token, with a stale revision, and with reviewer 81's valid session. Race two requests using one operation ID. Commit an approval, lose its response, and replay; inspect case, operation, and outbox rows for one logical transition. Roll back before commit and confirm the wake-up job does not run. Kill the process after commit but before dispatch and let the sweep recover the pending event. Force a provider timeout after possible acceptance and reconcile by event identity."
)
project["body"] += "<h2>Acceptance checks</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "A valid login never grants access to a case outside its current policy scope.",
    "The reviewer queue stays bounded and deterministic without an N+1 relation pattern.",
    "A replay preserves one status change, operation row, and outbox event.",
    "A lost queue wake-up does not erase a committed notification intent.",
]) + "</ul>"
project["body"] += "<h3>Common Mistakes</h3><ul><li>Assuming model binding includes authorization.</li><li>Eager loading children for an unbounded list.</li><li>Sending provider messages inside a retried database transaction.</li><li>Equating an after-commit queue hint with durable intent.</li></ul>"
project["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["data"]["related"]) + ".</p>"
entries.append(project)
by_path[project_path] = project

questions = [
    ("What does Laravel route model binding establish for case 62?", ["A model lookup, not reviewer permission", "Permission for any signed-in reviewer", "A committed approval transaction"], 0, "Binding resolves an identifier to a model; a policy still has to check the current reviewer and action."),
    ("Which check belongs before returning a private PermitResource?", ["Only a matching route parameter", "A view policy for this reviewer and case", "A successful queue dispatch"], 1, "The route must authorize the resolved case before serializing any of its private fields."),
    ("Why might a policy deny as not found?", ["To avoid querying assignments", "To disable the route", "To avoid disclosing a forbidden case's existence"], 2, "A private-resource policy can choose a missing-style response for both forbidden and absent cases."),
    ("What addresses repeated district queries in a bounded queue?", ["Eager loading the displayed district relation", "Loading every case before filtering", "Adding a longer HTTP timeout"], 0, "Loading the needed relation with the page avoids a separate district query for each rendered case."),
    ("How can a queue show attachment totals without loading every attachment model?", ["An unbounded with call", "An attachment count query or withCount", "A browser-side sum of hidden cases"], 1, "A count projection yields the displayed total without hydrating every attachment record."),
    ("What makes cursor continuation safe when creation timestamps tie?", ["An offset alone", "Sorting by status alone", "A unique case ID in the ordering"], 2, "A unique tie breaker gives the cursor a deterministic position among equal timestamps."),
    ("What does browser CSRF validation check?", ["The token-bearing request boundary", "The reviewer's current case assignment", "The queue worker's lease"], 0, "CSRF protection rejects an untrusted browser submission; it does not replace object authorization."),
    ("Where should a replay-safe approval result be enforced?", ["Only by disabling the button", "By a unique operation key in the database", "By a fresh ID on every retry"], 1, "A database uniqueness constraint arbitrates simultaneous retries of the same logical command."),
    ("Why must external email stay outside a deadlock-retried transaction closure?", ["It is always free", "It changes route binding", "The closure may execute again after a retry"], 2, "Retry can repeat nontransactional effects even if the database rolls back the first attempt."),
    ("What does after-commit dispatch prevent?", ["A worker reading an uncommitted row", "A lost dispatch after process crash", "Every possible duplicate provider send"], 0, "Dispatch after commit keeps the worker from seeing data before it is visible or after rollback."),
    ("What survives a crash after approval commit but before queue dispatch?", ["Only an in-memory callback", "A transactional outbox row", "A browser click handler"], 1, "The outbox row commits with the case and can be found by a later independent sweep."),
    ("How should a worker handle an ambiguous provider timeout?", ["Create a new unrelated event", "Assume the API response failed", "Retry or reconcile under the same event identity"], 2, "The provider may have accepted the first attempt; stable identity limits duplicate external delivery."),
]
assert len(questions) == 12 and [sum(row[2] == index for row in questions) for index in range(3)] == [4, 4, 4]
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: Laravel policy, query, and queue quiz",
            summary="Twelve explained decisions about policies, Eloquent cost, approval replay, and outbox recovery.",
            sort_order=3736, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes",
                "content_format": "html", "seo_ready": False,
                "questions": [{"prompt": prompt, "options": options, "answer": answer, "explanation": explanation}
                              for prompt, options, answer, explanation in questions]}
quiz["body"] = paragraph(quiz["summary"] + " Choose an answer, inspect the reason, and return to the related failure drill.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in [hub_path] + lessons + [project_path]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

for index_path, heading, target, summary in [
    ("web-tech/web-technology/project", "Laravel permit workflow project", project_path, project["summary"]),
    ("web-tech/quizzes", "Laravel workflow check", quiz_path, quiz["summary"]),
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
curriculum["body"] += "<h2>Laravel workflow practice</h2><p>" + link(project_path) + "; " + link(quiz_path) + ".</p>"
curriculum["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": 1, "new_quizzes": 1, "new_questions": 12}))
