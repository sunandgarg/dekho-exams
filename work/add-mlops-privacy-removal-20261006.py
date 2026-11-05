"""Add privacy exposure audits and training-data removal operations."""
from de_batch_publisher import publish

M = 'mlops/'
PRIVACY = 'Model privacy exposure audit and release gates'
REMOVAL = 'Training-data removal and model replacement'
lessons = [
    {
        'path': M + 'membership-exposure-audit-frame-and-limits',
        'title': 'Membership exposure audits: test train-versus-holdout distinguishability',
        'module': PRIVACY, 'project': False,
        'summary': 'A membership exposure audit asks whether model outputs help distinguish training records from comparable nontraining records.',
        'sections': [
            ('Define a narrow question', 'A retail-return classifier predicts whether a return needs manual review. The privacy team wants to know whether its exposed probabilities reveal something about which cases were used for training. Build a permitted audit with known member and nonmember records, then fix the observable output fields and a predeclared attack statistic. The result describes this audit frame and access level, not every possible adversary. [[mlops/prediction-api-output-contract-and-exposure-budget|API output scope]] determines what an ordinary caller can observe.'),
            ('Make cohorts comparable', 'Members and nonmembers should represent the same acquisition period, return types and labeling procedure where possible. A naive comparison of old training returns against newly collected returns can detect time drift rather than membership. Group related transactions by account to avoid near duplicates across cohorts. Keep audit samples separate from model tuning and threshold selection. If the attacker has only route labels, audit that surface; do not score with internal logits and present the result as public API risk. [[mlops/snapshot-split-and-environment-replay|Split replay]] helps preserve cohort identities.'),
            ('Predeclare a test and report uncertainty', 'One simple diagnostic marks an example as a likely member if its exposed confidence exceeds a fixed threshold. Count true-positive and false-positive rates on balanced, matched cohorts, and report their difference with sample sizes. A positive gap merits investigation; a zero gap does not prove privacy. More capable attacks or subgroup effects may still exist. Repeat across model revisions and output scopes without tuning the threshold on the same protected audit results. [[mlops/membership-risk-mitigation-and-retest|Mitigation review]] compares the same evaluation plan after a change.'),
            ('Handle audit data carefully', 'Audit records themselves can contain sensitive return details. Use approved identifiers, restrict raw inputs, separate the audit ledger from public telemetry and set retention. Store model digest, output scope, cohort definition, test threshold and result ID. Do not release record-level membership guesses to general dashboards. [[mlops/inference-logging-privacy|Inference logging limits]] apply here too; [[mlops/returns-privacy-audit-project|the project]] demonstrates why unmatched cohorts make a dramatic but misleading result.'),
        ],
        'code': '''def fixed_threshold_membership_audit(members, nonmembers, threshold):
    if not members or not nonmembers:
        return {"state": "hold:empty-cohort"}
    member_hits = sum(score >= threshold for score in members)
    nonmember_hits = sum(score >= threshold for score in nonmembers)
    true_positive_rate = member_hits / len(members)
    false_positive_rate = nonmember_hits / len(nonmembers)
    return {"state": "measured", "member_count": len(members),
            "nonmember_count": len(nonmembers),
            "true_positive_rate": true_positive_rate,
            "false_positive_rate": false_positive_rate,
            "rate_gap": true_positive_rate - false_positive_rate}

report = fixed_threshold_membership_audit(
    [0.82, 0.74, 0.43, 0.91], [0.39, 0.58, 0.72, 0.31], 0.70)
assert report["true_positive_rate"] == 0.75
assert report["false_positive_rate"] == 0.25
assert report["rate_gap"] == 0.5
''',
        'cost': 'This fixed-threshold diagnostic is O(m + n) time and O(1) extra space for m members and n nonmembers. A fuller audit costs additional model queries, matched labeling and controlled review. Small cohorts produce noisy rates; a single low-cost test is useful for triage but cannot certify privacy.',
        'mistakes': ['Comparing old training data with a newer holdout and calling time drift membership leakage.', 'Selecting the threshold after seeing the protected audit result.', 'Testing internal model logits while claiming risk from a route-only public API.', 'Treating a low measured gap as proof that no privacy attack can succeed.'],
        'related': [M + 'membership-risk-mitigation-and-retest', M + 'returns-privacy-audit-project', M + 'prediction-api-output-contract-and-exposure-budget', M + 'inference-logging-privacy', M + 'snapshot-split-and-environment-replay'],
    },
    {
        'path': M + 'membership-risk-mitigation-and-retest',
        'title': 'Privacy release gates: reduce exposed detail and retest model utility',
        'module': PRIVACY, 'project': False,
        'summary': 'An exposure concern calls for a scoped response and a repeated audit, without claiming that one mitigation removes all privacy risk.',
        'sections': [
            ('Separate interface and model changes', 'If a route-only client receives unnecessary probabilities, first fix its response contract. If a client legitimately needs calibrated probabilities, changing the interface may break an approved workflow; consider access scope, rate controls and a model-level review. More aggressive regularization or privacy-preserving training changes the model and needs a fresh quality gate. A restricted output can lower one attacker’s information but does not establish a universal privacy guarantee. [[mlops/prediction-api-output-contract-and-exposure-budget|Output contracts]] keep the least necessary fields per client.'),
            ('Re-run the same audit frame', 'Pin member and nonmember cohort definitions, observable fields, model versions and fixed test protocol before comparing incumbent and candidate. Changing the cohort or attack threshold between releases makes an apparent improvement hard to interpret. Report exposure diagnostic, task quality, minority-slice quality, latency and review volume together. A model can look safer under one test yet miss harmful returns. [[mlops/slice-quality-gates-and-uncertainty|Slice gates]] remain binding.'),
            ('Review residual uncertainty', 'A fixed-threshold confidence test is one lens. Record which attacker access was simulated, how many queries were allowed and which outputs were visible. If an audit found no detectable gap, describe it as a result on that frame rather than declaring the model private. A different attack or cohort may behave differently. Escalate high-impact findings to the security and data owners, who decide response scope and retention. [[mlops/membership-exposure-audit-frame-and-limits|The audit frame]] establishes the evidence boundary.'),
            ('Ship a reversible release', 'Treat response-scope and model changes as separate versioned components. Shadow, canary and rollback each with their own owner. Preserve the previous endpoint response for authorized clients until migration tests pass, but avoid keeping a broad unneeded score field available indefinitely. [[mlops/inference-client-migration-and-contract-tests|Client tests]] validate mixed versions; [[mlops/returns-privacy-audit-project|the project]] rejects a candidate with better audit numbers but unacceptable return-review quality.'),
        ],
        'code': '''def privacy_release_gate(report, limits):
    if report["unapproved_output_fields"]:
        return "hold:output-scope"
    if report["audit_gap"] > limits["maximum_audit_gap"]:
        return "hold:exposure-review"
    if report["rare_return_recall"] < limits["minimum_rare_recall"]:
        return "hold:quality"
    if not report["client_contract_passed"]:
        return "hold:client-contract"
    return "canary:scoped-response"

limits = {"maximum_audit_gap": 0.18, "minimum_rare_recall": 0.82}
report = {"unapproved_output_fields": 0, "audit_gap": 0.11,
          "rare_return_recall": 0.76, "client_contract_passed": True}
assert privacy_release_gate(report, limits) == "hold:quality"
assert privacy_release_gate({**report, "rare_return_recall": 0.87},
                            limits) == "canary:scoped-response"
''',
        'cost': 'The aggregate gate is O(1) time and space; repeating audits requires model calls and controlled sample handling. Narrowing an API response is cheap, but migrating clients and retraining a model can be expensive. A release should not trade away rare-case quality merely to improve one exposure diagnostic.',
        'mistakes': ['Calling output rounding a complete privacy defense.', 'Comparing audits with different cohort or attacker access definitions.', 'Shipping a lower audit gap while rare-return quality fails.', 'Forgetting that approved probability consumers need contract migration.'],
        'related': [M + 'membership-exposure-audit-frame-and-limits', M + 'returns-privacy-audit-project', M + 'prediction-api-output-contract-and-exposure-budget', M + 'inference-client-migration-and-contract-tests', M + 'slice-quality-gates-and-uncertainty'],
    },
    {
        'path': M + 'returns-privacy-audit-project',
        'title': 'Project: audit privacy exposure in a return-review model',
        'module': PRIVACY, 'project': True,
        'summary': 'Match audit cohorts, limit client output fields and hold a model change that harms rare-return review.',
        'sections': [
            ('Inventory what clients can see', 'A return-review service sends route and reason to warehouse scanners, but an older API revision also exposes a high-precision probability. Pin model digest, response scope and caller class. Create a permitted audit with known training and nontraining returns from the same period and comparable channels. Keep account-group boundaries intact. [[mlops/membership-exposure-audit-frame-and-limits|The audit frame]] is limited to outputs a given caller could actually receive.'),
            ('Catch a confounded result', 'The first diagnostic compares training records from one seasonal promotion with holdout records from another. Its large confidence gap looks alarming, but the periods have different return patterns. Mark that run incomparable. Rebuild matched cohorts, freeze a threshold before scoring and report true-positive and false-positive rates, counts and the resulting gap. A low gap is not a blanket privacy certificate.'),
            ('Test mitigation and task utility', 'Remove probability from the scanner response while retaining it only for the approved risk desk. A separately trained candidate has a lower measured exposure gap but misses rare damaged-item returns that the incumbent flags. Hold that candidate. [[mlops/membership-risk-mitigation-and-retest|The release gate]] requires both privacy evidence and protected task quality. Validate risk-desk contracts before changing its output scope.'),
            ('Publish a controlled packet', 'Record cohort definitions, output access, threshold, model revisions, diagnostic rates, task slices, caller migrations and canary owner. Keep record-level audit guesses out of broad dashboards. If a later candidate passes, canary the scoped response and monitor client failures; investigate any residual concerns without presenting one diagnostic as proof. Connect the packet to [[mlops/inference-logging-privacy|log retention]] and [[mlops/model-registry-promotion-gates|registry review]].'),
        ],
        'code': '''def privacy_case_disposition(audit, candidate, limits):
    if not audit["cohorts_matched"] or not audit["threshold_predeclared"]:
        return "hold:audit-design"
    if candidate["rare_damage_recall"] < limits["rare_damage_recall"]:
        return "hold:task-quality"
    if audit["rate_gap"] > limits["rate_gap"]:
        return "review:exposure"
    return "canary:scoped-client"

limits = {"rare_damage_recall": 0.82, "rate_gap": 0.18}
audit = {"cohorts_matched": True, "threshold_predeclared": True,
         "rate_gap": 0.11}
candidate = {"rare_damage_recall": 0.76}
assert privacy_case_disposition(audit, candidate, limits) == "hold:task-quality"
assert privacy_case_disposition(audit, {"rare_damage_recall": 0.87},
                                limits) == "canary:scoped-client"
''',
        'cost': 'The gate is O(1) time and space after reports are prepared. Matched audit data, human-reviewed rare-return labels and client contract tests are the expensive parts. Restricting the scanner response reduces one exposure surface without requiring the team to discard a useful incumbent model prematurely.',
        'mistakes': ['Calling a season difference evidence of membership leakage.', 'Publishing per-record membership guesses to a general dashboard.', 'Removing probabilities from a client that is approved to use them.', 'Promoting a candidate with weaker rare-damage recall because one audit gap fell.'],
        'related': [M + 'membership-exposure-audit-frame-and-limits', M + 'membership-risk-mitigation-and-retest', M + 'inference-logging-privacy', M + 'prediction-api-output-contract-and-exposure-budget', M + 'model-registry-promotion-gates'],
    },
    {
        'path': M + 'training-record-removal-lineage-and-impact-map',
        'title': 'Training-record removal: trace source rows into models and caches',
        'module': REMOVAL, 'project': False,
        'summary': 'A removal workflow starts with a versioned impact map from source records to snapshots, derived data and deployed artifacts.',
        'sections': [
            ('Resolve the record identity', 'A customer-service classifier was trained on ticket histories. An approved internal removal request identifies a set of ticket IDs. Resolve those IDs through raw storage, normalized examples, deduplicated groups, training snapshots and any feature cache. Preserve a minimal tombstone keyed by stable ID so the same row cannot be reintroduced by a later backfill. The request owner determines scope and retention exceptions; a pipeline should not infer them from one database delete. [[mlops/run-manifest-and-artifact-lineage|Run manifests]] make snapshot-to-model lineage queryable.'),
            ('Find every affected artifact', 'Traverse snapshot manifests to training runs, calibrators, indexes and model registry entries. Include archived artifacts that might be restored, shadow deployments and batch jobs using a pinned old model. A row removed from the latest dataset can still influence an older model served to clients. Record affected artifact digest, serving pointer, owner and disposition. [[mlops/model-consumer-inventory-and-retirement-gates|Consumer inventory]] identifies where each model revision still runs.'),
            ('Choose an approved replacement route', 'Where removal from the trained model is required by the governing policy, a clean retrain from an unaffected checkpoint and filtered snapshot is a straightforward baseline. A claimed shortcut needs its own defined evidence and should not be treated as equivalent by default. Preserve quality gates and audit history while avoiding raw removed records in general logs. A train-data deletion does not by itself erase backups, derived features or already trained weights. [[mlops/removal-retrain-and-artifact-reconciliation|Replacement controls]] verify each layer separately.'),
            ('Stop reintroduction', 'Add the tombstone to source admission and backfill filters before running a new snapshot. Check late events, retry queues and data imports against it. Retain the tombstone only under the organization’s approved policy and access controls. [[mlops/training-source-admission-and-quarantine|Source admission]] should reject affected IDs; [[mlops/ticket-removal-replacement-project|the project]] catches an archived model restored after the replacement was deployed.'),
        ],
        'code': '''def affected_artifacts(record_ids, snapshot_members, snapshot_to_models):
    affected_snapshots = {snapshot for snapshot, members in snapshot_members.items()
                          if members.intersection(record_ids)}
    affected_models = set()
    for snapshot in affected_snapshots:
        affected_models.update(snapshot_to_models.get(snapshot, ()))
    return affected_snapshots, affected_models

members = {"tickets-s47": {"ticket-47", "ticket-82"},
           "tickets-s48": {"ticket-91"}}
models = {"tickets-s47": {"router-r8", "router-r9"},
          "tickets-s48": {"router-r10"}}
snapshots, artifacts = affected_artifacts({"ticket-82"}, members, models)
assert snapshots == {"tickets-s47"}
assert artifacts == {"router-r8", "router-r9"}
''',
        'cost': 'The simple scan is O(S × R + E) in the worst case for S snapshots, R average IDs per snapshot and E model edges; an inverted record-to-snapshot index reduces lookup cost. Maintaining complete lineage and tombstone checks consumes storage, but reconstructing influence after manifests are lost is much more expensive and often impossible.',
        'mistakes': ['Deleting one source row and assuming deployed weights changed.', 'Ignoring archived model copies and batch jobs during the impact map.', 'Rebuilding before late imports are filtered by the removal tombstone.', 'Claiming an approximate removal shortcut is equivalent to clean retraining without evidence.'],
        'related': [M + 'removal-retrain-and-artifact-reconciliation', M + 'ticket-removal-replacement-project', M + 'run-manifest-and-artifact-lineage', M + 'model-consumer-inventory-and-retirement-gates', M + 'training-source-admission-and-quarantine'],
    },
    {
        'path': M + 'removal-retrain-and-artifact-reconciliation',
        'title': 'Data-removal releases: retrain, replace and block stale restores',
        'module': REMOVAL, 'project': False,
        'summary': 'A replacement is complete only when approved new artifacts serve every relevant consumer and old artifacts cannot silently return.',
        'sections': [
            ('Build a filtered, reproducible candidate', 'Create a new training snapshot that excludes approved record IDs and their derived copies. Pin filtering code, tombstone revision, source watermark, label taxonomy, random seed and base checkpoint. Avoid resuming from a checkpoint that already incorporated removed records when the policy requires a clean rebuild. Train and evaluate a new model and calibrator as distinct artifacts. [[mlops/snapshot-split-and-environment-replay|Snapshot replay]] makes the replacement reproducible.'),
            ('Test utility and removal scope separately', 'The candidate still needs task quality, slice performance and inference contract gates. A manifest check that removed IDs are absent proves only that the new input snapshot omitted them. It does not prove that all historic artifacts were purged, nor does a low membership-audit score certify removal. Review the scope of backup and incident evidence with the authorized data owner. [[mlops/membership-exposure-audit-frame-and-limits|Privacy audits]] answer a different question.'),
            ('Reconcile serving and storage', 'Enumerate production, shadow, batch, edge and archived model pointers. Move each approved consumer to the replacement or stop it, then disable stale artifact restoration paths. A registry backup restored later may recreate a pointer to the old model; reconciliation must reject it or keep that revision unavailable. Record disposition for every affected digest. [[mlops/registry-restore-and-promotion-reconciliation|Registry restore controls]] provide the recovery hook, and [[mlops/model-consumer-inventory-and-retirement-gates|consumer inventory]] supplies completeness.'),
            ('Close with evidence and an owner', 'Publish the request ID, approved scope, affected source and model digests, filtered snapshot, evaluation report, consumer migration states, backup disposition and unresolved exceptions. Do not mark complete while a batch job still reads the old model or a cache can reintroduce the source record. [[mlops/ticket-removal-replacement-project|The project]] rehearses a stale registry restore after the new pointer was promoted.'),
        ],
        'code': '''def removal_release_gate(request, inventory):
    if not request["filtered_snapshot_verified"]:
        return "hold:snapshot"
    if not request["quality_gates_passed"]:
        return "hold:quality"
    unresolved = [item for item in inventory if item["affected"]
                  and item["state"] not in {"replaced", "disabled"}]
    if unresolved:
        return "hold:affected-consumer"
    if not request["restore_blocked"]:
        return "hold:stale-restore"
    return "close:verified-scope"

request = {"filtered_snapshot_verified": True, "quality_gates_passed": True,
           "restore_blocked": True}
inventory = [{"affected": True, "state": "replaced"},
             {"affected": True, "state": "active"}]
assert removal_release_gate(request, inventory) == "hold:affected-consumer"
assert removal_release_gate(request, [{"affected": True,
       "state": "disabled"}],) == "close:verified-scope"
''',
        'cost': 'The gate scans c consumers in O(c) time and O(c) temporary space. Clean retraining can cost a full training run plus evaluation and migration. Keeping old models unavailable during incident recovery requires registry controls; otherwise the apparent saving from a quick source delete may be undone by a later restore.',
        'mistakes': ['Using a parent checkpoint trained on the removed records for a supposed clean rebuild.', 'Equating a filtered snapshot with total removal across all artifacts.', 'Leaving shadow or batch consumers on affected model revisions.', 'Closing the request while a registry backup can restore the old pointer.'],
        'related': [M + 'training-record-removal-lineage-and-impact-map', M + 'ticket-removal-replacement-project', M + 'snapshot-split-and-environment-replay', M + 'registry-restore-and-promotion-reconciliation', M + 'model-consumer-inventory-and-retirement-gates'],
    },
    {
        'path': M + 'ticket-removal-replacement-project',
        'title': 'Project: replace a ticket classifier after a training-record removal',
        'module': REMOVAL, 'project': True,
        'summary': 'Trace affected ticket IDs, rebuild from a filtered snapshot and stop a stale model from returning through a registry restore.',
        'sections': [
            ('Map the approved request', 'An internal data owner approves removal of ticket 82 from a support-ticket classifier. Map the ID to raw and normalized records, snapshots, derived caches, model runs and a batch-scoring job. Discover two affected model digests, including one archived revision that is absent from the current production pointer. [[mlops/training-record-removal-lineage-and-impact-map|The impact map]] prevents an apparently unused archived artifact from escaping review.'),
            ('Rebuild cleanly', 'Apply a stable tombstone before the next source import and create a new snapshot without the ticket or its derived copies. Do not resume from an affected checkpoint. Train a candidate, recalibrate if required, and pass response-contract and rare-ticket quality gates. Verify the manifest exclusion and store the approved scope, while avoiding a claim that this one check proves every storage copy is gone.'),
            ('Catch the restore failure', 'Move the production and batch consumers to the replacement. Then rehearse a registry restore from an older backup. The restored metadata tries to point a shadow endpoint at the affected model; reconciliation rejects that pointer and keeps the digest unavailable. [[mlops/removal-retrain-and-artifact-reconciliation|Release reconciliation]] holds completion until every affected consumer is replaced or disabled. Record the backup disposition separately from the new model’s quality result.'),
            ('Handoff the evidence', 'Deliver request ID, source tombstone revision, filtered snapshot digest, parent checkpoint proof, candidate evaluation, affected artifact inventory, consumer states and restore-rehearsal result. Note any unresolved retention exception for the authorized data owner rather than guessing. [[mlops/registry-restore-and-promotion-reconciliation|Restore controls]] and [[mlops/model-consumer-inventory-and-retirement-gates|retirement gates]] keep the old route from reappearing.'),
        ],
        'code': '''def ticket_removal_completion(affected_artifacts, consumers, blocked_digests):
    for consumer in consumers:
        if consumer["model_digest"] in affected_artifacts and consumer["active"]:
            return "hold:old-model-active"
    if not affected_artifacts.issubset(blocked_digests):
        return "hold:restore-allowlist"
    return "close:artifact-scope"

affected = {"router-r8", "router-r9"}
consumers = [{"model_digest": "router-r10", "active": True},
             {"model_digest": "router-r8", "active": False}]
assert ticket_removal_completion(affected, consumers, affected) \
       == "close:artifact-scope"
assert ticket_removal_completion(affected, consumers, {"router-r8"}) \
       == "hold:restore-allowlist"
''',
        'cost': 'The completion check is O(c + a) expected time and O(1) extra space for c consumers and a affected digests. The full workflow costs a clean training run, quality evaluation and consumer migration. Inventory and restore tests add operational work, but a replacement that leaves an active old model has not achieved its stated artifact scope.',
        'mistakes': ['Ignoring archived artifacts because only the current production model is visible.', 'Resuming training from a checkpoint that already used the removed record.', 'Marking completion while a batch consumer still uses the old digest.', 'Assuming a registry restore cannot reactivate a disabled revision.'],
        'related': [M + 'training-record-removal-lineage-and-impact-map', M + 'removal-retrain-and-artifact-reconciliation', M + 'registry-restore-and-promotion-reconciliation', M + 'model-consumer-inventory-and-retirement-gates', M + 'run-manifest-and-artifact-lineage'],
    },
]

crosslinks = [
    (M + 'prediction-api-output-contract-and-exposure-budget', M + 'membership-exposure-audit-frame-and-limits'),
    (M + 'inference-client-migration-and-contract-tests', M + 'membership-risk-mitigation-and-retest'),
    (M + 'inference-logging-privacy', M + 'returns-privacy-audit-project'),
    (M + 'run-manifest-and-artifact-lineage', M + 'training-record-removal-lineage-and-impact-map'),
    (M + 'registry-restore-and-promotion-reconciliation', M + 'removal-retrain-and-artifact-reconciliation'),
    (M + 'model-consumer-inventory-and-retirement-gates', M + 'ticket-removal-replacement-project'),
]

if __name__ == '__main__':
    publish(lessons, [PRIVACY, REMOVAL], crosslinks,
            'aitrove-mlops-privacy-removal-import-20261006.json', 6238,
            subject='mlops', hub_path=M + 'mlops-tutorial')
