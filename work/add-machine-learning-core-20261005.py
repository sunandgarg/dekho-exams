"""Add full Machine Learning lessons on baselines, errors and model behavior."""
from ml_fixture_writer_20261005 import publish_batch

lessons = []

def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='machine-learning/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))

add('regression-baselines-and-holdout-metrics',
    'Regression baselines and honest holdout metrics',
    'A regression baseline predicts a simple training-derived value so a new model must demonstrate useful error reduction on unseen outcomes.', [
    ('Choose a baseline that matches the loss', 'A logistics team predicts hours until a shipment clears a sorting center. If the decision is evaluated by absolute error, the training median is a strong constant benchmark; for squared error, the training mean is the corresponding constant benchmark. A previous-period forecast or a route-specific historical median can be harder to beat and may better reflect the operation. Define the baseline before fitting a larger model. [[machine-learning/getting-started|The first-model lesson]] ties prediction to a specific action.'),
    ('Keep the clock and partition honest', 'The baseline value must be estimated from training shipments only. The holdout consists of later shipments whose outcomes were unknown at prediction time. Recomputing the median after seeing the holdout leaks the answer into the benchmark and makes comparison meaningless. If the same shipment appears in multiple scans, keep all scans in one partition. [[machine-learning/group-and-time-validation|Group and time validation]] explains that boundary.'),
    ('Compare paired errors on the same rows', 'Predict every holdout shipment with both baseline and candidate model, then calculate each metric from the same labeled cases. Report the number of shipments, MAE, and a tail metric if late misses create operational harm. A model that lowers average error but produces rare severe underestimates may be worse for staffing. The code compares an explicit candidate prediction vector with a training-median baseline and refuses misaligned inputs.'),
    ('Interpret what improvement means', 'A small MAE gain is not automatically a business gain. Include the dispatch decision, capacity limit and cost of late action. A constant baseline can look weak if routes have different service levels; compare against a simple route baseline before deploying a complex predictor. Conversely, a model that cannot beat a training-only median on a future holdout has not justified its added maintenance cost. [[machine-learning/regression-error-slices-and-tail-cost|Error slices]] locate where the gap appears.'),
    ('Preserve the untouched final test', 'Use development folds to select features and settings. Evaluate the final choice once on the future test set; repeated tuning against that set turns it into development data. Store the row IDs, cutoff dates, target version and both prediction vectors. The teaching code calculates scores but does not create the partition; that design must be audited separately.')],
    '''from statistics import median

def mean_absolute_error(actual_hours, predicted_hours):
    if not actual_hours or len(actual_hours) != len(predicted_hours):
        raise ValueError("aligned nonempty outcomes required")
    return sum(abs(actual - predicted)
               for actual, predicted in zip(actual_hours, predicted_hours)) / len(actual_hours)

training_clearance_hours = [3, 4, 5, 8, 20]
future_actual_hours = [4, 6, 9, 7]
candidate_hours = [5, 6, 7, 8]
baseline_hour = median(training_clearance_hours)
baseline_hours = [baseline_hour] * len(future_actual_hours)
baseline_mae = mean_absolute_error(future_actual_hours, baseline_hours)
candidate_mae = mean_absolute_error(future_actual_hours, candidate_hours)
assert baseline_hour == 5
assert abs(baseline_mae - 2.0) < 1e-12
assert abs(candidate_mae - 1.0) < 1e-12''',
    'Computing the training median by sorting N values is O(N log N) time; evaluating M holdout rows is O(M) time and O(M) storage for prediction vectors. Training and serving a candidate model add separate costs that the comparison must justify.',
    ['Do not compute the baseline from the final test outcomes.', 'Do not compare models on different holdout rows or target definitions.', 'Do not equate a small average-error gain with operational value.'],
    ['machine-learning/regression-error-slices-and-tail-cost','machine-learning/ridge-regularization-with-training-only-scaling','machine-learning/group-and-time-validation','machine-learning/shipment-delay-model-review-project'])

add('regression-error-slices-and-tail-cost',
    'Regression error slices and costly tails',
    'Regression evaluation should show average and tail errors by operational slice because a single aggregate metric can hide expensive underestimation.', [
    ('Start with the sign of the mistake', 'A shipment predicted to clear in four hours but clearing in nine has a five-hour underestimate; planning staff may miss a handoff. Predicting nine when it clears in four may reserve capacity unnecessarily. Absolute error treats both as five, while the operation may not. Keep signed error alongside MAE and RMSE. RMSE weights larger misses more heavily, but neither metric encodes the specific cost curve. [[machine-learning/regression-baselines-and-holdout-metrics|The baseline lesson]] defines the comparison.'),
    ('Slice by conditions known at prediction', 'Compare errors for overnight versus daytime arrivals, high-volume centers and routes with short service windows. Use labels available at prediction time for slicing; a post-outcome category such as actual delay severity can still be useful diagnostically but cannot define a deployable routing rule. Include support counts. A slice with two shipments should not receive the same confidence as one with two thousand.'),
    ('Find tails without erasing the distribution', 'Report the maximum and a high quantile of underestimation, plus the fraction exceeding a policy-relevant threshold. The code calculates MAE, RMSE and underestimates of at least three hours per center. It does not estimate uncertainty or optimize a loss function. Keep the raw residual sequence for debugging; a single tail count cannot reveal whether a clock change, missing scan or rare route caused the error.'),
    ('Separate model error from target error', 'If actual clearance time is recorded from the wrong scan, both baseline and candidate may appear wrong. Audit target construction before changing features. If the model errors spike only after a new scanning system launches, evaluate label lineage and distribution shift. [[machine-learning/prediction-time-feature-availability|Feature availability]] and [[data-science/proxy-measurement-and-label-error|outcome measurement]] are independent checks.'),
    ('Use the slice report to choose a next experiment', 'A large overnight tail might justify an overnight-specific model, an additional early feature or a capacity buffer. Do not immediately branch the model on every weak slice; this can overfit and increase maintenance. Reserve a new holdout period to verify the proposed change. [[machine-learning/shipment-delay-model-review-project|The shipment project]] turns the error report into an explicit decision.')],
    '''from math import sqrt

def center_error_report(shipments, costly_underestimate_hours):
    groups = {}
    for center, actual_hours, predicted_hours in shipments:
        if actual_hours < 0 or predicted_hours < 0:
            raise ValueError("negative clearance time")
        groups.setdefault(center, []).append(actual_hours - predicted_hours)
    report = {}
    for center, signed_errors in groups.items():
        count = len(signed_errors)
        report[center] = {
            "shipments": count,
            "mae": sum(abs(error) for error in signed_errors) / count,
            "rmse": sqrt(sum(error ** 2 for error in signed_errors) / count),
            "costly_underestimates": sum(
                error >= costly_underestimate_hours for error in signed_errors),
        }
    return report

future_shipments = [("Harbor", 9, 4), ("Harbor", 6, 7),
                    ("Inland", 4, 5), ("Inland", 8, 7)]
report = center_error_report(future_shipments, 3)
assert report["Harbor"]["costly_underestimates"] == 1
assert report["Inland"]["costly_underestimates"] == 0
assert report["Harbor"]["mae"] == 3''',
    'For N scored shipments, group accumulation and metric calculation cost O(N) expected time and O(N) space for residuals. Quantiles require sorting within groups, up to O(N log N). Manual inspection of tail cases is often the expensive step.',
    ['Do not rely on aggregate MAE when the operational cost is asymmetric.', 'Do not report a slice rate without its shipment count.', 'Do not treat corrupted target timestamps as a feature-engineering problem.'],
    ['machine-learning/regression-baselines-and-holdout-metrics','machine-learning/ridge-regularization-with-training-only-scaling','machine-learning/prediction-time-feature-availability','machine-learning/shipment-delay-model-review-project'])

add('ridge-regularization-with-training-only-scaling',
    'Ridge regularization with training-only scaling',
    'Ridge regression penalizes squared coefficient size to reduce instability from noisy or correlated predictors, with preprocessing parameters learned only from training data.', [
    ('Specify the objective and its units', 'A clearance-time model may use route backlog, distance and staffing count. Ridge minimizes squared prediction error plus a nonnegative penalty on fitted slopes. The intercept is normally left unpenalized. A larger penalty shrinks coefficients toward zero; it does not select a sparse feature set by itself. Because the penalty acts on coefficient size, predictors measured in different units need scaling based on the training partition. [[machine-learning/leakage-safe-preprocessing-pipeline|The preprocessing lesson]] covers the split boundary.'),
    ('Use a one-feature calculation to expose the mechanism', 'The code centers training backlog and clearance hours, then divides their cross-product by backlog sum of squares plus the declared penalty. With penalty zero, it is ordinary least squares for this single predictor. With a positive penalty, the slope magnitude falls. This formula is a teaching case, not a general multi-feature solver; correlated features require a proper matrix or iterative implementation and a consistent scaling contract.'),
    ('Tune only inside development data', 'Choose the penalty with grouped or time-aware development folds that match deployment. For each fold, fit scaling and the ridge model on that fold’s training rows, then score its validation rows. Selecting the best penalty on the final test set makes that test optimistic. Report the selected penalty and the range of validation scores, not only the final coefficient. [[machine-learning/group-and-time-validation|The split lesson]] provides the operating pattern.'),
    ('Read coefficients with care', 'A shrunk coefficient is not a causal effect. Correlated backlog and staffing measures may divide predictive signal in ways that change when the training window shifts. Large shrinkage can improve future error while increasing training error; it may also underfit if the relationship is stable and data are plentiful. Compare against a constant or route baseline and inspect residuals by center. [[machine-learning/regression-error-slices-and-tail-cost|Error slices]] show whether the penalty fixes a real failure.'),
    ('Keep the complete fitted state', 'Store training means, scales, feature order, coefficient vector, intercept, penalty, target definition and model version together. A service that applies a new scaler to yesterday’s coefficients silently changes predictions. The example stores only the one-feature mean and intercept; production code must also validate the incoming feature schema and handle missing values under the frozen training policy.')],
    '''def one_feature_ridge(backlog_train, clearance_train, penalty):
    if len(backlog_train) != len(clearance_train) or len(backlog_train) < 2:
        raise ValueError("aligned training rows required")
    if penalty < 0:
        raise ValueError("negative penalty")
    backlog_mean = sum(backlog_train) / len(backlog_train)
    clearance_mean = sum(clearance_train) / len(clearance_train)
    centered_backlog = [value - backlog_mean for value in backlog_train]
    centered_clearance = [value - clearance_mean for value in clearance_train]
    denominator = sum(value ** 2 for value in centered_backlog) + penalty
    if denominator == 0:
        raise ValueError("constant feature with no penalty")
    slope = sum(backlog * clearance for backlog, clearance
                in zip(centered_backlog, centered_clearance)) / denominator
    intercept = clearance_mean - slope * backlog_mean
    return intercept, slope, backlog_mean

backlog = [12, 18, 24, 30]
clearance = [4, 5, 7, 9]
plain_intercept, plain_slope, _ = one_feature_ridge(backlog, clearance, 0)
ridge_intercept, ridge_slope, fitted_mean = one_feature_ridge(backlog, clearance, 50)
assert abs(ridge_slope) < abs(plain_slope)
assert fitted_mean == 21
assert ridge_intercept + ridge_slope * fitted_mean == sum(clearance) / 4''',
    'The one-feature fit is O(N) time and O(N) space for centered vectors. A multi-feature ridge solver scales with N rows and P features according to its linear algebra method, and each validation-fold refit multiplies training cost.',
    ['Do not fit a scaler on validation or test rows.', 'Do not interpret ridge coefficients as treatment effects.', 'Do not tune the penalty on the final holdout.'],
    ['machine-learning/leakage-safe-preprocessing-pipeline','machine-learning/regression-baselines-and-holdout-metrics','machine-learning/regression-error-slices-and-tail-cost','machine-learning/shipment-delay-model-review-project'])

add('rare-event-precision-recall-and-prevalence',
    'Rare-event precision, recall and changing prevalence',
    'For a rare event, precision and recall expose false-alert workload and missed cases more directly than accuracy, while precision changes with event prevalence.', [
    ('Put the confusion counts on the table', 'A receipt-review model flags suspicious claims. True positives are flagged claims later confirmed suspicious; false positives are flagged routine claims. Precision is true positives divided by all flags. Recall is true positives divided by all confirmed suspicious claims. A model that predicts routine for every claim can post high accuracy when suspicious claims are rare yet have zero recall. [[machine-learning/decision-threshold-and-cost|The decision-threshold lesson]] connects scores to analyst workload.'),
    ('Evaluate the intended threshold and capacity', 'Ranked probabilities become an action only at a cutoff or top-K capacity. Changing the cutoff moves precision and recall; the best operating point depends on review time and missed-case cost. The code calculates confusion counts for a frozen threshold on labeled holdout claims. It rejects an empty set and reports undefined precision as None when no alerts are sent, rather than silently calling it zero or one.'),
    ('Watch prevalence move', 'If the suspicious-claim rate falls while sensitivity and specificity stay similar, a larger share of flags can be false positives. Do not copy a precision number from a high-risk validation set to an ordinary production stream. If validation deliberately oversampled suspicious claims, raw precision from that set is not production precision. Reweight by the target population or evaluate a representative future holdout. [[data-science/stratified-sampling-and-design-weights|Sampling weights]] explain the design issue.'),
    ('Do not let one metric settle model choice', 'Recall near one can be obtained by flagging almost every claim, overwhelming reviewers. Precision near one may come from a tiny alert set that misses most suspicious cases. Report event prevalence, both denominators, alert count, and cost or capacity at the chosen threshold. A precision-recall curve can summarize threshold tradeoffs, but threshold selection still belongs to development data, not final test outcomes.'),
    ('Separate ranking from probability meaning', 'A model can rank suspicious claims well while its probabilities are poorly calibrated. If a 0.20 score is used to estimate expected review yield, calibration matters. If the action is simply the top 47 claims each morning, ranking and capacity may dominate. [[machine-learning/probability-calibration|Calibration]] tests score meaning; [[machine-learning/shipment-delay-model-review-project|the review project]] keeps classification and regression targets separate.')],
    '''def threshold_counts(labeled_scores, threshold):
    if not labeled_scores or not 0 <= threshold <= 1:
        raise ValueError("invalid scores or threshold")
    true_positive = false_positive = false_negative = true_negative = 0
    for suspicious, risk_score in labeled_scores:
        if suspicious not in (0, 1) or not 0 <= risk_score <= 1:
            raise ValueError("invalid label or risk score")
        flagged = risk_score >= threshold
        if flagged and suspicious:
            true_positive += 1
        elif flagged:
            false_positive += 1
        elif suspicious:
            false_negative += 1
        else:
            true_negative += 1
    alerts = true_positive + false_positive
    cases = true_positive + false_negative
    return {"precision": true_positive / alerts if alerts else None,
            "recall": true_positive / cases if cases else None,
            "alerts": alerts, "true_positive": true_positive,
            "false_positive": false_positive,
            "false_negative": false_negative,
            "true_negative": true_negative}

claims = [(1, .87), (0, .75), (1, .48), (0, .31), (0, .08)]
review = threshold_counts(claims, .45)
assert review["alerts"] == 3
assert abs(review["precision"] - 2 / 3) < 1e-12
assert review["recall"] == 1''',
    'For N scored claims, one threshold report is O(N) time and O(1) auxiliary space. Evaluating T thresholds directly is O(N × T); sorting once supports a full precision-recall sweep in O(N log N) time.',
    ['Do not use accuracy alone for a rare-event workflow.', 'Do not transfer precision from a case-enriched validation set without accounting for prevalence.', 'Do not call precision zero when the model sends no alerts.'],
    ['machine-learning/decision-threshold-and-cost','machine-learning/probability-calibration','machine-learning/decision-tree-splits-and-leaf-support','machine-learning/shipment-delay-model-review-project'])

add('decision-tree-splits-and-leaf-support',
    'Decision-tree splits and minimum leaf support',
    'A decision tree partitions feature space with successive rules; each split should reduce impurity on training data while retaining enough observations in every leaf to limit fragile rules.', [
    ('Read one split before fitting a forest', 'A receipt-review team might split claims on the count of prior manual corrections. At a candidate threshold, the left and right child groups have different suspicious-claim fractions. Weighted Gini impurity scores how mixed those groups remain. A lower score than the unsplit parent indicates a training-data improvement. The code searches midpoint thresholds for one feature and returns the best eligible split. It is not a complete recursive tree implementation.'),
    ('Guard tiny leaves', 'A threshold isolating one suspicious claim may make a pure child and look attractive on training data, yet fail on new claims. A declared minimum leaf size rejects such splits. Minimum size is a regularization choice, not a universal constant. Tune it in development folds, and inspect whether each leaf has enough positive cases for the intended action. [[machine-learning/group-and-time-validation|Grouped validation]] prevents the same customer’s claims from appearing on both sides.'),
    ('Understand what the tree can and cannot infer', 'A tree learns associations useful for prediction; a rule on prior corrections does not prove corrections cause fraud. Correlated features can substitute for one another, and a tree can change structure after small data shifts. Limit depth, leaf count or pruning based on a valid validation scheme. [[machine-learning/rare-event-precision-recall-and-prevalence|Rare-event metrics]] matter more than impurity alone at deployment.'),
    ('Handle feature availability and missing values', 'A prior-correction count computed after review is future information for a pre-review decision. Freeze it at claim submission time. Missing counts need an explicit route in the feature pipeline; replacing them with an all-data median before splitting leaks validation information. The simple code requires complete numeric feature values and binary labels, so it rejects unsupported inputs instead of inventing a branch.'),
    ('Compare to a baseline under the same clock', 'A tree may reduce training impurity yet lose to a constant or simple ruleset on a future holdout. Report the selected threshold, child support, holdout precision and recall, analyst capacity, and how the rule behaves by claim type. One split is interpretable; many nested splits can be difficult to maintain when claim categories or logging change. [[machine-learning/shipment-delay-model-review-project|The applied project]] records the model-choice evidence.')],
    '''def gini(binary_labels):
    if not binary_labels:
        raise ValueError("empty leaf")
    event_rate = sum(binary_labels) / len(binary_labels)
    return 2 * event_rate * (1 - event_rate)

def best_correction_split(feature_and_label, minimum_leaf):
    if minimum_leaf < 2 or len(feature_and_label) < 2 * minimum_leaf:
        raise ValueError("insufficient support")
    if any(label not in (0, 1) for _, label in feature_and_label):
        raise ValueError("binary labels required")
    ordered = sorted(feature_and_label)
    candidates = []
    for position in range(minimum_leaf, len(ordered) - minimum_leaf + 1):
        if ordered[position - 1][0] == ordered[position][0]:
            continue
        left = [label for _, label in ordered[:position]]
        right = [label for _, label in ordered[position:]]
        weighted = (len(left) * gini(left) + len(right) * gini(right)) / len(ordered)
        midpoint = (ordered[position - 1][0] + ordered[position][0]) / 2
        candidates.append((weighted, midpoint, len(left), len(right)))
    if not candidates:
        raise ValueError("no supported split")
    return min(candidates)

claims = [(0, 0), (1, 0), (2, 0), (3, 1), (4, 1), (5, 1)]
impurity, correction_cutoff, left_count, right_count = best_correction_split(claims, 2)
assert correction_cutoff == 2.5
assert impurity == 0
assert (left_count, right_count) == (3, 3)''',
    'Sorting N rows costs O(N log N). The direct list-slicing candidate loop is O(N²) time and O(N) transient space; cumulative class counts reduce the scan after sorting to O(N). Full trees multiply work across nodes and features.',
    ['Do not accept a pure training leaf with one case as stable evidence.', 'Do not interpret a split rule as a causal effect.', 'Do not evaluate a tree on claims from customers already present in training.'],
    ['machine-learning/rare-event-precision-recall-and-prevalence','machine-learning/group-and-time-validation','machine-learning/prediction-time-feature-availability','machine-learning/shipment-delay-model-review-project'])

add('shipment-delay-model-review-project',
    'Project: review shipment-delay and claim-risk models',
    'Build two small model reviews that use appropriate baselines and metrics for a continuous clearance-time target and a rare suspicious-claim target.', [
    ('Keep the two prediction tasks separate', 'For the logistics task, predict clearance hours at the first sorting scan. For the claims task, rank suspicious claims at submission, before human review. They have different target types, clocks, costs and validation sets. Do not reuse a single scorecard called accuracy for both. Record eligible rows, future holdout dates, entity grouping and feature availability. [[machine-learning/prediction-time-feature-availability|The feature-clock lesson]] is the first gate.'),
    ('Build simple benchmarks', 'Fit a training-median clearance baseline and a simple historical claim-review policy before trying larger models. Compare the clearance model with MAE and costly underestimates on the same future shipments. Compare the claim model with precision, recall, prevalence and alert volume at a capacity-compatible threshold. [[machine-learning/regression-baselines-and-holdout-metrics|Regression baselines]] and [[machine-learning/rare-event-precision-recall-and-prevalence|rare-event metrics]] define those comparisons.'),
    ('Inspect failure modes', 'For clearance, slice signed errors by sorting center and arrival shift. For claims, report false alerts and misses by claim type and customer history. Check that tree leaves are not built from one positive case and that a regularized regression stores its training scaler and penalty. A lower aggregate error cannot erase a severe tail or an unsupported subgroup. [[machine-learning/regression-error-slices-and-tail-cost|Error slices]] and [[machine-learning/decision-tree-splits-and-leaf-support|leaf support]] show what to audit.'),
    ('Keep development choices off the final holdout', 'Choose ridge penalty, tree leaf size and alert threshold with development folds that respect entities and time. Fit all learned preprocessing inside each fold. Once choices are fixed, score the future holdout once and store both model and baseline predictions. A second round of changes requires a new later holdout or a clearly labeled development analysis. [[machine-learning/leakage-safe-preprocessing-pipeline|Leakage-safe preprocessing]] explains why.'),
    ('Issue two bounded release decisions', 'The code gate checks for the evidence artifacts and positive support counts. It does not certify predictive value or calibrate scores. The release note should say whether each model beats its operational benchmark, where it fails, whether staffing capacity can absorb alerts, and what will be monitored after launch. If labels or features are unavailable at the stated clock, stop rather than inventing a valid test.')],
    '''def model_review_gate(packet):
    required = {"prediction_clocks", "future_holdouts", "baseline_scores",
                "candidate_scores", "slice_reports", "claim_prevalence",
                "claim_alert_count", "training_transform_manifest"}
    missing = sorted(required - set(packet))
    if missing:
        raise ValueError("missing review evidence: " + ", ".join(missing))
    if any(count <= 0 for count in packet["future_holdouts"].values()):
        raise ValueError("empty holdout")
    if not 0 <= packet["claim_prevalence"] <= 1:
        raise ValueError("invalid prevalence")
    if packet["claim_alert_count"] < 0:
        raise ValueError("invalid alert count")
    return {"packet_complete": True,
            "tasks": sorted(packet["future_holdouts"]),
            "alerts": packet["claim_alert_count"]}

packet = {"prediction_clocks": ["first sorting scan", "claim submission"],
          "future_holdouts": {"clearance_hours": 47, "claim_risk": 83},
          "baseline_scores": {"clearance_mae": 3.2, "claim_precision": .28},
          "candidate_scores": {"clearance_mae": 2.7, "claim_precision": .39},
          "slice_reports": ["center", "claim type"],
          "claim_prevalence": .12, "claim_alert_count": 19,
          "training_transform_manifest": "v4"}
review = model_review_gate(packet)
assert review == {"packet_complete": True,
                  "tasks": ["claim_risk", "clearance_hours"], "alerts": 19}''',
    'The gate is O(A + T log T) time for A artifact fields and T task names, with O(T) output space. Model fitting, data lineage and manual inspection of high-cost errors dominate actual project effort.',
    ['Do not evaluate a regression target with classification accuracy.', 'Do not tune a threshold on the final holdout.', 'Do not treat a complete packet as proof the model improves the workflow.'],
    ['machine-learning/regression-baselines-and-holdout-metrics','machine-learning/regression-error-slices-and-tail-cost','machine-learning/ridge-regularization-with-training-only-scaling','machine-learning/rare-event-precision-recall-and-prevalence','machine-learning/decision-tree-splits-and-leaf-support'])

publish_batch(
    lessons,
    module_title='Core models and operating metrics',
    module_summary='Compare simple baselines, inspect regression tails, regularize carefully and evaluate rare events and tree leaves.',
    project_heading='Shipment and claim model review',
    crosslinks=[
        ('machine-learning/getting-started', lessons[0]['path']),
        ('machine-learning/core-concepts', lessons[1]['path']),
        ('machine-learning/leakage-safe-preprocessing-pipeline', lessons[2]['path']),
        ('machine-learning/decision-threshold-and-cost', lessons[3]['path']),
        ('machine-learning/group-and-time-validation', lessons[4]['path']),
        ('machine-learning/practice-project', lessons[5]['path']),
    ],
    sort_start=14100,
)
