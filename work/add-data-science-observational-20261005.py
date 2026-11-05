"""Add original Data Science lessons on observational evidence."""
import datetime
import html
import json
from pathlib import Path
import re
import uuid

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
slugs = (
    'cohort-entry-and-survivorship-bias',
    'right-censoring-and-time-to-event',
    'proxy-measurement-and-label-error',
    'sensitivity-analysis-and-decision-stability',
    'support-resolution-cohort-project',
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

add('cohort-entry-and-survivorship-bias',
    'Cohort entry and survivorship bias: count the cases that could fail',
    'A cohort starts when units become eligible, not when their outcomes become convenient to observe.', [
    ('Choose a common starting event', 'A support dashboard claims that 94% of cases resolve within two days. Its query starts from cases marked resolved, so open cases never enter the denominator. The issue is selection: the dashboard conditions on reaching the favorable outcome. Start instead with every eligible case submitted during a fixed intake window. Record case ID, submission time, channel and any exclusions known at entry. [[data-science/metric-denominator-and-cohort|A cohort denominator]] must be chosen before resolution status is inspected.'),
    ('Align follow-up time', 'Cases submitted on the last day have less opportunity to resolve than cases submitted on the first. Freeze an analysis cutoff and compute follow-up from each submission to resolution or cutoff. For a strict two-day outcome, include only cases that had a full two-day observation window, or use a method designed for incomplete follow-up. Dropping open cases is never equivalent. If cases may re-open, define whether the first resolution, final resolution or durable resolution is the event.'),
    ('Trace attrition', 'Build a cohort ledger: 237 intake IDs, 11 excluded by a predeclared spam rule, 226 eligible, 178 resolved by cutoff and 48 still open. Among those eligible, 151 resolved within two days. The naive completed-case figure is 151/178, about 84.8%; the observed two-day fraction over all eligible cases is 151/226, about 66.8%, but it is only a final two-day outcome for cases with enough follow-up. Show a follow-up-eligible denominator separately. [[data-science/right-censoring-and-time-to-event|Censoring]] handles the remaining observation problem.'),
    ('Test whether groups enter differently', 'Compare channel, priority and submission week for eligible, excluded, resolved and open cases. A self-service route may close easy requests without agent assignment; an export of agent cases omits it. That is a frame error layered on top of survivorship. Keep the exclusion ledger and the intake snapshot so an analyst can reconstruct every denominator. [[data-science/sampling-frame-and-coverage-error|Frame coverage]] sets the outer boundary of the claim.'),
    ('State the claim at its proper scope', 'The completed-case figure describes completed cases only. A cohort resolution measure describes intake cases subject to a declared follow-up rule. Neither number establishes that a new workflow caused improvement: case mix, staffing and seasonality can change together. Publish counts beside rates, and refuse a single headline when the denominator is still moving.')],
    'def cohort_state(cases, analysis_cutoff):\n    summary = {"eligible": 0, "resolved": 0, "open": 0}\n    for case in cases:\n        if case["submitted_at"] > analysis_cutoff or case["spam_at_entry"]:\n            continue\n        summary["eligible"] += 1\n        resolved_at = case["resolved_at"]\n        if resolved_at is not None and resolved_at <= analysis_cutoff:\n            summary["resolved"] += 1\n        else:\n            summary["open"] += 1\n    assert summary["eligible"] == summary["resolved"] + summary["open"]\n    return summary',
    'One pass over N intake cases costs O(N) time and O(1) auxiliary space. A production cohort ledger stores one state and an exclusion reason per case, requiring O(N) space; timestamp normalization and duplicate identity resolution happen before this pass.',
    ['Do not use resolved cases as the denominator for an intake-cohort resolution claim.', 'Do not grant late entrants the same follow-up time as early entrants.', 'Do not infer a workflow effect from a before-and-after cohort without checking composition and concurrent changes.'],
    ['data-science/right-censoring-and-time-to-event','data-science/metric-denominator-and-cohort','data-science/sampling-frame-and-coverage-error','data-science/support-resolution-cohort-project'])

add('right-censoring-and-time-to-event',
    'Right censoring and time-to-event analysis for open cases',
    'A case still open at the analysis cutoff has a known observed duration but an unknown final resolution time.', [
    ('Preserve the unknown', 'If a case was submitted 31 hours before the snapshot and remains open, its resolution time exceeds 31 hours. It is not a zero-hour resolution, and it is not necessarily a failure at 48 hours. Store the observed duration together with an event indicator. [[data-science/cohort-entry-and-survivorship-bias|Cohort entry]] fixes when its clock began; the snapshot fixes where observation stopped.'),
    ('Construct risk sets', 'At each observed resolution time, count cases still under observation immediately beforehand and the resolutions at that time. A product of one minus events divided by the risk-set count estimates the chance of remaining unresolved past successive event times. Censored cases contribute exposure until their censoring time, then leave the risk set. Ties require a declared ordering rule. The simple function below computes this product for nonnegative durations and binary event indicators.'),
    ('Check the censoring assumption', 'This estimate needs censoring that is independent of future resolution, at least within any groups used for adjustment. A fixed administrative cutoff may be plausible, but cases abandoned because they are unusually difficult create a different problem. Report reasons for censoring and compare their distribution by channel and priority. If follow-up starts after submission for some cases, delayed entry needs explicit handling; the simple example does not support it.'),
    ('Read the curve with care', 'Suppose seven cases have observed durations of 8, 13, 21, 34, 38, 53 and 61 hours; the 38- and 61-hour observations are censored. Do not average the five observed resolution times and call that the mean cohort resolution time. A survival curve can estimate the unresolved share at a stated horizon if that horizon is observed, but its far tail is fragile when few cases remain at risk. Show the at-risk count beside any reported horizon.'),
    ('Tie estimates to service decisions', 'For a 48-hour service promise, report the estimated unresolved fraction at 48 hours and the number still at risk just before that point. Compare route or priority groups only after confirming their cohort-entry rules and follow-up periods match. [[data-science/sensitivity-analysis-and-decision-stability|Sensitivity analysis]] should show whether plausible informative censoring would change a staffing decision.')],
    'from collections import Counter\nfrom math import isclose\n\ndef unresolved_curve(observed_cases):\n    if any(duration < 0 or event not in (0, 1) for duration, event in observed_cases):\n        raise ValueError("invalid duration or event indicator")\n    risk = len(observed_cases)\n    survival = 1.0\n    points = []\n    event_counts = Counter(duration for duration, event in observed_cases if event)\n    censor_counts = Counter(duration for duration, event in observed_cases if not event)\n    for duration in sorted(event_counts.keys() | censor_counts.keys()):\n        events = event_counts[duration]\n        if events:\n            survival *= 1 - events / risk\n            points.append((duration, survival, risk))\n        risk -= events + censor_counts[duration]\n    return points\n\nfirst_time, first_unresolved, first_risk = unresolved_curve([(8, 1), (13, 1), (21, 0)])[0]\nassert first_time == 8 and first_risk == 3 and isclose(first_unresolved, 2 / 3)',
    'Counting N records costs O(N) expected time and O(N) space; sorting distinct times costs O(U log U) for U unique durations. The implementation illustrates administrative right censoring and does not handle delayed entry, competing events, sampling weights or interval-censored times.',
    ['Do not replace unknown final durations with the snapshot duration in an ordinary mean.', 'Do not interpret a far-tail estimate without the at-risk count.', 'Do not assume censoring is harmless when difficult cases leave observation early.'],
    ['data-science/cohort-entry-and-survivorship-bias','data-science/sensitivity-analysis-and-decision-stability','data-science/bootstrap-interval-interpretation','data-science/support-resolution-cohort-project'])

add('proxy-measurement-and-label-error',
    'Proxy measurements and label error in operational datasets',
    'A recorded field may be a convenient proxy for the decision quantity rather than a faithful measurement of it.', [
    ('Name the hidden quantity', 'A support team wants to measure whether a customer issue was solved. The ticket field marked closed is easy to query, but closure may mean an agent sent a reply, not that the customer confirmed a fix. Declare the intended outcome and the recorded proxy separately. A good database join cannot make a poor proxy valid. [[data-science/dataset-grain-and-join-cardinality|One row per case]] is necessary, but it does not settle what each field means.'),
    ('Audit disagreement with independent review', 'Draw a review sample from the full eligible frame, including open and closed cases. Reviewers inspect source conversation and later contact without seeing the proxy label where possible. Build a two-by-two count of proxy positive or negative against reviewed positive or negative, plus unknown review outcomes. If 47 reviewed cases contain 29 proxy-closed cases and only 22 genuinely solved cases, the difference in totals alone cannot tell which individual cases were misclassified; retain the paired labels.'),
    ('Look for differential error', 'A closure field may be more accurate for email than chat, or for low-priority cases than urgent cases. Compare disagreement by channel, agent workflow and week. If the error rate changes at the same time as a product change, a trend in the proxy can masquerade as a trend in real outcomes. A reviewer can also err, so document adjudication and any later outcome evidence. [[data-annotation/agreement-and-disagreement-review|Disagreement review]] is part of the measurement contract.'),
    ('Bound what can be claimed', 'Report the raw proxy rate, the paired audit counts and the estimated reviewed rate under the sampling design. Avoid silently substituting one for another. If a rare segment has only three reviewed cases, its apparent correction factor is unstable. A population adjustment based on an audit needs valid inclusion probabilities and a defensible error model; without those, present a sensitivity range. [[data-science/stratified-sampling-and-design-weights|Design weights]] matter when audit strata were sampled unequally.'),
    ('Choose a repairable process', 'Sometimes a better event can be captured prospectively: confirmed fix, no repeat contact within a declared window, or a customer response. Each alternative has its own missingness and delay. Version the outcome rule and run old and new definitions in parallel before comparing periods. A metric definition change is a measurement change, not automatically an improvement in service.')],
    'def paired_label_counts(reviewed_cases):\n    counts = {"true_positive": 0, "false_positive": 0,\n              "false_negative": 0, "true_negative": 0, "unknown": 0}\n    for case in reviewed_cases:\n        reviewed = case["reviewed_solved"]\n        if reviewed is None:\n            counts["unknown"] += 1\n            continue\n        proxy = bool(case["ticket_closed"])\n        key = ("true_positive" if proxy else "false_negative") if reviewed else ("false_positive" if proxy else "true_negative")\n        counts[key] += 1\n    return counts',
    'Pairing N reviewed cases costs O(N) time and O(1) auxiliary space after identities are joined. The audit itself costs reviewer time and may require delayed follow-up; disagreement by K strata needs O(K) additional counters and enough cases per stratum to be informative.',
    ['Do not treat a convenient status field as the outcome without an audit.', 'Do not discard unknown reviewed outcomes from the audit ledger.', 'Do not apply one correction factor across channels when error rates may differ.'],
    ['data-science/sensitivity-analysis-and-decision-stability','data-science/nonresponse-bias-and-follow-up','data-annotation/agreement-and-disagreement-review','data-science/support-resolution-cohort-project'])

add('sensitivity-analysis-and-decision-stability',
    'Sensitivity analysis: find which assumptions can reverse a decision',
    'A sensitivity check changes uncertain assumptions while keeping the target question and observed evidence fixed.', [
    ('List uncertainties before scenarios', 'A support-cohort estimate may depend on unresolved cases, imperfect closure labels and an incomplete self-service channel. Name each uncertainty and its plausible range using audit evidence or a documented operating limit. Do not select the range after seeing which result favors a proposed launch. [[data-science/proxy-measurement-and-label-error|Proxy error]] and [[data-science/nonresponse-bias-and-follow-up|missing outcomes]] are separate dimensions.'),
    ('Calculate a decision boundary', 'Suppose 86 of 143 fully observed eligible cases met a two-day service target, while 19 cases lack final confirmation. If all 19 failed, the rate over 162 cases is 86/162, about 53.1%. If all 19 succeeded, it is 105/162, about 64.8%. A policy requires at least 60%. That decision can flip under the missing outcomes; the correct report is a range and the number of additional confirmations needed to narrow it.'),
    ('Change one assumption, then combine', 'Vary follow-up classification, proxy-label correction and frame coverage individually first. This reveals which uncertainty drives the conclusion. Then evaluate coherent combinations: difficult cases may both remain unresolved and be absent from the easy-to-query export, so independent best-case assumptions are implausible. Keep each scenario’s denominator and cohort rule visible. If weights change, recompute the weighted rate rather than editing a rounded headline.'),
    ('Separate uncertainty types', 'A bootstrap interval describes sampling variation under its design assumptions. A sensitivity range describes how a result moves under stated deviations from uncertain assumptions. Neither substitutes for the other. An interval can be narrow around a biased proxy, and a wide sensitivity range can persist with thousands of observations. [[data-science/bootstrap-interval-interpretation|Resampling at the right unit]] addresses only one part of the problem.'),
    ('Make the next measurement actionable', 'If the decision remains the same across credible scenarios, record that stability and the assumptions tested. If it flips, state the smallest new observation that would resolve the uncertainty: recontact a random subset of the 19, review closure labels by channel, or recover missing intake IDs. Order that work by expected decision value, not by how easy a chart is to draw.')],
    'def binary_missing_outcome_range(success_count, observed_count, missing_count):\n    if not 0 <= success_count <= observed_count or missing_count < 0:\n        raise ValueError("invalid cohort counts")\n    total = observed_count + missing_count\n    if total == 0:\n        raise ValueError("empty cohort")\n    return success_count / total, (success_count + missing_count) / total\n\nlow, high = binary_missing_outcome_range(86, 143, 19)\nassert round(low, 3) == 0.531 and round(high, 3) == 0.648',
    'A single binary bound takes O(1) time and space. A grid of A × B × C assumption settings costs O(ABC) evaluations and can grow quickly; predeclare a small, interpretable range and preserve the scenario inputs with each output.',
    ['Do not describe an assumption range as a confidence interval.', 'Do not choose only scenarios that support the desired decision.', 'Do not vary a numerator without updating the corresponding denominator and cohort definition.'],
    ['data-science/proxy-measurement-and-label-error','data-science/right-censoring-and-time-to-event','data-science/bootstrap-interval-interpretation','data-science/support-resolution-cohort-project'])

add('support-resolution-cohort-project',
    'Project: audit support resolution with open cases and imperfect labels',
    'Produce a reviewable cohort analysis that preserves unresolved cases, audits a closure proxy and states when the decision is sensitive.', [
    ('Freeze the intake cohort', 'Create 162 eligible support cases across email, chat and self-service channels. Give every case a stable ID, submission time, channel, priority and analysis cutoff. Include 11 out-of-scope spam records in the raw fixture but not the eligible denominator, plus duplicate status events that must not create duplicate cases. Version the eligibility and exclusion rules. [[data-science/cohort-entry-and-survivorship-bias|Cohort entry]] must be reproducible from the raw event log.'),
    ('Track the observation clock', 'For each eligible case, store observed duration and whether confirmed resolution occurred by cutoff. Include 19 cases without final confirmation, some open and some with missing customer response. Build an unresolved-share curve and an at-risk table through the two-day mark; verify tie handling against a hand-calculated fixture. Do not replace missing final times with the cutoff duration in an ordinary average. [[data-science/right-censoring-and-time-to-event|The censoring lesson]] gives the calculation contract.'),
    ('Audit the outcome proxy', 'Select a fixed review sample across channels. Keep ticket-closed and reviewer-confirmed-solved as separate fields, including unknown review outcomes. Produce paired-label counts and disagreement by channel. Record reviewer guidance and adjudication notes. If chat cases use an automatic close rule, show its effect on the proxy separately from the underlying confirmed outcome. [[data-science/proxy-measurement-and-label-error|The proxy audit]] determines what the closure field can support.'),
    ('Write the decision packet', 'Report the intake count, exclusions, follow-up-eligible count, observed two-day successes, unresolved cases, proxy disagreements and any missing frame segment. Calculate a lower and upper rate under missing outcomes, then test a 60% operating gate. State whether the gate can flip; if it can, specify the follow-up audit that would be worth doing next. Do not replace the range with one favorable point estimate.'),
    ('Verify the work', 'Save the raw fixture, code revision, snapshot cutoff, cohort ledger, review sample selection, scenario parameters and outputs. Include assertions that eligible equals resolved plus open at cutoff; that paired review counts equal all selected review records; and that each scenario preserves the original cohort denominator. A peer should reproduce every headline count without a dashboard or private database.')],
    'def decision_state(success_count, observed_count, unresolved_count, required_rate):\n    if not 0 <= success_count <= observed_count or unresolved_count < 0:\n        raise ValueError("invalid counts")\n    total = observed_count + unresolved_count\n    if total == 0:\n        raise ValueError("empty cohort")\n    lower = success_count / total\n    upper = (success_count + unresolved_count) / total\n    return {"lower_rate": lower, "upper_rate": upper,\n            "decision_stable": lower >= required_rate or upper < required_rate}\n\nassert decision_state(86, 143, 19, 0.60)["decision_stable"] is False',
    'Cohort construction and paired-label reconciliation scan N events in O(N) expected time with ID indexes and O(N) storage. Sorting event durations for the unresolved-share curve costs O(N log N). Reviewer labor and delayed follow-up dominate compute cost; budget them explicitly.',
    ['Do not silently discard cases without final confirmation.', 'Do not collapse closure and confirmed resolution into one field.', 'Do not publish a pass or fail when plausible missing outcomes cross the operating gate.'],
    ['data-science/cohort-entry-and-survivorship-bias','data-science/right-censoring-and-time-to-event','data-science/proxy-measurement-and-label-error','data-science/sensitivity-analysis-and-decision-stability'])

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
               featured=False, sort_order=11700 + index, status='published', published_at=stamp,
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
    hub['data']['modules'].insert(-1, {'title':'Observational evidence and decision sensitivity',
                                      'summary':'Define entry, preserve open outcomes, audit proxy fields and test assumptions.',
                                      'lessons':tutorial_paths})
apply_module = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
if project_path not in apply_module['lessons']:
    apply_module['lessons'].append(project_path)
if '<h2>Observational evidence and decision sensitivity</h2>' not in hub['body']:
    hub['body'] += ('<h2>Observational evidence and decision sensitivity</h2>' + links(tutorial_paths)
                    + '<h2>Support resolution project</h2>' + links([project_path]))
hub['updated_at'] = stamp

project_hub = by_path[project_hub_path]
if project_path not in project_hub['data']['modules'][0]['lessons']:
    project_hub['data']['modules'][0]['lessons'].append(project_path)
if '<h2>Support resolution project</h2>' not in project_hub['body']:
    project_hub['body'] += '<h2>Support resolution project</h2>' + links([project_path])
project_hub['updated_at'] = stamp

for source, target in [
    ('data-science/metric-denominator-and-cohort', tutorial_paths[0]),
    ('data-science/missing-data-policy', tutorial_paths[1]),
    ('data-science/bootstrap-interval-interpretation', tutorial_paths[1]),
    ('data-annotation/agreement-and-disagreement-review', tutorial_paths[2]),
    ('data-science/nonresponse-bias-and-follow-up', tutorial_paths[2]),
    ('data-science/precision-budget-and-effective-sample-size', tutorial_paths[3]),
    ('applied-statistics/confidence-interval-coverage', tutorial_paths[3]),
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
print(json.dumps({'new_articles':len(lessons), 'new_projects':1, 'crosslinks_from_existing':7}))
