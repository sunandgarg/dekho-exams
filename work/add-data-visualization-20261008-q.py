"""Add original P–P plot and wind-rose lessons to Data Visualization."""
from data_visualization_batch import publish

prefix = "data-visualization/"
lessons = [
    {
        "slug": "pp-plots-reference-cdf-plotting-positions-and-tail-compression",
        "title": "P–P plots: compare observed probabilities with a fixed reference CDF",
        "summary": "Construct a probability–probability plot with an explicit plotting-position rule, then read its center and tail limits without confusing it with a Q–Q plot.",
        "sections": [
            ("Ask a probability-scale question", "A P–P plot checks whether an observed distribution agrees with a specified cumulative distribution function. Sort the observations. For each ordered value, put the reference CDF probability on one axis and an empirical plotting position on the other. If the two distributions agree, the points follow the diagonal within sampling variation. Both axes run from zero to one, so the coordinates are comparable across measurement units. This is a descriptive diagnostic, not a certificate that a model is correct. State which axis carries which probability: the sign of a deviation reverses if the axes are swapped. A persistent arc above the diagonal means the empirical cumulative share exceeds the proposed reference at those thresholds; it does not by itself name a physical cause. [[data-visualization/empirical-cdf-percentiles-and-tail-reading|Empirical CDFs]] show the same cumulative story against measured values, while [[data-visualization/qq-plots-quantile-alignment-ties-and-tail-deviation|Q–Q plots]] put values rather than probabilities on the axes."),
            ("Fix the reference before inspection", "Choose the reference distribution and its parameters from an external specification, an earlier frozen baseline or a fitting procedure whose use is declared. If mean and spread are estimated from the same sample, the resulting P–P points are drawn closer to the reference by construction; a line that looks good is then weaker evidence. Fitting after spotting a discrepancy compounds the problem. For a fresh validation set, keep the baseline version and population definition fixed. The worked contract uses a normal reference with a predeclared center of 71 and spread of 20. A normal CDF can assign probability to impossible negative values when the underlying measure cannot be negative, so choose a reference family consistent with the measurement domain. The plot should carry the exact center, spread, sample count and reference revision. [[data-visualization/chart-export-manifest-data-and-render-version|Chart export metadata]] and [[data-visualization/aggregation-grain-and-denominator|unit-of-analysis rules]] make that comparison repeatable."),
            ("Declare a plotting position and treat ties honestly", "For N sorted observations this lesson uses the midpoint position (rank minus one half) divided by N. It stays inside the open interval and gives every observation one ordinate. Other conventions are valid, but changing conventions moves the endpoints, especially when N is small. If measured values tie because a sensor rounds to whole units, several observations share a reference-CDF coordinate while their plotting positions differ. That vertical run is data, not a rendering error. If the reference has discrete jumps, the continuous midpoint convention requires a more careful discrete diagnostic; do not interpret the diagonal with continuous-case intuition. Missing, infinite and mixed-unit values must be resolved before sorting. [[data-visualization/unequal-bin-histograms-density-area-and-boundary-policy|Histograms]] can reveal rounding and mass points that a probability plot hides, and [[data-visualization/uncertainty-and-small-sample-display|small-sample guidance]] keeps isolated deviations in perspective."),
            ("Know what a probability scale suppresses", "Because both axes are bounded by zero and one, P–P plots are often easy to read through the center of a distribution. They compress extreme-value differences: a large change in the far tail may correspond to a tiny probability change near zero or one. Use a Q–Q plot or an explicit tail exceedance display when the operating decision depends on rare extreme values. Do not silently crop the first and last points; doing so makes a bad fit look quieter. Keep a square plotting region, equal numeric scales and a visible forty-five-degree reference line. An accessible companion table can list measured threshold, proposed CDF, empirical position and their difference. For two populations, use comparable panels or a stated two-sample construction rather than passing one estimated empirical CDF off as an independent fixed standard. [[data-visualization/small-multiples-shared-scales-and-facet-order|Shared-scale panels]] and [[data-visualization/accessible-color-and-text-alternatives|text alternatives]] preserve the evidence."),
        ],
        "code": '''from math import isfinite
from statistics import NormalDist

def probability_probability_points(
    response_ms: list[float], reference_center: float,
    reference_spread: float,
):
    if (not response_ms or not isfinite(reference_center) or
            not isfinite(reference_spread) or reference_spread <= 0 or
            any(not isfinite(value) for value in response_ms)):
        raise ValueError("finite observations and a positive reference spread are required")
    reference = NormalDist(mu=reference_center, sigma=reference_spread)
    ordered = sorted(response_ms)
    sample_size = len(ordered)
    return [(value, reference.cdf(value), (rank - 0.5) / sample_size)
            for rank, value in enumerate(ordered, start=1)]

latency_sample = [59.0, 71.0, 83.0, 71.0, 97.0]
points = probability_probability_points(latency_sample, 71.0, 20.0)
assert [row[0] for row in points] == [59.0, 71.0, 71.0, 83.0, 97.0]
assert [row[2] for row in points] == [0.1, 0.3, 0.5, 0.7, 0.9]
assert points[1][1] == points[2][1] == 0.5
assert points[0][1] < 0.5 < points[-1][1]''',
        "cost": "For N observations, validation is O(N), sorting is O(N log N), and one reference-CDF evaluation per row is O(N) under the standard constant-cost numerical model. The returned ledger and sorted copy require O(N) space. The five-value arithmetic check includes a repeated 71-millisecond reading: two points share reference probability 0.5 but occupy different empirical positions, 0.3 and 0.5. Five records are not enough to judge distributional fit; gather a representative, independently selected validation sample before interpreting the shape. A displayed diagonal is an expected relationship, not a formal acceptance test or a confidence band.",
        "mistakes": ["Calling a P–P plot a Q–Q plot while labeling its axes in measurement units.", "Estimating reference parameters on the inspection sample without disclosing the fit.", "Treating tied measured values as duplicates to delete before assigning ranks.", "Using center-focused visual agreement to dismiss a consequential extreme tail."],
        "drill": "Freeze a 71-millisecond center and 20-millisecond spread from a prior release. Plot 83 new, independently selected response times using midpoint positions; include an accessible table and compare the tail diagnosis with a Q–Q plot before changing the reference.",
        "related": [prefix + "qq-plots-quantile-alignment-ties-and-tail-deviation", prefix + "empirical-cdf-percentiles-and-tail-reading", prefix + "uncertainty-and-small-sample-display", prefix + "chart-export-manifest-data-and-render-version"],
    },
    {
        "slug": "wind-roses-direction-sectors-calm-share-and-speed-bands",
        "title": "Wind roses: map direction, speed and calm conditions without losing the denominator",
        "summary": "Bin directional observations across the north boundary, retain calm and missing readings separately, and report sector shares with a clear speed-band contract.",
        "sections": [
            ("Write down what a direction means", "A wind rose summarizes how often wind arrived from each compass sector, often subdivided by speed. In meteorological usage, a north reading means air came from the north; an arrow showing where the air travels points south. Confusing origin with travel direction rotates the interpretation by half a circle. Other directional datasets, such as vehicle headings, may use the direction of travel instead, so the chart title must say which convention applies. Angles wrap: 359 degrees and 1 degree belong next to each other, not at opposite ends of a linear axis. Choose a compass origin, clockwise ordering and sector count before grouping. With eight equal sectors, a north-centered bin covers angles near both zero and 360 degrees. [[data-visualization/chart-question-and-visual-encoding|Encoding choices]] and [[data-visualization/map-antimeridian-wrapping-bounds-and-projection-distortion|wrapped coordinates]] explain why a straight numeric interval can be misleading here."),
            ("Separate calm from missing and invalid", "When wind speed falls below a declared calm threshold, direction is physically uninformative or not reported. Give calm observations a separate count and share. A missing direction with a measurable wind speed is a data-quality issue, not calm. A missing speed is another quality issue. Decide whether the reporting denominator includes all valid measured periods, calm plus directional periods, or only non-calm directional periods, and put that choice beside every percentage. Comparing two stations using different calm thresholds changes the result even if their actual wind conditions match. Time spacing also matters: ten readings captured in one busy hour should not carry the same meaning as ten evenly spaced hours if the goal is time exposure. The example assumes one equally weighted observation per scheduled time slot and rejects malformed data. [[data-visualization/aggregation-grain-and-denominator|Denominator policy]] and [[data-visualization/time-series-gaps-calendars-and-provisional-periods|missing-period rules]] must be fixed before charting."),
            ("Keep speed bands and radial scale explicit", "A sector wedge can be divided into speed bands, but its total must reconcile to the number of qualifying observations in that sector. Use one speed unit throughout, non-overlapping boundaries and a named rule for observations exactly on a boundary. Here bands are below 6, from 6 through less than 14, and 14 or above, in metres per second. The code places a value of exactly 6 into the middle band. Label whether radius encodes count, percent of all valid periods, or percent within a sector. These answer different questions. If wedge angle is fixed, radial length is easy to compare but geometric area grows with its square; do not say area represents frequency unless the rendering actually uses an area-correct transform. Give a companion table of sector totals, band counts and shares. [[data-visualization/proportional-symbol-maps-area-scale-and-overlap|Area encoding]] and [[data-visualization/accessible-color-and-text-alternatives|accessible alternatives]] cover those distinctions."),
            ("Compare stations on matched exposure", "A rose from one winter month should not be compared casually with a full-year rose from another location. Align the observation window, sampling cadence, sensor height and missingness policy. Report the number of eligible time slots and the share excluded for missing readings; a direction bias can be produced by a sensor that drops out during storms. A wind rose aggregates away sequence. A short storm and recurring moderate winds may occupy the same direction sector but have different operational meaning. For an exposure or safety decision, pair the rose with a time-series chart and separate gust statistics. Do not infer local causes from sector frequencies alone. [[data-visualization/seasonal-subseries-plots-cycle-position-trend-and-incomplete-years|Seasonal subseries]] can expose changing seasonal patterns, while [[data-visualization/small-multiples-shared-scales-and-facet-order|small multiples]] keep station comparisons on a common radial scale."),
        ],
        "code": '''from math import isfinite

SECTORS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")

def wind_rose_ledger(readings: list[tuple[str, float | None, float | None]],
                     calm_below: float = 1.0):
    if not isfinite(calm_below) or calm_below < 0:
        raise ValueError("calm threshold must be finite and nonnegative")
    sector_bands = [[0, 0, 0] for _ in SECTORS]
    seen_slots = set()
    calm = missing = 0
    for slot_id, direction_from_degrees, speed_mps in readings:
        if not slot_id or slot_id in seen_slots:
            raise ValueError("each scheduled slot needs a unique ID")
        seen_slots.add(slot_id)
        if speed_mps is None or direction_from_degrees is None:
            missing += 1
            continue
        if (not isfinite(speed_mps) or speed_mps < 0 or
                not isfinite(direction_from_degrees) or
                not 0 <= direction_from_degrees < 360):
            raise ValueError("speed and direction must use declared units")
        if speed_mps < calm_below:
            calm += 1
            continue
        sector = int((direction_from_degrees + 22.5) // 45) % 8
        band = 0 if speed_mps < 6 else 1 if speed_mps < 14 else 2
        sector_bands[sector][band] += 1
    measured = len(readings) - missing
    if measured == 0:
        raise ValueError("no measured slots")
    directional = sum(sum(bands) for bands in sector_bands)
    assert directional + calm == measured
    return {
        "measured": measured, "missing": missing, "calm": calm,
        "calm_share": calm / measured,
        "sector_bands": dict(zip(SECTORS, sector_bands)),
    }

hourly_readings = [("hour-47", 359.0, 5.0), ("hour-48", 1.0, 6.0),
                   ("hour-49", 47.0, 14.0), ("hour-50", 271.0, 0.4),
                   ("hour-51", None, 9.0)]
rose = wind_rose_ledger(hourly_readings)
assert rose["sector_bands"]["N"] == [1, 1, 0]
assert rose["sector_bands"]["NE"] == [0, 0, 1]
assert (rose["measured"], rose["calm"], rose["missing"]) == (4, 1, 1)
assert rose["calm_share"] == 0.25''',
        "cost": "For N scheduled readings, validation and accumulation take O(N) expected time; the slot-ID set uses O(N) space, while the fixed eight-by-three tally uses O(1). The example groups 359 and 1 degrees into north, assigns exactly 6 metres per second to the middle speed band, and counts a measured low-speed west reading as calm. Four measured hours form the denominator, so calm share is 25 percent. The fifth scheduled hour is missing, not calm. A real deployment should monitor missing-share changes and may need duration weighting when observation intervals are unequal.",
        "mistakes": ["Reading meteorological wind direction as the direction air travels toward.", "Placing angles near zero and 360 degrees in distant bins.", "Converting missing directions into calm readings or silently dropping them from every count.", "Comparing roses with different sampling windows, calm thresholds or radial denominators."],
        "drill": "Build a rose for 83 scheduled hourly slots from a sensor log. Reconcile directional, calm and missing counts, document the direction convention and speed units, then compare two matched seasons using the same sectors and radial scale.",
        "related": [prefix + "aggregation-grain-and-denominator", prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "proportional-symbol-maps-area-scale-and-overlap", prefix + "small-multiples-shared-scales-and-facet-order"],
    },
]

publish(
    lessons,
    sort_start=8780,
    module_groups=[("Probability-scale distribution checks", [0]),
                   ("Circular direction and exposure displays", [1])],
    incoming={
        "qq-plots-quantile-alignment-ties-and-tail-deviation": [0],
        "empirical-cdf-percentiles-and-tail-reading": [0],
        "uncertainty-and-small-sample-display": [0],
        "distribution-and-outlier-displays": [0],
        "aggregation-grain-and-denominator": [1],
        "time-series-gaps-calendars-and-provisional-periods": [1],
        "proportional-symbol-maps-area-scale-and-overlap": [1],
        "small-multiples-shared-scales-and-facet-order": [1],
        "seasonal-subseries-plots-cycle-position-trend-and-incomplete-years": [1],
    },
    packet_name="aitrove-data-visualization-import-20261008-q.json",
)
