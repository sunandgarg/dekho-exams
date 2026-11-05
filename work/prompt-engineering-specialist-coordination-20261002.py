"""Add original specialist-agent coordination lessons, project, and quiz."""

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
project_path = "prompt-engineering/parcel-platform-specialist-review-project"
quiz_path = "quizzes/prompt-engineering-specialist-coordination"

specs = [
    {
        "slug": "specialist-delegation-threshold-and-baseline",
        "title": "Specialist agents: prove that delegation earns its cost",
        "summary": "Delegate only when independent bounded work beats a measured single-agent baseline.",
        "definition": "A multi-agent prompt workflow splits a task into specialist runs whose results must be combined by a controller. The extra agents do not create independent truth; they create separate context, tool calls, and failure paths. Begin with a single-agent baseline on the same task and acceptance checks. Delegate when the task has separable evidence sets, distinct tool permissions, or parallel work whose output can be reconciled. Keep sequential dependencies sequential. Set a maximum number of agents, tool calls, tokens, and elapsed time before dispatch. Compare answer quality, completeness, cost, and wall-clock latency on held-out cases; a faster-looking demonstration is not a release argument.",
        "case": "A fictional parcel platform has an elevated error rate after a release. Its controller can ask one agent to read the incident packet, or ask three bounded specialists to inspect telemetry, the release diff, and customer contacts. The baseline answers the causal question in 44 seconds with one missing caveat. The three-specialist run returns in 31 seconds but consumes more total model tokens and still needs a merge review. A second case with only one log excerpt takes 19 seconds in the baseline and 28 seconds with delegation. The workflow therefore routes small cases to one agent and sends only cases with independent evidence sets to specialists. Both paths face the same factual and authorization checks.",
        "sample": "Route to specialists only if: evidence sets are separable AND each packet has an owner.\nBaseline: one agent, same input and acceptance checks.\nBudget: at most 3 specialists, 1 retrieval pass each, 2-minute wall clock.\nReject multi-agent gain claims without case-level quality, token, and latency data.",
        "cost": "If independent runs take durations T1 through Tk, ideal parallel wall time approaches max(Ti) plus dispatch and merge time; total model work still grows roughly with the sum of per-agent tokens. Rate limits, shared-tool contention, and a slow specialist can erase the latency gain. A sequential chain costs approximately the sum of its stages. The controller should not spawn an agent to restate a fact it already has. Measure quality against the same held-out cases, including cases where specialists disagree or a required result arrives late.",
        "mistakes": ["Do not equate more agents with more reliable evidence.", "Do not compare a parallel run against an easier single-agent task.", "Do not parallelize a step that requires another agent's verified result."],
        "related": ["prompt-engineering/task-decomposition-and-handoffs", "prompt-engineering/parallel-tool-dependency-plan", "prompt-engineering/cost-latency-quality-budget"],
        "section": applications,
    },
    {
        "slug": "specialist-task-packet-and-authority",
        "title": "Specialist task packets: scope evidence and authority explicitly",
        "summary": "Give each agent a bounded question, input snapshot, tools, output contract, and stop rule.",
        "definition": "A specialist task packet is a narrow contract, not a vague role label. It names the exact question, input artifact versions, permitted tools, read or write authority, required evidence identifiers, output schema, deadline, and uncertainty language. Do not assume the specialist can see the controller's private history, another agent's findings, or a newer repository snapshot. Pass only the context it needs and record what was sent. Tool permissions must be enforced by the runtime, because text such as 'read only' cannot disable a write-capable tool. An agent should return a concise finding with claim, evidence, limits, and unresolved questions; the controller should retain the raw trace for audit.",
        "case": "The parcel incident controller sends three packets based on snapshot PK-214. Telemetry may read metric series and log counts but may not change alerts. Release review may inspect commit RC-47 and configuration diffs but may not deploy or revert. Customer review may read redacted support tags, not account details. A poorly scoped task says 'investigate and fix the outage'; the release specialist then suggests a rollback as if it had operational permission. The revised packet asks it to report changed settings and possible mechanisms only. A production action requires a separate operator decision after the evidence is reconciled.",
        "sample": "Agent: release-review. Snapshot: PK-214; release: RC-47.\nQuestion: Which config values changed, and how might they affect errors?\nTools: read-only diff and release metadata. No deploy, revert, or ticket write.\nReturn: claim ID, cited artifact IDs, observed fact, hypothesis, uncertainty.\nStop: one diff pass or 45 seconds; report incomplete work.",
        "cost": "For K specialists, packet preparation and merge overhead grows at least O(K), while careless context duplication can multiply token use by K. A bounded packet reduces irrelevant reads and makes the returned claims easier to verify. Version identifiers are cheap compared with investigating why one agent used pre-release metrics and another used post-release config. The controller must validate the response schema and check runtime tool scope; the model's declaration that it obeyed a permission rule is not an access-control record.",
        "mistakes": ["Do not give a specialist an open-ended 'fix it' task when it only owns read-only analysis.", "Do not assume agents share conversation history or artifact versions.", "Do not mistake a prompt's tool restriction for runtime enforcement."],
        "related": ["prompt-engineering/tool-call-authorization-contract", "prompt-engineering/prompt-envelope-and-data-boundaries", "prompt-engineering/evidence-id-traceability"],
        "section": applications,
    },
    {
        "slug": "parallel-agent-state-and-write-ownership",
        "title": "Parallel agents: isolate state and assign one writer",
        "summary": "Prevent stale snapshots and overlapping edits when specialists run together.",
        "definition": "Parallel specialists should read a named immutable snapshot or record the exact version each one observed. When outputs are combined, the controller compares those versions before treating results as one consistent picture. If agents can write, assign non-overlapping ownership of files, records, or actions; use a merge gate with conflict detection. A shared directory does not grant coordination by itself. Two agents editing the same file from the same old base can silently overwrite each other even if both prompts request careful work. Prefer read-only specialist analysis and a single controlled writer for consequential changes. Recheck external state immediately before any effect.",
        "case": "Telemetry reads incident snapshot PK-214 at 09:26 UTC. Release review accidentally reads PK-211 from 09:09, before release RC-47. Its conclusion that pool size was 32 conflicts with a later configuration record showing 8, but this is a version mismatch, not proof that either agent is dishonest. The controller re-runs the release packet on PK-214 before merging. In a separate proposed remediation, two agents both want to edit the same deployment manifest. The controller assigns one writer after analysis and requires a fresh diff against current main. No parallel agent is allowed to commit a competing manifest patch.",
        "sample": "Common read snapshot: PK-214.\nTelemetry result: PK-214; metrics 09:17..09:26 UTC.\nRelease result from PK-211: reject for merge; rerun on PK-214.\nWrite ownership: deployment manifest has one assigned editor.\nBefore effect: compare current version with reviewed patch base.",
        "cost": "Version checks across K results are O(K); a file-level merge can be much more expensive if overlapping edits require human resolution. Parallel read-only work often reduces wall time, but snapshot creation, storage, and reconciliation add cost. A single writer may serialize the final edit; that is acceptable when it prevents lost updates. The prompt should name ownership, while optimistic version checks or locks in the application enforce it. Keep a conflict as an explicit unresolved state rather than asking a model to blend incompatible records into a smooth narrative.",
        "mistakes": ["Do not combine findings from different state versions without reconciliation.", "Do not let two agents write the same resource because their descriptions sound independent.", "Do not treat a shared workspace as a locking or version-control protocol."],
        "related": ["prompt-engineering/conversation-checkpoint-reconstruction", "prompt-engineering/parallel-tool-dependency-plan", "prompt-engineering/workbook-edit-diff-and-preservation-gate"],
        "section": applications,
    },
    {
        "slug": "specialist-claim-merge-and-conflict-ledger",
        "title": "Specialist synthesis: merge claims, not fluent summaries",
        "summary": "Keep evidence IDs, version conflicts, and unknowns visible in the final answer.",
        "definition": "A controller merges specialist outputs at claim level. Each claim needs an identifier, originating specialist, evidence IDs, source snapshot, status, and statement. Evidence membership is a basic machine-checkable gate; it does not prove the evidence supports the claim. When two reports disagree, compare their observation windows and artifact versions before attempting to resolve the difference. A majority of agents can repeat one faulty assumption, so vote count is not an evidence rule. The final response separates observed facts from hypotheses, unresolved conflicts, and authorized next actions. A missing specialist is an explicit gap, not a silently omitted paragraph.",
        "case": "Telemetry reports 54 server errors between 09:17 and 09:26 UTC from metric MET-54. Release review confirms RC-47 changed connection-pool size from 32 to 8 in CFG-8. Customer review reports 41 support contacts in that window from redacted tag set SUP-41. These are three observations. The controller may say the release preceded the error rise and pool reduction is a candidate mechanism; it may not claim proven causation or duplicate charges without payment evidence. If customer review arrives with PK-211 while the other results use PK-214, it is held out of the merged finding until rechecked.",
        "sample": "CL-1 observed: 54 errors, MET-54, PK-214.\nCL-2 observed: pool 32 -> 8, CFG-8, PK-214.\nCL-3 observed: 41 contacts, SUP-41, PK-214.\nHypothesis: pool reduction contributed to errors; requires targeted verification.\nUnknown: charge impact; no payment evidence in these packets.",
        "cost": "Indexing E known evidence IDs and checking C returned claim references is O(E+C) expected time with sets and O(E) extra space. Manual claim-support review remains necessary because a real evidence ID can be attached to a false interpretation. Merge work grows with distinct claims and contradictions, not just agent count. Keep packet provenance and a conflict ledger so a later correction can update the one affected claim instead of rewriting the entire incident story. The small checker below verifies packet shape and reference membership only.",
        "mistakes": ["Do not turn temporal proximity into a proven causal statement.", "Do not use agent agreement as a substitute for checking independent evidence.", "Do not describe missing or stale specialist output as consensus."],
        "related": ["prompt-engineering/evidence-id-traceability", "prompt-engineering/cross-modal-conflict-ledger", "prompt-engineering/incident-log-timeline-triage"],
        "section": applications,
    },
    {
        "slug": "specialist-run-budget-timeout-and-release-gate",
        "title": "Specialist workflows: bound retries and review the full trace",
        "summary": "Make timeouts, partial results, tool effects, and release decisions explicit.",
        "definition": "A multi-agent run needs a controller-owned lifecycle: dispatch, deadline, result validation, conflict resolution, effect review, and final release. Give each specialist a retry limit and idempotency plan for tool effects; a timeout does not prove a request failed before its side effect. For read-only tasks, one retry on a fresh snapshot may be acceptable. For writes, inspect the action receipt before retrying. If a required specialist misses the deadline, issue a partial answer with named limits or stop, according to the task contract. Keep correlation IDs from the controller through each specialist and tool event, then evaluate the whole trajectory rather than grading only the final prose.",
        "case": "The parcel controller sets a 45-second limit per specialist and a two-minute overall deadline. Telemetry and release review return on time; customer review stalls after a support-search request. The controller does not invent a customer-impact number. It marks SUP-41 unverified, provides observed metric and config findings, and asks an operator to inspect support data before customer claims are released. A proposed rollback remains blocked: the reviewers have a plausible mechanism but no approved change request or rollback receipt. In an evaluation replay, the team scores timeout handling, evidence-version alignment, prohibited write attempts, and final wording separately.",
        "sample": "Run ID: IR-672; overall deadline 120 seconds.\nRequired: telemetry + release; optional: redacted customer tags.\nTimeout: mark missing packet; no guessed customer impact.\nWrite effect: none authorized; do not attempt rollback.\nRelease: facts cited; hypothesis labeled; gaps and next check named.",
        "cost": "With K independent agents, total model tokens are approximately the sum of each run plus controller synthesis, while wall time is bounded by the slowest required run and merge. A retry adds another run's cost and may duplicate a side effect unless the runtime checks receipts or idempotency keys. Trace review is O(T) in recorded events for a linear pass, but analyzing causal dependencies can take more work. Set deadlines from user value, not arbitrary prompt impatience. A bounded partial answer may be more useful than waiting indefinitely, provided its missing evidence and action limits are explicit.",
        "mistakes": ["Do not retry an ambiguous write without checking whether it already happened.", "Do not let the final answer hide a timed-out required specialist.", "Do not grade only fluent final prose while ignoring forbidden tool attempts."],
        "related": ["prompt-engineering/tool-loop-stop-rules", "prompt-engineering/side-effect-receipt-reconciliation", "prompt-engineering/prompt-trace-observability"],
        "section": production,
    },
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]).intersection(lookup)
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: coordinate a parcel-platform incident review"
titles[quiz_path] = "Specialist-agent coordination decisions"


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
                 difficulty="Advanced", tags=["prompt engineering", "specialist agents"],
                 sort_order=29400 + order, status="published", published_at=stamp,
                 created_at=stamp, updated_at=stamp)
    entry["data"].update(kind=kind, reading_minutes=11 if kind == "tutorial" else 19,
                         author_path="authors/aitrove-editorial", subject_root=subject_root,
                         section_path=section, content_format="html", seo_ready=True,
                         related=related(connections))
    return entry


claim_checker = '''known_evidence = {"MET-54", "CFG-8", "SUP-41"}
expected_snapshot = "PK-214"
packets = [
    {"claim_id": "CL-1", "snapshot": "PK-214", "evidence": ["MET-54"]},
    {"claim_id": "CL-2", "snapshot": "PK-214", "evidence": ["CFG-8"]},
    {"claim_id": "CL-3", "snapshot": "PK-211", "evidence": ["SUP-41"]},
]

seen_claims = set()
for packet in packets:
    claim_id = packet["claim_id"]
    valid = (
        claim_id not in seen_claims
        and packet["snapshot"] == expected_snapshot
        and bool(packet["evidence"])
        and all(ref in known_evidence for ref in packet["evidence"])
    )
    print(f"{claim_id}: {'merge-candidate' if valid else 'hold'}")
    seen_claims.add(claim_id)
'''

new_rows = []
for index, (path, spec) in enumerate(zip(paths, specs)):
    connections = [spec["section"], subject_root] + spec["related"] + [peer for peer in paths if peer != path] + [project_path, quiz_path]
    code_language = "python" if index == 3 else "text"
    code = claim_checker if index == 3 else spec["sample"]
    body = ("<p>" + html.escape(spec["definition"]) + "</p>"
            + "<h2>Operational case</h2><p>" + html.escape(spec["case"]) + "</p>"
            + f'<pre><code class="language-{code_language}">' + html.escape(code, quote=False) + "</code></pre>"
            + "<h2>Performance and operating cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
            + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(mistake) + "</li>" for mistake in spec["mistakes"]) + "</ul>"
            + "<h2>Connected lessons</h2>" + links(connections))
    new_rows.append(article(path, spec["title"], spec["summary"], body, spec["section"], index * 10, connections))

project_connections = paths + ["prompt-engineering/incident-log-timeline-triage", "prompt-engineering/prompt-release-review-packet", "prompt-engineering/evidence-reference-checker", quiz_path]
project_body = (
    "<p>Build a read-only incident review for a fictional parcel platform. Snapshot PK-214 contains metric MET-54, release diff CFG-8, and redacted support tag set SUP-41. The platform emitted 54 server errors between 09:17 and 09:26 UTC. Release RC-47 at 09:12 changed a connection-pool setting from 32 to 8. The tag set lists 41 contacts in the later window. Those records do not show whether any customer was charged twice. The goal is a grounded incident brief, not a rollback or a proof of causation.</p>"
    "<h2>Compare one controller with specialists</h2><p>Run the same incident packet through a single-agent baseline. Then dispatch a telemetry specialist, release-diff specialist, and redacted-support specialist on named snapshot PK-214. Each packet has its own question, read-only tools, evidence-ID output schema, 45-second deadline, and prohibition on mutations enforced by the runtime. The controller has a two-minute overall deadline. Record model tokens, elapsed time, complete claims, prohibited tool attempts, and unresolved gaps for both paths. Keep the multi-agent workflow only if its case-level gains justify the extra work.</p>"
    "<h2>Merge with evidence and version gates</h2><p>Telemetry can report 54 errors with MET-54. Release review can report the pool change with CFG-8. Support review can report 41 contacts only if it returns the redacted tag set from PK-214. A result from PK-211 is held for a fresh read, even if its prose sounds consistent. Use the claim checker to reject stale packets and unknown evidence identifiers, then inspect whether each cited artifact truly supports its statement. The final brief labels the pool change a candidate mechanism and lists targeted verification, such as pool saturation metrics and a controlled comparison. It states that charge impact is unknown. No specialist can authorize a rollback.</p>"
    '<pre><code class="language-text">PK-214; RC-47 at 09:12 UTC; 54 errors at 09:17..09:26 UTC.\nTelemetry: MET-54; release: CFG-8; support: SUP-41.\nObserved: pool setting 32 -> 8; 41 support contacts.\nHypothesis: smaller pool contributed to errors; not yet proven.\nUnknown: duplicate charges; no payment evidence.\nNo writes authorized; late or stale packet stays outside final claims.</code></pre>'
    "<h2>Performance and operating cost</h2><p>Three independent specialists can finish near the slowest specialist duration plus merge time, but their token consumption adds. Repeating the same context three times can cost more than one focused run. A timeout triggers a named evidence gap; it does not authorize invented customer impact. Review both final briefs against one held-out rubric covering observed facts, hypothesis language, snapshot alignment, tool scope, and partial-result handling. Retain traces and the final claim ledger so a later correction can be tied to its source packet.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not present a before-and-after timeline as causal proof.</li><li>Do not merge a support result from an older snapshot.</li><li>Do not let a specialist with read-only scope deploy a proposed fix.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Compare a single-agent incident brief with bounded specialists and a claim-level merge gate.", project_body, projects, 60, project_connections, kind="project"))

questions = [
    ("What establishes whether specialists helped?", "A same-task single-agent baseline with matched checks", "A longer final response", "The number of specialist names", "Compare quality, cost, and latency on the same cases."),
    ("Which tasks can run in parallel?", "Independent evidence reads on the same named snapshot", "A write that needs an unreturned approval", "A dependent step before its input exists", "Parallel work needs independent inputs."),
    ("What belongs in a specialist task packet?", "Question, artifact version, tools, authority, output, deadline", "Only a role label", "The entire unfiltered history", "A bounded packet makes the work checkable."),
    ("Can a prompt saying 'read only' disable a write-capable tool?", "No; the runtime must enforce permission", "Yes, always", "Only when several agents agree", "Text instructions are not an access-control boundary."),
    ("A release specialist uses PK-211 while others use PK-214. What next?", "Hold and rerun or reconcile the stale result", "Blend the summaries", "Choose the more confident agent", "Version mismatch must be resolved before synthesis."),
    ("Two agents propose edits to one deployment manifest. What prevents lost updates?", "One assigned writer and a version-checked merge", "A request to be careful", "More parallel edits", "Shared writes need ownership and conflict checks."),
    ("A claim cites a real evidence ID. Is its meaning proven?", "No; inspect whether that evidence supports the statement", "Yes, membership proves support", "Yes, if another agent agrees", "Reference membership is only a first gate."),
    ("Three agents repeat the same false assumption. What does majority vote prove?", "Nothing about independent evidence", "That causation is certain", "That the snapshot is current", "Shared assumptions can propagate through all agents."),
    ("RC-47 preceded a rise in errors. What wording is justified now?", "A candidate mechanism requiring verification", "RC-47 definitely caused every error", "No relationship is possible", "Temporal order alone does not establish cause."),
    ("Support review times out before confirming contacts. What should the brief say?", "Customer-contact evidence is incomplete", "Invent a likely count", "Copy an older number silently", "Missing results remain visible as gaps."),
    ("A write-capable tool times out after submission. What before retry?", "Check the effect receipt or current state", "Retry immediately", "Assume no side effect occurred", "Timeout does not prove the action did not happen."),
    ("What should a multi-agent evaluation inspect besides the final prose?", "Tool scope, snapshots, evidence claims, timeouts, and effects", "Only sentence style", "Only agent count", "A fluent answer can hide a broken trajectory."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-multimodal-evidence"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                  path=quiz_path, title=titles[quiz_path],
                  summary="Test delegation, task packets, shared state, claim synthesis, and timeout decisions.",
                  body="<p>Choose the action that keeps specialist work bounded and its merged answer grounded.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, production, quizzes]),
                  sort_order=29470, status="published", published_at=stamp,
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
    (applications, paths[:4], "Specialist-agent coordination", "Compare delegation against a baseline, scope packets, align state, and reconcile claims."),
    (production, paths[4:], "Specialist run release gate", "Bound timeouts and retries, review the trace, and name missing results."),
    (projects, [project_path], "Parcel-platform specialist review", "Combine independent incident findings without claiming unverified causation."),
    (quizzes, [quiz_path], "Specialist coordination decisions", "Test agent scope, merge conflicts, and lifecycle limits."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

root_hub = lookup[subject_root]
root_hub["body"] += "<h2>Specialist-agent coordination</h2><p>Delegate only when measured, give each specialist an explicit contract, and merge evidence with state and effect checks.</p>" + links(paths + [project_path, quiz_path])
root_hub["updated_at"] = stamp

backlinks = {
    "prompt-engineering/task-decomposition-and-handoffs": paths[0],
    "prompt-engineering/parallel-tool-dependency-plan": paths[2],
    "prompt-engineering/tool-call-authorization-contract": paths[1],
    "prompt-engineering/evidence-id-traceability": paths[3],
    "prompt-engineering/incident-log-timeline-triage": project_path,
    "prompt-engineering/side-effect-receipt-reconciliation": paths[4],
    "prompt-engineering/prompt-trace-observability": paths[4],
    "prompt-engineering/prompt-release-review-packet": project_path,
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
