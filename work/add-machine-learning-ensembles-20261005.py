"""Add original, connected Machine Learning ensemble and monitoring lessons."""
from ml_fixture_writer_20261005 import publish_batch

lessons = []


def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='machine-learning/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))


add('bootstrap-bagging-and-out-of-bag-evaluation',
    'Bootstrap bagging and out-of-bag evaluation',
    'Bagging trains separate predictors on replacement samples and combines their outputs; an out-of-bag prediction uses only predictors whose sample excluded that row.', [
    ('Make replacement explicit', 'A carrier forecasts clearance hours from the backlog seen at intake. Each bag draws as many training shipments as the training set contains, with replacement. A shipment may appear several times in one bag and not at all in another. Fit one tree or other base learner per bag, then average regression predictions. The benefit is lower sensitivity to a particular training sample when the learner is unstable. [[machine-learning/decision-tree-splits-and-leaf-support|Tree leaf support]] remains a separate constraint.'),
    ('Score a row only with trees that missed it', 'Out-of-bag evaluation gathers predictions for shipment i from the bags that did not contain i. A tree trained on that shipment cannot contribute to its out-of-bag score. The code uses short, fixed-threshold stumps so the sampling and score boundary are visible. Its threshold is declared, not optimized. With too few bags, some rows may have no eligible votes; that is a missing estimate, not a zero-error prediction.'),
    ('Keep the estimate in its lane', 'Out-of-bag error is useful while developing a bagged model, but it samples the same historical period. It does not simulate a new carrier, a warehouse policy change or a future outage. If multiple scans belong to one shipment, row-level bootstrap can put related scans on both sides of the evaluation. Sample at the independent shipment or site unit when that is the deployment unit. [[machine-learning/group-and-time-validation|Time and group validation]] checks a different question.'),
    ('Compare with a simpler model', 'Averaging many predictors adds memory and serving work. Report the gain over a training-only median and a single constrained tree on the same future rows. OOB predictions should be stored with vote counts so sparse coverage is visible. If the ensemble only fixes one tiny slice, inspect that slice and its label quality before adopting a more expensive service. [[machine-learning/regression-baselines-and-holdout-metrics|The baseline guide]] defines the paired comparison.'),
    ('Audit reproducibility', 'Record the seed, sampling unit, feature order, stump settings and training cutoff. Seeds make a run repeatable, but they do not remove sampling uncertainty. Refit with several declared seeds during development, then freeze one reviewed configuration. The later [[machine-learning/random-forest-feature-subsampling-and-leaf-support|forest lesson]] adds randomness in feature selection, which changes both diversity and how individual splits can be interpreted.')],
    '''from random import Random

shipments = [(8, 3), (11, 4), (15, 4), (19, 5),
             (23, 7), (27, 8), (31, 9), (36, 11)]

def fit_backlog_stump(sampled_rows, cutoff=21):
    overall = sum(hours for _, hours in sampled_rows) / len(sampled_rows)
    low = [hours for backlog, hours in sampled_rows if backlog < cutoff]
    high = [hours for backlog, hours in sampled_rows if backlog >= cutoff]
    return (sum(low) / len(low) if low else overall,
            sum(high) / len(high) if high else overall)

randomizer = Random(47)
eligible_votes = [[] for _ in shipments]
for _ in range(160):
    drawn = [randomizer.randrange(len(shipments)) for _ in shipments]
    low_hours, high_hours = fit_backlog_stump([shipments[index] for index in drawn])
    included = set(drawn)
    for index, (backlog, _) in enumerate(shipments):
        if index not in included:
            eligible_votes[index].append(low_hours if backlog < 21 else high_hours)

assert all(eligible_votes)
out_of_bag_mae = sum(
    abs(actual - sum(votes) / len(votes))
    for (_, actual), votes in zip(shipments, eligible_votes)
) / len(shipments)
assert out_of_bag_mae >= 0''',
    'For B bags of N rows, drawing and scoring these fixed stumps costs O(BN) time and O(BN) temporary vote storage; a real tree adds split-search cost and tree memory. OOB scoring reuses fitted bags but never replaces a future-period evaluation.',
    ['Do not let a tree vote on a row it trained on when computing OOB error.', 'Do not bootstrap dependent scans as if each were an independent shipment.', 'Do not call an OOB score a future deployment estimate.'],
    ['machine-learning/random-forest-feature-subsampling-and-leaf-support','machine-learning/decision-tree-splits-and-leaf-support','machine-learning/group-and-time-validation','machine-learning/ensemble-release-review-project'])


add('random-forest-feature-subsampling-and-leaf-support',
    'Random forest feature subsampling and leaf support',
    'A random forest combines bootstrap-trained trees while restricting split candidates to a sampled feature subset; leaf size controls how narrowly each tree can fit.', [
    ('Separate the two random choices', 'A shipment forest first samples training shipments for each tree. At each split it also considers only a sampled subset of input features. The second choice can stop every tree from choosing the same dominant backlog field and can reduce correlation between trees. It does not guarantee independent predictions. Feature sampling happens repeatedly at split nodes, not once for the entire forest. [[machine-learning/bootstrap-bagging-and-out-of-bag-evaluation|Bagging]] isolates the row-sampling part.'),
    ('Keep leaves large enough to mean something', 'A leaf containing one training shipment memorizes its outcome. Setting a minimum leaf count forces splits to retain support on both sides, trading some training fit for stability. In rare-event classification, raw row count may hide that a leaf contains no positive cases. Inspect class counts and calibration by slice. The example searches one split for a sampled feature set and rejects splits below a minimum leaf size; it is an inspectable component, not a full forest implementation.'),
    ('Score candidate splits on the right unit', 'The example uses weighted Gini impurity for a binary delayed-shipment label. It computes that impurity from training labels only. For a regression forest, the split criterion changes, commonly to a squared-error objective. Do not use a holdout label to pick thresholds. A holdout is for evaluating the fitted forest, and [[machine-learning/hyperparameter-search-and-untouched-test|model selection]] keeps its final test untouched.'),
    ('Avoid claiming causality from split frequency', 'A feature can be selected often because it has many possible thresholds, correlates with another field or is available only after a shipment was already delayed. Neither split count nor impurity reduction is an effect estimate. Check [[machine-learning/permutation-importance-on-held-out-data|held-out permutation importance]], feature availability, and whether the same conclusion survives alternative training windows. Correlated variables may substitute for one another.'),
    ('Bound the operational cost', 'More trees reduce Monte Carlo variation but increase training, storage and inference roughly with tree count. Larger minimum leaves and shallower trees can lower latency. Measure the actual request budget, not only validation accuracy. Save feature schema and model version with the forest; an extra or reordered field at serving time can invalidate every split. [[machine-learning/ensemble-release-review-project|The release review]] records the tradeoff.')],
    '''from random import Random

training_rows = [
    {"backlog": 9, "staff": 7, "delayed": 0},
    {"backlog": 12, "staff": 6, "delayed": 0},
    {"backlog": 16, "staff": 5, "delayed": 0},
    {"backlog": 22, "staff": 5, "delayed": 1},
    {"backlog": 26, "staff": 4, "delayed": 1},
    {"backlog": 33, "staff": 3, "delayed": 1},
]

def gini(rows):
    if not rows:
        raise ValueError("empty leaf")
    positive_rate = sum(row["delayed"] for row in rows) / len(rows)
    return 2 * positive_rate * (1 - positive_rate)

def best_supported_split(rows, candidate_features, minimum_leaf):
    candidates = []
    for feature in candidate_features:
        values = sorted({row[feature] for row in rows})
        for left_value, right_value in zip(values, values[1:]):
            threshold = (left_value + right_value) / 2
            left = [row for row in rows if row[feature] <= threshold]
            right = [row for row in rows if row[feature] > threshold]
            if min(len(left), len(right)) < minimum_leaf:
                continue
            score = (len(left) * gini(left) + len(right) * gini(right)) / len(rows)
            candidates.append((score, feature, threshold))
    return min(candidates) if candidates else None

candidate_features = Random(47).sample(["backlog", "staff"], k=1)
chosen_split = best_supported_split(training_rows, candidate_features, 2)
assert chosen_split is not None
assert chosen_split[0] < gini(training_rows)
assert chosen_split[1] in candidate_features''',
    'At one node with N rows, F candidate features and up to N thresholds each, this direct implementation can cost O(FN²) time because it repeatedly scans rows. A production tree sorts or bins values to reduce split-search work. Forest memory and serving time grow with the number and depth of trees.',
    ['Do not sample features once per forest and describe it as per-node sampling.', 'Do not leave one-row leaves unconstrained on small or noisy training sets.', 'Do not read feature split counts as causal effects.'],
    ['machine-learning/bootstrap-bagging-and-out-of-bag-evaluation','machine-learning/gradient-boosting-residuals-and-early-stopping','machine-learning/permutation-importance-on-held-out-data','machine-learning/ensemble-release-review-project'])


add('gradient-boosting-residuals-and-early-stopping',
    'Gradient boosting residuals and early stopping',
    'Squared-error gradient boosting adds small learners to correct the current training residuals, while a separate validation period decides when the sequence stops.', [
    ('Fit errors in sequence', 'For a clearance-time target, start with the training mean. Compute each training residual as actual minus current prediction, fit a shallow tree to those residuals, then add a fraction of the tree output to the prediction. Each stage depends on the preceding stages; this is the key difference from independently bagged trees. The code uses a declared backlog split and group means to expose the update, while a full implementation searches splits and supports other differentiable losses.'),
    ('Treat the learning rate and stage count as a pair', 'A small learning rate makes each correction modest, often requiring more stages. Too many stages can fit noise even when each individual tree is shallow. Tree depth and minimum leaf support also matter. Compare training and validation error at each stage on a fixed development partition. [[machine-learning/learning-curves-and-training-size-diagnosis|Training-size curves]] answer a different question: whether more rows improve a fixed model design.'),
    ('Stop without peeking at the final test', 'Choose the stage with the lowest development-validation loss, preferably with a tolerance or patience rule defined before looking. A future test remains sealed until the fitted settings are frozen. Repeatedly changing the rate, split policy or feature set after inspecting that final test converts it into development data. [[machine-learning/hyperparameter-search-and-untouched-test|The selection lesson]] states the boundary.'),
    ('Know what the validation curve cannot prove', 'A decreasing validation error on one convenient random split does not prove that the model handles a new warehouse. A new site or later period can have different label delay, staffing policy and feature coverage. Use groups and time cuts matching the deployment question. Report the selected stage, validation support and error slices. [[machine-learning/regression-error-slices-and-tail-cost|Tail errors]] may worsen while average squared error improves.'),
    ('Compare the actual service budget', 'Boosted stages execute sequentially at prediction time, unlike independently trained bagged trees. Distillation, fewer stages or shallower trees may be needed under a tight latency budget. An expensive model must beat the operational baseline on the same future rows by enough to justify training, storage, serving and review costs. [[machine-learning/ensemble-release-review-project|The release project]] makes that decision explicit.')],
    '''training_rows = [(8, 3), (12, 4), (17, 5), (24, 7), (29, 9), (35, 10)]
validation_rows = [(14, 4), (27, 8), (33, 9)]
cutoff = 21
learning_rate = 0.35
initial_hours = sum(hours for _, hours in training_rows) / len(training_rows)
training_predictions = [initial_hours] * len(training_rows)
validation_predictions = [initial_hours] * len(validation_rows)
stage_losses = []

for _ in range(12):
    residuals = [actual - predicted for (_, actual), predicted
                 in zip(training_rows, training_predictions)]
    left = [residual for (backlog, _), residual in zip(training_rows, residuals)
            if backlog < cutoff]
    right = [residual for (backlog, _), residual in zip(training_rows, residuals)
             if backlog >= cutoff]
    left_step = sum(left) / len(left)
    right_step = sum(right) / len(right)
    training_predictions = [
        predicted + learning_rate * (left_step if backlog < cutoff else right_step)
        for (backlog, _), predicted in zip(training_rows, training_predictions)
    ]
    validation_predictions = [
        predicted + learning_rate * (left_step if backlog < cutoff else right_step)
        for (backlog, _), predicted in zip(validation_rows, validation_predictions)
    ]
    loss = sum((actual - predicted) ** 2 for (_, actual), predicted
               in zip(validation_rows, validation_predictions)) / len(validation_rows)
    stage_losses.append(loss)

selected_stage = min(range(1, len(stage_losses) + 1),
                     key=lambda stage: stage_losses[stage - 1])
assert stage_losses[0] < sum((actual - initial_hours) ** 2
                             for _, actual in validation_rows) / len(validation_rows)
assert 1 <= selected_stage <= 12''',
    'With T stages, N training rows and a fixed two-leaf split, this illustration costs O(TN) time and O(N) working memory. Searching all features and thresholds raises fitting cost substantially. Serving evaluates stages in order and scales approximately with the number of stored trees.',
    ['Do not fit stage residuals from validation outcomes.', 'Do not use the final test to select the number of stages.', 'Do not assume lower squared error also fixes costly underestimation tails.'],
    ['machine-learning/random-forest-feature-subsampling-and-leaf-support','machine-learning/learning-curves-and-training-size-diagnosis','machine-learning/hyperparameter-search-and-untouched-test','machine-learning/ensemble-release-review-project'])


add('learning-curves-and-training-size-diagnosis',
    'Learning curves and training-size diagnosis',
    'A learning curve compares training and validation performance as the permitted training sample grows, exposing whether collecting more similar data is likely to help.', [
    ('Fix the question before drawing the curve', 'A carrier wants to know whether another month of labeled clearance events would help a backlog predictor. Refit the same model design on increasing chronological prefixes, then score each fit on a later development-validation period. Keep features, target construction and loss definition fixed. The code uses one-feature least squares so the fit can be inspected without a dependency; the concept applies to larger estimators. [[machine-learning/group-and-time-validation|Time-aware validation]] keeps the clock sensible.'),
    ('Read both error traces', 'If training and validation errors are both high and close, the model may be too simple or the available features weak. If training error is low while validation error remains much higher, the model may be too sensitive to the sample. More comparable data can sometimes narrow that gap, but only if the data-generation process is stable. A flat validation curve is evidence about this setup, not a universal statement that data collection is useless.'),
    ('Keep the validation cohort independent', 'Growing training windows can approach a fixed validation window, but must not include it. A later validation cohort avoids learning from the future; multiple rolling cutoffs give a more dependable picture than a single date. If each new prefix includes a new warehouse or revised measurement system, the curve mixes sample size with distribution change. Annotate those events before attributing any improvement to N alone.'),
    ('Avoid selecting on the final test', 'A curve is part of model development. If the team chooses a training horizon after reading these validation errors, use a separate final period for the release claim. Do not repeatedly redraw the curve with alternate feature sets against the same final holdout and call the last score untouched. [[machine-learning/hyperparameter-search-and-untouched-test|The selection protocol]] explains the distinction.'),
    ('Turn the shape into a decision', 'Compare additional label cost against the observed reduction in validation error and the operational cost of mistakes. If the gap is concentrated in one site, targeted labeling may be more useful than indiscriminate growth. If both curves are poor, investigate feature availability, target quality or model capacity before buying labels. [[machine-learning/ensemble-release-review-project|The project]] asks for a specific data or modeling action backed by the curve.')],
    '''from math import isclose

history = [(8, 3), (12, 4), (16, 4), (20, 6),
           (24, 7), (28, 8), (32, 10), (36, 11)]
later_validation = [(14, 4), (26, 8), (34, 10)]

def fit_backlog_line(rows):
    mean_backlog = sum(backlog for backlog, _ in rows) / len(rows)
    mean_hours = sum(hours for _, hours in rows) / len(rows)
    centered = [(backlog - mean_backlog, hours - mean_hours)
                for backlog, hours in rows]
    denominator = sum(backlog ** 2 for backlog, _ in centered)
    if denominator == 0:
        raise ValueError("no training backlog variation")
    slope = sum(backlog * hours for backlog, hours in centered) / denominator
    return mean_hours - slope * mean_backlog, slope

def mae(rows, intercept, slope):
    return sum(abs(hours - (intercept + slope * backlog))
               for backlog, hours in rows) / len(rows)

curve = []
for training_size in (4, 6, 8):
    training_prefix = history[:training_size]
    intercept, slope = fit_backlog_line(training_prefix)
    curve.append((training_size, mae(training_prefix, intercept, slope),
                  mae(later_validation, intercept, slope)))

assert [point[0] for point in curve] == [4, 6, 8]
assert all(point[1] >= 0 and point[2] >= 0 for point in curve)
assert isclose(curve[-1][1], mae(history, *fit_backlog_line(history)))''',
    'For K training sizes and a one-feature closed-form fit, the direct implementation costs O(KN) time and O(K) output space. Cross-validated curves multiply fits by fold count; model-specific fit cost can dominate. Use a small, declared grid of sample sizes before scheduling expensive ensembles.',
    ['Do not let a training prefix overlap its validation cohort.', 'Do not infer that more data will help when its population or labeling process differs.', 'Do not use a final test curve to choose model complexity or training horizon.'],
    ['machine-learning/gradient-boosting-residuals-and-early-stopping','machine-learning/paired-bootstrap-model-gain-intervals','machine-learning/group-and-time-validation','machine-learning/ensemble-release-review-project'])


add('paired-bootstrap-model-gain-intervals',
    'Paired bootstrap intervals for model gain',
    'A paired bootstrap resamples the evaluation units while keeping baseline and challenger predictions together, showing how unstable the observed error gain may be.', [
    ('Define the gain on aligned cases', 'A route model and a proposed ensemble predict clearance time for the same future shipments. For each shipment, calculate baseline absolute error minus challenger absolute error; a positive mean favors the challenger. The pairing matters because both models faced the same difficult cases. Resampling their errors independently destroys that relationship and invents variability. [[machine-learning/regression-baselines-and-holdout-metrics|The baseline guide]] establishes the common holdout.'),
    ('Resample independent units', 'Several shipments from one warehouse may share a staffing outage or scan clock. The code samples warehouse groups with replacement and carries every shipment in a selected group together. This protects within-site dependence better than drawing individual shipments, though six sites still give a fragile interval. If deployment must generalize to unseen regions, regions rather than warehouses may be the right unit. The resampling unit must match the claim.'),
    ('Treat percentiles as a diagnostic', 'The code reports the 5th and 95th percentiles of 1,600 bootstrap mean gains as a simple uncertainty band. It is not a guaranteed 90-percent frequentist confidence interval under arbitrary dependence or dataset selection. Small group counts, rare tail events and model tuning on the holdout can make it misleading. Record the number of independent groups and the fraction of draws favoring the challenger alongside the endpoints.'),
    ('Do not confuse sampling uncertainty with shift', 'Bootstrap draws rearrange observed sites; they cannot create a future labor strike, a new carrier contract or a changed target definition. Use a later untouched period and inspect [[machine-learning/regression-error-slices-and-tail-cost|costly error tails]] before release. A positive interval on one historical cohort does not prove improvement everywhere. Where the operational policy has asymmetric costs, bootstrap the policy value itself instead of relying on MAE.'),
    ('Make the release rule explicit', 'Decide in advance whether a gain must exceed a practical minimum and whether the lower interval endpoint must clear zero. If the result is uncertain, collect more independent labeled sites or run a limited pilot rather than reporting a false precision. [[machine-learning/ensemble-release-review-project|The release checklist]] combines paired gain, validity and serving cost in one decision.')],
    '''from random import Random

site_results = {
    "East": [(7, 5, 6), (9, 5, 8)],
    "West": [(4, 7, 5), (8, 6, 8)],
    "Harbor": [(11, 7, 10), (6, 4, 6)],
    "North": [(5, 8, 5), (9, 6, 8)],
    "Inland": [(10, 7, 9), (7, 5, 7)],
    "South": [(6, 8, 6), (12, 8, 11)],
}

def mean_gain(site_names):
    gains = [abs(actual - baseline) - abs(actual - challenger)
             for site in site_names
             for actual, baseline, challenger in site_results[site]]
    return sum(gains) / len(gains)

sites = list(site_results)
observed_gain = mean_gain(sites)
randomizer = Random(47)
draws = sorted(mean_gain([randomizer.choice(sites) for _ in sites])
               for _ in range(1600))
interval = (draws[80], draws[1520])
assert observed_gain > 0
assert interval[0] <= interval[1]
assert len(draws) == 1600''',
    'With B bootstrap replicates and N shipments, direct resampling and scoring costs O(BN) time; sorting B estimates costs O(B log B), with O(B + N) retained data. For large holdouts, cache per-group error sums and counts to avoid revisiting every shipment on each draw.',
    ['Do not resample baseline and challenger errors separately.', 'Do not bootstrap individual rows when deployment units are dependent groups.', 'Do not describe a percentile band as protection against future distribution shift.'],
    ['machine-learning/regression-baselines-and-holdout-metrics','machine-learning/feature-drift-and-delayed-label-monitoring','machine-learning/group-and-time-validation','machine-learning/ensemble-release-review-project'])


add('feature-drift-and-delayed-label-monitoring',
    'Feature drift and delayed-label monitoring',
    'A drift monitor compares serving inputs with a frozen reference distribution, while a separate matured-label cohort measures actual model error after outcomes have had time to arrive.', [
    ('Watch inputs without inventing outcomes', 'A shipment model scores intake backlog before clearance is known. A same-day dashboard can count missing values, schema violations and backlog-bin frequencies; it cannot calculate same-day clearance error before shipments have cleared. The code compares two fixed-bin distributions with total variation distance and separately filters records whose outcomes have matured. The bins and baseline period must be frozen before inspecting the live batch.'),
    ('Distinguish a warning from a failure', 'A high distance means the input mix changed according to this chosen summary. It does not prove predictions became worse. A new warehouse may be larger but easier to process, while a model can degrade with little marginal feature drift if the label rule changes. Investigate by site, model version and feature version. [[machine-learning/prediction-time-feature-availability|Availability at scoring time]] may change even when a column name does not.'),
    ('Use the correct outcome clock', 'For clearance within 48 hours, a cohort scored yesterday is not fully labeled today. Excluding still-open shipments from an error report preferentially keeps fast clearances and biases the result. Require each scored row to pass a defined maturity window before using its outcome, then report coverage and remaining missing labels. The code intentionally excludes pending rows even when a provisional outcome field is present.'),
    ('Separate alert, diagnosis and retraining', 'A distribution alarm opens an investigation: check upstream ingestion, missingness, site mix and timestamps. Confirm whether matured-label loss and the decision policy have changed before retraining. Retraining on the same broken feature pipeline can preserve the fault; reflexively deploying a new model also invalidates the previous comparison. [[machine-learning/leakage-safe-preprocessing-pipeline|The fitted pipeline]] and [[machine-learning/probability-calibration|calibration checks]] need versioned evidence.'),
    ('Define a response path', 'Set alert thresholds from a stable historical window and capacity for review, not from a single arbitrary number. Document owner, triage time, rollback option and the fresh validation period required for a replacement model. Monitor latency and error rate as well as statistical summaries. [[machine-learning/ensemble-release-review-project|The release project]] keeps operational readiness alongside model score.')],
    '''reference_backlogs = [7, 9, 11, 14, 18, 20, 23, 27]
served_backlogs = [9, 12, 21, 24, 31, 33, 35, 39]
frozen_edges = (15, 30)

def proportions(values, edges):
    if not values:
        raise ValueError("empty cohort")
    counts = [0] * (len(edges) + 1)
    for value in values:
        counts[sum(value >= edge for edge in edges)] += 1
    return [count / len(values) for count in counts]

reference_mix = proportions(reference_backlogs, frozen_edges)
served_mix = proportions(served_backlogs, frozen_edges)
drift_distance = sum(abs(previous - current)
                     for previous, current in zip(reference_mix, served_mix)) / 2

# scored day, clearance day (or None), observed hours (or None), predicted hours
scored_shipments = [(1, 3, 7, 6), (2, 4, 8, 7),
                    (4, None, None, 9), (7, 8, 5, 6)]
report_day = 10
maturity_days = 3
matured = [(actual, predicted) for scored, cleared, actual, predicted
           in scored_shipments
           if scored + maturity_days <= report_day
           and cleared is not None and cleared <= report_day
           and actual is not None]
matured_mae = sum(abs(actual - predicted) for actual, predicted in matured) / len(matured)
assert 0 <= drift_distance <= 1
assert len(matured) == 3
assert matured_mae == 1''',
    'Computing B fixed-bin counts over N served rows costs O(NB) time in this direct implementation and O(B) counter memory; binary-search bins can reduce per-row cost. Matured-label scoring is O(M) for M eligible rows. Logging, retention and privacy controls can cost more than the arithmetic.',
    ['Do not call feature drift proof of worse prediction quality.', 'Do not score only already-cleared shipments when outcomes are delayed.', 'Do not retrain automatically before checking upstream data and target definitions.'],
    ['machine-learning/paired-bootstrap-model-gain-intervals','machine-learning/prediction-time-feature-availability','machine-learning/probability-calibration','machine-learning/ensemble-release-review-project'])


add('ensemble-release-review-project',
    'Ensemble release review project',
    'Build a release record that compares a constrained tree, bagged or boosted candidate, and a training-only baseline on a later shipment cohort while checking uncertainty and monitoring readiness.', [
    ('Freeze the decision and data boundary', 'The service predicts clearance hours at intake so dispatch can allocate staff. Write the action threshold, cost of late underestimation, target clock and feature availability before training. Use shipment groups and a later date for final evaluation. Keep the later cohort untouched during feature design, tree sizing and stage selection. [[machine-learning/group-and-time-validation|The validation lesson]] defines that separation.'),
    ('Build one comparable scorecard', 'Fit the training-median baseline, a constrained tree, a bagged forest candidate and a boosted candidate on the same permitted training rows. Select settings using development validation. On the final cohort, store row-aligned predictions and report MAE, costly-underestimate rate, support by site and serving latency. A favorable out-of-bag score is useful diagnostic evidence but cannot replace the later cohort. Compare [[machine-learning/bootstrap-bagging-and-out-of-bag-evaluation|OOB behavior]] and [[machine-learning/gradient-boosting-residuals-and-early-stopping|selected boosting stage]] with their own limitations stated.'),
    ('Quantify the uncertain gain', 'Calculate each candidate’s paired gain over the baseline and resample the independent evaluation groups. Report the observed gain, an interval, group count and tail cases. If the interval includes a material loss or one site drives the result, do not hide that inside an overall score. [[machine-learning/paired-bootstrap-model-gain-intervals|The paired interval guide]] supplies the mechanics; the release decision remains a policy choice.'),
    ('Check the serving contract', 'Save model and preprocessing versions, feature order, missing-value policy, seed, training cutoff and selected settings. Reconstruct one historical request through the serving path and compare with the offline prediction. Set a latency budget and measure it under realistic batch size. Confirm that delayed outcomes are not treated as instant feedback. [[machine-learning/feature-drift-and-delayed-label-monitoring|The monitoring guide]] separates immediate input alerts from mature error.'),
    ('Record a disposition and next experiment', 'The code is a small decision gate over a reviewed scorecard; it cannot decide statistical validity by itself. State whether the candidate is ready for a limited pilot, needs more independent labels or fails a service constraint. Assign an owner and date to each blocker. If approved, plan a monitored comparison with rollback, rather than silently replacing the incumbent. The same record should explain why a simpler model was or was not sufficient.')],
    '''def release_disposition(review):
    blockers = []
    if not review["feature_clock_verified"] or not review["final_test_sealed"]:
        blockers.append("evaluation boundary")
    if review["independent_sites"] < 5:
        blockers.append("site support")
    if review["gain_interval_low_hours"] <= 0:
        blockers.append("uncertain gain")
    if review["tail_miss_rate"] > review["tail_rate_limit"]:
        blockers.append("costly tail")
    if review["p95_latency_ms"] > review["latency_budget_ms"]:
        blockers.append("serving latency")
    if not review["mature_label_monitor_ready"]:
        blockers.append("outcome monitoring")
    return "pilot review" if not blockers else "hold: " + ", ".join(blockers)

shipment_review = {
    "feature_clock_verified": True,
    "final_test_sealed": True,
    "independent_sites": 6,
    "gain_interval_low_hours": -0.2,
    "tail_miss_rate": 0.08,
    "tail_rate_limit": 0.06,
    "p95_latency_ms": 31,
    "latency_budget_ms": 45,
    "mature_label_monitor_ready": True,
}
decision = release_disposition(shipment_review)
assert decision == "hold: uncertain gain, costly tail"''',
    'Scoring N final shipments with T tree nodes traversed per prediction has model-dependent cost; paired score and slice aggregation is O(N), while grouped bootstrap adds O(BN) in a direct implementation. Serving p95 latency, retraining time and monitoring storage must be measured in the target environment.',
    ['Do not promote a candidate using its out-of-bag score alone.', 'Do not count correlated scans as independent sites.', 'Do not announce a release when outcome monitoring is not ready.'],
    ['machine-learning/bootstrap-bagging-and-out-of-bag-evaluation','machine-learning/random-forest-feature-subsampling-and-leaf-support','machine-learning/gradient-boosting-residuals-and-early-stopping','machine-learning/learning-curves-and-training-size-diagnosis','machine-learning/paired-bootstrap-model-gain-intervals','machine-learning/feature-drift-and-delayed-label-monitoring','machine-learning/shipment-delay-model-review-project'])


publish_batch(
    lessons,
    module_title='Ensembles, uncertainty and operations',
    module_summary='Bagging, forest splits, boosting, learning curves, paired uncertainty and delayed-label monitoring.',
    project_heading='Ensemble release review',
    crosslinks=[
        ('machine-learning/decision-tree-splits-and-leaf-support', lessons[0]['path']),
        ('machine-learning/bootstrap-bagging-and-out-of-bag-evaluation', lessons[1]['path']),
        ('machine-learning/hyperparameter-search-and-untouched-test', lessons[2]['path']),
        ('machine-learning/regression-baselines-and-holdout-metrics', lessons[3]['path']),
        ('machine-learning/regression-error-slices-and-tail-cost', lessons[4]['path']),
        ('machine-learning/prediction-time-feature-availability', lessons[5]['path']),
        ('machine-learning/shipment-delay-model-review-project', lessons[6]['path']),
    ],
    sort_start=4700,
)
