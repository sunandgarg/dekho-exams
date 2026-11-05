"""Add original ROC, confusion-matrix and EWMA visualization lessons."""
from data_visualization_batch import publish

prefix = "data-visualization/"
lessons = [
    {
        "slug": "roc-curves-tied-thresholds-false-positive-rates-and-partial-auc",
        "title": "ROC curves: read attainable thresholds and false-positive rates",
        "summary": "Build a binary ROC curve without splitting tied scores, then place AUC beside the operating point and cohort counts.",
        "sections": [
            ("Define both error denominators", "A receiver operating characteristic curve plots true-positive rate against false-positive rate as a score threshold moves. True-positive rate divides captured events by all actual events. False-positive rate divides false alerts by all actual non-events. The latter is not the fraction of alerts that are false. State which label is positive, when the score was produced and when outcomes became final. A hospital or factory may need a low false-positive rate because follow-up capacity is limited, but the curve alone cannot decide the cost of an alert. [[data-visualization/precision-recall-curves-threshold-ties-prevalence-and-average-precision|Precision–recall curves]] put false alerts in the denominator of precision and often make alert workload easier to see. [[data-visualization/confusion-matrices-class-order-row-normalization-and-abstentions|A confusion matrix]] makes the counts behind one selected threshold explicit."),
            ("Sweep score ties as a single decision", "Sort evaluation records by descending score. Start at the no-alert point, false-positive rate zero and true-positive rate zero. Add every record at a distinct score together; equal scores cannot be separated by a threshold that uses the score alone. After each group, divide cumulative true positives by the total positives and cumulative false positives by total negatives. The last point is one, one when every eligible record has a finite score. Retain the actual staircase vertices. A plotting package may remove intermediate collinear points for display, but the operational threshold table must keep enough detail to identify each attainable selection. A score need not be a calibrated probability to produce an ROC curve. [[data-visualization/probability-calibration-plots-bin-counts-prevalence-and-drift|Calibration plots]] test that separate question."),
            ("Keep AUC in its place", "Trapezoidal ROC AUC summarizes ranking over the full false-positive-rate range. It can be interpreted as the probability that a randomly selected positive outranks a randomly selected negative, with half credit for a tie, under the evaluation population. A high overall AUC may still conceal weak performance in the low-false-positive region where the system can operate. If only that range matters, specify its bounds and normalization before reporting a partial AUC, and show the actual portion of the curve. Compare models on the same held-out records and labels. The ROC axes use rates that do not algebraically contain prevalence, yet precision and the number of false alarms at deployment do depend on the population mix. Print counts and the intended threshold beside AUC."),
            ("Test slices and uncertain tails", "A curve built from 47 positives can jump by more than two percentage points with each newly captured positive. Likewise, one false alert has a large horizontal effect when few negatives were evaluated. Publish total positives, negatives and score coverage; use uncertainty intervals or unit-level resampling when records are clustered by customer, machine or site. Avoid comparing curves whose outcome windows or eligibility filters differ. [[data-visualization/uncertainty-and-small-sample-display|Uncertainty displays]] need to reveal thin support, while [[data-visualization/small-multiples-shared-scales-and-facet-order|shared axes]] matter when models or sites appear in separate panels. If labels are delayed, do not quietly count pending cases as negatives. A companion table should include threshold, selected count and all four confusion-matrix cells at the chosen operating points."),
        ],
        "code": '''from math import isfinite

def roc_thresholds(records: list[tuple[str, float, bool]]):
    identifiers = [record_id for record_id, _, _ in records]
    if len(identifiers) != len(set(identifiers)) or any(not key for key in identifiers):
        raise ValueError("record IDs must be unique and nonempty")
    if any(not isfinite(score) or type(event) is not bool
           for _, score, event in records):
        raise ValueError("scores and labels must be valid")
    positives = sum(event for _, _, event in records)
    negatives = len(records) - positives
    if not positives or not negatives:
        raise ValueError("ROC needs both positive and negative records")
    ranked = sorted(records, key=lambda row: row[1], reverse=True)
    points = [(None, 0.0, 0.0, 0)]
    true_positives = false_positives = cursor = 0
    while cursor < len(ranked):
        threshold = ranked[cursor][1]
        while cursor < len(ranked) and ranked[cursor][1] == threshold:
            true_positives += ranked[cursor][2]
            false_positives += not ranked[cursor][2]
            cursor += 1
        points.append((threshold, false_positives / negatives,
                       true_positives / positives, cursor))
    area = sum((points[index][1] - points[index - 1][1]) *
               (points[index][2] + points[index - 1][2]) / 2
               for index in range(1, len(points)))
    return points, area

quality_scores = [("lot-47", 0.91, True), ("lot-59", 0.64, False),
                  ("lot-83", 0.64, True), ("lot-97", 0.18, False)]
points, area = roc_thresholds(quality_scores)
assert points[0] == (None, 0.0, 0.0, 0)
assert points[2] == (0.64, 0.5, 1.0, 3)
assert points[-1][1:3] == (1.0, 1.0)
assert area == 0.875''',
        "cost": "For N labeled records, sorting takes O(N log N) time, and the grouped threshold sweep plus trapezoid sum take O(N). The sorted records, uniqueness set and output points need O(N) space. This four-record audit proves a tied score creates one shared threshold point and yields area 0.875. It does not estimate uncertainty, calibrate scores or determine a safe operating threshold. Those need an evaluation design and a stated decision cost.",
        "mistakes": ["Calling false positives divided by all alerts the false-positive rate.", "Breaking score ties in input order and drawing unattainable thresholds.", "Choosing a model by full AUC when only a narrow false-positive range is usable.", "Comparing AUCs from different label windows or evaluation cohorts."],
        "drill": "Score 470 held-out production lots with confirmed outcomes. Mark every tied threshold, report the four confusion-matrix counts at the 47-alert operating point, and inspect the first 0.05 of false-positive rate separately.",
        "related": [prefix + "precision-recall-curves-threshold-ties-prevalence-and-average-precision", prefix + "confusion-matrices-class-order-row-normalization-and-abstentions", prefix + "probability-calibration-plots-bin-counts-prevalence-and-drift", prefix + "uncertainty-and-small-sample-display"],
    },
    {
        "slug": "confusion-matrices-class-order-row-normalization-and-abstentions",
        "title": "Confusion matrices: fix class order, denominators and abstentions",
        "summary": "Build a classification error ledger with actual rows, predicted columns, fixed labels and visible support for every class.",
        "sections": [
            ("Make axes a written contract", "A confusion matrix is a count ledger, not merely a colored square. Fix the class vocabulary and its order before comparing model versions. This lesson puts actual class on each row and predicted class on each column. A cell at row Delivery, column Returns therefore means a real Delivery ticket routed to Returns. Swapping axes changes the question while leaving a superficially similar image. Use the same class keys in tables, hover text, screen-reader descriptions and any export. [[data-visualization/heatmap-missing-cells-and-color-domain|Heatmap color scales]] should make count ranges readable, but numerical labels must remain available. On a sparse matrix, zero means no observed cases; it does not prove an error is impossible."),
            ("Keep counts and row rates together", "Raw counts show workload. Row-normalized values divide each cell by the number of actual cases in its row, making recall-like class comparisons possible. Column normalization divides by the number predicted as that class, answering a precision-like question. Whole-matrix normalization divides by all cases and answers a third question. Never label all three simply 'accuracy.' Print row totals and column totals so readers can audit the denominators. A model that gets 9,400 common cases right and misses 47 rare cases can have impressive overall accuracy but fail the rare-class task. [[data-visualization/aggregation-grain-and-denominator|Denominator design]] and [[data-visualization/precision-recall-curves-threshold-ties-prevalence-and-average-precision|precision–recall analysis]] provide the neighboring view for rare binary outcomes. If a class has zero actual cases, its row rate is undefined, not zero."),
            ("Treat abstention and missing truth separately", "Some classifiers can decline to assign a class. Represent abstain as a predicted column and report coverage, the share of eligible records receiving a concrete prediction. Do not drop abstentions before calculating performance unless a separate coverage-conditioned table is clearly labeled. Missing ground truth is different: those records cannot enter a verified confusion matrix at all, and their count should be disclosed alongside the eligible population. In a human-review workflow, only the reviewed cases may have labels, creating selection bias. A matrix built from those cases is not automatically representative of all incoming work. [[data-visualization/linked-filters-cohort-denominators-and-selection-state|Linked filters]] should make this labeled-cohort restriction visible at all times."),
            ("Compare the errors that matter", "The diagonal marks correct classifications; off-diagonal cells identify which mistakes occur. A stable class order and shared color domain let readers compare model versions without relearning the image. Sort classes by a documented domain order, not by each version's frequency. When there are dozens of labels, show a targeted subset or a table rather than shrinking every cell until it is unreadable. Report cost-relevant pairs explicitly: sending a fraud report to routine support may be more expensive than confusing two routine categories. [[data-visualization/small-multiples-shared-scales-and-facet-order|Small multiples]] help comparisons, while [[data-visualization/accessible-color-and-text-alternatives|text alternatives]] carry exact counts where color alone cannot. The matrix describes a fixed decision rule; a threshold sweep needs a separate ROC or precision–recall view."),
        ],
        "code": '''def classification_ledger(records: list[tuple[str, str, str]],
                          classes: list[str]):
    if (not classes or "Abstain" in classes or
            len(classes) != len(set(classes)) or any(not item for item in classes)):
        raise ValueError("class labels must be unique and nonempty")
    identifiers = [ticket_id for ticket_id, _, _ in records]
    if len(identifiers) != len(set(identifiers)) or any(not key for key in identifiers):
        raise ValueError("ticket IDs must be unique and nonempty")
    actual_positions = {name: index for index, name in enumerate(classes)}
    predicted_positions = {name: index for index, name in
                           enumerate(classes + ["Abstain"])}
    counts = [[0 for _ in predicted_positions] for _ in classes]
    for _, actual, predicted in records:
        if actual not in actual_positions or predicted not in predicted_positions:
            raise ValueError("unknown actual or predicted class")
        counts[actual_positions[actual]][predicted_positions[predicted]] += 1
    row_rates = []
    for row in counts:
        support = sum(row)
        row_rates.append([value / support for value in row] if support else None)
    assert sum(map(sum, counts)) == len(records)
    return counts, row_rates

ticket_routes = [("ticket-47", "Billing", "Billing"),
                 ("ticket-59", "Billing", "Delivery"),
                 ("ticket-83", "Delivery", "Delivery"),
                 ("ticket-97", "Delivery", "Returns"),
                 ("ticket-101", "Returns", "Returns"),
                 ("ticket-131", "Returns", "Billing")]
labels = ["Billing", "Delivery", "Returns", "Technical"]
counts, row_rates = classification_ledger(ticket_routes, labels)
assert counts[0][:3] == [1, 1, 0]
assert row_rates[0][:3] == [0.5, 0.5, 0.0]
assert row_rates[3] is None
assert sum(counts[index][index] for index in range(4)) == 3''',
        "cost": "For N records and K actual classes, ledger construction takes O(N + K²) time and O(N + K²) space: the unique-ID set stores N keys and each dense matrix has K rows and K+1 predicted columns, including Abstain. A sparse map can avoid empty cells when K is large. The code rejects an unknown actual or predicted label; missing actual labels require a separate exclusion ledger. The six-ticket assertion checks axis direction, row normalization and an undefined zero-support row, not model quality.",
        "mistakes": ["Flipping actual and predicted axes between dashboards.", "Displaying row-normalized color without support counts.", "Reporting an empty actual-class row as zero recall.", "Discarding abstentions or unreviewed cases without changing the cohort label."],
        "drill": "Audit 470 routed tickets across four service classes. Reconcile row and column totals, add an Abstain predicted column, and explain how coverage and per-class recall change between two model versions.",
        "related": [prefix + "roc-curves-tied-thresholds-false-positive-rates-and-partial-auc", prefix + "precision-recall-curves-threshold-ties-prevalence-and-average-precision", prefix + "heatmap-missing-cells-and-color-domain", prefix + "linked-filters-cohort-denominators-and-selection-state"],
    },
    {
        "slug": "ewma-control-charts-startup-limits-baseline-and-slow-drift",
        "title": "EWMA control charts: detect slow shifts against a frozen baseline",
        "summary": "Compute a time-ordered exponentially weighted trace with startup limits, then separate process signals from specification failures.",
        "sections": [
            ("Freeze a trustworthy reference process", "An exponentially weighted moving average, or EWMA, updates a running statistic from each new observation. Before monitoring, estimate or choose a target mean and process spread from an in-control reference period. Record the unit, subgroup definition, sampling interval, instrument version and baseline dates. A baseline contaminated by a slow fault will normalize that fault away. Control limits describe variation expected under the reference process; they are not engineering specification limits for an individual product. [[data-visualization/p-charts-varying-denominators-and-process-baselines|P charts]] handle binomial proportions with varying denominators, whereas this worked EWMA assumes comparable numeric observations with one historical spread estimate. A process can remain in statistical control while producing values outside a customer tolerance."),
            ("Weight recent values without erasing history", "At time t, the statistic is lambda times the new reading plus one minus lambda times the previous EWMA. Lambda must be above zero and no greater than one. A smaller value smooths more and can highlight a sustained small shift, but it also delays a sudden jump and creates dependence between plotted points. Show raw readings or a linked table beside the smooth trace; smoothing alone can hide an isolated dangerous measurement. [[data-visualization/large-series-level-of-detail-and-extrema|Preserving extrema]] matters even when the monitoring statistic does not alert. Compare each EWMA point with limits designed for that same time index. Startup limits widen toward steady-state limits when the statistic begins at the fixed target; using the asymptotic limit immediately changes early false-alarm behavior."),
            ("Keep time steps honest", "A recurrence is defined over ordered observations, not an arbitrary display order. If two shifts are missing, do not quietly join the previous EWMA to the next reading as though no time passed. Decide whether the index counts samples or calendar periods, document any reset after maintenance, and mark instrument downtime. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Time-series gaps]] need a visible policy. The code below treats every input reading as the next consecutive sample and rejects nonfinite values; it does not infer time gaps. If the monitoring interval or subgroup size changes, a single baseline spread may no longer apply. Freeze lambda, target, spread and limit multiplier before evaluating a future run, then version them whenever they change."),
            ("Investigate signals without chasing noise", "An EWMA point beyond its control limit is a signal to investigate the process and measurement system, not proof of a particular cause. Repeated searching and changing limits after seeing a signal inflates false discoveries. Estimate false-alarm behavior and detection delay under a realistic process model before choosing lambda and limit width; independence and stable variance assumptions matter. [[data-visualization/cusum-charts-reference-shifts-reset-and-alert-calibration|CUSUM charts]] offer a related running-evidence design with a reference shift and reset rule. A published chart should include target, lambda, multiplier, baseline window, each raw reading, the EWMA value, both time-specific limits and the investigation outcome. [[data-visualization/chart-export-manifest-data-and-render-version|The export manifest]] protects that state when charts are shared outside the monitoring system."),
        ],
        "code": '''from math import isfinite, sqrt

def ewma_trace(readings: list[tuple[str, float]], target: float,
               sigma: float, weight: float = 0.25, multiplier: float = 3.0):
    if not isfinite(target) or not isfinite(sigma) or sigma <= 0:
        raise ValueError("target and positive baseline spread are required")
    if not isfinite(weight) or not 0 < weight <= 1:
        raise ValueError("weight must be in (0, 1]")
    if not isfinite(multiplier) or multiplier <= 0:
        raise ValueError("limit multiplier must be positive")
    if len({sample_id for sample_id, _ in readings}) != len(readings) or any(
            not sample_id or not isfinite(value) for sample_id, value in readings):
        raise ValueError("sample IDs and readings must be valid")
    current = target
    ledger = []
    for index, (sample_id, value) in enumerate(readings, start=1):
        current = weight * value + (1 - weight) * current
        startup_spread = sigma * sqrt(weight / (2 - weight) *
                                      (1 - (1 - weight) ** (2 * index)))
        lower = target - multiplier * startup_spread
        upper = target + multiplier * startup_spread
        ledger.append((sample_id, value, current, lower, upper,
                       current < lower or current > upper))
    return ledger

probe_readings = [("shift-47", 52.0), ("shift-59", 53.0),
                  ("shift-83", 54.0), ("shift-97", 56.0)]
trace = ewma_trace(probe_readings, target=50.0, sigma=2.0)
assert trace[0][2:5] == (50.5, 48.5, 51.5)
assert abs(trace[2][2] - 51.84375) < 1e-12
assert [row[-1] for row in trace] == [False, False, False, True]''',
        "cost": "For N ordered readings, the recurrence and time-specific limits take O(N) time and O(N) output space; streaming only the latest statistic and signal uses O(1) extra space. The four-reading check proves the startup-width calculation and a later alert under its chosen reference values. Those values are illustrative, not calibrated for a target false-alarm rate. The function assumes equally spaced independent baseline observations and does not solve missing periods, serial correlation or a drifting reference process.",
        "mistakes": ["Treating control limits as customer specification limits.", "Estimating the baseline from the same visibly drifting period being monitored.", "Changing lambda or limits after viewing alerts without versioning the rule.", "Hiding raw spikes or missing periods beneath a smooth EWMA line."],
        "drill": "Monitor 47 consecutive production shifts. Freeze a clean baseline first, compare startup with steady-state limits, flag gaps and resets, and explain each alert with the raw reading and investigation record.",
        "related": [prefix + "cusum-charts-reference-shifts-reset-and-alert-calibration", prefix + "p-charts-varying-denominators-and-process-baselines", prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "chart-export-manifest-data-and-render-version"],
    },
]

publish(
    lessons,
    sort_start=8765,
    module_groups=[("Classification decisions and errors", [0, 1]),
                   ("Monitoring slow process shifts", [2])],
    incoming={
        "precision-recall-curves-threshold-ties-prevalence-and-average-precision": [0, 1],
        "probability-calibration-plots-bin-counts-prevalence-and-drift": [0],
        "uncertainty-and-small-sample-display": [0],
        "heatmap-missing-cells-and-color-domain": [1],
        "aggregation-grain-and-denominator": [1],
        "linked-filters-cohort-denominators-and-selection-state": [1],
        "cusum-charts-reference-shifts-reset-and-alert-calibration": [2],
        "p-charts-varying-denominators-and-process-baselines": [2],
        "time-series-gaps-calendars-and-provisional-periods": [2],
    },
    packet_name="aitrove-data-visualization-import-20261008-l.json",
)
