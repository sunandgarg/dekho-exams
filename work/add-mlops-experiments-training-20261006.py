"""Add live model experiments and training recovery lessons."""
from de_batch_publisher import publish

M = 'mlops/'
E = 'Live model experiments and exposure evidence'
T = 'Training capacity and interruption recovery'

lessons = [
    {
        'path': M + 'sticky-model-assignment-and-exposure-logging',
        'title': 'Model experiments: separate assignment from actual exposure',
        'module': E, 'project': False,
        'summary': 'A live model comparison needs stable assignment, a record of which model actually served, and a joinable outcome clock.',
        'sections': [
            ('Choose the randomization unit', 'A receipt-risk experiment may assign by merchant rather than individual receipt so repeated decisions for one merchant stay on the same model. Hash a stable pseudonymous unit ID with an experiment revision and salt, then keep the allocation fixed for that revision. Assigning by request ID can send related receipts to both arms and contaminate the comparison. Record eligibility rules before assignment. [[mlops/shadow-canary-and-rollback|Shadow traffic]] is different: its candidate output is hidden and cannot measure the customer effect of a model decision.'),
            ('Log actual exposure after routing', 'Assignment means a unit was allocated; exposure means the selected model actually served an eligible decision. A timeout, fallback, cache hit or previous model retained by a long-running worker can prevent the intended exposure. Store experiment ID, unit ID, assigned arm, served model digest, decision ID and timestamp. Avoid logging raw receipt payloads. [[mlops/inference-logging-privacy|Inference logging]] provides a restricted join key, while [[mlops/prediction-outcome-join-and-maturity|outcome joins]] later connect exposed decisions to mature labels.'),
            ('Detect crossovers and denominator drift', 'Monitor eligible units, assigned units, exposed units, crossovers and missing exposure records by arm. If one model times out more often, analyzing only successful exposures creates a selected population. Keep the intent-to-treat assignment cohort for the primary experiment estimate and report served-model diagnostics separately. Preserve a mapping from unit to arm for the experiment duration. If allocation changes midstream, use a new experiment revision instead of rewriting the old assignment history.'),
            ('Test stable behavior', 'Replay the same merchant across workers and days, change request IDs, and verify arm stability. Force a timeout to confirm assignment remains logged while actual exposure records fallback. The [[mlops/receipt-model-experiment-project|receipt experiment project]] uses those records to detect crossovers and compare operational guardrails before it considers delayed quality outcomes.'),
        ],
        'code': '''from hashlib import sha256

def assign_model(experiment_id, merchant_key, candidate_share=0.23):
    if not 0 <= candidate_share <= 1:
        raise ValueError("candidate share must be a fraction")
    identity = (experiment_id + ":" + merchant_key).encode()
    bucket = int.from_bytes(sha256(identity).digest()[:8], "big") / 2**64
    return "candidate" if bucket < candidate_share else "control"

first = assign_model("receipt-risk-r9", "merchant-47")
assert first == assign_model("receipt-risk-r9", "merchant-47")
assert assign_model("receipt-risk-r9", "merchant-47", 0) == "control"
assert assign_model("receipt-risk-r9", "merchant-47", 1) == "candidate"
''',
        'cost': 'Assignment hashes k identity bytes in O(k) time with O(1) digest space. Persisted exposure and fallback events add storage proportional to eligible decisions. Stable hashing is not itself an experiment analysis: eligibility, missing exposures and outcome delay still determine whether the comparison is interpretable.',
        'mistakes': ['Randomizing each receipt when merchant-level spillover is expected.', 'Equating assigned arm with model actually served.', 'Analyzing only successful exposures after one arm times out more often.', 'Changing allocation without a new experiment revision.'],
        'related': [M + 'experiment-guardrails-and-interference', M + 'receipt-model-experiment-project', M + 'shadow-canary-and-rollback', M + 'inference-logging-privacy', M + 'prediction-outcome-join-and-maturity'],
    },
    {
        'path': M + 'experiment-guardrails-and-interference',
        'title': 'Model experiment guardrails: stop harm without misreading the sample',
        'module': E, 'project': False,
        'summary': 'A model A/B comparison needs operational stop rules, stable populations and a plan for shared capacity or cross-arm effects.',
        'sections': [
            ('Set stop rules before traffic moves', 'Choose a maximum timeout rate, unsafe-decision count, manual-review load and urgent-case failure boundary before seeing candidate results. Separate a fast safety stop from a slower quality conclusion that needs mature outcomes. State the observation window and minimum count for each rule. [[mlops/model-alert-symptoms-ownership-and-noise|Operational alerts]] identify immediate customer symptoms; an experiment stop also records which arm, model digest and allocation revision produced the breach.'),
            ('Watch shared systems', 'Two arms may compete for the same feature store, GPU queue or manual-review team. A candidate that consumes more capacity can slow the control arm, so the control is no longer an untouched baseline. Track total service load, arm-specific load and downstream saturation. If merchants interact or share limits, assign at a cluster that contains the interference boundary where practical. A/B routing does not remove confounding from concurrent infrastructure changes; annotate releases and incidents in the experiment timeline.'),
            ('Keep quality cohorts comparable', 'A receipt outcome may mature weeks after exposure. Evaluate both arms on the same eligibility, assignment and outcome-maturity rules. Report missing-label coverage by arm and use intent-to-treat as the primary comparison when fallback or crossover occurs. An apparent candidate win from only reviewed high-risk receipts may reflect selection into review rather than improved model decisions. [[mlops/prediction-outcome-join-and-maturity|Mature outcome joins]] and [[mlops/label-corrections-and-evaluation-ledger|label revisions]] keep the evaluation reproducible.'),
            ('Define a decision that can be defended', 'Before launch, write the primary outcome, guardrails, sample-size reasoning and stopping policy. After a stop, retain the allocation and exposure logs so a reviewer can separate harmful model output from serving failure. Do not repeatedly peek at an ordinary fixed-sample significance threshold and call the first favorable result final. The [[mlops/receipt-model-experiment-project|project]] exercises a candidate that raises manual-review load despite an appealing preliminary quality score.'),
        ],
        'code': '''def arm_guardrail(control, candidate):
    for arm in (control, candidate):
        if arm["requests"] < 470:
            return {"state": "observe", "reason": "small-arm"}
    candidate_timeout = candidate["timeouts"] / candidate["requests"]
    candidate_review = candidate["manual_review"] / candidate["requests"]
    if candidate["unsafe_decisions"] > 0:
        return {"state": "stop", "reason": "unsafe-decision"}
    if candidate_timeout > 0.025 or candidate_review > 0.08:
        return {"state": "stop", "reason": "operational-guardrail"}
    return {"state": "continue"}

control = {"requests": 500, "timeouts": 4,
           "manual_review": 23, "unsafe_decisions": 0}
candidate = {"requests": 500, "timeouts": 7,
             "manual_review": 47, "unsafe_decisions": 0}
assert arm_guardrail(control, candidate)["state"] == "stop"
''',
        'cost': 'This two-arm check is O(1) time and space after aggregation. Stable experiments may need substantial traffic and long follow-up for delayed outcomes; a fast operational stop should not be confused with statistical evidence that one model is better. Shared-capacity effects require system-level metrics in addition to per-arm counters.',
        'mistakes': ['Choosing guardrails only after seeing candidate traffic.', 'Calling an immature quality estimate a final win.', 'Ignoring candidate load that degrades the control arm.', 'Dropping fallback decisions from the assigned cohort.'],
        'related': [M + 'sticky-model-assignment-and-exposure-logging', M + 'receipt-model-experiment-project', M + 'prediction-outcome-join-and-maturity', M + 'model-alert-symptoms-ownership-and-noise', M + 'receipt-serving-slo-project'],
    },
    {
        'path': M + 'receipt-model-experiment-project',
        'title': 'Project: run a receipt-model experiment with exposure evidence',
        'module': E, 'project': True,
        'summary': 'Assign merchants consistently, log the model that served each receipt and enforce operational guardrails before reading delayed outcomes.',
        'sections': [
            ('Freeze the experiment plan', 'The current receipt model and candidate r9 share one endpoint. Assign eligible merchants to arms using a stable experiment revision, record the candidate traffic share and specify timeout, unsafe-decision and manual-review stop limits. Keep shadow traffic outside the experimental outcome cohort. [[mlops/sticky-model-assignment-and-exposure-logging|Assignment and exposure]] are separate records because a routed request may use a fallback instead of its assigned model.'),
            ('Build failure cases', 'Send repeated receipts from one merchant through different workers, force a candidate timeout, simulate a model digest mismatch and add a merchant that appears in both arms due to an old assignment cache. Record every deviation. Create a shared feature-store slowdown that affects both arms, demonstrating why a per-arm metric alone cannot prove the candidate caused it. Freeze expected stop or hold states before looking at outcome labels.'),
            ('Monitor and join outcomes', 'Compare assigned and exposed counts, crossovers, fallback, timeout and manual-review rates by arm. Stop promptly on predefined harm. For the slower quality result, join only mature outcomes by prediction ID and report coverage in both arms. Use the assignment cohort as the primary denominator; inspect actually served digests as a diagnostic. [[mlops/experiment-guardrails-and-interference|Guardrails and interference]] keep operational changes from being mistaken for a clean model comparison.'),
            ('Publish a decision record', 'The review record names experiment revision, allocation rule, model digests, eligibility, exposure loss, guardrail events, mature outcome window and unresolved limitations. A stopped experiment remains useful evidence but does not establish that the control is universally better. If a candidate is approved, send it through normal promotion and rollback checks rather than directly changing the full-traffic pointer.'),
        ],
        'code': '''def exposure_audit(assignments, exposures):
    crossover = []
    missing = []
    for decision_id, assigned in assignments.items():
        served = exposures.get(decision_id)
        if served is None:
            missing.append(decision_id)
        elif served not in (assigned, "fallback"):
            crossover.append(decision_id)
    return {"state": "hold" if crossover or missing else "ready",
            "crossover": sorted(crossover), "missing": sorted(missing)}

assigned = {"decision-47": "control", "decision-82": "candidate"}
served = {"decision-47": "control", "decision-82": "fallback"}
assert exposure_audit(assigned, served)["state"] == "ready"
assert exposure_audit(assigned, {**served, "decision-82": "control"})[
    "crossover"] == ["decision-82"]
''',
        'cost': 'Auditing a assignments costs O(a) expected time and O(a) space in the worst case for flagged IDs. Exposure storage and delayed-label joins scale with traffic. A fallback recorded as an expected exposure state still belongs in the assignment cohort and must be counted in operational and outcome analysis.',
        'mistakes': ['Calling a fallback exposure a candidate model prediction.', 'Dropping timed-out assigned units from the comparison.', 'Ignoring merchants that cross arms between workers.', 'Promoting a candidate from an immature or biased outcome slice.'],
        'related': [M + 'sticky-model-assignment-and-exposure-logging', M + 'experiment-guardrails-and-interference', M + 'prediction-outcome-join-and-maturity', M + 'promotion-attestation-and-reversible-pointer', M + 'shadow-canary-and-rollback'],
    },
    {
        'path': M + 'training-checkpoints-and-preemption-recovery',
        'title': 'Training checkpoints: resume state after interruption',
        'module': T, 'project': False,
        'summary': 'A checkpoint must capture the training state required to continue, not merely a copy of the current model weights.',
        'sections': [
            ('Save the state that affects the next update', 'A receipt classifier trained for many epochs can lose hours when a worker is preempted. A resume checkpoint should identify the model weights, optimizer state, learning-rate schedule, epoch and batch position, random generator state where relevant, and data snapshot. Saving only weights may restart with a different optimizer trajectory. Record code and environment digests to reject a checkpoint created by incompatible logic. [[mlops/snapshot-split-and-environment-replay|Training replay]] supplies the stable data and split identities.'),
            ('Publish checkpoints atomically', 'Write a new checkpoint to a temporary location, validate its manifest and checksum, then make it visible. Keep at least the last known-good checkpoint while a new write is in progress. A partially uploaded file should never be selected simply because its name has the latest step number. Checkpoint formats can carry executable deserialization risk, so load only trusted packages under the training environment policy. [[mlops/model-artifact-digest-and-safe-loading|Artifact trust]] applies to training state as well as serving packages.'),
            ('Resume only compatible runs', 'On restart, compare data snapshot, code digest, feature contract, optimizer configuration and world size before accepting a checkpoint. Distributed training may need per-worker state or a coordinated save point; one worker’s step count is not proof every worker committed the same update. If compatibility fails, begin a new run with a new manifest rather than quietly splicing histories. A resumed run should record interruption count and wasted work.'),
            ('Choose frequency from failure cost', 'Checkpointing every step wastes I/O; checkpointing once a day risks losing most of a day. Estimate save time, expected interruption frequency and recovery cost, then test a forced interruption near a write. The [[mlops/receipt-training-recovery-project|recovery project]] verifies that an interrupted run resumes from a complete checkpoint and produces a defensible final artifact.'),
        ],
        'code': '''def resume_checkpoint(checkpoint, requested):
    identity = ("data_digest", "code_digest", "optimizer_revision",
                "feature_contract")
    mismatches = [field for field in identity
                  if checkpoint.get(field) != requested.get(field)]
    if mismatches:
        return {"state": "new-run", "mismatches": mismatches}
    if not checkpoint.get("complete") or checkpoint.get("step", -1) < 0:
        return {"state": "new-run", "mismatches": ["incomplete"]}
    return {"state": "resume", "next_step": checkpoint["step"] + 1}

saved = {"data_digest": "data-47", "code_digest": "code-82",
         "optimizer_revision": "adam-r3", "feature_contract": "receipt-v4",
         "complete": True, "step": 129}
assert resume_checkpoint(saved, saved) == {"state": "resume", "next_step": 130}
assert resume_checkpoint(saved, {**saved, "data_digest": "data-48"})[
    "state"] == "new-run"
''',
        'cost': 'Comparing f manifest fields costs O(f) time and O(f) space for mismatch reporting. A real save copies O(B) bytes for B checkpoint state and incurs storage and upload time. Choose the save interval by measured I/O and expected lost work; a fast manifest check cannot prove that the checkpoint bytes are intact.',
        'mistakes': ['Saving only weights and losing optimizer or scheduler state.', 'Loading a half-written latest checkpoint.', 'Resuming with a changed data snapshot under the old run ID.', 'Assuming one distributed worker’s checkpoint describes the whole job.'],
        'related': [M + 'training-budget-and-resource-admission', M + 'receipt-training-recovery-project', M + 'snapshot-split-and-environment-replay', M + 'model-artifact-digest-and-safe-loading', M + 'pipeline-stage-inputs-and-cache-identity'],
    },
    {
        'path': M + 'training-budget-and-resource-admission',
        'title': 'Training resource gates: bound cost before starting a run',
        'module': T, 'project': False,
        'summary': 'A training request should state its compute budget, stopping conditions and recovery plan before it occupies shared capacity.',
        'sections': [
            ('Estimate cost from a pilot', 'Before launching a long receipt model run, measure steps per second, accelerator memory and checkpoint time on a small representative slice. Estimate total compute hours and leave a margin for evaluation, restart and data loading. A pilot with short examples can understate cost for long-tail inputs, so include worst-case shapes. Record the estimate and observed spend against the same run ID. [[mlops/training-checkpoints-and-preemption-recovery|Checkpointing]] converts some interruption risk into storage and I/O cost.'),
            ('Admit jobs under shared limits', 'A queue can reserve accelerator count, memory and maximum runtime per team. Reject or defer a job whose request exceeds its approved budget or whose data snapshot is missing. Do not let several high-priority experiments starve scheduled retraining. Distinguish exploratory runs from production candidates: a cheap exploratory run can skip full evaluation, but it cannot be promoted without the complete release evidence. [[mlops/model-registry-promotion-gates|Promotion gates]] remain separate from compute admission.'),
            ('Stop unproductive work deliberately', 'Set a maximum wall clock, spend limit, failed-step count and early-stop rule before viewing results. Early stopping should use a development metric, not repeatedly peek at the final holdout. A run that stops for budget reasons is not a failed model evaluation; mark its artifact incomplete and unpromotable. If a preemptible machine saves money but causes repeated restarts, include lost work and delay when comparing it with stable capacity.'),
            ('Audit the estimate', 'Compare predicted and actual runtime, checkpoint overhead, retries and evaluation cost. When a job exceeds its limit, preserve the last valid checkpoint and state why it stopped. The [[mlops/receipt-training-recovery-project|training recovery project]] simulates preemption and a budget breach, then asks whether the run should resume, restart or end.'),
        ],
        'code': '''def admit_training(estimated_gpu_hours, budget_gpu_hours,
                   checkpoint_supported, expected_interruptions):
    if min(estimated_gpu_hours, budget_gpu_hours, expected_interruptions) < 0:
        raise ValueError("resource values must be nonnegative")
    if estimated_gpu_hours > budget_gpu_hours:
        return {"state": "defer", "reason": "budget"}
    if expected_interruptions > 0 and not checkpoint_supported:
        return {"state": "defer", "reason": "no-recovery"}
    return {"state": "admit", "reserved_gpu_hours": estimated_gpu_hours}

assert admit_training(18.5, 23, True, 2)["state"] == "admit"
assert admit_training(28, 23, True, 2)["reason"] == "budget"
assert admit_training(18.5, 23, False, 2)["reason"] == "no-recovery"
''',
        'cost': 'Admission is O(1) time and space; estimating runtime requires a pilot or historical run data. Reserved capacity can remain idle if jobs start late, while underestimates can block other teams. Record measured cost after every run and revise estimates rather than turning the gate into an arbitrary fixed number.',
        'mistakes': ['Launching full training without a representative throughput pilot.', 'Calling an incomplete budget-stopped checkpoint a release candidate.', 'Using the final holdout for repeated early-stop decisions.', 'Ignoring restart time when claiming preemptible capacity is cheaper.'],
        'related': [M + 'training-checkpoints-and-preemption-recovery', M + 'receipt-training-recovery-project', M + 'pipeline-stage-inputs-and-cache-identity', M + 'reproducible-training-run-project', M + 'model-registry-promotion-gates'],
    },
    {
        'path': M + 'receipt-training-recovery-project',
        'title': 'Project: resume receipt-model training under a compute budget',
        'module': T, 'project': True,
        'summary': 'Checkpoint a receipt model, inject an interruption and show whether the resumed run stays within its declared resource and evidence limits.',
        'sections': [
            ('Define the run envelope', 'The receipt model uses a frozen data snapshot, fixed split, code digest, optimizer revision and 23 GPU-hour budget. Measure pilot throughput and set a checkpoint interval from expected interruption and upload cost. Store complete training state and a manifest under a new immutable run ID. [[mlops/training-budget-and-resource-admission|Resource admission]] decides whether the request can start; [[mlops/training-checkpoints-and-preemption-recovery|checkpoint rules]] decide whether it can resume.'),
            ('Inject failure at awkward points', 'Interrupt once just before a checkpoint and once while its bytes are being written. Keep an older complete checkpoint available. Restart on a compatible environment and verify step, optimizer state and data identity. Then change the feature contract without changing the checkpoint path; the run must refuse to resume under the old ID. Include a budget breach after repeated interruptions so the job ends with an incomplete artifact rather than silently requesting unlimited capacity.'),
            ('Verify the recovered run', 'Compare the resumed run with a clean run on the same snapshot: train/evaluation cohort counts, metric tolerance, final digest and elapsed spend. Exact bytes may differ under nondeterministic kernels; report that separately from metric agreement. Do not promote a partially trained model because it happens to pass one small smoke fixture. [[mlops/reproducible-training-run-project|Replay evidence]] identifies the earliest changed stage when results diverge.'),
            ('Deliver an operator record', 'Report interruption count, last valid checkpoint, discarded partial checkpoint, recovered step, wasted GPU hours, total cost and final promotion eligibility. A successful drill demonstrates an atomic checkpoint and a bounded recovery decision, not merely that a file existed. Link the final artifact to its complete manifest before any registry promotion.'),
        ],
        'code': '''def recovery_decision(checkpoint, run, spent_gpu_hours, limit_gpu_hours):
    if spent_gpu_hours > limit_gpu_hours:
        return {"state": "stop", "reason": "budget-exhausted"}
    required = ("data_digest", "code_digest", "feature_contract")
    if not checkpoint.get("complete"):
        return {"state": "restart", "reason": "partial-checkpoint"}
    if any(checkpoint.get(field) != run.get(field) for field in required):
        return {"state": "restart", "reason": "identity-changed"}
    return {"state": "resume", "step": checkpoint["step"] + 1}

run = {"data_digest": "data-47", "code_digest": "code-82",
       "feature_contract": "receipt-v4"}
saved = {**run, "complete": True, "step": 129}
assert recovery_decision(saved, run, 18, 23)["state"] == "resume"
assert recovery_decision({**saved, "complete": False}, run, 18, 23)[
    "state"] == "restart"
''',
        'cost': 'The recovery decision is O(f) for f identity fields and O(1) extra space. The actual cost is checkpoint I/O, lost work and repeated accelerator startup. Preserving one last known-good checkpoint increases storage but prevents a partial latest write from forcing a complete restart.',
        'mistakes': ['Selecting a partial checkpoint by the largest step number.', 'Resuming after a feature-contract change under the same run ID.', 'Exceeding the declared budget because interruptions are treated as free.', 'Promoting a budget-stopped, incomplete model artifact.'],
        'related': [M + 'training-checkpoints-and-preemption-recovery', M + 'training-budget-and-resource-admission', M + 'reproducible-training-run-project', M + 'run-manifest-and-artifact-lineage', M + 'model-registry-promotion-gates'],
    },
]

crosslinks = [
    (M + 'shadow-canary-and-rollback', M + 'sticky-model-assignment-and-exposure-logging'),
    (M + 'prediction-outcome-join-and-maturity', M + 'experiment-guardrails-and-interference'),
    (M + 'receipt-triage-release-project', M + 'receipt-model-experiment-project'),
    (M + 'snapshot-split-and-environment-replay', M + 'training-checkpoints-and-preemption-recovery'),
    (M + 'pipeline-stage-inputs-and-cache-identity', M + 'training-budget-and-resource-admission'),
    (M + 'reproducible-training-run-project', M + 'receipt-training-recovery-project'),
]

if __name__ == '__main__':
    publish(lessons, (E, T), crosslinks,
            'aitrove-mlops-experiments-training-import-20261006.json', 6130,
            subject='mlops', hub_path=M + 'mlops-tutorial')
