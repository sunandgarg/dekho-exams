"""Add edge release operations and production explanation evidence to MLOps."""
from de_batch_publisher import publish

M = 'mlops/'
E = 'Edge model release and offline recovery'
X = 'Production explanations and review evidence'

lessons = [
    {
        'path': M + 'edge-model-manifests-and-cohort-rollouts',
        'title': 'Edge model releases: pin runtime, preprocessing and cohort',
        'module': E, 'project': False,
        'summary': 'A device-side model is a release package with runtime and preprocessing requirements, not a model file copied to a handset.',
        'sections': [
            ('Ship a complete decision package', 'A receipt-scanning handheld may classify image quality while offline. Its result depends on image resize rules, token or pixel normalization, runtime version, model bytes and route policy. Record those as one signed or otherwise authenticated manifest with digests and a minimum compatible app version. A new model paired with an old preprocessor is an untested release. [[mlops/inference-chain-contracts-and-stage-identity|Chain identity]] applies on-device as well as in a server, while [[mlops/model-artifact-digest-and-safe-loading|artifact verification]] prevents loading unexpected bytes.'),
            ('Assign devices before download', 'Choose rollout cohorts by stable device or site identity, not by each request. Stage first to test units, then a small production cohort, then broader fleets after health evidence arrives. Distinguish eligible, assigned, downloaded, installed and actually serving counts. A device that downloaded a package but never activated it is not exposed. [[mlops/sticky-model-assignment-and-exposure-logging|Exposure evidence]] has the same assignment-versus-service distinction in online experiments; an edge fleet adds long offline intervals and varying app versions.'),
            ('Check compatibility at activation', 'Download to a staging location, verify the manifest and bytes, run a local smoke input, then atomically change the active pointer. Retain the previous package until the new one has served safely. Reject activation when free storage, runtime capability or input shape is incompatible. A failing download should leave the current model working. [[mlops/promotion-attestation-and-reversible-pointer|Reversible promotion]] should name the exact prior package rather than an alias that can change while the device is offline.'),
            ('Gate expansion on observed health', 'Compare crash rate, inference latency, local fallback, battery impact and missing-event coverage by cohort and device class. Low-connectivity devices may report late, so a quiet dashboard does not mean success. Hold expansion until the minimum observation window and reporting coverage are met. [[mlops/edge-offline-telemetry-and-rollback|Offline telemetry]] supplies a bounded, delayed view of actual use. The [[mlops/handheld-receipt-edge-release-project|handheld release project]] exercises a package that downloads successfully but cannot activate on an older runtime.'),
        ],
        'code': '''def edge_activation(package, device):
    if package["app_min"] > device["app_version"]:
        return "hold:app-version"
    if package["runtime"] not in device["supported_runtimes"]:
        return "hold:runtime"
    if package["bytes"] > device["free_bytes"]:
        return "hold:storage"
    if not package["digest_verified"] or not package["smoke_passed"]:
        return "hold:package-check"
    return "activate"

package = {"app_min": 7, "runtime": "receipt-runtime-r3", "bytes": 47_000_000,
           "digest_verified": True, "smoke_passed": True}
device = {"app_version": 8, "supported_runtimes": {"receipt-runtime-r3"},
          "free_bytes": 82_000_000}
assert edge_activation(package, device) == "activate"
assert edge_activation(package, {**device, "app_version": 6}) == "hold:app-version"
''',
        'cost': 'The activation gate is O(1) expected time and space for a small runtime set. Download and storage cost scale with package bytes, while smoke inference consumes device time and power. Cohort rollout reduces blast radius but prolongs mixed-version operation; maintain both versions only as long as compatibility and rollback require.',
        'mistakes': ['Counting a downloaded model as one that served decisions.', 'Updating the model without its preprocessing and runtime contract.', 'Replacing the current package before the new package passes a local smoke test.', 'Expanding a cohort while offline devices have not reported health.'],
        'related': [M + 'edge-offline-telemetry-and-rollback', M + 'handheld-receipt-edge-release-project', M + 'model-artifact-digest-and-safe-loading', M + 'promotion-attestation-and-reversible-pointer', M + 'sticky-model-assignment-and-exposure-logging'],
    },
    {
        'path': M + 'edge-offline-telemetry-and-rollback',
        'title': 'Offline edge telemetry: late events, coverage and rollback',
        'module': E, 'project': False,
        'summary': 'A fleet release needs evidence from devices that reconnect late and a rollback path that works before they reconnect.',
        'sections': [
            ('Timestamp observation and receipt separately', 'A handheld may classify receipts for days without network access. Each event needs a local decision ID, active package digest, device class, monotonic sequence and observation time. The server also records arrival time. Upload order is not decision order; a late batch must not be mistaken for a fresh failure spike. Avoid raw receipt images in routine telemetry. [[mlops/inference-logging-privacy|Restricted logging]] still governs identities and retention, and [[mlops/prediction-outcome-join-and-maturity|outcome joins]] need event-time boundaries.'),
            ('Make gaps measurable', 'A device can report a daily decision count and highest local sequence even if detailed diagnostics are sampled. Compare expected installed devices with devices that checked in, and report missing coverage by cohort and app version. A silent device may be healthy but offline; mark it unknown rather than successful. Keep a bounded local queue with an explicit overflow counter so lost events are visible after reconnection. [[mlops/trace-sampling-and-coverage-ledger|Coverage ledgers]] distinguish intentionally sampled detail from missing operational evidence.'),
            ('Preload a local recovery path', 'The current device package should retain the last known-good model and policy until the candidate passes activation and observation. A locally detectable crash loop or invalid inference output can move back to the previous pointer without waiting for a server command. Record the rollback cause and package pair. A remote kill switch cannot protect a disconnected device, so a dangerous release should also have local stop conditions. [[mlops/edge-model-manifests-and-cohort-rollouts|The release manifest]] must define compatible rollback targets.'),
            ('Interpret late reports before expansion', 'Use a cohort watermark: the latest observation time for which a required fraction of assigned devices has reported. Evaluate failure rates on observed exposure, not on mere download assignments, and publish reporting coverage beside every rate. A high error count arriving late may force a hold even after online devices looked healthy. [[mlops/handheld-receipt-edge-release-project|The project]] simulates three offline devices that report only after a planned expansion checkpoint, proving why a zero-alert dashboard is not enough.'),
        ],
        'code': '''def edge_cohort_gate(assigned, serving, reported, failures, min_coverage=0.8):
    if assigned <= 0 or min(serving, reported, failures) < 0:
        raise ValueError("invalid cohort counts")
    if serving > assigned or reported > serving or failures > reported:
        raise ValueError("inconsistent cohort counts")
    coverage = reported / serving if serving else 0
    if coverage < min_coverage:
        return {"state": "hold:coverage", "coverage": coverage}
    return {"state": "hold:failures" if failures else "review",
            "coverage": coverage}

assert edge_cohort_gate(47, 40, 28, 0)["state"] == "hold:coverage"
assert edge_cohort_gate(47, 40, 36, 0)["state"] == "review"
''',
        'cost': 'The cohort decision is O(1) time and space after aggregation. On-device queues use O(e) storage for e retained events and consume upload bandwidth on reconnect. A coverage threshold protects against premature expansion but may delay releases in low-connectivity fleets; choose it by measured reporting behavior and the cost of an unseen failure.',
        'mistakes': ['Using server arrival time as if it were device decision time.', 'Treating offline devices as healthy when no report arrives.', 'Keeping no local rollback package because a remote command exists.', 'Reporting error rates without the cohort reporting fraction.'],
        'related': [M + 'edge-model-manifests-and-cohort-rollouts', M + 'handheld-receipt-edge-release-project', M + 'trace-sampling-and-coverage-ledger', M + 'inference-logging-privacy', M + 'receipt-model-incident-drill-project'],
    },
    {
        'path': M + 'handheld-receipt-edge-release-project',
        'title': 'Project: stage a receipt-quality model on offline handhelds',
        'module': E, 'project': True,
        'summary': 'Release one receipt-quality model to a mixed device fleet, reject an incompatible runtime and reconcile late telemetry before expansion.',
        'sections': [
            ('Freeze the package and fleet', 'The new package contains a receipt-quality classifier, image resize rule and policy that sends unreadable images to manual capture. Pin every digest, supported input shape, runtime requirement, minimum app version and previous known-good package. Split handhelds into stable site cohorts and record assigned, downloaded, installed and serving states. [[mlops/edge-model-manifests-and-cohort-rollouts|The package gate]] should reject one older handset before activation while leaving its current classifier available.'),
            ('Exercise installation and offline use', 'Download to a temporary slot and verify bytes, runtime and smoke input before swapping the active pointer. Disconnect three devices; let them process receipts and queue compact decision events locally. Force one candidate crash loop and confirm its local rollback selects the previous complete package, not just the previous model file. Keep events from both digests with local sequence and observation time. [[mlops/edge-offline-telemetry-and-rollback|Offline recovery]] must work without a server round trip.'),
            ('Reconcile delayed evidence', 'Reconnect the devices after the nominal rollout checkpoint. Compute serving coverage and failure rate by observation window and device class. The late events reveal a crash on a device class absent from the online sample; hold expansion. Do not rewrite the earlier dashboard as if the events arrived on time. Compare expected sequence ranges with uploaded events to expose queue overflow. [[mlops/trace-sampling-and-coverage-ledger|Coverage rules]] distinguish missing events from sampled diagnostic traces.'),
            ('Publish the release decision', 'Deliver manifest identities, activation failures, actual exposure count, reporting coverage, crash and rollback events, estimated local queue loss and next cohort decision. Record the device class that remains on the old package and its owner. A successful download is not a successful rollout, and a passing online sample cannot settle risk for devices that have not reported. Link any manual capture load to [[mlops/receipt-serving-slo-project|the receipt service target]] before widening the cohort.'),
        ],
        'code': '''def fleet_expansion(assigned, serving, reported, crashes):
    if min(assigned, serving, reported, crashes) < 0:
        raise ValueError("negative fleet count")
    if serving > assigned or reported > serving or crashes > reported:
        raise ValueError("inconsistent fleet count")
    if serving == 0 or reported / serving < 0.85:
        return "hold:missing-telemetry"
    if crashes:
        return "hold:crash"
    return "expand"

assert fleet_expansion(47, 40, 31, 0) == "hold:missing-telemetry"
assert fleet_expansion(47, 40, 36, 1) == "hold:crash"
assert fleet_expansion(47, 40, 36, 0) == "expand"
''',
        'cost': 'The gate is O(1) time and space; maintaining old and new packages costs device storage proportional to both artifact sizes. Real rollout expense includes downloads, battery use, telemetry buffering and support for mixed versions. The sample coverage rule is illustrative and must be set from fleet reporting latency and acceptable release risk.',
        'mistakes': ['Swapping active model bytes before verifying the preprocessor and runtime.', 'Removing the previous package before the candidate is stable.', 'Counting assigned devices as exposed devices.', 'Expanding before late offline crash events are reconciled.'],
        'related': [M + 'edge-model-manifests-and-cohort-rollouts', M + 'edge-offline-telemetry-and-rollback', M + 'receipt-model-incident-drill-project', M + 'receipt-serving-slo-project', M + 'model-artifact-digest-and-safe-loading'],
    },
    {
        'path': M + 'explanation-provenance-and-validity-boundary',
        'title': 'Production explanations: pin the exact decision and method',
        'module': X, 'project': False,
        'summary': 'An explanation is meaningful only for the model, features, policy and method that produced the decision under review.',
        'sections': [
            ('Bind the explanation to the decision', 'A receipt reviewer may ask why a high-risk route was proposed. Store the decision ID, model digest, feature snapshot identity, preprocessing revision, score, policy revision, explanation method and method configuration. If the feature store changes before explanation runs, the resulting attribution may describe a different input. [[mlops/inference-logging-privacy|Restricted decision logs]] provide a stable join key; [[mlops/score-threshold-policy-and-change-control|policy identity]] distinguishes a high score from the threshold that turned it into review.'),
            ('Name what the method can show', 'A local feature attribution estimates how selected inputs relate to one prediction under a particular reference distribution or local approximation. It does not prove that changing a feature would cause the outcome to change. Correlated inputs can make an attribution unstable or misleading when a method perturbs them independently. Record reference data, approximation settings and validation diagnostics. If the method cannot support a claim, say so in the reviewer interface. [[mlops/model-card-scope-and-limitation-register|The model card]] should list approved explanation uses and known limits.'),
            ('Gate computation and display', 'Explanations may cost far more than scoring, so compute them asynchronously or for a bounded review subset when the latency budget requires it. Do not make a customer decision wait on an optional explanation that can time out. Validate that returned features belong to the scored feature contract, remove restricted attributes from broad display and refuse an explanation for a mismatched digest. [[mlops/explanation-stability-and-reviewer-use|Stability checks]] test whether the output is useful for the human task, not only whether it can be rendered.'),
            ('Preserve reproducibility', 'Retain the explanation artifact or enough immutable inputs to rerun it under the same method version, subject to privacy retention. A later model promotion should not silently regenerate prior explanations under new bytes. Compare a sampled set of explanation outputs after deployment to detect changed method defaults or reference data. [[mlops/receipt-explanation-audit-project|The audit project]] reconstructs a disputed receipt decision and rejects an attribution computed from the wrong feature snapshot.'),
        ],
        'code': '''def explanation_identity(decision, explanation):
    required = ("model_digest", "feature_snapshot", "policy_revision")
    mismatched = [field for field in required
                  if decision.get(field) != explanation.get(field)]
    if mismatched:
        return {"state": "reject", "mismatched": mismatched}
    if not explanation.get("method_revision"):
        return {"state": "reject", "mismatched": ["method_revision"]}
    return {"state": "display", "mismatched": []}

decision = {"model_digest": "risk-47", "feature_snapshot": "snap-82",
            "policy_revision": "policy-3"}
explanation = {**decision, "method_revision": "local-r4"}
assert explanation_identity(decision, explanation)["state"] == "display"
assert explanation_identity(decision, {**explanation,
       "feature_snapshot": "snap-83"})["state"] == "reject"
''',
        'cost': 'Identity comparison takes O(f) time and O(f) mismatch space for f manifest fields. The actual explanation cost depends on the method and number of model evaluations; an approximation may be much slower than inference. Retaining immutable feature evidence has storage and privacy cost, so use a defined retention window and access policy.',
        'mistakes': ['Explaining a historical decision with current feature values.', 'Treating feature attribution as a causal statement.', 'Displaying an explanation from a different model digest.', 'Allowing optional explanation work to consume the scoring deadline.'],
        'related': [M + 'explanation-stability-and-reviewer-use', M + 'receipt-explanation-audit-project', M + 'inference-logging-privacy', M + 'model-card-scope-and-limitation-register', M + 'score-threshold-policy-and-change-control'],
    },
    {
        'path': M + 'explanation-stability-and-reviewer-use',
        'title': 'Explanation quality gates: stability, reference data and reviewer use',
        'module': X, 'project': False,
        'summary': 'An explanation should be checked for repeatability and usefulness before it becomes evidence in a reviewer workflow.',
        'sections': [
            ('Test repeatability under a fixed decision', 'Run the same explanation several times with the same model, feature snapshot, method revision, reference data and seed. Large swings in feature rank or sign may indicate a fragile approximation. Define an acceptable comparison suited to the method; exact byte equality is too strict for some stochastic algorithms, while a vague “looks similar” review is too weak. [[mlops/explanation-provenance-and-validity-boundary|Provenance]] is required before stability can be interpreted. A stable output can still be systematically wrong.'),
            ('Probe realistic neighboring inputs', 'Perturb only features that can plausibly vary without breaking domain constraints. A merchant-age value cannot be changed independently of the merchant opening date if one is derived from the other. A model may rely on several correlated signals, so an attribution that swaps them in impossible combinations can mislead a reviewer. Test missing fields, scan artifacts and borderline scores. Compare explanation changes with prediction changes, but do not call the comparison a causal intervention.'),
            ('Evaluate the human task', 'Ask reviewers whether the explanation helps them find an input error, request missing evidence or decide to override. Measure time to a justified resolution and disagreement against adjudicated outcomes, not just whether they clicked the panel. An explanation can sound persuasive while increasing automation bias. Keep the model score and policy route visible as separate facts, and permit the reviewer to record a reason independent of the explanation. [[mlops/human-override-and-adjudication-ledger|Override records]] provide a later audit trail.'),
            ('Treat display changes as releases', 'A new attribution method, reference population or wording can change reviewer behavior without altering the model. Version the display and test it on frozen decisions, privacy checks and a staged reviewer cohort. Monitor missing explanations, generation failures and unusual override shifts. [[mlops/receipt-explanation-audit-project|The project]] forces an unstable feature ranking and a stale snapshot, then decides whether the panel should display, warn or hold. [[mlops/model-alert-symptoms-ownership-and-noise|Operational alerts]] should identify the owner of a broken explanation service without implying the scorer failed.'),
        ],
        'code': '''def explanation_rank_gate(rankings, minimum_top_agreement=0.75):
    if not rankings or any(not ranking for ranking in rankings):
        raise ValueError("missing rankings")
    anchor = rankings[0][0]
    agreement = sum(ranking[0] == anchor for ranking in rankings) / len(rankings)
    return {"state": "review" if agreement >= minimum_top_agreement
            else "hold", "agreement": agreement}

stable = [["scan_quality", "merchant_age"],
          ["scan_quality", "currency"], ["scan_quality", "merchant_age"],
          ["scan_quality", "receipt_length"]]
assert explanation_rank_gate(stable)["state"] == "review"
assert explanation_rank_gate(stable[:2] + [["currency"], ["currency"]])[
    "state"] == "hold"
''',
        'cost': 'Comparing the top feature across r runs is O(r) time and O(1) extra space. Producing those runs can cost r times the explanation computation. Top-rank agreement is only a simple screening diagnostic; it does not establish fidelity, absence of bias or usefulness to reviewers. The release gate needs task-level tests as well.',
        'mistakes': ['Assuming a repeated attribution is therefore correct.', 'Perturbing correlated features into impossible combinations.', 'Testing a panel only for render success and not reviewer decisions.', 'Changing reference data without a new explanation revision.'],
        'related': [M + 'explanation-provenance-and-validity-boundary', M + 'receipt-explanation-audit-project', M + 'human-override-and-adjudication-ledger', M + 'model-alert-symptoms-ownership-and-noise', M + 'slice-quality-gates-and-uncertainty'],
    },
    {
        'path': M + 'receipt-explanation-audit-project',
        'title': 'Project: audit an explanation for a disputed receipt decision',
        'module': X, 'project': True,
        'summary': 'Reconstruct one decision, reject stale explanation evidence and test whether reviewers can use the corrected panel without over-trusting it.',
        'sections': [
            ('Freeze the disputed decision', 'A receipt was routed to review by a fixed risk model and threshold policy. Preserve decision ID, score, route, model digest, feature snapshot, preprocessor, policy revision and observation time. Reconstruct only from permitted retained data. The explanation service must use the same identity and its own method revision and reference set. [[mlops/explanation-provenance-and-validity-boundary|The provenance gate]] rejects a panel generated from a newer merchant feature snapshot, even if the resulting feature list looks plausible.'),
            ('Challenge the explanation method', 'Generate repeated explanations under a fixed seed policy and inspect top-feature agreement. A scanner-quality signal is stable, but merchant age and receipt length trade places across runs. Do not present a single run as a definitive cause. Create a nearby input with a physically plausible scan-quality change and compare predictions; avoid impossible combinations of derived fields. [[mlops/explanation-stability-and-reviewer-use|Stability tests]] support a warning or hold, not a claim of causal effect.'),
            ('Exercise reviewer decisions', 'Give reviewers the original receipt evidence, proposed route and a panel marked with its scope and uncertainty. Ask them to identify whether missing scan quality needs re-capture, whether an override is justified and what evidence they used. Keep their decision separate from later adjudication. [[mlops/human-override-and-adjudication-ledger|The review ledger]] records an override reason but does not turn it into an outcome label. Compare panel-on and panel-off review of similar cases without treating fewer clicks as proof of better decisions.'),
            ('Deliver a release disposition', 'Publish provenance checks, retained snapshot coverage, method revision, stability result, privacy review, reviewer-task outcome and known limits. The stale-snapshot explanation is rejected; the corrected panel may proceed only with a warning if its unstable ranking is material to the task. Record a rollback of the panel separately from the model and score policy. Link future cases to [[mlops/receipt-model-card-review-project|the model scope review]] so explanations never extend the approved use of the model.'),
        ],
        'code': '''def explanation_audit(decision, panel, top_feature_agreement):
    if panel["model_digest"] != decision["model_digest"]:
        return "reject:model"
    if panel["feature_snapshot"] != decision["feature_snapshot"]:
        return "reject:snapshot"
    if not 0 <= top_feature_agreement <= 1:
        raise ValueError("invalid agreement")
    if top_feature_agreement < 0.75:
        return "hold:unstable"
    return "review-panel"

decision = {"model_digest": "risk-47", "feature_snapshot": "snap-82"}
panel = {**decision, "method_revision": "local-r4"}
assert explanation_audit(decision, panel, 0.82) == "review-panel"
assert explanation_audit(decision, {**panel,
       "feature_snapshot": "snap-83"}, 0.82) == "reject:snapshot"
assert explanation_audit(decision, panel, 0.5) == "hold:unstable"
''',
        'cost': 'The audit gate is O(1) time and space. The complete exercise costs repeated explanation runs, retained input storage, privacy review and reviewer time. A fixed rank threshold is a screening rule, not a measure of explanation truth; the final disposition also depends on method validity and whether the panel helps the actual review task.',
        'mistakes': ['Explaining a disputed decision from a later feature snapshot.', 'Describing a feature contribution as a causal reason.', 'Using reviewer agreement alone as a fidelity metric.', 'Rolling back the model when only the explanation panel is unsafe.'],
        'related': [M + 'explanation-provenance-and-validity-boundary', M + 'explanation-stability-and-reviewer-use', M + 'human-override-and-adjudication-ledger', M + 'receipt-model-card-review-project', M + 'inference-logging-privacy'],
    },
]

crosslinks = [
    (M + 'model-artifact-digest-and-safe-loading', M + 'edge-model-manifests-and-cohort-rollouts'),
    (M + 'trace-sampling-and-coverage-ledger', M + 'edge-offline-telemetry-and-rollback'),
    (M + 'receipt-model-incident-drill-project', M + 'handheld-receipt-edge-release-project'),
    (M + 'inference-logging-privacy', M + 'explanation-provenance-and-validity-boundary'),
    (M + 'human-override-and-adjudication-ledger', M + 'explanation-stability-and-reviewer-use'),
    (M + 'receipt-model-card-review-project', M + 'receipt-explanation-audit-project'),
]

if __name__ == '__main__':
    publish(lessons, (E, X), crosslinks,
            'aitrove-mlops-edge-explanations-import-20261006.json', 6160,
            subject='mlops', hub_path=M + 'mlops-tutorial')
