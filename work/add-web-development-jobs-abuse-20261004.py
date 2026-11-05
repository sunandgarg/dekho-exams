"""Add original background-work and public-endpoint abuse curriculum entries."""
import copy
import datetime
import html
import json
import re
import subprocess
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
entries = json.loads(fixture.read_text())
by_path = {entry['path']: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()

def p(value):
    return '<p>' + html.escape(value) + '</p>'

def link(path):
    assert path in by_path, path
    return '<a href="/' + html.escape(path, quote=True) + '">' + html.escape(by_path[path]['title']) + '</a>'

hubs = [
    {'path': 'web-tech/background-workflow-reliability', 'title': 'Background Workflow Reliability',
     'summary': 'Admit jobs, survive duplicate delivery, isolate poison work, and define cancellation and schedule ownership.',
     'overview': 'A web request can accept work that will complete later, but acceptance is a durable state transition rather than a promise of instant success. This track follows a permit-report generator whose queue, worker, database, and browser can fail independently. It keeps job IDs and progress resources stable, treats duplicate delivery as normal, quarantines records that cannot succeed, and makes cancellation and scheduled overlap explicit. Every retry path is tied to a business effect that can be verified.',
     'bridges': ['web-tech/background-jobs-and-outbox', 'web-tech/accepted-operations-and-status-resources']},
    {'path': 'web-tech/abuse-resistant-public-endpoints', 'title': 'Abuse-Resistant Public Endpoints',
     'summary': 'Bound identity and resource-heavy requests while preserving legitimate access and reviewable decisions.',
     'overview': 'An endpoint may be authenticated and still be costly to run. Recovery links, search, exports, and third-party sends each have a different abuse surface. This track applies budgets to actions and work, prevents identity disclosure through response differences, offers accessible alternatives to challenges, and records denial outcomes without turning every user into a permanent fingerprint. The goal is a service that can reject harmful volume while giving legitimate users a path to finish.',
     'bridges': ['web-tech/rate-limits-and-request-budgets', 'web-tech/identity-and-application-security']},
]

topics = [
    {
        'hub': 0, 'slug': 'job-admission-idempotency-and-status-resource', 'title': 'Job Admission, Idempotency, and Status Resources',
        'summary': 'Return a durable operation identity and a truthful state when asynchronous work is accepted.',
        'concept': 'Job admission records that a server has accepted a specific operation for later execution. It does not mean the result exists yet. A client-generated idempotency key should identify one requested business effect within a defined scope and retention window, while the server issues a stable job ID that the client can poll or observe. The state resource separates queued, running, succeeded, failed, and canceled outcomes. Authorization is checked when the job is requested and again before a private result is released.',
        'case': 'Reviewer 47 requests a 63-page permit report. The HTTP connection ends before rendering can finish. The browser retries the request after a timeout, but the server has already queued the first copy. Without an idempotency record, two expensive reports run and two email notices are sent. The server binds the reviewer, case, report revision, and idempotency key to one job row. A repeated request with the same key and same payload returns the existing job; the same key with a different revision is a conflict, not a second report.',
        'implementation': 'Commit the job row and an outbox intent in one database transaction where the architecture uses an outbox. Return an accepted response with a status path owned by that job, not a fabricated completed document. The status representation includes a small state enum, timestamps, progress when measurable, an error category, and a result reference only after success. Polling must respect the requester and tenant on every read. Define what a duplicate request returns after the original job succeeds and how long the key record remains. A user may refresh or reopen the page without losing the job ID. A result reference should be short-lived and scoped to the authorized case.',
        'cost': 'A unique index on tenant, requester, and idempotency key makes duplicate lookup close to O(log n) for n stored keys. Retention creates database growth, so prune keys only after their retry window and audit requirements pass. Polling every second across many open tabs can overload the status service; prefer bounded intervals, visibility-aware pause, or server push when warranted. Progress writes also cost storage and contention. Update them at meaningful checkpoints, not every rendered line. Report generation remains O(report bytes) plus query work and should have a CPU, memory, and time budget.',
        'failure': 'Send the same request twice before the first response returns; only one business job may exist. Reuse the key with a changed report revision and require a conflict response. Crash after the job row commits but before a queue send; the outbox relay must still publish the intent. Return an accepted response, then fail rendering; the status resource must report failure rather than keeping a perpetual queued label. Switch accounts and try reading the old status path. Expire a result link, then verify that the job record remains visible while the private file is denied.',
        'drill': 'Implement a report request for case 47 at revision 29. Persist key r-63 under the requester and return job 84. Repeat the same payload and inspect the identical job ID; change the revision and inspect a conflict. Restart the browser and reload job 84 through its authorized status path. Simulate a worker failure and verify the visible state and recovery action. Measure polling traffic with 83 concurrent reviewers.',
        'decision': 'Admission establishes one durable intent and status identity; completion is a later, separately verifiable state.',
        'code': "function sameAdmittedJob(existing, request) {\n  return existing.tenantId === request.tenantId && existing.key === request.key &&\n    existing.payloadDigest === request.payloadDigest;\n}\nconsole.log(sameAdmittedJob({ tenantId: 4, key: 'r-63', payloadDigest: 'a29' }, { tenantId: 4, key: 'r-63', payloadDigest: 'b29' }));\n// Output: false",
        'checks': ['Duplicate requests map to one job or an explicit conflict.', 'A status path is authorization checked on every read.', 'An accepted job can later report a terminal failure.'],
        'mistakes': ['Treating HTTP acceptance as finished work.', 'Using only a user-supplied key without payload binding.', 'Returning private results from a job ID alone.'],
        'related': ['web-tech/idempotent-write-requests', 'web-tech/export-and-erasure-job-state'],
    },
    {
        'hub': 0, 'slug': 'worker-leases-retries-and-duplicate-effects', 'title': 'Worker Leases, Retries, and Duplicate Effects',
        'summary': 'Assume a queued message can reappear, and protect the business effect before acknowledging it.',
        'concept': 'A worker lease is a temporary claim on a queued message, not proof that no other worker will ever process it. A crash, network loss, or lease expiry can cause delivery again after a side effect has already happened. Retry safety therefore belongs at the business boundary: the worker must recognize a completed effect by stable operation identity, not rely on the broker to deliver exactly once. A transient failure can be retried; a permanent validation failure should stop or move to review.',
        'case': 'The report worker for job 84 stores an artifact and sends a completion message. It crashes after the artifact write but before acknowledging the queue message. A second worker receives the same job. If it creates a new artifact and sends another message, reviewer 47 sees two reports for one request. Instead, the artifact has a stable key derived from job ID and output revision, and the completion event uses an effect ledger. The second worker verifies the stored artifact and records the job as complete without repeating the external send.',
        'implementation': 'Use a worker state transition guarded by job version or compare-and-swap. Store the effect identity before or with the effect where possible; for an external provider, pass a supported idempotency key and keep an outcome ledger. Keep the queue lease long enough for normal work or extend it while work is healthy, but do not mistake lease tuning for deduplication. A retry policy classifies transport failures, temporary dependencies, validation faults, and authorization changes. Before each private data read, recheck job ownership and current policy. Acknowledge only after the durable result and job state are committed. Record a retry count and next attempt time without embedding private payload in logs.',
        'cost': 'Each attempt may consume O(report bytes) processing and provider calls, so repeated full work can be expensive. A ledger lookup adds an indexed read per effect and storage proportional to retained effects. Lease extensions add broker calls but can avoid premature duplicate starts during long work. More concurrency increases throughput until database, provider, or CPU limits dominate. Bound workers per tenant and provider; retry storms after an outage should use delay and jitter rather than all workers waking together. Measure duplicate deliveries and duplicate effects separately.',
        'failure': 'Crash after storing the artifact but before queue acknowledgement. Redeliver the message and verify there is one final artifact and one completion notice. Expire a lease while the first worker still runs; a second worker may start, but only one guarded state transition can publish completion. Make the external provider time out after accepting a send, then retry using the same provider idempotency key where supported. Revoke the reviewer during a long job and confirm that result release follows current authorization. Inject a permanent malformed payload and prevent endless retries.',
        'drill': 'Run job 84 twice with two worker identities. Pause the first after artifact creation and let the second lease expire path execute. Compare artifact IDs and effect-ledger rows after both resume. Add a provider timeout and a database deadlock as separate failure classes. Record which is safe to retry and which requires operator review. Test a burst of 83 jobs after an outage while observing downstream capacity.',
        'decision': 'A lease limits simultaneous work temporarily; stable effect identity prevents duplicate business outcomes.',
        'code': "function shouldApplyReportEffect(job, appliedEffects) {\n  const effectId = `${job.id}:${job.outputRevision}`;\n  return !appliedEffects.has(effectId);\n}\nconsole.log(shouldApplyReportEffect({ id: 84, outputRevision: 29 }, new Set(['84:29'])));\n// Output: false",
        'checks': ['Redelivery does not duplicate the artifact or notice.', 'A lease expiry cannot bypass the effect ledger.', 'Retry classes separate transient from permanent failures.'],
        'mistakes': ['Calling a queue lease an exactly-once guarantee.', 'Acknowledging before durable effect state commits.', 'Retrying a provider call with a new effect identity.'],
        'related': ['web-tech/background-jobs-and-outbox', 'web-tech/email-intent-outbox-and-idempotent-send'],
    },
    {
        'hub': 0, 'slug': 'poison-job-quarantine-and-replay-control', 'title': 'Poison Job Quarantine and Replay Control',
        'summary': 'Stop a permanently failing job from cycling forever and make repair or replay auditable.',
        'concept': 'A poison job is work that repeatedly fails without an automatic path to success. It may contain invalid input, an obsolete schema, a missing permission, or a deterministic bug. Retrying it without limit consumes worker capacity and hides newer work behind it. Quarantine removes the job from the normal retry loop, preserves a minimal failure record, and requires a deliberate repair or replay decision. A dead-letter queue is a holding mechanism, not a data-loss policy or automatic fix.',
        'case': 'A permit report job from release 27 reaches a release-29 worker with an unsupported field shape. Every attempt throws before rendering. The queue keeps redelivering it, and a backlog of valid reports grows. After a bounded number of attempts, the worker records schema version, job ID, failure class, and tenant scope in quarantine. It does not copy the full private case into an operator dashboard. A developer ships a reader for the old shape. An operator can now replay the same job identity after checking current authorization and retention, rather than creating an unrelated duplicate request.',
        'implementation': 'Classify errors before counting them. A missing required field that cannot change is permanent; a temporary storage outage should be delayed and retried. Keep retry limits and delay schedules per failure class, not as one global number. Preserve the original job identity and effect ledger when replaying. The operator action records who approved replay, the code version, why it is safe, and the new attempt number. Guard against the job being both in quarantine and active at once. Expire quarantined private payload according to the retention policy; if data is gone, report an unrecoverable result instead of pretending to replay.',
        'cost': 'A poison item can consume O(attempt count times work before failure); moving it out after a bounded threshold protects queue capacity. Quarantine storage grows with unresolved jobs, so monitor age and count by failure class. Replaying a batch of old jobs may create a second load spike and provider expense. Use a rate-limited replay queue and test one item before widening. Minimal diagnostics may require a secure path to inspect the underlying record when needed, but logging entire private payloads increases exposure.',
        'failure': 'Feed an unsupported schema version and show it becomes quarantined after the chosen attempt bound. Restore a temporary storage dependency and show that a transient job retries successfully without quarantine. Attempt to replay a quarantined job after its tenant loses permission; the worker must refuse. Replay the same item twice concurrently and prove the effect ledger still yields one result. Delete its underlying record under retention rules, then request replay and return an honest unrecoverable state. Verify valid jobs continue while the poison item is isolated.',
        'drill': 'Create 47 report jobs, one with an old schema version. Limit that class to three automatic attempts. Measure queue age for the other 46 jobs. Add a compatibility reader, authorize one replay, and record the outcome without private payload in the operator log. Repeat the replay action and verify it cannot send a second completion notice. Define when a quarantined record is deleted and what the reviewer sees afterward.',
        'decision': 'Quarantine is a controlled exception workflow with retention and replay authority, not a hidden error bucket.',
        'code': "function jobDisposition(failure) {\n  if (failure.permanent || failure.attempts >= 3) return 'quarantine';\n  return 'retry-later';\n}\nconsole.log(jobDisposition({ permanent: false, attempts: 3 }));\n// Output: quarantine",
        'checks': ['Permanent failures do not block healthy work indefinitely.', 'Replay retains job and effect identity.', 'Operators see bounded diagnostics and an audit trail.'],
        'mistakes': ['Retrying invalid input without a stop condition.', 'Copying private payloads into a broad operator queue.', 'Replaying with a new idempotency identity.'],
        'related': ['web-tech/telemetry-shapes-redaction-and-cardinality', 'web-tech/data-retention-export-and-erasure'],
    },
    {
        'hub': 0, 'slug': 'scheduled-job-overlap-cancel-and-compensation', 'title': 'Scheduled Job Overlap, Cancellation, and Compensation',
        'summary': 'Define what happens when runs overlap, users cancel, or effects already escaped the system.',
        'concept': 'A schedule specifies when work becomes eligible, not that a prior run has finished. If a new tick arrives while an old run is active, the system needs a skip, coalesce, queue, or parallel policy. Cancellation is another state transition: it can stop future steps, but it cannot automatically undo a file already delivered or a message already sent. Compensation is a separate business action that may be partial and must be visible. These policies belong to the job contract before a scheduler is enabled.',
        'case': 'A nightly permit digest groups open case changes for each tenant. A large tenant takes longer than the interval and the next tick arrives. Parallel runs would email duplicate summaries and compete for the same database snapshot. The service coalesces ticks under a tenant and schedule window key, then records the exact source revision used. Reviewer 47 later cancels a manual report while rendering is in progress. The worker checks cancellation before publishing the artifact, but if a notification was already sent, the UI reports that fact and offers a corrective notice instead of pretending the send vanished.',
        'implementation': 'Give each scheduled occurrence a stable window ID and unique tenant key. Use a database claim or lease with fencing to prevent stale workers from committing after a newer run owns the window. Define whether missed ticks are replayed after downtime and how far back the system is allowed to catch up. Cancellation writes a requested state; workers check it at safe checkpoints and commit a terminal canceled state only after they stop. Separate reversible steps, such as deleting an unpublished temporary artifact, from irreversible effects, such as an external email. A compensation action gets its own ID and audit record.',
        'cost': 'Serializing one tenant reduces duplicate work but can increase delay for a large backlog. Coalescing may skip intermediate snapshots by design, so the digest must state its revision window. A claim lookup is O(log n) with an index across scheduled windows; scanning all tenants every second is wasteful. Cancellation checks add database reads, so place them at meaningful checkpoints instead of every rendered row. Compensation has operational cost and cannot guarantee that recipients forget a sent message. Measure overlap, skipped ticks, cancel latency, and already-escaped effects.',
        'failure': 'Pause one digest run before publish, fire the next schedule tick, and verify only one owner can commit for that window. Kill the worker after it sends an email but before state commit; replay must consult the effect ledger rather than send again. Request cancellation during rendering and confirm the unpublished artifact is removed. Request it after a notice was sent and show a partial-cancellation outcome. Simulate two days of scheduler outage; enforce the documented catch-up bound instead of launching an unlimited flood. Change tenant ownership during a long run and reject stale commit.',
        'drill': 'Create a digest schedule for 83 tenants with a 47-minute window. Force one tenant to run longer than the interval and compare skip, coalesce, and queue policies. Choose one, record missed-tick behavior, and test worker fencing. Add manual cancel before and after the notification step. The status resource should distinguish stopped work, published effects, and any compensation still pending.',
        'decision': 'A scheduler and a cancel button need explicit overlap and effect policies; neither implies work can be undone.',
        'code': "function mayCommitScheduledRun(run) {\n  return run.claimVersion === run.currentVersion && !run.cancelRequested;\n}\nconsole.log(mayCommitScheduledRun({ claimVersion: 4, currentVersion: 5, cancelRequested: false }));\n// Output: false",
        'checks': ['Only the current claim can publish a scheduled window.', 'Cancellation reports effects that already escaped.', 'Catch-up work respects a stated backlog bound.'],
        'mistakes': ['Running every missed tick at once after an outage.', 'Treating cancel requested as cancel completed.', 'Deleting evidence of an external send during compensation.'],
        'related': ['web-tech/export-and-erasure-job-state', 'web-tech/feature-release-and-experiment-controls'],
    },
]
topics.extend([
    {
        'hub': 1, 'slug': 'account-recovery-enumeration-and-throttle-policy', 'title': 'Account Recovery Enumeration and Throttle Policy',
        'summary': 'Bound recovery requests without exposing which identities exist or locking out legitimate owners.',
        'concept': 'Account enumeration occurs when a public response reveals whether an identity exists. Recovery endpoints are especially sensitive because they accept an email address before authentication. A generic visible message is insufficient if response status, timing, body size, or follow-up behavior differs in a measurable way. Throttling must protect both the target account and the requesting source without making it trivial to deny service to a real owner. The recovery token remains single-use, short-lived, and separate from the request rate limit.',
        'case': 'A permit portal lets reviewers request a sign-in link. An attacker sends 83 addresses and compares response times. Known accounts trigger mail delivery inside the request and take longer; unknown accounts return immediately. The attacker learns the employee directory even though both pages say Check your inbox. The service records a recovery intent with uniform public behavior, schedules delivery outside the request path, and applies budgets to identity, source, and destination. A legitimate reviewer who reaches a limit still sees a safe next step rather than an unbounded lockout.',
        'implementation': 'Normalize addresses for lookup according to the product identity policy, but do not invent provider-specific equivalence rules. Return the same public status and generic response shape for existing and absent identities. Keep expensive delivery work asynchronous and do not leak account existence through a status endpoint exposed to the requester. Rate-limit attempts by account identity, source context, and total provider spend; any one key is bypassable or can harm shared networks. Store tokens as verifiable hashes, bind them to the intended account and action, expire them, and consume them atomically. Keep recovery failure telemetry separate from public responses and restrict its retention. For an accessible alternative after a limit, provide a support path that does not disclose whether the address is registered.',
        'cost': 'A limit check is usually O(1) with a keyed counter, but distributed accuracy, window storage, and false positives cost engineering work. Uniform public timing should not mean an arbitrary fixed sleep on every request; queuing real work and keeping response processing consistent is cheaper and less fragile. Mail sends and provider charges can dominate the endpoint cost. Monitor attempts, delivery spend, suppression, valid-user recovery completion, and denial appeals. Choose thresholds from observed usage and adjust them when shared networks or accessibility needs expose mistakes.',
        'failure': 'Compare known and unknown identities across status, body length, and repeated timing samples. Queue delivery for the known account and confirm the public response remains indistinguishable within the chosen policy. Send many requests from one source against different identities, then from many sources against one account; both patterns should hit a bounded response. Try an expired token, a used token, and a token for a different action. Simulate provider outage and avoid sending a false success claim about actual delivery. Verify a locked-out legitimate reviewer has a documented recovery route.',
        'drill': 'Issue recovery requests for reviewer 47 and a nonexistent address using 83 attempts from multiple sources. Record only bounded counters and failure classes. Consume one token once, then replay it. Measure normal recovery completion and challenge or denial rates for legitimate accounts after the policy is enabled. Check that logs do not contain raw tokens or a publicly accessible known-account label.',
        'decision': 'Recovery protection must cover identity disclosure, request volume, token replay, and legitimate completion as one contract.',
        'code': "function publicRecoveryReply(requestAccepted) {\n  return { status: 202, message: 'If this account can receive recovery mail, instructions will follow.' };\n}\nconsole.log(publicRecoveryReply(false).status === publicRecoveryReply(true).status);\n// Output: true",
        'checks': ['Known and unknown identities share public response behavior.', 'Identity and source budgets both apply.', 'A consumed recovery token cannot be replayed.'],
        'mistakes': ['Changing only the visible message while status or timing differs.', 'Using an IP limit as the sole defense.', 'Logging raw recovery tokens.'],
        'related': ['web-tech/rate-limits-and-request-budgets', 'web-tech/account-recovery-and-session-revocation'],
    },
    {
        'hub': 1, 'slug': 'expensive-request-work-budgets-and-shed-load', 'title': 'Expensive Request Work Budgets and Load Shedding',
        'summary': 'Bound CPU, bytes, fan-out, provider spend, and concurrency before costly work begins.',
        'concept': 'A request budget limits the work one call can cause, not merely how many calls arrive per minute. Search queries, uploads, report exports, and batched API operations have different CPU, memory, storage, and third-party costs. Authenticated callers can still exhaust shared capacity, especially through high fan-out or repeated expensive parameters. Admission should estimate cost before execution, enforce hard bounds during execution, and give the client an actionable rejection or deferred job path.',
        'case': 'The permit search endpoint accepts a page size and many filters. A client asks for 47,000 rows and a count for every status group. The endpoint spawns a broad database scan and serializes a huge response while regular reviewers wait. Another client submits a small page size but repeats nested filters that make the query expensive. A simple requests-per-minute counter misses both. The service caps page size, filter count, execution time, concurrent expensive searches, and per-tenant budget. Larger reports move to an admitted background job with a status resource.',
        'implementation': 'Validate the size and shape of every input before allocating work. Estimate query cost from bounded dimensions, then enforce a per-request ceiling and a separate tenant concurrency quota. Set database statement timeouts and response byte limits; cancel downstream work when the client disconnects where safe. Keep a small reserved capacity for ordinary case reads so bulk exports cannot starve them. Charge expensive third-party sends to a provider budget and return a clear retry or delayed-job contract when full. Avoid an unlimited queue that only moves overload into a later collapse. Record budget denials by category without private query strings.',
        'cost': 'A cost estimator should be O(number of provided filter terms), with a strict bound on that count. Exact query planning can be expensive, so use conservative categories for admission and measure actual CPU, rows read, bytes, and provider charges afterward. Concurrency limits trade peak throughput for predictable latency. A queue absorbs short bursts only when workers and queue age are bounded; otherwise it becomes hidden debt. Track p95 task completion, admitted versus denied cost units, queue age, and error rates for normal low-cost requests.',
        'failure': 'Send a request with a huge page size and require rejection before database work. Submit many small but expensive filter combinations and confirm the tenant cost budget engages. Kill a client connection during a long search and check that unused downstream work is canceled. Saturate export workers and verify ordinary case reads still complete. Make a provider billing limit trip and stop optional sends while preserving core task state. Try to bypass limits by splitting one large operation into many parallel calls; the aggregate budget should still bind them.',
        'drill': 'Define cost units for case search: base 1, each filter 2, group count 8, and export 31. Admit only requests under a per-call threshold and a per-tenant concurrent budget. Run 83 parallel requests from one tenant and measure ordinary read latency. Move the largest report to a job, then bound queue age and give the user a status path. Review false denials for legitimate analysts.',
        'decision': 'Budget the work induced by a request, not just the request count.',
        'code': "function searchCost(query) {\n  return 1 + query.filterCount * 2 + (query.includeGroups ? 8 : 0);\n}\nconsole.log(searchCost({ filterCount: 5, includeGroups: true }));\n// Output: 19",
        'checks': ['Inputs are bounded before allocation.', 'Bulk work cannot starve ordinary case reads.', 'Aggregate tenant work remains limited across parallel calls.'],
        'mistakes': ['Using only requests per minute for costly queries.', 'Letting a queue grow without age or size limits.', 'Continuing expensive downstream work after cancellation.'],
        'related': ['web-tech/search-query-normalization-and-ranking', 'web-tech/quality-and-capacity-engineering'],
    },
    {
        'hub': 1, 'slug': 'human-challenges-accessible-alternatives-and-signal-retention', 'title': 'Human Challenges, Accessible Alternatives, and Signal Retention',
        'summary': 'Escalate suspicious actions without making visual puzzles the only route or retaining excessive signals.',
        'concept': 'A human challenge is one control in an abuse decision, not proof that a transaction is legitimate. It can block people using assistive technology, shared devices, privacy tools, or unstable connections. Challenge decisions should follow the risk of the action, and the server must still enforce business limits after a challenge is passed. Collected signals can themselves become sensitive data. The design needs an accessible alternate path, a short retention plan, and a way to detect false positives.',
        'case': 'A permit portal receives automated account creation and document-download attempts. A new rule places a visual puzzle before every export. Reviewers using a screen reader cannot complete it, while scripts that already hold valid sessions can solve or outsource it and continue downloading. The team changes the flow: low-risk case reads use normal authorization and quotas, suspicious bursts get a graduated response, and high-cost exports may require a challenge with an accessible alternative. The challenge result does not lift tenant or file-download limits.',
        'implementation': 'Map actions to risk and expected legitimate frequency. Keep edge signals, session context, identity budgets, and business-state checks separate so one noisy signal does not decide everything. Provide a nonvisual and noninteractive support path for users who cannot complete a challenge, with an accountable review process. Bind a successful challenge to one short-lived action context rather than a permanent allowlist. Limit signal collection to what is needed to make and review the decision; mask direct identifiers in routine dashboards and expire raw events promptly. Do not publish exact thresholds in client code, but make denial reasons reviewable to operators.',
        'cost': 'Every challenge adds latency and abandonment risk. Additional scripts may consume bytes and may share data with a vendor; account for that before embedding them on every page. A rules engine costs O(number of evaluated signals) per action when signals are bounded, but high-cardinality identity histories can increase storage and lookup work. Measure legitimate task completion, false-positive appeals, automated abuse volume, challenge solve rate, and privacy retention. A broad hard block can reduce visible abuse while silently denying real users, so outcome data needs both sides.',
        'failure': 'Turn off script and attempt a low-risk public task; it should remain available. Trigger an export challenge with a screen reader and complete the alternate path. Pass the challenge, then exceed the tenant export budget; the server must still deny excess work. Replay a challenge result for another case and require rejection. Simulate a vendor script failure and preserve a path to request help. Inspect operational logs after the retention window and verify raw device signals are gone while aggregate decision counts remain.',
        'drill': 'For case 47, define normal read, bulk export, and account creation as separate actions. Test a shared office network with 83 legitimate reviewers and one abusive client. Record which actions are allowed, delayed, challenged, or denied, and why. Have a keyboard and screen-reader user complete the alternative route. After the configured retention interval, inspect stored signals and document what remains available for tuning.',
        'decision': 'A challenge should be reversible, accessible, action-scoped, and unable to override the underlying business limits.',
        'code': "function canExportAfterChallenge(request) {\n  return request.authorized && request.withinTenantBudget &&\n    (!request.challengeRequired || request.challengePassed);\n}\nconsole.log(canExportAfterChallenge({ authorized: true, withinTenantBudget: false, challengeRequired: true, challengePassed: true }));\n// Output: false",
        'checks': ['A passed challenge does not bypass authorization or quotas.', 'An accessible alternate route is tested.', 'Raw signals expire under a stated policy.'],
        'mistakes': ['Putting a visual puzzle before every task.', 'Treating challenge success as permanent trust.', 'Keeping raw device signals without a retention bound.'],
        'related': ['web-tech/accessible-feedback-and-keyboard', 'web-tech/privacy-aware-external-integrations'],
    },
    {
        'hub': 1, 'slug': 'abuse-decision-telemetry-and-false-positive-rollback', 'title': 'Abuse Decision Telemetry and False-Positive Rollback',
        'summary': 'Measure defense outcomes and recover legitimate users when a rule blocks the wrong traffic.',
        'concept': 'An abuse control is a live product rule with measurable collateral effects. Blocking suspicious volume is useful only if the application also detects when real users cannot sign in, search, or export. Decision telemetry records which class of rule acted, the action category, and the outcome, while avoiding raw secrets and unnecessary identifiers. A rollback path must disable or narrow a mistaken rule quickly without removing the base authorization and work-budget checks.',
        'case': 'The permit portal deploys a new export rule after a scraping incident. It blocks repeated downloads from one network address. A municipal office shares that address among 83 reviewers, and legitimate exports fall sharply. The security dashboard shows fewer downloads and initially calls the rule successful. Support tickets and task-completion data reveal the damage. The team narrows the rule to account and case behavior, restores a safe review route for affected users, and keeps the server authorization and per-tenant export budget intact.',
        'implementation': 'Record the decision stage, rule version, action type, coarse client category, and eventual task outcome. Use stable request correlation for short investigations, but do not expose tokens, document text, or raw private search terms in general logs. Provide a safe override or appeal process with expiry and audit. Stage new rules on observed traffic before enforcing, compare legitimate completion against abuse indicators, then increase enforcement gradually. Maintain a kill action for the new rule and a bounded fallback to older thresholds. Separate rule rollback from disabling all protection. Review the effect on shared networks, assistive technology, and low-traffic regions before declaring success.',
        'cost': 'More telemetry adds write volume and analysis work. Aggregate by bounded categories instead of individual addresses or document IDs, and retain raw correlation only for a short investigation window. False positives have a direct support and trust cost, while too-loose rules increase compute and provider spend. A staged rule incurs temporary parallel evaluation, but this can prevent a broad outage. Measure denied requests, appeals, completed legitimate tasks, abuse cost, and time to disable a bad rule. Report both denominator and time window when comparing outcomes.',
        'failure': 'Enable the new export rule for a small cohort, then simulate 83 legitimate reviewers behind one address. The dashboard must show task completion falling, not only blocks rising. Roll back the rule version and prove ordinary export resumes while authorization and byte budgets stay active. Try an expired appeal token and require the standard decision. Send a burst from many addresses under one identity and confirm account-level controls still apply. Inspect logs for case content, recovery tokens, and unbounded high-cardinality labels. Force the telemetry sink to fail; request decisions should still follow a stated safe policy.',
        'drill': 'Create an enforcement record with rule version 4, owner, cohort, stop threshold, and rollback action. Replay one day of bounded outcome counts from a shared office and a small remote region. Trigger a false-positive alert, disable only version 4, and verify the older rate and work budgets remain. Close the incident with the observed legitimate completions, abuse attempts, appeals, and retention deletion result.',
        'decision': 'Defense success includes legitimate task completion and a narrow rollback path, not only the number of blocks.',
        'code': "function shouldRollBackRule(metrics) {\n  return metrics.legitimateCompletionDrop > 0.08 || metrics.appealsPerHundred > 3;\n}\nconsole.log(shouldRollBackRule({ legitimateCompletionDrop: 0.11, appealsPerHundred: 2 }));\n// Output: true",
        'checks': ['Rule outcomes include legitimate completion.', 'Rollback removes only the new rule layer.', 'Sensitive payloads stay out of routine telemetry.'],
        'mistakes': ['Calling more blocks success without a denominator.', 'Using permanent allowlists for appeals.', 'Turning off all budgets to fix one bad rule.'],
        'related': ['web-tech/telemetry-shapes-redaction-and-cardinality', 'web-tech/production-signals-and-incident-decisions'],
    },
])

assert len(hubs) == 2 and len(topics) == 8
for number, hub in enumerate(hubs):
    path = hub['path']
    assert path not in by_path
    entry = copy.deepcopy(by_path['web-tech/production-signals-and-incident-decisions'])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + path)), path=path,
                 title=hub['title'], summary=hub['summary'], sort_order=3050 + number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    entry['data'] = {'subject_root': 'web-tech/web-technology', 'section_path': path,
                     'content_format': 'html', 'seo_ready': False, 'modules': [],
                     'resource_tabs': [{'title': 'Web Development', 'path': 'web-tech/web-technology'},
                                       {'title': 'Projects', 'path': 'web-tech/web-technology/project'},
                                       {'title': 'Quizzes', 'path': 'web-tech/quizzes'}]}
    entries.append(entry)
    by_path[path] = entry

for number, topic in enumerate(topics):
    path = 'web-tech/' + topic['slug']
    assert path not in by_path
    subprocess.run(['node', '--check', '--input-type=module'], input=topic['code'],
                   text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path['web-tech/trace-context-across-request-and-job'])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + path)), path=path,
                 title=topic['title'], summary=topic['summary'], sort_order=3060 + number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    hub_path = hubs[topic['hub']]['path']
    related = [hub_path] + ['web-tech/' + item['slug'] for item in topics
                            if item['hub'] == topic['hub'] and item['slug'] != topic['slug']] + topic['related']
    body = p(topic['concept']) + '<h2>Working case</h2>' + p(topic['case'])
    body += '<h2>Implementation boundary</h2><pre><code class="language-javascript">' + html.escape(topic['code'], quote=False) + '</code></pre>' + p(topic['implementation'])
    body += '<h2>Cost and boundaries</h2>' + p(topic['cost']) + '<h2>Failure trace</h2>' + p(topic['failure'])
    body += '<h2>Verification</h2><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in topic['checks']) + '</ul>'
    body += '<h2>Practice drill</h2>' + p(topic['drill']) + '<h2>Decision note</h2>' + p(topic['decision'])
    body += '<h3>Common Mistakes</h3><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in topic['mistakes']) + '</ul>'
    entry['body'] = body
    entry['data'] = {'subject_root': 'web-tech/web-technology', 'section_path': hub_path,
                     'content_format': 'html', 'seo_ready': False, 'kind': 'tutorial',
                     'author_path': 'authors/aitrove-editorial', 'reading_minutes': 7, 'related': related}
    entries.append(entry)
    by_path[path] = entry

for topic in topics:
    entry = by_path['web-tech/' + topic['slug']]
    entry['body'] += '<h2>Related lessons</h2><p>' + '; '.join(link(target) for target in entry['data']['related']) + '.</p>'

for number, hub in enumerate(hubs):
    group = [item for item in topics if item['hub'] == number]
    entry = by_path[hub['path']]
    entry['data']['modules'] = [{'title': hub['title'], 'summary': hub['summary'],
                                 'lessons': ['web-tech/' + item['slug'] for item in group]}]
    entry['body'] = p(hub['overview']) + '<h2>Topics in this track</h2><ul>' + ''.join(
        '<li>' + link('web-tech/' + item['slug']) + ' — ' + html.escape(item['summary']) + '</li>' for item in group) + '</ul>'
    entry['body'] += '<h2>Prerequisite paths</h2><p>' + '; '.join(link(path) for path in hub['bridges']) + '.</p>'
    entry['body'] += '<h2>Neighbor track</h2><p>' + link(hubs[1 - number]['path']) + '.</p>'

root_entry = by_path['web-tech/web-technology']
for number, hub in enumerate(hubs):
    group = [item for item in topics if item['hub'] == number]
    root_entry['data']['modules'].append({'title': hub['title'], 'summary': hub['summary'],
                                          'lessons': [hub['path']] + ['web-tech/' + item['slug'] for item in group]})
    root_entry['body'] += '<h2>' + link(hub['path']) + '</h2>' + p(hub['summary']) + '<ul>' + ''.join(
        '<li>' + link('web-tech/' + item['slug']) + ' — ' + html.escape(item['summary']) + '</li>' for item in group) + '</ul>'
root_entry['updated_at'] = stamp

crosslinks = {
    'web-tech/background-jobs-and-outbox': [hubs[0]['path'], 'web-tech/job-admission-idempotency-and-status-resource'],
    'web-tech/accepted-operations-and-status-resources': ['web-tech/job-admission-idempotency-and-status-resource'],
    'web-tech/email-intent-outbox-and-idempotent-send': ['web-tech/worker-leases-retries-and-duplicate-effects'],
    'web-tech/export-and-erasure-job-state': ['web-tech/poison-job-quarantine-and-replay-control'],
    'web-tech/rate-limits-and-request-budgets': [hubs[1]['path'], 'web-tech/expensive-request-work-budgets-and-shed-load'],
    'web-tech/account-recovery-and-session-revocation': ['web-tech/account-recovery-enumeration-and-throttle-policy'],
    'web-tech/privacy-aware-external-integrations': ['web-tech/human-challenges-accessible-alternatives-and-signal-retention'],
    'web-tech/production-signals-and-incident-decisions': ['web-tech/abuse-decision-telemetry-and-false-positive-rollback'],
}
for path, targets in crosslinks.items():
    entry = by_path[path]
    entry['body'] += '<h2>Further connections</h2><p>' + '; '.join(link(target) for target in targets) + '.</p>'
    entry['updated_at'] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_hubs': len(hubs), 'new_lessons': len(topics), 'prose_words': {
    topic['slug']: len(re.findall(r"\b[\w'-]+\b", ' '.join(str(topic[key]) for key in
        ('concept', 'case', 'implementation', 'cost', 'failure', 'drill', 'decision', 'summary')))) for topic in topics}}))
