"""Add prediction-set coverage operations and evaluation-set governance."""
from de_batch_publisher import publish

M = 'mlops/'
COVERAGE = 'Prediction-set coverage and abstention operations'
BENCHMARK = 'Evaluation-set stewardship and contamination control'
lessons = [
    {
        'path': M + 'prediction-set-calibration-contract-and-versioning',
        'title': 'Prediction-set releases: version calibration scores and assumptions',
        'module': COVERAGE, 'project': False,
        'summary': 'A prediction set is a release artifact whose coverage claim depends on its calibration frame and scoring rule.',
        'sections': [
            ('Define what the set means', 'A warehouse scanner classifies a damaged parcel as crushed, torn, wet or clear. Instead of forcing one class, a prediction-set layer returns every class whose nonconformity score falls within a fitted cutoff. The target is a stated marginal coverage level over data exchangeable with the held-out calibration examples. It is not a guarantee for every camera, damage type or future shifted distribution. Record the base model, class order, nonconformity formula, cutoff, calibration IDs and target error rate together. [[mlops/slice-quality-gates-and-uncertainty|Slice quality gates]] still examine the groups that a marginal number can hide.'),
            ('Keep calibration separate from fitting', 'Train the base model on its training split. Fit the cutoff on a disjoint calibration split and reserve a later test split for one release check. The cutoff is an empirical quantile of calibration nonconformity scores; use a conservative finite-sample rank rather than interpolating a lower value. Parcel images from one shipment must stay in one split. Otherwise near-duplicate frames can make sets appear smaller and more reliable than they are. [[mlops/snapshot-split-and-environment-replay|Split replay]] preserves those shipment boundaries.'),
            ('Pin the whole tuple', 'Changing preprocessing, class order, calibration source or base model invalidates an old cutoff. Store a digest for each component and reject mixed revisions at serving time. A newer base model with the same labels can change the score distribution. An unchanged cutoff is not automatically reusable. Put the prediction set beside the single-class score and route in the response contract, with an explicit empty-set or full-set fallback. [[mlops/inference-request-response-contracts|Response contracts]] keep clients from treating a set as a sorted probability list.'),
            ('Evaluate usefulness alongside coverage', 'A set containing all four classes can cover the true class often yet be useless for routing. Measure empirical coverage, singleton rate, average set size, per-camera coverage and the fraction sent to manual review. Include uncertainty for sparse groups. If the widest sets overload reviewers, adjust workflow capacity or model quality; do not silently lower the cutoff after looking at the protected test set. [[mlops/prediction-set-coverage-and-review-capacity|Coverage monitoring]] pairs the statistical and operational views.'),
        ],
        'code': '''from math import ceil

def finite_sample_cutoff(calibration_scores, error_rate):
    if not calibration_scores or not 0 < error_rate < 1:
        raise ValueError("nonempty scores and an error rate in (0, 1) required")
    ordered = sorted(calibration_scores)
    rank = ceil((len(ordered) + 1) * (1 - error_rate))
    return float("inf") if rank > len(ordered) else ordered[rank - 1]

scores = [0.04, 0.12, 0.18, 0.27, 0.39, 0.48, 0.62, 0.71,
          0.76, 0.83, 0.89, 0.93, 0.94, 0.96, 0.97, 0.98,
          0.99, 0.995, 0.998, 0.999]
assert finite_sample_cutoff(scores, 0.1) == 0.998
assert finite_sample_cutoff(scores[:4], 0.1) == float("inf")
''',
        'cost': 'Sorting n calibration scores costs O(n log n) time and O(n) space. With a small calibration frame, the conservative rank can exceed n and yield an uninformative full set. At serving time, scoring c classes costs O(c) beyond the base model. Review volume grows when sets contain multiple plausible classes.',
        'mistakes': ['Claiming per-camera coverage from a marginal target alone.', 'Fitting the cutoff on training predictions.', 'Reusing a cutoff after changing the model or class order.', 'Calling a full-class set a useful answer because it covers the label.'],
        'related': [M + 'prediction-set-coverage-and-review-capacity', M + 'parcel-prediction-set-release-project', M + 'snapshot-split-and-environment-replay', M + 'slice-quality-gates-and-uncertainty', M + 'inference-request-response-contracts'],
    },
    {
        'path': M + 'prediction-set-coverage-and-review-capacity',
        'title': 'Prediction-set monitoring: coverage lag, set width and review load',
        'module': COVERAGE, 'project': False,
        'summary': 'Monitor prediction sets with mature outcomes and an explicit review-capacity budget; unlabeled width is only an early signal.',
        'sections': [
            ('Separate early and late measurements', 'The scanner can report set size immediately, but true coverage is known only after an inspected parcel receives a resolved damage label. Record predicted set, model and cutoff revisions, cohort, event time and label maturity. Report set width and manual-review rate daily; report coverage only on mature joined outcomes. Do not code missing labels as misses or successes. [[mlops/prediction-outcome-join-and-maturity|Mature outcome joins]] establish a comparable denominator.'),
            ('Watch selective labels', 'Parcels with wide sets are more likely to be sent to review, so the labeled cohort overrepresents uncertain cases. A coverage estimate from that queue does not describe all auto-cleared parcels. Reserve a small independent audit sample from cleared traffic and report it separately. Show counts and intervals by camera and package class. A nominal target does not save a sparse slice. [[mlops/selective-label-observation-and-audit-sampling|Audit sampling]] provides a frame outside the review policy.'),
            ('Bound operational cost', 'A prediction set is only useful if its route can be handled. Define how singletons, multiple classes and full sets map to automated clearance or human inspection. Track queue age and reviewer capacity; a new cutoff that increases coverage by sending every parcel to manual review fails the workflow. Evaluate both the incumbent and candidate on the same frozen traffic frame. [[mlops/score-threshold-policy-and-change-control|Threshold policy]] changes also alter reviewer load and need the same capacity discipline.'),
            ('Respond to shift without claiming guarantees', 'A new scanner lens or packaging material can break the similarity between calibration and production populations. Rising set width is an early signal, not proof that coverage fell. When mature audit labels show low coverage or a new cohort lacks evidence, pause automated use for that cohort, investigate data quality, then recalibrate on an approved new frame and requalify the release. [[mlops/drift-delayed-label-monitoring|Drift monitoring]] and [[mlops/parcel-prediction-set-release-project|the project]] connect diagnosis to reversible action.'),
        ],
        'code': '''def coverage_report(decisions, minimum_mature):
    mature = [row for row in decisions if row["outcome_mature"]]
    if len(mature) < minimum_mature:
        return {"state": "insufficient", "mature": len(mature)}
    covered = sum(row["true_class"] in row["prediction_set"]
                  for row in mature)
    mean_width = sum(len(row["prediction_set"]) for row in decisions) / len(decisions)
    return {"state": "measured", "coverage": covered / len(mature),
            "mean_width": mean_width, "mature": len(mature)}

rows = [{"prediction_set": {"torn", "wet"}, "true_class": "torn",
         "outcome_mature": True},
        {"prediction_set": {"clear"}, "true_class": "wet",
         "outcome_mature": True},
        {"prediction_set": {"crushed", "wet"}, "true_class": None,
         "outcome_mature": False}]
report = coverage_report(rows, 2)
assert report["coverage"] == 0.5 and report["mean_width"] == 5 / 3
''',
        'cost': 'Aggregation scans n decisions in O(n) time and O(n) temporary space in this sample; streaming counters use O(1) state per cohort. Independent audit labels and human review consume capacity. Recalibration adds a new fit and evaluation cycle, while merely raising the cutoff can hide a weak model behind wider sets.',
        'mistakes': ['Treating width as measured coverage before labels arrive.', 'Reporting review-queue coverage as coverage for all traffic.', 'Ignoring a multi-class-set surge that overwhelms reviewers.', 'Assuming an old coverage target survives a population shift.'],
        'related': [M + 'prediction-set-calibration-contract-and-versioning', M + 'parcel-prediction-set-release-project', M + 'prediction-outcome-join-and-maturity', M + 'selective-label-observation-and-audit-sampling', M + 'drift-delayed-label-monitoring'],
    },
    {
        'path': M + 'parcel-prediction-set-release-project',
        'title': 'Project: release parcel prediction sets with a bounded review queue',
        'module': COVERAGE, 'project': True,
        'summary': 'Calibrate a versioned prediction-set cutoff, measure minority coverage and stop a release that overwhelms reviewers.',
        'sections': [
            ('Freeze the parcel frame', 'The warehouse scanner has four damage classes. Split images by shipment, fit the base model on training shipments and reserve separate calibration and final evaluation shipments. Pin camera firmware, image preprocessing, class order, model digest and scoring formula. Calculate a finite-sample cutoff for the target error rate using only calibration scores. [[mlops/prediction-set-calibration-contract-and-versioning|The contract]] rejects any serving pair with a different model or cutoff revision.'),
            ('Find the easy-to-miss failure', 'The candidate passes overall coverage on the final set, but wet cartons from a recently installed camera are rarely included. Full-class sets increase after its lens update. Do not describe marginal coverage as a guarantee for the new camera. Hold automated clearance for that cohort and collect an independent audit sample; reviewed-only labels would bias the estimate. [[mlops/slice-quality-gates-and-uncertainty|Slice gates]] require a separate decision for the minority failure.'),
            ('Test review load and response behavior', 'Map singleton clear sets to automatic clearance only under the approved policy. Route ambiguous and full sets to manual inspection. A wider candidate cutoff raises daily reviews from 392 to 514 while staffing can handle 470. Hold promotion even if coverage improves. Verify the API returns class names and a set revision, rather than a class-index list that an old client might misread. [[mlops/prediction-set-coverage-and-review-capacity|Coverage and load monitoring]] should observe both effects.'),
            ('Deliver a reversible release packet', 'Record calibration IDs, finite-sample rank, test coverage, per-camera counts, set-width distribution, reviewer forecast and rollback pointer. Shadow the candidate first. If a later camera cohort shifts, route it to review and fit a new cutoff on a fresh approved calibration frame; do not quietly alter the live cutoff. Link decisions to [[mlops/promotion-attestation-and-reversible-pointer|promotion evidence]] and [[mlops/prediction-outcome-join-and-maturity|mature outcomes]].'),
        ],
        'code': '''def parcel_set_release(report, limits):
    if not report["split_disjoint"] or not report["tuple_matched"]:
        return "hold:contract"
    if report["minority_coverage"] < limits["minority_coverage"]:
        return "hold:minority-coverage"
    if report["daily_reviews"] > limits["daily_reviews"]:
        return "hold:review-capacity"
    return "canary"

limits = {"minority_coverage": 0.82, "daily_reviews": 470}
report = {"split_disjoint": True, "tuple_matched": True,
          "minority_coverage": 0.88, "daily_reviews": 514}
assert parcel_set_release(report, limits) == "hold:review-capacity"
assert parcel_set_release({**report, "daily_reviews": 392}, limits) \
       == "canary"
''',
        'cost': 'The aggregate release gate is O(1) time and space. Calibration sorting is O(n log n) for n examples, while per-request set construction is O(c) for c classes beyond base inference. The expensive part may be reviewer time: extra full sets convert inference uncertainty into a daily human queue.',
        'mistakes': ['Using shipment frames from one parcel across training and calibration.', 'Promoting from marginal coverage while a new camera slice fails.', 'Ignoring the review-volume increase caused by wider sets.', 'Sending bare class indices to clients with a different class order.'],
        'related': [M + 'prediction-set-calibration-contract-and-versioning', M + 'prediction-set-coverage-and-review-capacity', M + 'slice-quality-gates-and-uncertainty', M + 'promotion-attestation-and-reversible-pointer', M + 'prediction-outcome-join-and-maturity'],
    },
    {
        'path': M + 'evaluation-set-access-ledger-and-exposure-budget',
        'title': 'Evaluation-set governance: log access and protect the blind holdout',
        'module': BENCHMARK, 'project': False,
        'summary': 'A blind evaluation set loses independence when teams use its results to repeatedly tune the model or policy.',
        'sections': [
            ('Separate purposes and visibility', 'A payment-risk team needs exploratory validation to improve models and a protected holdout for a final release estimate. Give the sets different IDs, storage permissions and result visibility. Validation can be inspected repeatedly; the blind set should be queried under a fixed evaluation plan. Record who requested each run, the candidate digest, metric revision, cohort, timestamp and release decision. [[mlops/snapshot-split-and-environment-replay|Snapshot replay]] preserves the split; an access ledger preserves how the split was used.'),
            ('Count exposure, not just downloads', 'A person need not see raw rows to adapt to a holdout. Repeatedly receiving detailed scores and slice failures can guide another model iteration toward that same set. Set an exposure budget and require a new decision plan after repeated looks. A failed candidate may be diagnosed on validation data; do not turn blind results into another tuning dashboard. Keep a narrow emergency path with a reason and owner. [[mlops/evaluation-benchmark-retirement-and-refresh|Benchmark retirement]] addresses a set whose independence has already been spent.'),
            ('Keep entities and time boundaries honest', 'Two cards from one customer, or two sessions from one device, should not be split across training and protected evaluation when that would leak identity. For future deployment, reserve a later time frame where feasible, then document any limits to comparability. A final set assembled from only easy historical cases can be independent yet irrelevant. Test cohort coverage without exposing every label to model developers. [[mlops/slice-quality-gates-and-uncertainty|Slice gates]] are meaningful only when their evaluation frame matches the deployment population.'),
            ('Bind reports to reproducible artifacts', 'Store a manifest for data snapshot, label taxonomy, eligibility filters, metric implementation and candidate artifact. A rerun with changed labels or metric code is a new evaluation revision. Publish high-level pass or fail to the release team, and retain detailed diagnostics under a controlled review path. [[mlops/model-registry-promotion-gates|Registry promotion]] should consume the report ID, not an unversioned spreadsheet screenshot. [[mlops/payment-holdout-stewardship-project|The project]] finds two teams unknowingly reusing the same blind set.'),
        ],
        'code': '''def holdout_request(ledger, candidate_digest, exposure_limit):
    prior = sum(entry["candidate_digest"] == candidate_digest
                for entry in ledger)
    if prior >= exposure_limit:
        return "hold:exposure-budget"
    if any(entry["candidate_digest"] == candidate_digest
           and entry["result_scope"] == "detailed" for entry in ledger):
        return "hold:diagnostic-exposure"
    return "admit:sealed-result"

ledger = [{"candidate_digest": "risk-r47", "result_scope": "sealed"}]
assert holdout_request(ledger, "risk-r47", 2) == "admit:sealed-result"
assert holdout_request(ledger, "risk-r47", 1) == "hold:exposure-budget"
''',
        'cost': 'Scanning n ledger entries is O(n) time and O(1) extra space; an indexed candidate count can make admission O(1) expected time. The larger cost is maintaining a valid blind set and a controlled evaluation service. An exposure budget cannot undo prior leakage, but it makes repeated adaptation visible.',
        'mistakes': ['Treating detailed blind-set score reports as harmless because raw rows are hidden.', 'Running candidate after candidate against the same final set with no exposure ledger.', 'Splitting related customer records across training and holdout.', 'Promoting from a report whose label or metric revision is unknown.'],
        'related': [M + 'evaluation-benchmark-retirement-and-refresh', M + 'payment-holdout-stewardship-project', M + 'snapshot-split-and-environment-replay', M + 'model-registry-promotion-gates', M + 'slice-quality-gates-and-uncertainty'],
    },
    {
        'path': M + 'evaluation-benchmark-retirement-and-refresh',
        'title': 'Benchmark retirement: refresh a holdout after repeated exposure',
        'module': BENCHMARK, 'project': False,
        'summary': 'When an evaluation set has influenced training decisions, retire it as a blind release gate and create a new protected frame.',
        'sections': [
            ('Recognize a spent benchmark', 'A payment-risk holdout was intended for one final estimate. Over several releases, teams inspected its failure slices and modified features to improve those exact cases. The set is still useful for regression tests, but it no longer measures a fully independent future result. Mark its status and exposure history explicitly. Do not delete it or pretend the prior scores were fraudulent; state what the score now represents. [[mlops/evaluation-set-access-ledger-and-exposure-budget|The access ledger]] helps determine when independence was lost.'),
            ('Specify the successor before collecting it', 'Define target population, acquisition period, customer grouping, outcome maturity and minimum slice counts. Freeze the eligibility query and label policy before reviewing candidate scores. If fraud outcomes are delayed, wait until the frame matures; early labels can distort the risk estimate. Preserve old and new benchmark IDs, snapshot digests and taxonomy revisions. [[mlops/prediction-outcome-join-and-maturity|Outcome maturity]] prevents recent unlabeled payments from being counted as safe.'),
            ('Avoid a silent metric discontinuity', 'Evaluate an unchanged reference model on both old and new sets to understand distribution and label differences. Do not claim that a new model improved because its score on the successor set exceeds an older model’s score on the retired set. Report both models on the same new frame where possible, then start a new baseline. Keep the retired set as a named diagnostic suite with a visible “not blind” status. [[mlops/label-corrections-and-evaluation-ledger|Label lineage]] records judgments that changed between versions.'),
            ('Protect the successor', 'Limit raw access, use sealed result summaries, cap detailed looks and record every evaluation request. A refresh process that reveals all hard cases immediately repeats the same failure. If the successor lacks important slices, collect a supplemental frame rather than selectively swapping rows after seeing model outcomes. [[mlops/payment-holdout-stewardship-project|The project]] tests a candidate that looks good on a retired set but fails the fresh frame; [[mlops/model-registry-promotion-gates|promotion gates]] must reference the successor report.'),
        ],
        'code': '''def benchmark_comparison(old_report, new_report):
    if old_report["dataset_id"] != new_report["dataset_id"]:
        return "separate-baselines"
    if old_report["metric_revision"] != new_report["metric_revision"]:
        return "recompute:metric-revision"
    if old_report["label_revision"] != new_report["label_revision"]:
        return "recompute:label-revision"
    return "paired-comparison"

retired = {"dataset_id": "payments-legacy-r8", "metric_revision": "miss-r3",
           "label_revision": "risk-r4"}
successor = {**retired, "dataset_id": "payments-future-r9"}
assert benchmark_comparison(retired, successor) == "separate-baselines"
assert benchmark_comparison(retired, retired) == "paired-comparison"
''',
        'cost': 'Comparison validation is O(1) time and space. Creating a successor costs outcome labeling, collection time and controlled storage. Running the unchanged reference model on both frames doubles one evaluation pass, but it prevents a misleading before-and-after claim across different denominators.',
        'mistakes': ['Keeping an exposed benchmark as the only blind release gate.', 'Comparing scores from two different datasets as if they were paired.', 'Filling a new holdout with immature negative outcomes.', 'Refreshing rows after seeing which examples the current model misses.'],
        'related': [M + 'evaluation-set-access-ledger-and-exposure-budget', M + 'payment-holdout-stewardship-project', M + 'prediction-outcome-join-and-maturity', M + 'label-corrections-and-evaluation-ledger', M + 'model-registry-promotion-gates'],
    },
    {
        'path': M + 'payment-holdout-stewardship-project',
        'title': 'Project: retire a spent payment-risk holdout and qualify its successor',
        'module': BENCHMARK, 'project': True,
        'summary': 'Audit evaluation access, retire an exposed blind set and compare candidates on a newly protected future frame.',
        'sections': [
            ('Audit the old set', 'The payment-risk team has used one holdout for several releases. Its raw rows were not copied, yet detailed failure slices were sent to model developers after each run. Build a ledger of candidate digests, result scopes, metric revisions and decision dates. The history shows that developers changed features after seeing its hard cases. Reclassify the set as a regression suite rather than a blind release estimate. [[mlops/evaluation-set-access-ledger-and-exposure-budget|Exposure governance]] makes this status visible.'),
            ('Build a future frame', 'Before looking at candidate outcomes, freeze a later acquisition period, customer grouping, eligibility query, outcome window, label policy and metric implementation. Wait for labels to mature. Reject a candidate frame with the same customer in training and holdout. Set a minimum count for important merchant and device cohorts. The successor needs its own ID and snapshot digest; the retired set stays intact for historical diagnosis.'),
            ('Rebaseline fairly', 'Evaluate the unchanged incumbent and candidate on the successor with the same metric revision. The candidate looks stronger on the retired set but loses on a new merchant cohort in the successor. Hold promotion and inspect the failure on validation data, not by disclosing the protected labels for another tuning round. Run the incumbent on both frames to explain how the population changed without presenting cross-set scores as a paired model improvement. [[mlops/evaluation-benchmark-retirement-and-refresh|Retirement rules]] keep that comparison honest.'),
            ('Close the handoff', 'Deliver the access ledger, old-set status, successor manifest, maturity counts, cohort coverage, paired results and a controlled procedure for future evaluation requests. The registry release packet should point to the successor report ID and document the minority failure. A later candidate needs a fresh registered request, not an emailed copy of detailed holdout rows. Link the outcome to [[mlops/model-registry-promotion-gates|promotion gates]] and [[mlops/snapshot-split-and-environment-replay|split replay]].'),
        ],
        'code': '''def holdout_release(frame, result):
    if frame["status"] != "blind":
        return "hold:not-blind"
    if not frame["mature"] or not frame["entity_disjoint"]:
        return "hold:frame-integrity"
    if result["metric_revision"] != frame["metric_revision"]:
        return "hold:metric-revision"
    if not result["minority_gate_passed"]:
        return "hold:minority-quality"
    return "eligible:registry-review"

frame = {"status": "blind", "mature": True, "entity_disjoint": True,
         "metric_revision": "miss-r3"}
result = {"metric_revision": "miss-r3", "minority_gate_passed": False}
assert holdout_release(frame, result) == "hold:minority-quality"
assert holdout_release({**frame, "status": "regression"}, result) \
       == "hold:not-blind"
''',
        'cost': 'The release gate is O(1) time and space after reports exist. The expensive work is collecting future mature outcomes and protecting the successor from repeated exposure. Keeping the retired suite adds storage and evaluation time, but preserves historical regression evidence without mislabeling it as blind.',
        'mistakes': ['Calling a repeatedly inspected holdout independent.', 'Comparing an old-model score on the retired frame with a candidate score on the successor.', 'Allowing the same customer into training and the future holdout.', 'Ignoring a new merchant-cohort failure because the old benchmark improved.'],
        'related': [M + 'evaluation-set-access-ledger-and-exposure-budget', M + 'evaluation-benchmark-retirement-and-refresh', M + 'model-registry-promotion-gates', M + 'snapshot-split-and-environment-replay', M + 'slice-quality-gates-and-uncertainty'],
    },
]

crosslinks = [
    (M + 'slice-quality-gates-and-uncertainty', M + 'prediction-set-calibration-contract-and-versioning'),
    (M + 'prediction-outcome-join-and-maturity', M + 'prediction-set-coverage-and-review-capacity'),
    (M + 'promotion-attestation-and-reversible-pointer', M + 'parcel-prediction-set-release-project'),
    (M + 'snapshot-split-and-environment-replay', M + 'evaluation-set-access-ledger-and-exposure-budget'),
    (M + 'model-registry-promotion-gates', M + 'evaluation-benchmark-retirement-and-refresh'),
    (M + 'label-corrections-and-evaluation-ledger', M + 'payment-holdout-stewardship-project'),
]

if __name__ == '__main__':
    publish(lessons, [COVERAGE, BENCHMARK], crosslinks,
            'aitrove-mlops-coverage-benchmark-import-20261006.json', 6220,
            subject='mlops', hub_path=M + 'mlops-tutorial')
