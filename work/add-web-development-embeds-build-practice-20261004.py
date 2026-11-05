"""Add practice projects and an explained quiz for embeds and build integrity."""

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


def p(value):
    return "<p>" + html.escape(value) + "</p>"


def link(path):
    assert path in by_path, path
    return '<a href="/' + html.escape(path, quote=True) + '">' + html.escape(by_path[path]["title"]) + "</a>"


projects = [
    {
        "path": "web-tech/embedded-attachment-viewer-contract-project",
        "title": "Project: embedded attachment viewer contract",
        "summary": "Build a scoped supplier viewer with a safe frame, checked messages, short-lived channel, and full-page fallback.",
        "intro": "Build a supplier attachment viewer for case 62. The host page owns the case identity, authorization, and selected attachment state. A separate-origin frame receives only a short-lived reference and the capabilities needed to display the attachment: script execution and its own origin. The real origin lets the host target and check exact origins in the ready handshake; an opaque-origin sandbox would not. The frame cannot redirect the host, open arbitrary windows, or access device features. A plain server-rendered preview remains available when the frame does not load or cannot be operated. The handshake checks the exact origin and current frame window before establishing a task-scoped MessageChannel. Every selection message has a protocol version, task ID, request ID, bounded payload, and attachment ID that the host checks against the active case. The server checks object permission before a durable selection. Closing or replacing the viewer closes ports, clears timers, and invalidates outstanding requests. A supplier confirmation popup may return a hint, but only a server status read settles that handoff. The same task has a redirect path when the popup is blocked. Keyboard focus returns to the initiating control after the viewer closes, and the host never treats a frame load event as proof that the viewer is ready.",
        "scope": ["Reject a message from the right origin but the wrong window.", "Reject a replay after case or request ID changes.", "Close every port and timer when the frame reloads or the account changes.", "Complete the task through a preview and redirect when frames or popups fail."],
        "code": "function acceptSelection(activeCase, message) {\n  return message.version === 3 && message.caseId === activeCase.id &&\n    message.requestId === activeCase.pendingRequest &&\n    activeCase.allowedAttachmentIds.has(message.attachmentId);\n}\nconsole.log(acceptSelection({ id: 62, pendingRequest: 'r47', allowedAttachmentIds: new Set([29]) }, { version: 3, caseId: 62, requestId: 'r46', attachmentId: 29 }));\n// Output: false",
        "cost": "A frame adds a document, requests, layout work, script memory, and potentially isolated storage. Bound concurrent viewers and measure a realistic large attachment. A channel adds ports, handlers, pending promises, and progress traffic; close them on every exit path. Schema checks and correlation lookups are O(1) for the bounded protocol, but decoding a large message is proportional to payload size. Limit bytes and nesting before application logic. A server preview costs a second rendering path yet preserves task access during frame failure. Keep logs to rejection categories and counts rather than private attachment payloads.",
        "failure": "Open case 62, start task 29, and then switch to case 47 before the viewer responds. Deliver the old response and prove no selection changes. Send a valid-looking message from another frame, then from the expected frame with the wrong origin; both must fail. Reload the viewer midway through channel transfer and confirm the old port cannot update the host. Block the popup and finish through the redirect. Let the frame return a load event without a ready handshake, then use the preview. Attempt a top-level redirect from the frame. Repeat the workflow by keyboard and screen reader, including focus restoration.",
        "checks": ["Origin, source, version, request, and server permission are separate checks.", "A frame or popup failure preserves the task path.", "Ports, timers, and references are released on case and account changes.", "A return hint cannot mark a supplier confirmation complete."],
        "mistakes": ["Accepting an origin match while ignoring the current source window.", "Keeping a channel alive after its frame navigates.", "Replacing the host's server authorization with a message token."],
        "related": ["web-tech/frame-sandbox-capabilities-and-fallback", "web-tech/postmessage-origin-source-schema-and-replay", "web-tech/messagechannel-lifetime-and-request-correlation", "web-tech/popup-handoff-return-and-window-ownership"],
    },
    {
        "path": "web-tech/frontend-artifact-promotion-project",
        "title": "Project: frontend artifact promotion and rollback",
        "summary": "Release a pinned dashboard build with dependency review, asset integrity, regional manifest checks, and rollback.",
        "intro": "Build a release path for the case dashboard used by reviewers 47 and 62. A source change updates the package manifest and lockfile together. Continuous integration uses a pinned package manager and a clean install; it fails on a mismatch instead of repairing the graph. A dependency admission record explains new packages, install scripts, publisher changes, browser bytes, and a maintenance owner. The build runs with narrow credentials and emits one immutable artifact set. Its manifest records final asset paths, sizes, digests, and toolchain identity. External browser assets use matching integrity metadata and a visible text fallback if they fail; import-map paths are tied to the same release. The deployment uploads all hashed assets to both regions before switching the HTML pointer. Release 47 assets remain available while release 48 rolls out, because an open release-47 tab may lazy-load a report chunk later. Rollback restores a compatible HTML and API contract without deleting release-48 assets needed by open tabs. A release record links the source revision, resolved graph, manifest digest, and promotion event.",
        "scope": ["Fail release installation when the manifest and lockfile disagree.", "Surface new lifecycle scripts and dependency changes in review.", "Block promotion when a manifest asset is missing in either region.", "Keep both old and new tabs functional across rollout and rollback."],
        "code": "function canSwitchDocument(manifest, regionalAssets) {\n  return regionalAssets.every(region => manifest.assets.every(asset => region.has(asset.path)));\n}\nconsole.log(canSwitchDocument({ assets: [{ path: '/assets/case-48.js' }, { path: '/assets/report-48.js' }] }, [new Set(['/assets/case-48.js', '/assets/report-48.js']), new Set(['/assets/case-48.js'])]));\n// Output: false",
        "cost": "Clean installation can add network and filesystem work, but avoids unrecorded local state. Archive caching can reduce repeat downloads without treating an installed directory as release evidence. Dependency review has a fixed human cost; concentrate it on graph changes and install-time code. Retaining multiple hashed releases consumes storage, usually far less than broken open sessions. A manifest verification pass is O(number of assets times number of target regions); sample noncritical assets only when the critical path remains fully checked. Measure failed chunk requests, build duration, parse cost, oldest active client version, and rollback time.",
        "failure": "Alter the declared parser version but leave the lockfile unchanged; the release job must fail before bundling. Add a package with a new postinstall command and verify the review surfaces it before any privileged build step. Change one byte of an external chart script; the browser must block it and keep its text summary. Delete a lazy chunk from the second region before promotion and require the gate to stop. Then roll back while one release-48 tab stays open and another release-47 tab requests a delayed chunk. Both should keep working inside the supported compatibility window. Record any regional or API mismatch with the manifest digest that produced it.",
        "checks": ["The source revision maps to one resolved graph and one artifact manifest.", "Final browser bytes match recorded integrity values.", "The HTML pointer changes only after all critical assets exist.", "Rollback keeps supported open tabs and API calls working."],
        "mistakes": ["Rebuilding independently in each region.", "Accepting a clean vulnerability scan as approval of install scripts.", "Deleting prior hashed assets when a new document goes live."],
        "related": ["web-tech/locked-dependency-resolution-and-clean-installs", "web-tech/dependency-admission-scripts-and-provenance", "web-tech/external-asset-integrity-and-module-resolution", "web-tech/artifact-manifest-rollout-and-rollback-coherence"],
    },
]

for number, project in enumerate(projects, 1):
    assert project["path"] not in by_path
    subprocess.run(["node", "--check", "--input-type=module"], input=project["code"],
                   text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path["web-tech/case-save-incident-evidence-project"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project["path"])),
                 path=project["path"], title=project["title"], summary=project["summary"],
                 sort_order=1260 + number, created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                     "content_format": "html", "seo_ready": False, "kind": "project",
                     "author_path": "authors/aitrove-editorial", "reading_minutes": 8, "related": project["related"]}
    body = p(project["intro"]) + "<h2>Build contract</h2><ul>" + "".join(
        "<li>" + html.escape(item) + "</li>" for item in project["scope"]) + "</ul>"
    body += '<h2>Implementation checkpoint</h2><pre><code class="language-javascript">' + html.escape(project["code"], quote=False) + "</code></pre>"
    body += "<h2>Cost and boundaries</h2>" + p(project["cost"]) + "<h2>Failure drill</h2>" + p(project["failure"])
    body += "<h2>Acceptance checks</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in project["checks"]) + "</ul>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in project["mistakes"]) + "</ul>"
    body += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["related"]) + ".</p>"
    entry["body"] = body
    entries.append(entry)
    by_path[entry["path"]] = entry

questions = [
    ("What does a frame load event establish?", ["The frame document loaded, not that its application succeeded", "The attachment was authorized on the server", "The viewer sent a valid ready handshake"], "A frame can fire load while its intended application fails. Keep a timeout, ready contract, and fallback."),
    ("Which frame permission set is the safest starting point?", ["Only the capabilities the viewer task needs", "Every sandbox token to avoid browser errors", "Script and same-origin powers on a same-origin untrusted frame"], "Browser powers should follow an explicit task inventory. Broad sandbox permissions can erase the isolation the design assumed."),
    ("What must a private postMessage sender specify?", ["The intended recipient's exact origin", "A wildcard target origin", "The target page path as the origin"], "The browser matches scheme, host, and port for the target origin; a path is not part of that origin."),
    ("What must a receiver check after event.origin matches?", ["Expected source, schema, correlation, and application permission", "Only the message type string", "Only whether the payload is JSON"], "An origin check identifies a document origin, not a valid command or permission to change durable case state."),
    ("When should a MessageChannel close?", ["When its viewer task ends, reloads, or loses ownership", "Only when the browser process exits", "After every progress event"], "A port can retain handlers and buffers after the visible frame changes. Teardown belongs to the task lifecycle."),
    ("What does a supplier popup completion message prove?", ["Only that a return hint arrived; server state still needs checking", "The server settled the handoff", "The user owns every attachment in the case"], "The host should match the handoff ID and read its own server status before updating durable state."),
    ("What should a clean release install do with a stale lockfile?", ["Fail before building", "Silently rewrite it", "Ignore it when a local installed tree exists"], "A frozen graph is useful only if the manifest and lock agree; an automatic repair hides the deployed dependency set."),
    ("What does package provenance establish?", ["Evidence about a publishing route, not proof code is harmless", "That no install script can run", "That no vulnerability can exist"], "Signatures and provenance add evidence, while code behavior, authority, and context still need review."),
    ("When should an external asset digest be calculated?", ["From the final bytes served to the browser", "Before minification or CDN transformation", "From the package name alone"], "Integrity compares received bytes to a recorded digest. Any transformation after hashing can cause the browser to block the asset."),
    ("Does a document import map govern worker module resolution?", ["No; worker imports need their own explicit resolution plan", "Yes, in every worker and worklet", "Only when a popup is open"], "Document import maps resolve document module imports; workers and worklets have separate loading paths."),
    ("When may a release switch its HTML pointer?", ["After every required manifest asset is available in target regions", "As soon as the first page paints in staging", "Before uploading lazy chunks"], "A first paint can succeed while later interactions fail on missing chunks. Publish immutable assets before changing the document pointer."),
    ("What should rollback retain?", ["Assets and API compatibility needed by supported open tabs", "Only the restored HTML file", "Only the latest JavaScript bundle"], "Already open tabs can request old or new chunks after the pointer changes; rollback must preserve their supported compatibility window."),
]

quiz_path = "quizzes/web-development-embeds-build-decisions"
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path["quizzes/web-development-graphics-editor-decisions"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: embedded interfaces and build integrity quiz",
            summary="Twelve explained decisions about frame permissions, messages, ports, handoffs, dependency graphs, asset integrity, and rollout.",
            sort_order=1265, created_at=stamp, updated_at=stamp, published_at=stamp)


def quiz_item(number, value):
    prompt, options, explanation = value
    shift = number % 3
    return {"prompt": prompt, "options": options[shift:] + options[:shift],
            "answer": (0 - shift) % 3, "explanation": explanation}


quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes",
                "content_format": "html", "seo_ready": False,
                "questions": [quiz_item(number, value) for number, value in enumerate(questions)]}
quiz["body"] = p(quiz["summary"] + " Choose one answer, inspect its explanation, and return to the related boundary.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for project in projects for path in project["related"]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path["web-tech/web-technology/project"]
project_hub["data"]["modules"][0]["lessons"].extend(project["path"] for project in projects)
project_hub["body"] += "<h2>Embedded and build projects</h2><ul>" + "".join(
    "<li>" + link(project["path"]) + " — " + html.escape(project["summary"]) + "</li>" for project in projects) + "</ul>"
project_hub["summary"] = "Build and verify forty-seven projects across browser, API, data, identity, search, rendering, operations, privacy, feature release, GraphQL, compute, peer sessions, motion, regional recovery, graphics, editing, embedded interfaces, and build integrity."
project_hub["updated_at"] = stamp
quiz_hub = by_path["web-tech/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Embedded and build checks</h2><p>" + link(quiz_path) + " — " + html.escape(quiz["summary"]) + "</p>"
quiz_hub["updated_at"] = stamp

hub_project = {
    "web-tech/embedded-interfaces-and-cross-window-contracts": projects[0]["path"],
    "web-tech/frontend-build-and-artifact-integrity": projects[1]["path"],
}
for hub_path, project_path in hub_project.items():
    hub = by_path[hub_path]
    hub["body"] += "<h2>Practice path</h2><p>Build " + link(project_path) + " and check decisions in " + link(quiz_path) + ".</p>"
    hub["updated_at"] = stamp
for entry in entries:
    if entry["type"] != "article" or entry["data"].get("section_path") not in hub_project:
        continue
    project_path = hub_project[entry["data"]["section_path"]]
    entry["body"] += "<h2>Connected lessons</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + "; follow " + "; ".join(
        link(path) for path in entry["data"]["related"]) + ".</p>"
    entry["data"]["related"].extend([project_path, quiz_path])
    entry["updated_at"] = stamp
root_entry = by_path["web-tech/web-technology"]
root_entry["body"] += "<h2>Embedded and build practice</h2><p>Apply the tracks with " + link(projects[0]["path"]) + " and " + link(projects[1]["path"]) + ".</p>"
root_entry["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": len(projects), "new_quizzes": 1, "new_questions": len(questions)}))
