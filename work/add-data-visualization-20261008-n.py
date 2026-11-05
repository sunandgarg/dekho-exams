"""Add original inequality, process monitoring and sensitivity-chart lessons."""
from data_visualization_batch import publish

prefix = "data-visualization/"
lessons = [
    {
        "slug": "lorenz-curves-ranked-shares-zero-values-and-gini-area",
        "title": "Lorenz curves: audit ranked shares before quoting a Gini value",
        "summary": "Construct cumulative population and amount shares with an equality reference, a declared observation unit and an explicit zero-value policy.",
        "sections": [
            ("Fix the population and the quantity", "A Lorenz curve ranks units from the smallest nonnegative amount to the largest, then plots cumulative population share against cumulative amount share. The unit might be a household, customer, shipment or location; the amount might be income, support hours or energy consumption. State both. A curve over customers cannot be compared directly with one over invoices when some customers generate many invoices. Start at zero, zero and finish at one, one. The diagonal is an equal-share reference, not a fitted trend. [[data-visualization/aggregation-grain-and-denominator|Grain and denominator]] decisions determine the curve before a single point is drawn. Print the total amount, number of units, observation window and eligibility exclusions beside the chart."),
            ("Keep zero values and define negative values", "A unit with zero amount still occupies population share. It produces a horizontal segment at the bottom of the curve, often an important feature rather than noise to filter out. Negative amounts break the ordinary nonnegative Lorenz interpretation: debt, net profit and refunds need a separately defined policy, not an unannounced absolute value or shift. Missing amounts are different again. Disclose their count and decide whether the published population excludes them, estimates them, or uses a sensitivity range. If the source is a survey with weights, each unit's horizontal step is its normalized sampling weight; an unweighted curve like the code below must not be labeled as a population-weighted estimate. [[data-visualization/empirical-cdf-percentiles-and-tail-reading|An empirical CDF]] ranks values too, but its vertical axis counts units rather than their cumulative share of an amount."),
            ("Calculate area on the points actually shown", "For nonnegative individual amounts with equal unit weight, the Gini value is one minus twice the area under the piecewise-linear Lorenz curve. Calculate that area from every sorted unit boundary, not from a handful of plotted labels or a smoothed curve. A summary rounded to two decimals can hide a change that matters to policy, so show the underlying curve and selected checkpoints such as the bottom half's amount share. A Gini value near zero means the measured amount is distributed more evenly across the included units. It says nothing by itself about whether total resources are adequate. [[data-visualization/uncertainty-and-small-sample-display|Uncertainty and support]] deserve attention when comparing small places or sampled populations."),
            ("Compare periods without swapping the denominator", "Two curves can cross; then one scalar Gini cannot describe which segment has a larger share at every population depth. Put both periods on identical zero-to-one axes, retain the same unit definition and describe major population or data-collection changes. A rising total can coexist with a more bowed curve, and a falling total with a straighter one. Show totals as a separate companion view rather than asking normalized curves to reveal volume. If a few units dominate the tail, provide a table of their share without exposing private identities. [[data-visualization/small-multiples-shared-scales-and-facet-order|Shared-scale panels]] and [[data-visualization/accessible-color-and-text-alternatives|text alternatives]] keep the comparison readable without relying on line color alone."),
        ],
        "code": '''from math import isfinite

def lorenz_ledger(amounts: list[tuple[str, float]]):
    unit_ids = [unit_id for unit_id, _ in amounts]
    if not amounts or len(unit_ids) != len(set(unit_ids)) or any(
            not unit_id for unit_id in unit_ids):
        raise ValueError("units need unique, nonempty IDs")
    if any(not isfinite(amount) or amount < 0 for _, amount in amounts):
        raise ValueError("ordinary Lorenz amounts must be finite and nonnegative")
    total = sum(amount for _, amount in amounts)
    if total <= 0:
        raise ValueError("positive total amount is required")
    ranked = sorted(amounts, key=lambda record: record[1])
    points = [(0.0, 0.0)]
    cumulative = 0.0
    for position, (_, amount) in enumerate(ranked, start=1):
        cumulative += amount
        points.append((position / len(ranked), cumulative / total))
    doubled_area = sum((points[index][0] - points[index - 1][0]) *
                       (points[index][1] + points[index - 1][1])
                       for index in range(1, len(points)))
    return points, 1 - doubled_area

district_amounts = [("district-47", 47.0), ("district-59", 59.0),
                    ("district-83", 83.0), ("district-211", 211.0)]
curve, gini = lorenz_ledger(district_amounts)
assert curve[2] == (0.5, 106 / 400)
assert curve[-1] == (1.0, 1.0)
assert abs(gini - 0.3225) < 1e-12
assert lorenz_ledger([("empty-47", 0.0), ("full-59", 47.0)])[0][1] == (0.5, 0.0)''',
        "cost": "For N units, sorting takes O(N log N) time and the cumulative sweep plus trapezoidal area take O(N). The ranked records, uniqueness set and point list need O(N) space. The four-district check yields bottom-half share 0.265 and Gini 0.3225; a separate zero-amount check proves that zero units remain in the population. This code is deliberately unweighted and rejects negative amounts. Survey weights or negative wealth require a different declared calculation and interpretation.",
        "mistakes": ["Ranking invoices while describing the horizontal axis as households.", "Removing zero-amount units because they make a flat segment.", "Calculating Gini from smoothed drawing coordinates instead of the ranked data.", "Comparing two normalized curves without reporting totals and population coverage."],
        "drill": "Build two yearly curves for 470 synthetic service districts. Reconcile every amount to the published total, include zero-use districts, show bottom-half and top-decile shares, and explain any missing or negative records before comparing Gini values.",
        "related": [prefix + "aggregation-grain-and-denominator", prefix + "empirical-cdf-percentiles-and-tail-reading", prefix + "small-multiples-shared-scales-and-facet-order", prefix + "uncertainty-and-small-sample-display"],
    },
    {
        "slug": "individuals-moving-range-charts-baseline-gaps-and-two-point-variation",
        "title": "Individuals and moving-range charts: monitor level and local variation",
        "summary": "Pair single-observation measurements with successive absolute differences while freezing baseline center and limits before monitoring begins.",
        "sections": [
            ("Use the pair when each period has one reading", "An individuals chart plots one measurement per ordered sampling point. A companion moving-range chart plots the absolute difference between consecutive readings, so it can reveal a jump that deserves attention even when the level remains inside its own limits. The pair is useful when rational subgroups of repeated measurements are unavailable. Do not substitute it for a subgroup chart when several readings are deliberately sampled within each period; averaging or selecting one would discard within-period variation. [[data-visualization/p-charts-varying-denominators-and-process-baselines|A p chart]] instead monitors proportions with varying denominators. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Time-series gap rules]] apply before any adjacent difference is calculated."),
            ("Freeze a credible baseline", "Estimate a center from an earlier stable phase. For moving ranges of two successive baseline observations, divide their mean by the appropriate two-point constant to estimate short-term standard deviation; three such estimated standard deviations on either side of the center give illustrative individuals limits. The moving-range chart has its own upper limit and a zero lower bound under this standard pairing. Record the baseline IDs, sampling interval, calibration version and exclusions. Do not recompute limits after every surprising new point, because an actual shift would then move the reference line along with it. [[data-visualization/cusum-charts-reference-shifts-reset-and-alert-calibration|CUSUM]] and [[data-visualization/ewma-control-charts-startup-limits-baseline-and-slow-drift|EWMA]] can complement this pair when small persistent shifts matter more than isolated jumps."),
            ("Do not bridge missing or changed periods", "A moving range is meaningful only between adjacent observations of the process under the chosen sampling plan. If one shift is missing, comparing the readings on either side spans a longer interval and should not silently become an ordinary two-point range. Start a new run after a known process reset or measurement-system change, and mark the gap on the chart. Serial correlation can make the textbook limits misleading: slowly drifting readings have small successive differences even when the process is no longer stable. Inspect raw points and time spacing, and validate false-alert behavior on a clean baseline before operational use. Control limits describe process behavior under assumptions; they are not product acceptance specifications."),
            ("Make alerts inspectable", "Show the measurement, moving range, reference center, both limit sets and which rule triggered. A point outside a limit is a signal to investigate, not proof of a faulty product or a named root cause. Record investigation outcome and subsequent measurement rather than redrawing away a signal. For small baselines, estimates can be unstable; the six-point demonstration below is an arithmetic check, not a recommended operational baseline size. [[data-visualization/chart-export-manifest-data-and-render-version|A chart export manifest]] should carry the baseline version and missing-period policy so another reader can reproduce the same alarms. Use [[data-visualization/accessible-color-and-text-alternatives|text flags]] as well as colored markers."),
        ],
        "code": '''from math import isfinite

def individual_range_ledger(baseline: list[tuple[str, float]],
                            monitoring: list[tuple[str, float]]):
    all_readings = baseline + monitoring
    identifiers = [sample_id for sample_id, _ in all_readings]
    if len(baseline) < 5 or len(identifiers) != len(set(identifiers)) or any(
            not sample_id or not isfinite(value)
            for sample_id, value in all_readings):
        raise ValueError("use valid unique samples and at least five baseline readings")
    baseline_values = [value for _, value in baseline]
    ranges = [abs(current - previous)
              for previous, current in zip(baseline_values, baseline_values[1:])]
    center = sum(baseline_values) / len(baseline_values)
    mean_range = sum(ranges) / len(ranges)
    if mean_range == 0:
        raise ValueError("zero baseline variation needs an investigation")
    sigma_estimate = mean_range / 1.128
    individual_limits = (center - 3 * sigma_estimate,
                         center + 3 * sigma_estimate)
    range_limits = (0.0, 3.267 * mean_range)
    last_value = baseline_values[-1]
    plotted = []
    for sample_id, value in monitoring:
        moving_range = abs(value - last_value)
        plotted.append((sample_id, value, moving_range,
                        value < individual_limits[0] or value > individual_limits[1],
                        moving_range > range_limits[1]))
        last_value = value
    return center, mean_range, individual_limits, range_limits, plotted

reference_shifts = [("shift-47", 47.0), ("shift-59", 49.0),
                    ("shift-83", 48.0), ("shift-97", 50.0),
                    ("shift-101", 49.0), ("shift-131", 51.0)]
new_shifts = [("shift-149", 52.0), ("shift-173", 54.0)]
center, average_range, bounds, range_bounds, marks = individual_range_ledger(
    reference_shifts, new_shifts)
assert center == 49.0 and average_range == 1.6
assert bounds[0] < 47 < bounds[1] < 54
assert marks == [("shift-149", 52.0, 1.0, False, False),
                 ("shift-173", 54.0, 2.0, True, False)]''',
        "cost": "With B baseline readings and M monitored readings, calculating center, successive baseline ranges and alerts takes O(B + M) time. The returned monitor ledger uses O(M) space, while ID validation uses O(B + M); streaming from a prevalidated unique-ID source needs only constant additional state. The eight-reading check detects a level signal at 54 while both observed moving ranges remain below their own limit. Its baseline is intentionally too small for a reliable operating rule. Validate a longer stable phase and the sampling schedule before treating limits as alarms.",
        "mistakes": ["Including new alarm points in the baseline average and moving limits.", "Treating a missing shift as though its two neighbors were adjacent samples.", "Calling a control limit a product specification or a guaranteed false-alarm probability.", "Ignoring serial correlation because the moving ranges happen to be small."],
        "drill": "Use 47 verified stable production shifts as a frozen baseline, then monitor 83 later shifts. Mark gaps and equipment resets, display both charts with versioned limits, and explain every alert with its raw reading, adjacent reading and investigation state.",
        "related": [prefix + "ewma-control-charts-startup-limits-baseline-and-slow-drift", prefix + "cusum-charts-reference-shifts-reset-and-alert-calibration", prefix + "p-charts-varying-denominators-and-process-baselines", prefix + "time-series-gaps-calendars-and-provisional-periods"],
    },
    {
        "slug": "tornado-sensitivity-charts-baseline-scenarios-and-asymmetric-effects",
        "title": "Tornado charts: keep scenario ranges attached to their assumptions",
        "summary": "Rank one-factor-at-a-time output changes around a reproducible baseline without mistaking a wide input range for causal importance.",
        "sections": [
            ("Start at a reproducible base case", "A tornado chart compares how a model output changes when each input is moved to a declared low and high scenario while every other input stays at its baseline. Write down the model version, baseline inputs, output unit and evaluation date first. The central line is the base-case output, not automatically zero. A bar may extend mainly to one side if the output response is asymmetric. Keep the low-input and high-input labels with their actual output values; for a cost input, increasing the input may move profit left instead of right. [[data-visualization/diverging-bars-zero-reference-and-signed-difference|Diverging bars]] explain signed changes, but a tornado's reference is an output produced by a specific model state."),
            ("Make ranges comparable before sorting", "The width of a sensitivity bar depends on both the model and the tested range. Comparing an input moved by 47 percent with another moved by 2 percent and calling the wider result 'more important' confuses scenario design with model sensitivity. Use justified low and high bounds such as operational limits or prespecified uncertainty ranges, and print them in a table. Sort bars by a declared measure, such as maximum absolute movement from the base case; retain a stable secondary order for ties. If different input units matter, a percentage change can help explain the scenario but must be defined even when the baseline is zero. [[data-visualization/scale-baseline-and-axis-integrity|Axis integrity]] requires one output scale across all rows."),
            ("Do not present one-factor variation as a forecast", "One-factor-at-a-time bars hold other inputs fixed. They miss interactions: a lower order count and a lower margin together may hurt more than either separate bar suggests. They also ignore correlations and the probability of a scenario. A bar should not be read as a confidence interval or as the expected range of outcomes. Show combined scenarios separately when constraints tie inputs together, and use an uncertainty method suited to the actual model if probability statements are needed. [[data-visualization/forecast-fan-charts-prediction-intervals-and-horizon|Forecast bands]] encode a different claim. [[data-visualization/asymmetric-error-bars-interval-type-and-axis-clipping|Interval labels]] help prevent scenario ranges from masquerading as statistical error bars."),
            ("Audit the model calls behind the picture", "Evaluate the base case once and each low and high scenario with all other inputs unchanged. Store every exact input vector and output before sorting for display; otherwise a later reader cannot reproduce why a bar moved. Validate that the baseline lies within each scenario's declared range, and reject nonfinite model results. Include the actual input units and whether a low scenario means 'better' or simply a smaller number. For crowded dashboards, show the largest few bars with a link or table containing the rest instead of silently dropping variables. [[data-visualization/chart-export-manifest-data-and-render-version|An export manifest]] can retain input range, model revision and ordering rule. A clear table is also a [[data-visualization/accessible-color-and-text-alternatives|text alternative]] to colored bars."),
        ],
        "code": '''from math import isfinite

def margin_model(inputs: dict[str, float]) -> float:
    return inputs["weekly_orders"] * inputs["unit_margin"] - inputs["fixed_cost"]

def tornado_ledger(baseline: dict[str, float],
                   bounds: dict[str, tuple[float, float]]):
    if set(baseline) != set(bounds) or not baseline or any(
            not isfinite(value) for value in baseline.values()):
        raise ValueError("every finite baseline input needs one scenario range")
    base_output = margin_model(baseline)
    rows = []
    for name, (low, high) in bounds.items():
        if (not isfinite(low) or not isfinite(high) or
                low > baseline[name] or high < baseline[name]):
            raise ValueError("scenario must bracket its baseline input")
        low_case = dict(baseline)
        high_case = dict(baseline)
        low_case[name] = low
        high_case[name] = high
        low_output = margin_model(low_case)
        high_output = margin_model(high_case)
        if not isfinite(low_output) or not isfinite(high_output):
            raise ValueError("model result is not finite")
        impact = max(abs(low_output - base_output),
                     abs(high_output - base_output))
        rows.append((name, low, high, low_output, high_output, impact))
    rows.sort(key=lambda row: (-row[-1], row[0]))
    return base_output, rows

base_inputs = {"weekly_orders": 47.0, "unit_margin": 83.0,
               "fixed_cost": 1700.0}
scenario_bounds = {"weekly_orders": (42.0, 52.0),
                   "unit_margin": (74.0, 92.0),
                   "fixed_cost": (1500.0, 1900.0)}
baseline_output, rows = tornado_ledger(base_inputs, scenario_bounds)
assert baseline_output == 2201.0
assert [row[0] for row in rows] == ["unit_margin", "weekly_orders", "fixed_cost"]
assert rows[0][3:6] == (1778.0, 2624.0, 423.0)
assert rows[-1][3:5] == (2401.0, 2001.0)''',
        "cost": "For P inputs and model-evaluation cost C, the base plus two scenarios per input take O(P·C) model time; copying P-element input maps for each scenario also costs O(P²) in this small standard-library implementation. The row list is O(P) space, with O(P) temporary space per call. The worked weekly margin model returns base output 2,201, correctly orders the three tested ranges and shows that lower fixed cost raises profit. For expensive models, keep the same scenario contract while avoiding unnecessary full-map copies in the evaluation adapter.",
        "mistakes": ["Calling the longest bar the most important variable without comparing the ranges tested.", "Assuming low input always produces the left endpoint of the output bar.", "Reading one-factor-at-a-time scenarios as joint uncertainty or prediction intervals.", "Sorting a published tornado by a new rule without preserving scenario values and model version."],
        "drill": "For a synthetic service operation, freeze 47 weekly orders and a 2,201-unit base margin. Evaluate every low and high scenario independently, add one combined worst-case scenario to expose interactions, and give readers an exact input-output table beside the sorted bars.",
        "related": [prefix + "diverging-bars-zero-reference-and-signed-difference", prefix + "asymmetric-error-bars-interval-type-and-axis-clipping", prefix + "forecast-fan-charts-prediction-intervals-and-horizon", prefix + "chart-export-manifest-data-and-render-version"],
    },
]

publish(
    lessons,
    sort_start=8771,
    module_groups=[("Inequality and ranked shares", [0]),
                   ("Process variation and scenario sensitivity", [1, 2])],
    incoming={
        "aggregation-grain-and-denominator": [0],
        "empirical-cdf-percentiles-and-tail-reading": [0],
        "small-multiples-shared-scales-and-facet-order": [0],
        "ewma-control-charts-startup-limits-baseline-and-slow-drift": [1],
        "cusum-charts-reference-shifts-reset-and-alert-calibration": [1],
        "p-charts-varying-denominators-and-process-baselines": [1],
        "diverging-bars-zero-reference-and-signed-difference": [2],
        "asymmetric-error-bars-interval-type-and-axis-clipping": [2],
        "forecast-fan-charts-prediction-intervals-and-horizon": [2],
        "chart-export-manifest-data-and-render-version": [2],
    },
    packet_name="aitrove-data-visualization-import-20261008-n.json",
)
