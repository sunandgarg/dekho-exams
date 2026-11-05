"""Add reproducible pipelines and batch inference lessons to MLOps."""
from de_batch_publisher import publish

M = 'mlops/'
P = 'Reproducible training pipelines'
B = 'Batch inference and replay'

lessons = [
    {
        'path': M + 'pipeline-stage-inputs-and-cache-identity',
        'title': 'Pipeline stages: cache by complete input identity',
        'module': P, 'project': False,
        'summary': 'A cached training stage is reusable only when its code, configuration, data and environment inputs are unchanged.',
        'sections': [
            ('Define a stage as a contract', 'A receipt training pipeline may validate data, assemble features, split cohorts, fit a model and evaluate it. Each stage needs declared inputs, output artifacts and failure conditions. A stage that reads a mutable “latest” table outside its declared inputs cannot be replayed from its run record. Put the dataset snapshot, transformation revision, split policy and runtime image digest in the stage identity. [[mlops/run-manifest-and-artifact-lineage|Training manifests]] connect those identities to the resulting model. Scheduling tells the stage when to run; it does not make its outputs reproducible.'),
            ('Compute cache keys from all effective inputs', 'Caching a feature stage by source-code hash alone is unsafe when the source partition changes. Include exact data artifact digests, code revision, configuration values and environment identity. Conversely, a display-only run label should not invalidate expensive computation. Record the cache hit and its producer run so an auditor can distinguish a reused artifact from a freshly computed one. Randomized stages need a declared seed; nondeterministic hardware kernels may still prevent byte-for-byte reproduction, which should be stated rather than concealed.'),
            ('Keep stages atomic and inspectable', 'Write output to a temporary location, validate it and publish an immutable artifact only after success. A failed stage should not leave a half-written dataset at the path another stage reads. Avoid rerunning the entire pipeline when one evaluation stage fails; reuse valid immutable parents. But if an upstream data correction changes its digest, every dependent stage must be reconsidered. [[mlops/feature-schema-evolution-and-consumers|Feature contract changes]] are particularly easy to omit from cache identity when they live in a separate repository.'),
            ('Test invalidation before trusting the cache', 'Build a fixture where only data changes, one where only feature configuration changes and one where only a run label changes. The first two must miss the cache; the last may hit it. Compare artifact digests and stage metadata after each run. The [[mlops/reproducible-training-run-project|replay project]] asks for the exact inputs that produced a candidate, plus an explicit explanation when a replay is semantically equal but not byte-identical.'),
        ],
        'code': '''import hashlib
import json

def stage_cache_key(stage_name, code_digest, input_digests, config, image_digest):
    if not stage_name or not code_digest or not image_digest:
        raise ValueError("stage, code and image identity are required")
    payload = {"stage": stage_name, "code": code_digest,
               "inputs": input_digests, "config": config,
               "image": image_digest}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()

inputs = {"receipts": "sha256:data-r47"}
first = stage_cache_key("features", "sha256:code-r8", inputs,
                        {"age_cap_days": 3650}, "sha256:image-r6")
assert first == stage_cache_key("features", "sha256:code-r8", inputs,
                                {"age_cap_days": 3650}, "sha256:image-r6")
assert first != stage_cache_key("features", "sha256:code-r8",
                                {"receipts": "sha256:data-r48"},
                                {"age_cap_days": 3650}, "sha256:image-r6")
''',
        'cost': 'Canonicalizing m metadata fields takes O(m) space, while hashing takes O(B) time for B encoded metadata bytes. Computing input digests can require a full scan of large data before a cache lookup. Reuse verified immutable artifact digests when available; a mutable path or timestamp is not a trustworthy substitute.',
        'mistakes': ['Caching on code revision while ignoring changed data.', 'Using a mutable latest-table name as an input identity.', 'Publishing partial stage outputs after failure.', 'Claiming exact reproducibility from a seed while the execution kernel remains nondeterministic.'],
        'related': [M + 'snapshot-split-and-environment-replay', M + 'reproducible-training-run-project', M + 'run-manifest-and-artifact-lineage', M + 'feature-schema-evolution-and-consumers', M + 'model-artifact-digest-and-safe-loading'],
    },
    {
        'path': M + 'snapshot-split-and-environment-replay',
        'title': 'Training replay: freeze the cohort, split and runtime',
        'module': P, 'project': False,
        'summary': 'Reproducing a model requires the same eligible population and split boundary, not merely the same training script.',
        'sections': [
            ('Freeze the population at a declared cutoff', 'A receipt model trained on settled outcomes must name the data snapshot and the latest outcome timestamp allowed into training. An updated table can acquire late labels or corrected rows after the first run. Querying it again by the same date filter may return a different cohort. Store immutable row identifiers or a content-addressed snapshot and record exclusions. [[mlops/prediction-outcome-join-and-maturity|Outcome maturity]] prevents recent unresolved transactions from becoming accidental negative examples.'),
            ('Make the split reproducible and defensible', 'A random seed only repeats a random split for identical ordered rows. If rows arrive in a different order, assignments may change. Use stable entity IDs or persisted split membership, and apply time and group boundaries that match the expected production failure. Keep a final holdout separate from repeated candidate tuning. For receipt fraud, the same merchant or investigation can appear in many records; splitting related records across train and test can overstate performance. [[mlops/retraining-trigger-and-challenger|Challenger comparison]] needs the same frozen evaluation cohort.'),
            ('Pin the execution environment', 'Record interpreter, dependency lock, container digest, hardware class and training configuration. A package update can change preprocessing or numerical behavior without any edit to model code. Capture random seeds and nondeterministic operations, then define what “reproduced” means: identical bytes, metrics within tolerance or matching ranking on a fixed cohort. Choose the claim before rerunning. [[mlops/pipeline-stage-inputs-and-cache-identity|Stage identity]] should include the environment inputs that affect output.'),
            ('Verify replay with a manifest diff', 'Rerun from the frozen snapshot, compare row counts, split membership, feature summaries, evaluation results and artifact digests. If a result differs, identify the earliest stage whose output changed. A perfect metric match does not prove the same model bytes, while a changed digest does not always imply a meaningful quality change. The [[mlops/reproducible-training-run-project|training project]] records both and refuses to call a run identical without evidence.'),
        ],
        'code': '''from hashlib import sha256

def stable_split(entity_id, evaluation_fraction=0.23):
    if not 0 < evaluation_fraction < 1:
        raise ValueError("evaluation fraction must be between zero and one")
    digest = sha256(entity_id.encode()).digest()
    bucket = int.from_bytes(digest[:8], "big") / 2**64
    return "evaluation" if bucket < evaluation_fraction else "training"

merchant_ids = ["merchant-47", "merchant-82", "merchant-129"]
original = {merchant: stable_split(merchant) for merchant in merchant_ids}
reordered = {merchant: stable_split(merchant) for merchant in reversed(merchant_ids)}
assert original == reordered
assert stable_split("merchant-47") == original["merchant-47"]
''',
        'cost': 'Hashing one entity ID costs O(k) time for its encoded length k and O(1) fixed digest space. Assigning n rows is O(total ID bytes). This stable split prevents order-dependent reassignment, but it does not enforce temporal separation; keep a time cutoff and persist membership when evaluation design requires both.',
        'mistakes': ['Assuming a date-filtered mutable table is a frozen snapshot.', 'Using a random seed while row ordering changes.', 'Letting records from the same merchant cross the evaluation boundary.', 'Calling tolerance-level metric agreement byte-for-byte reproduction.'],
        'related': [M + 'pipeline-stage-inputs-and-cache-identity', M + 'reproducible-training-run-project', M + 'run-manifest-and-artifact-lineage', M + 'retraining-trigger-and-challenger', M + 'prediction-outcome-join-and-maturity'],
    },
    {
        'path': M + 'reproducible-training-run-project',
        'title': 'Project: replay a receipt model from frozen training evidence',
        'module': P, 'project': True,
        'summary': 'Build a small training pipeline whose artifacts can be explained, invalidated and compared across reruns.',
        'sections': [
            ('Define the training contract', 'The pipeline consumes a frozen receipt snapshot, an outcome revision cutoff and a feature-contract version. It validates inputs, builds features, assigns stable merchant-level splits, trains a model and evaluates a fixed holdout. Each stage publishes an immutable artifact only after validation passes. [[mlops/pipeline-stage-inputs-and-cache-identity|Stage identities]] include data and configuration, while [[mlops/snapshot-split-and-environment-replay|replay evidence]] records the eligible population and runtime.'),
            ('Construct invalidation fixtures', 'Run the pipeline twice with identical inputs; the second run may reuse verified artifacts. Then change one label revision, one feature threshold and one presentation-only run name. Require the first two to invalidate dependent stages and the last to leave computation unchanged. Include a failed training attempt that writes half an artifact; the publishing step must not expose it. Record cache hits and their producer run IDs so reuse is visible rather than mistaken for fresh work.'),
            ('Compare candidate and incumbent fairly', 'Evaluate the new artifact and current production model on the same frozen holdout and feature availability rules. Check overall loss, urgent-case recall and operational latency. A better average metric cannot waive a protected slice limit. Keep test feedback out of repeated parameter tuning. [[mlops/model-registry-promotion-gates|Promotion gates]] consume the manifest and evaluation results for the exact new artifact digest.'),
            ('Deliver the replay report', 'Produce a manifest with input digests, stage versions, split membership digest, environment digest, model digest and metric-code revision. Report whether a rerun matched bytes, matched metrics within a declared tolerance or differed. Explain the earliest changed stage. A reviewer should be able to reproduce the candidate without consulting a mutable “latest” table or guessing which dependency image ran.'),
        ],
        'code': '''def replay_comparison(expected, observed, metric_tolerance=0.002):
    identity_fields = ("data_digest", "split_digest", "code_digest",
                       "image_digest", "feature_contract")
    changed = [field for field in identity_fields
               if expected.get(field) != observed.get(field)]
    if changed:
        return {"state": "different-inputs", "changed": changed}
    if expected["model_digest"] == observed["model_digest"]:
        return {"state": "byte-identical"}
    delta = abs(expected["holdout_loss"] - observed["holdout_loss"])
    return {"state": "metric-equivalent" if delta <= metric_tolerance
            else "different-result", "loss_delta": delta}

base = {"data_digest": "d47", "split_digest": "s82", "code_digest": "c5",
        "image_digest": "i6", "feature_contract": "receipt-v3",
        "model_digest": "m8", "holdout_loss": 0.173}
assert replay_comparison(base, dict(base))["state"] == "byte-identical"
assert replay_comparison(base, {**base, "data_digest": "d48"})[
    "state"] == "different-inputs"
''',
        'cost': 'Comparing a fixed-size manifest is O(f) time and O(f) space for f identity fields. Training and evaluation dominate runtime; retaining immutable snapshots and artifacts adds storage cost. Metric equivalence is a limited claim, not proof that the same decision function was produced for every input.',
        'mistakes': ['Calling a cached stage freshly executed.', 'Publishing incomplete output after a failed stage.', 'Comparing models on different holdout populations.', 'Using a matching score to claim identical artifact bytes.'],
        'related': [M + 'pipeline-stage-inputs-and-cache-identity', M + 'snapshot-split-and-environment-replay', M + 'run-manifest-and-artifact-lineage', M + 'model-registry-promotion-gates', M + 'trusted-model-promotion-project'],
    },
    {
        'path': M + 'batch-inference-partition-and-idempotency',
        'title': 'Batch inference: make partitions idempotent and outputs identifiable',
        'module': B, 'project': False,
        'summary': 'A batch scoring retry should either reproduce the same partition output or make a new version explicit, never append duplicate decisions.',
        'sections': [
            ('Identify a scoring job completely', 'A nightly receipt job needs a logical partition, input snapshot digest, model digest, feature-contract version and scoring-code revision. A calendar date alone is not enough: a corrected source may be replayed for the same date. Derive a job key from the full identity and write outputs under that key. Each prediction keeps its source record ID and model identity. [[mlops/model-artifact-digest-and-safe-loading|Artifact verification]] ensures the model bytes are the intended version before a partition begins.'),
            ('Publish atomically after reconciliation', 'Write to a temporary location, count inputs and outputs, check unique record IDs and validate failures. Publish a manifest pointer only when the partition is complete. A retry with identical identity can reuse the existing completed output; a retry after code or data changes creates a distinct version. Do not append to a shared “today” file, which can double predictions after a worker crash. A durable store should enforce uniqueness or conditional publication, not rely on a process-local set.'),
            ('Make record failures visible', 'One malformed receipt should have an explicit rejected state rather than silently disappearing. Define whether partial success is allowed and how consumers distinguish completed, incomplete and held partitions. If an output must preserve input order, say so; otherwise join by stable record ID rather than row position. [[mlops/feature-contract-and-admission-gates|Admission rules]] decide which records can be scored, while batch reconciliation accounts for every input.'),
            ('Drill retries and duplicate inputs', 'Kill a worker after it writes half its output, then rerun the same job key. Confirm only one completed manifest is visible. Feed duplicate receipt IDs and a changed model digest into the same date partition; the former must hold or deduplicate under a declared rule, and the latter must create a new output version. The [[mlops/nightly-receipt-batch-project|nightly batch project]] closes the loop with downstream consumption checks.'),
        ],
        'code': '''import hashlib
import json

def batch_job_key(partition, input_digest, model_digest, code_digest):
    identity = {"partition": partition, "input": input_digest,
                "model": model_digest, "code": code_digest}
    if not all(identity.values()):
        raise ValueError("complete batch identity is required")
    encoded = json.dumps(identity, sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()

job = batch_job_key("2026-10-06", "data-47", "model-82", "code-5")
assert job == batch_job_key("2026-10-06", "data-47", "model-82", "code-5")
assert job != batch_job_key("2026-10-06", "data-47", "model-83", "code-5")
''',
        'cost': 'Building the key is O(B) in encoded identity bytes and O(B) temporary space. Scoring n records costs model-dependent inference plus O(n) reconciliation. A production idempotency guarantee needs atomic publish or a store constraint; this function creates identity but cannot prevent two workers from racing to publish.',
        'mistakes': ['Using a date as the only job identity.', 'Appending retry output to a shared file.', 'Joining predictions back to inputs by row order.', 'Treating a partition as complete without accounting for rejected records.'],
        'related': [M + 'batch-replay-versioning-and-consumer-reconciliation', M + 'nightly-receipt-batch-project', M + 'model-artifact-digest-and-safe-loading', M + 'feature-contract-and-admission-gates', M + 'prediction-outcome-join-and-maturity'],
    },
    {
        'path': M + 'batch-replay-versioning-and-consumer-reconciliation',
        'title': 'Batch replay: supersede outputs without duplicating downstream actions',
        'module': B, 'project': False,
        'summary': 'A corrected historical batch is a new decision version; consumers need a clear supersession rule and reconciliation report.',
        'sections': [
            ('Name the purpose of a replay', 'A backfill may reconstruct missing scores, apply a corrected feature value or compare a new model. Those are different operations. A comparison run should not replace production decisions. A correction run may supersede earlier outputs, but only after approval and consumer readiness. Keep original and replacement job keys, the changed input or code, and the effective publication time. [[mlops/batch-inference-partition-and-idempotency|Batch identity]] makes two runs for the same calendar partition distinguishable.'),
            ('Protect downstream side effects', 'A scoring table can be recomputed; a customer email or manual-review assignment may not be safely repeated. Publish outputs to an immutable versioned location and let consumers advance a pointer or process a change feed keyed by decision version. Require idempotency keys for any action. A replay must state whether it is historical analysis or an operational correction. Never send both old and new decisions to an append-only action queue without a supersession protocol.'),
            ('Reconcile old and new populations', 'Count unchanged IDs, added IDs, removed IDs and changed scores. Confirm every input has one scored, rejected or held outcome. If a source correction removes a receipt, do not leave its old score silently active. Record tombstones or explicit withdrawal events where the consumer contract requires them. [[mlops/prediction-outcome-join-and-maturity|Outcome joins]] should preserve which decision version an outcome evaluates; a replayed score is not a retroactive production prediction.'),
            ('Gate publication with a diff', 'Review a sample of changed decisions and all high-impact changes before switching the active pointer. Simulate a downstream consumer that has not acknowledged the new version and hold publication. The [[mlops/nightly-receipt-batch-project|batch project]] checks record accounting, supersession and no duplicate customer action under replay. Store the diff manifest for audit and rollback.'),
        ],
        'code': '''def reconcile_batch(previous, replacement):
    old_ids, new_ids = set(previous), set(replacement)
    shared = old_ids & new_ids
    changed = {receipt_id for receipt_id in shared
               if previous[receipt_id] != replacement[receipt_id]}
    return {"added": sorted(new_ids - old_ids),
            "removed": sorted(old_ids - new_ids),
            "changed": sorted(changed),
            "unchanged_count": len(shared - changed)}

old = {"receipt-47": "review", "receipt-82": "clear"}
new = {"receipt-47": "clear", "receipt-129": "review"}
assert reconcile_batch(old, new) == {
    "added": ["receipt-129"], "removed": ["receipt-82"],
    "changed": ["receipt-47"], "unchanged_count": 0}
''',
        'cost': 'Diffing two maps with n and m IDs takes O(n + m) expected time and O(n + m) space; sorting output lists adds O(k log k) for k changed IDs. Keeping versions costs storage, but it is safer than overwriting a production output with no way to explain changed downstream actions.',
        'mistakes': ['Treating a model-comparison replay as an approved operational correction.', 'Sending replayed decisions through the original action queue.', 'Ignoring receipts removed by a corrected source snapshot.', 'Joining an outcome to a replayed score instead of its original production decision.'],
        'related': [M + 'batch-inference-partition-and-idempotency', M + 'nightly-receipt-batch-project', M + 'prediction-outcome-join-and-maturity', M + 'label-corrections-and-evaluation-ledger', M + 'run-manifest-and-artifact-lineage'],
    },
    {
        'path': M + 'nightly-receipt-batch-project',
        'title': 'Project: publish and replay a nightly receipt scoring partition',
        'module': B, 'project': True,
        'summary': 'Run a versioned receipt scoring batch, recover from partial failure and reconcile a corrected replay before consumers act.',
        'sections': [
            ('Set the batch contract', 'At 02:00, score a frozen receipt partition with one verified model digest and feature-contract version. Give the job a key derived from partition, data, model and code identities. Each input must end as scored, rejected or held, with a stable receipt ID. [[mlops/batch-inference-partition-and-idempotency|Idempotent publication]] keeps partial output invisible until counts and uniqueness checks pass.'),
            ('Prepare failure fixtures', 'Include 529 valid receipts, one malformed amount, duplicate IDs, a worker crash halfway through a write and a retry with the same job key. A corrected source snapshot removes one receipt and changes another. Freeze expected output counts and changed-ID sets before running. Use a distinct model digest for a comparison-only replay to prove that comparison results never move the production pointer.'),
            ('Stage, verify and publish', 'Validate input identity and model artifact, write a temporary output, reconcile source IDs with scored and rejected IDs, then publish one immutable manifest. Retry a failed job without appending duplicate results. For a corrected replay, compare old and new outputs and require downstream consumers to acknowledge the supersession protocol. [[mlops/batch-replay-versioning-and-consumer-reconciliation|Replay reconciliation]] exposes removed, added and changed decisions.'),
            ('Test consumer behavior', 'Simulate a manual-review service keyed by receipt and decision version. The same completed batch must not create a second review task. A correction may update an existing task only under an explicit rule; a comparison run must create none. Report time to complete, per-record failures, duplicate prevention, diff counts and the active output manifest. Keep the old version available for audit and rollback until retention policy permits deletion.'),
        ],
        'code': '''def batch_accounting(input_ids, scored_ids, rejected_ids):
    inputs = list(input_ids)
    scored, rejected = set(scored_ids), set(rejected_ids)
    if len(inputs) != len(set(inputs)):
        return {"state": "hold", "reason": "duplicate-input"}
    if scored & rejected:
        return {"state": "hold", "reason": "conflicting-outcome"}
    if scored | rejected != set(inputs):
        return {"state": "hold", "reason": "incomplete-partition"}
    return {"state": "publish", "input_count": len(inputs)}

receipts = ["receipt-47", "receipt-82", "receipt-129"]
assert batch_accounting(receipts, receipts[:2], receipts[2:])[
    "state"] == "publish"
assert batch_accounting(receipts, receipts[:1], receipts[2:])[
    "state"] == "hold"
''',
        'cost': 'Accounting uses O(n) expected time and O(n) space for n input IDs. Inference, storage and downstream reconciliation dominate a real batch. This set-based check is local; atomic publication and cross-worker idempotency require durable conditional writes or database constraints.',
        'mistakes': ['Exposing half a partition after a worker crash.', 'Dropping malformed records without a rejected outcome.', 'Creating duplicate review tasks on retry.', 'Publishing a comparison replay as if it replaced production decisions.'],
        'related': [M + 'batch-inference-partition-and-idempotency', M + 'batch-replay-versioning-and-consumer-reconciliation', M + 'model-artifact-digest-and-safe-loading', M + 'receipt-feature-admission-project', M + 'prediction-outcome-join-and-maturity'],
    },
]

crosslinks = [
    (M + 'run-manifest-and-artifact-lineage', M + 'pipeline-stage-inputs-and-cache-identity'),
    (M + 'retraining-trigger-and-challenger', M + 'snapshot-split-and-environment-replay'),
    (M + 'trusted-model-promotion-project', M + 'reproducible-training-run-project'),
    (M + 'model-artifact-digest-and-safe-loading', M + 'batch-inference-partition-and-idempotency'),
    (M + 'prediction-outcome-join-and-maturity', M + 'batch-replay-versioning-and-consumer-reconciliation'),
    (M + 'receipt-triage-release-project', M + 'nightly-receipt-batch-project'),
]

if __name__ == '__main__':
    publish(lessons, (P, B), crosslinks,
            'aitrove-mlops-pipelines-batch-import-20261006.json', 6112,
            subject='mlops', hub_path=M + 'mlops-tutorial')
