"""Add original interrupted time-series Data Science lessons."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
slugs = (
    'interrupted-series-outcome-clock-and-data-contract',
    'segmented-regression-level-and-slope-change',
    'controlled-interrupted-series-comparison',
    'interrupted-series-seasonality-and-residual-dependence',
    'interrupted-series-transition-and-lag-sensitivity',
    'interrupted-series-policy-review-project',
)
new_paths = {'data-science/' + slug for slug in slugs}
rows = [row for row in rows if row['path'] not in new_paths]
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
lessons = []

def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='data-science/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))

add('interrupted-series-outcome-clock-and-data-contract',
    'Interrupted-series outcome clock and data contract',
    'An interrupted time-series study needs a fixed intervention date, repeated outcomes on a stable measurement scale, and explicit treatment of preparation and transition periods.', [
    ('Start with the operational event', 'A service organization introduces a routing rule across its entire queue in September. The announcement happened in July, staff training began in August, and the rule took effect on September 1. Those are three distinct dates. If staff alter behavior during training, August is not an untouched baseline month. Freeze the event ledger before looking for a favorable break. [[data-science/branch-month-panel-and-rollout-clock|The branch rollout clock]] handles a related timing problem when adoption differs by branch.'),
    ('Specify the outcome at each time point', 'Use a monthly deadline-breach rate: eligible tickets breaching the deadline divided by all eligible tickets closed during that month. Retain both numerator and denominator, the inclusion rule, time zone, close-date convention and any ticket migration. A jump in the rate may follow a denominator change rather than the routing rule. Monthly counts also vary; a month with forty tickets carries different measurement uncertainty from one with four thousand.'),
    ('Demand enough history to interrogate the model', 'A line through two pre-policy points always fits, but tells little about seasonality or a changing slope. Inspect several complete cycles if the operation has an annual pattern. Record missing months rather than silently connecting adjacent observations. The code checks a complete monthly grid, unique month keys, positive denominators and numerator bounds. It does not claim that a given number of observations guarantees a credible effect.'),
    ('Separate the analytic windows', 'Mark clearly untreated months, possible anticipation months, transition months and stable post-policy months. Do not relabel the last pre-month after seeing a sharp dip or rise. If the rule rolled out over several weeks, a simple September step may misstate exposure. [[data-science/interrupted-series-transition-and-lag-sensitivity|Transition sensitivity]] makes that uncertainty explicit. The resulting series is the input to [[data-science/segmented-regression-level-and-slope-change|segmented estimation]].'),
    ('State the missing counterfactual', 'The pre-policy trend is used to predict what would have happened after September without the rule. That extrapolation can fail if demand, staffing, holidays, product mix or the recording system changed at the same time. The time-series structure gives more information than a simple before/after average, but it does not itself isolate the policy. A suitable unaffected comparison series can improve the design, as described in [[data-science/controlled-interrupted-series-comparison|the controlled-series lesson]].')],
    '''def audit_monthly_outcomes(monthly_rows, first_month, last_month):
    expected = set(range(first_month, last_month + 1))
    seen = set()
    rates = {}
    for month, breaches, eligible in monthly_rows:
        if month in seen or month not in expected:
            raise ValueError("duplicate or out-of-window month")
        if eligible <= 0 or breaches < 0 or breaches > eligible:
            raise ValueError("invalid rate components")
        seen.add(month)
        rates[month] = breaches / eligible
    if seen != expected:
        raise ValueError("missing months: " + str(sorted(expected - seen)))
    return [rates[month] for month in sorted(expected)]

queue_rows = [(month, 17 + month, 100 + 2 * month)
              for month in range(1, 15)]
breach_rates = audit_monthly_outcomes(queue_rows, 1, 14)
assert len(breach_rates) == 14
assert abs(breach_rates[0] - 18 / 102) < 1e-12''',
    'For T months, dictionary-backed validation is O(T) expected time and O(T) space. A complete data contract also needs historical definition and intervention logs, which cannot be inferred from the numeric rate alone.',
    ['Do not choose the intervention month after viewing the outcome break.', 'Do not treat training and launch dates as interchangeable.', 'Do not calculate rates without preserving their numerators and denominators.'],
    ['data-science/segmented-regression-level-and-slope-change','data-science/controlled-interrupted-series-comparison','data-science/interrupted-series-transition-and-lag-sensitivity','data-science/interrupted-series-policy-review-project'])

add('segmented-regression-level-and-slope-change',
    'Segmented regression for level and slope changes',
    'A segmented time-series model distinguishes an immediate level shift at intervention from a change in the rate of change afterward.', [
    ('Define the two quantities', 'Suppose the breach rate was rising by half a percentage point per month before a September routing policy. At the first stable post-policy month, the observed series may sit below the projection of that old trend. That vertical difference is a level shift. If the post-policy path then falls faster or rises more slowly, its slope differs too. Report both in rate points per month, plus the modeled gap at an agreed horizon. [[data-science/interrupted-series-outcome-clock-and-data-contract|The outcome clock]] fixes which month is first treated.'),
    ('Fit on the declared windows', 'The teaching implementation fits a straight line separately to pre- and post-policy points and evaluates both lines at the first post-policy time index. Subtracting the extrapolated pre line from the post line there yields a level contrast; subtracting slopes yields a slope contrast. It is algebraically equivalent to a four-parameter segmented line on complete windows without extra covariates. It does not calculate uncertainty or handle autocorrelated errors.'),
    ('Do not confuse a slope with a total effect', 'If the level falls by five rate points but the post slope is one point per month higher than the pre slope, the modeled gap narrows over time. At horizon h, the gap is level change plus h times slope change when h counts months since the first post point. State that horizon. An immediate improvement may disappear, and a small first-month change can accumulate into a large later gap.'),
    ('Check extrapolation before interpretation', 'A linear pretrend may be a poor counterfactual if the rate approaches a floor, varies with season, or changes after an unrelated staffing event. Inspect residuals, ticket denominators and outliers rather than reporting only a coefficient. With very few post months, the post slope is unstable. [[data-science/interrupted-series-seasonality-and-residual-dependence|Time dependence and seasonality]] affect uncertainty and model shape.'),
    ('Keep the causal claim conditional', 'The calculation establishes a break relative to a linear continuation, not why the break happened. A concurrent policy could create it. A comparison series subject to the same external shocks may help, but only if it did not receive the routing rule or its spillovers. [[data-science/controlled-interrupted-series-comparison|The controlled design]] compares breaks rather than raw levels.')],
    '''def fit_line(points):
    if len(points) < 3:
        raise ValueError("need at least three points per segment")
    times = [month for month, _ in points]
    values = [rate for _, rate in points]
    mean_time = sum(times) / len(times)
    mean_rate = sum(values) / len(values)
    spread = sum((month - mean_time) ** 2 for month in times)
    if spread == 0:
        raise ValueError("no time variation")
    slope = sum((month - mean_time) * (rate - mean_rate)
                for month, rate in points) / spread
    intercept = mean_rate - slope * mean_time
    return intercept, slope

def segmented_change(monthly_rates, first_post):
    pre = [(month, rate) for month, rate in monthly_rates.items()
           if month < first_post]
    post = [(month, rate) for month, rate in monthly_rates.items()
            if month >= first_post]
    pre_intercept, pre_slope = fit_line(pre)
    post_intercept, post_slope = fit_line(post)
    level = (post_intercept + post_slope * first_post -
             (pre_intercept + pre_slope * first_post))
    return level, post_slope - pre_slope

breach_rates = {month: .17 + .005 * month for month in range(1, 9)}
breach_rates.update({month: .155 + .002 * (month - 9)
                     for month in range(9, 15)})
level_shift, slope_shift = segmented_change(breach_rates, 9)
assert abs(level_shift - (-.06)) < 1e-12
assert abs(slope_shift - (-.003)) < 1e-12''',
    'With T monthly observations, two ordinary least-squares line fits cost O(T) time and O(T) space in this implementation because it materializes two lists. A production regression with seasonal terms and dependence-aware uncertainty has additional solver and diagnostic costs.',
    ['Do not report a post slope alone as the policy effect.', 'Do not read a fitted break as causal without checking simultaneous events.', 'Do not use ordinary independent-error intervals when residuals are serially dependent.'],
    ['data-science/interrupted-series-outcome-clock-and-data-contract','data-science/controlled-interrupted-series-comparison','data-science/interrupted-series-seasonality-and-residual-dependence','data-science/interrupted-series-policy-review-project'])

add('controlled-interrupted-series-comparison',
    'Controlled interrupted time series with a comparison series',
    'A controlled interrupted series subtracts the comparison series’ level and slope breaks from the treated series’ breaks at the same intervention date.', [
    ('Choose a comparison that shares shocks', 'North’s support queue receives the September routing rule; a separate South queue does not. Both face the same billing release and seasonal ticket surge. If South is measured the same way and remains unexposed, its trajectory may reveal changes that a North-only model would wrongly assign to the rule. Selection is a design argument, not a correlation contest. A South queue with shared overflow routing could receive an indirect effect and fail as a control. [[data-science/spillover-aware-comparison-pool|The spillover lesson]] screens that risk.'),
    ('Subtract changes, not levels', 'Fit or derive a level and slope break for North and South at the same September cutoff. The controlled level contrast is North’s level change minus South’s level change; the controlled slope contrast is the corresponding difference in slope changes. A constant difference in baseline rates does not by itself invalidate this contrast. The harder question is whether the untreated breaks would have been comparable in the absence of the policy.'),
    ('Check the earlier relationship', 'Plot the treated-minus-control rate difference over the pre-policy months. A drifting difference means the two queues did not track in a simple way; a controlled segmented model can include group-specific pretrends, but extrapolation becomes more fragile. Check calendar alignment, denominators, case mix and prior policy changes. A comparison affected by a different concurrent policy may introduce bias instead of removing it. [[data-science/event-time-pretrend-and-support-audit|Pretrend audits]] provide complementary checks.'),
    ('Interpret the worked contrast', 'In the fixture, North’s own immediate break is -0.06 rate points and South’s is -0.02, producing a controlled level contrast of -0.04. North’s slope change is -0.003 per month and South’s is +0.001, producing a controlled slope contrast of -0.004 per month. The code performs the final contrast on estimated inputs; the actual line fits and their uncertainty must be done upstream. [[data-science/segmented-regression-level-and-slope-change|Segmented regression]] explains those inputs.'),
    ('Do not let a control create certainty', 'One control cannot guarantee shared counterfactual shocks. The two series may respond differently to holidays or ticket mix, and residual errors can be correlated within and across time. Report a clear comparison selection rule, all observed and modeled paths, and a sensitivity check with another eligible control where possible. [[data-science/interrupted-series-policy-review-project|The review project]] treats absent comparison support as a limitation rather than inventing a match.')],
    '''def controlled_break(treated_break, comparison_break):
    required = {"level", "slope"}
    if set(treated_break) != required or set(comparison_break) != required:
        raise ValueError("both fitted breaks need level and slope")
    return {measure: treated_break[measure] - comparison_break[measure]
            for measure in required}

treated = {"level": -.06, "slope": -.003}
comparison = {"level": -.02, "slope": .001}
net_break = controlled_break(treated, comparison)
assert abs(net_break["level"] - (-.04)) < 1e-12
assert abs(net_break["slope"] - (-.004)) < 1e-12

def gap_at_horizon(breaks, months_after_first_post):
    if months_after_first_post < 0:
        raise ValueError("negative horizon")
    return breaks["level"] + months_after_first_post * breaks["slope"]

assert abs(gap_at_horizon(net_break, 3) - (-.052)) < 1e-12''',
    'The final subtraction and horizon calculation are O(1) time and space. Fitting G group series over T observations costs at least O(G × T) data access; uncertainty estimation must respect serial dependence and any shared shocks.',
    ['Do not select a comparison using post-policy outcomes.', 'Do not use a queue indirectly exposed through shared routing as untreated.', 'Do not confuse a difference in baseline levels with a difference in breaks.'],
    ['data-science/segmented-regression-level-and-slope-change','data-science/spillover-aware-comparison-pool','data-science/interrupted-series-seasonality-and-residual-dependence','data-science/interrupted-series-policy-review-project'])

add('interrupted-series-seasonality-and-residual-dependence',
    'Seasonality and residual dependence in interrupted series',
    'Monthly interrupted-series residuals may retain seasonal structure or correlation across adjacent months, so model fit and uncertainty require checks beyond a visible policy break.', [
    ('Inspect residuals after fitting the policy terms', 'Subtract the fitted segmented path from each observed monthly rate and examine what remains. A run of positive residuals after the intervention can indicate a misspecified lag or trend. A yearly cycle remaining in residuals means the model has not captured seasonality. The code calculates descriptive lag correlations; it is not an automatic test of significance or a complete diagnostic. [[data-science/segmented-regression-level-and-slope-change|The segmented model]] supplies the fitted path.'),
    ('Separate repeated seasonal pattern from intervention timing', 'If the policy launches just before the annual peak, a step term may absorb the peak. Compare the same calendar months across years when enough history exists, and consider prespecified month effects or seasonal terms. With less than one full pre-policy cycle, the data cannot establish an annual pattern internally. Adding eleven month indicators to a short series can consume most of the information and make the level estimate unstable.'),
    ('Dependence changes uncertainty', 'Adjacent residuals can move together because staffing and workload persist. Ordinary regression standard errors that assume independent errors may then understate uncertainty. Depending on series length and residual structure, a model may use a specified error process or a dependence-aware covariance estimate. Choosing the correction after scanning for the smallest p-value defeats its purpose. The plain Python calculation here stops at flagging structure; it does not produce an interval.'),
    ('Check the outcome scale', 'A breach rate near zero or one has bounded support, while monthly breach counts depend on changing eligible-ticket volume. A linear rate model can predict outside the possible range. For very low event counts, a count or binomial model with an exposure denominator may better match the data. But a more complicated family does not fix an unmeasured concurrent event. [[data-science/interrupted-series-outcome-clock-and-data-contract|The data contract]] preserves both rate components.'),
    ('Report the diagnostics with the estimate', 'Include residual plots or sequences, lag definitions, coverage by calendar month and the final uncertainty method. A large lag correlation in twelve months is a prompt to inspect the series, not proof of a particular autoregressive model. Do not treat a corrected standard error as a correction for biased counterfactual trend. [[data-science/controlled-interrupted-series-comparison|A suitable comparison]] addresses a different weakness.')],
    '''from math import sqrt

def lag_correlation(residuals, lag):
    if lag <= 0 or len(residuals) - lag < 3:
        raise ValueError("lag has too few paired months")
    earlier = residuals[:-lag]
    later = residuals[lag:]
    mean_earlier = sum(earlier) / len(earlier)
    mean_later = sum(later) / len(later)
    numerator = sum((left - mean_earlier) * (right - mean_later)
                    for left, right in zip(earlier, later))
    left_energy = sum((value - mean_earlier) ** 2 for value in earlier)
    right_energy = sum((value - mean_later) ** 2 for value in later)
    if left_energy == 0 or right_energy == 0:
        raise ValueError("constant residual segment")
    return numerator / sqrt(left_energy * right_energy)

model_residuals = [((month % 12) - 5.5) / 1000
                   for month in range(36)]
annual_lag = lag_correlation(model_residuals, 12)
nearby_lag = lag_correlation(model_residuals, 1)
assert annual_lag > .99
assert -1 <= nearby_lag <= 1''',
    'For T months, one lag correlation is O(T) time and O(T) slice space. Checking L lags directly is O(L × T). Seasonal model estimation and dependence-aware uncertainty add model-specific costs; short series length, not computation, is often the limiting factor.',
    ['Do not infer independent errors from a plausible-looking fitted line.', 'Do not fit a full seasonal cycle with less than a cycle of baseline evidence and call it validated.', 'Do not treat adjusted uncertainty as a fix for a confounded intervention date.'],
    ['data-science/segmented-regression-level-and-slope-change','data-science/controlled-interrupted-series-comparison','data-science/interrupted-series-transition-and-lag-sensitivity','data-science/interrupted-series-policy-review-project'])

add('interrupted-series-transition-and-lag-sensitivity',
    'Transition windows and lag sensitivity for policy series',
    'A policy may be announced, trained, launched and adopted at different times; a lag sensitivity audit shows how the estimated post-policy gap changes under declared exposure windows.', [
    ('Map the actual adoption process', 'A routing rule is announced in July, taught in August and enabled in September. Staff may alter triage before the switch, and the queue may need two months to reach steady use. A model with a clean September step can be misleading. Define a clearly untreated window, one or more transition months, and a stable post-policy window from operational logs. [[data-science/interrupted-series-outcome-clock-and-data-contract|The clock lesson]] fixes these dates.'),
    ('Ask whether effect timing is plausible', 'An immediate level change implies an abrupt impact at the first treated observation. A gradual rollout may appear as a slope change or delayed level shift. If the outcome is measured at ticket closure, tickets opened before launch may close afterward and blur the boundary. The lag should follow the workflow and measurement delay, not just the month that produces the largest estimated benefit.'),
    ('Freeze a small set of alternatives', 'The fixture compares lags of zero, one and two months after the launch, treating the intervening months as transition rather than baseline. For each lag it averages the observed minus predicted untreated rate over the remaining stable post months. The resulting means can differ because the included months differ. They are descriptive sensitivity results; a full study should refit its declared model for each alternative and show uncertainty and fit.'),
    ('Preserve the denominator of every scenario', 'A two-month lag leaves fewer stable post months than a zero-month lag. Report that count alongside the mean gap. Do not compare a six-month estimate and a one-month estimate as though equally informed. If all post months are labeled transition, the effect is not estimable in the available follow-up. [[data-science/segmented-regression-level-and-slope-change|Segmented estimates]] also need enough points on each side to estimate a slope.'),
    ('Interpret disagreement rather than hiding it', 'If the sign reverses between plausible lag choices, investigate rollout logs, closure delay and unrelated events. If the gap begins before training, anticipation or pre-existing trend is possible. Stable signs over a few handpicked windows still do not establish causality; the same shared shock can affect every window. [[data-science/interrupted-series-policy-review-project|The review packet]] should retain each declared scenario and its exclusion rules.')],
    '''def post_gap_by_lag(observed_rate, untreated_prediction,
                        launch_month, candidate_lags):
    if set(observed_rate) != set(untreated_prediction):
        raise ValueError("observed and predicted months differ")
    results = {}
    for lag in candidate_lags:
        if lag < 0:
            raise ValueError("negative lag")
        stable_months = sorted(month for month in observed_rate
                               if month >= launch_month + lag)
        if not stable_months:
            raise ValueError("no stable post-policy months")
        gaps = [observed_rate[month] - untreated_prediction[month]
                for month in stable_months]
        results[lag] = {"months": len(gaps),
                        "mean_gap": sum(gaps) / len(gaps)}
    return results

observed = {9: .19, 10: .17, 11: .14, 12: .13, 13: .12}
prediction = {month: .20 for month in observed}
lag_audit = post_gap_by_lag(observed, prediction, 9, (0, 1, 2))
assert [lag_audit[lag]["months"] for lag in (0, 1, 2)] == [5, 4, 3]
assert lag_audit[2]["mean_gap"] < lag_audit[0]["mean_gap"]''',
    'For L lag scenarios and T available months, the direct scan costs O(L × T) time and O(T + L) transient/output space. Re-fitting a model for every lag costs more; the analytic limitation is shrinking post-period support.',
    ['Do not choose a lag solely because it maximizes the policy gap.', 'Do not count training months as clean baseline without an exposure argument.', 'Do not report a delayed estimate without its remaining post-month count.'],
    ['data-science/interrupted-series-outcome-clock-and-data-contract','data-science/segmented-regression-level-and-slope-change','data-science/interrupted-series-seasonality-and-residual-dependence','data-science/interrupted-series-policy-review-project'])

add('interrupted-series-policy-review-project',
    'Project: audit an interrupted policy series',
    'Build an interrupted-series review packet that separates a visible break from a defensible policy effect and records every timing, comparison and uncertainty decision.', [
    ('State the decision and missing path', 'A support team wants to know whether its September routing rule reduced deadline breaches through the following February. The needed counterfactual is the breach-rate path the queue would have followed without the rule. Create a one-page design brief naming the queue, ticket eligibility, launch and training dates, monthly numerator and denominator, and a policy-relevant horizon. Do this before modeling. [[data-science/interrupted-series-outcome-clock-and-data-contract|The clock and data contract]] is the first gate.'),
    ('Build two aligned series', 'Retain the treated monthly outcomes and, if available, an unaffected comparison queue measured by the same rule and calendar. Record why the comparison shares demand shocks yet avoids the routing rule and overflow. If no valid comparison exists, label the design single-series and make the concurrent-event limitation prominent. Keep both raw and modeled paths for inspection. [[data-science/controlled-interrupted-series-comparison|The controlled contrast]] must be defended, not merely calculated.'),
    ('Estimate and interrogate', 'Fit the declared segmented specification, report level and slope changes and calculate the predicted gap at the decision horizon. Inspect pretrend fit, residual runs, seasonal coverage and serial dependence. Use an uncertainty method suitable for the observed dependence; the simple code below checks packet completeness but does not fit regression or produce a valid interval. [[data-science/segmented-regression-level-and-slope-change|Level and slope]] and [[data-science/interrupted-series-seasonality-and-residual-dependence|residual diagnostics]] provide separate evidence.'),
    ('Preserve all timing scenarios', 'Use operational records to define anticipation and transition months. Repeat the planned analysis for credible zero-, one- and two-month lags and retain the post-month count for each. Record every concurrent staffing, billing or product event that could explain the same break. A favorable alternate window is not a reason to discard the preregistered one. [[data-science/interrupted-series-transition-and-lag-sensitivity|Lag sensitivity]] exposes the tradeoff between delay and follow-up.'),
    ('Issue a bounded recommendation', 'The final packet should show observed rates and denominators, fitted counterfactuals, level and slope contrasts, uncertainty, diagnostic failures and plausible alternate explanations. If the measurement changed at launch, the comparison is contaminated or all post months fall in transition, stop at a descriptive trend statement. A clean packet is reviewable evidence, not proof that every other cause has been eliminated. [[data-science/single-branch-policy-transfer-review-project|The transfer review]] addresses a separate question: whether a local effect can inform other branches.')],
    '''def interrupted_series_packet_gate(packet):
    required = {"event_ledger", "monthly_numerators", "monthly_denominators",
                "frozen_windows", "level_estimate", "slope_estimate",
                "residual_review", "concurrent_event_log", "lag_scenarios"}
    missing = sorted(required - set(packet))
    if missing:
        raise ValueError("missing packet items: " + ", ".join(missing))
    months = set(packet["monthly_numerators"])
    if months != set(packet["monthly_denominators"]):
        raise ValueError("numerator and denominator months differ")
    if not packet["lag_scenarios"]:
        raise ValueError("no timing sensitivity")
    if not all(packet["monthly_denominators"][month] > 0
               for month in months):
        raise ValueError("nonpositive denominator")
    return {"packet_complete": True, "months": len(months),
            "comparison_available": bool(packet.get("comparison_ledger"))}

packet = {"event_ledger": {"training": 8, "launch": 9},
          "monthly_numerators": {month: 19 for month in range(1, 15)},
          "monthly_denominators": {month: 110 for month in range(1, 15)},
          "frozen_windows": {"pre": list(range(1, 8)),
                             "post": list(range(9, 15))},
          "level_estimate": -.04, "slope_estimate": -.003,
          "residual_review": "recorded", "concurrent_event_log": [],
          "lag_scenarios": [0, 1, 2], "comparison_ledger": ["South"]}
review = interrupted_series_packet_gate(packet)
assert review == {"packet_complete": True, "months": 14,
                  "comparison_available": True}''',
    'The packet gate scans M monthly keys in O(M) expected time and O(M) space for the month set. Model fitting, comparison validation and dependence-aware inference have separate costs. Passing the gate confirms inspectable inputs, not a causal effect.',
    ['Do not call packet completeness statistical validity.', 'Do not omit concurrent-event notes because their list is inconvenient.', 'Do not publish a controlled estimate from an indirectly exposed comparison queue.'],
    ['data-science/interrupted-series-outcome-clock-and-data-contract','data-science/segmented-regression-level-and-slope-change','data-science/controlled-interrupted-series-comparison','data-science/interrupted-series-seasonality-and-residual-dependence','data-science/interrupted-series-transition-and-lag-sensitivity'])

assert len(lessons) == len(new_paths) == 6
titles = {path: row['title'] for path, row in by_path.items()}
titles.update({item['path']: item['title'] for item in lessons})

def prose(value):
    return re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',
                  lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                  html.escape(value))

def links(targets):
    return '<ul>' + ''.join('<li><a href="/' + target + '">' + html.escape(titles[target]) + '</a></li>'
                            for target in targets) + '</ul>'

def article_body(item):
    parts = ['<p>' + html.escape(item['summary']) + '</p>']
    for heading, paragraph in item['sections']:
        parts.extend(('<h2>' + html.escape(heading) + '</h2>', '<p>' + prose(paragraph) + '</p>'))
    parts.extend(('<h2>Implementation</h2>',
                  '<pre><code class="language-python">' + html.escape(item['code']) + '</code></pre>',
                  '<h2>Performance and operating cost</h2>', '<p>' + html.escape(item['cost']) + '</p>',
                  '<h3>Common Mistakes</h3>',
                  '<ul>' + ''.join('<li>' + html.escape(mistake) + '</li>' for mistake in item['mistakes']) + '</ul>',
                  '<h2>Read next</h2>', links(item['related'])))
    return ''.join(parts)

root_path = 'data-science/data-science-for-beginners'
project_hub_path = root_path + '/project'
for index, item in enumerate(lessons):
    is_project = item['path'].endswith('-project')
    body = article_body(item)
    path = item['path']
    row = dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://aitrove.in/' + path)),
               type='article', path=path, title=item['title'], summary=item['summary'], body=body,
               category='AI & Data', subject='data-science-project' if is_project else 'data-science',
               difficulty='Advanced', tags=['ai-data', 'data-science'], potd_date=None,
               featured=False, sort_order=13800 + index, status='published', published_at=stamp,
               created_at=stamp, updated_at=stamp,
               data={'subject_root':root_path,
                     'section_path':project_hub_path if is_project else root_path,
                     'content_format':'html', 'seo_ready':True,
                     'kind':'project' if is_project else 'tutorial',
                     'reading_minutes':max(5, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                     'author_path':'authors/aitrove-editorial',
                     'verification_suite':'Editorial, code and internal-link checks',
                     'related':[{'path':target, 'title':titles[target]} for target in item['related']]})
    rows.append(row)
    by_path[path] = row

tutorial_paths = ['data-science/' + slug for slug in slugs[:5]]
project_path = 'data-science/' + slugs[-1]
hub = by_path[root_path]
module_title = 'Interrupted time-series policy evaluation'
if not any(module['title'] == module_title for module in hub['data']['modules']):
    hub['data']['modules'].insert(-1, {'title':module_title,
                                      'summary':'Audit intervention timing, level and slope breaks, comparison paths, residuals and lags.',
                                      'lessons':tutorial_paths})
apply_module = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
if project_path not in apply_module['lessons']:
    apply_module['lessons'].append(project_path)
if '<h2>' + module_title + '</h2>' not in hub['body']:
    hub['body'] += '<h2>' + module_title + '</h2>' + links(tutorial_paths)
    hub['body'] += '<h2>Interrupted-series policy review</h2>' + links([project_path])
hub['updated_at'] = stamp

project_hub = by_path[project_hub_path]
if project_path not in project_hub['data']['modules'][0]['lessons']:
    project_hub['data']['modules'][0]['lessons'].append(project_path)
if '<h2>Interrupted-series policy review</h2>' not in project_hub['body']:
    project_hub['body'] += '<h2>Interrupted-series policy review</h2>' + links([project_path])
project_hub['updated_at'] = stamp

for source, target in [
    ('data-science/branch-month-panel-and-rollout-clock', tutorial_paths[0]),
    ('data-science/cohort-time-difference-in-differences', tutorial_paths[1]),
    ('data-science/spillover-aware-comparison-pool', tutorial_paths[2]),
    ('data-science/event-time-pretrend-and-support-audit', tutorial_paths[3]),
    ('data-science/negative-control-and-placebo-rollout-checks', tutorial_paths[4]),
    ('data-science/single-branch-policy-transfer-review-project', project_path),
]:
    source_row = by_path[source]
    anchor = '<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in source_row['body']:
        source_row['body'] += anchor
        source_row['data'].setdefault('related', []).append({'path':target, 'title':titles[target]})
        source_row['updated_at'] = stamp

assert len({row['path'] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_articles':len(lessons), 'new_projects':1, 'crosslinks_from_existing':6}))
