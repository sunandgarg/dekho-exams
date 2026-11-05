"""Build an original Bayesian decision sequence in the Data Science path."""
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
    'prior-predictive-checks-for-event-rates',
    'beta-binomial-updating-and-effective-prior-size',
    'posterior-intervals-and-decision-probabilities',
    'shared-priors-and-partial-pooling-limits',
    'support-escalation-bayesian-monitoring-project',
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

add('prior-predictive-checks-for-event-rates',
    'Prior predictive checks for a binary service rate',
    'A prior is a probability model written before the current outcomes are seen; test the outcomes it implies before updating it.', [
    ('Define the event and sampling unit', 'A support audit labels a checked case as escalated or not escalated within seven days. One case contributes one binary outcome, and the parameter is the escalation probability for the eligible case population during that period. A beta prior represents uncertainty about that probability. It does not fix the probability for every customer segment or solve an incomplete sampling frame. [[data-science/sampling-frame-and-coverage-error|Coverage checks]] come first.'),
    ('Choose parameters on the outcome scale', 'Suppose an earlier, comparable operating period suggests a rate near 10%. Beta(3, 27) has mean 3/30, or 10%, and concentration 30. That concentration affects how strongly the prior influences small samples; it is not a claim that exactly 30 historical cases existed. Record the origin of this belief, population match and review date. A prior borrowed from a different queue can be systematically wrong.'),
    ('Simulate the audit before it happens', 'For each possible rate drawn from the prior, simulate the number of escalations in a 47-case audit. Inspect the range and extremes. A prior that frequently predicts implausible audit counts needs revision before looking at the current labels. The exact probability of zero escalations under this prior is roughly 5.2%. That calculation is a prior predictive probability, not the chance that the true rate is zero.'),
    ('Check competing priors', 'Compare a concentrated Beta(3, 27) with a weaker prior that has the same mean, such as Beta(1, 9). They predict the same average rate but different variation across repeated audits. Ask whether both are plausible given expected changes in staffing, case mix and policy. [[data-science/beta-binomial-updating-and-effective-prior-size|Updating]] later combines these assumptions with observed counts; it cannot make a poor prior choice disappear from a tiny audit.'),
    ('Preserve the pre-data record', 'Save the outcome definition, audit eligibility rule, prior parameters, predictive checks and reasons for accepting or revising the prior. If the current data influenced the prior, disclose that dependence and avoid counting the same evidence twice. For a new queue with no credible prior period, use a weak, defensible prior and present sensitivity to alternatives.')],
    'def prior_probability_of_zero_events(alpha, beta, audit_cases):\n    if alpha <= 0 or beta <= 0 or audit_cases < 0:\n        raise ValueError("positive beta shapes and nonnegative case count required")\n    probability = 1.0\n    for completed_cases in range(audit_cases):\n        probability *= (beta + completed_cases) / (alpha + beta + completed_cases)\n    return probability\n\nzero_event_probability = prior_probability_of_zero_events(3, 27, 47)\nassert round(zero_event_probability, 3) == 0.052',
    'The product uses O(N) time and O(1) space for N audit cases. With a very large N, multiply in log space to reduce underflow. Prior predictive simulation over S audits adds O(SN) draws if every case is generated individually.',
    ['Do not choose the prior after seeing the current audit and present it as independent.', 'Do not interpret prior concentration as literal historical case count.', 'Do not let a rate prior conceal a broken sampling frame.'],
    ['data-science/beta-binomial-updating-and-effective-prior-size','data-science/posterior-intervals-and-decision-probabilities','data-science/shared-priors-and-partial-pooling-limits','data-science/support-escalation-bayesian-monitoring-project'])

add('beta-binomial-updating-and-effective-prior-size',
    'Beta-binomial updating with an auditable case count',
    'A beta prior and binary audit outcomes produce a beta posterior whose parameters add observed event and non-event counts.', [
    ('Freeze the likelihood', 'Assume each audited eligible case has a binary seven-day escalation outcome and, conditional on one stable rate, the cases are exchangeable. If cases cluster by customer or the rate changes during the audit, a single binomial likelihood is a convenience that needs checking. An audit of 47 cases with six escalations contains 41 non-escalations. The numerator and denominator must come from the same eligible cohort. [[data-science/metric-denominator-and-cohort|Cohort rules]] prevent a silent denominator change.'),
    ('Apply the conjugate update', 'Starting with Beta(3, 27), six events and 41 non-events yield Beta(9, 68). The posterior mean is 9/77, about 11.7%; the raw audit share is 6/47, about 12.8%. The difference reflects the prior. It is not a correction for selection bias, label error or late outcome arrival. Those need separate analysis.'),
    ('Explain effective prior size without a fable', 'The shape sum, 30, controls the weight of the prior mean in the posterior mean: 30/77 times 10%, plus 47/77 times 6/47. This algebra can be described as an effective prior sample size under this model, but the shapes are distribution parameters rather than 30 actual past observations. If prior evidence comes from an overlapping sample, adding the same cases again double-counts them.'),
    ('Check sequential consistency', 'Process the first audit batch and then the second, or combine their event and non-event totals before updating. Both paths give the same Beta(9, 68) posterior when the prior is used once and the likelihood assumptions hold. This makes a useful data-pipeline assertion. Save batch IDs so retries do not update the posterior twice. [[data-science/reproducible-analysis-snapshot|Snapshot lineage]] makes a later correction traceable.'),
    ('Look beyond the posterior mean', 'Two audits can share a similar posterior mean while having very different uncertainty because their sample sizes differ. Report the full posterior or an interval with the mean. Check whether the audit could plausibly be generated under the model. If queues have different rates, [[data-science/shared-priors-and-partial-pooling-limits|group-level analysis]] may be more informative than a single pooled rate.')],
    'def update_beta_rate(prior_alpha, prior_beta, escalated_cases, audited_cases):\n    if prior_alpha <= 0 or prior_beta <= 0:\n        raise ValueError("prior shapes must be positive")\n    if not 0 <= escalated_cases <= audited_cases:\n        raise ValueError("events must fit within audited cases")\n    return prior_alpha + escalated_cases, prior_beta + audited_cases - escalated_cases\n\nfirst = update_beta_rate(3, 27, 2, 17)\nsecond = update_beta_rate(*first, 4, 30)\nassert second == update_beta_rate(3, 27, 6, 47) == (9, 68)\nassert round(second[0] / sum(second), 3) == 0.117',
    'One update takes O(1) time and space. Updating B batches costs O(B). The important operational cost is preserving unique batch identity and outcome maturity; duplicate or premature labels change the posterior even though the arithmetic remains valid.',
    ['Do not add the same audit batch twice.', 'Do not treat a posterior mean as a correction for missing or mislabeled outcomes.', 'Do not claim a stable common rate when case mix or time materially changes it.'],
    ['data-science/prior-predictive-checks-for-event-rates','data-science/posterior-intervals-and-decision-probabilities','data-science/shared-priors-and-partial-pooling-limits','data-science/support-escalation-bayesian-monitoring-project'])

add('posterior-intervals-and-decision-probabilities',
    'Posterior intervals and threshold decisions',
    'A posterior distribution can answer conditional probability questions about a rate and support a stated decision rule.', [
    ('Report an interval with its model', 'After six escalations among 47 audited cases and a Beta(3, 27) prior, the posterior is Beta(9, 68). An equal-tail 80% credible interval encloses the middle 80% of probability under that posterior. Its interpretation is conditional on the prior, the binomial likelihood, valid labels and the selected cohort. It is not a promise that 80% of future observed audit shares fall in that interval.'),
    ('Compute a probability that matches the action', 'Suppose leadership adds review capacity if the escalation rate probably exceeds 15%. Calculate posterior probability that the underlying rate exceeds 15%, then compare it with a decision threshold fixed before seeing the result. That probability is about the model parameter, not the probability that a randomly selected case escalates. [[data-science/decision-objective-and-action-unit|The action objective]] should explain why a threshold crossing changes staffing.'),
    ('Separate parameter and predictive uncertainty', 'A future 47-case audit has two sources of variation: uncertainty about the rate and random case outcomes conditional on that rate. A credible interval for the rate does not directly describe future escalation counts. To forecast counts, draw a rate from the posterior and then draw binary outcomes, or use the beta-binomial predictive distribution. Check predicted counts against held-out periods where possible.'),
    ('Treat Monte Carlo as an approximation', 'A standard-library sampler can draw many rates from the beta posterior. Sort them for equal-tail quantiles and count draws above a threshold. Repeating with a fixed seed makes a lesson reproducible, while a larger number of draws reduces Monte Carlo noise. A production report should state the random seed, draw count and numerical precision, or use a vetted distribution implementation.'),
    ('Test prior sensitivity', 'Recalculate interval and threshold probability under a weaker reasonable prior. If the staffing decision changes, the sample has not overwhelmed prior choice; say so. [[data-science/prior-predictive-checks-for-event-rates|The prior predictive check]] helps rule out implausible priors before the audit. Never substitute a posterior probability for the cost analysis of false alarms and missed escalations.')],
    'from random import Random\n\ndef posterior_rate_summary(alpha, beta, threshold, draws=20000, seed=47):\n    if alpha <= 0 or beta <= 0 or not 0 <= threshold <= 1 or draws < 100:\n        raise ValueError("invalid posterior summary request")\n    generator = Random(seed)\n    rates = sorted(generator.betavariate(alpha, beta) for _ in range(draws))\n    return {"mean": alpha / (alpha + beta),\n            "middle_80": (rates[int(draws * 0.10)], rates[int(draws * 0.90)]),\n            "probability_above": sum(rate > threshold for rate in rates) / draws}\n\nsummary = posterior_rate_summary(9, 68, 0.15)\nassert 0 < summary["middle_80"][0] < summary["mean"]\nassert summary["mean"] < summary["middle_80"][1] < 1\nassert 0 <= summary["probability_above"] <= 1',
    'Generating and sorting S beta draws costs O(S log S) time and O(S) memory. A direct distribution quantile and survival function can avoid simulation for this conjugate case. The example intentionally keeps the numerical method visible.',
    ['Do not describe a credible interval as a confidence interval with identical interpretation.', 'Do not read a parameter probability as a future case probability.', 'Do not choose a decision cutoff after inspecting which action the posterior favors.'],
    ['data-science/prior-predictive-checks-for-event-rates','data-science/beta-binomial-updating-and-effective-prior-size','data-science/shared-priors-and-partial-pooling-limits','data-science/support-escalation-bayesian-monitoring-project'])

add('shared-priors-and-partial-pooling-limits',
    'Shared priors, shrinkage and the limits of fixed pooling',
    'A shared prior pulls sparse group estimates toward a common rate, but a fixed shared prior is only a baseline for a hierarchical model.', [
    ('Identify the group comparison', 'In one period, the North queue has four escalations in six audited cases; South has two in 41. Raw shares are 66.7% and 4.9%, respectively. North is so small that a raw rank can swing with one case. Yet pooling all 47 cases into a single 12.8% rate hides the observed difference. The question is whether each queue needs its own staffing response and how much uncertainty that response can tolerate.'),
    ('Apply a fixed shared prior as a baseline', 'Using Beta(3, 27) independently for each queue yields posterior means 7/36, about 19.4%, for North and 5/71, about 7.0%, for South. The small North sample moves more toward the prior mean than a large sample would. This is shrinkage under a fixed prior whose parameters came from an earlier comparable period; it is not a jointly fitted hierarchical posterior. [[data-science/beta-binomial-updating-and-effective-prior-size|The update rule]] is unchanged.'),
    ('Distinguish actual hierarchical learning', 'In a hierarchical model, group rates share a population distribution and its parameters are estimated with uncertainty. The data help determine how much pooling is appropriate. A fixed shared prior cannot learn that groups are more dispersed than expected. If North truly operates under a distinct policy or customer mix, forcing it toward the common mean may hide an issue. Group definitions and outcome windows must be comparable before sharing information.'),
    ('Check the prior against both groups', 'The North observation of four events in six cases may be surprising under a prior centered at 10%. Examine the prior predictive probability of such counts and posterior predictive replication. It may reflect random noise, a changed queue, or a poor prior. A posterior mean alone cannot tell which. [[data-science/prior-predictive-checks-for-event-rates|Prior predictive checks]] and an operational investigation should accompany escalation.'),
    ('Decide with uncertainty, not a league table', 'Publish each group’s event count, audited denominator, posterior distribution and prior source. If a small group crosses an action threshold only under one prior choice, mark the decision as sensitive and collect more cases. Avoid ranking groups by point estimates without accounting for the large and unequal uncertainty. [[data-science/posterior-intervals-and-decision-probabilities|Threshold probabilities]] can be reported per group with one predeclared rule.')],
    'def fixed_prior_group_means(group_counts, prior_alpha=3, prior_beta=27):\n    if prior_alpha <= 0 or prior_beta <= 0:\n        raise ValueError("prior shapes must be positive")\n    means = {}\n    for queue_name, (escalated, audited) in group_counts.items():\n        if not 0 <= escalated <= audited:\n            raise ValueError("invalid group counts")\n        means[queue_name] = (prior_alpha + escalated) / (prior_alpha + prior_beta + audited)\n    return means\n\nqueue_means = fixed_prior_group_means({"North": (4, 6), "South": (2, 41)})\nassert round(queue_means["North"], 3) == 0.194\nassert round(queue_means["South"], 3) == 0.070',
    'Fixed-prior updates cost O(G) time and output space for G groups. A full hierarchical model requires fitting shared parameters, checking numerical diagnostics and simulating predictions; its cost depends on group count, parameterization and inference method.',
    ['Do not label fixed-prior updates as a fitted hierarchical model.', 'Do not shrink a genuinely different operating group into an unrelated population.', 'Do not rank tiny groups by raw event share without showing uncertainty.'],
    ['data-science/prior-predictive-checks-for-event-rates','data-science/beta-binomial-updating-and-effective-prior-size','data-science/posterior-intervals-and-decision-probabilities','data-science/support-escalation-bayesian-monitoring-project'])

add('support-escalation-bayesian-monitoring-project',
    'Project: Bayesian monitoring of support escalations',
    'Build an auditable event-rate report with a predeclared prior, posterior decision rule and queue-level stress checks.', [
    ('Lock the audit contract', 'Define one case as one eligible support ticket closed during a fixed intake period, with a seven-day escalation window. Exclude cases whose window has not matured, and deduplicate reopened tickets by the approved case identifier. Use a 47-case mature audit with six escalations as the fixture. Divide it into North, four of six, and South, two of 41, so group totals reconcile to the overall count. [[data-science/metric-denominator-and-cohort|Cohort definitions]] remain visible in every report.'),
    ('Review the prior before labels', 'Declare Beta(3, 27) from an earlier comparable period and test its implied distribution over 47-case audit counts. Compare with a weaker Beta(1, 9) prior sharing the same mean. Save both choices and the reason for preferring one before current escalation labels are opened. [[data-science/prior-predictive-checks-for-event-rates|Predictive checking]] is part of the project record, not a retrospective story.'),
    ('Update with reconciled counts', 'Compute Beta(9, 68) for the overall cohort and group posteriors separately. Assert that 6 + 41 equals 47, that the group event totals equal six, and that processing two batches reaches the same posterior as a combined update. Store batch IDs to make retries idempotent. [[data-science/beta-binomial-updating-and-effective-prior-size|The update lesson]] gives the arithmetic and its assumptions.'),
    ('Publish decision uncertainty', 'For the overall rate, report the posterior mean, an equal-tail 80% credible interval, and probability that the rate exceeds a predeclared 15% review trigger. Show how this probability moves under the weaker prior. Compare North and South with denominators and intervals rather than point-estimate ranks. [[data-science/posterior-intervals-and-decision-probabilities|The interval lesson]] keeps parameter and future-count uncertainty distinct.'),
    ('Audit model fit and operational choice', 'Simulate future audit counts from the posterior and compare with the next matured period. Check whether North’s high event count is plausible under the shared prior; investigate policy or case-mix changes before relying on shrinkage. Release a short decision note with staffing action, assumed costs, data snapshot, prior version and unresolved limits. [[data-science/shared-priors-and-partial-pooling-limits|Shared-prior limits]] govern the queue interpretation.')],
    'def reconcile_audit(group_counts, expected_cases, expected_escalations):\n    audited = sum(cases for events, cases in group_counts.values())\n    escalated = sum(events for events, cases in group_counts.values())\n    if any(not 0 <= events <= cases for events, cases in group_counts.values()):\n        raise ValueError("invalid group counts")\n    if (audited, escalated) != (expected_cases, expected_escalations):\n        raise ValueError("group totals do not match the audit")\n    return 3 + escalated, 27 + audited - escalated\n\nposterior = reconcile_audit({"North": (4, 6), "South": (2, 41)}, 47, 6)\nassert posterior == (9, 68)',
    'Reconciliation over G groups costs O(G) time and O(1) extra space. Posterior simulation with S draws costs at least O(S); sorting draws for intervals costs O(S log S). Most project effort is checking case identity, outcome maturity and prior applicability.',
    ['Do not update with unresolved seven-day outcomes.', 'Do not count reopened cases twice.', 'Do not present shared-prior shrinkage as proof that queues have the same true rate.'],
    ['data-science/prior-predictive-checks-for-event-rates','data-science/beta-binomial-updating-and-effective-prior-size','data-science/posterior-intervals-and-decision-probabilities','data-science/shared-priors-and-partial-pooling-limits'])

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
               featured=False, sort_order=12400 + index, status='published', published_at=stamp,
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
    hub['data']['modules'].insert(-1, {'title':'Bayesian event-rate analysis',
                                      'summary':'Check priors, update event rates, quantify decisions and inspect group pooling.',
                                      'lessons':tutorial_paths})
apply_module = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
if project_path not in apply_module['lessons']:
    apply_module['lessons'].append(project_path)
if '<h2>Bayesian event-rate analysis</h2>' not in hub['body']:
    hub['body'] += ('<h2>Bayesian event-rate analysis</h2>' + links(tutorial_paths)
                    + '<h2>Bayesian escalation project</h2>' + links([project_path]))
hub['updated_at'] = stamp

project_hub = by_path[project_hub_path]
if project_path not in project_hub['data']['modules'][0]['lessons']:
    project_hub['data']['modules'][0]['lessons'].append(project_path)
if '<h2>Bayesian escalation project</h2>' not in project_hub['body']:
    project_hub['body'] += '<h2>Bayesian escalation project</h2>' + links([project_path])
project_hub['updated_at'] = stamp

for source, target in [
    ('data-science/precision-budget-and-effective-sample-size', tutorial_paths[0]),
    ('data-science/reproducible-analysis-snapshot', tutorial_paths[1]),
    ('data-science/bootstrap-interval-interpretation', tutorial_paths[2]),
    ('data-science/subgroup-distribution-and-aggregation-reversal', tutorial_paths[3]),
    ('data-science/support-case-audit-sampling-project', project_path),
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
