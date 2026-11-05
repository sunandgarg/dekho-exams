"""Add original Data Visualization and Time Series paths to the local AI & Data preview."""
import datetime
import html
import json
from pathlib import Path
import re
import uuid

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
rows = [row for row in rows if not row['path'].startswith(('data-visualization/', 'time-series/'))]
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
lessons = []

def add(path, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path=path, title=title, summary=summary, sections=sections,
                        code=code, cost=cost, mistakes=mistakes, related=related))

add('data-visualization/chart-question-and-visual-encoding',
    'Chart design starts with a question, unit and visual encoding',
    'A chart is a visual comparison over defined observations; its marks and axes must preserve the quantity the reader is meant to compare.', [
    ('Write the comparison', 'A receipt operations report might ask whether the share of reviews completed within 24 hours changed by channel. That is a rate by category and period, not a count of tickets. Record the population, numerator, denominator, time window and update cadence before picking a shape. [[data-science/metric-denominator-and-cohort|Metric denominators]] belong in the chart contract because a change in eligibility can look like a change in performance.'),
    ('Map quantities to marks', 'Position on a common scale is useful for comparing rates across channels; a bar chart makes zero a visible reference. Use a line only when adjacent points are connected by an ordered process such as time. A scatter plot asks whether two numeric quantities move together. A decorative shape must not imply a numerical relationship the dataset does not contain.'),
    ('Preserve context', 'Show units, sample counts and the period cutoff. A rate can rise when a low-volume channel disappears even if no channel improves. Add a small companion table or labels with denominators when that composition matters. [[data-visualization/aggregation-grain-and-denominator|Aggregation grain]] determines what the visual mark actually represents. Never use a legend to hide a definition required to read the chart.'),
    ('Specify a review fixture', 'Create one channel with 34 timely reviews out of 47 receipts and another with 18 out of 23. The second bar is higher despite its lower count. Ask a reviewer to state that distinction from the figure alone, then test an empty channel. Empty is missing evidence, not a zero percent service rate.')],
    'def channel_completion_rate(timely_count, eligible_count):\n    if eligible_count < 0 or timely_count < 0 or timely_count > eligible_count:\n        raise ValueError("invalid receipt counts")\n    return None if eligible_count == 0 else timely_count / eligible_count\n\nchannel_rates = {\n    "portal": channel_completion_rate(34, 47),\n    "email": channel_completion_rate(18, 23),\n}',
    'Computing C channel rates is O(C) time and O(C) output space. Rendering cost grows with the number of marks, labels and interaction states; filter or aggregate only under a stated rule so the viewer can recover the denominator.',
    ['Do not substitute counts for rates when channel volumes differ.', 'Do not connect unordered categories with a line.', 'Do not render an empty denominator as a measured zero.'],
    ['data-visualization/aggregation-grain-and-denominator','data-visualization/scale-baseline-and-axis-integrity','data-science/metric-denominator-and-cohort','applied-statistics/population-estimand-and-sampling-frame'])

add('data-visualization/aggregation-grain-and-denominator',
    'Aggregation grain and denominator: make every plotted mark auditable',
    'A visual aggregate is trustworthy only when each source row, grouping key and denominator have a declared meaning.', [
    ('Fix the source grain', 'A receipt table can contain one row per receipt while a status log contains several rows per receipt. Joining them and counting rows creates a review volume that rises when the workflow emits more events. Reduce the log to one terminal outcome per receipt before joining, or build an explicit event-level chart. [[data-science/dataset-grain-and-join-cardinality|Join cardinality]] is a precondition for visual accuracy.'),
    ('Choose the denominator', 'A chart titled “review completion rate” needs a rule for receipts that were submitted but not yet eligible, rejected at intake or still open. Keep numerator and denominator alongside the plotted rate in the data contract. When filtering by channel, recompute both counts for the filtered cohort; never filter precomputed overall rates and average them.'),
    ('Control time bins', 'A daily chart needs one time zone, one interval convention and an explicit policy for late events. A receipt submitted at 23:58 and completed after midnight might belong to the submission-day cohort even though its completion event occurs next day. [[time-series/observation-calendar-and-missing-periods|Calendar policy]] keeps those two clocks apart. Document whether incomplete days are omitted or shown as provisional.'),
    ('Reconcile the visual', 'For two channels with 34 of 47 and 18 of 23 timely receipts, the combined rate is 52 of 70, about 74.3 percent. The simple average of the two channel percentages is different. Test that the dashboard total uses summed counts. Include an empty group and one duplicated receipt ID to catch silent inflation.')],
    'def weighted_completion_rate(channel_counts):\n    timely = 0\n    eligible = 0\n    for timely_count, eligible_count in channel_counts:\n        if not 0 <= timely_count <= eligible_count:\n            raise ValueError("invalid channel counts")\n        timely += timely_count\n        eligible += eligible_count\n    return None if eligible == 0 else timely / eligible',
    'Aggregating N rows by C keys is O(N) expected time and O(C) state with a hash map. Sorting labels adds O(C log C). A database group-by can move the work closer to the source, but its join and filter contracts still need inspection.',
    ['Do not average percentages when group sizes differ.', 'Do not count event rows as independent receipts.', 'Do not combine submission and completion timestamps without a cohort rule.'],
    ['data-visualization/chart-question-and-visual-encoding','data-visualization/dashboard-filter-and-provenance','data-science/dataset-grain-and-join-cardinality','time-series/observation-calendar-and-missing-periods'])

add('data-visualization/scale-baseline-and-axis-integrity',
    'Axis scales, baselines and labels: prevent a correct number from telling a false story',
    'Axis choices change visual distance, so the scale must match the comparison and be disclosed wherever it changes interpretation.', [
    ('Use a meaningful baseline', 'Bar length is read against its baseline. Starting a bar axis at 0.71 can make two completion rates of 0.74 and 0.77 look several times apart. Use zero for ordinary bar lengths and show exact values when a small difference matters. A line chart may use a narrower range to show variation, but the displayed bounds and units must remain obvious.'),
    ('Inspect transformations', 'A logarithmic axis can reveal values across orders of magnitude, but equal screen distances then represent equal ratios rather than equal differences. Zero and negative values need an explicit treatment. Never switch an axis to logarithmic merely to fit an outlier, and never compare a linear-panel slope with a log-panel slope as though they share meaning.'),
    ('Keep category order honest', 'Sort categories by a documented metric or a stable domain order. If the order changes at each refresh, motion can look like a performance shift when values are steady. Labels should state percent versus percentage points; moving from 74 to 77 percent is a three-point change, not a three-percent relative change. [[data-visualization/chart-question-and-visual-encoding|The chart question]] decides which comparison is primary.'),
    ('Test presentation rules', 'Prepare two rates, 0.74 and 0.77, and verify both bars share zero. Then format them as 74.0% and 77.0%. If a narrow view clips labels, retain an accessible text table. Recheck after filtering because an automatic axis may silently rescale and change the apparent difference.')],
    'def percentage_point_change(previous_rate, current_rate):\n    if not all(0 <= rate <= 1 for rate in (previous_rate, current_rate)):\n        raise ValueError("rates must be between zero and one")\n    return (current_rate - previous_rate) * 100\n\nchange_points = percentage_point_change(0.74, 0.77)',
    'Scale formatting is O(M) for M plotted marks. The larger cost is review: test every filter state that changes axis bounds, zero visibility or label collisions. Cache formatted labels only when underlying rate and unit versions match.',
    ['Do not truncate a bar axis without making the baseline explicit.', 'Do not label a percentage-point movement as a relative percent.', 'Do not hide nonpositive observations when using a logarithmic scale.'],
    ['data-visualization/chart-question-and-visual-encoding','data-visualization/distribution-and-outlier-displays','data-visualization/accessible-color-and-text-alternatives','applied-statistics/distribution-quantiles-and-outlier-policy'])

add('data-visualization/distribution-and-outlier-displays',
    'Distribution plots: keep the tail, missing values and bin policy visible',
    'Histograms and quantile summaries answer shape questions that a single mean or trend line cannot settle.', [
    ('Distinguish populations', 'Review delay among completed receipts excludes receipts still open. A histogram of completed delays therefore cannot describe the full submission cohort without a censoring policy. State the population and cutoff. [[applied-statistics/distribution-quantiles-and-outlier-policy|Distribution summaries]] help reveal a long tail, while a separate pending count shows records that do not yet have a delay.'),
    ('Choose bins deliberately', 'A histogram with bins of one hour may appear noisy; a bin of one day can conceal a 24-hour service threshold. Fix bin edges across compared periods and label whether the left or right edge is included. Do not auto-bin each channel independently and then compare the resulting bar heights as though the units were identical.'),
    ('Retain the tail', 'A rare 47-hour delay can matter more operationally than a high-volume cluster near five hours. If the axis is cropped to show the center, disclose the number above the cap and provide a full-range or quantile companion view. Invalid negative delays should be separated from valid extremes. [[data-visualization/scale-baseline-and-axis-integrity|Axis policy]] must remain stable across cohorts.'),
    ('Make a small fixture', 'Start with delays of 3, 4, 5, 6 and 47 hours. The mean is 13 and the median is 5. A chart that omits the last value while still reporting the original mean is internally inconsistent. Test zero valid observations, one extreme observation and a delayed arrival that changes a closed reporting period.')],
    'def delay_bins(delays_hours, edges):\n    if len(edges) < 2 or edges[0] < 0 or any(left >= right for left, right in zip(edges, edges[1:])):\n        raise ValueError("bin edges must increase from a nonnegative start")\n    counts = [0] * (len(edges) - 1)\n    overflow = 0\n    for delay in delays_hours:\n        if delay < edges[0]:\n            raise ValueError("delay falls below the declared range")\n        location = next((index for index, (left, right) in enumerate(zip(edges, edges[1:]))\n                         if left <= delay < right), None)\n        if location is None:\n            overflow += 1\n        else:\n            counts[location] += 1\n    return counts, overflow',
    'This direct bin search costs O(NB) for N observations and B bins, with O(B) output space. A binary search on sorted edges reduces lookup to O(N log B). Store missing and overflow counts separately so a faster renderer cannot erase them.',
    ['Do not compare histograms with different bin edges as if they were identical.', 'Do not trim a valid operational tail without reporting the omitted count.', 'Do not treat an unfinished receipt as a completed zero-hour delay.'],
    ['data-visualization/scale-baseline-and-axis-integrity','data-visualization/uncertainty-and-small-sample-display','applied-statistics/distribution-quantiles-and-outlier-policy','data-science/missing-data-policy'])

add('data-visualization/uncertainty-and-small-sample-display',
    'Uncertainty on charts: show denominators and intervals beside estimates',
    'A plotted estimate is not a population fact; its uncertainty and sample unit affect how strongly a visual difference can be read.', [
    ('Show the independent count', 'Two channels can both report a 75 percent completion rate, yet one may have 12 receipts and another 12,000. Put eligible counts near marks or in an accessible companion table. If customers submit repeated receipts, the independent count may be customers rather than rows. [[applied-statistics/cluster-bootstrap-and-standard-error|Cluster resampling]] keeps those observations together.'),
    ('Choose an interval contract', 'Specify the estimator, interval construction, confidence level and sampling unit. Error bars from an independent-row formula are misleading when assignments or outcomes cluster by reviewer. A confidence interval describes a repeated-sampling procedure; it is not a probability distribution over the displayed fixed rate. [[applied-statistics/confidence-interval-coverage|Coverage]] requires a valid observation process.'),
    ('Separate overlap from decision', 'Overlapping intervals do not by themselves establish that a difference is absent, and nonoverlap is not a universal experiment test. If the task is to compare channels, calculate and display an interval for the difference under the study design. Pair this with practical limits: a two-point change may matter only above a declared volume or cost threshold.'),
    ('Handle thin groups', 'A filter may leave one receipt or none. Use a visible “insufficient data” state rather than a narrow-looking point with absent error bars. Check that each interval is within the metric domain and that chart tooling does not clip it without notice. Keep the raw numerator and denominator available for audit.')],
    'def interval_mark(point_rate, lower_rate, upper_rate, eligible_count):\n    if eligible_count < 2:\n        return {"state": "insufficient_data", "eligible_count": eligible_count}\n    if not 0 <= lower_rate <= point_rate <= upper_rate <= 1:\n        raise ValueError("invalid rate interval")\n    return {"state": "measured", "point": point_rate,\n            "lower": lower_rate, "upper": upper_rate, "eligible_count": eligible_count}',
    'Formatting M intervals is O(M) time and space. Interval estimation may be much more expensive, especially when resampling clusters; calculate it in a versioned data job and render the stored estimate with its construction metadata.',
    ['Do not draw error bars without naming their meaning.', 'Do not use receipt count as the independent sample size when customers repeat.', 'Do not interpret overlapping intervals as a complete test of a difference.'],
    ['data-visualization/distribution-and-outlier-displays','data-visualization/dashboard-filter-and-provenance','applied-statistics/confidence-interval-coverage','applied-statistics/cluster-bootstrap-and-standard-error'])

add('data-visualization/accessible-color-and-text-alternatives',
    'Accessible charts: encode meaning without relying on color alone',
    'A chart needs legible labels, keyboard access where interactive, and a text route to the same substantive data.', [
    ('Keep meaning redundant', 'A red and green pair is not enough to distinguish two completion series. Use direct labels, distinct line styles or marker shapes, and a legend that names the measured groups. Color can reinforce meaning but should not carry it alone. [[data-visualization/scale-baseline-and-axis-integrity|Axis labels]] must include units and remain legible at narrow widths.'),
    ('Write a useful alternative', 'An image alternative should state the main comparison and notable exception, not simply “bar chart.” A companion table should expose exact values, periods and denominators for readers who cannot use the graphic. For an interactive chart, its filter controls need visible names, keyboard focus and a text update when the dataset changes.'),
    ('Test the states', 'Check high zoom, narrow layout, monochrome output and keyboard-only interaction. A hover tooltip is not an adequate source of the only exact value. If a tooltip reports 74 percent but the accessible table says 73.6 percent, declare rounding once and use it consistently. [[data-visualization/dashboard-filter-and-provenance|Dashboard filters]] must update both representations together.'),
    ('Budget complexity', 'A dense chart with 40 small labels may be technically accessible but still hard to scan. Reduce visible series, use a stable sort and provide a drill-down or table for detail. Retain disclosure of hidden groups and totals so simplification does not selectively remove an unfavorable channel.')],
    'def chart_alt_text(period_label, channel_rates):\n    measured = [(channel, rate) for channel, rate in channel_rates.items() if rate is not None]\n    if not measured:\n        return f"{period_label}: no channel has an eligible denominator."\n    highest_channel, highest_rate = max(measured, key=lambda item: item[1])\n    return (f"{period_label}: {len(measured)} channels measured; "\n            f"{highest_channel} has the highest completion rate at {highest_rate:.1%}.")',
    'A short alternative over C channels costs O(C) time and O(C) temporary space in this implementation. For larger datasets, aggregate once and reuse the exact result for chart, table and alternative text to prevent divergence.',
    ['Do not rely on hue alone to identify a series.', 'Do not put the only exact value in a pointer-only tooltip.', 'Do not write alternative text from stale data after filters change.'],
    ['data-visualization/chart-question-and-visual-encoding','data-visualization/dashboard-filter-and-provenance','data-visualization/uncertainty-and-small-sample-display','data-science/metric-denominator-and-cohort'])

add('data-visualization/dashboard-filter-and-provenance',
    'Dashboard filters and provenance: make every view reproducible',
    'A dashboard is a family of data queries; each control changes the population and needs an explicit, inspectable state.', [
    ('Version the query state', 'A screenshot of a 74 percent review rate means little without period, channel, eligibility version and data-refresh time. Encode those fields in a shareable state record. If a filter changes the cohort, recompute counts and intervals rather than carrying cached percentages across populations. [[data-visualization/aggregation-grain-and-denominator|The denominator]] must travel with every filtered value.'),
    ('Manage defaults', 'A default “last 30 days” view moves each day. Use a fixed reporting cutoff for reproducible review packets and mark live periods provisional. If the dashboard initially excludes low-volume channels, disclose that exclusion rather than implying the total includes all channels. Make “all eligible channels” a testable state.'),
    ('Prevent stale joins', 'A filter change may return fast chart data while the companion table or alternative text still shows the previous request. Apply response IDs or cancellation to keep all representations synchronized. The data pipeline should expose snapshot ID and query version. [[data-engineering/backfill-publication-boundary|Publication boundaries]] offer a model for replacing a complete snapshot atomically.'),
    ('Reproduce a decision', 'Save a review packet with filter state, metric definition, source snapshot, numerator, denominator and chart version. Re-run it after a late receipt arrives; the old packet must remain explainable even if the live dashboard changes. Test an invalid channel and a period with no eligible receipts rather than silently falling back to another state.')],
    'def dashboard_state(snapshot_id, start_day, end_day, channels):\n    if not snapshot_id or start_day >= end_day:\n        raise ValueError("invalid snapshot or period")\n    selected = tuple(sorted(set(channels)))\n    if not selected:\n        raise ValueError("select at least one channel")\n    return {"snapshot_id": snapshot_id, "start_day": start_day,\n            "end_day": end_day, "channels": selected}',
    'Canonicalizing C selected channels costs O(C log C) time and O(C) space. Query and render costs depend on the backend and mark count; a versioned aggregate cache can help, but its key must include every population-changing filter.',
    ['Do not publish a decision screenshot without snapshot and filter state.', 'Do not reuse an overall interval after changing the cohort.', 'Do not let chart, table and alternative text resolve different query responses.'],
    ['data-visualization/accessible-color-and-text-alternatives','data-visualization/aggregation-grain-and-denominator','data-engineering/backfill-publication-boundary','time-series/observation-calendar-and-missing-periods'])

add('data-visualization/receipt-review-dashboard-project',
    'Project: build an auditable receipt-review dashboard',
    'Build a small review dashboard whose rates, distribution, uncertainty and accessible summary all come from one versioned data contract.', [
    ('Define the packet', 'Use receipt ID, channel, submission time, terminal outcome time and eligibility status as the input. Write the target population, time zone, daily cutoff and duplicate-ID policy. Produce an input manifest with source snapshot and row counts. [[data-visualization/aggregation-grain-and-denominator|Grain and denominator]] must be documented before drawing the first mark.'),
    ('Implement three views', 'Create a bar comparison of channel completion rates, a delay distribution with overflow count and a trend of daily eligible submissions. Each view needs axes, units, exact values and a text alternative. Show eligible counts beside rates and mark open or incomplete days. [[data-visualization/accessible-color-and-text-alternatives|Accessible encoding]] is part of completion, not optional polish.'),
    ('Validate data and display', 'Check two channels at 34 of 47 and 18 of 23: the combined completion rate is 52 of 70, not the mean of the two percentages. Check delays of 3, 4, 5, 6 and 47 hours: the median is 5 and the tail remains visible. Add a duplicated receipt and an empty period; both must have deliberate states.'),
    ('Submit reproducible evidence', 'Save the data fixture, calculated aggregates, rendering script or chart specification, filter state and a short decision note. The note should name what can and cannot be inferred from the sample. A reviewer should be able to trace a displayed mark to source IDs and explain every exclusion. Link the project to [[applied-statistics/confidence-interval-coverage|uncertainty]] only if an interval construction is included and tested.')],
    'def dashboard_total(channel_counts):\n    timely_total = 0\n    eligible_total = 0\n    for timely, eligible in channel_counts:\n        if not 0 <= timely <= eligible:\n            raise ValueError("invalid channel")\n        timely_total += timely\n        eligible_total += eligible\n    return None if eligible_total == 0 else timely_total / eligible_total\n\nassert dashboard_total([(34, 47), (18, 23)]) == 52 / 70',
    'A single pass over N receipts can accumulate C channel groups in O(N) expected time and O(C) state; the distribution adds O(B) bins. Rendering should reuse those aggregates. The deliverable must include runtime checks on real input before operational use.',
    ['Do not average channel percentages into a total.', 'Do not hide a 47-hour valid delay from the distribution.', 'Do not submit a screenshot without data and filter provenance.'],
    ['data-visualization/chart-question-and-visual-encoding','data-visualization/distribution-and-outlier-displays','data-visualization/dashboard-filter-and-provenance','applied-statistics/confidence-interval-coverage'])

add('time-series/observation-calendar-and-missing-periods',
    'Time-series calendar: distinguish missing periods from measured zeros',
    'A time series is an ordered set of observations under a fixed calendar, sampling interval and reporting cutoff.', [
    ('Define the clock', 'Receipt submissions arrive as instants while a daily operations report uses business dates. Choose a time zone and decide whether daily bins are left-closed or right-closed. Daylight-saving changes can create local days with different hour counts; do not assume every local day contains 24 hours. [[data-visualization/aggregation-grain-and-denominator|Aggregation grain]] links the calendar to the population counted in each bin.'),
    ('Preserve absence', 'A day with no submissions is a measured zero only if ingestion was healthy and that day was in scope. An outage or absent file is missing data. Use an explicit completeness flag rather than filling every gap with zero, because a false zero changes trends, seasonality and service decisions. [[data-science/missing-data-policy|Missingness policy]] belongs in the dataset manifest.'),
    ('Handle revisions', 'A submission may arrive late or be corrected after a daily snapshot closes. Set a watermark and label recent days provisional. Publish a new snapshot when historical counts are revised; keep the old version for a decision audit. Store event time and ingestion time separately so a late record can be located without inventing an artificial submission date.'),
    ('Exercise boundary cases', 'Construct events at 23:59 and 00:01 around the chosen cutoff, plus a calendar day with no source file and a day with a confirmed empty file. The first two must land in different daily bins; only the confirmed empty day may become zero. Test a repeated receipt ID so a retry does not inflate volume.')],
    'def daily_submission_counts(events, calendar_days, complete_days):\n    counts = {day: 0 for day in calendar_days}\n    seen_receipts = set()\n    for receipt_id, business_day in events:\n        if receipt_id in seen_receipts:\n            raise ValueError("duplicate receipt")\n        seen_receipts.add(receipt_id)\n        if business_day in counts:\n            counts[business_day] += 1\n    return {day: counts[day] if day in complete_days else None\n            for day in calendar_days}',
    'A single pass over N events and D calendar days costs O(N + D) expected time and O(N + D) state with duplicate detection. If upstream uniqueness is proven, counts need only O(D) state; retain the proof and revision policy.',
    ['Do not convert an ingestion outage into zero demand.', 'Do not group UTC timestamps by a local date without an explicit time zone.', 'Do not silently overwrite a closed historical snapshot.'],
    ['time-series/lag-features-and-future-leakage','time-series/seasonal-naive-baseline','data-visualization/aggregation-grain-and-denominator','data-science/missing-data-policy'])

add('time-series/lag-features-and-future-leakage',
    'Lag features: prove each input existed at forecast time',
    'A forecasting feature is valid only if the production system can know its value at the prediction cutoff.', [
    ('State the forecast origin', 'Suppose a staffing forecast is issued at 18:00 for tomorrow’s receipt count. Yesterday’s finalized count may be available, while today’s final count is not. Define the origin timestamp, target window and availability delay for every source. [[time-series/observation-calendar-and-missing-periods|Calendar policy]] separates event time from ingestion time.'),
    ('Build causal lags', 'A lag of seven days is a value observed seven calendar positions before the target; it is not the seventh previous nonmissing row. Reindex to the declared calendar first. Rolling means should exclude the target period and any recent period still incomplete at the origin. A shift after rolling can work, but inspect actual timestamps rather than trusting a pipeline name.'),
    ('Treat external signals', 'A promotion plan may be known in advance; realized promotion clicks are not. A weather forecast available at issue time can be a feature, whereas realized weather for tomorrow leaks the answer period. Keep a version or availability timestamp for external values. [[machine-learning/group-and-time-validation|Time-aware validation]] must replay those same feature availability rules.'),
    ('Run a leakage test', 'Give a sequence with a sharp final spike and request a forecast before that spike occurred. Changing the spike must not change features for earlier origins. Also test a missing date, because a naive row shift can turn an eight-day-old observation into a supposed seven-day lag when one row is absent.')],
    'def lag_seven_at_origin(values_by_day, ordered_days, origin_index):\n    if not 0 <= origin_index < len(ordered_days):\n        raise ValueError("invalid forecast origin")\n    lag_index = origin_index - 7\n    if lag_index < 0:\n        return None\n    return values_by_day.get(ordered_days[lag_index])',
    'A direct indexed lag lookup is O(1) after an ordered calendar is built; creating all L lags for D origins is O(DL) time and space if materialized. The hard constraint is temporal availability, which needs audit metadata rather than faster arithmetic.',
    ['Do not compute a rolling statistic that includes the target day.', 'Do not treat previous nonmissing row as a fixed calendar lag.', 'Do not train on realized external values unavailable at issue time.'],
    ['time-series/observation-calendar-and-missing-periods','time-series/rolling-origin-backtest-and-gap','machine-learning/group-and-time-validation','data-science/missing-data-policy'])

add('time-series/seasonal-naive-baseline',
    'Seasonal naive forecast: establish a baseline before fitting a model',
    'A seasonal naive forecast repeats the last observed value at the same phase of a known cycle.', [
    ('Match the horizon', 'For a daily series with a weekly pattern, next Monday can use the previous Monday as a baseline. The baseline must use the value known at the forecast origin; if that previous Monday is incomplete or revised later, record the version actually available. A last-value baseline is also useful when no stable seasonality is evident. [[time-series/observation-calendar-and-missing-periods|Calendar completeness]] matters more than a fancy estimator.'),
    ('Compare against a real alternative', 'A trained model should beat simple rules on the same origins, target windows and missing-period policy. Report error by weekday and horizon, not merely a pooled average. A model that improves low-volume weekdays while failing a peak day may harm staffing. [[time-series/multi-horizon-errors-and-denominators|Metric slices]] expose that tradeoff.'),
    ('Separate trend and seasonality', 'Repeating last week cannot respond to a sustained rise in submissions. A drift baseline projects recent change, but it can amplify an anomalous week. Before adding such a rule, plot observed data, report the history window and compare it to the simpler seasonal rule. Do not tune the baseline on the same final holdout used for model selection.'),
    ('Build a tiny fixture', 'Use two complete weeks of daily counts. A Monday value of 47 in the previous week should yield 47 for the next Monday at a seven-day seasonal lag. Remove that earlier Monday and require a missing forecast or a declared fallback, not a silent lookup of Sunday.')],
    'def seasonal_naive(history, target_index, season_length=7):\n    if season_length < 1 or target_index < 0:\n        raise ValueError("invalid season or target")\n    source_index = target_index - season_length\n    if source_index < 0 or source_index >= len(history):\n        return None\n    return history[source_index]',
    'Each forecast is O(1) time and O(1) extra space after calendar alignment. Forecasting H positions is O(H). The baseline gives an inexpensive performance floor and exposes data-quality failures before a fitted model adds operational cost.',
    ['Do not replace a missing seasonal source with the nearest row without a rule.', 'Do not compare models on different origins or holdout periods.', 'Do not assume weekly seasonality merely because data is daily.'],
    ['time-series/rolling-origin-backtest-and-gap','time-series/multi-horizon-errors-and-denominators','time-series/observation-calendar-and-missing-periods','data-science/exploratory-analysis-without-peeking'])

add('time-series/rolling-origin-backtest-and-gap',
    'Rolling-origin backtests: rehearse the forecast as it would have run',
    'A backtest evaluates forecasts at successive historical origins using only data available before each origin.', [
    ('Move origin forward', 'Choose an initial training window, issue a forecast, score its target period, then move the origin. Expanding windows retain all prior history; sliding windows discard older periods. State which behavior is intended and why. A random row split lets future observations train a model for earlier predictions and invalidates the deployment simulation.'),
    ('Leave a data gap', 'If outcomes finalize two days after submission, the training window at today’s origin must stop before those unresolved days. A gap also protects against lookahead from lagged features or source processing delays, but its size should come from availability facts. [[time-series/lag-features-and-future-leakage|Feature lineage]] must be reconstructed for every origin.'),
    ('Avoid overlapping-score confusion', 'A seven-day forecast issued daily creates overlapping target windows. Scoring every daily origin is still useful, yet errors are correlated and naive confidence calculations can overstate independent evidence. Report origin count, horizon and evaluation period. Keep one final recent holdout untouched while choosing features and model settings.'),
    ('Test the index arithmetic', 'With 35 daily observations, an initial 14-day training window, a two-day gap and a three-day forecast horizon, the first target begins at index 16. Its target indices are 16, 17 and 18. Confirm later origins never train on their own target rows and stop before the horizon exceeds available history.')],
    'def rolling_origins(observation_count, min_train=14, gap=2, horizon=3):\n    if min_train < 1 or gap < 0 or horizon < 1:\n        raise ValueError("invalid backtest window")\n    for train_end in range(min_train, observation_count - gap - horizon + 1):\n        target_start = train_end + gap\n        yield range(0, train_end), range(target_start, target_start + horizon)',
    'For O origins, generating index windows costs O(O) iterator overhead, but refitting a model can dominate at O times its training cost. Store compact origin and score records rather than copying every training slice unless reproducibility requires it.',
    ['Do not random-split a temporally ordered forecast task.', 'Do not choose a gap by habit when source availability has a different delay.', 'Do not treat overlapping forecast errors as independent replicates.'],
    ['time-series/lag-features-and-future-leakage','time-series/seasonal-naive-baseline','time-series/multi-horizon-errors-and-denominators','machine-learning/group-and-time-validation'])

add('time-series/multi-horizon-errors-and-denominators',
    'Forecast metrics by horizon: keep errors, zeros and denominators explicit',
    'Forecast quality changes with how far ahead a prediction is made, so a pooled score can conceal operational failures.', [
    ('Score each horizon', 'A one-day forecast and a seven-day forecast support different staffing decisions. Calculate absolute error at each horizon and report origin count and target count. A mean across all scored cells can overweight horizons with more available observations. Define a fixed evaluation matrix or present separate horizon metrics. [[time-series/rolling-origin-backtest-and-gap|Rolling origins]] provide the forecast records.'),
    ('Handle zero demand', 'Percentage error divides by actual demand and becomes undefined at zero. Dropping zero days can make a service with intermittent receipts look much better than it is. MAE stays defined, while a scaled error needs a training-only scale that is nonzero. Show the number of zero-demand targets and how each metric treats them.'),
    ('Make bias visible', 'Mean absolute error hides the direction of error. A model that underforecasts every peak day may have acceptable MAE yet repeatedly understaff the queue. Report signed error, peak-day slices and interval coverage if intervals are supplied. [[time-series/forecast-interval-and-calibration|Interval evaluation]] addresses the uncertainty of future counts, not just point accuracy.'),
    ('Recompute an example', 'For actual counts 47, 52 and 0, with forecasts 43, 58 and 6, absolute errors are 4, 6 and 6; MAE is 16 divided by 3. Signed forecast-minus-actual errors are -4, 6 and 6. A percentage metric cannot consume the final actual value without an explicit zero policy.')],
    'def forecast_error_summary(actual_counts, predicted_counts):\n    if len(actual_counts) != len(predicted_counts) or not actual_counts:\n        raise ValueError("paired nonempty forecasts required")\n    errors = [forecast - actual for actual, forecast in zip(actual_counts, predicted_counts)]\n    return {"mae": sum(abs(error) for error in errors) / len(errors),\n            "bias": sum(errors) / len(errors),\n            "zero_actuals": sum(actual == 0 for actual in actual_counts)}',
    'Calculating metrics for N paired forecasts costs O(N) time and O(N) memory here; streaming sums reduce memory to O(1). Grouping by H horizons needs O(H) aggregates. Preserve the origin and target identifiers so paired scores remain auditable.',
    ['Do not silently drop zero-demand targets from a percentage metric.', 'Do not combine horizons with unequal record counts without a weighting rule.', 'Do not report only unsigned error for an asymmetric staffing cost.'],
    ['time-series/rolling-origin-backtest-and-gap','time-series/forecast-interval-and-calibration','time-series/seasonal-naive-baseline','applied-statistics/hypothesis-test-and-effect-size'])

add('time-series/forecast-interval-and-calibration',
    'Forecast intervals: measure future-outcome coverage by horizon',
    'A forecast interval describes plausible future observations under an explicit model and evaluation process.', [
    ('Separate two uncertainties', 'An interval around an estimated historical mean is not the same as an interval for tomorrow’s actual receipt count. Future observations include process noise and possible shifts. Construct a prediction interval for the quantity that operations needs. [[applied-statistics/confidence-interval-coverage|Confidence-interval coverage]] is related, but its target can be a fixed population parameter rather than a future outcome.'),
    ('Check empirical coverage', 'On held-out backtest origins, count how often actual demand falls between the stated lower and upper bounds. Report this by forecast horizon and volume slice. A nominal 90 percent interval that covers only 62 percent of peak days is not operationally calibrated for staffing. Also report width; a needlessly huge interval can cover everything while remaining useless.'),
    ('Preserve causal calibration', 'If residual quantiles are used to form bounds, estimate them from earlier backtest errors and evaluate on later periods. Reusing the final test errors to tune their own interval width leaks outcome information. Intervals for counts should respect the nonnegative domain, but clipping a lower bound can alter achieved coverage and should be rechecked.'),
    ('Exercise a fixture', 'Use four held-out actual counts and fixed interval bounds. Verify that values exactly on endpoints count as covered under the documented convention. Reject inverted bounds and negative actual counts. A later release should compare measured coverage with the earlier baseline under the same horizon and calendar rules.')],
    'def empirical_interval_coverage(actual_counts, bounds):\n    if len(actual_counts) != len(bounds) or not actual_counts:\n        raise ValueError("paired intervals required")\n    covered = 0\n    for actual, (lower, upper) in zip(actual_counts, bounds):\n        if actual < 0 or lower > upper:\n            raise ValueError("invalid count or interval")\n        covered += lower <= actual <= upper\n    return covered / len(actual_counts)',
    'Coverage over N paired records is O(N) time and O(1) extra space. Constructing model intervals may cost far more, especially with simulation or repeated fitting. Cache intervals with model, origin, horizon and source-snapshot IDs.',
    ['Do not label a mean-estimate interval as a future-outcome interval.', 'Do not tune bounds on the final period used to report coverage.', 'Do not report coverage without interval width and horizon.'],
    ['time-series/multi-horizon-errors-and-denominators','time-series/forecast-monitoring-and-retraining','applied-statistics/confidence-interval-coverage','data-science/bootstrap-interval-interpretation'])

add('time-series/forecast-monitoring-and-retraining',
    'Forecast monitoring: separate data delay, demand shift and model failure',
    'Forecast operations need a versioned prediction ledger and an outcome-availability rule before error alerts can be trusted.', [
    ('Log each issue', 'Store forecast origin, target period, model version, source snapshot, point estimate, interval and issued time. When actuals arrive, match by target identifier and outcome version. Without that ledger, a later revision can make old forecasts appear to have used information they never had. [[time-series/observation-calendar-and-missing-periods|Watermarks]] explain why recent actuals may still be provisional.'),
    ('Diagnose the alert', 'A sudden run of zero actuals can mean an ingestion outage rather than a genuine collapse in demand. Check source freshness and completeness before calculating drift or launching retraining. Compare error by horizon, channel and peak day. [[time-series/multi-horizon-errors-and-denominators|Directional error]] can reveal persistent underforecasting while average magnitude looks stable.'),
    ('Control retraining', 'A scheduled refit is not automatically an improvement. Rebuild features under the same availability contract, compare with the incumbent and seasonal naive baseline on later origins, then publish atomically with rollback metadata. Keep an untouched evaluation period for release decisions and avoid automatically training on provisional labels.'),
    ('Prove reversibility', 'Simulate a bad release that underforecasts one channel. The monitor should identify the affected horizon and source version, and the serving layer should restore the prior model without rewriting historical forecast records. Record whether the correction changes only future forecasts or also revises dashboard history.')],
    'def eligible_forecast_errors(forecast_rows, final_actuals):\n    scored = []\n    for forecast in forecast_rows:\n        target_key = forecast["target_key"]\n        if target_key not in final_actuals:\n            continue\n        scored.append((target_key, forecast["prediction"] - final_actuals[target_key]))\n    return scored',
    'Matching F forecasts to final actuals in a dictionary costs O(F) expected time and O(F) output space. Retraining cost depends on the model, but gate checks should stay cheap enough to run for every candidate release.',
    ['Do not alert on error before the outcome is final.', 'Do not treat an ingestion outage as demand drift.', 'Do not overwrite historical predictions when a model is replaced.'],
    ['time-series/forecast-interval-and-calibration','time-series/receipt-volume-forecast-project','mlops/shadow-canary-and-rollback','time-series/observation-calendar-and-missing-periods'])

add('time-series/receipt-volume-forecast-project',
    'Project: forecast receipt volume with a reproducible rolling backtest',
    'Build a daily receipt-volume forecast whose calendar, feature availability, baseline, backtest and release decision can all be inspected.', [
    ('Create the dataset contract', 'Use daily receipt counts with a declared business time zone, complete-day flag and source snapshot. Include a confirmed zero day, an outage day and a late-arriving receipt. The outage must remain missing. Record the forecast origin and target horizon before selecting features. [[time-series/observation-calendar-and-missing-periods|Calendar rules]] belong in the submitted manifest.'),
    ('Establish the comparison', 'Implement last-value and seven-day seasonal naive baselines. If a candidate model is added, construct only features known at each origin and retain a two-day outcome delay when that matches the fixture. Run expanding or sliding rolling-origin backtests and explain the choice. [[time-series/rolling-origin-backtest-and-gap|Origin windows]] must not cross into their target periods.'),
    ('Evaluate decisions', 'Report MAE, signed bias and record counts separately by horizon. Show errors for peak days and zero-demand days. If intervals are supplied, report empirical coverage and width on a later period; never tune them on that same period. A candidate should beat the baseline under a stated business cost, not merely a favorable pooled score.'),
    ('Submit a release packet', 'Deliver the input fixture, calendar manifest, feature-availability table, forecast ledger, backtest results and a short decision record. Include tests that change a future value without affecting earlier features, remove a seasonal source day and simulate a stale actual. Show how a prior model version can be restored. [[time-series/forecast-monitoring-and-retraining|Monitoring]] begins with that ledger.')],
    'def release_gate(candidate_mae, baseline_mae, candidate_bias, max_abs_bias):\n    if baseline_mae <= 0 or candidate_mae < 0 or max_abs_bias < 0:\n        raise ValueError("invalid evaluation metrics")\n    return {"candidate_beats_baseline": candidate_mae < baseline_mae,\n            "bias_within_limit": abs(candidate_bias) <= max_abs_bias}',
    'Generating O origins at H horizons creates O(OH) score records. A baseline is O(OH); fitted models add repeated training cost. Store one compact record per origin and horizon so an audit can reconstruct metrics without duplicating full datasets.',
    ['Do not fill an outage day with zero demand.', 'Do not select a model on the final evaluation period.', 'Do not ship a model without a baseline and rollback record.'],
    ['time-series/seasonal-naive-baseline','time-series/rolling-origin-backtest-and-gap','time-series/multi-horizon-errors-and-denominators','time-series/forecast-monitoring-and-retraining'])

assert len(lessons) == 16
assert len({item['path'] for item in lessons}) == len(lessons)
titles = {path: row['title'] for path, row in by_path.items()}
titles.update({item['path']: item['title'] for item in lessons})

def prose(value):
    return re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',
                  lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                  html.escape(value))

def links(paths):
    return '<ul>' + ''.join('<li><a href="/' + path + '">' + html.escape(titles[path]) + '</a></li>' for path in paths) + '</ul>'

def article_body(item):
    parts = ['<p>' + html.escape(item['summary']) + '</p>']
    for heading, paragraph in item['sections']:
        parts.extend(('<h2>' + html.escape(heading) + '</h2>', '<p>' + prose(paragraph) + '</p>'))
    parts.extend(('<h2>Implementation</h2>', '<pre><code class="language-python">' + html.escape(item['code']) + '</code></pre>',
                  '<h2>Performance and operating cost</h2>', '<p>' + html.escape(item['cost']) + '</p>',
                  '<h3>Common Mistakes</h3>', '<ul>' + ''.join('<li>' + html.escape(mistake) + '</li>' for mistake in item['mistakes']) + '</ul>',
                  '<h2>Read next</h2>', links(item['related'])))
    return ''.join(parts)

def make_row(path, title, summary, body, entry_type, subject, section_path, root_path, order, metadata):
    return dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://aitrove.in/' + path)), type=entry_type,
                path=path, title=title, summary=summary, body=body, category='AI & Data',
                subject=subject, difficulty='Intermediate', tags=['ai-data', subject], potd_date=None,
                featured=False, sort_order=order, status='published', published_at=stamp,
                created_at=stamp, updated_at=stamp,
                data={'subject_root':root_path, 'section_path':section_path,
                      'content_format':'html', 'seo_ready':True, **metadata})

subject_config = {
 'data-visualization': {
     'root':'data-visualization/data-visualization-tutorial', 'name':'Data Visualization',
     'summary':'Design auditable charts from explicit populations, stable scales, visible uncertainty and accessible representations.',
     'groups':[('Meaning and scale', ['chart-question-and-visual-encoding','aggregation-grain-and-denominator','scale-baseline-and-axis-integrity','distribution-and-outlier-displays']),
               ('Uncertainty and delivery', ['uncertainty-and-small-sample-display','accessible-color-and-text-alternatives','dashboard-filter-and-provenance'])],
     'project':'receipt-review-dashboard-project',
     'foundation':['data-science/data-science-for-beginners','applied-statistics/applied-statistics-tutorial']},
 'time-series': {
     'root':'time-series/time-series-tutorial', 'name':'Time Series',
     'summary':'Forecast ordered data with explicit calendars, causal features, baselines, rolling evaluation and release checks.',
     'groups':[('Observation and baselines', ['observation-calendar-and-missing-periods','lag-features-and-future-leakage','seasonal-naive-baseline']),
               ('Evaluation and operations', ['rolling-origin-backtest-and-gap','multi-horizon-errors-and-denominators','forecast-interval-and-calibration','forecast-monitoring-and-retraining'])],
     'project':'receipt-volume-forecast-project',
     'foundation':['data-engineering/data-engineering-tutorial','machine-learning/machine-learning-tutorial']},
}

for slug, config in subject_config.items():
    root_path = config['root']
    project_hub_path = root_path + '/project'
    titles[root_path] = config['name'] + ' Tutorial'
    titles[project_hub_path] = config['name'] + ': Projects'
    modules = [{'title':group_title, 'summary':'Read in order and run the failure checks.',
                'lessons':[slug + '/' + lesson_name for lesson_name in lesson_names]}
               for group_title, lesson_names in config['groups']]
    project_path = slug + '/' + config['project']
    modules.append({'title':'Apply your knowledge', 'lessons':[project_path]})
    all_paths = [path for module in modules for path in module['lessons']]
    tabs = [{'title':config['name'], 'path':root_path}, {'title':'Projects', 'path':project_hub_path}]
    hub_body = ('<p>' + html.escape(config['summary']) + '</p><h2>Learning path</h2>' + links(all_paths)
                + '<h2>Connected foundations</h2><p>Use the earlier data and model boundaries as prerequisites.</p>'
                + links(config['foundation']) + '<h2>Practice</h2>' + links([project_hub_path]))
    hub = make_row(root_path, titles[root_path], config['summary'], hub_body,
                   'subject', slug, root_path, root_path, 8500 if slug == 'data-visualization' else 8600,
                   {'modules':modules, 'resource_tabs':tabs})
    project_body = ('<p>Apply the ' + html.escape(config['name']) + ' curriculum to a checked project.</p>'
                    '<h2>Project brief</h2>' + links([project_path])
                    + '<h2>Required concepts</h2>' + links(all_paths[:-1])
                    + '<h2>Completion standard</h2><p>Submit runnable work, a data manifest, measured results and failure-case evidence.</p>')
    project_hub = make_row(project_hub_path, titles[project_hub_path],
                           'A checked project for the ' + config['name'] + ' curriculum.', project_body,
                           'subject', slug + '-project', project_hub_path, root_path,
                           8501 if slug == 'data-visualization' else 8601,
                           {'modules':[{'title':'Projects','lessons':[project_path]}], 'resource_tabs':tabs})
    rows.extend((hub, project_hub))
    by_path[root_path] = hub
    by_path[project_hub_path] = project_hub

for index, item in enumerate(lessons):
    slug = item['path'].split('/')[0]
    root_path = subject_config[slug]['root']
    is_project = item['path'].endswith('-project')
    section_path = root_path + '/project' if is_project else root_path
    body = article_body(item)
    article = make_row(item['path'], item['title'], item['summary'], body, 'article',
                       slug + '-project' if is_project else slug, section_path, root_path,
                       8700 + index,
                       {'kind':'project' if is_project else 'tutorial',
                        'reading_minutes':max(5, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                        'author_path':'authors/aitrove-editorial',
                        'verification_suite':'Editorial and syntax review; project inputs needed for runtime checks',
                        'related':[{'path':path,'title':titles[path]} for path in item['related']]})
    rows.append(article)
    by_path[item['path']] = article

for source, target in [
    ('data-science/metric-denominator-and-cohort','data-visualization/aggregation-grain-and-denominator'),
    ('applied-statistics/distribution-quantiles-and-outlier-policy','data-visualization/distribution-and-outlier-displays'),
    ('applied-statistics/confidence-interval-coverage','data-visualization/uncertainty-and-small-sample-display'),
    ('data-engineering/backfill-publication-boundary','data-visualization/dashboard-filter-and-provenance'),
    ('machine-learning/group-and-time-validation','time-series/rolling-origin-backtest-and-gap'),
    ('mlops/shadow-canary-and-rollback','time-series/forecast-monitoring-and-retraining'),
    ('data-science/missing-data-policy','time-series/observation-calendar-and-missing-periods'),
]:
    row = by_path[source]
    anchor = '<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in row['body']:
        row['body'] += anchor
        row['data']['related'].append({'path':target,'title':titles[target]})
        row['updated_at'] = stamp

assert len({row['path'] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_articles':len(lessons), 'new_subject_hubs':4, 'crosslinks_from_existing':7}))
