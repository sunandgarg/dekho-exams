"""Add two practical navigation guides across the Prompt Engineering curriculum."""

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
diagnosis_path = "prompt-engineering/prompt-failure-diagnosis-map"
release_path = "prompt-engineering/prompt-release-review-packet"
assert diagnosis_path not in lookup and release_path not in lookup
titles = {entry["path"]: entry["title"] for entry in entries}
titles[diagnosis_path] = "Prompt failure diagnosis: find the broken contract first"
titles[release_path] = "Prompt release review: assemble the decision packet"


def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(paths):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(paths)) + "</ul>"


def related(paths):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(paths)]


diagnosis_groups = [
    ("Wrong task or incomplete answer", ["prompt-engineering/task-contract", "prompt-engineering/intent-to-acceptance-check", "prompt-engineering/clarification-versus-assumption-gate", "prompt-engineering/output-budget-and-completeness-contract"]),
    ("Wrong evidence or unsupported claim", ["prompt-engineering/retrieval-evidence-selection", "prompt-engineering/retrieval-freshness-and-conflict", "prompt-engineering/evidence-id-traceability", "prompt-engineering/cross-modal-conflict-ledger"]),
    ("Malformed or unsafe output", ["prompt-engineering/schema-and-abstention", "prompt-engineering/schema-repair-retry-budget", "prompt-engineering/output-sink-validation", "prompt-engineering/sensitive-output-redaction-gate"]),
    ("Unexpected tool behavior", ["prompt-engineering/tool-call-authorization-contract", "prompt-engineering/tool-result-instruction-quarantine", "prompt-engineering/side-effect-receipt-reconciliation", "prompt-engineering/request-risk-routing-contract"]),
    ("Regression after a change", ["prompt-engineering/paired-prompt-evaluation-uncertainty", "prompt-engineering/evaluation-label-disagreement", "prompt-engineering/prompt-release-artifact-bundle", "prompt-engineering/prompt-trace-observability"]),
]

diagnosis_body = (
    "<p>Prompt failure diagnosis is the process of identifying which contract broke before changing wording. A bad final answer may begin with a missing task field, stale retrieval result, wrong tool permission, truncated output, or an invalid test label. Freeze the failing request and its permitted evidence first. Record the prompt bundle, model settings, tool schema, retrieval snapshot, validator result, and any external effect receipt. Reproduce with the same inputs before editing the prompt. If the failure cannot be reproduced, preserve the trace and mark the cause unresolved rather than writing a confident story about model behavior.</p>"
    "<h2>Classify the observed failure</h2><p>A support assistant labels ticket TK-934 as billing when the actual request is a service outage with an invoice impact. Inspect the task label definitions and expected decision before adding examples. If the output omits the evidence ID, inspect schema validation and the output ceiling. If it cites a retired policy, inspect retrieval filters and freshness. If it tries to change an account, inspect the server permission decision and tool arguments; no prompt rewrite can supply missing authorization. One response can contain several failures. Record the earliest broken boundary and the downstream symptoms separately so the repair targets the cause.</p>"
    "<h2>Run a controlled repair</h2><p>Choose one hypothesis and change one component at a time: task wording, example pair, evidence selection, parser, tool scope, or model setting. Keep the original case in a development set and preserve an independent holdout. Re-run nearby cases that should remain unchanged. A targeted example may fix the outage-versus-billing boundary while causing the model to overuse the incident label; a shorter output may fix latency while dropping a required field. Compare both errors and costs by slice. If the expected label itself is disputed, adjudicate it before scoring the prompt. Use a negative control to check that the candidate does not produce a forbidden answer merely because its style improved.</p>"
    '<pre><code class="language-text">Failure TK-934: incident labeled billing.\nBundle: PEB-124; evidence snapshot: IS-83; parser: V5.\nTask check: incident wins when outage is the primary event.\nHypothesis: an invoice mention is overweighted.\nChange: one contrastive pair in development set only.\nGate: held-out incident slice improves; billing slice does not regress.\nOther checks: schema complete, no account effect, cost within budget.</code></pre>'
    "<h2>Performance and review cost</h2><p>Replaying N cases against V variants takes O(NV) model calls, and detailed human review is concentrated on disagreements and high-impact failures. Inspecting an existing trace is often cheaper than generating fresh variants. If several components changed together, the team may need a small factorial experiment or a rollback to isolate the cause; that cost grows rapidly with the number of independent factors. Preserve a compact failure record so future incidents do not pay the same discovery cost. A faster prompt that hides a critical error is not an improvement.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not rewrite prompt prose before checking evidence, parser, and permissions.</li><li>Do not tune on the final holdout case that should test the repair.</li><li>Do not call an unresolved label disagreement a model failure.</li></ul>"
)
for group_title, targets in diagnosis_groups:
    diagnosis_body += "<h2>" + html.escape(group_title) + "</h2><p>Open the checks that match this symptom and inspect their evidence before changing the prompt.</p>" + links(targets)
diagnosis_connections = [subject_root, production, release_path] + [path for _, targets in diagnosis_groups for path in targets]
diagnosis_body += "<h2>Release follow-through</h2>" + links([release_path, "prompt-engineering/prompt-evaluation-ci-gate", "prompt-engineering/negative-control-prompt-evaluation"])

release_groups = [
    ("Task and authority", ["prompt-engineering/task-contract", "prompt-engineering/role-tone-and-authority-limit", "prompt-engineering/tool-call-authorization-contract", "prompt-engineering/system-prompt-as-nonsecret-contract"]),
    ("Evidence and expected outcomes", ["prompt-engineering/evaluation-case-version-ledger", "prompt-engineering/retrieval-quality-gate-project", "prompt-engineering/evaluation-label-disagreement", "prompt-engineering/adversarial-case-mutation-corpus"]),
    ("Candidate comparison", ["prompt-engineering/paired-prompt-evaluation-uncertainty", "prompt-engineering/release-regression-gate", "prompt-engineering/fairness-slice-testing", "prompt-engineering/refusal-and-safe-continuation-contract"]),
    ("Operating limits", ["prompt-engineering/cost-latency-quality-budget", "prompt-engineering/sensitive-output-redaction-gate", "prompt-engineering/prompt-telemetry-privacy-budget", "prompt-engineering/high-impact-advice-review-gate"]),
    ("Promotion and recovery", ["prompt-engineering/prompt-evaluation-ci-gate", "prompt-engineering/prompt-release-artifact-bundle", "prompt-engineering/online-prompt-experiment-stop-rules", "prompt-engineering/prompt-version-rollout"]),
]

release_body = (
    "<p>A prompt release review packet is the evidence needed to approve or block a specific candidate bundle. It names the task, allowed actions, exact prompt and model settings, evidence and parser versions, case-set revision, evaluation results, critical failures, operating costs, and rollback owner. Approval applies to that bundle and environment, not to an informal prompt string. A green aggregate score cannot override a predeclared critical failure. If the case labels, tool schema, or retrieval index changed after testing, the team must replay the affected cases before promotion.</p>"
    "<h2>Build a case-level decision record</h2><p>For candidate PEB-131, the owner starts with 53 frozen cases under policy LP-14. The candidate improves routine response completeness but fails case CL-487 by returning a private payment field in an export filename. The review packet includes the trace ID and blocked sink, not the private value. The release is blocked until the output gate is repaired and both candidate and baseline are replayed on the same case revision. The reviewer also sees two unresolved reference labels, a wrong-account negative control, cost per 1,000 eligible requests, and the median and tail latency observed under the same test load. The decision states what was measured and what remains unknown.</p>"
    "<h2>Check the release boundary</h2><p>After offline gates pass, promotion should use the same bundle digest in staging and any canary. Keep the traffic assignment stable, define eligible requests, and name a stop rule before exposure. A rollback pointer changes future requests; it does not undo a completed ticket, payment, or export. Keep receipt reconciliation separate. For a high-impact workflow, make the human owner and escalation path explicit. The packet should identify which privacy fields are logged, which are withheld, and how a reviewer can access redacted evidence without copying the original payload into ordinary telemetry.</p>"
    '<pre><code class="language-text">Candidate: PEB-131; baseline: PEB-124; case set: EV-53@LP-14.\nCritical result: CL-487 private field in export filename -> block.\nOther results: completeness by slice; unresolved labels: 2.\nCost: model calls, input/output tokens, median and tail latency.\nRe-test: same evidence and parser versions for both bundles.\nPromotion: digest match, stable assignment, named stop owner.\nRollback: restore prior digest; reconcile completed effects.</code></pre>'
    "<h2>Performance and review cost</h2><p>One paired pass over N cases costs 2N model calls; attack mutations, repeated samples, and human adjudication add to that budget. Keeping a manifest and digest takes O(L) work for L bytes of release metadata. The review packet occupies O(N) case records plus artifact pointers. Do not reduce it to a dashboard total if the release can make consequential errors. A smaller, well-chosen critical set may run on every merge, while broader replay can run before promotion under a written policy. Failed reviews are useful when they preserve the exact cause and the next check.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not approve a prompt string that was tested with a different parser or tool catalog.</li><li>Do not hide a critical failure behind an improved average score.</li><li>Do not assume rollback reverses an external effect already committed.</li></ul>"
)
for group_title, targets in release_groups:
    release_body += "<h2>" + html.escape(group_title) + "</h2><p>Review the linked contracts and attach the relevant case-level evidence to the packet.</p>" + links(targets)
release_connections = [production, subject_root, diagnosis_path] + [path for _, targets in release_groups for path in targets]
release_body += "<h2>Related implementation</h2>" + links([diagnosis_path, "devops/continuous-integration", "devops/artifact-promotion", "devops/progressive-delivery", "python/testing"])


def make_article(path, section, subject, order, summary, body, connections):
    entry = copy.deepcopy(lookup["prompt-engineering/evaluation-slice-design"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)),
                 path=path, title=titles[path], summary=summary, body=body,
                 subject=subject, difficulty="Advanced", tags=["prompt engineering", "field guide"],
                 sort_order=order, status="published", published_at=stamp,
                 created_at=stamp, updated_at=stamp)
    entry["data"].update(kind="tutorial", reading_minutes=13,
                         author_path="authors/aitrove-editorial", subject_root=subject_root,
                         section_path=section, content_format="html", seo_ready=True,
                         related=related(connections))
    return entry


new_rows = [
    make_article(diagnosis_path, subject_root, "prompt-engineering", 26600,
                 "Locate the broken task, evidence, output, tool, or evaluation contract before editing wording.",
                 diagnosis_body, diagnosis_connections),
    make_article(release_path, production, "prompt-engineering-production", 26610,
                 "Review the exact bundle, case-level results, operating limits, and rollback plan.",
                 release_body, release_connections),
]

for hub_path, new_path, heading, summary in [
    (subject_root, diagnosis_path, "Troubleshooting by symptom", "Trace failures to task, evidence, output, tools, or evaluation before changing wording."),
    (production, release_path, "Release review packet", "Bring case-level checks, costs, promotion, and rollback into one decision."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": heading, "summary": summary, "lessons": [new_path]})
    hub["body"] += "<h2>" + html.escape(heading) + "</h2><p>" + html.escape(summary) + "</p>" + links([new_path])
    hub["updated_at"] = stamp

lookup[subject_root]["body"] += "<p><strong>For a release decision:</strong> " + link(release_path) + ".</p>"
lookup[subject_root]["updated_at"] = stamp

backlinks = {
    "prompt-engineering/evaluate-and-revise": diagnosis_path,
    "prompt-engineering/evaluation-slice-design": diagnosis_path,
    "prompt-engineering/prompt-trace-observability": diagnosis_path,
    "prompt-engineering/retrieval-freshness-and-conflict": diagnosis_path,
    "prompt-engineering/output-sink-validation": diagnosis_path,
    "prompt-engineering/prompt-evaluation-ci-gate": release_path,
    "prompt-engineering/prompt-release-artifact-bundle": release_path,
    "prompt-engineering/online-prompt-experiment-stop-rules": release_path,
    "prompt-engineering/approval-evaluation-board-project": release_path,
    "prompt-engineering/support-safety-boundary-project": release_path,
}
for existing_path, new_path in backlinks.items():
    entry = lookup[existing_path]
    entry["body"] += "<p><strong>Field guide:</strong> " + link(new_path) + ".</p>"
    entry["data"]["related"] = related([item["path"] for item in entry["data"]["related"]] + [new_path])
    entry["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newGuides": len(new_rows),
                  "backlinkedPages": len(backlinks),
                  "newPaths": [entry["path"] for entry in new_rows]}))
