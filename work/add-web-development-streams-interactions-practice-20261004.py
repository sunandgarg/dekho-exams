"""Add large-data and complex-interaction projects with explained questions."""

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


def para(value):
    return f"<p>{html.escape(value)}</p>"


def link(path):
    assert path in by_path, path
    return f'<a href="/{html.escape(path, quote=True)}">{html.escape(by_path[path]["title"])}</a>'


projects = [
    dict(path="web-tech/streamed-case-activity-and-export-project", title="Project: streamed case activity and export",
         summary="Build a bounded activity reader and large export flow that distinguish partial data from completion.",
         intro="Build a case 47 activity view that begins showing valid events before the full feed arrives. The server sends newline-framed JSON containing 62 records, including a multibyte note. Split byte chunks at arbitrary positions during testing; the client must decode characters continuously, carry an unfinished line, enforce a maximum frame size, and parse only complete records. A slow enrichment step must not create an unbounded promise queue. If the connection fails after event 29, the view shows a partial state and resumes only through a server-supported cursor with event-ID deduplication. Changing to case 62 cancels the old reader and prevents late updates from entering the new route. Add a 740 MB evidence export that runs as a server job, reports Ready separately from Downloaded, and uses a normal file response or bounded download path instead of buffering the whole artifact in JavaScript.",
         scope=["Test every byte split of a short UTF-8 fixture, multiple records per chunk, a missing final delimiter, malformed JSON, and a frame over the configured limit.",
                "Bound both record count and queued bytes under a slow sink; keep completion pending until all accepted work settles.",
                "Use generation, event ID, and a server cursor to separate abort, partial failure, replay, and normal terminal completion.",
                "Authorize and expire export artifacts; reject range resume when artifact identity or validator changes."],
         code='function acceptsReplay(savedEventIds, incomingEvent) {\n  return !savedEventIds.has(incomingEvent.eventId);\n}\nconsole.log(acceptsReplay(new Set(["case-47-29"]), { eventId: "case-47-29" }));\n// Output: false',
         cost="Decoding n bytes and parsing their records is O(n) work. A bounded unfinished frame and queue keep working memory near O(m + q), where m is the maximum frame and q the admitted queue bytes; retaining all rendered records still consumes separate memory. A full browser arrayBuffer of a 740 MB export can duplicate that scale in application memory, while a normal streamed download avoids that application-level copy. Cursor resume saves transfer after failure but requires retained server history and deduplication. Measure first usable event, peak queue bytes, total completion, aborted work, retry transfer, and browser memory rather than relying on one fast happy path.",
         failure="Feed one JSON record in two chunks and ensure it is not parsed until the delimiter arrives. Split a multibyte character; a per-chunk decoder will corrupt it and should fail the test. Make enrichment take ten times longer than network delivery and inspect whether memory stays bounded. End the response after event 29 without a terminal frame; any 'All activity loaded' label is wrong. Replay event 29 and omit event 31, then verify duplicate suppression and gap reporting. Switch routes before the old stream errors. Finally restart an export download from a new artifact revision with an old byte range; the client must reject the mixed file.",
         checks=["Arbitrary byte splits produce the same ordered records without text corruption.", "Slow processing remains within a measured byte budget and cannot report early completion.", "Partial, cancelled, failed, and complete states remain distinct through route changes and retries.", "Large export download avoids a full JavaScript buffer and rejects changed-artifact resume."],
         mistakes=["Calling JSON.parse on each network chunk.", "Launching one unawaited task for every record.", "Treating a transport close as proof of a complete feed.", "Resuming a large file using only its filename."],
         related=["web-tech/incremental-response-framing-and-utf8", "web-tech/stream-backpressure-and-bounded-work", "web-tech/stream-cancellation-and-partial-result-contract", "web-tech/large-export-download-and-integrity", "web-tech/fetch-status-and-abort"]),
    dict(path="web-tech/accessible-operations-workspace-project", title="Project: accessible operations workspace",
         summary="Build a readable queue, stable assignment suggestions, non-drag reordering, and restrained async feedback.",
         intro="Build a case operations workspace with a 62-row queue, an assignee search field, priority reordering, and background status updates. The read-only queue starts as a native table with labeled headers and one clear case action per row. If the team adds cell editing, define a separate grid interaction mode, including arrow movement, entry into an editor, Escape behavior, and an exit path. The assignee combobox keeps DOM focus on its input, references a mounted active option, and ignores stale search responses. Reordering works with pointer drag, keyboard controls, and a single-pointer path that does not require dragging; each sends the same stable-ID mutation with a version check. A successful save announces one concise status without stealing focus. A blocking conflict offers a focused error summary and a route back to the affected control.",
         scope=["Compare a native read-only table with an interactive grid prototype; count Tab stops and test header context, edit mode, sorting, and virtualization.",
                "Exercise combobox Down Arrow, Up Arrow, Enter, Escape, Tab, text editing, result shrinkage, pointer selection, and out-of-order responses.",
                "Move case 47 with keyboard and taps without dragging; preserve focus, announce its new position, and reject a concurrent stale order.",
                "Stream 62 progress updates while a note field has focus; keep announcements bounded and distinguish routine success from a blocking conflict."],
         code='function movedCasePosition(order, caseId) {\n  const position = order.indexOf(caseId);\n  return position < 0 ? null : { position: position + 1, total: order.length };\n}\nconsole.log(JSON.stringify(movedCasePosition([62, 47, 93], 47)));\n// Output: {"position":2,"total":3}',
         cost="A read-only table with n rows and c columns mounts O(n × c) cells; virtualization lowers mounted DOM work but can remove the focused row and hide total context unless carefully implemented. Filtering n local combobox options is O(n) per query, while server search adds network races. Reordering a copied n-item ID list is O(n) time and memory; a rank-based server model may be cheaper at large scale but needs conflict handling. Short status messages cost little compute, yet unbounded live-region announcements impose high human cost. Measure keyboard task steps and focus stability with actual users and assistive technology alongside render performance.",
         failure="Replace the table role with grid and observe that arrow keys still scroll the page. Either implement the grid keyboard contract or remove the role. Return an old assignee result after a newer query and inspect whether aria-activedescendant points to a removed option. Filter the priority list during a drag and see whether a DOM index moves the wrong case; switch to stable IDs and a version. Then make every streamed progress row live and listen for repeated announcements while typing. A routine success toast must not move the caret from the note field, while a failed submission needs a discoverable error route.",
         checks=["Read-only rows expose useful header context without hundreds of Tab stops.", "Combobox focus, active option, and current query remain in agreement under delayed results.", "Every reorder action works by keyboard and a non-drag pointer method with correct IDs.", "Background success preserves focus, and conflicts provide a clear recovery path."],
         mistakes=["Adding grid semantics without its keyboard model.", "Leaving an active-descendant reference after its option unmounts.", "Offering keyboard reordering as the only alternative to pointer dragging.", "Making an entire changing panel a live region."],
         related=["web-tech/data-table-versus-interactive-grid", "web-tech/combobox-suggestions-and-active-option", "web-tech/reorder-controls-without-dragging", "web-tech/async-status-announcements-and-focus", "web-tech/accessible-names-and-native-controls"]),
]

for number, project in enumerate(projects, start=1):
    assert project["path"] not in by_path
    subprocess.run(["node", "--check", "--input-type=module"], input=project["code"],
                   text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project["path"])),
                 path=project["path"], title=project["title"], summary=project["summary"],
                 sort_order=1120 + number, created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                     "content_format": "html", "seo_ready": False, "kind": "project",
                     "author_path": "authors/aitrove-editorial", "reading_minutes": 8, "related": project["related"]}
    body = para(project["intro"])
    body += "<h2>Build contract</h2><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in project["scope"]) + "</ul>"
    body += '<h2>Implementation checkpoint</h2><pre><code class="language-javascript">' + html.escape(project["code"], quote=False) + "</code></pre>"
    body += "<h2>Cost and boundaries</h2>" + para(project["cost"])
    body += "<h2>Failure drill</h2>" + para(project["failure"])
    body += "<h2>Acceptance checks</h2><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in project["checks"]) + "</ul>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in project["mistakes"]) + "</ul>"
    body += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["related"]) + ".</p>"
    entry["body"] = body
    entries.append(entry)
    by_path[entry["path"]] = entry

quiz_path = "quizzes/web-development-streams-interactions-decisions"
questions = [
    ("Can one network chunk be assumed to contain one complete JSON record?", ["No; a record may span chunks or share one chunk with others", "Yes, when the server uses a newline", "Yes, when fetch resolves"], "Transport chunk boundaries are independent of application records. Decode bytes continuously and frame complete lines before attempting to parse each JSON value."),
    ("What protects a multibyte character split between byte chunks?", ["A streaming text decoder", "Parsing each chunk with JSON.parse", "Treating every byte as a full character"], "A UTF-8 character may use several bytes. A stateful decoder carries an incomplete sequence across chunks before the application frames text records."),
    ("What happens if the reader launches unawaited work for every record?", ["Memory and pending tasks can grow without a useful bound", "The stream gains automatic end-to-end backpressure", "The browser guarantees ordered completion"], "Backpressure depends on consumer readiness. Unawaited work breaks that chain and can leave thousands of retained payloads and detached errors."),
    ("What should a feed show when the connection closes before its terminal frame?", ["A partial or failed state with the last confirmed position", "Complete success because some rows appeared", "No distinction from a user cancellation"], "Earlier rows may be useful, but they do not prove the full feed arrived. Preserve confirmed progress and make retry or reread behavior explicit."),
    ("How should a resumed feed handle a repeated event ID?", ["Deduplicate it and continue checking order", "Count it as a second action", "Discard every event after it"], "Replay windows often repeat the last item. Stable event IDs and sequence checks prevent duplicate display and reveal missing records."),
    ("Why avoid arrayBuffer() for a very large download?", ["It may hold the whole artifact in application memory", "It always verifies file integrity", "It makes the server job unnecessary"], "A normal file response or bounded destination avoids an application-level copy of a huge artifact. Job readiness and transfer completion are separate states."),
    ("When does a read-only case list need an interactive grid?", ["Only when cell-level selection or editing warrants its keyboard contract", "Whenever it has more than one column", "Whenever it contains a case link"], "A native table already expresses reading relationships. Grid semantics add focus and arrow-key behavior that authors must implement for genuine cell-level interaction."),
    ("Where can focus remain in an editable combobox with active-descendant behavior?", ["On the input while the active option is referenced", "On a removed option after filtering", "On the document body after every arrow key"], "The input can retain DOM focus while an active option is exposed through a stable mounted ID. Popup visibility and active state must change together."),
    ("What must happen when suggestions shrink below the active index?", ["Move to a valid mounted option or clear active state", "Keep referring to the removed option", "Commit the oldest stale suggestion"], "An active-descendant reference to an unmounted option has no usable target. Reconcile the index and ID whenever results change."),
    ("What alternatives should accompany drag-based reordering?", ["Keyboard and non-drag single-pointer controls", "Only a hidden keyboard shortcut", "Only a longer drag handle"], "A keyboard route does not by itself help someone who uses a pointer but cannot drag. Buttons or select-then-target controls can invoke the same ID-based move."),
    ("What should an ordinary successful save do to focus?", ["Leave focus in the ongoing task and announce a short result", "Move focus to every success toast", "Rerender the whole live activity panel"], "A routine background result can use a concise status message without interrupting typing. A blocking error has a different focus and recovery need."),
    ("Why avoid making the whole activity panel a live region?", ["Frequent updates can repeat excessive unrelated content", "It prevents all network requests", "It guarantees every result is current"], "A small mounted status region can report meaningful changes. Streaming every row into a live panel can overwhelm speech and distract from the active control."),
]

assert quiz_path not in by_path
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: streams and interaction decisions quiz",
            summary="Twelve explained decisions about streaming, bounded work, downloads, grids, suggestions, reordering, and feedback.",
            sort_order=1125, created_at=stamp, updated_at=stamp, published_at=stamp)


def quiz_item(index, item):
    prompt, options, explanation = item
    shift = index % len(options)
    return {"prompt": prompt, "options": options[shift:] + options[:shift],
            "answer": (0 - shift) % len(options), "explanation": explanation}


quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes",
                "content_format": "html", "seo_ready": False,
                "questions": [quiz_item(index, item) for index, item in enumerate(questions)]}
quiz["body"] = para(quiz["summary"] + " Choose one response, inspect its explanation, and revisit a missed boundary.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for project in projects for path in project["related"][:4]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path["web-tech/web-technology/project"]
project_hub["data"]["modules"][0]["lessons"].extend(project["path"] for project in projects)
project_hub["body"] += "<h2>Streams and interaction projects</h2><ul>" + "".join(
    f'<li>{link(project["path"])} — {html.escape(project["summary"])}</li>' for project in projects) + "</ul>"
project_hub["summary"] = "Build and verify twenty-four projects across browser, API, data, identity, search, quality, rendering, forms, navigation, delivery, streaming, accessibility, privacy, offline, live, and release contracts."
project_hub["updated_at"] = stamp

quiz_hub = by_path["web-tech/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Streams and interaction checks</h2><p>" + link(quiz_path) + " — " + html.escape(quiz["summary"]) + "</p>"
quiz_hub["updated_at"] = stamp

for hub_path, project_path in [("web-tech/streaming-and-large-data-interfaces", projects[0]["path"]),
                               ("web-tech/complex-accessible-interactions", projects[1]["path"])]:
    hub = by_path[hub_path]
    hub["body"] += "<h2>Practice path</h2><p>Build " + link(project_path) + " and check decisions in " + link(quiz_path) + ".</p>"
    hub["updated_at"] = stamp

for entry in entries:
    if entry["type"] != "article" or entry["data"].get("section_path") not in {
        "web-tech/streaming-and-large-data-interfaces", "web-tech/complex-accessible-interactions"
    }:
        continue
    project_path = projects[0]["path"] if entry["data"]["section_path"] == "web-tech/streaming-and-large-data-interfaces" else projects[1]["path"]
    entry["body"] += "<h2>Apply and check</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + ".</p>"
    entry["data"]["related"].extend([project_path, quiz_path])
    entry["updated_at"] = stamp

root_entry = by_path["web-tech/web-technology"]
root_entry["body"] += "<h2>Streams and interaction practice</h2><p>Apply the large-data and complex-control contracts with " + link(projects[0]["path"]) + " and " + link(projects[1]["path"]) + ".</p>"
root_entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": len(projects), "new_quizzes": 1, "new_questions": len(questions)}))
