"""Add distributed-training and decision-confidence paths."""
from de_batch_publisher import publish

DISTRIBUTED = 'Distributed training and recovery'
CONFIDENCE = 'Confidence, abstention and evidence checks'
LESSONS = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    assert len(sections) == 5
    LESSONS.append(dict(path='deep-learning/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add('distributed-sampler-tail-and-global-loss-weighting',
    'Distributed sampler tails and global loss weighting',
    'Data-parallel workers must agree on which examples count and on the denominator used for one optimizer update; an even number of steps alone does not guarantee that.', [
    ('Count sampled identities before scaling', 'A distributed sampler partitions dataset indices across ranks. When the dataset length is not divisible by worker count, one policy repeats indices to equalize shard lengths; another drops a tail. With 47 unique receipts and three workers, padding to 48 slots repeats one receipt. That extra slot changes the training population unless it is explicitly masked or accepted as the sampling policy. Audit unique identities, duplicate identities and omitted identities per epoch. [[deep-learning/batching-and-class-sampling|Sampling choices]] can outweigh a small optimizer change.'),
    ('Refresh order every epoch', 'A distributed sampler seeded once can generate the same shuffled order each epoch unless its epoch value is advanced before the loader iterator is created. The epoch value must be the same on all ranks. If one worker skips an epoch or has a different dataset manifest, ranks may see different step counts and collective communication can hang. Log world size, rank, manifest hash, sampler seed, epoch and accepted-example count. A successful first epoch does not prove that later epochs reshuffle.'),
    ('Match the global denominator', 'A conventional data-parallel reducer averages gradients across workers. If all ranks have the same local batch size and each computes a local mean, that average is the global example mean. If rank zero has three examples while rank one has one, averaging their local means gives each rank equal weight, not each example. For a sample-averaged loss, each rank should contribute its local loss sum multiplied by world size and divided by the global accepted-example count before the gradient average. Agree on any sampler duplicates and ignored labels first. [[deep-learning/gradient-accumulation-and-effective-batch|Effective-batch accounting]] extends across ranks.'),
    ('Handle uneven work deliberately', 'A worker that runs out of data earlier can leave peers waiting at an all-reduce. Either construct equal work with a documented duplicate or drop policy, or use a supported uneven-input join mechanism with a stated gradient-weight convention. Do not let a broad exception handler swallow an exhausted-loader event while other ranks continue. For validation, avoid padding duplicates in the metric denominator; gather predictions with stable example identities and deduplicate before calculating reported rates.'),
    ('Prove parity on a tiny batch', 'Copy one model to two simulated workers. Backpropagate four examples as one batch, then split them three and one, apply the distributed scaling rule and average worker gradients. Compare every parameter gradient before stepping. Repeat with a zero-valid-target rank, a short final step and a sampler epoch change. The code example below audits sampler slots; the paired project performs the gradient comparison. A low training loss alone cannot reveal a wrong denominator.')],
    '''from collections import Counter
from torch.utils.data import DistributedSampler, TensorDataset
import torch

receipt_features = torch.arange(47, dtype=torch.float32).unsqueeze(1)
receipt_dataset = TensorDataset(receipt_features)
worker_count = 3
samplers = [DistributedSampler(receipt_dataset, num_replicas=worker_count,
                               rank=worker_rank, shuffle=True, seed=71,
                               drop_last=False)
            for worker_rank in range(worker_count)]

for sampler in samplers:
    sampler.set_epoch(2)
second_epoch_slots = [receipt_id for sampler in samplers
                      for receipt_id in sampler]
slot_counts = Counter(second_epoch_slots)
assert len(second_epoch_slots) == 48
assert len(slot_counts) == 47
assert sum(count - 1 for count in slot_counts.values()) == 1

for sampler in samplers:
    sampler.set_epoch(3)
third_epoch_slots = [receipt_id for sampler in samplers
                     for receipt_id in sampler]
assert second_epoch_slots != third_epoch_slots''',
    'Data parallelism replicates model parameters and optimizer state on each worker. For P parameters, gradient synchronization communicates on the order of P values per update, although bucket overlap and network topology affect wall time. Sampler bookkeeping is cheap relative to training, but repeated tail examples alter the effective data weights. Scaling by the wrong denominator can be fast and still train a different objective.',
    ['Do not assume a non-divisible dataset is partitioned without duplicates.', 'Do not advance the sampler seed independently on each worker.', 'Do not average unequal local means when the intended unit is one accepted example.'],
    ['deep-learning/batching-and-class-sampling', 'deep-learning/gradient-accumulation-and-effective-batch', 'deep-learning/train-eval-validation-loop', 'deep-learning/distributed-checkpoint-manifest-and-resume', 'deep-learning/receipt-multiworker-parity-project'], DISTRIBUTED)

add('distributed-checkpoint-manifest-and-resume',
    'Distributed checkpoint manifests and coherent resume',
    'A distributed checkpoint is complete only when every required shard and the shared training position belong to the same generation and are durably visible.', [
    ('Name one update boundary', 'Stop at an optimizer-step boundary and assign a generation ID. Record model parameters and buffers, optimizer moments, scheduler and scaler state, completed update number, sampler epoch and next data position. If a save begins between accumulated microbatches, the checkpoint also needs partial gradients and accepted-example counts, or it cannot resume the same update. Most systems choose a clean step boundary instead. [[deep-learning/checkpoint-resume-state|Single-process resume state]] provides the base inventory.'),
    ('Stage shards before advertisement', 'Each worker writes a new shard under a generation-specific staging name, syncs it and reports a checksum and size. A coordinator writes a manifest only after every expected shard is present and verified, then atomically advertises that generation as the latest complete one. A crash during shard write should leave the previous complete generation discoverable. A filename that exists is not sufficient evidence; it can contain a partial write or belong to a different run.'),
    ('Tie the manifest to data order', 'Store the dataset manifest hash, number of ranks, sampler seed and epoch with the checkpoint. If a resumed job changes rank count, sharding and sampler order may change; the model weights can load while the next examples differ. Some checkpoint formats can reshard model and optimizer state, but that does not reconstruct an identical data stream automatically. Define whether the goal is exact update replay or a statistically valid continuation and test the appropriate claim.'),
    ('Coordinate every rank', 'The coordinator should not publish a pointer while another rank is still writing. A barrier or explicit acknowledgments must cover data durability as well as process arrival. On restart, all workers read the same manifest and reject missing or mismatched shards before any rank enters training collectives. If one rank loads generation 83 while another loads 84, synchronized gradients cannot repair their inconsistent optimizer moments. [[deep-learning/distributed-sampler-tail-and-global-loss-weighting|Sampler accounting]] must agree too.'),
    ('Test failure injection', 'Kill one worker after it creates half a shard, kill the coordinator before pointer publication, then kill it immediately after publication. In the first two cases, readers should select the previous complete generation; in the third, they should select the new one only when all checksums pass. Compare the first resumed fixed-batch update with an uninterrupted reference at the same rank count. The code below illustrates the coordinator-side commit; production workers must supply durable shard acknowledgments.')],
    '''import hashlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

def publish_generation(checkpoint_root: Path, generation: int,
                       shard_payloads: dict[int, bytes], expected_ranks: int) -> None:
    if set(shard_payloads) != set(range(expected_ranks)):
        raise ValueError("incomplete worker generation")
    generation_dir = checkpoint_root / f"generation-{generation}"
    generation_dir.mkdir()
    shard_manifest = []
    for worker_rank, payload in sorted(shard_payloads.items()):
        shard_name = f"rank-{worker_rank}.bin"
        shard_path = generation_dir / shard_name
        with shard_path.open("wb") as shard_file:
            shard_file.write(payload)
            shard_file.flush()
            os.fsync(shard_file.fileno())
        shard_manifest.append({"rank": worker_rank, "name": shard_name,
                               "sha256": hashlib.sha256(payload).hexdigest()})
    manifest = {"generation": generation, "rank_count": expected_ranks,
                "shards": shard_manifest}
    staged_pointer = checkpoint_root / "latest.pending"
    with staged_pointer.open("w", encoding="utf-8") as pointer_file:
        json.dump(manifest, pointer_file)
        pointer_file.flush()
        os.fsync(pointer_file.fileno())
    os.replace(staged_pointer, checkpoint_root / "latest.json")

with TemporaryDirectory() as scratch_directory:
    checkpoint_root = Path(scratch_directory)
    publish_generation(checkpoint_root, 83, {0: b"rank-zero", 1: b"rank-one"}, 2)
    restored_manifest = json.loads((checkpoint_root / "latest.json").read_text())
    assert len(restored_manifest["shards"]) == 2''',
    'A checkpoint stores parameters, buffers and optimizer state; adaptive optimizers can require several times the parameter bytes. Sharded writing distributes I/O but adds coordination and checksum work proportional to shard size. The example uses fsync on files and an atomic pointer replacement; a real durable filesystem may also require directory syncing and an object-store-specific commit protocol. Profile save stalls and retain at least one previous complete generation.',
    ['Do not advertise a generation before every shard is durable and checked.', 'Do not call weights-only loading an exact optimizer resume.', 'Do not assume changing rank count preserves the same sampler order.'],
    ['deep-learning/checkpoint-resume-state', 'deep-learning/distributed-sampler-tail-and-global-loss-weighting', 'deep-learning/gradient-accumulation-and-effective-batch', 'deep-learning/mixed-precision-scaling-and-gradient-clipping', 'deep-learning/receipt-multiworker-parity-project'], DISTRIBUTED)

add('receipt-multiworker-parity-project',
    'Project: prove multiworker receipt-training parity',
    'Move a receipt-quality classifier from one worker to two while auditing duplicated sampler slots, unequal local batches, checkpoint recovery and metric denominators.', [
    ('Pin a one-worker reference', 'Split receipt identities before any augmentation. Record the label map, model revision, random seeds, optimizer, precision and accepted examples per update. Train a tiny deterministic batch in full precision and save its gradients before stepping. Then make two model copies for a three-plus-one split; the global gradient should match the one-worker mean within numerical tolerance. [[deep-learning/gradient-accumulation-and-effective-batch|The effective-batch rule]] is the reference, not the number of loader iterations.'),
    ('Audit the sampler epoch', 'Use 47 receipt identities across three simulated ranks and show that padding to 48 slots repeats one identity. Decide whether training accepts that duplicate or uses a masked tail. Call set_epoch consistently on each rank, compare two epoch orders and log unique IDs seen. For validation, gather predictions with receipt IDs and count each identity once. [[deep-learning/distributed-sampler-tail-and-global-loss-weighting|The sampler lesson]] gives the audit query.'),
    ('Execute a real two-worker smoke test', 'On a suitable multi-device runner, initialize a process group, put one model replica on each device and wrap it for synchronous gradient reduction. Give every rank the same number of update boundaries. Compare first-step gradients and parameters with the one-worker reference, then run an epoch and report accepted-example counts by rank. This page’s executable snippet simulates the gradient algebra on one process; it does not claim to start a distributed job.'),
    ('Interrupt and recover', 'Save at a completed update with two worker shards and a manifest. Kill one rank halfway through the next save; restart from the last advertised generation and check the first resumed fixed-batch update. Change world size in a separate experiment and state the resulting data-order difference even if model state loads. [[deep-learning/distributed-checkpoint-manifest-and-resume|The manifest rule]] decides which generation is safe to use.'),
    ('Publish the measured trade', 'Compare one-worker and two-worker examples per second, synchronization time, peak memory, class-specific validation results and the number of sampler duplicates. Submit the small gradient-parity assertion, a duplicate-ID report, one injected-failure trace and a deduplicated validation metric. A faster run that silently doubles one rare-class receipt or weights the short rank equally with the long rank has not met the project contract.')],
    '''import copy
import torch
from torch import nn

torch.manual_seed(37)
reference_model = nn.Linear(3, 2)
worker_models = [copy.deepcopy(reference_model) for _ in range(2)]
receipt_features = torch.tensor([[0.7, 0.2, 0.1], [0.1, 0.8, 0.1],
                                 [0.2, 0.3, 0.5], [0.6, 0.1, 0.3]])
quality_labels = torch.tensor([0, 1, 1, 0])

reference_loss = nn.functional.cross_entropy(
    reference_model(receipt_features), quality_labels)
reference_loss.backward()
world_size = len(worker_models)
accepted_count = quality_labels.numel()
for worker_model, (first, last) in zip(worker_models, ((0, 3), (3, 4))):
    local_loss_sum = nn.functional.cross_entropy(
        worker_model(receipt_features[first:last]), quality_labels[first:last],
        reduction="sum")
    (local_loss_sum * world_size / accepted_count).backward()

for parameter_index, reference_parameter in enumerate(reference_model.parameters()):
    worker_parameters = [list(worker.parameters())[parameter_index]
                         for worker in worker_models]
    averaged_worker_gradient = sum(parameter.grad for parameter in worker_parameters) / world_size
    torch.testing.assert_close(averaged_worker_gradient, reference_parameter.grad,
                               rtol=1e-6, atol=1e-7)''',
    'Each worker stores a full model and optimizer copy; activation memory follows its local microbatch. Synchronization transfers gradients of all parameters per update, and small batches can be communication-bound. The one-process parity check costs two extra model copies but catches loss-weight mistakes before a multi-device run. Validation deduplication uses stable receipt IDs and adds memory proportional to the number of evaluated examples or a sorted streaming merge.',
    ['Do not report the simulated gradient test as a completed multi-device run.', 'Do not divide each rank’s unequal-size mean by worker count and call it a global example mean.', 'Do not count padded sampler duplicates as independent validation receipts.'],
    ['deep-learning/distributed-sampler-tail-and-global-loss-weighting', 'deep-learning/distributed-checkpoint-manifest-and-resume', 'deep-learning/gradient-accumulation-and-effective-batch', 'deep-learning/receipt-training-memory-project', 'deep-learning/receipt-image-quality-project'], DISTRIBUTED, True)

add('temperature-scaling-and-selective-risk',
    'Temperature scaling and selective risk',
    'A classifier can rank classes correctly while expressing unsafe confidence; a held-out temperature and an explicit abstention rule address different parts of that problem.', [
    ('Fit confidence after the model', 'Freeze the trained classifier and collect logits and labels from a separate calibration split. Divide every class logit by one positive temperature and choose the temperature that reduces calibration negative log likelihood. This one-parameter map changes probability sharpness while preserving each example’s class ordering. It cannot fix a wrong top class or a missing input feature. [[deep-learning/logits-loss-gradient|Logits]] must be saved before softmax so the map is applied in the intended place.'),
    ('Keep splits independent', 'The calibration split cannot be the same population used to fit classifier weights if the goal is out-of-sample confidence. Avoid tuning the temperature repeatedly on the final test set, and group images from one physical receipt on one side of each split. A new acquisition device may need a fresh calibration study, but per-device fits require enough observations and a clear fallback. [[deep-learning/staged-unfreezing-and-domain-shift-audit|Domain-shift auditing]] should report probability quality by source, not just average accuracy.'),
    ('Measure what a probability means', 'Compare mean confidence with observed correctness in fixed or adaptive bins, and report the sample count per bin. A small expected calibration error can hide rare high-confidence failures because binning and class balance matter. Use negative log likelihood and a proper score alongside diagrams, then inspect high-impact slices. The temperature is positive; parameterizing its logarithm keeps optimization in the valid range. Fit on frozen logits, not on a model that continues to change during calibration.'),
    ('Add an abstention policy', 'After calibration, accept a model answer only when its maximum probability clears a selected threshold; otherwise send it for manual review or an alternate workflow. Coverage is the share accepted. Selective risk is the error fraction among accepted cases. Raising the threshold usually lowers coverage but does not guarantee lower risk in every subgroup. Choose the threshold on validation under a stated review-capacity or error-budget rule, then report both coverage and risk on untouched data.'),
    ('Test the operating limit', 'Report class-specific coverage, wrong high-confidence predictions and the number of manual reviews per hundred receipts. On an all-blurry batch, a high-confidence model can still be wrong; calibration does not certify that uncertainty reflects all unfamiliar inputs. Keep the model revision, temperature, threshold and label map together. The serving system should reject nonfinite logits and missing preprocessing fields before confidence calculation. [[deep-learning/inference-schema-and-latency|Inference contracts]] protect the output decision.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

calibration_logits = torch.tensor([[2.7, 0.4, -0.8], [0.3, 2.2, -0.2],
                                   [1.8, 1.2, -0.5], [-0.2, 0.6, 1.9],
                                   [1.4, 0.7, -0.3], [0.5, 1.3, 0.2]])
calibration_labels = torch.tensor([0, 1, 1, 2, 0, 1])
log_temperature = nn.Parameter(torch.tensor(0.0))
temperature_optimizer = torch.optim.Adam([log_temperature], lr=0.047)
for _ in range(83):
    temperature_optimizer.zero_grad(set_to_none=True)
    calibrated_loss = functional.cross_entropy(
        calibration_logits / log_temperature.exp(), calibration_labels)
    calibrated_loss.backward()
    temperature_optimizer.step()

temperature = log_temperature.detach().exp()
calibrated_probabilities = functional.softmax(
    calibration_logits / temperature, dim=1)
assert temperature > 0
assert torch.equal(calibration_logits.argmax(dim=1),
                   calibrated_probabilities.argmax(dim=1))
assert torch.isfinite(calibrated_probabilities).all()''',
    'Fitting one temperature costs repeated softmax and loss evaluations over the calibration logits, roughly O(iterations × cases × classes), and requires storing logits and labels. Serving adds one scalar division and softmax per prediction. Abstention can reduce automated errors at the price of review workload; that workload is a system cost and must be measured at the selected coverage. This tiny six-case fit illustrates mechanics, not a reliable production calibration.',
    ['Do not fit confidence on the untouched final test set.', 'Do not expect temperature scaling to change the predicted top class.', 'Do not quote selective risk without coverage and subgroup counts.'],
    ['deep-learning/logits-loss-gradient', 'deep-learning/train-eval-validation-loop', 'deep-learning/staged-unfreezing-and-domain-shift-audit', 'deep-learning/inference-schema-and-latency', 'deep-learning/receipt-confidence-audit-project'], CONFIDENCE)

add('occlusion-attribution-and-sanity-checks',
    'Occlusion attribution and explanation sanity checks',
    'Replacing one input region and measuring a score change can locate model sensitivity, but the map depends on the replacement and does not prove causal human reasoning.', [
    ('Define the score and replacement', 'Fix a target class logit, then replace one image patch at a time with a stated baseline such as a neutral local intensity. The difference between the original and altered logit is a patch sensitivity under that intervention. A zero patch on a white receipt creates an artificial black square; a local-median patch has a different meaning. Use more than one plausible baseline and note where results disagree. [[deep-learning/convolution-output-geometry-and-receptive-field|Spatial geometry]] determines which input region maps to a feature response.'),
    ('Keep preprocessing identical', 'The image supplied to an explanation probe must pass through the same resize, normalization and channel order as ordinary inference. Apply a replacement in a declared space: raw pixels before normalization or normalized tensors after it. Mixing those spaces can create an out-of-range patch and a large score difference unrelated to the model’s ordinary evidence. Use eval mode and a frozen model revision. Log the exact target class; a map for the currently predicted class can change target when the patch is removed.'),
    ('Inspect rather than certify', 'A bright patch map may overlap the printed receipt defect, yet that alone does not establish why the classifier made its decision. Test an untrained or randomized-weight model with the same probe, compare maps after controlled input changes, and measure whether removing top-ranked patches changes the target score more than removing equally sized random patches. These tests may expose maps that mainly reflect edges or preprocessing. [[deep-learning/receipt-defect-localization-project|A localization label]] provides independent evidence for overlap checks.'),
    ('Budget the probe', 'For an image partitioned into R patches, a simple occlusion map uses one original forward pass plus R altered forward passes. That can be expensive for large images or an online endpoint. Batch altered inputs if memory permits, and run the full audit offline if it would violate serving latency. A coarse patch grid is cheaper but can miss small evidence; overlapping small patches cost more and spread one pixel across several interventions. Report patch size and stride with every map.'),
    ('Use failure slices', 'Check low-contrast, edge-truncated and correctly classified receipts separately from high-confidence mistakes. A map that follows a scanner border instead of text may reveal shortcut learning. If removing a region flips the class, record the changed score and whether the altered image remains plausible. Do not turn an attractive heatmap into a user-facing claim of proof. [[deep-learning/temperature-scaling-and-selective-risk|Confidence]] and attribution answer different questions and both need held-out checks.')],
    '''import torch
from torch import nn

torch.manual_seed(89)
receipt_patch = torch.tensor([[[[0.9, 0.8, 0.7, 0.9],
                                [0.9, 0.2, 0.3, 0.8],
                                [0.8, 0.1, 0.2, 0.7],
                                [0.9, 0.8, 0.9, 0.8]]]])
quality_model = nn.Sequential(nn.Flatten(), nn.Linear(16, 2)).eval()
randomized_model = nn.Sequential(nn.Flatten(), nn.Linear(16, 2)).eval()

def patch_sensitivity(model: nn.Module, image: torch.Tensor,
                      target_class: int, replacement: float) -> torch.Tensor:
    with torch.inference_mode():
        original_score = model(image)[0, target_class]
        score_changes = torch.zeros(2, 2)
        for patch_row in range(2):
            for patch_column in range(2):
                altered = image.clone()
                top, left = patch_row * 2, patch_column * 2
                altered[:, :, top:top + 2, left:left + 2] = replacement
                score_changes[patch_row, patch_column] = (
                    original_score - model(altered)[0, target_class])
    return score_changes

attribution = patch_sensitivity(quality_model, receipt_patch, 1, 0.8)
randomized_attribution = patch_sensitivity(randomized_model, receipt_patch, 1, 0.8)
parameter_sensitivity = (attribution - randomized_attribution).abs().mean()
assert attribution.shape == (2, 2)
assert torch.isfinite(parameter_sensitivity)''',
    'A naive patch probe requires O(R × F) model work for R regions and one forward cost F, plus storage for a small map; batching probes trades memory for throughput. Comparison with a randomized model roughly doubles that work. The interpretation also has a data cost: patch replacement can create unrealistic images. Measure probe stability under several baselines and keep ordinary inference independent of the optional explanation pass.',
    ['Do not call a sensitivity map causal proof of a human-readable reason.', 'Do not replace pixels in a different normalization space than the model expects.', 'Do not judge a map only by visual appeal without model and input counterfactuals.'],
    ['deep-learning/convolution-output-geometry-and-receptive-field', 'deep-learning/receipt-defect-localization-project', 'deep-learning/temperature-scaling-and-selective-risk', 'deep-learning/frozen-features-versus-fine-tuning', 'deep-learning/receipt-confidence-audit-project'], CONFIDENCE)

add('receipt-confidence-audit-project',
    'Project: audit receipt confidence and review handoff',
    'Calibrate a receipt-quality classifier, choose an abstention threshold under a review budget and test whether its visual sensitivity follows receipt evidence.', [
    ('Freeze the evaluation populations', 'Split by physical receipt before producing multiple crops or captures. Keep training, calibration, threshold-selection and final test populations separate. Include readable, blurred and cut-off receipts from more than one capture device. Record class counts and device counts; a good aggregate score can hide a small device group with dangerous confident mistakes. [[deep-learning/receipt-image-quality-project|The quality classifier]] supplies logits while this project evaluates decisions made from them.'),
    ('Fit one positive temperature', 'Freeze model weights and fit a single log-temperature parameter on calibration logits only. Verify top-class identities do not change and compare negative log likelihood, reliability bins and high-confidence error counts before and after. A six-example demonstration is not enough to establish calibration; use a population with enough cases in each important slice. [[deep-learning/temperature-scaling-and-selective-risk|Temperature scaling]] adjusts sharpness, not classification accuracy.'),
    ('Choose a review threshold', 'On a separate threshold-selection group, evaluate a grid of maximum-probability cutoffs. Choose the lowest cutoff meeting a predeclared accepted-case error target while keeping review volume within staffed capacity. On the final test population report coverage, selective error, class recall and manual reviews per hundred receipts. If no cutoff meets both constraints, do not invent a number; return the capacity or model-quality conflict as the project result.'),
    ('Audit image evidence', 'Probe a sample of confident correct and confident wrong receipts with two plausible occlusion baselines. Measure target-logit change when replacing defect regions and equally sized background regions. Repeat after randomizing model weights as a sanity check. A heatmap that looks aligned with text but barely changes when weights change is not adequate evidence. [[deep-learning/occlusion-attribution-and-sanity-checks|The attribution protocol]] specifies patch size, target logit and baseline.'),
    ('Ship a reversible decision artifact', 'Package model weights, preprocessing, class map, temperature, review threshold, model revision and a fallback for nonfinite logits or missing image fields. Reload the package in a clean process and compare fixed-batch decisions. Monitor coverage, review queue, high-confidence wrong cases and source-device mix. The outcome may be a request for better labels or a larger review team rather than an automatic release; preserve the previous artifact until the new policy meets the stated limits.')],
    '''import torch
from torch.nn import functional as functional

quality_logits = torch.tensor([[2.8, 0.3, -0.4], [0.5, 2.1, 0.1],
                               [0.9, 1.1, 0.3], [0.2, 0.8, 1.7],
                               [1.6, 0.9, 0.1], [0.3, 1.2, 0.6]])
quality_labels = torch.tensor([0, 1, 2, 2, 0, 1])
saved_temperature = torch.tensor(1.43)
probabilities = functional.softmax(quality_logits / saved_temperature, dim=1)
confidence, predictions = probabilities.max(dim=1)
wrong = predictions.ne(quality_labels)

def review_metrics(minimum_confidence: float) -> tuple[float, float, int]:
    accepted = confidence >= minimum_confidence
    accepted_count = int(accepted.sum())
    if accepted_count == 0:
        return 0.0, float("nan"), len(confidence)
    coverage = accepted_count / len(confidence)
    selective_error = float(wrong[accepted].float().mean())
    review_count = len(confidence) - accepted_count
    return coverage, selective_error, review_count

candidate_policies = {cutoff: review_metrics(cutoff)
                      for cutoff in (0.37, 0.53, 0.71)}
assert all(0 <= coverage <= 1 for coverage, _, _ in candidate_policies.values())
assert all(0 <= count <= 6 for _, _, count in candidate_policies.values())''',
    'Temperature fitting is cheap compared with classifier training, and serving adds one division and softmax. Review workload can dominate operating cost: report accepted and routed counts at real traffic volume. Occlusion probes multiply inference by the number of tested patches, so keep them in offline audit or an explicitly budgeted diagnostic path. The six-case code illustrates metric definitions and does not justify a production cutoff.',
    ['Do not choose and report a cutoff on the same final test group.', 'Do not report a low selective error while concealing near-zero coverage.', 'Do not treat a visually plausible attribution map as a substitute for held-out decision checks.'],
    ['deep-learning/temperature-scaling-and-selective-risk', 'deep-learning/occlusion-attribution-and-sanity-checks', 'deep-learning/receipt-image-quality-project', 'deep-learning/staged-unfreezing-and-domain-shift-audit', 'deep-learning/inference-schema-and-latency'], CONFIDENCE, True)

CROSSLINKS = [
    ('deep-learning/batching-and-class-sampling', 'deep-learning/distributed-sampler-tail-and-global-loss-weighting'),
    ('deep-learning/gradient-accumulation-and-effective-batch', 'deep-learning/distributed-sampler-tail-and-global-loss-weighting'),
    ('deep-learning/checkpoint-resume-state', 'deep-learning/distributed-checkpoint-manifest-and-resume'),
    ('deep-learning/mixed-precision-scaling-and-gradient-clipping', 'deep-learning/distributed-checkpoint-manifest-and-resume'),
    ('deep-learning/receipt-training-memory-project', 'deep-learning/receipt-multiworker-parity-project'),
    ('deep-learning/receipt-image-quality-project', 'deep-learning/receipt-multiworker-parity-project'),
    ('deep-learning/logits-loss-gradient', 'deep-learning/temperature-scaling-and-selective-risk'),
    ('deep-learning/train-eval-validation-loop', 'deep-learning/temperature-scaling-and-selective-risk'),
    ('deep-learning/staged-unfreezing-and-domain-shift-audit', 'deep-learning/receipt-confidence-audit-project'),
    ('deep-learning/receipt-defect-localization-project', 'deep-learning/occlusion-attribution-and-sanity-checks'),
    ('deep-learning/inference-schema-and-latency', 'deep-learning/receipt-confidence-audit-project'),
    ('deep-learning/deep-learning-tutorial', 'deep-learning/receipt-confidence-audit-project'),
]

if __name__ == '__main__':
    publish(LESSONS, (DISTRIBUTED, CONFIDENCE), CROSSLINKS,
            'aitrove-deep-learning-distributed-confidence-import-20261006.json',
            7850, subject='deep-learning')
