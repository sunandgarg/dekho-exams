"""Publish original lessons on sunbursts, sparklines, and geographic flows."""
from data_visualization_batch import publish

prefix = "data-visualization/"
lessons = [
    {
        "slug": "sunburst-charts-leaf-ledgers-parent-totals-and-depth",
        "title": "Sunburst charts: reconcile the leaf ledger before drawing rings",
        "summary": "Build a radial hierarchy from one counted leaf ledger, keep parent totals consistent, and make narrow outer sectors inspectable.",
        "sections": [
            ("One record belongs to one leaf", "A sunburst partitions a whole into nested categories. The center represents the root, the next ring divides it into top-level groups, and each outward ring divides its parent again. Start from records or an explicitly aggregated leaf ledger, with one complete path per counted item. The same support ticket cannot appear once under Email and again under Chat unless the measure is deliberately ticket-channel events rather than distinct tickets. State that grain next to the chart. A root total of 47 tickets means every first-ring wedge must add to 47, and each branch must equal the sum of its immediate children when the branches represent totals. A separate parent count entered from another report is a common double-counting route. The preparation code below derives parent totals from leaves. [[data-visualization/treemap-hierarchy-leaf-sums-and-area-comparison|Treemaps]] share the accounting requirement; [[data-visualization/aggregation-grain-and-denominator|grain and denominator]] checks establish what the area means."),
            ("Treat absent categories as data, not empty geometry", "An incomplete classification is still a counted record. Give it an explicit category such as Unassigned at the first stage where classification is absent, or stop its path at a documented terminal node. Do not distribute its count across known children to make the ring appear complete. If one branch stops at depth two while another reaches depth four, the outer rings describe different levels of detail; the caption must say so. This lesson uses three-level paths so every ticket has the same depth and comparison is direct. Repeated label text in different branches does not imply the same node: the full path is the identifier. For example, Resolved under Email and Resolved under Portal are two separate sectors. Preserve full-path IDs in hover text, exports, and keyboard focus targets. [[data-visualization/missingness-matrices-record-order-patterns-and-co-missing-fields|Missingness]] and [[data-visualization/chart-export-manifest-data-and-render-version|export manifests]] cover the adjoining data contract."),
            ("Read angular share against the right parent", "A sector's angle communicates its share of the root at its depth, while a child-to-parent percentage answers a different question. Show both numerator and denominator in a tooltip or adjacent table. In the worked ledger, the Support branch contains 33 of 47 tickets, so it spans roughly 253 degrees of the first ring. Within Support, Email accounts for 19 of 33, not 19 of 47. A viewer cannot recover those denominators reliably from a small arc alone. Freeze branch order for repeated reports; re-sorting by the latest count makes equal categories move around the circle between periods. Use a stable color mapping for the first ring, then related shades or labels for descendants. If every small leaf receives a different saturated color, color stops carrying a useful meaning. [[data-visualization/stacked-bars-composition-and-changing-denominators|Stacked bars]] are often clearer when only two levels matter."),
            ("Provide a route out of crowded outer rings", "The outer ring can contain dozens of thin sectors even when its parent occupies a generous angle. Do not turn a two-pixel arc into the only way to discover a category. Expose a searchable hierarchy table with full path, count, share of parent and share of root. Keyboard users should be able to enter a branch, inspect children and return to the same focus position. If categories are grouped into Other, define the threshold in counts or root share, retain the original leaves in the downloadable ledger, and never combine categories across different parents merely because their labels match. A sunburst is strongest for following hierarchy and relative composition, not for precise comparison between distant narrow sectors. For precise ranking, pair it with a bar view. [[data-visualization/interactive-chart-keyboard-focus-and-data-table-contract|Chart accessibility]] and [[data-visualization/waffle-charts-fixed-cell-budget-largest-remainders-and-small-groups|waffle charts]] offer alternatives for small shares."),
        ],
        "code": '''from collections import Counter

def prepare_ticket_sunburst(leaf_ledger):
    totals = Counter()
    if not leaf_ledger:
        raise ValueError("leaf ledger cannot be empty")
    for path, ticket_count in leaf_ledger:
        if (not isinstance(path, tuple) or len(path) != 3 or
                any(not isinstance(label, str) or not label.strip() for label in path) or
                isinstance(ticket_count, bool) or not isinstance(ticket_count, int) or
                ticket_count <= 0):
            raise ValueError("each leaf needs three labels and a positive count")
        for depth in range(4):
            totals[path[:depth]] += ticket_count
    for path, parent_count in totals.items():
        if len(path) == 3:
            continue
        child_sum = sum(count for child, count in totals.items()
                        if len(child) == len(path) + 1 and child[:-1] == path)
        assert parent_count == child_sum
    return totals

ticket_leaves = [
    (("Support", "Email", "Resolved"), 14),
    (("Support", "Email", "Escalated"), 5),
    (("Support", "Chat", "Resolved"), 11),
    (("Support", "Chat", "Escalated"), 3),
    (("Billing", "Portal", "Resolved"), 8),
    (("Billing", "Portal", "Escalated"), 4),
    (("Billing", "Phone", "Unassigned"), 2),
]
totals = prepare_ticket_sunburst(ticket_leaves)
assert totals[()] == 47
assert totals[("Support",)] == 33
assert totals[("Support", "Email")] == 19
assert round(totals[("Support",)] / totals[()] * 360) == 253''',
        "cost": "Let R be the number of leaf-ledger rows, D the path depth and N the number of distinct hierarchy nodes. Accumulating prefixes takes O(RD) time and O(N) space. The audit loop shown compares each parent with all nodes, so its simple form costs O(N²) time; for a large hierarchy, keep a child-sum counter during the same prefix pass and reduce reconciliation to O(RD + N). The code prepares totals, not drawing coordinates. A renderer assigns a parent interval first, then partitions that interval among children using the derived totals and a fixed category order. It must not sum the root and branch totals again as if each were independent data.",
        "mistakes": ["Counting the same record under multiple leaves without changing the measure definition.", "Supplying independent parent values that exceed or disagree with their children.", "Merging identical leaf labels from different parents instead of using full-path IDs.", "Interpreting a sector's root share as its share of its immediate parent.", "Leaving narrow outer-ring categories inaccessible without a searchable table."],
        "drill": "Build a three-stage classification for 47 customer tickets. Introduce an Unassigned path for records lacking a final outcome, reconcile every parent with its children, and report both parent share and root share for the smallest leaf before drawing any arcs.",
        "related": [prefix + "treemap-hierarchy-leaf-sums-and-area-comparison", prefix + "aggregation-grain-and-denominator", prefix + "interactive-chart-keyboard-focus-and-data-table-contract", prefix + "stacked-bars-composition-and-changing-denominators"],
    },
    {
        "slug": "sparklines-shared-domain-missing-days-and-small-space",
        "title": "Sparklines: keep small trends comparable and honest",
        "summary": "Prepare compact daily series with a shared value domain, explicit gaps and a text summary before shrinking a chart into a cell.",
        "sections": [
            ("A compact line still needs a measurement contract", "A sparkline removes most visible chart furniture to fit a sequence beside a number or name. The missing axes do not remove the need for units, period, aggregation rule and value domain. If two rows represent daily shipped orders, make the date window identical and disclose whether today's count is final. If one row covers twelve complete days and another covers eleven complete days plus a live partial day, their endpoints are not comparable. Tiny plots are most useful for seeing shape at a glance; the adjacent text should carry the exact latest value, change and time range. Define whether the line connects daily totals, daily averages or cumulative totals. A cumulative series almost always rises and can hide daily reversals. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Time-series gaps]] and [[data-visualization/seasonal-subseries-plots-cycle-position-trend-and-incomplete-years|seasonal subseries]] help with period design."),
            ("Share the scale when rows are compared", "An automatically fitted vertical domain makes every row fill its tiny box, but it can make a calm series look as volatile as one with a one-day spike. If the purpose is comparison across regions, use one locked vertical domain for all regional sparklines with the same unit and period. In the worked data, the shared range runs from nine to 48 shipped orders; East's spike remains visibly larger than West's gradual rise. If the purpose is within-row movement only, row-specific domains can be defensible, but label that choice and do not invite cross-row height comparisons. A zero baseline may be helpful for counts; for rate or temperature series, a domain around the relevant operating range can be better if disclosed. Avoid mixing percentages and counts in one unlabeled column. [[data-visualization/scale-baseline-and-axis-integrity|Axis integrity]] still applies when the axis is visually absent."),
            ("Leave missing days open", "An unknown day is neither zero nor a straight bridge between neighbors. The code below returns contiguous observed runs so a renderer draws separate paths and marks the missing slot. It also rejects duplicate or skipped dates, because the positions in a daily sparkline must be equally spaced in calendar time. A sudden line to zero on a day with no data claims an event that was never measured. Connecting across the gap claims continuity that was not observed. If a short gap is deliberately interpolated for display, preserve a gap marker and distinguish the estimated segment with a separate style and text. Highlight an important peak with its value and date, but do not cover the rest of the line with dots. [[data-visualization/calendar-heatmap-complete-days-time-zones-and-missingness|Calendar heatmaps]] provide a larger view of complete and missing days."),
            ("Shrink marks, not interpretation", "A 70-pixel chart cannot display hundreds of distinct time positions legibly. For a long series, compute a pixel-column minimum and maximum so a brief spike survives reduction; a single average per column can erase it. Keep first and last observed points, known gaps and annotated events. On mobile, show fewer comparable rows at once rather than forcing labels to microscopic sizes. A text alternative should state the time window, last value, high, low and missing count. If a screen reader must traverse every point, provide an adjacent table or expandable full chart; reading a stream of unlabeled coordinates is not useful. Export the original observations and the reduction method. [[data-visualization/large-series-level-of-detail-and-extrema|Level of detail]], [[data-visualization/accessible-color-and-text-alternatives|accessible alternatives]] and [[data-visualization/chart-export-manifest-data-and-render-version|export manifests]] complete the contract."),
        ],
        "code": '''from datetime import date, timedelta
from math import isfinite

def prepare_daily_sparklines(regional_series):
    if not regional_series:
        raise ValueError("at least one region is required")
    expected_days = None
    all_values = []
    prepared = {}
    for region, observations in regional_series.items():
        if not region or not observations:
            raise ValueError("region and daily observations are required")
        days = [day for day, _ in observations]
        if (any(not isinstance(day, date) for day in days) or
                any(right - left != timedelta(days=1)
                    for left, right in zip(days, days[1:]))):
            raise ValueError("days must be unique, ordered and consecutive")
        if expected_days is None:
            expected_days = days
        elif days != expected_days:
            raise ValueError("regions must use the same calendar window")
        runs, current = [], []
        for day, value in observations:
            if value is None:
                if current:
                    runs.append(current)
                    current = []
                continue
            if (isinstance(value, bool) or not isinstance(value, (int, float)) or
                    not isfinite(value) or value < 0):
                raise ValueError("daily counts must be finite and nonnegative")
            current.append((day, value))
            all_values.append(value)
        if current:
            runs.append(current)
        prepared[region] = {"runs": runs, "missing": len(days) - sum(map(len, runs))}
    if not all_values:
        raise ValueError("there are no measured values")
    return (min(all_values), max(all_values)), prepared

first_day = date(2026, 4, 6)
east = [12, 14, 13, None, 17, 19, 48, 20, 18, 21, 20, 23]
west = [9, 10, 11, 12, 13, 13, 14, 15, 16, 16, 17, 18]
daily = {"East": list(zip((first_day + timedelta(days=offset)
                            for offset in range(12)), east)),
         "West": list(zip((first_day + timedelta(days=offset)
                            for offset in range(12)), west))}
domain, series = prepare_daily_sparklines(daily)
assert domain == (9, 48)
assert series["East"]["missing"] == 1
assert [len(run) for run in series["East"]["runs"]] == [3, 8]''',
        "cost": "For S series of T daily slots, validation and run construction take O(ST) time; keeping the plotted observations and gaps takes O(ST) space. The shared domain requires one pass over measured values, not a separate scale fit for every row. On a 70-pixel surface, a renderer should reduce a much longer series by pixel column using extrema and explicit gap flags, then retain the source data for interaction. Do not use a per-column mean when the reader must detect rare spikes; it can remove the very event the compact chart is meant to reveal.",
        "mistakes": ["Letting each row auto-scale while encouraging comparison between rows.", "Treating a missing daily value as zero or silently connecting across it.", "Placing rows with different date windows on the same implied horizontal scale.", "Compressing long data by averages that erase brief maxima or minima.", "Removing every unit, date and text summary because the chart is small."],
        "drill": "Create a grid of 47 daily-order sparklines for equally long periods. Lock a shared range for comparable regions, mark provisional days, count missing slots, and check whether the highest single-day value remains visible after reducing each chart to its final pixel width.",
        "related": [prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "large-series-level-of-detail-and-extrema", prefix + "accessible-color-and-text-alternatives", prefix + "scale-baseline-and-axis-integrity"],
    },
    {
        "slug": "flow-maps-directed-routes-dateline-and-width-scales",
        "title": "Flow maps: separate direction, magnitude and geographic route",
        "summary": "Validate a directed movement ledger before drawing arrows, preserve reciprocal flows, and avoid false straight-line paths near the dateline.",
        "sections": [
            ("A map does not repair a broken movement ledger", "A geographic flow map places directed movements between locations. The link may represent shipments, journeys or messages, but it needs a declared unit and time window. Define whether 47 means shipments, parcels, people or distinct vehicles; these are different grains and cannot share a width scale. One record needs a stable origin, destination, direction and nonnegative magnitude. Reciprocal routes are not one undirected line: 47 units eastward and 23 westward have different operational meaning even if they use the same endpoints. Aggregate only records with the same directed pair and compatible time and unit definitions. Compare the sum of mapped links with the source ledger before rendering. Any excluded route, unknown endpoint or local movement needs an explicit count. [[data-visualization/sankey-flow-conservation-and-unobserved-exits|Sankey reconciliation]] and [[data-visualization/chord-diagrams-directed-flows-self-loops-and-sector-totals|directed chord flows]] expose the same accounting risks without geography."),
            ("Treat coordinates as locations, not routes", "The endpoints are geographic facts; the line between them is often just a schematic connection. An aircraft, truck or fiber packet may not follow the shortest path. If the chart uses straight projected segments, label them as connections rather than surveyed routes. A great-circle arc gives a spherical shortest connection, yet a map projection bends that arc and may split it at the antimeridian. Drawing a straight line between longitude 179 and longitude minus 178 on a world map can send a three-degree connection almost all the way around the display. The code validates longitude and latitude, computes a wrapped longitude difference and estimates great-circle distance as a diagnostic. It does not claim the movement actually followed that path. Use a projection-aware renderer to interpolate, clip and draw the arc. [[data-visualization/map-antimeridian-wrapping-bounds-and-projection-distortion|Dateline handling]] is required before global deployment."),
            ("Encode magnitude without losing the small flows", "Arrow width should follow a published scale and unit. Linear width makes a route of 40 units twice as thick as one of 20, but the total ink area also depends on route length; never ask users to infer volume from ink area. If a square-root width scale prevents large links from dominating, say so and show the numeric values beside the map. Two-way traffic needs offset curves, paired arrows or an interactive direction filter so the reciprocal links do not hide each other. Dense hubs can become opaque even when the ledger is correct. Filter by origin, destination or period, then retain the full route table and its total. Grouping minor routes into an unnamed Other line with no endpoint creates a false geographic path. [[data-visualization/proportional-symbol-maps-area-scale-and-overlap|Proportional symbols]] and [[data-visualization/linked-filters-cohort-denominators-and-selection-state|linked filters]] help when destinations crowd together."),
            ("Expose the ledger next to the map", "A useful flow map includes a table with origin, destination, direction, magnitude, unit, period and any route method. A keyboard user should reach that table without trying to select a hairline arrow. A reader should be able to sort by largest flow and see the same filters that shaped the map. If positions are deliberately jittered to separate overlapping links, keep the true coordinates in the export and say that the display geometry was adjusted. Do not publish precise coordinates for sensitive facilities when aggregated regions answer the question; the mapped grain itself is a disclosure choice. For before-and-after comparisons, freeze the projection, viewport and width scale so movement in the graphic reflects changed data rather than changed camera settings. [[data-visualization/interactive-chart-keyboard-focus-and-data-table-contract|Accessible chart controls]] and [[data-visualization/chart-export-manifest-data-and-render-version|export manifests]] cover the delivery layer."),
        ],
        "code": '''from collections import Counter
from math import asin, cos, isfinite, radians, sin, sqrt

def prepare_transfer_flows(sites, transfers):
    if not sites or not transfers:
        raise ValueError("sites and transfers are required")
    for site, point in sites.items():
        if (not site or not isinstance(point, tuple) or len(point) != 2 or
                any(isinstance(value, bool) or not isinstance(value, (int, float))
                    or not isfinite(value) for value in point) or
                not -180 <= point[0] <= 180 or not -90 <= point[1] <= 90):
            raise ValueError(f"invalid coordinate: {site}")
    directed = Counter()
    for origin, destination, units in transfers:
        if (origin not in sites or destination not in sites or origin == destination or
                isinstance(units, bool) or not isinstance(units, int) or units <= 0):
            raise ValueError("invalid directed transfer")
        directed[(origin, destination)] += units
    routes = []
    for (origin, destination), units in sorted(directed.items()):
        west_lon, west_lat = sites[origin]
        east_lon, east_lat = sites[destination]
        delta_lon = ((east_lon - west_lon + 180) % 360) - 180
        delta_lat = east_lat - west_lat
        arc = sin(radians(delta_lat) / 2) ** 2 + (
            cos(radians(west_lat)) * cos(radians(east_lat)) *
            sin(radians(delta_lon) / 2) ** 2)
        distance_km = 2 * 6371.0088 * asin(min(1.0, sqrt(arc)))
        routes.append((origin, destination, units, round(distance_km, 1)))
    assert sum(route[2] for route in routes) == sum(row[2] for row in transfers)
    return routes

sites = {"West sensor": (179, -17), "East sensor": (-178, -16),
         "Inland hub": (-176, -15)}
transfers = [("West sensor", "East sensor", 31),
             ("West sensor", "East sensor", 16),
             ("East sensor", "West sensor", 23),
             ("West sensor", "Inland hub", 11)]
routes = prepare_transfer_flows(sites, transfers)
assert sum(route[2] for route in routes) == 81
assert any(route[:3] == ("West sensor", "East sensor", 47) for route in routes)
assert any(route[:3] == ("East sensor", "West sensor", 23) for route in routes)''',
        "cost": "With E transfer rows and V site records, coordinate checks and directed aggregation take O(V + E) expected time and O(V + R) space, where R is the number of unique directed pairs. Sorting the aggregated pairs for stable export adds O(R log R) time. The distance calculation is constant work per pair and is only a spherical diagnostic, not an observed itinerary. The worked ledger totals 81 units across three directed routes, including 47 eastward and 23 westward between the same two sites. A projection-aware drawing library still has to sample and clip each route according to the chosen map projection.",
        "mistakes": ["Combining reciprocal movements into one undirected route.", "Drawing a long straight line across the map when a short connection crosses the dateline.", "Calling a schematic or great-circle connector the observed travel path.", "Changing arrow-width scale between panels while comparing periods.", "Dropping unknown endpoints or self-movements without reconciling the excluded total."],
        "drill": "Take 47 directed dispatch records, including reverse movements and a route near the antimeridian. Reconcile the displayed sum with the ledger, label the connection method, and provide a sortable route table before adding arrow geometry.",
        "related": [prefix + "map-antimeridian-wrapping-bounds-and-projection-distortion", prefix + "sankey-flow-conservation-and-unobserved-exits", prefix + "chord-diagrams-directed-flows-self-loops-and-sector-totals", prefix + "interactive-chart-keyboard-focus-and-data-table-contract"],
    },
]

publish(
    lessons,
    sort_start=8800,
    module_groups=[("Nested radial hierarchies", [0]),
                   ("Compact time-series displays", [1]),
                   ("Geographic movement displays", [2])],
    incoming={
        "treemap-hierarchy-leaf-sums-and-area-comparison": [0],
        "aggregation-grain-and-denominator": [0],
        "stacked-bars-composition-and-changing-denominators": [0],
        "waffle-charts-fixed-cell-budget-largest-remainders-and-small-groups": [0],
        "time-series-gaps-calendars-and-provisional-periods": [1],
        "large-series-level-of-detail-and-extrema": [1],
        "calendar-heatmap-complete-days-time-zones-and-missingness": [1],
        "accessible-color-and-text-alternatives": [1],
        "map-antimeridian-wrapping-bounds-and-projection-distortion": [2],
        "sankey-flow-conservation-and-unobserved-exits": [2],
        "chord-diagrams-directed-flows-self-loops-and-sector-totals": [2],
        "proportional-symbol-maps-area-scale-and-overlap": [2],
    },
    packet_name="aitrove-data-visualization-import-20261010-d.json",
)
