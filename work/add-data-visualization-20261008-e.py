"""Publish five original Data Visualization lessons and their internal links."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-data-visualization-import-20261008-e.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "data-visualization/"
hub = prefix + "data-visualization-tutorial"

lessons = [
    {
        "slug": "beeswarm-plots-collision-spacing-and-sample-count",
        "title": "Beeswarm plots: show individual values without inventing spread",
        "summary": "Keep the measured axis exact, treat sideways displacement as layout, and disclose how many marks are present.",
        "sections": [
            ("A dot is an observation", "A beeswarm places individual observations along a measured axis and moves marks sideways only enough to reduce overlap. The lateral coordinate is not a second measured variable. State that in the axis caption, because a wide swarm can otherwise be mistaken for more variation. If the mark count exceeds the display's collision capacity, use a declared sample or a distribution summary instead of silently dropping points. [[data-visualization/scatterplot-overplotting-density-and-sampling-bias|Overplotting and sampling bias]] determine whether the displayed dots still represent the underlying population. Report the raw count and the displayed count for every group."),
            ("Preserve ties and identity", "Repeated equal measurements should remain repeated observations. A deterministic layout lets an analyst compare revisions without random movement that looks like new data. Stable IDs matter when a reader selects or exports a point. If several rows share the same subject and timestamp, decide whether they are repeated measurements or duplicates before drawing. The plot cannot make that data decision. [[data-visualization/chart-export-manifest-data-and-render-version|The export manifest]] should preserve observation ID, group, measured value, sampling rule and layout version. A text alternative can list the median, range, count and number of tied values."),
            ("Collision radius is a visual parameter", "A beeswarm solver needs marker diameter in display pixels as well as the scale that maps values to pixels. Zooming, resizing or switching to mobile changes collision geometry. Thus an offset computed for one viewport cannot safely be reused for another. Cap the lateral spread only if the chart explicitly allows overlap after that cap; hiding dots is not acceptable. [[data-visualization/accessible-color-and-text-alternatives|Accessible mark encodings]] need a visible outline or shape difference when groups share a panel. Test the chart at the narrowest intended width."),
            ("Compare with a distribution summary", "The swarm is good for a few hundred visible records, particularly when outliers and ties are the story. At larger scale it becomes slow to lay out and hard to read. A box, violin or ECDF can summarize shape, while a small sample of dots reveals examples without pretending to be complete. [[data-visualization/box-violin-and-kde-bandwidth-for-group-comparisons|Box and violin plots]] have their own bandwidth and whisker decisions; they are not interchangeable with raw observations. If groups have unequal sample sizes, annotate counts next to labels so width is not mistaken for prevalence."),
        ],
        "code": '''from hashlib import sha256
from math import isfinite

def stable_strip_positions(records: list[tuple[str, str, float]],
                           spread: float = 0.38) -> list[tuple[str, str, float, float]]:
    if not 0 <= spread <= 0.5:
        raise ValueError("spread must fit inside one category")
    identifiers = [record_id for record_id, _, _ in records]
    if len(identifiers) != len(set(identifiers)) or any(not key for key in identifiers):
        raise ValueError("observation IDs must be unique and nonempty")
    if any(not group or not isfinite(value) for _, group, value in records):
        raise ValueError("group and measured value must be valid")
    placed = []
    for record_id, group, value in records:
        digest = sha256(record_id.encode("utf-8")).digest()
        fraction = int.from_bytes(digest[:8], "big") / (2**64 - 1)
        placed.append((record_id, group, value, (2 * fraction - 1) * spread))
    return placed

service_times = [("ticket-47", "priority", 81.0),
                 ("ticket-59", "priority", 81.0),
                 ("ticket-83", "standard", 97.0)]
positions = stable_strip_positions(service_times)
assert len(positions) == 3 and positions[0][2] == positions[1][2]
assert positions == stable_strip_positions(service_times)''',
        "cost": "Preparing N stable strip positions takes O(N) expected time and O(N) output space. This code produces reproducible jitter; it is not a collision-solving beeswarm. A true beeswarm needs screen-space marker geometry and may require O(N squared) comparisons in a simple placement algorithm. Do not label the jittered result collision-free. Preserve exact measured values and IDs in the export, and recalculate visual offsets when the display scale changes.",
        "mistakes": ["Reading sideways jitter as a measured quantity.", "Suppressing overlapped observations without recording the omitted count.", "Reseeding random positions on every redraw, making stable records appear to move.", "Calling deterministic jitter a collision-free beeswarm without checking marker radius."],
        "drill": "Draw 81 support-ticket response times across three queues. Keep equal values as separate dots, show each queue's count and compare a narrow mobile layout with a distribution summary.",
        "related": [prefix + "scatterplot-overplotting-density-and-sampling-bias", prefix + "box-violin-and-kde-bandwidth-for-group-comparisons", prefix + "accessible-color-and-text-alternatives", prefix + "chart-export-manifest-data-and-render-version"],
    },
    {
        "slug": "calendar-heatmap-complete-days-time-zones-and-missingness",
        "title": "Calendar heatmaps: distinguish an empty day from an absent day",
        "summary": "Generate the full date grid, fix the reporting time zone and encode missing observations separately from zero.",
        "sections": [
            ("A blank square has several meanings", "A calendar heatmap arranges daily values in a weekly grid. A white day could mean zero events, no feed, a day outside the reporting range or a suppressed value. Those states cannot share one silent color. Generate every expected local date first, then join observations and label each cell's status. [[data-visualization/heatmap-missing-cells-and-color-domain|Missing-cell heatmaps]] need the same distinction. For a support operation, a zero confirmed ticket count is evidence; an uncollected Saturday is not. Show the number of complete days beside any annual total."),
            ("Choose the reporting day", "An event at 00:20 UTC may belong to the prior local day. Convert timestamps to the declared reporting zone before aggregating, and record the zone in the export. Daylight-saving changes produce 23- or 25-hour local days in some regions; counts remain counts, but per-hour rates need an exposure adjustment. A calendar grid without its time-zone contract can move incidents across cells and distort weekday patterns. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Time-series calendar rules]] cover incomplete current periods and delayed arrivals. Mark provisional days rather than painting them as final."),
            ("Keep color comparable", "Fix the numeric color domain across years or related teams when the goal is comparison. Otherwise each year may assign the darkest shade to a different count. If the distribution has a long tail, state any transform or clipped maximum. A daily rate requires the matching daily denominator; weekend exposure often differs from weekday exposure. [[data-visualization/aggregation-grain-and-denominator|Grain and denominator]] come before color selection. A tooltip should expose date, value, status, denominator if used and refresh time, while a text table remains available for keyboard and screen-reader users."),
            ("Week structure is a locale decision", "Some audiences expect Monday-first weeks; others expect Sunday-first. Label weekdays, show month boundaries and test leap years, year transitions and ISO week edges. Do not infer a causal weekday pattern from a few colored streaks. A release schedule, holiday closure or data-delivery gap may explain the pattern. [[data-visualization/chart-annotations-event-windows-and-causal-claims|Event annotations]] should state what happened without claiming effect. Export an explicit date-status table so another analyst can reconstruct the image rather than reverse-engineering its colors."),
        ],
        "code": '''from datetime import date, timedelta

def complete_daily_series(start: date, end: date,
                          observed: dict[date, int | None]
                          ) -> list[tuple[date, str, int | None]]:
    if end < start or any(day < start or day > end for day in observed):
        raise ValueError("dates must fall inside the requested period")
    if any(value is not None and (not isinstance(value, int) or value < 0)
           for value in observed.values()):
        raise ValueError("daily counts must be nonnegative integers")
    result = []
    day = start
    while day <= end:
        value = observed.get(day)
        status = "missing" if value is None else "observed"
        result.append((day, status, value))
        day += timedelta(days=1)
    return result

calendar_rows = complete_daily_series(
    date(2026, 10, 1), date(2026, 10, 4),
    {date(2026, 10, 1): 47, date(2026, 10, 2): 0,
     date(2026, 10, 4): 59})
assert calendar_rows[1] == (date(2026, 10, 2), "observed", 0)
assert calendar_rows[2] == (date(2026, 10, 3), "missing", None)''',
        "cost": "For D days and O observed keys, validation and completion take O(D+O) time and O(D) output space. This code assumes the input keys already represent the correct reporting-zone dates; timestamp conversion belongs upstream. If a source uses null to mean suppression rather than missing delivery, give it its own status before calling this function. Store daily exposure separately when coloring rates.",
        "mistakes": ["Turning missing days into zeros.", "Aggregating UTC dates and labeling the result as a local calendar.", "Allowing each year to auto-scale its colors during comparison.", "Treating a partly reported current day as final."],
        "drill": "Build a 47-day operations calendar with a confirmed zero, a late feed, a holiday closure and one provisional day. Export the four states and explain the color domain.",
        "related": [prefix + "heatmap-missing-cells-and-color-domain", prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "aggregation-grain-and-denominator", prefix + "chart-annotations-event-windows-and-causal-claims"],
    },
    {
        "slug": "parallel-coordinates-normalization-axis-order-and-brushing",
        "title": "Parallel coordinates: make every axis conversion inspectable",
        "summary": "Compare multivariate profiles only after documenting normalization, axis order and missing-value treatment.",
        "sections": [
            ("A polyline is one record", "Parallel coordinates display one entity as a line crossing several vertical axes. Its crossings are the entity's values; line slopes between axes are visual connectors, not measured rates of change. Before drawing, name every metric and unit. A route whose five service measures have incompatible units cannot be read honestly on one raw height scale. [[data-visualization/scale-baseline-and-axis-integrity|Scale integrity]] applies independently to every axis. Put the raw value in a tooltip or adjacent table so a normalized line does not erase the original measurement."),
            ("Normalization changes the question", "Min-max normalization maps each axis to a shared display interval, but a single extreme entity can compress all others. Fixed policy bounds may be more stable than bounds computed from the current filter. If lower is preferable for one metric, invert its display direction and label that inversion. Never silently reverse an axis just to make good records form a tidy line. [[data-visualization/bullet-chart-target-bands-and-kpi-context|Target-oriented KPI charts]] may be clearer if the decision is only whether a threshold was met. Keep the bounds, direction and unit beside each dimension in exported metadata."),
            ("Axis order and brushing are analytic choices", "Swapping two adjacent axes changes which relationships are visually easiest to see, even though the data stay unchanged. Pick an order tied to the question, such as intake, response, resolution and cost, then preserve it across comparable views. Brushing one range selects entities; a linked table should show which IDs remain and how many were excluded. [[data-visualization/linked-filters-cohort-denominators-and-selection-state|Linked filters]] require explicit cohort state. Avoid drawing every record at full opacity: a thousand crossing lines become an opaque band. Sampling must retain a visible selected count and a full-population summary."),
            ("Missing values must not become fabricated paths", "A line should break or be omitted with an explicit reason when one dimension is absent; zero is not a replacement for missing. Check whether the missingness is related to the outcome being inspected. If only high-cost projects fail to report quality, excluding incomplete records changes the apparent relationship. [[data-visualization/chart-export-manifest-data-and-render-version|An export manifest]] should name complete-case rules, filter state, axis order, bounds and transformed values. For accessibility, offer a sortable table of the underlying records and a concise summary of which dimensions separate selected groups."),
        ],
        "code": '''from math import isfinite

def normalize_profile(profile: dict[str, float | None],
                      axes: dict[str, tuple[float, float, bool]]
                      ) -> dict[str, float | None]:
    if set(profile) != set(axes):
        raise ValueError("profile dimensions must match axis declarations")
    normalized = {}
    for metric, (low, high, lower_is_better) in axes.items():
        value = profile[metric]
        if not all(isfinite(bound) for bound in (low, high)) or high <= low:
            raise ValueError("axis bounds must be finite and ordered")
        if value is None:
            normalized[metric] = None
            continue
        if not isfinite(value) or not low <= value <= high:
            raise ValueError("measurement outside declared axis")
        position = (value - low) / (high - low)
        normalized[metric] = 1 - position if lower_is_better else position
    return normalized

axes = {"response_minutes": (0, 120, True),
        "resolved_percent": (0, 100, False)}
depot_profile = normalize_profile(
    {"response_minutes": 47, "resolved_percent": 81}, axes)
assert round(depot_profile["response_minutes"], 4) == 0.6083
assert depot_profile["resolved_percent"] == 0.81''',
        "cost": "For D dimensions in one record, normalization takes O(D) time and O(D) output space; N records take O(ND). Rendering N polylines can dominate interaction cost, especially when brushing triggers full redraws. The code rejects values outside policy bounds rather than clipping them invisibly. If clipping is intended, export both raw and displayed values and count clipped records by axis.",
        "mistakes": ["Interpreting connector slope as a real-world rate of change.", "Recomputing axis bounds after a filter and comparing line heights as if scale stayed fixed.", "Silently reversing one axis or replacing missing with zero.", "Drawing all records at full opacity and calling the dense band a cluster."],
        "drill": "Compare 59 depots on response time, resolution rate and cost. Publish fixed axis bounds, invert only metrics where lower is better, then brush a subgroup and reconcile its ID count to the table.",
        "related": [prefix + "scale-baseline-and-axis-integrity", prefix + "bullet-chart-target-bands-and-kpi-context", prefix + "linked-filters-cohort-denominators-and-selection-state", prefix + "chart-export-manifest-data-and-render-version"],
    },
    {
        "slug": "bump-chart-rank-ties-membership-and-period-coverage",
        "title": "Bump charts: show rank movement without losing ties or entrants",
        "summary": "Declare the ranking metric, tie policy and eligible entities for each period before connecting positions.",
        "sections": [
            ("Rank is an ordering, not a magnitude", "A bump chart connects an entity's ranks across periods. A move from third to first may reflect a tiny absolute difference or a major change; the line does not tell you which. Name the ranked measure and link to values behind each position. [[data-visualization/paired-change-slope-and-dumbbell-charts|Paired-change charts]] work better when the actual size of change matters. If a new entity enters the cohort, existing ranks can fall without their own measurements changing. Display entrants and exits as membership events rather than implying deterioration."),
            ("Ties need a written rule", "Equal measurements can share a rank, be assigned adjacent ranks by a secondary key, or be shown in a tied band. These choices produce different line paths. Competition ranking gives equal values the same rank and skips the next position; dense ranking does not skip. Neither should be selected by accident inside a plotting library. Preserve raw values and the chosen tie rule in the export. [[data-visualization/chart-export-manifest-data-and-render-version|Reproducible chart exports]] also need source period and eligibility criteria. Test ties at both top and bottom before publishing."),
            ("Hold the cohort question steady", "A panel can rank the same fixed set of entities every period or rank whoever was eligible at the time. The first view tracks a stable cohort; the second reflects changing membership. State which one readers see. If a missing measurement removes an entity from one period, show a line break or missing marker rather than assigning last place. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Provisional periods and data gaps]] are especially easy to hide in a rank-only display. Mark a period as provisional when its numerator or denominator can still change."),
            ("Limit crossings and preserve access", "Many crossing lines defeat tracing. Highlight a small set chosen by a documented rule, fade the remainder and let the reader search by entity ID. A table with period, rank, value and membership status is essential, because color-only line identity and hover-only labels fail on touch and assistive technology. [[data-visualization/accessible-color-and-text-alternatives|Text alternatives]] should call out the biggest rank rise, biggest fall, ties and entrants. Do not claim a trend from two ranks alone; a third period or actual values may tell a different story."),
        ],
        "code": '''from math import isfinite

def competition_ranks(scores: dict[str, float]) -> dict[str, int]:
    if any(not entity for entity in scores):
        raise ValueError("entity IDs must be nonempty")
    if any(not isfinite(value) for value in scores.values()):
        raise ValueError("scores must be finite")
    ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    ranks = {}
    prior_score = None
    current_rank = 0
    for position, (entity, score) in enumerate(ordered, start=1):
        if prior_score is None or score != prior_score:
            current_rank = position
        ranks[entity] = current_rank
        prior_score = score
    return ranks

week_47 = competition_ranks({"north": 81, "south": 81,
                             "west": 59, "east": 47})
assert week_47 == {"north": 1, "south": 1, "west": 3, "east": 4}''',
        "cost": "Ranking N entities costs O(N log N) time and O(N) output space per period; connecting P periods takes O(PN) output storage for a fixed cohort. The code uses higher-score-first competition ranks and stable ID ordering only for reproducible output. It does not fill absent entities. Before rendering, validate that every period uses the same score definition and disclose whether the eligible set is fixed or variable.",
        "mistakes": ["Reading a one-place rise as a fixed-size improvement.", "Allowing a chart library to break ties arbitrarily.", "Assigning missing entities last place.", "Comparing periods with changing eligibility without labeling entrants and exits."],
        "drill": "Rank 47 service depots over six weeks with two ties and one new entrant. Reconcile every rank to its score and show how the entrant changes the apparent position of unchanged depots.",
        "related": [prefix + "paired-change-slope-and-dumbbell-charts", prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "accessible-color-and-text-alternatives", prefix + "chart-export-manifest-data-and-render-version"],
    },
    {
        "slug": "p-charts-varying-denominators-and-process-baselines",
        "title": "P charts: account for varying denominators before flagging a rate",
        "summary": "Use a declared baseline and period-specific limits for binomial proportions, then investigate signals without inventing causes.",
        "sections": [
            ("A rate needs its opportunity count", "A p chart follows a proportion such as defective shipments divided by inspected shipments. Forty-seven defects in 470 inspections and 47 in 4,700 do not carry the same sampling uncertainty. Plot the period denominator or put it in a table, and calculate limits from the baseline proportion using each period's sample size. [[data-visualization/aggregation-grain-and-denominator|Denominator discipline]] is the first check. Do not mix units such as orders and line items, or change the defect definition midway through the series."),
            ("Freeze the baseline before judging a new point", "Choose a stable historical interval and document excluded outages, policy changes and incomplete periods. Pool baseline defects over baseline opportunities for a center line. Calculating a fresh center from every newly flagged point can move the goalposts. A period beyond an approximate three-standard-error limit is a signal to investigate; it does not prove a specific cause. [[data-visualization/chart-annotations-event-windows-and-causal-claims|Event annotations]] should distinguish observed timing from causal evidence. A confirmed process change may justify a new baseline, but record where the old phase ends."),
            ("Know the approximation's limits", "The simple p-chart formula assumes independent, comparable Bernoulli opportunities and a fairly stable underlying probability. Correlated batches, rare events or extra variation can make the limits misleading. Tiny sample sizes produce wide limits; values must still stay between zero and one. If repeated points reveal more variation than the model allows, investigate the collection process or choose a method suited to overdispersion. [[data-visualization/uncertainty-and-small-sample-display|Small-sample displays]] help communicate why a large-looking percentage swing may be weak evidence. A control limit is not a target or a confidence interval for a business decision."),
            ("Explain the chart without color", "Show the center line, period-specific bounds, actual rate, numerator and denominator in the export. Mark flagged points with shape and text, not red alone. If a late-arriving batch changes a historical numerator, recompute the affected point and disclose the revision. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Provisional periods]] should be clearly separate from finalized ones. An accessible summary can state which periods crossed limits and which lacked enough data, while leaving the causal diagnosis to the investigation."),
        ],
        "code": '''from math import sqrt

def p_chart_rows(baseline: list[tuple[int, int]],
                 periods: list[tuple[str, int, int]]
                 ) -> list[tuple[str, float, float, float, bool]]:
    def valid(defects: int, inspected: int) -> bool:
        return (isinstance(defects, int) and isinstance(inspected, int)
                and inspected > 0 and 0 <= defects <= inspected)
    if not baseline or any(not valid(d, n) for d, n in baseline):
        raise ValueError("baseline requires valid defect counts")
    if any(not label or not valid(d, n) for label, d, n in periods):
        raise ValueError("period counts or labels are invalid")
    center = sum(d for d, _ in baseline) / sum(n for _, n in baseline)
    output = []
    for label, defects, inspected in periods:
        radius = 3 * sqrt(center * (1 - center) / inspected)
        lower, upper = max(0.0, center - radius), min(1.0, center + radius)
        rate = defects / inspected
        output.append((label, rate, lower, upper, rate < lower or rate > upper))
    return output

baseline = [(47, 470), (59, 590), (81, 810)]
signals = p_chart_rows(baseline, [("week-47", 47, 470),
                                  ("week-48", 3, 470)])
assert round(signals[0][1], 4) == 0.1
assert signals[1][-1] is True''',
        "cost": "For B baseline periods and P plotted periods, this calculation takes O(B+P) time and O(P) output space. The three-standard-error limits are an approximation under an independent binomial model; the code does not test independence, estimate overdispersion or infer a cause. A production pipeline should version the baseline and defect definition, enforce finalized counts, and show denominator size with every point.",
        "mistakes": ["Comparing percentages while concealing sharply different sample sizes.", "Recomputing the baseline after every flagged period.", "Calling a control limit a business target.", "Treating a signal as proof of the annotated event's effect."],
        "drill": "Track 59 weekly inspection proportions with variable sample sizes. Freeze a baseline, flag points beyond their own limits and investigate a week whose rate is high but denominator is small.",
        "related": [prefix + "aggregation-grain-and-denominator", prefix + "uncertainty-and-small-sample-display", prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "chart-annotations-event-windows-and-causal-claims"],
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
        "featured": False, "sort_order": 8733 + offset, "status": "published",
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
    for start, end, heading in ((0, 2, "Individual marks and complete days"),
                                (2, 5, "Profiles, ranks and process limits")):
        targets = new_paths[start:end]
        row["data"]["modules"].append({"title": heading, "lessons": targets})
        row["body"] += f'<h2>{heading}</h2><ul>' + ''.join(
            f'<li>{link(target)}</li>' for target in targets) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "scatterplot-overplotting-density-and-sampling-bias": [new_paths[0]],
    prefix + "box-violin-and-kde-bandwidth-for-group-comparisons": [new_paths[0]],
    prefix + "heatmap-missing-cells-and-color-domain": [new_paths[1]],
    prefix + "time-series-gaps-calendars-and-provisional-periods": [new_paths[1], new_paths[3], new_paths[4]],
    prefix + "scale-baseline-and-axis-integrity": [new_paths[2]],
    prefix + "linked-filters-cohort-denominators-and-selection-state": [new_paths[2]],
    prefix + "paired-change-slope-and-dumbbell-charts": [new_paths[3]],
    prefix + "aggregation-grain-and-denominator": [new_paths[4]],
    prefix + "uncertainty-and-small-sample-display": [new_paths[4]],
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
