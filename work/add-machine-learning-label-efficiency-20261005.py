"""Add original Machine Learning lessons on label efficiency and updates."""
from ml_fixture_writer_20261005 import publish_batch

lessons = []


def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='machine-learning/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))


add('pseudo-label-selection-and-contamination-control',
    'Pseudo-label selection and contamination control',
    'Self-training proposes labels for an allowed unlabeled training pool, then adds only predictions that meet a declared confidence rule; final evaluation rows remain untouched.', [
    ('Keep an unlabeled pool inside development', 'A dispatch model has many shipment records whose handoff outcomes are not yet reviewed. A classifier fitted on genuine training labels scores an unlabeled development pool. Selected high-confidence scores may become pseudo-labels for another fit, but they are still model guesses. The final test cohort cannot enter that pool even without labels: using its features to tune the procedure changes the evaluation question. [[machine-learning/group-and-time-validation|The split boundary]] applies to unlabeled records too.'),
    ('Require trustworthy scores before a confidence rule', 'A threshold such as 0.9 has no useful meaning if the score is poorly calibrated. Validate probability behavior on disjoint, genuinely labeled development cases before selecting pseudo-labels. The code accepts a frozen score list and returns proposals; it does not train a classifier or claim that the labels are true. It caps proposals per class so one easy majority class cannot consume the entire budget. [[machine-learning/probability-calibration|Calibration]] is a prerequisite, not a guarantee.'),
    ('Track provenance through every iteration', 'Store record ID, original score, model version, threshold and pseudo-label generation round. Do not overwrite an eventual human or mature outcome with the earlier guess. When a guessed label is wrong, repeated self-training can reinforce that error. Audit a sample of proposals by class and site before expanding the procedure. [[machine-learning/rare-event-precision-recall-and-prevalence|Rare-event prevalence]] makes majority-class confidence especially deceptive.'),
    ('Compare against the supervised baseline', 'A larger training table is not automatically a better model. Fit a supervised-only baseline and a candidate with pseudo-labels under the same development protocol, then compare on genuine later labels. Report which sites contributed pseudo-labels and whether improvement remains after removing weak or correlated cases. If the pseudo-labeled candidate merely becomes more confident without better log loss or policy value, reject it. [[machine-learning/handoff-triage-model-review-project|The triage review]] supplies the scorecard.'),
    ('Respect delayed outcomes', 'Some apparently unlabeled shipments are simply still in transit. A late handoff label may mature after a fixed window, making those cases better held for ordinary supervised learning than guessed now. Keep pseudo-label selection separate from the delayed-label monitor and from human review queues. [[machine-learning/feature-drift-and-delayed-label-monitoring|Outcome maturity]] determines when a real label can replace a provisional one.')],
    '''# IDs and scores come from an approved unlabeled development pool.
unlabeled_scores = [
    ("S201", 0.96), ("S202", 0.93), ("S203", 0.58),
    ("S204", 0.04), ("S205", 0.08), ("S206", 0.91),
]
sealed_test_ids = {"T901", "T902"}

def select_pseudo_labels(scored_rows, low=0.10, high=0.90, per_class=2):
    if not 0 <= low < 0.5 < high <= 1:
        raise ValueError("invalid confidence limits")
    proposals = {0: [], 1: []}
    for shipment_id, missed_probability in scored_rows:
        if not 0 <= missed_probability <= 1:
            raise ValueError("invalid probability")
        if missed_probability <= low:
            proposals[0].append((shipment_id, 0, missed_probability))
        elif missed_probability >= high:
            proposals[1].append((shipment_id, 1, missed_probability))
    proposals[0].sort(key=lambda row: row[2])
    proposals[1].sort(key=lambda row: -row[2])
    return proposals[0][:per_class] + proposals[1][:per_class]

selected = select_pseudo_labels(unlabeled_scores)
assert len(selected) == 4
assert not {row[0] for row in selected} & sealed_test_ids
assert {row[1] for row in selected} == {0, 1}''',
    'Scanning N scored rows costs O(N) time; sorting eligible proposals costs O(N log N) time and O(N) memory. Retraining on a larger set adds model-specific cost. Each iteration also needs human audit, provenance storage and a fresh evaluation against genuine labels.',
    ['Do not add sealed-test features to the self-training pool.', 'Do not treat a model score as a verified label.', 'Do not use a high score cutoff without checking calibration and class support.'],
    ['machine-learning/weak-label-rules-coverage-and-conflicts','machine-learning/active-learning-uncertainty-and-diversity','machine-learning/probability-calibration','machine-learning/label-budget-and-incremental-learning-project'])


add('weak-label-rules-coverage-and-conflicts',
    'Weak-label rules, coverage and conflicts',
    'Weak supervision assigns provisional labels through explicit rules that may vote, conflict or abstain; coverage and agreement are diagnostics, not proof of label quality.', [
    ('Write rules from observable evidence', 'A scan gap may indicate a missed handoff, while ample crew may indicate an on-time case. A rule should inspect only fields available at the intended labeling point and return positive, negative or abstain. The code creates three small rules and measures how often any rule votes. It does not convert silence into a negative label. [[machine-learning/prediction-time-feature-availability|Feature timing]] prevents a future outcome field from quietly becoming a rule input.'),
    ('Inspect conflicts before combining votes', 'Two rules can disagree on the same shipment. That can reveal different operational meanings, inconsistent feature clocks or simply weak heuristics. A majority vote is one combination policy, but it ignores rule accuracy and correlation. The code leaves ties unassigned. Several rules copied from the same scan system do not provide independent confirmation. Keep a matrix of individual votes and a conflict count before generating any training target.'),
    ('Audit against genuinely reviewed cases', 'Choose a stratified, time- and site-aware set of human-reviewed shipments. Estimate each rule’s positive and negative error, coverage and drift across sites; do not tune rules repeatedly on the final test labels. The weak labels may help train a candidate, but evaluation must use independent genuine outcomes. [[machine-learning/rare-event-precision-recall-and-prevalence|Rare-event metrics]] explain why a rule with high overall agreement may still miss most failures.'),
    ('Keep rule provenance and ownership', 'Store the rule version, fields used, execution time and reason for each vote. When the scan pipeline changes, a once-useful rule can degrade without an exception. Review rule outputs after ingestion changes and retain the original human label where one exists. [[machine-learning/feature-drift-and-delayed-label-monitoring|The monitoring guide]] separates early input alarms from delayed outcome evidence.'),
    ('Compare with other label-budget tactics', 'Pseudo-labels come from a model’s own predictions; active learning sends selected cases to a reviewer; weak rules use domain logic. These approaches can be combined, but their labels have different trust levels and costs. Do not merge all three into one column without provenance. [[machine-learning/pseudo-label-selection-and-contamination-control|Self-training]] and [[machine-learning/active-learning-uncertainty-and-diversity|active review]] are distinct workflows.')],
    '''# Each rule returns 1, 0, or None for abstention.
shipments = [
    {"id": "S301", "scan_gap": 4, "crew": 8},
    {"id": "S302", "scan_gap": 0, "crew": 9},
    {"id": "S303", "scan_gap": 3, "crew": 2},
    {"id": "S304", "scan_gap": 1, "crew": 5},
]

def gap_rule(row):
    return 1 if row["scan_gap"] >= 3 else None

def low_crew_rule(row):
    return 1 if row["crew"] <= 3 else None

def well_staffed_rule(row):
    return 0 if row["crew"] >= 7 else None

rules = (gap_rule, low_crew_rule, well_staffed_rule)
votes = {row["id"]: [rule(row) for rule in rules] for row in shipments}
covered = sum(any(vote is not None for vote in row_votes)
              for row_votes in votes.values())
conflicts = sum(len({vote for vote in row_votes if vote is not None}) > 1
                for row_votes in votes.values())

def majority_or_abstain(row_votes):
    positives = row_votes.count(1)
    negatives = row_votes.count(0)
    return 1 if positives > negatives else 0 if negatives > positives else None

provisional = {shipment_id: majority_or_abstain(row_votes)
               for shipment_id, row_votes in votes.items()}
assert covered == 3
assert conflicts == 1
assert provisional["S301"] is None
assert provisional["S304"] is None''',
    'Applying R rules to N rows costs O(NR) time and O(NR) storage if every vote is retained. A final majority is cheap, but gold-label audits, conflict analysis and rule maintenance dominate the real operating cost. Related rules can make naive vote counts misleading.',
    ['Do not treat an abstention as a negative label.', 'Do not count correlated rules as independent evidence.', 'Do not evaluate weak labels against the same reviewed cases used to tune the rules.'],
    ['machine-learning/pseudo-label-selection-and-contamination-control','machine-learning/active-learning-uncertainty-and-diversity','machine-learning/feature-drift-and-delayed-label-monitoring','machine-learning/label-budget-and-incremental-learning-project'])


add('active-learning-uncertainty-and-diversity',
    'Active learning with uncertainty and diversity',
    'Active learning chooses which unlabeled cases receive costly human review, often combining model uncertainty with a coverage rule so the batch is not a stack of near duplicates.', [
    ('Define the review budget and candidate pool', 'A dispatch analyst can review three ambiguous shipment records this week. Only development-period unlabeled cases are eligible; no final-test row belongs in the queue. The classifier supplies scores, but they are ranking signals, not verified event rates unless calibrated. For a binary task, scores near one half are one uncertainty proxy. [[machine-learning/pseudo-label-selection-and-contamination-control|Pseudo-labeling]] instead assigns provisional labels without asking the analyst.'),
    ('Prevent one site from taking every slot', 'Uncertainty alone may pick many nearly identical shipments from the same warehouse. The code sorts by closeness to one half and allows one candidate per site. This simple site quota is a diversity policy, not a full optimal batch selector. A different task may require route, equipment type or shift coverage. Record the chosen rule before inspection so a desired result cannot guide the queue retrospectively.'),
    ('Expect sampling bias in the reviewed labels', 'The reviewed set overrepresents uncertain cases by design. Its raw event frequency does not estimate the production prevalence, and accuracy on that set is not an unbiased deployment metric. Keep a separate random or policy-relevant audit sample, plus a sealed future cohort, for evaluation. [[machine-learning/rare-event-precision-recall-and-prevalence|The prevalence guide]] explains how class mix affects precision.'),
    ('Audit reviewer consistency', 'Some ambiguous cases are ambiguous because the event clock or evidence is unclear. Give reviewers an explicit label definition and an abstain or escalation path. Re-review a small overlap sample to measure disagreement; do not force a label merely because the model requested one. Store reviewer version, decision time and adjudication history. [[data-annotation/data-annotation-tutorial|The annotation curriculum]] provides the wider workflow.'),
    ('Measure value per label', 'After adding reviewed cases, retrain the development model and compare it with a random-sampling acquisition baseline under equal label cost. Gains can flatten once a particular boundary is well sampled. Report performance on genuine held-out labels and by site. [[machine-learning/fold-local-feature-selection-and-stability|Feature selection]] must still happen inside the training folds when the labeled set changes.')],
    '''unlabeled_pool = [
    ("S401", "Harbor", 0.49), ("S402", "Harbor", 0.51),
    ("S403", "Inland", 0.47), ("S404", "North", 0.54),
    ("S405", "South", 0.88), ("S406", "Inland", 0.62),
]
sealed_test_ids = {"T903", "T904"}

def review_queue(scored_cases, budget):
    ordered = sorted(scored_cases, key=lambda case: (abs(case[2] - 0.5), case[0]))
    selected = []
    covered_sites = set()
    for shipment_id, site, probability in ordered:
        if site in covered_sites:
            continue
        selected.append((shipment_id, site, probability))
        covered_sites.add(site)
        if len(selected) == budget:
            break
    return selected

queue = review_queue(unlabeled_pool, budget=3)
assert len(queue) == 3
assert len({site for _, site, _ in queue}) == 3
assert not {shipment_id for shipment_id, _, _ in queue} & sealed_test_ids
assert queue[0][0] == "S401"''',
    'Sorting N candidates costs O(N log N) time and O(N) memory, while scoring the pool adds model-specific cost. Human review is the limiting resource. Site quotas may improve coverage but can displace a highly informative case, so compare acquisition policies at equal review budget.',
    ['Do not evaluate deployment accuracy on only the actively selected review queue.', 'Do not fill the queue with duplicate records from one site.', 'Do not force a disputed human label into training without adjudication.'],
    ['machine-learning/pseudo-label-selection-and-contamination-control','machine-learning/weak-label-rules-coverage-and-conflicts','machine-learning/handoff-triage-model-review-project','machine-learning/label-budget-and-incremental-learning-project'])


add('online-updates-with-delayed-feedback',
    'Online updates with delayed feedback',
    'An online classifier updates its parameters from newly matured labels in event order, after it has recorded each prediction, rather than rebuilding from the entire history on every arrival.', [
    ('Score before learning from the event', 'A handoff model predicts at intake. The actual missed-handoff label arrives later, sometimes after a route investigation. Record the prediction, model version and feature snapshot first. Only a matured label can trigger an update. The code simulates chronological days, scores arriving shipments, and applies small logistic-gradient steps for earlier cases whose labels became available. The event’s own hidden label is never read during its prediction.'),
    ('Keep a fixed feature contract', 'Online updating does not remove preprocessing risk. Store feature order, scaling state, missing-value policy and label definition with each model version. Recomputing a global mean from future rows while replaying historical examples changes old inputs. [[machine-learning/leakage-safe-preprocessing-pipeline|The pipeline guide]] defines the fitted transform contract; [[machine-learning/prediction-time-feature-availability|feature timing]] defines the input clock.'),
    ('Evaluate predict-then-update honestly', 'A streaming report can compare each stored prediction with its label after maturity. It must not re-score the event using a model already updated from that event. Report the count of mature outcomes and the backlog of pending labels. Early reports can overrepresent fast resolutions. [[machine-learning/feature-drift-and-delayed-label-monitoring|Delayed-label monitoring]] explains that censoring problem.'),
    ('Watch drift and forgetting', 'A fixed learning rate can chase recent noise, while a decaying rate can stop adapting after a real process change. Keep a replay sample from earlier periods or compare with a periodically retrained model if older regimes still matter. Do not update solely because an input histogram changed; confirm feature integrity and mature-label loss. An online fit can be cheaper per update but harder to reproduce and roll back than a batch model.'),
    ('Use a release gate for parameter changes', 'Log update order, label arrival, learning rate, seed if sampling and an immutable checkpoint. Evaluate proposed update rules on a historical stream without accessing labels before their arrival. Keep a sealed later stream for a final comparison. [[machine-learning/label-budget-and-incremental-learning-project|The applied review]] brings the update and monitoring decisions together.')],
    '''from math import exp

# Arrival day, shipment ID, backlog, label day, eventual missed-handoff label.
arrivals = [(1, "S501", 0.4, 3, 0), (2, "S502", 1.8, 5, 1),
            (4, "S503", 1.2, 7, 0), (6, "S504", 2.3, 8, 1)]
intercept, slope = 0.0, 0.0
pending = []
predictions = {}
learning_rate = 0.15

def probability(backlog, fitted_intercept, fitted_slope):
    score = fitted_intercept + fitted_slope * backlog
    return 1 / (1 + exp(-score))

for day in range(1, 10):
    for arrival_day, shipment_id, backlog, label_day, missed in arrivals:
        if arrival_day == day:
            predictions[shipment_id] = probability(backlog, intercept, slope)
            pending.append((shipment_id, backlog, label_day, missed))
    matured = [record for record in pending if record[2] == day]
    pending = [record for record in pending if record[2] > day]
    for shipment_id, backlog, label_day, missed in matured:
        residual = probability(backlog, intercept, slope) - missed
        intercept -= learning_rate * residual
        slope -= learning_rate * backlog * residual

assert len(predictions) == 4
assert not pending
assert predictions["S501"] == 0.5
assert all(0 < score < 1 for score in predictions.values())''',
    'Each one-feature event score and mature-label update costs O(1) arithmetic and parameter storage; with F features the update is O(F). A pending-label queue uses O(P) space for P unresolved cases. Logging, replay buffers, checkpoints and late correction handling add operational cost.',
    ['Do not use a shipment’s outcome before its label arrival day.', 'Do not report re-scored historical predictions as pre-update accuracy.', 'Do not change scaling or target definitions silently between checkpoints.'],
    ['machine-learning/feature-drift-and-delayed-label-monitoring','machine-learning/active-learning-uncertainty-and-diversity','machine-learning/label-prior-shift-and-odds-adjustment','machine-learning/label-budget-and-incremental-learning-project'])


add('label-prior-shift-and-odds-adjustment',
    'Label-prior shift and odds adjustment',
    'A prior-shift odds adjustment changes a calibrated binary posterior when the class prevalence changes but the feature distribution within each class remains stable.', [
    ('Name the strong assumption', 'Suppose the missed-handoff share rises from an older cohort to a recent one. Prior shift assumes that, conditional on whether a handoff is missed, the distribution of intake features is unchanged. Only the class prior changes. A new scanner, route policy or crew allocation can violate that assumption. The code shows the odds conversion under the assumption; it cannot diagnose whether the assumption holds. [[machine-learning/feature-drift-and-delayed-label-monitoring|Feature monitoring]] gives a first warning, not proof.'),
    ('Use independent prevalence evidence', 'The old prior should come from the population the original calibrated model represented. Estimate the new prior from a properly matured, representative labeled cohort or a validated quantification method. An actively sampled review queue overrepresents uncertain cases and cannot provide it directly. Nor can the same-day fraction of resolved shipments when slow failures remain pending. [[machine-learning/active-learning-uncertainty-and-diversity|Active sampling]] and [[machine-learning/feature-drift-and-delayed-label-monitoring|label maturity]] explain those traps.'),
    ('Adjust odds, not raw probability by addition', 'Convert the old posterior to odds, multiply by the ratio of new prior odds to old prior odds, then convert back to probability. This follows from the unchanged class-conditional feature likelihoods. The code checks that a baseline posterior equal to the old prior maps to the new prior. Directly adding the prevalence difference can leave the interval from zero to one and is not the same operation.'),
    ('Recheck calibration and decisions', 'Even when the algebra is correct, the old probabilities may be miscalibrated and the new prevalence estimate noisy. Evaluate adjusted predictions on a later independent labeled cohort. Review log loss, calibration and the number of dispatch interventions. A changed probability may move cases across the cost threshold, so the resulting policy needs a new capacity check. [[machine-learning/probability-calibration|Calibration]] and [[machine-learning/decision-threshold-and-cost|threshold costing]] remain separate tests.'),
    ('Prefer retraining when the mechanism changed', 'If the scanner schema, carrier mix or relation between backlog and outcome changed, an odds multiplier cannot repair the model. Compare the adjusted candidate with a recent-data refit under the same evaluation boundary. Record which assumption justified the adjustment and when it expires. [[machine-learning/label-budget-and-incremental-learning-project|The project]] asks for a hold decision when that evidence is absent.')],
    '''def adjust_for_prior_shift(old_probability, old_prior, new_prior):
    if not all(0 < value < 1 for value in
               (old_probability, old_prior, new_prior)):
        raise ValueError("probabilities and priors must be inside (0, 1)")
    old_odds = old_probability / (1 - old_probability)
    prior_odds_ratio = (new_prior / (1 - new_prior)) / (old_prior / (1 - old_prior))
    adjusted_odds = old_odds * prior_odds_ratio
    return adjusted_odds / (1 + adjusted_odds)

old_prior = 0.18
new_prior = 0.31
scores = [0.06, 0.18, 0.42, 0.73]
adjusted = [adjust_for_prior_shift(score, old_prior, new_prior)
            for score in scores]
assert abs(adjust_for_prior_shift(old_prior, old_prior, new_prior) - new_prior) < 1e-12
assert all(new > old for old, new in zip(scores, adjusted))
assert all(0 < score < 1 for score in adjusted)''',
    'The adjustment is O(N) time for N scored cases and O(1) working state if streamed. Estimating the new prior, checking class-conditional stability and validating the policy require independent labels and far more work than the conversion itself.',
    ['Do not infer the new prior from an actively sampled or immature-label cohort.', 'Do not apply an odds correction when the class-conditional feature process changed.', 'Do not treat the adjusted output as calibrated without a later labeled check.'],
    ['machine-learning/online-updates-with-delayed-feedback','machine-learning/probability-calibration','machine-learning/feature-drift-and-delayed-label-monitoring','machine-learning/label-budget-and-incremental-learning-project'])


add('label-budget-and-incremental-learning-project',
    'Label budget and incremental learning project',
    'Design a limited-review shipment workflow that keeps provisional, weak, human and matured labels separate while evaluating an incremental classifier against a fixed baseline.', [
    ('Define the label ledger', 'For every shipment, store intake time, feature snapshot, prediction, label status, label source, arrival time and any later correction. Separate human-reviewed labels, matured operational outcomes, weak-rule votes and model-generated pseudo-labels. A single overwritten label column conceals the trust level and permits leakage. [[machine-learning/weak-label-rules-coverage-and-conflicts|Weak rules]] and [[machine-learning/pseudo-label-selection-and-contamination-control|pseudo-labels]] need distinct provenance.'),
    ('Allocate review capacity deliberately', 'Reserve a fixed number of analyst reviews for ambiguous or high-value cases, with site coverage, and a smaller random audit for measuring the production distribution. Do not evaluate the model on only the actively selected queue. Track reviewer disagreement and unresolved cases. Compare active acquisition with a random-review baseline at the same label cost. [[machine-learning/active-learning-uncertainty-and-diversity|The acquisition guide]] supplies the selection boundary.'),
    ('Replay the stream in event order', 'Before each label matures, score and store the case using the model version active at intake. When genuine labels arrive, update the candidate or schedule a batch refit. Keep weak and pseudo-label inputs clearly tagged and compare versions on a sealed later stream. A later model may be more accurate, but it must not re-score old cases to rewrite its pre-update history. [[machine-learning/online-updates-with-delayed-feedback|The online guide]] demonstrates predict-then-update.'),
    ('Check shift before correcting scores', 'If recent prevalence changes, obtain a representative, matured estimate and examine whether class-conditional feature behavior remains stable. Only then evaluate a prior-odds adjustment as one candidate. Also compare recent-data retraining and no change. A same-day shift alarm is not enough evidence to move dispatch thresholds. [[machine-learning/label-prior-shift-and-odds-adjustment|The adjustment guide]] states its narrow assumption.'),
    ('Record the release decision', 'The code checks the evidence packet for a bounded pilot discussion. It does not certify that labels are correct or that an online model will improve outcomes. Include owner, rollback, privacy handling, review capacity, final cohort performance and matured-label monitoring. Hold release when any boundary is unresolved. [[machine-learning/handoff-triage-model-review-project|The triage project]] defines the action and cost scorecard.')],
    '''def label_workflow_gate(packet):
    checks = {
        "label_sources_separated": "label provenance",
        "sealed_future_cohort": "future evaluation",
        "review_budget_and_audit": "review allocation",
        "prediction_before_update": "event order",
        "matured_outcomes_only": "outcome maturity",
        "shift_assumption_audited": "shift assumption",
        "rollback_owner_named": "rollback owner",
    }
    missing = [reason for field, reason in checks.items() if not packet.get(field)]
    return "pilot review" if not missing else "hold: " + ", ".join(missing)

dispatch_workflow = {
    "label_sources_separated": True,
    "sealed_future_cohort": True,
    "review_budget_and_audit": True,
    "prediction_before_update": True,
    "matured_outcomes_only": False,
    "shift_assumption_audited": False,
    "rollback_owner_named": True,
}
assert label_workflow_gate(dispatch_workflow) == (
    "hold: outcome maturity, shift assumption"
)''',
    'The gate itself is O(K) for K checks. Candidate scoring and updates scale with feature count and event volume; weak rules cost O(NR) over N rows and R rules, while active selection adds sorting. Human review, provenance storage and delayed corrections dominate many deployments.',
    ['Do not merge weak, pseudo and human labels into one unqualified target.', 'Do not evaluate an active-learning model only on actively selected cases.', 'Do not update from an outcome before it has matured.'],
    ['machine-learning/pseudo-label-selection-and-contamination-control','machine-learning/weak-label-rules-coverage-and-conflicts','machine-learning/active-learning-uncertainty-and-diversity','machine-learning/online-updates-with-delayed-feedback','machine-learning/label-prior-shift-and-odds-adjustment','machine-learning/handoff-triage-model-review-project'])


publish_batch(
    lessons,
    module_title='Label efficiency and incremental decisions',
    module_summary='Self-training, weak rules, active review, delayed online updates and conditional prior adjustment.',
    project_heading='Label budget and incremental learning review',
    crosslinks=[
        ('machine-learning/probability-calibration', lessons[0]['path']),
        ('machine-learning/rare-event-precision-recall-and-prevalence', lessons[1]['path']),
        ('machine-learning/handoff-triage-model-review-project', lessons[2]['path']),
        ('machine-learning/feature-drift-and-delayed-label-monitoring', lessons[3]['path']),
        ('machine-learning/class-weighting-versus-decision-thresholds', lessons[4]['path']),
        ('machine-learning/ensemble-release-review-project', lessons[5]['path']),
    ],
    sort_start=5000,
)
