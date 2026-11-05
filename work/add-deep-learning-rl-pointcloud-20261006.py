"""Add deep reinforcement learning and point-cloud learning paths."""
from de_batch_publisher import publish

RL = 'Deep reinforcement learning and decision replay'
POINTS = 'Point-cloud learning and 3D inspection'
LESSONS = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    assert len(sections) == 5
    LESSONS.append(dict(path='deep-learning/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add('dqn-transition-replay-and-reward-contract',
    'DQN transitions, replay sampling and reward contracts',
    'A value network cannot repair a faulty decision log: state timing, valid actions, terminal flags and reward accounting determine what replay teaches.', [
    ('Define one decision boundary', 'A warehouse replenishment agent might choose whether to move a spare carton before the next dispatch. Store the observation available immediately before that choice, the selected action, the reward earned over the following interval, the next observation and whether the episode ended. A later stock count cannot appear in the earlier state. Attach event time, policy version and action-eligibility rules to the transition, then test whether the same record can be reconstructed from the event ledger. [[deep-learning/causal-dilated-convolution-receptive-field|Causal feature construction]] prevents a learned shortcut from reading the future.'),
    ('Make reward units explicit', 'A positive reward for completed orders and a negative reward for late orders sounds simple until a single late order gets counted on every subsequent time step. Define when each outcome is booked and what a terminal penalty means. Keep physical units alongside the scalar reward so an engineer can audit one episode by hand. If the organization changes the cost of an expedited move, version the reward function and do not mix labels from two versions in one unexplained training run.'),
    ('Separate termination from truncation', 'A terminal state means there is no next decision in the modeled episode; a log cut because the shift ended may merely truncate observation. These cases can require different bootstrap treatment. The code models a terminal flag and refuses sampling before the replay buffer contains enough distinct transitions. Retain a stable episode ID to identify adjacent records. [[deep-learning/dqn-target-network-and-action-mask|The target lesson]] uses the flag to suppress bootstrap on true terminal transitions.'),
    ('Sample without hiding coverage', 'Uniform replay breaks the tight correlation of neighboring observations and reuses costly experience, but it does not invent actions the logger never tried. Record counts by warehouse, action, stock band and failure mode. A buffer dominated by quiet hours can underrepresent rare stockouts; stratified analysis is still needed even if mini-batches are random. Split evaluation by episode or time period before filling training replay, since shared adjacent transitions across train and test inflate performance.'),
    ('Keep exploration out of unsafe decisions', 'Epsilon-greedy exploration can choose a random action only from the permitted set. An action mask belongs to the state contract and must be applied both while collecting decisions and while estimating future values. In an operational setting, begin with simulation or a tightly bounded shadow policy and define a rollback to the existing dispatcher. [[deep-learning/inventory-dispatch-dqn-project|The project]] checks action legality, order completion and stockout cost together.')],
    '''from collections import deque
from dataclasses import dataclass
from random import Random

@dataclass(frozen=True)
class DispatchTransition:
    stock_before: tuple[int, int]
    action: int
    reward: float
    stock_after: tuple[int, int]
    terminal: bool
    episode_id: str

replay = deque(maxlen=47)
replay.extend([
    DispatchTransition((8, 3), 1, 2.0, (7, 4), False, "shift-47"),
    DispatchTransition((7, 4), 0, -1.0, (6, 4), True, "shift-47"),
    DispatchTransition((5, 2), 1, 3.0, (4, 3), True, "shift-48"),
])
randomizer = Random(47)
batch = randomizer.sample(list(replay), k=2)
assert len(batch) == 2 and len(set(batch)) == 2
assert all(record.episode_id and record.action in (0, 1) for record in batch)''',
    'Appending to a bounded deque is O(1) amortized time and O(C) memory for capacity C. Converting the entire deque to a list for each sample is O(C); a large production replay store needs indexed sampling or batched storage. One sampled mini-batch is O(B) after indexing for batch size B. Environment interaction may dominate training cost, while uniform random replay still leaves distribution mismatch between historical behavior and a proposed policy.',
    ['Do not place a post-decision count in the pre-decision state.', 'Do not treat a log cutoff as a true terminal event without a declared rule.', 'Do not claim replay covers actions that the logging policy never selected.'],
    ['deep-learning/dqn-target-network-and-action-mask', 'deep-learning/inventory-dispatch-dqn-project', 'deep-learning/train-eval-validation-loop', 'deep-learning/causal-dilated-convolution-receptive-field', 'deep-learning/adamw-decay-groups-and-update-indexed-schedules'], RL)

add('dqn-target-network-and-action-mask',
    'DQN target networks, legal-action masks and value updates',
    'Freeze a separate target estimator long enough to form stable bootstrap values, and exclude impossible actions before both selection and target calculation.', [
    ('Identify the two estimators', 'An online network estimates action values and receives gradient updates. A target network is a delayed copy used to form the next-state estimate. Without that delay, the value being fitted moves with every parameter update and can magnify errors. Copy all weights at a declared interval or use a declared soft-update coefficient. Save both model states and the target-update counter in a resumable checkpoint. [[deep-learning/checkpoint-resume-state|Checkpoint identity]] matters when training continues after interruption.'),
    ('Apply masks before taking a maximum', 'If an empty shelf cannot supply an item, its dispatch action must not compete for the maximum future value. Represent legal actions as a Boolean mask for each state and assert that each nonterminal state has at least one legal action. Masked values may use a sufficiently low finite sentinel, but choose it with the numeric dtype in mind. The code uses an explicit Boolean mask and a two-action synthetic batch. The same eligibility logic must operate during data collection and serving.'),
    ('Compute a detached bootstrap target', 'For reward r and discount gamma, the target is r plus gamma times the best permitted next value unless the transition is terminal. The target path must not backpropagate through the target network. Double DQN chooses the next action with the online model and evaluates that action with the target model; this can reduce overestimation from taking a maximum over noisy estimates, but does not correct an invalid reward or observation. The snippet demonstrates the double-estimator choice.'),
    ('Audit learning against a baseline', 'Report reward by whole episode, stockouts, late orders and action frequency on held-out simulated periods. Compare with the current dispatch rule under identical demand sequences. A low temporal-difference loss is not proof of an improved operating policy. Freeze the environment and random seeds for comparison, then vary demand and lead-time assumptions to see where the candidate fails. [[deep-learning/inventory-dispatch-dqn-project|The applied project]] includes this counterfactual replay.'),
    ('Bound operational exposure', 'A network may assign a high value to a rare action because the replay log barely contains it. Track state-action support and require a fallback or human review outside that support. Shadow scoring exposes policy disagreements without executing them. If online rollout is allowed, cap the affected inventory, add a hard legal-action filter and retain a rapid disable switch. An offline score alone cannot establish safety under a changed policy.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

torch.manual_seed(47)
online_values = nn.Linear(2, 2)
target_values = nn.Linear(2, 2)
target_values.load_state_dict(online_values.state_dict())
stock_before = torch.tensor([[8., 3.], [5., 0.]])
stock_after = torch.tensor([[7., 4.], [4., 0.]])
chosen_actions = torch.tensor([[1], [0]])
rewards = torch.tensor([2., -3.])
terminals = torch.tensor([False, True])
legal_next = torch.tensor([[True, True], [True, False]])
predicted = online_values(stock_before).gather(1, chosen_actions).squeeze(1)
with torch.no_grad():
    next_action = online_values(stock_after).masked_fill(~legal_next, -1e9).argmax(1, keepdim=True)
    bootstrap = target_values(stock_after).gather(1, next_action).squeeze(1)
    expected = rewards + 0.93 * (~terminals).float() * bootstrap
loss = functional.smooth_l1_loss(predicted, expected)
loss.backward()
assert torch.isfinite(loss) and target_values.weight.grad is None''',
    'For B transitions, A actions and a value network requiring F operations per state, two network passes cost roughly O(BF + BA) and carry online activations proportional to the model width and B. A fixed target copy doubles parameter storage but avoids target-path gradient storage. Action masking adds O(BA) work. In a real simulator, generating sufficiently varied transitions may be far more expensive than this small update; measure episode throughput as well as accelerator time.',
    ['Do not maximize over actions that are impossible at the next state.', 'Do not allow target-network gradients into the optimizer step.', 'Do not use training loss as a substitute for held-out episode outcomes.'],
    ['deep-learning/dqn-transition-replay-and-reward-contract', 'deep-learning/inventory-dispatch-dqn-project', 'deep-learning/checkpoint-resume-state', 'deep-learning/adamw-decay-groups-and-update-indexed-schedules', 'deep-learning/temperature-scaling-and-selective-risk'], RL)

add('inventory-dispatch-dqn-project',
    'Project: audit a neural inventory dispatch policy before release',
    'Train a masked value model in a reproducible simulator, then reject any policy that improves reward while violating stock or service gates.', [
    ('Specify the decision process', 'Use a small warehouse with two stock locations and one spare transfer choice at each order event. The state includes only known stock, inbound arrivals already confirmed, backlog and time within a shift. An action either transfers one spare unit or waits; transfers are illegal when the source has no usable stock. Record demand seed, lead-time assumptions, reward version and episode termination. [[deep-learning/dqn-transition-replay-and-reward-contract|The transition contract]] gives each event an auditable before-and-after record.'),
    ('Build baselines before fitting', 'Run the existing reorder rule and a fixed safe action under the same demand draws. Count completed orders, late orders, stockouts and expedited moves in natural units before compressing them into a reward. A candidate that raises a weighted reward by causing more stockouts has failed even if the score looks better. Keep a development set for reward and model selection and a final set of unseen demand periods.'),
    ('Wire the model without pretending it is trained', 'The code performs one masked value update on a tiny synthetic batch. It verifies finite loss, legal next-action selection and a detached target branch. It is a wiring check, not a trained dispatch policy; the full project requires generating many independent episodes and evaluating checkpoints on held-out seeds. [[deep-learning/dqn-target-network-and-action-mask|The value lesson]] explains the two estimators and why masks belong to both paths.'),
    ('Compare under distribution changes', 'Test slower supplier lead times, bursts of demand and inventory-record delays. Report mean and lower-tail episode return, stockout count, late-order count and illegal-action attempts; group uncertainty by independent episode. Inspect actions near the limits of the replay distribution. A model trained only on quiet periods can overvalue transfer actions in a shortage, so no broad release follows from one simulator setting.'),
    ('Gate and observe the release', 'Require no legal-action violations, no increase in stockouts against the baseline, an acceptable late-order rate and bounded inference latency. Start with shadow decisions and log disagreements against the current dispatch rule. Permit a narrow rollout only after operational review, with a reversible switch back to the baseline and a fixed data-collection window. Publish the environment assumptions, replay support table, seeds and failure episodes with the model artifact.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

torch.manual_seed(47)
dispatch_values = nn.Sequential(nn.Linear(3, 16), nn.ReLU(), nn.Linear(16, 2))
target_values = nn.Sequential(nn.Linear(3, 16), nn.ReLU(), nn.Linear(16, 2))
target_values.load_state_dict(dispatch_values.state_dict())
observations = torch.tensor([[8., 3., 1.], [5., 0., 2.]])
next_observations = torch.tensor([[7., 4., 1.], [4., 0., 2.]])
selected_actions = torch.tensor([[1], [0]])
rewards = torch.tensor([2., -3.])
terminal = torch.tensor([False, True])
legal_next = torch.tensor([[True, True], [True, False]])
optimizer = torch.optim.AdamW(dispatch_values.parameters(), lr=0.0007)
with torch.no_grad():
    next_choice = dispatch_values(next_observations).masked_fill(~legal_next, -1e9).argmax(1, keepdim=True)
    future_value = target_values(next_observations).gather(1, next_choice).squeeze(1)
    target = rewards + 0.93 * (~terminal).float() * future_value
prediction = dispatch_values(observations).gather(1, selected_actions).squeeze(1)
loss = functional.smooth_l1_loss(prediction, target)
optimizer.zero_grad(set_to_none=True)
loss.backward()
optimizer.step()
assert torch.isfinite(loss) and target_values[0].weight.grad is None''',
    'Each update processes B transitions and A action scores; the dominant arithmetic is the neural network forward and backward passes, approximately proportional to B times its parameter operations. Replay requires O(CD) storage for C transitions of dimension D, plus metadata such as episode and policy IDs. Simulator cost scales with episodes and steps per episode. The toy batch demonstrates the update path only; rollout gates require independent episode measurements and an operational fallback.',
    ['Do not let a weighted reward conceal worsening stockouts.', 'Do not release from a simulator calibrated on one quiet period.', 'Do not execute an out-of-support action without a hard eligibility check.'],
    ['deep-learning/dqn-transition-replay-and-reward-contract', 'deep-learning/dqn-target-network-and-action-mask', 'deep-learning/train-eval-validation-loop', 'deep-learning/checkpoint-resume-state', 'deep-learning/inference-schema-and-latency'], RL, True)

add('point-cloud-coordinate-frame-and-sampling-contract',
    'Point-cloud coordinate frames, sampling and scan identity',
    'A 3D model sees unordered coordinates; unit, sensor pose, point density and scan-level split rules determine whether those coordinates mean the same thing later.', [
    ('Keep geometry in declared units', 'A warehouse depth sensor may export meters while an annotation tool displays millimeters. The same numeric triple then describes a very different object. Record units, handedness, axis directions, sensor-to-world transform, capture time and sensor calibration revision with each scan. Transform points into a declared frame before computing features. The code centers four points after validating their dimensions; centering alone does not correct a wrong physical scale.'),
    ('Preserve scan identity across crops', 'A large pallet scan is often cut into several training crops. Neighboring crops share the pallet, warehouse lighting and scanner artifacts. Split by physical pallet or acquisition session before crop generation, then report the number of independent pallets in every evaluation set. Do not place one face of a pallet in training and another face in final test. [[deep-learning/augmentation-leakage-boundary|The parent split rule]] applies to 3D scans as strongly as it does to images.'),
    ('Choose a point budget openly', 'Sampling a fixed number of points controls memory and batch shape. Uniform random sampling is cheap but can miss a small broken corner; grid or farthest-point methods change coverage and cost. Keep the raw scan and the sampling seed so reviewers can inspect whether the defect existed in the selected subset. Record point count before and after filtering, and reject a scan with too few usable returns rather than padding it silently into apparent certainty.'),
    ('Separate pose changes from defects', 'Centering removes translation, but rotation and scale require explicit handling. Random rotation augmentation is valid only if the label is invariant under those rotations; a tipped pallet may be a defect, so arbitrary rotation can erase the signal. Estimate sensor pose when available and compare a model trained in physical coordinates against one using centered local coordinates. [[deep-learning/point-set-permutation-invariance-and-pooling|The set model]] handles ordering, not every geometric transform automatically.'),
    ('Replay the deployed path', 'Compare training and serving transformations on a fixed raw scan: unit conversion, coordinate frame, crop bounds, point sampling, outlier filtering and normalization. Audit missing depth returns and reflective wrap separately. Measure p95 scan decode, sampling and model inference time at the target point budget. [[deep-learning/pallet-point-cloud-inspection-project|The inspection project]] reports defect recall by point density and scanner site.')],
    '''from math import isfinite

scan_points_m = [(1.2, 2.4, 0.7), (1.4, 2.5, 0.7),
                 (1.2, 2.6, 0.9), (1.4, 2.3, 0.9)]

def center_scan(points_m):
    if not points_m or any(len(point) != 3 or not all(map(isfinite, point)) for point in points_m):
        raise ValueError("scan needs finite x, y and z coordinates")
    center = tuple(sum(point[axis] for point in points_m) / len(points_m)
                   for axis in range(3))
    return [tuple(point[axis] - center[axis] for axis in range(3))
            for point in points_m], center

centered_points, scan_center = center_scan(scan_points_m)
assert len(centered_points) == 4
assert all(abs(sum(point[axis] for point in centered_points)) < 1e-9
           for axis in range(3))
assert all(abs(actual - expected) < 1e-9
           for actual, expected in zip(scan_center, (1.3, 2.45, 0.8)))''',
    'Centering N points takes O(N) time and O(N) output storage; the raw scan may be much larger than a sampled model input. A dense voxel grid with K cells along each axis uses O(K cubed) space even when most cells are empty, while point-set storage is O(N). More points improve the chance of retaining a small flaw but raise feature and neighbor-search costs. The snippet verifies a coordinate operation, not a calibrated sensor transform.',
    ['Do not mix millimeters and meters in one model input.', 'Do not split crops from one physical scan across train and final test.', 'Do not assume centering makes the model rotation invariant.'],
    ['deep-learning/point-set-permutation-invariance-and-pooling', 'deep-learning/pallet-point-cloud-inspection-project', 'deep-learning/augmentation-leakage-boundary', 'deep-learning/convolution-output-geometry-and-receptive-field', 'computer-vision/annotation-geometry-and-quality'], POINTS)

add('point-set-permutation-invariance-and-pooling',
    'Point-set permutation invariance and pooled features',
    'A shared point encoder followed by symmetric pooling gives a scan-level representation that does not change when input points are reordered.', [
    ('Treat order as meaningless', 'A scanner may return the same surface points in a different order because of packet timing or crop serialization. A scan-level classifier should not change its prediction under that permutation. Apply the same feature network to every point, then aggregate with a symmetric operation such as maximum or mean. The code verifies the pooled vector is unchanged after an explicit permutation. The choice of pooling still changes sensitivity to rare defects and noise.'),
    ('Know what max pooling sees', 'Elementwise maximum keeps the strongest activation for each feature channel. One strongly activated point can represent a small damaged edge, but a spurious reflection can also dominate. Mean pooling uses information from many points and may dilute a tiny fault. Compare both on defect size and missing-return slices. A simple global representation does not preserve detailed neighborhood geometry; if local shape matters, add measured local grouping only after checking a set baseline.'),
    ('Keep per-point and global tasks separate', 'Pallet classification yields one label per scan. Segmenting damaged surface points requires outputs tied to the individual input points. In that case combine each point feature with a broadcast global feature before prediction, and restore predictions to the raw scan IDs after sampling. Sorting or shuffling input points should permute per-point outputs in the same way rather than leave them fixed. [[deep-learning/segmentation-mask-alignment-and-ignore-pixels|Segmentation alignment]] has a parallel issue in images.'),
    ('Test missing density and transforms', 'Permutation invariance alone does not guarantee resilience to point deletion, changed sensor density, translation, rotation or scale. Evaluate deliberate resampling and coordinate perturbations within the sensor tolerance, then inspect whether the model uses the pallet rather than its scan rig. Group held-out scans by site and calibration period. [[deep-learning/point-cloud-coordinate-frame-and-sampling-contract|The coordinate contract]] fixes what each number means before any invariant architecture is useful.'),
    ('Measure the inference budget', 'A shared encoder processes every retained point; doubling the point budget roughly doubles pointwise work and activation storage for a fixed width. Pooling itself is cheap. Track p95 latency for raw scan decode, outlier rejection, sampling and network inference. A tiny network forward can be operationally slow when preprocessing copies millions of coordinates. [[deep-learning/pallet-point-cloud-inspection-project|The project]] gates the complete inspection decision.')],
    '''import torch
from torch import nn

torch.manual_seed(47)
pallet_points = torch.tensor([[[0.1, 0.2, 0.0], [0.3, 0.1, 0.1],
                               [0.2, 0.4, 0.2], [0.4, 0.3, 0.0]]])
point_encoder = nn.Sequential(nn.Linear(3, 16), nn.ReLU(),
                              nn.Linear(16, 8))
point_features = point_encoder(pallet_points)
scan_features = point_features.amax(dim=1)
reordered_features = point_encoder(pallet_points[:, [2, 0, 3, 1], :]).amax(dim=1)
assert scan_features.shape == (1, 8)
assert torch.allclose(scan_features, reordered_features)
inspection_head = nn.Linear(8, 2)
inspection_logits = inspection_head(scan_features)
assert inspection_logits.shape == (1, 2)''',
    'For B scans, N points and a point encoder with F operations per point, pointwise work is O(BNF) and activations scale with O(BNW) for hidden width W. Symmetric pooling adds O(BNW) comparisons or additions and a small O(BW) output. Local-neighbor architectures can incur extra search and grouping costs; a global set encoder avoids those costs but may miss fine spatial structure. This synthetic shape and reorder check proves permutation behavior only, not inspection accuracy.',
    ['Do not mistake order invariance for rotation or scale invariance.', 'Do not use one global class logit as if it located damaged points.', 'Do not hide reflective outliers behind a mean accuracy score.'],
    ['deep-learning/point-cloud-coordinate-frame-and-sampling-contract', 'deep-learning/pallet-point-cloud-inspection-project', 'deep-learning/segmentation-mask-alignment-and-ignore-pixels', 'deep-learning/augmentation-leakage-boundary', 'deep-learning/inference-schema-and-latency'], POINTS)

add('pallet-point-cloud-inspection-project',
    'Project: inspect pallet damage from 3D point scans',
    'Build a scan-level defect detector with a declared coordinate frame, scan-group evaluation and a review path for missing or low-density depth.', [
    ('Build the scan ledger', 'Collect raw depth scans with pallet ID, scanner site, acquisition session, units, sensor pose and calibration revision. Record reviewed defect types, location and severity, plus whether depth returns are missing near the suspected defect. Split by pallet before creating training crops or resampled point sets. Keep a reserved scanner and time period for the final transfer check. [[deep-learning/point-cloud-coordinate-frame-and-sampling-contract|The geometry lesson]] defines the transformations to version.'),
    ('Set a transparent baseline', 'Compare a simple geometric threshold on height or missing volume with a point-set classifier. A neural score is only useful if it finds defects the baseline misses without overwhelming inspectors with false flags. Record defect prevalence, manual review capacity and the cost of a missed structural flaw. Include clean pallets with reflective wrap, partial occlusion and irregular loading so the detector sees operational negatives rather than only tidy scans.'),
    ('Verify the model path', 'The code executes one synthetic class update for a shared point encoder with max pooling. It checks tensor axes and finite loss; it does not train on pallet scans or prove that max pooling captures a small break. Compare a mean-pooling ablation and a physical-geometry baseline under the same pallet-level holdout. [[deep-learning/point-set-permutation-invariance-and-pooling|The set lesson]] separates order invariance from physical invariance.'),
    ('Score operational slices', 'Report pallet-level recall for severe defects, false flags per inspected pallet, abstention rate for poor scans and review time. Slice by point density, defect size, scanner site, pallet material and reflective packaging. Examine missed defects in raw coordinate space; if the sampled cloud discarded the flaw, changing classifier depth alone cannot fix the problem. Freeze the score threshold before the final scanner-site evaluation.'),
    ('Release with a review route', 'Package unit conversion, calibration version, crop and sampling rules, model weights, threshold and minimum usable point count. Route sparse or malformed scans to rescan or manual review; do not label them clean. Measure p95 scan-to-decision time including decode and sampling. Keep the threshold baseline available as a rollback while collecting reviewed failures and per-site drift evidence.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

torch.manual_seed(47)
pallet_scans = torch.rand(4, 32, 3)
reviewed_damage = torch.tensor([0, 1, 0, 1])
point_encoder = nn.Sequential(nn.Linear(3, 16), nn.ReLU(), nn.Linear(16, 8), nn.ReLU())
inspection_head = nn.Linear(8, 2)
optimizer = torch.optim.AdamW(list(point_encoder.parameters()) +
                              list(inspection_head.parameters()), lr=0.0007)
encoded_points = point_encoder(pallet_scans)
scan_features = encoded_points.amax(dim=1)
damage_logits = inspection_head(scan_features)
assert damage_logits.shape == (4, 2)
loss = functional.cross_entropy(damage_logits, reviewed_damage)
optimizer.zero_grad(set_to_none=True)
loss.backward()
optimizer.step()
assert torch.isfinite(loss)''',
    'For B scans and N retained points, point encoding and activation memory grow approximately linearly with BN at fixed layer widths. Raw scanner data, crop construction and repeated sampling can dominate end-to-end cost. Increasing N may preserve smaller defects but reduces throughput; select it from measured recall-versus-latency curves. The example is a single synthetic optimizer step, not a validated detector, and its random points have no physical meaning.',
    ['Do not claim scan-level random-crop accuracy as pallet-level generalization.', 'Do not classify a scan with too few valid returns as clean.', 'Do not ship a class score without a reviewed threshold and a rescan route.'],
    ['deep-learning/point-cloud-coordinate-frame-and-sampling-contract', 'deep-learning/point-set-permutation-invariance-and-pooling', 'deep-learning/augmentation-leakage-boundary', 'deep-learning/inference-schema-and-latency', 'deep-learning/receipt-confidence-audit-project'], POINTS, True)

CROSSLINKS = [
    ('deep-learning/causal-dilated-convolution-receptive-field', 'deep-learning/dqn-transition-replay-and-reward-contract'),
    ('deep-learning/train-eval-validation-loop', 'deep-learning/dqn-target-network-and-action-mask'),
    ('deep-learning/checkpoint-resume-state', 'deep-learning/inventory-dispatch-dqn-project'),
    ('deep-learning/inference-schema-and-latency', 'deep-learning/inventory-dispatch-dqn-project'),
    ('deep-learning/augmentation-leakage-boundary', 'deep-learning/point-cloud-coordinate-frame-and-sampling-contract'),
    ('deep-learning/segmentation-mask-alignment-and-ignore-pixels', 'deep-learning/point-set-permutation-invariance-and-pooling'),
    ('deep-learning/inference-schema-and-latency', 'deep-learning/pallet-point-cloud-inspection-project'),
    ('deep-learning/receipt-confidence-audit-project', 'deep-learning/pallet-point-cloud-inspection-project'),
    ('deep-learning/deep-learning-tutorial', 'deep-learning/pallet-point-cloud-inspection-project'),
]

if __name__ == '__main__':
    publish(LESSONS, (RL, POINTS), CROSSLINKS,
            'aitrove-deep-learning-rl-pointcloud-import-20261006.json',
            7950, subject='deep-learning')
