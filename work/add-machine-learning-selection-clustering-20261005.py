"""Add full Machine Learning lessons on model selection and unsupervised structure."""
from ml_fixture_writer_20261005 import publish_batch

lessons = []

def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='machine-learning/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))

add('hyperparameter-search-and-untouched-test',
    'Hyperparameter search and an untouched final test',
    'Hyperparameter search selects a model setting using development data; a final test estimates performance only after that selection and preprocessing are frozen.', [
    ('Separate fitting, selection and evaluation', 'A shipment-clearance model has candidate ridge penalties of 0, 20 and 80. For each development fold, fit scaling and coefficients on the fold training rows, then score that fold’s held-out rows. Average those validation errors to choose a penalty. The future test period is not a fourth fold in the search; it is opened once after the penalty and feature set are fixed. [[machine-learning/group-and-time-validation|The validation lesson]] explains why the fold calendar matters.'),
    ('Count the search as part of the model', 'Trying dozens of features, loss functions and penalties and retaining the lowest validation error can overfit the development sample even if each individual fit is clean. Compare multiple candidates under the same folds and keep a record of all attempted settings. A nested outer validation loop can estimate the performance of the entire selection procedure when data support it. For a single final release, an untouched future holdout serves a similar practical purpose.'),
    ('Inspect fold spread and failure modes', 'A mean MAE of 2.8 hours may conceal one route-month fold at 6.4 hours. Keep each fold score and support count, and investigate whether a deployment boundary or weather event explains the discrepancy. A setting that wins by 0.02 hours with much greater compute cost may not be worth adopting. [[machine-learning/regression-error-slices-and-tail-cost|Error slices]] should accompany the selected score.'),
    ('Freeze all learned state', 'The selected setting is not just a penalty. Save feature order, missing-value policy, scaler parameters, training end date, target definition and model artifact. If preprocessing is fitted on the whole development dataset before cross-validation, validation rows influence it. [[machine-learning/leakage-safe-preprocessing-pipeline|The pipeline lesson]] keeps every learned transform inside the fold.'),
    ('Use the final test once', 'The code chooses from already computed inner-fold scores and breaks a tie toward the smaller penalty. It does not fit models or estimate uncertainty. Once the setting is selected, fit it on all permitted development rows, then score a later test period. If the result disappoints and the model changes, acquire a new final period or label the old one as development data. [[machine-learning/segmentation-and-model-selection-project|The applied review]] records that boundary.')],
    '''def choose_penalty(inner_fold_mae):
    if not inner_fold_mae:
        raise ValueError("no candidates")
    ranked = []
    for penalty, fold_errors in inner_fold_mae.items():
        if penalty < 0 or not fold_errors or any(error < 0 for error in fold_errors):
            raise ValueError("invalid candidate scores")
        ranked.append((sum(fold_errors) / len(fold_errors), penalty))
    mean_error, selected_penalty = min(ranked)
    return selected_penalty, mean_error

# These errors came from the same three time-aware development folds.
development_scores = {0: [3.3, 3.0, 4.2],
                      20: [2.9, 2.8, 3.6],
                      80: [3.1, 3.0, 3.5]}
penalty, validation_mae = choose_penalty(development_scores)
assert penalty == 20
assert abs(validation_mae - 3.1) < 1e-12''',
    'For H settings and F recorded fold scores, selection is O(H × F) time and O(H) ranking space. The actual cost is H × F model fits, multiplied again by outer folds if nested evaluation is used.',
    ['Do not include final test scores in the hyperparameter table.', 'Do not preprocess across development folds before fitting.', 'Do not hide the number of attempted settings when interpreting a tiny validation win.'],
    ['machine-learning/ridge-regularization-with-training-only-scaling','machine-learning/group-and-time-validation','machine-learning/permutation-importance-on-held-out-data','machine-learning/segmentation-and-model-selection-project'])

add('permutation-importance-on-held-out-data',
    'Permutation importance on held-out data',
    'Permutation importance measures how much a fitted model’s held-out error changes when one feature column is shuffled while the model remains fixed.', [
    ('Start with a useful model and valid data', 'A clearance-time model predicts from backlog and route distance. First confirm that it beats a training-only baseline on a future holdout; feature importance for a poor model can be misleading. Preserve the model and holdout rows. For one feature, shuffle values across holdout records, predict again, and compare loss. The model is not retrained. [[machine-learning/regression-baselines-and-holdout-metrics|The baseline lesson]] establishes the reference error.'),
    ('Use repeats rather than one lucky shuffle', 'One permutation can accidentally leave values close to their original locations, especially in a short holdout. Repeat with fixed, distinct random seeds and report the distribution of loss increases. The code uses three repeats for a compact demonstration and measures MAE increase; a real analysis needs enough records and repetitions for stable comparison. A negative increase means the shuffled feature happened to improve this measured loss, not that the feature is harmful in every setting.'),
    ('Keep the interpretation predictive', 'A large importance means the fitted model relied on that feature for this holdout distribution and metric. It does not prove the feature causes longer clearance times. Correlated features can substitute for each other, making each individual permutation appear weak even when the pair carries useful signal. The shuffle can also produce feature combinations that rarely occur in real shipments. [[machine-learning/decision-tree-splits-and-leaf-support|Tree rules]] have related interpretation limits.'),
    ('Respect entities and time', 'If rows share a route or customer, shuffling across unrelated groups may create impossible profiles. One may permute within declared strata, but then the question changes to importance conditional on that grouping. Do not use test data repeatedly to select features; reserve a development holdout for diagnostic selection and keep a separate final test. [[machine-learning/group-and-time-validation|Split design]] still governs inspection.'),
    ('Use the result to test a hypothesis', 'If a feature thought essential has near-zero importance, check whether it is redundant, broken at serving time or suppressed by preprocessing. If a future-only feature appears dominant, remove it before celebrating. Document feature version, loss, seeds and holdout support. [[machine-learning/segmentation-and-model-selection-project|The review project]] asks for a concrete follow-up rather than a decorative ranking.')],
    '''from random import Random

def mean_absolute_error(actual, predicted):
    if not actual or len(actual) != len(predicted):
        raise ValueError("aligned outcomes required")
    return sum(abs(left - right) for left, right in zip(actual, predicted)) / len(actual)

def backlog_predictor(shipment):
    return shipment["backlog"] / 4

def backlog_permutation_increase(holdout_shipments, seeds):
    actual = [shipment["clearance_hours"] for shipment in holdout_shipments]
    baseline = mean_absolute_error(actual, [backlog_predictor(shipment)
                                            for shipment in holdout_shipments])
    changes = []
    for seed in seeds:
        values = [shipment["backlog"] for shipment in holdout_shipments]
        Random(seed).shuffle(values)
        altered = [dict(shipment, backlog=value)
                   for shipment, value in zip(holdout_shipments, values)]
        changed_error = mean_absolute_error(actual, [backlog_predictor(shipment)
                                                      for shipment in altered])
        changes.append(changed_error - baseline)
    return changes

shipments = [{"backlog": hours * 4, "clearance_hours": hours}
             for hours in (3, 5, 8, 12, 15)]
increases = backlog_permutation_increase(shipments, (23, 47, 61))
assert len(increases) == 3 and all(increase >= 0 for increase in increases)
assert any(increase > 0 for increase in increases)''',
    'With R repeats and N holdout rows, direct permutation evaluation costs O(R × N) time and O(N + R) space. Each additional feature multiplies prediction calls; model serving time can dominate the shuffle itself.',
    ['Do not present permutation importance as a causal effect.', 'Do not compute importance before verifying holdout predictive quality.', 'Do not shuffle across operational groups without considering impossible combinations.'],
    ['machine-learning/hyperparameter-search-and-untouched-test','machine-learning/prediction-time-feature-availability','machine-learning/decision-tree-splits-and-leaf-support','machine-learning/segmentation-and-model-selection-project'])

add('distance-scaling-before-clustering',
    'Distance scaling before clustering',
    'Distance-based clustering depends on feature units; fit a scaling rule on the analysis population before interpreting which records are near each other.', [
    ('Expose the unit problem', 'A warehouse profile includes average backlog of 1,200 tickets and a handoff delay of 8 minutes. In raw Euclidean distance, a backlog change of 100 overwhelms a delay change of 2 even if operations consider both important. Scaling changes the geometry and therefore the clusters. Choose features for the question first, then choose weights or a scale that reflects meaningful variation. [[machine-learning/k-means-objective-and-restart-stability|K-means]] optimizes distance under that geometry.'),
    ('Fit the transform on the intended cohort', 'The teaching code uses training means and population standard deviations to standardize each numeric feature. A zero-variance feature carries no distance information and is rejected. If the clusters will score later warehouses, save the fitted means, scales and feature order; do not refit per incoming batch. If the goal is a one-time descriptive map of a fixed cohort, that cohort can define the transform, but future claims need a frozen state.'),
    ('Treat outliers and categories deliberately', 'One extreme warehouse can inflate standard deviation and compress ordinary sites. A median-based scale or capped feature may be better, but caps must be fitted without looking at future evaluation rows. Encoding a category as arbitrary integers creates fake distances; use a suitable representation or a distance designed for mixed data. The code accepts only numeric feature columns and makes no claim that standard scaling is always right.'),
    ('Test sensitivity to design choices', 'Re-run clustering with a defensible alternative feature set or scaling method. If membership changes sharply, the segmentation is design-dependent. A lower within-cluster distance alone cannot tell whether segments help staffing or routing decisions. Compare cluster profiles with operational outcomes that were not used to construct the distance, while avoiding post-hoc claims of causal effect. [[machine-learning/segmentation-and-model-selection-project|The project]] captures that audit.'),
    ('Keep prediction and interpretation distinct', 'Clusters describe similarity under a chosen feature space; they do not discover natural types guaranteed to exist outside it. Scaling fitted on combined training and future data can also contaminate a predictive downstream evaluation. [[machine-learning/leakage-safe-preprocessing-pipeline|The pipeline lesson]] applies when clusters become model features.')],
    '''from math import sqrt

def fit_numeric_scale(warehouse_profiles, features):
    if not warehouse_profiles or not features:
        raise ValueError("profiles and features required")
    state = {}
    for feature in features:
        values = [profile[feature] for profile in warehouse_profiles]
        mean = sum(values) / len(values)
        scale = sqrt(sum((value - mean) ** 2 for value in values) / len(values))
        if scale == 0:
            raise ValueError("constant feature: " + feature)
        state[feature] = (mean, scale)
    return state

def scaled_profile(profile, state):
    return {feature: (profile[feature] - mean) / scale
            for feature, (mean, scale) in state.items()}

warehouses = [{"backlog": 800, "handoff_minutes": 4},
              {"backlog": 1200, "handoff_minutes": 8},
              {"backlog": 1600, "handoff_minutes": 12}]
scale = fit_numeric_scale(warehouses, ("backlog", "handoff_minutes"))
middle = scaled_profile(warehouses[1], scale)
assert abs(middle["backlog"]) < 1e-12
assert abs(middle["handoff_minutes"]) < 1e-12''',
    'For N profiles and P features, fitting means and scales costs O(N × P) time and O(P) fitted-state space; the displayed value lists use O(N) temporary space per feature. Distance calculations add their own cluster-specific cost.',
    ['Do not cluster mixed-unit columns without a justified distance rule.', 'Do not encode categories as arbitrary numeric distances.', 'Do not refit the scaler independently for each production batch.'],
    ['machine-learning/k-means-objective-and-restart-stability','machine-learning/principal-components-and-variance-retention','machine-learning/leakage-safe-preprocessing-pipeline','machine-learning/segmentation-and-model-selection-project'])

add('k-means-objective-and-restart-stability',
    'K-means objective and restart stability',
    'K-means assigns each point to its nearest centroid and updates centroids to reduce within-cluster squared distance, but its result depends on scale, initialization and the chosen cluster count.', [
    ('State the object being minimized', 'For warehouse profiles represented as scaled numeric vectors, k-means seeks K centroids minimizing the sum of squared distances from each profile to its assigned centroid. The teaching implementation alternates assignment and centroid updates for a tiny two-dimensional cohort. It does not select K automatically. A smaller inertia at larger K is expected; by itself it is not evidence that more segments are operationally useful. [[machine-learning/distance-scaling-before-clustering|Scaling]] defines the distance first.'),
    ('Handle initialization and empty groups', 'Different starting centroids can settle at different local solutions. Repeat fits with distinct initializations and compare inertia and membership, not just one run. If no point is assigned to a centroid, the update is undefined; the code stops rather than silently retaining an empty group. Production libraries may use explicit reinitialization strategies. Keep the chosen seed and initial centroids in a reproducible analysis record.'),
    ('Inspect cluster support and meaning', 'A one-warehouse cluster may identify a genuine exceptional site or a measurement error. Review feature distributions, site size and incident logs before giving it a business label. The cluster number is merely an index; relabeling across runs does not imply instability if the same sites remain grouped. Compare partitions by membership or a label-invariant score. [[machine-learning/segmentation-and-model-selection-project|The applied audit]] treats actionability separately from fit.'),
    ('Know when the shape assumption fails', 'Centroid distance favors roughly compact groups under the chosen metric and can split one elongated operational pattern into several segments. Dense pockets separated by noise may call for a density-based method. High-dimensional sparse representations can also make Euclidean distance less informative. This page deliberately focuses on the objective and checks; it does not claim K-means is the default answer for every unlabeled dataset.'),
    ('Do not turn a cluster into a causal claim', 'If high-backlog warehouses form one group and have more delays, the cluster does not show that backlog caused the delays. A downstream staffing policy needs evaluation against a baseline and an allocation constraint. If cluster IDs become predictive features, fit the scaler and centroids only on training rows within the validation fold. [[machine-learning/group-and-time-validation|The split lesson]] still applies.')],
    '''def squared_distance(profile, centroid):
    return sum((left - right) ** 2 for left, right in zip(profile, centroid))

def fit_small_kmeans(profiles, initial_centroids, iterations=20):
    if not profiles or not initial_centroids or iterations <= 0:
        raise ValueError("profiles, centroids and iterations required")
    width = len(profiles[0])
    if width == 0 or any(len(profile) != width for profile in profiles):
        raise ValueError("inconsistent profile width")
    if any(len(centroid) != width for centroid in initial_centroids):
        raise ValueError("inconsistent centroid width")
    centroids = [tuple(centroid) for centroid in initial_centroids]
    for _ in range(iterations):
        assignments = [min(range(len(centroids)),
                           key=lambda index: squared_distance(profile, centroids[index]))
                       for profile in profiles]
        groups = [[profile for profile, assigned in zip(profiles, assignments)
                   if assigned == index] for index in range(len(centroids))]
        if any(not group for group in groups):
            raise ValueError("empty cluster")
        updated = [tuple(sum(profile[column] for profile in group) / len(group)
                         for column in range(width)) for group in groups]
        if updated == centroids:
            break
        centroids = updated
    inertia = sum(squared_distance(profile, centroids[assigned])
                  for profile, assigned in zip(profiles, assignments))
    return centroids, assignments, inertia

warehouses = [(1.0, 1.0), (1.2, .9), (8.0, 8.0), (8.2, 7.8)]
centroids, membership, inertia = fit_small_kmeans(
    warehouses, [(1.0, 1.0), (8.0, 8.0)])
assert membership == [0, 0, 1, 1]
assert inertia > 0''',
    'With I iterations, N profiles, K centroids and P dimensions, the direct assignment step is O(I × N × K × P) time; group construction uses O(N × P) space. Multiple restarts multiply the fitting cost.',
    ['Do not compare inertia across different K as if lower automatically means better.', 'Do not ignore empty clusters or single-site segments.', 'Do not fit centroids on validation rows when cluster IDs feed a predictive model.'],
    ['machine-learning/distance-scaling-before-clustering','machine-learning/principal-components-and-variance-retention','machine-learning/permutation-importance-on-held-out-data','machine-learning/segmentation-and-model-selection-project'])

add('principal-components-and-variance-retention',
    'Principal components and variance retention',
    'Principal component analysis rotates centered numeric features toward directions of greatest variance, then projects records onto selected directions without using outcome labels.', [
    ('Center and scale before rotating', 'A warehouse dataset has backlog and handoff duration. PCA on raw columns can point almost entirely toward whichever column has larger units. Define the feature set and a training-only scaling policy first. Fit PCA on the same permitted training cohort, then apply its fixed center, scale and axes to later records. The first axis maximizes variance under that transformed geometry, not business value. [[machine-learning/distance-scaling-before-clustering|Distance scaling]] explains the unit choice.'),
    ('Read a component as a weighted direction', 'The code computes the leading direction of a two-feature covariance matrix through repeated multiplication and normalization. Its projection is a score along that direction; reversing the sign of the direction reverses all scores without changing the represented subspace. Do not label a component "operational quality" from the sign alone. Inspect feature loadings and the source records before assigning an interpretation.'),
    ('Choose dimensions by downstream purpose', 'Retaining 92% of training variance means the selected components reconstruct much of the scaled input variation. It does not guarantee preservation of a rare predictive signal or small-group structure. A low-variance feature can be essential to detect costly incidents. Compare downstream holdout performance or reconstruction error under the intended use, with PCA fitted inside each development fold. [[machine-learning/hyperparameter-search-and-untouched-test|Model selection]] handles the final test boundary.'),
    ('Watch missing values and drift', 'PCA requires a declared missing-value policy. Filling future records from statistics fitted on future batches changes the projection over time. If warehouse processes shift, old components may no longer summarize the same pattern; monitor transformed feature distributions and reconstruction error. A visually pleasing two-dimensional scatter is not proof of natural clusters. [[machine-learning/k-means-objective-and-restart-stability|K-means]] asks a separate partition question.'),
    ('Use a numerically sound solver in larger work', 'The short power-iteration example makes the leading-axis idea inspectable for two features. It does not implement a full PCA decomposition or handle nearly equal eigenvalues with careful numerical diagnostics. Use a tested linear algebra implementation for high-dimensional or sparse data, and store feature order and fitted transform with any downstream model. [[machine-learning/segmentation-and-model-selection-project|The project]] audits what the projection is used for.')],
    '''from math import sqrt

def leading_axis_two_features(training_profiles, iterations=40):
    if len(training_profiles) < 3 or any(len(profile) != 2 for profile in training_profiles):
        raise ValueError("at least three two-feature profiles required")
    means = tuple(sum(profile[column] for profile in training_profiles) /
                  len(training_profiles) for column in range(2))
    centered = [(left - means[0], right - means[1])
                for left, right in training_profiles]
    covariance = [
        [sum(left * left for left, _ in centered),
         sum(left * right for left, right in centered)],
        [sum(left * right for left, right in centered),
         sum(right * right for _, right in centered)],
    ]
    axis = (1.0, 1.0)
    for _ in range(iterations):
        rotated = (covariance[0][0] * axis[0] + covariance[0][1] * axis[1],
                   covariance[1][0] * axis[0] + covariance[1][1] * axis[1])
        length = sqrt(rotated[0] ** 2 + rotated[1] ** 2)
        if length == 0:
            raise ValueError("no variance in the training profiles")
        axis = (rotated[0] / length, rotated[1] / length)
    return means, axis

profiles = [(1.0, 2.0), (2.0, 3.0), (3.0, 5.0), (4.0, 6.0)]
means, axis = leading_axis_two_features(profiles)
scores = [sum((value - mean) * direction
              for value, mean, direction in zip(profile, means, axis))
          for profile in profiles]
assert abs(sum(scores)) < 1e-10
assert abs(sum(direction ** 2 for direction in axis) - 1) < 1e-10''',
    'For N two-feature profiles and I power iterations, this teaching fit is O(N + I) time and O(N) space. General PCA cost depends on N, feature count and solver; projection of M new records onto D retained components costs O(M × P × D).',
    ['Do not infer predictive value from explained variance alone.', 'Do not refit PCA on later evaluation records.', 'Do not interpret the arbitrary sign of a component as a fixed business direction.'],
    ['machine-learning/distance-scaling-before-clustering','machine-learning/k-means-objective-and-restart-stability','machine-learning/hyperparameter-search-and-untouched-test','machine-learning/segmentation-and-model-selection-project'])

add('segmentation-and-model-selection-project',
    'Project: select a model and audit warehouse segments',
    'Prepare one predictive model-selection record and one unsupervised warehouse-segmentation record with frozen data boundaries, fitted transforms and action tests.', [
    ('Frame two outputs', 'The predictive output estimates clearance hours at first sorting scan. The unsupervised output groups warehouses by predeclared backlog and handoff features to inform a staffing discussion. A prediction can be scored against future clearance hours; a cluster has no ground-truth label by default. Keep separate success criteria, partitions and release claims. [[machine-learning/hyperparameter-search-and-untouched-test|Model selection]] defines the predictive test boundary.'),
    ('Select and inspect the predictive model', 'Compare a training-only baseline with candidate ridge settings on time-aware development folds. Fit each scaler inside its fold, choose a penalty and freeze the resulting pipeline. Inspect future MAE and costly underestimates. If the final model performs poorly, do not tune against the final test and report it as untouched. Use a development holdout for permutation importance and record correlated-feature caveats. [[machine-learning/permutation-importance-on-held-out-data|Feature inspection]] has a narrower meaning than causality.'),
    ('Build and challenge the segments', 'Specify numeric features and scaling, then fit K-means with declared K values and multiple initializations. Report inertia, membership stability, smallest cluster support and site profiles. Fit PCA only as a diagnostic projection or a separately tested transformation; do not choose clusters solely because a two-dimensional plot looks tidy. [[machine-learning/distance-scaling-before-clustering|Scale choice]], [[machine-learning/k-means-objective-and-restart-stability|centroid fitting]] and [[machine-learning/principal-components-and-variance-retention|PCA]] are distinct decisions.'),
    ('Demand an operational test', 'A segment label is useful only if it changes a staffing or routing decision that can be evaluated. Compare the proposed segment-based action to the current policy on a later period or a controlled rollout, accounting for capacity. Avoid naming one cluster "bad warehouses" from a correlation with delays. Store feature definitions and centroid version so a later scoring run means the same thing.'),
    ('Deliver a reviewable packet', 'The code checks for evidence artifacts, not model quality. Include the fold plan, all candidate scores, final test record, feature-importance protocol, scale manifest, cluster restarts, PCA purpose and intended action. If the scale was fitted on future sites or test outcomes influenced model selection, stop and rebuild the evaluation. [[machine-learning/leakage-safe-preprocessing-pipeline|The pipeline lesson]] covers that failure.')],
    '''def selection_and_segment_gate(packet):
    required = {"fold_calendar", "candidate_scores", "final_test_record",
                "training_transform_manifest", "permutation_protocol",
                "segment_features", "cluster_restarts", "pca_purpose",
                "staffing_action"}
    missing = sorted(required - set(packet))
    if missing:
        raise ValueError("missing review evidence: " + ", ".join(missing))
    if not packet["candidate_scores"] or not packet["cluster_restarts"]:
        raise ValueError("selection or segment evidence absent")
    if packet["final_test_record"]["shipments"] <= 0:
        raise ValueError("empty final test")
    return {"packet_complete": True,
            "candidates": len(packet["candidate_scores"]),
            "restarts": len(packet["cluster_restarts"])}

packet = {"fold_calendar": ["spring", "summer", "autumn"],
          "candidate_scores": {0: 3.5, 20: 3.1, 80: 3.2},
          "final_test_record": {"shipments": 57, "mae": 3.3},
          "training_transform_manifest": "warehouse-scale-v2",
          "permutation_protocol": "development holdout, three seeds",
          "segment_features": ["backlog", "handoff_minutes"],
          "cluster_restarts": [23, 47, 61],
          "pca_purpose": "diagnostic projection only",
          "staffing_action": "compare shift allocation against current roster"}
review = selection_and_segment_gate(packet)
assert review == {"packet_complete": True, "candidates": 3,
                  "restarts": 3}''',
    'The artifact gate is O(A) expected time for A packet keys and O(A) sorting space for missing keys. Candidate fitting, repeated clustering, site review and the staffing evaluation are the substantial costs.',
    ['Do not call cluster membership a validated outcome label.', 'Do not tune the predictive model on the final future test.', 'Do not fit scaling or PCA on later sites while claiming a frozen transform.'],
    ['machine-learning/hyperparameter-search-and-untouched-test','machine-learning/permutation-importance-on-held-out-data','machine-learning/distance-scaling-before-clustering','machine-learning/k-means-objective-and-restart-stability','machine-learning/principal-components-and-variance-retention'])

publish_batch(
    lessons,
    module_title='Selection, inspection and unsupervised structure',
    module_summary='Keep the final test untouched, inspect feature reliance and evaluate distance-based segments under a frozen transform.',
    project_heading='Model selection and warehouse segmentation review',
    crosslinks=[
        ('machine-learning/ridge-regularization-with-training-only-scaling', lessons[0]['path']),
        ('machine-learning/prediction-time-feature-availability', lessons[1]['path']),
        ('machine-learning/leakage-safe-preprocessing-pipeline', lessons[2]['path']),
        ('machine-learning/decision-tree-splits-and-leaf-support', lessons[3]['path']),
        ('machine-learning/vector-vs-raster-in-machine-learning', lessons[4]['path']),
        ('machine-learning/shipment-delay-model-review-project', lessons[5]['path']),
    ],
    sort_start=14200,
)
