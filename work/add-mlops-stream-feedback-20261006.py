"""Publish stream-scoring and selective-feedback MLOps modules."""
from de_batch_publisher import publish

M = 'mlops/'
S = 'Stateful stream inference and event-time recovery'
F = 'Selective feedback and evaluation coverage'

lessons = [
    {
        'path': M + 'stream-inference-event-time-and-state-contract',
        'title': 'Stream inference: event time, feature state and decision identity',
        'module': S, 'project': False,
        'summary': 'A stream-scoring service must identify the event, the state it read and the model it used before a score is defensible.',
        'sections': [
            ('Separate three clocks', 'A receipt event has an occurrence time, an arrival time and a scoring time. Those clocks can disagree after mobile disconnection, broker retry or upstream delay. A merchant-spend feature should include only events eligible at the receipt occurrence time if training used that definition. If the product intentionally scores from the latest available state instead, document that different contract and train accordingly. [[mlops/feature-training-serving-parity|Training-serving parity]] fails quietly when one side uses event time and the other uses processing time.'),
            ('Pin state with the decision', 'Record an event ID, source partition and offset, feature-state revision or window cutoff, model digest, preprocessing digest and policy revision with each output. A watermark indicates progress, not proof that no older event can arrive; late data needs an explicit policy. Do not overwrite an earlier decision merely because a later event corrected the aggregate. [[mlops/inference-chain-contracts-and-stage-identity|The inference chain]] names the runtime stages, while the state revision says which history those stages actually saw.'),
            ('Define late-event behavior', 'Choose a bounded lateness period and one of three actions for events beyond it: ignore for live scoring, emit a revision with a new identity, or send to reconciliation. Decide whether late input updates future feature state even when the old decision is immutable. That choice changes later scores. Keep a dead-letter route for malformed timestamps and impossible clock skew. [[mlops/late-feature-materialization-and-read-repair|Late feature repair]] is useful only when its effect on decisions is stated.'),
            ('Test the stream in event order and arrival order', 'Replay the same events in several arrival orders while preserving event timestamps, then compare final state and decisions under the declared lateness policy. Include duplicates, a delayed partition and a state restore. If the output differs, verify whether that difference is permitted and visible in the decision ledger. [[mlops/stream-scoring-replay-and-output-reconciliation|Replay controls]] make recovery testable; [[mlops/receipt-stream-scoring-project|the project]] applies them to a burst of offline receipt uploads.'),
        ],
        'code': '''def score_stream_event(event, state_cutoff, model_digest, allowed_lag_seconds):
    if not event.get("event_id") or not model_digest:
        raise ValueError("decision identity required")
    if allowed_lag_seconds < 0:
        raise ValueError("negative lag")
    lag = state_cutoff - event["occurred_at"]
    if lag > allowed_lag_seconds:
        return {"route": "reconcile", "event_id": event["event_id"]}
    return {"route": "score", "event_id": event["event_id"],
            "state_cutoff": state_cutoff, "model_digest": model_digest}

receipt = {"event_id": "receipt-47", "occurred_at": 1_000}
assert score_stream_event(receipt, 1_020, "risk-r8", 82)["route"] == "score"
assert score_stream_event(receipt, 1_200, "risk-r8", 82)["route"] == "reconcile"
''',
        'cost': 'The gate is O(1) time and output space per event. Maintaining keyed windows costs O(k) state for active keys and retained history; late-event tolerance enlarges that state and delays completeness. A tighter bound reduces memory but sends more valid delayed events to reconciliation. Choose it from observed delay and the cost of a late correction.',
        'mistakes': ['Using broker arrival order as if it were business event order.', 'Treating a watermark as an absolute guarantee against late data.', 'Logging a model digest without the feature-state cutoff.', 'Silently replacing a prior decision when old data arrives.'],
        'related': [M + 'stream-scoring-replay-and-output-reconciliation', M + 'receipt-stream-scoring-project', M + 'feature-training-serving-parity', M + 'inference-chain-contracts-and-stage-identity', M + 'late-feature-materialization-and-read-repair'],
    },
    {
        'path': M + 'stream-scoring-replay-and-output-reconciliation',
        'title': 'Stream scoring replay: checkpoints, duplicates and output reconciliation',
        'module': S, 'project': False,
        'summary': 'Restoring stream state is not enough; published decisions must also survive source replay without silent duplication.',
        'sections': [
            ('Name the recovery boundary', 'A stateful scorer restores feature aggregates from a checkpoint and rereads source events after that position. State may be consistent while an external decision sink already contains some outputs that the restored job emits again. End-to-end exactly-once behavior needs a replayable source and an idempotent or transactional sink. Record the source offsets, checkpoint ID, model digest and output transaction or idempotency key as one recovery packet. [[mlops/batch-inference-partition-and-idempotency|Batch idempotency]] shares the output-identity principle but uses different scheduling boundaries.'),
            ('Build a stable decision key', 'A useful key combines immutable event identity and scoring revision. A model redeployment does not automatically authorize a new customer decision for an old event; a deliberate rescore must use a new revision and link to its predecessor. Reject duplicate writes with the same key and same content. If the same key arrives with different model or route data, raise a conflict instead of last-write-wins. [[mlops/promotion-attestation-and-reversible-pointer|Promotion identity]] makes the model side of that conflict inspectable.'),
            ('Reconcile after restart', 'Compare the intended event range with emitted decision keys, sink acknowledgments and dead-letter counts. Gaps may come from a permanently late event, an expired source offset, a failed output transaction or a held schema. Replaying the source should either reproduce the same decision or create a clearly named correction, according to policy. Sampling logs alone cannot prove completeness. [[mlops/trace-sampling-and-coverage-ledger|Coverage ledgers]] distinguish sampled diagnostics from required accounting.'),
            ('Drill the failure path', 'Kill the worker after state changes but before sink acknowledgment, restore from the prior checkpoint and verify one externally visible decision per key. Repeat with a model pointer change during downtime. The restart should honor the pinned revision for replay or explicitly enter a correction workflow; it must not score old events with an unnamed new model. [[mlops/receipt-stream-scoring-project|The project]] reconciles 47 repeated uploads and a checkpoint rewind.'),
        ],
        'code': '''def reconcile_decisions(events, published):
    expected = {(event["event_id"], event["scoring_revision"])
                for event in events if event["eligible"]}
    observed = {(row["event_id"], row["scoring_revision"])
                for row in published}
    return {"missing": expected - observed, "unexpected": observed - expected,
            "duplicate_rows": len(published) - len(observed)}

events = [{"event_id": "receipt-47", "scoring_revision": "r8", "eligible": True},
          {"event_id": "receipt-82", "scoring_revision": "r8", "eligible": True}]
published = [{"event_id": "receipt-47", "scoring_revision": "r8"},
             {"event_id": "receipt-47", "scoring_revision": "r8"}]
report = reconcile_decisions(events, published)
assert report["missing"] == {("receipt-82", "r8")}
assert report["duplicate_rows"] == 1
''',
        'cost': 'The comparison is O(e + p) expected time and O(e + p) memory for e eligible events and p published rows. Run it in bounded partitions in production. Checkpoint storage and transactional sinks add latency and operational cost; idempotent keys can be simpler when exact transaction coordination is unavailable, provided conflicts and gaps remain observable.',
        'mistakes': ['Calling state checkpointing end-to-end exactly once without checking the sink.', 'Using model version alone as a decision key.', 'Letting replay overwrite a decision with a different route.', 'Measuring only duplicates while missing decisions go unnoticed.'],
        'related': [M + 'stream-inference-event-time-and-state-contract', M + 'receipt-stream-scoring-project', M + 'batch-inference-partition-and-idempotency', M + 'trace-sampling-and-coverage-ledger', M + 'promotion-attestation-and-reversible-pointer'],
    },
    {
        'path': M + 'receipt-stream-scoring-project',
        'title': 'Project: recover a receipt stream scorer after offline uploads',
        'module': S, 'project': True,
        'summary': 'Score delayed receipt events against explicit state cutoffs, restore a checkpoint and reconcile the decision sink.',
        'sections': [
            ('Freeze the business contract', 'A handheld uploads receipts after a store reconnects. The live scorer uses a seven-minute merchant window and a fixed receipt-risk model. Define whether each receipt reads merchant history up to its occurrence time or to its scoring time; this project chooses occurrence time. Pin the model, preprocessing, threshold policy and state schema. An event older than the allowed delay goes to reconciliation, not an unmarked live route. [[mlops/stream-inference-event-time-and-state-contract|The event-time contract]] is the test oracle.'),
            ('Inject disorder and repetition', 'Produce 470 receipts with known event IDs, then reorder arrival, replay 47 uploads and delay one source partition. Record the watermark and latest state cutoff for each score. Compare outputs to a reference run in occurrence order. A duplicate upload must not add twice to merchant state or emit a second customer-facing decision. The delayed partition must either remain within the declared late tolerance or generate a reconciliation record. [[mlops/feature-training-serving-parity|Feature parity]] is checked at the state cutoff, not merely on the final aggregate.'),
            ('Crash at the difficult point', 'Stop the scorer after an output reaches the sink but before its acknowledgment returns. Restore the last checkpoint and replay source events. Compare expected event-and-revision keys with published keys, detect duplicate rows and verify any conflicting content is rejected. If the model pointer moved during downtime, the replay still uses its pinned revision. [[mlops/stream-scoring-replay-and-output-reconciliation|The recovery ledger]] makes the gap and duplicate visible.'),
            ('Deliver the incident packet', 'Publish input ranges, state and model revisions, duplicate and late counts, output gaps, repaired decisions and explicit exceptions. Check that the reconciled sink has one active decision per eligible key; a deliberate correction carries a new scoring revision and a predecessor link. Test backlog recovery time and memory before declaring the system production ready. [[mlops/incident-triage-and-evidence-timeline|Incident evidence]] should show when the store disconnected, not just when uploads arrived.'),
        ],
        'code': '''def receipt_stream_release(events, output_keys, late_ids):
    eligible = {event["event_id"] for event in events
                if event["event_id"] not in late_ids}
    if len(output_keys) != len(set(output_keys)):
        return "hold:duplicate-output"
    if set(output_keys) != eligible:
        return "hold:missing-or-extra-output"
    return "accept:reconciled"

events = [{"event_id": "receipt-47"}, {"event_id": "receipt-82"},
          {"event_id": "receipt-93"}]
assert receipt_stream_release(events, ["receipt-47", "receipt-82"],
                              {"receipt-93"}) == "accept:reconciled"
assert receipt_stream_release(events, ["receipt-47", "receipt-47"],
                              {"receipt-93"}) == "hold:duplicate-output"
''',
        'cost': 'The set comparison is O(e + o) expected time and O(e + o) memory for events and outputs; bound the reconciliation window in production. Retaining a longer event-time window increases keyed state and checkpoint bytes. An offline surge raises backlog and catch-up compute even if steady traffic is small, so size recovery from the surge rather than the daily average.',
        'mistakes': ['Scoring delayed receipts against whatever state exists at upload time.', 'Counting repeated uploads as independent merchant activity.', 'Restoring state without reconciling already published decisions.', 'Allowing an old event to pick up a newly promoted model during replay.'],
        'related': [M + 'stream-inference-event-time-and-state-contract', M + 'stream-scoring-replay-and-output-reconciliation', M + 'feature-training-serving-parity', M + 'incident-triage-and-evidence-timeline', M + 'batch-inference-partition-and-idempotency'],
    },
    {
        'path': M + 'selective-label-observation-and-audit-sampling',
        'title': 'Selective labels: measure what the model never lets reviewers see',
        'module': F, 'project': False,
        'summary': 'A model changes which cases receive labels, so evaluation coverage must include decisions hidden by its own routing policy.',
        'sections': [
            ('Map the observation path', 'A receipt-risk model sends suspicious cases to human review and releases the rest. Reviewers label many routed cases, while released cases may never receive an immediate fraud outcome. A dashboard built only from reviewed labels describes the selected queue, not all scored receipts. Record each decision, review assignment, label availability and observation maturity as separate events. [[mlops/prediction-outcome-join-and-maturity|Outcome maturity]] handles delay; selective observation asks why a label exists at all.'),
            ('Reserve an independent audit lane', 'Define a permitted, small and randomized sample of cases from otherwise unreviewed routes for later adjudication. The sampling probability must be recorded at assignment time, not inferred after outcomes arrive. Keep privacy, reviewer capacity and product policy limits explicit. This lane estimates blind spots without claiming that one sample fixes every bias. Stratify only on pre-decision attributes and retain enough examples near the threshold. [[mlops/sticky-model-assignment-and-exposure-logging|Exposure logging]] keeps the scored population distinct from the audited population.'),
            ('Report denominator and uncertainty', 'Show total scored, routed, randomly audited, matured and unresolved counts by cohort. Error rates from voluntary or risk-triggered reviews cannot be generalized to all decisions without assumptions. A random audit estimate may use inverse sampling weights when probabilities vary, but extreme weights inflate variance. Publish the effective sample size and a confidence interval. [[mlops/slice-quality-gates-and-uncertainty|Slice uncertainty]] prevents a small audited subgroup from being called a clear pass.'),
            ('Protect the evaluation lane', 'Freeze audit assignment before labels are known and keep its evaluation subset separate from training and threshold tuning. A policy change alters both decision quality and which cases become visible; compare policies on a shared independent audit frame or an experiment designed for that purpose. [[mlops/feedback-policy-shift-and-offline-comparison|Policy-shift comparison]] covers this issue, while [[mlops/receipt-feedback-coverage-project|the project]] exposes a misleading reviewed-only improvement.'),
        ],
        'code': '''def audit_coverage(scored, reviewed, audited, matured):
    if scored <= 0 or min(reviewed, audited, matured) < 0:
        raise ValueError("invalid counts")
    if reviewed > scored or audited > scored or matured > reviewed + audited:
        raise ValueError("inconsistent counts")
    return {"audit_share": audited / scored,
            "observed_share": matured / scored,
            "unobserved": scored - matured}

coverage = audit_coverage(4_700, 820, 235, 914)
assert coverage["audit_share"] == 0.05
assert coverage["unobserved"] == 3_786
''',
        'cost': 'The count gate is O(1) time and space after aggregation. Random audits consume adjudication time and may carry product or privacy costs; too few audits yield wide intervals, while too many displace routine review. Preserve the assignment probability and maturity window so the measurement can be interpreted later.',
        'mistakes': ['Treating reviewed cases as a random sample of all predictions.', 'Recording audit membership only after seeing the label.', 'Reporting an error rate without the number of unobserved decisions.', 'Using the audit holdout to tune the next model and then to approve it.'],
        'related': [M + 'feedback-policy-shift-and-offline-comparison', M + 'receipt-feedback-coverage-project', M + 'prediction-outcome-join-and-maturity', M + 'sticky-model-assignment-and-exposure-logging', M + 'slice-quality-gates-and-uncertainty'],
    },
    {
        'path': M + 'feedback-policy-shift-and-offline-comparison',
        'title': 'Feedback policy shift: compare models when labels depend on routing',
        'module': F, 'project': False,
        'summary': 'A new review threshold changes the labeled population; compare candidates with an observation design that survives that change.',
        'sections': [
            ('Separate model and policy changes', 'If a new model and review threshold launch together, observed reviewer error can improve simply because different cases reached review. Pin model digest, score policy, assignment cohort and label channel for each decision. Evaluate the candidate on a shared frozen labeled frame before changing the policy, then run a staged online comparison with an independent audit lane. [[mlops/score-threshold-policy-and-change-control|Threshold control]] ensures a policy change has its own revision.'),
            ('Know what offline replay can answer', 'A frozen dataset can compare scores and routes for examples already labeled, but it cannot reveal outcomes for cases never observed under the old policy. Do not fill missing outcomes with the model prediction and call that ground truth. If logged assignment probabilities and support exist, weighted estimators can be considered; when a route had zero chance of observation, no weighting can recover its missing labels. [[mlops/selective-label-observation-and-audit-sampling|Audit sampling]] creates support where permitted.'),
            ('Gate the online comparison', 'Use sticky assignment to keep a receipt on one model-and-policy pair. Record exposure only when the decision actually served, then wait for outcome maturity. Compare quality, review load, override rate and unresolved share by cohort. A candidate that reduces review volume may make its observed label rate look better while missing hard cases; audit outcomes are the check. [[mlops/experiment-guardrails-and-interference|Experiment guardrails]] address interference and operational limits.'),
            ('Publish limits explicitly', 'Report the population covered by labels, the audit inclusion probabilities, effective sample size, uncertainty and any route with no observation support. Mark off-policy estimates as unsupported when their assumptions fail. The right disposition may be “need more audit coverage,” even if the reviewed-only metric looks favorable. [[mlops/receipt-feedback-coverage-project|The project]] tests that decision on a receipt triage rollout.'),
        ],
        'code': '''def weighted_audit_rate(audits):
    if not audits:
        raise ValueError("audit rows required")
    weighted_errors = 0.0
    total_weight = 0.0
    for audit in audits:
        probability = audit["selection_probability"]
        if not 0 < probability <= 1:
            raise ValueError("unsupported selection probability")
        weight = 1 / probability
        weighted_errors += weight * bool(audit["error"])
        total_weight += weight
    return weighted_errors / total_weight

audits = [{"selection_probability": 0.25, "error": True},
          {"selection_probability": 0.50, "error": False},
          {"selection_probability": 0.50, "error": False}]
assert weighted_audit_rate(audits) == 0.5
''',
        'cost': 'The weighted pass is O(a) time and O(1) extra space for a audited rows. It is a self-normalized descriptive estimate, not a causal proof of a policy improvement; large inverse probabilities increase variance. Independent audits cost reviewer time, and delayed outcomes extend the comparison window. Report uncertainty before using the estimate for promotion.',
        'mistakes': ['Treating missing labels as correct predictions.', 'Comparing reviewed-only error after changing the review threshold.', 'Using inverse weights when some route had zero observation probability.', 'Ignoring audit variance because the point estimate improved.'],
        'related': [M + 'selective-label-observation-and-audit-sampling', M + 'receipt-feedback-coverage-project', M + 'score-threshold-policy-and-change-control', M + 'experiment-guardrails-and-interference', M + 'prediction-outcome-join-and-maturity'],
    },
    {
        'path': M + 'receipt-feedback-coverage-project',
        'title': 'Project: audit blind spots in receipt-risk feedback',
        'module': F, 'project': True,
        'summary': 'Compare a receipt-routing change using a protected audit sample, mature outcomes and a visible unobserved population.',
        'sections': [
            ('Freeze the rollout identities', 'A candidate receipt model reduces manual review volume. Record its model digest, threshold revision, stable assignment cohort and every served decision. The existing review queue supplies labels mainly for routed receipts, so reviewed-only error is not a whole-population quality measure. Create a policy-approved audit lane from otherwise released receipts before outcomes are known; write its inclusion probability with each assignment. [[mlops/selective-label-observation-and-audit-sampling|Selective-label coverage]] defines the counts to report.'),
            ('Wait for comparable labels', 'Hold back enough time for customer corrections and independent adjudication to mature. Distinguish missing, pending and negative outcomes. Keep audit outcomes separate from labels created by routine risk review. The candidate’s reviewed-only error falls, yet the audit sample finds more missed high-value blurry receipts. Report both observations and their denominators, plus uncertainty for the small affected slice. [[mlops/prediction-outcome-join-and-maturity|Outcome joins]] prevent late corrections from being assigned to the wrong decision revision.'),
            ('Challenge the apparent win', 'Replay both models on a shared frozen evaluation set and compare scores and routes, but do not pretend that it reveals outcomes for never-reviewed live receipts. Use the audit lane to estimate released-route error under recorded selection probabilities. If one cohort had no audit support, mark that comparison unresolved and expand coverage rather than extrapolating. [[mlops/feedback-policy-shift-and-offline-comparison|The policy-shift lesson]] explains the support requirement.'),
            ('Deliver a release decision', 'Hold expansion until the missed-case signal is resolved, or restore the prior model-and-policy pair if the quality gate fails. Preserve customer exposure, reviewer workload, audit cost and the unresolved population in the packet. A later retrain may use routine labels under the normal lineage process, but the protected evaluation audit cannot quietly become both training data and final approval data. [[mlops/retraining-trigger-and-challenger|Retraining governance]] should explicitly record that boundary.'),
        ],
        'code': '''def feedback_release_gate(scored, matured, audit_supported,
                          baseline_missed, candidate_missed):
    if scored <= 0 or not 0 <= matured <= scored:
        raise ValueError("invalid population")
    if not audit_supported or matured / scored < 0.18:
        return "hold:insufficient-observation"
    if candidate_missed > baseline_missed:
        return "hold:missed-cases"
    return "review:expansion"

assert feedback_release_gate(4_700, 914, True, 7, 13) == "hold:missed-cases"
assert feedback_release_gate(4_700, 500, True, 7, 5) == \
       "hold:insufficient-observation"
assert feedback_release_gate(4_700, 914, True, 7, 5) == "review:expansion"
''',
        'cost': 'The gate is O(1) time and space after population and audit aggregation. Auditing 235 of 4,700 receipts adds reviewer work; delaying rollout until outcomes mature costs time but avoids treating absent labels as success. The count threshold is only a coverage screen, not a statistical significance test; include interval estimates and slice sample sizes in the final packet.',
        'mistakes': ['Declaring victory from a lower reviewed-only error rate.', 'Assigning audit cases after a customer correction arrives.', 'Reusing the protected audit sample to tune and approve the same candidate.', 'Treating an unsupported cohort as if its quality matched the observed cohort.'],
        'related': [M + 'selective-label-observation-and-audit-sampling', M + 'feedback-policy-shift-and-offline-comparison', M + 'prediction-outcome-join-and-maturity', M + 'retraining-trigger-and-challenger', M + 'experiment-guardrails-and-interference'],
    },
]

crosslinks = [
    (M + 'feature-training-serving-parity', M + 'stream-inference-event-time-and-state-contract'),
    (M + 'batch-inference-partition-and-idempotency', M + 'stream-scoring-replay-and-output-reconciliation'),
    (M + 'late-feature-materialization-and-read-repair', M + 'receipt-stream-scoring-project'),
    (M + 'prediction-outcome-join-and-maturity', M + 'selective-label-observation-and-audit-sampling'),
    (M + 'experiment-guardrails-and-interference', M + 'feedback-policy-shift-and-offline-comparison'),
    (M + 'retraining-trigger-and-challenger', M + 'receipt-feedback-coverage-project'),
]

if __name__ == '__main__':
    publish(lessons, (S, F), crosslinks,
            'aitrove-mlops-stream-feedback-import-20261006.json', 6184,
            subject='mlops', hub_path=M + 'mlops-tutorial')
