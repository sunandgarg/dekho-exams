"""Add original Machine Learning lessons for operational classification triage."""
from ml_fixture_writer_20261005 import publish_batch

lessons = []


def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='machine-learning/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))


add('nearest-neighbor-distance-and-local-support',
    'Nearest-neighbor distance and local support',
    'A nearest-neighbor classifier predicts from nearby labeled training cases under a declared distance, feature scale and neighborhood size.', [
    ('Define similarity for the decision', 'A dispatch desk wants to flag likely missed handoffs using intake backlog and available crew. Two shipments are neighbors only because the chosen feature representation and distance say so. Backlog counts and crew counts have different units; fit their centers and scales on training cases, then reuse those values for every query. A feature recorded after handoff cannot become a distance coordinate. [[machine-learning/prediction-time-feature-availability|The feature clock]] comes first.'),
    ('Count support before trusting a vote', 'The code finds the three nearest past shipments and uses a majority vote. It returns their distances as well as the class, because a three-to-zero vote among very distant cases is weak local evidence. With one neighbor, an odd label can change a decision; with too many, the neighborhood can cross distinct operating regimes. Select neighbor count and distance policy on development folds. [[machine-learning/group-and-time-validation|Group and time boundaries]] matter because repeated scans make near duplicates.'),
    ('Plan for distance ties and missing values', 'Equal distances need a deterministic tie rule. This teaching code orders by distance and training-row position, then gives class zero the tie if votes split. A deployed policy should state how duplicates, missing crew counts and mixed numeric/categorical attributes are handled. Encoding a warehouse name as an arbitrary integer creates fictional geometry. [[machine-learning/distance-scaling-before-clustering|The scaling lesson]] explains why one large-range field can dominate.'),
    ('Recognize the high-dimensional limit', 'With many weak or redundant features, distances may become less useful and exact neighbor lookup can approach a scan of the training set. Feature selection, dimensionality reduction or a different model may be preferable. Do not assume a spatial index always helps. Compare a simple logistic model and tree on the same future cohort. [[machine-learning/logistic-regression-log-loss-and-odds|The logistic lesson]] gives one baseline with cheaper serving.'),
    ('Keep local labels and privacy in scope', 'Nearest-neighbor serving may retain every labeled training row, including records that should be deleted or restricted. Store an approved feature representation, access controls and a deletion policy. A neighbor explanation should not reveal another shipment’s private details. Review local error by site and prevalence; a nearby majority from the wrong class mix can conceal rare failures. [[machine-learning/rare-event-precision-recall-and-prevalence|Rare-event evaluation]] still applies.')],
    '''from math import sqrt

past_shipments = [
    (11, 8, 0), (14, 7, 0), (17, 6, 0),
    (24, 5, 1), (28, 4, 1), (31, 3, 1),
]
query_backlog, query_crew = 26, 5

def training_scale(rows):
    means = [sum(row[column] for row in rows) / len(rows) for column in (0, 1)]
    spreads = [sqrt(sum((row[column] - means[column]) ** 2 for row in rows) / len(rows))
               for column in (0, 1)]
    if any(spread == 0 for spread in spreads):
        raise ValueError("constant distance feature")
    return means, spreads

means, spreads = training_scale(past_shipments)
neighbors = sorted(
    (sqrt(((backlog - query_backlog) / spreads[0]) ** 2
          + ((crew - query_crew) / spreads[1]) ** 2), index, missed)
    for index, (backlog, crew, missed) in enumerate(past_shipments)
)[:3]
votes_for_miss = sum(missed for _, _, missed in neighbors)
predicted_miss = int(votes_for_miss > len(neighbors) / 2)
assert predicted_miss == 1
assert len(neighbors) == 3
assert all(distance >= 0 for distance, _, _ in neighbors)''',
    'For N stored rows and F numeric features, this brute-force query costs O(NF + N log N) time because it sorts all distances, with O(NF) retained training storage. A size-k heap can reduce the selection step. Index performance depends on dimension and metric; test the actual serving workload.',
    ['Do not compute a new scale from each query or from the final test set.', 'Do not interpret a unanimous but distant neighborhood as strong evidence.', 'Do not use arbitrary integer codes for categories as distances.'],
    ['machine-learning/naive-bayes-smoothing-and-dependent-features','machine-learning/fold-local-feature-selection-and-stability','machine-learning/distance-scaling-before-clustering','machine-learning/handoff-triage-model-review-project'])


add('naive-bayes-smoothing-and-dependent-features',
    'Naive Bayes smoothing and dependent features',
    'A categorical naive Bayes classifier combines a training-derived class prior with per-feature likelihoods while assuming features are independent after conditioning on class.', [
    ('State the conditional assumption precisely', 'A missed-handoff triage model might observe an intake scan gap and a staffing alert. Naive Bayes multiplies each feature likelihood conditional on whether the handoff was missed. It does not claim the features are unconditionally independent. If both alerts are generated from the same system outage, their evidence is counted twice under the model. The ranking may remain useful, but the numeric probability can be overconfident. [[machine-learning/probability-calibration|Calibration]] must be checked separately.'),
    ('Smooth unseen combinations', 'A rare class may have no training case with one alert present. Without smoothing, its likelihood becomes zero and can overwhelm all other evidence. The code applies add-one smoothing to Bernoulli feature counts, then adds log likelihoods to avoid multiplying tiny numbers. This is a small binary-feature teaching model; event counts in documents or continuous measurements require different likelihood families and assumptions.'),
    ('Keep the class prior from the right period', 'The prior reflects the positive share in the training cohort. It may differ after a carrier contract or label policy changes. Do not insert the future test prevalence into the training prior to make a result look better. Report the observed prevalence by development and final cohorts. [[machine-learning/rare-event-precision-recall-and-prevalence|The rare-event guide]] shows why accuracy and precision shift with class mix.'),
    ('Inspect correlated signals and missingness', 'A scan-gap alert and delayed-scan count can be almost the same event. Including both can produce extreme log odds without new information. Compare performance with one removed, inspect conditional co-occurrence and distinguish an absent alert from a missing sensor reading. Treating missing as false changes the question. [[machine-learning/prediction-time-feature-availability|Feature availability]] needs a serving-time contract.'),
    ('Compare against a calibrated alternative', 'Use the same future rows to compare this model with a training-rate baseline and logistic regression. Evaluate precision, recall and log loss before deciding whether its simplicity is worth the independence approximation. A probability threshold comes from intervention cost, not from the Bayes formula itself. [[machine-learning/decision-threshold-and-cost|Decision policy]] remains a separate layer.')],
    '''from math import exp, log

# scan gap, staffing alert, missed handoff
training_events = [
    (0, 0, 0), (0, 1, 0), (0, 0, 0), (1, 0, 0),
    (1, 1, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1),
]

def log_class_score(signals, missed):
    matching = [event for event in training_events if event[2] == missed]
    prior = len(matching) / len(training_events)
    score = log(prior)
    for column, present in enumerate(signals):
        present_count = sum(event[column] for event in matching)
        smoothed_present = (present_count + 1) / (len(matching) + 2)
        score += log(smoothed_present if present else 1 - smoothed_present)
    return score

def missed_probability(signals):
    log_safe = log_class_score(signals, 0)
    log_missed = log_class_score(signals, 1)
    odds = exp(log_missed - log_safe)
    return odds / (1 + odds)

assert missed_probability((1, 1)) > missed_probability((0, 0))
assert 0 < missed_probability((1, 0)) < 1''',
    'Counting class-feature pairs takes O(NF) training time and O(CF) model storage for N rows, F binary features and C classes. A score costs O(CF) time. Log arithmetic prevents many underflow failures, but correlated features and shifted priors still require evaluation.',
    ['Do not interpret the conditional independence assumption as a fact about the process.', 'Do not allow an unseen feature value to create a zero likelihood without a policy.', 'Do not assume the returned probability is calibrated.'],
    ['machine-learning/nearest-neighbor-distance-and-local-support','machine-learning/logistic-regression-log-loss-and-odds','machine-learning/probability-calibration','machine-learning/handoff-triage-model-review-project'])


add('fold-local-feature-selection-and-stability',
    'Fold-local feature selection and stability',
    'Feature selection ranks or tests candidate inputs using training data inside each validation fold, then checks whether the chosen set and gain survive other folds.', [
    ('Treat a selector as fitted state', 'Suppose a handoff model considers backlog, crew count and route congestion. A selector that compares each feature with the missed-handoff label has learned from those labels, even if no classifier was fitted yet. Running it on the whole dataset before cross-validation leaks validation outcomes into every training fold. Fit the selector inside each fold, then transform that fold’s validation rows using only its selected columns. [[machine-learning/leakage-safe-preprocessing-pipeline|The pipeline guide]] applies to selectors too.'),
    ('Use a score that matches its claim', 'The code ranks numeric features by the absolute difference between positive and negative training means. It is a univariate screening example, not a feature-importance estimate, proof of causality or optimal subset search. Correlated features can split value, interactions can be missed, and a rare class can make the mean unstable. The classifier’s actual validation score, cost and slice performance decide whether a selected set is useful.'),
    ('Measure selection stability', 'Record selected names across time-aware or group-aware development folds. If one feature wins only when a single warehouse enters training, investigate measurement and site dependence. A stable shortlist can reduce maintenance and inference cost, but stability alone does not guarantee better predictions. [[machine-learning/permutation-importance-on-held-out-data|Held-out permutation importance]] asks a different question about a fitted model.'),
    ('Reject future-only predictors first', 'No statistical selector can make an unavailable field deployable. Remove outcomes, post-handoff scan counts and identifiers that encode the label before ranking. For each remaining feature, record capture time, missingness and feature version. A strong score from a leaking field is evidence of a broken experiment. [[machine-learning/prediction-time-feature-availability|The clock check]] precedes feature search.'),
    ('Freeze the final feature contract', 'After choosing the selection method and its settings on development folds, refit it on permitted development rows and evaluate the complete pipeline once on a sealed future test. Keep the chosen feature order with the trained model. Re-selecting columns from live outcomes without a new validation process changes the model. [[machine-learning/hyperparameter-search-and-untouched-test|Untouched-test selection]] defines that final step.')],
    '''from collections import Counter

development_rows = [
    {"backlog": 8, "crew": 8, "congestion": 2, "missed": 0},
    {"backlog": 12, "crew": 7, "congestion": 3, "missed": 0},
    {"backlog": 17, "crew": 6, "congestion": 4, "missed": 0},
    {"backlog": 22, "crew": 5, "congestion": 4, "missed": 1},
    {"backlog": 27, "crew": 4, "congestion": 6, "missed": 1},
    {"backlog": 31, "crew": 3, "congestion": 7, "missed": 1},
]
candidate_names = ("backlog", "crew", "congestion")

def choose_feature(training_rows):
    positives = [row for row in training_rows if row["missed"] == 1]
    negatives = [row for row in training_rows if row["missed"] == 0]
    if not positives or not negatives:
        raise ValueError("both classes required")
    gaps = {name: abs(sum(row[name] for row in positives) / len(positives)
                      - sum(row[name] for row in negatives) / len(negatives))
            for name in candidate_names}
    return max(candidate_names, key=lambda name: (gaps[name], name))

folds = [([0, 1, 3, 4], [2, 5]), ([0, 2, 3, 5], [1, 4])]
selected = []
for training_ids, validation_ids in folds:
    assert set(training_ids).isdisjoint(validation_ids)
    selected.append(choose_feature([development_rows[index] for index in training_ids]))

selection_counts = Counter(selected)
assert len(selected) == 2
assert set(selection_counts).issubset(candidate_names)
assert all(count > 0 for count in selection_counts.values())''',
    'This univariate screen takes O(KNF) time across K folds, N rows per fold and F features, with O(F) score memory. More complex subset search can be much costlier. The larger expense may be repeated downstream model fitting, so budget selection and evaluation together.',
    ['Do not select features once on all labeled rows before cross-validation.', 'Do not keep a future-only field because its ranking score is high.', 'Do not treat a selected feature as a causal driver.'],
    ['machine-learning/nearest-neighbor-distance-and-local-support','machine-learning/permutation-importance-on-held-out-data','machine-learning/leakage-safe-preprocessing-pipeline','machine-learning/handoff-triage-model-review-project'])


add('class-weighting-versus-decision-thresholds',
    'Class weighting versus decision thresholds',
    'Class weighting changes the training loss assigned to each labeled class, while a decision threshold changes which already-produced scores trigger an action.', [
    ('Separate the two controls', 'A missed handoff occurs less often than an on-time handoff. Weighting positive examples more heavily asks the optimizer to spend more capacity fitting them; moving the alert threshold changes the dispatch rule after training. These interventions can produce similar recall at one operating point but different rankings and probability behavior. Choose the operation according to the failure mode rather than treating the controls as interchangeable. [[machine-learning/decision-threshold-and-cost|The threshold guide]] defines the action layer.'),
    ('Estimate weights from training labels only', 'The code sets a declared positive weight and fits two one-feature logistic models, one weighted and one unweighted. Weighted loss can shift a probability upward at the same backlog. A balanced inverse-frequency weight is one possible starting value, but its formula reflects class counts, not the real cost of a missed handoff. Do not use final-test prevalence to calculate training weights. [[machine-learning/rare-event-precision-recall-and-prevalence|Prevalence]] belongs in every evaluation report.'),
    ('Recheck calibration after weighting', 'A weighted classifier’s numeric outputs often should not be read as event frequencies without checking them on representative, disjoint labeled data. If dispatch computes expected cost from those values, calibration matters. A lower threshold applied to a calibrated model may be easier to audit than changing the training objective; the comparison must use the same future cohort. [[machine-learning/probability-calibration|Calibration checks]] expose a shifted probability scale.'),
    ('Inspect false alarms and missed events', 'Report precision, recall, number of daily alerts, and errors by site at each candidate operating point. An alert policy that catches most misses but creates more reviews than the desk can process is not usable. Conversely, a weighted fit can help if the learner ignored a rare class entirely. Select settings inside development data, then verify once on an untouched later period. [[machine-learning/hyperparameter-search-and-untouched-test|Model selection]] protects that claim.'),
    ('Keep labels and the intervention stable', 'Weights cannot correct a mislabeled outcome, a new carrier mix or a feature that arrives after the alert decision. If a staffing change reduces misses, the target rate and action value can shift. Monitor outcome maturity and post-deployment error before retraining. [[machine-learning/feature-drift-and-delayed-label-monitoring|The monitoring guide]] separates immediate feature changes from delayed error evidence.')],
    '''from math import exp

shipments = [(0.1, 0), (0.3, 0), (0.5, 0), (0.8, 0),
             (1.1, 0), (1.4, 0), (1.7, 0), (2.0, 1)]

def chance(intercept, slope, backlog):
    score = intercept + slope * backlog
    return 1 / (1 + exp(-score))

def fit_weighted_logistic(positive_weight):
    intercept, slope = 0.0, 0.0
    for _ in range(1000):
        intercept_gradient = 0.0
        slope_gradient = 0.0
        for backlog, missed in shipments:
            weight = positive_weight if missed else 1.0
            residual = weight * (chance(intercept, slope, backlog) - missed)
            intercept_gradient += residual
            slope_gradient += backlog * residual
        intercept -= 0.06 * intercept_gradient / len(shipments)
        slope -= 0.06 * slope_gradient / len(shipments)
    return intercept, slope

plain = fit_weighted_logistic(1.0)
upweighted = fit_weighted_logistic(5.0)
assert chance(*upweighted, 1.5) > chance(*plain, 1.5)
assert 0 < chance(*plain, 1.5) < 1''',
    'A dense one-feature full-batch fit takes O(IN) time over I iterations and N rows; with F features it is O(INF). Applying a new threshold to stored scores is O(N) and needs no retraining. Calibrating and auditing either policy adds data and review cost.',
    ['Do not derive training weights from final-test labels.', 'Do not assume weighted output remains calibrated.', 'Do not optimize recall without checking review capacity and precision.'],
    ['machine-learning/rare-event-precision-recall-and-prevalence','machine-learning/decision-threshold-and-cost','machine-learning/probability-calibration','machine-learning/handoff-triage-model-review-project'])


add('multiclass-confusion-and-action-costs',
    'Multiclass confusion and action costs',
    'Multiclass evaluation reports where each true category is sent, while an action policy compares expected costs across possible interventions instead of choosing a label mechanically.', [
    ('Define mutually exclusive outcomes', 'A handoff can fail because of an intake scan gap, insufficient crew or a weather block. A single-label multiclass classifier assigns one primary reason under an adjudication rule; if multiple reasons may apply simultaneously, that is a multilabel task instead. Fix the label rule before training. A confusion matrix records true categories by predicted category and exposes which mistake pairs dominate. [[machine-learning/rare-event-precision-recall-and-prevalence|Class prevalence]] should accompany the matrix.'),
    ('Read each class with its denominator', 'The code counts a small three-class future cohort and computes recall for each true class. A high overall accuracy could still miss most weather blocks if they are rare. Report support and per-class precision as well; a model can have high recall by overpredicting a category. At low counts, one case changes a rate substantially. Keep an unassigned or uncertain path where the operational process requires it rather than forcing a reason from weak evidence.'),
    ('Optimize the action, not the class name', 'Adding crew, repairing a scanner and rerouting are different interventions with different effects and costs. If probabilities are calibrated and the cost matrix is credible, compute the expected cost of each action and choose the least costly permitted one. The lowest-cost action need not correspond to the most probable failure label. [[machine-learning/decision-threshold-and-cost|The binary cost lesson]] is the simpler version of this policy.'),
    ('Validate probability and cost inputs', 'A multiclass probability vector should be nonnegative and sum to one; its class order must match the cost columns exactly. Calibration by class and by site deserves inspection before interpreting expected costs. Cost entries should reflect resource limits and who bears the consequence, not convenient invented numbers. The example uses fictional costs only to show the arithmetic. [[machine-learning/probability-calibration|Calibration]] remains a prerequisite for a probability-based dispatch rule.'),
    ('Test the complete decision workflow', 'Report confusion, per-class support and realized intervention cost on a later, untouched cohort. Compare against a simple current rule, not only another classifier. Watch for label latency and policy feedback: rerouting can change the eventual reason recorded. [[machine-learning/feature-drift-and-delayed-label-monitoring|Monitoring]] must preserve the prediction-time record and the outcome clock.')],
    '''categories = ("scan_gap", "crew_shortage", "weather_block")
future_cases = [
    ("scan_gap", "scan_gap"), ("scan_gap", "crew_shortage"),
    ("crew_shortage", "crew_shortage"), ("crew_shortage", "crew_shortage"),
    ("crew_shortage", "scan_gap"), ("weather_block", "weather_block"),
    ("weather_block", "crew_shortage"),
]
confusion = {(actual, predicted): sum(
    observed == actual and assigned == predicted
    for observed, assigned in future_cases)
    for actual in categories for predicted in categories}
recall = {category: confusion[(category, category)] /
          sum(confusion[(category, prediction)] for prediction in categories)
          for category in categories}

current_risk = {"scan_gap": 0.25, "crew_shortage": 0.50, "weather_block": 0.25}
action_cost = {
    "repair_scanner": {"scan_gap": 1, "crew_shortage": 6, "weather_block": 4},
    "add_crew": {"scan_gap": 4, "crew_shortage": 1, "weather_block": 5},
    "reroute": {"scan_gap": 5, "crew_shortage": 4, "weather_block": 1},
}
expected_cost = {action: sum(current_risk[reason] * costs[reason]
                             for reason in categories)
                 for action, costs in action_cost.items()}
chosen_action = min(expected_cost, key=expected_cost.get)
assert chosen_action == "add_crew"
assert recall["weather_block"] == 0.5
assert abs(sum(current_risk.values()) - 1) < 1e-12''',
    'Counting N labeled rows is O(N + C²) time and O(C²) memory for C classes. Comparing A actions against C probabilities costs O(AC) per decision. Maintaining accurate cost inputs and representative calibration data is usually harder than the arithmetic.',
    ['Do not force a single label when multiple causes can co-occur.', 'Do not infer a rare-class recall from one or two cases without showing support.', 'Do not align probabilities and cost columns by undocumented list position.'],
    ['machine-learning/rare-event-precision-recall-and-prevalence','machine-learning/decision-threshold-and-cost','machine-learning/probability-calibration','machine-learning/handoff-triage-model-review-project'])


add('handoff-triage-model-review-project',
    'Handoff triage model review project',
    'Compare local, probabilistic and cost-sensitive classifiers for missed handoffs, then document a bounded dispatch policy on a later cohort.', [
    ('Lock the action and outcome clock', 'The desk decides at intake whether to investigate a likely missed handoff. Record what counts as a miss, when the label matures and which crew or scan fields exist before intervention. Partition by site and date so repeated scans cannot bridge training and validation. Keep the final later cohort sealed until model design and threshold are fixed. [[machine-learning/group-and-time-validation|The split lesson]] and [[machine-learning/prediction-time-feature-availability|feature timing]] form the review boundary.'),
    ('Compare three distinct inductive assumptions', 'Nearest neighbors assumes nearby shipment profiles have useful local labels; categorical naive Bayes combines conditional likelihoods; logistic regression fits a linear log-odds surface. Fit any scaling, smoothing choice, feature selector and weights inside development folds. Compare all three with a training-rate baseline. [[machine-learning/nearest-neighbor-distance-and-local-support|Neighbor support]], [[machine-learning/naive-bayes-smoothing-and-dependent-features|feature dependence]] and [[machine-learning/fold-local-feature-selection-and-stability|fold-local selection]] are separate failure modes.'),
    ('Build an action scorecard', 'On the untouched cohort, report prevalence, confusion counts, precision, recall, calibration and daily alert volume. Show slices by site and shift with denominators. Evaluate the actual staffing cost of false alarms against missed handoffs. If the desk chooses among multiple interventions, compare their expected and realized costs rather than choosing the most likely label blindly. [[machine-learning/multiclass-confusion-and-action-costs|The multiclass guide]] explains that distinction.'),
    ('Explain why weighting was or was not needed', 'If the learner ignores the rare class, compare a class-weighted fit with a calibrated unweighted fit using a cost-selected threshold. Recheck probability quality after weighting. Do not claim a training weight equals the business cost ratio. The same future cases must support the comparison. [[machine-learning/class-weighting-versus-decision-thresholds|The weighting guide]] keeps optimization and policy separate.'),
    ('Record a pilot decision', 'The code lists evidence required for a limited pilot discussion. A passing checklist does not prove future value; it means a named owner can review the attached measurements, rollback rule and delayed-label monitor. If calibration or capacity is missing, hold the alert workflow and collect the required evidence. [[machine-learning/feature-drift-and-delayed-label-monitoring|The monitoring lesson]] supplies the post-launch clock.')],
    '''def triage_review(packet):
    requirements = {
        "feature_clock_checked": "prediction-time features",
        "site_time_split_checked": "site and time split",
        "final_cohort_sealed": "final cohort",
        "class_support_reported": "class support",
        "calibration_checked": "calibration",
        "review_capacity_checked": "desk capacity",
        "cost_rule_written": "intervention costs",
        "delayed_label_monitor_ready": "matured-label monitor",
    }
    missing = [description for key, description in requirements.items()
               if not packet.get(key)]
    return "pilot review" if not missing else "hold: " + ", ".join(missing)

dispatch_packet = {
    "feature_clock_checked": True,
    "site_time_split_checked": True,
    "final_cohort_sealed": True,
    "class_support_reported": True,
    "calibration_checked": False,
    "review_capacity_checked": False,
    "cost_rule_written": True,
    "delayed_label_monitor_ready": True,
}
assert triage_review(dispatch_packet) == "hold: calibration, desk capacity"''',
    'Brute-force neighbor scoring is O(NF) per case before neighbor selection, while a fitted naive Bayes or logistic score is O(F) per case. The review gate is O(K) for K requirements; it cannot calculate calibration, operational cost or case-review capacity without their underlying data.',
    ['Do not reuse a final cohort to choose features or a threshold.', 'Do not interpret naive Bayes or weighted-model scores as calibrated without checking.', 'Do not launch an alert stream that exceeds the desk’s review capacity.'],
    ['machine-learning/nearest-neighbor-distance-and-local-support','machine-learning/naive-bayes-smoothing-and-dependent-features','machine-learning/fold-local-feature-selection-and-stability','machine-learning/class-weighting-versus-decision-thresholds','machine-learning/multiclass-confusion-and-action-costs','machine-learning/feature-drift-and-delayed-label-monitoring'])


publish_batch(
    lessons,
    module_title='Neighbor, probabilistic and cost-sensitive triage',
    module_summary='Local neighbors, smoothed Bayes scores, fold-local feature choice, weighted loss and multiclass dispatch cost.',
    project_heading='Handoff triage model review',
    crosslinks=[
        ('machine-learning/distance-scaling-before-clustering', lessons[0]['path']),
        ('machine-learning/logistic-regression-log-loss-and-odds', lessons[1]['path']),
        ('machine-learning/leakage-safe-preprocessing-pipeline', lessons[2]['path']),
        ('machine-learning/decision-threshold-and-cost', lessons[3]['path']),
        ('machine-learning/rare-event-precision-recall-and-prevalence', lessons[4]['path']),
        ('machine-learning/classification-and-segmentation-review-project', lessons[5]['path']),
    ],
    sort_start=4900,
)
