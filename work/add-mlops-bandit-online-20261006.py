"""Add contextual-bandit policy operations and incremental-learning releases."""
from de_batch_publisher import publish

M = 'mlops/'
BANDIT = 'Contextual-bandit policy release evidence'
ONLINE = 'Incremental model update and replay control'
lessons = [
    {
        'path': M + 'bandit-decision-propensity-and-reward-ledger',
        'title': 'Bandit decision logs: preserve action probabilities and delayed rewards',
        'module': BANDIT, 'project': False,
        'summary': 'A bandit decision log needs the chosen action, its selection probability, context revision and eventual reward to support evaluation.',
        'sections': [
            ('Log the decision before its result', 'A delivery app chooses one of three pickup-notification timings for each eligible order. The policy sees a context, chooses an action and later observes completion only for that action. Store decision ID, eligible action set, chosen action, probability assigned by the logging policy, policy revision, context feature revision and event time before sending the notification. A model score is not the probability that the logging policy chose the action. [[mlops/experiment-guardrails-and-interference|Experiment guardrails]] still protect user cohorts, but a bandit needs the extra probability trail.'),
            ('Join delayed rewards without inventing counterfactuals', 'The reward might arrive after a pickup window closes. Join by decision ID, set a maturity cutoff and retain missing or corrected outcomes as separate states. Do not treat an unobserved completion for an unchosen timing as a failure; that timing was never sent. Preserve the reward definition and revision, such as completed pickup within a fixed window, because changing it alters every policy comparison. [[mlops/prediction-outcome-join-and-maturity|Outcome maturity]] gives the same discipline to supervised decisions.'),
            ('Check support and integrity', 'For any action a candidate policy might choose in a recorded context, the logging policy needs a nonzero probability of that action if historical logs are to evaluate it with inverse-propensity weighting. A deterministic logger with no exploration leaves other actions unsupported. Validate that logged probability is finite, positive and no greater than one, that the chosen action was eligible and that a decision ID appears once. Quarantine broken records instead of silently replacing missing probability with one. [[mlops/bandit-off-policy-estimate-and-support-gates|Offline policy gates]] reject unsupported comparisons.'),
            ('Keep rollout evidence separable', 'During a policy change, log the logging policy revision on every decision rather than pooling all events as though one policy served them. Track action mix, reward maturity, cancellation outcomes and notification burden by cohort. The policy may optimize completion but annoy users with excess alerts, so the release needs service guardrails as well as reward. [[mlops/pickup-notification-policy-project|The project]] catches a candidate that shifts heavily toward an action the historical logger almost never tried.'),
        ],
        'code': '''from math import isfinite

def validate_bandit_decision(decision):
    probability = decision["logged_probability"]
    if not isfinite(probability) or not 0 < probability <= 1:
        return "reject:probability"
    if decision["chosen_action"] not in decision["eligible_actions"]:
        return "reject:ineligible-action"
    if not decision["decision_id"] or not decision["policy_revision"]:
        return "reject:identity"
    return "admit"

record = {"decision_id": "pickup-47", "policy_revision": "timing-r8",
          "eligible_actions": {"early", "middle", "late"},
          "chosen_action": "middle", "logged_probability": 0.27}
assert validate_bandit_decision(record) == "admit"
assert validate_bandit_decision({**record, "logged_probability": 0}) \
       == "reject:probability"
''',
        'cost': 'Validation is O(1) expected time and space for a small eligible-action set. Storing decision probabilities and reward joins grows linearly with decisions. Exploration can reduce short-term reward, so the policy budget and user-impact guardrails must be explicit before logs are collected.',
        'mistakes': ['Recording a model score instead of the probability of the chosen action.', 'Filling an unchosen action with an invented negative reward.', 'Mixing decisions from multiple logging policies without their revisions.', 'Assuming a deterministic policy generated support for an untried action.'],
        'related': [M + 'bandit-off-policy-estimate-and-support-gates', M + 'pickup-notification-policy-project', M + 'experiment-guardrails-and-interference', M + 'prediction-outcome-join-and-maturity', M + 'feedback-policy-shift-and-offline-comparison'],
    },
    {
        'path': M + 'bandit-off-policy-estimate-and-support-gates',
        'title': 'Bandit offline evaluation: support, variance and release limits',
        'module': BANDIT, 'project': False,
        'summary': 'An offline policy estimate needs known logging probabilities, action support and enough effective observations to be useful.',
        'sections': [
            ('State the estimand', 'Historical pickup decisions reveal reward only for the notification timing actually sent. To estimate a candidate policy from those logs, weight each observed reward by candidate probability for the logged action divided by the logging probability for that action. Average across eligible mature decisions. This inverse-propensity estimate targets the candidate policy under the logged context distribution when probabilities are correct and support exists; it is not a controlled live experiment. [[mlops/bandit-decision-propensity-and-reward-ledger|The decision ledger]] supplies the denominator.'),
            ('Reject absent support', 'If the candidate places weight on late notifications in a context where the logger always chose early, there is no observed late reward for that context. The estimate cannot rescue it by dividing by zero, dropping those contexts or guessing their reward. Mark the candidate unsupported and gather controlled exploration or narrow the candidate to supported actions. Even a tiny nonzero logging probability creates very large weights and a noisy estimate. Report the weight distribution and effective sample size, not just the estimated reward.'),
            ('Keep reward and cohort definitions fixed', 'Use mature rewards, identical eligibility filters and a pinned reward revision for incumbent and candidate. A delivery change that speeds pickups but raises cancellations may score well on the wrong reward. Evaluate safety cohorts and notification burden separately. The result can be distorted if logged action probabilities were wrong, if users interfere with one another or if new production contexts differ from the logged frame. [[mlops/experiment-guardrails-and-interference|Interference controls]] and [[mlops/selective-label-observation-and-audit-sampling|observation coverage]] show why an offline score has limits.'),
            ('Promote through a bounded experiment', 'Require valid logs, target support, a minimum effective sample size, acceptable cohort bounds and a fixed rollback rule before a canary. The offline estimate is a filter for weak candidates, not a promise of live lift. A small online randomized allocation can then measure actual outcomes under the new policy, with mature rewards and guardrails. [[mlops/pickup-notification-policy-project|The project]] rejects a high estimated reward driven by one rare, heavily weighted action.'),
        ],
        'code': '''def ips_estimate(decisions):
    if not decisions:
        return {"state": "hold:no-decisions"}
    weights = []
    weighted_rewards = []
    for decision in decisions:
        for action, target_probability in decision["target_probs"].items():
            if target_probability > 0 and decision["behavior_probs"].get(action, 0) <= 0:
                return {"state": "hold:unsupported-action"}
        chosen = decision["chosen_action"]
        weight = decision["target_probs"].get(chosen, 0) / \
                 decision["behavior_probs"][chosen]
        weights.append(weight)
        weighted_rewards.append(weight * decision["reward"])
    weight_square_sum = sum(weight * weight for weight in weights)
    effective_n = sum(weights) ** 2 / weight_square_sum if weight_square_sum else 0
    return {"state": "measured", "value": sum(weighted_rewards) / len(decisions),
            "effective_n": effective_n}

logs = [{"chosen_action": "early", "behavior_probs": {"early": 0.5,
         "late": 0.5}, "target_probs": {"early": 0.5, "late": 0.5},
         "reward": 1},
        {"chosen_action": "late", "behavior_probs": {"early": 0.5,
         "late": 0.5}, "target_probs": {"early": 0.5, "late": 0.5},
         "reward": 0}]
assert ips_estimate(logs)["value"] == 0.5
assert ips_estimate(logs)["effective_n"] == 2
''',
        'cost': 'The estimate is O(n × a) time for n decisions and a candidate actions per context, with O(n) temporary weight storage. Heavy weights reduce effective sample size even when raw n is large. A stricter support gate may delay rollout, but replacing missing evidence with a guessed reward would make the estimate look precise without data.',
        'mistakes': ['Using a chosen-action probability of zero or an invented default.', 'Reporting raw sample count without weight concentration.', 'Treating an offline estimate as evidence of live causal lift.', 'Discarding unsupported contexts until the remaining estimate looks favorable.'],
        'related': [M + 'bandit-decision-propensity-and-reward-ledger', M + 'pickup-notification-policy-project', M + 'experiment-guardrails-and-interference', M + 'selective-label-observation-and-audit-sampling', M + 'feedback-policy-shift-and-offline-comparison'],
    },
    {
        'path': M + 'pickup-notification-policy-project',
        'title': 'Project: evaluate a pickup-notification bandit before rollout',
        'module': BANDIT, 'project': True,
        'summary': 'Audit action logs and mature rewards, reject unsupported policy actions and run a bounded canary.',
        'sections': [
            ('Freeze the decision frame', 'A delivery app sends one of three pickup reminders. Each decision captures eligible timings, chosen timing, logging probability, policy revision, order cohort and a decision ID. Join a pickup-completion reward only after its observation window closes. A duplicate client retry keeps its original decision rather than drawing another action. [[mlops/bandit-decision-propensity-and-reward-ledger|The decision ledger]] prevents accidental duplication and missing probabilities.'),
            ('Find the unsupported candidate', 'The candidate heavily favors late reminders for remote districts. Historic policy logs show zero late allocations there. Do not compute an offline reward for that candidate by pretending early rewards apply to late timing. Restrict the candidate to supported actions for the first comparison or allocate a small, separately approved exploration cohort. Another candidate has nonzero support but effective sample size of only 47 despite 820 recorded decisions; hold it while rare high weights are investigated. [[mlops/bandit-off-policy-estimate-and-support-gates|The estimate gate]] exposes both problems.'),
            ('Protect the live experiment', 'For a supported candidate with adequate effective sample size, reserve a limited user cohort and a fixed maximum notification rate. Measure completion, cancellations, opt-outs and messages sent, with no overlapping notification experiments in the same orders. Keep the incumbent and a reversible allocation switch. Do not declare a win before the completion window matures. [[mlops/experiment-guardrails-and-interference|Experiment guardrails]] keep interactions and exposure accounting honest.'),
            ('Publish the decision record', 'Deliver action-support tables, logged probability checks, reward maturity, weight distribution, effective sample size, cohort outcomes and the canary stop rule. Record whether an offline gain survived live measurement. The project is complete only when a poor or unsupported policy has an explicit hold decision, and a safe candidate has an owner for rollback. Link the case to [[mlops/prediction-outcome-join-and-maturity|mature rewards]] and [[mlops/promotion-attestation-and-reversible-pointer|promotion evidence]].'),
        ],
        'code': '''def pickup_policy_gate(report, limits):
    if report["unsupported_contexts"]:
        return "hold:unsupported"
    if report["effective_n"] < limits["minimum_effective_n"]:
        return "hold:low-effective-sample"
    if report["notification_rate"] > limits["maximum_rate"]:
        return "hold:burden"
    if not report["rewards_mature"]:
        return "hold:immature-reward"
    return "canary:bounded-cohort"

limits = {"minimum_effective_n": 82, "maximum_rate": 0.47}
report = {"unsupported_contexts": 0, "effective_n": 47,
          "notification_rate": 0.39, "rewards_mature": True}
assert pickup_policy_gate(report, limits) == "hold:low-effective-sample"
assert pickup_policy_gate({**report, "effective_n": 120}, limits) \
       == "canary:bounded-cohort"
''',
        'cost': 'The aggregate gate is O(1) time and space; collecting valid exploration data and mature outcomes is the real cost. Extra notifications can disturb users, so the experiment has a burden cap. A more conservative policy may need longer to gather enough supported examples for a reliable comparison.',
        'mistakes': ['Assigning a counterfactual reward to an unchosen reminder.', 'Reusing the same order twice because a client retried.', 'Ignoring effective sample size when a few decisions dominate the estimate.', 'Calling an experiment complete before pickup outcomes mature.'],
        'related': [M + 'bandit-decision-propensity-and-reward-ledger', M + 'bandit-off-policy-estimate-and-support-gates', M + 'experiment-guardrails-and-interference', M + 'prediction-outcome-join-and-maturity', M + 'promotion-attestation-and-reversible-pointer'],
    },
    {
        'path': M + 'incremental-update-ledger-and-feedback-admission',
        'title': 'Incremental model updates: admit feedback once and preserve lineage',
        'module': ONLINE, 'project': False,
        'summary': 'An incremental learner consumes a sequence of labeled updates; replay, corrections and ordering must be governed like a release.',
        'sections': [
            ('Define the update unit', 'A warehouse staffing forecast is adjusted as shift outcomes arrive. Every update needs a source event ID, label revision, feature snapshot, event time, observation window and parent model checkpoint. The update stream is not automatically trustworthy because it is recent. Reject labels that have not matured, features collected after the forecast decision and records from excluded facilities. [[mlops/prediction-outcome-join-and-maturity|Outcome maturity]] and [[mlops/feature-training-serving-parity|feature parity]] set the admission boundary.'),
            ('Make ingestion idempotent', 'Delivery systems retry. Applying the same gradient update twice gives a different model even if the input data is unchanged. Keep a durable ledger of applied event ID and label revision alongside the checkpoint. If a corrected label arrives after the old version was used, do not blindly train again on both versions; either use a learner with a defined reversal method or rebuild from a clean checkpoint and replay a corrected event stream. [[mlops/label-corrections-and-evaluation-ledger|Label correction records]] preserve the superseded judgment.'),
            ('Bound ordering and staleness', 'Online arrivals may be out of event-time order. Decide whether the learner requires event-time ordering or accepts arrival order, and record the policy. Hold an update whose feature snapshot is older than the allowed lag. When a shift is temporarily missing labels, do not interpret the gap as a zero outcome. Use a watermark for closed windows and keep late records in an explicit correction queue. [[mlops/stream-inference-event-time-and-state-contract|Event-time contracts]] apply to scoring; updates need an equally clear clock.'),
            ('Version every published state', 'A mutable weight file makes incident recovery impossible. Save checkpoints with parent digest, applied-event watermark, feature code revision, update code digest and evaluation report ID. A new state is a candidate until it passes fresh quality and capacity gates; the serving pointer moves separately. [[mlops/incremental-checkpoint-replay-and-rollback|Checkpoint replay]] makes recovery deterministic, and [[mlops/warehouse-online-update-project|the project]] tests a late correction after a duplicate retry.'),
        ],
        'code': '''def admit_incremental_feedback(ledger, event):
    if not event["mature"] or event["feature_after_decision"]:
        return "hold:invalid-observation"
    applied_revision = ledger.get(event["event_id"])
    if applied_revision == event["label_revision"]:
        return "skip:duplicate"
    if applied_revision is not None:
        return "replay:corrected-label"
    ledger[event["event_id"]] = event["label_revision"]
    return "apply"

ledger = {}
shift = {"event_id": "shift-82", "label_revision": "r1",
         "mature": True, "feature_after_decision": False}
assert admit_incremental_feedback(ledger, shift) == "apply"
assert admit_incremental_feedback(ledger, shift) == "skip:duplicate"
assert admit_incremental_feedback(ledger, {**shift, "label_revision": "r2"}) \
       == "replay:corrected-label"
''',
        'cost': 'A hash-ledger lookup is O(1) expected time and O(n) stored IDs over n applied events. Rebuilding after a correction can cost O(n) update work from the chosen clean checkpoint. Compacting ledger state without a durable event archive makes replay cheaper today but leaves recovery unverifiable later.',
        'mistakes': ['Applying duplicate feedback as a second gradient step.', 'Training on immature outcomes or post-decision features.', 'Applying both old and corrected labels without a defined reversal.', 'Serving weights from a mutable file with no parent checkpoint.'],
        'related': [M + 'incremental-checkpoint-replay-and-rollback', M + 'warehouse-online-update-project', M + 'prediction-outcome-join-and-maturity', M + 'label-corrections-and-evaluation-ledger', M + 'stream-inference-event-time-and-state-contract'],
    },
    {
        'path': M + 'incremental-checkpoint-replay-and-rollback',
        'title': 'Incremental learning releases: checkpoint replay and forgetting gates',
        'module': ONLINE, 'project': False,
        'summary': 'An updated model state must be reproducible from its parent checkpoint and admitted events before promotion.',
        'sections': [
            ('Checkpoint a closed update window', 'At the end of an approved warehouse shift window, freeze the parent model digest, ordered event IDs, label revisions, feature transform and update code. Write a candidate checkpoint to a new immutable path, never over the current serving artifact. Record the applied-event watermark and an integrity digest for the event list. If a worker dies halfway through, restart from the last committed checkpoint and replay the window. [[mlops/training-checkpoints-and-preemption-recovery|Checkpoint recovery]] covers training interruptions; incremental updates add duplicate and correction semantics.'),
            ('Test retained and new behavior', 'A learner that adapts to a new warehouse can forget older facilities. Evaluate the candidate on a recent mature window and a pinned retention suite covering established sites, holidays and rare staff shortages. Compare against the current serving model on the same frames. Monitor underforecast cost and overstaffing, not only average error. [[mlops/slice-quality-gates-and-uncertainty|Slice gates]] protect an older facility whose performance regresses while the global metric improves.'),
            ('Publish through a separate pointer', 'The candidate state remains offline until evaluation, artifact integrity and serving-compatibility checks pass. Promote by changing a versioned pointer, then canary by facility. If quality or capacity falls, restore the prior pointer; keep the candidate and event ledger for diagnosis. Do not attempt to reverse individual gradient updates in a generic learner when its update operation has no valid inverse. [[mlops/promotion-attestation-and-reversible-pointer|A reversible pointer]] is simpler and testable.'),
            ('Handle corrected labels honestly', 'If a label revision changes inside a committed window, create a new candidate from the last clean parent and replay corrected events in the defined order. Preserve both checkpoint lineages and note which served decisions used the old state. A replay may produce different bytes if update order, seeds or runtime change, so pin them and allow only a documented numeric tolerance. [[mlops/warehouse-online-update-project|The project]] catches a correction that a naive second update would double count.'),
        ],
        'code': '''def incremental_promotion(candidate, incumbent, limits):
    if candidate["parent_digest"] != incumbent["artifact_digest"]:
        return "hold:wrong-parent"
    if not candidate["replay_complete"] or candidate["duplicate_events"]:
        return "hold:replay-integrity"
    if candidate["old_site_error"] > limits["old_site_error"]:
        return "hold:forgetting"
    if candidate["new_site_error"] > limits["new_site_error"]:
        return "hold:new-site-quality"
    return "canary:versioned-pointer"

incumbent = {"artifact_digest": "staff-r47"}
limits = {"old_site_error": 0.18, "new_site_error": 0.22}
candidate = {"parent_digest": "staff-r47", "replay_complete": True,
             "duplicate_events": 0, "old_site_error": 0.24,
             "new_site_error": 0.16}
assert incremental_promotion(candidate, incumbent, limits) == "hold:forgetting"
assert incremental_promotion({**candidate, "old_site_error": 0.15},
                             incumbent, limits) == "canary:versioned-pointer"
''',
        'cost': 'The aggregate gate is O(1) time and space; a replay from a clean checkpoint costs O(u) update work for u admitted events. Keeping an older-facility retention suite and immutable checkpoints uses storage and evaluation compute, but it makes catastrophic forgetting and rollback visible before every warehouse is exposed.',
        'mistakes': ['Overwriting the serving checkpoint in place.', 'Testing only the newest warehouse and missing older-site regression.', 'Applying a corrected label as an extra update to a nonreversible learner.', 'Claiming deterministic replay without pinning event order and runtime.'],
        'related': [M + 'incremental-update-ledger-and-feedback-admission', M + 'warehouse-online-update-project', M + 'training-checkpoints-and-preemption-recovery', M + 'slice-quality-gates-and-uncertainty', M + 'promotion-attestation-and-reversible-pointer'],
    },
    {
        'path': M + 'warehouse-online-update-project',
        'title': 'Project: release a warehouse staffing model after incremental updates',
        'module': ONLINE, 'project': True,
        'summary': 'Admit mature shift feedback, replay a corrected event and reject an update that forgets an older facility.',
        'sections': [
            ('Freeze the parent and event window', 'The staffing forecast receives mature shift outcomes each evening. Start from one approved parent checkpoint and an immutable list of shift IDs with label revisions, feature snapshots and event times. Exclude a forecast-time feature that was actually recorded after the shift. Collapse duplicate delivery of shift 82. [[mlops/incremental-update-ledger-and-feedback-admission|The admission ledger]] records exactly one applied revision per event.'),
            ('Correct a label through replay', 'After the first candidate checkpoint is saved, shift 82 receives a corrected staffing outcome. Do not feed revision two as an extra gradient step on top of revision one. Return to the last clean parent, replace the event in the ordered window and replay the window into a new candidate artifact. Keep both manifests for audit. A skipped late event remains in the correction queue with an owner rather than disappearing.'),
            ('Run a retention gate', 'The new candidate improves forecast error at a recently opened site but increases understaffing errors at a longstanding facility. Evaluate both on a pinned older-site suite and the recent mature window. Hold promotion until the older-site regression is addressed. A mean across all warehouses would conceal the harm. [[mlops/incremental-checkpoint-replay-and-rollback|The release gate]] requires parent identity, replay integrity and quality on both frames.'),
            ('Canary and hand off', 'For a candidate that passes, move a versioned serving pointer for one facility, record the checkpoint digest in every forecast and watch staffing overrides. Revert the pointer if the underforecast guardrail trips. Deliver applied-event watermark, excluded records, correction history, replay digest, recent and retained errors, and rollback owner. [[mlops/promotion-attestation-and-reversible-pointer|Promotion evidence]] closes the trace from feedback to the deployed forecast.'),
        ],
        'code': '''def warehouse_update_window(events):
    seen = {}
    for event in events:
        if not event["mature"] or event["feature_after_forecast"]:
            return "hold:invalid-event"
        previous = seen.get(event["shift_id"])
        if previous is not None and previous != event["label_revision"]:
            return "replay:corrected-label"
        seen[event["shift_id"]] = event["label_revision"]
    return "admit:" + str(len(seen))

window = [{"shift_id": "shift-47", "label_revision": "r1",
           "mature": True, "feature_after_forecast": False},
          {"shift_id": "shift-47", "label_revision": "r1",
           "mature": True, "feature_after_forecast": False}]
assert warehouse_update_window(window) == "admit:1"
assert warehouse_update_window(window + [{**window[0],
       "label_revision": "r2"}]) == "replay:corrected-label"
''',
        'cost': 'The window pass is O(n) expected time and O(n) space for n events. Replaying a corrected window adds another O(u) training update pass. Retention evaluation and a canary cost extra compute, but prevent a new-site improvement from shipping with an older-site understaffing regression.',
        'mistakes': ['Applying an event twice after a delivery retry.', 'Training on a feature recorded after the forecast time.', 'Adding a corrected label as if it were a second independent shift.', 'Promoting on new-site error while an older facility gets worse.'],
        'related': [M + 'incremental-update-ledger-and-feedback-admission', M + 'incremental-checkpoint-replay-and-rollback', M + 'promotion-attestation-and-reversible-pointer', M + 'slice-quality-gates-and-uncertainty', M + 'training-checkpoints-and-preemption-recovery'],
    },
]

crosslinks = [
    (M + 'experiment-guardrails-and-interference', M + 'bandit-decision-propensity-and-reward-ledger'),
    (M + 'feedback-policy-shift-and-offline-comparison', M + 'bandit-off-policy-estimate-and-support-gates'),
    (M + 'prediction-outcome-join-and-maturity', M + 'pickup-notification-policy-project'),
    (M + 'label-corrections-and-evaluation-ledger', M + 'incremental-update-ledger-and-feedback-admission'),
    (M + 'training-checkpoints-and-preemption-recovery', M + 'incremental-checkpoint-replay-and-rollback'),
    (M + 'promotion-attestation-and-reversible-pointer', M + 'warehouse-online-update-project'),
]

if __name__ == '__main__':
    publish(lessons, [BANDIT, ONLINE], crosslinks,
            'aitrove-mlops-bandit-online-import-20261006.json', 6232,
            subject='mlops', hub_path=M + 'mlops-tutorial')
