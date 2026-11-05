"""Add original experimental-evidence prompt lessons, project, and quiz."""

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
project_path = "prompt-engineering/parcel-scan-study-synthesis-project"
quiz_path = "quizzes/prompt-engineering-research-synthesis"

specs = [
    {
        "slug": "research-question-eligibility-prompt-contract",
        "title": "Research prompts: fix the question and eligibility first",
        "summary": "Specify population, intervention, comparator, outcome, and decision rules before reading results.",
        "definition": "An evidence-synthesis prompt needs a question and a selection contract before the model sees attractive results. Name the population, change being tested, comparator, measured outcome, observation window, acceptable study designs, and exclusion rules. Fix which report versions and search snapshot are in scope. The model can apply the rules to candidate records and flag ambiguous cases, but a reviewer owns final eligibility decisions. Save excluded records with reasons. Without this ledger, a polished summary may select only studies that support the desired answer. A narrative scan of a few supplied reports is not a comprehensive review unless its search and screening process actually supports that description.",
        "case": "A fictional parcel operator asks whether a scan-confirmation panel lowers misrouted parcels. The target population is outbound parcels at staffed sorting lines, the comparator is the existing panel, the outcome is misroutes per allocated parcel, and follow-up ends after a full shift. Before seeing results, the editor includes controlled line trials and excludes simulator exercises and before-after reports from the primary comparison. Trial ST-47 and trial ST-88 qualify. Observational report ST-61 is retained in a separate context bucket because route mix changed between shifts. An assistant that drops ST-88 after finding a worse candidate result violates the contract even if its remaining paragraph is accurate.",
        "sample": "Question: staffed sorting lines; new scan panel vs existing panel.\nPrimary outcome: misrouted parcels / allocated parcels during full shift.\nPrimary set: controlled line trials ST-47 and ST-88.\nContext only: ST-61, shift comparison with changing route mix.\nKeep an exclusion reason and report version for every screened record.",
        "cost": "Screening S candidate records is O(S) decisions once metadata is available; full-text review can dominate time when outcomes or design are unclear. A model may reduce the first-pass workload, but every uncertain exclusion needs review because an error can remove a contrary finding. Store the fixed rule and case-level decisions separately from prose. Repeating the same search later may return a different corpus, so use a dated snapshot and identifiers. The prompt should ask for missing information, not fill absent design details from plausibility.",
        "mistakes": ["Do not write eligibility rules after reading which study wins.", "Do not silently combine controlled trials with changed-shift observations.", "Do not call a supplied packet a complete literature review without a reproducible search."],
        "related": ["prompt-engineering/time-sensitive-research-contract", "prompt-engineering/evidence-bound-report-summary", "prompt-engineering/prompt-envelope-and-data-boundaries"],
        "section": applications,
    },
    {
        "slug": "study-result-extraction-and-duplicate-report-gate",
        "title": "Study extraction prompts: preserve the result behind each claim",
        "summary": "Capture design, denominators, time point, missing data, and exact result location.",
        "definition": "A study-extraction prompt should produce a record, not a free-form conclusion. Capture study ID, report version, design, allocation method if stated, eligible population, outcome definition, time point, numerator, denominator, missing outcomes, and location of the source result. Mark unavailable fields as unknown. If two documents describe one study, link them to one study ID instead of counting them as independent evidence. Keep the original wording or a bounded excerpt in the private review packet where permitted, then write a fresh synthesis from verified fields. Page or table anchors let a reviewer check each number before any calculation or claim leaves the workflow.",
        "case": "ST-47's abstract reports a 7.5 percentage-point reduction, while its results table supplies 48 misroutes among 240 control parcels and 30 among 240 candidate parcels. The extraction packet records both counts and the results-table anchor. A later conference summary repeats ST-47's same cohort and does not become a third trial. ST-88 reports 18 of 120 in control and 21 of 120 with the candidate panel. Its adverse result remains in the record. ST-61 lacks a stable allocation mechanism and has a different route mix; its design field stays observational rather than being promoted to a randomized trial because the model expects one.",
        "sample": "ST-47 | controlled line trial | control 48/240 | candidate 30/240 | full shift.\nST-88 | controlled line trial | control 18/120 | candidate 21/120 | full shift.\nST-61 | changed-shift observation | route mix differs | context only.\nDuplicate report: ST-47 conference summary -> same cohort, one study ID.\nRequired: result anchor, missing-outcome field, report version.",
        "cost": "For N reports, extraction is O(N) model jobs plus manual review of each uncertain field. Deduplicating reports by study identity needs a maintained index; title similarity alone can merge different cohorts or split one cohort into several entries. Keeping explicit numerators and denominators costs more text than a headline percentage, but makes arithmetic and missingness checkable. If a report only states a percentage without a denominator, do not manufacture counts. Anchor verification is a human or parser step, not something a self-assured model statement can replace.",
        "mistakes": ["Do not count two reports of one cohort as two studies.", "Do not fill an unstated denominator from a nearby chart or abstract.", "Do not let an abstract headline override the checkable result table without review."],
        "related": ["prompt-engineering/document-page-anchor-and-field-conflict", "prompt-engineering/dataset-intake-column-contract", "prompt-engineering/evidence-id-traceability"],
        "section": applications,
    },
    {
        "slug": "study-effect-measure-and-denominator-check",
        "title": "Study effects: calculate the measure outside the model",
        "summary": "Keep event counts, denominators, direction, and uncertainty distinct.",
        "definition": "An effect-measure prompt states which event and direction matter, then hands arithmetic to deterministic code. For a binary outcome, each arm's observed event rate is events divided by its stated denominator. The candidate-minus-control risk difference is a signed absolute difference; multiply by 100 only when reporting percentage points. It is not a relative percent change or a confidence interval. Check that counts are integers, denominators are positive, events do not exceed denominators, and the time window is the same. The model may explain the result after the program computes it, but it must not turn a point estimate into evidence of statistical certainty or operational causation.",
        "case": "In ST-47, the control rate is 48/240=20.0% and the candidate rate is 30/240=12.5%, so the candidate-minus-control difference is -7.5 percentage points. In ST-88, 18/120=15.0% and 21/120=17.5%, giving +2.5 points. One trial favors the candidate; the other does not. The assistant initially writes that the panel 'cuts misroutes by 7.5%' for all sorting lines, which confuses percentage points with relative percent and drops the contrary trial. The corrected report names each study's observed rates and leaves uncertainty and generalization for separate assessment.",
        "sample": "ST-47: 48/240=20.0%; 30/240=12.5%; difference=-7.5 points.\nST-88: 18/120=15.0%; 21/120=17.5%; difference=+2.5 points.\nDirection: candidate minus control; negative means fewer misroutes.\nNo confidence interval or pooled effect is computed by this check.",
        "cost": "Computing N independent study differences takes O(N) time and O(1) working space per streamed study. The code below validates the four counts in each record and prints signed differences. It does not adjust for cluster allocation, missing outcomes, study design, uncertainty, or dependencies among reports. Those choices require a separate analysis plan and suitable methods. Preserve raw counts alongside formatted percentages; rounding each arm before subtracting can produce a different displayed difference near a reporting threshold.",
        "mistakes": ["Do not confuse percentage points with relative percent change.", "Do not infer certainty or causation from a point estimate alone.", "Do not pool studies just because both have numeric outcomes."],
        "related": ["prompt-engineering/deterministic-calculation-gates", "prompt-engineering/aggregate-denominator-reconciliation", "prompt-engineering/evidence-bound-report-summary"],
        "section": applications,
    },
    {
        "slug": "study-design-bias-and-conflicting-results",
        "title": "Conflicting studies: inspect design before averaging outcomes",
        "summary": "Keep trial disagreements, confounding, missingness, and population differences visible.",
        "definition": "A prompt for conflicting studies should ask why estimates differ before asking for one verdict. Check allocation, baseline differences, missing outcomes, outcome definitions, follow-up windows, and whether several reports describe the same participants. Separate measured observations from explanations for heterogeneity. An observational comparison can be useful context, yet a changing route mix may confound any before-after difference. A model should not assign a numeric bias score from thin report text or dismiss a contrary result as an outlier because it is inconvenient. A qualified reviewer chooses whether quantitative pooling is sensible; absent that plan, show the study-level outcomes and the limits of comparison.",
        "case": "ST-47 favors the new panel by 7.5 points; ST-88 goes the other direction by 2.5 points. The sites used different parcel mixes, but the packet does not say whether that explains the difference. ST-61 appears favorable in a changed-shift comparison, yet the later shift handled fewer oversized parcels. The assistant must not let ST-61 break the tie or declare two favorable 'studies' versus one unfavorable trial. It labels ST-61 observational, keeps the two controlled trials distinct, and requests allocation details, missing-outcome counts, and route composition before a stronger synthesis.",
        "sample": "ST-47: candidate lower by 7.5 points; controlled line trial.\nST-88: candidate higher by 2.5 points; controlled line trial.\nST-61: later shift differed in route mix; observational context.\nUnresolved: allocation details, missing outcomes, site comparability.\nDo not pool or vote until comparability and analysis plan are reviewed.",
        "cost": "Comparing K studies across D predeclared design fields costs O(KD) reviewer checks, even before statistical analysis. A single aggregate sentence is cheaper to write but can conceal missing outcomes or an incompatible outcome definition. Build a structured comparison record once, then reuse it for an editorial summary and a reviewer queue. If source documents disagree about a study's denominator, resolve that conflict at the report level before calculating. Model generation time is rarely the limiting cost; locating and adjudicating incomplete methods is.",
        "mistakes": ["Do not count studies as votes without considering design and cohort overlap.", "Do not call an observational shift comparison a controlled trial.", "Do not invent a reason why two valid estimates disagree."],
        "related": ["prompt-engineering/retrieval-freshness-and-conflict", "prompt-engineering/cross-modal-conflict-ledger", "prompt-engineering/paired-prompt-evaluation-uncertainty"],
        "section": applications,
    },
    {
        "slug": "research-synthesis-release-and-reproduction-gate",
        "title": "Research synthesis release: expose the method and its limits",
        "summary": "Tie the final brief to a frozen search, study ledger, checked calculations, and review decision.",
        "definition": "A release-ready research brief has a traceable input set and a restrained output contract. Store the question, search or supplied-corpus snapshot, eligibility rules, included and excluded study IDs with reasons, extraction records, calculation script and output, unresolved conflicts, review notes, and final text revision. Before release, verify every number and design label against its report anchor, and check that the brief includes contrary findings and missing evidence. Use a label matching the actual process: a limited evidence packet is a limited evidence packet. Do not call it an exhaustive or systematic review if discovery and screening were not performed to that standard. If the brief could drive a consequential operational decision, route it to the accountable reviewer rather than turning the generated recommendation into an automatic effect.",
        "case": "The parcel operator's final packet contains ST-47 and ST-88 as controlled line trials and ST-61 as context. It reports the observed -7.5 and +2.5 point differences separately. The first draft says the scan panel 'has been proven to reduce misroutes' and omits ST-88. The release gate blocks it. The corrected brief says the two controlled results disagree, the changed-shift report cannot settle that disagreement, and additional line trials with specified allocation and missing-outcome reporting would narrow uncertainty. An operations owner reviews any proposed rollout. The published brief's dataset revision, script output, and text hash match the reviewed packet.",
        "sample": "Input: frozen packet RS-214; include ST-47, ST-88; context ST-61.\nChecked arithmetic: -7.5 and +2.5 percentage points.\nFinal claim: controlled results disagree; no pooled effect claimed.\nGate: contrary result present, exclusions logged, owner review recorded.\nRelease: reviewed text and input revision match distributed artifact.",
        "cost": "For K included studies and C public claims, a direct evidence audit is O(K+C) when records and anchors are indexed, plus the time needed to inspect disputed passages. Re-running a deterministic calculation is cheap compared with locating a changed report or adjudicating an exclusion. A frozen input set makes revisions reproducible; a new search date requires a new packet and review. If the model rewrites the summary after approval, compare the exact new text against the approved version rather than assuming the earlier check carries forward.",
        "mistakes": ["Do not describe a limited supplied packet as an exhaustive review.", "Do not release a summary that hides a contrary trial.", "Do not automate a rollout from an unreviewed generated synthesis."],
        "related": ["prompt-engineering/prompt-release-artifact-bundle", "prompt-engineering/time-sensitive-research-contract", "prompt-engineering/high-impact-advice-review-gate"],
        "section": production,
    },
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]).intersection(lookup)
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: synthesize conflicting parcel-scan trials"
titles[quiz_path] = "Research-synthesis prompt decisions"


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
                 difficulty="Advanced", tags=["prompt engineering", "research synthesis"],
                 sort_order=29500 + order, status="published", published_at=stamp,
                 created_at=stamp, updated_at=stamp)
    entry["data"].update(kind=kind, reading_minutes=11 if kind == "tutorial" else 19,
                         author_path="authors/aitrove-editorial", subject_root=subject_root,
                         section_path=section, content_format="html", seo_ready=True,
                         related=related(connections))
    return entry


effect_checker = '''studies = [
    {"id": "ST-47", "control_events": 48, "control_total": 240,
     "candidate_events": 30, "candidate_total": 240},
    {"id": "ST-88", "control_events": 18, "control_total": 120,
     "candidate_events": 21, "candidate_total": 120},
]

for study in studies:
    control_events = study["control_events"]
    control_total = study["control_total"]
    candidate_events = study["candidate_events"]
    candidate_total = study["candidate_total"]
    if not all(type(value) is int for value in (
        control_events, control_total, candidate_events, candidate_total
    )) or not (0 <= control_events <= control_total and control_total > 0
              and 0 <= candidate_events <= candidate_total and candidate_total > 0):
        raise ValueError(f"invalid event counts: {study['id']}")
    difference_points = 100 * (
        candidate_events / candidate_total - control_events / control_total
    )
    print(f"{study['id']}: {difference_points:+.2f} percentage points")
'''

new_rows = []
for index, (path, spec) in enumerate(zip(paths, specs)):
    connections = [spec["section"], subject_root] + spec["related"] + [peer for peer in paths if peer != path] + [project_path, quiz_path]
    code_language = "python" if index == 2 else "text"
    code = effect_checker if index == 2 else spec["sample"]
    body = ("<p>" + html.escape(spec["definition"]) + "</p>"
            + "<h2>Operational case</h2><p>" + html.escape(spec["case"]) + "</p>"
            + f'<pre><code class="language-{code_language}">' + html.escape(code, quote=False) + "</code></pre>"
            + "<h2>Performance and operating cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
            + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(mistake) + "</li>" for mistake in spec["mistakes"]) + "</ul>"
            + "<h2>Connected lessons</h2>" + links(connections))
    new_rows.append(article(path, spec["title"], spec["summary"], body, spec["section"], index * 10, connections))

project_connections = paths + ["prompt-engineering/evidence-bound-report-summary", "prompt-engineering/document-page-anchor-and-field-conflict", "prompt-engineering/prompt-release-review-packet", quiz_path]
project_body = (
    "<p>Draft a bounded evidence brief about a fictional scan-confirmation panel on staffed parcel sorting lines. The approved packet RS-214 contains controlled trials ST-47 and ST-88, observational changed-shift report ST-61, and a duplicate conference summary of ST-47. The primary outcome is misrouted parcels divided by allocated parcels over a full shift. The brief must describe what the packet shows, not decide a rollout.</p>"
    "<h2>Screen and extract</h2><p>Write eligibility rules before opening outcome counts: controlled line trials enter the primary comparison, simulator exercises are excluded, and changed-shift observations remain context. Record report versions and inclusion reasons. Link the conference summary to ST-47 rather than counting it twice. Extract numerator, denominator, time point, design, missing-outcome status, and result anchor for both controlled trials. Mark unstated methods unknown. Do not turn ST-61 into a controlled trial because its result is attractive.</p>"
    "<h2>Calculate and write the brief</h2><p>ST-47 has 48/240 control misroutes and 30/240 candidate misroutes: 20.0% versus 12.5%, a candidate-minus-control difference of -7.5 percentage points. ST-88 has 18/120 and 21/120: 15.0% versus 17.5%, a +2.5-point difference. Run the deterministic arithmetic check; it produces no uncertainty interval. Keep both outcomes in the brief. Explain that route mix differs in ST-61 and that the packet does not establish why the controlled trials disagree. Request allocation and missing-outcome details before stronger interpretation. An operations owner reviews any proposed rollout separately.</p>"
    '<pre><code class="language-text">RS-214: controlled ST-47 and ST-88; context ST-61.\nST-47: 48/240 vs 30/240; candidate-control = -7.5 points.\nST-88: 18/120 vs 21/120; candidate-control = +2.5 points.\nDo not count the ST-47 conference report as another trial.\nFinal: trial results disagree; no pooled effect or rollout authorization.</code></pre>'
    "<h2>Performance and operating cost</h2><p>Screening S reports is O(S) initial decisions, while verifying K extracted studies requires attention to methods and result anchors. The calculation is O(K) with constant extra space per study, but it does not replace a design or uncertainty analysis. Maintain the frozen packet, inclusion ledger, extraction rows, code output, reviewer notes, and final text revision. The exact approved brief is the release artifact; a later rewrite gets a new review.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not remove ST-88 to make the story consistent.</li><li>Do not treat a repeated ST-47 report as an independent trial.</li><li>Do not present point differences as proof of a general effect.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Screen, extract, calculate, and review a fictional packet with conflicting line-trial outcomes.", project_body, projects, 60, project_connections, kind="project"))

questions = [
    ("When should study eligibility rules be fixed?", "Before inspecting attractive or contrary results", "After choosing a preferred result", "Only after writing the brief", "Predeclared rules reduce result-driven selection."),
    ("Which records enter this packet's primary comparison?", "Controlled line trials ST-47 and ST-88", "Only the favorable trial", "ST-61 and the duplicate summary", "The controlled line trials match the declared design rule."),
    ("How should the ST-47 conference summary be counted?", "As a report of ST-47, not another study", "As an independent trial", "As a replacement for all counts", "One cohort can have several reports."),
    ("A denominator is absent from a report. What should extraction return?", "Unknown, with a review flag", "An inferred nearby number", "A model confidence score", "Do not invent event counts."),
    ("ST-47 has 48/240 control and 30/240 candidate events. What is candidate minus control?", "-7.5 percentage points", "-7.5 percent relative change", "+7.5 percentage points", "12.5% minus 20.0% is -7.5 points."),
    ("ST-88 has 18/120 control and 21/120 candidate events. What is the difference?", "+2.5 percentage points", "-2.5 percentage points", "+3 events per 100 parcels", "17.5% minus 15.0% is +2.5 points."),
    ("Does the effect-checking script compute a confidence interval?", "No; it validates counts and prints point differences", "Yes, from two rates alone", "Yes, whenever output has decimals", "Uncertainty needs a separate method."),
    ("Can ST-61 settle the disagreement between the controlled trials?", "No; its route mix changed between shifts", "Yes, because it is favorable", "Yes, because it has a study ID", "The observational comparison has a different design."),
    ("Two controlled results point in opposite directions. What should synthesis do?", "Report both and examine design and outcome differences", "Average them without a plan", "Drop the smaller trial silently", "Contradictions are part of the evidence."),
    ("What label fits a few supplied reports without a full search?", "A limited evidence packet", "An exhaustive systematic review", "A final causal proof", "Describe only the process actually performed."),
    ("What belongs in the release packet?", "Eligibility ledger, extraction, checked code output, review, exact text", "Only the final paragraph", "Only the favorable study", "A reviewer needs the path from inputs to claims."),
    ("Who decides a consequential rollout after the brief?", "The accountable operations owner after review", "The generated summary automatically", "The most favorable trial alone", "The prompt does not authorize operational change."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-multimodal-evidence"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                  path=quiz_path, title=titles[quiz_path],
                  summary="Test eligibility, extraction, denominators, conflicting designs, and release claims.",
                  body="<p>Choose the step that keeps a generated research brief faithful to its evidence packet.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, production, quizzes]),
                  sort_order=29570, status="published", published_at=stamp,
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
    (applications, paths[:4], "Research evidence and study results", "Predeclare eligibility, extract exact results, calculate effects, and preserve disagreements."),
    (production, paths[4:], "Research brief release gate", "Tie the final claim to the frozen packet, exclusions, calculations, and reviewer."),
    (projects, [project_path], "Conflicting parcel-scan trials", "Make a bounded brief from two opposed trials and one observational report."),
    (quizzes, [quiz_path], "Research synthesis decisions", "Test selection, event rates, design differences, and release wording."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

root_hub = lookup[subject_root]
root_hub["body"] += "<h2>Experimental-evidence synthesis</h2><p>Freeze eligibility, extract study-level outcomes, verify arithmetic, and keep conflicting designs visible.</p>" + links(paths + [project_path, quiz_path])
root_hub["updated_at"] = stamp

backlinks = {
    "prompt-engineering/time-sensitive-research-contract": paths[0],
    "prompt-engineering/evidence-bound-report-summary": paths[3],
    "prompt-engineering/document-page-anchor-and-field-conflict": paths[1],
    "prompt-engineering/deterministic-calculation-gates": paths[2],
    "prompt-engineering/aggregate-denominator-reconciliation": paths[2],
    "prompt-engineering/retrieval-freshness-and-conflict": paths[3],
    "prompt-engineering/prompt-release-review-packet": paths[4],
    "prompt-engineering/high-impact-advice-review-gate": paths[4],
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
