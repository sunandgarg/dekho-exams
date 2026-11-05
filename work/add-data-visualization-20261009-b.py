"""Publish original radar and waffle chart lessons."""
from data_visualization_batch import publish

prefix = "data-visualization/"
lessons = [
    {
        "slug": "radar-charts-metric-direction-normalization-and-axis-order",
        "title": "Radar charts: normalize metrics before comparing profiles",
        "summary": "Make each spoke's unit, direction and fixed range explicit; preserve axis order and avoid treating polygon area as a score.",
        "sections": [
            ("A profile is not a single measure", "A radar chart places several ordered metrics on radial spokes and connects one entity's values into a closed profile. It can help a team notice that a delivery operation is strong on timeliness yet weak on geographic coverage. The polygon is a visual index into those separate measurements, not an aggregate score. Before drawing a spoke, state its unit, whether higher or lower is better, and the fixed comparison range. Plotting minutes, percentages and hours on one unnamed radial scale makes the shape meaningless. Use the same definition for every entity and reporting period. A metric called accuracy must retain its denominator and eligibility policy, while a latency metric must say which requests and percentile it covers. [[data-visualization/aggregation-grain-and-denominator|Grain and denominator rules]], [[data-visualization/chart-question-and-visual-encoding|chart questions]] and [[data-visualization/dashboard-filter-and-provenance|dashboard provenance]] establish those inputs."),
            ("Normalize with a documented direction", "For each metric, map its declared lower and upper bounds to a common zero-to-one scale. If higher is better, a value at the upper bound maps to one. If lower is better, a value at the lower bound maps to one. The worked contract rejects out-of-range values rather than clipping them without warning. A clipping policy can be useful in an operational dashboard, but a clipped marker must be distinguished from a true value at the boundary. Bounds should come from a versioned target or stable domain rule, not from each panel's current minimum and maximum. Otherwise the same raw value moves when a new peer arrives. Put the raw numbers and their units in the adjacent text table. A normalized 0.8 on delivery time means a position within a declared 15-to-75-minute range; it does not mean 80 percent of deliveries were on time. [[data-visualization/scale-baseline-and-axis-integrity|Axis integrity]] and [[data-visualization/bullet-chart-target-bands-and-kpi-context|bullet targets]] show the underlying value more directly."),
            ("Freeze spoke order and read shape cautiously", "The order of spokes changes which values become adjacent and therefore changes the polygon's edges and area, even when the data stay identical. Pick an order by a declared operational grouping or a stable metric schema, then keep it across every panel and export. Repeat the first normalized value only to close the drawing path; do not count that repeated vertex as a sixth metric. A filled polygon can obscure another entity's outline, so compare few entities, label them directly and keep opacity low. Do not rank teams by enclosed area: area is affected by spoke order and radial transformation and has no defensible unit as an overall performance measure. If the goal is exact comparison across eight teams, a grouped dot plot or small multiples usually makes individual differences easier to read. [[data-visualization/parallel-coordinates-normalization-axis-order-and-brushing|Parallel coordinates]] handles more profiles, while [[data-visualization/small-multiples-shared-scales-and-facet-order|small multiples]] avoids overlapping fills."),
            ("Make absent and inapplicable metrics visible", "A missing accuracy rate should not be drawn at the center, because zero on the normalized axis denotes a measured value at the worst declared bound. Nor should a team with no eligible requests receive an invented score. Show an explicit gap, a separate missing marker, or omit the affected polygon with a reason; keep the metrics table complete. If a spoke is inapplicable to some entities, compare only a documented common metric set or separate those entities into another view. A trend panel should freeze ranges over time, or an apparent improvement can come solely from moving targets. Add text that identifies the largest raw differences and the sample sizes, then let readers inspect each metric separately. [[data-visualization/missingness-matrices-record-order-patterns-and-co-missing-fields|Missingness diagnostics]], [[data-visualization/accessible-color-and-text-alternatives|accessible alternatives]] and [[data-visualization/chart-export-manifest-data-and-render-version|export manifests]] preserve that context."),
        ],
        "code": '''from math import isfinite

def prepare_delivery_radar(metric_spec, readings):
    if len(metric_spec) < 3:
        raise ValueError("a radar profile needs at least three spokes")
    metric_names = [name for name, _, _, _ in metric_spec]
    if len(set(metric_names)) != len(metric_names) or set(readings) != set(metric_names):
        raise ValueError("metrics must be unique and match the readings")
    normalized = []
    for name, lower, upper, direction in metric_spec:
        value = readings[name]
        numbers = (lower, upper, value)
        if (not name or direction not in ("higher", "lower") or
                any(isinstance(number, bool) or not isinstance(number, (int, float))
                    or not isfinite(number) for number in numbers) or
                lower >= upper or not lower <= value <= upper):
            raise ValueError(f"invalid range or reading for {name}")
        fraction = (value - lower) / (upper - lower)
        normalized.append(fraction if direction == "higher" else 1 - fraction)
    return metric_names, normalized + normalized[:1]

delivery_metrics = [
    ("delivery_minutes", 15, 75, "lower"),
    ("accuracy_percent", 85, 100, "higher"),
    ("coverage_percent", 60, 100, "higher"),
    ("resolution_hours", 2, 14, "lower"),
]
delivery_readings = {"delivery_minutes": 27, "accuracy_percent": 94,
                     "coverage_percent": 88, "resolution_hours": 5}
spokes, closed_profile = prepare_delivery_radar(delivery_metrics, delivery_readings)
assert spokes == [name for name, _, _, _ in delivery_metrics]
assert [round(value, 2) for value in closed_profile] == [0.8, 0.6, 0.7, 0.75, 0.8]''',
        "cost": "For K metrics, validation and normalization take O(K) time and O(K) space. Rendering one profile adds K line segments; comparing E profiles adds O(EK) marks and may become unreadable well before computational cost matters. In the worked profile, 27 minutes on a 15-to-75-minute lower-is-better scale maps to 0.8; 94 percent accuracy on an 85-to-100-percent higher-is-better scale maps to 0.6. Coverage maps to 0.7, resolution time to 0.75, and the final 0.8 closes the path. These are four distinct metrics. No mean or area score is implied by the closing coordinate.",
        "mistakes": ["Putting raw minutes, percentages and hours on one radial scale without per-spoke normalization.", "Recomputing each spoke's bounds from the current comparison group.", "Treating a polygon's enclosed area as a meaningful total score or ranking.", "Changing spoke order between entities and then comparing their outlines.", "Drawing missing or not-applicable metrics at normalized zero without a separate state."],
        "drill": "Compare 47 delivery teams on four fixed metrics. Publish each metric's unit, direction, bounds, raw value and eligible population. Show only two profiles at once, keep spoke order fixed, and check the same comparison against a grouped dot plot before asking anyone to rank teams.",
        "related": [prefix + "parallel-coordinates-normalization-axis-order-and-brushing", prefix + "small-multiples-shared-scales-and-facet-order", prefix + "bullet-chart-target-bands-and-kpi-context", prefix + "accessible-color-and-text-alternatives"],
    },
    {
        "slug": "waffle-charts-fixed-cell-budget-largest-remainders-and-small-groups",
        "title": "Waffle charts: allocate whole cells without losing the total",
        "summary": "Turn category counts into a fixed grid with an exact denominator, deterministic remainder allocation and labels that preserve small groups.",
        "sections": [
            ("A cell is a share, not necessarily a record", "A waffle chart represents parts of one whole using a fixed grid of equal-sized cells. A 10-by-10 grid has one hundred visual units; when the underlying cohort contains 83 tickets, one cell represents roughly 0.83 ticket's worth of share, not a literal individual ticket. Say what the whole is and whether every category is mutually exclusive and exhaustive. If the same ticket can be both pending and escalated, it cannot be counted in both cells of a simple part-to-whole grid without an explicit overlap rule. Use a bar chart when precise rank or a small difference matters more than the visual composition. A waffle grid is useful when readers need a quick impression of shares and an adjacent exact-count table is available. [[data-visualization/stacked-bars-composition-and-changing-denominators|Stacked bars]], [[data-visualization/mosaic-plots-joint-area-conditional-rate-and-empty-cells|mosaic plots]] and [[data-visualization/aggregation-grain-and-denominator|denominator rules]] provide useful comparisons."),
            ("Allocate a fixed cell budget once", "Each category's ideal cell count is its exact count divided by the total, multiplied by the grid size. Independent rounding can produce a grid with 99 or 101 cells. The worked contract first grants each category the floor of its ideal quota, then distributes the remaining cells to the largest fractional remainders. Ties break by the input category order, which is part of the published contract. This guarantees that cell counts sum to the grid size while keeping each allocation near its quota. The categories stay in a stable semantic order rather than sorting by current size on each refresh. If the whole is zero, there is no share to plot; display an empty state instead of a blank grid that could be read as zero in every category. [[data-visualization/pareto-chart-cumulative-share-and-category-boundary|Cumulative categories]] and [[data-visualization/scale-baseline-and-axis-integrity|scale rules]] help keep the total visible."),
            ("Keep rare groups visible in text", "A category below one cell's share may legitimately receive zero colored cells after allocation. Hiding it from the legend would turn a rounding choice into a false claim that the group does not exist. Label every nonzero category with its exact count and percentage, and disclose the cell value. For operational failures, consider a separate rare-case list or a bar chart if one missed record is consequential. More cells improve resolution but make the grid harder to scan on a phone; choose the budget from the question and display size, not from the desire to show every fractional percent. Do not draw a half-filled cell unless its encoding is explained. Multiple waffle charts need the same cell budget, category order and color mapping, and their raw population totals should appear beside each grid. [[data-visualization/accessible-color-and-text-alternatives|Text alternatives]] and [[data-visualization/large-series-level-of-detail-and-extrema|detail limits]] protect readers from hidden exceptions."),
            ("Make layout and interaction deterministic", "A row-major grid fills cells across a row before moving down. A column-major grid produces a different visual boundary; neither changes the counts, but changing the rule between panels can make categories look shifted. Publish rows, columns, fill order and category order. The contract below returns a complete two-dimensional cell ledger so a renderer can color it without recalculating shares. Keyboard or screen-reader output should provide one summary per category instead of announcing one hundred indistinguishable squares. Hovering a cell should describe the category share and exact count, not pretend that a rounded cell corresponds to a particular ticket. When dashboard filters change the cohort, recompute every allocation from the filtered counts and update the denominator in the same transaction. [[data-visualization/linked-filters-cohort-denominators-and-selection-state|Linked filters]], [[data-visualization/interactive-chart-keyboard-focus-and-data-table-contract|keyboard access]] and [[data-visualization/chart-export-manifest-data-and-render-version|export contracts]] complete that behavior."),
        ],
        "code": '''def allocate_ticket_waffle(category_counts, rows: int, columns: int):
    if (not isinstance(rows, int) or isinstance(rows, bool) or rows < 1 or
            not isinstance(columns, int) or isinstance(columns, bool) or columns < 1):
        raise ValueError("grid dimensions must be positive integers")
    if not category_counts:
        raise ValueError("at least one category is required")
    names = [name for name, _ in category_counts]
    if len(set(names)) != len(names) or any(not name for name in names):
        raise ValueError("category names must be unique and nonempty")
    if any(not isinstance(count, int) or isinstance(count, bool) or count < 0
           for _, count in category_counts):
        raise ValueError("counts must be nonnegative integers")
    total = sum(count for _, count in category_counts)
    if total == 0:
        raise ValueError("a zero-size cohort has no shares")
    cell_budget = rows * columns
    floors = [count * cell_budget // total for _, count in category_counts]
    remainders = [count * cell_budget % total for _, count in category_counts]
    extra = cell_budget - sum(floors)
    for index in sorted(range(len(names)), key=lambda index: (-remainders[index], index))[:extra]:
        floors[index] += 1
    grid = [name for name, cells in zip(names, floors) for _ in range(cells)]
    return dict(zip(names, floors)), [grid[offset:offset + columns]
                                      for offset in range(0, cell_budget, columns)]

ticket_counts = [("resolved", 47), ("pending", 29), ("escalated", 7)]
allocation, grid = allocate_ticket_waffle(ticket_counts, rows=10, columns=10)
assert allocation == {"resolved": 57, "pending": 35, "escalated": 8}
assert len(grid) == 10 and all(len(row) == 10 for row in grid)
assert sum(allocation.values()) == 100''',
        "cost": "For K categories and C cells, exact integer quotas take O(K) time, sorting remainders takes O(K log K), and constructing the cell ledger takes O(C). Space is O(K + C). The sample has 83 tickets: 47 resolved, 29 pending and 7 escalated. In a one-hundred-cell grid, the largest-remainder rule assigns 57, 35 and 8 cells. Those figures total exactly one hundred, but their displayed cell counts are rounded shares of the 83-ticket cohort. The exact counts stay in the legend and export. If the escalated group had fewer than one cell's share, its nonzero count would still need a label even if the allocation gave it no cell.",
        "mistakes": ["Rounding every category independently and drawing a grid with too many or too few cells.", "Describing each square as one record when the cohort size differs from the cell budget.", "Dropping a nonzero category from the legend because it received zero rounded cells.", "Comparing grids with different cell budgets or changing category colors between panels.", "Counting overlapping categories twice without defining a mutually exclusive partition."],
        "drill": "Create two ten-by-ten grids for weekly ticket cohorts of 83 and 47. Reconcile the category counts to each cohort total, allocate cells with one frozen rule, list any nonzero category that receives no cell, and compare the result with a labeled stacked bar.",
        "related": [prefix + "stacked-bars-composition-and-changing-denominators", prefix + "mosaic-plots-joint-area-conditional-rate-and-empty-cells", prefix + "aggregation-grain-and-denominator", prefix + "accessible-color-and-text-alternatives"],
    },
]

publish(
    lessons,
    sort_start=8788,
    module_groups=[("Multimetric profiles", [0]),
                   ("Fixed-grid composition", [1])],
    incoming={
        "parallel-coordinates-normalization-axis-order-and-brushing": [0],
        "small-multiples-shared-scales-and-facet-order": [0],
        "bullet-chart-target-bands-and-kpi-context": [0],
        "dashboard-filter-and-provenance": [0],
        "stacked-bars-composition-and-changing-denominators": [1],
        "mosaic-plots-joint-area-conditional-rate-and-empty-cells": [1],
        "aggregation-grain-and-denominator": [1],
        "linked-filters-cohort-denominators-and-selection-state": [1],
    },
    packet_name="aitrove-data-visualization-import-20261009-b.json",
)
