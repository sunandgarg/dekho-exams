"""Add adversarial generation and autoregressive inference paths."""
from de_batch_publisher import publish

GAN = 'Adversarial generation and coverage audits'
DECODER = 'Autoregressive decoding and cache parity'
LESSONS = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    assert len(sections) == 5
    LESSONS.append(dict(path='deep-learning/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add('gan-discriminator-generator-update-boundary',
    'GAN discriminator and generator update boundaries',
    'Adversarial training has two optimizers and two different gradient destinations; a mistaken detach or frozen-state rule can train the wrong network.', [
    ('Give each network one objective', 'The generator turns a noise vector into a candidate sample. The discriminator scores whether a sample resembles the training population. For a simple logistic setup, train the discriminator on real inputs as real and generator outputs as fake; train the generator so the discriminator calls its output real. The discriminator should return logits, not a probability already passed through sigmoid, when using a logits-based binary cross entropy. Check the input scale and generator output activation together. [[deep-learning/logits-loss-gradient|The logits contract]] prevents a silent extra sigmoid.'),
    ('Cut the graph during the discriminator step', 'When optimizing the discriminator, fake samples are training inputs for that network. Detach them from the generator graph so the discriminator backward pass does not spend memory producing generator gradients. Zero the discriminator gradients before its backward pass, then step only its optimizer. Real and fake batches should have compatible shapes and preprocessing. Do not cache old fake samples without documenting that policy; a stale fake distribution changes what the discriminator is asked to separate. The code uses a single tiny batch to expose the update boundary.'),
    ('Preserve input gradients during the generator step', 'For the generator update, compute fresh fake samples and pass them through the discriminator without detaching. The discriminator weights should not be updated, but the derivative of its score with respect to its input is needed to train the generator. Temporarily marking discriminator parameters nontrainable can save their gradient storage while still allowing gradients to flow into generated samples. Step only the generator optimizer, then restore discriminator parameter settings before the next discriminator update. A no-grad block around discriminator evaluation would sever the generator signal.'),
    ('Track more than a loss curve', 'A discriminator loss near a familiar value does not prove realistic output or balanced competition. Save fixed-noise outputs across checkpoints; measure generated diversity, nearest training neighbors and downstream utility. Watch gradient norms, score distributions on real and fake inputs, and whether one network becomes an easy shortcut detector for image borders or normalization. A generator can improve its own objective while producing a tiny set of repeated samples. [[deep-learning/gan-mode-coverage-and-duplicate-audit|Coverage auditing]] makes that failure measurable.'),
    ('Choose the adversarial variant deliberately', 'The example uses a non-saturating logistic generator loss because it gives a useful signal when the discriminator is initially confident. Other adversarial objectives have different score meanings and constraints; changing to a critic objective is not a one-line label swap. Keep optimizer settings, discriminator updates per generator update, batch order and model revision in the experiment manifest. Compare candidate checkpoints against a held-out real set and an applied task, not against the discriminator that co-trained with them. [[deep-learning/receipt-paper-texture-gan-project|The project]] gives a bounded use case.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

torch.manual_seed(47)
generator = nn.Sequential(nn.Linear(7, 24), nn.ReLU(), nn.Linear(24, 16), nn.Tanh())
discriminator = nn.Sequential(nn.Linear(16, 18), nn.ReLU(), nn.Linear(18, 1))
generator_optimizer = torch.optim.AdamW(generator.parameters(), lr=0.0004)
discriminator_optimizer = torch.optim.AdamW(discriminator.parameters(), lr=0.0003)
real_texture = torch.rand(5, 16) * 2 - 1
latent_noise = torch.randn(5, 7)

discriminator_optimizer.zero_grad(set_to_none=True)
detached_fake = generator(latent_noise).detach()
real_scores = discriminator(real_texture)
fake_scores = discriminator(detached_fake)
discriminator_loss = (functional.binary_cross_entropy_with_logits(
    real_scores, torch.ones_like(real_scores)) +
    functional.binary_cross_entropy_with_logits(
        fake_scores, torch.zeros_like(fake_scores))) / 2
discriminator_loss.backward()
discriminator_optimizer.step()

for parameter in discriminator.parameters():
    parameter.requires_grad_(False)
discriminator_optimizer.zero_grad(set_to_none=True)
generator_optimizer.zero_grad(set_to_none=True)
fresh_fake = generator(torch.randn(5, 7))
generator_scores = discriminator(fresh_fake)
generator_loss = functional.binary_cross_entropy_with_logits(
    generator_scores, torch.ones_like(generator_scores))
generator_loss.backward()
generator_optimizer.step()
for parameter in discriminator.parameters():
    parameter.requires_grad_(True)
assert torch.isfinite(generator_loss + discriminator_loss)''',
    'Each paired update performs one generator forward for discriminator training and another generator forward with a backward pass for generator training, plus discriminator forwards on real and fake inputs. The exact ratio depends on the chosen update schedule. Detaching the first fake batch avoids an unneeded generator graph, while freezing discriminator parameters during the second pass reduces gradient storage without removing its input derivative. Adversarial training can require many checkpoints and evaluations; one loss number is cheap but inadequate evidence of output quality.',
    ['Do not detach generator output during its own update.', 'Do not wrap the discriminator in no-grad during the generator update.', 'Do not interpret discriminator loss alone as a quality or coverage score.'],
    ['deep-learning/logits-loss-gradient', 'deep-learning/gan-mode-coverage-and-duplicate-audit', 'deep-learning/receipt-paper-texture-gan-project', 'deep-learning/diffusion-forward-noise-and-timestep-target', 'deep-learning/variational-latent-kl-and-collapse'], GAN)

add('gan-mode-coverage-and-duplicate-audit',
    'GAN mode coverage and near-duplicate audits',
    'A generator may fool its current discriminator while omitting entire parts of the target population or reproducing training images too closely.', [
    ('Separate fidelity from coverage', 'A small number of attractive samples says little about how much of the real population is represented. Partition a held-out real set into meaningful modes such as clean paper, folded edge, low exposure and textured background. Compare generated counts and feature distributions for every mode. These categories need not be training labels; they are an audit vocabulary for missing regions. A generator that emits only clean paper can look polished and still be useless for stress-testing a receipt classifier. [[deep-learning/gan-discriminator-generator-update-boundary|The training loss]] does not expose this omission.'),
    ('Fix sampling before comparison', 'Use a fixed seed list and a separately sampled seed list. The fixed set shows whether a checkpoint changed particular outputs; the fresh set estimates population variety. Keep generator revision, noise distribution, output normalization and sample count in the audit record. Never select the most flattering samples by hand for the coverage calculation. Report both within-set nearest-neighbor distances and distances to real training images. Low within-set distance suggests repetition; suspiciously low training-neighbor distance can signal memorization, though distance alone is not a privacy guarantee.'),
    ('Choose features that match the task', 'Pixel distance can be dominated by small alignment changes, while an image embedding may ignore a narrow cut-off edge. Use several comparisons: aligned raw pixels, a frozen general image feature and a receipt-quality feature. Inspect nearest pairs manually, particularly any generated sample resembling a training receipt with residual personal text. Do not train the audit feature on the final held-out set. The code below uses two-dimensional audit features to make assignments visible; production images need a validated feature extractor and a human-reviewed closest-pair sample.'),
    ('Detect memorization and mode collapse separately', 'A generator can collapse to a few novel outputs without copying training images, or copy many training images while covering apparent modes. Count unique generated neighborhoods and covered held-out modes, then inspect closest training neighbors. Compare the same measures at several checkpoints instead of assuming late training is always better. A discriminator overfitted to its own training set may reward a generator that exploits its blind spots. [[deep-learning/receipt-background-diffusion-project|The diffusion project]] uses a similar privacy and downstream-utility gate despite a different objective.'),
    ('Use downstream utility as a final gate', 'For augmentation, compare a receipt-quality model trained on real data alone with one trained on approved synthetic textures, holding real training identities and test data fixed. Report rare-defect recall, false accepts and device slices. Coverage of visual modes is necessary but not sufficient: a generated texture may have unrealistic correlations with defects. If the synthetic arm harms the held-out decision, do not release the samples merely because a feature-space score improved. [[deep-learning/receipt-paper-texture-gan-project|The applied project]] packages these audits.')],
    '''import torch

heldout_mode_centers = torch.tensor([[0.0, 0.0], [2.7, 0.3], [-1.6, 2.1]])
generated_features = torch.tensor([[0.1, -0.1], [0.2, 0.0],
                                   [2.6, 0.4], [2.9, 0.1],
                                   [0.0, 0.2], [2.8, 0.2]])
training_features = torch.tensor([[0.0, 0.1], [2.4, 0.3], [-1.5, 2.0]])
assigned_modes = torch.cdist(generated_features, heldout_mode_centers).argmin(dim=1)
covered_mode_count = int(torch.unique(assigned_modes).numel())
closest_training_distance = torch.cdist(
    generated_features, training_features).amin(dim=1)
pairwise = torch.cdist(generated_features, generated_features)
pairwise.fill_diagonal_(float("inf"))
closest_generated_distance = pairwise.amin(dim=1)
assert covered_mode_count == 2
assert closest_training_distance.shape == closest_generated_distance.shape == (6,)''',
    'For M generated samples, R real audit samples and feature width d, a brute-force real-neighbor scan costs O(MRd) time; a generated-pair scan costs O(M²d) time and O(M²) memory if the full matrix is kept. Chunked distance computation lowers peak memory, while approximate indexes trade exact neighbors for speed. Image encoding may dominate these comparisons. Audit cost grows with checkpoints and seeds, so choose a fixed protocol rather than silently reducing the sample size for weak candidates.',
    ['Do not present a small curated grid as evidence of population coverage.', 'Do not treat a single feature distance threshold as proof of privacy.', 'Do not use the co-trained discriminator as the sole quality judge.'],
    ['deep-learning/gan-discriminator-generator-update-boundary', 'deep-learning/receipt-paper-texture-gan-project', 'deep-learning/receipt-background-diffusion-project', 'deep-learning/receipt-confidence-audit-project', 'deep-learning/variational-latent-kl-and-collapse'], GAN)

add('receipt-paper-texture-gan-project',
    'Project: audit a receipt-paper texture GAN',
    'Generate text-free receipt-paper textures, then decide whether they add real held-out classifier value without sacrificing privacy or mode coverage.', [
    ('Limit the generated object', 'Use paper texture patches with merchant names, dates, amounts, barcodes and account information removed before training. Record the image range, patch size, removal process and physical-receipt split. Keep all crops of each receipt in one split. A tiny GAN can establish the update mechanics on synthetic vectors, but production texture work needs a suitable image generator and sufficient diverse data. Compare with the existing diffusion-background experiment rather than assuming one generative family wins. [[deep-learning/receipt-background-diffusion-project|That project]] has a matching downstream test.'),
    ('Train with separate optimizer ownership', 'Record discriminator and generator revisions, update ratio, noise distribution and fixed-seed visual outputs. During the discriminator update, detach generated patches; during the generator update, retain discriminator input gradients and step only the generator. Save both optimizer states if a run may resume. Monitor real/fake scores and gradient norms but do not treat a familiar score balance as success. [[deep-learning/gan-discriminator-generator-update-boundary|The update lesson]] gives the exact boundary. Reject any patch where text removal has left recognizable private fields.'),
    ('Audit every mode and near neighbor', 'Reserve real held-out texture patches for coverage measurement and set a fixed sampling protocol. Compare clean, creased, shadowed and fibrous paper groups, then inspect nearest generated-to-training pairs. Test multiple image feature spaces because a broad feature can miss faint text. Manually review the closest pairs and record exclusions. The code below defines a release gate over measured outcomes; its illustrative numbers are not a claim about a trained generator. [[deep-learning/gan-mode-coverage-and-duplicate-audit|Coverage auditing]] specifies the inputs to that gate.'),
    ('Run the paired downstream experiment', 'Train a receipt-quality classifier once on approved real examples alone and once with approved synthetic backgrounds, keeping label budget, model, optimizer and real test identities fixed. Measure blur and clipped-edge recall, false accepts and manual-review load on real held-out captures. Report generated sample counts and how many were rejected in privacy or coverage screening. Synthetic variety does not automatically produce useful variation for a particular classifier; the downstream decision is the final arbiter.'),
    ('Release a reversible artifact', 'Package the generator, preprocessing, removal method, seed manifest, nearest-neighbor audit and paired classifier results. Set minimum covered-mode count, maximum unreviewed near-duplicate count and class-specific decision gates before final testing. If any gate fails, keep the generator out of production augmentation. A later generator checkpoint must repeat every gate because adversarial training can gain one mode while losing another. Maintain the previous approved training set and classifier for rollback.')],
    '''from dataclasses import dataclass

@dataclass(frozen=True)
class TextureAudit:
    covered_modes: int
    private_or_unreviewed_neighbors: int
    clipped_edge_recall: float
    false_accepts: int

def rejection_reasons(reference: TextureAudit,
                      candidate: TextureAudit) -> list[str]:
    failures = []
    if candidate.covered_modes < 4:
        failures.append("missing paper mode")
    if candidate.private_or_unreviewed_neighbors != 0:
        failures.append("unresolved neighbor audit")
    if candidate.clipped_edge_recall < reference.clipped_edge_recall:
        failures.append("clipped-edge recall")
    if candidate.false_accepts > reference.false_accepts:
        failures.append("false accepts")
    return failures

real_only = TextureAudit(4, 0, 0.93, 2)
synthetic_arm = TextureAudit(3, 0, 0.94, 2)
assert rejection_reasons(real_only, synthetic_arm) == ["missing paper mode"]''',
    'Training uses two networks and often several discriminator evaluations per generator update; generator inference alone is cheaper than training. The expensive evidence is repeated sampling, nearest-neighbor inspection and paired downstream model training. The gate function is O(1) once its inputs are measured, but calculating exact image-neighbor distances can be O(MRd) for M generated samples, R training images and embedding width d. Report audit sample sizes and device cost instead of presenting illustrative code values as measured results.',
    ['Do not train on paper patches that retain private receipt text.', 'Do not release after a curated image review without coverage and neighbor counts.', 'Do not assume lower generator loss improves real held-out classifier decisions.'],
    ['deep-learning/gan-discriminator-generator-update-boundary', 'deep-learning/gan-mode-coverage-and-duplicate-audit', 'deep-learning/receipt-background-diffusion-project', 'deep-learning/receipt-image-quality-project', 'deep-learning/receipt-confidence-audit-project'], GAN, True)

add('autoregressive-kv-cache-position-and-mask-parity',
    'Autoregressive KV cache position and mask parity',
    'Caching attention keys and values avoids repeating earlier projections, but one wrong position or mask can change the next-token distribution silently.', [
    ('Separate prefill from decode', 'A causal decoder first processes the supplied prefix. During this prefill, each position may attend only to allowed earlier positions. Afterward, each new token contributes a key and value at its own absolute position; the next query attends to all permitted cached positions. A cache stores per-layer key and value tensors, not merely the final logits. It should be associated with one exact prefix, model revision and attention configuration. [[deep-learning/scaled-dot-product-attention-mask-contract|Attention masks]] define which cached positions are visible.'),
    ('Keep position and padding rules aligned', 'For a padded batch, the visible-token count and the physical tensor index may differ. An incremental position ID must match the model’s training and full-forward convention. Reusing a prefix cache for a different prefix, or appending at an off-by-one position, can produce fluent-looking but numerically different outputs. Check each batch member separately when lengths differ. Sliding-window and other bounded-attention layers also evict old states by a model-specific rule; simply concatenating every past key can violate that rule. Record cache length and visible-token count at each step.'),
    ('Prove one-head arithmetic first', 'The code below compares attention over a four-position key/value array with attention over a three-position cache followed by one appended position. Both calls use the same final query and the same keys and values; exact numerical parity is expected. This is an algebra check for one attention operation, not a whole-transformer cache implementation. A full parity test must compare logits from an uncached full-prefix forward against incremental forwards across several lengths, batch padding patterns and device precisions.'),
    ('Count the memory trade', 'Without caching, repeated decoding projects earlier tokens again and revisits the growing prefix. A cache avoids much repeated projection work, yet keys and values occupy memory proportional to layer count, retained sequence length, head count and head width. Beam search may multiply that memory by the number of live hypotheses, and cached rows must be reordered when beams are selected. [[deep-learning/decoding-stop-rules-and-beam-score|Decoding policies]] determine how many hypotheses survive each step. Measure first-token latency, later-token latency and peak cache memory separately.'),
    ('Test cache invalidation', 'Invalidate a cache when the model revision, tokenizer, prefix text, prefix mask, position convention or context-window policy changes. If two user requests share a prefix, sharing a mutable cache object can leak one request’s appended tokens into another; copy or isolate state before decoding. Compare fixed-prefix logits after serialization and reload, and deliberately alter one prefix token to ensure cache reuse is rejected. [[deep-learning/service-event-decoder-parity-project|The project]] turns these checks into a release test for event sequences.')],
    '''import math
import torch
from torch.nn import functional as functional

torch.manual_seed(47)
projected_keys = torch.randn(1, 4, 8)
projected_values = torch.randn(1, 4, 8)
last_query = torch.randn(1, 1, 8)

def attended_value(query, keys, values):
    scores = query @ keys.transpose(-2, -1) / math.sqrt(keys.shape[-1])
    return functional.softmax(scores, dim=-1) @ values

full_result = attended_value(last_query, projected_keys, projected_values)
cached_keys = projected_keys[:, :3, :]
cached_values = projected_values[:, :3, :]
updated_keys = torch.cat((cached_keys, projected_keys[:, 3:4, :]), dim=1)
updated_values = torch.cat((cached_values, projected_values[:, 3:4, :]), dim=1)
cached_result = attended_value(last_query, updated_keys, updated_values)
torch.testing.assert_close(full_result, cached_result)
assert updated_keys.shape == (1, 4, 8)''',
    'For L retained tokens, H attention heads, width d per head and N layers, storing keys and values requires O(2NLHd) elements per request before allocator overhead. A decode step still compares its query with up to L keys, so the attention portion is not constant time. Cache use removes repeated earlier key/value projection and much full-prefix recomputation; the actual latency gain depends on model architecture, kernel and memory pressure. The simple code recomputes only one attention output and does not benchmark a transformer.',
    ['Do not reuse a mutable cache across different request prefixes.', 'Do not assume padded tensor index equals the next visible position.', 'Do not compare cached and full runs with different masks or position IDs.'],
    ['deep-learning/scaled-dot-product-attention-mask-contract', 'deep-learning/causal-target-shift-and-padding-loss', 'deep-learning/decoding-stop-rules-and-beam-score', 'deep-learning/service-event-decoder-parity-project', 'deep-learning/inference-schema-and-latency'], DECODER)

add('decoding-stop-rules-and-beam-score',
    'Decoding stop rules, sampling and beam-score accounting',
    'Token generation is a decision policy over logits; stopping, forbidden tokens and sequence scores affect output as much as the next-token model does.', [
    ('Mask invalid tokens before sampling', 'A decoder may forbid padding, a start marker after the prefix or application-specific events. Apply those masks to raw logits before softmax, and reject a step where every candidate is forbidden. Renormalize the remaining distribution. For top-p sampling, sort valid probabilities and keep the smallest prefix whose cumulative mass reaches the threshold, including the token that crosses it. Sample from the retained, renormalized probabilities with an explicit random generator. The code demonstrates one step with a fixed seed; it is not a language-quality claim.'),
    ('Define stopping independently of padding', 'An end token terminates a generated sequence; padding only fills a batch tensor and must not be interpreted as a model-selected end. Set a maximum new-token count as a hard guard even when the model usually emits an end token. State whether the end token is included in stored output and whether a minimum generated length suppresses it temporarily. If a model never emits end, return a capped status rather than silently presenting a complete sequence. [[deep-learning/causal-target-shift-and-padding-loss|The shifted training target]] must include the intended end event.'),
    ('Score beams with the same units', 'Beam search accumulates log probabilities for each candidate sequence and keeps a bounded number of live hypotheses. Raw summed log probability favors short sequences because every added token contributes a nonpositive term. A length normalization or penalty changes the ranking; document its formula and when it is applied. Finished beams must not keep collecting token probability. When live beams are reordered, reorder their per-layer caches and any batch-specific masks with the same parent indices. [[deep-learning/autoregressive-kv-cache-position-and-mask-parity|Cache parity]] is part of beam correctness.'),
    ('Separate diversity from correctness', 'Greedy decoding is deterministic under a fixed model and preprocessing. Sampling introduces variation; beam search optimizes a score under a finite search width, not factual or task correctness. Compare output validity, duplicate sequences, event-order constraints and error costs under a fixed held-out prefix set. Top-p and temperature change the distribution; a lower temperature is not a substitute for a trained model that respects domain rules. For service events, invalid order may need a constrained decoder or a post-decode rejection path.'),
    ('Budget the requested length', 'Latency rises with generated tokens, and beam search adds model and cache work for multiple hypotheses. Report time to first event, later-event rate, p95 whole-request latency and capped-output fraction. A model with good per-token accuracy can be unusable if it rarely emits end. Keep decoding settings in the serving artifact, not in an undocumented caller default. [[deep-learning/service-event-decoder-parity-project|The applied project]] compares policies under event-sequence contracts.')],
    '''import torch
from torch.nn import functional as functional

torch.manual_seed(47)
event_logits = torch.tensor([1.2, 0.8, 2.1, -0.3, 0.4])
start_token, padding_token = 0, 4
masked_logits = event_logits.clone()
masked_logits[[start_token, padding_token]] = float("-inf")
if not torch.isfinite(masked_logits).any():
    raise ValueError("no permitted next event")
sorted_logits, sorted_ids = torch.sort(masked_logits, descending=True)
sorted_probabilities = functional.softmax(sorted_logits, dim=0)
cumulative_mass = torch.cumsum(sorted_probabilities, dim=0)
keep = cumulative_mass - sorted_probabilities < 0.82
candidate_ids = sorted_ids[keep]
candidate_probabilities = sorted_probabilities[keep]
candidate_probabilities /= candidate_probabilities.sum()
sampled_offset = torch.multinomial(candidate_probabilities, 1)
next_event = int(candidate_ids[sampled_offset])
assert next_event not in (start_token, padding_token)
assert len(candidate_ids) >= 1''',
    'Sorting V vocabulary logits for top-p selection costs O(V log V) time per generated token; selecting a fixed top-k can be cheaper. Beam search generally multiplies decode-state storage and candidate scoring by beam width, though batching can improve hardware use. A maximum of K new tokens bounds work and cache growth for a request. The five-logit code is a policy check; real latency includes model forward passes, cache movement and output serialization, which should be measured at realistic prefix and output lengths.',
    ['Do not treat padding as a generated end token.', 'Do not discard the token that first crosses the top-p cumulative threshold.', 'Do not compare beam sums across lengths without the stated normalization rule.'],
    ['deep-learning/causal-target-shift-and-padding-loss', 'deep-learning/autoregressive-kv-cache-position-and-mask-parity', 'deep-learning/service-event-decoder-parity-project', 'deep-learning/scaled-dot-product-attention-mask-contract', 'deep-learning/inference-schema-and-latency'], DECODER)

add('service-event-decoder-parity-project',
    'Project: release an incremental service-event decoder',
    'Train a next-event model, then prove cached decoding, stop behavior and event-order rules on held-out service sessions before serving predictions.', [
    ('Freeze a session grammar', 'Represent service events with an explicit start token, end token and padding token, plus domain events such as opened, assigned, repaired and closed. Split by service session and, where appropriate, customer or asset; do not let a session prefix appear in training while its suffix becomes a held-out target. Construct shifted targets so each position predicts the next event and ignore padding in loss. [[deep-learning/causal-target-shift-and-padding-loss|The target-shift lesson]] gives the training audit. Keep tokenizer and event-ID mapping versioned.'),
    ('Establish full-prefix behavior', 'Train a modest causal decoder or start with an existing one and save logits for fixed held-out prefixes. Verify that appending a future event cannot change earlier-position logits. Include a one-event prefix, a padded mixed-length batch and a prefix exactly at the context boundary. A high teacher-forced next-token score is insufficient if deployment decoding has a different mask or position convention. [[deep-learning/sequence-attention-leakage-project|The attention leakage project]] gives the causal test pattern.'),
    ('Prove cache parity step by step', 'Prefill the same prefix and compare each next-event logit vector from the full-prefix path with the cached incremental path across several append steps. Keep dropout disabled, masks aligned and the same precision. Deliberately alter one prefix or model revision and verify its cache is rejected. If beam search is enabled, reorder every cache layer when parent beams change. The code below supplies a small pure-Python release checker over measured maximum logit gaps and request identities; the model-specific cache implementation must produce those measurements. [[deep-learning/autoregressive-kv-cache-position-and-mask-parity|The cache lesson]] explains the memory trade.'),
    ('Exercise stop and invalid-order cases', 'For a fixed held-out prefix set, compare greedy, sampled and beam policies under the same maximum new-event count. Verify that end stops output, padding never appears as an emitted event, and unfinished sequences are tagged as capped. Reject impossible orderings such as closed followed by assigned unless the domain explicitly allows reopening. Measure invalid-event rate and sequence duplication, not only token accuracy. [[deep-learning/decoding-stop-rules-and-beam-score|The policy lesson]] defines the controls.'),
    ('Publish a bounded serving artifact', 'Package model revision, tokenizer, event-order rules, cache strategy, stopping policy, maximum prefix and output lengths, and the exact parity tolerance. Measure first-event and p95 whole-request latency, peak cache memory and invalid-sequence rate at intended concurrency. A parity failure blocks cache acceleration; a policy failure blocks the new decoding setting even if model logits are correct. Keep a full-prefix or previous-version fallback until fixed-batch replay and monitored rollout pass.')],
    '''from dataclasses import dataclass

@dataclass(frozen=True)
class DecodeAudit:
    matching_prefix: bool
    maximum_logit_gap: float
    emitted_padding: int
    invalid_event_orders: int
    capped_sequences: int

def release_failures(result: DecodeAudit, allowed_gap: float,
                     allowed_capped: int) -> list[str]:
    failures = []
    if not result.matching_prefix or result.maximum_logit_gap > allowed_gap:
        failures.append("cache parity")
    if result.emitted_padding:
        failures.append("padding emission")
    if result.invalid_event_orders:
        failures.append("event grammar")
    if result.capped_sequences > allowed_capped:
        failures.append("end-token coverage")
    return failures

heldout_audit = DecodeAudit(True, 0.00003, 0, 1, 2)
assert release_failures(heldout_audit, 0.0001, 3) == ["event grammar"]''',
    'Full-prefix parity evaluation repeats a growing prefix and can be costly across many held-out sessions, but it is a one-time release check rather than a serving path. Cache memory grows with retained context, layers and concurrent requests; beam width can multiply it. The pure-Python gate is O(1) after metrics are collected. Runtime benchmarks must include tokenizer work, prefill, each decode step and session-specific masks. An illustrative passing tolerance does not replace a device-specific numerical study.',
    ['Do not cache one request prefix and reuse it for a different service session.', 'Do not mark capped sequences complete when no end token was emitted.', 'Do not release a fast decoder with an invalid event-order rate hidden inside average token accuracy.'],
    ['deep-learning/autoregressive-kv-cache-position-and-mask-parity', 'deep-learning/decoding-stop-rules-and-beam-score', 'deep-learning/causal-target-shift-and-padding-loss', 'deep-learning/sequence-attention-leakage-project', 'deep-learning/service-event-lstm-project'], DECODER, True)

CROSSLINKS = [
    ('deep-learning/logits-loss-gradient', 'deep-learning/gan-discriminator-generator-update-boundary'),
    ('deep-learning/variational-latent-kl-and-collapse', 'deep-learning/gan-mode-coverage-and-duplicate-audit'),
    ('deep-learning/diffusion-forward-noise-and-timestep-target', 'deep-learning/receipt-paper-texture-gan-project'),
    ('deep-learning/receipt-background-diffusion-project', 'deep-learning/receipt-paper-texture-gan-project'),
    ('deep-learning/receipt-image-quality-project', 'deep-learning/receipt-paper-texture-gan-project'),
    ('deep-learning/scaled-dot-product-attention-mask-contract', 'deep-learning/autoregressive-kv-cache-position-and-mask-parity'),
    ('deep-learning/causal-target-shift-and-padding-loss', 'deep-learning/decoding-stop-rules-and-beam-score'),
    ('deep-learning/sequence-attention-leakage-project', 'deep-learning/service-event-decoder-parity-project'),
    ('deep-learning/service-event-lstm-project', 'deep-learning/service-event-decoder-parity-project'),
    ('deep-learning/inference-schema-and-latency', 'deep-learning/autoregressive-kv-cache-position-and-mask-parity'),
    ('deep-learning/deep-learning-tutorial', 'deep-learning/service-event-decoder-parity-project'),
]

if __name__ == '__main__':
    publish(LESSONS, (GAN, DECODER), CROSSLINKS,
            'aitrove-deep-learning-gan-decoder-import-20261006.json',
            7880, subject='deep-learning')
