"""Publish four original Data Visualization lessons and reciprocal links."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-data-visualization-import-20261008-j.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "data-visualization/"
hub = prefix + "data-visualization-tutorial"

lessons = [
    {
        "slug": "chord-diagrams-directed-flows-self-loops-and-sector-totals",
        "title": "Chord diagrams: audit directed flows before drawing ribbons",
        "summary": "Turn a directed source-to-destination matrix into an auditable chord layout without hiding self-flows or double-counting totals.",
        "sections": [
            ("Fix the unit and direction first", "A chord diagram curls a square flow matrix around a circle. One row identifies the source; one column identifies the destination. A matrix entry can represent parcels moved between depots, but it cannot mix parcel count with shipment value. Decide whether the story is directed before any ribbons are drawn: a transfer from North to East is not the same record as East to North. If the values describe mutual relationships rather than movements, use an undirected contract and explain how two mirrored cells are consolidated. [[data-visualization/network-graph-identity-degree-and-layout-stability|Network graphs]] emphasize topology; chords emphasize the volume between a manageable set of named groups. Their apparent symmetry can mislead readers when source and destination have different meanings, so label the ends or use a visible directional cue."),
            ("Reconcile sectors and ribbons", "For a directed matrix, the outbound total of a group is its row sum and inbound total is its column sum. Decide whether each sector encodes outbound alone or inbound plus outbound; otherwise a sector width may appear to contradict its label. The worked contract below reports both. A transfer from a group to itself belongs on the diagonal and must be kept or explicitly excluded. Draw a self-loop distinctly because it can consume a large share of an arc without crossing the center. A ribbon should have an auditable value in an accompanying table. [[data-visualization/sankey-flow-conservation-and-unobserved-exits|Sankey diagrams]] are often clearer when a process has ordered stages and conservation across them must be inspected."),
            ("Keep categories and filters stable", "Arc order changes which ribbons overlap and can make the same data look dense or sparse. Set one documented category order across periods and filtered views. If an unseen group is grouped into Other, publish which group IDs it contains and keep its membership fixed when comparing periods. An interaction should reveal source, destination, amount, unit, time window and whether the value is a self-loop. It should also disclose the current filter cohort. [[data-visualization/linked-filters-cohort-denominators-and-selection-state|Linked filter state]] is part of the reading contract: a selected destination must not silently redefine the total behind each sector. Export the full matrix rather than only the visible top ribbons."),
            ("Use density as a stopping rule", "With 47 groups, there can be 2,209 directed cells before any filtering. Even a complete and accurate chord can become an unreadable knot. Start with a ranked table, a small set of stable groups or a matrix heatmap when precise cell comparisons matter. [[data-visualization/heatmap-missing-cells-and-color-domain|Heatmaps]] preserve a fixed row-column grid and make absent flows easier to spot. If the chord is retained, annotate whether zeros mean no observed movement or unavailable data, and provide text alternatives for keyboard and screen-reader access. Test the display at narrow widths; hiding labels does not remove the underlying ambiguity."),
        ],
        "code": '''def directed_flow_ledger(groups: list[str],
                         flows: dict[tuple[str, str], int]):
    if not groups or len(groups) != len(set(groups)) or any(not name for name in groups):
        raise ValueError("group names must be unique and nonempty")
    known = set(groups)
    if any(source not in known or target not in known or
           type(amount) is not int or amount < 0
           for (source, target), amount in flows.items()):
        raise ValueError("flow endpoints and amounts must be valid")
    matrix = [[flows.get((source, target), 0) for target in groups]
              for source in groups]
    outbound = {source: sum(matrix[index])
                for index, source in enumerate(groups)}
    inbound = {target: sum(matrix[index][column]
                           for index in range(len(groups)))
               for column, target in enumerate(groups)}
    assert sum(outbound.values()) == sum(inbound.values())
    return matrix, outbound, inbound

depots = ["North", "East", "West"]
transfers = {("North", "East"): 47, ("East", "North"): 13,
             ("North", "North"): 5, ("West", "East"): 29}
matrix, outbound, inbound = directed_flow_ledger(depots, transfers)
assert matrix[0] == [5, 47, 0]
assert outbound["North"] == 52
assert inbound["East"] == 76
assert sum(outbound.values()) == 94''',
        "cost": "For G groups, matrix construction takes O(G²) time and O(G²) space even when most flows are zero. The sparse input map is better for storage and for very large networks; the dense matrix is useful only when the chosen renderer requires it. The ledger counts each directed transfer once, including a self-loop, and proves that aggregate outbound equals aggregate inbound. It does not turn the chart into a conservation model across time: inventory changes and external entries still require their own rows.",
        "mistakes": ["Adding both directions into one ribbon while calling the result directed.", "Dropping self-loops because they do not cross the circle.", "Changing arc order or the membership of Other between comparison panels.", "Treating an unavailable matrix cell as an observed zero."],
        "drill": "Audit 59 transfer routes between five depots. Reconcile each outbound and inbound subtotal, then compare a chord with a matrix table at phone width.",
        "related": [prefix + "sankey-flow-conservation-and-unobserved-exits", prefix + "network-graph-identity-degree-and-layout-stability", prefix + "heatmap-missing-cells-and-color-domain", prefix + "linked-filters-cohort-denominators-and-selection-state"],
    },
    {
        "slug": "bivariate-choropleths-two-rates-nine-classes-and-joint-legends",
        "title": "Bivariate choropleths: map two rates with a readable joint legend",
        "summary": "Classify two regional rates independently, then document all nine combinations, denominators and missing regions.",
        "sections": [
            ("Make each variable a comparable regional rate", "A bivariate choropleth gives each area one color based on two measurements. First establish a meaningful rate for each variable, with its own numerator, denominator, period and units. Coloring counties by raw counts mainly maps population size, while comparing a rate from 2024 with another from 2026 can imply a joint pattern that never existed at one time. Check whether the geography is identical for both data sets and whether boundary changes have been resolved. [[data-visualization/choropleth-rates-boundaries-and-missing-regions|Single-variable choropleths]] explain why boundary version and denominator belong in the legend. If two measures cannot be made comparable, separate maps with explicit units are the honest choice."),
            ("Classify each axis before mixing color", "A typical joint legend has three classes for the horizontal measure and three for the vertical measure. That yields nine named combinations, such as low–high, not nine unlabeled shades. Declare two cut points per variable and how exact boundary values are handled. The code uses lower-inclusive classes: a value equal to the first cut moves into the middle class. Choose cut points against the analytic question, then freeze them across panels. Recomputing quantiles on every filter action can cause a region's color to change even when its rate does not. [[data-visualization/small-multiples-shared-scales-and-facet-order|Shared scales]] apply to map panels too. A 3×3 legend should label both axes, their directions and the numeric boundaries."),
            ("Separate missingness from low values", "A region missing either measure has no joint class. Give it a separate visible symbol and a table row explaining which measure is missing. A zero is a valid numeric value only when the upstream measurement process really observed zero. Suppression of small counts is not zero, and imputing it can distort a rate. [[data-visualization/heatmap-missing-cells-and-color-domain|Heatmap missing cells]] face the same distinction. Reconcile the number of mapped, missing, suppressed and excluded regions before styling. If an area has a tiny denominator, attach count and uncertainty in a companion table so its saturated color is not mistaken for strong evidence."),
            ("Use the map for patterns, the table for values", "Nine colors are hard to decode from memory, especially when several patches are similar or the map is viewed on a small display. Test the palette under common color-vision differences and in grayscale; provide class text and both exact rates on focus or in a linked table. A bivariate map can suggest a spatial association, but it does not establish that one measure causes the other. Large regions occupy more screen area regardless of population, and neighboring regions are not independent evidence by default. [[data-visualization/accessible-color-and-text-alternatives|Accessible color and text alternatives]] should be part of the export, not an afterthought. Include the breakpoints, data period, geographic key and unmapped-count summary with every image."),
        ],
        "code": '''from math import isfinite

def joint_rate_classes(regions: list[tuple[str, float | None, float | None]],
                       first_cuts: tuple[float, float],
                       second_cuts: tuple[float, float]):
    if not (first_cuts[0] < first_cuts[1] and second_cuts[0] < second_cuts[1]):
        raise ValueError("each pair of cuts must increase")
    if len({region for region, _, _ in regions}) != len(regions):
        raise ValueError("region keys must be unique")
    cells = []
    for region, first_rate, second_rate in regions:
        if not region:
            raise ValueError("region key is required")
        if first_rate is None or second_rate is None:
            cells.append((region, None, first_rate, second_rate))
            continue
        if not isfinite(first_rate) or not isfinite(second_rate):
            raise ValueError("rates must be finite")
        first_class = sum(first_rate >= cut for cut in first_cuts)
        second_class = sum(second_rate >= cut for cut in second_cuts)
        cells.append((region, (first_class, second_class),
                      first_rate, second_rate))
    return cells

service_regions = [("ward-47", 12.0, 31.0),
                   ("ward-59", 19.0, 45.0),
                   ("ward-83", None, 24.0)]
classified = joint_rate_classes(service_regions, (12.0, 18.0), (25.0, 40.0))
assert classified[0][1] == (1, 1)
assert classified[1][1] == (2, 2)
assert classified[2][1] is None''',
        "cost": "Classifying R regions takes O(R) time and O(R) output space; the nine-color lookup is constant size. The function preserves exact rates and missingness alongside class coordinates, and its assertions pin the breakpoint tie rule. It assumes both inputs are already compatible rates. Validate numerators, denominators, units, boundary version and time window upstream before interpreting any mapped class.",
        "mistakes": ["Mixing raw counts with rates in one joint legend.", "Recomputing class breaks separately for each period while comparing colors.", "Coloring a suppressed or absent rate as low.", "Shipping nine colors without numeric boundaries or an accessible table."],
        "drill": "Classify 47 wards for two service rates. Report all nine cell counts plus missing regions, and test whether the map stays interpretable in grayscale.",
        "related": [prefix + "choropleth-rates-boundaries-and-missing-regions", prefix + "small-multiples-shared-scales-and-facet-order", prefix + "heatmap-missing-cells-and-color-domain", prefix + "accessible-color-and-text-alternatives"],
    },
    {
        "slug": "dendrograms-linkage-distance-cut-height-and-leaf-order",
        "title": "Dendrograms: read merge height without overreading leaf order",
        "summary": "Audit distance, linkage and cut height before labeling clusters from a hierarchical tree.",
        "sections": [
            ("A tree is built from a distance rule", "A dendrogram shows a sequence of cluster merges. Its shape depends first on what distance means: Euclidean distance on raw fields lets large-unit features dominate, while a domain-specific distance may weight errors or missingness differently. Standardize only when that operation fits the question and record the fitted scaling parameters. Then choose a linkage rule. Single linkage merges by the nearest pair of members and can chain points; complete linkage uses the farthest pair; average linkage uses the mean of pair distances. These are different cluster definitions, not styling options. [[data-visualization/correlation-heatmap-pairwise-coverage-and-ordering|Correlation heatmaps]] often sit next to a dendrogram, but the correlation-to-distance transformation must be stated if it creates the tree."),
            ("Read height, not horizontal spacing", "The vertical coordinate of a merge records the linkage distance at which its child clusters join. Horizontal leaf placement is usually a layout choice: sibling branches can be rotated without changing any membership or merge distance. Do not infer that two neighboring leaf labels are the closest original pair merely because they appear adjacent. Put the distance metric and linkage rule in the caption, and label the merge-height axis with units or a dimensionless scale. A flat cut at a chosen height partitions the leaves, but that height is a decision threshold, not a statistical test. [[data-visualization/chart-question-and-visual-encoding|The chart question]] should say whether the reader needs a hierarchy, a fixed number of groups or actual pairwise distances."),
            ("Inspect unstable merges", "Small changes in records or scaling can reorder merges near the same height. A visually dramatic split is not automatic evidence of a natural population boundary. Refit after reasonable perturbations, compare membership and report how often groups persist; keep the data snapshot fixed while changing one assumption at a time. If a leaf represents a collapsed branch, show how many original members it contains. Truncating a large dendrogram can hide lower merges, so label contracted nodes explicitly. [[data-visualization/uncertainty-and-small-sample-display|Uncertainty displays]] are useful when the tree is used to support a decision, especially with few observations or noisy distances. Keep an accessible membership table for every cut shown."),
            ("Choose the right comparison view", "A tree can hold many leaves but becomes difficult to read at phone width. For a few entities, a labeled distance matrix may answer the exact-pair question faster. For many groups, a cut-level summary and downloadable membership table are more useful than microscopic text. In linked views, selecting a branch should highlight its exact IDs in the associated chart without recomputing the clustering under the cursor. [[data-visualization/linked-filters-cohort-denominators-and-selection-state|Linked filters]] should disclose whether they merely highlight a fixed tree or rebuild it from a filtered population. Rebuilding changes the merge history and needs a new analysis version in the export."),
        ],
        "code": '''from math import isfinite

def average_linkage_merges(values: dict[str, float]):
    if len(values) < 2 or any(not label or not isfinite(value)
                              for label, value in values.items()):
        raise ValueError("at least two finite labeled observations are required")
    clusters = {label: (label,) for label in values}
    merges = []
    while len(clusters) > 1:
        candidates = []
        labels = sorted(clusters)
        for left_index, left in enumerate(labels):
            for right in labels[left_index + 1:]:
                distances = [abs(values[first] - values[second])
                             for first in clusters[left] for second in clusters[right]]
                candidates.append((sum(distances) / len(distances), left, right))
        height, left, right = min(candidates)
        members = tuple(sorted(clusters.pop(left) + clusters.pop(right)))
        cluster_id = "|".join(members)
        clusters[cluster_id] = members
        merges.append((members, height))
    return merges

sensor_offsets = {"sensor-47": 4.0, "sensor-59": 5.0,
                  "sensor-83": 19.0, "sensor-97": 21.0}
merges = average_linkage_merges(sensor_offsets)
assert merges[0] == (("sensor-47", "sensor-59"), 1.0)
assert merges[1] == (("sensor-83", "sensor-97"), 2.0)
assert merges[2][1] == 15.5''',
        "cost": "This transparent teaching implementation recomputes all candidate average distances at every merge. For N observations it uses O(N³) time in the worst case and O(N²) temporary space: each merge compares pair distances across the current partition; use a tested clustering library for real data. Its scalar absolute-distance rule is deliberately narrow. The output provides memberships and heights, not leaf x-coordinates. Those can be rearranged without changing the hierarchy.",
        "mistakes": ["Reading adjacent leaves as the closest original observations.", "Changing the distance metric or scaling without documenting a new tree.", "Treating a chosen cut height as a significance threshold.", "Truncating branches without their member counts or a membership table."],
        "drill": "Cluster 47 sensor offsets using two distance definitions. Save both trees, compare cut memberships and explain which merges changed because of the metric.",
        "related": [prefix + "correlation-heatmap-pairwise-coverage-and-ordering", prefix + "chart-question-and-visual-encoding", prefix + "uncertainty-and-small-sample-display", prefix + "linked-filters-cohort-denominators-and-selection-state"],
    },
    {
        "slug": "probability-calibration-plots-bin-counts-prevalence-and-drift",
        "title": "Probability calibration plots: compare predicted risk with observed frequency",
        "summary": "Build a reliability table with honest bin counts, event rates and a fixed evaluation cohort.",
        "sections": [
            ("Separate ranking from calibrated probability", "A score can rank likely events well yet overstate their chance. A calibration plot asks whether cases assigned a given probability experience the event at approximately that frequency. For an equipment-alert model, a group with average predicted failure probability 0.31 should have an observed failure share near 0.31 over a sufficiently large, representative evaluation set. This is not a claim about any single device. [[data-visualization/scatterplot-regression-overlays-fit-scope-and-prediction-bands|Regression overlays]] often invite a best-fit line; a calibration plot instead compares observed and predicted rates against the identity diagonal. Ranking metrics, decision thresholds and the cost of false alarms answer different questions and should be displayed separately."),
            ("Construct bins without concealing support", "Partition predictions with a stated rule. Equal-width bins have stable numeric boundaries but may leave some bins thin; equal-count bins balance support yet their boundaries move between cohorts. For each nonempty bin, plot mean predicted probability on x and observed event fraction on y. Include count and event count in a table or label, because a point based on 7 cases is not as stable as one based on 700. Do not join empty bins with a line. The code uses fixed equal-width bins and makes p=1 belong to the final bin. [[data-visualization/uncertainty-and-small-sample-display|Small-sample displays]] explain why approximate agreement needs interval context, especially near the extremes."),
            ("Protect the evaluation split", "Calibration estimated on the same records used to fit or tune a model is optimistic. Hold out an evaluation period or cohort and keep its definition stable. If scores are recalibrated, fit that transformation on a separate calibration set, then evaluate it on untouched data. Log model version, score timestamp, outcome window and censoring or delayed-label policy. A device marked as no failure before its observation window closes is not a verified negative. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Provisional periods]] must be separated from complete labels. Also show prevalence: when base failure rate shifts between cohorts, the curve may move even if the model's ranking stays useful."),
            ("Inspect slices and drift carefully", "A global curve can hide one badly miscalibrated plant or device family. Compare slices only when each has enough cases, and keep the same bin boundaries and evaluation window. Report omitted records and missing scores. Point movement between months may be sampling noise, model drift or a change in who gets scored; the plot alone cannot distinguish them. [[data-visualization/small-multiples-shared-scales-and-facet-order|Small multiples with shared scales]] make comparisons less deceptive, while [[data-visualization/chart-export-manifest-data-and-render-version|an export manifest]] keeps model and data versions attached to the image. Provide the underlying bin table so readers can check the plotted rates rather than measuring the diagonal by eye."),
        ],
        "code": '''from math import isfinite

def calibration_bins(records: list[tuple[str, float, bool]], width: int = 5):
    if type(width) is not int or width <= 0:
        raise ValueError("bin count must be positive")
    identifiers = [device_id for device_id, _, _ in records]
    if len(identifiers) != len(set(identifiers)) or any(not item for item in identifiers):
        raise ValueError("device IDs must be unique and nonempty")
    bins = [[0, 0.0, 0] for _ in range(width)]
    for _, probability, failed in records:
        if (not isfinite(probability) or not 0 <= probability <= 1
                or type(failed) is not bool):
            raise ValueError("probabilities and event flags must be valid")
        bucket = min(int(probability * width), width - 1)
        bins[bucket][0] += 1
        bins[bucket][1] += probability
        bins[bucket][2] += failed
    return [(bucket, count, score_sum / count, events / count, events)
            for bucket, (count, score_sum, events) in enumerate(bins)
            if count]

inspection_results = [("unit-47", 0.22, False),
                      ("unit-59", 0.31, True),
                      ("unit-83", 0.37, False),
                      ("unit-97", 1.0, True)]
reliability = calibration_bins(inspection_results)
assert reliability[0] == (1, 3, 0.3, 1 / 3, 1)
assert reliability[1] == (4, 1, 1.0, 1.0, 1)''',
        "cost": "For N predictions and B fixed bins, accumulation takes O(N + B) time and O(B + N) space because unique IDs are validated. Empty bins are omitted rather than invented. The four-record check demonstrates bin assignment and arithmetic, not credible calibration evidence; real evaluation needs sufficient support, a held-out cohort and uncertainty intervals. The function does not estimate those intervals or repair delayed labels.",
        "mistakes": ["Using training records as the final reliability evaluation.", "Plotting one bin point without its case count or event count.", "Calling a high-ranking score calibrated without comparing observed frequency.", "Treating unfinished outcome windows as verified negatives."],
        "drill": "Hold out 470 device predictions. Build fixed bins for two months, print counts and event rates, then identify whether a shifted curve also coincides with changed prevalence or incomplete labels.",
        "related": [prefix + "uncertainty-and-small-sample-display", prefix + "small-multiples-shared-scales-and-facet-order", prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "chart-export-manifest-data-and-render-version"],
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
        "featured": False, "sort_order": 8757 + offset, "status": "published",
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
    for start, end, heading in ((0, 2, "Flow and geographic comparisons"),
                                (2, 4, "Hierarchy and probability evidence")):
        targets = new_paths[start:end]
        row["data"]["modules"].append({"title": heading, "lessons": targets})
        row["body"] += f'<h2>{heading}</h2><ul>' + ''.join(
            f'<li>{link(target)}</li>' for target in targets) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "sankey-flow-conservation-and-unobserved-exits": [new_paths[0]],
    prefix + "network-graph-identity-degree-and-layout-stability": [new_paths[0]],
    prefix + "choropleth-rates-boundaries-and-missing-regions": [new_paths[1]],
    prefix + "accessible-color-and-text-alternatives": [new_paths[1]],
    prefix + "correlation-heatmap-pairwise-coverage-and-ordering": [new_paths[2]],
    prefix + "chart-question-and-visual-encoding": [new_paths[2]],
    prefix + "uncertainty-and-small-sample-display": [new_paths[2], new_paths[3]],
    prefix + "small-multiples-shared-scales-and-facet-order": [new_paths[1], new_paths[3]],
    prefix + "chart-export-manifest-data-and-render-version": [new_paths[3]],
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
