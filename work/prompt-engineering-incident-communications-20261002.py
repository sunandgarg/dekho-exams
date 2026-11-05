"""Add original incident-communication prompt lessons, project, and quiz."""

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
project_path = "prompt-engineering/harbor-checkout-incident-update-project"
quiz_path = "quizzes/prompt-engineering-incident-communications"

specs = [
    {
        "slug": "incident-update-audience-owner-and-release-gate",
        "title": "Incident updates: audience, owner, and release gate",
        "summary": "Give each update a reader, evidence owner, approval path, and publishing boundary.",
        "definition": "An incident-update prompt is a draft contract, not permission to publish. It identifies the audience, communication channel, incident commander, evidence owner, approval route, timestamp, and next-update commitment. An internal handoff may include diagnostic hypotheses and operator actions; a public update should describe confirmed user impact and current action without exposing credentials, customer identifiers, or speculative causes. Require the drafting assistant to label missing facts instead of filling them with plausible language. The person who can approve an update should be explicit, because polished text can move faster than the incident team can verify it.",
        "case": "A fictional Harbor Checkout service starts rejecting some checkout API attempts. The incident commander owns the operational decision; a communications lead drafts a customer status update from an approved metric snapshot and current action log. The draft says which checkout path is affected and when the next update is due. It does not claim all purchases fail, name a suspected dependency as the cause, or send anything to the status page. The commander reviews the exact text and snapshot before a human publisher releases it. A new metric window or major operational change requires a fresh draft and review.",
        "sample": "Audience: checkout customers; channel: status page draft only.\nEvidence owner: metrics lead; approval: incident commander.\nImpact: checkout API failures in the measured 14:00-14:10 UTC window.\nCause: unconfirmed; do not guess.\nNext update: 14:30 UTC, or sooner on a material change.\nNo status-page write without explicit release approval.",
        "cost": "Drafting from E checked facts is O(E) reading and comparison work; approval adds human latency but prevents a plausible draft from becoming a false public claim. Keep internal and public views separate so the public context stays small and disclosure risk stays bounded. A model can produce several audience variants quickly, yet every variant needs the same evidence version and approval record. Publishing tools must remain outside the drafting prompt unless a separately authorized workflow supplies them.",
        "mistakes": ["Do not treat a generated draft as a sent update.", "Do not copy an internal hypothesis into a public cause statement.", "Do not publish a later metric window under an earlier approval."],
        "related": ["prompt-engineering/tool-call-authorization-contract", "prompt-engineering/time-sensitive-research-contract", "devops/incident-response"],
        "section": applications,
    },
    {
        "slug": "incident-impact-window-denominator-and-scope",
        "title": "Incident impact: window, denominator, and scope",
        "summary": "Make every impact number reproducible before placing it in an update.",
        "definition": "An impact statement needs a measurement window, population, unit, numerator, denominator, and source identity. A rate without a denominator invites readers to assume that every customer or request is affected. The prompt should ask whether retries, synthetic traffic, duplicate attempts, and delayed records are counted. Report measured attempts as attempts, not people. If a snapshot is incomplete, say it is preliminary and avoid a false precision. When several regions or payment paths differ, preserve their scope rather than averaging away a concentrated failure. The incident team should be able to reproduce the arithmetic from the frozen snapshot used for approval.",
        "case": "Harbor's metrics lead freezes the 14:00-14:10 UTC checkout API window. It contains 18,600 attempts and 3,720 failed attempts, so the failure share is 3,720 divided by 18,600, or 20%. The numerator is failed checkout API attempts; the denominator is all checkout API attempts in that ten-minute window. This does not mean 20% of customers failed to buy, because one customer may retry and the snapshot says nothing about later completion. The public draft says 'about one in five checkout attempts failed during the measured window' only after the lead confirms the counter definitions and ingestion completeness.",
        "sample": "Window: 14:00-14:10 UTC.\nPopulation: checkout API attempts in the measured service.\nFailed attempts: 3,720; total attempts: 18,600.\nRate: 3,720 / 18,600 = 0.20 = 20%.\nDo not translate attempts into affected customers.\nSnapshot ID: HC-1410; counters and ingestion checked by metrics lead.",
        "cost": "For N event records, a direct count is O(N) time and O(1) aggregate memory; a precomputed metrics snapshot can reduce query time but adds ingestion and label-validation work. A single numerator and denominator are cheap to compute, while checking retries and missing telemetry takes longer. Freeze the window and snapshot ID in the draft so later recomputation does not silently change an already approved statement. If telemetry is incomplete, publish the bounded observation rather than a precise percentage that the team cannot defend.",
        "mistakes": ["Do not describe request attempts as distinct customers.", "Do not combine a numerator from one window with a denominator from another.", "Do not imply a measured rate covers an unmeasured region or path."],
        "related": ["prompt-engineering/aggregate-denominator-reconciliation", "prompt-engineering/evidence-id-traceability", "devops/incident-response"],
        "section": applications,
    },
    {
        "slug": "incident-facts-hypotheses-eta-and-update-clock",
        "title": "Incident updates: separate facts, hypotheses, and ETA",
        "summary": "State what is observed, what is being tested, and when the next update will arrive.",
        "definition": "A time-sensitive incident prompt should maintain three distinct fields: confirmed observation, working hypothesis, and planned action. Only evidence-backed observations belong in a public fact statement. A hypothesis can guide internal triage without becoming an announced root cause. An ETA is a forecast with assumptions; if no defensible restoration time exists, give the next update time rather than inventing a fix time. Record timestamps with a timezone and specify whether an action is planned, started, completed, or verified. A rollback command beginning is not the same as user recovery. The next-update clock remains useful even when the diagnosis changes.",
        "case": "At 14:12 UTC Harbor knows the checkout API failure rate in the earlier measured window, while a recently deployed change is only one possible cause. The public draft states the observed checkout impact and that the team is investigating. At 14:16 UTC an operator starts a rollback; the next draft says rollback is underway, not that service is restored. Later, a fresh metric window and a synthetic checkout both pass, and the incident commander decides whether recovery can be announced. The team commits to another update at 14:30 UTC even if investigation is still open. No model-generated ETA replaces that promise.",
        "sample": "Confirmed: checkout API failures measured in HC-1410.\nHypothesis: recent deployment may be involved; internal only.\nAction: rollback started at 14:16 UTC; outcome pending.\nPublic wording: investigating elevated checkout failures.\nNext update: 14:30 UTC; no restoration ETA yet.\nRecovery requires fresh metrics and checkout-path verification.",
        "cost": "Checking F facts against E evidence items is O(F+E) when evidence IDs are indexed, plus time to query new windows. This separation increases drafting discipline but prevents repeated correction of confident, unsupported claims. Scheduling an update is cheap; meeting it needs an owner and a fallback message if the situation is unchanged. Do not wait for a perfect root cause before issuing a time-bound update, and do not substitute a tool's success response for observed customer recovery.",
        "mistakes": ["Do not turn a suspected deployment into a confirmed cause.", "Do not equate rollback start with restored checkout service.", "Do not invent a restoration ETA to fill a template."],
        "related": ["prompt-engineering/time-sensitive-research-contract", "prompt-engineering/incident-log-timeline-triage", "devops/incident-response"],
        "section": applications,
    },
    {
        "slug": "incident-internal-handoff-and-decision-ledger",
        "title": "Incident handoffs: preserve actions and decisions",
        "summary": "Transfer evidence, owner, action state, and open risks without rewriting the timeline.",
        "definition": "An internal incident handoff prompt should produce a decision ledger with event time, author, evidence ID, current owner, action state, unresolved question, and next check. It is more than a prose recap. The incoming responder needs to know which commands were requested, which actually ran, which receipts exist, and which changes must not be repeated. Keep raw customer data and credentials out of the handoff; link to controlled records by internal identifier when authorized. Preserve uncertainty and corrections. If a timestamp is missing, mark it missing rather than sorting an inferred event into a fabricated sequence.",
        "case": "Harbor's first responder hands off at 14:20 UTC. The ledger records snapshot HC-1410, rollback start at 14:16, the operator receipt showing deployment traffic switched, and the still-open question of whether error rates have returned to baseline. The next owner must query a later window and run a representative checkout before marking recovery. A short public update can omit internal deployment detail, but the handoff cannot. It also records the approved 14:30 update commitment, so the next communications lead does not miss it while debugging. The model drafts the ledger; the outgoing and incoming responders verify action states together.",
        "sample": "14:10 UTC | HC-1410 | 3,720/18,600 failed attempts | verified.\n14:16 UTC | rollback started | operator action | receipt pending.\n14:20 UTC | traffic switch receipt recorded | not recovery proof.\nOwner: incoming incident commander.\nOpen: later-window rate and synthetic checkout.\nCommunication commitment: next public update by 14:30 UTC.",
        "cost": "Maintaining a ledger of A actions is O(A) append work; verifying a handoff is O(A) for the active slice, not the whole historical incident. A compact evidence index reduces repeated searches while preserving links to full controlled records. Timezone normalization is a small extra cost that prevents action-order mistakes. Avoid copying entire logs into the prompt: a task-scoped event slice is cheaper to review and less likely to disclose user data or bury the next required action.",
        "mistakes": ["Do not mark a requested command as executed without a receipt.", "Do not erase a mistaken update; record its correction and time.", "Do not omit the next public-update commitment from the handoff."],
        "related": ["prompt-engineering/incident-log-timeline-triage", "prompt-engineering/side-effect-receipt-reconciliation", "devops/incident-review-actions"],
        "section": production,
    },
    {
        "slug": "incident-resolution-correction-and-review-gate",
        "title": "Incident resolution: verify recovery and correct the record",
        "summary": "Require independent recovery checks and carry corrections into the incident review.",
        "definition": "A resolution prompt should require a clear recovery criterion, observation window, evidence owner, and approval before drafting 'resolved.' Check current metrics and representative customer behavior, not merely the completion of a rollback or deployment. If an earlier public number, time, or cause was wrong, issue a correction with its own timestamp rather than silently editing history. A later incident review should distinguish the immediate trigger from contributing factors and list action owners with verifiable completion checks. Do not promise that recurrence is impossible. The final public update can state restored behavior while leaving deeper causal analysis for a reviewed follow-up.",
        "case": "Harbor's rollback finishes, but the incident remains open until a later checkout API window is within the agreed baseline and a synthetic checkout succeeds. The incident commander approves a resolution draft after checking both results and the operational receipt. If the earlier 20% metric is revised because a counter included synthetic attempts, the communications lead labels the correction and states the revised denominator; the earlier message is not silently overwritten. The review links the metric snapshot, rollback receipt, checkout test, public update approvals, and follow-up owners. A model can assemble the packet, but it cannot close the incident by declaring its own answer correct.",
        "sample": "Recovery gate: later failure rate within agreed baseline.\nBehavior gate: synthetic checkout succeeds end to end.\nAction gate: rollback receipt and actual traffic state match.\nApproval: incident commander reviews the exact resolution draft.\nCorrection: timestamp any revised impact metric and reason.\nReview: assign owner, due date, and completion evidence per action.",
        "cost": "For V independent checks and U published updates, closure review is O(V+U) plus the observation window needed to catch relapse. A synthetic checkout tests one path, so it cannot replace metrics across all affected traffic. Preserving corrections and receipts uses storage and review time, yet it makes later analysis reproducible. Post-incident actions should be few enough to verify: a long unowned list creates work without reducing the failure mode the team actually observed.",
        "mistakes": ["Do not declare resolution from a rollback receipt alone.", "Do not silently replace an inaccurate earlier impact statement.", "Do not close review actions without an owner and completion evidence."],
        "related": ["prompt-engineering/prompt-release-review-packet", "prompt-engineering/side-effect-receipt-reconciliation", "devops/incident-review-actions"],
        "section": production,
    },
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]).intersection(lookup)
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: draft Harbor Checkout incident updates"
titles[quiz_path] = "Incident-communication prompt decisions"


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
                 difficulty="Advanced", tags=["prompt engineering", "incident communication"],
                 sort_order=30300 + order, status="published", published_at=stamp,
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

project_connections = paths + ["prompt-engineering/incident-log-timeline-triage", "prompt-engineering/aggregate-denominator-reconciliation", "devops/incident-response", "devops/incident-review-actions", quiz_path]
project_body = (
    "<p>Prepare an incident-communication packet for fictional Harbor Checkout. The checkout API snapshot HC-1410 covers 14:00-14:10 UTC: 3,720 failures among 18,600 attempts, exactly 20% of measured attempts. The project produces a public draft, an internal handoff, a recovery gate, and a correction route. It does not publish a status message or operate the checkout service. An incident commander must approve the exact external wording after the metrics lead verifies its source.</p>"
    "<h2>Draft the first update</h2><p>State that elevated checkout failures are under investigation. Name the affected API path and measured window. Do not translate attempts into unique customers, claim that every transaction failed, assign a root cause, or offer a restoration time without evidence. Put the next update at 14:30 UTC. A recent deployment is an internal hypothesis, not a public fact. The communications lead drafts from HC-1410; the incident commander checks the text and a human publisher controls the status page.</p>"
    "<h2>Record action without declaring recovery</h2><p>At 14:16 UTC an operator starts a rollback. The handoff records its receipt and the next owner, but it keeps customer recovery open. A later window must return to the agreed baseline, and a synthetic checkout must succeed before the commander approves a resolution draft. If the metric definition changes after publication, timestamp a correction with the revised numerator, denominator, and reason. The incident review retains the earlier draft, approvals, receipts, corrected impact, and owners for follow-up work.</p>"
    '<pre><code class="language-text">HC-1410: 3,720 failed / 18,600 checkout API attempts = 20%.\n14:12 UTC public draft: investigating measured checkout failures.\n14:16 UTC rollback starts; recovery is not yet confirmed.\n14:20 UTC handoff: receipt, owner, open checks, 14:30 update.\nResolution: later metric window plus synthetic checkout plus approval.\nCorrection: timestamp any changed count; preserve earlier record.</code></pre>'
    "<h2>Performance and operating cost</h2><p>Counting N raw events is O(N) time and O(1) aggregate memory; validating counter definitions, ingestion, and retries costs additional operator work. A handoff over A active actions is O(A) review. The two recovery checks test different failure modes, while the observation window catches a relapse that a single synthetic request could miss. Approval delays publication slightly, but prevents an unverified draft from becoming a customer-facing claim. Use compact evidence IDs instead of copying sensitive logs into every prompt.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not call the 20% attempt rate a customer rate.</li><li>Do not publish the internal deployment hypothesis as root cause.</li><li>Do not mark the service restored when the rollback only starts.</li><li>Do not erase a wrong update; issue a timestamped correction.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Draft measured updates, preserve the action ledger, and gate resolution on evidence.", project_body, projects, 60, project_connections, kind="project"))

questions = [
    ("Who approves Harbor's exact public update?", "The incident commander", "The drafting model", "Any on-call reader", "The external text has an explicit approver."),
    ("What does HC-1410 measure?", "Checkout API attempts in the 14:00-14:10 UTC window", "Distinct customers across the day", "All payment systems", "The scope and window bind the number."),
    ("What is 3,720 divided by 18,600?", "20%", "2%", "50%", "The numerator is one fifth of the denominator."),
    ("May the update call 20% an affected-customer rate?", "No, attempts may include retries", "Yes, attempts equal customers", "Only if the text is short", "The population is attempts, not people."),
    ("How should a recent deployment be presented before cause is verified?", "As an internal hypothesis", "As confirmed public root cause", "As a restoration ETA", "Triage possibilities are not confirmed facts."),
    ("What can the public update promise without a defensible fix ETA?", "A next-update time", "Guaranteed restoration at 14:30", "No further communication", "A time-bound update is distinct from a recovery forecast."),
    ("What does rollback start at 14:16 UTC prove?", "An action began, not that checkout recovered", "Every checkout succeeded", "The root cause was confirmed", "Action status and user outcome require different evidence."),
    ("What belongs in the internal handoff?", "Owner, action state, receipt, open checks, and update commitment", "Only polished public prose", "Raw credentials", "The next responder needs operational state."),
    ("What makes an action executed rather than merely proposed?", "An operator or tool receipt", "A model prediction", "A checklist item", "A side effect needs external evidence."),
    ("What gates the resolution draft?", "Later metrics, a representative checkout, and commander approval", "Rollback start alone", "An earlier snapshot", "Independent checks cover distinct failure modes."),
    ("What should happen if the published denominator is later corrected?", "Issue a timestamped correction with the revised basis", "Silently overwrite history", "Leave the false number unmarked", "The record should preserve what changed and why."),
    ("May a drafting prompt send the status-page update by itself?", "No; publication requires a separate authorized action", "Yes, if the wording is fluent", "Yes, if the model repeats the command", "Drafting and publishing are distinct capabilities."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-multimodal-evidence"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                  path=quiz_path, title=titles[quiz_path],
                  summary="Test audience approval, impact arithmetic, action state, recovery, and corrections.",
                  body="<p>Choose the incident-communication decision supported by the measured evidence and release gate.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, production, quizzes]),
                  sort_order=30370, status="published", published_at=stamp,
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
    (applications, paths[:3], "Incident update prompts", "Bound audience, impact arithmetic, facts, and the next update clock."),
    (production, paths[3:], "Incident handoff and closure", "Keep an action ledger, verify recovery, and correct earlier claims."),
    (projects, [project_path], "Harbor Checkout incident packet", "Draft measured updates and gate recovery on actual service evidence."),
    (quizzes, [quiz_path], "Incident communication decisions", "Test denominators, hypotheses, action receipts, and release authority."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

root_hub = lookup[subject_root]
root_hub["body"] += "<h2>Incident communication reviews</h2><p>Separate audience, measurable impact, action state, and confirmed recovery.</p>" + links(paths + [project_path, quiz_path])
root_hub["updated_at"] = stamp

backlinks = {
    "prompt-engineering/incident-log-timeline-triage": paths[3],
    "prompt-engineering/evidence-id-traceability": paths[1],
    "prompt-engineering/aggregate-denominator-reconciliation": paths[1],
    "prompt-engineering/time-sensitive-research-contract": paths[2],
    "prompt-engineering/prompt-release-review-packet": paths[4],
    "prompt-engineering/side-effect-receipt-reconciliation": paths[3],
    "devops/incident-response": paths[0],
    "devops/incident-review-actions": paths[4],
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
