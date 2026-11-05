"""Add Vue permit review project and assessment drafts."""
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


def p(value):
    return "<p>" + html.escape(value) + "</p>"


def link(path):
    assert path in by_path, path
    return '<a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a>"


hub_path = "web-tech/vue-reactivity-and-component-boundaries"
lessons = [
    "web-tech/vue-source-state-computed-views-and-large-snapshots",
    "web-tech/vue-watch-cleanup-and-stale-request-ownership",
    "web-tech/vue-props-emits-and-keyed-editor-ownership",
    "web-tech/vue-server-rendering-and-hydration-stability",
]
project_path = "web-tech/vue-permit-review-queue-project"
quiz_path = "quizzes/web-development-vue-reactivity-boundaries"
assert project_path not in by_path and quiz_path not in by_path

project = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: Vue permit review queue",
               summary="Build one review queue with derived counts, cancelable details, owned mutations, and stable hydration.",
               sort_order=3665, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                   "content_format": "html", "seo_ready": False, "kind": "project", "author_path": "authors/aitrove-editorial",
                   "reading_minutes": 9, "related": [hub_path] + lessons}
project["body"] = p(
    "Build a Vue permit review queue whose source snapshot contains 47,000 records. A reviewer searches, opens a case detail, writes a private note, and requests approval. Keep the case snapshot and search phrase as authoritative inputs; visible rows and count must be derived together. Switching from case 47 to 81 while a detail request is pending must invalidate the old request even when a test transport ignores abort. The case card proposes an approval through an event; the parent owns pending state, operation identity, server response, and rollback. Sorting or inserting a row must never move a note to another case. The server-rendered first view must be isolated per request and agree with the first browser render before a saved preference applies."
)
project["body"] += "<h2>Build contract</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "Derive filtered rows and count from a single snapshot; replace large shallow data immutably if shallow tracking is chosen.",
    "Watch only selected identity fields, register cleanup immediately, and reject stale or mismatched response payloads.",
    "Give rows stable case ID keys, emit approval commands, and keep private drafts owned by case ID.",
    "Create request-scoped server state and reuse its permitted snapshot for the first browser render.",
]) + "</ul>"
project["body"] += '<h2>Implementation checkpoint</h2><pre><code class="language-javascript">' + html.escape(
    'function mayPublishPermitDetail(requestGeneration, activeGeneration, responseCaseId, selectedCaseId) {\n'
    '  return requestGeneration === activeGeneration && responseCaseId === selectedCaseId;\n'
    '}\n'
    'console.log(mayPublishPermitDetail(47, 81, 47, 81));\n'
    '// Output: false', quote=False) + "</code></pre>"
project["body"] += "<h2>Cost and boundaries</h2>" + p(
    "Filtering a snapshot is O(n) for n cases and may allocate an O(n) result array. Computed caching prevents unnecessary reruns when dependencies stay stable but cannot make each changed phrase free. Shallow tracking avoids nested proxy work, provided updates replace data instead of mutating a hidden field. A watcher can abort obsolete requests, yet the server may already have done work and an abort-ignoring transport still requires a generation guard. Saved drafts and pending operations consume memory proportional to active cases; define cleanup at submission, logout, and expiry. Per-request server state costs initialization time but prevents data crossing reviewer sessions. Serialized boot data uses response bytes and must exclude records the viewer is not allowed to see."
)
project["body"] += "<h2>Failure drill</h2>" + p(
    "Type a phrase while a new snapshot arrives and check that count and rows agree. Mutate a nested object under shallow storage as a negative test, then repair the update by replacing the case and snapshot. Select case 47, then 81; return 81 first and 47 last, with abort ignored. Only case 81 may appear. Reject an approval from the server after a card emits its request; no other component should retain an optimistic status. Insert case 29 ahead of a drafted case and reverse sorting. Run two simultaneous server renders for different reviewers on one worker, then hydrate one browser with a different time zone and saved filter. Check private data isolation and initial markup agreement."
)
project["body"] += "<h2>Acceptance checks</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "Rows and count correspond to the same snapshot and phrase after every update.",
    "No stale detail, late response, or rejected approval appears as current data.",
    "Drafts stay with their case IDs through sort, insert, switch, and logout.",
    "Two server requests cannot share selected case state, and hydration begins from matching permitted data.",
]) + "</ul>"
project["body"] += "<h3>Common Mistakes</h3><ul><li>Keeping filtered rows and count as separately writable state.</li><li>Assuming request abort alone prevents a stale response from publishing.</li><li>Sharing user-specific refs across server requests or mutating a child prop.</li></ul>"
project["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["data"]["related"]) + ".</p>"
entries.append(project)
by_path[project_path] = project

questions = [
    ("A list and count depend on the same snapshot and phrase. Where should the count come from?", ["The computed visible list", "An unrelated delayed watcher", "The current row index"], 0, "Deriving count from the same visible-list computation keeps both values aligned in one reactive update."),
    ("What does a computed value cache against?", ["Any wall-clock change", "Its reactive dependencies", "The size of the browser window only"], 1, "A computed getter re-evaluates when reactive values it used change; an ordinary time read is not reactive by itself."),
    ("A shallow ref holds immutable cases. How should a changed case become visible?", ["Mutate a nested field silently", "Write a second count ref", "Replace the snapshot or affected immutable path"], 2, "Shallow tracking observes the top-level value, so replacing that value is the declared update boundary."),
    ("What should a watcher own when selection starts a fetch?", ["The request and its invalidation cleanup", "Every derived count", "A random list key"], 0, "The watcher is the external synchronization boundary and should register cancellation as soon as the run starts."),
    ("Why keep a generation check after aborting an older request?", ["To make the URL shorter", "Abort may not stop an already delivered or mock response", "To give the old response priority"], 1, "Abort helps reduce work, but a separate current-generation check prevents obsolete data from publishing."),
    ("Which response may replace case 81 detail?", ["Any response arriving last", "A successful response for case 47", "One matching the active generation and case ID"], 2, "Both request generation and selected identity must still match before private detail can enter the current panel."),
    ("A child receives a case object prop. Who should commit approval state?", ["The parent that owns the record", "The child by mutating a nested status", "The template key"], 0, "An emitted command lets the parent coordinate pending state, server response, and rollback around one authoritative record."),
    ("What key survives insertion and sorting of permit rows?", ["The row's current position", "An immutable case ID", "A new random token each render"], 1, "A stable entity ID keeps component state and private drafts associated with the same case across reorderings."),
    ("Switching to another case should reset local editor state. Which boundary is smallest?", ["The entire app root", "Every queue row", "The selected editor subtree keyed by case ID"], 2, "Keying only the editor changes the lifetime of the form without remounting the whole queue and its unrelated state."),
    ("How should user-specific Vue state be created for server rendering?", ["Fresh for each request", "One mutable module ref for every visitor", "From the previous response's cache"], 0, "Request-scoped state prevents a long-running server worker from carrying one reviewer's private selection into another response."),
    ("When may a saved browser-only display preference change a server-rendered view?", ["During an incompatible first render", "After mount as a separate update", "Only by editing server authorization"], 1, "The first browser render should match authorized server HTML; a local display preference can apply after hydration."),
    ("A server/client mismatch was recovered automatically. What is the appropriate response?", ["Ignore every warning", "Serialize more private data", "Find the unstable markup or initial data"], 2, "Recovery can discard and rebuild nodes, so the underlying structure or data mismatch still deserves correction."),
]
assert len(questions) == 12 and [sum(item[2] == index for item in questions) for index in range(3)] == [4, 4, 4]
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: Vue reactivity and boundaries quiz",
            summary="Twelve explained choices about computed state, request cleanup, component ownership, and hydration.",
            sort_order=3666, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes",
                "content_format": "html", "seo_ready": False,
                "questions": [{"prompt": prompt, "options": options, "answer": answer, "explanation": explanation}
                              for prompt, options, answer, explanation in questions]}
quiz["body"] = p(quiz["summary"] + " Choose an answer, inspect the explanation, and return to the lesson behind a missed boundary.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in [hub_path] + lessons + [project_path]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path["web-tech/web-technology/project"]
project_hub["data"]["modules"][0]["lessons"].append(project_path)
project_hub["body"] += "<h2>Vue review queue project</h2><p>" + link(project_path) + " — " + html.escape(project["summary"]) + "</p>"
project_hub["updated_at"] = stamp
quiz_hub = by_path["web-tech/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Vue state check</h2><p>" + link(quiz_path) + " — " + html.escape(quiz["summary"]) + "</p>"
quiz_hub["updated_at"] = stamp
hub = by_path[hub_path]
hub["body"] += "<h2>Practice and check</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + ".</p>"
hub["updated_at"] = stamp
for path in lessons:
    entry = by_path[path]
    entry["body"] += "<h2>Apply and check</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + ".</p>"
    entry["data"]["related"].extend([project_path, quiz_path])
    entry["updated_at"] = stamp
curriculum = by_path["web-tech/web-technology"]
curriculum["body"] += "<h2>Vue state practice</h2><p>" + link(project_path) + "; " + link(quiz_path) + ".</p>"
curriculum["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": 1, "new_quizzes": 1, "new_questions": 12}))
