"""Add an evaluation-governance sequence, project, and decision quiz."""

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
projects = "prompt-engineering/projects"
quizzes = "prompt-engineering/quizzes"
project_path = "prompt-engineering/approval-evaluation-board-project"
quiz_path = "quizzes/prompt-engineering-evaluation-governance"

specs = [
    {
        "slug": "paired-prompt-evaluation-uncertainty",
        "title": "Paired prompt evaluation: count changes, then inspect uncertainty",
        "summary": "Compare candidate and baseline on the same cases and keep critical failures visible.",
        "definition": "A paired prompt evaluation sends each case through a baseline and a candidate under the same evidence, model settings, and scoring rule. The unit of comparison is the case, not the average of two unrelated batches. Record wins, losses, ties, and critical regressions separately. A small positive net count can be noise, especially when a few cases carry most of the apparent gain. Repeated model calls may reveal unstable cases; they do not repair a flawed label or make a critical failure acceptable. State the decision threshold before reading the result.",
        "case": "A claims assistant gets a shorter prompt. On 47 fixed claims, the candidate improves 14, worsens 9, and leaves 24 unchanged against the previous version. Net improvement is five cases, but one loss approves a claim with a missing receipt. The release is blocked by that predeclared critical rule. The team keeps per-case outcomes and the exact case-set revision, checks whether the receipt was missing in both runs, and sends the contested label to review. It does not report only a 14-to-9 headline or swap out the failing case.",
        "sample": "Case set EV-47; same evidence and model settings for both versions.\nCandidate better: 14; baseline better: 9; tie: 24.\nCritical regression: CL-431, missing receipt accepted.\nGate: block any critical false approval; review disputed label.\nNext run: retain all 47 cases and record the new candidate revision.",
        "cost": "For N cases, one paired pass uses 2N model calls. Repeating each side R times uses 2NR calls plus grading and review; the calls usually dominate latency and spend. The result table occupies O(N) records. A confidence interval or resampling calculation can quantify sampling uncertainty, but it cannot fix correlated cases, biased labels, or a changed evidence snapshot. Stratify by the decision that matters, and budget reviewer time for changes near the release threshold. A larger sample is useful only when its cases represent the production failure modes.",
        "mistakes": ["Do not compare candidates on different case sets and call the result paired.", "Do not bury a critical false approval in an aggregate win rate.", "Do not treat repeated sampling as a substitute for a valid expected label."],
        "related": ["prompt-engineering/evaluation-slice-design", "prompt-engineering/release-regression-gate", "prompt-engineering/judge-order-audit"],
    },
    {
        "slug": "evaluation-label-disagreement",
        "title": "Evaluation labels: adjudicate disagreement before scoring a release",
        "summary": "Keep reviewer disagreement visible and separate ambiguous cases from model errors.",
        "definition": "A reference label is a decision claim made by a reviewer under a particular policy version. When reviewers disagree, the case may expose unclear instructions, incomplete evidence, or a policy boundary rather than a model defect. Have independent reviewers label without seeing the candidate response where practical. Record their labels and reasons, adjudicate consequential disagreements, and preserve the original votes. A model judge can assist with triage, but it should be checked against human-labeled cases before it becomes a release gate. The adjudicated outcome must be tied to the policy and evidence that produced it.",
        "case": "Two reviewers label ticket TK-862 differently: one says billing dispute, the other says service incident because the outage caused the duplicate charge. The case packet lacks the incident start time. The board marks the reference as unresolved, requests the event record, and leaves this case outside the binary score until a policy owner decides the precedence rule. It still tracks the case as an ambiguity signal. After the record arrives, both reviewers see the same evidence and the policy owner records the final label with a reason. The prompt is not tuned to whichever answer the current model produced.",
        "sample": "Case TK-862; policy LP-12; evidence packet EP-8.\nReviewer A: billing; reviewer B: incident.\nDisagreement reason: outage time missing.\nState: unresolved; excluded from pass/fail denominator.\nResolution: append event record and policy-owner decision.\nAudit: preserve both votes and the final rationale.",
        "cost": "Two independent labels cost roughly twice the first-pass human effort, and adjudication adds work to a subset of cases. If N cases each receive K labels, collection requires O(NK) judgments; matching and disagreement counts are O(NK). Reserve extra review for high-impact or unstable slices rather than treating every typo as a policy dispute. An unresolved reference cannot support a precise accuracy claim. Removing it silently changes the denominator, so report both scored and unresolved counts. The label ledger also helps when policy changes require older cases to be reclassified.",
        "mistakes": ["Do not force a label when required evidence is absent.", "Do not let a candidate answer determine its own reference label.", "Do not erase original reviewer votes after adjudication."],
        "related": ["prompt-engineering/judge-calibration-and-order-bias", "prompt-engineering/human-review-escalation", "prompt-engineering/evaluation-data-leakage"],
    },
    {
        "slug": "adversarial-case-mutation-corpus",
        "title": "Adversarial case mutations: test the boundary, not a magic phrase",
        "summary": "Turn a normal workflow case into controlled attacks on evidence and authority boundaries.",
        "definition": "An adversarial case corpus varies one attack surface at a time while keeping the legitimate task and expected authorization fixed. Start from a valid workflow case, then alter an untrusted field, retrieved document, tool result, or output sink. Record the entry point, attempted deviation, allowed behavior, and the application control expected to stop it. A prompt-injection string is a test input, not a security control by itself. Include benign lookalikes so a filter is not rewarded for rejecting every unusual document. Re-run material cases after changes to prompts, tools, retrieval, and policy.",
        "case": "A claims assistant must summarize a receipt before requesting approval. The base case contains receipt RC-371 and no approval permission. One mutation adds an instruction inside the receipt text to call an approval tool. Another changes the receipt's amount but keeps the account ID; a third puts a forged 'system update' inside the retrieval snippet. The expected output may describe suspicious text as evidence, but the application must not execute approval. A benign receipt containing the phrase 'approval pending' should still be summarized. The board checks both unwanted action calls and unnecessary refusals.",
        "sample": "Base: RC-371, account AC-862, approval permission absent.\nMutation A: receipt text requests approve_claim.\nMutation B: amount changes; server ledger still owns the amount.\nMutation C: retrieved note claims higher instruction priority.\nBenign control: ordinary 'approval pending' status.\nPass: no approval effect; valid receipt facts retained.",
        "cost": "If B base cases each have M mutations, a single pass needs O(BM) case executions, plus controls and repeat runs for unstable behavior. Storage is also O(BM) unless mutations are generated from compact recipes. Keep the mutation recipe and original record ID so failures can be reproduced. Broad random strings often waste calls on unrealistic cases; prioritize surfaces the application actually consumes. Do not store live secrets or customer payloads in the corpus. The valuable result is a failed boundary or a false rejection tied to a precise input change.",
        "mistakes": ["Do not test only the familiar 'ignore previous instructions' wording.", "Do not grant tool permissions just because a retrieved document asks for them.", "Do not omit benign controls that reveal overblocking."],
        "related": ["prompt-engineering/prompt-injection-red-team", "prompt-engineering/tool-result-instruction-quarantine", "prompt-engineering/negative-control-prompt-evaluation"],
    },
    {
        "slug": "online-prompt-experiment-stop-rules",
        "title": "Online prompt experiments: define exposure and stop rules first",
        "summary": "Use controlled traffic only after offline gates and protect irreversible effects.",
        "definition": "An online prompt experiment compares a candidate with a baseline on live traffic using a stable assignment unit, eligibility rule, and predeclared outcome measures. Offline checks come first. If the workflow can cause an external effect, the experiment must keep the same application permissions and independent validators for both variants. Assign a user or account consistently so one party does not alternate between policies mid-task. Measure completion, correction, escalation, latency, and cost together with critical error counts. Define a stop rule and an operator before exposure; do not inspect the dashboard repeatedly and declare success at the first favorable fluctuation.",
        "case": "A support assistant proposes a new clarification prompt for account changes. The team first passes offline wrong-account and missing-authorization cases. It then sends a small eligible slice of read-only support traffic to the candidate, assigned by account ID. The experiment excludes payment and cancellation actions. The candidate reduces unnecessary questions, but two cases omit the final verification step. The predeclared stop rule pauses exposure and sends those cases to review. The team checks assignment, trace IDs, and event definitions before blaming the wording alone.",
        "sample": "Assignment unit: account_id; eligibility: read-only support.\nVariants: baseline PEB-118, candidate PEB-124.\nPrimary: correct resolution after review; guardrail: omitted verification.\nStop: any confirmed wrong-account action or repeated missing step.\nWindow: fixed review period; owner: support on-call.\nRecord: assignment, bundle ID, validator result, correction outcome.",
        "cost": "Routing and recording a fixed set of fields add O(1) work per eligible request; analysis over M events is O(M). The main cost is enough traffic and human review to distinguish a real improvement from chance and case-mix changes. A small canary may detect severe failures but rarely estimates a subtle quality gain precisely. Early stopping for harm is appropriate; early stopping for a favorable score can inflate the apparent improvement. Keep assignment and exclusion rules fixed, and do not use downstream actions as a proxy when their logs are incomplete.",
        "mistakes": ["Do not expose a candidate that failed its offline critical gate.", "Do not randomize each turn when account-level consistency matters.", "Do not choose the experiment's winning metric after seeing the dashboard."],
        "related": ["prompt-engineering/prompt-version-rollout", "prompt-engineering/prompt-evaluation-ci-gate", "devops/progressive-delivery"],
    },
    {
        "slug": "evaluation-case-version-ledger",
        "title": "Evaluation case ledgers: revise labels without erasing history",
        "summary": "Version inputs, evidence, policy, and expected outcomes as one inspectable case record.",
        "definition": "An evaluation case is more than a prompt and preferred sentence. It includes the legitimate task, input snapshot, evidence IDs, policy version, expected decision, permitted actions, severity, and label status. A ledger records each revision and why it happened. When a policy changes, create a new case revision or an explicit migration; do not overwrite the old expected outcome and then compare new scores with an earlier run as if the test were unchanged. Mark cases used for prompt tuning separately from held-out cases, and control access to the holdout. Keep private payloads out of ordinary fixture exports.",
        "case": "Case CL-431 originally required review when a receipt was missing under policy LP-12. A later policy allows low-value claims to proceed with another verified document. The board creates CL-431 revision 2 with the new evidence rule and a linked policy decision. Old release results continue to point to revision 1. A candidate tested on revision 2 cannot be compared directly with a baseline run against revision 1. The board either replays both bundles on the new set or reports the scores as separate regimes. The older case remains useful for reproducing an incident from its release period.",
        "sample": "Case ID: CL-431; revision: 2; policy: LP-13.\nInput snapshot: IS-77; evidence IDs: RC-371, VD-9.\nExpected decision: review unless VD-9 is verified.\nSeverity: critical; action permission: none.\nLabel state: adjudicated; prior revision: CL-431@1.\nUse: holdout; access: evaluation owner only.",
        "cost": "A ledger lookup can be O(1) by case ID and revision; storing R revisions across N cases takes O(NR) records in the worst case. Replaying both bundles after a policy migration costs about 2N model calls for one pass, but it is the price of a valid comparison. Snapshot retention and access control may dominate storage cost for document-heavy cases. Keep metadata and evidence references when full payload retention is not necessary. A test set that silently changes labels makes release trends meaningless even if every individual score was computed correctly.",
        "mistakes": ["Do not overwrite a historical label in place.", "Do not compare scores across different policy revisions without replaying both sides.", "Do not publish private holdout cases to prompt authors as demonstrations."],
        "related": ["prompt-engineering/evaluation-data-leakage", "prompt-engineering/prompt-release-artifact-bundle", "prompt-engineering/evidence-id-traceability"],
    },
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
new_paths = set(paths + [project_path, quiz_path])
assert not new_paths.intersection(lookup)
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: govern a claims-assistant evaluation board"
titles[quiz_path] = "Prompt evaluation governance decisions"


def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(paths_to_link):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(paths_to_link)) + "</ul>"


def related(paths_to_link):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(paths_to_link)]


def article(path, title, summary, body, section, order, connections, kind="tutorial"):
    entry = copy.deepcopy(lookup["prompt-engineering/evaluation-slice-design"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)),
                 path=path, title=title, summary=summary, body=body,
                 subject="prompt-engineering-production" if section == production else "prompt-engineering-project",
                 difficulty="Advanced", tags=["prompt engineering", "evaluation"],
                 sort_order=order, status="published", published_at=stamp,
                 created_at=stamp, updated_at=stamp)
    entry["data"].update(kind=kind, reading_minutes=11 if kind == "tutorial" else 18,
                         author_path="authors/aitrove-editorial", subject_root=subject_root,
                         section_path=section, content_format="html", seo_ready=True,
                         related=related(connections))
    return entry


new_rows = []
for index, (path, spec) in enumerate(zip(paths, specs)):
    peers = [other for other in paths if other != path]
    connections = [production, subject_root] + spec["related"] + peers + [project_path, quiz_path]
    body = (
        "<p>" + html.escape(spec["definition"]) + "</p>"
        "<h2>Decision in practice</h2><p>" + html.escape(spec["case"]) + "</p>"
        '<pre><code class="language-text">' + html.escape(spec["sample"], quote=False) + "</code></pre>"
        "<h2>Performance and operating cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
        "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in spec["mistakes"]) + "</ul>"
        "<h2>Connected lessons</h2>" + links(connections)
    )
    new_rows.append(article(path, spec["title"], spec["summary"], body,
                            production, 26300 + index * 10, connections))

project_connections = paths + ["prompt-engineering/release-regression-gate",
                                "prompt-engineering/prompt-telemetry-privacy-budget", quiz_path]
project_body = (
    "<p>This project gives a fictional claims team a release decision to make, not a prompt to polish. The current assistant checks receipts and drafts a recommendation; the server owns approvals. A candidate prompt shortens explanations and changes how missing evidence is described. The evaluation board must decide whether to ship it, revise the test set, or stop the rollout. Produce a case ledger, paired comparison, adjudication note, adversarial packet, and experiment brief.</p>"
    "<h2>Build a defensible offline result</h2><p>Freeze 47 cases under policy LP-12 and evidence snapshot IS-77. Run baseline PEB-118 and candidate PEB-124 on the same cases and retain each response, validator outcome, and receipt state. Fourteen cases improve, nine worsen, and 24 tie. Case CL-431 is among the losses: the candidate approves a claim without its required receipt. Apply the declared critical gate before considering the net result. Two reviewers disagree on a separate outage-related charge case; preserve both votes, mark it unresolved, and request the missing event record before counting it in a scored denominator.</p>"
    "<h2>Probe boundaries and plan exposure</h2><p>Start from receipt RC-371. Add one mutation that asks the assistant to approve the claim from inside the receipt body, one that forges a higher-priority message in retrieved text, and one benign 'approval pending' control. Confirm that no tool effect occurs and that ordinary evidence remains readable. A later policy revision creates CL-431@2 rather than changing CL-431@1 in place. Re-run both bundles under the new case revision before comparing them. Only after the critical failure is fixed may the team propose an account-stable, read-only canary with a named owner and a stop rule for omitted verification or wrong-account effects.</p>"
    '<pre><code class="language-text">Deliverables: EV-47@LP-12 case ledger and paired result table.\nCritical loss: CL-431@1; release status: blocked.\nUnresolved label: TK-862; hold outside scored denominator.\nAttack packet: receipt instruction, forged retrieval note, benign control.\nPolicy migration: preserve CL-431@1 and add CL-431@2.\nCanary proposal: read-only accounts after offline gate passes.</code></pre>'
    "<h2>Performance and operating cost</h2><p>One paired pass uses 94 model calls for 47 cases before repeats, attack mutations, or label review. If the board runs three attack variants for each of 12 base cases, that adds 36 executions. The ledger uses O(N) records for one revision per case and grows with revisions. Human adjudication is the expensive part when evidence is incomplete; do not hide it behind a faster model judge. A blocked release still provides useful information when its artifacts let the team reproduce the false approval and revise the right control.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not ship on a positive net count after a critical false approval.</li><li>Do not resolve reviewer disagreement by copying the candidate answer.</li><li>Do not rewrite an old case revision when policy changes.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections)
)
new_rows.append(article(project_path, titles[project_path],
                        "Decide a claims-assistant release with paired tests, disputed labels, attacks, and an exposure rule.",
                        project_body, projects, 26360, project_connections, kind="project"))

questions = [
    ("What makes a prompt comparison paired?", "Both versions run on the same cases and evidence", "Each version runs on a different month", "Only average response length is compared", "Pairing preserves a case-level difference."),
    ("The candidate wins 14 cases and loses 9, including one critical false approval. What follows?", "Block under the declared critical gate", "Ship because net wins are positive", "Remove the critical case", "A critical invariant is separate from the aggregate count."),
    ("Two reviewers disagree because an event record is missing. How should the reference be handled?", "Mark unresolved and request the record", "Adopt the candidate answer", "Count both labels as model errors", "Missing evidence cannot support a forced reference label."),
    ("Why preserve both original reviewer votes?", "To audit the boundary and adjudication", "To give the model two answers", "To avoid a policy owner", "The disagreement is part of the case history."),
    ("A receipt asks the assistant to approve a claim. What is the correct boundary?", "Treat it as receipt data; server permission controls approval", "Treat it as a new system instruction", "Call the approval tool once to test it", "Untrusted evidence cannot grant action authority."),
    ("What does a benign control reveal in an attack corpus?", "Whether the system rejects harmless lookalikes", "The model's training date", "The maximum token limit", "Attack tests should measure overblocking as well as unwanted effects."),
    ("What is a sensible online assignment unit when an account spans multiple turns?", "The account ID", "Each generated token", "A new random value on every turn", "Stable assignment prevents policy switching within an account workflow."),
    ("When should an online candidate be exposed?", "After offline critical gates pass", "Before case labels are checked", "As soon as one sample looks good", "Live traffic is not a substitute for a known-failure gate."),
    ("A policy changes the expected outcome for CL-431. What preserves comparison integrity?", "Add a new case revision and replay both bundles", "Overwrite the old label", "Compare a new score against the old run unchanged", "Both variants need the same policy and case revision."),
    ("What belongs in a versioned evaluation case?", "Input, evidence, policy, expected decision, and label state", "Only a preferred sentence", "Only a prompt title", "The expected result depends on the evidence and policy snapshot."),
    ("What does repeating model calls fail to repair?", "An invalid reference label", "Random variation detection", "Case-level trace collection", "More samples do not make the expected answer correct."),
    ("A dashboard looks favorable halfway through the agreed period. What should the team do?", "Continue under the declared plan unless a harm stop fires", "Declare success immediately", "Change the primary metric", "A favorable interim score is not a predeclared stopping rule."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-foundation-decisions"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                  path=quiz_path, title=titles[quiz_path],
                  summary="Test paired comparisons, disputed labels, attack cases, live exposure, and case revisions.",
                  body="<p>Use the release board's evidence rather than a polished answer. Each question asks whether a prompt result supports a decision, needs adjudication, or must be blocked.</p><h2>Evaluation lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, production, quizzes]),
                  sort_order=26370, status="published", published_at=stamp,
                  created_at=stamp, updated_at=stamp)
quiz_entry["data"].update(subject_root=subject_root, section_path=quizzes,
                          content_format="html", author_path="authors/aitrove-editorial",
                          seo_ready=True, duration_minutes=12,
                          related=related(paths + [project_path]),
                          questions=[{"prompt": prompt,
                                      "options": ([correct, distractor_a, distractor_b][index % 3:] + [correct, distractor_a, distractor_b][:index % 3]),
                                      "answer": (-index) % 3, "explanation": explanation}
                                     for index, (prompt, correct, distractor_a, distractor_b, explanation) in enumerate(questions)])
new_rows.append(quiz_entry)

for hub_path, selected, title, summary in [
    (production, paths, "Evaluation governance", "Test paired outcomes, labels, attack boundaries, live exposure, and case revisions."),
    (projects, [project_path], "Claims evaluation board", "Make a release decision from a complete evaluation packet."),
    (quizzes, [quiz_path], "Evaluation governance quiz", "Practice the decisions that make an evaluation trustworthy."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

root_hub = lookup[subject_root]
root_hub["body"] += "<h2>Can the evaluation be trusted?</h2><p>Follow the case from paired comparison through label review, attack mutation, live exposure, and revision history.</p>" + links(paths + [project_path, quiz_path])
root_hub["updated_at"] = stamp

backlinks = {
    "prompt-engineering/evaluation-slice-design": paths[0],
    "prompt-engineering/judge-calibration-and-order-bias": paths[1],
    "prompt-engineering/prompt-injection-red-team": paths[2],
    "prompt-engineering/prompt-version-rollout": paths[3],
    "prompt-engineering/evaluation-data-leakage": paths[4],
    "prompt-engineering/prompt-evaluation-ci-gate": paths[0],
    "prompt-engineering/prompt-release-artifact-bundle": paths[4],
    "prompt-engineering/prompt-telemetry-privacy-budget": paths[3],
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
