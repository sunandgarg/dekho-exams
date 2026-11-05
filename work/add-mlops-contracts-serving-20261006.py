"""Add feature admission and serving reliability to the MLOps curriculum."""
from de_batch_publisher import publish

M = 'mlops/'
C = 'Feature contracts and data admission'
S = 'Serving reliability and capacity'

lessons = [
    {
        'path': M + 'feature-contract-and-admission-gates',
        'title': 'Feature contracts: admit only usable inference records',
        'module': C, 'project': False,
        'summary': 'An inference feature contract defines types, units, absence rules, event clocks and rejection behavior before a record reaches a model.',
        'sections': [
            ('Define the boundary that the model actually needs', 'A receipt-risk model expects amount in minor currency units, a merchant age in days and a transaction timestamp. Calling all three “numbers” is not a contract. Specify accepted types, units, allowable ranges, missing-value policy and the version of each field definition. A value of 4700 means something different in cents and whole currency units. [[mlops/feature-training-serving-parity|Training-serving parity]] compares values after this boundary; the admission gate first decides whether values are valid enough to compare.'),
            ('Separate malformed, absent and stale values', 'A missing merchant age can be an allowed unknown, while an age of minus 47 days signals a clock or join defect. A timestamp from an event that arrives 82 minutes late is different again. Give each state its own decision: reject, substitute an explicit missing indicator, or route to a fallback. Do not quietly cast strings to floats when a source changes its schema. The returned decision should name the violated rule without copying sensitive payloads into logs. [[mlops/inference-logging-privacy|Inference logging]] covers that diagnostic boundary.'),
            ('Tie the contract to a model version', 'A new model might accept a category that the old model cannot encode. Keep the expected contract with the model artifact and validate a candidate against both the incoming stream and the rollback model before promotion. A schema file alone is weak evidence; run the same validation on a frozen slice containing nulls, extremes and source revisions. [[mlops/model-registry-promotion-gates|Promotion gates]] should require the contract result for the exact artifact digest.'),
            ('Measure rejection as a production signal', 'Track admitted, rejected and fallback counts by feature-contract version and low-cardinality source class. A sudden jump in rejected receipts may be a provider defect rather than a model failure. Review representative rejected records under controlled access and inspect the first bad source revision. Test malformed types, changed units, nonfinite values and future timestamps before a release. The [[mlops/receipt-feature-admission-project|admission project]] turns these cases into a release gate.'),
        ],
        'code': '''from datetime import datetime, timezone
from math import isfinite

def admit_receipt(receipt, now):
    amount = receipt.get("amount_minor")
    if type(amount) is not int or not 0 <= amount <= 4_700_000:
        return {"state": "reject", "reason": "amount-contract"}
    age = receipt.get("merchant_age_days")
    if age is not None and (type(age) not in (int, float) or
                            not isfinite(age) or not 0 <= age <= 36_500):
        return {"state": "reject", "reason": "merchant-age-contract"}
    occurred = receipt.get("occurred_at")
    if not isinstance(occurred, datetime) or occurred.tzinfo is None:
        return {"state": "reject", "reason": "event-clock-contract"}
    if occurred > now:
        return {"state": "reject", "reason": "future-event"}
    return {"state": "admit", "features":
            {"amount_minor": amount, "merchant_age_days": age}}

clock = datetime(2026, 10, 6, tzinfo=timezone.utc)
valid = {"amount_minor": 4_700, "merchant_age_days": None,
         "occurred_at": clock}
assert admit_receipt(valid, clock)["state"] == "admit"
assert admit_receipt({**valid, "amount_minor": True}, clock)["state"] == "reject"
''',
        'cost': 'Validation is O(f) time for f checked fields and O(f) space for the accepted feature copy. Per-record validation cost is small beside model inference, but rejected-record review and quarantine storage grow with bad-source volume. Do not let an unlimited quarantine queue turn one schema incident into a storage incident.',
        'mistakes': ['Treating cents and whole currency units as interchangeable.', 'Silently converting malformed values instead of recording a contract failure.', 'Using one null rule for every feature.', 'Logging the full rejected receipt in a broad-access metrics stream.'],
        'related': [M + 'feature-schema-evolution-and-consumers', M + 'receipt-feature-admission-project', M + 'feature-training-serving-parity', M + 'model-registry-promotion-gates', 'feature-stores/feature-stores-tutorial'],
    },
    {
        'path': M + 'feature-schema-evolution-and-consumers',
        'title': 'Feature schema evolution: keep producers and rollback models compatible',
        'module': C, 'project': False,
        'summary': 'A feature rename or unit change is a release with consumers, not an isolated edit to a training column.',
        'sections': [
            ('Inventory every consumer of a field', 'A receipt amount feeds online scoring, batch replay, dashboards and perhaps the previous model retained for rollback. Before changing `amount_minor`, list each consumer and the contract version it accepts. Adding an optional field may be safe for a tolerant reader, yet removing a field can break the rollback path. [[mlops/run-manifest-and-artifact-lineage|Run lineage]] records the training input version; runtime compatibility must still be tested against live producers.'),
            ('Distinguish additive changes from changed meaning', 'Changing an integer amount from cents to thousands of cents without renaming it preserves the type and destroys the meaning. Introduce a new field and migrate consumers in stages. Keep both fields only while both are derived from one authoritative source and checked for equivalence. Document when the old field stops being emitted. A name alias can make a deployment pass while leaving historical replay wrong. [[mlops/feature-contract-and-admission-gates|Admission rules]] should reject an unexpected contract version rather than guess units.'),
            ('Prove temporal consistency', 'Training rows need values available at their prediction time. An updated feature view may backfill corrected values that did not exist when older decisions were made. Store event time and availability time, and define whether replay means historical truth or information available then. [[feature-stores/historical-point-in-time-join|Point-in-time joins]] address the latter. A schema migration test should include old and new event windows, late-arriving updates and the previous serving model.'),
            ('Release in a reversible order', 'First deploy readers that understand the new field while still accepting old records. Then emit both fields, compare values, move model candidates to the new contract and finally retire the old field after the rollback window closes. Gate each step on mismatch and unknown-version rates. The [[mlops/receipt-feature-admission-project|receipt admission project]] tests a unit migration with a deliberately stale consumer so the hold decision is visible.'),
        ],
        'code': '''def compatible_contract(producer, consumers):
    failures = []
    for consumer_name, required in consumers.items():
        for field, unit in required.items():
            if producer.get(field) != unit:
                failures.append((consumer_name, field, unit))
    return {"ready": not failures, "failures": failures}

producer = {"amount_minor": "cent", "merchant_age_days": "day",
            "amount_thousands": "thousand-cent"}
consumers = {"candidate-r8": {"amount_thousands": "thousand-cent"},
             "rollback-r7": {"amount_minor": "cent"}}
assert compatible_contract(producer, consumers)["ready"]
assert not compatible_contract({"amount_thousands": "thousand-cent"},
                               consumers)["ready"]
''',
        'cost': 'Checking c consumers against their required fields costs O(total required fields) time and O(failures) space. Dual-writing two representations adds producer work and temporary storage; it also creates a comparison obligation. The example checks declared fields and units, while a real release must also test value equivalence and historical availability.',
        'mistakes': ['Changing a unit without changing the field identity.', 'Deleting the old field while a rollback model still requires it.', 'Backfilling future-known values into a historical training replay.', 'Keeping dual writes forever without a retirement condition.'],
        'related': [M + 'feature-contract-and-admission-gates', M + 'receipt-feature-admission-project', M + 'run-manifest-and-artifact-lineage', M + 'feature-training-serving-parity', 'feature-stores/historical-point-in-time-join'],
    },
    {
        'path': M + 'receipt-feature-admission-project',
        'title': 'Project: release a versioned receipt feature admission gate',
        'module': C, 'project': True,
        'summary': 'Build a replayable admission gate for a receipt model, then prove a unit migration does not break the candidate or rollback service.',
        'sections': [
            ('State the operating task', 'A payment intake system scores receipts with amount, merchant age and event time. The model must never see an amount with unknown units, a future event or a field silently converted from text. Define accepted, rejected and fallback outcomes, plus one short reason code for each failure. The [[mlops/feature-contract-and-admission-gates|feature contract]] is part of the model release package, not an informal convention in the request handler.'),
            ('Build adversarial fixtures', 'Create valid records, null merchant ages, boolean amounts, oversized amounts, stale timestamps, future timestamps and an upstream change from cents to thousands of cents. Freeze expected decisions before writing migration code. Include both the new candidate and the old rollback model as consumers. [[mlops/feature-schema-evolution-and-consumers|Schema evolution]] forces the migration to support both until rollback is no longer needed.'),
            ('Wire admission to promotion', 'Store the contract version, model digest and source schema revision with each test result. Reject a candidate whose fixture pass rate falls below its declared threshold, even if offline quality improved. Shadow live requests through the new gate and compare outcome counts with the old gate without using the shadow output for customer decisions. Keep restricted examples of rejected data for debugging; publish only reason counts and low-cardinality source labels. [[mlops/shadow-canary-and-rollback|Shadow rollout]] provides the comparison pattern.'),
            ('Review the release evidence', 'Report fixture failures, live rejection rate, unknown-version rate, candidate and rollback compatibility, and median and tail admission latency. Simulate an upstream unit change after candidate promotion; the gate must hold requests or use an approved fallback, not issue scores in the wrong units. Record who approves retirement of the old field and the earliest date the rollback model can be removed.'),
        ],
        'code': '''def admission_release(candidate_checks, rollback_checks, shadow_counts):
    if not all(candidate_checks.values()):
        return {"state": "hold", "reason": "candidate-fixture"}
    if not all(rollback_checks.values()):
        return {"state": "hold", "reason": "rollback-fixture"}
    total = shadow_counts["accepted"] + shadow_counts["rejected"]
    if total < 470:
        return {"state": "hold", "reason": "small-shadow-sample"}
    if shadow_counts["rejected"] / total > 0.03:
        return {"state": "hold", "reason": "rejection-rate"}
    return {"state": "ready", "checked": total}

fixtures = {"units": True, "future_clock": True, "nulls": True}
rollback = {"old_amount_minor": True}
assert admission_release(fixtures, rollback,
                         {"accepted": 489, "rejected": 11})["state"] == "ready"
assert admission_release(fixtures, {"old_amount_minor": False},
                         {"accepted": 489, "rejected": 11})["state"] == "hold"
''',
        'cost': 'The gate evaluation is O(f) time for fixture results and O(1) extra space aside from its response. Running both model contracts in shadow doubles validation work for sampled requests. Set a bounded review queue for rejected records, and treat threshold selection as an explicit product decision grounded in observed traffic.',
        'mistakes': ['Passing candidate fixtures while ignoring the retained rollback model.', 'Treating a high rejection rate as harmless because accepted predictions look accurate.', 'Using shadow outputs for customer decisions.', 'Publishing raw rejected receipts through a monitoring dashboard.'],
        'related': [M + 'feature-contract-and-admission-gates', M + 'feature-schema-evolution-and-consumers', M + 'shadow-canary-and-rollback', M + 'model-registry-promotion-gates', M + 'receipt-triage-release-project'],
    },
    {
        'path': M + 'inference-latency-budget-and-tail-observation',
        'title': 'Inference latency budgets: measure queue, feature and model time',
        'module': S, 'project': False,
        'summary': 'A model that computes quickly can still miss the service deadline when requests wait in a queue or feature lookup stalls.',
        'sections': [
            ('Allocate the request deadline', 'A receipt-scoring endpoint has a 240 ms service deadline. Reserve time for ingress, feature lookup, queue wait, model execution and response serialization. The budget is a design constraint, not a promise that each part always finishes exactly on schedule. Instrument each stage with a bounded set of labels: route, model version, outcome class and region. Never put request IDs into metric labels; retain request-level correlation in traces with privacy controls. [[mlops/inference-logging-privacy|Inference logs]] distinguish useful join keys from unnecessary payloads.'),
            ('Measure tails and failed requests', 'A low mean can hide an overloaded slice. Record duration histograms and count timeouts, cancellations, rejections and fallback responses in the same evaluation window. A p95 value calculated only from successful requests excludes some of the slowest calls. Compare candidate and incumbent under comparable traffic and hardware. [[mlops/shadow-canary-and-rollback|Canary release]] needs this operational comparison in addition to model quality.'),
            ('Use one end-to-end clock', 'Start a monotonic timer when the service accepts a request and stop it when a response or terminal failure is committed. Service stages can have nested timers, but their measured durations may overlap under asynchronous work; do not sum overlapping spans and call that user latency. Include retries and queue wait in the end-to-end result. Set a downstream deadline that leaves time to return an honest fallback before the client gives up.'),
            ('Test load shapes, not just steady throughput', 'Run bursts, cold starts, large feature payloads and a slow feature store. Track latency by model version and outcome, but keep label cardinality bounded. The [[mlops/receipt-serving-slo-project|serving SLO project]] asks whether the system can reject excess work promptly instead of letting a growing queue make every customer wait. A fast model without admission control is still an unreliable service.'),
        ],
        'code': '''def request_budget(stages_ms, deadline_ms):
    if deadline_ms <= 0 or any(value < 0 for value in stages_ms.values()):
        raise ValueError("durations and deadline must be valid")
    spent = sum(stages_ms.values())
    return {"within_budget": spent <= deadline_ms,
            "spent_ms": spent, "remaining_ms": max(0, deadline_ms - spent)}

receipt_path = {"ingress": 18, "feature_lookup": 71, "queue": 33,
                "model": 62, "serialization": 19}
assert request_budget(receipt_path, 240) == {
    "within_budget": True, "spent_ms": 203, "remaining_ms": 37}
assert not request_budget({**receipt_path, "queue": 82}, 240)["within_budget"]
''',
        'cost': 'Combining s nonoverlapping stage durations takes O(s) time and O(1) auxiliary space. Histograms add bounded metric storage per label combination; request identifiers as labels would cause unbounded cardinality. The arithmetic example assumes sequential stages, so real traces must account for overlap and record end-to-end latency directly.',
        'mistakes': ['Reporting a success-only p95 that omits timeouts.', 'Summing overlapping spans as if they were sequential.', 'Ignoring queue time because model execution is fast.', 'Using request IDs as metric labels.'],
        'related': [M + 'queue-saturation-and-fallback-policy', M + 'receipt-serving-slo-project', M + 'shadow-canary-and-rollback', M + 'inference-logging-privacy', 'streaming-analytics/streaming-analytics-tutorial'],
    },
    {
        'path': M + 'queue-saturation-and-fallback-policy',
        'title': 'Serving overload: bound queues and choose a fallback before time runs out',
        'module': S, 'project': False,
        'summary': 'An inference service must limit work in flight and define what happens when it cannot score within the caller deadline.',
        'sections': [
            ('Budget capacity in work units', 'A queue of 470 tiny requests may be manageable, while 470 image embeddings may exhaust memory. Define a concurrency limit, queue length or weighted work budget for the deployed model and hardware. Admit only work that has a credible chance of finishing before its deadline. When capacity is exhausted, return a declared overloaded state or an approved deterministic fallback. Silently waiting past the caller deadline wastes compute and hides the cause. [[mlops/inference-latency-budget-and-tail-observation|Latency budgets]] make the decision measurable.'),
            ('Separate safe fallback from a guess', 'For a receipt-risk service, a timeout might route a transaction to manual review; it should not return a fabricated low-risk score. The fallback must have an explicit customer and operations contract, with its own volume limit and audit trail. If an old model is the fallback, check its feature contract and availability; the old model may share the failed feature store and thus fail at the same time. [[mlops/feature-schema-evolution-and-consumers|Schema compatibility]] matters during degradation as much as during promotion.'),
            ('Plan retry behavior across boundaries', 'A client retry can multiply load during an outage. Set caller and server deadlines, bounded retries with jitter where appropriate, and idempotent request identity for side-effecting workflows. Do not retry a model score blindly if it triggers a downstream action. Count initial attempts separately from retry attempts so dashboards reveal amplification. A circuit breaker can stop calls to a known-failing dependency, but it should not conceal persistent failures from incident owners.'),
            ('Exercise the failure path', 'Load test at normal and burst rates, then slow the feature store and model independently. Verify that rejected work leaves the queue promptly, admitted work respects deadlines, and fallback counts are visible. Check that a rollout does not consume all spare capacity with shadow traffic. The [[mlops/receipt-serving-slo-project|serving project]] includes overload, dependency failure and rollback drills with an explicit customer outcome for each.'),
        ],
        'code': '''def admission_decision(active_work, queued_work, deadline_ms,
                       estimated_wait_ms, model_ms):
    if min(active_work, queued_work, deadline_ms,
           estimated_wait_ms, model_ms) < 0:
        raise ValueError("capacity inputs must be nonnegative")
    if active_work >= 24 and queued_work >= 47:
        return "manual-review-overload"
    if estimated_wait_ms + model_ms > deadline_ms:
        return "manual-review-deadline"
    return "admit"

assert admission_decision(12, 8, 180, 31, 62) == "admit"
assert admission_decision(24, 47, 180, 31, 62) == "manual-review-overload"
assert admission_decision(12, 8, 80, 31, 62) == "manual-review-deadline"
''',
        'cost': 'This local admission decision is O(1) time and space. A production counter must update atomically across workers, and estimated wait time can be wrong during bursts. Model execution and fallback routing have different costs; reserve capacity for manual review rather than shifting an unbounded queue into another service.',
        'mistakes': ['Returning a low-risk score on timeout without evidence.', 'Allowing retries to multiply an already overloaded queue.', 'Using a queue limit without a request deadline.', 'Assuming a fallback model has independent dependencies.'],
        'related': [M + 'inference-latency-budget-and-tail-observation', M + 'receipt-serving-slo-project', M + 'feature-schema-evolution-and-consumers', M + 'shadow-canary-and-rollback', M + 'drift-delayed-label-monitoring'],
    },
    {
        'path': M + 'receipt-serving-slo-project',
        'title': 'Project: operate receipt scoring with a deadline and overload path',
        'module': S, 'project': True,
        'summary': 'Define a measurable receipt-scoring service objective, then test capacity, timeout and fallback behavior under failure.',
        'sections': [
            ('Write the customer-visible contract', 'The service receives a receipt and either returns a risk decision within 240 ms or routes it to a declared manual-review state. Choose an end-to-end availability definition that counts timeout and invalid responses, not just process health. Define a target window, traffic population and exclusions before looking at a favorable dashboard. The [[mlops/inference-latency-budget-and-tail-observation|latency budget]] allocates time across lookup, queue, model and response.'),
            ('Build load and fault fixtures', 'Replay a normal hour, a short 3× burst, a slow feature-store period and a cold model restart. Include large payloads and a candidate model with higher CPU demand. Record accepted, timed out, overloaded and manual-review outcomes. Use the same inputs for the current and candidate release; a result on idle hardware is not comparable to one on a saturated node. [[mlops/queue-saturation-and-fallback-policy|Overload policy]] decides when the queue must stop growing.'),
            ('Gate deployment on complete evidence', 'Require the candidate to meet quality and latency bounds while preserving enough rollback capacity. Check that the fallback path works when the feature store is unavailable, and that shadow requests are canceled when the main request ends. Emit low-cardinality duration metrics and trace identifiers; keep receipt payloads under a separate privacy policy. Canary a small traffic share and halt if customer-visible manual review exceeds its budget. [[mlops/shadow-canary-and-rollback|Rollback]] must restore both model pointer and serving capacity.'),
            ('Review the failure drill', 'Report end-to-end deadline success, tail latency, timeout rate, queue depth, fallback volume and cost per accepted score. During a simulated outage, verify that no fabricated safe score appears and that operations can distinguish capacity overload from malformed features. Store the test hardware, model digest and source revision so a later comparison is meaningful. A release is ready only when the rollback drill and the customer fallback meet their stated limits.'),
        ],
        'code': '''def serving_gate(outcomes, minimum_total=470):
    total = sum(outcomes.values())
    if total < minimum_total:
        return {"state": "hold", "reason": "insufficient-traffic"}
    timely = outcomes.get("scored-in-budget", 0)
    unsafe = outcomes.get("fabricated-safe-score", 0)
    fallback = outcomes.get("manual-review", 0)
    if unsafe or timely / total < 0.96 or fallback / total > 0.04:
        return {"state": "hold", "reason": "service-objective"}
    return {"state": "ready", "evaluated": total}

window = {"scored-in-budget": 481, "manual-review": 19}
assert serving_gate(window)["state"] == "ready"
assert serving_gate({**window, "fabricated-safe-score": 1})["state"] == "hold"
''',
        'cost': 'Aggregating k outcome counters takes O(k) time and O(1) auxiliary space. A load test costs compute and may need isolated capacity to avoid affecting customers. This gate checks one window only; production release policy should also cover traffic slices, tail latency and repeated windows so a brief good period cannot mask a persistent problem.',
        'mistakes': ['Measuring only model compute time instead of the request deadline.', 'Calling a process healthy while customers receive timeouts.', 'Sending shadow load without reserving capacity.', 'Treating manual review as free or unlimited capacity.'],
        'related': [M + 'inference-latency-budget-and-tail-observation', M + 'queue-saturation-and-fallback-policy', M + 'shadow-canary-and-rollback', M + 'receipt-triage-release-project', M + 'inference-logging-privacy'],
    },
]

crosslinks = [
    (M + 'feature-training-serving-parity', M + 'feature-contract-and-admission-gates'),
    (M + 'model-registry-promotion-gates', M + 'feature-schema-evolution-and-consumers'),
    (M + 'receipt-triage-release-project', M + 'receipt-feature-admission-project'),
    (M + 'shadow-canary-and-rollback', M + 'inference-latency-budget-and-tail-observation'),
    (M + 'inference-logging-privacy', M + 'queue-saturation-and-fallback-policy'),
    (M + 'drift-delayed-label-monitoring', M + 'receipt-serving-slo-project'),
]

if __name__ == '__main__':
    publish(lessons, (C, S), crosslinks,
            'aitrove-mlops-contracts-serving-import-20261006.json', 6100,
            subject='mlops', hub_path=M + 'mlops-tutorial')
