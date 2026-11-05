"""Add original convolution and transfer-learning pathways to AI Trove."""
from de_batch_publisher import publish

CONV = 'Convolution geometry and residual design'
TRANSFER = 'Transfer learning and domain shift'
LESSONS = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    assert len(sections) == 5
    LESSONS.append(dict(path='deep-learning/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add('convolution-output-geometry-and-receptive-field',
    'Convolution output geometry and receptive fields',
    'A convolutional stack changes spatial resolution and the portion of the input each output can inspect; both properties belong in the model contract.', [
    ('Calculate the grid before training', 'For one spatial axis, the output length is floor((input + 2 × padding − dilation × (kernel − 1) − 1) / stride + 1). Calculate height and width separately when kernels or strides differ. A 47 by 83 receipt crop sent through a three-wide convolution with padding one and stride two becomes 24 by 42, not 23 by 41. This floor operation matters at odd sizes. Assert the observed tensor shape against the calculation before connecting a classifier or decoder. [[deep-learning/tensor-shape-dtype-contract|The tensor contract]] also fixes channel order.'),
    ('Separate resolution from context', 'A three-wide kernel at dilation one sees three neighboring positions in one layer. A second three-wide, stride-one layer expands the theoretical receptive field to five; a stride-two layer changes the spacing between positions used by later layers. Track two values: receptive-field width and jump, the distance in original pixels between adjacent outputs. Starting at one for both, a layer with kernel k, dilation d and stride s adds (k − 1) × d × previous jump to field width and multiplies jump by s. Large theoretical context is no guarantee that training uses distant pixels.'),
    ('Choose padding for the task', 'Zero padding creates artificial borders. That may be acceptable for whole-image classification, but a defect next to a cropped edge can receive a different context from a defect in the center. Reflection padding can reduce the artificial step yet has its own constraint: the padding width must be smaller than the input extent. Keep crop policy, padding mode and any resize in the model artifact. [[deep-learning/augmentation-leakage-boundary|Augmentation]] should model camera variation without moving evidence outside the label.'),
    ('Inspect aliasing and detail loss', 'Stride two discards spatial samples. It can help cost and context, but tiny receipt marks may vanish after repeated reductions. Compare a shallow high-resolution branch against a deeper reduced branch on the small-defect slice, and inspect false negatives by mark width. Pooling is another reduction; it does not restore removed detail. When the target is a pixel mask, keep a clear map from output grid coordinates to input pixels and test odd dimensions as well as the usual square input.'),
    ('Validate with a shape probe', 'A shape probe should include the smallest accepted crop, an odd-width crop and the maximum configured crop. Record each intermediate feature map and compare with the formula. An intentionally invalid kernel/input pair should fail before a training job begins. Put the probe in the same configuration path used by serving: a model that trains on resized 224-square crops and serves on native 47 by 83 crops has a different output geometry and potentially different edge behavior.')],
    '''from dataclasses import dataclass
import torch
from torch import nn

@dataclass(frozen=True)
class ConvPlan:
    kernel: int
    stride: int
    padding: int
    dilation: int = 1

def output_extent(input_extent: int, plan: ConvPlan) -> int:
    numerator = input_extent + 2 * plan.padding - plan.dilation * (plan.kernel - 1) - 1
    if numerator < 0:
        raise ValueError("kernel does not fit the crop")
    return numerator // plan.stride + 1

receipt_crop = torch.zeros(2, 1, 47, 83)
first_plan = ConvPlan(kernel=3, stride=2, padding=1)
edge_bank = nn.Conv2d(1, 12, kernel_size=first_plan.kernel,
                      stride=first_plan.stride, padding=first_plan.padding)
edge_maps = edge_bank(receipt_crop)
expected_grid = (output_extent(47, first_plan), output_extent(83, first_plan))
assert expected_grid == (24, 42)
assert edge_maps.shape == (2, 12, *expected_grid)''',
    'A standard convolution with input channels C, output channels F, kernel area K and output grid area G performs work proportional to G × C × F × K per example. Its weights occupy C × F × K parameters plus optional biases. Activations scale with batch × F × G and often dominate training memory at high resolution. A larger stride reduces G but may erase narrow evidence; measure the small-object slice before accepting that trade.',
    ['Do not assume odd input dimensions divide evenly under a stride.', 'Do not confuse output resolution with receptive-field width.', 'Do not change resize or padding behavior between training and serving.'],
    ['deep-learning/tensor-shape-dtype-contract', 'deep-learning/augmentation-leakage-boundary', 'deep-learning/receipt-image-quality-project', 'deep-learning/inference-schema-and-latency', 'deep-learning/receipt-defect-localization-project'], CONV)

add('residual-blocks-and-normalization-state',
    'Residual blocks and normalization state',
    'A residual path must align shapes before addition, while batch-normalization statistics have a separate lifecycle from gradient updates.', [
    ('Define the addition contract', 'A residual block returns a transformed feature map plus a shortcut. Addition requires identical batch, channel, height and width dimensions. If the main branch changes width or downsamples, use a projection shortcut with matching stride and output channels; silently broadcasting a singleton channel is a bug, not a substitute. Assert branch shapes at the addition point. [[deep-learning/convolution-output-geometry-and-receptive-field|Convolution geometry]] predicts the new grid before the first optimizer step.'),
    ('Place nonlinearities deliberately', 'The block below applies convolution, batch normalization and activation on the main path, then adds the shortcut and activates the sum. Other residual layouts exist, but changing the order changes the function and checkpoint compatibility. A zeroed main branch should still pass shortcut information through the final activation. The shortcut makes a short route for signals and gradients, yet it does not guarantee that an oversized learning rate or bad labels will train successfully. Compare training curves against a plain stack under a fixed data split.'),
    ('Treat running statistics as state', 'BatchNorm has learned affine parameters and running mean/variance buffers. Setting requires_grad false freezes the affine parameters but does not stop running buffers from changing in train mode. During low-label transfer, a backbone can be frozen for gradients while its feature distribution drifts because those buffers keep updating. Evaluate and serve with eval mode; if the plan is to freeze the backbone entirely, keep its BatchNorm modules in eval mode even when the new head trains. [[deep-learning/train-eval-validation-loop|The train/eval contract]] controls this state.'),
    ('Handle small and uneven batches', 'Batch statistics become noisy with very small per-device batches. Gradient accumulation does not create a larger BatchNorm batch, because each forward pass still normalizes its own microbatch. A final batch of one can fail for a feature map with one spatial position. Options include a frozen pretrained normalization state, a different normalization layer, or a data loader that avoids the problematic batch; each changes the model behavior and needs validation. [[deep-learning/gradient-accumulation-and-effective-batch|Accumulation]] changes update cadence, not normalization scope.'),
    ('Test the transition to inference', 'Capture output for a fixed feature tensor in evaluation mode, save weights and buffers, reload into a fresh model, and compare output. Compare one train-mode pass separately to expose running-stat updates. Check projection and identity variants, odd spatial sizes and a batch of one. A checkpoint containing only trainable parameters is incomplete when nontrainable buffers affect inference; record a whole state dictionary and a model revision in the artifact.')],
    '''import torch
from torch import nn

class ReceiptResidualBlock(nn.Module):
    def __init__(self, input_channels: int, output_channels: int, stride: int = 1):
        super().__init__()
        self.main = nn.Sequential(
            nn.Conv2d(input_channels, output_channels, 3, stride, 1, bias=False),
            nn.BatchNorm2d(output_channels), nn.ReLU(),
            nn.Conv2d(output_channels, output_channels, 3, 1, 1, bias=False),
            nn.BatchNorm2d(output_channels))
        self.shortcut = (nn.Identity() if stride == 1 and input_channels == output_channels
                         else nn.Sequential(nn.Conv2d(input_channels, output_channels, 1,
                                                      stride, bias=False),
                                            nn.BatchNorm2d(output_channels)))
        self.activation = nn.ReLU()

    def forward(self, receipt_features: torch.Tensor) -> torch.Tensor:
        transformed = self.main(receipt_features)
        shortcut = self.shortcut(receipt_features)
        if transformed.shape != shortcut.shape:
            raise RuntimeError("residual branches have different shapes")
        return self.activation(transformed + shortcut)

block = ReceiptResidualBlock(12, 24, stride=2).eval()
with torch.inference_mode():
    result = block(torch.randn(2, 12, 47, 83))
assert result.shape == (2, 24, 24, 42)''',
    'The two main 3 by 3 convolutions and optional 1 by 1 projection dominate arithmetic; the addition itself is linear in the output feature-map size. BatchNorm keeps channel-wise buffers and reads activation statistics during training. Projection blocks add parameters and compute, while identity shortcuts are cheap. Memory still grows with stored activations, so residual connections are not a substitute for a measured training budget.',
    ['Do not add branches with mismatched spatial or channel dimensions.', 'Do not equate frozen gradients with frozen BatchNorm running statistics.', 'Do not omit buffers from a checkpoint intended for inference.'],
    ['deep-learning/convolution-output-geometry-and-receptive-field', 'deep-learning/train-eval-validation-loop', 'deep-learning/checkpoint-resume-state', 'deep-learning/gradient-accumulation-and-effective-batch', 'deep-learning/receipt-defect-localization-project'], CONV)

add('receipt-defect-localization-project',
    'Project: localize receipt defects with a residual CNN',
    'Build a pixel-level defect detector that keeps coordinate alignment across convolution, downsampling and a residual block, then audit failures at crop edges.', [
    ('Write a mask contract', 'For each receipt image, store an image identity, native height and width, a binary mask for unreadable regions and a crop transform. Split by receipt identity before extracting overlapping crops. A mask cannot be resized with the same smooth interpolation as a photograph: use nearest-neighbor for discrete labels, and verify that every positive pixel still maps to the right location. [[deep-learning/augmentation-leakage-boundary|Split-before-augmentation]] prevents neighboring crops from contaminating validation.'),
    ('Design the spatial path', 'Use a stride-one feature stem and one stride-two residual block. Upsample to the original crop size for a one-channel logit mask; size-based interpolation removes ambiguity for odd heights and widths. The network below is a minimal shape-checked reference, not a claim that one block is enough for every receipt. Compare its receptive field against the width of known defects. [[deep-learning/convolution-output-geometry-and-receptive-field|Geometry accounting]] explains the half-resolution feature grid.'),
    ('Keep the loss and metric honest', 'Train on logits with a binary cross-entropy loss; threshold probabilities only for an evaluation decision. Report pixel recall, intersection over union and receipt-level miss rate, with edge defects separated from center defects. A model can earn a good global pixel score by predicting background everywhere when defects are rare. Fix the threshold using validation data; leave a held-out test split untouched. [[deep-learning/logits-loss-gradient|Logits and loss]] must keep the same target scale.'),
    ('Challenge the padding choice', 'Create a test set with marks touching the crop edge and one with the same marks translated into the center. Compare false-negative rates. Test zero padding against an explicit alternative under the same split, optimizer and threshold policy. A change in crop size can also change the feature-map grid, so assert output mask dimensions for 47 by 83, 48 by 84 and a narrow minimum crop. Do not infer edge reliability from center-only visual examples.'),
    ('Package the serving boundary', 'Save a full state dictionary, class definition version, normalization values, resize policy, mask threshold and output-coordinate transform. Reload the artifact and check pixel-aligned output for the same fixed image. Log latency and peak memory at the largest accepted crop. The project passes only when an edge-defect counterexample, a blank receipt and a low-contrast receipt all have documented outcomes, including what the product does when confidence is low.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

class ReceiptDefectNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.stem = nn.Sequential(nn.Conv2d(1, 12, 3, padding=1, bias=False),
                                  nn.BatchNorm2d(12), nn.ReLU())
        self.main = nn.Sequential(nn.Conv2d(12, 24, 3, stride=2, padding=1,
                                            bias=False), nn.BatchNorm2d(24), nn.ReLU(),
                                  nn.Conv2d(24, 24, 3, padding=1, bias=False),
                                  nn.BatchNorm2d(24))
        self.shortcut = nn.Conv2d(12, 24, 1, stride=2)
        self.head = nn.Conv2d(24, 1, 1)

    def forward(self, receipt_images: torch.Tensor) -> torch.Tensor:
        high_resolution = self.stem(receipt_images)
        low_resolution = functional.relu(self.main(high_resolution)
                                         + self.shortcut(high_resolution))
        low_resolution_logits = self.head(low_resolution)
        return functional.interpolate(low_resolution_logits,
                                      size=receipt_images.shape[-2:],
                                      mode="bilinear", align_corners=False)

model = ReceiptDefectNet()
receipt_images = torch.rand(2, 1, 47, 83)
defect_masks = torch.zeros_like(receipt_images)
defect_masks[:, :, 11:16, 33:39] = 1
mask_logits = model(receipt_images)
loss = functional.binary_cross_entropy_with_logits(mask_logits, defect_masks)
loss.backward()
assert mask_logits.shape == defect_masks.shape
assert torch.isfinite(loss)''',
    'Convolution work grows with image area, kernel area and channel products; the retained high-resolution stem activation can dominate memory. Bilinear output resizing costs O(batch × image pixels) and does not recover detail already erased by a coarse feature grid. Track receipt-level miss rate alongside pixel metrics, and profile largest accepted crops rather than only the 47 by 83 reference.',
    ['Do not split overlapping crops from one receipt across training and validation.', 'Do not use smooth interpolation on a binary ground-truth mask.', 'Do not treat a high background-dominated pixel accuracy as defect detection.'],
    ['deep-learning/convolution-output-geometry-and-receptive-field', 'deep-learning/residual-blocks-and-normalization-state', 'deep-learning/augmentation-leakage-boundary', 'deep-learning/logits-loss-gradient', 'deep-learning/inference-schema-and-latency'], CONV, True)

add('frozen-features-versus-fine-tuning',
    'Frozen features versus fine-tuning a pretrained backbone',
    'Feature extraction and fine-tuning use the same pretrained weights but change which state is allowed to move, how much memory training needs and what can overfit.', [
    ('Establish a frozen baseline', 'Replace the pretrained classifier with a new head for the target labels, freeze every backbone parameter and train only the head. Keep the backbone in evaluation mode if its normalization buffers are intended to remain fixed. Match the preprocessing expected by the selected weights; changing color order or normalization can make the features meaningless even though tensor shapes match. [[deep-learning/receipt-image-quality-project|Receipt-quality labels]] provide a concrete target while the pretrained backbone supplies initial visual features.'),
    ('Unfreeze only when evidence warrants it', 'A frozen baseline is fast to run and makes a useful lower-risk comparison. If errors cluster on domain-specific marks, unfreeze a late block and measure whether held-out groups improve. New head parameters start from a different distribution than pretrained features, so use a separately controlled learning rate for each parameter group. Training every layer from the first update on a small dataset can move useful features before the head stabilizes. [[deep-learning/train-eval-validation-loop|Validation discipline]] decides whether adaptation helped.'),
    ('Separate gradients from module mode', 'requires_grad false prevents gradient accumulation for frozen parameters, but train mode can still update BatchNorm buffers and apply dropout. Use a wrapper or training-loop rule that reapplies eval to a frozen backbone after calling model.train on the full model. If a late block is unfrozen, choose explicitly whether its normalization buffers also adapt. Do not infer the choice from optimizer parameter groups. [[deep-learning/residual-blocks-and-normalization-state|Normalization state]] belongs in the checkpoint and test plan.'),
    ('Budget the two phases', 'With a frozen backbone, no backward graph through its internal layers is needed; only the new head requires gradient storage. Fine-tuning late layers stores their activations for backward, increasing memory and training time. Keep frozen-feature caching only when preprocessing is deterministic and the backbone truly fixed; random augmentation changes features each epoch. If cached features are derived from images with sensitive information, apply the same retention and access controls as the original inputs.'),
    ('Keep comparison fair', 'Use the same identity-disjoint split, label map, target metric and decision threshold policy for frozen and fine-tuned models. Compare by source device and defect type, not only the mean score. A small average gain can hide a serious regression on low-contrast receipts. Save both candidates, preprocessing configuration and validation report; choose with a stated rule before opening the final test population.')],
    '''import torch
from torch import nn
from torchvision.models import resnet18, ResNet18_Weights

selected_weights = ResNet18_Weights.IMAGENET1K_V1
quality_backbone = resnet18(weights=selected_weights)
input_features = quality_backbone.fc.in_features
quality_backbone.fc = nn.Linear(input_features, 3)
for parameter_name, parameter in quality_backbone.named_parameters():
    parameter.requires_grad = parameter_name.startswith("fc.")

quality_backbone.train()
for module_name, module in quality_backbone.named_modules():
    if module_name and not module_name.startswith("fc"):
        module.eval()

head_optimizer = torch.optim.AdamW(quality_backbone.fc.parameters(), lr=0.00037)
assert all(not parameter.requires_grad for parameter in quality_backbone.layer1.parameters())
assert quality_backbone.bn1.training is False
assert quality_backbone.fc.training is True
preprocess_for_inference = selected_weights.transforms()''',
    'Feature extraction still runs a backbone forward pass, but saves much less backward state and updates only the head. Fine-tuning a late stage adds its parameter gradients, optimizer state and retained activations. Full fine-tuning can approach the cost of training the whole network. Pretrained weights may download once, so pin their identity and cache the artifact in a controlled build rather than depending on a network fetch at serving time.',
    ['Do not freeze parameters while leaving running normalization buffers free to drift by accident.', 'Do not compare models built with different image normalization or label splits.', 'Do not deploy a model that downloads its pretrained weights during a request.'],
    ['deep-learning/residual-blocks-and-normalization-state', 'deep-learning/train-eval-validation-loop', 'deep-learning/receipt-image-quality-project', 'deep-learning/augmentation-leakage-boundary', 'deep-learning/staged-unfreezing-and-domain-shift-audit'], TRANSFER)

add('staged-unfreezing-and-domain-shift-audit',
    'Staged unfreezing and domain-shift audits',
    'A staged adaptation should show which layer was unfrozen, which population improved and whether the new model forgot behavior it previously handled.', [
    ('Name the shifted population', 'Suppose a receipt classifier trained mostly on thermal-paper scans begins receiving glossy mobile-camera images. Keep the original scan validation set and a device-disjoint glossy validation set. Split by receipt and merchant identity where repeated layouts could leak. The question is not whether training loss falls; it is whether the new domain improves without an unacceptable regression on the original one. [[deep-learning/augmentation-leakage-boundary|Identity-safe splitting]] precedes any adaptation.'),
    ('Stage the update', 'First train only the replacement head, then unfreeze a late feature block with a smaller learning rate than the head. Evaluate after each stage and stop if the predeclared acceptance rule fails. Construct optimizer groups only from parameters that require gradients; after a stage transition, rebuild the optimizer deliberately because its groups and moments no longer describe the intended parameter set. If continuity of the head optimizer state matters, migrate it explicitly and verify it rather than silently resetting.'),
    ('Inspect normalization and preprocessing', 'Glossy photos may change brightness statistics, but blindly updating BatchNorm running buffers on a tiny domain slice can destabilize older images. Run a controlled variant with those buffers fixed and one with explicit adaptation. Use the same input color space, resize and weight-specific normalization in every variant. [[deep-learning/frozen-features-versus-fine-tuning|Frozen-feature policy]] explains why gradient flags alone do not define model state.'),
    ('Use slices that explain failure', 'Report confusion matrices by paper type, acquisition device and defect class. Track calibration or threshold changes separately from representation changes: a better ranking score can still produce worse decisions at a fixed threshold. If labels are sparse in the shifted domain, include confidence intervals or raw numerator and denominator for each slice. Do not let a broad aggregate hide two missed cutoff receipts in a small critical subgroup.'),
    ('Record rollback evidence', 'Save the frozen baseline, each accepted stage and its exact preprocessing and threshold. Re-evaluate both domains after loading from disk to expose buffer or serialization mistakes. Keep the rollout reversible: an inference error or domain regression should select the previous artifact, not trigger another unreviewed training run. [[deep-learning/checkpoint-resume-state|Checkpoint state]] concerns training continuation; serving needs a separately tested inference artifact.')],
    '''import torch
from torch import nn
from torchvision.models import resnet18, ResNet18_Weights

domain_model = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
domain_model.fc = nn.Linear(domain_model.fc.in_features, 3)
for parameter in domain_model.parameters():
    parameter.requires_grad = False
for parameter in domain_model.fc.parameters():
    parameter.requires_grad = True

def make_optimizer(model: nn.Module, adapt_last_block: bool):
    for parameter in model.layer4.parameters():
        parameter.requires_grad = adapt_last_block
    parameter_groups = [
        {"params": list(model.fc.parameters()), "lr": 0.00043},
    ]
    if adapt_last_block:
        parameter_groups.append({"params": list(model.layer4.parameters()),
                                 "lr": 0.000047})
    optimizer = torch.optim.AdamW(parameter_groups, weight_decay=0.013)
    selected_ids = [id(parameter) for group in optimizer.param_groups
                    for parameter in group["params"]]
    assert len(selected_ids) == len(set(selected_ids))
    return optimizer

frozen_optimizer = make_optimizer(domain_model, adapt_last_block=False)
adapted_optimizer = make_optimizer(domain_model, adapt_last_block=True)
assert len(frozen_optimizer.param_groups) == 1
assert len(adapted_optimizer.param_groups) == 2''',
    'Unfreezing the late block adds its backward activations, gradients and optimizer moments. Rebuilding an optimizer at a stage boundary is cheap relative to training, but resetting moments changes the trajectory and must be recorded. A two-domain validation pass roughly doubles evaluation work compared with one domain; it is still cheaper than releasing an adaptation that fails on previously supported receipts.',
    ['Do not infer population improvement from training loss alone.', 'Do not add the same parameter to multiple optimizer groups or leave an unfrozen parameter out.', 'Do not call a stage accepted without checking regression on the original domain.'],
    ['deep-learning/frozen-features-versus-fine-tuning', 'deep-learning/residual-blocks-and-normalization-state', 'deep-learning/augmentation-leakage-boundary', 'deep-learning/checkpoint-resume-state', 'deep-learning/receipt-domain-adaptation-project'], TRANSFER)

add('receipt-domain-adaptation-project',
    'Project: adapt a receipt model to a new capture device',
    'Compare a frozen visual backbone with a staged late-block update on a new device population, using explicit regression limits and a reloadable serving artifact.', [
    ('Build the two-domain manifest', 'Collect 470 scanned receipts and 137 mobile captures with readable, blurred and cut-off labels. Group by physical receipt and merchant layout before splitting; multiple photos of the same paper cannot cross train and validation. Reserve an untouched test set from each domain. Record counts by class and capture device so that a result based on three cutoff examples is not reported as stable evidence. [[deep-learning/receipt-image-quality-project|The base project]] defines the quality task.'),
    ('Create the frozen reference', 'Load a pinned pretrained backbone, replace its head and train only that head with the backbone held in eval mode. Use the preprocessing associated with the selected weight identity and persist it. Record training cost, old-domain and new-domain confusion matrices and the chosen threshold. This becomes the rollback candidate, not just a number in a notebook. [[deep-learning/frozen-features-versus-fine-tuning|Frozen versus adapted state]] defines the reference.'),
    ('Run one controlled adaptation', 'Unfreeze only the final block and create separate learning-rate groups for the block and head. Keep the identity split, preprocessing, labels and validation schedule fixed. Declare an acceptance rule before training: for example, improve mobile-capture recall by at least four percentage points while allowing no more than one percentage point loss on scanned-receipt recall. Because the mobile group is small, include counts and uncertainty; the rule is a product decision, not a statistical guarantee.'),
    ('Audit the hidden state', 'Before each stage, print the trainable parameter names and check BatchNorm mode for the frozen and unfrozen blocks. Save a full state dictionary and reload it into a newly created model. Compare logits for a fixed scanned and mobile image under eval mode. Break the preprocessing once on purpose, such as swapping channel order, and confirm an input-contract test catches it. [[deep-learning/residual-blocks-and-normalization-state|Running statistics]] can change predictions without a trainable gradient.'),
    ('Publish a decision record', 'Show both-domain confusion matrices, latency, memory, training-time cost, acceptance-rule result and a list of the worst mobile and scan errors. If the adapted model misses the old-domain limit, ship the frozen candidate and document which slice failed. Package weights, architecture revision, weight identity, preprocessing, label map and threshold. A deployment smoke test should reload from that package and reproduce fixed-batch logits before the traffic switch.')],
    '''import torch
from torch import nn

def recall_from_counts(true_positive: int, false_negative: int) -> float:
    denominator = true_positive + false_negative
    if denominator == 0:
        raise ValueError("recall requires at least one positive case")
    return true_positive / denominator

baseline_scan_recall = recall_from_counts(90, 10)
adapted_scan_recall = recall_from_counts(89, 11)
baseline_mobile_recall = recall_from_counts(54, 16)
adapted_mobile_recall = recall_from_counts(59, 11)
mobile_gain = adapted_mobile_recall - baseline_mobile_recall
scan_regression = baseline_scan_recall - adapted_scan_recall
accepted = mobile_gain >= 0.04 and scan_regression <= 0.010001
assert accepted

class QualityHead(nn.Module):
    def __init__(self, input_width: int):
        super().__init__()
        self.classifier = nn.Linear(input_width, 3)

    def forward(self, backbone_features: torch.Tensor) -> torch.Tensor:
        return self.classifier(backbone_features)

artifact = {"label_map": {0: "readable", 1: "blurred", 2: "cut_off"},
            "scan_recall": adapted_scan_recall,
            "mobile_recall": adapted_mobile_recall}
assert set(artifact["label_map"]) == {0, 1, 2}''',
    'The frozen run spends compute on backbone forward passes and head updates. Late-block tuning adds backward compute and activation memory for that block. Evaluation now covers two populations and slices within each; its cost scales with the total examples. Keep numerator and denominator beside each rate, because a one-case change can matter more than a rounded percentage in a 137-image domain.',
    ['Do not put two captures of one physical receipt on opposite sides of a split.', 'Do not ship the adapted model because only the new-domain mean improved.', 'Do not save weights without the preprocessing and threshold that produced the accepted metrics.'],
    ['deep-learning/frozen-features-versus-fine-tuning', 'deep-learning/staged-unfreezing-and-domain-shift-audit', 'deep-learning/receipt-image-quality-project', 'deep-learning/residual-blocks-and-normalization-state', 'deep-learning/inference-schema-and-latency'], TRANSFER, True)

CROSSLINKS = [
    ('deep-learning/tensor-shape-dtype-contract', 'deep-learning/convolution-output-geometry-and-receptive-field'),
    ('deep-learning/receipt-image-quality-project', 'deep-learning/receipt-defect-localization-project'),
    ('deep-learning/augmentation-leakage-boundary', 'deep-learning/receipt-defect-localization-project'),
    ('deep-learning/train-eval-validation-loop', 'deep-learning/residual-blocks-and-normalization-state'),
    ('deep-learning/checkpoint-resume-state', 'deep-learning/residual-blocks-and-normalization-state'),
    ('deep-learning/gradient-accumulation-and-effective-batch', 'deep-learning/residual-blocks-and-normalization-state'),
    ('deep-learning/logits-loss-gradient', 'deep-learning/receipt-defect-localization-project'),
    ('deep-learning/batching-and-class-sampling', 'deep-learning/receipt-domain-adaptation-project'),
    ('deep-learning/inference-schema-and-latency', 'deep-learning/receipt-domain-adaptation-project'),
    ('deep-learning/mixed-precision-scaling-and-gradient-clipping', 'deep-learning/receipt-defect-localization-project'),
    ('deep-learning/receipt-training-memory-project', 'deep-learning/receipt-defect-localization-project'),
    ('deep-learning/deep-learning-tutorial', 'deep-learning/frozen-features-versus-fine-tuning'),
]

if __name__ == '__main__':
    publish(LESSONS, (CONV, TRANSFER), CROSSLINKS,
            'aitrove-deep-learning-cnn-transfer-import-20261006.json', 7830,
            subject='deep-learning')
