"""Add executable Prompt Engineering evaluation labs and connected practice."""

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
production = "prompt-engineering/production"
quizzes = "prompt-engineering/quizzes"
quiz_path = "quizzes/prompt-engineering-evaluation-labs"

labs = [
    {
        "slug": "evidence-reference-checker",
        "title": "Code lab: reject unknown evidence IDs",
        "summary": "Check generated evidence references against the authorized records for this request.",
        "definition": "An evidence-reference check verifies that every record ID attached to a generated decision belongs to the current authorized evidence bundle. It is a structural gate, not a proof that the cited passage supports the decision. Keep that distinction explicit. A policy ID retrieved for another account or an expired version may be real yet still outside this request's permitted set. Build the set after authorization and version filtering, then validate the output before a final decision reaches a downstream system.",
        "case": "A claims assistant receives policy record POL-47 and receipt RC-83 for case CL-291. The first response cites both records and passes the reference gate. The second cites a plausible but absent receipt RC-99, so it is rejected even though the prose sounds confident. A separate reviewer still has to check whether POL-47 actually authorizes the requested outcome. If a record changes between retrieval and review, pin the evidence version or rerun the check against the new bundle.",
        "code": '''allowed_evidence_ids = {"POL-47", "RC-83"}
responses = [
    {"case_id": "CL-291", "decision": "approve", "evidence_ids": ["POL-47", "RC-83"]},
    {"case_id": "CL-292", "decision": "approve", "evidence_ids": ["POL-47", "RC-99"]},
]

for response in responses:
    cited_ids = set(response["evidence_ids"])
    unknown_ids = cited_ids - allowed_evidence_ids
    valid = bool(cited_ids) and not unknown_ids
    print(f"{response['case_id']}: {'pass' if valid else 'reject'}")
''',
        "expected": "CL-291: pass\nCL-292: reject\n",
        "cost": "Converting citations to a set and comparing them with the already-built allowed set takes O(C) expected time and O(C) extra space for C cited IDs. Building the allowed set from E records takes O(E) time and space. This check is cheap relative to retrieval or model generation, but it cannot establish semantic support. Test duplicate IDs, empty citations, stale versions, and records from a different tenant. Keep the actual evidence text and access decision available for a later claim-level review.",
        "mistakes": ["Do not treat an existing ID as proof that the cited claim is true.", "Do not build the allowed set before tenant and version filtering.", "Do not allow a final decision with an empty evidence list."],
        "related": ["prompt-engineering/evidence-id-traceability", "prompt-engineering/retrieval-freshness-and-conflict"],
    },
    {
        "slug": "abstention-slice-scorer",
        "title": "Code lab: score answered cases and abstentions",
        "summary": "Report coverage and errors by case slice, with critical mistakes visible.",
        "definition": "An abstention score must show how often the system answers and how often those answers are wrong. A model that sends every case to review has no answered-case errors but provides no useful coverage. Score by operational slice rather than collapsing low-risk and high-risk cases into a single average. Freeze expected labels before evaluating a candidate prompt, and keep the examples out of the prompt itself. Here, the label review means the system withheld a final decision.",
        "case": "A claims team tests five held-out cases. Two routine cases receive correct final labels. Two high-impact cases include one wrong approval and one deliberate review. A third routine case is also withheld because its receipt date is missing. A single accuracy percentage would conceal the unsupported high-impact approval. The release conversation needs answered counts, wrong answered counts, and withheld counts for each slice, with the critical error called out separately.",
        "code": '''cases = [
    {"id": "CL-301", "slice": "routine", "expected": "approve", "actual": "approve"},
    {"id": "CL-302", "slice": "routine", "expected": "deny", "actual": "deny"},
    {"id": "CL-303", "slice": "routine", "expected": "deny", "actual": "review"},
    {"id": "CL-304", "slice": "high-impact", "expected": "deny", "actual": "approve"},
    {"id": "CL-305", "slice": "high-impact", "expected": "deny", "actual": "review"},
]

for case_slice in ("routine", "high-impact"):
    selected = [case for case in cases if case["slice"] == case_slice]
    answered = [case for case in selected if case["actual"] != "review"]
    wrong = [case for case in answered if case["actual"] != case["expected"]]
    print(f"{case_slice}: answered={len(answered)}/{len(selected)} wrong={len(wrong)}")
''',
        "expected": "routine: answered=2/3 wrong=0\nhigh-impact: answered=1/2 wrong=1\n",
        "cost": "The simple implementation scans the N cases once per slice, so S slices cost O(SN) time and O(N) temporary space in the largest pass. Grouping cases in one pass can reduce time to O(N + S) when the dataset grows. The computational cost is minor; labeling and adjudicating cases usually dominate. Report raw counts alongside rates because a zero in a tiny slice is weak evidence. An expected review label needs a separate policy for whether withholding was correct; this sample measures coverage and wrong final decisions only.",
        "mistakes": ["Do not report an error rate without the answered share.", "Do not combine high-impact and routine errors into one release threshold.", "Do not call a withheld case correct merely because it avoided a wrong answer."],
        "related": ["prompt-engineering/selective-prediction-thresholds", "prompt-engineering/evaluation-slice-design"],
    },
    {
        "slug": "judge-order-audit",
        "title": "Code lab: find pairwise judge order changes",
        "summary": "Normalize candidate identities and flag verdicts that change after order reversal.",
        "definition": "A pairwise judge order audit compares a judge's preference for two fixed candidate responses after their presentation order is swapped. Record verdicts using stable candidate IDs, not first or second position. If the normalized winner changes, presentation order may be influencing the judgment. A changed verdict is a signal for review, not a calibrated estimate of bias from a few examples. Human adjudication should examine the rubric and the original responses.",
        "case": "A support team compares prompt candidate A with candidate B on three tickets. For ticket TK-481, A wins in either presentation order. For TK-482, the winner changes from B to A after the swap. The third case ties twice. The team sends TK-482 to an independent reviewer and checks whether the rubric rewards the right behavior. They keep both judge calls and the response text; a single retained score would hide the order effect.",
        "code": '''pairwise_reviews = [
    {"ticket_id": "TK-481", "winner_ab": "A", "winner_ba": "A"},
    {"ticket_id": "TK-482", "winner_ab": "B", "winner_ba": "A"},
    {"ticket_id": "TK-483", "winner_ab": "tie", "winner_ba": "tie"},
]

changed = [
    review["ticket_id"]
    for review in pairwise_reviews
    if review["winner_ab"] != review["winner_ba"]
]
print("changed:", ", ".join(changed) if changed else "none")
''',
        "expected": "changed: TK-482\n",
        "cost": "The comparison is O(N) time for N paired cases and O(F) space for F flagged case IDs. The expensive work is obtaining two judge calls per case and adjudicating disagreements. If a judge is stochastic, repeat each order before drawing a strong conclusion, then compare disagreement patterns by task slice. Pin the rubric and candidate responses during the audit. A tie in one order and a preference in the other is also a changed verdict worth review.",
        "mistakes": ["Do not record the winning screen position as the candidate identity.", "Do not discard the reversed-order judgment after averaging scores.", "Do not treat one changed verdict as a population-level bias estimate."],
        "related": ["prompt-engineering/judge-calibration-and-order-bias", "prompt-engineering/metamorphic-prompt-tests"],
    },
    {
        "slug": "release-regression-gate",
        "title": "Code lab: block a critical prompt regression",
        "summary": "Replay frozen cases and reject a candidate that breaks a high-impact invariant.",
        "definition": "A prompt release gate compares a candidate version against frozen cases and blocks it when a critical invariant fails, even if aggregate output looks better. Keep a baseline result for diagnosis and a labeled expected outcome for the gate. Run the same input and evidence versions for both candidates; otherwise the comparison mixes prompt effects with data changes. The gate below checks final labels on critical cases and reports any changed result for review.",
        "case": "A claims prompt revision fixes several routine explanations but changes CL-411 from deny to approve despite an expired receipt. The baseline and candidate are replayed against the same policy snapshot. The release is blocked because the critical case is wrong. A second changed case, CL-412, remains review and needs no final-decision override. The team records the candidate version, failing case, and evidence snapshot so the author can make a targeted repair before the next run.",
        "code": '''frozen_cases = [
    {"id": "CL-411", "critical": True, "expected": "deny", "baseline": "deny", "candidate": "approve"},
    {"id": "CL-412", "critical": True, "expected": "review", "baseline": "review", "candidate": "review"},
    {"id": "CL-413", "critical": False, "expected": "approve", "baseline": "review", "candidate": "approve"},
]

critical_failures = [
    case["id"] for case in frozen_cases
    if case["critical"] and case["candidate"] != case["expected"]
]
changed_cases = [
    case["id"] for case in frozen_cases
    if case["candidate"] != case["baseline"]
]
print("release:", "block" if critical_failures else "allow")
print("critical_failures:", ", ".join(critical_failures) or "none")
print("changed_cases:", ", ".join(changed_cases) or "none")
''',
        "expected": "release: block\ncritical_failures: CL-411\nchanged_cases: CL-411, CL-413\n",
        "cost": "A single replay comparison is O(N) time and O(N) worst-case space for the two result lists. Model calls, not list scans, dominate release cost; comparing both versions doubles calls when baseline outputs were not stored. Preserve sampled responses and model settings with the case snapshot. The critical gate is necessary but insufficient: check privacy, unauthorized tool effects, latency, and slice coverage separately. A release set that was used to write the prompt no longer gives an independent estimate.",
        "mistakes": ["Do not promote on aggregate gains while a critical case fails.", "Do not compare different evidence snapshots as if only the prompt changed.", "Do not reuse a tuned development case as the sole release holdout."],
        "related": ["prompt-engineering/prompt-version-rollout", "prompt-engineering/evaluation-data-leakage"],
    },
]

for lab in labs:
    lab["path"] = "prompt-engineering/" + lab["slug"]
new_paths = {quiz_path} | {lab["path"] for lab in labs}
assert not new_paths.intersection(lookup), "lab route already exists"
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({lab["path"]: lab["title"] for lab in labs})
titles[quiz_path] = "Prompt evaluation code labs"


def link(path):
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(paths):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(paths)) + "</ul>"


def related(paths):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(paths)]


article_template = lookup["prompt-engineering/evaluation-slice-design"]
new_rows = []
for index, lab in enumerate(labs):
    neighbors = [other["path"] for other in labs if other["path"] != lab["path"]]
    connections = [production, subject_root] + lab["related"] + neighbors + [quiz_path]
    body = (
        "<p>" + html.escape(lab["definition"]) + "</p>"
        "<h2>Decision in practice</h2><p>" + html.escape(lab["case"]) + "</p>"
        '<pre><code class="language-python">' + html.escape(lab["code"], quote=False) + "</code></pre>"
        "<p><strong>Expected output:</strong> " + html.escape(lab["expected"].strip().replace("\n", "; ")) + "</p>"
        "<h2>Performance and operating cost</h2><p>" + html.escape(lab["cost"]) + "</p>"
        "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in lab["mistakes"]) + "</ul>"
        "<h2>Connected lessons</h2>" + links(connections)
    )
    entry = copy.deepcopy(article_template)
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + lab["path"])),
                 path=lab["path"], title=lab["title"], summary=lab["summary"],
                 body=body, subject="prompt-engineering-production", difficulty="Advanced",
                 tags=["prompt engineering", "evaluation", "python"], sort_order=25700 + index * 10,
                 status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
    entry["data"].update(kind="tutorial", reading_minutes=9, author_path="authors/aitrove-editorial",
                         subject_root=subject_root, section_path=production,
                         content_format="html", seo_ready=True, related=related(connections))
    new_rows.append(entry)

quiz_questions = [
    ("A response cites an ID that is absent from this request's allowed bundle. What should the gate do?", "Reject the response before a final decision", "Accept it if the ID looks plausible", "Ask the model to invent a replacement", 0, "An unknown reference has no authorized record in this request."),
    ("A cited record ID exists. What remains unproven?", "Whether its passage supports the claim", "Whether the string can be parsed", "Whether the response has a case ID", 0, "Reference membership is only a structural check."),
    ("Which set should the evidence checker use?", "Records filtered for the current request and version", "Every ID ever stored", "IDs from the model's previous answer", 0, "Scope and version determine which records are permitted."),
    ("A system withholds every case. Which metric exposes the problem?", "Answered share", "Wrong answered count alone", "Average response length", 0, "Zero answered-case errors can coexist with zero coverage."),
    ("The high-impact slice has one wrong approval among one answered case. What should the report show?", "The raw count and the answered denominator", "Only the overall average", "Only the withheld count", 0, "The small slice and its critical error must remain visible."),
    ("What does review mean in the sample scorer?", "No final decision was issued", "The decision was automatically correct", "The answer was approved by a person", 0, "The sample uses review as an abstention label."),
    ("Why store a judge winner as candidate A or B?", "Identity stays stable after presentation order swaps", "Position is always accurate", "It reduces model token usage", 0, "First and second positions reverse; candidate identities do not."),
    ("A pairwise judge picks B in A/B order and A in B/A order. What next?", "Flag the case for rubric and response review", "Average the labels as a tie", "Discard the reversed call", 0, "The normalized winner changed across orderings."),
    ("A judge produces a tie in one order and a preference in the other. How is it classified?", "Changed verdict", "Stable verdict", "Missing data", 0, "The outcome changed and deserves review."),
    ("A candidate improves routine cases but fails a critical frozen case. What is the release result?", "Block the release", "Promote on aggregate gain", "Delete the critical case", 0, "A critical invariant is a hard release gate."),
    ("Why pin the evidence snapshot for baseline and candidate replay?", "To isolate the prompt change from data changes", "To guarantee identical model text", "To remove the need for labels", 0, "Different evidence would confound the comparison."),
    ("A case used to tune the prompt is the only release test. What is missing?", "An independent holdout", "A longer prompt", "A prettier score report", 0, "A tuned case cannot supply an independent final check."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-applied-decisions"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                  path=quiz_path, title=titles[quiz_path],
                  summary="Interpret executable evidence, abstention, judge-order, and release checks.",
                  body="<p>Read the four code labs, then choose the operational response each result requires. The questions focus on what a check proves and where human review still matters.</p><h2>Code labs</h2>" + links([lab["path"] for lab in labs]) + "<h2>Related practice</h2>" + links([production, quizzes, subject_root]),
                  sort_order=26070, status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
quiz_entry["data"].update(subject_root=subject_root, section_path=quizzes, content_format="html",
                          author_path="authors/aitrove-editorial", seo_ready=True, duration_minutes=12,
                          related=related([lab["path"] for lab in labs] + [production, quizzes]),
                          questions=[{"prompt": question, "options": ([a, b, c][index % 3:] + [a, b, c][:index % 3]),
                                      "answer": (answer - index) % 3, "explanation": explanation}
                                     for index, (question, a, b, c, answer, explanation) in enumerate(quiz_questions)])
new_rows.append(quiz_entry)

production_hub = lookup[production]
production_hub["data"]["modules"].append({
    "title": "Executable evaluation labs",
    "summary": "Run small deterministic checks before interpreting model output or promoting a prompt.",
    "lessons": [lab["path"] for lab in labs],
})
production_hub["body"] += "<h2>Executable evaluation labs</h2><p>Use these short programs to check evidence references, abstention, judge consistency, and critical release cases. A passing structural check still needs semantic review where the claim depends on a passage.</p>" + links([lab["path"] for lab in labs] + [quiz_path])
production_hub["updated_at"] = stamp

quiz_hub = lookup[quizzes]
quiz_hub["data"]["modules"].append({
    "title": "Evaluation code labs",
    "summary": "Interpret the output of small executable prompt checks.",
    "lessons": [quiz_path],
})
quiz_hub["body"] += "<h2>Evaluation code lab quiz</h2>" + links([quiz_path] + [lab["path"] for lab in labs])
quiz_hub["updated_at"] = stamp

root_hub = lookup[subject_root]
root_hub["body"] += "<h2>Run the evaluation checks</h2><p>The production code labs exercise four separate gates. Start with the reference checker, then score decisions, inspect judge order, and replay a release.</p>" + links([lab["path"] for lab in labs] + [quiz_path])
root_hub["updated_at"] = stamp

backlinks = {
    "prompt-engineering/evidence-id-traceability": labs[0]["path"],
    "prompt-engineering/selective-prediction-thresholds": labs[1]["path"],
    "prompt-engineering/judge-calibration-and-order-bias": labs[2]["path"],
    "prompt-engineering/prompt-version-rollout": labs[3]["path"],
}
for existing_path, new_path in backlinks.items():
    entry = lookup[existing_path]
    entry["body"] += "<p><strong>Try the executable check:</strong> " + link(new_path) + ".</p>"
    entry["data"]["related"] = related([item["path"] for item in entry["data"]["related"]] + [new_path])
    entry["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newArticles": len(labs), "newQuizzes": 1, "newPaths": sorted(new_paths)}))
