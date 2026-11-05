"""Add original serverless operating-boundary content to local fixtures."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
course = "devops/devops-tutorial"
project_hub = course + "/project"
quiz_hub = "devops/quizzes"


def lesson(slug, title, summary, definition, decision, language, sample, cost, mistakes, related):
    return dict(path="devops/" + slug, title=title, summary=summary,
                definition=definition, decision=decision, language=language,
                sample=sample, cost=cost, mistakes=mistakes, related=related)


specs = [
    lesson(
        "serverless-invocation-budget",
        "Serverless invocation budgets: separate CPU, elapsed time, and I/O",
        "A function can be cheap in CPU and still exceed an end-to-end deadline while waiting on dependencies.",
        "A serverless invocation runs inside a provider-defined resource envelope. CPU time, elapsed duration, memory, request size, outbound connections, and subrequests may have separate ceilings. A handler that waits on a database can use little CPU while consuming its entire wall-clock budget; a busy serialization loop can hit a CPU ceiling before the caller's timeout. The contract must name the caller deadline, function budget, dependency timeout, and fallback behavior. Provider limits change, so record the effective environment and tier alongside the release.",
        "An invoice-preview endpoint has a 4.5-second client budget. Assign 350 milliseconds to edge routing, 900 to authentication, 1,600 to ledger lookup, 800 to rendering, and 850 to residual network and retry margin. Pass the remaining deadline to each dependency; do not give every call its own full 4.5 seconds. Return a bounded failure when the ledger cannot answer rather than allowing the platform to terminate the invocation after a partial response. In a disposable test, inject a slow ledger and a CPU-heavy rendering payload separately. Capture elapsed time, CPU time, subrequest count, response code, and the version handling the request. A timeout that leaves a downstream write uncertain requires reconciliation before retry.",
        "text",
        "Invoice preview deadline: 4500 ms\nEdge and routing: 350 ms\nAuthentication: 900 ms\nLedger lookup: 1600 ms\nRendering: 800 ms\nResidual margin: 850 ms\nFailure: no partial invoice is published",
        "One request that makes D sequential dependency calls has O(D) network waits even if local CPU work is small. Parallel calls can reduce latency but increase concurrency and connection demand. Measure duration and CPU independently at p95 and p99; a cheaper execution tier can fail a workload that previously met its deadline. Keep a margin for queueing and client transit, not just handler code.",
        ["Do not confuse CPU time with elapsed time.", "Do not assign the full caller deadline to every nested call.", "Do not retry an uncertain write without checking its result."],
        ["devops/retry-timeout-budgets", "devops/grpc-deadline-propagation", "devops/observability-signals"],
    ),
    lesson(
        "serverless-concurrency-downstream-capacity",
        "Serverless concurrency: cap the function before the database fails",
        "Automatic scaling can multiply database connections faster than the database can accept them.",
        "A function platform can increase active invocations as demand rises, but downstream systems retain finite connection, write, and rate budgets. A concurrency ceiling protects a dependency only when it is derived from measured per-invocation demand and leaves capacity for other clients. Synchronous requests may be rejected or throttled at the ceiling; queued events may accumulate age. Both outcomes need an explicit user and retry policy. Increasing the ceiling without load testing merely transfers overload to the next boundary.",
        "A claims-status function opens one database connection per active invocation. The database permits 120 service connections, of which 35 are reserved for other workloads and 15 for administration and failover. The remaining 70 form an upper bound before accounting for connection bursts and transaction duration. Start a load test below that bound, measure connection occupancy and p99 latency, and tighten the function ceiling if the database degrades earlier. For queue-triggered work, limit consumer parallelism and watch oldest-message age; for HTTP, return a retryable response with a bounded client policy rather than accepting unbounded backlog. A shared pool or proxy can reduce connection churn but does not create extra database write capacity.",
        "text",
        "Database connection budget: 120\nOther services: 35\nAdministration and failover: 15\nTheoretical function maximum: 70\nRelease gate: lower measured ceiling if p99 or lock wait rises\nQueue signal: oldest pending event age",
        "At C concurrent invocations with one connection each, demand is O(C); with K connections per invocation it can reach O(C times K). Restricting concurrency can protect the database while raising queue delay or HTTP rejection. Track all three: function throttles, database saturation, and user completion time. Reserve a separate recovery path so a stuck batch cannot consume every execution slot.",
        ["Do not treat automatic function scaling as downstream capacity.", "Do not set the ceiling equal to the database maximum.", "Do not hide queue age after lowering consumer concurrency."],
        ["devops/database-pool-pressure", "devops/overload-shedding", "devops/queue-age-scaling-contract"],
    ),
    lesson(
        "serverless-event-idempotency-ledger",
        "Serverless event idempotency: commit the effect and receipt together",
        "At-least-once delivery requires a durable way to recognize work already completed.",
        "A queue or event source may redeliver an event after a worker fails, a visibility lease expires, or acknowledgement is lost. In-memory deduplication cannot cover a new invocation. A durable idempotency key must identify the business operation, not merely the transport attempt; the effect and its receipt should be committed in one transaction when they share a database. If the effect spans an external service, use a stable request key there and reconcile an uncertain response. A receipt written before the effect can lose work; a receipt written afterward in a separate transaction can repeat it.",
        "A settlement function receives the same payout event twice after its first acknowledgement is lost. It inserts a receipt keyed by settlement ID and writes the ledger movement inside the same database transaction. The second invocation sees the existing receipt and returns the stored outcome. A new event with the same key but a different amount is a conflict for investigation, not a silent duplicate. If the processor sends a bank instruction, pass a stable idempotency key to the bank and keep an uncertain state until the bank's status API confirms the result. Exercise the crash immediately before commit and immediately after commit; both replays must leave one movement.",
        "sql",
        "BEGIN;\nWITH accepted AS (\n  INSERT INTO settlement_receipts (settlement_id, payload_hash, result_status)\n  VALUES ('stl-8472', 'payload-digest-47', 'applied')\n  ON CONFLICT (settlement_id) DO NOTHING\n  RETURNING settlement_id\n)\nINSERT INTO ledger_movements (settlement_id, account_id, amount_cents)\nSELECT settlement_id, 'reserve-claims', 4731 FROM accepted;\nDO $$\nBEGIN\n  IF EXISTS (\n    SELECT 1 FROM settlement_receipts\n    WHERE settlement_id = 'stl-8472'\n      AND payload_hash <> 'payload-digest-47'\n  ) THEN\n    RAISE EXCEPTION 'settlement payload conflict';\n  END IF;\nEND $$;\nCOMMIT;",
        "A unique-key lookup is typically O(log N) with a B-tree index; the receipt table grows with processed operations and needs retention aligned to the replay horizon. The SQL assumes settlement_receipts has a unique settlement_id and that ledger_movements also forbids duplicate settlement IDs. Only an inserted receipt can feed the movement in this transaction; a changed payload raises an error and rolls back. In application code, bind the validated digest and amount as parameters instead of interpolating event text. Test concurrent duplicates and record receipt conflicts, uncertain external outcomes, and replay age.",
        ["Do not deduplicate only in process memory.", "Do not mark an event complete before its effect commits.", "Do not treat the transport message ID as the business identity without checking producer behavior."],
        ["devops/transactional-outbox-delivery", "devops/queue-visibility-lease", "devops/object-event-ordering-idempotency"],
    ),
    lesson(
        "serverless-cold-start-latency",
        "Serverless cold starts: measure initialization against the user path",
        "Initialization is a separate latency source that can be hidden by warm-only load tests.",
        "A function may prepare a new execution environment after inactivity, scaling, a code change, or platform recycling. Loading modules, establishing clients, and fetching configuration can add latency before handler work begins. A warm request may reuse an environment, but reuse is not a durability guarantee and process-local state cannot hold required business data. The useful question is whether initialization makes the full request miss its service objective under the traffic pattern that creates new environments.",
        "An access-check function passes a steady-state 180-millisecond target, then rises above 900 milliseconds during a morning burst. Test a cold cohort and a warm cohort with the same auth data; separate environment initialization, secret fetch, first database handshake, and handler time. Move invariant client setup outside the handler only when it is safe to reuse, but refresh expiring credentials and avoid caching a tenant-specific decision globally. If pre-initialized capacity is available, price it against measured tail-latency improvement rather than buying it for every function. Preserve the release version in the trace so a slow new bundle is not mistaken for a provider incident.",
        "text",
        "Access-check latency record\nCohort: cold or warm\nVersion: immutable deployment identifier\nInit: module load and configuration\nDependency: first connection and secret lookup\nHandler: authorization decision\nOutcome: end-to-end p99 against user objective",
        "If initialization loads M modules and opens D clients, cold-path work grows with those initialization costs while warm invocations amortize them. Pre-initialized capacity trades idle spend for lower startup variance. Monitor cold-path fraction, init duration, total request latency, and failure rate together. A faster warm median is not evidence that a burst fits the user objective.",
        ["Do not benchmark only a warm environment.", "Do not rely on process-local state for durable records.", "Do not cache tenant-specific authorization across invocations."],
        ["devops/synthetic-transaction-monitoring", "devops/service-level-objectives", "devops/telemetry-sensitive-data-boundary"],
    ),
    lesson(
        "scheduled-function-overlap-control",
        "Scheduled functions: control overlap, catch-up, and missed runs",
        "A schedule is an invocation request, not proof that one complete job ran exactly once.",
        "A scheduled function can outlive its interval, fail after partial work, or be invoked again while a prior run remains active. A process-local mutex cannot coordinate separate execution environments. Use a durable lease or compare-and-set marker with an expiry, and make each unit of work restartable. A run record should distinguish scheduled time, actual start, last checkpoint, completion, and repair owner. If missed intervals must be replayed, define the catch-up window and a backfill rate that does not overwhelm the source system.",
        "A nightly entitlement reconciliation usually takes 11 minutes but occasionally takes 39. The next trigger must not start another full scan over the same accounts. Acquire a lease for the intended interval, checkpoint each account range, and renew only while progress continues. Kill the worker after range 17, then run the next trigger and show that it resumes the unfinished interval without applying duplicate entitlement changes. Expire a stalled lease only after its fencing token prevents the old holder from committing. Record skipped or delayed intervals and alert when the oldest unfinished interval exceeds the reporting deadline. A manual rerun uses the same interval identity and audit trail.",
        "text",
        "Entitlement reconciliation\nInterval ID: UTC scheduled date\nLease: owner, expiry, fencing generation\nProgress: last committed account range\nRetry: resume incomplete interval\nCatch-up: bounded oldest unfinished interval\nCompletion: count and reconciliation checksum",
        "Scanning A accounts is O(A) per completed interval. Replaying a full scan after every failure multiplies provider calls and can create correlated rate-limit failures. Checkpointing adds writes and operational complexity but caps repeated work. Measure run delay, duplicate attempts, lease loss, backlog age, and the time until the entitlement view is consistent.",
        ["Do not use a process-local lock for a distributed schedule.", "Do not let an expired worker commit after a new lease holder starts.", "Do not mark the scheduled trigger as proof of completed work."],
        ["devops/cronjob-schedule-safety", "devops/lease-leadership-fencing", "devops/database-backfill-checkpoints"],
    ),
    lesson(
        "serverless-version-data-rollback",
        "Serverless rollback: restore code traffic without assuming data rolled back",
        "An immutable function version can be reselected quickly while its external writes remain in place.",
        "Function releases often package code, assets, bindings, and configuration into a version, then route traffic to one or more versions. Redirecting traffic to an earlier version does not reverse database writes, queue acknowledgements, cache entries, or storage mutations. A safe rollout keeps both versions compatible with the active schema and event format for the rollback window. For asynchronous consumers, in-flight messages may be processed by both versions around a shift; record the version alongside each effect and avoid a destructive schema contraction until old workers have drained.",
        "A receipt API deploys version B to a small cohort. B writes a new optional tax field while A remains active. The team observes a mismatch in tax rounding and routes new traffic back to A. Before declaring recovery, inspect receipts created by B, reconcile affected totals, confirm A can read them, and identify queued events still using B's payload format. Keep the schema additive until the replay horizon closes. A rollback drill should include a write made by B, an A read of that record, a delayed event, and a cache key created under B. Compare error rates by version rather than aggregating them into one fleet average.",
        "text",
        "Receipt release gate\nA: current handler, reads optional tax field\nB: candidate handler, writes optional tax field\nCanary: cohort and version-specific errors\nRollback: route new calls to A\nReconcile: B-written records and delayed events\nContract: no schema removal before replay window closes",
        "Version routing changes are O(1) control-plane updates, but recovery cost scales with affected writes and queued events. Retaining two compatible paths adds temporary code and storage cost; removing one too early can turn a quick traffic rollback into data repair. Track version-specific failure rates, outstanding event age, and the count of records requiring reconciliation before ending the incident.",
        ["Do not call a code rollback a data rollback.", "Do not contract the schema while old invocations can still run.", "Do not aggregate away a small failed canary cohort."],
        ["devops/api-compatibility-window", "devops/event-schema-evolution", "devops/progressive-delivery"],
    ),
]

project_path = "devops/serverless-boundary-drill-project"
quiz_path = "quizzes/devops-serverless-operations-decisions"
titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
titles[project_path] = "Project: prove a serverless release survives duplicate events and rollback"
titles[quiz_path] = "DevOps serverless operations decisions"
assert all(item["path"] not in by_path for item in specs)
assert project_path not in by_path and quiz_path not in by_path
assert all(path in titles for item in specs for path in item["related"])


def links(paths):
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in dict.fromkeys(paths)
    ) + "</ul>"


for heading, summary, paths in [
    ("Serverless capacity and latency", "Budget invocation time, downstream concurrency, and environment startup.", [specs[i]["path"] for i in (0, 1, 3)]),
    ("Serverless work and release safety", "Make redelivery, schedules, and version rollback explicit operating contracts.", [specs[i]["path"] for i in (2, 4, 5)]),
]:
    by_path[course]["data"]["modules"].append({"title": heading, "summary": summary, "lessons": paths})
    by_path[course]["body"] += f"<h2>{html.escape(heading)}</h2><p>{html.escape(summary)}</p>" + links(paths)
by_path[course]["updated_at"] = stamp

for index, item in enumerate(specs):
    path = item["path"]
    row = copy.deepcopy(by_path["devops/continuous-integration"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
               title=item["title"], summary=item["summary"], subject="devops",
               category="DevOps", difficulty="Advanced", tags=["devops", "serverless"],
               sort_order=25000 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"kind": "tutorial", "reading_minutes": 6,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": course, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in item["related"]]}
    row["body"] = (
        f"<p>{html.escape(item['definition'])}</p><h2>Operational decision</h2>"
        f"<p>{html.escape(item['decision'])}</p>"
        f'<pre><code class="language-{item["language"]}">{html.escape(item["sample"])}</code></pre>'
        f"<h2>Cost and verification</h2><p>{html.escape(item['cost'])}</p>"
        + "<h3>Common Mistakes</h3><ul>"
        + "".join(f"<li>{html.escape(mistake)}</li>" for mistake in item["mistakes"])
        + "</ul><h2>Connected lessons</h2>" + links([course, *item["related"]])
    )
    rows.append(row)

related_paths = [item["path"] for item in specs]
project = copy.deepcopy(by_path["devops/practice-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)),
               path=project_path, title=titles[project_path],
               summary="Test function budgets, database protection, redelivery, schedule fencing, and data-compatible rollback.",
               difficulty="Advanced", sort_order=25090,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 10,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in related_paths]}
project["body"] = (
    "<p>Build a disposable receipt-processing service with an HTTP function, a queue consumer, a scheduled reconciliation job, and a database. The acceptance target is one settled receipt per business event under retries, bounded database pressure during a burst, and an earlier handler version that remains able to read records written during the canary. Use a local emulator or disposable provider account; do not run the faults against live financial data.</p>"
    "<h2>Define each boundary</h2><p>Give the HTTP path a caller deadline and explicit time allocations for authentication, lookup, and response. Limit the function's concurrency from measured database headroom. Give each event a stable settlement ID, a stored payload hash, and one unique movement key. Give the scheduled job an interval identity, durable checkpoint, lease expiry, and fencing generation. Save immutable function versions and the active schema before the canary.</p>"
    "<pre><code class=\"language-text\">Receipt drill acceptance\nDeadline: slow dependency returns a bounded result\nConcurrency: database remains below its tested safe occupancy\nDuplicate event: one ledger movement after two deliveries\nSchedule: expired holder cannot commit after lease transfer\nCanary: version-specific outcome is observable\nRollback: prior handler reads candidate-written records\nRepair: uncertain external effect is reconciled before retry</code></pre>"
    "<h2>Inject failure and recover</h2><p>Delay the ledger call until the client budget expires and inspect CPU time separately from elapsed duration. Replay the same queue message after commit but before acknowledgement; verify one movement and one stored outcome. Raise concurrent HTTP calls until the configured ceiling rejects or queues work while the database remains stable. Stop a scheduled run after checkpoint 17, let another holder resume, and prove the old holder cannot commit. Deploy a candidate that writes an optional receipt field, route a small cohort to it, then send new traffic back to the prior version. Read candidate-written records through the old version and reconcile any changed totals.</p>"
    "<h2>Report evidence</h2><p>Record duration, CPU, throttles, oldest event age, database connections, duplicate attempts, lease transitions, and version-specific error rates. State which failure was contained and which work remained pending. A passing HTTP response is insufficient if a queued settlement was duplicated or a scheduled interval silently skipped.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not count a trigger as a completed business operation.</li><li>Do not infer database safety from function success alone.</li><li>Do not assume redirecting traffic reverses writes.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*related_paths, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Serverless boundary drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("A handler waits on a database until the client leaves. Which budget was consumed?", ["Elapsed deadline, even if CPU time stayed low", "Only CPU time", "Only deployment startup time"], "I/O waits consume the caller's elapsed deadline."),
    ("How should nested calls use a 4.5-second caller deadline?", ["Pass the remaining budget and preserve a response margin", "Give each call 4.5 seconds", "Retry until the platform stops the handler"], "Independent full timeouts can exceed the caller's budget."),
    ("What sets a safe function concurrency ceiling for a database writer?", ["Measured downstream headroom including other clients and failover", "The provider's maximum function concurrency", "The largest number a dashboard accepts"], "Function scaling cannot create database capacity."),
    ("What should be monitored after lowering queue-consumer concurrency?", ["Oldest event age and completion time", "Only function errors", "Only database free space"], "A protected database can coexist with a growing backlog."),
    ("A queue redelivers after an acknowledgement is lost. What must remain stable?", ["The business operation key and stored outcome", "The process memory address", "The transport attempt number"], "A new invocation needs durable business-level deduplication."),
    ("Why is a receipt written separately before an effect unsafe?", ["A crash can suppress an effect that never committed", "It always doubles the effect", "It prevents duplicate messages"], "The receipt and effect need a common atomic or reconciled boundary."),
    ("Why compare cold and warm function cohorts?", ["Initialization may affect the tail latency of new environments", "Warm-only tests include every startup cost", "Cold starts make all requests fail"], "Warm traffic can hide initialization overhead."),
    ("Can process-local cache hold required settlement state?", ["No; the environment may disappear or be replaced", "Yes, if the handler is short", "Yes, if the provider reuses it once"], "Environment reuse is an optimization, not durable storage."),
    ("What protects a scheduled job from another invocation after lease expiry?", ["A durable fencing generation checked on commit", "A local boolean", "A longer log retention setting"], "The old holder must be unable to commit after leadership moves."),
    ("What does a trigger success prove?", ["Only that invocation happened unless work completion is recorded", "Every account was reconciled", "No interval was missed"], "Completion needs a durable job result and checkpoint."),
    ("Does reverting function traffic restore earlier database rows?", ["No; candidate-written data needs compatibility and reconciliation", "Yes, with an immutable code version", "Yes, if the canary was small"], "Code routing does not undo external writes."),
    ("What should a serverless canary compare?", ["Version-specific errors and affected records", "Only fleet-wide average errors", "Only deployment command exit status"], "A small failed cohort can disappear in aggregate metrics."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on function budgets, concurrency, redelivery, schedules, and rollback.",
            sort_order=25100, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in related_paths],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Choose the operating decision that keeps a serverless request or event within its actual boundary. Check the downstream and data consequences as well as the function outcome.</p>"
    "<h2>Review these lessons</h2>" + links(related_paths)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-service-traffic-decisions", "quizzes/devops-platform-reliability"])
    + "<h3>Common Mistakes</h3><ul><li>Do not mistake provider scaling for application safety.</li><li>Do not treat a successful deploy as proof that delayed events are compatible.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Serverless operations check</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": path, "title": titles[path]} for path in [project_path, quiz_path])

for source, targets in {
    "devops/retry-timeout-budgets": [specs[0]["path"]],
    "devops/database-pool-pressure": [specs[1]["path"]],
    "devops/transactional-outbox-delivery": [specs[2]["path"]],
    "devops/synthetic-transaction-monitoring": [specs[3]["path"]],
    "devops/cronjob-schedule-safety": [specs[4]["path"]],
    "devops/progressive-delivery": [specs[5]["path"]],
    "devops/cross-system-release-project": [project_path],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Serverless operating-boundary follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1,
                  "total_records": len(rows)}))
