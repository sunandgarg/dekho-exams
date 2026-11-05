"""Add four Data Visualization lessons with validated links and a CMS packet."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-data-visualization-import-20261008-k.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "data-visualization/"
hub = prefix + "data-visualization-tutorial"

lessons = [
    {
        "slug": "precision-recall-curves-threshold-ties-prevalence-and-average-precision",
        "title": "Precision–recall curves: preserve threshold ties and class prevalence",
        "summary": "Build an auditable precision–recall staircase from held-out scores, then read average precision against the actual event rate.",
        "sections": [
            ("Start with the decision population", "A precision–recall curve describes a ranked binary score across possible alert thresholds. Precision is true alerts divided by all alerts; recall is true alerts divided by all actual events. They answer different questions. If a maintenance team can inspect 47 machines per shift, the useful region may be the high-precision, low-recall end, while a safety review may tolerate many inspections to find nearly every fault. Define the event, prediction timestamp, outcome window, eligible population and positive class before plotting. [[data-visualization/probability-calibration-plots-bin-counts-prevalence-and-drift|Probability calibration]] answers whether a score of 0.30 corresponds to about 30% observed risk; a precision–recall curve asks how selected alerts trade false alarms for captured events. A ranking can be useful and still be poorly calibrated."),
            ("Sweep tied scores as one threshold", "Sort records by decreasing score. At each distinct score, include all records with that score before measuring precision and recall. Splitting tied cases in arbitrary input order invents operating points that no threshold can achieve. Add a no-alert endpoint at recall zero and precision one only as a plotting convention: it does not mean the model has already found an event. At the opposite end, all eligible records are selected and precision equals the cohort event rate. The stepwise curve must retain its actual points; smoothing or interpolating precision can imply a threshold that never existed. [[data-visualization/empirical-cdf-percentiles-and-tail-reading|An empirical CDF]] uses a similar idea of preserving observed steps rather than drawing a continuous story through discrete decisions."),
            ("Interpret area and baseline carefully", "Average precision weights precision at each achieved recall increment. It is not always the same number as trapezoidal area under a line interpolated between curve points, and neither is classification accuracy. The event prevalence is a useful no-skill reference when scores are independent of labels; if prevalence changes from one plant to another, the apparent precision of the same ranking can change too. Put both event count and total eligible count beside every panel. Compare models on the same untouched evaluation cohort, outcome definition and time window. [[data-visualization/small-multiples-shared-scales-and-facet-order|Shared small-multiple scales]] stop separate panels from hiding the difficult low-recall region. When costs matter, also show the selected operating threshold and its alert volume rather than publishing only a scalar summary."),
            ("Expose uncertainty and selection limits", "Few positives produce large stair steps: one additional true event can move recall markedly. Bootstrap or another justified interval method may describe sampling uncertainty, but resample at the correct independent unit, such as machine or customer, when multiple records belong to one unit. Delayed outcomes, unreviewed alerts and selectively labeled negatives can bias the curve; an apparent negative is not a confirmed one merely because a record is old. [[data-visualization/uncertainty-and-small-sample-display|Small-sample uncertainty]] and [[data-visualization/time-series-gaps-calendars-and-provisional-periods|provisional periods]] need explicit treatment. A companion table should give threshold, true positives, false positives, precision, recall and selected count at a few operationally relevant cuts."),
        ],
        "code": '''def precision_recall_steps(records: list[tuple[str, float, bool]]):
    from math import isfinite
    identifiers = [record_id for record_id, _, _ in records]
    if len(identifiers) != len(set(identifiers)) or any(not key for key in identifiers):
        raise ValueError("record identifiers must be unique and nonempty")
    if any(not isfinite(score) or type(event) is not bool
           for _, score, event in records):
        raise ValueError("finite scores and boolean labels are required")
    positives = sum(event for _, _, event in records)
    if positives == 0:
        raise ValueError("recall requires at least one positive")
    ranked = sorted(records, key=lambda item: item[1], reverse=True)
    points = []
    true_positives = false_positives = cursor = 0
    while cursor < len(ranked):
        threshold = ranked[cursor][1]
        while cursor < len(ranked) and ranked[cursor][1] == threshold:
            true_positives += ranked[cursor][2]
            false_positives += not ranked[cursor][2]
            cursor += 1
        selected = true_positives + false_positives
        points.append((threshold, true_positives / selected,
                       true_positives / positives, selected))
    average_precision = sum(
        precision * (recall - (points[index - 1][2] if index else 0))
        for index, (_, precision, recall, _) in enumerate(points))
    return points, average_precision, positives / len(records)

inspection_scores = [("press-47", 0.91, True),
                     ("press-59", 0.73, False),
                     ("press-83", 0.73, True),
                     ("press-97", 0.22, False)]
steps, average_precision, prevalence = precision_recall_steps(inspection_scores)
assert len(steps) == 3
assert steps[1] == (0.73, 2 / 3, 1.0, 3)
assert abs(average_precision - 5 / 6) < 1e-12
assert prevalence == 0.5''',
        "cost": "Sorting N records takes O(N log N) time. The threshold sweep is O(N), while the sorted copy and output need O(N) space; unique-ID validation also needs O(N) space. The sample's average precision is 5/6 because recall rises first by one half at precision one and then by one half at precision two thirds. Four records demonstrate arithmetic and tie handling, not a credible model comparison. The function assumes labels are complete and the evaluation cohort has already been held out.",
        "mistakes": ["Breaking equal scores in row order and presenting unreachable thresholds.", "Calling trapezoidal interpolation average precision without defining the calculation.", "Comparing curves built from cohorts with different prevalence or outcome windows.", "Reading the no-alert plotting endpoint as measured model performance."],
        "drill": "Evaluate 470 held-out inspection scores with 59 confirmed events. Print every attainable tied-score threshold, mark the 47-alert operating point, and compare its event capture with the full curve.",
        "related": [prefix + "probability-calibration-plots-bin-counts-prevalence-and-drift", prefix + "uncertainty-and-small-sample-display", prefix + "small-multiples-shared-scales-and-facet-order", prefix + "time-series-gaps-calendars-and-provisional-periods"],
    },
    {
        "slug": "bland-altman-plots-paired-bias-agreement-limits-and-proportional-error",
        "title": "Bland–Altman plots: assess paired measurement agreement",
        "summary": "Compare paired device readings with signed bias, agreement limits and a check for magnitude-dependent error.",
        "sections": [
            ("Pair the same specimen under both methods", "A method-agreement plot starts with two readings of the same item under conditions that make comparison meaningful. Put their mean on the horizontal axis and the signed difference, new instrument minus reference instrument, on the vertical axis. A scatterplot or high correlation between devices can coexist with a large systematic offset, so correlation is not an agreement test. Define the acceptable difference in the original unit before seeing the result. For a temperature probe, an average offset of 0.8 degrees may matter or not depending on the process tolerance; a statistically precise estimate does not make an operationally unsafe offset acceptable. [[data-visualization/paired-change-slope-and-dumbbell-charts|Paired-change charts]] show each item's two readings, while this plot concentrates on the distribution of pairwise error across the measurement range."),
            ("Compute bias and descriptive limits", "The horizontal reference line is the mean signed difference, or bias. Under assumptions including approximately stable difference variance and a suitable difference distribution, conventional agreement limits are bias plus or minus 1.96 sample standard deviations of differences. Those lines describe the spread expected for individual differences under the model. They are not confidence intervals for the mean bias and are not a pass/fail tolerance supplied by the process owner. Report the number of pairs, direction of subtraction and raw units with the limits. [[data-visualization/asymmetric-error-bars-interval-type-and-axis-clipping|Interval labeling]] matters here: a reader must be able to tell agreement limits from uncertainty about where those limits lie. A small sample makes estimated limits unstable."),
            ("Look for error that changes with magnitude", "A fan-shaped cloud suggests that larger measurements have greater absolute disagreement; a sloped pattern suggests proportional bias. One global pair of horizontal limits can then misrepresent both ends of the range. Inspect residual patterns and consider a justified transformation or a model in which spread depends on magnitude. Do not automatically use percent difference: dividing by a near-zero mean can explode, and a ratio may be inappropriate for values that cross zero. [[data-visualization/scatterplot-regression-overlays-fit-scope-and-prediction-bands|Regression overlays]] can reveal a trend, but a line drawn through differences is only descriptive until its assumptions and uncertainty are examined. Mark outliers for investigation without quietly deleting them."),
            ("Respect independent units and coverage", "Repeated measurements from the same machine are correlated. Treating 47 repeated readings from one unit as 47 independent machines understates uncertainty. Choose a design that separates repeatability within each method from agreement between methods, or analyze at the proper unit. Check whether pairs cover the full operating range; limits estimated from a narrow band cannot be claimed for extreme values never sampled. An accessible table should list specimen ID, both values, pair mean, signed difference and any excluded or missing reading. [[data-visualization/chart-export-manifest-data-and-render-version|An export manifest]] should preserve calibration date, units, method versions and the subtraction direction, because reversing that direction changes the sign of bias and both limit labels."),
        ],
        "code": '''from math import sqrt, isfinite

def agreement_summary(pairs: list[tuple[str, float, float]]):
    identifiers = [specimen_id for specimen_id, _, _ in pairs]
    if len(pairs) < 2 or len(set(identifiers)) != len(pairs) or any(not key for key in identifiers):
        raise ValueError("at least two uniquely identified pairs are required")
    if any(not isfinite(reference) or not isfinite(candidate)
           for _, reference, candidate in pairs):
        raise ValueError("all paired readings must be finite")
    points = [(specimen_id, (reference + candidate) / 2,
               candidate - reference)
              for specimen_id, reference, candidate in pairs]
    bias = sum(difference for _, _, difference in points) / len(points)
    variance = sum((difference - bias) ** 2
                   for _, _, difference in points) / (len(points) - 1)
    spread = sqrt(variance)
    return points, bias, (bias - 1.96 * spread, bias + 1.96 * spread)

probe_pairs = [("batch-47", 41.0, 42.0),
               ("batch-59", 54.0, 55.0),
               ("batch-83", 63.0, 66.0)]
points, bias, limits = agreement_summary(probe_pairs)
assert points == [("batch-47", 41.5, 1.0),
                  ("batch-59", 54.5, 1.0),
                  ("batch-83", 64.5, 3.0)]
assert abs(bias - 5 / 3) < 1e-12
assert limits[0] < 0 < limits[1]''',
        "cost": "For N pairs, constructing points and calculating sample variance each take O(N) time. The returned plot table takes O(N) space; streaming just the bias and variance is possible with O(1) extra space when individual points are not needed. The three-pair check fixes the sign convention and sample-variance denominator. It is too small to justify operational agreement limits and does not account for repeated measures or magnitude-dependent spread.",
        "mistakes": ["Calling high correlation proof that two methods agree.", "Confusing agreement limits for individual differences with confidence limits around mean bias.", "Reversing the subtraction direction between chart and report.", "Counting repeated readings from one item as independent specimens."],
        "drill": "Pair 59 items across two measurement devices. State a tolerable difference first, then plot signed differences, check for magnitude-dependent spread and report which items fall outside that tolerance.",
        "related": [prefix + "paired-change-slope-and-dumbbell-charts", prefix + "asymmetric-error-bars-interval-type-and-axis-clipping", prefix + "scatterplot-regression-overlays-fit-scope-and-prediction-bands", prefix + "chart-export-manifest-data-and-render-version"],
    },
    {
        "slug": "upset-plots-exclusive-intersections-set-universe-and-cardinality",
        "title": "UpSet plots: count exact intersections without double counting",
        "summary": "Turn overlapping memberships into exclusive intersection bars with a stated universe and reproducible set order.",
        "sections": [
            ("Define one universe of unique entities", "An intersection plot is useful when a Venn drawing becomes too crowded. Consider support tickets tagged Billing, Delivery or Returns. Each ticket needs a stable unique ID and a documented observation period; multiple log rows for the same ticket should not become multiple members. Decide whether the universe is all tickets, all tagged tickets or only tickets passing an eligibility filter. That choice changes the meaning of the empty-membership group. [[data-visualization/aggregation-grain-and-denominator|Aggregation grain and denominator]] apply before any bars are drawn. A set-size bar counts every ticket in a set, including tickets in other sets; summing set-size bars therefore double-counts overlap by design."),
            ("Distinguish exact from inclusive intersections", "An exact intersection for Billing and Returns contains tickets with those two tags and no other displayed tag. An inclusive intersection contains those tickets even when they also carry Delivery. UpSet-style bars often use exact membership masks, but analysts sometimes compute inclusive intersections in SQL and label them as exact. State which contract each bar uses. The worked function returns an exact mask for every record and excludes the all-false mask from plotted bars while retaining its count in the audit. The sum of all exact masks must equal the size of the universe, including items outside all displayed sets. [[data-visualization/mosaic-plots-joint-area-conditional-rate-and-empty-cells|Mosaic plots]] offer a different view of joint categories, but they also require a clear rule for empty cells and denominators."),
            ("Keep column and set order stable", "Sort intersections by count for exploration, then freeze a documented column order when comparing periods. Otherwise a bar that moves horizontally can be mistaken for a membership change. Order the set rows consistently, and show the connected dots or a textual equivalent beneath each bar. A bar for no sets can be meaningful if every ticket belongs to the universe regardless of tagging; do not silently discard it from reconciliation. [[data-visualization/small-multiples-shared-scales-and-facet-order|Stable facet order]] helps the same reader compare versions. A companion table should give exact mask, count, period, filters, and the underlying entity IDs or an authorized export path."),
            ("Stop before combinations swamp the chart", "With K sets there are up to 2^K exact masks, including the empty mask, even though many may have zero observations. An unreadable wall of tiny bars is not comprehensive communication. Select a justified subset of sets, group lower-value combinations with a visible membership rule or offer a searchable intersection table. Do not hide suppressed small groups inside a falsely labeled zero. [[data-visualization/interactive-chart-keyboard-focus-and-data-table-contract|Keyboard and table access]] matters because a dot matrix alone cannot expose exact membership to every reader. If the set definitions drift across months, a stable-looking bar chart can still compare different concepts; publish the rule version beside the counts."),
        ],
        "code": '''def exact_intersections(records: dict[str, set[str]],
                        sets_in_order: list[str]):
    if not sets_in_order or len(sets_in_order) != len(set(sets_in_order)):
        raise ValueError("set names must be unique and nonempty")
    if any(not name for name in sets_in_order):
        raise ValueError("set names must be nonempty")
    known = set(sets_in_order)
    if any(not ticket_id or not membership <= known
           for ticket_id, membership in records.items()):
        raise ValueError("ticket IDs and memberships must be valid")
    counts = {}
    for membership in records.values():
        mask = tuple(name in membership for name in sets_in_order)
        counts[mask] = counts.get(mask, 0) + 1
    assert sum(counts.values()) == len(records)
    return counts

ticket_tags = {"ticket-47": {"Billing", "Returns"},
               "ticket-59": {"Billing", "Returns", "Delivery"},
               "ticket-83": {"Delivery"}, "ticket-97": set()}
set_order = ["Billing", "Delivery", "Returns"]
intersections = exact_intersections(ticket_tags, set_order)
assert intersections[(True, False, True)] == 1
assert intersections[(True, True, True)] == 1
assert intersections[(False, False, False)] == 1
assert sum(intersections.values()) == 4''',
        "cost": "For N records and K named sets, computing membership masks takes O(NK) time and O(MK) space for M observed masks, with M at most min(N, 2^K). The worst-case chart itself becomes difficult well before that bound. The function assumes each record key is already a unique entity and its tag collection is a set. It counts exact intersections, not inclusive overlaps, and deliberately retains the empty mask for reconciliation.",
        "mistakes": ["Summing set-size bars as if their members were disjoint.", "Labeling an inclusive SQL overlap as an exact intersection.", "Dropping the no-set group without explaining the changed universe.", "Reordering sets or redefining tags across comparison panels without a version note."],
        "drill": "Build an exact-mask ledger for 470 tickets and four tags. Reconcile every mask to the eligible universe, then compute one inclusive overlap separately and explain why the two counts differ.",
        "related": [prefix + "aggregation-grain-and-denominator", prefix + "mosaic-plots-joint-area-conditional-rate-and-empty-cells", prefix + "small-multiples-shared-scales-and-facet-order", prefix + "interactive-chart-keyboard-focus-and-data-table-contract"],
    },
    {
        "slug": "contour-plots-grid-masks-levels-and-interpolation-boundaries",
        "title": "Contour plots: respect measured grids and interpolation boundaries",
        "summary": "Read isolines and filled bands against a regular grid, declared contour levels and explicit missing-cell masks.",
        "sections": [
            ("Know what a contour line represents", "A contour line joins locations estimated to share one value of a continuous field. A filled contour uses bands between stated levels. Both require a coordinate system and an underlying surface. In a warehouse temperature survey, readings at sensor positions are observations; color between sensors is an interpolation model, not another measurement. If observations sit on an irregular mesh, state how they were gridded before rendering. [[data-visualization/heatmap-missing-cells-and-color-domain|A heatmap]] shows cell values directly and may be more honest when only measured cells matter. Contours are appropriate when spatial continuity is scientifically defensible and the uncertainty between samples is acceptable for the question."),
            ("Choose levels and preserve the numeric domain", "Use one ascending level list across panels that readers will compare. Automatic levels chosen independently for each frame can make unchanged values move to new colors. The legend should give units, exact boundaries and what happens below the first or above the last level. Do not choose dozens of bands merely to create a smooth-looking gradient; more colors do not add measurements. [[data-visualization/small-multiples-shared-scales-and-facet-order|Shared scales and panels]] apply to contours as well. Preserve the aspect ratio if x and y use comparable spatial units, and label a transformed coordinate axis if a map projection or other conversion changes distance. Separate contour lines from the base grid in an accessible data export."),
            ("Mask gaps rather than inventing a bridge", "Missing readings can create holes in the surface. Mark unavailable grid cells and state whether the renderer masks a cell, a vertex or any quadrilateral touching it; these policies have different visible footprints. Never replace an absent observation with zero just to satisfy a plotting library. A sensor fault along a wall can create an apparent cold band if imputed as zero. [[data-visualization/choropleth-rates-boundaries-and-missing-regions|Missing mapped regions]] present the same honest-versus-smooth choice. Show the sampled domain boundary and avoid extrapolating contours far outside the convex hull of observations unless an explicit physical model supports it."),
            ("Treat interpolation as a model to validate", "Linear interpolation within each grid cell can create straight segments even when the real field bends; smoothing can conceal localized peaks. Keep point markers or a linked table to show where measurements actually exist. Cross-validate by withholding sensors in several areas, compare predicted values against withheld readings and investigate systematic error near edges. [[data-visualization/uncertainty-and-small-sample-display|Uncertainty]] grows where sensors are sparse, while [[data-visualization/chart-export-manifest-data-and-render-version|render provenance]] should record grid version, interpolation method, level list and mask policy. For a decision about safety limits, publish the original measurements and margin near the threshold instead of relying on the contour image alone."),
        ],
        "code": '''from math import isfinite

def contour_cells(x_coordinates: list[float], y_coordinates: list[float],
                  values: list[list[float | None]], levels: list[float]):
    if len(x_coordinates) < 2 or len(y_coordinates) < 2:
        raise ValueError("a contour grid needs at least two points per axis")
    if any(not isfinite(position) for position in x_coordinates + y_coordinates):
        raise ValueError("coordinates must be finite")
    if any(right <= left for left, right in zip(x_coordinates, x_coordinates[1:])):
        raise ValueError("x coordinates must increase")
    if any(top <= bottom for bottom, top in zip(y_coordinates, y_coordinates[1:])):
        raise ValueError("y coordinates must increase")
    if len(values) != len(y_coordinates) or any(len(row) != len(x_coordinates) for row in values):
        raise ValueError("grid dimensions do not match axes")
    if len(levels) < 2 or any(not isfinite(level) for level in levels) or any(
            upper <= lower for lower, upper in zip(levels, levels[1:])):
        raise ValueError("at least two increasing finite levels are required")
    if any(reading is not None and not isfinite(reading)
           for row in values for reading in row):
        raise ValueError("observed values must be finite")
    usable = []
    masked = []
    for row in range(len(y_coordinates) - 1):
        for column in range(len(x_coordinates) - 1):
            corners = (values[row][column], values[row][column + 1],
                       values[row + 1][column], values[row + 1][column + 1])
            cell = (column, row)
            (usable if all(value is not None for value in corners) else masked).append(cell)
    return usable, masked

sensor_grid = [[18.0, 20.0, 22.0], [19.0, None, 24.0], [20.0, 23.0, 25.0]]
usable, masked = contour_cells([0.0, 47.0, 94.0], [0.0, 59.0, 118.0],
                               sensor_grid, [18.0, 21.0, 24.0, 27.0])
assert usable == []
assert masked == [(0, 0), (1, 0), (0, 1), (1, 1)]''',
        "cost": "Validating a grid with X columns, Y rows and L contour levels takes O(XY + X + Y + L) time and O(XY) output space for the cell audit. An actual contour renderer adds work that depends on its interpolation and line-tracing algorithm. This standard-library check does not draw isolines; it makes the mask rule explicit: any cell touching a missing corner is unavailable. A single missing center reading masks all four neighboring cells in the sample, rather than fabricating a continuous field.",
        "mistakes": ["Treating interpolated values as if they were sensor readings.", "Changing levels between comparison panels without announcing the change.", "Filling missing cells with zero and displaying a false low region.", "Drawing contours beyond the sampled domain without a model and uncertainty statement."],
        "drill": "Map 47 warehouse sensors on a fixed coordinate system. Hide three sensors, audit the masked cells, compare two fixed level sets, and record held-out interpolation error near the perimeter.",
        "related": [prefix + "heatmap-missing-cells-and-color-domain", prefix + "small-multiples-shared-scales-and-facet-order", prefix + "choropleth-rates-boundaries-and-missing-regions", prefix + "chart-export-manifest-data-and-render-version"],
    },
]

new_paths = [prefix + lesson["slug"] for lesson in lessons]
assert all(path not in by_path for path in new_paths)
titles = {path: row["title"] for path, row in by_path.items()}
titles.update(zip(new_paths, (lesson["title"] for lesson in lessons)))
marker = re.compile(r"\[\[([^|\]]+)\|([^\]]+)\]\]")

def render(value: str) -> str:
    parts, start = [], 0
    for match in marker.finditer(value):
        parts.append(html.escape(value[start:match.start()]))
        path, label = match.groups()
        if path not in titles:
            raise ValueError(f"broken link: {path}")
        parts.append(f'<a href="/{html.escape(path, quote=True)}">{html.escape(label)}</a>')
        start = match.end()
    return "".join(parts) + html.escape(value[start:])

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
        "featured": False, "sort_order": 8761 + offset, "status": "published",
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
    for start, end, heading in ((0, 2, "Model decisions and measurement agreement"),
                                (2, 4, "Set intersections and spatial surfaces")):
        targets = new_paths[start:end]
        row["data"]["modules"].append({"title": heading, "lessons": targets})
        row["body"] += f'<h2>{heading}</h2><ul>' + ''.join(
            f'<li>{link(target)}</li>' for target in targets) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "probability-calibration-plots-bin-counts-prevalence-and-drift": [new_paths[0]],
    prefix + "uncertainty-and-small-sample-display": [new_paths[0], new_paths[1]],
    prefix + "paired-change-slope-and-dumbbell-charts": [new_paths[1]],
    prefix + "asymmetric-error-bars-interval-type-and-axis-clipping": [new_paths[1]],
    prefix + "aggregation-grain-and-denominator": [new_paths[2]],
    prefix + "mosaic-plots-joint-area-conditional-rate-and-empty-cells": [new_paths[2]],
    prefix + "interactive-chart-keyboard-focus-and-data-table-contract": [new_paths[2]],
    prefix + "heatmap-missing-cells-and-color-domain": [new_paths[3]],
    prefix + "choropleth-rates-boundaries-and-missing-regions": [new_paths[3]],
    prefix + "small-multiples-shared-scales-and-facet-order": [new_paths[0], new_paths[3]],
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
