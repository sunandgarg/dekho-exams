"""Add original Spring Batch scope, checkpoint, and scaling lessons."""
import copy
import datetime
import html
import json
import pathlib
import re
import uuid

root = pathlib.Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def prose(value):
    escaped = html.escape(value)
    return re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',
                  lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                  escaped)


lessons = [
    dict(
        slug='batch-step-scope-late-binding',
        title='Spring Batch step scope: bind a reader to one execution',
        summary='A step-scoped reader can receive job parameters when a step starts, so concurrent launches do not share an input path held by a singleton.',
        blocks=[
            ('Bind at execution time', 'A settlement import receives its source path as a job parameter. The application context starts before any particular job execution exists, so a singleton reader cannot safely resolve that parameter at bean creation. Give the reader step scope and inject the parameter into its factory method. Spring creates the target when the step runs. The Step definition itself normally stays unscoped. [[spring/batch-job-identity|Job identity]] explains why the source version must also be represented in the identifying parameters.'),
            ('Keep paths and state separate', 'One reader instance belongs to one executing step. Do not store the current file name in a static field or mutate a shared bean before launching another job. A step-scoped proxy handles late access, but it does not make the underlying file immutable. Pin the file version before launch and verify it again on restart. [[spring/batch-input-snapshot|Input snapshots]] and [[spring/batch-source-digest-guard|digest checks]] address that separate risk.'),
            ('Test two launches', 'Launch two job instances with distinct source paths at the same time. Each should read only its own receipt references. Then fail one after a committed chunk and restart it with the same identifying input version; confirm its resumed reader still points at that source. A test that runs one job at a time cannot detect a shared mutable path.')],
        code='@Bean\n@StepScope\nFlatFileItemReader<ReceiptCsvRow> receiptReader(\n        @Value("#{jobParameters[\'inputPath\']}") String inputPath,\n        LineMapper<ReceiptCsvRow> receiptLineMapper) {\n    return new FlatFileItemReaderBuilder<ReceiptCsvRow>()\n        .name("settlementReceiptReader")\n        .resource(new FileSystemResource(inputPath))\n        .lineMapper(receiptLineMapper)\n        .saveState(true)\n        .build();\n}',
        cost='The scoped proxy adds little per-item work because target creation happens at step start. File opening and replay dominate; the input must remain available for a restart.',
        mistakes=['Do not step-scope the entire Step merely to inject a reader path.', 'Do not reuse one mutable singleton reader across simultaneous executions.', 'Do not equate a stable path string with immutable file contents.'],
        related=['spring/batch-job-identity', 'spring/batch-input-snapshot', 'spring/batch-source-digest-guard', 'spring/batch-flatfile-reader-checkpoint', 'spring/batch-job-scope-parallel-limit'],
        backlink='spring/batch-job-identity'),
    dict(
        slug='batch-job-scope-parallel-limit',
        title='Spring Batch job scope: avoid a shared bean in partition workers',
        summary='A job-scoped bean is created for one job execution, but worker threads in a partitioned or multithreaded step do not automatically carry its scope context.',
        blocks=[
            ('Choose the correct owner', 'A settlement run has one immutable exchange-rate snapshot. Job scope can expose a value to ordinary sequential steps because those steps execute within the job context. A partition worker has its own StepExecution and may run on a different thread or process. Do not inject a job-scoped object directly into code that expects every partition thread to resolve it. Pass an immutable snapshot ID through partition context and load it within the worker instead. [[spring/batch-step-scope-late-binding|Step scope]] fits values owned by each execution.'),
            ('Make the value durable', 'A job-scoped field in memory is not a restart record. Save the snapshot identity in identifying parameters or a durable manifest, then check that it still names the same data after a crash. If the value is too large for job parameters, store it externally and pass a key. [[spring/batch-input-snapshot|The input manifest]] establishes this ownership for file and query sources.'),
            ('Prove parallel isolation', 'Run two jobs concurrently and divide each into partitions. Assert that every output row names the snapshot for its own job, never a neighboring launch. Kill a worker after one partition commits and restart that job. The restarted partition should reload the recorded snapshot ID rather than whichever snapshot is currently configured in the application.')],
        code='record SettlementRun(String manifestId, String exchangeSnapshotId) {}\n\n// Persist both identifiers before launch; partition workers receive IDs,\n// not a mutable job-scoped service instance.\nExecutionContext workerInput = new ExecutionContext();\nworkerInput.putString("settlement.manifestId", run.manifestId());\nworkerInput.putString("settlement.exchangeSnapshotId", run.exchangeSnapshotId());',
        cost='Passing small identifiers costs little. Each worker may need one snapshot lookup, which should be cached by immutable ID with a bounded lifetime and included in capacity estimates.',
        mistakes=['Do not assume job scope is propagated to arbitrary partition threads.', 'Do not keep a restart-critical snapshot only in a JVM field.', 'Do not use one mutable singleton to switch snapshots between active jobs.'],
        related=['spring/batch-step-scope-late-binding', 'spring/batch-partition-range-ownership', 'spring/batch-input-snapshot', 'spring/batch-job-identity', 'spring/batch-parallel-flow-independence'],
        backlink='spring/batch-input-snapshot'),
    dict(
        slug='batch-executioncontext-key-ownership',
        title='Spring Batch ExecutionContext keys: give each stream its own checkpoint',
        summary='Readers and writers persist small restart values in an ExecutionContext; colliding keys can restore the wrong cursor or overwrite another component.',
        blocks=[
            ('Treat the context as a shared map', 'A receipt reader stores its next offset and a writer stores its last output segment. Both may update the same StepExecution context at a checkpoint. Keys such as index or position are too vague; use stable, component-specific names. Give framework ItemStream implementations distinct names as well, because they derive state keys from those names. [[spring/batch-flatfile-reader-checkpoint|The file-reader checkpoint]] depends on this state being restored to the matching reader.'),
            ('Persist only restart state', 'Keep a cursor, immutable manifest ID or small counter in the context. Do not put an entire receipt list, a live connection or a non-serializable service there. Large values increase repository writes and may exceed database column capacity. If a business audit must survive after metadata cleanup, write it to a domain table; ExecutionContext is a recovery mechanism, not an audit store. [[spring/batch-repository-assertions|Repository assertions]] can inspect what was saved after a failed run.'),
            ('Test a collision deliberately', 'Configure two readers in one step with different names, stop after a chunk, and verify both offsets are present under distinct keys. Restart and assert no duplicated or missing source reference. A green first execution says little about restore behavior. Change a component name only with a migration or an intentional new job identity, because old checkpoint keys may no longer match.')],
        code='final class ReceiptCursor implements ItemStream {\n    private long nextOffset;\n\n    @Override public void update(ExecutionContext state) {\n        state.putLong("receiptCursor.nextOffset", nextOffset);\n    }\n\n    @Override public void open(ExecutionContext state) {\n        nextOffset = state.getLong("receiptCursor.nextOffset", 0L);\n    }\n\n    @Override public void close() {}\n}',
        cost='A few primitive values are cheap to serialize. Context growth adds database I/O at checkpoints and can make recovery slower than replaying the source.',
        mistakes=['Do not give two ItemStreams the same state name in one step.', 'Do not store large row collections or live resources in ExecutionContext.', 'Do not rename checkpoint keys without planning what existing failed jobs will restore.'],
        related=['spring/batch-flatfile-reader-checkpoint', 'spring/batch-repository-assertions', 'spring/batch-chunk-restart', 'spring/batch-partition-restart-shape', 'spring/batch-durable-restart-check'],
        backlink='spring/batch-repository-assertions'),
    dict(
        slug='batch-flatfile-reader-checkpoint',
        title='Spring Batch FlatFileItemReader: save state against an immutable source',
        summary='A restartable file reader records position at committed checkpoints; that position is valid only while the source bytes and reader mapping stay compatible.',
        blocks=[
            ('Know what the cursor proves', 'A settlement CSV reader may have consumed 47 records when a later write fails. The last committed chunk, not the last attempted read, defines safe restart progress. A named FlatFileItemReader can save its current item count in the StepExecution context and restore it on a new execution. That cursor does not certify the file contents. [[spring/batch-source-digest-guard|The source digest guard]] must reject replacement bytes under the same input identity.'),
            ('Keep checkpoint and output aligned', 'Let the chunk transaction commit destination writes and repository state together where the infrastructure supports that boundary. A remote file or external API cannot join the database transaction; its writer needs idempotent keys so replay is safe. Turning off saveState can be reasonable for a one-shot disposable import, but it removes position-based restart. [[spring/batch-idempotent-writer|Idempotent writes]] remain useful even with a saved cursor because failures can occur between systems.'),
            ('Exercise a real restart', 'Process a small immutable fixture, inject a failure during the second chunk, then terminate the process. Relaunch the same job instance with the same source version and inspect persisted StepExecution state. Compare the complete destination key set with the source: no gap, duplicate or silent skip. Test a changed file separately and require rejection before the reader resumes.')],
        code='@Bean\n@StepScope\nFlatFileItemReader<ReceiptCsvRow> settlementReader(\n        @Value("#{jobParameters[\'inputPath\']}") String inputPath,\n        LineMapper<ReceiptCsvRow> receiptLineMapper) {\n    return new FlatFileItemReaderBuilder<ReceiptCsvRow>()\n        .name("settlementCsvReader")\n        .resource(new FileSystemResource(inputPath))\n        .lineMapper(receiptLineMapper)\n        .saveState(true)\n        .build();\n}',
        cost='Persisting a small cursor adds a repository update at checkpoints. A larger chunk reduces update frequency but increases work replayed after a failure and memory held before commit.',
        mistakes=['Do not restart from a line number in a replaced file.', 'Do not set saveState(false) while promising position-based restart.', 'Do not assume a saved cursor makes a non-idempotent external writer safe.'],
        related=['spring/batch-step-scope-late-binding', 'spring/batch-source-digest-guard', 'spring/batch-idempotent-writer', 'spring/batch-chunk-restart', 'spring/batch-executioncontext-key-ownership'],
        backlink='spring/batch-chunk-restart'),
    dict(
        slug='batch-partition-range-ownership',
        title='Spring Batch partitioner: assign disjoint receipt ranges',
        summary='A partitioner assigns stable, named input ranges to worker StepExecutions; correctness starts with full coverage and no overlap.',
        blocks=[
            ('Use half-open boundaries', 'A 47-row immutable manifest can be divided into four ranges: [0,12), [12,24), [24,36) and [36,47). Each worker owns its lower bound and excludes its upper bound. That convention avoids a duplicate row at a boundary and is easy to verify mechanically. The partitioner returns a distinct ExecutionContext for each named range; [[spring/batch-step-scope-late-binding|step-scoped components]] can bind to those values when a worker starts.'),
            ('Name the work, not the thread', 'Give each partition a name derived from its immutable range or shard identity. Do not use a thread index, since scheduling order is not a business identity. A database query must filter by the exact partition predicate and a stable ordering key. If new rows can appear during the run, first freeze a source snapshot; otherwise a range calculated from changing row positions will miss or repeat work. [[spring/batch-input-snapshot|Input snapshotting]] remains the first step.'),
            ('Prove the partition set', 'Before launching workers, compare the union of assigned IDs with the manifest and assert every ID occurs once. After a forced partition failure, compare the destination set again. This is more useful than asserting only that the manager step completed: a manager can succeed while the partitioner silently omitted a range if the test input never exercises its edge.')],
        code='int receiptCount = 47;\nint targetPartitions = 4;\nint width = (receiptCount + targetPartitions - 1) / targetPartitions;\nMap<String, ExecutionContext> ranges = new LinkedHashMap<>();\nfor (int start = 0; start < receiptCount; start += width) {\n    int endExclusive = Math.min(receiptCount, start + width);\n    ExecutionContext input = new ExecutionContext();\n    input.putInt("receipt.startInclusive", start);\n    input.putInt("receipt.endExclusive", endExclusive);\n    ranges.put("receiptRange-" + start, input);\n}',
        cost='Partitioning adds worker setup and repository rows. It pays only when independent work exceeds coordination cost; database pool size and destination contention often cap throughput first.',
        mistakes=['Do not use inclusive upper bounds in adjacent ranges without adjusting the next lower bound.', 'Do not derive partition identity from the executing thread number.', 'Do not partition an unfrozen query result by row position.'],
        related=['spring/batch-partition-restart-shape', 'spring/batch-input-snapshot', 'spring/batch-step-scope-late-binding', 'spring/batch-idempotent-writer', 'spring/batch-job-scope-parallel-limit'],
        backlink='spring/batch-input-snapshot'),
    dict(
        slug='batch-partition-restart-shape',
        title='Spring Batch partition restart: preserve worker names and input slices',
        summary='A failed partition should resume its recorded slice; changing the grid hint or source boundaries during restart can create a different workload.',
        blocks=[
            ('The repository records worker executions', 'A partition manager creates named worker StepExecutions with their input contexts. On restart, a splitter can reconstitute failed work from those records rather than recompute an arbitrary new distribution. Treat the original partition names, bounds and manifest version as part of the recovery contract. [[spring/batch-partition-range-ownership|Range ownership]] defines what each worker may write.'),
            ('A grid is capacity, not identity', 'The requested grid size is a hint for the initial division, and a restart may use the saved partition set. Do not assume changing it from four to seven repartitions an interrupted job safely. If a deployment requires a new split, launch a new job instance against an explicitly versioned source after reconciling committed output. Keep destination writes keyed by manifest and receipt reference, so a repeated partition cannot duplicate side effects. [[spring/batch-idempotent-writer|Writer idempotency]] is the second layer of protection.'),
            ('Run the hard-stop case', 'Kill the worker process after one partition commits while another has not. Inspect the repository for each partition name, status and context. Restart with the same job identity and verify only incomplete slices run; assert the final destination set equals the source once. A unit test of partitioner arithmetic is necessary but cannot prove repository-driven restart.')],
        code='for (Map.Entry<String, ExecutionContext> partition : persistedRanges.entrySet()) {\n    String partitionName = partition.getKey();\n    int start = partition.getValue().getInt("receipt.startInclusive");\n    int end = partition.getValue().getInt("receipt.endExclusive");\n    assertThat(partitionName).startsWith("receiptRange-");\n    assertThat(start).isLessThan(end);\n}',
        cost='Persisted partition metadata costs rows and coordination. Recovery can save substantial replay, but operational checks must track each worker rather than just the manager status.',
        mistakes=['Do not treat a new grid size as permission to redistribute an incomplete job.', 'Do not delete failed worker metadata before reconciliation.', 'Do not count manager completion as proof of every expected receipt key.'],
        related=['spring/batch-partition-range-ownership', 'spring/batch-repository-assertions', 'spring/batch-killed-worker-recovery', 'spring/batch-idempotent-writer', 'spring/batch-executioncontext-key-ownership'],
        backlink='spring/batch-killed-worker-recovery'),
    dict(
        slug='batch-multithread-processor-transaction',
        title='Spring Batch multithreaded step: keep processor work independent of the chunk transaction',
        summary='Concurrent item processing changes thread ownership; a processor should not assume the step transaction is active on its worker thread.',
        blocks=[
            ('Separate computation from effects', 'A settlement processor normalizes receipt references and computes minor-unit totals. In a multithreaded step, several processor calls may run at once. Keep that code stateless and pure so ordering and thread identity do not affect the output. Spring transactions are thread-bound; work moved to a processor thread should not rely on the main chunk transaction. A database write from that worker can commit independently and survive a later chunk rollback. [[spring/batch-committed-chunk|Committed chunk boundaries]] explain the recovery consequence.'),
            ('Bound the parallelism', 'Measure the serial reader, processor and writer separately before increasing threads. A slow shared reader or writer can leave processors idle, while a database pool smaller than the requested concurrency can turn parallelism into connection waits. Size the executor, connection pool and downstream admission together. [[spring/bounded-executor-rejection|Bounded executor rejection]] matters if a scheduler launches many jobs at once.'),
            ('Verify repeatability', 'Run the same immutable source with one worker and then with several. Compare output by stable receipt key rather than row order. Inject an exception in one processor and assert no separately committed business effect remains from that item. If the processor must call a remote service, move it to an explicit, replay-safe stage with an idempotency key rather than hiding it inside a pure mapping step.')],
        code='final class NormalizeReceipt implements ItemProcessor<RawReceipt, NormalizedReceipt> {\n    @Override public NormalizedReceipt process(RawReceipt receipt) {\n        String reference = receipt.reference().strip();\n        long amountMinor = Math.multiplyExact(receipt.unitPriceMinor(), receipt.units());\n        return new NormalizedReceipt(reference, amountMinor);\n    }\n}',
        cost='Parallel processors help only when processor CPU or latency dominates. More threads consume memory and connections; the serial reader and writer can remain the throughput limit.',
        mistakes=['Do not put mutable counters in an unsynchronized shared processor.', 'Do not assume a worker thread inherits the chunk transaction.', 'Do not add threads before measuring reader and writer throughput.'],
        related=['spring/batch-committed-chunk', 'spring/batch-partition-range-ownership', 'spring/bounded-executor-rejection', 'spring/batch-parallel-flow-independence', 'spring/transaction-thread-boundary'],
        backlink='spring/batch-committed-chunk'),
    dict(
        slug='batch-parallel-flow-independence',
        title='Spring Batch parallel flows: make dependency order explicit',
        summary='A split flow may run independent steps together; a step that reads another branch’s unfinished output needs an explicit join and durable handoff.',
        blocks=[
            ('Parallel is not ordered', 'A settlement job can import receipts while another branch loads an immutable exchange-rate snapshot. A split flow schedules both branches, but it does not make either branch finish before the other reads shared state. Put reconciliation after the split joins, and make the input artifacts durable. If one branch fails, inspect the overall job status and both StepExecutions before deciding whether to restart. [[spring/batch-flow-exitstatus-restart|Flow status]] can differ from the status of one step.'),
            ('Design for partial completion', 'One branch may commit all its chunks while the other fails. Restart should reuse the completed branch only when its output still matches the same manifest and job parameters. Otherwise fail for reconciliation or create a new job instance. Do not make one branch truncate a shared table that the other branch is reading. [[spring/batch-input-snapshot|Pinned input]] and [[spring/batch-idempotent-writer|idempotent writes]] allow replay without guessing.'),
            ('Test adverse scheduling', 'Delay the receipt branch after its first chunk while the rate branch completes, then reverse their relative timing. Reconciliation must not start until both have reached the required terminal state. Assert the final result by business key, not by log order. A second test should fail one branch and verify that the committed output of the other is visible for operator review, not silently discarded.')],
        code='Flow parallelInputs = new FlowBuilder<SimpleFlow>("settlementInputs")\n    .split(settlementTaskExecutor)\n    .add(receiptImportFlow, exchangeSnapshotFlow)\n    .build();\n// Configure reconciliation after parallelInputs has joined both branches.',
        cost='Parallel flows shorten wall time when branches are independent and resources are available. They also increase peak database and I/O demand and complicate partial-failure review.',
        mistakes=['Do not read another branch’s output before the split has joined.', 'Do not assume a failed branch rolls back work already committed by its sibling.', 'Do not treat log ordering as an execution dependency.'],
        related=['spring/batch-flow-exitstatus-restart', 'spring/batch-committed-chunk', 'spring/batch-idempotent-writer', 'spring/batch-job-scope-parallel-limit', 'spring/batch-input-snapshot'],
        backlink='spring/batch-committed-chunk'),
    dict(
        slug='batch-flow-exitstatus-restart',
        title='Spring Batch flow status: distinguish step failure from job restartability',
        summary='A step ExitStatus drives transition matching, while the job BatchStatus determines whether the same instance can be restarted.',
        blocks=[
            ('Read both levels', 'A reconciliation step can report a review-required exit code while the job reaches a configured terminal state. ExitStatus describes the outcome used by flow transitions; BatchStatus records lifecycle state such as COMPLETED, FAILED or STOPPED. A transition that ends the job as COMPLETED makes that job instance non-restartable, even if a preceding step failed. Use a failing or stopped transition when an operator must correct data and resume the same instance. [[spring/batch-running-execution-recovery|Running execution recovery]] is a separate case after abrupt process death.'),
            ('Define the operational contract', 'For settlement imports, treat rejected business rows differently from unavailable infrastructure. A small accepted rejection count might finish as COMPLETED with a review flag in a durable summary. A database outage should leave a FAILED job eligible for restart after repair. Record exact counts and keys in business tables, not only a custom exit string, because repository metadata may later be archived. [[spring/batch-skip-quarantine|Rejected-row quarantine]] covers the durable review path.'),
            ('Assert the next launch', 'Build tests for each transition: normal completion, review-required completion, failure and deliberate stop. Inspect both the job and step statuses, then actually relaunch with the same identifying parameters. The expected behavior should be explicit: completed instances reject a duplicate launch, while failed or stopped instances follow their configured restart path. A single status assertion cannot prove restartability.')],
        code='JobExecution execution = jobLauncher.run(settlementJob, identifyingParameters);\nBatchStatus lifecycle = execution.getStatus();\nString outcome = execution.getExitStatus().getExitCode();\nassertThat(lifecycle).isEqualTo(BatchStatus.FAILED);\nassertThat(outcome).isEqualTo("FAILED");\n// Relaunch the same identifying parameters only after the failure is repaired.',
        cost='Flow transitions add no meaningful item-processing cost, but incorrect terminal status can force a new instance and manual reconciliation of already committed output.',
        mistakes=['Do not mark a recoverable failure COMPLETED merely to suppress an alert.', 'Do not infer job restartability from one step’s ExitStatus.', 'Do not change identifying parameters to bypass a failed execution without reconciling writes.'],
        related=['spring/batch-running-execution-recovery', 'spring/batch-job-identity', 'spring/batch-skip-quarantine', 'spring/batch-parallel-flow-independence', 'spring/batch-durable-restart-check'],
        backlink='spring/batch-running-execution-recovery'),
]

titles = {path: row['title'] for path, row in by_path.items()}
titles.update({'spring/' + lesson['slug']: lesson['title'] for lesson in lessons})
for number, lesson in enumerate(lessons):
    path = 'spring/' + lesson['slug']
    assert path not in by_path, path
    for target in lesson['related']:
        assert target in titles, (path, target)
    body = '<p>' + prose(lesson['summary']) + '</p>'
    for heading, content in lesson['blocks']:
        body += '<h2>' + html.escape(heading) + '</h2><p>' + prose(content) + '</p>'
    body += '<h2>Implementation contract</h2><pre><code class="language-java">' + html.escape(lesson['code'], quote=False) + '</code></pre>'
    body += '<h2>Cost and verification</h2><p>' + prose(lesson['cost']) + '</p>'
    body += '<h3>Common Mistakes</h3><ul>' + ''.join('<li>' + prose(mistake) + '</li>' for mistake in lesson['mistakes']) + '</ul>'
    body += '<h2>Read next</h2><p>' + ', '.join('<a href="/' + target + '">' + html.escape(titles[target]) + '</a>' for target in lesson['related']) + '.</p>'
    row = copy.deepcopy(by_path['spring/component-scan-vs-bean'])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://aitrove.in/' + path)), path=path, title=lesson['title'], summary=lesson['summary'], body=body, subject='spring-production', tags=['spring', 'spring-batch', lesson['slug']], sort_order=6600 + number, published_at=stamp, created_at=stamp, updated_at=stamp)
    row['data'] = {'subject_root': 'spring/spring-boot', 'section_path': 'spring/production', 'kind': 'tutorial', 'content_format': 'html', 'seo_ready': True, 'reading_minutes': max(4, round(len(re.sub(r'<[^>]+>', ' ', body).split()) / 150)), 'author_path': 'authors/aitrove-editorial', 'framework_version': 'Spring Batch 6 / Spring Boot 4 where relevant', 'java_version': '21 or later', 'verification_suite': 'Spring Batch API contract review; snippets require an application-specific model', 'related': [{'path': target, 'title': titles[target]} for target in lesson['related']]}
    rows.append(row)
    by_path[path] = row

new_paths = ['spring/' + lesson['slug'] for lesson in lessons]
hub = by_path['spring/production']
hub['data']['modules'].append({'title': 'Batch scope, checkpoint and scaling contracts', 'summary': 'Step binding, state keys, file checkpoints, partition ranges, concurrent processing and flow status.', 'lessons': new_paths})
hub['body'] += '<h2>Batch scope, checkpoint and scaling contracts</h2><ul>' + ''.join('<li><a href="/' + path + '">' + html.escape(titles[path]) + '</a></li>' for path in new_paths) + '</ul>'
hub['updated_at'] = stamp
parent = by_path['spring/spring-boot']
parent['body'] += '<h2>Batch execution boundaries</h2><p><a href="/spring/production">Production</a> now includes <a href="/spring/batch-step-scope-late-binding">step-scoped readers</a>, <a href="/spring/batch-partition-range-ownership">partition ownership</a> and <a href="/spring/batch-flow-exitstatus-restart">flow restart status</a>.</p>'
parent['updated_at'] = stamp
for lesson in lessons:
    target = 'spring/' + lesson['slug']
    entry = by_path[lesson['backlink']]
    entry['body'] += '<h2>Related Batch contract</h2><p><a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    entry['updated_at'] = stamp
for source, target in [
    ('spring/batch-input-snapshot', 'spring/batch-step-scope-late-binding'),
    ('spring/batch-job-identity', 'spring/batch-job-scope-parallel-limit'),
    ('spring/batch-chunk-restart', 'spring/batch-executioncontext-key-ownership'),
    ('spring/batch-source-digest-guard', 'spring/batch-flatfile-reader-checkpoint'),
    ('spring/batch-killed-worker-recovery', 'spring/batch-partition-range-ownership'),
    ('spring/batch-repository-assertions', 'spring/batch-partition-restart-shape'),
    ('spring/transaction-thread-boundary', 'spring/batch-multithread-processor-transaction'),
    ('spring/batch-idempotent-writer', 'spring/batch-parallel-flow-independence'),
    ('spring/batch-durable-restart-check', 'spring/batch-flow-exitstatus-restart'),
]:
    entry = by_path[source]
    entry['body'] += '<h2>Related Batch contract</h2><p><a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    entry['updated_at'] = stamp

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(f'Added {len(lessons)} Spring Batch lessons; {len(rows)} total fixture records')
