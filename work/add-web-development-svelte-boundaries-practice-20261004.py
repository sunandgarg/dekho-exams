"""Add a Svelte permit review project and assessment drafts."""
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


hub_path = "web-tech/svelte-reactivity-and-server-boundaries"
lessons = [
    "web-tech/svelte-runes-source-state-derived-views-and-effect-cleanup",
    "web-tech/svelte-props-callbacks-and-keyed-editor-ownership",
    "web-tech/sveltekit-form-actions-validation-and-mutation-replay",
    "web-tech/sveltekit-request-scoped-load-and-hydration-state",
]
project_path = "web-tech/svelte-permit-review-and-action-project"
quiz_path = "quizzes/web-development-svelte-reactivity-server-boundaries"
assert hub_path in by_path and all(path in by_path for path in lessons)
assert project_path not in by_path and quiz_path not in by_path

project = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: Svelte permit review and approval action",
               summary="Build a queue with derived results, keyed drafts, a server-owned approval action, and private load data.",
               sort_order=3685, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                   "content_format": "html", "seo_ready": False, "kind": "project", "author_path": "authors/aitrove-editorial",
                   "reading_minutes": 9, "related": [hub_path] + lessons}
project["body"] = paragraph(
    "Build a permit review queue for two reviewers whose allowed case sets do not overlap. The first reviewer receives 47 cases in the first server page, searches the list, types a private note, and requests approval for case 62. Begin with a plain POST form that works when JavaScript is disabled. The owner must preserve the note under case 62 through insertion and sorting, show pending state without treating it as a committed server result, and return one approval when a lost response causes the same operation to be replayed. A second reviewer must never see the first reviewer's case IDs in HTML or serialized data. A saved 29-row browser preference may apply after hydration, once the initial page has matched the server's 47-row view."
)
project["body"] += "<h2>Build contract</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "Use one authorized source snapshot and phrase; derive matching rows and count without copying them into writable state.",
    "Key case cards by immutable ID and route approval intent through a parent callback rather than child prop mutation.",
    "Validate the action's fields and server identity, check case permission, and deduplicate a stable operation ID atomically.",
    "Fetch per reviewer in server load, return a bounded payload, and delay browser-only preferences until after first render.",
]) + "</ul>"
project["body"] += '<h2>Implementation checkpoint</h2><pre><code class="language-javascript">' + html.escape(
    'function mayCommitPermitApproval(operationId, committedOperations) {\n'
    '  return !committedOperations.has(operationId);\n'
    '}\n'
    'const committedOperations = new Set(["permit-62-reviewer-47-retry-81"]);\n'
    'console.log(mayCommitPermitApproval("permit-62-reviewer-47-retry-81", committedOperations));\n'
    '// Output: false', quote=False) + "</code></pre>"
project["body"] += "<h2>Cost and boundaries</h2>" + paragraph(
    "Local filtering scans n summaries per changed phrase and may allocate O(n) matching references. Keep the rendered first page bounded even if the server knows about 47,000 cases. Stable row keys retain view state, so private draft storage grows with the number of retained case IDs and needs logout and expiry cleanup. An operation deduplication table grows with retained commands and must be transactional with the approval mutation; a client Set alone is only an illustration of the replay decision, not the production authority. Each server load spends permission and query work for its viewer. Shared caching is safe only when the full visibility boundary is part of the key and invalidation rule. An enhanced form can improve pending feedback, but it costs browser code and must preserve the ordinary POST path."
)
project["body"] += "<h2>Failure drill</h2>" + paragraph(
    "Insert case 29 above a drafted case 62 and reverse sort; the note must remain with 62. Reject approval for case 62 after the card reports intent and confirm every status display returns to the server result. Commit approval, lose the response, and replay the same operation ID; one audit notification may remain. Tamper with the hidden case ID and sign in as a reviewer without permission: the action must reject both paths. Run two concurrent server loads and scan both responses for cross-reviewer case IDs. Hydrate with a stored 29-row preference and a different time zone; the first browser tree must match the server before personalization updates it. Disable scripts and submit the form again."
)
project["body"] += "<h2>Acceptance checks</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "Search results and count describe one authorized snapshot; no stale copied count is displayed.",
    "Every draft, pending command, and committed status remains attached to the intended case ID.",
    "An authorized approval replay yields one logical write; malformed or forbidden requests yield no write.",
    "Server responses and the initial browser tree stay isolated and consistent across reviewers and preferences.",
]) + "</ul>"
project["body"] += "<h3>Common Mistakes</h3><ul><li>Persisting an entire private case snapshot in browser storage.</li><li>Letting a card change its received case object.</li><li>Treating a hidden form field as permission.</li><li>Sharing mutable load state between requests.</li></ul>"
project["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["data"]["related"]) + ".</p>"
entries.append(project)
by_path[project_path] = project

questions = [
    ("A queue has one authorized batch and one search phrase. Where should its visible count come from?", ["A derived visible-case result", "A later effect that copies a number", "The last rendered row index"], 0, "Deriving count from the same visible result keeps the heading and rows aligned with one source batch."),
    ("What is the update rule for a $state.raw server snapshot?", ["Mutate a nested field and assume tracking", "Replace the snapshot value", "Write the count into a separate effect"], 1, "Raw state treats the snapshot as a replaceable value, so an accepted update should assign a new snapshot."),
    ("Which job belongs in $effect?", ["Computing the filtered list", "Copying the count", "Synchronizing an external subscription with cleanup"], 2, "Effects are for external work such as subscriptions, and returned cleanup prevents old work from surviving."),
    ("How should a permit card request approval?", ["Call a parent-owned callback with the case ID", "Mutate the received status object", "Write directly to a global reviewer variable"], 0, "The child reports intent; the parent can then coordinate pending state, the server result, and rollback."),
    ("Which each-block key survives insertion and sorting?", ["The row's position", "The immutable case ID", "A fresh random token for every render"], 1, "An entity ID keeps the same row view and draft owner attached to the record after a reorder."),
    ("A private note must survive switching between cases. Where can its owner be recorded?", ["In one shared input for all rows", "In the current list index", "In an account-scoped map keyed by case ID"], 2, "A case-ID draft map can preserve each note independently and can be cleared at submission or logout."),
    ("Which path must still work when JavaScript is disabled?", ["A plain POST form action", "Only a client click handler", "Only an optimistic status badge"], 0, "A server form action can process the ordinary POST without requiring enhancement or browser script."),
    ("Where does case-level authorization belong for an approval?", ["In a hidden case ID field", "In the server action and mutation service", "In a CSS disabled state"], 1, "The request's authenticated identity and permission for that case must be verified on the server."),
    ("An approval committed but its response was lost. What identifies a safe replay?", ["A new random operation each retry", "The button label", "The same stable operation ID checked atomically"], 2, "Server-owned deduplication must bind replay to the original logical mutation and return its prior result."),
    ("Where should reviewer-specific server load state live?", ["Inside each request", "In a mutable module singleton", "In the previous viewer's cached page"], 0, "Request-scoped data keeps one reviewer's private cases out of another response on a reused worker."),
    ("When may a saved browser row limit change the server-rendered list?", ["Before the initial browser tree differs", "After the first matching render", "By changing server authorization"], 1, "The browser first matches the authorized server view, then applies a local display preference as a later update."),
    ("What is safe to return from a server load function?", ["Every record in the service object", "A module-level current reviewer", "Only serialized fields authorized for that viewer"], 2, "Load data is delivered to the page and may enter HTML or navigation payloads, so it must be viewer-scoped."),
]
assert len(questions) == 12 and [sum(item[2] == index for item in questions) for index in range(3)] == [4, 4, 4]
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: Svelte reactivity and server boundaries quiz",
            summary="Twelve explained choices about runes, keyed ownership, form actions, and private load data.",
            sort_order=3686, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes",
                "content_format": "html", "seo_ready": False,
                "questions": [{"prompt": prompt, "options": options, "answer": answer, "explanation": explanation}
                              for prompt, options, answer, explanation in questions]}
quiz["body"] = paragraph(quiz["summary"] + " Choose an answer, inspect the reason, and return to the matching implementation boundary.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in [hub_path] + lessons + [project_path]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

for index_path, heading, target, summary in [
    ("web-tech/web-technology/project", "Svelte review project", project_path, project["summary"]),
    ("web-tech/quizzes", "Svelte boundary check", quiz_path, quiz["summary"]),
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
curriculum["body"] += "<h2>Svelte review practice</h2><p>" + link(project_path) + "; " + link(quiz_path) + ".</p>"
curriculum["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": 1, "new_quizzes": 1, "new_questions": 12}))
