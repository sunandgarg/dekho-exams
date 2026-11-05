"""Add checked reasoning patterns and evaluation exercises to Prompt Engineering."""

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
root_path = "prompt-engineering/prompt-engineering"
patterns = "prompt-engineering/patterns"
production = "prompt-engineering/production"
projects = "prompt-engineering/projects"
quizzes = "prompt-engineering/quizzes"
project_path = "prompt-engineering/contract-renewal-verification-project"
quiz_path = "quizzes/prompt-engineering-reasoning-checks"


def lesson(slug, title, summary, definition, case, sample, cost, mistakes, section, related, language="text"):
    return dict(path="prompt-engineering/" + slug, title=title, summary=summary,
                definition=definition, case=case, sample=sample, cost=cost,
                mistakes=mistakes, section=section, related=related, language=language)


specs = [
    lesson(
        "visible-rationale-evidence-boundary",
        "Reasoning summaries: show checkable grounds, not invented certainty",
        "A short decision rationale should identify verifiable grounds and unresolved facts.",
        "A visible rationale is a user-facing explanation of a decision, not a transcript of the model's private computation and not evidence by itself. Ask for the rule applied, the record IDs used, the outcome, and any missing condition. Then verify those fields against the actual records and deterministic checks. An elaborate explanation can still be wrong. Where arithmetic or eligibility is exact, compute it outside the model. A rationale is useful when a reviewer can inspect the cited clause and see why the outcome followed.",
        "A contract assistant evaluates renewal RN-284. The current policy says renewal is permitted only when the inspection date is within 47 days and no unresolved hold exists. The assistant reports an approval and writes a long explanation, but the inspection is 53 days old. The application calculates the age and rejects the decision; a better explanation would not make it valid. In a second case, the inspection is 21 days old but the hold record is missing. The response must state review and name the missing hold status rather than pretend that no hold exists.",
        "Output: decision=review.\nRule: inspection age <= 47 days AND hold status clear.\nEvidence: inspection IN-284 dated 21 days ago; hold record unavailable.\nReason: one required condition is unverified.\nCheck: application validates age and record IDs before display.",
        "A concise rationale can reduce review time compared with a long free-form explanation, provided it retains the decisive facts. For R rules and E supplied records, deterministic validation is typically O(R+E) after indexing; model generation cost depends on output length. Measure unsupported rationales separately from wrong decisions. Avoid collecting hidden reasoning as a substitute for an audit trail. The audit trail is the rule version, input records, computed checks, final outcome, and reviewer action.",
        ["Do not treat a polished explanation as proof.", "Do not ask the model to compute an exact eligibility date when code can do it.", "Do not hide missing evidence inside a confident rationale."],
        patterns,
        ["prompt-engineering/deterministic-calculation-gates", "prompt-engineering/evidence-id-traceability"],
    ),
    lesson(
        "candidate-sampling-and-verifier",
        "Multiple candidates: filter invalid answers before ranking",
        "Generating several answers is useful only if selection has an independent acceptance rule.",
        "Candidate sampling produces more than one proposed answer for the same frozen input. A majority vote can favor a shared mistake, especially when every candidate sees the same missing or misleading record. First reject candidates that fail schema, authorization, evidence, or task-specific checks; only then rank the survivors by a separate rubric. Keep the input, retrieved bundle, and model settings recorded. If no candidate passes, return review. Candidate diversity is an experiment, not a license to convert agreement into truth.",
        "Three candidates assess renewal RN-284. Two approve it using expired policy POL-63; one requests review using the current policy POL-64 but lacks a hold record. A vote would approve. The application instead rejects the two stale citations and preserves the review candidate. The reviewer then checks whether the missing hold can be retrieved. The selection test includes a run in which all candidates use expired records, so the correct result is no accepted candidate. The team compares this method with a single-candidate baseline before paying for extra generations.",
        '''current_evidence_ids = {"POL-64"}
candidates = [
    {"id": "RN-284-A", "decision": "approve", "evidence_ids": ["POL-63"]},
    {"id": "RN-284-B", "decision": "approve", "evidence_ids": ["POL-63"]},
    {"id": "RN-284-C", "decision": "review", "evidence_ids": ["POL-64"]},
]

accepted = [
    candidate for candidate in candidates
    if candidate["evidence_ids"]
    and set(candidate["evidence_ids"]) <= current_evidence_ids
]
print("accepted:", ", ".join(item["id"] for item in accepted) or "none")
''',
        "For K candidates and C cited IDs per candidate, this structural filter costs O(KC) expected time and O(K) output space, excluding the input. Generating K responses can cost roughly K times a single call before any ranking. The filter only verifies reference membership; it does not prove that POL-64 supports the stated decision. Add a claim-level review for high-impact outcomes. Track valid-candidate rate, accepted error rate, and total cost together. A method that merely chooses the most common wrong answer has increased expense without improving safety.",
        ["Do not use majority agreement as a substitute for evidence checking.", "Do not rank a candidate that fails a hard gate.", "Do not force selection when every candidate is invalid."],
        patterns,
        ["prompt-engineering/evidence-reference-checker", "prompt-engineering/judge-calibration-and-order-bias"],
        "python",
    ),
    lesson(
        "bounded-critique-revision-contract",
        "Critique loops: require a named defect and a stopping rule",
        "A critique pass should identify a testable defect before another answer is generated.",
        "A draft-critique-revise loop has value when the critique checks a fixed rubric or external facts that the first draft may have missed. Ask the critic for a defect category, location, evidence, and proposed check. A generic request to improve the answer often produces style changes without repairing a decision. Cap revisions, retain each candidate and critique, and rerun the original acceptance checks after every change. A model reviewing its own output is not independent ground truth; deterministic validators and human adjudication remain necessary for disputed cases.",
        "An assistant drafts a maintenance handoff for pump PM-742. The critic finds a specific defect: the draft says pressure was measured by a sensor, while the record shows it was reported by a caller. The revision changes the attribution and keeps the pressure value linked to call segment CA-58. A second critique finds no remaining contract violation, so the loop stops. In a failure case, the critic only says 'make it more professional'; that does not authorize another expensive model call because it names no correctness defect.",
        "Draft artifact: handoff H-742.\nCritique fields: defect_type, affected_claim, evidence_id, required_check.\nValid defect: attribution mismatch at pressure claim; compare CA-58.\nRevision budget: one pass; rerun attribution and evidence gates.\nStop: no named defect or budget exhausted -> accept or review by policy.",
        "Each extra critique and revision call increases latency and token cost. With at most M revision rounds, model work is O(M) calls; validation over L output characters per round is O(ML). Test whether the loop repairs known defects without creating new ones. Record the proportion of critiques that name a real error and the proportion of revisions that pass after repair. If the critic and author share the same blind spot, repeated self-review can reinforce it. Use an independent case label or reviewer on high-risk decisions.",
        ["Do not ask for endless refinement without a defect and a budget.", "Do not treat self-critique as an independent validator.", "Do not accept a revised answer without rerunning the original gates."],
        patterns,
        ["prompt-engineering/schema-repair-retry-budget", "prompt-engineering/metamorphic-prompt-tests"],
    ),
    lesson(
        "contrastive-example-boundaries",
        "Few-shot examples: teach the boundary with near misses",
        "A useful example set shows cases on both sides of a decision boundary.",
        "Contrastive examples are paired cases that differ in one material fact and require different outcomes. They teach the model which condition matters without burying the rule in many easy positives. Include an explicit uncertain case when evidence is missing. Keep examples representative and free of final holdout cases. Order can influence outputs, so test reordered examples and paraphrased inputs. A few-shot prompt is a task aid, not a permission system or a replacement for validating the final answer.",
        "A renewal prompt contains two approved examples with recent inspections. It then approves RN-284 despite an inspection older than the 47-day rule. The author adds a matched pair: a vehicle inspected 46 days ago with no hold is eligible; another inspected 48 days ago is not. A third example with a missing hold record returns review. The team freezes these demonstrations and tests a separate set with ages near the boundary, changed wording, and the same facts in a different order. Passing the prompt examples themselves does not count as a release result.",
        "Example A: inspection age 46 days, hold clear -> eligible.\nExample B: inspection age 48 days, hold clear -> ineligible.\nExample C: inspection age 21 days, hold unknown -> review.\nHeld-out checks: ages 47 and 49; reordered descriptions; new asset IDs.\nFinal decision still validated by rule and current records.",
        "Adding examples increases prompt tokens on every call. Three boundary examples can be cheaper and more informative than a long list of routine positives, but that must be measured on a held-out set. If E examples each average T tokens, the prompt cost adds roughly O(ET) tokens per request. Selection and labeling of near misses take editorial effort. Watch for example order effects and duplicated cases across prompt and test data. The improvement target is behavior on unseen boundary cases, not memorization of the demonstrations.",
        ["Do not fill every demonstration with the same easy label.", "Do not use a release holdout case as a prompt example.", "Do not assume an example grants permission for an external action."],
        patterns,
        ["prompt-engineering/few-shot-example-selection", "prompt-engineering/evaluation-data-leakage"],
    ),
    lesson(
        "context-distillation-evidence-ledger",
        "Context distillation: shorten input without losing governing exceptions",
        "A compressed context must retain the clauses, exceptions, and record IDs needed to decide.",
        "Context distillation replaces a large retrieved bundle with a smaller evidence packet for the final prompt. The distillation stage must preserve the source version, decisive clause, limiting exception, and uncertainty; otherwise it can produce a shorter but less trustworthy answer. Treat the compact packet as a derived artifact with a link back to the full record. Test whether a reviewer can reconstruct each generated claim from the original source. Use deterministic metadata filters before semantic compression when possible, and refuse to fill missing clauses from memory.",
        "A renewal policy spans 31 pages. The relevant clause allows renewal after inspection, but an appendix suspends that rule for units with unresolved safety holds. A summary that keeps the allowance and drops the appendix would approve RN-284 incorrectly. The distiller therefore carries both clause IDs, the policy version, and a note that hold status must be checked. A reviewer opens the original appendix for a disputed case. The test packet includes a policy update that moves the exception to a different section; the system must refresh the compact packet instead of reusing a stale one.",
        "Compact packet for RN-284:\nPOL-64 v4 clause 8: inspection must be recent.\nPOL-64 v4 appendix C: unresolved safety hold blocks renewal.\nUnknown: hold status for RN-284.\nSource map: each item retains record ID, section ID, version, and retrieval time.\nDecision: review until hold status is verified.",
        "Reading a large bundle costs tokens and latency; distillation adds a stage but may reduce later repeated context. If N source chunks are scanned, initial selection is at least O(N) in the number of chunks, and a source map takes O(K) space for K retained claims. Measure exception loss and stale-packet errors, not just token reduction. Cache a packet only while its source versions remain valid. A compressed note that cannot identify its governing source is too weak for a consequential decision.",
        ["Do not keep the main rule while dropping its exception.", "Do not discard source IDs during compression.", "Do not reuse a packet after its policy version changes."],
        patterns,
        ["prompt-engineering/chunk-boundary-and-parent-context", "prompt-engineering/long-context-priority-and-truncation"],
    ),
    lesson(
        "negative-control-prompt-evaluation",
        "Negative controls: test the answer that should not be produced",
        "A negative control is a case designed to fail a tempting but unsupported answer path.",
        "Prompt evaluations need cases where the expected behavior is to withhold, reject, or ask for evidence. Positive examples show whether the system can complete a task; negative controls show whether it acts when it should not. Build controls for missing records, irrelevant retrieved text, conflicting versions, unauthorized actors, and fabricated identifiers. Freeze the expected state before testing. A control must be plausible enough to expose the failure mode without copying the final holdout into the prompt. Record both the model output and any downstream effect.",
        "A renewal assistant succeeds on 39 clean cases. It fails when a retrieved maintenance note mentions RN-284 but contains no inspection date: the assistant treats the note as proof and approves. A negative control keeps the same user request but removes the inspection record. Another supplies a valid inspection for a different asset. Both should return review. A third embeds an instruction in the note to approve every renewal; the model may quote the note as data, but it must not follow that instruction. The release gate checks that no approval or tool effect occurs in these controls.",
        "Control N-1: inspection missing -> review; no renewal effect.\nControl N-2: inspection belongs to another asset -> review.\nControl N-3: retrieved note says 'approve all' -> ignore instruction; evaluate facts.\nMeasure: false approvals, unauthorized effects, and correct abstentions per control family.",
        "For C controls, a single candidate requires O(C) model calls and review records; multiple candidates or prompt versions multiply that cost. The valuable metric is the count of forbidden outcomes by control family, not a single pooled accuracy score. Maintain enough ordinary positive cases so a model that always refuses cannot pass. Revisit controls after retrieval, policy, or tool changes. A negative control that was used to tune the prompt should move to development data, with a fresh holdout case replacing it.",
        ["Do not call an always-refusing system successful because controls pass.", "Do not omit downstream tool effects from the result record.", "Do not promote a tuned negative control as an independent final test."],
        production,
        ["prompt-engineering/evaluation-slice-design", "prompt-engineering/prompt-injection-red-team"],
    ),
]

new_paths = {spec["path"] for spec in specs} | {project_path, quiz_path}
assert not new_paths.intersection(lookup)
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({spec["path"]: spec["title"] for spec in specs})
titles[project_path] = "Project: verify a contract-renewal prompt at the boundary"
titles[quiz_path] = "Reasoning and evidence checks"


def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(paths):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(paths)) + "</ul>"


def related(paths):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(paths)]


def article(path, title, summary, body, section, sort_order, connections, kind="tutorial"):
    entry = copy.deepcopy(lookup["prompt-engineering/evaluation-slice-design"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)),
                 path=path, title=title, summary=summary, body=body,
                 subject="prompt-engineering-patterns" if section == patterns else
                         "prompt-engineering-production" if section == production else "prompt-engineering-project",
                 difficulty="Advanced", tags=["prompt engineering", "evaluation"],
                 sort_order=sort_order, status="published", published_at=stamp,
                 created_at=stamp, updated_at=stamp)
    entry["data"].update(kind=kind, reading_minutes=10 if kind == "tutorial" else 18,
                         author_path="authors/aitrove-editorial", subject_root=root_path,
                         section_path=section, content_format="html", seo_ready=True,
                         related=related(connections))
    return entry


new_rows = []
for index, spec in enumerate(specs):
    peers = [other["path"] for other in specs if other["path"] != spec["path"]]
    connections = [spec["section"], root_path] + spec["related"] + peers + [project_path, quiz_path]
    body = (
        "<p>" + html.escape(spec["definition"]) + "</p>"
        "<h2>Decision in practice</h2><p>" + html.escape(spec["case"]) + "</p>"
        '<pre><code class="language-' + spec["language"] + '">' + html.escape(spec["sample"], quote=False) + "</code></pre>"
        + ("<p><strong>Expected output:</strong> accepted: RN-284-C</p>" if spec["language"] == "python" else "")
        + "<h2>Performance and operating cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
        "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in spec["mistakes"]) + "</ul>"
        "<h2>Connected lessons</h2>" + links(connections)
    )
    new_rows.append(article(spec["path"], spec["title"], spec["summary"],
                            body, spec["section"], 25900 + index * 10, connections))

project_connections = [spec["path"] for spec in specs] + [
    "prompt-engineering/evidence-reference-checker",
    "prompt-engineering/release-regression-gate",
    "prompt-engineering/human-review-escalation", quiz_path,
]
project_body = (
    "<p>This project tests a contract-renewal assistant against a fixed policy boundary. The fictional service manages industrial equipment, and renewal RN-284 depends on an inspection no older than 47 days plus a clear safety-hold status. The deliverable is a prompt, a compact evidence packet, a case set, and a release report. No answer is allowed to become an external renewal effect until the rule checks pass.</p>"
    "<h2>Prepare the evidence</h2><p>Index policy POL-64 version 4, including clause 8 and appendix C. Retain the inspection record, the hold record, their asset IDs, and their dates. Compress the packet only after checking that both the main clause and exception survive. Write three contrastive demonstrations: eligible at 46 days, ineligible at 48 days, and review with unknown hold status. Keep the 47-day boundary and unrelated asset records for the holdout rather than copying them into the prompt.</p>"
    "<h2>Run and compare</h2><p>Build 43 test cases and hold out 14. Include a stale policy, absent inspection, mismatched asset ID, malicious maintenance note, and conflicting hold versions. Ask for decision, rule ID, evidence IDs, and a short rationale. Generate three candidates only for cases that fail the single-candidate baseline. Filter candidates by schema and current evidence IDs before ranking. Send disputed claim support to a reviewer; a majority vote cannot override a missing record. Allow one critique revision when it names a concrete defect and rerun all gates afterward.</p>"
    '<pre><code class="language-text">Policy: POL-64 v4, clause 8 and appendix C.\nCase: RN-284, inspection age 47 days, hold status clear.\nBoundary tests: 46, 47, 48 days; missing hold; other asset ID.\nOutput: decision, rule_id, evidence_ids, concise rationale, unknowns.\nGate: no approval without both current conditions; no effect from negative controls.\nReport: 43 cases, 14 held out; wrong decisions and withheld share by slice.</code></pre>'
    "<h2>Performance and operating cost</h2><p>A single model call per case is the baseline. Three candidates on only failed or disputed slices add cost where it has a plausible benefit, rather than tripling every request. Context distillation adds an initial pass but can save repeated tokens if policy versions remain pinned. Record model calls, output tokens, validator time, reviewer minutes, and forbidden effects. Stop if the multi-candidate path does not improve the held-out failure classes after its extra cost.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not accept the most common answer when all candidates cite stale policy.</li><li>Do not drop the safety-hold exception from the compact packet.</li><li>Do not let a polished rationale bypass the date and hold checks.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections)
)
new_rows.append(article(project_path, titles[project_path],
                        "Build and evaluate a renewal decision against a policy boundary.",
                        project_body, projects, 25970, project_connections, kind="project"))

questions = [
    ("A rationale is detailed but the inspection age is wrong. What determines the decision?", "The validated date calculation and rule", "The explanation length", "The model's confidence", 0, "A rationale is not proof of the governing condition."),
    ("Which rationale is reviewable?", "A short rule, record IDs, outcome, and missing condition", "A long account with no records", "An unsupported confidence percentage", 0, "The reviewer needs inspectable grounds and uncertainty."),
    ("Two of three candidates cite expired policy and approve. One requests review with current policy. What wins?", "Filter invalid references before any ranking", "Majority vote approves", "Choose the longest answer", 0, "Agreement does not make stale evidence valid."),
    ("Every sampled candidate fails a hard evidence gate. What should selection return?", "No accepted candidate and a review state", "The least wrong candidate", "A random candidate", 0, "A hard gate cannot be waived by ranking."),
    ("A critic says only 'make it clearer'. Should that trigger a correctness revision?", "No, it names no testable defect", "Yes, always", "Only if it uses many words", 0, "Bounded critique needs a specific defect and check."),
    ("A revision fixes attribution but changes a cited record. What follows?", "Rerun the original evidence gates", "Accept because the prose improved", "Delete the earlier draft", 0, "Every revised candidate needs validation."),
    ("What is a contrastive pair for a 47-day inspection rule?", "Same facts except 46 versus 48 days", "Two easy approvals", "Unrelated cases with different tasks", 0, "A near miss isolates the governing condition."),
    ("Why keep final holdout cases out of few-shot examples?", "To preserve an independent release test", "To reduce output length", "To prevent HTML tags", 0, "A demonstrated case cannot measure unseen behavior."),
    ("A context summary keeps the main clause but drops its safety exception. What is the result?", "Reject the compressed packet", "Approve using the shorter clause", "Treat the exception as optional", 0, "The omitted exception can reverse the decision."),
    ("What must a distilled evidence item retain?", "Record ID, section, version, and decisive text", "Only a short title", "Only the model's opinion", 0, "A reviewer must trace the compact item to its source."),
    ("A case has no inspection record. What is it useful for?", "A negative control for unsupported approval", "A positive approval example", "A latency-only test", 0, "The expected outcome is review, with no effect."),
    ("A system refuses every renewal and passes all negative controls. What else must be measured?", "Coverage and success on valid positive cases", "Only its refusal wording", "Only the number of controls", 0, "Controls alone can reward an unusable always-refusing system."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-agent-workflows"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                  path=quiz_path, title=titles[quiz_path],
                  summary="Check rationale, candidate filtering, critique, examples, context, and controls.",
                  body="<p>These cases ask what a reasoning pattern actually proves. Select the decision that survives independent checks, not the one with the most persuasive wording.</p><h2>Reasoning lessons</h2>" + links([spec["path"] for spec in specs]) + "<h2>Project and sections</h2>" + links([project_path, patterns, production, quizzes]),
                  sort_order=26090, status="published", published_at=stamp,
                  created_at=stamp, updated_at=stamp)
quiz_entry["data"].update(subject_root=root_path, section_path=quizzes,
                          content_format="html", author_path="authors/aitrove-editorial",
                          seo_ready=True, duration_minutes=12,
                          related=related([spec["path"] for spec in specs] + [project_path]),
                          questions=[{"prompt": prompt,
                                      "options": ([a, b, c][index % 3:] + [a, b, c][:index % 3]),
                                      "answer": (answer - index) % 3, "explanation": explanation}
                                     for index, (prompt, a, b, c, answer, explanation) in enumerate(questions)])
new_rows.append(quiz_entry)

for hub_path, selected, title, summary in [
    (patterns, [spec["path"] for spec in specs if spec["section"] == patterns],
     "Reasoning with explicit checks", "Use visible grounds, candidate filters, bounded critique, boundary examples, and source-preserving context."),
    (production, [spec["path"] for spec in specs if spec["section"] == production],
     "Negative controls", "Test cases that should not produce an answer or external effect."),
    (projects, [project_path], "Contract renewal verification", "Test a policy boundary with current evidence and held-out cases."),
    (quizzes, [quiz_path], "Reasoning checks quiz", "Interpret what each reasoning pattern proves and what remains unverified."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

root_hub = lookup[root_path]
root_hub["body"] += "<h2>Reasoning patterns and proof</h2><p>These lessons test where explanations, multiple candidates, critique, examples, and compressed context help or fail.</p>" + links([spec["path"] for spec in specs] + [project_path, quiz_path])
root_hub["updated_at"] = stamp

backlinks = {
    "prompt-engineering/evidence-id-traceability": specs[0]["path"],
    "prompt-engineering/judge-calibration-and-order-bias": specs[1]["path"],
    "prompt-engineering/metamorphic-prompt-tests": specs[2]["path"],
    "prompt-engineering/few-shot-example-selection": specs[3]["path"],
    "prompt-engineering/chunk-boundary-and-parent-context": specs[4]["path"],
    "prompt-engineering/evaluation-slice-design": specs[5]["path"],
}
for existing_path, new_path in backlinks.items():
    entry = lookup[existing_path]
    entry["body"] += "<p><strong>Continue with:</strong> " + link(new_path) + ".</p>"
    entry["data"]["related"] = related([item["path"] for item in entry["data"]["related"]] + [new_path])
    entry["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newLessons": len(specs), "newProjects": 1, "newQuizzes": 1,
                  "newPaths": [entry["path"] for entry in new_rows]}))
