"""Add original federated-optimization and evaluation lessons."""
from ml_fixture_writer_20261005 import publish_batch

lessons = []


def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='machine-learning/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))


add('federated-client-data-and-target-contract',
    'Federated client data and target contract',
    'Federated training keeps examples at participating sites while exchanging model updates; it still needs a common label, feature and prediction-time contract.', [
    ('Define the unit that stays local', 'A network of repair depots wants to predict which inspected pumps will need follow-up within 37 days. Photos and work orders stay inside each depot. A client is one depot, not an arbitrary training shard. The server can coordinate rounds and receive approved update packets, but that arrangement does not by itself prevent information leakage from those packets. [[privacy-aware-ml/federated-updates-and-aggregation-risk|Aggregation risk]] is a separate security decision.'),
    ('Align labels before averaging models', 'Every depot must use the same event definition, observation window, censoring rule and exclusion policy. A work order reopened after 39 days is not a positive for the 37-day target, and a pump observed for only 12 days is not a verified negative. If local labels disagree, averaging updates cannot create a coherent global objective. [[machine-learning/prediction-time-feature-availability|Feature availability]] also needs one shared clock.'),
    ('Version the feature transformation', 'Image crop, sensor units, missing-value codes and category mapping must be compatible across clients. A local calibration step may be acceptable if it is part of the serving contract, but silently fitting one global scaler on a central sample defeats the claimed data boundary. Record the preprocessing version with each update. [[machine-learning/leakage-safe-preprocessing-pipeline|Fold-local preprocessing]] offers the analogous single-site discipline.'),
    ('State the population objective', 'Example-weighted averaging tends toward the distribution represented by the participating examples. Equal-client averaging gives a tiny depot the same influence as a large one. Neither is automatically fair or operationally correct. Define whether the target is a random pump, a random depot, or minimum acceptable quality at each depot before selecting weights. [[machine-learning/federated-aggregation-and-weighting|Aggregation]] turns this into arithmetic.'),
    ('Keep local and global holdouts', 'Reserve a later-period test at each depot, untouched by round selection. Include newly added depots in a separate portability assessment if deployment will expand. Report depot counts, example counts, positive counts and maturity by split; a pooled metric alone hides whether one depot fails. [[machine-learning/federated-site-evaluation-and-denominators|Site evaluation]] specifies the denominators.')],
    '''depot_contracts = [
    {"depot": "north-47", "target_days": 37, "sensor_unit": "celsius", "crop_version": "v4", "matured": 182},
    {"depot": "west-62", "target_days": 37, "sensor_unit": "celsius", "crop_version": "v4", "matured": 94},
    {"depot": "east-83", "target_days": 37, "sensor_unit": "celsius", "crop_version": "v4", "matured": 57},
]

def validate_client_contracts(contracts):
    if not contracts:
        raise ValueError("at least one depot required")
    expected = (contracts[0]["target_days"], contracts[0]["sensor_unit"], contracts[0]["crop_version"])
    for depot in contracts:
        actual = (depot["target_days"], depot["sensor_unit"], depot["crop_version"])
        if actual != expected or depot["matured"] <= 0:
            raise ValueError("incompatible or empty depot contract")
    return sum(depot["matured"] for depot in contracts)

assert validate_client_contracts(depot_contracts) == 333''',
    'Contract validation is O(C) time for C clients and O(1) auxiliary memory. The real cost lies in local feature preparation, outcome maturation and version coordination. Moving only updates can reduce raw-data transfer, but it does not remove communication, security review or the need for representative evaluation.',
    ['Do not call a short-observed pump a verified negative for a longer horizon.', 'Do not aggregate updates produced from incompatible feature units or label definitions.', 'Do not equate local data residence with a formal privacy guarantee.'],
    ['machine-learning/federated-aggregation-and-weighting','machine-learning/non-iid-client-drift-and-local-steps','machine-learning/client-participation-and-dropout-audit','machine-learning/federated-site-evaluation-and-denominators'])


add('federated-aggregation-and-weighting',
    'Federated averaging and client weighting',
    'A federated round combines compatible local model updates using declared client weights; the weights determine whose data dominates the global model.', [
    ('Start from the same checkpoint', 'Each participating repair depot receives the same global model version and preprocessing contract, trains locally for the agreed step budget, and returns an update. Reject packets from an older checkpoint or mismatched tensor shape. Averaging weights from different starting versions does not represent the intended round. [[machine-learning/federated-client-data-and-target-contract|The client contract]] defines those versions.'),
    ('Compute an explicit weighted delta', 'A common baseline multiplies each client delta by its eligible example count, sums the results, then divides by total eligible examples. The code uses a two-parameter toy model so the weighting is inspectable. It is not a full optimizer. Equal-client weighting produces a different answer, and a capped count can prevent one large site from overwhelming small sites if that matches the objective.'),
    ('Distinguish participation from population', 'Only clients that finish a round contribute to that round. If slow depots systematically drop out, the weighted average may drift toward fast, well-connected sites. Log invited, started, completed and rejected clients with reasons; a large total example count does not prove geographic coverage. [[machine-learning/client-participation-and-dropout-audit|Participation audit]] checks that selection.'),
    ('Constrain update scale', 'Local training can produce a large delta from data shift, a bad sensor conversion, excessive local epochs or malicious input. Inspect norms and nonfinite values before aggregation. Clipping can bound influence but changes optimization; it is not a substitute for secure aggregation or differential privacy. [[privacy-aware-ml/privacy-unit-and-contribution-bounds|Contribution bounds]] have their own privacy meaning.'),
    ('Evaluate the result, not the averaging step', 'A numerically valid average may worsen rare-failure recall at one depot. Compare local and global validation by site, and use a later holdout after choosing rounds. [[machine-learning/federated-site-evaluation-and-denominators|Site evaluation]] makes the outcome visible; [[machine-learning/federated-release-review-project|the project]] converts it into a release decision.')],
    '''client_updates = [
    {"depot": "north-47", "base": "round-8", "examples": 180, "delta": (0.20, -0.04)},
    {"depot": "west-62", "base": "round-8", "examples": 90, "delta": (-0.10, 0.08)},
    {"depot": "east-83", "base": "round-8", "examples": 30, "delta": (0.50, -0.02)},
]

def weighted_delta(updates, expected_base):
    if not updates or any(update["base"] != expected_base or update["examples"] <= 0 for update in updates):
        raise ValueError("incompatible client update")
    dimensions = len(updates[0]["delta"])
    if any(len(update["delta"]) != dimensions for update in updates):
        raise ValueError("parameter shapes differ")
    total = sum(update["examples"] for update in updates)
    return tuple(sum(update["examples"] * update["delta"][dimension] for update in updates) / total
                 for dimension in range(dimensions))

round_delta = weighted_delta(client_updates, "round-8")
assert tuple(round(value, 3) for value in round_delta) == (0.14, -0.002)''',
    'Aggregating C clients with D parameters costs O(C times D) arithmetic and O(D) accumulator memory if updates stream securely into the server. Upload traffic is roughly proportional to participating clients times model size before compression or protocol overhead. This toy code omits transport, secure aggregation, training and adversarial checks.',
    ['Do not average updates from different starting checkpoints.', 'Do not hide the choice between example-weighted and equal-client objectives.', 'Do not treat clipping alone as a privacy or poisoning solution.'],
    ['machine-learning/federated-client-data-and-target-contract','machine-learning/non-iid-client-drift-and-local-steps','machine-learning/client-participation-and-dropout-audit','machine-learning/federated-site-evaluation-and-denominators'])


add('non-iid-client-drift-and-local-steps',
    'Non-IID clients, local steps and update disagreement',
    'When client distributions differ, additional local steps can move models toward site-specific objectives and make their returned updates disagree.', [
    ('Measure heterogeneity before tuning', 'Repair depots may handle different pump types, inspection cameras and maintenance schedules. Compare matured outcome prevalence, feature ranges and model errors by depot. A low pooled loss can coexist with a high missed-failure rate at a smaller site. [[machine-learning/group-error-gaps-and-policy-audit|Group error gaps]] make that failure visible.'),
    ('Read disagreement with context', 'Two client deltas pointing in opposite directions may signal data heterogeneity, label inconsistency, or noisy small samples. The code computes cosine agreement for toy updates; it is a diagnostic, not proof of a particular cause. Pair it with contract checks, eligible sample counts and held-out site metrics. [[machine-learning/federated-client-data-and-target-contract|The shared target]] must be checked first.'),
    ('Control the local work budget', 'More local epochs reduce communication rounds but can increase drift and overfitting at small depots. Compare one, three and five local passes under a fixed total compute or communication budget, keeping sampling and evaluation cohorts constant. Select the schedule on development sites, then report untouched later-period performance. Do not tune per site on its test records.'),
    ('Separate personalization from one global model', 'If one global model cannot meet each depot’s minimum performance, a calibrated local head or site-specific threshold may help. That adds serving, monitoring and rollback complexity. Define whether local adaptation uses private training data or leaked later outcomes. [[machine-learning/decision-threshold-and-cost|Threshold choice]] can sometimes address action costs without retraining the representation.'),
    ('Consider who is absent', 'Update disagreement among successful clients says nothing about clients that failed to participate. Slow links, old devices or low-volume depots may be exactly where the model needs improvement. [[machine-learning/client-participation-and-dropout-audit|The participation audit]] must run alongside drift diagnostics.')],
    '''from math import sqrt

depot_deltas = {
    "north-47": (0.24, -0.04),
    "west-62": (0.17, -0.02),
    "east-83": (-0.19, 0.03),
}

def cosine_agreement(first, second):
    numerator = sum(left * right for left, right in zip(first, second))
    first_norm = sqrt(sum(value * value for value in first))
    second_norm = sqrt(sum(value * value for value in second))
    if first_norm == 0 or second_norm == 0:
        raise ValueError("zero update needs separate handling")
    return numerator / (first_norm * second_norm)

assert cosine_agreement(depot_deltas["north-47"], depot_deltas["west-62"]) > 0.99
assert cosine_agreement(depot_deltas["north-47"], depot_deltas["east-83"]) < -0.99''',
    'One pairwise cosine costs O(D) time for D parameters. All C-by-C client comparisons cost O(C squared times D) time; sampled comparisons or update summaries are cheaper. Extra local epochs increase device compute and can reduce rounds while worsening drift. Choose settings on site-level validation rather than minimizing communication alone.',
    ['Do not infer the cause of opposing updates from cosine alone.', 'Do not improve the pooled metric by sacrificing a small high-risk depot.', 'Do not compare local-epoch settings under different participation cohorts without reporting the change.'],
    ['machine-learning/federated-client-data-and-target-contract','machine-learning/federated-aggregation-and-weighting','machine-learning/client-participation-and-dropout-audit','machine-learning/federated-site-evaluation-and-denominators'])


add('client-participation-and-dropout-audit',
    'Client participation, dropouts and stale updates',
    'A federated round observes only clients that finish on time; selection and dropout can shift both the training population and its reported quality.', [
    ('Track the full round funnel', 'For each depot, record eligibility, invitation, acceptance, local training start, completion, accepted update and reason for rejection. A round with four accepted updates from four invitees looks healthy; the same four from twenty eligible depots may not represent the network. Keep counts by site type and device class. [[machine-learning/federated-aggregation-and-weighting|Aggregation]] applies only after this funnel.'),
    ('Reject stale updates deliberately', 'A client can finish after the server has moved to a new global version. Applying its delta to the new checkpoint changes the optimization equation. Choose a synchronous cutoff or a specifically designed asynchronous protocol with version-aware weights; do not silently append late updates. The code flags a stale base and an incomplete packet.'),
    ('Distinguish randomness from systematic loss', 'If participation is approximately random, missing clients add variance. If low-connectivity or high-failure depots miss most rounds, the model can be biased toward easier sites. Compare participating and nonparticipating client metadata and pre-round performance, while respecting local data boundaries. [[machine-learning/covariate-shift-and-support-overlap|Support overlap]] gives the broader selection warning.'),
    ('Budget communication as a distribution', 'Log upload bytes, round duration, retry count and battery or compute limits. A median round time hides sites that consistently exceed the deadline. Shortening the timeout may speed training while systematically excluding them. Tune the cutoff with site coverage and target performance, not speed alone.'),
    ('Audit exposure to personal data', 'Update packets and client metadata may leak information even if raw images remain local. Minimize identifiers and apply an explicit threat model before collecting site-level telemetry. [[privacy-aware-ml/threat-model-and-data-minimization|Data minimization]] and [[privacy-aware-ml/federated-updates-and-aggregation-risk|aggregation risk]] set those boundaries.')],
    '''round_packets = [
    {"depot": "north-47", "invited": True, "finished": True, "base": "round-8", "examples": 180},
    {"depot": "west-62", "invited": True, "finished": True, "base": "round-7", "examples": 90},
    {"depot": "east-83", "invited": True, "finished": False, "base": "round-8", "examples": 30},
    {"depot": "south-94", "invited": False, "finished": False, "base": None, "examples": 66},
]

def round_funnel(packets, expected_base):
    invited = [packet for packet in packets if packet["invited"]]
    accepted = [packet for packet in invited if packet["finished"]
                and packet["base"] == expected_base and packet["examples"] > 0]
    stale = [packet["depot"] for packet in invited if packet["finished"]
             and packet["base"] != expected_base]
    return {"eligible": len(packets), "invited": len(invited),
            "accepted": len(accepted), "stale": stale}

assert round_funnel(round_packets, "round-8") == {
    "eligible": 4, "invited": 3, "accepted": 1, "stale": ["west-62"]
}''',
    'The audit scans C client packets in O(C) time and stores O(C) accepted or rejected IDs in the worst case. Logging every step has network and retention costs. A shorter round can improve wall time but reduce site coverage; evaluate both before changing the timeout.',
    ['Do not count invited clients as successful participants.', 'Do not apply an old-checkpoint delta to the current model without a defined asynchronous method.', 'Do not describe missing clients as random without testing participation patterns.'],
    ['machine-learning/federated-client-data-and-target-contract','machine-learning/federated-aggregation-and-weighting','machine-learning/non-iid-client-drift-and-local-steps','machine-learning/federated-site-evaluation-and-denominators'])


add('federated-site-evaluation-and-denominators',
    'Federated evaluation by site and denominator',
    'Federated evaluation needs both example-weighted and site-weighted views, with denominators for mature outcomes, participation and rare failures.', [
    ('Name the measure before aggregating', 'A depot-level missed-failure rate uses confirmed follow-up events as its denominator; calibration at 37 days needs mature outcomes. Do not average client accuracy values when their denominators and class prevalences differ and then call the result a network-wide example metric. [[machine-learning/rare-event-precision-recall-and-prevalence|Rare-event metrics]] show why prevalence matters.'),
    ('Compute micro and macro separately', 'A micro average weights every evaluated pump equally. A macro average weights each depot equally. The code computes both from toy correct-prediction counts; their difference is information, not a rounding problem. Neither replaces the minimum site-specific standard when deployment happens at all depots. [[machine-learning/group-error-gaps-and-policy-audit|Group gaps]] should be shown next to the averages.'),
    ('Evaluate an untouched period at every site', 'Select rounds, aggregation weights and local-step budgets using development periods. Then run the selected checkpoint on later local holdouts without sending raw records to the server. Record the model and feature versions and the local result schema. If a client has too few mature positives, report an interval or “insufficient support” rather than a precise recall.'),
    ('Treat participation as part of the result', 'Only reporting sites are visible in the result table. Publish the number invited and evaluated, and compare reporting sites with missing ones. A high pooled score from the largest two depots does not license a rollout to six. [[machine-learning/client-participation-and-dropout-audit|Participation records]] close that denominator.'),
    ('Protect the evaluation channel', 'Even aggregate metrics can reveal sensitive local properties when groups are small or reported repeatedly. Set minimum cell sizes, retention and access rules. This is separate from the training objective. [[privacy-aware-ml/privacy-budget-and-safe-release|Safe release]] discusses disclosure controls; [[machine-learning/federated-release-review-project|the project]] uses the audited scorecard.')],
    '''site_results = [
    {"depot": "north-47", "evaluated": 200, "correct": 180},
    {"depot": "west-62", "evaluated": 50, "correct": 35},
    {"depot": "east-83", "evaluated": 20, "correct": 12},
]

def accuracy_views(results):
    if not results or any(row["evaluated"] <= 0 or not 0 <= row["correct"] <= row["evaluated"] for row in results):
        raise ValueError("invalid local denominator")
    micro = sum(row["correct"] for row in results) / sum(row["evaluated"] for row in results)
    macro = sum(row["correct"] / row["evaluated"] for row in results) / len(results)
    worst = min(row["correct"] / row["evaluated"] for row in results)
    return micro, macro, worst

micro, macro, worst = accuracy_views(site_results)
assert round(micro, 3) == 0.841
assert round(macro, 3) == 0.733
assert worst == 0.6''',
    'Aggregating C site summaries is O(C) time and O(1) auxiliary memory. The expensive part is local holdout scoring and maturity tracking. Transferring only metrics reduces raw-data movement but does not automatically protect small cohorts; suppression and access controls may be needed.',
    ['Do not label a mean of site accuracies as example-weighted accuracy.', 'Do not infer quality at sites that did not report.', 'Do not publish unstable rare-event rates from tiny local denominators.'],
    ['machine-learning/federated-client-data-and-target-contract','machine-learning/client-participation-and-dropout-audit','machine-learning/non-iid-client-drift-and-local-steps','machine-learning/federated-release-review-project'])


add('federated-release-review-project',
    'Project: federated depot model release review',
    'A federated release review joins label compatibility, accepted-client coverage, site-level performance, update controls and rollback into one decision packet.', [
    ('Freeze the round design', 'Three repair depots train a 37-day follow-up predictor. Before the run, freeze label maturity, feature units, crop version, starting checkpoint, eligible-client list, local epoch budget and update rejection rules. Keep later-period local test sets untouched until round selection ends. [[machine-learning/federated-client-data-and-target-contract|The client contract]] identifies the fields that must agree.'),
    ('Compare sensible alternatives', 'Evaluate a local-only baseline at each depot, a global model trained with example-weighted updates, and an equal-site weighting candidate. Use the same local holdouts and action threshold for the comparison. Record communication rounds and total upload bytes as well as error costs. [[machine-learning/federated-aggregation-and-weighting|Weighted aggregation]] specifies the numerical choice.'),
    ('Review who contributed', 'Count eligible, invited, finished, accepted and stale clients by round and site type. If one remote depot rarely participates, its eventual test result still matters. Inspect update disagreement and local-step sensitivity without treating either as proof of causality. [[machine-learning/client-participation-and-dropout-audit|Dropouts]] and [[machine-learning/non-iid-client-drift-and-local-steps|client drift]] need separate readings.'),
    ('Evaluate the target population', 'Report micro and macro performance, the worst site, rare-failure recall with mature-positive counts, and calibration by depot. A global gain that fails a small depot’s minimum standard is a hold. The code below applies explicit gates to a hypothetical packet; it does not train a model or establish a privacy guarantee. [[machine-learning/federated-site-evaluation-and-denominators|Site denominators]] belong beside every result.'),
    ('Check the security and rollback path', 'Verify update authentication, allowed metadata, server retention, threat model, compatible client versions and rollback to the previous checkpoint. A shadow run can test logging before decisions use the new model. [[privacy-aware-ml/federated-updates-and-aggregation-risk|Update exposure]] remains relevant even with no raw image transfer.')],
    '''release_packet = {
    "contract_versions_match": True,
    "accepted_client_fraction": 0.75,
    "micro_accuracy_gain": 0.024,
    "worst_site_recall": 0.58,
    "minimum_site_recall": 0.64,
    "rare_event_support_checked": True,
    "update_security_reviewed": True,
    "rollback_checkpoint_kept": True,
}

def federated_release_gate(packet):
    holds = []
    if not packet["contract_versions_match"] or packet["accepted_client_fraction"] < 0.70:
        holds.append("client contract or coverage")
    if packet["micro_accuracy_gain"] <= 0 or packet["worst_site_recall"] < packet["minimum_site_recall"]:
        holds.append("site performance")
    if not all(packet[key] for key in (
        "rare_event_support_checked", "update_security_reviewed", "rollback_checkpoint_kept"
    )):
        holds.append("release controls")
    return "hold: " + ", ".join(holds) if holds else "eligible for shadow evaluation"

assert federated_release_gate(release_packet) == "hold: site performance"''',
    'The gate is O(1). Producing its evidence requires repeated local training, communication rounds, mature holdouts, site-level evaluation and an update security review. The numerical thresholds are example deployment rules, not universal defaults. Preserve the previous model and preprocessing versions until a rollback drill passes.',
    ['Do not promote from a pooled gain when one depot fails its minimum.', 'Do not claim private training from local data residence alone.', 'Do not ignore nonparticipating sites or stale update packets.'],
    ['machine-learning/federated-client-data-and-target-contract','machine-learning/federated-aggregation-and-weighting','machine-learning/non-iid-client-drift-and-local-steps','machine-learning/client-participation-and-dropout-audit','machine-learning/federated-site-evaluation-and-denominators','privacy-aware-ml/federated-updates-and-aggregation-risk'])


publish_batch(
    lessons,
    module_title='Federated training and site-level evaluation',
    module_summary='Align local data contracts, aggregate compatible updates, audit participation and drift, then evaluate every deployment site.',
    project_heading='Federated depot model release review',
    crosslinks=[
        ('privacy-aware-ml/federated-updates-and-aggregation-risk', lessons[0]['path']),
        ('machine-learning/ensemble-release-review-project', lessons[1]['path']),
        ('machine-learning/negative-transfer-by-target-slice', lessons[2]['path']),
        ('machine-learning/online-updates-with-delayed-feedback', lessons[3]['path']),
        ('machine-learning/group-error-gaps-and-policy-audit', lessons[4]['path']),
        ('privacy-aware-ml/learner-aggregate-release-project', lessons[5]['path']),
    ],
    sort_start=6000,
)
