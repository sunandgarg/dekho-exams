"""Add recurrent-sequence and reconstruction-model editorial pathways."""
from de_batch_publisher import publish

RECURRENCE = 'Recurrent sequences and state ownership'
RECONSTRUCTION = 'Reconstruction models and anomaly scores'
LESSONS = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    assert len(sections) == 5
    LESSONS.append(dict(path='deep-learning/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add('packed-lstm-lengths-and-last-valid-state',
    'Packed LSTM sequences and the last valid state',
    'Packing makes an LSTM stop at each record’s real length; the final state must represent the last event, not an allocated padding slot.', [
    ('Make length a first-class input', 'A batch of event histories has shape batch by allocated steps by features, but each history also needs a measured count of real steps. Padding is storage, not an event. Reject zero-length histories or handle them with a separate fallback; a packed recurrent call expects a positive length. Verify that every length is at most the allocated width and corresponds to the feature rows produced by the same tokenizer or event encoder. [[deep-learning/tensor-shape-dtype-contract|The tensor contract]] should include both the data shape and the length vector.'),
    ('Pack before recurrence', 'A packed sequence lets the recurrent cell skip padding timesteps. When inputs are not sorted by length, request internal sorting and let the API restore output order. If lengths are provided as a tensor, put them on CPU for the packing call. The final hidden state from a one-layer, forward-only LSTM then belongs to the last real step of each original sequence. Reading output at the last allocated index instead would mix in padding behavior or return a zero after unpacking. [[deep-learning/causal-target-shift-and-padding-loss|Padding-aware loss]] is a separate requirement when every step receives a target.'),
    ('Keep directions and layers explicit', 'For a one-layer, forward-only LSTM, the last hidden slice and an output gathered at length minus one agree within floating-point tolerance. That shortcut changes for a bidirectional model: its backward final state summarizes a reverse traversal, and output at the last forward position does not contain the backward final summary. A stacked model adds another layer axis. Name the chosen direction and layer before selecting a state; do not treat the first dimension of the hidden tensor as the batch dimension.'),
    ('Separate batch padding from online state', 'Packing is useful when independent histories are processed together. A live stream may instead carry hidden and cell state from one request to its next event. That state must be keyed by stream identity and reset when a stream ends, changes owner or times out. A packed batch does not solve state ownership across requests. [[deep-learning/recurrent-hidden-state-reset-and-truncated-gradients|State reset rules]] cover that boundary and the gradient history retained during training.'),
    ('Probe a padding counterfactual', 'Create two batches with identical valid prefixes but different values in every padded slot. Their final states and predictions should match when lengths are correct. Change one length deliberately and confirm the test fails. Check a one-event history, an unsorted batch and a last batch smaller than the usual batch size. Keep the probe in model tests because a preprocessing change can silently replace the length vector while leaving tensors numerically well formed.')],
    '''import torch
from torch import nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

torch.manual_seed(47)
service_histories = torch.tensor([
    [[0.2, 0.4, 0.1], [0.5, 0.2, 0.3], [0.1, 0.7, 0.2], [0.3, 0.2, 0.8]],
    [[0.9, 0.1, 0.2], [0.4, 0.6, 0.1], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
    [[0.3, 0.5, 0.2], [0.2, 0.1, 0.8], [0.6, 0.3, 0.4], [0.0, 0.0, 0.0]]])
history_lengths = torch.tensor([4, 2, 3], dtype=torch.long)
assert bool(((history_lengths > 0) & (history_lengths <= 4)).all())

event_lstm = nn.LSTM(input_size=3, hidden_size=7, batch_first=True)
packed_histories = pack_padded_sequence(service_histories, history_lengths.cpu(),
                                        batch_first=True, enforce_sorted=False)
packed_outputs, (last_hidden, last_cell) = event_lstm(packed_histories)
event_outputs, restored_lengths = pad_packed_sequence(
    packed_outputs, batch_first=True, total_length=4)
last_valid = event_outputs[torch.arange(3), history_lengths - 1]
torch.testing.assert_close(last_valid, last_hidden[-1])
assert torch.equal(restored_lengths, history_lengths)
assert last_cell.shape == (1, 3, 7)''',
    'For sequence length T and hidden width H, a recurrent layer performs work across T dependent steps; four LSTM gates increase per-step matrix work relative to a plain recurrent cell. Packing avoids cell work on padded positions, although sorting and packing add overhead and may limit some kernel choices. Activations stored for backward scale with valid steps and hidden width. Measure valid events per second, not allocated slots per second.',
    ['Do not use the final allocated padding slot as the last event.', 'Do not treat a bidirectional final state as though it were a one-direction output at length minus one.', 'Do not accept zero or incorrect lengths just because the padded tensor has the right shape.'],
    ['deep-learning/tensor-shape-dtype-contract', 'deep-learning/causal-target-shift-and-padding-loss', 'deep-learning/recurrent-hidden-state-reset-and-truncated-gradients', 'deep-learning/train-eval-validation-loop', 'deep-learning/service-event-lstm-project'], RECURRENCE)

add('recurrent-hidden-state-reset-and-truncated-gradients',
    'Recurrent hidden-state resets and truncated gradients',
    'A recurrent state belongs to one ordered stream; detaching it limits gradient history, while resetting it prevents another stream from inheriting private context.', [
    ('Define state ownership', 'An LSTM carries hidden and cell tensors with layer, batch and width axes. Batch column zero at the next chunk must still represent the same stream as column zero in the previous chunk, or the state must be reset. Shuffling chunks without their stream identifiers creates cross-customer contamination even when the loss calculation succeeds. At serving time, key state by an opaque conversation or device identifier, put a time-to-live on it, and clear it at an end event or identity change. A state cache is part of the prediction contract, not an internal convenience.'),
    ('Detach at the training boundary', 'If chunks from one long history are processed in order, the computational graph can span all previous chunks unless hidden and cell states are detached after a chosen truncation boundary. Detaching keeps their numeric contents for the next chunk while stopping gradients from flowing backward across that boundary. Resetting to zero discards the contents too. These operations solve different problems. [[deep-learning/gradient-accumulation-and-effective-batch|Gradient accumulation]] can still combine losses from multiple chunks before an optimizer step, but retained graphs and update timing must be accounted for.'),
    ('Apply per-stream reset masks', 'A batch can contain one continuing device and one new device. Reset only the changed column, not the whole batch, by multiplying detached state by a zero-or-one keep mask broadcast over layers and features. Verify the mask comes from stable stream identity, not from a label or sequence length that merely happens to match. If a stream is removed and the batch is compacted, reorder state columns with the same mapping or allocate a fresh state. A checksum of stream IDs next to state helps expose accidental reuse.'),
    ('Name the temporal limit', 'Truncating every 23 events means a loss cannot send gradient through earlier chunks, although the numeric state can carry old information forward. That is a modeling trade: shorter spans reduce memory and make updates more frequent, but may weaken learning of long dependencies. Compare several spans against a fixed validation set grouped by stream and report event count, optimizer updates and peak memory. [[deep-learning/packed-lstm-lengths-and-last-valid-state|Packing]] handles within-batch padding; it does not decide how far the backward graph reaches.'),
    ('Test a handoff failure', 'Feed stream A for one chunk, replace its identifier with stream B and assert B receives a zero initial state. Feed a second chunk of A and assert the state is retained but detached. Hold model weights fixed in evaluation mode when testing state ownership; otherwise dropout or training updates can make the comparison noisy. Also test worker restart: either restore state from a versioned checkpoint or explicitly start a new session, with a documented effect on predictions.')],
    '''import torch
from torch import nn

torch.manual_seed(83)
event_lstm = nn.LSTM(input_size=4, hidden_size=6, batch_first=True)
event_head = nn.Linear(6, 2)
optimizer = torch.optim.AdamW(list(event_lstm.parameters())
                              + list(event_head.parameters()), lr=0.00047)
first_chunk = torch.randn(2, 3, 4)
first_labels = torch.tensor([0, 1])

optimizer.zero_grad(set_to_none=True)
first_outputs, carried_state = event_lstm(first_chunk)
first_loss = nn.functional.cross_entropy(event_head(first_outputs[:, -1]),
                                         first_labels)
first_loss.backward()
optimizer.step()

same_stream_next = torch.tensor([True, False]).view(1, 2, 1)
next_state = tuple(state.detach() * same_stream_next for state in carried_state)
assert all(not state.requires_grad for state in next_state)
assert torch.count_nonzero(next_state[0][:, 1]) == 0
second_chunk = torch.randn(2, 3, 4)
second_outputs, second_state = event_lstm(second_chunk, next_state)
assert second_outputs.shape == (2, 3, 6)
assert second_state[0].shape == (1, 2, 6)''',
    'Without truncation, retained activations and graph history grow with the number of processed steps until backward releases them. Detaching bounds that history to the chosen chunk span, while state tensors themselves occupy O(layers × batch × hidden width). LSTM work remains sequential across timesteps. An online state cache adds memory proportional to concurrent streams, so expiration and eviction belong in capacity planning.',
    ['Do not carry a hidden state into a different stream after batch reshuffling.', 'Do not confuse detach, which cuts gradients, with reset, which clears information.', 'Do not claim long-horizon training when the backward span ends at every short chunk.'],
    ['deep-learning/packed-lstm-lengths-and-last-valid-state', 'deep-learning/gradient-accumulation-and-effective-batch', 'deep-learning/checkpoint-resume-state', 'deep-learning/inference-schema-and-latency', 'deep-learning/service-event-lstm-project'], RECURRENCE)

add('service-event-lstm-project',
    'Project: predict service escalation from event histories',
    'Build an escalation classifier for variable-length histories, then prove that padding, customer mixing and carried state cannot create false evidence.', [
    ('Freeze the event contract', 'Represent each service event by a timestamp, event type and known-at-event features. Exclude notes or outcomes recorded after the prediction time. Split 470 histories by customer and ticket before windowing; two windows from the same ticket cannot cross train and validation. Keep a label map for routine versus escalated and a count of valid events for each history. [[deep-learning/causal-target-shift-and-padding-loss|Temporal target alignment]] prevents a model from reading the answer it is supposed to predict.'),
    ('Start with packed independent histories', 'Pad a batch only for storage and pack it with measured lengths before an LSTM. Score the last real hidden state with a two-class head. Compare against a simple non-recurrent baseline using the same split and threshold-selection rule. Evaluate by history length and customer cohort so an apparent gain on long tickets cannot hide failures on one-event tickets. [[deep-learning/packed-lstm-lengths-and-last-valid-state|The packing contract]] makes the last event unambiguous.'),
    ('Add a stateful serving variant carefully', 'If events arrive one at a time, a state cache can avoid replaying the full history. Key it by ticket identity, version it with the model and set an expiry. Replay and cached-state predictions should agree under deterministic evaluation for a controlled ticket. On handoff to a different ticket, reset both hidden and cell state. A negative test that reuses the previous customer state should fail an isolation assertion. [[deep-learning/recurrent-hidden-state-reset-and-truncated-gradients|State ownership]] is a release gate.'),
    ('Probe leakage and padding', 'Make a copy of a validation batch and replace only padded rows with extreme values; predictions should remain the same. Swap lengths between two records and confirm the test notices. Then move a post-escalation event into the input to demonstrate how a leaky pipeline can score implausibly well. Report the difference without publishing that leaky model. Keep the counterfactual tests with the data pipeline because a correct network cannot repair a future-looking input.'),
    ('Release with measured limits', 'Report customer-grouped precision and recall, false alarms per hundred tickets, latency by history length, peak state-cache occupancy and restart behavior. Save feature encoding, label map, maximum history length, model weights and threshold together. If a ticket exceeds the limit, define whether to replay its latest window or to reject the request. The project is complete when a fresh process can reload the artifact and reproduce the same two fixed-ticket logits.')],
    '''import torch
from torch import nn
from torch.nn.utils.rnn import pack_padded_sequence

class EscalationHistoryModel(nn.Module):
    def __init__(self, event_width: int = 4, hidden_width: int = 9):
        super().__init__()
        self.encoder = nn.LSTM(event_width, hidden_width, batch_first=True)
        self.classifier = nn.Linear(hidden_width, 2)

    def forward(self, event_features: torch.Tensor,
                valid_lengths: torch.Tensor) -> torch.Tensor:
        if bool((valid_lengths < 1).any()) or bool((valid_lengths > event_features.size(1)).any()):
            raise ValueError("invalid event count")
        packed = pack_padded_sequence(event_features, valid_lengths.cpu(),
                                      batch_first=True, enforce_sorted=False)
        _, (last_hidden, _) = self.encoder(packed)
        return self.classifier(last_hidden[-1])

torch.manual_seed(59)
escalation_model = EscalationHistoryModel().eval()
event_features = torch.randn(3, 5, 4)
valid_lengths = torch.tensor([5, 2, 4])
changed_padding = event_features.clone()
changed_padding[1, 2:] = 1000
changed_padding[2, 4:] = -1000
with torch.inference_mode():
    baseline_logits = escalation_model(event_features, valid_lengths)
    changed_logits = escalation_model(changed_padding, valid_lengths)
torch.testing.assert_close(baseline_logits, changed_logits)
assert baseline_logits.shape == (3, 2)''',
    'The LSTM cost grows with valid event count and hidden width, while packing saves work on padding. Its timesteps remain dependent, so a long ticket can dominate latency even in a mixed batch. A stateful service exchanges replay cost for O(active tickets × layers × hidden width) cache memory and stricter identity handling. Measure tail latency and cache eviction, not just average batch throughput.',
    ['Do not split windows from one ticket across train and validation.', 'Do not let post-escalation events into the input history.', 'Do not reuse cached state for a new ticket or silently ignore the supplied valid lengths.'],
    ['deep-learning/packed-lstm-lengths-and-last-valid-state', 'deep-learning/recurrent-hidden-state-reset-and-truncated-gradients', 'deep-learning/causal-target-shift-and-padding-loss', 'deep-learning/train-eval-validation-loop', 'deep-learning/inference-schema-and-latency'], RECURRENCE, True)

add('masked-reconstruction-loss-and-anomaly-threshold',
    'Masked reconstruction loss and anomaly thresholds',
    'An autoencoder learns to reconstruct accepted normal windows; its reconstruction error becomes an anomaly score only after missing values and threshold calibration are defined.', [
    ('Define what the model sees', 'An encoder compresses a telemetry window into a smaller representation and a decoder predicts the original features. Training on a pool labeled normal does not guarantee every row is normal. Audit contamination from known faults, maintenance events and sensor outages before fitting. Normalize each feature with statistics computed only from the training population, and persist those statistics for serving. [[deep-learning/train-eval-validation-loop|Split discipline]] keeps threshold calibration separate from fitting.'),
    ('Mask missing measurements', 'Zero may be a meaningful reading, so do not use zero as a missing-value marker. Store a Boolean observation mask and impute absent inputs from training-set statistics before the encoder. Calculate reconstruction loss only on observed targets, dividing by the observed count per window. A window with no observed fields has no defensible score and should be rejected. Count coverage beside score, since a low error based on one field is not comparable with a full six-field window.'),
    ('Choose the scoring unit', 'For each window, squared error can be averaged over observed feature positions. That mean gives a comparable scale across different coverage, but it may hide one critical sensor spike under five quiet sensors. Consider separate feature-family scores or a maximum standardized residual when the product needs sensitivity to localized faults. Pin the choice before threshold tuning. A decoder with too much capacity may reconstruct faults well, so low error is not a proof of normality. [[deep-learning/telemetry-autoencoder-alert-project|The alert project]] tests this failure mode.'),
    ('Calibrate without reusing training loss', 'Fit the model on training normals, score a disjoint normal calibration set and choose a threshold under an explicit alert-budget target. A percentile on four reference windows is only a code illustration, not a credible operating threshold. Use enough independent device-days to estimate the tail, and report the numerator and denominator for false alarms. If labeled incidents exist, inspect detection recall on a separate incident set, but do not tune repeatedly on the final test group.'),
    ('Monitor shifts after release', 'A sensor replacement or seasonal operating mode can raise reconstruction error without a fault. Track feature coverage, score distribution, alert rate and downstream confirmed incidents by device cohort. Store model, preprocessing and threshold revisions together so a rollback restores the decision rule, not just weights. A changed score distribution calls for investigation and possibly fresh validation, not an automatic threshold increase that hides genuine failures.')],
    '''import torch
from torch import nn

class TelemetryAutoencoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(6, 4), nn.ReLU(), nn.Linear(4, 2))
        self.decoder = nn.Sequential(nn.Linear(2, 4), nn.ReLU(), nn.Linear(4, 6))

    def forward(self, readings: torch.Tensor) -> torch.Tensor:
        return self.decoder(self.encoder(readings))

torch.manual_seed(73)
normal_readings = torch.tensor([[0.2, 0.4, 0.1, 0.7, 0.3, 0.6],
                                [0.3, 0.5, 0.2, 0.6, 0.4, 0.0]])
observed = torch.tensor([[True, True, True, True, True, True],
                         [True, True, True, True, True, False]])
training_medians = torch.tensor([0.25, 0.45, 0.15, 0.65, 0.35, 0.55])
model_inputs = torch.where(observed, normal_readings, training_medians)
reconstruction = TelemetryAutoencoder()(model_inputs)
observed_count = observed.sum(dim=1)
if bool((observed_count == 0).any()):
    raise ValueError("unscorable telemetry window")
window_scores = (((reconstruction - normal_readings).square() * observed)
                 .sum(dim=1) / observed_count)
assert window_scores.shape == (2,)
assert torch.isfinite(window_scores).all()''',
    'For input width D and hidden widths H and Z, dense encoder/decoder work scales with the matrix products across their layers; parameter storage does not grow with the number of windows. Per-window masked score calculation is O(D). Calibration requires scoring a separate population and retaining enough score samples or a controlled quantile sketch to estimate the tail. A larger decoder can improve reconstruction while making anomalies less separable.',
    ['Do not turn missing readings into genuine zeros in the target loss.', 'Do not choose an alert threshold from the same training windows used to fit the model.', 'Do not assume every high-error window is a fault or every low-error window is safe.'],
    ['deep-learning/train-eval-validation-loop', 'deep-learning/tensor-shape-dtype-contract', 'deep-learning/variational-latent-kl-and-collapse', 'deep-learning/inference-schema-and-latency', 'deep-learning/telemetry-autoencoder-alert-project'], RECONSTRUCTION)

add('variational-latent-kl-and-collapse',
    'Variational latent sampling, KL accounting and collapse',
    'A variational autoencoder predicts a distribution for each latent coordinate and balances reconstruction against a KL penalty; neither term should be hidden in an opaque total.', [
    ('Parameterize a distribution', 'The encoder produces a mean and log variance for every latent coordinate. Draw standard noise and form a sample as mean plus exp(0.5 × log variance) times noise. This separates the random draw from trainable parameters, allowing gradients through the sample path. Store log variance rather than a raw standard deviation to avoid requiring a positive unconstrained network output. Numerical range still matters: unbounded log variance can overflow an exponential. [[deep-learning/logits-loss-gradient|Loss contracts]] should record reductions and dtype.'),
    ('Keep both losses on named scales', 'A reconstruction term measures the decoded output against the observed input under a chosen likelihood or proxy loss. For a diagonal Gaussian posterior against a unit Gaussian prior, the per-example KL is minus one half times the sum over latent coordinates of one plus log variance minus squared mean minus variance. Average both per-example sums over the batch before combining them. Changing reconstruction from a sum over features to a mean per feature changes its relative weight against KL even if a coefficient stays unchanged.'),
    ('Watch for latent collapse', 'If the decoder can reconstruct without using the sampled code, the posterior can move close to the prior and KL can approach zero. That can look like a tidy optimization trace while the latent carries little input information. Track reconstruction, KL, latent means and an intervention that swaps latent codes between inputs. A scheduled KL weight or reduced decoder capacity may help in some tasks, but choose it using held-out behavior rather than treating a nonzero KL as proof of useful representation.'),
    ('Separate generation from anomaly scoring', 'Sampling from the prior can generate new outputs, while scoring an observed telemetry window requires a stable procedure. A single random latent sample injects score noise; use the posterior mean or average a fixed number of samples and report the compute and variance. A VAE reconstruction score is not calibrated fault probability. Compare it to a deterministic autoencoder and a simple per-feature baseline on the same held-out incidents. [[deep-learning/masked-reconstruction-loss-and-anomaly-threshold|Threshold calibration]] is still required.'),
    ('Guard numerical and deployment state', 'Check finite mean, log variance, KL, reconstruction and gradients before stepping. Save model weights, preprocessing, latent policy, random-seed policy when sampling, reduction convention and threshold. At serving, switching from sampled latents to means changes score distribution, so a threshold calibrated under one policy cannot be reused silently under the other. Test a fixed batch after reload and track both score components through model revisions.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

class SensorVariationalEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.shared = nn.Sequential(nn.Linear(6, 9), nn.ReLU())
        self.mean_head = nn.Linear(9, 3)
        self.log_variance_head = nn.Linear(9, 3)
        self.decoder = nn.Linear(3, 6)

    def forward(self, normalized_readings: torch.Tensor):
        hidden = self.shared(normalized_readings)
        latent_mean = self.mean_head(hidden)
        latent_log_variance = self.log_variance_head(hidden).clamp(-12, 8)
        latent_std = torch.exp(0.5 * latent_log_variance)
        latent_sample = latent_mean + latent_std * torch.randn_like(latent_std)
        return self.decoder(latent_sample), latent_mean, latent_log_variance

torch.manual_seed(67)
model = SensorVariationalEncoder()
normal_readings = torch.rand(4, 6)
reconstructed, latent_mean, log_variance = model(normal_readings)
reconstruction_per_case = functional.mse_loss(
    reconstructed, normal_readings, reduction="none").sum(dim=1)
kl_per_case = -0.5 * (1 + log_variance - latent_mean.square()
                      - log_variance.exp()).sum(dim=1)
reconstruction_loss = reconstruction_per_case.mean()
kl_loss = kl_per_case.mean()
total_loss = reconstruction_loss + 0.37 * kl_loss
total_loss.backward()
assert torch.isfinite(total_loss)
assert kl_per_case.shape == (4,)''',
    'Encoder and decoder matrix products dominate work; sampling and diagonal KL add O(batch × latent width) arithmetic and storage. Averaging several latent samples multiplies decoder work by the sample count. Clamping log variance prevents some overflow but changes gradients at the clamp bounds, so log clamp frequency should be monitored. A small KL number can signal collapse rather than computational efficiency.',
    ['Do not compare KL to a reconstruction term whose reduction convention changed unnoticed.', 'Do not call a near-zero KL proof that the latent representation is good.', 'Do not calibrate an anomaly threshold with sampled latents and serve with posterior means.'],
    ['deep-learning/masked-reconstruction-loss-and-anomaly-threshold', 'deep-learning/logits-loss-gradient', 'deep-learning/mixed-precision-scaling-and-gradient-clipping', 'deep-learning/checkpoint-resume-state', 'deep-learning/telemetry-autoencoder-alert-project'], RECONSTRUCTION)

add('telemetry-autoencoder-alert-project',
    'Project: calibrate an autoencoder alert for freezer telemetry',
    'Train a compact reconstruction model on normal freezer windows, calibrate an alert budget on separate device-days and challenge it with sensor loss and operating-mode shifts.', [
    ('Partition the operating record', 'Collect temperature, compressor current, door state and three other measurements in fixed windows. Keep maintenance windows and confirmed faults out of the normal fitting pool, then split by device and day before scaling. Reserve separate normal calibration days, incident evaluation days and a final untouched test group. Multiple overlapping windows from one day must not appear on both sides of a split. [[deep-learning/masked-reconstruction-loss-and-anomaly-threshold|Masked scoring]] needs an observation flag for every feature.'),
    ('Fit and record a baseline', 'Compute feature medians and scales from training normals only. Fit a six-to-two-to-six autoencoder and compare it with a simple standardized-distance rule. Loss excludes missing targets and rejects an all-missing window. Keep the reconstruction loss, feature coverage and score distribution by device; a low training loss alone does not establish fault separation. Run a controlled VAE candidate with named reconstruction and KL terms, but keep its serving score policy fixed. [[deep-learning/variational-latent-kl-and-collapse|KL accounting]] prevents a hidden change in scale.'),
    ('Calibrate the alert budget', 'Choose a score threshold on normal calibration device-days for a stated false-alert budget, such as no more than three alerts per device-day under the observed sample. Group consecutive flagged windows into one incident before counting alerts. Evaluate fault recall and time to first alert on a separate incident set. A toy four-window quantile in code only illustrates an API; real tail calibration needs far more independent days and a confidence statement.'),
    ('Attack the decision rule', 'Withhold the compressor-current reading, then repeat with all fields missing; the first should be scored with coverage attached, and the second rejected. Test a door-open service period, a sensor replacement and a genuine warming fault. An overly capable decoder may reconstruct a warming fault, while a new sensor offset may create false positives. Report those failures explicitly instead of tuning the threshold on the final test days.'),
    ('Package a reversible release', 'Save weights, feature order, medians, scales, missing-value policy, threshold, aggregation window and model revision. On a fresh process, reload and reproduce fixed-window scores and alert decisions. Monitor score and coverage distributions by device cohort and compare confirmed incidents against the expected alert budget. If a drift appears, route it to evaluation; do not silently raise the threshold. Keep the preceding artifact available for rollback.')],
    '''import torch
from torch import nn

class FreezerWindowAutoencoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(6, 3), nn.ReLU(), nn.Linear(3, 2))
        self.decoder = nn.Sequential(nn.Linear(2, 3), nn.ReLU(), nn.Linear(3, 6))

    def forward(self, normalized_window: torch.Tensor) -> torch.Tensor:
        return self.decoder(self.encoder(normalized_window))

torch.manual_seed(71)
training_normals = torch.rand(8, 6)
calibration_normals = torch.rand(5, 6)
candidate_windows = torch.rand(2, 6)
detector = FreezerWindowAutoencoder()
optimizer = torch.optim.AdamW(detector.parameters(), lr=0.0037)
for _ in range(23):
    optimizer.zero_grad(set_to_none=True)
    reconstruction = detector(training_normals)
    loss = (reconstruction - training_normals).square().mean()
    loss.backward()
    optimizer.step()

detector.eval()
with torch.inference_mode():
    calibration_scores = (detector(calibration_normals) - calibration_normals).square().mean(dim=1)
    candidate_scores = (detector(candidate_windows) - candidate_windows).square().mean(dim=1)
threshold = torch.quantile(calibration_scores, 0.8)  # API illustration only
candidate_alerts = candidate_scores > threshold
assert candidate_alerts.shape == (2,)
assert torch.isfinite(candidate_scores).all()''',
    'Dense model work is small for six features; data preparation, storage and operational alert review can dominate system cost. Online scoring is O(DH + HZ + ZH + HD) for feature width D and internal widths H and Z. Calibration and evaluation cost grows with independent device-days, not just window count. This toy quantile is deliberately too small for deployment; estimate threshold uncertainty and alert clustering on real historical days.',
    ['Do not calibrate and evaluate on overlapping windows from the same device-day.', 'Do not turn an all-missing window into a low-error normal score.', 'Do not equate one flagged window with one operational incident when alerts cluster.'],
    ['deep-learning/masked-reconstruction-loss-and-anomaly-threshold', 'deep-learning/variational-latent-kl-and-collapse', 'deep-learning/train-eval-validation-loop', 'deep-learning/inference-schema-and-latency', 'deep-learning/checkpoint-resume-state'], RECONSTRUCTION, True)

CROSSLINKS = [
    ('deep-learning/tensor-shape-dtype-contract', 'deep-learning/packed-lstm-lengths-and-last-valid-state'),
    ('deep-learning/causal-target-shift-and-padding-loss', 'deep-learning/packed-lstm-lengths-and-last-valid-state'),
    ('deep-learning/sequence-attention-leakage-project', 'deep-learning/service-event-lstm-project'),
    ('deep-learning/train-eval-validation-loop', 'deep-learning/service-event-lstm-project'),
    ('deep-learning/inference-schema-and-latency', 'deep-learning/recurrent-hidden-state-reset-and-truncated-gradients'),
    ('deep-learning/checkpoint-resume-state', 'deep-learning/recurrent-hidden-state-reset-and-truncated-gradients'),
    ('deep-learning/batching-and-class-sampling', 'deep-learning/packed-lstm-lengths-and-last-valid-state'),
    ('deep-learning/gradient-accumulation-and-effective-batch', 'deep-learning/recurrent-hidden-state-reset-and-truncated-gradients'),
    ('deep-learning/logits-loss-gradient', 'deep-learning/variational-latent-kl-and-collapse'),
    ('deep-learning/mixed-precision-scaling-and-gradient-clipping', 'deep-learning/variational-latent-kl-and-collapse'),
    ('deep-learning/receipt-image-quality-project', 'deep-learning/masked-reconstruction-loss-and-anomaly-threshold'),
    ('deep-learning/deep-learning-tutorial', 'deep-learning/telemetry-autoencoder-alert-project'),
]

if __name__ == '__main__':
    publish(LESSONS, (RECURRENCE, RECONSTRUCTION), CROSSLINKS,
            'aitrove-deep-learning-recurrence-reconstruction-import-20261006.json',
            7840, subject='deep-learning')
