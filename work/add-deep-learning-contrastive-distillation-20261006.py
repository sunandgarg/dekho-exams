"""Add self-supervised representation and teacher-student training paths."""
from de_batch_publisher import publish

CONTRASTIVE = 'Self-supervised views and contrastive objectives'
DISTILLATION = 'Teacher-student distillation contracts'
LESSONS = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    assert len(sections) == 5
    LESSONS.append(dict(path='deep-learning/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add('contrastive-view-identity-and-augmentation-contract',
    'Contrastive view identity and augmentation contracts',
    'A self-supervised image pair is useful only when both views preserve the signal the downstream model must recognize and the split respects the original item.', [
    ('Name the unit of identity', 'Two crops from one photographed receipt are two views of one physical receipt, not two independent examples. Store a stable receipt identity before generating any crop, rotation, exposure change or compression artifact. Group the train and held-out split by that identity and, where possible, by capture session. A validation image copied into training under another filename will make representation quality appear better than it is. [[deep-learning/augmentation-leakage-boundary|The augmentation boundary]] applies before labels are considered, because a self-supervised objective can memorize near-duplicates too.'),
    ('Define which changes preserve meaning', 'A mild change in brightness may preserve a visible fold or cut-off edge. A crop that removes the edge does not. If the downstream task detects clipped receipts, making an original and a crop-without-the-clipping into a positive pair teaches the encoder to ignore the very defect of interest. Write a task-specific invariance table: allowed exposure shift, small perspective warp, blur range and crop coverage. Reject a proposed view transform when a reviewer cannot still identify the same defect. Generic image augmentation defaults are not a contract for document quality.'),
    ('Separate pairing from class labels', 'In a basic instance-discrimination task, the two views of the same source are positive; views of other sources in the batch act as negatives. That rule says nothing about whether two different receipts share a quality class. Pushing all other receipts apart may waste capacity or create false negatives, especially if multiple captures of one physical receipt have inconsistent identifiers. Track source and session IDs so obvious false negatives can be masked or the batch can be sampled differently. [[deep-learning/contrastive-temperature-and-negative-mask|The contrastive loss]] needs a precise positive index for every anchor.'),
    ('Audit the view generator', 'Sample and save paired previews at fixed seeds across lighting, device and defect slices. Calculate how often the generator produces an empty crop, saturates the image, erases a cut-off edge or makes both views nearly identical. Keep the generator configuration and code revision with the pretrained checkpoint. A model can optimize a shortcut in view-generation artifacts instead of learning receipt structure; paired visual audits and downstream ablations are more informative than one training loss curve. Record source ID, seed and transform parameters for failure replay.'),
    ('Evaluate transfer after pretraining', 'Freeze the encoder and train a small quality head on the labeled training population; then test a fine-tuned encoder under the same split. Compare against an encoder trained from scratch with equal downstream labels and compute budget. Report each defect slice, device slice and calibration, not just an average score. A contrastive objective can produce well-separated training embeddings yet fail to improve the decision the product makes. [[deep-learning/receipt-contrastive-pretraining-project|The project]] ties view design to that release test.')],
    '''from collections import defaultdict

receipt_records = [
    {"receipt_id": "r-047", "capture_id": "front", "split": "train"},
    {"receipt_id": "r-047", "capture_id": "tilted", "split": "train"},
    {"receipt_id": "r-083", "capture_id": "front", "split": "holdout"},
    {"receipt_id": "r-083", "capture_id": "low-light", "split": "holdout"},
]
splits_by_receipt = defaultdict(set)
for record in receipt_records:
    splits_by_receipt[record["receipt_id"]].add(record["split"])
assert all(len(assigned_splits) == 1 for assigned_splits in splits_by_receipt.values())

def pair_captures(records):
    grouped = defaultdict(list)
    for record in records:
        grouped[record["receipt_id"]].append(record["capture_id"])
    return {receipt_id: tuple(captures) for receipt_id, captures in grouped.items()
            if len(captures) >= 2}

positive_sources = pair_captures(receipt_records)
assert positive_sources["r-047"] == ("front", "tilted")''',
    'Generating two image views approximately doubles image preprocessing and encoder forward/backward work relative to one-view training. Storage can stay near one copy of each source if views are generated on demand, but deterministic replay requires seeds and transform records. Pair lookup and split auditing are O(N) in source records. Downstream evaluation is additional cost, not optional overhead: without it the pretrained representation has no verified application value.',
    ['Do not split two captures of one physical receipt across train and holdout.', 'Do not crop away a target defect and call the altered image an equivalent positive view.', 'Do not interpret other instances in a batch as guaranteed semantic negatives.'],
    ['deep-learning/augmentation-leakage-boundary', 'deep-learning/contrastive-temperature-and-negative-mask', 'deep-learning/receipt-contrastive-pretraining-project', 'deep-learning/receipt-defect-localization-project', 'deep-learning/frozen-features-versus-fine-tuning'], CONTRASTIVE)

add('contrastive-temperature-and-negative-mask',
    'Contrastive temperature and negative-mask accounting',
    'A two-view batch needs an exact positive index, a self-comparison mask and an explicit policy for duplicate identities before its loss means what the team thinks it means.', [
    ('Build the similarity matrix', 'Encode B source images twice, producing 2B projected embeddings. Normalize each vector, then form pairwise dot products; with normalized vectors those are cosine similarities. Divide by a positive temperature before applying a stable softmax cross entropy. The matched view for the first B anchors appears B positions later, while the second B anchors match B positions earlier. The diagonal is not a negative: an image has perfect similarity to itself and must be excluded. [[deep-learning/contrastive-view-identity-and-augmentation-contract|View identity]] determines those indices before tensor arithmetic.'),
    ('Account for negatives correctly', 'For each anchor, the denominator contains all other views except itself. It includes the matched positive once and the remaining 2B minus two views as apparent negatives. If two batch entries are captures of the same physical receipt, those apparent negatives can contradict the positive objective. Choose a batch sampler that keeps one source identity per batch, or construct an explicit multi-positive/masked loss. Merely hiding the duplicate from the positive index leaves it in the denominator and still pushes it away.'),
    ('Understand temperature without folklore', 'A smaller positive temperature makes a fixed similarity difference affect the softmax more strongly; gradients concentrate around difficult comparisons. Too small a value can make optimization brittle or encourage attention to mislabeled negatives. A larger value softens those comparisons but may produce weak separation. Select temperature on a development set using downstream transfer and representation diagnostics, not the lowest pretraining loss alone. Keep the projection head and encoder roles distinct: the head can absorb objective-specific geometry while the encoder supplies downstream features.'),
    ('Watch batch and distributed effects', 'The similarity matrix is quadratic in the number of views. Larger batches expose more negatives but increase memory and the chance of false negatives. In distributed training, gathering embeddings across ranks changes both the denominator and gradient flow; an implementation that gathers detached peer embeddings is not equivalent to one with fully differentiable gathering. Count unique source identities globally, define whether repeated sampler tail items contribute, and test a tiny reference batch. [[deep-learning/distributed-sampler-tail-and-global-loss-weighting|Sampler tails]] alter this objective in a less obvious way than a supervised mean loss.'),
    ('Check representation collapse and shortcuts', 'Track embedding variance per dimension, nearest-neighbor identities and positive-versus-negative similarity distributions. If every vector becomes almost identical, the objective or masking may be broken; if similarity separates only device type, the encoder may exploit capture metadata instead of receipt quality. Evaluate a frozen linear probe on labeled training data and a held-out physical-receipt set. The code below checks the exact two-view index algebra and computes one stable cross entropy. It is not a complete training system.')],
    '''import torch
from torch.nn import functional as functional

torch.manual_seed(47)
source_embeddings = torch.randn(5, 12)
first_views = source_embeddings + 0.04 * torch.randn_like(source_embeddings)
second_views = source_embeddings + 0.04 * torch.randn_like(source_embeddings)
projected_views = functional.normalize(
    torch.cat((first_views, second_views), dim=0), dim=1)
temperature = 0.23
similarities = projected_views @ projected_views.T / temperature
self_mask = torch.eye(len(projected_views), dtype=torch.bool)
similarities = similarities.masked_fill(self_mask, float("-inf"))
positive_indices = (torch.arange(len(projected_views)) + 5) % 10
contrastive_loss = functional.cross_entropy(similarities, positive_indices)
assert torch.isfinite(contrastive_loss)
assert positive_indices.tolist() == [5, 6, 7, 8, 9, 0, 1, 2, 3, 4]''',
    'For B identities and d-dimensional projections, the similarity multiply costs O(B²d) time and O(B²) matrix memory. Two encoder views also require roughly twice the encoding work of one-view training. This small dense implementation is useful for checking indexing, but a large multiworker job may need chunked similarities or another negative-sampling design. Temperature changes arithmetic, not asymptotic cost; a larger global batch can dominate memory even if the encoder itself fits.',
    ['Do not include the diagonal self-similarity as a negative or positive.', 'Do not allow duplicate physical receipts to become unexamined false negatives.', 'Do not compare losses at different temperatures as if they were on one fixed scale.'],
    ['deep-learning/contrastive-view-identity-and-augmentation-contract', 'deep-learning/receipt-contrastive-pretraining-project', 'deep-learning/distributed-sampler-tail-and-global-loss-weighting', 'deep-learning/batching-and-class-sampling', 'deep-learning/frozen-features-versus-fine-tuning'], CONTRASTIVE)

add('receipt-contrastive-pretraining-project',
    'Project: pretrain receipt features from unlabeled captures',
    'Use paired views of unlabeled receipts to train an encoder, then test whether those features improve scarce-label receipt-quality decisions on untouched physical receipts.', [
    ('Freeze identities and baselines', 'Create a manifest with physical receipt ID, capture session, device and any available defect label. Split by physical receipt before augmenting, and reserve the final test group from all pretraining, hyperparameter selection and nearest-neighbor inspection. Establish two downstream baselines: a quality model trained from scratch and a frozen generic feature encoder, both with the same labeled examples. The project is about incremental value from receipt-specific unlabeled captures, not about obtaining a low unsupervised loss. [[deep-learning/augmentation-leakage-boundary|Split discipline]] applies to every unlabeled capture.'),
    ('Specify the paired-view rule', 'Generate two mild views of each pretraining image while preserving visible clipped edges, blur and folds. Reject transforms that erase a defect or expose nonreceipt metadata as a shortcut. Sample at most one physical receipt per batch unless a multi-positive objective is implemented. Store fixed-seed view previews for a device and defect audit. The same source image must remain identifiable across views, but two views should not be byte-identical. [[deep-learning/contrastive-view-identity-and-augmentation-contract|The view contract]] defines allowed variation.'),
    ('Train with an indexed loss', 'Pass both views through a shared encoder and projection head. Normalize projected vectors, mask self-similarity, map each anchor to its other view and calculate cross entropy. The snippet uses a small dense encoder and one step on synthetic features to demonstrate this contract; actual receipt images require image preprocessing and a suitable convolutional or attention encoder. Log global unique identities, positive similarities, apparent-negative similarities, embedding variance and loss. [[deep-learning/contrastive-temperature-and-negative-mask|The loss lesson]] explains the denominator.'),
    ('Measure transfer under scarce labels', 'Train a frozen linear head using the same limited label budget for every encoder. Then fine-tune an encoder separately, keeping the final test untouched. Report class recall, false accepts, confidence coverage and device breakdown. Compare results across at least two label budgets; a representation can help when labels are scarce and make little difference when labels are plentiful. Inspect nearest neighbors for false similarity based on paper color or camera border rather than quality. Do not select the winning temperature by the final test.'),
    ('Deliver a reproducible artifact', 'Save the source manifest hash, view generator configuration, batch identity rule, encoder and head revisions, projection-head handling and downstream split IDs. The projection head used for the contrastive objective need not be the downstream feature API; document which tensor is exported. Add a fixed-batch reload check and a table of paired baselines. If held-out recall does not improve, publish the negative result as a boundary of the method rather than substituting an easier metric. [[deep-learning/receipt-confidence-audit-project|The confidence audit]] catches cost shifted into human review.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

torch.manual_seed(47)
receipt_vectors = torch.randn(6, 16)
view_a = receipt_vectors + 0.03 * torch.randn_like(receipt_vectors)
view_b = receipt_vectors + 0.05 * torch.randn_like(receipt_vectors)
encoder = nn.Sequential(nn.Linear(16, 24), nn.ReLU(), nn.Linear(24, 12))
projection = nn.Linear(12, 8)
optimizer = torch.optim.AdamW(list(encoder.parameters()) +
                              list(projection.parameters()), lr=0.0007)
projected = functional.normalize(projection(encoder(torch.cat((view_a, view_b)))), dim=1)
scores = projected @ projected.T / 0.27
scores.fill_diagonal_(float("-inf"))
positive_index = (torch.arange(12) + 6) % 12
optimizer.zero_grad(set_to_none=True)
loss = functional.cross_entropy(scores, positive_index)
loss.backward()
optimizer.step()
assert torch.isfinite(loss)
assert projected.shape == (12, 8)''',
    'The encoder runs once per view and stores both computational graphs for backpropagation. Pairwise scores require O(B²d) multiply work and O(B²) memory for B receipt identities and projection width d. The toy dense network is small; a real image encoder usually dominates compute. Preparing fixed-seed visual audits and downstream label-budget comparisons adds work, but those checks determine whether pretraining helped the product rather than merely optimizing a proxy loss.',
    ['Do not pretrain on final-test receipt identities and call the later evaluation untouched.', 'Do not export the projection tensor as the downstream feature without checking that choice.', 'Do not use a view transform that removes the rare defect whose recall is being measured.'],
    ['deep-learning/contrastive-view-identity-and-augmentation-contract', 'deep-learning/contrastive-temperature-and-negative-mask', 'deep-learning/frozen-features-versus-fine-tuning', 'deep-learning/receipt-image-quality-project', 'deep-learning/receipt-confidence-audit-project'], CONTRASTIVE, True)

add('distillation-soft-target-temperature-and-label-balance',
    'Distillation soft targets, temperature and label balance',
    'A student can learn from a frozen teacher distribution and real labels, but the temperature, class map and loss reductions must be fixed before comparing candidates.', [
    ('Freeze a trustworthy teacher', 'Distillation transfers a teacher’s behavior, including its blind spots. Evaluate the teacher on physical-receipt holdouts and rare defects before using it as supervision. Freeze its weights, put it in evaluation mode and record preprocessing, class order and revision. The student must see the same input semantics, even if its architecture is smaller. A teacher whose class index two means clipped receipt cannot supervise a student whose index two means blurred receipt. [[deep-learning/receipt-image-quality-project|The quality task]] supplies a concrete class map and held-out identity rule.'),
    ('Separate hard and soft objectives', 'The hard-label term compares unscaled student logits with human labels. The soft term compares the teacher and student distributions after both logits are divided by the same positive temperature. A common choice is teacher-to-student KL divergence with batch-mean reduction and a temperature-squared factor, which keeps gradient scale more comparable as temperature changes. Combine the terms with declared weights. Do not feed teacher probabilities into a loss expecting integer class IDs. [[deep-learning/logits-loss-gradient|Logit and loss contracts]] determine which tensor each term accepts.'),
    ('Interpret the temperature', 'At temperature one, a confident teacher may assign almost no probability to alternatives. Raising temperature reveals relative preferences between non-top classes, but excessive smoothing can make the distribution close to uniform and uninformative. It does not improve teacher correctness. Compare temperatures using a development split and check class-specific student errors. The code below calculates one combined training step with a frozen teacher and verifies that only the student is updated. Teacher inference adds training cost but is absent from the final student inference path.'),
    ('Guard against teacher error', 'A teacher can be confidently wrong on clipped edges or unusual capture devices. Inspect teacher disagreement with human labels by slice, and decide whether to downweight its soft loss for those records or obtain better labels. Never silently replace hard labels with teacher top classes. If teacher probabilities are cached, tie each row to receipt identity, preprocessing hash, teacher revision and class map; stale caches can train the student on the wrong image after an augmentation change. A student may surpass a teacher on some slices, but this must be measured rather than assumed.'),
    ('Evaluate the intended deployment', 'Train a student from scratch with hard labels and another with the declared mixture, holding architecture, label set and training budget constant. Compare top-class accuracy, rare-defect recall, confidence quality, artifact size and actual target-device latency. Calibrate student probabilities separately after training if decisions use confidence; the distillation temperature is a training parameter, not automatically the serving calibration temperature. [[deep-learning/receipt-student-distillation-project|The applied release]] pairs the student comparison with edge constraints.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

torch.manual_seed(47)
receipt_features = torch.randn(7, 9)
quality_labels = torch.tensor([0, 2, 1, 2, 0, 1, 2])
teacher = nn.Sequential(nn.Linear(9, 28), nn.ReLU(), nn.Linear(28, 3))
student = nn.Sequential(nn.Linear(9, 11), nn.ReLU(), nn.Linear(11, 3))
teacher.eval()
for parameter in teacher.parameters():
    parameter.requires_grad_(False)
optimizer = torch.optim.AdamW(student.parameters(), lr=0.0008)
temperature = 2.3
with torch.no_grad():
    teacher_logits = teacher(receipt_features)
student_logits = student(receipt_features)
teacher_targets = functional.softmax(teacher_logits / temperature, dim=1)
student_log_probs = functional.log_softmax(student_logits / temperature, dim=1)
soft_loss = functional.kl_div(student_log_probs, teacher_targets,
                              reduction="batchmean") * temperature**2
hard_loss = functional.cross_entropy(student_logits, quality_labels)
training_loss = 0.38 * soft_loss + 0.62 * hard_loss
optimizer.zero_grad(set_to_none=True)
training_loss.backward()
optimizer.step()
assert all(parameter.grad is None for parameter in teacher.parameters())
assert torch.isfinite(training_loss)''',
    'Training adds one teacher forward per student batch and stores student activations for backward propagation; a frozen teacher does not need an autograd graph. Cached teacher logits can reduce repeated teacher compute but require storage O(NC) for N records and C classes, plus strict identity and preprocessing versioning. Student inference cost depends only on the student graph. The temperature and KL operations are O(BC) per batch, usually small beside neural forward passes. Measure the final device path rather than inferring speed from parameter count.',
    ['Do not let gradients or training-mode statistics update the teacher.', 'Do not reuse the training temperature as an untested serving calibration value.', 'Do not accept teacher predictions as ground truth when they conflict with reviewed labels.'],
    ['deep-learning/logits-loss-gradient', 'deep-learning/teacher-feature-adapter-and-layer-alignment', 'deep-learning/receipt-student-distillation-project', 'deep-learning/post-training-quantization-calibration-contract', 'deep-learning/temperature-scaling-and-selective-risk'], DISTILLATION)

add('teacher-feature-adapter-and-layer-alignment',
    'Teacher feature adapters and layer alignment',
    'Matching internal teacher features can guide a narrow student, but dimensions, spatial resolution and representation scale must be reconciled deliberately.', [
    ('Choose an internal comparison point', 'A teacher and student need not have matching depth or hidden width. Select a teacher feature after a stable block and a student feature with related receptive field or semantic role. For image networks, an early edge detector should not be forced to match a late global decision representation without a reason. Record layer names, pre- or post-activation choice, spatial shape and normalization behavior. Freeze the teacher and capture features under the same input preprocessing. [[deep-learning/convolution-output-geometry-and-receptive-field|Convolution geometry]] explains why stride changes spatial support.'),
    ('Map shapes with a learned adapter', 'If student features have twelve channels and teacher features have twenty-four, use a small projection such as a linear layer or one-by-one convolution to map the student feature into the teacher space. Match spatial resolution with a documented pooling or interpolation rule when needed. Train the adapter with the student and exclude it from final inference if it is used only for the auxiliary loss. A shape-compatible projection does not prove semantic alignment; compare downstream decisions and feature variance. The code uses vector features so the shape contract is visible.'),
    ('Normalize the auxiliary objective', 'Raw mean squared error can be dominated by teacher feature magnitude. Normalize features or choose an explicit weighting so the auxiliary term does not swamp human-label loss. Report each loss separately and inspect gradient norms for student backbone, adapter and classifier. A near-zero feature loss might mean the adapter learned a trivial mapping or the teacher features had low variance. Use a feature collapse check and compare a logit-only distillation baseline. [[deep-learning/distillation-soft-target-temperature-and-label-balance|Soft-target learning]] is a simpler reference.'),
    ('Handle residual and spatial differences', 'For convolutional teachers, feature width may vary along with height and width. Interpolation can blur local defects while pooling can discard them; neither is neutral. Prefer comparison points with similar effective receptive fields, and inspect cut-off edges after any resize. If a teacher has residual connections or normalization running state, extraction must come from the intended post-block tensor. Verify hooks are removed after use and do not retain tensors across batches, which can leak memory in long training runs.'),
    ('Test whether the hint helps', 'Train equal-budget students with hard labels alone, hard plus soft logits, and hard plus soft plus feature alignment. Select objective weights on a development split, then report a held-out defect table and device latency. The adapter can be thrown away at serving time only if the exported student output does not depend on it. Keep a fixed-input parity check for the exported graph. A teacher hint that raises average accuracy but degrades an important rare defect is not a successful transfer. [[deep-learning/receipt-student-distillation-project|The student project]] uses this ablation.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

torch.manual_seed(47)
receipt_features = torch.randn(5, 9)
teacher_backbone = nn.Sequential(nn.Linear(9, 24), nn.ReLU())
student_backbone = nn.Sequential(nn.Linear(9, 12), nn.ReLU())
feature_adapter = nn.Linear(12, 24)
for parameter in teacher_backbone.parameters():
    parameter.requires_grad_(False)
teacher_backbone.eval()
with torch.no_grad():
    teacher_features = teacher_backbone(receipt_features)
student_features = student_backbone(receipt_features)
aligned_student = feature_adapter(student_features)
hint_loss = functional.mse_loss(functional.normalize(aligned_student, dim=1),
                                functional.normalize(teacher_features, dim=1))
hint_loss.backward()
assert aligned_student.shape == teacher_features.shape == (5, 24)
assert all(parameter.grad is None for parameter in teacher_backbone.parameters())
assert torch.isfinite(hint_loss)''',
    'The adapter adds O(Bdsdt) multiply work for batch B, student width ds and teacher width dt in this dense example, as well as a teacher forward during training. A spatial adapter has additional height and width factors. Feature storage and hooks can raise training memory substantially if several layers are compared. If the adapter serves only the loss, it can be omitted from the final student graph; verify that omission in a clean export. Extra auxiliary compute is justified only by measured held-out gains or a better release tradeoff.',
    ['Do not align unrelated layer positions solely because their tensors can be resized.', 'Do not allow adapter output magnitude to dominate the hard-label objective.', 'Do not claim a smaller serving model until the adapter is absent from the exported graph.'],
    ['deep-learning/distillation-soft-target-temperature-and-label-balance', 'deep-learning/receipt-student-distillation-project', 'deep-learning/convolution-output-geometry-and-receptive-field', 'deep-learning/structured-pruning-and-latency-parity', 'deep-learning/inference-schema-and-latency'], DISTILLATION)

add('receipt-student-distillation-project',
    'Project: distill and release a receipt-quality student',
    'Transfer a reviewed teacher into a smaller receipt classifier, then prove that the student meets class-specific decision and device limits before release.', [
    ('Pin teacher, student and populations', 'Freeze a teacher trained only on the allowed training receipts and verify its class map, preprocessing and held-out defect behavior. Choose a smaller student architecture before tuning distillation weights. Partition physical receipts into training, development, calibration and final test identities; do not reuse the final test to select temperature or channels. Train a hard-label-only student as a fair baseline. [[deep-learning/distillation-soft-target-temperature-and-label-balance|The soft-target contract]] fixes the teacher-to-student objective.'),
    ('Run controlled ablations', 'Use the same student initialization policy, training examples and update budget for hard labels alone, hard plus teacher logits, and an optional feature-hint variant. Freeze teacher parameters and keep it in evaluation mode for every run. Save class-map and preprocessing hashes with cached logits if caching is used. Check that training loss reduction is not merely copying teacher errors on clipped receipts. [[deep-learning/teacher-feature-adapter-and-layer-alignment|Feature alignment]] adds an adapter that must not sneak into the exported classifier.'),
    ('Measure decisions by slice', 'On development data compare quality-class recall, false accepts and teacher-student disagreement, including low light, blur, clipped edges and capture devices. Fit any serving calibration on a separate calibration group and choose a manual-review threshold before opening final test. The code below counts disagreements and errors for a fixed synthetic audit batch; it is a metric-definition check rather than evidence that a real student passed. [[deep-learning/temperature-scaling-and-selective-risk|Selective risk]] defines the review tradeoff.'),
    ('Test the target runtime', 'Export the student without training-only teacher and adapter layers. Reload it in a clean process and compare fixed-batch logits with its pre-export graph. Measure cold-start, resident memory, median and tail latency with preprocessing at the intended device batch size. A narrow student may still be slower if its operators lack efficient kernels. Compare a later quantized student as a separate candidate, calibrating it on representative data and rerunning the same final gates. [[deep-learning/receipt-edge-model-release-project|The edge release]] supplies the device gate pattern.'),
    ('Make failure visible', 'Set acceptable rare-defect recall loss, false-accept count, review workload, memory and 95th-percentile latency before final test. If the distilled student fails one gate, keep the teacher or hard-label student as appropriate; do not compensate by reporting only average accuracy. Deliver the ablation table, disagreement examples, class-map manifest, calibration fit, exported-graph parity and rollback bundle. A smaller model is an engineering option, not a reason to hide changed decisions from operators.')],
    '''import torch

teacher_logits = torch.tensor([[3.1, 0.4, -0.2], [0.2, 0.8, 2.1],
                               [0.1, 2.5, 0.3], [1.3, 0.9, 0.4],
                               [0.4, 0.6, 1.8], [2.0, 0.5, 0.3]])
student_logits = torch.tensor([[2.7, 0.5, 0.1], [0.2, 1.4, 1.3],
                               [0.3, 2.0, 0.4], [1.1, 1.3, 0.5],
                               [0.3, 0.6, 1.4], [1.8, 0.7, 0.2]])
reviewed_labels = torch.tensor([0, 2, 1, 0, 2, 0])
teacher_decisions = teacher_logits.argmax(dim=1)
student_decisions = student_logits.argmax(dim=1)
disagreement = teacher_decisions.ne(student_decisions)
student_errors = student_decisions.ne(reviewed_labels)
teacher_errors = teacher_decisions.ne(reviewed_labels)
audit = {"teacher_errors": int(teacher_errors.sum()),
         "student_errors": int(student_errors.sum()),
         "disagreements": int(disagreement.sum())}
assert audit == {"teacher_errors": 0, "student_errors": 2, "disagreements": 2}''',
    'Distillation pays for teacher inference during student training but deploys only the student. Feature-hint experiments add adapter and teacher-feature storage, while calibration and device benchmarking add separate work. The six-record code audit is O(NC) for N records and C classes and cannot estimate population error. Real release tests need adequate counts in rare slices and repeated tail-latency measurements. Measure end-to-end device cost; a parameter ratio is not a latency guarantee.',
    ['Do not select distillation settings on final-test receipts.', 'Do not package the teacher or feature adapter into a student-only latency claim.', 'Do not hide a clipped-edge false accept behind a lower aggregate error count.'],
    ['deep-learning/distillation-soft-target-temperature-and-label-balance', 'deep-learning/teacher-feature-adapter-and-layer-alignment', 'deep-learning/receipt-edge-model-release-project', 'deep-learning/receipt-confidence-audit-project', 'deep-learning/receipt-image-quality-project'], DISTILLATION, True)

CROSSLINKS = [
    ('deep-learning/augmentation-leakage-boundary', 'deep-learning/contrastive-view-identity-and-augmentation-contract'),
    ('deep-learning/batching-and-class-sampling', 'deep-learning/contrastive-temperature-and-negative-mask'),
    ('deep-learning/distributed-sampler-tail-and-global-loss-weighting', 'deep-learning/contrastive-temperature-and-negative-mask'),
    ('deep-learning/frozen-features-versus-fine-tuning', 'deep-learning/receipt-contrastive-pretraining-project'),
    ('deep-learning/receipt-defect-localization-project', 'deep-learning/contrastive-view-identity-and-augmentation-contract'),
    ('deep-learning/receipt-image-quality-project', 'deep-learning/receipt-contrastive-pretraining-project'),
    ('deep-learning/logits-loss-gradient', 'deep-learning/distillation-soft-target-temperature-and-label-balance'),
    ('deep-learning/convolution-output-geometry-and-receptive-field', 'deep-learning/teacher-feature-adapter-and-layer-alignment'),
    ('deep-learning/post-training-quantization-calibration-contract', 'deep-learning/receipt-student-distillation-project'),
    ('deep-learning/receipt-edge-model-release-project', 'deep-learning/receipt-student-distillation-project'),
    ('deep-learning/receipt-confidence-audit-project', 'deep-learning/receipt-student-distillation-project'),
    ('deep-learning/deep-learning-tutorial', 'deep-learning/receipt-student-distillation-project'),
]

if __name__ == '__main__':
    publish(LESSONS, (CONTRASTIVE, DISTILLATION), CROSSLINKS,
            'aitrove-deep-learning-contrastive-distillation-import-20261006.json',
            7870, subject='deep-learning')
