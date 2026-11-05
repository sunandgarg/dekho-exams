"""Add original Data Engineering lessons on quality drift and query admission."""
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
QUALITY = 'Statistical quality and correction windows'
ADMISSION = 'Query admission and tenant isolation'
context = runpy.run_path(str(ROOT / 'work/add-data-engineering-lineage-residency-20261006.py'))
LESSONS = context['LESSONS']
LESSONS.clear()
add = context['add']


add('cohort-baselines-and-denominator-drift', 'Cohort baselines and denominator drift',
    'A cohort baseline compares a metric with a relevant historical population, while denominator checks distinguish true behavioral change from missing input.', [
    ('Define the observation unit', 'A payment-success rate needs successful payment attempts divided by eligible attempts. Comparing raw success counts across days can mistake a source outage for a business decline. Name the denominator, exclusion rules, grain and event-time window before setting a threshold. [[data-engineering/fact-grain-and-measure-additivity|Fact grain]] matters because retry events should not automatically count as new eligible attempts. Keep numerator and denominator in the published quality record.'),
    ('Compare like with like', 'A Saturday overnight batch should not be judged against a weekday afternoon baseline. Segment by processing calendar, region, channel or another known demand driver, but require a minimum cohort size before trusting a narrow split. Too many tiny cohorts make the alert unstable and expensive. Record which reference windows were selected and which were excluded because of incidents or backfills.'),
    ('Guard the input before the statistic', 'A percentage can remain plausible when both numerator and denominator lose the same shard. Check source completeness, unique-key count and expected partition coverage first. If a region delivered zero rows, mark the rate unavailable instead of reporting a reassuring zero-percent change. [[data-engineering/quality-quarantine-and-reconciliation|Reconciliation]] validates the input boundary separately from drift.'),
    ('Use a bounded comparison', 'A median and median absolute deviation can resist one unusually large historic day, though a near-zero deviation needs a floor to avoid division by zero. Alert only when the absolute shift and relative shift matter to the consumer. Show actual value, baseline, threshold, cohort size and source generations together. A fixed global threshold can hide a serious change in a quiet region.'),
    ('Retire stale baselines deliberately', 'A new payment channel or scheduled price change may shift the normal distribution. Do not silently train the incident into the baseline. Approve the new regime after source checks and business review, then version the reference window. Test the gate with a missing shard, a legitimate scheduled promotion and a real conversion drop; they should produce different outcomes.')],
    '''from statistics import median

historic_rates = [0.71, 0.73, 0.72, 0.74, 0.72, 0.73, 0.71]
eligible_attempts = 470
successful_attempts = 277

def rate_guard(successes, eligible, history):
    if eligible < 300:
        return "insufficient-input"
    observed = successes / eligible
    baseline = median(history)
    deviation = median(abs(rate - baseline) for rate in history)
    return "drift" if abs(observed - baseline) > max(0.07, 4 * deviation) else "pass"

assert rate_guard(successful_attempts, eligible_attempts, historic_rates) == "drift"
assert rate_guard(0, 0, historic_rates) == "insufficient-input"''',
    'Sorting for a median costs O(H log H) time and O(H) space for H historical rates in this reference implementation. A production monitor can maintain compact summaries, but should preserve enough raw counts to audit a disputed alert. Every additional cohort multiplies retained state and test volume; choose segments that correspond to real consumer or source boundaries.',
    ['Do not compare raw counts when the eligible population changed.', 'Do not report a normal rate from incomplete source partitions.', 'Do not auto-refresh a baseline with an unresolved incident.'],
    ['data-engineering/fact-grain-and-measure-additivity', 'data-engineering/quality-quarantine-and-reconciliation', 'data-engineering/correction-aware-quality-alerts', 'data-engineering/payment-quality-release-project', 'data-engineering/pipeline-slos-and-error-budgets'], QUALITY)

add('correction-aware-quality-alerts', 'Correction-aware quality alerts',
    'A correction-aware alert evaluates a published interval and its revision history without counting the same late change as a fresh incident on every replay.', [
    ('Anchor the interval and version', 'An account-day total may be published at noon and corrected after a late settlement arrives. Store event-time interval, source cutoff, table generation, correction generation and quality result. An alert key based only on calendar day conflates distinct evidence; a key based only on run ID creates a new incident for every retry. [[data-engineering/watermark-retention-and-late-corrections|Late-arrival policy]] defines how long an interval may legitimately change.'),
    ('Separate provisional from final checks', 'A window still accepting late events can have an expected shortfall. Apply a provisional threshold before closure and a stricter final reconciliation after the correction horizon. The status should say provisional, final or reopened. A consumer reading a provisional number needs that state attached to the release, especially when the serving index lags the warehouse.'),
    ('Deduplicate alerts by cause', 'If the first failed run, its automatic retry and a manual replay all see the same missing source shard, create one incident with attempt evidence attached. A later independent loss after the source recovers can open another incident. Use the dataset, interval and failure signature as a stable key; close the incident only when a committed generation passes the check. [[data-engineering/run-scoped-lineage-and-release-evidence|Run evidence]] identifies which attempts were published.'),
    ('Prevent false recovery', 'A late correction can improve a metric while still leaving the row count below the source control. Require all release gates to pass before resolving the incident. Check totals, unique keys, source positions and the consumer-visible index generation. A green task and a quiet alert channel do not prove the old dashboard answer was replaced.'),
    ('Exercise replay and reopen', 'Publish an interval with 47 missing transactions, retry it twice, then apply a 31-transaction correction. The incident should remain open because 16 are still absent. Apply the final 16 and publish one corrected generation; now resolve it. Replaying the identical correction must not reopen or double-count. If a later source gap appears, its new failure signature should create a separate case.')],
    '''control_count = 470
published = {"generation": 71, "count": 423}
corrections = [(72, 31), (73, 16), (73, 16)]

def apply_unique_corrections(base, changes):
    count = base["count"]
    seen = set()
    for generation, increment in changes:
        if generation in seen:
            continue
        seen.add(generation)
        count += increment
    return count

assert apply_unique_corrections(published, corrections[:1]) == 454
assert apply_unique_corrections(published, corrections) == control_count''',
    'The replay scan is O(C) expected time and O(C) deduplication state for C correction records. Production systems can use a stable correction ID and bounded retention, but that horizon must cover supported replays. Incident state adds one record per active dataset-interval-signature combination; excessive partition-level keys can overwhelm operators and should be rolled up by a meaningful failure boundary.',
    ['Do not create one alert per retry of the same source failure.', 'Do not close an incident when only one of several release checks recovered.', 'Do not apply a duplicate late correction twice.'],
    ['data-engineering/watermark-retention-and-late-corrections', 'data-engineering/run-scoped-lineage-and-release-evidence', 'data-engineering/cohort-baselines-and-denominator-drift', 'data-engineering/payment-quality-release-project', 'data-engineering/quality-quarantine-and-reconciliation'], QUALITY)

add('payment-quality-release-project', 'Project: gate a payment mart on quality evidence',
    'Publish a payment mart only when cohort drift, source completeness and late-correction evidence agree with the release contract.', [
    ('Freeze the source controls', 'Create one payment-day interval with 470 eligible attempts and a control count for each region. Keep the source snapshot and schema ID in the manifest. The candidate mart initially contains 423 records because one shard was delayed. A global success rate may still look plausible; [[data-engineering/cohort-baselines-and-denominator-drift|cohort baselines]] and input coverage must be checked separately.'),
    ('Build a provisional candidate', 'Calculate per-region success rates from deduplicated payment attempts, label the interval provisional and keep it off the final reader pointer. Record numerator, denominator, cohort size and reference window. A cohort below its minimum sample size yields insufficient evidence, not pass. Allow a dated last-good mart to serve while the candidate is quarantined.'),
    ('Replay corrections once', 'Deliver 31 delayed records, retry the same correction message, then deliver 16 more. Use correction IDs or source positions so the retry has no effect. [[data-engineering/correction-aware-quality-alerts|The incident]] remains open after the first correction and closes only after the source count reaches 470 and regional totals reconcile. Keep all candidate attempts in the run manifest.'),
    ('Commit and check the consumer', 'Publish a new table snapshot and its serving index as one release generation. Query payment success rate and count through the consumer route; verify both refer to that generation. Run a rollback simulation that restores the previous pointer without deleting evidence. A correction that passes warehouse checks but never reaches the index is not a successful release.'),
    ('Submit the evidence package', 'Include source controls, candidate and final row counts, cohort baseline version, two correction IDs, duplicate replay result, incident timeline, committed snapshot and query output. Add a deliberately missing shard test and a legitimate high-volume promotion test. They should not be confused merely because each changes the raw transaction count.')],
    '''source_control = {"north": 230, "south": 240}
candidate = {"north": 230, "south": 193}
correction_batches = [("batch-72", "south", 31), ("batch-73", "south", 16),
                      ("batch-72", "south", 31)]

def reconcile(rows, changes, expected):
    result, seen = dict(rows), set()
    for correction_id, region, count in changes:
        if correction_id not in seen:
            result[region] += count
            seen.add(correction_id)
    return result == expected

assert not reconcile(candidate, correction_batches[:1], source_control)
assert reconcile(candidate, correction_batches, source_control)''',
    'Reconciliation is O(R + C) expected time for R regions and C correction messages, with O(R + C) state. The project also retains candidate snapshots and a last-good serving generation; these add storage but make rejected releases inspectable. A full regional baseline scan costs more than one global aggregate, so schedule it at the release boundary rather than on every query.',
    ['Do not pass a cohort check when its source denominator is incomplete.', 'Do not treat a duplicate correction as new revenue.', 'Do not publish a corrected table while the serving index still points at stale data.'],
    ['data-engineering/cohort-baselines-and-denominator-drift', 'data-engineering/correction-aware-quality-alerts', 'data-engineering/quality-quarantine-and-reconciliation', 'data-engineering/serving-index-and-freshness-contract', 'data-engineering/replay-manifest-and-audit-trail'], QUALITY, True)

add('query-admission-queues-and-deadlines', 'Query admission queues and deadlines',
    'Query admission decides whether a request runs, waits or fails before it consumes scarce memory and worker capacity.', [
    ('Put a bound on waiting', 'A BI dashboard may issue dozens of interactive queries while a batch analyst starts a broad scan. If all run immediately, memory pressure can slow or fail everyone. Give each workload a concurrency limit and a queue limit. When the queue is full, reject with a clear retry response rather than accumulating unbounded requests. [[data-engineering/serving-index-and-freshness-contract|A serving index]] helps only the queries it was built for; admission still protects shared compute.'),
    ('Treat deadline as an end-to-end budget', 'A 12-second query target includes queue wait, execution and result delivery. A query that waited 11 seconds should not start a 30-second scan merely because a worker became free. Record enqueue time and absolute deadline; expire stale work before starting. This prevents old dashboard refreshes from crowding out the user’s latest request.'),
    ('Reserve capacity for critical reads', 'Separate interactive serving, scheduled extracts and exploratory scans into workload groups. A reserved slice protects critical reads during a batch burst, while controlled borrowing can use idle capacity when policy allows. Avoid a single high-priority queue that permanently starves maintenance work. Define minimum progress or maximum wait for every accepted class.'),
    ('Account for cost before admission', 'Estimate scanned bytes, memory and partition breadth using the query plan or a coarse request class. An estimate is imperfect, so combine it with runtime caps and cancellation. Reject a query that exceeds a tenant or class budget even when the cluster is idle; otherwise one expensive request can consume the next interval’s allowance. [[data-engineering/pipeline-cost-attribution-and-right-sizing|Cost attribution]] closes the loop after execution.'),
    ('Test a burst and recovery', 'Queue five interactive requests behind two running slots, add one batch scan and then cancel the oldest interactive request. Verify that no more than two run, the expired request never starts, and an admitted batch request eventually progresses. Report queue time and execution time separately. A low execution p95 can hide users waiting in admission.')],
    '''from collections import deque

queue = deque([{"id": "q-47", "deadline": 52},
               {"id": "q-48", "deadline": 61},
               {"id": "q-49", "deadline": 58}])

def admit_ready(waiting, now, free_slots):
    started = []
    while waiting and len(started) < free_slots:
        request = waiting.popleft()
        if request["deadline"] > now:
            started.append(request["id"])
    return started

assert admit_ready(queue, 55, 2) == ["q-48", "q-49"]''',
    'Admission is O(Q) time in the worst case when Q expired entries must be removed and O(Q) memory for a bounded queue. Executing a query can be much more expensive than this control path. A strict queue limit protects coordinator memory; deadlines prevent stale work from occupying future capacity. Measure rejection, wait and runtime by workload class.',
    ['Do not measure only execution time while ignoring queue delay.', 'Do not start a request whose end-to-end deadline has already passed.', 'Do not allow an unbounded queue to masquerade as capacity.'],
    ['data-engineering/serving-index-and-freshness-contract', 'data-engineering/tenant-query-budgets-and-fairness', 'data-engineering/analytics-burst-isolation-project', 'data-engineering/pipeline-cost-attribution-and-right-sizing', 'data-engineering/pipeline-slos-and-error-budgets'], ADMISSION)

add('tenant-query-budgets-and-fairness', 'Tenant query budgets and fairness',
    'A tenant query budget limits one tenant’s concurrent work and cumulative resource use so a shared analytics service can preserve latency for others.', [
    ('Identify the tenant at the trusted edge', 'The tenant key must come from authenticated request context, not a user-editable SQL comment. Enforce row access separately from compute limits: a fair scheduler does not stop a query from reading another tenant’s rows. [[data-engineering/row-policy-and-column-mask-tests|Row policy tests]] must still run under every service identity and job type.'),
    ('Cap active and queued work', 'Give each tenant a maximum running count, waiting count and query deadline. A single large tenant should not fill the global queue while smaller tenants wait. Use per-tenant queues or weighted scheduling with an explicit minimum share. A tenant at its cap can wait within its own bound, but should not consume another tenant’s reserved slot.'),
    ('Track usage over a window', 'Concurrency alone does not stop a tenant from submitting one expensive scan after another. Record bytes scanned, CPU time or charged work units against a rolling budget. Decide whether unused allowance carries over; an unlimited rollover creates a future burst. Include retries and cancelled work according to a written billing and abuse policy. [[data-engineering/query-admission-queues-and-deadlines|Admission]] should check the budget before work begins.'),
    ('Avoid false precision in estimates', 'A query planner can underestimate skew, cache misses and join expansion. Treat estimates as admission hints and enforce runtime limits. When the actual cost exceeds the estimate, charge the measured usage and stop or throttle according to contract. Keep the reason visible to the user; an opaque timeout makes it impossible to distinguish fairness from a broken query.'),
    ('Validate isolation with contention', 'Start two expensive scans for tenant North, one dashboard read for tenant South and a maintenance job. The South read should meet its queue target even when North reaches its cap. Verify global memory stays bounded and that maintenance eventually runs. Observe both per-tenant and total utilization; a reservation that stays idle during a heavy burst may waste capacity unless safe borrowing is defined.')],
    '''limits = {"north": 2, "south": 1}
running = {"north": 2, "south": 0}
remaining_units = {"north": 16, "south": 47}

def may_start(tenant, estimated_units):
    return (tenant in limits and running[tenant] < limits[tenant]
            and estimated_units <= remaining_units[tenant])

assert not may_start("north", 8)
assert may_start("south", 8)
assert not may_start("south", 52)''',
    'The reference checks use O(1) expected map lookups and O(T) stored policy state for T tenants. A scheduler needs bounded queues and accounting for active requests; its runtime cost is usually small beside query execution. Reserved capacity raises predictable cost, while controlled borrowing improves utilization. Keep authorization enforcement separate from this resource policy.',
    ['Do not accept a tenant identifier supplied only in query text.', 'Do not mistake compute fairness for row-level access control.', 'Do not rely solely on estimated cost without runtime limits.'],
    ['data-engineering/query-admission-queues-and-deadlines', 'data-engineering/row-policy-and-column-mask-tests', 'data-engineering/analytics-burst-isolation-project', 'data-engineering/pipeline-cost-attribution-and-right-sizing', 'data-engineering/serving-index-and-freshness-contract'], ADMISSION)

add('analytics-burst-isolation-project', 'Project: protect analytics reads during a tenant burst',
    'Design and test an admission policy that protects customer dashboards while allowing bounded batch progress during a shared-cluster burst.', [
    ('Record the workload contract', 'Two tenants share an analytics cluster. North runs long exploratory scans; South has a dashboard with a 14-second end-to-end target. A maintenance extract must complete within 36 minutes. Set per-class concurrency, queue size, deadline and measured usage budget. [[data-engineering/query-admission-queues-and-deadlines|Admission rules]] apply before query execution, while row policies protect data access.'),
    ('Simulate the burst', 'Start two North scans, enqueue a third, then submit two South dashboard queries and one maintenance extract. Reject the North request that exceeds its waiting bound. Expire a queued dashboard refresh whose deadline passes, then admit its newer replacement. Record enqueue, start and finish time for each accepted request. A dashboard that runs quickly after a long wait still misses its target.'),
    ('Enforce tenant boundaries', 'Derive tenant identity from authenticated context, execute row-policy tests under both tenant identities and confirm North cannot read South’s account rows. Apply cost limits to measured work units as well as estimated units. [[data-engineering/tenant-query-budgets-and-fairness|Tenant fairness]] must not accidentally allow a query to borrow authorization along with idle compute.'),
    ('Publish only a consistent result', 'Run dashboard queries against a named serving-index generation and disclose its source cutoff. A backlog can make a fast query stale; compare the answer’s freshness with the product contract. If the index rebuild and interactive queries share workers, reserve enough capacity for both or provide a dated last-good response. [[data-engineering/serving-index-and-freshness-contract|Freshness evidence]] belongs in the result.'),
    ('Review the failure transcript', 'Deliver admitted, queued, expired and rejected request lists; queue and runtime percentiles; per-tenant work units; policy and row-access test results; and maintenance completion time. Inject one estimate that is too low and verify a runtime cap still stops it. The policy passes only when South’s latency target and the maintenance deadline both hold under the burst.')],
    '''requests = [
    {"id": "north-71", "tenant": "north", "units": 31},
    {"id": "north-72", "tenant": "north", "units": 29},
    {"id": "south-73", "tenant": "south", "units": 5},
]
running_cap = {"north": 2, "south": 1}

def schedule_by_tenant(items, caps):
    active, accepted = {}, []
    for request in items:
        tenant = request["tenant"]
        if active.get(tenant, 0) < caps[tenant]:
            accepted.append(request["id"])
            active[tenant] = active.get(tenant, 0) + 1
    return accepted

assert schedule_by_tenant(requests, running_cap) == ["north-71", "north-72", "south-73"]''',
    'The reference pass is O(Q) time for Q requests and O(T) counter state for T tenants. A full scheduler also maintains bounded waiting queues and per-window usage ledgers. Capacity reserved for dashboards and maintenance adds cost, but an uncontrolled burst can exceed the user-facing deadline even when the average cluster utilization appears reasonable.',
    ['Do not let a long scan fill every shared worker.', 'Do not report latency without queue time and freshness.', 'Do not treat tenant resource limits as a replacement for data-access policy.'],
    ['data-engineering/query-admission-queues-and-deadlines', 'data-engineering/tenant-query-budgets-and-fairness', 'data-engineering/row-policy-and-column-mask-tests', 'data-engineering/serving-index-and-freshness-contract', 'data-engineering/pipeline-slos-and-error-budgets'], ADMISSION, True)


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
    for module_title in (QUALITY, ADMISSION):
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
            hub['body'] += '<h2>' + ('Quality release project' if module_title == QUALITY else 'Burst isolation project') + '</h2>' + link_list(projects)
        if projects[0] not in project_hub['data']['modules'][0]['lessons']:
            project_hub['data']['modules'][0]['lessons'].append(projects[0])
        if projects[0] not in project_hub['body']:
            project_hub['body'] += '<h2>' + module_title + '</h2>' + link_list(projects)
    hub['updated_at'] = project_hub['updated_at'] = now

    crosslinks = [
        ('data-engineering/quality-quarantine-and-reconciliation', 'data-engineering/cohort-baselines-and-denominator-drift'),
        ('data-engineering/fact-grain-and-measure-additivity', 'data-engineering/cohort-baselines-and-denominator-drift'),
        ('data-engineering/watermark-retention-and-late-corrections', 'data-engineering/correction-aware-quality-alerts'),
        ('data-engineering/run-scoped-lineage-and-release-evidence', 'data-engineering/correction-aware-quality-alerts'),
        ('data-engineering/revenue-mart-release-project', 'data-engineering/payment-quality-release-project'),
        ('data-engineering/pipeline-slos-and-error-budgets', 'data-engineering/payment-quality-release-project'),
        ('data-engineering/serving-index-and-freshness-contract', 'data-engineering/query-admission-queues-and-deadlines'),
        ('data-engineering/pipeline-cost-attribution-and-right-sizing', 'data-engineering/query-admission-queues-and-deadlines'),
        ('data-engineering/row-policy-and-column-mask-tests', 'data-engineering/tenant-query-budgets-and-fairness'),
        ('data-engineering/data-classification-and-access-boundaries', 'data-engineering/tenant-query-budgets-and-fairness'),
        ('data-engineering/regional-analytics-recovery-project', 'data-engineering/analytics-burst-isolation-project'),
        ('data-engineering/governed-customer-mart-project', 'data-engineering/analytics-burst-isolation-project'),
    ]
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
    import_path = ROOT / 'work/aitrove-data-engineering-quality-admission-import-20261006.json'
    import_path.write_text(json.dumps([by_path[path] for path in sorted(changed)], ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'new_articles': len(LESSONS), 'new_projects': 2,
                      'crosslinks': len(crosslinks), 'import_rows': len(changed),
                      'import_path': str(import_path)}))


if __name__ == '__main__':
    publish()
