"""Add operational score-policy and monitoring-evidence modules to MLOps."""
from de_batch_publisher import publish

M = 'mlops/'
P = 'Score policy and human review controls'
T = 'Monitoring evidence and telemetry limits'

lessons = [
    {
        'path': M + 'score-threshold-policy-and-change-control',
        'title': 'Score thresholds are release policy, not model metadata',
        'module': P, 'project': False,
        'summary': 'A threshold can change customer outcomes without changing model bytes, so it needs separate evidence, ownership and rollback.',
        'sections': [
            ('Keep score and action separate', 'A receipt model may emit a risk score while a policy routes the receipt to review, clears it or asks for more information. The model artifact and the threshold policy have different owners and release clocks. A new threshold can double review volume even when the model digest is untouched. Record both identities on each decision. [[mlops/inference-request-response-contracts|The public response contract]] describes the route, while [[mlops/model-card-scope-and-limitation-register|the operating card]] states where that route is permitted.'),
            ('Select the operating point honestly', 'Tune a threshold on a development or policy-selection cohort with mature outcomes, then evaluate the frozen choice on a separate holdout. Define the cost of false review, missed urgent case and reviewer capacity before looking for a favorable cut. A score near 0.8 need not mean an 80 percent event probability unless calibration was checked. Revisit calibration by relevant population and time window before treating scores as probabilities. [[mlops/prediction-outcome-join-and-maturity|Mature outcome joins]] matter because reviewed receipts often receive labels earlier than cleared ones.'),
            ('Version the whole decision rule', 'Store policy revision, model digest, eligibility, threshold, tie behavior, fallback route and effective time together. A comparison using different model digests or eligibility rules cannot isolate the threshold effect. Before promotion, replay the proposed rule over a frozen decision set and estimate review volume and missed-case rate for important slices. [[mlops/slice-quality-gates-and-uncertainty|Slice gates]] must still hold; a strong aggregate result does not excuse a weak cohort. A policy approval should name a rollback revision, not just a new number.'),
            ('Monitor the change as a production release', 'Start with a limited exposure, count actions by route and compare the observed rate with the pre-release estimate. Watch capacity, overrides and delayed outcomes; a threshold can look safe for hours while mature labels take weeks. If the manual queue saturates, revert the policy pointer without claiming the model was defective. [[mlops/receipt-score-policy-project|The applied project]] runs two policy revisions against the same digest and demonstrates why policy change evidence is distinct from [[mlops/model-registry-promotion-gates|model promotion]].'),
        ],
        'code': '''def route_receipt(score, policy):
    if not 0 <= score <= 1:
        raise ValueError("score outside accepted range")
    if not 0 <= policy["review_at"] <= 1:
        raise ValueError("invalid review threshold")
    return {"route": "review" if score >= policy["review_at"] else "clear",
            "policy_revision": policy["revision"]}

policy = {"revision": "receipt-policy-r47", "review_at": 0.72}
assert route_receipt(0.72, policy)["route"] == "review"
assert route_receipt(0.71, policy)["route"] == "clear"
assert route_receipt(0.72, {**policy, "review_at": 0.81})[
    "route"] == "clear"
''',
        'cost': 'Routing one score takes O(1) time and space. Replaying n stored decisions over k candidate thresholds costs O(nk) without a sorted-score index; sorting once can reduce repeated count queries. The code shows a boundary rule, not a threshold-selection procedure. Review capacity and delayed labels dominate the operational cost of a policy change.',
        'mistakes': ['Changing the threshold without a new policy revision.', 'Tuning on the same holdout used for the final release claim.', 'Interpreting an uncalibrated score as a probability.', 'Rolling back model bytes when only the policy changed.'],
        'related': [M + 'human-override-and-adjudication-ledger', M + 'receipt-score-policy-project', M + 'model-card-scope-and-limitation-register', M + 'slice-quality-gates-and-uncertainty', M + 'prediction-outcome-join-and-maturity'],
    },
    {
        'path': M + 'human-override-and-adjudication-ledger',
        'title': 'Human overrides: keep decisions, reasons and labels distinct',
        'module': P, 'project': False,
        'summary': 'A reviewer may override a model route, but that action is not automatically a ground-truth label or a model error.',
        'sections': [
            ('Record three separate events', 'Store the model score and proposed route, the reviewer action, and the eventual adjudicated outcome as separate events tied to one decision ID. The reviewer may have information the model never saw, or may make a mistake. Treating every override as a positive label contaminates training and evaluation. Keep reviewer identity under restricted access, but preserve role, reason code, timestamp and policy revision for audit. [[mlops/inference-logging-privacy|Decision logging]] supplies a privacy-aware join; [[mlops/label-corrections-and-evaluation-ledger|the label ledger]] records later corrections.'),
            ('Design reasons that support investigation', 'A short controlled set of reason codes should distinguish missing feature, document quality, contextual evidence, policy exception and reviewer disagreement. Free text may help an investigation but can capture sensitive customer information; apply access and retention rules. Do not force a reviewer to choose “model wrong” when the reason was an expired feature. Review the codes periodically for ambiguity. [[mlops/feature-contract-and-admission-gates|Admission failures]] should be visible before the model score so the reviewer is not blamed for an input problem.'),
            ('Measure override rates with denominators', 'Report overrides per eligible decision and per reviewed decision, broken down by model digest, policy revision, reason and meaningful cohort. A rising override count could reflect a lower review threshold, a staffing shift or real quality loss. Compare the same eligibility window and expose missing reviewer records. An override rate alone is not a calibration score; use mature outcomes to decide whether model or policy changes improve decisions. [[mlops/score-threshold-policy-and-change-control|Threshold changes]] can alter which cases reach humans.'),
            ('Close the feedback loop deliberately', 'Create a queue for adjudicating disputed decisions, with an owner, evidence standard and correction history. Only adjudicated outcomes may enter the evaluation set under its documented label rule. Feed recurring reason codes into a feature or policy investigation, not directly into automatic retraining. [[mlops/receipt-score-policy-project|The project]] injects a reviewer override caused by a stale feature and tests whether the system keeps that reason separate from model accuracy. The record should allow an operator to reconstruct what each actor knew at decision time.'),
        ],
        'code': '''def append_review_event(history, event):
    if event["decision_id"] not in history:
        history[event["decision_id"]] = []
    if event["kind"] not in {"model", "reviewer", "adjudication"}:
        raise ValueError("unknown event kind")
    history[event["decision_id"]].append(event)
    return history[event["decision_id"]]

record = {}
append_review_event(record, {"decision_id": "receipt-82", "kind": "model",
                             "route": "clear"})
append_review_event(record, {"decision_id": "receipt-82", "kind": "reviewer",
                             "route": "review", "reason": "stale-feature"})
assert len(record["receipt-82"]) == 2
assert all(event["kind"] != "adjudication" for event in record["receipt-82"])
''',
        'cost': 'Appending an event is O(1) expected time with O(e) retained space for e events. Production storage needs durable writes, access controls and deduplication by event ID. The small example separates event types but does not prove that a reviewer action was justified; adjudication and mature outcome evidence remain independent costs.',
        'mistakes': ['Using reviewer override as ground truth without adjudication.', 'Dropping the original model route after a human changes it.', 'Comparing override counts without stable denominators.', 'Using unrestricted free text as the only reason field.'],
        'related': [M + 'score-threshold-policy-and-change-control', M + 'receipt-score-policy-project', M + 'label-corrections-and-evaluation-ledger', M + 'inference-logging-privacy', M + 'feature-contract-and-admission-gates'],
    },
    {
        'path': M + 'receipt-score-policy-project',
        'title': 'Project: release a receipt threshold with review evidence',
        'module': P, 'project': True,
        'summary': 'Change a receipt review threshold under a fixed model digest, measure capacity and preserve human overrides without relabeling them.',
        'sections': [
            ('Freeze the comparison', 'Use one approved receipt model digest and two policy revisions. The current rule reviews at score 0.81; the candidate reviews at 0.72. Specify tie behavior, eligible population, fallback route and reviewer capacity before replaying outcomes. Split policy selection from final evaluation by time and keep mature-label coverage visible. [[mlops/score-threshold-policy-and-change-control|Threshold governance]] needs both action impact and quality evidence; [[mlops/model-card-scope-and-limitation-register|the model card]] prevents expansion into unsupported uses.'),
            ('Replay the decision set', 'Evaluate the two rules on the same frozen receipts and count review volume, missed urgent cases and slice-level changes. Include a new-merchant slice whose mature labels are sparse. Mark it insufficient rather than declaring the new threshold safe there. Simulate an afternoon burst to test whether the reviewer queue can absorb extra cases. Record the policy revision with each replayed route; otherwise a later model change can make the comparison impossible to explain.'),
            ('Exercise the reviewer path', 'For one cleared receipt, a reviewer sees a stale feature and changes the route. Store the proposed route, override event and reason separately; do not add a positive label. Later adjudication may confirm or reject the concern, and its corrected outcome belongs in [[mlops/label-corrections-and-evaluation-ledger|the label ledger]]. [[mlops/human-override-and-adjudication-ledger|The override contract]] lets an operator separate missing input evidence from a model mistake. Force a duplicate reviewer submission and verify that the event ID prevents a second action.'),
            ('Make a reversible decision', 'A staged release can stop when manual-review load crosses its approved limit, even if early quality numbers look promising. Deliver the fixed digest, old and candidate policies, cohort counts, mature-label coverage, capacity test, override examples, stop conditions and rollback pointer. Record whether broad release is approved, restricted or held. [[mlops/receipt-model-experiment-project|Live experiment exposure]] can follow the offline gate, but it must not bypass it. The final record states what remains unknown and who owns the next review.'),
        ],
        'code': '''def policy_replay(scores, current_at, candidate_at, daily_review_limit):
    current = sum(score >= current_at for score in scores)
    candidate = sum(score >= candidate_at for score in scores)
    return {"current_review": current, "candidate_review": candidate,
            "state": "hold" if candidate > daily_review_limit else "pilot"}

receipt_scores = [0.12, 0.47, 0.73, 0.82, 0.94]
result = policy_replay(receipt_scores, 0.81, 0.72, 2)
assert result == {"current_review": 2, "candidate_review": 3,
                  "state": "hold"}
assert policy_replay(receipt_scores, 0.81, 0.72, 3)["state"] == "pilot"
''',
        'cost': 'A replay over n scores is O(n) time and O(1) extra space for two thresholds. Full evaluation also joins labels, applies slice gates and simulates queue capacity; those steps consume substantially more time and evidence. The five scores are a deterministic illustration, not an estimate of a real queue or event rate.',
        'mistakes': ['Treating a lower threshold as a model release with no policy record.', 'Counting a reviewer override as an outcome label.', 'Approving the candidate before checking review capacity.', 'Discarding insufficient slice evidence because the aggregate improves.'],
        'related': [M + 'score-threshold-policy-and-change-control', M + 'human-override-and-adjudication-ledger', M + 'receipt-model-card-review-project', M + 'receipt-model-experiment-project', M + 'label-corrections-and-evaluation-ledger'],
    },
    {
        'path': M + 'monitoring-cardinality-and-metric-identities',
        'title': 'Model monitoring dimensions without metric-cardinality failure',
        'module': T, 'project': False,
        'summary': 'Keep operational metrics bounded while retaining detailed, restricted events for per-decision investigations.',
        'sections': [
            ('Choose bounded dimensions', 'A metric may be split by model family, approved digest, route, region and status. Each label combination creates another time series, so adding receipt ID or merchant ID can multiply storage until monitoring fails during the incident it should reveal. Use controlled vocabularies and cap version retention. Keep request identifiers in restricted logs or traces instead. [[mlops/inference-logging-privacy|Decision logs]] support exact joins; [[mlops/model-alert-symptoms-ownership-and-noise|alerts]] need only dimensions that lead to a different owner or action.'),
            ('Match metric type to question', 'Count requests, failures and fallback as counters; observe latency distributions with buckets suited to the service deadline; export active in-flight work as a gauge. Track numerator and denominator separately so a rate cannot hide changing traffic volume. A deployment might leave an old digest label active for a short rollback window, but it should not create a fresh metric name for every run ID. [[mlops/inference-latency-budget-and-tail-observation|Tail latency]] requires a distribution, not an average of worker times.'),
            ('Budget the series before adding labels', 'Estimate the product of label values for each metric family across replicas and retained versions. A few bounded dimensions can still create thousands of series when combined. Put a ceiling in review and compare planned series growth with monitoring capacity. If a question needs arbitrary merchant-level cuts, compute it from access-controlled event data rather than live time-series labels. A single “other” bucket can contain unexpected values while preserving counts; investigate the bucket rather than silently dropping it.'),
            ('Test observability under change', 'Roll out a new digest and confirm old series age out on schedule. Force a fallback and verify both total request and fallback counters move. Scrape during a burst and check that the telemetry pipeline does not add material serving latency. [[mlops/receipt-monitoring-evidence-project|The project]] injects a receipt-ID label proposal and rejects it before production, then tests a bounded alternative that still identifies model-specific failure. Monitoring cost belongs in capacity planning, not just the dashboard backlog.'),
        ],
        'code': '''def estimate_series(label_values, replicas):
    if replicas < 0 or any(count < 0 for count in label_values.values()):
        raise ValueError("negative series dimension")
    total = replicas
    for count in label_values.values():
        total *= count
    return total

bounded = {"model": 3, "region": 2, "route": 3, "status": 4}
assert estimate_series(bounded, 5) == 360
assert estimate_series({**bounded, "receipt_id": 47000}, 5) == 16920000
''',
        'cost': 'The estimate is O(d) time and O(1) extra space for d dimensions. Real series count depends on which combinations actually occur, but the product is a useful upper bound. Each extra series consumes memory, storage, network and query work. The 47,000 receipt IDs are fictional; the calculation shows why an unbounded identifier is unsuitable as a metric label.',
        'mistakes': ['Putting decision IDs or customer IDs in metric labels.', 'Exporting only a rate without the numerator and denominator.', 'Averaging worker latency while queue time is omitted.', 'Keeping all historical digest label sets active forever.'],
        'related': [M + 'trace-sampling-and-coverage-ledger', M + 'receipt-monitoring-evidence-project', M + 'inference-logging-privacy', M + 'model-alert-symptoms-ownership-and-noise', M + 'inference-latency-budget-and-tail-observation'],
    },
    {
        'path': M + 'trace-sampling-and-coverage-ledger',
        'title': 'Trace sampling and coverage: know what production evidence misses',
        'module': T, 'project': False,
        'summary': 'Sample expensive traces without sampling away the event counts and identities needed for incident and quality analysis.',
        'sections': [
            ('Separate counters from sampled detail', 'Request and failure counters should describe all traffic, while detailed traces can be sampled to control cost. A low trace rate may still help diagnose typical latency but can miss rare timeouts or feature failures. Keep a compact durable decision record where later outcome joins require one, subject to the privacy and retention policy. [[mlops/inference-logging-privacy|Restricted inference logging]] carries that identity; [[mlops/monitoring-cardinality-and-metric-identities|bounded metrics]] report the population. Do not derive an exact failure count by counting sampled traces.'),
            ('Make sampling rules explicit', 'Head sampling decides before knowing whether a request will fail; tail sampling can retain completed error traces but requires buffering and enough time to assemble spans. Record sampling policy revision and expected probability. Ensure a trace carries model digest, policy revision and region without raw receipt contents. If errors are kept at a higher rate than successes, the sampled set is biased; comparing their raw counts does not estimate production error rate. Use complete counters for rates and sampled traces for causal investigation.'),
            ('Track missing events as a first-class metric', 'Compare ingress counts, accepted inference counts, decision-log writes and trace samples by time bucket. The gaps should be explained: rejected requests, logging failures, sampling or delayed delivery. A telemetry outage can coincide with a model outage, so silence is not evidence of health. [[mlops/prediction-outcome-join-and-maturity|Outcome coverage]] needs its own numerator and denominator because labels can be delayed or selectively observed. A sampled trace is not a replacement for the stable decision ID in the outcome ledger.'),
            ('Exercise the pipeline during failure', 'Drop trace export for one interval and verify serving continues while a telemetry-health alert fires. Force a model timeout and ensure a complete failure counter increments even when the trace is not sampled. Inspect tail-sampling buffer pressure and late span loss. [[mlops/receipt-monitoring-evidence-project|The project]] compares full request counts with sampled traces and shows a missing-log incident that a trace dashboard alone would hide. State the blind spots in the on-call runbook.'),
        ],
        'code': '''def coverage_audit(ingress, accepted, decisions, rejected):
    counts = (ingress, accepted, decisions, rejected)
    if any(value < 0 for value in counts):
        raise ValueError("negative count")
    unexplained = ingress - decisions - rejected
    if accepted < decisions or unexplained < 0:
        return {"state": "invalid", "gap": unexplained}
    return {"state": "investigate" if unexplained else "reconciled",
            "gap": unexplained}

assert coverage_audit(470, 450, 450, 20)["state"] == "reconciled"
assert coverage_audit(470, 450, 447, 20) == {"state": "investigate",
                                               "gap": 3}
''',
        'cost': 'The count comparison is O(1) time and space after aggregation. Tail sampling costs buffer memory proportional to concurrent traces and retention time; complete decision logging costs durable writes proportional to accepted requests. Counts from different windows or delayed pipelines cannot be compared directly, so align watermarks before declaring a gap.',
        'mistakes': ['Using sampled trace counts as exact production failure rates.', 'Keeping errors at a higher rate without reporting sampling bias.', 'Treating no traces during export failure as no requests.', 'Joining outcomes only to trace IDs that happen to be sampled.'],
        'related': [M + 'monitoring-cardinality-and-metric-identities', M + 'receipt-monitoring-evidence-project', M + 'inference-logging-privacy', M + 'prediction-outcome-join-and-maturity', M + 'incident-triage-and-evidence-timeline'],
    },
    {
        'path': M + 'receipt-monitoring-evidence-project',
        'title': 'Project: measure receipt inference without losing the denominator',
        'module': T, 'project': True,
        'summary': 'Build bounded metrics, sampled traces and a coverage ledger that exposes missing decision records during an incident.',
        'sections': [
            ('Design the telemetry contract', 'For the receipt endpoint, keep full counters for ingress, accepted requests, rejected requests, decisions, fallback and errors. Observe end-to-end latency by bounded route and digest. Permit model, region, route and status labels; reject receipt ID, merchant key and free-form error text as metric labels. Put exact decision identity in restricted durable logs. [[mlops/monitoring-cardinality-and-metric-identities|The series budget]] calculates the largest expected metric family before any instrument is deployed.'),
            ('Set trace policy and expected coverage', 'Sample a fixed share of ordinary successful requests and retain error traces when practical. Annotate each trace with the sampling policy revision and approved model identity. Keep full failure counters regardless of trace sampling. Write a compact decision event for accepted requests to support later outcome joins. [[mlops/trace-sampling-and-coverage-ledger|Sampling rules]] must explain why 47 traces from 470 requests are not 47 total decisions or an unbiased quality sample.'),
            ('Inject a telemetry failure', 'Send a deterministic load with valid, invalid and fallback receipts. Then drop three decision-log writes while allowing inference to continue. The ingress, rejection and decision counts should show a gap of three after their windows align. Raise a telemetry-health incident and retain the affected decision IDs from the gateway when available. Do not fill the gap by fabricating model outputs. [[mlops/incident-triage-and-evidence-timeline|The incident timeline]] should separate serving health from evidence health.'),
            ('Deliver an operating record', 'Report configured labels, upper-bound series count, full request counts, trace sampling rate, decision-log coverage, delayed delivery window and alert owner. Run one burst with the candidate telemetry enabled and compare serving tail latency. A monitoring change that harms inference latency is not harmless. Link future quality analysis to [[mlops/prediction-outcome-join-and-maturity|mature outcome joins]] and flag the missing records so no analyst silently treats them as negative outcomes.'),
        ],
        'code': '''def evidence_health(ingress, rejected, decisions, maximum_gap=0):
    if min(ingress, rejected, decisions) < 0 or rejected + decisions > ingress:
        raise ValueError("invalid evidence counts")
    gap = ingress - rejected - decisions
    return {"gap": gap, "state": "alert" if gap > maximum_gap else "healthy"}

assert evidence_health(470, 20, 450) == {"gap": 0, "state": "healthy"}
assert evidence_health(470, 20, 447) == {"gap": 3, "state": "alert"}
''',
        'cost': 'The health calculation is O(1) time and space. Full counters are cheap, but durable decision events and trace buffers scale with traffic. A zero-gap rule may alert during normal delivery delay; compare aligned event-time windows and set a measured grace interval before paging. The deterministic counts demonstrate the contract, not a recommended production threshold.',
        'mistakes': ['Adding receipt ID to a metric because it helps one dashboard query.', 'Sampling decision logs required for outcome joins.', 'Declaring a gap before delayed log delivery reaches its watermark.', 'Assuming serving is healthy because telemetry is silent.'],
        'related': [M + 'monitoring-cardinality-and-metric-identities', M + 'trace-sampling-and-coverage-ledger', M + 'inference-logging-privacy', M + 'incident-triage-and-evidence-timeline', M + 'receipt-serving-slo-project'],
    },
]

crosslinks = [
    (M + 'model-registry-promotion-gates', M + 'score-threshold-policy-and-change-control'),
    (M + 'label-corrections-and-evaluation-ledger', M + 'human-override-and-adjudication-ledger'),
    (M + 'receipt-model-experiment-project', M + 'receipt-score-policy-project'),
    (M + 'model-alert-symptoms-ownership-and-noise', M + 'monitoring-cardinality-and-metric-identities'),
    (M + 'inference-logging-privacy', M + 'trace-sampling-and-coverage-ledger'),
    (M + 'receipt-model-incident-drill-project', M + 'receipt-monitoring-evidence-project'),
]

if __name__ == '__main__':
    publish(lessons, (P, T), crosslinks,
            'aitrove-mlops-policy-telemetry-import-20261006.json', 6148,
            subject='mlops', hub_path=M + 'mlops-tutorial')
