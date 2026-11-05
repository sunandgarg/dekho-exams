"""Publish original lessons on bubble charts, Marimekko charts, and circle packing."""
from data_visualization_batch import publish

prefix = "data-visualization/"
lessons = [
    {
        "slug": "bubble-charts-area-scaling-overlap-and-third-measure",
        "title": "Bubble charts: scale the third measure by area",
        "summary": "Use two positions and one area measure without letting radius scaling, overlap or missing records distort the comparison.",
        "sections": [
            ("Three measures require three separate contracts", "A bubble chart is a scatterplot whose marker area carries another nonnegative quantity. Position answers two questions; size answers a third. In an operations review, horizontal position could be median minutes to close a ticket, vertical position the fraction that breached a service target, and circle area the number of open tickets. Those measures come from different aggregations, so write the population and period beside each one. A depot with no measured closure time does not belong at zero minutes. Keep it in an excluded-record table instead of placing it at the origin. Likewise, a zero open-ticket count can be represented as a zero-area mark in the source table, but it cannot be selected on a chart. Show the count in an adjacent row or give zero-count depots a clearly labeled outline symbol with a fixed visual size that is not part of the area scale. [[data-visualization/chart-question-and-visual-encoding|Encoding choice]] and [[data-visualization/aggregation-grain-and-denominator|grain]] should be settled before selecting colors."),
            ("Area, not diameter, carries volume", "A circle's area grows with the square of its diameter. Setting diameter directly proportional to a count makes 81 tickets look nine times wider and 81 times larger than nine tickets, despite a true ninefold count difference. To make area proportional to count, set diameter to a fixed maximum diameter times the square root of count divided by the maximum count. In the worked ledger, depots with nine, 36 and 81 open tickets receive diameters of 12, 24 and 36 pixels when the largest bubble is 36 pixels wide. Their areas then have the same 1:4:9 ratio as their counts. A plotting library may accept area in points squared instead of diameter in pixels; inspect that API rather than applying the square root twice. Display at least two labeled reference circles and the actual numeric value on focus or in a table. [[data-visualization/proportional-symbol-maps-area-scale-and-overlap|Proportional map symbols]] face the same area problem."),
            ("Overlap can erase the observation that matters", "Large bubbles drawn last can hide smaller ones at nearly identical coordinates. Sort by descending size before drawing so smaller circles remain on top, add a visible stroke, and use moderate transparency only if overlapping colors have a meaningful legend. Transparency alone does not reveal every record when several points coincide. Offer a list of the observations at the selected coordinate, and preserve stable depot IDs in that list. Do not jitter either quantitative axis unless the adjustment is disclosed and the original values are still available. For dense data, switch to a hexbin or density view for the first scan, then open the original bubbles through a filter. A third encoded variable adds visual load; a fourth color measure should be used only when it answers an explicit question. [[data-visualization/scatterplot-overplotting-density-and-sampling-bias|Overplotting]] and [[data-visualization/hexbin-density-grid-resolution-and-exposure|hexbins]] explain the fallback."),
            ("Freeze the comparison frame", "When two periods are placed side by side, keep the horizontal range, vertical range and maximum-bubble reference the same. Rescaling each panel independently can make a decline in ticket volume look like no change at all. The chart must state whether the size measure is a count, rate or monetary total; negative quantities cannot use an ordinary area scale without a separate sign channel. If a filter removes the largest depot, retain the original size reference when the user is comparing filtered and unfiltered views. Supply an accessible table with depot, both positional measures, ticket count and exclusion reason. If the story is primarily about count rank, bars will usually be faster to read than circles. [[data-visualization/small-multiples-shared-scales-and-facet-order|Shared-scale panels]], [[data-visualization/interactive-chart-keyboard-focus-and-data-table-contract|keyboard access]] and [[data-visualization/chart-export-manifest-data-and-render-version|export contracts]] cover the handoff."),
        ],
        "code": '''from math import isfinite, sqrt

def prepare_depot_bubbles(depot_rows, maximum_diameter=36):
    if (not depot_rows or isinstance(maximum_diameter, bool) or
            not isinstance(maximum_diameter, (int, float)) or
            not isfinite(maximum_diameter) or maximum_diameter <= 0):
        raise ValueError("rows and a positive maximum diameter are required")
    known = set()
    for depot, close_minutes, breach_fraction, open_tickets in depot_rows:
        if not depot or depot in known:
            raise ValueError("depot IDs must be unique")
        known.add(depot)
        if (any(isinstance(value, bool) or not isinstance(value, (int, float))
                or not isfinite(value) for value in (close_minutes, breach_fraction)) or
                close_minutes < 0 or not 0 <= breach_fraction <= 1 or
                isinstance(open_tickets, bool) or not isinstance(open_tickets, int) or
                open_tickets < 0):
            raise ValueError("invalid depot measures")
    maximum_count = max(row[3] for row in depot_rows)
    if maximum_count == 0:
        raise ValueError("all zero counts need a different chart")
    marks = []
    for depot, close_minutes, breach_fraction, open_tickets in depot_rows:
        diameter = maximum_diameter * sqrt(open_tickets / maximum_count)
        marks.append((depot, close_minutes, breach_fraction,
                      open_tickets, round(diameter, 2)))
    return sorted(marks, key=lambda mark: (-mark[3], mark[0]))

depots = [("Harbor", 31, 0.12, 9),
          ("Ridge", 47, 0.19, 36),
          ("Canal", 54, 0.27, 81)]
marks = prepare_depot_bubbles(depots)
assert [(mark[0], mark[4]) for mark in marks] == [
    ("Canal", 36.0), ("Ridge", 24.0), ("Harbor", 12.0)]
assert 81 / 9 == (36 / 12) ** 2''',
        "cost": "For N depots, validation, maximum-count lookup and diameter calculation take O(N) time. Sorting by count for a deliberate draw order takes O(N log N) time and O(N) output space. This preparation does not solve geometric overlap; a naive pairwise collision test takes O(N²), so large interactive charts should use spatial indexing or aggregate to a density view. The size reference is computed once from the full comparison set, then held fixed across related panels and filters. Rendering libraries differ on whether their size parameter means area, radius or diameter, so test the displayed reference circles against the numeric contract.",
        "mistakes": ["Setting circle diameter directly proportional to count and exaggerating area differences.", "Changing the largest-circle reference separately for each comparison panel.", "Using missing x or y measurements as zero and placing records at the origin.", "Hiding coincident points behind a large opaque marker with no accessible record list.", "Adding color as a fourth measure without a question, legend or readable alternative."],
        "drill": "Prepare a depot review with 47 locations. Choose one period and one grain, hold the area reference fixed across two panels, then verify that a depot with four times another depot's count has twice its diameter rather than four times its diameter.",
        "related": [prefix + "scatterplot-overplotting-density-and-sampling-bias", prefix + "proportional-symbol-maps-area-scale-and-overlap", prefix + "small-multiples-shared-scales-and-facet-order", prefix + "interactive-chart-keyboard-focus-and-data-table-contract"],
    },
    {
        "slug": "marimekko-charts-column-width-conditional-share-and-cell-area",
        "title": "Marimekko charts: make width, height and area reconcile",
        "summary": "Build variable-width stacked columns from a counted ledger and explain the distinct denominators behind column width, segment height and cell area.",
        "sections": [
            ("Start with one counted cross-tab", "A Marimekko chart divides a rectangle into columns of unequal width, then stacks categories within each column. One counted ledger must drive every dimension: the column total determines width, a cell divided by its column total determines height, and the same cell divided by the grand total determines rectangle area. These are three related but different questions. For support channels by outcome, a wide channel is common in the entire population; a tall Escalated segment means a high escalation share within that channel. Neither alone proves which channel contributes the most escalations overall. Count records once, define the period and clarify whether the cell count is tickets, interactions or customers. A customer who opened three tickets contributes three tickets if tickets are the declared grain. [[data-visualization/aggregation-grain-and-denominator|Grain and denominator]] and [[data-visualization/mosaic-plots-joint-area-conditional-rate-and-empty-cells|mosaic plots]] cover the adjoining accounting ideas."),
            ("Derive geometry from counts", "The sample ledger totals 116 tickets across Web, Phone and Partner channels. Web holds 38, Phone 50 and Partner 28, so their horizontal shares are 38/116, 50/116 and 28/116. Within Phone, 25 of 50 tickets are Escalated; that cell is half the Phone column's height but only 25/116 of the whole chart area. The code returns both conditional and joint shares for every cell, then checks that all cell areas sum to one. Keep the channel order fixed between periods. A category missing from one channel gets a zero-height cell in the data table, not a fabricated sliver. Categories with no counts anywhere can leave the comparison, but state the universe used for the display. [[data-visualization/stacked-bars-composition-and-changing-denominators|Stacked bars]] are easier when the column volumes are similar or only within-channel rates matter."),
            ("Area is hard to read precisely", "A narrow column can contain a tall segment that still has little area. If the viewer needs to compare exact escalation rates, label the percentages or pair the chart with a sorted bar chart. If the viewer needs exact contribution to all escalations, show counts or joint shares beside the chart. Do not place a single legend percentage against every segment because each conditional percentage has a different column denominator. Avoid text inside cells too small to hold it: give those records an external label, a keyboard-accessible table and a search path. Color should identify outcomes consistently across columns, and cell borders should remain visible without relying solely on color. [[data-visualization/accessible-color-and-text-alternatives|Text alternatives]] and [[data-visualization/likert-diverging-stacks-neutral-split-and-response-denominators|diverging stacks]] offer related approaches."),
            ("Use the right comparison for change", "Two Marimekko panels can be compared only if their column and category definitions are the same and both panels disclose their population sizes. If the population grows, the second panel still fills the same rectangle; its areas communicate shares, not absolute growth. Show the grand totals in the titles, or pair the panels with a count chart. Keep the same outcome colors and category ordering, and do not reorder columns by a changed rank if the task is to track a channel over time. Very small columns may vanish on a mobile viewport. Collapse the display to a table or offer a focused single-channel view rather than making touch targets thinner than a finger. The export should include the original counts, column totals, conditional shares and joint shares, not just the rendered coordinates. [[data-visualization/chart-export-manifest-data-and-render-version|Export manifests]] and [[data-visualization/small-multiples-shared-scales-and-facet-order|small multiples]] make repeat views auditable."),
        ],
        "code": '''from collections import Counter

def prepare_channel_mekko(ticket_counts, channel_order, outcome_order):
    if not ticket_counts or not channel_order or not outcome_order:
        raise ValueError("counts and category orders are required")
    if (len(set(channel_order)) != len(channel_order) or
            len(set(outcome_order)) != len(outcome_order)):
        raise ValueError("category order contains duplicates")
    known_channels, known_outcomes = set(channel_order), set(outcome_order)
    cells = Counter()
    for channel, outcome, count in ticket_counts:
        if (channel not in known_channels or outcome not in known_outcomes or
                isinstance(count, bool) or not isinstance(count, int) or count < 0):
            raise ValueError("invalid counted cell")
        cells[(channel, outcome)] += count
    totals = {channel: sum(cells[(channel, outcome)] for outcome in outcome_order)
              for channel in channel_order}
    if any(total == 0 for total in totals.values()):
        raise ValueError("each displayed column needs a positive total")
    grand_total = sum(totals.values())
    columns, left = [], 0.0
    for channel in channel_order:
        width = totals[channel] / grand_total
        bottom, segments = 0.0, []
        for outcome in outcome_order:
            count = cells[(channel, outcome)]
            height = count / totals[channel]
            segments.append({"outcome": outcome, "count": count,
                             "height": height, "area": count / grand_total,
                             "bottom": bottom})
            bottom += height
        assert abs(bottom - 1) < 1e-12
        columns.append({"channel": channel, "left": left,
                        "width": width, "total": totals[channel],
                        "segments": segments})
        left += width
    assert abs(left - 1) < 1e-12
    return grand_total, columns

ticket_counts = [
    ("Web", "Closed", 21), ("Web", "Escalated", 8), ("Web", "Open", 9),
    ("Phone", "Closed", 17), ("Phone", "Escalated", 25), ("Phone", "Open", 8),
    ("Partner", "Closed", 12), ("Partner", "Escalated", 6),
    ("Partner", "Open", 10),
]
grand_total, columns = prepare_channel_mekko(
    ticket_counts, ["Web", "Phone", "Partner"],
    ["Closed", "Escalated", "Open"])
assert grand_total == 116
assert [column["total"] for column in columns] == [38, 50, 28]
assert columns[1]["segments"][1]["height"] == 0.5
assert columns[1]["segments"][1]["area"] == 25 / 116
assert abs(sum(segment["area"] for column in columns
               for segment in column["segments"]) - 1) < 1e-12''',
        "cost": "With R counted rows, C displayed columns and O outcomes, aggregation takes O(R) expected time and O(CO) cell storage. Constructing the full rectangular grid takes O(CO) time and space even when some observed cells are absent; those cells retain explicit zero counts. A fixed category order lets a renderer place rectangles in one pass. Floating-point coordinates may not sum to exactly one, so the tests use a small tolerance while the underlying integer counts remain authoritative. Do not round each cell percentage before computing positions: independent rounding creates gaps, overlaps and totals that no longer reconcile.",
        "mistakes": ["Giving every column equal width while claiming to show its share of the total.", "Reading conditional segment height as the segment's contribution to all records.", "Rounding percentages before laying out the rectangles and losing reconciliation.", "Comparing equal-sized panels as absolute totals without stating their different population sizes.", "Putting text only inside narrow cells that cannot be read or focused."],
        "drill": "Build a channel-by-outcome ledger for 47 reporting units. Reconcile row, column and grand totals; label one cell with both its within-channel share and its joint share; then test the chart at a mobile width without discarding the small cells.",
        "related": [prefix + "mosaic-plots-joint-area-conditional-rate-and-empty-cells", prefix + "stacked-bars-composition-and-changing-denominators", prefix + "aggregation-grain-and-denominator", prefix + "chart-export-manifest-data-and-render-version"],
    },
    {
        "slug": "circle-packing-leaf-area-parent-enclosure-and-label-crowding",
        "title": "Circle packing: compare leaves without misreading parent circles",
        "summary": "Prepare a hierarchy for nested circles, count only leaves, and distinguish proportional leaf area from the whitespace inside enclosing parents.",
        "sections": [
            ("Containment communicates ancestry first", "Circle packing nests child circles inside larger enclosing circles. The visible enclosure answers where a leaf belongs, while a leaf's area can encode a count. These meanings are easy to mix. A parent circle encloses child circles plus empty space, so its visible area is generally not a precise representation of the sum of its children's counts. Do not place a parent total on the same area scale as leaves and invite literal area comparison. Show exact totals in labels or a companion table. Use a full-path identifier for every node: Open under Dispatch and Open under Billing are different leaves. In a service queue ledger, count each ticket in exactly one terminal queue. If the same ticket can belong to multiple queues, change the measure to queue assignments or choose another view. [[data-visualization/treemap-hierarchy-leaf-sums-and-area-comparison|Treemaps]] use space more efficiently, while [[data-visualization/sunburst-charts-leaf-ledgers-parent-totals-and-depth|sunbursts]] show ancestry in rings."),
            ("Calculate weights before drawing circles", "Build totals upward from terminal leaves, never by adding a separately entered parent value to its children. A leaf with count 16 needs four times the area of a leaf with count four, which means twice the radius before any layout scaling. The worked code computes both prefix totals and target leaf radii, and verifies the root total. A packing algorithm then moves the circles to fit within their enclosing parents, often scaling them together. Padding and the arrangement of siblings introduce empty space. A stable label order and stable layout seed matter in recurring reports, or viewers will mistake a rearranged cluster for a changed relationship. Preserve leaf identifiers through layout updates. [[data-visualization/aggregation-grain-and-denominator|Grain]] and [[data-visualization/chart-export-manifest-data-and-render-version|export manifests]] keep the geometric view tied to its ledger."),
            ("Small leaves need another route to inspection", "If a leaf's rendered diameter is smaller than a usable touch or focus target, do not rely on the circle for discovery. Provide a searchable hierarchy table with full path, leaf count and parent share; let users focus a row and highlight the circle. Labels should not be forcibly clipped into tiny circles. Put full paths in the table and display only short names where there is enough room. A branch with hundreds of tiny leaves may need a drill-down action with an explicit breadcrumb back to the parent. Grouping them as Other is valid only within one parent and with a declared threshold; the original leaves must remain in the data export. [[data-visualization/interactive-chart-keyboard-focus-and-data-table-contract|Keyboard focus]] and [[data-visualization/accessible-color-and-text-alternatives|text alternatives]] are part of the chart, not optional extras."),
            ("Choose the view for the comparison", "A packed-circle diagram is good for exploring a hierarchy and spotting dominant leaves within a branch. It is weak for precise ranking of leaves scattered across different parents because people compare circle areas poorly and blank packing space interferes with apparent size. For rank questions, pair the diagram with a bar chart sorted by count. For proportional share across the entire hierarchy, a treemap may waste less space. For following a path from root to leaf, a sunburst can make depth more explicit. Keep the same top-level colors and comparable scale across updates, and state whether the geometry was recalculated after a filter. A filter that removes a branch should not silently make every surviving leaf look larger when the task is to compare before and after. [[data-visualization/scale-baseline-and-axis-integrity|Scale integrity]] and [[data-visualization/linked-filters-cohort-denominators-and-selection-state|linked filters]] apply even without visible axes."),
        ],
        "code": '''from collections import Counter
from math import isclose, pi, sqrt

def prepare_queue_pack(leaf_counts):
    if not leaf_counts:
        raise ValueError("leaf counts are required")
    totals, seen = Counter(), set()
    for path, count in leaf_counts:
        if (not isinstance(path, tuple) or len(path) != 3 or
                any(not isinstance(label, str) or not label.strip()
                    for label in path) or path in seen or
                isinstance(count, bool) or not isinstance(count, int) or count <= 0):
            raise ValueError("each unique leaf needs three labels and a positive count")
        seen.add(path)
        for depth in range(4):
            totals[path[:depth]] += count
    leaves = {path: sqrt(count / pi) for path, count in leaf_counts}
    assert totals[()] == sum(leaf_counts[index][1]
                             for index in range(len(leaf_counts)))
    return totals, leaves

queue_leaves = [
    (("Operations", "Dispatch", "Open"), 16),
    (("Operations", "Dispatch", "Closed"), 4),
    (("Operations", "Returns", "Open"), 9),
    (("Operations", "Returns", "Closed"), 7),
    (("Finance", "Billing", "Open"), 13),
    (("Finance", "Billing", "Closed"), 11),
]
totals, radii = prepare_queue_pack(queue_leaves)
assert totals[()] == 60
assert totals[("Operations",)] == 36
assert isclose(radii[("Operations", "Dispatch", "Open")] /
               radii[("Operations", "Dispatch", "Closed")], 2)
assert isclose(pi * radii[("Finance", "Billing", "Open")] ** 2, 13)''',
        "cost": "For R leaf rows and fixed depth D, deriving prefix totals takes O(RD) time and O(N) space for N distinct nodes. Computing one target radius per leaf takes O(R) time and space. These are weights, not final coordinates. The packing step depends on the renderer and its padding/layout algorithm; it may alter absolute radii while preserving relative leaf areas. Do not use enclosing-parent pixel area as an exact sum because it includes blank regions. For a large tree, prepare a compact table and allow branch-by-branch exploration rather than drawing all leaves as subpixel circles.",
        "mistakes": ["Counting a parent value again after already summing its leaves.", "Comparing enclosing parent-circle area as though empty packing space were data.", "Using equal radius instead of equal area for equal leaf counts.", "Merging leaves with the same short label under different parents.", "Making tiny circles the only path to discover or select small categories."],
        "drill": "Prepare a three-level queue tree with 47 terminal categories. Reconcile each branch from leaves, compute target leaf areas, and create a companion table that allows a reader to find every small leaf even when its rendered circle cannot hold a label.",
        "related": [prefix + "treemap-hierarchy-leaf-sums-and-area-comparison", prefix + "sunburst-charts-leaf-ledgers-parent-totals-and-depth", prefix + "aggregation-grain-and-denominator", prefix + "interactive-chart-keyboard-focus-and-data-table-contract"],
    },
]

publish(
    lessons,
    sort_start=8900,
    module_groups=[("Area-encoded scatterplots", [0]),
                   ("Variable-width composition charts", [1]),
                   ("Nested-circle hierarchies", [2])],
    incoming={
        "scatterplot-overplotting-density-and-sampling-bias": [0],
        "proportional-symbol-maps-area-scale-and-overlap": [0],
        "hexbin-density-grid-resolution-and-exposure": [0],
        "small-multiples-shared-scales-and-facet-order": [0],
        "mosaic-plots-joint-area-conditional-rate-and-empty-cells": [1],
        "stacked-bars-composition-and-changing-denominators": [1],
        "likert-diverging-stacks-neutral-split-and-response-denominators": [1],
        "chart-export-manifest-data-and-render-version": [1],
        "treemap-hierarchy-leaf-sums-and-area-comparison": [2],
        "sunburst-charts-leaf-ledgers-parent-totals-and-depth": [2],
        "aggregation-grain-and-denominator": [2],
        "interactive-chart-keyboard-focus-and-data-table-contract": [2],
    },
    packet_name="aitrove-data-visualization-import-20261010-e.json",
)
