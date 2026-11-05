"""Add ML release testing and feature freshness lessons."""
from de_batch_publisher import publish

M = 'mlops/'
C = 'ML release testing and environment gates'
F = 'Online feature freshness'

lessons = [
    {
        'path': M + 'ml-test-pyramid-and-data-fixtures',
        'title': 'ML tests: separate code, data, model and service failures',
        'module': C, 'project': False,
        'summary': 'An ML release needs small deterministic checks and a few realistic integration checks, each tied to a different failure boundary.',
        'sections': [
            ('Start with the cheapest contract checks', 'A receipt model can pass an accuracy test while its service rejects every request because the amount field changed units. Test parsers, feature transforms, schema admission, missing-value behavior and output shape with tiny fixed fixtures before spending time on training. Keep each fixture under a stated contract version and include invalid as well as valid records. [[mlops/feature-contract-and-admission-gates|Feature admission]] owns the input boundary; these tests prove a release still implements it.'),
            ('Add data and training checks', 'Validate a frozen data snapshot for row identity, label maturity, split isolation, class counts and feature availability. Then train a small deterministic smoke model to verify the pipeline can finish and publish complete artifacts. The smoke run does not establish production quality. Run the full candidate evaluation on a fixed holdout, protected slices and cost limits only after the cheap checks pass. [[mlops/snapshot-split-and-environment-replay|Training replay]] explains why the data and split identities belong in the test record.'),
            ('Test the deployed interface', 'Load the exact candidate artifact in a staging service with the production request schema. Check one accepted request, one rejected request, a deadline breach, a fallback and a rollback load. A model file that loads in a notebook can still fail in a different image or feature environment. Shadow traffic can reveal operational behavior, but it should not be the first time anyone checks the request contract. [[mlops/inference-latency-budget-and-tail-observation|Latency budgets]] turn a vague speed expectation into a measurable service test.'),
            ('Report failure at the right layer', 'A test report should name the artifact digest, fixture revision, environment image and failing boundary. Do not bury a schema failure under “accuracy regression.” Keep test inputs small enough for every code change, then reserve full training and load tests for changes that can affect them. The [[mlops/receipt-ci-release-gate-project|release-gate project]] exercises code, data, model and service failures separately so one broad pass/fail flag cannot hide which layer broke.'),
        ],
        'code': '''def release_checks(results):
    ordered = ("schema", "transform", "data", "training-smoke",
               "quality", "service-smoke", "rollback")
    for check in ordered:
        if check not in results:
            return {"state": "hold", "reason": "missing-" + check}
        if not results[check]:
            return {"state": "hold", "reason": "failed-" + check}
    return {"state": "ready", "checks": len(ordered)}

passing = {name: True for name in ("schema", "transform", "data",
    "training-smoke", "quality", "service-smoke", "rollback")}
assert release_checks(passing)["state"] == "ready"
assert release_checks({**passing, "schema": False}) == {
    "state": "hold", "reason": "failed-schema"}
''',
        'cost': 'Checking k results is O(k) time and O(1) extra space. The expensive checks are full training, evaluation and load testing; ordering cheap failures first reduces wasted compute. A Boolean result is only useful if it is tied to the exact artifact, dataset and environment tested.',
        'mistakes': ['Using one accuracy number as the entire release test.', 'Running costly training before cheap schema checks.', 'Testing a notebook loader but not the deployed request interface.', 'Reusing a passing test report for a different artifact digest.'],
        'related': [M + 'environment-promotion-and-smoke-contracts', M + 'receipt-ci-release-gate-project', M + 'feature-contract-and-admission-gates', M + 'snapshot-split-and-environment-replay', M + 'model-registry-promotion-gates'],
    },
    {
        'path': M + 'environment-promotion-and-smoke-contracts',
        'title': 'Environment promotion: keep the tested artifact and contract together',
        'module': C, 'project': False,
        'summary': 'Promotion moves an immutable model package through environments while proving the serving image and input contract still match.',
        'sections': [
            ('Promote bytes, not a retraining recipe', 'A candidate trained in development should not be retrained from a mutable table when it enters staging. Move or reference the same immutable artifact digest, feature-contract version and evaluation record. The target environment may have different secrets, endpoints and capacity, but model bytes and declared behavior stay identifiable. [[mlops/model-artifact-digest-and-safe-loading|Artifact verification]] checks what was received; [[mlops/promotion-attestation-and-reversible-pointer|promotion evidence]] binds the decision to those bytes.'),
            ('Test environment-specific dependencies', 'Staging can use a different feature store, network policy, identity or hardware class. Run smoke requests against each target environment with expected admission, fallback and output states. Check that the serving image can read only the intended package and that its feature lookup has the required permissions. A passing unit test cannot prove a production service account can reach the correct data. Record the environment identity and observed model digest in the smoke result.'),
            ('Control mutable pointers', 'A registry alias is convenient, but resolving it at different times can select different versions. Resolve the candidate and rollback aliases to immutable digests at the start of a release, then compare them again before moving traffic. Store the old and new pointer values in the release event. If a concurrent release changes the pointer, halt rather than silently overwriting it. [[mlops/shadow-canary-and-rollback|Canary rollout]] needs a known rollback target throughout its observation window.'),
            ('Make rollback a tested transition', 'Promotion is incomplete until the old package can load under the current feature producer and serving image. Stage a request against the rollback digest, then rehearse pointer restoration. If the new feature schema removes an old field, a model-only rollback may fail. The [[mlops/receipt-ci-release-gate-project|CI release project]] forces this compatibility test before any simulated customer traffic moves.'),
        ],
        'code': '''def promotion_transition(candidate, tested, current, rollback):
    if candidate["digest"] != tested["digest"]:
        return {"state": "hold", "reason": "untested-bytes"}
    if candidate["feature_contract"] != tested["feature_contract"]:
        return {"state": "hold", "reason": "contract-mismatch"}
    if not tested["target_smoke_passed"]:
        return {"state": "hold", "reason": "target-smoke"}
    if current["digest"] != rollback["digest"] or not rollback["loadable"]:
        return {"state": "hold", "reason": "rollback-not-ready"}
    return {"state": "ready", "from": current["digest"],
            "to": candidate["digest"]}

candidate = {"digest": "sha256:r9", "feature_contract": "receipt-v4"}
tested = {**candidate, "target_smoke_passed": True}
current = {"digest": "sha256:r8"}
rollback = {"digest": "sha256:r8", "loadable": True}
assert promotion_transition(candidate, tested, current, rollback)["state"] == "ready"
assert promotion_transition({**candidate, "digest": "sha256:other"},
                            tested, current, rollback)["state"] == "hold"
''',
        'cost': 'Comparing a fixed release record is O(1) time and space. Staging environments, load tests and dual-capacity canaries cost resources. The example checks a snapshot of the pointer; a production registry needs an atomic compare-and-swap or equivalent guard against concurrent releases.',
        'mistakes': ['Retraining during environment promotion and calling it the same candidate.', 'Assuming staging permissions match production permissions.', 'Resolving a mutable alias after the test instead of pinning a digest.', 'Keeping a rollback pointer whose model cannot load current features.'],
        'related': [M + 'ml-test-pyramid-and-data-fixtures', M + 'receipt-ci-release-gate-project', M + 'model-artifact-digest-and-safe-loading', M + 'promotion-attestation-and-reversible-pointer', M + 'shadow-canary-and-rollback'],
    },
    {
        'path': M + 'receipt-ci-release-gate-project',
        'title': 'Project: gate a receipt model through CI and staging',
        'module': C, 'project': True,
        'summary': 'Build a release record that carries one model digest from fixture tests through staging smoke checks and rollback rehearsal.',
        'sections': [
            ('Define the candidate package', 'A receipt-risk candidate has a model digest, feature-contract version, frozen evaluation report and serving image digest. CI runs schema, transform, data, training-smoke and quality checks against that package. The target staging service then runs accepted, rejected and fallback requests. [[mlops/ml-test-pyramid-and-data-fixtures|The ML test layers]] identify which failure boundary a result belongs to instead of flattening every failure into an accuracy result.'),
            ('Build adversarial cases', 'Change the amount unit while leaving its type intact, remove one serving permission, swap the artifact after the quality report and make the rollback model incompatible with the new feature producer. Freeze expected hold reasons. A passing average score must not override any of these failures. Store each test result with the package digest and target environment so the report cannot be borrowed by another candidate.'),
            ('Move through staging deliberately', 'Verify package bytes, resolve both candidate and rollback digests, run target-environment smoke checks and compare the registry pointer immediately before transition. A concurrent release should halt the operation. If all gates pass, route a small shadow load and then a canary with known limits. [[mlops/environment-promotion-and-smoke-contracts|Environment promotion]] keeps the tested bytes and contract together; [[mlops/shadow-canary-and-rollback|canary checks]] cover live operation.'),
            ('Produce the reviewable result', 'Report the failed boundary, fixture revision, artifact digest, image digest, data snapshot, target smoke outcome and rollback load result. The project should demonstrate a safe hold for each adversarial case and a clean transition for the complete package. A final “ready” state authorizes the next release step, not an automatic claim that customers saw better outcomes; those require observation and mature labels.'),
        ],
        'code': '''def staged_release(ci, staging, candidate_digest, tested_digest):
    if candidate_digest != tested_digest:
        return {"state": "hold", "reason": "candidate-changed"}
    required_ci = {"schema", "transform", "data", "quality"}
    required_stage = {"accept", "reject", "fallback", "rollback-load"}
    if not required_ci <= {name for name, passed in ci.items() if passed}:
        return {"state": "hold", "reason": "ci"}
    if not required_stage <= {name for name, passed in staging.items() if passed}:
        return {"state": "hold", "reason": "staging"}
    return {"state": "ready", "digest": candidate_digest}

ci = {name: True for name in ("schema", "transform", "data", "quality")}
stage = {name: True for name in ("accept", "reject", "fallback", "rollback-load")}
assert staged_release(ci, stage, "sha256:r9", "sha256:r9")["state"] == "ready"
assert staged_release(ci, {**stage, "rollback-load": False},
                      "sha256:r9", "sha256:r9")["state"] == "hold"
''',
        'cost': 'Evaluating c CI and s staging results takes O(c + s) time and O(c + s) temporary set space. Full training and load tests dominate cost. Passing this simple gate does not verify report issuer identity or enforce atomic registry updates; those remain controls of the release system.',
        'mistakes': ['Accepting quality evidence after the artifact bytes change.', 'Skipping a rejected-input smoke request.', 'Calling a canary safe before checking rollback compatibility.', 'Treating a staging pass as proof of long-term production quality.'],
        'related': [M + 'ml-test-pyramid-and-data-fixtures', M + 'environment-promotion-and-smoke-contracts', M + 'model-registry-promotion-gates', M + 'trusted-model-promotion-project', M + 'receipt-feature-admission-project'],
    },
    {
        'path': M + 'online-feature-freshness-budget-and-ttl',
        'title': 'Online feature freshness: use event and availability clocks',
        'module': F, 'project': False,
        'summary': 'A valid feature value can still be too old for a decision; freshness needs a task-specific limit and explicit missing state.',
        'sections': [
            ('Name both clocks', 'A merchant activity feature has an event time describing the activity and an availability time when the online store received it. A value can have a recent event time but arrive late, or an old event time that was just republished. Record both. For receipt-risk scoring, define a maximum age from event time and a publication lag limit from availability time. [[mlops/feature-training-serving-parity|Training-serving parity]] compares values under a prediction clock; freshness adds a runtime rule for whether the value is usable now.'),
            ('Separate TTL from safety', 'A store TTL may remove records after a configured duration. It does not prove values remaining in the store are fresh enough for every model. A daily merchant category can tolerate more age than a minute-level fraud signal. Enforce the model-specific freshness budget at retrieval, not only in storage configuration. A missing value and an expired value should have distinguishable reason codes, even if both route to the same approved fallback. [[mlops/feature-contract-and-admission-gates|Admission gates]] define that fallback boundary.'),
            ('Choose behavior before an outage', 'When a feature is stale, the service may abstain, use a documented older model that does not require it or send the receipt for review. Do not silently fill the feature with the last cached value and report a normal score. Keep fallback volume and source lag visible by feature view and region. Avoid entity IDs as metric labels; investigate individual records through restricted traces. [[mlops/queue-saturation-and-fallback-policy|Serving fallback]] covers capacity failures, while this policy covers information age.'),
            ('Test late and out-of-order writes', 'Feed an older event after a newer event, a future timestamp, a record exactly at the freshness boundary and an online-store outage. The latest arrival need not be the latest event. Check that a late correction updates historical evidence without overwriting a newer online value improperly. The [[mlops/receipt-feature-freshness-project|freshness project]] tests both serving decisions and the monitoring signals that reveal a stuck materialization job.'),
        ],
        'code': '''from datetime import timedelta

def feature_freshness(record, decision_at, max_age_minutes=47):
    if record is None:
        return {"state": "unavailable", "reason": "missing"}
    event_at = record["event_at"]
    available_at = record["available_at"]
    if event_at > decision_at or available_at > decision_at:
        return {"state": "unavailable", "reason": "future-clock"}
    if decision_at - event_at > timedelta(minutes=max_age_minutes):
        return {"state": "unavailable", "reason": "stale-event"}
    return {"state": "usable", "value": record["value"]}

from datetime import datetime, timezone
now = datetime(2026, 10, 6, tzinfo=timezone.utc)
recent = {"event_at": now - timedelta(minutes=23),
          "available_at": now - timedelta(minutes=4), "value": 82}
assert feature_freshness(recent, now)["state"] == "usable"
assert feature_freshness({**recent, "event_at": now - timedelta(minutes=82)},
                         now)["reason"] == "stale-event"
''',
        'cost': 'One feature check is O(1) time and space. Fetching many feature views adds network latency and monitoring dimensions. A shorter TTL can reduce stale reads but increase misses and recomputation; choose it from decision needs and source update behavior, not as a substitute for a request-time freshness check.',
        'mistakes': ['Treating a stored value as fresh merely because TTL has not deleted it.', 'Using ingestion time in place of event time.', 'Silently scoring with a stale cache value.', 'Allowing an out-of-order older event to replace a newer online value.'],
        'related': [M + 'late-feature-materialization-and-read-repair', M + 'receipt-feature-freshness-project', M + 'feature-training-serving-parity', M + 'feature-contract-and-admission-gates', M + 'queue-saturation-and-fallback-policy'],
    },
    {
        'path': M + 'late-feature-materialization-and-read-repair',
        'title': 'Feature materialization lag: detect stuck updates and repair safely',
        'module': F, 'project': False,
        'summary': 'Online feature publication needs a watermark, entity-level freshness checks and a repair plan that preserves event ordering.',
        'sections': [
            ('Track source and publication progress separately', 'A materialization job can report success while reading no new source partitions. Record the latest source event time seen, latest source partition completed and latest value published online. Compare those watermarks with expected arrival patterns. A global watermark can hide a stalled region, so monitor a bounded set of meaningful slices. [[mlops/online-feature-freshness-budget-and-ttl|Request-time freshness]] still protects individual decisions when a dashboard is late to notice lag.'),
            ('Preserve ordering under late arrival', 'An old merchant event arriving after a newer one belongs in historical storage but should not automatically replace the online value. Compare event time and a deterministic tie-breaker before publishing. If a correction changes a past event, recompute affected historical rows and decide whether current online state must change. [[mlops/batch-replay-versioning-and-consumer-reconciliation|Replay rules]] show why correcting history and changing current operations are separate transitions.'),
            ('Repair a stuck slice', 'Pause or isolate the faulty publisher, identify the last verified partition and replay from that point into a staging view. Reconcile entity counts, duplicate keys, event-time maxima and feature values before swapping the view. A blind “refresh all” can overwrite good current values with stale records or double downstream work. Keep old and new view versions long enough to compare requests. If the source itself is late, refreshing more often does not create information that has not arrived.'),
            ('Test a realistic outage', 'Simulate a region whose source partition stops for 82 minutes while other regions remain current. Confirm freshness fallback appears only where needed, alert ownership points to the source or publisher, and repaired values become usable after event-time checks. The [[mlops/receipt-feature-freshness-project|receipt project]] measures both time to detect the lag and time to restore safe scoring, not just job success.'),
        ],
        'code': '''def choose_online_record(current, arriving):
    if current is None:
        return arriving
    current_key = (current["event_at"], current["revision"])
    arriving_key = (arriving["event_at"], arriving["revision"])
    return arriving if arriving_key > current_key else current

current = {"event_at": 82, "revision": 2, "value": 470}
late = {"event_at": 47, "revision": 9, "value": 471}
correction = {"event_at": 82, "revision": 3, "value": 472}
assert choose_online_record(current, late) == current
assert choose_online_record(current, correction) == correction
''',
        'cost': 'The per-entity comparison is O(1) time and space. A repair over n source records costs at least O(n) scan time plus online writes; staged reconciliation may need O(u) state for u entities. The example assumes revision order is meaningful within an event timestamp, which the producer contract must enforce.',
        'mistakes': ['Trusting a successful job status without checking source and online watermarks.', 'Letting a late old event overwrite a newer online value.', 'Refreshing every entity when only one partition is stuck.', 'Confusing historical correction with permission to change a past production decision.'],
        'related': [M + 'online-feature-freshness-budget-and-ttl', M + 'receipt-feature-freshness-project', M + 'batch-replay-versioning-and-consumer-reconciliation', M + 'feature-schema-evolution-and-consumers', M + 'model-alert-symptoms-ownership-and-noise'],
    },
    {
        'path': M + 'receipt-feature-freshness-project',
        'title': 'Project: keep receipt scoring safe during feature publication lag',
        'module': F, 'project': True,
        'summary': 'Test a delayed regional feature feed, preserve online event order and restore the scoring path through a staged repair.',
        'sections': [
            ('Set the receipt policy', 'A receipt score uses merchant activity that must be no older than 47 minutes at decision time. The feature record carries event and availability timestamps, publisher revision and region. A missing or stale feature routes to manual review under a declared reason code. [[mlops/online-feature-freshness-budget-and-ttl|Freshness policy]] is checked per request even when the feature store reports that a record exists.'),
            ('Build fault fixtures', 'Include current values, an entity whose value is 82 minutes old, a late event older than the online value, an equal-time correction with a higher revision, a future timestamp and a region whose materialization watermark stops. Freeze expected serve, fallback and publish decisions. Make the stopped region small enough that aggregate global metrics could hide it, forcing slice-aware investigation.'),
            ('Stage recovery', 'Detect the stalled source or publisher using separate watermarks, replay the missing partition into a staging view and reconcile entity counts and event-time maxima. An older arriving event must remain historical rather than replacing current online state. Only then switch the affected region to the repaired view. [[mlops/late-feature-materialization-and-read-repair|Materialization repair]] keeps the scope bounded; [[mlops/feature-training-serving-parity|parity checks]] compare repaired values with historical reconstruction.'),
            ('Report customer outcomes', 'Measure stale-feature fallback rate, detection delay, repair duration, incorrectly overwritten entities and new receipt scores after recovery. Confirm no previously issued decision is silently rewritten. Keep sample receipt payloads restricted and alert by low-cardinality region and feature view. The drill is complete only when the scoring service resumes with fresh values and the fallback count returns to its expected range.'),
        ],
        'code': '''from datetime import timedelta

def freshness_release(records, decision_at, maximum_age_minutes=47):
    failures = []
    for entity_id, row in records.items():
        if row["event_at"] > decision_at:
            failures.append((entity_id, "future"))
        elif decision_at - row["event_at"] > timedelta(
                minutes=maximum_age_minutes):
            failures.append((entity_id, "stale"))
    return {"state": "hold" if failures else "ready",
            "failures": failures}

from datetime import datetime, timezone
now = datetime(2026, 10, 6, tzinfo=timezone.utc)
records = {"merchant-47": {"event_at": now - timedelta(minutes=23)},
           "merchant-82": {"event_at": now - timedelta(minutes=82)}}
assert freshness_release(records, now)["state"] == "hold"
assert freshness_release({"merchant-47": records["merchant-47"]},
                         now)["state"] == "ready"
''',
        'cost': 'Checking n entity records is O(n) time and O(f) space for f failures. A real release samples or batches checks across a large store and then enforces request-time freshness for every live decision. Staged repair doubles storage for the affected view until comparison and rollback windows close.',
        'mistakes': ['Assuming a global healthy watermark proves every region is current.', 'Letting a late event overwrite a newer online value.', 'Repairing the store while allowing stale features to score normally.', 'Rewriting previously issued decisions after a feature correction.'],
        'related': [M + 'online-feature-freshness-budget-and-ttl', M + 'late-feature-materialization-and-read-repair', M + 'feature-training-serving-parity', M + 'receipt-feature-admission-project', M + 'model-alert-symptoms-ownership-and-noise'],
    },
]

crosslinks = [
    (M + 'model-registry-promotion-gates', M + 'ml-test-pyramid-and-data-fixtures'),
    (M + 'trusted-model-promotion-project', M + 'environment-promotion-and-smoke-contracts'),
    (M + 'receipt-triage-release-project', M + 'receipt-ci-release-gate-project'),
    (M + 'feature-training-serving-parity', M + 'online-feature-freshness-budget-and-ttl'),
    (M + 'drift-delayed-label-monitoring', M + 'late-feature-materialization-and-read-repair'),
    (M + 'receipt-serving-slo-project', M + 'receipt-feature-freshness-project'),
]

if __name__ == '__main__':
    publish(lessons, (C, F), crosslinks,
            'aitrove-mlops-ci-freshness-import-20261006.json', 6124,
            subject='mlops', hub_path=M + 'mlops-tutorial')
