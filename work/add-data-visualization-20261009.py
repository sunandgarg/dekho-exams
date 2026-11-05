"""Publish lag-plot and embedding-audit lessons for Data Visualization."""
from data_visualization_batch import publish

prefix = "data-visualization/"
lessons = [
    {
        "slug": "lag-plots-calendar-pairs-missing-periods-and-trend-confounding",
        "title": "Lag plots: pair exact periods before reading dependence",
        "summary": "Plot a series against its earlier values with a declared calendar, pair count and missing-period policy; separate serial dependence from a shared trend.",
        "sections": [
            ("Define the pair, not just the shift", "A lag plot is a scatterplot of one series against itself at a fixed time offset. For lag 2, a mark might place a service's latency in week 47 on X and latency in week 49 on Y. The mark represents that ordered pair, not two independent records. A diagonal cloud may indicate persistence; a curve or alternating bands may expose nonlinear or periodic behavior. Neither shape proves a forecasting relationship. Name the measurement, its units, the calendar and the direction of the shift in the title or caption. State whether X is the earlier value, as it is here, because swapping axes changes the story a reader tells about high and low values. A lag plot answers a different question from [[data-visualization/autocorrelation-plots-regular-lags-pair-counts-and-seasonality|autocorrelation]], which reduces the paired values at each lag to a summary coefficient. The scatter keeps outliers and nonlinear shapes visible."),
            ("Use clock distance rather than row distance", "A two-row shift is only a two-week lag when every row stands for exactly one week. If the export skips week 49, pairing the rows for weeks 48 and 50 as if they were adjacent creates a false lag-one mark. Key observations by a normalized period identifier, reject duplicate periods, and look up the target by adding the declared lag. A blank measurement stays blank. Do not replace it with zero just to keep the plot dense. The worked contract accepts consecutive integer period IDs; a calendar with fiscal exceptions needs a separate, explicit successor table. For daily timestamps, settle the time zone and daylight-saving policy before deriving the period ID. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Calendar gaps]], [[data-visualization/event-aligned-time-series-baseline-windows-and-missing-periods|event alignment]] and [[data-visualization/missingness-matrices-record-order-patterns-and-co-missing-fields|missingness diagnostics]] provide the surrounding audit trail."),
            ("Publish the denominator and the missing-pair ledger", "A plot with 83 points can look stable while half the intended periods vanished. Count all possible starts between the observed first and last period for the chosen lag, then report how many produced finite pairs. The omitted count includes a missing earlier period, a missing later period, or both; classify the reason separately if it affects the operational decision. The example constructs pairs by keyed lookup rather than materializing every period in a very sparse calendar. That makes its runtime depend on observed records, while the denominator still reflects the declared span. If a series has separate operating regimes, color by a predeclared regime or make small multiples with identical axes. Do not compute one overall trend line across a known sensor replacement. [[data-visualization/small-multiples-shared-scales-and-facet-order|Small multiples]] and [[data-visualization/scatterplot-regression-overlays-fit-scope-and-prediction-bands|fit-scope rules]] make that split inspectable."),
            ("Check whether the shape survives detrending", "Two adjacent values can line up along a diagonal simply because both rise over a long interval. That is not the same as a stable short-run dependency. Examine the original time plot, a differenced or detrended view when the analytical question calls for it, and at least one nearby lag. Keep the preprocessing contract attached to every panel. A seasonal process may create a strong lag at the cycle length even when the lag-one plot looks diffuse. Points can overlap, so opacity, hexbin counts or a marginal density may help without replacing the underlying pair count. Use symmetric numeric limits when the same unit appears on both axes; the identity line then has a literal equality meaning. [[data-visualization/hexbin-density-grid-resolution-and-exposure|Hexbin exposure]], [[data-visualization/scale-baseline-and-axis-integrity|axis integrity]] and [[data-visualization/connected-scatterplots-time-order-gaps-and-trajectory-reading|ordered trajectories]] solve different reading problems."),
        ],
        "code": '''from math import isfinite

def latency_lag_pairs(readings: list[tuple[int, float | None]], lag: int):
    if not isinstance(lag, int) or isinstance(lag, bool) or lag < 1:
        raise ValueError("lag must be a positive number of periods")
    by_week = {}
    for week, latency_ms in readings:
        if not isinstance(week, int) or isinstance(week, bool) or week in by_week:
            raise ValueError("week IDs must be unique integers")
        if latency_ms is not None and (isinstance(latency_ms, bool) or
                not isinstance(latency_ms, (int, float)) or not isfinite(latency_ms) or
                latency_ms < 0):
            raise ValueError("latency must be finite, nonnegative or missing")
        by_week[week] = latency_ms
    if not by_week:
        raise ValueError("at least one observed week is required")
    first_week, last_week = min(by_week), max(by_week)
    possible = max(0, last_week - first_week - lag + 1)
    pairs = sorted((week, latency_ms, by_week[week + lag])
                   for week, latency_ms in by_week.items()
                   if week + lag <= last_week and latency_ms is not None
                   and by_week.get(week + lag) is not None)
    return pairs, possible, possible - len(pairs)

weekly_latency = [(50, 83.0), (47, 72.0), (52, 79.0),
                  (48, 76.0), (49, None), (51, 77.0), (53, 75.0)]
pairs, possible, omitted = latency_lag_pairs(weekly_latency, lag=2)
assert pairs == [(48, 76.0, 83.0), (50, 83.0, 79.0),
                 (51, 77.0, 75.0)]
assert (possible, omitted) == (5, 2)''',
        "cost": "For N supplied weeks, validation and keyed pairing take expected O(N) time; sorting the output takes O(N log N). The dictionary and pair ledger use O(N) space. The algorithm does not iterate across empty calendar positions, so a sparse span does not force a span-sized allocation. In the worked series, weeks 47 through 53 offer five possible lag-two starts. Only three pairs have measurements at both ends; the two omitted starts touch missing week 49. The point (83, 79) belongs to weeks 50 and 52. A renderer should label that point by its earlier week, not by the array index of the row that happened to arrive first.",
        "mistakes": ["Shifting by row count after missing calendar periods have been dropped.", "Drawing a diagonal reference line on independently scaled axes and calling it equality.", "Reporting the plotted point count without the eligible period-pair count.", "Reading trend-driven diagonal structure as a stable short-run forecasting law.", "Changing detrending, imputation or period definitions between comparison panels."],
        "drill": "Take 83 weekly latency measurements, leave three outage weeks explicitly absent, and compare lag one, lag two and lag four. For each panel, publish the intended pair count, plotted pair count and missing-pair count. Then repeat on a declared detrended series and record which visual patterns remain.",
        "related": [prefix + "autocorrelation-plots-regular-lags-pair-counts-and-seasonality", prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "scatterplot-overplotting-density-and-sampling-bias", prefix + "seasonal-subseries-plots-cycle-position-trend-and-incomplete-years"],
    },
    {
        "slug": "embedding-scatterplots-neighbor-retention-seeds-and-projection-limits",
        "title": "Embedding scatterplots: audit neighborhoods before naming clusters",
        "summary": "Treat a two-dimensional embedding as a projection of higher-dimensional records, then inspect neighbor retention, run settings and label leakage before interpreting the map.",
        "sections": [
            ("Separate the map from the feature space", "An embedding scatterplot gives each high-dimensional record a two-dimensional position so a human can inspect local structure. The plotted axes are coordinates of a fitted projection, not physical units or original features. A short distance on the map can suggest similar records under the chosen input representation, but map distance is not automatically the original distance. Some algorithms prioritize local neighborhoods and distort separation between distant groups. Others preserve a different notion of geometry. Choose the feature representation, distance metric and preprocessing before discussing the shape of the picture. For ticket text vectors, the unit is one ticket, not a sentence fragment that slipped in during preprocessing. A plot of sampled tickets must say how the sample was selected. [[data-visualization/chart-question-and-visual-encoding|Visual encoding]], [[data-visualization/scatterplot-overplotting-density-and-sampling-bias|overplotting]] and [[data-visualization/large-series-level-of-detail-and-extrema|level of detail]] remain ordinary chart obligations."),
            ("Freeze a reproducible projection contract", "Two maps are comparable only when they use compatible records, preprocessing, distance definitions, algorithm settings and random initialization rules. Keep a run manifest with the feature version, training population, sample IDs, projection settings and seed. A seed makes one run reproducible; it does not make every run or changed dataset geometrically identical. Do not compare the absolute X or Y coordinate across separately fitted maps. Rotation, reflection and nonlinear warping may move an otherwise similar configuration, while a changed sample can alter neighborhoods. If the user must track records over time, fit a stable reference projection where the method permits it or align maps with a declared procedure; still inspect the underlying neighbor sets. [[data-visualization/chart-export-manifest-data-and-render-version|Export manifests]] and [[data-visualization/dashboard-filter-and-provenance|provenance]] make this distinction operational."),
            ("Check neighbors against the original vectors", "The worked contract accepts already computed map coordinates and original numeric features. It does not implement a projection algorithm. For each record it finds the nearest neighbor in both spaces and counts whether the original neighbor survived the map. Ties break by stable record ID so an audit reruns predictably. The score is a compact diagnostic, not a certificate that every distance, density or group boundary is faithful. Run it at several neighborhood sizes, inspect representative failures and compare known operational slices. Standardize numeric features under a documented rule before Euclidean distance; otherwise a field measured in thousands can overwhelm one measured in fractions. If the original representation is an embedding vector, use the metric intended for that representation rather than quietly substituting Euclidean distance. [[data-visualization/scatterplot-matrices-pairwise-coverage-and-multiple-comparisons|Pairwise coverage]] and [[data-visualization/correlation-heatmap-pairwise-coverage-and-ordering|coverage summaries]] offer useful checks on the data before projection."),
            ("Keep labels and visual density honest", "Coloring an embedding by a known category can help find errors, but those labels may also have influenced the feature vectors or preprocessing. Disclose that path before claiming independent separation. A visible island can be produced by the projection objective, sample composition or density imbalance rather than a real, well-separated class. Show group counts, a legend and a selection-to-record table; do not rely on a hover tooltip as the only way to identify outliers. When thousands of points share pixels, use opacity or density bins and keep rare groups inspectable. Compare the view with a simpler baseline and a second run configuration before acting on small islands. [[data-visualization/hexbin-density-grid-resolution-and-exposure|Density bins]], [[data-visualization/interactive-chart-keyboard-focus-and-data-table-contract|keyboard selection]] and [[data-visualization/accessible-color-and-text-alternatives|text alternatives]] help readers audit the same records."),
        ],
        "code": '''from math import isfinite

def ticket_neighbor_retention(records: list[tuple[str, tuple[float, ...],
                                                  tuple[float, float]]]):
    if len(records) < 3:
        raise ValueError("at least three tickets are required")
    ticket_ids = [ticket_id for ticket_id, _, _ in records]
    feature_width = len(records[0][1])
    if len(set(ticket_ids)) != len(records) or feature_width == 0:
        raise ValueError("ticket IDs must be unique and vectors nonempty")
    for ticket_id, features, position in records:
        if (not ticket_id or len(features) != feature_width or len(position) != 2 or
                any(not isinstance(value, (int, float)) or isinstance(value, bool)
                    or not isfinite(value) for value in (*features, *position))):
            raise ValueError("all vectors and map positions must be finite")

    def nearest(index: int, projected: bool):
        source = records[index][2 if projected else 1]
        candidates = []
        for other_index, (other_id, features, position) in enumerate(records):
            if other_index == index:
                continue
            target = position if projected else features
            distance_squared = sum((left - right) ** 2
                                   for left, right in zip(source, target))
            candidates.append((distance_squared, other_id))
        return min(candidates)[1]

    retained = [ticket_ids[index] for index in range(len(records))
                if nearest(index, False) == nearest(index, True)]
    return retained, len(retained) / len(records)

support_tickets = [
    ("billing-47", (0.0, 0.0, 0.0), (0.0, 0.0)),
    ("billing-53", (0.1, 0.1, 0.1), (0.1, 0.1)),
    ("login-83", (3.0, 3.0, 3.0), (3.0, 3.0)),
    ("login-89", (3.1, 3.1, 3.1), (3.1, 3.1)),
    ("refund-97", (8.0, 0.0, 0.0), (0.25, 0.25)),
]
retained, share = ticket_neighbor_retention(support_tickets)
assert retained == ["billing-47", "billing-53", "login-83", "login-89"]
assert share == 0.8''',
        "cost": "For N records with D original features, the direct audit compares every ordered pair and costs O(N²D) time. It keeps only one row of distance candidates at a time, so working space is O(N) beyond the supplied vectors and map coordinates. At larger scale, audit a documented sample or use a nearest-neighbor index whose metric and approximation error are recorded. The five-ticket example retains the same nearest neighbor for four tickets. The projected refund ticket lands near a billing ticket even though its nearest neighbor in the three-feature space is a login ticket; the retention score is therefore 4/5, or 0.8. Do not interpret that single score as a probability that the map is correct. Inspect the specific mismatch before using the map to route tickets.",
        "mistakes": ["Treating the two map axes as named features or comparing raw coordinates from separately fitted maps.", "Declaring an island a real cluster from spacing alone without checking original-space neighborhoods.", "Using a label to build the representation and then describing its color separation as independent validation.", "Reporting one seed, one neighborhood size and one overall retention score without inspecting failures.", "Computing original-space distances on unscaled mixed-unit features without a metric contract."],
        "drill": "Project 83 support tickets from a frozen feature version. Record the sample IDs, preprocessing, metric, projection settings and seed. Audit nearest-neighbor retention for two neighborhood sizes, inspect ten failed neighbors by ticket ID, and repeat the projection with a second seed before naming any visible island.",
        "related": [prefix + "scatterplot-overplotting-density-and-sampling-bias", prefix + "hexbin-density-grid-resolution-and-exposure", prefix + "chart-export-manifest-data-and-render-version", prefix + "interactive-chart-keyboard-focus-and-data-table-contract"],
    },
]

publish(
    lessons,
    sort_start=8786,
    module_groups=[("Temporal dependence diagnostics", [0]),
                   ("High-dimensional projection audits", [1])],
    incoming={
        "autocorrelation-plots-regular-lags-pair-counts-and-seasonality": [0],
        "time-series-gaps-calendars-and-provisional-periods": [0],
        "seasonal-subseries-plots-cycle-position-trend-and-incomplete-years": [0],
        "connected-scatterplots-time-order-gaps-and-trajectory-reading": [0],
        "scatterplot-overplotting-density-and-sampling-bias": [0, 1],
        "hexbin-density-grid-resolution-and-exposure": [1],
        "chart-export-manifest-data-and-render-version": [1],
        "interactive-chart-keyboard-focus-and-data-table-contract": [1],
    },
    packet_name="aitrove-data-visualization-import-20261009.json",
)
