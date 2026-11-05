"""Add audio and short-video Deep Learning paths."""
from de_batch_publisher import publish

AUDIO = 'Audio windows, spectral features and alarm review'
VIDEO = 'Video clips, temporal evidence and event review'
LESSONS = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    assert len(sections) == 5
    LESSONS.append(dict(path='deep-learning/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add('audio-sample-rate-stft-and-window-contract',
    'Audio sample rates, short-time spectra and window contracts',
    'A waveform model receives samples at a declared rate; a spectrogram adds window, hop and padding choices that must match training and serving.', [
    ('Start with physical time', 'A recording of 32,000 samples at 16,000 samples per second lasts two seconds. The same array tagged as 8,000 samples per second appears four seconds long and shifts every frequency interpretation. Keep original rate, target rate, channel layout and recording-device identity in the manifest. Resampling means calculating new samples with an appropriate anti-aliasing filter; changing metadata is not resampling. The code checks duration and the spectral frame layout for one consistent rate. [[deep-learning/ctc-time-length-and-blank-alignment-contract|Sequence lengths]] later depend on this contract.'),
    ('Declare the analysis window', 'A short-time Fourier transform divides a waveform into overlapping windows. The transform’s FFT width controls frequency-bin spacing, while the hop controls how often a frame begins. With centered padding disabled, a 32,000-sample signal, 400-sample window and 160-sample hop yields 198 complete frames under a standard floor-count rule. A centered transform yields a different count because it pads the ends. State the window function, padding mode, return type and magnitude or power conversion; a tensor with the expected rank can still have the wrong time base.'),
    ('Protect the label interval', 'A machine alarm label may mark a brief squeal inside a long recording. Training on a clip labeled alarm when the selected crop excludes that squeal creates incorrect supervision. Keep event start and end times, then decide whether a window is positive by overlap, center time or any audible presence. The rule affects class balance and false-alert interpretation. Save waveform excerpts and spectrogram snapshots for reviewed cases. [[deep-learning/audio-time-frequency-mask-and-label-boundary|Masking]] must preserve the evidence needed for the label.'),
    ('Normalize with training-only statistics', 'Record microphone gain, clipping fraction, channel mixing and silence handling. A log-power spectrum usually needs a floor before logarithms so silent bins remain finite. Any mean and scale applied to features should come from training recordings, then be frozen for later devices and sites. A model can learn microphone hiss or compression artifacts rather than a fault. Group the split by physical machine and recording session before extracting overlapping windows. [[deep-learning/augmentation-leakage-boundary|The split boundary]] applies to every crop.'),
    ('Compare deployed preprocessing byte for byte', 'Replay a fixed waveform through both training and serving paths and compare sample count, spectral bins, frame count, value range and output logits within tolerance. Check p95 time from audio capture through resampling, feature extraction and model scoring. A fast neural forward does not compensate for a slow decoder or resampler. [[deep-learning/machine-audio-alarm-project|The applied project]] gates the full alert path and review load.')],
    '''import torch

sample_rate = 16000
sample_count = 32000
window_size = 400
hop_size = 160
waveform = torch.linspace(-0.7, 0.7, sample_count)
window = torch.hann_window(window_size)
complex_spectrum = torch.stft(waveform, n_fft=window_size,
                              hop_length=hop_size, win_length=window_size,
                              window=window, center=False, return_complex=True)
power_spectrum = complex_spectrum.abs().square()
log_power = torch.log(power_spectrum.clamp_min(1e-7))
assert sample_count / sample_rate == 2.0
assert log_power.shape == (window_size // 2 + 1,
                           1 + (sample_count - window_size) // hop_size)
assert torch.isfinite(log_power).all()''',
    'For N samples, FFT width F and hop H, the frame count is approximately N/H, and a direct FFT implementation uses roughly O((N/H) F log F) arithmetic with O((N/H) F) spectral storage. A log-power representation adds no trainable parameters but can become a large intermediate tensor for long recordings. Resampling and decode add separate costs. The example verifies frame geometry and finite values, not alarm accuracy or correct resampling of a real file.',
    ['Do not relabel sample-rate metadata and call that resampling.', 'Do not infer event presence from a recording-level label after cropping.', 'Do not change centered padding or hop size between training and serving.'],
    ['deep-learning/audio-time-frequency-mask-and-label-boundary', 'deep-learning/machine-audio-alarm-project', 'deep-learning/ctc-time-length-and-blank-alignment-contract', 'deep-learning/augmentation-leakage-boundary', 'deep-learning/inference-schema-and-latency'], AUDIO)

add('audio-time-frequency-mask-and-label-boundary',
    'Audio time-frequency masks and label preservation',
    'Spectral masking can regularize an audio model, but hiding the only labeled event turns a positive window into a contradictory training case.', [
    ('Separate augmentation from missing data', 'A training-time frequency mask removes a band of spectral values; a time mask removes consecutive frames. These artificial omissions are not equivalent to microphone dropouts or packet loss in the field. Use them only after verifying the source label remains supported. A brief fault chirp might occupy four of eighty frames; masking those four frames erases the event. Keep reviewed event boundaries and cap mask size relative to the event interval. [[deep-learning/audio-sample-rate-stft-and-window-contract|The window contract]] maps frames back to physical time.'),
    ('Choose replacement values deliberately', 'Setting a log-power mask to numeric zero does not mean silence if the log scale was standardized. It may mean average energy. Choose a replacement consistent with the representation, and audit whether masked regions become an easy synthetic cue. Apply augmentation to training examples only; validation should reflect the intended field distribution unless a separate stress test is declared. Record seeds, mask widths and the proportion of examples whose label-bearing interval was touched. Never report augmented validation as if it were untouched deployment data.'),
    ('Preserve timestamp alignment', 'If hop length is 160 samples at 16,000 samples per second, one frame step is ten milliseconds. A time mask from frames twenty through twenty-seven covers roughly a short region, but window support overlaps neighboring frames. Align event times to frame support rather than treating each frame as an isolated instant. The pure-Python code rejects a mask overlapping a reviewed event span before replacing values. A production implementation should also consider the window width and boundary rounding.'),
    ('Evaluate rare-event recall', 'Compare clean validation and a controlled noise or dropout stress set by microphone type, fault length and background noise. Report event recall, false alarms per machine-hour and latency to first alert. A small aggregate accuracy gain can hide lower recall for short squeals. Track whether masking improves robustness only on synthetic corruption and degrades real recordings. [[deep-learning/machine-audio-alarm-project|The project]] includes a reviewed fault gallery and an alert-budget gate.'),
    ('Keep a reproducible transform manifest', 'Package sample rate, spectral transform, normalization, mask distributions and augmentation order with the model. A waveform shift before spectral extraction and a time mask after extraction do not have identical effects. Run fixed seeds through the same input twice and assert reproducibility where required. Keep augmentation off at serving. If fault times are unavailable, use conservative masks and inspect positive crops manually rather than assuming their labels survive.')],
    '''def safe_time_mask(spectral_rows, start, stop, event_start, event_stop):
    if not (0 <= start <= stop <= len(spectral_rows[0])):
        raise ValueError("invalid frame interval")
    if max(start, event_start) < min(stop, event_stop):
        raise ValueError("mask would remove reviewed fault evidence")
    masked = [row.copy() for row in spectral_rows]
    for row in masked:
        row[start:stop] = [0.0] * (stop - start)
    return masked

fault_spectrum = [[0.3] * 12, [0.8] * 12]
masked_spectrum = safe_time_mask(fault_spectrum, 1, 4, 7, 10)
assert all(row[1:4] == [0.0, 0.0, 0.0] for row in masked_spectrum)
assert fault_spectrum[0][1] == 0.3
try:
    safe_time_mask(fault_spectrum, 8, 11, 7, 10)
except ValueError:
    pass
else:
    raise AssertionError("event-overlapping mask was accepted")''',
    'The reference copies a frequency-by-time array, costing O(FT) time and space for F bins and T frames; an in-place tensor operation can avoid the copy but must not mutate cached validation features. Mask generation itself is O(FM) for mask width M when applied to every frequency row. The real operating cost is extra training variants and label review. A mask that removes the event can lower model quality despite being computationally cheap.',
    ['Do not apply augmentation masks to the final clean evaluation without labeling it a stress test.', 'Do not let a time mask erase the only positive event.', 'Do not assume zero means silence after log scaling or standardization.'],
    ['deep-learning/audio-sample-rate-stft-and-window-contract', 'deep-learning/machine-audio-alarm-project', 'deep-learning/augmentation-leakage-boundary', 'deep-learning/contrastive-view-identity-and-augmentation-contract', 'deep-learning/inference-schema-and-latency'], AUDIO)

add('machine-audio-alarm-project',
    'Project: classify machine alarms from short audio windows',
    'Detect reviewed fault sounds while preserving sample-rate, event-window and microphone boundaries through training and deployment.', [
    ('Build a recording ledger', 'Collect machine audio with recording session, site, microphone, rate, channel count and reviewed fault intervals. Split by machine and session before creating overlapping windows. Keep a clean holdout with microphones and operating regimes that were not used to tune thresholds. Define whether the output is window-level fault presence or an event timestamp; the small model below predicts one class per spectral window. [[deep-learning/audio-sample-rate-stft-and-window-contract|The audio lesson]] fixes the preprocessing geometry.'),
    ('Run a spectral training check', 'Extract log-power or log-mel features with frozen settings, normalize using training-only statistics and reject nonfinite or clipped inputs. The code trains a tiny convolutional classifier on already prepared spectral tensors to verify shape, label and gradient flow. It does not read recordings, resample or establish fault performance. Use the exact deployed extraction path for real experiments. Save one fixed waveform and its derived feature tensor as a parity fixture.'),
    ('Protect short alarms during augmentation', 'Time or frequency masks must not remove the reviewed fault interval. Separate clean and corrupted evaluation sets, then report detection recall for short and long faults, noise conditions and device families. [[deep-learning/audio-time-frequency-mask-and-label-boundary|The masking lesson]] gives an explicit guard. If a fault event spans several windows, score it as one event after deduplicating neighboring alerts; window accuracy alone can exaggerate success.'),
    ('Measure on-call cost', 'Select score and event-merging thresholds on development sessions, then freeze them. Report event recall, median and p95 detection delay, false alarms per machine-hour and review minutes per shift. Compare with a simple energy or spectral rule under the same alarm budget. Inspect false alarms caused by maintenance sounds and benign speed changes. A high window-level score may still page an operator repeatedly for one sustained noise.'),
    ('Release with missing-audio behavior', 'Package sample rate, resampling, spectral settings, normalization, window stride, class map, threshold and deduplication policy. Gate on rare-fault recall, false-alarm budget and capture-to-alert latency. If a microphone disconnects or produces invalid audio, report unavailable input instead of a confident healthy prediction. Replay fixed recordings in a clean process and retain the earlier alarm path when the candidate misses a gate.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

torch.manual_seed(47)
log_spectral_windows = torch.rand(4, 1, 16, 20)
reviewed_alarm_classes = torch.tensor([0, 1, 2, 1])
alarm_model = nn.Sequential(nn.Conv2d(1, 8, 3, padding=1), nn.ReLU(),
                            nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(8, 3))
optimizer = torch.optim.AdamW(alarm_model.parameters(), lr=0.0007)
optimizer.zero_grad(set_to_none=True)
alarm_logits = alarm_model(log_spectral_windows)
assert alarm_logits.shape == (4, 3)
loss = functional.cross_entropy(alarm_logits, reviewed_alarm_classes)
loss.backward()
optimizer.step()
assert torch.isfinite(loss)''',
    'The example consumes O(BFT) spectral values for B windows, F frequency bins and T frames, with convolutional activation storage during training. Real cost includes audio decode, resampling, spectral extraction, overlapping window scoring and alert deduplication. Smaller window strides increase the number of model calls and may reduce detection delay, but can also multiply correlated false alerts. Measure the complete capture-to-alert pipeline on target hardware; the toy update is only a wiring check.',
    ['Do not split overlapping windows from one recording across train and test.', 'Do not count repeated windows from one fault as independent successful events.', 'Do not emit healthy status when the microphone input is unavailable.'],
    ['deep-learning/audio-sample-rate-stft-and-window-contract', 'deep-learning/audio-time-frequency-mask-and-label-boundary', 'deep-learning/temperature-scaling-and-selective-risk', 'deep-learning/inference-schema-and-latency', 'deep-learning/receipt-confidence-audit-project'], AUDIO, True)

add('video-clip-timestamps-and-grouped-evaluation',
    'Video clip timestamps and recording-group evaluation',
    'Short-video labels depend on frame timestamps and source-recording identity; splitting adjacent clips independently can make held-out accuracy meaningless.', [
    ('Sample by elapsed time', 'A camera may drop frames or vary its frame rate. Taking every fifth decoded frame then changes the real-time span across recordings. Choose target timestamps relative to the clip start and select or interpolate frames according to a declared policy. The code selects frames nearest 0, 120 and 240 milliseconds from an irregular timestamp list. A duplicate selected frame or a large timestamp gap should be recorded rather than silently treated as smooth motion. [[deep-learning/video-temporal-convolution-and-aggregation|The model lesson]] expects a fixed frame count.'),
    ('Attach labels to intervals', 'A conveyor jam label may describe seconds four through six of a ten-second recording. A clip from seconds zero through two is not a jam clip just because it came from the same file. Define overlap or center-time rules for assigning labels and mark ambiguous boundary clips for review. Keep source recording ID, camera, line, shift and event interval with every derived clip. Save timestamped thumbnails to audit whether selected frames actually contain the action.'),
    ('Split at the source boundary', 'Many overlapping clips from one recording share most pixels and background. A random clip split lets near-duplicates into train and test, and a model can memorize the conveyor or camera angle. Split by recording, then consider a stricter camera or site holdout for transfer claims. Report the number of independent recordings and jams, not merely the inflated clip count. [[deep-learning/augmentation-leakage-boundary|Augmentation leakage]] has the same parent-identity problem.'),
    ('Preserve temporal order and sampling revision', 'A model with a temporal convolution receives frames in a specific order. Reversing them can change the meaning of a jam onset even if average appearance is similar. Record target times, clip duration, frame resize and any missing-frame substitution. If inference uses a rolling stream while training used offline clips centered around an event, the model may have seen future frames during training. Declare whether the task is retrospective tagging or live early warning.'),
    ('Evaluate at event level', 'Adjacent positive clips from one jam should count as one incident for recall and alert load. Report event recall, first-alert delay, false alerts per camera-hour, and performance by lighting and camera movement. Compare against a static-frame baseline to prove the temporal model contributes more than background recognition. [[deep-learning/conveyor-jam-video-project|The project]] ties those metrics to a reversible release.')],
    '''def nearest_timestamp_indices(frame_times_ms, target_times_ms):
    if not frame_times_ms or frame_times_ms != sorted(frame_times_ms):
        raise ValueError("frame timestamps must be ordered")
    return [min(range(len(frame_times_ms)),
                key=lambda index: (abs(frame_times_ms[index] - target), index))
            for target in target_times_ms]

decoded_frame_times = [0, 40, 83, 121, 160, 203, 241]
selected = nearest_timestamp_indices(decoded_frame_times, [0, 120, 240])
assert selected == [0, 3, 6]
assert [decoded_frame_times[index] for index in selected] == [0, 121, 241]''',
    'This direct search is O(FT) time for F decoded frames and T requested timestamps, with O(T) output space; a two-pointer pass over sorted timestamps can reduce selection to O(F + T) for long recordings. Decoding and storing all frames usually cost far more memory and time. A clip with C channels, T frames and H-by-W resolution uses O(CTHW) input values before model activations. Record actual time gaps so a fixed tensor shape does not conceal variable motion speed.',
    ['Do not split adjacent clips from one recording between training and final test.', 'Do not assign a full-recording event label to clips outside the event interval.', 'Do not treat frame index spacing as fixed elapsed time on variable-rate video.'],
    ['deep-learning/video-temporal-convolution-and-aggregation', 'deep-learning/conveyor-jam-video-project', 'deep-learning/augmentation-leakage-boundary', 'deep-learning/causal-dilated-convolution-receptive-field', 'deep-learning/inference-schema-and-latency'], VIDEO)

add('video-temporal-convolution-and-aggregation',
    'Video temporal convolutions and clip aggregation',
    'A three-dimensional convolution processes channel, time and spatial axes together; a clip-level head must then aggregate evidence without erasing short events.', [
    ('Check the five axes', 'A common video tensor order is batch, channels, frames, height and width. Swapping channels with time can make a valid-looking convolution run on the wrong axis if dimensions happen to match. The code asserts the input and output shapes for a five-frame grayscale clip. Record whether values are RGB, grayscale or encoded motion and keep preprocessing identical at serving. [[deep-learning/video-clip-timestamps-and-grouped-evaluation|The clip lesson]] defines the physical-time meaning of each frame slot.'),
    ('Choose temporal support for the event', 'A width-three temporal kernel sees neighboring frames, while stacking layers broadens its receptive field. Early temporal pooling can discard a fault visible in only one or two frames. Global average pooling is easy but can dilute a brief jam; maximum pooling may react strongly to noise. Compare aggregation rules on reviewed short and sustained events with the same clip sampling. Keep spatial resolution high enough to see belt motion but measure its memory cost.'),
    ('Distinguish offline and causal use', 'An offline clip classifier can inspect frames before and after an event midpoint. A live warning at time t cannot use frames after t. If deployment is live, construct training clips ending at t, then evaluate first-alert delay on replayed streams. A symmetric temporal convolution over a clip ending at t is still causal with respect to t, but a centered clip around t is not. [[deep-learning/causal-dilated-convolution-receptive-field|Causal sequence reasoning]] applies despite the different model shape.'),
    ('Control duplicate and background cues', 'Random crops from the same video can share camera texture, timestamps or compression artifacts. Split by recording and camera when needed, and use controlled background changes to see whether motion matters. Compare with a one-frame classifier and a simple frame-difference statistic. If the temporal model only wins on a split that shares source recordings, do not claim event generalization. Report error by event duration and the independent video count.'),
    ('Measure the streaming envelope', 'The model may score overlapping clips every few frames. Count decoded frames, reused feature work, GPU memory and p95 end-to-end alert time. A long clip or dense stride can increase both coverage and compute. Package clip duration, sampling timestamps, frame resize, aggregation and score threshold. [[deep-learning/conveyor-jam-video-project|The project]] tests whether event recall improves at an acceptable false-alert rate and latency.')],
    '''import torch
from torch import nn

torch.manual_seed(47)
camera_clips = torch.rand(2, 1, 5, 8, 8)
temporal_features = nn.Conv3d(1, 4, kernel_size=(3, 3, 3),
                              padding=(1, 1, 1))(camera_clips)
assert temporal_features.shape == (2, 4, 5, 8, 8)
spatially_pooled = temporal_features.mean(dim=(-1, -2))
assert spatially_pooled.shape == (2, 4, 5)
clip_features = spatially_pooled.amax(dim=-1)
jam_head = nn.Linear(4, 2)
jam_logits = jam_head(clip_features)
assert jam_logits.shape == (2, 2)''',
    'For B clips, C input channels, F filters, T frames, H-by-W pixels and a kernel of k_t by k_h by k_w, direct 3D convolution work is roughly O(BCFTHWk_tk_hk_w). Intermediate activations occupy O(BFTHW), often dominating the tiny classifier head. Temporal max pooling adds little compute but can amplify noisy peaks; average pooling may miss brief events. The example checks shape and aggregation only. Measure the full decode-and-score path at the target clip rate.',
    ['Do not confuse channel and frame axes.', 'Do not train on clips centered on future frames for a live-warning claim.', 'Do not let global pooling hide short events without an event-duration audit.'],
    ['deep-learning/video-clip-timestamps-and-grouped-evaluation', 'deep-learning/conveyor-jam-video-project', 'deep-learning/convolution-output-geometry-and-receptive-field', 'deep-learning/causal-dilated-convolution-receptive-field', 'deep-learning/inference-schema-and-latency'], VIDEO)

add('conveyor-jam-video-project',
    'Project: detect conveyor jams from timestamped video clips',
    'Train a short-clip event model and test it by independent recording, first-alert delay and false pages per camera-hour.', [
    ('Build the event ledger', 'Record camera and conveyor IDs, physical recording IDs, frame timestamps and reviewed jam start and end times. Extract clips ending at each proposed live decision time; label them by a declared event-overlap rule. Split whole recordings before clip extraction, then reserve later time periods or new camera angles for a final transfer test. Keep ambiguous onset frames available for review. [[deep-learning/video-clip-timestamps-and-grouped-evaluation|The clip lesson]] prevents adjacent-clip leakage.'),
    ('Run the model wiring check', 'The code performs one synthetic update on a tiny 3D convolutional classifier. It proves batch, channel, frame, height and width ordering plus a finite class loss; it cannot establish real event detection. Train the actual model against a one-frame baseline and a motion-statistic baseline under the same event ledger. Test a frame-order shuffle to see whether the candidate depends on temporal evidence. [[deep-learning/video-temporal-convolution-and-aggregation|The temporal lesson]] explains aggregation tradeoffs.'),
    ('Score independent events', 'Merge neighboring positive clip scores into one alert with a frozen cooldown. Report jam-event recall, first-alert delay, false pages per camera-hour and recall by jam duration. Group bootstrap or uncertainty calculations by recording rather than by thousands of overlapping clips. Inspect lighting transitions, maintenance, camera shakes and temporarily stopped belts. A high clip accuracy can coexist with repeated false pages during a single maintenance period.'),
    ('Test actual live replay', 'Replay a recording in timestamp order and make each decision using only frames available by that time. Include video decode, resize, clip buffering, model forward and cooldown in p95 latency. Test dropped frames and missing video: output an unavailable status or fallback signal rather than a confident no-jam. Select thresholds on development recordings; do not watch the final replay and retune.'),
    ('Release with a clear rollback', 'Package sampling times, resize, normalization, model weights, threshold, cooldown and camera-specific eligibility. Gate on event recall, false-page budget and first-alert deadline. Retain the previous operational monitor if the model misses any gate. The deliverable includes event-level counts, replay traces and failure clips with reviewed timestamps, not just one averaged score.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

torch.manual_seed(47)
timestamped_clips = torch.rand(4, 1, 5, 8, 8)
reviewed_jam_labels = torch.tensor([0, 1, 0, 1])
jam_model = nn.Sequential(nn.Conv3d(1, 8, kernel_size=3, padding=1),
                          nn.ReLU(), nn.AdaptiveAvgPool3d(1),
                          nn.Flatten(), nn.Linear(8, 2))
optimizer = torch.optim.AdamW(jam_model.parameters(), lr=0.0007)
optimizer.zero_grad(set_to_none=True)
jam_logits = jam_model(timestamped_clips)
assert jam_logits.shape == (4, 2)
loss = functional.cross_entropy(jam_logits, reviewed_jam_labels)
loss.backward()
optimizer.step()
assert torch.isfinite(loss)''',
    'Clip input and intermediate activations scale with BTHW for B clips, T frames and H-by-W resolution, multiplied by model channel widths. Serving cost includes repeated decode and overlapping clip inference; event cooldown reduces alert count but not necessarily compute. Increasing frame rate or clip overlap can improve onset coverage while raising throughput needs. The toy update is a tensor-path check, not a measurement of event recall or camera-hour false pages.',
    ['Do not score overlapping positive clips as separate independent jams.', 'Do not use future frames in a claimed live decision.', 'Do not hide dropped video behind a negative class prediction.'],
    ['deep-learning/video-clip-timestamps-and-grouped-evaluation', 'deep-learning/video-temporal-convolution-and-aggregation', 'deep-learning/receipt-confidence-audit-project', 'deep-learning/inference-schema-and-latency', 'deep-learning/temperature-scaling-and-selective-risk'], VIDEO, True)

CROSSLINKS = [
    ('deep-learning/ctc-time-length-and-blank-alignment-contract', 'deep-learning/audio-sample-rate-stft-and-window-contract'),
    ('deep-learning/augmentation-leakage-boundary', 'deep-learning/audio-sample-rate-stft-and-window-contract'),
    ('deep-learning/contrastive-view-identity-and-augmentation-contract', 'deep-learning/audio-time-frequency-mask-and-label-boundary'),
    ('deep-learning/temperature-scaling-and-selective-risk', 'deep-learning/machine-audio-alarm-project'),
    ('deep-learning/inference-schema-and-latency', 'deep-learning/machine-audio-alarm-project'),
    ('deep-learning/augmentation-leakage-boundary', 'deep-learning/video-clip-timestamps-and-grouped-evaluation'),
    ('deep-learning/causal-dilated-convolution-receptive-field', 'deep-learning/video-temporal-convolution-and-aggregation'),
    ('deep-learning/convolution-output-geometry-and-receptive-field', 'deep-learning/video-temporal-convolution-and-aggregation'),
    ('deep-learning/receipt-confidence-audit-project', 'deep-learning/conveyor-jam-video-project'),
    ('deep-learning/inference-schema-and-latency', 'deep-learning/conveyor-jam-video-project'),
    ('deep-learning/deep-learning-tutorial', 'deep-learning/conveyor-jam-video-project'),
]

if __name__ == '__main__':
    publish(LESSONS, (AUDIO, VIDEO), CROSSLINKS,
            'aitrove-deep-learning-audio-video-import-20261006.json',
            7940, subject='deep-learning')
