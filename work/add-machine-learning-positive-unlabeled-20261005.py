"""Add original positive-unlabeled learning lessons and release review."""
from ml_fixture_writer_20261005 import publish_batch

lessons = []


def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='machine-learning/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))


add('positive-unlabeled-target-and-observation-state',
    'Positive–unlabeled target and observation state',
    'Positive–unlabeled learning distinguishes a true event from whether that event was confirmed; an unresolved record is not a verified negative.', [
    ('Separate truth from observation', 'A repair network records confirmed seal failures after an inspection. Many pumps have no failure ticket because the follow-up is incomplete or no technician has adjudicated the case. Let Y mean the true 37-day failure event and S mean a confirmed positive ticket. S equals one only when Y equals one; S equals zero can contain either truth value. A classifier trained with S as Y answers the ticket-confirmation question, not automatically the failure question.'),
    ('Fix the population and clock', 'Include pumps eligible for scoring at the same inspection decision. Store inspection time, observation cutoff and follow-up maturity. A pump with only 12 observed days cannot be declared free of a 37-day event. If the missing status comes from incomplete follow-up, a time-to-event formulation may be more appropriate than a generic PU classifier. [[data-science/right-censoring-and-time-to-event|Right censoring]] describes that case.'),
    ('Keep label provenance', 'Record how a positive was confirmed: workshop teardown, sensor alarm review, warranty claim or audit. These processes may select different kinds of failures. The selection method is an input to model validity, not just an annotation note. [[machine-learning/pu-selection-mechanism-and-scar-audit|Selection audit]] tests whether confirmed positives resemble all positives.'),
    ('Reserve an adjudicated test', 'Hold out later inspections and independently resolve a sampled set of their outcomes under a common rubric. Neither PU training nor the rule for selecting a threshold should use this test set. Report unresolved cases separately instead of silently assigning them zero. [[machine-learning/pu-evaluation-with-adjudicated-sample|Evaluation]] defines its denominators.'),
    ('State the operating action', 'The product may send the highest-risk pumps to manual review under a fixed capacity. The goal is to find failures without overwhelming technicians, not to maximize the number of predicted tickets. [[machine-learning/selective-prediction-and-review-capacity|Review capacity]] and [[machine-learning/positive-unlabeled-release-project|the project]] connect scores to actions.')],
    '''inspections = [
    {"asset": "seal-47", "confirmed_failure": True, "matured_days": 42},
    {"asset": "seal-62", "confirmed_failure": False, "matured_days": 41},
    {"asset": "seal-83", "confirmed_failure": False, "matured_days": 12},
]

def observation_state(record, horizon_days):
    if record["confirmed_failure"]:
        return "labeled-positive"
    if record["matured_days"] < horizon_days:
        return "unresolved-follow-up"
    return "unlabeled-mature"  # Still not an adjudicated negative.

states = [observation_state(record, 37) for record in inspections]
assert states == ["labeled-positive", "unlabeled-mature", "unresolved-follow-up"]
assert states.count("labeled-positive") == 1''',
    'State assignment costs O(N) time for N inspections and O(N) memory when retained. Mature follow-up does not prove absence if the capture system misses failures. Adjudication, provenance logging and outcome lag dominate the operational cost; the code checks the contract only.',
    ['Do not relabel every unconfirmed case as a true negative.', 'Do not confuse ticket prediction with failure prediction.', 'Do not ignore immature follow-up when defining the training population.'],
    ['machine-learning/pu-selection-mechanism-and-scar-audit','machine-learning/pu-class-prior-and-sensitivity','machine-learning/pu-nonnegative-risk-objective','machine-learning/pu-evaluation-with-adjudicated-sample'])


add('pu-selection-mechanism-and-scar-audit',
    'PU label selection: SCAR and site-dependent confirmation',
    'A PU correction based on constant positive-labeling probability requires selected positives to represent all positives; site-dependent confirmation can violate that assumption.', [
    ('Write the selection assumption', 'Under selected-completely-at-random labeling, every true positive has the same probability c of being confirmed, regardless of features. Then the probability of an observed positive at feature vector X is c times the probability of a true positive. This identity is useful only if confirmation does not depend on pump type, depot, severity or how easy a fault is to inspect.'),
    ('Look for selection gradients', 'A high-volume depot may teardown every returned pump while a small depot files tickets only for severe cases. Confirmed positives then overrepresent that depot and severity. Compare capture policies, inspection staffing, claim channels and known audit results by slice. The code audits confirmation fractions among a small set of independently adjudicated positives; it does not establish selection independence from every unobserved feature.'),
    ('Keep the denominator honest', 'A confirmation rate computed among all pumps is not c: it mixes true prevalence with selection. Estimating c requires information about true positives or a defensible model of the labeling process. If no such information exists, report a plausible range and the decisions that change across it. [[machine-learning/pu-class-prior-and-sensitivity|Sensitivity analysis]] makes that explicit.'),
    ('Use local selection when justified', 'A selected-at-random model may let confirmation probability vary with recorded depot or inspection pathway. That still assumes no remaining selection driver after conditioning. It needs support in each stratum and careful estimation; a zero-confirmation stratum cannot be repaired by a weight. [[machine-learning/covariate-shift-and-support-overlap|Support overlap]] states the adjacent identifiability issue.'),
    ('Do not confuse annotation with outcome', 'A false ticket, duplicate claim or delayed teardown can break the implication that S equals one means Y equals one. Audit a sample of confirmed positives before choosing a PU method. [[machine-learning/positive-unlabeled-target-and-observation-state|The observation contract]] must hold before any correction is meaningful.')],
    '''adjudicated_positives = [
    {"depot": "north-47", "confirmed": True},
    {"depot": "north-47", "confirmed": True},
    {"depot": "north-47", "confirmed": False},
    {"depot": "west-62", "confirmed": True},
    {"depot": "west-62", "confirmed": False},
    {"depot": "west-62", "confirmed": False},
]

def confirmation_by_depot(positives):
    counts = {}
    for record in positives:
        bucket = counts.setdefault(record["depot"], [0, 0])
        bucket[0] += bool(record["confirmed"])
        bucket[1] += 1
    return {depot: confirmed / total for depot, (confirmed, total) in counts.items()}

fractions = confirmation_by_depot(adjudicated_positives)
assert round(fractions["north-47"], 3) == 0.667
assert round(fractions["west-62"], 3) == 0.333
assert fractions["north-47"] != fractions["west-62"]''',
    'Grouping N independently adjudicated positives costs O(N) time and O(C) memory for C depots. The audit needs enough adjudicated positives per site; small denominators make apparent differences noisy. A fraction difference is a warning, not proof of the exact labeling mechanism.',
    ['Do not estimate positive confirmation probability from the fraction of all pumps with tickets.', 'Do not assume SCAR when work practices vary across depots.', 'Do not treat an observed site difference from tiny samples as a precise selection probability.'],
    ['machine-learning/positive-unlabeled-target-and-observation-state','machine-learning/pu-class-prior-and-sensitivity','machine-learning/pu-nonnegative-risk-objective','machine-learning/pu-evaluation-with-adjudicated-sample'])


add('pu-class-prior-and-sensitivity',
    'PU class prior and confirmation-rate sensitivity',
    'Positive prevalence and confirmation probability determine how observed ticket rates translate into true event risk under a stated selection model.', [
    ('Separate prevalence from capture', 'The observed positive-ticket fraction is not the true failure prevalence when some failures are never confirmed. Under constant capture c, observed rate equals true prevalence times c. If tickets cover 12 percent of eligible pumps and c is 0.6, the implied prevalence is 20 percent. This arithmetic is conditional on the selection model and matched population; it is not a way to discover c from tickets alone.'),
    ('Bound the plausible scenarios', 'Use independently adjudicated audits, process knowledge or a validated capture study to set a range for c. Apply each value to the same observed rate and inspect whether review capacity, threshold choice or site performance changes. The code evaluates three illustrative scenarios; none is presented as an estimated truth. [[machine-learning/pu-selection-mechanism-and-scar-audit|The SCAR audit]] explains why one c may fail by depot.'),
    ('Watch impossible combinations', 'If observed ticket rate exceeds an assumed c, dividing yields a prevalence above one; the assumption is incompatible with that population. Clipping the result to one hides the contradiction. Likewise, an observed score divided by c may exceed one because the fitted score or c is misspecified. Treat that as a model diagnostic, not merely a formatting issue.'),
    ('Avoid prior leakage', 'Do not choose prevalence from a later test period and feed it into earlier training without marking the data transfer. If failure prevalence shifts after a maintenance policy change, a historical prior may no longer apply. [[machine-learning/label-prior-shift-and-odds-adjustment|Prior shift]] addresses an adjacent deployed-model problem.'),
    ('Carry uncertainty into the decision', 'A release decision should show the range of expected review volume and missed failures across plausible c and prevalence values. If one plausible scenario violates the staffing limit, hold the automation or use a more conservative manual review path. [[machine-learning/positive-unlabeled-release-project|The project]] makes that gate explicit.')],
    '''observed_ticket_rate = 0.12
capture_scenarios = (0.45, 0.60, 0.75)

def implied_prevalence(observed_rate, capture_probability):
    if not 0 <= observed_rate <= 1 or not 0 < capture_probability <= 1:
        raise ValueError("valid rates required")
    if observed_rate > capture_probability:
        raise ValueError("observed rate exceeds assumed capture")
    return observed_rate / capture_probability

prevalence_scenarios = [implied_prevalence(observed_ticket_rate, capture)
                        for capture in capture_scenarios]
assert [round(value, 3) for value in prevalence_scenarios] == [0.267, 0.2, 0.16]
assert prevalence_scenarios[0] > prevalence_scenarios[-1]''',
    'Evaluating S capture scenarios costs O(S) time and O(S) storage. Obtaining defensible capture bounds is much costlier than the arithmetic because it needs outcome adjudication or a capture study. When the selection model fails, the range is not an uncertainty interval for truth.',
    ['Do not identify true prevalence from ticket rate alone.', 'Do not silently clip an impossible implied prevalence.', 'Do not reuse a future-period prior in an earlier training decision.'],
    ['machine-learning/positive-unlabeled-target-and-observation-state','machine-learning/pu-selection-mechanism-and-scar-audit','machine-learning/pu-nonnegative-risk-objective','machine-learning/pu-evaluation-with-adjudicated-sample'])


add('pu-nonnegative-risk-objective',
    'Nonnegative PU risk objective and its assumptions',
    'A PU risk objective can combine labeled positives and an unlabeled mixture using an assumed class prior, but a negative component below zero signals empirical overfitting or assumption failure.', [
    ('Decompose the binary risk', 'For an illustrative loss, the expected negative-class loss among unlabeled pumps includes both true negatives and hidden positives. Subtract the prior-weighted positive contribution to estimate negative risk. Add the prior-weighted positive loss for the full objective. This is an expectation identity under representative positive sampling and a correct prior; it is not a generic fix for selective tickets.'),
    ('Keep the negative estimate bounded', 'With flexible models and few labeled positives, the empirical difference can become negative even though true risk cannot. A nonnegative variant bounds that term below by zero. The code computes this arithmetic from declared aggregate losses, not neural gradients. The bound prevents one failure mode but does not make labels or prior correct.'),
    ('Compare against simple baselines', 'A ticket-versus-unlabeled classifier may be a useful ranking baseline, even if its raw probability targets confirmation rather than true failure. Compare a mature-label supervised subset, the simple baseline and the PU objective on the same independently adjudicated holdout. [[machine-learning/pu-evaluation-with-adjudicated-sample|Holdout evaluation]] separates model choice from ticket availability.'),
    ('Treat prior as a sensitivity parameter', 'A wrong positive prevalence changes the subtraction and the learned boundary. Train or evaluate a small grid of plausible priors and record how rankings and review volume move. Do not tune prior against the final test. [[machine-learning/pu-class-prior-and-sensitivity|Prior sensitivity]] defines the range.'),
    ('Budget the batch mixture', 'If a minibatch contains only a few positive examples, its risk estimate can fluctuate sharply. Track the number of unique confirmed failures and avoid repeated near-duplicates from one asset. [[machine-learning/group-and-time-validation|Identity-aware splits]] protect evaluation and prevent training batches from appearing more diverse than they are.')],
    '''def nonnegative_pu_risk(positive_loss_on_positives,
                            negative_loss_on_positives,
                            negative_loss_on_unlabeled,
                            positive_prior):
    if not 0 < positive_prior < 1:
        raise ValueError("class prior must be inside (0, 1)")
    positive_component = positive_prior * positive_loss_on_positives
    estimated_negative = (negative_loss_on_unlabeled
                          - positive_prior * negative_loss_on_positives)
    return positive_component + max(0.0, estimated_negative), estimated_negative

risk, raw_negative = nonnegative_pu_risk(0.38, 0.72, 0.19, 0.31)
assert round(raw_negative, 4) == -0.0332
assert round(risk, 4) == 0.1178
assert risk >= 0''',
    'This scalar audit is O(1). Training requires repeated positive and unlabeled batches plus model forward/backward passes; cost depends on model size and batch construction. The nonnegative clamp stabilizes an empirical component but cannot identify a class prior or correct biased positive selection.',
    ['Do not apply the decomposition when confirmed positives are an unexamined selective subset.', 'Do not infer the true prior from the same objective without additional assumptions.', 'Do not report training risk as held-out failure recall.'],
    ['machine-learning/positive-unlabeled-target-and-observation-state','machine-learning/pu-selection-mechanism-and-scar-audit','machine-learning/pu-class-prior-and-sensitivity','machine-learning/pu-evaluation-with-adjudicated-sample'])


add('pu-evaluation-with-adjudicated-sample',
    'Evaluate PU models with an adjudicated sample',
    'An independent adjudicated sample can measure true outcome errors; if it is stratified, its selection weights and denominators must be retained.', [
    ('Sample beyond easy positives', 'Review both confirmed-ticket and unresolved pumps from a later period under one failure rubric. Sample across model-score bands, depots, equipment families and observation maturity, including low-score cases. If only suspicious high-score pumps are adjudicated, the measured precision does not represent the deployment population. [[machine-learning/positive-unlabeled-target-and-observation-state|The target contract]] defines who was eligible.'),
    ('Log inclusion probabilities', 'A stratified audit may oversample high-risk pumps to find enough failures. Keep each sampled record’s chance of selection from its stratum. Weighted totals can recover population rates when every relevant stratum has positive inclusion probability. The code computes a toy weighted recall and states the verified-positive denominator explicitly; it is not an uncertainty interval.'),
    ('Choose the right metrics', 'At a fixed review capacity, measure verified failure recall, false review volume and precision against adjudicated truth. Break them out by depot and equipment age. Do not use ticket labels as test truth. If some outcomes remain unresolvable, report that fraction and bound or defer the metric instead of treating unresolved as negative. [[machine-learning/rare-event-precision-recall-and-prevalence|Rare-event metrics]] explain the stakes.'),
    ('Protect the test from model selection', 'Estimate capture scenarios, fit the model and choose the action threshold on training/development periods. Evaluate one selected candidate on the later adjudicated test. If results lead to revision, create a fresh later test rather than recycling the same cases indefinitely. [[machine-learning/hyperparameter-search-and-untouched-test|The final-test boundary]] still applies.'),
    ('Report sampling variance and support', 'Large inverse inclusion weights and few verified failures can make a point estimate unstable. Report sampled and estimated population denominators, effective sample size and uncertainty by site where feasible. If a depot has zero audited failures, do not print a perfect recall. [[machine-learning/positive-unlabeled-release-project|Release review]] can hold until support improves.')],
    '''audited = [
    {"asset": "seal-47", "true_failure": 1, "reviewed": 1, "inclusion": 0.5},
    {"asset": "seal-62", "true_failure": 1, "reviewed": 0, "inclusion": 0.25},
    {"asset": "seal-83", "true_failure": 0, "reviewed": 1, "inclusion": 0.5},
]

def weighted_failure_recall(records):
    if any(not 0 < record["inclusion"] <= 1 for record in records):
        raise ValueError("positive inclusion probabilities required")
    found = sum(record["true_failure"] * record["reviewed"] / record["inclusion"]
                for record in records)
    positives = sum(record["true_failure"] / record["inclusion"] for record in records)
    if positives == 0:
        return None
    return found / positives

assert round(weighted_failure_recall(audited), 3) == 0.333
assert weighted_failure_recall([audited[2]]) is None''',
    'Weighted scoring is O(N) time and O(1) auxiliary memory for N audited cases. Adjudication is the dominant cost. High weights inflate uncertainty; a weighted point estimate from three records, as here, is only an arithmetic illustration and must not drive release.',
    ['Do not test against confirmation tickets as if they were complete truth.', 'Do not forget sampling weights after oversampling suspicious cases.', 'Do not call zero observed failures perfect recall.'],
    ['machine-learning/positive-unlabeled-target-and-observation-state','machine-learning/pu-selection-mechanism-and-scar-audit','machine-learning/pu-class-prior-and-sensitivity','machine-learning/pu-nonnegative-risk-objective'])


add('positive-unlabeled-release-project',
    'Project: release review for unresolved pump failures',
    'A PU release decision must establish that unconfirmed cases remain unlabeled, selection assumptions are defensible, and a separately adjudicated test supports the action threshold.', [
    ('Freeze the case definition', 'A service team wants to rank pumps for manual seal inspection. Record the 37-day event definition, eligible inspection cohort, confirmation channels, observation maturity and data cutoffs. S equals a verified ticket; Y is the failure truth. Keep the two states in separate fields. [[machine-learning/positive-unlabeled-target-and-observation-state|The observation contract]] is the first release condition.'),
    ('Audit the labeling process', 'Compare confirmed and independently adjudicated positives across depots and severity. If capture varies strongly by site, do not apply one constant correction without qualification. Specify plausible confirmation and prevalence ranges, then rerun the capacity decision across them. [[machine-learning/pu-selection-mechanism-and-scar-audit|Selection]] and [[machine-learning/pu-class-prior-and-sensitivity|prior sensitivity]] define this evidence.'),
    ('Compare training choices', 'Evaluate a ticket-versus-unlabeled baseline, a nonnegative PU objective and a supervised model trained only on fully adjudicated cases. Keep architecture and feature access comparable. The PU objective’s arithmetic depends on the chosen prior; a lower training risk is not the release metric. [[machine-learning/pu-nonnegative-risk-objective|The risk lesson]] explains the assumption.'),
    ('Score the held-out action', 'Independently adjudicate a later stratified test sample, retain inclusion probabilities, and estimate verified failure recall and false-review burden at the proposed review budget. Report mature-positive counts and site slices. A threshold that helps the pooled estimate but misses one depot’s failures is a hold. [[machine-learning/pu-evaluation-with-adjudicated-sample|Weighted evaluation]] supplies the denominator.'),
    ('Require a fallback', 'If audit support is too thin, keep the previous rule or send uncertain cases to manual review while more outcomes mature. Store the old model, threshold and label-contract version. The code is a gate over an illustrative packet, not a claim that the sample proves field benefit.')],
    '''release_packet = {
    "unlabeled_kept_distinct": True,
    "selection_audit_complete": True,
    "prior_sensitivity_stable": False,
    "adjudicated_test_positive_count": 43,
    "minimum_test_positives": 38,
    "worst_depot_failure_recall": 0.57,
    "minimum_depot_recall": 0.64,
    "review_capacity_met": True,
    "rollback_ready": True,
}

def pu_release_gate(packet):
    holds = []
    if not packet["unlabeled_kept_distinct"] or not packet["selection_audit_complete"]:
        holds.append("label contract")
    if not packet["prior_sensitivity_stable"]:
        holds.append("prior sensitivity")
    if packet["adjudicated_test_positive_count"] < packet["minimum_test_positives"] or packet["worst_depot_failure_recall"] < packet["minimum_depot_recall"]:
        holds.append("held-out failure recall")
    if not packet["review_capacity_met"] or not packet["rollback_ready"]:
        holds.append("operating controls")
    return "hold: " + ", ".join(holds) if holds else "eligible for shadow review"

assert pu_release_gate(release_packet) == "hold: prior sensitivity, held-out failure recall"''',
    'The gate is O(1). Its evidence requires confirmed-ticket review, an adjudicated later-period sample, capture-scenario analysis, repeated model training and a capacity simulation. Those costs should be planned before promising automated review. A passing gate permits a controlled shadow phase, not a claim of complete outcome ascertainment.',
    ['Do not promote on confirmation-ticket accuracy.', 'Do not suppress a site regression behind a pooled metric.', 'Do not call an untested capture assumption a measured fact.'],
    ['machine-learning/positive-unlabeled-target-and-observation-state','machine-learning/pu-selection-mechanism-and-scar-audit','machine-learning/pu-class-prior-and-sensitivity','machine-learning/pu-nonnegative-risk-objective','machine-learning/pu-evaluation-with-adjudicated-sample','machine-learning/label-budget-and-incremental-learning-project'])


publish_batch(
    lessons,
    module_title='Positive–unlabeled learning and incomplete labels',
    module_summary='Separate true events from confirmed tickets, audit selection, test prior assumptions and evaluate on adjudicated outcomes.',
    project_heading='Unresolved pump-failure release review',
    crosslinks=[
        ('machine-learning/weak-label-rules-coverage-and-conflicts', lessons[0]['path']),
        ('machine-learning/label-prior-shift-and-odds-adjustment', lessons[1]['path']),
        ('data-science/outcome-label-validation-subsample-design', lessons[2]['path']),
        ('machine-learning/pseudo-label-selection-and-contamination-control', lessons[3]['path']),
        ('machine-learning/rare-event-precision-recall-and-prevalence', lessons[4]['path']),
        ('machine-learning/label-budget-and-incremental-learning-project', lessons[5]['path']),
    ],
    sort_start=6200,
)
