"""Add original multi-task learning and release-review lessons."""
from ml_fixture_writer_20261005 import publish_batch

lessons = []


def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='machine-learning/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))


add('multitask-targets-and-label-availability',
    'Multi-task targets and per-head label availability',
    'A multi-task model shares some representation across distinct prediction targets, but every head needs its own label definition, maturity clock and missing-label mask.', [
    ('Define each decision separately', 'A pump-inspection model may predict whether a seal needs replacement and estimate repair minutes. The first target is a binary decision; the second is a duration observed only after a completed job. They differ from a multi-label classifier that emits several tags under one label scheme. A replacement label can be known while duration is missing, and a missing duration is not zero minutes. [[machine-learning/multilabel-schema-and-unknown-targets|Unknown targets]] require an explicit state.'),
    ('Name the serving moment', 'Both heads should use the same inspection-time inputs if they share an encoder. Repair minutes recorded after dispatch cannot enter either head’s input. If the duration prediction is requested only after replacement approval, that later decision may justify a different feature clock and perhaps a separate model. [[machine-learning/prediction-time-feature-availability|Prediction-time availability]] decides whether sharing is legitimate.'),
    ('Keep masks with labels', 'Store a boolean observed flag per task and per record. A mask of false means no training loss for that head on that record; it does not say the outcome was negative. The code builds a small status packet and rejects a duration observed without a positive, completed repair under this local data contract. Real systems may define different duration populations, so validate that rule first.'),
    ('Split by physical pump and time', 'Multiple photographs of one pump and its later work order belong to one split. For a future release, hold out later inspections and wait until target windows mature. Do not put an early photo in training and a later view in test. [[machine-learning/group-and-time-validation|Identity and time splits]] protect both heads.'),
    ('Report support per task', 'A model may have 8,000 replacement labels but only 470 repair durations. State each denominator by depot, camera and pump family, along with the intersection having both labels. The intersection may be a selective subset of difficult jobs, creating bias in the shared representation. [[machine-learning/multitask-head-loss-and-masking|Masked loss]] uses those counts.')],
    '''inspection_cases = [
    {"pump": "station-47", "replace": 1, "replace_observed": True,
     "repair_minutes": 74, "duration_observed": True},
    {"pump": "station-62", "replace": 0, "replace_observed": True,
     "repair_minutes": None, "duration_observed": False},
    {"pump": "station-83", "replace": None, "replace_observed": False,
     "repair_minutes": None, "duration_observed": False},
]

def task_support(cases):
    for case in cases:
        if case["duration_observed"] and (case["replace"] != 1 or case["repair_minutes"] is None):
            raise ValueError("duration outside completed replacement contract")
    return {"replacement": sum(case["replace_observed"] for case in cases),
            "duration": sum(case["duration_observed"] for case in cases)}

assert task_support(inspection_cases) == {"replacement": 2, "duration": 1}''',
    'Checking N records costs O(N) time and O(1) auxiliary memory. Storing separate masks and label provenance increases data work but prevents silent zero-imputation. Shared inference may save encoder compute, yet label maturity and outcome adjudication remain per-head costs.',
    ['Do not convert missing duration to zero.', 'Do not assume both tasks share a prediction clock just because they share an image.', 'Do not report one training-row count for heads with different label coverage.'],
    ['machine-learning/multitask-head-loss-and-masking','machine-learning/multitask-loss-balance-and-gradient-conflict','machine-learning/multitask-negative-transfer-review','machine-learning/multitask-release-review-project'])


add('multitask-head-loss-and-masking',
    'Multi-task head losses with observed-label masks',
    'A shared encoder can feed separate heads while each head computes loss only on records with an observed target under its own denominator.', [
    ('Choose a compatible shared input', 'For inspection photos, an image encoder can serve a replacement classifier and a repair-duration regressor. The heads need different output units and losses; a binary log loss and an absolute-duration loss cannot be added meaningfully until their scales and priorities are defined. The code illustrates the masked per-head arithmetic, not a full neural training loop. [[machine-learning/multitask-targets-and-label-availability|Target contracts]] come first.'),
    ('Normalize within each head', 'Divide each head’s observed loss sum by its own number of observed labels, not the total batch size. Otherwise a rare duration label becomes weaker merely because many classification-only cases were batched with it. A head with no observed labels in the batch contributes no loss and should not produce an invalid divide-by-zero. The batch sampler still needs enough duration cases over time.'),
    ('Do not leak task identity', 'If duration is observed only after a replacement, its missingness tells the model something about the replacement outcome. Masks may guide training, but must not be supplied as a serving-time feature if unknown at inspection. Nor should a duration head be evaluated on nonreplacement pumps unless the target has been defined for them.'),
    ('Keep standalone baselines', 'Train the replacement and duration tasks separately with the same eligible examples, encoders and splits. A shared model is justified only if it improves a declared goal—quality, latency, storage or upkeep—without breaching either task’s minimum. [[machine-learning/multitask-negative-transfer-review|Negative-transfer review]] compares the results.'),
    ('Track training and serving costs separately', 'A shared encoder may save inference when both outputs are requested in one call, but two heads and their losses can complicate training. If duration is rarely requested, always computing it may waste serving resources. Measure the actual request path and report head-specific output validity. [[machine-learning/model-inference-budget-and-device-profile|Device profiling]] defines the measurement boundary.')],
    '''from math import log

batch = [
    {"replace_y": 1, "replace_p": 0.82, "replace_known": True,
     "minutes_y": 74, "minutes_pred": 69, "minutes_known": True},
    {"replace_y": 0, "replace_p": 0.18, "replace_known": True,
     "minutes_y": None, "minutes_pred": 52, "minutes_known": False},
    {"replace_y": None, "replace_p": 0.55, "replace_known": False,
     "minutes_y": None, "minutes_pred": 61, "minutes_known": False},
]

def observed_head_losses(records):
    classification = [-row["replace_y"] * log(row["replace_p"])
                      - (1 - row["replace_y"]) * log(1 - row["replace_p"])
                      for row in records if row["replace_known"]]
    duration = [abs(row["minutes_y"] - row["minutes_pred"])
                for row in records if row["minutes_known"]]
    return {"replacement": sum(classification) / len(classification) if classification else None,
            "duration_minutes": sum(duration) / len(duration) if duration else None}

head_losses = observed_head_losses(batch)
assert round(head_losses["replacement"], 3) == 0.198
assert head_losses["duration_minutes"] == 5''',
    'Loss aggregation costs O(B) time and O(B) storage as written for batch size B; streaming sums reduce auxiliary memory to O(1). Full training adds encoder and head forward/backward passes. Inference savings depend on whether both heads run for the same request and whether feature preparation dominates latency.',
    ['Do not average a sparse head over records with no label for that head.', 'Do not add losses with different units without a documented weighting rule.', 'Do not expose a training-only observed-label mask as an inspection-time feature.'],
    ['machine-learning/multitask-targets-and-label-availability','machine-learning/multitask-loss-balance-and-gradient-conflict','machine-learning/multitask-negative-transfer-review','machine-learning/multitask-release-review-project'])


add('multitask-loss-balance-and-gradient-conflict',
    'Multi-task loss balance and shared-gradient conflict',
    'Loss weights set the training tradeoff between tasks; opposing gradients in shared parameters can reveal an optimization conflict but do not alone prove worse generalization.', [
    ('State which task may yield', 'A replacement false negative may trigger a missed repair, while a duration error affects scheduling. Those costs are not expressed by raw log loss and minutes error. Choose weights on development data against explicit task guardrails. A scalar total loss can fall while the high-cost task gets worse. [[machine-learning/decision-threshold-and-cost|Decision costs]] must be evaluated after training.'),
    ('Compare gradient direction carefully', 'For shared encoder parameters, compute each head’s gradient before combining them. A negative dot product means the two local updates point in partly opposing directions on that batch. It may be temporary noise or a systematic conflict. The code computes cosine for small illustrative vectors; it does not implement a gradient-surgery optimizer. Repeat across batches, sites and training stages.'),
    ('Control scale before interpreting conflict', 'A duration loss measured in minutes may have a far larger numeric magnitude than a binary log loss. Normalize targets and inspect gradient norms, not just loss numbers. Altering weights changes the optimization objective and can move one task below its accepted quality. [[machine-learning/multitask-head-loss-and-masking|Per-head loss]] establishes the denominator first.'),
    ('Separate conflict from negative transfer', 'Even aligned training gradients can produce a joint model that generalizes worse than separate models because of limited shared capacity or label selection. Conversely, occasional negative cosine need not harm held-out quality. The decisive evidence is each task’s untouched-test result with the same target cohort and serving contract. [[machine-learning/multitask-negative-transfer-review|The comparison]] defines that evidence.'),
    ('Keep the intervention small', 'If one task harms the other, try a measured change: fewer shared layers, a different sampling ratio, or separate models. Recheck latency and maintainability. Do not add elaborate optimization machinery because one batch showed disagreement; diagnose labels and task compatibility first.')],
    '''from math import sqrt

replacement_gradient = (0.8, -0.2, 0.4)
duration_gradient = (-0.5, 0.1, -0.2)

def gradient_cosine(first, second):
    if len(first) != len(second):
        raise ValueError("shared-parameter gradients must align by shape")
    dot = sum(left * right for left, right in zip(first, second))
    first_norm = sqrt(sum(value * value for value in first))
    second_norm = sqrt(sum(value * value for value in second))
    if first_norm == 0 or second_norm == 0:
        return None
    return dot / (first_norm * second_norm)

agreement = gradient_cosine(replacement_gradient, duration_gradient)
assert agreement is not None and agreement < -0.98
assert gradient_cosine(replacement_gradient, replacement_gradient) == 1.0''',
    'A cosine over D shared parameters costs O(D) time and O(1) scalar storage. Obtaining separate per-task gradients can require extra backward passes or retained computation graphs. More sophisticated balancing adds training cost; justify it with held-out task gains, not the diagnostic alone.',
    ['Do not infer negative transfer solely from one opposing-gradient batch.', 'Do not compare loss magnitudes expressed in different units as if they were priorities.', 'Do not choose weights from the final untouched test.'],
    ['machine-learning/multitask-targets-and-label-availability','machine-learning/multitask-head-loss-and-masking','machine-learning/multitask-negative-transfer-review','machine-learning/multitask-release-review-project'])


add('multitask-negative-transfer-review',
    'Multi-task negative transfer and per-task baselines',
    'Negative transfer occurs when shared training harms a target relative to a credible single-task baseline under the same evaluation contract.', [
    ('Make the comparison paired', 'For each later-period pump, compare the shared model and replacement-only baseline on the same replacement label. For completed repairs, compare the shared duration head and duration-only baseline on the same duration records. A different test population can manufacture an apparent gain or loss. [[machine-learning/group-and-time-validation|Split design]] must stay fixed.'),
    ('Name the noninferiority margins', 'A joint model may save serving time while losing a small amount of accuracy. Decide beforehand whether any loss is acceptable for each head and slice. Replacement recall on rare severe faults may have a zero-regression rule, while duration mean absolute error may allow a one-minute change. The example gate uses local margins; these are not universal values.'),
    ('Inspect where sharing helps', 'A shared visual encoder could help duration prediction on rare pump families if damage appearance is informative. It could also make the replacement head rely on post-repair documentation patterns if target clocks were mixed. Break results down by camera, depot, pump family and label support. [[machine-learning/multitask-targets-and-label-availability|Task contracts]] explain the clock risk.'),
    ('Measure the resource gain', 'Compute full-path latency and peak memory for joint and separate serving, with both heads requested and with replacement-only requests. A shared model is not automatically cheaper if it activates an expensive duration head on every request. [[machine-learning/model-inference-budget-and-device-profile|Serving budgets]] use measured costs.'),
    ('Retain a split option', 'If the duration head improves but replacement recall regresses, keep separate models or share fewer layers. Release decisions are not a vote on architectural elegance. [[machine-learning/multitask-release-review-project|The project]] holds the joint model unless all required task and operating gates pass.')],
    '''paired_results = {
    "replacement_recall_single": 0.88,
    "replacement_recall_joint": 0.84,
    "duration_mae_single": 13.4,
    "duration_mae_joint": 12.7,
    "joint_p95_ms": 63,
    "separate_p95_ms": 89,
}

def compare_joint_model(results, minimum_recall, max_duration_mae):
    return {
        "replacement_ok": results["replacement_recall_joint"] >= minimum_recall,
        "duration_ok": results["duration_mae_joint"] <= max_duration_mae,
        "serving_gain_ms": results["separate_p95_ms"] - results["joint_p95_ms"],
        "recall_change": results["replacement_recall_joint"] - results["replacement_recall_single"],
    }

review = compare_joint_model(paired_results, minimum_recall=0.87, max_duration_mae=14)
assert review["replacement_ok"] is False
assert review["duration_ok"] is True
assert review["serving_gain_ms"] == 26
assert round(review["recall_change"], 2) == -0.04''',
    'The gate is O(1) once metrics exist. Obtaining paired metrics costs inference over the same held-out records for joint and single-task models, plus full-path device benchmarks. Training separate baselines increases compute but is necessary to identify whether parameter sharing helps or harms.',
    ['Do not claim a joint win from one improved head while another breaches its minimum.', 'Do not compare models on different head-specific test cohorts.', 'Do not infer serving savings from parameter count alone.'],
    ['machine-learning/multitask-targets-and-label-availability','machine-learning/multitask-head-loss-and-masking','machine-learning/multitask-loss-balance-and-gradient-conflict','machine-learning/multitask-release-review-project'])


add('multitask-release-review-project',
    'Project: release review for shared pump-inspection heads',
    'A multi-task release decision joins per-head label support, separate baselines, error guardrails and measured shared-serving cost.', [
    ('Freeze both targets', 'The depot system predicts seal replacement and repair duration from inspection evidence. Record the replacement horizon, duration population, prediction clock, observed-label masks and exclusion rules. Keep photos of one physical pump in one split and reserve later inspections for the final test. [[machine-learning/multitask-targets-and-label-availability|Target availability]] is the input gate.'),
    ('Train three comparable candidates', 'Use one replacement-only model, one duration-only model and a shared-encoder two-head model. Keep preprocessing and eligible records matched. Tune task weights and shared-layer depth on development data only. Log masked loss denominators and gradient diagnostics but select by held-out task quality. [[machine-learning/multitask-head-loss-and-masking|Head loss]] and [[machine-learning/multitask-loss-balance-and-gradient-conflict|gradient conflict]] support diagnosis.'),
    ('Score each task and slice', 'For replacement, report severe-fault recall, calibration and false review volume. For duration, report absolute error among completed repairs and the fraction without a duration label. Include depot, camera and pump-family slices with sample counts. Compare each head against its single-task counterpart on paired cases. [[machine-learning/multitask-negative-transfer-review|Negative-transfer review]] supplies the comparison.'),
    ('Measure the real serving path', 'Benchmark p95 time, peak memory and fallback behavior for replacement-only calls and calls that request both outputs. Ensure a duration prediction is never presented for a pump outside its target population without a defined interpretation. Keep separate-model artifacts ready if the shared candidate breaches a critical head guardrail.'),
    ('Make the release call', 'The sample packet below holds a shared model with a replacement recall regression despite better duration error and latency. A shadow test can verify logging before action, but it cannot override the predeclared safety minimum. Preserve versions and rollback steps.')],
    '''release_packet = {
    "replacement_labels_mature": True,
    "duration_mask_audited": True,
    "replacement_recall": 0.84,
    "minimum_replacement_recall": 0.87,
    "duration_mae_minutes": 12.7,
    "maximum_duration_mae_minutes": 14.0,
    "p95_full_path_ms": 63,
    "maximum_p95_ms": 78,
    "separate_baselines_kept": True,
    "rollback_tested": True,
}

def multitask_release_gate(packet):
    holds = []
    if not packet["replacement_labels_mature"] or not packet["duration_mask_audited"]:
        holds.append("label contract")
    if packet["replacement_recall"] < packet["minimum_replacement_recall"]:
        holds.append("replacement recall")
    if packet["duration_mae_minutes"] > packet["maximum_duration_mae_minutes"]:
        holds.append("duration error")
    if packet["p95_full_path_ms"] > packet["maximum_p95_ms"] or not packet["separate_baselines_kept"] or not packet["rollback_tested"]:
        holds.append("serving or rollback")
    return "hold: " + ", ".join(holds) if holds else "eligible for shadow review"

assert multitask_release_gate(release_packet) == "hold: replacement recall"''',
    'The gate is O(1). Its inputs require three model trainings, mature head-specific labels, paired held-out scoring and device benchmarks. A shared encoder may lower inference cost when both heads run, but training and monitoring can become more complex. The example thresholds are local operating rules, not general standards.',
    ['Do not infer that the shared model is better because total loss fell.', 'Do not present a duration head outside its defined population.', 'Do not release after a critical head regresses merely because another head or latency improves.'],
    ['machine-learning/multitask-targets-and-label-availability','machine-learning/multitask-head-loss-and-masking','machine-learning/multitask-loss-balance-and-gradient-conflict','machine-learning/multitask-negative-transfer-review','machine-learning/positive-unlabeled-release-project'])


publish_batch(
    lessons,
    module_title='Multi-task models and shared representation',
    module_summary='Define each target and mask, train separate heads, inspect loss conflicts and compare every task with a standalone baseline.',
    project_heading='Shared pump-inspection model release review',
    crosslinks=[
        ('machine-learning/multilabel-schema-and-unknown-targets', lessons[0]['path']),
        ('machine-learning/teacher-student-distillation-objective', lessons[1]['path']),
        ('machine-learning/non-iid-client-drift-and-local-steps', lessons[2]['path']),
        ('machine-learning/negative-transfer-by-target-slice', lessons[3]['path']),
        ('machine-learning/model-compression-release-project', lessons[4]['path']),
    ],
    sort_start=6300,
)
