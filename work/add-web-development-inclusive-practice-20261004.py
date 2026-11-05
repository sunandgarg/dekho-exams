"""Add inclusive-interface and localized-content practice routes."""

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


def link(path):
    assert path in by_path, path
    return f'<a href="/{html.escape(path, quote=True)}">{html.escape(by_path[path]["title"])}</a>'


def para(value):
    return f"<p>{html.escape(value)}</p>"


projects = [
    dict(path="web-tech/inclusive-case-review-project", title="Project: inclusive case review",
         summary="Make queue actions, archive confirmation, form errors, and zoom behavior work as one task.",
         intro="Build the reviewer path for case 47, from a queue link to an archive decision and back. The task must work with the keyboard, at 200 percent zoom, with reduced motion, and after a server rejection. Start with native links and buttons. Name each repeated action so its target is clear. Use a modal confirmation only if the consequence warrants interruption; after success, focus should land on a stable queue target. A rejected archive stays recoverable. Do not count a passing initial screenshot as proof that the whole path works.",
         scope=["Create a queue with at least 47 distinct records, including long titles, and give each navigation and action control a useful name.", "Implement an archive confirmation with a named dialog, safe initial focus, cancellation, server-error handling, and a focus destination after the row disappears.", "Add a case-note form that retains good input and maps validation, conflict, permission, and transport failures to different recovery copy."],
         code='<button type="button" id="archive-case-47" aria-label="Archive case 47">Archive</button>\n<dialog id="archive-dialog" aria-labelledby="archive-title"><h2 id="archive-title">Archive case 47?</h2><button id="cancel-archive">Cancel</button><button id="confirm-archive">Archive case</button></dialog>',
         language="html", cost="Native controls reduce custom keyboard code, but the full journey still has focus and error branches to test. A real screen-reader pass costs time; it is more informative than relying only on an automated name check. Long labels and zoom may increase page height. That is acceptable if focus, reading order, and actions stay visible. The archive request needs server authorization and an idempotent result if the user activates confirmation twice.",
         failure="First, open the dialog from a queue row that will be removed. Confirm the archive, then inspect whether focus vanishes with the row. Next, force the server to reject the archive; the dialog should stay open with an actionable message, and the record should remain. Finally, zoom until the viewport narrows and try the same sequence with a long translated title. The implementation is incomplete if any required control leaves the viewport or the error is expressed only by color.",
         checks=["Complete the journey using only Tab, Shift-Tab, Enter, and Escape.", "Archive one record, then check the focus destination and announced result.", "Inject a server conflict and a network timeout; verify distinct recovery paths.", "Repeat at 200 percent zoom with reduced motion and a long title."],
         mistakes=["Testing a button label but not the result after activation.", "Moving focus back to a row deleted by successful archive.", "Calling a viewport responsive while its confirmation dialog clips."],
         related=["web-tech/accessible-names-and-native-controls", "web-tech/dialog-focus-and-interruption-boundary", "web-tech/form-errors-and-recovery-paths", "web-tech/reflow-zoom-and-motion-preferences", "web-tech/record-level-authorization"]),
    dict(path="web-tech/localized-guide-release-project", title="Project: localized guide release",
         summary="Publish a translated guide with stable route identity, correct values, and mixed-direction checks.",
         intro="Build a two-language guide for uploading inspection photos. Give the English and Hindi pages one stable content identity but separate, shareable routes. The guide must declare its actual page language, link to a related lesson in the same language when available, and preserve an old localized slug after an edit. Give each translation a source revision and editorial readiness state. A translated title attached to an old English body is not a release. The project should show what happens when one locale is missing a critical message or lags behind an upload-rule change.",
         scope=["Store a stable guide ID, per-locale slug, source revision, translation revision, and readiness field; retain redirect aliases for old slugs.", "Render a case timestamp and reimbursement from canonical values through an explicit display locale and time-zone policy.", "Exercise mixed-direction reviewer names and case IDs, and check long translated copy at a narrow zoomed viewport."],
         code='const guide = { id: "photo-intake", sourceRevision: 47, routes: { en: "/en/guides/photo-intake", hi: "/hi/guides/photo-intake" }, ready: { en: 47, hi: 46 } };\nconst hindiIsCurrent = guide.ready.hi === guide.sourceRevision;',
         language="javascript", cost="Per-locale pages add review work, cache entries, and link variants. Revision checks and redirects use little storage compared with the cost of sending a reader to stale instructions. Construct locale formatters once per view rather than once per row. Do not use display strings as API values. Keep the translation release check separate from route existence so a successful response cannot hide obsolete content.",
         failure="Advance the source guide from revision 46 to 47 when the accepted image size changes. The Hindi route still exists but is not ready. The release process must surface that mismatch and apply its explicit fallback or hold policy. Rename the Hindi slug while an old bookmark remains; the old route must redirect to the current page without looping. Then insert a Latin reviewer name into an Arabic test page and copy its case ID into search to check that visual order did not alter the identifier.",
         checks=["Open both locale routes directly and inspect declared language, body, and related links.", "Change a slug and verify the old path redirects to the intended new route.", "Advance the source revision and verify the lagging translation is flagged.", "Change locale while retaining exact amount, currency code, and canonical instant."],
         mistakes=["Assuming a healthy localized URL means the guide is translated and current.", "Using a rendered date or money string as stored data.", "Mirroring a page instead of setting direction and isolating mixed text."],
         related=["web-tech/message-catalog-contracts-and-fallback", "web-tech/currency-date-and-time-zone-presentation", "web-tech/right-to-left-and-mixed-direction-content", "web-tech/localized-route-and-translation-release", "web-tech/internal-link-architecture"]),
]

for number, project in enumerate(projects, start=1):
    assert project["path"] not in by_path
    entry = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project["path"])),
                 path=project["path"], title=project["title"], summary=project["summary"],
                 sort_order=980 + number, created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                     "content_format": "html", "seo_ready": False, "kind": "project",
                     "author_path": "authors/aitrove-editorial", "reading_minutes": 8, "related": project["related"]}
    body = para(project["intro"])
    body += "<h2>Build contract</h2><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in project["scope"]) + "</ul>"
    body += f'<h2>Implementation checkpoint</h2><pre><code class="language-{project["language"]}">' + html.escape(project["code"], quote=False) + "</code></pre>"
    body += "<h2>Cost and boundaries</h2>" + para(project["cost"])
    body += "<h2>Failure drill</h2>" + para(project["failure"])
    body += "<h2>Acceptance checks</h2><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in project["checks"]) + "</ul>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in project["mistakes"]) + "</ul>"
    body += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["related"]) + ".</p>"
    entry["body"] = body
    entries.append(entry)
    by_path[entry["path"]] = entry

quiz_path = "quizzes/web-development-inclusive-global-contracts"
questions = [
    ("Which element fits navigation to a case detail route?", ["A link with a real destination", "A generic container with a click handler", "A button with no route"], 0, "A link communicates navigation, has standard keyboard behavior, and still exposes the destination if client script does not run."),
    ("Forty queue buttons all say 'Open'. What is missing?", ["A longer animation", "Target context in each accessible name", "Another generic role"], 1, "Repeated actions need enough record context that a person can choose the intended case without inferring the target from visual position."),
    ("A modal archive confirmation opens. Where should focus go?", ["To a meaningful control or heading inside it", "To the browser address bar", "To a background row"], 0, "A modal temporarily owns interaction. Initial focus must make its purpose and safe next action clear, then remain within it while open."),
    ("A successful archive removes its trigger row. What follows?", ["Focus the detached trigger", "Drop focus to the document body", "Move focus to a stable queue target"], 2, "The removed node cannot be a useful return destination. Choose a surviving control or heading and announce the result."),
    ("A server denies case access. Should the form mark the date field invalid?", ["Yes, for every failure", "No; permission and field validation are different recovery paths", "Only if the date is long"], 1, "A field error should name something the person can correct. Permission, conflict, and transport failures need distinct messages."),
    ("What should a rejected form preserve?", ["Only its heading", "Its valid entered values and a route to correction", "Nothing; reset it"], 1, "Keeping valid work reduces re-entry and makes a specific correction possible after the server rejects one part of the submission."),
    ("A queue wraps at narrow width, but its dialog clips at zoom. Is the archive task usable?", ["Yes, because the queue wraps", "Only in landscape", "No, the complete task still fails"], 2, "The confirmation and error states belong to the same task. Testing only the initial queue misses required controls outside the viewport."),
    ("Reduced motion is requested. What remains necessary?", ["An understandable state-change cue", "The full decorative slide", "No indication that results changed"], 0, "Remove nonessential movement while preserving text or focus feedback that tells the person the result actually changed."),
    ("How should a translated archive question be assembled?", ["Concatenate translated fragments", "Translate the whole message with a named case-title value", "Use the English key as visible text"], 1, "A whole message allows different word order and inflection. Named variables keep the case title tied to its meaning."),
    ("Does formatting INR for another locale convert the reimbursement?", ["Yes, by changing the symbol", "Only when the browser requests it", "No; formatting and conversion are separate operations"], 2, "Locale formatting changes presentation. The stored exact amount and currency code remain unchanged without an explicit conversion rule."),
    ("Unknown-direction reviewer names appear beside Arabic text. What helps preserve order?", ["A global CSS mirror", "Isolate the inserted name and declare page direction", "Strip punctuation"], 1, "Document direction and isolation give the browser a reliable base for mixed text without changing stored identifiers."),
    ("A localized guide exists but its revision trails the source rule. What should release do?", ["Flag its readiness and apply the explicit fallback or hold policy", "Treat status 200 as proof it is current", "Delete all old route aliases"], 0, "Route reachability cannot prove editorial currency. Revision and readiness checks surface stale instructions before publication."),
]

assert quiz_path not in by_path
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: inclusive and global delivery quiz",
            summary="Twelve explained decisions about accessible tasks, translation contracts, exact values, and localized routes.",
            sort_order=994, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes",
                "content_format": "html", "seo_ready": False,
                "questions": [{"prompt": prompt, "options": options, "answer": answer, "explanation": explanation}
                              for prompt, options, answer, explanation in questions]}
quiz["body"] = para(quiz["summary"] + " Choose a response, read its explanation, and reopen the related lesson when a boundary is unclear.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for project in projects for path in project["related"][:4]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path["web-tech/web-technology/project"]
project_hub["data"]["modules"][0]["lessons"].extend(project["path"] for project in projects)
project_hub["body"] += "<h2>Inclusive and global delivery projects</h2><ul>" + "".join(
    f'<li>{link(project["path"])} — {html.escape(project["summary"])}</li>' for project in projects) + "</ul>"
project_hub["summary"] = "Build and verify eleven projects across browser, API, data, identity, accessibility, localization, offline, live, and release contracts."
project_hub["updated_at"] = stamp

quiz_hub = by_path["web-tech/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Inclusive and global delivery checks</h2><p>" + link(quiz_path) + " — " + html.escape(quiz["summary"]) + "</p>"
quiz_hub["updated_at"] = stamp

for path, project_path in [("web-tech/inclusive-interface-engineering", projects[0]["path"]),
                           ("web-tech/internationalization-and-content-delivery", projects[1]["path"])]:
    hub = by_path[path]
    hub["body"] += "<h2>Practice path</h2><p>Build " + link(project_path) + " and check choices in " + link(quiz_path) + ".</p>"
    hub["updated_at"] = stamp

for entry in entries:
    if entry["type"] != "article" or entry["data"].get("section_path") not in {
        "web-tech/inclusive-interface-engineering", "web-tech/internationalization-and-content-delivery"
    }:
        continue
    project_path = projects[0]["path"] if entry["data"]["section_path"] == "web-tech/inclusive-interface-engineering" else projects[1]["path"]
    entry["body"] += "<h2>Apply and check</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + ".</p>"
    entry["data"]["related"].extend([project_path, quiz_path])
    entry["updated_at"] = stamp

root_entry = by_path["web-tech/web-technology"]
root_entry["body"] += "<h2>Inclusive and global practice</h2><p>Apply the interface and publication contracts with " + link(projects[0]["path"]) + " and " + link(projects[1]["path"]) + ".</p>"
root_entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": len(projects), "new_quizzes": 1, "new_questions": len(questions)}))
