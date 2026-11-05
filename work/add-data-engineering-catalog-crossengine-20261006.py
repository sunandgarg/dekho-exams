"""Publish six original lessons on external metadata and cross-engine verification."""
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
CATALOG = 'External-table metadata and freshness'
ENGINE = 'Cross-engine result verification'
context = runpy.run_path(str(ROOT / 'work/add-data-engineering-lineage-residency-20261006.py'))
LESSONS = context['LESSONS']
LESSONS.clear()
add = context['add']

add('external-table-metadata-cache-and-refresh', 'External-table metadata cache and refresh',
    'An external query can be slow or incomplete before it scans a single row: its engine first has to discover a trustworthy file set.', [
    ('Locate the planning bottleneck', 'Separate catalog lookup, object listing, file-footer reads and actual row scan in query traces. When millions of objects sit behind a broad prefix, listing may dominate latency even if the filter selects one hour of data. Record files considered, files opened, metadata age and scan bytes for the same predicate. An index that speeds partition lookup does not automatically reduce physical bytes scanned. [[data-engineering/partition-planning-and-skew|Partition planning]] is a separate design decision.'),
    ('Treat freshness as a contract', 'A cache of paths, partition values and statistics cuts remote metadata calls. It also represents an earlier view of the object store. Define an allowed metadata age for each consumer and record the latest successful refresh generation. The query must either use metadata within that window, refresh before reading or fail closed when the required freshness cannot be met. Do not report a successful empty result when the relevant files have merely not been discovered.'),
    ('Refresh after a published batch', 'An ingest job should write data files, validate them and publish its own batch marker before requesting metadata refresh. For predictable arrivals, refreshing only changed prefixes can avoid a full inventory. Make the refresh idempotent and bind its success record to the batch marker. If the job fails halfway through a listing, leave the prior usable cache intact and expose the lag. A refresh timestamp without a completed generation is weak evidence.'),
    ('Distinguish cache from table snapshot', 'A metadata cache is a planning aid, not an atomic table commit. Concurrent object writes and deletions can still make an ordinary external-table listing inconsistent with another engine or with a previous query. For a transactional lakehouse table, pin its committed snapshot and let the table format define file membership. [[data-engineering/lakehouse-snapshot-and-atomic-commit|Snapshot publication]] supplies a stronger boundary than refreshing a list of keys.'),
    ('Measure the exchange', 'Compare cold and warm plans with the same predicate and data version. Count catalog calls, listed objects, refresh work, median planning time and p95 end-to-end latency. A tighter freshness budget can force more listings and higher object-store cost; a longer one may miss a new batch. Keep both numbers visible. Test a changed table location too: an old cache can stay internally consistent while pointing at the wrong prefix.')],
    '''from datetime import datetime, timedelta, timezone

cache = {"generation": "telemetry-47", "refreshed_at": datetime(2026, 9, 27, 8, tzinfo=timezone.utc),
         "paths": ("hour=08/events-47.parquet",)}
published_generation = "telemetry-48"
query_time = datetime(2026, 9, 27, 10, tzinfo=timezone.utc)

def may_serve(metadata, required_generation, now, maximum_age):
    return (metadata["generation"] == required_generation
            and now - metadata["refreshed_at"] <= maximum_age)

assert not may_serve(cache, published_generation, query_time, timedelta(hours=3))
cache.update(generation=published_generation, refreshed_at=query_time,
             paths=("hour=08/events-47.parquet", "hour=09/events-48.parquet"))
assert may_serve(cache, published_generation, query_time, timedelta(minutes=47))''',
    'Checking one cache generation is O(1) time and space; rebuilding an inventory is at least O(F) metadata work for F discovered files unless the platform supports a narrower refresh. Caching reduces repeated listings but adds refresh jobs and lag monitoring. A scan can still be expensive after a fast plan if file layout and predicate pruning are poor.',
    ['Do not equate a warm metadata cache with an atomic data snapshot.', 'Do not call an empty query correct when a new partition was never discovered.', 'Do not refresh before the writer finishes and publishes its batch.'],
    ['data-engineering/partition-planning-and-skew', 'data-engineering/lakehouse-snapshot-and-atomic-commit', 'data-engineering/serving-index-and-freshness-contract', 'data-engineering/partition-registration-and-manifest-gates', 'data-engineering/external-telemetry-catalog-project'], CATALOG)

add('partition-registration-and-manifest-gates', 'Partition registration and manifest gates',
    'A partition becomes queryable only when its data, catalog entry and release marker agree; a directory name by itself proves little.', [
    ('Choose a discovery model', 'Explicit registration lists only known partitions, while projection derives possible locations from a pattern. Projection avoids a per-partition catalog write, but it can invent empty locations and may be specific to one query engine. Explicit registration costs metadata operations and can lag ingestion. Choose based on partition count, sparsity, engine mix and freshness needs, then test another engine rather than assuming it reads the same projected inventory.'),
    ('Make the release marker authoritative', 'Write all objects for a batch under immutable names and validate their schema, row count and checksums. Build a manifest naming the expected objects and their sizes. Only then register the partition or advance a published marker. A consumer should require a complete manifest before treating a newly visible directory as a finished interval. [[data-engineering/task-retries-and-atomic-partition-output|Atomic partition output]] still matters when a task retries and leaves abandoned objects.'),
    ('Compare three inventories', 'At promotion, compare the manifest file set, object-store listing and catalog-visible partitions. The sets need not be identical at every instant, but the published files must all be present, the catalog must target the correct prefix and no unapproved file may be read. Check object size or checksum where available; matching file names alone will miss an overwritten object. Save the comparison report with the release generation.'),
    ('Handle correction and removal', 'A corrected hour should publish a new immutable generation and switch the catalog or table pointer to it. Retire older objects only after reader and replay retention permits. Removing a partition entry before its replacement is ready creates a query gap; adding the replacement without excluding old files can double count. [[data-engineering/compaction-retention-and-replay-horizon|Retention rules]] determine when stale bytes may be collected.'),
    ('Test the broken boundary', 'Inject one missing object, one stray object, a catalog entry pointing at the previous generation and a projection range that omits a valid date. The gate should reject each release with a concrete reason. Also show that a projected empty location is not an ingestion success signal. A second engine must resolve the same published file set before cross-engine comparison is meaningful.')],
    '''manifest = {"generation": "sensor-47", "files": {
    "day=27/hour=08/part-47.parquet": 2375,
    "day=27/hour=08/part-48.parquet": 6400,
}}
objects = dict(manifest["files"])
catalog_prefix = "day=27/hour=08/"

def release_issues(expected, observed, prefix):
    missing = set(expected) - set(observed)
    unexpected = set(observed) - set(expected)
    changed = {path for path in expected.keys() & observed.keys()
               if expected[path] != observed[path]}
    wrong_prefix = {path for path in expected if not path.startswith(prefix)}
    return missing, unexpected, changed, wrong_prefix

assert release_issues(manifest["files"], objects, catalog_prefix) == (set(), set(), set(), set())
assert release_issues(manifest["files"], {"day=27/hour=08/part-47.parquet": 2375}, catalog_prefix)[0]''',
    'Set comparison is O(F) expected time and O(F) auxiliary space for F files. Full object inventory and checksums can dominate wall time and request spend; compare only changed prefixes when the storage and publication contract allows it. Projection may save catalog writes but can increase planning work for many nonexistent partitions.',
    ['Do not register a partition before every expected object is durable.', 'Do not mistake a projected location for a completed batch.', 'Do not replace objects in place while readers or caches retain old metadata.'],
    ['data-engineering/external-table-metadata-cache-and-refresh', 'data-engineering/task-retries-and-atomic-partition-output', 'data-engineering/compaction-retention-and-replay-horizon', 'data-engineering/replay-manifest-and-audit-trail', 'data-engineering/external-telemetry-catalog-project'], CATALOG)

add('external-telemetry-catalog-project', 'Project: publish telemetry with a catalog freshness gate',
    'Build a small external telemetry release that rejects incomplete files and stale metadata before an analyst query can use it.', [
    ('Stage a measurable workload', 'Create 47 hourly telemetry partitions with immutable object names. Give one hour 23 files and the others three each, so a broad listing and a pruned query have visibly different planning costs. Record the source generation, object inventory and query predicate. Establish baseline planning time, listed-object count and scan bytes. [[data-engineering/partition-planning-and-skew|Partition design]] affects the result independently of cache policy.'),
    ('Publish one hour safely', 'Write a manifest for the next hour with expected paths, sizes, record counts and a batch generation. Omit one object on the first attempt. The gate must reject it before catalog registration and keep the last published hour readable. Add the missing object, rerun the gate, register the partition and then refresh the metadata cache. Store the completed refresh generation, not merely its start time.'),
    ('Exercise a stale reader', 'Issue a query that requires the newly published generation while the cache still names the previous one. It must refresh, use a permitted direct listing or return a freshness error under the chosen contract. It must not return zero rows as though there were no telemetry. [[data-engineering/external-table-metadata-cache-and-refresh|Cache freshness]] is checked at the query boundary, not inferred from the ingest success log.'),
    ('Compare engines and corrections', 'Read the same published hour from a second engine. If one engine derives partitions from a pattern and the other uses registered entries, prove that both see the same manifest files. Publish a corrected generation with one changed record, and ensure readers move as a unit instead of reading old and new objects together. Leave retained files until their replay horizon closes.'),
    ('Submit release evidence', 'Provide the failed and successful gate reports, inventory diff, catalog entry, cache generation, reader response, p95 planning time and request count. Include a trace where a table location changes but the cache has not refreshed; the gate must catch it. A fast query with stale or partial data fails this project even if its latency chart looks excellent.')],
    '''expected_files = {
    "hour=09/telemetry-47.parquet": 470,
    "hour=09/telemetry-48.parquet": 480,
}
observed_files = {"hour=09/telemetry-47.parquet": 470}

def can_publish(manifest_files, object_files, catalog_generation, requested_generation):
    return (manifest_files == object_files
            and catalog_generation == requested_generation)

assert not can_publish(expected_files, observed_files, "telemetry-46", "telemetry-47")
observed_files["hour=09/telemetry-48.parquet"] = 480
assert can_publish(expected_files, observed_files, "telemetry-47", "telemetry-47")''',
    'The reference gate compares F file entries in O(F) expected time and O(F) stored inventory. Production cost also includes object listings, catalog registration, cache refresh and two engine queries. A targeted prefix refresh saves work when arrivals are predictable. The safety gate may add latency to publication; measure it against the cost of serving a partial interval.',
    ['Do not return a stale empty result for a newly published hour.', 'Do not treat a catalog timestamp as proof that a refresh completed.', 'Do not let two engines compare different file generations.'],
    ['data-engineering/external-table-metadata-cache-and-refresh', 'data-engineering/partition-registration-and-manifest-gates', 'data-engineering/replay-manifest-and-audit-trail', 'data-engineering/serving-index-and-freshness-contract', 'data-engineering/cross-engine-shadow-read-project'], CATALOG, True)

add('cross-engine-sql-semantic-differences', 'Cross-engine SQL semantic differences',
    'A translated query can compile and still change a business answer because data types, null rules and time boundaries are part of the computation.', [
    ('Define the result contract first', 'Name the business grain, column types, null meaning, currency precision, time zone and ordering requirements before translating SQL. A generated query is only a candidate implementation of that contract. Compare outputs from a pinned input generation; otherwise a late event can masquerade as an engine difference. [[data-engineering/semantic-metric-contract-and-reconciliation|Metric contracts]] provide the shared definition.'),
    ('Probe null and anti-join behavior', 'A NOT IN predicate can produce surprising results when its right side contains NULL. Other constructs differ in how casts, division by zero or invalid dates fail or return NULL. Use a tiny fixture with null keys, duplicate keys and malformed values to expose semantics before full-table reconciliation. Prefer explicit null policy and a tested anti-join formulation to a dialect-dependent shortcut.'),
    ('Protect numeric meaning', 'Decimal precision, scale and rounding mode matter for payment totals. Casting to binary floating point to make two schemas appear compatible can introduce small differences on every row that grow after aggregation. Specify whether tolerance is zero, an absolute amount or a relative bound, and explain why. For money, compare integer minor units or exact decimals when both engines support them.'),
    ('Pin time boundaries', 'A timestamp with an offset and a local wall-clock value are not interchangeable. A daily grouping near midnight can shift between regions if one engine applies a session time zone and the other uses UTC. Set the zone in the query or connection, provide daylight-saving boundary fixtures and compare interval inclusion rules. [[data-engineering/event-time-and-late-arrivals|Event-time handling]] also determines which late records belong to the result.'),
    ('Compare canonical values', 'Normalize only representation differences allowed by the contract, such as a decimal string format or stable column alias. Preserve meaningful differences, including NULL versus zero and a missing row versus an empty string. Sort by a complete key before comparing sets, and do not compare unordered result positions. Keep the original values alongside canonical values so a discrepancy remains explainable.')],
    '''from decimal import Decimal
from datetime import datetime, timezone

source = [("region-west", "2026-09-27T23:40:00+00:00", "47.25"),
          ("region-east", "2026-09-28T00:20:00+00:00", None)]
target = [("region-east", "2026-09-28T00:20:00Z", None),
          ("region-west", "2026-09-27T23:40:00Z", "47.25")]

def canonical(rows):
    return sorted((region,
                   datetime.fromisoformat(timestamp.replace("Z", "+00:00")).astimezone(timezone.utc),
                   None if amount is None else Decimal(amount))
                  for region, timestamp, amount in rows)

assert canonical(source) == canonical(target)''',
    'Canonicalizing N rows requires O(N log N) time for sorting and O(N) output space. Large comparisons should partition by stable key and use staged hashes plus row-level follow-up. Exact decimal arithmetic costs more than floating point but avoids an unjustified numeric tolerance. Query scans in both engines often dominate the comparison job.',
    ['Do not assume successful SQL translation proves equivalent results.', 'Do not convert NULL to zero during canonicalization.', 'Do not compare unordered row positions or unpinned input generations.'],
    ['data-engineering/semantic-metric-contract-and-reconciliation', 'data-engineering/schema-compatibility-and-consumer-rollout', 'data-engineering/migration-reconciliation-and-cutover', 'data-engineering/cross-engine-shadow-reads-and-discrepancy-triage', 'data-engineering/cross-engine-shadow-read-project'], ENGINE)

add('cross-engine-shadow-reads-and-discrepancy-triage', 'Cross-engine shadow reads and discrepancy triage',
    'Shadow reads let a replacement engine answer real workloads without exposing its result until differences have been classified and bounded.', [
    ('Select representative queries', 'Capture queries by business metric and cost class, including filtered detail, grouped aggregates, null-heavy joins and a query near a date boundary. Redact sensitive literals in stored traces, then replay against a pinned source generation in both engines. A random sample of cheap queries may miss the one monthly revenue report whose decimal and time-zone semantics matter most.'),
    ('Build a comparison envelope', 'Record query ID, translated SQL revision, source generation, target generation, session settings, row count, key coverage, exact controls and latency. Run the two queries close enough to avoid source drift or read immutable snapshots. If matching snapshots are unavailable, classify the comparison as inconclusive rather than using a tolerance to excuse it. [[data-engineering/cross-engine-sql-semantic-differences|Semantic fixtures]] establish the allowed normalization.'),
    ('Triage differences by cause', 'Separate missing rows, duplicate rows, numeric drift, null changes, time-bucket shifts and nondeterministic order. A count match can hide compensating missing and duplicate records; a matching total can hide two opposing errors. Drill into stable keys and inspect raw values before changing a tolerance. Keep a reproducible minimal fixture for each confirmed translation bug.'),
    ('Gate the cutover', 'Set explicit acceptance rules for critical queries: exact key coverage, exact money totals, bounded latency and no unexplained mismatch. Run shadow comparisons across multiple release intervals and corrections. Move a small consumer cohort only after the gate passes; retain an immediate path back to the old engine and record the pointer generation. [[data-engineering/migration-reconciliation-and-cutover|Cutover reconciliation]] covers pipeline state as well as query answers.'),
    ('Control shadow cost and data exposure', 'Replay under a concurrency ceiling and cost budget so validation does not overwhelm production workloads. Compare aggregates first, then rows only for flagged partitions, while still sampling detail queries. Keep shadow outputs under the same access policy as live results. Monitor both extra scan spend and latency; running every query twice forever is not an acceptable steady state.')],
    '''old_engine = {"west": {"rows": 47, "cents": 237500},
              "east": {"rows": 23, "cents": 64000}}
new_engine = {"west": {"rows": 47, "cents": 237500},
              "east": {"rows": 23, "cents": 64025}}

def compare_controls(expected, candidate):
    differences = {}
    for region in expected.keys() | candidate.keys():
        if region not in expected or region not in candidate:
            differences[region] = {"missing_side": "target" if region not in candidate else "source"}
            continue
        fields = {field: (expected[region][field], candidate[region][field])
                  for field in ("rows", "cents")
                  if expected[region][field] != candidate[region][field]}
        if fields:
            differences[region] = fields
    return differences

assert compare_controls(old_engine, new_engine) == {"east": {"cents": (64000, 64025)}}''',
    'For G matched groups, control comparison uses O(G) expected time and O(D) discrepancy space for D mismatching groups. Full keyed row comparison needs O(N) indexed state or a partitioned external join. Shadow execution can nearly double query scan cost for the sampled workload, so cap concurrency and retire the shadow path after the acceptance window.',
    ['Do not accept matching row counts as proof of matching keys.', 'Do not widen tolerances to hide unexplained money differences.', 'Do not call a comparison valid when engines read different source generations.'],
    ['data-engineering/cross-engine-sql-semantic-differences', 'data-engineering/migration-reconciliation-and-cutover', 'data-engineering/quality-quarantine-and-reconciliation', 'data-engineering/semantic-metric-contract-and-reconciliation', 'data-engineering/cross-engine-shadow-read-project'], ENGINE)

add('cross-engine-shadow-read-project', 'Project: migrate a dashboard with shadow reads',
    'Move a regional payments dashboard to a second query engine while preserving its keys, exact monetary totals and time-bucket behavior.', [
    ('Freeze the input and contract', 'Pin a source generation containing 470 payments across three regions, null customer references, a correction and events close to a UTC midnight boundary. State the dashboard grain, minor-unit money representation, permitted filters and expected report time zone. Save both engine session settings. [[data-engineering/cross-engine-sql-semantic-differences|Semantic probes]] must pass before a production-sized shadow run.'),
    ('Translate and run unseen', 'Translate the detail and aggregate queries to the target dialect. Execute them under a separate shadow identity, without displaying target answers to users. Attach source and target generation IDs to each result. Limit replay to a fixed concurrency and scan budget. Compare stable keys and exact cents totals, then measure p50 and p95 latency for the same filter shapes.'),
    ('Plant three faults', 'Make the target treat one null reference as zero, shift one event into the next local day and duplicate a corrected payment. Show that row-count-only and grand-total-only checks each miss at least one planted fault. The discrepancy report must identify affected keys, categories and query revisions. [[data-engineering/cross-engine-shadow-reads-and-discrepancy-triage|Shadow triage]] should produce a small reproducible fixture for each cause.'),
    ('Gate and canary', 'Repair the translation, replay multiple intervals and require exact key coverage and exact cents totals for critical queries. Move only one dashboard cohort to the new engine. Observe freshness and latency while the old route remains available. If one later correction diverges, roll the cohort back to the prior pointer and keep the failed candidate for diagnosis.'),
    ('Deliver evidence', 'Submit the contract, source generations, SQL revisions, semantic fixtures, mismatch reports before and after repair, spend limit, query latency and canary rollback trace. Include one unresolved scenario and mark it as blocking; a cutover gate should not silently ignore a missing interval. The final dashboard result should be reproducible from the pinned manifest and comparison inputs.')],
    '''from collections import Counter

source_payments = [("pay-47", "west", 2375), ("pay-48", "east", 6400),
                   ("pay-49", "west", -125)]
target_payments = [("pay-49", "west", -125), ("pay-47", "west", 2375),
                   ("pay-48", "east", 6400)]

def reconcile(records):
    keys = Counter(payment_id for payment_id, _, _ in records)
    totals = {}
    for payment_id, region, cents in records:
        totals[region] = totals.get(region, 0) + cents
    return keys, totals

assert reconcile(source_payments) == reconcile(target_payments)
assert reconcile(source_payments)[1] == {"west": 2250, "east": 6400}''',
    'The reference reconciliation uses O(N) expected time and O(K + G) space for N rows, K distinct payment keys and G regions. Real shadow reads add two engine scans, comparison storage and a bounded canary period. Partitioned hashes can reduce detailed comparisons, but every mismatch must be resolved against pinned row evidence before a critical dashboard is moved.',
    ['Do not expose the shadow result before its gate passes.', 'Do not accept aggregate totals without checking duplicate and missing payment keys.', 'Do not lose the old routing pointer before the canary interval ends.'],
    ['data-engineering/cross-engine-sql-semantic-differences', 'data-engineering/cross-engine-shadow-reads-and-discrepancy-triage', 'data-engineering/migration-reconciliation-and-cutover', 'data-engineering/order-event-migration-project', 'data-engineering/external-telemetry-catalog-project'], ENGINE, True)

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
                   featured=False, sort_order=7910 + index, status='published',
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
    for module_title in (CATALOG, ENGINE):
        lessons = [item['path'] for item in LESSONS if item['module'] == module_title and not item['project']]
        projects = [item['path'] for item in LESSONS if item['module'] == module_title and item['project']]
        assert len(lessons) == 2 and len(projects) == 1
        if not any(module['title'] == module_title for module in hub['data']['modules']):
            hub['data']['modules'].insert(-1, {'title': module_title,
                                               'summary': 'Verify the publication boundary, then complete the applied project.',
                                               'lessons': lessons})
        practice = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
        if projects[0] not in practice['lessons']:
            practice['lessons'].append(projects[0])
        if '<h2>' + module_title + '</h2>' not in hub['body']:
            hub['body'] += '<h2>' + module_title + '</h2>' + link_list(lessons)
            hub['body'] += '<h2>' + ('External catalog project' if module_title == CATALOG else 'Cross-engine project') + '</h2>' + link_list(projects)
        if projects[0] not in project_hub['data']['modules'][0]['lessons']:
            project_hub['data']['modules'][0]['lessons'].append(projects[0])
        if projects[0] not in project_hub['body']:
            project_hub['body'] += '<h2>' + module_title + '</h2>' + link_list(projects)
    hub['updated_at'] = project_hub['updated_at'] = now

    crosslinks = [
        ('data-engineering/partition-planning-and-skew', 'data-engineering/external-table-metadata-cache-and-refresh'),
        ('data-engineering/serving-index-and-freshness-contract', 'data-engineering/external-table-metadata-cache-and-refresh'),
        ('data-engineering/task-retries-and-atomic-partition-output', 'data-engineering/partition-registration-and-manifest-gates'),
        ('data-engineering/replay-manifest-and-audit-trail', 'data-engineering/partition-registration-and-manifest-gates'),
        ('data-engineering/lakehouse-snapshot-and-atomic-commit', 'data-engineering/external-telemetry-catalog-project'),
        ('data-engineering/compaction-retention-and-replay-horizon', 'data-engineering/external-telemetry-catalog-project'),
        ('data-engineering/semantic-metric-contract-and-reconciliation', 'data-engineering/cross-engine-sql-semantic-differences'),
        ('data-engineering/schema-compatibility-and-consumer-rollout', 'data-engineering/cross-engine-sql-semantic-differences'),
        ('data-engineering/migration-reconciliation-and-cutover', 'data-engineering/cross-engine-shadow-reads-and-discrepancy-triage'),
        ('data-engineering/quality-quarantine-and-reconciliation', 'data-engineering/cross-engine-shadow-reads-and-discrepancy-triage'),
        ('data-engineering/order-event-migration-project', 'data-engineering/cross-engine-shadow-read-project'),
        ('data-engineering/semantic-metric-contract-and-reconciliation', 'data-engineering/cross-engine-shadow-read-project'),
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
    import_path = ROOT / 'work/aitrove-data-engineering-catalog-crossengine-import-20261006.json'
    import_path.write_text(json.dumps([by_path[path] for path in sorted(changed)], ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'new_articles': len(LESSONS), 'new_projects': 2,
                      'crosslinks': len(crosslinks), 'import_rows': len(changed),
                      'import_path': str(import_path)}))


if __name__ == '__main__':
    publish()
