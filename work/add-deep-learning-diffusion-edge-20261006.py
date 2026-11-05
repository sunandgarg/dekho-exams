"""Add diffusion and edge-inference lessons with applied receipt projects."""
from de_batch_publisher import publish

DIFFUSION = 'Diffusion training and sampling contracts'
EDGE = 'Compression and edge release'
LESSONS = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    assert len(sections) == 5
    LESSONS.append(dict(path='deep-learning/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add('diffusion-forward-noise-and-timestep-target',
    'Diffusion forward noise and timestep targets',
    'A noise predictor is trained against a precisely defined corruption schedule; changing the schedule or target at inference creates a different problem.', [
    ('Define the clean-data contract', 'Start with a frozen image transform, value range and channel order. For receipt backgrounds, that may mean one grayscale channel scaled to minus one through one, with text and personal information removed before training. Split physical receipts before creating crops. The clean image x0, sampled Gaussian noise epsilon and integer timestep t are three distinct pieces of the training record. Save the transform version beside the noise schedule. A model trained on centered pixels will not interpret raw byte-valued pixels correctly. [[deep-learning/receipt-image-quality-project|The receipt classifier]] uses its own preprocessing contract.'),
    ('Derive one noisy image directly', 'Choose beta at each training timestep and define alpha as one minus beta. The cumulative product alpha_bar[t] records how much clean signal remains after t. Then x_t equals square-root alpha_bar[t] times x0 plus square-root one-minus-alpha_bar[t] times epsilon. Sampling x_t in one expression avoids iterating through every earlier corruption step during training. It also makes an exact reconstruction check possible when x0 and epsilon are retained. A different beta table changes the meaning of the same integer timestep, even if image shape and model weights match.'),
    ('Choose the prediction target explicitly', 'A basic noise-prediction objective asks the network for epsilon and scores its output against the exact sampled epsilon, often with mean squared error. Other parameterizations predict a clean sample or a velocity-like combination; their conversions and loss weights differ. Store the target type in the artifact and never infer it from a filename. Timestep embeddings must receive the same indexing convention at train and inference time. If one implementation calls the first step zero and another calls it one, their noise levels no longer line up. [[deep-learning/logits-loss-gradient|Loss contracts]] matter more than a convenient tensor shape.'),
    ('Inspect the schedule endpoints', 'Inspect the lowest and highest alpha_bar values as well as images at early, middle and late steps. A late image that still exposes every receipt line may not be a useful near-noise endpoint; an early image that loses text structure immediately may make small-step training harder. Do not judge the schedule only from a graph of beta values. Check that every beta lies strictly between zero and one, that alpha_bar decreases, and that the calculation stays finite in the chosen precision. Keep schedule construction in full precision if a low-precision cumulative product underflows.'),
    ('Audit the sampling distribution', 'Uniformly sampled timesteps give every index equal training frequency, but equal frequency is not equal difficulty. Report loss by timestep bucket rather than only one average. Record the seed, sampled timestep, noise tensor identity and image identity for a small reproducible audit batch. Augmentation must happen before corruption so the target noise still matches the image being scored. If a training transform edits x_t after epsilon was drawn, the original epsilon is no longer the exact target. [[deep-learning/diffusion-reverse-step-and-guidance|Reverse stepping]] relies on this same schedule.')],
    '''import torch

torch.manual_seed(47)
clean_receipts = torch.rand(3, 1, 8, 8) * 2 - 1
beta_schedule = torch.linspace(0.001, 0.047, 47, dtype=torch.float64)
alpha_retained = torch.cumprod(1.0 - beta_schedule, dim=0)
sampled_steps = torch.tensor([4, 23, 46])
signal = alpha_retained[sampled_steps].sqrt().view(-1, 1, 1, 1)
noise_scale = (1 - alpha_retained[sampled_steps]).sqrt().view(-1, 1, 1, 1)
sampled_noise = torch.randn_like(clean_receipts)
noisy_receipts = signal * clean_receipts + noise_scale * sampled_noise
recovered_clean = (noisy_receipts - noise_scale * sampled_noise) / signal
torch.testing.assert_close(recovered_clean, clean_receipts, atol=1e-6, rtol=1e-6)
assert bool(torch.all(alpha_retained[1:] < alpha_retained[:-1]))''',
    'The direct corruption step is O(BCHW) for batch size B and image shape C by H by W, plus O(T) schedule construction for T timesteps. Training cost is dominated by one network forward and backward pass per batch. Keeping a full tensor of independently noised copies for every timestep would multiply image storage by T without improving this objective. The code uses float64 for the schedule audit; production may cast selected coefficients to model dtype after constructing and checking them.',
    ['Do not reuse a checkpoint with an altered beta schedule or prediction target.', 'Do not normalize x0 twice while leaving epsilon unchanged.', 'Do not assume low loss at easy timesteps implies adequate denoising at late steps.'],
    ['deep-learning/logits-loss-gradient', 'deep-learning/train-eval-validation-loop', 'deep-learning/diffusion-reverse-step-and-guidance', 'deep-learning/receipt-background-diffusion-project', 'deep-learning/receipt-image-quality-project'], DIFFUSION)

add('diffusion-reverse-step-and-guidance',
    'Diffusion reverse steps and conditional guidance',
    'A reverse update combines the predicted noise with the exact training schedule; guidance adds a second prediction whose training meaning must be known.', [
    ('Recover a clean estimate first', 'For an epsilon-predicting model, estimate x0 by subtracting the predicted noise contribution from x_t and dividing by the retained-signal coefficient. This estimate is not guaranteed to lie in the training image range, particularly under strong guidance or at a high-noise step. Decide whether and where to clip it, then keep that choice fixed during evaluation. A deterministic reverse update can combine the clean estimate and predicted noise at an earlier alpha_bar value. It is one sampler rule, not a claim that all diffusion samplers are interchangeable. [[deep-learning/diffusion-forward-noise-and-timestep-target|The forward schedule]] defines these coefficients.'),
    ('Define conditional and unconditional branches', 'Classifier-free guidance requires a predictor that has learned to operate both with and without the condition. During training, deliberately replace a documented fraction of conditions with a null condition; during sampling, run the same model with the null and requested conditions. Combine outputs as unconditional plus guidance-scale times conditional-minus-unconditional. A scale of one yields the conditional prediction in this convention. An arbitrary empty string or zero vector is not automatically the trained null representation. For structured receipt metadata, reserve an explicit null token and test it.'),
    ('Price the guidance choice', 'The two branches can often be evaluated in one doubled batch, but they still perform roughly twice the model work and may raise peak memory. Raising guidance can make requested attributes more visible while reducing variety or pushing values outside the trained range. Evaluate fidelity and diversity together. If the condition names a receipt defect, inspect whether generated images contain that defect rather than merely shifting brightness. A guidance scale tuned for one schedule, resolution or model revision is not a universal number.'),
    ('Keep the timestep trajectory explicit', 'A sampler may skip training indices to reduce latency. Store the ordered inference indices, the scheduler rule and endpoint convention with the generated artifact. A jump from step 46 to 23 is not the same update as 46 to 45. The code below demonstrates a deterministic transition from step 23 to 22 and does not add stochastic posterior variance. It uses dummy predictions to check algebra; a trained network must supply them in deployment. Run a fixed-noise replay after any scheduler change and compare output distributions, not just one pleasing image.'),
    ('Gate synthetic data use', 'Generated receipt backgrounds can help stress a downstream quality classifier, but they must not leak holdout receipts or replace evaluation on real captures. Audit near-duplicates against training inputs, visible personal fields, class labels and capture-device mix. Report downstream error on real held-out receipts with and without generated augmentation. If synthetic training improves average accuracy while making a rare cut-off class worse, the project fails its intended purpose. [[deep-learning/receipt-background-diffusion-project|The applied project]] makes these gates concrete.')],
    '''import torch

beta_schedule = torch.linspace(0.001, 0.047, 47, dtype=torch.float64)
alpha_retained = torch.cumprod(1 - beta_schedule, dim=0)
noisy_receipt = torch.full((1, 1, 8, 8), 0.18, dtype=torch.float64)
unconditional_noise = torch.full_like(noisy_receipt, 0.04)
conditional_noise = torch.full_like(noisy_receipt, 0.07)
guidance_scale = 1.7
guided_noise = unconditional_noise + guidance_scale * (
    conditional_noise - unconditional_noise)
current_step, previous_step = 23, 22
clean_estimate = (noisy_receipt -
                  (1 - alpha_retained[current_step]).sqrt() * guided_noise
                  ) / alpha_retained[current_step].sqrt()
previous_receipt = (alpha_retained[previous_step].sqrt() * clean_estimate +
                    (1 - alpha_retained[previous_step]).sqrt() * guided_noise)
assert previous_receipt.shape == noisy_receipt.shape
assert torch.isfinite(previous_receipt).all()''',
    'For K reverse steps, one conditional pass per step costs roughly K model forwards; guidance normally needs two predictions per step, so model compute is near 2K forwards. Activation batching may improve throughput without eliminating the work. Memory depends on implementation: a combined conditional/unconditional batch can double activations, while sequential calls add latency. The algebraic tensor operations shown here are O(BCHW) per step and are usually much cheaper than the denoiser.',
    ['Do not request an unconditional prediction from a model never trained with null conditions.', 'Do not swap timestep schedules while keeping the old model checkpoint.', 'Do not treat a deterministic one-step example as a complete stochastic sampler.'],
    ['deep-learning/diffusion-forward-noise-and-timestep-target', 'deep-learning/receipt-background-diffusion-project', 'deep-learning/temperature-scaling-and-selective-risk', 'deep-learning/inference-schema-and-latency', 'deep-learning/receipt-defect-localization-project'], DIFFUSION)

add('receipt-background-diffusion-project',
    'Project: train and audit a receipt-background denoiser',
    'Build a small conditional noise predictor for synthetic receipt backgrounds, then reject memorization and prove downstream value on real held-out captures.', [
    ('Specify the limited target', 'Produce grayscale background texture only, with text, merchant names, dates and identifiers removed before any model training. Hold out entire physical receipts, not crops, and freeze a 47-step schedule with the exact input scaling and condition vocabulary. The condition in this exercise is a coarse paper-contrast value. The 8 by 8 network below demonstrates one noise-prediction update, not a production image generator; real texture synthesis needs more receptive field, data and evaluation. [[deep-learning/diffusion-forward-noise-and-timestep-target|The forward-noise contract]] establishes the target.'),
    ('Train both condition modes', 'Draw a clean synthetic background, sample an integer timestep and fresh Gaussian noise, then construct x_t. Append the normalized timestep and contrast condition to the flattened noisy image. Drop the contrast condition for a recorded subset of updates and supply a separate null flag, so the network can distinguish missing conditioning from a genuine zero-contrast request. Score predicted epsilon against the exact sampled epsilon. Log loss by timestep bucket and condition-present status; an aggregate loss can hide a branch that never learns.'),
    ('Build a fixed-noise sampling audit', 'After training, sample from fixed seeded noise using one documented reverse trajectory. Compare guidance scale one against a stronger scale while holding the noise seed, model and schedule constant. Inspect range violations, near-constant outputs and diversity across seeds. Do not advertise low training loss as proof of image quality. Record model revision, preprocessing and scheduler config with every generated set. [[deep-learning/diffusion-reverse-step-and-guidance|Reverse guidance]] describes the two predictions required at each step.'),
    ('Check privacy and duplication', 'Search generated backgrounds for nearest training-image neighbors using several measures, including raw-pixel distance after alignment and a feature representation. Manually review the closest pairs; a distance threshold alone does not certify absence of memorized text. Keep an immutable list of excluded personal fields and check source permissions before training. If background removal left a faint account number, synthetic release must stop even if the denoising objective is numerically correct. Distinct synthetic seeds are not proof of distinct real-world information.'),
    ('Measure a downstream decision', 'Train the same receipt-quality classifier twice: once with real data alone, once with the approved synthetic backgrounds used only as training augmentation. Keep the real held-out receipt set and threshold-selection policy fixed. Report blur and cut-off recall, false accepts, calibration and device slices. Reject the synthetic set if it worsens an agreed safety slice or offers no repeatable gain. Deliver the schedule, training manifest, nearest-neighbor audit and paired classifier results. [[deep-learning/receipt-confidence-audit-project|Confidence review]] can expose harmful shifts masked by one accuracy figure.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

torch.manual_seed(47)
backgrounds = torch.rand(4, 1, 8, 8) * 2 - 1
paper_contrast = torch.tensor([[0.2], [0.7], [0.4], [0.9]])
beta_schedule = torch.linspace(0.001, 0.047, 47)
alpha_retained = torch.cumprod(1 - beta_schedule, dim=0)
sampled_steps = torch.randint(0, 47, (4,))
sampled_noise = torch.randn_like(backgrounds)
signal = alpha_retained[sampled_steps].sqrt().view(4, 1, 1, 1)
noise_scale = (1 - alpha_retained[sampled_steps]).sqrt().view(4, 1, 1, 1)
noisy_backgrounds = signal * backgrounds + noise_scale * sampled_noise
condition_present = torch.tensor([[1.0], [0.0], [1.0], [0.0]])
condition_value = paper_contrast * condition_present
model_inputs = torch.cat((noisy_backgrounds.flatten(1),
                          sampled_steps.float().unsqueeze(1) / 46,
                          condition_value, condition_present), dim=1)
noise_predictor = nn.Sequential(nn.Linear(67, 96), nn.ReLU(), nn.Linear(96, 64))
optimizer = torch.optim.AdamW(noise_predictor.parameters(), lr=0.001)
optimizer.zero_grad(set_to_none=True)
predicted_noise = noise_predictor(model_inputs).view_as(sampled_noise)
training_loss = functional.mse_loss(predicted_noise, sampled_noise)
training_loss.backward()
optimizer.step()
assert torch.isfinite(training_loss)''',
    'This illustrative dense predictor has forward cost proportional to the input width times 96 plus 96 times 64 per sample, and it stores activations for backpropagation. A realistic image denoiser is much more expensive and repeats a forward pass for every sampling step; conditional guidance typically adds another pass. Nearest-neighbor checks also require a search over generated and training images, so define an audit sample and indexing plan before scaling output volume. The project accepts no speed or privacy claim from the tiny code example.',
    ['Do not train on receipt text and assume later generation is private.', 'Do not reuse validation receipts as generator training data or augmentation seeds.', 'Do not infer downstream utility from denoising loss or visual appeal alone.'],
    ['deep-learning/diffusion-forward-noise-and-timestep-target', 'deep-learning/diffusion-reverse-step-and-guidance', 'deep-learning/receipt-image-quality-project', 'deep-learning/receipt-confidence-audit-project', 'deep-learning/staged-unfreezing-and-domain-shift-audit'], DIFFUSION, True)

add('post-training-quantization-calibration-contract',
    'Post-training quantization and calibration contracts',
    'Smaller integer weights are useful only when calibration data, operator support and held-out decisions survive conversion to the target runtime.', [
    ('Separate weight rounding from executable quantization', 'Quantization maps a real range to integer codes through a scale and sometimes a zero point. A symmetric signed eight-bit weight mapping can use a separate scale for each output channel. That reduces rounding error when channels have different ranges. The code below performs a transparent weight round-trip and measures reconstruction error. It does not produce an integer inference kernel: multiplying restored floating-point weights still runs floating-point arithmetic. A deployable conversion also needs supported operators, activation handling and a target-specific runtime. [[deep-learning/inference-schema-and-latency|Inference contracts]] include these choices.'),
    ('Choose representative calibration traffic', 'For post-training static activation quantization, observers estimate activation ranges from a representative calibration set. Select data after the same preprocessing used at deployment, covering normal receipts, blur, cut-off edges, exposure extremes and capture devices. Keep calibration separate from final test identities and labels used for release decisions. A set of random tensors can exercise code paths but cannot characterize real activation ranges. Record sample count, collection window, device mix, preprocessing hash and observer configuration. Drift in those inputs can make a previously acceptable scale harmful.'),
    ('Inspect outliers and granularity', 'One extreme weight or activation can expand a tensor-wide scale so much that small meaningful values collapse to zero. Per-channel weight scales often improve resolution, but not every runtime accelerates every granularity. Compare per-tensor and per-channel error by layer and by input slice. Clipping a range can lower average error while saturating rare but important defects. Plot clipping frequency and held-out decision changes, especially for the examples closest to the review threshold. [[deep-learning/temperature-scaling-and-selective-risk|A confidence policy]] may be more sensitive than top-class accuracy.'),
    ('Evaluate the converted artifact', 'Run the exported model in the actual device runtime, then compare outputs with the original model on fixed and held-out batches. Audit preprocessing parity, unsupported operator fallbacks, class-specific error, calibration and latency at realistic batch size. Count artifact bytes including scales and metadata, and measure resident memory rather than multiplying parameter count by a theoretical compression ratio. A model that silently dequantizes between layers may shrink on disk but miss the latency target. Keep baseline and candidate artifacts under versioned manifests for rollback.'),
    ('Escalate only after diagnosis', 'If conversion damages a critical class, isolate the first layer with a large activation or output discrepancy. Try better calibration coverage, a different supported granularity or leaving that layer in higher precision. Quantization-aware training is a separate intervention that simulates rounding effects while updating weights; it has training cost and still needs held-out validation. Do not tune repeatedly on the final test. [[deep-learning/receipt-edge-model-release-project|The edge project]] turns measurements into a release decision.')],
    '''import torch

classifier_weights = torch.tensor([[0.08, -0.32, 0.71, -0.19],
                                   [2.4, -1.8, 0.3, 0.06],
                                   [-0.04, 0.11, -0.09, 0.24]])
channel_maximum = classifier_weights.abs().amax(dim=1, keepdim=True)
channel_scales = channel_maximum.clamp_min(1e-8) / 127
integer_codes = (classifier_weights / channel_scales).round().clamp(
    -127, 127).to(torch.int8)
restored_weights = integer_codes.float() * channel_scales
maximum_error = (classifier_weights - restored_weights).abs().amax(dim=1)
assert integer_codes.dtype == torch.int8
assert torch.isfinite(maximum_error).all()
assert bool((maximum_error <= channel_scales.squeeze(1) / 2 + 1e-6).all())''',
    'Computing per-channel maximums and rounding is O(P) in the number of weights. Raw signed eight-bit codes occupy roughly one byte per weight versus four bytes for float32, before channel scales, packing alignment and runtime metadata. Static activation calibration adds a forward pass over representative inputs; deployment conversion and benchmark cost depend on the target backend. End-to-end latency may improve, stay flat or regress because of unsupported operations and quantize/dequantize boundaries. Measure on the actual device.',
    ['Do not claim integer inference from a dequantized-weight demonstration.', 'Do not calibrate activations with random tensors or final-test identities.', 'Do not hide rare-class regressions behind aggregate accuracy and file size.'],
    ['deep-learning/inference-schema-and-latency', 'deep-learning/structured-pruning-and-latency-parity', 'deep-learning/receipt-edge-model-release-project', 'deep-learning/temperature-scaling-and-selective-risk', 'deep-learning/staged-unfreezing-and-domain-shift-audit'], EDGE)

add('structured-pruning-and-latency-parity',
    'Structured pruning and latency parity',
    'Removing complete hidden channels can create a smaller dense model; zeroing weights without rebuilding the graph often leaves the original compute shape.', [
    ('Select a removable structure', 'An unstructured mask sets individual weights to zero while preserving tensor dimensions. A dense runtime may still execute the same matrix multiplication. Structured pruning removes an entire hidden channel, filter or attention head and rewrites dependent dimensions, which can reduce dense compute. The choice must respect residual branches, normalization and downstream consumers. A channel used in two branches cannot disappear from one without repairing both. For a small classifier, start with one pair of linear layers and prove exact masked-graph parity before fine-tuning.'),
    ('Copy both sides of the boundary', 'If the first layer emits eight hidden values and only four are kept, copy those four rows of its weight and matching bias entries. Then copy the same four columns of the next layer. Preserve the next-layer bias. The two-layer example below compares this compact graph with the original graph after explicitly masking removed hidden values; exact equality is expected up to floating-point tolerance before fine-tuning. It does not claim parity with the unpruned model, because dropping useful channels changes its outputs. [[deep-learning/logits-loss-gradient|Logit changes]] must then be measured on real validation cases.'),
    ('Choose channels using held-out evidence', 'Magnitude is one possible ranking signal, but a small weight can still contribute through a correlated or rare activation. Compare candidate prune sets on a selection set that includes weak receipt edges and low-contrast text. Refit weights after structural removal, then use a separate final test to check class recall and confidence. Track the exact channel indices and model revision so the compact graph can be reconstructed. For convolutional backbones, spatial shape and skip-connection constraints make this more than a row-slicing operation.'),
    ('Benchmark the compiled path', 'Parameter count and multiply-add estimates are useful screening measures; wall-clock latency depends on kernel choice, memory traffic, batch size and device. An awkward channel width can be slower than a slightly larger aligned width on some hardware. Warm the model, synchronize accelerators where required, and report median and tail latency for the actual serving batch. Include preprocessing and any transfer to the device. [[deep-learning/inference-schema-and-latency|The inference baseline]] should use the same input and runtime.'),
    ('Combine compression carefully', 'Prune first or quantize first according to an explicit experiment; changing graph dimensions after calibration can invalidate activation scales. A useful sequence is prune, fine-tune, freeze, calibrate the compact model, convert and retest. Keep each candidate artifact immutable and compare it with the same holdout and device workload. If a speed gain fails a rare-defect recall gate, reduce pruning or restore the prior model. [[deep-learning/post-training-quantization-calibration-contract|Calibration]] cannot repair missing capacity by itself.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

torch.manual_seed(47)
feature_layer = nn.Linear(6, 8)
decision_layer = nn.Linear(8, 3)
retained_channels = torch.tensor([0, 2, 5, 7])
compact_feature = nn.Linear(6, len(retained_channels))
compact_decision = nn.Linear(len(retained_channels), 3)
with torch.no_grad():
    compact_feature.weight.copy_(feature_layer.weight[retained_channels])
    compact_feature.bias.copy_(feature_layer.bias[retained_channels])
    compact_decision.weight.copy_(decision_layer.weight[:, retained_channels])
    compact_decision.bias.copy_(decision_layer.bias)

receipt_features = torch.randn(5, 6)
hidden_values = functional.relu(feature_layer(receipt_features))
channel_mask = torch.zeros(8)
channel_mask[retained_channels] = 1
masked_logits = decision_layer(hidden_values * channel_mask)
compact_logits = compact_decision(functional.relu(compact_feature(receipt_features)))
torch.testing.assert_close(masked_logits, compact_logits, atol=1e-6, rtol=1e-6)''',
    'The dense two-layer multiply work falls from approximately 6×8 + 8×3 to 6×4 + 4×3 multiplies per example, excluding biases and activation overhead. Parameter storage falls with the same changed dimensions. Selection and copy cost are minor for one layer, but iterative pruning and fine-tuning can dominate project time. Neither multiply count nor a zero mask proves latency gain; use repeated timing on the device and include the cost of any new data movement or operator fallback.',
    ['Do not mistake a zero-valued weight mask for a smaller executable graph.', 'Do not compare the compact graph with the full unpruned graph when testing copy parity.', 'Do not prune one branch of a residual path without reconciling its consumers.'],
    ['deep-learning/post-training-quantization-calibration-contract', 'deep-learning/receipt-edge-model-release-project', 'deep-learning/inference-schema-and-latency', 'deep-learning/receipt-defect-localization-project', 'deep-learning/frozen-features-versus-fine-tuning'], EDGE)

add('receipt-edge-model-release-project',
    'Project: release a compact receipt model to an edge device',
    'Package a receipt-quality model for a constrained device only after converted-runtime measurements and defect-specific decision gates pass.', [
    ('Freeze the baseline contract', 'Pin the original receipt model, preprocessing revision, class map, confidence threshold and device runtime. Capture a held-out set grouped by physical receipt and a separate calibration population spanning lighting, blur, crop and device differences. Record model bytes, resident memory, cold-start time, median and 95th-percentile request latency at the intended batch size. Report class recall and false accepts. A smaller file by itself is not a release result. [[deep-learning/receipt-image-quality-project|The classifier project]] supplies the decision context.'),
    ('Build separate compression candidates', 'Create one structured-pruned candidate with a physically smaller graph and one calibrated quantized candidate in a backend that supports its operators. Optionally try a compact model with both changes, but recalibrate after pruning. Store each model and conversion configuration under distinct revisions. Do not reuse scales from the original graph after channels are removed. [[deep-learning/structured-pruning-and-latency-parity|Structural parity]] checks the graph rewrite; [[deep-learning/post-training-quantization-calibration-contract|calibration]] checks integer ranges.'),
    ('Benchmark the actual serving path', 'Run the same normalized fixed inputs through baseline and candidates in the target runtime. Compare logits, decisions near the threshold and nonfinite outputs before bulk timing. Warm each candidate and measure many realistic requests, including preprocessing and serialization when they are part of user-visible latency. Record thermal state, power mode and backend version. An isolated desktop matrix benchmark cannot establish mobile or embedded tail latency. Report accepted-case coverage and manual review volume if the system can abstain.'),
    ('Apply a predeclared release gate', 'Write gates before reading the final test results: for example, defect recall may not fall by more than one percentage point, false accepts may not rise, and the target device 95th-percentile latency must meet its limit. Compute uncertainty intervals or at least event counts for small slices; one error out of a tiny group is too noisy for a strong claim. The code below evaluates supplied metrics and returns all failed gates. It does not fabricate benchmark measurements. If no candidate passes, retain the baseline.'),
    ('Ship with recovery state', 'The release bundle includes model, scales, preprocessing, class map, threshold, runtime compatibility and checksum. Run a clean-process reload test and a staged device rollout. Monitor out-of-range activation counts, latency tails, confidence coverage, manual review workload and class-specific corrections. Keep the previous package available for rollback if a source-device shift appears after deployment. [[deep-learning/receipt-confidence-audit-project|The confidence audit]] identifies cases that should route to review rather than receive an automatic answer.')],
    '''from dataclasses import dataclass

@dataclass(frozen=True)
class EdgeMetrics:
    defect_recall: float
    false_accepts: int
    p95_latency_ms: float
    resident_megabytes: float

def release_failures(baseline: EdgeMetrics, candidate: EdgeMetrics,
                     latency_limit_ms: float, memory_limit_mb: float) -> list[str]:
    failures = []
    if candidate.defect_recall < baseline.defect_recall - 0.01:
        failures.append("defect recall gate")
    if candidate.false_accepts > baseline.false_accepts:
        failures.append("false accept gate")
    if candidate.p95_latency_ms > latency_limit_ms:
        failures.append("latency gate")
    if candidate.resident_megabytes > memory_limit_mb:
        failures.append("memory gate")
    return failures

reference = EdgeMetrics(0.94, 3, 31.4, 42.0)
converted = EdgeMetrics(0.925, 3, 18.7, 19.0)
assert release_failures(reference, converted, 23.0, 24.0) == [
    "defect recall gate"]''',
    'Compression preparation can take longer than original training once calibration, fine-tuning and device validation are counted. Disk bytes are only one component of memory; activations, backend buffers and image preprocessing remain. For N measured requests, sorting latency for an exact empirical percentile costs O(N log N), while streaming approximations can lower memory. The release gate is O(1) once reliable metrics exist. Budget repeat device runs and human review of rare-class errors before claiming an edge win.',
    ['Do not publish a smaller checkpoint that runs floating-point fallback kernels and misses latency limits.', 'Do not set gates after inspecting the final test outcome.', 'Do not conceal a defect-recall failure with good average accuracy or a lower p95 latency.'],
    ['deep-learning/post-training-quantization-calibration-contract', 'deep-learning/structured-pruning-and-latency-parity', 'deep-learning/inference-schema-and-latency', 'deep-learning/receipt-confidence-audit-project', 'deep-learning/receipt-image-quality-project'], EDGE, True)

CROSSLINKS = [
    ('deep-learning/logits-loss-gradient', 'deep-learning/diffusion-forward-noise-and-timestep-target'),
    ('deep-learning/train-eval-validation-loop', 'deep-learning/diffusion-forward-noise-and-timestep-target'),
    ('deep-learning/receipt-image-quality-project', 'deep-learning/receipt-background-diffusion-project'),
    ('deep-learning/receipt-defect-localization-project', 'deep-learning/diffusion-reverse-step-and-guidance'),
    ('deep-learning/receipt-confidence-audit-project', 'deep-learning/receipt-background-diffusion-project'),
    ('deep-learning/inference-schema-and-latency', 'deep-learning/post-training-quantization-calibration-contract'),
    ('deep-learning/frozen-features-versus-fine-tuning', 'deep-learning/structured-pruning-and-latency-parity'),
    ('deep-learning/temperature-scaling-and-selective-risk', 'deep-learning/post-training-quantization-calibration-contract'),
    ('deep-learning/receipt-image-quality-project', 'deep-learning/receipt-edge-model-release-project'),
    ('deep-learning/receipt-confidence-audit-project', 'deep-learning/receipt-edge-model-release-project'),
    ('deep-learning/deep-learning-tutorial', 'deep-learning/receipt-edge-model-release-project'),
]

if __name__ == '__main__':
    publish(LESSONS, (DIFFUSION, EDGE), CROSSLINKS,
            'aitrove-deep-learning-diffusion-edge-import-20261006.json',
            7860, subject='deep-learning')
