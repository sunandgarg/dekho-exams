"""Add synthetic production probes and hosted-model migration modules."""
from de_batch_publisher import publish

M = 'mlops/'
PROBES = 'Synthetic production probes and monitoring integrity'
HOSTED = 'Hosted-model dependency migration and retirement'
lessons = [
    {
        'path': M + 'synthetic-probe-contract-and-traffic-isolation',
        'title': 'Synthetic inference probes: test the full route without polluting outcomes',
        'module': PROBES, 'project': False,
        'summary': 'A production probe is a controlled request with a pinned expected envelope, isolated from customer decisions and training feedback.',
        'sections': [
            ('Define a probe as a contract', 'A cold-chain spoilage model routes sensor readings to quarantine or release. A ping to the HTTP process proves only that the process answered; it does not exercise parsing, feature retrieval, model loading, policy routing or response formatting. Create a small approved set of synthetic sensor records with expected schema, model tuple, route envelope and maximum latency. A probe may tolerate a score interval rather than demand an identical float across hardware. [[mlops/inference-request-response-contracts|Response contracts]] identify the fields that must survive the route.'),
            ('Isolate probe effects', 'Mark each request with a non-user probe identity before it enters the serving path. Route its result to a separate telemetry stream and suppress any side effect that would release a real shipment, open a customer case, send a notification or join a training label. Keep a narrowly scoped allowlist of probe IDs and prevent clients from asserting that marker themselves. A synthetic request that enters outcome monitoring can manufacture apparent model success. [[mlops/prediction-outcome-join-and-maturity|Outcome joins]] should reject probe identities explicitly.'),
            ('Pick probes for failure boundaries', 'Use one ordinary sensor record, one missing-feature case and one boundary case near the quarantine threshold. Add an expired feature snapshot to verify fallback behavior. Version the probe inputs alongside the model and feature contract: a valid expected result can change after an approved threshold release. Run probes from more than one region if the service can fail over. [[mlops/region-failover-model-and-feature-identity|Failover identity]] guards against a standby running an old model or feature revision.'),
            ('Keep probes distinct from quality evidence', 'Passing probes confirms that chosen paths still behave within their contract. It does not establish population accuracy or catch an unseen cohort. Track probe failures, route mismatches and latency, then compare with representative production telemetry and mature outcomes. A bad probe may also fail because its fixture expired; treat that as a fixture issue until diagnosed. [[mlops/probe-alerts-coverage-and-rehearsal|Probe alert design]] makes these limits visible, and [[mlops/cold-chain-probe-drill-project|the project]] tests a stale-feature fallback.'),
        ],
        'code': '''def probe_result(request, response, contract):
    if request["identity"] != contract["probe_identity"]:
        return "reject:identity"
    if response["model_revision"] != contract["model_revision"]:
        return "fail:model-revision"
    if response["route"] not in contract["allowed_routes"]:
        return "fail:route"
    if response["latency_ms"] > contract["deadline_ms"]:
        return "fail:latency"
    return "pass"

contract = {"probe_identity": "cold-chain-probe-r47",
            "model_revision": "spoilage-r8", "allowed_routes": {"quarantine"},
            "deadline_ms": 82}
request = {"identity": "cold-chain-probe-r47"}
response = {"model_revision": "spoilage-r8", "route": "quarantine",
            "latency_ms": 46}
assert probe_result(request, response, contract) == "pass"
assert probe_result(request, {**response, "route": "release"}, contract) \
       == "fail:route"
''',
        'cost': 'Contract evaluation is O(1) expected time and space for a fixed route set. Each scheduled probe consumes an inference and possibly a feature read. A large probe fleet can distort capacity and cost measurements, so rate-limit it, label it in telemetry and schedule enough runs to detect outages within the required response window.',
        'mistakes': ['Calling an HTTP 200 response proof that the model path is healthy.', 'Letting synthetic decisions enter customer actions or training labels.', 'Allowing arbitrary clients to set the trusted probe marker.', 'Treating a handful of passing fixtures as evidence of model accuracy.'],
        'related': [M + 'probe-alerts-coverage-and-rehearsal', M + 'cold-chain-probe-drill-project', M + 'inference-request-response-contracts', M + 'prediction-outcome-join-and-maturity', M + 'region-failover-model-and-feature-identity'],
    },
    {
        'path': M + 'probe-alerts-coverage-and-rehearsal',
        'title': 'Probe alert quality: coverage, noise and failure rehearsal',
        'module': PROBES, 'project': False,
        'summary': 'A probe suite needs explicit route coverage, alert thresholds and rehearsed failure cases before it can be trusted on call.',
        'sections': [
            ('Map every probe to a failure boundary', 'List the service paths that matter: parse request, fetch online features, load model, apply policy and produce a response before deadline. Map each synthetic request to the steps it traverses and the failure it should catch. An all-green dashboard can still omit the fallback route or one region. Keep a coverage ledger with owner, last successful run and current model revision. [[mlops/trace-sampling-and-coverage-ledger|Trace coverage]] gives sampled production evidence; a probe ledger states which paths are deliberately exercised.'),
            ('Avoid alerting on one weak signal', 'A single timeout may be a transient network interruption; a sequence of route mismatches may be a real release fault. Set alert policy by route and expected run frequency, with a bounded confirmation window and a severe path for an unsafe release decision. Do not average a failed quarantine probe with healthy ordinary probes. Record the exact fixture, region, dependency revision and response. [[mlops/monitoring-cardinality-and-metric-identities|Metric identities]] keep revisions separate rather than hiding an issue behind one pooled series.'),
            ('Rehearse known failures', 'Before relying on a new suite, deliberately point a canary at a stale feature snapshot, a mismatched model revision and a slow dependency. Confirm that the expected probe fails, an alert reaches the correct owner and the runbook names a reversible action. Run the rehearsal in a controlled environment or dedicated canary cohort, not by corrupting live customer traffic. [[mlops/incident-triage-and-evidence-timeline|Incident evidence]] preserves the timeline for the real event.'),
            ('Measure alert utility', 'Track true incidents caught, false alerts, time to detection, unattended failures and the age of probe fixtures. Retire fixtures that no longer represent a valid request, and add new ones when the response contract or feature source changes. Suppress a known fixture failure with an expiry and owner rather than muting the entire suite. [[mlops/cold-chain-probe-drill-project|The drill]] catches a probe that stayed green because it never read the live feature store.'),
        ],
        'code': '''def probe_alert(window, policy):
    if window["unsafe_route_mismatches"]:
        return "page:unsafe-route"
    if window["scheduled_runs"] < policy["minimum_runs"]:
        return "investigate:missing-runs"
    if window["consecutive_failures"] >= policy["failure_streak"]:
        return "page:repeated-failure"
    return "observe"

policy = {"minimum_runs": 3, "failure_streak": 2}
window = {"unsafe_route_mismatches": 0, "scheduled_runs": 3,
          "consecutive_failures": 2}
assert probe_alert(window, policy) == "page:repeated-failure"
assert probe_alert({**window, "unsafe_route_mismatches": 1}, policy) \
       == "page:unsafe-route"
''',
        'cost': 'Alert evaluation is O(1) time and space after window aggregation. Probe execution cost scales with run frequency and regions; confirmation windows reduce noise but lengthen detection. A safety-critical route should use a tighter alert policy than an ordinary latency variation, with the extra page load reviewed regularly.',
        'mistakes': ['Averaging a failed critical route with healthy ordinary routes.', 'Counting missing scheduled runs as healthy because no failures arrived.', 'Muting an entire suite indefinitely for one obsolete fixture.', 'Assuming a probe exercises a dependency without verifying its route trace.'],
        'related': [M + 'synthetic-probe-contract-and-traffic-isolation', M + 'cold-chain-probe-drill-project', M + 'trace-sampling-and-coverage-ledger', M + 'monitoring-cardinality-and-metric-identities', M + 'incident-triage-and-evidence-timeline'],
    },
    {
        'path': M + 'cold-chain-probe-drill-project',
        'title': 'Project: detect a stale-feature failure in a cold-chain model',
        'module': PROBES, 'project': True,
        'summary': 'Build isolated production probes, map route coverage and rehearse a failure that a simple health check misses.',
        'sections': [
            ('Register the probe suite', 'The cold-chain service predicts whether refrigerated shipments require quarantine. Register an ordinary reading, an expired feature record and a boundary reading near the policy cutoff. Each fixture carries a revision, expected route envelope, model and feature versions, region and deadline. Mark requests as synthetic through a trusted internal identity; customer clients cannot add the marker. [[mlops/synthetic-probe-contract-and-traffic-isolation|The probe contract]] prevents synthetic outcomes from entering the claims and training ledgers.'),
            ('Expose the misleading green light', 'The HTTP readiness endpoint still returns success while the online feature store serves a snapshot from the prior day. The ordinary fixture uses a cached default and passes, but the stale-feature fixture should invoke quarantine fallback. Its route trace reveals that the first probe never fetched the feature store. Update the route coverage ledger; a green status without that dependency was incomplete. [[mlops/probe-alerts-coverage-and-rehearsal|Probe coverage]] is defined by executed paths, not fixture count.'),
            ('Exercise alert and rollback', 'Point a dedicated canary at the stale snapshot, confirm two consecutive failures and page the serving owner. An unsafe release result pages immediately. Restore the last approved feature pointer, rerun the probe and inspect production feature freshness before closing the event. Keep the probe output out of real shipment release and outcome labels throughout the drill. Record exact timestamps, revisions and decisions in [[mlops/incident-triage-and-evidence-timeline|the incident timeline]].'),
            ('Handoff an honest report', 'Report which routes the suite covers, which it does not, the delayed first detection, false alerts, regional run counts and fixture expiry dates. A passing probe does not verify statistical model quality, so schedule a separate mature-outcome review. [[mlops/drift-delayed-label-monitoring|Drift monitoring]] addresses that slower question. The completed project has a runnable route gate, an alert record and a tested rollback owner.'),
        ],
        'code': '''def cold_chain_probe_gate(trace, expected):
    missing = expected["required_stages"] - set(trace["stages"])
    if missing:
        return "fail:missing-stage"
    if trace["feature_age_min"] > expected["max_feature_age_min"]:
        return "fail:stale-feature"
    if trace["route"] != expected["route"]:
        return "fail:route"
    return "pass"

expected = {"required_stages": {"parse", "feature-read", "model", "policy"},
            "max_feature_age_min": 47, "route": "quarantine"}
trace = {"stages": ["parse", "feature-read", "model", "policy"],
         "feature_age_min": 82, "route": "quarantine"}
assert cold_chain_probe_gate(trace, expected) == "fail:stale-feature"
assert cold_chain_probe_gate({**trace, "feature_age_min": 39}, expected) \
       == "pass"
''',
        'cost': 'Stage comparison is O(s) time and O(s) extra space for s stages. Probe cost is a small stream of inference calls and traces; the rehearsal adds controlled failure work. A stale feature that goes undetected can invalidate many customer decisions, so the probe budget should match the cost and time sensitivity of that failure.',
        'mistakes': ['Testing only process readiness while skipping the feature read.', 'Letting probe requests trigger real shipment release.', 'Calling the incident closed after the probe passes without checking customer decisions.', 'Leaving fixtures tied to an obsolete model revision.'],
        'related': [M + 'synthetic-probe-contract-and-traffic-isolation', M + 'probe-alerts-coverage-and-rehearsal', M + 'incident-triage-and-evidence-timeline', M + 'drift-delayed-label-monitoring', M + 'region-failover-model-and-feature-identity'],
    },
    {
        'path': M + 'hosted-model-dependency-manifest-and-retirement-window',
        'title': 'Hosted-model dependencies: pin behavior and plan retirement',
        'module': HOSTED, 'project': False,
        'summary': 'A hosted model is a versioned production dependency whose availability, output contract and retirement date belong in the release manifest.',
        'sections': [
            ('Inventory the dependency', 'A multilingual support-ticket router calls an externally hosted language model and expects a JSON object with queue, urgency and reason. Record deployment ID, model revision when exposed, API revision, region, prompt revision, tool schema, maximum input and output sizes, timeout, rate limit, cost unit and retirement notice. If the provider can update an alias without notice, treat the alias as mutable and monitor its resolved identity where available. [[mlops/generative-release-manifest-and-prompt-model-binding|Release manifests]] bind prompt and model; the external dependency adds lifecycle and service behavior.'),
            ('Do not equate endpoint uptime with compatibility', 'A replacement may return HTTP success while changing field names, valid queue labels, refusal patterns, language handling or latency. Pin a consumer-owned parser schema and reject malformed outputs. Keep a fixture set of representative tickets and hard cases in several languages. Classify every response as valid route, abstention or contract failure before measuring task quality. [[mlops/inference-request-response-contracts|Response contracts]] protect downstream consumers from shape drift.'),
            ('Work backward from the retirement window', 'Discover announced end dates early enough to allocate evaluation, client migration and rollback time. Stand up a successor deployment while the incumbent remains available when the hosting terms allow it. Record the latest safe cutover date and what happens if no successor passes: a controlled human-routing fallback may be preferable to a silent automatic substitution. [[mlops/model-consumer-inventory-and-retirement-gates|Consumer inventory]] identifies clients that still depend on the old queue labels.'),
            ('Budget operating risk', 'A candidate with better average routing quality may cost more per ticket, exceed the latency budget or have a lower regional quota. Model the peak request rate and ticket-length distribution, then test the slow and long cases. Preserve approved input handling and retention rules in both deployments. [[mlops/hosted-model-paired-replay-and-cutover|Paired replay]] evaluates these changes before traffic shifts; [[mlops/ticket-router-hosted-model-migration-project|the project]] catches a JSON shape regression hidden by a good average score.'),
        ],
        'code': '''def dependency_ready(manifest, now_day, required_days):
    if not manifest["deployment_id"] or not manifest["api_revision"]:
        return "hold:identity"
    if manifest["retirement_day"] - now_day < required_days:
        return "urgent:migration-window"
    if not manifest["fallback_owner"]:
        return "hold:no-fallback-owner"
    return "tracked"

manifest = {"deployment_id": "ticket-route-r47", "api_revision": "r8",
            "retirement_day": 180, "fallback_owner": "support-ops"}
assert dependency_ready(manifest, 100, 47) == "tracked"
assert dependency_ready(manifest, 150, 47) == "urgent:migration-window"
''',
        'cost': 'Manifest admission is O(1) time and space. Keeping two hosted deployments during migration can double reserved capacity or incur paired-request charges. Testing peak throughput and long tickets costs inference calls, but prevents an apparently compatible successor from failing under real volume.',
        'mistakes': ['Treating a mutable deployment alias as a stable model digest.', 'Checking only status codes and ignoring output meaning.', 'Starting the migration after the retirement window closes.', 'Assuming the successor has the incumbent region, quota or retention behavior.'],
        'related': [M + 'hosted-model-paired-replay-and-cutover', M + 'ticket-router-hosted-model-migration-project', M + 'generative-release-manifest-and-prompt-model-binding', M + 'inference-request-response-contracts', M + 'model-consumer-inventory-and-retirement-gates'],
    },
    {
        'path': M + 'hosted-model-paired-replay-and-cutover',
        'title': 'Hosted-model migration: paired replay and reversible cutover',
        'module': HOSTED, 'project': False,
        'summary': 'Replay the same workload through incumbent and successor deployments, then move traffic only after behavior and capacity gates pass.',
        'sections': [
            ('Build a paired evaluation frame', 'Take a consented, redacted set of multilingual support tickets with adjudicated destination queues. Replay each ticket through incumbent and candidate using pinned prompt, schema and decoding settings appropriate to each model. Store deployment identity, request ID, latency, output validity, route and abstention reason. Because outputs may vary, compare task decisions and contract compliance rather than exact strings. [[mlops/hosted-model-dependency-manifest-and-retirement-window|The dependency manifest]] identifies both deployments and their service limits.'),
            ('Gate behavior by cohort', 'Compute route accuracy, unsafe misroutes, malformed JSON, abstention rate and p95 latency by language and ticket type. A candidate that improves overall accuracy but misroutes urgent Spanish safety tickets fails the protected slice. Count malformed responses as failures rather than dropping them from the denominator. Reconcile usage and billable units separately from model quality. [[mlops/slice-quality-gates-and-uncertainty|Slice gates]] keep a minority failure visible.'),
            ('Cut over in stages', 'Start with shadow requests where customer-facing routing still uses the incumbent. Then move a small supported cohort through a versioned pointer. Log provider deployment, prompt, parser and policy revisions on every ticket. Keep incumbent capacity and rollback path until the soak window closes. If the provider retires it before rollback is possible, preapprove a human-routing fallback; do not claim rollback remains available. [[mlops/shadow-canary-and-rollback|Canary practice]] supplies staged exposure, and [[mlops/queue-saturation-and-fallback-policy|fallback policy]] bounds customer delay.'),
            ('Retire the old path deliberately', 'After passing mature review outcomes, client contract tests and capacity checks, stop the old traffic, archive evaluation evidence, remove stale secrets and update consumer inventory. Do not delete incident evidence needed to explain tickets routed during the overlap. If an alias auto-upgrades, re-run probes and gate the resolved model revision before treating it as equivalent. [[mlops/ticket-router-hosted-model-migration-project|The project]] rehearses a late retirement notice and an urgent-ticket regression.'),
        ],
        'code': '''def hosted_candidate_gate(report, limits):
    if report["schema_failures"]:
        return "hold:response-contract"
    if report["urgent_slice_misses"] > limits["urgent_slice_misses"]:
        return "hold:urgent-slice"
    if report["p95_ms"] > limits["p95_ms"]:
        return "hold:latency"
    if report["peak_rps_capacity"] < limits["required_rps"]:
        return "hold:capacity"
    return "canary:versioned-pointer"

limits = {"urgent_slice_misses": 0, "p95_ms": 820,
          "required_rps": 47}
report = {"schema_failures": 0, "urgent_slice_misses": 1,
          "p95_ms": 680, "peak_rps_capacity": 63}
assert hosted_candidate_gate(report, limits) == "hold:urgent-slice"
assert hosted_candidate_gate({**report, "urgent_slice_misses": 0}, limits) \
       == "canary:versioned-pointer"
''',
        'cost': 'The aggregate gate is O(1) time and space. Paired replay approximately doubles calls over the sampled frame, and keeping both deployments consumes overlapping capacity. Staged rollout increases operational coordination but lets teams stop a bad candidate before every ticket reaches it.',
        'mistakes': ['Dropping malformed candidate responses from quality denominators.', 'Comparing only average routing accuracy across languages.', 'Claiming rollback after the incumbent deployment has retired.', 'Switching an alias without recording the resolved deployment revision.'],
        'related': [M + 'hosted-model-dependency-manifest-and-retirement-window', M + 'ticket-router-hosted-model-migration-project', M + 'slice-quality-gates-and-uncertainty', M + 'shadow-canary-and-rollback', M + 'queue-saturation-and-fallback-policy'],
    },
    {
        'path': M + 'ticket-router-hosted-model-migration-project',
        'title': 'Project: migrate a multilingual ticket router before model retirement',
        'module': HOSTED, 'project': True,
        'summary': 'Inventory a hosted model, run paired multilingual evaluation and cut over with a tested human-routing fallback.',
        'sections': [
            ('Register incumbent and candidate', 'A ticket router receives English, Hindi and Spanish support requests and emits queue, urgency and reason. Record incumbent and successor deployment IDs, prompt and parser revisions, region, quota, cost unit and retirement window. Freeze a redacted paired ticket set with adjudicated queues and urgent cases. [[mlops/hosted-model-dependency-manifest-and-retirement-window|The manifest]] keeps the two deployments distinct even if an API alias points to both at different times.'),
            ('Catch a hidden regression', 'The candidate improves aggregate routing accuracy yet sometimes replaces the required urgency field with priority. Its parser rejects those outputs. After a prompt repair, the candidate still sends one urgent Spanish safety ticket to a routine queue. Hold the release; neither a success status nor a better global average justifies the error. Keep schema failures in the denominator and rerun the protected slice. [[mlops/hosted-model-paired-replay-and-cutover|Paired gates]] define what must pass.'),
            ('Plan the actual cutover', 'The incumbent retires in 47 days. Reserve a shadow window, a supported-cohort canary, a soak period and a decision deadline that leaves time for fallback training. Point each accepted ticket at an explicit deployment revision and retain enough incumbent capacity for rollback until it truly disappears. If the candidate misses the deadline, route supported tickets to a staffed triage queue with queue-age monitoring rather than silently substituting an untested model.'),
            ('Deliver the migration packet', 'Report per-language route quality, urgent misroutes, malformed outputs, abstentions, p95 latency, peak request capacity, unit cost, revision identity and remaining retirement days. Record who can switch the pointer and who owns the staffed fallback. After a successful soak, update consumer inventory and archive the old route contract. Link the final decision to [[mlops/model-consumer-inventory-and-retirement-gates|retirement gates]] and [[mlops/inference-client-migration-and-contract-tests|client contract tests]].'),
        ],
        'code': '''def ticket_migration_action(candidate, days_left, minimum_window):
    if candidate["schema_failures"] or candidate["urgent_misroutes"]:
        return "hold:candidate-quality"
    if days_left < minimum_window and not candidate["fallback_staffed"]:
        return "hold:no-retirement-fallback"
    if candidate["peak_rps"] < candidate["required_rps"]:
        return "hold:capacity"
    return "canary:explicit-deployment"

candidate = {"schema_failures": 0, "urgent_misroutes": 1,
             "fallback_staffed": True, "peak_rps": 63, "required_rps": 47}
assert ticket_migration_action(candidate, 47, 21) == "hold:candidate-quality"
assert ticket_migration_action({**candidate, "urgent_misroutes": 0},
                               47, 21) == "canary:explicit-deployment"
''',
        'cost': 'The release decision is O(1) time and space. Paired evaluation uses two paid inference calls per sampled ticket, with extra human adjudication for disputed routes. Staffing a fallback costs more than automatic routing, but an untested forced upgrade can create incorrect urgent decisions and an uncontrolled incident.',
        'mistakes': ['Accepting a candidate because its global score improved despite urgent misroutes.', 'Ignoring a renamed response field that breaks the consumer parser.', 'Waiting until the incumbent is gone to design a fallback.', 'Failing to record which hosted revision routed each customer ticket.'],
        'related': [M + 'hosted-model-dependency-manifest-and-retirement-window', M + 'hosted-model-paired-replay-and-cutover', M + 'model-consumer-inventory-and-retirement-gates', M + 'inference-client-migration-and-contract-tests', M + 'queue-saturation-and-fallback-policy'],
    },
]

crosslinks = [
    (M + 'inference-request-response-contracts', M + 'synthetic-probe-contract-and-traffic-isolation'),
    (M + 'trace-sampling-and-coverage-ledger', M + 'probe-alerts-coverage-and-rehearsal'),
    (M + 'incident-triage-and-evidence-timeline', M + 'cold-chain-probe-drill-project'),
    (M + 'generative-release-manifest-and-prompt-model-binding', M + 'hosted-model-dependency-manifest-and-retirement-window'),
    (M + 'shadow-canary-and-rollback', M + 'hosted-model-paired-replay-and-cutover'),
    (M + 'model-consumer-inventory-and-retirement-gates', M + 'ticket-router-hosted-model-migration-project'),
]

if __name__ == '__main__':
    publish(lessons, [PROBES, HOSTED], crosslinks,
            'aitrove-mlops-probes-hosted-import-20261006.json', 6226,
            subject='mlops', hub_path=M + 'mlops-tutorial')
