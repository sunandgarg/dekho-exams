"""Add artifact trust and outcome feedback to the MLOps curriculum."""
from de_batch_publisher import publish

M = 'mlops/'
A = 'Model artifact trust and release evidence'
F = 'Outcome feedback and label lineage'

lessons = [
    {
        'path': M + 'model-artifact-digest-and-safe-loading',
        'title': 'Model artifacts: verify digest, origin and loading format',
        'module': A, 'project': False,
        'summary': 'The file loaded by a serving process must be the exact reviewed artifact, and its loader must match the trust level of its origin.',
        'sections': [
            ('Treat the artifact as executable input', 'A model directory can contain weights, tokenizer files, feature mappings and loader metadata. Some serialization formats can execute code during loading; a matching filename is not proof of safety. Accept artifacts only from an approved build path and use a loader appropriate for that format and trust boundary. Keep a manifest of required files and digests, then compare bytes before use. [[mlops/run-manifest-and-artifact-lineage|Run lineage]] explains where the files came from; the digest check verifies which bytes arrived.'),
            ('Bind bytes to the reviewed release', 'A registry alias can move from one version to another. Resolve the alias to an immutable artifact digest during promotion, and put that digest in the deployment record. A server should refuse to load a directory with an unexpected file, missing file or hash mismatch. Hashing confirms integrity relative to a trusted manifest; it does not prove the manifest itself is honest. Protect the manifest through a separately trusted release channel. [[mlops/model-registry-promotion-gates|Promotion gates]] should evaluate the same digest that serving will load.'),
            ('Keep loader authority narrow', 'Loading an untrusted Python object in the serving process can give the object the privileges of that process. Prefer restricted data formats and explicit model construction when the system allows it. If a trusted legacy format is unavoidable, isolate build and inference identities, restrict file origins and test the loader in a disposable environment before promotion. Never download a model artifact from a mutable URL at process startup without pinning its digest and origin policy.'),
            ('Drill a tampered package', 'Alter one byte of a model file, remove a vocabulary file and change a manifest entry in a test package. Each case should fail before the serving pointer changes. Record the rejected digest and reason without echoing secrets or full file contents. The [[mlops/trusted-model-promotion-project|trusted promotion project]] combines digest verification with registry, contract and rollback checks.'),
        ],
        'code': '''from hashlib import sha256

def verify_artifact_files(files, expected_digests):
    if set(files) != set(expected_digests):
        return {"state": "reject", "reason": "file-set"}
    for name, expected in expected_digests.items():
        actual = sha256(files[name]).hexdigest()
        if actual != expected:
            return {"state": "reject", "reason": "digest", "file": name}
    return {"state": "verified", "files": len(files)}

package = {"weights.bin": b"receipt-model-r8",
           "features.json": b'{"amount_minor":"cent"}'}
digests = {name: sha256(content).hexdigest()
           for name, content in package.items()}
assert verify_artifact_files(package, digests)["state"] == "verified"
assert verify_artifact_files({**package, "weights.bin": b"changed"},
                             digests)["state"] == "reject"
''',
        'cost': 'Hashing all files takes O(B) time for B artifact bytes and O(1) streaming memory per file, apart from the in-memory bytes used in this compact example. Verify before activation and cache the result for immutable digests. A hash alone does not authenticate who issued the expected manifest or make an unsafe deserializer safe.',
        'mistakes': ['Trusting a registry alias without resolving its immutable digest.', 'Loading a package before checking every required file.', 'Treating a hash as proof that the manifest issuer is trusted.', 'Deserializing unknown objects inside the privileged serving process.'],
        'related': [M + 'promotion-attestation-and-reversible-pointer', M + 'trusted-model-promotion-project', M + 'run-manifest-and-artifact-lineage', M + 'model-registry-promotion-gates', M + 'feature-contract-and-admission-gates'],
    },
    {
        'path': M + 'promotion-attestation-and-reversible-pointer',
        'title': 'Promotion evidence: bind evaluation, contract and rollback to one digest',
        'module': A, 'project': False,
        'summary': 'A release decision is valid only for the exact artifact and environment tested; moving an alias must retain a known rollback target.',
        'sections': [
            ('Describe what the evidence actually covers', 'An evaluation record should name model digest, data snapshot, feature contract, metric code revision, slice definitions and hardware profile. A passing quality score from another digest is not evidence for the candidate being deployed. Keep the builder identity and dependency lock alongside the package. The record is an attestation about a build and evaluation; its trust depends on who can issue and alter it. [[mlops/model-artifact-digest-and-safe-loading|Artifact verification]] checks that serving receives the attested bytes.'),
            ('Make promotion a small, auditable transition', 'Separate candidate registration from the serving pointer. Before moving the pointer, verify artifact digest, contract compatibility, evaluation limits, privacy approval where relevant and serving latency. Resolve the current pointer to an immutable rollback digest and confirm the old package is still loadable. A mutable alias is useful operationally, but the change event must store old and new digests so an incident can reconstruct what ran. [[mlops/model-registry-promotion-gates|Registry gates]] provide the decision context.'),
            ('Design rollback before canary', 'Rollback is more than resetting an alias if the feature producer, tokenizer or schema changed. Keep the old serving image, compatible inputs and capacity until the candidate clears its observation window. Stage a rollback drill using the same deployment method used in production, then measure time to restore customer outcomes. [[mlops/shadow-canary-and-rollback|Canary controls]] should halt on tail latency, error and quality guardrails rather than only average accuracy.'),
            ('Reject stale or borrowed evidence', 'A digest may pass yesterday and fail today because a dependency image, policy or input contract changed. Define evidence freshness and environment scope. Reject a signed report from a different project or a report whose artifact digest does not match the candidate. The [[mlops/trusted-model-promotion-project|release project]] tests a swapped report, missing rollback package and broken input contract.'),
        ],
        'code': '''def promotion_ready(candidate, evidence, rollback):
    required = {"artifact_digest", "feature_contract", "data_snapshot"}
    if not required <= evidence.keys():
        return {"state": "hold", "reason": "missing-evidence"}
    if evidence["artifact_digest"] != candidate["artifact_digest"]:
        return {"state": "hold", "reason": "digest-mismatch"}
    if evidence["feature_contract"] != candidate["feature_contract"]:
        return {"state": "hold", "reason": "contract-mismatch"}
    if not evidence.get("quality_passed") or not evidence.get("latency_passed"):
        return {"state": "hold", "reason": "failed-gate"}
    if not rollback.get("loadable") or not rollback.get("input_compatible"):
        return {"state": "hold", "reason": "no-rollback"}
    return {"state": "ready", "rollback_digest": rollback["artifact_digest"]}

candidate = {"artifact_digest": "sha256:r8", "feature_contract": "receipt-v3"}
evidence = {**candidate, "data_snapshot": "snapshot-82",
            "quality_passed": True, "latency_passed": True}
old = {"artifact_digest": "sha256:r7", "loadable": True,
       "input_compatible": True}
assert promotion_ready(candidate, evidence, old)["state"] == "ready"
assert promotion_ready(candidate, {**evidence, "artifact_digest": "sha256:other"},
                       old)["state"] == "hold"
''',
        'cost': 'Comparing a fixed release record is O(1) time and space. The expensive work is producing trustworthy evidence: evaluation runs, load tests and rollback drills. The code checks key equality and gate booleans, not cryptographic signatures or issuer authorization; enforce those at the release system boundary.',
        'mistakes': ['Applying a passing report to a different artifact digest.', 'Keeping a rollback alias but deleting its underlying package.', 'Moving the model pointer while the old input contract is no longer emitted.', 'Treating a signed report from an untrusted issuer as sufficient evidence.'],
        'related': [M + 'model-artifact-digest-and-safe-loading', M + 'trusted-model-promotion-project', M + 'model-registry-promotion-gates', M + 'shadow-canary-and-rollback', M + 'feature-schema-evolution-and-consumers'],
    },
    {
        'path': M + 'trusted-model-promotion-project',
        'title': 'Project: promote a receipt model with artifact and rollback evidence',
        'module': A, 'project': True,
        'summary': 'Build a release gate that ties package bytes, feature contract, evaluation and rollback to one candidate digest.',
        'sections': [
            ('Define the release bundle', 'A new receipt-risk model contains weights, a feature map and a metadata manifest. Pin their digests and record the build identity, source revision, data snapshot, evaluation slices and feature contract. The candidate remains registered but unserved until all checks pass. The [[mlops/model-artifact-digest-and-safe-loading|artifact boundary]] rejects missing or altered files before any loader runs.'),
            ('Create adversarial release cases', 'Prepare one complete package, one altered weight file, one borrowed evaluation report, one missing tokenizer or feature map, and one candidate that cannot be rolled back because the previous contract is no longer emitted. Freeze expected hold reasons. Include a quality report with good overall accuracy but failed urgent-case recall; its gate must fail. [[mlops/promotion-attestation-and-reversible-pointer|Promotion evidence]] must refer to the exact digest and environment under review.'),
            ('Stage and observe the transition', 'Verify digests, evaluate quality and serving cost, confirm the old package loads, then move a staging pointer. Run shadow and canary traffic while recording old and new digests in every release event. Keep a human-readable decision and the machine-check results. Avoid loading arbitrary serialized objects from a package merely because its registry entry exists. [[mlops/shadow-canary-and-rollback|Canary behavior]] tests customer outcomes after the pointer moves.'),
            ('Exercise recovery', 'Tamper with the candidate after staging and confirm deployment rejects it. Simulate a feature-producer change during canary; roll back model and producer together if required. Report verification time, promotion holds, canary outcomes and recovery duration. The final artifact is a release record that identifies exactly what ran, why it was accepted and which package can replace it during an incident.'),
        ],
        'code': '''def release_state(artifact_check, evidence_check, rollback_check,
                  canary_error_rate):
    for name, passed in (("artifact", artifact_check),
                         ("evidence", evidence_check),
                         ("rollback", rollback_check)):
        if not passed:
            return {"state": "hold", "reason": name}
    if not 0 <= canary_error_rate <= 1:
        raise ValueError("error rate must be a fraction")
    if canary_error_rate > 0.012:
        return {"state": "rollback", "reason": "canary-errors"}
    return {"state": "promote"}

assert release_state(True, True, True, 0.008)["state"] == "promote"
assert release_state(False, True, True, 0.008)["state"] == "hold"
assert release_state(True, True, True, 0.021)["state"] == "rollback"
''',
        'cost': 'The final decision uses O(1) time and space; artifact hashing costs O(B) for B package bytes and canary observation costs requests and retained aggregates. A small canary may be too noisy to support a tight error threshold, so set its sample size and observation period before looking at results.',
        'mistakes': ['Executing a model loader before verifying package identity.', 'Accepting evaluation evidence from a different digest.', 'Declaring rollback ready without loading the old package.', 'Ignoring a failed canary because the offline score improved.'],
        'related': [M + 'model-artifact-digest-and-safe-loading', M + 'promotion-attestation-and-reversible-pointer', M + 'model-registry-promotion-gates', M + 'shadow-canary-and-rollback', M + 'receipt-triage-release-project'],
    },
    {
        'path': M + 'prediction-outcome-join-and-maturity',
        'title': 'Prediction-outcome joins: evaluate only mature, matched decisions',
        'module': F, 'project': False,
        'summary': 'A production quality metric needs the exact prediction, its later outcome and a declared maturity rule.',
        'sections': [
            ('Join decisions by immutable identity', 'A receipt can be rescored after a correction. Joining an outcome to a receipt ID alone may attach it to the wrong decision. Store a unique prediction ID, model digest, decision timestamp, feature-contract version and decision purpose. The outcome record should identify which decision it evaluates and when the result became known. [[mlops/inference-logging-privacy|Inference logging]] defines a privacy-conscious join key; a raw receipt image need not be copied into the metric table.'),
            ('Declare an observation window', 'A disputed transaction may be resolved 23 days after prediction. Recent decisions lack the same opportunity to acquire a positive outcome. Mark them pending rather than negative. A maturity delay is a policy tied to the outcome process, not an arbitrary wait that improves the chart. Track coverage: how many eligible predictions have observed outcomes and which populations remain missing. [[mlops/drift-delayed-label-monitoring|Delayed-label monitoring]] separates current serving health from mature quality.'),
            ('Avoid outcome selection bias', 'Some decisions are reviewed manually because the model marked them risky. Those decisions receive labels sooner and more often than low-risk decisions. A quality estimate from reviewed cases alone describes the reviewed population. Preserve the selection rule, sample a known fraction of low-risk cases if lawful and practical, and report population-weighted or stratified results only when the sampling design supports them. An outcome feed can also contain corrections; keep versions rather than overwriting history.'),
            ('Audit join failures', 'Count duplicate prediction IDs, orphan outcomes, multiple outcomes, late arrivals and missing coverage by model version and slice. Test a record whose outcome arrives after the cutoff and a receipt with two distinct predictions. The [[mlops/receipt-outcome-feedback-project|feedback project]] builds an evaluation set from this ledger and refuses to claim accuracy when the label population is too sparse.'),
        ],
        'code': '''from datetime import timedelta

def mature_pairs(predictions, outcomes, cutoff, maturity_days=23):
    by_prediction = {}
    for outcome in outcomes:
        key = outcome["prediction_id"]
        if key in by_prediction:
            raise ValueError("duplicate outcome for prediction")
        by_prediction[key] = outcome
    pairs = []
    for prediction in predictions:
        if prediction["at"] > cutoff - timedelta(days=maturity_days):
            continue
        outcome = by_prediction.get(prediction["prediction_id"])
        if outcome is not None and outcome["observed_at"] <= cutoff:
            pairs.append((prediction, outcome))
    return pairs

from datetime import datetime, timezone
cutoff = datetime(2026, 10, 6, tzinfo=timezone.utc)
old = {"prediction_id": "decision-47", "at": cutoff - timedelta(days=27)}
new = {"prediction_id": "decision-82", "at": cutoff - timedelta(days=8)}
labels = [{"prediction_id": "decision-47", "observed_at": cutoff}]
assert len(mature_pairs([old, new], labels, cutoff)) == 1
''',
        'cost': 'Joining p predictions to o outcomes uses O(p + o) expected time and O(o) lookup memory. Materialized joins can reduce repeated scans but need correction handling and retention limits. The example rejects duplicate outcomes; a full ledger should version revisions and choose the active label under an explicit rule.',
        'mistakes': ['Using receipt ID when one receipt has several predictions.', 'Counting pending outcomes as negative labels.', 'Measuring only cases selected for manual review as if they were all traffic.', 'Overwriting corrected outcomes without preserving the earlier version.'],
        'related': [M + 'label-corrections-and-evaluation-ledger', M + 'receipt-outcome-feedback-project', M + 'drift-delayed-label-monitoring', M + 'inference-logging-privacy', M + 'retraining-trigger-and-challenger'],
    },
    {
        'path': M + 'label-corrections-and-evaluation-ledger',
        'title': 'Label corrections: version outcomes before rebuilding quality metrics',
        'module': F, 'project': False,
        'summary': 'A corrected outcome changes an evaluation result; retaining revision history makes the change explainable and reproducible.',
        'sections': [
            ('Keep a ledger, not a mutable label cell', 'A receipt initially marked fraudulent may later be cleared. Store each label revision with prediction ID, event time, recorded time, reviewer or source class, reason and superseded revision. A current view can select the latest approved revision, while a historical report should state the revision cutoff it used. [[mlops/prediction-outcome-join-and-maturity|Prediction-outcome joins]] need this selection rule before calculating a confusion matrix.'),
            ('Separate real changes from processing errors', 'A correction can reflect new evidence, a clerical fix, a taxonomy change or a bad join. These cases have different implications. A taxonomy change may require recomputing the full evaluation cohort; a bad join may require withdrawing a prior report. Do not trigger retraining automatically because one metric moved after a data repair. [[mlops/retraining-trigger-and-challenger|Retraining decisions]] should examine the corrected cohort and compare the same frozen population.'),
            ('Recompute dependent evidence', 'When an approved label revision changes, identify which evaluation windows, slice dashboards and model-comparison reports depend on that prediction. Mark stale reports, recompute them under their original cohort definitions and show the delta with counts. Avoid silently replacing a published metric, since an operator may need to explain why yesterday’s alert disappeared. The report should carry model digest, cohort cutoff, label revision cutoff and metric-code revision.'),
            ('Control conflicts and access', 'Two reviewers may submit conflicting labels. Require an adjudication state and leave the prediction out of final quality scoring until it resolves, rather than choosing the latest timestamp blindly. Restrict sensitive adjudication notes; aggregate metrics need only label, scope and revision identity. The [[mlops/receipt-outcome-feedback-project|feedback project]] tests conflicting revisions and reproduces both old and current reports.'),
        ],
        'code': '''def active_labels(revisions, cutoff):
    selected = {}
    for row in revisions:
        if row["recorded_at"] > cutoff or row["state"] != "approved":
            continue
        key = row["prediction_id"]
        previous = selected.get(key)
        if previous is None or row["revision"] > previous["revision"]:
            selected[key] = row
    return {key: row["label"] for key, row in selected.items()}

history = [
    {"prediction_id": "decision-47", "revision": 1,
     "recorded_at": 3, "state": "approved", "label": "fraud"},
    {"prediction_id": "decision-47", "revision": 2,
     "recorded_at": 8, "state": "approved", "label": "clear"},
    {"prediction_id": "decision-82", "revision": 1,
     "recorded_at": 7, "state": "disputed", "label": "fraud"},
]
assert active_labels(history, 5) == {"decision-47": "fraud"}
assert active_labels(history, 9) == {"decision-47": "clear"}
''',
        'cost': 'Scanning r label revisions takes O(r) expected time and O(u) space for u unique prediction IDs. An indexed ledger can query only revised decisions for an incremental rebuild. This compact selector assumes strictly increasing revision numbers per prediction; a production ledger must enforce uniqueness and resolve conflicting writers transactionally.',
        'mistakes': ['Overwriting a label and losing the prior report’s evidence.', 'Choosing the newest conflicting label without adjudication.', 'Changing a dashboard number without identifying the report revision.', 'Triggering retraining on a correction caused by a broken join.'],
        'related': [M + 'prediction-outcome-join-and-maturity', M + 'receipt-outcome-feedback-project', M + 'retraining-trigger-and-challenger', M + 'drift-delayed-label-monitoring', 'data-annotation/label-drift-and-audit-sampling'],
    },
    {
        'path': M + 'receipt-outcome-feedback-project',
        'title': 'Project: build a versioned receipt outcome feedback loop',
        'module': F, 'project': True,
        'summary': 'Join production decisions to delayed outcomes, preserve corrections and publish only reproducible quality reports.',
        'sections': [
            ('Define the decision ledger', 'Record each receipt decision with unique prediction ID, model digest, decision time, eligibility class and a privacy-safe join key. Do not treat a later rescore as the same prediction. Store outcome arrivals separately, with observed time and label revision. [[mlops/prediction-outcome-join-and-maturity|Mature joins]] decide which predictions enter a report; recent pending cases remain visible in coverage counts.'),
            ('Build a frozen evaluation cohort', 'Choose a prediction window and a 23-day maturity rule before observing model performance. Include a low-risk sample that was never sent to manual review, plus reviewed high-risk cases, and retain the selection probability if weighted estimates will be used. Add orphan outcomes, duplicate IDs, late labels, one corrected label and one unresolved dispute. Report cohort size, observed-label coverage and missingness by model and traffic slice.'),
            ('Version quality evidence', 'Create a report keyed by model digest, cohort window, data snapshot, label revision cutoff and metric-code revision. After an approved correction, mark the old report superseded and calculate a new report under the same cohort rules. [[mlops/label-corrections-and-evaluation-ledger|The label ledger]] explains why the score changed. Do not let a correction quietly rewrite an earlier operational decision without an audit event.'),
            ('Gate the next model decision', 'Use the mature cohort to compare incumbent and challenger with the same sampling and label rules. If coverage is low or reviewer selection is biased, mark the quality result inconclusive. A drift alert may trigger investigation, but only sufficient, reproducible outcome evidence should support a retraining or promotion decision. [[mlops/retraining-trigger-and-challenger|Challenger evaluation]] and [[mlops/model-registry-promotion-gates|promotion gates]] consume this report.'),
        ],
        'code': '''def feedback_report(predictions, resolved_labels, minimum_coverage=0.72):
    if not predictions:
        return {"state": "hold", "reason": "empty-cohort"}
    ids = [row["prediction_id"] for row in predictions]
    if len(ids) != len(set(ids)):
        return {"state": "hold", "reason": "duplicate-prediction"}
    matched = [row for row in predictions
               if row["prediction_id"] in resolved_labels]
    coverage = len(matched) / len(predictions)
    if coverage < minimum_coverage:
        return {"state": "inconclusive", "coverage": coverage}
    correct = sum(row["predicted_label"] ==
                  resolved_labels[row["prediction_id"]] for row in matched)
    return {"state": "reportable", "coverage": coverage,
            "accuracy_on_matched": correct / len(matched)}

cohort = [{"prediction_id": "decision-47", "predicted_label": "fraud"},
          {"prediction_id": "decision-82", "predicted_label": "clear"}]
assert feedback_report(cohort, {"decision-47": "fraud"})["state"] == "inconclusive"
assert feedback_report(cohort, {"decision-47": "fraud",
                                "decision-82": "clear"})["state"] == "reportable"
''',
        'cost': 'The compact report scans p predictions in O(p) expected time and uses O(p) space for duplicate detection and matches. Joining revisions, calculating slices and adjusting for known sampling probabilities add work. Accuracy on matched cases is not population accuracy when label availability depends on the model decision; retain that limitation in every report.',
        'mistakes': ['Publishing accuracy from an immature recent cohort.', 'Collapsing rescored decisions under one receipt ID.', 'Hiding low label coverage behind a precise percentage.', 'Editing an old report in place after a label correction.'],
        'related': [M + 'prediction-outcome-join-and-maturity', M + 'label-corrections-and-evaluation-ledger', M + 'drift-delayed-label-monitoring', M + 'retraining-trigger-and-challenger', M + 'receipt-triage-release-project'],
    },
]

crosslinks = [
    (M + 'run-manifest-and-artifact-lineage', M + 'model-artifact-digest-and-safe-loading'),
    (M + 'model-registry-promotion-gates', M + 'promotion-attestation-and-reversible-pointer'),
    (M + 'shadow-canary-and-rollback', M + 'trusted-model-promotion-project'),
    (M + 'inference-logging-privacy', M + 'prediction-outcome-join-and-maturity'),
    (M + 'drift-delayed-label-monitoring', M + 'label-corrections-and-evaluation-ledger'),
    (M + 'retraining-trigger-and-challenger', M + 'receipt-outcome-feedback-project'),
    (M + 'receipt-feature-admission-project', M + 'trusted-model-promotion-project'),
    (M + 'receipt-serving-slo-project', M + 'receipt-outcome-feedback-project'),
]

if __name__ == '__main__':
    publish(lessons, (A, F), crosslinks,
            'aitrove-mlops-artifacts-feedback-import-20261006.json', 6106,
            subject='mlops', hub_path=M + 'mlops-tutorial')
