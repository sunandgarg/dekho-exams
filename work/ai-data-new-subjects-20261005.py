"""Create original Data Engineering and Deep Learning subject curricula."""
import copy
import datetime
import html
import json
from pathlib import Path
import re
import uuid

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
rows = [row for row in rows if not row['path'].startswith(('data-engineering/', 'deep-learning/'))]
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()

def prose(value):
    return re.sub(r'\[\[([^|]+)\|([^\]]+)\]',
                  lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                  html.escape(value))

lessons = [
 dict(path='data-engineering/source-contract-and-raw-landing', title='Data source contracts: preserve raw records before transformation',
      summary='A source contract fixes record identity, event time, schema expectations and ownership before a pipeline edits or aggregates incoming data.',
      sections=[
       ('Name the source boundary', 'A receipt processor emits submissions and later corrections. The ingest job must know which field is the stable receipt ID, which timestamp describes the business event, which timestamp describes arrival, and who can change the schema. Capture raw bytes or a governed immutable copy before casting fields. Without the raw record, a transformation bug cannot be replayed after the source has moved on. [[data-science/reproducible-analysis-snapshot|Analysis snapshots]] depend on this earlier boundary.'),
       ('Validate but do not erase', 'Reject a record with a missing ID or an impossible timestamp into a quarantine stream with its source offset and reason. Do not quietly drop it, and do not coerce a malformed amount to zero. A contract may permit additive optional fields while rejecting a changed key type. Version the rule and count each rejection reason. An alert should compare the rejection rate with the source volume; one bad row in 47 records is very different from one in millions.'),
       ('Retain provenance', 'Store source system, partition or file identity, record position, ingest time and contract version. If an upstream team republishes a file, identify whether it is the same bytes or a new revision. Separate raw storage permissions from curated access; the raw layer may contain sensitive fields analysts should not see. [[data-engineering/quality-quarantine-and-reconciliation|Quality reconciliation]] uses the provenance to trace a missing receipt.'),
       ('Prove a schema change', 'Run the ingest contract against an old valid record, an additive-field record, a missing-key record and a changed timestamp format. The first two should be accepted under the written rule; the latter two should be quarantined with precise reasons. A parse success is not proof of semantic validity.')],
      code='from dataclasses import dataclass\nfrom datetime import datetime\n\n@dataclass(frozen=True)\nclass ReceiptEvent:\n    receipt_id: str\n    event_time: datetime\n    amount_cents: int\n\ndef validate_receipt(record: ReceiptEvent) -> None:\n    if not record.receipt_id or record.event_time.tzinfo is None:\n        raise ValueError("receipt identity and timezone are required")\n    if record.amount_cents < 0:\n        raise ValueError("negative receipt amount")',language='python',
      cost='Validation is O(N) for N records and usually small per row. Retaining raw input costs storage and access-control work; it is also what makes a correct replay possible.',
      mistakes=['Do not discard raw records after a failed transform.', 'Do not use arrival time as event time without saying so.', 'Do not coerce malformed money to a valid-looking zero.'],
      related=['data-engineering/quality-quarantine-and-reconciliation','data-engineering/incremental-watermark-and-ties','data-science/reproducible-analysis-snapshot','data-science/missing-data-policy']),
 dict(path='data-engineering/incremental-watermark-and-ties', title='Incremental extraction: advance a compound watermark without losing ties',
      summary='A compound watermark combines update time and a stable tie-breaker so a paged extractor can resume without skipping records that share a timestamp.',
      sections=[
       ('Why one timestamp is insufficient', 'A source updates several receipts at the same millisecond. If a job stops after page one and resumes with updated_at greater than its last timestamp, every remaining receipt with the same timestamp is skipped. Order by (updated_at, receipt_id) and persist both values. Query lexicographically after the saved pair. Use stable source ordering and treat the checkpoint as part of committed output, not as an optimistic progress marker.'),
       ('Define the consistency limit', 'A timestamp poll can still miss backdated changes, clock errors or deletes that leave no row. If those events matter, use a source change log or a bounded overlap window plus idempotent target upserts. The overlap trades repeated reads for a chance to catch late writes; it is not a proof against arbitrarily late records. [[data-engineering/cdc-replay-and-deletes|CDC]] carries a different change contract.'),
       ('Commit output before progress', 'Write the selected page into a staging or target transaction and move the checkpoint only after the page is durable. On a crash before commit, reread the page; on a crash after commit, resume from the saved pair. Therefore the target write must tolerate retries. [[data-engineering/idempotent-load-and-checkpoint|Idempotent loading]] closes that loop.'),
       ('Test the tie and crash', 'Create 53 source records with one identical update timestamp, page at 17 records, and interrupt after the second page. On restart, assert all 53 IDs appear once in the target. Then insert a backdated update and confirm the documented overlap or CDC policy handles it, or label that scenario unsupported.')],
      code='SELECT receipt_id, updated_at, amount_cents\nFROM receipt_source\nWHERE updated_at > :last_time\n   OR (updated_at = :last_time AND receipt_id > :last_id)\nORDER BY updated_at, receipt_id\nLIMIT :page_size;',language='sql',
      cost='With an index on (updated_at, receipt_id), each page can seek in O(log N) and scan O(P) rows for page size P. An overlap window increases repeated reads; a missing index turns polling into repeated table scans.',
      mistakes=['Do not advance on timestamp alone when records share it.', 'Do not save a checkpoint before its output is durable.', 'Do not assume timestamp polling observes physical deletes.'],
      related=['data-engineering/idempotent-load-and-checkpoint','data-engineering/cdc-replay-and-deletes','data-engineering/backfill-publication-boundary','data-science/reproducible-analysis-snapshot']),
 dict(path='data-engineering/cdc-replay-and-deletes', title='Change data capture: apply updates and deletes by source order',
      summary='A CDC consumer applies insert, update and delete events with source ordering and replay protection, then advances its offset only after the target state is durable.',
      sections=[
       ('Treat a delete as data', 'A receipt correction stream may emit a delete when a record is withdrawn. If the consumer ignores delete events, downstream tables keep a receipt that no longer exists at the source. A tombstone can remove the row or mark it inactive according to the warehouse retention policy. The business key and source position are part of every change; arrival order over the network is not necessarily commit order.'),
       ('Guard against replay and reordering', 'Keep the last applied source position per key or per ordered partition. A duplicate event should have no second effect; an older update must not revive a row after a newer delete. If the source splits one key across partitions without a global order, establish a consistent partitioning or version rule first. [[data-engineering/idempotent-load-and-checkpoint|Target and checkpoint ownership]] must be transactional or reconciled after failures.'),
       ('Bootstrap consistently', 'An initial snapshot and a live change stream need a handoff position. Start the stream from a point consistent with the snapshot; otherwise changes during copying can be missed or applied twice. Applying twice is safe only if the target operation is idempotent. Reconcile row counts and sampled keys after bootstrap, including a record updated and then deleted during the handoff.'),
       ('Make history policy explicit', 'A raw change log may retain an audit trail while a current-state table exposes only the latest row. Do not delete raw evidence to satisfy a curated current-state query, and do not expose deleted sensitive content beyond its retention policy. [[data-engineering/warehouse-history-asof-join|Historical dimensions]] use ordered changes for a different purpose: reconstructing a past view.')],
      code='def apply_change(current, event):\n    prior = current.get(event.receipt_id)\n    if prior is not None and event.source_position <= prior["position"]:\n        return False\n    current[event.receipt_id] = {\n        "position": event.source_position,\n        "deleted": event.operation == "DELETE",\n        "value": None if event.operation == "DELETE" else event.payload,\n    }\n    return True',language='python',
      cost='Applying E events is O(E) expected time with keyed state; durable position state grows with active or tombstoned keys. Retention and compaction need a rule that cannot allow an old replay to resurrect forgotten keys.',
      mistakes=['Do not ignore deletes because the target is analytical.', 'Do not use consumer arrival time as source commit order.', 'Do not start a change stream after a snapshot without a consistent handoff position.'],
      related=['data-engineering/idempotent-load-and-checkpoint','data-engineering/incremental-watermark-and-ties','data-engineering/warehouse-history-asof-join','data-engineering/quality-quarantine-and-reconciliation']),
 dict(path='data-engineering/idempotent-load-and-checkpoint', title='Idempotent loads: commit target rows and extraction progress together',
      summary='An idempotent load produces the same target state after a retry and ties its progress marker to committed output.',
      sections=[
       ('Expect at-least-once work', 'A worker can write a receipt batch and crash before acknowledging it. The scheduler then replays the same batch. If the target only appends, the result doubles. Use a stable receipt key or source event ID and an upsert or deduplication rule. An upsert needs conflict semantics: a later version may replace an earlier one, but an old replay must not overwrite a newer value.'),
       ('Place the checkpoint with the write', 'In one database transaction, validate a batch, apply its rows, and record the last source position. Either both commit or neither does. If target and checkpoint live in different systems, a single local transaction cannot cover them; design a replay-and-reconcile protocol instead of claiming exactly-once delivery. [[data-engineering/incremental-watermark-and-ties|Compound extraction markers]] define which page to read next.'),
       ('Make mutations observable', 'Record rows inserted, rows updated, stale events skipped and rejected records separately. A no-op retry should still confirm the batch identity was seen. Test a crash before commit, a crash immediately after commit, and the same batch delivered twice. The final target rows and checkpoint must match the uninterrupted run.'),
       ('Separate identity from batch position', 'A batch ID prevents a repeated file from applying twice, but it cannot by itself prevent an older correction file from overwriting a newer receipt. Retain row-level version or source position for mutable records. [[data-engineering/cdc-replay-and-deletes|CDC ordering]] makes this especially important.')],
      code='with database:\n    if not database.execute(\n        "SELECT 1 FROM processed_batches WHERE batch_id = ?",\n        (batch_id,)).fetchone():\n        database.executemany(\n            "INSERT INTO receipts(receipt_id, amount_cents) VALUES(?, ?) "\n            "ON CONFLICT(receipt_id) DO UPDATE SET amount_cents=excluded.amount_cents",\n            receipt_rows)\n        database.execute(\n            "INSERT INTO processed_batches(batch_id, last_position) VALUES(?, ?)",\n            (batch_id, last_source_position))',language='python',
      cost='With indexed keys, batch upserts cost about O(B log N) for B rows in a table of N rows; transaction logs and unique indexes add write amplification. Reconciliation scans can dominate very large backfills.',
      mistakes=['Do not acknowledge a batch before its target transaction commits.', 'Do not claim a batch ID protects against out-of-order row versions.', 'Do not claim exactly-once effects across two independent stores without a recovery protocol.'],
      related=['data-engineering/incremental-watermark-and-ties','data-engineering/cdc-replay-and-deletes','data-engineering/backfill-publication-boundary','data-engineering/quality-quarantine-and-reconciliation']),
 dict(path='data-engineering/event-time-and-late-arrivals', title='Event time and late arrivals: close windows with an explicit correction policy',
      summary='Event-time processing groups records by when they occurred, while a watermark states how much out-of-order arrival a live aggregate is prepared to wait for.',
      sections=[
       ('Two clocks answer different questions', 'A receipt submitted at 23:58 may reach the pipeline after midnight. Event-time reporting assigns it to the submission day; ingestion-time reporting assigns it to the day it arrived. Neither is automatically correct. State the business question, record both clocks, and measure the delay distribution. A watermark such as maximum observed event time minus a configured lateness allowance tells the processor which windows it considers complete.'),
       ('Do not confuse complete with final', 'A watermark is a processing policy, not evidence that no older event will ever arrive. Events later than the allowed delay need an explicit route: revise prior aggregates, publish a restatement, or quarantine them with a manual reconciliation queue. Dropping them without a count changes historical rates silently. [[data-science/metric-denominator-and-cohort|Cohort metrics]] need the same late-arrival rule in reports.'),
       ('Bound state and correction cost', 'Holding open windows consumes memory proportional to active keys and windows. A long allowed lateness period improves completeness but delays publication and enlarges state. A short period improves freshness but causes more corrections. Measure late-event rate, aggregate revisions and state size rather than picking an arbitrary delay.'),
       ('Test across the boundary', 'Feed events in this order: a timely receipt, a newer-day receipt, then a late receipt for the prior day. Verify the prior-day total and correction signal under the chosen policy. Also test duplicate delivery and timezone conversion. A window keyed by local midnight can shift during daylight-saving transitions.')],
      code='from datetime import timedelta\n\nlatest_event_time = max(event.event_time for event in received_events)\nwatermark = latest_event_time - timedelta(hours=3)\nfor event in received_events:\n    if event.event_time < watermark:\n        late_events.append(event)\n    else:\n        open_windows[event.event_time.date()].append(event)',language='python',
      cost='Each event can be assigned in O(1) expected time, but open state grows with active windows and keys. Corrections may require rebuilding downstream aggregates even when ingestion itself is cheap.',
      mistakes=['Do not use ingest time when the metric is defined by event time.', 'Do not drop records past a watermark without an explicit count and repair path.', 'Do not describe an event-time window as immutable before correction policy closes it.'],
      related=['data-engineering/backfill-publication-boundary','data-engineering/quality-quarantine-and-reconciliation','data-science/metric-denominator-and-cohort','data-engineering/source-contract-and-raw-landing']),
 dict(path='data-engineering/quality-quarantine-and-reconciliation', title='Data quality gates: quarantine bad rows and reconcile complete batches',
      summary='A quality gate checks both individual records and batch-level invariants, retaining rejected rows for diagnosis rather than silently shrinking the dataset.',
      sections=[
       ('Use two levels of checks', 'A row rule rejects a missing receipt ID, invalid currency or negative amount. A batch rule checks source count, accepted count, rejected count, unique keys and expected partitions. A file can have valid rows but still be incomplete because the transfer stopped halfway. Therefore a row parser alone is not a release gate. [[data-engineering/source-contract-and-raw-landing|The source contract]] defines which failures are fatal and which may be quarantined.'),
       ('Keep the rejected record recoverable', 'Store a bounded copy of the raw record, source position, rule version and reason in an access-controlled quarantine. Redact sensitive fields from alert messages. If the producer fixes the record, replay it with its original identity; do not assign a new identity that could double count it. Expire quarantine data according to retention policy, but first preserve aggregate failure counts for trend analysis.'),
       ('Reconcile before publish', 'Assert source_rows = accepted_rows + rejected_rows + intentionally_skipped_rows. Count distinct keys and compare totals that should be conserved, such as amount in cents, only when transformation semantics permit it. Pause publication when a required partition is missing or rejection rate crosses an agreed threshold. A warning alone can allow an incomplete dashboard to look authoritative.'),
       ('Run failure drills', 'Test a truncated input, duplicate key, malformed timestamp and a whole missing partition. Verify which cases stop publication and which go to quarantine. Check that a retry does not duplicate accepted rows. [[data-engineering/idempotent-load-and-checkpoint|Idempotent loads]] keep repair from creating a second failure.')],
      code='def reconcile_batch(source_count, accepted_count, rejected_count, skipped_count):\n    accounted = accepted_count + rejected_count + skipped_count\n    if accounted != source_count:\n        raise ValueError(f"unaccounted records: {source_count - accounted}")\n    if source_count and rejected_count / source_count > 0.02:\n        raise ValueError("receipt rejection budget exceeded")\n    return {"source": source_count, "accepted": accepted_count,\n            "rejected": rejected_count, "skipped": skipped_count}',language='python',
      cost='Row checks are O(N); distinct-key checks use O(K) memory for K keys in a local hash set or an indexed database. Quarantine storage and review effort grow with failure volume.',
      mistakes=['Do not assume valid rows imply a complete file.', 'Do not discard invalid rows before recording why they failed.', 'Do not publish a partially reconciled batch as a normal update.'],
      related=['data-engineering/source-contract-and-raw-landing','data-engineering/idempotent-load-and-checkpoint','data-engineering/backfill-publication-boundary','data-science/missing-data-policy']),
 dict(path='data-engineering/warehouse-history-asof-join', title='Warehouse history: join facts to the dimension version valid at event time',
      summary='A historical dimension keeps effective-time versions so a fact can be interpreted with the attributes that were valid when the event occurred.',
      sections=[
       ('Keep the old meaning', 'A store moves to a new operating region in September. A report of August receipts should use the August region when the question asks what was known then. Replacing the store row in place rewrites every past fact. A type-2 dimension stores non-overlapping validity intervals for the business key; the fact joins to the interval containing its event time. Decide whether a report instead wants today’s region, and name that distinct question.'),
       ('Enforce one interval per fact', 'For one store and timestamp, exactly one dimension row should match. Gaps create unmatched facts; overlapping intervals multiply them. Use half-open validity periods to avoid a boundary timestamp matching two versions. Check active interval uniqueness and row counts around the join. [[data-science/dataset-grain-and-join-cardinality|Cardinality checks]] are a correctness requirement, not an optimization.'),
       ('Handle corrections deliberately', 'A late source correction may change a past interval and every derived aggregate it touched. Rebuild affected partitions or publish a restated version. Preserve the raw change trail and dimension history for audit. [[data-engineering/cdc-replay-and-deletes|CDC replay]] can feed the versions, but a CDC event alone does not define business effective time.'),
       ('Test the boundary', 'Construct two store versions with an exact change timestamp and three receipts before, at and after that instant. Assert each fact matches one version. Then create a deliberate overlap and make the quality gate fail before report publication.')],
      code='SELECT r.receipt_id, r.submitted_at, d.operating_region\nFROM receipt_fact AS r\nJOIN store_region_history AS d\n  ON r.store_id = d.store_id\n AND r.submitted_at >= d.valid_from\n AND (d.valid_to IS NULL OR r.submitted_at < d.valid_to);',language='sql',
      cost='An indexed lookup on (store_id, valid_from) costs about O(log H) per fact among H history rows; an unbounded range join can be much more expensive. Retaining history increases storage but prevents silent rewriting of past context.',
      mistakes=['Do not overwrite a historical dimension if past reports need past attributes.', 'Do not allow interval overlaps to multiply fact rows.', 'Do not equate CDC arrival time with business effective time.'],
      related=['data-engineering/cdc-replay-and-deletes','data-engineering/backfill-publication-boundary','data-science/dataset-grain-and-join-cardinality','data-science/metric-denominator-and-cohort']),
 dict(path='data-engineering/backfill-publication-boundary', title='Backfills: rebuild history without exposing a half-written result',
      summary='A backfill computes corrected partitions under a versioned rule and publishes them only after quality checks pass as a complete replacement.',
      sections=[
       ('Separate build from visibility', 'A new receipt-tax rule requires rebuilding six months of aggregates. Updating the visible table one month at a time makes dashboards mix old and new rules. Build corrected partitions in a staging namespace, validate totals and key coverage, then switch a version pointer or replace partitions through the warehouse’s atomic publish mechanism. Readers should see either the old complete version or the new complete version.'),
       ('Pin inputs and rules', 'Record source snapshots, code revision, transform parameters and affected partition range. If the source receives late changes while the backfill runs, choose a consistent cutoff and apply subsequent changes after publication. Running a backfill against moving data without a cutoff creates a result no one can reproduce. [[data-science/reproducible-analysis-snapshot|Snapshot manifests]] document that choice.'),
       ('Budget replay pressure', 'A backfill can compete with live ingest for CPU, I/O and database locks. Limit concurrency and measure lag in the live pipeline. Maintain a rollback pointer to the prior version, but do not assume rollback can undo irreversible downstream exports. List consumers and cache invalidation before the switch.'),
       ('Verify the repaired history', 'Compare row counts, key uniqueness, rejection counts and representative totals against the old version. Recompute at least one downstream report and record the expected change. Deliberately fail a staged partition and confirm that no pointer swap occurs. [[data-engineering/quality-quarantine-and-reconciliation|Quality gates]] make publication conditional on complete evidence.')],
      code='backfill_manifest = {\n    "version": "receipt-rule-v47",\n    "source_snapshot": source_snapshot_id,\n    "partitions": list(affected_months),\n    "validated": all(partition_checks.values()),\n}\nif not backfill_manifest["validated"]:\n    raise RuntimeError("backfill failed quality gates")\npublish_version_pointer(backfill_manifest["version"])',language='python',
      cost='A full backfill reads and rewrites O(H) historical rows for H affected records, plus temporary storage for a parallel version. An atomic pointer switch is cheap; the expensive part is the validated rebuild and downstream reconciliation.',
      mistakes=['Do not expose a mixture of old and new transformation rules.', 'Do not rebuild against an unpinned moving source without a cutoff policy.', 'Do not publish when one required partition failed validation.'],
      related=['data-engineering/quality-quarantine-and-reconciliation','data-engineering/idempotent-load-and-checkpoint','data-engineering/event-time-and-late-arrivals','data-science/reproducible-analysis-snapshot']),
]

lessons.extend([
 dict(path='deep-learning/tensor-shape-dtype-contract', title='Tensor contracts: shape, dtype, device and mask',
      summary='A tensor boundary states what every axis means, which numeric type is valid and whether padding represents data.',
      sections=[
       ('Name every axis', 'A batch of receipt images has shape (batch, channel, height, width). A text encoder may expect (batch, token). Write these contracts at the loader boundary and assert them before the model. A tensor with the right total element count can still have transposed axes. [[deep-learning/batching-and-class-sampling|Batch construction]] must preserve the same contract for a short final batch.'),
       ('Pin numeric semantics', 'Image bytes become floating values under a named scaling rule; class targets remain integer indices for an index-based classification loss. Check finite values before training, and record dtype and precision policy. Move inputs, targets and model parameters to the intended device. A mixed CPU and accelerator calculation can fail only on a less common branch.'),
       ('Represent absence', 'Padding a variable-length sequence changes storage, not meaning. Carry a mask marking real elements and apply it to attention or aggregation. An all-zero input might be a real dark image, so zero alone is a weak missingness marker. [[data-science/missing-data-policy|Missingness rules]] belong in the dataset contract.'),
       ('Test before training', 'Feed one item, an incomplete last batch, a corrupted image and an unknown label. Assert axes, dtype, range and finite values. Route the corrupted item to a visible rejection path rather than converting it to a plausible black image. Save the contract with the model artifact so inference can enforce it.')],
      code='def validate_image_batch(images, class_ids, class_count):\n    if images.ndim != 4 or images.shape[1] != 3:\n        raise ValueError("expected NCHW RGB images")\n    if class_ids.shape != (images.shape[0],):\n        raise ValueError("one class index per image")\n    if images.dtype != torch.float32 or class_ids.dtype != torch.int64:\n        raise TypeError("unexpected tensor dtype")\n    if not torch.isfinite(images).all():\n        raise ValueError("non-finite input")\n    if ((class_ids < 0) | (class_ids >= class_count)).any():\n        raise ValueError("class index out of range")',language='python',
      cost='Shape and dtype checks cost O(1); scanning all pixels for non-finite values costs O(BCHW) per batch. The scan has a measurable cost, but silent invalid values can poison an entire training run.',
      mistakes=['Do not infer axis meaning from shape alone.', 'Do not cast integer class indices to float for an index-based loss.', 'Do not treat padding as an observation.'],
      related=['deep-learning/logits-loss-gradient','deep-learning/batching-and-class-sampling','deep-learning/inference-schema-and-latency','data-science/missing-data-policy']),
 dict(path='deep-learning/logits-loss-gradient', title='Logits, cross-entropy and gradients: align the training calculation',
      summary='Classification training needs raw class scores, integer targets and an explicit gradient lifecycle.',
      sections=[
       ('Follow the score contract', 'A classifier produces one raw score per class. Cross-entropy consumes those logits and class-index targets; it performs the stable normalization needed for the loss. Applying softmax before that loss compresses scores a second time and changes gradients. Convert logits to probabilities only when a metric or decision policy needs them. [[machine-learning/probability-calibration|Calibration]] tests whether those probabilities match observed frequency.'),
       ('Control one update', 'For each batch, clear old gradients, run the forward pass, calculate loss, backpropagate and step the optimizer. If gradients are deliberately accumulated, divide loss or adjust the update policy and record how many examples contribute. An omitted zero step otherwise accumulates gradients by accident. Variable batch sizes can also change the effective weight of an update.'),
       ('Inspect the failure path', 'Verify finite loss and gradient norms, target range and output shape. A falling training loss is insufficient evidence of generalization: the model may learn a leaked field or repeated receipt identity. [[machine-learning/group-and-time-validation|Grouped and time-aware validation]] makes that shortcut more visible. Stop rather than silently skipping every non-finite batch.'),
       ('Overfit a small batch first', 'Train on a fixed tiny batch until the model can fit it. If it cannot, inspect labels, learning rate, loss inputs and gradient flow before growing the architecture. Then test a second fixed batch size. This narrow experiment catches shape and optimizer mistakes faster than a full training run.')],
      code='optimizer.zero_grad(set_to_none=True)\nlogits = receipt_model(image_batch)\nif logits.shape != (image_batch.shape[0], class_count):\n    raise ValueError("class-score shape changed")\nloss = torch.nn.functional.cross_entropy(logits, class_ids)\nif not torch.isfinite(loss):\n    raise ValueError("non-finite loss")\nloss.backward()\noptimizer.step()',language='python',
      cost='Forward and backward passes dominate computation and activation memory; backward keeps intermediates related to batch size and model depth. A larger batch helps throughput only until memory or generalization becomes the limit.',
      mistakes=['Do not softmax before a cross-entropy API expecting logits.', 'Do not accumulate gradients accidentally.', 'Do not treat lower training loss as proof of deployment value.'],
      related=['deep-learning/tensor-shape-dtype-contract','deep-learning/train-eval-validation-loop','deep-learning/checkpoint-resume-state','machine-learning/probability-calibration']),
 dict(path='deep-learning/train-eval-validation-loop', title='Training and validation modes: measure the model you will serve',
      summary='Validation switches the model to evaluation behavior, disables gradient work and weights metrics by observed examples.',
      sections=[
       ('Separate optimization from measurement', 'Training updates parameters; validation estimates behavior on records that did not guide those updates. Set training mode before optimization and evaluation mode before measurement. Dropout and batch normalization change behavior across modes. A validation score computed in training mode measures a different system from the one served. Use inference mode during validation to avoid retaining a gradient graph.'),
       ('Count images, not batches', 'The last batch may contain fewer images. Average loss weighted by batch size, then divide by the evaluated image count; an average of batch means overweights a short final batch. Track confusion counts by relevant group, not only rounded accuracy. [[machine-learning/group-and-time-validation|Holdout design]] determines whether the result answers the intended future question.'),
       ('Freeze the selection rule', 'Choose a primary validation metric and checkpoint rule before inspecting results. Repeatedly trying architectures, thresholds and preprocessing against the same holdout adapts the project to that holdout. Keep a final untouched test set for one evaluation after selection. [[deep-learning/augmentation-leakage-boundary|Augmentation and splitting]] must respect this boundary.'),
       ('Verify mode restoration', 'Run validation on two batches, including a short batch, and calculate the weighted mean by hand. Assert the model has a known mode after the helper returns. A validation helper that leaves the model in evaluation mode can silently disable training behavior in the next epoch.')],
      code='def validation_loss(receipt_model, validation_loader, loss_function):\n    receipt_model.eval()\n    weighted_loss = 0.0\n    image_count = 0\n    with torch.inference_mode():\n        for images, class_ids in validation_loader:\n            batch_loss = loss_function(receipt_model(images), class_ids)\n            weighted_loss += batch_loss.item() * len(images)\n            image_count += len(images)\n    if image_count == 0:\n        raise ValueError("empty validation set")\n    return weighted_loss / image_count',language='python',
      cost='Validation takes O(V) forward evaluations for V examples without a backward graph. Frequent validation spends training time; infrequent validation can miss overfitting or an unstable update.',
      mistakes=['Do not evaluate dropout or batch normalization in training mode.', 'Do not average batch means without weighting the short batch.', 'Do not tune repeatedly on the final test partition.'],
      related=['deep-learning/logits-loss-gradient','deep-learning/augmentation-leakage-boundary','deep-learning/checkpoint-resume-state','machine-learning/group-and-time-validation']),
])

lessons.extend([
 dict(path='data-engineering/receipt-pipeline-replay-project', title='Project: build a replayable receipt pipeline with an atomic publish gate',
      summary='Implement a receipt pipeline that survives retries, deletes, late events and a failed backfill without exposing inconsistent aggregates.',
      sections=[
       ('Define the deliverable', 'Build a raw landing table, current receipt table and daily aggregate. Each input needs source identity, event time, arrival time and source position. Write correction and delete semantics before building the transform. A second run over identical input must leave exactly the same current state and aggregate. [[data-engineering/source-contract-and-raw-landing|Begin with the source contract]], then document retention and ownership.'),
       ('Implement replay', 'Consume a deliberately shuffled fixture through a source-order field. Apply an update and later delete for the same receipt; replay of an older update must not resurrect it. Commit the checkpoint with target state or document an equivalent recovery design. [[data-engineering/cdc-replay-and-deletes|CDC ordering]] and [[data-engineering/idempotent-load-and-checkpoint|idempotent writes]] define the failure cases.'),
       ('Test time and publication', 'Insert a receipt after its business day closes and state whether the daily aggregate is corrected, versioned or left final. Stage a backfill with one required partition missing. The visible aggregate must remain the prior complete version; the failed candidate and reason must remain inspectable. [[data-engineering/backfill-publication-boundary|The publish boundary]] is the central acceptance test.'),
       ('Submit evidence', 'Provide schema, fixture, runnable command and outputs from initial load, same-input replay, crash-and-restart, delete, late arrival and failed backfill. Reconcile source, accepted, rejected and skipped counts. State per-page cost and temporary backfill storage. A final dashboard screenshot cannot establish these invariants.')],
      code='def assert_replay_invariants(load_fixture, snapshot_state, fixture):\n    load_fixture(fixture)\n    first_state = snapshot_state()\n    load_fixture(fixture)\n    second_state = snapshot_state()\n    assert first_state == second_state\n    assert second_state["source_count"] == (\n        second_state["accepted_count"] + second_state["rejected_count"]\n        + second_state["skipped_count"]\n    )',language='python',
      cost='One pass over N source events is O(N) before index costs; a keyed B-tree upsert adds about O(log K) per event for K current receipts. Rebuilding H historical rows costs O(H) plus staging storage.',
      mistakes=['Do not call a pipeline replayable because its second run finished.', 'Do not lose deletes when deriving current state.', 'Do not expose a failed staged backfill.'],
      related=['data-engineering/source-contract-and-raw-landing','data-engineering/cdc-replay-and-deletes','data-engineering/event-time-and-late-arrivals','data-engineering/backfill-publication-boundary']),
 dict(path='deep-learning/receipt-image-quality-project', title='Project: classify receipt image quality with a checked training contract',
      summary='Train a receipt-image classifier, then check identity splits, tensor contracts, validation arithmetic, recovery and serving behavior.',
      sections=[
       ('Define the task', 'Choose labels such as readable, blurred and cut-off. Record how annotators handle a photo with more than one defect: use a priority rule or a multi-label target with a matching loss. For single-label training, pin class order and image input format. Split original receipt identities before augmentation. [[deep-learning/tensor-shape-dtype-contract|Tensor checks]] and [[deep-learning/augmentation-leakage-boundary|split checks]] must run.'),
       ('Train against a baseline', 'Start with class prevalence and a simple image model. Show a tiny-batch overfit check, then train under a fixed optimizer and epoch budget. Log examples seen, loss, invalid gradients and validation counts. Use raw logits for cross-entropy and the correct evaluation mode. [[deep-learning/logits-loss-gradient|The loss contract]] and [[deep-learning/train-eval-validation-loop|weighted validation]] are review criteria.'),
       ('Exercise recovery and serving', 'Interrupt training after a checkpoint and resume with the same class mapping and input manifest. Compare one fixed-batch update. Publish an inference manifest with preprocessing and maximum request size. Reject a corrupt image and oversized request; measure loaded high-percentile latency at a stated concurrency. [[deep-learning/inference-schema-and-latency|Serving]] must match the selected checkpoint.'),
       ('Report failure slices', 'Show a confusion table and error examples for dim light, angled photos and duplicate captures. State the count per slice; do not give percentages without denominators. Compare the selected model with the baseline on an untouched test partition once. Submit code, run manifest, sample IDs and failure-case outputs so another engineer can reproduce the decision.')],
      code='def check_image_project(train_ids, validation_ids, test_ids, class_names):\n    partitions = [set(train_ids), set(validation_ids), set(test_ids)]\n    if any(not group for group in partitions):\n        raise ValueError("empty image partition")\n    if any(partitions[left] & partitions[right]\n           for left, right in ((0, 1), (0, 2), (1, 2))):\n        raise ValueError("identity leaked across partitions")\n    if len(class_names) != len(set(class_names)):\n        raise ValueError("duplicate class label")',language='python',
      cost='Each training epoch reads O(N) images; decoding and augmentation may dominate loader CPU. Include peak device memory, total training time and loaded inference tail latency in the project report.',
      mistakes=['Do not split variants independently of original receipts.', 'Do not promote a checkpoint without preprocessing metadata.', 'Do not hide tiny failure slices behind overall accuracy.'],
      related=['deep-learning/tensor-shape-dtype-contract','deep-learning/train-eval-validation-loop','deep-learning/checkpoint-resume-state','deep-learning/inference-schema-and-latency']),
])

lessons.extend([
 dict(path='deep-learning/batching-and-class-sampling', title='Batching and class sampling: know the population the optimizer sees',
      summary='Batch construction controls memory, gradient noise and class exposure; sampling changes the training distribution.',
      sections=[
       ('Choose size by measurement', 'A batch must fit inputs, activations, optimizer state and temporary workspace. Start with a measured size and observe peak memory and examples per second. Doubling the batch can improve device use, but can also reduce update frequency or exhaust memory. Keep the short final batch or say why it is discarded; repeated dropping can exclude particular records when order is stable.'),
       ('Treat imbalance as policy', 'Oversampling rare damaged receipts makes the optimizer see a class mix unlike live traffic. That may improve ranking of unusual cases, but raw probabilities no longer automatically describe deployment prevalence. Evaluate on a holdout with the actual mix and calibrate if decisions require probabilities. [[machine-learning/decision-threshold-and-cost|Thresholds]] should reflect review capacity and error costs.'),
       ('Keep identities apart', 'A sampler can put near-duplicate photos of one receipt into many training batches. That is acceptable within training, but not across training and validation. Split by receipt or customer group before creating samplers or variants. [[deep-learning/augmentation-leakage-boundary|The split boundary]] defines the correct order.'),
       ('Audit effective exposure', 'Count unique receipt IDs and class counts over a sampled epoch. Check every target index and confirm that no evaluation ID appears in training. Document replacement. When a rare class has only a few unique cases, repeated exposure is not new information; report the unique count beside sample count.')],
      code='from torch.utils.data import WeightedRandomSampler\n\ntraining_counts = torch.bincount(training_class_ids, minlength=class_count)\nif (training_counts == 0).any():\n    raise ValueError("training class has no observations")\nper_receipt_weight = 1.0 / training_counts[training_class_ids].float()\ntraining_sampler = WeightedRandomSampler(\n    weights=per_receipt_weight,\n    num_samples=len(training_class_ids),\n    replacement=True,\n)',language='python',
      cost='A batch of B images adds O(BCHW) input memory plus model activations. Constructing weights is O(N); sampling N records per epoch adds selection work and can repeat scarce rows many times.',
      mistakes=['Do not assume oversampled probabilities match live prevalence.', 'Do not sample before a grouped split.', 'Do not discard a short batch silently.'],
      related=['deep-learning/tensor-shape-dtype-contract','deep-learning/augmentation-leakage-boundary','machine-learning/group-and-time-validation','machine-learning/decision-threshold-and-cost']),
 dict(path='deep-learning/augmentation-leakage-boundary', title='Image augmentation: split originals first and preserve the label',
      summary='Augmentation creates training variants only after an identity-aware split, using transforms that keep the label true.',
      sections=[
       ('Split originals first', 'Two photos of one receipt, or crops of one photo, belong in the same partition. Split by receipt identity before generating variants. If augmentation runs first and variants land in training and validation, the model can recognize the underlying receipt instead of generalizing. [[machine-learning/group-and-time-validation|Grouped validation]] addresses the same identity issue for tabular records.'),
       ('Check label preservation', 'A mild brightness change may preserve a damage label. A crop removing the torn corner does not. Define allowed transforms per label and inspect a sample of outputs. A transform is not safe merely because it is common in image pipelines. Keep the untouched validation distribution close to deployment input, including blur or poor lighting when those occur.'),
       ('Make randomness auditable', 'Record transform names, ranges, library configuration and a run seed. A seed helps repeatability, though worker scheduling and accelerator kernels can still vary. Store original receipt IDs with augmented variants for group checks. [[deep-learning/checkpoint-resume-state|Checkpoint metadata]] should include the augmentation policy version.'),
       ('Compare against a baseline', 'Train once without augmentation and once with the declared policy under the same split and evaluation procedure. Report overall results and the failure slices that motivated the policy. If improvement appears only on augmented validation images, that test cannot support a deployment claim.')],
      code='def assert_disjoint_receipts(training_rows, validation_rows):\n    training_ids = {row.receipt_id for row in training_rows}\n    validation_ids = {row.receipt_id for row in validation_rows}\n    overlap = training_ids & validation_ids\n    if overlap:\n        raise ValueError(f"receipt overlap: {len(overlap)}")\n\nassert_disjoint_receipts(training_rows, validation_rows)\naugmented_training_rows = augment_receipts(training_rows, policy_version)',language='python',
      cost='Set overlap checks cost O(N) time and memory for N unique IDs. Offline augmentation adds storage proportional to variants; online augmentation spends CPU per batch and can limit loader throughput.',
      mistakes=['Do not split variants independently of their original.', 'Do not crop away evidence while retaining the original label.', 'Do not augment validation to inflate the result.'],
      related=['deep-learning/batching-and-class-sampling','deep-learning/train-eval-validation-loop','machine-learning/group-and-time-validation','deep-learning/receipt-image-quality-project']),
 dict(path='deep-learning/checkpoint-resume-state', title='Checkpoint recovery: save optimizer state and the run boundary',
      summary='A resumable run records weights and optimizer state alongside epoch, class mapping, configuration and input identity.',
      sections=[
       ('Distinguish deploy from resume', 'Weights may be enough for inference. They are not enough for a faithful training restart because momentum and adaptive optimizer statistics affect the next update. Save model and optimizer state, completed epoch, configuration, class mapping and input manifest. Save scheduler or precision-scaler state when used. [[data-science/reproducible-analysis-snapshot|Input snapshots]] prevent a restart from silently changing data.'),
       ('Write a complete artifact', 'Serialize to a temporary file in the same filesystem, then replace the published checkpoint. A process killed mid-write should leave the previous complete artifact readable. For remote object storage, use an immutable object plus a pointer rather than assuming rename is atomic. Keep best-validation and latest-recovery artifacts distinct.'),
       ('Check before resuming', 'Compare architecture, class order, data manifest and configuration. A checkpoint may load while labels have changed order, returning plausible but wrong classifications. Restore random state if exact stochastic continuation matters; hardware and kernel behavior can still prevent bitwise replay. Document any deliberate learning-rate change rather than presenting it as an identical continuation.'),
       ('Drill a failure', 'Train a few updates, interrupt during candidate checkpoint writing, then restart. Confirm the prior checkpoint remains readable and a truncated candidate is rejected. Compare the next fixed-batch loss under a controlled setup. [[deep-learning/train-eval-validation-loop|Validation]] determines which artifact may be promoted.')],
      code='checkpoint = {\n    "completed_epoch": completed_epoch,\n    "model_state": receipt_model.state_dict(),\n    "optimizer_state": optimizer.state_dict(),\n    "class_names": class_names,\n    "data_manifest": data_manifest_id,\n}\ntemporary_path = checkpoint_path.with_suffix(".pending")\ntorch.save(checkpoint, temporary_path)\ntemporary_path.replace(checkpoint_path)',language='python',
      cost='A save transfers O(P + S) bytes for P model parameters and S optimizer state. Frequent checkpoints cost I/O and storage; sparse saves increase lost work after failure.',
      mistakes=['Do not claim a faithful optimizer resume from weights alone.', 'Do not overwrite the only valid checkpoint during an incomplete write.', 'Do not load without checking class order and input identity.'],
      related=['deep-learning/train-eval-validation-loop','deep-learning/inference-schema-and-latency','data-science/reproducible-analysis-snapshot','deep-learning/receipt-image-quality-project']),
 dict(path='deep-learning/inference-schema-and-latency', title='Inference contracts: preserve preprocessing and measure tail latency',
      summary='Deployment binds weights to input transforms and class mapping, then measures latency under realistic request load.',
      sections=[
       ('Package the decision', 'Publish model weights, preprocessing version, dimensions, channel order, class names and threshold together. A server that resizes differently or reverses channels may return plausible scores with the wrong meaning. Validate file type, decoded dimensions and maximum bytes before allocating large tensors. [[deep-learning/tensor-shape-dtype-contract|Tensor contracts]] are API constraints, not training-only checks.'),
       ('Separate score and action', 'Return a score only with a declared class order. Convert logits to probabilities when the endpoint promises them, then apply a threshold chosen under a review-capacity policy. Include an abstain path for unsupported or poor-quality inputs. [[machine-learning/decision-threshold-and-cost|Threshold analysis]] connects model output to the operational action.'),
       ('Measure loaded behavior', 'Warm the model, then measure decode, preprocessing, queue, forward pass and serialization separately. Report median and high-percentile latency under concurrent traffic, rather than one idle request. Batch inference may raise throughput while making one request wait longer. State maximum batch and timeout, and reject overload predictably.'),
       ('Monitor failure safely', 'Count decode failures, invalid shapes, abstentions and score shifts by relevant slice. Avoid raw personal images in routine logs. Keep a rollback artifact and known-good requests; compare outputs and class names with the manifest before shifting traffic.')],
      code='def predict_receipt(image_bytes, receipt_model, preprocess, class_names):\n    if len(image_bytes) > 4_000_000:\n        raise ValueError("image exceeds request limit")\n    image_tensor = preprocess(image_bytes)\n    if image_tensor.shape != (3, 224, 224):\n        raise ValueError("unexpected dimensions")\n    receipt_model.eval()\n    with torch.inference_mode():\n        logits = receipt_model(image_tensor.unsqueeze(0))\n        probabilities = logits.softmax(dim=1)[0]\n    return dict(zip(class_names, probabilities.tolist()))',language='python',
      cost='Prediction costs preprocessing and one model forward pass. Concurrent requests add queue and memory pressure; batching exchanges lower compute per image for additional wait time. Measure p95 under intended concurrency.',
      mistakes=['Do not deploy weights without class mapping and preprocessing.', 'Do not treat an idle request as a latency guarantee.', 'Do not log sensitive images during routine errors.'],
      related=['deep-learning/tensor-shape-dtype-contract','deep-learning/checkpoint-resume-state','deep-learning/receipt-image-quality-project','machine-learning/decision-threshold-and-cost']),
])

assert len({item['path'] for item in lessons}) == len(lessons)
titles = {path: row['title'] for path, row in by_path.items()}
titles.update({item['path']: item['title'] for item in lessons})

def internal_list(paths):
    return '<ul>' + ''.join('<li><a href="/' + path + '">' + html.escape(titles[path]) + '</a></li>' for path in paths) + '</ul>'

def article_body(item):
    body = ['<p>' + html.escape(item['summary']) + '</p>']
    for heading, paragraph in item['sections']:
        body += ['<h2>' + html.escape(heading) + '</h2>', '<p>' + prose(paragraph) + '</p>']
    body += ['<h2>Implementation</h2>', '<pre><code class="language-' + item['language'] + '">' + html.escape(item['code']) + '</code></pre>',
             '<h2>Performance and operating cost</h2>', '<p>' + html.escape(item['cost']) + '</p>',
             '<h3>Common Mistakes</h3>', '<ul>' + ''.join('<li>' + html.escape(mistake) + '</li>' for mistake in item['mistakes']) + '</ul>',
             '<h2>Read next</h2>', internal_list(item['related'])]
    return ''.join(body)

def new_row(path, title, summary, body, row_type, subject, section_path, subject_root, sort_order, data):
    return dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://aitrove.in/' + path)), type=row_type,
                path=path, title=title, summary=summary, body=body, category='AI & Data',
                subject=subject, difficulty='Intermediate', tags=['ai-data', subject], potd_date=None,
                featured=False, sort_order=sort_order, status='published', published_at=stamp,
                created_at=stamp, updated_at=stamp, data={'subject_root':subject_root,
                'section_path':section_path, 'content_format':'html', 'seo_ready':True, **data})

subject_config = {
 'data-engineering': {
    'root':'data-engineering/data-engineering-tutorial', 'name':'Data Engineering',
    'summary':'Build receipt pipelines that preserve source identity, survive replay and publish only reconciled results.',
    'groups':[('Source and replay', ['source-contract-and-raw-landing','incremental-watermark-and-ties','cdc-replay-and-deletes','idempotent-load-and-checkpoint']),
              ('Time, quality and publication', ['event-time-and-late-arrivals','quality-quarantine-and-reconciliation','warehouse-history-asof-join','backfill-publication-boundary'])],
    'project':'receipt-pipeline-replay-project'},
 'deep-learning': {
    'root':'deep-learning/deep-learning-tutorial', 'name':'Deep Learning',
    'summary':'Train and serve an image classifier through checked data, loss, validation, recovery and inference boundaries.',
    'groups':[('Training contracts', ['tensor-shape-dtype-contract','logits-loss-gradient','batching-and-class-sampling','augmentation-leakage-boundary']),
              ('Evaluation and deployment', ['train-eval-validation-loop','checkpoint-resume-state','inference-schema-and-latency'])],
    'project':'receipt-image-quality-project'},
}

for slug, config in subject_config.items():
    subject_root = config['root']
    project_hub = subject_root + '/project'
    titles[subject_root] = config['name'] + ' Tutorial'
    titles[project_hub] = config['name'] + ': Projects'
    modules = [{'title': label, 'summary':'Read in order and run the stated failure checks.',
                'lessons':[slug + '/' + name for name in names]} for label, names in config['groups']]
    project_path = slug + '/' + config['project']
    modules.append({'title':'Apply your knowledge', 'lessons':[project_path]})
    all_paths = [path for module in modules for path in module['lessons']]
    prior_root = 'data-science/data-science-for-beginners' if slug == 'data-engineering' else 'machine-learning/machine-learning-tutorial'
    hub_body = ('<p>' + html.escape(config['summary']) + '</p><h2>Learning path</h2>' + internal_list(all_paths)
                + '<h2>Connected foundation</h2><p>Bring the earlier analysis and evaluation contracts into this subject.</p>'
                + internal_list([prior_root, 'data-science/reproducible-analysis-snapshot' if slug == 'data-engineering' else 'machine-learning/group-and-time-validation'])
                + '<h2>Practice</h2><p>Complete the project with its failure-case evidence.</p>' + internal_list([project_hub]))
    tabs = [{'title':config['name'], 'path':subject_root}, {'title':'Projects', 'path':project_hub}]
    hub = new_row(subject_root, config['name'] + ' Tutorial', config['summary'], hub_body,
                  'subject', slug, subject_root, subject_root, 7600 if slug == 'data-engineering' else 7700,
                  {'modules':modules, 'resource_tabs':tabs})
    project_body = ('<p>Build and review a complete ' + html.escape(config['name']) + ' project.</p>'
                    '<h2>Project brief</h2>' + internal_list([project_path])
                    + '<h2>Required concepts</h2>' + internal_list(all_paths[:-1])
                    + '<h2>Completion standard</h2><p>Submit inputs, runnable work, measured output, failure-case results and a short decision note.</p>')
    project = new_row(project_hub, config['name'] + ': Projects', 'A checked project for the ' + config['name'] + ' curriculum.',
                      project_body, 'subject', slug + '-project', project_hub, subject_root,
                      7601 if slug == 'data-engineering' else 7701,
                      {'modules':[{'title':'Projects','lessons':[project_path]}], 'resource_tabs':tabs})
    rows.extend([hub, project])
    by_path[subject_root] = hub
    by_path[project_hub] = project

for index, item in enumerate(lessons):
    slug = item['path'].split('/')[0]
    subject_root = subject_config[slug]['root']
    is_project = item['path'].endswith('-project')
    section_path = subject_root + '/project' if is_project else subject_root
    row = new_row(item['path'], item['title'], item['summary'], article_body(item), 'article',
                  slug + '-project' if is_project else slug, section_path, subject_root,
                  7800 + index, {'kind':'project' if is_project else 'tutorial',
                  'reading_minutes':max(5, len(article_body(item).split()) // 180),
                  'author_path':'authors/aitrove-editorial',
                  'verification_suite':'Editorial and syntax review; project data needed for runtime checks',
                  'related':[{'path':path, 'title':titles[path]} for path in item['related']]})
    rows.append(row)
    by_path[item['path']] = row

for source, target in [
    ('data-science/reproducible-analysis-snapshot','data-engineering/data-engineering-tutorial'),
    ('data-science/dataset-grain-and-join-cardinality','data-engineering/warehouse-history-asof-join'),
    ('machine-learning/group-and-time-validation','deep-learning/augmentation-leakage-boundary'),
    ('machine-learning/probability-calibration','deep-learning/inference-schema-and-latency'),
]:
    row = by_path[source]
    anchor = '<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in row['body']:
        row['body'] += anchor
        row['data']['related'].append({'path':target,'title':titles[target]})
        row['updated_at'] = stamp

assert len({row['path'] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_lessons':len(lessons), 'new_subject_hubs':4, 'new_links_from_existing':4}))
