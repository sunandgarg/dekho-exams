"""Add incident response and model retirement lessons to MLOps."""
from de_batch_publisher import publish

M = 'mlops/'
I = 'Monitoring alerts and incident response'
R = 'Model retirement and retained evidence'

lessons = [
    {
        'path': M + 'model-alert-symptoms-ownership-and-noise',
        'title': 'Model alerts: page on customer symptoms with a named owner',
        'module': I, 'project': False,
        'summary': 'A production model alert is useful only when it identifies customer impact, an owner and an action that can be taken now.',
        'sections': [
            ('Separate immediate symptoms from slow evidence', 'An endpoint timing out is visible now; model accuracy may take 23 days to measure because outcomes arrive later. Page on acute customer symptoms such as timeout rate, invalid responses or a broken fallback. Send feature drift and uncertain quality changes to investigation unless they cross a predeclared operational boundary. A shifted histogram alone does not establish that customers received wrong decisions. [[mlops/drift-delayed-label-monitoring|Delayed-label monitoring]] keeps these clocks separate, while [[mlops/inference-latency-budget-and-tail-observation|latency observation]] captures the live request path.'),
            ('Attach ownership and a first action', 'For each alert, name the on-call team, affected service, model digest, comparison window, expected response and rollback or mitigation route. A page that says only “feature distribution changed” forces the responder to invent the question during an incident. Put a dashboard link in the operational alert configuration, but keep raw personal data out of broad notifications. Route source schema failures to the producer owner and model-quality changes to the model owner, with one coordinator when both are involved.'),
            ('Control noise with counts and duration', 'A ratio from four requests can look dramatic. Require a minimum population, a sustained breach or both, while preserving a fast path for severe safety failures. Group related symptoms under one incident rather than paging separately for queue growth, timeout and fallback volume when they share a cause. Use low-cardinality labels such as service and release; customer ID labels can overwhelm metric storage. A muted alert must have an expiry and owner so it does not become a permanent blind spot.'),
            ('Test the alert as a product', 'Inject a feature-store outage, a model crash, slow requests and a delayed-label gap. Verify that the right owner receives one actionable page for customer impact and that nonurgent monitoring remains visible without repeated pages. Measure detection delay, false pages and time to identify the release. The [[mlops/receipt-model-incident-drill-project|incident drill]] requires a responder to use the alert record, not tribal knowledge, to choose mitigation.'),
        ],
        'code': '''def alert_decision(window):
    total = window["requests"]
    if total < 470:
        return {"state": "observe", "reason": "small-window"}
    timeout_rate = window["timeouts"] / total
    if window["unsafe_decisions"] > 0:
        return {"state": "page", "reason": "unsafe-decision"}
    if timeout_rate > 0.025 and window["breach_minutes"] >= 7:
        return {"state": "page", "reason": "sustained-timeouts"}
    if window["feature_drift"]:
        return {"state": "investigate", "reason": "drift-signal"}
    return {"state": "healthy"}

window = {"requests": 500, "timeouts": 19, "unsafe_decisions": 0,
          "breach_minutes": 8, "feature_drift": False}
assert alert_decision(window)["state"] == "page"
assert alert_decision({**window, "timeouts": 0,
                       "feature_drift": True})["state"] == "investigate"
''',
        'cost': 'A window decision is O(1) time and space once counts are aggregated. Histograms and counters cost storage proportional to label combinations and retention. The example uses illustrative limits; production thresholds need traffic baselines, sampling checks and a policy for severe low-volume failures.',
        'mistakes': ['Paging on every drift statistic as if it proved customer harm.', 'Alerting on a ratio without a denominator.', 'Sending a page with no owner or mitigation step.', 'Muting a noisy alert indefinitely instead of repairing its rule.'],
        'related': [M + 'incident-triage-and-evidence-timeline', M + 'receipt-model-incident-drill-project', M + 'drift-delayed-label-monitoring', M + 'inference-latency-budget-and-tail-observation', M + 'queue-saturation-and-fallback-policy'],
    },
    {
        'path': M + 'incident-triage-and-evidence-timeline',
        'title': 'Model incidents: build a release and evidence timeline before rollback',
        'module': I, 'project': False,
        'summary': 'An incident timeline ties customer symptoms to model, feature, data and infrastructure changes so mitigation targets the failing boundary.',
        'sections': [
            ('Start with the visible failure', 'A receipt service may show higher manual-review volume after a model release. First determine whether the cause is model decisions, feature admission, source lag, queue saturation or a downstream review outage. Record when the symptom began and its customer scope. Compare model digest, feature-contract version, producer revision and serving image around that time. [[mlops/model-alert-symptoms-ownership-and-noise|Actionable alerts]] provide the entry point, not the diagnosis.'),
            ('Keep event time and observation time separate', 'A data pipeline can publish late records whose event timestamps are old. A chart grouped only by event time may make a failure appear to precede the deployment that caused it. Retain deployment time, data availability time, request time and alert observation time. Annotate metric windows and sample counts. When labels are delayed, do not claim quality recovered because the most recent window has few outcomes. [[mlops/prediction-outcome-join-and-maturity|Mature evaluation]] determines when quality evidence is usable.'),
            ('Mitigate by reversing the responsible change', 'If the candidate model caused errors, restore the known-good model and compatible feature producer. If the feature store is stale, rolling back the model alone may leave the outage unchanged. If capacity is exhausted, limit intake and use the approved fallback while scaling or repairing the dependency. Record the exact action, actor, timestamp and pre/post metrics. [[mlops/promotion-attestation-and-reversible-pointer|Promotion evidence]] tells the responder which old digest is loadable; [[mlops/queue-saturation-and-fallback-policy|fallback policy]] defines a safe customer outcome.'),
            ('Close with an evidence-backed review', 'After stabilization, compare request outcomes, error counts and mature quality cohorts. Distinguish a mitigation that reduced errors from a root-cause repair. Keep the incident timeline and the smallest set of restricted examples needed for review under privacy policy. The [[mlops/receipt-model-incident-drill-project|receipt drill]] tests a false model alarm caused by a feature producer, so responders must avoid a reflexive but ineffective model rollback.'),
        ],
        'code': '''def incident_changes(events, symptom_at):
    allowed = {"model", "feature-producer", "serving-image", "data-source"}
    return sorted((event for event in events
                   if event["kind"] in allowed and
                   event["deployed_at"] <= symptom_at),
                  key=lambda event: event["deployed_at"], reverse=True)

events = [{"kind": "model", "deployed_at": 17, "revision": "r8"},
          {"kind": "feature-producer", "deployed_at": 21, "revision": "f4"},
          {"kind": "model", "deployed_at": 29, "revision": "r9"}]
assert [event["revision"] for event in incident_changes(events, 24)] == [
    "f4", "r8"]
''',
        'cost': 'Filtering e release events takes O(e) time; sorting matches takes O(k log k) time and O(k) space. A production timeline also needs clock normalization and provenance checks. Temporal proximity is a clue, not proof of causation; compare affected and unaffected traffic and test the suspected boundary before declaring a root cause.',
        'mistakes': ['Rolling back the model when a feature producer is broken.', 'Treating old event timestamps as deployment chronology.', 'Claiming quality recovered from immature labels.', 'Closing an incident after mitigation without recording the root-cause repair.'],
        'related': [M + 'model-alert-symptoms-ownership-and-noise', M + 'receipt-model-incident-drill-project', M + 'promotion-attestation-and-reversible-pointer', M + 'queue-saturation-and-fallback-policy', M + 'prediction-outcome-join-and-maturity'],
    },
    {
        'path': M + 'receipt-model-incident-drill-project',
        'title': 'Project: run a receipt-model incident drill with honest mitigation',
        'module': I, 'project': True,
        'summary': 'Simulate a customer-visible scoring failure, identify the responsible release and prove the chosen mitigation helps.',
        'sections': [
            ('Prepare the drill', 'The receipt service has a stable model digest, a recent candidate and a feature producer that emits amount in the wrong unit for one region. Introduce a sustained timeout burst as a separate fault. Freeze a timeline with deployment and symptom timestamps, plus request counts by region and outcome. [[mlops/model-alert-symptoms-ownership-and-noise|Alert rules]] should page on customer impact while keeping a drift-only signal in the investigation queue.'),
            ('Require a bounded diagnosis', 'The responder identifies which region and requests are affected, checks feature admission failures, compares model digests and verifies the old artifact remains loadable. A model rollback is a candidate action, not a default answer. The wrong-unit fault needs a producer repair or rejected-input fallback. The timeout burst needs capacity or dependency mitigation. [[mlops/incident-triage-and-evidence-timeline|The evidence timeline]] forces each claim to carry an observation window and release identity.'),
            ('Execute and verify mitigation', 'Route malformed features to approved manual review, stop the faulty producer release and verify that the feature contract accepts new traffic. Bound the inference queue for the timeout incident and return a declared fallback before the deadline. If the candidate model separately fails a quality or safety guardrail, restore the old model and compatible producer together. Record actions and compare pre/post customer outcomes on the same population.'),
            ('Write the review artifact', 'Report time to detection, time to customer mitigation, the first incorrect hypothesis, root cause, recovery tests and follow-up owner. Keep metric dimensions low-cardinality and sensitive receipt payloads restricted. Verify the next on-call person can follow the runbook without access to the original responders. The project is complete when the drill catches an ineffective rollback and demonstrates a mitigation that actually changes the customer symptom.'),
        ],
        'code': '''def mitigation_result(before, after):
    if before["requests"] < 470 or after["requests"] < 470:
        return {"state": "inconclusive", "reason": "small-window"}
    old_rate = before["failed"] / before["requests"]
    new_rate = after["failed"] / after["requests"]
    if new_rate >= old_rate:
        return {"state": "ineffective", "before": old_rate, "after": new_rate}
    return {"state": "improved", "before": old_rate, "after": new_rate}

before = {"requests": 500, "failed": 39}
after = {"requests": 500, "failed": 7}
assert mitigation_result(before, after)["state"] == "improved"
assert mitigation_result(before, before)["state"] == "ineffective"
''',
        'cost': 'The compact comparison is O(1) time and space. Incident analysis costs retained metrics, trace sampling and operator time. A lower post-action failure rate alone does not prove the action caused improvement when traffic mix changes; compare slices and timelines before attributing the result.',
        'mistakes': ['Choosing model rollback before inspecting the feature contract.', 'Using an unapproved safe score as an outage fallback.', 'Comparing pre/post windows with different traffic populations.', 'Ending the drill without an owner for the root-cause repair.'],
        'related': [M + 'model-alert-symptoms-ownership-and-noise', M + 'incident-triage-and-evidence-timeline', M + 'feature-contract-and-admission-gates', M + 'queue-saturation-and-fallback-policy', M + 'shadow-canary-and-rollback'],
    },
    {
        'path': M + 'model-consumer-inventory-and-retirement-gates',
        'title': 'Model retirement: find consumers before removing a version',
        'module': R, 'project': False,
        'summary': 'A model version can be removed only after serving, batch, rollback, audit and replay consumers have explicit replacements or retention decisions.',
        'sections': [
            ('Inventory live and latent consumers', 'The current endpoint is only one consumer. Nightly scoring may pin an old digest, a canary may still receive traffic, and incident rollback may depend on an earlier package. Historical replay, audit investigations and saved evaluation reports may also reference the artifact. List every alias, deployment, scheduled job, workflow and retention obligation by immutable digest. [[mlops/promotion-attestation-and-reversible-pointer|Reversible promotion]] assumes the old artifact remains loadable during the observation window.'),
            ('Separate stop-serving from deletion', 'First stop new traffic and batch jobs from selecting the old version, then verify no hidden consumer resolves its alias. Mark it retired for new work but retain the package and manifest until rollback and evidence windows close. Deletion may be irreversible in a registry, and a renamed pointer can still be used by a worker that cached the old digest. Check actual invocation logs and scheduled definitions rather than assuming an empty dashboard means no dependency.'),
            ('Preserve enough evidence to explain past decisions', 'A historical customer decision may need its model digest, feature contract, training manifest and decision record even if the raw training data reaches its retention limit. Retention rules differ for model packages, personal data and aggregated metrics. Keep the minimal lawful evidence and delete data under the applicable policy; an audit requirement is not a reason to keep unrestricted raw payloads forever. [[mlops/inference-logging-privacy|Inference privacy]] and [[mlops/run-manifest-and-artifact-lineage|lineage]] define what each record contributes.'),
            ('Test a no-consumer state', 'Disable the old alias in staging, run endpoint and batch smoke tests, verify rollback now points to an approved successor and scan scheduled jobs for pinned digests. Require a grace period with zero observed use and an owner sign-off before deleting a package. The [[mlops/receipt-model-retirement-project|retirement project]] includes a hidden nightly batch consumer so the first deletion attempt must hold.'),
        ],
        'code': '''def retirement_gate(model_digest, consumers, rollback_digests,
                    retention_hold):
    active = sorted(name for name, digest in consumers.items()
                    if digest == model_digest)
    if active:
        return {"state": "hold", "reason": "active-consumers", "names": active}
    if model_digest in rollback_digests:
        return {"state": "hold", "reason": "rollback-target"}
    if retention_hold:
        return {"state": "retain", "reason": "evidence-window"}
    return {"state": "eligible-for-review"}

jobs = {"online": "sha256:r8", "nightly": "sha256:r7"}
assert retirement_gate("sha256:r7", jobs, set(), False)["state"] == "hold"
assert retirement_gate("sha256:r7", {"online": "sha256:r8"},
                       set(), True)["state"] == "retain"
''',
        'cost': 'Scanning c declared consumers takes O(c) time and O(a log a) for sorting a active names, with O(a) space. The hard part is inventory completeness: a stale configuration outside the registry may still load the artifact. Treat this function as one gate in an observed-use and retention review, not as deletion authorization.',
        'mistakes': ['Deleting a version because the main endpoint no longer uses it.', 'Removing an artifact still needed for rollback.', 'Keeping raw personal data indefinitely because the model package has an audit hold.', 'Assuming a registry alias inventory includes every pinned batch job.'],
        'related': [M + 'retention-and-derivative-deletion-boundary', M + 'receipt-model-retirement-project', M + 'promotion-attestation-and-reversible-pointer', M + 'batch-inference-partition-and-idempotency', M + 'inference-logging-privacy'],
    },
    {
        'path': M + 'retention-and-derivative-deletion-boundary',
        'title': 'MLOps retention: trace source deletion into features and training artifacts',
        'module': R, 'project': False,
        'summary': 'A deleted source record may survive in feature tables, snapshots, evaluation files and model artifacts unless lineage drives a policy-specific response.',
        'sections': [
            ('Map data derivatives before deciding action', 'A receipt can appear in raw storage, cleaned tables, offline features, online feature caches, training snapshots, sampled debug logs and reports. A trained model may contain information from many records. Record lineage from source class to derivative artifact and the retention policy for each. A deletion request may require removing some derivatives, rebuilding others or preserving narrowly scoped evidence under a valid obligation. Do not promise that deleting one row automatically removes its influence from an existing model. [[mlops/run-manifest-and-artifact-lineage|Training manifests]] help locate affected snapshots.'),
            ('Distinguish deletion from withdrawal', 'A pipeline may delete a source row while a published scoring output remains active. Withdraw or supersede operational outputs under their consumer contract, then clear caches and queued work where required. Keep a restricted tombstone or deletion receipt if policy allows, so a later backfill does not resurrect the record from an old snapshot. [[mlops/batch-replay-versioning-and-consumer-reconciliation|Batch replay]] can produce replacement outputs after source corrections, but customer actions need their own idempotent withdrawal rule.'),
            ('Decide model-level treatment explicitly', 'If a training snapshot contained data that must no longer influence a model, assess whether the model must be retired, retrained from an eligible snapshot or handled under a documented exception. The answer depends on legal and product policy; a generic hash or feature deletion cannot remove learned parameters. Record affected model digests and owners. [[mlops/model-consumer-inventory-and-retirement-gates|Retirement gates]] prevent deleting an affected model before traffic has moved to an approved replacement.'),
            ('Verify the whole path', 'Exercise a test deletion with a source row present in an online cache, a batch output and a training snapshot. Check every derivative under the applicable policy, record unresolved items and test a backfill to ensure the row stays excluded. The [[mlops/receipt-model-retirement-project|retirement project]] keeps a minimal evidence ledger while removing unnecessary copies and replacing an affected model where required.'),
        ],
        'code': '''def affected_derivatives(children_by_parent, source_id):
    pending = [source_id]
    seen = {source_id}
    while pending:
        parent = pending.pop()
        for child in children_by_parent.get(parent, ()):
            if child not in seen:
                seen.add(child)
                pending.append(child)
    seen.remove(source_id)
    return seen

lineage = {"receipt-47": {"feature-82", "batch-129"},
           "feature-82": {"snapshot-91"},
           "snapshot-91": {"model-r7"}}
assert affected_derivatives(lineage, "receipt-47") == {
    "feature-82", "batch-129", "snapshot-91", "model-r7"}
''',
        'cost': 'Traversing reachable lineage takes O(v + e) time and O(v) space for v visited artifacts and e edges. Large shared artifacts can make the affected set broad, so record artifact-level lineage and policy-specific actions. Reachability identifies candidates for review; it does not determine whether deleting, retraining or retaining each item is lawful or technically sufficient.',
        'mistakes': ['Assuming raw-row deletion erases a model’s learned influence.', 'Leaving an online feature cache or batch output active after source withdrawal.', 'Allowing a historical backfill to resurrect a deleted record.', 'Deleting audit evidence without checking its separate retention obligation.'],
        'related': [M + 'model-consumer-inventory-and-retirement-gates', M + 'receipt-model-retirement-project', M + 'run-manifest-and-artifact-lineage', M + 'batch-replay-versioning-and-consumer-reconciliation', M + 'inference-logging-privacy'],
    },
    {
        'path': M + 'receipt-model-retirement-project',
        'title': 'Project: retire a receipt model without breaking batch or audit',
        'module': R, 'project': True,
        'summary': 'Move consumers off an old receipt model, resolve an affected data lineage case and retain only justified evidence.',
        'sections': [
            ('Define the retirement target', 'The receipt endpoint now serves model r8, while r7 remains in a nightly batch definition and a rollback alias. A source receipt in r7’s training snapshot has an active deletion request. Inventory deployed aliases, scheduled jobs, stored outputs, training snapshots and evaluation reports by digest. [[mlops/model-consumer-inventory-and-retirement-gates|Consumer inventory]] must find both visible and latent uses before any package is removed.'),
            ('Stage a safe replacement', 'Move the nightly job to an approved replacement and test the same input partition. Choose a new rollback target that loads under the current feature contract; do not remove r7 until a recovery drill passes. For the deletion case, trace the source through online features, batch output and the training snapshot. Apply the relevant data policy to each derivative and record whether a new model must be trained. [[mlops/retention-and-derivative-deletion-boundary|Derivative lineage]] identifies affected artifacts but leaves policy decisions explicit.'),
            ('Verify absence and preservation', 'Scan job definitions and observed requests for r7, run a grace period with no uses and confirm old operational outputs have been withdrawn or superseded. Keep a minimal manifest and decision ledger when a valid audit obligation remains, while removing unnecessary raw payload copies. Test a backfill that reads an old snapshot; the withdrawn receipt must not reappear. A comparison-only historical replay may still need controlled access to r7 until its retention window ends.'),
            ('Issue the retirement decision', 'Report each consumer’s replacement, last observed use, rollback drill result, lineage actions and retention hold. The outcome may be “stop serving but retain artifact” rather than deletion. If the hidden nightly job still points to r7, the gate must hold. Only a separately authorized cleanup step should delete the package after the evidence and rollback windows close.'),
        ],
        'code': '''def retirement_review(active_consumers, rollback_ready,
                      lineage_resolved, evidence_hold):
    if active_consumers:
        return {"state": "hold", "reason": "consumer-remains"}
    if not rollback_ready:
        return {"state": "hold", "reason": "rollback-not-ready"}
    if not lineage_resolved:
        return {"state": "hold", "reason": "lineage-open"}
    if evidence_hold:
        return {"state": "retire-serving-retain-artifact"}
    return {"state": "eligible-for-cleanup-review"}

assert retirement_review(["nightly-receipts"], True, True, False)[
    "state"] == "hold"
assert retirement_review([], True, True, True)[
    "state"] == "retire-serving-retain-artifact"
''',
        'cost': 'The final state check is O(1) aside from holding the consumer list. Inventory scans, lineage traversal and observed-use windows require storage and operational time. “Eligible for cleanup review” is deliberately not a delete command; package deletion should be a separately authorized action with a tested recovery path.',
        'mistakes': ['Deleting r7 while the nightly batch still pins it.', 'Moving the rollback alias without proving the successor loads.', 'Assuming source deletion resolved every derived copy.', 'Treating an audit hold as permission to retain all raw receipts without limit.'],
        'related': [M + 'model-consumer-inventory-and-retirement-gates', M + 'retention-and-derivative-deletion-boundary', M + 'batch-inference-partition-and-idempotency', M + 'promotion-attestation-and-reversible-pointer', M + 'run-manifest-and-artifact-lineage'],
    },
]

crosslinks = [
    (M + 'drift-delayed-label-monitoring', M + 'model-alert-symptoms-ownership-and-noise'),
    (M + 'shadow-canary-and-rollback', M + 'incident-triage-and-evidence-timeline'),
    (M + 'receipt-serving-slo-project', M + 'receipt-model-incident-drill-project'),
    (M + 'promotion-attestation-and-reversible-pointer', M + 'model-consumer-inventory-and-retirement-gates'),
    (M + 'run-manifest-and-artifact-lineage', M + 'retention-and-derivative-deletion-boundary'),
    (M + 'nightly-receipt-batch-project', M + 'receipt-model-retirement-project'),
]

if __name__ == '__main__':
    publish(lessons, (I, R), crosslinks,
            'aitrove-mlops-incidents-retirement-import-20261006.json', 6118,
            subject='mlops', hub_path=M + 'mlops-tutorial')
