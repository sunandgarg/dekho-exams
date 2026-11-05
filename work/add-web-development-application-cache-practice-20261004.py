"""Add a cache-recovery project and assessment to the local drafts."""
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


hub_path = "web-tech/application-cache-consistency-and-capacity"
lessons = [
    "web-tech/cache-aside-fill-races-and-version-guards",
    "web-tech/cache-stampede-singleflight-and-hot-key-budgets",
    "web-tech/cache-memory-eviction-and-degraded-read-paths",
    "web-tech/negative-cache-entries-and-stale-read-contracts",
]
project_path = "web-tech/permit-cache-recovery-and-consistency-project"
quiz_path = "quizzes/web-development-application-cache-contracts"
assert project_path not in by_path and quiz_path not in by_path

project = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
project.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)),
    path=project_path,
    title="Project: permit cache recovery and consistency",
    summary="Keep case reads correct through stale fills, hot-key expiry, eviction, and source failures.",
    sort_order=3625,
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
    "The permit portal caches case summaries and a daily district count. Case approval must read current source state; the count may be up to 47 seconds old. Six API replicas share the cache, and a morning refresh sends 900 browsers to one hot key. During a rollout, the cache restarts empty, a reviewer creates a case previously cached as absent, and an old read fill races a newer approval. Build the cache layer so each condition has a recorded outcome. The database stays authoritative. A cache failure can slow an allowed read but cannot invent an approval, grant access, or convert a timeout into a legitimate not-found response."
)
project["body"] += "<h2>Build contract</h2><ul>" + "".join(
    "<li>" + html.escape(item) + "</li>"
    for item in [
        "Publish a retained version floor after each case write and reject an old fill even when the value slot is empty.",
        "Collapse district-count refresh within each replica, bound cross-replica source work, and expire any refresh lease after a crash.",
        "Set a memory and entry-size budget; test cold-cache and unreachable-cache reads against source connection limits.",
        "Represent present, confirmed absent, stale, and source error separately; invalidate absence on case creation and enforce route-specific maximum ages.",
    ]
) + "</ul>"
project["body"] += '<h2>Implementation checkpoint</h2><pre><code class="language-javascript">' + html.escape(
    'function admitCachedCase(versionFloor, loadedVersion, authoritativeAction) {\n'
    '  if (authoritativeAction) return "read-source";\n'
    '  return loadedVersion < versionFloor ? "reject-old-fill" : "store-copy";\n'
    '}\n'
    'console.log(admitCachedCase(30, 29, false));\n'
    '// Output: reject-old-fill',
    quote=False,
) + "</code></pre>"
project["body"] += "<h2>Cost and boundaries</h2>" + paragraph(
    "A retained version floor adds one comparison and an atomic cache update per fill, plus storage even when the value is absent. Singleflight retains at most one in-flight load per active key within an instance, but a shared refresh lease adds network work and needs a fencing rule. A smaller memory budget increases source misses; an excessive budget can crowd host memory. Negative entries reduce repeated absent-case queries but delay new-case visibility unless creation invalidates them. Measure source calls per hot-key burst, stale-version rejects, floor-publication failures, maximum stale age, memory use, evictions, miss admission, and user-visible case latency. A hit-rate graph without source-load and correctness checks is not an acceptance test."
)
project["body"] += "<h2>Failure drill</h2>" + paragraph(
    "Pause a version 29 fill, approve the case as version 30, publish the version floor, clear the value slot, then resume the old fill; version 29 must be rejected. Fail the floor publication in another run and confirm the service reports bounded stale behavior rather than a strict guarantee. Expire the count key across all six replicas while 900 readers arrive, then record how many aggregate queries reach the database. Kill the refresh-lease holder and let another instance complete; the old holder cannot overwrite it. Fill the cache with oversized inspection previews and restart it at peak load while source admissions remain bounded. Query a missing case, create it before its negative lifetime ends, and confirm the creation invalidates absence. Finally, time out the source; the result must be an error, never a cached not-found."
)
project["body"] += "<h2>Acceptance checks</h2><ul>" + "".join(
    "<li>" + html.escape(item) + "</li>"
    for item in [
        "Late fills cannot pass a newer version floor, even when the cached value is absent.",
        "Hot-key expiry and cold restart stay within the database miss budget.",
        "Memory pressure evicts only disposable copies and preserves the essential source-backed path.",
        "Absent, stale, denied, and failed reads remain distinct, with current authority for every mutation.",
    ]
) + "</ul>"
project["body"] += "<h3>Common Mistakes</h3><ul><li>Declaring success from steady-state hit rate alone.</li><li>Using one global TTL for counts, permissions, and absent cases.</li><li>Testing cache restart without concurrent peak traffic.</li></ul>"
project["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["data"]["related"]) + ".</p>"
entries.append(project)
by_path[project_path] = project

questions = [
    ("A version 29 fill finishes after version 30 was committed and its floor published. What should happen?", ["Reject the old fill", "Replace version 30", "Delete the source record"], 0, "The retained version floor rejects an old fill even when the cached value slot was cleared by invalidation."),
    ("Why does delete-after-write alone not close every cache-aside race?", ["It disables database commits", "A paused old read may refill after deletion", "It changes the tenant ID"], 1, "A read may load old data before the write and place it in the cache after the writer deletes the key."),
    ("Which read must bypass a merely eventual case-summary cache?", ["A public aggregate count", "A decorative chart label", "A current approval permission check"], 2, "A permission or approval decision requires current authority; a display cache cannot grant the action."),
    ("What can process-local singleflight guarantee across six API replicas?", ["At most one load per key within each process", "Exactly one load across the fleet", "No cache misses ever"], 0, "Each process can collapse its own concurrent callers, while other replicas may still load the same key."),
    ("A refresh-lease owner crashes. Which property is needed?", ["An infinite lock", "A lease expiry and safe takeover", "A public cache for approvals"], 1, "A bounded lease lets another worker refresh after a crash; old holders must not overwrite newer results."),
    ("What does expiry jitter mainly reduce?", ["Incorrect authorization", "Database transaction conflicts", "Synchronized scheduled misses"], 2, "Staggering expiration can spread routine refresh work, though it cannot by itself handle a full cache flush."),
    ("Large preview entries evict hot case summaries. What should be reconsidered?", ["Entry size and workload-specific memory budgets", "Browser font size", "Only the SQL table name"], 0, "A few large entries can displace many useful small copies; size caps and separate budgets protect the working set."),
    ("A cache restart makes every read miss. Which path needs an explicit limit?", ["Only the cache dashboard", "Source-read admission", "The page title length"], 1, "A cold cache shifts work to the source, which needs a measured concurrency and timeout budget."),
    ("Which data must not live solely in an evicting performance cache?", ["A disposable district count", "A recomputable case summary", "Authoritative session or job state"], 2, "Eviction is acceptable for replaceable copies, not the sole record of a durable or security-sensitive fact."),
    ("A missing case is created during its negative-cache lifetime. What helps users see it?", ["Creation invalidates or bounds the negative entry", "Treat every timeout as absent", "Keep absence forever"], 0, "A confirmed absence can become false when a new record is created; invalidation or a short bound restores visibility."),
    ("A database timeout occurs during an absent-case lookup. How should it be classified?", ["Confirmed not-found", "Source error, separate from absence", "Permission granted"], 1, "An unavailable source did not prove the record is absent, so caching not-found would hide an outage."),
    ("A stale case list still offers Approve. What decides the mutation?", ["The old list value", "The cached button state", "Current source permission and record version"], 2, "A stale display may aid reading, but the server must recheck authority and version before committing an action."),
]
assert len(questions) == 12 and [sum(question[2] == index for question in questions) for index in range(3)] == [4, 4, 4]
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
    path=quiz_path,
    title="Web Development: application cache contracts quiz",
    summary="Twelve explained choices about stale fills, hot keys, eviction, and negative results.",
    sort_order=3626,
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
project_hub["body"] += "<h2>Application cache project</h2><p>" + link(project_path) + " — " + html.escape(project["summary"]) + "</p>"
project_hub["updated_at"] = stamp
quiz_hub = by_path["web-tech/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Application cache check</h2><p>" + link(quiz_path) + " — " + html.escape(quiz["summary"]) + "</p>"
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
root_entry["body"] += "<h2>Application cache practice</h2><p>" + link(project_path) + "; " + link(quiz_path) + ".</p>"
root_entry["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": 1, "new_quizzes": 1, "new_questions": len(questions), "answer_positions": {str(index): sum(question[2] == index for question in questions) for index in range(3)}}))
