"""Add original gains, residual-diagnostic and population-pyramid lessons."""
from data_visualization_batch import publish

prefix = "data-visualization/"
lessons = [
    {
        "slug": "cumulative-gains-lift-score-ties-and-contact-capacity",
        "title": "Cumulative gains and lift: rank contacts without hiding score ties",
        "summary": "Turn a ranked response model into an auditable contact-capacity curve with attainable thresholds, cohort counts and a random-selection baseline.",
        "sections": [
            ("Define the decision population", "A cumulative gains chart asks how many confirmed responders appear among the highest-ranked share of eligible contacts. The horizontal axis is contacts selected divided by all eligible contacts. The vertical axis is responders captured divided by all confirmed responders. Lift at that point is gain divided by selected share. These are different denominators; mixing them produces an impressive-looking but meaningless line. Freeze the eligibility rule, scoring date, response window and label-maturity rule before ranking. An unobserved response is not automatically a negative response. [[data-visualization/aggregation-grain-and-denominator|Grain and denominator]] checks belong beside the chart, especially when one customer has several campaign records."),
            ("Use a reachable threshold", "Sort by descending score and advance one whole score group at a time. Equal scores cannot be separated using the model score alone. A budget of 47 contacts might land inside a tie containing 11 people. Either contact the whole tied group, stop before it, or apply a declared secondary rule that the team can reproduce; do not show a fractional customer as an attainable decision. Plot points after complete groups, print the actual selected count, and draw the random-selection gain baseline as selected share. The random baseline has lift one at every positive selected share. [[data-visualization/roc-curves-tied-thresholds-false-positive-rates-and-partial-auc|ROC thresholds]] face the same tie issue, but their horizontal axis divides false alerts by actual non-events rather than contacts by all eligible records."),
            ("Read lift with capacity, not as a trophy", "If the top quarter contains half of all responders, cumulative lift at that contact depth is two. It does not mean the model doubles every person's response probability. Cumulative lift generally approaches one when all eligible contacts are selected, so a large value at a tiny first group should not dominate the decision. Show selected count, captured responders, gain and lift at each usable capacity. If outreach cost varies by channel or customer, a count-based gain curve is insufficient; calculate expected net value under the actual contact rule. [[data-visualization/precision-recall-curves-threshold-ties-prevalence-and-average-precision|Precision–recall curves]] show positive yield among selected contacts and are a useful companion, while [[data-visualization/probability-calibration-plots-bin-counts-prevalence-and-drift|calibration]] asks whether the scores themselves can be read as probabilities."),
            ("Protect evaluation against selection bias", "A campaign label is often observed only for people previously contacted. Ranking that historical contacted subset can make a new model appear stronger than it is for the full eligible population. Record who had a chance to respond, the old contact policy, and whether the evaluation uses randomized outreach or an appropriate correction. Compare candidate models on the same held-out cohort and response window. If outcome prevalence changes, gains and lift at a fixed share may shift because the target population changed. Slice by campaign, region or customer tenure only when each slice has enough confirmed responders to support the curve. [[data-visualization/uncertainty-and-small-sample-display|Small-sample displays]] should expose the event counts behind sharp early jumps."),
        ],
        "code": '''from math import isfinite

def gains_ledger(contacts: list[tuple[str, float, bool]]):
    contact_ids = [contact_id for contact_id, _, _ in contacts]
    if not contacts or len(contact_ids) != len(set(contact_ids)) or any(
            not contact_id for contact_id in contact_ids):
        raise ValueError("contacts need unique, nonempty IDs")
    if any(not isfinite(score) or type(responded) is not bool
           for _, score, responded in contacts):
        raise ValueError("scores must be finite and responses must be known")
    total_responses = sum(responded for _, _, responded in contacts)
    if total_responses == 0:
        raise ValueError("gain is undefined without responders")
    ranked = sorted(contacts, key=lambda record: record[1], reverse=True)
    selected = captured = cursor = 0
    points = [(None, 0, 0.0, 0.0, None)]
    while cursor < len(ranked):
        threshold = ranked[cursor][1]
        while cursor < len(ranked) and ranked[cursor][1] == threshold:
            captured += ranked[cursor][2]
            selected += 1
            cursor += 1
        share = selected / len(ranked)
        gain = captured / total_responses
        points.append((threshold, selected, share, gain, gain / share))
    return points

campaign_contacts = [("contact-47", 0.94, True),
                     ("contact-59", 0.87, False),
                     ("contact-83", 0.87, True),
                     ("contact-97", 0.61, False),
                     ("contact-101", 0.55, True),
                     ("contact-131", 0.31, False),
                     ("contact-149", 0.21, False),
                     ("contact-173", 0.08, False)]
trace = gains_ledger(campaign_contacts)
assert trace[2][:4] == (0.87, 3, 3 / 8, 2 / 3)
assert abs(trace[2][4] - 16 / 9) < 1e-12
assert trace[-1][1:] == (8, 1.0, 1.0, 1.0)''',
        "cost": "Sorting N contacts takes O(N log N) time; the grouped sweep takes O(N) time. The ranked records, ID set and returned points use O(N) space. The eight-contact check proves that a tied score contributes a single attainable point and gives lift 16/9 after selecting three contacts. That tiny ledger illustrates arithmetic only. It does not estimate campaign return or correct selective labels from past outreach.",
        "mistakes": ["Using responders among selected contacts as cumulative gain; that ratio is precision.", "Splitting tied scores to make an exact budget look reachable without a secondary rule.", "Comparing lift measured on different eligible populations or outcome windows.", "Calling never-contacted people nonresponders when their outcome cannot be observed."],
        "drill": "Take 470 eligible contacts with mature response labels and a fixed campaign window. Mark every tied threshold, then publish selected count, captured responders, gain, lift and outreach cost at capacities 47, 94 and 141; explain any capacity that falls inside a tie.",
        "related": [prefix + "precision-recall-curves-threshold-ties-prevalence-and-average-precision", prefix + "roc-curves-tied-thresholds-false-positive-rates-and-partial-auc", prefix + "probability-calibration-plots-bin-counts-prevalence-and-drift", prefix + "aggregation-grain-and-denominator"],
    },
    {
        "slug": "regression-residual-plots-fitted-values-segments-and-error-spread",
        "title": "Regression residual plots: locate bias, spread and missing segments",
        "summary": "Build residual-versus-predicted coordinates and fixed-bin summaries from held-out records before interpreting a regression error plot.",
        "sections": [
            ("Name the residual and the split", "For this lesson, residual means observed value minus predicted value. A positive residual is an underprediction; a negative residual is an overprediction. Put predicted value on the horizontal axis and residual on the vertical axis with a visible zero line. State the outcome unit and whether the records are training, validation or a final held-out set. Training residuals can look artificially calm after model selection. If repeated measurements belong to the same account or machine, preserve that identity when splitting and when estimating uncertainty. [[data-visualization/scatterplot-overplotting-density-and-sampling-bias|Overplotting controls]] matter when thousands of residuals pile onto rounded predictions."),
            ("Inspect structure before a score", "A curved center suggests the model misses a systematic relationship; a fan-shaped spread suggests error size changes with the predicted level. Bands or clusters may reveal a missing segment or a target recorded at only a few allowed values. None of these shapes by itself identifies a cause. Color or facet by a prespecified segment, but hold axes fixed across panels so one group's errors do not look small only because its scale expanded. [[data-visualization/small-multiples-shared-scales-and-facet-order|Small multiples]] make that comparison testable. Plot residuals against time as a second view; time order can reveal drift that disappears when points are sorted by predicted value."),
            ("Pair points with fixed-bin summaries", "Choose predicted-value bin boundaries before reading the result. For each bin, print support, mean signed residual, mean absolute error and perhaps an upper error quantile. The signed mean detects directional bias; the absolute mean cannot cancel positive and negative misses. A bin with three records should not receive the same visual authority as one with three thousand. Keep bins fixed when comparing model versions or periods and disclose records outside the chart domain. [[data-visualization/aggregation-grain-and-denominator|Population and denominator rules]] still apply: removing failed predictions changes the displayed population. [[data-visualization/uncertainty-and-small-sample-display|Uncertainty views]] can show how unstable a sparse bin's mean is."),
            ("Do not turn every pattern into a linear-model violation", "The familiar constant-variance diagnostic is useful for some regression assumptions, but count-like or positive skewed outcomes may naturally have error spread that grows with the expected value. The plot still documents operational error; interpreting it requires the loss function and data-generating process. Large residuals can be genuine costly cases, label errors or records outside the model's intended domain. Investigate with stable IDs, not anonymous dots. If the outcome was transformed during training, bring predictions and actuals back to a common declared scale before computing residuals. [[data-visualization/qq-plots-quantile-alignment-ties-and-tail-deviation|A Q–Q plot]] checks tail shape; it answers a different question from residual versus fitted value."),
        ],
        "code": '''from bisect import bisect_right
from math import isfinite, sqrt

def residual_profile(records: list[tuple[str, float, float]],
                     edges: list[float]):
    if (len(edges) < 2 or any(not isfinite(edge) for edge in edges)
            or any(left >= right for left, right in zip(edges, edges[1:]))):
        raise ValueError("bin edges must be finite and strictly increasing")
    record_ids = [record_id for record_id, _, _ in records]
    if len(record_ids) != len(set(record_ids)) or any(not key for key in record_ids):
        raise ValueError("record IDs must be unique and nonempty")
    bins = [[] for _ in range(len(edges) - 1)]
    points = []
    for record_id, observed, predicted in records:
        if (not isfinite(observed) or not isfinite(predicted)
                or predicted < edges[0] or predicted > edges[-1]):
            raise ValueError("record is invalid or outside the plot domain")
        residual = observed - predicted
        index = min(bisect_right(edges, predicted) - 1, len(bins) - 1)
        bins[index].append(residual)
        points.append((record_id, predicted, residual))
    summaries = []
    for index, errors in enumerate(bins):
        count = len(errors)
        summaries.append((edges[index], edges[index + 1], count,
                          sum(errors) / count if count else None,
                          sum(abs(error) for error in errors) / count
                          if count else None,
                          sqrt(sum(error * error for error in errors) / count)
                          if count else None))
    return points, summaries

shipment_estimates = [("shipment-47", 23, 20), ("shipment-59", 31, 32),
                      ("shipment-83", 44, 48), ("shipment-97", 68, 60),
                      ("shipment-101", 69, 72), ("shipment-131", 78, 88)]
points, bands = residual_profile(shipment_estimates, [0, 50, 100])
assert points[3] == ("shipment-97", 60, 8)
assert bands[0][2:5] == (3, -2 / 3, 8 / 3)
assert bands[1][2:5] == (3, -5 / 3, 7.0)''',
        "cost": "For N records and B fixed bins, assigning each prediction with binary search takes O(N log B) time and summarizing residuals takes O(N + B); storing the points, ID set and bin contents uses O(N + B) space. The six-shipment assertion checks sign convention and separates signed bias from absolute error. It does not diagnose serial correlation, supply uncertainty intervals or validate the model split. Those require a held-out design and more observations.",
        "mistakes": ["Switching residual sign between charts without changing the label.", "Re-estimating bins for each model so apparent segment changes cannot be compared.", "Dropping observations whose predictions lie beyond the drawn axis without an exclusion count.", "Using only average signed residual when large positive and negative errors cancel."],
        "drill": "Export 470 held-out shipment predictions with stable IDs and outcome times. Build residual-versus-predicted and residual-versus-time views, keep fixed bin edges and shared axes, and audit the three bins with the largest mean absolute error alongside their support counts.",
        "related": [prefix + "scatterplot-overplotting-density-and-sampling-bias", prefix + "small-multiples-shared-scales-and-facet-order", prefix + "qq-plots-quantile-alignment-ties-and-tail-deviation", prefix + "uncertainty-and-small-sample-display"],
    },
    {
        "slug": "population-pyramids-age-bands-mirrored-scales-and-unknown-categories",
        "title": "Population pyramids: compare age bands without losing the denominator",
        "summary": "Build a mirrored age distribution with shared age bins, one total-population denominator and an explicit unrecorded-category ledger.",
        "sections": [
            ("A mirror is a layout, not a negative population", "A population pyramid places age bands vertically and two recorded categories on opposite sides of a central zero line. One side is plotted with negative coordinates solely to mirror the bars; its underlying counts remain nonnegative. Name the categories as they were collected rather than guessing what a binary field means. The familiar pyramid shape is not a requirement: a region with older residents or migration concentrated in working ages may have a wide middle. Keep youngest ages at the bottom or label any reversed order prominently. [[data-visualization/scale-baseline-and-axis-integrity|Axis integrity]] matters because the left and right extents must have equal magnitude when their bar lengths are compared."),
            ("Choose count or share deliberately", "Counts show service volume. Shares show age structure for differently sized places or years. If each bar uses a percent, choose a denominator and print it: this lesson divides every age-and-category count by the total recorded population, including people whose category is unrecorded. Dividing the left side by its own category total and the right side by another total answers a different conditional question and makes widths deceptively comparable. For two places, use identical bin widths, axis limits and denominator definitions; show the underlying total of each place nearby. [[data-visualization/small-multiples-shared-scales-and-facet-order|Shared-scale panels]] prevent a small district from visually matching a large city by accident."),
            ("Reconcile coverage before drawing", "Age bands must cover the intended population once each without overlaps or gaps, and the reporting date must be the same across both sides. A top band such as 85 and older is open-ended; preserve that label rather than pretending it spans the same number of years as a five-year band. Unknown ages need an exclusion count and explanation outside the plotted bands. An unrecorded category is also not a third side; print its total and age-band breakdown in a companion table so the two mirrored sides do not silently claim to represent everyone. [[data-visualization/stacked-bars-composition-and-changing-denominators|Composition charts]] offer another view when more than two categories are central to the question."),
            ("Treat small counts as data, not shape", "A one-person change can visibly reshape a small-area band. Consider disclosure rules and uncertainty when publishing small geographies; combining bins may protect privacy and reduce noise, but the regrouping must apply to every compared area and year. Suppressed cells are not zero. Printed counts and an accessible table let readers distinguish a narrow bar from a missing value. [[data-visualization/accessible-color-and-text-alternatives|Accessible alternatives]] should give the age band, each count, total and percentage without relying on color or left-right position alone. A smooth outline drawn through sparse age groups adds no information and can imply detail the input never had."),
        ],
        "code": '''def pyramid_ledger(age_bands: list[tuple[int, int, int, int, int]]):
    if not age_bands:
        raise ValueError("at least one age band is required")
    ordered = sorted(age_bands)
    for index, (start_age, end_age, male, female, unrecorded) in enumerate(ordered):
        if (type(start_age) is not int or type(end_age) is not int
                or start_age < 0 or end_age <= start_age or
                any(type(count) is not int or count < 0
                    for count in (male, female, unrecorded))):
            raise ValueError("invalid age boundary or count")
        if index and start_age != ordered[index - 1][1]:
            raise ValueError("age bands must be contiguous and nonoverlapping")
    population = sum(male + female + unrecorded
                     for _, _, male, female, unrecorded in ordered)
    if population == 0:
        raise ValueError("percentage denominator cannot be zero")
    bars = [(start_age, end_age, -male / population,
             female / population, unrecorded / population)
            for start_age, end_age, male, female, unrecorded in ordered]
    assert abs(sum(right - left + missing
                   for _, _, left, right, missing in bars) - 1) < 1e-12
    return population, bars

catchment_counts = [(0, 18, 47, 45, 3), (18, 65, 141, 138, 5),
                    (65, 85, 29, 35, 2)]
population, bars = pyramid_ledger(catchment_counts)
assert population == 445
assert bars[0] == (0, 18, -47 / 445, 45 / 445, 3 / 445)
assert sum(band[4] for band in bars) == 10 / 445''',
        "cost": "For B age bands, sorting and validating the intervals takes O(B log B) time; the ledger needs O(B) output space. If input is already sorted and validated upstream, the count sweep is O(B). The 445-person check proves that both mirrored sides and the ten unrecorded-category records share one denominator. The code accepts only closed, finite upper age boundaries; an open-ended oldest band needs a separately labeled representation rather than a fabricated endpoint.",
        "mistakes": ["Reading negative drawing coordinates as negative people.", "Using each side's own total while labeling bars as shares of the whole population.", "Changing age-band widths between places or treating suppressed cells as zero.", "Dropping unrecorded categories while claiming the visible bars sum to the entire population."],
        "drill": "Compare two synthetic clinic catchments with 445 and 1,410 registered residents. Reconcile every age-band count to its population total, draw count and percentage versions on shared axes, and print unrecorded-category counts beside both charts.",
        "related": [prefix + "stacked-bars-composition-and-changing-denominators", prefix + "small-multiples-shared-scales-and-facet-order", prefix + "accessible-color-and-text-alternatives", prefix + "aggregation-grain-and-denominator"],
    },
]

publish(
    lessons,
    sort_start=8768,
    module_groups=[("Ranked outreach and regression checks", [0, 1]),
                   ("Population structure and comparison", [2])],
    incoming={
        "precision-recall-curves-threshold-ties-prevalence-and-average-precision": [0],
        "roc-curves-tied-thresholds-false-positive-rates-and-partial-auc": [0],
        "probability-calibration-plots-bin-counts-prevalence-and-drift": [0],
        "scatterplot-overplotting-density-and-sampling-bias": [1],
        "qq-plots-quantile-alignment-ties-and-tail-deviation": [1],
        "uncertainty-and-small-sample-display": [1],
        "stacked-bars-composition-and-changing-denominators": [2],
        "small-multiples-shared-scales-and-facet-order": [2],
        "accessible-color-and-text-alternatives": [2],
        "aggregation-grain-and-denominator": [2],
    },
    packet_name="aitrove-data-visualization-import-20261008-m.json",
)
