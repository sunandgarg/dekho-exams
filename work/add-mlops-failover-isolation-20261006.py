"""Publish inference failover and shared-serving capacity lessons."""
from de_batch_publisher import publish

M = 'mlops/'
F = 'Inference failover and recovery identity'
C = 'Shared model serving and capacity isolation'

lessons = [
    {
        'path': M + 'region-failover-model-and-feature-identity',
        'title': 'Region failover for inference: match model and feature state',
        'module': F, 'project': False,
        'summary': 'A healthy standby endpoint is useful only when its model, policy and feature freshness are suitable for the decisions it will serve.',
        'sections': [
            ('Treat the region as a complete decision path', 'An inference request may cross a gateway, feature store, model worker, policy service and decision log. Moving only the model endpoint to a second region can produce a response with stale features or an older threshold. Maintain a manifest for each region: approved artifact digest, API contract, feature snapshot or watermark, policy revision, log sink and readiness state. [[mlops/run-manifest-and-artifact-lineage|Artifact lineage]] identifies the model; [[mlops/feature-training-serving-parity|feature parity]] tests whether inputs carry the intended meaning across environments.'),
            ('Decide what lag is acceptable', 'The standby may have a replicated feature stream that trails the primary by minutes. Define a recovery point for feature state and a separate maximum age for individual features. A failover gate must compare the standby watermark to request time and the feature-specific freshness budget. Some decisions may route to manual review when lagged; others may be rejected. Do not present a successful score from stale state as an ordinary decision. [[mlops/online-feature-freshness-budget-and-ttl|Freshness budgets]] and [[mlops/queue-saturation-and-fallback-policy|fallback rules]] need to agree.'),
            ('Pin the served identity', 'Record the region, artifact digest, policy revision, feature watermark and decision ID for every served response. A mutable alias such as production can point to different bytes in each region during deployment, so failover should compare resolved digests rather than alias text. Promotion must replicate and verify the package before traffic moves. If the standby has the previous approved digest, state whether that is an authorized rollback or a hold. [[mlops/promotion-attestation-and-reversible-pointer|A reversible pointer]] protects routing, but it cannot make a missing artifact appear.'),
            ('Test the unhappy path', 'Run a planned switch when the standby is current, then simulate an absent artifact and a lagged feature watermark. The first switch should succeed; the others should hold or use a named safe route. Keep the primary isolated long enough to check whether it continued issuing decisions during failover. [[mlops/receipt-region-failover-project|The failover project]] tests duplicate decision IDs and recovery records. A load balancer health check that returns 200 is weaker than a scored canary with verified identity and freshness.'),
        ],
        'code': '''def standby_route(primary, standby, maximum_lag_seconds=47):
    if primary["api_contract"] != standby["api_contract"]:
        return "hold:api-contract"
    if primary["approved_digest"] != standby["approved_digest"]:
        return "hold:model-digest"
    lag = primary["feature_watermark"] - standby["feature_watermark"]
    if lag < 0 or lag > maximum_lag_seconds:
        return "manual-review:feature-lag"
    return "serve:standby"

primary = {"api_contract": "receipt-v2", "approved_digest": "model-47",
           "feature_watermark": 1000}
standby = {**primary, "feature_watermark": 970}
assert standby_route(primary, standby) == "serve:standby"
assert standby_route(primary, {**standby, "approved_digest": "model-46"}) == "hold:model-digest"
''',
        'cost': 'The manifest comparison is O(1) time and space. Real failover costs duplicate capacity, artifact replication, fresh feature delivery and periodic drills. A 47-second global lag threshold is illustrative; the correct budget depends on the feature and decision. A healthy endpoint does not guarantee a safe feature watermark or complete decision logging.',
        'mistakes': ['Failing over based only on endpoint health.', 'Comparing alias names without resolving artifact digests.', 'Using a single freshness threshold for every feature.', 'Omitting region identity from decision records.'],
        'related': [M + 'failover-drills-and-decision-reconciliation', M + 'receipt-region-failover-project', M + 'online-feature-freshness-budget-and-ttl', M + 'promotion-attestation-and-reversible-pointer', M + 'inference-request-response-contracts'],
    },
    {
        'path': M + 'failover-drills-and-decision-reconciliation',
        'title': 'Failover drills: reconcile decisions across regions',
        'module': F, 'project': False,
        'summary': 'A failover drill must prove one logical outcome per decision key even when clients retry across regions.',
        'sections': [
            ('Give requests a stable identity', 'A client may time out after the primary writes a decision and retry against the standby. The retry should reuse the same idempotency key, scoped to caller and logical operation. A region-specific request ID is still useful for traces, but it cannot serve as the only deduplication key. Record the decision state, model digest, route and issuing region behind that stable key. [[mlops/inference-logging-privacy|Restricted logging]] keeps raw receipt data out of the reconciliation store while preserving a joinable identity.'),
            ('State the recovery contract', 'Choose recovery time and tolerable feature-state loss before a drill. Define whether a failover can serve the last approved model or must match the newest approved digest, and what to do with lagged features. Keep a single operator decision record for switch, hold, rollback and return to primary. [[mlops/region-failover-model-and-feature-identity|Region identity checks]] guard the start of serving; they do not prove that two regions will not issue conflicting responses during a split or a delayed DNS transition.'),
            ('Reconcile, then resume normal routing', 'Collect all decision events for the drill window from both regions and group them by stable key. Identical repeated responses are harmless if consumers see one committed logical decision. Different routes or digests for one key require quarantine and review. Also compare gateway counts with decision-log counts to find lost events. Preserve a record of requests with no durable response; do not invent an outcome from a log gap. [[mlops/prediction-outcome-join-and-maturity|Outcome joins]] later depend on these IDs remaining stable.'),
            ('Measure what the drill changed', 'Report switch time, rejected or manually reviewed receipts, feature lag, duplicate retries, divergent decisions, log gaps and return-to-primary time. Test a false-positive health alarm as well as an actual regional loss, because unnecessary switches create their own risk. [[mlops/receipt-region-failover-project|The project]] demonstrates an apparently successful cutover that still fails reconciliation because one receipt was scored differently on both sides. The drill is complete only when the discrepancy has an owner and a resolution.'),
        ],
        'code': '''def reconcile_decisions(events):
    grouped = {}
    for event in events:
        grouped.setdefault(event["decision_key"], set()).add(
            (event["route"], event["model_digest"]))
    divergent = sorted(key for key, outcomes in grouped.items()
                       if len(outcomes) > 1)
    return {"state": "hold" if divergent else "consistent",
            "divergent_keys": divergent}

events = [{"decision_key": "receipt-47", "route": "review",
           "model_digest": "model-47"},
          {"decision_key": "receipt-47", "route": "review",
           "model_digest": "model-47"}]
assert reconcile_decisions(events)["state"] == "consistent"
assert reconcile_decisions(events + [{**events[0], "route": "clear"}])[
    "divergent_keys"] == ["receipt-47"]
''',
        'cost': 'For n events, grouping uses O(n) expected time and O(n) memory; sorting only divergent keys adds O(d log d) time for d discrepancies. Cross-region logs may arrive late, so the drill must wait for a defined watermark before declaring no divergence. The example checks response identity, not whether the underlying business action was applied twice.',
        'mistakes': ['Generating a new idempotency key on every retry.', 'Calling the drill successful from gateway uptime alone.', 'Dropping logs from the old region before reconciliation.', 'Assuming identical API responses prove downstream side effects were deduplicated.'],
        'related': [M + 'region-failover-model-and-feature-identity', M + 'receipt-region-failover-project', M + 'inference-logging-privacy', M + 'prediction-outcome-join-and-maturity', M + 'incident-triage-and-evidence-timeline'],
    },
    {
        'path': M + 'receipt-region-failover-project',
        'title': 'Project: fail over receipt inference and reconcile every decision',
        'module': F, 'project': True,
        'summary': 'Run an inference switch with an artifact mismatch, lagged features and a cross-region retry, then publish the recovery evidence.',
        'sections': [
            ('Prepare both decision paths', 'Deploy the approved receipt artifact and API policy to two regions. Record their resolved digests, feature watermarks, contract versions and log sinks. Set a per-feature age budget and a recovery-time objective. Keep the standby out of the live route until its canary verifies a real decision response with the expected identity. [[mlops/region-failover-model-and-feature-identity|The readiness gate]] must distinguish “endpoint responds” from “safe to score.”'),
            ('Inject failure in stages', 'First interrupt the primary after it logs a decision but before the client receives the response. Retry the same logical receipt against the standby with the same idempotency key. Next stage an old artifact on standby; expect a hold. Finally restore the artifact but delay its feature stream beyond the permitted age; expect manual review or rejection. Do not weaken the gate to make the drill pass. Record every route switch and its operator.'),
            ('Reconcile the overlap window', 'Export redacted decisions and gateway requests from both regions for a fixed window that includes late log arrival. Group by stable key, compare route and model digest, and flag missing or conflicting entries. [[mlops/failover-drills-and-decision-reconciliation|The reconciliation method]] finds one conflicting receipt introduced on purpose. Investigate whether both paths produced downstream actions; an idempotent inference response does not make external side effects idempotent. Preserve disputed decisions for manual handling and avoid a second automated score.'),
            ('Return with a measured decision', 'Switch back only after the original region has the current approved digest, fresh features and complete logging. Deliver the recovery timeline, feature lag, time to safe route, duplicate retries, divergent keys, missing logs and operator decision. Link the drill to [[mlops/receipt-model-incident-drill-project|the incident playbook]] and revise its hold conditions if the drill exposed a gap. A final green health check without reconciled decisions is not a completed recovery exercise.'),
        ],
        'code': '''def recovery_state(manifests, decisions):
    primary, standby = manifests
    if primary["digest"] != standby["digest"]:
        return "hold:artifact"
    if standby["feature_lag_seconds"] > 47:
        return "manual-review:lag"
    seen = {}
    for decision in decisions:
        identity = (decision["route"], decision["digest"])
        old = seen.setdefault(decision["key"], identity)
        if old != identity:
            return "hold:divergent-decision"
    return "recover"

manifests = ({"digest": "model-47"},
             {"digest": "model-47", "feature_lag_seconds": 18})
decisions = [{"key": "r-82", "route": "review", "digest": "model-47"}]
assert recovery_state(manifests, decisions) == "recover"
assert recovery_state(manifests, decisions + [{**decisions[0], "route": "clear"}]) == "hold:divergent-decision"
''',
        'cost': 'The reconciliation loop is O(n) expected time and O(n) space for n decisions. Duplicate regional capacity and continuous artifact and feature replication are the larger costs. The sample gate is deliberately small; a real drill needs log completeness, caller idempotency and business-action checks before traffic returns.',
        'mistakes': ['Accepting standby traffic before checking its artifact digest.', 'Reusing a stale feature snapshot after a healthy model canary.', 'Counting repeated requests without comparing their issued decisions.', 'Returning to primary while the overlap window still has unresolved log gaps.'],
        'related': [M + 'region-failover-model-and-feature-identity', M + 'failover-drills-and-decision-reconciliation', M + 'receipt-model-incident-drill-project', M + 'receipt-serving-slo-project', M + 'inference-logging-privacy'],
    },
    {
        'path': M + 'multi-model-admission-and-noisy-neighbors',
        'title': 'Multi-model serving: admission control for noisy neighbors',
        'module': C, 'project': False,
        'summary': 'Sharing inference workers saves idle capacity only when one model cannot consume the memory, queue and latency budget of another.',
        'sections': [
            ('Measure each tenant separately', 'A shared worker may host a receipt triage model and an invoice classifier. Track request rate, queue wait, inference time, memory resident, load time and fallback by model digest and client. Aggregate endpoint latency hides the small model whose tail latency doubles when a larger model reloads. [[mlops/inference-latency-budget-and-tail-observation|Tail observation]] should retain the model key, while [[mlops/model-alert-symptoms-ownership-and-noise|alerts]] should name the affected owner rather than page everyone for total endpoint utilization.'),
            ('Reserve before dispatch', 'Set per-model in-flight and queued-request limits based on measured service time and memory. Reject or route overflow to a named fallback before the shared queue grows without bound. A high-priority model may need reserved slots; fairness can use weighted queues, but weights should reflect business harm and service-level objectives. One model that loads a large artifact can evict another from cache and trigger repeated cold starts. [[mlops/model-artifact-digest-and-safe-loading|Artifact loading]] is part of the serving path, not free background work.'),
            ('Isolate the expensive boundary', 'Keep models with strict tail latency or very high traffic on dedicated workers when sharing makes isolation too costly. Separate GPU memory pools or deployment groups where an out-of-memory event can restart every tenant. Requests and limits at the container level help but do not guarantee per-model fairness inside one process; the dispatch queue still needs its own control. [[mlops/queue-saturation-and-fallback-policy|Queue saturation rules]] describe how an overloaded model should fail without taking down unrelated traffic.'),
            ('Prove protection under burst', 'Load test both models together, then burst one while holding the other at a steady baseline. Record its p95/p99 latency, rejected count and model reloads. A single-model benchmark cannot reveal interference. [[mlops/receipt-shared-serving-capacity-project|The project]] forces a surge in invoice traffic while checking whether receipt triage retains reserved slots. If a shared configuration fails the test, move the strict model to dedicated capacity and measure the extra cost.'),
        ],
        'code': '''def admit_model_request(model_key, active, limits):
    if model_key not in limits:
        return "reject:unknown-model"
    if active.get(model_key, 0) >= limits[model_key]:
        return "reject:model-capacity"
    return "admit"

limits = {"receipt-risk": 47, "invoice-classifier": 20}
active = {"receipt-risk": 18, "invoice-classifier": 20}
assert admit_model_request("receipt-risk", active, limits) == "admit"
assert admit_model_request("invoice-classifier", active, limits) == "reject:model-capacity"
assert admit_model_request("unknown", active, limits) == "reject:unknown-model"
''',
        'cost': 'Admission is O(1) expected time and space per request. A production dispatcher must update counters atomically to prevent concurrent over-admission. Reserving slots lowers peak utilization, while sharing lowers idle infrastructure cost. Measure the combined bill and the induced tail latency; a cheaper shared endpoint may be unacceptable for the strict model.',
        'mistakes': ['Watching only endpoint-wide average latency.', 'Assuming container CPU limits enforce per-model fairness.', 'Letting artifact reloads consume the strict model’s reserved memory.', 'Setting queue limits without a caller-visible overload response.'],
        'related': [M + 'model-cache-warmup-and-capacity-planning', M + 'receipt-shared-serving-capacity-project', M + 'queue-saturation-and-fallback-policy', M + 'inference-latency-budget-and-tail-observation', M + 'model-alert-symptoms-ownership-and-noise'],
    },
    {
        'path': M + 'model-cache-warmup-and-capacity-planning',
        'title': 'Model cache warmup and memory planning for shared inference',
        'module': C, 'project': False,
        'summary': 'Plan resident models and cold-start behavior before a shared serving pool receives real traffic.',
        'sections': [
            ('Budget bytes, not model counts', 'Two models of similar file size can have different resident memory after deserialization, runtime compilation or device transfer. Measure artifact download, load time, peak resident bytes and steady-state bytes for each digest on the actual worker type. Reserve room for features, request buffers and runtime overhead. A cache that holds the popular models during quiet tests may churn under burst. [[mlops/multi-model-admission-and-noisy-neighbors|Admission control]] protects in-flight work; this page handles what happens before a model is ready.'),
            ('Choose a warm set from demand', 'Keep frequently used, latency-sensitive models resident and prewarm them after deployment or autoscaling. A rarely used model can load on demand if the caller contract permits a delayed or retryable response. Measure the first-request penalty separately from warmed inference. An artifact digest change invalidates the warm set even if the model name stays the same. Do not silently serve a previous digest while the new one loads; [[mlops/promotion-attestation-and-reversible-pointer|promotion identity]] has to match the response record.'),
            ('Avoid cache thrash', 'If total resident bytes exceed worker capacity, an unbounded set of sporadic models can repeatedly evict one another. Track loads, evictions, cold-start rate and p99 latency by model. Estimate memory headroom for the worst concurrent warm set, not the average number of loaded models. If the strict receipt model is repeatedly evicted by invoice variants, pin it or separate the pool. [[mlops/inference-latency-budget-and-tail-observation|Latency budgets]] should include download and load time when those events can happen on a customer request.'),
            ('Plan for scale-out and failure', 'A newly added worker begins cold, so autoscaling capacity is not immediately equivalent to ready capacity. Preload the approved digests, verify checksums and score a canary before shifting production traffic. Reserve enough ready workers to survive one failed instance without evicting every model. [[mlops/receipt-shared-serving-capacity-project|The applied capacity project]] compares cost and p99 response times for shared and dedicated pools under a burst and a forced worker restart. A capacity plan without startup measurements is incomplete.'),
        ],
        'code': '''def warm_set_fits(models, worker_memory_mb, reserve_mb):
    if worker_memory_mb <= 0 or reserve_mb < 0:
        raise ValueError("invalid memory budget")
    if any(size < 0 for size in models.values()):
        raise ValueError("invalid model size")
    available = worker_memory_mb - reserve_mb
    required = sum(models.values())
    return {"fits": required <= available,
            "headroom_mb": available - required}

resident = {"receipt-risk": 820, "invoice-classifier": 460}
assert warm_set_fits(resident, 2048, 384) == {"fits": True, "headroom_mb": 384}
assert not warm_set_fits(resident, 1400, 384)["fits"]
''',
        'cost': 'Summing m resident model sizes costs O(m) time and O(1) extra space. Storage, load and warmup cost scale with artifact bytes; model count alone says little about memory. The estimate uses measured resident sizes but omits fragmentation and temporary peak allocation, so validate it under concurrent requests and on scale-out workers.',
        'mistakes': ['Using artifact file size as resident memory without measurement.', 'Sending customer traffic to a new worker before warmup completes.', 'Ignoring a digest change because the alias name stayed the same.', 'Treating average cache hit rate as proof that critical models stay warm.'],
        'related': [M + 'multi-model-admission-and-noisy-neighbors', M + 'receipt-shared-serving-capacity-project', M + 'model-artifact-digest-and-safe-loading', M + 'inference-latency-budget-and-tail-observation', M + 'training-budget-and-resource-admission'],
    },
    {
        'path': M + 'receipt-shared-serving-capacity-project',
        'title': 'Project: protect receipt inference in a shared model pool',
        'module': C, 'project': True,
        'summary': 'Place receipt triage beside an invoice classifier, inject cold loads and a traffic burst, then choose shared or dedicated capacity from measured harm and cost.',
        'sections': [
            ('Define the serving envelope', 'The receipt model has a strict tail-latency budget and a safe manual-review fallback. The invoice classifier has a looser deadline and a larger artifact. Measure both artifacts’ resident and peak memory, load time and steady inference time on the target worker. Reserve slots for receipt requests before sharing a queue. [[mlops/model-cache-warmup-and-capacity-planning|The warm set]] names exact approved digests, and [[mlops/multi-model-admission-and-noisy-neighbors|per-model admission]] prevents invoice traffic from taking every slot.'),
            ('Run three comparative loads', 'First test each model alone to establish a baseline. Next hold receipt traffic steady while invoice traffic surges to several times its usual rate. Finally restart one worker and force both artifacts to load again. Capture p50, p95 and p99 latency, rejected requests, queue wait, cold starts, evictions and memory pressure for each model separately. Aggregate endpoint latency may look acceptable while receipt p99 fails. Keep the same input mix and concurrency for all comparisons.'),
            ('Apply the protection policy', 'When invoice traffic exhausts its allocation, reject or delay invoice requests before they enter the receipt reserve. Ensure overload uses a documented response rather than an ordinary score. If the receipt model is evicted or exceeds its deadline during the test, pin it, increase ready replicas or move it to dedicated workers. [[mlops/queue-saturation-and-fallback-policy|Fallback policy]] describes what the receipt caller sees; a container restart alone does not make a safe decision.'),
            ('Record the capacity decision', 'Compare infrastructure cost per hour with p99 receipt latency, missed requests and operator burden. Document chosen worker count, memory reserve, model limits, warmup time and when to retest. A shared pool may be cheaper at low traffic but lose that advantage once enough idle capacity is reserved for isolation. Link the result to [[mlops/receipt-serving-slo-project|the receipt service-level target]] and to [[mlops/model-alert-symptoms-ownership-and-noise|model-specific alerts]] so a future invoice surge is detected quickly.'),
        ],
        'code': '''def serving_choice(shared, dedicated, receipt_p99_limit_ms=180):
    if shared["receipt_p99_ms"] > receipt_p99_limit_ms:
        return "dedicated:latency"
    if shared["receipt_failed_requests"] > 0:
        return "dedicated:failed-requests"
    if shared["hourly_cost"] < dedicated["hourly_cost"]:
        return "shared"
    return "dedicated:cost"

shared = {"receipt_p99_ms": 214, "receipt_failed_requests": 0,
          "hourly_cost": 4.7}
dedicated = {"receipt_p99_ms": 136, "receipt_failed_requests": 0,
             "hourly_cost": 6.2}
assert serving_choice(shared, dedicated) == "dedicated:latency"
assert serving_choice({**shared, "receipt_p99_ms": 150}, dedicated) == "shared"
''',
        'cost': 'The final comparison is O(1) time and space, but the evidence requires representative multi-model load tests, cold-start trials and cost measurement. The threshold and prices are fictional planning values. A single p99 estimate from too few requests is unstable; measure over enough traffic and repeat under a worker restart before making a hosting decision.',
        'mistakes': ['Deciding from a single-model benchmark.', 'Calling shared capacity cheaper without counting reserved idle replicas.', 'Ignoring cold starts after scale-out and restart.', 'Accepting an endpoint-wide SLO while receipt-specific p99 fails.'],
        'related': [M + 'multi-model-admission-and-noisy-neighbors', M + 'model-cache-warmup-and-capacity-planning', M + 'receipt-serving-slo-project', M + 'queue-saturation-and-fallback-policy', M + 'model-alert-symptoms-ownership-and-noise'],
    },
]

crosslinks = [
    (M + 'online-feature-freshness-budget-and-ttl', M + 'region-failover-model-and-feature-identity'),
    (M + 'incident-triage-and-evidence-timeline', M + 'failover-drills-and-decision-reconciliation'),
    (M + 'receipt-model-incident-drill-project', M + 'receipt-region-failover-project'),
    (M + 'queue-saturation-and-fallback-policy', M + 'multi-model-admission-and-noisy-neighbors'),
    (M + 'model-artifact-digest-and-safe-loading', M + 'model-cache-warmup-and-capacity-planning'),
    (M + 'receipt-serving-slo-project', M + 'receipt-shared-serving-capacity-project'),
]

if __name__ == '__main__':
    publish(lessons, (F, C), crosslinks,
            'aitrove-mlops-failover-isolation-import-20261006.json', 6142,
            subject='mlops', hub_path=M + 'mlops-tutorial')
