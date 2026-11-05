"""Add original contextual-bandit and off-policy-evaluation lessons."""
from ml_fixture_writer_20261005 import publish_batch

lessons = []


def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='machine-learning/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))


add('contextual-bandit-action-logging-and-support',
    'Contextual bandit action logging and support',
    'A contextual bandit records the context, available actions, selected action, selection probability and eventual reward for each decision.', [
    ('Define one decision at a time', 'A warehouse can either send a shipment to a rapid review lane or keep the standard lane. At intake, the routing system sees backlog and service tier, chooses one action, and later observes the outcome under that action. The outcome for the action not taken is missing. This is a different data shape from a fully labeled classifier: the logged reward belongs only to the selected action. [[machine-learning/decision-threshold-and-cost|Decision costing]] explains why the action, rather than a score alone, is the object of evaluation.'),
    ('Record the probability that produced the action', 'A logging policy can choose rapid review with probability 0.25 in one context and 0.60 in another. Save the probability assigned to the action actually taken at decision time. Recomputing it from a later policy version loses the information needed for inverse-propensity evaluation. Log the candidate action set, policy version, feature snapshot, action time and reward-ready time with an immutable decision ID. [[machine-learning/prediction-time-feature-availability|Feature timing]] prevents post-decision values from entering context.'),
    ('Check support before counterfactual analysis', 'A proposed policy must only choose actions that the logging policy had a nonzero chance of taking in matching contexts. If rapid review was forbidden for premium shipments, no logged record can identify its effect there. A small nonzero chance may technically provide support but yield a high-variance estimate. The code checks probabilities and reports the minimum observed selection probability; it cannot prove support for every unobserved context. [[machine-learning/inverse-propensity-policy-value|The IPS lesson]] makes the consequence explicit.'),
    ('Keep eligibility separate from preference', 'Some shipments are legally or operationally ineligible for rapid review. The candidate policy must obey the same action constraints; an exploration scheme must never override them. Record why an action was unavailable. Otherwise a missing action might be mistaken for a random draw and a candidate could be evaluated on impossible decisions. [[machine-learning/exploration-budget-and-guardrails|Exploration controls]] make the action set explicit.'),
    ('Treat delayed rewards as data, not zeros', 'The handoff outcome may arrive after dispatch or be corrected later. Join it by decision ID and apply a declared maturity window. An incomplete reward is not a failed shipment. Record all decisions, including those still pending, so evaluation can expose selective observation. [[machine-learning/delayed-bandit-rewards-and-maturity|Reward maturity]] handles that clock.')],
    '''# Decision ID, context, eligible actions, selected action, selection probability.
decision_log = [
    ("R801", "high-backlog", ("standard", "rapid"), "rapid", 0.35),
    ("R802", "low-backlog", ("standard", "rapid"), "standard", 0.80),
    ("R803", "premium", ("standard",), "standard", 1.00),
]

def validate_action_log(rows):
    seen_ids = set()
    lowest_probability = 1.0
    for decision_id, context, eligible, action, action_probability in rows:
        if decision_id in seen_ids or not context or action not in eligible:
            raise ValueError("invalid or duplicate decision")
        if not 0 < action_probability <= 1:
            raise ValueError("invalid logged action probability")
        seen_ids.add(decision_id)
        lowest_probability = min(lowest_probability, action_probability)
    return {"decisions": len(seen_ids), "min_logged_probability": lowest_probability}

summary = validate_action_log(decision_log)
assert summary == {"decisions": 3, "min_logged_probability": 0.35}''',
    'Validating N decision records costs O(N) time and O(N) IDs for duplicate detection. Logging one probability is cheap; storing immutable feature snapshots, policy versions, eligibility rules and later rewards is the substantial systems work. No estimator can reconstruct a missing selection probability reliably after the policy changes.',
    ['Do not attach the reward of the chosen action to every available action.', 'Do not infer a historical selection probability from the current policy.', 'Do not treat an ineligible action as merely an unchosen eligible action.'],
    ['machine-learning/inverse-propensity-policy-value','machine-learning/doubly-robust-contextual-policy-value','machine-learning/exploration-budget-and-guardrails','machine-learning/delayed-bandit-rewards-and-maturity'])


add('inverse-propensity-policy-value',
    'Inverse-propensity policy value',
    'Inverse-propensity scoring estimates the reward of a candidate action policy by weighting observed rewards according to candidate and logging action probabilities.', [
    ('Evaluate a declared target policy', 'A proposed routing policy gives each eligible action a probability in each recorded context. For each logged decision, divide its candidate probability for the action actually taken by the probability that the logging policy assigned that action. Multiply the observed reward by this ratio, then average over all decisions. A deterministic candidate gives zero weight to rows where the logging action differs. [[machine-learning/contextual-bandit-action-logging-and-support|The action log]] supplies the denominator.'),
    ('Understand the assumptions', 'The logging probability must describe the actual randomized selection after eligibility constraints, and the observed reward must be attached to the chosen action. Candidate actions need positive logging support. Context and action versions must be consistent. If operators secretly override assigned actions in a way the log omits, the recorded probability is wrong. The estimator then need not identify the proposed policy value. [[machine-learning/exploration-budget-and-guardrails|Guardrails]] must be visible in the log.'),
    ('Report weight concentration', 'Rarely selected actions receive large weights. The code reports raw IPS, a self-normalized ratio and effective sample size. Self-normalization can reduce instability but generally changes the finite-sample bias; it is a diagnostic companion, not a silent substitute for raw IPS. Display the largest weights and their contributing cases. A handful of rewarded shipments must not be presented as a certain operational gain. [[machine-learning/doubly-robust-contextual-policy-value|The augmented propensity estimate]] is another comparison, with its own assumptions.'),
    ('Keep policy selection separate from evaluation', 'If many candidate policies are tried and the one with the largest IPS estimate is reported on those same cases, selection optimism returns. Use historical development logs to design the candidate, then a later untouched logged cohort for evaluation. Repeated decisions for the same depot or customer may require clustered uncertainty. [[machine-learning/group-and-time-validation|The time split]] preserves that boundary.'),
    ('Check reward definition before arithmetic', 'A rapid-lane reward might combine timely handoff with staffing cost. Declare units, observation window and missing-reward rule before comparing policies. Off-policy estimators cannot fix a reward that omits the downstream cost the business actually cares about. [[machine-learning/delayed-bandit-rewards-and-maturity|Reward maturity]] covers unresolved outcomes; [[machine-learning/bandit-policy-release-review-project|the release review]] checks the full policy.')],
    '''# Selected action, logging probability, candidate probability, mature reward.
logged_decisions = [
    ("rapid", 0.25, 1.0, 1.0),
    ("standard", 0.75, 0.0, 0.0),
    ("rapid", 0.50, 1.0, 0.0),
    ("standard", 0.50, 0.0, 1.0),
]

def policy_value(rows):
    if not rows:
        raise ValueError("no mature logged decisions")
    weighted_rewards = 0.0
    weights = []
    for action, logging_probability, candidate_probability, reward in rows:
        if action not in {"rapid", "standard"}:
            raise ValueError("unknown action")
        if not 0 < logging_probability <= 1 or not 0 <= candidate_probability <= 1:
            raise ValueError("invalid policy probability")
        weight = candidate_probability / logging_probability
        weighted_rewards += weight * reward
        weights.append(weight)
    raw_ips = weighted_rewards / len(rows)
    normalized = weighted_rewards / sum(weights) if sum(weights) else None
    effective_size = sum(weights) ** 2 / sum(weight ** 2 for weight in weights)
    return raw_ips, normalized, effective_size

ips, normalized, effective_size = policy_value(logged_decisions)
assert ips == 1.0
assert normalized == 2 / 3
assert effective_size == 1.8''',
    'For N mature decisions, scoring takes O(N) time and O(1) running memory; the teaching implementation keeps O(N) weights for inspection. Effective sample size can be far smaller than N when probabilities are small. Logging, reward maturity and credible uncertainty estimates usually dominate compute.',
    ['Do not divide by a policy score that was not the actual selection probability.', 'Do not compare a candidate action with zero logging support.', 'Do not report a self-normalized estimate without naming its changed bias behavior.'],
    ['machine-learning/contextual-bandit-action-logging-and-support','machine-learning/doubly-robust-contextual-policy-value','machine-learning/exploration-budget-and-guardrails','machine-learning/bandit-policy-release-review-project'])


add('doubly-robust-contextual-policy-value',
    'Augmented propensity policy value',
    'An augmented propensity estimate combines a reward model for candidate actions with a propensity-weighted correction for observed reward errors.', [
    ('Build two separate components', 'For each context, predict reward under each eligible action using a reward model fitted without its evaluation outcome. Average those predictions under the candidate policy. Then add a correction: candidate probability divided by logged selection probability, multiplied by observed reward minus predicted reward for the logged action. The code handles a deterministic rapid-lane candidate and supplied reward estimates. [[machine-learning/inverse-propensity-policy-value|IPS]] provides the correction term and its support requirement.'),
    ('Read the name precisely', 'Under the usual contextual-bandit identification assumptions, the estimate can remain consistent if either the reward model or the logging propensity model is correctly specified. That does not mean it is immune to missing actions, incorrect reward definitions, changed outcomes, extreme weights or leakage. If logging propensities are exact by design, the reward model can reduce variance, but a small example cannot verify that advantage. [[machine-learning/contextual-bandit-action-logging-and-support|Action logging]] is still foundational.'),
    ('Keep nuisance fitting away from evaluation outcomes', 'Fit reward estimates on an earlier or cross-fitted partition; do not evaluate each row with a reward model trained on its own observed reward. Record the reward-model version and the features available at the original decision. A model that uses a post-routing signal introduces a different form of leakage even if its prediction error looks low. [[machine-learning/leakage-safe-preprocessing-pipeline|Pipeline isolation]] and [[machine-learning/prediction-time-feature-availability|feature timing]] both apply.'),
    ('Diagnose rather than trust one number', 'Report the direct reward-model average, raw IPS, augmented estimate, largest weights and support by relevant context. Large disagreement among estimators deserves investigation. It is not a rule to pick the most favorable number. Repeated depot events and an adaptive logging policy complicate intervals; use an uncertainty method that respects those dependencies. [[machine-learning/paired-bootstrap-model-gain-intervals|Paired evaluation]] offers a starting point, not a blanket solution.'),
    ('Protect the decision boundary', 'An offline estimate is a screening tool. Promotion requires operational eligibility, latency, review capacity, mature reward coverage and a bounded prospective plan when policy actions themselves affect future outcomes. [[machine-learning/bandit-policy-release-review-project|The release project]] combines these conditions.')],
    '''# Logged action, logging probability, observed reward, predicted reward
# for standard and rapid actions from a separately fitted reward model.
records = [
    ("rapid", 0.50, 1.0, 0.2, 0.6),
    ("standard", 0.75, 0.0, 0.3, 0.7),
    ("rapid", 0.25, 0.0, 0.4, 0.5),
    ("standard", 0.50, 1.0, 0.5, 0.8),
]

def rapid_policy_dr(rows):
    terms = []
    for action, logged_probability, reward, standard_estimate, rapid_estimate in rows:
        if action not in {"standard", "rapid"} or not 0 < logged_probability <= 1:
            raise ValueError("invalid logged action")
        chosen_estimate = rapid_estimate if action == "rapid" else standard_estimate
        correction = ((reward - chosen_estimate) / logged_probability
                      if action == "rapid" else 0.0)
        terms.append(rapid_estimate + correction)
    return sum(terms) / len(terms)

estimate = rapid_policy_dr(records)
assert round(estimate, 3) == 0.35''',
    'Scoring N rows costs O(N) time and O(1) running memory when streamed, beyond fitting the reward model. That fit must be repeated across suitable folds or historical partitions to avoid evaluation leakage. Extreme inverse probabilities can still create high variance even when the reward model is useful.',
    ['Do not fit and evaluate the reward model on the same row without a valid split.', 'Do not read the two-part construction as protection against missing support or bad reward measurement.', 'Do not select the largest estimate among methods after seeing results.'],
    ['machine-learning/inverse-propensity-policy-value','machine-learning/contextual-bandit-action-logging-and-support','machine-learning/delayed-bandit-rewards-and-maturity','machine-learning/bandit-policy-release-review-project'])


add('exploration-budget-and-guardrails',
    'Exploration budget and action guardrails',
    'An exploration policy assigns nonzero probability to eligible alternatives while respecting hard action constraints and a declared intervention budget.', [
    ('Start with the eligible set', 'At a depot, some shipments cannot use the rapid lane because capacity or handling rules forbid it. Filter those actions before randomization. The code uses an epsilon-greedy choice over the resulting action set and returns the exact probability of the chosen action. No exploration probability can make an ineligible action safe. [[machine-learning/contextual-bandit-action-logging-and-support|The log schema]] must retain this action set and the reason it changed.'),
    ('Know the actual probability', 'For K eligible actions, epsilon-greedy selects the currently preferred action with probability one minus epsilon plus epsilon divided by K, and each other action with epsilon divided by K. Record that probability after all guardrails, throttles and fallbacks have executed. If operators override a draw or a budget cap reroutes it, the pre-override probability is not the probability of the action delivered. [[machine-learning/inverse-propensity-policy-value|IPS]] fails when that denominator is wrong.'),
    ('Budget learning separately from service risk', 'A five-percent exploration budget is not permission to risk five percent of critical shipments. Define which contexts permit experimentation, maximum rapid-lane volume, per-site load and stop conditions. Compare reward and harm, not just average clicks or short-term speed. For high-stakes decisions, a randomized policy may be inappropriate without a formal review. [[machine-learning/group-error-gaps-and-policy-audit|Group error]] and [[machine-learning/selective-prediction-and-review-capacity|review capacity]] are operating constraints.'),
    ('Distinguish learning from evaluation', 'The same adaptive log can support learning, but candidate selection and evaluation should be separated by time or other valid design. If exploration probabilities shrink to nearly zero for alternatives, counterfactual estimates become unstable. Reserve a controlled, policy-approved evaluation cohort with enough support rather than trying to rescue a deterministic history by arithmetic. [[machine-learning/doubly-robust-contextual-policy-value|Augmented propensity evaluation]] cannot create data for absent actions.'),
    ('Account for delayed outcomes', 'A policy update based only on quickly observed wins may prefer actions with short reward latency. Freeze a maturity rule, monitor pending outcomes and keep a rollback path when changing exploration. [[machine-learning/delayed-bandit-rewards-and-maturity|The reward guide]] separates pending cases from failures.')],
    '''import random

def choose_lane(eligible_actions, preferred_action, epsilon, rng):
    if not eligible_actions or preferred_action not in eligible_actions:
        raise ValueError("preferred action must be eligible")
    if not 0 <= epsilon <= 1:
        raise ValueError("epsilon outside probability range")
    action_count = len(eligible_actions)
    chosen = (rng.choice(eligible_actions) if rng.random() < epsilon
              else preferred_action)
    propensity = (1 - epsilon if chosen == preferred_action else 0)
    propensity += epsilon / action_count
    return chosen, propensity

local_rng = random.Random(47)
eligible = ("standard", "rapid")
decision = choose_lane(eligible, "standard", 0.20, local_rng)
assert decision[0] in eligible
assert decision[1] in {0.10, 0.90}
forced_standard = choose_lane(("standard",), "standard", 0.20, local_rng)
assert forced_standard == ("standard", 1.0)''',
    'Selecting among K eligible actions costs O(K) if constructing and sampling a list, with O(K) action-set storage; the simple code receives that list. Policy logs and safeguards must scale with decisions. More exploration can improve support but consumes real operational capacity and may impose measurable harm.',
    ['Do not explore actions forbidden by operational rules.', 'Do not log the pre-override probability as if it generated the final action.', 'Do not treat a nominal exploration percentage as an acceptable harm budget.'],
    ['machine-learning/contextual-bandit-action-logging-and-support','machine-learning/inverse-propensity-policy-value','machine-learning/delayed-bandit-rewards-and-maturity','machine-learning/bandit-policy-release-review-project'])


add('delayed-bandit-rewards-and-maturity',
    'Delayed bandit rewards and outcome maturity',
    'Bandit rewards should be evaluated only after a declared observation window, while pending outcomes and late corrections remain visible in the denominator.', [
    ('Define when a reward exists', 'For a rapid-lane routing decision, the reward might be an on-time handoff minus a staffing penalty. An on-time status cannot be finalized until the handoff window closes; some cases may remain disputed. Record decision time, outcome deadline, actual label-ready time and current status separately. The code partitions a log into mature and pending records at a fixed audit time. [[machine-learning/contextual-bandit-action-logging-and-support|The action log]] links those records by immutable ID.'),
    ('Do not call pending cases failures', 'If rapid-lane successes tend to be recorded quickly while standard-lane failures appear after several days, scoring only currently labeled cases biases a comparison. The opposite pattern is also possible. Report how many decisions have matured by action, depot and time cohort. A row with a missing reward is not automatically a zero reward. [[machine-learning/feature-drift-and-delayed-label-monitoring|Delayed-label monitoring]] applies the same principle to supervised models.'),
    ('Handle censoring as a design issue', 'For some shipments, the final outcome may never be recorded. A fixed maturity window reduces ordinary delay but does not solve outcome-dependent missingness. Trace missing labels, compare data-collection routes and consider sensitivity ranges. Inverse-propensity weights correct action selection under their assumptions; they do not automatically correct selective reward observation. [[machine-learning/inverse-propensity-policy-value|IPS]] therefore needs a mature, sufficiently observed cohort.'),
    ('Separate interim and final rewards', 'A quick scan confirmation is a proxy for the eventual service outcome. If used for fast learning, label it as an interim reward and compare it with the final reward on matured cases. Do not change a production policy on a proxy gain without checking downstream harm. [[data-science/proxy-measurement-and-label-error|Proxy measurement]] explains how apparent improvement can reflect the wrong target.'),
    ('Keep the evaluation clock fixed', 'Specify the audit time and maturity age before viewing outcome rates. A later backfill can update an analysis but should not rewrite what the model knew at a historical decision. For policy comparison, use the same reward window and case eligibility for every candidate. [[machine-learning/bandit-policy-release-review-project|The release review]] refuses a value estimate built from incompatible clocks.')],
    '''# Decision ID, chosen lane, decision day, reward-ready day, final reward.
outcomes = [
    ("R901", "rapid", 1, 4, 1.0),
    ("R902", "standard", 2, 7, 0.0),
    ("R903", "rapid", 4, 9, 1.0),
    ("R904", "standard", 5, None, None),
]

def reward_maturity(rows, audit_day):
    mature, pending = [], []
    for decision_id, lane, decision_day, ready_day, reward in rows:
        if ready_day is not None and ready_day <= audit_day:
            if reward is None or ready_day < decision_day:
                raise ValueError("invalid mature reward")
            mature.append((decision_id, lane, reward))
        else:
            pending.append((decision_id, lane))
    return mature, pending

mature, pending = reward_maturity(outcomes, audit_day=7)
assert [decision_id for decision_id, _, _ in mature] == ["R901", "R902"]
assert len(pending) == 2''',
    'Partitioning N decisions costs O(N) time and O(N) memory when retaining case lists, or O(A) counters for A actions when streamed. The difficult costs are durable joins, label-quality review and waiting long enough for the outcome to represent the declared reward.',
    ['Do not encode pending or unknown rewards as zero.', 'Do not compare actions with different maturity windows.', 'Do not assume action-selection weighting fixes missing-outcome bias.'],
    ['machine-learning/contextual-bandit-action-logging-and-support','machine-learning/inverse-propensity-policy-value','machine-learning/exploration-budget-and-guardrails','machine-learning/bandit-policy-release-review-project'])


add('bandit-policy-release-review-project',
    'Contextual bandit policy release review project',
    'Review a rapid-lane routing candidate with logged action probabilities, eligible-action support, mature rewards, offline value estimates and a bounded pilot plan.', [
    ('Freeze the decision record', 'Specify context available at intake, eligible lanes, logging-policy version, selection probability and the reward contract. For every decision, save the chosen action and immutable case ID before later outcomes arrive. [[machine-learning/contextual-bandit-action-logging-and-support|The logging lesson]] defines the minimum record. Exclude any action that safety or service rules make ineligible.'),
    ('Check identification before value', 'Audit support for every candidate action and context. Compute raw inverse-propensity value, largest weights and effective sample size; compare with an independently fitted augmented propensity estimate. A model-only estimate and a weighting estimate that sharply disagree call for investigation, not a favorable-number choice. [[machine-learning/inverse-propensity-policy-value|IPS]] and [[machine-learning/doubly-robust-contextual-policy-value|augmented evaluation]] expose distinct failures.'),
    ('Wait for a common reward clock', 'Define when the handoff result is mature, report pending and missing outcomes by action, and retain staffing cost in the reward. A quicker proxy may help monitoring but cannot silently replace the final target. [[machine-learning/delayed-bandit-rewards-and-maturity|Reward maturity]] supplies the eligibility rule.'),
    ('Plan the bounded live comparison', 'Offline estimates screen candidates; they do not prove how the challenger would affect outcomes once its actions change the system. Review exploration eligibility, per-site capacity, stop conditions, monitoring ownership and rollback. If a prospective randomized comparison is authorized, preserve its assignment and actual action logs. [[machine-learning/exploration-budget-and-guardrails|The exploration guide]] keeps probabilities and constraints aligned.'),
    ('Record a decision, not a metric alone', 'The code checks whether an evidence packet contains necessary artifacts; it cannot certify a good policy. Attach numerical estimates with uncertainty, sample support, group-level harms and an explicit owner for the pilot. If any condition is missing, hold the release discussion rather than treating it as passed.')],
    '''def bandit_review_gate(packet):
    requirements = {
        "action_support_checked": "action support",
        "propensities_logged": "logged probabilities",
        "reward_maturity_audited": "reward maturity",
        "weight_concentration_reported": "weight concentration",
        "group_harms_reviewed": "group harms",
        "capacity_guardrail_set": "capacity guardrail",
        "rollback_owner_named": "rollback owner",
    }
    blockers = [label for key, label in requirements.items() if not packet.get(key)]
    return "eligible for pilot review" if not blockers else "hold: " + ", ".join(blockers)

rapid_lane_packet = {
    "action_support_checked": True,
    "propensities_logged": True,
    "reward_maturity_audited": False,
    "weight_concentration_reported": True,
    "group_harms_reviewed": True,
    "capacity_guardrail_set": False,
    "rollback_owner_named": True,
}
assert bandit_review_gate(rapid_lane_packet) == (
    "hold: reward maturity, capacity guardrail"
)''',
    'The checklist is O(K) for K requirements. Offline IPS and augmented propensity scoring each scan N mature decisions in O(N) time. The true operating cost lies in safe randomized support, delayed reward collection, candidate serving, monitoring and the ability to reverse a harmful policy.',
    ['Do not promote a candidate because one offline estimator looks favorable.', 'Do not evaluate an action without logged support or a valid selection probability.', 'Do not call a pending outcome a failure or omit capacity from the reward contract.'],
    ['machine-learning/contextual-bandit-action-logging-and-support','machine-learning/inverse-propensity-policy-value','machine-learning/doubly-robust-contextual-policy-value','machine-learning/exploration-budget-and-guardrails','machine-learning/delayed-bandit-rewards-and-maturity','machine-learning/group-error-gaps-and-policy-audit'])


publish_batch(
    lessons,
    module_title='Contextual bandits and policy evidence',
    module_summary='Log decisions, evaluate alternative actions offline and review exploration and reward maturity.',
    project_heading='Bandit policy release review',
    crosslinks=[
        ('machine-learning/decision-threshold-and-cost', lessons[0]['path']),
        ('machine-learning/contextual-bandit-action-logging-and-support', lessons[1]['path']),
        ('machine-learning/paired-bootstrap-model-gain-intervals', lessons[2]['path']),
        ('machine-learning/selective-prediction-and-review-capacity', lessons[3]['path']),
        ('machine-learning/feature-drift-and-delayed-label-monitoring', lessons[4]['path']),
        ('machine-learning/distribution-shift-response-project', lessons[5]['path']),
    ],
    sort_start=5300,
)
