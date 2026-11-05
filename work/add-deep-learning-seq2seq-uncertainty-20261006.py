"""Add sequence-to-sequence and predictive-uncertainty learning paths."""
from de_batch_publisher import publish

SEQ = 'Encoder-decoder attention and generated evidence'
UNCERTAINTY = 'Neural ensemble uncertainty and review routing'
LESSONS = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    assert len(sections) == 5
    LESSONS.append(dict(path='deep-learning/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add('encoder-decoder-cross-attention-and-source-mask',
    'Encoder-decoder cross-attention and source masks',
    'A decoder query may attend to encoded source positions, but padding and future-target access have different mask rules.', [
    ('Separate three attention paths', 'The encoder can read the available source sequence in both directions. Decoder self-attention may read only earlier target positions when generating autoregressively. Cross-attention uses decoder states as queries and encoded source states as keys and values. A source key-padding mask blocks meaningless padded source positions. It is not a causal mask on the source. [[deep-learning/scaled-dot-product-attention-mask-contract|The attention-mask lesson]] defines the shape and polarity checks for each path.'),
    ('Keep source length physical', 'An incident summary may draw from a timestamped service-event sequence. Source positions should represent events known before the summary request, not post-resolution notes. Store source event IDs, cutoff time, tokenization revision and padding lengths. A model that reads events after the alert appears to summarize well but cannot do so when deployed. Group train and final test by incident, since two summaries of one incident are not independent observations.'),
    ('Check the mask at the boundary', 'For a batch of two incident records, source lengths of five and three require a mask that hides only the last two positions of the second record. A Boolean key-padding mask commonly uses True for blocked positions; verify the chosen API rather than guessing. The code checks that the second query places zero attention weight on padded source positions. Inspect finite outputs when one source is empty; many implementations require an explicit no-source route.'),
    ('Preserve source evidence', 'Attention weights are routing coefficients, not proof that generated text is supported. Keep a link from each generated statement to available source events and compare against a simple extractive summary. A long source can dilute rare severe events under truncation; record what was cut and test incident severity slices. [[deep-learning/service-incident-seq2seq-project|The applied project]] rejects summaries that invent or omit material facts.'),
    ('Profile both sequence axes', 'Cross-attention compares each target position with source positions. Long incident histories and long generated summaries therefore raise both compute and memory. Cache the encoded source when decoding many target tokens, but re-encode when the event ledger changes. Measure p95 tokenization, encoding, incremental decoding and evidence validation rather than only one attention layer.')],
    '''import torch
from torch import nn

torch.manual_seed(47)
encoded_events = torch.rand(2, 5, 8)
decoder_queries = torch.rand(2, 3, 8)
source_padding = torch.tensor([[False, False, False, False, False],
                               [False, False, False, True, True]])
cross_attention = nn.MultiheadAttention(8, 2, batch_first=True)
context, weights = cross_attention(decoder_queries, encoded_events,
                                   encoded_events, key_padding_mask=source_padding,
                                   need_weights=True)
assert context.shape == (2, 3, 8)
assert weights.shape == (2, 3, 5)
assert torch.allclose(weights[1, :, 3:], torch.zeros_like(weights[1, :, 3:]))
assert torch.isfinite(context).all()''',
    'For batch B, target length T, source length S and width D, cross-attention score work is roughly O(BTSD), with O(BTS) attention-weight storage when weights are materialized. Projection costs add terms proportional to sequence length and D squared. Source encoding and target self-attention add separate work. The example verifies mask geometry only; it does not establish grounded incident summaries or a fast decoder.',
    ['Do not apply a target causal mask as if it were a source padding mask.', 'Do not include post-decision events in an input for a live summary.', 'Do not treat an attention weight as proof that a statement is supported.'],
    ['deep-learning/teacher-forcing-shift-and-generation-parity', 'deep-learning/service-incident-seq2seq-project', 'deep-learning/scaled-dot-product-attention-mask-contract', 'deep-learning/causal-target-shift-and-padding-loss', 'deep-learning/inference-schema-and-latency'], SEQ)

add('teacher-forcing-shift-and-generation-parity',
    'Teacher forcing, target shifts and generation parity',
    'A sequence-to-sequence model trains against known previous tokens but must generate from its own history at serving time.', [
    ('Shift the target once', 'If the reviewed incident summary is a token sequence ending in an end marker, the decoder input starts with a beginning marker followed by every target token except the final one. Labels are the original target tokens. Never feed the token being predicted into the same input position. The code constructs the input and label arrays and checks the offset. [[deep-learning/causal-target-shift-and-padding-loss|The causal shift lesson]] covers the same off-by-one failure for decoder-only training.'),
    ('Mask target padding separately', 'A batched summary can end after five tokens in one incident and twelve in another. Ignore padding labels in the loss while still preventing decoder self-attention from reading future target tokens. Source padding belongs to cross-attention. Track beginning, end and pad token IDs as part of the vocabulary revision; mixing them can create an apparently good loss and endless generation. Check the empty-summary and maximum-length cases explicitly.'),
    ('Measure exposure at generation', 'During teacher-forced training, every previous target token is correct. At serving, an early mistaken word becomes part of subsequent context and can compound. Evaluate by actually decoding complete summaries, not only by next-token loss. Compare greedy and beam decoding with a fixed length rule, and inspect repeated phrases, premature end markers and missing severe facts. [[deep-learning/decoding-stop-rules-and-beam-score|The decoding lesson]] defines a stable stop contract.'),
    ('Tie claims to available events', 'A service summary should identify which source event supports each critical claim. Record the incident cutoff, source event IDs and generated tokens, then let reviewers mark unsupported statements. An extractive baseline may be safer for a sparse event ledger. If a source is missing, use a declared unavailable response rather than completing a plausible story from learned patterns. The model must not silently fill gaps with invented operational details.'),
    ('Keep release parity measurable', 'Replay the same incident through training preprocessing and serving preprocessing, checking token IDs, masks and logits at the first generated step. Then perform full decoding with only past generated tokens. Measure factual error, severe-event omission, p95 latency and fallback frequency by incident type. [[deep-learning/service-incident-seq2seq-project|The project]] gates these outcomes before any operator-facing release.')],
    '''START_ID, END_ID, PAD_ID = 47, 58, 69

def shifted_summary(reviewed_tokens):
    if not reviewed_tokens or reviewed_tokens[-1] != END_ID:
        raise ValueError("reviewed summary must end with END_ID")
    if PAD_ID in reviewed_tokens or START_ID in reviewed_tokens:
        raise ValueError("special tokens are not summary content")
    decoder_input = [START_ID] + reviewed_tokens[:-1]
    labels = list(reviewed_tokens)
    assert len(decoder_input) == len(labels)
    return decoder_input, labels

decoder_input, labels = shifted_summary([72, 83, 94, END_ID])
assert decoder_input == [START_ID, 72, 83, 94]
assert labels == [72, 83, 94, END_ID]
assert all(decoder_input[position] != labels[position]
           for position in range(len(labels)))''',
    'Constructing shifted labels uses O(T) time and memory for T target tokens. Teacher-forced training can score all target positions in parallel within a batch, while autoregressive serving emits tokens one step at a time and can incur T model invocations. Caching past keys and values reduces repeated decoder work but uses sequence-growing memory. The snippet checks only token alignment; it does not validate a tokenizer or full text quality.',
    ['Do not expose the next target token at its own prediction position.', 'Do not evaluate only teacher-forced loss when serving uses free generation.', 'Do not treat a missing source event as permission to invent one.'],
    ['deep-learning/encoder-decoder-cross-attention-and-source-mask', 'deep-learning/service-incident-seq2seq-project', 'deep-learning/causal-target-shift-and-padding-loss', 'deep-learning/decoding-stop-rules-and-beam-score', 'deep-learning/autoregressive-kv-cache-position-and-mask-parity'], SEQ)

add('service-incident-seq2seq-project',
    'Project: generate grounded summaries of service incidents',
    'Train an encoder-decoder model on time-bounded incident records, then gate release on source support, severe-fact recall and full-decoding behavior.', [
    ('Build a source-and-summary ledger', 'Each record needs incident ID, source event IDs, event timestamps, decision cutoff and a reviewed summary with links to supporting events. Remove notes written after the cutoff. Split by whole incident and reserve a later period or new service team. Store source and target tokenizer revisions. [[deep-learning/encoder-decoder-cross-attention-and-source-mask|The cross-attention lesson]] fixes source scope and padding.'),
    ('Fit against an extractive baseline', 'First make a deterministic summary from event fields and compare it with the proposed neural model. Train with shifted targets, separate source and target masks, and loss that ignores pad labels. The code exercises one synthetic encoder-decoder forward and loss; its random token IDs do not establish factual generation. [[deep-learning/teacher-forcing-shift-and-generation-parity|The shift lesson]] explains why the target input omits the token being predicted.'),
    ('Review actual generations', 'Decode complete summaries on held-out incidents. Mark unsupported statements, severe-event omissions, repeated claims and premature stopping. Report these rates by incident type and source length, alongside the percentage routed to manual review. Next-token accuracy is not a factuality measure. Compare against the extractive baseline at equal review time and count independent incidents rather than individual summary sentences.'),
    ('Replay serving constraints', 'At serving, restrict source records to events available by the requested cutoff. Test empty histories, duplicate events, truncated long histories and updates that arrive while a summary is generated. Measure source encoding, token-by-token decoding, evidence validation and p95 total time. Keep output tokens, source IDs and model revision in an audit record, without exposing private event data beyond the authorized view.'),
    ('Release with a safe fallback', 'Require zero unsupported severe claims in the reviewed gate set, acceptable severe-fact recall, a bounded review workload and response latency. If evidence is missing or validation fails, show the extractive event list or an unavailable status. Keep the prior workflow as rollback. Any later change to source schema, vocabulary or stop rule requires a new parity run.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

torch.manual_seed(47)
vocabulary_size = 101
source_ids = torch.tensor([[4, 7, 9, 0], [3, 8, 0, 0]])
target_ids = torch.tensor([[47, 12, 0], [47, 23, 0]])
source_padding = source_ids.eq(0)
target_padding = target_ids.eq(0)
embedding = nn.Embedding(vocabulary_size, 8)
seq2seq = nn.Transformer(d_model=8, nhead=2, num_encoder_layers=1,
                         num_decoder_layers=1, dim_feedforward=16,
                         dropout=0.0, batch_first=True)
causal_mask = torch.triu(torch.ones(3, 3, dtype=torch.bool), diagonal=1)
hidden = seq2seq(embedding(source_ids), embedding(target_ids),
                 tgt_mask=causal_mask, src_key_padding_mask=source_padding,
                 tgt_key_padding_mask=target_padding,
                 memory_key_padding_mask=source_padding)
vocabulary_head = nn.Linear(8, vocabulary_size)
logits = vocabulary_head(hidden)
next_token_labels = torch.tensor([[12, 58, 0], [23, 58, 0]])
loss = functional.cross_entropy(logits.reshape(-1, vocabulary_size),
                                next_token_labels.reshape(-1), ignore_index=0)
loss.backward()
assert logits.shape == (2, 3, vocabulary_size) and torch.isfinite(loss)''',
    'For B incidents, source length S, target length T and hidden width D, attention score work includes O(BS squared D), O(BT squared D) and O(BTSD). Full sequence decoding adds repeated steps and cache memory, while source tokenization and evidence checks add operational cost. The synthetic forward checks masks and gradient flow only; it does not train on real incidents or measure claim support.',
    ['Do not count post-cutoff events as available source evidence.', 'Do not claim grounded summaries from next-token loss alone.', 'Do not release without a fallback when the source ledger is incomplete.'],
    ['deep-learning/encoder-decoder-cross-attention-and-source-mask', 'deep-learning/teacher-forcing-shift-and-generation-parity', 'deep-learning/decoding-stop-rules-and-beam-score', 'deep-learning/service-event-decoder-parity-project', 'deep-learning/inference-schema-and-latency'], SEQ, True)

add('deep-ensemble-seed-diversity-and-disagreement',
    'Deep ensembles, seed diversity and predictive disagreement',
    'Independently trained networks can disagree on a case even when their averaged class probability looks confident; both signals need a review policy.', [
    ('Train independent members', 'A deep ensemble uses separately initialized models trained on the same declared training set, ideally with independently shuffled batches and documented seeds. Five checkpoints from one training run are not five independent fits. Keep architecture, class mapping, preprocessing and evaluation split consistent across members. For receipt damage triage, group receipts by store or acquisition session before any split so shared print defects do not leak into final evaluation. [[deep-learning/augmentation-leakage-boundary|The split lesson]] applies to every member.'),
    ('Average probabilities, not labels', 'Each member produces a probability distribution over the same classes. Average those distributions, then apply the operational threshold to the average. Majority vote discards score strength; averaging raw logits changes scale and is not generally equivalent. The code computes predictive entropy of the mean and the average member entropy. Their difference is a useful disagreement signal, but neither number alone proves calibrated risk.'),
    ('Separate uncertainty questions', 'High mean predictive entropy can arise because every model is unsure or because confident members disagree. The disagreement gap helps distinguish these patterns, yet it is sensitive to member diversity and calibration. Inspect both along with error rate. A severe defect that all models confidently miss will have low disagreement, so no uncertainty score replaces a stress test on uncommon damage and new scanners. [[deep-learning/temperature-scaling-and-selective-risk|Selective risk]] turns a chosen score into a review threshold.'),
    ('Account for cost and correlation', 'Training M independent members roughly multiplies training compute by M and stores M sets of weights. At serving, batching can share hardware overhead, but inference work and resident memory still grow. If all members share the same label errors or data blind spots, extra models add cost without reliable uncertainty. Compare ensemble performance with a single well-tuned model and record per-member failure overlap by store, lighting and defect type.'),
    ('Evaluate review yield', 'Select the review threshold on a development set. On untouched data, report severe-defect recall, risk among auto-approved cases, human review volume and error capture by the uncertainty queue. [[deep-learning/receipt-ensemble-review-project|The project]] checks those quantities under scanner and store shift. Do not report only an averaged accuracy score while operators face an unbounded queue.')],
    '''from math import log

def entropy(probabilities):
    if any(value < 0 for value in probabilities) or abs(sum(probabilities) - 1) > 1e-9:
        raise ValueError("class probabilities must form a distribution")
    return -sum(value * log(value) for value in probabilities if value > 0)

member_probabilities = [(.73, .18, .09), (.61, .28, .11), (.24, .65, .11)]
class_count = len(member_probabilities[0])
mean_probability = tuple(sum(member[class_id] for member in member_probabilities)
                         / len(member_probabilities) for class_id in range(class_count))
predictive_entropy = entropy(mean_probability)
mean_member_entropy = sum(map(entropy, member_probabilities)) / len(member_probabilities)
disagreement = predictive_entropy - mean_member_entropy
assert abs(sum(mean_probability) - 1) < 1e-9
assert disagreement >= -1e-12
assert predictive_entropy > mean_member_entropy''',
    'Aggregating M models across C classes costs O(MC) time and O(C) streaming accumulator space once their outputs exist. Model inference dominates: roughly M forward passes and M parameter sets, with possible parallelism at increased memory use. The entropy calculation is cheap but requires calibrated, aligned class probabilities. The sample distributions illustrate disagreement arithmetic, not a measured error probability.',
    ['Do not call several checkpoints from one run independent ensemble members.', 'Do not use low disagreement as proof that a prediction is correct.', 'Do not choose the review threshold on the final test set.'],
    ['deep-learning/mc-dropout-mode-and-batchnorm-boundary', 'deep-learning/receipt-ensemble-review-project', 'deep-learning/temperature-scaling-and-selective-risk', 'deep-learning/receipt-confidence-audit-project', 'deep-learning/augmentation-leakage-boundary'], UNCERTAINTY)

add('mc-dropout-mode-and-batchnorm-boundary',
    'Monte Carlo dropout, evaluation mode and batch-normalization boundaries',
    'Repeated stochastic forwards can expose prediction variation, but enabling dropout by putting the entire model in training mode can corrupt normalization behavior.', [
    ('Know which randomness is active', 'Standard inference disables dropout. Monte Carlo dropout intentionally keeps dropout masks changing over several no-gradient forwards, then averages probabilities. A model must actually contain and have been trained with dropout for this procedure to have the intended meaning. Preserve a fixed input and preprocessing pipeline across passes; otherwise input augmentation and dropout uncertainty are mixed. [[deep-learning/deep-ensemble-seed-diversity-and-disagreement|The ensemble lesson]] offers a separate multi-checkpoint comparison.'),
    ('Freeze batch normalization', 'Calling train on the entire network also makes batch-normalization layers use current-batch statistics and update running estimates. That can make the answer depend on neighboring requests or mutate the deployed model. Set the model to evaluation mode, then enable only the designated dropout modules. The code asserts batch normalization remains in evaluation mode and its running mean is unchanged across repeated forwards. Check any custom stochastic layers separately.'),
    ('Aggregate class probabilities', 'Run several passes under no-grad or inference mode, collect per-class probabilities, then calculate their mean and variability. Compare the resulting review queue with a normal deterministic forward. More passes reduce Monte Carlo sampling noise but increase latency almost linearly. A high variance can flag unstable predictions; a low variance can still conceal a confidently shared error. Calibration and severe-defect recall remain external checks.'),
    ('Keep request isolation', 'Changing module train flags on a shared model object can race with other inference requests. Use a dedicated stochastic copy, a scoped mode-restoration guard with serialization, or a serving architecture that isolates the uncertainty worker. The choice depends on concurrency requirements. Record the number of passes, seeds when reproducibility is needed and whether batch norm state remained fixed. Do not silently change normal production inference for every request.'),
    ('Measure the decision benefit', 'Report severe-defect error capture, auto-approval risk, review volume and p95 latency at several pass counts. If a three-member deep ensemble gives better review yield at similar cost, use that evidence; if deterministic temperature-scaled confidence is sufficient, extra stochastic forwards may be wasteful. [[deep-learning/receipt-ensemble-review-project|The applied project]] compares methods under held-out store and scanner changes.')],
    '''import torch
from torch import nn

torch.manual_seed(47)
receipt_features = torch.rand(4, 6)
review_model = nn.Sequential(nn.Linear(6, 8), nn.BatchNorm1d(8),
                             nn.ReLU(), nn.Dropout(p=0.35), nn.Linear(8, 2))
review_model.eval()
for layer in review_model.modules():
    if isinstance(layer, nn.Dropout):
        layer.train()
normalization = next(layer for layer in review_model.modules()
                     if isinstance(layer, nn.BatchNorm1d))
before = normalization.running_mean.clone()
with torch.inference_mode():
    probabilities = torch.stack([review_model(receipt_features).softmax(dim=1)
                                 for _ in range(7)])
mean_probability = probabilities.mean(dim=0)
assert probabilities.shape == (7, 4, 2)
assert torch.isfinite(mean_probability).all()
assert not normalization.training and torch.equal(before, normalization.running_mean)''',
    'For P stochastic passes and a model forward cost F, inference work is O(PF); storing all B-by-C probability matrices costs O(PBC), though streaming moments can reduce it to O(BC). Model weights remain one copy unless request isolation uses dedicated replicas. Batch-normalization state should not change. This synthetic mode check establishes the mechanics, not calibrated uncertainty or a production-safe concurrency strategy.',
    ['Do not call train on the whole model just to enable dropout.', 'Do not equate low dropout variance with low error risk.', 'Do not mutate a shared inference model’s mode without request isolation.'],
    ['deep-learning/deep-ensemble-seed-diversity-and-disagreement', 'deep-learning/receipt-ensemble-review-project', 'deep-learning/residual-blocks-and-normalization-state', 'deep-learning/temperature-scaling-and-selective-risk', 'deep-learning/inference-schema-and-latency'], UNCERTAINTY)

add('receipt-ensemble-review-project',
    'Project: route uncertain receipt defects to human review',
    'Compare a single classifier, independent ensemble and stochastic-dropout pass under identical receipt splits and a fixed review budget.', [
    ('Build a defect ledger', 'Keep receipt ID, store, scanner, capture session, reviewed defect class and review outcome. Split by store and acquisition period before augmentation, then hold back a new scanner or later store group for final evaluation. Include both severe and cosmetic damage, reflective paper, blur and partial scans. [[deep-learning/augmentation-leakage-boundary|The split rule]] prevents near-identical images from appearing on both sides of the final comparison.'),
    ('Fit and compare candidates', 'Train independent ensemble members with separate initialization seeds and documented shared data. Compare against the strongest single model and a model explicitly trained with dropout. The code aggregates three synthetic probability vectors and computes a disagreement score; it is a wiring check, not a trained detector. [[deep-learning/deep-ensemble-seed-diversity-and-disagreement|The ensemble lesson]] explains what member variation can and cannot reveal.'),
    ('Choose a review rule once', 'On development data, set a score threshold that fits the daily review capacity. Report the resulting auto-approval count, severe-defect recall, risk among auto-approved cases and errors caught by reviewers. Then freeze the rule for untouched stores and scanners. If a review queue exceeds staffing, the model must abstain or slow its auto-approval path according to an agreed policy, not lower the threshold after seeing final labels.'),
    ('Replay full latency', 'Measure image decode, preprocessing, all model forwards, aggregation and queue submission at intended concurrency. A seven-pass dropout path may be slower than an ensemble batched on a GPU. Keep batch normalization fixed for stochastic inference and test request isolation. [[deep-learning/mc-dropout-mode-and-batchnorm-boundary|The mode lesson]] prevents a serving worker from changing model state during another request.'),
    ('Release with explicit failure handling', 'Gate on severe-defect recall, auto-approved risk, review capacity and p95 response time by scanner slice. Route unreadable images and missing metadata to manual review rather than to a confident negative class. Package model member revisions, score calibration, threshold, preprocessing and rollback pointer. Review disagreements after launch and retrain only after a new independent evaluation split is prepared.')],
    '''from math import log

receipt_votes = [(.73, .18, .09), (.61, .28, .11), (.24, .65, .11)]
mean_vote = tuple(sum(vote[class_id] for vote in receipt_votes) / len(receipt_votes)
                  for class_id in range(3))

def uncertainty(distribution):
    return -sum(probability * log(probability) for probability in distribution
                if probability > 0)

predictive = uncertainty(mean_vote)
member_average = sum(map(uncertainty, receipt_votes)) / len(receipt_votes)
disagreement = predictive - member_average
review_threshold = 0.08
route_to_review = disagreement >= review_threshold
assert len(mean_vote) == 3 and abs(sum(mean_vote) - 1) < 1e-9
assert disagreement >= -1e-12
assert isinstance(route_to_review, bool)''',
    'Aggregating M member predictions for C classes takes O(MC) arithmetic and O(C) accumulator space. Training and serving M full models are the dominant costs; dropout uses one model but P stochastic forwards. A review queue adds human time that can exceed compute cost, so measure errors caught per reviewed receipt and daily queue volume. The synthetic vectors demonstrate aggregation only, not a validated threshold or detector.',
    ['Do not tune a review threshold on the untouched store test set.', 'Do not approve malformed images as clean because every model agrees.', 'Do not omit human review capacity from the operating cost.'],
    ['deep-learning/deep-ensemble-seed-diversity-and-disagreement', 'deep-learning/mc-dropout-mode-and-batchnorm-boundary', 'deep-learning/temperature-scaling-and-selective-risk', 'deep-learning/receipt-confidence-audit-project', 'deep-learning/inference-schema-and-latency'], UNCERTAINTY, True)

CROSSLINKS = [
    ('deep-learning/scaled-dot-product-attention-mask-contract', 'deep-learning/encoder-decoder-cross-attention-and-source-mask'),
    ('deep-learning/causal-target-shift-and-padding-loss', 'deep-learning/teacher-forcing-shift-and-generation-parity'),
    ('deep-learning/decoding-stop-rules-and-beam-score', 'deep-learning/service-incident-seq2seq-project'),
    ('deep-learning/service-event-decoder-parity-project', 'deep-learning/service-incident-seq2seq-project'),
    ('deep-learning/temperature-scaling-and-selective-risk', 'deep-learning/deep-ensemble-seed-diversity-and-disagreement'),
    ('deep-learning/residual-blocks-and-normalization-state', 'deep-learning/mc-dropout-mode-and-batchnorm-boundary'),
    ('deep-learning/receipt-confidence-audit-project', 'deep-learning/receipt-ensemble-review-project'),
    ('deep-learning/inference-schema-and-latency', 'deep-learning/receipt-ensemble-review-project'),
    ('deep-learning/deep-learning-tutorial', 'deep-learning/service-incident-seq2seq-project'),
]

if __name__ == '__main__':
    publish(LESSONS, (SEQ, UNCERTAINTY), CROSSLINKS,
            'aitrove-deep-learning-seq2seq-uncertainty-import-20261006.json',
            7980, subject='deep-learning')
