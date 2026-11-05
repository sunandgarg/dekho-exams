"""Publish a second set of original Data Visualization lessons."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-data-visualization-import-20261008-b.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "data-visualization/"
hub = prefix + "data-visualization-tutorial"

lessons = [
    {
        "slug": "stacked-bars-composition-and-changing-denominators",
        "title": "Stacked bars: separate composition from volume and preserve denominators",
        "summary": "Use absolute and normalized stacks for different questions, and retain every segment count.",
        "sections": [
            ("A stack has two possible questions", "An absolute stacked bar shows a total and its parts in the same unit. A normalized bar forces every total to one and shows the mix instead. These are not interchangeable. If depot A closes 47 of 81 requests while depot B closes 470 of 810, both have the same closed share, but the latter carries ten times the workload. Place total and share in adjacent views when both matter. [[data-visualization/aggregation-grain-and-denominator|Define the denominator]] before calculating either bar. The title should say whether the horizontal extent means requests or a fraction of eligible requests."),
            ("Keep categories stable", "Assign each status one color and one position across periods. If a status disappears, retain its zero-valued place in the data contract rather than shifting every later segment. The unanchored middle segments in a stack are difficult to compare precisely; when one category is the focus, use a grouped bar or a separate trend. Sort bars by a declared metric, such as eligible volume, and keep that order fixed across comparison panels. [[data-visualization/small-multiples-shared-scales-and-facet-order|Facet ordering]] follows the same rule."),
            ("Handle absent and ineligible records", "A missing status is not necessarily a measured zero. If the warehouse omits unresolved requests, a normalized stack can show an apparently perfect closure rate even as the unobserved group grows. Reconcile segment counts to the cohort total, expose an unknown state, and reserve a separate no-exposure state when the denominator is zero. A percentage bar for zero eligible requests has no defined composition. [[data-visualization/heatmap-missing-cells-and-color-domain|Missing-state display]] should use a label or pattern in addition to color."),
            ("Audit every filter", "When a dashboard filters by region or week, recompute each segment count from the selected cohort and normalize only after filtering. Do not average prior percentages. Tooltips and exports should include segment count, denominator and percentage; rounded shares may sum to 99.9 or 100.1, which is a display effect rather than a data error. [[data-visualization/linked-filters-cohort-denominators-and-selection-state|Linked selections]] must update totals and segments together. Test one-bar, zero-cohort and category-absent states before release."),
        ],
        "code": '''def composition_by_depot(
    counts: dict[str, dict[str, int]], statuses: tuple[str, ...]
) -> dict[str, dict[str, tuple[int, float | None]]]:
    if len(set(statuses)) != len(statuses) or not statuses:
        raise ValueError("statuses must be unique and nonempty")
    result = {}
    for depot, segments in counts.items():
        if set(segments) - set(statuses) or any(value < 0 for value in segments.values()):
            raise ValueError("unknown status or negative count")
        total = sum(segments.values())
        result[depot] = {
            status: (segments.get(status, 0),
                     segments.get(status, 0) / total if total else None)
            for status in statuses
        }
    return result

mix = composition_by_depot(
    {"north": {"closed": 47, "pending": 34},
     "south": {"closed": 470, "pending": 340}},
    ("closed", "pending", "unknown"))
assert mix["north"]["closed"] == (47, 47 / 81)
assert mix["south"]["closed"] == (470, 470 / 810)
assert mix["north"]["unknown"] == (0, 0.0)''',
        "cost": "For D depots, S declared statuses and M supplied segment values, validation and construction take O(M + DS) expected time and O(DS) output space. Reusing a prebuilt status set removes repeated set construction in a larger implementation. Rendering a normalized bar still needs the absolute counts for labels and audit. The example treats an absent segment as observed zero only under the stated complete-status contract; without that contract, an absent segment must be marked unknown.",
        "mistakes": ["Reading equal-width normalized bars as equal workloads.", "Dropping unresolved statuses before calculating shares.", "Changing stack order between weeks and implying a category moved.", "Averaging percentages instead of adding segment counts first."],
        "drill": "Prepare 13 weekly depot bars with different cohort sizes. Show absolute and normalized versions, then remove one status record from a source extract and verify reconciliation fails rather than silently improving a percentage.",
        "related": [prefix + "aggregation-grain-and-denominator", prefix + "small-multiples-shared-scales-and-facet-order", prefix + "linked-filters-cohort-denominators-and-selection-state", prefix + "heatmap-missing-cells-and-color-domain"],
    },
    {
        "slug": "log-and-symmetric-log-scales-with-zero-values",
        "title": "Logarithmic axes: disclose zero handling and the linear threshold",
        "summary": "Use transformed axes for multiplicative comparisons without silently deleting zeros or negative values.",
        "sections": [
            ("Distance changes meaning", "A linear axis gives equal pixel distance to equal additive differences. A log axis gives equal distance to equal ratios: moving from 8 to 80 occupies the same distance as moving from 80 to 800 at base ten. This can reveal multiplicative growth across orders of magnitude, but it can also disguise an operational change measured in fixed units. Print the axis transformation and ticks prominently. [[data-visualization/scale-baseline-and-axis-integrity|Baseline and scale integrity]] still matters when the axis no longer has a visually useful zero."),
            ("Zero cannot sit on a log axis", "The logarithm of zero is undefined, as is the real logarithm of a negative count. A plotting tool may drop these rows, clip them or show a warning. None of those choices should happen silently. Count excluded values before drawing and put that count near the chart. Adding one to every value changes the estimand and can greatly change small counts, so it needs a stated measurement reason rather than being a default repair. For rates, check whether zero reflects a genuine observation or a missing denominator. [[data-visualization/aggregation-grain-and-denominator|Denominator policy]] comes first."),
            ("Signed measures need another contract", "A symmetric-log scale keeps a linear region around zero and transitions to log-like spacing outside a chosen threshold. It can display positive and negative deviations across a wide range, but the threshold controls the visual emphasis around zero. State its numeric value and show at least the threshold ticks. Alternatively, use separate panels or a linear scale when precise near-zero comparisons matter. Never tell a reader that equal distances have one consistent meaning across the linear and log regions. [[data-visualization/small-multiples-shared-scales-and-facet-order|Comparison panels]] should share the same threshold."),
            ("Test the reading task", "Give reviewers two exact questions: which site doubled, and which gained more units? If the axis helps one task but hinders the other, pair it with a table or linear companion view. Annotate omitted nonpositive values and preserve them in the export. Tooltips should report original measurements, not transformed coordinates. [[data-visualization/chart-export-manifest-data-and-render-version|The export manifest]] must record scale type, base, threshold, units and exclusion policy. Test values just below and above the threshold to catch a misleading transition."),
        ],
        "code": '''from math import isclose, isfinite, log10

def log_axis_values(readings: list[float]) -> tuple[list[float], int]:
    if any(not isfinite(reading) for reading in readings):
        raise ValueError("non-finite reading")
    positive = [reading for reading in readings if reading > 0]
    return [log10(reading) for reading in positive], len(readings) - len(positive)

def signed_axis_coordinate(reading: float, threshold: float) -> float:
    if not isfinite(reading) or not isfinite(threshold) or threshold <= 0:
        raise ValueError("invalid reading or threshold")
    magnitude = abs(reading)
    mapped = magnitude / threshold if magnitude <= threshold else 1 + log10(magnitude / threshold)
    return -mapped if reading < 0 else mapped

positions, omitted = log_axis_values([0, 8, 80, 800])
assert omitted == 1 and isclose(positions[2] - positions[1], 1)
assert signed_axis_coordinate(-47, 1) == -signed_axis_coordinate(47, 1)''',
        "cost": "Mapping N values takes O(N) time and O(N) output space; counting exclusions can be streamed with O(1) additional state. Axis ticks, inverse mapping and renderer behavior add separate costs. The signed mapping is an instructional contract, not a drop-in replacement for a plotting library's symmetric-log formula; choose and document one renderer's exact transform before comparing saved coordinates. Preserve original values for exports and accessible text.",
        "mistakes": ["Allowing the renderer to drop zero observations without a visible count.", "Adding one to every count without explaining the changed ratio near zero.", "Comparing panels that use different symmetric-log thresholds.", "Describing distance on a log axis as an additive difference."],
        "drill": "Chart 31 sensors ranging from zero to 81,000 units. Answer both multiplicative and additive questions, count all omitted values, and repeat a signed-deviation view with two declared thresholds to show what changes.",
        "related": [prefix + "scale-baseline-and-axis-integrity", prefix + "small-multiples-shared-scales-and-facet-order", prefix + "chart-export-manifest-data-and-render-version", prefix + "aggregation-grain-and-denominator"],
    },
    {
        "slug": "paired-change-slope-and-dumbbell-charts",
        "title": "Paired-change charts: match entities before drawing a slope",
        "summary": "Use slope and dumbbell views only after the before-and-after population is reconciled.",
        "sections": [
            ("The line encodes identity", "A slope chart connects two measurements for the same entity. Its line claims a valid pair, not just two values with matching labels. If a store was renamed, split or absent in one period, resolve that identity before drawing. A join on display name can connect unrelated stores, while a broad outer join can make missing endpoints look like zero. [[data-science/dataset-grain-and-join-cardinality|Join cardinality]] should be checked at one row per entity and period. Record which entities were excluded from the paired population."),
            ("Choose difference or ratio deliberately", "A dumbbell chart places two points on a shared quantitative scale; a slope chart emphasizes direction between endpoints. The axis unit and baseline decide whether a move appears large. A change from 47 to 81 is 34 units and about 72 percent of the starting value, but those answer different questions. For baseline zero, a percentage change is undefined. State which measure is encoded by the sorted order and put exact start, end and difference in accessible text. [[data-visualization/scale-baseline-and-axis-integrity|Axis rules]] apply to both forms."),
            ("Control clutter and crossings", "With dozens of entities, labels and crossing segments become hard to follow. Sort by one declared endpoint or difference, keep label positions consistent, and consider small multiples or a ranked difference bar when comparison is more important than identity tracking. Highlight selected entities without fading the rest into illegibility. A connected pair should use a line style, endpoint labels or shape in addition to color. [[data-visualization/accessible-color-and-text-alternatives|Accessible encodings]] matter when the positive and negative groups share a palette."),
            ("Check comparability across periods", "Before-after values may use different denominator definitions, currencies, coverage windows or measurement instruments. Do not join a complete prior quarter to an incomplete current quarter. Record the cohort cutoff and period length. If the chart includes only entities observed in both periods, say how many were lost and whether they differ from those retained; survivorship can reverse the narrative. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Provisional-period handling]] also applies when there are only two points."),
        ],
        "code": '''def paired_depot_change(
    prior: dict[str, int | None], current: dict[str, int | None]
) -> tuple[list[tuple[str, int, int, int]], set[str]]:
    if any(value is not None and value < 0 for value in [*prior.values(), *current.values()]):
        raise ValueError("negative request count")
    matched = []
    excluded = set(prior) | set(current)
    for depot_id in sorted(set(prior) & set(current)):
        before, after = prior[depot_id], current[depot_id]
        if before is None or after is None:
            continue
        matched.append((depot_id, before, after, after - before))
        excluded.remove(depot_id)
    return matched, excluded

pairs, absent = paired_depot_change(
    {"depot-47": 47, "depot-81": 81, "depot-94": 31},
    {"depot-47": 81, "depot-81": None, "depot-109": 40})
assert pairs == [("depot-47", 47, 81, 34)]
assert absent == {"depot-81", "depot-94", "depot-109"}''',
        "cost": "For P prior and C current entities, hash-set intersection and validation take O(P + C) expected time; sorting K matched IDs takes O(K log K), with O(P + C) temporary space. If an ordered warehouse query already supplies stable IDs, sorting can be handled upstream. The excluded set is part of the chart contract; deleting it to make the visualization tidy hides selection bias. A renderer still needs label-collision handling for crowded panels.",
        "mistakes": ["Connecting two stores with the same display name but different stable IDs.", "Substituting zero for a missing endpoint.", "Showing a percentage increase when the baseline is zero.", "Ignoring entities absent from the second period when describing the population."],
        "drill": "Compare 47 depots across two quarters. Plant a renamed depot, a split depot and four incomplete current-quarter records; reconcile identity and report matched and excluded counts before drawing slopes.",
        "related": [prefix + "scale-baseline-and-axis-integrity", prefix + "small-multiples-shared-scales-and-facet-order", prefix + "accessible-color-and-text-alternatives", prefix + "time-series-gaps-calendars-and-provisional-periods"],
    },
    {
        "slug": "empirical-cdf-percentiles-and-tail-reading",
        "title": "Empirical CDFs: read thresholds and tails without choosing bins",
        "summary": "Construct a cumulative distribution from observed values, preserving ties and sample size.",
        "sections": [
            ("The step answers a threshold question", "An empirical cumulative distribution function, or ECDF, gives the fraction of observed values less than or equal to each threshold. A point at 47 minutes and 0.8 means 80 percent of observations took at most 47 minutes. Unlike a histogram, it needs no bin width, so comparisons across groups are less sensitive to display choices. It still depends on the population, missing-value policy and observation window. [[data-visualization/distribution-and-outlier-displays|Distribution plots]] should expose those rules before any percentile is interpreted."),
            ("Ties produce one jump", "Repeated measurements at the same value create one larger step. If 31 of 81 jobs finish at exactly 12 minutes, the ECDF rises by 31/81 there; do not create a fake continuous slope between identical values. To compute a nearest-rank percentile, choose the first observed value whose cumulative share meets or exceeds the requested probability. Other quantile conventions interpolate and can return a number no job achieved. State the convention, especially for service targets. [[applied-statistics/population-estimand-and-sampling-frame|Sampling rules]] determine whether a percentile describes all jobs or a selected frame."),
            ("Keep the tail visible", "Most observations can cluster near a short duration while a few long delays drive customer pain. An ECDF makes the proportion under a service threshold easy to read, but the far-right tail may still be squeezed by the axis. Add an inset, tail table or direct threshold counts when the rare cases matter. A survival-style complementary curve, one minus the ECDF, answers what fraction exceeds a threshold; be clear about strict versus inclusive inequalities at ties. [[data-visualization/uncertainty-and-small-sample-display|Small samples]] need counts beside smooth-looking curves."),
            ("Compare only compatible cohorts", "Two curves can differ because of case mix, eligibility, time window or measurement precision. Use consistent axis limits and units, label sample sizes, and show whether pending cases were excluded or censored. A naive ECDF of only completed jobs makes the slow unfinished work disappear. For a queue with unresolved jobs, use an analysis that handles censoring or restrict the claim to completed jobs. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Observation status]] is part of the underlying data, not a cosmetic legend choice."),
        ],
        "code": '''from math import ceil, isfinite

def completion_ecdf(minutes: list[float]) -> list[tuple[float, int, float]]:
    if not minutes or any(not isfinite(value) or value < 0 for value in minutes):
        raise ValueError("need finite nonnegative durations")
    ordered = sorted(minutes)
    steps = []
    for value in ordered:
        if steps and steps[-1][0] == value:
            steps[-1] = (value, steps[-1][1] + 1, 0.0)
        else:
            steps.append((value, 1, 0.0))
    cumulative = 0
    result = []
    for value, tied, _ in steps:
        cumulative += tied
        result.append((value, tied, cumulative / len(ordered)))
    return result

durations = [12, 12, 31, 47, 81]
curve = completion_ecdf(durations)
nearest_rank_80 = sorted(durations)[ceil(0.8 * len(durations)) - 1]
assert curve[0] == (12, 2, 0.4)
assert curve[-1][2] == 1.0 and nearest_rank_80 == 47''',
        "cost": "Sorting N durations costs O(N log N) time and O(N) space for the ordered copy and output; scanning ties is O(N). Already-sorted warehouse output avoids the local sort. A chart with many distinct observations may still need visual reduction at screen resolution, but threshold queries should use the exact ordered values. The simple ECDF treats every supplied duration as complete and equally weighted; it is not a censored-data estimator.",
        "mistakes": ["Reading a completed-only ECDF as the distribution of all started jobs.", "Treating a large jump at a tied value as a renderer defect.", "Quoting a percentile without its sample size and quantile convention.", "Moving axis bounds between cohorts and comparing apparent steepness."],
        "drill": "Build curves for two depot cohorts of 47 and 81 completed cases. Include repeated durations and unresolved work, then report the fraction within 31 minutes and exactly which cases were excluded.",
        "related": [prefix + "distribution-and-outlier-displays", prefix + "uncertainty-and-small-sample-display", prefix + "large-series-level-of-detail-and-extrema", prefix + "time-series-gaps-calendars-and-provisional-periods"],
    },
    {
        "slug": "sankey-flow-conservation-and-unobserved-exits",
        "title": "Sankey diagrams: reconcile flows before sizing links",
        "summary": "Make every stage transition accountable, including dropouts and unobserved destinations.",
        "sections": [
            ("A link represents a transfer", "A Sankey diagram uses link width to encode quantity moving between stages. The visual claim is stronger than a list of counts: a unit leaving one stage must either enter a named next stage, exit the process, or remain unobserved under a declared cutoff. If 81 claims enter triage and 47 reach review, the other 34 need a visible destination, not an unexplained gap. [[data-visualization/aggregation-grain-and-denominator|Unit-of-analysis rules]] prevent one claim with multiple events from becoming several flows."),
            ("Give nodes stage-specific identities", "The same label at two stages does not necessarily describe the same state. Use stable stage and state IDs, deduplicate by entity and transition, and decide how repeated or backward transitions are handled. A diagram that assumes a directed acyclic process can fail when work returns to triage. In that case, either aggregate one chosen journey window or use another graph view that represents loops. [[data-visualization/network-graph-identity-degree-and-layout-stability|Network diagrams]] can show cycles, though they answer a different question."),
            ("Check conservation at intermediate stages", "For a closed interval, incoming and outgoing measured quantities at a transit state should balance after explicit additions, losses and stock change. If 47 enter review and 42 leave, five may still be in progress; add a pending exit or annotate the stock. For a live interval, arrivals and departures can differ because the cohort has not matured. Attach extraction time and observation horizon to the flow, and never compare incoming of one cohort to outgoing of another. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Provisional periods]] need separate handling."),
            ("Make ordering and scale inspectable", "Link crossing is partly a layout choice. Reordering nodes can reduce crossings without changing the data, so visual proximity must not be treated as a causal relation. Show quantities, units and denominators in text or a companion table. Fixed link colors can track origin across stages, but blending may obscure a small branch; direct labels or hover summaries help. [[data-visualization/accessible-color-and-text-alternatives|Accessible alternatives]] should list source, target and value. Large graphs may be better as a transition table."),
        ],
        "code": '''from collections import defaultdict

def reconcile_flow(
    links: list[tuple[str, str, int]], transit_nodes: set[str]
) -> dict[str, tuple[int, int]]:
    incoming = defaultdict(int)
    outgoing = defaultdict(int)
    for source, target, quantity in links:
        if not source or not target or quantity < 0:
            raise ValueError("invalid flow link")
        outgoing[source] += quantity
        incoming[target] += quantity
    balances = {node: (incoming[node], outgoing[node]) for node in transit_nodes}
    if any(entered != left for entered, left in balances.values()):
        raise ValueError(f"unreconciled transit node: {balances}")
    return balances

journey = [("intake", "review", 47),
           ("intake", "unobserved-exit", 34),
           ("review", "closed", 42),
           ("review", "pending", 5)]
assert reconcile_flow(journey, {"review"}) == {"review": (47, 47)}
assert sum(value for source, _, value in journey if source == "intake") == 81''',
        "cost": "For E links and T transit nodes, accumulation and reconciliation take O(E + T) expected time and O(V) space for V encountered nodes. Layout can be substantially more expensive and depends on the rendering algorithm; do not mix that cost with the inexpensive accounting check. A real workflow also checks duplicate entity transitions and whether stock change belongs in the diagram. The example treats all links as counts in one cohort and one period.",
        "mistakes": ["Hiding exits to make the main path look complete.", "Counting multiple events from one entity as separate stage transfers.", "Balancing one period's arrivals against another period's departures.", "Assuming node position or link crossing has business meaning."],
        "drill": "Model 81 claims through intake, review and closure. Add a pending branch and an unobserved exit; fail the reconciliation when either is removed, then render a transition table beside the flow.",
        "related": [prefix + "aggregation-grain-and-denominator", prefix + "network-graph-identity-degree-and-layout-stability", prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "accessible-color-and-text-alternatives"],
    },
    {
        "slug": "treemap-hierarchy-leaf-sums-and-area-comparison",
        "title": "Treemaps: validate hierarchy and leaf totals before assigning area",
        "summary": "Prevent duplicated parent values, unstable tiles and tiny unreadable leaves.",
        "sections": [
            ("Area is a sum contract", "A treemap divides a rectangle into nested areas proportional to a nonnegative measure. To compare storage used by product teams, assign each leaf one value and derive parent totals from those leaves. If a parent row already contains the total, summing it with its children doubles the area. Validate that every leaf has one parent, that the hierarchy has no cycle, and that the root total agrees with the source. [[data-visualization/aggregation-grain-and-denominator|Grain checks]] protect the basic unit before layout begins."),
            ("Labels cannot rescue tiny tiles", "A rectangle's area is hard to estimate precisely, and small leaves cannot hold readable text. Use the treemap for broad composition and a sorted table or bar view for exact comparison. Group genuinely small categories into a named remainder only when their combined value and membership are reported. Do not simply omit leaves to make labels fit. [[data-visualization/stacked-bars-composition-and-changing-denominators|Stacked bars]] often work better when the hierarchy has only one level or exact cross-category comparison matters."),
            ("Keep identity across versions", "Many tiling algorithms can rearrange rectangles after a small value change. A user comparing two snapshots may see tiles move and mistake movement for a new category. Use stable IDs, a declared sort and a layout method chosen for the comparison task. If two versions must be compared, consider a fixed hierarchy with an accompanying difference bar; do not imply that a tile's new screen position has meaning. [[data-visualization/small-multiples-shared-scales-and-facet-order|Shared-scale panels]] help only when the same root total basis is explicit."),
            ("Separate structure from measure", "Zero-value leaves may be valid members of the hierarchy but have no visible area. Missing measures are different: they should be counted and surfaced outside the tiled display. A negative measure cannot be represented as area without a different visual contract. Tooltips should show path, leaf value, parent total and share; keyboard users need an ordered text tree or table. [[data-visualization/accessible-color-and-text-alternatives|Accessible text]] can retain the small leaves that the drawing cannot label."),
        ],
        "code": '''def hierarchy_totals(
    parent_of: dict[str, str | None], leaf_values: dict[str, int]
) -> dict[str, int]:
    internal = {parent for parent in parent_of.values() if parent is not None}
    if set(leaf_values) != set(parent_of) - internal or any(value < 0 for value in leaf_values.values()):
        raise ValueError("invalid leaf value")
    if any(parent is not None and parent not in parent_of for parent in parent_of.values()):
        raise ValueError("unknown parent")
    for start in parent_of:
        seen = set()
        node = start
        while node is not None:
            if node in seen:
                raise ValueError("cycle in hierarchy")
            seen.add(node)
            node = parent_of[node]
    totals = {node: 0 for node in parent_of}
    for leaf, value in leaf_values.items():
        node = leaf
        while node is not None:
            totals[node] += value
            node = parent_of[node]
    return totals

tree = {"all": None, "support": "all", "mobile": "support",
        "web": "support", "payments": "all"}
totals = hierarchy_totals(tree, {"mobile": 47, "web": 81, "payments": 31})
assert totals["support"] == 128 and totals["all"] == 159''',
        "cost": "For V nodes, L leaves and maximum depth H, cycle validation and ancestor accumulation take O((V + L)H) time and O(V + H) space for totals and one ancestor set. A deep or very large hierarchy should validate and sum in one postorder pass, O(V). Production layout adds sorting, tiling and label placement. Every terminal node needs a nonnegative measure for area encoding.",
        "mistakes": ["Adding stored parent totals to leaf values and doubling displayed area.", "Treating zero-area leaves as nonexistent members.", "Reading a tile move between snapshots as a change in business structure.", "Dropping tiny categories without reporting the remainder."],
        "drill": "Build a three-level storage hierarchy with 47 leaves. Insert one duplicate parent total, one missing measure and one cycle; reject each before rendering, then compare the resulting treemap with a sorted leaf table.",
        "related": [prefix + "stacked-bars-composition-and-changing-denominators", prefix + "aggregation-grain-and-denominator", prefix + "accessible-color-and-text-alternatives", prefix + "small-multiples-shared-scales-and-facet-order"],
    },
    {
        "slug": "network-graph-identity-degree-and-layout-stability",
        "title": "Network graphs: define nodes and edges before trusting the layout",
        "summary": "Check identity, direction, duplicates and degree before placing nodes on a canvas.",
        "sections": [
            ("The edge is the claim", "A node-link graph represents entities and relationships. Before running a force layout, specify whether an edge means a message, a transaction, a dependency or a co-occurrence, and whether direction matters. Two messages from depot A to depot B may be two events or one weighted relationship. Resolve that choice at the declared grain. Stable node IDs prevent two accounts with the same display name from merging. [[data-visualization/aggregation-grain-and-denominator|The unit of analysis]] extends to graph edges."),
            ("Layout distance is not a metric", "Force layouts position nodes by an algorithm balancing constraints. Nearby nodes may be strongly connected, but the distance is not automatically a business quantity; changing a random seed, viewport or graph subset can move them. Pin important positions or show a fixed comparison layout when inspecting versions. Report quantitative graph measures separately with their definitions. [[data-visualization/small-multiples-shared-scales-and-facet-order|Comparison panels]] should preserve a stable node identity and comparable viewport."),
            ("Count what selection removes", "A filtered network can make a high-degree node appear isolated if many of its neighbors are hidden. Show selected and total degree separately or state that the graph describes only the visible subgraph. Validate dangling edges whose endpoints are absent; do not let the renderer silently discard them. For large graphs, aggregate by a declared community or show a ranked adjacency table, because a dense hairball hides paths and edge direction. [[data-visualization/large-series-level-of-detail-and-extrema|Resolution limits]] apply to edges and nodes as much as to points in a chart."),
            ("Design for inspection", "Hover-only relationships are inaccessible on touch and keyboard. Provide a searchable node list, ordered neighbor table, edge direction labels and a way to inspect an entity without relying on color. Keep private identifiers out of public graph exports. A link of width 8 should name the weight unit and time interval; do not use width for one measure and tooltip for another. [[data-visualization/accessible-color-and-text-alternatives|Text alternatives]] carry exact relationships that an overview cannot show."),
        ],
        "code": '''from collections import defaultdict

def directed_degrees(
    node_ids: set[str], links: list[tuple[str, str, int]]
) -> dict[str, tuple[int, int]]:
    if not node_ids:
        raise ValueError("empty node set")
    incoming = defaultdict(int)
    outgoing = defaultdict(int)
    for source, target, weight in links:
        if source not in node_ids or target not in node_ids or weight <= 0:
            raise ValueError("dangling edge or nonpositive weight")
        outgoing[source] += weight
        incoming[target] += weight
    return {node: (incoming[node], outgoing[node]) for node in node_ids}

degrees = directed_degrees(
    {"depot-47", "depot-81", "depot-94"},
    [("depot-47", "depot-81", 31),
     ("depot-81", "depot-94", 8)])
assert degrees["depot-81"] == (31, 8)
assert sum(value[0] for value in degrees.values()) == 39''',
        "cost": "For V nodes and E links, endpoint validation and weighted-degree counting take O(V + E) expected time and O(V) space. Layout may take many iterative passes and dominate CPU; this accounting step should run first so bad graph data does not get disguised by an attractive arrangement. The function sums weights and permits repeated directed pairs by design. If the chart promises one edge per pair, aggregate and count duplicates explicitly before layout.",
        "mistakes": ["Treating screen distance from a force layout as an exact relationship strength.", "Discarding edges with missing endpoints without an audit count.", "Mixing event count with unique-neighbor degree.", "Comparing two filtered layouts without identifying removed nodes and edges."],
        "drill": "Map handoffs among 31 service teams. Add a duplicate label, a dangling edge and a filtered-out hub; preserve stable IDs and report both visible and full-graph weighted degrees.",
        "related": [prefix + "sankey-flow-conservation-and-unobserved-exits", prefix + "aggregation-grain-and-denominator", prefix + "large-series-level-of-detail-and-extrema", prefix + "accessible-color-and-text-alternatives"],
    },
    {
        "slug": "chart-annotations-event-windows-and-causal-claims",
        "title": "Chart annotations: align events to the right clock without claiming causality",
        "summary": "Treat deployment lines, policy changes and outages as versioned data with time windows and uncertainty.",
        "sections": [
            ("An annotation is another dataset", "A vertical line on a chart often marks a deployment, policy change or outage. That event has its own timestamp, time zone, scope, source and uncertainty. A release may roll through regions over several hours; drawing one instant across all regions invents precision. Model it as a window or per-region events, then map it to the same clock as the measured series. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|The time-series clock]] must be settled before annotations are placed."),
            ("Scope must match the measured population", "If only one depot received a new workflow, an all-depot annotation can imply that every plotted change followed the intervention. Filter event records by affected site, product and population, and expose the scope in the label. Preserve events outside the visible interval in the export but do not draw them in the viewport. Distinguish a data outage from a true operational incident: both can create a cliff, but only one is a measured outcome. [[data-visualization/aggregation-grain-and-denominator|Population contracts]] determine whether a note belongs on a chart."),
            ("Timing does not prove effect", "A change in the curve after a marked event may be coincidence, seasonality, a denominator shift or a delayed measurement. Write labels such as 'workflow enabled' rather than 'workflow improved response time' unless a separate analysis supports the latter. If an effect is being estimated, show the design, comparison group and uncertainty elsewhere. [[applied-statistics/hypothesis-test-and-effect-size|Effect-size analysis]] is distinct from descriptive annotation. Keep the event visible even when the post-event result disappoints expectations."),
            ("Avoid collision and preserve provenance", "Several events on one day can produce overlapping labels. Group them in a visible list keyed to markers, prioritizing material scope and preserving access to every event. The annotation export should include event ID, earliest and latest time, scope, label and source version. A revised event time should update the chart and its manifest together. [[data-visualization/chart-export-manifest-data-and-render-version|Reproducible exports]] need both series and annotation versions. Test daylight-saving boundaries and a deployment window that straddles the chart's range."),
        ],
        "code": '''from datetime import datetime, timezone

def visible_events(
    events: list[tuple[str, datetime, datetime, set[str]]],
    view_start: datetime, view_end: datetime, depot_id: str
) -> list[str]:
    if view_start.tzinfo is None or view_end.tzinfo is None or view_start >= view_end:
        raise ValueError("invalid aware view interval")
    selected = []
    for event_id, began, ended, depots in events:
        if not event_id or began.tzinfo is None or ended.tzinfo is None or began >= ended:
            raise ValueError("invalid event interval")
        if depot_id in depots and began < view_end and ended > view_start:
            selected.append(event_id)
    return selected

utc = timezone.utc
window = [("release-47", datetime(2026, 8, 11, 9, tzinfo=utc),
           datetime(2026, 8, 11, 11, tzinfo=utc), {"north"})]
assert visible_events(window, datetime(2026, 8, 11, 10, tzinfo=utc),
                      datetime(2026, 8, 12, tzinfo=utc), "north") == ["release-47"]
assert visible_events(window, datetime(2026, 8, 11, 10, tzinfo=utc),
                      datetime(2026, 8, 12, tzinfo=utc), "south") == []''',
        "cost": "Scanning E events is O(E) time and O(M) output space for M matching IDs. An indexed event store can narrow by time and scope for many dashboards. The example uses half-open display intervals and event windows, so a window ending exactly at the view start is excluded. It does not infer causality or validate whether a deployment reached every unit in its declared scope; those are separate evidence checks.",
        "mistakes": ["Drawing a gradual rollout as one global instant.", "Annotating all depots with an event that affected only one.", "Writing a causal outcome claim in an event label without a study.", "Failing to version corrected event times alongside the plotted series."],
        "drill": "Annotate a 29-day response-time chart with three region-specific rollouts, one data outage and one event that crosses the visible interval boundary. Verify the right events appear for each region and export their time windows.",
        "related": [prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "chart-export-manifest-data-and-render-version", prefix + "dashboard-filter-and-provenance", prefix + "uncertainty-and-small-sample-display"],
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
        "featured": False, "sort_order": 8716 + offset, "status": "published",
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
    for start, heading in ((0, "Composition, scales and paired comparisons"),
                           (4, "Flow, hierarchy, networks and events")):
        targets = new_paths[start:start + 4]
        row["data"]["modules"].append({"title": heading, "lessons": targets})
        row["body"] += f'<h2>{heading}</h2><ul>' + ''.join(
            f'<li>{link(target)}</li>' for target in targets) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "aggregation-grain-and-denominator": [new_paths[0], new_paths[4], new_paths[5]],
    prefix + "scale-baseline-and-axis-integrity": [new_paths[1], new_paths[2]],
    prefix + "distribution-and-outlier-displays": [new_paths[3]],
    prefix + "time-series-gaps-calendars-and-provisional-periods": [new_paths[7]],
    prefix + "accessible-color-and-text-alternatives": [new_paths[5], new_paths[6]],
    prefix + "chart-question-and-visual-encoding": [new_paths[0], new_paths[2], new_paths[3]],
    prefix + "dashboard-filter-and-provenance": [new_paths[7]],
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
