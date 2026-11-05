"""Publish optimized-model release and training-data incident modules."""
from de_batch_publisher import publish

M = 'mlops/'
O = 'Optimized model releases and numerical parity'
P = 'Training-data poisoning and recovery'

lessons = [
    {
        'path': M + 'optimized-model-calibration-and-parity',
        'title': 'Optimized model release: calibration, score drift and parity',
        'module': O, 'project': False,
        'summary': 'Treat quantization or mixed precision as a new model release whose scores and routes must be checked against the original.',
        'sections': [
            ('Freeze the conversion input', 'A receipt-risk classifier exported for faster inference has at least two relevant artifacts: the approved full-precision model and the converted candidate. Record both digests, conversion tool revision, operator set, quantization configuration, preprocessing digest and calibration snapshot. A calibration set is an input to the release, not an anonymous tuning convenience. It must represent normal input ranges and approved slices without borrowing the final evaluation set. Keep [[mlops/run-manifest-and-artifact-lineage|run lineage]] and [[mlops/model-artifact-digest-and-safe-loading|artifact identity]] attached to the candidate.'),
            ('Compare decisions, not only averages', 'A small mean score difference can hide a route flip for a receipt near the manual-review threshold. Replay a frozen evaluation set through both artifacts with the same input features and runtime contract. Compare score error distribution, prediction agreement, threshold crossings and quality by merchant cohort, device class and scan quality. Keep an explicit allowance for numerical differences; byte equality is usually the wrong requirement. [[mlops/score-threshold-policy-and-change-control|Threshold policy]] determines which score differences matter operationally.'),
            ('Debug where the loss starts', 'When a slice fails, inspect preprocessing parity first, then intermediate activations or per-layer error where the runtime supports them. Poor calibration coverage can distort ranges; an unsupported operator can force a slow or numerically different fallback. Change one conversion setting at a time and repeat the frozen replay. Do not tune on the held-out decision audit until it passes. [[mlops/slice-quality-gates-and-uncertainty|Slice gates]] keep a global pass from hiding a concentrated failure.'),
            ('Define the release contract', 'Publish the candidate with the original model and a reversible pointer. The gate must name the benchmark dataset digest, allowed score-distance measure, maximum threshold-flip count, latency budget and target runtime. A pass on one machine says nothing about another execution provider. [[mlops/optimized-model-hardware-matrix-and-fallback|The hardware matrix]] supplies that part of the contract; [[mlops/receipt-optimized-inference-project|the project]] shows a candidate with attractive median latency that still fails its boundary cohort.'),
        ],
        'code': '''def parity_gate(reference_scores, candidate_scores, threshold, max_error):
    if len(reference_scores) != len(candidate_scores) or not reference_scores:
        raise ValueError("paired nonempty scores required")
    if not 0 <= threshold <= 1 or max_error < 0:
        raise ValueError("invalid gate")
    distances = [abs(reference - candidate) for reference, candidate
                 in zip(reference_scores, candidate_scores)]
    flips = sum((reference >= threshold) != (candidate >= threshold)
                for reference, candidate in zip(reference_scores, candidate_scores))
    return {"max_error": max(distances), "route_flips": flips,
            "release": max(distances) <= max_error and flips == 0}

reference = [0.14, 0.48, 0.77, 0.91]
candidate = [0.15, 0.51, 0.75, 0.90]
assert not parity_gate(reference, candidate, 0.50, 0.04)["release"]
assert parity_gate(reference, [0.15, 0.47, 0.75, 0.90], 0.50, 0.04)["release"]
''',
        'cost': 'The paired pass is O(n) time and O(n) extra space for n scores; it can be O(1) extra space if distances are reduced as they arrive. Generating candidate scores dominates compute cost. Calibration and replay consume dataset storage, accelerator time and reviewer effort. A narrower error allowance reduces numerical drift but may reject a useful conversion, so set it against route consequences rather than a convenient round number.',
        'mistakes': ['Approving a converted model from file size or median latency alone.', 'Calibrating on the same held-out set used for final approval.', 'Comparing scores without the route threshold.', 'Losing the conversion configuration or the original model digest.'],
        'related': [M + 'optimized-model-hardware-matrix-and-fallback', M + 'receipt-optimized-inference-project', M + 'score-threshold-policy-and-change-control', M + 'slice-quality-gates-and-uncertainty', M + 'run-manifest-and-artifact-lineage'],
    },
    {
        'path': M + 'optimized-model-hardware-matrix-and-fallback',
        'title': 'Hardware matrix for optimized models: provider support and fallback',
        'module': O, 'project': False,
        'summary': 'A converted model can run slower, use more memory or fail on a different processor; qualify the actual serving fleet.',
        'sections': [
            ('Name the real target fleet', 'Inventory CPU instruction class, accelerator, runtime build, execution provider, memory limit and app version for each serving cohort. “GPU” is not a hardware specification. Some hosts can execute a quantized graph but lack the fast operator implementation; they silently dequantize or move part of the graph to the CPU. Record the actual provider selected at load time, not merely the preferred provider in configuration. [[mlops/edge-model-manifests-and-cohort-rollouts|Edge release manifests]] need the same capability check.'),
            ('Benchmark the full request path', 'Measure warm and cold initialization, preprocessing, inference, postprocessing, peak memory, p50 and tail latency at a defined concurrency. Compare with the existing artifact on identical input batches and host classes. Include throttled devices and small batches; a throughput win on a full accelerator can become a tail-latency loss at low traffic. Track fallback count and provider partition changes. [[mlops/inference-chain-contracts-and-stage-identity|Inference chain identity]] makes the two benchmarks comparable.'),
            ('Route unsupported hosts explicitly', 'The release manifest maps each qualified hardware class to a tested artifact and runtime. Unknown classes retain the approved baseline or enter a controlled hold. Do not assume an optimized artifact is universally smaller in memory after runtime graph expansion. A class that fails correctness or latency must not receive the candidate, even if the aggregate fleet metric passes. Preserve a rollback package on each host and test that it loads under the current runtime. [[mlops/promotion-attestation-and-reversible-pointer|The promotion pointer]] must resolve to a compatible artifact.'),
            ('Watch the deployed execution path', 'Emit model digest, runtime revision, selected provider and hardware class with sampled decision telemetry. A new host image or driver can change provider choice without changing the model digest. Alert on unexpected fallback and tail-latency regressions by class; a single global average conceals both. [[mlops/receipt-optimized-inference-project|The project]] qualifies three host classes and deliberately holds one that loses its accelerator path. Re-run the matrix when runtime, driver or graph settings change.'),
        ],
        'code': '''def qualified_artifact(host, matrix, baseline_digest):
    key = (host["hardware"], host["runtime"], host["provider"])
    qualification = matrix.get(key)
    if qualification is None or not qualification["parity_passed"]:
        return baseline_digest
    if qualification["p99_ms"] > qualification["p99_budget_ms"]:
        return baseline_digest
    return qualification["artifact_digest"]

matrix = {("arm-r5", "ort-r8", "cpu-int8"):
          {"parity_passed": True, "p99_ms": 63, "p99_budget_ms": 82,
           "artifact_digest": "receipt-int8-47"}}
host = {"hardware": "arm-r5", "runtime": "ort-r8", "provider": "cpu-int8"}
assert qualified_artifact(host, matrix, "receipt-fp32-31") == "receipt-int8-47"
assert qualified_artifact({**host, "provider": "cpu-fallback"}, matrix,
                          "receipt-fp32-31") == "receipt-fp32-31"
''',
        'cost': 'Lookup is O(1) expected time and space after a qualification matrix exists. Matrix construction scales with artifact variants, hardware classes and workloads; each cell needs correctness and performance runs. Retaining a baseline costs storage but bounds an unsupported-provider failure. More variants can improve fleet coverage while increasing validation and rollback work.',
        'mistakes': ['Reading configured provider as proof the provider actually executed.', 'Using one accelerator benchmark for all host classes.', 'Ignoring model-load memory and cold-start time.', 'Letting unknown hardware receive an unqualified optimized artifact.'],
        'related': [M + 'optimized-model-calibration-and-parity', M + 'receipt-optimized-inference-project', M + 'edge-model-manifests-and-cohort-rollouts', M + 'inference-chain-contracts-and-stage-identity', M + 'promotion-attestation-and-reversible-pointer'],
    },
    {
        'path': M + 'receipt-optimized-inference-project',
        'title': 'Project: release a faster receipt model without changing review routes',
        'module': O, 'project': True,
        'summary': 'Convert a receipt-risk classifier, test score and route parity, qualify hardware classes and stage a reversible rollout.',
        'sections': [
            ('Prepare the release packet', 'Start with a pinned full-precision receipt-risk model, preprocessing digest and threshold policy. Create a candidate from a recorded conversion configuration and a calibration snapshot that excludes final evaluation receipts. Record the candidate digest and runtime build. The business contract is unchanged: receipts above the review threshold still go to review, and missing fields still take the existing fallback route. [[mlops/optimized-model-calibration-and-parity|Numerical parity]] is a separate acceptance gate from [[mlops/optimized-model-hardware-matrix-and-fallback|hardware qualification]].'),
            ('Run the frozen replay', 'Replay 4,700 paired decisions covering ordinary scans, blurred images, short receipts, high-value purchases and a dense band around the review threshold. Preserve each decision ID so discrepancies are traceable. Compare maximum and percentile score error, route flips and slice-level quality. A candidate that reduces median inference from 51 to 34 milliseconds but moves four borderline receipts away from manual review is held; latency cannot waive the route contract. Investigate calibration coverage before changing the business threshold.'),
            ('Qualify each deployment cell', 'Benchmark the corrected candidate on the production ARM CPU, a newer accelerator node and an older fallback node at fixed concurrency. Record selected provider, warm and cold latency, p99, peak memory and the baseline comparison. The older node dequantizes part of the graph and exceeds its p99 budget, so it keeps the full-precision artifact. Verify the baseline still loads after the runtime upgrade. [[mlops/edge-offline-telemetry-and-rollback|Offline telemetry]] is relevant if the ARM cohort includes handhelds.'),
            ('Ship with an evidence-backed pointer', 'Stage a small compatible cohort, compare observed route rates and latency by hardware class, then expand only after enough exposed decisions arrive. The release packet contains the conversion recipe, calibration and evaluation digests, hardware matrix, threshold-flip report, rollback digest and cohort observation window. [[mlops/promotion-attestation-and-reversible-pointer|Reversible promotion]] moves each class independently. A runtime or driver change invalidates the corresponding performance cell even when the artifact bytes do not change.'),
        ],
        'code': '''def receipt_optimized_release(cells, route_flips):
    if route_flips < 0:
        raise ValueError("negative route flips")
    if route_flips:
        return "hold:route-parity"
    if not cells:
        return "hold:no-hardware-evidence"
    if any(not cell["provider_verified"] or cell["p99_ms"] > cell["budget_ms"]
           for cell in cells):
        return "partial:baseline-on-failing-cells"
    return "stage:candidate"

cells = [{"provider_verified": True, "p99_ms": 69, "budget_ms": 84},
         {"provider_verified": False, "p99_ms": 91, "budget_ms": 84}]
assert receipt_optimized_release(cells, 4) == "hold:route-parity"
assert receipt_optimized_release(cells, 0) == "partial:baseline-on-failing-cells"
assert receipt_optimized_release(cells[:1], 0) == "stage:candidate"
''',
        'cost': 'The disposition loop is O(h) time and O(1) extra space for h hardware cells; paired score replay is O(n) across n receipts. The large cost is executing both models, keeping representative snapshots and benchmarking every supported cell. Partial rollout preserves a storage copy of the baseline and adds a temporary mixed-fleet burden, but avoids treating an incompatible host as a release success.',
        'mistakes': ['Waiving route flips because average accuracy stays flat.', 'Claiming a fleet-wide speedup from one fast host.', 'Changing the threshold to compensate for conversion drift.', 'Omitting the baseline load test after a runtime upgrade.'],
        'related': [M + 'optimized-model-calibration-and-parity', M + 'optimized-model-hardware-matrix-and-fallback', M + 'promotion-attestation-and-reversible-pointer', M + 'slice-quality-gates-and-uncertainty', M + 'edge-offline-telemetry-and-rollback'],
    },
    {
        'path': M + 'training-source-admission-and-quarantine',
        'title': 'Training source admission: provenance, trust tiers and quarantine',
        'module': P, 'project': False,
        'summary': 'A retraining feed needs source identity and a quarantine route before its examples can influence a production model.',
        'sections': [
            ('Define who can contribute examples', 'A receipt classifier may train from reviewed customer submissions, partner imports and correction queues. Those sources have different controls and incentives. Assign each record an immutable source ID, collection window, ingestion batch, reviewer or automated label channel, consent and retention status. A row without origin should not enter an approved snapshot merely because its schema is valid. [[mlops/feature-contract-and-admission-gates|Feature admission]] checks shape and meaning; source admission checks whether the record is trusted for this training purpose.'),
            ('Separate quality defects from hostile influence', 'A sudden burst of one merchant category, duplicated images with contradictory labels or labels that change only near the review threshold deserves investigation. It may be pipeline failure, coordinated abuse or a legitimate seasonal shift. Do not claim an attack from a statistical anomaly alone. Keep rate, duplicate and disagreement signals by source and time, then obtain independent evidence. [[mlops/label-corrections-and-evaluation-ledger|The label ledger]] records corrections without silently rewriting the past.'),
            ('Quarantine by lineage', 'When a batch is suspect, freeze its immutable identifier, prevent it from entering the next snapshot and record the reason and investigator. Quarantine is reversible only through a reviewed decision. Preserve a safe snapshot pointer and a list of affected training runs, challenger models and evaluation sets. A suspicious record can contaminate both model fitting and the apparent validation result, so test-set lineage also matters. [[mlops/snapshot-split-and-environment-replay|Snapshot replay]] gives a route back to the exact accepted inputs.'),
            ('Admit only after review', 'Review sampled raw evidence within privacy limits, compare against a trusted independent channel and decide whether to reject, relabel or accept the batch. If the source is compromised, pause future ingestion until its controls change. Document the evidence and all affected artifact digests; do not merely delete suspect rows from a mutable table. [[mlops/poisoning-signal-triage-and-clean-retrain|The triage playbook]] determines whether a retrain is needed, and [[mlops/receipt-training-source-incident-project|the project]] walks through an ambiguous partner-label surge.'),
        ],
        'code': '''def admit_training_batch(batch, approved_sources, quarantined_batches):
    if not batch.get("batch_id") or not batch.get("source_id"):
        return "reject:missing-lineage"
    if batch["batch_id"] in quarantined_batches:
        return "hold:quarantine"
    if batch["source_id"] not in approved_sources:
        return "hold:unapproved-source"
    if not batch.get("retention_approved"):
        return "reject:retention"
    return "admit"

batch = {"batch_id": "partner-47", "source_id": "partner-r8",
         "retention_approved": True}
assert admit_training_batch(batch, {"partner-r8"}, set()) == "admit"
assert admit_training_batch(batch, {"partner-r8"}, {"partner-47"}) == "hold:quarantine"
assert admit_training_batch({**batch, "source_id": "unknown"},
                            {"partner-r8"}, set()) == "hold:unapproved-source"
''',
        'cost': 'Admission lookup is O(1) expected time and space for indexed source and quarantine sets. Persistent provenance adds storage per record or batch and review latency for held data. Overly broad quarantine slows legitimate retraining; overly narrow quarantine lets a contaminated snapshot through. Bound each hold to a concrete lineage scope and an accountable review.',
        'mistakes': ['Treating a schema-valid row as a trusted training example.', 'Calling every distribution shift a poisoning attack.', 'Quarantining mutable table rows without preserving batch identity.', 'Checking training rows while ignoring validation-set contamination.'],
        'related': [M + 'poisoning-signal-triage-and-clean-retrain', M + 'receipt-training-source-incident-project', M + 'label-corrections-and-evaluation-ledger', M + 'snapshot-split-and-environment-replay', M + 'feature-contract-and-admission-gates'],
    },
    {
        'path': M + 'poisoning-signal-triage-and-clean-retrain',
        'title': 'Poisoning signal triage: isolate influence and recover a clean model',
        'module': P, 'project': False,
        'summary': 'Investigate suspicious training influence with comparison runs, clean reference data and a reversible production response.',
        'sections': [
            ('Start with observable symptoms', 'A rise in false negatives for high-value receipts after a partner batch arrived may indicate poisoned labels, a parser defect, delayed ground truth or a real behavior change. Align the first bad decision window with source ingestion, training run, evaluation snapshot and promotion timeline. Keep the hypothesis open. [[mlops/incident-triage-and-evidence-timeline|The incident timeline]] links those facts; [[mlops/training-source-admission-and-quarantine|source admission]] provides a safe hold while investigation continues.'),
            ('Measure influence without leaking the suspect set', 'Compare the candidate trained with the suspect batch against a run that excludes only that batch, using the same code, seed policy, clean training base and independent frozen evaluation set. Look at route flips and slice deltas, not just global score. If the clean reference set shares the compromised source, the comparison cannot settle the question. Avoid “test until it passes” on the same held-out examples. Use a second review set or adjudicated outcomes when available. [[mlops/slice-quality-gates-and-uncertainty|Uncertainty-aware slice gates]] keep small cohorts honest.'),
            ('Contain the current serving effect', 'If a suspect trained model is live, identify every serving digest and cohort exposed to it. Repoint to the last approved unaffected artifact or apply a reviewed conservative route policy while that artifact loads. Preserve decision logs needed for later outcome review under the existing privacy policy. Quarantine the batch and pause automatic retraining triggers; otherwise the same data can re-enter a fresh candidate. [[mlops/promotion-attestation-and-reversible-pointer|Reversible pointers]] reduce response time when the prior package is still compatible.'),
            ('Close with a reproducible recovery', 'Rebuild from an accepted snapshot whose source manifest excludes the suspect batch. Re-run quality, calibration and serving-contract checks, then stage promotion with an explicit incident link. Keep the quarantined evidence and exclusion decision in a restricted ledger; do not erase records so completely that the event cannot be explained. Reopen the source only after its admission controls change. [[mlops/receipt-training-source-incident-project|The project]] includes a deceptive pass on global accuracy and a failure on a targeted cohort.'),
        ],
        'code': '''def retrain_incident_gate(clean_slice_error, suspect_slice_error,
                          clean_reference_independent, suspected_batch_quarantined):
    if min(clean_slice_error, suspect_slice_error) < 0:
        raise ValueError("negative error count")
    if not clean_reference_independent:
        return "hold:reference-contaminated"
    if not suspected_batch_quarantined:
        return "hold:batch-still-admitted"
    if suspect_slice_error > clean_slice_error:
        return "investigate:batch-influence"
    return "review:other-causes"

assert retrain_incident_gate(3, 12, True, True) == "investigate:batch-influence"
assert retrain_incident_gate(3, 12, False, True) == "hold:reference-contaminated"
assert retrain_incident_gate(3, 12, True, False) == "hold:batch-still-admitted"
''',
        'cost': 'The toy gate is O(1) time and space, while the actual comparison may require two full training runs, fresh evaluation and reviewer time. Retaining clean reference sets costs storage and access control. Excluding one batch isolates a hypothesis only when all other training inputs and evaluation conditions are held fixed; it does not prove malicious intent.',
        'mistakes': ['Declaring an attack from a single anomalous slice.', 'Comparing runs that also changed code, hyperparameters or evaluation data.', 'Rolling back a model while automatic retraining still reads the suspect batch.', 'Using a contaminated validation set as proof of recovery.'],
        'related': [M + 'training-source-admission-and-quarantine', M + 'receipt-training-source-incident-project', M + 'incident-triage-and-evidence-timeline', M + 'promotion-attestation-and-reversible-pointer', M + 'slice-quality-gates-and-uncertainty'],
    },
    {
        'path': M + 'receipt-training-source-incident-project',
        'title': 'Project: investigate suspect receipt labels and rebuild safely',
        'module': P, 'project': True,
        'summary': 'Contain an abnormal partner-label batch, test its influence and restore a receipt-risk model from accepted source lineage.',
        'sections': [
            ('Freeze the evidence', 'A partner feed contributes 8,200 reviewed receipt labels. One afternoon, the share of “safe” labels rises sharply among high-value blurry scans. Preserve batch IDs, source identity, ingestion time, reviewer channel, deduplication fingerprints and the training runs that consumed them. The change may reflect a labeling UI bug or coordinated manipulation; record both hypotheses. [[mlops/training-source-admission-and-quarantine|Source admission]] blocks the batch from future snapshots while the team investigates. No raw receipt images belong in general incident dashboards.'),
            ('Trace training and serving exposure', 'Build a lineage graph from the batch to the next training snapshot, candidate digest, promotion event and serving cohorts. The candidate shows unchanged global accuracy but more false negatives for high-value blurry scans. Identify decisions made by the candidate and keep their route and model digest for later adjudication. If that model is live, stage the previous unaffected digest, verify its runtime compatibility and compare routes before expanding rollback. [[mlops/incident-triage-and-evidence-timeline|The evidence timeline]] separates when labels arrived from when the model began serving.'),
            ('Run a controlled comparison', 'Train one run with all previously accepted inputs and one run with the suspect batch, keeping code, preprocessing and split policy fixed. Evaluate on an independent adjudicated set that excludes the partner feed. Report uncertainty for the affected slice and inspect whether duplicate or conflicting labels cluster by submitter. A larger error count in the suspect run supports batch influence, not proof of hostile intent. [[mlops/poisoning-signal-triage-and-clean-retrain|The triage procedure]] defines that limit.'),
            ('Recover and reopen carefully', 'Publish a clean snapshot manifest, replacement model digest, slice report, threshold crossing report and rollback observation. Keep the partner source paused until the labeling path is repaired and a sampled independent review passes. Record whether affected customer decisions need review under the product policy. The project is complete only when automatic retraining excludes the held batch, the clean candidate passes normal promotion gates and the source reopening decision has an owner. [[mlops/retraining-trigger-and-challenger|Retraining triggers]] resume after those controls are verified.'),
        ],
        'code': '''def incident_batch_disposition(batch_id, quarantined, clean_reference,
                               clean_slice_errors, suspect_slice_errors):
    if not batch_id:
        raise ValueError("batch id required")
    if not quarantined or not clean_reference:
        return "hold:containment-or-reference"
    if clean_slice_errors < 0 or suspect_slice_errors < 0:
        raise ValueError("invalid errors")
    if suspect_slice_errors > clean_slice_errors:
        return "rebuild:accepted-snapshot"
    return "investigate:other-cause"

assert incident_batch_disposition("partner-47", True, True, 4, 13) == \
       "rebuild:accepted-snapshot"
assert incident_batch_disposition("partner-47", False, True, 4, 13) == \
       "hold:containment-or-reference"
assert incident_batch_disposition("partner-47", True, True, 4, 4) == \
       "investigate:other-cause"
''',
        'cost': 'The disposition check is O(1), but lineage traversal grows with affected batches, runs, artifacts and cohorts. A controlled rebuild consumes another training run and independent adjudication. Quarantine delays model freshness; keep the known-good artifact serving while this cost is paid. Do not trade away clean-reference independence to shorten the incident.',
        'mistakes': ['Deleting the suspicious batch before recording its lineage.', 'Assuming unchanged global accuracy means the model is safe.', 'Calling a partner malicious before ruling out a label workflow defect.', 'Resuming automatic retraining while the held batch remains in an input view.'],
        'related': [M + 'training-source-admission-and-quarantine', M + 'poisoning-signal-triage-and-clean-retrain', M + 'snapshot-split-and-environment-replay', M + 'retraining-trigger-and-challenger', M + 'incident-triage-and-evidence-timeline'],
    },
]

crosslinks = [
    (M + 'run-manifest-and-artifact-lineage', M + 'optimized-model-calibration-and-parity'),
    (M + 'edge-model-manifests-and-cohort-rollouts', M + 'optimized-model-hardware-matrix-and-fallback'),
    (M + 'promotion-attestation-and-reversible-pointer', M + 'receipt-optimized-inference-project'),
    (M + 'feature-contract-and-admission-gates', M + 'training-source-admission-and-quarantine'),
    (M + 'incident-triage-and-evidence-timeline', M + 'poisoning-signal-triage-and-clean-retrain'),
    (M + 'retraining-trigger-and-challenger', M + 'receipt-training-source-incident-project'),
]

if __name__ == '__main__':
    publish(lessons, (O, P), crosslinks,
            'aitrove-mlops-optimization-poisoning-import-20261006.json', 6172,
            subject='mlops', hub_path=M + 'mlops-tutorial')
