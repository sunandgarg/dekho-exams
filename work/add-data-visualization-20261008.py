"""Add eight Data Visualization tutorials and connect them to the track."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-data-visualization-import-20261008.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "data-visualization/"
hub = prefix + "data-visualization-tutorial"

lessons = [
    {
        "slug": "time-series-gaps-calendars-and-provisional-periods",
        "title": "Time-series charts: distinguish missing days, zeros and provisional periods",
        "summary": "Build a complete display calendar, preserve gaps, and label the clocks behind each point.",
        "sections": [
            ("A line implies continuity", "A time-series chart maps measurements to ordered instants or calendar periods. Connecting two observed points across an unobserved day implies a path that was never measured. A recorded zero is different: it says the instrument or process observed the period and counted none. Store both the period key and an observation-status field before drawing the line. [[time-series/observation-calendar-and-missing-periods|The observation calendar]] defines which periods were expected. Use a visible break, hollow mark, or separate missingness strip when a period has no measurement; do not silently replace it with zero."),
            ("Name the two clocks", "Operational data often has an event timestamp and a processing timestamp. A refund received late may belong to Tuesday's customer cohort but be visible only on Thursday's dashboard. Choose the clock that answers the chart's question and label it in the axis or subtitle. When bucketing timestamps into local days, choose one time zone and convert before taking the date. Daylight-saving changes make a local day shorter or longer than 24 hours in some regions. An elapsed-duration chart should use instants; a calendar-day chart should use dates in the declared zone."),
            ("Mark provisional periods", "A current day is incomplete even when its count is known so far. Drawing it with the same line and scale as closed days invites a false decline. Carry a finalized flag from the data source, and either exclude the open interval or render it with a different stroke and an explicit as-of time. [[data-engineering/watermark-retention-and-late-corrections|Late corrections]] can reopen an earlier point, so the chart's data-version label matters. A reader must know whether yesterday is final, not only whether the plotting job ran."),
            ("Protect the comparison", "Never join lines across a product outage, a changed population, or a denominator change without an annotation or split. Keep the y-axis unit and calculation stable across the displayed range. If one week contains 42, 47 and 51 eligible cases while the next has a different intake rule, raw counts compare different populations. [[data-visualization/aggregation-grain-and-denominator|The aggregation contract]] should produce both numerator and denominator where a rate is intended. A moving average may reduce noise, but its window, edge behavior and missing-day policy must be stated."),
            ("Check the drawn output", "Test an interior missing day, an observed zero, an incomplete final day, a late revision, and a daylight-saving boundary for the region being displayed. Confirm that hover text, downloadable data and the axis all use the same period key. A chart-library setting that connects nulls can undo a carefully prepared missingness contract. Inspect the rendered image, not only the input array. [[data-visualization/accessible-color-and-text-alternatives|The text alternative]] should report the gap and the as-of timestamp too."),
        ],
        "code": '''from datetime import date, timedelta

def complete_daily_series(observed: dict[date, int],
                          start: date, end: date) -> list[tuple[date, int | None]]:
    if end < start or any(count < 0 for count in observed.values()):
        raise ValueError("invalid date range or count")
    if any(day < start or day > end for day in observed):
        raise ValueError("observation outside display range")
    return [(start + timedelta(days=offset),
             observed.get(start + timedelta(days=offset)))
            for offset in range((end - start).days + 1)]

points = complete_daily_series(
    {date(2026, 8, 11): 47, date(2026, 8, 13): 0},
    date(2026, 8, 11), date(2026, 8, 13))
assert [count for _, count in points] == [47, None, 0]''',
        "cost": "For D expected periods and O observed keys, validation plus calendar completion takes O(D + O) time and O(D) output space. The code assumes an already chosen calendar zone and one authoritative count per day. Converting event timestamps and resolving duplicates belong upstream. For a long history, query only the visible interval, and keep finalization state beside each point; creating a million empty periods in a browser is a serving error, not a charting technique.",
        "mistakes": ["Converting an unobserved period into zero and drawing a continuous line.", "Bucketing by server time zone while labeling the axis with the user's local dates.", "Treating today's partial count as a completed daily value.", "Using a rolling average without showing its window and missing-period rule."],
        "drill": "Plot a 29-day refund series with one observed zero, two missing days and a provisional last day. Export the period keys and states, then verify that the line breaks only where observation is absent.",
        "related": [prefix + "aggregation-grain-and-denominator", prefix + "scale-baseline-and-axis-integrity", prefix + "dashboard-filter-and-provenance", "time-series/observation-calendar-and-missing-periods"],
    },
    {
        "slug": "scatterplot-overplotting-density-and-sampling-bias",
        "title": "Dense scatterplots: reveal overlap without hiding rare observations",
        "summary": "Use density cells and deliberate sampling when points overlap, while retaining the populations and exceptions that matter.",
        "sections": [
            ("Overplotting changes what a point means", "A scatterplot maps paired values to two position channels. When thousands of records land on the same pixels, the visible mark count no longer approximates the record count. Transparency can expose a dense center, but repeated strokes saturate and rare points can disappear beneath it. Before changing the mark style, count records per screen-space cell and inspect whether the question is about density, outliers, groups or exact cases. [[data-visualization/chart-question-and-visual-encoding|The chart question]] determines whether a point cloud is still the right view."),
            ("Bin at a declared resolution", "A two-dimensional density grid counts observations inside fixed x and y intervals. It can show population structure without rendering every dot. The cells need axis units, bounds and bin width; changing cell size changes the picture. A cell count is not a probability unless divided by the declared population or area. Use the same grid for comparisons across cohorts, otherwise apparent hot spots may be a change in binning. Preserve a drill-down path to the original records where access rules permit it. A heatmap of density has the same [[data-visualization/heatmap-missing-cells-and-color-domain|color-domain obligations]] as any other heatmap."),
            ("Sampling is a data product", "Uniform sampling can make a common cluster readable yet omit a rare but important failure mode. If the operational question concerns unusual refunds, retain those cases deliberately and label the sample design. A stratified sample can hold a fixed number from each category, but its plotted mix no longer reflects population proportions unless weights or counts are shown. Never present sampled points as the full dataset. Record the random seed, inclusion rule and population size. [[applied-statistics/population-estimand-and-sampling-frame|The sampling frame]] matters even when the result is only exploratory."),
            ("Separate trend from uncertainty", "A diagonal cloud does not by itself establish a causal effect. Outliers, groups and repeated measures can alter the apparent slope. Show marginal distributions or group facets when one cluster masks another. If a fitted trend is added, distinguish raw marks from the fitted line and state whether the fit is weighted, filtered or calculated on the visible sample. [[applied-statistics/regression-residuals-and-influence|Influence checks]] are needed before treating that line as a stable summary. A truncated axis can also make a weak relation seem strong."),
            ("Validate at the pixel budget", "Test identical coordinates, boundary points, non-finite values and a small rare cohort. Count how many records end in each visible density cell, then reconcile the total with the filtered input. Hovering a cell should report its count and ranges, not invent a single representative record. At high density, compare a grid and a sampled-point layer side by side: the grid describes mass, while the points retain individual exceptions. On a small screen, favor one readable layer over simultaneous translucent layers that obscure both."),
        ],
        "code": '''from math import floor, isfinite

def density_cells(points: list[tuple[float, float]],
                  x_bounds: tuple[float, float],
                  y_bounds: tuple[float, float],
                  columns: int, rows: int) -> dict[tuple[int, int], int]:
    x_low, x_high = x_bounds
    y_low, y_high = y_bounds
    if columns < 1 or rows < 1 or x_low >= x_high or y_low >= y_high:
        raise ValueError("invalid grid")
    counts: dict[tuple[int, int], int] = {}
    for amount, handling_minutes in points:
        if not all(map(isfinite, (amount, handling_minutes))):
            raise ValueError("non-finite observation")
        if not (x_low <= amount <= x_high and
                y_low <= handling_minutes <= y_high):
            raise ValueError("point outside declared domain")
        column = min(columns - 1, floor((amount - x_low) * columns / (x_high - x_low)))
        row = min(rows - 1, floor((handling_minutes - y_low) * rows / (y_high - y_low)))
        counts[(column, row)] = counts.get((column, row), 0) + 1
    return counts

cells = density_cells([(47, 18), (47, 18), (81, 39)],
                      (0, 100), (0, 50), 5, 5)
assert sum(cells.values()) == 3 and max(cells.values()) == 2''',
        "cost": "For N points and C occupied cells, fixed-grid counting takes O(N) time and O(C) memory, with C no larger than the number of grid positions. Rendering one rectangle per occupied cell can be much cheaper than rendering N circles. The example rejects out-of-domain points; a production view may instead maintain an explicit overflow bucket, but it must label that choice. Recompute bins when the axis domain or pixel resolution changes, and do not confuse screen-density counts with a probability density estimate.",
        "mistakes": ["Lowering opacity and assuming the visible marks still represent all records.", "Sampling rare cases away while evaluating an exception-handling workflow.", "Comparing density grids built with different bounds or cell widths.", "Calling a fitted slope causal based on a crowded scatterplot."],
        "drill": "Generate 4,700 routine handling cases plus 31 rare high-delay cases. Compare raw points, a fixed grid and a seeded stratified sample; report whether each view keeps the rare cluster visible and whether displayed counts reconcile.",
        "related": [prefix + "chart-question-and-visual-encoding", prefix + "heatmap-missing-cells-and-color-domain", prefix + "small-multiples-shared-scales-and-facet-order", "applied-statistics/regression-residuals-and-influence"],
    },
    {
        "slug": "small-multiples-shared-scales-and-facet-order",
        "title": "Small multiples: compare groups with honest scales and facet order",
        "summary": "Repeat one chart grammar across groups, then choose shared or local axes according to the intended comparison.",
        "sections": [
            ("A facet is a repeated measurement frame", "Small multiples split the same visual grammar into panels, one per group. They reduce line crossings and legend lookup when a single plot has too many series. The gain depends on consistency: each panel should use the same measure, time window, mark type and aggregation rule. A panel for customer tickets and a panel for revenue do not become comparable simply because they share a grid. [[data-visualization/aggregation-grain-and-denominator|Declare the measure]] before arranging panels. Keep a visible label on each panel; color alone is insufficient."),
            ("Shared scales answer magnitude questions", "If the reader needs to know which depot has the largest delay, a shared y-domain lets equal heights mean equal values. Local y-domains can make a low-volume depot's variation legible, but a steep line then no longer means a larger absolute change. If independent domains are necessary, print the local minimum and maximum in every panel and avoid a headline about cross-panel magnitude. [[data-visualization/scale-baseline-and-axis-integrity|Axis integrity]] applies to every facet. For percentages, a fixed zero-to-one domain is often an honest baseline; for residuals around zero, a symmetric domain may expose sign and spread better."),
            ("Keep the time window and missingness aligned", "Shared x-axes help readers distinguish a simultaneous event from a panel-specific shift. A region with no observations on Wednesday should show a gap, not compress its calendar so Thursday occupies Wednesday's position. When groups enter the system at different times, an aligned calendar makes the unequal exposure visible. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Time-series gap rules]] should be applied before faceting. If panels use different time windows by design, label them prominently and avoid visual comparison of positions."),
            ("Order panels for the task", "Alphabetical order is stable but often unhelpful when inspecting performance. Sorting by a predeclared baseline or current value can put high-risk groups first; automatic resorting on every hover makes the layout hard to track. Record the sort key and freeze it for an analysis session. Do not omit small groups without stating a threshold and the number omitted. [[data-visualization/uncertainty-and-small-sample-display|Small-sample uncertainty]] often explains why an apparently extreme panel should receive inspection rather than a confident ranking."),
            ("Budget the screen", "Thirty tiny panels may be technically complete yet unreadable on a phone. Allow searching or paging through stable groups while keeping the same scale contract. A summary panel can show the total or reference band, but it must follow the same population rules. Test keyboard order and screen-reader panel labels. If each facet needs a unique tooltip, interaction cost grows with the number of panels; prioritize a simple data table for exact values. A chart grid should make comparisons easier, not force the reader to memorize dozens of legends."),
        ],
        "code": '''from math import isfinite

def facet_domains(series: dict[str, list[float]],
                  shared: bool) -> dict[str, tuple[float, float]]:
    if not series or any(not values for values in series.values()):
        raise ValueError("each facet needs observed values")
    if any(not isfinite(value) for values in series.values() for value in values):
        raise ValueError("non-finite plotted value")
    if shared:
        values = [value for group in series.values() for value in group]
        domain = (min(values), max(values))
        return {name: domain for name in series}
    return {name: (min(values), max(values)) for name, values in series.items()}

depot_delays = {"north": [18, 47], "south": [3, 8]}
assert facet_domains(depot_delays, True)["south"] == (3, 47)
assert facet_domains(depot_delays, False)["south"] == (3, 8)''',
        "cost": "For N values across G groups, scanning domains takes O(N + G) time. The shared branch stores an extra O(N) flattened list for clarity; a streaming minimum and maximum reduce that auxiliary memory to O(1), while the returned G domains still need O(G) space. Rendering cost scales with both the number of panels and marks. A UI that rerenders every facet after each filter may become slow even when the domain calculation is cheap; memoize by the complete filter and data-version key only when measurements justify it.",
        "mistakes": ["Using independent y-domains while claiming one group has the larger magnitude.", "Dropping missing dates and shifting one panel's x positions relative to the rest.", "Reordering facets during interaction without labeling the sort key.", "Suppressing tiny cohorts without reporting how many groups were hidden."],
        "drill": "Facet five depot delay series on one weekly calendar. Produce a shared-scale view for absolute comparison and a labeled independent-scale view for within-depot variation; write down which conclusions differ.",
        "related": [prefix + "scale-baseline-and-axis-integrity", prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "uncertainty-and-small-sample-display", prefix + "accessible-color-and-text-alternatives"],
    },
    {
        "slug": "heatmap-missing-cells-and-color-domain",
        "title": "Heatmaps: make missing cells, rates and color domains explicit",
        "summary": "Construct a complete matrix and keep unmeasured cells separate from zero-valued measurements.",
        "sections": [
            ("A cell needs two keys and one measure", "A heatmap is a matrix of marks whose position comes from two discrete dimensions and whose fill encodes a value. The first decision is the unit of a cell: one depot-day, one product-hour, or one model-class pair. Build the complete expected key grid before coloring it. Otherwise an absent record disappears, compresses the layout, or is mistaken for a low value. A white cell may mean zero, unobserved, unavailable or suppressed; these states require separate labels or patterns. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Calendar completeness]] matters when columns are days."),
            ("Rates need their denominators", "A defect-rate cell with 4 defects in 8 inspections and another with 40 in 800 inspections should not be interpreted as equally reliable even if their colors reflect 50% and 5%. Carry inspected count into a tooltip, visible annotation, or companion display. If no inspections occurred, the rate is undefined rather than zero. [[data-visualization/aggregation-grain-and-denominator|Measure grain]] determines whether the numerator and denominator belong to the same cell. If filters remove rows, recompute both counts instead of averaging precomputed cell percentages."),
            ("Fix the color domain for comparison", "An automatically rescaled palette can make the same value change color when the viewer filters a subset. For cross-filter or before-after comparisons, set a stable domain and show its endpoints. A sequential palette fits a nonnegative rate; a diverging palette needs a meaningful center such as zero difference or target variance. Quantile coloring gives bins with similar record counts, not equal numeric widths. Label the bin rule. [[data-visualization/accessible-color-and-text-alternatives|Accessible encodings]] add text or pattern cues so the chart still works without color."),
            ("Choose ordering deliberately", "Alphabetical row order is reproducible, but ordering by a stable baseline can expose patterns. Clustering rows by similarity can reveal structure yet change the question: adjacent rows no longer imply geographic or operational proximity. If an algorithm orders rows, record its input period and freeze the order for comparisons. Keep hidden categories and totals visible. A truncated matrix that shows only the busiest depots is a selected population, not the entire network. [[data-visualization/small-multiples-shared-scales-and-facet-order|Facet-order discipline]] applies here too."),
            ("Test the matrix contract", "Include an observed zero, a missing key, a present key with zero exposure, an invalid negative count and a high-rate low-volume cell. Confirm each has a distinct state. Check the matrix against a long-form data table with the same row and column order. On mobile, provide axis labels that remain visible while scrolling; a distant legend is not enough. Exported CSV should retain status, numerator and denominator rather than only a color code."),
        ],
        "code": '''def inspection_matrix(
    observations: dict[tuple[str, str], tuple[int, int]],
    depots: list[str], days: list[str]
) -> dict[tuple[str, str], tuple[str, float | None, int | None]]:
    expected = {(depot, day) for depot in depots for day in days}
    if len(expected) != len(depots) * len(days) or set(observations) - expected:
        raise ValueError("duplicate labels or unexpected cell")
    grid = {}
    for key in expected:
        if key not in observations:
            grid[key] = ("missing", None, None)
            continue
        defects, inspected = observations[key]
        if not 0 <= defects <= inspected:
            raise ValueError("invalid cell counts")
        grid[key] = ("no-exposure", None, 0) if inspected == 0 else (
            "observed", defects / inspected, inspected)
    return grid

matrix = inspection_matrix(
    {("north", "Mon"): (0, 47), ("north", "Tue"): (0, 0)},
    ["north"], ["Mon", "Tue", "Wed"])
assert matrix[("north", "Mon")] == ("observed", 0.0, 47)
assert matrix[("north", "Tue")][0] == "no-exposure"
assert matrix[("north", "Wed")][0] == "missing"''',
        "cost": "For R row labels, C column labels and M supplied observations, building the expected grid takes O(RC + M) time and O(RC) space. Large sparse matrices should keep sparse storage and generate only visible tiles, but must still represent missing cells and axis positions correctly. The demonstration returns status, rate and denominator; a production export should also retain the numerator and source snapshot. Color scaling and rendering add work proportional to visible cells, not merely to supplied observations.",
        "mistakes": ["Assigning the same white fill to an observed zero and an absent cell.", "Changing the color domain after filtering without warning the reader.", "Averaging cell percentages instead of recomputing counts for a new group.", "Sorting rows by one selected day, then describing the layout as a stable geographic order."],
        "drill": "Build a depot-by-day inspection matrix with 6 depots and 17 days. Insert one missing cell, one zero-exposure cell and one observed zero. Verify their states in both chart legend and exported data.",
        "related": [prefix + "aggregation-grain-and-denominator", prefix + "accessible-color-and-text-alternatives", prefix + "scatterplot-overplotting-density-and-sampling-bias", prefix + "dashboard-filter-and-provenance"],
    },
    {
        "slug": "choropleth-rates-boundaries-and-missing-regions",
        "title": "Choropleth maps: normalize counts and audit boundary coverage",
        "summary": "Join measures to the right polygons, use a stated denominator, and distinguish unmapped places from zero-valued regions.",
        "sections": [
            ("Area color is not an event count", "A choropleth fills geographic regions according to a measure. Large polygons occupy more pixels and can dominate attention even when they contain few people or events. Raw incident counts often track exposure, such as population or active deliveries, more than risk. For a comparable rate, carry numerator and denominator for each polygon and specify the period. [[applied-statistics/poisson-count-rate-and-exposure|Exposure-based rates]] explain why 8 incidents across 47,000 trips differ from 8 across 470 trips. A map can still show counts when workload is the question; label it as a count map."),
            ("Join by stable region identity", "Names drift, abbreviations collide, and administrative boundaries change. Join facts to geometry with stable region IDs and a boundary version. Report unmatched fact IDs, polygons with no measure, duplicate assignments and overlapping boundaries before rendering. [[geospatial-analytics/geometry-validation-and-spatial-joins|Spatial joins]] are a separate operation from coloring polygons; they can duplicate a record if geometries overlap. If one region splits midyear, a before-after map needs a common boundary basis or an explicit break. Do not let a chart library silently drop unmatched regions."),
            ("Projection and extent shape perception", "A projection transforms coordinates into map space. It can distort area, shape or distance; no flat map preserves everything. For regional comparison, keep the same projection, extent and viewport across panels, and avoid interpreting the visible area of a polygon as its population. Insets for distant regions need clear labels and scale context. If exact comparison of rates matters more than location, provide a sorted bar chart alongside the map. [[data-visualization/chart-question-and-visual-encoding|Choose the visual]] that serves the question, not merely the available geometry."),
            ("Class breaks are an editorial decision", "Equal-width bins, quantile bins and fixed policy thresholds answer different questions. A quantile palette can assign different colors to tiny numeric differences when many regions cluster tightly; fixed thresholds can leave some colors unused. Print numeric breakpoints and keep them stable when comparing dates. Use a separate treatment for missing data and low-exposure suppression. [[data-visualization/heatmap-missing-cells-and-color-domain|Color-domain rules]] carry over to map legends. Keep the original rate in the accessible table and tooltip; color bins are a summary, not the data."),
            ("Protect sensitive locations", "Very small denominators can make rates unstable and expose information about a few people or facilities. Define a minimum publishable group size, aggregate or suppress as appropriate, and show a visible suppressed state. Do not infer that a blank region has zero risk. [[geospatial-analytics/aggregation-and-location-privacy|Location privacy]] and [[data-visualization/uncertainty-and-small-sample-display|small-sample display]] belong to the same release review. Test a region with no geometry, a polygon with no observation, a zero numerator and a zero denominator separately."),
        ],
        "code": '''def regional_rates(
    boundary_ids: set[str],
    incident_counts: dict[str, tuple[int, int]]
) -> dict[str, tuple[str, float | None]]:
    unknown = set(incident_counts) - boundary_ids
    if unknown:
        raise ValueError(f"facts without geometry: {sorted(unknown)}")
    result = {}
    for region_id in boundary_ids:
        if region_id not in incident_counts:
            result[region_id] = ("missing", None)
            continue
        incidents, trips = incident_counts[region_id]
        if not 0 <= incidents <= trips:
            raise ValueError("invalid regional counts")
        result[region_id] = ("no-exposure", None) if trips == 0 else (
            "observed", incidents / trips)
    return result

rates = regional_rates({"zone-47", "zone-81", "zone-94"},
                       {"zone-47": (8, 470), "zone-81": (0, 81)})
assert rates["zone-47"][1] == 8 / 470
assert rates["zone-81"] == ("observed", 0.0)
assert rates["zone-94"] == ("missing", None)''',
        "cost": "For B boundary IDs and M measured regions, this join-and-rate check takes O(B + M) expected time and O(B) output space using hash sets. Rendering cost depends on polygon vertex count, projection and viewport clipping, none of which this code performs. Simplify geometry only to a documented tolerance and keep an exact source for hit tests. A cached tile or geometry file must carry the same boundary version as the measures. The code distinguishes zero and missing; a real publication layer also enforces suppression and uncertainty policy.",
        "mistakes": ["Coloring raw counts as if the map showed per-person or per-trip risk.", "Joining on human-readable region names without checking unmatched and duplicated keys.", "Treating a missing polygon or missing measure as zero.", "Changing map bounds or class breaks between comparison dates."],
        "drill": "Map 23 service zones with one split boundary, one missing measure and one zone below the publishable exposure threshold. Reconcile region IDs and rates before drawing polygons; add a sorted rate table for exact comparison.",
        "related": [prefix + "heatmap-missing-cells-and-color-domain", prefix + "uncertainty-and-small-sample-display", "geospatial-analytics/geometry-validation-and-spatial-joins", "geospatial-analytics/aggregation-and-location-privacy"],
    },
    {
        "slug": "linked-filters-cohort-denominators-and-selection-state",
        "title": "Interactive dashboards: recompute cohorts after linked filters",
        "summary": "Make selections compose predictably, recalculate numerators and denominators, and expose the active state.",
        "sections": [
            ("A selection changes the population", "Linked filtering lets a selection in one view constrain another. Clicking a depot, brushing a date range or choosing a channel changes the cohort behind every plotted metric. The interaction contract must specify whether filters combine with AND or OR, whether a second click toggles, and whether an empty selection means all or none. Show active filters in text and offer a clear reset. [[data-visualization/dashboard-filter-and-provenance|Dashboard provenance]] needs the same filter state that the user sees; otherwise a shared screenshot cannot be reproduced."),
            ("Recompute base counts", "A precomputed overall completion percentage cannot simply be filtered and averaged. Reapply the filter to eligible records, then sum timely and eligible counts for the selected cohort. If a record appears in both a status log and an order table, deduplicate to the declared unit before counting. [[data-visualization/aggregation-grain-and-denominator|Grain and denominator rules]] are the invariant under interaction. A filtered group with zero eligible records should display an undefined rate and zero denominator, not a zero-percent success rate."),
            ("Synchronize every view", "When a brush narrows a chart, its companion count, data table, map and export must use the same selected IDs or query predicate. Some dashboards filter the marks but leave the headline KPI unfiltered; users then compare incompatible populations. Carry one normalized state object and one data-version token into each query. If a backend response arrives after the user changes filters again, discard the stale response instead of replacing a newer view. A request ID or abort signal can enforce this. [[data-visualization/large-series-level-of-detail-and-extrema|Large-series rendering]] may be approximate, but filter semantics must remain exact."),
            ("Make selection discoverable and reversible", "Hover-only behavior hides controls from touch and keyboard users. Provide visible filter chips, keyboard-operable controls, focus cues and a readable selection summary. Color should not be the sole indication of selected marks. A reset should restore the documented default and preserve the date or snapshot policy, not silently switch to today's data. [[data-visualization/accessible-color-and-text-alternatives|Accessible chart controls]] include data values outside the plotted canvas. Keep the browser back button or a shareable query state when deep analysis paths matter."),
            ("Test the state machine", "Exercise no filters, one filter, two intersecting filters, mutually exclusive filters, a zero-eligible result, and rapid filter changes. Compare chart, KPI and export row counts for each state. For a selected region and channel, check that removing one chip broadens the cohort only along that dimension. Record the expected query predicate alongside a screenshot in a release test. If the chart is based on sampled or aggregated data, do not use a pixel brush to imply record-level exactness unless the backend can resolve it."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class ReviewRecord:
    receipt_id: str
    region: str
    channel: str
    eligible: bool
    timely: bool

def filtered_completion(records: list[ReviewRecord],
                        regions: set[str], channels: set[str]
                        ) -> tuple[int, int, float | None]:
    if len({record.receipt_id for record in records}) != len(records):
        raise ValueError("duplicate receipt identity")
    selected = [record for record in records
                if (not regions or record.region in regions)
                and (not channels or record.channel in channels)
                and record.eligible]
    if any(record.timely and not record.eligible for record in records):
        raise ValueError("timely receipt cannot be ineligible")
    timely = sum(record.timely for record in selected)
    eligible = len(selected)
    return timely, eligible, timely / eligible if eligible else None

receipts = [ReviewRecord("r-47", "north", "web", True, True),
            ReviewRecord("r-81", "north", "store", True, False),
            ReviewRecord("r-94", "south", "web", True, True)]
assert filtered_completion(receipts, {"north"}, {"web"}) == (1, 1, 1.0)
assert filtered_completion(receipts, {"south"}, {"store"}) == (0, 0, None)''',
        "cost": "For N records, duplicate validation and filtering take O(N) expected time and O(N) temporary space in this direct version; the selected list can be avoided with streaming counters to use O(N) identity state and O(1) additional cohort state. For a remote dashboard, query cost and transfer volume usually dominate. Cache only by normalized filters, authorization context and data version. Never reuse a cached result across tenants or revisions merely because the visible filter chips match.",
        "mistakes": ["Filtering colored marks while leaving headline metrics on the full population.", "Averaging cached percentages after a filter instead of summing base counts.", "Treating an empty cohort as a measured zero-percent rate.", "Letting an older network response overwrite the result of a newer selection."],
        "drill": "Connect a weekly trend, region bar chart and completion KPI. Test six filter states and verify the same eligible count in the chart tooltip, KPI, table and CSV export for each state.",
        "related": [prefix + "dashboard-filter-and-provenance", prefix + "aggregation-grain-and-denominator", prefix + "accessible-color-and-text-alternatives", prefix + "chart-export-manifest-data-and-render-version"],
    },
    {
        "slug": "large-series-level-of-detail-and-extrema",
        "title": "Large chart series: reduce marks without erasing spikes",
        "summary": "Choose a visible-resolution data product and preserve first, last, minimum and maximum values in each bucket.",
        "sections": [
            ("More samples than pixels need a display rule", "A line chart with hundreds of thousands of readings across a 900-pixel plot cannot show each reading distinctly. Sending every point still costs transfer, parsing, memory, layout and interaction time. A random sample or every-50th-point stride can erase a brief but operationally important spike. Decide whether the reader is inspecting shape, extrema, exact intervals or anomalies. [[data-visualization/chart-question-and-visual-encoding|The chart task]] determines the reduction method. The full-resolution data remains the source; the plotted series is a deliberately derived view."),
            ("Preserve a bounded envelope", "For each time bucket, retain its first, last, minimum and maximum observations, ordered by timestamp and deduplicated by identity. This keeps endpoints connected and exposes local peaks and troughs that a mean would smooth away. It is not lossless: the order of several internal turns and narrow oscillations may still be compressed. Show the bucket width or resolution when it affects interpretation, and fetch raw samples on zoom or request. If missing intervals exist, split segments before reducing; joining across a gap creates a fictional line. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Gap policy]] applies before level of detail."),
            ("Build levels against stable data versions", "Precomputed hourly, daily or pixel-width buckets must use a fixed time origin and a named aggregation function. If a late event revises an old bucket, invalidate that level together with raw data. Cache keys need range, resolution, filters, unit and source generation. A multi-resolution chart can request a coarser level during pan, then replace it with fine points after the interaction settles; label provisional rendering when it might change a decision. [[data-engineering/serving-index-and-freshness-contract|Serving freshness]] constrains what a pre-aggregated chart can claim."),
            ("Keep exactness available", "Tooltips on reduced marks should describe the bucket, extrema and sample count. Calling a retained minimum a point-in-time average is wrong. A downloadable CSV should offer the filtered raw interval or clearly name the reduced level. If a user clicks a peak to investigate a machine stoppage, resolve it to source IDs rather than an arbitrary nearby display point. [[data-visualization/chart-export-manifest-data-and-render-version|The export manifest]] should state whether the series is raw or reduced."),
            ("Measure end-to-end cost", "Track transfer bytes, parse time, memory, first paint, pan latency and number of marks actually drawn. A server-side envelope can reduce browser work but adds query and cache-maintenance cost. A canvas renderer can draw many marks faster than DOM-based SVG, yet it needs deliberate keyboard and text alternatives. Test a single-sample range, identical timestamps, gaps and a narrow spike at each bucket boundary. The acceptance check is not only a speedup: the operational alert must remain visible at the default zoom."),
        ],
        "code": '''def extrema_envelope(samples: list[tuple[int, float]],
                     bucket_size: int) -> list[tuple[int, float]]:
    if bucket_size < 1 or any(samples[index][0] >= samples[index + 1][0]
                               for index in range(len(samples) - 1)):
        raise ValueError("bucket size or time order is invalid")
    reduced = []
    for start in range(0, len(samples), bucket_size):
        bucket = samples[start:start + bucket_size]
        selected = {bucket[0], bucket[-1],
                    min(bucket, key=lambda point: point[1]),
                    max(bucket, key=lambda point: point[1])}
        reduced.extend(sorted(selected, key=lambda point: point[0]))
    return reduced

readings = [(47, 4.0), (48, 4.1), (49, 81.0), (50, 4.2),
            (51, 4.0), (52, 3.9)]
visible = extrema_envelope(readings, 4)
assert (49, 81.0) in visible and visible[0] == readings[0]
assert len(visible) <= 4 * ((len(readings) + 3) // 4)''',
        "cost": "For N sorted samples and bucket size B, the demonstration runs in O(N + (N/B) log 4) time and emits at most four observations per bucket, O(N/B) output space. Python slices hold up to O(B) temporary items. It assumes strictly increasing timestamps and one continuous segment; production data with same-time events needs an explicit tie policy, and gaps need separate segments. Maintaining a pyramid of levels increases storage but can make viewport requests proportional to visible resolution rather than total history.",
        "mistakes": ["Taking every nth reading and deleting a short-lived alarm spike.", "Reducing across a missing-data gap and drawing a continuous line.", "Calling a retained minimum or maximum a bucket average.", "Caching a reduced level without the filter and source-version keys."],
        "drill": "Reduce a 47,000-point sensor series to a 900-pixel view. Insert 19 one-point spikes at varied bucket positions and verify every spike survives the chosen display reduction; compare load and pan times with the raw series.",
        "related": [prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "linked-filters-cohort-denominators-and-selection-state", prefix + "chart-export-manifest-data-and-render-version", "data-engineering/serving-index-and-freshness-contract"],
    },
    {
        "slug": "chart-export-manifest-data-and-render-version",
        "title": "Chart exports: carry the data, filters and render contract together",
        "summary": "Give exported images an auditable data table and a compact manifest of the choices that produced them.",
        "sections": [
            ("An image is not the full evidence", "A PNG captures pixels; it does not preserve the records, filter predicates, missingness states or exact values behind them. SVG retains scalable geometry, but it can still omit the underlying analytical contract. For a decision-grade chart, export an image, a machine-readable table of plotted values and a manifest describing the query and rendering choices. The package should answer which source snapshot, cohort, units, time zone, grouping rule, axis domain, palette and code version produced the picture. [[data-visualization/dashboard-filter-and-provenance|Dashboard provenance]] supplies these ingredients; export binds them to an artifact."),
            ("Version the plotted data product", "A chart may use raw events, daily aggregates or a reduced display level. The export must name that level. Include a dataset snapshot or immutable revision, plus the report's as-of time when corrections are possible. A hash of canonical manifest bytes detects accidental changes to the manifest; it does not authenticate a source by itself. If integrity across systems matters, sign the package through a trusted release path. Never include private identifiers or unmasked rows merely because a chart view was authorized. [[data-engineering/data-classification-and-access-boundaries|Data classification]] still governs exports."),
            ("Keep visible and downloadable values aligned", "The CSV or JSON table must use the same filters, denominator, sort, unit and missing-value policy as the displayed chart. If the chart shows rounded percentages, include underlying counts and unrounded rates in the data export while documenting the display rounding. A tooltip, table and image title should agree on the period and finalization status. [[data-visualization/linked-filters-cohort-denominators-and-selection-state|Linked filters]] can change the cohort moments before a user clicks export; capture one state and one data version atomically for the whole package."),
            ("Make the visual portable and accessible", "An SVG is useful for vector editing and high-resolution print, but font substitution and external styles can change its appearance. A PNG is more predictable but loses scale and selectable text. Include an accessible text summary and data table in either case. Document the output size, color profile where relevant, and the scale tick labels. [[data-visualization/accessible-color-and-text-alternatives|Text alternatives]] should describe the main pattern, notable exceptions and uncertainty rather than repeat a generic chart title. For a public download, test that no hidden private series remain in SVG markup or embedded metadata."),
            ("Recreate before release", "Re-run the export from its manifest in a clean environment. Compare plotted counts, axis limits, filters, title, source generation and checksum, allowing only declared rendering differences such as font rasterization. A changed query definition should make an old package non-reproducible by design; report that conflict instead of silently rendering with today's code. Keep an editorial preview for review, then publish an immutable artifact reference when the chart is used in a report or audit. [[data-visualization/large-series-level-of-detail-and-extrema|Reduced series]] need the level and bucket rule in the manifest."),
        ],
        "code": '''import hashlib
import json

def chart_manifest(query_id: str, dataset_version: str,
                   filters: dict[str, list[str]],
                   axis_domain: tuple[float, float],
                   plotted_rows: int) -> tuple[dict, str]:
    if not query_id or not dataset_version or plotted_rows < 0:
        raise ValueError("missing chart identity")
    if axis_domain[0] >= axis_domain[1]:
        raise ValueError("invalid axis domain")
    manifest = {
        "query_id": query_id,
        "dataset_version": dataset_version,
        "filters": {key: sorted(set(values))
                    for key, values in sorted(filters.items())},
        "y_axis_domain": list(axis_domain),
        "plotted_rows": plotted_rows,
        "unit": "minutes",
        "render_contract": "depot-delay-v3",
    }
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    return manifest, hashlib.sha256(payload).hexdigest()

first = chart_manifest("depot-delay-week", "snapshot-81",
                       {"region": ["north", "north"]}, (0, 47), 31)
second = chart_manifest("depot-delay-week", "snapshot-81",
                        {"region": ["north"]}, (0, 47), 31)
assert first == second and len(first[1]) == 64''',
        "cost": "For F total filter values and M serialized manifest bytes, sorting normalized filters costs O(F log F) in the worst case; JSON encoding and SHA-256 hashing take O(M) time and O(M) temporary memory. Exporting an image or plotted data can cost much more and depends on the renderer and row count. This hash identifies equal manifest bytes, not equal pixels or trustworthy provenance. Add a data-file checksum and a signed release record when the export package crosses a trust boundary.",
        "mistakes": ["Publishing only a screenshot when reviewers need the plotted data and cohort definition.", "Exporting a CSV from a stale filter state while the chart shows a newer selection.", "Assuming a manifest hash proves who created the data.", "Embedding hidden private rows in an otherwise public SVG or HTML export."],
        "drill": "Export one filtered depot-delay chart as SVG and CSV with a manifest. Change only the filter and verify the manifest digest changes, then rebuild the original chart from its saved version and compare counts and axis bounds.",
        "related": [prefix + "dashboard-filter-and-provenance", prefix + "linked-filters-cohort-denominators-and-selection-state", prefix + "accessible-color-and-text-alternatives", prefix + "large-series-level-of-detail-and-extrema"],
    },
]

new_paths = [prefix + lesson["slug"] for lesson in lessons]
assert len(new_paths) == len(set(new_paths))
assert not set(new_paths) & by_path.keys()
titles = {path: row["title"] for path, row in by_path.items()}
titles.update(zip(new_paths, (lesson["title"] for lesson in lessons)))
marker = re.compile(r"\[\[([^|\]]+)\|([^\]]+)\]\]")

def render(value: str) -> str:
    pieces = []
    start = 0
    for match in marker.finditer(value):
        pieces.append(html.escape(value[start:match.start()]))
        path, label = match.groups()
        if path not in titles:
            raise ValueError(f"broken link: {path}")
        pieces.append(f'<a href="/{html.escape(path, quote=True)}">{html.escape(label)}</a>')
        start = match.end()
    return "".join(pieces) + html.escape(value[start:])

def link(path: str) -> str:
    if path not in titles:
        raise ValueError(f"broken related link: {path}")
    return f'<a href="/{html.escape(path, quote=True)}">{html.escape(titles[path])}</a>'

def body_for(lesson: dict) -> str:
    body = f'<p>{render(lesson["summary"])}</p>'
    for heading, paragraph in lesson["sections"]:
        body += f'<h2>{html.escape(heading)}</h2><p>{render(paragraph)}</p>'
    body += '<h2>Worked contract</h2><pre><code class="language-python">' + html.escape(lesson["code"]) + '</code></pre>'
    body += '<h2>Performance and operating cost</h2><p>' + render(lesson["cost"]) + '</p>'
    body += '<h3>Common Mistakes</h3><ul>' + ''.join(f'<li>{render(item)}</li>' for item in lesson["mistakes"]) + '</ul>'
    body += '<h2>Validation drill</h2><p>' + render(lesson["drill"]) + '</p>'
    body += '<h2>Read next</h2><ul>' + ''.join(f'<li>{link(path)}</li>' for path in lesson["related"]) + '</ul>'
    return body

changed = []
for offset, lesson in enumerate(lessons):
    path = new_paths[offset]
    body = body_for(lesson)
    row = {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
        "type": "article", "path": path, "title": lesson["title"],
        "summary": lesson["summary"], "body": body, "category": "AI & Data",
        "subject": "data-visualization", "difficulty": "Advanced",
        "tags": ["ai-data", "data-visualization", "tutorial"], "potd_date": None,
        "featured": False, "sort_order": 8708 + offset, "status": "published",
        "published_at": stamp, "created_at": stamp, "updated_at": stamp,
        "data": {"subject_root": hub, "section_path": hub,
                 "content_format": "html", "seo_ready": True, "kind": "tutorial",
                 "reading_minutes": max(6, round(len(re.sub('<[^>]+>', ' ', body).split()) / 180)),
                 "author_path": "authors/aitrove-editorial",
                 "verification_suite": "Executable standard-library example and editorial review",
                 "related": [{"path": target, "title": titles[target]}
                             for target in lesson["related"]]},
    }
    rows.append(row)
    by_path[path] = row
    changed.append(row)

for path in (hub, "data-visualization"):
    row = by_path[path]
    for start, heading in ((0, "Time, density, facets and matrices"),
                           (4, "Maps, interaction, scale and exports")):
        targets = new_paths[start:start + 4]
        row["data"]["modules"].append({"title": heading, "lessons": targets})
        row["body"] += f'<h2>{heading}</h2><ul>' + ''.join(
            f'<li>{link(target)}</li>' for target in targets) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "aggregation-grain-and-denominator": [new_paths[0], new_paths[3], new_paths[5]],
    prefix + "distribution-and-outlier-displays": [new_paths[1]],
    prefix + "scale-baseline-and-axis-integrity": [new_paths[2], new_paths[4]],
    prefix + "accessible-color-and-text-alternatives": [new_paths[3], new_paths[7]],
    prefix + "dashboard-filter-and-provenance": [new_paths[5], new_paths[7]],
    prefix + "uncertainty-and-small-sample-display": [new_paths[4]],
    prefix + "receipt-review-dashboard-project": [new_paths[5], new_paths[6]],
}
for source, targets in incoming.items():
    row = by_path[source]
    row["body"] += '<h2>Continue this visualization path</h2><ul>' + ''.join(
        f'<li>{link(target)}</li>' for target in targets) + '</ul>'
    related = row["data"].setdefault("related", [])
    known = {value["path"] for value in related}
    related.extend({"path": target, "title": titles[target]}
                   for target in targets if target not in known)
    row["updated_at"] = stamp
    changed.append(row)

assert len(rows) == len({row["path"] for row in rows})
changed = list({row["path"]: row for row in changed}.values())
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
packet.write_text(json.dumps(changed, ensure_ascii=False, indent=2) + "\n")
print(f"Added {len(lessons)} lessons; publication packet has {len(changed)} entries: {packet}")
