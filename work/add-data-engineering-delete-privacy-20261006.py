"""Add original Data Engineering lessons on delete maintenance and aggregate privacy."""
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
DELETES = 'Delete-file maintenance and snapshot safety'
PRIVACY = 'Aggregate privacy and lineage access'
context = runpy.run_path(str(ROOT / 'work/add-data-engineering-lineage-residency-20261006.py'))
LESSONS = context['LESSONS']
LESSONS.clear()
add = context['add']

add('delete-file-amplification-and-compaction', 'Delete-file amplification and compaction',
    'A lakehouse delete can avoid rewriting a large data file immediately, but accumulated delete metadata raises planning and read cost until maintenance catches up.', [
    ('Distinguish logical removal from rewritten data', 'A reader may combine live data files with position deletes, equality deletes or a table-specific deletion bitmap. The row disappears from the current query, yet the original bytes can remain in older files and snapshots. Do not treat a successful row-level query as physical erasure. [[data-engineering/deletion-propagation-and-erasure-proof|Erasure proof]] must examine retention and every copy separately.'),
    ('Count work at the query boundary', 'One tiny delete file per transaction can make a scan open hundreds of objects before producing a few rows. Track applicable delete-file count, delete bytes, changed-row density, data-file size and query latency by partition. A table-wide average hides a hot partition. Run the same query before and after maintenance; file count alone is a proxy, not the user-facing outcome.'),
    ('Choose the narrowest rewrite', 'If the data files are well sized but delete files are fragmented, compact compatible delete files without rewriting unaffected data. If many rows in a data file are deleted, rewrite that data file with surviving rows and publish a new snapshot. Preserve the delete applicability rules and sequence ordering; combining incompatible generations can resurrect a row or erase a newer insert.'),
    ('Schedule by benefit and budget', 'Estimate bytes read, bytes written, metadata operations and expected scan reduction for each candidate partition. Prefer the hottest high-amplification partitions under a daily I/O budget. A low-traffic historical partition may safely wait. Coordinate maintenance with ingestion so repeated rewrites do not chase each new small batch; [[data-engineering/compaction-retention-and-replay-horizon|retention policy]] determines when old files may finally be removed.'),
    ('Prove the post-commit state', 'Commit replacement files and metadata as one snapshot, then compare visible keys and control totals before moving consumers. A failed rewrite must leave the old snapshot queryable. Check readers pinned to older snapshots before deleting physical files. Measure query p95 after the commit and record whether the predicted benefit materialized; otherwise the scheduler may spend more than it saves.')],
    '''partitions = [
    {"name": "orders-west", "data_mb": 384, "delete_files": 47, "reads_per_day": 260},
    {"name": "orders-archive", "data_mb": 512, "delete_files": 6, "reads_per_day": 2},
]

def maintenance_priority(partition):
    return partition["delete_files"] * partition["reads_per_day"] / partition["data_mb"]

ranked = sorted(partitions, key=maintenance_priority, reverse=True)
assert ranked[0]["name"] == "orders-west"
assert maintenance_priority(ranked[0]) > maintenance_priority(ranked[1])''',
    'Ranking P partitions costs O(P log P) time and O(P) space in this reference. Actual rewrite cost is dominated by bytes read and written, while every retained snapshot adds metadata and storage pressure. A cheap delete-file merge can reduce open overhead without reclaiming deleted row bytes; a data-file rewrite costs more but may reduce both scan work and later delete handling.',
    ['Do not infer physical erasure from a current-snapshot query.', 'Do not merge delete metadata across incompatible sequence boundaries.', 'Do not rewrite every partition on the same fixed schedule without measuring read benefit.'],
    ['data-engineering/compaction-retention-and-replay-horizon', 'data-engineering/deletion-propagation-and-erasure-proof', 'data-engineering/lakehouse-snapshot-and-atomic-commit', 'data-engineering/snapshot-safe-delete-rewrite', 'data-engineering/order-lake-delete-maintenance-project'], DELETES)

add('snapshot-safe-delete-rewrite', 'Snapshot-safe delete rewrites',
    'A delete rewrite is correct only if the new snapshot preserves the visible row set and an older retained snapshot remains readable for its supported lifetime.', [
    ('Pin the starting snapshot', 'A maintenance worker reads snapshot 74 while ingestion continues. It must identify the exact data files, applicable deletes and sequence positions it intends to replace. An unpinned scan can mix two table states and produce a candidate that never corresponded to one valid snapshot. [[data-engineering/optimistic-table-commits-and-conflicts|Optimistic commit rules]] decide whether the replacement still applies when another writer advances the table.'),
    ('Preserve applicability', 'A position delete names a file and row location; moving rows to a new file changes that location. A rewrite must apply the old delete before writing surviving rows, then retire only metadata whose scope is fully replaced. An equality delete may also affect other live files. Do not discard it merely because one rewritten file no longer needs it. Retain or transform it according to the table format and sequence contract.'),
    ('Validate two snapshots', 'Compare visible key sets, duplicate counts and monetary controls between the pinned source and candidate. Also query one older retained snapshot through its original metadata after the new commit. A maintenance job that produces the right current answer but garbage-collects files still referenced by an older snapshot breaks time travel and rollback. [[data-engineering/replay-manifest-and-audit-trail|The manifest]] should name both snapshots and their file inventories.'),
    ('Handle concurrent writes explicitly', 'If an ingestion commit adds a newer row or delete while compaction runs, either rebase the candidate after conflict validation or retry from the new snapshot. Never publish a replacement that silently drops the concurrent change. Bound retries and surface repeated conflicts; a hot partition might need a smaller maintenance slice or a quiet window rather than an infinite retry loop.'),
    ('Separate commit from cleanup', 'A new snapshot can be committed before obsolete files are eligible for physical removal. Keep cleanup asynchronous and governed by replay horizons, legal holds and replica lag. Verify no retained snapshot references a file before removing it. A delete request may require an independent erasure workflow that can shorten the normal retention path only where policy permits.')],
    '''source_rows = {"order-47": 2375, "order-48": 6400, "order-49": -125}
deleted = {"order-48"}

def visible_rows(rows, removed):
    return {order_id: cents for order_id, cents in rows.items()
            if order_id not in removed}

candidate = visible_rows(source_rows, deleted)
assert candidate == {"order-47": 2375, "order-49": -125}
assert sum(candidate.values()) == 2250
assert source_rows["order-48"] == 6400  # retained snapshot still has its bytes''',
    'Filtering N rows uses O(N) expected time and O(N) candidate space. Real snapshot validation also reads metadata and often the rewritten data, so its I/O is proportional to selected files. Retaining old files costs storage until expiry, but deleting them early can invalidate rollback. Conflict retries multiply rewrite cost and should be measured separately from successful maintenance.',
    ['Do not remove an equality delete that still applies to another live file.', 'Do not garbage-collect files referenced by retained snapshots.', 'Do not ignore an ingestion commit that lands during a rewrite.'],
    ['data-engineering/optimistic-table-commits-and-conflicts', 'data-engineering/lakehouse-snapshot-and-atomic-commit', 'data-engineering/compaction-retention-and-replay-horizon', 'data-engineering/delete-file-amplification-and-compaction', 'data-engineering/order-lake-delete-maintenance-project'], DELETES)

add('order-lake-delete-maintenance-project', 'Project: reduce delete overhead without breaking old snapshots',
    'Plan a bounded delete-file maintenance run, prove current-row equivalence and keep a retained snapshot readable after publication.', [
    ('Create the workload', 'Load 470 order rows into three partitions. Mark 73 rows as deleted through several small delete batches, then create a retained snapshot before maintenance. Give one partition most of the delete files and most of the reader traffic. Record per-partition file counts, scan bytes, query latency and visible totals. [[data-engineering/delete-file-amplification-and-compaction|The priority score]] should select the hot partition first rather than the largest partition by bytes.'),
    ('Build a bounded plan', 'Set a daily rewrite ceiling of 768 MB and list the selected files, applicable delete generations and expected bytes written. Choose whether merging delete metadata or rewriting data files offers the better read-cost reduction. Name the snapshot and input sequence in the plan. A plan with no budget ceiling can consume capacity needed by ingestion or interactive reads.'),
    ('Inject a concurrent update', 'Start rewriting from snapshot 74, then commit one new order and one delete to the same partition. The first candidate must fail conflict validation or be safely rebased. Retry with the new snapshot and prove that the newer insert is visible while the deleted old row remains absent. [[data-engineering/snapshot-safe-delete-rewrite|Snapshot safety]] is tested at both the current and retained generations.'),
    ('Validate publication and cleanup', 'Compare current key sets, duplicate counts and amount totals with a pinned pre-rewrite oracle. Query the retained snapshot to show its older answer is still readable. Commit the replacement atomically. Run garbage-collection eligibility checks but leave old files in place while the replay horizon references them; record this as retained storage, not an incomplete maintenance commit.'),
    ('Deliver the evidence', 'Provide the before-and-after file inventory, selection score, I/O budget, conflict trace, retry snapshot, two query outputs, p95 scan latency and cleanup eligibility report. Include a deliberately invalid candidate that omits one delete and show the gate rejecting it. A lower file count without row-equivalence proof is not a successful project result.')],
    '''source = {f"order-{order_number}": order_number * 25
          for order_number in range(47, 517)}
deleted = {f"order-{order_number}" for order_number in range(47, 120)}

def current_snapshot(rows, removed):
    return {key: amount for key, amount in rows.items() if key not in removed}

before = current_snapshot(source, deleted)
after = current_snapshot(source, deleted)
assert len(source) == 470
assert len(before) == 397
assert before == after''',
    'The reference comparison is O(N) expected time and O(N) state for N orders. The lakehouse exercise also incurs object opens, delete-file scans, candidate writes and one retained snapshot. A bounded maintenance plan controls compute spend; it does not authorize early deletion of files needed by readers pinned to older generations.',
    ['Do not select work by file size alone when reader traffic differs.', 'Do not publish a candidate that ignores a concurrent commit.', 'Do not treat a correct current query as proof that retained snapshots survived.'],
    ['data-engineering/delete-file-amplification-and-compaction', 'data-engineering/snapshot-safe-delete-rewrite', 'data-engineering/compaction-retention-and-replay-horizon', 'data-engineering/optimistic-table-commits-and-conflicts', 'data-engineering/replay-manifest-and-audit-trail'], DELETES, True)

add('small-group-suppression-and-release-grain', 'Small-group suppression and release grain',
    'An aggregate can expose a person when its released group is too narrow or when another published total lets a reader subtract a hidden group.', [
    ('Name the privacy unit', 'A customer may make several transactions. Counting rows instead of distinct customers makes a small group look safer than it is. Define the privacy unit and the smallest combination of dimensions that a consumer may query. A region-day-channel cube is far more revealing than a region-month rollup, even when both report the same overall revenue. [[data-engineering/fact-grain-and-measure-additivity|Fact grain]] must be separate from the release grain.'),
    ('Set a minimum cohort rule', 'Require a minimum distinct-person count for each released cell and suppress cells below it. State whether totals that include suppressed cells can also be released. A single suppressed cell can be recovered by subtracting visible child cells from an exact parent total. Test the full set of available queries and exports, not one dashboard tile in isolation. A threshold reduces risk but does not prove anonymity.'),
    ('Generalize when suppression destroys use', 'If store-day cells are sparse, publish store-week or region-day groups instead. Bucketing can preserve useful trends while making individuals harder to isolate. Keep the grouping decision and owner approval in the dataset contract. Never choose a broader group by silently merging unrelated populations if that changes the business meaning of the metric.'),
    ('Control repeated releases', 'A cell with 47 people today and 48 tomorrow may disclose the added person when exact totals are compared. Define a release cadence and whether historical revisions replace earlier public answers. For high-risk use, consider a formally reviewed privacy mechanism with a budget for repeated queries; simple thresholding cannot solve every differencing attack. [[data-engineering/correction-aware-quality-alerts|Correction handling]] still has to keep the published numbers accurate.'),
    ('Test the consumer surface', 'Query permitted groups, suppressed groups, parent totals and neighboring dates through the same API the consumer uses. Inspect CSV exports, cached responses and chart tooltips. A privacy check only in the transformation job is bypassed if a flexible query endpoint can create narrower groups. Record the accepted release schema and deny unapproved dimensions before any result leaves the service.')],
    '''customers_by_region = {
    "west": {"cust-47", "cust-48", "cust-49", "cust-50", "cust-51", "cust-52"},
    "east": {"cust-53", "cust-54"},
}

def releasable_counts(groups, minimum_people):
    return {region: len(customers) for region, customers in groups.items()
            if len(customers) >= minimum_people}

assert releasable_counts(customers_by_region, 5) == {"west": 6}''',
    'Counting distinct units across N records is O(N) expected time and O(U) state for U distinct people in the reference. Fine-grained cubes multiply stored groups and disclosure checks; broader groups cost less but lose detail. This simple gate is illustrative, not a formal privacy guarantee: repeated releases and overlapping totals require additional policy and testing.',
    ['Do not count transactions when the privacy unit is a person.', 'Do not publish an exact parent total that reveals one suppressed child by subtraction.', 'Do not claim a group threshold alone guarantees anonymity.'],
    ['data-engineering/fact-grain-and-measure-additivity', 'data-engineering/data-classification-and-access-boundaries', 'data-engineering/row-policy-and-column-mask-tests', 'data-engineering/lineage-metadata-minimization', 'data-engineering/regional-metrics-privacy-release-project'], PRIVACY)

add('lineage-metadata-minimization', 'Lineage metadata minimization and access',
    'Lineage is operational evidence, but raw file paths, partition values and row samples can reveal information even when the data table itself is protected.', [
    ('Separate graph shape from evidence', 'Most readers need to know that a regional mart depends on orders and exchange rates; they do not need customer IDs, exact object paths or failed-row payloads. Publish dataset- and transform-level edges broadly, then keep run-level versions in a restricted evidence store. [[data-engineering/run-scoped-lineage-and-release-evidence|Runtime lineage]] remains precise without making every detail visible in the catalog.'),
    ('Classify metadata fields', 'A partition key may contain an account number or small geographic area. A file path can reveal a tenant name. Label fields by sensitivity, not by the fact that they are metadata. Remove or tokenize identifiers before emitting traces and catalog events, and avoid copying sample records into error descriptions. [[data-engineering/data-classification-and-access-boundaries|The classification contract]] should cover lineage and diagnostic copies.'),
    ('Grant by investigation purpose', 'A general analyst may inspect upstream dataset names and published freshness. An incident responder may temporarily read a run manifest with input generations, while an erasure operator needs deletion evidence. Apply separate roles, retention windows and access logs. A single all-access catalog role makes sensitive metadata available to people who never needed the underlying rows.'),
    ('Preserve joinability safely', 'Use opaque run IDs to connect an alert, trace and restricted manifest. The lookup from opaque ID to sensitive source details belongs behind access control; hashing a predictable customer ID without a secret does not reliably hide it. Keep stable IDs only for the period required to investigate and audit a release. Avoid high-cardinality identifiers in metric labels even when access is restricted.'),
    ('Exercise a failed job', 'Cause a malformed row to fail and inspect every emitted surface: job log, trace, alert, catalog event and support export. None of the broad surfaces should contain the row payload or tenant path. An authorized reviewer must still be able to map the opaque incident key to the restricted evidence and the exact published generation. Record denied access attempts without echoing the protected value.')],
    '''run_manifest = {
    "run_id": "run-247",
    "dataset": "regional_sales",
    "source_path": "restricted/tenant-47/orders",
    "generation": 82,
}

def catalog_projection(manifest):
    return {"run_id": manifest["run_id"],
            "dataset": manifest["dataset"],
            "generation": manifest["generation"]}

public_metadata = catalog_projection(run_manifest)
assert "source_path" not in public_metadata
assert public_metadata["generation"] == 82''',
    'Projecting M manifests is O(M) time and O(M) output state; access checks add one policy decision per read. Keeping full evidence in a restricted store has storage and operational cost, but avoids broad catalog exposure. A useful catalog need not replicate every source field. Measure audit retention and lookup frequency before expanding a lineage payload.',
    ['Do not assume metadata is nonsensitive because it is not a table row.', 'Do not put predictable raw IDs in broadly visible logs or metric labels.', 'Do not remove so much evidence that an authorized responder cannot reconstruct a release.'],
    ['data-engineering/run-scoped-lineage-and-release-evidence', 'data-engineering/telemetry-correlation-and-cardinality-budget', 'data-engineering/data-classification-and-access-boundaries', 'data-engineering/small-group-suppression-and-release-grain', 'data-engineering/regional-metrics-privacy-release-project'], PRIVACY)

add('regional-metrics-privacy-release-project', 'Project: release regional metrics without exposing small groups',
    'Build a regional payment summary whose query surface, exports and lineage catalog agree on the same disclosure boundary.', [
    ('Write the release contract', 'Create payment records for several regions and days, including a sparse region with two people making multiple payments. Define the person as the privacy unit and name the permitted region-week output grain. List every consumer: dashboard, CSV export, query API and catalog. [[data-engineering/small-group-suppression-and-release-grain|The group gate]] must apply to all of them, not only the chart.'),
    ('Build and challenge the aggregate', 'Count distinct people and sum payment amounts for each candidate cell. Set a minimum of five people, suppress the sparse region and test whether any exact parent total reveals its amount through subtraction. If it does, withhold or coarsen that parent as well. Introduce a late correction and rerun the release checks before moving the pointer. A corrected table does not authorize a narrower disclosure.'),
    ('Split broad and restricted lineage', 'Publish dataset dependencies, release generation and opaque run ID in the general catalog. Keep partition paths, tenant mapping and detailed source positions in a restricted manifest. [[data-engineering/lineage-metadata-minimization|Metadata minimization]] should be visible in a failed-job log and support export too. Grant one incident-responder role temporary access and prove a general analyst is denied the restricted view.'),
    ('Test differencing and replay', 'Publish two adjacent candidate weeks, then see whether subtracting their exact totals isolates a newly added person. Reject or generalize a release that leaks through this path. Replay the same correction and verify the published aggregate does not double count it. Query both the serving API and a cached response after pointer movement; an old cache can disclose an earlier, less protected generation.'),
    ('Submit a proof bundle', 'Provide the privacy-unit definition, approved dimensions, suppressed-cell report, parent-total test, late-correction result, public and restricted lineage projections, role checks, cache result and final consumer query. Show one denied narrow query and one permitted broad query. The exercise is not complete merely because a transformation produced a table with fewer rows.')],
    '''payments = [
    ("west", "cust-47", 2375), ("west", "cust-48", 6400),
    ("west", "cust-49", 1250), ("west", "cust-50", 3100),
    ("west", "cust-51", 800), ("east", "cust-52", 900),
    ("east", "cust-52", 400), ("east", "cust-53", 1700),
]

def released_totals(records, minimum_people):
    groups = {}
    for region, customer_id, cents in records:
        state = groups.setdefault(region, {"people": set(), "cents": 0})
        state["people"].add(customer_id)
        state["cents"] += cents
    return {region: state["cents"] for region, state in groups.items()
            if len(state["people"]) >= minimum_people}

assert released_totals(payments, 5) == {"west": 13925}''',
    'Aggregation is O(N) expected time and O(U + G) state for N payments, U unique people and G groups. Full disclosure testing adds work across all released combinations and versions, not just the current table. A restricted evidence store and dated last-good release add storage, while coarse cells reduce analytical detail. The threshold demonstration is not a formal anonymity guarantee.',
    ['Do not count the same person twice because they made multiple payments.', 'Do not expose a suppressed amount through a parent total or stale export.', 'Do not put tenant paths into a broadly readable lineage catalog.'],
    ['data-engineering/small-group-suppression-and-release-grain', 'data-engineering/lineage-metadata-minimization', 'data-engineering/row-policy-and-column-mask-tests', 'data-engineering/correction-aware-quality-alerts', 'data-engineering/replay-manifest-and-audit-trail'], PRIVACY, True)

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
    for module_title in (DELETES, PRIVACY):
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
            hub['body'] += '<h2>' + ('Delete maintenance project' if module_title == DELETES else 'Private metrics project') + '</h2>' + link_list(projects)
        if projects[0] not in project_hub['data']['modules'][0]['lessons']:
            project_hub['data']['modules'][0]['lessons'].append(projects[0])
        if projects[0] not in project_hub['body']:
            project_hub['body'] += '<h2>' + module_title + '</h2>' + link_list(projects)
    hub['updated_at'] = project_hub['updated_at'] = now

    crosslinks = [('data-engineering/compaction-retention-and-replay-horizon', 'data-engineering/delete-file-amplification-and-compaction'),
        ('data-engineering/deletion-propagation-and-erasure-proof', 'data-engineering/delete-file-amplification-and-compaction'),
        ('data-engineering/optimistic-table-commits-and-conflicts', 'data-engineering/snapshot-safe-delete-rewrite'),
        ('data-engineering/lakehouse-snapshot-and-atomic-commit', 'data-engineering/snapshot-safe-delete-rewrite'),
        ('data-engineering/versioned-order-lake-release-project', 'data-engineering/order-lake-delete-maintenance-project'),
        ('data-engineering/replay-manifest-and-audit-trail', 'data-engineering/order-lake-delete-maintenance-project'),
        ('data-engineering/fact-grain-and-measure-additivity', 'data-engineering/small-group-suppression-and-release-grain'),
        ('data-engineering/row-policy-and-column-mask-tests', 'data-engineering/small-group-suppression-and-release-grain'),
        ('data-engineering/run-scoped-lineage-and-release-evidence', 'data-engineering/lineage-metadata-minimization'),
        ('data-engineering/data-classification-and-access-boundaries', 'data-engineering/lineage-metadata-minimization'),
        ('data-engineering/governed-customer-mart-project', 'data-engineering/regional-metrics-privacy-release-project'),
        ('data-engineering/regional-data-boundary-and-egress-gates', 'data-engineering/regional-metrics-privacy-release-project')]
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
    import_path = ROOT / 'work/aitrove-data-engineering-delete-privacy-import-20261006.json'
    import_path.write_text(json.dumps([by_path[path] for path in sorted(changed)], ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'new_articles': len(LESSONS), 'new_projects': 2,
                      'crosslinks': len(crosslinks), 'import_rows': len(changed),
                      'import_path': str(import_path)}))


if __name__ == '__main__':
    publish()
