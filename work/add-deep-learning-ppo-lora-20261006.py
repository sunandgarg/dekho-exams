"""Add PPO and low-rank-adaptation learning paths."""
from de_batch_publisher import publish

PPO = 'Actor-critic rollouts and clipped policy updates'
LORA = 'Low-rank adapters and merge parity'
LESSONS = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    assert len(sections) == 5
    LESSONS.append(dict(path='deep-learning/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add('ppo-rollout-advantage-and-bootstrap-boundary',
    'PPO rollouts, advantage estimates and bootstrap boundaries',
    'An actor-critic update begins with fresh policy data; its advantage calculation must distinguish true endings from collection cutoffs.', [
    ('Collect one policy version', 'A warehouse simulator should record the observation available before dispatch, the chosen action, its old log probability, reward, value estimate, next observation and action mask. Keep the policy and reward versions with each rollout. PPO may optimize several times against this fixed batch, but newly collected data belongs to a new policy version. Mixing the two makes probability ratios meaningless. [[deep-learning/dqn-transition-replay-and-reward-contract|The transition lesson]] covers observation timing shared with DQN.'),
    ('Separate endings from cutoffs', 'A true terminal shift cannot bootstrap a future value. A collector may stop after a fixed number of steps while the shift continues; that cutoff can use the critic value of the next observation. Both cases stop advantage recursion before an unrelated trajectory. The code stores terminal and cutoff separately. Treating every cutoff as terminal biases returns downward; carrying a recurrence into the next shift mixes unrelated outcomes.'),
    ('Work backward through rewards', 'At each step compute reward plus discounted next value when nonterminal, minus the current value. Propagate later errors backward with discount and trace decay until an episode boundary. This produces an advantage estimate while allowing control over variance and bias. Save the critic predictions made during collection; do not silently recompute old values after a critic update. Check several tiny episodes by hand before training at scale.'),
    ('Respect legal actions', 'Save the eligibility mask used when the action was sampled. A later mask change alters its log probability and can corrupt the policy ratio. For a transfer action, stock availability must be determined from the pre-decision state, not a post-decision inventory count. [[deep-learning/dqn-target-network-and-action-mask|The action-mask lesson]] explains why a neural score never overrides legality. Invalid logged actions should fail data validation rather than enter the optimizer.'),
    ('Evaluate independent shifts', 'Normalize advantages only within a declared training batch and keep reward values in their original units for evaluation. Report order completion, late orders, stockouts and illegal actions by independent held-out shift. A lower surrogate loss can coexist with worse decisions. [[deep-learning/warehouse-shift-ppo-project|The applied project]] compares a policy against a fixed dispatch baseline under matched demand draws.')],
    '''def advantages(rewards, values, following, terminal, cutoff,
               discount=0.93, decay=0.87):
    count = len(rewards)
    if not count or any(len(part) != count for part in
                        (values, following, terminal, cutoff)):
        raise ValueError("rollout fields must align")
    result = [0.0] * count
    carry = 0.0
    for step in range(count - 1, -1, -1):
        next_value = 0.0 if terminal[step] else discount * following[step]
        error = rewards[step] + next_value - values[step]
        carry = error + (0.0 if cutoff[step] else discount * decay * carry)
        result[step] = carry
    return result

shift_advantages = advantages([2., -1., 3.], [1., .5, 1.2],
                              [.5, 0., .7], [False, True, False],
                              [False, True, True])
assert len(shift_advantages) == 3
assert abs(shift_advantages[1] + 1.5) < 1e-9
assert abs(shift_advantages[2] - 2.451) < 1e-9''',
    'For T rollout steps, this backward pass uses O(T) time and O(T) output memory. Observations and action masks usually dominate collection storage. Several optimizer epochs reuse the same environment experience but cost repeated network passes and can move the policy too far from its recorded behavior. Simulator steps may dominate wall time even when this recurrence is cheap.',
    ['Do not bootstrap from a truly terminal state.', 'Do not propagate advantages across unrelated shifts.', 'Do not recompute old action probabilities with updated actor weights.'],
    ['deep-learning/ppo-clipped-policy-ratio-and-kl-guard', 'deep-learning/warehouse-shift-ppo-project', 'deep-learning/dqn-transition-replay-and-reward-contract', 'deep-learning/dqn-target-network-and-action-mask', 'deep-learning/train-eval-validation-loop'], PPO)

add('ppo-clipped-policy-ratio-and-kl-guard',
    'PPO clipped policy ratios, critic loss and KL guards',
    'Clipping limits the update incentive on sampled actions, while critic error and policy movement still need separate checks.', [
    ('Use the recorded denominator', 'Subtract the old log probability captured during rollout from the current actor log probability for the same state, action and legal-action mask. Exponentiating gives the probability ratio. A ratio close to one means little movement on that recorded action, not necessarily every action. [[deep-learning/ppo-rollout-advantage-and-bootstrap-boundary|The rollout contract]] freezes the old denominator and makes accidental reuse of stale data visible.'),
    ('Clip the objective', 'Multiply the ratio by the estimated advantage and compare that contribution with the ratio clamped around one. Choose the smaller contribution for maximization, or minimize its negative. Positive and negative advantages respond differently; test both signs on a small batch. The code checks finite gradients in this objective. The clamp limits a particular incentive, but repeated optimization or other losses can still move the full policy substantially.'),
    ('Keep critic diagnostics separate', 'The critic predicts discounted return; it is not a second action chooser. Fit it against returns built from rollout estimates and advantages. Report value error apart from actor loss, especially if both share a feature encoder. Record entropy and its coefficient if used for exploration. [[deep-learning/adamw-decay-groups-and-update-indexed-schedules|Optimizer settings]] and clipping thresholds belong in the checkpoint, not in undocumented notebook cells.'),
    ('Watch policy movement', 'Track approximate KL on collected states, ratio spread, clipping fraction and entropy by optimizer epoch. Define a KL stop rule before the experiment. The estimate is diagnostic, not a guarantee about unvisited states. If most ratios are clipped, more epochs may waste compute or worsen decisions. Compare across independent simulator seeds instead of selecting the smoothest training curve.'),
    ('Gate operating outcomes', 'Evaluate order completion, stockouts, late orders, transfer cost and action-mask violations on held-out demand sequences. A healthy surrogate objective cannot compensate for a reward booked twice or an incorrect simulator. [[deep-learning/warehouse-shift-ppo-project|The project]] keeps episode-level service gates and a deterministic rollback policy alongside training metrics.')],
    '''import torch
from torch import nn
from torch.distributions import Categorical

torch.manual_seed(47)
stock_states = torch.tensor([[8., 3.], [5., 0.], [7., 2.]])
legal_actions = torch.tensor([[True, True], [True, False], [True, True]])
recorded_actions = torch.tensor([1, 0, 0])
estimated_advantages = torch.tensor([1.3, -0.7, 0.4])
actor = nn.Linear(2, 2)
new_logits = actor(stock_states).masked_fill(~legal_actions, -1e9)
new_log_prob = Categorical(logits=new_logits).log_prob(recorded_actions)
old_log_prob = new_log_prob.detach() - torch.tensor([0.12, -0.09, 0.05])
ratio = (new_log_prob - old_log_prob).exp()
unclipped = ratio * estimated_advantages
clipped = ratio.clamp(0.83, 1.17) * estimated_advantages
actor_loss = -torch.minimum(unclipped, clipped).mean()
actor_loss.backward()
assert torch.isfinite(actor_loss) and actor.weight.grad is not None''',
    'For B samples and A actions, the probability calculation and mask add O(BA) operations around the actor forward. Extra optimizer epochs multiply network compute and activation storage. Old log probabilities, actions, masks and advantages occupy O(B) to O(BA) rollout memory. Clipping has no hard guarantee on complete policy divergence; measure KL and held-out episode behavior.',
    ['Do not recompute the denominator with the new actor.', 'Do not call objective clipping a hard safety constraint.', 'Do not hide critic collapse inside a combined loss value.'],
    ['deep-learning/ppo-rollout-advantage-and-bootstrap-boundary', 'deep-learning/warehouse-shift-ppo-project', 'deep-learning/adamw-decay-groups-and-update-indexed-schedules', 'deep-learning/early-stopping-best-state-and-seed-variance', 'deep-learning/dqn-target-network-and-action-mask'], PPO)

add('warehouse-shift-ppo-project',
    'Project: audit a warehouse-shift PPO dispatcher',
    'Train an actor-critic policy in a versioned simulator and gate release on episode service, legality and response time.', [
    ('Specify the environment', 'At each order event, the actor sees stock, known inbound units, backlog and remaining shift time. Actions are wait or transfer one spare unit when available. Book service and transfer costs exactly once, then log observation, mask, decision, reward and next state. Freeze demand seeds and supplier-delay assumptions for each comparison. [[deep-learning/ppo-rollout-advantage-and-bootstrap-boundary|The rollout lesson]] separates terminal shifts from collection cutoffs.'),
    ('Establish fixed baselines', 'Run the existing threshold dispatch rule and a no-transfer policy under the same demand draws. Record completed orders, late orders, stockouts, expedited moves and invalid attempts in natural units before compressing them into reward. Choose reward weights only with development simulations. A learned actor that raises weighted reward while increasing stockouts fails the service gate. Hold back later demand periods and different delay regimes.'),
    ('Train with measured updates', 'Collect fresh rollouts with old action log probabilities, compute advantages and returns, then apply a limited number of clipped actor-critic updates. Track value error, ratio clipping, approximate KL, entropy and action frequency. The snippet makes one synthetic update to verify the tensor path; it is not a trained warehouse controller. [[deep-learning/ppo-clipped-policy-ratio-and-kl-guard|The update lesson]] explains the early-stop guard.'),
    ('Stress independent shifts', 'Evaluate multiple held-out demand seeds, burst periods, supplier delays and missing stock observations. Report mean and lower-tail return, stockouts, late orders, illegal actions and disagreements against the baseline. Replay each decision with only information available at that moment. Inspect any shift where return improves but a service metric worsens. Save failure traces with environment and policy versions for reproduction.'),
    ('Release behind a hard filter', 'Shadow-score operational events before allowing any action. Keep a deterministic legality filter, timeout fallback and the old dispatcher. Require no increase in stockouts, a defined lateness budget and bounded p95 decision time. Package actor, critic, feature schema, reward version and rollback pointer. Simulator gains alone do not establish safe unsupervised dispatch.')],
    '''import torch
from torch import nn
from torch.distributions import Categorical
from torch.nn import functional as functional

torch.manual_seed(47)
states = torch.tensor([[8., 3., 2.], [5., 0., 1.], [7., 2., 3.]])
legal = torch.tensor([[True, True], [True, False], [True, True]])
actions = torch.tensor([1, 0, 0])
returns = torch.tensor([2.4, -1.1, 3.2])
actor, critic = nn.Linear(3, 2), nn.Linear(3, 1)
optimizer = torch.optim.AdamW(list(actor.parameters()) + list(critic.parameters()), lr=.0007)
new_log_prob = Categorical(logits=actor(states).masked_fill(~legal, -1e9)).log_prob(actions)
old_log_prob = new_log_prob.detach() - torch.tensor([.1, -.08, .04])
values = critic(states).squeeze(1)
advantage = returns - values.detach()
ratio = (new_log_prob - old_log_prob).exp()
actor_loss = -torch.minimum(ratio * advantage, ratio.clamp(.83, 1.17) * advantage).mean()
loss = actor_loss + .4 * functional.smooth_l1_loss(values, returns)
optimizer.zero_grad(set_to_none=True)
loss.backward()
optimizer.step()
assert torch.isfinite(loss) and all(legal[row, action] for row, action in enumerate(actions))''',
    'A training update evaluates actor and critic on B samples; repeated epochs multiply that cost. Rollout generation takes E environment steps and may dominate elapsed time, while stored masks can require O(EA) memory for A actions. The synthetic batch checks only finite gradients and legal recorded choices. A release needs independent episode measurements, simulator validation and a hard serving guard.',
    ['Do not mistake a synthetic update for measured dispatch performance.', 'Do not reuse stale rollout probabilities after a policy revision.', 'Do not remove the hard action filter when the actor scores well.'],
    ['deep-learning/ppo-rollout-advantage-and-bootstrap-boundary', 'deep-learning/ppo-clipped-policy-ratio-and-kl-guard', 'deep-learning/inventory-dispatch-dqn-project', 'deep-learning/dqn-transition-replay-and-reward-contract', 'deep-learning/inference-schema-and-latency'], PPO, True)

add('lora-rank-scaling-and-frozen-base-contract',
    'LoRA rank, scaling and frozen-base contracts',
    'Low-rank adapters train two small matrices around a frozen map; their savings depend on target layers, activations and exact base identity.', [
    ('Count the changed weights', 'For a projection from 47 inputs to 83 outputs, a rank-four adapter trains four times the sum of 47 and 83, or 520 matrix entries. The base map holds 47 times 83, or 3,901 entries, and stays resident even when frozen. The effective update is a scaled product of the two adapter factors. Record any trainable biases or task head separately; freezing one layer is not freezing the entire encoder.'),
    ('Choose target projections', 'Adapters can modify attention query and value projections, output projections or feed-forward maps. More targets increase trainable memory and capacity. Start with a measured subset, then compare held-out quality and peak memory against full fine-tuning and a frozen-feature baseline. [[deep-learning/frozen-features-versus-fine-tuning|The transfer lesson]] frames that choice. A small rank can underfit a task; it is not a universal defense against overfitting.'),
    ('Initialize without a surprise change', 'A zero-initialized output factor makes the adapted model initially match the frozen base. Scaling, often alpha divided by rank, sets the update magnitude and belongs in saved metadata. With both factors initialized nonzero, the first forward already differs from the base. The snippet verifies base-output parity at initialization and confirms only adapter weights receive gradients. Compare several seeds when selecting rank and scaling.'),
    ('Profile actual memory', 'Freezing base weights avoids their gradients and optimizer-state tensors, yet the base weights and forward activations still consume memory. Long sequences can make activations the dominant expense. Quantizing the frozen base changes arithmetic and needs separate calibration; it is not merely a smaller file. [[deep-learning/training-memory-profiler-and-allocator-boundaries|The memory lesson]] separates reserved memory from active tensors.'),
    ('Keep the adapter attached to its base', 'Save the exact base-checkpoint fingerprint, targeted layer names, rank, scaling, dropout, tokenizer and feature schema with adapter weights. A different base can accept the same tensor shapes while producing incorrect outputs. [[deep-learning/lora-merge-parity-and-adapter-identity|The merge lesson]] checks that the exported combined weight reproduces the unmerged evaluation path.')],
    '''import torch
from torch import nn

torch.manual_seed(47)
base = nn.Linear(47, 83, bias=False)
base.weight.requires_grad_(False)
down = nn.Linear(47, 4, bias=False)
up = nn.Linear(4, 83, bias=False)
nn.init.zeros_(up.weight)
features = torch.rand(2, 47)
adapted = base(features) + (8 / 4) * up(down(features))
assert torch.allclose(adapted, base(features))
adapted.square().mean().backward()
assert base.weight.grad is None and up.weight.grad is not None
assert 4 * (47 + 83) == 520 and 47 * 83 == 3901''',
    'A dense projection costs O(BIO) operations for batch B, input I and output O. The adapter adds O(BR(I + O)) work and R(I + O) trainable weights for rank R. The base still consumes IO stored weights and its forward compute; optimizer memory falls with trainable parameters, not total parameters. Whole-model savings require profiling target layers and sequence lengths.',
    ['Do not claim frozen base weights disappear from memory.', 'Do not omit target names, rank or scale from an adapter manifest.', 'Do not assume every task can match full fine-tuning with a tiny rank.'],
    ['deep-learning/lora-merge-parity-and-adapter-identity', 'deep-learning/service-event-lora-adaptation-project', 'deep-learning/frozen-features-versus-fine-tuning', 'deep-learning/training-memory-profiler-and-allocator-boundaries', 'deep-learning/adamw-decay-groups-and-update-indexed-schedules'], LORA)

add('lora-merge-parity-and-adapter-identity',
    'LoRA merge parity, base identity and adapter release',
    'A merged adapter must reproduce the unmerged evaluation path within tolerance; base drift and duplicate application are release defects.', [
    ('Merge with the declared scale', 'For base weight W, down matrix A, up matrix B and scale alpha divided by rank, the merged weight is W plus scale times B multiplied by A. In evaluation mode with dropout disabled, its linear output should match the separate adapter branch within numeric tolerance. The code compares both paths on fixed inputs. [[deep-learning/lora-rank-scaling-and-frozen-base-contract|The rank lesson]] explains the factor dimensions.'),
    ('Bind to the correct checkpoint', 'An adapter file is incomplete without the base model hash, target-layer names, tokenizer or feature schema and preprocessing revision. A new base with the same shapes can still invalidate the adapter. Save merge script revision as well. [[deep-learning/checkpoint-resume-state|Checkpoint identity]] matters for a release as much as for training recovery. Refuse a load when the manifest does not match.'),
    ('Do not apply twice', 'Adding an adapter delta to weights that were already merged doubles the update. Store an explicit merged or unmerged state and test the loader for repeat calls. Multiple task adapters need immutable base weights or isolated merged copies, not mutation of one shared process between requests. If requests can use different adapters concurrently, test that their outputs never cross.'),
    ('Check target numeric precision', 'Merging before quantization need not match merging into an already quantized weight. Rounding, scale and adapter dropout can shift scores. Evaluate in deterministic mode at the deployed dtype, report maximum logit difference and count any class-decision flips. [[deep-learning/post-training-quantization-calibration-contract|The calibration lesson]] supplies an additional quality check for low-bit serving.'),
    ('Gate a reversible release', 'Measure task quality, p95 latency and peak memory for unmerged and merged paths. A merged copy removes the extra adapter branch at inference but may require one full model copy per task. Keep the previous base plus adapter as a rollback pair. [[deep-learning/service-event-lora-adaptation-project|The applied project]] compares both release paths on held-out incidents.')],
    '''import torch
from torch import nn

torch.manual_seed(47)
base = nn.Linear(6, 4, bias=False)
down = nn.Linear(6, 2, bias=False)
up = nn.Linear(2, 4, bias=False)
features = torch.rand(3, 6)
scale = 5 / 2
unmerged = base(features) + scale * up(down(features))
combined_weight = base.weight + scale * (up.weight @ down.weight)
merged = nn.functional.linear(features, combined_weight)
assert combined_weight.shape == (4, 6)
assert torch.allclose(unmerged, merged, atol=1e-6, rtol=1e-5)
assert not torch.allclose(base.weight, combined_weight)''',
    'One I-by-O merge at rank R takes O(IOR) arithmetic and materializes O(IO) combined weights. Leaving the adapter separate adds O(BR(I + O)) work per batch B. Keeping several merged copies can multiply resident base memory by task count. Quantized merge arithmetic needs its own parity measurement; this example checks floating-point algebra only.',
    ['Do not merge an adapter twice.', 'Do not use a same-shaped but different base model.', 'Do not infer low-bit parity from a full-precision unit check.'],
    ['deep-learning/lora-rank-scaling-and-frozen-base-contract', 'deep-learning/service-event-lora-adaptation-project', 'deep-learning/post-training-quantization-calibration-contract', 'deep-learning/checkpoint-resume-state', 'deep-learning/inference-schema-and-latency'], LORA)

add('service-event-lora-adaptation-project',
    'Project: adapt a service-event classifier with low-rank weights',
    'Attach an adapter to a frozen event encoder, compare it with frozen and full-update baselines, then release with merge parity and base identity.', [
    ('Split whole incidents', 'Collect event text and structured fields with incident ID, source, event time and reviewed class. Hold out whole incidents and a later period; strip resolution notes and post-alert actions that reveal the answer. A small adapter can memorize leakage as easily as a full model. [[deep-learning/augmentation-leakage-boundary|The split lesson]] protects the comparison across model choices.'),
    ('Compare three candidates', 'Measure a frozen encoder with a trainable head, selected low-rank adapters, and fuller fine-tuning if resources allow. Use the same labels, tokenization, class weighting and held-out incidents. The snippet performs one synthetic update and confirms the base receives no weight gradient. It does not train a real event detector. [[deep-learning/lora-rank-scaling-and-frozen-base-contract|The adapter lesson]] gives parameter and memory arithmetic.'),
    ('Audit costly mistakes', 'Report severe-incident recall, macro F1, calibration and abstention by event family and source system. Compare class changes against the frozen baseline. A lower average loss can hide a drop on a rare incident class. Repeat across seeds, record trainable count and peak memory, and select the checkpoint with validation data rather than the final training step.'),
    ('Check merge and serving', 'Pair the selected adapter with its exact base fingerprint. Compare unmerged and merged logits on fixed held-out events, then count thresholded decision flips. Test the deployed precision and runtime rather than extrapolating from float parity. Measure tokenization plus model p95 latency and resident memory for the adapter-loading strategy. [[deep-learning/lora-merge-parity-and-adapter-identity|The merge lesson]] prevents duplicate deltas and base drift.'),
    ('Publish with fallback', 'Shadow-score incoming events and review disagreements before affecting any alert. Require no severe-recall drop, an acceptable review workload, matching base identity and declared merge tolerance. Retain the previous classifier if a source changes format or adapter load fails. Package base hash, target layers, rank, scale, tokenizer, threshold and rollback pointer as one release unit.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

torch.manual_seed(47)
base = nn.Linear(6, 8, bias=False)
base.weight.requires_grad_(False)
down, up = nn.Linear(6, 2, bias=False), nn.Linear(2, 8, bias=False)
nn.init.zeros_(up.weight)
head = nn.Linear(8, 3)
optimizer = torch.optim.AdamW(list(down.parameters()) +
                              list(up.parameters()) + list(head.parameters()), lr=.0007)
events = torch.rand(4, 6)
labels = torch.tensor([0, 2, 1, 2])
logits = head(torch.relu(base(events) + 2.5 * up(down(events))))
loss = functional.cross_entropy(logits, labels)
optimizer.zero_grad(set_to_none=True)
loss.backward()
optimizer.step()
assert torch.isfinite(loss) and base.weight.grad is None
assert up.weight.grad is not None''',
    'For an I-by-O frozen projection and rank R, the adapter adds R(I + O) trainable weights and O(BR(I + O)) work at batch B. The base still occupies IO weight storage and O(BIO) forward work, while larger encoders retain activation cost. The toy step checks gradient routing only; quality, merge parity and low-bit behavior require held-out incidents and target-runtime tests.',
    ['Do not split messages from one incident between training and final test.', 'Do not ship an adapter without exact base and tokenizer identity.', 'Do not let overall accuracy hide severe-incident recall loss.'],
    ['deep-learning/lora-rank-scaling-and-frozen-base-contract', 'deep-learning/lora-merge-parity-and-adapter-identity', 'deep-learning/frozen-features-versus-fine-tuning', 'deep-learning/temperature-scaling-and-selective-risk', 'deep-learning/inference-schema-and-latency'], LORA, True)

CROSSLINKS = [
    ('deep-learning/dqn-transition-replay-and-reward-contract', 'deep-learning/ppo-rollout-advantage-and-bootstrap-boundary'),
    ('deep-learning/dqn-target-network-and-action-mask', 'deep-learning/ppo-clipped-policy-ratio-and-kl-guard'),
    ('deep-learning/inventory-dispatch-dqn-project', 'deep-learning/warehouse-shift-ppo-project'),
    ('deep-learning/inference-schema-and-latency', 'deep-learning/warehouse-shift-ppo-project'),
    ('deep-learning/frozen-features-versus-fine-tuning', 'deep-learning/lora-rank-scaling-and-frozen-base-contract'),
    ('deep-learning/post-training-quantization-calibration-contract', 'deep-learning/lora-merge-parity-and-adapter-identity'),
    ('deep-learning/receipt-student-distillation-project', 'deep-learning/service-event-lora-adaptation-project'),
    ('deep-learning/inference-schema-and-latency', 'deep-learning/service-event-lora-adaptation-project'),
    ('deep-learning/deep-learning-tutorial', 'deep-learning/service-event-lora-adaptation-project'),
]

if __name__ == '__main__':
    publish(LESSONS, (PPO, LORA), CROSSLINKS,
            'aitrove-deep-learning-ppo-lora-import-20261006.json',
            7970, subject='deep-learning')
