"""Add pixel-mask learning and activation-memory accounting paths."""
from de_batch_publisher import publish

SEGMENTATION = 'Pixel-level defect learning and mask audits'
MEMORY = 'Activation recomputation and memory measurement'
LESSONS = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    assert len(sections) == 5
    LESSONS.append(dict(path='deep-learning/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add('segmentation-mask-alignment-and-ignore-pixels',
    'Segmentation mask alignment and ignored pixels',
    'A pixel classifier is trained on image–mask geometry; a wrong interpolation rule or ignored-label denominator can turn accurate code into a different task.', [
    ('Name the mask classes', 'For receipt defects, one mask might distinguish ordinary paper, clipped edge and obscuring fold. Record integer IDs, mutually exclusive or overlapping semantics, and an ignore value for pixels whose annotation cannot be trusted. A mutually exclusive target with one ID per pixel belongs with per-pixel multiclass logits and cross entropy. Independent overlapping defect layers require a different multi-label loss and threshold policy. Do not switch between these representations without changing the target and metrics. [[deep-learning/logits-loss-gradient|The logits rule]] applies at every pixel, not only once per image.'),
    ('Keep geometric transforms paired', 'A crop, horizontal shift, perspective transform or resize applied to the image must apply the same geometric mapping to the mask. Image intensity can be interpolated smoothly; class IDs cannot. Use nearest-neighbor label interpolation and verify that resized masks contain only known IDs and the ignore value. An image resized independently of its mask may still have the expected width and height while every defect boundary has moved. Save several transformed image–mask overlays at fixed seeds. [[deep-learning/augmentation-leakage-boundary|Split identities]] before generating augmented pairs.'),
    ('Handle unknown borders explicitly', 'When a crop or warp introduces pixels outside the annotated source, decide whether they become background or ignored; the default should not silently invent negative evidence. In the example, 255 means ignored. A cross-entropy implementation excludes ignored targets from the loss denominator when class-index targets are used. Count accepted pixels per batch and reject a batch with no accepted pixels rather than dividing by zero or learning from an empty annotation. For rare clipped edges, report positive-pixel and positive-image counts separately.'),
    ('Align model output resolution', 'A model may emit logits at one-quarter of input resolution. Either upsample logits to the mask grid with a documented continuous interpolation rule, or reduce the mask using a label-preserving policy that does not erase narrow defects. These two choices are not interchangeable for a one-pixel clipped edge. Record output stride, final-grid size and any tile padding. [[deep-learning/convolution-output-geometry-and-receptive-field|Convolution geometry]] predicts the feature-map shape, but visual overlays verify whether the physical boundary still lines up.'),
    ('Verify the full target path', 'Run a tiny batch through decode, transform, model, loss and metric computation. Assert image–mask spatial dimensions, allowed mask values, finite loss and unchanged ignored-pixel count after transforms that should preserve area. Save a fixed batch to compare after library or preprocessing upgrades. A low training loss with most pixels marked background may say little about the defect class. [[deep-learning/dice-iou-empty-mask-and-threshold-policy|The metric policy]] must therefore be fixed separately from the loss.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

receipt_image = torch.arange(16, dtype=torch.float32).view(1, 1, 4, 4) / 15
defect_mask = torch.tensor([[[0, 0, 1, 1], [0, 2, 2, 1],
                             [0, 2, 255, 0], [0, 0, 0, 0]]])
resized_image = functional.interpolate(receipt_image, size=(8, 8),
                                       mode="bilinear", align_corners=False)
resized_mask = functional.interpolate(defect_mask.unsqueeze(1).float(),
                                      size=(8, 8), mode="nearest-exact").squeeze(1).long()
segmentation_head = nn.Conv2d(1, 3, kernel_size=1)
pixel_logits = segmentation_head(resized_image)
valid_count = int(resized_mask.ne(255).sum())
assert valid_count > 0
pixel_loss = functional.cross_entropy(pixel_logits, resized_mask, ignore_index=255)
assert set(resized_mask.unique().tolist()) <= {0, 1, 2, 255}
assert pixel_logits.shape == (1, 3, 8, 8)
assert torch.isfinite(pixel_loss)''',
    'Image and mask transforms cost O(BHW) for B images of height H and width W, while the model usually dominates training compute. Per-pixel logits and gradients occupy O(BCHW) memory for C classes at output resolution. Upsampling logits to a large mask grid can raise activation memory sharply; downsampling masks can erase small defects. The example uses a tiny one-by-one head solely to test the label path. Measure accepted-pixel counts and peak memory at production image size.',
    ['Do not bilinearly interpolate integer class IDs.', 'Do not treat unannotated pixels as confirmed background without an annotation rule.', 'Do not accept matching tensor shapes as proof that image and mask geometry align.'],
    ['deep-learning/convolution-output-geometry-and-receptive-field', 'deep-learning/augmentation-leakage-boundary', 'deep-learning/dice-iou-empty-mask-and-threshold-policy', 'deep-learning/receipt-defect-segmentation-project', 'deep-learning/receipt-defect-localization-project'], SEGMENTATION)

add('dice-iou-empty-mask-and-threshold-policy',
    'Dice, IoU, empty masks and threshold policy',
    'Pixel overlap scores need a declared treatment for ignored pixels, absent classes and probability thresholds before they can compare segmentation checkpoints.', [
    ('Count intersection and union on valid pixels', 'For a chosen defect class, true positives are pixels marked defect in both prediction and reviewed mask; false positives are predicted defect on reviewed nondefect pixels; false negatives are missed reviewed defect pixels. IoU divides true positives by their union. Dice divides twice the intersection by the total predicted and reviewed positives. Exclude ignored pixels from every count, including predicted positives. Aggregate counts across images before computing a micro score if the intended unit is a pixel, and report per-image or per-class scores separately.'),
    ('Declare the both-empty case', 'When neither prediction nor target contains a defect, the denominator of both IoU and Dice is zero. Returning one rewards easy empty images; returning zero penalizes correct absence; excluding the case changes the evaluated population. Choose the policy in advance and report how many images were both empty. The code returns no overlap score for both-empty images and keeps their count. For a defect detector, an absence false-positive rate is often more informative than assigning a perfect overlap to empty images. [[deep-learning/receipt-defect-segmentation-project|The project]] reports both.'),
    ('Select thresholds away from final test', 'For a binary or multi-label mask, a probability threshold turns continuous output into a hard mask. Lowering it usually raises recall and false positives. Select one policy on a development group, then freeze it before the final physical-receipt holdout. A multiclass argmax has no independent per-class threshold unless the decision rule is changed. Count tiny connected defects separately: an average IoU can be high because large folds are easy while clipped-edge slivers disappear. [[deep-learning/temperature-scaling-and-selective-risk|Confidence calibration]] does not automatically select a pixel mask threshold.'),
    ('Preserve the image-level question', 'A user may care whether any clipped edge is present, not its exact pixel boundary. Derive an image-level detection rule from the mask and report image-level recall and false alerts alongside overlap. Compare output after tile merging and any morphological cleanup, because those operations can remove small islands or create false regions. A model that gains Dice by expanding every defect may inflate false alerts on clean receipts. Keep the postprocessing revision and threshold with the model artifact.'),
    ('Use uncertainty-aware reporting', 'Show raw true-positive, false-positive and false-negative counts by defect and capture device, plus the number of held-out physical receipts. Bootstrap by receipt identity rather than by pixel if an interval is needed, since pixels within one receipt are not independent examples. Do not choose a threshold on the same final test used to report its score. [[deep-learning/segmentation-mask-alignment-and-ignore-pixels|Mask alignment]] is a prerequisite; overlap numbers cannot rescue shifted annotations.')],
    '''def overlap_counts(target, prediction, ignored_value=255):
    if len(target) != len(prediction):
        raise ValueError("mask length mismatch")
    true_positive = false_positive = false_negative = 0
    for target_pixel, predicted_pixel in zip(target, prediction):
        if target_pixel == ignored_value:
            continue
        true_positive += target_pixel == 1 and predicted_pixel == 1
        false_positive += target_pixel != 1 and predicted_pixel == 1
        false_negative += target_pixel == 1 and predicted_pixel != 1
    denominator = true_positive + false_positive + false_negative
    if denominator == 0:
        return {"iou": None, "dice": None, "both_empty": True}
    return {"iou": true_positive / denominator,
            "dice": 2 * true_positive / (2 * true_positive + false_positive + false_negative),
            "both_empty": False}

reviewed_pixels = [0, 1, 1, 0, 255, 0, 0, 0]
predicted_pixels = [0, 1, 0, 0, 1, 0, 0, 0]
result = overlap_counts(reviewed_pixels, predicted_pixels)
assert result == {"iou": 0.5, "dice": 2 / 3, "both_empty": False}''',
    'Counting overlap is O(HW) time and O(1) auxiliary memory for one image if pixels stream through the metric. Storing all probability maps for later threshold sweeps is O(NHW) and can be expensive; accumulate candidate-threshold counts when possible. Per-image IoU and micro-IoU answer different questions because large masks carry more pixels. Rare-class confidence intervals depend on independent receipt counts, not the much larger pixel count.',
    ['Do not silently assign an IoU of one to every both-empty mask.', 'Do not calculate overlap on ignored pixels or on masks with mismatched geometry.', 'Do not choose a threshold after viewing final-test performance.'],
    ['deep-learning/segmentation-mask-alignment-and-ignore-pixels', 'deep-learning/receipt-defect-segmentation-project', 'deep-learning/receipt-defect-localization-project', 'deep-learning/temperature-scaling-and-selective-risk', 'deep-learning/receipt-confidence-audit-project'], SEGMENTATION)

add('receipt-defect-segmentation-project',
    'Project: segment clipped edges and folds on receipts',
    'Train a pixel-level defect model with ignored annotation regions, then prove that mask overlap and image-level alerts survive held-out receipts and full-resolution inference.', [
    ('Prepare paired annotations', 'Collect grayscale receipt images with reviewed masks for background, clipped edge and fold, plus an ignore code for uncertain borders. Split by physical receipt before generating crops and keep annotation versions in the manifest. Audit overlays from multiple capture devices, especially narrow clipped edges near the crop boundary. The tiny model below runs one training step to validate dimensions and ignored-pixel handling; it is not a production architecture. [[deep-learning/segmentation-mask-alignment-and-ignore-pixels|The alignment lesson]] defines the preprocessing contract.'),
    ('Train with explicit pixel accounting', 'Use per-pixel multiclass logits and ignore uncertain pixels in the loss. Count accepted pixels and positive pixels per batch; reject empty-supervision batches. Sample images so rare defect masks are seen without repeating a few physical receipts so often that validation becomes misleading. Keep all geometric image transforms paired with nearest-neighbor mask transforms. Save a fixed image–mask–logit triplet after each code change. A model can lower loss by learning background while missing almost every clipped edge.'),
    ('Validate overlap and detection', 'Choose a development-set checkpoint and any postprocessing threshold before final test. Report per-class Dice and IoU with an explicit both-empty policy, plus image-level clipped-edge recall and false alerts. Preserve counts by device and defect size. Compare to a simple image-level classifier: pixel masks cost annotation and runtime, so they should earn that cost through better localization or decisions. [[deep-learning/dice-iou-empty-mask-and-threshold-policy|The metric lesson]] specifies counts and denominators.'),
    ('Test full-resolution tiles', 'If inference uses overlapping tiles, account for padding, coordinate offsets and merging. A defect split across tile boundaries must not vanish or be double-counted. Compare full-image predictions from tiled and untiled runs where memory allows; inspect seam regions and near-edge masks. Record tile size, overlap, blending and output threshold with the model. Measure p95 end-to-end latency including image decode, tiling and mask assembly, not only the neural forward. [[deep-learning/inference-schema-and-latency|The serving contract]] applies to masks too.'),
    ('Release only with a reversible gate', 'Define minimum clipped-edge image recall, maximum false alerts, per-class overlap floor, review capacity and latency before final test. Export class map, preprocessing, tile policy and ignore-label treatment. Reload a fixed batch in a clean process and compare mask logits. Keep the previous classifier or manual review route if the segmentation candidate misses a gate. Deliver annotated examples, mask-overlap counts and a failure gallery, not a single aggregate score.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

torch.manual_seed(47)
receipt_images = torch.rand(4, 1, 8, 8)
reviewed_masks = torch.zeros(4, 8, 8, dtype=torch.long)
reviewed_masks[:, 2:4, 5:7] = 1
reviewed_masks[:, 5:7, 1:4] = 2
reviewed_masks[:, 0, 0] = 255
model = nn.Sequential(nn.Conv2d(1, 8, 3, padding=1), nn.ReLU(),
                      nn.Conv2d(8, 3, 1))
optimizer = torch.optim.AdamW(model.parameters(), lr=0.0007)
optimizer.zero_grad(set_to_none=True)
logits = model(receipt_images)
assert logits.shape == (4, 3, 8, 8)
assert int(reviewed_masks.ne(255).sum()) == 252
loss = functional.cross_entropy(logits, reviewed_masks, ignore_index=255)
loss.backward()
optimizer.step()
assert torch.isfinite(loss)''',
    'Dense per-pixel logits use O(BCHW) storage and a full-resolution model may need substantially more activation memory than an image classifier. Tiled inference trades peak memory for repeated border compute and merging work; overlapping tiles can increase total pixels processed. Mask annotation and review are material project costs. The toy model has only two convolutions and proves tensor and loss wiring, not accuracy. Benchmark image decode, full-resolution assembly and serving latency on the target runtime.',
    ['Do not claim a high pixel score when clipped-edge image recall is poor.', 'Do not train on masks bilinearly resized into fractional class IDs.', 'Do not evaluate tiled images without checking seams and coordinate restoration.'],
    ['deep-learning/segmentation-mask-alignment-and-ignore-pixels', 'deep-learning/dice-iou-empty-mask-and-threshold-policy', 'deep-learning/receipt-defect-localization-project', 'deep-learning/inference-schema-and-latency', 'deep-learning/receipt-image-quality-project'], SEGMENTATION, True)

add('activation-checkpointing-recompute-and-rng-parity',
    'Activation checkpointing, recomputation and RNG parity',
    'Activation checkpointing saves memory by rerunning a forward segment during backward; it is unrelated to saving training state on disk.', [
    ('Separate two meanings of checkpoint', 'A durable training checkpoint stores model and optimizer state so a process can resume after interruption. Activation checkpointing deliberately avoids retaining selected intermediate tensors from a forward segment, then recomputes them during backward. It trades extra compute for lower saved-activation memory and cannot restore a crashed run. [[deep-learning/checkpoint-resume-state|The resume lesson]] covers the disk artifact. Use distinct names in code and metrics so an operator does not mistake a memory optimization for recovery protection.'),
    ('Choose a pure recomputable segment', 'The wrapped function must produce the same needed values when backward reruns it. Avoid untracked global counters, file writes, mutating batch-normalization state inside a recomputed region, or branches that depend on external state changed between calls. Store input tensors that define the segment; select a block large enough to save meaningful activations but not so large that recomputation dominates latency. The example wraps a simple feed-forward block with dropout and compares gradients against a plain forward under the same seed.'),
    ('Preserve stochastic behavior deliberately', 'Dropout draws random masks. A checkpointed backward needs the same stochastic choices as the original forward for gradient parity, so use an RNG-preservation setting when that parity is required. Saving and restoring RNG state has overhead and can have device-specific limits; do not assume stochastic operators on arbitrary extra devices are automatically handled. Make the checkpoint implementation mode explicit and test fixed-input output and parameter gradients. [[deep-learning/mixed-precision-scaling-and-gradient-clipping|Precision settings]] must also match in the comparison.'),
    ('Measure saved memory and added time', 'On a CUDA device, reset peak statistics immediately before a representative train step and synchronize around timing. Record peak tensor-allocated and allocator-reserved bytes separately. The allocator may reserve blocks beyond live tensors, so a lower allocated peak may not produce a proportional drop in process-visible memory. Run several warm steps with the same batch shape and optimizer state already initialized. [[deep-learning/training-memory-profiler-and-allocator-boundaries|The profiler lesson]] distinguishes these measurements.'),
    ('Check the release claim', 'Compare plain and checkpointed gradients and one optimizer step within a stated numerical tolerance, then evaluate task metrics after equal accepted-example budgets. If memory drops but update time rises enough to miss a training deadline, report that cost. If the larger batch made possible by checkpointing changes the effective optimization, it is a second experiment, not a clean parity test. [[deep-learning/receipt-activation-recompute-project|The project]] measures both memory and model behavior.')],
    '''import torch
from torch import nn
from torch.utils.checkpoint import checkpoint

torch.manual_seed(47)
receipt_block = nn.Sequential(nn.Linear(12, 24), nn.ReLU(),
                              nn.Dropout(0.2), nn.Linear(24, 12))
base_inputs = torch.randn(3, 12)
plain_inputs = base_inputs.clone().requires_grad_(True)
torch.manual_seed(71)
plain_loss = receipt_block(plain_inputs).square().mean()
plain_loss.backward()
plain_gradients = [parameter.grad.clone() for parameter in receipt_block.parameters()]
receipt_block.zero_grad(set_to_none=True)

recomputed_inputs = base_inputs.clone().requires_grad_(True)
torch.manual_seed(71)
recomputed_loss = checkpoint(receipt_block, recomputed_inputs,
                             use_reentrant=False, preserve_rng_state=True).square().mean()
recomputed_loss.backward()
torch.testing.assert_close(plain_loss, recomputed_loss)
torch.testing.assert_close(plain_inputs.grad, recomputed_inputs.grad)
for expected_gradient, parameter in zip(plain_gradients, receipt_block.parameters()):
    torch.testing.assert_close(expected_gradient, parameter.grad)''',
    'Let A be the saved activations of a wrapped block and F its forward cost. Checkpointing can avoid retaining much of A, but typically adds up to another F of recomputation during backward; exact savings depend on segment boundaries and implementation. Model parameters, optimizer moments and input tensors remain. RNG preservation adds bookkeeping. The demonstration checks parity on a small block but cannot quantify memory benefit on a larger network; measure peak allocated bytes and update time on the actual accelerator.',
    ['Do not describe activation recomputation as a recoverable disk checkpoint.', 'Do not checkpoint a function with untracked side effects or changing global state.', 'Do not disable RNG preservation for a stochastic block and still expect exact gradient parity.'],
    ['deep-learning/checkpoint-resume-state', 'deep-learning/training-memory-profiler-and-allocator-boundaries', 'deep-learning/receipt-activation-recompute-project', 'deep-learning/mixed-precision-scaling-and-gradient-clipping', 'deep-learning/receipt-training-memory-project'], MEMORY)

add('training-memory-profiler-and-allocator-boundaries',
    'Training memory profiling and allocator boundaries',
    'A memory report must distinguish live tensors, allocator reservations, optimizer initialization and the peak of the actual forward–backward–step path.', [
    ('Choose the measured boundary', 'State whether the report covers data transfer, forward, backward, gradient clipping, optimizer step or all of them. Adam-like optimizers may allocate moment tensors at the first step, so a warm forward-only profile undercounts a real training update. Measure a representative full update after optimizer state exists. Reset peak statistics at the chosen boundary, synchronize the accelerator before and after timing, and log batch shape, dtype, model revision and gradient-accumulation count. [[deep-learning/gradient-accumulation-and-effective-batch|An effective batch]] may include several microbatches.'),
    ('Separate allocated and reserved bytes', 'Live tensor allocation reports memory currently occupied by tensors; an allocator may reserve extra blocks for reuse. Peak allocated and peak reserved therefore answer different questions. A process can hit a device limit even if a later snapshot shows fewer live tensors. Clearing unused cached blocks does not free memory still held by model weights or activations, and calling a cache-clear operation after every step can reduce throughput. Collect both metrics and compare them with device-level process usage when diagnosing an out-of-memory event.'),
    ('Account for hidden retained graphs', 'Appending loss tensors or outputs that still reference a computation graph to a Python list can keep activations alive across steps. Log scalar values after detaching rather than storing graphs for dashboards. Forward hooks and explanation maps can cause similar retention. A rising allocated baseline over repeated identical steps deserves an object-lifetime audit before changing batch size. The profiler code captures one representative step but also needs a repeated-step trend in production. [[deep-learning/occlusion-attribution-and-sanity-checks|Diagnostic probes]] should not stay attached to the training graph.'),
    ('Compare methods under identical work', 'A fair activation-checkpointing or mixed-precision comparison holds model, microbatch, accepted examples, optimizer state and input size fixed. Then report peak allocated, peak reserved and synchronized update time. Only after that parity check should a larger batch be tested as a separate throughput experiment. Batch size can change normalization statistics, gradient noise and data order. [[deep-learning/activation-checkpointing-recompute-and-rng-parity|Recomputation]] trades time for memory; it does not automatically improve examples per second.'),
    ('Keep device assumptions explicit', 'CUDA counters describe CUDA allocator behavior and do not measure CPU RAM, pinned transfer buffers or every external library allocation. On a CPU-only runner, return an unavailable marker for those GPU counters rather than reporting zero as if no memory were used. Record device, driver/runtime revision and compilation mode. [[deep-learning/receipt-activation-recompute-project|The applied project]] requires measured benefit on a target runner and explains when the technique is worth deploying.')],
    '''import time
import torch
from torch import nn
from torch.nn import functional as functional

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
receipt_model = nn.Sequential(nn.Linear(16, 32), nn.ReLU(), nn.Linear(32, 3)).to(device)
optimizer = torch.optim.AdamW(receipt_model.parameters(), lr=0.0007)
features = torch.randn(6, 16, device=device)
labels = torch.tensor([0, 2, 1, 2, 0, 1], device=device)

def training_update():
    optimizer.zero_grad(set_to_none=True)
    loss = functional.cross_entropy(receipt_model(features), labels)
    loss.backward()
    optimizer.step()
    return float(loss.detach())

training_update()  # initialize optimizer state before the measured step
if device.type == "cuda":
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
started = time.perf_counter()
observed_loss = training_update()
if device.type == "cuda":
    torch.cuda.synchronize()
elapsed_seconds = time.perf_counter() - started
peak_allocated = torch.cuda.max_memory_allocated() if device.type == "cuda" else None
peak_reserved = torch.cuda.max_memory_reserved() if device.type == "cuda" else None
assert elapsed_seconds >= 0 and observed_loss >= 0
assert peak_allocated is None or peak_reserved >= peak_allocated''',
    'Profiling adds small counter and synchronization overhead, but synchronization changes asynchronous execution timing and should be applied consistently across compared runs. A training step is dominated by model work, not counter reads. Peak memory depends on model parameters, gradients, optimizer moments, activations, batch inputs and allocator behavior. The code intentionally returns no GPU-memory number on CPU; it would be false precision to substitute process RAM or zero. Repeat warm measurements and report the distribution, not one favorable run.',
    ['Do not compare a forward-only baseline with a full checkpointed optimizer update.', 'Do not treat allocator-reserved bytes as identical to live-tensor allocation.', 'Do not report zero GPU memory on a CPU-only machine as a device benchmark.'],
    ['deep-learning/activation-checkpointing-recompute-and-rng-parity', 'deep-learning/receipt-activation-recompute-project', 'deep-learning/receipt-training-memory-project', 'deep-learning/mixed-precision-scaling-and-gradient-clipping', 'deep-learning/inference-schema-and-latency'], MEMORY)

add('receipt-activation-recompute-project',
    'Project: measure activation recomputation on receipt training',
    'Checkpoint a receipt encoder block only after proving gradient parity, then report the measured memory saving and update-time cost on the intended training device.', [
    ('Build a fixed training reference', 'Use a receipt-quality model, fixed physical-receipt split, preprocessing and labeled batch. Pin the optimizer and seed, then run one full-precision reference update with no recomputation. Save per-parameter gradients, output logits and next-step weights. Warm the optimizer before memory measurement so moment allocation is not confused with activations. [[deep-learning/receipt-training-memory-project|The earlier memory project]] covers accumulation and precision; this project isolates recomputation.'),
    ('Choose a legal segment', 'Wrap an encoder block whose forward is safe to replay during backward. Inspect dropout and normalization behavior, hooks and counters; side effects inside a replayed function can change state twice. Use an explicit checkpoint variant and RNG policy. Compare plain and recomputed output, input gradient, parameter gradients and one optimizer update within a declared tolerance. If parity fails, stop before reporting any memory result. [[deep-learning/activation-checkpointing-recompute-and-rng-parity|The recomputation lesson]] gives a minimal test.'),
    ('Measure like for like', 'On the intended accelerator, run several warm updates with identical batch size, image shape, dtype and optimizer state. Reset peak counters per step and synchronize timing. Report median update time, peak allocated bytes and peak reserved bytes for both paths; also report device-level process memory when available. The code below gates supplied measurements and does not pretend to collect GPU data in this environment. [[deep-learning/training-memory-profiler-and-allocator-boundaries|The profiler lesson]] explains each counter.'),
    ('Test a second use of saved memory', 'If recomputation frees enough memory for a larger microbatch, treat that as a separate run. Preserve effective batch and accepted-example weighting if the aim is an optimization comparison; otherwise state that the training objective changed. Measure examples per second and rare-defect validation behavior. A smaller allocated peak can still yield lower throughput because backward reruns part of the forward. Do not claim a win based only on the largest batch that fits.'),
    ('Release a reproducible decision', 'Predeclare a minimum memory saving, maximum update-time increase and gradient tolerance. Keep the original training path when the technique misses these gates. Package model and block revisions, input shape, optimizer state, device, precision, RNG policy and profiler trace. Re-run the fixed-batch parity test after library upgrades. The deliverable is a measured tradeoff with a rollback path, not a statement that activation checkpointing is always beneficial.')],
    '''from dataclasses import dataclass

@dataclass(frozen=True)
class MemoryRun:
    peak_allocated_mb: float
    median_update_ms: float
    largest_gradient_gap: float

def release_failures(reference: MemoryRun, candidate: MemoryRun) -> list[str]:
    failures = []
    if candidate.largest_gradient_gap > 0.0001:
        failures.append("gradient parity")
    if candidate.peak_allocated_mb > reference.peak_allocated_mb * 0.82:
        failures.append("memory saving")
    if candidate.median_update_ms > reference.median_update_ms * 1.35:
        failures.append("update latency")
    return failures

plain_run = MemoryRun(2140, 38.2, 0.0)
recomputed_run = MemoryRun(1600, 55.4, 0.00003)
assert release_failures(plain_run, recomputed_run) == ["update latency"]''',
    'A checkpointed block trades stored activations for extra recomputation. The release gate itself is O(1), but each candidate needs multiple measured full updates and a gradient-parity comparison across model parameters. Peak allocated bytes are only one memory view; record reserved and device-level usage too. The example shows a candidate that saves memory yet fails its update-time gate. Its numbers are illustrative, not benchmarks from this machine. A larger-batch follow-up adds another training and validation cost.',
    ['Do not use illustrative values as measured GPU results.', 'Do not report memory savings before matching gradients and update boundaries.', 'Do not assume a larger fitting batch preserves the original effective-batch objective.'],
    ['deep-learning/activation-checkpointing-recompute-and-rng-parity', 'deep-learning/training-memory-profiler-and-allocator-boundaries', 'deep-learning/receipt-training-memory-project', 'deep-learning/gradient-accumulation-and-effective-batch', 'deep-learning/receipt-image-quality-project'], MEMORY, True)

CROSSLINKS = [
    ('deep-learning/convolution-output-geometry-and-receptive-field', 'deep-learning/segmentation-mask-alignment-and-ignore-pixels'),
    ('deep-learning/augmentation-leakage-boundary', 'deep-learning/segmentation-mask-alignment-and-ignore-pixels'),
    ('deep-learning/receipt-defect-localization-project', 'deep-learning/receipt-defect-segmentation-project'),
    ('deep-learning/receipt-image-quality-project', 'deep-learning/receipt-defect-segmentation-project'),
    ('deep-learning/inference-schema-and-latency', 'deep-learning/receipt-defect-segmentation-project'),
    ('deep-learning/checkpoint-resume-state', 'deep-learning/activation-checkpointing-recompute-and-rng-parity'),
    ('deep-learning/receipt-training-memory-project', 'deep-learning/receipt-activation-recompute-project'),
    ('deep-learning/mixed-precision-scaling-and-gradient-clipping', 'deep-learning/training-memory-profiler-and-allocator-boundaries'),
    ('deep-learning/gradient-accumulation-and-effective-batch', 'deep-learning/receipt-activation-recompute-project'),
    ('deep-learning/receipt-optimizer-selection-project', 'deep-learning/training-memory-profiler-and-allocator-boundaries'),
    ('deep-learning/deep-learning-tutorial', 'deep-learning/receipt-defect-segmentation-project'),
]

if __name__ == '__main__':
    publish(LESSONS, (SEGMENTATION, MEMORY), CROSSLINKS,
            'aitrove-deep-learning-segmentation-memory-import-20261006.json',
            7900, subject='deep-learning')
