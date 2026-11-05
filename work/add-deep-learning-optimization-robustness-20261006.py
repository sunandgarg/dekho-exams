"""Add optimizer-selection and input-sensitivity Deep Learning paths."""
from de_batch_publisher import publish

OPTIMIZATION = 'Optimization schedules and checkpoint selection'
ROBUSTNESS = 'Perturbation sensitivity and release gates'
LESSONS = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    assert len(sections) == 5
    LESSONS.append(dict(path='deep-learning/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add('adamw-decay-groups-and-update-indexed-schedules',
    'AdamW decay groups and update-indexed schedules',
    'An optimizer schedule needs an exact update counter, a declared parameter-group policy and a resume rule; epoch labels alone are too vague.', [
    ('Count parameter updates rather than batches', 'Gradient accumulation can process several microbatches before one optimizer step. A learning-rate schedule intended to warm over five parameter updates should advance only when those five updates occur, not after each microbatch. Record completed update count in the checkpoint and define whether the logged rate belongs to the update just made or the next one. With 47 planned updates and a five-update warmup, a resume after update 23 must use the rate for update 24, not restart at the first warmup value. [[deep-learning/gradient-accumulation-and-effective-batch|Effective-batch accounting]] supplies the same update boundary.'),
    ('Separate decay from the data gradient', 'AdamW applies decoupled weight shrinkage rather than adding a squared-weight penalty into Adam’s adaptive gradient statistics. That does not mean every parameter should decay. A common policy excludes biases and normalization offsets, while matrix weights receive a declared coefficient. Enumerate groups before constructing the optimizer and assert every trainable parameter belongs to exactly one group. Otherwise a parameter may silently receive two updates or no update. The code demonstrates the policy with a single linear layer; a production model needs a complete audited parameter inventory.'),
    ('Specify the schedule equation', 'The example uses a linear warmup followed by a cosine descent to a nonzero floor. It computes the learning rate explicitly from zero-based update index, so it does not depend on an implicit scheduler step order. The first warmup update receives one-fifth of peak rate; the fifth receives peak rate; the final planned update receives the floor. If training ends early, the rate may never reach the floor. If training extends beyond the budget, define whether to clamp at the floor or recompute the plan. Store peak, floor, warmup count and total planned updates.'),
    ('Resume the complete optimizer state', 'Loading model weights without Adam moments changes the next parameter update even if learning rate is restored. A coherent checkpoint includes optimizer state, completed update count, scaler state for mixed precision and any sampler position needed to reconstruct the next batch. Restore the optimizer before setting the rate for the next update, then compare one fixed-batch step with an uninterrupted reference. [[deep-learning/checkpoint-resume-state|The resume lesson]] gives the broader state inventory. A plotted learning-rate line is no proof of resume parity.'),
    ('Compare schedules fairly', 'Hold data order, effective batch, total accepted examples, architecture and evaluation windows fixed when comparing a constant rate with warmup and decay. Report class-specific validation behavior and multiple seeds rather than naming the schedule that happened to achieve one best run. An overly small floor may stop useful late learning; an overly high peak may destabilize early updates. [[deep-learning/early-stopping-best-state-and-seed-variance|Checkpoint selection]] must follow a separately declared rule, or schedule tuning and model selection become entangled.')],
    '''import math
import torch
from torch import nn

receipt_classifier = nn.Linear(9, 3)
optimizer = torch.optim.AdamW([
    {"params": [receipt_classifier.weight], "weight_decay": 0.04},
    {"params": [receipt_classifier.bias], "weight_decay": 0.0},
], lr=0.001)

planned_updates = 47
warmup_updates = 5
peak_rate = 0.001
floor_rate = 0.00003

def rate_for_update(update_index: int) -> float:
    if not 0 <= update_index < planned_updates:
        raise ValueError("update outside planned budget")
    if update_index < warmup_updates:
        return peak_rate * (update_index + 1) / warmup_updates
    progress = (update_index - warmup_updates + 1) / (planned_updates - warmup_updates)
    return floor_rate + 0.5 * (peak_rate - floor_rate) * (1 + math.cos(math.pi * progress))

assert math.isclose(rate_for_update(0), 0.0002)
assert math.isclose(rate_for_update(4), peak_rate)
assert math.isclose(rate_for_update(46), floor_rate)
for group in optimizer.param_groups:
    group["lr"] = rate_for_update(23)''',
    'The schedule calculation is O(1) per optimizer update. AdamW stores first and second moments for each trainable parameter, so optimizer state can exceed model-weight storage; excluding bias from decay does not remove its moment storage. The warmup and cosine arithmetic is negligible beside a forward and backward pass. The material cost is experimental: comparing schedules fairly requires multiple training runs, and a wrong update index can waste those runs while still producing a smooth-looking learning-rate chart.',
    ['Do not advance an update-indexed schedule for every accumulation microbatch.', 'Do not load weights alone and call the next AdamW update an exact resume.', 'Do not apply weight decay twice by combining decoupled decay with an unexamined L2 penalty.'],
    ['deep-learning/gradient-accumulation-and-effective-batch', 'deep-learning/checkpoint-resume-state', 'deep-learning/mixed-precision-scaling-and-gradient-clipping', 'deep-learning/early-stopping-best-state-and-seed-variance', 'deep-learning/receipt-optimizer-selection-project'], OPTIMIZATION)

add('early-stopping-best-state-and-seed-variance',
    'Early stopping, best-state restoration and seed variance',
    'Stopping a run and choosing a checkpoint are separate actions; a patience counter is valid only with a fixed metric, cadence and tie policy.', [
    ('Freeze the selection metric first', 'Decide whether validation loss, clipped-edge recall or a constrained composite selects a checkpoint before reading the run. Validation loss is continuous and often easier to rank, but the deployed decision may care about a rare class or review capacity. If several metrics matter, set hard gates and one tie-break metric. Keep threshold fitting and calibration on separate data if they influence a final decision. [[deep-learning/temperature-scaling-and-selective-risk|Confidence selection]] should not secretly reuse the checkpoint-selection population.'),
    ('Define patience in evaluations', 'Patience counts validation checks, not necessarily epochs. An evaluation every 300 parameter updates with patience three allows 900 updates without a qualifying improvement. Define a minimum improvement, comparison direction and tie rule. In the example, a new loss must beat the best by more than 0.005; tiny oscillations do not reset patience. A run that stops on three misses may still have passed through a transient local fluctuation, so do not call patience a guarantee against overfitting. Record each check with completed update count.'),
    ('Restore the best coherent generation', 'The last model in memory after early stopping is usually not the chosen model. Save a deep copy or durable checkpoint when a qualifying improvement occurs, and restore that generation for final evaluation. If training might resume from the best checkpoint, retain its optimizer, scheduler, scaler and sampler state too. For pure inference, model weights, buffers and preprocessing are sufficient, but that is a different artifact. [[deep-learning/checkpoint-resume-state|Resume-state accounting]] avoids confusing the two. Verify the restored checkpoint reproduces saved validation logits.'),
    ('Estimate run-to-run variation', 'A single seed is one realization of initialization, data shuffling and augmentation. Repeat a small set of defensible candidate configurations over the same declared seeds, then report the spread of rare-defect recall and false accepts. Do not cherry-pick the best seed after opening final test. If the winning configuration changes across seeds, the conclusion is uncertain even if one run has a high score. Split IDs and device slices should remain fixed so variance is not confounded with a changing evaluation population.'),
    ('Protect the final test', 'Use the development set to select schedule, patience, objective weights and checkpoint. After that, lock the procedure and run the final physical-receipt holdout once for a release decision. Every repeated look at final test to adjust hyperparameters spends information from that holdout. If the result fails, document the failure and create a new evaluation population for another selection cycle. [[deep-learning/receipt-optimizer-selection-project|The project]] requires a predeclared selection record rather than a retrospective narrative.')],
    '''from dataclasses import dataclass

@dataclass
class SelectionState:
    best_loss: float = float("inf")
    best_check: int = -1
    missed_checks: int = 0

def observe_validation(state: SelectionState, check_index: int,
                       validation_loss: float, min_improvement: float,
                       patience: int) -> bool:
    if validation_loss < state.best_loss - min_improvement:
        state.best_loss = validation_loss
        state.best_check = check_index
        state.missed_checks = 0
    else:
        state.missed_checks += 1
    return state.missed_checks >= patience

loss_trace = [0.53, 0.47, 0.461, 0.460, 0.4605, 0.4603, 0.461]
selection = SelectionState()
stop_check = None
for check_index, observed_loss in enumerate(loss_trace):
    if observe_validation(selection, check_index, observed_loss, 0.005, 3):
        stop_check = check_index
        break
assert selection.best_check == 2
assert stop_check == 5''',
    'The patience logic is O(1) per validation check, but validation itself costs a model forward over every selected example and checkpoint storage can be large. Saving every slight improvement may create excessive I/O; a declared minimum improvement controls selection frequency, not correctness. Multiple seeds multiply training cost roughly by the number of runs. That expense is useful when result variance is comparable to the improvement being claimed; report compute budget and uncertainty rather than relying on one lucky run.',
    ['Do not evaluate the final in-memory model when the best checkpoint occurred earlier.', 'Do not count optimizer updates as patience checks when validation cadence differs.', 'Do not choose a seed after examining the final test and report it as an unbiased result.'],
    ['deep-learning/train-eval-validation-loop', 'deep-learning/checkpoint-resume-state', 'deep-learning/adamw-decay-groups-and-update-indexed-schedules', 'deep-learning/receipt-optimizer-selection-project', 'deep-learning/temperature-scaling-and-selective-risk'], OPTIMIZATION)

add('receipt-optimizer-selection-project',
    'Project: select a receipt training schedule without test leakage',
    'Compare constant and warmup-decay training under one receipt split, then restore a chosen checkpoint and audit stability across seeds before final release.', [
    ('Lock the experiment manifest', 'Group receipt crops by physical receipt and reserve training, development, calibration and final-test populations. Fix model shape, optimizer family, effective batch, accepted-example budget and class weights. Define one constant-rate candidate and one five-update warmup followed by a 47-update cosine decay. Record per-parameter decay groups and whether the rate is applied before each parameter step. [[deep-learning/adamw-decay-groups-and-update-indexed-schedules|The schedule contract]] makes a resumed run comparable with an uninterrupted one.'),
    ('Run one seed as a smoke test', 'Log the first, warmup-end, resumed and final planned learning rates, along with loss by class and accepted-example counts. Save a coherent checkpoint at update 23, resume it and compare the next fixed-batch parameter update with the uninterrupted reference. A mismatch can come from optimizer moments, scheduler index, sampler position or mixed-precision scaler. Do not proceed to expensive repeats until this parity check passes. [[deep-learning/checkpoint-resume-state|The checkpoint lesson]] lists the state needed for replay.'),
    ('Apply a predeclared selection rule', 'Evaluate on the development population at fixed update intervals and save the best qualifying checkpoint under one primary metric, with a declared minimum improvement and patience. Restore that checkpoint rather than the last one. If clipped-edge recall has a hard floor, reject any candidate below it before ranking validation loss. The code below checks a decision record over illustrative measured results; it does not train a model or claim these numbers were observed. [[deep-learning/early-stopping-best-state-and-seed-variance|The selection lesson]] sets the tie policy.'),
    ('Repeat and inspect spread', 'Run both candidates over the same set of independent seeds, preserving split IDs and evaluation cadence. Report per-seed best checkpoint update, clipped-edge recall, false accepts and calibration error; show the spread, not only the mean. If a candidate wins one seed but loses most others, do not call it the stable schedule. A rare class with few receipts needs event counts alongside percentages. Review any data-source or device slice whose result moves in the opposite direction from the aggregate.'),
    ('Open final test once', 'After choosing a schedule and checkpoint policy on development data, fit any probability temperature or review threshold on the calibration group. Freeze model artifact, preprocessing and decision policy. Run one final held-out physical-receipt evaluation and publish all release gates, including failures. Retain the prior model if the new plan misses a class-specific gate. Deliver the manifest, update-rate trace, resume-parity check, per-seed table and final decision, not merely the best validation scalar.')],
    '''from dataclasses import dataclass

@dataclass(frozen=True)
class RunResult:
    seed: int
    clipped_recall: float
    false_accepts: int
    best_validation_loss: float
    restored_best: bool

def eligible_results(runs: list[RunResult], minimum_recall: float,
                     maximum_false_accepts: int) -> list[RunResult]:
    return [run for run in runs if run.restored_best and
            run.clipped_recall >= minimum_recall and
            run.false_accepts <= maximum_false_accepts]

schedule_runs = [
    RunResult(47, 0.94, 2, 0.31, True),
    RunResult(71, 0.92, 3, 0.29, True),
    RunResult(83, 0.91, 2, 0.33, False),
]
accepted = eligible_results(schedule_runs, 0.92, 3)
assert [run.seed for run in accepted] == [47, 71]
assert len(accepted) < len(schedule_runs)''',
    'A fair schedule comparison costs at least one full training run per candidate and seed. Validation cadence adds repeated forward passes; coherent checkpoints add disk I/O and optimizer-state storage. The gate code is O(R) for R run records, but preparing reliable records is the expensive part. Keep the same accepted-example and update budget when comparing schedules, and include time spent on resume and calibration checks in the project estimate.',
    ['Do not use the final test to tune warmup length or patience.', 'Do not rank a run whose best state was never restored.', 'Do not report only the best seed when schedule choice is unstable across repeats.'],
    ['deep-learning/adamw-decay-groups-and-update-indexed-schedules', 'deep-learning/early-stopping-best-state-and-seed-variance', 'deep-learning/checkpoint-resume-state', 'deep-learning/receipt-confidence-audit-project', 'deep-learning/receipt-image-quality-project'], OPTIMIZATION, True)

add('fgsm-input-scale-and-perturbation-threat-model',
    'FGSM input scale and perturbation threat models',
    'A gradient-sign perturbation tests one precisely bounded input change; its numeric radius means nothing until image units and attacker access are defined.', [
    ('State what can change', 'Choose whether the test perturbs raw image intensities, normalized tensors, a document crop or a full camera frame. Specify the norm, maximum change, valid pixel range and whether the perturbation may cover text, background or borders. A radius of 0.06 in zero-to-one pixel space is not the same as 0.06 after standardization by a small channel deviation. Real capture problems such as motion blur and paper folds are separate stressors. [[deep-learning/augmentation-leakage-boundary|Augmentation policy]] may already cover some natural changes, but it does not define an adversarial test.'),
    ('Differentiate the input, not parameters', 'For a fixed model and reviewed target label, create a clean input tensor with gradients enabled and compute loss. Obtain the gradient with respect to that input, then add radius times its sign for an untargeted one-step perturbation. Clamp to the valid pixel range and, if preprocessing uses normalization, return to the intended space before applying the bound. Detach the resulting image for evaluation. The code uses a tiny classifier and checks the infinity-norm bound; it says nothing about how a trained receipt model will behave.'),
    ('Keep the threat model honest', 'A one-step gradient-sign search is a diagnostic under white-box access to model gradients, not a proof that all allowed perturbations have been explored. Results depend on clean correctness, label quality and input clipping. Evaluate attack success on examples the model originally classified correctly as well as on the whole population, and report both denominators. Repeated or stronger searches can find failures a single step misses. Do not describe one failed attack as certification of robustness or as a guarantee against camera and print changes.'),
    ('Inspect perturbation visibility', 'Save clean and perturbed pairs at actual display scaling, with the changed-pixel range and regions affected. Receipt text and cut-off edges are semantically sensitive; an imperceptible numeric change may still alter OCR or downstream human interpretation in a low-contrast area. Conversely, a large numeric change may be unrealistic for a capture pipeline. Measure class-specific failures and confidence shifts, especially confident false accepts. [[deep-learning/temperature-scaling-and-selective-risk|Selective risk]] shows whether a review policy catches those cases.'),
    ('Build a repeatable stress suite', 'Version the model, preprocessing, label map, input units, radius and attack implementation. Test multiple radii and independent natural corruption groups without combining them into a single ambiguous score. Keep physical receipt identities out of training if they are in the held-out stress set. [[deep-learning/receipt-perturbation-stress-project|The applied project]] pairs numeric attacks with physically plausible changes and a release decision.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

torch.manual_seed(47)
quality_model = nn.Sequential(nn.Flatten(), nn.Linear(16, 3))
clean_pixels = torch.rand(4, 1, 4, 4).detach().requires_grad_(True)
reviewed_labels = torch.tensor([0, 2, 1, 0])
clean_logits = quality_model(clean_pixels)
clean_loss = functional.cross_entropy(clean_logits, reviewed_labels)
input_gradient = torch.autograd.grad(clean_loss, clean_pixels)[0]
radius = 0.06
perturbed_pixels = (clean_pixels.detach() + radius * input_gradient.sign()).clamp(0, 1)
maximum_change = (perturbed_pixels - clean_pixels.detach()).abs().amax()
assert maximum_change <= radius + 1e-7
assert bool(((perturbed_pixels >= 0) & (perturbed_pixels <= 1)).all())''',
    'One gradient-sign step adds a model forward and backward pass per stress batch, followed by O(BCHW) input arithmetic. Evaluating several radii repeats model work unless the same input gradient is intentionally reused under a stated protocol. More intensive searches can cost many forwards and backwards per example. The cost is acceptable for an offline audit, but applying such a search to every live request would change latency and the threat model. Report hardware, batch size and search budget with robustness results.',
    ['Do not apply a raw-pixel radius directly to standardized tensors without conversion.', 'Do not call one unsuccessful attack a robustness certificate.', 'Do not count initially misclassified examples as new attack successes without separating denominators.'],
    ['deep-learning/augmentation-leakage-boundary', 'deep-learning/adversarial-training-clean-robust-balance', 'deep-learning/receipt-perturbation-stress-project', 'deep-learning/receipt-confidence-audit-project', 'deep-learning/inference-schema-and-latency'], ROBUSTNESS)

add('adversarial-training-clean-robust-balance',
    'Adversarial training and the clean–stress tradeoff',
    'Training on perturbed inputs can reduce failures under a chosen test, but it can also change clean accuracy and does not cover threats outside the declared search.', [
    ('Keep a clean baseline', 'Train and freeze a reference receipt classifier under the existing split, preprocessing and update budget. Measure normal validation and final-test decisions by defect and capture device. The adversarial-training candidate must use the same labeled training identities and a declared extra compute budget. If it sees more real examples or gets more optimizer updates, any difference cannot be assigned to the perturbation policy alone. [[deep-learning/train-eval-validation-loop|The evaluation loop]] should preserve group boundaries and identical class maps.'),
    ('Generate perturbations against the current candidate', 'For each training batch, compute a gradient with respect to the input while holding reviewed labels fixed. Apply a bounded change in the declared pixel space, clamp it and detach the perturbed input before the parameter-update forward pass. The code combines clean and perturbed losses in one optimizer update. It is a one-step stress objective, not an exhaustive inner maximization. If model weights or preprocessing change, cached perturbations become stale. [[deep-learning/fgsm-input-scale-and-perturbation-threat-model|The threat-model lesson]] defines the numeric bound.'),
    ('Balance losses and inspect slices', 'A weighted clean-plus-stress loss exposes a choice: too little stress weight may leave the attack effective; too much may lower performance on ordinary images. Tune the weight and radius on development data, then lock them before final test. Monitor clipped-edge recall, false accepts, confidence and manual-review volume under clean, numeric and natural-corruption conditions. A smaller stress error with a larger clean false-accept rate is not automatically an improvement for the product. [[deep-learning/receipt-confidence-audit-project|The confidence audit]] makes this operational cost visible.'),
    ('Avoid gradient masking claims', 'A model may appear resistant to one gradient attack because of saturated preprocessing or a non-smooth operation, not because the decision is stable. Test more than one search strength, multiple starting points where appropriate and physically plausible corruptions. Check input gradients for finite, nontrivial values and compare against a clean model under the same attack. Do not state a certified guarantee without a method that actually proves one. Keep attack code and normalization versioned so a future audit can reproduce the reported failures.'),
    ('Decide on measured constraints', 'Set release gates before inspecting final test: minimum clean rare-defect recall, maximum false accepts, acceptable review capacity and target stress performance. If no candidate satisfies all gates, keep the reference model and revise data or review policy. [[deep-learning/receipt-perturbation-stress-project|The project]] runs this comparison across numeric and natural perturbations. The training objective is one engineering control, not a substitute for capture quality checks or human review.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

torch.manual_seed(47)
quality_model = nn.Sequential(nn.Flatten(), nn.Linear(16, 3))
optimizer = torch.optim.AdamW(quality_model.parameters(), lr=0.0007)
clean_pixels = torch.rand(5, 1, 4, 4)
reviewed_labels = torch.tensor([0, 1, 2, 1, 0])
attack_source = clean_pixels.detach().clone().requires_grad_(True)
attack_loss = functional.cross_entropy(quality_model(attack_source), reviewed_labels)
input_gradient = torch.autograd.grad(attack_loss, attack_source)[0]
perturbed_pixels = (attack_source.detach() + 0.04 * input_gradient.sign()).clamp(0, 1)

optimizer.zero_grad(set_to_none=True)
clean_loss = functional.cross_entropy(quality_model(clean_pixels), reviewed_labels)
stress_loss = functional.cross_entropy(quality_model(perturbed_pixels), reviewed_labels)
combined_loss = 0.65 * clean_loss + 0.35 * stress_loss
combined_loss.backward()
optimizer.step()
assert torch.isfinite(combined_loss)
assert not perturbed_pixels.requires_grad''',
    'This one-step training example adds an attack forward and backward pass, then evaluates the clean and perturbed batches for the parameter update. It can therefore cost several times a clean-only update, depending on model and batching. Stronger inner searches increase cost with search steps. Input perturbation storage is O(BCHW) and ordinary model gradients still require parameter memory. A numerical stress gain is useful only when clean performance, natural-corruption behavior and deployment latency remain inside the declared gates.',
    ['Do not report robustness only at the radius used during training.', 'Do not train on final-test receipt identities or tune the clean–stress weight on final test.', 'Do not mistake weak input gradients for proven resistance to input changes.'],
    ['deep-learning/fgsm-input-scale-and-perturbation-threat-model', 'deep-learning/receipt-perturbation-stress-project', 'deep-learning/augmentation-leakage-boundary', 'deep-learning/receipt-confidence-audit-project', 'deep-learning/temperature-scaling-and-selective-risk'], ROBUSTNESS)

add('receipt-perturbation-stress-project',
    'Project: stress-test receipt decisions under bounded image changes',
    'Audit a receipt-quality classifier under numeric perturbations and realistic capture changes, then decide whether a stress-trained candidate actually improves the deployed decision.', [
    ('Freeze the deployment path', 'Pin image decode, crop, normalization, model revision, class map, confidence threshold and review routing. Group all captures from one physical receipt before forming training, development and final-test populations. Collect clean held-out examples across devices and rare clipped-edge cases. Save baseline predictions and accepted-case counts before generating any perturbation. [[deep-learning/receipt-image-quality-project|The quality project]] supplies the original classifier contract.'),
    ('Create two distinct stress families', 'First, apply a bounded input-gradient perturbation with radii specified in zero-to-one pixel space, recording clean correctness and changed decisions. Second, use physically plausible capture changes such as measured blur, low exposure, perspective shift and partial edge occlusion. Do not call the second group adversarial examples unless its generation actually follows a search objective. Review altered images to ensure their ground-truth defect label still applies. [[deep-learning/fgsm-input-scale-and-perturbation-threat-model|The numeric test]] has a narrower claim than a camera stress test.'),
    ('Train and evaluate a candidate', 'Train a clean reference and a candidate with a declared clean-plus-stress objective, equal real training identities and a documented update budget. Choose radius and loss weight on development data only. Test several search strengths, not merely the training radius; inspect gradients for finite values. Measure clean, numeric and natural-stress recall and false accepts by class and device. [[deep-learning/adversarial-training-clean-robust-balance|The training lesson]] explains why one improved stress score can conceal a clean regression.'),
    ('Apply a predeclared gate', 'Set minimum clipped-edge recall and maximum false accepts separately for clean and stressed traffic, plus maximum manual-review volume. The code below evaluates illustrative measured slice records; it does not claim a trained model achieved them. If a slice has too few examples, report event counts and postpone a strong pass claim rather than hiding it in a global average. A confidence threshold may route uncertain images to review; count that workload explicitly. [[deep-learning/receipt-confidence-audit-project|The review audit]] makes the denominator visible.'),
    ('Ship a reversible decision', 'Package stress generator version, radii and input units, natural-corruption parameters, slice manifests, model revision, calibration and release-gate table. Keep the previous classifier available. Monitor real-world capture mix, false accepts and manual review after staged rollout; a lab perturbation suite cannot anticipate every camera failure. If a candidate passes numeric stress but harms clean or natural-stress decisions, do not release it. State the remaining untested threat boundaries in the artifact.')],
    '''from dataclasses import dataclass

@dataclass(frozen=True)
class DecisionSlice:
    name: str
    receipt_count: int
    clipped_recall: float
    false_accepts: int
    review_count: int

def failed_gates(slices: list[DecisionSlice]) -> list[str]:
    failures = []
    for result in slices:
        if result.receipt_count < 47:
            failures.append(result.name + ": insufficient evidence")
        if result.clipped_recall < 0.91:
            failures.append(result.name + ": clipped recall")
        if result.false_accepts > 3:
            failures.append(result.name + ": false accepts")
        if result.review_count > 19:
            failures.append(result.name + ": review capacity")
    return failures

audit_slices = [DecisionSlice("clean", 83, 0.95, 2, 12),
                DecisionSlice("low-exposure", 53, 0.90, 3, 17)]
assert failed_gates(audit_slices) == ["low-exposure: clipped recall"]''',
    'For N held-out images and A attack settings, one-step gradient tests add roughly A model backward passes plus prediction forwards, while natural-corruption generation adds image-processing cost. The release-gate scan is O(S) for S slice records, but reliable slice measurement requires enough independent physical receipts. Storing all perturbed images can be expensive; storing seeds, source identities and transform parameters enables replay when the transform is deterministic. Budget manual review for label preservation and high-confidence wrong cases.',
    ['Do not merge clean and stressed scores into one average that hides a rare-class failure.', 'Do not leave input units or perturbation radius out of the audit artifact.', 'Do not call a one-step numeric stress pass a guarantee for physical camera changes.'],
    ['deep-learning/fgsm-input-scale-and-perturbation-threat-model', 'deep-learning/adversarial-training-clean-robust-balance', 'deep-learning/receipt-image-quality-project', 'deep-learning/receipt-confidence-audit-project', 'deep-learning/receipt-optimizer-selection-project'], ROBUSTNESS, True)

CROSSLINKS = [
    ('deep-learning/gradient-accumulation-and-effective-batch', 'deep-learning/adamw-decay-groups-and-update-indexed-schedules'),
    ('deep-learning/checkpoint-resume-state', 'deep-learning/early-stopping-best-state-and-seed-variance'),
    ('deep-learning/mixed-precision-scaling-and-gradient-clipping', 'deep-learning/adamw-decay-groups-and-update-indexed-schedules'),
    ('deep-learning/receipt-training-memory-project', 'deep-learning/receipt-optimizer-selection-project'),
    ('deep-learning/receipt-image-quality-project', 'deep-learning/receipt-optimizer-selection-project'),
    ('deep-learning/augmentation-leakage-boundary', 'deep-learning/fgsm-input-scale-and-perturbation-threat-model'),
    ('deep-learning/temperature-scaling-and-selective-risk', 'deep-learning/receipt-perturbation-stress-project'),
    ('deep-learning/receipt-confidence-audit-project', 'deep-learning/receipt-perturbation-stress-project'),
    ('deep-learning/occlusion-attribution-and-sanity-checks', 'deep-learning/fgsm-input-scale-and-perturbation-threat-model'),
    ('deep-learning/receipt-edge-model-release-project', 'deep-learning/receipt-perturbation-stress-project'),
    ('deep-learning/deep-learning-tutorial', 'deep-learning/receipt-perturbation-stress-project'),
]

if __name__ == '__main__':
    publish(LESSONS, (OPTIMIZATION, ROBUSTNESS), CROSSLINKS,
            'aitrove-deep-learning-optimization-robustness-import-20261006.json',
            7890, subject='deep-learning')
