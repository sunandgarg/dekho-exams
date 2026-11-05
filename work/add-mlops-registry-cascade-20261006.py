"""Publish registry recovery and model-cascade release modules."""
from de_batch_publisher import publish

M = 'mlops/'
R = 'Registry recovery and artifact restore'
C = 'Model cascades and component release contracts'

lessons = [
    {
        'path': M + 'registry-backup-artifact-and-metadata-consistency',
        'title': 'Model registry backups: keep metadata and artifact bytes consistent',
        'module': R, 'project': False,
        'summary': 'A registry restore fails if version records survive but the referenced model bytes or promotion decisions do not.',
        'sections': [
            ('Treat the registry as more than a table', 'A production model registry commonly separates version metadata from large artifact objects. A database backup can restore a model version whose URI points to deleted bytes; an artifact copy without its approval and alias history cannot explain why a model served. Inventory the backend store, artifact store, immutable image store and promotion ledger. Define recovery point and recovery time objectives for each. [[mlops/run-manifest-and-artifact-lineage|Run lineage]] connects training to artifacts; [[mlops/promotion-attestation-and-reversible-pointer|promotion attestations]] connect artifacts to serving decisions.'),
            ('Make a coherent recovery set', 'Capture a metadata checkpoint with a known time or transaction boundary, then ensure every artifact reachable from the retained registry versions exists in the backup set. Object copies may lag the database snapshot, and mutable aliases may move during copying. Prefer immutable version and digest references in the manifest; record alias state only after its target is confirmed. Keep encryption keys and access policy recoverable through a separate controlled process. A backup that cannot decrypt or load a model is not a usable backup.'),
            ('Verify by reading, not by counting files', 'Restore into an isolated environment, query the active and prior versions, fetch each referenced artifact, verify its digest and load it with the intended runtime. Check approval records and the previous rollback target. Rehearse a failed artifact fetch and a metadata row whose object has not arrived. [[mlops/model-artifact-digest-and-safe-loading|Digest verification]] detects corruption; [[mlops/model-runtime-dependency-inventory|runtime inventory]] tests whether recovered bytes can still execute.'),
            ('Set a realistic recovery boundary', 'A recent backup may still lose a promotion after its checkpoint. Decide whether the restore should hold all serving pointer changes, replay an append-only promotion log or keep the last known-good deployment pinned until reconciliation. Never infer the correct active model from the highest version number. [[mlops/registry-restore-and-promotion-reconciliation|Restore reconciliation]] makes the alias decision explicit, and [[mlops/receipt-registry-disaster-drill-project|the project]] tests a metadata backup newer than one artifact copy.'),
        ],
        'code': '''def verify_registry_backup(versions, artifact_digests):
    missing = []
    mismatched = []
    for version in versions:
        actual = artifact_digests.get(version["artifact_uri"])
        if actual is None:
            missing.append(version["version_id"])
        elif actual != version["expected_digest"]:
            mismatched.append(version["version_id"])
    return {"missing": missing, "mismatched": mismatched,
            "restorable": not missing and not mismatched}

versions = [{"version_id": "risk-r47", "artifact_uri": "objects/r47",
             "expected_digest": "sha256:47"},
            {"version_id": "risk-r48", "artifact_uri": "objects/r48",
             "expected_digest": "sha256:48"}]
report = verify_registry_backup(versions, {"objects/r47": "sha256:47"})
assert report["missing"] == ["risk-r48"]
assert not report["restorable"]
''',
        'cost': 'Verification is O(v) expected time and O(v) worst-case result space for v retained versions; hashing artifact bytes adds O(b) work for b total bytes. Replicated storage and restore drills add cost, but an untested backup offers no measured recovery time. Keep the retention set aligned with active, rollback and audit obligations instead of copying every abandoned experiment forever.',
        'mistakes': ['Backing up registry rows while artifact objects are copied on a different schedule.', 'Restoring an alias to the newest version without an approval record.', 'Counting stored files instead of loading and hashing the referenced model.', 'Forgetting the key or runtime required to use restored bytes.'],
        'related': [M + 'registry-restore-and-promotion-reconciliation', M + 'receipt-registry-disaster-drill-project', M + 'run-manifest-and-artifact-lineage', M + 'model-artifact-digest-and-safe-loading', M + 'promotion-attestation-and-reversible-pointer'],
    },
    {
        'path': M + 'registry-restore-and-promotion-reconciliation',
        'title': 'Registry restore: reconcile aliases, approvals and serving pointers',
        'module': R, 'project': False,
        'summary': 'Recover registry state without promoting an unapproved version or discarding a legitimate post-backup change.',
        'sections': [
            ('Freeze deployment while state is uncertain', 'After a registry database failure, serving replicas may still have a model loaded. Do not restart them blindly against an empty or stale registry. Pin current served digests from endpoint telemetry and stop automatic promotion while the restore runs. Restore the database and artifact objects into an isolated environment, then compare its active alias with the deployment pointer and append-only promotion records. [[mlops/model-registry-promotion-gates|Normal promotion gates]] remain in force during recovery.'),
            ('Classify divergent states', 'There are several distinct cases: the restored alias points to an artifact absent from backup, serving runs a newer approved digest, serving runs a digest with no surviving approval, or the restored alias is older but safe. Each needs a disposition. Preserve the prior pointer and evidence; do not choose by timestamp alone because clocks and replication lag can disagree. [[mlops/promotion-attestation-and-reversible-pointer|Attestation]] is the authority for a valid promotion, while [[mlops/registry-backup-artifact-and-metadata-consistency|the backup manifest]] proves the bytes exist.'),
            ('Rebuild a safe pointer', 'For each candidate digest, require available verified bytes, a compatible runtime, approval for the intended environment and a passing smoke contract. If any condition is missing, keep the last known-good serving digest and hold new deployments. Replay post-backup promotion events only after de-duplicating event IDs and validating expected previous pointers. A successful event can be reapplied once; a conflicting one must be reviewed instead of forced. [[mlops/environment-promotion-and-smoke-contracts|Environment smoke tests]] cover the live runtime.'),
            ('Reopen with an audit trail', 'Publish the recovered registry revision, artifact verification results, serving digest per cohort, lost or replayed promotion events and remaining exceptions. Confirm that the UI alias and actual endpoint agree before removing the freeze. Run a rollback test to the previous approved digest. [[mlops/receipt-registry-disaster-drill-project|The project]] includes an approved promotion after the backup boundary and a newer unapproved version that must stay dark.'),
        ],
        'code': '''def restored_pointer(candidate, artifact_digests, approvals, runtime_ok):
    if candidate["digest"] not in artifact_digests:
        return "hold:missing-artifact"
    if candidate["digest"] not in approvals:
        return "hold:unapproved"
    if not runtime_ok.get(candidate["digest"], False):
        return "hold:incompatible-runtime"
    return "restore:" + candidate["digest"]

candidate = {"digest": "receipt-r47"}
assert restored_pointer(candidate, {"receipt-r47"}, {"receipt-r47"},
                        {"receipt-r47": True}) == "restore:receipt-r47"
assert restored_pointer({"digest": "receipt-r48"}, {"receipt-r48"},
                        {"receipt-r47"}, {"receipt-r48": True}) == "hold:unapproved"
''',
        'cost': 'The gate is O(1) expected time and space for indexed evidence sets. A full reconciliation scans promotion events and affected deployments, O(p + d) for p events and d deployments. Freezing promotion delays releases, but is cheaper than silently reassigning production to a version whose approval or bytes did not survive.',
        'mistakes': ['Restarting all serving replicas before checking their loaded digests.', 'Trusting the restored alias as the source of truth by itself.', 'Replaying promotion records without validating the previous pointer.', 'Reopening deployment while the registry UI and serving endpoints disagree.'],
        'related': [M + 'registry-backup-artifact-and-metadata-consistency', M + 'receipt-registry-disaster-drill-project', M + 'model-registry-promotion-gates', M + 'environment-promotion-and-smoke-contracts', M + 'promotion-attestation-and-reversible-pointer'],
    },
    {
        'path': M + 'receipt-registry-disaster-drill-project',
        'title': 'Project: restore a receipt-model registry without changing live decisions',
        'module': R, 'project': True,
        'summary': 'Restore metadata and artifacts from different points, reconcile a promotion and prove the live model remains approved.',
        'sections': [
            ('Create a controlled failure', 'The receipt-risk service has model r47 live and r46 as rollback. A database backup records r47, but artifact replication for r47 is delayed. A later approved promotion event to r48 exists only in the append-only log, and a draft r49 was registered but never approved. Start the drill by pinning the digest actually served on every cohort. Freeze automated promotion, preserve the deployment pointers and isolate the restore. [[mlops/registry-backup-artifact-and-metadata-consistency|Backup consistency]] reveals the missing r47 bytes before any alias is trusted.'),
            ('Restore and classify', 'Restore the metadata checkpoint, obtain r47 bytes from the original artifact store or a verified alternate copy, and hash them against the manifest. If the bytes cannot be recovered, keep the loaded r47 replicas and stage a compatible approved fallback rather than restarting. Compare restored alias, r48 promotion event, r49 draft state and actual deployment identity. [[mlops/registry-restore-and-promotion-reconciliation|Reconciliation]] requires approval and expected previous pointer before r48 can be replayed.'),
            ('Prove behavior before switching', 'Load r47 and r48 in the isolated recovery environment, run the frozen receipt smoke set and verify the policy route and output schema. Rebuild the registry alias only after r48 bytes, approval and runtime all pass. Keep r49 dark even if its version number is highest. Check rollback to r47 and record artifact availability in every region that might serve the model. [[mlops/region-failover-model-and-feature-identity|Region failover identity]] prevents a recovered alias from hiding different deployed bytes.'),
            ('Measure the recovery result', 'Publish time to restore metadata, time to obtain verified artifact bytes, time to reconcile promotions and time to re-enable deployment. Report recovery-point loss, service interruption, missing audit records and follow-up repairs. The drill passes only when serving digests match approved pointers and r49 remains unavailable for production. Repeat after registry schema or artifact-store layout changes; a one-time success does not validate a changed recovery path.'),
        ],
        'code': '''def disaster_drill_gate(serving, approved, available, smoke_passed):
    if not serving:
        return "hold:no-serving-evidence"
    for cohort, digest in serving.items():
        if digest not in approved or digest not in available:
            return "hold:" + cohort
        if digest not in smoke_passed:
            return "hold:smoke-" + cohort
    return "restore-complete"

serving = {"north": "receipt-r47", "south": "receipt-r48"}
assert disaster_drill_gate(serving, {"receipt-r47", "receipt-r48"},
                           {"receipt-r47", "receipt-r48"},
                           {"receipt-r47", "receipt-r48"}) == "restore-complete"
assert disaster_drill_gate(serving, {"receipt-r47"},
                           {"receipt-r47", "receipt-r48"},
                           {"receipt-r47", "receipt-r48"}) == "hold:south"
''',
        'cost': 'The final gate is O(c) time and O(1) extra space for c cohorts. The drill itself pays for isolated infrastructure, artifact copies, load tests and operator time. Recovery objectives are meaningful only when measured against the slowest required component, not just database restore duration.',
        'mistakes': ['Assuming a metadata restore includes model bytes.', 'Promoting the highest restored version without checking approval.', 'Restarting loaded production replicas before an artifact copy is verified.', 'Reporting database restore time as the total recovery time.'],
        'related': [M + 'registry-backup-artifact-and-metadata-consistency', M + 'registry-restore-and-promotion-reconciliation', M + 'region-failover-model-and-feature-identity', M + 'promotion-attestation-and-reversible-pointer', M + 'model-artifact-digest-and-safe-loading'],
    },
    {
        'path': M + 'cascade-model-version-manifest-and-routing',
        'title': 'Model cascades: pin component versions and route decisions',
        'module': C, 'project': False,
        'summary': 'A fast first-stage model and a slower specialist must be released as one routed decision system.',
        'sections': [
            ('Name the cascade as the release unit', 'A receipt pipeline may run a cheap quality detector first, then send uncertain cases to a richer risk model. The final decision depends on both model digests, preprocessing, the uncertainty cutoff and the route policy. Promoting either model alone changes the effective system. Create a cascade manifest containing every component, input and output schema, routing rule, timeout and approved fallback. [[mlops/inference-chain-contracts-and-stage-identity|Inference chain identity]] records the execution path; the cascade manifest records the permitted combinations.'),
            ('Preserve one decision context', 'Every stage should receive the same immutable receipt snapshot or an explicitly versioned derived view. Carry a decision ID, component versions and feature snapshot across the handoff. If the first stage times out, do not treat its absent score as “low risk”; choose a documented fallback or manual route. If the second stage fails, preserve the first-stage result and error state without inventing a final score. [[mlops/stage-deadline-and-degraded-path-tests|Deadline tests]] expose these cases.'),
            ('Measure routed populations', 'The specialist only sees cases selected by the first stage, so its observed quality and latency cannot be compared to the full population without route coverage. Evaluate the complete cascade on a frozen end-to-end set, then inspect each branch, threshold boundary and cohort. Count manual routes and missing outcomes. [[mlops/selective-label-observation-and-audit-sampling|Selective labels]] matter when a branch changes which receipts receive review.'),
            ('Roll out a compatible pair', 'Preload all required component artifacts and prove schema and runtime compatibility before moving the cascade pointer. Stage a sticky cohort, observe branch proportions and tail latency, then expand. Keep the prior complete manifest as rollback; rolling back only one component can create an untested pair. [[mlops/cascade-budget-and-degraded-path-gates|The budget gate]] protects tail cost, and [[mlops/receipt-cascade-release-project|the project]] catches a schema mismatch hidden by a happy-path smoke test.'),
        ],
        'code': '''def cascade_route(quality_score, quality_model, risk_model,
                  review_threshold=0.64):
    if not quality_model or not risk_model:
        raise ValueError("component digests required")
    if quality_score is None:
        return {"route": "manual-review", "reason": "quality-unavailable"}
    if not 0 <= quality_score <= 1:
        raise ValueError("invalid score")
    return {"route": "risk-model" if quality_score < review_threshold
            else "fast-accept", "quality_digest": quality_model,
            "risk_digest": risk_model}

assert cascade_route(0.47, "quality-r8", "risk-r31")["route"] == "risk-model"
assert cascade_route(None, "quality-r8", "risk-r31")["route"] == "manual-review"
''',
        'cost': 'Routing is O(1) time and space per request. Total compute is first-stage cost plus specialist cost multiplied by route share; tail latency also includes handoff and fallback. A lower specialist share can save compute yet miss difficult receipts, so route changes need end-to-end quality gates rather than a cost-only target.',
        'mistakes': ['Promoting one component while leaving an incompatible partner live.', 'Interpreting a missing first-stage score as a safe result.', 'Reporting specialist accuracy as if it covered every receipt.', 'Rolling back one digest instead of the complete cascade manifest.'],
        'related': [M + 'cascade-budget-and-degraded-path-gates', M + 'receipt-cascade-release-project', M + 'inference-chain-contracts-and-stage-identity', M + 'stage-deadline-and-degraded-path-tests', M + 'selective-label-observation-and-audit-sampling'],
    },
    {
        'path': M + 'cascade-budget-and-degraded-path-gates',
        'title': 'Cascade release gates: branch quality, deadlines and cost',
        'module': C, 'project': False,
        'summary': 'A cascade must meet branch-specific quality and a full-request deadline, including when a component fails.',
        'sections': [
            ('Budget every branch', 'Write a deadline for the complete receipt decision, then divide it among preprocessing, first-stage scoring, specialist scoring, routing overhead and fallback. Do not promise the specialist its full standalone timeout after the first stage has already consumed most of the request budget. Measure p99 end-to-end by branch, not an average of component p99 values. [[mlops/inference-latency-budget-and-tail-observation|Tail observation]] shows the experienced deadline; [[mlops/stage-deadline-and-degraded-path-tests|degraded-path tests]] exercise failures.'),
            ('Gate quality at route boundaries', 'Include receipts just above and below the first-stage cutoff, low-quality scans, large purchase amounts and missing fields. Recalculate which cases reach the specialist when either model or cutoff changes. If fewer cases reach it, verify whether missed-risk rate rises in the fast branch. A branch with little traffic may need a wider uncertainty interval and a longer canary. [[mlops/slice-quality-gates-and-uncertainty|Slice gates]] protect small but important cohorts.'),
            ('Count capacity and economic effects', 'Estimate cost per completed decision from first-stage work, specialist route share, retries and manual fallbacks. The specialist may need reserved capacity for a sudden shift in route share; autoscaling based only on total request rate can lag. Distinguish model budget from reviewer budget. [[mlops/inference-cost-ledger-and-allocation|The cost ledger]] provides an allocation, while [[mlops/multi-model-admission-and-noisy-neighbors|multi-model admission]] protects shared host capacity.'),
            ('Test promotion and rollback', 'Warm both components, validate interstage schema, inject a first-stage timeout and a specialist crash, and check the selected fallback. Stage the manifest as one versioned unit. Monitor branch share, missing stages, route errors, p99 and outcome coverage before expanding. A failed canary restores the prior manifest and its policy, not just the model that most recently changed. [[mlops/receipt-cascade-release-project|The project]] applies these gates to a receipt-quality plus risk cascade.'),
        ],
        'code': '''def cascade_release_gate(quality_ok, branch_p99_ms, branch_budget_ms,
                         missed_fast_cases, max_missed_fast_cases):
    if not quality_ok:
        return "hold:quality"
    if not branch_p99_ms or set(branch_p99_ms) != set(branch_budget_ms):
        return "hold:branch-evidence"
    if any(branch_p99_ms[name] > branch_budget_ms[name]
           for name in branch_p99_ms):
        return "hold:deadline"
    if missed_fast_cases > max_missed_fast_cases:
        return "hold:fast-branch-errors"
    return "stage:cascade"

latency = {"fast": 41, "specialist": 86, "fallback": 70}
budget = {"fast": 57, "specialist": 94, "fallback": 82}
assert cascade_release_gate(True, latency, budget, 2, 3) == "stage:cascade"
assert cascade_release_gate(True, {**latency, "specialist": 101},
                            budget, 2, 3) == "hold:deadline"
''',
        'cost': 'The branch gate is O(b) time and O(1) extra space for b branches. Benchmarks and adjudicated quality checks dominate operational cost. Specialist reserve capacity raises idle spend, but underprovisioning can turn a route-share shift into a deadline failure; size it from burst and branch-share observations.',
        'mistakes': ['Adding component p99 values to claim an end-to-end p99.', 'Checking only the common fast branch.', 'Reducing specialist traffic without testing missed risk.', 'Restoring an old model with a new routing cutoff after a failed canary.'],
        'related': [M + 'cascade-model-version-manifest-and-routing', M + 'receipt-cascade-release-project', M + 'inference-latency-budget-and-tail-observation', M + 'slice-quality-gates-and-uncertainty', M + 'inference-cost-ledger-and-allocation'],
    },
    {
        'path': M + 'receipt-cascade-release-project',
        'title': 'Project: release a receipt-quality and risk-model cascade',
        'module': C, 'project': True,
        'summary': 'Pin two model artifacts and a routing policy, test every branch and stage a reversible cascade release.',
        'sections': [
            ('Freeze the pair', 'The first model checks whether a receipt image is readable; uncertain images go to a specialist risk model. Pin quality-model digest, specialist digest, preprocessing revisions, interstage schema, cutoff, deadline, fallback policy and prior complete manifest. A new quality model emits a confidence field under a different name, so a happy-path test that bypasses the specialist does not catch the mismatch. [[mlops/cascade-model-version-manifest-and-routing|The cascade manifest]] blocks an unqualified pair.'),
            ('Replay all branches', 'Run a frozen set with clear scans, borderline scans, corrupted inputs and high-value blurry receipts. Compare final route, branch exposure, score and latency to the approved cascade. Inject a first-stage timeout, specialist failure and missing confidence field. The schema mismatch must hold promotion rather than defaulting the specialist input to zero. [[mlops/cascade-budget-and-degraded-path-gates|Branch gates]] include a manual fallback under the full-request deadline.'),
            ('Stage under real load', 'Correct the schema contract and preload both artifacts on the target host classes. Stage a small sticky cohort, then compare branch share, fast-branch misses, specialist capacity, p99 and manual review load. A shift in scan quality can suddenly send more traffic to the specialist, so test a burst before expanding. [[mlops/multi-model-admission-and-noisy-neighbors|Shared capacity admission]] protects other models on the same nodes. [[mlops/selective-label-observation-and-audit-sampling|Audit coverage]] checks released receipts that routine review never sees.'),
            ('Finish with a reversible release packet', 'Record the approved pair, route-policy revision, replay evidence, host matrix, canary exposure and prior full manifest. Promote one cascade pointer only after all components are ready. In rollback, restore the old pair and cutoff together; do not leave a new quality model feeding the old specialist. Track branch-level outcomes until they mature. If the specialist fails later, a documented fallback route and owner must be available before the first customer-facing failure.'),
        ],
        'code': '''def cascade_manifest_ready(manifest, available_artifacts, schema_pairs):
    pair = (manifest["quality_digest"], manifest["risk_digest"])
    if not set(pair).issubset(available_artifacts):
        return "hold:artifact"
    if pair not in schema_pairs:
        return "hold:interstage-schema"
    if manifest["fallback"] not in {"manual-review", "prior-cascade"}:
        return "hold:fallback"
    return "stage:complete-manifest"

manifest = {"quality_digest": "quality-r8", "risk_digest": "risk-r31",
            "fallback": "manual-review"}
assert cascade_manifest_ready(manifest, {"quality-r8", "risk-r31"},
                              {("quality-r8", "risk-r31")}) == \
       "stage:complete-manifest"
assert cascade_manifest_ready(manifest, {"quality-r8", "risk-r31"},
                              set()) == "hold:interstage-schema"
''',
        'cost': 'The compatibility gate is O(1) expected time and space for indexed artifact and schema sets. End-to-end replay costs two model executions on routed cases, and warm specialist capacity may remain idle during ordinary traffic. That cost should be compared with avoided manual review and missed-risk cost, never used alone to waive branch quality.',
        'mistakes': ['Testing only clear scans that skip the specialist.', 'Defaulting a missing interstage field to a safe-looking score.', 'Canarying a pair without burst capacity for the specialist.', 'Rolling back one component while retaining the new cutoff and schema.'],
        'related': [M + 'cascade-model-version-manifest-and-routing', M + 'cascade-budget-and-degraded-path-gates', M + 'multi-model-admission-and-noisy-neighbors', M + 'selective-label-observation-and-audit-sampling', M + 'promotion-attestation-and-reversible-pointer'],
    },
]

crosslinks = [
    (M + 'run-manifest-and-artifact-lineage', M + 'registry-backup-artifact-and-metadata-consistency'),
    (M + 'model-registry-promotion-gates', M + 'registry-restore-and-promotion-reconciliation'),
    (M + 'region-failover-model-and-feature-identity', M + 'receipt-registry-disaster-drill-project'),
    (M + 'inference-chain-contracts-and-stage-identity', M + 'cascade-model-version-manifest-and-routing'),
    (M + 'stage-deadline-and-degraded-path-tests', M + 'cascade-budget-and-degraded-path-gates'),
    (M + 'multi-model-admission-and-noisy-neighbors', M + 'receipt-cascade-release-project'),
]

if __name__ == '__main__':
    publish(lessons, (R, C), crosslinks,
            'aitrove-mlops-registry-cascade-import-20261006.json', 6190,
            subject='mlops', hub_path=M + 'mlops-tutorial')
