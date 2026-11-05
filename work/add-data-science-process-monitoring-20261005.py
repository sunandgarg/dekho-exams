"""Add original process-monitoring lessons and a release project to Data Science."""
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
    'control-limits-versus-service-targets',
    'p-chart-with-changing-daily-denominators',
    'ewma-for-small-persistent-rate-shifts',
    'frozen-baselines-and-alert-investigation',
    'support-breach-process-monitoring-project',
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

add('control-limits-versus-service-targets',
    'Control limits and service targets answer different questions',
    'A control limit describes expected process variation under a frozen baseline, while a service target states an operational requirement.', [
    ('Separate stability from adequacy', 'A support team may have a stable five-percent late-response rate while its contractual target is below three percent. Stability does not make the process acceptable. Conversely, a single late-response rate of 3.4 percent may miss the target without proving a change in the underlying process. Show both judgments: observed rate against the target, and observed rate against a process-monitoring rule. Mixing them creates false alarms or excuses a consistently poor service level. [[data-science/metric-denominator-and-cohort|The metric denominator]] must be fixed first.'),
    ('Choose a meaningful baseline', 'A process baseline should use periods with comparable case eligibility, clocks, staffing and logging. Do not blend a known outage week into the baseline merely because it adds more data. Keep the baseline date range and exclusion rationale in the release packet. A process chart assumes the baseline represents the system whose future variation is being monitored; if a new support policy changes that system, investigate and then deliberately establish a new baseline. [[data-science/instrumentation-change-and-metric-guardrails|Instrumentation changes]] can mimic process changes.'),
    ('Interpret a signal as a prompt to investigate', 'A point outside a three-standard-deviation control limit suggests a special cause under the chart model. It does not identify the cause. Possible explanations include changed queue routing, a real backlog, a bad timestamp, and a denominator extract that lost eligible cases. A point within limits does not prove every case met the target or that the process has no slow drift. [[data-science/frozen-baselines-and-alert-investigation|Alert investigation]] needs evidence beyond the chart.'),
    ('Match chart design to the measurement', 'For a binary late/not-late outcome summarized by day, a proportion chart accounts for the number of cases each day. For a continuous duration, an individuals or subgroup chart needs a different variance model. Do not place a three-sigma band around daily percentages using the raw standard deviation of all individual case flags; the variability of a daily proportion depends on its denominator. [[data-science/p-chart-with-changing-daily-denominators|The p-chart lesson]] makes that dependence explicit.'),
    ('Make the decision rule reviewable', 'Store the target separately from the control center and limits. A day may be marked target miss, process signal, both or neither. This four-way state is more useful than one red/green badge. Confirm who investigates, what evidence they check, and whether an observed breach requires immediate action regardless of statistical signal. [[data-science/support-breach-process-monitoring-project|The project]] turns this into an auditable daily packet.')],
    '''def classify_service_day(late_cases, eligible_cases, target_rate, center, lower, upper):
    if eligible_cases <= 0 or not 0 <= late_cases <= eligible_cases:
        raise ValueError("invalid daily counts")
    if not 0 <= target_rate <= 1 or not 0 <= lower <= center <= upper <= 1:
        raise ValueError("invalid target or control limits")
    observed_rate = late_cases / eligible_cases
    return {"rate": observed_rate,
            "target_miss": observed_rate > target_rate,
            "process_signal": observed_rate < lower or observed_rate > upper}

steady_but_poor = classify_service_day(9, 180, 0.03, 0.05, 0.01, 0.09)
assert steady_but_poor["target_miss"]
assert not steady_but_poor["process_signal"]
unusual_but_on_target = classify_service_day(0, 180, 0.03, 0.05, 0.01, 0.09)
assert not unusual_but_on_target["target_miss"]
assert unusual_but_on_target["process_signal"]''',
    'Classifying D daily summaries is O(D) time and O(D) output space if results are retained. The example takes limits as inputs; choosing and validating the chart model is separate work. A fast alert rule cannot repair an unstable metric definition.',
    ['Do not call an in-control process compliant with its service target.', 'Do not infer a root cause from one chart signal.', 'Do not recompute limits from the same day being judged.'],
    ['data-science/p-chart-with-changing-daily-denominators','data-science/ewma-for-small-persistent-rate-shifts','data-science/frozen-baselines-and-alert-investigation','data-science/support-breach-process-monitoring-project'])

add('p-chart-with-changing-daily-denominators',
    'P-charts with changing daily denominators',
    'A p-chart monitors a binary outcome share and changes its limits with each period’s eligible count, because a small day is noisier than a large one.', [
    ('Pool the baseline by cases', 'For five baseline support days, late and eligible counts are (5,100), (7,120), (6,110), (4,90) and (8,130). The pooled baseline late share is 30/550, about 0.0545. Averaging five daily percentages equally would give small days the same weight as large days and answer a different question. The pooled share is the center line when each eligible case is the Bernoulli unit and baseline periods are comparable. [[data-science/metric-denominator-and-cohort|Eligibility rules]] belong in the chart contract.'),
    ('Recompute limits by day size', 'For a new day with n eligible cases, the simple three-sigma p-chart upper limit is center plus three times the square root of center times (one minus center) divided by n. The lower limit subtracts the same term, clipped at zero; the upper limit is clipped at one. With 140 cases, 12 late responses yield about 0.0857, below the illustrative upper limit. Twenty-one late responses yield 0.15 and exceed it. A 40-case day needs wider limits than a 140-case day.'),
    ('State the distribution assumptions', 'The basic calculation treats cases in a subgroup as Bernoulli trials with a common baseline probability and enough independence for the binomial variance. Repeated contacts from one customer, different queue mixes, and day-level common shocks can produce overdispersion. If those dominate, a simple p-chart may alert too often. Segment comparable queues or use a model that reflects the dependence, and validate the resulting false-alarm behavior on held-out baseline periods.'),
    ('Distinguish early warning from root cause', 'A point above the upper limit is a signal to inspect, not a verdict that staff performed badly. First reconcile eligible counts, missing event timestamps, case creation times and routing versions. Then look at queue mix and known incidents. A rate below the lower limit also matters: it may reflect improvement or a logging outage that stopped recording late cases. [[data-science/frozen-baselines-and-alert-investigation|The investigation lesson]] preserves the evidence trail.'),
    ('Freeze parameters for monitoring', 'Estimate the center from a designated baseline and store its version. During monitoring, hold that center fixed while each new day’s n changes its limits. Recomputing the center after every alert can absorb a real shift into the baseline and erase evidence. Periodically review the model with a documented change process, especially after policy or instrumentation changes. [[data-science/ewma-for-small-persistent-rate-shifts|EWMA monitoring]] asks a different question about smaller sustained shifts.')],
    '''from math import sqrt

def pooled_late_rate(baseline_days):
    if not baseline_days or any(total <= 0 or not 0 <= late <= total
                                for late, total in baseline_days):
        raise ValueError("invalid baseline")
    return sum(late for late, _ in baseline_days) / sum(total for _, total in baseline_days)

def p_chart_signal(late_cases, eligible_cases, baseline_rate):
    if eligible_cases <= 0 or not 0 <= late_cases <= eligible_cases:
        raise ValueError("invalid daily counts")
    if not 0 <= baseline_rate <= 1:
        raise ValueError("invalid baseline rate")
    spread = 3 * sqrt(baseline_rate * (1 - baseline_rate) / eligible_cases)
    lower = max(0.0, baseline_rate - spread)
    upper = min(1.0, baseline_rate + spread)
    rate = late_cases / eligible_cases
    return rate, lower, upper, rate < lower or rate > upper

baseline = [(5, 100), (7, 120), (6, 110), (4, 90), (8, 130)]
center = pooled_late_rate(baseline)
assert center == 30 / 550
assert not p_chart_signal(12, 140, center)[3]
assert p_chart_signal(21, 140, center)[3]''',
    'Pooling B baseline days is O(B) time and O(1) additional space. Scanning D monitoring days is O(D). The simple limits can misbehave with tiny expected counts, clustering or changing case mix; validating the chart model costs more than the arithmetic.',
    ['Do not average daily percentages equally when estimating a case-level center.', 'Do not reuse a fixed daily limit when eligible counts change.', 'Do not assume a binomial model remains valid under strong within-day dependence.'],
    ['data-science/control-limits-versus-service-targets','data-science/ewma-for-small-persistent-rate-shifts','data-science/frozen-baselines-and-alert-investigation','data-science/support-breach-process-monitoring-project'])

add('ewma-for-small-persistent-rate-shifts',
    'EWMA monitoring for small persistent rate shifts',
    'An exponentially weighted moving average combines the current rate with prior monitored values to surface sustained changes that may not trigger a single-day rule.', [
    ('Define the monitored series', 'Suppose each day contains exactly 200 eligible support cases and the established late-response share is 0.05. Let the daily observed share be x. An EWMA updates z to 0.25 times x plus 0.75 times the previous z, starting at the frozen baseline center. A single higher day moves z partway; several higher days accumulate. This is useful for persistent small shifts, provided the baseline process and daily subgroup definition are stable. [[data-science/control-limits-versus-service-targets|The target]] remains a separate operational threshold.'),
    ('Use limits for the statistic being charted', 'The EWMA has less variation than a raw daily proportion because it averages information over time. With independent equal-size daily proportions and baseline Bernoulli variance, its time-t standard deviation includes the factor lambda divided by (two minus lambda) and a startup term that approaches one. Compare z with limits built for z, not the wider p-chart limits for one raw day. A chart can signal from a sustained rise even when each daily value individually stays inside its own limits.'),
    ('Preserve the time order', 'Do not sort days by rate or drop quiet days before updating the state. A late-arriving daily batch requires a controlled replay from the last trusted checkpoint, not insertion into a finished sequence without recalculation. The EWMA value depends on every earlier monitored point and on its initialization. Store baseline version, lambda, last processed date, subgroup size and the sequence of values used to reach the current state. [[data-science/reproducible-analysis-snapshot|A snapshot]] supports replay.'),
    ('Do not apply fixed-size limits blindly', 'If daily eligible counts range from 40 to 700, the variance of each daily proportion changes. The fixed-n formula below is intentionally restricted to equal-size teaching subgroups. In production, use a monitored statistic and limits designed for variable precision, stabilize subgroup sizes where appropriate, or model daily counts directly. Seasonality, serial correlation and changes in queue mix can also invalidate simple independent-day limits.'),
    ('Treat signals as tests of process behavior', 'The code feeds ten days near 0.04 followed by eight days at 0.09, with a baseline center of 0.05. It checks that the latter stretch generates at least one upper signal. That assertion is a code exercise, not evidence that a real service process changed. Investigate logging, workload, staffing and case mix before action. [[data-science/frozen-baselines-and-alert-investigation|The alert workflow]] records that decision.')],
    '''from math import sqrt

def ewma_rate_signals(daily_rates, baseline_rate, daily_count,
                      weight=0.25, sigma_width=3):
    if not 0 < weight <= 1 or daily_count <= 0:
        raise ValueError("invalid EWMA configuration")
    if not 0 < baseline_rate < 1 or any(not 0 <= rate <= 1 for rate in daily_rates):
        raise ValueError("invalid rates")
    if sigma_width <= 0:
        raise ValueError("invalid limit width")
    daily_sigma = sqrt(baseline_rate * (1 - baseline_rate) / daily_count)
    smoothed = baseline_rate
    results = []
    for day_index, observed_rate in enumerate(daily_rates, start=1):
        smoothed = weight * observed_rate + (1 - weight) * smoothed
        ewma_sigma = daily_sigma * sqrt(
            weight / (2 - weight) * (1 - (1 - weight) ** (2 * day_index)))
        lower = max(0.0, baseline_rate - sigma_width * ewma_sigma)
        upper = min(1.0, baseline_rate + sigma_width * ewma_sigma)
        results.append((day_index, smoothed, lower, upper,
                        smoothed < lower or smoothed > upper))
    return results

series = [0.04] * 10 + [0.09] * 8
signals = ewma_rate_signals(series, 0.05, 200)
assert any(day > 10 and flagged for day, _, _, _, flagged in signals)''',
    'Updating D ordered days is O(D) time and O(D) space if every state is retained; keeping only the latest state is O(1) space. Replaying after a backfill is O(D) from the checkpoint. The equal-size independent-day variance assumption is the main limit, not computation.',
    ['Do not compare an EWMA state with raw daily p-chart limits.', 'Do not reorder days or ignore late backfills.', 'Do not use the fixed-count formula when subgroup sizes change materially.'],
    ['data-science/control-limits-versus-service-targets','data-science/p-chart-with-changing-daily-denominators','data-science/frozen-baselines-and-alert-investigation','data-science/support-breach-process-monitoring-project'])

add('frozen-baselines-and-alert-investigation',
    'Frozen baselines and alert investigation',
    'A monitoring alert is reproducible only when the baseline, extraction, measurement contract and response rule are frozen before the new period arrives.', [
    ('Separate baseline and monitoring phases', 'Estimate the late-response center and chart parameters from a designated historical window. Then freeze a versioned baseline for later days. If an outlying day is folded back into the center as soon as it appears, the chart adapts to the very change it was meant to detect. Rebaseline only after the cause is understood and the process definition has intentionally changed. A deployment that alters response timestamps may require a new measurement contract before any statistical comparison.'),
    ('Triage the data path first', 'For a signaled day, verify eligible case count, event timestamp coverage, deduplication and query version. Compare raw case IDs and numerator IDs with the daily aggregate. Check whether yesterday’s data were complete at the extraction cutoff. A logging outage can produce a low rate that looks like excellent performance, while a missing denominator can produce an artificial spike. [[data-science/sql-reconciliation-and-query-cost|Reconciliation]] should precede stories about staff behavior.'),
    ('Investigate operations second', 'If the data path is intact, inspect queue mix, site, shift, campaign timing, staffing and incident records. Keep contemporaneous evidence rather than explaining the alert from memory a week later. A chart says that the current metric is unusual under its baseline model; it does not isolate which factor moved. Do not split into many subgroups until one produces an attractive narrative without accounting for repeated searching.'),
    ('Record four distinct outcomes', 'The day may miss the service target, trigger a process signal, do both, or do neither. For each alert, record the observed rate, case count, versioned baseline limits, operational target, cause hypothesis, checks performed and final disposition. A confirmed data error requires corrected aggregates and replay of downstream EWMA state. A confirmed process shift may require intervention and later a reviewed new baseline. [[data-science/ewma-for-small-persistent-rate-shifts|Stateful monitoring]] makes backfill handling especially important.'),
    ('Design a release gate', 'Do not send a public chart when its eligible count is zero, its baseline version is missing, or the current query version is incompatible with the baseline. An alert can still be raised internally as an instrumentation incident. Store a resolved or unresolved disposition for each signal, including who reviewed it and when. [[data-science/support-breach-process-monitoring-project|The project]] implements a compact packet builder and a release decision.')],
    '''def alert_packet(day, late_cases, eligible_cases, query_version,
                     baseline_version, baseline_query_version,
                     observed_rate, lower, upper, service_target):
    if eligible_cases <= 0 or not 0 <= late_cases <= eligible_cases:
        raise ValueError("invalid daily counts")
    if abs(observed_rate - late_cases / eligible_cases) > 1e-12:
        raise ValueError("reported rate does not reconcile")
    if not baseline_version or not query_version:
        raise ValueError("missing provenance")
    if not 0 <= lower <= upper <= 1 or not 0 <= service_target <= 1:
        raise ValueError("invalid monitoring thresholds")
    compatible = query_version == baseline_query_version
    return {"day": day, "baseline_version": baseline_version,
            "eligible_cases": eligible_cases, "late_cases": late_cases,
            "target_miss": observed_rate > service_target,
            "process_signal": observed_rate < lower or observed_rate > upper,
            "publishable": compatible}

packet = alert_packet("shift-47", 21, 140, "response-v3", "base-2026q3",
                      "response-v3", 0.15, 0.0, 0.112, 0.03)
assert packet["process_signal"] and packet["target_miss"]
assert packet["publishable"]''',
    'A packet for one day is O(1) time and space once daily counts and limits exist. Reconciling N underlying case IDs costs O(N) expected time with hashed IDs. Incident review time grows with evidence collection and should not be hidden inside a chart computation.',
    ['Do not rebaseline automatically after an inconvenient signal.', 'Do not investigate operations before verifying denominator and timestamp integrity.', 'Do not publish a chart across incompatible metric versions.'],
    ['data-science/control-limits-versus-service-targets','data-science/p-chart-with-changing-daily-denominators','data-science/ewma-for-small-persistent-rate-shifts','data-science/support-breach-process-monitoring-project'])

add('support-breach-process-monitoring-project',
    'Project: release a support breach monitoring packet',
    'Build a daily late-response monitor with variable-denominator limits, target flags, baseline provenance and an explicit release gate.', [
    ('Freeze the metric and baseline', 'Define a late response from a case’s eligible start timestamp and first qualifying response timestamp. Keep one case ID per eligible interaction and a fixed extraction cutoff. Use five illustrative baseline days: (5,100), (7,120), (6,110), (4,90), (8,130). Their pooled center is 30/550. Archive query version, case-ID reconciliation and the baseline period before evaluating new days. [[data-science/control-limits-versus-service-targets|The service target]] of 0.03 remains separate from the chart center.'),
    ('Evaluate a new day by its denominator', 'For a new day with 140 eligible cases, compare 12 late responses and then 21 late responses against limits calculated from that day’s denominator and the frozen center. The first day’s share is about 0.0857 and stays below the illustrative upper limit; the second is 0.15 and signals. Both miss the 0.03 service target. Save the count and the rate, because a screenshot of percentages cannot reveal whether a denominator changed. [[data-science/p-chart-with-changing-daily-denominators|The p-chart]] supplies the calculation.'),
    ('Track small persistent changes separately', 'For equal-size 200-case monitoring subgroups, run a fixed-weight EWMA from the frozen baseline center to detect a sustained modest shift. Do not use that fixed-count setup on the 140-case day without adjusting the variance model. Store every daily input and the resulting EWMA state so a corrected historical day can be replayed. [[data-science/ewma-for-small-persistent-rate-shifts|The EWMA lesson]] states its restricted assumptions.'),
    ('Run an incident check before release', 'A signal triggers case-ID reconciliation, timestamp coverage inspection, query-version comparison, and a review of routing and staffing evidence. Record whether the cause is a data incident, a process change, or unresolved. A version mismatch blocks publication even if the chart formula runs. An unresolved alert can remain visible internally with a clear status; it should not become a confident public performance claim. [[data-science/frozen-baselines-and-alert-investigation|The alert workflow]] keeps that distinction.'),
    ('Publish a compact, inspectable packet', 'Include baseline counts and version, new-day numerator and denominator, center, daily limits, target miss, process signal, investigation disposition, and the next action owner. The code below constructs the numerical portion; production release also needs the underlying case reconciliation and signed-off status mapping. If the binary-case independence assumption fails because workload shocks cluster cases within days, redesign the chart model before relying on its false-alarm rate.')],
    '''from math import sqrt

def support_breach_packet(baseline_days, late_cases, eligible_cases,
                          service_target, baseline_query, current_query):
    if not baseline_days or any(total <= 0 or not 0 <= late <= total
                                for late, total in baseline_days):
        raise ValueError("invalid baseline")
    if eligible_cases <= 0 or not 0 <= late_cases <= eligible_cases:
        raise ValueError("invalid new day")
    if not 0 <= service_target <= 1:
        raise ValueError("invalid target")
    center = sum(late for late, _ in baseline_days) / sum(
        total for _, total in baseline_days)
    spread = 3 * sqrt(center * (1 - center) / eligible_cases)
    upper = min(1.0, center + spread)
    lower = max(0.0, center - spread)
    observed = late_cases / eligible_cases
    return {"rate": observed, "center": center, "lower": lower,
            "upper": upper, "target_miss": observed > service_target,
            "process_signal": observed < lower or observed > upper,
            "publishable": bool(baseline_query)
                           and baseline_query == current_query}

baseline = [(5, 100), (7, 120), (6, 110), (4, 90), (8, 130)]
ordinary = support_breach_packet(baseline, 12, 140, 0.03, "v3", "v3")
signaled = support_breach_packet(baseline, 21, 140, 0.03, "v3", "v3")
assert ordinary["target_miss"] and not ordinary["process_signal"]
assert signaled["target_miss"] and signaled["process_signal"]
assert not support_breach_packet(baseline, 21, 140, 0.03, "v3", "v4")["publishable"]''',
    'Pooling B baseline days costs O(B) time and O(1) additional space. Each monitored day is O(1) after baseline preparation; a D-day replay is O(D). The release cost includes reconciling individual cases and examining chart assumptions, not only calculating limits.',
    ['Do not publish the chart when the current extraction is incompatible with the baseline.', 'Do not collapse target miss and process signal into one flag.', 'Do not apply fixed-count EWMA limits to a variable-count p-chart series.'],
    ['data-science/control-limits-versus-service-targets','data-science/p-chart-with-changing-daily-denominators','data-science/ewma-for-small-persistent-rate-shifts','data-science/frozen-baselines-and-alert-investigation'])

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
               difficulty='Intermediate', tags=['ai-data', 'data-science'], potd_date=None,
               featured=False, sort_order=13100 + index, status='published', published_at=stamp,
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
if not any(module['title'] == 'Process monitoring and alert quality' for module in hub['data']['modules']):
    hub['data']['modules'].insert(-1, {'title':'Process monitoring and alert quality',
                                      'summary':'Separate service targets from control limits, account for changing denominators and investigate signals against a frozen baseline.',
                                      'lessons':tutorial_paths})
apply_module = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
if project_path not in apply_module['lessons']:
    apply_module['lessons'].append(project_path)
if '<h2>Process monitoring and alert quality</h2>' not in hub['body']:
    hub['body'] += '<h2>Process monitoring and alert quality</h2>' + links(tutorial_paths)
    hub['body'] += '<h2>Support breach monitoring project</h2>' + links([project_path])
hub['updated_at'] = stamp

project_hub = by_path[project_hub_path]
if project_path not in project_hub['data']['modules'][0]['lessons']:
    project_hub['data']['modules'][0]['lessons'].append(project_path)
if '<h2>Support breach monitoring project</h2>' not in project_hub['body']:
    project_hub['body'] += '<h2>Support breach monitoring project</h2>' + links([project_path])
project_hub['updated_at'] = stamp

for source, target in [
    ('data-science/metric-denominator-and-cohort', tutorial_paths[0]),
    ('data-science/instrumentation-change-and-metric-guardrails', tutorial_paths[1]),
    ('data-science/retention-cohort-and-maturity', tutorial_paths[2]),
    ('data-science/sql-reconciliation-and-query-cost', tutorial_paths[3]),
    ('data-science/fulfillment-delay-analysis-project', project_path),
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
