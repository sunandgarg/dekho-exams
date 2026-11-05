"""Add original distribution, retention and serial-dependence lessons."""
from data_visualization_batch import publish

prefix = "data-visualization/"
lessons = [
    {
        "slug": "unequal-bin-histograms-density-area-and-boundary-policy",
        "title": "Unequal-bin histograms: make rectangle area carry frequency",
        "summary": "Compute density heights for unequal intervals, document edge inclusion and reconcile plotted area to the measured population.",
        "sections": [
            ("Define the measured population before the bins", "A histogram partitions a numerical measure into adjacent intervals. Each observation belongs to one interval, and the shape depends on the chosen boundaries. Specify the observation unit, measurement unit, eligibility window and treatment of missing values before drawing. A delivery-latency chart over requests differs from one over customers even if both use milliseconds on the horizontal axis. Fixed bin edges let readers compare weeks without interpreting a shifted boundary as a changed distribution. Do not silently trim values outside the visible domain; either expand the domain or label the excluded count and range. [[data-visualization/aggregation-grain-and-denominator|Grain and denominator]] choices come first, and [[data-visualization/distribution-and-outlier-displays|outlier displays]] can preserve extreme values that a compact histogram hides."),
            ("For unequal widths, height is a density", "When widths vary, raw counts cannot be the rectangle heights if the picture is supposed to preserve frequency. Divide each bin's count by its width for count density, or divide again by the total number of included observations for probability density. The rectangle area then equals its count or share. A 40-unit-wide bin containing two requests and an 80-unit-wide bin containing four requests have equal probability-density height, although the second contains twice as many requests. Print counts or shares on demand; height alone is easy to misread. State whether intervals are left-closed and right-open, and make the final upper boundary inclusive if that is the published rule. [[data-visualization/scale-baseline-and-axis-integrity|Axis integrity]] requires a labeled density unit, such as share per millisecond, rather than a mislabeled 'number of requests' vertical axis."),
            ("Choose edges without chasing the answer", "A histogram with very wide bins buries local peaks. Very narrow bins turn sampling noise into apparent structure. Pick boundaries using measurement resolution and a declared analytical purpose, then inspect sensitivity using another reasonable fixed bin plan. Do not search many boundaries and publish only the one that makes a preferred group look unusual. For side-by-side cohorts, use shared edges and a shared vertical density scale; sample-size differences belong in annotations and raw-count tables. If an interval is open-ended, it has no finite width and cannot receive an ordinary density rectangle. Split it at a finite bound, or display its count separately. [[data-visualization/small-multiples-shared-scales-and-facet-order|Shared-scale small multiples]] make the bin plan visible across groups."),
            ("Reconcile the chart before interpretation", "The bin ledger should sum to the included record count. For a probability-density histogram, the sum of height times width should equal one apart from floating-point rounding. Those checks catch dropped boundary observations, double assignment and a denominator that includes records outside the plotted range. The code below rejects out-of-range measurements rather than making an attractive but incomplete chart. A separate report can show excluded or invalid records under a declared policy. Give readers an accessible interval table with bounds, counts, shares and density; a smooth overlay is a different estimate with its own bandwidth and should not erase the measured bins. [[data-visualization/box-violin-and-kde-bandwidth-for-group-comparisons|Density bandwidth]] and [[data-visualization/accessible-color-and-text-alternatives|text alternatives]] cover those follow-on decisions."),
        ],
        "code": '''from bisect import bisect_right
from math import isfinite

def histogram_ledger(latencies_ms: list[float], edges_ms: list[float]):
    if (not latencies_ms or len(edges_ms) < 2 or
            any(not isfinite(edge) for edge in edges_ms) or
            any(left >= right for left, right in zip(edges_ms, edges_ms[1:]))):
        raise ValueError("supply observations and strictly increasing finite edges")
    counts = [0] * (len(edges_ms) - 1)
    for latency in latencies_ms:
        if not isfinite(latency) or latency < edges_ms[0] or latency > edges_ms[-1]:
            raise ValueError("every observation must be finite and inside the domain")
        index = min(bisect_right(edges_ms, latency) - 1, len(counts) - 1)
        counts[index] += 1
    total = len(latencies_ms)
    ledger = [(left, right, count, count / total,
               count / (total * (right - left)))
              for left, right, count in zip(edges_ms, edges_ms[1:], counts)]
    assert sum(row[2] for row in ledger) == total
    assert abs(sum((row[1] - row[0]) * row[4] for row in ledger) - 1) < 1e-12
    return ledger

request_latencies = [47, 59, 83, 97, 131, 149, 173, 211, 227, 251]
bins = histogram_ledger(request_latencies, [40, 80, 160, 320])
assert [row[2] for row in bins] == [2, 4, 4]
assert bins[0][4] == bins[1][4] == 0.005
assert histogram_ledger([40, 80, 160, 320], [40, 80, 160, 320])[-1][2] == 2''',
        "cost": "For N measurements and B bins, binary search assigns each observation in O(log B) time, so the sweep costs O(N log B); constructing the ledger costs O(B). The returned counts and rows need O(B) extra space. The ten-request check gives bin shares 0.2, 0.4 and 0.4, while the first two densities both equal 0.005 share per millisecond. The boundary assertion places 80 in the second interval and includes 320 in the final interval. Preserve this boundary policy when computing comparison charts.",
        "mistakes": ["Using raw counts as rectangle heights when widths differ.", "Labeling a probability-density vertical axis as a count axis.", "Dropping the last-edge observation or assigning an internal edge twice.", "Changing bin boundaries between cohorts and reading the changed geometry as changed behavior."],
        "drill": "Measure 470 request latencies, declare three unequal finite intervals and audit every boundary value. Publish an interval ledger, an excluded-record count, a fixed-edge comparison for a second week and a density-area check that equals one.",
        "related": [prefix + "distribution-and-outlier-displays", prefix + "aggregation-grain-and-denominator", prefix + "box-violin-and-kde-bandwidth-for-group-comparisons", prefix + "small-multiples-shared-scales-and-facet-order"],
    },
    {
        "slug": "cohort-retention-heatmaps-maturity-denominators-and-return-events",
        "title": "Cohort retention heatmaps: keep immature cells blank",
        "summary": "Fix first-entry membership, define the return event and reserve zero for a mature period with no returning members.",
        "sections": [
            ("Anchor each member once", "A cohort retention heatmap groups entities by a first qualifying period, then shows the share that performs a specified return action at each elapsed age. Rows are entry cohorts; columns are ages, not calendar dates. The entity might be a user, account or device, and those IDs are not interchangeable. Deduplicate signup records, resolve identity before grouping and keep each member in the original cohort. If a person returns after an inactive week, they still belong to their first cohort. Choose the return event precisely: opening the app, completing a project and making a payment yield different retention curves. [[data-visualization/aggregation-grain-and-denominator|Grain and denominator]] rules prevent an event count from masquerading as a user count. [[data-visualization/funnel-chart-cohorts-stage-order-and-conversion|Funnels]] answer a related but different progression question."),
            ("Hold the original denominator fixed", "In return-in-period retention, the numerator at age three is the number of original cohort members active in that period; the denominator is the size of that original eligible cohort. Do not divide by last week's active members unless the chart explicitly measures conditional continuation. Several return events by one member in the same period count once. An age-zero cell is one only if it represents enrollment by definition; it is not automatically one when age zero requires a distinct return action. State whether the chart means activity in that exact period, any activity up to that period, or continuous activity in every period. Those definitions can reverse the visual impression. [[data-visualization/linked-filters-cohort-denominators-and-selection-state|Linked filters]] must recalculate cohort membership and denominator together rather than filtering only the numerator."),
            ("Separate zero from not yet observed", "A young cohort has not reached later ages. Its future cells are undefined, not zero percent. A mature cohort with no returning member has a genuine zero. The current partial week is another state: until it closes, all cohorts' cells for that calendar week are provisional, because an apparent decline can simply be missing future activity. Keep a last-complete-period watermark, emit blank cells beyond it and label the watermark on the display. The triangular blank region should use a distinct missing pattern or text, not the low-retention color. Older data can still be incomplete because event ingestion is delayed; an as-of timestamp and an ingestion-lag audit should accompany published comparisons. [[data-visualization/heatmap-missing-cells-and-color-domain|Heatmap missingness]] and [[data-visualization/time-series-gaps-calendars-and-provisional-periods|period completeness]] provide the display contract."),
            ("Compare equal ages and adequate support", "Reading down one age column compares groups at the same lifecycle point; reading diagonally compares the same calendar period across groups of different ages. The latter can reveal a platform outage, but it is not a direct retention comparison. Show cohort sizes because 50 percent may represent one of two members or 5,000 of 10,000. Keep one zero-to-one color range across all rows and do not stretch each row independently. For small cohorts, add counts or uncertainty intervals and avoid strong claims from a bright cell. Segment-specific charts need an eligibility rule frozen at entry; defining a segment using future behavior leaks outcomes into cohort assignment. [[data-visualization/uncertainty-and-small-sample-display|Small-sample display]] and [[data-visualization/calendar-heatmap-complete-days-time-zones-and-missingness|calendar completeness]] help audit this comparison."),
        ],
        "code": '''from collections import defaultdict

def retention_ledger(enrollments: list[tuple[str, int]],
                     return_events: list[tuple[str, int]],
                     last_complete_period: int, max_age: int):
    if max_age < 0 or not isinstance(last_complete_period, int):
        raise ValueError("age and complete-period watermark must be valid")
    entry = {}
    cohorts = defaultdict(set)
    for member_id, period in enrollments:
        if not member_id or member_id in entry or period > last_complete_period:
            raise ValueError("members need one completed entry period")
        entry[member_id] = period
        cohorts[period].add(member_id)
    if not entry:
        raise ValueError("at least one enrolled member is required")
    returned = defaultdict(set)
    for member_id, period in return_events:
        if (member_id not in entry or period < entry[member_id] or
                period > last_complete_period):
            raise ValueError("return event falls outside the observed member history")
        returned[(entry[member_id], period - entry[member_id])].add(member_id)
    rows = []
    for cohort_period in sorted(cohorts):
        size = len(cohorts[cohort_period])
        cells = [1.0]
        for age in range(1, max_age + 1):
            cells.append(None if cohort_period + age > last_complete_period
                         else len(returned[(cohort_period, age)]) / size)
        rows.append((cohort_period, size, cells))
    return rows

members = [("member-47", 47), ("member-59", 47), ("member-83", 47),
           ("member-97", 48), ("member-131", 48), ("member-149", 49)]
returns = [("member-47", 48), ("member-47", 48), ("member-83", 48),
           ("member-47", 49), ("member-97", 49)]
heatmap = retention_ledger(members, returns, last_complete_period=49, max_age=2)
assert heatmap[0] == (47, 3, [1.0, 2 / 3, 1 / 3])
assert heatmap[1] == (48, 2, [1.0, 1 / 2, None])
assert heatmap[2] == (49, 1, [1.0, None, None])''',
        "cost": "For E enrollments, A return records, C cohorts and H requested ages, membership construction and event deduplication take O(E + A) expected time; sorting cohort keys takes O(C log C), and cell construction takes O(C·H). The entry and activity sets use O(E + A) space in the worst case, with O(C·H) output cells. Duplicate age-one activity from member-47 still counts once, while the newest cohort's future cells are None rather than zero. Period integers stand for consecutive, fully closed reporting periods; use a calendar-aware key upstream when weeks or months cross time-zone or fiscal boundaries.",
        "mistakes": ["Reassigning a returning member to a new entry cohort.", "Dividing by the previous period's active members while labeling the result cohort retention.", "Painting future or partial-period cells as zero percent.", "Counting duplicate return events as multiple retained users."],
        "drill": "Build weekly retention for 47 synthetic signup cohorts with a fixed last-complete-week watermark. Reconcile unique entry IDs, duplicate activity events and cohort sizes; publish age-one and age-four counts as well as rates, and leave all immature cells blank.",
        "related": [prefix + "heatmap-missing-cells-and-color-domain", prefix + "linked-filters-cohort-denominators-and-selection-state", prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "funnel-chart-cohorts-stage-order-and-conversion"],
    },
    {
        "slug": "autocorrelation-plots-regular-lags-pair-counts-and-seasonality",
        "title": "Autocorrelation plots: align equal-spaced periods before reading lag peaks",
        "summary": "Calculate lagged association only over valid pairs, report support by lag and distinguish a seasonal clue from a causal explanation.",
        "sections": [
            ("A lag must mean the same elapsed time", "An autocorrelation plot places lag on the horizontal axis and the association between a series and its own shifted values on the vertical axis. Lag two means two sampling intervals, not merely two available rows. If a daily series skips Tuesday and the values on Monday and Wednesday are adjacent in a database query, treating them as lag one silently changes the elapsed time. Choose a fixed sampling schedule, sort by period, reject duplicates and gaps or apply a separately documented missing-data policy. The simple ledger below requires consecutive integer period IDs and finite measurements. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Gap and calendar rules]] establish the input contract; [[data-visualization/event-aligned-time-series-baseline-windows-and-missing-periods|event-aligned charts]] answer a different timing question."),
            ("Show pair counts, not just spikes", "At lag k, only N minus k aligned pairs remain from N complete observations. Large lags therefore have less support, and a dramatic coefficient based on four pairs is fragile. Print the number of pairs beside a selected coefficient or in a companion table. The worked code uses Pearson correlation with means recalculated for each aligned pair set. This is a descriptive lagged Pearson coefficient, not every software package's traditional autocorrelation-function estimator, which may use a full-series mean and normalization. Name the estimator before comparing values across tools. A constant member of a pair set has zero variance, so the coefficient is undefined; display a missing mark instead of a fabricated zero. [[data-visualization/uncertainty-and-small-sample-display|Small-sample display]] keeps thin tails visible without overstating them."),
            ("Read repetition cautiously", "An alternating workload may produce a negative lag-one value and a positive lag-two value. A slow trend can also produce several high positive lag values even without a repeating cycle. A weekly schedule, a changed product mix or an instrumentation reset may create peaks that disappear after appropriate stratification or differencing. Inspect the run chart and known operational calendar before calling a spike seasonality. Correlation at a lag is not evidence that an earlier observation causes a later one. If the goal is forecasting, validate the candidate lag on held-out future periods and avoid using future values while constructing features. [[data-visualization/forecast-fan-charts-prediction-intervals-and-horizon|Forecast intervals]] describe predictive uncertainty, while [[data-visualization/chart-annotations-event-windows-and-causal-claims|event annotations]] make causal claims easier to audit."),
            ("Treat reference bands as assumptions", "A horizontal zero line helps read sign. Statistical confidence bands require a noise model, chosen estimator and a policy for many inspected lags; a generic shaded band is not a universal significance test. Adjacent lag estimates are related, and checking dozens of lags invites chance extremes. Freeze a practical maximum lag based on the question and available pairs, then disclose it. When input values are residuals from a fitted model, describe that fit and its validation window; residual autocorrelation can expose missing structure, but a model trained on the entire evaluation span can hide it. Compare adjacent operational phases on the same vertical scale and keep period count, gap policy and estimator in the export. [[data-visualization/chart-export-manifest-data-and-render-version|An export manifest]] carries the needed calculation details."),
        ],
        "code": '''from math import isfinite, sqrt

def lagged_pearson(readings: list[tuple[int, float]], max_lag: int):
    if len(readings) < 4 or not 1 <= max_lag <= len(readings) - 3:
        raise ValueError("retain at least three pairs at every requested lag")
    periods = [period for period, _ in readings]
    values = [value for _, value in readings]
    if (any(not isinstance(period, int) for period in periods) or
            any(current != previous + 1
                for previous, current in zip(periods, periods[1:])) or
            any(not isfinite(value) for value in values)):
        raise ValueError("readings must be ordered, consecutive and finite")
    coefficients = []
    for lag in range(1, max_lag + 1):
        before, after = values[:-lag], values[lag:]
        count = len(before)
        before_mean = sum(before) / count
        after_mean = sum(after) / count
        centered_before = [value - before_mean for value in before]
        centered_after = [value - after_mean for value in after]
        numerator = sum(left * right for left, right in zip(centered_before,
                                                            centered_after))
        spread_before = sum(value * value for value in centered_before)
        spread_after = sum(value * value for value in centered_after)
        correlation = (numerator / sqrt(spread_before * spread_after)
                       if spread_before and spread_after else None)
        coefficients.append((lag, count, correlation))
    return coefficients

alternating_load = list(zip(range(47, 55), [47.0, 59.0] * 4))
lag_summary = lagged_pearson(alternating_load, 3)
assert lag_summary[0] == (1, 7, -1.0)
assert lag_summary[1] == (2, 6, 1.0)
assert lag_summary[2] == (3, 5, -1.0)
assert lagged_pearson([(47, 83.0), (48, 83.0), (49, 83.0),
                       (50, 83.0)], 1)[0][2] is None''',
        "cost": "For N readings and K requested lags, each lag builds and scans N minus k paired values, yielding O(N·K) time and O(N + K) extra space, including temporary centered lists and the result. This favors an inspectable short-lag audit over an optimized transform; large K and long series justify a separately tested faster estimator with its own normalization rules. The eight-period alternating example returns minus one at lags one and three, plus one at lag two, and support counts seven, six and five. Constant readings return an undefined coefficient rather than a false zero.",
        "mistakes": ["Treating consecutive database rows as consecutive time periods after a gap.", "Comparing coefficients from different estimator conventions without naming the method.", "Calling a high-lag spike seasonality when only a handful of pairs remain.", "Adding generic significance bands without a noise model or multiple-lag policy."],
        "drill": "Take 83 completed daily workload measurements. Audit dates for gaps and duplicates, predeclare seven lags, plot each lagged coefficient with its pair count, then compare the result with a run chart and the known weekly operating schedule.",
        "related": [prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "event-aligned-time-series-baseline-windows-and-missing-periods", prefix + "forecast-fan-charts-prediction-intervals-and-horizon", prefix + "chart-annotations-event-windows-and-causal-claims"],
    },
]

publish(
    lessons,
    sort_start=8774,
    module_groups=[("Distribution area and cohort maturity", [0, 1]),
                   ("Serial dependence and seasonal evidence", [2])],
    incoming={
        "distribution-and-outlier-displays": [0],
        "box-violin-and-kde-bandwidth-for-group-comparisons": [0],
        "scale-baseline-and-axis-integrity": [0],
        "heatmap-missing-cells-and-color-domain": [1],
        "linked-filters-cohort-denominators-and-selection-state": [1],
        "funnel-chart-cohorts-stage-order-and-conversion": [1],
        "uncertainty-and-small-sample-display": [1, 2],
        "time-series-gaps-calendars-and-provisional-periods": [1, 2],
        "event-aligned-time-series-baseline-windows-and-missing-periods": [2],
        "forecast-fan-charts-prediction-intervals-and-horizon": [2],
    },
    packet_name="aitrove-data-visualization-import-20261008-o.json",
)
