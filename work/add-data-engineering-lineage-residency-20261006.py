"""Add six original Data Engineering pages on runtime evidence and replica controls."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'src/data/fixtures.json'
HUB = 'data-engineering/data-engineering-tutorial'
PROJECT_HUB = HUB + '/project'
LINEAGE = 'Runtime lineage and incident evidence'
RESIDENCY = 'Residency and replica erasure'
LESSONS = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    assert len(sections) == 5
    LESSONS.append(dict(path='data-engineering/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add('run-scoped-lineage-and-release-evidence', 'Run-scoped lineage and release evidence',
    'Run-scoped lineage records the exact input and output generations used by one execution, rather than only a planned table dependency.', [
    ('Distinguish design from execution', 'A planned DAG says that the revenue job reads orders and rates. It cannot prove which order snapshot or rate revision produced a specific published total. Record a run ID, code release, named input generations, output generation and final status for every publish attempt. [[data-engineering/pipeline-lineage-and-impact-analysis|Static lineage]] still helps estimate impact, but runtime evidence answers what actually happened.'),
    ('Capture the committed boundary', 'An attempt may read data, write candidate files and then fail. Its lineage is useful for debugging, yet it must not be labelled as the lineage of a published dataset. Attach the output generation only after the atomic commit succeeds. Keep failed attempts under their own run IDs. A consumer should be able to follow the current table pointer to one successful run and then to its exact inputs.'),
    ('Avoid false many-to-many edges', 'A job that reads customer and invoice tables may write separate customer and invoice summaries. Treating every input as the parent of every output invents dependencies. Capture edges at the output or transform level, including filtered partitions when practical. If the implementation cannot prove a column-level edge, label it as unknown rather than presenting an inferred edge as certain.'),
    ('Preserve identity across retries', 'A retry of the same interval is a new attempt under a stable logical run key. Pin source generations or record that inputs changed before retry; otherwise two attempts with the same scheduled time can calculate different answers. [[data-engineering/replay-manifest-and-audit-trail|The replay manifest]] should retain both attempts and name the winning publication. This also makes a rollback reviewable.'),
    ('Query backward from an answer', 'Given a suspicious dashboard total, start with its serving generation, find the table snapshot and successful run, then inspect input versions and source positions. Test the chain with a deliberately failed attempt between two successful releases: the failed candidate must appear in diagnostics but never in the published answer. Keep access controls on lineage metadata because identifiers and partition values can reveal sensitive activity.')],
    '''runs = [
    {"id": "run-71", "status": "failed", "inputs": ("orders-47", "rates-8"), "output": None},
    {"id": "run-72", "status": "committed", "inputs": ("orders-48", "rates-8"), "output": "revenue-49"},
]

def published_parents(releases, output_generation):
    matches = [run for run in releases if run["output"] == output_generation
               and run["status"] == "committed"]
    if len(matches) != 1:
        raise ValueError("output has no unique committed run")
    return matches[0]["inputs"]

assert published_parents(runs, "revenue-49") == ("orders-48", "rates-8")''',
    'The direct lookup above scans R runs in O(R) time and stores O(R) records. Indexing committed output generation reduces expected lookup to O(1), while recording partition or column edges increases metadata volume. Retain evidence at least as long as the snapshots and audit period it must explain; sampling away successful release events destroys the proof chain.',
    ['Do not label a failed candidate as the parent of a published snapshot.', 'Do not infer all-to-all edges from a multi-input, multi-output job.', 'Do not identify a run solely by its scheduled timestamp.'],
    ['data-engineering/pipeline-lineage-and-impact-analysis', 'data-engineering/replay-manifest-and-audit-trail', 'data-engineering/telemetry-correlation-and-cardinality-budget', 'data-engineering/revenue-incident-evidence-project', 'data-engineering/lakehouse-snapshot-and-atomic-commit'], LINEAGE)

add('telemetry-correlation-and-cardinality-budget', 'Telemetry correlation and cardinality budgets',
    'A pipeline correlation key joins bounded logs, metrics and traces to the release being diagnosed without making every event identifier a metric label.', [
    ('Give the release a stable context', 'Carry a logical interval, attempt ID and output generation through extraction, transformation, publication and serving. The identifiers let an operator jump from a freshness alert to the failed span and then to the run manifest. For an asynchronous queue, record the parent context or a link to the producing operation; clock-adjacent log lines are not enough to establish causality. [[data-engineering/run-scoped-lineage-and-release-evidence|Run lineage]] supplies data versions that request traces alone do not.'),
    ('Keep metric labels bounded', 'A counter by pipeline and failure class has a useful, finite set of series. Adding order ID, file path or run ID as a metric label can create a new time series for every record and exhaust storage. Put high-cardinality identifiers in sampled traces or access-controlled logs, then retain aggregate metrics for alerting. Estimate the product of label cardinalities before adding a dimension.'),
    ('Measure the consumer boundary', 'A green task metric only says a worker finished. Record the last accepted source interval, committed table generation, indexed serving generation and p95 consumer query latency. An index may lag a successful table release. [[data-engineering/serving-index-and-freshness-contract|The freshness contract]] must read from the generation the consumer sees, not from the latest successful extraction log.'),
    ('Control sensitive context', 'Tracing baggage and log attributes can travel through services and exporters. Do not put customer names, raw payloads or secret tokens in correlation context. Use opaque IDs, restrict access to lookup tables and set retention by classification. Redaction after export does not undo exposure to an earlier collector. Test representative error paths because exceptions often log entire records.'),
    ('Budget signal loss explicitly', 'A sampled trace is diagnostic evidence, not a complete audit record. Keep every committed release manifest and a small set of hard counters even if trace sampling drops routine spans. During an incident, temporarily raise tracing for a named pipeline without turning on global full capture. Validate that a failed publish emits a failure class, a bounded counter increment and no new serving generation.')],
    '''label_values = {"pipeline": 7, "stage": 6, "failure_class": 5}

def estimated_series(cardinalities):
    total = 1
    for count in cardinalities.values():
        total *= count
    return total

assert estimated_series(label_values) == 210
with_record_id = {**label_values, "record_id": 470000}
assert estimated_series(with_record_id) == 98700000''',
    'Estimating series is O(L) time and O(1) auxiliary space for L label dimensions. Actual cardinality depends on observed combinations, but the upper-bound product catches expensive labels early. Trace storage grows with sampled operations and attribute bytes; metric storage grows with distinct series over retention windows. Keep audit manifests separately from sampled telemetry.',
    ['Do not place event IDs or file paths in metric labels.', 'Do not assume a trace sample is a complete publication audit.', 'Do not propagate sensitive payloads through trace context.'],
    ['data-engineering/run-scoped-lineage-and-release-evidence', 'data-engineering/pipeline-slos-and-error-budgets', 'data-engineering/serving-index-and-freshness-contract', 'data-engineering/revenue-incident-evidence-project', 'data-engineering/failure-classification-and-retry-budget'], LINEAGE)

add('revenue-incident-evidence-project', 'Project: trace a missing revenue slice to one release',
    'Investigate a missing regional revenue slice using committed generations, input versions and bounded telemetry, then publish a corrected answer.', [
    ('Create a controlled discrepancy', 'Build an account-day revenue mart from order generation 48 and rate revision 8. Publish generation 49, then introduce a failed generation-50 attempt that omitted one region because a filter used the wrong field. The serving index must keep pointing to generation 49 while the failed candidate remains inspectable. The incident begins with a consumer query returning 7,300 cents where the approved control expects 9,100.'),
    ('Follow the answer backward', 'Record the query generation, index pointer, table snapshot, successful run ID and its exact inputs. Compare the failed candidate separately; do not mistake the most recent attempt for the published answer. [[data-engineering/run-scoped-lineage-and-release-evidence|Run-scoped lineage]] should show whether the missing slice originated in source input, transform logic or index publication.'),
    ('Use signals without exploding labels', 'Alert on consumer-visible freshness and a regional reconciliation failure using bounded labels such as pipeline, stage and failure class. Put run-50 in the trace and restricted log, not a metric dimension. [[data-engineering/telemetry-correlation-and-cardinality-budget|The cardinality budget]] should remain unchanged as the number of orders rises. Verify no raw customer identifier enters diagnostic attributes.'),
    ('Repair from pinned inputs', 'Correct the transform, pin the accepted order and rate generations, and rerun the affected interval. Compare totals, unique account-day keys and the region distribution before publishing generation 51. Switch the table and index pointers only after both are validated. A partial index load must not become visible. Keep the failed attempt and correction reason in the manifest.'),
    ('Hand over an evidence chain', 'Deliver the original query, observed mismatch, alert timestamp, trace link key, published lineage, failed attempt, corrected checksums and first good query. Reproduce the investigation from the artifacts alone. Record detection and repair durations separately; a green worker dashboard after rerun is weaker evidence than the corrected consumer answer.')],
    '''attempts = [
    {"run": "run-49", "status": "committed", "generation": 49, "regional_cents": 7300},
    {"run": "run-50", "status": "failed", "generation": 50, "regional_cents": 0},
    {"run": "run-51", "status": "committed", "generation": 51, "regional_cents": 9100},
]

def visible_total(records, published_generation):
    releases = [item for item in records if item["generation"] == published_generation
                and item["status"] == "committed"]
    if len(releases) != 1:
        raise ValueError("invalid published generation")
    return releases[0]["regional_cents"]

assert visible_total(attempts, 49) == 7300
assert visible_total(attempts, 51) == 9100''',
    'The reference scan is O(R) time for R attempts and O(R) retained evidence; a generation index makes lookups O(1) expected. The exercise also pays for pinned input snapshots and one extra candidate output. That is deliberate: discarding failure evidence to save metadata makes the exact cause harder to prove.',
    ['Do not display an uncommitted candidate as the current answer.', 'Do not repair from moving inputs without recording the new versions.', 'Do not equate a successful rerun with a validated consumer query.'],
    ['data-engineering/run-scoped-lineage-and-release-evidence', 'data-engineering/telemetry-correlation-and-cardinality-budget', 'data-engineering/pipeline-lineage-and-impact-analysis', 'data-engineering/replay-manifest-and-audit-trail', 'data-engineering/serving-index-and-freshness-contract'], LINEAGE, True)

add('regional-data-boundary-and-egress-gates', 'Regional data boundaries and egress gates',
    'A regional data boundary defines where classified inputs, derived outputs, processing jobs and diagnostic copies may exist; an egress gate checks each movement against that policy.', [
    ('Inventory more than the main table', 'A warehouse table may stay in an approved region while query results, temporary spill files, error queues, traces, backups or a disaster-recovery replica cross the boundary. List every storage and processing location in the data product manifest. Attach classification and allowed region set to the dataset, then propagate the restriction to derived data unless an approved transformation changes its classification. [[data-engineering/data-classification-and-access-boundaries|Classification]] begins the decision; it does not enforce placement.'),
    ('Check movement before bytes move', 'Validate destination region, service purpose, encryption key boundary and recipient authorization before a copy job starts. A nightly transfer that fails a policy check should not create a partial object at the destination. Apply the gate to backfills and emergency failover as well as steady-state replication. [[data-engineering/data-pipeline-rpo-rto-and-replication-lag|Recovery targets]] cannot be met by silently violating a placement contract.'),
    ('Treat processing as a location', 'A dataset stored in one region can still be processed elsewhere by an export, managed query service or diagnostic tool. Keep the execution location in the release manifest and test the path a real operator uses. An encryption key in an approved region does not by itself prove that plaintext processing stayed there. Distinguish storage, transit, processing and support-access boundaries.'),
    ('Record exceptions with expiry', 'Some products allow de-identified aggregates to leave the source region. State the transformation, re-identification risk, owner approval, receiving region and exception expiry. Reject an exception whose scope is simply all customer data. When the job changes schema or joins a new identifier, rerun classification before reusing the exception.'),
    ('Exercise denied and allowed routes', 'Run a permitted intra-region materialization and a prohibited cross-region export in a test environment. The permitted path should publish one generation with location evidence; the prohibited path should write no destination artifact and emit a policy denial. Inspect backup and error paths too. A policy document without a failing deployment test is only an intention.')],
    '''datasets = {
    "customer_receipts": {"classification": "restricted", "allowed": {"region-west"}},
    "daily_counts": {"classification": "aggregate", "allowed": {"region-west", "region-east"}},
}

def permit_copy(catalog, dataset_name, destination):
    if dataset_name not in catalog:
        raise KeyError("unclassified dataset")
    return destination in catalog[dataset_name]["allowed"]

assert permit_copy(datasets, "daily_counts", "region-east")
assert not permit_copy(datasets, "customer_receipts", "region-east")''',
    'The catalog lookup and set membership are O(1) expected time and space per decision, with O(D + P) policy storage for D datasets and P allowed placements. Real gates also check service identities, keys and lineage before transfer; those calls add latency and must fail closed when policy state is unavailable. The cost of regional copies includes network egress, storage and duplicate retention.',
    ['Do not check only the primary table while ignoring logs, spill and backup copies.', 'Do not treat encryption key location as proof of processing location.', 'Do not let an emergency recovery path bypass the egress gate.'],
    ['data-engineering/data-classification-and-access-boundaries', 'data-engineering/data-pipeline-rpo-rto-and-replication-lag', 'data-engineering/replica-version-erasure-and-restore-guard', 'data-engineering/replica-erasure-proof-project', 'data-engineering/dataset-ownership-and-change-approval'], RESIDENCY)

add('replica-version-erasure-and-restore-guard', 'Replica version erasure and restore guards',
    'Replica erasure must account for every object version and restore path, because hiding a current key does not remove historical bytes or prevent an old backup from republishing them.', [
    ('Separate logical from physical deletion', 'A delete marker can make the current object unreadable while older versions still occupy storage. A replication rule may copy the marker, omit it, or leave version-specific deletion to the destination operator. Do not infer destination erasure from a successful source delete. Enumerate versions by object identity and region, including retained snapshots, index generations and dead-letter copies. [[data-engineering/deletion-propagation-and-erasure-proof|The deletion ledger]] should track each surface independently.'),
    ('Freeze resurrection paths', 'A backup restored after an erasure can bring back a pre-deletion customer row. Persist a durable deletion ledger outside the backup being restored, with entity key and monotonically ordered deletion position. Before any restored generation becomes queryable, replay the ledger through the restored data and serving index. A lagging replica must reject an older upsert after the deletion position.'),
    ('Respect retention holds explicitly', 'Immutable retention or a legal hold may prevent immediate physical removal. Record the hold owner, scope, expiry condition and access restrictions; do not mark the bytes erased while the hold remains. Once the hold is released, expire the applicable object versions and snapshots, then verify that the cleanup job completed. An audit claim must distinguish inaccessible, logically deleted and physically removed states.'),
    ('Prove completion at every destination', 'For each entity and copy, collect version listing, current-read test, snapshot reference check and cleanup result. A current-read 404 is insufficient if a version-specific read still succeeds. Include cross-account replicas, old disaster-recovery regions and staged backfills. Report partial failure as pending, retry with bounded backoff and prevent publication of a restored copy until checks pass.'),
    ('Test an adversarial restore', 'Delete customer 47 at source position 73, then restore a snapshot ending at 71. The replay gate must remove the customer before opening the restored table. Inject a delayed update at 72 and verify it cannot recreate the row. Check the current table, index and raw version inventory, then record separate evidence for each. [[data-engineering/regional-data-boundary-and-egress-gates|Placement policy]] still applies to the restore location.')],
    '''restored_rows = {"customer-47": {"position": 71, "cents": 2300}}
deletions = {"customer-47": 73}

def guard_restore(rows, deletion_positions):
    safe = dict(rows)
    for customer_id, delete_position in deletion_positions.items():
        if customer_id in safe and safe[customer_id]["position"] <= delete_position:
            safe.pop(customer_id)
    return safe

assert guard_restore(restored_rows, deletions) == {}
late_update = {"customer-47": {"position": 72, "cents": 2400}}
assert guard_restore(late_update, deletions) == {}''',
    'The reference guard is O(K) time for K deletion keys and O(N) copied row state. A production restore can avoid scanning every record by indexing deletion keys and affected partitions, but must still verify all replicas and historical versions. Version inventory, retention holds and cross-region cleanup make the full erasure cost proportional to the number of copies and retained generations, not just current rows.',
    ['Do not treat a delete marker as proof that all versions are gone.', 'Do not restore a backup before replaying later deletions.', 'Do not claim physical erasure while an immutable hold still retains bytes.'],
    ['data-engineering/deletion-propagation-and-erasure-proof', 'data-engineering/regional-data-boundary-and-egress-gates', 'data-engineering/event-envelope-identity-and-tombstones', 'data-engineering/replica-erasure-proof-project', 'data-engineering/compaction-retention-and-replay-horizon'], RESIDENCY)

add('replica-erasure-proof-project', 'Project: prove erasure after a regional restore',
    'Release a restored customer mart only after regional placement, tombstone replay, version inventory and consumer-read checks agree.', [
    ('Set the contract and inventory', 'A customer mart has a primary, one disaster-recovery replica, a serving index and a retained backup. Customer 47 is erased at source position 73, while the newest backup stops at 71. Classify each artifact, record its region and list which copies may legally exist. [[data-engineering/regional-data-boundary-and-egress-gates|The regional gate]] should deny an unauthorized destination before any restore files are written.'),
    ('Simulate an incomplete delete', 'Remove the current primary row but leave one older object version in the replica. A current-read test may pass while a version-specific read still retrieves data. The erasure workflow must report pending, not complete. Delete or expire the historical version when policy permits, then verify the version inventory again. If a hold blocks removal, record its authority and keep the result explicitly pending.'),
    ('Restore behind a publication gate', 'Restore the backup to an authorized region into candidate storage, replay the deletion ledger from position 72 onward and build the serving index from the corrected snapshot. Inject an update at 72 after the delete at 73; source ordering must reject it. [[data-engineering/replica-version-erasure-and-restore-guard|The restore guard]] must pass before the table pointer or index pointer changes.'),
    ('Check all reader surfaces', 'Run current and version-specific reads against both object stores, query the restored mart and serving index, inspect dead-letter copies and confirm no old snapshot pointer is publicly selectable. Compare deletion-ledger position, table generation and index generation in one manifest. A missing response from one region is not a pass; it is an unverified result that blocks completion.'),
    ('Deliver a defensible proof bundle', 'Provide the classification decision, copy inventory, denied egress attempt, deletion-ledger entry, candidate restore manifest, version listings, hold status, post-replay query output and publication timestamp. Include a rerun that shows the process is idempotent. Separate logical hiding, inaccessible retained bytes and verified physical removal in the final state report.')],
    '''copies = [
    {"region": "region-west", "version": "v-71", "customer": "customer-47", "present": False},
    {"region": "region-east", "version": "v-68", "customer": "customer-47", "present": True},
]

def erasure_complete(inventory, customer_id):
    return all(not item["present"] for item in inventory
               if item["customer"] == customer_id)

assert not erasure_complete(copies, "customer-47")
copies[1]["present"] = False
assert erasure_complete(copies, "customer-47")''',
    'The inventory check is O(V) time over V recorded versions and O(1) auxiliary space. A real proof costs version listings, regional reads, snapshot scans and restore validation; it must include every known copy and detect inventory gaps. Candidate storage and index rebuild add temporary cost, but publishing first would expose deleted data again.',
    ['Do not declare completion from one region or one current-read response.', 'Do not publish a restored table before applying the later deletion ledger.', 'Do not hide a pending legal hold inside a successful erasure status.'],
    ['data-engineering/regional-data-boundary-and-egress-gates', 'data-engineering/replica-version-erasure-and-restore-guard', 'data-engineering/deletion-propagation-and-erasure-proof', 'data-engineering/regional-analytics-recovery-project', 'data-engineering/replay-manifest-and-audit-trail'], RESIDENCY, True)


def publish():
    rows = json.loads(FIXTURE.read_text())
    new_paths = {item['path'] for item in LESSONS}
    assert len(new_paths) == len(LESSONS) == 6
    rows = [row for row in rows if row['path'] not in new_paths]
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

    changed = set(new_paths) | {HUB, PROJECT_HUB}
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
                   featured=False, sort_order=7890 + index, status='published',
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
    for module_title in (LINEAGE, RESIDENCY):
        lessons = [item['path'] for item in LESSONS if item['module'] == module_title and not item['project']]
        projects = [item['path'] for item in LESSONS if item['module'] == module_title and item['project']]
        assert len(lessons) == 2 and len(projects) == 1
        if not any(module['title'] == module_title for module in hub['data']['modules']):
            hub['data']['modules'].insert(-1, {'title': module_title,
                                               'summary': 'Follow the evidence chain, then test the release gate.',
                                               'lessons': lessons})
        practice = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
        if projects[0] not in practice['lessons']:
            practice['lessons'].append(projects[0])
        if '<h2>' + module_title + '</h2>' not in hub['body']:
            hub['body'] += '<h2>' + module_title + '</h2>' + link_list(lessons)
            hub['body'] += '<h2>' + ('Incident evidence project' if module_title == LINEAGE else 'Replica erasure project') + '</h2>' + link_list(projects)
        if projects[0] not in project_hub['data']['modules'][0]['lessons']:
            project_hub['data']['modules'][0]['lessons'].append(projects[0])
        if projects[0] not in project_hub['body']:
            project_hub['body'] += '<h2>' + module_title + '</h2>' + link_list(projects)
    hub['updated_at'] = project_hub['updated_at'] = now

    crosslinks = [
        ('data-engineering/pipeline-lineage-and-impact-analysis', 'data-engineering/run-scoped-lineage-and-release-evidence'),
        ('data-engineering/replay-manifest-and-audit-trail', 'data-engineering/run-scoped-lineage-and-release-evidence'),
        ('data-engineering/pipeline-slos-and-error-budgets', 'data-engineering/telemetry-correlation-and-cardinality-budget'),
        ('data-engineering/failure-classification-and-retry-budget', 'data-engineering/telemetry-correlation-and-cardinality-budget'),
        ('data-engineering/revenue-mart-release-project', 'data-engineering/revenue-incident-evidence-project'),
        ('data-engineering/serving-index-and-freshness-contract', 'data-engineering/revenue-incident-evidence-project'),
        ('data-engineering/data-classification-and-access-boundaries', 'data-engineering/regional-data-boundary-and-egress-gates'),
        ('data-engineering/data-pipeline-rpo-rto-and-replication-lag', 'data-engineering/regional-data-boundary-and-egress-gates'),
        ('data-engineering/deletion-propagation-and-erasure-proof', 'data-engineering/replica-version-erasure-and-restore-guard'),
        ('data-engineering/event-envelope-identity-and-tombstones', 'data-engineering/replica-version-erasure-and-restore-guard'),
        ('data-engineering/regional-analytics-recovery-project', 'data-engineering/replica-erasure-proof-project'),
        ('data-engineering/governed-customer-mart-project', 'data-engineering/replica-erasure-proof-project'),
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
    import_path = ROOT / 'work/aitrove-data-engineering-lineage-residency-import-20261006.json'
    import_path.write_text(json.dumps([by_path[path] for path in sorted(changed)], ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'new_articles': len(LESSONS), 'new_projects': 2,
                      'crosslinks': len(crosslinks), 'import_rows': len(changed),
                      'import_path': str(import_path)}))


if __name__ == '__main__':
    publish()
