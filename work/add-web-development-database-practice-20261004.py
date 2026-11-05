"""Add a live database change project and assessment to the local drafts."""
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
    return '<a href="/' + html.escape(path, quote=True) + '">' + html.escape(by_path[path]["title"]) + "</a>"


hub_path = "web-tech/database-capacity-and-online-change-operations"
lessons = [
    "web-tech/connection-pool-budgets-and-queue-admission",
    "web-tech/transaction-retry-deadlock-and-side-effect-boundaries",
    "web-tech/resumable-data-backfills-and-reconciliation",
    "web-tech/online-index-builds-and-query-plan-release-gates",
]
project_path = "web-tech/permit-data-change-with-live-traffic-project"
quiz_path = "quizzes/web-development-database-online-operations"
assert project_path not in by_path and quiz_path not in by_path

project = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
project.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)),
    path=project_path,
    title="Project: permit data change under live traffic",
    summary="Release a duration-field backfill and queue index while preserving connection capacity and write correctness.",
    sort_order=3615,
    created_at=stamp,
    updated_at=stamp,
    published_at=stamp,
)
project["data"] = {
    "subject_root": "web-tech/web-technology",
    "section_path": "web-tech/web-technology/project",
    "content_format": "html",
    "seo_ready": False,
    "kind": "project",
    "author_path": "authors/aitrove-editorial",
    "reading_minutes": 9,
    "related": [hub_path] + lessons,
}
project["body"] = paragraph(
    "Move a permit service from free-text inspection duration to an integer minute field while reviewers keep editing cases. The database contains 2.7 million historical records. Six API replicas, two report workers, and a bounded connection ceiling already serve a busy morning queue. A new index must support organization-scoped open-case review. The release has four independent gates: enough connection capacity, safe transaction retries, a resumable and reconciled backfill, and a valid index with an observed query benefit. A failed gate pauses the dependent reader rollout; it does not silently change the response contract for current users."
)
project["body"] += "<h2>Build contract</h2><ul>" + "".join(
    "<li>" + html.escape(item) + "</li>"
    for item in [
        "Budget every process pool under the database ceiling, reserve emergency slots, and bound acquisition waiting during rollout.",
        "Retry an entire aborted transaction after rereading current case state; persist one outbox intent and deduplicate delivery by operation identity.",
        "Backfill duration in bounded case-ID batches. Keep new writes current, replay a failed chunk safely, and reconcile every unresolved row before reader cutover.",
        "Build the queue index using the chosen engine's supported online procedure. Check validity, representative plans, write latency, and cleanup after cancellation.",
    ]
) + "</ul>"
project["body"] += '<h2>Implementation checkpoint</h2><pre><code class="language-javascript">' + html.escape(
    'function permitReaderCutover(backfillMismatches, indexValid, queueP95Ms, queueBudgetMs) {\n'
    '  return backfillMismatches === 0 && indexValid && queueP95Ms <= queueBudgetMs;\n'
    '}\n'
    'console.log(permitReaderCutover(1, true, 47, 63));\n'
    '// Output: false',
    quote=False,
) + "</code></pre>"
project["body"] += "<h2>Cost and boundaries</h2>" + paragraph(
    "The backfill costs O(N) reads and up to O(N) writes for N historical cases; its chunk size controls lock and log pressure, not total work. The new index uses storage and adds write maintenance. Transaction retries consume extra reads and compute under contention. Pool waiting consumes request memory and time even before SQL begins. Separate metrics for connection acquisition, transaction aborts, backfill lag, index build progress, query p95, and write p95. Keep reviewer notes and personal case contents out of broad operational logs. The project is complete only when the old and new fields agree for every record the new reader may return."
)
project["body"] += "<h2>Failure drill</h2>" + paragraph(
    "Double API replicas during rollout and prove the connection budget still leaves maintenance access. Force opposing lock order on two assignment updates and verify one rolled-back attempt creates no external message. Crash the backfill after a batch commit but before a separate checkpoint and replay it. Edit an already processed case, then reconcile the new minute value. Cancel the concurrent index build and inspect its validity before any queue reader uses it. Finally, show that one mismatched duration keeps the feature gate closed even when the index is valid and queue latency is 47 milliseconds."
)
project["body"] += "<h2>Acceptance checks</h2><ul>" + "".join(
    "<li>" + html.escape(item) + "</li>"
    for item in [
        "No rollout or failover state can demand more connections than the tested ceiling.",
        "Retryable conflicts restart the whole transaction; committed side effects appear once.",
        "A crash, concurrent edit, or late import cannot leave an undetected duration mismatch.",
        "The index is valid and useful for representative tenants before the new queue depends on it.",
    ]
) + "</ul>"
project["body"] += "<h3>Common Mistakes</h3><ul><li>Scaling application replicas without scaling the connection budget.</li><li>Advancing a backfill checkpoint before its data is durable.</li><li>Releasing a query solely because its index definition exists.</li></ul>"
project["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["data"]["related"]) + ".</p>"
entries.append(project)
by_path[project_path] = project

questions = [
    ("Six API replicas each hold up to 29 connections. What must the database budget include?", ["Those 174 slots plus workers and reserves", "Only one replica's 29 slots", "Only active browser tabs"], 0, "Fleet-wide maximum demand includes every replica, worker, scheduled job, and reserved maintenance connection, not one process alone."),
    ("A pool is full while the database slows. What prevents waiting from growing without bound?", ["More idle browser tabs", "A finite waiter limit and acquisition deadline", "A longer request timeout only"], 1, "The pool queue consumes application time and memory; admission must have both a bounded size and a bounded wait."),
    ("Where should a handler wait for an external image service?", ["Inside an open database transaction", "While holding a leased connection", "After releasing its database connection"], 2, "A slow external call must not occupy a scarce database slot and extend lock ownership for unrelated requests."),
    ("A serialization conflict aborts an assignment. What should the retry repeat?", ["The whole transaction, including fresh reads", "Only the final UPDATE", "Only the email send"], 0, "A fresh transaction must re-evaluate current state and permission; retrying a fragment keeps an outdated decision."),
    ("What belongs inside a retryable transaction instead of a direct email send?", ["A browser alert", "One durable outbox intent", "An unbounded sleep"], 1, "The outbox intent commits with the database state and can be delivered afterward under a stable identity."),
    ("A unique constraint reports a business conflict. What should a narrow retry policy do?", ["Retry forever", "Convert it into a deadlock", "Stop and return the domain conflict"], 2, "Constraint violations often express real data conflicts and must not be classified as transient serialization failures."),
    ("A backfill crashes after a chunk writes but before its checkpoint. What property allows restart?", ["Idempotent replay of that chunk", "A larger HTTP cache", "An unbounded transaction"], 0, "The last chunk may run again, so conversion and conditional writes must produce the same stored result on replay."),
    ("A user edits an already processed row. Why is the high-water mark insufficient?", ["It resets all primary keys", "It records traversal progress, not later correctness", "It prevents every insert"], 1, "A checkpoint says which keys were visited; the write path or reconciliation must cover edits behind it."),
    ("Which result is required before readers rely only on the new duration field?", ["A worker log saying done", "One sample case converted", "Reconciliation of all relevant rows and exceptions"], 2, "A completed scan alone cannot prove agreement for concurrent edits, malformed rows, or late imported cases."),
    ("What can a failed PostgreSQL concurrent index build leave behind?", ["An invalid index artifact that needs inspection", "A guaranteed valid index", "A second application database"], 0, "An interrupted or failed build can leave an artifact that exists but is unusable for the intended query and needs cleanup."),
    ("Why separate an index build from the dependent queue release?", ["To avoid testing real data", "To gate the query on validity and measured plan benefit", "To remove tenant filters"], 1, "The reader should depend on the index only after build, validity, representative plan, and write-latency checks pass."),
    ("What makes an index worth keeping after the release?", ["Its name matches the endpoint", "It uses every table column", "Measured read benefit exceeds storage and write costs"], 2, "An index has ongoing maintenance and storage cost, so its value depends on the actual workload and observed query plan."),
]
assert len(questions) == 12 and [sum(question[2] == index for question in questions) for index in range(3)] == [4, 4, 4]
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
    path=quiz_path,
    title="Web Development: database online operations quiz",
    summary="Twelve explained choices about pool capacity, transaction retries, backfills, and index gates.",
    sort_order=3616,
    created_at=stamp,
    updated_at=stamp,
    published_at=stamp,
)
quiz["data"] = {
    "subject_root": "web-tech/web-technology",
    "section_path": "web-tech/quizzes",
    "content_format": "html",
    "seo_ready": False,
    "questions": [
        {"prompt": prompt, "options": options, "answer": answer, "explanation": explanation}
        for prompt, options, answer, explanation in questions
    ],
}
quiz["body"] = paragraph(quiz["summary"] + " Choose an answer, inspect its explanation, then return to the related lesson for a missed boundary.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in [hub_path] + lessons + [project_path]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path["web-tech/web-technology/project"]
project_hub["data"]["modules"][0]["lessons"].append(project_path)
project_hub["body"] += "<h2>Live data change project</h2><p>" + link(project_path) + " — " + html.escape(project["summary"]) + "</p>"
project_hub["updated_at"] = stamp
quiz_hub = by_path["web-tech/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Database operations check</h2><p>" + link(quiz_path) + " — " + html.escape(quiz["summary"]) + "</p>"
quiz_hub["updated_at"] = stamp
hub = by_path[hub_path]
hub["body"] += "<h2>Practice and check</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + ".</p>"
hub["updated_at"] = stamp
for path in lessons:
    entry = by_path[path]
    entry["body"] += "<h2>Apply and check</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + ".</p>"
    entry["data"]["related"].extend([project_path, quiz_path])
    entry["updated_at"] = stamp
root_entry = by_path["web-tech/web-technology"]
root_entry["body"] += "<h2>Database operations practice</h2><p>" + link(project_path) + "; " + link(quiz_path) + ".</p>"
root_entry["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": 1, "new_quizzes": 1, "new_questions": len(questions), "answer_positions": {str(index): sum(question[2] == index for question in questions) for index in range(3)}}))
