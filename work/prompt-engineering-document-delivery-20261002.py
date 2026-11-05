"""Add original document-delivery prompt lessons, project, and quiz."""

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
project_path = "prompt-engineering/north-quay-maintenance-briefing-project"
quiz_path = "quizzes/prompt-engineering-document-delivery"

specs = [
    {
        "slug": "document-brief-audience-and-decision-contract",
        "title": "Document prompts: define the reader's decision before drafting",
        "summary": "Specify audience, decision, scope, evidence packet, and editable deliverable.",
        "definition": "A document-production prompt is a contract for a decision artifact. Define who will read it, what decision the reader must make, which evidence packet is allowed, what is excluded, the required file format, and the review gate. The prompt should identify the claim types it may make: observed counts, interpretations, and proposed actions. A polished narrative cannot repair an unclear denominator or an absent decision owner. Ask for an outline before laying out pages, then require each section to answer a reader question. Preserve editability with actual headings and paragraphs in the requested document format; a page image that looks right is not an editable report.",
        "case": "North Quay's fictional maintenance board needs to decide whether to authorize a follow-up review of overdue inspections. Its frozen packet contains 47 inspection records: 38 current, 6 overdue, and 3 pending validation. The report can state those counts and identify the six overdue records. It cannot call the three pending records completed or overdue without new evidence. The board asks for a short editable report, not a recommendation to replace equipment. The document brief names the operations lead as decision owner and marks equipment replacement outside scope. A reviewer can reject a persuasive page that hides the pending category or silently broadens the requested decision.",
        "sample": "Reader: North Quay maintenance board.\nDecision: authorize a follow-up review of 6 overdue records.\nPacket: 47 inspections = 38 current + 6 overdue + 3 pending.\nDeliverable: editable report with heading hierarchy and decision box.\nExcluded: equipment replacement proposal; status guesses for pending.\nGate: reconcile counts and inspect rendered pages before release.",
        "cost": "Outlining costs one additional drafting pass, but reduces layout rework caused by late changes to purpose. For N records, count reconciliation is O(N) and should happen before the model writes conclusions. A short report still needs page-by-page inspection because one wrapped heading or clipped note can change the meaning of a decision box. Keep the prompt brief proportional to the decision; copying every raw record into the model can increase cost and exposure without improving the board's view.",
        "mistakes": ["Do not let the document's tone imply a decision beyond the authorized question.", "Do not collapse pending validation into current or overdue.", "Do not substitute a flattened page image for an editable report."],
        "related": ["prompt-engineering/task-contract", "prompt-engineering/intent-to-acceptance-check", "prompt-engineering/evidence-bound-report-summary"],
        "section": applications,
    },
    {
        "slug": "report-claim-ledger-and-number-reconciliation",
        "title": "Report prompts: reconcile every claim with the packet",
        "summary": "Keep an internal claim ledger with evidence IDs, arithmetic, and unresolved records.",
        "definition": "A report claim ledger maps each material statement to a permitted evidence item or calculation. It is an internal verification record, not a demand to expose private source material in the published report. The prompt should distinguish a raw observation, an arithmetic result, and a judgment. Require exact units, denominator, and status definitions for every count or rate. If records disagree, retain the conflict and name the owner who can resolve it; do not select the more convenient value. Reconcile totals deterministically before drafting and recheck every number after editing, because a late wording change can turn a correct count into a misleading claim.",
        "case": "The North Quay packet has 47 records. A worksheet says 38 current, 6 overdue, and 3 pending validation; the sum is 47. A draft sentence says 'nine inspections need immediate action' by adding overdue and pending. That arithmetic is valid as a combined count but its label is not: pending validation is not the same as overdue. The ledger rejects the sentence. It accepts 'six overdue inspections require follow-up; three statuses await validation.' A chart showing 6 of 47 overdue must keep 47 as its denominator and label pending separately. If a second sheet reports seven overdue, the discrepancy remains open until a record-level reconciliation identifies the difference.",
        "sample": "Claim C1: 47 records in frozen packet; verify record IDs are distinct.\nClaim C2: 38 current + 6 overdue + 3 pending = 47.\nClaim C3: overdue share = 6/47, approximately 12.8%.\nBlocked: '9 require immediate action' conflates two statuses.\nConflict: second sheet says 7 overdue -> hold claim for record review.",
        "cost": "A single pass over N records builds counts in O(N) time and O(K) space for K status buckets; a record-ID check may require O(N) additional space. A claim ledger adds one review decision per material statement, but makes corrections cheaper than rereading the full report after every revision. Arithmetic should be performed by a deterministic calculation or spreadsheet cell, not trusted to an unverified prose generation. Reconcile the final exported file too; correct draft text does not prove the output artifact retained the correct numbers.",
        "mistakes": ["Do not turn a valid sum into an unsupported operational category.", "Do not calculate a rate without naming its denominator.", "Do not conceal a conflicting count by selecting the first sheet."],
        "related": ["prompt-engineering/aggregate-denominator-reconciliation", "prompt-engineering/evidence-id-traceability", "prompt-engineering/deterministic-calculation-gates"],
        "section": applications,
    },
    {
        "slug": "editable-report-structure-and-render-review",
        "title": "Editable report prompts: inspect structure and rendered pages",
        "summary": "Use real heading styles, preserve text editability, and catch page-level defects.",
        "definition": "An editable-report prompt should specify both logical document structure and rendered appearance. Use actual title and heading styles, meaningful text rather than images of paragraphs, descriptive labels for figures, and a reading order that matches the intended flow. Define page constraints such as margins, repeated headers, and where a decision summary may split. After generation, render every page and inspect it at reading size for clipping, orphaned headings, footnotes that drift from their claim, and charts too small to read. Text extraction checks whether expected words exist; rendered inspection checks whether people can use the page. Neither check alone is sufficient.",
        "case": "North Quay's report contains a decision summary, count reconciliation, an overdue-record list, and a pending-validation note. A generated page places the pending note in a narrow callout; its last line is clipped in the PDF preview. Text extraction still finds the words, so a text-only check would pass. The layout is repaired, then all pages are rerendered. The heading hierarchy is checked in the editable file rather than inferred from bold text. The figure describing the 38/6/3 split gets a purpose-based text alternative that states the values without duplicating an adjacent paragraph word for word.",
        "sample": "Structure: title -> decision summary -> counts -> overdue records -> limits.\nEditable file: heading styles, selectable paragraphs, labeled figure.\nRender gate: inspect every page at reading size.\nText gate: expected counts and pending note remain extractable.\nFailure: clipped callout -> repair layout -> rerender all pages.",
        "cost": "Rendering P pages and checking their text is at least O(P) page operations; image inspection also scales with pixel area. A change to a shared header or style can affect every page, so rerender the whole document after that edit. Manual review focuses on high-risk page boundaries, figures, and footnotes rather than reading every line twice. A smaller font may hide overflow but can make the report unreadable; fix the underlying layout or shorten the content with the decision owner instead.",
        "mistakes": ["Do not equate bold text with a real heading hierarchy.", "Do not approve a file from text extraction while its rendered note is clipped.", "Do not shrink type to conceal overflow without checking readability."],
        "related": ["prompt-engineering/semantic-structure-output-gate", "prompt-engineering/purpose-bound-image-alternatives", "prompt-engineering/output-sink-validation"],
        "section": applications,
    },
    {
        "slug": "slide-deck-claim-and-reading-order-contract",
        "title": "Slide prompts: one claim, supporting evidence, usable order",
        "summary": "Build a presentation from verified claims, with readable visuals and intentional speaker notes.",
        "definition": "A slide-deck prompt should specify the audience, meeting decision, claim per slide, supporting evidence, and what belongs in speaker notes. The deck is a different reading surface from the report: it should not paste paragraphs onto slides or suppress important caveats to create visual space. Each visual needs units and an explanation that survives without color alone. The file should retain editable text and a logical object order for assistive reading. Verify the slide's claim against the report ledger after every edit. Speaker notes may add context, but must not hold the only statement of a material limitation that changes the visible claim.",
        "case": "North Quay requests a six-slide briefing. Slide two states 'Six of 47 inspections are overdue' and shows all three categories: 38 current, 6 overdue, 3 pending. Its first draft used a red segment for overdue without a text label, so the category was unclear without color. The revision adds labels and counts. A later slide asks for authorization to review the six overdue records; it does not recommend replacing equipment. The notes explain that the three pending records await validation, while the visible slide also states this limit. Reading-order inspection finds the chart title after the chart, and the order is corrected before release.",
        "sample": "Slide 1: decision and scope.\nSlide 2: 47 = 38 current + 6 overdue + 3 pending.\nSlide 3: six overdue records and proposed review owner.\nSlide 4: three pending validations; no assumed status.\nSlide 5: review timeline and open questions.\nSlide 6: authorization requested; limitations visible.",
        "cost": "For S slides and C material claims, verification is O(S+C) review steps when the ledger indexes claims by ID. Rendering and inspecting all S slides adds O(S) image operations, with extra time for charts and reading-order checks. Reusing the report's verified numbers reduces contradictory edits, but an automated copy can still move a caveat into notes or lose a category label. A dense deck may save slide count while increasing comprehension cost; trim by decision relevance, not by hiding uncertainty.",
        "mistakes": ["Do not paste the report into slides and call it a presentation.", "Do not make a category depend on color alone.", "Do not bury a limitation in speaker notes while the visible claim overstates certainty."],
        "related": ["prompt-engineering/chart-interpretation-axis-and-unit-gate", "prompt-engineering/evidence-bound-report-summary", "prompt-engineering/accessible-output-evaluation-slices"],
        "section": applications,
    },
    {
        "slug": "pdf-export-text-tags-and-release-reconciliation",
        "title": "PDF export prompts: verify the delivered file again",
        "summary": "Check exported text, page appearance, navigation, and claim consistency before delivery.",
        "definition": "A PDF export is a new artifact with its own failure modes. A release prompt should name the source file, export method, expected page count or range, required text, and manual checks. Verify selectable text, document structure or tags where supported, reading order, descriptive alternatives for meaningful figures, and visible layout on every page. Do not assume the source application's accessibility checks automatically carry through conversion. Compare the exported report's counts and decision statement with the approved claim ledger and editable source. If the PDF is flattened or loses structure, repair the export path or clearly withhold that artifact rather than describing it as accessible.",
        "case": "North Quay's editable report passes its own review. The first PDF export preserves 47, 38, 6, and 3 as text, but moves a footnote to the next page and leaves the chart out of the reading order. The PDF is not released. The team adjusts the source layout and export settings, exports again, inspects each page, and checks structure in the actual PDF. The final delivery packet retains the editable report, six-slide deck, PDF, claim ledger, and a short note of tested limitations. A request for equipment replacement approval would require a new brief; no formatting check can authorize it.",
        "sample": "Source: approved editable North Quay report.\nExport checks: text selectable; 47/38/6/3 present; pages inspect clean.\nStructure: heading order, figure alternative, logical reading order.\nCross-file: report, six slides, and PDF use the same claims.\nRelease: owner reviews actual files; failed PDF is withheld.",
        "cost": "With P PDF pages, visual and text checks take O(P) page passes, plus a small set of cross-file claim comparisons. Structural inspection takes longer when a chart or multi-column layout has a complex reading order. Re-export after source edits and rerun checks on the new file; a previous PDF pass does not transfer to changed bytes. Hashing the approved artifact is O(B) for B bytes and gives a stable receipt for which exact file was reviewed, though it does not prove the file is correct.",
        "mistakes": ["Do not infer PDF accessibility from a clean source document alone.", "Do not release a flattened PDF that only appears readable in a screenshot.", "Do not reuse an earlier approval after the exported bytes change."],
        "related": ["prompt-engineering/prompt-release-artifact-bundle", "prompt-engineering/output-sink-validation", "prompt-engineering/prompt-release-review-packet"],
        "section": production,
    },
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]).intersection(lookup)
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: deliver a North Quay maintenance briefing"
titles[quiz_path] = "Document and presentation prompt decisions"


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
                 difficulty="Advanced", tags=["prompt engineering", "document delivery"],
                 sort_order=29800 + order, status="published", published_at=stamp,
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

project_connections = paths + ["prompt-engineering/evidence-bound-report-summary", "prompt-engineering/prompt-release-artifact-bundle", "prompt-engineering/accessible-output-evaluation-slices", quiz_path]
project_body = (
    "<p>Produce a decision packet for the fictional North Quay maintenance board. The frozen input contains 47 distinct inspection records: 38 current, 6 overdue, and 3 pending validation. The board can authorize a follow-up review of the six overdue records; equipment replacement is outside this brief. Deliver an editable report, a six-slide briefing, a PDF export of the report, an internal claim ledger, and a release checklist. The project assesses the prompt contract and verification process, not a real maintenance decision.</p>"
    "<h2>Define the claims before formatting</h2><p>Record C1 as 47 distinct inspections, C2 as the 38/6/3 split, and C3 as six overdue inspections requiring review. If a rate is useful, 6 divided by 47 is approximately 12.8%, with 47 named as the denominator. The three pending records stay unresolved; do not combine them with overdue under an 'immediate action' label. A conflicting spreadsheet count of seven overdue pauses that claim until record IDs are reconciled. The report decision summary must ask for a review, not for replacement funding.</p>"
    "<h2>Create and inspect each artifact</h2><p>Build the report with real heading styles and editable text. Render every page and check the decision box, chart alternative, footnotes, and long record labels. Build six slides with a visible claim per slide, labeled categories, and a logical object order; notes may add context but cannot hide the pending-validation limit. Export the approved report to PDF, then inspect the actual PDF for selectable text, clean pages, structure, and reading order. A clean source file does not waive export checks. Keep the claim ledger and exact reviewed artifact identities with the packet.</p>"
    '<pre><code class="language-text">Frozen input: 47 = 38 current + 6 overdue + 3 pending.\nDecision: authorize review of 6 overdue records only.\nReport: editable headings, decision summary, limitations, page review.\nSlides: six claims with labels, visible caveats, reading-order check.\nPDF: export from approved report, inspect text, pages, and structure.\nRelease: reconcile all three files to C1-C3 and record tested limits.</code></pre>'
    "<h2>Performance and operating cost</h2><p>Record reconciliation is O(N) over N inspection rows. Claim review is O(C) for C material claims when each has a ledger entry. Rendering a P-page report and S-slide deck is O(P+S) artifact passes before inspection time; the PDF adds another O(P) pass. Recheck the exact files after any edit because an earlier screenshot or accessibility pass applies only to the earlier bytes. The expensive failure is a convincing packet whose numbers or decision boundary differ across formats.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not promote pending validation into an overdue status.</li><li>Do not move a material limitation entirely into speaker notes.</li><li>Do not approve a PDF merely because the editable report passed review.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Draft and verify one decision across an editable report, six-slide deck, and PDF export.", project_body, projects, 60, project_connections, kind="project"))

questions = [
    ("What should the North Quay document prompt define first?", "Reader, decision, packet, exclusions, and deliverable", "Only page colors", "The most persuasive conclusion", "The artifact is governed by its decision contract."),
    ("How many inspection records are in the frozen packet?", "47", "44", "50", "The three categories sum to 47."),
    ("What is the valid status split?", "38 current, 6 overdue, 3 pending", "38 overdue, 6 current, 3 pending", "38 current, 9 overdue", "Pending is a separate status."),
    ("Why is 'nine need immediate action' unsupported?", "It conflates overdue with pending validation", "The sum of six and three is wrong", "All records are current", "A valid sum can carry an invalid label."),
    ("What denominator belongs with the overdue share?", "47 inspection records", "Only six overdue records", "Three pending records", "The rate is six of all 47 records."),
    ("Two sheets disagree on the overdue count. What should happen?", "Hold the claim and reconcile record IDs", "Choose the larger count", "Hide both counts", "Conflicts require record-level resolution."),
    ("What makes a report heading structurally useful?", "An actual heading style in logical order", "Bold text only", "A screenshot of the heading", "Visual weight alone does not create document structure."),
    ("Text extraction finds a note, but the rendered page clips it. Is the page ready?", "No; repair and rerender the affected artifact", "Yes; extracted text is sufficient", "Yes if the title fits", "Readers need visible, usable pages."),
    ("Where must a material pending-status limit appear in the deck?", "On the visible slide claim or its direct context", "Only in hidden speaker notes", "Nowhere if the chart is attractive", "Notes cannot repair an overconfident visible claim."),
    ("What should be checked after exporting the approved report to PDF?", "The actual PDF's text, pages, structure, and reading order", "Only the editable source", "Only the filename", "Conversion can change the delivered artifact."),
    ("What should happen if the PDF loses chart reading order?", "Withhold, repair, re-export, and inspect again", "Release because the chart looks fine", "Delete the claim ledger", "Visual appearance cannot prove usable reading order."),
    ("What does an artifact hash establish?", "Which exact bytes were reviewed", "That the report is factually correct", "That the PDF is accessible", "A stable identity is useful, but correctness needs separate checks."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-multimodal-evidence"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                  path=quiz_path, title=titles[quiz_path],
                  summary="Test document briefs, claim ledgers, report layout, slide claims, and PDF release checks.",
                  body="<p>Choose the document-delivery decision supported by the frozen packet and reviewed artifact.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, production, quizzes]),
                  sort_order=29870, status="published", published_at=stamp,
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
    (applications, paths[:4], "Reports and presentations", "Define decisions, reconcile claims, and inspect editable reports and slide decks."),
    (production, paths[4:], "PDF export release", "Verify the delivered file's text, pages, structure, and approved claims."),
    (projects, [project_path], "Maintenance briefing packet", "Review one frozen inspection packet across report, slides, and PDF."),
    (quizzes, [quiz_path], "Document delivery decisions", "Test counts, structure, caveats, and actual export checks."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

root_hub = lookup[subject_root]
root_hub["body"] += "<h2>Reports, slides, and PDF delivery</h2><p>Carry a verified decision and claim ledger through editable files and final exports.</p>" + links(paths + [project_path, quiz_path])
root_hub["updated_at"] = stamp

backlinks = {
    "prompt-engineering/task-contract": paths[0],
    "prompt-engineering/evidence-bound-report-summary": paths[1],
    "prompt-engineering/aggregate-denominator-reconciliation": paths[1],
    "prompt-engineering/semantic-structure-output-gate": paths[2],
    "prompt-engineering/purpose-bound-image-alternatives": paths[2],
    "prompt-engineering/chart-interpretation-axis-and-unit-gate": paths[3],
    "prompt-engineering/prompt-release-artifact-bundle": paths[4],
    "prompt-engineering/output-sink-validation": paths[4],
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
