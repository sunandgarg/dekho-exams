"""Add original spreadsheet prompt contracts, a release project, and a quiz."""

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
project_path = "prompt-engineering/replenishment-workbook-review-project"
quiz_path = "quizzes/prompt-engineering-spreadsheet-workflows"

specs = [
    {
        "slug": "workbook-task-contract-and-cell-provenance",
        "title": "Workbook prompts: name sheets, ranges, types, and provenance",
        "summary": "Turn an ambiguous spreadsheet request into a bounded, auditable workbook task.",
        "definition": "A workbook task contract identifies the file version, named sheet, header row, exact input and output columns, row selection rule, units, blank-cell behavior, and whether the model is reading, proposing, or editing. Capture formula text and displayed values separately. A visible value can be a stale formula result, a manually typed constant, or a rounded display of a more precise number. The prompt should say which fields are authoritative and what evidence must be returned for each claim. A screenshot is useful for layout, but it cannot establish hidden rows, formulas, validation rules, or every sheet in a file. Inspect the workbook structure before asking a model to infer operations from it.",
        "case": "A fictional depot asks for a reorder view from Inventory October, version 7. Its Stock sheet has one header row and SKU records below it; B is on-hand units, C is inbound units, D is reserved units, E is a reorder threshold, and F is a formula output. Another sheet, Archive, contains last quarter's numbers. A vague request to 'fix the low items' lets the assistant read the wrong sheet and treat the formatted F value as source data. The bounded request names Stock rows 2 through 48, defines available units as B plus C minus D, and asks for a proposed change list only. It preserves SKU identifiers and excludes Archive. Each proposed result carries its sheet and row address.",
        "sample": "Workbook: Inventory October v7; sheet: Stock; rows: 2..48.\nInputs: B on-hand, C inbound, D reserved, E threshold; units: whole items.\nOutput F: available = B + C - D; flag only if available < E.\nReturn proposed edits with cell address, old formula, new formula, and reason.\nDo not edit Archive or infer hidden rows from a screenshot.",
        "cost": "Reading N selected rows is O(N), while opening a large workbook can also incur cost from formulas, styles, and linked sheets outside the selected range. Restrict the prompt context to the schema and rows needed for the decision, but retain a stable workbook version and source coordinates so the result can be checked later. Formula evaluation belongs to a spreadsheet calculation engine or independent program. A language model's answer may be well phrased and still use the wrong sheet or a rounded display value. Adding explicit range and unit fields costs a few tokens and prevents expensive full-workbook rework.",
        "mistakes": ["Do not identify a workbook only by its filename when several revisions exist.", "Do not treat the displayed value as proof of a current formula result.", "Do not infer hidden rows, formulas, or sheet names from a screenshot."],
        "related": ["prompt-engineering/dataset-intake-column-contract", "prompt-engineering/aggregate-denominator-reconciliation", "prompt-engineering/prompt-envelope-and-data-boundaries"],
        "section": applications,
    },
    {
        "slug": "formula-prompt-reference-and-type-gate",
        "title": "Formula prompts: test references, types, and fill behavior",
        "summary": "Specify the target cell and copy direction before accepting a generated formula.",
        "definition": "A formula-generation prompt needs a target cell, column meanings, expected data types, intended fill range, calculation rule, and edge cases. Ask for the formula plus a small table of hand-checked inputs and outputs. Relative cell references move when copied; absolute references stay fixed; mixed references lock one axis. This is part of the contract, not a formatting preference. A model can propose a plausible expression, but the spreadsheet engine must parse it in the target product and locale, and a reviewer must confirm that it still points to the intended columns after filling. Keep text-valued SKUs out of arithmetic and reject numbers stored as text until they are normalized under an explicit rule.",
        "case": "In Stock, F2 should compute available units as B2+C2-D2 and fill through F48. A proposed formula for F2 uses E2 instead of D2 because E is labeled 'minimum'; it parses, yet it produces the wrong inventory balance. Another answer inserts a fixed $B$2 reference, so every row reuses the first SKU's on-hand value. The editor checks F2 and F3 with different input values before filling, then asks the workbook engine to calculate the full range. For SKU RM-47, B2=18, C2=7, D2=9 and E2=20, so F2 must be 16 and the reorder flag is true because 16 is below 20.",
        "sample": "Target F2; fill F2:F48; formula =B2+C2-D2.\nRM-47 row 2: 18 + 7 - 9 = 16; threshold 20; reorder yes.\nSecond row check: 31 + 0 - 12 = 19; threshold 18; reorder no.\nReject =B2+C2-E2 and =$B$2+C2-D2.",
        "cost": "For N rows, recalculating a simple row-wise arithmetic formula is O(N) time and O(1) additional working space per row; the workbook application may retain N results. Testing two different rows catches a fixed-reference error that a single-row check cannot expose. Complex formulas and cross-sheet dependencies can have much higher recalculation cost, so benchmark against the real workbook when scale matters. The prompt itself cannot prove syntax compatibility across products, locales, or calculation modes. Keep the formula proposal and the engine-calculated result as separate review artifacts.",
        "mistakes": ["Do not check only the first copied formula.", "Do not confuse a threshold with a reserved quantity because both are numeric columns.", "Do not treat a parsed formula as a correct business rule."],
        "related": ["prompt-engineering/workbook-task-contract-and-cell-provenance", "prompt-engineering/aggregate-denominator-reconciliation", "prompt-engineering/locale-formatting-structured-values"],
        "section": applications,
    },
    {
        "slug": "workbook-edit-diff-and-preservation-gate",
        "title": "Workbook edits: review a cell diff before applying changes",
        "summary": "Constrain mutations to approved cells and preserve unrelated workbook behavior.",
        "definition": "Treat an AI-proposed spreadsheet edit as a patch against a known workbook version. Record each proposed cell address, old value or formula, new value or formula, reason, and expected result. Compare the patch with an allowlist of editable sheets and ranges before applying it. The editing program, not the prompt, enforces that boundary. Preserve protected sheets, data validation, named ranges, styles, hidden rows, and existing formulas unless the task explicitly authorizes their change. A dry run should report changed cells and any workbook-level changes. If the input version no longer matches the patch base, stop and inspect the conflict instead of applying a stale suggestion.",
        "case": "A depot assistant proposes 47 formulas in F2:F48. The diff also shows one change to E19, the threshold for SKU RM-63, and a missing validation rule on column B. Neither is in scope. The reviewer rejects the patch rather than accepting its correct-looking F values. A second patch changes only F2:F48, preserves Stock headers and Archive unchanged, and records the old and new formula for every modified cell. It is applied to a copy of version 7. The output workbook hash and change ledger are saved together for the final recalculation check.",
        "sample": "Allowed: Stock!F2:F48 formula cells.\nDenied: Stock!E19 threshold; Archive!*; validation/style changes.\nPatch item: Stock!F2 old =B2-D2 new =B2+C2-D2.\nPrecondition: source workbook is Inventory October v7.\nApply to copy; compare formula and workbook-structure diffs.",
        "cost": "A cell diff over M stored cells is O(M) time if the editor compares whole sheets; a narrower changed-range list is cheaper but can miss collateral workbook changes. Keep a structural check for the properties the editing library can modify, and compare the untouched sheets or hashes where appropriate. A full byte-for-byte workbook comparison is usually noisy because metadata can change on save, so review meaningful cell and workbook features. The model's patch plan is compact; its safety comes from preconditions, range checks, dry-run inspection, and rollback to the original file.",
        "mistakes": ["Do not let the assistant enforce its own edit permissions with prompt text alone.", "Do not accept a correct output column if unrelated cells or validation changed.", "Do not apply a patch made for an older workbook revision."],
        "related": ["prompt-engineering/formula-prompt-reference-and-type-gate", "prompt-engineering/prompt-release-artifact-bundle", "prompt-engineering/side-effect-receipt-reconciliation"],
        "section": applications,
    },
    {
        "slug": "spreadsheet-export-formula-injection-boundary",
        "title": "Spreadsheet exports: keep untrusted labels as text",
        "summary": "Separate prompt instructions from CSV and workbook cell-interpretation rules.",
        "definition": "When a model prepares spreadsheet data, an untrusted label remains data even if it resembles a formula or an instruction. CSV stores fields, not cell types; a spreadsheet application may interpret a leading formula character as an executable expression when the file is opened. Check each exported field after serialization and again in the target spreadsheet application, especially values starting with equals, plus, minus, at-sign, tabs, or line breaks. Quoting a CSV field addresses separators and quotes but does not by itself force text interpretation in every spreadsheet client. If the export format supports explicit text cell types, use them; otherwise choose and verify a client-specific neutralization policy. Preserve the original untrusted value separately for audit rather than silently rewriting it.",
        "case": "One Stock row has the supplier label '=1+1' as literal text. The assistant treats it as a harmless SKU note and produces a CSV export. A reviewer opens it in a spreadsheet program and sees a computed value instead of the label. The team switches to a workbook export with the supplier label written as a text-typed cell, then reopens that file in the target program to confirm the visible value is the literal label. The inventory formulas remain in approved F cells; the supplier column never becomes a formula channel. A CSV delivery, if required, gets a separately tested escaping policy for that application and a save-and-reopen check.",
        "sample": "Untrusted supplier label: =1+1 (literal text).\nAllowed formula cells: Stock!F2:F48 only.\nPreferred export: explicit text cell type for supplier labels.\nCSV fallback: client-tested neutralization; open, save, reopen, inspect.\nRetain raw source label in the audit record.",
        "cost": "Scanning N exported fields costs O(N) time and O(1) extra space per field in a streaming exporter, excluding the output buffer. A manual open-and-reopen test costs more but checks the client behavior that a string scan cannot prove. A prompt saying 'do not execute formulas' cannot control how a spreadsheet program imports CSV. The correct boundary is at serialization and application import, with raw and exported representations kept distinct. Review also covers embedded delimiters and line breaks so one attacker-controlled value cannot shift content into another cell.",
        "mistakes": ["Do not assume CSV quotes make formula-looking values safe as text.", "Do not treat a prompt instruction as a substitute for typed export or client testing.", "Do not alter raw audit data without recording the exported transformation."],
        "related": ["python/csv-spreadsheet-export-boundary", "python/csv-duplicate-headers", "prompt-engineering/prompt-envelope-and-data-boundaries"],
        "section": applications,
    },
    {
        "slug": "spreadsheet-recalculation-and-release-check",
        "title": "Spreadsheet release checks: recalculate, reconcile, then inspect",
        "summary": "Verify formula results in the target engine and match the reviewed workbook artifact.",
        "definition": "A workbook with correct formula text can still show stale cached values if calculation is manual or the file has not been recalculated by a compatible engine. A release gate reopens the edited file, checks calculation settings, forces or confirms recalculation as needed, and independently verifies selected results and totals. It also checks formula errors, unexpected blanks, protected ranges, changed sheet names, and links to external workbooks. The reviewer should compare the final file hash with the file placed in the download or shared location. If the export is CSV, recheck its field types and formula-looking values in the target application. A model explanation is evidence of intent, not of the released workbook's state.",
        "case": "The depot's new F2 formula is correct, yet the saved workbook still displays 11 from an earlier B2-D2 calculation. The reviewer opens it in the target spreadsheet application, confirms calculation mode, recalculates, and sees 16. A separate row-level calculation verifies RM-58 at 31+0-12=19 and RM-63 at 4+11-2=13. Against thresholds 18 and 15, only RM-47 and RM-63 need reorder review. The team checks F2:F48 for formula errors, confirms E19 remained unchanged, and records the hash of the file users actually receive. If the download hash differs, release stops.",
        "sample": "RM-47: 18 + 7 - 9 = 16 < 20: reorder.\nRM-58: 31 + 0 - 12 = 19 >= 18: no reorder.\nRM-63: 4 + 11 - 2 = 13 < 15: reorder.\nGate: recalculate; inspect F2:F48; compare independent rows.\nGate: approved change list and released file hash match.",
        "cost": "For N simple formula rows, an independent pass is O(N) time and O(1) working space if rows are streamed. Workbook-engine recalculation cost depends on its dependency graph; it can exceed O(N) when formulas reference large or volatile ranges. Sampling only a few rows is fast but cannot prove all 47 rows are sound, so scan the full edited range for error states and independently recompute business-critical aggregates or a chosen set of cases. A full application round trip is slower than checking prompt text, but it catches cached-value and import behavior that the model cannot observe.",
        "mistakes": ["Do not release a workbook based only on formula strings or old displayed values.", "Do not assume every spreadsheet library evaluates formulas when saving.", "Do not review one file and distribute another."],
        "related": ["prompt-engineering/workbook-edit-diff-and-preservation-gate", "prompt-engineering/aggregate-denominator-reconciliation", "prompt-engineering/prompt-release-artifact-bundle"],
        "section": production,
    },
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]).intersection(lookup)
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: review a depot replenishment workbook"
titles[quiz_path] = "Spreadsheet prompt and workbook release decisions"


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
                 difficulty="Advanced", tags=["prompt engineering", "spreadsheets"],
                 sort_order=29300 + order, status="published", published_at=stamp,
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

project_connections = paths + ["prompt-engineering/dataset-intake-column-contract", "prompt-engineering/prompt-release-artifact-bundle", "python/csv-spreadsheet-export-boundary", quiz_path]
project_body = (
    "<p>Prepare a reviewed Stock-sheet patch for fictional depot workbook Inventory October v7. Rows 2 through 48 hold SKU, on-hand, inbound, reserved, and threshold fields. The project output is a copied workbook plus a cell-level change ledger, calculation evidence, and an export check. A prompt proposes formulas and explains the business rule; a workbook tool applies approved changes. Never use the model's arithmetic explanation as the final calculation record.</p>"
    "<h2>Establish the input contract</h2><p>Name the exact workbook version and Stock sheet. Check that rows are SKU records, units are whole items, and B through E have the approved meanings. The only editable cells are F2:F48. Archive and Stock thresholds stay untouched. Ask the assistant for a proposed formula, intended fill range, two hand-check cases, and a cell diff. If it proposes =B2+C2-E2 or a fixed $B$2 reference, reject it before applying the patch.</p>"
    "<h2>Apply and inspect the patch</h2><p>Use =B2+C2-D2 in F2 and fill down with relative references. For RM-47, 18+7-9=16 and threshold 20 means reorder review. For RM-58, 31+0-12=19 against threshold 18 means no reorder. For RM-63, 4+11-2=13 against threshold 15 means reorder review. The preview must list old and new formulas by cell. Reject any change to E19, Archive, styles, or validation. Reopen the edited copy in the target spreadsheet application, recalculate, scan F2:F48 for errors, and independently check the three rows. A supplier label that literally reads =1+1 must stay text in any export. Test the final output in the receiving application, then match its hash to the reviewed file.</p>"
    '<pre><code class="language-text">Source: Inventory October v7; Stock rows 2..48.\nAllowed patch: F2:F48 = B+C-D; all other cells preserved.\nRM-47: 16 &lt; 20 reorder; RM-58: 19 &gt;= 18 no; RM-63: 13 &lt; 15 reorder.\nReject: stale display, changed E19, formula-typed supplier label.\nRelease: recalculated file, cell diff, application check, matching hash.</code></pre>'
    "<h2>Performance and operating cost</h2><p>Proposing a uniform formula for N rows takes O(N) patch entries if every changed cell is listed; independent arithmetic is O(N) for a full simple-row pass. Workbook save and recalculation may cost more when unrelated formulas or links are present. Review a structural diff as well as F2:F48, since a writing library may alter validations or metadata outside the requested range. Keep the original file for rollback and preserve the exact reviewed output hash.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not accept an edit plan without an allowlisted range and base version.</li><li>Do not infer a clean release from correct formula text while displayed values remain stale.</li><li>Do not export formula-looking supplier text without a tested text boundary.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Patch, recalculate, and release a fictional inventory workbook with a checked cell diff.", project_body, projects, 60, project_connections, kind="project"))

questions = [
    ("What identifies the workbook used for a prompt-driven edit?", "A version plus sheet and bounded range", "Only the filename", "Only a screenshot", "Version and coordinates make the task checkable."),
    ("Why record both formula text and displayed value?", "The displayed value may be stale or rounded", "They are always identical", "Formula text proves workbook calculation mode", "A saved display is not proof of current calculation."),
    ("Stock F2 needs available units. Which formula matches the contract?", "=B2+C2-D2", "=B2+C2-E2", "=$B$2+C2-D2 for all rows", "Reserved units are subtracted, and on-hand follows the row."),
    ("Why test F3 after F2 before filling?", "It exposes wrongly fixed references", "It changes the threshold", "It proves every workbook feature is preserved", "Two rows can reveal a copy-reference mistake."),
    ("RM-47 has 18 on hand, 7 inbound, 9 reserved, threshold 20. What is the result?", "16 available; reorder review", "34 available; no reorder", "20 available; no reorder", "18+7-9=16, which is below 20."),
    ("A patch changes F2:F48 and E19. Accept it?", "No; E19 is outside the approved range", "Yes if F values look correct", "Yes if the prompt says it is safe", "The edit boundary is enforced by the applying tool."),
    ("The workbook version changed after the model proposed its patch. What next?", "Stop and compare the new base before applying", "Apply the old patch anyway", "Remove the precondition", "A stale patch may overwrite newer cells."),
    ("Does quoting a CSV field force formula-looking text in every spreadsheet client?", "No; verify text interpretation in the target client", "Yes, always", "Only if the model says so", "CSV quoting handles field structure, not universal cell typing."),
    ("Where does a literal supplier label beginning = belong?", "A text-typed field with tested export behavior", "An approved formula cell", "The prompt's instruction hierarchy", "Untrusted labels remain data."),
    ("Formula text is correct but the displayed result is old. What is required?", "Recalculate in a compatible engine and recheck", "Publish because the text parses", "Rewrite the threshold", "Cached results may not reflect current inputs."),
    ("What independently confirms RM-63 with 4 on hand, 11 inbound, 2 reserved, threshold 15?", "13 available; reorder review", "17 available; no reorder", "15 available; no reorder", "4+11-2=13, below 15."),
    ("Which artifact should be distributed?", "The exact recalculated file whose hash passed review", "Any file with the same title", "The newest unreviewed save", "The reviewed result must match what users receive."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-multimodal-evidence"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                  path=quiz_path, title=titles[quiz_path],
                  summary="Test workbook scope, formula references, edit diffs, safe exports, and recalculation.",
                  body="<p>Choose the decision that keeps a prompt-driven spreadsheet change within its approved workbook contract.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, production, quizzes]),
                  sort_order=29370, status="published", published_at=stamp,
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
    (applications, paths[:4], "Workbook prompts and guarded edits", "Bound ranges, verify references, review cell patches, and protect text exports."),
    (production, paths[4:], "Spreadsheet calculation release gate", "Recalculate the final workbook and compare it with the reviewed artifact."),
    (projects, [project_path], "Depot inventory workbook review", "Apply a bounded formula patch with calculation and export checks."),
    (quizzes, [quiz_path], "Spreadsheet workflow decisions", "Test formulas, edit scope, export safety, and release evidence."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

root_hub = lookup[subject_root]
root_hub["body"] += "<h2>Spreadsheet and workbook operations</h2><p>Bound sheets and cells, test formulas after filling, preserve unrelated workbook features, and release a recalculated file.</p>" + links(paths + [project_path, quiz_path])
root_hub["updated_at"] = stamp

backlinks = {
    "prompt-engineering/dataset-intake-column-contract": paths[0],
    "prompt-engineering/aggregate-denominator-reconciliation": paths[1],
    "prompt-engineering/chart-interpretation-axis-and-unit-gate": paths[4],
    "prompt-engineering/prompt-release-artifact-bundle": paths[4],
    "prompt-engineering/prompt-envelope-and-data-boundaries": paths[3],
    "python/csv-spreadsheet-export-boundary": paths[3],
    "python/csv-duplicate-headers": paths[0],
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
