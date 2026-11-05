"""Add original SQL analysis lessons to the Data Science curriculum."""
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
    'sql-null-semantics-and-counts',
    'sql-conditional-aggregation-and-cohort-rates',
    'sql-window-functions-and-event-selection',
    'sql-reconciliation-and-query-cost',
    'support-intake-sql-audit-project',
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

add('sql-null-semantics-and-counts',
    'SQL null semantics: count records without inventing outcomes',
    'SQL null is an unknown value marker, not a zero, an empty string or a failed outcome.', [
    ('Separate rows from observed values', 'A support export has 47 eligible case rows, but only 39 have a reviewer outcome. COUNT(*) returns 47 while COUNT(review_outcome) returns 39. Both numbers are useful and answer different questions. A resolved-rate denominator cannot be inferred from one count without a written cohort policy. [[data-science/missing-data-policy|Missing-data rules]] must identify unknown, not applicable and not yet observed outcomes before SQL turns them into metrics.'),
    ('Use three-valued predicates deliberately', 'A predicate such as review_outcome = 1 does not evaluate to false when the outcome is null; it evaluates to unknown, and WHERE removes that row. Likewise, review_outcome != 1 does not select null rows. Write IS NULL for unknowns and define whether the metric uses all eligible rows or only observed rows. In conditional aggregation, use ELSE 0 for a known false condition but preserve an explicit unknown count alongside it.'),
    ('Watch NOT IN with nulls', 'If an exclusion subquery returns even one null ID, case_id NOT IN (subquery) can yield unknown for every candidate and remove the whole cohort. Use NOT EXISTS with a correlated, non-null identity comparison, and validate null IDs in the exclusion source. This is a query-semantics failure, not a rare numerical corner case. A zero-row result should trigger an anomaly check before publication.'),
    ('Keep missingness visible', 'For each segment, report eligible cases, reviewed cases, positive reviewed cases and unknown outcomes. A segment with five positives from 37 reviewed cases out of 47 eligible cases has an observed-case positive rate of 5/37, but its eligible-case positive fraction is not known without assumptions about the ten missing outcomes. [[data-science/nonresponse-bias-and-follow-up|Nonresponse bounds]] give one way to show that gap.'),
    ('Test against a tiny fixture', 'Include one row with review_outcome = 1, one with 0 and one with NULL. Assert the three counts separately. Add a null to the exclusion table and confirm the NOT EXISTS query still returns eligible cases. Run the fixture in the same SQL dialect as production; subtle casts and boolean behavior vary by engine.')],
    'WITH review_cases(case_id, review_outcome) AS (\n    VALUES (201, 1), (202, 0), (203, NULL), (204, 1)\n)\nSELECT COUNT(*) AS eligible_cases,\n       COUNT(review_outcome) AS reviewed_cases,\n       SUM(CASE WHEN review_outcome = 1 THEN 1 ELSE 0 END) AS positive_reviews,\n       SUM(CASE WHEN review_outcome IS NULL THEN 1 ELSE 0 END) AS unknown_reviews\nFROM review_cases;',
    'The aggregation scans N rows in O(N) time and O(1) memory for one global group. Grouped counts require O(G) aggregate state for G segments. A NOT EXISTS anti-join can use an indexed case ID; without an index, a nested plan may repeatedly scan the exclusion table.',
    ['Do not treat COUNT(column) as a count of all cohort rows.', 'Do not expect a comparison with NULL to be true or false.', 'Do not use NOT IN when the subquery can contain null identities.'],
    ['data-science/sql-conditional-aggregation-and-cohort-rates','data-science/missing-data-policy','data-science/nonresponse-bias-and-follow-up','data-science/support-intake-sql-audit-project'])

add('sql-conditional-aggregation-and-cohort-rates',
    'SQL conditional aggregation: rates with an auditable denominator',
    'A rate query should expose its numerator, denominator and missing-outcome count before it divides.', [
    ('Start from the eligible base', 'Build the denominator from a frozen intake cohort, not from rows that happen to survive a join to outcomes. A LEFT JOIN preserves eligible cases without review; a WHERE predicate on the joined outcome can silently turn it into an inner join. If the metric is review completion, the denominator is all eligible cases. If the metric is positive among reviewed cases, the denominator is reviewed cases. Label those rates separately. [[data-science/metric-denominator-and-cohort|Cohort rules]] belong in query comments and review notes.'),
    ('Aggregate states before dividing', 'Count eligible, observed, positive and unknown with explicit CASE expressions. Protect a zero denominator with NULLIF or an equivalent guard, and do not convert the resulting undefined rate to zero. Zero means a measured rate of zero; null means no rate can be computed under the rule. Save the integer counts so readers can re-evaluate a percentage at another precision.'),
    ('Avoid multiplication through joins', 'A case may have three status events and two reviewer notes. Joining both raw tables to the case table yields six combinations for that case. COUNT(DISTINCT case_id) can hide some symptoms while sums and subgroup fields remain wrong. Reduce each child to one row per case under a declared rule before joining. [[data-science/dataset-grain-and-join-cardinality|Join cardinality]] must be tested explicitly.'),
    ('Keep time windows explicit', 'A case submitted near the analysis cutoff may not have enough follow-up for a two-day resolution outcome. A CASE expression cannot fix that by itself. Store follow_up_eligible as a separate condition, and report how many cases fall outside it. If late events can revise an outcome, pin the event snapshot used by the query. [[data-science/cohort-entry-and-survivorship-bias|Cohort entry]] and observation time are separate columns.'),
    ('Read a concrete result', 'In a five-case fixture, three have outcomes, two are positive and two are unknown. The observed positive rate is 2/3; the reviewed fraction is 3/5. The SQL returns both counts and leaves the analyst to choose the rate that matches the decision. A dashboard that shows only 66.7% conceals the 40% unobserved share.')],
    'WITH case_outcomes(case_id, eligible, review_outcome) AS (\n    VALUES (301, 1, 1), (302, 1, 0), (303, 1, NULL),\n           (304, 1, 1), (305, 1, NULL)\n), counts AS (\n    SELECT SUM(CASE WHEN eligible = 1 THEN 1 ELSE 0 END) AS eligible_count,\n           SUM(CASE WHEN eligible = 1 AND review_outcome IS NOT NULL THEN 1 ELSE 0 END) AS reviewed_count,\n           SUM(CASE WHEN eligible = 1 AND review_outcome = 1 THEN 1 ELSE 0 END) AS positive_count\n    FROM case_outcomes\n)\nSELECT eligible_count, reviewed_count, positive_count,\n       1.0 * positive_count / NULLIF(reviewed_count, 0) AS positive_among_reviewed,\n       1.0 * reviewed_count / NULLIF(eligible_count, 0) AS reviewed_fraction\nFROM counts;',
    'The aggregate is O(N) time and O(1) memory before grouping. In a warehouse, pruning by cohort window and joining already deduplicated outcome rows reduces scan cost; COUNT(DISTINCT) over an exploded join can require much more memory and still leave other measures wrong.',
    ['Do not filter joined outcomes in WHERE when the cohort must retain unobserved cases.', 'Do not publish a ratio without its integer numerator and denominator.', 'Do not use COUNT(DISTINCT) as a substitute for defining one outcome row per case.'],
    ['data-science/sql-null-semantics-and-counts','data-science/sql-window-functions-and-event-selection','data-science/dataset-grain-and-join-cardinality','data-science/support-intake-sql-audit-project'])

add('sql-window-functions-and-event-selection',
    'SQL window functions: select one event with a deterministic rule',
    'A window function can rank event versions without collapsing the audit trail before the selection rule is applied.', [
    ('Define which version wins', 'A support case can have several resolution events because agents edit status or a replay emits corrected records. Decide whether the analysis uses the latest event known at a snapshot, the first valid resolution or the final resolution before cutoff. These are different measures. For a latest-known snapshot, rank events per case by occurrence time, revision and stable event ID, all descending. The final event ID breaks ties and makes reruns deterministic.'),
    ('Apply the cutoff before ranking', 'Filter event rows to those known by the analysis snapshot, then compute ROW_NUMBER. Ranking all history first and filtering afterward can discard an older valid event when the globally latest one arrived after the cutoff. This is a point-in-time error. [[data-science/reproducible-analysis-snapshot|Snapshot discipline]] requires the source revision and cutoff to be fixed in the review packet.'),
    ('Retain the losing rows for audit', 'The ranked table should expose row number and tie-break columns, even if the final metric keeps only rank one. Count cases with multiple candidates and exact timestamp ties. A change in winning row after a backfill should produce a revision record, not an unexplained jump in a published rate. [[data-engineering/warehouse-history-asof-join|Historical joins]] are the next boundary when event rows need versioned dimensions.'),
    ('Separate sequence from aggregate', 'ROW_NUMBER chooses a record; SUM OVER computes a running measure while keeping every record. Neither is a cure for duplicate business identities. If two source IDs refer to the same case, resolve identity first. A window partition on the wrong key creates plausible but invalid output, especially when a customer has several separate cases.'),
    ('Probe a tie fixture', 'For case 401, two events share the same occurrence timestamp but revisions 1 and 2. Revision 2 should win. For case 402, an event arrived after the snapshot; it must be absent from the ranked input. Assert the two selected IDs and the count of excluded late events. Without those assertions, ordering bugs tend to appear only when source traffic is replayed.')],
    'WITH status_events(case_id, event_id, occurred_minute, revision, known_minute, status) AS (\n    VALUES (401, 91, 20, 1, 25, \'open\'),\n           (401, 92, 20, 2, 27, \'resolved\'),\n           (402, 93, 17, 1, 21, \'open\'),\n           (402, 94, 29, 1, 35, \'resolved\')\n), ranked AS (\n    SELECT case_id, event_id, status,\n           ROW_NUMBER() OVER (\n               PARTITION BY case_id\n               ORDER BY occurred_minute DESC, revision DESC, event_id DESC\n           ) AS position\n    FROM status_events\n    WHERE known_minute <= 30\n)\nSELECT case_id, event_id, status\nFROM ranked\nWHERE position = 1\nORDER BY case_id;',
    'For N event rows, partition sorting is O(N log N) worst-case time and may spill to disk. An index aligned with case ID and ordering columns can reduce sorting work, though snapshot filters and engine plans matter. Retaining the ranked audit view costs storage but makes revisions explainable.',
    ['Do not rank future-known events before applying the snapshot cutoff.', 'Do not order only by a timestamp that can tie.', 'Do not partition by customer ID when the metric unit is a case.'],
    ['data-science/sql-conditional-aggregation-and-cohort-rates','data-science/sql-reconciliation-and-query-cost','data-science/reproducible-analysis-snapshot','data-science/support-intake-sql-audit-project'])

add('sql-reconciliation-and-query-cost',
    'SQL reconciliation: prove the cohort survived each transformation',
    'A query that returns a plausible number still needs row-count, key and unmatched-record checks at each stage.', [
    ('Write conservation checks', 'Start with the raw intake IDs and a declared eligibility rule. Count raw events, distinct case IDs, eligible case IDs, matched outcomes, unmatched outcomes and final metric rows. An eligibility filter may intentionally remove records, but every removal needs a reason and a count. A one-to-one outcome join should preserve eligible case count even when the outcome is missing. [[data-science/dataset-grain-and-join-cardinality|Cardinality checks]] make this an executable contract.'),
    ('Use anti-joins to find gaps', 'A LEFT JOIN from eligible cases to selected outcomes followed by WHERE outcome.case_id IS NULL identifies cases without an outcome. Reverse the direction to find orphaned outcomes with no eligible case. Report both. An unmatched case is not automatically bad data: it may be open or censored. The ledger should classify it before any rate denominator changes. [[data-science/right-censoring-and-time-to-event|Open-case semantics]] matter here.'),
    ('Inspect the plan, not just the SQL text', 'Run the database EXPLAIN facility on the exact production-shaped query. Check whether filters prune partitions and whether key joins use indexes or scan large tables repeatedly. A query that runs quickly on 47 rows may become expensive at 47 million. Query plans vary by engine and statistics, so record the plan with a representative input scale. Avoid adding an index solely from intuition when the warehouse is columnar or the workload is dominated by partition scans.'),
    ('Protect metric revisions', 'After a backfill, compare old and new snapshots by case ID: added, removed and changed outcome rows. Recompute the rate from both snapshots and attribute the difference to those categories. If 13 late resolutions arrive, a previously published two-day rate may restate; the system should show the revision version and reason. [[data-engineering/backfill-publication-boundary|Atomic publication]] prevents readers from seeing a half-updated table.'),
    ('Set an explicit stop rule', 'Fail the metric build if eligible IDs are duplicated, outcome IDs are unexpectedly orphaned, or the final joined row count differs from the eligible count under a one-to-one contract. Separate expected open cases from unexpected missing cases, and keep the failed batch available for investigation. A zero-row query without an error is not proof of a zero rate.')],
    'WITH eligible_cases(case_id) AS (\n    VALUES (501), (502), (503), (504)\n), selected_outcomes(case_id, solved) AS (\n    VALUES (501, 1), (502, 0), (505, 1)\n), joined AS (\n    SELECT intake.case_id, outcome.solved\n    FROM eligible_cases AS intake\n    LEFT JOIN selected_outcomes AS outcome ON outcome.case_id = intake.case_id\n)\nSELECT COUNT(*) AS eligible_after_join,\n       SUM(CASE WHEN solved IS NULL THEN 1 ELSE 0 END) AS unmatched_eligible,\n       COUNT(solved) AS observed_outcomes\nFROM joined;',
    'A hash join of N eligible cases and M outcomes costs O(N + M) expected time and space; indexed nested-loop joins have a different cost profile. Reconciliation counts can run alongside the final query, but retaining per-ID differences for a backfill takes O(N + M) storage.',
    ['Do not accept a plausible rate without checking row conservation.', 'Do not classify all unmatched cases as data corruption.', 'Do not infer production cost from a tiny fixture or from SQL syntax alone.'],
    ['data-science/sql-window-functions-and-event-selection','data-science/sql-conditional-aggregation-and-cohort-rates','data-engineering/quality-quarantine-and-reconciliation','data-science/support-intake-sql-audit-project'])

add('support-intake-sql-audit-project',
    'Project: build an auditable support-intake SQL report',
    'Build a repeatable SQL report that keeps every eligible intake case visible while selecting one event version and exposing missing outcomes.', [
    ('Create a fixture with failure cases', 'Use 47 eligible cases and seven ineligible records. Add duplicate status events, one exact occurrence-time tie with distinct revisions, four cases still open at cutoff, three reviewer outcomes recorded as null and one outcome whose case ID is absent from the intake table. Save both event occurrence and known-at times. The fixture should be small enough to inspect by hand but large enough to expose a wrong join or denominator.'),
    ('Write a staged query', 'Stage one selects eligible case IDs. Stage two filters status events by the frozen known-at cutoff. Stage three ranks status versions per case with a stable tie-break. Stage four left-joins one selected outcome back to every eligible case. Stage five calculates eligible, observed, positive and unknown counts before any rate. [[data-science/sql-window-functions-and-event-selection|Deterministic event selection]] and [[data-science/sql-conditional-aggregation-and-cohort-rates|conditional counts]] must remain separate steps.'),
    ('Reconcile every transition', 'Assert the eligible count remains 47 after the outcome join. Count duplicate raw event IDs, multiply matched cases and orphaned outcomes before computing the headline. Run a reverse anti-join for outcomes with no eligible intake record. Label open cases separately from missing reviewer decisions. [[data-science/sql-reconciliation-and-query-cost|Reconciliation rules]] should fail the report when identities unexpectedly multiply.'),
    ('Publish two rates, not one', 'Report review coverage over all eligible cases and positive share among observed reviews, with each integer numerator and denominator. State that the observed positive share does not estimate the eligible-cohort share unless missing outcomes are addressed. Add a lower and upper eligible-cohort bound using the missing count. Include an analysis cutoff and a metric revision number in every output row.'),
    ('Deliver a review packet', 'Provide schema, source fixture, SQL dialect, query, execution plan from a representative table size, expected result assertions and a short note explaining unresolved cases. A peer should rerun the report, alter a tie revision, and see the selected event change without changing eligible row count. Save that as a regression check.')],
    'WITH eligible_cases(case_id) AS (\n    VALUES (601), (602), (603), (604), (605)\n), reviews(case_id, review_outcome) AS (\n    VALUES (601, 1), (602, 0), (603, NULL), (604, 1)\n), audit AS (\n    SELECT intake.case_id, reviews.review_outcome\n    FROM eligible_cases AS intake\n    LEFT JOIN reviews ON reviews.case_id = intake.case_id\n)\nSELECT COUNT(*) AS eligible_count, COUNT(review_outcome) AS reviewed_count,\n       SUM(CASE WHEN review_outcome = 1 THEN 1 ELSE 0 END) AS positive_count,\n       SUM(CASE WHEN review_outcome IS NULL THEN 1 ELSE 0 END) AS unknown_count\nFROM audit;',
    'A staged report over N eligible cases and M events is dominated by event sorting at O(M log M) in the worst case, plus joins at O(N + M) expected cost when hash joins are available. Store per-stage counts and selected event IDs; aggregate outputs alone cannot explain a revision.',
    ['Do not turn a left join into an inner join with a post-join WHERE filter.', 'Do not report the positive share without review coverage.', 'Do not discard tie-breaking and cutoff logic from the delivered query.'],
    ['data-science/sql-null-semantics-and-counts','data-science/sql-conditional-aggregation-and-cohort-rates','data-science/sql-window-functions-and-event-selection','data-science/sql-reconciliation-and-query-cost'])

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
                  '<pre><code class="language-sql">' + html.escape(item['code']) + '</code></pre>',
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
               featured=False, sort_order=11800 + index, status='published', published_at=stamp,
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
    hub['data']['modules'].insert(-1, {'title':'SQL analysis and metric verification',
                                      'summary':'Keep unknowns, denominators, event versions and row counts explicit.',
                                      'lessons':tutorial_paths})
apply_module = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
if project_path not in apply_module['lessons']:
    apply_module['lessons'].append(project_path)
if '<h2>SQL analysis and metric verification</h2>' not in hub['body']:
    hub['body'] += ('<h2>SQL analysis and metric verification</h2>' + links(tutorial_paths)
                    + '<h2>SQL audit project</h2>' + links([project_path]))
hub['updated_at'] = stamp

project_hub = by_path[project_hub_path]
if project_path not in project_hub['data']['modules'][0]['lessons']:
    project_hub['data']['modules'][0]['lessons'].append(project_path)
if '<h2>SQL audit project</h2>' not in project_hub['body']:
    project_hub['body'] += '<h2>SQL audit project</h2>' + links([project_path])
project_hub['updated_at'] = stamp

for source, target in [
    ('data-science/missing-data-policy', tutorial_paths[0]),
    ('data-science/metric-denominator-and-cohort', tutorial_paths[1]),
    ('data-science/dataset-grain-and-join-cardinality', tutorial_paths[2]),
    ('data-science/reproducible-analysis-snapshot', tutorial_paths[2]),
    ('data-engineering/quality-quarantine-and-reconciliation', tutorial_paths[3]),
    ('data-science/column-profile-and-domain-constraints', tutorial_paths[3]),
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
print(json.dumps({'new_articles':len(lessons), 'new_projects':1, 'crosslinks_from_existing':6}))
