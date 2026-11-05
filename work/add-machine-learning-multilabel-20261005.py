"""Add original multi-label classification lessons and an applied review."""
from ml_fixture_writer_20261005 import publish_batch

lessons = []


def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='machine-learning/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))


add('multilabel-schema-and-unknown-targets',
    'Multi-label schema and unknown targets',
    'A multi-label target can assign several independent flags to one case, and each flag needs a distinct positive, negative or unknown annotation state.', [
    ('Choose the unit and vocabulary', 'A parcel incident can involve a broken seal and water damage at the same time. Define one parcel as the unit, then version the allowed label names and their meanings. A single multiclass field would force a false choice between coexisting conditions. [[machine-learning/multiclass-confusion-and-action-costs|Multiclass evaluation]] applies when exactly one class is assigned; the distinction changes both training data and metrics.'),
    ('Keep unknown distinct from negative', 'A reviewer may have inspected the seal but not the interior. The missing interior annotation is unknown, not evidence that water damage is absent. The code validates explicit zero, one and unknown states, and counts observed supervision per label. If unknown is silently filled with zero, the model learns from invented negatives. [[data-annotation/label-unit-taxonomy-and-guidelines|Annotation guidelines]] must say which inspection establishes a negative.'),
    ('Treat each label as an action contract', 'Some flags merely route a parcel for manual review; others stop dispatch. Record the action, deadline and cost of a missed condition for every flag. Two labels may require the same action, but a model output should preserve the distinction if investigation or audit depends on it. [[machine-learning/per-label-thresholds-and-action-cost|Per-label thresholds]] convert scores into actions without forcing one global cutoff.'),
    ('Split at the parcel or incident group', 'Several photos, claims and scans from one parcel must remain in one training or evaluation partition. A related batch can share the same damage event. Splitting individual image rows at random makes memorization appear to be generalization. [[machine-learning/group-and-time-validation|Group and time validation]] defines a credible held-out cohort.'),
    ('Measure annotation coverage', 'Report how many cases were reviewed for each label and where unknown states concentrate. A rare label with six positives and many unknowns cannot support the same evaluation claim as a common, fully audited label. Revisit sampling and adjudication before choosing a more complex model. [[machine-learning/multilabel-metrics-and-denominators|Multi-label metrics]] need those denominators.')],
    '''labels = ("seal-breach", "water-damage", "address-mismatch")
parcel_annotations = [
    ("P941", {"seal-breach": 1, "water-damage": 0, "address-mismatch": None}),
    ("P942", {"seal-breach": 0, "water-damage": 1, "address-mismatch": 1}),
    ("P943", {"seal-breach": 1, "water-damage": None, "address-mismatch": 0}),
]

def supervision_counts(rows, vocabulary):
    counts = {label: {"positive": 0, "negative": 0, "unknown": 0}
              for label in vocabulary}
    for parcel_id, annotation in rows:
        if set(annotation) != set(vocabulary):
            raise ValueError("label vocabulary changed")
        for label in vocabulary:
            state = annotation[label]
            if state not in (0, 1, None):
                raise ValueError("invalid target state")
            bucket = "unknown" if state is None else ("positive" if state else "negative")
            counts[label][bucket] += 1
    return counts

report = supervision_counts(parcel_annotations, labels)
assert report["water-damage"] == {"positive": 1, "negative": 1, "unknown": 1}
assert report["seal-breach"]["positive"] == 2''',
    'Counting N parcels across L labels costs O(NL) time and O(L) summary memory. A dense target matrix costs O(NL) storage; sparse representations save space when most known labels are negative, but must still preserve unknown states. The expensive work is defining and auditing labels consistently.',
    ['Do not collapse an uninspected label into a negative.', 'Do not use a single multiclass category for conditions that can coexist.', 'Do not split related photos or claims across train and test.'],
    ['machine-learning/binary-relevance-and-label-dependence','machine-learning/per-label-thresholds-and-action-cost','machine-learning/multilabel-metrics-and-denominators','machine-learning/multilabel-release-review-project'])


add('binary-relevance-and-label-dependence',
    'Binary relevance and label dependence',
    'Binary relevance fits one classifier per label, giving a clear baseline while leaving relationships among labels to the shared features or a later joint model.', [
    ('Build the independent baseline first', 'For each parcel condition, train a binary head using only cases whose annotation for that label is known. Share a consistent feature snapshot but keep positive and negative denominators separate. The code shows two fixed linear heads over inspection features; a production training run would fit each head on its own eligible rows. [[machine-learning/multilabel-schema-and-unknown-targets|The schema lesson]] protects against treating missing labels as negatives.'),
    ('Understand the independence assumption', 'Separate heads do not directly condition one predicted label on another predicted label. If a torn seal and water damage often co-occur, shared image features may still capture both, but the architecture alone does not encode their dependence. A classifier chain or joint model can use label relationships, yet training-time true labels and serving-time predicted labels create different inputs for downstream heads. Evaluate that mismatch rather than assuming dependence always helps.'),
    ('Avoid learning a shortcut from the review process', 'A water-damage label might appear mostly on parcels escalated after a seal alert. A model can then learn reviewer selection rather than water damage. Audit who was inspected for each label, sample some routine parcels and compare error on a held-out fully audited subset. [[machine-learning/active-learning-uncertainty-and-diversity|Selected-label workflows]] have the same evaluation bias.'),
    ('Compare against joint training fairly', 'Keep parcel groups, label taxonomy, threshold-selection set and evaluation window fixed when comparing independent and joint models. Report per-label false negatives, exact-set errors and latency. A joint model can share compute but may make a rare label worse. [[machine-learning/multilabel-metrics-and-denominators|Metric denominators]] reveal that regression.'),
    ('Make serving cost explicit', 'L independent heads over a cached D-dimensional embedding require roughly O(LD) multiply-add work after encoding, while L separate full encoders would multiply the expensive stage. Monitor missing inputs and confidence by label. [[machine-learning/frozen-embedding-linear-probe|The frozen-probe lesson]] explains the representation option; [[machine-learning/per-label-thresholds-and-action-cost|action thresholds]] are selected separately.')],
    '''from math import exp

condition_heads = {
    "seal-breach": {"weights": (1.2, -0.4), "bias": -0.2},
    "water-damage": {"weights": (-0.3, 1.4), "bias": -0.3},
}

def condition_probabilities(inspection_features, heads):
    probabilities = {}
    for label, parameters in heads.items():
        score = sum(weight * value for weight, value in
                    zip(parameters["weights"], inspection_features))
        score += parameters["bias"]
        probabilities[label] = 1 / (1 + exp(-score))
    return probabilities

parcel_features = (1.8, 1.5)  # Seal anomaly and moisture signal.
scores = condition_probabilities(parcel_features, condition_heads)
assert scores["seal-breach"] > 0.7
assert scores["water-damage"] > 0.7''',
    'For L labels and D input features, inference through L linear heads costs O(LD) time and O(LD) stored weights, after feature extraction. Fitting L separate models also multiplies validation work. A shared encoder can dominate latency and memory, so measure the full path rather than head arithmetic alone.',
    ['Do not train a head on unknown labels converted to zero.', 'Do not claim independent heads prove labels are independent in the world.', 'Do not compare model families using different annotation-eligibility rules.'],
    ['machine-learning/multilabel-schema-and-unknown-targets','machine-learning/per-label-thresholds-and-action-cost','machine-learning/multilabel-metrics-and-denominators','machine-learning/multilabel-release-review-project'])


add('per-label-thresholds-and-action-cost',
    'Per-label thresholds and action cost',
    'Each multi-label score can have its own decision threshold when missed conditions and unnecessary reviews have different costs.', [
    ('Start with calibrated score meaning', 'A seal-breach score and address-mismatch score need not share the same prevalence or cost. A single 0.5 cutoff may route too many address cases while missing costly seal failures. Estimate thresholds on a development cohort using a declared cost for false alarms and misses. If scores are used as probabilities, check their calibration per label first. [[machine-learning/probability-calibration|Calibration]] must be assessed on cases with mature, known labels.'),
    ('Select without touching the final test', 'The code evaluates a small grid of thresholds for each label using its known development rows. It chooses the lowest cost and reports the chosen cutoff. This is a teaching selector, not a claim that a small grid or six rows is enough for deployment. Reserve a later test cohort for the policy’s actual error and workload. [[machine-learning/hyperparameter-search-and-untouched-test|The untouched-test guide]] treats a threshold as a tuned choice.'),
    ('Check combined workload', 'Per-label cutoffs can each look affordable while their union sends too many parcels to a shared review desk. Deduplicate case-level actions and measure how many unique parcels are escalated. If one flag blocks dispatch while another asks for routine inspection, define precedence. [[machine-learning/selective-prediction-and-review-capacity|Review capacity]] is a case-level constraint, not the sum of separate label metrics.'),
    ('Keep unknown outcomes out of cost fitting', 'Only labels that were actually assessed belong in that label’s threshold calculation. A parcel can contribute to seal-breach selection and remain unknown for water damage. Report eligible support by label and site so a low estimated cost is not mistaken for strong evidence. [[machine-learning/multilabel-schema-and-unknown-targets|Unknown-state handling]] makes this explicit.'),
    ('Watch policy interactions', 'A dispatch stop caused by one predicted flag can prevent later observation of another condition. After deployment, outcome labels may depend on the action itself. Log the issued labels, final action and inspection pathway; sample a fixed audit cohort where possible. [[machine-learning/group-error-gaps-and-policy-audit|Group error auditing]] and [[machine-learning/multilabel-release-review-project|the project review]] cover those consequences.')],
    '''development = {
    "seal-breach": [(0.12, 0), (0.37, 1), (0.61, 1), (0.84, 1)],
    "address-mismatch": [(0.14, 0), (0.42, 0), (0.67, 1), (0.79, 1)],
}
costs = {"seal-breach": {"miss": 7, "false_alarm": 1},
         "address-mismatch": {"miss": 2, "false_alarm": 3}}
candidates = (0.25, 0.50, 0.75)

def choose_cutoffs(rows_by_label, cost_by_label, cutoffs):
    selected = {}
    for label, rows in rows_by_label.items():
        if not rows:
            raise ValueError("missing development labels")
        def total_cost(cutoff):
            return sum(cost_by_label[label]["miss"] if score < cutoff and truth else
                       cost_by_label[label]["false_alarm"] if score >= cutoff and not truth else 0
                       for score, truth in rows)
        selected[label] = min(cutoffs, key=lambda cutoff: (total_cost(cutoff), cutoff))
    return selected

cutoffs = choose_cutoffs(development, costs, candidates)
assert cutoffs == {"seal-breach": 0.25, "address-mismatch": 0.50}''',
    'Searching T candidate thresholds over N labeled rows for each of L labels costs O(LTN) in the simple implementation and O(L) output space. Sorting scores can reduce repeated scans. Operational review volume and delayed labels dominate the cost of selecting a numeric cutoff.',
    ['Do not tune thresholds on the final test.', 'Do not ignore the union of per-label alerts hitting one review queue.', 'Do not fit cost on labels that were never inspected.'],
    ['machine-learning/multilabel-schema-and-unknown-targets','machine-learning/multilabel-metrics-and-denominators','machine-learning/multilabel-calibration-and-cardinality','machine-learning/multilabel-release-review-project'])


add('multilabel-metrics-and-denominators',
    'Multi-label metrics and denominators',
    'Multi-label evaluation needs both case-level and label-level measures because one case can have several correct and incorrect flags.', [
    ('Report exact-set and per-label error separately', 'Exact-set accuracy credits a parcel only when every predicted flag matches every known true flag. Hamming loss counts incorrect label assignments divided by assessed case-label pairs. Exact-set accuracy becomes harder as the number of labels grows; Hamming loss can look small when most labels are negative. The code computes both on a fully annotated illustrative cohort. [[machine-learning/multilabel-schema-and-unknown-targets|Unknown labels]] require masking and adjusted denominators in a real audit.'),
    ('Distinguish micro from macro F1', 'Micro F1 pools true positives, false positives and false negatives across labels before combining precision and recall. Macro F1 computes F1 for each label and averages them equally. A frequent seal label can dominate the pooled result while a rare safety flag fails. Display each label’s support and confusion counts alongside both summaries. [[machine-learning/rare-event-precision-recall-and-prevalence|Rare-event precision]] explains why prevalence matters.'),
    ('Choose metrics from the action', 'A parcel with one missed critical flag may be worse than three unnecessary low-cost flags. Exact-set and F1 numbers alone do not encode that distinction. Include per-label false-negative cost, unique parcels sent to review and deadline misses. [[machine-learning/per-label-thresholds-and-action-cost|Threshold selection]] should use the same action contract that evaluation reports.'),
    ('Handle undefined results deliberately', 'A label with no positive cases has undefined recall; a label with no predicted positives has undefined precision. Do not silently turn these into a perfect score. Report support and the chosen zero-division convention, or withhold a metric until there is adequate evidence. Splitting by site and camera reduces support further. [[machine-learning/group-error-gaps-and-policy-audit|Group auditing]] keeps denominators visible.'),
    ('Protect the evaluation population', 'Use parcel-grouped and time-appropriate held-out data. If only difficult parcels receive full inspection, the fully annotated subset is selected and its metrics may not describe routine traffic. Record inclusion rules and a random audit sample when feasible. [[machine-learning/multilabel-release-review-project|The project]] asks for both model metrics and annotation coverage.')],
    '''label_order = ("seal", "water", "address")
actual = [(1, 1, 0), (1, 0, 0), (0, 1, 1), (0, 0, 1)]
predicted = [(1, 0, 0), (1, 0, 0), (0, 1, 0), (1, 0, 1)]

def multilabel_report(truth_rows, predicted_rows, labels):
    if len(truth_rows) != len(predicted_rows) or not truth_rows:
        raise ValueError("aligned evaluated cases required")
    exact = sum(truth == prediction for truth, prediction in
                zip(truth_rows, predicted_rows)) / len(truth_rows)
    mistakes = sum(left != right for truth, prediction in
                   zip(truth_rows, predicted_rows) for left, right in
                   zip(truth, prediction))
    counts = {}
    for position, label in enumerate(labels):
        tp = sum(t[position] == 1 and p[position] == 1 for t, p in zip(truth_rows, predicted_rows))
        fp = sum(t[position] == 0 and p[position] == 1 for t, p in zip(truth_rows, predicted_rows))
        fn = sum(t[position] == 1 and p[position] == 0 for t, p in zip(truth_rows, predicted_rows))
        counts[label] = {"tp": tp, "fp": fp, "fn": fn, "support": tp + fn}
    pooled = {name: sum(item[name] for item in counts.values()) for name in ("tp", "fp", "fn")}
    def f1(item):
        denominator = 2 * item["tp"] + item["fp"] + item["fn"]
        return 2 * item["tp"] / denominator if denominator else None
    return {"exact_set_accuracy": exact,
            "hamming_loss": mistakes / (len(truth_rows) * len(labels)),
            "micro_f1": f1(pooled),
            "macro_f1": sum(f1(item) for item in counts.values()) / len(counts),
            "by_label": counts}

report = multilabel_report(actual, predicted, label_order)
assert report["exact_set_accuracy"] == 0.25
assert report["hamming_loss"] == 0.25
assert report["by_label"]["water"]["fn"] == 1''',
    'Computing counts over N cases and L labels costs O(NL) time and O(L) summary memory. A dense indicator matrix costs O(NL) storage; streaming counts avoids it when issued predictions and mature labels can be joined safely. Fully audited target cases are the limiting resource.',
    ['Do not describe exact-set accuracy as ordinary per-label accuracy.', 'Do not report macro F1 without per-label support and undefined-rate handling.', 'Do not include unknown annotations in a negative-label denominator.'],
    ['machine-learning/multilabel-schema-and-unknown-targets','machine-learning/per-label-thresholds-and-action-cost','machine-learning/multilabel-calibration-and-cardinality','machine-learning/multilabel-release-review-project'])


add('multilabel-calibration-and-cardinality',
    'Multi-label calibration and label cardinality',
    'Each label can have a different probability calibration curve, while the number of true or predicted labels per case reveals a separate change in case mix.', [
    ('Calibrate each condition on eligible outcomes', 'A score of 0.7 for water damage should be checked against observed water outcomes among comparable, fully inspected parcels. A good seal-breach reliability curve does not certify the water score. The code summarizes mean predicted risk and observed event rate by label over a fixed mature cohort. A single four-case mean is only a diagnostic; real calibration needs support across risk ranges. [[machine-learning/probability-calibration|Probability calibration]] explains binning and independent calibration data.'),
    ('Measure label cardinality separately', 'Cardinality is the average number of positive labels per case. It can change if parcels sustain more compound damage, if annotation rules expand or if model thresholds move. Compare actual cardinality on mature fully audited cases with predicted cardinality at the issued cutoffs. A changed prediction count alone is not proof of a changed real condition rate. [[machine-learning/multilabel-schema-and-unknown-targets|The label schema]] must stay versioned.'),
    ('Keep probability and action distinct', 'Calibrating each label’s score does not choose a review threshold or guarantee that combined case-level actions fit capacity. A model can be well calibrated yet send too many parcels to inspection when several labels trigger together. [[machine-learning/per-label-thresholds-and-action-cost|Per-label costing]] and [[machine-learning/selective-prediction-and-review-capacity|review capacity]] turn risk into policy.'),
    ('Watch selective inspection', 'A water label may be observed only when the parcel was already routed to review. Then observed water prevalence and apparent calibration are conditional on inspection. Keep a random audit stream or evaluate an identified fully inspected cohort; report what population the curve represents. [[data-annotation/active-learning-and-selection-bias|Selection in labeling]] can invalidate a naive reliability chart.'),
    ('Review changing co-occurrence', 'Even stable per-label rates can hide a rise in cases with both seal and water damage. Track common pairs with support and compare the cost of combined actions. Do not fit an elaborate dependence model from sparse pairs. [[machine-learning/binary-relevance-and-label-dependence|Binary relevance]] is a sensible baseline; [[machine-learning/multilabel-release-review-project|the release review]] checks the joint workload.')],
    '''label_order = ("seal", "water")
issued = [((0.8, 0.2), (1, 0)), ((0.6, 0.7), (1, 1)),
          ((0.3, 0.4), (0, 0)), ((0.2, 0.9), (0, 1))]
cutoffs = {"seal": 0.5, "water": 0.6}

def calibration_and_cardinality(rows, labels, thresholds):
    summary = {}
    for position, label in enumerate(labels):
        mean_risk = sum(scores[position] for scores, _ in rows) / len(rows)
        observed_rate = sum(truth[position] for _, truth in rows) / len(rows)
        summary[label] = {"mean_risk": mean_risk, "observed_rate": observed_rate}
    true_cardinality = sum(sum(truth) for _, truth in rows) / len(rows)
    predicted_cardinality = sum(
        sum(scores[position] >= thresholds[label]
            for position, label in enumerate(labels)) for scores, _ in rows
    ) / len(rows)
    return summary, true_cardinality, predicted_cardinality

calibration, actual_count, predicted_count = calibration_and_cardinality(
    issued, label_order, cutoffs)
assert actual_count == 1.0
assert predicted_count == 1.0
assert calibration["water"]["observed_rate"] == 0.5''',
    'Scanning N mature cases and L labels costs O(NL) time and O(L) summary memory. Calibration by risk range and operating slice needs enough positive and negative outcomes in each cell, which often makes label collection more expensive than scoring.',
    ['Do not use a pooled calibration curve to certify every label.', 'Do not infer true cardinality from issued predictions without mature labels.', 'Do not evaluate only parcels selected for inspection and call it population calibration.'],
    ['machine-learning/multilabel-schema-and-unknown-targets','machine-learning/binary-relevance-and-label-dependence','machine-learning/per-label-thresholds-and-action-cost','machine-learning/multilabel-release-review-project'])


add('multilabel-release-review-project',
    'Multi-label parcel review project',
    'Review a parcel-condition model with unknown annotation states, separate label cutoffs, case-level review workload, per-label errors and a sealed target period.', [
    ('Freeze the inspection and label contract', 'Define the parcel or incident unit, the allowed condition flags and which inspection establishes each negative. Keep unknown annotations distinct from confirmed absence. Group related photos and preserve a later target period. [[machine-learning/multilabel-schema-and-unknown-targets|The schema lesson]] is the record of these decisions.'),
    ('Build a transparent first model', 'Use a binary head per label on eligible training rows, then compare any joint-label alternative on the same grouped development cohort. Record feature timing and annotation coverage. [[machine-learning/binary-relevance-and-label-dependence|The baseline]] shows what a joint model must improve.'),
    ('Select the action policy', 'Choose per-label cutoffs using declared costs and an isolated development set. Combine triggered flags into unique parcel actions and check the actual review desk’s deadline and capacity. Do not choose cutoffs from final-test outcomes. [[machine-learning/per-label-thresholds-and-action-cost|Cost selection]] and [[machine-learning/selective-prediction-and-review-capacity|review capacity]] are both needed.'),
    ('Evaluate the right denominators', 'Report exact-set accuracy, Hamming loss, micro and macro F1, per-label support, false negatives, calibration and average true and predicted label count. These describe different properties; no one score is a release verdict. Check depot and camera slices and disclose selectively inspected labels. [[machine-learning/multilabel-metrics-and-denominators|The metric guide]] and [[machine-learning/multilabel-calibration-and-cardinality|calibration guide]] define the reports.'),
    ('Name the bounded next step', 'The code checks evidence fields in a release packet. It cannot decide whether measured misses or costs are acceptable. Attach the actual values, the owner, a rollback route and the next evaluation window; hold the pilot review if label coverage or capacity is still unknown.')],
    '''def multilabel_review_gate(packet):
    required = {
        "unknowns_preserved": "unknown labels",
        "parcel_groups_sealed": "parcel groups",
        "cutoffs_selected_on_development": "development cutoffs",
        "per_label_support_reported": "label support",
        "case_review_capacity_checked": "review capacity",
        "calibration_audited": "label calibration",
        "rollback_owner_named": "rollback owner",
    }
    missing = [label for field, label in required.items() if not packet.get(field)]
    return "eligible for pilot review" if not missing else "hold: " + ", ".join(missing)

parcel_packet = {
    "unknowns_preserved": True, "parcel_groups_sealed": True,
    "cutoffs_selected_on_development": True,
    "per_label_support_reported": False,
    "case_review_capacity_checked": False,
    "calibration_audited": True, "rollback_owner_named": True,
}
assert multilabel_review_gate(parcel_packet) == (
    "hold: label support, review capacity"
)''',
    'The gate costs O(K) for K checks. Multi-label evaluation over N cases and L conditions is O(NL), while a T-threshold grid is O(LTN) in a direct implementation. The larger operating costs are complete annotation, review capacity and validation across parcel groups and time.',
    ['Do not replace unknown target states with negatives.', 'Do not release from a single pooled metric when a rare costly label fails.', 'Do not sum per-label alert counts and mistake them for unique parcels requiring review.'],
    ['machine-learning/multilabel-schema-and-unknown-targets','machine-learning/binary-relevance-and-label-dependence','machine-learning/per-label-thresholds-and-action-cost','machine-learning/multilabel-metrics-and-denominators','machine-learning/multilabel-calibration-and-cardinality','data-annotation/label-unit-taxonomy-and-guidelines'])


publish_batch(
    lessons,
    module_title='Multi-label classification and decisions',
    module_summary='Preserve unknown labels, train clear baselines, select per-label actions and evaluate both cases and labels.',
    project_heading='Multi-label parcel review',
    crosslinks=[
        ('machine-learning/multiclass-confusion-and-action-costs', lessons[0]['path']),
        ('machine-learning/frozen-embedding-linear-probe', lessons[1]['path']),
        ('machine-learning/decision-threshold-and-cost', lessons[2]['path']),
        ('machine-learning/rare-event-precision-recall-and-prevalence', lessons[3]['path']),
        ('machine-learning/probability-calibration', lessons[4]['path']),
        ('machine-learning/transfer-learning-release-review-project', lessons[5]['path']),
    ],
    sort_start=5500,
)
