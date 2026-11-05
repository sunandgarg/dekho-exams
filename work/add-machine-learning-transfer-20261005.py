"""Add original transfer-learning lessons and a target-domain release review."""
from ml_fixture_writer_20261005 import publish_batch

lessons = []


def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='machine-learning/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))


add('pretrained-encoder-target-contract',
    'Pretrained encoder and target-task contract',
    'Transfer learning reuses a representation learned elsewhere, but the target task still needs its own label, input, split and evaluation contract.', [
    ('Separate representation from decision', 'A pretrained image encoder turns a parcel photo into a feature vector. A new head predicts whether the parcel needs damage review. The source model’s original label set does not define the target label or intervention. Write the target unit, photograph timing, positive class and review action before extracting features. [[computer-vision/image-unit-label-and-consent|The image-unit guide]] covers the difference between a photo, parcel and shipment as an evaluation unit.'),
    ('Pin preprocessing with the weights', 'The encoder expects an input shape, channel order, pixel range, normalization and crop rule. Changing any of these can change embeddings even when the weights stay fixed. Store the complete preprocessing contract with the encoder version and head. The code compares an observed input against a declared contract; it is a validation guard, not a substitute for checking image quality. [[computer-vision/pixel-geometry-and-preprocessing|Pixel geometry]] and [[computer-vision/augmentation-and-serving-parity|serving parity]] address adjacent failures.'),
    ('Establish the target split before adaptation', 'Photos of the same parcel, burst capture or depot incident belong on one side of each split. A frozen encoder does not prevent leakage if near-duplicate target photos appear in both training and evaluation. Use a later depot or period for an honest target test where deployment differs. [[computer-vision/grouped-evaluation-and-shift|Grouped evaluation]] is the relevant boundary.'),
    ('Check that the source can be used', 'Track the source checkpoint identifier, permitted use, training-data description where available, known exclusions and security review. A source representation can be technically useful yet unsuitable because of licensing, privacy or input-data restrictions. Do not assert an unknown source dataset has no overlap with target evaluation images. [[machine-learning/pretraining-overlap-and-provenance-audit|The provenance audit]] records what can and cannot be verified.'),
    ('Define a baseline before claiming transfer', 'Compare a frozen encoder plus small head against an operational rule and a target-only model where feasible. Use the same target test, threshold and review cost for each. A lower training loss says little about the new depot. [[machine-learning/frozen-embedding-linear-probe|The linear probe]] gives a cheap first adaptation; [[machine-learning/negative-transfer-by-target-slice|the slice audit]] checks whether any gain survives target variation.')],
    '''encoder_contract = {
    "checkpoint_id": "parcel-vision-v4",
    "height": 224,
    "width": 224,
    "channels": 3,
    "pixel_min": 0.0,
    "pixel_max": 1.0,
    "target_positive": "damage-review",
}
incoming_image = {"height": 224, "width": 224, "channels": 3,
                  "pixel_min": 0.0, "pixel_max": 1.0}

def validate_encoder_input(contract, observed):
    required = ("height", "width", "channels", "pixel_min", "pixel_max")
    mismatches = [field for field in required
                  if contract[field] != observed.get(field)]
    return mismatches

assert validate_encoder_input(encoder_contract, incoming_image) == []
assert validate_encoder_input(
    encoder_contract, {**incoming_image, "channels": 1}
) == ["channels"]''',
    'Checking K contract fields is O(K) time and O(K) mismatch storage. Extracting an embedding costs the encoder’s inference compute and its input tensor memory; caching vectors trades storage for repeated inference. The largest hidden cost is collecting an independent, correctly labeled target test cohort.',
    ['Do not reuse the source task’s label meaning as the target label.', 'Do not change normalization or crop rules between training and serving.', 'Do not claim source-data independence when the pretraining manifest is unavailable.'],
    ['machine-learning/frozen-embedding-linear-probe','machine-learning/staged-fine-tuning-and-checkpoint-selection','machine-learning/pretraining-overlap-and-provenance-audit','machine-learning/transfer-learning-release-review-project'])


add('frozen-embedding-linear-probe',
    'Frozen embeddings and a linear probe',
    'A linear probe trains a small classifier on fixed target embeddings to test whether the pretrained representation separates the new labels without updating the encoder.', [
    ('Keep the encoder fixed', 'Encode parcel photos once with a pinned model and preprocessing contract. Train the probe only on target training parcels; use a separate development group to choose regularization and threshold. Because the encoder does not update, the probe isolates how useful its existing features are for the target task. [[machine-learning/pretrained-encoder-target-contract|The contract guide]] pins the representation and target definition.'),
    ('Make the small head real', 'The code fits a two-feature logistic head with batch gradient steps and L2 penalty on the weights. It operates on already-extracted embeddings so it runs without a large image library. Production code should use a tested numerical implementation, standardize dimensions using training-only statistics when appropriate, and monitor convergence. The result is a real training loop, not a line-by-line stand-in for full image model training. [[machine-learning/logistic-regression-log-loss-and-odds|Log loss]] explains the objective.'),
    ('Test the right baseline', 'A visually similar source task may still encode the wrong signal for torn seals, glare or lighting at the target depot. Compare the probe with an operational heuristic and, if labels permit, a target-only model. Keep the same parcel-grouped split, decision threshold and false-negative cost. [[computer-vision/grouped-evaluation-and-shift|Grouped evaluation]] prevents repeated photos from inflating the result.'),
    ('Read probe success carefully', 'A strong probe shows that a simple head can extract useful information from the frozen vectors on this evaluation set. It does not prove every target subgroup is covered, that the representation is causal, or that unfreezing layers would help. Inspect error by camera, packaging material and depot. [[machine-learning/negative-transfer-by-target-slice|The target-slice audit]] compares paired errors and support.'),
    ('Measure the serving path', 'Caching embeddings accelerates repeated experiments but the live service still runs the encoder unless vectors already exist at decision time. Report end-to-end latency, memory and the fallback if feature extraction fails. [[deep-learning/inference-schema-and-latency|Inference contracts]] put the head’s small compute in context. [[machine-learning/staged-fine-tuning-and-checkpoint-selection|Staged tuning]] is a later comparison, not a prerequisite.')],
    '''from math import exp

# Fixed embeddings from a pinned encoder; labels come from target parcels.
training_parcels = [
    ((-1.4, -0.8), 0), ((-1.0, -1.2), 0), ((-0.8, -0.6), 0),
    ((0.7, 0.9), 1), ((1.2, 0.8), 1), ((0.9, 1.3), 1),
]

def train_damage_probe(rows, steps=180, rate=0.25, penalty=0.02):
    weights = [0.0, 0.0]
    bias = 0.0
    for _ in range(steps):
        gradients = [0.0, 0.0]
        bias_gradient = 0.0
        for embedding, damaged in rows:
            logit = sum(coef * value for coef, value in zip(weights, embedding)) + bias
            probability = 1 / (1 + exp(-logit))
            residual = probability - damaged
            gradients[0] += residual * embedding[0]
            gradients[1] += residual * embedding[1]
            bias_gradient += residual
        for position in range(2):
            gradient = gradients[position] / len(rows) + penalty * weights[position]
            weights[position] -= rate * gradient
        bias -= rate * bias_gradient / len(rows)
    return weights, bias

probe_weights, probe_bias = train_damage_probe(training_parcels)
def damage_probability(embedding):
    logit = sum(coef * value for coef, value in zip(probe_weights, embedding))
    return 1 / (1 + exp(-(logit + probe_bias)))

assert damage_probability((1.0, 1.0)) > 0.8
assert damage_probability((-1.0, -1.0)) < 0.2''',
    'For N target rows, D embedding dimensions and T full-batch steps, head training costs O(TND) time and O(D) parameter memory; stored embeddings cost O(ND). Encoder extraction may dominate both. Retain grouped target holdouts rather than spending every labeled parcel on the probe.',
    ['Do not fit scaling or the probe on the final target test.', 'Do not report head-only latency as end-to-end image latency.', 'Do not interpret a high training score on six illustrative rows as deployment evidence.'],
    ['machine-learning/pretrained-encoder-target-contract','machine-learning/staged-fine-tuning-and-checkpoint-selection','machine-learning/negative-transfer-by-target-slice','machine-learning/transfer-learning-release-review-project'])


add('staged-fine-tuning-and-checkpoint-selection',
    'Staged fine-tuning and checkpoint selection',
    'Staged fine-tuning first trains a task head with the encoder frozen, then tests a limited encoder update using an untouched validation role and a final target holdout.', [
    ('Start from an interpretable probe', 'A frozen encoder with a trained head establishes a cheap baseline. Unfreeze a declared upper block only after that baseline is measured. Changing every layer at once can destroy useful pretrained features, increase memory use and overfit a small target set. The exact layer choice is an experiment, not a universal rule. [[machine-learning/frozen-embedding-linear-probe|The probe lesson]] supplies the starting point.'),
    ('Use a separate, smaller update rate for reused weights', 'The head begins near a new task solution; the encoder already contains a learned representation. It is common to test a smaller update rate for reused layers than for the head. Log which parameters are trainable, their update rates, optimizer state and checkpoint. Some layers maintain running statistics even when their weights are frozen, so inspect the training/inference behavior of the chosen framework. [[deep-learning/checkpoint-resume-state|Checkpoint state]] must include more than weights.'),
    ('Select only on development data', 'The code compares frozen and partially tuned checkpoint records using predeclared validation loss, then reports a final-test value only after selection. Its records are illustrative; it does not implement a neural optimizer. If several unfreezing depths, augmentations and seeds are tried, the validation set becomes part of a large search. A later independent target cohort is needed to assess the chosen design. [[machine-learning/hyperparameter-search-and-untouched-test|Untouched testing]] states the boundary.'),
    ('Measure the tradeoff across slices', 'A tuned encoder may improve familiar photos while worsening images from a new camera or packaging type. Compare paired errors, calibration and review load by slice, with support. Do not promote a small average gain if it hides a costly miss increase at one depot. [[machine-learning/negative-transfer-by-target-slice|Negative transfer]] is an empirical finding on the target task.'),
    ('Include serving cost in the decision', 'Fine-tuning does not necessarily make inference slower if architecture stays fixed, but training costs rise and the new checkpoint needs storage, validation and rollback. If it changes input size or adds layers, inference may also change. [[deep-learning/inference-schema-and-latency|Serving latency]] belongs beside target error. [[machine-learning/transfer-learning-release-review-project|The release review]] compares both.')],
    '''# Candidate records are produced by separate training runs, not this selector.
checkpoints = [
    {"id": "frozen-head-v3", "stage": "frozen", "validation_loss": 0.41,
     "trainable_parameters": 513},
    {"id": "upper-block-v1", "stage": "partial", "validation_loss": 0.36,
     "trainable_parameters": 180513},
    {"id": "all-layers-v1", "stage": "full", "validation_loss": 0.44,
     "trainable_parameters": 2200513},
]

def choose_checkpoint(training_records):
    if len({record["id"] for record in training_records}) != len(training_records):
        raise ValueError("duplicate checkpoint ID")
    return min(training_records, key=lambda record: record["validation_loss"])

selected = choose_checkpoint(checkpoints)
assert selected["id"] == "upper-block-v1"
sealed_test_losses = {"frozen-head-v3": 0.43, "upper-block-v1": 0.39,
                      "all-layers-v1": 0.50}
final_test_loss = sealed_test_losses[selected["id"]]  # Revealed after selection.
assert final_test_loss == 0.39''',
    'Scanning K checkpoint summaries costs O(K) time and O(1) extra memory. Fine-tuning a trainable encoder is far more expensive than fitting only a small head because gradients and optimizer state cover more parameters. Retaining multiple checkpoints also consumes storage and review time.',
    ['Do not select a checkpoint using final-test loss.', 'Do not assume frozen weights imply frozen normalization statistics.', 'Do not describe a chosen learning-rate schedule as a universal recipe.'],
    ['machine-learning/frozen-embedding-linear-probe','machine-learning/negative-transfer-by-target-slice','machine-learning/pretraining-overlap-and-provenance-audit','machine-learning/transfer-learning-release-review-project'])


add('negative-transfer-by-target-slice',
    'Negative transfer by target slice',
    'Negative transfer is a target-domain regression caused by reusing a source representation or update strategy, measured against a valid target baseline on the same cases.', [
    ('Define the comparison before looking at results', 'A parcel-damage model can use a frozen pretrained encoder, a tuned encoder or target-only features. Evaluate each on the same untouched target parcels with the same label definition and action threshold. Compare absolute error counts and paired differences, not scores from different depots. [[machine-learning/pretrained-encoder-target-contract|The target contract]] prevents a label or preprocessing change from masquerading as transfer failure.'),
    ('Report the harm that matters', 'The code counts paired mistakes for an operational baseline and a transferred candidate by camera site. The candidate improves the overall error count in the tiny illustration but worsens one site. For damage review, false negatives may cost more than extra manual inspections, so inspect those separately before deployment. [[computer-vision/detection-metrics-and-thresholds|Threshold metrics]] and [[machine-learning/decision-threshold-and-cost|decision costing]] determine the right report.'),
    ('Avoid a false cause claim', 'A site gap can arise from lighting, packaging mix, label quality or sample noise. An error table does not establish which. Inspect representative failure cases with consent and blinding where possible, then test a targeted change on a later cohort. Source-task similarity is a hypothesis; target-domain paired outcomes are the evidence. [[computer-vision/grouped-evaluation-and-shift|Grouped shift evaluation]] helps keep near-duplicate parcels together.'),
    ('Keep model selection out of the final slice report', 'If a developer tries many checkpoints and chooses the one with the smallest final-test site gap, that test is now training information. Use development slices for design and a sealed later target period for confirmation. Small slices need support counts and uncertainty; a zero miss count on a handful of photos is not a guarantee. [[machine-learning/paired-bootstrap-model-gain-intervals|Paired intervals]] can describe some uncertainty when resampling respects parcel groups.'),
    ('Decide whether to transfer at all', 'The simplest target-only baseline may win once inference cost, errors and maintenance are included. A source model that helps one camera but hurts another may be restricted to a well-supported domain, sent to review, or rejected. [[machine-learning/transfer-learning-release-review-project|The release project]] records that disposition explicitly.')],
    '''# Site, true damage label, baseline decision, transferred decision.
target_cases = [
    ("Harbor", 1, 0, 1), ("Harbor", 0, 1, 0),
    ("Harbor", 1, 0, 1), ("Harbor", 0, 0, 0),
    ("Inland", 1, 1, 0), ("Inland", 0, 0, 1),
    ("Inland", 1, 1, 1), ("Inland", 0, 0, 0),
]

def paired_site_errors(rows):
    report = {}
    for site, truth, baseline, transferred in rows:
        counts = report.setdefault(site, {"support": 0, "baseline_errors": 0,
                                          "transfer_errors": 0, "transfer_misses": 0})
        counts["support"] += 1
        counts["baseline_errors"] += baseline != truth
        counts["transfer_errors"] += transferred != truth
        counts["transfer_misses"] += truth == 1 and transferred == 0
    return report

site_report = paired_site_errors(target_cases)
assert site_report["Harbor"]["baseline_errors"] == 3
assert site_report["Harbor"]["transfer_errors"] == 0
assert site_report["Inland"]["transfer_errors"] == 2''',
    'Auditing N paired target cases costs O(N) time and O(S) counters for S sites. A credible slice comparison needs new target labels and correct parcel grouping; these collection and review costs can dominate the metric calculation.',
    ['Do not compare candidates on different target populations.', 'Do not hide a costly false-negative increase inside average accuracy.', 'Do not call a small subgroup gap a proven causal effect of pretraining.'],
    ['machine-learning/pretrained-encoder-target-contract','machine-learning/frozen-embedding-linear-probe','machine-learning/staged-fine-tuning-and-checkpoint-selection','machine-learning/transfer-learning-release-review-project'])


add('pretraining-overlap-and-provenance-audit',
    'Pretraining overlap and provenance audit',
    'A transferred model needs a record of checkpoint origin and known training overlap so target evaluation does not quietly reuse the same units or restricted data.', [
    ('Trace the checkpoint', 'Store the source model identifier, license terms, intended use, source-data description, preprocessing version and model artifact digest. If the source training set is opaque, say so; there is no general way to prove non-overlap from a checkpoint alone. The code compares known parcel group IDs in a source manifest with target evaluation groups. [[machine-learning/pretrained-encoder-target-contract|The encoder contract]] pins the artifact being audited.'),
    ('Check groups, not only exact files', 'A source photo and target test photo of the same parcel can have different bytes after cropping, compression or a new camera angle. Exact hashes catch exact duplicates but not that shared evaluation unit. Check parcel, capture session and incident group IDs where available; use visual similarity review for uncertain cases. [[deep-learning/augmentation-leakage-boundary|Augmentation leakage]] explains why variants belong together.'),
    ('Separate declared absence from unknown provenance', 'A zero intersection between two known manifests means those manifests share no listed IDs. It does not establish that the source model never saw the target photos if its full pretraining corpus is undisclosed. Record the scope of the check and hold out a newly collected target period where possible. Do not manufacture a clean-provenance claim from missing metadata. [[computer-vision/grouped-evaluation-and-shift|Target grouping]] still matters when the source corpus is unknown.'),
    ('Review rights and data handling', 'Checkpoint reuse may be limited by license, collection consent, retention policy or security review. Keep these checks in the editorial and engineering workflow; this tutorial does not grant rights to any third-party model or dataset. If the allowed use is uncertain, resolve it before deployment, even if target validation looks strong. [[computer-vision/image-unit-label-and-consent|Image consent]] supplies the data-side question.'),
    ('Version the audit with each update', 'A later checkpoint or a refreshed pretraining set changes the overlap boundary. Attach the audit to the exact artifact digest and target evaluation cohort, then rerun it when either changes. [[machine-learning/transfer-learning-release-review-project|The release review]] treats unresolved provenance as a decision blocker.')],
    '''import hashlib

source_groups = {"parcel-A17", "parcel-B24", "parcel-C05"}
target_test_groups = {"parcel-C05", "parcel-D91", "parcel-E44"}
checkpoint_bytes = b"parcel-encoder-release-4"

def provenance_audit(known_source_groups, evaluation_groups, artifact_bytes):
    overlap = sorted(known_source_groups & evaluation_groups)
    return {
        "known_group_overlap": overlap,
        "source_groups_known": len(known_source_groups),
        "target_groups_checked": len(evaluation_groups),
        "artifact_sha256": hashlib.sha256(artifact_bytes).hexdigest(),
    }

audit = provenance_audit(source_groups, target_test_groups, checkpoint_bytes)
assert audit["known_group_overlap"] == ["parcel-C05"]
assert len(audit["artifact_sha256"]) == 64''',
    'Intersecting S source and T target group IDs costs O(S + T) expected time and O(S + T) set memory; hashing an artifact costs O(B) time for B bytes. Manual near-duplicate review and verifying legal or consent conditions may be more expensive than either operation.',
    ['Do not claim no source overlap when the source training manifest is unavailable.', 'Do not rely on byte equality to detect all parcel-level duplicates.', 'Do not transfer a checkpoint without recording its permitted use and exact version.'],
    ['machine-learning/pretrained-encoder-target-contract','machine-learning/negative-transfer-by-target-slice','machine-learning/staged-fine-tuning-and-checkpoint-selection','machine-learning/transfer-learning-release-review-project'])


add('transfer-learning-release-review-project',
    'Transfer learning release review project',
    'Review a parcel-damage model that reuses a pretrained encoder against target-only baselines, target slices, source overlap and serving constraints.', [
    ('Lock the target task and source artifact', 'Define the parcel-level damage-review label, image capture deadline, target-group split and intervention cost. Pin the source checkpoint and preprocessing contract, then document what is known about source training and permitted use. [[machine-learning/pretrained-encoder-target-contract|The target contract]] and [[machine-learning/pretraining-overlap-and-provenance-audit|provenance audit]] form the first two records.'),
    ('Measure cheap adaptation first', 'Extract frozen embeddings and fit a small head on target training parcels. Compare it with an operational rule and a target-only baseline on the same grouped development cohort. If the frozen probe is adequate, extra tuning must justify its training and maintenance cost. [[machine-learning/frozen-embedding-linear-probe|The probe]] is a concrete starting point.'),
    ('Test staged tuning without contaminating the holdout', 'Choose trainable blocks, update rates and checkpoints using development data. Preserve a later untouched parcel cohort for final comparison. Report point error, false negatives, calibration and review load globally and by camera or depot. [[machine-learning/staged-fine-tuning-and-checkpoint-selection|Checkpoint selection]] and [[machine-learning/negative-transfer-by-target-slice|the target-slice audit]] address different failure modes.'),
    ('Check the full serving path', 'The complete encoder and head must fit image input validation, memory, latency and fallback requirements at the warehouse. If the checkpoint changes image geometry or crop rules, revalidate the entire input pipeline. Retain the prior model or manual-review path for rollback. [[deep-learning/inference-schema-and-latency|Serving contracts]] cover that operational boundary.'),
    ('Record a bounded decision', 'The code checks whether a review packet includes required artifacts. It cannot certify a model as safe or useful. Attach measured values, group support, owners and the next evaluation window; an unresolved source-overlap question remains visible rather than being treated as a negative result.')],
    '''def transfer_review_gate(packet):
    requirements = {
        "target_groups_sealed": "target groups",
        "encoder_contract_pinned": "encoder contract",
        "source_provenance_reviewed": "source provenance",
        "frozen_baseline_measured": "frozen baseline",
        "slice_errors_reported": "slice errors",
        "serving_latency_checked": "serving latency",
        "rollback_path_named": "rollback path",
    }
    missing = [label for field, label in requirements.items() if not packet.get(field)]
    return "eligible for pilot review" if not missing else "hold: " + ", ".join(missing)

parcel_packet = {
    "target_groups_sealed": True,
    "encoder_contract_pinned": True,
    "source_provenance_reviewed": False,
    "frozen_baseline_measured": True,
    "slice_errors_reported": True,
    "serving_latency_checked": False,
    "rollback_path_named": True,
}
assert transfer_review_gate(parcel_packet) == (
    "hold: source provenance, serving latency"
)''',
    'The gate costs O(K) for K requirements. A frozen probe trains in O(TND) for T steps, N target examples and D embedding features, plus encoder extraction. Fine-tuning raises training memory and compute. Target labeling, overlap review, serving validation and rollback readiness remain necessary regardless of model speed.',
    ['Do not use the final target holdout to choose checkpoints or thresholds.', 'Do not treat an opaque source-data manifest as proof of no overlap.', 'Do not release on average accuracy without site-level misses and full-path latency.'],
    ['machine-learning/pretrained-encoder-target-contract','machine-learning/frozen-embedding-linear-probe','machine-learning/staged-fine-tuning-and-checkpoint-selection','machine-learning/negative-transfer-by-target-slice','machine-learning/pretraining-overlap-and-provenance-audit','computer-vision/grouped-evaluation-and-shift'])


publish_batch(
    lessons,
    module_title='Transfer learning and target evidence',
    module_summary='Pin the source and target contracts, test frozen representations, tune carefully and audit target regressions.',
    project_heading='Transfer learning release review',
    crosslinks=[
        ('computer-vision/image-unit-label-and-consent', lessons[0]['path']),
        ('machine-learning/logistic-regression-log-loss-and-odds', lessons[1]['path']),
        ('deep-learning/checkpoint-resume-state', lessons[2]['path']),
        ('computer-vision/grouped-evaluation-and-shift', lessons[3]['path']),
        ('deep-learning/augmentation-leakage-boundary', lessons[4]['path']),
        ('machine-learning/bandit-policy-release-review-project', lessons[5]['path']),
    ],
    sort_start=5400,
)
