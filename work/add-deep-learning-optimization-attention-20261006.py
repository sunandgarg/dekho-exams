"""Publish two deep-learning paths with testable PyTorch examples."""
from de_batch_publisher import publish

OPTIMIZATION = 'Optimization under a memory budget'
ATTENTION = 'Attention masks and sequence targets'
LESSONS = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    assert len(sections) == 5
    LESSONS.append(dict(path='deep-learning/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add('gradient-accumulation-and-effective-batch',
    'Gradient accumulation and effective batch accounting',
    'Accumulation changes when the optimizer steps; a correct large-batch approximation also preserves the weight of every example, including the final short microbatch.', [
    ('Define the unit being averaged', 'A microbatch is one forward and backward pass. An optimizer update can combine several microbatches; its effective batch is the total examples whose gradients contributed to that update, multiplied by the number of workers when gradients are reduced across workers. Dividing every microbatch mean by the number of microbatches fails when their sizes differ. For sample-averaged cross-entropy, sum the losses in each microbatch and divide by the total accepted examples in the update. [[deep-learning/batching-and-class-sampling|Sampling policy]] determines which examples enter that denominator.'),
    ('Step once at the accumulation boundary', 'Clear gradients before the first microbatch, call backward once per microbatch, then clip if required and step once. Clearing inside the loop discards earlier contributions. Stepping after each backward changes both the effective batch and the parameter point at which later gradients are computed. A final partial accumulation window still needs an update, with its own denominator; dropping it changes the training population. Count optimizer updates separately from examples seen and loader iterations.'),
    ('State where equivalence ends', 'With a deterministic model and a loss separable over examples, accumulated gradients can match one full-batch gradient up to floating-point order. Batch normalization reads microbatch statistics, so it can change the function itself. Dropout draws different masks, and distributed reduction conventions can add another scaling factor. Learning-rate schedules indexed by optimizer updates should advance once per effective batch, not once per microbatch. [[deep-learning/train-eval-validation-loop|Validation]] must compare the resulting model, not merely the first loss.'),
    ('Control long-sequence cost', 'Accumulation reduces the peak activations of one pass but does not reduce the model weights, optimizer moments or the largest single-example activation. If one sequence alone exceeds memory, accumulation cannot fix it; trim sequence length, checkpoint activations or change the model. Do not retain each loss tensor in a Python list while logging; detach its scalar value so previous computation graphs can be released.'),
    ('Prove the accounting', 'Run a fixed three-example batch as one pass, then as microbatches of two and one with copied initial weights. Compare every parameter gradient before stepping. Test an incomplete final window and a distributed configuration with a documented loss reduction convention. Record example count, microbatch count, optimizer-step count and gradient norm. A run that says only "batch size 47" conceals the update cadence that determines its training behavior.')],
    '''import copy
import torch
from torch import nn

torch.manual_seed(47)
full_model = nn.Linear(3, 2)
split_model = copy.deepcopy(full_model)
receipt_features = torch.tensor([[0.7, 0.2, 0.1],
                                 [0.1, 0.6, 0.3],
                                 [0.4, 0.1, 0.5]])
quality_labels = torch.tensor([0, 1, 0])

full_loss = nn.functional.cross_entropy(
    full_model(receipt_features), quality_labels, reduction="mean")
full_loss.backward()

accepted_examples = quality_labels.numel()
for first, last in ((0, 2), (2, 3)):
    logits = split_model(receipt_features[first:last])
    loss_sum = nn.functional.cross_entropy(
        logits, quality_labels[first:last], reduction="sum")
    (loss_sum / accepted_examples).backward()

for full_parameter, split_parameter in zip(full_model.parameters(),
                                            split_model.parameters()):
    torch.testing.assert_close(full_parameter.grad, split_parameter.grad,
                               rtol=1e-6, atol=1e-7)''',
    'Each microbatch stores activations for at most its own samples, so peak activation memory is closer to the microbatch footprint than the full effective-batch footprint. Total forward and backward work remains roughly proportional to all examples; more microbatches add launch and synchronization overhead. The model and optimizer state remain resident. A short last batch must be weighted by its example count.',
    ['Do not divide each unequal-size microbatch mean by the number of microbatches.', 'Do not reset gradients or advance the scheduler between microbatches of one update.', 'Do not promise full-batch equivalence when batch-dependent layers change their statistics.'],
    ['deep-learning/batching-and-class-sampling', 'deep-learning/logits-loss-gradient', 'deep-learning/mixed-precision-scaling-and-gradient-clipping', 'deep-learning/checkpoint-resume-state', 'deep-learning/receipt-training-memory-project'], OPTIMIZATION)

add('mixed-precision-scaling-and-gradient-clipping',
    'Mixed precision, loss scaling and gradient clipping',
    'Autocast can reduce compute and activation cost, but scaled gradients must be unscaled before clipping and the scale must change only at an optimizer-step boundary.', [
    ('Keep a numerical baseline', 'Train a small fixed batch in full precision before enabling autocast. Record finite loss, gradient norm, predictions and update count. Mixed precision chooses lower precision for eligible operations; it does not mean every tensor or reduction is half precision. Depending on hardware, bfloat16 may need no gradient scaling while float16 often benefits from it. A speedup is hardware- and shape-dependent, so compare measured throughput and accuracy rather than assuming a universal gain. [[deep-learning/logits-loss-gradient|The logits-and-loss contract]] stays the same.'),
    ('Order the update deliberately', 'Run forward and loss under autocast, scale the loss, then run backward. For float16, wait until all microbatches for the current effective batch have contributed before unscaling. Clip the unscaled gradients and call the scaler-controlled optimizer step; it can skip an unsafe update when gradients are nonfinite. Update the scale once at that boundary. Clearing gradients and advancing a scheduler tied to real optimizer updates require an explicit rule for a skipped step.'),
    ('Understand overflow evidence', 'A falling scale or repeated skipped updates can mean unstable activations, an excessive learning rate or a model that does not fit float16 range. Log loss, unscaled norm, scale and skipped-update count without dumping sensitive training examples. Switching precision or reducing learning rate may be warranted, but first locate the first nonfinite tensor. Clipping after scaling changes the intended threshold by the scale factor and can suppress almost every useful update.'),
    ('Account for resumed state', 'A checkpoint that resumes mixed-precision training should carry model weights, optimizer, scheduler, scaler, update number and data position as one coherent generation. Saving only weights changes future steps even if the first forward output matches. If an update was skipped, the recorded optimizer step must not advance as though parameters changed. [[deep-learning/checkpoint-resume-state|Checkpoint recovery]] covers the publication boundary for a complete state bundle.'),
    ('Test on the deployment device', 'Autocast support, kernels, memory behavior and precision vary by accelerator. Profile the same batch shape and sequence length that production uses, including a short final batch and a long tail example. Compare full precision and mixed precision on a frozen validation set, not on a repeatedly tuned test set. A tiny numerical difference is expected; a label flip near a decision threshold needs a product-level tolerance and measured frequency.')],
    '''import torch
from torch import nn

device = torch.device("cuda")
if not torch.cuda.is_available():
    raise RuntimeError("This float16 example requires a CUDA device")

quality_model = nn.Linear(3, 2).to(device)
optimizer = torch.optim.AdamW(quality_model.parameters(), lr=0.00047)
scaler = torch.amp.GradScaler("cuda")
features = torch.tensor([[0.7, 0.2, 0.1], [0.1, 0.6, 0.3]], device=device)
labels = torch.tensor([0, 1], device=device)

optimizer.zero_grad(set_to_none=True)
with torch.autocast(device_type="cuda", dtype=torch.float16):
    logits = quality_model(features)
    loss = nn.functional.cross_entropy(logits, labels)
scaler.scale(loss).backward()
scaler.unscale_(optimizer)
gradient_norm = nn.utils.clip_grad_norm_(quality_model.parameters(), 1.7)
assert torch.isfinite(gradient_norm)
scaler.step(optimizer)
scaler.update()''',
    'Autocast can reduce eligible activation sizes and accelerate supported kernels, while scaler bookkeeping and some full-precision operations remain. Loss scaling does not repair a truly divergent model. Unscale and norm calculation inspect all gradients, costing O(P) for P parameters; clipping does not lower activation memory. Measure memory and examples per second on the actual device, including skipped updates.',
    ['Do not clip scaled gradients as though they were ordinary gradients.', 'Do not update the scale in the middle of one effective batch.', 'Do not treat every skipped step as a successful parameter update in a scheduler or checkpoint.'],
    ['deep-learning/gradient-accumulation-and-effective-batch', 'deep-learning/checkpoint-resume-state', 'deep-learning/train-eval-validation-loop', 'deep-learning/logits-loss-gradient', 'deep-learning/receipt-training-memory-project'], OPTIMIZATION)

add('receipt-training-memory-project',
    'Project: train a receipt model under a memory budget',
    'Build a receipt-quality classifier with explicit effective-batch accounting, a measured precision decision and recovery evidence rather than hiding memory failures behind a smaller batch.', [
    ('Fix the experimental contract', 'Split receipt identities before augmentation and freeze a label map for readable, blurred and cut-off images. Record the device memory limit, image dimensions, model revision, optimizer, loss reduction and number of examples per optimizer update. Keep one full-precision baseline small enough to run. [[deep-learning/receipt-image-quality-project|The original receipt project]] supplies the data and evaluation boundary; this project tests whether the optimized training loop preserves it.'),
    ('Build a weighted accumulation loop', 'Choose a microbatch that fits the device, then accumulate to an effective batch of 47 accepted examples. The final microbatch will often be short; sum unreduced losses and divide by the actual number of accepted examples, not by a rounded-up microbatch count. Clip only after all contributions are present, and step once. Test a copied model on a tiny deterministic batch against a full-batch gradient before using the full image dataset. [[deep-learning/gradient-accumulation-and-effective-batch|Effective-batch accounting]] is a release check.'),
    ('Introduce precision after the baseline', 'Measure full precision, float16 autocast with scaling and, if supported, bfloat16 autocast. Record peak allocated memory, accepted examples per second, nonfinite gradients, skipped steps and frozen validation metrics. If precision changes predictions near the acceptance threshold, quantify the change by class. [[deep-learning/mixed-precision-scaling-and-gradient-clipping|Scaling and clipping]] must occur in the documented order.'),
    ('Interrupt and restore', 'Save a checkpoint only at an optimizer-step boundary with model, optimizer, scheduler, scaler, sampler position and step count. Crash after an unfinished checkpoint write and prove the last complete checkpoint still resumes. Compare the first resumed fixed-batch update against an uninterrupted reference under a controlled seed. A new device type or changed microbatch plan may prevent bitwise identity; state the expected tolerance.'),
    ('Report the tradeoff', 'Submit a memory trace, training-time breakdown, gradient comparison, update and skip counts, validation result and checkpoint recovery trace. Also show a deliberately wrong run that divides a short microbatch mean by the number of microbatches; report its gradient discrepancy. Do not declare success solely because an out-of-memory error disappeared while the accepted-example count or class mix changed.')],
    '''import copy
import torch
from torch import nn

torch.manual_seed(83)
reference_model = nn.Linear(3, 3)
bounded_model = copy.deepcopy(reference_model)
receipt_vectors = torch.tensor([[0.8, 0.1, 0.1],
                                [0.2, 0.5, 0.3],
                                [0.1, 0.3, 0.6]])
quality_targets = torch.tensor([0, 1, 2])

nn.functional.cross_entropy(reference_model(receipt_vectors),
                            quality_targets).backward()
for start, stop in ((0, 2), (2, 3)):
    loss_sum = nn.functional.cross_entropy(
        bounded_model(receipt_vectors[start:stop]),
        quality_targets[start:stop], reduction="sum")
    (loss_sum / quality_targets.numel()).backward()

for reference_weight, bounded_weight in zip(reference_model.parameters(),
                                             bounded_model.parameters()):
    torch.testing.assert_close(reference_weight.grad, bounded_weight.grad,
                               rtol=1e-6, atol=1e-7)''',
    'Peak activation memory follows the largest microbatch, but model, gradients and optimizer moments still occupy memory. More microbatches can lower examples per second through repeated launches, while autocast may restore throughput on suitable hardware. Instrument both peak memory and wall-clock cost. A checkpoint stores additional optimizer and scaler state, and final selection must use the same validation population as the baseline.',
    ['Do not change the dataset split while comparing precision modes.', 'Do not omit the short final microbatch or give it the same weight as a full microbatch.', 'Do not resume from weights alone and call the optimizer trajectory recovered.'],
    ['deep-learning/gradient-accumulation-and-effective-batch', 'deep-learning/mixed-precision-scaling-and-gradient-clipping', 'deep-learning/receipt-image-quality-project', 'deep-learning/checkpoint-resume-state', 'deep-learning/augmentation-leakage-boundary'], OPTIMIZATION, True)


add('scaled-dot-product-attention-mask-contract',
    'Scaled dot-product attention and mask contracts',
    'An attention score combines a query with every permitted key; a mask must encode exactly which key positions may influence each query position.', [
    ('Track four axes', 'For a batched multi-head implementation, queries have batch, head, query-position and feature axes; keys and values have batch, head, key-position and feature axes. Scores occupy batch by head by query-position by key-position. Scale dot products by the square root of the query/key feature width before softmax so score magnitude does not grow unchecked with width. The resulting weights mix value vectors, not key vectors. [[deep-learning/tensor-shape-dtype-contract|Tensor contracts]] should assert every axis before training.'),
    ('Specify mask meaning per API', 'In one common scaled-dot-product API, a Boolean True means the key may participate; another multi-head API uses True to mean padding should be ignored. Carry a named allow-mask at the boundary and convert it deliberately when switching APIs. A padding mask blocks invalid key positions; a causal mask blocks keys to the right of the query. Combine them by logical AND. A key mask alone does not guarantee padded query outputs are zero, so zero or exclude those outputs before downstream pooling.'),
    ('Avoid rows with no valid keys', 'Softmax over all negative-infinity scores is undefined in a simple reference implementation and may produce NaN. A request with zero valid tokens should fail validation or use an explicit safe fallback. With causal attention and right padding, valid query positions normally retain at least their own key. Left padding, cached decoding and cross-attention need separate tests, because their query and key lengths or alignments can differ.'),
    ('Control dropout at evaluation', 'Some low-level attention functions apply the passed dropout probability even when the containing model is in evaluation mode. Pass zero explicitly during evaluation or serving. Compare deterministic outputs for the same input twice, and confirm no output at position p changes when only a future token changes. [[deep-learning/train-eval-validation-loop|Train/eval mode checks]] apply to custom attention calls as well as ordinary dropout modules.'),
    ('Budget sequence length', 'Dense score computation scales quadratically with sequence length and linearly with heads and batch size; specialized kernels may avoid storing the entire score matrix, but arithmetic still grows with attended pairs. Profile the longest accepted sequence rather than the median. A mask does not automatically make a dense kernel sparse. Restrict length, choose a supported efficient kernel or change the attention pattern when the cost exceeds the product budget.')],
    '''import torch
import torch.nn.functional as functional

torch.manual_seed(61)
receipt_tokens = torch.randn(1, 1, 4, 8)
valid_tokens = torch.tensor([[True, True, True, False]])
sequence_length = receipt_tokens.size(-2)
causal_allow = torch.ones(sequence_length, sequence_length,
                          dtype=torch.bool).tril()
key_allow = valid_tokens[:, None, None, :]
allow_mask = causal_allow[None, None, :, :] & key_allow

attended = functional.scaled_dot_product_attention(
    receipt_tokens, receipt_tokens, receipt_tokens,
    attn_mask=allow_mask, dropout_p=0.0)
attended = attended * valid_tokens[:, None, :, None]
assert attended.shape == receipt_tokens.shape
assert torch.count_nonzero(attended[:, :, -1, :]) == 0
assert not allow_mask[0, 0, 0, 1]
assert not allow_mask[0, 0, 2, 3]''',
    'A dense attention layer computes roughly O(B × H × L × S × D) work for batch B, heads H, query length L, key length S and head width D. A naive implementation also stores O(B × H × L × S) scores. Kernel choice can reduce stored intermediates, but padding still wastes work unless batching or the kernel exploits lengths. Validate masks before expensive model execution.',
    ['Do not carry a Boolean mask between APIs without checking which truth value means allowed.', 'Do not assume padding keys also zero padded query outputs.', 'Do not rely on model.eval() alone to disable a dropout probability passed to a low-level attention function.'],
    ['deep-learning/tensor-shape-dtype-contract', 'deep-learning/train-eval-validation-loop', 'deep-learning/causal-target-shift-and-padding-loss', 'natural-language-processing/unicode-tokenization-boundary', 'deep-learning/sequence-attention-leakage-project'], ATTENTION)

add('causal-target-shift-and-padding-loss',
    'Causal target shifts and padding-aware loss',
    'A next-token learner should predict position t plus one from positions no later than t, while padding and any unavailable targets contribute no loss.', [
    ('Separate model input from target', 'For tokens A, B, C and D, feed A, B and C and score predictions against B, C and D. If the model receives D at the position used to predict D, the task leaks its own answer even when the attention mask is causal. Make the one-position shift explicit in the data contract, and assert input length equals target length after shifting. [[natural-language-processing/unicode-tokenization-boundary|Tokenization]] fixes the vocabulary and special-token policy before this calculation.'),
    ('Mask the target, not just attention', 'A key padding mask can keep a token from being attended to but does not stop a padded target from entering cross-entropy. Replace target positions without a real next token by the loss function’s ignore value, or use a weighted unreduced loss with a verified denominator. A batch with one long sequence and many short sequences can otherwise be dominated by padding. Count valid target tokens per optimizer update and report loss per valid token, not per allocated slot.'),
    ('Test causal independence', 'Hold a prefix fixed, change only a future token, and assert that logits for earlier positions stay unchanged under deterministic evaluation. This catches a reversed triangular mask, an accidental bidirectional layer and shifted labels that read future information. A model can still score well on a leaky validation set, so the counterfactual test is more decisive than a low loss. [[deep-learning/scaled-dot-product-attention-mask-contract|Attention mask semantics]] determine which comparisons are legal.'),
    ('Handle boundary tokens deliberately', 'A start token can give the first target a predecessor; an end token lets the model learn when to stop. Whether the final input predicts an end token is a modeling choice, not a side effect of padding. Left-padding during generation differs from right-padding during training; position IDs and cached key/value length may need adjustment. Document the serving prompt limit and stop behavior alongside the training shift. [[deep-learning/inference-schema-and-latency|Inference contracts]] protect this boundary.'),
    ('Measure the actual denominator', 'For each batch, log allocated positions, valid input positions and valid target positions. Reject an all-padding batch before softmax or loss reduction. If using gradient accumulation with variable lengths, sum token losses and divide by the total valid targets across the effective batch; averaging per-sequence means first gives short sequences extra weight. Pin the token weighting rule before comparing runs.')],
    '''import torch
import torch.nn.functional as functional

pad_id = 0
event_sequences = torch.tensor([[7, 12, 19, 23, 0],
                                [7, 31, 17, 0, 0]])
model_inputs = event_sequences[:, :-1]
next_targets = event_sequences[:, 1:].clone()
next_targets[next_targets == pad_id] = -100

torch.manual_seed(29)
vocabulary_size = 47
next_token_logits = torch.randn(2, 4, vocabulary_size,
                                requires_grad=True)
token_loss_sum = functional.cross_entropy(
    next_token_logits.transpose(1, 2), next_targets,
    ignore_index=-100, reduction="sum")
valid_targets = (next_targets != -100).sum()
mean_token_loss = token_loss_sum / valid_targets
mean_token_loss.backward()
assert int(valid_targets) == 5
assert model_inputs.shape == next_targets.shape
assert torch.isfinite(mean_token_loss)''',
    'Shifting itself costs O(B × L) views or copies depending on later operations. A vocabulary cross-entropy over V classes costs roughly O(B × L × V) arithmetic and logits storage unless a fused implementation changes intermediates. Padding consumes attention and output compute even when ignored by loss. Report valid-token throughput, not only padded tokens per second.',
    ['Do not score each token against itself because the labels were left unshifted.', 'Do not assume an attention mask removes padded positions from the loss.', 'Do not average unequal-length sequence means when the intended unit is one valid target token.'],
    ['deep-learning/scaled-dot-product-attention-mask-contract', 'deep-learning/logits-loss-gradient', 'natural-language-processing/unicode-tokenization-boundary', 'deep-learning/gradient-accumulation-and-effective-batch', 'deep-learning/sequence-attention-leakage-project'], ATTENTION)

add('sequence-attention-leakage-project',
    'Project: audit a next-event attention decoder',
    'Train a small event-sequence decoder with causal and padding controls, then break each control deliberately to prove the tests detect leakage.', [
    ('Construct event sequences', 'Generate 470 customer-service event histories with a fixed vocabulary, a start event, an end event and right padding. Split by customer identity before forming overlapping windows so nearby windows from one customer cannot land in both train and validation. Record the tokenizer version, maximum sequence length and count of valid target positions. [[natural-language-processing/grouped-temporal-text-validation|Grouped temporal validation]] keeps the evaluation population honest.'),
    ('Implement one attention block', 'Project input embeddings into queries, keys and values, preserve batch and sequence axes, and combine causal and valid-key masks. Exclude padded query positions from pooling or downstream metrics. Pass zero attention dropout during evaluation. On a test pair that differs only after position three, compare earlier outputs exactly within a numerical tolerance. [[deep-learning/scaled-dot-product-attention-mask-contract|The mask contract]] defines the expected shape and truth values.'),
    ('Align labels and loss', 'Train with inputs excluding the final token and targets excluding the first. Ignore padding targets; include the end-event target if the product needs a stop prediction. Sum unreduced token losses and divide by valid targets across each effective batch. Add a test where every target is ignored and reject that batch instead of dividing by zero. [[deep-learning/causal-target-shift-and-padding-loss|Target shifting]] is independent of the attention mask.'),
    ('Run negative controls', 'First remove the causal mask and show that changing a future event alters an earlier output. Then keep the mask but stop shifting targets; show that a leakage assertion catches the self-target path. Finally count padding positions in the loss and report the denominator error. A model with a lower leaked loss fails the project; it is learning information unavailable when the product makes its prediction.'),
    ('Publish a checked result', 'Provide fixed data manifests, model revision, mask tensor shapes, causal counterfactual results, valid-target counts, training and validation loss, and inference latency at the maximum accepted length. Restart from a checkpoint and compare the next update. Report how much compute was spent on padding and state a length limit. The final serving artifact must include vocabulary IDs and start/end semantics, not only weights.')],
    '''import torch
from torch import nn
import torch.nn.functional as functional

class ServiceEventAttention(nn.Module):
    def __init__(self, vocabulary_size=47, width=12):
        super().__init__()
        self.embedding = nn.Embedding(vocabulary_size, width)
        self.project_qkv = nn.Linear(width, width * 3, bias=False)

    def forward(self, event_ids, valid_tokens):
        if not bool(valid_tokens.any(dim=1).all()):
            raise ValueError("each history needs a valid token")
        hidden = self.embedding(event_ids)
        query, key, value = self.project_qkv(hidden).chunk(3, dim=-1)
        positions = event_ids.size(1)
        causal_allow = torch.ones(positions, positions,
                                  dtype=torch.bool, device=event_ids.device).tril()
        allow_mask = (causal_allow[None, None, :, :]
                      & valid_tokens[:, None, None, :])
        attended = functional.scaled_dot_product_attention(
            query.unsqueeze(1), key.unsqueeze(1), value.unsqueeze(1),
            attn_mask=allow_mask, dropout_p=0.0)
        return attended.squeeze(1) * valid_tokens[:, :, None]

torch.manual_seed(83)
decoder_block = ServiceEventAttention().eval()
first_history = torch.tensor([[7, 12, 19, 23]])
changed_future = torch.tensor([[7, 12, 19, 31]])
valid_tokens = torch.ones_like(first_history, dtype=torch.bool)
with torch.inference_mode():
    first_output = decoder_block(first_history, valid_tokens)
    second_output = decoder_block(changed_future, valid_tokens)
torch.testing.assert_close(first_output[:, :3], second_output[:, :3])''',
    'The one-head reference uses O(B × L squared × D) attention arithmetic, plus embeddings and QKV projections. The causal mask protects information flow but does not by itself make long sequences cheap. Profile peak memory and latency at the accepted maximum length, and compare valid-token throughput with allocated-token throughput. Identity-safe validation and negative controls cost extra runs but prevent a misleading low loss.',
    ['Do not split overlapping windows from one customer across train and validation.', 'Do not take a low loss as proof that future events were hidden.', 'Do not publish an inference block without the same vocabulary, length limit and stop-token policy used in training.'],
    ['deep-learning/scaled-dot-product-attention-mask-contract', 'deep-learning/causal-target-shift-and-padding-loss', 'deep-learning/checkpoint-resume-state', 'natural-language-processing/grouped-temporal-text-validation', 'deep-learning/inference-schema-and-latency'], ATTENTION, True)


CROSSLINKS = [
    ('deep-learning/batching-and-class-sampling', 'deep-learning/gradient-accumulation-and-effective-batch'),
    ('deep-learning/logits-loss-gradient', 'deep-learning/gradient-accumulation-and-effective-batch'),
    ('deep-learning/checkpoint-resume-state', 'deep-learning/mixed-precision-scaling-and-gradient-clipping'),
    ('deep-learning/train-eval-validation-loop', 'deep-learning/mixed-precision-scaling-and-gradient-clipping'),
    ('deep-learning/receipt-image-quality-project', 'deep-learning/receipt-training-memory-project'),
    ('deep-learning/augmentation-leakage-boundary', 'deep-learning/receipt-training-memory-project'),
    ('deep-learning/tensor-shape-dtype-contract', 'deep-learning/scaled-dot-product-attention-mask-contract'),
    ('natural-language-processing/unicode-tokenization-boundary', 'deep-learning/scaled-dot-product-attention-mask-contract'),
    ('deep-learning/inference-schema-and-latency', 'deep-learning/causal-target-shift-and-padding-loss'),
    ('natural-language-processing/text-serving-contract', 'deep-learning/causal-target-shift-and-padding-loss'),
    ('natural-language-processing/grouped-temporal-text-validation', 'deep-learning/sequence-attention-leakage-project'),
    ('deep-learning/train-eval-validation-loop', 'deep-learning/sequence-attention-leakage-project'),
]


if __name__ == '__main__':
    publish(LESSONS, (OPTIMIZATION, ATTENTION), CROSSLINKS,
            'aitrove-deep-learning-optimization-attention-import-20261006.json',
            7820, subject='deep-learning')
