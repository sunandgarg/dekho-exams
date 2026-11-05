"""Add a connected, original survival-analysis sequence to Data Science."""
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
    'event-time-risk-sets-and-tied-outcomes',
    'kaplan-meier-resolution-curve',
    'competing-risks-and-resolution-incidence',
    'restricted-mean-unresolved-time',
    'support-resolution-time-audit-project',
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

add('event-time-risk-sets-and-tied-outcomes',
    'Event-time risk sets and tied outcomes',
    'A risk set counts cases still observable and eligible immediately before an event time; its denominator changes as events and censoring occur.', [
    ('Fix the clock before counting', 'For a support-resolution analysis, time zero is case creation and the event is the first recorded resolution. A case still open at the audit cutoff is right-censored at its observed age. A cancelled case needs an explicit outcome policy: it is a competing event if cancellation prevents ordinary resolution, not an ordinary unresolved case. Record timestamps, status, cohort entry and extraction cutoff together. [[data-science/right-censoring-and-time-to-event|Right-censoring]] explains why an open case still contributes observed time.'),
    ('Build the denominator at each event time', 'Use eight cases with observed durations and event flags: (2,1), (3,0), (3,1), (5,1), (5,0), (8,1), (10,0), (10,1). At day two, eight cases are at risk. At day three, seven remain; one resolves and one is censored. Both belong to the day-three risk set immediately before either outcome. After processing that time, five remain. The risk set at day five is five, then three at day eight and two at day ten.'),
    ('State a tie convention', 'At a shared timestamp, count event cases against the pre-time risk set, then remove both events and censored cases before the next time. This convention prevents a day-three censor from shrinking the denominator before the day-three resolution. If source timestamps are rounded to whole days, ties can be frequent; keep the time unit and tie rule in the analysis contract. Do not fabricate an arbitrary within-day ordering just because rows arrived in a particular file order.'),
    ('Check conservation', 'At each distinct time, the next risk count equals the current count minus resolutions minus censored cases. The sequence here is eight, seven, five, three, two, then zero. An event after a case was censored, a negative duration, or duplicate case ID violates the input contract. Reconcile event counts with the operational status ledger before estimating a curve. [[data-science/dataset-grain-and-join-cardinality|Dataset grain]] matters: one row per case, not one row per status update.'),
    ('Expose the event table', 'Keep columns for time, at risk, resolved, censored and remaining. That table is the audit trail for [[data-science/kaplan-meier-resolution-curve|the Kaplan–Meier curve]], competing-outcome calculations and later horizon summaries. When cases enter observation late because the extract includes only cases that reached a specific queue, a simple case-created cohort is no longer valid; account for delayed entry or choose a new time origin.')],
    '''def event_table(case_observations):
    if len({case_id for case_id, _, _ in case_observations}) != len(case_observations):
        raise ValueError("duplicate case ID")
    by_day = {}
    for case_id, duration_days, resolved in case_observations:
        if duration_days < 0 or resolved not in (0, 1):
            raise ValueError("invalid duration or event flag")
        counts = by_day.setdefault(duration_days, {"resolved": 0, "censored": 0})
        counts["resolved" if resolved else "censored"] += 1
    at_risk = len(case_observations)
    table = []
    for day, counts in sorted(by_day.items()):
        if counts["resolved"] + counts["censored"] > at_risk:
            raise ValueError("risk count exhausted")
        table.append((day, at_risk, counts["resolved"], counts["censored"]))
        at_risk -= counts["resolved"] + counts["censored"]
    return table

cases = [("C21", 2, 1), ("C22", 3, 0), ("C23", 3, 1),
         ("C24", 5, 1), ("C25", 5, 0), ("C26", 8, 1),
         ("C27", 10, 0), ("C28", 10, 1)]
assert event_table(cases) == [(2, 8, 1, 0), (3, 7, 1, 1),
                              (5, 5, 1, 1), (8, 3, 1, 0), (10, 2, 1, 1)]''',
    'Grouping N case records is O(N) expected time and O(U) space for U distinct durations; sorting those durations costs O(U log U). A single chronological pass then costs O(U). Bad cohort definitions dominate computational cost as a source of error.',
    ['Do not remove same-time censors before counting same-time events.', 'Do not treat status-update rows as independent cases.', 'Do not label a cancellation as ordinary censoring without an outcome policy.'],
    ['data-science/kaplan-meier-resolution-curve','data-science/competing-risks-and-resolution-incidence','data-science/restricted-mean-unresolved-time','data-science/support-resolution-time-audit-project'])

add('kaplan-meier-resolution-curve',
    'Kaplan–Meier curves for support resolution',
    'The Kaplan–Meier product estimates the chance a case remains unresolved beyond each observed resolution time under a suitable censoring assumption.', [
    ('Choose the event and interpret the axis', 'Here the event is resolution. The estimated survival function S(t) means the probability that resolution has not happened by time t; it is an unresolved-case curve, not a customer-survival curve. Start at S(0)=1 for a cohort observed at creation. With the eight-case event table, multiply the current estimate by 1 minus resolved divided by at risk at each event time. A censor changes a later denominator but creates no step at its own time. [[data-science/event-time-risk-sets-and-tied-outcomes|The risk-set table]] fixes tie handling.'),
    ('Work through a nontrivial tie', 'At day two, S becomes 7/8, or 0.875. Day three has seven at risk, one resolution and one censor; multiply 0.875 by 6/7 to get 0.75. At day five, five at risk and one resolution yield 0.60. Day eight yields 0.40; day ten yields 0.20. The day-three and day-five censors remain in the same-time denominator and leave afterward. This calculation differs from dividing cumulative resolved cases by the original eight because censored cases stop contributing later exposure.'),
    ('Read fixed horizons with care', 'By day six the curve is still at 0.60, so the estimated resolution probability by that horizon is 0.40 in this illustrative cohort. State the horizon and the number at risk nearby. A flat tail after the last event is not proof that the eventual resolution probability has stopped changing; no later events may be observable. If a service target is day six, report its cohort definition and cutoff maturity before comparing queues.'),
    ('Name the censoring assumption', 'Administrative censoring at a planned extraction date is often easier to defend than censoring caused by a case disappearing from the system. The estimator needs censoring to be sufficiently independent of the future resolution time, conditional on relevant grouping variables. If escalated cases are selectively removed from the extract, the curve can be optimistic. A plotted line cannot detect that design failure. [[data-science/complete-case-selection-and-target-population|Complete-case selection]] is a related warning.'),
    ('Use the right estimator for the question', 'One minus S(t) is useful when resolution is the only event that ends follow-up and other exits are genuine censoring. If cancellation prevents later resolution, treating cancellation as censoring can overstate the observed-world chance of resolution. Use [[data-science/competing-risks-and-resolution-incidence|competing-risk incidence]] for that question. If the decision concerns average time spent open through a finite horizon, use [[data-science/restricted-mean-unresolved-time|restricted mean unresolved time]].')],
    '''def unresolved_curve(event_rows):
    unresolved_share = 1.0
    points = []
    for day, at_risk, resolved, censored in event_rows:
        if at_risk <= 0 or min(resolved, censored) < 0 or resolved + censored > at_risk:
            raise ValueError("invalid event table")
        unresolved_share *= 1 - resolved / at_risk
        points.append((day, unresolved_share, at_risk))
    return points

rows = [(2, 8, 1, 0), (3, 7, 1, 1), (5, 5, 1, 1),
        (8, 3, 1, 0), (10, 2, 1, 1)]
curve = unresolved_curve(rows)
assert [round(point[1], 3) for point in curve] == [0.875, 0.75, 0.6, 0.4, 0.2]
day_six_unresolved = next(value for day, value, _ in reversed(curve) if day <= 6)
assert round(1 - day_six_unresolved, 2) == 0.4''',
    'Given a sorted table of U distinct outcome times, curve calculation costs O(U) time and O(U) output space. Keeping only one requested horizon can use O(1) additional space. The statistical limit is thin late risk sets, not run time.',
    ['Do not call S(t) the resolution probability when resolution is the event.', 'Do not interpret a flat censored tail as a measured long-run plateau.', 'Do not use one minus Kaplan–Meier as observed-world incidence with competing exits.'],
    ['data-science/event-time-risk-sets-and-tied-outcomes','data-science/competing-risks-and-resolution-incidence','data-science/restricted-mean-unresolved-time','data-science/support-resolution-time-audit-project'])

add('competing-risks-and-resolution-incidence',
    'Competing risks and resolution incidence',
    'A competing event prevents the event of interest from occurring in the observed workflow; cumulative incidence tracks each outcome without pretending competing exits are ordinary censoring.', [
    ('Separate possible endings', 'Suppose a support case can resolve, be cancelled, or remain open at extraction. Resolution and cancellation are terminal outcomes in the recorded workflow. An open case is administratively censored. If cancellation permanently rules out later resolution of that same case, it is a competing event. A different business question—what resolution time might have been if cancellation were impossible—needs stronger causal assumptions and cannot be answered by relabelling cancellations as censored.'),
    ('Update the event-free share first', 'At each day use the risk set immediately before any outcome at that day. Let Sprev be the share still free of both terminal events. Add Sprev times resolution count divided by at risk to the resolution cumulative incidence, and similarly for cancellations. Then multiply Sprev by one minus total terminal events divided by at risk. Remove censors after this tied-time calculation. [[data-science/event-time-risk-sets-and-tied-outcomes|Risk-set discipline]] keeps the denominator consistent.'),
    ('Check a small ledger', 'Six cases have outcomes at day two (one resolution), day three (one cancellation and one censor), day five (one resolution), and day seven (one resolution and one cancellation). The resolution cumulative incidence is 1/6 at day two, 7/18 at day five and 11/18 at day seven. Cancellation incidence finishes at 7/18. They sum to one because this small ledger eventually records a terminal event for every noncensored survivor; the day-three censor itself added to neither incidence.'),
    ('Interpret the difference from Kaplan–Meier', 'If cancelled cases are instead treated as censored in a resolution-only Kaplan–Meier calculation, the estimator describes a different hypothetical setting and can produce a higher resolution probability than the observed-world cumulative incidence. State which quantity answers the decision. A queue owner deciding how many cases will actually resolve before day seven needs resolution cumulative incidence with cancellations included, not a hypothetical no-cancellation curve.'),
    ('Keep uncertainty and policy visible', 'A cancellation code may cover duplicates, customer withdrawal and agent error. Those mechanisms might deserve separate competing causes or a sensitivity analysis, depending on the operational decision. Sparse events leave unstable cause-specific estimates at late times. Report each event count, censor count and risk count, plus the event-code version and observation cutoff. [[data-science/support-resolution-time-audit-project|The audit project]] applies these checks to a release packet.')],
    '''def cumulative_outcome_incidence(event_rows):
    event_free = 1.0
    resolved_incidence = 0.0
    cancelled_incidence = 0.0
    output = []
    for day, at_risk, resolved, cancelled, censored in event_rows:
        if at_risk <= 0 or min(resolved, cancelled, censored) < 0:
            raise ValueError("invalid event count")
        if resolved + cancelled + censored > at_risk:
            raise ValueError("more outcomes than cases at risk")
        resolved_incidence += event_free * resolved / at_risk
        cancelled_incidence += event_free * cancelled / at_risk
        event_free *= 1 - (resolved + cancelled) / at_risk
        output.append((day, resolved_incidence, cancelled_incidence, event_free))
    return output

ledger = [(2, 6, 1, 0, 0), (3, 5, 0, 1, 1),
          (5, 3, 1, 0, 0), (7, 2, 1, 1, 0)]
incidence = cumulative_outcome_incidence(ledger)
assert round(incidence[-1][1], 6) == round(11 / 18, 6)
assert round(incidence[-1][2], 6) == round(7 / 18, 6)
assert round(sum(incidence[-1][1:]), 6) == 1.0''',
    'For U sorted event times and K terminal causes, a full event table costs O(U × K) time and output space. The two-cause scan shown uses O(U) time and output space. Cause coding and enough mature follow-up are the real constraints.',
    ['Do not classify a terminal competing exit as ordinary administrative censoring.', 'Do not add a censored case to any event incidence.', 'Do not interpret cause-specific incidence as a causal effect of preventing another cause.'],
    ['data-science/event-time-risk-sets-and-tied-outcomes','data-science/kaplan-meier-resolution-curve','data-science/restricted-mean-unresolved-time','data-science/support-resolution-time-audit-project'])

add('restricted-mean-unresolved-time',
    'Restricted mean unresolved time at a business horizon',
    'Restricted mean unresolved time is the area under the unresolved-case curve from case creation to a specified horizon; it remains meaningful when the far tail is unobserved.', [
    ('Set a decision horizon', 'A support lead may care about case-days spent open during the first six days, not the eventual mean resolution time. Define a horizon τ=6 days before looking at outcomes. The restricted mean is the integral of S(t) from zero to τ, where S(t) is the unresolved-case survival curve. This makes the unit case-days per initially observed case. It is a bounded summary; it does not fill in the unobserved tail after day six. [[data-science/kaplan-meier-resolution-curve|The curve lesson]] defines S(t).'),
    ('Integrate the steps exactly', 'Using the eight-case curve, S is one from day zero to two, 0.875 from two to three, 0.75 from three to five, and 0.60 from five to six. The areas are 2, 0.875, 1.5 and 0.6 case-days. Their sum is 4.975 unresolved case-days through day six. A raw average over only resolved cases would discard open cases and likely understate open time. A raw average of observed durations mixes resolved and censored durations without accounting for their different meanings.'),
    ('Compare groups on common ground', 'Two queues need the same time origin, event definition, extraction rule and τ. A queue with newer cases might have little mature follow-up at day six; plotting a day-six estimate from only a few at-risk cases is possible but fragile. Publish the risk set at τ and a defensible uncertainty interval before treating a difference as operational. [[data-science/cohort-entry-and-survivorship-bias|Cohort entry]] guards against comparing cases with unequal opportunity to age.'),
    ('Choose a horizon supported by data', 'If the final observed follow-up is before τ or the risk set has vanished through censoring without observing a terminal event, do not extrapolate a flat line as though the remaining area were known. Shorten τ, extend follow-up, or state that the comparison is not estimable from this extract. A horizon can reflect a service target, but it must also have observable support in each group. Report the preselected horizon even if a different one looks more favorable.'),
    ('Distinguish resolution and all-exit time', 'With cancellations, the area under the all-terminal-event-free curve describes time until either resolution or cancellation. The area under a resolution-only Kaplan–Meier curve that censors cancellations answers a different question and depends on stronger assumptions. Decide which open-time quantity belongs in the operating metric. [[data-science/competing-risks-and-resolution-incidence|Competing outcomes]] should be displayed beside the bounded time summary so a faster exit cannot hide a rise in cancellations.')],
    '''def restricted_open_days(curve, horizon_days):
    if horizon_days <= 0:
        raise ValueError("horizon must be positive")
    previous_day = 0
    unresolved_share = 1.0
    open_days = 0.0
    for event_day, share_after_event in curve:
        if event_day < previous_day or not 0 <= share_after_event <= unresolved_share:
            raise ValueError("invalid curve")
        if event_day >= horizon_days:
            return open_days + (horizon_days - previous_day) * unresolved_share
        open_days += (event_day - previous_day) * unresolved_share
        previous_day = event_day
        unresolved_share = share_after_event
    if previous_day < horizon_days:
        raise ValueError("horizon exceeds observed event support")
    return open_days

steps = [(2, 0.875), (3, 0.75), (5, 0.60), (8, 0.40), (10, 0.20)]
assert abs(restricted_open_days(steps, 6) - 4.975) < 1e-12''',
    'Integrating a sorted U-step curve costs O(U) time and O(1) additional space. Bootstrapping an interval requires repeated cohort-level resampling and should preserve the case as the sampling unit. The horizon-support check is more consequential than micro-optimizing the scan.',
    ['Do not call a six-day restricted mean the eventual mean resolution time.', 'Do not compare groups at different horizons or time origins.', 'Do not extend the final observed step beyond supported follow-up without an explicit model.'],
    ['data-science/event-time-risk-sets-and-tied-outcomes','data-science/kaplan-meier-resolution-curve','data-science/competing-risks-and-resolution-incidence','data-science/support-resolution-time-audit-project'])

add('support-resolution-time-audit-project',
    'Project: audit support resolution time and competing exits',
    'Build an event ledger, verify tied-time risk sets, estimate day-six resolution and bounded open time, and separate cancellations from censoring.', [
    ('Freeze a case-level cohort', 'Start with cases created during a documented enrollment window and follow each from creation to first resolution, cancellation, or extraction cutoff. Keep one case ID, queue, created timestamp, final event timestamp, terminal status and source-record version per row. Reject impossible negative intervals and duplicate IDs before analysis. If the extract includes only cases reaching a specialist queue, change the time origin or explicitly model delayed entry. [[data-science/cohort-entry-and-survivorship-bias|Cohort entry]] is part of the estimand.'),
    ('Make the event table reviewable', 'Use an eight-case single-outcome fixture first: durations and resolution flags (2,1), (3,0), (3,1), (5,1), (5,0), (8,1), (10,0), (10,1). The risk sets at distinct days are eight, seven, five, three and two. Check that each day removes exactly its resolutions and censors before the next day. The day-three event and censor share the same seven-case denominator. [[data-science/event-time-risk-sets-and-tied-outcomes|The event-table lesson]] supplies the accounting rule.'),
    ('Reproduce the fixed-horizon metrics', 'Calculate unresolved shares of 0.875, 0.75 and 0.60 after days two, three and five. Day-six estimated resolution is 0.40, and restricted mean unresolved time through day six is 4.975 case-days. These are training-fixture values, not a production service claim. Capture the calculation code, denominator table, selected horizon and extraction cutoff in the project output. [[data-science/restricted-mean-unresolved-time|The bounded-time measure]] avoids inventing a distant tail.'),
    ('Introduce cancellations deliberately', 'Create a second six-case ledger with one resolution at day two; one cancellation and one censor at day three; one resolution at day five; one resolution and one cancellation at day seven. Verify final cumulative resolution incidence 11/18 and cancellation incidence 7/18. Do not merge this fixture into the first one: it tests a different outcome policy. Explain why censoring cancellations in a resolution-only curve would answer a different question. [[data-science/competing-risks-and-resolution-incidence|Competing risks]] provides the accounting.'),
    ('Write the release decision', 'The packet should contain cohort SQL or extraction logic, a status-code map, one-row-per-case checks, event table, unresolved curve, cumulative incidence by terminal outcome, common-horizon restricted mean, risk counts and a caveat on censoring. Compare queue groups only after checking their entry dates and follow-up maturity. If cancellation meanings shifted during collection or the day-six risk set is too thin, withhold the cross-queue comparison and document the repair needed.')],
    '''def support_resolution_audit(case_records, horizon_days):
    if len({case_id for case_id, _, _ in case_records}) != len(case_records):
        raise ValueError("duplicate case ID")
    day_counts = {}
    for case_id, day, outcome in case_records:
        if day < 0 or outcome not in {"resolved", "cancelled", "open"}:
            raise ValueError("invalid case record")
        day_counts.setdefault(day, {"resolved": 0, "cancelled": 0, "open": 0})[outcome] += 1
    at_risk = len(case_records)
    event_free = 1.0
    resolution_incidence = 0.0
    cancellation_incidence = 0.0
    open_days = 0.0
    previous_day = 0
    for day, counts in sorted(day_counts.items()):
        if day > horizon_days:
            break
        open_days += (day - previous_day) * event_free
        resolution_incidence += event_free * counts["resolved"] / at_risk
        cancellation_incidence += event_free * counts["cancelled"] / at_risk
        event_free *= 1 - (counts["resolved"] + counts["cancelled"]) / at_risk
        at_risk -= sum(counts.values())
        previous_day = day
    if previous_day < horizon_days and at_risk == 0:
        raise ValueError("no observed support through horizon")
    open_days += (horizon_days - previous_day) * event_free
    return resolution_incidence, cancellation_incidence, open_days

cases = [("R31", 2, "resolved"), ("R32", 3, "cancelled"),
         ("R33", 3, "open"), ("R34", 5, "resolved"),
         ("R35", 7, "cancelled"), ("R36", 7, "resolved")]
resolution, cancellation, open_days = support_resolution_audit(cases, 7)
assert round(resolution, 6) == round(11 / 18, 6)
assert round(cancellation, 6) == round(7 / 18, 6)
assert open_days > 0''',
    'The ledger grouping pass is O(N) expected time and O(U) space; sorting U distinct days costs O(U log U), followed by an O(U) scan. A release build should also test timestamp ordering, status-code provenance and group-specific follow-up. These checks catch errors faster hardware cannot.',
    ['Do not reuse the single-event fixture as if its censors were known cancellations.', 'Do not publish a day-six queue comparison without sufficient follow-up in both queues.', 'Do not turn an unresolved status into a resolution event to make totals reconcile.'],
    ['data-science/event-time-risk-sets-and-tied-outcomes','data-science/kaplan-meier-resolution-curve','data-science/competing-risks-and-resolution-incidence','data-science/restricted-mean-unresolved-time'])

assert len(lessons) == 5
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
               featured=False, sort_order=12800 + index, status='published', published_at=stamp,
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
if not any(module['title'] == 'Survival analysis and competing outcomes' for module in hub['data']['modules']):
    hub['data']['modules'].insert(-1, {'title':'Survival analysis and competing outcomes',
                                      'summary':'Build risk sets, estimate unresolved time, separate terminal outcomes and report a supported horizon.',
                                      'lessons':tutorial_paths})
apply_module = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
if project_path not in apply_module['lessons']:
    apply_module['lessons'].append(project_path)
if '<h2>Survival analysis and competing outcomes</h2>' not in hub['body']:
    hub['body'] += '<h2>Survival analysis and competing outcomes</h2>' + links(tutorial_paths)
    hub['body'] += '<h2>Support resolution-time project</h2>' + links([project_path])
hub['updated_at'] = stamp

project_hub = by_path[project_hub_path]
if project_path not in project_hub['data']['modules'][0]['lessons']:
    project_hub['data']['modules'][0]['lessons'].append(project_path)
if '<h2>Support resolution-time project</h2>' not in project_hub['body']:
    project_hub['body'] += '<h2>Support resolution-time project</h2>' + links([project_path])
project_hub['updated_at'] = stamp

for source, target in [
    ('data-science/right-censoring-and-time-to-event', tutorial_paths[0]),
    ('data-science/cohort-entry-and-survivorship-bias', tutorial_paths[1]),
    ('data-science/right-censoring-and-time-to-event', tutorial_paths[2]),
    ('data-science/metric-denominator-and-cohort', tutorial_paths[3]),
    ('data-science/right-censoring-and-time-to-event', project_path),
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
