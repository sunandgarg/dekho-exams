"""Add multi-stage inference and endpoint resource-protection lessons."""
from de_batch_publisher import publish

M = 'mlops/'
C = 'Multi-stage inference and dependency failure'
R = 'Inference resource protection and request identity'

lessons = [
    {
        'path': M + 'inference-chain-contracts-and-stage-identity',
        'title': 'Multi-stage inference: pin each stage and its contract',
        'module': C, 'project': False,
        'summary': 'A serving chain needs versioned stage inputs and outputs so a healthy final endpoint cannot hide a broken intermediate transform.',
        'sections': [
            ('Describe the whole chain', 'A receipt request may pass through image extraction, merchant normalization, risk scoring and a route policy. The final risk model alone does not define the behavior; a changed extraction model can alter every downstream feature. Record the stage order, artifact digests, input and output schemas, policy revision and overall chain revision. [[mlops/feature-training-serving-parity|Training-serving parity]] compares feature meaning, while [[mlops/inference-request-response-contracts|the public API contract]] covers only what callers send and receive. Both matter, but neither fully describes intermediate stage identity.'),
            ('Specify stage failure states', 'Each stage should return a typed success or a named failure such as unreadable image, unsupported currency, timeout or contract mismatch. Do not turn missing text into an empty string that happens to produce a plausible low-risk score. Decide which failures route to manual review and which reject the request. A stage may be optional only if the downstream model was evaluated with that stage absent. [[mlops/model-card-scope-and-limitation-register|The approved scope]] should name that degraded path; a fallback is a different decision policy, not invisible error handling.'),
            ('Allocate one end-to-end deadline', 'Give each stage a sub-budget within the caller deadline and retain queue, network and serialization time. A chain of individually fast stages can still miss the endpoint SLO, especially when a shared feature service stalls. Pass the remaining deadline downstream rather than starting a fresh full timeout at every hop. [[mlops/inference-latency-budget-and-tail-observation|Tail latency measurement]] needs stage-level spans and one end-to-end clock. Count a stage timeout as a failed or degraded decision even if a later policy returns a successful manual-review route.'),
            ('Promote as a tested unit', 'An independent extractor release can change the risk model input distribution while its digest stays fixed. Test stage contracts, a frozen end-to-end fixture set and a small live canary before changing the chain pointer. Preserve the previous complete chain for rollback; mixing old and new stages during rollback can produce an untested combination. [[mlops/receipt-inference-chain-project|The project]] injects an extractor change and verifies that the route policy receives a typed failure rather than a fabricated low-risk score.'),
        ],
        'code': '''def chain_decision(extraction, risk_score, chain):
    if extraction["digest"] != chain["extractor_digest"]:
        return {"route": "hold", "reason": "extractor-mismatch"}
    if extraction["state"] != "ready":
        return {"route": "manual-review", "reason": extraction["state"]}
    if risk_score is None or not 0 <= risk_score <= 1:
        return {"route": "hold", "reason": "invalid-risk-score"}
    return {"route": "review" if risk_score >= chain["review_at"]
            else "clear", "reason": "scored"}

chain = {"extractor_digest": "extract-47", "review_at": 0.72}
extraction = {"digest": "extract-47", "state": "ready"}
assert chain_decision(extraction, 0.81, chain)["route"] == "review"
assert chain_decision({**extraction, "state": "unreadable"}, None, chain)[
    "route"] == "manual-review"
''',
        'cost': 'The illustrated gate is O(1) time and space. A chain with s serial stages has latency near the sum of stage service and transfer times, with each stage able to fail the request. Extra stage replicas, contract tests and complete-chain rollback packages raise operating cost but prevent an untested combination of otherwise valid artifacts.',
        'mistakes': ['Logging only the final model digest.', 'Mapping extraction failure to an ordinary empty feature.', 'Giving every stage a full endpoint timeout.', 'Rolling back one stage into a chain combination never tested.'],
        'related': [M + 'stage-deadline-and-degraded-path-tests', M + 'receipt-inference-chain-project', M + 'feature-training-serving-parity', M + 'inference-request-response-contracts', M + 'inference-latency-budget-and-tail-observation'],
    },
    {
        'path': M + 'stage-deadline-and-degraded-path-tests',
        'title': 'Test partial failure and deadline exhaustion in model chains',
        'module': C, 'project': False,
        'summary': 'A chain should make one defensible decision when an early stage fails, a later stage times out or the total deadline expires.',
        'sections': [
            ('Carry remaining time forward', 'Start an absolute request deadline at ingress and recompute time remaining before each stage. The extraction stage can consume most of the budget on a hard scan; the risk model must not then begin a fresh unrestricted wait. Include queue time and transit overhead. A deadline exhausted before scoring should return a named fallback state without an invented score. [[mlops/inference-chain-contracts-and-stage-identity|Stage contracts]] establish which failures are permitted, and [[mlops/queue-saturation-and-fallback-policy|overload policy]] says how callers see the result.'),
            ('Exercise the failure matrix', 'For each stage, test malformed input, unavailable dependency, slow response, stale artifact and wrong schema. Confirm that downstream stages are skipped when their preconditions fail and that the decision log records the first causal failure. A later timeout should not overwrite an earlier contract mismatch. Keep a control case that traverses the whole chain. [[mlops/ml-test-pyramid-and-data-fixtures|Deterministic fixtures]] make the branches repeatable; a live canary checks deployed wiring and real resource limits.'),
            ('Name the degraded decision', 'Manual review may be safe for an unreadable receipt but unsafe for a request that must be rejected on authorization failure. The fallback table needs owner, expected volume and test evidence. Separate “no model score was produced” from “model score below threshold” in the response and event stream. [[mlops/human-override-and-adjudication-ledger|Reviewer actions]] later refer to what the system actually proposed. A degraded path should have its own usage counter so it cannot quietly become the normal path.'),
            ('Detect correlated dependency loss', 'Several stages may use one feature store or authentication service. A single dependency outage can drive every stage timeout and cause the fallback queue to saturate. Test under a joint failure rather than only one isolated stage at a time. [[mlops/receipt-inference-chain-project|The applied chain project]] injects both a slow extractor and missing merchant feature, then checks deadline, fallback load and complete decision identity. The operator record should identify the first broken dependency, not merely the final HTTP status.'),
        ],
        'code': '''def run_stage_budget(deadline_ms, elapsed_ms, planned_stage_ms):
    if min(deadline_ms, elapsed_ms, planned_stage_ms) < 0:
        raise ValueError("negative time")
    remaining = deadline_ms - elapsed_ms
    if remaining <= 0:
        return {"state": "fallback", "reason": "deadline-exhausted"}
    if planned_stage_ms > remaining:
        return {"state": "fallback", "reason": "stage-cannot-fit"}
    return {"state": "run", "budget_ms": remaining}

assert run_stage_budget(180, 140, 30) == {"state": "run", "budget_ms": 40}
assert run_stage_budget(180, 140, 47)["state"] == "fallback"
assert run_stage_budget(180, 181, 1)["reason"] == "deadline-exhausted"
''',
        'cost': 'Each stage budget check is O(1) time and space. The production clock should be monotonic, and measured stage duration can differ from the plan; always enforce the actual absolute deadline. Exercising s stages over f failure classes needs O(sf) cases before combined outages, while complete tracing adds storage proportional to requests and stages.',
        'mistakes': ['Resetting the full request deadline at each stage.', 'Calling manual review equivalent to a low model score.', 'Testing only isolated failures when stages share a dependency.', 'Reporting only final status and losing the first failure cause.'],
        'related': [M + 'inference-chain-contracts-and-stage-identity', M + 'receipt-inference-chain-project', M + 'queue-saturation-and-fallback-policy', M + 'ml-test-pyramid-and-data-fixtures', M + 'receipt-serving-slo-project'],
    },
    {
        'path': M + 'receipt-inference-chain-project',
        'title': 'Project: verify a receipt extraction-to-decision chain',
        'module': C, 'project': True,
        'summary': 'Pin extraction, normalization, risk scoring and route policy as one release, then inject stage failures and measure the complete deadline.',
        'sections': [
            ('Freeze a chain manifest', 'Record the extractor digest, normalization revision, risk model digest, feature contract, route policy revision and endpoint contract. Prepare a frozen set of clean scans, unreadable scans, missing merchant fields and unsupported currencies. Each fixture needs an expected route and reason, not only an expected numeric score. [[mlops/inference-chain-contracts-and-stage-identity|The chain contract]] binds intermediate outputs to the exact downstream consumer. Keep the previous complete manifest as the rollback target.'),
            ('Break one stage at a time', 'Make extraction return unreadable; scoring must not run. Make normalization return the wrong schema; the chain must hold rather than coerce a value. Delay merchant lookup until only 18 milliseconds remain in the endpoint budget; the later risk stage must not start with a fresh timeout. Record the first failure, elapsed time and fallback state. [[mlops/stage-deadline-and-degraded-path-tests|The failure matrix]] names every planned branch before the test is run.'),
            ('Test combined failure and canary', 'During a small live canary, pause the shared feature store while sending a hard scan. Count joint failures and manual-review load. Confirm that the public response says a degraded route was used and that logs retain all stage digests. If fallback saturates review staff, stop the canary. [[mlops/receipt-serving-slo-project|The service-level exercise]] provides the latency target, and [[mlops/inference-logging-privacy|decision logging]] gives a restricted trace across stages.'),
            ('Choose rollout or hold', 'Deliver the manifest, fixture results, observed stage latency, combined-failure behavior, canary volume and rollback target. A passing model-only metric does not cover a changed extractor. Approve only the tested chain combination, and make rollback restore the whole chain pointer. If an independent stage must be promoted, rerun the end-to-end fixture set and record a new chain revision. Preserve any unreadable receipts for manual handling rather than replacing them with an apparently clean score.'),
        ],
        'code': '''def chain_release_gate(stages, expected, fallback_load, capacity):
    mismatches = [name for name, digest in expected.items()
                  if stages.get(name) != digest]
    if mismatches:
        return {"state": "hold", "reason": "stage-identity",
                "stages": mismatches}
    if fallback_load > capacity:
        return {"state": "hold", "reason": "review-capacity"}
    return {"state": "canary"}

expected = {"extractor": "extract-47", "risk": "risk-82",
            "policy": "policy-3"}
assert chain_release_gate(expected, expected, 18, 23)["state"] == "canary"
assert chain_release_gate({**expected, "extractor": "extract-46"},
                          expected, 18, 23)["reason"] == "stage-identity"
''',
        'cost': 'Comparing s stage identities takes O(s) time and O(s) mismatch space. End-to-end tests have cost proportional to the number of fixtures and stage invocations; a live canary adds staff and fallback capacity. The gate cannot substitute for stage outputs, deadline measurements or evidence that the fallback actually reaches the review queue.',
        'mistakes': ['Approving a model digest without pinning its extractor.', 'Starting later stages after an earlier required stage fails.', 'Letting a degraded route overload human review.', 'Rolling back only the risk model and retaining the new extractor.'],
        'related': [M + 'inference-chain-contracts-and-stage-identity', M + 'stage-deadline-and-degraded-path-tests', M + 'receipt-serving-slo-project', M + 'receipt-feature-admission-project', M + 'inference-logging-privacy'],
    },
    {
        'path': M + 'inference-payload-and-compute-admission',
        'title': 'Inference ingress: bound payload size and compute before model work',
        'module': R, 'project': False,
        'summary': 'Validate input shape and resource cost before parsing or model execution so one request cannot exhaust a shared serving pool.',
        'sections': [
            ('Limit the earliest expensive boundary', 'A receipt endpoint may accept a scan image and metadata. Reject oversized bodies at the gateway before copying them into application memory; then check decoded dimensions, file count, page count and permitted format before extraction. A compressed file can expand far beyond its upload size, so both compressed and decoded limits matter. [[mlops/inference-request-response-contracts|The API contract]] must return a stable rejection code. Do not let a malformed payload reach a GPU worker simply because its HTTP body passed a size check.'),
            ('Estimate work by request class', 'A one-page image and a 47-page document can have very different extraction and inference cost. Define bounded request classes with a maximum estimated work unit, then admit against the model-specific concurrency and queue budget. Separate authentication, authorization and customer quota from model capacity; a valid customer can still send a request that exceeds the endpoint limit. [[mlops/multi-model-admission-and-noisy-neighbors|Per-model admission]] protects neighboring models; this ingress gate prevents a single allowed request from consuming unreasonable resources.'),
            ('Fail clearly and do not retry blindly', 'Return an explicit client error for invalid shape or unsupported size; retriable overload needs a different code and bounded retry advice. A caller that retries an invalid 47-page document will only repeat the waste. Log a reason and bounded size bucket, not the document bytes, in operational telemetry. [[mlops/monitoring-cardinality-and-metric-identities|Metric-cardinality rules]] keep document IDs out of labels, while [[mlops/inference-logging-privacy|restricted logs]] retain a joinable request ID if investigation is needed.'),
            ('Test bypass and expansion cases', 'Exercise tiny files with huge declared dimensions, compressed payloads with high expansion ratios, malformed metadata, arrays with too many elements and concurrent near-limit requests. Ensure the gateway and application enforce compatible limits; one layer may be bypassed during internal calls. [[mlops/receipt-endpoint-resource-guard-project|The project]] demonstrates a request rejected before extraction and a permitted request that still meets its latency budget. A 413 response alone does not prove the decoder never allocated memory.'),
        ],
        'code': '''def admit_receipt_payload(request, max_bytes=4_700_000,
                          max_pages=8, max_pixels=18_000_000):
    checks = (request["body_bytes"], request["pages"], request["pixels"])
    if any(value < 0 for value in checks):
        raise ValueError("negative payload measure")
    if request["body_bytes"] > max_bytes:
        return "reject:body-size"
    if request["pages"] > max_pages or request["pixels"] > max_pixels:
        return "reject:decode-work"
    return "admit"

receipt = {"body_bytes": 470_000, "pages": 2, "pixels": 8_200_000}
assert admit_receipt_payload(receipt) == "admit"
assert admit_receipt_payload({**receipt, "pages": 47}) == "reject:decode-work"
''',
        'cost': 'Checking declared bounds is O(1) time and space. Decoding still costs work proportional to expanded pixels and pages, so verify actual decoded size before large allocations and enforce runtime memory limits. Tight limits may reject legitimate long receipts; choose them from measured use and a documented alternate review path.',
        'mistakes': ['Checking upload bytes but not decoded pixel count.', 'Treating invalid shape as retriable server overload.', 'Placing the first size check after expensive decoding.', 'Assuming valid authentication makes resource use safe.'],
        'related': [M + 'idempotent-inference-retries-and-quotas', M + 'receipt-endpoint-resource-guard-project', M + 'inference-request-response-contracts', M + 'multi-model-admission-and-noisy-neighbors', M + 'monitoring-cardinality-and-metric-identities'],
    },
    {
        'path': M + 'idempotent-inference-retries-and-quotas',
        'title': 'Inference retries: bound repeated work and preserve one decision',
        'module': R, 'project': False,
        'summary': 'A retry after timeout should not trigger unlimited model work or create conflicting decisions for one logical request.',
        'sections': [
            ('Name the logical operation', 'Give the caller an idempotency key scoped to tenant, endpoint and a canonical request digest. A retry of the same request can retrieve the completed decision; reusing a key with a different payload must be rejected. Preserve the decision ID, model digest and policy revision with the result. [[mlops/failover-drills-and-decision-reconciliation|Cross-region reconciliation]] needs this stable identity during failover, while [[mlops/inference-request-response-contracts|the API contract]] states the expected retry behavior.'),
            ('Stop duplicate in-flight work', 'Check a durable or appropriately shared in-flight record before starting inference. A second request with the same key may wait for the first within its deadline or receive a retry-later state; it must not launch another expensive extraction. Set a finite record lifetime longer than expected retry windows and protect the record update against races. An in-memory dictionary on one worker cannot deduplicate across replicas or regions. [[mlops/region-failover-model-and-feature-identity|Region identity]] also determines whether replay of an old decision is allowed after policy changes.'),
            ('Apply quotas at multiple levels', 'Bound request rate, in-flight work, queued work and cumulative compute by tenant and model. A small fast request repeated thousands of times can be as harmful as one oversized document. Reject excess before expensive stages and return a stable overload response. Do not count a cached replay as fresh model capacity, but include it in the caller rate budget if abuse is possible. [[mlops/inference-payload-and-compute-admission|Payload admission]] handles individual requests; [[mlops/queue-saturation-and-fallback-policy|queue limits]] keep accepted work bounded.'),
            ('Verify conflict and timeout behavior', 'Send the same key twice concurrently, then send the same key with changed contents. Expect one logical decision for identical requests and an explicit conflict for changed contents. Force the first response to be lost after its decision was committed; retry should return the prior decision identity. [[mlops/receipt-endpoint-resource-guard-project|The project]] tests that repeated receipts do not inflate model work or create a second route. A caller must know whether a timeout means “not processed” or “unknown”; it should never assume the former.'),
        ],
        'code': '''from hashlib import sha256

def replay_status(records, tenant, key, payload):
    identity = (tenant, key)
    digest = sha256(payload).hexdigest()
    existing = records.get(identity)
    if existing is None:
        records[identity] = {"digest": digest, "decision": "decision-47"}
        return "new"
    if existing["digest"] != digest:
        return "conflict"
    return "replay:" + existing["decision"]

records = {}
assert replay_status(records, "merchant-82", "key-47", b"receipt-A") == "new"
assert replay_status(records, "merchant-82", "key-47", b"receipt-A") == "replay:decision-47"
assert replay_status(records, "merchant-82", "key-47", b"receipt-B") == "conflict"
''',
        'cost': 'Digesting b payload bytes costs O(b) time and O(1) extra hash space; the record lookup is O(1) expected time. A durable shared record uses O(k) storage for k active keys and needs atomic creation. The example is single-process and deliberately lacks cross-worker synchronization; production deduplication must enforce one writer or transactional uniqueness.',
        'mistakes': ['Generating a new key on each retry.', 'Accepting one key with a different payload.', 'Using worker-local memory as cross-region deduplication.', 'Retaining keys for less time than clients retry.'],
        'related': [M + 'inference-payload-and-compute-admission', M + 'receipt-endpoint-resource-guard-project', M + 'failover-drills-and-decision-reconciliation', M + 'queue-saturation-and-fallback-policy', M + 'receipt-inference-api-migration-project'],
    },
    {
        'path': M + 'receipt-endpoint-resource-guard-project',
        'title': 'Project: protect receipt inference from expensive and repeated input',
        'module': R, 'project': True,
        'summary': 'Place shape limits, tenant quotas and idempotency ahead of extraction, then prove rejected and retried requests do not consume duplicate model work.',
        'sections': [
            ('Write the ingress contract', 'Specify maximum upload bytes, decoded pixels, pages and accepted formats for receipt scans. Define a bounded alternate review path for legitimate larger submissions. Add tenant rate and in-flight limits, a stable idempotency key and a response code for size, conflict and temporary overload. [[mlops/inference-payload-and-compute-admission|Payload admission]] should run before extraction; [[mlops/inference-request-response-contracts|the public contract]] explains each rejection to callers.'),
            ('Inject resource abuse cases', 'Send a compressed scan whose decoded dimensions exceed the pixel limit, a 47-page document and a burst of small valid receipts. Verify oversized requests never start the extractor or GPU worker. The burst should hit a tenant limit while unrelated tenants retain their model slots. Record gateway request count, admission result, expensive stage invocations and caller-visible response for each case. [[mlops/multi-model-admission-and-noisy-neighbors|Shared model isolation]] adds protection against one model consuming the entire pool.'),
            ('Test retries after uncertain completion', 'Allow one valid receipt to commit a decision, then drop its response. Retry with the original tenant, key and payload: return the existing decision ID without a second model invocation. Retry with the same key but changed bytes: reject as a conflict. [[mlops/idempotent-inference-retries-and-quotas|The retry rule]] must use an atomic shared record in the deployed system. A local unit example proves branch logic, not cross-replica safety; run the integration test across two workers.'),
            ('Publish the load and safety result', 'Report accepted, rejected, replayed and conflicting requests; extraction and model invocation counts; p99 latency for unaffected tenants; quota state and deduplication record lifetime. Identify the owner of each limit and the procedure for a legitimate oversized document. A guard that silently drops requests or converts malformed input to a low-risk score fails this exercise. Link the result to [[mlops/receipt-serving-slo-project|the serving target]] and to [[mlops/receipt-monitoring-evidence-project|complete telemetry counts]] so the protection is observable.'),
        ],
        'code': '''def guard_result(payload_bytes, pages, replay_state, tenant_active):
    if payload_bytes > 4_700_000 or pages > 8:
        return "reject:payload"
    if replay_state == "conflict":
        return "reject:key-conflict"
    if replay_state == "completed":
        return "return:prior-decision"
    if tenant_active >= 23:
        return "retry:tenant-capacity"
    return "start:inference"

assert guard_result(470_000, 2, "new", 18) == "start:inference"
assert guard_result(470_000, 47, "new", 0) == "reject:payload"
assert guard_result(470_000, 2, "completed", 23) == "return:prior-decision"
''',
        'cost': 'The illustrated gate is O(1) time and space per request. A real decoder needs resource limits after expansion, and deduplication requires a shared atomic store. Quotas trade some peak throughput for isolation. The integration check should confirm that rejected requests never enter expensive stages and that replayed responses do not consume fresh inference capacity.',
        'mistakes': ['Enforcing payload limits only after extraction.', 'Returning a fresh decision for a retry whose first response was lost.', 'Letting one tenant consume reserved capacity for others.', 'Using a non-atomic per-worker retry map in a multi-worker deployment.'],
        'related': [M + 'inference-payload-and-compute-admission', M + 'idempotent-inference-retries-and-quotas', M + 'receipt-serving-slo-project', M + 'multi-model-admission-and-noisy-neighbors', M + 'receipt-monitoring-evidence-project'],
    },
]

crosslinks = [
    (M + 'feature-training-serving-parity', M + 'inference-chain-contracts-and-stage-identity'),
    (M + 'inference-latency-budget-and-tail-observation', M + 'stage-deadline-and-degraded-path-tests'),
    (M + 'receipt-feature-admission-project', M + 'receipt-inference-chain-project'),
    (M + 'inference-request-response-contracts', M + 'inference-payload-and-compute-admission'),
    (M + 'failover-drills-and-decision-reconciliation', M + 'idempotent-inference-retries-and-quotas'),
    (M + 'receipt-serving-slo-project', M + 'receipt-endpoint-resource-guard-project'),
]

if __name__ == '__main__':
    publish(lessons, (C, R), crosslinks,
            'aitrove-mlops-chains-abuse-import-20261006.json', 6154,
            subject='mlops', hub_path=M + 'mlops-tutorial')
