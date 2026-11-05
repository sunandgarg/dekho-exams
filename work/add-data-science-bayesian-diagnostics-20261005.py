"""Add original Bayesian model-checking lessons to Data Science."""
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
    'posterior-predictive-group-discrepancy',
    'prior-sensitivity-for-action-thresholds',
    'held-out-predictive-log-score',
    'sequential-posterior-monitoring-contract',
    'support-rate-model-checking-project',
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

add('posterior-predictive-group-discrepancy',
    'Posterior predictive checks for a hidden group gap',
    'A posterior predictive check asks whether replicated data from a fitted model exhibit the feature that matters in the observed data.', [
    ('Specify the discrepancy', 'A 53-case support audit contains 11 escalations: eight among 17 West cases and three among 36 East cases. A pooled model assigns one escalation probability to every case. Its overall count may fit while the observed West-minus-East rate gap, about 38.7 percentage points, remains hard to reproduce. Choose that gap as the discrepancy before inspecting simulated results. [[data-science/subgroup-distribution-and-aggregation-reversal|Subgroup analysis]] explains why a pooled average can hide a service problem.'),
    ('Generate replicated audits', 'With a Beta(4, 36) prior, the pooled posterior after 11 events in 53 cases is Beta(15, 78). Draw a possible rate from that posterior, then simulate 17 West and 36 East binary outcomes at the same drawn rate. Repeating this creates replicated audits under the fitted pooled model. Compare each replicated group gap with the observed gap. A small tail fraction flags a mismatch; it is not a classically calibrated p-value.'),
    ('Look at what the model can and cannot express', 'The pooled model can only create a group gap through binomial noise. If the observed gap is rarely reproduced, investigate whether queues differ in case mix, staffing, measurement or true underlying rates. A group-specific model could help, but its fit also needs checking. [[data-science/shared-priors-and-partial-pooling-limits|Shared-prior estimates]] are a baseline; a fitted hierarchical model would carry uncertainty in its population distribution.'),
    ('Separate model criticism from forecast testing', 'The same 53 outcomes informed the posterior and are used in this check. That is acceptable for diagnosing a structural miss, but it does not measure future predictive accuracy. A held-out mature period is needed for that. [[data-science/held-out-predictive-log-score|Held-out scoring]] asks a different question. Report both, and do not claim that passing a predictive check proves the model is true.'),
    ('Preserve simulation details', 'Save the audit snapshot, chosen discrepancy, posterior parameters, random seed, number of replications and observed statistic. Repeat with enough replications to make Monte Carlo noise small relative to the decision. If a few runs disagree materially, increase draws. Investigate source labels before changing a model merely to fit one unusual group count.')],
    'from random import Random\n\ndef replicated_gap_tail(west_events, west_cases, east_events, east_cases,\n                        prior_alpha=4, prior_beta=36, replications=3000, seed=53):\n    if not (0 <= west_events <= west_cases and 0 <= east_events <= east_cases):\n        raise ValueError("invalid group counts")\n    if min(west_cases, east_cases, replications) <= 0:\n        raise ValueError("positive group sizes and replications required")\n    observed_gap = west_events / west_cases - east_events / east_cases\n    alpha = prior_alpha + west_events + east_events\n    beta = prior_beta + west_cases + east_cases - west_events - east_events\n    generator = Random(seed)\n    exceedances = 0\n    for _ in range(replications):\n        pooled_rate = generator.betavariate(alpha, beta)\n        west_rep = sum(generator.random() < pooled_rate for _ in range(west_cases))\n        east_rep = sum(generator.random() < pooled_rate for _ in range(east_cases))\n        exceedances += west_rep / west_cases - east_rep / east_cases >= observed_gap\n    return exceedances / replications\n\ntail_fraction = replicated_gap_tail(8, 17, 3, 36)\nassert 0 <= tail_fraction <= 1',
    'With S replications and N total cases, direct Bernoulli simulation costs O(SN) time and O(1) working space. Large audits can draw binomial group counts directly. The tail fraction is a diagnostic of the chosen discrepancy under this model, not a general goodness score.',
    ['Do not call a posterior predictive tail fraction a conventional p-value.', 'Do not check only the overall event count when group disparity drives the decision.', 'Do not treat an in-sample check as held-out predictive validation.'],
    ['data-science/prior-sensitivity-for-action-thresholds','data-science/held-out-predictive-log-score','data-science/sequential-posterior-monitoring-contract','data-science/support-rate-model-checking-project'])

add('prior-sensitivity-for-action-thresholds',
    'Prior sensitivity for an operational action threshold',
    'A decision supported by a small audit should be recalculated under plausible prior strengths before it changes staffing.', [
    ('Hold the data and action fixed', 'The audit has 11 escalations among 53 mature cases. Leadership plans extra review capacity when evidence suggests the underlying rate exceeds 17%. Fix that rate threshold and the loss of an unnecessary shift before comparing priors. A prior-sensitivity check changes only the prior assumptions, not the observed cohort or decision rule. [[data-science/decision-objective-and-action-unit|The decision objective]] defines what an extra shift is meant to prevent.'),
    ('Compare equal-mean priors', 'Beta(1, 9), Beta(4, 36) and Beta(12, 108) all have prior mean 10% but concentrations of 10, 40 and 120. With the same 11 events in 53 cases, posterior means are 12/63, about 19.0%; 15/93, about 16.1%; and 23/173, about 13.3%. The 17% action threshold lies inside this spread. A decision based only on one prior mean or one posterior mean would conceal that fragility.'),
    ('Check plausibility before preference', 'The concentrated prior might reflect a stable historical service process, or it might be stale after a queue redesign. Review the older cohort, its outcome definition and its prior predictive implications. [[data-science/prior-predictive-checks-for-event-rates|Prior predictive checks]] can reject implausible choices before the current audit. Do not pick the weak prior just because it triggers the desired staffing action, or the strong prior because it avoids cost.'),
    ('Compare decision quantities', 'For each prior, calculate the posterior probability that the rate exceeds 17%, not just the mean. A cost-sensitive policy may require probability above a prespecified level. Show the probability range and whether all plausible priors lead to the same action. If they disagree, either collect more mature cases or use a conservative temporary action whose cost is acceptable. [[data-science/posterior-intervals-and-decision-probabilities|Posterior decisions]] are conditional on the model.'),
    ('Do not use sensitivity as a ritual', 'A list of arbitrary priors has little value. Tie alternatives to distinct evidence states: little reliable history, a comparable prior period, and a strong but potentially outdated history. Save parameters and rationale. If the likelihood is wrong because West and East have different rates, prior sensitivity alone will not repair that structural problem. [[data-science/posterior-predictive-group-discrepancy|Group checks]] target the likelihood.')],
    'def posterior_means_by_prior(prior_shapes, escalations, audited):\n    if not 0 <= escalations <= audited:\n        raise ValueError("invalid audit counts")\n    means = {}\n    for prior_name, (alpha, beta) in prior_shapes.items():\n        if alpha <= 0 or beta <= 0:\n            raise ValueError("prior shapes must be positive")\n        means[prior_name] = (alpha + escalations) / (alpha + beta + audited)\n    return means\n\npriors = {"weak": (1, 9), "working": (4, 36), "strong": (12, 108)}\nmeans = posterior_means_by_prior(priors, 11, 53)\nassert round(means["weak"], 3) == 0.190\nassert round(means["working"], 3) == 0.161\nassert round(means["strong"], 3) == 0.133',
    'Computing posterior means for P candidate priors is O(P) time and output space. Probability calculations using Monte Carlo add sampling cost per prior. More computation cannot identify which prior population is comparable; that requires data lineage and domain review.',
    ['Do not choose a prior after seeing which staffing action it favors.', 'Do not vary the prior while silently changing the audit cohort or threshold.', 'Do not use prior sensitivity to excuse a poor likelihood model.'],
    ['data-science/posterior-predictive-group-discrepancy','data-science/held-out-predictive-log-score','data-science/sequential-posterior-monitoring-contract','data-science/support-rate-model-checking-project'])

add('held-out-predictive-log-score',
    'Held-out predictive log scores for a binary rate model',
    'A model should be checked on outcomes that were unavailable when its posterior and prediction rule were formed.', [
    ('Freeze a time boundary', 'Fit the service-rate model on 53 cases whose seven-day outcomes have matured. The next 29 mature cases, with five escalations, form a later holdout. Do not use any of those 29 labels to choose the prior, inspect group anomalies, or tune a threshold before scoring. [[data-science/reproducible-analysis-snapshot|A frozen snapshot]] records the exact cutoff and exclusions. Future cases are a stronger operational test than a random split that mixes policy periods.'),
    ('Predict one future binary case', 'A Beta(15, 78) posterior implies a next-case escalation probability of 15/93, about 16.1%, under the one-rate exchangeable model. Freeze that probability for all 29 held-out cases to make a fixed-model comparison. A baseline using the earlier prior mean predicts 10%. The observed holdout share is 5/29, about 17.2%; this does not mean the model was calibrated from one small holdout.'),
    ('Score both outcomes', 'Binary log loss penalizes an assigned probability when its event outcome is surprising. Add the negative log probability for each held-out case and divide by 29. Lower is better. It rewards probabilities that describe both events and non-events, unlike a thresholded accuracy score that discards probability information. Clip only to guard machine arithmetic at zero or one; a clipped score should be disclosed if it affects results.'),
    ('Separate fixed forecasts from updating', 'The fixed-score comparison does not update after each held-out label. A live sequential forecast could update its posterior as cases mature, but then it must score each case with the probability recorded before that outcome arrived. Do not calculate a posterior using all 29 holdout outcomes and call its in-sample probabilities held-out predictions. [[data-science/sequential-posterior-monitoring-contract|The monitoring contract]] prevents this look-ahead.'),
    ('Inspect more than one aggregate score', 'Report log loss by queue and calendar period. A pooled model may score acceptably overall while assigning poor probabilities to West. Compare it with a simple baseline under the same time boundary and eligibility rule. Predictive performance does not prove causal validity or that the model’s staffing decision is cost-effective. [[data-science/posterior-predictive-group-discrepancy|A group discrepancy check]] can reveal a structural miss that one scalar score obscures.')],
    'from math import log\n\ndef binary_log_loss(events, cases, predicted_rate):\n    if not 0 <= events <= cases or cases == 0:\n        raise ValueError("invalid held-out counts")\n    if not 0 < predicted_rate < 1:\n        raise ValueError("probability must be inside (0, 1)")\n    return -(events * log(predicted_rate) +\n             (cases - events) * log(1 - predicted_rate)) / cases\n\nmodel_loss = binary_log_loss(5, 29, 15 / 93)\nbaseline_loss = binary_log_loss(5, 29, 0.10)\nassert model_loss < baseline_loss',
    'For aggregated binary counts, one log-loss evaluation is O(1); per-case scoring is O(N) for N holdout cases. Training and model fitting are separate costs. A small holdout gives a noisy comparison, so report denominators and repeat over later periods.',
    ['Do not fit or tune with holdout outcomes before scoring them.', 'Do not confuse one-case predictive probability with the joint predictive distribution of 29 cases.', 'Do not treat a lower aggregate log loss as proof of good subgroup performance.'],
    ['data-science/posterior-predictive-group-discrepancy','data-science/prior-sensitivity-for-action-thresholds','data-science/sequential-posterior-monitoring-contract','data-science/support-rate-model-checking-project'])

add('sequential-posterior-monitoring-contract',
    'Sequential posterior monitoring with mature outcomes',
    'A posterior may be updated as new batches arrive, but the update ledger must keep outcomes mature, unique and ordered.', [
    ('Define a batch boundary', 'A seven-day escalation label is unknown on the day a case closes. Batches should include only cases whose outcome window has matured by the monitoring cutoff. Suppose batch A contains 19 cases with three escalations and batch B contains 34 cases with eight. Together they give 11 of 53, but only after both windows close. A partially mature batch undercounts later escalations. [[data-science/right-censoring-and-time-to-event|Censoring]] offers another analysis path when time-to-escalation is itself important.'),
    ('Prevent duplicate evidence', 'Store a stable batch ID, case IDs, cohort rule, close date, outcome-maturity date and source snapshot. Before updating, verify that no case appears in an earlier batch and that 0 ≤ events ≤ cases. An ingestion retry must not add the same 19 cases twice. [[data-science/beta-binomial-updating-and-effective-prior-size|Conjugate updating]] is arithmetically simple; identity control is the failure-prone part.'),
    ('Record probabilities before decisions', 'At each checkpoint, save the posterior, the probability of crossing the service threshold and the action rule before the next labels arrive. A Bayesian posterior can be recomputed after every mature batch, but the operating policy may have costs, capacity limits and repeated interventions. Assess its long-run false-action and missed-action behavior by simulating realistic sequences, rather than assuming that any posterior threshold automatically has a desired error rate.'),
    ('Handle changing regimes', 'If the support process changed between batches, the common-rate likelihood may no longer apply. Report batch-level rates and case mix, inspect predictive misfit, and consider a time-varying model or a reset with an explicit rationale. Do not carry a strong posterior from an obsolete period into a new queue as if it were fresh evidence. [[data-science/prior-sensitivity-for-action-thresholds|Sensitivity checks]] show whether the carried prior drives the decision.'),
    ('Keep the audit trail replayable', 'Rebuild the current posterior from the immutable batch ledger and compare it with the stored state. A corrected label requires a new ledger revision and a replay, not a silent subtraction from a dashboard card. Record who approved the correction and which downstream staffing decisions used the earlier state. [[data-science/support-rate-model-checking-project|The project]] combines this ledger with held-out scoring.')],
    'def replay_mature_batches(prior_alpha, prior_beta, batches):\n    if prior_alpha <= 0 or prior_beta <= 0:\n        raise ValueError("prior shapes must be positive")\n    seen = set()\n    alpha, beta = prior_alpha, prior_beta\n    for batch in batches:\n        if batch["id"] in seen or not batch["mature"]:\n            raise ValueError("duplicate or immature batch")\n        events, cases = batch["escalations"], batch["cases"]\n        if not 0 <= events <= cases:\n            raise ValueError("invalid batch counts")\n        seen.add(batch["id"])\n        alpha += events\n        beta += cases - events\n    return alpha, beta\n\nledger = [{"id": "west-sep", "mature": True, "escalations": 3, "cases": 19},\n          {"id": "east-sep", "mature": True, "escalations": 8, "cases": 34}]\nassert replay_mature_batches(4, 36, ledger) == (15, 78)',
    'Replaying B batches is O(B) expected time and O(B) space for the batch-ID set. Exact case-level deduplication requires additional identity storage or reconciliation and may dominate the job. Do not infer statistical validity from a ledger that only checks arithmetic.',
    ['Do not count a case before its outcome window matures.', 'Do not accept a retry as fresh evidence.', 'Do not assume a posterior threshold has a known long-run false-action rate without evaluating the full policy.'],
    ['data-science/posterior-predictive-group-discrepancy','data-science/prior-sensitivity-for-action-thresholds','data-science/held-out-predictive-log-score','data-science/support-rate-model-checking-project'])

add('support-rate-model-checking-project',
    'Project: check a Bayesian support-rate model before acting',
    'Build a reproducible model audit with posterior replication, prior alternatives, future scoring and a mature-batch ledger.', [
    ('Freeze the evidence', 'Use 53 mature audited support cases with 11 seven-day escalations. West contributes eight of 17 cases; East contributes three of 36. Keep case IDs, queue labels, close dates, maturity dates and source snapshots. A second, later holdout contains 29 mature cases with five escalations. The earlier period alone fits the model; the later period is reserved for scoring. [[data-science/metric-denominator-and-cohort|Cohort rules]] must reconcile all counts.'),
    ('Check prior and model structure', 'Record Beta(4, 36) as the working prior and Beta(1, 9) and Beta(12, 108) as weak and strong alternatives. Update each using the same 11 of 53 evidence, then compare posterior means and action probabilities at a 17% rate threshold. Simulate 17 West and 36 East outcomes from the pooled posterior and compare group-rate gaps. [[data-science/posterior-predictive-group-discrepancy|Posterior replication]] exposes a mismatch hidden by the total.'),
    ('Score the future period', 'Use the working posterior Beta(15, 78) to predict each case in the next 29-case holdout with the frozen next-case rate 15/93. Compare binary log loss to a 10% baseline. Keep outcomes hidden until predictions are stored, then report both overall and queue-level scores. [[data-science/held-out-predictive-log-score|Held-out scoring]] measures future prediction rather than in-sample fit.'),
    ('Replay the monitoring ledger', 'Split the 53 fit cases into a 19-case batch with three escalations and a 34-case batch with eight. Check that each batch is mature and unique, then replay the prior to Beta(15, 78). Add fixtures for an immature batch and a repeated ID; both must fail. [[data-science/sequential-posterior-monitoring-contract|The monitoring contract]] makes the state reproducible after corrections.'),
    ('Write the decision record', 'Publish data cutoff, prior rationales, group discrepancy, sensitivity grid, holdout loss, threshold rule, staffing cost assumptions and unresolved case-mix changes. A model can forecast better than a baseline while still failing an important queue check. State which finding drives the action and what additional evidence would change it. [[data-science/decision-objective-and-action-unit|The staffing objective]] remains an operational choice, not a property of Bayes’ rule.')],
    'def audit_rate_model(west, east, prior=(4, 36)):\n    west_events, west_cases = west\n    east_events, east_cases = east\n    if min(west_cases, east_cases, *prior) <= 0:\n        raise ValueError("positive group sizes and prior shapes required")\n    if not (0 <= west_events <= west_cases and 0 <= east_events <= east_cases):\n        raise ValueError("invalid group counts")\n    events = west_events + east_events\n    cases = west_cases + east_cases\n    return {"events": events, "cases": cases,\n            "posterior": (prior[0] + events, prior[1] + cases - events),\n            "observed_gap": west_events / west_cases - east_events / east_cases}\n\npacket = audit_rate_model((8, 17), (3, 36))\nassert packet["events"] == 11 and packet["cases"] == 53\nassert packet["posterior"] == (15, 78)',
    'Group reconciliation is O(G) for G queues; the two-queue fixture is O(1). Posterior replication adds O(SN) work for S simulations and N cases, while scoring a future period is O(N). Human review of outcome maturity, prior relevance and action cost is essential.',
    ['Do not use holdout labels to tune the prior before scoring.', 'Do not treat an overall rate fit as proof of queue-level fit.', 'Do not publish an action without the cohort, prior and checkpoint history.'],
    ['data-science/posterior-predictive-group-discrepancy','data-science/prior-sensitivity-for-action-thresholds','data-science/held-out-predictive-log-score','data-science/sequential-posterior-monitoring-contract'])

assert len(lessons) == len(new_paths) == 5
assert {item['path'] for item in lessons} == new_paths
titles = {path: row['title'] for path, row in by_path.items()}
titles.update({item['path']: item['title'] for item in lessons})

def prose(value):
    return re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',
                  lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                  html.escape(value))

def links(paths):
    return '<ul>' + ''.join('<li><a href="/' + path + '">' + html.escape(titles[path]) + '</a></li>'
                            for path in paths) + '</ul>'

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
               difficulty='Intermediate', tags=['ai-data', 'data-science'], potd_date=None,
               featured=False, sort_order=12600 + index, status='published', published_at=stamp,
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
module_paths = {path for module in hub['data']['modules'] for path in module['lessons']}
if not set(tutorial_paths).issubset(module_paths):
    hub['data']['modules'].insert(-1, {'title':'Bayesian model checks and monitoring',
                                      'summary':'Criticize model fit, stress priors, score future cases and replay mature batches.',
                                      'lessons':tutorial_paths})
apply_module = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
if project_path not in apply_module['lessons']:
    apply_module['lessons'].append(project_path)
if '<h2>Bayesian model checks and monitoring</h2>' not in hub['body']:
    hub['body'] += ('<h2>Bayesian model checks and monitoring</h2>' + links(tutorial_paths)
                    + '<h2>Support rate model-checking project</h2>' + links([project_path]))
hub['updated_at'] = stamp

project_hub = by_path[project_hub_path]
if project_path not in project_hub['data']['modules'][0]['lessons']:
    project_hub['data']['modules'][0]['lessons'].append(project_path)
if '<h2>Support rate model-checking project</h2>' not in project_hub['body']:
    project_hub['body'] += '<h2>Support rate model-checking project</h2>' + links([project_path])
project_hub['updated_at'] = stamp

for source, target in [
    ('data-science/shared-priors-and-partial-pooling-limits', tutorial_paths[0]),
    ('data-science/prior-predictive-checks-for-event-rates', tutorial_paths[1]),
    ('data-science/posterior-intervals-and-decision-probabilities', tutorial_paths[2]),
    ('data-science/beta-binomial-updating-and-effective-prior-size', tutorial_paths[3]),
    ('data-science/support-escalation-bayesian-monitoring-project', project_path),
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
