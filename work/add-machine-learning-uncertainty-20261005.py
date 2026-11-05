"""Add original Machine Learning lessons for prediction uncertainty and review."""
from ml_fixture_writer_20261005 import publish_batch

lessons = []


def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='machine-learning/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))


add('split-conformal-clearance-intervals',
    'Split conformal intervals for clearance forecasts',
    'Split conformal regression uses absolute errors from a held-out calibration set to place an empirical margin around a fixed point predictor.', [
    ('Reserve a calibration cohort', 'A shipment model predicts hours until clearance. Fit the predictor on training shipments, select its settings on development data, then freeze it before scoring a separate calibration cohort. None of those calibration outcomes may have influenced the model or preprocessing. The margin comes from absolute calibration residuals, not training residuals. [[machine-learning/group-and-time-validation|The split guide]] explains why related shipments and future timestamps must not leak between roles.'),
    ('Choose a finite-sample rank', 'For a requested miscoverage fraction alpha and n calibration residuals, use the rank ceiling of (n plus one) times (one minus alpha), with one-based indexing. When that rank exceeds n, a finite margin cannot support the requested finite-sample claim without a wider convention; the code raises instead of quietly taking the largest observed error. The resulting interval is the point forecast plus or minus the selected residual. It is a teaching implementation of the split procedure.'),
    ('State the coverage scope', 'The familiar marginal coverage guarantee relies on calibration and future examples being exchangeable under the prediction procedure. A later warehouse policy, selective labeling or dependent repeated scans can break that condition. Marginal coverage does not mean every site, backlog range or individual shipment has the same coverage. [[machine-learning/interval-coverage-by-operating-slice|Slice coverage]] checks where the global margin is too small.'),
    ('Separate width from usefulness', 'An interval that covers nearly every eventual clearance time by spanning several days may not help dispatch. Report empirical coverage, median or mean width and the proportion of intervals crossing the staffing decision boundary. Compare against a simple historical route interval on the same future cohort. [[machine-learning/regression-baselines-and-holdout-metrics|The regression baseline]] anchors the point-prediction comparison; neither score alone establishes decision value.'),
    ('Do not recycle the final test', 'Use calibration once under a frozen method, then evaluate interval behavior on a later test period. Changing alpha, strata or feature engineering after examining final-test misses turns the test into development data. Record training, calibration and test IDs, model version and prediction timestamp. [[machine-learning/uncertainty-and-escalation-review-project|The applied review]] checks all three roles.')],
    '''from math import ceil

# The predictor is already fitted; these are untouched calibration predictions.
calibration_actual = [6, 8, 5, 10, 7, 9, 4, 11, 8]
calibration_forecast = [5, 7, 6, 8, 7, 8, 6, 9, 7]

def conformal_margin(actual, predicted, alpha):
    if not actual or len(actual) != len(predicted) or not 0 < alpha < 1:
        raise ValueError("aligned calibration rows and valid alpha required")
    residuals = sorted(abs(observed - forecast)
                       for observed, forecast in zip(actual, predicted))
    rank = ceil((len(residuals) + 1) * (1 - alpha))
    if rank > len(residuals):
        raise ValueError("calibration sample too small for finite margin")
    return residuals[rank - 1]

margin = conformal_margin(calibration_actual, calibration_forecast, alpha=0.20)
future_forecast = 8
future_interval = (future_forecast - margin, future_forecast + margin)
assert margin == 2
assert future_interval == (6, 10)''',
    'For N calibration cases, sorting residuals costs O(N log N) time and O(N) memory; serving an interval around an existing forecast is O(1). Recalibration requires new, eligible labels and a renewed exchangeability assessment, not merely a fast quantile calculation.',
    ['Do not calculate the margin from training residuals or a tuned final test.', 'Do not describe marginal coverage as a per-site or per-shipment guarantee.', 'Do not substitute the largest residual when the requested rank exceeds the sample.'],
    ['machine-learning/interval-coverage-by-operating-slice','machine-learning/regression-error-slices-and-tail-cost','machine-learning/group-and-time-validation','machine-learning/uncertainty-and-escalation-review-project'])


add('interval-coverage-by-operating-slice',
    'Prediction interval coverage by operating slice',
    'Interval auditing reports the fraction of later outcomes inside each issued range and the range width by site or operating condition, with support counts.', [
    ('Audit issued intervals, not reconstructed ones', 'A clearance forecast is useful only if its range was available when dispatch acted. Store lower and upper bounds with model version and intake timestamp. When the shipment later clears, compare the outcome with those original bounds. Recomputing an interval after its outcome is known destroys the evaluation. The code groups fixed predictions by site and reports coverage, mean width and support. [[machine-learning/split-conformal-clearance-intervals|The conformal lesson]] explains one way those bounds might be created.'),
    ('Keep the denominator visible', 'Two covered shipments out of two produce 100-percent observed coverage but very little evidence. Report the number of mature outcomes for every slice and compare with the number scored. Slow shipments may not have cleared yet, so evaluating only resolved cases can make the range appear too good. [[machine-learning/feature-drift-and-delayed-label-monitoring|Delayed-label monitoring]] provides the maturity rule. The code assumes its input rows are already eligible.'),
    ('Inspect width alongside hits', 'A site can achieve high coverage by issuing unusably wide ranges. Report width by site and by backlog band; compare the width with staffing lead time or service window. A range that crosses every action threshold may leave dispatch with no better decision than a baseline. Pair interval coverage with point error and tail underestimation. [[machine-learning/regression-error-slices-and-tail-cost|The tail guide]] captures one-sided harm.'),
    ('Understand the global-to-local gap', 'A globally calibrated residual margin can under-cover an overnight site if that site has more variable clearance times. The audit identifies the gap; it does not make a small local calibration set reliable. Consider better features, a valid stratified calibration design or a broader margin, and test changes on a new period. Avoid repeatedly optimizing slice-specific widths against the final holdout.'),
    ('Escalate only when the range changes an action', 'Define a review rule for intervals crossing a dispatch deadline or exceeding a width budget. Measure the review queue, coverage among accepted predictions and outcomes among escalated cases. High selective accuracy can be obtained by escalating nearly everything. [[machine-learning/selective-prediction-and-review-capacity|Selective prediction]] shows how to report both error and workload.')],
    '''issued_ranges = [
    ("Harbor", 7, 5, 9), ("Harbor", 12, 7, 11),
    ("Harbor", 8, 6, 10), ("Inland", 4, 2, 6),
    ("Inland", 9, 6, 10), ("Inland", 11, 7, 10),
]

def coverage_report(rows):
    grouped = {}
    for site, actual, lower, upper in rows:
        if lower > upper:
            raise ValueError("reversed interval")
        grouped.setdefault(site, []).append((lower <= actual <= upper, upper - lower))
    return {
        site: {
            "support": len(results),
            "coverage": sum(hit for hit, _ in results) / len(results),
            "mean_width": sum(width for _, width in results) / len(results),
        }
        for site, results in grouped.items()
    }

report = coverage_report(issued_ranges)
assert report["Harbor"]["coverage"] == 2 / 3
assert report["Inland"]["coverage"] == 2 / 3
assert report["Harbor"]["support"] == 3''',
    'Auditing M issued intervals costs O(M) expected time and O(S) grouped summary state for S slices; the teaching code stores per-row results and uses O(M) memory. Data retention, maturation checks and human review are the larger operating costs.',
    ['Do not recompute an issued interval using the observed outcome.', 'Do not report coverage without support and width.', 'Do not evaluate only fast-clearing cases when slow labels are pending.'],
    ['machine-learning/split-conformal-clearance-intervals','machine-learning/selective-prediction-and-review-capacity','machine-learning/feature-drift-and-delayed-label-monitoring','machine-learning/uncertainty-and-escalation-review-project'])


add('group-error-gaps-and-policy-audit',
    'Group error gaps and policy audit',
    'A group audit computes outcomes and error rates separately for relevant populations, then investigates differences in labels, exposure and intervention cost before changing policy.', [
    ('Specify the groups and action', 'A handoff alert sends a case to an overloaded review desk. Compare false-negative and false-positive rates by site, shift or another justified group; if people are affected, relevant protected-group analysis may also be required under the applicable governance process. A selection-rate difference alone does not explain why outcomes differ. The code reports confusion counts by site and exposes the denominator for each rate. [[machine-learning/decision-threshold-and-cost|The decision threshold]] defines what an alert means.'),
    ('Read rates with their denominators', 'False-negative rate divides missed handoffs without alerts by all actual misses. False-positive rate divides false alarms by all actual non-misses. A site with three positive outcomes cannot support the same confidence as a site with three thousand. Report raw counts, missing labels and the share eligible for evaluation. [[machine-learning/rare-event-precision-recall-and-prevalence|Prevalence]] can differ across sites, changing precision even at similar error rates.'),
    ('Audit measurement and exposure', 'A group gap may reflect scanner reliability, outcome definition, dispatch capacity or model behavior. Do not assume a single cause from the table. Intervention itself can change subsequent labels, making historical outcomes an imperfect counterfactual for a new policy. Review feature availability, sampling and target construction before changing thresholds. [[machine-learning/prediction-time-feature-availability|Feature timing]] and [[data-science/proxy-measurement-and-label-error|measurement error]] are separate checks.'),
    ('Avoid declaring fairness from one metric', 'Matching alert rates, false-negative rates and false-positive rates are different policy objectives; they need not agree when underlying event rates differ. Decide which harms and constraints matter to affected groups, then assess the tradeoffs with stakeholders and the relevant governance team. The table is diagnostic evidence, not a legal determination or a certificate of fairness. A model can pass an aggregate metric while failing a small intersectional slice.'),
    ('Recheck after deployment', 'Store group definitions, model version, threshold and outcome maturity rule with each report. Watch both error and review burden after a policy change, because a fixed threshold can drift when site mix changes. [[machine-learning/feature-drift-and-delayed-label-monitoring|The monitoring lesson]] supplies the delayed-label clock. [[machine-learning/uncertainty-and-escalation-review-project|The project]] combines subgroup error with escalation capacity.')],
    '''# Site, actual miss, alert issued. Rows are mature future outcomes.
cases = [
    ("Harbor", 1, 1), ("Harbor", 1, 0), ("Harbor", 0, 1),
    ("Harbor", 0, 0), ("Inland", 1, 1), ("Inland", 1, 1),
    ("Inland", 0, 0), ("Inland", 0, 0),
]

def site_error_audit(rows):
    sites = {}
    for site, actual, alert in rows:
        counts = sites.setdefault(site, {"tp": 0, "fn": 0, "fp": 0, "tn": 0})
        key = ("tp" if alert else "fn") if actual else ("fp" if alert else "tn")
        counts[key] += 1
    report = {}
    for site, counts in sites.items():
        positives = counts["tp"] + counts["fn"]
        negatives = counts["fp"] + counts["tn"]
        report[site] = {
            **counts,
            "positive_support": positives,
            "negative_support": negatives,
            "false_negative_rate": counts["fn"] / positives if positives else None,
            "false_positive_rate": counts["fp"] / negatives if negatives else None,
        }
    return report

audit = site_error_audit(cases)
assert audit["Harbor"]["false_negative_rate"] == 0.5
assert audit["Inland"]["false_positive_rate"] == 0
assert audit["Harbor"]["positive_support"] == 2''',
    'One pass over N mature labeled cases costs O(N) expected time and O(G) counters for G groups. Intersections increase G and shrink support. Reliable labels, protected-data handling where applicable, and review of policy effects cost more than the count operation.',
    ['Do not call a rate with tiny support a stable group property.', 'Do not equate one parity metric with a complete fairness assessment.', 'Do not compare groups whose outcome clocks or eligibility rules differ.'],
    ['machine-learning/selective-prediction-and-review-capacity','machine-learning/rare-event-precision-recall-and-prevalence','machine-learning/decision-threshold-and-cost','machine-learning/uncertainty-and-escalation-review-project'])


add('selective-prediction-and-review-capacity',
    'Selective prediction and review capacity',
    'A selective predictor acts automatically only on cases outside a declared uncertainty band and routes the remainder to review, trading automation coverage for error risk and human workload.', [
    ('Define acceptance and escalation before scoring', 'A missed-handoff probability below a low cutoff can be treated as routine; above a high cutoff it may trigger an alert; values between the cutoffs go to an analyst. The code uses fixed bounds on already-issued probabilities and reports the fraction handled automatically plus errors on those handled. The bounds are policy settings selected in development, not on the final test labels. [[machine-learning/probability-calibration|Calibration]] matters if the numeric bounds represent expected risk.'),
    ('Report coverage with selective error', 'An automated subset can look accurate because the system escalates every difficult case. Always pair error on accepted cases with the accepted fraction, counts, and outcomes among escalated cases. A policy handling five percent of traffic at zero observed error may still overload reviewers. Report the full population’s realized cost, not only a headline accepted accuracy. [[machine-learning/decision-threshold-and-cost|Decision costing]] turns each branch into a resource question.'),
    ('Measure queue capacity and delay', 'A human-review branch has arrival rate, service time and a deadline. If the queue cannot process all escalated shipments before dispatch closes, review is not an effective fallback. Set a maximum daily escalation volume and a timeout policy. Consider interval width or a missing-feature flag as an additional escalation trigger when raw probability does not capture uncertainty. [[machine-learning/interval-coverage-by-operating-slice|Interval coverage]] may expose the conditions that need review.'),
    ('Check group effects', 'A global uncertainty band may send far more cases from one site to manual review, or automate cases for a site where the model is less accurate. Audit acceptance, false negatives and review wait by group with support counts. [[machine-learning/group-error-gaps-and-policy-audit|The group audit]] is a diagnostic framework, not a guarantee that a chosen band is fair. Document the reason for different treatment if site-specific thresholds are considered.'),
    ('Keep feedback unbiased', 'If reviewers label only uncertain cases, their labels do not represent the automatically handled population. Reserve a random audit sample from automated decisions and maintain a later sealed evaluation cohort. Do not retrain from the review queue alone without addressing its selection mechanism. [[machine-learning/active-learning-uncertainty-and-diversity|Active learning]] uses selected labels for development while keeping evaluation separate.')],
    '''# Shipment ID, issued missed-handoff probability, mature outcome.
cases = [("S601", 0.08, 0), ("S602", 0.19, 0),
         ("S603", 0.43, 1), ("S604", 0.55, 0),
         ("S605", 0.82, 1), ("S606", 0.94, 1)]
low_cutoff, high_cutoff = 0.25, 0.75

def disposition(probability):
    if probability < low_cutoff:
        return "routine", 0
    if probability > high_cutoff:
        return "alert", 1
    return "review", None

decisions = [(shipment_id, *disposition(probability), actual)
             for shipment_id, probability, actual in cases]
automatic = [row for row in decisions if row[1] != "review"]
reviewed = [row for row in decisions if row[1] == "review"]
automatic_error_rate = sum(predicted != actual
                           for _, _, predicted, actual in automatic) / len(automatic)
automatic_coverage = len(automatic) / len(decisions)
assert automatic_coverage == 4 / 6
assert automatic_error_rate == 0
assert len(reviewed) == 2''',
    'Routing N issued scores costs O(N) time and O(1) counters if streamed. Review workload scales with escalated volume; latency and staffing cost can dominate model inference. Store issued decisions and outcomes to audit the entire policy, not only the accepted subset.',
    ['Do not report selective accuracy without automation coverage.', 'Do not assume human review is available before the decision deadline.', 'Do not evaluate future performance only from the selectively reviewed queue.'],
    ['machine-learning/group-error-gaps-and-policy-audit','machine-learning/interval-coverage-by-operating-slice','machine-learning/active-learning-uncertainty-and-diversity','machine-learning/uncertainty-and-escalation-review-project'])


add('ensemble-disagreement-and-outcome-noise',
    'Ensemble disagreement and outcome noise',
    'Variation among independently refitted models signals sensitivity to the training sample, while repeated outcome variability at similar inputs signals a different source of uncertainty.', [
    ('Do not call every spread the same uncertainty', 'Four shipment models trained on different valid samples may issue clearance forecasts of six, seven, nine and ten hours for one intake record. Their spread shows model sensitivity under that training protocol. It does not measure all future outcome variation, because every model can agree and still miss a sudden outage. The code reports between-model spread and the observed squared error of their mean on a small mature cohort.'),
    ('Construct refits without leakage', 'Train each model on a declared resample or fold within the permitted development window. Keep feature transformations inside each refit and do not let calibration or final-test outcomes train any member. Correlated models may agree for the wrong reason, so low disagreement is not a guarantee of reliability. [[machine-learning/bootstrap-bagging-and-out-of-bag-evaluation|The bagging lesson]] shows how training samples vary; the spread here has a different diagnostic purpose.'),
    ('Inspect residual noise separately', 'A center may have clearance time that varies because of random dock congestion not captured at intake. Even if refitted models agree on a seven-hour mean, individual outcomes can range widely. Compare issued forecasts with mature outcomes across similar operating conditions. That residual variation mixes unobserved process noise, measurement error and model misspecification; it is not a clean mathematical decomposition from a small table. [[machine-learning/regression-error-slices-and-tail-cost|Error slices]] identify where to investigate.'),
    ('Avoid false precision from a tiny ensemble', 'A standard deviation across four highly correlated models is not a calibrated prediction interval. Increasing members may stabilize the estimate of disagreement, but it cannot make a shifted future cohort exchangeable. If dispatch requires an interval with an explicit coverage target, use a separately calibrated procedure and audit it later. [[machine-learning/split-conformal-clearance-intervals|The conformal lesson]] states the relevant boundary and coverage scope.'),
    ('Turn uncertainty into a decision test', 'Compare whether high disagreement predicts future errors or only flags rare but easy routes. Record support, interval width, review volume and cost of unnecessary escalation. A review rule is useful only when it improves policy value under capacity constraints. [[machine-learning/selective-prediction-and-review-capacity|Selective prediction]] closes that loop.')],
    '''from math import sqrt

# Each tuple holds forecasts from independently refitted development models.
issued_forecasts = [(6, 7, 9, 10), (5, 5, 6, 6), (8, 8, 9, 9)]
mature_outcomes = [12, 5, 8]

def mean_and_spread(member_forecasts):
    center = sum(member_forecasts) / len(member_forecasts)
    spread = sqrt(sum((forecast - center) ** 2 for forecast in member_forecasts)
                  / len(member_forecasts))
    return center, spread

diagnostics = [mean_and_spread(members) for members in issued_forecasts]
mean_squared_error = sum((actual - center) ** 2
                         for actual, (center, _) in zip(mature_outcomes, diagnostics))
mean_squared_error /= len(mature_outcomes)
assert diagnostics[0][1] > diagnostics[1][1]
assert mean_squared_error > 0
assert diagnostics[0][0] == 8''',
    'For N cases and B model members, this diagnostic costs O(NB) time and O(N) summary storage when forecast vectors are streamed. Training B independent models and serving all B predictions can multiply compute and latency. Store only the detail needed for a reviewed decision.',
    ['Do not label ensemble spread a calibrated interval.', 'Do not infer irreducible noise from residuals without checking misspecification and label error.', 'Do not treat agreement among correlated models as certainty.'],
    ['machine-learning/bootstrap-bagging-and-out-of-bag-evaluation','machine-learning/split-conformal-clearance-intervals','machine-learning/selective-prediction-and-review-capacity','machine-learning/uncertainty-and-escalation-review-project'])


add('uncertainty-and-escalation-review-project',
    'Uncertainty and escalation review project',
    'Review a shipment forecast and handoff-alert workflow using a separate interval calibration cohort, group-level error audit, selective-review capacity and a final untouched period.', [
    ('Freeze the populations and clocks', 'Define the clearance-time target, missed-handoff event, intake feature snapshot and human-review deadline. Split training, tuning, calibration and final evaluation by shipment and appropriate time boundaries. Store original issued predictions so later labels cannot rewrite them. [[machine-learning/group-and-time-validation|The split guide]] and [[machine-learning/prediction-time-feature-availability|feature guide]] establish this record.'),
    ('Build the interval evidence', 'Fit a point predictor on training rows, freeze it, and derive a conformal residual margin on the calibration cohort. On the final future period, report interval coverage, width and costly underestimates globally and by site. Do not claim per-site coverage from a global marginal construction. [[machine-learning/split-conformal-clearance-intervals|Interval construction]] and [[machine-learning/interval-coverage-by-operating-slice|slice auditing]] are separate artifacts.'),
    ('Audit alert and escalation harms', 'For the handoff classifier, report class support, false negatives, false positives, automated acceptance and reviewer queue volume by site and relevant affected group. Examine target measurement and intervention effects before changing thresholds. [[machine-learning/group-error-gaps-and-policy-audit|The group audit]] does not certify fairness from one rate. [[machine-learning/selective-prediction-and-review-capacity|The review policy]] must fit the actual staffing window.'),
    ('Challenge apparent confidence', 'Compare ensemble disagreement with mature outcomes, then ask whether the signal catches difficult cases that a simpler rule misses. A low disagreement value is not a coverage promise. Keep the final period sealed until uncertainty and escalation rules are selected. [[machine-learning/ensemble-disagreement-and-outcome-noise|The disagreement guide]] gives the limitation.'),
    ('Record a bounded pilot decision', 'The code is a checklist over a separate review packet; it cannot compute exchangeability, subgroup validity or queue service time. Attach the measurements, owners, rollback path and next evaluation window. A missing condition holds the release discussion. Existing models and routes continue under their reviewed policy until a new decision is made.')],
    '''def uncertainty_release_gate(packet):
    checks = {
        "separate_calibration": "calibration boundary",
        "future_test_sealed": "future test",
        "issued_ranges_logged": "issued intervals",
        "slice_support_reported": "slice support",
        "review_queue_within_capacity": "review capacity",
        "mature_labels_checked": "mature labels",
        "rollback_owner_named": "rollback owner",
    }
    blockers = [reason for field, reason in checks.items() if not packet.get(field)]
    return "pilot review" if not blockers else "hold: " + ", ".join(blockers)

shipment_packet = {
    "separate_calibration": True,
    "future_test_sealed": True,
    "issued_ranges_logged": True,
    "slice_support_reported": False,
    "review_queue_within_capacity": False,
    "mature_labels_checked": True,
    "rollback_owner_named": True,
}
assert uncertainty_release_gate(shipment_packet) == (
    "hold: slice support, review capacity"
)''',
    'The gate costs O(K) for K checks. Residual calibration is O(N log N) when sorting N errors; future coverage and group counts are O(M) for M mature cases. The dominant operating cost may be human-review capacity and the time required for outcome labels to mature.',
    ['Do not use final outcomes to choose an interval margin or escalation band.', 'Do not claim that global interval coverage holds for every group.', 'Do not route cases to a review queue that cannot meet the action deadline.'],
    ['machine-learning/split-conformal-clearance-intervals','machine-learning/interval-coverage-by-operating-slice','machine-learning/group-error-gaps-and-policy-audit','machine-learning/selective-prediction-and-review-capacity','machine-learning/ensemble-disagreement-and-outcome-noise','machine-learning/feature-drift-and-delayed-label-monitoring'])


publish_batch(
    lessons,
    module_title='Uncertainty, group error and escalation',
    module_summary='Separate interval calibration, operating-slice coverage, group errors and review capacity.',
    project_heading='Uncertainty and escalation review',
    crosslinks=[
        ('machine-learning/regression-error-slices-and-tail-cost', lessons[0]['path']),
        ('machine-learning/split-conformal-clearance-intervals', lessons[1]['path']),
        ('machine-learning/rare-event-precision-recall-and-prevalence', lessons[2]['path']),
        ('machine-learning/decision-threshold-and-cost', lessons[3]['path']),
        ('machine-learning/bootstrap-bagging-and-out-of-bag-evaluation', lessons[4]['path']),
        ('machine-learning/ensemble-release-review-project', lessons[5]['path']),
    ],
    sort_start=5100,
)
