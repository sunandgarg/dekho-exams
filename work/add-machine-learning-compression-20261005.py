"""Add original model-compression lessons tied to measured deployment costs."""
from ml_fixture_writer_20261005 import publish_batch

lessons = []


def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='machine-learning/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))


add('model-inference-budget-and-device-profile',
    'Model inference budget and device profile',
    'A compression target should be defined by end-to-end latency, peak memory, artifact size and error on the deployment device before any model is changed.', [
    ('Measure the path users wait for', 'A depot camera model does not serve only a matrix multiplication. Image decode, crop, normalization, encoder, head, serialization and queue time all affect the moment an inspection result arrives. Set a decision deadline and profile the full pipeline on the intended device under realistic concurrency. [[deep-learning/inference-schema-and-latency|The serving guide]] defines the input and timing boundary.'),
    ('Report a distribution, not a fastest run', 'Warm up the runtime, then retain enough timed cases across image sizes and camera types. The code computes a nearest-rank median and 95th percentile from an illustrative set of completed requests; it is a statistics check, not an actual benchmark. Report sample count, hardware, batch size, thread count and cold-start behavior with the numbers. A compressed model that helps the median but misses the deadline for the largest images may not help operations.'),
    ('Measure memory and storage separately', 'Artifact bytes affect delivery and cold start; peak resident memory includes activations, runtime and preprocessing buffers. Parameter count is neither peak memory nor end-to-end latency. A sparse weight tensor may serialize smaller while running at the same speed on a backend without sparse kernels. [[machine-learning/structured-pruning-and-compute-shape|Pruning]] makes that distinction concrete.'),
    ('Keep accuracy at the same decision point', 'The baseline and candidate need the same target cohort, preprocessing contract, threshold and action cost unless a policy change is explicitly part of the comparison. Report false negatives by depot and camera, not only average accuracy. [[machine-learning/negative-transfer-by-target-slice|Target-slice auditing]] can expose a small but costly regression.'),
    ('Turn the budget into a test', 'Name maximum artifact size, peak memory, p95 latency and acceptable error before tuning compression settings. Use development data for choosing settings and a later untouched target period for acceptance. [[machine-learning/compression-pareto-and-shadow-check|The Pareto review]] compares candidates; [[machine-learning/model-compression-release-project|the project]] records promotion rules.')],
    '''from math import ceil

# Completed end-to-end inspection requests on one declared device profile.
latency_ms = [32, 35, 36, 37, 39, 40, 42, 43, 44, 45,
              46, 47, 48, 49, 50, 52, 55, 58, 67, 74]

def nearest_rank(values, fraction):
    if not values or not 0 < fraction <= 1:
        raise ValueError("valid samples and fraction required")
    ordered = sorted(values)
    return ordered[ceil(fraction * len(ordered)) - 1]

profile = {"requests": len(latency_ms),
           "median_ms": nearest_rank(latency_ms, 0.50),
           "p95_ms": nearest_rank(latency_ms, 0.95),
           "deadline_misses": sum(duration > 60 for duration in latency_ms)}
assert profile == {"requests": 20, "median_ms": 45,
                   "p95_ms": 67, "deadline_misses": 2}''',
    'Sorting N latency samples takes O(N log N) time and O(N) storage; streaming approximate quantiles can reduce memory for large telemetry. A valid device benchmark consumes repeated real inference and must include realistic concurrency and input sizes. Training or compressing a model can cost far more than this reporting step.',
    ['Do not compare candidates timed on different hardware or input mixes.', 'Do not call parameter count a measured memory or latency saving.', 'Do not hide cold start or tail latency behind an average.'],
    ['machine-learning/teacher-student-distillation-objective','machine-learning/structured-pruning-and-compute-shape','machine-learning/affine-quantization-and-range-audit','machine-learning/compression-pareto-and-shadow-check'])


add('teacher-student-distillation-objective',
    'Teacher–student distillation objective',
    'Distillation trains a smaller student against task labels and softened teacher predictions, then tests whether the student preserves target-task decisions at lower serving cost.', [
    ('Keep the teacher frozen', 'A large parcel-image teacher can supply class logits on the target training cohort. A smaller student learns from true damage labels and the teacher’s relative scores; the teacher is not updated by the student loss. The code computes one hard-label cross-entropy and one temperature-scaled teacher-to-student divergence, then combines them. It is an objective calculation, not a full neural training framework. [[deep-learning/logits-loss-gradient|Logit and loss mechanics]] give the optimization context.'),
    ('Use the temperature consistently', 'Divide both teacher and student logits by the same positive temperature before softmax. A higher value exposes more of the relative mass in lower-ranked classes. The conventional temperature-squared factor keeps the soft-loss scale from vanishing as the distribution softens; its coefficient still requires development tuning. Do not copy a teacher’s incorrect confidence as ground truth. [[machine-learning/probability-calibration|Calibration]] is a separate check.'),
    ('Protect the target holdout', 'Generate teacher targets for training cases only. Select student size, loss mixture and checkpoint on development data, then evaluate on a target holdout untouched by those choices. If the teacher was trained on target-test images, a favorable student comparison can inherit overlap. [[machine-learning/pretraining-overlap-and-provenance-audit|The provenance audit]] records what is known about teacher training.'),
    ('Compare with a student trained without the teacher', 'The relevant gain is not only whether the student approaches teacher accuracy. Compare a same-size student trained on true labels alone, using identical target splits and serving hardware. Report class-specific misses, especially expensive damage types, and the full-pipeline speed. [[machine-learning/model-inference-budget-and-device-profile|Device profiling]] defines the cost side.'),
    ('Know the limits of imitation', 'Teacher predictions may carry source-domain shortcuts or annotation mistakes into the student. A small model may be less accurate on rare camera conditions even when mean loss improves. Inspect paired target errors and retain a manual-review fallback. [[machine-learning/model-compression-release-project|The release project]] treats that as a decision condition.')],
    '''from math import exp, log

teacher_logits = (2.4, 0.9, -0.7)
student_logits = (1.8, 1.1, -0.4)
true_class = 0  # Parcel requires seal review.
temperature = 2.5
soft_weight = 0.6

def softmax(logits, scale=1.0):
    if scale <= 0:
        raise ValueError("positive temperature required")
    shifted = [value / scale for value in logits]
    peak = max(shifted)
    exponentials = [exp(value - peak) for value in shifted]
    total = sum(exponentials)
    return [value / total for value in exponentials]

teacher_soft = softmax(teacher_logits, temperature)
student_soft = softmax(student_logits, temperature)
soft_loss = sum(teacher_share * log(teacher_share / student_share)
                for teacher_share, student_share in zip(teacher_soft, student_soft))
soft_loss *= temperature ** 2
hard_loss = -log(softmax(student_logits)[true_class])
combined_loss = soft_weight * soft_loss + (1 - soft_weight) * hard_loss
assert 0 < soft_loss < hard_loss
assert combined_loss > 0''',
    'For C output classes, this per-case objective costs O(C) time and O(C) temporary probabilities. Training the student also requires its forward and backward passes plus teacher inference or stored teacher logits. At serving time only the student should run; measure the complete pipeline rather than assuming parameter reduction guarantees speed.',
    ['Do not soften only the teacher logits while comparing against an unsoftened student distribution.', 'Do not train or select from an untouched target holdout.', 'Do not accept average imitation quality without rare-class and device checks.'],
    ['machine-learning/model-inference-budget-and-device-profile','machine-learning/structured-pruning-and-compute-shape','machine-learning/compression-pareto-and-shadow-check','machine-learning/model-compression-release-project'])


add('structured-pruning-and-compute-shape',
    'Structured pruning and compute shape',
    'Structured pruning removes an entire channel or unit and its connected weights so the exported computation can actually shrink, subject to backend support and accuracy checks.', [
    ('Distinguish a zero from a smaller graph', 'Setting individual weights to zero creates sparsity but can leave dense tensor shapes unchanged. Removing a whole hidden unit changes the first layer’s output width and the next layer’s input width. The code removes one unit from a two-layer toy head, updates both matrices and counts stored weights. The operation is illustrative; a real graph must also update biases, normalization and all downstream branches. [[machine-learning/model-inference-budget-and-device-profile|Measured profiling]] decides whether the edit helps.'),
    ('Choose units on development data', 'Magnitude, activation statistics and sensitivity tests can propose units to prune, but none is a guaranteed measure of operational importance. Remove in stages, retrain or fine-tune if needed, and compare with an unpruned checkpoint on the same held-out target cohort. [[machine-learning/staged-fine-tuning-and-checkpoint-selection|Checkpoint selection]] keeps the final test isolated.'),
    ('Preserve the feature contract', 'A pruned head still expects the same incoming embedding ordering unless the encoder is also changed. If pruning reaches the encoder, output shapes and every connected consumer need versioned updates. A stale consumer can fail loudly or, worse, accept a wrong vector length after padding. [[machine-learning/pretrained-encoder-target-contract|The target contract]] pins shape and preprocessing.'),
    ('Do not promise runtime speed from sparsity alone', 'Backends differ in whether they exploit zero blocks or smaller dense matrices. A pruned graph may serialize smaller yet run slower because of added conversion, poor kernel choice or memory movement. Benchmark artifact bytes, peak memory and p95 latency on the real serving device. [[machine-learning/compression-pareto-and-shadow-check|The Pareto review]] uses observed cost, not a theoretical operations count.'),
    ('Audit error after each removal', 'A unit with low average activation may be important for a rare package material. Compare false negatives by label, site and image type, and keep an unpruned rollback artifact. [[machine-learning/negative-transfer-by-target-slice|Paired slice checks]] capture a regression hidden by mean accuracy.')],
    '''# Two-layer inspection head: three input features, four hidden units,
# then one output. Units are columns in input_to_hidden and rows below.
input_to_hidden = [
    [0.3, 0.8, -0.4, 0.2],
    [0.1, -0.5, 0.7, 0.6],
    [0.9, 0.2, 0.4, -0.3],
]
hidden_to_output = [[0.6], [-0.2], [0.8], [0.1]]
kept_units = (0, 2, 3)

def remove_hidden_units(first_layer, second_layer, retained):
    if len(second_layer) != len(first_layer[0]):
        raise ValueError("hidden width mismatch")
    return ([[row[index] for index in retained] for row in first_layer],
            [second_layer[index] for index in retained])

smaller_first, smaller_second = remove_hidden_units(
    input_to_hidden, hidden_to_output, kept_units)
original_weights = sum(map(len, input_to_hidden)) + sum(map(len, hidden_to_output))
remaining_weights = sum(map(len, smaller_first)) + sum(map(len, smaller_second))
assert original_weights == 16
assert remaining_weights == 12''',
    'Removing H of U hidden units in a dense D-to-U-to-O head reduces weight storage from DU + UO to D(U-H) + (U-H)O. Rebuilding matrices costs O(DU + UO) time in the teaching code. Actual speed depends on backend kernels, batch size and surrounding preprocessing.',
    ['Do not call zero-valued weights a guaranteed latency improvement.', 'Do not prune one layer without updating every connected tensor and state.', 'Do not select units using the final target test.'],
    ['machine-learning/model-inference-budget-and-device-profile','machine-learning/affine-quantization-and-range-audit','machine-learning/compression-pareto-and-shadow-check','machine-learning/model-compression-release-project'])


add('affine-quantization-and-range-audit',
    'Affine quantization and range audit',
    'Quantization maps floating values to a finite integer range using a scale and zero point, trading representation precision for possible model-size and device-speed gains.', [
    ('Understand the mapping', 'For a chosen floating range, a uniform integer quantizer rounds each value divided by a scale and shifted by a zero point, then clamps to supported integer limits. Dequantization reverses the mapping approximately. The code uses a symmetric signed eight-bit teaching variant with zero point zero. A production converter chooses ranges and operator behavior for its backend; copying this small function is not an export pipeline. [[machine-learning/model-inference-budget-and-device-profile|The device profile]] tells whether a lower-precision artifact helps.'),
    ('Choose calibration data with coverage', 'Post-training activation quantization needs a representative set of inputs to observe value ranges. If calibration sees only bright parcel photos, darker depot images may clip. Measure saturation and output drift by camera and package type. Never select the calibration range on the final target test. [[computer-vision/grouped-evaluation-and-shift|Target grouping]] preserves the later check.'),
    ('Separate size from accuracy and speed', 'Eight-bit weights can use fewer bytes than 32-bit floats, but extra scales, unsupported operators or conversion steps affect both size and latency. Some hardware accelerates the integer path; other devices may not. Report actual artifact bytes, p95 latency and peak memory on the serving backend, with the same preprocessing as the baseline. [[machine-learning/compression-pareto-and-shadow-check|The Pareto review]] keeps these measurements together.'),
    ('Investigate outliers and rare errors', 'A wide calibration range may waste precision near common values; a tight one clips rare extremes. Quantization can move a parcel score across an action threshold even when average numerical error is small. Compare issued decisions and per-label false negatives, not only mean absolute output difference. [[machine-learning/per-label-thresholds-and-action-cost|Action costs]] identify consequential changes.'),
    ('Escalate only after measured failure', 'If post-training conversion causes unacceptable target error, consider another calibration policy or quantization-aware training, selected on development data. This increases training and maintenance cost; it is not automatically better. [[machine-learning/model-compression-release-project|The release review]] records the exact converter, range and rollback artifact.')],
    '''from math import isfinite

calibration_peak = 2.54
scale = calibration_peak / 127

def symmetric_int8(values, step):
    if step <= 0:
        raise ValueError("positive scale required")
    encoded = []
    for value in values:
        if not isfinite(value):
            raise ValueError("finite input required")
        encoded.append(max(-127, min(127, round(value / step))))
    return encoded, [integer * step for integer in encoded]

inspection_values = [0.0, 0.37, -1.14, 2.8]
integers, restored = symmetric_int8(inspection_values, scale)
clipped = sum(abs(value / scale) > 127 for value in inspection_values)
assert integers[0] == 0
assert integers[-1] == 127
assert clipped == 1
assert abs(restored[1] - inspection_values[1]) <= scale / 2 + 1e-12''',
    'Converting N scalar values costs O(N) time and O(N) output storage; packed integer model inference depends on backend support. Calibration scans representative data, and quantization-aware training adds model optimization work. Measure transfer and conversion overhead, because integer arithmetic alone does not determine end-to-end latency.',
    ['Do not calibrate activation ranges on the sealed final test.', 'Do not equate fewer weight bits with a measured latency gain.', 'Do not ignore threshold flips on rare costly cases.'],
    ['machine-learning/model-inference-budget-and-device-profile','machine-learning/structured-pruning-and-compute-shape','machine-learning/compression-pareto-and-shadow-check','machine-learning/model-compression-release-project'])


add('compression-pareto-and-shadow-check',
    'Compression Pareto review and shadow check',
    'A compression candidate should be compared on target error and measured serving resources, with a shadow period before it changes live decisions.', [
    ('Keep all dimensions visible', 'A student, pruned head and quantized artifact may trade target error, p95 latency and peak memory differently. A candidate dominates another only if it is no worse on every declared measure and better on at least one. The code finds nondominated candidates from an invented device profile; it does not decide which tradeoff the business can accept. [[machine-learning/model-inference-budget-and-device-profile|The baseline profile]] fixes hardware and measurement rules.'),
    ('Apply hard acceptance bounds first', 'A model that exceeds the memory budget or breaches a safety-critical miss limit is not rescued by a low average latency. Keep error by site and label, artifact compatibility and security checks as gates. Then compare the surviving candidates’ operating costs. [[machine-learning/multilabel-metrics-and-denominators|Per-label denominators]] prevent a small rare class from disappearing in a pooled score.'),
    ('Shadow the selected artifact', 'Run the candidate beside the live model on the same incoming cases without changing actions. Log both outputs, missing scores, latency and later outcomes. A shadow comparison tests serving and predictive behavior under the current policy; if the candidate would alter review decisions, observed outcomes may reflect current interventions. [[machine-learning/champion-challenger-shadow-comparison|The shadow guide]] states that boundary.'),
    ('Measure cold and loaded conditions', 'A smaller file may cold-start faster yet run no faster after warm-up. Benchmark under expected concurrency and image sizes, with p95 and deadline misses. Watch peak resident memory and crash rate during the shadow period. [[deep-learning/inference-schema-and-latency|Serving contracts]] include these failures.'),
    ('Name promotion and rollback', 'Record chosen candidate, device profile, model version, target cohort, acceptance limits, pilot owner and old artifact retained for rollback. Do not choose a candidate on the final test and then call that same test independent evidence. [[machine-learning/model-compression-release-project|The release project]] assembles the decision packet.')],
    '''# Same target cohort and serving device for all candidates.
candidates = [
    {"name": "baseline", "error": 0.07, "p95_ms": 84, "peak_mb": 620},
    {"name": "student", "error": 0.08, "p95_ms": 51, "peak_mb": 290},
    {"name": "pruned", "error": 0.09, "p95_ms": 62, "peak_mb": 340},
    {"name": "int8", "error": 0.075, "p95_ms": 56, "peak_mb": 230},
]
metrics = ("error", "p95_ms", "peak_mb")

def dominates(left, right):
    return (all(left[key] <= right[key] for key in metrics) and
            any(left[key] < right[key] for key in metrics))

frontier = [candidate["name"] for candidate in candidates
            if not any(dominates(other, candidate) for other in candidates
                       if other is not candidate)]
assert set(frontier) == {"baseline", "student", "int8"}''',
    'A direct Pareto screen over C candidates and M metrics takes O(C squared times M) time and O(C) output storage; C is usually small. Measuring each model on the same target set and hardware costs far more. Shadow inference temporarily doubles or increases serving work and must fit available capacity.',
    ['Do not compare latency from different devices or loads.', 'Do not choose a candidate on the final test and reuse that test as an independent release check.', 'Do not call a shadow gain proven policy value when the live action would change.'],
    ['machine-learning/model-inference-budget-and-device-profile','machine-learning/teacher-student-distillation-objective','machine-learning/structured-pruning-and-compute-shape','machine-learning/model-compression-release-project'])


add('model-compression-release-project',
    'Model compression release project',
    'Review a smaller parcel-inspection model against the same target cases and serving device, with accuracy, memory, latency, shadow behavior and rollback.', [
    ('Set the deployment budget', 'Record the camera input contract, target label definitions, decision deadline, p95 latency limit, peak memory cap and artifact size limit. Profile the complete existing service before choosing a compression method. [[machine-learning/model-inference-budget-and-device-profile|The baseline guide]] defines the measurements.'),
    ('Produce candidate artifacts', 'A student may train from teacher outputs; a structured-pruned model removes connected units; a quantized model changes numeric representation. Each method needs versioned settings and a target development cohort. The methods can be combined, but every combination is a new candidate requiring its own validation. [[machine-learning/teacher-student-distillation-objective|Distillation]], [[machine-learning/structured-pruning-and-compute-shape|pruning]] and [[machine-learning/affine-quantization-and-range-audit|quantization]] have different failure modes.'),
    ('Compare outcomes and cost', 'Use a sealed target period and the same device to report per-label misses, calibration, p95 latency, peak memory, artifact bytes and deadline failures. Evaluate site and image-size slices. A nondominated candidate is not automatically acceptable if it breaches a hard miss or capacity bound. [[machine-learning/compression-pareto-and-shadow-check|The Pareto review]] makes the tradeoffs visible.'),
    ('Shadow before a bounded pilot', 'Log candidate and live predictions on the same requests without changing actions. Count missing candidate scores and runtime errors. Inspect later mature outcomes, then plan any action-changing pilot with an owner and retained old artifact. [[machine-learning/champion-challenger-shadow-comparison|Shadow comparison]] is evidence about the current policy, not a full counterfactual policy test.'),
    ('Record what remains unresolved', 'The code checks that a release packet includes required artifacts. It cannot certify the model or make an acceptance decision from absent numbers. Attach measured results and limits. If device testing or rare-label review is incomplete, hold promotion.')],
    '''def compression_release_gate(packet):
    required = {
        "device_profile_fixed": "device profile",
        "target_test_sealed": "target test",
        "rare_label_errors_checked": "rare-label errors",
        "p95_and_memory_measured": "latency and memory",
        "artifact_compatibility_checked": "artifact compatibility",
        "shadow_failures_reported": "shadow failures",
        "rollback_artifact_retained": "rollback artifact",
    }
    missing = [label for field, label in required.items() if not packet.get(field)]
    return "eligible for pilot review" if not missing else "hold: " + ", ".join(missing)

inspection_packet = {
    "device_profile_fixed": True, "target_test_sealed": True,
    "rare_label_errors_checked": False,
    "p95_and_memory_measured": True,
    "artifact_compatibility_checked": True,
    "shadow_failures_reported": False,
    "rollback_artifact_retained": True,
}
assert compression_release_gate(inspection_packet) == (
    "hold: rare-label errors, shadow failures"
)''',
    'The gate is O(K) for K checks. Distillation adds teacher inference and student training; pruning and quantization add conversion and validation. End-to-end benchmarks and a shadow period use real serving resources, and enough target labels are needed to assess rare costly regressions.',
    ['Do not claim a model is faster from size or parameter count alone.', 'Do not accept pooled accuracy when rare costly labels regress.', 'Do not discard the previous serving artifact before rollback is tested.'],
    ['machine-learning/model-inference-budget-and-device-profile','machine-learning/teacher-student-distillation-objective','machine-learning/structured-pruning-and-compute-shape','machine-learning/affine-quantization-and-range-audit','machine-learning/compression-pareto-and-shadow-check','machine-learning/multilabel-release-review-project'])


publish_batch(
    lessons,
    module_title='Model compression and serving tradeoffs',
    module_summary='Measure the deployment budget, compare distillation, pruning and quantization, then review target error and device cost.',
    project_heading='Model compression release review',
    crosslinks=[
        ('deep-learning/inference-schema-and-latency', lessons[0]['path']),
        ('machine-learning/transfer-learning-release-review-project', lessons[1]['path']),
        ('deep-learning/checkpoint-resume-state', lessons[2]['path']),
        ('machine-learning/per-label-thresholds-and-action-cost', lessons[3]['path']),
        ('machine-learning/champion-challenger-shadow-comparison', lessons[4]['path']),
        ('machine-learning/sequential-policy-review-project', lessons[5]['path']),
    ],
    sort_start=5700,
)
