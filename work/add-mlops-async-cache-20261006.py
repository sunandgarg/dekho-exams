"""Add asynchronous inference and prediction-cache identity lessons."""
from de_batch_publisher import publish

M = 'mlops/'
A = 'Asynchronous inference and result reconciliation'
C = 'Prediction cache identity and expiry'

lessons = [
    {
        'path': M + 'async-inference-job-contract-and-expiry',
        'title': 'Asynchronous inference: bind a queued job to immutable inputs',
        'module': A, 'project': False,
        'summary': 'A queued prediction needs a stable job ID, input digest, model identity and expiry policy because acceptance is not completion.',
        'sections': [
            ('Separate accepted from completed', 'A receipt archive may submit a scan that takes too long for a synchronous endpoint. The submission response acknowledges durable acceptance and returns a job ID; it is not a prediction. Define states such as accepted, running, succeeded, failed, expired and canceled, with one terminal state per logical job. Store caller, input object digest, approved model digest, feature contract, policy revision and submission time. [[mlops/inference-request-response-contracts|The API contract]] must distinguish these states so a caller never treats an accepted job as a clear receipt.'),
            ('Freeze what the worker will read', 'A queue can hold work while model pointers and input objects change. Pin immutable input bytes or a versioned object plus digest, and pin the model and policy approved for that job. Reject an input that has been replaced or deleted before processing; do not silently read a newer file under the old job ID. [[mlops/model-artifact-digest-and-safe-loading|Artifact identity]] protects the model package, while [[mlops/feature-contract-and-admission-gates|feature admission]] checks the delayed input when it is actually processed. The result should state the identities it used.'),
            ('Set expiry from business value', 'A receipt classification needed before daily reconciliation can become useless after the cutoff. Set queue age, processing timeout and result retention separately. Expire a job that waited too long instead of consuming compute and delivering a stale action. Caller retries should reuse a logical key and either return the existing job or a clear conflict. [[mlops/idempotent-inference-retries-and-quotas|Retry identity]] avoids duplicate work, but asynchronous jobs also need a terminal result and a retention clock.'),
            ('Test lifecycle edges', 'Stop the worker after claiming a job, delay the queue beyond expiry and change the current production model alias. The retried job must either complete under its pinned digest or fail with an explicit identity error, never switch models unnoticed. [[mlops/async-result-ledger-and-replay|The result ledger]] reconciles terminal states and late notifications. The [[mlops/receipt-async-inference-project|applied project]] exercises a job that expires while a newer model is already serving synchronous traffic.'),
        ],
        'code': '''def async_job_state(job, now_seconds):
    if now_seconds < job["submitted_at"]:
        raise ValueError("clock before submission")
    if job["state"] in {"succeeded", "failed", "expired", "canceled"}:
        return job["state"]
    if now_seconds - job["submitted_at"] > job["max_queue_age"]:
        return "expired"
    if not job["input_digest"] or not job["model_digest"]:
        return "failed"
    return job["state"]

job = {"state": "accepted", "submitted_at": 1000, "max_queue_age": 47,
       "input_digest": "input-82", "model_digest": "risk-47"}
assert async_job_state(job, 1020) == "accepted"
assert async_job_state(job, 1048) == "expired"
''',
        'cost': 'The state check is O(1) time and space. Queue storage scales with pending jobs and immutable input bytes; workers pay for warmup, inference and result writes. A stale job may be cheaper to expire than to run, but expiry must be visible to callers and counted in operating metrics.',
        'mistakes': ['Treating job acceptance as a completed model decision.', 'Resolving a mutable production alias only when a delayed worker starts.', 'Reading a changed input object under the old job ID.', 'Using one timeout for queue age, execution and result retention.'],
        'related': [M + 'async-result-ledger-and-replay', M + 'receipt-async-inference-project', M + 'idempotent-inference-retries-and-quotas', M + 'model-artifact-digest-and-safe-loading', M + 'batch-inference-partition-and-idempotency'],
    },
    {
        'path': M + 'async-result-ledger-and-replay',
        'title': 'Async result ledgers: reconcile output, failure and notification',
        'module': A, 'project': False,
        'summary': 'A notification is a hint to fetch a result, not the result itself; the ledger must account for every accepted job.',
        'sections': [
            ('Write terminal state once', 'A worker should commit either a result reference or a failure record with job ID, input digest, model digest, policy revision and completion time. A retry may race with the first attempt, so use a conditional terminal transition or an equivalent uniqueness rule. Do not overwrite a succeeded result with a later timeout notification. [[mlops/async-inference-job-contract-and-expiry|The job contract]] defines accepted and terminal states; [[mlops/idempotent-inference-retries-and-quotas|idempotency]] gives duplicate submissions one logical identity.'),
            ('Treat delivery channels separately', 'The output object, failure object and notification may be written or delivered at different times. A success notification can arrive twice; a notification can be lost even though the result exists. Reconcile accepted jobs against durable terminal records and object existence, not notification counts alone. A missing output after a success marker is a consistency incident. [[mlops/receipt-monitoring-evidence-project|The telemetry coverage ledger]] teaches the same denominator discipline: accepted work is the population, not observed notifications.'),
            ('Replay without double action', 'If a job fails due to temporary input download or output upload trouble, retry it within a bounded attempt budget using the same job ID and pinned identities. A permanent invalid payload should enter a reviewable failure state. When a result feeds a downstream payment or review action, the consumer must deduplicate by decision ID; rerunning inference can produce another score but must not trigger the action twice. [[mlops/failover-drills-and-decision-reconciliation|Decision reconciliation]] checks divergent routes during retries and regional recovery.'),
            ('Audit aged gaps', 'Report counts for accepted, running, succeeded, failed, expired and canceled jobs by submission window. Flag jobs beyond expected age without terminal state, and check result-object retention before retrying. Preserve failure cause and attempt history so an operator can distinguish compute failure from lost notification. [[mlops/receipt-async-inference-project|The project]] drops one notification and one output upload, then reconciles both without claiming the entire queue completed successfully. Include an owner and escalation time for stuck jobs.'),
        ],
        'code': '''def reconcile_async_jobs(accepted, terminal, output_exists):
    gaps = []
    invalid = []
    for job_id in accepted:
        record = terminal.get(job_id)
        if record is None:
            gaps.append(job_id)
        elif record["state"] == "succeeded" and not output_exists.get(job_id, False):
            invalid.append(job_id)
    return {"missing_terminal": sorted(gaps),
            "missing_output": sorted(invalid)}

accepted = {"job-47", "job-82"}
terminal = {"job-47": {"state": "succeeded"}}
assert reconcile_async_jobs(accepted, terminal, {"job-47": True}) == {
    "missing_terminal": ["job-82"], "missing_output": []}
assert reconcile_async_jobs(accepted, terminal, {"job-47": False})[
    "missing_output"] == ["job-47"]
''',
        'cost': 'Reconciling n accepted jobs is O(n) expected time and O(n) output space in the worst case; sorting gap lists adds O(g log g) for g gaps. Durable result objects and terminal records cost storage until retention expires. Scanning large queues can be partitioned by submission window, but the accepted-job denominator must remain complete.',
        'mistakes': ['Counting notifications as completed jobs.', 'Overwriting an existing success with a delayed retry failure.', 'Replaying a downstream side effect when an inference result is redelivered.', 'Deleting failure records before the reconciliation window closes.'],
        'related': [M + 'async-inference-job-contract-and-expiry', M + 'receipt-async-inference-project', M + 'receipt-monitoring-evidence-project', M + 'failover-drills-and-decision-reconciliation', M + 'batch-replay-versioning-and-consumer-reconciliation'],
    },
    {
        'path': M + 'receipt-async-inference-project',
        'title': 'Project: reconcile a queued receipt classification job',
        'module': A, 'project': True,
        'summary': 'Submit slow receipt scans as immutable jobs, inject output and notification failures, and account for every accepted request.',
        'sections': [
            ('Define the job envelope', 'A bulk receipt scan can take longer than an interactive deadline. Accept a versioned input object and return a job ID, submission time and status location. Pin the image digest, extraction chain revision, risk model digest and policy revision at submission. Set a queue-age limit tied to the reconciliation cutoff. [[mlops/async-inference-job-contract-and-expiry|The job contract]] makes accepted distinct from completed; [[mlops/inference-chain-contracts-and-stage-identity|chain identity]] prevents a worker from mixing stage versions later.'),
            ('Inject three failures', 'Submit three jobs. Allow one to succeed and notify normally; complete one but drop its notification; let one model invocation finish while its output upload fails. Also queue a fourth until it expires. Retry the failing job with the same pinned identities and bounded attempt count. A consumer must poll or reconcile durable state rather than wait forever for a notification. [[mlops/async-result-ledger-and-replay|The ledger]] identifies missing terminal records and a success marker without an output object.'),
            ('Protect the downstream action', 'The review system consumes completed results by decision ID. Deliver the same success twice and verify it creates one review task. If the output changes between attempts under the same job ID, quarantine the conflict rather than silently choosing the latest score. [[mlops/idempotent-inference-retries-and-quotas|Retry control]] prevents repeated expensive work at ingress, while [[mlops/failover-drills-and-decision-reconciliation|decision reconciliation]] prevents repeated or divergent actions after result delivery.'),
            ('Publish job accounting', 'Report accepted, terminal, expired, failed, retried and unresolved counts; input and model digests; output-object checks; notification delivery; consumer deduplication and time to completion. If a job has no terminal record, state that explicitly rather than treating it as failed or succeeded. The project passes only when every accepted job is terminal or has an owned open investigation. Link capacity and queue age to [[mlops/model-alert-symptoms-ownership-and-noise|operator alerts]] before enabling a larger submitter.'),
        ],
        'code': '''def async_release_report(accepted, succeeded, failed, expired):
    terminal = succeeded | failed | expired
    if (terminal - accepted or (succeeded & failed) or (succeeded & expired)
            or (failed & expired)):
        return {"state": "invalid", "unresolved": []}
    unresolved = sorted(accepted - terminal)
    return {"state": "investigate" if unresolved else "accounted",
            "unresolved": unresolved}

accepted = {"job-47", "job-82", "job-93"}
assert async_release_report(accepted, {"job-47"}, {"job-82"},
                            {"job-93"})["state"] == "accounted"
assert async_release_report(accepted, {"job-47"}, set(),
                            {"job-93"})["unresolved"] == ["job-82"]
''',
        'cost': 'Set operations take O(n) expected time and O(n) memory for n jobs. The real cost is input storage, queued worker capacity, retry compute, result storage and notification handling. Scale-out can improve throughput but does not make result commits atomic; verify durable state transitions and consumer idempotency separately.',
        'mistakes': ['Assuming a success notification proves the output object exists.', 'Letting queued jobs use whatever model alias is current at execution time.', 'Counting duplicate success deliveries as separate reviews.', 'Hiding a job with no terminal record inside a generic failure total.'],
        'related': [M + 'async-inference-job-contract-and-expiry', M + 'async-result-ledger-and-replay', M + 'batch-replay-versioning-and-consumer-reconciliation', M + 'idempotent-inference-retries-and-quotas', M + 'model-alert-symptoms-ownership-and-noise'],
    },
    {
        'path': M + 'prediction-cache-key-and-version-identity',
        'title': 'Prediction caches: key by every input that changes the decision',
        'module': C, 'project': False,
        'summary': 'A cached decision is valid only for the same authorized input, model, feature state and policy under a defined freshness window.',
        'sections': [
            ('Decide whether caching is valid', 'A receipt may be rescored after a merchant update or a policy change. Caching can save compute for repeated identical requests, but a cache hit may hide new evidence. Before enabling it, define which inputs are immutable, which features can change and the maximum age acceptable for the decision. [[mlops/online-feature-freshness-budget-and-ttl|Feature freshness]] sets an upper bound; a cache lifetime cannot make stale features fresh. Distinguish a reusable model score from a final route, because a policy threshold may change without retraining.'),
            ('Construct an identity-rich key', 'Scope a key to tenant and authorization context, canonical request digest, feature snapshot or watermark, preprocessing revision, model digest and policy revision when caching the final route. A cached score can omit policy revision only if policy is reapplied on every hit and its response is logged with the current policy. Never share a result across tenants because two receipts happen to contain the same bytes. [[mlops/inference-request-response-contracts|The API boundary]] names the response semantics; [[mlops/model-artifact-digest-and-safe-loading|artifact identity]] pins model bytes.'),
            ('Set a defensible expiry', 'Use the shortest relevant lifetime among feature freshness, business decision validity and data retention. A cache entry should carry creation time, expiry and the identities it covers; reject it when any required identity changes. A global “clear cache” during a release is not enough if some replicas or regions miss the invalidation. Versioned keys make old entries unreachable without relying on perfect broadcast. [[mlops/region-failover-model-and-feature-identity|Region failover]] needs the same digest and watermark checks before reusing a cached route.'),
            ('Measure hit quality, not just hit rate', 'Track hits, misses, stale rejections, identity mismatches and recompute latency by bounded model and route dimensions. Sample a limited set of hits for fresh recomputation to detect an invalid assumption, without turning routine sampling into customer-visible decisions. [[mlops/prediction-cache-invalidation-and-audit|Invalidation tests]] exercise policy and feature changes; [[mlops/receipt-cache-consistency-project|the project]] catches a high hit rate that conceals old merchant data.'),
        ],
        'code': '''from hashlib import sha256
import json

def decision_cache_key(tenant, request_bytes, feature_revision,
                       model_digest, policy_revision):
    fields = (tenant, sha256(request_bytes).hexdigest(), feature_revision,
              model_digest, policy_revision)
    canonical = json.dumps(fields, separators=(",", ":"), ensure_ascii=False)
    return sha256(canonical.encode()).hexdigest()

base = decision_cache_key("merchant-47", b"receipt-82", "features-r3",
                          "risk-47", "policy-4")
assert base == decision_cache_key("merchant-47", b"receipt-82",
                                  "features-r3", "risk-47", "policy-4")
assert base != decision_cache_key("merchant-47", b"receipt-82",
                                  "features-r4", "risk-47", "policy-4")
''',
        'cost': 'Hashing b request bytes and v identity bytes costs O(b + v) time and O(v) temporary space for the canonical identity. Cache storage scales with distinct live keys and response size. JSON array encoding preserves field boundaries; a raw delimiter join could make different identity tuples collide.',
        'mistakes': ['Keying only on raw request bytes while feature state changes.', 'Reusing a final route after the threshold policy changes.', 'Sharing cache entries across tenants or authorization scopes.', 'Using cache TTL longer than the shortest feature freshness budget.'],
        'related': [M + 'prediction-cache-invalidation-and-audit', M + 'receipt-cache-consistency-project', M + 'online-feature-freshness-budget-and-ttl', M + 'score-threshold-policy-and-change-control', M + 'region-failover-model-and-feature-identity'],
    },
    {
        'path': M + 'prediction-cache-invalidation-and-audit',
        'title': 'Cache invalidation tests for model, feature and policy changes',
        'module': C, 'project': False,
        'summary': 'A cache needs tests for each identity that can change a decision, including a silent feature update and a threshold-only release.',
        'sections': [
            ('List every invalidation trigger', 'A new model digest, feature revision, preprocessor, tenant permission or policy threshold can change the answer. Build a table of which values are part of a score cache versus a final-decision cache. If only scores are cached, reapply current policy and log that policy revision on every hit. If final decisions are cached, policy revision belongs in the key. [[mlops/prediction-cache-key-and-version-identity|Identity-rich keys]] make most releases naturally miss old entries without global deletion.'),
            ('Test time as an input', 'An entry can be correct when written and wrong after a feature budget expires. Validate the entry expiry against the current clock and any embedded feature watermark; do not simply reset its TTL on every hit. A stale entry must trigger recomputation or the documented fallback. [[mlops/online-feature-freshness-budget-and-ttl|Freshness limits]] apply even if the model artifact is unchanged. A client retry immediately after a timeout can use an idempotency record for the same logical decision; that is a separate promise from a general prediction cache.'),
            ('Probe cross-region and partial invalidation', 'Warm the same request in two replicas, change the feature revision and confirm both reject the old key. Then fail over to a region whose cache has an earlier entry. The fallback region must check model and feature identity rather than trust the cache presence. A broadcast invalidation can be delayed or lost, which is why versioned keys and short expiry are useful. [[mlops/region-failover-model-and-feature-identity|Failover identity]] should be checked before routing cached responses to customers.'),
            ('Audit actual hits', 'Record entry creation and expiry, model digest, feature revision, policy revision and hit or recompute decision in restricted events. Count stale rejects and conflicting recomputations. A high hit rate is a cost metric, not a correctness metric; a sampled fresh recompute should compare routes and investigate any divergence. [[mlops/receipt-cache-consistency-project|The applied project]] forces a merchant feature change and a policy-only release, then proves the original route cannot be reused.'),
        ],
        'code': '''def reusable_cached_decision(entry, current, now_seconds):
    if now_seconds >= entry["expires_at"]:
        return "miss:expired"
    required = ("tenant", "feature_revision", "model_digest",
                "policy_revision", "request_digest")
    if any(entry.get(field) != current.get(field) for field in required):
        return "miss:identity"
    return "hit"

entry = {"tenant": "merchant-47", "feature_revision": "f3",
         "model_digest": "risk-47", "policy_revision": "p4",
         "request_digest": "req-82", "expires_at": 1082}
current = {key: value for key, value in entry.items() if key != "expires_at"}
assert reusable_cached_decision(entry, current, 1047) == "hit"
assert reusable_cached_decision(entry, {**current,
       "policy_revision": "p5"}, 1047) == "miss:identity"
''',
        'cost': 'The gate compares a fixed set of fields in O(f) time and O(1) extra space for f fields. Versioned cache keys increase entry count during rollouts until old entries expire, while very short TTLs lower hit rate. A fresh recompute sample costs additional model work but can reveal silent identity bugs that hit-rate metrics cannot.',
        'mistakes': ['Refreshing TTL on every hit until old feature state lives forever.', 'Clearing one replica while another continues serving old entries.', 'Using hit rate as evidence of decision correctness.', 'Confusing an idempotent retry record with a reusable prediction cache.'],
        'related': [M + 'prediction-cache-key-and-version-identity', M + 'receipt-cache-consistency-project', M + 'online-feature-freshness-budget-and-ttl', M + 'idempotent-inference-retries-and-quotas', M + 'region-failover-model-and-feature-identity'],
    },
    {
        'path': M + 'receipt-cache-consistency-project',
        'title': 'Project: prove receipt prediction-cache identity across releases',
        'module': C, 'project': True,
        'summary': 'Warm a receipt decision, change a merchant feature and policy threshold, then verify no stale route survives a regional switch.',
        'sections': [
            ('Choose what the cache stores', 'Cache the final receipt route for a short bounded window, with tenant, request digest, feature revision, model digest and policy revision in the key. Record creation time, expiry and source decision ID. The same receipt bytes can produce a different route after merchant data or threshold changes, so bytes alone are insufficient. [[mlops/prediction-cache-key-and-version-identity|The cache identity]] must include every input that changes the final decision. Keep a separate idempotency record for a client retry of one logical request.'),
            ('Force two invalidations', 'Warm a clear result, then advance the merchant feature revision while leaving model and policy unchanged. The old entry must miss and the next decision must use fresh features. Restore the feature revision in a new test and change only the review threshold; again the final route entry must miss. Keep the original model digest constant so the test isolates feature and policy behavior. [[mlops/prediction-cache-invalidation-and-audit|The invalidation matrix]] states expected miss reasons before the test runs.'),
            ('Switch regions and compare', 'Populate a standby-region cache with the old entry. Fail traffic over after the current region has the new approved feature watermark and policy revision. The standby must reject its old entry even if the raw request and tenant match. Recompute or route to manual review if its feature state is too old. [[mlops/region-failover-model-and-feature-identity|Failover checks]] prevent a healthy standby endpoint from silently serving a stale cached route.'),
            ('Publish the outcome', 'Report hit and miss counts, stale rejections, recompute latency, decision digests, expiry settings and any divergent routes. Compare a small fresh-recompute sample with cache hits. State the maximum feature age covered by the cache and who owns changing it. A result that saves model calls but reuses an old decision fails. Link the result to [[mlops/receipt-feature-freshness-project|feature freshness]] and [[mlops/receipt-score-policy-project|policy change control]] so both release processes exercise this cache test.'),
        ],
        'code': '''def cache_release_check(warm_entry, current_identity, now_seconds):
    if now_seconds >= warm_entry["expires_at"]:
        return "recompute:expired"
    for field in ("tenant", "request_digest", "feature_revision",
                  "model_digest", "policy_revision"):
        if warm_entry[field] != current_identity[field]:
            return "recompute:" + field
    return "reuse"

warm = {"tenant": "merchant-47", "request_digest": "req-82",
        "feature_revision": "f3", "model_digest": "risk-47",
        "policy_revision": "p4", "expires_at": 1082}
identity = {key: value for key, value in warm.items() if key != "expires_at"}
assert cache_release_check(warm, identity, 1047) == "reuse"
assert cache_release_check(warm, {**identity, "feature_revision": "f4"},
                           1047) == "recompute:feature_revision"
''',
        'cost': 'The identity comparison is O(f) time and O(1) extra space for f fields. Recompute misses increase inference load during a model or policy rollout; reserve capacity for that surge. Testing both regions consumes additional cache storage and traffic, but the cost is bounded compared with silently serving decisions under an outdated feature or policy.',
        'mistakes': ['Reusing a final route after only the policy threshold changes.', 'Testing invalidation only in the primary region.', 'Making a cached score and a cached decision share one key format.', 'Counting lower inference cost as a success despite route divergence.'],
        'related': [M + 'prediction-cache-key-and-version-identity', M + 'prediction-cache-invalidation-and-audit', M + 'receipt-feature-freshness-project', M + 'receipt-score-policy-project', M + 'region-failover-model-and-feature-identity'],
    },
]

crosslinks = [
    (M + 'batch-inference-partition-and-idempotency', M + 'async-inference-job-contract-and-expiry'),
    (M + 'receipt-monitoring-evidence-project', M + 'async-result-ledger-and-replay'),
    (M + 'nightly-receipt-batch-project', M + 'receipt-async-inference-project'),
    (M + 'online-feature-freshness-budget-and-ttl', M + 'prediction-cache-key-and-version-identity'),
    (M + 'region-failover-model-and-feature-identity', M + 'prediction-cache-invalidation-and-audit'),
    (M + 'receipt-feature-freshness-project', M + 'receipt-cache-consistency-project'),
]

if __name__ == '__main__':
    publish(lessons, (A, C), crosslinks,
            'aitrove-mlops-async-cache-import-20261006.json', 6166,
            subject='mlops', hub_path=M + 'mlops-tutorial')
