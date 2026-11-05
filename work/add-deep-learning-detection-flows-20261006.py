"""Add box-detection and invertible-density Deep Learning paths."""
from de_batch_publisher import publish

DETECTION = 'Object boxes, matching and duplicate control'
FLOWS = 'Invertible density modeling and anomaly review'
LESSONS = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    assert len(sections) == 5
    LESSONS.append(dict(path='deep-learning/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add('box-coordinate-transform-and-one-to-one-matching',
    'Bounding-box transforms and one-to-one detection matching',
    'A detection score depends on box coordinates, image transforms and a one-prediction-to-one-object matching rule before any average precision calculation.', [
    ('Declare the coordinate system', 'Represent a box by left, top, right and bottom edges in one image coordinate space. This page uses continuous edge coordinates and area equal to width times height, with right and bottom edges excluded from the interior. Pixel-index-inclusive conventions require a different area rule. Record whether values are original-pixel, resized-pixel or normalized coordinates. Reject negative widths, out-of-bounds values and nonfinite coordinates before matching. [[computer-vision/annotation-geometry-and-quality|Annotation geometry]] is part of the dataset contract.'),
    ('Apply every image transform to boxes', 'A resize from 32-by-48 to 64-by-96 doubles each x and y edge. A crop subtracts its top-left offset, clips the remaining box to the crop and may remove the object entirely. Horizontal flips reverse x edges relative to the current image width. Do not transform an image and then compare predicted boxes in resized coordinates against annotations left in the original coordinate space. Save image overlays after each transform. [[deep-learning/segmentation-mask-alignment-and-ignore-pixels|Mask alignment]] follows a related but pixel-level rule.'),
    ('Compute overlap on valid geometry', 'Intersection-over-union divides shared area by the union area. A pair of boxes with no overlap has zero IoU; a degenerate zero-area box should be rejected rather than awarded a score. The example uses independently chosen edges and checks the resulting overlap. A score near a matching threshold can flip with one annotation pixel, so report performance across agreed thresholds and by object size, especially tiny clipped corners.'),
    ('Match once per reviewed object', 'Within each image and class, sort detections by confidence. A prediction can claim at most one unmatched reviewed box above the IoU threshold. Once a reviewed box is claimed, another overlapping prediction is a false positive, even if its IoU is high. An ignored region needs a separate rule; never count unlabeled areas as confirmed negatives by default. Matching across different images or classes can create fictitious true positives. [[deep-learning/class-aware-nms-and-score-thresholds|Suppression]] reduces duplicates before this evaluation.'),
    ('Keep metrics tied to the task', 'Average precision integrates precision over recall as a confidence threshold moves; it is not the accuracy of one fixed threshold. Report the chosen IoU matching threshold, class aggregation, ignored-region policy and score cutoff. For receipt fields, also report whether all required fields were found on a whole receipt and the count of duplicate boxes a reviewer must dismiss. [[deep-learning/receipt-field-box-detector-project|The project]] gates those operational outcomes.')],
    '''from math import isclose

def box_iou(first, second):
    for box in (first, second):
        left, top, right, bottom = box
        if not (left < right and top < bottom):
            raise ValueError("box must have positive width and height")
    overlap_width = max(0, min(first[2], second[2]) - max(first[0], second[0]))
    overlap_height = max(0, min(first[3], second[3]) - max(first[1], second[1]))
    intersection = overlap_width * overlap_height
    first_area = (first[2] - first[0]) * (first[3] - first[1])
    second_area = (second[2] - second[0]) * (second[3] - second[1])
    return intersection / (first_area + second_area - intersection)

reviewed_total_box = (13, 17, 37, 41)
predicted_total_box = (19, 20, 43, 44)
assert isclose(box_iou(reviewed_total_box, predicted_total_box), 378 / 774)''',
    'A single box-pair IoU is O(1) time and space. Comparing P predictions with G reviewed boxes is O(PG) overlap work before matching, while sorting P detections by confidence is O(P log P). For large image batches, dense pairwise IoU tables occupy O(PG) memory; stream per image and class when practical. Matching policy can change reported precision without changing model weights, so version it with the evaluation output.',
    ['Do not mix original and resized box coordinates.', 'Do not match two predictions to the same reviewed object.', 'Do not use one IoU area convention in training and another in evaluation.'],
    ['deep-learning/class-aware-nms-and-score-thresholds', 'deep-learning/receipt-field-box-detector-project', 'computer-vision/detection-metrics-and-thresholds', 'computer-vision/annotation-geometry-and-quality', 'deep-learning/segmentation-mask-alignment-and-ignore-pixels'], DETECTION)

add('class-aware-nms-and-score-thresholds',
    'Class-aware suppression and detection score thresholds',
    'Duplicate boxes should be suppressed within the correct class after a declared score filter; a suppression rule can also erase nearby real objects.', [
    ('Filter before suppression', 'A detector may emit many candidate boxes with objectness and class scores. Define exactly which score is ranked, whether class scores are calibrated and which low-score candidates are removed before suppression. A threshold chosen on the final test set leaks evaluation into the policy. Retain a development split with whole-receipt identities and freeze the threshold there. The code uses already scored detections and does not claim to compute neural logits. [[deep-learning/temperature-scaling-and-selective-risk|Calibration]] is separate from box overlap.'),
    ('Suppress within a class', 'Non-maximum suppression selects the highest-scored box, then removes lower-scored same-class boxes whose overlap exceeds a fixed IoU threshold. A total-field box and a date-field box may overlap without being duplicates, so class-agnostic suppression can discard a real field. The example keeps a same-location box of another class while dropping a near-duplicate total box. Verify that input boxes have valid geometry and that scores are finite before sorting.'),
    ('Know when overlap is not duplication', 'Two adjacent line-item fields can share border pixels, especially after a coarse resize. A low suppression threshold may erase one. A high threshold may leave several copies of the same total. Review both duplicate count and missed-object count by class and object size. For crowded forms, consider a different suppression or assignment policy, but show the failure cases before adding complexity. [[deep-learning/box-coordinate-transform-and-one-to-one-matching|One-to-one matching]] still governs evaluation after suppression.'),
    ('Keep deterministic ordering', 'When two boxes have equal scores, a stable tie rule makes replay and debugging possible. The implementation sorts by score then original index and emits retained original indices. Production libraries may have backend-specific tie behavior, so test the exact deployed operator if audit reproducibility matters. Apply the same cutoff, coordinate clipping and suppression to validation and serving. A change in these policies is a model-release change even when weights are unchanged.'),
    ('Measure the complete postprocessor', 'Record candidate count before and after score filtering, boxes after suppression, classwise false alerts and p95 postprocessing time. A tiny model can still have slow serving when thousands of dense candidates require pairwise comparisons. Compare detection quality at the frozen score and IoU settings on held-out receipts. [[deep-learning/receipt-field-box-detector-project|The applied project]] packages both thresholds with the model and retains a rollback route.')],
    '''from math import isfinite

def overlap(first, second):
    width = max(0, min(first[2], second[2]) - max(first[0], second[0]))
    height = max(0, min(first[3], second[3]) - max(first[1], second[1]))
    shared = width * height
    first_area = (first[2] - first[0]) * (first[3] - first[1])
    second_area = (second[2] - second[0]) * (second[3] - second[1])
    return shared / (first_area + second_area - shared)

def class_aware_nms(detections, score_floor, overlap_limit):
    for box, score, label in detections:
        if not (box[0] < box[2] and box[1] < box[3] and isfinite(score)):
            raise ValueError("invalid detection")
    candidates = sorted((index for index, item in enumerate(detections)
                         if item[1] >= score_floor),
                        key=lambda index: (-detections[index][1], index))
    retained = []
    for index in candidates:
        box, _, label = detections[index]
        if all(detections[kept][2] != label or
               overlap(box, detections[kept][0]) <= overlap_limit
               for kept in retained):
            retained.append(index)
    return retained

receipt_fields = [((10, 10, 30, 30), 0.93, "total"),
                  ((12, 12, 31, 31), 0.81, "total"),
                  ((10, 10, 30, 30), 0.72, "date")]
assert class_aware_nms(receipt_fields, 0.4, 0.5) == [0, 2]''',
    'Sorting N candidates costs O(N log N); the simple retained-box scan can cost O(N²) overlap checks in the worst case and O(N) output storage. The code is an audit-sized reference, not a high-throughput GPU postprocessor. Score filtering can reduce N substantially, but an aggressive cutoff may remove rare small fields. Profile candidate counts and deployed operator latency as well as model forward time.',
    ['Do not suppress boxes from different classes unless the task explicitly requires that.', 'Do not tune score or IoU cutoffs on the final test set.', 'Do not treat overlapping nearby objects as automatic duplicates.'],
    ['deep-learning/box-coordinate-transform-and-one-to-one-matching', 'deep-learning/receipt-field-box-detector-project', 'computer-vision/detection-metrics-and-thresholds', 'deep-learning/temperature-scaling-and-selective-risk', 'deep-learning/inference-schema-and-latency'], DETECTION)

add('receipt-field-box-detector-project',
    'Project: detect total, date and merchant fields on receipts',
    'Build a field-box workflow with reviewed coordinate transforms, class-aware duplicate control and whole-receipt release gates.', [
    ('Create a field-level annotation contract', 'Label total, date and merchant boxes on full receipt images. Record original dimensions, edge-coordinate convention and annotation uncertainty; group every crop from one physical receipt in the same split. Define whether an unreadable field is absent, present but ignored, or needs manual review. Audit overlays after resize and crop, especially at narrow page edges. [[deep-learning/box-coordinate-transform-and-one-to-one-matching|The box lesson]] fixes the geometry and one-to-one match policy.'),
    ('Prove the output wiring', 'The code performs one update for a deliberately restricted one-box-per-image toy head. It predicts a class and a valid normalized box, then combines class loss with box regression loss. It does not represent a full multi-object detector and must not be used to claim recall for receipts with several fields. Replace it with a proper multi-box architecture and assignment rule for the actual task. Keep a tiny deterministic fixture to test class order, box validity and gradient flow.'),
    ('Train and postprocess under one policy', 'Use paired image–box transforms and a per-class matching rule. Choose score cutoff and class-aware suppression on development receipts, then freeze them. Preserve all candidate boxes for diagnostic review, but expose only postprocessed detections to the application. Test crowded layouts where date and merchant text overlap and cases with two totals. [[deep-learning/class-aware-nms-and-score-thresholds|The suppression lesson]] describes how a real field can disappear.'),
    ('Evaluate whole-receipt usefulness', 'Report per-class precision and recall at a declared IoU threshold, duplicate boxes per receipt, exact presence of all required fields and time saved in review. Break results out by store format, device, blur and cropped edge. A detector can improve average precision while failing the receipts that need the most human attention. Include omitted or uncertain annotations in an explicit ignored-region count rather than silently counting them as background.'),
    ('Release with a reversible manifest', 'Package image normalization, class map, box convention, score threshold, suppression IoU, model revision and expected output schema. Replay fixed receipts in a clean process and check coordinate restoration to original pixels. Gate on field recall, duplicate load, p95 end-to-end latency and a manual fallback for missing fields. Keep the prior review flow if any gate fails. [[deep-learning/inference-schema-and-latency|The serving contract]] should include postprocessing time.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

torch.manual_seed(47)
receipt_images = torch.rand(3, 1, 32, 32)
reviewed_classes = torch.tensor([0, 2, 1])
reviewed_boxes = torch.tensor([[0.12, 0.48, 0.66, 0.71],
                               [0.09, 0.08, 0.57, 0.23],
                               [0.18, 0.27, 0.81, 0.46]])
field_head = nn.Sequential(nn.Conv2d(1, 8, 3, padding=1), nn.ReLU(),
                           nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(8, 7))
optimizer = torch.optim.AdamW(field_head.parameters(), lr=0.0007)
optimizer.zero_grad(set_to_none=True)
raw = field_head(receipt_images)
center = raw[:, 3:5].sigmoid()
extent = raw[:, 5:7].sigmoid() * 0.5
predicted_boxes = torch.cat(((center - extent / 2).clamp(0, 1),
                             (center + extent / 2).clamp(0, 1)), dim=1)
assert torch.all(predicted_boxes[:, :2] <= predicted_boxes[:, 2:])
loss = (functional.cross_entropy(raw[:, :3], reviewed_classes) +
        functional.smooth_l1_loss(predicted_boxes, reviewed_boxes))
loss.backward()
optimizer.step()
assert torch.isfinite(loss)''',
    'The toy head makes one class and box prediction per image, so its cost is dominated by the small convolution and cannot stand in for a multi-box detector. Production detectors add candidate generation, assignment and often O(N²) worst-case suppression for N candidates. Box annotations and whole-receipt review are material operating costs. Report preprocessing, model and postprocessing latency separately, plus candidate counts and memory at the real image size.',
    ['Do not score the one-box toy as though it detected three fields in one receipt.', 'Do not evaluate boxes before restoring original-image coordinates.', 'Do not ship a detector without class-aware duplicate and missing-field audits.'],
    ['deep-learning/box-coordinate-transform-and-one-to-one-matching', 'deep-learning/class-aware-nms-and-score-thresholds', 'deep-learning/receipt-defect-segmentation-project', 'computer-vision/detection-metrics-and-thresholds', 'deep-learning/inference-schema-and-latency'], DETECTION, True)

add('flow-change-of-variables-and-density-accounting',
    'Invertible flows and change-of-variables accounting',
    'An invertible model assigns density by mapping observations to a known base distribution and adding the log volume change of every transformation.', [
    ('Start with continuous, owned features', 'Suppose a service window has two reviewed continuous features: standardized request latency and standardized error pressure. A flow maps this vector to a base distribution while retaining enough information to invert the mapping. This is different from an autoencoder that may compress dimensions or a classifier that predicts a label directly. Keep feature units, normalization statistics and missing-value policy fixed. A density from one transformed feature scale is not numerically comparable with a density from another scale without accounting for the transformation.'),
    ('Carry the Jacobian term', 'If z is the transformed observation, the data log density equals base log density at z plus the log absolute determinant of the forward data-to-base Jacobian. Omitting that determinant rewards arbitrary shrinking or stretching. For a triangular affine coupling, only the scaled coordinates contribute to the determinant, so it can be computed without building a dense matrix. The code transforms a two-feature vector, inverts it and checks a finite log density. [[deep-learning/flow-affine-coupling-and-stability|The coupling lesson]] extends the layer.'),
    ('Separate exact math from model usefulness', 'An exact likelihood calculation means the formula is tractable for the chosen continuous representation. It does not mean high likelihood is equivalent to operational normality, nor that rare incidents always receive lower likelihood. A flow can spend capacity on irrelevant pixel or telemetry detail. Compare its alert ranking with a simple baseline and stratify by incident type. [[deep-learning/telemetry-autoencoder-alert-project|The reconstruction project]] provides a different anomaly score for comparison.'),
    ('Keep inversion testable', 'Every transform in a chain must have a declared inverse and log-determinant sign. Compose forward log determinants by addition, and test reconstruction error on fixed examples and extreme but valid feature values. A forward transform using z equals x minus shift times an exponential has the opposite sign from the inverse transform; a sign error may still produce finite losses. Check the analytic density on a tiny case against a direct calculation before training a large model.'),
    ('Plan the serving boundary', 'Persist base-distribution parameters, feature standardization, layer order and alert threshold with the weights. Score only windows built from measurements observable by the alert time. A missing feature should trigger a documented fallback instead of an arbitrary zero that could look highly probable. [[deep-learning/telemetry-flow-anomaly-project|The project]] evaluates alerts by reviewed incident and on-call workload, rather than treating likelihood alone as a release gate.')],
    '''from math import exp, isclose, log, pi

latency_signal, error_signal = 2.0, 3.0
log_scale = 0.2 * latency_signal
shift = 0.5 * latency_signal
base_first = latency_signal
base_second = (error_signal - shift) * exp(-log_scale)
forward_log_determinant = -log_scale
base_log_density = -0.5 * (base_first ** 2 + base_second ** 2) - log(2 * pi)
observed_log_density = base_log_density + forward_log_determinant
restored_error_signal = base_second * exp(log_scale) + shift
assert isclose(restored_error_signal, error_signal)
assert isclose(observed_log_density,
               -0.5 * (4.0 + (2.0 * exp(-0.4)) ** 2) - log(2 * pi) - 0.4)''',
    'A two-feature affine coupling is O(1). For D features and L layers, forward work depends on each conditioner network plus O(LD) elementwise transforms; saved activations and conditioner widths dominate training memory. A dense Jacobian determinant would be much more expensive, which is why structured coupling matters. Exact density does not remove the cost of fitting, calibrating or reviewing anomalies. The example is a mathematical self-check, not a trained incident model.',
    ['Do not omit or reverse the forward log-determinant sign.', 'Do not compare raw density values across different feature scales.', 'Do not equate low density with a confirmed incident.'],
    ['deep-learning/flow-affine-coupling-and-stability', 'deep-learning/telemetry-flow-anomaly-project', 'deep-learning/variational-latent-kl-and-collapse', 'deep-learning/telemetry-autoencoder-alert-project', 'deep-learning/temperature-scaling-and-selective-risk'], FLOWS)

add('flow-affine-coupling-and-stability',
    'Affine coupling layers, inverse checks and scale stability',
    'A coupling layer changes one feature group using the other, allowing a cheap inverse and triangular log determinant; repeated layers need controlled scale and feature mixing.', [
    ('Split features deliberately', 'An affine coupling leaves one feature group unchanged while a conditioner predicts shift and log scale for the other group. This makes inversion direct even if the conditioner itself is a noninvertible neural network. In a two-feature illustration, latency conditions the transformation of error pressure. If every layer always leaves latency untouched, the model never reshapes that dimension; alternate or permute feature groups across layers. Keep the permutation recorded so an inverse uses the exact reverse order. [[deep-learning/flow-change-of-variables-and-density-accounting|Density accounting]] supplies the sign convention.'),
    ('Clamp the learned log scale', 'An unconstrained exponential scale can overflow, underflow or produce extreme density terms. Bound the log scale with a smooth function and monitor its distribution. The code uses a bounded hyperbolic tangent; the bound is an engineering choice to validate on real standardized telemetry, not a universal constant. A bounded scale can also limit expressiveness, so inspect held-out likelihood and inverse error. Use finite-value checks before an optimizer step to avoid corrupting model state.'),
    ('Check both directions', 'For forward data-to-base mapping, subtract shift and multiply by the negative exponential scale; its log determinant is negative scale. The inverse multiplies by the positive exponential and adds shift. Test round-trip reconstruction per batch and compare forward plus inverse log determinants with zero. A mistaken feature permutation can preserve shapes and even train while making inversion wrong. The miniature code asserts exact tensor closeness for one layer.'),
    ('Handle missing and discrete inputs', 'A continuous density model does not automatically assign a probability mass to discrete counts. Counts may need a separate model or a documented continuous representation; naive jitter changes the target distribution. Missing values are not ordinary zeros after standardization. Segment by completeness and route incomplete windows through a separately evaluated path. A feature mask added to the vector may be useful, but then train and serve with that mask and audit missingness drift.'),
    ('Validate against operations', 'Likelihood should be assessed on unseen time periods and service families, not only by average negative log likelihood. Review false alerts during deployments, quiet nights and high-traffic but healthy periods. Compare with an autoencoder and simple percentile rule at equal alert budgets. [[deep-learning/telemetry-flow-anomaly-project|The applied project]] freezes an on-call threshold only after the model passes inverse, density and workload checks.')],
    '''import torch
from torch import nn

torch.manual_seed(47)
telemetry = torch.tensor([[0.8, -0.3], [1.4, 0.2], [-0.5, 0.9]])
conditioner = nn.Linear(1, 2)
shift_and_raw_scale = conditioner(telemetry[:, :1])
shift = shift_and_raw_scale[:, :1]
log_scale = shift_and_raw_scale[:, 1:].tanh() * 0.8
base_second = (telemetry[:, 1:] - shift) * torch.exp(-log_scale)
base_vector = torch.cat((telemetry[:, :1], base_second), dim=1)
forward_log_determinant = -log_scale.squeeze(1)
restored_second = base_vector[:, 1:] * torch.exp(log_scale) + shift
restored = torch.cat((base_vector[:, :1], restored_second), dim=1)
torch.testing.assert_close(restored, telemetry)
torch.testing.assert_close(forward_log_determinant + log_scale.squeeze(1),
                           torch.zeros(3))''',
    'The affine elementwise transform is O(BD) for batch B and transformed dimension D, plus the conditioner network cost. The triangular determinant requires summing log scales, not materializing a D-by-D Jacobian. Multiple alternating layers add conditioner work and backward activations. The small example verifies one layer’s inverse and determinant signs; it does not establish whether the resulting density is useful for incident ranking. Profile scale extremes and inverse error on the actual feature distribution.',
    ['Do not leave the same feature group unchanged in every layer.', 'Do not let an exponential log scale grow without finite-value and inverse checks.', 'Do not treat missing telemetry as a normal standardized zero without a policy.'],
    ['deep-learning/flow-change-of-variables-and-density-accounting', 'deep-learning/telemetry-flow-anomaly-project', 'deep-learning/variational-latent-kl-and-collapse', 'deep-learning/checkpoint-resume-state', 'deep-learning/telemetry-autoencoder-alert-project'], FLOWS)

add('telemetry-flow-anomaly-project',
    'Project: review telemetry anomalies with an invertible flow',
    'Fit a continuous density model on healthy service windows and test whether its low-density alerts improve reviewed incident recall at a fixed on-call budget.', [
    ('Define a healthy training population', 'Use standardized continuous latency and error-pressure features from reviewed healthy windows. Split by time and service family, and isolate deployments or incidents from the healthy fit. Record feature arrival times so scoring never sees later telemetry. Store normalization statistics from training only. The synthetic code below trains one two-feature coupling layer and checks finite density; it does not prove anomaly-detection performance. [[deep-learning/flow-change-of-variables-and-density-accounting|The density lesson]] defines the calculation.'),
    ('Train with inverse tests attached', 'Alternate feature order across enough layers to transform all dimensions. After every architecture change, run forward–inverse round trips, determinant-sign checks and finite-loss tests at normal and extreme valid inputs. Inspect per-feature standardization and learned log-scale range. A lower negative log likelihood on healthy windows may merely improve modeling of routine traffic variation. [[deep-learning/flow-affine-coupling-and-stability|The coupling lesson]] explains why the inverse and scale must be audited.'),
    ('Calibrate an alert policy', 'Turn low density into an alert only after selecting a threshold on a development period with a fixed daily review budget. Compare a simple percentile rule and the existing reconstruction model under the same alert budget. Evaluate reviewed incident recall, false pages per service-day and time-to-first-alert by incident type. Keep uncertainty about unlabeled incidents visible. A surprising but healthy deployment can be low-density, while a harmful common-looking incident can be high-density.'),
    ('Test shifts and missing data', 'Score unseen service families and later periods. Break results down by high traffic, maintenance, telemetry gaps and feature latency. Route missing or nonfinite inputs to a stated fallback rather than passing them into the flow. Preserve alert examples with feature values, base coordinates and density components for review, while avoiding claims that a low-density feature caused an incident. A human incident label and a model anomaly score answer different questions.'),
    ('Release with rollback and workload gates', 'Package feature units, normalization, layer order, base distribution, model weights and threshold. Replay fixed healthy and incident windows in a clean process. Gate on incident recall at a maximum false-page rate, finite density, inverse error and p95 scoring latency. Keep the simpler monitor when the flow misses a gate. The deliverable is an alert ledger tied to review capacity, not a histogram of impressive likelihood values.')],
    '''import math
import torch
from torch import nn

torch.manual_seed(47)
healthy_windows = torch.tensor([[0.2, -0.3], [0.5, 0.1],
                                [-0.4, 0.2], [0.1, -0.2]])
conditioner = nn.Linear(1, 2)
optimizer = torch.optim.AdamW(conditioner.parameters(), lr=0.0007)
optimizer.zero_grad(set_to_none=True)
shift_and_scale = conditioner(healthy_windows[:, :1])
shift = shift_and_scale[:, :1]
log_scale = shift_and_scale[:, 1:].tanh() * 0.8
latent_second = (healthy_windows[:, 1:] - shift) * torch.exp(-log_scale)
latent = torch.cat((healthy_windows[:, :1], latent_second), dim=1)
base_log_density = -0.5 * latent.square().sum(dim=1) - math.log(2 * math.pi)
data_log_density = base_log_density - log_scale.squeeze(1)
loss = -data_log_density.mean()
assert torch.isfinite(loss)
loss.backward()
optimizer.step()''',
    'One two-feature coupling layer is cheap, but it leaves one coordinate unchanged and is only a training-path demonstration. A usable flow stacks alternating conditioners, whose computation and saved activations dominate O(BD) elementwise transforms. Scoring every service window also incurs feature-fetch and logging costs. Review labels, incident grouping and the agreed alert budget determine whether a gain matters. The synthetic optimizer step verifies a finite gradient, not a validated anomaly detector.',
    ['Do not claim that a finite synthetic likelihood proves useful alerts.', 'Do not fit normalization on future or incident windows.', 'Do not deploy low-density pages without a false-page budget and missing-data fallback.'],
    ['deep-learning/flow-change-of-variables-and-density-accounting', 'deep-learning/flow-affine-coupling-and-stability', 'deep-learning/telemetry-autoencoder-alert-project', 'deep-learning/temperature-scaling-and-selective-risk', 'deep-learning/inference-schema-and-latency'], FLOWS, True)

CROSSLINKS = [
    ('computer-vision/annotation-geometry-and-quality', 'deep-learning/box-coordinate-transform-and-one-to-one-matching'),
    ('computer-vision/detection-metrics-and-thresholds', 'deep-learning/box-coordinate-transform-and-one-to-one-matching'),
    ('deep-learning/segmentation-mask-alignment-and-ignore-pixels', 'deep-learning/box-coordinate-transform-and-one-to-one-matching'),
    ('deep-learning/temperature-scaling-and-selective-risk', 'deep-learning/class-aware-nms-and-score-thresholds'),
    ('deep-learning/receipt-defect-localization-project', 'deep-learning/receipt-field-box-detector-project'),
    ('deep-learning/inference-schema-and-latency', 'deep-learning/receipt-field-box-detector-project'),
    ('deep-learning/variational-latent-kl-and-collapse', 'deep-learning/flow-change-of-variables-and-density-accounting'),
    ('deep-learning/telemetry-autoencoder-alert-project', 'deep-learning/telemetry-flow-anomaly-project'),
    ('deep-learning/temperature-scaling-and-selective-risk', 'deep-learning/telemetry-flow-anomaly-project'),
    ('deep-learning/checkpoint-resume-state', 'deep-learning/flow-affine-coupling-and-stability'),
    ('deep-learning/deep-learning-tutorial', 'deep-learning/receipt-field-box-detector-project'),
]

if __name__ == '__main__':
    publish(LESSONS, (DETECTION, FLOWS), CROSSLINKS,
            'aitrove-deep-learning-detection-flows-import-20261006.json',
            7930, subject='deep-learning')
