"""Add original UI-to-code prompt lessons, project, and quiz to local fixtures."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
lookup = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
subject_root = "prompt-engineering/prompt-engineering"
applications = "prompt-engineering/applications"
production = "prompt-engineering/production"
projects = "prompt-engineering/projects"
quizzes = "prompt-engineering/quizzes"
project_path = "prompt-engineering/dispatch-queue-ui-implementation-project"
quiz_path = "quizzes/prompt-engineering-ui-to-code"

specs = [
    {
        "slug": "ui-brief-component-and-state-contract",
        "title": "UI prompts: turn a brief into components and states",
        "summary": "Name the data, component boundaries, interactions, and observable states before code generation.",
        "definition": "A UI implementation prompt is an executable work contract. It should describe the user's task, available data, existing components, design constraints, state transitions, and acceptance checks. Separate what the brief establishes from what the implementer must inspect in the repository. State which component owns a filter, where the URL or application state lives, and what happens when data is loading, empty, stale, or unavailable. Ask for a short inventory of unknowns before code changes. A screenshot cannot answer ownership, persistence, or error behavior; those decisions need an explicit brief or a reviewed assumption.",
        "case": "A fictional dispatch team has a queue of 47 shipments, including 6 on hold. The requested screen has a status filter and a count above the list. The prompt makes the count mean currently visible records: 47 for All and 6 for Held. A network failure is an error state, not an empty queue. The filter is a reusable control, but the queue page owns the selected status and fetch result. The implementer checks whether the application already has a filter component and a spacing scale before creating another pair. The brief leaves the action behind a shipment row out of scope.",
        "sample": "Task: implement the Dispatch Queue status filter.\nData: 47 shipments; Held filter returns 6.\nOwnership: queue page owns selected status and fetch result.\nStates: loading, 47 All, 6 Held, true empty result, request error.\nReuse: inspect existing filter control and tokens before adding code.\nAcceptance: visible count follows the selected filter; error never says zero.\nUnknown: ask which filter, if any, belongs in the URL.",
        "cost": "A client-side filter over N loaded rows is O(N) time per selection and O(N) space for a copied visible list; server-side filtering instead spends a request and must reconcile count with the returned page. The prompt does not choose between them without knowing dataset size and pagination. Inventory work adds review time, but prevents duplicate components and contradictory state stores. Keep generated changes scoped to the queue page and shared primitives that really need alteration.",
        "mistakes": ["Do not make a loading or network error appear as a zero-result search.", "Do not invent filter persistence or URL behavior from a still image.", "Do not create a second control before inspecting the existing component library."],
        "related": ["prompt-engineering/code-change-acceptance-contract", "prompt-engineering/clarification-versus-assumption-gate", "prompt-engineering/intent-to-acceptance-check"],
        "section": applications,
    },
    {
        "slug": "screenshot-to-code-evidence-and-semantic-map",
        "title": "Screenshot prompts: separate pixels from behavior",
        "summary": "Treat an image as visual evidence and specify the missing interaction and semantic facts.",
        "definition": "A screenshot-to-code prompt should label what is visible, what is inferred, and what remains unknown. Pixel position, color, and apparent grouping are observations. Element role, reading order, keyboard behavior, hidden states, and data source are not visible proof. Map each visible control to its intended semantic element and action, then require confirmation where the image cannot resolve an ambiguity. Use the screen as a comparison target after the implementation renders; do not treat a close visual match as evidence that controls work. Preserve the product's existing type scale and spacing rules unless a real design requirement calls for a change.",
        "case": "The Dispatch Queue screenshot shows a pill labeled Held, six visible rows, and a small number beside the heading. It does not reveal whether Held is a button, a link, or a tab; whether the six rows are all matching records or only one page; or how keyboard focus is drawn. The prompt records those unknowns. The selected filter becomes a labeled native control in the implementation, with a visible focus indicator and a count tied to the current result. A screenshot comparison checks spacing and alignment. A separate interaction check confirms that selecting All restores 47 rows in the fictional fixture.",
        "sample": "Visible evidence: Held label, six rows, heading count, card spacing.\nUnknown: role, pagination, focus treatment, fetch behavior.\nSemantic contract: named filter control; heading and list in reading order.\nBehavior check: Held -> 6 visible; All -> 47 visible.\nReview: compare rendered image, then test keyboard and state changes.",
        "cost": "Rendering and image comparison cost roughly O(P) work for P pixels per captured state, while interaction checks scale with the number of tested transitions. A single screenshot is cheap but covers one width and one state. Keep a small, risk-based set of captures instead of multiplying every state by every browser and width without a reason. Store the observation and the chosen assumption together so reviewers can distinguish an intentional design decision from a guess.",
        "mistakes": ["Do not infer an element's semantics from its color or shape.", "Do not approve a button because it looks correct while it cannot be reached by keyboard.", "Do not crop away the state or viewport that would reveal overflow."],
        "related": ["prompt-engineering/image-generation-brief-and-review", "prompt-engineering/semantic-structure-output-gate", "html/html-tutorial/accessibility"],
        "section": applications,
    },
    {
        "slug": "responsive-interaction-state-matrix",
        "title": "Responsive UI prompts: test states, not one viewport",
        "summary": "Specify representative widths, content extremes, and interaction states without fixing the layout to a screenshot.",
        "definition": "A responsive UI prompt defines the behavior that must survive width and content changes. Pair a few representative viewport widths with the states most likely to break: a long label, no records, loading, a request error, keyboard focus, and an open menu. Require natural reflow, reachable actions, readable text, and no horizontal clipping at the chosen widths. The widths are test fixtures, not promises that every device has that exact size. A state matrix makes the review finite: test each high-risk combination and explain why lower-risk combinations are covered by the same layout rule.",
        "case": "On the Dispatch Queue page, the 47-row All state fills a desktop list, while a narrow phone width compresses the filter and one long destination label. The Held view has 6 rows. An empty search has a specific message and a clear action; a failed request shows retry rather than the empty message. The matrix checks wide All, narrow Held with long text, narrow empty, and narrow error with keyboard focus on Retry. It also checks that the count remains tied to the filtered data. A prompt that says 'make responsive' without these conditions could pass while the filter disappears off-screen.",
        "sample": "Wide + All: 47 visible; count 47; columns readable.\nNarrow + Held: 6 visible; long destination wraps; filter reachable.\nNarrow + empty: zero matches message; clear filter action.\nNarrow + request error: retry control; no false zero count.\nKeyboard: filter and retry have visible focus in reading order.",
        "cost": "A full Cartesian test of V viewports and S states has O(VS) cases. Select a small set that covers distinct layout rules and failure transitions, then add cases when a regression exposes a new boundary. Browser automation and screenshots cost more than a static prompt, so run cheap state assertions before costly pixel comparisons. The content and interaction contract should remain valid if the design's exact breakpoint changes.",
        "mistakes": ["Do not lock every dimension to the source screenshot's pixels.", "Do not treat an error as an empty result to simplify the state table.", "Do not omit long content or keyboard focus from the narrow-width check."],
        "related": ["css/responsive-layout", "prompt-engineering/accessible-output-evaluation-slices", "prompt-engineering/regression-test-oracle-contract"],
        "section": applications,
    },
    {
        "slug": "design-token-and-component-reuse-gate",
        "title": "UI code prompts: reuse tokens and components with a change gate",
        "summary": "Inspect existing design rules, limit shared changes, and require a reviewable diff.",
        "definition": "A component-reuse gate asks the implementer to search existing controls and design tokens before introducing new markup or CSS. Reuse is a decision, not an absolute rule: extend a shared component when its public contract can support the new behavior without harming other screens; otherwise keep the change local and explain why. State typography, spacing, color, and focus requirements as named design rules rather than arbitrary values copied from an image. Require the final change list to identify any shared component, its consumers, and regression checks. This prevents a page-specific prompt from silently changing a site's common navigation or controls.",
        "case": "The Dispatch Queue already has a Select control and spacing tokens. The requested status filter can use that Select with one new option list, so the prompt forbids a duplicate pill control made only to match the screenshot. The existing focus style is retained. If the Select cannot represent the required label or state, the implementer records that mismatch and proposes a narrow extension with checks on the two screens that already consume it. The queue's row layout stays local. The prompt asks for a diff summary that names affected files and visible behavior, not a claim that all UI is improved.",
        "sample": "Inspect: existing Select, list row, type scale, spacing and focus tokens.\nDecision: reuse Select if its role and state contract fit.\nShared change: list every current consumer and regression check.\nLocal change: keep queue row layout inside the queue feature.\nReview packet: changed files, before/after behavior, unresolved assumptions.",
        "cost": "Repository search and consumer review add O(F) inspection over relevant files, but can avoid maintaining two controls with separate bug paths. A shared component edit expands the regression surface to its C consumers, so the release check is O(C) screens or representative contract tests. Copying CSS may seem faster for one page but creates future update work when tokens change. Do not optimize for fewer files if that means hiding a behavioral change in a global style.",
        "mistakes": ["Do not duplicate a control solely to copy a screenshot's shape.", "Do not change global tokens to fix one page without checking other consumers.", "Do not report a shared change as page-local in the review packet."],
        "related": ["prompt-engineering/code-change-acceptance-contract", "prompt-engineering/output-sink-validation", "css/form-control-states"],
        "section": applications,
    },
    {
        "slug": "ui-visual-and-accessibility-release-gate",
        "title": "UI release prompts: compare appearance and verify access",
        "summary": "Gate release on rendered states, keyboard operation, semantics, and truthful error feedback.",
        "definition": "A UI release prompt should demand evidence from the rendered implementation, not a confident description of its appearance. Capture agreed states at representative widths, compare them with the approved visual intent, and inspect differences that matter to the task. Then run separate behavior and accessibility checks: keyboard reachability, visible focus, control names, reading order, and status feedback. A screenshot can detect a clipped label but cannot prove a filter works or a screen reader receives an update. Record which states were tested, what failed, what was fixed, and which limits remain. The person responsible for release decides whether the evidence is sufficient.",
        "case": "The Dispatch Queue release packet includes wide All at 47, narrow Held at 6, a true empty search, and a request error. Visual review finds a clipped destination in narrow Held and the implementer fixes wrapping. Keyboard review then finds that the custom Retry control has no visible focus; the implementer changes it to a named button using the existing focus style. A scripted state check confirms the error cannot display '0 shipments' as though the server returned a valid empty list. The reviewer records both fixes and approves only after the rendered states are recaptured.",
        "sample": "Evidence: wide All 47; narrow Held 6; empty; error.\nVisual: no clipped label or hidden action.\nBehavior: filter changes count; Retry requests data again.\nAccess: named controls, reading order, keyboard focus visible.\nRelease: attach failures, fixes, recaptures, and unresolved limits.",
        "cost": "For R rendered states and P pixels per capture, visual review is about O(RP) pixel work plus human inspection. Interaction and access checks add actions per state; they should target observable risk, not try to prove every possible combination. Keep screenshot baselines in a stable rendering environment, because platform font and browser differences can create noise unrelated to a code regression. Automated checks reduce routine misses but do not replace manual keyboard and reading-order review.",
        "mistakes": ["Do not treat matching pixels as proof of correct keyboard behavior.", "Do not treat a successful click as proof that a control has a usable name or focus state.", "Do not publish a release packet that omits known failures or untested states."],
        "related": ["prompt-engineering/accessible-output-evaluation-slices", "prompt-engineering/regression-test-oracle-contract", "prompt-engineering/prompt-release-review-packet"],
        "section": production,
    },
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]).intersection(lookup)
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: implement and review a dispatch queue UI"
titles[quiz_path] = "UI-to-code prompt decisions"


def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(selected):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(selected)) + "</ul>"


def related(selected):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(selected)]


def article(path, title, summary, body, section, order, connections, kind="tutorial"):
    entry = copy.deepcopy(lookup["prompt-engineering/evaluation-slice-design"])
    subject = "prompt-engineering-applications" if section == applications else "prompt-engineering-production" if section == production else "prompt-engineering-project"
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                 title=title, summary=summary, body=body, subject=subject,
                 difficulty="Advanced", tags=["prompt engineering", "ui engineering"],
                 sort_order=29700 + order, status="published", published_at=stamp,
                 created_at=stamp, updated_at=stamp)
    entry["data"].update(kind=kind, reading_minutes=11 if kind == "tutorial" else 19,
                         author_path="authors/aitrove-editorial", subject_root=subject_root,
                         section_path=section, content_format="html", seo_ready=True,
                         related=related(connections))
    return entry


new_rows = []
for index, (path, spec) in enumerate(zip(paths, specs)):
    connections = [spec["section"], subject_root] + spec["related"] + [peer for peer in paths if peer != path] + [project_path, quiz_path]
    body = ("<p>" + html.escape(spec["definition"]) + "</p>"
            + "<h2>Operational case</h2><p>" + html.escape(spec["case"]) + "</p>"
            + '<pre><code class="language-text">' + html.escape(spec["sample"], quote=False) + "</code></pre>"
            + "<h2>Performance and operating cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
            + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(mistake) + "</li>" for mistake in spec["mistakes"]) + "</ul>"
            + "<h2>Connected lessons</h2>" + links(connections))
    new_rows.append(article(path, spec["title"], spec["summary"], body, spec["section"], index * 10, connections))

project_connections = paths + ["prompt-engineering/code-change-acceptance-contract", "prompt-engineering/browser-observation-action-contract", "prompt-engineering/prompt-release-review-packet", quiz_path]
project_body = (
    "<p>Implement a fictional Dispatch Queue from an approved screen brief and one desktop screenshot. The fixture contains 47 shipments, 6 on hold. Build a status filter, visible-result count, and row list. Deliver a component inventory, interaction contract, responsive state matrix, rendered review packet, and test results. Leave shipment actions outside this change. The screenshot supplies visual evidence but no authority about hidden states, URL persistence, or control semantics.</p>"
    "<h2>Plan the implementation boundary</h2><p>Inspect existing Select, list-row, typography, spacing, and focus patterns. The queue page owns filter selection and fetch state. Reuse the Select if it can express the approved behavior. Record whether the filter belongs in the URL as an unresolved product decision until confirmed; keep the initial implementation local if no routing behavior is specified. All shows 47 visible records and Held shows 6. Loading is pending work, empty means a successful query returned no matches, and error means data could not be obtained. Do not turn the error into a misleading count of zero.</p>"
    "<h2>Build the state and access matrix</h2><p>Check a wide All state, a narrow Held state with a long destination, a narrow empty search, and a narrow request error. The filter and Retry controls need names, keyboard access, and a visible focus state. Keep headings and rows in a logical reading order. Compare each rendered state with the approved visual intent, then test filter transitions and error recovery separately. A screenshot does not reveal those interactions. If an existing shared Select must change, identify every consumer and run regression checks there too.</p>"
    '<pre><code class="language-text">Fixture: All 47; Held 6; other status counts are unspecified.\nStates: loading | result | empty | request error.\nAcceptance: count = visible successful result, never a failed fetch.\nWidths: wide All; narrow Held with long text; narrow empty/error.\nAccess: named controls, keyboard path, visible focus, reading order.\nRelease packet: captures, state assertions, affected consumers, fixes.</code></pre>'
    "<h2>Performance and operating cost</h2><p>Filtering N loaded rows costs O(N) per selection; a copied visible list costs O(N) additional space. If production data is paginated, the server owns filtering and the count must describe the returned scope or a verified total. A complete V-by-S screenshot grid costs O(VS) captures, so choose representative states by distinct failure risk. Run cheap state assertions before image comparisons. The reviewer should reject a visually close screen if the error state lies about data, the filter cannot be used by keyboard, or a shared component change lacks consumer checks.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not infer URL state or pagination from a desktop image.</li><li>Do not copy pixels at the expense of semantic controls and natural reflow.</li><li>Do not approve a polished error screen that reports a successful empty result.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Turn a fictional dispatch brief into a reviewed, responsive, accessible UI change.", project_body, projects, 60, project_connections, kind="project"))

questions = [
    ("What should a UI implementation prompt name before code is generated?", "Data, ownership, states, interactions, and acceptance checks", "Only colors and spacing", "A final screenshot alone", "The work contract needs behavior as well as appearance."),
    ("A queue request fails. Which state should the page show?", "Request error with recovery, not a zero-result success", "Empty results", "Six held shipments", "Failure and valid empty data have different meanings."),
    ("What can a desktop screenshot establish by itself?", "Visible appearance at that state and width", "Keyboard order", "Whether a filter persists in the URL", "Hidden behavior needs other evidence."),
    ("The Held filter has six rows. What confirms it works?", "An interaction assertion that selects Held and checks six visible rows", "Matching pill color", "A model's description of the screenshot", "A visual match cannot prove state transition."),
    ("What should happen before creating a new status Select?", "Inspect the existing control and its contract", "Copy the screenshot as CSS", "Edit every global token", "Reuse depends on compatibility with existing behavior."),
    ("A shared Select change affects three other pages. What belongs in review?", "Consumer list and regression checks", "Only the queue screenshot", "A claim that the change is local", "Shared edits widen the affected surface."),
    ("What does a responsive prompt need beyond 'make it responsive'?", "Representative widths, content extremes, and risky states", "One fixed screenshot size", "Only a desktop baseline", "Concrete conditions make reflow reviewable."),
    ("Which narrow state is useful for finding clipping?", "Held rows with a long destination label", "An empty page only", "A blank loading spinner", "Long content exposes width assumptions."),
    ("What is the cost of checking every combination of V widths and S states?", "O(VS) cases", "O(V + S) in every case", "No additional work", "The full state matrix multiplies dimensions."),
    ("Does a passing screenshot comparison prove accessibility?", "No; test names, keyboard reachability, focus, and reading order separately", "Yes, pixels include every interaction", "Only if colors match", "Visual evidence and access evidence answer different questions."),
    ("How should the count behave after a successful Held filter?", "Show 6 visible results", "Keep 47 regardless of filter", "Show zero during a failed request", "The count contract is tied to successful visible data."),
    ("What should a UI release packet disclose?", "Tested states, failures, fixes, recaptures, and remaining limits", "Only the final screenshot", "An unverified claim of completion", "Reviewers need traceable evidence for the release decision."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-multimodal-evidence"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                  path=quiz_path, title=titles[quiz_path],
                  summary="Test UI brief boundaries, screenshot evidence, responsive states, reuse, and release checks.",
                  body="<p>Choose the implementation decision supported by the stated evidence.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, production, quizzes]),
                  sort_order=29770, status="published", published_at=stamp,
                  created_at=stamp, updated_at=stamp)
quiz_entry["data"].update(subject_root=subject_root, section_path=quizzes,
                          content_format="html", author_path="authors/aitrove-editorial",
                          seo_ready=True, duration_minutes=12,
                          related=related(paths + [project_path]),
                          questions=[{"prompt": prompt,
                                      "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                      "answer": (-index) % 3, "explanation": explanation}
                                     for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)])
new_rows.append(quiz_entry)

for hub_path, selected, title, summary in [
    (applications, paths[:4], "UI brief to code", "Convert visual evidence into explicit component, state, responsive, and reuse contracts."),
    (production, paths[4:], "UI release evidence", "Compare rendered states and test keyboard, semantics, and truthful feedback."),
    (projects, [project_path], "Dispatch Queue UI review", "Implement and inspect a fictional filtered queue across data and viewport states."),
    (quizzes, [quiz_path], "UI-to-code decisions", "Test visual evidence boundaries, behavior, reuse, and release checks."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

root_hub = lookup[subject_root]
root_hub["body"] += "<h2>UI briefs, implementation, and release checks</h2><p>Define components and states, treat screenshots as partial evidence, and inspect rendered behavior before release.</p>" + links(paths + [project_path, quiz_path])
root_hub["updated_at"] = stamp

backlinks = {
    "prompt-engineering/code-change-acceptance-contract": paths[0],
    "prompt-engineering/image-generation-brief-and-review": paths[1],
    "prompt-engineering/semantic-structure-output-gate": paths[1],
    "prompt-engineering/accessible-output-evaluation-slices": paths[2],
    "prompt-engineering/regression-test-oracle-contract": paths[2],
    "prompt-engineering/output-sink-validation": paths[3],
    "prompt-engineering/prompt-release-review-packet": paths[4],
    "css/responsive-layout": paths[2],
    "html/html-tutorial/accessibility": paths[4],
}
for old_path, new_path in backlinks.items():
    entry = lookup[old_path]
    entry["body"] += "<p><strong>Continue with:</strong> " + link(new_path) + ".</p>"
    entry["data"]["related"] = related([item["path"] for item in entry["data"].get("related", [])] + [new_path])
    entry["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newLessons": len(specs), "newProjects": 1, "newQuizzes": 1,
                  "newPaths": [entry["path"] for entry in new_rows]}))
