"""Add data-analysis and reporting applications to Prompt Engineering."""

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
projects = "prompt-engineering/projects"
quizzes = "prompt-engineering/quizzes"
project_path = "prompt-engineering/shipment-report-verification-project"
quiz_path = "quizzes/prompt-engineering-data-workflows"

aggregation_code = '''shipments = [
    {"shipment_id": "SH-841", "region": "north", "late": False},
    {"shipment_id": "SH-842", "region": "south", "late": True},
    {"shipment_id": "SH-843", "region": "south", "late": False},
    {"shipment_id": "SH-844", "region": "north", "late": True},
    {"shipment_id": "SH-845", "region": "south", "late": False},
    {"shipment_id": "SH-846", "region": "north", "late": False},
    {"shipment_id": "SH-842", "region": "south", "late": True},
]

unique_shipments = {}
for shipment in shipments:
    shipment_id = shipment["shipment_id"]
    previous = unique_shipments.get(shipment_id)
    if previous is not None and previous != shipment:
        raise ValueError(f"conflicting duplicate: {shipment_id}")
    unique_shipments[shipment_id] = shipment

late_count = sum(shipment["late"] for shipment in unique_shipments.values())
denominator = len(unique_shipments)
if denominator == 0:
    raise ValueError("empty shipment cohort")
late_rate = 100 * late_count / denominator
print(f"unique={denominator} late={late_count} rate={late_rate:.2f}%")'''

specs = [
    {
        "slug": "dataset-intake-column-contract",
        "title": "Dataset intake prompts: define a column before analyzing it",
        "summary": "Record grain, units, missingness, and selection rules before asking for findings.",
        "definition": "A dataset-intake prompt should establish what one row represents, which time window and population were exported, the meaning and unit of each relevant column, and how null, duplicate, or corrected records are represented. It should ask for unknown definitions instead of inferring them from a few sample rows. Keep the schema and source revision alongside the analysis request so a later report can be reproduced. A model can flag suspicious columns, but the data owner must confirm business semantics. No summary is reliable if a field named total alternates between cents and whole currency units.",
        "case": "An operations analyst receives a shipment export with 4,823 rows. The column arrival_time contains UTC timestamps for most rows but local depot time for a small legacy slice. A status value of closed may mean delivered or canceled depending on the carrier version. The assistant cannot compute a late-delivery rate from this sample until the time zone and status mapping are supplied. It produces a compact intake question list and a record-level exception bucket. The analyst then confirms that 100 rows are exact duplicates, leaving 4,723 unique shipments; 23 still lack a resolved status, so the known-status cohort has 4,700 shipments.",
        "sample": "Dataset: shipment_export_v7; row grain: one shipment event.\nRequired: shipment_id, promised_at, delivered_at, status, carrier_version.\nUnknown: legacy timestamp zone; meaning of closed by carrier.\nRaw=4,823; exact duplicates=100; unique=4,723; unknown=23.\nKnown-status denominator=4,700 after time and status review.",
        "cost": "Scanning R rows for missing fields and duplicate keys takes O(R) expected time with a hash map and O(U) space for U unique keys. Time-zone conversion and versioned status mapping add work proportional to affected rows. A model call is cheap compared with publishing a wrong denominator, but repeated whole-file prompts waste tokens and may expose private records. Supply a typed schema, aggregate profile, and selected exceptions first. Measure unresolved definitions as a first-class result; do not bury them in a footnote after a confident chart.",
        "mistakes": ["Do not infer column units from a small sample.", "Do not treat an event row count as a shipment count without checking duplicates.", "Do not mix local and UTC timestamps in one comparison."],
        "related": ["prompt-engineering/input-normalization-contract", "prompt-engineering/schema-and-abstention", "prompt-engineering/retrieval-freshness-and-conflict"],
        "sample_lang": "text",
    },
    {
        "slug": "classification-rubric-and-unknown-label",
        "title": "Classification prompts: write the label boundary first",
        "summary": "Separate similar classes, multi-label cases, and unknowns with a reviewable rubric.",
        "definition": "A classification prompt should provide a finite label set, the evidence required for each label, precedence or multi-label rules, and an explicit unknown route. Labels should represent business decisions that can be reviewed, not vague sentiment about the text. Include near-boundary examples in evaluation, especially cases that mention a topic without requesting its associated action. The model's label is a proposal; downstream effects still require separate authorization. Track disagreements by case type rather than optimizing only overall accuracy, which can hide a rare but costly class.",
        "case": "A support queue uses labels delivery_delay, damaged_item, billing_dispute, and unknown. Ticket TK-917 says a package arrived late and the outer box was torn, but the customer asks only when a replacement for the damaged item will ship. If the queue permits multiple labels, the case can carry both delivery_delay and damaged_item while damaged_item owns the response workflow. Ticket TK-918 merely asks what the late-delivery policy says; it is not evidence that this customer's parcel was late. A thin prompt that keys on the word late would misroute the second ticket. The rubric requires a claimed event, requested action, and evidence span.",
        "sample": "TK-917: claimed late arrival + torn box; request=replacement status.\nLabels: delivery_delay, damaged_item; primary=damaged_item.\nTK-918: policy question only; no claimed late event.\nRoute: informational policy answer, not delay compensation.\nUnknown: missing event or conflicting account evidence -> human review.",
        "cost": "A fixed rubric over L labels has O(L) decision work per case in a simple implementation; review time rises with ambiguous labels and overlapping policies. Adding more examples increases prompt tokens and can overfit to wording rather than the intended boundary. Use a held-out set with positive, negative, and near-boundary cases for each label. Report per-class precision and recall and the share sent to unknown. A classifier that rarely abstains may appear efficient while passing unsupported cases into an automated effect.",
        "mistakes": ["Do not classify a policy question as a reported incident.", "Do not force an uncertain ticket into a known class to avoid an unknown label.", "Do not use the label alone as approval for a refund or replacement."],
        "related": ["prompt-engineering/contrastive-example-boundaries", "prompt-engineering/selective-prediction-thresholds", "prompt-engineering/request-risk-routing-contract"],
        "sample_lang": "text",
    },
    {
        "slug": "aggregate-denominator-reconciliation",
        "title": "Aggregation prompts: pin the denominator and recompute the rate",
        "summary": "Use the model to specify the cohort, then calculate counts with a deterministic program.",
        "definition": "An aggregation prompt should state the unit of analysis, inclusion window, exclusion rules, deduplication key, numerator, denominator, and rounding policy. The model can propose those definitions and explain the result, but a deterministic query or program must count the records. Reconcile raw rows to eligible rows and eligible rows to each group before publishing percentages. A group rate and overall rate must use their own denominators; averaging group percentages without weights is generally wrong when group sizes differ. Treat a zero denominator and conflicting duplicate as explicit errors, not a zero-percent result.",
        "case": "A six-shipment extract contains two late deliveries and one repeated event for the same shipment. Counting all seven rows would report two late rows out of seven, while deduplicating by shipment ID yields two of six, or 33.33 percent. The sample code rejects duplicates that disagree on region or lateness rather than silently keeping the last row. At full scale, the team reconciles 4,823 raw events to 4,723 unique shipments, excludes 23 unresolved statuses, and counts 282 late of 4,700 eligible shipments: 6.00 percent. North has 80 of 2,000 late; south has 202 of 2,700. Those group rates differ, so a narrative should name the cohort before suggesting any reason for the difference.",
        "sample": aggregation_code,
        "cost": "For R input rows, hash-based deduplication and counting take O(R) expected time and O(U) space for U unique shipment IDs. Grouping by G regions adds O(G) counters. A database query may move the work closer to storage, but its result still needs a reconciled filter and key definition. The model's token use should depend on a small schema and aggregate output, not the entire row set. Recompute percentages from checked counts and display enough precision to avoid hiding a material change behind rounding.",
        "mistakes": ["Do not use raw event rows as the denominator when the question asks about shipments.", "Do not average regional rates without weighting by regional shipment counts.", "Do not resolve conflicting duplicate records by whichever row appears last."],
        "related": ["prompt-engineering/deterministic-calculation-gates", "prompt-engineering/read-only-sql-generation-gate", "prompt-engineering/dataset-intake-column-contract"],
        "sample_lang": "python",
    },
    {
        "slug": "evidence-bound-report-summary",
        "title": "Report summaries: preserve contrary results and missing data",
        "summary": "Bind each reported claim to a checked figure, time window, and limitation.",
        "definition": "A report-writing prompt should receive verified metrics, a named audience, a decision question, and a required claim-to-evidence map. The assistant can turn numbers into readable prose, but it must not invent a causal explanation or omit a result merely because it complicates the headline. Distinguish measured change, plausible explanation, and proposed follow-up. Require the summary to mention excluded records and the period covered. If a headline depends on one region while another moves in the opposite direction, preserve that contrast. Review the final rendered summary against the aggregate table, not just against the prompt.",
        "case": "A weekly parcel report shows a 6.00 percent late rate across 4,700 eligible shipments. North has 80 late out of 2,000, or 4.00 percent. South has 202 out of 2,700, about 7.48 percent. An assistant draft says service improved everywhere because the overall rate fell from a prior week. That claim is unsupported: the prior-week regional denominators have not been supplied, and 23 legacy records were excluded because their delivery status remains unresolved. A defensible summary states the current counts and exclusion, then asks for comparable prior-week cohorts before attributing an improvement.",
        "sample": "Audience: operations lead; period: week W-39.\nChecked: all=282/4,700=6.00%; north=80/2,000=4.00%.\nChecked: south=202/2,700≈7.48%; unresolved statuses=23.\nAllowed claim: south's observed rate exceeds north's in this cohort.\nBlocked claim: a change caused improvement across every region.",
        "cost": "Checking K narrative claims against M verified figures takes O(K+M) with an indexed metric map; manual adjudication of ambiguous claims is the expensive part. A claim ledger adds modest storage but makes later corrections traceable. Short summaries reduce reading time, yet compressing away the denominator or exception count can invert the decision. Evaluate summaries for numerical agreement, omitted contrary results, unsupported causal language, and missing caveats. A polished paragraph with one false claim is worse than a shorter statement of what remains unknown.",
        "mistakes": ["Do not describe an observed difference as a proven cause.", "Do not omit a contrary region to make the headline cleaner.", "Do not compare weeks until the cohorts and exclusion rules match."],
        "related": ["prompt-engineering/evidence-id-traceability", "prompt-engineering/aggregate-denominator-reconciliation", "prompt-engineering/evaluation-label-disagreement"],
        "sample_lang": "text",
    },
    {
        "slug": "chart-interpretation-axis-and-unit-gate",
        "title": "Chart prompts: inspect axes, units, and missing series first",
        "summary": "Extract chart structure before interpreting a visual pattern or writing a caption.",
        "definition": "A chart-interpretation prompt should first capture axis labels, units, scale, series names, time span, filters, and visible gaps. A plotted shape alone cannot establish a value, especially when the axis begins above zero or uses a logarithmic scale. Prefer the underlying data table for exact comparisons and use the chart for visual orientation. If only an image is available, mark values as estimates and preserve uncertainty from resolution or obscured labels. A caption should separate what the chart displays from any explanation of why it happened.",
        "case": "A dashboard screenshot plots weekly late-delivery rates for two depots. Its vertical axis starts at 3 percent rather than zero, so the difference between 4.0 and 7.5 percent looks much larger than it would on a full scale. A pale third line is visible, but its legend is clipped in the screenshot. The assistant asks for the source table and full legend before naming that series or stating exact values. Once the table arrives, it reports the rates with denominators and notes that 23 unresolved records are outside the plotted late-rate cohorts. It does not claim that a staffing change caused the difference.",
        "sample": "Visual intake: x=week; y=late rate (%); y-min=3%, not 0%.\nSeries: north, south, third series label clipped.\nTable check: north=4.00%; south≈7.48%; unknown status=23.\nCaption: observed rates and denominators; no causal claim.\nIf source table absent: estimated visual values, not exact numbers.",
        "cost": "Reading a source table of P plotted points is O(P) for a simple validation pass, while image interpretation adds model cost and can fail on low-resolution labels. Avoid repeated image prompts when a structured export is available. Keep the source table, chart configuration, and generated caption together so a chart refresh cannot leave an obsolete narrative on screen. Measure unit errors, missing-series omissions, and false exactness separately. A larger screenshot is not a substitute for the underlying data when the decision depends on precise values.",
        "mistakes": ["Do not treat a truncated axis as evidence of an extreme change.", "Do not name an obscured series from its color alone.", "Do not report image-derived estimates as exact table values."],
        "related": ["prompt-engineering/image-region-verification-contract", "prompt-engineering/multimodal-evidence-boundary", "prompt-engineering/evidence-bound-report-summary"],
        "sample_lang": "text",
    },
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]).intersection(lookup)
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: verify a shipment performance report"
titles[quiz_path] = "Prompt engineering for data workflows"


def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(selected):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(selected)) + "</ul>"


def related(selected):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(selected)]


def article(path, title, summary, body, section, order, connections, kind="tutorial"):
    entry = copy.deepcopy(lookup["prompt-engineering/evaluation-slice-design"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)),
                 path=path, title=title, summary=summary, body=body,
                 subject="prompt-engineering-applications" if section == applications else "prompt-engineering-project",
                 difficulty="Advanced", tags=["prompt engineering", "data workflows"],
                 sort_order=order, status="published", published_at=stamp,
                 created_at=stamp, updated_at=stamp)
    entry["data"].update(kind=kind, reading_minutes=11 if kind == "tutorial" else 18,
                         author_path="authors/aitrove-editorial", subject_root=subject_root,
                         section_path=section, content_format="html", seo_ready=True,
                         related=related(connections))
    return entry


new_rows = []
for index, (path, spec) in enumerate(zip(paths, specs)):
    connections = [applications, subject_root] + spec["related"] + [peer for peer in paths if peer != path] + [project_path, quiz_path]
    body = ("<p>" + html.escape(spec["definition"]) + "</p>"
            + "<h2>Operational case</h2><p>" + html.escape(spec["case"]) + "</p>"
            + f'<pre><code class="language-{spec["sample_lang"]}">' + html.escape(spec["sample"], quote=False) + "</code></pre>"
            + "<h2>Performance and operating cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
            + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(mistake) + "</li>" for mistake in spec["mistakes"]) + "</ul>"
            + "<h2>Connected lessons</h2>" + links(connections))
    new_rows.append(article(path, spec["title"], spec["summary"], body, applications, 28400 + index * 10, connections))

project_connections = paths + ["prompt-engineering/read-only-sql-generation-gate", "prompt-engineering/evaluation-slice-design", "python/mutation-testing", quiz_path]
project_body = (
    "<p>This project turns a fictional shipment export into a report for an operations lead. The assistant can propose schema questions, label tickets, explain checked counts, draft prose, and interpret a chart. It cannot silently decide the carrier's status mapping, run a data correction, or assert causation from a visual trend. Deliver a reproducible packet: source revision, column contract, deduplication policy, calculation output, claim ledger, chart data, and a list of unresolved records. Keep raw customer identifiers out of the prompt bundle and report.</p>"
    "<h2>Reconcile the cohort</h2><p>The raw export has 4,823 events. Remove 100 exact duplicate shipment IDs and place conflicting duplicates in review rather than taking the last record. Of 4,723 unique shipments, 23 legacy records have unresolved status and are excluded from the stated rate. The 4,700 eligible shipments include 282 marked late. North contributes 80 late of 2,000, and south contributes 202 of 2,700. The overall rate is 6.00 percent, north is 4.00 percent, and south is about 7.48 percent. Keep this exclusion rule fixed across comparisons and normalize legacy local timestamps before determining lateness.</p>"
    "<h2>Review labels and narrative</h2><p>Classify ticket TK-917 as both delivery delay and damage, with damage owning the replacement request. Treat TK-918 as a question about policy, not a confirmed late parcel. Draft an executive paragraph with the current rates and denominators, then compare each claim with the verified aggregate. Reject a sentence saying every region improved when prior-week regional cohorts are unavailable. The chart's y-axis begins at 3 percent and one legend entry is clipped, so obtain its source table before using exact values or naming the third series. Add a benign control with a complete table and a clear zero-based axis.</p>"
    '<pre><code class="language-text">Raw=4,823; exact duplicates=100; unique=4,723.\nUnknown status=23 excluded; eligible=4,700.\nLate=282; overall=282/4,700=6.00%.\nNorth=80/2,000=4.00%; south=202/2,700≈7.48%.\nTK-917: delay + damage; TK-918: policy question only.\nReport gate: checked counts, matched claims, visible chart scale.</code></pre>'
    "<h2>Performance and operating cost</h2><p>Deduplication and counting over R events take O(R) expected time and O(U) space for U unique shipments. Sorting or reconciling conflicting corrections adds review work. For C held-out reporting cases and V prompt variants, comparison uses O(CV) model evaluations plus deterministic checks. Measure wrong denominators, false labels, unsupported causal claims, omitted contrary results, and source-table mismatches separately. A report that reads well but changes the cohort fails. Preserve the exact dataset revision and code output so another analyst can reproduce every published number.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not use row count as a shipment count without a stable key.</li><li>Do not call a policy question a confirmed delay.</li><li>Do not claim an image supplies exact numbers when the source table is available.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Build a reproducible shipment report with checked cohorts, labels, claims, and chart captions.", project_body, projects, 28460, project_connections, kind="project"))

questions = [
    ("A column named total has mixed units. What comes first?", "Confirm units and source version", "Average all values", "Ask for a shorter chart", "A name is not a verified unit contract."),
    ("An export has 4,823 events, 100 exact duplicates, and 23 unresolved statuses. What is the known-status denominator?", "4,700 eligible shipments", "4,823 event rows", "4,723 unique shipments", "Unknown-status rows are excluded by the stated cohort rule."),
    ("A ticket asks what a delay policy says but reports no delayed parcel. How should it be routed?", "As an informational policy question", "As a confirmed delay claim", "As an automatic refund", "Topic mention is not evidence of the event."),
    ("When should a classifier use unknown?", "When required evidence or class boundary is unresolved", "Whenever a ticket is long", "Only when all labels are equally common", "Unknown prevents unsupported downstream action."),
    ("Two rows share a shipment ID but disagree on lateness. What should deduplication do?", "Flag the conflict for review", "Keep whichever appears last", "Count both as separate shipments", "Conflicting duplicates are not exact duplicates."),
    ("Why is the unweighted average of two regional rates unsafe?", "Their shipment denominators may differ", "Percentages cannot be compared", "It always equals the overall rate", "The overall rate weights each region by its cohort size."),
    ("What supports an executive summary claim?", "A checked figure, cohort, period, and limitation", "A fluent sentence", "A model confidence phrase", "Claims need traceable quantitative support."),
    ("The overall rate fell but prior regional cohorts are missing. What cannot be claimed?", "Every region improved", "The current overall numerator", "The current north denominator", "A regional trend needs comparable regional data."),
    ("A chart y-axis starts at 3 percent. What risk does that create?", "Visual differences may look exaggerated", "The data values are invalid", "All series are missing", "Scale changes the visual impression."),
    ("The legend is clipped and no source table is available. What should the caption do?", "Mark values and the unnamed series as uncertain", "Invent the series name from its color", "Publish exact values anyway", "The image does not support exact identification."),
    ("What should happen if the eligible cohort has zero records?", "Return an explicit denominator error", "Report zero percent late", "Reuse last week's denominator", "A zero denominator cannot support a rate."),
    ("Which outcome blocks a report despite good prose?", "An unsupported causal claim or wrong denominator", "A short title", "One fewer paragraph", "Presentation quality cannot repair a false metric."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-multimodal-evidence"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                  path=quiz_path, title=titles[quiz_path],
                  summary="Test dataset intake, class boundaries, denominators, claims, and chart interpretation.",
                  body="<p>These cases test whether a data analysis has a stable cohort and a checkable claim. Choose the operation that preserves uncertainty when the source is incomplete.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, quizzes]),
                  sort_order=28470, status="published", published_at=stamp,
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
    (applications, paths, "Data and reporting workflows", "Define columns, label cases, recompute aggregates, bind claims, and inspect charts."),
    (projects, [project_path], "Shipment report verification", "Build a reproducible operations report from a messy export."),
    (quizzes, [quiz_path], "Data workflows quiz", "Test cohort, label, numerical, and chart boundaries."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

root_hub = lookup[subject_root]
root_hub["body"] += "<h2>Data analysis and reporting</h2><p>Use prompts to define the question; verify the cohort, calculation, and claim outside the model.</p>" + links(paths + [project_path, quiz_path])
root_hub["updated_at"] = stamp

backlinks = {
    "prompt-engineering/input-normalization-contract": paths[0],
    "prompt-engineering/contrastive-example-boundaries": paths[1],
    "prompt-engineering/deterministic-calculation-gates": paths[2],
    "prompt-engineering/read-only-sql-generation-gate": paths[2],
    "prompt-engineering/evidence-id-traceability": paths[3],
    "prompt-engineering/image-region-verification-contract": paths[4],
    "prompt-engineering/evaluation-slice-design": project_path,
}
for old_path, new_path in backlinks.items():
    entry = lookup[old_path]
    entry["body"] += "<p><strong>Continue with:</strong> " + link(new_path) + ".</p>"
    entry["data"]["related"] = related([item["path"] for item in entry["data"]["related"]] + [new_path])
    entry["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newLessons": len(specs), "newProjects": 1, "newQuizzes": 1,
                  "newPaths": [entry["path"] for entry in new_rows]}))
