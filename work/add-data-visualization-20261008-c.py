"""Publish four additional Data Visualization lessons."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-data-visualization-import-20261008-c.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "data-visualization/"
hub = prefix + "data-visualization-tutorial"

lessons = [
    {
        "slug": "box-violin-and-kde-bandwidth-for-group-comparisons",
        "title": "Box and violin charts: compare groups without inventing density",
        "summary": "Keep sample size, quartiles and bandwidth visible when a smoothed shape represents observations.",
        "sections": [
            ("Begin with observations", "A box summarizes a group's quartiles and median; a violin adds an estimated density shape. Neither replaces the sample size. A smooth violin made from seven delivery times can look as confident as one made from seven thousand. Put each group's count beside its label and show individual points for small groups. [[data-visualization/distribution-and-outlier-displays|Distribution and outlier displays]] explain what the summary hides. First check whether groups cover the same window, unit and eligibility rule. Otherwise the apparent difference may be a cohort change."),
            ("Declare the quartile rule", "Software packages can interpolate quartiles differently, and whiskers may mean the extrema or a multiple of the interquartile range. State the rule in the chart caption or export record. A point beyond a whisker is not automatically bad data; it is flagged under that rule. If the decision needs the fraction exceeding a service threshold, calculate that fraction directly rather than asking a box to imply it. [[data-visualization/empirical-cdf-percentiles-and-tail-reading|An empirical CDF]] answers threshold questions without a smoothing choice."),
            ("Treat bandwidth as a parameter", "A violin's width depends on a density estimate and its bandwidth. A wide bandwidth can merge two real modes; a narrow one can turn routine noise into several peaks. Compare more than one defensible bandwidth, retain a rug or points, and do not imply that a thin tail continues beyond a physical limit. The mirrored shape is a drawing convention, not a second population. Normalize violin widths by count only if width should carry count. Otherwise make widths equal and show counts separately. [[data-visualization/aggregation-grain-and-denominator|Grain and denominator]] still matter."),
            ("Keep groups comparable", "Use the same quantitative axis, bandwidth rule and density normalization across groups. Truncating each group to its own range can make spreads seem alike. For latency data, inspect zeros, censored values and caps before estimating density. If the data include repeated readings from the same device, an independent violin discards pairing. [[data-visualization/paired-change-slope-and-dumbbell-charts|A paired view]] retains it. Supply a text table with each count, median, quartiles and threshold exceedance for readers who cannot use the shape."),
        ],
        "code": '''def quartile_summary(readings: list[float]) -> dict[str, float | int]:
    from math import isfinite
    if not readings or any(not isfinite(value) for value in readings):
        raise ValueError("readings must be finite and nonempty")
    ordered = sorted(readings)
    def midpoint(values: list[float]) -> float:
        middle = len(values) // 2
        return (values[middle] if len(values) % 2 else
                (values[middle - 1] + values[middle]) / 2)
    middle = len(ordered) // 2
    lower = ordered[:middle]
    upper = ordered[middle + len(ordered) % 2:]
    return {"count": len(ordered), "median": midpoint(ordered),
            "q1": midpoint(lower) if lower else ordered[0],
            "q3": midpoint(upper) if upper else ordered[0]}

depot_latency = quartile_summary([47, 51, 59, 68, 81, 83, 96])
assert depot_latency == {"count": 7, "median": 68, "q1": 51, "q3": 83}''',
        "cost": "Sorting N observations costs O(N log N) time and O(N) storage for the ordered copy. A chart with G groups repeats this per group; density estimation adds work set by the estimator and evaluation grid. The code declares a median-of-halves quartile convention and handles a one-item group. It does not draw a violin or claim that seven points support a smooth density. Store the exact convention with the exported summary.",
        "mistakes": ["Drawing a smooth violin for a tiny group without points.", "Comparing boxes whose whiskers use different rules.", "Treating a flagged point as an invalid measurement.", "Changing density bandwidth between groups and reading widths as a real difference."],
        "drill": "Compare response times for three depots with 7, 47 and 810 records. Print each count, median and quartile rule; draw points for the smallest group, then inspect whether two bandwidth choices alter the visual claim.",
        "related": [prefix + "distribution-and-outlier-displays", prefix + "empirical-cdf-percentiles-and-tail-reading", prefix + "paired-change-slope-and-dumbbell-charts", prefix + "uncertainty-and-small-sample-display"],
    },
    {
        "slug": "correlation-heatmap-pairwise-coverage-and-ordering",
        "title": "Correlation heatmaps: show pairwise coverage before interpreting color",
        "summary": "Keep a correlation matrix honest about missing pairs, redundant cells and feature order.",
        "sections": [
            ("The matrix has more than coefficients", "A correlation cell describes observations shared by two variables. With missing fields, one cell may use 810 records and another 47; identical color saturation hides that difference. Carry a second matrix of pairwise counts and expose it in labels, tooltips or a companion table. A blank pair means insufficient shared records or an undefined statistic, not zero association. [[data-visualization/heatmap-missing-cells-and-color-domain|Missing-cell rules]] distinguish these states. Record which rows passed eligibility filters before calculating either matrix."),
            ("Choose a missing-data contract", "Pairwise deletion uses every available pair but can give each cell a different population. Complete-case deletion holds one population constant but may discard most records and change who remains. State the choice and counts. A constant column has zero variance and no Pearson correlation; mark it undefined. Do not fill its cell with zero merely to complete a square. [[data-science/dataset-grain-and-join-cardinality|Dataset grain and join checks]] should precede calculation so duplicated rows do not inflate confidence."),
            ("Order features for the reading task", "Alphabetical order is stable and auditable. A domain order groups related measures. Data-driven clustering can reveal blocks, but the clustering method and input matrix become part of the result; changing order between periods makes comparison harder. Fix order for side-by-side charts, or record the exact order for each export. Show a legend centered on zero with identical limits in every panel. [[data-visualization/scale-baseline-and-axis-integrity|Scale integrity]] prevents a weak coefficient from receiving the same shade as a strong one elsewhere."),
            ("Do not infer a mechanism", "A large coefficient can arise from shared time trends, repeated entities, selection or a third variable. The matrix is a screen for questions, not proof that changing one field changes another. Confirm striking cells with paired scatter plots, units and source counts; outliers can dominate a linear coefficient. Avoid painting both triangles when space is tight, since the duplicate area adds no information. [[data-visualization/scatterplot-overplotting-density-and-sampling-bias|Dense scatter views]] help inspect what the matrix compressed. Describe the population and time range beside every matrix."),
        ],
        "code": '''from math import sqrt

def pearson_pair(records: list[dict[str, float | None]],
                 left: str, right: str) -> tuple[float | None, int]:
    pairs = [(record[left], record[right]) for record in records
             if record.get(left) is not None and record.get(right) is not None]
    count = len(pairs)
    if count < 2:
        return None, count
    left_mean = sum(value[0] for value in pairs) / count
    right_mean = sum(value[1] for value in pairs) / count
    cross = sum((x - left_mean) * (y - right_mean) for x, y in pairs)
    left_square = sum((x - left_mean) ** 2 for x, _ in pairs)
    right_square = sum((y - right_mean) ** 2 for _, y in pairs)
    if not left_square or not right_square:
        return None, count
    return cross / sqrt(left_square * right_square), count

shipments = [{"distance": 47, "cost": 81},
             {"distance": 59, "cost": 97},
             {"distance": 71, "cost": 113},
             {"distance": 83, "cost": None}]
coefficient, paired_count = pearson_pair(shipments, "distance", "cost")
assert round(coefficient, 12) == 1 and paired_count == 3''',
        "cost": "For P fields and N rows, a direct full matrix performs O(P²N) pair work and stores O(P²) coefficients and counts. Columnar execution can lower constant costs, but pairwise coverage still needs explicit accounting. The example returns undefined for insufficient pairs or constant values and does not provide a significance test. A precise coefficient on three shared rows is weak evidence for a broad population claim.",
        "mistakes": ["Showing a coefficient without its pairwise record count.", "Coloring undefined correlations as zero.", "Changing row order across comparison periods without notice.", "Treating a strong correlation as a causal intervention result."],
        "drill": "Build a five-field matrix where one field appears in only 47 of 810 records. Show the count matrix beside the coefficient matrix, then compare pairwise and complete-case populations.",
        "related": [prefix + "heatmap-missing-cells-and-color-domain", prefix + "scatterplot-overplotting-density-and-sampling-bias", prefix + "scale-baseline-and-axis-integrity", prefix + "dashboard-filter-and-provenance"],
    },
    {
        "slug": "forecast-fan-charts-prediction-intervals-and-horizon",
        "title": "Forecast fan charts: label interval meaning and forecast horizon",
        "summary": "Separate observed history from forecasts and keep coverage claims attached to their method.",
        "sections": [
            ("A band needs a named quantity", "A shaded region around a forecast could show uncertainty in an estimated mean, uncertainty for a future individual outcome, or a range of scenarios. These are different claims. A future-observation prediction interval is usually wider than an interval for the mean under the same model assumptions. Label the target, coverage level and calibration period. [[data-visualization/uncertainty-and-small-sample-display|Uncertainty displays]] should also expose sample size and unstable estimates. Color alone must not carry the difference between observed and projected values."),
            ("Mark the boundary", "Draw the last observed time as a visible boundary and use a different line style for forecasts. A continuous line through that boundary can make modeled values look measured. Do not fill missing observed dates with predictions and call the whole line history. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Time-series gap rules]] still govern the observed segment. State whether the first future period is a complete day, week or fiscal interval, especially when a dashboard refreshes mid-period."),
            ("Nested bands need checks", "A fan chart may show 50, 80 and 95 percent intervals. At each horizon, narrower bands must sit inside wider ones. The lower bound may fall and the upper bound may rise as coverage increases. Check containment in the data before rendering. Wider horizons often have wider uncertainty, but that shape is not guaranteed for every conditioned model or bounded target. Never widen bands by hand for appearance. [[data-visualization/chart-export-manifest-data-and-render-version|The export]] should retain interval definition, model version and generation time."),
            ("Backtest the claim", "If an interval claims 80 percent coverage, compare past issued intervals with realized values at a fixed forecast horizon and documented window. Count misses alongside nominal coverage. A recent shock or measurement change can break earlier calibration. An 80 percent band is not a promise that exactly eight of every ten future points must land inside it; coverage is assessed across repeated forecasts under stated conditions. [[data-visualization/chart-annotations-event-windows-and-causal-claims|Event annotations]] can mark changed processes without proving their cause."),
        ],
        "code": '''def validate_fan_rows(rows: list[dict]) -> None:
    previous_horizon = -1
    for row in rows:
        horizon = row["horizon"]
        if not isinstance(horizon, int) or horizon <= previous_horizon:
            raise ValueError("horizons must increase")
        previous_horizon = horizon
        center = row["forecast"]
        inner = row["interval_50"]
        outer = row["interval_80"]
        if not (outer[0] <= inner[0] <= center <= inner[1] <= outer[1]):
            raise ValueError("intervals must nest around forecast")

issued_forecast = [
    {"horizon": 1, "forecast": 81,
     "interval_50": (75, 87), "interval_80": (68, 94)},
    {"horizon": 2, "forecast": 83,
     "interval_50": (74, 92), "interval_80": (62, 104)},
]
validate_fan_rows(issued_forecast)
assert issued_forecast[1]["interval_80"][1] == 104''',
        "cost": "Validation scans H horizons in O(H) time and O(1) additional space. Rendering nested bands scales with horizons times interval levels. The check verifies ordering and containment only; it cannot establish empirical coverage, calibration or model quality. Finite numeric values and exact time-zone handling also need validation at the source boundary before a production forecast is issued.",
        "mistakes": ["Calling a mean-confidence band a future-observation prediction interval.", "Drawing forecast points with the same style as measurements.", "Allowing an 80 percent band to cross inside its 50 percent band.", "Claiming nominal coverage without checking past issued forecasts against outcomes."],
        "drill": "Issue 47 weekly forecasts with saved 50 and 80 percent bounds. Mark the observed-to-forecast boundary, validate every nested interval, and report realized coverage at horizons one and four separately.",
        "related": [prefix + "uncertainty-and-small-sample-display", prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "chart-export-manifest-data-and-render-version", prefix + "chart-annotations-event-windows-and-causal-claims"],
    },
    {
        "slug": "funnel-chart-cohorts-stage-order-and-conversion",
        "title": "Funnel charts: hold the cohort still before calculating conversion",
        "summary": "Reconcile stage populations and time windows before publishing conversion rates or drop-off shapes.",
        "sections": [
            ("A funnel is a population claim", "Each stage should represent the same entrants moving through a declared sequence within a stated observation window. Counting every visit at stage one and only new users at stage two mixes populations. Define entrant ID, entry date, stage completion event and maximum allowed delay. Then count unique entrants reaching each stage. [[data-visualization/aggregation-grain-and-denominator|Grain and denominator rules]] make rates reproducible. Keep re-entries and repeated events explicit, since deduplication changes every step."),
            ("Distinguish step and overall rates", "A step conversion divides the current stage count by the immediately previous count. An overall conversion divides by the entry count. If 470 entrants reach review and 188 reach approval out of 810 starts, approval's step rate is 188/470 or 40 percent; overall approval is 188/810 or about 23.2 percent. Both are useful, but a chart with unlabeled percentages is ambiguous. Show count and denominator beside each rate. [[data-visualization/stacked-bars-composition-and-changing-denominators|Composition charts]] face the same denominator trap."),
            ("Late arrivals can make a false drop", "A current-week cohort has had less time to reach later stages than an older cohort. Wait until the conversion window has matured or mark rates provisional with a maturity cutoff. Do not compare a mature 29-day cohort with one observed for two days. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Provisional-period labels]] make this visible. If stages can be skipped or revisited, a strict funnel loses information; use a transition or flow view instead. [[data-visualization/sankey-flow-conservation-and-unobserved-exits|Flow conservation]] applies when exits and skips matter."),
            ("Audit monotonicity", "For a strict cohort funnel, counts cannot rise as stages advance. An increase signals duplicate counting, a changed filter, late data or a non-strict process. Do not clamp bars to make the chart look right. Inspect raw identities and stage timestamps. Segment filters should use a stable entry-time property; filtering later by a property acquired after conversion can bias the chart toward successful entrants. [[data-visualization/linked-filters-cohort-denominators-and-selection-state|Linked filters]] must preserve the entry cohort. Export stage order, window, counts and both rate definitions."),
        ],
        "code": '''def strict_funnel(stage_members: list[tuple[str, set[str]]]
                  ) -> list[tuple[str, int, float | None, float | None]]:
    if not stage_members or len({name for name, _ in stage_members}) != len(stage_members):
        raise ValueError("stages must be named and unique")
    entrants = stage_members[0][1]
    previous = entrants
    result = []
    for stage_name, members in stage_members:
        if not members <= previous:
            raise ValueError("stage contains non-eligible entrants")
        result.append((stage_name, len(members),
                       len(members) / len(previous) if previous else None,
                       len(members) / len(entrants) if entrants else None))
        previous = members
    return result

stages = [("start", {"u47", "u59", "u71", "u83"}),
          ("review", {"u47", "u59", "u71"}),
          ("approve", {"u47", "u71"})]
funnel = strict_funnel(stages)
assert funnel[-1] == ("approve", 2, 2 / 3, 2 / 4)''',
        "cost": "For S stages and total M stored membership IDs, subset checks and counts use O(M) expected time with hash sets and O(S) output space beyond the supplied sets. Persisting full ID sets can be costly; a warehouse may compute stage membership with distinct keys and checked joins. The example assumes a strict nested sequence and says nothing about timestamps or cohort maturity; enforce those earlier in the data pipeline.",
        "mistakes": ["Mixing sessions at one stage with unique people at another.", "Using a previous-stage denominator while labeling it overall conversion.", "Comparing mature and immature cohorts without a cutoff.", "Forcing increasing counts down to the prior stage instead of fixing the event model."],
        "drill": "Build a three-stage funnel for 810 entrants with a 29-day window. Report step and overall rates, then inject a skipped-stage user and explain why strict validation rejects that path.",
        "related": [prefix + "aggregation-grain-and-denominator", prefix + "stacked-bars-composition-and-changing-denominators", prefix + "sankey-flow-conservation-and-unobserved-exits", prefix + "linked-filters-cohort-denominators-and-selection-state"],
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
        "featured": False, "sort_order": 8724 + offset, "status": "published",
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
    for start, heading in ((0, "Distribution and association"),
                           (2, "Forecasts and conversion")):
        targets = new_paths[start:start + 2]
        row["data"]["modules"].append({"title": heading, "lessons": targets})
        row["body"] += f'<h2>{heading}</h2><ul>' + ''.join(
            f'<li>{link(target)}</li>' for target in targets) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "distribution-and-outlier-displays": [new_paths[0]],
    prefix + "empirical-cdf-percentiles-and-tail-reading": [new_paths[0]],
    prefix + "heatmap-missing-cells-and-color-domain": [new_paths[1]],
    prefix + "scatterplot-overplotting-density-and-sampling-bias": [new_paths[1]],
    prefix + "uncertainty-and-small-sample-display": [new_paths[2]],
    prefix + "time-series-gaps-calendars-and-provisional-periods": [new_paths[2]],
    prefix + "aggregation-grain-and-denominator": [new_paths[3]],
    prefix + "sankey-flow-conservation-and-unobserved-exits": [new_paths[3]],
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
