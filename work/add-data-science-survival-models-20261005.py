"""Add original survival-model and validation lessons to Data Science."""
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
    'cox-partial-likelihood-and-hazard-ratios',
    'proportional-hazards-diagnostics',
    'interval-censored-resolution-times',
    'fixed-horizon-survival-prediction-calibration',
    'support-resolution-model-review-project',
)
new_paths = {'data-science/' + slug for slug in slugs}
rows = [row for row in rows if row['path'] not in new_paths]
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
lessons = []

def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='data-science/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost,
                        mistakes=mistakes, related=related))

add('cox-partial-likelihood-and-hazard-ratios',
    'Cox partial likelihood and hazard-ratio interpretation',
    'A Cox model relates covariates to the instantaneous event rate among cases still at risk, while leaving the baseline hazard shape unspecified.', [
    ('Define the event before the ratio', 'For support operations, let the event be recorded resolution and time zero be case creation. A binary covariate marks whether a case entered the priority queue at creation. Under a proportional-hazards model, exp(beta) compares the resolution hazard for priority versus standard cases at the same elapsed age, conditional on modeled covariates. A value above one means a higher instantaneous resolution rate among still-unresolved cases. It is not a ratio of six-day resolution probabilities, and it does not directly express saved case-days. [[data-science/restricted-mean-open-time-between-queues|Restricted mean open time]] answers a different decision question.'),
    ('See how the risk set enters fitting', 'At each distinct resolution time, the partial-likelihood contribution compares the event case’s exp(beta times covariate) with the sum of those terms among every case still at risk just before that event. A right-censored case remains in earlier denominators and leaves after its censor time. This teaching implementation scans a no-ties, one-covariate ledger over a coefficient grid. It makes the mechanism inspectable; a production fit needs a vetted optimizer, tie handling, uncertainty estimation and careful treatment of delayed entry. [[data-science/event-time-risk-sets-and-tied-outcomes|Risk-set accounting]] is the foundation.'),
    ('Do not promote a baseline attribute that arrived later', 'Priority assignment recorded after case creation cannot be copied back to day zero. Doing so grants the eventual priority group guaranteed unresolved time before assignment. Use only covariates known at time zero for this static illustration, or represent later changes as time-varying intervals with an explicit observation design. [[data-science/landmark-analysis-and-immortal-time|Landmark analysis]] shows one conditional alternative.'),
    ('State what the model assumes', 'The hazard ratio is assumed constant over elapsed time for a fixed covariate contrast, even while the baseline hazard can rise or fall. Cases also need a defensible censoring mechanism and consistent outcome coding. A priority queue may receive more complex cases, so the fitted association is not automatically the causal effect of priority routing. Check available pre-assignment severity measures, case mix, and model stability before drawing an operational conclusion. [[data-science/proportional-hazards-diagnostics|Diagnostics]] test whether one ratio hides a changing relationship.'),
    ('Use a risk ratio only for its intended output', 'A hazard ratio can summarize a relative association for a model whose assumptions hold. A queue manager deciding staffing needs actual six-day resolution probabilities and open-time costs as well. Estimate those on a supported horizon and validate them on later cases; a model can rank cases reasonably while predicting the wrong absolute rate. [[data-science/fixed-horizon-survival-prediction-calibration|Horizon calibration]] checks that absolute prediction.')],
    '''from math import exp, log

def cox_log_partial_likelihood(case_records, coefficient):
    if len({case_id for case_id, _, _, _ in case_records}) != len(case_records):
        raise ValueError("duplicate case ID")
    if any(day <= 0 or resolved not in (0, 1) or priority not in (0, 1)
           for _, day, resolved, priority in case_records):
        raise ValueError("invalid case record")
    event_days = [day for _, day, resolved, _ in case_records if resolved]
    if len(event_days) != len(set(event_days)):
        raise ValueError("this teaching calculation requires untied events")
    score = 0.0
    for _, event_day, resolved, priority in case_records:
        if not resolved:
            continue
        risk_weight = sum(exp(coefficient * peer_priority)
                          for _, peer_day, _, peer_priority in case_records
                          if peer_day >= event_day)
        score += coefficient * priority - log(risk_weight)
    return score

cases = [("P61", 2, 1, 1), ("P62", 3, 1, 0), ("P63", 4, 0, 0),
         ("P64", 5, 1, 1), ("P65", 6, 0, 1), ("P66", 7, 1, 0),
         ("P67", 8, 1, 1), ("P68", 9, 0, 0)]
grid = [step / 100 for step in range(-200, 201)]
best_coefficient = max(grid, key=lambda value: cox_log_partial_likelihood(cases, value))
priority_hazard_ratio = exp(best_coefficient)
assert priority_hazard_ratio > 0
assert cox_log_partial_likelihood(cases, best_coefficient) >= (
    cox_log_partial_likelihood(cases, 0))''',
    'With N records, E event times and G grid coefficients, the direct risk-set scan is O(G × E × N) time and O(N) space for the ledger. Production partial-likelihood fitting precomputes risk information and handles ties; this grid is an explanation and input check, not an inference engine.',
    ['Do not interpret a hazard ratio as a fixed-horizon probability ratio.', 'Do not treat a post-creation queue assignment as a baseline feature.', 'Do not use this no-ties grid as a production replacement for an established survival fitter.'],
    ['data-science/proportional-hazards-diagnostics','data-science/interval-censored-resolution-times','data-science/fixed-horizon-survival-prediction-calibration','data-science/support-resolution-model-review-project'])

add('proportional-hazards-diagnostics',
    'Diagnose the proportional-hazards assumption',
    'A proportional-hazards model assigns one time-constant covariate effect; systematic changes in event-time residuals can expose a misleading single hazard ratio.', [
    ('Ask whether one ratio is coherent', 'A priority workflow may accelerate early resolutions but have little effect on difficult cases still open after two weeks. One constant priority hazard ratio then compresses distinct phases into a number that may answer neither phase well. Compare group curves, event counts and at-risk counts over elapsed time before fitting. A crossing or changing separation warrants closer examination, although visual patterns alone are not a formal test. [[data-science/kaplan-meier-resolution-curve|The unresolved curves]] establish the observed shape.'),
    ('Inspect event-time residuals', 'For a binary priority covariate, a Schoenfeld-style residual at a resolution event is the event case’s priority indicator minus its risk-set-weighted expected priority indicator under the fitted coefficient. If residuals have a systematic relationship with event time, the assumed constant effect may be doubtful. The code computes raw residuals for untied events; it does not standardize them, estimate their variance, or produce a formal significance test. A production review uses a supported residual diagnostic and plots alongside the business timeline.'),
    ('Avoid mechanical p-value decisions', 'With many covariates, some checks flag by chance. With a very large cohort, tiny departures can yield small p-values even when fixed-horizon decisions barely change. Review effect shape, late risk-set support, and whether the difference matters to the intended policy. A failed diagnostic does not identify why the relationship changed; the issue might be genuinely time-dependent treatment, shifting case mix, delayed entry, or misrecorded resolution times.'),
    ('Choose a revised estimand or model', 'If priority impact differs early and late, report time-specific contrasts or a prespecified restricted-mean difference at a common horizon. A stratified Cox fit can handle a nonproportional nuisance category when its coefficient is not the desired output. A time-varying coefficient model needs an explicit interval structure and adequate events in each period. Do not search many cut points after seeing the residual plot and present the best-looking split as a prespecified result. [[data-science/restricted-mean-open-time-between-queues|Bounded open-time comparison]] avoids requiring one constant hazard ratio.'),
    ('Keep causal claims separate', 'A proportional-hazards diagnostic concerns model form, not confounding. Even a perfectly flat residual pattern cannot make queue assignment random. Record priority rules, pre-assignment severity and policy version alongside the diagnostic. If the question is whether prioritization causes faster resolution, build a design that addresses treatment selection. [[data-science/support-resolution-model-review-project|The model-review project]] treats this as a release gate, not a decorative chart.')],
    '''from math import exp

def priority_event_residuals(case_records, coefficient):
    event_days = [day for _, day, resolved, _ in case_records if resolved]
    if len(event_days) != len(set(event_days)):
        raise ValueError("untied event times required")
    residuals = []
    for _, event_day, resolved, priority in case_records:
        if not resolved:
            continue
        risk_set = [(peer_priority, exp(coefficient * peer_priority))
                    for _, peer_day, _, peer_priority in case_records
                    if peer_day >= event_day]
        total_weight = sum(weight for _, weight in risk_set)
        expected_priority = sum(indicator * weight for indicator, weight in risk_set) / total_weight
        residuals.append((event_day, priority - expected_priority))
    return sorted(residuals)

cases = [("P61", 2, 1, 1), ("P62", 3, 1, 0), ("P63", 4, 0, 0),
         ("P64", 5, 1, 1), ("P65", 6, 0, 1), ("P66", 7, 1, 0),
         ("P67", 8, 1, 1), ("P68", 9, 0, 0)]
residuals = priority_event_residuals(cases, 0.35)
assert len(residuals) == 5
assert all(-1 <= value <= 1 for _, value in residuals)
assert [day for day, _ in residuals] == [2, 3, 5, 7, 8]''',
    'The direct implementation scans N cases for each of E events: O(E × N) time and O(E) output space. It is a transparent raw residual calculation. Scaling, uncertainty tests, tied events and clustered cases require more machinery than this exercise includes.',
    ['Do not call an unscaled residual scan a formal assumption test.', 'Do not treat a flat residual plot as proof of no confounding.', 'Do not choose time splits only after inspecting the pattern.'],
    ['data-science/cox-partial-likelihood-and-hazard-ratios','data-science/restricted-mean-open-time-between-queues','data-science/survival-curve-uncertainty-and-tail-support','data-science/support-resolution-model-review-project'])

add('interval-censored-resolution-times',
    'Interval-censored support resolution times',
    'An interval-censored event is known to have occurred between two inspections, while its exact time is unknown; neither endpoint is an observed event time.', [
    ('Preserve the observation interval', 'A batch system checks case status every few days. A case unresolved at day two but resolved when next checked at day five has a resolution time in (2,5]. Labelling it as a day-five resolution creates an artificial delay; labelling it as day two creates an artificial improvement. Store the last confirmed unresolved age and first confirmed resolved age. An open case last checked at day seven is right-censored beyond seven. [[data-science/right-censoring-and-time-to-event|Right censoring]] and interval censoring carry different information.'),
    ('Handle interval boundaries consistently', 'The teaching ledger has several (left,right] resolution intervals and one right-censored case (7,infinity). A case resolved at the first inspection may be left-censored within (0,first inspection]. If an event timestamp is exact, keep it as exact rather than broadening it to an arbitrary daily window. Reject a negative age, a zero-width interval in this simplified model, or a right endpoint earlier than its left. A system that changed inspection cadence can change interval widths without changing the underlying resolution process.'),
    ('Use a likelihood that respects what was seen', 'For an illustrative exponential resolution model with rate lambda, the probability of resolution in (L,R] is exp(-lambda L) minus exp(-lambda R). The probability of still being unresolved beyond L is exp(-lambda L). Summing the log of the appropriate contribution for each case yields a likelihood that uses interval information without inventing exact event times. The grid search below is deliberately small and parametric; it is not a general nonparametric interval-censored survival estimator.'),
    ('Separate model fit from business interpretation', 'A constant hazard assumption can be implausible when new cases are easy and old cases become increasingly difficult. Inspect whether predicted inspection-state shares match observed ones by interval and queue. A fitted rate is conditional on the inspection schedule and inclusion rule; it should not be compared with a Kaplan–Meier curve built from invented exact times. If the goal is a six-day service claim, report an interval-aware estimate and uncertainty under a method that supports the observation pattern.'),
    ('Build a verification route', 'For production, use an implementation designed for interval censoring and verify its supported interval conventions. Keep raw inspections so the bounds can be rebuilt after a status correction. Avoid replacing infinity with a giant made-up timestamp in an export. [[data-science/support-resolution-model-review-project|The review project]] blocks model release when interval cases are silently forced into the exact-time path.')],
    '''from math import expm1, log

def interval_resolution_log_likelihood(observations, resolution_rate):
    if resolution_rate <= 0:
        raise ValueError("rate must be positive")
    total = 0.0
    for last_unresolved_day, first_resolved_day in observations:
        if last_unresolved_day < 0:
            raise ValueError("negative observation age")
        if first_resolved_day is None:
            total -= resolution_rate * last_unresolved_day
            continue
        if first_resolved_day <= last_unresolved_day:
            raise ValueError("invalid resolution interval")
        interval_width = first_resolved_day - last_unresolved_day
        total += -resolution_rate * last_unresolved_day
        total += log(-expm1(-resolution_rate * interval_width))
    return total

inspections = [(0, 2), (2, 5), (4, 7), (7, None), (0, 3)]
candidate_rates = [step / 1000 for step in range(20, 501, 2)]
best_rate = max(candidate_rates, key=lambda rate:
                interval_resolution_log_likelihood(inspections, rate))
assert 0.02 <= best_rate <= 0.5
assert interval_resolution_log_likelihood(inspections, best_rate) >= (
    interval_resolution_log_likelihood(inspections, 0.1))''',
    'With N observations and G candidate rates, the explicit grid is O(N × G) time and O(N) input space. A general interval-censored fit needs more careful optimization and uncertainty calculation. The dominant data risk is losing inspection bounds during extraction.',
    ['Do not substitute the right inspection time as the exact resolution time.', 'Do not call a right-censored case an interval-censored resolution.', 'Do not present a constant-rate grid search as a model-free survival curve.'],
    ['data-science/right-censoring-and-time-to-event','data-science/cox-partial-likelihood-and-hazard-ratios','data-science/fixed-horizon-survival-prediction-calibration','data-science/support-resolution-model-review-project'])

add('fixed-horizon-survival-prediction-calibration',
    'Calibrate resolution predictions at a fixed horizon',
    'Fixed-horizon calibration compares predicted event probabilities with observed event shares among cases whose outcome status is known at that horizon.', [
    ('Freeze the prediction time and event', 'Suppose a model predicts the probability that a case resolves by day six using information available at creation. Store that prediction before observing later statuses. The target is resolution by day six, not eventual resolution or any terminal exit. A case that resolves on day five is a positive outcome; a case still observed open at day eight is negative at day six. Do not turn a case censored on day four into a negative: its day-six status is unknown. [[data-science/competing-risks-and-resolution-incidence|Competing exits]] require an explicit separate target policy.'),
    ('Use a fully observed teaching cohort', 'The code below requires each case to have a resolution event by day six or to remain observed through day six. It rejects early censoring rather than silently dropping those cases. In a production cohort with early censoring, evaluate with an appropriate censor-aware method and a censoring model whose support covers the horizon. A mature cohort formed solely by older creation dates can avoid administrative early censoring, but its population and calendar period need to match the intended deployment.'),
    ('Inspect probability groups and scoring', 'In an eight-case ledger, four predictions at or above 0.5 average near 0.71 and three of those four cases resolve by day six. Four lower predictions average near 0.28 and one of those four resolves. These small bins are only a calculation check. Report bin counts and uncertainty before reading small differences as model failure. The Brier score is the mean squared difference between predicted resolution probability and observed six-day outcome for this fully observed fixture. Lower is better on that scoring rule.'),
    ('Keep discrimination separate', 'A model can rank high-risk cases ahead of low-risk cases while systematically predicting 0.80 when only 0.55 resolve. A concordance statistic alone will not reveal that absolute error. Compare calibration at prespecified business horizons and operationally meaningful groups, then examine score distribution drift. Recalibration should use held-out or later data; tuning and evaluating on the same cases hides optimism. [[data-science/held-out-predictive-log-score|Held-out scoring]] offers another proper-score view.'),
    ('Make censoring visible in release notes', 'If early censoring exists, a naive complete-case plot can be biased because short follow-up may depend on case age or queue. Document the fraction censored before the horizon by group. An inverse-censoring-weighted score requires an estimated censoring distribution and adequate support; a weight is not a substitute for investigating why cases disappeared. [[data-science/support-resolution-model-review-project|The model-review project]] gates the simple path on complete horizon observation.')],
    '''def horizon_calibration(case_predictions, horizon_days):
    if horizon_days <= 0 or not case_predictions:
        raise ValueError("invalid horizon or empty cohort")
    if len({case_id for case_id, _, _, _ in case_predictions}) != len(case_predictions):
        raise ValueError("duplicate case ID")
    groups = {"lower": [], "higher": []}
    squared_errors = []
    for case_id, resolution_probability, observed_day, resolved in case_predictions:
        if not 0 <= resolution_probability <= 1 or observed_day < 0:
            raise ValueError("invalid prediction or observation")
        if resolved not in (0, 1):
            raise ValueError("invalid event flag")
        if not resolved and observed_day < horizon_days:
            raise ValueError("outcome unknown at horizon")
        outcome = int(bool(resolved and observed_day <= horizon_days))
        group = "higher" if resolution_probability >= 0.5 else "lower"
        groups[group].append((resolution_probability, outcome))
        squared_errors.append((resolution_probability - outcome) ** 2)
    return {name: {"count": len(values),
                   "predicted": sum(prob for prob, _ in values) / len(values),
                   "observed": sum(outcome for _, outcome in values) / len(values)}
            for name, values in groups.items() if values}, (
            sum(squared_errors) / len(squared_errors))

cases = [("H71", .70, 2, 1), ("H72", .80, 4, 1),
         ("H73", .60, 5, 1), ("H74", .75, 8, 0),
         ("H75", .20, 3, 1), ("H76", .30, 8, 0),
         ("H77", .25, 9, 1), ("H78", .35, 8, 0)]
bins, brier = horizon_calibration(cases, 6)
assert bins["higher"]["observed"] == .75
assert bins["lower"]["observed"] == .25
assert 0 <= brier <= 1''',
    'Grouping N fully observed cases is O(N) time and O(N) space here because bin records are retained; streaming totals reduce additional space to O(1) for fixed bins. Censor-aware evaluation needs extra estimation and must not be approximated by relabeling missing outcomes.',
    ['Do not score a case censored before the horizon as a negative.', 'Do not equate ranking ability with calibrated probabilities.', 'Do not tune and evaluate probability bins on the same release data without saying so.'],
    ['data-science/cox-partial-likelihood-and-hazard-ratios','data-science/interval-censored-resolution-times','data-science/held-out-predictive-log-score','data-science/support-resolution-model-review-project'])

add('support-resolution-model-review-project',
    'Project: review a support-resolution survival model',
    'Build a release packet that separates exact events, interval observations and early censoring before interpreting hazard ratios or six-day predictions.', [
    ('Fix the case-level contract', 'Define case creation as time zero and resolution as the event. Record one case ID, pre-creation priority flag, observed end age, event flag, cancellation status, and status-timestamp precision. Keep inspection bounds for cases whose resolution was discovered only at periodic checks. Do not merge these into exact timestamps to make one uniform table. [[data-science/interval-censored-resolution-times|Interval observations]] require their own path, and [[data-science/competing-risks-and-resolution-incidence|cancellation]] needs its own outcome policy.'),
    ('Verify relative-risk fitting', 'On an exact-time, no-ties teaching ledger, reproduce a one-covariate Cox partial-likelihood grid and exponentiate its coefficient for a priority-versus-standard hazard ratio. Check event-time risk sets, censor removal, and coefficient sign. Then use an established fitter for the production model, with its tie method and uncertainty settings recorded. A hazard ratio is a conditional instantaneous-rate comparison, not a direct estimate of saved staff time. [[data-science/cox-partial-likelihood-and-hazard-ratios|The fitting lesson]] sets that boundary.'),
    ('Inspect model form and action relevance', 'Plot group unresolved curves with risk counts and inspect event-time residuals for a changing priority effect. Do not treat one p-value as a complete diagnostic. If the relative effect varies meaningfully with elapsed age, prefer a prespecified six-day restricted-mean contrast or a model designed for time-varying effects. Record whether priority was genuinely known at creation; any later assignment needs a different exposure design. [[data-science/proportional-hazards-diagnostics|Assumption checks]] and [[data-science/landmark-analysis-and-immortal-time|timing checks]] both matter.'),
    ('Validate absolute predictions', 'Freeze predicted six-day resolution probabilities on a later case-created cohort. Verify that every case is either resolved by day six or observed at least through day six before using the simple bin-and-Brier calculation. Separate cases censored earlier, estimate how many there are by queue, and route evaluation to a censor-aware method if needed. Report predicted and observed shares with bin counts; a model may rank well yet overstate six-day resolution. [[data-science/fixed-horizon-survival-prediction-calibration|The horizon lesson]] supplies a strict training fixture.'),
    ('Make release or withhold explicit', 'The packet should name the cohort dates, status-code map, tie method, interval-case count, cancellation count, early-censor count, fit diagnostics, horizon support and calibration result. Withhold an absolute prediction claim when horizon status is unknown, an interval event has been coerced to an exact day, or the model fails a material assumption needed for the decision. The code below is a gate for the simple fully observed path; it does not fit or certify a survival model.')],
    '''def model_review_gate(case_records, horizon_days):
    if horizon_days <= 0:
        raise ValueError("invalid horizon")
    if len({case_id for case_id, _, _, _, _ in case_records}) != len(case_records):
        raise ValueError("duplicate case ID")
    exact_events = interval_events = early_censors = 0
    for case_id, observed_day, outcome, exact_time, baseline_priority in case_records:
        if observed_day < 0 or baseline_priority not in (0, 1):
            raise ValueError("invalid case record")
        if outcome not in {"resolved", "cancelled", "open"}:
            raise ValueError("unknown terminal status")
        if outcome == "resolved":
            exact_events += bool(exact_time)
            interval_events += not exact_time
        elif outcome == "open" and observed_day < horizon_days:
            early_censors += 1
    return {"exact_events": exact_events,
            "interval_events": interval_events,
            "early_censors": early_censors,
            "simple_horizon_score_ready": interval_events == 0
                                          and early_censors == 0}

ledger = [("M81", 2, "resolved", True, 1),
          ("M82", 5, "resolved", False, 0),
          ("M83", 4, "open", True, 1),
          ("M84", 8, "open", True, 0)]
review = model_review_gate(ledger, 6)
assert review["exact_events"] == 1
assert review["interval_events"] == 1
assert review["early_censors"] == 1
assert not review["simple_horizon_score_ready"]''',
    'A one-pass gate over N case records costs O(N) expected time for uniqueness checking and O(N) space for case IDs. Full model fitting, interval-aware inference and censor-adjusted validation have additional costs. The gate prevents unsupported evaluation claims; it is not a statistical approval certificate.',
    ['Do not hide interval events by assigning their first observed resolved day as exact.', 'Do not release a simple horizon score when cases disappear before the horizon.', 'Do not interpret a fitted priority association as a randomized policy effect.'],
    ['data-science/cox-partial-likelihood-and-hazard-ratios','data-science/proportional-hazards-diagnostics','data-science/interval-censored-resolution-times','data-science/fixed-horizon-survival-prediction-calibration'])

assert len(lessons) == len(new_paths) == 5
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
               featured=False, sort_order=13200 + index, status='published', published_at=stamp,
               created_at=stamp, updated_at=stamp,
               data={'subject_root':root_path,
                     'section_path':project_hub_path if is_project else root_path,
                     'content_format':'html', 'seo_ready':True,
                     'kind':'project' if is_project else 'tutorial',
                     'reading_minutes':max(5, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                     'author_path':'authors/aitrove-editorial',
                     'verification_suite':'Editorial and syntax review; project inputs needed for runtime checks',
                     'related':[{'path':target, 'title':titles[target]} for target in item['related']]})
    rows.append(row)
    by_path[path] = row

tutorial_paths = ['data-science/' + slug for slug in slugs[:4]]
project_path = 'data-science/' + slugs[-1]
hub = by_path[root_path]
if not any(module['title'] == 'Survival models and prediction checks' for module in hub['data']['modules']):
    hub['data']['modules'].insert(-1, {'title':'Survival models and prediction checks',
                                      'summary':'Interpret relative hazards, test time-constant effects, preserve inspection intervals and validate fixed-horizon probabilities.',
                                      'lessons':tutorial_paths})
apply_module = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
if project_path not in apply_module['lessons']:
    apply_module['lessons'].append(project_path)
if '<h2>Survival models and prediction checks</h2>' not in hub['body']:
    hub['body'] += '<h2>Survival models and prediction checks</h2>' + links(tutorial_paths)
    hub['body'] += '<h2>Support resolution model review</h2>' + links([project_path])
hub['updated_at'] = stamp

project_hub = by_path[project_hub_path]
if project_path not in project_hub['data']['modules'][0]['lessons']:
    project_hub['data']['modules'][0]['lessons'].append(project_path)
if '<h2>Support resolution model review</h2>' not in project_hub['body']:
    project_hub['body'] += '<h2>Support resolution model review</h2>' + links([project_path])
project_hub['updated_at'] = stamp

for source, target in [
    ('data-science/kaplan-meier-resolution-curve', tutorial_paths[0]),
    ('data-science/survival-curve-uncertainty-and-tail-support', tutorial_paths[1]),
    ('data-science/right-censoring-and-time-to-event', tutorial_paths[2]),
    ('data-science/restricted-mean-unresolved-time', tutorial_paths[3]),
    ('data-science/specialist-queue-survival-comparison-project', project_path),
]:
    source_row = by_path[source]
    anchor = '<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in source_row['body']:
        source_row['body'] += anchor
        if source_row['type'] == 'article':
            source_row['data'].setdefault('related', []).append({'path':target, 'title':titles[target]})
        source_row['updated_at'] = stamp

assert len({row['path'] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_articles':len(lessons), 'new_projects':1, 'crosslinks_from_existing':5}))
