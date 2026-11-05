"""Add original connected-scatter and missingness-matrix lessons."""
from data_visualization_batch import publish

prefix = "data-visualization/"
lessons = [
    {
        "slug": "connected-scatterplots-time-order-gaps-and-trajectory-reading",
        "title": "Connected scatterplots: preserve time order, gaps and trajectory direction",
        "summary": "Trace paired measurements through the X–Y plane without inventing observations across missing periods or interpreting loops as proof of causation.",
        "sections": [
            ("Make two measures and one clock explicit", "A connected scatterplot places one quantitative measure on the horizontal axis and another on the vertical axis, then joins observations in chronological order. Time is encoded by the path rather than either axis. That separates it from an ordinary time-series line chart, whose horizontal axis is time, and from an unconnected scatterplot, which contains no ordered journey. Use it when the question concerns how two measures move together across successive periods: did both rise, did one lead the other, and did the system return to a former combination? Put the units, measurement grain and time-step rule next to the chart. Two plotted values must refer to the same entity and period; pairing this week's costs with last week's outcomes by accident can create a false loop. [[data-visualization/chart-question-and-visual-encoding|Chart encoding]], [[data-visualization/aggregation-grain-and-denominator|grain rules]] and [[data-visualization/event-aligned-time-series-baseline-windows-and-missing-periods|period alignment]] should be fixed first."),
            ("Order the path by time, never by X value", "Many plotting libraries connect points in input order. A database result without an explicit time sort can therefore produce a different path on a second run. Sort by a unique, declared period key and reject duplicate observations unless the aggregation policy specifies how to combine them. Mark the start and end, add sparse period labels and draw direction arrows where a reversal would otherwise be ambiguous. An arrow points forward through time, not necessarily toward increasing X or Y. Keep both numeric axes stable across compared groups. If a measure can be negative, retain a meaningful zero line when that helps interpretation; do not force both axes to zero merely to fill a square frame. The worked contract returns ordered points and allowable segments so a renderer cannot accidentally reorder them. [[data-visualization/scale-baseline-and-axis-integrity|Axis integrity]] and [[data-visualization/small-multiples-shared-scales-and-facet-order|shared-scale panels]] protect comparisons."),
            ("Break at unobserved periods", "A straight segment from period 48 to period 50 suggests a continuous movement through the middle even when period 49 was never measured. Break the line at that gap or draw a distinctly styled connection with a documented interpolation rule. The simple contract below only connects consecutive integer periods. It leaves points after a gap visible but starts a new path. For irregular calendars, a consecutive integer is not enough: use an explicit sequence of expected periods that incorporates holidays, fiscal weeks or excluded maintenance windows. A blank period is not a zero measurement. Nor should the line skip a failed sensor silently. Show completeness counts and use a companion pair of ordinary time-series charts when it matters which variable changed during a gap. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Calendar and provisional-period rules]] describe that boundary."),
            ("Read shape without claiming a mechanism", "A path heading northeast means both measures increased between adjacent observations. A loop means the pair revisited a part of the X–Y plane after taking a different route. It may be consistent with lag, seasonality, changed population mix or measurement timing; the shape alone cannot choose among them. Large jumps can dominate the path and hide small movements, while overlapping segments can make direction hard to follow. Annotate major period boundaries, then test the story against the original separate time series. If many entities are present, one dense web is rarely legible; use a few labeled trajectories or small multiples. Avoid animation as the only route to chronology, and provide an ordered table of period, X and Y. [[data-visualization/animated-charts-stable-identity-locked-scales-and-pause-state|Animation controls]], [[data-visualization/accessible-color-and-text-alternatives|accessible text]] and [[data-visualization/chart-annotations-event-windows-and-causal-claims|causal-claim limits]] remain relevant."),
        ],
        "code": '''from math import isfinite

def paired_trajectory(readings: list[tuple[int, float, float]]):
    if not readings:
        raise ValueError("at least one paired period is required")
    seen = set()
    for period, acquisition_cost, activation_rate in readings:
        if (not isinstance(period, int) or period in seen or
                not isfinite(acquisition_cost) or acquisition_cost < 0 or
                not isfinite(activation_rate) or not 0 <= activation_rate <= 1):
            raise ValueError("periods must be unique; paired measures must be valid")
        seen.add(period)
    points = sorted(readings)
    segments = [(earlier, later)
                for earlier, later in zip(points, points[1:])
                if later[0] == earlier[0] + 1]
    gaps = [(earlier[0], later[0])
            for earlier, later in zip(points, points[1:])
            if later[0] != earlier[0] + 1]
    return points, segments, gaps

weekly_acquisition = [(50, 83.0, 0.59), (47, 71.0, 0.47),
                      (48, 79.0, 0.53), (51, 77.0, 0.64)]
points, segments, gaps = paired_trajectory(weekly_acquisition)
assert [period for period, _, _ in points] == [47, 48, 50, 51]
assert [(start[0], end[0]) for start, end in segments] == [(47, 48), (50, 51)]
assert gaps == [(48, 50)]
assert points[-1][2] == 0.64''',
        "cost": "For N paired periods, validation takes O(N) expected time, sorting takes O(N log N), and segment construction takes O(N). The duplicate-key set, sorted points and segment ledger use O(N) space. In the worked data, the input arrives out of order, but the output orders periods 47, 48, 50 and 51. The chart draws segments from 47 to 48 and from 50 to 51; it refuses to suggest an observed route through missing period 49. The activation rate rises to 0.64 by the final period even though acquisition cost falls from 83 to 77 between 50 and 51. Those are adjacent descriptive changes, not an estimated causal effect.",
        "mistakes": ["Connecting points in database-return order or sorting by the horizontal measure.", "Pairing measures from different cohorts or period definitions.", "Drawing a solid segment through an unobserved period without an interpolation rule.", "Calling a loop evidence that one measure caused a delayed change in the other."],
        "drill": "Track 83 weekly cost and activation pairs for one stable cohort. Audit duplicate weeks, mark every break in the expected calendar, label start and end, then compare the trajectory with two ordinary time-series charts before interpreting a loop.",
        "related": [prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "event-aligned-time-series-baseline-windows-and-missing-periods", prefix + "small-multiples-shared-scales-and-facet-order", prefix + "chart-annotations-event-windows-and-causal-claims"],
    },
    {
        "slug": "missingness-matrices-record-order-patterns-and-co-missing-fields",
        "title": "Missingness matrices: reveal record-order patterns and co-missing fields",
        "summary": "Build a binary presence matrix with explicit null rules, row order, pattern counts and field-pair support before imputing or dropping records.",
        "sections": [
            ("Treat presence as a separate variable", "A missingness matrix displays records on one axis and fields on the other, coloring each cell according to whether the field was observed. Its first job is to show structure hidden by overall missing percentages: a whole block lost during one import, one field absent only for a particular cohort, or two fields disappearing together. Define missing before plotting. In this lesson, None and floating-point NaN are missing; zero and an empty string count as observed values unless a separate domain rule says otherwise. That rule must be applied before rendering and recorded with the chart, because changing it can redraw the pattern without changing any source records. An imputed value is not originally observed and should retain a separate provenance flag. [[data-visualization/heatmap-missing-cells-and-color-domain|Heatmap missing-cell encoding]] and [[data-visualization/dashboard-filter-and-provenance|dashboard provenance]] support that distinction."),
            ("Keep the row order meaningful", "A random row order can turn a sustained outage into a scattered texture. Sort records by acquisition time, batch ID or another declared operational sequence, and retain stable unique row identifiers. A secondary sort by missingness pattern can reveal common combinations but destroys chronology; if you use it, label the new order and keep a time-ordered companion view. At large N, drawing every row may produce thousands of subpixel cells. Aggregate into windows, sample with a fixed documented rule, or summarize repeated patterns; never hide rare but consequential failures in an average. Show row count and per-field observed counts beside the matrix. If batches have different schemas, use an explicit not-applicable state rather than treating structurally absent fields as ordinary missing data. [[data-visualization/large-series-level-of-detail-and-extrema|Level of detail]] and [[data-visualization/time-series-gaps-calendars-and-provisional-periods|time gaps]] determine how much the reader can see."),
            ("Count patterns and pair overlap, not just column rates", "Two fields may each be missing in a quarter of records yet fail in completely different rows. A matrix shows the difference; pattern frequencies and pairwise co-missing counts quantify it. The code creates a boolean mask per row, counts each exact pattern, and counts records in which every selected pair is missing. These pair counts are not a correlation coefficient and cannot by themselves explain why values are absent. Show the denominator for every pair: records eligible for both fields. If eligibility changes across rows, restrict the calculation to comparable records or add explicit applicability flags. A pair with no missing records has zero co-missing count, but a field that is always missing cannot be assessed for variation. [[data-visualization/correlation-heatmap-pairwise-coverage-and-ordering|Pairwise coverage]] and [[data-visualization/aggregation-grain-and-denominator|denominator policy]] prevent false comparisons."),
            ("Do not infer a missing-data mechanism from color blocks", "A matrix can expose dependence on observed batches or fields, but it cannot prove that values are missing completely at random, missing at random conditional on observed variables, or missing not at random. The last case depends on unseen values, which the chart cannot display. Avoid turning a visually coherent pattern into an imputation rule without investigating the collection process and validating the downstream model. A form redesign, sensor outage, consent rule or ETL change can all create similar bands. Keep collection timestamps and data-quality events available for annotation; compare raw and post-cleaning views so deletion does not make failure disappear. Use a text table of missing rates, frequent patterns and affected periods for readers who cannot parse a dense matrix. [[data-visualization/chart-annotations-event-windows-and-causal-claims|Event annotations]] and [[data-visualization/accessible-color-and-text-alternatives|text alternatives]] keep interpretation bounded."),
        ],
        "code": '''from collections import Counter
from itertools import combinations
from math import isnan

FIELDS = ("order_total", "delivery_zone", "carrier_id")

def absent(value):
    return value is None or (isinstance(value, float) and isnan(value))

def missingness_ledger(records: list[tuple[int, str, dict]]):
    seen = set()
    matrix = []
    pattern_counts = Counter()
    pair_counts = Counter()
    missing_by_field = Counter()
    for period, order_id, values in records:
        if (not isinstance(period, int) or not order_id or order_id in seen or
                set(values) != set(FIELDS)):
            raise ValueError("rows need unique IDs and the declared schema")
        seen.add(order_id)
        missing = tuple(field for field in FIELDS if absent(values[field]))
        pattern_counts[missing] += 1
        missing_by_field.update(missing)
        pair_counts.update(combinations(missing, 2))
        matrix.append((period, order_id, tuple(field in missing for field in FIELDS)))
    matrix.sort(key=lambda row: (row[0], row[1]))
    return matrix, missing_by_field, pattern_counts, pair_counts

orders = [(50, "order-83", {"order_total": 83.0, "delivery_zone": None,
                             "carrier_id": None}),
          (47, "order-47", {"order_total": 47.0, "delivery_zone": "W",
                             "carrier_id": "carrier-7"}),
          (48, "order-59", {"order_total": float("nan"),
                             "delivery_zone": "E", "carrier_id": None}),
          (51, "order-97", {"order_total": 0.0, "delivery_zone": "",
                             "carrier_id": "carrier-9"})]
matrix, field_counts, patterns, pairs = missingness_ledger(orders)
assert [row[0] for row in matrix] == [47, 48, 50, 51]
assert field_counts == {"order_total": 1, "delivery_zone": 1, "carrier_id": 2}
assert pairs[("delivery_zone", "carrier_id")] == 1
assert patterns[()] == 2
assert matrix[-1][2] == (False, False, False)''',
        "cost": "For N records and K declared fields, building masks and field counts takes O(NK) time. Counting every missing pair takes O(sum mᵢ²), at most O(NK²), where mᵢ is the number of missing fields in row i; sorting the row ledger adds O(N log N). Matrix storage is O(NK), while pattern and pair counters can reach O(min(N, 2ᴷ) plus K²) entries. The sample has four orders, two fully observed patterns, one missing total, one missing zone and two missing carrier IDs. Only one record loses both zone and carrier. Its final record's zero total and empty zone remain observed under the declared rule; another business rule could mark the empty zone missing, but must be versioned and disclosed.",
        "mistakes": ["Conflating zero, empty string, NaN, None and not-applicable without a field contract.", "Sorting rows by missingness and then describing a resulting band as chronological.", "Interpreting co-missing counts as a causal mechanism or a formal correlation measure.", "Removing bad records before charting and presenting the cleaned matrix as raw quality evidence."],
        "drill": "Audit 83 ordered import batches with three required fields and one optional field. Publish raw missingness patterns, per-field support and the most common co-missing pair; keep not-applicable separate and annotate any schema or collection change.",
        "related": [prefix + "heatmap-missing-cells-and-color-domain", prefix + "correlation-heatmap-pairwise-coverage-and-ordering", prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "dashboard-filter-and-provenance"],
    },
]

publish(
    lessons,
    sort_start=8784,
    module_groups=[("Paired time-series trajectories", [0]),
                   ("Data completeness diagnostics", [1])],
    incoming={
        "time-series-gaps-calendars-and-provisional-periods": [0, 1],
        "event-aligned-time-series-baseline-windows-and-missing-periods": [0],
        "small-multiples-shared-scales-and-facet-order": [0],
        "chart-annotations-event-windows-and-causal-claims": [0, 1],
        "heatmap-missing-cells-and-color-domain": [1],
        "correlation-heatmap-pairwise-coverage-and-ordering": [1],
        "dashboard-filter-and-provenance": [1],
        "large-series-level-of-detail-and-extrema": [1],
    },
    packet_name="aitrove-data-visualization-import-20261008-s.json",
)
