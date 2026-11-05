"""Add layout and browser execution practice routes."""

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
    dict(path="web-tech/adaptive-review-interface-project", title="Project: adaptive review interface",
         summary="Build a case workspace that survives intrinsic-size pressure, varied host widths, theme changes, and font fallbacks.",
         intro="Build a review workspace with a queue rail, case detail panel, action row, and reusable case summary. Seed short and very long case titles, a 120-character equipment code, and translated action labels. The outer shell uses Grid to express rail and detail regions; the action row uses Flexbox because its buttons form a single sequence that may wrap. The summary card must also work inside a narrow drawer on a wide screen, so base its internal layout on its containing slot rather than only on viewport width. Put vendor, foundation, component, and utility styles in a declared cascade order. Then test cold font loading and reduced motion while preserving readable text and a persistent save message.",
         scope=["Use explicit shrinkable grid tracks and a wrapping policy; keep every action and full case identifier reachable at narrow width and high zoom.", "Give the summary card a named query container in each host and a useful stacked default when the query does not apply.", "Define owned spacing and surface tokens in declared layers; test focused, error, and disabled states after changing a shared value.", "Compare fallback and loaded font states, then save with reduced motion and verify the confirmation remains present."],
         code='.review-shell { display: grid; grid-template-columns: minmax(14rem, 18rem) minmax(0, 1fr); }\n.review-detail { min-width: 0; }\n.review-detail__id { overflow-wrap: anywhere; }\n.summary-slot { container: case-summary / inline-size; }\n@container case-summary (min-width: 34rem) { .summary-card { display: grid; grid-template-columns: minmax(0, 1fr) auto; } }',
         language="css", cost="The layout rules cost little compared with the ongoing cost of route-specific overrides, but changes to shared tokens can affect many states. Long text wrapping raises card height, so scrolling and focus must still work. A font file adds transfer and may shift line metrics when it replaces the fallback. Keep only needed faces and measure cold and warm behavior. A named container makes the card more reusable, though nested containers need an ownership convention so future wrappers do not change which width controls the rule.",
         failure="First set the detail track to a plain 1fr and seed the long identifier; inspect horizontal overflow and unreachable actions. Put the summary into a narrow drawer while keeping a wide viewport and confirm that a viewport-only breakpoint misses the change. Add an unlayered toolbar rule and inspect why it wins over a layered component rule. Delay the custom font and observe whether the Resolve button moves under the pointer. Finally enable reduced motion; the save confirmation must still communicate success without a slide effect.",
         checks=["At narrow width and high zoom, full identifiers and all actions remain reachable without page-wide horizontal overflow.", "The same summary card adapts in full-page and drawer hosts at one viewport width.", "Changing a compact spacing token does not alter unrelated error feedback or focus appearance.", "Cold font load and reduced motion leave text readable and save status clear."],
         mistakes=["Assuming 1fr always defeats a content minimum.", "Using only viewport queries for a card in different host widths.", "Fixing cascade conflicts with escalating specificity.", "Making motion the sole confirmation of a save."],
         related=["web-tech/grid-flex-and-intrinsic-size-contracts", "web-tech/container-queries-for-reusable-panels", "web-tech/cascade-layers-and-design-token-ownership", "web-tech/font-loading-and-motion-fallbacks", "web-tech/reflow-zoom-and-motion-preferences"]),
    dict(path="web-tech/responsive-import-worker-project", title="Project: responsive import worker",
         summary="Process a case measurement file without blocking input or retaining obsolete browser resources.",
         intro="Build a local measurement-file preview for case 47 and case 62. The page must show that processing has begun before the full parse finishes and must keep a separate control responsive. Use an event-loop trace to explain why a promise callback by itself does not move CPU work away from the main thread. Compare bounded task yields with a dedicated worker. If the worker path transfers an ArrayBuffer, document that the sender loses that buffer. Give every job a generation ID, reject stale results after switching cases, and decide whether to terminate or reuse the worker when the route closes. A photo preview may create an object URL and observer; both need one owner and cleanup path.",
         scope=["Measure first visible progress, total completion, and response to a second control for synchronous, chunked, and worker paths.", "Send job IDs with worker messages; reject obsolete results and handle malformed files with a bounded error state.", "Transfer bytes only when ownership can move, or pay for a deliberate copy; release worker, observer, listener, and object URL resources on route exit.", "Run repeated open, replace, and close cycles to inspect callback count and retained memory."],
         code='function ownsWorkerResult(result, activeCaseId, activeJobId) {\n  return result.caseId === activeCaseId && result.jobId === activeJobId;\n}\nconsole.log(ownsWorkerResult({ caseId: 47, jobId: 62 }, 62, 62));\n// Output: false',
         language="javascript", cost="A worker adds startup, module-loading, messaging, and memory overhead, while a transferred buffer avoids one large copy by detaching it from the sender. Chunked main-thread work avoids worker setup but lengthens total completion through task yields. Compare the measured tradeoff with realistic file sizes rather than choosing by fashion. Cleanup code adds branches, but unreleased observers, URLs, and workers can accumulate through a long review session. The project should record both interaction delay and total processing time.",
         failure="Resolve the case 62 job before the case 47 job, then let 47 finish after route change. The panel must stay on 62. Try reading the transferred buffer from the sender; this should expose the ownership mistake during development rather than in a later feature. Parse a malformed file and verify no success message appears. Open and close a preview thirty times and count resize callbacks; one active panel should not have thirty active observers. Leave the route mid-import and confirm pending work cannot alter another page.",
         checks=["A processing status paints before a long import completes and a second control remains usable.", "Case switches reject stale worker success and error messages.", "Transfer versus copy behavior is documented and tested with the actual byte buffer.", "Thirty preview cycles do not multiply callbacks or retain old object URLs."],
         mistakes=["Assuming Promise.then runs CPU work on a separate thread.", "Posting a cancel message to an uninterrupted synchronous worker loop and expecting instant cancellation.", "Reusing bytes after transfer.", "Treating DOM removal as cleanup for observers and object URLs."],
         related=["web-tech/event-loop-tasks-microtasks-and-paint", "web-tech/workers-messages-transfer-and-cancellation", "web-tech/cooperative-main-thread-scheduling", "web-tech/browser-memory-and-resource-lifecycles", "web-tech/react-effects-and-request-races"]),
]

for number, project in enumerate(projects, start=1):
    assert project["path"] not in by_path
    entry = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project["path"])),
                 path=project["path"], title=project["title"], summary=project["summary"],
                 sort_order=1030 + number, created_at=stamp, updated_at=stamp, published_at=stamp)
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

quiz_path = "quizzes/web-development-layout-runtime-contracts"
questions = [
    ("What makes a grid detail track shrink below its content minimum?", ["Using minmax(0, 1fr) with an appropriate item minimum", "Using only 1fr", "Hiding the whole page overflow"], 0, "A fractional track can still honor an automatic content minimum. An explicit zero minimum and a deliberate text-wrapping policy permit the detail region to shrink."),
    ("Which relationship usually fits Flexbox best?", ["A one-axis action row that may wrap", "A complete two-region page shell with related columns", "The document's source order"], 0, "Flexbox distributes items along one principal axis. A wrapping action row is a clearer fit than forcing a page-level rail and detail relationship into it."),
    ("Why use a container query for a summary card?", ["Its host width varies independently of viewport size", "The browser has no viewport", "It grants record permissions"], 0, "A card may be wide on a phone route and narrow in a desktop drawer. The width of its own containing slot governs the useful layout change."),
    ("Where should the size query container be placed for a card's descendants?", ["On a suitable ancestor slot", "On an unrelated sibling", "Only on the card's text node"], 0, "A size query styles descendants of a declared container. A named ancestor slot gives the card a stable width context across hosts."),
    ("What can make a layered normal component rule lose unexpectedly?", ["An unlayered normal author rule", "A shorter class name", "A CSS custom property by itself"], 0, "Unlayered normal author declarations can take precedence over layered normal declarations, even when a component layer was meant to be the owner."),
    ("Why test a cold font load?", ["Fallback and loaded font metrics may move controls", "Cached fonts are always invalid", "It removes all animation"], 0, "A preferred font can arrive after initial text is visible. Different metrics can change wrapping and control positions during an interaction."),
    ("What should remain when reduced motion removes a transition?", ["Persistent, readable save feedback", "Only the moving effect", "No status or focus path"], 0, "Motion can be reduced without removing the content that communicates the result. A save still needs readable and accessible feedback."),
    ("When do promise microtasks run relative to the next task?", ["After the current stack and before the next task", "Only after the next browser tab opens", "In a separate CPU thread"], 0, "Promise reactions run in the microtask checkpoint after the current stack clears. That does not move heavy work off the main thread."),
    ("Does Promise.then around a parser guarantee a paint first?", ["No; the heavy microtask can still block the next rendering opportunity", "Yes, every promise creates a paint", "Only when the query is empty"], 0, "A promise callback is still main-thread work. A long callback or a chain of microtasks can delay input and visible updates."),
    ("What happens to an ArrayBuffer transferred to a worker?", ["The sender loses ownership of the transferred buffer", "Both sides edit the same ordinary buffer", "The DOM updates automatically"], 0, "Transfer can avoid copying large bytes, but the sender's original buffer is detached and must not be reused as if it still held the file."),
    ("Why check a job ID on worker results?", ["To reject work from an obsolete case route", "To reduce every file to one byte", "To make worker code access the DOM"], 0, "A worker can complete after the page has switched cases. A current-job check prevents an old result from replacing the new route's state."),
    ("What must happen when a preview closes?", ["Disconnect its observer and revoke its object URL when no longer displayed", "Leave every listener alive", "Only remove the image's CSS class"], 0, "DOM removal alone does not guarantee that observers, listeners, object URLs, and workers owned by the preview are released."),
]


def varied_quiz_item(number, question):
    prompt, options, answer, explanation = question
    shift = number % len(options)
    return {"prompt": prompt, "options": options[shift:] + options[:shift],
            "answer": (answer - shift) % len(options), "explanation": explanation}

assert quiz_path not in by_path
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: layout and runtime contracts quiz",
            summary="Twelve explained decisions about CSS constraints, font and motion fallbacks, event ordering, workers, and cleanup.",
            sort_order=1035, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes",
                "content_format": "html", "seo_ready": False,
                "questions": [varied_quiz_item(number, question) for number, question in enumerate(questions)]}
quiz["body"] = para(quiz["summary"] + " Choose one response, inspect its explanation, and revisit the lesson for a missed boundary.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for project in projects for path in project["related"][:4]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path["web-tech/web-technology/project"]
project_hub["data"]["modules"][0]["lessons"].extend(project["path"] for project in projects)
project_hub["body"] += "<h2>Layout and runtime projects</h2><ul>" + "".join(
    f'<li>{link(project["path"])} — {html.escape(project["summary"])}</li>' for project in projects) + "</ul>"
project_hub["summary"] = "Build and verify seventeen projects across browser, API, data, identity, search, quality, layout, runtime, accessibility, localization, privacy, offline, live, and release contracts."
project_hub["updated_at"] = stamp

quiz_hub = by_path["web-tech/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Layout and runtime checks</h2><p>" + link(quiz_path) + " — " + html.escape(quiz["summary"]) + "</p>"
quiz_hub["updated_at"] = stamp

for hub_path, project_path in [("web-tech/css-layout-and-interface-systems", projects[0]["path"]),
                               ("web-tech/browser-execution-and-resource-lifecycle", projects[1]["path"])]:
    hub = by_path[hub_path]
    hub["body"] += "<h2>Practice path</h2><p>Build " + link(project_path) + " and check decisions in " + link(quiz_path) + ".</p>"
    hub["updated_at"] = stamp

for entry in entries:
    if entry["type"] != "article" or entry["data"].get("section_path") not in {
        "web-tech/css-layout-and-interface-systems", "web-tech/browser-execution-and-resource-lifecycle"
    }:
        continue
    project_path = projects[0]["path"] if entry["data"]["section_path"] == "web-tech/css-layout-and-interface-systems" else projects[1]["path"]
    entry["body"] += "<h2>Apply and check</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + ".</p>"
    entry["data"]["related"].extend([project_path, quiz_path])
    entry["updated_at"] = stamp

root_entry = by_path["web-tech/web-technology"]
root_entry["body"] += "<h2>Layout and runtime practice</h2><p>Apply browser layout and execution decisions with " + link(projects[0]["path"]) + " and " + link(projects[1]["path"]) + ".</p>"
root_entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": len(projects), "new_quizzes": 1, "new_questions": len(questions)}))
