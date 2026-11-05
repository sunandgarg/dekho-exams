"""Add original Computer Vision and Streaming Analytics paths to AI Trove preview."""
import datetime
import html
import json
from pathlib import Path
import re
import uuid

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
rows = [row for row in rows if not row['path'].startswith(('computer-vision/', 'streaming-analytics/'))]
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
lessons = []

def add(path, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path=path, title=title, summary=summary, sections=sections,
                        code=code, cost=cost, mistakes=mistakes, related=related))

add('computer-vision/image-unit-label-and-consent',
    'Vision dataset contract: image unit, label definition and consent',
    'A vision task begins by defining what one image represents, what a label means and whether that image may be retained for the task.', [
    ('Name the operational decision', 'A receipt-quality classifier could flag images that require manual recapture because text is unreadable. That is different from predicting fraud or extracting line items. Define the capture channel, image format, label unit and action before collecting examples. A multi-page receipt may be one submission with several images; splitting pages across train and test would leak the same submission. [[data-science/dataset-grain-and-join-cardinality|Dataset grain]] must match the decision.'),
    ('Write a label rubric', '“Unreadable” needs observable criteria: perhaps the merchant and total cannot both be verified by a trained reviewer at normal zoom. Borderline glare, partial crops and unfamiliar scripts need examples in the rubric. Record an uncertainty or adjudication state instead of forcing every case into a confident binary label. [[computer-vision/annotation-geometry-and-quality|Annotation quality]] is measurable only after the rubric is stable.'),
    ('Constrain image use', 'A receipt image can contain names, addresses and payment fragments. Store the minimum necessary image and metadata, define access and retention, and prevent a training export from bypassing deletion requests. A person’s consent to process a receipt for reimbursement does not automatically authorize every unrelated model experiment. Keep raw-image and derived-feature lifecycles linked.'),
    ('Test the manifest', 'Create two images from one receipt, one blurred image and one image whose label is unknown. Verify that the two pages share a submission group, the unknown label does not become a negative, and deleted images cannot reappear through a cached training set. Count eligible submissions as well as image files.')],
    'def validate_image_record(record):\n    required = {"image_id", "submission_id", "capture_time", "consent_scope", "label"}\n    if required - record.keys():\n        raise ValueError("missing image fields")\n    if record["label"] not in {"readable", "unreadable", "uncertain"}:\n        raise ValueError("unknown label state")\n    if "receipt_quality" not in record["consent_scope"]:\n        raise ValueError("image is outside consent scope")\n    return record["submission_id"]',
    'Validation is O(1) per record and O(N) over N images; retaining group IDs for a split costs O(G) memory for G submissions. Image storage and annotation review dominate the arithmetic cost, so record licensing, retention and label decisions before scaling capture.',
    ['Do not mix pages from one submission across evaluation partitions.', 'Do not convert an uncertain label into a negative.', 'Do not assume operational upload consent covers unrelated training.'],
    ['computer-vision/annotation-geometry-and-quality','computer-vision/grouped-evaluation-and-shift','data-science/dataset-grain-and-join-cardinality','mlops/inference-logging-privacy'])

add('computer-vision/pixel-geometry-and-preprocessing',
    'Pixel geometry and preprocessing: preserve the mapping back to the original image',
    'Image preprocessing changes dimensions, color values and coordinates; the model contract must record each transformation.', [
    ('Declare the coordinate frame', 'A detector may output boxes on a resized 320-by-320 tensor while reviewers inspect a 1280-by-960 original. A direct overlay without inverse scaling puts boxes in the wrong place. Record original width and height, crop offsets, resize scale and any padding. [[computer-vision/annotation-geometry-and-quality|Box annotations]] need one coordinate convention such as half-open x-min, y-min, x-max, y-max.'),
    ('Handle aspect ratio', 'Stretching a long receipt into a square changes character shapes; padding preserves aspect ratio but changes the box origin. Compare the effect on the task and reproduce exactly the same policy at serving time. A crop may remove the merchant or total even when the remaining pixels look sharp. Keep an uncropped inspection view for difficult cases.'),
    ('Make color explicit', 'A three-channel array may mean RGB or BGR depending on the decoder. Normalization can use byte values or scaled floats; silently applying it twice shifts the input distribution. Store channel order, value range and image orientation handling in the model manifest. [[mlops/feature-training-serving-parity|Training-serving parity]] applies to pixels as well as tabular features.'),
    ('Use a geometry fixture', 'Take an original image 1280 pixels wide and resize it to 320 without padding. A box whose original horizontal coordinates are 160 and 480 maps to 40 and 120. Reverse the transform and confirm the original coordinates return. Test a padded portrait image separately; one scale factor is insufficient without the padding offset.')],
    'def scale_box_xyxy(box, source_size, target_size):\n    source_width, source_height = source_size\n    target_width, target_height = target_size\n    if min(source_width, source_height, target_width, target_height) <= 0:\n        raise ValueError("image dimensions must be positive")\n    x_min, y_min, x_max, y_max = box\n    if not 0 <= x_min < x_max <= source_width or not 0 <= y_min < y_max <= source_height:\n        raise ValueError("box lies outside source image")\n    return (x_min * target_width / source_width, y_min * target_height / source_height,\n            x_max * target_width / source_width, y_max * target_height / source_height)',
    'Coordinate conversion is O(1) per box; resizing an image is O(P) in pixel count P, with a new tensor often requiring O(P) memory. Retain transform metadata so annotation overlays and error reviews do not require guessing how pixels moved.',
    ['Do not overlay resized coordinates on an unscaled original.', 'Do not assume RGB when the decoder returns another order.', 'Do not stretch receipts without checking task-relevant distortion.'],
    ['computer-vision/annotation-geometry-and-quality','computer-vision/augmentation-and-serving-parity','mlops/feature-training-serving-parity','data-visualization/scale-baseline-and-axis-integrity'])

add('computer-vision/annotation-geometry-and-quality',
    'Vision annotations: validate boxes, masks and reviewer agreement',
    'A box marks a rectangular extent; a mask labels pixels, and each task needs a consistent annotation policy.', [
    ('Choose the representation', 'For unreadable receipt detection, an image-level label may be enough. Localizing glare or a cropped total needs boxes or masks, which cost more to produce and review. Do not request pixel masks when the downstream decision only needs an image-level flag. State whether coordinates are absolute pixels or normalized fractions and whether right and bottom edges are included.'),
    ('Validate geometry', 'A box must have positive area and lie inside the declared image bounds. A mask must match the image dimensions after any resize. If an image rotates due to orientation metadata, rotate its annotations too. [[computer-vision/pixel-geometry-and-preprocessing|Preprocessing metadata]] should make that transform reversible for review.'),
    ('Measure label variation', 'Two reviewers can disagree on the border of a glare patch even if both agree the receipt needs recapture. Preserve both labels on a sample and adjudicate according to a versioned rubric. Report disagreement by capture channel, script and image quality. A large dataset with inconsistent borders can teach a detector contradictory geometry.'),
    ('Build a failure fixture', 'Use a 640-by-480 image with a valid box from x 120 to 300 and y 40 to 190. Reject an inverted box, one that extends beyond the image and one with zero area. Then change image orientation and confirm that the displayed overlay still encloses the intended region.')],
    'def validate_box(box, image_width, image_height):\n    x_min, y_min, x_max, y_max = box\n    if image_width <= 0 or image_height <= 0:\n        raise ValueError("invalid image size")\n    if not (0 <= x_min < x_max <= image_width and 0 <= y_min < y_max <= image_height):\n        raise ValueError("invalid bounding box")\n    return (x_max - x_min) * (y_max - y_min)',
    'Validating B boxes costs O(B) time and O(1) extra space per image. Dense masks consume O(P) storage per image before compression, where P is pixel count; choose their fidelity only when the decision benefits from it.',
    ['Do not mix normalized and pixel coordinates in one field.', 'Do not rotate an image without rotating its labels.', 'Do not interpret a reviewer disagreement as model error before adjudication.'],
    ['computer-vision/pixel-geometry-and-preprocessing','computer-vision/grouped-evaluation-and-shift','computer-vision/detection-metrics-and-thresholds','applied-statistics/population-estimand-and-sampling-frame'])

add('computer-vision/grouped-evaluation-and-shift',
    'Vision evaluation splits: group captures and test acquisition shift',
    'A random image split can overstate generalization when the same receipt, device or capture session appears on both sides.', [
    ('Group near duplicates', 'A user may upload several crops of one receipt. Those images share text, lighting and device artifacts, so treat the submission as one split unit. Hashes can find exact duplicates, but near-duplicate review still needs a policy. [[machine-learning/group-and-time-validation|Group validation]] prevents a model from memorizing the same physical document in train and test.'),
    ('Add a temporal holdout', 'Camera software, compression and receipt layouts change. Keep a later capture period untouched while choosing the model, then report performance on it. A model that works on old scanner images may fail on dim mobile photos. Show results by device family, channel, language and document type, with counts and intervals where sample size allows.'),
    ('Separate label leakage', 'Filenames, upload paths or processing flags can encode the reviewer’s decision. Strip such metadata from model inputs and verify that a baseline trained on filenames alone cannot predict the label. Apply preprocessing fit only to training data, and use the exact same decoder and resize policy in validation. [[computer-vision/augmentation-and-serving-parity|Augmentation]] belongs only to training.'),
    ('Inspect a split fixture', 'Create three submissions with two images each. All images from one submission must share a partition. Add a later fourth submission captured by a new device and reserve it for a shift test. Report both image count and submission count; a six-image test set with only three independent receipts is not six independent examples.')],
    'def group_partition(image_records, test_submission_ids):\n    test_ids = set(test_submission_ids)\n    training = []\n    testing = []\n    for record in image_records:\n        destination = testing if record["submission_id"] in test_ids else training\n        destination.append(record["image_id"])\n    return training, testing',
    'Assigning N images to partitions costs O(N + G) expected time and O(N + G) space for G selected groups. Per-device and temporal slices reduce effective sample sizes; report uncertainty rather than treating every crop as independent evidence.',
    ['Do not split near-identical captures across training and evaluation.', 'Do not allow label-bearing filenames into model features.', 'Do not report only an overall score when acquisition channels differ.'],
    ['computer-vision/image-unit-label-and-consent','computer-vision/augmentation-and-serving-parity','computer-vision/detection-metrics-and-thresholds','machine-learning/group-and-time-validation'])

add('computer-vision/augmentation-and-serving-parity',
    'Vision augmentation: preserve labels and match serving transforms',
    'Augmentation changes training inputs to represent plausible capture variation, but it must not alter the task label by accident.', [
    ('Choose plausible variation', 'Mild rotation, exposure change or compression can resemble receipt capture conditions. A horizontal flip makes most receipt text unnatural and can invalidate text-location labels. Start with errors observed in the held-out capture channels, not an arbitrary list of transforms. Keep original and transformed images linked so failure analysis can identify harmful augmentation.'),
    ('Transform targets together', 'If a crop moves a glare region, its box or mask must move with it. If a crop removes the labeled region entirely, the resulting label needs a defined rule. Reject boxes that become zero area. [[computer-vision/annotation-geometry-and-quality|Geometry validation]] should run after each transform during development.'),
    ('Keep validation clean', 'Do not add random training augmentation to validation or final test images. Serving must use deterministic decode, orientation, resize and normalization steps. A different channel order or resize interpolation at serving time can erase training gains. [[mlops/feature-training-serving-parity|Parity checks]] should compare sampled tensors from both paths on identical raw files.'),
    ('Test one transform', 'Rotate or crop a synthetic image with a known box, then check the transformed coordinates and inverse mapping. Use a receipt whose total is near the edge to catch a crop that silently removes the deciding text. Also test an unmodified image: a supposedly harmless augmentation pipeline should not change its label or size unexpectedly.')],
    'def translate_box(box, x_offset, y_offset, crop_width, crop_height):\n    x_min, y_min, x_max, y_max = box\n    shifted = (max(0, x_min - x_offset), max(0, y_min - y_offset),\n               min(crop_width, x_max - x_offset), min(crop_height, y_max - y_offset))\n    if shifted[0] >= shifted[2] or shifted[1] >= shifted[3]:\n        return None\n    return shifted',
    'A box transform is O(1); pixel augmentation is O(P) per image and can multiply training I/O if variants are materialized. Generate variants during training when practical, and record random seeds plus transform versions for reproducible review.',
    ['Do not flip text images just because the library supports it.', 'Do not transform an image without its boxes or masks.', 'Do not apply random augmentation to the final test partition.'],
    ['computer-vision/pixel-geometry-and-preprocessing','computer-vision/grouped-evaluation-and-shift','computer-vision/receipt-quality-project','mlops/feature-training-serving-parity'])

add('computer-vision/detection-metrics-and-thresholds',
    'Vision decision metrics: separate localization, class errors and abstention',
    'Vision evaluation depends on the task: image classification, object localization and segmentation count different errors.', [
    ('Match metric to action', 'A receipt recapture gate needs false-negative and false-positive rates at a chosen threshold, because missed unreadable images delay review while unnecessary recaptures frustrate users. A detector that marks glare boxes also needs a localization match rule, such as intersection over union, before precision or recall is counted. [[machine-learning/decision-threshold-and-cost|Decision cost]] should set the operating point.'),
    ('Define a box match', 'Intersection over union is overlap area divided by union area. State the coordinate convention and threshold; a prediction can have the right class but miss the affected region. Match predictions to ground truth one-to-one so duplicate boxes do not earn duplicate true positives. An empty prediction set or an image with no target boxes needs an explicit scoring policy.'),
    ('Slice the errors', 'Report results by device, lighting, script and receipt format, not only one aggregate. Sparse slices need counts and intervals. A system that performs well on bright English receipts can fail on darker captures while the overall score barely moves. [[computer-vision/grouped-evaluation-and-shift|Acquisition shift]] is a deployment risk, not merely a test-set detail.'),
    ('Use a geometry fixture', 'Two 20-by-20 boxes overlapping over a 10-by-20 region have intersection area 200 and union 600, so IoU is one third. Verify that disjoint boxes return zero. Then apply the recapture threshold to image-level probabilities separately; an IoU cutoff and a class-probability cutoff do different jobs.')],
    'def box_iou(first, second):\n    left = max(first[0], second[0])\n    top = max(first[1], second[1])\n    right = min(first[2], second[2])\n    bottom = min(first[3], second[3])\n    intersection = max(0, right - left) * max(0, bottom - top)\n    first_area = (first[2] - first[0]) * (first[3] - first[1])\n    second_area = (second[2] - second[0]) * (second[3] - second[1])\n    if first_area <= 0 or second_area <= 0:\n        raise ValueError("boxes need positive area")\n    return intersection / (first_area + second_area - intersection)',
    'One IoU calculation is O(1); comparing P predicted boxes with G ground-truth boxes naively costs O(PG) per image. One-to-one matching and per-slice metrics add work, but prevent a high aggregate score from concealing duplicate detections or capture-channel failures.',
    ['Do not use image classification accuracy to claim good box localization.', 'Do not count duplicate detections as multiple true positives.', 'Do not choose the decision threshold on the final holdout.'],
    ['computer-vision/annotation-geometry-and-quality','computer-vision/receipt-quality-project','machine-learning/decision-threshold-and-cost','data-visualization/uncertainty-and-small-sample-display'])

add('computer-vision/receipt-quality-project',
    'Project: audit a receipt-image recapture gate',
    'Build a checked receipt-quality pipeline that can flag unreadable captures while preserving data, label and serving boundaries.', [
    ('Prepare the evidence', 'Create a synthetic image manifest with submission groups, device channel, capture time, consent scope and readable, unreadable or uncertain labels. Include two crops of one receipt, a withdrawn image and a later device type. State exactly when a user is asked to recapture. [[computer-vision/image-unit-label-and-consent|The task contract]] must precede model choice.'),
    ('Implement the path', 'Validate image size and orientation, apply deterministic preprocessing, and store reversible geometry for any box overlay. Partition by submission, then use training-only augmentation that preserves labels. A simple baseline is acceptable; the project is judged on data and decision integrity rather than model complexity. [[computer-vision/grouped-evaluation-and-shift|The later device]] stays untouched for a shift check.'),
    ('Measure failures', 'Report confusion counts and the threshold cost of missed unreadable images versus unnecessary recaptures. If localization is attempted, show one-to-one box matching and IoU. Slice results by device and glare condition with denominators. An uncertain label should be adjudicated or excluded under a declared rule, never silently treated as readable.'),
    ('Submit a release packet', 'Provide the synthetic fixture, label rubric, preprocessing manifest, split IDs, exact metric calculation, representative false positives and negatives, and rollback decision. Assert that the withdrawn image is absent from training and serving caches. Include a privacy deletion test and one manual-review route for low-confidence cases.')],
    'def recapture_decision(unreadable_probability, threshold=0.63):\n    if not 0 <= unreadable_probability <= 1 or not 0 < threshold < 1:\n        raise ValueError("invalid probability or threshold")\n    return "request_recapture" if unreadable_probability >= threshold else "continue_review"\n\nassert recapture_decision(0.71) == "request_recapture"',
    'A threshold decision is O(1) after inference; image decoding and model inference dominate latency and memory. The release packet must measure those costs on the intended device and image-size distribution before this synthetic fixture becomes an operational path.',
    ['Do not split crops of one receipt across train and test.', 'Do not retain withdrawn images in an augmentation cache.', 'Do not ship an accuracy figure without threshold-specific error counts.'],
    ['computer-vision/image-unit-label-and-consent','computer-vision/augmentation-and-serving-parity','computer-vision/detection-metrics-and-thresholds','mlops/shadow-canary-and-rollback'])

add('streaming-analytics/event-contract-and-partition-key',
    'Stream event contract: identity, version and partition key',
    'A stream is an ordered sequence within declared partitions, not a globally ordered table of facts.', [
    ('Define one event', 'A receipt-submitted event needs event ID, receipt ID, occurrence time, ingestion time, schema version and producer identity. A retry must retain the same event ID if it represents the same fact. Distinguish an update from a new submission with an event type and version. [[data-engineering/source-contract-and-raw-landing|Dataset contracts]] begin at producers, before a consumer tries to infer missing fields.'),
    ('Choose the partition key', 'Partitioning by receipt ID keeps events for one receipt in order on a single partition, while events for different receipts can interleave. A hot key can overload a partition, so measure key distribution. Do not assume total ordering across partitions. A consumer that needs per-customer state must choose a compatible key or deliberately repartition.'),
    ('Plan schema change', 'Additive fields with defaults can be easier to roll out than changing the meaning of an existing field. Consumers should reject unknown required versions into a quarantine path rather than guessing. Store raw event bytes or a reproducible decoder version for replay. A published contract should say which fields may be absent and how deletion events are represented.'),
    ('Exercise a retry', 'Send the same receipt-submitted event twice with identical event ID; the downstream count should increase once. Send a correction with a new event ID and explicit superseded version; it should update the state under a declared rule. Add an event with no receipt ID and confirm it is rejected before partitioning.')],
    'def validate_receipt_event(event):\n    required = {"event_id", "receipt_id", "occurred_at", "ingested_at", "schema_version"}\n    if required - event.keys() or not event["event_id"] or not event["receipt_id"]:\n        raise ValueError("missing stream identity")\n    if event["schema_version"] not in {2, 3}:\n        raise ValueError("unsupported event schema")\n    return event["receipt_id"]',
    'Validation is O(1) per event and O(N) for N events. Partition-key skew can dominate end-to-end latency even when total throughput looks healthy; publish per-partition lag and key-distribution diagnostics.',
    ['Do not assign a new event ID to a retry of the same fact.', 'Do not assume one global order across partitions.', 'Do not silently reinterpret a field under the same schema version.'],
    ['streaming-analytics/event-time-window-and-boundaries','streaming-analytics/idempotent-sink-and-replay','data-engineering/backfill-publication-boundary','time-series/observation-calendar-and-missing-periods'])

add('streaming-analytics/event-time-window-and-boundaries',
    'Event-time windows: place each event by occurrence, not arrival',
    'A streaming window groups an unbounded event sequence into finite intervals under a stated clock and boundary convention.', [
    ('Separate clocks', 'A receipt may be submitted at 09:59 but delivered to analytics at 10:04 after a network retry. An event-time 09:00–10:00 window counts it in the earlier hour; a processing-time window counts it in the later one. Choose based on the business question and keep both timestamps. [[time-series/observation-calendar-and-missing-periods|Calendar policy]] determines time zone and reporting cutoff.'),
    ('Declare the window', 'A tumbling one-hour window gives each event one interval. A sliding one-hour window advancing every ten minutes can count an event in several windows; those overlapping counts cannot be summed into an overall total. Use half-open intervals so an event exactly at 10:00 belongs to 10:00–11:00, not both hours.'),
    ('Keep identity and denominator', 'If a receipt emits submitted and corrected events, counting both as submissions inflates volume. Filter event types and deduplicate business facts before aggregation. For a completion-rate stream, numerator and denominator may arrive on different schedules; publish provisional rates or delay publication until both are sufficiently complete. [[data-visualization/aggregation-grain-and-denominator|Metric grain]] remains important in streaming.'),
    ('Test boundaries', 'With a 60-minute tumbling window, events at minutes 59, 60 and 119 map to windows starting at 0, 60 and 60. Test a negative timestamp if the chosen epoch representation permits it; integer division should still place it consistently. Then deliver minute 59 after minute 60 and verify event time, not arrival order, controls membership.')],
    'def tumbling_window_start(event_minute, window_minutes=60):\n    if window_minutes < 1:\n        raise ValueError("window length must be positive")\n    return (event_minute // window_minutes) * window_minutes\n\nassert [tumbling_window_start(minute) for minute in (59, 60, 119)] == [0, 60, 60]',
    'Window assignment is O(1) per event. Maintaining W active keyed windows needs O(W) state; overlapping sliding windows can multiply state and update work, so define the analysis need before choosing a shorter slide.',
    ['Do not mix event time and arrival time in one metric without a label.', 'Do not sum overlapping sliding-window counts as a unique total.', 'Do not count a correction event as a new submission by default.'],
    ['streaming-analytics/watermark-late-data-and-revisions','streaming-analytics/state-retention-and-stream-joins','time-series/observation-calendar-and-missing-periods','data-visualization/aggregation-grain-and-denominator'])

add('streaming-analytics/watermark-late-data-and-revisions',
    'Watermarks and late events: define when a window becomes final',
    'A watermark is a progress estimate for event time; it trades waiting for late data against timely output and bounded state.', [
    ('Choose a delay budget', 'If most receipt events arrive within four minutes but mobile uploads can take longer, a four-minute lateness budget produces timely numbers with a known late-event tail. Measure the observed delay distribution before setting it. The watermark does not guarantee no older event will ever arrive. [[streaming-analytics/event-time-window-and-boundaries|Window boundaries]] determine which aggregate a late event would change.'),
    ('Decide the late path', 'A late event can be dropped with a count, routed to a correction stream, or allowed to revise a previously emitted window while state remains. Each choice changes the consumer contract. A dashboard should label provisional versus final values and version corrections. [[data-engineering/backfill-publication-boundary|Atomic publication]] can prevent readers from mixing old and new window versions.'),
    ('Handle idle partitions', 'A slow or idle input partition can hold back a combined watermark even when other partitions are current. Track per-partition progress and define idleness carefully; marking an active but delayed partition idle can make its events unexpectedly late. A single global “lag” number can hide this state.'),
    ('Rehearse a late record', 'Emit a 09:58 receipt before the 10:00 hourly window is finalized, then replay the same event after the chosen lateness boundary. The first should update the provisional aggregate; the second should take the declared late path rather than silently changing a final number. Check duplicate IDs in both paths.')],
    'def lateness_route(event_minute, window_end_minute, watermark_minute, grace_minutes):\n    if grace_minutes < 0 or window_end_minute <= event_minute:\n        raise ValueError("invalid window or grace period")\n    if watermark_minute < window_end_minute:\n        return "provisional_window"\n    if watermark_minute < window_end_minute + grace_minutes:\n        return "revision_window"\n    return "late_correction_queue"',
    'Routing is O(1) per event; holding state for more grace time increases memory roughly with active keys times retained windows. Measure late-event frequency and correction cost rather than picking a watermark delay only from desired dashboard speed.',
    ['Do not treat a watermark as proof that older events cannot arrive.', 'Do not revise a final metric without a versioned correction contract.', 'Do not ignore idle or slow partitions when diagnosing watermark lag.'],
    ['streaming-analytics/event-time-window-and-boundaries','streaming-analytics/idempotent-sink-and-replay','streaming-analytics/monitoring-lag-and-batch-parity','data-engineering/backfill-publication-boundary'])

add('streaming-analytics/idempotent-sink-and-replay',
    'Idempotent streaming sinks: make retries safe across failures',
    'A consumer can see an event again after a crash or replay; its externally visible effect needs a stable identity and commit rule.', [
    ('Locate the failure gap', 'If a consumer writes an hourly count and crashes before committing its input position, it will process the same event again. At-least-once delivery is often workable when the sink deduplicates by event ID or writes a versioned aggregate idempotently. A producer-side duplicate guarantee does not automatically cover a nontransactional downstream database. [[streaming-analytics/event-contract-and-partition-key|Event identity]] is the key.'),
    ('Choose the sink operation', 'A blind increment is unsafe on replay. An upsert keyed by window, metric and version can replace the same result, while an event ledger with a unique event ID can guard incremental updates in one transaction. Document how corrections supersede previous values and how a deleted receipt is reversed. Avoid claiming end-to-end exactly-once behavior without checking every boundary.'),
    ('Keep replay deterministic', 'A replay needs the same schema decoder, event selection rule and aggregation version as the original run, or a deliberate migration. Store input offsets and code version with checkpoints. [[data-engineering/backfill-publication-boundary|Backfill publication]] can rebuild into a separate snapshot and switch readers once counts reconcile.'),
    ('Test a crash', 'Process a three-event fixture, crash after writing the second result but before recording progress, then replay from the previous checkpoint. The final count must match a clean run. Add a correction and verify it changes the intended window once, including after a second replay. Compare both event ledger and visible aggregate.')],
    'def apply_once(event, seen_event_ids, counts_by_window):\n    event_id = event["event_id"]\n    if event_id in seen_event_ids:\n        return False\n    window_key = event["window_key"]\n    seen_event_ids.add(event_id)\n    counts_by_window[window_key] = counts_by_window.get(window_key, 0) + 1\n    return True',
    'A hash-set check is O(1) expected per event but an unbounded set uses O(N) memory. Production deduplication needs a durable bounded identity store or a sink transaction; the in-memory fixture demonstrates semantics, not crash durability.',
    ['Do not use blind increments with replayable input.', 'Do not equate producer idempotence with an end-to-end sink guarantee.', 'Do not discard replay metadata before the retention window ends.'],
    ['streaming-analytics/event-contract-and-partition-key','streaming-analytics/state-retention-and-stream-joins','streaming-analytics/receipt-event-pipeline-project','data-engineering/backfill-publication-boundary'])

add('streaming-analytics/state-retention-and-stream-joins',
    'Stateful stream joins: bound waiting time and unmatched records',
    'A stream join keeps state while waiting for related events, so its key, time bounds and expiry behavior are part of correctness.', [
    ('Choose the join identity', 'Receipt-submitted and receipt-reviewed events should join by receipt ID. If two review events arrive, define whether the latest version supersedes the first or both represent separate actions. A consumer that joins on customer ID can accidentally match a review to a different receipt. [[data-science/dataset-grain-and-join-cardinality|Join cardinality]] must be stated before streaming state is built.'),
    ('Bound the waiting period', 'A review can occur hours after submission. Keep the submission state long enough for normal cases, then route unmatched reviews and expired submissions to separate outputs. Never hold every unmatched key forever; memory grows with unclosed cases. A tight timeout saves memory but can drop valid slow reviews, so measure the delay distribution and document late corrections.'),
    ('Mind event ordering', 'The review event may arrive before the submission event even if it occurred later. A processing-order join that discards unmatched reviews will lose it. Event-time ordering and a bounded buffer can help, but the watermark and grace policy still govern when the pair is final. [[streaming-analytics/watermark-late-data-and-revisions|Late routing]] must include both sides of the join.'),
    ('Exercise state transitions', 'Send review before submission for receipt R47, then complete the pair. Send a submission that never gets a review and confirm it expires into a pending output. Send duplicate review IDs and verify no extra pair appears. A backfill replay should produce the same matched, pending and correction totals.')],
    'def pair_receipt_events(submissions, reviews):\n    matches = []\n    for receipt_id, submission in submissions.items():\n        review = reviews.get(receipt_id)\n        if review is not None:\n            matches.append((receipt_id, submission, review))\n    return matches',
    'A batch-style fixture scan is O(S) expected time and O(M) output space for S submissions and M matches. A live join also keeps O(U) state for U unmatched IDs and must expire it under a measured lateness policy.',
    ['Do not join on a broader key than the business unit.', 'Do not hold unmatched state indefinitely.', 'Do not assume arrival order matches occurrence order.'],
    ['streaming-analytics/event-time-window-and-boundaries','streaming-analytics/watermark-late-data-and-revisions','streaming-analytics/monitoring-lag-and-batch-parity','data-science/dataset-grain-and-join-cardinality'])

add('streaming-analytics/monitoring-lag-and-batch-parity',
    'Streaming operations: monitor lag, corrections and batch parity',
    'A low-latency aggregate is useful only when freshness, completeness and replay behavior are visible to its consumers.', [
    ('Separate lag measures', 'Producer-to-broker delay, consumer backlog, event-time watermark lag and dashboard publication delay are different. Report each with per-partition slices. A low processing latency can coexist with stale data if an upstream partition stops sending. [[streaming-analytics/watermark-late-data-and-revisions|Watermark behavior]] explains when an hourly value can be called final.'),
    ('Reconcile to a stable baseline', 'Run a periodic batch calculation over an immutable event snapshot and compare its counts to finalized streaming windows. Match event-type filters, deduplication keys, time zone and correction version. A mismatch should identify affected windows and event IDs rather than merely showing a total difference. [[data-engineering/backfill-publication-boundary|Rebuild and swap]] can repair a corrupted aggregate without mixing versions.'),
    ('Set alert ownership', 'A rising backlog might need capacity, while a flat watermark with no input could mean an idle source. Late-correction volume can reveal a producer clock problem. Give each alert a threshold, owner, diagnosis steps and a safe rollback or pause action. Track rejected schema versions and dead-letter queues separately from accepted events.'),
    ('Test fault recovery', 'Pause one input partition, replay a duplicate burst and inject a malformed event. The dashboard should show stale or provisional state, not a false confirmed zero. After recovery, the batch parity job should reconcile the same fixed snapshot and identify any remaining late corrections. Record checkpoint and code versions in the incident packet.')],
    'def count_parity(stream_counts, batch_counts):\n    windows = set(stream_counts) | set(batch_counts)\n    return {window: (stream_counts.get(window, 0), batch_counts.get(window, 0))\n            for window in windows\n            if stream_counts.get(window, 0) != batch_counts.get(window, 0)}',
    'Comparing W finalized windows costs O(W) expected time and O(D) output space for D mismatches. A full batch recomputation costs O(N) over source events but provides an independent correctness check when stream state has been replayed or revised.',
    ['Do not report only consumer processing speed as data freshness.', 'Do not compare stream and batch totals under different filters or clocks.', 'Do not turn an idle producer into a measured zero window.'],
    ['streaming-analytics/idempotent-sink-and-replay','streaming-analytics/receipt-event-pipeline-project','data-engineering/backfill-publication-boundary','data-visualization/dashboard-filter-and-provenance'])

add('streaming-analytics/receipt-event-pipeline-project',
    'Project: build a replay-safe receipt event dashboard',
    'Build an hourly receipt-submission stream with explicit event-time windows, duplicate handling, late corrections and batch reconciliation.', [
    ('Prepare the event fixture', 'Create submission events with stable event IDs, receipt IDs, occurrence and ingestion times, schema versions and partition keys. Include a retry of the same event, an out-of-order submission, an unsupported schema and a correction after the first hourly output. [[streaming-analytics/event-contract-and-partition-key|The event contract]] must state which records count as submissions.'),
    ('Compute and publish', 'Assign each event to a half-open one-hour event-time window. Deduplicate by event ID, record a provisional count and route events after the watermark under a declared grace policy. Publish window ID, version, count, watermark and last update time. A replayed event must not increment the visible count twice. [[streaming-analytics/idempotent-sink-and-replay|Sink behavior]] must survive the fault fixture.'),
    ('Reconcile independently', 'Calculate counts from a fixed raw-event snapshot with a separate batch pass and compare every finalized window. Explain discrepancies by event ID and correction version. Simulate a consumer crash after writing but before checkpointing; the final output must match the clean run. Measure state size, backlog and correction volume during the run.'),
    ('Submit a handoff', 'Provide source events, schema definition, dedup ledger or sink transaction plan, window results, replay trace, parity report and dashboard state example. Mark an idle source stale rather than displaying a confirmed zero. Include a recovery procedure that rebuilds into a separate snapshot and switches only after reconciliation.')],
    'def receipt_hourly_counts(events):\n    counts = {}\n    seen_ids = set()\n    for event in events:\n        event_id = event["event_id"]\n        if event_id in seen_ids:\n            continue\n        seen_ids.add(event_id)\n        if event["type"] != "submitted":\n            continue\n        hour_start = (event["occurred_minute"] // 60) * 60\n        counts[hour_start] = counts.get(hour_start, 0) + 1\n    return counts',
    'A pass over N events is O(N) expected time and O(U + W) memory for U unique IDs and W windows. A production system must bound durable dedup and window state, and its batch parity check must use the same event-selection and correction rules.',
    ['Do not count a retried event twice.', 'Do not publish a provisional window as final without a watermark rule.', 'Do not claim replay safety from an in-memory set alone.'],
    ['streaming-analytics/event-time-window-and-boundaries','streaming-analytics/watermark-late-data-and-revisions','streaming-analytics/monitoring-lag-and-batch-parity','data-engineering/backfill-publication-boundary'])

assert len(lessons) == 14
assert len({item['path'] for item in lessons}) == len(lessons)
titles = {path: row['title'] for path, row in by_path.items()}
titles.update({item['path']: item['title'] for item in lessons})

def prose(value):
    return re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',
                  lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                  html.escape(value))

def links(paths):
    return '<ul>' + ''.join('<li><a href="/' + path + '">' + html.escape(titles[path]) + '</a></li>' for path in paths) + '</ul>'

def article_body(item):
    parts = ['<p>' + html.escape(item['summary']) + '</p>']
    for heading, paragraph in item['sections']:
        parts.extend(('<h2>' + html.escape(heading) + '</h2>', '<p>' + prose(paragraph) + '</p>'))
    parts.extend(('<h2>Implementation</h2>', '<pre><code class="language-python">' + html.escape(item['code']) + '</code></pre>',
                  '<h2>Performance and operating cost</h2>', '<p>' + html.escape(item['cost']) + '</p>',
                  '<h3>Common Mistakes</h3>', '<ul>' + ''.join('<li>' + html.escape(mistake) + '</li>' for mistake in item['mistakes']) + '</ul>',
                  '<h2>Read next</h2>', links(item['related'])))
    return ''.join(parts)

def make_row(path, title, summary, body, entry_type, subject, section_path, root_path, order, metadata):
    return dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://aitrove.in/' + path)), type=entry_type,
                path=path, title=title, summary=summary, body=body, category='AI & Data',
                subject=subject, difficulty='Intermediate', tags=['ai-data', subject], potd_date=None,
                featured=False, sort_order=order, status='published', published_at=stamp,
                created_at=stamp, updated_at=stamp,
                data={'subject_root':root_path, 'section_path':section_path,
                      'content_format':'html', 'seo_ready':True, **metadata})

subject_config = {
 'computer-vision': {
     'root':'computer-vision/computer-vision-tutorial', 'name':'Computer Vision',
     'summary':'Build image systems with explicit labels, reversible geometry, grouped evaluation and threshold-specific failure review.',
     'groups':[('Data and coordinates', ['image-unit-label-and-consent','pixel-geometry-and-preprocessing','annotation-geometry-and-quality']),
               ('Evaluation and release', ['grouped-evaluation-and-shift','augmentation-and-serving-parity','detection-metrics-and-thresholds'])],
     'project':'receipt-quality-project',
     'foundation':['data-science/data-science-for-beginners','deep-learning/deep-learning-tutorial'],
     'neighbors':['mlops/mlops-tutorial','streaming-analytics/streaming-analytics-tutorial']},
 'streaming-analytics': {
     'root':'streaming-analytics/streaming-analytics-tutorial', 'name':'Streaming Analytics',
     'summary':'Process event streams with versioned contracts, event-time windows, late corrections, replay-safe sinks and batch parity.',
     'groups':[('Event and time contracts', ['event-contract-and-partition-key','event-time-window-and-boundaries','watermark-late-data-and-revisions']),
               ('State and operations', ['idempotent-sink-and-replay','state-retention-and-stream-joins','monitoring-lag-and-batch-parity'])],
     'project':'receipt-event-pipeline-project',
     'foundation':['data-engineering/data-engineering-tutorial','time-series/time-series-tutorial'],
     'neighbors':['data-visualization/data-visualization-tutorial','computer-vision/computer-vision-tutorial']},
}

for config in subject_config.values():
    titles[config['root']] = config['name'] + ' Tutorial'
    titles[config['root'] + '/project'] = config['name'] + ': Projects'

for slug, config in subject_config.items():
    root_path = config['root']
    project_hub_path = root_path + '/project'
    modules = [{'title':group_title, 'summary':'Read in order and run the failure checks.',
                'lessons':[slug + '/' + lesson_name for lesson_name in lesson_names]}
               for group_title, lesson_names in config['groups']]
    project_path = slug + '/' + config['project']
    modules.append({'title':'Apply your knowledge', 'lessons':[project_path]})
    all_paths = [path for module in modules for path in module['lessons']]
    tabs = [{'title':config['name'], 'path':root_path}, {'title':'Projects', 'path':project_hub_path}]
    hub_body = ('<p>' + html.escape(config['summary']) + '</p><h2>Learning path</h2>' + links(all_paths)
                + '<h2>Connected foundations</h2><p>Use the earlier data and model boundaries as prerequisites.</p>'
                + links(config['foundation']) + '<h2>Further paths</h2>' + links(config['neighbors'])
                + '<h2>Practice</h2>' + links([project_hub_path]))
    hub = make_row(root_path, titles[root_path], config['summary'], hub_body,
                   'subject', slug, root_path, root_path, 9200 if slug == 'computer-vision' else 9300,
                   {'modules':modules, 'resource_tabs':tabs})
    project_body = ('<p>Apply the ' + html.escape(config['name']) + ' curriculum to a checked project.</p>'
                    '<h2>Project brief</h2>' + links([project_path])
                    + '<h2>Required concepts</h2>' + links(all_paths[:-1])
                    + '<h2>Completion standard</h2><p>Submit runnable work, a data manifest, measured results and failure-case evidence.</p>')
    project_hub = make_row(project_hub_path, titles[project_hub_path],
                           'A checked project for the ' + config['name'] + ' curriculum.', project_body,
                           'subject', slug + '-project', project_hub_path, root_path,
                           9201 if slug == 'computer-vision' else 9301,
                           {'modules':[{'title':'Projects','lessons':[project_path]}], 'resource_tabs':tabs})
    rows.extend((hub, project_hub))
    by_path[root_path] = hub
    by_path[project_hub_path] = project_hub

for index, item in enumerate(lessons):
    slug = item['path'].split('/')[0]
    root_path = subject_config[slug]['root']
    is_project = item['path'].endswith('-project')
    section_path = root_path + '/project' if is_project else root_path
    body = article_body(item)
    article = make_row(item['path'], item['title'], item['summary'], body, 'article',
                       slug + '-project' if is_project else slug, section_path, root_path,
                       9400 + index,
                       {'kind':'project' if is_project else 'tutorial',
                        'reading_minutes':max(5, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                        'author_path':'authors/aitrove-editorial',
                        'verification_suite':'Editorial and syntax review; project inputs needed for runtime checks',
                        'related':[{'path':path,'title':titles[path]} for path in item['related']]})
    rows.append(article)
    by_path[item['path']] = article

for source, target in [
    ('data-science/dataset-grain-and-join-cardinality','computer-vision/image-unit-label-and-consent'),
    ('deep-learning/deep-learning-tutorial','computer-vision/computer-vision-tutorial'),
    ('machine-learning/group-and-time-validation','computer-vision/grouped-evaluation-and-shift'),
    ('mlops/feature-training-serving-parity','computer-vision/augmentation-and-serving-parity'),
    ('data-engineering/event-time-and-late-arrivals','streaming-analytics/event-time-window-and-boundaries'),
    ('data-engineering/cdc-replay-and-deletes','streaming-analytics/idempotent-sink-and-replay'),
    ('time-series/observation-calendar-and-missing-periods','streaming-analytics/watermark-late-data-and-revisions'),
]:
    row = by_path[source]
    anchor = '<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in row['body']:
        row['body'] += anchor
        if row['type'] == 'article':
            row['data']['related'].append({'path':target,'title':titles[target]})
        row['updated_at'] = stamp

for source, target in [
    ('data-engineering/data-engineering-tutorial','streaming-analytics/streaming-analytics-tutorial'),
    ('time-series/time-series-tutorial','streaming-analytics/streaming-analytics-tutorial'),
    ('mlops/mlops-tutorial','computer-vision/computer-vision-tutorial'),
]:
    row = by_path[source]
    anchor = '<p><strong>Continue into another subject:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in row['body']:
        row['body'] += anchor
        row['updated_at'] = stamp

assert len({row['path'] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_articles':len(lessons), 'new_subject_hubs':4, 'crosslinks_from_existing':10}))
