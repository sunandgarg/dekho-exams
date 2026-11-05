"""Publish original lessons on large-scale migration and materialized-view refresh."""
import datetime
import html
import json
import re
import runpy
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'src/data/fixtures.json'
HUB = 'data-engineering/data-engineering-tutorial'
PROJECT_HUB = HUB + '/project'
MIGRATION = 'Online schema migration and historical repair'
REFRESH = 'Materialized views and freshness budgets'
context = runpy.run_path(str(ROOT / 'work/add-data-engineering-lineage-residency-20261006.py'))
LESSONS = context['LESSONS']
LESSONS.clear()
add = context['add']

add('expand-contract-schema-migration', 'Expand-contract schema migration',
    'An expand-contract migration changes a shared data contract in stages so old and new readers can coexist until measured evidence permits the old field to retire.', [
    ('Start with the reader inventory', 'A raw event carries amount_cents, while a new producer wants amount_minor_units and currency. The rename is not merely a DDL command: dashboards, streaming jobs, backfills and exports may depend on the old name. Inventory readers by owner, query identity and last observed use. Mark unknown readers as a release blocker until access logs or owner review resolve them. [[data-engineering/schema-compatibility-and-consumer-rollout|Consumer rollout]] supplies the compatibility plan.'),
    ('Expand before changing writers', 'Add the new nullable fields and publish a schema version that accepts both representations. Write both fields from one validated amount in the producer; a second independent calculation can produce disagreement. Test the serialized event and persisted table, since compatibility in one layer does not guarantee compatibility in the other. Keep the old field available while lagging readers and retained historical objects still require it.'),
    ('Backfill with a fence', 'A large table should be repaired in bounded partitions rather than one unbounded rewrite. Pin input snapshot and transform revision, write candidates to new generations, and record a high-water position. Live updates can race a backfill: compare source positions or use a change log so a stale repair never overwrites a later value. [[data-engineering/backfill-publication-boundary|The publication boundary]] prevents a half-migrated partition from reaching readers.'),
    ('Move readers using evidence', 'Switch one consumer at a time to the new field, then compare counts, null rates and monetary totals by event date and currency. If historical rows cannot be converted, surface an explicit unknown state; do not invent a zero amount. Observe reader lag through the maximum replay horizon before claiming the old field is unused. A rollback should restore the previous reader pointer without losing newly written events.'),
    ('Contract only after the horizon', 'Stop dual-writing after every required reader has moved and historical replay tests pass. Remove the old field in a later release, not in the same deployment that switches readers. Rehearse a delayed reader, a backfill retry and an emergency rollback. Attach the schema IDs, reconciliation output and approval to the release manifest so a future operator can reconstruct the decision.')],
    '''events = [
    {"id": "pay-47", "amount_cents": 2375, "currency": "USD"},
    {"id": "pay-48", "amount_cents": 6420, "currency": "USD"},
]

def expand_payment(event):
    migrated = dict(event)
    migrated["amount_minor_units"] = event["amount_cents"]
    return migrated

expanded = [expand_payment(event) for event in events]
assert sum(row["amount_minor_units"] for row in expanded) == 8795
assert all(row["amount_cents"] == row["amount_minor_units"] for row in expanded)''',
    'The reference pass is O(N) time and O(N) output space for N events. At scale, dual fields increase storage and transport size during the overlap, while a historical rewrite consumes I/O proportional to retained bytes. Partitioned checkpoints limit retry work; they do not remove the need to reconcile concurrent updates and old reader behavior.',
    ['Do not drop a field because the newest application build no longer reads it.', 'Do not let a stale backfill replace a newer live update.', 'Do not equate a nullable new column with a complete historical migration.'],
    ['data-engineering/schema-compatibility-and-consumer-rollout', 'data-engineering/schema-registry-transitive-compatibility', 'data-engineering/backfill-publication-boundary', 'data-engineering/migration-reconciliation-and-cutover', 'data-engineering/payment-schema-cutover-project'], MIGRATION)

add('migration-reconciliation-and-cutover', 'Migration reconciliation and cutover gates',
    'A cutover gate compares old and new representations at a fixed input position and refuses publication when correctness, coverage or replay guarantees differ.', [
    ('Choose a stable comparison point', 'A migrating order ledger continues to receive events. Comparing old output at position 81 with new output at position 84 creates a false mismatch. Pin both calculations to the same source position, schema revision and event-time interval. Store the pin in a manifest. For a stream, wait until both paths have acknowledged the position; wall-clock completion alone is not a consistency boundary.'),
    ('Compare more than totals', 'Equal aggregate revenue can hide one duplicate positive amount and one missing negative adjustment. Check primary-key sets, duplicate counts, row-level amount hashes, null rates, currency distribution and totals by region and date. Treat accepted exclusions as named rules with counts. [[data-engineering/quality-quarantine-and-reconciliation|Quality quarantine]] gives mismatches a place to wait without contaminating a published reader.'),
    ('Separate candidate from visible state', 'Write the new representation and index as candidate generations. Keep readers on the last accepted pointer until every check passes. If an index build fails after the table is correct, the release remains incomplete. An atomic pointer switch must identify the table and serving index generations together; otherwise the application can query a new table through an old index.'),
    ('Prove rollback and delayed replay', 'Before cutover, replay a delayed event encoded with the old schema and verify the new path still interprets it. Then move the reader pointer, force a failed post-cutover check, and restore the old pointer. Preserve the new candidate for diagnosis. Rollback of the pointer does not reverse external side effects, so downstream exports need their own versioned handoff or pause window.'),
    ('Make failure observable', 'A failed gate should identify the interval, input position, first differing key, affected count and failed predicate without exposing sensitive row payloads in public logs. Record gate duration separately from migration throughput. A pass at one small canary interval is not proof for the full history; run the same controls across every partition included in the release.')],
    '''old_rows = {"order-47": 2375, "order-48": -125, "order-49": 6400}
new_rows = {"order-47": 2375, "order-48": -125, "order-49": 6400}

def reconciliation_report(previous, candidate):
    keys = previous.keys() | candidate.keys()
    mismatched = [key for key in keys if previous.get(key) != candidate.get(key)]
    return {"equal": not mismatched, "mismatched_keys": sorted(mismatched),
            "previous_total": sum(previous.values()), "candidate_total": sum(candidate.values())}

assert reconciliation_report(old_rows, new_rows)["equal"]
new_rows["order-48"] = -100
assert reconciliation_report(old_rows, new_rows)["mismatched_keys"] == ["order-48"]''',
    'The reference comparison is O(N) expected time and O(N) key state for N records. A distributed version can compare partition digests first, then inspect only mismatched partitions, but digest equality alone is not a substitute for control totals and key counts. Candidate generations temporarily double storage, and each gate adds reads before publication.',
    ['Do not compare outputs produced from different source positions.', 'Do not accept equal totals as proof of equal records.', 'Do not switch the table pointer before the serving index is ready.'],
    ['data-engineering/expand-contract-schema-migration', 'data-engineering/quality-quarantine-and-reconciliation', 'data-engineering/lakehouse-snapshot-and-atomic-commit', 'data-engineering/serving-index-and-freshness-contract', 'data-engineering/payment-schema-cutover-project'], MIGRATION)

add('payment-schema-cutover-project', 'Project: migrate a live payment amount contract',
    'Move a payment mart from one amount field to a currency-aware contract while preserving old readers, late events and a reversible release pointer.', [
    ('Prepare the contract', 'Create 470 payment records under the old schema, with separate settled and refunded events. Record schema IDs, readers, source positions and the maximum supported replay interval. Add amount_minor_units and currency without removing amount_cents. Require dual-write equality for existing currency records and quarantine records lacking a trustworthy currency. [[data-engineering/expand-contract-schema-migration|The staged migration]] prevents one deployment from forcing all consumers to change at once.'),
    ('Repair history in bounded units', 'Split historical data into event-date partitions and pin a source snapshot for each repair. Persist partition progress and candidate output generation. Inject a live correction during the repair; its later source position must win over the old snapshot. Rerun one partition to prove idempotence. The candidate remains hidden until all partitions needed by the reader contract have passed.'),
    ('Reconcile old and new paths', 'Calculate totals, refunded amounts, primary-key sets, duplicate counts and null rates by currency and date from the same source position. Introduce a duplicated refund so a global total comparison is insufficient. [[data-engineering/migration-reconciliation-and-cutover|The cutover gate]] must fail and report the first differing key. Repair it, rerun the check and retain both failed and successful evidence.'),
    ('Cut over and roll back', 'Build the new table and serving index as one candidate release. Move a canary reader, then all approved readers, using versioned pointers. Simulate an index build failure before publication and confirm the old reader still answers. After a successful cutover, revert the pointer once and verify the old representation remains valid during the overlap window.'),
    ('Submit release evidence', 'Deliver the reader inventory, schema changes, dual-write comparison, partition checkpoints, pinned source positions, mismatch report, fixed reconciliation, old and new pointer IDs, rollback result and delayed old-schema replay. Do not report completion until the replay horizon closes and owner review confirms that retiring amount_cents will not break a dormant export.')],
    '''payments = [("pay-47", 2375), ("pay-48", -125), ("pay-49", 6400)]

def materialize_amounts(records):
    return {payment_id: {"amount_cents": cents,
                         "amount_minor_units": cents, "currency": "USD"}
            for payment_id, cents in records}

candidate = materialize_amounts(payments)
assert sum(row["amount_minor_units"] for row in candidate.values()) == 8650
assert all(row["amount_cents"] == row["amount_minor_units"]
           for row in candidate.values())''',
    'The sample materialization uses O(N) time and O(N) state. In a real lake or warehouse, the migration pays for dual writes, candidate snapshots, index rebuilds and partition-level comparison scans. A bounded repair budget limits blast radius and makes retries affordable; premature removal of the old field saves bytes while risking delayed consumers and historical replay.',
    ['Do not drop the old field before delayed readers and exports have moved.', 'Do not let a duplicated refund pass because another error cancels its total.', 'Do not publish a table whose serving index build failed.'],
    ['data-engineering/expand-contract-schema-migration', 'data-engineering/migration-reconciliation-and-cutover', 'data-engineering/schema-registry-transitive-compatibility', 'data-engineering/backfill-publication-boundary', 'data-engineering/replay-manifest-and-audit-trail'], MIGRATION, True)

add('materialized-view-refresh-strategies', 'Materialized view refresh strategies',
    'A materialized view trades extra storage and refresh work for faster reads; the refresh mode must match the source change pattern and the freshness contract.', [
    ('Choose the result grain', 'A store-day sales summary should have one key per store and day. If the source query joins to a nonunique dimension, one order can multiply before aggregation. Define the key and test uniqueness before selecting a refresh strategy. [[data-engineering/fact-grain-and-measure-additivity|Measure additivity]] determines which fields can be summed and which need recomputation from components.'),
    ('Compare full and incremental work', 'A full refresh recomputes every result, making correctness straightforward but paying a read and write cost proportional to the full input. An incremental refresh reads changes and updates affected keys, but it needs stable row identity, delete handling and a way to revisit old groups after corrections. Small deltas do not guarantee cheap refresh when one change invalidates a large join or window.'),
    ('Treat freshness as observed age', 'A target such as five minutes is a goal for how old the consumer-visible answer may be, not a promise that a scheduler runs exactly every five minutes. Record source commit time, last successful refresh time, table generation and serving pointer. If refresh duration exceeds the target, queueing more refreshes can deepen the backlog. [[data-engineering/serving-index-and-freshness-contract|The freshness contract]] is checked at the reader boundary.'),
    ('Handle late and deleted input', 'A refund arriving tomorrow may change last month’s store-day aggregate. A watermark that only reads newer event dates misses it. Drive the refresh from change positions or affected keys, and include deletes and corrections in the same state transition. Keep a bounded replay horizon with a documented older-correction path; silently ignoring old changes makes the view fast but wrong.'),
    ('Test publication and recovery', 'Build refreshed rows in a candidate generation and publish atomically after row-count, key and control-total checks. Inject a failed refresh and confirm the last good view remains queryable with its age visible. Benchmark both full and incremental modes under realistic update concentration, because a tiny uniform test data set hides skew and write amplification.')],
    '''sales = [("west", "2026-10-01", 2375),
         ("west", "2026-10-01", -125),
         ("east", "2026-10-01", 6400)]

def rebuild_store_day(events):
    totals = {}
    for store, day, cents in events:
        key = (store, day)
        totals[key] = totals.get(key, 0) + cents
    return totals

assert rebuild_store_day(sales)[("west", "2026-10-01")] == 2250''',
    'The reference full rebuild costs O(N) expected time and O(G) state for N events and G store-day groups. Incremental work can approach O(C) for C changed records when affected groups are indexed, but maintaining that index and handling deletes adds state. Refreshes consume compute, storage and write I/O even when no user is querying the view.',
    ['Do not mistake a refresh schedule for a measured freshness guarantee.', 'Do not ignore deletes or corrections outside the newest event-date partition.', 'Do not assume incremental refresh is cheap for a broad join.'],
    ['data-engineering/fact-grain-and-measure-additivity', 'data-engineering/serving-index-and-freshness-contract', 'data-engineering/watermark-retention-and-late-corrections', 'data-engineering/refresh-lag-and-cost-budget', 'data-engineering/store-day-view-refresh-project'], REFRESH)

add('refresh-lag-and-cost-budget', 'Refresh lag and cost budgets',
    'A refresh budget joins an observed staleness limit with compute and failure limits, so a view is neither perpetually stale nor needlessly rebuilt.', [
    ('Define the consumer deadline', 'A dashboard may tolerate a 12-minute-old store-day total, while fraud operations need a fresher feed. Record the maximum age at the point of query, the consequence of stale output and whether a dated last-good value is acceptable. The allowed lag must include ingestion, upstream processing, view refresh and index publication; assigning the full budget to the final job hides upstream delay.'),
    ('Measure stage age separately', 'Track newest accepted source position, candidate refresh start, last committed view generation and current reader pointer. A view can be freshly rebuilt from old source data. Emit both source age and view age, and label the interval when a correction window is still open. [[data-engineering/pipeline-slos-and-error-budgets|Pipeline SLOs]] should count the consumer-visible failure, not only successful scheduler invocations.'),
    ('Choose a policy from cost curves', 'Shorter intervals increase fixed startup work, metadata traffic and contention; longer intervals increase staleness and the size of each change set. Measure bytes scanned, changed groups, write volume and wall time per refresh. Use these observations to choose a target and capacity margin. When a backlog appears, prioritize the newest useful generation and cancel superseded work only if publication semantics permit.'),
    ('Degrade explicitly under stress', 'If the next refresh would exceed its deadline, keep a dated last-good snapshot and raise a freshness breach. Do not replace a correct but stale answer with an incomplete candidate. Define whether a full rebuild is allowed during peak traffic and reserve a recovery budget. [[data-engineering/query-admission-queues-and-deadlines|Admission control]] can protect interactive reads while a large repair runs.'),
    ('Exercise a burst', 'Generate 47 change batches while a refresh worker is paused, then resume it. Observe queue depth, actual age, scanned bytes and first good consumer query. Inject one failed candidate followed by a successful generation. Verify that a green job status without a moved serving pointer does not clear the breach. Record the cost per recovered minute of freshness.')],
    '''from datetime import datetime, timezone

def visible_age_seconds(now, source_committed_at, view_built_at):
    return {"source_age": (now - source_committed_at).total_seconds(),
            "view_age": (now - view_built_at).total_seconds()}

clock = datetime(2026, 10, 6, 12, 0, tzinfo=timezone.utc)
ages = visible_age_seconds(clock,
    datetime(2026, 10, 6, 11, 47, tzinfo=timezone.utc),
    datetime(2026, 10, 6, 11, 58, tzinfo=timezone.utc))
assert ages == {"source_age": 780.0, "view_age": 120.0}
assert ages["source_age"] > 720''',
    'The age check is O(1) time and space. Refresh cost depends on bytes scanned, changed groups and view write amplification, while telemetry cost grows with retained samples and workload dimensions. A fixed worker reservation costs capacity even when idle; the alternative is a documented recovery delay during bursts. Alert on observed age rather than an ideal schedule.',
    ['Do not infer fresh source data from a recent view build timestamp.', 'Do not clear a freshness incident before the reader pointer moves.', 'Do not shorten a target lag without checking whether refresh runtime can meet it.'],
    ['data-engineering/materialized-view-refresh-strategies', 'data-engineering/pipeline-slos-and-error-budgets', 'data-engineering/query-admission-queues-and-deadlines', 'data-engineering/pipeline-cost-attribution-and-right-sizing', 'data-engineering/store-day-view-refresh-project'], REFRESH)

add('store-day-view-refresh-project', 'Project: keep a store-day view within its freshness budget',
    'Build a store-day materialization, process corrections and a refresh backlog, and prove that the consumer sees only accepted generations.', [
    ('Build the baseline', 'Load 470 order events across stores and dates, including refunds as negative amounts. Define one row per store-day and retain counts and amount components. Create a full rebuild as a correctness oracle, then an incremental candidate driven by changed order IDs. Check that a duplicated dimension row cannot multiply a sale. [[data-engineering/materialized-view-refresh-strategies|The refresh strategy]] depends on the affected-key path, not merely the small size of one delta.'),
    ('Apply late corrections', 'Correct one old refund and delete one order that had already contributed to a published day. Recompute those affected store-day groups from their remaining source rows, or maintain reversible components with exact row identity. Comparing only the newest event date must fail this test. Record the change position and candidate generation so a replay of the same correction cannot change totals twice.'),
    ('Budget a burst', 'Set a 12-minute consumer age target and queue 47 small change batches while the worker is paused. Measure source age, view age, queue wait, bytes scanned and refresh duration. [[data-engineering/refresh-lag-and-cost-budget|The lag budget]] should report a breach when the source is old even if the view build timestamp is recent. Preserve a dated last-good answer until a valid candidate catches up.'),
    ('Gate the release', 'Compare the incremental candidate with the full rebuild by store-day key, row count and amount. Inject a failed index build: the table candidate may exist, but the reader pointer must remain on the old accepted generation. After repair, publish the table and index pointer together, query through the consumer route, and record the first generation that meets the age target.'),
    ('Deliver an operating record', 'Submit source and view positions, refresh plan, changed-key inventory, correction and delete tests, full-versus-incremental comparison, backlog curve, cost per run, failed candidate, accepted pointer and consumer query. Include one rollback and one retry. A task-success message without a tested reader generation does not meet the project acceptance criteria.')],
    '''orders = {"order-47": ("west", "2026-10-01", 2375),
          "order-48": ("west", "2026-10-01", -125),
          "order-49": ("east", "2026-10-01", 6400)}

def store_day_totals(source):
    totals = {}
    for store, day, cents in source.values():
        key = (store, day)
        totals[key] = totals.get(key, 0) + cents
    return totals

assert store_day_totals(orders)[("west", "2026-10-01")] == 2250
orders.pop("order-48")
assert store_day_totals(orders)[("west", "2026-10-01")] == 2375''',
    'The oracle rebuild uses O(N) time and O(G) state for N source records and G groups. Incremental refresh can narrow reads to changed keys, but requires an index from order identity to group and a safe path for deletes. The project intentionally retains a last-good snapshot and failed candidate, which increase temporary storage while making rollback and diagnosis possible.',
    ['Do not update only recent event dates when old refunds can change.', 'Do not expose a table candidate before the matching index is ready.', 'Do not call the freshness target met until the consumer query reads the new generation.'],
    ['data-engineering/materialized-view-refresh-strategies', 'data-engineering/refresh-lag-and-cost-budget', 'data-engineering/fact-grain-and-measure-additivity', 'data-engineering/serving-index-and-freshness-contract', 'data-engineering/replay-manifest-and-audit-trail'], REFRESH, True)

def publish():
    rows = json.loads(FIXTURE.read_text())
    paths = {item['path'] for item in LESSONS}
    assert len(paths) == len(LESSONS) == 6
    rows = [row for row in rows if row['path'] not in paths]
    by_path = {row['path']: row for row in rows}
    titles = {path: row['title'] for path, row in by_path.items()}
    titles.update({item['path']: item['title'] for item in LESSONS})
    now = datetime.datetime.now(datetime.UTC).isoformat()

    def prose(value):
        return re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',
                      lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                      html.escape(value))

    def link_list(targets):
        return '<ul>' + ''.join('<li><a href="/' + target + '">' +
                               html.escape(titles[target]) + '</a></li>' for target in targets) + '</ul>'

    changed = set(paths) | {HUB, PROJECT_HUB}
    for index, item in enumerate(LESSONS):
        for target in item['related']:
            assert target in titles, target
        body = '<p>' + html.escape(item['summary']) + '</p>'
        for heading, paragraph in item['sections']:
            body += '<h2>' + html.escape(heading) + '</h2><p>' + prose(paragraph) + '</p>'
        body += ('<h2>Implementation</h2><pre><code class="language-python">' +
                 html.escape(item['code']) + '</code></pre>' +
                 '<h2>Performance and operating cost</h2><p>' + html.escape(item['cost']) +
                 '</p><h3>Common Mistakes</h3><ul>' +
                 ''.join('<li>' + html.escape(mistake) + '</li>' for mistake in item['mistakes']) +
                 '</ul><h2>Read next</h2>' + link_list(item['related']))
        path = item['path']
        row = dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://aitrove.in/' + path)),
                   type='article', path=path, title=item['title'], summary=item['summary'], body=body,
                   category='AI & Data', subject='data-engineering-project' if item['project'] else 'data-engineering',
                   difficulty='Advanced', tags=['ai-data', 'data-engineering'], potd_date=None,
                   featured=False, sort_order=7900 + index, status='published',
                   published_at=now, created_at=now, updated_at=now,
                   data={'subject_root': HUB, 'section_path': PROJECT_HUB if item['project'] else HUB,
                         'content_format': 'html', 'seo_ready': True,
                         'kind': 'project' if item['project'] else 'tutorial',
                         'reading_minutes': max(5, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                         'author_path': 'authors/aitrove-editorial',
                         'verification_suite': 'Editorial, code and internal-link checks',
                         'related': [{'path': target, 'title': titles[target]} for target in item['related']]})
        rows.append(row)
        by_path[path] = row

    hub, project_hub = by_path[HUB], by_path[PROJECT_HUB]
    for module_title in (MIGRATION, REFRESH):
        lessons = [item['path'] for item in LESSONS if item['module'] == module_title and not item['project']]
        projects = [item['path'] for item in LESSONS if item['module'] == module_title and item['project']]
        assert len(lessons) == 2 and len(projects) == 1
        if not any(module['title'] == module_title for module in hub['data']['modules']):
            hub['data']['modules'].insert(-1, {'title': module_title,
                                               'summary': 'Check the failure boundary, then complete the release exercise.',
                                               'lessons': lessons})
        practice = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
        if projects[0] not in practice['lessons']:
            practice['lessons'].append(projects[0])
        if '<h2>' + module_title + '</h2>' not in hub['body']:
            hub['body'] += '<h2>' + module_title + '</h2>' + link_list(lessons)
            hub['body'] += '<h2>' + ('Schema cutover project' if module_title == MIGRATION else 'View refresh project') + '</h2>' + link_list(projects)
        if projects[0] not in project_hub['data']['modules'][0]['lessons']:
            project_hub['data']['modules'][0]['lessons'].append(projects[0])
        if projects[0] not in project_hub['body']:
            project_hub['body'] += '<h2>' + module_title + '</h2>' + link_list(projects)
    hub['updated_at'] = project_hub['updated_at'] = now

    crosslinks = [('data-engineering/schema-compatibility-and-consumer-rollout', 'data-engineering/expand-contract-schema-migration'),
        ('data-engineering/schema-registry-transitive-compatibility', 'data-engineering/expand-contract-schema-migration'),
        ('data-engineering/backfill-publication-boundary', 'data-engineering/migration-reconciliation-and-cutover'),
        ('data-engineering/quality-quarantine-and-reconciliation', 'data-engineering/migration-reconciliation-and-cutover'),
        ('data-engineering/order-event-migration-project', 'data-engineering/payment-schema-cutover-project'),
        ('data-engineering/replay-manifest-and-audit-trail', 'data-engineering/payment-schema-cutover-project'),
        ('data-engineering/fact-grain-and-measure-additivity', 'data-engineering/materialized-view-refresh-strategies'),
        ('data-engineering/watermark-retention-and-late-corrections', 'data-engineering/materialized-view-refresh-strategies'),
        ('data-engineering/pipeline-slos-and-error-budgets', 'data-engineering/refresh-lag-and-cost-budget'),
        ('data-engineering/pipeline-cost-attribution-and-right-sizing', 'data-engineering/refresh-lag-and-cost-budget'),
        ('data-engineering/serving-index-and-freshness-contract', 'data-engineering/store-day-view-refresh-project'),
        ('data-engineering/revenue-mart-release-project', 'data-engineering/store-day-view-refresh-project')]
    for source, target in crosslinks:
        assert source in by_path and target in by_path, (source, target)
        changed.add(source)
        row = by_path[source]
        anchor = ('<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' +
                  html.escape(titles[target]) + '</a>.</p>')
        if anchor not in row['body']:
            row['body'] += anchor
            row['data'].setdefault('related', []).append({'path': target, 'title': titles[target]})
            row['updated_at'] = now
    assert len({row['path'] for row in rows}) == len(rows)
    FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
    import_path = ROOT / 'work/aitrove-data-engineering-migration-refresh-import-20261006.json'
    import_path.write_text(json.dumps([by_path[path] for path in sorted(changed)], ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'new_articles': len(LESSONS), 'new_projects': 2,
                      'crosslinks': len(crosslinks), 'import_rows': len(changed),
                      'import_path': str(import_path)}))


if __name__ == '__main__':
    publish()
