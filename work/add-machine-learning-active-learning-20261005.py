"""Add original active-learning operations and evaluation lessons."""
from ml_fixture_writer_20261005 import publish_batch

lessons = []


def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='machine-learning/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))


add('active-learning-pool-eligibility-and-snapshot',
    'Active-learning pool eligibility and round snapshots',
    'A query strategy can select only records that are legal to label, unresolved, available at the decision clock and separate from the fixed evaluation set.', [
    ('Define the label request', 'An invoice operations model flags documents that require a tax-code review. Each acquired label asks an analyst whether the invoice truly needs specialist review under a versioned policy. A record with no confirmed outcome is not automatically a negative. The label request must include the allowed evidence and a reason code so the analyst can adjudicate it consistently.'),
    ('Freeze the eligible pool', 'At each acquisition round, save a pool snapshot with document IDs, customer group, arrival time, policy version and exclusion reason. Remove already labeled invoices, duplicates, legally restricted records and the untouched test set before scoring. A later correction to the pool must create a new version. Otherwise a reported label-efficiency curve cannot be reproduced.'),
    ('Keep entities together', 'Several invoices can share a purchase order or supplier template. If a template appears in both the acquisition pool and final test, apparent generalization may be recognition of repeated form. Split by supplier or template family when that matches the deployment claim. [[machine-learning/group-and-time-validation|Group and time validation]] establishes the boundary.'),
    ('Track selection probability', 'A deterministic top-uncertainty list concentrates labels near a model boundary. That may train a useful classifier, but it is not a representative sample of all invoices. Store the acquisition score, policy and any randomized component. [[data-annotation/active-learning-and-selection-bias|Selection bias]] affects population claims.'),
    ('Reserve a random lane', 'A small random slice can reveal new invoice patterns and provide a training comparison. The final evaluation set must be sampled independently before active selection or analyzed with an appropriate design. The example filters eligible records; it does not choose labels or estimate population performance.')],
    '''invoice_pool = [
    {"invoice": "bill-47", "labeled": False, "restricted": False,
     "test_holdout": False, "duplicate_of": None},
    {"invoice": "bill-62", "labeled": True, "restricted": False,
     "test_holdout": False, "duplicate_of": None},
    {"invoice": "bill-83", "labeled": False, "restricted": False,
     "test_holdout": True, "duplicate_of": None},
    {"invoice": "bill-94", "labeled": False, "restricted": False,
     "test_holdout": False, "duplicate_of": "bill-47"},
]

def eligible_invoices(records):
    return [record["invoice"] for record in records
            if not record["labeled"] and not record["restricted"]
            and not record["test_holdout"] and record["duplicate_of"] is None]

assert eligible_invoices(invoice_pool) == ["bill-47"]''',
    'Filtering N records costs O(N) time and O(N) output storage. Exact duplicate checks are cheap with stable IDs; near-duplicate templates need indexed similarity review. Persisting each round’s snapshot adds storage but is necessary to reconstruct which invoices could have been queried.',
    ['Do not let the final test set enter the acquisition pool.', 'Do not interpret selected labels as representative prevalence.', 'Do not silently rescore a changed pool under the old round ID.'],
    ['machine-learning/active-learning-batch-selection-and-cost','machine-learning/active-learning-oracle-disagreement','machine-learning/active-learning-evaluation-and-stopping','machine-learning/invoice-active-learning-release-project'])


add('active-learning-batch-selection-and-cost',
    'Active-learning batch selection under annotation cost',
    'An acquisition batch should trade uncertain cases against duplicate coverage, slice coverage and reviewer time; selecting the highest score repeatedly can waste the budget.', [
    ('Choose a measurable objective', 'For tax-code review, uncertainty may be distance from a calibrated decision threshold. It is a ranking signal, not expected improvement by itself: a poorly calibrated model can be confidently wrong, and an unreadable scan can stay uncertain regardless of how many similar scans are labeled. [[machine-learning/active-learning-uncertainty-and-diversity|Uncertainty and diversity]] provide the starting vocabulary.'),
    ('Reject redundancy within a batch', 'If 30 invoices use the same supplier form, a top-score list might spend the entire annotation budget on near copies. Enforce a per-template or supplier cap, then compare coverage by customer sector and document quality. A cap can also exclude a common high-risk group, so inspect the selected distribution after each round rather than treating diversity as an automatic improvement.'),
    ('Use actual label cost', 'A one-page typed invoice may take 34 seconds to label; a nine-page scan may take several minutes and two reviewers. Rank candidate value against expected review time when budget is measured in staff hours. The code greedily selects by an illustrative value-per-minute score while respecting a template cap. It is a policy sketch, not a claim of globally optimal acquisition.'),
    ('Keep random comparison stable', 'For the same staff-minute budget, label an independently sampled random batch with the same policy and reviewer process. Evaluate both resulting models on the same untouched test. More queried records is not necessarily better when one strategy receives easier labels.'),
    ('Log why a case was picked', 'Persist model version, score, expected minutes, template ID, pool version and final decision. A policy update or label-cost underestimate can then be diagnosed. [[machine-learning/active-learning-evaluation-and-stopping|Round comparison]] relies on those logs.')],
    '''candidates = [
    {"invoice": "bill-47", "template": "supplier-a", "value": 0.84, "minutes": 2},
    {"invoice": "bill-58", "template": "supplier-a", "value": 0.91, "minutes": 2},
    {"invoice": "bill-76", "template": "supplier-b", "value": 0.72, "minutes": 3},
    {"invoice": "bill-95", "template": "supplier-c", "value": 0.39, "minutes": 1},
]

def choose_batch(records, minute_budget):
    chosen, used_templates, spent = [], set(), 0
    ranked = sorted(records, key=lambda row: row["value"] / row["minutes"], reverse=True)
    for record in ranked:
        if record["template"] in used_templates or spent + record["minutes"] > minute_budget:
            continue
        chosen.append(record["invoice"])
        used_templates.add(record["template"])
        spent += record["minutes"]
    return chosen, spent

assert choose_batch(candidates, 5) == (["bill-58", "bill-95"], 3)''',
    'Sorting N candidates costs O(N log N) time and O(N) memory, followed by O(N) selection. Greedy selection may leave budget unused and can miss a better combination. Full model scoring, duplicate detection and human labeling often dominate; compare end-to-end gain per staff hour.',
    ['Do not maximize uncertainty while ignoring repeated templates.', 'Do not compare strategies by label count when label times differ.', 'Do not call the greedy heuristic globally optimal.'],
    ['machine-learning/active-learning-pool-eligibility-and-snapshot','machine-learning/active-learning-oracle-disagreement','machine-learning/active-learning-evaluation-and-stopping','machine-learning/invoice-active-learning-release-project'])


add('active-learning-oracle-disagreement',
    'Active-learning annotator disagreement and adjudication',
    'Selection often concentrates ambiguous records. Disagreement may expose unclear policy or bad evidence, not merely an annotator who needs correction.', [
    ('Route hard cases intentionally', 'A tax-code exception can depend on contract context absent from an invoice scan. If the query strategy repeatedly picks these cases, a reviewer cannot produce a reliable binary label by guessing. Allow “insufficient evidence” and capture what document was missing. Later evidence can change the target state; that is not the same as changing the analyst’s opinion.'),
    ('Separate model uncertainty from label uncertainty', 'Two models may disagree while trained analysts agree. Conversely, models may agree on a shortcut while analysts dispute whether the invoice is exempt. Record initial independent votes and a final adjudicated outcome. Do not train on the final result without storing the disagreement and policy version. [[data-annotation/active-learning-and-selection-bias|Selection effects]] can amplify disputed cases.'),
    ('Budget second review by impact', 'Double annotation of every record may exhaust the budget. Route policy-sensitive classes, contradictory evidence and novel templates for independent second review; sample some easy cases to measure background error. The code marks records for adjudication when votes differ or either vote is unknown.'),
    ('Avoid majority-vote theater', 'Three analysts repeating an unclear rule do not resolve a broken definition. Escalate recurrent disagreements to a policy owner and version the instruction. After a policy change, revisit labels made under the old rule and keep test labels under the same target contract as training.'),
    ('Measure downstream value', 'Compare model quality with raw first votes and adjudicated labels at the same staff-minute cost. If most queries are unanswerable, revise the acquisition policy or data collection rather than adding more labels. [[machine-learning/active-learning-evaluation-and-stopping|Stopping rules]] need this signal.')],
    '''review_votes = [
    {"invoice": "bill-47", "first": "review", "second": "review"},
    {"invoice": "bill-62", "first": "clear", "second": "review"},
    {"invoice": "bill-83", "first": "unknown", "second": "unknown"},
]

def adjudication_queue(votes):
    return [record["invoice"] for record in votes
            if record["first"] != record["second"]
            or "unknown" in (record["first"], record["second"])]

assert adjudication_queue(review_votes) == ["bill-62", "bill-83"]''',
    'Routing N vote pairs costs O(N) time and O(N) output storage. A second review nearly doubles direct labeling work on selected records; policy adjudication may take longer than annotation. Measure total resolution time and label reversals, not just the number of completed tasks.',
    ['Do not force an answer when evidence is missing.', 'Do not erase disagreement after adjudication.', 'Do not blame annotators for an undefined label policy.'],
    ['machine-learning/active-learning-pool-eligibility-and-snapshot','machine-learning/active-learning-batch-selection-and-cost','machine-learning/active-learning-evaluation-and-stopping','machine-learning/invoice-active-learning-release-project'])


add('active-learning-evaluation-and-stopping',
    'Active-learning evaluation and stopping by value',
    'A label-acquisition strategy earns its place only when it improves a fixed deployment metric at comparable cost on an evaluation set independent of the selected pool.', [
    ('Freeze evaluation before acquisition', 'Use a later-period, supplier-grouped test set representative of the invoices the service will face. The active learner must not query it, choose thresholds from it or see its labels between rounds. A selected-label validation set overrepresents uncertain invoices and cannot establish population performance without an explicit sampling design.'),
    ('Compare cost curves', 'At each cumulative staff-hour checkpoint, train the active and random-sampling baselines under the same architecture, label policy and development protocol. Plot false tax-code clearances, review volume and calibration with support counts. Compare paired predictions on the same test invoices; a curve drawn against label count hides expensive cases. [[machine-learning/learning-curves-and-training-size-diagnosis|Learning curves]] frame the comparison.'),
    ('Inspect acquisition drift', 'Query scores change as the model changes. A strategy can move from genuinely informative examples to near duplicates, annotation disputes or an overrepresented supplier. Log pool coverage, novel templates, class mix and adjudication share each round. [[machine-learning/active-learning-oracle-disagreement|Oracle disagreement]] can become the limiting cost.'),
    ('Stop for a reason', 'A practical stop rule can combine no material gain over random selection across several budget checkpoints, exhausted staff minutes, rising unresolved-label fraction, or a breached review-capacity limit. Predeclare the rule and use development measurements for operational stopping. Do not repeatedly peek at final-test scores until one looks favorable.'),
    ('Keep a release path', 'If active selection helps a narrow slice but harms another, retain the random-lane labels and consider a revised batch policy. After release, track the same decision costs under drift and retraining. [[machine-learning/invoice-active-learning-release-project|The project]] makes the gate explicit.')],
    '''budget_checkpoints = [
    {"hours": 18, "active_missed": 15, "random_missed": 17},
    {"hours": 34, "active_missed": 13, "random_missed": 14},
    {"hours": 51, "active_missed": 13, "random_missed": 12},
]

def no_recent_gain(checkpoints, window):
    if len(checkpoints) < window:
        return False
    recent = checkpoints[-window:]
    return all(row["active_missed"] >= row["random_missed"]
               for row in recent)

assert no_recent_gain(budget_checkpoints, 1) is True
assert no_recent_gain(budget_checkpoints, 2) is False''',
    'Checking R budget checkpoints costs O(R) at most and O(1) extra memory. The real expense is parallel random-baseline labeling, repeated model training and a fixed independently labeled test. Those costs are part of proving label efficiency; omitting them can make an acquisition policy look cheaper than it is.',
    ['Do not evaluate population quality on the selected training pool.', 'Do not compare by acquired-label count when label costs vary.', 'Do not repeatedly tune against the untouched final test.'],
    ['machine-learning/active-learning-pool-eligibility-and-snapshot','machine-learning/active-learning-batch-selection-and-cost','machine-learning/active-learning-oracle-disagreement','machine-learning/invoice-active-learning-release-project'])


add('invoice-active-learning-release-project',
    'Project: release review for invoice-label acquisition',
    'A label-efficiency claim requires a reproducible eligible pool, budgeted queries, adjudicated labels and a paired comparison with random acquisition.', [
    ('Lock the problem and pool', 'The classifier decides which new invoices need specialist tax-code review. Freeze policy version, supplier-grouped later test, eligible unlabeled pool and each round’s exclusion list. No test invoice, duplicate or restricted document may enter a query batch. [[machine-learning/active-learning-pool-eligibility-and-snapshot|Pool snapshots]] make this auditable.'),
    ('Run two acquisition lanes', 'Start both candidates with the same initial labeled set. Spend matched analyst minutes on an uncertainty-plus-template-diversity policy and on random eligible invoices. Keep model architecture and development tuning identical. Log scores, acquisition probability where relevant, expected minutes and actual minutes. [[machine-learning/active-learning-batch-selection-and-cost|Batch design]] defines the costs.'),
    ('Adjudicate the difficult cases', 'Assign independent second review to conflicts and unanswerable scans. Record first vote, second vote, evidence gap, policy escalation and final disposition. Do not collapse unknown into clear. Report the fraction of acquired records that could not be resolved under the frozen policy. [[machine-learning/active-learning-oracle-disagreement|Disagreement handling]] keeps the label stream credible.'),
    ('Compare value at equal cost', 'At predetermined budget checkpoints, compare missed tax-code exceptions and review volume on the same untouched test. Include supplier, template and scan-quality slices with support counts. Stop if gains disappear, annotation disputes dominate or staff capacity is exceeded. [[machine-learning/active-learning-evaluation-and-stopping|Evaluation and stopping]] set the decision.'),
    ('Make a bounded claim', 'The sample gate below holds an active acquisition policy even though its selected-model score improved: the comparison spent more analyst minutes than the random lane. Rebalance the budget and rerun a paired checkpoint before saying it saves labels or staff time.')],
    '''release_packet = {
    "pool_and_test_disjoint": True,
    "policy_version_locked": True,
    "active_analyst_minutes": 246,
    "random_analyst_minutes": 219,
    "allowed_budget_gap_minutes": 12,
    "active_missed_exceptions": 8,
    "random_missed_exceptions": 11,
    "unresolved_disputes": 0,
}

def review_acquisition_release(packet):
    blockers = []
    if not packet["pool_and_test_disjoint"] or not packet["policy_version_locked"]:
        blockers.append("pool or label contract failed")
    if packet["active_analyst_minutes"] > packet["random_analyst_minutes"] + packet["allowed_budget_gap_minutes"]:
        blockers.append("annotation budgets not comparable")
    if packet["active_missed_exceptions"] > packet["random_missed_exceptions"]:
        blockers.append("no exception-capture gain")
    if packet["unresolved_disputes"]:
        blockers.append("unresolved labels remain")
    return {"release": not blockers, "blockers": blockers}

decision = review_acquisition_release(release_packet)
assert decision == {"release": False,
                    "blockers": ["annotation budgets not comparable"]}''',
    'The packet gate is O(1). The project cost includes scoring the full pool, duplicate screening, analyst minutes, independent adjudication, repeated training and a separate random-acquisition control. A claimed saving is incomplete if it counts model queries but omits staff time.',
    ['Do not claim label efficiency from unequal annotation budgets.', 'Do not include selected training cases in the final-test denominator.', 'Do not approve unresolved ambiguous labels merely to complete a batch.'],
    ['machine-learning/active-learning-pool-eligibility-and-snapshot','machine-learning/active-learning-batch-selection-and-cost','machine-learning/active-learning-oracle-disagreement','machine-learning/active-learning-evaluation-and-stopping','machine-learning/active-learning-uncertainty-and-diversity'])


publish_batch(
    lessons,
    module_title='Active learning and annotation budgets',
    module_summary='Control query eligibility, batch cost, label disagreements and fixed-test evidence across acquisition rounds.',
    project_heading='Invoice label-acquisition release project',
    crosslinks=[
        ('machine-learning/active-learning-uncertainty-and-diversity', 'machine-learning/active-learning-pool-eligibility-and-snapshot'),
        ('machine-learning/learning-curves-and-training-size-diagnosis', 'machine-learning/active-learning-evaluation-and-stopping'),
        ('data-annotation/active-learning-and-selection-bias', 'machine-learning/active-learning-batch-selection-and-cost'),
        ('machine-learning/group-and-time-validation', 'machine-learning/active-learning-evaluation-and-stopping'),
    ],
    sort_start=6700,
)
