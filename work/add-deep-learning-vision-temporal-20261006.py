"""Add vision-token and causal-forecasting Deep Learning paths."""
from de_batch_publisher import publish

VISION = 'Vision tokens and resolution contracts'
TEMPORAL = 'Causal convolution and interval forecasts'
LESSONS = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    assert len(sections) == 5
    LESSONS.append(dict(path='deep-learning/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add('vision-transformer-patch-grid-and-token-contract',
    'Vision transformer patch grids and token contracts',
    'A vision transformer receives an ordered patch sequence; image padding, patch size and class-token position determine which visual evidence reaches attention.', [
    ('Compute the grid before the encoder', 'A 24-by-32 receipt with 8-by-8 nonoverlapping patches produces a 3-by-4 grid, or twelve image tokens. A separate class token raises the sequence length to thirteen. Record channel count, color normalization, resize policy, patch dimensions, grid order and any padded border. A crop whose size is not divisible by the patch size needs a declared pad or crop rule. The code computes exactly this miniature grid. [[deep-learning/convolution-output-geometry-and-receptive-field|Convolution geometry]] predicts the projection output.'),
    ('Treat position as part of the input contract', 'Self-attention alone cannot tell whether the same token content came from the top-left or bottom-right patch. Add a position representation after fixing row-major token order. If a class token is prepended, it needs its own position slot; reshaping it into the two-dimensional image grid is wrong. A token permutation with unchanged positions changes the image meaning. Tests should assert that flattening and unflattening preserve row and column identity.'),
    ('Inspect patch-size information loss', 'A tiny clipped edge can occupy less than one patch. Coarse patches reduce token count and attention cost but make it easier to lose boundary detail in the projection. Smaller patches increase the number of tokens approximately with inverse patch area and can raise attention-map memory quadratically in token count. Compare patch choices on the same physical-receipt holdout, including small defects and blur. [[deep-learning/receipt-defect-segmentation-project|Pixel masks]] require an additional dense-output design beyond one class token.'),
    ('Keep padding from becoming a cue', 'If only one defect class tends to use padded images, a classifier may learn border geometry instead of the defect. Record valid image area and use identical resizing rules across train and evaluation. For variable aspect ratios, test whether the model supports variable grids and whether padded patch tokens must be masked in attention. A standard fixed-grid encoder may simply expect one image size. Do not infer variable-size support from a successful tensor reshape.'),
    ('Compare with a cheaper reference', 'Run a convolutional classifier under the same split, preprocessing and compute budget. Report small-defect recall, false alerts, p95 preprocessing-plus-model latency and peak memory, not only aggregate accuracy. The patch sequence may be appropriate when broad context matters, but an image model earns its complexity through measured improvement. [[deep-learning/receipt-vision-transformer-project|The project]] tests that decision and preserves the token contract for serving.')],
    '''import torch
from torch import nn

receipt_images = torch.randn(2, 1, 24, 32)
patch_size = 8
patch_projection = nn.Conv2d(1, 16, kernel_size=patch_size,
                             stride=patch_size)
patch_grid = patch_projection(receipt_images)
assert patch_grid.shape == (2, 16, 3, 4)
image_tokens = patch_grid.flatten(2).transpose(1, 2)
class_token = nn.Parameter(torch.zeros(1, 1, 16))
position_vectors = nn.Parameter(torch.zeros(1, 13, 16))
tokens = torch.cat((class_token.expand(2, -1, -1), image_tokens), dim=1)
tokens = tokens + position_vectors
assert tokens.shape == (2, 13, 16)
assert image_tokens.size(1) == (24 // patch_size) * (32 // patch_size)''',
    'Patch projection is proportional to the image area and embedding width. For B images, N tokens and embedding width D, dense self-attention has approximately O(BN²D) arithmetic and O(BN²) attention-map storage per layer before implementation-specific optimizations. Halving both patch dimensions roughly quadruples N and can increase the attention map by about sixteenfold. The small example checks dimensions only; it does not train an attention model or establish accuracy. Measure memory at the intended resolution.',
    ['Do not forget the extra class-token position when checking sequence length.', 'Do not assume a patch boundary preserves a one-pixel defect.', 'Do not resize or pad different receipt classes with different rules.'],
    ['deep-learning/vision-position-grid-resizing-and-transfer', 'deep-learning/receipt-vision-transformer-project', 'deep-learning/scaled-dot-product-attention-mask-contract', 'deep-learning/convolution-output-geometry-and-receptive-field', 'deep-learning/receipt-defect-segmentation-project'], VISION)

add('vision-position-grid-resizing-and-transfer',
    'Vision position grids, resolution changes and transfer',
    'Changing a pretrained image grid changes its patch-token count; spatial position vectors need a two-dimensional resize while the class-token vector stays separate.', [
    ('Count old and new positions', 'A 3-by-4 patch grid has twelve image positions plus one class position. If image height doubles with width unchanged, the new grid is 6-by-4, giving twenty-four image positions plus one class position. Copying all thirteen old vectors into a twenty-five-token sequence fails by shape; blindly repeating vectors discards spatial meaning. Record the old and new grids, patch size, and position-embedding revision with the transferred model. [[deep-learning/vision-transformer-patch-grid-and-token-contract|The patch contract]] comes first.'),
    ('Interpolate only the spatial part', 'Remove the class-token vector, reshape the remaining positions into their old two-dimensional grid, resize that grid, flatten in the original row-major order, then prepend the untouched class vector. The example performs this with a 3-by-4 to 6-by-4 resize and asserts both the result length and exact class-vector preservation. Its vectors are illustrative; a pretrained model also needs compatible patch projection and encoder weights. A one-dimensional interpolation over flattened positions can blend the end of one row with the start of the next.'),
    ('Revisit the visual task after resizing', 'A higher input resolution changes more than positional vectors: an edge that occupied a fraction of one patch may now cross different tokens, and crop policy may expose another part of the receipt. Retrain or fine-tune under the new preprocessing and evaluate on a held-out physical-receipt set. Compare small defects, camera families and edge-of-frame cases. [[deep-learning/staged-unfreezing-and-domain-shift-audit|Staged unfreezing]] offers one controlled comparison; it is not a substitute for a new test.'),
    ('Check class-head compatibility', 'A transferred encoder may have an output head for different labels. Reset or replace that head if the receipt classes change, and record which parameters were initialized versus copied. Verify class ID order, image normalization and color-channel adaptation. The presence of a loaded state dictionary does not prove that every weight was compatible or that the new head was trained. Save a fixed-image embedding and logits before and after the resize operation to catch accidental shifts.'),
    ('Measure the new serving envelope', 'More patches raise attention cost and may invalidate a deployment latency or memory target. Compare the same batch, precision and device at the old and new image sizes, including decode and resize. If the high-resolution model misses the latency gate, test a smaller patch grid or a localized crop path before assuming an architectural win. [[deep-learning/receipt-vision-transformer-project|The project]] makes resolution and rollback part of the release decision.')],
    '''import torch
from torch.nn import functional as functional

old_rows, old_columns = 3, 4
new_rows, new_columns = 6, 4
embedding_width = 8
old_positions = torch.arange((1 + old_rows * old_columns) * embedding_width,
                             dtype=torch.float32).view(1, 13, embedding_width)
class_position = old_positions[:, :1, :]
image_positions = old_positions[:, 1:, :].transpose(1, 2)
image_grid = image_positions.reshape(1, embedding_width, old_rows, old_columns)
larger_grid = functional.interpolate(image_grid, size=(new_rows, new_columns),
                                     mode="bicubic", align_corners=False)
larger_positions = torch.cat((class_position,
                              larger_grid.flatten(2).transpose(1, 2)), dim=1)
assert larger_positions.shape == (1, 25, embedding_width)
torch.testing.assert_close(larger_positions[:, :1, :], class_position)''',
    'Resizing the position table costs O(ND) storage for N new patch positions and embedding width D, with interpolation work proportional to the new grid size. The dominant follow-on cost is the model: dense attention-map storage grows with the square of the new token count. A 3-by-4 to 6-by-4 grid changes image-token count from twelve to twenty-four, roughly quadrupling a dense image-token attention map before the class-token contribution. Validate exact shapes and run target-device memory and latency measurements.',
    ['Do not interpolate the class-token vector as though it were an image patch.', 'Do not flatten before spatial interpolation and blend unrelated row boundaries.', 'Do not compare resolutions under different cropping, class maps or test receipts.'],
    ['deep-learning/vision-transformer-patch-grid-and-token-contract', 'deep-learning/receipt-vision-transformer-project', 'deep-learning/frozen-features-versus-fine-tuning', 'deep-learning/staged-unfreezing-and-domain-shift-audit', 'deep-learning/inference-schema-and-latency'], VISION)

add('receipt-vision-transformer-project',
    'Project: compare receipt vision tokens with a convolutional baseline',
    'Train a small patch-token classifier for receipt-quality decisions, then test whether its added attention cost improves small-defect and device-shift outcomes.', [
    ('Fix the data and decision', 'Use a physical-receipt split with labels for usable image, clipped edge and severe fold. Keep crop, grayscale normalization and review policy identical for the token model and convolutional baseline. Define whether a receipt can carry more than one defect; the miniature code uses one mutually exclusive label per image. Save class IDs and the exact resized image dimensions. [[deep-learning/vision-transformer-patch-grid-and-token-contract|The patch lesson]] determines token count.'),
    ('Run a token wiring check', 'The code converts 24-by-32 images into twelve patches, prepends a class token, adds position vectors, applies one encoder layer and updates a three-class head. It checks that the token count and loss are finite. It is an architecture smoke test on random images, not evidence of field accuracy. Train the real candidate from a declared initialization with deterministic validation and compare accepted-example and compute budgets. [[deep-learning/logits-loss-gradient|Logit loss]] should receive raw class scores.'),
    ('Test resolution and transfer as separate changes', 'If using transferred weights at a different image size, resize only the spatial position grid and document head replacement. First compare architectures at one resolution. Then compare old and new resolutions for the selected architecture, holding splits and annotation rules fixed. This prevents a resolution improvement from being misreported as an attention improvement. [[deep-learning/vision-position-grid-resizing-and-transfer|The position lesson]] details this step.'),
    ('Look where the classifier fails', 'Report clipped-edge recall by edge width, false alerts on clean receipts, device-specific error, calibration and p95 end-to-end latency. Inspect border patches and occluded text. If a class token scores the image correctly but a safety-critical clipped edge is missed, a pixel-level model or targeted crop may be a better workflow. Keep examples of wrong predictions with image and label provenance rather than relying on a single aggregate score. [[deep-learning/receipt-defect-segmentation-project|Segmentation]] is a related alternative.'),
    ('Package a reversible release', 'Predeclare minimum small-defect recall, maximum false alerts, memory ceiling and p95 latency. Export patch size, image dimensions, normalization, position table, class map and model revision. Reload and compare logits on fixed images in a clean process. Keep the prior convolutional path if the token model misses any gate. A release report should state the measured advantage and its serving cost, not merely that a transformer was trained.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

torch.manual_seed(47)
receipt_images = torch.rand(3, 1, 24, 32)
quality_labels = torch.tensor([0, 2, 1], dtype=torch.long)
patch_projection = nn.Conv2d(1, 24, kernel_size=8, stride=8)
class_token = nn.Parameter(torch.zeros(1, 1, 24))
positions = nn.Parameter(torch.zeros(1, 13, 24))
encoder = nn.TransformerEncoderLayer(d_model=24, nhead=3,
                                     dim_feedforward=48, batch_first=True)
quality_head = nn.Linear(24, 3)
parameters = list(patch_projection.parameters()) + [class_token, positions]
parameters += list(encoder.parameters()) + list(quality_head.parameters())
optimizer = torch.optim.AdamW(parameters, lr=0.0007)
optimizer.zero_grad(set_to_none=True)
patch_tokens = patch_projection(receipt_images).flatten(2).transpose(1, 2)
all_tokens = torch.cat((class_token.expand(3, -1, -1), patch_tokens), dim=1)
assert all_tokens.shape == (3, 13, 24)
quality_logits = quality_head(encoder(all_tokens + positions)[:, 0])
loss = functional.cross_entropy(quality_logits, quality_labels)
loss.backward()
optimizer.step()
assert torch.isfinite(loss)''',
    'For N tokens, D embedding width and B images, a standard dense attention layer incurs approximately O(BN²D) arithmetic and O(BN²) attention-map storage, plus projection and feed-forward work. At production resolution N may be far larger than thirteen. The example allocates one tiny encoder layer and performs one update, so it tests wiring only. Compare wall time and peak memory including preprocessing against a convolutional model on the intended hardware and batch policy.',
    ['Do not label random-input smoke-test loss as model performance.', 'Do not credit architecture for a gain caused by a different image resolution.', 'Do not release without small-defect recall and full-pipeline latency checks.'],
    ['deep-learning/vision-transformer-patch-grid-and-token-contract', 'deep-learning/vision-position-grid-resizing-and-transfer', 'deep-learning/receipt-defect-segmentation-project', 'deep-learning/receipt-defect-localization-project', 'deep-learning/inference-schema-and-latency'], VISION, True)

add('causal-dilated-convolution-receptive-field',
    'Causal dilated convolution and receptive field',
    'A sequence convolution is causal only when its padding and indexing prevent future samples from influencing an earlier output.', [
    ('State the forecast clock', 'For a warehouse queue at minute 47, a forecast must use measurements observable at or before minute 47. A one-dimensional convolution with symmetric padding can place future values in the window around an output even if its output shape looks right. Use left padding of dilation times kernel-width-minus-one for stride-one causal convolution, then verify by perturbing a later input and checking every earlier output. The code does that directly. [[deep-learning/recurrent-hidden-state-reset-and-truncated-gradients|Recurrent state]] has a different but related time-boundary problem.'),
    ('Calculate the receptive field', 'For a chain of stride-one causal convolutions with kernel width k and dilation values d, the receptive-field length is one plus the sum of (k minus one) times each d. Three width-three layers with dilations one, two and four see fifteen time positions. A lookback shorter than this can leave much of the nominal receptive field filled with padding. Receptive field is a maximum context span, not evidence that every old measurement matters equally. Record all layer widths, dilations, strides and crop rules.'),
    ('Keep feature latency explicit', 'Event time and availability time differ. A database metric observed at 47 might not be available until 49. If the forecast runs at 47, including it violates the information boundary even though its event timestamp is not in the future. Build training windows from the as-available feature view, not a backfilled table. For missing minutes, choose a gap marker, forward-fill rule or explicit mask and apply it in serving. [[deep-learning/graph-neighbor-sampling-and-time-split|Time-safe graph splits]] rely on the same observable-at principle.'),
    ('Compare long context with a short baseline', 'Dilations expand coverage without proportionally expanding kernel parameters, but a long nominal lookback can still add compute and noise. Compare with last-value, seasonal and short-window models on identical rolling origins. Report errors by demand regime, missingness and holiday or incident periods. If the long-context model helps only on windows after a future-data backfill, the gain is suspect. [[deep-learning/warehouse-queue-tcn-project|The project]] uses a rolling release gate.'),
    ('Check deployment alignment', 'A causal model trained to output a value at every input time must select the final output for a next-horizon forecast and must shift labels consistently. An off-by-one label can yield attractive validation loss while serving a forecast for the already observed interval. Save an input window with timestamps, expected horizon and model output, and replay it after changes. Do not treat matching tensor lengths as proof of correct forecast alignment.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

torch.manual_seed(47)
queue_history = torch.arange(11, dtype=torch.float32).view(1, 1, 11)
causal_filter = nn.Conv1d(1, 1, kernel_size=3, dilation=2, bias=False)
left_padding = 2 * (3 - 1)
baseline = causal_filter(functional.pad(queue_history, (left_padding, 0)))
changed_future = queue_history.clone()
changed_future[:, :, -1] = 900
replayed = causal_filter(functional.pad(changed_future, (left_padding, 0)))
assert baseline.shape == queue_history.shape
torch.testing.assert_close(baseline[:, :, :-1], replayed[:, :, :-1])
assert 1 + (3 - 1) * sum((1, 2, 4)) == 15''',
    'For B windows, input channels C_in, output channels C_out, length T and kernel width k, a direct convolution is on the order of O(BTC_inC_outk) operations per layer; dilation changes spacing, not the number of kernel weights. Activations cost O(BTC_out) per layer in training, apart from backend buffers. Stacking layers increases the receptive field and stored activations. The test proves causal indexing for one convolution but does not measure forecast skill or data-availability leakage.',
    ['Do not use symmetric same-padding and assume it is causal.', 'Do not train on backfilled features unavailable at prediction time.', 'Do not confuse output alignment with the forecast horizon.'],
    ['deep-learning/quantile-forecast-loss-and-crossing-policy', 'deep-learning/warehouse-queue-tcn-project', 'deep-learning/recurrent-hidden-state-reset-and-truncated-gradients', 'deep-learning/causal-target-shift-and-padding-loss', 'deep-learning/inference-schema-and-latency'], TEMPORAL)

add('quantile-forecast-loss-and-crossing-policy',
    'Quantile forecast loss and crossing policy',
    'A probabilistic forecast needs a declared horizon, quantile order and calibration check; low point error alone cannot justify an uncertainty interval.', [
    ('Define the unit and horizon', 'A queue forecast might estimate completed orders thirty minutes ahead for each warehouse. Record whether the target is an integer count, rate or time-to-clear, and whether it covers a point at minute 77 or the sum over minutes 48 through 77. Those are different labels. Build features only from values available at issue time. A quantile model predicts conditional cutoffs, such as lower, median and upper outcomes, not three independent accuracy scores. [[deep-learning/causal-dilated-convolution-receptive-field|The causal lesson]] fixes the input clock.'),
    ('Use asymmetric pinball cost', 'At quantile q, underpredicting an observation by five contributes q times five; overpredicting by five contributes one-minus-q times five. Thus a lower quantile is punished less for being below the observation and more for being above it. The code checks both directions with fresh values rather than relying on a library helper. Aggregate the loss at matched horizons and nonmissing labels. Point forecast metrics can accompany it, but mean absolute error does not assess the promised interval.'),
    ('Prevent or audit crossing', 'Separately trained outputs can produce an estimated lower quantile above the upper quantile. Reject crossing predictions in a release audit, or parameterize ordered outputs with positive increments. Sorting after prediction may hide a modeling issue and can change which head receives training gradients. The project uses a median with positive distances to lower and upper bounds. This enforces order but not empirical coverage. [[deep-learning/warehouse-queue-tcn-project|The project]] audits both.'),
    ('Measure interval coverage and width together', 'For a proposed lower–upper interval, coverage is the fraction of realized demand values inside it; width measures how informative that interval is. A huge interval can attain high coverage without helping staffing. Evaluate coverage by warehouse, traffic regime and horizon on rolling held-out periods. An interval selected on the same final period used to report coverage leaks tuning into evaluation. Count missing labels and avoid reporting confidence from a tiny number of independent days.'),
    ('Make the decision cost visible', 'If staffing undercapacity is more costly than idle staff, an upper quantile may feed the decision rule, but the ratio of costs needs operational validation. Keep the forecast distribution and the staffing policy separate so either can be changed without mislabeling model accuracy. Report labor or service-level outcomes under replay with capacity constraints, rather than assuming a lower pinball loss guarantees a better operational decision. Retain a seasonal baseline for rollback.')],
    '''from math import isclose

def pinball(observed, predicted, quantile):
    if not 0 < quantile < 1:
        raise ValueError("quantile must be between zero and one")
    error = observed - predicted
    return max(quantile * error, (quantile - 1) * error)

observed_orders = 47
lower_estimate = 42
upper_estimate = 52
assert lower_estimate <= upper_estimate
assert isclose(pinball(observed_orders, lower_estimate, 0.2), 1.0)
assert isclose(pinball(observed_orders, upper_estimate, 0.8), 1.0)
observed_interval_hit = lower_estimate <= observed_orders <= upper_estimate
assert observed_interval_hit''',
    'The scalar pinball calculation is O(1); over N forecast rows and Q quantiles it costs O(NQ) time with streaming O(1) auxiliary space per row. Training cost is dominated by the forecasting network, while storing every horizon and quantile needs O(NHQ) output space for H horizons. Coverage estimates need enough independent issue times, not merely many overlapping windows from one day. The numeric check is illustrative and does not establish calibrated intervals.',
    ['Do not score a point target against an interval-sum forecast.', 'Do not claim calibration because lower and upper outputs are ordered.', 'Do not tune quantiles or interval width on the final reporting period.'],
    ['deep-learning/causal-dilated-convolution-receptive-field', 'deep-learning/warehouse-queue-tcn-project', 'deep-learning/temperature-scaling-and-selective-risk', 'deep-learning/early-stopping-best-state-and-seed-variance', 'deep-learning/inference-schema-and-latency'], TEMPORAL)

add('warehouse-queue-tcn-project',
    'Project: forecast warehouse queues with a causal temporal model',
    'Forecast next-window order volume with a causal dilated convolution, ordered quantiles and rolling-origin evaluation that respects feature availability.', [
    ('Build the observation ledger', 'For each warehouse and issue minute, retain event time, arrival time, queue size, worker capacity and future demand label. Split by time and warehouse identity according to the deployment question. Exclude late-arriving features from a forecast that would have run earlier. Compare against last-value and same-time-last-week baselines. Keep missing-interval and calendar rules fixed across train and test. [[deep-learning/causal-dilated-convolution-receptive-field|The causal lesson]] defines the receptive field and timestamp gate.'),
    ('Train one legal forward path', 'Use left padding before a dilated convolution so the final activation sees only the present and earlier measurements. The code accepts twelve observations, predicts one next-window outcome, and makes ordered lower, median and upper quantiles using positive distances. It runs a synthetic optimizer step to catch shape and gradient faults; it does not demonstrate forecast accuracy. Tune lookback, dilation and horizon on earlier validation periods only. [[deep-learning/quantile-forecast-loss-and-crossing-policy|The quantile lesson]] defines the loss.'),
    ('Backtest at rolling origins', 'Replay many issue times in order, building each feature window from the as-available view. Advance the origin only after predictions are stored; do not normalize using future rows. Report pinball loss by quantile and horizon, median absolute error, interval coverage and width, plus error around promotions and capacity shocks. Group uncertainty by day or warehouse rather than pretending overlapping windows are independent. Preserve forecast timestamps to investigate any too-good result.'),
    ('Evaluate the staffing decision', 'Feed frozen forecasts into a staffing rule with a declared overcapacity and undercapacity cost. Replay the decision under actual capacity limits and compare service-level breaches, idle hours and emergency shifts against the seasonal baseline. A model may reduce forecast loss but worsen a thresholded decision near a staffing boundary. Inspect intervals that crossed a schedule-change deadline too late to act. Keep human override and a low-information fallback when inputs are delayed.'),
    ('Release and monitor', 'Predeclare acceptable interval coverage, width, service-level outcome and p95 scoring latency. Package feature arrival policy, normalization statistics, model weights, quantile order, horizon and calendar version. Re-run fixed windows in a clean process; alarm on missing telemetry, shifted arrival delays and rising interval misses. If the model fails the gate, route to the baseline rather than quietly widening intervals. The deliverable is a reproducible backtest and operational replay.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

torch.manual_seed(47)
queue_windows = torch.rand(4, 2, 12)
next_window_orders = torch.tensor([43.0, 51.0, 62.0, 47.0])
forecast_net = nn.Sequential(nn.ConstantPad1d((4, 0)),
                             nn.Conv1d(2, 8, kernel_size=3, dilation=2),
                             nn.ReLU(), nn.Conv1d(8, 3, kernel_size=1))
optimizer = torch.optim.AdamW(forecast_net.parameters(), lr=0.0007)
optimizer.zero_grad(set_to_none=True)
raw = forecast_net(queue_windows)[:, :, -1]
median = raw[:, 0]
lower = median - functional.softplus(raw[:, 1])
upper = median + functional.softplus(raw[:, 2])
ordered = torch.stack((lower, median, upper), dim=1)
assert ordered.shape == (4, 3)
assert torch.all(ordered[:, 0] <= ordered[:, 1])
assert torch.all(ordered[:, 1] <= ordered[:, 2])
quantiles = torch.tensor([0.2, 0.5, 0.8])
errors = next_window_orders[:, None] - ordered
loss = torch.maximum(quantiles * errors, (quantiles - 1) * errors).mean()
loss.backward()
optimizer.step()
assert torch.isfinite(loss)''',
    'For B windows of length T, a small width-k causal convolution costs roughly O(BTC_inC_outk), plus its activation memory and the final quantile head. The project also pays for as-available feature retrieval and rolling replay, which can dominate model inference in a warehouse system. Three quantiles require O(BQ) output values for Q quantiles; long horizons multiply that storage. The synthetic batch validates shapes and ordered outputs, not calibration or staffing value. Benchmark the full issue-time path.',
    ['Do not let a centered or late-arriving feature into an issue-time window.', 'Do not report interval coverage without its width and sample count.', 'Do not claim an ordered synthetic output is a calibrated forecast.'],
    ['deep-learning/causal-dilated-convolution-receptive-field', 'deep-learning/quantile-forecast-loss-and-crossing-policy', 'deep-learning/service-event-lstm-project', 'deep-learning/early-stopping-best-state-and-seed-variance', 'deep-learning/inference-schema-and-latency'], TEMPORAL, True)

CROSSLINKS = [
    ('deep-learning/scaled-dot-product-attention-mask-contract', 'deep-learning/vision-transformer-patch-grid-and-token-contract'),
    ('deep-learning/convolution-output-geometry-and-receptive-field', 'deep-learning/vision-transformer-patch-grid-and-token-contract'),
    ('deep-learning/frozen-features-versus-fine-tuning', 'deep-learning/vision-position-grid-resizing-and-transfer'),
    ('deep-learning/receipt-defect-localization-project', 'deep-learning/receipt-vision-transformer-project'),
    ('deep-learning/receipt-defect-segmentation-project', 'deep-learning/receipt-vision-transformer-project'),
    ('deep-learning/recurrent-hidden-state-reset-and-truncated-gradients', 'deep-learning/causal-dilated-convolution-receptive-field'),
    ('deep-learning/causal-target-shift-and-padding-loss', 'deep-learning/causal-dilated-convolution-receptive-field'),
    ('deep-learning/temperature-scaling-and-selective-risk', 'deep-learning/quantile-forecast-loss-and-crossing-policy'),
    ('deep-learning/service-event-lstm-project', 'deep-learning/warehouse-queue-tcn-project'),
    ('deep-learning/inference-schema-and-latency', 'deep-learning/warehouse-queue-tcn-project'),
    ('deep-learning/deep-learning-tutorial', 'deep-learning/receipt-vision-transformer-project'),
]

if __name__ == '__main__':
    publish(LESSONS, (VISION, TEMPORAL), CROSSLINKS,
            'aitrove-deep-learning-vision-temporal-import-20261006.json',
            7920, subject='deep-learning')
