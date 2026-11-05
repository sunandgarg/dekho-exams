"""Add original forecasting prompt lessons, a review project, and a quiz."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
lookup = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
subject_root = "prompt-engineering/prompt-engineering"
applications = "prompt-engineering/applications"
production = "prompt-engineering/production"
projects = "prompt-engineering/projects"
quizzes = "prompt-engineering/quizzes"
project_path = "prompt-engineering/aster-kit-demand-forecast-review-project"
quiz_path = "quizzes/prompt-engineering-forecast-review"

specs = [
    dict(slug="forecast-prompt-target-horizon-and-grain", title="Forecast prompts: define target, horizon, and time grain", section=applications,
         summary="Specify exactly what quantity is predicted and when it becomes final.",
         definition="A forecasting prompt needs a target with units, entity key, time grain, forecast origin, horizon, and data-finalization rule. A request for 'next week's demand' is ambiguous if the source records orders by local day but the planner buys kits by depot-week. The application should convert timestamps to the agreed depot calendar, aggregate once, and provide a typed series. The model can explain the contract or flag a missing field; it should not improvise the calendar boundary. Preserve whether the target is submitted orders, fulfilled orders, or consumed stock. Those measures answer different operating questions.",
         case="Aster Repair plans weekly replacement-kit inventory for depot D-47. Each week runs Monday 00:00 through the next Monday 00:00 in the depot's local time zone. The target is fulfilled kits, not submitted requests. At the Sunday 18:00 planning origin, the current week has not finished, so the next complete week is the forecast target. A prompt that treats Sunday's partial count as a full week will understate demand. The contract marks unfinished periods as partial and excludes them from a full-week baseline.",
         sample="Entity: depot D-47\nTarget: fulfilled replacement kits, count\nGrain: depot-local Monday-to-Monday week\nOrigin: Sunday 18:00 local\nHorizon: next complete week\nCurrent week: partial, not a completed observation",
         cost="Converting and aggregating N event records by entity and local week is O(N) expected time with a keyed map and O(W) storage for W resulting weeks. Calendar conversion deserves an explicit test near time-zone changes; one wrong boundary can alter several weekly totals. Keep the source event count and aggregation version beside the series so an analyst can reproduce the target before debating models.",
         mistakes=["Do not mix submitted orders with fulfilled kits.", "Do not treat a partial week as a complete observation.", "Do not leave the depot calendar implicit."],
         related=["prompt-engineering/dataset-intake-column-contract", "prompt-engineering/locale-formatting-structured-values"]),
    dict(slug="forecast-prompt-as-of-input-and-future-feature-gate", title="Forecast prompts: enforce the as-of data boundary", section=applications,
         summary="Reject features that were unavailable when the forecast was issued.",
         definition="Every input feature has an event time and an availability time. A historical backtest must use only values that would have been available at its forecast origin, including revisions, delayed reports, and planned events. Future calendar dates may be known in advance; future realized sales or weather are not. A prompt that sees the final corrected table may appear accurate while depending on hindsight. The data pipeline should build an as-of snapshot for each origin, then pass the model a manifest of allowed series and known-future fields. Unknown inputs belong in a scenario, not a factual forecast feature.",
         case="Aster's operations table includes a stockout adjustment entered three days after a week ended. The revised fulfilled count is suitable for a later report, but it was unavailable to the planner at that week's Sunday forecast origin. A future promotion is approved only on Tuesday, after that origin. The backtest excludes both from the earlier input snapshot. A model-produced narrative that cites Tuesday's approval as if the Sunday planner knew it fails the as-of check even if its numeric forecast happens to be close.",
         sample="Forecast origin: Sunday 18:00 local\nHistorical revision posted Wednesday: unavailable at origin\nPromotion approved Tuesday: unavailable at origin\nCalendar week boundary: known in advance\nBacktest input: origin-specific snapshot only",
         cost="Building N origin snapshots from an event-sourced store can be O(N log N) for indexed as-of lookups, or more if each snapshot scans the full history. Cache snapshots by origin and data version without letting newer revisions overwrite old views. The extra storage buys an honest replay. Prompt wording alone cannot repair leakage if the input table was assembled with future values.",
         mistakes=["Do not use the latest corrected table to replay an older forecast without an as-of view.", "Do not call an unapproved future promotion a known feature.", "Do not judge leakage solely by whether a final number looks plausible."],
         related=["prompt-engineering/evaluation-data-leakage", "prompt-engineering/time-sensitive-research-contract"]),
    dict(slug="forecast-prompt-missing-weeks-and-stockout-censoring", title="Forecast prompts: distinguish missing weeks from zero demand", section=applications,
         summary="Separate absent records, true zeros, and censored fulfilled demand.",
         definition="A time series with gaps must not silently fill every missing period with zero. A missing row can mean an ingest failure, a closed depot, or no activity; each has a different effect on a forecast. Fulfilled-kit counts can also be censored by stockouts: 32 fulfilled kits do not prove only 32 were wanted if the depot ran out. Pass explicit status fields for missingness, closure, and stock availability, and require the model to list unresolved periods before making a numeric recommendation. A deterministic data check should reject duplicate entity-week keys and impossible negative counts.",
         case="Depot D-47 has no row for one week because a scanner export failed. Another week records zero fulfilled kits during a scheduled closure. A third shows 32 kits fulfilled after inventory reached zero on Thursday. Filling the first with zero would invent a collapse; treating the third as unbounded true demand would pretend the missing requests were measured. The prompt keeps three distinct statuses. A planner may use the closure week for calendar context, but holds the scanner gap and stockout week for review or explicit sensitivity analysis.",
         sample="Week A: missing export -> unknown count\nWeek B: scheduled closure -> observed zero fulfilled\nWeek C: 32 fulfilled, stockout Thursday -> demand censored\nNegative count or duplicate depot-week key -> reject",
         cost="Checking N weekly rows for gaps, duplicates, and invalid values is O(N) expected time with a set. Reconstructing stockout-adjusted demand needs extra evidence and may remain impossible, so it should not be invented in the prompt. Excluding uncertain weeks can reduce training data; the trade-off must be visible in the model evaluation and in the final recommendation.",
         mistakes=["Do not convert an absent export into zero demand.", "Do not equate stockout-limited fulfilment with unconstrained demand.", "Do not hide excluded weeks from the backtest record."],
         related=["prompt-engineering/dataset-intake-column-contract", "prompt-engineering/aggregate-denominator-reconciliation"]),
    dict(slug="forecast-prompt-baseline-and-rolling-origin-test", title="Forecast prompts: compare against a rolling baseline", section=production,
         summary="Evaluate actual forecasts at the intended horizon without shuffling time.",
         definition="A forecast should be compared with a simple baseline using the same origins, horizon, eligible rows, and error measure. Rolling-origin tests train or select information only through each origin, then score a later period. State whether the score is mean absolute error, signed error, or another measure and why that measure matches the decision. Keep per-origin errors, not just one average; a candidate that improves the average but fails during busy weeks may be unusable. The language model may explain results, while a deterministic evaluator calculates them.",
         case="Aster holds out four completed weeks with actual fulfilled counts 42, 47, 45, and 50. A prior-week baseline predicts 40, 42, 47, and 45; its absolute errors are 2, 5, 2, and 5, giving a mean absolute error of 3.5 kits. A candidate predicts 43, 46, 46, and 49; each absolute error is 1, giving mean absolute error 1.0. These fictional results support further review of the candidate, not a guarantee about the next week. Each prediction must have been frozen at its own origin.",
         sample="Actual:    42, 47, 45, 50\nBaseline:  40, 42, 47, 45 -> errors 2, 5, 2, 5 -> MAE 3.5\nCandidate: 43, 46, 46, 49 -> errors 1, 1, 1, 1 -> MAE 1.0\nSame four origins and one-week horizon",
         cost="Scoring F frozen forecasts is O(F) time and O(1) memory when streamed. Training a new model for each origin can cost much more than scoring, so choose a realistic evaluation window and record compute cost. Do not compare a candidate trained on later revisions with a baseline generated from earlier snapshots. The clean baseline makes extra model complexity earn its place.",
         mistakes=["Do not shuffle weeks across training and evaluation.", "Do not compare methods at different horizons or origins.", "Do not let the model calculate an unverified average from prose alone."],
         related=["prompt-engineering/evaluation-slice-design", "prompt-engineering/deterministic-calculation-gates"]),
    dict(slug="forecast-prompt-scenario-assumption-ledger", title="Forecast prompts: keep scenarios separate from predictions", section=production,
         summary="Label what changes under each assumption and who approved it.",
         definition="A scenario is a conditional calculation, not an observed future. List each adjustable driver with value, units, owner, approval status, and time window. Start from a frozen baseline forecast, apply only approved and measurable assumptions, and show the resulting delta. If a driver has no defensible effect size, describe the direction of concern without fabricating a precise adjustment. Scenarios can be useful for capacity planning even when their probabilities are unknown, but the prompt must not mix a worst case with an expected-value forecast or silently double-count overlapping changes.",
         case="The Aster baseline for next week is 54 kits. Marketing proposes a depot promotion that might add eight kits, but it has not been approved. The model must report the 54-kit baseline separately from a conditional 62-kit promotion scenario. A supplier delay could reduce available stock, not necessarily change customer demand; that belongs in the inventory decision rather than being subtracted from demand. The planner sees which assumptions are unapproved and which quantities are merely planning inputs.",
         sample="Baseline forecast: 54 kits\nPromotion scenario: +8 kits if approved -> 62 kits\nApproval: pending, not in baseline\nSupplier delay: stock constraint, not demand reduction\nScenario probability: unknown",
         cost="For S independent scenarios and D drivers, a direct review is O(SD); interacting drivers may require a more careful model. Keep the ledger short and traceable, since long lists of speculative adjustments can outgrow the signal in the baseline. A conditional scenario helps a decision only when its assumptions can be checked before inventory is committed.",
         mistakes=["Do not report 62 kits as the baseline while promotion approval is pending.", "Do not subtract a stock shortage from customer demand.", "Do not assign a probability to a scenario without evidence."],
         related=["prompt-engineering/architecture-capacity-units-and-headroom-check", "prompt-engineering/research-synthesis-release-and-reproduction-gate"]),
    dict(slug="forecast-prompt-interval-coverage-and-calibration", title="Forecast prompts: label intervals and check coverage", section=production,
         summary="Separate a point estimate from an empirically checked uncertainty range.",
         definition="A point forecast alone conceals uncertainty relevant to inventory. If a method produces an interval, state its intended coverage, construction version, horizon, and eligible backtest cases; then measure how often later actuals fell inside it. A prompt must not invent an '80% confidence' label from the width of a hand-drawn range. Coverage on a small history is descriptive and may shift after a process change. Examine whether misses concentrate in high-demand weeks, since average coverage can hide the cases most expensive for the planner.",
         case="Aster's interval method had 20 eligible one-week backtest cases; 16 actual counts landed within their frozen intervals. Observed coverage is 16/20, or 80%, over that sample. For the next week it emits a point estimate of 54 and an interval from 45 to 65 kits. Depot stock capacity is 60, so the upper end crosses the current capacity. The memo states the interval's empirical history and the capacity exposure; it does not call the next week's outcome 80% certain or imply that 20 cases establish permanent calibration.",
         sample="Backtest: 16 covered / 20 eligible = 80% observed coverage\nNext-week point: 54 kits\nNext-week interval: 45-65 kits\nCurrent capacity: 60 kits\nUpper interval exceeds capacity by 5 kits",
         cost="Coverage scoring across F frozen intervals is O(F) time. Calibration by horizon or demand band needs enough cases per slice; sparse slices should be labeled untested rather than assigned a misleading percentage. Wider intervals may improve coverage while making inventory decisions less specific. Report width and miss severity beside coverage, and keep the interval method version with the release packet.",
         mistakes=["Do not call an arbitrary range a calibrated interval.", "Do not hide that only 20 cases support the observed coverage.", "Do not treat an interval boundary as a guaranteed maximum."],
         related=["prompt-engineering/chart-prompt-accessibility-and-render-review", "prompt-engineering/aggregate-denominator-reconciliation"]),
    dict(slug="forecast-prompt-inventory-decision-and-release-gate", title="Forecast prompts: gate inventory recommendations on evidence", section=production,
         summary="Tie forecast quality and uncertainty to a reversible stock decision.",
         definition="A forecast is an input to a decision, not an automatic purchase order. The recommendation should combine the frozen forecast, current usable stock, replenishment lead time, service target, capacity, and the cost of shortage or excess. If any decisive field is missing, ask for it or issue a bounded analysis rather than a quantity to order. Require a human owner to approve any external stock movement. Record which model and data snapshot supported the recommendation, then compare realized demand with the forecast after the period closes; a prompt should not claim success from a plan alone.",
         case="Aster's point estimate is 54 kits and its one-week interval extends to 65, above the depot's 60-kit capacity. The planner cannot simply order 65: usable stock, inbound shipments, storage constraints, and lead time still need verification. A draft memo flags the five-kit exposure above capacity and offers options such as earlier replenishment or a nearby depot transfer for human review. The purchase action remains pending. If a late stock correction changes the usable quantity, the recommendation is recomputed before approval.",
         sample="Forecast bundle: origin, target, data version, model version\nPoint 54; interval 45-65; capacity 60\nUnknown: usable stock and inbound receipt timing\nAction: hold purchase quantity; request missing inputs\nAfter close: record actual and decision outcome",
         cost="Combining forecasts with inventory records is O(D) for D depot-item decisions once the records are indexed, but the real cost lies in checking stale stock and external effects. A saved release packet allows later comparison between forecast error and decision error. Approval and receipt reconciliation add latency; they prevent a fluent explanation from becoming an unauthorized purchase or transfer.",
         mistakes=["Do not turn a point forecast directly into a purchase quantity.", "Do not order beyond capacity without reviewing alternatives.", "Do not mark the recommendation successful before actual demand and stock outcomes are known."],
         related=["prompt-engineering/side-effect-receipt-reconciliation", "prompt-engineering/architecture-capacity-units-and-headroom-check"]),
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]) & lookup.keys()
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: review Aster depot kit forecasts"
titles[quiz_path] = "Forecast prompt decisions"


def link(path):
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(selected):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(selected)) + "</ul>"


def related(selected):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(selected)]


def article(path, title, summary, body, section, order, connections, kind="tutorial"):
    row = copy.deepcopy(lookup["prompt-engineering/evaluation-slice-design"])
    subjects = {applications: "prompt-engineering-applications", production: "prompt-engineering-production", projects: "prompt-engineering-project"}
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path, title=title,
               summary=summary, body=body, subject=subjects[section], difficulty="Advanced",
               tags=["prompt engineering", "forecasting"], sort_order=31700 + order,
               status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"].update(kind=kind, reading_minutes=11 if kind == "tutorial" else 18,
                       author_path="authors/aitrove-editorial", subject_root=subject_root,
                       section_path=section, content_format="html", seo_ready=True,
                       related=related(connections))
    return row


new_rows = []
for index, (path, spec) in enumerate(zip(paths, specs)):
    connections = [spec["section"], subject_root] + spec["related"] + [other for other in paths if other != path] + [project_path, quiz_path]
    body = ("<p>" + html.escape(spec["definition"]) + "</p>"
            + "<h2>Operational case</h2><p>" + html.escape(spec["case"]) + "</p>"
            + '<pre><code class="language-text">' + html.escape(spec["sample"], quote=False) + "</code></pre>"
            + "<h2>Performance and review cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
            + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in spec["mistakes"]) + "</ul>"
            + "<h2>Connected lessons</h2>" + links(connections))
    new_rows.append(article(path, spec["title"], spec["summary"], body, spec["section"], index * 10, connections))

project_connections = paths + ["prompt-engineering/deterministic-calculation-gates", "prompt-engineering/evaluation-data-leakage", quiz_path]
project_body = (
    "<p>Review a fictional one-week replacement-kit forecast for Aster Repair depot D-47. Start by defining fulfilled kits as the target, a depot-local Monday-to-Monday week as the grain, and Sunday 18:00 as the forecast origin. A partial current week is not a completed observation. The task is to prepare a human-review packet; no purchase or transfer is authorized by this exercise.</p>"
    "<h2>Rebuild an honest backtest</h2><p>Use origin-specific snapshots. A correction posted Wednesday and a promotion approved Tuesday were unavailable at the earlier Sunday origin. Mark a scanner-export gap as unknown, a scheduled-closure week as an observed zero, and a 32-kit stockout week as censored fulfilled demand. Four held-out actuals are 42, 47, 45, and 50. The prior-week baseline predicts 40, 42, 47, and 45, producing mean absolute error 3.5. A candidate predicts 43, 46, 46, and 49, producing mean absolute error 1.0. Both methods must use the same one-week origins and eligible periods.</p>"
    "<h2>Keep scenarios and decisions separate</h2><p>The candidate's next-week point forecast is 54 kits. A promotion scenario adds eight only if that unapproved event occurs, yielding 62; it is not the baseline. Sixteen of 20 frozen interval backtests covered the actual, an observed 80% for that small set. The current interval is 45 to 65 kits, while storage capacity is 60. Ask for usable stock, inbound receipt timing, and lead time before proposing an order quantity. The decision memo should show the five-kit interval exposure above capacity without treating the interval as a hard maximum.</p>"
    '<pre><code class="language-text">Baseline backtest errors: 2, 5, 2, 5 -> MAE 3.5 kits\nCandidate backtest errors: 1, 1, 1, 1 -> MAE 1.0 kit\nPoint: 54 kits; conditional promotion: 62 kits\nInterval: 45-65 kits; observed coverage: 16/20\nCapacity: 60 kits; usable stock and inbound timing: unknown\nOrder quantity: pending review</code></pre>'
    "<h2>Performance and review cost</h2><p>Aggregate N events in O(N) expected time, score F frozen forecasts in O(F), and check interval coverage in O(F). Model fitting and data reconstruction may dominate those arithmetic checks. The review packet must include the as-of snapshot, rejected periods, target calendar, baseline and candidate errors, interval method, scenario approvals, and decision owner. A fluent forecast summary without those records is not reproducible.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not use a partial week or a future correction as past data.</li><li>Do not fill an ingest gap with zero.</li><li>Do not present the conditional 62-kit scenario as the 54-kit baseline.</li><li>Do not order from the point forecast while stock and lead time are unknown.</li></ul>"
    "<h2>Related lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Reconcile time boundaries, rolling errors, scenario assumptions, and stock decisions.", project_body, projects, 80, project_connections, "project"))

questions = [
    ("What is the target for D-47's kit plan?", "Fulfilled kits for the next complete depot-local week", "Submitted requests without a time grain", "The current partial week's count", "Target, unit, entity, and grain must be fixed first."),
    ("May a Wednesday correction enter Sunday's historical forecast input?", "No, it was unavailable at the origin", "Yes, it improves backtest accuracy", "Yes, if the model requests it", "An as-of replay uses only information available then."),
    ("How should a scanner-export gap be represented?", "Unknown count pending review", "A confirmed zero", "A guaranteed stockout", "Missing records and observed zeros are different."),
    ("What does the 32-kit stockout week prove?", "At least 32 were fulfilled; unconstrained demand is unknown", "Demand was exactly 32", "All later weeks will be 32", "Fulfilment can be censored by missing stock."),
    ("What is the prior-week baseline MAE for errors 2, 5, 2, 5?", "3.5 kits", "14 kits per week", "1.0 kit", "The four absolute errors sum to 14 and average to 3.5."),
    ("What makes the baseline and candidate comparison fair?", "Same origins, horizon, eligible periods, and metric", "A later data snapshot only for the candidate", "Different forecast horizons", "Both methods need the same replay conditions."),
    ("How should the pending promotion be shown?", "As a conditional 62-kit scenario separate from 54", "As a confirmed 62-kit baseline", "As a reduction in stock capacity", "An unapproved driver is not observed future demand."),
    ("What is observed interval coverage when 16 of 20 cases contain actuals?", "80% over those 20 cases", "A guarantee for next week", "16% of all future weeks", "Coverage is a retrospective sample measure."),
    ("What does a 45-65 interval imply with 60-kit capacity?", "Its upper end exceeds capacity by five kits", "Demand can never exceed 65", "Order 65 immediately", "The interval exposes a planning constraint, not an authorized order."),
    ("Which field is still needed before an order quantity?", "Usable stock and inbound receipt timing", "Only a polished chart", "A model persona", "The decision depends on inventory position and replenishment timing."),
    ("Who approves an external kit purchase?", "A human owner after reviewing the release packet", "The forecasting prompt by default", "The interval method", "A forecast is evidence for a decision, not purchase authority."),
    ("When can Aster assess the forecast and decision outcome?", "After the target week closes and actuals are recorded", "When the prompt finishes drafting", "Before any stock check", "Outcome evaluation needs realized demand and stock results."),
]
quiz = copy.deepcopy(lookup["quizzes/prompt-engineering-qualitative-user-research"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Test target definitions, as-of inputs, rolling errors, intervals, and stock authority.",
            body="<p>Choose the forecast decision supported by the frozen inputs and review packet.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, production, quizzes]),
            sort_order=31790, status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"].update(subject_root=subject_root, section_path=quizzes, content_format="html",
                    author_path="authors/aitrove-editorial", seo_ready=True, duration_minutes=12,
                    related=related(paths + [project_path]),
                    questions=[{"prompt": prompt,
                                "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                "answer": (-index) % 3, "explanation": explanation}
                               for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)])
new_rows.append(quiz)

for hub_path, selected, title, summary in [
    (applications, paths[:3], "Forecast input contracts", "Define the series and reject future or ambiguous data."),
    (production, paths[3:], "Forecast evaluation and decisions", "Test baselines, distinguish scenarios, check intervals, and gate stock actions."),
    (projects, [project_path], "Aster kit forecast review", "Apply the full forecast review to a fictional depot."),
    (quizzes, [quiz_path], "Forecast decisions", "Test temporal evidence and inventory boundaries."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

lookup[subject_root]["body"] += "<h2>Forecast review prompts</h2><p>Trace time-series evidence from target definition to a bounded stock decision.</p>" + links(paths + [project_path, quiz_path])
lookup[subject_root]["updated_at"] = stamp

backlinks = {
    "prompt-engineering/dataset-intake-column-contract": paths[0],
    "prompt-engineering/evaluation-data-leakage": paths[1],
    "prompt-engineering/aggregate-denominator-reconciliation": paths[2],
    "prompt-engineering/evaluation-slice-design": paths[3],
    "prompt-engineering/architecture-capacity-units-and-headroom-check": paths[4],
    "prompt-engineering/deterministic-calculation-gates": paths[5],
    "prompt-engineering/side-effect-receipt-reconciliation": paths[6],
}
for old_path, new_path in backlinks.items():
    entry = lookup[old_path]
    entry["body"] += "<p><strong>Continue with:</strong> " + link(new_path) + ".</p>"
    entry["data"]["related"] = related([item["path"] for item in entry["data"].get("related", [])] + [new_path])
    entry["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newLessons": len(specs), "newProjects": 1, "newQuizzes": 1,
                  "newPaths": [entry["path"] for entry in new_rows]}))
