"""Add original sequential decision and reinforcement-learning lessons."""
from ml_fixture_writer_20261005 import publish_batch

lessons = []


def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='machine-learning/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))


add('sequential-decision-state-and-reward-contract',
    'Sequential decision state and reward contract',
    'A sequential decision process records the state before an action, the action taken, immediate reward, next state and whether the episode has ended.', [
    ('Distinguish a sequence from a one-step choice', 'A rapid-lane assignment has an immediate result but may also change the next queue length and the choices available to later shipments. When actions alter future state, evaluating each intake as an isolated bandit can miss delayed capacity cost. Define a decision interval, state snapshot, eligible actions, transition and terminal condition. [[machine-learning/contextual-bandit-action-logging-and-support|The bandit log]] remains useful for one-step action probabilities; sequential evaluation also needs next-state records.'),
    ('Put enough history into the state', 'A stock-control state containing only current bin level may be inadequate if an outstanding replenishment order will arrive tomorrow. The Markov assumption says that, conditional on recorded state and action, earlier history adds no information to the next-state and reward distribution. It is an assumption to test, not a label attached to any convenient feature vector. The code validates transition shape and legal actions for a small warehouse process.'),
    ('Define reward from actual operations', 'Dispatching a parcel can earn service value, replenishing costs labor, and a shortage can impose a later penalty. Choose units and timing before optimizing; otherwise an agent may improve the logged immediate score while increasing real delays. Include capacity, safety and prohibited-action rules outside the reward as hard constraints where necessary. [[machine-learning/decision-threshold-and-cost|Cost-based decisions]] show why the business action contract matters.'),
    ('Track episode boundaries', 'A terminal state has no future value to bootstrap. A time-limit cutoff can be a truncation rather than a genuine terminal business outcome; those cases may need different handling. Record both the stop reason and reward maturity. [[machine-learning/temporal-difference-return-and-terminal|Temporal-difference updates]] use this distinction; [[machine-learning/delayed-bandit-rewards-and-maturity|delayed rewards]] affect the input log.'),
    ('Check who generated the trajectory', 'A historical policy determines which state-action pairs appear in data. A candidate that repeatedly chooses a rare action can move into states the log never visited. A single-step propensity check does not cover that entire path. [[machine-learning/offline-trajectory-support-and-simulator-risk|Offline trajectory support]] audits the sequence-level gap before release.')],
    '''eligible_actions = {
    "low-stock": {"replenish", "wait"},
    "ready-stock": {"dispatch", "hold"},
    "closed": set(),
}
transitions = [
    ("low-stock", "replenish", -2.0, "ready-stock", False),
    ("ready-stock", "dispatch", 5.0, "low-stock", False),
    ("low-stock", "wait", -7.0, "closed", True),
]

def validate_trajectory(rows, action_map):
    for position, (state, action, reward, next_state, terminated) in enumerate(rows):
        if action not in action_map[state] or next_state not in action_map:
            raise ValueError("invalid state-action transition")
        if terminated != (next_state == "closed"):
            raise ValueError("terminal state mismatch")
        if position and state != rows[position - 1][3]:
            raise ValueError("broken trajectory chain")
    return len(rows)

assert validate_trajectory(transitions, eligible_actions) == 3''',
    'Validating T recorded transitions costs O(T) time and O(SA) action-map storage for S states and their eligible actions. Real logs also need timestamps, policy versions, state history, reward maturity and constraints. A larger state space increases collection and coverage demands faster than simple validation cost.',
    ['Do not call a one-step score the value of a policy that changes future state.', 'Do not mark every time limit as a true terminal business outcome.', 'Do not encode a safety constraint only as a small negative reward.'],
    ['machine-learning/bellman-value-iteration-for-stock-control','machine-learning/temporal-difference-return-and-terminal','machine-learning/q-learning-control-and-exploration','machine-learning/sequential-policy-review-project'])


add('bellman-value-iteration-for-stock-control',
    'Bellman value iteration for stock control',
    'Value iteration repeatedly updates each state with the best expected immediate reward plus discounted next-state value when a transition model is known.', [
    ('Define the finite process first', 'A low-stock bin may replenish at a labor cost or wait and risk shortage. A ready bin may dispatch for service value or hold and incur storage cost. The code uses deterministic transitions to make every calculation visible; a real transition model can distribute probability across several next states. [[machine-learning/sequential-decision-state-and-reward-contract|The state contract]] defines actions, reward units and terminal behavior before any Bellman update.'),
    ('Apply synchronous updates', 'At each sweep, compute every new value from the previous sweep, not partially updated values. For each action, add immediate reward to gamma times the previous next-state value, then choose the best eligible action. The terminal value stays zero. With gamma below one and bounded rewards, this finite discounted update converges under the stated model; the stopping tolerance controls numerical approximation, not model truth.'),
    ('Extract policy after convergence', 'A state value estimates the best discounted return from that state. The policy selects the action achieving the best one-step reward plus continued value. The code finds replenishment and dispatch preferable in its invented process. Those actions are consequences of its stated rewards and transitions, not general advice for a warehouse. [[machine-learning/q-learning-control-and-exploration|Q-learning]] addresses the case where transitions are sampled rather than supplied.'),
    ('Challenge the model, not just the solver', 'A perfect value-iteration implementation can optimize a wrong simulator. Check transition frequencies on held-out operational data, especially low-frequency shortages and changes caused by the candidate action. If capacity or lead time is omitted from state, planning may assume replenishment is instant. [[machine-learning/offline-trajectory-support-and-simulator-risk|Simulator risk]] limits offline claims.'),
    ('Report cost and horizon', 'The discount factor describes how later rewards enter this mathematical objective; it should not hide long-term harms merely to make computation easy. Report gamma, reward scale, termination rule, convergence tolerance and sensitivity to alternative transition estimates. [[machine-learning/sequential-policy-review-project|The release review]] requires those artifacts.')],
    '''discount = 0.80
model = {
    "low-stock": {
        "replenish": [(-2.0, "ready-stock", 1.0)],
        "wait": [(-7.0, "closed", 1.0)],
    },
    "ready-stock": {
        "dispatch": [(5.0, "low-stock", 1.0)],
        "hold": [(-1.0, "ready-stock", 1.0)],
    },
    "closed": {},
}

def action_value(outcomes, state_values, gamma):
    if abs(sum(probability for _, _, probability in outcomes) - 1) > 1e-9:
        raise ValueError("transition probabilities do not sum to one")
    return sum(probability * (reward + gamma * state_values[next_state])
               for reward, next_state, probability in outcomes)

values = {state: 0.0 for state in model}
for sweep in range(180):
    updated = {state: (max(action_value(outcomes, values, discount)
                           for outcomes in actions.values()) if actions else 0.0)
               for state, actions in model.items()}
    change = max(abs(updated[state] - values[state]) for state in model)
    values = updated
    if change < 1e-9:
        break
policy = {state: max(actions, key=lambda action:
                     action_value(actions[action], values, discount))
          for state, actions in model.items() if actions}
assert policy == {"low-stock": "replenish", "ready-stock": "dispatch"}
assert abs(values["low-stock"] - 5.5555555556) < 1e-5''',
    'For S states, at most A actions per state, O possible next-state outcomes per action and K sweeps, direct value iteration costs O(KSAO) time and O(S) working values, excluding model storage. Large or continuous state spaces need approximation and additional validation. Exact convergence of a small model does not establish operational accuracy.',
    ['Do not use newly updated state values in some states and old values in others while claiming a synchronous sweep.', 'Do not bootstrap value from a true terminal state.', 'Do not treat an optimal policy for an estimated model as proven optimal in operations.'],
    ['machine-learning/sequential-decision-state-and-reward-contract','machine-learning/temporal-difference-return-and-terminal','machine-learning/q-learning-control-and-exploration','machine-learning/sequential-policy-review-project'])


add('temporal-difference-return-and-terminal',
    'Episode returns, temporal difference and terminal states',
    'An episode return sums discounted observed rewards, while a temporal-difference update changes a state estimate using the next reward and a bootstrapped next-state estimate.', [
    ('Keep the two targets separate', 'A completed stock-control episode reveals a realized sequence of rewards. Backward return calculation uses the rewards through the end. A one-step temporal-difference update uses the current reward plus a discounted estimate of the next state; it can update before the episode finishes. Neither is automatically unbiased for an operational policy when the log selectively records episodes. [[machine-learning/sequential-decision-state-and-reward-contract|The trajectory contract]] supplies the event order.'),
    ('Stop bootstrapping at a real terminal', 'When the process reaches closed, its continuation value is zero. The code calculates all discounted returns for one fixed episode and updates a state estimate with a terminal transition. A time-limit truncation may still have future value; treating every cutoff as terminal can bias learning. Log why the episode stopped. [[machine-learning/delayed-bandit-rewards-and-maturity|Reward maturity]] also determines whether a transition is ready for training.'),
    ('Know what each method trades', 'Full returns reflect realized later outcomes but can be variable and require completed episodes. Bootstrapping can reduce delay and variability but introduces bias from the current value estimate. Compare learning stability on held-out trajectories and across reward timings. A single illustrative episode cannot establish that one estimator is superior. [[machine-learning/q-learning-control-and-exploration|Control learning]] adds the further question of which action to choose.'),
    ('Keep behavior policy visible', 'The observed episode came from a policy that chose replenishment, dispatch and then waiting. Its returns describe those choices. They are not the value of an arbitrary alternative policy, because that alternative may visit different states. [[machine-learning/offline-trajectory-support-and-simulator-risk|Offline support]] checks what logged transitions can identify.'),
    ('Assess objective sensitivity', 'If shortage penalties are recorded late, a quick proxy can make waiting appear attractive until the final outcome arrives. Compare estimated values with mature service outcomes and staffing cost. [[machine-learning/sequential-policy-review-project|The project]] records the reward clock before policy review.')],
    '''episode = [
    ("low-stock", "replenish", -2.0, "ready-stock", False),
    ("ready-stock", "dispatch", 5.0, "low-stock", False),
    ("low-stock", "wait", -7.0, "closed", True),
]
discount = 0.80

def discounted_returns(trajectory, gamma):
    result = [0.0] * len(trajectory)
    continuation = 0.0
    for position in range(len(trajectory) - 1, -1, -1):
        _, _, reward, _, terminated = trajectory[position]
        continuation = reward + (0.0 if terminated else gamma * continuation)
        result[position] = continuation
    return result

def td_update(current_value, reward, next_value, terminated, rate, gamma):
    target = reward + (0.0 if terminated else gamma * next_value)
    return current_value + rate * (target - current_value)

returns = discounted_returns(episode, discount)
terminal_update = td_update(-1.0, -7.0, 99.0, True, 0.5, discount)
assert abs(returns[0] - (-2.48)) < 1e-9
assert terminal_update == -4.0''',
    'Backward returns over T transitions cost O(T) time and O(T) output storage; a one-step temporal-difference update is O(1) given current values. Delayed or incomplete episodes increase storage and waiting cost. Statistical uncertainty and policy-selection bias require more than this arithmetic.',
    ['Do not bootstrap from the next state after a true terminal transition.', 'Do not confuse one episode’s realized return with a population policy value.', 'Do not train on an outcome before its declared reward window has matured.'],
    ['machine-learning/sequential-decision-state-and-reward-contract','machine-learning/bellman-value-iteration-for-stock-control','machine-learning/q-learning-control-and-exploration','machine-learning/sequential-policy-review-project'])


add('q-learning-control-and-exploration',
    'Q-learning control and exploration',
    'Tabular Q-learning updates a state-action value toward observed reward plus the best estimated next-action value, while its behavior policy must still collect eligible alternatives.', [
    ('Separate behavior from update target', 'A warehouse learner may sometimes choose a less-preferred eligible action to obtain evidence. The behavior policy generates the transition. The Q-learning target uses the largest estimated next-action value, not necessarily the next action the behavior policy would take. That distinction makes this an off-policy control update. [[machine-learning/exploration-budget-and-guardrails|Exploration guardrails]] still govern what actions can actually be tried.'),
    ('Handle terminal and eligible actions', 'The code applies one update to a nonterminal low-stock transition and another to a terminal shortage transition. It looks up the maximum only among legal next actions and uses zero continuation at a true terminal. A value for a forbidden action must never be selected by a maximization routine. [[machine-learning/sequential-decision-state-and-reward-contract|The action map]] defines this legal set.'),
    ('Do not mistake a toy update for a deployment policy', 'Convergence statements for tabular Q-learning require conditions on exploration and learning rates in a stationary finite process. An adaptive warehouse with delayed rewards, shared constraints and incomplete state does not satisfy them by declaration. Audit coverage and compare a fixed safe policy on independent later episodes. [[machine-learning/offline-trajectory-support-and-simulator-risk|Offline support]] is a separate release concern.'),
    ('Inspect learning dynamics', 'Report visits by state and action, update size, realized long-run return, shortage rate and capacity incidents. A high estimated Q value for rarely tried replenishment may reflect noise or an optimistic initialization. A small maximum update is not enough to prove the system objective is correct. [[machine-learning/temporal-difference-return-and-terminal|Return and TD]] clarify the bootstrapped target.'),
    ('Keep exploration within operations', 'An epsilon-greedy or other behavior rule needs a logged selection probability after eligibility and overrides. Never explore a prohibited action merely to populate the Q table. If safe exploration is not possible, rely on a reviewed simulator or conservative policy instead of claiming new action effects from absent data. [[machine-learning/sequential-policy-review-project|The project]] asks for a bounded pilot and rollback.')],
    '''eligible = {"low-stock": ("replenish", "wait"),
            "ready-stock": ("dispatch", "hold"), "closed": ()}
q_values = {("low-stock", "replenish"): 1.0,
            ("low-stock", "wait"): -2.0,
            ("ready-stock", "dispatch"): 4.0,
            ("ready-stock", "hold"): 0.0}

def q_update(table, state, action, reward, next_state, terminated,
             legal_actions, rate=0.5, gamma=0.8):
    if action not in legal_actions[state]:
        raise ValueError("ineligible action")
    continuation = (0.0 if terminated else
                    max(table[(next_state, next_action)]
                        for next_action in legal_actions[next_state]))
    previous = table[(state, action)]
    table[(state, action)] = previous + rate * (
        reward + gamma * continuation - previous)
    return table[(state, action)]

first = q_update(q_values, "low-stock", "replenish", -2.0,
                 "ready-stock", False, eligible)
terminal = q_update(q_values, "low-stock", "wait", -7.0,
                    "closed", True, eligible)
assert abs(first - 1.1) < 1e-9
assert terminal == -4.5''',
    'One tabular update scans at most A eligible next actions, costing O(A) time and O(SA) stored values for S states and A actions. Collecting enough safe transitions is harder than table arithmetic. Function approximators add training cost and can amplify errors outside the visited state-action distribution.',
    ['Do not bootstrap from a terminal state.', 'Do not maximize over forbidden or unobserved actions without checking support.', 'Do not infer a good operational policy from a few stable-looking table updates.'],
    ['machine-learning/sequential-decision-state-and-reward-contract','machine-learning/temporal-difference-return-and-terminal','machine-learning/offline-trajectory-support-and-simulator-risk','machine-learning/sequential-policy-review-project'])


add('offline-trajectory-support-and-simulator-risk',
    'Offline trajectory support and simulator risk',
    'An offline sequential policy can enter state-action paths missing from the logged behavior, so its estimated value needs path support and a separately checked environment model.', [
    ('Look beyond one-step overlap', 'A historical stock policy may try both replenishment and waiting in low-stock states, yet never dispatch after a particular replenishment delay. A candidate that repeatedly chooses a new sequence changes the state mix. One-step action probabilities are necessary for some estimators but do not by themselves establish coverage of the resulting trajectories. [[machine-learning/contextual-bandit-action-logging-and-support|Bandit support]] is a simpler, single-decision boundary.'),
    ('Count observed state-action pairs', 'The code compares a proposed state-action plan with counts in a fixed transition log. Missing pairs are blockers for direct evidence. Counts above zero are only a coarse screen: context may be too broad, and rare pairs produce unstable estimates. Include state features, time, policy version and next-state distributions in a serious audit. [[machine-learning/sequential-decision-state-and-reward-contract|The state definition]] determines what the counts mean.'),
    ('Do not trust a learned simulator by construction', 'Value iteration can find an optimal policy for any supplied transition model, including a wrong one. Test a simulator’s one-step transitions and reward predictions on held-out episodes, then check longer rollouts for compounding error. A model that matches common dispatches can still fail on rare shortage paths that matter most. [[machine-learning/bellman-value-iteration-for-stock-control|Value iteration]] solves the stated model, not the real warehouse.'),
    ('Keep conservative alternatives', 'Where a candidate enters unsupported states, stay with a reviewed behavior policy, restrict the action set, or collect controlled evidence under operational approval. A synthetic rollout is a stress test, not observed proof. Report coverage gaps and sensitivity to transition assumptions rather than a single projected return. [[machine-learning/q-learning-control-and-exploration|Q-learning]] cannot repair absent transitions merely by repeated updates.'),
    ('Plan prospective review', 'Before a live pilot, name capacity and safety guardrails, assignment logging, monitoring windows and rollback criteria. If actions affect future customer or staff outcomes, evaluate those outcomes at their real maturity time. [[machine-learning/sequential-policy-review-project|The release project]] keeps unsupported claims visible.')],
    '''# Historical transitions are summarized by observed state and action.
logged_visits = {
    ("low-stock", "replenish"): 47,
    ("low-stock", "wait"): 13,
    ("ready-stock", "dispatch"): 52,
    ("ready-stock", "hold"): 0,
}
candidate_plan = [("low-stock", "replenish"),
                  ("ready-stock", "hold"),
                  ("ready-stock", "dispatch")]

def support_screen(plan, counts, minimum_visits):
    return [{"state": state, "action": action,
             "visits": counts.get((state, action), 0)}
            for state, action in plan
            if counts.get((state, action), 0) < minimum_visits]

gaps = support_screen(candidate_plan, logged_visits, minimum_visits=8)
assert gaps == [{"state": "ready-stock", "action": "hold", "visits": 0}]''',
    'Screening P proposed state-action entries against a hash map costs O(P) expected time and O(G) output space for G gaps. Reliable sequential evaluation is much more costly: coverage deteriorates with path length, and simulator error can compound across transitions. A low-cost count is a blocker check, not a value estimator.',
    ['Do not treat a one-step supported action as proof that a new trajectory is supported.', 'Do not present simulated long-run reward as observed policy value.', 'Do not use a nonzero visit count as evidence of adequate precision without inspecting its context.'],
    ['machine-learning/sequential-decision-state-and-reward-contract','machine-learning/bellman-value-iteration-for-stock-control','machine-learning/q-learning-control-and-exploration','machine-learning/sequential-policy-review-project'])


add('sequential-policy-review-project',
    'Sequential stock-control policy review project',
    'Review a stock-control policy using a state and reward contract, a checked transition model, episode outcomes, action support, safety constraints and rollback.', [
    ('Freeze the process definition', 'Define the stock unit, decision interval, state snapshot, legal actions, transition event, reward timing and genuine terminal event. Include outstanding orders if they affect the next state. [[machine-learning/sequential-decision-state-and-reward-contract|The state contract]] is the minimum record for both planning and learning.'),
    ('Build a small baseline model', 'Estimate transitions and immediate rewards from historical episodes with their policy versions. Solve the finite planning model and compare its proposed actions with the reviewed existing policy. Validate one-step probabilities and longer simulated trajectories on held-out periods. [[machine-learning/bellman-value-iteration-for-stock-control|Value iteration]] only certifies the calculation for that model.'),
    ('Check learning and logged support', 'Calculate mature episode returns and inspect terminal handling. If Q-learning is considered, report safe exploration, state-action visits and stability across seeds. Screen every proposed action and trajectory against historical support. [[machine-learning/temporal-difference-return-and-terminal|Returns]], [[machine-learning/q-learning-control-and-exploration|Q updates]] and [[machine-learning/offline-trajectory-support-and-simulator-risk|support]] each answer different questions.'),
    ('Assess business consequences', 'Report shortages, service value, labor cost, capacity incidents and group-level effects across future periods. An attractive simulated discounted return is insufficient if rare shortages are omitted or safety rules are violated. Any prospective test needs assignment logs, stop rules and an approved rollback. [[machine-learning/exploration-budget-and-guardrails|Exploration controls]] carry over from one-step policies.'),
    ('Keep the decision bounded', 'The code checks that the review packet exists; it does not establish model accuracy, safe exploration or expected improvement. Attach measured results, uncertainty and the responsible owner before considering a pilot. A missing state or support check keeps the release on hold.')],
    '''def sequential_review_gate(packet):
    requirements = {
        "state_contract_signed": "state contract",
        "reward_clock_audited": "reward clock",
        "terminal_rules_tested": "terminal rules",
        "transition_model_checked": "transition model",
        "trajectory_support_checked": "trajectory support",
        "safety_actions_enforced": "safety actions",
        "rollback_owner_named": "rollback owner",
    }
    missing = [label for field, label in requirements.items() if not packet.get(field)]
    return "eligible for pilot review" if not missing else "hold: " + ", ".join(missing)

stock_packet = {
    "state_contract_signed": True, "reward_clock_audited": True,
    "terminal_rules_tested": True, "transition_model_checked": False,
    "trajectory_support_checked": False, "safety_actions_enforced": True,
    "rollback_owner_named": True,
}
assert sequential_review_gate(stock_packet) == (
    "hold: transition model, trajectory support"
)''',
    'The gate is O(K) for K checks. Finite value iteration costs O(JSAO) for J sweeps, S states, A actions and O outcomes per action; trajectory audits scan logged decisions. The main operating costs are safe evidence collection, rare-event validation, model monitoring and a credible rollback path.',
    ['Do not replace business safety constraints with a weak reward penalty.', 'Do not infer a long-run candidate value from missing state-action trajectories.', 'Do not call an optimal solution to an unchecked simulator a release-ready policy.'],
    ['machine-learning/sequential-decision-state-and-reward-contract','machine-learning/bellman-value-iteration-for-stock-control','machine-learning/temporal-difference-return-and-terminal','machine-learning/q-learning-control-and-exploration','machine-learning/offline-trajectory-support-and-simulator-risk','machine-learning/bandit-policy-release-review-project'])


publish_batch(
    lessons,
    module_title='Sequential decisions and value learning',
    module_summary='Define state and reward, solve a small known model, learn from episodes and audit offline path support.',
    project_heading='Sequential stock-control review',
    crosslinks=[
        ('machine-learning/bandit-policy-release-review-project', lessons[0]['path']),
        ('machine-learning/contextual-bandit-action-logging-and-support', lessons[1]['path']),
        ('machine-learning/delayed-bandit-rewards-and-maturity', lessons[2]['path']),
        ('machine-learning/exploration-budget-and-guardrails', lessons[3]['path']),
        ('machine-learning/importance-weighted-risk-under-shift', lessons[4]['path']),
        ('machine-learning/multilabel-release-review-project', lessons[5]['path']),
    ],
    sort_start=5600,
)
