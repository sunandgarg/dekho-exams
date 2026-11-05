"""Add five original chart-design lessons and reciprocal links."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-data-visualization-import-20261008-h.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "data-visualization/"
hub = prefix + "data-visualization-tutorial"

lessons = [
    {
        "slug": "forest-plots-effect-measures-null-lines-and-intervals",
        "title": "Forest plots: align estimates, intervals and the no-effect value",
        "summary": "Compare like-for-like effects on one scale and explain what each interval and marker means.",
        "sections": [
            ("Choose one effect measure", "A forest plot places estimates on a shared horizontal scale with an interval beside each estimate. Mean differences, risk ratios and odds ratios cannot be mixed as though their numbers shared a unit. State the effect measure, population, comparison direction and interval method before plotting. The no-effect value is zero for an additive difference and one for a multiplicative ratio. A log-scaled ratio axis often makes equal proportional changes on either side of one visually comparable; it cannot accept zero or negative endpoints. [[data-visualization/diverging-bars-zero-reference-and-signed-difference|Signed differences]] have a different zero reference and should not inherit ratio-axis labels."),
            ("Keep the interval type attached", "A horizontal line may be a confidence interval, a credible interval, a sensitivity range or something else. Say which. Do not infer that a row with an interval touching the no-effect line is equivalent to a row with a wide interval far beyond it. Both estimate magnitude and precision matter. [[data-visualization/asymmetric-error-bars-interval-type-and-axis-clipping|Asymmetric error bars]] explain why endpoints must be kept as numbers, not reconstructed from a visual radius. When an interval exceeds the plot boundary, use a clipped-end marker and print its true endpoint. Never replace the endpoint with the axis maximum in the underlying data."),
            ("Marker area needs a contract", "A larger square can indicate greater analytic weight, sample size or merely visual emphasis. Those are not interchangeable. If marker area represents a weight, name the weighting method and provide the numeric weights. A pooled estimate at the bottom is a separate calculation, not the average of x positions on the screen; omit it when the included rows are not meaningfully combinable. [[data-visualization/proportional-symbol-maps-area-scale-and-overlap|Area-scaled symbols]] follow the same rule: doubling a marker radius quadruples its area. A plain point estimate with equal marker size is safer when weights are not part of the analysis."),
            ("Sort without changing meaning", "Sorting rows by effect size can make a striking ladder but may hide prespecified groups or study chronology. Declare the row order, retain stable IDs, and distinguish subgroups without implying that adjacency is evidence of similarity. A plot of model variants should note which intervals are correlated because they share data; counting each variant as an independent result overstates evidence. [[data-visualization/uncertainty-and-small-sample-display|Uncertainty and sample-size displays]] help explain sparse rows. Supply an accessible table with row ID, estimate, lower and upper bounds, unit, interval type and weight, then compare the chart against that table before publishing."),
        ],
        "code": '''from math import isfinite, log

def ratio_forest_positions(
    rows: list[tuple[str, float, float, float]]
) -> list[tuple[str, float, float, float]]:
    names = [name for name, _, _, _ in rows]
    if len(names) != len(set(names)) or any(not name for name in names):
        raise ValueError("row names must be unique and nonempty")
    output = []
    for name, estimate, lower, upper in rows:
        if not all(isfinite(value) and value > 0
                   for value in (estimate, lower, upper)):
            raise ValueError("ratio estimates and endpoints must be positive")
        if not lower <= estimate <= upper:
            raise ValueError("estimate must lie within its interval")
        output.append((name, log(estimate), log(lower), log(upper)))
    return output

depot_comparisons = ratio_forest_positions([
    ("north depot", 1.25, 1.06, 1.47),
    ("south depot", 0.80, 0.65, 1.03),
])
assert depot_comparisons[0][1] > 0
assert depot_comparisons[1][1] < 0
assert log(1) == 0''',
        "language": "python",
        "cost": "Validating and transforming N rows takes O(N) time and O(N) output space. The code prepares positive ratio estimates for a log axis; it does not calculate intervals, pool rows or assign weights. Keep original ratio values in the export because logarithmic positions are drawing coordinates. If a row has a zero, negative or undefined ratio, investigate the estimator rather than forcing it onto the log plot.",
        "mistakes": ["Mixing additive differences and ratios on one unlabeled axis.", "Drawing the no-effect line at zero for a raw ratio plot.", "Using square size as weight without stating the weighting rule.", "Silently truncating interval endpoints or treating related model variants as independent studies."],
        "drill": "Compare 47 depot-level rate ratios with intervals. Identify rows that need clipped-end markers, then explain why a pooled diamond should not be drawn until the estimands and weights are reviewed.",
        "related": [prefix + "asymmetric-error-bars-interval-type-and-axis-clipping", prefix + "diverging-bars-zero-reference-and-signed-difference", prefix + "proportional-symbol-maps-area-scale-and-overlap", prefix + "uncertainty-and-small-sample-display"],
    },
    {
        "slug": "scatterplot-matrices-pairwise-coverage-and-multiple-comparisons",
        "title": "Scatterplot matrices: disclose which rows support each pair",
        "summary": "Treat pairwise missingness, scales and the number of comparisons as part of the matrix.",
        "sections": [
            ("Each cell has its own population", "A scatterplot matrix shows pairwise relationships among several variables. If missing values differ by column, the cell for queue depth versus delay may use different records from the cell for delay versus cost. A common complete-case filter makes populations consistent but may discard many rows. Pairwise deletion retains more data but changes the population from cell to cell. State which policy was used and print the valid count in every cell. [[data-visualization/correlation-heatmap-pairwise-coverage-and-ordering|Correlation heatmaps]] face the same coverage problem but hide the underlying point clouds."),
            ("Use one variable scale across its row and column", "A variable appearing on several axes should keep a common unit and domain where possible. Otherwise the apparent slope and spread change as a reader moves across the grid. Label only the outer axes if the layout is tight, but keep units available in a companion table. Transformations such as logarithms must be consistent for every appearance of the variable, and invalid nonpositive values need an explicit exclusion count. [[data-visualization/log-and-symmetric-log-scales-with-zero-values|Log-scale boundaries]] should be chosen for the data, not merely to make a diagonal cluster look tidy."),
            ("A matrix multiplies visual tests", "With seven variables there are 21 distinct off-diagonal pairs. One remarkable-looking cell may occur by chance, especially after inspecting many matrices, filters and periods. Use the display to generate questions rather than to announce discovered laws. Annotate pre-specified comparisons, and follow up with a model or analysis suited to the decision. [[data-visualization/scatterplot-regression-overlays-fit-scope-and-prediction-bands|Regression overlays]] need their own fit population and assumptions; a line in every cell can overwhelm the matrix and invite unsupported causal readings."),
            ("Control density and reading order", "Plotting the same large cohort in 42 mirrored cells can be expensive and visually opaque. Use the lower triangle for points and reserve the diagonal for univariate distributions or compact count summaries. Sample only with a declared rule, preserving rare groups if that is part of the question. [[data-visualization/scatterplot-overplotting-density-and-sampling-bias|Overplotting techniques]] can reveal concentration without creating false individual positions. Sort variables in a stable, meaningful sequence and offer a per-cell data table or drill-down so the matrix remains usable at phone width and high zoom."),
        ],
        "code": '''from math import isfinite

def pairwise_points(records: list[dict[str, float | None]],
                    horizontal: str, vertical: str
                   ) -> list[tuple[float, float]]:
    if not horizontal or not vertical or horizontal == vertical:
        raise ValueError("two distinct variable names required")
    points = []
    for record in records:
        x_value, y_value = record.get(horizontal), record.get(vertical)
        if x_value is None or y_value is None:
            continue
        if not isfinite(x_value) or not isfinite(y_value):
            raise ValueError("non-finite values require an explicit policy")
        points.append((x_value, y_value))
    return points

depot_rows = [
    {"queue": 47.0, "delay": 31.0, "cost": 81.0},
    {"queue": 59.0, "delay": None, "cost": 97.0},
    {"queue": 83.0, "delay": 43.0, "cost": None},
]
assert pairwise_points(depot_rows, "queue", "delay") == [(47, 31), (83, 43)]
assert pairwise_points(depot_rows, "queue", "cost") == [(47, 81), (59, 97)]''',
        "language": "python",
        "cost": "For P variables and N records, preparing every unique pair costs O(P squared times N) time. Retaining all displayed points for the lower triangle can take O(P squared times N) space; stream or aggregate when that footprint is too large. The example uses pairwise deletion and makes no correlation or significance claim. Report the per-cell count and dropped-row policy so two adjacent clouds are not mistaken for identical cohorts.",
        "mistakes": ["Reporting one global sample size when cells use different valid rows.", "Auto-scaling the same variable differently across matrix cells.", "Treating the most striking of many inspected pairs as confirmed evidence.", "Rendering mirrored dense cells without a detail view or sampling record."],
        "drill": "Build a lower-triangle matrix for seven operational measures. Put valid-row counts in all 21 cells, fix each variable's scale across appearances and identify three relationships chosen before viewing the grid.",
        "related": [prefix + "correlation-heatmap-pairwise-coverage-and-ordering", prefix + "log-and-symmetric-log-scales-with-zero-values", prefix + "scatterplot-regression-overlays-fit-scope-and-prediction-bands", prefix + "scatterplot-overplotting-density-and-sampling-bias"],
    },
    {
        "slug": "streamgraphs-centered-baselines-category-order-and-total-volume",
        "title": "Streamgraphs: preserve totals behind a moving baseline",
        "summary": "Use a centered stack for shape exploration, but give readers a separate way to inspect the total.",
        "sections": [
            ("The baseline is a layout choice", "A streamgraph stacks nonnegative category values over time around a moving or centered baseline. Its flowing shape can help reveal broad category shifts, but the vertical position of a layer is partly an artifact of the baseline calculation. Layer thickness represents value; the upper edge alone does not. Do not label the vertical axis like an ordinary zero-based stacked area chart unless it actually has a fixed zero. [[data-visualization/stacked-bars-composition-and-changing-denominators|Stacked composition]] explains why categories and their denominator must be stable enough to compare."),
            ("Totals still need a view", "Centering a total of 47 and a total of 188 both around the same midpoint can make the chart attractive while hiding the operational difference. Include a separate total line, a compact table or a conventional zero-based stacked view when volume matters. A streamgraph is a poor sole view for audit questions such as whether all categories reconcile to the source total. [[data-visualization/waterfall-chart-bridge-reconciliation-and-subtotals|Waterfall reconciliation]] handles additive changes with a more explicit baseline. For each time bin, validate that layer values sum to the reported total before calculating any layout offset."),
            ("Order controls readability", "A layer buried in the middle may be easier to follow than one whose boundaries both move erratically, but changing the order between frames makes categories impossible to track. Select a stable order and color identity for the whole time range. If categories enter or leave, distinguish true zero from missing data; an absent category record should not silently become a zero-thickness layer. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Missing periods and provisional bins]] require an explicit display state, even in a decorative-looking flow chart."),
            ("Keep the raw table accessible", "Layer thickness is hard to read precisely, particularly on a narrow viewport. Provide a table with period, category, value, total and any excluded share. Label categories directly where possible and offer keyboard-accessible inspection for the rest. [[data-visualization/interactive-chart-keyboard-focus-and-data-table-contract|Interactive chart access]] should preserve each period and category ID when focus moves. Export the stacking order and baseline algorithm so an updated chart library cannot silently change the shape while the underlying observations stay fixed."),
        ],
        "code": '''from math import isfinite

def centered_stack(categories: list[str],
                   periods: list[dict[str, float]]
                  ) -> list[dict[str, tuple[float, float]]]:
    if not categories or len(categories) != len(set(categories)):
        raise ValueError("ordered categories must be unique")
    output = []
    for period in periods:
        if set(period) != set(categories):
            raise ValueError("each period needs every category, including real zeros")
        if any(not isfinite(value) or value < 0 for value in period.values()):
            raise ValueError("values must be finite and nonnegative")
        baseline = -sum(period.values()) / 2
        layers = {}
        for category in categories:
            upper = baseline + period[category]
            layers[category] = (baseline, upper)
            baseline = upper
        output.append(layers)
    return output

service_mix = centered_stack(
    ["routine", "urgent"],
    [{"routine": 47, "urgent": 59}, {"routine": 81, "urgent": 97}],
)
assert service_mix[0] == {
    "routine": (-53.0, -6.0), "urgent": (-6.0, 53.0)
}
assert service_mix[1]["urgent"][1] == 89.0''',
        "language": "python",
        "cost": "For T periods and C categories, validation and centered stacking take O(TC) time and O(TC) output space. This code uses a simple centered baseline, not an optimized wiggle offset; those two layouts differ. It requires a complete category set per period and rejects negative measures. Keep the original values and totals for accessibility and reconciliation. For large C, crowded labels and thin layers may make small multiples or a ranked table clearer.",
        "mistakes": ["Reading the moving layer boundary as a zero-based value.", "Using a centered streamgraph alone when the decision depends on total volume.", "Changing category order across periods and making colors switch identity.", "Replacing missing category records with zero without a recorded rule."],
        "drill": "Show 47 reporting periods and eight service classes. Reconcile each total, hold category order fixed and place a separate total-volume line beside the centered streamgraph.",
        "related": [prefix + "stacked-bars-composition-and-changing-denominators", prefix + "waterfall-chart-bridge-reconciliation-and-subtotals", prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "interactive-chart-keyboard-focus-and-data-table-contract"],
    },
    {
        "slug": "horizon-charts-band-encoding-baselines-and-decoding",
        "title": "Horizon charts: trade vertical space for a harder value lookup",
        "summary": "Explain the baseline, band width and color order so compact time series remain decodable.",
        "sections": [
            ("Folded bands need a key", "A horizon chart divides a value's distance from a baseline into bands and overlays those bands in a short row. It can fit many series in little vertical space, but a reader must decode band color as well as vertical shape. State the baseline and numeric size of one band. If the chart shows deviations from 47 incidents per day, a value of 87 occupies two 20-unit bands above that reference, not 87 units of vertical height. [[data-visualization/scale-baseline-and-axis-integrity|Baseline integrity]] matters more when the display has been folded."),
            ("Positive and negative need separate meaning", "For signed deviations, use distinguishable sequences for above and below the baseline, not just a lighter and darker tint of one hue. Include text labels for the sign and a small decoding key with concrete values. A monochrome or color-vision test should still allow readers to distinguish the two directions through texture, labels or a paired table. [[data-visualization/accessible-color-and-text-alternatives|Accessible color alternatives]] are a requirement of the underlying comparison, not a finishing layer. Missing observations need a gap; they are not zero deviation."),
            ("Fix a common band domain", "If each row chooses its own band width, the darkest color represents a different numeric amount in each series. That defeats cross-row comparison. Choose a shared band width and number of bands for all rows being compared, and decide how out-of-range values are signaled. Clipping an extreme silently is worse than showing an overflow marker and its numeric value. [[data-visualization/large-series-level-of-detail-and-extrema|Extrema-preserving reduction]] helps keep short-lived spikes when a long series must be downsampled before folding."),
            ("Use compactness only when it helps", "A horizon chart is suited to scanning many similarly scaled time series for timing and magnitude patterns. It is weak for exact readout, unfamiliar audiences and small numbers of series, where an ordinary line chart is easier. Keep a linked detail view or accessible table with timestamp, original value, baseline, signed deviation and band encoding. [[data-visualization/small-multiples-shared-scales-and-facet-order|Small multiples]] are the natural comparison when there is enough vertical space. Document the folding rule in the export so future renders preserve the same visual thresholds."),
        ],
        "code": '''from math import isfinite

def horizon_bands(value: float, baseline: float,
                  band_width: float, band_count: int
                 ) -> tuple[str, list[float], bool]:
    if not all(isfinite(number) for number in (value, baseline, band_width)):
        raise ValueError("values must be finite")
    if band_width <= 0 or not isinstance(band_count, int) or band_count < 1:
        raise ValueError("positive band width and count required")
    delta = value - baseline
    remaining = abs(delta)
    heights = []
    for _ in range(band_count):
        height = min(remaining, band_width)
        heights.append(height)
        remaining -= height
    sign = "above" if delta > 0 else "below" if delta < 0 else "at"
    return sign, heights, remaining > 0

assert horizon_bands(87, 47, 20, 3) == ("above", [20, 20, 0], False)
assert horizon_bands(18, 47, 20, 2) == ("below", [20, 9], False)
assert horizon_bands(130, 47, 20, 3)[2] is True''',
        "language": "python",
        "cost": "Encoding N observations with B bands takes O(NB) time and O(NB) output space when every band height is retained. The overflow flag prevents silent saturation but the rendering layer must draw a visible marker and numeric value. This function returns a sign and positive band heights; the renderer chooses color and clipping. Do not compare rows using different baselines or band widths unless the chart explicitly separates those views.",
        "mistakes": ["Reading folded height as the full original value.", "Changing band width from row to row while reusing one color key.", "Letting values above the maximum band range saturate without an overflow label.", "Encoding missing as a zero deviation from baseline."],
        "drill": "Display 59 equipment series around a shared service threshold. Check the band key against five exact values, mark overflows and offer a full-height line chart for one selected machine.",
        "related": [prefix + "scale-baseline-and-axis-integrity", prefix + "accessible-color-and-text-alternatives", prefix + "large-series-level-of-detail-and-extrema", prefix + "small-multiples-shared-scales-and-facet-order"],
    },
    {
        "slug": "animated-charts-stable-identity-locked-scales-and-pause-state",
        "title": "Animated charts: do not let motion invent data",
        "summary": "Keep record IDs, scales and frame provenance stable; offer pause and a static path through the same observations.",
        "sections": [
            ("Frames are data snapshots", "An animated chart displays a sequence of observations, not a continuous measurement just because movement looks continuous. Store the date, source revision, eligibility rule and unit for every frame. When data exist only at two dates, intermediate positions are visual interpolation and must not be described as observed measurements. A bar that grows from 47 to 81 may imply smooth change even if the underlying quantity jumped at one import. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Time-series completeness]] should determine which frames can be compared and which remain provisional."),
            ("Identity must survive reordering", "Use stable entity IDs across frames. A ranked bar animation may reorder entities; if color or label is assigned by array position, it can appear that one entity changes into another. Match records by ID, separate newly entering and exiting entities, and never fill a missing measurement with zero unless zero is a real observation. [[data-visualization/bump-chart-rank-ties-membership-and-period-coverage|Rank movement charts]] are often better as a static alternative when the main question is who changed position. Keep the selection anchored to ID if a user pauses halfway through a transition."),
            ("Lock the scale or disclose change", "An axis that rescales independently at every frame can make a flat series appear to surge or a large decline look minor. Fix a domain across the full sequence when the comparison is meant to be quantitative. If an extreme new value requires a domain change, pause, label the change and provide the numeric context. [[data-visualization/scale-baseline-and-axis-integrity|Axis integrity]] applies to every frame, and [[data-visualization/large-series-level-of-detail-and-extrema|extrema checks]] must run before the domain is chosen. Keep category colors, units and legend order stable too."),
            ("Motion is optional", "Provide play, pause, next-frame and previous-frame controls that work with a keyboard. Do not trap focus on the chart. Respect reduced-motion preference and offer a static small-multiple view or data table that carries the same observations. A paused live feed should indicate whether resuming continues from the pause point or jumps to the latest state. [[data-visualization/interactive-chart-keyboard-focus-and-data-table-contract|Keyboard and table contracts]] keep the analysis available without timed interaction. Export frame ID, timestamp, scale domain and source record IDs so a particular visual state can be cited and reproduced."),
        ],
        "code": '''function pairedFrameValues(previousFrame, nextFrame) {
  const previous = new Map(previousFrame.map(record => [record.id, record.value]));
  const next = new Map(nextFrame.map(record => [record.id, record.value]));
  if (previous.size !== previousFrame.length || next.size !== nextFrame.length) {
    throw new Error("each frame needs unique record IDs");
  }
  const paired = [];
  for (const [id, earlierValue] of previous) {
    if (next.has(id)) {
      const laterValue = next.get(id);
      if (!Number.isFinite(earlierValue) || !Number.isFinite(laterValue)) {
        throw new Error("frame values must be finite");
      }
      paired.push({id, earlierValue, laterValue});
    }
  }
  return paired;
}

const pairedDepots = pairedFrameValues(
  [{id: "north-47", value: 47}, {id: "south-59", value: 59}],
  [{id: "south-59", value: 81}, {id: "north-47", value: 52}],
);
if (pairedDepots[0].id !== "north-47" || pairedDepots[0].laterValue !== 52) {
  throw new Error("records must match by identity, not array position");
}''',
        "language": "javascript",
        "cost": "Building two ID maps and pairing N previous records with M next records takes O(N+M) time and space. This code deliberately omits entering and exiting entities from interpolation; the view should represent them with explicit entry or exit states, not fabricate an earlier zero. A full animation also needs frame controls, reduced-motion handling, stable scales and a static equivalent. The pairing function is the data boundary that prevents position-based identity errors.",
        "mistakes": ["Presenting interpolated in-between positions as measured observations.", "Matching reordered rows by array index so entities switch labels or colors.", "Auto-scaling every frame while inviting quantitative comparison.", "Autoplaying without a working pause and static way to inspect the data."],
        "drill": "Animate 47 weekly depot snapshots. Lock the quantity scale, audit entry and exit states, pause on a chosen week and confirm the static table reports the same IDs and values.",
        "related": [prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "bump-chart-rank-ties-membership-and-period-coverage", prefix + "scale-baseline-and-axis-integrity", prefix + "interactive-chart-keyboard-focus-and-data-table-contract"],
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
        "featured": False, "sort_order": 8748 + offset, "status": "published",
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
    for start, end, heading in ((0, 2, "Effect estimates and multivariable grids"),
                                (2, 5, "Compact and moving time series")):
        targets = new_paths[start:end]
        row["data"]["modules"].append({"title": heading, "lessons": targets})
        row["body"] += f'<h2>{heading}</h2><ul>' + ''.join(
            f'<li>{link(target)}</li>' for target in targets) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "asymmetric-error-bars-interval-type-and-axis-clipping": [new_paths[0]],
    prefix + "uncertainty-and-small-sample-display": [new_paths[0]],
    prefix + "correlation-heatmap-pairwise-coverage-and-ordering": [new_paths[1]],
    prefix + "scatterplot-regression-overlays-fit-scope-and-prediction-bands": [new_paths[1]],
    prefix + "stacked-bars-composition-and-changing-denominators": [new_paths[2]],
    prefix + "waterfall-chart-bridge-reconciliation-and-subtotals": [new_paths[2]],
    prefix + "scale-baseline-and-axis-integrity": [new_paths[3], new_paths[4]],
    prefix + "small-multiples-shared-scales-and-facet-order": [new_paths[3]],
    prefix + "bump-chart-rank-ties-membership-and-period-coverage": [new_paths[4]],
    prefix + "interactive-chart-keyboard-focus-and-data-table-contract": [new_paths[4]],
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
