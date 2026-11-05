"""Add original distribution-over-time, count-monitoring and seasonal lessons."""
from data_visualization_batch import publish

prefix = "data-visualization/"
lessons = [
    {
        "slug": "historical-percentile-ribbons-period-support-and-interval-meaning",
        "title": "Historical percentile ribbons: show the spread of observations over time",
        "summary": "Build a median and percentile band from completed periods while keeping record counts, eligibility and interval meaning visible.",
        "sections": [
            ("Define what each vertical slice contains", "A historical percentile ribbon connects selected quantiles of observations at each completed time period. Its center might be the median; the shaded area might span the 25th to 75th percentiles. That band describes the spread of observed units within a period. It is not a confidence interval for the median and not a prediction interval for next week. Name the observation unit and eligibility rule. Daily response times across requests tell a different story from daily medians across customers, because a heavy user receives more weight in the first view. A change in which units qualify can move every quantile without any change in the behavior of continuing units. [[data-visualization/aggregation-grain-and-denominator|Grain and denominator]] and [[data-visualization/linked-filters-cohort-denominators-and-selection-state|cohort filters]] should be settled before computing a ribbon."),
            ("Freeze the quantile rule and period watermark", "Quantile software has several interpolation conventions. This lesson uses linear interpolation between adjacent sorted observations at position p times N minus one, where p is the fraction from zero to one. State that convention when numerical values are compared across tools. Keep the same percentile levels, units and scale through the chart. The latest partial period often looks artificially narrow because late observations have not arrived; stop at a declared last-complete-period watermark or clearly mark the partial region. A missing period should break the ribbon, not be joined by an unexplained bridge. The code rejects duplicate unit-period pairs and omits records after the watermark, but real event pipelines also need an ingestion-completeness check. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Period completeness]] and [[data-visualization/chart-export-manifest-data-and-render-version|export metadata]] make that rule reproducible."),
            ("Keep sample support beside the envelope", "A wide ribbon can reflect genuine diversity, a changed unit mix, an outlier or fewer observations. Show the count at each period, and use a threshold or a distinct mark when support becomes too thin for the selected quantiles. The 25th and 75th percentiles enclose the central half of the observed values under the chosen sample convention; they do not promise that half of a future population will land there. For small N, interpolation creates numbers that may never have been measured. That is acceptable when disclosed, but do not present extra decimal places as physical precision. If paired entities recur across periods, a ribbon of marginal distributions does not show individual trajectories. Use a separate paired view when the question is who improved. [[data-visualization/paired-change-slope-and-dumbbell-charts|Paired-change charts]] and [[data-visualization/uncertainty-and-small-sample-display|small-sample displays]] address those cases."),
            ("Use the ribbon where a line would hide the population", "A single median line may remain flat while the upper tail grows sharply; the shaded interval makes that difference visible. Conversely, a rising median with a stable width can indicate a broad shift rather than merely more extreme cases. Do not stack opaque bands until they conceal each other. If several groups must be compared, use shared-scale panels or thin boundaries with explicit labels, then include an accessible table of median, endpoints and counts. A plotted outer range can be useful, but it may be dominated by a handful of measurement errors; reconcile impossible values before charting. [[data-visualization/small-multiples-shared-scales-and-facet-order|Small multiples]] and [[data-visualization/accessible-color-and-text-alternatives|text alternatives]] preserve the comparison. [[data-visualization/forecast-fan-charts-prediction-intervals-and-horizon|Forecast fan charts]] are a different claim about unseen future outcomes."),
        ],
        "code": '''from collections import defaultdict
from math import floor, isfinite

def interpolated_quantile(sorted_values: list[float], fraction: float) -> float:
    position = fraction * (len(sorted_values) - 1)
    lower = floor(position)
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[min(lower + 1, len(sorted_values) - 1)] * weight

def latency_ribbon(records: list[tuple[int, str, float]],
                   last_complete_period: int):
    if not isinstance(last_complete_period, int):
        raise ValueError("watermark must be a complete integer period")
    grouped = defaultdict(list)
    seen = set()
    excluded = 0
    for period, request_id, latency_ms in records:
        if (not isinstance(period, int) or not request_id or
                not isfinite(latency_ms) or latency_ms < 0 or
                (period, request_id) in seen):
            raise ValueError("records need unique unit-period IDs and finite latency")
        seen.add((period, request_id))
        if period > last_complete_period:
            excluded += 1
            continue
        grouped[period].append(latency_ms)
    if not grouped:
        raise ValueError("no completed observations")
    rows = []
    for period in sorted(grouped):
        values = sorted(grouped[period])
        rows.append((period, len(values),
                     interpolated_quantile(values, 0.25),
                     interpolated_quantile(values, 0.50),
                     interpolated_quantile(values, 0.75)))
    return rows, excluded

samples = [(47, "request-47", 47), (47, "request-59", 59),
           (47, "request-83", 83), (47, "request-97", 97),
           (48, "request-131", 59), (48, "request-149", 83),
           (48, "request-173", 97), (48, "request-211", 131),
           (49, "request-227", 47)]
period_rows, provisional_count = latency_ribbon(samples, 48)
assert period_rows == [(47, 4, 56.0, 71.0, 86.5),
                       (48, 4, 77.0, 90.0, 105.5)]
assert provisional_count == 1''',
        "cost": "For N records split across P completed periods, validation and grouping take O(N) expected time; sorting within groups costs O(sum nₚ log nₚ), bounded by O(N log N), and sorting period keys costs O(P log P). The ledger, grouped values and duplicate-key set use O(N + P) space. The worked sample yields a first-period central band from 56 to 86.5 milliseconds, median 71 and support four; the later incomplete record is counted as excluded. Four observations are an arithmetic check, not enough support for a stable production ribbon. Publish a minimum-count policy before interpreting thin periods.",
        "mistakes": ["Labeling a within-period percentile band as uncertainty in the median.", "Joining the last completed period to an incomplete current period without a provisional mark.", "Comparing quantiles after changing unit eligibility or interpolation convention.", "Hiding period counts and inferring individual movement from marginal distributions."],
        "drill": "Build a weekly latency ribbon from 83 completed weeks of synthetic requests. Reconcile eligible request IDs, display sample count and the 25th, 50th and 75th percentiles for each week, and show which week is excluded by the watermark.",
        "related": [prefix + "uncertainty-and-small-sample-display", prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "paired-change-slope-and-dumbbell-charts", prefix + "forecast-fan-charts-prediction-intervals-and-horizon"],
    },
    {
        "slug": "u-charts-defects-per-unit-varying-exposure-and-frozen-limits",
        "title": "U charts: monitor defect counts when inspection exposure changes",
        "summary": "Normalize nonconformity counts by inspected units and compute exposure-specific limits from a frozen baseline.",
        "sections": [
            ("Count defects, not defective units", "A U chart monitors the rate of counted nonconformities per inspection unit when the number of inspected units changes by period. One unit can carry more than one defect. If the question instead asks whether each unit is defective at least once, count units with any defect and consider a proportion chart; the numerator cannot exceed the denominator there. Define an inspection unit consistently: one shipment, one component or one fixed area. A day with more inspected shipments naturally has more total findings even at an unchanged defect rate, which is why a raw-count line misleads. Record defect definitions, inspection coverage, sampling plan and the exposure denominator alongside each point. [[data-visualization/p-charts-varying-denominators-and-process-baselines|P charts]] treat a binary outcome per unit, while [[data-visualization/aggregation-grain-and-denominator|grain and denominator]] rules secure the rate."),
            ("Pool the baseline by exposure", "Estimate the reference rate as total baseline defects divided by total baseline inspected units. Do not average the individual period rates without weights; a shift inspecting 47 units should not count as much as one inspecting 131 units. Under the illustrative Poisson-count model, each period's rate has an upper limit of center plus three times the square root of center divided by that period's exposure. The lower limit is the same subtraction clipped to zero. Limits widen with smaller exposure, so drawing a single horizontal upper line across changing sample sizes gives the wrong alert rule. Freeze baseline periods and limits before monitoring; the later signal should not teach the baseline to accept itself. [[data-visualization/individuals-moving-range-charts-baseline-gaps-and-two-point-variation|Individuals charts]] monitor a different continuous-measure situation, and [[data-visualization/chart-export-manifest-data-and-render-version|export metadata]] should retain the baseline revision."),
            ("Check the count model before operational alarms", "The simple limits assume approximately independent defects at a stable rate with Poisson-like variation after exposure normalization. Clusters, batches, changing severity mix, repeated inspection of the same unit or overdispersion can make the nominal limits too narrow. Very low expected counts also make symmetric three-standard-deviation approximations rough; a calibrated count method may be preferable. Inspect residual patterns, baseline stability and known process changes before deploying alerts. A point beyond a limit is an investigation signal, not proof that its batch fails a customer specification. A rate can fall below the lower limit because inspection has changed or a real improvement has occurred; do not automatically suppress lower-side signals. [[data-visualization/cusum-charts-reference-shifts-reset-and-alert-calibration|CUSUM]] and [[data-visualization/ewma-control-charts-startup-limits-baseline-and-slow-drift|EWMA]] can be considered for sustained small shifts after their assumptions are checked."),
            ("Make every alert traceable", "The chart should expose period ID, defects counted, units inspected, observed defects per unit, center, lower and upper limit and the exact rule used. Include an annotation when inspection policy or defect taxonomy changes. One unusually high day should prompt a check of source counts and exposure before a process explanation. Compare groups only if the inspection unit and coverage are compatible; a warehouse with twice the inspection depth can appear worse because it detects more issues, not because it generates more. Use a table and explicit alert label so a reader need not rely on color. [[data-visualization/accessible-color-and-text-alternatives|Accessible text]] and [[data-visualization/time-series-gaps-calendars-and-provisional-periods|gap handling]] help keep the chart auditable."),
        ],
        "code": '''from math import isfinite, sqrt

def defect_rate_ledger(baseline: list[tuple[str, int, int]],
                       monitoring: list[tuple[str, int, int]]):
    if len(baseline) < 5:
        raise ValueError("baseline needs at least five periods for this demonstration")
    seen = set()
    for period_id, defects, inspected_units in baseline + monitoring:
        if (not period_id or period_id in seen or
                not isinstance(defects, int) or defects < 0 or
                not isinstance(inspected_units, int) or inspected_units <= 0):
            raise ValueError("period IDs, counts and exposure must be valid")
        seen.add(period_id)
    center = sum(row[1] for row in baseline) / sum(row[2] for row in baseline)
    if not isfinite(center) or center <= 0:
        raise ValueError("a positive baseline defect rate is required")
    plotted = []
    for period_id, defects, inspected_units in monitoring:
        observed = defects / inspected_units
        spread = 3 * sqrt(center / inspected_units)
        lower, upper = max(0.0, center - spread), center + spread
        plotted.append((period_id, defects, inspected_units,
                        observed, lower, upper,
                        observed < lower or observed > upper))
    return center, plotted

reference = [("shift-47", 2, 47), ("shift-59", 3, 59),
             ("shift-83", 1, 83), ("shift-97", 4, 97),
             ("shift-131", 2, 131)]
new_shifts = [("shift-149", 8, 47), ("shift-173", 3, 131)]
center, points = defect_rate_ledger(reference, new_shifts)
assert abs(center - 12 / 417) < 1e-12
assert points[0][-1] is True and points[1][-1] is False
assert points[0][5] > points[1][5]
assert points[0][4] == points[1][4] == 0.0''',
        "cost": "With B baseline periods and M monitoring periods, validation, pooled-rate calculation and alert generation take O(B + M) time. The identifier set uses O(B + M) space and the returned plot ledger O(M); a trusted unique-ID stream could reduce additional state. The sample pools 12 findings over 417 inspected units, then flags eight findings among 47 units while three among 131 units remains within its narrower exposure-specific limits. Five baseline periods are an arithmetic demonstration, not a reliable operating baseline. Validate enough stable history and the Poisson dispersion assumption before turning a flag into an alert.",
        "mistakes": ["Counting nonconforming units as defects when one unit can have several findings.", "Averaging daily defect rates without weighting by inspected units.", "Using one fixed upper limit while exposure changes substantially.", "Interpreting a statistical signal as proof of product failure or a named cause."],
        "drill": "Freeze 47 stable inspection shifts and monitor 83 later shifts with changing unit counts. Reconcile every defect and exposure value, plot each point's own limits, and log investigations for signals after checking for clustered findings.",
        "related": [prefix + "p-charts-varying-denominators-and-process-baselines", prefix + "individuals-moving-range-charts-baseline-gaps-and-two-point-variation", prefix + "cusum-charts-reference-shifts-reset-and-alert-calibration", prefix + "ewma-control-charts-startup-limits-baseline-and-slow-drift"],
    },
    {
        "slug": "seasonal-subseries-plots-cycle-position-trend-and-incomplete-years",
        "title": "Seasonal subseries plots: compare the same cycle position across years",
        "summary": "Group repeated cycle positions, draw their chronological traces and calculate reference means only from complete cycles.",
        "sections": [
            ("Choose a cycle for a real operational reason", "A seasonal subseries plot groups observations by their position within a known repeating cycle: all first quarters together, all second quarters together and so on. Within each group, preserve chronological order across cycles and draw a reference mean or median for that position. The view exposes both differences between cycle positions and changes within one position over years. A quarterly series needs four positions; a weekly schedule might need seven weekdays. Do not infer the cycle merely because a pattern looks attractive after trying many candidates. Document the calendar origin and whether a period is a full business day, fiscal week or standard month. [[data-visualization/autocorrelation-plots-regular-lags-pair-counts-and-seasonality|Autocorrelation plots]] can suggest repetition, but their lag peaks do not supply the business calendar. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Time-series calendar rules]] fix the period definitions."),
            ("Align like positions and keep the trend visible", "A quarter-one rise across years can coexist with quarter three being the seasonal high. If the group means are calculated over the entire time span, a rising long-term trend can make later years look elevated at every position and exaggerate a seasonal story. Inspect the original chronological series and, when justified, a separately labeled detrended view. Do not quietly subtract a trend and publish the adjusted trace as raw volume. The seasonal subseries plot is descriptive; a repeated peak does not establish that the calendar position causes it. Keep all panels on one vertical scale so a small within-quarter change is not magnified by a custom axis. [[data-visualization/small-multiples-shared-scales-and-facet-order|Shared-scale panels]] and [[data-visualization/chart-annotations-event-windows-and-causal-claims|event annotations]] make context visible without overclaiming."),
            ("Do not let an unfinished cycle define the reference", "A current year with only two complete quarters can contribute those two observed points, but it must not be treated as a four-quarter baseline. Mark its unobserved quarters as missing, not zero, and freeze the complete historical cycles used for the reference means. A backfilled quarter can change the baseline; version that change. The code below requires each reference cycle to contain every position once and permits a later incomplete cycle for display only. Real calendar data also need an explicit policy for holidays, leap days, 53-week years and corrected reports. Counts behind averages belong in the accompanying table. [[data-visualization/calendar-heatmap-complete-days-time-zones-and-missingness|Calendar completeness]] and [[data-visualization/heatmap-missing-cells-and-color-domain|missing-cell encoding]] apply when the same data is shown as a matrix."),
            ("Make the grouped view answer a concrete question", "For capacity planning, ask whether the same quarter reliably peaks, whether peak magnitude is changing and whether the latest complete point is unusual relative to its own season. A grouped trace can reveal that a conventional time-series line obscures those comparisons. Yet two historical cycles are weak evidence of recurrence; unusual one-off events can dominate a group mean. Show the exact number of complete cycles, use a median reference when outliers are common and inspect sensitivity to leaving out a cycle. Do not project the group mean forward as a forecast without an evaluated model and uncertainty. [[data-visualization/forecast-fan-charts-prediction-intervals-and-horizon|Forecast fan charts]] have that different purpose. Provide labels and a reference table for readers who cannot distinguish traces by color alone; [[data-visualization/accessible-color-and-text-alternatives|accessible chart guidance]] covers the contract."),
        ],
        "code": '''from collections import defaultdict
from math import isfinite

def seasonal_subseries(readings: list[tuple[int, int, float]],
                       positions: int, last_reference_cycle: int):
    if positions < 2 or not isinstance(last_reference_cycle, int):
        raise ValueError("declare cycle length and reference cutoff")
    by_position = defaultdict(list)
    seen = set()
    reference_cycles = set()
    for cycle, position, volume in readings:
        if (not isinstance(cycle, int) or not isinstance(position, int) or
                not 1 <= position <= positions or not isfinite(volume) or
                (cycle, position) in seen):
            raise ValueError("cycle positions must be unique, valid and finite")
        seen.add((cycle, position))
        by_position[position].append((cycle, volume))
        if cycle <= last_reference_cycle:
            reference_cycles.add(cycle)
    if not reference_cycles or any(
            (cycle, position) not in seen
            for cycle in reference_cycles for position in range(1, positions + 1)):
        raise ValueError("every reference cycle must be complete")
    result = []
    for position in range(1, positions + 1):
        trace = sorted(by_position[position])
        reference = [volume for cycle, volume in trace
                     if cycle in reference_cycles]
        result.append((position, len(reference), sum(reference) / len(reference), trace))
    return result

quarterly_orders = [(47, 1, 47), (47, 2, 59), (47, 3, 83), (47, 4, 71),
                    (48, 1, 59), (48, 2, 71), (48, 3, 97), (48, 4, 83),
                    (49, 1, 61), (49, 2, 73)]
panels = seasonal_subseries(quarterly_orders, positions=4,
                            last_reference_cycle=48)
assert panels[0] == (1, 2, 53.0, [(47, 47), (48, 59), (49, 61)])
assert panels[2] == (3, 2, 90.0, [(47, 83), (48, 97)])
assert panels[3][3] == [(47, 71), (48, 83)]''',
        "cost": "For N readings, validation and grouping take O(N) expected time; sorting each position's trace costs O(sum nₛ log nₛ), bounded by O(N log N). Checking reference completeness takes O(C·S) for C reference cycles and S positions. Stored traces and the duplicate-key set need O(N) space. The toy quarterly ledger uses two complete reference years, giving a first-quarter mean of 53 orders and a third-quarter mean of 90. The partial third year appears only where observed, and never changes the frozen reference. Two cycles verify code behavior but cannot establish dependable seasonality.",
        "mistakes": ["Starting the four-position cycle at the wrong fiscal quarter.", "Treating an unobserved current-quarter cell as a measured zero.", "Mixing a trend-adjusted trace with raw-volume reference means without labeling the change.", "Calling a cycle-position mean a validated forecast or causal explanation."],
        "drill": "Take 47 completed fiscal years with four quarters each and one partial current year. Audit duplicate and missing quarter keys, show chronological traces for each quarter, calculate references only from complete years, and compare the grouped view with the ungrouped time series.",
        "related": [prefix + "autocorrelation-plots-regular-lags-pair-counts-and-seasonality", prefix + "small-multiples-shared-scales-and-facet-order", prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "forecast-fan-charts-prediction-intervals-and-horizon"],
    },
]

publish(
    lessons,
    sort_start=8777,
    module_groups=[("Observed spread and defect-rate monitoring", [0, 1]),
                   ("Seasonal pattern diagnostics", [2])],
    incoming={
        "uncertainty-and-small-sample-display": [0],
        "paired-change-slope-and-dumbbell-charts": [0],
        "forecast-fan-charts-prediction-intervals-and-horizon": [0, 2],
        "p-charts-varying-denominators-and-process-baselines": [1],
        "individuals-moving-range-charts-baseline-gaps-and-two-point-variation": [1],
        "cusum-charts-reference-shifts-reset-and-alert-calibration": [1],
        "autocorrelation-plots-regular-lags-pair-counts-and-seasonality": [2],
        "small-multiples-shared-scales-and-facet-order": [2],
        "time-series-gaps-calendars-and-provisional-periods": [0, 2],
    },
    packet_name="aitrove-data-visualization-import-20261008-p.json",
)
