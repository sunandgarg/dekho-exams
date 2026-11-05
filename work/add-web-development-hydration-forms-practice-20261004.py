"""Add original projects and explained decisions for rendering/data and forms."""

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
    return f"<p>{html.escape(value)}</p>"


def link(path):
    assert path in by_path, path
    return f'<a href="/{html.escape(path, quote=True)}">{html.escape(by_path[path]["title"])}</a>'


projects = [
    dict(path="web-tech/case-queue-rendering-and-mutation-project", title="Project: server-rendered case queue",
         summary="Build a first-render snapshot, scoped client cache, and conflict-aware optimistic case action.",
         intro="Build a review queue for accounts 29 and 62. A direct visit to case 47 must show useful server-rendered HTML before application code loads; hydration must use precisely the same first snapshot. The client receives only the fields needed for that first interaction, including record version and retrieval time. When reviewer 29 resolves case 47, update the detail and both queue memberships immediately with a pending marker, then reconcile from the server response. Reopen the case in another tab and force version conflicts. A late read from before the edit must not put 47 back into Pending. The project is complete only when account switching clears private cache entries and a shared server cache cannot leak case 47 to account 62.",
         scope=["Render server HTML and first client tree from one request-scoped snapshot; test two time zones and a stored preference change.",
                "Bootstrap a minimal client record with a freshness deadline, then measure cold-entry duplicate requests and return-route revalidation.",
                "Key detail and queue entries by account, record, filter, and page; map each write to the affected views.",
                "Use a conditional version and stable retry identity; settle two mutations in reverse order and repair a conflict from the server record."],
         code='function canApplyCaseResponse(response, activeAccountId, currentVersion) {\n  return response.accountId === activeAccountId && response.version >= currentVersion;\n}\nconsole.log(canApplyCaseResponse({ accountId: 29, version: 6 }, 29, 7));\n// Output: false',
         cost="Rendering n queue rows is O(n) for the first tree and consumes corresponding DOM memory. A bootstrap snapshot adds bytes to the HTML, but avoids an immediate duplicate fetch when its freshness window is still valid. Updating m cache views can trigger m reads or local transformations; broad invalidation is easier to reason about and may cost more network traffic. An optimistic before-image consumes extra memory until confirmation. Document the first-content and interaction timings alongside stale-view defects so a fast screen is not accepted while it displays the wrong case.",
         failure="First make the server render Pending while a stored client value says Resolved. Capture the hydration warning and fix the first-render source. Next reuse a request cache across two accounts and inspect the resulting HTML for private data; the cache must be scoped before any browser reconciliation. Delay an old Pending fetch until after a successful Resolve write and ensure its response cannot restore old membership. Finally time out the mutation after a server commit, retry with the same identity, and verify one accepted transition. A version conflict should present the new server record and a clear recovery choice, never an unexplained silent rollback.",
         checks=["Initial HTML and hydration agree across locale and stored-preference changes.", "Account 62 never sees account 29's server HTML or client cache rows.", "A late read and a reverse-order write response cannot overwrite a newer accepted version.", "Timeout retry produces one server mutation and an honest final UI state."],
         mistakes=["Reading browser-only data during the initial server-matched render.", "Using a shared private server cache across requests.", "Invalidating only the detail view after a queue-changing write.", "Rolling back a failed mutation over a later accepted change."],
         related=["web-tech/hydration-and-deterministic-first-render", "web-tech/server-data-bootstrap-and-freshness", "web-tech/client-cache-keys-and-invalidation", "web-tech/optimistic-mutations-and-rollback", "web-tech/record-level-authorization"]),
    dict(path="web-tech/recoverable-case-intake-form-project", title="Project: recoverable case intake form",
         summary="Build a working native form with raced validation, honest autosave, and upload acceptance states.",
         intro="Build an intake form with Save draft and Send for review actions. It must submit to a server route with JavaScript disabled, preserve entered values after a server error, and identify which submitter initiated the request. Add a live reference check that may return out of order; a result for CASE-47 must not describe the field after the operator changes it to CASE-62. Save a recoverable local draft of a 120-character diagnosis, label its state separately from a server-confirmed save, and compare its base version with the server when the page reopens. Add evidence upload with Selected, Transferring, Processing, Accepted, and Rejected states. The server owns final validation and file acceptance.",
         scope=["Use native controls and a real form action so both submitter paths remain operable without the client bundle.",
                "Apply asynchronous field feedback only when its value and sequence still match current input; keep final uniqueness validation on the server.",
                "Persist a private local draft with account, record, and base version; handle quota failure, sign-out, and a newer server version.",
                "Send evidence with FormData and a browser-set multipart boundary; document one-shot retry identity or a chunk session with integrity and finalization."],
         code='function canShowReferenceResult(request, inputValue, latestSequence) {\n  return request.value === inputValue && request.sequence === latestSequence;\n}\nconsole.log(canShowReferenceResult({ value: "CASE-47", sequence: 3 }, "CASE-62", 4));\n// Output: false',
         cost="A native form serializes f controls in O(f) work and can complete without a client runtime. An eager reference check may send one request per edit; debounce reduces traffic but delays feedback. Local draft serialization costs O(k) for k stored bytes and may fail at quota. A b-byte file needs O(b) transfer; a c-byte chunk protocol introduces roughly O(b/c) requests and temporary server storage. The implementation should measure request count, interrupted-work recovery, and the accuracy of saved-state labels, because apparent speed is worthless when it conceals rejected work.",
         failure="Disable JavaScript and verify both actions still reach distinct server behavior. Reenable it, then delay the first reference response until after the second; old feedback must be ignored even if cancellation raced with completion. Interrupt autosave after the request leaves, close the tab, and reopen after another browser advances the server version. Both draft and server text must remain available until the operator chooses. Send a file with an intentionally hand-written multipart Content-Type and observe the parse failure, then restore browser header ownership. Reject a transferred file during server processing and confirm the UI never calls it Accepted.",
         checks=["Keyboard submission and both actions work without scripts.", "Out-of-order validation cannot replace feedback for a newer value.", "A local draft never claims server confirmation and does not overwrite a newer version.", "Upload transfer, processing, and acceptance remain separate states."],
         mistakes=["Using submit() to trigger a normal validated form action.", "Treating a field-availability response as a final reservation.", "Clearing a draft before server confirmation.", "Setting multipart Content-Type manually for FormData."],
         related=["web-tech/native-form-submission-and-progressive-enhancement", "web-tech/asynchronous-field-validation-races", "web-tech/autosave-draft-recovery-and-conflicts", "web-tech/multipart-upload-progress-and-retry-boundaries", "web-tech/form-server-validation"]),
]

for number, project in enumerate(projects, start=1):
    assert project["path"] not in by_path
    subprocess.run(["node", "--check", "--input-type=module"], input=project["code"],
                   text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project["path"])),
                 path=project["path"], title=project["title"], summary=project["summary"],
                 sort_order=1060 + number, created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                     "content_format": "html", "seo_ready": False, "kind": "project",
                     "author_path": "authors/aitrove-editorial", "reading_minutes": 8, "related": project["related"]}
    body = paragraph(project["intro"])
    body += "<h2>Build contract</h2><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in project["scope"]) + "</ul>"
    body += '<h2>Implementation checkpoint</h2><pre><code class="language-javascript">' + html.escape(project["code"], quote=False) + "</code></pre>"
    body += "<h2>Cost and boundaries</h2>" + paragraph(project["cost"])
    body += "<h2>Failure drill</h2>" + paragraph(project["failure"])
    body += "<h2>Acceptance checks</h2><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in project["checks"]) + "</ul>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in project["mistakes"]) + "</ul>"
    body += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["related"]) + ".</p>"
    entry["body"] = body
    entries.append(entry)
    by_path[entry["path"]] = entry

quiz_path = "quizzes/web-development-rendering-forms-decisions"
questions = [
    ("What should the first client render use for a server-rendered case status?", ["The exact server snapshot for that request", "A stale browser-storage value", "A new random status"], "A server-rendered view hydrates against the browser's first component tree. A browser-only status read can change the text before hydration, so use the serialized request snapshot first and reconcile afterward."),
    ("When should browser-only preferences change the rendered page?", ["After a stable first render has hydrated", "Before the initial client tree is created", "Only after a full page reload"], "The first tree must agree with server HTML. Read local preferences after hydration, then update presentation with a layout and accessibility plan for the change."),
    ("How should private server query data be cached?", ["Per request or within an authorization-safe scope", "In one process-global entry named case", "Only by the page title"], "A shared private cache can place one user's data into another user's server HTML. Request ownership and complete identity are required before client-side repair is even relevant."),
    ("What should a client bootstrap include to support freshness?", ["A minimal record plus retrieval time or version", "Only a permanent fresh flag", "Every historical event in the database"], "The first client view needs enough data to continue and a way to decide when to refresh. A minimal snapshot avoids a redundant immediate fetch without making old data permanent."),
    ("Which values belong in a filtered queue cache key?", ["Account, filter, and page inputs", "Only the word queue", "The latest button label"], "A cache key must represent the response identity. Omitting account or filter can reuse private or semantically wrong rows across routes and users."),
    ("What must a Resolve mutation refresh besides case detail?", ["Any list or count whose membership changes", "Only the action button color", "Nothing after an optimistic update"], "A status change may remove a case from Pending and add it to Resolved. Keeping only detail current leaves contradictory queue views on screen."),
    ("What should happen after a version conflict in an optimistic edit?", ["Reconcile with the authoritative server record", "Always restore the oldest local snapshot", "Mark the edit successful despite rejection"], "A blind rollback can erase a later accepted mutation or a colleague's edit. Fetch or use the server's current record, then present an explicit recovery choice."),
    ("Which programmatic form method follows normal validation and submitter behavior?", ["requestSubmit with the intended button", "submit without any button", "A synthetic click on a generic div"], "requestSubmit follows the form submission algorithm. submit bypasses constraint validation and the submit event, which can lose the intended action and error path."),
    ("How should an old asynchronous field response be handled?", ["Ignore it when value or sequence no longer matches", "Show it because it arrived last", "Use it as proof the later value is reserved"], "Network completion order need not match typing order. Compare the request's value and sequence with the current field before changing feedback."),
    ("What does a local autosave copy prove?", ["Only that this browser retained a recoverable draft", "That the server accepted the write", "That another device has the same text"], "A local draft is useful after interruption but has a different durability and visibility boundary from a confirmed server version. Label those states separately."),
    ("What should happen when a recovered draft has an older base version than the server?", ["Show a conflict and preserve both values", "Silently overwrite the server", "Discard both versions immediately"], "The draft descends from an older record. A later timestamp on the local browser does not establish authority over a newer confirmed server version."),
    ("Who sets multipart Content-Type when fetch sends FormData?", ["The browser, including its boundary", "The developer with a bare multipart/form-data value", "The filename extension"], "The multipart boundary must match the body encoding. Let the browser set that header, and keep transfer completion separate from server validation and acceptance."),
]

assert quiz_path not in by_path
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: rendering and forms decisions quiz",
            summary="Twelve explained decisions about hydration, data freshness, client caches, mutation recovery, form submission, drafts, and uploads.",
            sort_order=1065, created_at=stamp, updated_at=stamp, published_at=stamp)


def quiz_item(index, item):
    prompt, options, explanation = item
    shift = index % len(options)
    return {"prompt": prompt, "options": options[shift:] + options[:shift],
            "answer": (0 - shift) % len(options), "explanation": explanation}


quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes",
                "content_format": "html", "seo_ready": False,
                "questions": [quiz_item(index, item) for index, item in enumerate(questions)]}
quiz["body"] = paragraph(quiz["summary"] + " Choose one response and inspect the explanation before retrying a missed boundary.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for project in projects for path in project["related"][:4]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path["web-tech/web-technology/project"]
project_hub["data"]["modules"][0]["lessons"].extend(project["path"] for project in projects)
project_hub["body"] += "<h2>Rendering and forms projects</h2><ul>" + "".join(
    f'<li>{link(project["path"])} — {html.escape(project["summary"])}</li>' for project in projects) + "</ul>"
project_hub["summary"] = "Build and verify twenty projects across browser, API, data, identity, search, quality, rendering, forms, accessibility, privacy, offline, live, and release contracts."
project_hub["updated_at"] = stamp

quiz_hub = by_path["web-tech/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Rendering and forms checks</h2><p>" + link(quiz_path) + " — " + html.escape(quiz["summary"]) + "</p>"
quiz_hub["updated_at"] = stamp

for hub_path, project_path in [("web-tech/server-rendering-and-client-data-flow", projects[0]["path"]),
                               ("web-tech/forms-and-data-entry-workflows", projects[1]["path"])]:
    hub = by_path[hub_path]
    hub["body"] += "<h2>Practice path</h2><p>Build " + link(project_path) + " and check decisions in " + link(quiz_path) + ".</p>"
    hub["updated_at"] = stamp

for entry in entries:
    if entry["type"] != "article" or entry["data"].get("section_path") not in {
        "web-tech/server-rendering-and-client-data-flow", "web-tech/forms-and-data-entry-workflows"
    }:
        continue
    project_path = projects[0]["path"] if entry["data"]["section_path"] == "web-tech/server-rendering-and-client-data-flow" else projects[1]["path"]
    entry["body"] += "<h2>Apply and check</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + ".</p>"
    entry["data"]["related"].extend([project_path, quiz_path])
    entry["updated_at"] = stamp

root_entry = by_path["web-tech/web-technology"]
root_entry["body"] += "<h2>Rendering and form practice</h2><p>Apply the data-flow and submission contracts with " + link(projects[0]["path"]) + " and " + link(projects[1]["path"]) + ".</p>"
root_entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": len(projects), "new_quizzes": 1, "new_questions": len(questions)}))
