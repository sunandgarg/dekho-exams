"""Add original Likert and dot-density lessons to Data Visualization."""
from data_visualization_batch import publish

prefix = "data-visualization/"
lessons = [
    {
        "slug": "likert-diverging-stacks-neutral-split-and-response-denominators",
        "title": "Likert diverging stacks: keep the neutral split and response denominator honest",
        "summary": "Build survey-response bars around a declared midpoint while retaining item counts, nonresponse and the ordered response distribution.",
        "sections": [
            ("Plot an ordered response, not a signed measurement", "A Likert item records an ordered category such as strongly disagree, disagree, neutral, agree or strongly agree. A diverging stacked bar puts the disagreement categories to the left of a center and agreement categories to the right. It makes direction and balance easy to scan across questions. Yet the categories are ordinal: the spacing between adjacent labels is not guaranteed to represent an equal psychological distance. Do not claim a change from one category to another has a precise numeric magnitude merely because the bar uses equal-width units. The chart should preserve the original five counts and their order; a single favorable-minus-unfavorable score can hide a polarized item with many respondents on both ends. [[data-visualization/stacked-bars-composition-and-changing-denominators|Stacked-bar composition]] explains the part-to-whole encoding, while [[data-visualization/diverging-bars-zero-reference-and-signed-difference|signed diverging bars]] serve a different data type."),
            ("Declare the center and the neutral convention", "For a five-category item, one useful convention splits the neutral share evenly across the center: half extends left and half extends right. It makes negative and positive segment lengths symmetric around a visually centered neutral category. The neutral response itself remains one category and one count; splitting its drawing width must never double its reported count. Other layouts keep the full neutral block on one side or omit it from the diverging calculation. These choices change the visual origin, so use one convention across every compared item and name it in the legend. The contract below returns segment endpoints, not a plotting-library call, so a renderer can draw exact intervals and an accessible table can show unsplit counts. The center position is a presentation rule, not a statistic. [[data-visualization/scale-baseline-and-axis-integrity|Baseline integrity]] applies as much to opinion charts as to numeric axes."),
            ("Separate item response from invitation count", "If 83 people receive a questionnaire and only 59 answer an item, a bar normalized to 100 percent of answers describes those 59 respondents. It does not imply 83 people expressed an opinion. Show response count and missing count beside each item, and choose whether the displayed percentages use answered responses or all invited people. A survey can have different eligible populations per item because of branching, so a single global denominator may be wrong. Missing, skipped, not applicable and explicit neutral are distinct states. The worked example accepts an eligible count per item and uses answered responses for the five segments while returning the missing total separately. If groups differ in response propensity, equal-looking bars can be misleading; inspect who answered before interpreting a difference. [[data-visualization/aggregation-grain-and-denominator|Grain and denominator]] and [[data-visualization/linked-filters-cohort-denominators-and-selection-state|cohort filters]] make that comparison auditable."),
            ("Compare the distribution before sorting the questions", "Sorting items by net agreement can help locate extremes but can also hide the questionnaire's intended order. Declare the sort key and preserve a stable question ID, especially if a dashboard allows resorting. For paired waves, compare like-for-like populations and wording; a changed label or response option can move a bar without a real attitude change. Small subgroups deserve visible sample counts and, where appropriate, an uncertainty display rather than a bold ranking. Use a consistent left-to-right palette whose labels are readable without color. The full five-category distribution belongs in the accompanying table, including neutral and missing counts. Avoid stacked bars so narrow that individual slices disappear; a small-multiple table or grouped display can be clearer for close comparisons. [[data-visualization/uncertainty-and-small-sample-display|Small-sample display]], [[data-visualization/small-multiples-shared-scales-and-facet-order|shared scales]] and [[data-visualization/accessible-color-and-text-alternatives|text alternatives]] support that choice."),
        ],
        "code": '''RESPONSE_ORDER = ("strongly_disagree", "disagree", "neutral",
                  "agree", "strongly_agree")

def likert_layout(items: list[tuple[str, int, dict[str, int]]]):
    seen_items = set()
    output = []
    for item_id, eligible, counts in items:
        if (not item_id or item_id in seen_items or
                not isinstance(eligible, int) or eligible <= 0 or
                set(counts) != set(RESPONSE_ORDER) or
                any(not isinstance(counts[key], int) or counts[key] < 0
                    for key in RESPONSE_ORDER)):
            raise ValueError("items need unique IDs, eligibility and five counts")
        seen_items.add(item_id)
        answered = sum(counts.values())
        if answered == 0 or answered > eligible:
            raise ValueError("answered count must be positive and at most eligible")
        shares = {key: counts[key] / answered for key in RESPONSE_ORDER}
        neutral_half = shares["neutral"] / 2
        cursor = -(shares["strongly_disagree"] + shares["disagree"] + neutral_half)
        segments = []
        for key, width in (("strongly_disagree", shares["strongly_disagree"]),
                           ("disagree", shares["disagree"]),
                           ("neutral_left", neutral_half),
                           ("neutral_right", neutral_half),
                           ("agree", shares["agree"]),
                           ("strongly_agree", shares["strongly_agree"])):
            segments.append((key, cursor, cursor + width))
            cursor += width
        output.append({"item": item_id, "eligible": eligible,
                       "answered": answered, "missing": eligible - answered,
                       "counts": counts.copy(), "segments": segments})
    return output

survey = [("onboarding-clarity", 83,
           {"strongly_disagree": 5, "disagree": 7, "neutral": 11,
            "agree": 23, "strongly_agree": 13})]
layout = likert_layout(survey)[0]
assert (layout["answered"], layout["missing"]) == (59, 24)
assert abs(layout["segments"][0][1] + 17.5 / 59) < 1e-12
assert abs(layout["segments"][2][2]) < 1e-12
assert abs(layout["segments"][-1][2] - 41.5 / 59) < 1e-12
assert layout["counts"]["neutral"] == 11''',
        "cost": "For I items and a fixed five-response scale, validating counts and constructing segment endpoints costs O(I) time and O(I) output space. With a configurable K-category scale, the same approach is O(IK) in time and space. The worked item has 59 answers among 83 eligible people, leaving 24 missing. Its 11 neutral answers are displayed as two widths of 5.5 divided by 59, but still reported as 11 respondents. The left edge is negative 17.5 divided by 59 and the right edge positive 41.5 divided by 59; those lengths sum to one answered-response unit. They are drawing coordinates, not a claim that attitudes are numeric distances.",
        "mistakes": ["Treating nonresponse as neutral or silently removing missing counts from the report.", "Counting neutral twice after drawing half its width on each side of the center.", "Mixing percent of answered respondents with percent of all eligible people across items.", "Ranking tiny subgroups as if a few answers establish a stable preference order."],
        "drill": "Collect 47 survey items with item-specific eligible counts. For each, reconcile all five answers and missing records, produce centered segments with the same neutral convention, and compare the chart with an accessible count table before sorting items by net agreement.",
        "related": [prefix + "stacked-bars-composition-and-changing-denominators", prefix + "diverging-bars-zero-reference-and-signed-difference", prefix + "aggregation-grain-and-denominator", prefix + "uncertainty-and-small-sample-display"],
    },
    {
        "slug": "dot-density-maps-fixed-dot-value-random-placement-and-area",
        "title": "Dot-density maps: fixed dot value, reproducible placement and area meaning",
        "summary": "Convert regional counts to stable synthetic dots without implying exact locations, and audit rounding, area, projection and rendering limits.",
        "sections": [
            ("State what one dot represents", "A dot-density map places repeated symbols inside a geographic area to express an aggregate count. If one dot represents 47 households, a region with 470 households receives ten dots. Those coordinates are a visual allocation inside the region, not the known addresses of the households. This distinction belongs in the title or legend, because a reader may otherwise infer a cluster at a fabricated location. Use a fixed dot value across compared regions and state the rounding rule for counts that are not exact multiples. A region with zero reported count needs a different treatment from one with missing data; drawing neither would conflate absence with ignorance. [[data-visualization/choropleth-rates-boundaries-and-missing-regions|Choropleth missingness]] and [[data-visualization/proportional-symbol-maps-area-scale-and-overlap|proportional symbols]] offer related but different spatial encodings."),
            ("Choose the allocation unit and map projection", "Dots dispersed uniformly inside a coarse district depict its district-level total but provide no evidence of neighborhood-level distribution. If a finer geographic breakdown exists, allocate within those smaller units first; do not use a population-weighted placement mask unless that secondary data is reliable, documented and appropriate to the measured phenomenon. Map area matters. On an equal-area projection, a region covering twice the physical area can display the same number of dots at half the visual density. A projection that changes relative area across the map can create a false density comparison. Longitude and latitude degrees are not equal-area drawing units, so do not sample uniformly in raw degrees and treat the result as an area-faithful map. The small contract below accepts rectangular regions already expressed in equal-area planar coordinates. A real irregular polygon needs a proper geometry sampler and masking around holes or excluded land. [[data-visualization/map-antimeridian-wrapping-bounds-and-projection-distortion|Projection and wrapping]] must be resolved before placement."),
            ("Make random placement stable and disclose rounding", "If dots jump to new positions after every refresh, a reader can mistake random redraw for a changed population. Use a fixed seed tied to a chart revision, and preserve that seed in export metadata. Independent seeds across regions keep one region's appearance stable when another region is added. The count-to-dot conversion here rounds each region to the nearest whole dot, with exact half-dot ties rounded upward for nonnegative counts. This introduces at most half a dot value of absolute rounding error per region. Show original counts in a table and keep an aggregate reconciliation of rendered-equivalent count versus source count. Choosing a very large dot value can erase small regions; choosing a tiny value can flood the display and slow rendering. Set a practical visible-dot budget before drawing. [[data-visualization/chart-export-manifest-data-and-render-version|Export manifests]] capture the dot value and seed, while [[data-visualization/large-series-level-of-detail-and-extrema|level-of-detail controls]] cover dense outputs."),
            ("Limit what a viewer can infer", "A dot map can help compare the spatial density of counts when the areas, units and projection are compatible. It cannot locate an individual observation, prove a cluster inside a region, or explain why a count is high. Dot overlap at small view scales can make density look darker without revealing individual marks; zoom behavior needs a declared reference scale or a separate small-scale rendering policy. For several categories, maintain the same dot value and distinguish categories by labels and accessible symbols or colors, then reconcile each category's count independently. If totals are the decision metric, a table or proportional symbol map may be easier to read. If rates are the decision metric, a choropleth with a meaningful denominator may be better. Do not mix a count-encoded dot map with a rate legend. [[data-visualization/aggregation-grain-and-denominator|Denominator discipline]] and [[data-visualization/accessible-color-and-text-alternatives|accessible text]] keep the map's claim precise."),
        ],
        "code": '''from hashlib import sha256
from math import isfinite, floor
from random import Random

def dot_density_rectangles(regions: list[tuple[str, int, tuple[float, float, float, float]]],
                           dot_value: int, revision: str, max_dots: int = 20000):
    if (not isinstance(dot_value, int) or dot_value <= 0 or
            not revision or not isinstance(max_dots, int) or max_dots <= 0):
        raise ValueError("dot value, revision and budget must be valid")
    seen = set()
    output = []
    rendered_total = source_total = 0
    for region_id, household_count, bounds in regions:
        if (not region_id or region_id in seen or
                not isinstance(household_count, int) or household_count < 0 or
                len(bounds) != 4 or any(not isfinite(edge) for edge in bounds)):
            raise ValueError("region IDs, counts and planar bounds must be valid")
        seen.add(region_id)
        west, south, east, north = bounds
        if not west < east or not south < north:
            raise ValueError("rectangles need positive area")
        dot_count = floor(household_count / dot_value + 0.5)
        if rendered_total // dot_value + dot_count > max_dots:
            raise ValueError("visible dot budget exceeded; increase dot value")
        seed_bytes = sha256((revision + ":" + region_id).encode()).digest()
        randomizer = Random(int.from_bytes(seed_bytes[:8], "big"))
        dots = [(randomizer.uniform(west, east), randomizer.uniform(south, north))
                for _ in range(dot_count)]
        output.append((region_id, household_count, dots))
        source_total += household_count
        rendered_total += dot_count * dot_value
    return output, source_total, rendered_total

districts = [("district-47", 470, (0.0, 0.0, 4.0, 2.0)),
             ("district-59", 117, (4.0, 0.0, 6.0, 2.0))]
placements, source, represented = dot_density_rectangles(districts, 47, "release-83")
assert [len(row[2]) for row in placements] == [10, 2]
assert (source, represented) == (587, 564)
assert placements == dot_density_rectangles(districts, 47, "release-83")[0]
assert all(0 <= x <= 4 and 0 <= y <= 2 for x, y in placements[0][2])''',
        "cost": "For R regions and D emitted dots, region validation and count conversion take O(R) time, placement O(D) time, and the returned coordinates O(D) space. The per-region seed hash has constant input handling apart from identifier length. The worked first rectangle holds ten dots for 470 households; the second holds two dots for 117 households. Those twelve dots represent 564 households against a source total of 587, a 23-household rounding gap shown explicitly rather than hidden. This is a rectangle-only placement contract in equal-area planar coordinates. For real polygons, use a geometry library with interior and hole checks; no synthetic point should escape its region.",
        "mistakes": ["Presenting a synthetic dot as an actual household or event location.", "Sampling uniformly in raw longitude and latitude while interpreting dot spacing as equal area.", "Changing the random seed on refresh and implying moved observations.", "Leaving a low-count region visually blank without showing its original count and rounding loss."],
        "drill": "Map 47 synthetic districts with one dot per 47 households. Audit original count, displayed dot count and rounding error by district; hold the seed and projection fixed across two releases, and reject a scale that exceeds the visible-dot budget.",
        "related": [prefix + "choropleth-rates-boundaries-and-missing-regions", prefix + "proportional-symbol-maps-area-scale-and-overlap", prefix + "map-antimeridian-wrapping-bounds-and-projection-distortion", prefix + "large-series-level-of-detail-and-extrema"],
    },
]

publish(
    lessons,
    sort_start=8782,
    module_groups=[("Ordinal survey response displays", [0]),
                   ("Count-based geographic displays", [1])],
    incoming={
        "stacked-bars-composition-and-changing-denominators": [0],
        "diverging-bars-zero-reference-and-signed-difference": [0],
        "uncertainty-and-small-sample-display": [0],
        "aggregation-grain-and-denominator": [0, 1],
        "choropleth-rates-boundaries-and-missing-regions": [1],
        "proportional-symbol-maps-area-scale-and-overlap": [1],
        "map-antimeridian-wrapping-bounds-and-projection-distortion": [1],
        "large-series-level-of-detail-and-extrema": [1],
    },
    packet_name="aitrove-data-visualization-import-20261008-r.json",
)
