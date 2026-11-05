"""Add standalone prompt lessons for recurring AI workflows."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "src/data/fixtures.json"
entries = json.loads(FIXTURE.read_text())
lookup = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
root_path = "prompt-engineering/prompt-engineering"
applications = "prompt-engineering/applications"
production = "prompt-engineering/production"
projects = "prompt-engineering/projects"
quizzes = "prompt-engineering/quizzes"
project_path = "prompt-engineering/depot-watch-recurring-review-project"
quiz_path = "quizzes/prompt-engineering-recurring-workflows"

specs = [
    dict(slug="recurring-task-intent-and-stop-condition", title="Recurring prompts: define the trigger and stop condition", section=applications,
         summary="Distinguish a one-time follow-up from a repeated task and define when it should stop.",
         definition="A recurring-task prompt is a saved instruction that runs again when a scheduler invokes it. Specify the user decision it serves, its cadence, the permitted data scope, the output artifact, and a stopping condition. 'Keep an eye on shipments' is not an executable contract: the task could check once, monitor every minute, or send a message after every unchanged run. Separate the schedule from the task body. The scheduler decides when to invoke; the prompt decides what to inspect and how to report a result. Confirm that the named dataset and destination will still be available on later runs.",
         case="A fictional depot manager wants a morning review of held parcels for North Pier. The run compares the current held set with the prior confirmed snapshot and flags new holds, released holds, and records whose status cannot be verified. It stops after the 30-day pilot or when the manager cancels it. The prompt names the North Pier depot and limits itself to read-only shipment data. It does not infer permission to rebook shipments or contact customers from the word 'review'.",
         sample="Task: review North Pier held parcels at each scheduled run.\nWindow: current snapshot against last confirmed run.\nOutput: changed records, unresolved records, run time, and evidence IDs.\nStop: end of 30-day pilot or manager cancellation.\nAllowed: read shipment status. Forbidden: rebook or notify customers.",
         cost="A run over N shipment records costs O(N) for a full comparison, or O(C) when a trustworthy change feed exposes C changed records. Retaining a small prior snapshot has O(N) storage cost; this must be weighed against missing changes when the feed is incomplete. A vague schedule can create unbounded model calls and duplicate notifications. Bound both run frequency and the period for which the task remains active.",
         mistakes=["Do not convert 'check tomorrow' into an indefinite daily task.", "Do not treat a reporting instruction as permission to change shipments.", "Do not omit the end condition for a pilot workflow."],
         related=["prompt-engineering/task-contract", "prompt-engineering/clarification-versus-assumption-gate", "prompt-engineering/tool-call-authorization-contract"]),
    dict(slug="recurring-task-timezone-and-window-contract", title="Recurring prompts: bind local time and data windows", section=applications,
         summary="Make the schedule's time zone, cutoff, and reporting window explicit.",
         definition="A repeated task needs two different clocks: the scheduled invocation time and the period of data the run examines. Record a named time zone, the user's intended local hour, the window start and end, and how to handle late-arriving records. Calendar time and a fixed number of elapsed hours are different contracts. Daylight-saving changes, holidays, and missed runs can alter what 'yesterday' means. The prompt should receive resolved timestamps from the scheduler or application, then state them in the output. It must not calculate an authoritative billing or operations window by guessing from the model's own clock.",
         case="North Pier's review runs at 08:15 in the depot's local time. The reporting window ends at the previous local midnight, so an 08:15 run does not silently include morning updates that have not yet settled. A late scan may arrive after the cutoff; the next run marks it as a revision to an earlier window rather than quietly rewriting yesterday's report. The application supplies the exact start and end instants and the time-zone identifier. If the schedule misses a day, the run reports the uncovered interval before computing changes.",
         sample="Local schedule: 08:15, depot time zone.\nResolved data window: [start instant, end instant).\nLate scan: label as revision to prior window.\nMissed run: identify uncovered interval before comparison.\nEvery report prints resolved cutoff and invocation time.",
         cost="Window filtering is O(N) without an index on event time and closer to O(log N + W) for W matching events with a suitable index. Explicit time windows add a small amount of prompt text but prevent costly duplicate or missing record reviews. A zero-length or overlapping interval is a validation error. Test local-time transitions against the actual scheduler because providers differ in how they handle a clock hour that is skipped or repeated.",
         mistakes=["Do not use the model's current date as the only source of a reporting cutoff.", "Do not assume a daily schedule always spans exactly 24 elapsed hours.", "Do not hide a missed interval behind a normal-looking report."],
         related=["prompt-engineering/time-sensitive-research-contract", "prompt-engineering/retrieval-freshness-and-conflict", "prompt-engineering/incident-impact-window-denominator-and-scope"]),
    dict(slug="recurring-run-freshness-and-empty-state", title="Recurring prompts: validate fresh inputs and empty states", section=applications,
         summary="Reject stale snapshots and distinguish no changes from no data.",
         definition="A scheduled prompt often starts without a person present to notice a missing attachment or a stale cache. Require each input to carry a source, collection timestamp, coverage interval, and retrieval status. An empty set from a successful query can mean no matching records. An empty set caused by a failed query means unknown. These states need different output. Set an age limit for data and a completeness threshold for expected partitions before generating a normal report. A model cannot repair a missing source by producing a plausible zero count.",
         case="At 08:15 the North Pier status endpoint returns zero held parcels, but its refresh timestamp is two days old. The previous verified snapshot contained 47 held records. Reporting 'all 47 released' would be false. The run marks the source stale and requests operator attention. On another day a fresh response returns an empty set with all expected partitions present; only then may the report state that no held parcels were found in that verified window. The evidence packet preserves which path produced each result.",
         sample="Query status: success; snapshot age: 49 hours; limit: 3 hours.\nResult count: 0; previous verified held count: 47.\nDecision: stale source, state unknown; no release claim.\nFresh zero with complete partitions: verified empty set.\nFailure to query: unavailable, never zero.",
         cost="Checking P source partitions takes O(P) metadata reads before content analysis; a full reconciliation may add O(N) record work. The gate can delay a report, yet the alternative is a confidently wrong operational statement. Keep staleness limits tied to the business decision, not to a universal number. Log source IDs and timestamps without copying unnecessary customer fields into the prompt or telemetry.",
         mistakes=["Do not translate a failed query into a zero result.", "Do not compare a stale snapshot with a fresh one as though both were current.", "Do not bury a missing partition in an average-quality score."],
         related=["prompt-engineering/retrieval-freshness-and-conflict", "prompt-engineering/selective-prediction-thresholds", "prompt-engineering/prompt-telemetry-privacy-budget"]),
    dict(slug="recurring-run-idempotency-and-retry-boundary", title="Recurring prompts: survive retries without duplicate effects", section=production,
         summary="Tie every run to a stable identity and reconcile uncertain side effects.",
         definition="Schedulers may retry an invocation after a timeout even when the first attempt partly succeeded. Give the run a stable identity based on schedule and intended window, then record stage receipts outside the model. A retry can recompute a read-only summary, but sending the same message or editing the same record twice may be harmful. The prompt should ask for the existing receipt before proposing another effect. Idempotency belongs in the application and destination API; a sentence saying 'do this only once' does not enforce it. After an ambiguous result, query the authoritative destination before retrying.",
         case="North Pier's report is generated for window W-47. The first attempt saves the draft but times out before the scheduler gets a response. A retry with the same run identity finds draft receipt R-47 and continues from that artifact, rather than creating a second draft. If a notification send times out, the system checks the message destination for the idempotency key before attempting another send. The prompt may describe the uncertainty, but it cannot declare delivery based on its own prior text.",
         sample="Run identity: north-pier / W-47 / review-v3.\nDraft stage: receipt R-47 already exists -> reuse.\nNotification stage: outcome unknown -> query destination by key.\nDuplicate receipt found -> do not send again.\nNo authoritative result -> hold and escalate.",
         cost="A keyed receipt lookup is O(1) average in an indexed store. A retry adds latency and possibly another model call, so resume from verified stages where possible. Stable run keys reduce duplicate side effects and make cost attribution easier. Keep an expiry rule for idempotency records longer than the maximum retry horizon; otherwise a delayed retry can bypass the deduplication window.",
         mistakes=["Do not invent a fresh run ID for each retry of the same scheduled window.", "Do not assume a timeout proves the effect failed.", "Do not rely on prompt wording as the only duplicate-send control."],
         related=["prompt-engineering/side-effect-receipt-reconciliation", "prompt-engineering/browser-effect-receipt-and-recovery", "prompt-engineering/tool-loop-stop-rules"]),
    dict(slug="recurring-task-notification-threshold-and-noise", title="Recurring prompts: notify only on actionable changes", section=production,
         summary="Separate routine run records from user-facing alerts and suppress unchanged noise.",
         definition="Notification policy is part of a recurring task's output contract. Define what counts as a meaningful change, the severity threshold, the destination, and a quiet path when nothing actionable changes. Preserve an audit record for every run without sending that record to the user each time. Group related events within a stated window and de-duplicate alerts by case identity. A missing data source may warrant a failure alert even when no business event is confirmed. The prompt classifies candidate messages; the delivery layer enforces channel rules and user preferences.",
         case="North Pier sees the same six held parcels across three morning runs. The run ledger records all three checks, but the manager receives no repeated alert. A seventh parcel becomes held with a verified scan, so one alert names the new record and its evidence. A failed endpoint on the following morning produces a distinct source-failure notice rather than claiming another parcel change. If the manager muted routine changes but not failures, the trusted notification service applies that preference.",
         sample="No verified change -> record run; no user notification.\nNew hold H-71 -> one actionable alert with evidence ID.\nSame H-71 next run -> suppress duplicate alert.\nSource unavailable -> failure notice, not a hold count.\nChannel and mute settings -> enforced by delivery service.",
         cost="Comparing current and prior sets is O(N) with hash keys and O(N) storage for the snapshots. Alert grouping adds a small keyed state store, but reduces review time and notification fatigue. A high threshold can miss emerging incidents; a low threshold can overwhelm the user. Evaluate precision, missed critical events, and alerts per week on held-out windows, then set a documented threshold rather than letting the model improvise one per run.",
         mistakes=["Do not send the unchanged run ledger as a fresh alert.", "Do not suppress a source failure because no changed business record was found.", "Do not let model prose override a user's channel or mute settings."],
         related=["prompt-engineering/online-prompt-experiment-stop-rules", "prompt-engineering/incident-update-audience-owner-and-release-gate", "prompt-engineering/memory-write-intent-and-durable-fact-gate"]),
    dict(slug="recurring-task-approval-and-authority-renewal", title="Recurring prompts: renew authority for sensitive actions", section=production,
         summary="Keep scheduled checks read-only until each effect has current authorization.",
         definition="An instruction saved months ago is not a permanent grant to perform every later action. Divide recurring work into observation, recommendation, draft creation, and external effect. The trusted application grants each category separately and can revoke it. If a run proposes a sensitive effect, the prompt must produce a reviewable proposal tied to fresh evidence and request an approval bound to that exact effect. A prior approval for another window, recipient, or amount does not transfer. Recheck access at each run; a user who lost permission must not inherit it through an old schedule.",
         case="The North Pier manager authorized read-only daily reviews, not customer emails. A held parcel may merit an outreach recommendation, but the assistant saves a draft with shipment ID, reason, and proposed recipient; no message is sent. A supervisor can approve a specific draft after checking current shipment status. If the status changes before approval, the draft expires and requires a fresh review. If the manager's depot access is revoked during the pilot, later scheduled runs stop reading that depot's records.",
         sample="Scheduled authority: read North Pier status only.\nCandidate outreach: draft D-71 with current evidence.\nEffect: send requires supervisor approval bound to D-71.\nStatus changes before approval -> expire D-71.\nDepot access revoked -> stop future reads.",
         cost="Per-run authorization and pre-effect rechecks add lookup latency, generally O(1) for indexed identity and record checks. Draft review creates human work, so reserve it for genuinely consequential effects. A stale approval is more expensive than a missed automation: it can send the wrong message to the wrong person. Log the approval identity and effect receipt without storing unrelated customer data in the prompt trace.",
         mistakes=["Do not treat a saved schedule as permanent consent for future effects.", "Do not reuse approval from a different draft or reporting window.", "Do not rely on the model to enforce revoked access."],
         related=["prompt-engineering/tool-call-authorization-contract", "prompt-engineering/browser-form-preview-submit-boundary", "prompt-engineering/retrieval-identity-and-document-permission-gate"]),
    dict(slug="recurring-task-replay-and-run-audit", title="Recurring prompts: make every run replayable and auditable", section=production,
         summary="Record the exact inputs, prompt version, decisions, and receipts needed to explain a run.",
         definition="A run audit connects the scheduler event to the data snapshot, prompt and model version, validation results, output artifact, notification decision, and any effect receipts. Store identifiers and hashes where full payload retention is unnecessary. Replaying a run means using the same approved input snapshot and versions in a controlled environment; it does not guarantee identical model wording. Compare decision fields and critical claims against a reference oracle. Keep failed and skipped runs, since excluding them creates a misleading success rate. Separate an attempted run from a verified completed outcome.",
         case="The manager disputes an alert about parcel H-71. The team retrieves run identity W-47, snapshot hash S-47, prompt version review-v3, validation status, and alert receipt A-71. A replay on that frozen snapshot reproduces the decision to flag a new hold, while a later live query shows the parcel was released after the original cutoff. The team corrects the present-day state without rewriting the historical report. Another run that failed to fetch partition P-4 remains visible as incomplete, not counted as a successful no-change run.",
         sample="Run W-47: schedule event, window, snapshot S-47, prompt review-v3.\nValidation: all expected partitions present.\nDecision: new hold H-71; alert receipt A-71.\nReplay: frozen S-47, compare decision fields.\nLater release: new fact, not a rewrite of W-47.\nFailed P-4 run: incomplete and visible.",
         cost="Writing a compact ledger row per run is O(1); retaining full snapshots can be O(NR) over N records and R runs, so use retention limits and content-addressed storage where appropriate. Replay costs another model call and possibly validation work. It is most useful for disputed decisions and release regressions, not routine unchanged checks. Count failed, skipped, and duplicate attempts explicitly when reporting reliability.",
         mistakes=["Do not claim byte-for-byte model reproduction from a replay.", "Do not remove failed runs from the denominator of reliability metrics.", "Do not overwrite old evidence when a later status changes."],
         related=["prompt-engineering/prompt-trace-observability", "prompt-engineering/evaluation-case-version-ledger", "prompt-engineering/prompt-release-artifact-bundle"]),
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]) & lookup.keys()
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: build a North Pier recurring review"
titles[quiz_path] = "Recurring prompt workflow decisions"


def link(path):
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(path_list):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(path_list)) + "</ul>"


def related(path_list):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(path_list)]


def make_article(path, title, summary, body, section, order, connections, kind="tutorial"):
    entry = copy.deepcopy(lookup["prompt-engineering/evaluation-slice-design"])
    subjects = {applications: "prompt-engineering-applications", production: "prompt-engineering-production", projects: "prompt-engineering-project"}
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path, title=title,
                 summary=summary, body=body, subject=subjects[section], difficulty="Advanced",
                 tags=["prompt engineering", "recurring workflows"], sort_order=30700 + order,
                 status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
    entry["data"].update(kind=kind, reading_minutes=11 if kind == "tutorial" else 18,
                         author_path="authors/aitrove-editorial", subject_root=root_path,
                         section_path=section, content_format="html", seo_ready=True,
                         related=related(connections))
    return entry


new_rows = []
for index, (path, spec) in enumerate(zip(paths, specs)):
    connections = [spec["section"], root_path] + spec["related"] + [other for other in paths if other != path] + [project_path, quiz_path]
    body = ("<p>" + html.escape(spec["definition"]) + "</p>"
            + "<h2>Operational case</h2><p>" + html.escape(spec["case"]) + "</p>"
            + '<pre><code class="language-text">' + html.escape(spec["sample"], quote=False) + "</code></pre>"
            + "<h2>Performance and operating cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
            + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in spec["mistakes"]) + "</ul>"
            + "<h2>Connected lessons</h2>" + links(connections))
    new_rows.append(make_article(path, spec["title"], spec["summary"], body, spec["section"], index * 10, connections))

project_connections = paths + ["prompt-engineering/side-effect-receipt-reconciliation", "prompt-engineering/prompt-evaluation-ci-gate", quiz_path]
project_body = (
    "<p>Design a recurring North Pier depot review for a fictional 30-day pilot. At 08:15 local time each day, it compares the last settled reporting window with the previous verified snapshot. It can read parcel status and create a draft report. It cannot rebook shipments or contact customers. The deliverable is a schedule contract, a run prompt, a validation gate, an alert policy, and a replayable audit row. This project describes a workflow; it does not create a live schedule or send a message.</p>"
    "<h2>Specify the run</h2><p>The scheduler supplies resolved start and end instants, local time-zone identity, and stable run key. The application supplies a fresh status snapshot with its collection time and partition manifest. The prompt classifies new holds, released holds, and unresolved records only after the freshness and completeness gate passes. A stale empty response remains unknown. If one day is missed, the next run identifies the uncovered interval rather than silently merging it with today's window.</p>"
    "<h2>Constrain effects and alerts</h2><p>For window W-47, six held parcels are unchanged and H-71 becomes newly held. The run writes a draft and emits one alert candidate about H-71. The notification service checks mute settings and a deduplication key before delivery. A timeout after draft creation triggers a receipt lookup; the retry reuses the draft. A proposed customer email remains a draft requiring a supervisor's fresh approval tied to that exact recipient and shipment state. After the pilot expires or access is revoked, the run stops.</p>"
    '<pre><code class="language-text">Schedule: daily 08:15 local, end after 30 days.\nRun key: north-pier / W-47 / review-v3.\nInputs: resolved window, snapshot S-47, partition manifest.\nDecision: six unchanged holds; H-71 new hold.\nEffect: draft receipt R-47; one alert candidate.\nRetry: reuse R-47, check alert receipt before any send.\nCustomer email: draft only, supervisor approval required.</code></pre>'
    "<h2>Release and operating cost</h2><p>Test a fresh zero result, stale zero result, missing partition, missed run, duplicate invocation, ambiguous send, revoked access, and expired pilot. Treat unauthorized effects and false all-clear reports as hard failures. Comparing N records is O(N) with keyed sets; a receipt check is O(1) average in an indexed store. The audit row records schedule event, window, snapshot hash, prompt version, validation outcome, artifact ID, alert decision, and receipts. Replay against the frozen snapshot checks decision fields without claiming identical wording from a model.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not let a stale zero look like a verified empty depot.</li><li>Do not create a second draft merely because the first invocation timed out.</li><li>Do not send customer outreach under a read-only review grant.</li><li>Do not notify the manager on every unchanged run.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections))
new_rows.append(make_article(project_path, titles[project_path], "Design a bounded daily review with freshness, retry, alert, and approval gates.", project_body, projects, 80, project_connections, "project"))

questions = [
    ("What distinguishes a recurring task from a one-time check?", "A stated cadence and stop condition", "A longer prompt", "A model-generated reminder", "A repeatable schedule needs explicit start and end behavior."),
    ("Who decides when the saved prompt runs?", "The scheduler", "The model's own clock", "A retrieved document", "Invocation timing belongs to the scheduler."),
    ("What should a run use for its reporting cutoff?", "Resolved timestamps from the application", "An assumed current date", "The prior answer's wording", "A verified window prevents overlap and gaps."),
    ("A stale endpoint returns zero holds. What is the state?", "Unknown until fresh data arrives", "All holds released", "The depot is empty forever", "Stale zero is not verified empty."),
    ("A query fails and returns no records. How is that represented?", "Source unavailable", "Verified zero", "No change", "Failure and an empty successful result are different states."),
    ("What key should a retry use for the same reporting window?", "The original stable run identity", "A new random identity", "The model's last sentence", "A stable key supports deduplication."),
    ("The draft save times out. What is the next step?", "Check the destination for a receipt", "Always save another draft", "Declare success without evidence", "The effect may already have happened."),
    ("Six held parcels remain unchanged. What should the manager receive?", "No repeated change alert", "Six new alerts", "An invented urgent notice", "The run can be logged without a user notification."),
    ("The source is unavailable. Should alert silence imply no issue?", "No; send a distinct failure signal if policy requires", "Yes; no records means no issue", "Only if the model sounds confident", "A data failure is not a verified no-change run."),
    ("May a read-only daily review send customer email?", "Only after separate, current effect approval", "Yes, because the schedule is saved", "Yes, if the customer is mentioned", "Observation authority does not grant an external effect."),
    ("What happens when depot access is revoked?", "Future runs stop accessing that depot", "The old schedule keeps the grant", "The model decides based on tone", "Authorization is checked at each invocation."),
    ("What does a controlled replay prove?", "Whether decision fields follow frozen inputs and versions", "Identical wording is guaranteed", "Later facts replace old evidence", "Replay supports diagnosis without a byte-identical model-output promise."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-memory-lifecycle"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
                  title=titles[quiz_path], summary="Test schedule intent, time windows, freshness, retries, alerts, and approval.",
                  body="<p>Choose the recurring-run decision justified by verified data and current authority.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, production, quizzes]),
                  sort_order=30790, status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
quiz_entry["data"].update(subject_root=root_path, section_path=quizzes, content_format="html",
                          author_path="authors/aitrove-editorial", seo_ready=True, duration_minutes=12,
                          related=related(paths + [project_path]),
                          questions=[{"prompt": prompt,
                                      "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                      "answer": (-index) % 3, "explanation": explanation}
                                     for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)])
new_rows.append(quiz_entry)

for hub_path, selected, title, summary in [
    (applications, paths[:3], "Recurring task inputs", "Specify cadence, windows, and fresh evidence before each review."),
    (production, paths[3:], "Recurring task controls", "Deduplicate retries, bound alerts and effects, and retain run evidence."),
    (projects, [project_path], "North Pier recurring review", "Apply the schedule and control contracts to a daily depot case."),
    (quizzes, [quiz_path], "Recurring workflow decisions", "Test the failure paths in a repeated AI task."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

lookup[root_path]["body"] += "<h2>Recurring AI workflows</h2><p>Build repeated tasks around current evidence, bounded authority, and verified outcomes.</p>" + links(paths + [project_path, quiz_path])
lookup[root_path]["updated_at"] = stamp

backlinks = {
    "prompt-engineering/task-contract": paths[0],
    "prompt-engineering/time-sensitive-research-contract": paths[1],
    "prompt-engineering/retrieval-freshness-and-conflict": paths[2],
    "prompt-engineering/side-effect-receipt-reconciliation": paths[3],
    "prompt-engineering/incident-update-audience-owner-and-release-gate": paths[4],
    "prompt-engineering/tool-call-authorization-contract": paths[5],
    "prompt-engineering/prompt-trace-observability": paths[6],
    "prompt-engineering/prompt-evaluation-ci-gate": project_path,
}
for old_path, new_path in backlinks.items():
    entry = lookup[old_path]
    entry["body"] += "<p><strong>Continue with:</strong> " + link(new_path) + ".</p>"
    entry["data"]["related"] = related([item["path"] for item in entry["data"].get("related", [])] + [new_path])
    entry["updated_at"] = stamp

entries.extend(new_rows)
FIXTURE.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newLessons": len(specs), "newProjects": 1, "newQuizzes": 1,
                  "newPaths": [entry["path"] for entry in new_rows]}))
