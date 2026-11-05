"""Publish five additional original Data Visualization lessons."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-data-visualization-import-20261008-g.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "data-visualization/"
hub = prefix + "data-visualization-tutorial"

lessons = [
    {
        "slug": "ridgeline-plots-density-normalization-bandwidth-and-overlap",
        "title": "Ridgeline plots: compare distributions without hiding their size",
        "summary": "Use shared units and smoothing, disclose whether each ridge has unit area, and make overlaps readable.",
        "sections": [
            ("First decide what height means", "A ridgeline plot stacks several distribution curves along one shared horizontal measure. Each ridge can be a normalized density or a count-scaled curve. Those choices answer different questions. Unit-area curves compare shape but erase group size; count-scaled curves retain volume but can bury small groups. Put the choice beside the chart and list group counts. A ridge with 47 observations should not appear as equally well supported as one with 4,700 just because both curves reach the same height. [[data-visualization/box-violin-and-kde-bandwidth-for-group-comparisons|Box and violin displays]] offer a less overlapping alternative when the group count grows."),
            ("One bandwidth across comparable groups", "A density ridge depends on the smoothing bandwidth. A narrow bandwidth can turn individual observations into false-looking peaks; a wide one can erase real mixtures. If the goal is comparison, use one documented bandwidth in the same units for every group, then inspect the underlying counts and a histogram or ECDF. Near a hard lower bound such as zero minutes, a symmetric kernel can place visual density below zero. Clip display only with an explicit boundary rule, or use a boundary-aware estimator. [[data-visualization/empirical-cdf-percentiles-and-tail-reading|ECDFs]] avoid bandwidth choice entirely and are useful for checking tail claims."),
            ("Overlap is a design parameter", "The vertical offset between ridges changes what is concealed. With heavy overlap, the front ridge can cover a smaller peak in the ridge behind it. Keep a thin outline, enough transparency and a stable layer order. Do not use color alone for identity; label each ridge on its own baseline. For a screen reader or a small phone, publish a companion table of group size, median and selected percentiles. [[data-visualization/accessible-color-and-text-alternatives|Accessible chart alternatives]] help preserve the comparison when curves cannot be seen or hovered."),
            ("Keep populations and windows aligned", "A weekly ridge may show an apparent shift because the eligible population changed, not because individual values moved. Define the event, unit, missing-value rule and period before comparing curves. If a week has too few valid observations, mark it as insufficient rather than creating a smooth curve from a handful of points. Keep the horizontal domain fixed across a report; otherwise a later ridge can look compressed only because its axis changed. [[data-visualization/aggregation-grain-and-denominator|Aggregation grain]] and [[data-visualization/time-series-gaps-calendars-and-provisional-periods|period completeness]] should accompany the exported chart data."),
        ],
        "code": '''from math import exp, isfinite, pi, sqrt

def gaussian_ridge(samples: list[float], grid: list[float],
                   bandwidth: float) -> list[float]:
    if not samples or not grid or not isfinite(bandwidth) or bandwidth <= 0:
        raise ValueError("samples, grid and positive bandwidth required")
    if any(not isfinite(value) for value in samples + grid):
        raise ValueError("values must be finite")
    scale = len(samples) * bandwidth * sqrt(2 * pi)
    return [sum(exp(-0.5 * ((position - value) / bandwidth) ** 2)
                for value in samples) / scale for position in grid]

weekly_minutes = {"week 47": [27, 31, 35, 41],
                  "week 48": [31, 37, 43, 49]}
grid_minutes = [30, 40, 50]
ridge_rows = {week: gaussian_ridge(values, grid_minutes, 8)
              for week, values in weekly_minutes.items()}
assert len(ridge_rows["week 47"]) == 3
assert all(height > 0 for heights in ridge_rows.values() for height in heights)
assert ridge_rows["week 47"][0] > ridge_rows["week 48"][0]''',
        "language": "python",
        "cost": "For G groups, M grid positions and N total observations, direct Gaussian evaluation takes O(MN) time and O(GM) output space. The sample lists also occupy O(N) memory. A histogram convolution or a vetted density library is preferable for a very large grid. The code estimates unbounded Gaussian densities; it does not correct a physical zero boundary or choose a statistically justified bandwidth. Save the bandwidth, group counts, grid and raw eligibility rule with every export.",
        "mistakes": ["Reading equal-height, unit-area ridges as equal numbers of events.", "Using a different automatic bandwidth for each group while comparing peaks.", "Allowing overlap to hide a smaller group without outlines or a table.", "Treating a four-record smooth curve as stable evidence of several modes."],
        "drill": "Compare 59 weekly response-time groups. Mark weeks with fewer than 47 valid records, hold the unit and horizontal range fixed, and verify one apparent tail shift with an ECDF.",
        "related": [prefix + "box-violin-and-kde-bandwidth-for-group-comparisons", prefix + "empirical-cdf-percentiles-and-tail-reading", prefix + "accessible-color-and-text-alternatives", prefix + "aggregation-grain-and-denominator"],
    },
    {
        "slug": "scatterplot-regression-overlays-fit-scope-and-prediction-bands",
        "title": "Regression overlays: separate fitted trend from individual spread",
        "summary": "Fit on a declared population, show the data behind the line, and keep confidence and prediction bands distinct.",
        "sections": [
            ("Define the fit population", "A line on a scatterplot is a model output, not a property of the pixels. State which rows entered the fit, the x and y units, the time window and exclusions. If the visible chart filters to one region while the line is still fitted across all regions, label that difference or refit intentionally. A pooled line can hide opposing group trends. Plot groups separately before deciding whether a shared slope is defensible. [[data-visualization/scatterplot-overplotting-density-and-sampling-bias|Overplotting and sampling]] can make a line look better supported than the visible points imply."),
            ("Do not mix two kinds of band", "A confidence band for the conditional mean describes uncertainty in the estimated average curve under the model. A prediction band for a new observation includes individual variation and is normally wider. Label the band type, level and fitting method; never call an arbitrary shaded region a confidence interval. [[data-visualization/asymmetric-error-bars-interval-type-and-axis-clipping|Interval endpoints]] should be retained in the exported data. A narrow mean band does not promise that the next delivery will land near the line."),
            ("Check influential points and model shape", "One distant x value may pull a straight line through a cloud that otherwise has little trend. Inspect residuals and report the fit's valid x range. If the relationship bends, a straight line can be a poor summary even when it is easy to draw. Do not extend the overlay far beyond observed x values unless extrapolation is the explicit task and its uncertainty is shown. [[data-visualization/qq-plots-quantile-alignment-ties-and-tail-deviation|Q–Q diagnostics]] can reveal distribution departures in residuals but do not repair confounding or nonlinearity."),
            ("Keep explanation separate from causation", "A rising line means the plotted variables co-vary in the selected records. It does not establish that changing x will change y. Annotate outages, policy changes or cohorts where they matter, but do not turn temporal coincidence into a mechanism. [[data-visualization/chart-annotations-event-windows-and-causal-claims|Event annotations]] have the same limit. Publish the coefficients and row count alongside the plot, and offer a table of fitted values if the chart is interactive. A model revision should change its version in the export so the old and new lines can be reproduced."),
        ],
        "code": '''from math import isfinite

def fit_straight_line(points: list[tuple[float, float]]) -> tuple[float, float]:
    if len(points) < 3 or any(not (isfinite(x) and isfinite(y))
                              for x, y in points):
        raise ValueError("at least three finite pairs required")
    mean_x = sum(x for x, _ in points) / len(points)
    mean_y = sum(y for _, y in points) / len(points)
    xx = sum((x - mean_x) ** 2 for x, _ in points)
    if xx == 0:
        raise ValueError("x values need variation")
    slope = sum((x - mean_x) * (y - mean_y) for x, y in points) / xx
    return mean_y - slope * mean_x, slope

dispatch_records = [(2, 47), (3, 59), (4, 71), (5, 83)]
intercept, slope = fit_straight_line(dispatch_records)
assert (intercept, slope) == (23.0, 12.0)
assert intercept + slope * 6 == 95.0''',
        "language": "python",
        "cost": "Computing a simple least-squares line takes O(N) time and O(1) extra space for N pairs. The code deliberately does not calculate uncertainty bands: those require a named model, assumptions, residual variance and an interval method. It is only a descriptive fit; the four exact points are a code check, not evidence of predictive accuracy. Keep the raw rows or an auditable snapshot when shipping a chart with a fitted overlay.",
        "mistakes": ["Fitting on all rows while displaying only a filtered subset without saying so.", "Calling a mean-confidence band a prediction interval for the next record.", "Extrapolating a straight line beyond observed x values as though support were unchanged.", "Interpreting an association line as proof of a causal effect."],
        "drill": "Fit dispatch delay against queue depth for 188 records. Compare pooled and depot-specific slopes, identify the most influential record, and label any uncertainty band with its exact meaning.",
        "related": [prefix + "scatterplot-overplotting-density-and-sampling-bias", prefix + "asymmetric-error-bars-interval-type-and-axis-clipping", prefix + "qq-plots-quantile-alignment-ties-and-tail-deviation", prefix + "chart-annotations-event-windows-and-causal-claims"],
    },
    {
        "slug": "map-antimeridian-wrapping-bounds-and-projection-distortion",
        "title": "Map boundaries: handle antimeridian crossings before drawing routes",
        "summary": "Normalize longitude, split crossings and treat projection distance as a display property.",
        "sections": [
            ("Longitude has a seam", "A route from 177 degrees east to 178 degrees west crosses a narrow part of the Pacific. A renderer that simply connects numeric longitudes may draw a line across nearly the entire map. Choose a longitude convention, validate it at ingestion, and split a crossing before sending geometry to the visual layer. Keep the original coordinates as well as display segments. [[data-visualization/proportional-symbol-maps-area-scale-and-overlap|Symbol maps]] also need a clear coordinate meaning; a route line needs the additional seam rule."),
            ("A bounding box can wrap", "For an antimeridian-spanning area, a western longitude numerically greater than the eastern longitude can describe a small region. Do not automatically swap the two values or calculate width by direct subtraction. Compute wrapped angular span and tell a mapping library whether its viewport crosses the seam. A naive min-to-max bounding box may zoom to almost the whole world. [[data-visualization/choropleth-rates-boundaries-and-missing-regions|Region boundaries]] need the same care when a polygon is split into multiple pieces for display."),
            ("Projection changes visual geometry", "A flat map projects a curved surface. Pixel distance, area and direction can vary with projection and latitude. Use a projection appropriate to the question, and avoid estimating physical travel distance with screen coordinates. A straight segment drawn in longitude and latitude is not automatically the shortest path on Earth. When a route represents measured travel, retain the actual track; when it represents an abstract connection, label it as such. [[data-visualization/scale-baseline-and-axis-integrity|Scale integrity]] applies to maps as well as charts."),
            ("Preserve identity across pieces", "After a crossing is cut into two display segments, both pieces must retain one route ID so a tooltip, filter and export refer to the same underlying trip. A segment count is not a trip count. Include source coordinate order, time zone for event timestamps, geometry version and wrapping method in the export. Test endpoints exactly at positive and negative 180 degrees. [[data-visualization/chart-export-manifest-data-and-render-version|The export manifest]] should record enough to reproduce the same viewport and splitting rule after a map library upgrade."),
        ],
        "code": '''from math import isfinite

def split_dateline_segment(west: tuple[float, float],
                           east: tuple[float, float]
                          ) -> list[list[tuple[float, float]]]:
    lon_a, lat_a = west
    lon_b, lat_b = east
    if not all(isfinite(value) for value in (*west, *east)):
        raise ValueError("coordinates must be finite")
    if not (-180 <= lon_a <= 180 and -180 <= lon_b <= 180
            and -90 <= lat_a <= 90 and -90 <= lat_b <= 90):
        raise ValueError("longitude or latitude outside range")
    difference = lon_b - lon_a
    if abs(difference) <= 180:
        return [[west, east]]
    adjusted_b = lon_b - 360 if difference > 180 else lon_b + 360
    seam = -180 if adjusted_b < lon_a else 180
    fraction = (seam - lon_a) / (adjusted_b - lon_a)
    seam_lat = lat_a + fraction * (lat_b - lat_a)
    opposite = 180 if seam == -180 else -180
    return [[west, (seam, seam_lat)], [(opposite, seam_lat), east]]

shipping_route = split_dateline_segment((177, -17), (-178, -18))
assert shipping_route == [
    [(177, -17), (180, -17.6)],
    [(-180, -17.6), (-178, -18)],
]''',
        "language": "python",
        "cost": "Splitting one two-point segment is O(1) time and space; a route with N points needs O(N) processing and output. The interpolation is linear in longitude and latitude for display geometry, not a geodesic calculation. For long-distance navigation or polar tracks, densify with a suitable geographic method before projecting. A production pipeline must define how exact-seam endpoints, multi-segment tracks and duplicate 180-degree coordinates are serialized.",
        "mistakes": ["Drawing a nearly global line between two points that are close across the seam.", "Swapping wrapped bounding-box longitudes and accidentally selecting most of the world.", "Measuring real distance from flat-map pixels.", "Counting two rendered pieces as two journeys."],
        "drill": "Draw 47 shipping tracks with three seam crossings. Keep one ID per journey, verify wrapped viewport width, and compare the exported track length with the number of display segments.",
        "related": [prefix + "proportional-symbol-maps-area-scale-and-overlap", prefix + "choropleth-rates-boundaries-and-missing-regions", prefix + "scale-baseline-and-axis-integrity", prefix + "chart-export-manifest-data-and-render-version"],
    },
    {
        "slug": "event-aligned-time-series-baseline-windows-and-missing-periods",
        "title": "Event-aligned charts: choose a baseline before comparing trajectories",
        "summary": "Align observations to a real event, retain calendar context and make missing periods explicit.",
        "sections": [
            ("Event time is not calendar time", "An event-aligned chart puts each subject's event at relative time zero. This lets a reader compare trajectories before and after events that occurred on different calendar dates. Store the actual event timestamp as well as the relative offset; otherwise seasonality, outages and policy changes disappear. Specify whether an offset means elapsed hours, calendar days or complete reporting periods. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Time-series period rules]] are essential when the event occurs late in a day or across a daylight-saving change."),
            ("Fix the baseline rule", "A common display subtracts each subject's pre-event value or divides by it. These produce different shapes and units. Select the baseline window before inspecting outcomes, report how many valid observations contributed to it, and reject a percentage change when the baseline is zero. If one subject has only one pre-event measurement and another has 47, their aligned curves carry different reliability. [[data-visualization/aggregation-grain-and-denominator|Denominator and grain]] rules should stay visible with the chart. Plot absolute values alongside normalized values when the magnitude of the original series matters."),
            ("Missing is not flat", "Do not fill missing pre-event days with the baseline or connect a line across an unobserved outage without a marker. A cohort average at relative day five may use fewer subjects than at day one because follow-up ends; show the contributing count by offset. Attrition can make a trend look like improvement. [[data-visualization/uncertainty-and-small-sample-display|Small-sample uncertainty]] belongs near sparse tails, and [[data-visualization/forecast-fan-charts-prediction-intervals-and-horizon|forecast intervals]] must not be substituted for missing actual observations."),
            ("The line does not prove an effect", "A change at time zero can reflect selection into the event, a concurrent intervention, regression to the mean or ordinary seasonality. An annotation identifies timing, not causality. Compare a relevant untreated group or a pre-specified benchmark if the decision requires an effect estimate, and state the assumptions of that comparison. [[data-visualization/chart-annotations-event-windows-and-causal-claims|Annotation and causal-claim boundaries]] apply here. Export subject ID, event date, relative offset, original value, baseline window, normalized value and eligibility state so every plotted line can be reconstructed."),
        ],
        "code": '''from datetime import date
from math import isfinite

def event_aligned_change(event_day: date, observations: dict[date, float],
                         baseline_days: tuple[date, ...]
                        ) -> list[tuple[int, float, float]]:
    if not baseline_days or len(set(baseline_days)) != len(baseline_days):
        raise ValueError("baseline days must be distinct")
    if any(day >= event_day or day not in observations for day in baseline_days):
        raise ValueError("baseline must be observed before the event")
    if any(not isfinite(value) for value in observations.values()):
        raise ValueError("observations must be finite")
    baseline = sum(observations[day] for day in baseline_days) / len(baseline_days)
    return sorted(((day - event_day).days, value, value - baseline)
                  for day, value in observations.items())

incident_counts = {
    date(2026, 10, 5): 47, date(2026, 10, 6): 59,
    date(2026, 10, 8): 38, date(2026, 10, 9): 35,
}
aligned = event_aligned_change(
    date(2026, 10, 7), incident_counts,
    (date(2026, 10, 5), date(2026, 10, 6)),
)
assert aligned == [(-2, 47, -6), (-1, 59, 6), (1, 38, -15), (2, 35, -18)]
assert all(offset != 0 for offset, _, _ in aligned)''',
        "language": "python",
        "cost": "For N observations and B baseline days, validation and averaging take O(N+B) time; sorting relative periods takes O(N log N) time and O(N) output space. The function leaves missing event day zero absent instead of inventing a value. Calendar dates are appropriate only when day-level reporting is the contract; intraday events need zoned timestamps and a declared binning method. Subtracting a baseline describes change, not a causal estimate.",
        "mistakes": ["Discarding calendar dates after alignment and losing concurrent-event context.", "Choosing a favorable baseline window after seeing the result.", "Drawing a continuous line over days with no observations.", "Calling a post-event change proof that the event caused it."],
        "drill": "Align 81 facilities around a maintenance intervention. Show each facility's baseline window and post-event coverage, then recompute the cohort curve using only facilities observed through day 14.",
        "related": [prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "aggregation-grain-and-denominator", prefix + "uncertainty-and-small-sample-display", prefix + "chart-annotations-event-windows-and-causal-claims"],
    },
    {
        "slug": "interactive-chart-keyboard-focus-and-data-table-contract",
        "title": "Interactive charts: make selection work without a pointer",
        "summary": "Treat focus, selection and the data table as part of the chart's public interface.",
        "sections": [
            ("Hover is not access", "A tooltip visible only on pointer hover excludes keyboard and many touch users. Give each interactive mark a reachable focus target, a meaningful accessible name and the same detail on focus as on hover. Arrow keys can move within a series, while Home and End can jump to its bounds; publish the key rules next to the chart. Keep a visible focus indicator. [[data-visualization/accessible-color-and-text-alternatives|Color and text alternatives]] cover the static layer, but a chart with filters and selections also needs an interaction contract."),
            ("Separate focus from selection", "Focus says where keyboard input will act. Selection says which records are included in the current analysis. Do not silently change the filter merely because focus moved to another point. If Enter selects a point, announce the new selection and update the related table or summary. A selected range should survive a resize and a redraw by stable record IDs rather than pixel coordinates. [[data-visualization/linked-filters-cohort-denominators-and-selection-state|Linked filters and cohort state]] should make the selected population and denominator visible across all charts."),
            ("Avoid a thousand tab stops", "Putting every mark in the page's normal Tab sequence can make a dense chart unusable. A single chart entry point followed by arrow-key movement may be better, provided the active point's name and value are exposed, the user can exit with Tab, and the navigation order is predictable. Do not trap focus inside the plot. For large series, offer direct search, a bounded table, or a downloadable data file so a user does not have to press an arrow 4,700 times. [[data-visualization/large-series-level-of-detail-and-extrema|Large-series reduction]] must preserve access to underlying records when visual points are aggregated."),
            ("The table is a first-class view", "An accessible data table should use the same filters, units, missing-value markers and ordering as the chart. If the chart displays a sampled or binned series, identify that fact and provide a route to full records when appropriate. Do not generate a table from SVG positions; derive both views from one data model. [[data-visualization/chart-export-manifest-data-and-render-version|Export provenance]] should include the selection, filter and sort state so a shared screenshot and a CSV tell the same story. Test with only a keyboard, at narrow width, and with zoom before publication."),
        ],
        "code": '''function nextChartPoint(currentIndex, pointCount, key) {
  if (!Number.isInteger(pointCount) || pointCount < 1 ||
      !Number.isInteger(currentIndex) || currentIndex < 0 ||
      currentIndex >= pointCount) {
    throw new RangeError("chart point state is invalid");
  }
  if (key === "ArrowRight" || key === "ArrowDown") {
    return Math.min(currentIndex + 1, pointCount - 1);
  }
  if (key === "ArrowLeft" || key === "ArrowUp") {
    return Math.max(currentIndex - 1, 0);
  }
  if (key === "Home") return 0;
  if (key === "End") return pointCount - 1;
  return currentIndex;
}

const visibleRecordIds = ["depot-47", "depot-59", "depot-83"];
let focusedIndex = 0;
focusedIndex = nextChartPoint(focusedIndex, visibleRecordIds.length, "End");
if (visibleRecordIds[focusedIndex] !== "depot-83") {
  throw new Error("keyboard focus must follow chart order");
}
if (nextChartPoint(focusedIndex, visibleRecordIds.length, "ArrowRight") !== 2) {
  throw new Error("focus must stop at the last record");
}''',
        "language": "javascript",
        "cost": "A key transition takes O(1) time and space; the displayed order and accessible table require O(N) record storage for N visible points. The pure function handles movement only. The browser component must connect it to focus, accessible names, announcement text and selection state, and must retain Tab exit. If a virtualized chart reorders records, map stable IDs to the new order before restoring focus. Treat the table as the source-aligned view, not as a decorative duplicate.",
        "mistakes": ["Making hover-only tooltip content unavailable on focus and touch.", "Changing the selected cohort whenever a user merely moves focus.", "Adding every dense-series mark to the Tab order with no shortcut or data table.", "Restoring focus by pixel position after filter changes instead of stable record identity."],
        "drill": "Audit a 188-point chart using only keyboard navigation. Verify focus visibility, Enter selection, Tab exit, a synchronized table and stable record identity after a filter change.",
        "related": [prefix + "accessible-color-and-text-alternatives", prefix + "linked-filters-cohort-denominators-and-selection-state", prefix + "large-series-level-of-detail-and-extrema", prefix + "chart-export-manifest-data-and-render-version"],
    },
]

new_paths = [prefix + lesson["slug"] for lesson in lessons]
assert len(set(new_paths)) == len(new_paths) and not set(new_paths) & by_path.keys()
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
    body += f'<h2>Worked contract</h2><pre><code class="language-{lesson["language"]}">' + html.escape(lesson["code"]) + '</code></pre>'
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
        "featured": False, "sort_order": 8743 + offset, "status": "published",
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
    for start, end, heading in ((0, 3, "Distributions, fits and mapped routes"),
                                (3, 5, "Event alignment and chart interaction")):
        targets = new_paths[start:end]
        row["data"]["modules"].append({"title": heading, "lessons": targets})
        row["body"] += f'<h2>{heading}</h2><ul>' + ''.join(
            f'<li>{link(target)}</li>' for target in targets) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "box-violin-and-kde-bandwidth-for-group-comparisons": [new_paths[0]],
    prefix + "empirical-cdf-percentiles-and-tail-reading": [new_paths[0]],
    prefix + "scatterplot-overplotting-density-and-sampling-bias": [new_paths[1]],
    prefix + "asymmetric-error-bars-interval-type-and-axis-clipping": [new_paths[1]],
    prefix + "proportional-symbol-maps-area-scale-and-overlap": [new_paths[2]],
    prefix + "choropleth-rates-boundaries-and-missing-regions": [new_paths[2]],
    prefix + "time-series-gaps-calendars-and-provisional-periods": [new_paths[3]],
    prefix + "chart-annotations-event-windows-and-causal-claims": [new_paths[3]],
    prefix + "accessible-color-and-text-alternatives": [new_paths[4]],
    prefix + "linked-filters-cohort-denominators-and-selection-state": [new_paths[4]],
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
