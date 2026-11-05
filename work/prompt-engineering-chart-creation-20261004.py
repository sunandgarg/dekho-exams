"""Add original chart-creation prompt lessons, a project, and a quiz."""

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
project_path = "prompt-engineering/cold-chain-chart-review-project"
quiz_path = "quizzes/prompt-engineering-chart-creation"

specs = [
    dict(slug="chart-prompt-decision-and-measure-contract", title="Chart prompts: state the decision and measured quantity", section=applications,
         summary="Begin with the reader's question, metric definition, and data grain.",
         definition="A chart prompt should begin with the decision the viewer must make, not a request for a fashionable graphic. State the measured quantity, unit, observation grain, population, and relevant threshold. A shipment count, a temperature reading, and time spent above a limit are different measures. The model can propose a display, but the application should supply verified data and a typed metric contract. If a requested conclusion cannot be supported by the available grain, the prompt must refuse that claim and offer a narrower one. A title should name what the marks encode rather than imply a causal finding.",
         case="A fictional cold-chain team has six hourly readings for container C-47: 4.1, 4.4, missing, 5.8, 5.5, and 4.9 degrees Celsius. The operational question is which observed hours crossed a 5.0-degree limit and whether a missing hour prevents an all-clear. A line chart can show the observed sequence and a threshold, but the readings cannot prove how long the container stayed above the limit between samples. The prompt asks for observed exceedances, not continuous exposure time or product safety.",
         sample="Decision: identify observed readings above 5.0 °C.\nEntity: container C-47; grain: one scheduled reading per hour.\nSeries: 4.1, 4.4, missing, 5.8, 5.5, 4.9 °C.\nAllowed claim: two observed readings exceed the limit.\nUnsupported claim: hours continuously above the limit.",
         cost="Defining M measures takes O(M) review effort before rendering, while inspecting N records takes O(N) for a direct scan. That small up-front cost avoids expensive revision after a chart communicates the wrong quantity. Do not ask the model to infer a missing unit or population from a column name alone. A prompt with a precise decision contract is shorter than a broad creative brief followed by repeated corrections.",
         mistakes=["Do not equate two high readings with two hours of continuous exposure.", "Do not omit the unit or observation grain.", "Do not write a safety conclusion that the readings cannot establish."],
         related=["prompt-engineering/dataset-intake-column-contract", "prompt-engineering/chart-interpretation-axis-and-unit-gate", "prompt-engineering/document-brief-audience-and-decision-contract"]),
    dict(slug="chart-prompt-encoding-and-scale-choice", title="Chart prompts: choose marks and scales by data type", section=applications,
         summary="Match time, categories, and magnitudes to an explicit visual encoding.",
         definition="A prompt for chart creation should map each field to a visual channel with a reason. Ordered time points can use positions along a time axis; independent categories can use bars or dots. The chosen mark should preserve the comparison the reader needs. State the scale domain and whether zero is required for a magnitude comparison. A truncated bar axis can exaggerate a small difference; a nonzero line-axis baseline may be acceptable when clearly labeled and used to inspect small variation. Avoid dual axes unless their units and relationship are explicit. Color should carry a named category or status, not decorate the page.",
         case="Container C-47's hourly readings are ordered observations. The chart uses points connected only across adjacent observed hours. It places time on the horizontal axis, degrees Celsius on the vertical axis, and a labeled 5.0-degree threshold. The missing third hour breaks the connection; no line segment crosses that gap. A separate category comparison of depot counts would use bars with a zero baseline. The prompt does not request a pie chart for hourly values or a second axis for an unrelated humidity series.",
         sample="Mark: point plus line for adjacent observed readings.\nX: scheduled hour in local time; Y: temperature in °C.\nThreshold: labeled 5.0 °C reference line.\nMissing hour: visible gap, not an interpolated mark.\nNo dual axis and no unlabelled scale truncation.",
         cost="Rendering N marks is generally O(N), while adding too many series increases visual search and legend review. A long sequence may need downsampling, but the method must preserve peaks relevant to the threshold. Encoding review is a low-cost gate: inspect whether the field type, unit, baseline, and mark agree before drawing. If the model invents a chart type first and maps data afterward, a misleading scale can survive even when every underlying value is correct.",
         mistakes=["Do not join points across a missing interval.", "Do not use a nonzero bar baseline for an ordinary magnitude comparison.", "Do not encode an unlabelled second unit on the same axis."],
         related=["prompt-engineering/chart-interpretation-axis-and-unit-gate", "prompt-engineering/evidence-bound-report-summary", "prompt-engineering/ui-visual-and-accessibility-release-gate"]),
    dict(slug="chart-prompt-missing-data-and-denominator", title="Chart prompts: expose missing data and checked denominators", section=applications,
         summary="Keep absent observations distinct from zero and compute rates over eligible records.",
         definition="A chart prompt must state how missing, invalid, duplicate, and late records affect both marks and summary statistics. A missing temperature is not a zero-degree reading. Count eligible observations separately from scheduled slots, then name the denominator whenever a rate appears. Do not interpolate missing values unless the task explicitly authorizes a method and labels the result as estimated. When duplicate readings conflict, resolve the data issue before plotting rather than letting the model choose a convenient value. A chart can show uncertainty or a gap; it need not manufacture a continuous series.",
         case="C-47 has six scheduled slots and five valid observations. Two observed values exceed 5.0 degrees, so the observed exceedance rate is 2 divided by 5, or 40%; the missing slot is excluded from that denominator and remains visible as missing. The team does not call 40% the fraction of time above the limit. If the missing slot later receives a verified late reading, the chart version changes and the rate is recomputed. A conflicting duplicate at the same hour blocks release until the sensor record is reconciled.",
         sample="Scheduled slots: 6; valid readings: 5; missing: 1.\nObserved exceedances: 2; eligible denominator: 5.\nObserved exceedance rate: 2 / 5 = 40%.\nMissing slot: gap, not 0 °C.\nConflicting duplicate: hold chart until resolved.",
         cost="A single pass over N records can validate slot membership and compute counts in O(N) time with O(U) storage for U unique slot keys. Reconciliation of duplicates may add review time, but it prevents a false aggregate from being repeated in reports. Displaying the denominator adds little space and removes ambiguity. Keep rate and count together so a viewer does not mistake a small sample for a stable operational trend.",
         mistakes=["Do not plot a missing reading as zero.", "Do not divide by six when the stated rate is over five valid observations.", "Do not describe a reading fraction as elapsed exposure time."],
         related=["prompt-engineering/aggregate-denominator-reconciliation", "prompt-engineering/dataset-intake-column-contract", "prompt-engineering/evidence-bound-report-summary"]),
    dict(slug="chart-prompt-reproducible-spec-and-lineage", title="Chart prompts: produce a reproducible spec and data lineage", section=production,
         summary="Store field mappings, transforms, inputs, and version IDs outside prose.",
         definition="A chart-generation prompt should produce a machine-checkable spec, not only a picture and a persuasive caption. The spec records the input dataset version, field names and types, filters, aggregations, scale domains, threshold, missing-value rule, and output size. Keep raw data and transforms separate so a reviewer can recompute every mark. A rendered image is a view of that spec; it is not evidence that the transformation was correct. The application validates the spec against an allowlist of fields and operators before rendering. Store a content hash or immutable artifact ID for the exact input used.",
         case="The C-47 chart packet names snapshot S-47 and a six-slot window. Its spec maps local hour to x, observed temperature to y, and a 5.0-degree threshold to a reference line. It rejects a model-proposed field called estimated_temperature because that field is not in the approved dataset. A late third-hour record later creates snapshot S-48 and a new chart version; the old report remains tied to S-47. The reviewer can compare the two versions without asking the model to remember how it drew the first one.",
         sample="Input: snapshot S-47, six scheduled slots.\nFields: local_hour, observed_temperature_c, reading_status.\nTransform: valid readings only for rate; missing slot retained as gap.\nEncoding: hour -> x; temperature -> y; limit -> rule.\nReject unknown field: estimated_temperature_c.",
         cost="Validating K spec fields and transforms is O(K), with a separate O(N) check against N source rows when recomputing marks. Storing one compact spec per version is inexpensive relative to keeping an unreviewable screenshot as the only artifact. A renderer can change appearance across releases, so preserve both spec version and rendered output ID when comparing. The prompt should not bury important transforms in free-form wording that a parser cannot verify.",
         mistakes=["Do not accept a field the approved dataset does not contain.", "Do not replace source data lineage with a screenshot filename.", "Do not silently mutate an old chart when a late record arrives."],
         related=["prompt-engineering/prompt-release-artifact-bundle", "prompt-engineering/workbook-task-contract-and-cell-provenance", "prompt-engineering/api-example-fixture-and-secret-safety-gate"]),
    dict(slug="chart-prompt-accessibility-and-render-review", title="Chart prompts: review rendered and nonvisual outputs", section=production,
         summary="Check the image, labels, text alternative, and underlying values as one artifact.",
         definition="A valid chart spec does not guarantee a readable result. Review the rendered artifact at its intended size, including axis labels, units, threshold annotation, legend, contrast, and clipping. Provide a concise text alternative that states the chart's purpose and a longer data view when exact values matter. Avoid encoding status by color alone; pair it with labels or distinct marks. The text alternative must match the actual plot, including missing intervals and uncertainty, rather than repeating an earlier draft claim. A release gate compares rendered marks with the source table and checks keyboard or screen-reader access when the chart is interactive.",
         case="The C-47 plot renders correctly at desktop width but clips the 5.0-degree threshold label on a narrow report page. A visual review catches the cut-off label before release. The text alternative states that two of five observed hourly readings exceed the limit and that the third scheduled hour is missing. An accompanying data view lists all six slots, including the missing one. The team checks that an interactive tooltip is reachable by keyboard; if it is not, the static data view still exposes the exact values.",
         sample="Visual check: title, time zone, °C axis, 5.0 °C label, gap.\nText: two of five observed readings above limit; one missing slot.\nExact data: six scheduled rows available in a data view.\nColor: supplemented by labels or distinct marks.\nNarrow render: threshold label must remain visible.",
         cost="A visual review costs a small fixed inspection per viewport, while exact value reconciliation requires O(N) comparisons for N plotted rows. Accessible alternatives add authoring time but allow a reader to obtain the same critical finding without relying on color or pixels. Automated schema checks cannot catch clipping, misleading label placement, or a stale text alternative. Treat the rendered chart and its nonvisual description as one release unit.",
         mistakes=["Do not assume a valid spec means the rendered chart is legible.", "Do not make color the sole carrier of threshold status.", "Do not publish a text alternative that ignores the missing hour."],
         related=["prompt-engineering/accessible-output-evaluation-slices", "prompt-engineering/purpose-bound-image-alternatives", "prompt-engineering/ui-visual-and-accessibility-release-gate"]),
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]) & lookup.keys()
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: review a cold-chain temperature chart"
titles[quiz_path] = "Chart-creation prompt decisions"


def link(path):
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(paths_to_link):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(paths_to_link)) + "</ul>"


def related(paths_to_link):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(paths_to_link)]


def article(path, title, summary, body, section, order, connections, kind="tutorial"):
    row = copy.deepcopy(lookup["prompt-engineering/evaluation-slice-design"])
    subjects = {applications: "prompt-engineering-applications", production: "prompt-engineering-production", projects: "prompt-engineering-project"}
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path, title=title,
               summary=summary, body=body, subject=subjects[section], difficulty="Advanced",
               tags=["prompt engineering", "chart creation"], sort_order=31100 + order,
               status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"].update(kind=kind, reading_minutes=11 if kind == "tutorial" else 18,
                       author_path="authors/aitrove-editorial", subject_root=subject_root,
                       section_path=section, content_format="html", seo_ready=True,
                       related=related(connections))
    return row


new_rows = []
for index, (path, spec) in enumerate(zip(paths, specs)):
    connections = [spec["section"], subject_root] + spec["related"] + [other for other in paths if other != path] + [project_path, quiz_path]
    body = ("<p>" + html.escape(spec["definition"]) + "</p>"
            + "<h2>Operational case</h2><p>" + html.escape(spec["case"]) + "</p>"
            + '<pre><code class="language-text">' + html.escape(spec["sample"], quote=False) + "</code></pre>"
            + "<h2>Performance and operating cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
            + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in spec["mistakes"]) + "</ul>"
            + "<h2>Connected lessons</h2>" + links(connections))
    new_rows.append(article(path, spec["title"], spec["summary"], body, spec["section"], index * 10, connections))

project_connections = paths + ["prompt-engineering/chart-interpretation-axis-and-unit-gate", "prompt-engineering/aggregate-denominator-reconciliation", quiz_path]
project_body = (
    "<p>Prepare a prompt and review packet for a fictional cold-chain container C-47. Six hourly slots contain five observed temperatures in degrees Celsius: 4.1, 4.4, a missing third slot, 5.8, 5.5, and 4.9. The limit is 5.0. The reader needs to see which observed values exceed that limit and where the record is incomplete. The project creates a chart contract and a review plan; it does not assert product safety or infer continuous exposure between samples.</p>"
    "<h2>Build the chart contract</h2><p>Use ordered hourly points, a labeled temperature axis, and a labeled limit line. Break the line at the missing third slot. The observed exceedance rate is two of five valid readings, or 40%, with the denominator printed beside the rate. The prompt must reject a zero substituted for the missing slot and must not claim two hours continuously above the threshold. A late verified reading changes the dataset version and triggers a new chart, rather than overwriting the original report.</p>"
    "<h2>Review the artifact</h2><p>Bind the chart to snapshot S-47 and list the exact fields and transforms. Validate that every requested field exists and that the rendered marks match the six-slot data view. Inspect desktop and narrow layouts for labels, clipping, and a visible gap. Provide a text alternative that states two of five observed readings exceed the limit and one slot is missing. If an interactive tooltip is not keyboard accessible, the exact data view must still carry the values.</p>"
    '<pre><code class="language-text">C-47 slots: 4.1, 4.4, missing, 5.8, 5.5, 4.9 °C.\nLimit: 5.0 °C; observed exceedances: 2 / 5 = 40%.\nChart: hourly points, gap at slot 3, labeled limit line.\nPacket: snapshot S-47, field mapping, transform, render ID.\nClaim boundary: no continuous-exposure or safety conclusion.</code></pre>'
    "<h2>Performance and review cost</h2><p>A pass over N slots validates observations and computes the rate in O(N) time, with O(N) space for the explicit chart data view. Checking the specification takes O(K) for K fields and transforms. Rendering and narrow-screen inspection add review time but reveal errors that a JSON schema cannot detect. The release packet keeps the original snapshot and chart version so a later correction can be explained without rewriting earlier evidence.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not fill the missing slot with zero.</li><li>Do not divide the observed rate by all six scheduled slots.</li><li>Do not join a line across the missing hour.</li><li>Do not treat a valid spec as proof of a readable render.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Create and verify an evidence-bound hourly temperature chart.", project_body, projects, 60, project_connections, "project"))

questions = [
    ("What question should anchor the C-47 chart?", "Which observed readings exceed 5.0 °C", "How long the product was unsafe", "Which color looks impressive", "The available grain supports observed threshold crossings."),
    ("What is the observation grain?", "One scheduled reading per hour", "Continuous temperature", "One reading per shipment", "The data has discrete hourly slots."),
    ("What chart encoding fits ordered hourly readings?", "Time on x and temperature on y", "Unrelated categories in a pie", "A second hidden axis", "Position preserves order and measured magnitude."),
    ("What happens at the missing third slot?", "The line shows a gap", "The value becomes zero", "The line implies an observed midpoint", "Missing data must remain visibly missing."),
    ("What is the observed exceedance count?", "Two", "Three", "Six", "The 5.8 and 5.5 readings exceed the 5.0 limit."),
    ("What is the eligible denominator for observed exceedance rate?", "Five valid readings", "Six scheduled slots", "Two high readings", "The named rate is over observed valid readings."),
    ("What is the observed exceedance rate?", "40%", "33.33%", "50%", "Two divided by five is 40%."),
    ("Can the chart claim two continuous hours above the limit?", "No, the series is sampled hourly", "Yes, two points prove the full interval", "Yes, if the line is red", "Between-sample behavior is not measured."),
    ("What should a chart spec preserve?", "Input version, fields, transforms, and scales", "Only a screenshot", "Only a persuasive caption", "Those details make marks reviewable."),
    ("The model requests an unknown estimated-temperature field. What follows?", "Reject it against the approved dataset", "Invent the values", "Hide the field name", "Field validation prevents unsupported marks."),
    ("A narrow render clips the limit label. Is it ready?", "No, repair and inspect the render", "Yes, the spec is valid", "Yes, if a caption is confident", "Visual defects require render review."),
    ("What should the nonvisual alternative include?", "Two of five high readings and one missing slot", "Only the chart colors", "A safety claim", "The alternative must preserve the decision-relevant facts."),
]
quiz = copy.deepcopy(lookup["quizzes/prompt-engineering-terminal-workflows"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Test measure, encoding, missing data, lineage, and rendered access.",
            body="<p>Choose the chart decision supported by the measured C-47 data.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, production, quizzes]),
            sort_order=31170, status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"].update(subject_root=subject_root, section_path=quizzes, content_format="html",
                    author_path="authors/aitrove-editorial", seo_ready=True, duration_minutes=12,
                    related=related(paths + [project_path]),
                    questions=[{"prompt": prompt,
                                "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                "answer": (-index) % 3, "explanation": explanation}
                               for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)])
new_rows.append(quiz)

for hub_path, selected, title, summary in [
    (applications, paths[:3], "Prompted chart design", "Choose the measure and encoding, then expose gaps and checked denominators."),
    (production, paths[3:], "Chart release checks", "Store reproducible specs and review rendered and nonvisual outputs."),
    (projects, [project_path], "Cold-chain chart review", "Apply measured-data limits to a six-slot temperature chart."),
    (quizzes, [quiz_path], "Chart-creation decisions", "Test marks, gaps, rates, lineage, and accessibility."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

lookup[subject_root]["body"] += "<h2>Chart creation with prompts</h2><p>Turn a measured question into a checked chart specification and accessible artifact.</p>" + links(paths + [project_path, quiz_path])
lookup[subject_root]["updated_at"] = stamp

backlinks = {
    "prompt-engineering/dataset-intake-column-contract": paths[0],
    "prompt-engineering/chart-interpretation-axis-and-unit-gate": paths[1],
    "prompt-engineering/aggregate-denominator-reconciliation": paths[2],
    "prompt-engineering/workbook-task-contract-and-cell-provenance": paths[3],
    "prompt-engineering/accessible-output-evaluation-slices": paths[4],
    "prompt-engineering/purpose-bound-image-alternatives": paths[4],
    "prompt-engineering/evidence-bound-report-summary": project_path,
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
