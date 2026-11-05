"""Add original infrastructure-change prompt lessons, project, and quiz."""

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
project_path = "prompt-engineering/aster-queue-retention-change-review-project"
quiz_path = "quizzes/prompt-engineering-infrastructure-changes"

specs = [
    {
        "slug": "infrastructure-prompt-scope-owner-and-environment",
        "title": "Infrastructure prompts: bind scope, owner, and environment",
        "summary": "Identify the exact managed resource, workspace, desired change, and forbidden effects.",
        "definition": "An infrastructure-change prompt is a review contract for a stateful system. It should name the environment, workspace, resource owner, desired configuration change, expected plan shape, and effects that must block progress. The prompt can draft configuration or inspect a sanitized plan, but it cannot infer that a repository directory points at the intended cloud account. Require the operator to verify the selected workspace and provider identity outside the model before planning. Separate a proposed edit from a reviewed plan and an applied change. Record the current value and target value so an attractive diff does not quietly expand scope to unrelated resources.",
        "case": "A fictional Aster Reports team wants to change queue retention from 47 hours to 71 hours in its production workspace. The queue is managed by the reports platform team. A database in the same workspace is out of scope; any proposed database replacement blocks the change. The prompt asks for the queue address, workspace identity, current and target retention, owner, and expected in-place update. It leaves provider account and workspace confirmation to a trusted operator check. A model cannot establish that the terminal is in production merely because a folder is named prod.",
        "sample": "Environment: Aster Reports production; operator verifies workspace/account.\nOwned resource: report queue; retention 47h -> 71h.\nExpected: one in-place retention update.\nBlocked: database replacement, deletion, import, or address move.\nOwner: reports platform team; apply requires reviewed plan and receipt.",
        "cost": "Inspecting R relevant managed resources is O(R) review work, while verifying the target workspace is a separate identity check. A narrow prompt reduces context size and makes an unexpected replacement easier to notice. A plan can contact provider APIs and may expose sensitive values, so a full raw state dump is not a cheap or safe substitute for a targeted summary. Require a human to confirm the environment before any operation that could change remote state.",
        "mistakes": ["Do not infer account identity from a directory name.", "Do not let an unrelated database replacement ride with a queue change.", "Do not report configuration text as an applied infrastructure change."],
        "related": ["prompt-engineering/code-change-acceptance-contract", "prompt-engineering/tool-call-authorization-contract", "devops/terraform-state-and-plan"],
        "section": applications,
    },
    {
        "slug": "infrastructure-plan-action-and-replacement-gate",
        "title": "Infrastructure plans: classify every action before apply",
        "summary": "Compare the actual plan with the approved change envelope and stop on replacement.",
        "definition": "A plan-review prompt should parse each proposed resource action into create, in-place update, replacement, destroy, import, or state-only change, then compare it with the approved envelope. Replacement is not merely a larger update; it may interrupt service or lose data even when the final name stays the same. Ask which attribute causes replacement and whether it is tied to the requested change. Unknown or sensitive plan fields remain unknown; do not guess at them from a provider's normal behavior. A speculative plan is useful evidence, but the final apply must use a fresh approved plan or a saved reviewed plan under the team's workflow.",
        "case": "Aster's sanitized plan shows the expected queue-retention update and an unexpected production database replacement. The prompt lists both actions and blocks approval. It asks the operator to inspect the database change's cause and compare current configuration, provider version, and recent drift before any apply. The team later fixes the unintended attribute and regenerates a plan with only the queue update. The old blocked plan is kept in the review record, but it is not used for execution. A fluent summary saying 'minor retention change' would be false while the replacement remains in the plan.",
        "sample": "Plan P1: queue retention update -> expected candidate.\nPlan P1: database replacement -> BLOCK; cause unresolved.\nInvestigate configuration, provider, and drift; do not apply P1.\nPlan P2: queue update only -> eligible for owner review.\nApply only the exact reviewed plan under the approved workflow.",
        "cost": "Classifying A plan actions is O(A) inspection before deeper dependency review. A single unexpected replacement can dominate risk, so average action counts are not enough; check every destructive or state-changing action individually. Replanning adds time and provider calls but prevents an obsolete plan from being treated as current evidence. A saved plan file can contain sensitive material and must be handled as a controlled artifact, not attached to public documentation or pasted into an unrestricted prompt.",
        "mistakes": ["Do not summarize a plan by its requested change while hiding extra actions.", "Do not treat replacement as an in-place update.", "Do not approve a new plan merely because an earlier plan was reviewed."],
        "related": ["prompt-engineering/output-sink-validation", "prompt-engineering/side-effect-receipt-reconciliation", "devops/terraform-replacement-headroom"],
        "section": applications,
    },
    {
        "slug": "infrastructure-drift-secret-and-state-boundary",
        "title": "Infrastructure prompts: quarantine state secrets and drift",
        "summary": "Use redacted evidence to separate manual drift from intended configuration changes.",
        "definition": "Infrastructure state and plan files may contain credentials, identifiers, and other sensitive attributes. A prompt should receive only the fields needed for the current question, with secrets and unrelated resources removed. Redaction must preserve action type and the attribute path that explains a proposed change; otherwise the model may call a dangerous replacement harmless. Drift is a difference between recorded configuration or state and observed infrastructure, not automatic permission to overwrite the live value. The prompt should ask whether the manual change is intentional, who owns it, and whether the desired state should adopt or reverse it. State access and lock recovery belong to controlled operational tools, not model instructions.",
        "case": "Aster's database replacement is traced to a manual setting change made during an earlier incident, while the queue-retention request is unrelated. The prompt receives a redacted attribute diff and incident change record, not the full state file. It marks the database question as a separate ownership decision: keep the manual value and update configuration, or revert it through an approved change. Until that is resolved, the queue plan must be regenerated without an accidental database action. A hidden token in the state is never needed to classify the replacement, so it remains outside the model context.",
        "sample": "Input: resource address, action, changed attribute name, redacted values.\nDrift: database manual setting changed during prior incident.\nUnknown: whether to adopt or reverse; owner must decide.\nNever paste raw state, token, or saved binary plan into the prompt.\nRegenerate and review the queue-only plan after resolution.",
        "cost": "Redacting N plan fields is O(N) work; manual review is still needed for fields whose names reveal sensitive information. A narrow diff lowers model token use and disclosure risk. Drift investigation may require a separate incident record and owner conversation, which costs more than simply applying the plan but preserves change authority. If a state lock is held, diagnose its active owner before recovery; deleting a lock based on a model guess can allow concurrent writes and corrupt the operational record.",
        "mistakes": ["Do not paste raw state into a general-purpose prompt.", "Do not treat detected drift as approval to overwrite an incident change.", "Do not force-unlock state without establishing whether another run is active."],
        "related": ["prompt-engineering/privacy-and-data-minimization", "prompt-engineering/sensitive-output-redaction-gate", "devops/infrastructure-drift-triage", "devops/terraform-state-secret-boundary"],
        "section": applications,
    },
    {
        "slug": "infrastructure-apply-approval-and-receipt-contract",
        "title": "Infrastructure apply: separate review from execution",
        "summary": "Require a reviewed plan identity, authorized operator, lock, and apply receipt.",
        "definition": "An apply prompt may prepare an execution checklist, but approval and execution are separate capabilities. The checklist should identify the reviewed plan, target workspace, authorized operator, change window, state lock, expected actions, and stop conditions. Verify that the plan applied is the one reviewed or that a newly generated plan received fresh approval. Do not issue an auto-approve command just because the prompt says 'safe.' After apply, collect the tool's outcome, changed resource identities, and any partial failure. A model assertion that apply succeeded is not a receipt. If execution fails midway, inspect live state before deciding whether to retry or rollback.",
        "case": "After Aster resolves the unrelated database drift, plan P2 contains only the 47-to-71-hour queue-retention update. The reports platform owner approves P2 for the verified production workspace. The operator checks that no other run holds the state lock, executes the reviewed plan through the controlled pipeline, and records run R-47. The pipeline reports the queue update completed, but the team still checks the queue's actual retention setting and a new plan for unexpected changes. If P2 had changed since review, the approval would not transfer automatically. The prompt can list these checks; it cannot click apply or declare success from its own prose.",
        "sample": "Reviewed plan: P2; queue retention update only.\nTarget: verified production workspace and account.\nAuthority: reports platform owner approves; operator executes.\nReceipt: pipeline run R-47 with action result and timestamp.\nPostcheck: live queue setting 71h; no unexpected plan actions.",
        "cost": "The checklist is O(A) for A reviewed actions, with extra time for locking, identity checks, and post-apply verification. A saved plan avoids silently applying a different set of proposed changes, but the artifact needs restricted storage because it may contain secrets. Postchecks are not redundant: provider completion can precede application-level readiness or reveal partial execution. Maintain a rollback or forward-fix route appropriate to the resource; changing retention back may not restore messages that already expired under an earlier policy.",
        "mistakes": ["Do not confuse a plan approval with permission for any later plan.", "Do not call a model summary an apply receipt.", "Do not assume a failed apply left every resource unchanged."],
        "related": ["prompt-engineering/tool-call-authorization-contract", "prompt-engineering/side-effect-receipt-reconciliation", "devops/terraform-state-lock-recovery"],
        "section": applications,
    },
    {
        "slug": "infrastructure-postapply-verification-and-rollback-review",
        "title": "Infrastructure release: verify live state and rollback limits",
        "summary": "Check the actual resource, drift, behavior, and recovery path after apply.",
        "definition": "An infrastructure release prompt should state what must be true after apply and how each claim will be checked. Compare the live resource, a fresh plan, application behavior, and relevant monitoring with the approved change. A zero-diff plan alone may miss a user-visible failure, while a healthy dashboard cannot prove the desired configuration was applied. Define rollback or forward-fix conditions before release and name the owner who can act. Some changes are not fully reversible: reducing retention later will not recreate events already deleted. The release packet should preserve plan identity, apply receipt, observed state, tests, and unresolved limits.",
        "case": "For Aster, pipeline run R-47 reports the queue setting changed from 47 to 71 hours. A direct provider read confirms 71 hours; a fresh plan has no unexpected actions. The reports team checks that new messages are accepted and an existing test message remains readable. Operations watches queue age and dead-letter count during the observation window. A rollback plan can restore the configured retention value, but cannot guarantee recovery of a message that expired before the change. The reviewer records the earlier blocked database replacement as resolved separately rather than pretending it never occurred.",
        "sample": "Receipt: R-47 applied P2 to verified production workspace.\nState: provider read says 71h; fresh plan shows no unexpected action.\nBehavior: message acceptance and retained test record pass.\nMonitor: queue age, failed delivery, dead-letter count.\nLimit: reverting retention cannot resurrect expired messages.",
        "cost": "For V postchecks across R relevant resources, review work is O(V+R), plus an observation period set by workload behavior. A fresh plan and provider read add calls but test different failure modes. Track the tested time window: a five-minute smoke test cannot establish long-term retention behavior by itself. A small controlled fixture can verify that the service still accepts and reads messages now, while retention outcomes need later observation or a safe accelerated test environment.",
        "mistakes": ["Do not infer application health solely from a zero-diff infrastructure plan.", "Do not promise rollback can restore already expired data.", "Do not close the change without checking the actual resource and operator receipt."],
        "related": ["prompt-engineering/prompt-release-review-packet", "prompt-engineering/release-regression-gate", "devops/infrastructure-drift-triage", "devops/rollback-image-retention"],
        "section": production,
    },
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]).intersection(lookup)
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: review an Aster queue retention change"
titles[quiz_path] = "Infrastructure-change prompt decisions"


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
                 difficulty="Advanced", tags=["prompt engineering", "infrastructure changes"],
                 sort_order=30200 + order, status="published", published_at=stamp,
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

project_connections = paths + ["devops/terraform-state-and-plan", "devops/terraform-replacement-headroom", "prompt-engineering/side-effect-receipt-reconciliation", quiz_path]
project_body = (
    "<p>Review a fictional Aster Reports production infrastructure change. The requested queue-retention value moves from 47 hours to 71 hours. The queue is owned by the reports platform team. A database in the same workspace is outside scope. Deliver a prompt packet with the change envelope, redacted plan review, drift decision, apply checklist, and post-apply evidence. This project does not connect to a cloud account or execute an infrastructure change.</p>"
    "<h2>Block the first plan</h2><p>Operator verification establishes the intended production workspace and account. Sanitized plan P1 shows the expected queue update plus an unexpected database replacement. The prompt classifies both actions and blocks P1. Investigation finds a manual database setting changed during an earlier incident. Its owner must choose whether configuration should adopt or reverse that setting through a separate change. The model sees only resource address, action, and redacted attribute path, not raw state, a token, or a binary plan. After resolution, a fresh P2 contains only the queue update and receives a new review.</p>"
    "<h2>Apply and inspect the actual outcome</h2><p>The reports platform owner approves P2. An authorized operator checks state locking and executes the reviewed plan through the controlled pipeline. Run R-47 reports completion. A provider read confirms 71 hours, and a new plan has no unexpected actions. A test message is accepted and read, while operations watches queue age and dead-letter counts during the observation window. The packet states a rollback limit: setting retention back cannot recreate already expired messages. Keep the blocked P1 and its resolution in the review history.</p>"
    '<pre><code class="language-text">Request: queue retention 47h -> 71h; database out of scope.\nP1: queue update + database replacement -> BLOCK.\nInvestigate drift without exposing raw state or saved plan.\nP2: queue update only; owner approves; operator applies.\nR-47: execution receipt; provider read 71h; postchecks pass.\nRollback limit: configuration reversal cannot restore expired data.</code></pre>'
    "<h2>Performance and operating cost</h2><p>Classifying A plan actions takes O(A) review, and checking V postconditions adds O(V) work plus an observation period. This is small compared with the cost of an unexpected database replacement. A redacted packet reduces disclosure and token cost but must still preserve enough action detail to expose risk. Neither a plan nor a pipeline success line proves the resource and application behave as intended; verify the live setting and a representative message path before closing the change.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not apply P1 because its queue change looks right.</li><li>Do not send raw state or a saved plan to an unrestricted model.</li><li>Do not call P2 complete until the actual resource and message path are checked.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Block an unexpected replacement, then review and verify a queue-only plan.", project_body, projects, 60, project_connections, kind="project"))

questions = [
    ("What identifies the real target for an infrastructure change?", "Operator-verified workspace and account", "A folder named production", "The model's guess", "Directory names cannot establish cloud identity."),
    ("What change is requested for Aster?", "Queue retention 47 hours to 71 hours", "Database replacement", "Queue deletion", "The approved scope is a retention update."),
    ("What must happen to plan P1?", "Block it because it includes database replacement", "Apply it for the queue update", "Ignore the replacement line", "Every plan action needs review."),
    ("What should the reviewer do after P1 reveals replacement?", "Inspect cause, drift, and ownership before replanning", "Call it a minor update", "Auto-approve", "Replacement is outside the change envelope."),
    ("May a raw Terraform state file be pasted into a broad prompt?", "No; use a sanitized, task-scoped diff", "Yes, state is always public", "Only after hiding the filename", "State and plan can contain secrets."),
    ("Does detected drift authorize reversal of a prior incident change?", "No; the owner must decide whether to adopt or reverse it", "Yes, always", "Only if the model is confident", "Drift is evidence, not approval."),
    ("Can approval for P1 transfer automatically to fresh P2?", "No; review and approve P2 itself", "Yes, both mention a queue", "Yes if P2 is shorter", "Plan identity matters."),
    ("What proves an apply executed?", "A pipeline or tool receipt such as R-47", "A model statement", "A draft checklist", "The external action needs a system result."),
    ("What follows a partial apply failure?", "Inspect live state before retry or rollback", "Assume all resources unchanged", "Delete the state lock immediately", "Partial effects may remain."),
    ("What confirms the requested queue setting after R-47?", "A provider read of 71 hours", "The commit message", "The earlier P1", "Verify the actual resource."),
    ("Can reverting retention restore messages that already expired?", "No", "Yes, always", "Only if the plan was saved", "Configuration reversal does not resurrect lost data."),
    ("What closes the change review?", "Receipt, live state, behavior checks, and recorded limits", "A zero-diff plan alone", "The model's approval", "Different checks cover different failure modes."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-multimodal-evidence"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                  path=quiz_path, title=titles[quiz_path],
                  summary="Test workspace scope, plan actions, drift, secrets, apply receipts, and verification.",
                  body="<p>Choose the infrastructure-change decision supported by the stated plan and ownership.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, production, quizzes]),
                  sort_order=30270, status="published", published_at=stamp,
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
    (applications, paths[:4], "Infrastructure change prompts", "Bound workspace and scope, inspect plans, quarantine state, and separate apply authority."),
    (production, paths[4:], "Infrastructure release evidence", "Verify live resources, behavior, drift, and rollback limits after apply."),
    (projects, [project_path], "Aster queue change review", "Block an unexpected database replacement before a queue-retention update."),
    (quizzes, [quiz_path], "Infrastructure change decisions", "Test plan actions, state boundaries, receipts, and postchecks."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

root_hub = lookup[subject_root]
root_hub["body"] += "<h2>Infrastructure change reviews</h2><p>Keep target identity, plan action, state secrecy, apply authority, and live verification separate.</p>" + links(paths + [project_path, quiz_path])
root_hub["updated_at"] = stamp

backlinks = {
    "prompt-engineering/code-change-acceptance-contract": paths[0],
    "prompt-engineering/tool-call-authorization-contract": paths[0],
    "prompt-engineering/side-effect-receipt-reconciliation": paths[3],
    "prompt-engineering/sensitive-output-redaction-gate": paths[2],
    "prompt-engineering/release-regression-gate": paths[4],
    "devops/terraform-state-and-plan": paths[1],
    "devops/infrastructure-drift-triage": paths[2],
    "devops/terraform-state-secret-boundary": paths[2],
    "devops/terraform-replacement-headroom": paths[1],
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
