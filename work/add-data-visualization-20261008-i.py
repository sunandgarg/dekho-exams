"""Add four original visualization lessons with reciprocal site links."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-data-visualization-import-20261008-i.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "data-visualization/"
hub = prefix + "data-visualization-tutorial"

lessons = [
    {
        "slug": "survival-curves-risk-sets-censoring-and-tail-support",
        "title": "Survival curves: show who remains at risk after each event",
        "summary": "Build a step curve from observed events, keep censoring visible and stop trusting a thin tail.",
        "sections": [
            ("Define the event and the clock", "A survival curve estimates the share of a starting cohort that has not yet experienced a specified event by elapsed time. A device-failure chart, for instance, needs a clear start such as commissioning and an event such as first unrecoverable shutdown. Mixing calendar dates with elapsed operating days changes the risk set. Units matter too: a device observed for 47 calendar days but active for 31 operating days is not interchangeable with one observed continuously. [[data-visualization/event-aligned-time-series-baseline-windows-and-missing-periods|Event-aligned time series]] can show measurements around a milestone, while a survival curve asks when the first event occurs. Decide how replacement devices, repeat failures and delayed entry will be treated before fitting the curve; the simple right-censored calculation below assumes every device enters at elapsed time zero."),
            ("A censor mark is not a failure", "Right censoring means observation ended without the event being seen. A study cutoff, withdrawal or lost sensor feed can create one, but those reasons need separate counts because their relationship to failure risk may differ. The Kaplan–Meier step drops only when events occur. A censor at time 59 leaves the height unchanged while reducing the group available for later event times. When events and censors share a recorded time, declare whether events are processed before same-time censors; the code uses that convention. Put the censor marks on the curve and provide an at-risk table at chosen time ticks. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Missing periods]] are a different data problem: do not silently turn an unobserved failure time into a clean censor without checking what was actually known."),
            ("Read the tail against its denominator", "A flat tail can look reassuring even when only two devices remain under observation. Show the number at risk at regular, meaningful intervals and consider ending the displayed curve where support becomes too sparse for the decision. Do not stretch the last estimated step into a guarantee beyond follow-up. If two cohorts enter in different years or face different servicing policies, their curves are descriptive until the cohort definitions and confounding are reviewed. [[data-visualization/uncertainty-and-small-sample-display|Small-sample uncertainty]] belongs beside the estimate, and a confidence band needs a stated method. An ordinary percent-without-failure line is not equivalent when follow-up lengths differ because it treats early withdrawals as though they had complete observation."),
            ("Keep the underlying event ledger", "The plot is a compression of the event ledger, not a substitute for it. Preserve device ID, entry time, exit time, event flag, censor reason, cohort, and data-cutoff date. Reconcile the at-risk count before each event: prior risk minus prior events and censors must equal the next risk count. If failures can be precluded by a different event, a conventional one-event survival curve may answer the wrong question; define a competing-event analysis instead. [[data-visualization/empirical-cdf-percentiles-and-tail-reading|Empirical CDFs]] are useful when event times are fully observed, but they do not automatically handle censoring. Export a table of each step time, event count, censor count, risk count and estimated survival so a reader can audit every drop without estimating coordinates from pixels."),
        ],
        "code": '''from collections import Counter
from math import isfinite

def device_survival_steps(records: list[tuple[str, float, bool]]):
    identifiers = [device_id for device_id, _, _ in records]
    if len(identifiers) != len(set(identifiers)) or any(not item for item in identifiers):
        raise ValueError("device IDs must be unique and nonempty")
    if any(not isfinite(duration) or duration < 0 or type(failed) is not bool
           for _, duration, failed in records):
        raise ValueError("duration and event flags must be valid")
    events = Counter(duration for _, duration, failed in records if failed)
    censors = Counter(duration for _, duration, failed in records if not failed)
    risk_count, survival, steps = len(records), 1.0, []
    for duration in sorted(events.keys() | censors.keys()):
        failed_count = events[duration]
        censored_count = censors[duration]
        survival *= 1 - failed_count / risk_count
        steps.append((duration, risk_count, failed_count,
                      censored_count, survival))
        risk_count -= failed_count + censored_count
    return steps

depot_devices = [
    ("station-47", 3, True), ("station-59", 4, False),
    ("station-83", 4, True), ("station-97", 7, False),
]
depot_steps = device_survival_steps(depot_devices)
assert depot_steps[0] == (3, 4, 1, 0, 0.75)
assert depot_steps[1] == (4, 3, 1, 1, 0.5)
assert depot_steps[-1][-1] == 0.5''',
        "language": "python",
        "cost": "Counting and sorting N event or censor records takes O(N log N) time and O(N) space. The function returns every observed exit time so censors can be marked even when the step height stays level. It assumes entry at time zero, one terminal event, and a declared event-before-censor tie rule; it does not calculate confidence limits or correct informative censoring. Validate the event ledger and at-risk table before drawing smooth-looking output.",
        "mistakes": ["Treating a censored record as an observed failure or as complete follow-up.", "Omitting at-risk counts while interpreting the last flat segment.", "Combining elapsed operating time with calendar time on one axis.", "Comparing cohorts without checking different entry policies, follow-up windows or censor reasons."],
        "drill": "Audit 47 devices across two installation cohorts. Print the risk set at months 0, 6, 12 and 18, mark withdrawals, then explain where the tail no longer supports a useful comparison.",
        "related": [prefix + "event-aligned-time-series-baseline-windows-and-missing-periods", prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "uncertainty-and-small-sample-display", prefix + "empirical-cdf-percentiles-and-tail-reading"],
    },
    {
        "slug": "mosaic-plots-joint-area-conditional-rate-and-empty-cells",
        "title": "Mosaic plots: make cell area match the underlying count",
        "summary": "Use widths and conditional heights to expose how two categorical variables share one total.",
        "sections": [
            ("Choose a denominator before drawing tiles", "A two-way mosaic plot partitions one rectangle by a contingency table. Each first-category column gets width proportional to its count in the full data set. Within that column, second-category tile heights represent conditional shares. Multiplying width by height yields the cell's share of the grand total. That area contract is the point of the chart. If the column widths are all equal instead, the display answers a different question: it emphasizes within-group composition and conceals unequal group sizes. [[data-visualization/stacked-bars-composition-and-changing-denominators|Stacked bars]] are often easier to read when exact conditional rates are the primary comparison, while [[data-visualization/treemap-hierarchy-leaf-sums-and-area-comparison|treemaps]] use area for hierarchical totals rather than a two-way cross-classification."),
            ("Declare the table grain", "Count one unit only once in the table unless the chart explicitly represents events rather than entities. If a shipment can appear in several outcome categories, a standard contingency table is not valid until a mutually exclusive rule is chosen. A missing outcome is its own category or an explicit exclusion; quietly dropping it changes every tile's area. [[data-visualization/aggregation-grain-and-denominator|Aggregation grain and denominator]] should be fixed upstream. Record the category order even if one group has a zero count, and distinguish a true zero cell from a category never collected. Reconcile each column subtotal with source records before calculating widths, then reconcile all columns to the grand total. A plot that looks rectangular can still be numerically wrong."),
            ("Read association without mistaking size for rate", "A wider group contributes more observations, while a taller tile within that group represents a larger conditional share. Readers often compare tile heights across groups and forget the width, or compare areas when the question is only about rates. Label both count and within-group percentage in a companion table. If a tiny tile cannot hold text, put the label outside or leave it to an accessible table rather than enlarging the tile. [[data-visualization/heatmap-missing-cells-and-color-domain|Heatmaps]] can encode a rate in color, but their equal-size cells do not show count automatically. Do not imply statistical significance from a striking mosaic pattern; sampling design, uncertainty and multiple subgroup inspections remain separate questions."),
            ("Keep order and coverage stable", "A mosaic is more legible with a limited number of well-defined categories. Many thin columns or slivers make the visual fragile on phones and at high zoom. Sort categories by a declared business order, not by whichever tile creates the strongest pattern in each filter state. If a dashboard filter removes units, recompute column totals and display the new grand total; a stale denominator can make area and labels disagree. [[data-visualization/linked-filters-cohort-denominators-and-selection-state|Linked filters]] should expose which cohort is selected. Export the exact cross-tabulation with count, row total, grand total, conditional percentage and excluded count so the visible geometry can be independently reconstructed."),
        ],
        "code": '''def mosaic_tiles(table: dict[str, dict[str, int]],
                 outcomes: list[str]):
    if not table or not outcomes or len(outcomes) != len(set(outcomes)):
        raise ValueError("groups and ordered outcomes are required")
    if any(set(cells) != set(outcomes) for cells in table.values()):
        raise ValueError("every group needs every outcome, including zeros")
    if any(type(count) is not int or count < 0
           for cells in table.values() for count in cells.values()):
        raise ValueError("counts must be nonnegative integers")
    group_totals = {group: sum(cells.values()) for group, cells in table.items()}
    if any(total == 0 for total in group_totals.values()):
        raise ValueError("empty groups need a separate missing-data state")
    grand_total = sum(group_totals.values())
    tiles, left = [], 0.0
    for group, cells in table.items():
        right = left + group_totals[group] / grand_total
        bottom = 0.0
        for outcome in outcomes:
            top = bottom + cells[outcome] / group_totals[group]
            tiles.append((group, outcome, left, right, bottom, top,
                          cells[outcome]))
            bottom = top
        left = right
    return tiles

review_counts = {
    "early shift": {"accepted": 47, "returned": 13},
    "late shift": {"accepted": 20, "returned": 20},
}
review_tiles = mosaic_tiles(review_counts, ["accepted", "returned"])
early_accepted = review_tiles[0]
assert abs((early_accepted[3] - early_accepted[2]) *
           (early_accepted[5] - early_accepted[4]) - 0.47) < 1e-12
assert review_tiles[-1][-1] == 20''',
        "language": "python",
        "cost": "For G groups and K outcome categories, validation and tile construction take O(GK) time and O(GK) output space. The positions are normalized to a unit square; the first tile covers 47 percent of the area because 47 of 100 reviewed shipments fall in that cell. Floating-point boundaries are drawing coordinates, not replacement counts. Keep the integer table available for labels and audit exports.",
        "mistakes": ["Making every group equally wide while claiming tile area represents total count.", "Dropping unknown outcomes without updating the denominator and exclusion note.", "Enlarging tiny tiles to fit labels, which breaks the area contract.", "Reading an attractive pattern as evidence of association without examining uncertainty or sampling."],
        "drill": "Cross-tabulate 83 inspected shipments by shift and disposition, including an unknown disposition. Reconcile the grand total and verify that each tile area equals its cell count divided by 83.",
        "related": [prefix + "aggregation-grain-and-denominator", prefix + "stacked-bars-composition-and-changing-denominators", prefix + "treemap-hierarchy-leaf-sums-and-area-comparison", prefix + "heatmap-missing-cells-and-color-domain"],
    },
    {
        "slug": "ternary-plots-closed-compositions-zero-parts-and-total-loss",
        "title": "Ternary plots: preserve the total behind a three-part composition",
        "summary": "Map three nonnegative parts into a triangle only after defining what the whole contains.",
        "sections": [
            ("The triangle represents a closed whole", "A ternary plot places three nonnegative components of one whole at a point inside a triangle. A point near a corner has a large share of the component named at that corner. The chart requires a real closure rule: if raw materials, labor and transport make only 83 percent of a project budget, normalizing those three to 100 percent silently discards the remainder. Add a declared other category, change the question or use a different display. [[data-visualization/stacked-bars-composition-and-changing-denominators|Stacked composition]] is easier when the reader needs several exact shares. A ternary plot earns its space when the trade-off among exactly three parts is itself the question and the total is comparable or available elsewhere."),
            ("Keep the raw total next to normalized shares", "Closure removes scale. A project costing 47 units and another costing 470 can occupy the same triangle point when their ratios match. Preserve total cost as a table column, size encoding with a disclosed area scale, or a linked separate chart. Do not let marker color quietly reintroduce a fourth variable without a readable legend and accessible alternative. [[data-visualization/proportional-symbol-maps-area-scale-and-overlap|Area-scaled markers]] explain why marker radius is not proportional to magnitude. Zeros are legitimate triangle-edge cases, whereas negative components or a zero total cannot be mapped as shares. Before plotting, decide whether a recorded zero is a real absence, a rounded small positive amount or missing data; these cases should not share one symbol."),
            ("A trend can be a denominator effect", "If one component's share rises, at least one other share must fall even when its raw amount is unchanged. That closure constraint can manufacture apparent negative relationships between parts. Compare raw components and totals before attributing a movement to a process change. [[data-visualization/correlation-heatmap-pairwise-coverage-and-ordering|Correlation heatmaps]] on closed shares need special care for exactly this reason. If several periods are shown, connect points only when each project ID and period order are stable. Label direction and elapsed time; a long geometric move is a large change in composition, not necessarily a large change in dollars or units. The triangle should not be used as a causal diagram."),
            ("Fix corners, orientation and precision", "Choose a component order and corner labeling once for every panel and export. Reordering corners rotates the apparent story even when the numbers are unchanged. Use meaningful tick spacing and consistent normalization, preferably with a table reporting the original values and resulting shares to a stated precision. When values are rounded, their displayed shares may sum to 99.9 or 100.1; keep full precision for coordinates and explain display rounding. [[data-visualization/parallel-coordinates-normalization-axis-order-and-brushing|Parallel coordinates]] offer another way to inspect several components without enforcing a three-part closure. For accessible interaction, keyboard focus should reveal all three components, the raw total and the record ID, not just an unlabeled point location."),
        ],
        "code": '''from math import isfinite, sqrt

def triangle_positions(records: list[tuple[str, float, float, float]]):
    identifiers = [record_id for record_id, _, _, _ in records]
    if len(identifiers) != len(set(identifiers)) or any(not item for item in identifiers):
        raise ValueError("composition IDs must be unique and nonempty")
    points = []
    for record_id, materials, labor, transport in records:
        parts = (materials, labor, transport)
        if any(not isfinite(part) or part < 0 for part in parts):
            raise ValueError("components must be finite and nonnegative")
        total = sum(parts)
        if total <= 0:
            raise ValueError("a zero total has no composition")
        x_position = (labor + transport / 2) / total
        y_position = (sqrt(3) / 2) * transport / total
        points.append((record_id, x_position, y_position, total,
                       tuple(part / total for part in parts)))
    return points

budget_points = triangle_positions([
    ("depot-47", 47, 31, 22),
    ("depot-59", 94, 62, 44),
])
assert abs(budget_points[0][1] - 0.42) < 1e-12
assert budget_points[0][1:3] == budget_points[1][1:3]
assert budget_points[0][3] == 100
assert budget_points[1][3] == 200''',
        "language": "python",
        "cost": "Validating and normalizing N compositions costs O(N) time and O(N) output space. The two budgets share coordinates because their proportions match, yet their totals differ by a factor of two. The function supplies plotting coordinates for corners materials-left, labor-right and transport-top; it does not determine whether the three categories truly exhaust the business total. That semantic check belongs at the data boundary.",
        "mistakes": ["Normalizing an incomplete three-part subset without naming the omitted share.", "Comparing triangle distance as though it represented absolute amount.", "Treating closure-induced negative relationships as independent evidence.", "Changing corner order between panels or hiding raw totals after normalization."],
        "drill": "Plot 59 project budgets using three exhaustive cost components. Identify any zero-total or negative record, retain the raw totals and explain why two projects with identical shares can require different spending decisions.",
        "related": [prefix + "stacked-bars-composition-and-changing-denominators", prefix + "proportional-symbol-maps-area-scale-and-overlap", prefix + "correlation-heatmap-pairwise-coverage-and-ordering", prefix + "parallel-coordinates-normalization-axis-order-and-brushing"],
    },
    {
        "slug": "cusum-charts-reference-shifts-reset-and-alert-calibration",
        "title": "CUSUM charts: accumulate small departures from a stable target",
        "summary": "Define the reference process, update rule and alert threshold before reading a rising trace.",
        "sections": [
            ("A cumulative trace needs a frozen baseline", "A cumulative-sum chart can detect a sustained small departure that a point-by-point threshold misses. Start with a process metric measured at consistent intervals and a target estimated from an independent, stable baseline period. A cumulative sum of raw values will drift simply because the metric is positive; subtract the target and a reference allowance before accumulating evidence of an upward shift. Use a separate lower trace for downward shifts. [[data-visualization/p-charts-varying-denominators-and-process-baselines|P charts]] handle varying binomial denominators; their rate and limits should not be replaced by a CUSUM of unadjusted percentages. If observation precision or exposure changes across periods, standardize or model that change before applying a fixed CUSUM rule."),
            ("The allowance and threshold are design choices", "In a tabular upper CUSUM, each new value adds its deviation from the target minus an allowance, and negative running totals reset to zero. A lower CUSUM mirrors the logic for downward movement. The allowance controls the size of shift the chart is tuned to notice; the decision threshold controls when an alert is raised. Neither number is a universal constant. Calibrate them against the operational false-alarm rate and detection delay the team can tolerate, using an appropriate baseline model. [[data-visualization/uncertainty-and-small-sample-display|Uncertainty displays]] help explain how noisy short runs can be. The worked numbers below demonstrate mechanics only and must not be copied as an alert policy for another process."),
            ("A signal is a review trigger", "Mark the exact first threshold crossing on the chart. Keep every earlier point and the zero resets visible; truncating the history can make the signal look instantaneous. An alert says the observed sequence is unusual under the chosen reference model, not that a particular maintenance event caused it. [[data-visualization/chart-annotations-event-windows-and-causal-claims|Event annotations]] need timestamps and a caution about causal interpretation. If a baseline is re-estimated after every signal, the chart can absorb the very drift it was intended to detect. Version the target, allowance, threshold and any planned reset date. When a legitimate process change establishes a new operating state, start a documented new chart rather than silently splicing scales."),
            ("Audit the measurement pipeline", "A sustained run of delayed, duplicated or missing readings can resemble a process shift. Validate sampling cadence, units, sensor identity and data revision status before interpreting the trace. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Time-series gaps]] must remain gaps or be handled by an explicit rule; inserting zero will push a lower trace down for the wrong reason. Serial correlation also changes the false-alarm behavior of a rule calibrated for independent observations. Keep an export with period ID, raw reading, target version, upper and lower cumulative values, and alert state. [[data-visualization/chart-export-manifest-data-and-render-version|Chart manifests]] make the calculation reproducible after a dashboard or threshold update."),
        ],
        "code": '''from math import isfinite

def process_shift_trace(readings: list[float], target: float,
                        allowance: float, threshold: float):
    if (not all(isfinite(value) for value in [*readings, target,
                                               allowance, threshold])
            or allowance < 0 or threshold <= 0):
        raise ValueError("finite readings, nonnegative allowance and positive threshold required")
    upper = lower = 0.0
    trace = []
    for period_index, reading in enumerate(readings, start=1):
        upper = max(0.0, upper + reading - target - allowance)
        lower = max(0.0, lower + target - reading - allowance)
        trace.append((period_index, upper, lower,
                      upper >= threshold, lower >= threshold))
    return trace

depot_trace = process_shift_trace([48, 49, 52, 54],
                                  target=47, allowance=2, threshold=8)
assert depot_trace[:2] == [(1, 0.0, 0.0, False, False),
                           (2, 0.0, 0.0, False, False)]
assert depot_trace[-1] == (4, 8.0, 0.0, True, False)''',
        "language": "python",
        "cost": "Updating N readings takes O(N) time and O(N) space when the full trace is retained; an online alarm needs O(1) state. The sequence reaches the illustrative upper threshold only after two larger readings accumulate. No false-alarm guarantee follows from those values. Choose target, allowance and threshold from the real measurement process and validate assumptions such as independence or expected exposure before production alerts.",
        "mistakes": ["Using a target recomputed from the same drifting window being monitored.", "Copying example allowance and threshold values into a live alert without calibration.", "Filling missing readings with zero or treating duplicate periods as independent evidence.", "Calling the first alert proof of a specific cause rather than a trigger for investigation."],
        "drill": "Monitor 47 daily throughput readings. Freeze a baseline version, compare an upper and lower trace, record every reset, and test how one missing day changes the alert when it is omitted versus incorrectly filled with zero.",
        "related": [prefix + "p-charts-varying-denominators-and-process-baselines", prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "chart-annotations-event-windows-and-causal-claims", prefix + "chart-export-manifest-data-and-render-version"],
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
        "featured": False, "sort_order": 8753 + offset, "status": "published",
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
    for start, end, heading in ((0, 2, "Event and category evidence"),
                                (2, 4, "Compositions and process signals")):
        targets = new_paths[start:end]
        row["data"]["modules"].append({"title": heading, "lessons": targets})
        row["body"] += f'<h2>{heading}</h2><ul>' + ''.join(
            f'<li>{link(target)}</li>' for target in targets) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "event-aligned-time-series-baseline-windows-and-missing-periods": [new_paths[0]],
    prefix + "empirical-cdf-percentiles-and-tail-reading": [new_paths[0]],
    prefix + "stacked-bars-composition-and-changing-denominators": [new_paths[1], new_paths[2]],
    prefix + "treemap-hierarchy-leaf-sums-and-area-comparison": [new_paths[1]],
    prefix + "aggregation-grain-and-denominator": [new_paths[1]],
    prefix + "parallel-coordinates-normalization-axis-order-and-brushing": [new_paths[2]],
    prefix + "correlation-heatmap-pairwise-coverage-and-ordering": [new_paths[2]],
    prefix + "p-charts-varying-denominators-and-process-baselines": [new_paths[3]],
    prefix + "time-series-gaps-calendars-and-provisional-periods": [new_paths[0], new_paths[3]],
    prefix + "chart-annotations-event-windows-and-causal-claims": [new_paths[3]],
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
