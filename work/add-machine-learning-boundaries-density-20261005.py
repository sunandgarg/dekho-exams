"""Add original classification-boundary and density-clustering lessons."""
from ml_fixture_writer_20261005 import publish_batch

lessons = []


def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='machine-learning/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))


add('logistic-regression-log-loss-and-odds',
    'Logistic regression, log loss and odds',
    'Binary logistic regression maps a linear feature score to a probability and fits its coefficients by reducing log loss on labeled training rows.', [
    ('Name the event before fitting', 'A dispatch team predicts whether a shipment will miss its handoff window. The positive class is a missed handoff, defined using a fixed outcome clock; backlog measured at intake is one possible predictor. Logistic regression models log odds as an intercept plus weighted features, then turns that score into a value between zero and one. It is a classification model despite its name. [[machine-learning/prediction-time-feature-availability|Feature timing]] determines whether the score can be served.'),
    ('Use log loss to train the probability score', 'For a labeled row, log loss rises sharply when the model assigns tiny probability to an event that occurs. The code implements a one-feature batch gradient step and checks that the fitted probability rises with backlog. It keeps the calculation inspectable, but lacks a convergence check, a production optimizer, missing-value handling and regularization. Use a tested solver for deployed multi-feature models, especially when classes are rare or predictors are correlated.'),
    ('Interpret odds without overclaiming', 'A one-unit feature increase adds its coefficient to the log odds, holding the other modeled inputs fixed. Exponentiating that coefficient gives a modeled odds multiplier, not a causal effect. If backlog and staffing policy respond to each other, the coefficient can shift when the data window changes. Scale features using training rows only, store the fitted transform, and evaluate errors by site. [[machine-learning/leakage-safe-preprocessing-pipeline|The preprocessing guide]] covers that state.'),
    ('Separate ranking, calibration and action', 'A classifier can rank missed handoffs well while its probabilities are too high for a cost calculation. Check [[machine-learning/probability-calibration|calibration]] on independent rows before interpreting 0.7 as a frequency. Then choose a decision threshold from false-alarm and missed-handoff costs; the optimizer does not learn that operational threshold automatically. [[machine-learning/decision-threshold-and-cost|The threshold lesson]] shows the separate decision layer.'),
    ('Test against real alternatives', 'Compare a training-rate constant, constrained tree and linear logistic model on the same later period. Report prevalence, precision, recall, log loss and calibration support. A good average log loss may hide a failure at a small warehouse or during overnight intake. [[machine-learning/rare-event-precision-recall-and-prevalence|Rare-event metrics]] make the class mix visible. Freeze the later test before selecting feature transforms or penalty strength.')],
    '''from math import exp, log

training_backlogs = [0.2, 0.5, 0.9, 1.2, 1.6, 2.0, 2.4, 2.8]
missed_handoff = [0, 0, 0, 0, 1, 0, 1, 1]

def probability(score):
    if score >= 0:
        return 1 / (1 + exp(-score))
    scaled = exp(score)
    return scaled / (1 + scaled)

def log_loss(backlogs, labels, intercept, slope):
    terms = []
    for backlog, label in zip(backlogs, labels):
        chance = min(max(probability(intercept + slope * backlog), 1e-12), 1 - 1e-12)
        terms.append(-label * log(chance) - (1 - label) * log(1 - chance))
    return sum(terms) / len(terms)

intercept, slope = 0.0, 0.0
initial_loss = log_loss(training_backlogs, missed_handoff, intercept, slope)
for _ in range(1200):
    residuals = [probability(intercept + slope * backlog) - label
                 for backlog, label in zip(training_backlogs, missed_handoff)]
    intercept -= 0.08 * sum(residuals) / len(residuals)
    slope -= 0.08 * sum(backlog * residual for backlog, residual
                        in zip(training_backlogs, residuals)) / len(residuals)

assert log_loss(training_backlogs, missed_handoff, intercept, slope) < initial_loss
assert probability(intercept + slope * 0.5) < probability(intercept + slope * 2.5)''',
    'For I full-batch iterations, N rows and F features, direct gradient updates take O(INF) time and O(N + F) working memory if residuals are retained. Serving one score is O(F). Reliable solvers add convergence controls and may have different costs for sparse or high-dimensional inputs.',
    ['Do not treat a fitted coefficient as a causal effect.', 'Do not use the classification threshold as a substitute for calibration.', 'Do not fit scaling or select penalties on the final test period.'],
    ['machine-learning/linear-margin-classifiers-and-hinge-loss','machine-learning/rare-event-precision-recall-and-prevalence','machine-learning/probability-calibration','machine-learning/classification-and-segmentation-review-project'])


add('linear-margin-classifiers-and-hinge-loss',
    'Linear margin classifiers and hinge loss',
    'A linear margin classifier seeks a separating score with a buffer around the boundary, penalizing examples that fall inside that buffer or on the wrong side.', [
    ('Distinguish a margin from a probability', 'A missed-handoff model may output a signed score: positive for predicted miss, negative otherwise. The hinge penalty for a labeled row is the amount by which its signed margin falls below one, floored at zero. This encourages a gap around the boundary. The raw score is not a calibrated chance of failure. [[machine-learning/logistic-regression-log-loss-and-odds|Logistic regression]] optimizes a different loss and yields probabilities that still require calibration checks.'),
    ('Balance the buffer against violations', 'A soft-margin linear classifier combines hinge loss with a penalty on weight size. Stronger weight regularization allows more margin violations but may improve stability under noisy labels. An overly weak penalty can follow mislabeled outliers. The example uses a one-dimensional batch subgradient with fixed training-scale inputs; a production solver needs convergence diagnostics and an explicit feature-scaling pipeline. [[machine-learning/leakage-safe-preprocessing-pipeline|Fit scaling]] on each training fold.'),
    ('Inspect cases closest to the boundary', 'Rows beyond the margin do not contribute to the hinge term; rows inside or across it do. A support-vector implementation exploits this geometry, though the simple code updates against every row. Investigate borderline shipments for inconsistent target timestamps, mixed sites and missing features. A boundary can move sharply when a rare site has only a handful of labels. [[machine-learning/rare-event-precision-recall-and-prevalence|Prevalence and recall]] still matter after the margin is fitted.'),
    ('Evaluate the operational policy separately', 'Choose a score cutoff against a development cohort according to review capacity and missed-handoff cost. If downstream dispatch needs a numeric probability, calibrate the score using disjoint data; do not label the score itself as 80-percent confidence. For a new site or future month, report ranking and decision metrics separately. [[machine-learning/decision-threshold-and-cost|The decision-policy lesson]] provides the cost calculation.'),
    ('Know when to switch model family', 'A linear boundary may be too simple when backlog interacts strongly with shift staffing or route mix. Add only features available at scoring time, then compare with a constrained tree or forest. Kernels can create nonlinear boundaries but add fitting, memory and serving costs. Use [[machine-learning/hyperparameter-search-and-untouched-test|development-only selection]] and leave the final future test sealed.')],
    '''training_rows = [(-2.0, -1), (-1.3, -1), (-0.8, -1),
                 (0.6, 1), (1.1, 1), (1.8, 1)]
weight, intercept = 0.0, 0.0
weight_penalty = 0.04
learning_rate = 0.12

def objective(rows, fitted_weight, fitted_intercept):
    hinge = sum(max(0.0, 1 - label * (fitted_weight * backlog + fitted_intercept))
                for backlog, label in rows) / len(rows)
    return hinge + weight_penalty * fitted_weight ** 2 / 2

initial_objective = objective(training_rows, weight, intercept)
for _ in range(500):
    violations = [(backlog, label) for backlog, label in training_rows
                  if label * (weight * backlog + intercept) < 1]
    gradient_weight = weight_penalty * weight - sum(
        label * backlog for backlog, label in violations) / len(training_rows)
    gradient_intercept = -sum(label for _, label in violations) / len(training_rows)
    weight -= learning_rate * gradient_weight
    intercept -= learning_rate * gradient_intercept

assert objective(training_rows, weight, intercept) < initial_objective
assert all(label * (weight * backlog + intercept) > 0
           for backlog, label in training_rows)''',
    'The dense full-batch teaching loop takes O(INF) time over I iterations, N rows and F features, with O(F) model storage. A kernel classifier can retain many training cases and become much more expensive to train and serve. Measure actual latency before choosing it over a linear or tree model.',
    ['Do not interpret a margin score as a probability.', 'Do not scale validation or serving features with new fitted statistics.', 'Do not select the margin penalty using the final test labels.'],
    ['machine-learning/logistic-regression-log-loss-and-odds','machine-learning/decision-threshold-and-cost','machine-learning/decision-tree-splits-and-leaf-support','machine-learning/classification-and-segmentation-review-project'])


add('dbscan-core-border-and-noise-points',
    'DBSCAN core, border and noise points',
    'DBSCAN expands clusters from points with enough neighbors inside a chosen radius and leaves unsupported points labeled as noise.', [
    ('Define density in the scaled feature space', 'A warehouse planner compares sites using intake volume and late-scan rate. After fitting the feature transformation on an allowed reference period, choose a distance, radius and minimum-neighbor count. A core site has at least that count inside its radius, including itself in this implementation. A border site is close to a core site without meeting the count on its own; a noise site is not reached. [[machine-learning/distance-scaling-before-clustering|Scaling]] changes what a radius means.'),
    ('Expand only from core sites', 'Starting at a core site, collect its neighbors. Every newly reached core site adds its neighbors, so a cluster can follow a non-round region. A border site can join a cluster but does not expand it further. The code computes all neighborhoods first and then performs this expansion. It marks an isolated warehouse as noise, rather than forcing it into the nearest cluster. [[machine-learning/k-means-objective-and-restart-stability|K-means]] makes a different assignment choice.'),
    ('Treat parameter choice as part of the finding', 'A small radius can mark most sites noise; a large radius may join unrelated populations. Raising the minimum count can erase a legitimate small operating regime. Inspect cluster support and rerun over a defensible parameter range. If memberships change with a slight radius adjustment, report that instability. Do not set the radius solely to produce a desired number of named business segments.'),
    ('Separate unusual from defective', 'Noise is a geometric label, not a fraud or data-quality verdict. An isolated warehouse might serve a distinct geography, have a broken scan feed or represent a new process worth preserving. Review raw records, measurement units and operational context. For high-dimensional data, distances can concentrate, making one global radius hard to interpret. [[machine-learning/principal-components-and-variance-retention|A projection]] may aid inspection but can also hide useful separation.'),
    ('Plan the assignment contract', 'Classic DBSCAN defines clusters on the fitted sample; assigning a new site requires an explicit policy such as checking core neighborhoods under the frozen scaling and radius. Do not quietly refit all sites each day and assume cluster IDs remain stable. Keep the feature schema, radius and fitted reference data version. [[machine-learning/classification-and-segmentation-review-project|The applied review]] tests whether any resulting segment changes a real decision.')],
    '''from math import dist

warehouse_profiles = [(0.0, 0.0), (0.4, 0.3), (0.8, 0.1),
                      (8.0, 8.0), (8.3, 8.2), (8.7, 8.1),
                      (20.0, 3.0)]
radius = 1.0
minimum_neighbors = 3
neighbors = [[other for other, candidate in enumerate(warehouse_profiles)
              if dist(profile, candidate) <= radius]
             for profile in warehouse_profiles]
core = {index for index, nearby in enumerate(neighbors)
        if len(nearby) >= minimum_neighbors}
labels = [None] * len(warehouse_profiles)
cluster_id = 0

for start in range(len(warehouse_profiles)):
    if labels[start] is not None:
        continue
    if start not in core:
        labels[start] = -1
        continue
    queue = [start]
    queued = {start}
    while queue:
        current = queue.pop()
        labels[current] = cluster_id
        if current in core:
            for nearby in neighbors[current]:
                if labels[nearby] is None or labels[nearby] == -1:
                    if nearby not in queued:
                        queue.append(nearby)
                        queued.add(nearby)
    cluster_id += 1

assert cluster_id == 2
assert labels[-1] == -1
assert labels[:3] == [0, 0, 0]
assert labels[3:6] == [1, 1, 1]''',
    'The direct all-pairs neighborhood construction takes O(N²F) time and O(N²) memory for N sites with F features; expansion follows the stored neighbor graph. Spatial indexing can help some distance settings, while dense neighborhoods may still require substantial memory. Do not silently scale this teaching implementation to millions of rows.',
    ['Do not interpret noise as confirmed bad data or misconduct.', 'Do not fit the scale or tune radius using future outcome labels.', 'Do not assume cluster numeric IDs are stable across refits.'],
    ['machine-learning/agglomerative-linkage-and-cluster-cuts','machine-learning/distance-scaling-before-clustering','machine-learning/k-means-objective-and-restart-stability','machine-learning/classification-and-segmentation-review-project'])


add('agglomerative-linkage-and-cluster-cuts',
    'Agglomerative linkage and cluster cuts',
    'Agglomerative clustering starts with one cluster per observation and repeatedly joins the closest pair under a declared linkage rule.', [
    ('Linkage answers what closest means', 'A planner groups warehouse profiles after scaling intake volume and delay rate. Single linkage uses the closest cross-cluster pair and can chain through narrow bridges; complete linkage uses the farthest cross-cluster pair, favoring compact groups. Average linkage uses an average. Ward-style linkage instead follows a variance objective and has its own distance assumptions. The code implements complete linkage only, so its merges should not be described as Ward merges.'),
    ('Read the merge history before choosing a cut', 'A hierarchy records which groups joined and at what distance. Cutting it at two groups is a decision that changes the final segmentation, not a property that the data announced. The example stops at two clusters and checks two clearly separated operating groups. On real data, inspect the jump in merge distances, support counts and operational interpretability; the same numerical cut may behave differently after adding a new site.'),
    ('Check the distance contract', 'If volume has a much larger numeric range than late-scan rate, Euclidean distance can largely ignore the rate. Fit scaling on the reference cohort and preserve that transform when comparing future sites. Missing measurements need a defined policy before distance is computed. [[machine-learning/distance-scaling-before-clustering|The scaling guide]] covers this, while [[machine-learning/principal-components-and-variance-retention|PCA]] explains a possible but lossy projection.'),
    ('Compare stability with other cluster ideas', 'A long chain of sites might become one group under single linkage but split under complete linkage. [[machine-learning/dbscan-core-border-and-noise-points|DBSCAN]] can leave sparse sites unassigned; agglomerative clustering will eventually merge every site if allowed to run to one group. [[machine-learning/k-means-objective-and-restart-stability|K-means]] optimizes a center-based objective. Compare memberships under reasonable distances and linkage settings, not just one summary score.'),
    ('Do not turn a grouping into a causal story', 'A cluster of high-volume sites may appear to have worse handoff rates because the sites serve different routes or use different clocks. The grouping describes the selected features. It does not show that changing a site’s cluster label would change its outcome. Review measurement quality and any proposed staffing rule separately. [[machine-learning/classification-and-segmentation-review-project|The project]] asks for an action test and a no-action option.')],
    '''from math import dist

warehouse_profiles = [(1.0, 1.1), (1.3, 0.9), (0.8, 1.4),
                      (7.8, 8.0), (8.1, 8.4), (8.5, 7.7)]
distances = {(left, right): dist(warehouse_profiles[left], warehouse_profiles[right])
             for left in range(len(warehouse_profiles))
             for right in range(left + 1, len(warehouse_profiles))}

def point_distance(left, right):
    return distances[(min(left, right), max(left, right))]

def complete_linkage(first, second):
    return max(point_distance(left, right)
               for left in first for right in second)

clusters = [frozenset([index]) for index in range(len(warehouse_profiles))]
merge_distances = []
while len(clusters) > 2:
    options = [(complete_linkage(clusters[left], clusters[right]), left, right)
               for left in range(len(clusters))
               for right in range(left + 1, len(clusters))]
    distance, left, right = min(options)
    merge_distances.append(distance)
    joined = clusters[left] | clusters[right]
    clusters = [group for index, group in enumerate(clusters)
                if index not in (left, right)] + [joined]

assert set(clusters) == {frozenset({0, 1, 2}), frozenset({3, 4, 5})}
assert len(merge_distances) == 4''',
    'The distance matrix takes O(N²F) time and O(N²) memory. This direct merge search revisits interpoint distances over O(N) rounds, costing up to O(N³) time. Use a tested clustering implementation and measure memory before applying full hierarchical methods to large cohorts.',
    ['Do not call complete linkage Ward linkage.', 'Do not treat a two-group cut as an inherent truth about the sites.', 'Do not infer an operational effect from cluster membership alone.'],
    ['machine-learning/dbscan-core-border-and-noise-points','machine-learning/distance-scaling-before-clustering','machine-learning/k-means-objective-and-restart-stability','machine-learning/classification-and-segmentation-review-project'])


add('classification-and-segmentation-review-project',
    'Classification and warehouse segmentation review project',
    'Prepare a handoff-risk classifier and an independent warehouse-segmentation audit with separate data boundaries, evaluation claims and operational actions.', [
    ('Write two questions, not one vague model goal', 'The supervised task predicts a missed handoff at intake so dispatch can intervene. The unsupervised task asks whether warehouse profiles form stable operating groups worth investigating. They need different evidence. The classifier has labeled future outcomes, costs and a threshold. Clusters have distance, scale, membership stability and a proposed action test, but no automatic notion of accuracy. [[machine-learning/logistic-regression-log-loss-and-odds|The logistic model]] and [[machine-learning/dbscan-core-border-and-noise-points|density clusters]] start these separate threads.'),
    ('Freeze both information boundaries', 'Partition shipment records by site and time for classification, fit all transforms within training folds, and score an untouched later cohort once. For segmentation, define the reference sites and features before inspecting business outcomes used to judge actionability. A site’s future delay rate must not enter its historical cluster features. Record feature availability at the decision clock. [[machine-learning/group-and-time-validation|The split guide]] and [[machine-learning/prediction-time-feature-availability|feature guide]] address the supervised boundary.'),
    ('Compare models and decisions', 'Fit a training-rate baseline, logistic model, linear margin model and constrained tree. Select settings within development data, then compare precision, recall, log loss where probabilities exist, calibration and review workload on the same later cases. A margin score requires separate calibration before probability-based costing. [[machine-learning/linear-margin-classifiers-and-hinge-loss|The margin lesson]] makes that distinction. The final action threshold follows explicit false-alarm and missed-handoff costs.'),
    ('Stress-test the segmentation', 'Compare scaled k-means, complete-linkage groups and DBSCAN over a declared range of reasonable parameters. Report unassigned DBSCAN sites, membership changes, cluster support and whether a segment label changes a staffing decision that can be tested prospectively. If the grouping collapses after a minor scaling change or lacks a specific action, keep it exploratory. Do not force every warehouse into a named segment merely to populate a dashboard.'),
    ('Approve only a bounded pilot', 'The code checks whether the review packet has minimum evidence before a pilot discussion; its boolean fields need human-audited records behind them. Include model version, preprocessing state, inference p95, label maturity, owner, rollback and a monitored pilot period. A failed check holds the pilot without claiming the idea is worthless. [[machine-learning/feature-drift-and-delayed-label-monitoring|Monitoring]] and [[machine-learning/ensemble-release-review-project|release review]] give the follow-through.')],
    '''def pilot_readiness(packet):
    required = {
        "future_labels_sealed": "future evaluation",
        "training_only_transforms": "fitted transforms",
        "classifier_calibration_checked": "probability calibration",
        "threshold_costed": "decision cost",
        "cluster_stability_checked": "segment stability",
        "segment_action_defined": "segment action",
        "monitoring_and_rollback_ready": "operations",
    }
    missing = [label for key, label in required.items() if not packet.get(key)]
    return "pilot review" if not missing else "hold: " + ", ".join(missing)

warehouse_packet = {
    "future_labels_sealed": True,
    "training_only_transforms": True,
    "classifier_calibration_checked": False,
    "threshold_costed": True,
    "cluster_stability_checked": True,
    "segment_action_defined": False,
    "monitoring_and_rollback_ready": True,
}
assert pilot_readiness(warehouse_packet) == (
    "hold: probability calibration, segment action"
)''',
    'For N shipment predictions and F linear features, one scoring pass is O(NF), while cluster comparisons can require O(S²) distance memory for S sites. The packet check is O(K) for K review requirements; it does not measure inference latency, clustering stability or policy value by itself.',
    ['Do not evaluate a classifier and an unlabeled clustering with one accuracy number.', 'Do not treat a margin score as a calibrated probability.', 'Do not give an unstable cluster a business label without an action test.'],
    ['machine-learning/logistic-regression-log-loss-and-odds','machine-learning/linear-margin-classifiers-and-hinge-loss','machine-learning/dbscan-core-border-and-noise-points','machine-learning/agglomerative-linkage-and-cluster-cuts','machine-learning/distance-scaling-before-clustering','machine-learning/ensemble-release-review-project'])


publish_batch(
    lessons,
    module_title='Classification boundaries and density structure',
    module_summary='Logistic loss, margin classifiers, density clusters and hierarchical linkage with separate evaluation contracts.',
    project_heading='Classification and segmentation review',
    crosslinks=[
        ('machine-learning/rare-event-precision-recall-and-prevalence', lessons[0]['path']),
        ('machine-learning/decision-threshold-and-cost', lessons[1]['path']),
        ('machine-learning/distance-scaling-before-clustering', lessons[2]['path']),
        ('machine-learning/k-means-objective-and-restart-stability', lessons[3]['path']),
        ('machine-learning/segmentation-and-model-selection-project', lessons[4]['path']),
    ],
    sort_start=4800,
)
