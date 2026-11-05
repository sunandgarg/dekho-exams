"""Add original architecture-decision prompt lessons, project, and quiz."""

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
project_path = "prompt-engineering/receipt-ingest-architecture-review-project"
quiz_path = "quizzes/prompt-engineering-architecture-decisions"

specs = [
    {
        "slug": "architecture-brief-constraints-and-decision-owner",
        "title": "Architecture prompts: start with constraints and an owner",
        "summary": "Define the decision, workload, quality targets, constraints, and missing measurements.",
        "definition": "An architecture prompt should name one decision, the person accountable for it, the current system, observed workload, quality targets, non-negotiable constraints, and facts still unknown. Ask the model to distinguish measurements from estimates before it proposes a design. A diagram is not a decision: it can show components while hiding why a queue, database, or retry rule is needed. Record the client-visible behavior, data correctness rule, failure tolerance, and operational budget. If the input lacks a measured service rate, the prompt should request a load test or return a conditional comparison rather than inventing capacity. Keep the proposed design scoped to the decision actually requested.",
        "case": "A fictional Receipt Ingest service accepts 18,600 requests per minute on a normal business day. Product wants to choose whether to add a queue before the receipt writer. A burst multiplier of 2.4 is a planning assumption, not an observed peak. Each request has an identity key so retries must not write two receipts. The engineering lead owns the decision; operations must review a worker-failure plan. The prompt asks for response-time and loss targets but marks both as missing until the teams set them. It does not treat the normal traffic figure as proof that one worker can handle the peak.",
        "sample": "Decision: direct writes or bounded queue before receipt writer.\nObserved: 18,600 accepted requests/minute in normal period.\nAssumed: 2.4x planning burst; validate against traffic traces.\nInvariant: one durable receipt per request identity.\nOwner: engineering lead; operations reviews failure behavior.\nUnknown: latency target, loss tolerance, measured worker capacity.",
        "cost": "Capturing the brief takes a few review turns but avoids modeling a workload that has not been defined. For N requirements, a claim ledger is O(N) entries; the hard part is verifying the numbers and resolving conflicts, not writing the entries. A short list of unknowns can prevent expensive redesign after a benchmark disproves an assumption. Do not turn a budget into a target without specifying the time window and measurement point. The model may organize the decision, while the accountable engineer approves its scope.",
        "mistakes": ["Do not call an assumed burst factor an observed peak.", "Do not propose a queue without stating which failure or latency constraint it addresses.", "Do not make the model the decision owner."],
        "related": ["prompt-engineering/task-contract", "prompt-engineering/clarification-versus-assumption-gate", "prompt-engineering/intent-to-acceptance-check"],
        "section": applications,
    },
    {
        "slug": "architecture-capacity-units-and-headroom-check",
        "title": "Capacity prompts: check units, headroom, and a failed worker",
        "summary": "Turn stated traffic and measured throughput into a reproducible capacity estimate.",
        "definition": "A capacity prompt should show each unit conversion and assumption before it recommends an instance count. Separate sustained demand, burst demand, measured sustainable capacity per worker, and reserve for an unavailable worker. Use a deterministic calculation for integer rounding. The number is a planning lower bound under the stated workload, not proof that latency, database capacity, or network limits will hold. Ask which resource saturates first and what load test would falsify the estimate. When the worker benchmark is missing, leave the denominator blank instead of dividing by a fabricated throughput.",
        "case": "Receipt Ingest sees 18,600 requests per minute, or 310 per second. Applying the assumed 2.4 burst factor gives 744 requests per second. A load test under the same request mix measures 47 sustainable requests per second per healthy worker. The peak therefore needs 16 healthy workers because 15 provide only 705 per second, while 16 provide 752. To retain 16 after one worker fails, deploy 17. This ignores database, queue, and network limits until separate tests verify them. The estimate must be revised if the 2.4 factor or measured worker rate changes.",
        "sample": "from math import ceil\n\nnormal_requests_per_minute = 18_600\nplanning_burst_factor = 2.4\nmeasured_worker_rps = 47\nfailed_worker_reserve = 1\n\npeak_rps = ceil(normal_requests_per_minute / 60 * planning_burst_factor)\nhealthy_workers = ceil(peak_rps / measured_worker_rps)\ndeployed_workers = healthy_workers + failed_worker_reserve\nassert (deployed_workers - 1) * measured_worker_rps >= peak_rps\nprint(f\"peak_rps={peak_rps} healthy_workers={healthy_workers} deployed_workers={deployed_workers}\")",
        "language": "python",
        "cost": "The arithmetic is O(1) time and space for fixed inputs; measurement and load testing dominate effort. At 47 requests per second, 16 healthy workers provide 752 per second, only eight above the planning peak, so the team should test burst duration, uneven routing, and downstream saturation before treating this as safe headroom. A queue can absorb a transient mismatch but adds storage, delay, and replay behavior. The prompt must state whether the arrival rate counts retries, because retries can raise offered load during failures.",
        "mistakes": ["Do not round down a fractional worker requirement.", "Do not add a failed-worker reserve and then forget to evaluate capacity after that worker is gone.", "Do not claim end-to-end capacity from a worker-only benchmark."],
        "related": ["prompt-engineering/deterministic-calculation-gates", "prompt-engineering/cost-latency-quality-budget", "prompt-engineering/aggregate-denominator-reconciliation"],
        "section": applications,
    },
    {
        "slug": "architecture-alternatives-and-consequence-ledger",
        "title": "Architecture decisions: compare real alternatives and consequences",
        "summary": "Record the direct-write and queued designs against the same constraints.",
        "definition": "An architecture decision prompt should compare plausible alternatives under identical workload and correctness assumptions. Record what each option gains, what it costs, its failure behavior, and the evidence needed before acceptance. Avoid a feature checklist in which one option is given the best implementation and the other a straw version. Name which consequences are reversible and which require data migration or client contract changes. A decision record may be proposed, accepted, or superseded; a new choice should preserve the reason the earlier one was made. The model can draft the comparison, but measured tests and an accountable reviewer settle the decision.",
        "case": "For Receipt Ingest, direct writes keep a simple request path and can return a durable result immediately, but a writer slowdown may push latency or failure to clients. A bounded queue can absorb short bursts and decouple acceptance from processing, but it changes the meaning of 'accepted' and requires backlog monitoring, replay rules, and a dead-letter path. Both need request-ID deduplication to avoid duplicate receipts. The prompt asks whether a client needs a final receipt in the same response; if so, queueing cannot be treated as equivalent without a new status contract. The engineering lead proposes one option only after a load test and client review.",
        "sample": "Option A: direct write; simple response; writer failure reaches client.\nOption B: bounded queue; async completion; backlog and replay duties.\nShared invariant: request ID yields at most one durable receipt.\nOpen contract: does HTTP acceptance mean complete or enqueued?\nDecision status: proposed until client and load evidence are reviewed.",
        "cost": "Comparing O alternatives against C constraints takes O(OC) explicit checks. The matrix is small; quality depends on using the same evidence for both options. Queueing adds storage proportional to arrival rate multiplied by backlog duration, plus worker and operational cost. Direct writes avoid that queue but may need spare writer capacity for burst traffic. A model should state these costs as conditional rather than pretend to price a system without retention, traffic mix, or infrastructure rates.",
        "mistakes": ["Do not compare a complete queue design with an unrealistically weak direct-write design.", "Do not equate enqueue acknowledgement with a durable completed receipt.", "Do not erase a superseded decision and its reason."],
        "related": ["prompt-engineering/evidence-bound-report-summary", "prompt-engineering/role-priority-and-conflict-resolution", "prompt-engineering/schema-migration-prompt-review"],
        "section": applications,
    },
    {
        "slug": "architecture-failure-mode-and-observability-contract",
        "title": "Architecture prompts: test the failure path and its signals",
        "summary": "Tie overload, retries, and dependency faults to observable user outcomes.",
        "definition": "A failure-mode prompt should enumerate the events that could break the chosen design, the user-visible effect, the signal that detects it, and the recovery step. For a queued system, examine duplicate delivery, full queue, poisoned message, worker loss, and downstream unavailability. For direct writes, examine request timeout after a successful commit and retry behavior. The prompt should require bounded retries and an explicit point where human operators take over. Observability is not a list of dashboards: each metric or trace must answer a recovery question. Define what is measured at the client boundary, because an internal healthy worker count can coexist with failing requests.",
        "case": "Receipt Ingest's proposed queue accepts a request, then the writer fails for 90 seconds. New requests may enter the bounded queue only until its capacity is reached. The prompt requires queue depth, oldest-message age, acceptance failures, duplicate-suppression count, and end-to-end completion latency. A poisoned record moves to a reviewed failure path after a bounded retry count; it must not block every later receipt. Recovery replays by request ID so a duplicate delivery cannot produce a second durable receipt. An operator must know when backlog age exceeds the agreed target and whether the system is still accepting work it cannot complete.",
        "sample": "Fault: writer unavailable for 90 seconds.\nUser effect: accepted receipt may remain incomplete; queue may fill.\nSignals: acceptance failure, oldest age, depth, completion latency.\nRecovery: bounded retry; isolate poison; replay by request ID.\nEscalation: stop accepting beyond bounded capacity and page owner.",
        "cost": "At a planning peak of 744 requests per second, a complete 90-second writer outage could add 66,960 arrivals before retries or rejection, if admission remains open and no work drains. That is a scenario calculation, not a recommended queue size; capacity must also account for payload bytes, burst duration, and recovery drain rate. Tracking M in-flight identities needs O(M) state until retention or compaction. A prompt that asks only for 'high availability' misses the concrete backlog and duplicate behavior operators must test.",
        "mistakes": ["Do not describe queue depth as proof of completed receipts.", "Do not retry a poison record forever.", "Do not accept more work than bounded storage and recovery policy permit."],
        "related": ["prompt-engineering/incident-log-timeline-triage", "prompt-engineering/tool-loop-stop-rules", "prompt-engineering/side-effect-receipt-reconciliation"],
        "section": applications,
    },
    {
        "slug": "architecture-review-load-test-and-rollout-gate",
        "title": "Architecture release: require evidence, rollback, and ownership",
        "summary": "Stage the change against load, correctness, and recovery checks before expansion.",
        "definition": "An architecture release prompt should turn a proposed decision into an evidence packet: load-test workload, correctness checks, failure injection, operational signals, rollout stages, stop conditions, rollback method, and named owners. The prompt must not declare a design production-ready from a diagram or a single arithmetic estimate. State which hypothesis each test addresses and what result would block release. A rollback may restore old traffic routing while queued work remains, so the plan must say who drains, replays, or quarantines in-flight records. An accepted decision record and a deployed change are separate states; approval does not prove rollout occurred.",
        "case": "The Receipt Ingest lead chooses a limited queued pilot only after clients accept the asynchronous completion contract. A load test uses the measured 47-request-per-second worker mix and the 744-request-per-second planning peak, then checks completion latency and database load. A failure test removes one of 17 deployed workers and confirms the 16 survivors can sustain the target under the tested mix. Another test replays duplicate request IDs and interrupts the writer. The pilot starts with a small traffic slice; expansion stops if oldest-message age or duplicate receipt count breaches the agreed threshold. Operations owns rollback and the in-flight queue disposition.",
        "sample": "Gate 1: client accepts enqueue-versus-complete response contract.\nGate 2: 744-rps load mix; database and latency within agreed limits.\nGate 3: one worker lost; 16 healthy workers sustain test.\nGate 4: duplicate and writer-failure tests preserve one receipt/ID.\nPilot: small traffic slice; stop thresholds and queue disposition named.\nStatus: accepted ADR != completed rollout; record deployment receipt.",
        "cost": "A staged rollout costs extra test environments, observation time, and operational review, but bounds the number of users exposed to a wrong assumption. If R rollout stages each run K checks, review work is O(RK), plus recovery drills. Reusing the same workload definition across tests makes comparisons meaningful. The queue's backlog after rollback can outlive the routing change, so the team must budget time and capacity to drain it safely. Record both passing and failing runs; a selective success trace cannot justify expansion.",
        "mistakes": ["Do not use a clean diagram as evidence of load or failure behavior.", "Do not rollback routing without a plan for already accepted queued work.", "Do not report an accepted decision record as proof of a completed deployment."],
        "related": ["prompt-engineering/prompt-release-review-packet", "prompt-engineering/release-regression-gate", "prompt-engineering/online-prompt-experiment-stop-rules"],
        "section": production,
    },
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]).intersection(lookup)
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: review a receipt-ingest architecture decision"
titles[quiz_path] = "Architecture-decision prompt checks"


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
                 difficulty="Advanced", tags=["prompt engineering", "architecture review"],
                 sort_order=30000 + order, status="published", published_at=stamp,
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
            + '<pre><code class="language-' + spec.get("language", "text") + '">' + html.escape(spec["sample"], quote=False) + "</code></pre>"
            + "<h2>Performance and operating cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
            + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(mistake) + "</li>" for mistake in spec["mistakes"]) + "</ul>"
            + "<h2>Connected lessons</h2>" + links(connections))
    new_rows.append(article(path, spec["title"], spec["summary"], body, spec["section"], index * 10, connections))

project_connections = paths + ["prompt-engineering/deterministic-calculation-gates", "prompt-engineering/prompt-release-review-packet", "prompt-engineering/incident-log-timeline-triage", quiz_path]
project_body = (
    "<p>Write a reviewable architecture decision for a fictional Receipt Ingest service. The service normally accepts 18,600 requests per minute. A 2.4 planning burst is assumed; the measured worker throughput is 47 requests per second under the relevant mix. Each request identity may produce only one durable receipt. Compare direct writes with a bounded queue, including what a client response means in each design. Deliver an assumption ledger, verified capacity estimate, proposed decision record, failure exercise, and staged release gate. The engineering lead owns acceptance; operations reviews recovery.</p>"
    "<h2>Calculate before comparing</h2><p>Normal traffic is 310 requests per second, and the assumed burst is 744 per second. A worker measurement of 47 per second yields 16 healthy workers at peak, with 17 deployed if one may be unavailable. This is a worker-only planning bound; test the database, network, traffic mix, and latency separately. A complete 90-second writer outage at 744 arrivals per second could produce 66,960 arrivals before retries or rejection if admission stays open. That scenario makes queue capacity and admission policy explicit rather than recommending an untested size.</p>"
    "<h2>Compare and test the two contracts</h2><p>Direct writes can return a completed receipt in the request path but expose writer slowdown to clients. A bounded queue can absorb a brief mismatch but may return only an enqueue acknowledgement; the client must accept a later completion state. Both paths require request-ID deduplication. The proposed queue decision stays unaccepted until client contract review and load evidence exist. Test duplicate replay, poisoned work, full queue behavior, and one failed worker. During a small pilot, stop expansion if completion latency, oldest-message age, or duplicate receipts breach the agreed limits. A rollback plan must account for already accepted queued work.</p>"
    '<pre><code class="language-text">Observed normal: 18,600/min = 310/s.\nAssumed peak: 310 x 2.4 = 744/s.\nMeasured worker: 47/s; 16 healthy; 17 deployed for one loss.\nWriter outage scenario: 744 x 90 = 66,960 arrivals.\nOpen: client response contract, database capacity, latency target.\nRelease: limited pilot, stop limits, rollback owner and queue plan.</code></pre>'
    "<h2>Performance and operating cost</h2><p>Fixed-input capacity arithmetic is O(1); checking N workload records to validate the traffic assumption is O(N). Comparing two options across C constraints is O(C), while R release stages with K checks require O(RK) review actions. These counts say nothing about actual production safety without representative load and failure measurements. The final record should distinguish measured, assumed, proposed, accepted, deployed, and superseded states so no diagram or model response appears to authorize a rollout.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not present 17 workers as an end-to-end guarantee.</li><li>Do not treat queue acceptance as completed receipt delivery.</li><li>Do not rollback routing while leaving in-flight work without an owner.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Compare direct writes and a bounded queue using checked capacity and recovery evidence.", project_body, projects, 60, project_connections, kind="project"))

questions = [
    ("What should an architecture prompt distinguish at the start?", "Observed workload, assumptions, and missing measurements", "Only a preferred diagram", "A model's confidence", "The brief must separate evidence from planning inputs."),
    ("What is 18,600 requests per minute in requests per second?", "310", "744", "47", "Divide the minute rate by 60."),
    ("What is the 2.4x planning peak from 310 per second?", "744 per second", "310 per second", "1,116 per second", "The multiplier applies to normal demand."),
    ("At 47 per worker, how many healthy workers cover 744 per second?", "16", "15", "17 after losing one of 17", "Fifteen supply only 705 per second."),
    ("How many deployed workers retain that capacity after one fails?", "17", "16", "15", "One reserve leaves 16 healthy workers."),
    ("What does the worker count fail to prove?", "Database and end-to-end latency capacity", "The arithmetic result", "That workers have identities", "Other resources can saturate first."),
    ("What contract question separates direct writes from queueing?", "Does acceptance mean completed or only enqueued?", "Which diagram is prettier?", "Can a queue be named?", "The client must know what response success means."),
    ("What remains necessary in either design?", "Request-ID deduplication", "Unlimited retries", "No failure handling", "Retries can otherwise create duplicate receipts."),
    ("At 744 arrivals per second, what can a 90-second total writer outage add?", "66,960 arrivals before retries or rejection", "744 arrivals", "16 arrivals", "Multiply the arrival rate by outage duration."),
    ("What should happen to a poisoned queued record?", "Bound retries and isolate it for review", "Retry forever", "Block all later receipts", "Unbounded retry stalls recovery."),
    ("What must a rollback plan include for a queued pilot?", "Disposition of already accepted in-flight work", "Only routing reversal", "Deletion of the decision record", "Queued work can outlive routing changes."),
    ("Does an accepted architecture record prove deployment?", "No; a separate rollout receipt is needed", "Yes, always", "Only if the diagram is complete", "Decision status and deployment status differ."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-multimodal-evidence"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                  path=quiz_path, title=titles[quiz_path],
                  summary="Test constraints, capacity arithmetic, alternatives, failure modes, and release evidence.",
                  body="<p>Choose the architecture decision supported by the stated workload and evidence.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, production, quizzes]),
                  sort_order=30070, status="published", published_at=stamp,
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
    (applications, paths[:4], "Architecture decisions", "Define constraints, calculate capacity, compare alternatives, and test failure paths."),
    (production, paths[4:], "Architecture release evidence", "Load-test the chosen contract and stage its rollout with rollback ownership."),
    (projects, [project_path], "Receipt Ingest decision", "Review a fictional service's direct-write and bounded-queue alternatives."),
    (quizzes, [quiz_path], "Architecture decision checks", "Test planning assumptions, arithmetic, contracts, and rollback."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

root_hub = lookup[subject_root]
root_hub["body"] += "<h2>Architecture decisions and release evidence</h2><p>Make workload assumptions explicit, check capacity arithmetic, and review failure and rollout behavior.</p>" + links(paths + [project_path, quiz_path])
root_hub["updated_at"] = stamp

backlinks = {
    "prompt-engineering/task-contract": paths[0],
    "prompt-engineering/cost-latency-quality-budget": paths[1],
    "prompt-engineering/deterministic-calculation-gates": paths[1],
    "prompt-engineering/schema-migration-prompt-review": paths[2],
    "prompt-engineering/incident-log-timeline-triage": paths[3],
    "prompt-engineering/side-effect-receipt-reconciliation": paths[3],
    "prompt-engineering/release-regression-gate": paths[4],
    "prompt-engineering/prompt-release-review-packet": paths[4],
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
