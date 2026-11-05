"""Extend the Data Science time-to-event sequence with advanced operational checks."""
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
    'left-truncation-and-delayed-entry-risk-sets',
    'survival-curve-uncertainty-and-tail-support',
    'landmark-analysis-and-immortal-time',
    'restricted-mean-open-time-between-queues',
    'specialist-queue-survival-comparison-project',
)
paths = {'data-science/' + slug for slug in slugs}
rows = [row for row in rows if row['path'] not in paths]
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
lessons = []

def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='data-science/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost,
                        mistakes=mistakes, related=related))

add('left-truncation-and-delayed-entry-risk-sets',
    'Delayed entry and left-truncated risk sets',
    'Delayed entry means a case becomes observable only after surviving event-free to a later age, so it must not join earlier event denominators.', [
    ('Separate the two clocks', 'An escalation dashboard may first observe a case when it reaches the specialist queue, even though the case was created earlier. Case age remains measured from creation; observation entry is the age at specialist arrival. A case resolved before arrival never appears in this extract. That is left truncation, not right censoring. The data describe cases conditional on reaching the queue. [[data-science/cohort-entry-and-survivorship-bias|Cohort entry]] determines whether that conditional population matches the decision.'),
    ('Build the eligible risk set', 'At a resolution time t, include a case only if its observation-entry age is strictly before t and its exit age is at least t. This example uses day-level observations with an explicit (entry, exit] convention. Two cases start observation at age zero. Three enter at ages three or four. At day two, only two are eligible, so one resolution halves the estimated unresolved share. At day five, four cases are eligible and one resolves. At day seven, two remain and one resolves while another is censored.'),
    ('Keep entry distinct from censoring', 'A case censored at day six contributed exposure before day six and then left the risk set. A case that entered at day four contributed no exposure to earlier denominators. Treating both as ordinary missing rows changes the meaning of the estimator. Store entry age, exit age, terminal status and the source timestamps; do not derive entry from the first status row unless that row reliably marks the start of observation. [[data-science/event-time-risk-sets-and-tied-outcomes|Tied outcomes]] still use the pre-time denominator.'),
    ('Check the selection mechanism', 'Delayed-entry adjustment counts only observed survivors. It cannot recover cases that resolved before entering a specialist queue, nor can it describe all created support cases without a representative intake cohort. If high-complexity cases enter sooner, queue-entry timing may also depend on future resolution. Compare entry-age distributions and the operational routing rule across periods. An apparently improved specialist curve can reflect routing changes rather than faster work.'),
    ('Choose an estimand a reader can act on', 'For service-wide time to resolution, start from a creation cohort and observe every case from age zero. For time after specialist assignment, reset the clock at assignment and define the population as assigned cases. Use delayed entry only when age since original creation matters and the inclusion process is defensible. [[data-science/specialist-queue-survival-comparison-project|The specialist-queue project]] asks for both views before a comparison is released.')],
    '''from bisect import bisect_left

def delayed_entry_curve(case_records):
    if len({case_id for case_id, _, _, _ in case_records}) != len(case_records):
        raise ValueError("duplicate case ID")
    if any(entry < 0 or exit_day <= entry or event not in (0, 1)
           for _, entry, exit_day, event in case_records):
        raise ValueError("invalid observation interval")
    entries = sorted(entry for _, entry, _, _ in case_records)
    exits = sorted(exit_day for _, _, exit_day, _ in case_records)
    event_days = sorted({exit_day for _, _, exit_day, event in case_records if event})
    unresolved = 1.0
    points = []
    for day in event_days:
        at_risk = bisect_left(entries, day) - bisect_left(exits, day)
        events = sum(event for _, _, exit_day, event in case_records if exit_day == day)
        if at_risk <= 0 or events > at_risk:
            raise ValueError("invalid risk set")
        unresolved *= 1 - events / at_risk
        points.append((day, at_risk, unresolved))
    return points

cases = [("S31", 0, 2, 1), ("S32", 0, 6, 0),
         ("S33", 3, 5, 1), ("S34", 4, 7, 1), ("S35", 3, 7, 0)]
curve = delayed_entry_curve(cases)
assert [(day, risk) for day, risk, _ in curve] == [(2, 2), (5, 4), (7, 2)]
assert [round(share, 4) for _, _, share in curve] == [0.5, 0.375, 0.1875]''',
    'Sorting N entry and exit ages costs O(N log N) time and O(N) space. Binary-searching U event times costs O(U log N); the direct event count in this compact code adds O(N × U). Pre-aggregating event counts reduces that scan to O(N log N + U log N).',
    ['Do not count a later entrant in an earlier event denominator.', 'Do not call cases absent before queue entry right-censored.', 'Do not generalize a conditional specialist cohort to all created cases.'],
    ['data-science/event-time-risk-sets-and-tied-outcomes','data-science/survival-curve-uncertainty-and-tail-support','data-science/landmark-analysis-and-immortal-time','data-science/specialist-queue-survival-comparison-project'])

add('survival-curve-uncertainty-and-tail-support',
    'Survival-curve uncertainty and thin-tail support',
    'A survival estimate needs both an uncertainty interval and the number still at risk; late steps based on a few cases carry little precision.', [
    ('Read beyond the line', 'The unresolved-case curve can look stable after day five even when only two cases remain under observation. A fixed-horizon estimate should report its event table, risk count and uncertainty. For a Kaplan–Meier step with d resolutions among n at risk, Greenwood accumulates d divided by n times (n minus d) across event times while the estimated unresolved share stays strictly between zero and one. [[data-science/kaplan-meier-resolution-curve|The curve]] supplies the point estimate; the variance calculation describes sampling uncertainty under its assumptions.'),
    ('Use bounded interval construction', 'A plain symmetric interval around a probability can extend below zero or above one. A log-log transformation keeps the resulting bounds in the probability range when the estimate lies strictly between zero and one. The code below returns an approximate pointwise interval at each supported event time. It deliberately leaves S equal to zero or one without this transformed interval rather than dividing by an undefined logarithm. An alternative interval method is needed at those boundaries.'),
    ('Explain what the interval covers', 'A 95% pointwise interval describes uncertainty at a specified time under repeated samples and the estimator assumptions; it is not a 95% band that covers the entire curve at every time simultaneously. Inspecting twenty horizons and reporting the narrowest or most favorable one defeats the stated decision horizon. The interval also does not repair informative censoring, shifted status codes or a queue cohort that excludes early resolutions. [[data-science/right-censoring-and-time-to-event|The censoring contract]] comes first.'),
    ('Show how precision collapses', 'In the eight-case teaching ledger, the day-two resolution has eight at risk, while the day-ten resolution has only two. The later step changes the estimated unresolved share from 0.40 to 0.20, but its Greenwood contribution is much larger. A dashboard that draws both steps with identical visual authority hides the thinning denominator. Pair the curve with at-risk counts at planned milestones and stop the comparison when a group lacks adequate follow-up.'),
    ('Plan the uncertainty unit', 'If a customer contributes multiple cases, case-level independence may fail. Either select one case per customer, use a customer-level resampling plan, or state why the case is the independent unit. Stratified sampling and different entry dates need their own variance treatment. This simple interval is a teaching calculation for independent cases, not a substitute for a full design-aware analysis. [[data-science/restricted-mean-open-time-between-queues|A queue comparison]] adds a common horizon and a difference scale.')],
    '''from math import exp, log, sqrt

def unresolved_intervals(event_rows, z_score=1.96):
    unresolved = 1.0
    greenwood = 0.0
    output = []
    for day, at_risk, resolved, censored in event_rows:
        if at_risk <= 0 or min(resolved, censored) < 0:
            raise ValueError("invalid event table")
        if resolved + censored > at_risk:
            raise ValueError("more outcomes than cases at risk")
        unresolved *= 1 - resolved / at_risk
        if resolved and at_risk > resolved:
            greenwood += resolved / (at_risk * (at_risk - resolved))
        interval = None
        if 0 < unresolved < 1:
            transformed = log(-log(unresolved))
            standard_error = sqrt(greenwood) / abs(log(unresolved))
            lower = exp(-exp(transformed + z_score * standard_error))
            upper = exp(-exp(transformed - z_score * standard_error))
            interval = (lower, upper)
        output.append((day, unresolved, interval))
    return output

ledger = [(2, 8, 1, 0), (3, 7, 1, 1), (5, 5, 1, 1),
          (8, 3, 1, 0), (10, 2, 1, 1)]
estimates = unresolved_intervals(ledger)
assert round(estimates[2][1], 2) == 0.60
assert all(bounds is None or bounds[0] <= share <= bounds[1]
           for _, share, bounds in estimates)''',
    'An already ordered U-row event table takes O(U) time and O(U) output space; reporting one chosen horizon uses O(1) additional space. Pointwise intervals become unstable in thin tails even though the loop remains cheap. Repeated customer-level bootstrap samples cost substantially more.',
    ['Do not present a pointwise interval as a simultaneous curve band.', 'Do not hide the day-ten risk count behind a smooth-looking plot.', 'Do not interpret the interval as protection against informative censoring.'],
    ['data-science/kaplan-meier-resolution-curve','data-science/restricted-mean-open-time-between-queues','data-science/left-truncation-and-delayed-entry-risk-sets','data-science/specialist-queue-survival-comparison-project'])

add('landmark-analysis-and-immortal-time',
    'Landmark analysis and immortal-time traps',
    'A post-entry action must not be treated as if it were known at case creation; doing so gives its future recipients guaranteed event-free time before the action.', [
    ('Locate the classification error', 'Suppose escalation may happen on day three or day six after a case opens. Labelling every eventually escalated case as escalated from day zero means a case must remain unresolved long enough to earn that label. A case resolved on day two could never enter the escalated group. The apparent early advantage is built into the grouping rule. This is an immortal-time error, not a subtle model-tuning problem. [[data-science/cohort-entry-and-survivorship-bias|Entry and selection]] should be checked before drawing curves.'),
    ('Choose a landmark and reset the question', 'At a prespecified day-four landmark, retain only cases still unresolved and observed immediately after day four. Classify exposure using escalation history strictly before that instant, then follow both groups from the landmark. A case escalated on day six is unexposed at day four, even if it escalates later. The estimand is now conditional on surviving unresolved to day four; do not report it as the effect among all cases at creation.'),
    ('Handle timestamp boundaries', 'If escalation and resolution share a rounded day-four timestamp, the order is unknown. Reject or adjudicate the record using finer timestamps rather than assigning whichever order helps the analysis. A censor at day three is absent from the day-four landmark cohort, while a censor at day seven is eligible at day four. Keep the chosen boundary convention in the extraction code and in the report. [[data-science/event-time-risk-sets-and-tied-outcomes|Risk sets]] depend on these choices.'),
    ('Know what the design cannot prove', 'Escalation is usually triggered by case difficulty, so landmark grouping is still confounded by severity and prior agent action. A lower resolution rate after escalation does not establish that escalation caused delay. Adjust for defensible pre-landmark attributes or use a designed intervention if the goal is causal. A time-varying exposure model can use later status changes without freezing them at day zero, but it still needs careful confounding assumptions.'),
    ('Write down the eligible population', 'The code emits one row per eligible case with its day-four exposure state and residual follow-up. It excludes a day-two resolution, keeps a case escalated at day three, and keeps a case escalating at day six in the day-four unexposed group. A second landmark would define a different population and should not be selected after inspecting outcomes. [[data-science/specialist-queue-survival-comparison-project|The audit project]] requires an explicit decision about whether this conditional view is even needed.')],
    '''def landmark_cases(case_records, landmark_day):
    if landmark_day <= 0:
        raise ValueError("landmark must be positive")
    if len({case_id for case_id, _, _, _ in case_records}) != len(case_records):
        raise ValueError("duplicate case ID")
    eligible = []
    for case_id, exit_day, resolved, escalation_day in case_records:
        if exit_day < 0 or resolved not in (0, 1):
            raise ValueError("invalid outcome")
        if escalation_day is not None:
            if escalation_day < 0 or escalation_day > exit_day:
                raise ValueError("impossible escalation time")
            if escalation_day == landmark_day and exit_day >= landmark_day:
                raise ValueError("ambiguous landmark ordering")
        if exit_day <= landmark_day:
            continue
        was_escalated = escalation_day is not None and escalation_day < landmark_day
        eligible.append((case_id, was_escalated, exit_day - landmark_day, resolved))
    return eligible

cases = [("L41", 2, 1, None), ("L42", 8, 1, 3),
         ("L43", 10, 0, 6), ("L44", 7, 1, None)]
cohort = landmark_cases(cases, 4)
assert cohort == [("L42", True, 4, 1), ("L43", False, 6, 0),
                  ("L44", False, 3, 1)]''',
    'Selecting a landmark cohort from N records costs O(N) time and O(N) output space. Repeating many candidate landmarks can be expensive and invites selective reporting. The larger cost is interpreting a conditional observational comparison as a causal intervention.',
    ['Do not assign eventual escalation status to the case at day zero.', 'Do not include a case that resolved before the landmark.', 'Do not call a landmark association a causal effect without a defensible design.'],
    ['data-science/cohort-entry-and-survivorship-bias','data-science/left-truncation-and-delayed-entry-risk-sets','data-science/restricted-mean-open-time-between-queues','data-science/specialist-queue-survival-comparison-project'])

add('restricted-mean-open-time-between-queues',
    'Compare queues by restricted mean open time',
    'A difference in restricted mean open time compares the area under two unresolved-case curves over the same prespecified horizon, in case-days.', [
    ('Keep the contrast in its own units', 'If queue A has a six-day restricted mean of 4.975 open case-days and queue B has 4.250, the A-minus-B difference is 0.725 case-days through day six. It is not a 0.725-day difference in eventual mean resolution time. Nor does it prove a routing change caused the difference. The two cohorts must share a time origin, outcome definition, calendar eligibility window, censoring policy and horizon. [[data-science/restricted-mean-unresolved-time|The single-curve calculation]] defines the area.'),
    ('Check common support', 'A queue introduced only last week may have many cases censored before day six. Its day-six estimate has little support even if a function returns a number. Record at-risk counts at the horizon and a minimum acceptable follow-up rule before comparison. If one queue lacks support, shorten the common horizon for both or wait for more mature data. Never let each queue choose its own maximum follow-up: the resulting areas answer different questions. [[data-science/survival-curve-uncertainty-and-tail-support|Tail diagnostics]] make this visible.'),
    ('Use a worked contrast without hidden censoring', 'For a clean arithmetic check, six A cases end at days two, four, five, eight, eight and eight; the final three remain unresolved beyond the day-six horizon. Six B cases end at days one, two, four, five, eight and eight; the final two also remain unresolved beyond day six. With no censoring before day six, area under each unresolved curve equals the average of each duration capped at six. A is 29/6, or about 4.833 case-days; B is 24/6, or four. The difference is 5/6 case-day. This fixture checks code, not a population claim.'),
    ('Add uncertainty at the correct unit', 'For a real comparison, recompute both curves and their area difference in each bootstrap replicate, resampling independent customers within queue if one customer can open several cases. Retain cohort and censoring structure within replicates. A narrow interval from resampling individual status updates would be false precision. If queue assignment depends on case complexity, uncertainty about the descriptive difference is separate from bias in a causal claim. [[data-science/bootstrap-interval-interpretation|Bootstrap units]] need an explicit contract.'),
    ('Pair open time with exit types', 'A queue can show shorter open time because it resolves cases faster or because it cancels more of them. Publish resolution and cancellation cumulative incidence at the same horizon beside the bounded open-time difference. For the first metric, state whether the curve counts only resolution or any terminal exit; changing that rule changes the area. [[data-science/competing-risks-and-resolution-incidence|Competing outcomes]] prevent a fast cancellation from masquerading as better resolution.')],
    '''def capped_open_time(case_observations, horizon_days):
    if horizon_days <= 0 or not case_observations:
        raise ValueError("missing cases or horizon")
    if any(duration < horizon_days for duration, observed_event in case_observations
           if not observed_event):
        raise ValueError("early censoring needs a Kaplan-Meier area estimate")
    if any(duration < 0 or observed_event not in (0, 1)
           for duration, observed_event in case_observations):
        raise ValueError("invalid observation")
    return sum(min(duration, horizon_days) for duration, _ in case_observations) / len(case_observations)

queue_a = [(2, 1), (4, 1), (5, 1), (8, 0), (8, 0), (8, 0)]
queue_b = [(1, 1), (2, 1), (4, 1), (5, 1), (8, 0), (8, 0)]
queue_a_days = capped_open_time(queue_a, 6)
queue_b_days = capped_open_time(queue_b, 6)
assert queue_a_days == 29 / 6
assert queue_b_days == 4
assert abs((queue_a_days - queue_b_days) - 5 / 6) < 1e-12''',
    'For N case records without censoring before the selected horizon, direct capped averaging is O(N) time and O(1) additional space. With early censoring, compute separate Kaplan–Meier curves at O(N log N) sorting cost, then integrate. Resampling B replicates multiplies that work by B.',
    ['Do not apply capped averaging when a case was censored before the horizon.', 'Do not compare queues over different horizons.', 'Do not mistake a descriptive queue difference for an effect of queue assignment.'],
    ['data-science/restricted-mean-unresolved-time','data-science/survival-curve-uncertainty-and-tail-support','data-science/competing-risks-and-resolution-incidence','data-science/specialist-queue-survival-comparison-project'])

add('specialist-queue-survival-comparison-project',
    'Project: audit specialist-queue resolution comparisons',
    'Release a queue comparison only after validating observation entry, status timing, common-horizon support and the action-unit interpretation.', [
    ('Freeze two cohorts and one question', 'Create a case-created cohort for service-wide resolution and a separate specialist-entry cohort for the conditional queue view. Keep created time, specialist-entry time, resolution or cancellation time, extraction cutoff, queue assignment and customer ID. State whether the decision is about all created cases, cases that reached a specialist, or cases still open at a day-four landmark. These are different populations. [[data-science/left-truncation-and-delayed-entry-risk-sets|Delayed entry]] cannot silently turn one into another.'),
    ('Verify the event accounting', 'Reproduce the delayed-entry teaching ledger with risk counts two at day two, four at day five and two at day seven. Then reconcile the production extract: one case per ID, entry earlier than exit, no terminal event after a case has left observation, and a documented rule for same-day events and censoring. Preserve cancellations as their own cause when they prevent ordinary resolution. [[data-science/competing-risks-and-resolution-incidence|Cause-specific incidence]] belongs beside any open-time curve.'),
    ('Show uncertainty with denominator support', 'For each queue, print the unresolved share and at-risk count at the prespecified business horizon, plus a pointwise interval where its assumptions hold. A case-created queue introduced too recently may have too little mature follow-up; withhold the cross-queue figure rather than extend a flat tail. The interval does not validate independent censoring. [[data-science/survival-curve-uncertainty-and-tail-support|The uncertainty lesson]] separates statistical spread from observation bias.'),
    ('Compare bounded open time carefully', 'Use a shared six-day horizon only if both queues support it. A test ledger without early censors gives 29/6 case-days for queue A and four for queue B, so the descriptive A-minus-B difference is 5/6 case-day. In the real ledger, early censors require survival-curve integration rather than capped averaging. Record a customer-level resampling plan if one customer can create repeated cases. [[data-science/restricted-mean-open-time-between-queues|The contrast lesson]] identifies the needed assumptions.'),
    ('Reject a misleading escalation story', 'Do not label cases eventually escalated as escalated at creation. If escalation status is part of a secondary comparison, define a day-four landmark, retain only cases open at that instant, and use status already known by then. Explain that the resulting estimate is conditional and observational. The final packet contains cohort definitions, input checks, event tables, cause-specific outcomes, horizon support, uncertainty method, time-varying status policy and a clear release or withhold decision. [[data-science/landmark-analysis-and-immortal-time|Landmark analysis]] specifies the boundary.')],
    '''def audit_queue_records(case_records, horizon_days):
    if horizon_days <= 0:
        raise ValueError("invalid horizon")
    if len({case_id for case_id, _, _, _, _ in case_records}) != len(case_records):
        raise ValueError("duplicate case ID")
    queue_counts = {}
    for case_id, queue, entry_day, exit_day, outcome in case_records:
        if entry_day < 0 or exit_day <= entry_day:
            raise ValueError("invalid observation interval")
        if outcome not in {"resolved", "cancelled", "censored"}:
            raise ValueError("unmapped terminal status")
        counts = queue_counts.setdefault(queue, {"cases": 0, "at_risk_at_horizon": 0})
        counts["cases"] += 1
        if entry_day < horizon_days <= exit_day:
            counts["at_risk_at_horizon"] += 1
    if len(queue_counts) < 2:
        raise ValueError("comparison needs at least two queues")
    return queue_counts

ledger = [("Q51", "north", 0, 2, "resolved"),
          ("Q52", "north", 0, 8, "censored"),
          ("Q53", "south", 0, 5, "resolved"),
          ("Q54", "south", 0, 8, "cancelled")]
readiness = audit_queue_records(ledger, 6)
assert readiness["north"]["cases"] == 2
assert readiness["south"]["at_risk_at_horizon"] == 1''',
    'Validation of N case records is O(N) expected time and O(G) space for G queues. Estimating each curve adds sorting; uncertainty resampling adds repeated case-level passes. A release should block on absent follow-up or inconsistent status mapping even when all code completes.',
    ['Do not mix a case-created population with a specialist-entry population in one denominator.', 'Do not release a queue difference solely because the point estimates separate.', 'Do not interpret eventual escalation as a baseline attribute.'],
    ['data-science/left-truncation-and-delayed-entry-risk-sets','data-science/survival-curve-uncertainty-and-tail-support','data-science/landmark-analysis-and-immortal-time','data-science/restricted-mean-open-time-between-queues'])

assert len(lessons) == len(paths) == 5
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
               featured=False, sort_order=12900 + index, status='published', published_at=stamp,
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
if not any(module['title'] == 'Advanced time-to-event decisions' for module in hub['data']['modules']):
    hub['data']['modules'].insert(-1, {'title':'Advanced time-to-event decisions',
                                      'summary':'Handle delayed entry, quantify uncertainty, avoid immortal time and compare queues at one horizon.',
                                      'lessons':tutorial_paths})
apply_module = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
if project_path not in apply_module['lessons']:
    apply_module['lessons'].append(project_path)
if '<h2>Advanced time-to-event decisions</h2>' not in hub['body']:
    hub['body'] += '<h2>Advanced time-to-event decisions</h2>' + links(tutorial_paths)
    hub['body'] += '<h2>Specialist-queue survival project</h2>' + links([project_path])
hub['updated_at'] = stamp
project_hub = by_path[project_hub_path]
if project_path not in project_hub['data']['modules'][0]['lessons']:
    project_hub['data']['modules'][0]['lessons'].append(project_path)
if '<h2>Specialist-queue survival project</h2>' not in project_hub['body']:
    project_hub['body'] += '<h2>Specialist-queue survival project</h2>' + links([project_path])
project_hub['updated_at'] = stamp

for source, target in [
    ('data-science/event-time-risk-sets-and-tied-outcomes', tutorial_paths[0]),
    ('data-science/kaplan-meier-resolution-curve', tutorial_paths[1]),
    ('data-science/cohort-entry-and-survivorship-bias', tutorial_paths[2]),
    ('data-science/restricted-mean-unresolved-time', tutorial_paths[3]),
    ('data-science/support-resolution-time-audit-project', project_path),
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
