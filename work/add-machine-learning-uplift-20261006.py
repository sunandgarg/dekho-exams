"""Add a connected, original uplift-modeling module to Machine Learning."""

from ml_fixture_writer_20261005 import publish_batch


lessons = []


def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='machine-learning/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))


add('uplift-question-and-randomized-event-contract',
    'Uplift targets and randomized event contracts',
    'Uplift estimates the change in an outcome caused by assigning an action, conditional on information available before that assignment.', [
    ('Define the decision before the model', 'A learning platform can send a reminder to a learner who has not finished a lesson. The decision is whether to send it at 09:00 on an eligible day; the outcome is lesson completion within the next seven days. Sending at noon, sending a different message, or counting completion over 30 days defines another treatment question. [[causal-inference/estimand-and-counterfactual-unit|The causal estimand]] fixes the unit, action, comparison and horizon before features are built.'),
    ('Separate baseline response from incremental response', 'A learner with an 82% completion probability after a reminder may have completed with 80% probability anyway. The estimated uplift is two percentage points, not 82. Another learner with a 36% treated probability and 19% untreated probability has lower absolute response but 17 points of uplift. A policy that targets the first learner because the treated probability is highest can waste a scarce outreach slot.'),
    ('Log the assignment mechanism', 'For every eligible decision, record learner ID, decision timestamp, assigned action, probability of that assignment, policy version, eligibility rule and pre-decision features. Keep rows for control assignments and unanswered messages. Assignment probability must be known at decision time. [[online-experimentation/exposure-and-event-logging|Experiment exposure logs]] help distinguish assignment from delivery; the primary intention-to-treat analysis uses assignment.'),
    ('Preserve outcome maturity', 'A seven-day outcome is not available two days after assignment. Either wait for the complete window or mark the row immature; do not turn it into a non-completion. A learner can receive multiple reminders, so choose a washout rule or model a sequential policy instead of treating overlapping decisions as independent. [[machine-learning/group-and-time-validation|Group-and-time validation]] keeps a learner from appearing on both sides of a test split.'),
    ('Name the identification boundary', 'Random assignment makes treatment groups comparable in expectation; it does not repair missing outcomes, broken randomization, interference between learners, or a change in message content. Observational logs require measured confounders and overlap, with stronger assumptions than a randomized holdout. [[machine-learning/overlap-and-heterogeneity-diagnostics|Overlap diagnostics]] test whether the proposed targeting population has support.')],
    '''decision_log = [
    {"learner": "acct-47", "assigned_at": 120, "action": 1, "assignment_probability": 0.46, "observed_through": 128},
    {"learner": "acct-83", "assigned_at": 124, "action": 0, "assignment_probability": 0.54, "observed_through": 126},
]

def mature_assignment_rows(records, outcome_window_days=7):
    mature = []
    for record in records:
        if record["action"] not in (0, 1):
            raise ValueError("unknown action")
        if not 0 < record["assignment_probability"] <= 1:
            raise ValueError("invalid logged assignment probability")
        if record["observed_through"] >= record["assigned_at"] + outcome_window_days:
            mature.append(record)
    return mature

assert [row["learner"] for row in mature_assignment_rows(decision_log)] == ["acct-47"]''',
    'Filtering N decisions is O(N) time and O(N) output space. The costly part is a trustworthy event stream, a stable randomization key and seven-day outcome reconciliation. Retaining a permanent control fraction has opportunity cost, but without support for both actions a personalized causal claim cannot be checked.',
    ['Do not train on only delivered reminders when the decision was assignment.', 'Do not mark a two-day-old seven-day outcome as a failure.', 'Do not confuse high treated response with large treatment effect.'],
    ['machine-learning/s-and-t-learner-treatment-effect-baselines','machine-learning/cross-fitted-doubly-robust-uplift-scores','machine-learning/overlap-and-heterogeneity-diagnostics','machine-learning/uplift-ranking-and-policy-value-evaluation','causal-inference/estimand-and-counterfactual-unit'])


add('s-and-t-learner-treatment-effect-baselines',
    'S-learners and T-learners for treatment-effect baselines',
    'An S-learner fits one outcome model with action as an input; a T-learner fits separate outcome models by action and subtracts their predictions.', [
    ('Use a small baseline first', 'For reminder targeting, estimate completion under action and control within prespecified learner segments before fitting a flexible model. If eight eligible learners in a segment were randomized, four assigned reminders with three completions and four assigned control with one completion, the observed segment contrast is 3/4 minus 1/4, or 0.50. It is noisy. It is still a useful arithmetic test for the event pipeline.'),
    ('Understand what each learner fits', 'An S-learner uses one function m(x,a) and computes m(x,1) minus m(x,0). Shared parameters help small arms, but heavy regularization may suppress the action feature and flatten real heterogeneity. A T-learner fits m1(x) only on treated rows and m0(x) only on controls. It can capture distinct response patterns, yet each arm has fewer examples and extrapolates where its own arm is sparse.'),
    ('Keep the split outside both fits', 'Split by learner and decision time before tuning features, hyperparameters or segment boundaries. Fit preprocessing only on the training period. A categorical encoding learned from future cohorts can leak changes in the catalog or learner mix. [[machine-learning/group-and-time-validation|Temporal validation]] protects the forecast setting; [[machine-learning/uplift-ranking-and-policy-value-evaluation|uplift evaluation]] checks whether model differences actually improve decisions.'),
    ('Distinguish outcome fit from effect fit', 'Low log loss for both arm models does not establish accurate differences. If both models make the same 11-point upward error for one learner, their difference might survive; if the errors oppose each other, uplift can be badly wrong despite decent overall accuracy. Compare effect ranking, policy value, arm-specific calibration and segment support on held-out randomized assignments.'),
    ('Choose complexity for the evidence', 'If treatment is rare or segments are thin, shrink toward a simpler common model and report uncertainty rather than claiming a precise per-learner effect. In observational data, separate arm regressions alone do not remove confounding. An X-learner can use imputed effects when arm sizes differ, while [[machine-learning/cross-fitted-doubly-robust-uplift-scores|augmented weighting scores]] also use assignment probabilities.')],
    '''from statistics import mean

randomized_segment = [
    {"action": 1, "completed": 1}, {"action": 1, "completed": 1},
    {"action": 1, "completed": 0}, {"action": 1, "completed": 1},
    {"action": 0, "completed": 1}, {"action": 0, "completed": 0},
    {"action": 0, "completed": 0}, {"action": 0, "completed": 0},
]

def segment_uplift(assignments):
    treated = [row["completed"] for row in assignments if row["action"] == 1]
    control = [row["completed"] for row in assignments if row["action"] == 0]
    if not treated or not control:
        raise ValueError("both randomized arms are required")
    return mean(treated) - mean(control)

assert segment_uplift(randomized_segment) == 0.5''',
    'The arithmetic segment baseline is O(N) time and O(N) temporary space. For a T-learner, fitting cost is the sum of two outcome-model fits; an S-learner fits once but predicts twice per learner. Cross-validation multiplies those costs. Arm-specific sample size, rather than total row count, limits credible heterogeneity.',
    ['Do not treat an outcome-model accuracy score as an uplift score.', 'Do not create segments after looking at test outcomes.', 'Do not fit a separate arm model where that arm has no local support.'],
    ['machine-learning/uplift-question-and-randomized-event-contract','machine-learning/cross-fitted-doubly-robust-uplift-scores','machine-learning/overlap-and-heterogeneity-diagnostics','machine-learning/uplift-ranking-and-policy-value-evaluation','machine-learning/intervention-uplift-release-project'])


add('cross-fitted-doubly-robust-uplift-scores',
    'Cross-fitted augmented weighting scores for uplift',
    'An augmented uplift score combines predictions under each action with an inverse-assignment correction for the action actually observed.', [
    ('Build the score from two nuisance estimates', 'Let m1 and m0 be predicted completion probabilities under reminder and control, and let e be the probability of reminder assignment. For a treated row, add (outcome minus m1) divided by e to m1 minus m0. For a control row, subtract (outcome minus m0) divided by (1 minus e). The resulting pseudo-outcome is noisy; it is not a literal personal counterfactual.'),
    ('Check the arithmetic', 'Suppose m1 is 0.42, m0 is 0.31 and e is 0.40. A treated learner who completes gets 0.42 minus 0.31 plus (1 minus 0.42)/0.40 = 1.56. A score above one is legitimate: inverse weighting magnifies a rare observed outcome. It should not be displayed as a probability. Averaging scores over supported groups can target an average effect under appropriate assumptions.'),
    ('Cross-fit before learning heterogeneity', 'Partition learners into folds. Fit outcome and propensity models on every fold except one, predict the held-out fold, construct scores there, then train a final effect model from those out-of-fold scores. Keep every episode of one learner in the same fold. This reduces own-row overfitting; it does not create identification when unmeasured factors affect both reminders and completion.'),
    ('Use logged randomization when available', 'If assignment was randomized with logged e, use that known probability rather than estimating it. For observational assignment, propensity estimation needs only pre-action confounders, a credible causal graph, and stable action definitions. [[causal-inference/confounder-graph-and-covariate-timing|Covariate timing]] is the first defense. A wrong outcome model and wrong propensity model can both fail; two-model correction never means immunity to missing confounders.'),
    ('Inspect unstable corrections', 'When e approaches zero or one, residual terms explode. Report effective sample size, weight tails and treatment counts by score band; predeclare any trimming policy. [[machine-learning/overlap-and-heterogeneity-diagnostics|Overlap diagnostics]] decide where estimates are supportable. Keep model tuning out of the final randomized test, where [[machine-learning/uplift-ranking-and-policy-value-evaluation|policy value]] is measured.')],
    '''def doubly_robust_uplift_score(action, outcome, treated_prediction,
                               control_prediction, treatment_probability):
    if action not in (0, 1) or outcome not in (0, 1):
        raise ValueError("binary action and outcome required")
    if not 0 < treatment_probability < 1:
        raise ValueError("both actions need positive probability")
    baseline = treated_prediction - control_prediction
    if action == 1:
        return baseline + (outcome - treated_prediction) / treatment_probability
    return baseline - (outcome - control_prediction) / (1 - treatment_probability)

treated_score = doubly_robust_uplift_score(1, 1, 0.42, 0.31, 0.40)
assert abs(treated_score - 1.56) < 1e-12''',
    'One score costs O(1) time and space after nuisance predictions exist; N scores cost O(N). Cross-fitting K folds trains nuisance models K times and stores out-of-fold predictions. Inverse weights can dominate variance when one action is rare, so compute cost is seldom the binding limit; data support is.',
    ['Do not call a pseudo-outcome a personal treatment probability.', 'Do not use in-sample nuisance predictions when claiming cross-fitted evaluation.', 'Do not infer causal protection from two-model correction if confounders are missing.'],
    ['machine-learning/uplift-question-and-randomized-event-contract','machine-learning/s-and-t-learner-treatment-effect-baselines','machine-learning/overlap-and-heterogeneity-diagnostics','machine-learning/uplift-ranking-and-policy-value-evaluation','causal-inference/overlap-and-weighting-diagnostics'])


add('overlap-and-heterogeneity-diagnostics',
    'Overlap and heterogeneity diagnostics for uplift models',
    'An uplift estimate is locally credible only where both actions could have been observed for comparable eligible decisions.', [
    ('Locate unsupported learners', 'If a policy always sends reminders to learners with an overdue assignment, the observational log contains no untreated comparison for that state. A model may still output a number, but it extrapolates beyond evidence. Inspect treatment propensity distributions for both arms and count decisions in predeclared slices. [[causal-inference/overlap-and-weighting-diagnostics|Overlap and weighting diagnostics]] explain why extreme inverse weights destabilize averages.'),
    ('Use effective sample size, not raw count', 'For weights w, effective sample size is (sum w)^2 divided by sum(w squared). It can be far below the logged row count when a few rare assignments dominate. Report it separately for treated and control observations within each policy-relevant segment. A segment with 300 rows and an effective control sample of 18 should not receive a confident fine-grained ranking.'),
    ('Separate heterogeneity from noise', 'Split learners by a feature defined before treatment, such as whether they have previously completed a course. Compare treated and control outcomes within each segment with uncertainty intervals, then ask whether segment effects differ. A positive point estimate in one tiny slice and a negative estimate in another is not evidence of a stable interaction. Reserve a randomized holdout for final evaluation.'),
    ('Respect the unit of uncertainty', 'One learner may generate several eligible decisions. Resample learners, not rows, when estimating uncertainty for an average effect or policy value. Calendar weeks may also be correlated through campaigns and exams; block by week when this is material. [[online-experimentation/sample-ratio-and-aa-diagnostics|Sample-ratio checks]] can reveal randomization defects before any uplift plot is interpreted.'),
    ('Declare a fallback policy', 'Where overlap fails, do not smooth away the unsupported region and quietly target it. Keep a uniform randomized holdout, use a simple default action, or collect exploration data under a governed policy. [[machine-learning/contextual-bandit-action-logging-and-support|Action logging and support]] connect this decision to the bandit setting; the current uplift analysis stays with one-shot treatment assignment.')],
    '''logged_decisions = [
    {"learner": "acct-47", "action": 1, "treatment_probability": 0.28},
    {"learner": "acct-62", "action": 0, "treatment_probability": 0.47},
    {"learner": "acct-83", "action": 1, "treatment_probability": 0.61},
    {"learner": "acct-94", "action": 0, "treatment_probability": 0.74},
]

def assignment_weight(record):
    probability = record["treatment_probability"]
    if not 0 < probability < 1:
        raise ValueError("missing action support")
    observed_probability = probability if record["action"] else 1 - probability
    return 1 / observed_probability

weights = [assignment_weight(record) for record in logged_decisions]
effective_count = sum(weights) ** 2 / sum(weight ** 2 for weight in weights)
assert round(max(weights), 3) == 3.846
assert effective_count < len(logged_decisions)''',
    'A pass over N logged decisions costs O(N) time and O(N) memory if weights are retained, or O(1) extra memory for streaming sums. Segment and clustered-uncertainty checks add repeated passes or resampling fits. Trimming changes the target population, so record its rule and excluded share.',
    ['Do not treat an out-of-support prediction as an observed causal effect.', 'Do not report only raw segment counts when weights are concentrated.', 'Do not bootstrap repeated decisions as independent learner rows.'],
    ['machine-learning/uplift-question-and-randomized-event-contract','machine-learning/cross-fitted-doubly-robust-uplift-scores','machine-learning/uplift-ranking-and-policy-value-evaluation','machine-learning/capacity-constrained-treatment-policy','causal-inference/overlap-and-weighting-diagnostics'])


add('uplift-ranking-and-policy-value-evaluation',
    'Uplift ranking and offline policy-value evaluation',
    'A useful uplift model sends the action to people whose outcomes change because of it; outcome accuracy alone cannot establish that ranking.', [
    ('Freeze scores before the test', 'Train an effect model on earlier decisions, then score a later randomized test cohort using only pre-assignment features. Sort eligible learners by predicted uplift and predeclare capacity bands, such as the top 15% and 30%. For each band, estimate treated-minus-control completion with assignment probabilities accounted for. Plotting an uplift curve after changing bands to flatter the model turns the test into training.'),
    ('Evaluate the policy that will run', 'Define a policy pi(x) returning reminder or control. Under a randomized logging policy with known probability for each action, inverse-propensity policy value averages observed outcome divided by the probability of the logged action only when pi(x) matches that action. This estimates expected outcome under the new policy if consistency, support, and stable outcome measurement hold. [[machine-learning/inverse-propensity-policy-value|Inverse-propensity policy value]] develops the estimator.'),
    ('Compare incremental value, not just value', 'A policy value of 0.41 means little without a comparable baseline. Report value minus the no-reminder policy on the same test population, plus reminder cost and operational capacity. For 1,000 eligible learners, estimated uplift of 0.04 among 120 targeted learners implies about 4.8 additional completions in expectation, not 40 across the full cohort. A small benefit may disappear under uncertainty or message fatigue.'),
    ('Understand metric failure modes', 'AUC or accuracy on completion may reward finding learners who would finish anyway. A naive uplift curve can be distorted by uneven treatment rates across score bands; use randomized arms or appropriate weighting. Ranking each positive example against a tiny sampled set of negatives also changes the question. Check assignment balance and held-out arm outcome rates before presenting any curve.'),
    ('Make uncertainty operational', 'Use learner-level resampling or a suitable influence-function approach for confidence intervals; keep test choices frozen. A high-variance inverse-weighted estimate may require a larger randomized test or an outcome-model-assisted estimate. [[machine-learning/cross-fitted-doubly-robust-uplift-scores|Augmented weighting]] can improve stability when its nuisance models behave, but it cannot replace randomized support.')],
    '''randomized_holdout = [
    {"segment": "high", "action": 1, "outcome": 1, "logged_probability": 0.5},
    {"segment": "high", "action": 0, "outcome": 0, "logged_probability": 0.5},
    {"segment": "low", "action": 1, "outcome": 0, "logged_probability": 0.5},
    {"segment": "low", "action": 0, "outcome": 1, "logged_probability": 0.5},
]

def inverse_propensity_policy_value(records, policy):
    if not records:
        raise ValueError("empty evaluation cohort")
    weighted_outcome = 0.0
    for record in records:
        if not 0 < record["logged_probability"] <= 1:
            raise ValueError("invalid probability of logged action")
        if policy(record) == record["action"]:
            weighted_outcome += record["outcome"] / record["logged_probability"]
    return weighted_outcome / len(records)

target_high = lambda record: int(record["segment"] == "high")
assert inverse_propensity_policy_value(randomized_holdout, target_high) == 1.0''',
    'Policy scoring is O(N) for N test decisions; sorting all scores is O(N log N), or O(N log K) with a heap for a top-K capacity. Inverse weighting can have high variance when the new policy selects rarely logged actions. Keep the test cohort large enough for the intended decision and its uncertainty.',
    ['Do not use completion AUC as the sole uplift metric.', 'Do not select the best-looking capacity band on the final test.', 'Do not divide by the count of matching actions; the inverse-weighted denominator is the full eligible cohort.'],
    ['machine-learning/uplift-question-and-randomized-event-contract','machine-learning/cross-fitted-doubly-robust-uplift-scores','machine-learning/overlap-and-heterogeneity-diagnostics','machine-learning/capacity-constrained-treatment-policy','machine-learning/inverse-propensity-policy-value'])


add('capacity-constrained-treatment-policy',
    'Capacity-constrained treatment policies and guardrails',
    'A treatment policy converts estimated incremental benefit into an action under capacity, cost, eligibility and safety limits.', [
    ('Convert probability uplift into net value', 'If one additional course completion is worth 24 units to an outreach team and one reminder costs 0.7 units, a learner with predicted uplift 0.06 has estimated net value 24 times 0.06 minus 0.7 = 0.74 units. A learner at 0.02 yields negative 0.22 units and should not be targeted merely because capacity remains. Units must describe a real decision objective, not an arbitrary score scale.'),
    ('Apply eligibility before ranking', 'Exclude opted-out learners, recently contacted learners and accounts with immature outcomes before computing a top-K list. The eligibility contract is versioned and shared by training, evaluation and serving. A model that was evaluated on one eligible population but served on another has no directly transferable policy-value estimate. [[machine-learning/uplift-question-and-randomized-event-contract|The event contract]] defines this population.'),
    ('Respect budget and tie rules', 'With a limit of 24 reminders per day, select positive-net-value learners until capacity is used. For deterministic replay, sort ties by a stable learner ID after net value. If the outreach team imposes per-region ceilings, solve the constrained selection explicitly and evaluate that exact rule, not an unconstrained top-24 proxy. [[machine-learning/uplift-ranking-and-policy-value-evaluation|Offline policy value]] must use the deployed policy.'),
    ('Keep a measurement lane', 'Retain a randomized control group among eligible learners so that changes in lesson difficulty, exam season or message fatigue can be separated from model drift. Do not treat the control lane as leftover capacity. Monitor opt-outs, complaint rate, delivery failures and group-level effects alongside completions. A high average uplift does not excuse a severe harm in a protected or operationally important slice.'),
    ('Define rollback and refresh', 'Freeze the model, feature snapshot, value conversion, capacity and policy version in each decision log. Pause targeting if assignment logs fail, overlap falls below the release threshold, or a guardrail breaches its limit. Update the model only after outcome windows mature and a fresh randomized evaluation supports the change. [[machine-learning/intervention-uplift-release-project|The release project]] gives a concrete decision packet.')],
    '''eligible_learners = [
    {"learner": "acct-47", "uplift": 0.06, "opted_out": False},
    {"learner": "acct-62", "uplift": 0.02, "opted_out": False},
    {"learner": "acct-83", "uplift": 0.11, "opted_out": True},
    {"learner": "acct-94", "uplift": 0.04, "opted_out": False},
]

def choose_reminders(records, capacity, value_per_completion=24, reminder_cost=0.7):
    if capacity < 0:
        raise ValueError("capacity must be nonnegative")
    candidates = []
    for record in records:
        net_value = value_per_completion * record["uplift"] - reminder_cost
        if not record["opted_out"] and net_value > 0:
            candidates.append((net_value, record["learner"]))
    candidates.sort(key=lambda candidate: (-candidate[0], candidate[1]))
    return [learner for _, learner in candidates[:capacity]]

assert choose_reminders(eligible_learners, 2) == ["acct-47", "acct-94"]''',
    'For N eligible learners, sorting costs O(N log N) time and O(N) space; a bounded heap can reduce selection to O(N log K). Constrained optimization, control-lane allocation and monitoring add operational cost. The largest risk is an overconfident uplift estimate near the net-value threshold.',
    ['Do not fill capacity with negative-net-value actions.', 'Do not evaluate one eligibility rule and serve another.', 'Do not remove the randomized control lane after an early positive result.'],
    ['machine-learning/uplift-question-and-randomized-event-contract','machine-learning/overlap-and-heterogeneity-diagnostics','machine-learning/uplift-ranking-and-policy-value-evaluation','machine-learning/intervention-uplift-release-project','online-experimentation/ramp-rollback-and-decision-packet'])


add('intervention-uplift-release-project',
    'Project: release an evidence-backed lesson-reminder policy',
    'A reminder-policy release joins randomized assignment logs, cross-fitted uplift estimates, held-out policy value, contact limits and live guardrails.', [
    ('Specify the intervention', 'At 09:00, a learner who is eligible and has not completed the current lesson may receive one reminder. The primary outcome is completion within seven days; opt-out and complaint events are guardrails. Freeze the reminder text, delivery channel, time zone and seven-day window. [[machine-learning/uplift-question-and-randomized-event-contract|The target contract]] determines which decision episodes enter analysis.'),
    ('Prepare evidence in order', 'Audit one row per decision and verify logged assignment probability. Keep a randomized holdout with both arms in every planned target segment. Wait for outcome maturity, split by learner and calendar time, fit S- and T-learner baselines, then fit a cross-fitted augmented weighting model only if its added complexity improves held-out policy value. [[machine-learning/s-and-t-learner-treatment-effect-baselines|Baselines]] and [[machine-learning/cross-fitted-doubly-robust-uplift-scores|cross-fitting]] answer different failure modes.'),
    ('Review support and uncertainty', 'Report propensity distribution, arm counts and effective sample size for high- and low-score bands. On the untouched randomized period, compare the proposed top-capacity policy with no reminders and with the prior uniform policy. Show effect uncertainty by learner-level resampling; a positive point estimate whose interval includes material loss is not a release case. [[machine-learning/overlap-and-heterogeneity-diagnostics|Overlap checks]] can remove unsupported segments before any rollout.'),
    ('Replay the actual serving rule', 'Apply opt-outs, contact cooldown, positive net value and a daily cap of 24 in the same order in offline evaluation and production. Keep a randomized measurement lane. Record model version, eligibility version, decision timestamp, action probability, chosen action and reason. [[machine-learning/capacity-constrained-treatment-policy|Capacity-constrained policy design]] explains the order; [[machine-learning/uplift-ranking-and-policy-value-evaluation|policy-value evaluation]] measures the complete rule.'),
    ('Set a release and rollback gate', 'The packet below represents a failed overlap check, so it blocks release despite positive estimated value. The human review should also inspect assignment-ratio defects, immature outcomes, opt-out spikes and any complaint harm. During the ramp, stop new reminders if the log pipeline fails or a guardrail breaches its declared threshold; restore the previous policy and retain the randomized comparison for diagnosis.')],
    '''release_packet = {
    "assignment_log_complete": True,
    "outcome_window_mature": True,
    "randomization_check_passed": True,
    "overlap_check_passed": False,
    "incremental_completions_lower_bound": 2.4,
    "daily_contact_capacity": 24,
    "planned_daily_contacts": 19,
    "opt_out_guardrail_passed": True,
}

def review_reminder_release(packet):
    failures = []
    for check in ("assignment_log_complete", "outcome_window_mature",
                  "randomization_check_passed", "overlap_check_passed",
                  "opt_out_guardrail_passed"):
        if not packet[check]:
            failures.append(check)
    if packet["incremental_completions_lower_bound"] <= 0:
        failures.append("incremental_value_uncertain")
    if packet["planned_daily_contacts"] > packet["daily_contact_capacity"]:
        failures.append("capacity_exceeded")
    return {"release": not failures, "failures": failures}

assert review_reminder_release(release_packet) == {
    "release": False, "failures": ["overlap_check_passed"]}''',
    'The packet check is O(1); producing trustworthy fields requires event reconciliation, repeated nuisance fitting, grouped uncertainty estimates and live guardrail monitoring. Randomized holdout consumes contact opportunity but measures whether the policy still helps after user behavior and content change.',
    ['Do not approve from a positive point estimate when support or uncertainty fails.', 'Do not drop the control arm during rollout.', 'Do not claim a live gain from an offline score without checking the served eligibility and capacity rules.'],
    ['machine-learning/uplift-question-and-randomized-event-contract','machine-learning/s-and-t-learner-treatment-effect-baselines','machine-learning/cross-fitted-doubly-robust-uplift-scores','machine-learning/overlap-and-heterogeneity-diagnostics','machine-learning/uplift-ranking-and-policy-value-evaluation','machine-learning/capacity-constrained-treatment-policy','online-experimentation/ramp-rollback-and-decision-packet'])


publish_batch(
    lessons,
    module_title='Uplift modeling and intervention decisions',
    module_summary='Estimate who benefits from an action, test policy value on randomized evidence and release a capacity-limited treatment rule.',
    project_heading='Lesson-reminder uplift release project',
    crosslinks=[
        ('machine-learning/decision-threshold-and-cost', 'machine-learning/capacity-constrained-treatment-policy'),
        ('machine-learning/group-and-time-validation', 'machine-learning/s-and-t-learner-treatment-effect-baselines'),
        ('machine-learning/inverse-propensity-policy-value', 'machine-learning/uplift-ranking-and-policy-value-evaluation'),
        ('causal-inference/estimand-and-counterfactual-unit', 'machine-learning/uplift-question-and-randomized-event-contract'),
        ('causal-inference/overlap-and-weighting-diagnostics', 'machine-learning/overlap-and-heterogeneity-diagnostics'),
        ('online-experimentation/exposure-and-event-logging', 'machine-learning/uplift-question-and-randomized-event-contract'),
        ('online-experimentation/ramp-rollback-and-decision-packet', 'machine-learning/intervention-uplift-release-project'),
    ],
    sort_start=6800,
)
