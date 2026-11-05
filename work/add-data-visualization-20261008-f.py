"""Add five original Data Visualization lessons and reciprocal navigation."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-data-visualization-import-20261008-f.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "data-visualization/"
hub = prefix + "data-visualization-tutorial"

lessons = [
    {
        "slug": "pareto-chart-cumulative-share-and-category-boundary",
        "title": "Pareto charts: reconcile the cumulative line to the categories",
        "summary": "Sort one additive measure, retain the whole denominator and make the category boundary explicit.",
        "sections": [
            ("Start with an additive question", "A Pareto chart ranks categories by a nonnegative contribution and traces their cumulative share of the total. The measure could be incident count, repair hours or cost; those are different prioritization questions. State the unit and aggregation grain before sorting. If one ticket appears under several causes, the category totals may exceed the number of tickets. Either allocate each ticket once or label the chart as multi-tag occurrences. [[data-visualization/aggregation-grain-and-denominator|Aggregation and denominator rules]] determine whether the cumulative line has a meaningful one-hundred-percent endpoint."),
            ("Keep the total visible", "Calculate the percentage from all eligible categories, including the long tail. Grouping minor categories into Other can make a useful display, but the grouped value must equal the sum of the hidden categories and the full total must remain unchanged. A threshold line at eighty percent is only a reading aid; it does not prove an eighty-twenty distribution. Report the smallest number of categories needed to cross the chosen threshold, and name the threshold as a policy choice. [[data-visualization/stacked-bars-composition-and-changing-denominators|Composition charts]] face the same problem when categories enter or leave the frame."),
            ("Separate bar scale from share scale", "Bars encode the additive quantity, while the cumulative line encodes a percentage. These are different units, so label both axes and give the percentage line an explicit zero-to-one-hundred range. A dual-axis overlay can be compact, but lines and bars should remain legible independently. [[data-visualization/dual-axis-charts-independent-scales-and-spurious-alignment|Dual-axis integrity]] matters here because changing the right axis can make the cumulative curve look steeper. A companion table with category, contribution, cumulative contribution and share makes the chart auditable without decoding line height."),
            ("Handle ties, zeros and time changes", "When two categories have equal contributions, use a stable secondary key so repeated renders keep the same order. Zero categories may remain in the export even if the display omits them. If the chart is refreshed weekly, changing rank order is expected; do not compare bar positions as though category identity stayed fixed. [[data-visualization/bump-chart-rank-ties-membership-and-period-coverage|Rank-movement charts]] are better for that question. If the total is zero, a cumulative percentage is undefined. Show the count table and an explicit no-contributions state rather than drawing a flat zero-percent line."),
        ],
        "code": '''from math import isfinite

def pareto_rows(contributions: dict[str, float]
                ) -> list[tuple[str, float, float]]:
    if not contributions or any(not name for name in contributions):
        raise ValueError("categories must be named")
    if any(not isfinite(value) or value < 0
           for value in contributions.values()):
        raise ValueError("contributions must be finite and nonnegative")
    total = sum(contributions.values())
    if total <= 0:
        raise ValueError("a zero total has no cumulative share")
    ordered = sorted(contributions.items(), key=lambda item: (-item[1], item[0]))
    running = 0.0
    result = []
    for category, value in ordered:
        running += value
        result.append((category, value, running / total))
    return result

repair_hours = {"pump seals": 47, "sensor faults": 81,
                "cable damage": 29, "other": 43}
priority = pareto_rows(repair_hours)
assert priority[0] == ("sensor faults", 81, 0.405)
assert priority[-1][2] == 1.0''',
        "cost": "For C categories, sorting costs O(C log C) time and output takes O(C) space. Floating-point sums can round slightly for large fractional inputs; use exact decimal or integer minor units for financial totals. The example requires nonnegative additive contributions and rejects an all-zero chart. Production exports should retain category membership, source period and any Other grouping rule so cumulative shares can be reproduced.",
        "mistakes": ["Using overlapping cause tags while claiming the bars count unique incidents.", "Removing the long tail before calculating percentages.", "Treating an eighty-percent crossing as a universal law.", "Leaving the two axes unlabeled or suppressing the all-zero state."],
        "drill": "Rank 47 maintenance causes by total repair hours, then by incident count. Reconcile both denominators and explain why the first three categories differ between the two charts.",
        "related": [prefix + "aggregation-grain-and-denominator", prefix + "stacked-bars-composition-and-changing-denominators", prefix + "dual-axis-charts-independent-scales-and-spurious-alignment", prefix + "bump-chart-rank-ties-membership-and-period-coverage"],
    },
    {
        "slug": "asymmetric-error-bars-interval-type-and-axis-clipping",
        "title": "Asymmetric error bars: tell readers what each endpoint means",
        "summary": "Carry lower and upper endpoints with every estimate, and never relabel arbitrary spread as uncertainty.",
        "sections": [
            ("The interval needs a type", "An error bar may encode a standard deviation, a confidence interval, a prediction interval, an instrument tolerance or a minimum-to-maximum range. These answer different questions. Put the interval type, level where applicable, method and sample size in the chart caption. [[data-visualization/uncertainty-and-small-sample-display|Uncertainty displays]] explain why a narrow-looking interval does not automatically mean a precise individual prediction. A bar without that contract invites the reader to supply the wrong interpretation. If the calculation is model-based, identify the population and conditions under which it applies."),
            ("Keep the endpoints, not just a radius", "Some intervals are asymmetric around the estimate, especially near natural boundaries or after a nonlinear transform. Export estimate, lower and upper as three separate numbers. A renderer may ask for downward and upward distances, which can be derived from those endpoints without losing meaning. An estimate outside its own stated interval is a data error for many common interval definitions and should be stopped or explained. [[data-visualization/forecast-fan-charts-prediction-intervals-and-horizon|Forecast fan charts]] make this distinction even more important because uncertainty often widens with horizon."),
            ("Draw limits honestly", "If an endpoint falls beyond the plotted axis, do not clip it silently. Extend the axis, use a visible arrow with the endpoint value, or choose another layout. A log axis cannot display zero or negative endpoints; transforming the point and interval requires the same transformation applied to both, with the method stated. [[data-visualization/log-and-symmetric-log-scales-with-zero-values|Log and symmetric-log scales]] are not cosmetic switches. The chart should show whether a bound is physical, statistical or merely the display edge."),
            ("Compare groups without overclaiming", "Overlap of two intervals is not a general significance test, and non-overlap is not the only way to establish a difference. If the decision concerns the difference between groups, estimate and plot that difference with its own interval. [[data-visualization/diverging-bars-zero-reference-and-signed-difference|Signed differences]] put zero at the relevant comparison point. Check whether the same subjects appear in both groups; paired data require a paired calculation. For accessible reading, list each estimate and its endpoints in text, with units and the interval definition repeated where the chart may be shared alone."),
        ],
        "code": '''from math import isfinite

def errorbar_distances(rows: list[tuple[str, float, float, float]]
                       ) -> list[tuple[str, float, float, float]]:
    names = [name for name, _, _, _ in rows]
    if len(names) != len(set(names)) or any(not name for name in names):
        raise ValueError("estimate labels must be unique and nonempty")
    output = []
    for name, estimate, lower, upper in rows:
        if not all(isfinite(value) for value in (estimate, lower, upper)):
            raise ValueError("estimate and bounds must be finite")
        if not lower <= estimate <= upper:
            raise ValueError("estimate must lie within its interval")
        output.append((name, estimate, estimate - lower, upper - estimate))
    return output

service_intervals = errorbar_distances([
    ("priority queue", 81, 59, 113),
    ("standard queue", 97, 83, 149),
])
assert service_intervals == [
    ("priority queue", 81, 22, 32),
    ("standard queue", 97, 14, 52),
]''',
        "cost": "Preparing N intervals takes O(N) time and O(N) output space. The code validates geometry but cannot establish that endpoints were calculated with the right statistical method. Keep the original endpoints and method metadata even if the chart library wants only positive distances. Avoid computing an interval from a small sample with an unverified shortcut just because the renderer accepts two numbers.",
        "mistakes": ["Calling a range or standard deviation a confidence interval.", "Forcing asymmetric endpoints into equal visual arms.", "Clipping a bound at the axis edge without a marker or label.", "Inferring a group-difference test only from overlap of separate intervals."],
        "drill": "Show 59 response-time estimates with asymmetric intervals. Identify five bounds outside the current axis and revise the view without hiding those endpoints.",
        "related": [prefix + "uncertainty-and-small-sample-display", prefix + "forecast-fan-charts-prediction-intervals-and-horizon", prefix + "log-and-symmetric-log-scales-with-zero-values", prefix + "diverging-bars-zero-reference-and-signed-difference"],
    },
    {
        "slug": "qq-plots-quantile-alignment-ties-and-tail-deviation",
        "title": "Q–Q plots: compare distribution shape beyond one summary number",
        "summary": "Pair probabilities rather than row positions, state the reference distribution and inspect tail behavior separately.",
        "sections": [
            ("A quantile is an ordered position", "A Q–Q plot compares quantiles from two distributions at the same cumulative probabilities. It does not pair individual records, even if both samples have the same size. State whether the horizontal axis is an observed reference group or a theoretical distribution, and label units on both axes. [[data-visualization/empirical-cdf-percentiles-and-tail-reading|ECDF and percentile reading]] provide the underlying probability view. A line of points near a diagonal suggests broadly similar locations and spreads only if both axes use the same unit and scale; otherwise the reference may have a non-unit slope."),
            ("Choose a quantile convention", "Software packages differ in how they interpolate between observations. Write down the convention when results will be compared across tools. Repeated values produce repeated or flat stretches; adding random jitter to hide ties changes the apparent pattern. For samples of different sizes, evaluate a common probability grid rather than aligning the first observation of each sorted list. Do not include probability zero or one in a theoretical distribution whose inverse CDF is infinite there. [[data-visualization/box-violin-and-kde-bandwidth-for-group-comparisons|Box and violin views]] are useful companions when the Q–Q plot is too technical for a general audience."),
            ("Read center and tails separately", "A nearly straight center with an upward bend in the high tail may indicate more large values in the vertical sample. A shift can move all points above the reference; a scale difference can change the slope. Avoid treating visual departures as an automatic hypothesis test. With a small sample, endpoints are unstable; with a huge sample, slight departures may be practically irrelevant. [[data-visualization/uncertainty-and-small-sample-display|Sample-size uncertainty]] belongs in the caption. If the question is about service-level failures, count observations beyond a meaningful threshold as well as inspecting tail curvature."),
            ("Keep the comparison reproducible", "Filter both samples by the same eligibility and time-window rules, then report their sizes and missing-value counts. If one group contains outages and the other excludes them, the plot is comparing policies as well as distributions. [[data-visualization/chart-export-manifest-data-and-render-version|A chart export manifest]] should include filters, quantile grid, interpolation rule and transformed values. Provide a compact table of selected quantile pairs so a reader can inspect exact numbers without relying on hover or color. Never reverse the axes silently between reports."),
        ],
        "code": '''from math import isfinite

def interpolate_quantile(sorted_values: list[float], probability: float) -> float:
    if not sorted_values or not 0 <= probability <= 1:
        raise ValueError("sample and probability are required")
    index = (len(sorted_values) - 1) * probability
    low = int(index)
    high = min(low + 1, len(sorted_values) - 1)
    return sorted_values[low] + (index - low) * (sorted_values[high] - sorted_values[low])

def paired_quantiles(reference: list[float], current: list[float],
                     probabilities: list[float]) -> list[tuple[float, float, float]]:
    if not reference or not current or any(not isfinite(value)
                                            for value in reference + current):
        raise ValueError("samples must contain finite values")
    if any(not 0 <= probability <= 1 for probability in probabilities):
        raise ValueError("probabilities must be inside zero and one")
    first, second = sorted(reference), sorted(current)
    return [(p, interpolate_quantile(first, p), interpolate_quantile(second, p))
            for p in probabilities]

quantile_pairs = paired_quantiles([47, 59, 81, 97, 113],
                                 [52, 61, 83, 101, 129], [0.25, 0.5, 0.75])
assert quantile_pairs == [(0.25, 59, 61), (0.5, 81, 83), (0.75, 97, 101)]''',
        "cost": "Sorting reference and current samples of sizes A and B takes O(A log A + B log B) time; Q paired probabilities take O(Q) additional time and output space. The code uses linear interpolation at index (N minus one) times probability. It compares two empirical distributions, not a theoretical normal curve or a significance test. Preserve the method and sample sizes with the plot.",
        "mistakes": ["Pairing rows by index instead of pairing equal probabilities.", "Switching interpolation methods between reports without disclosure.", "Jittering ties until they look like genuine tail structure.", "Calling every visible bend a statistically important deviation."],
        "drill": "Compare 81 delivery-time records before and after a routing change. Plot common percentiles, report sample counts, and inspect whether the upper tail moved more than the median.",
        "related": [prefix + "empirical-cdf-percentiles-and-tail-reading", prefix + "box-violin-and-kde-bandwidth-for-group-comparisons", prefix + "uncertainty-and-small-sample-display", prefix + "chart-export-manifest-data-and-render-version"],
    },
    {
        "slug": "proportional-symbol-maps-area-scale-and-overlap",
        "title": "Proportional-symbol maps: size circles by area, not radius",
        "summary": "Declare the location meaning and value unit, then preserve zero, overlap and boundary context.",
        "sections": [
            ("A symbol has a location contract", "A circle over a map may represent a precise facility, a regional centroid or an approximate address. Those are not equivalent. State what the coordinate means and how much location precision the data support. [[data-visualization/choropleth-rates-boundaries-and-missing-regions|Choropleth maps]] color whole regions; proportional symbols encode a value at a point or chosen anchor. Do not place a regional total at a centroid without telling the reader that the circle summarizes an area. If location is sensitive, aggregate or coarsen before publication rather than relying on small marker size to conceal it."),
            ("Area should represent quantity", "If a symbol encodes a nonnegative count, its visual area should be proportional to that count. Doubling the radius multiplies area by four, exaggerating the larger value. Compute radius from the square root of value relative to a declared maximum. Use a visible reference legend with at least two example magnitudes. A zero count should remain a recorded zero, even if its circle has no area; a tiny outline or table entry may be needed to keep the location discoverable. [[data-visualization/scale-baseline-and-axis-integrity|Scale integrity]] also means fixing the size domain across maps intended for comparison."),
            ("Overlapping circles need an explicit policy", "Dense areas can hide smaller symbols under larger ones. Drawing order, opacity and zoom can all change what a reader sees. Try smaller maximum radius, outlines, clustering with disclosed counts, or an alternate ranked table. Do not let overlap remove records from the export. [[data-visualization/hexbin-density-grid-resolution-and-exposure|Hexbin density]] may be better when the question is where point events concentrate, while a proportional-symbol map is better when each point already has a meaningful aggregate. Test overlapping facilities at the closest supported zoom and on a narrow phone viewport."),
            ("Count and rate are different maps", "A large population center may dominate a count map while having a modest per-person rate. A rate can be mapped with symbol size only if the legend names its denominator and the sampling uncertainty is not buried. Often a count-sized symbol plus a separately encoded rate is too much for one map; use paired maps or a table. [[data-visualization/aggregation-grain-and-denominator|The denominator contract]] must follow the geography and period. Export ID, coordinate meaning, count, denominator, computed rate, symbol radius and suppression state, so the map can be checked without its pixels."),
        ],
        "code": '''from math import isfinite, sqrt

def area_scaled_radii(values: dict[str, float],
                      maximum_radius: float) -> dict[str, float]:
    if not isfinite(maximum_radius) or maximum_radius <= 0:
        raise ValueError("maximum radius must be positive")
    if not values or any(not place for place in values):
        raise ValueError("locations must be named")
    if any(not isfinite(value) or value < 0 for value in values.values()):
        raise ValueError("mapped values must be finite and nonnegative")
    maximum_value = max(values.values())
    if maximum_value == 0:
        return {place: 0.0 for place in values}
    return {place: maximum_radius * sqrt(value / maximum_value)
            for place, value in values.items()}

service_calls = {"north depot": 47, "south depot": 188, "west depot": 0}
radii = area_scaled_radii(service_calls, 20)
assert radii["south depot"] == 20
assert radii["north depot"] == 10
assert radii["west depot"] == 0''',
        "cost": "For N locations, finding the maximum and calculating radii takes O(N) time and O(N) output space. The code sizes nonnegative values by area and leaves geographic projection, collision handling and legend generation to the map renderer. A production map must keep one fixed reference maximum across views that readers are expected to compare; recalculating it after every filter changes apparent size.",
        "mistakes": ["Making radius proportional to count and thereby exaggerating area.", "Treating a regional centroid as an exact event location.", "Letting large symbols cover small ones without a table or overlap strategy.", "Comparing maps whose size domains were auto-scaled independently."],
        "drill": "Map 59 service depots with zero, small and large call counts. Use area-scaled circles, disclose the location meaning and produce a fixed-size legend for two reporting periods.",
        "related": [prefix + "choropleth-rates-boundaries-and-missing-regions", prefix + "scale-baseline-and-axis-integrity", prefix + "hexbin-density-grid-resolution-and-exposure", prefix + "aggregation-grain-and-denominator"],
    },
    {
        "slug": "gantt-timelines-dependencies-overlap-and-date-bounds",
        "title": "Gantt timelines: make task dates and dependencies auditable",
        "summary": "Define interval boundaries, separate planned from actual work and verify dependency logic before drawing bars.",
        "sections": [
            ("Bars are intervals", "A Gantt-style timeline uses a horizontal interval for each task. Decide whether the end timestamp is exclusive or inclusive; an end-exclusive interval allows one task to end exactly when another begins without overlap. State the time zone and whether a displayed day means a calendar day or working day. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Calendar semantics]] matter when a task crosses holidays or daylight-saving changes. Never reduce an actual timestamp to a date label before checking that its start and end still make sense."),
            ("Plan and actual are different records", "A baseline plan should remain visible after work slips. Store planned start and finish separately from actual start and finish, and mark unfinished work as open rather than inventing an actual end at today. A progress fill is a third measurement, not a substitute for dates. [[data-visualization/chart-annotations-event-windows-and-causal-claims|Annotations]] can identify approvals, outages and scope changes, but placing them near a delay does not establish causation. Report the date at which the displayed project state was captured so a screenshot can be interpreted later."),
            ("Dependencies are a graph", "A predecessor relationship means the successor has a scheduling constraint, not merely that its bar appears later on the page. Validate referenced task IDs, detect cycles and apply the chosen lag rule before rendering arrows. When a dependency is violated, show the violation rather than nudging a bar into a visually tidy position. [[data-visualization/network-graph-identity-degree-and-layout-stability|Network identity rules]] apply: stable task IDs are safer than matching labels, which may change. For a crowded plan, show a selected path and a searchable dependency table instead of drawing every connector."),
            ("Resource overlap is not always an error", "Two tasks can run concurrently on different teams; two tasks assigned to one exclusive machine cannot. Declare resource capacity before flagging overlap. A timeline sorted by start date may be useful for operations, while sorting by workstream may be better for planning; document the order so movement is not mistaken for a schedule change. [[data-visualization/linked-filters-cohort-denominators-and-selection-state|Linked selection state]] should preserve which tasks and resources are visible. Provide an accessible task table with interval, status, predecessor and resource fields, and test the mobile view where narrow bars become untappable."),
        ],
        "code": '''from datetime import datetime

def exclusive_resource_conflicts(
    tasks: list[tuple[str, str, datetime, datetime]]
) -> list[tuple[str, str, str]]:
    identifiers = [task_id for task_id, _, _, _ in tasks]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("task IDs must be unique")
    by_resource = {}
    for task_id, resource, start, end in tasks:
        if not task_id or not resource or start.tzinfo is None or end.tzinfo is None:
            raise ValueError("tasks need IDs, resources and zoned dates")
        if end <= start:
            raise ValueError("end-exclusive interval must have positive duration")
        by_resource.setdefault(resource, []).append((start, end, task_id))
    conflicts = []
    for resource, intervals in by_resource.items():
        ordered = sorted(intervals)
        for index, previous in enumerate(ordered):
            for current in ordered[index + 1:]:
                if current[0] >= previous[1]:
                    break
                conflicts.append((resource, previous[2], current[2]))
    return conflicts

from datetime import timezone
utc = timezone.utc
inspection = ("inspect-47", "crane-A", datetime(2026, 10, 8, 8, tzinfo=utc),
              datetime(2026, 10, 8, 11, tzinfo=utc))
repair = ("repair-59", "crane-A", datetime(2026, 10, 8, 10, tzinfo=utc),
          datetime(2026, 10, 8, 13, tzinfo=utc))
assert exclusive_resource_conflicts([inspection, repair]) == [
    ("crane-A", "inspect-47", "repair-59")
]
short_job = ("check-83", "crane-A", datetime(2026, 10, 8, 10, 30, tzinfo=utc),
             datetime(2026, 10, 8, 10, 45, tzinfo=utc))
assert len(exclusive_resource_conflicts([inspection, repair, short_job])) == 3''',
        "cost": "For N tasks, sorting costs O(N log N); enumerating every conflicting pair takes O(N squared) time in the worst case and O(N plus K) space for K reported pairs. When many tasks overlap, K itself can be quadratic. This check is not a dependency scheduler or a capacity planner. Validate dependency references and cycles separately before publishing arrows, and preserve planned and actual intervals in the export.",
        "mistakes": ["Mixing inclusive and exclusive task end dates.", "Overwriting the original plan with actual dates.", "Drawing dependency arrows without validating task IDs or cycles.", "Calling every overlap an error without a resource-capacity rule."],
        "drill": "Plot 47 maintenance tasks with planned and actual dates, two exclusive machines and three predecessor chains. Flag interval conflicts and an unfinished task without assigning it a fake actual end.",
        "related": [prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "chart-annotations-event-windows-and-causal-claims", prefix + "network-graph-identity-degree-and-layout-stability", prefix + "linked-filters-cohort-denominators-and-selection-state"],
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
        "featured": False, "sort_order": 8738 + offset, "status": "published",
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
    for start, end, heading in ((0, 3, "Cumulative totals, uncertainty and quantiles"),
                                (3, 5, "Mapped symbols and task timelines")):
        targets = new_paths[start:end]
        row["data"]["modules"].append({"title": heading, "lessons": targets})
        row["body"] += f'<h2>{heading}</h2><ul>' + ''.join(
            f'<li>{link(target)}</li>' for target in targets) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "aggregation-grain-and-denominator": [new_paths[0], new_paths[3]],
    prefix + "dual-axis-charts-independent-scales-and-spurious-alignment": [new_paths[0]],
    prefix + "uncertainty-and-small-sample-display": [new_paths[1], new_paths[2]],
    prefix + "forecast-fan-charts-prediction-intervals-and-horizon": [new_paths[1]],
    prefix + "empirical-cdf-percentiles-and-tail-reading": [new_paths[2]],
    prefix + "choropleth-rates-boundaries-and-missing-regions": [new_paths[3]],
    prefix + "hexbin-density-grid-resolution-and-exposure": [new_paths[3]],
    prefix + "time-series-gaps-calendars-and-provisional-periods": [new_paths[4]],
    prefix + "network-graph-identity-degree-and-layout-stability": [new_paths[4]],
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
