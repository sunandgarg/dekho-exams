"""Add another set of original Data Visualization lessons."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-data-visualization-import-20261008-d.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "data-visualization/"
hub = prefix + "data-visualization-tutorial"

lessons = [
    {
        "slug": "hexbin-density-grid-resolution-and-exposure",
        "title": "Hexbin density: count overlapping points without hiding exposure",
        "summary": "Declare coordinates, bin resolution and whether color means count or rate.",
        "sections": [
            ("Overplotting is a counting problem", "When thousands of marks overlap, a dark patch can reflect drawing order or opacity rather than a trustworthy count. Binning makes the count explicit. A hexagonal grid offers a compact neighborhood shape, but it still imposes a resolution and origin. Record both. [[data-visualization/scatterplot-overplotting-density-and-sampling-bias|Overplotting and sampling bias]] explain why a random sample may help inspection but cannot silently replace total-density reporting. Show how many points survived filtering and coordinate validation before any bins are painted."),
            ("Coordinate units determine the grid", "A grid in longitude and latitude degrees does not represent equal ground area across latitudes. For a geographic density question, project coordinates into an appropriate metric system before choosing cell width. If this is only a relative screen-space view, say so and avoid claims about area-normalized risk. Keep projection, extent and grid origin fixed across time panels. Otherwise unchanged points may fall into different cells. [[data-visualization/choropleth-rates-boundaries-and-missing-regions|Geographic rate maps]] have a related denominator problem."),
            ("Count and exposure answer different questions", "A cell with 81 incidents may cover 810,000 journeys; a cell with 47 may cover 4,700. Count highlights workload, while incidents per journey describe a different quantity. Preserve zero-exposure cells separately from zero-incident cells. Dividing by drawn polygon area does not produce a population risk. [[data-visualization/aggregation-grain-and-denominator|The denominator contract]] must match the decision. If sparse cells are suppressed for privacy, label that suppression and retain a public aggregate total rather than pretending the hidden cells are zero."),
            ("Test resolution and edge effects", "A coarse grid can merge two nearby clusters; a fine grid can fragment one. Inspect multiple declared widths while keeping the color domain comparable. Points exactly on the extent edge need a documented inclusion rule. Export each bin's identifier, center or polygon, count, exposure and suppression state so the chart can be checked without its pixels. [[data-visualization/chart-export-manifest-data-and-render-version|The export manifest]] should retain projection, extent, width and origin. An accessible summary should identify the highest-count cells and explain the unit encoded by color."),
        ],
        "code": '''from collections import Counter
from math import floor, isfinite

def audit_spatial_counts(points: list[tuple[float, float]],
                         cell_width: float) -> Counter[tuple[int, int]]:
    if not isfinite(cell_width) or cell_width <= 0:
        raise ValueError("cell width must be positive")
    if any(not isfinite(x) or not isfinite(y) for x, y in points):
        raise ValueError("coordinates must be finite")
    return Counter((floor(x / cell_width), floor(y / cell_width))
                   for x, y in points)

depot_coordinates = [(47.2, 81.6), (47.7, 81.1), (59.4, 81.5)]
audit = audit_spatial_counts(depot_coordinates, 4)
assert audit[(11, 20)] == 2 and sum(audit.values()) == 3''',
        "cost": "This rectangular audit grid takes O(N) expected time and O(B) space for N points and B occupied bins. It checks count conservation before passing projected coordinates to a hexbin renderer; rectangular cells and hexagons do not share identifiers. The renderer decides hexagon placement and edge rules. A real map also needs projection and exposure joins versioned with its bin table. Preserve input and retained counts to detect losses.",
        "mistakes": ["Calling raw incident counts a risk rate.", "Using degree-based cells as if they had equal ground area.", "Changing grid extent between periods and interpreting bin movement as behavior change.", "Hiding suppressed or zero-exposure cells as ordinary zero counts."],
        "drill": "Bin 810 projected service calls at two widths. Reconcile counts to input, attach journey exposure by cell and compare the busiest cell with the highest incident-rate cell.",
        "related": [prefix + "scatterplot-overplotting-density-and-sampling-bias", prefix + "choropleth-rates-boundaries-and-missing-regions", prefix + "aggregation-grain-and-denominator", prefix + "chart-export-manifest-data-and-render-version"],
    },
    {
        "slug": "diverging-bars-zero-reference-and-signed-difference",
        "title": "Diverging bars: put signed differences on one shared zero",
        "summary": "Choose a meaningful reference, keep a shared scale and retain both values behind every gap.",
        "sections": [
            ("The reference is the argument", "A diverging bar begins at zero and extends according to a signed difference. That zero must mean something: actual minus plan, current minus prior, or group A minus group B. Put the formula and unit near the axis. A negative result may mean a shortfall, a benefit or simply a lower measurement. Label the groups rather than assuming red always means bad. [[data-visualization/scale-baseline-and-axis-integrity|A shared baseline]] lets readers compare directions."),
            ("Keep both operands available", "A difference of 34 could arise from 47 versus 81 or 4,700 versus 4,734. The same bar length does not reveal operational scale. Tooltips and exports should contain both values, the reference version and any denominator used to make a rate. If teams differ sharply in size, a rate difference may answer the comparison better than counts. [[data-visualization/aggregation-grain-and-denominator|Denominator design]] precedes color choice. A gap based on a missing or zero denominator is undefined, not a zero-length bar."),
            ("Sort for the decision", "Ranking by signed difference groups shortfalls; ranking by absolute difference surfaces the largest departures in either direction. State the sort key. Do not reorder every small multiple independently if the reader must follow the same entity through time. [[data-visualization/small-multiples-shared-scales-and-facet-order|Shared facet order]] preserves identity. For equal comparison of positive and negative magnitudes, set a symmetric numeric domain around zero. An asymmetric domain can compress one side. Never clip a long bar without an exact value label and visible break."),
            ("Expose uncertainty", "A small bar near zero may be noise rather than stable movement. For estimates, add an interval marker and explain whether it crosses zero. The chart should not declare every positive value a success. A materiality threshold belongs on the plot only when its rule is documented and consistent across entities. [[data-visualization/uncertainty-and-small-sample-display|Small-sample uncertainty]] matters most near the boundary. Include a text alternative listing signed gaps, both operands and the largest departures on either side."),
        ],
        "code": '''from math import isfinite

def signed_plan_gaps(rows: list[tuple[str, float, float]]
                     ) -> list[tuple[str, float, float, float]]:
    names = [name for name, _, _ in rows]
    if len(names) != len(set(names)) or any(not name for name in names):
        raise ValueError("entity names must be unique and nonempty")
    if any(not isfinite(actual) or not isfinite(plan)
           for _, actual, plan in rows):
        raise ValueError("measurements must be finite")
    return sorted(((name, actual, plan, actual - plan)
                   for name, actual, plan in rows), key=lambda item: item[3])

depot_gaps = signed_plan_gaps([("north", 47, 81),
                              ("south", 113, 97),
                              ("west", 59, 59)])
assert depot_gaps[0] == ("north", 47, 81, -34)
assert depot_gaps[-1][3] == 16''',
        "cost": "For N entities, computing differences takes O(N) time and sorting takes O(N log N) time with O(N) output space. Reusing order across facets avoids repeated sort decisions, though it may make one panel less locally ranked. The example calculates absolute signed differences. A rate gap needs validated denominators and a declared unit before plotting. A chart library's autoscale should not override a specified symmetric domain.",
        "mistakes": ["Coloring negative bars as bad when lower is preferable.", "Discarding the actual and plan values after calculating a gap.", "Using unequal left and right scales to exaggerate one direction.", "Confusing percentage-point change with percent change."],
        "drill": "Plot 47 depots' actual-minus-plan gaps. Sort by signed difference, show both operands, then compare that ranking to a rate-gap view based on eligible volume.",
        "related": [prefix + "scale-baseline-and-axis-integrity", prefix + "aggregation-grain-and-denominator", prefix + "small-multiples-shared-scales-and-facet-order", prefix + "uncertainty-and-small-sample-display"],
    },
    {
        "slug": "waterfall-chart-bridge-reconciliation-and-subtotals",
        "title": "Waterfall charts: reconcile every step to the closing total",
        "summary": "Model changes as signed contributions, and keep subtotals distinct from new contributions.",
        "sections": [
            ("A bridge is an equation", "A waterfall begins with an opening amount, applies signed changes in a declared order, and ends with a closing amount. Every floating bar implies a cumulative level before and after its step. The diagram is useful when the question is why a total changed, but the numbers must reconcile exactly. An unexplained residual should be shown as a named residual, not hidden in the last bar. [[data-visualization/aggregation-grain-and-denominator|The aggregation grain]] must stay stable: summing transaction-level changes and mixing them with account-level balances can double count."),
            ("Separate a subtotal from a change", "A subtotal displays the running balance at a checkpoint; it does not add to that balance again. A renderer may call an item relative, absolute or total, but the source data should declare its semantic role independently of the library. Recalculate every subtotal from the opening amount and preceding changes. If a reported checkpoint disagrees, stop the publication pipeline or show the discrepancy explicitly. [[data-visualization/chart-export-manifest-data-and-render-version|The export contract]] should keep item role, signed amount, running level and source period."),
            ("Choose order without inventing causality", "Steps may be ordered by business process, chronology or contribution magnitude. A magnitude order helps show large drivers but can imply a process order that never occurred; label it as a decomposition rather than an event timeline. If two drivers overlap, their estimated contributions may not be independently additive. State the allocation rule before drawing. [[data-visualization/chart-annotations-event-windows-and-causal-claims|Annotations and causal claims]] require more evidence than a visually convenient bridge. For an exact ledger, preserve source transaction IDs or reconciliation batches."),
            ("Read signed values and scale", "A decrease may be good or bad depending on the metric. Use text and bar direction as well as color. A zero step should remain in the export but can be collapsed in a crowded display if the omission is stated. If the starting balance is negative, make zero visible and verify connectors still show the true running level. [[data-visualization/diverging-bars-zero-reference-and-signed-difference|Signed comparison charts]] are better when the task is ranking independent gaps rather than explaining one total. Test refunds, reversals, missing steps and rounding before release."),
        ],
        "code": '''from decimal import Decimal

def reconcile_bridge(opening: Decimal,
                     steps: list[tuple[str, Decimal]],
                     expected_close: Decimal) -> list[tuple[str, Decimal]]:
    if len({name for name, _ in steps}) != len(steps):
        raise ValueError("step names must be unique")
    running = opening
    levels = [("opening", running)]
    for name, change in steps:
        running += change
        levels.append((name, running))
    if running != expected_close:
        raise ValueError("bridge does not reconcile")
    return levels

bridge = reconcile_bridge(
    Decimal("810.00"),
    [("new contracts", Decimal("147.00")),
     ("returns", Decimal("-59.00")),
     ("credits", Decimal("-81.00"))],
    Decimal("817.00"))
assert bridge[-1] == ("credits", Decimal("817.00"))''',
        "cost": "For S changes, reconciliation is O(S) time and O(S) output space. The currency example uses Decimal so binary floating-point rounding does not create a false residual. The code validates the exact closing balance but does not check whether step categories overlap or whether source ledger rows were omitted; those are upstream accounting controls. A large waterfall often needs grouped minor steps, with an auditable rollup behind the group.",
        "mistakes": ["Adding a subtotal as though it were another contribution.", "Forcing the final bar to the reported close despite a residual.", "Mixing time periods or grains in one bridge.", "Using color alone to identify increase and decrease."],
        "drill": "Explain a move from 810 to 817 units with three signed steps. Then remove the credit step and verify reconciliation fails. Add a subtotal after returns without changing the closing amount.",
        "related": [prefix + "aggregation-grain-and-denominator", prefix + "chart-export-manifest-data-and-render-version", prefix + "chart-annotations-event-windows-and-causal-claims", prefix + "diverging-bars-zero-reference-and-signed-difference"],
    },
    {
        "slug": "bullet-chart-target-bands-and-kpi-context",
        "title": "Bullet charts: show a measure, target and performance bands honestly",
        "summary": "Keep KPI units and band thresholds explicit instead of compressing context into a gauge.",
        "sections": [
            ("One axis carries one measure", "A bullet chart places an observed value and a target on a shared quantitative scale, often with qualitative background bands. It fits a compact dashboard, but the target and bands must use the same unit and period as the observation. A monthly result against an annual target is not meaningful unless the annual target is allocated by a stated rule. [[data-visualization/scale-baseline-and-axis-integrity|Baseline and axis integrity]] matter even in a small card. Show the observed number and target in text so the graphic is not the sole carrier of the result."),
            ("Treat bands as policy, not decoration", "Labels such as below, meets and exceeds imply thresholds selected for a reason. Store the numeric band boundaries and their version. If leadership changes a target, historical cards should either retain the old policy or clearly restate history under the new one. A band extending from 47 to 81 is not an uncertainty interval; it is a classification rule. [[data-visualization/uncertainty-and-small-sample-display|Uncertainty intervals]] have a different meaning and should not share the same visual treatment."),
            ("Direction changes the interpretation", "For revenue, higher may be preferable; for response time, lower may be preferable. The chart's target marker is descriptive until the preferred direction is declared. Put that direction in the accompanying text and label the bands accordingly. A single color progression cannot safely carry this distinction. [[data-visualization/accessible-color-and-text-alternatives|Accessible text and non-color cues]] should state whether 68 seconds is better or worse than a target of 59 seconds. A zero target needs a deliberate percentage policy; percent-of-target is undefined there."),
            ("Compare cards using a shared contract", "Several bullet charts can support comparison only if they use compatible axes or clearly named units. Autoscaling each card to its own maximum makes equal lengths represent different values. If metrics use incompatible units, separate panels and display target-relative gaps explicitly, rather than placing them on one fake common scale. [[data-visualization/diverging-bars-zero-reference-and-signed-difference|Signed gap views]] may be clearer for ranking departures from target. Export raw value, target, bands, direction and period. Check missing observations and partial periods before applying a performance label."),
        ],
        "code": '''from math import isfinite

def classify_kpi(observed: float, target: float,
                 minimum: float, maximum: float,
                 lower_is_better: bool) -> tuple[float, str]:
    values = (observed, target, minimum, maximum)
    if any(not isfinite(value) for value in values):
        raise ValueError("KPI values must be finite")
    if not minimum <= observed <= maximum or not minimum <= target <= maximum:
        raise ValueError("measure or target outside axis")
    gap = observed - target
    meets = observed <= target if lower_is_better else observed >= target
    return gap, "meets target" if meets else "misses target"

response_kpi = classify_kpi(68, 59, 0, 120, lower_is_better=True)
assert response_kpi == (9, "misses target")
revenue_kpi = classify_kpi(81, 59, 0, 120, lower_is_better=False)
assert revenue_kpi == (22, "meets target")''',
        "cost": "Classifying one card takes O(1) time and space; N cards take O(N). Rendering cost is small, but target lookup and policy versioning dominate operational correctness. The code checks a shared axis and preferred direction. It does not invent background bands or calculate a percentage when the target is zero. Store band thresholds and time period with the emitted card to make historical comparisons reproducible.",
        "mistakes": ["Comparing a monthly observed value with an annual target.", "Using attractive background bands without a stated threshold policy.", "Assuming higher is always better.", "Letting each card auto-scale while comparing bar lengths across cards."],
        "drill": "Build three service KPI cards: response time, resolved tickets and refund rate. Declare direction, target, axis and band policy for each, then test a missing observation and a zero target.",
        "related": [prefix + "scale-baseline-and-axis-integrity", prefix + "uncertainty-and-small-sample-display", prefix + "accessible-color-and-text-alternatives", prefix + "diverging-bars-zero-reference-and-signed-difference"],
    },
    {
        "slug": "dual-axis-charts-independent-scales-and-spurious-alignment",
        "title": "Dual-axis charts: test whether two series really need one plot",
        "summary": "Independent vertical scales can manufacture alignment; compare shared-time alternatives first.",
        "sections": [
            ("Two axes create a choice", "A dual-axis chart places two measures against a shared horizontal dimension while giving each its own vertical scale. It can be compact, but independent scale ranges allow almost any pair of trends to look aligned or opposed. State both units, put each series next to its axis label, and inspect the same data as separate aligned panels before publishing. [[data-visualization/small-multiples-shared-scales-and-facet-order|Small multiples]] preserve time alignment without implying that pixel height has a shared meaning."),
            ("Audit the apparent correlation", "The eye can mistake coincident peaks for a relationship when one series has been shifted, smoothed or clipped. If the question is whether the measures co-vary, use paired observations in a scatter plot and name any lag rather than inferring it from two lines. [[data-visualization/correlation-heatmap-pairwise-coverage-and-ordering|Correlation coverage]] matters when dates are missing from one source. Do not quietly forward-fill one series to align timestamps. Carry measurement cadence and missingness into the displayed record."),
            ("When shared axes are possible", "If the two series have the same unit and meaning, use a single axis. If they differ only by a constant conversion, convert one before plotting and disclose the conversion. If they have unrelated units but the question is relative change from a baseline, an indexed chart can be clearer, provided the base period and undefined zero-base cases are stated. [[data-visualization/log-and-symmetric-log-scales-with-zero-values|Transformed scales]] also demand explicit zero handling. A second axis is not a shortcut around incompatible denominators."),
            ("Keep exports and text independent", "When a second axis is justified by a particular reading task, export both raw series, scale domains, ticks and units. Use distinct line patterns, not just colors, and name the axes in a text summary. Test the chart with one series removed; readers should still know which axis belongs to the remaining series. [[data-visualization/chart-export-manifest-data-and-render-version|The chart manifest]] should record every transformation and scale domain. Check mobile width: overlapping axis labels can erase the distinctions that made the chart defensible."),
        ],
        "code": '''from math import isfinite

def paired_series_rows(
    first: dict[str, float], second: dict[str, float]
) -> tuple[list[tuple[str, float, float]], list[str]]:
    if any(not isfinite(value) for value in [*first.values(), *second.values()]):
        raise ValueError("series values must be finite")
    shared = sorted(first.keys() & second.keys())
    missing = sorted(first.keys() ^ second.keys())
    return [(period, first[period], second[period]) for period in shared], missing

requests = {"week-47": 81, "week-48": 97, "week-49": 113}
latency = {"week-47": 59, "week-49": 68, "week-50": 83}
pairs, unpaired = paired_series_rows(requests, latency)
assert pairs == [("week-47", 81, 59), ("week-49", 113, 68)]
assert unpaired == ["week-48", "week-50"]''',
        "cost": "For A and B keyed observations, set intersection and sorting use O(A+B+K log K) time and O(A+B) additional space for K paired periods. This preparation does not select axis domains or establish a correlation. It prevents silent alignment by index position. A production chart should also validate time-zone and aggregation-period equivalence before treating two keys as the same time.",
        "mistakes": ["Choosing independent axis domains solely to align peaks.", "Forward-filling missing dates without a stated imputation rule.", "Using two axes for measures that share a convertible unit.", "Relying on color alone to tie each line to its axis."],
        "drill": "Plot weekly requests and latency for 47 weeks as separate aligned panels and as a dual-axis view. Remove two latency weeks and verify the paired observation count changes visibly.",
        "related": [prefix + "small-multiples-shared-scales-and-facet-order", prefix + "correlation-heatmap-pairwise-coverage-and-ordering", prefix + "log-and-symmetric-log-scales-with-zero-values", prefix + "chart-export-manifest-data-and-render-version"],
    },
]

new_paths = [prefix + lesson["slug"] for lesson in lessons]
assert len(new_paths) == len(set(new_paths)) and not set(new_paths) & by_path.keys()
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
        "featured": False, "sort_order": 8728 + offset, "status": "published",
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
    for start, end, heading in ((0, 2, "Dense points and signed gaps"),
                                (2, 5, "Bridges, targets and dual axes")):
        targets = new_paths[start:end]
        row["data"]["modules"].append({"title": heading, "lessons": targets})
        row["body"] += f'<h2>{heading}</h2><ul>' + ''.join(
            f'<li>{link(target)}</li>' for target in targets) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "scatterplot-overplotting-density-and-sampling-bias": [new_paths[0], new_paths[4]],
    prefix + "choropleth-rates-boundaries-and-missing-regions": [new_paths[0]],
    prefix + "aggregation-grain-and-denominator": [new_paths[1], new_paths[2]],
    prefix + "scale-baseline-and-axis-integrity": [new_paths[1], new_paths[3]],
    prefix + "chart-export-manifest-data-and-render-version": [new_paths[2], new_paths[4]],
    prefix + "uncertainty-and-small-sample-display": [new_paths[3]],
    prefix + "small-multiples-shared-scales-and-facet-order": [new_paths[4]],
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
