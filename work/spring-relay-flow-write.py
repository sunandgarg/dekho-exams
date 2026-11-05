"""Add original, source-kit-backed Spring relay lessons and checked curriculum links."""
from __future__ import annotations
import datetime, html, json, pathlib, re, uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILE = ROOT / 'src/data/fixtures.json'
rows = json.loads(FILE.read_text())
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
specs = []

def add(subject, slug, title, opening, sections, code, limits, mistakes, links):
    specs.append(dict(subject=subject, path='spring/' + slug, title=title,
        opening=opening, sections=sections, code=code, limits=limits,
        mistakes=mistakes, links=links))

add('spring-data', 'outbox-relay-state-machine', 'Spring outbox relay: claim, deliver, and acknowledge one event',
'An outbox relay moves a committed event through pending, claimed, and delivered states without folding a remote side effect into the producer transaction.', [
('The checked sequence', [
'The fixture commits a shipment request and one outbox event together. A worker then claims the event with a token and lease, calls a separate consumer transaction, and acknowledges the event. The stock balance changes from 10 to 7 once. The delivered row cannot be claimed again. This sequence is invoked by a test, not a running background service.',
'[[spring/outbox-atomic-write|The producer write]] proves one local transaction. [[spring/outbox-claim-lease|The claim]] prevents a second sequential worker from taking an unexpired lease. [[spring/consumer-idempotency|The consumer ledger]] handles a repeat delivery. None of those steps makes a network publish atomic with a database commit.']),
('State transitions have owners', [
'PENDING is durable work waiting for a poller. DELIVERED means this model received a successful consumer result and completed a token-checked acknowledgement; it is not proof that an external broker persisted an event. A crash after consumer commit but before acknowledgement leaves PENDING work for another claim. The consumer must accept the same event ID without repeating the business mutation.',
'Keep the outbox row long enough for support and audit, then define retention separately. An index on status, next_attempt_at, and lease_until would matter at scale; this tiny H2 fixture does not measure a polling query plan.'])],
'''accept("EVENT-21", "SKU-17", 3, false);
claim("EVENT-21", "worker-A", 100, 50);
consume("EVENT-21");
acknowledge("EVENT-21", "worker-A", 110);''',
'The JUnit test calls each stage in one process with a logical clock. It has no broker, scheduler thread, crash injector, or cross-node clock agreement. Delivery semantics across a real network need a separate integration test.',
['Do not mark an event delivered before checking the downstream result.', 'Do not treat an outbox insert as a completed publish.', 'Do not delete pending rows because a worker process restarted.'],
['spring/outbox-atomic-write','spring/outbox-claim-lease','spring/consumer-idempotency','spring/relay-failure-trace'])

add('spring-data', 'outbox-claim-lease', 'Spring outbox claims: lease expiry and token-fenced acknowledgement',
'An outbox claim grants one worker a bounded chance to process an event; the claim token identifies the worker allowed to acknowledge it.', [
('Reject the stale worker', [
'The H2 update takes a PENDING row only when it is due and its current lease is absent or expired. Worker A claims at logical time 100 until 120. At 120 its acknowledgement fails; worker B reclaims the row. A second acknowledgement from A still fails because the token no longer matches. B can acknowledge before its own lease expires.',
'One conditional UPDATE makes the state check and mutation a single database statement. [[spring/outbox-expiring-lease|The earlier lease fixture]] covers a smaller claim boundary. The relay test adds the due-time predicate and requires an unexpired lease for acknowledgement.']),
('Where fencing stops', [
'The token fences only this outbox row. If A publishes to a broker just before or after its lease expires, the database cannot undo that publish. A downstream [[spring/consumer-idempotency|event-ID ledger]] still has to reject a repeat. The fixture runs sequentially: H2 behavior here says nothing about lock contention, SKIP LOCKED, isolation levels, or throughput on the target database.',
'Lease length must exceed normal processing time or support renewal with a checked owner token. An unbounded lease can strand work; a very short lease causes avoidable duplicates. Measure actual processing latency and recovery goals before choosing it.'])],
'''update delivery_outbox set claim_token = ?, lease_until = ?
where event_id = ? and status = 'PENDING' and next_attempt_at <= ?
  and (claim_token is null or lease_until <= ?);''',
'Logical timestamps make the test deterministic. The model does not account for clock skew across machines or an external publish that finishes after the lease expires.',
['Do not acknowledge using only the event ID.', 'Do not count a lease as a distributed lock on external systems.', 'Do not infer concurrent claim safety from sequential H2 tests.'],
['spring/outbox-relay-state-machine','spring/consumer-idempotency','spring/outbox-expiring-lease','spring/relay-retry-schedule'])

add('spring-production', 'relay-retry-schedule', 'Spring outbox retries: due time, delay cap, and attempt accounting',
'A retry schedule stores when a failed event may be claimed again instead of immediately repeating a failed operation.', [
('Schedule after a failed attempt', [
'The local model starts with zero failures and due time zero. A failed claimed attempt increments failures, clears its claim, and sets next_attempt_at to the logical failure time plus 10 units. The second failure waits 20 units. A third would wait no more than 40. The test proves that a claim one unit before each due time fails and a claim at the due time succeeds.',
'This is a bounded deterministic policy, not a recommendation to use 10 milliseconds or seconds in production. The fixture uses abstract time units. A real worker needs a retry classification, randomized jitter for shared outages, an elapsed-time budget, and metrics for age and attempt count. [[spring/relay-dead-letter|The dead state]] handles exhausted work.']),
('Retries can repeat success', [
'A network timeout does not prove that the consumer rejected the request. The consumer may have committed and lost its response. Retrying the same stable event ID is safer than generating a replacement ID, provided the [[spring/consumer-idempotency|consumer ledger]] and business mutation commit together. Do not hold the producer transaction open while waiting for a retry.',
'The test calls fail directly. It does not classify HTTP status, broker acknowledgement, connection reset, or permanent schema rejection. Those belong to the actual transport adapter and have separate operational costs.'])],
'''update delivery_outbox set failures = failures + 1,
    next_attempt_at = ? + case when failures = 0 then 10
        when failures = 1 then 20 else 40 end
where event_id = ? and claim_token = ?;''',
'The schedule is checked with one event and a logical clock. No timer, queue, jitter, outage storm, or real latency distribution is measured.',
['Do not retry immediately in a tight loop.', 'Do not issue a new event ID for the same delivery attempt.', 'Do not call every failure transient.'],
['spring/outbox-relay-state-machine','spring/relay-dead-letter','spring/consumer-idempotency','spring/outbox-claim-lease'])

add('spring-production', 'relay-dead-letter', 'Spring outbox retry budget: park a poison event for inspection',
'A retry budget moves repeatedly failed work into a state that automatic claims will no longer select.', [
('Stop at the boundary', [
'The fixture uses a three-failure budget. Each claimed attempt fails with its current token. On the third failure, the row becomes DEAD; a later claim fails even after its due time. The stock balance remains unchanged because the consumer was never called. The row stays available for an operator to inspect rather than disappearing.',
'DEAD is only a local state in the model. It is not a configured broker dead-letter topic. A production operator workflow should expose the event ID, safe error category, attempt history, age, and a controlled replay action. Do not put raw credentials or personal payloads in those diagnostics.']),
('Replay needs a rule', [
'If a schema bug caused the failures, a code fix may make replay safe; if the consumer partially applied a side effect, replay requires [[spring/consumer-idempotency|a stable deduplication key]]. Decide whether the original event ID remains stable and whether the attempt counter resets. Record who released the event and why.',
'A single global attempt count may treat a brief outage like a poison payload. Pair attempts with a total elapsed budget and error classification when the actual transport exists. [[spring/relay-retry-schedule|The retry lesson]] states what this local clock check covers.'])],
'''status = nextFailureCount >= 3 ? "DEAD" : "PENDING";
// The claim query selects only PENDING rows.''',
'The test checks one row and three sequential failures. It does not provide a dead-letter queue, retention policy, alerting, manual replay API, or broker failure classification.',
['Do not silently discard exhausted events.', 'Do not auto-replay a parked event with a new identity.', 'Do not leak sensitive payloads into error dashboards.'],
['spring/relay-retry-schedule','spring/consumer-idempotency','spring/relay-failure-trace','spring/receipt-outbox-command'])

add('spring-data', 'consumer-idempotency', 'Spring consumer idempotency: reserve an event ID with the stock mutation',
'A consumer event ledger uses a unique event ID to reject a repeated delivery before it repeats a business mutation.', [
('One transaction covers both writes', [
'The consumer inserts EVENT-23 into applied_event and subtracts two units from SKU-17 inside one TransactionTemplate callback. The first call changes stock from 10 to 8; the second insert violates the event-ID primary key and the method reports a duplicate without another stock change. The constraint, not a preflight SELECT, decides the race.',
'If the stock item does not exist, the callback throws and rolls back the event reservation. The test then creates the item and retries the same event successfully. A reservation committed before the business mutation would instead suppress a valid retry. [[spring/transaction-propagation|Transaction boundaries]] matter more than a boolean already-seen check.']),
('Idempotent result has a scope', [
'This model makes the database mutation idempotent for one event ID in one datasource. It does not make an email, webhook, or file write automatically idempotent. The ledger key must be stable across retries and unique in the relevant tenant or source namespace. Retention cannot expire the key while the producer may still redeliver the event.',
'The test uses H2 and sequential calls. On a target database, test two concurrent consumers inserting the same key, transaction isolation, statement timeout, and rollback visibility. [[spring/outbox-claim-lease|A relay lease]] reduces duplicate work; the consumer constraint handles duplicates that still reach it.'])],
'''transactions.executeWithoutResult(status -> {
    jdbc.update("insert into applied_event values (?)", eventId);
    int changed = jdbc.update("update stock_balance set available = available - ? where sku = ?", units, sku);
    if (changed != 1) throw new IllegalStateException("unknown stock item");
});''',
'The excerpt shortens the checked fixture, which reads units and SKU from the outbox. No external broker, tenant registry, stock floor constraint, or concurrent consumer race is included.',
['Do not check existence then insert without a unique constraint.', 'Do not commit the event marker before the business change.', 'Do not use a fresh event ID on a redelivery.'],
['spring/outbox-relay-state-machine','spring/outbox-claim-lease','spring/transaction-propagation','java/database-isolation'])

add('spring-data', 'relay-transaction-boundaries', 'Spring outbox transaction boundaries: where atomicity ends',
'The producer transaction and consumer transaction are separate commits with a delivery gap between them.', [
('Producer rollback', [
'The producer fixture inserts a shipment request and an event row in one TransactionTemplate callback. An injected runtime failure after both inserts leaves neither row. A successful call leaves one of each. That is local database atomicity, not a guarantee that another service received the event. [[spring/outbox-atomic-write|The earlier outbox lesson]] covers the same principle from the command side.',
'The relay later claims the row, calls the consumer, and acknowledges it. Those steps must not be wrapped in one long transaction across a remote wait. The consumer commits its own event marker and stock mutation together. A crash between that commit and relay acknowledgement means delivery may repeat; [[spring/consumer-idempotency|the marker]] is the recovery boundary.']),
('Handle failure evidence', [
'An exception from a JDBC statement should leave an observable rolled-back row count in the test. A timeout from a remote call is weaker evidence: it may mean the response was lost after commit. The local kit tests producer rollback and consumer rollback with H2; it does not simulate a process kill, network partition, broker offset or two databases.',
'Spring rollback behavior depends on the transaction manager and exception type. The fixture uses unchecked exceptions with a JDBC transaction manager. If an application uses checked exceptions or catches a failure inside a callback, specify the rollback rule and assert persisted state.'])],
'''transactions.executeWithoutResult(status -> {
    jdbc.update("insert into shipment_request values (?)", requestId);
    jdbc.update("insert into delivery_outbox values (?, ?, ?, 'PENDING', null, null, 0, 0)", eventId, sku, units);
});''',
'One H2 datasource and sequential JUnit calls are checked. There is no distributed transaction, durable broker, real process restart, or target-database isolation test.',
['Do not publish remotely inside a local transaction and assume rollback will retract it.', 'Do not swallow a database failure and assume rollback still happens.', 'Do not mark the producer commit as delivery completion.'],
['spring/outbox-atomic-write','spring/consumer-idempotency','spring/checked-exception-rollback','spring/relay-failure-trace'])

add('spring-testing', 'relay-failure-trace', 'Spring relay failure trace: inspect persisted state at each cut point',
'A delivery trace tests the state left behind at producer failure, retry, lease expiry, duplicate delivery, and consumer failure.', [
('Read the row, not the exception alone', [
'OutboxRelayFlowTest has seven deterministic checks. Producer rollback leaves zero request and outbox rows. A successful delivery leaves stock at 7 and the outbox row DELIVERED. A duplicate event changes stock only once. An unknown SKU rolls back the applied_event insert. Retry attempts remain unclaimable until due, and a third failure moves the row to DEAD.',
'At lease expiry, the old worker cannot acknowledge. A replacement token can. These assertions tie each branch to persisted state, which is more useful than testing only that a callback threw. [[spring/outbox-claim-lease|The lease]], [[spring/relay-retry-schedule|retry]], and [[spring/consumer-idempotency|consumer]] lessons explain the separate invariants.']),
('Name the missing cut points', [
'The test does not kill a process after a broker confirms publication but before the outbox acknowledgement. It also does not run two workers concurrently against the target database, start a scheduler, inject transport timeouts, or verify duplicate delivery after restart. Those checks need a real broker and database in a separate integration environment.',
'The logical clock prevents flaky sleeps and makes due times exact. It cannot reveal scheduler lag, clock skew between hosts, or throughput under load. Keep those claims out of a local unit-scale report.'])],
'''mvn -q -Dtest=OutboxRelayFlowTest test
# Run the full source-kit suite before publishing an updated ZIP.''',
'The suite is reproducible locally with H2 and Spring JDBC. It cannot certify delivery behavior of a deployed queue, load balancer, or database cluster.',
['Do not report a local state-machine test as an end-to-end broker test.', 'Do not omit row-state assertions after a simulated failure.', 'Do not use wall-clock sleeps for exact retry boundaries.'],
['spring/outbox-relay-state-machine','spring/relay-retry-schedule','spring/consumer-idempotency','spring/testing-boundaries'])

add('spring-exercises', 'relay-cut-point-exercise', 'Spring exercise: predict outbox state across a lost acknowledgement',
'A lost acknowledgement exercise asks which rows change when the consumer commits but the relay cannot mark the outbox delivered.', [
('Run the sequence', [
'Accept EVENT-31 for two units of SKU-17. Let worker A claim it and call the consumer successfully. Stock moves from 10 to 8, and applied_event contains EVENT-31. Stop before acknowledgement. At the lease expiry, worker B reclaims the PENDING row and calls the consumer with the same event ID. Predict the second stock balance, applied_event count, and whether B may acknowledge.',
'The answer is 8, one, and yes if B still owns an unexpired claim. The second consumer call hits the unique event-ID key and skips the stock update. Worker A must not acknowledge after B has taken the claim. [[spring/consumer-idempotency|The event ledger]] and [[spring/outbox-claim-lease|fencing token]] protect different rows.']),
('Change one assumption', [
'Remove the applied_event unique key. The second call may subtract stock again. Move the applied_event insert into a separate committed transaction before the stock mutation. A business failure can then make a later valid retry look like a duplicate. Predict the final rows before running the checked tests.',
'Extend the kit with a test for a failed external publish after claim, then state what cannot be proved without a broker. A passing H2 test is evidence for local SQL state transitions only.'])],
'''mvn -q -Dtest=OutboxRelayFlowTest test''',
'This is a self-check backed by an in-process source kit, not a hosted judge. The lost-acknowledgement scenario is reasoned from separately checked claims and duplicate calls; no process is actually killed.',
['Do not change the event ID when replaying the same event.', 'Do not assume a failed acknowledgement means the consumer rolled back.', 'Do not equate a passed local exercise with target-system recovery.'],
['spring/relay-failure-trace','spring/consumer-idempotency','spring/outbox-claim-lease','spring/relay-transaction-boundaries'])

add('spring-projects', 'outbox-relay-service-project', 'Spring project: turn the local outbox model into a measured relay',
'A production relay must connect durable claim state to an actual transport, consumer, observability, and recovery policy.', [
('Build in testable slices', [
'Start from [[spring/outbox-relay-state-machine|the checked local state machine]]. Put the producer request and outbox insert in one database transaction. Add a poller that selects due rows in bounded batches, conditional claims with tokens and lease renewal, and a transport adapter that publishes a stable event ID. Acknowledge only after the transport contract says the message is accepted. On uncertain results, retry with the same identity.',
'At the consumer, commit a unique applied-event key with the business mutation. Set a retry budget, a parked-event review path, and metrics for pending age, repeated delivery, dead rows and oldest unacknowledged event. Define tenant scope, payload version and schema migration before creating a second producer.']),
('Prove the missing boundary', [
'Run two workers against the target database and observe one claim winner. Kill a worker after the consumer commits but before acknowledgement; verify a later retry changes stock once. Inject transport timeout, slow consumer, expired lease, malformed payload and storage outage. Record the final row state after each cut point. Measure polling query plans and backlog drain rate with realistic row counts.',
'The current kit does none of those deployed checks. Its H2 tests provide a starting contract, not a deployable service. [[spring/relay-failure-trace|The trace]] lists checked behavior; [[spring/relay-dead-letter|the dead-state lesson]] describes the operational decision still needed.'])],
'''mvn -q test
# Replace the local direct consumer call with a real transport adapter and integration tests.''',
'No broker, scheduler, deployment manifest, external database, replay console, or production alert is shipped with this exercise. Those are required before describing the relay as operational.',
['Do not publish directly from the request path and call it an outbox relay.', 'Do not claim exactly-once transport delivery from a consumer ledger.', 'Do not launch without a way to inspect and replay parked work.'],
['spring/outbox-relay-state-machine','spring/relay-failure-trace','spring/relay-dead-letter','spring/tenant-command-api-project'])


def para(value):
    escaped = html.escape(value)
    return '<p>' + re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',
        lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>', escaped) + '</p>'

titles = {path: row['title'] for path, row in by_path.items()}
titles.update({spec['path']: spec['title'] for spec in specs})
for spec in specs:
    path = spec['path']
    assert path not in by_path, path
    assert all(target in titles for target in spec['links']), path
    hub = next(row for row in rows if row['type'] == 'subject' and row['subject'] == spec['subject'])
    body = para(spec['opening'])
    for heading, paragraphs in spec['sections']:
        body += '<h2>' + html.escape(heading) + '</h2>' + ''.join(para(value) for value in paragraphs)
    language = 'bash' if spec['code'].startswith('mvn ') else 'sql' if spec['code'].startswith('update ') else 'java'
    body += '<h2>Checked source</h2><pre><code class="language-' + language + '">' + html.escape(spec['code'].strip(), quote=False) + '</code></pre>'
    body += '<h2>Verification boundary</h2>' + para('OutboxRelayFlowTest has seven local tests in the downloadable Spring source kit. The excerpt is shortened; the kit contains the complete test.')
    body += '<h2>Costs and limits</h2>' + para(spec['limits'])
    body += '<h3>Common Mistakes</h3><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in spec['mistakes']) + '</ul>'
    body += '<h2>Read next</h2>' + para(', '.join('[[' + target + '|' + titles[target] + ']]' for target in spec['links']) + '.')
    row = by_path['spring/if-match-receipt-write'].copy()
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://aitrove.in/' + path)), type='article',
        path=path, title=spec['title'], summary=spec['opening'], body=body,
        subject=spec['subject'], difficulty='Intermediate', status='published',
        tags=['spring', 'spring-boot', 'outbox'], featured=False,
        sort_order=900 + len(rows), published_at=stamp, created_at=stamp, updated_at=stamp)
    row['data'] = {'subject_root': 'spring/spring-boot', 'section_path': hub['path'],
        'kind': 'tutorial', 'content_format': 'html',
        'reading_minutes': max(4, round(len(re.sub(r'<[^>]+>', ' ', body).split()) / 150)),
        'author_path': 'authors/aitrove-editorial', 'seo_ready': True,
        'related': [{'path': target, 'title': titles[target]} for target in spec['links']],
        'framework_version': 'Spring Boot 4.0.8 / Spring Framework 7',
        'java_version': '21 source-kit baseline', 'verification_suite': 'OutboxRelayFlowTest',
        'download_path': '/downloads/aitrove-spring-source-kit.zip'}
    rows.append(row)
    by_path[path] = row

groups = {
    'spring-data': ('Relay state and consumer commit', ['spring/outbox-relay-state-machine','spring/outbox-claim-lease','spring/consumer-idempotency','spring/relay-transaction-boundaries']),
    'spring-production': ('Retry and parked work', ['spring/relay-retry-schedule','spring/relay-dead-letter']),
    'spring-testing': ('Relay cut-point checks', ['spring/relay-failure-trace']),
    'spring-exercises': ('Outbox replay trace', ['spring/relay-cut-point-exercise']),
    'spring-projects': ('Delivery service design', ['spring/outbox-relay-service-project']),
}
for subject, (title, paths) in groups.items():
    hub = next(row for row in rows if row['type'] == 'subject' and row['subject'] == subject)
    hub['data']['modules'].append({'title': title, 'summary': 'Trace ownership, retry and duplicate delivery boundaries.', 'lessons': paths})
    hub['updated_at'] = stamp
    if '<h2>Section lessons</h2>' in hub['body']:
        links = '<ul>' + ''.join('<li><a href="/' + path + '">' + html.escape(titles[path]) + '</a></li>'
            for module in hub['data']['modules'] for path in module['lessons']) + '</ul>'
        hub['body'] = re.sub(r'(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)',
            lambda match: match[1] + links + match[2], hub['body'])

reverse = {
    'spring/receipt-outbox-command': ['spring/outbox-relay-state-machine'],
    'spring/outbox-atomic-write': ['spring/relay-transaction-boundaries'],
    'spring/outbox-expiring-lease': ['spring/outbox-claim-lease'],
    'spring/consumer-dedup-transaction': ['spring/consumer-idempotency'],
    'spring/transaction-propagation': ['spring/relay-transaction-boundaries'],
    'spring/testing-boundaries': ['spring/relay-failure-trace'],
    'spring/tenant-command-api-project': ['spring/outbox-relay-service-project'],
    'java/database-isolation': ['spring/consumer-idempotency'],
}
for path, targets in reverse.items():
    assert path in by_path, path
    row = by_path[path]
    marker = '<h2>Continue with checked relay behavior</h2>'
    row['body'] = row['body'].split(marker)[0] + marker + para('Continue with ' + ', '.join(
        '[[' + target + '|' + titles[target] + ']]' for target in targets) + '.')
    row['updated_at'] = stamp

quiz = by_path['quizzes/spring-data-production']
assert len(quiz['data']['questions']) == 25
quiz['data']['questions'].extend([
    {'prompt':'A producer inserts a shipment request and outbox row, then throws an unchecked exception in the same transaction. What should remain?',
     'options':['Neither row','The outbox row only','Both rows marked delivered'], 'answer':0,
     'explanation':'The checked TransactionTemplate callback rolls both inserts back; delivery has not begun.'},
    {'prompt':'A consumer commits stock and its applied-event marker, but the relay loses its acknowledgement. What protects the retry?',
     'options':['The same event ID and unique applied-event key','A new event ID','A longer producer transaction'], 'answer':0,
     'explanation':'The retry may reach the consumer again. Its unique key rejects a second mutation for the same event.'},
    {'prompt':'Worker A has a lease until logical time 120. At 120 worker B reclaims the event. Can A acknowledge at 121?',
     'options':['No, its claim token is stale','Yes, if the event ID matches','Yes, if its publish was fast'], 'answer':0,
     'explanation':'The acknowledgement checks both the current token and an unexpired lease.'},
    {'prompt':'An event has failed three times under a three-failure budget. What does the local claim query do?',
     'options':['It excludes the DEAD row','It immediately gives the row a fourth claim','It deletes the row'], 'answer':0,
     'explanation':'The third failure parks the row in DEAD; only PENDING rows are claimable.'},
    {'prompt':'What does OutboxRelayFlowTest prove about delivery?',
     'options':['Sequential H2 state transitions and local transaction results','Broker persistence after process kill','Concurrent claims on the production database'], 'answer':0,
     'explanation':'The fixture is in-process with a logical clock; broker and target-database checks remain separate.'},
])
quiz['updated_at'] = stamp
FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'added': [spec['path'] for spec in specs], 'quizQuestions': len(quiz['data']['questions'])}))
