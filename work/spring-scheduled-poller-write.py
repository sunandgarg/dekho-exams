"""Publish original Spring scheduled-poller lessons from the checked local fixture."""
from __future__ import annotations
import datetime, html, json, pathlib, re, uuid
ROOT=pathlib.Path(__file__).resolve().parents[1]
FILE=ROOT/'src/data/fixtures.json'
rows=json.loads(FILE.read_text()); by_path={r['path']:r for r in rows}
stamp=datetime.datetime.now(datetime.UTC).isoformat(); specs=[]

def add(subject,slug,title,opening,sections,code,proof,limits,mistakes,links):
 specs.append(dict(subject=subject,path='spring/'+slug,title=title,opening=opening,sections=sections,code=code,proof=proof,limits=limits,mistakes=mistakes,links=links))

add('spring-core','scheduled-outbox-worker','Spring TaskScheduler: poll committed outbox rows in the background',
'A scheduled outbox worker runs a bounded polling callback after the producer has committed work.',[
('The checked worker',[
'The source kit creates a ThreadPoolTaskScheduler with one thread and schedules a poll every 20 milliseconds after the previous callback finishes. The test inserts EVENT-41, waits on a latch for the callback to acknowledge it, then cancels the scheduled future and shuts the scheduler down. A local consumer transaction changes SKU-29 from 10 to 7. The row ends DELIVERED.',
'Fixed delay measures from the end of one invocation to the start of the next. It does not mean that each event completes inside 20 milliseconds. [[spring/poller-batch-limit|The batch budget]] stops one invocation from draining an unlimited backlog. [[spring/outbox-claim-lease|A guarded claim]] still matters when more than one process runs; one scheduler thread is not a distributed lock.' ]),
('Keep the boundary visible',[
'The transport in this fixture is a Java callback, not a broker. The scheduler is started inside a JUnit test, not installed in ReceiptApplication. It uses an in-memory H2 database and wall-clock due times. A process kill loses that database in this fixture, so the test does not establish restart recovery.',
'When installed in a service, configure pool size, poll interval, exception reporting and shutdown as deployment settings. Keep the remote call outside the producer transaction. [[spring/relay-transaction-boundaries|The transaction lesson]] explains why the two commits cannot be one local atomic step.'])],
'''var future = scheduler.scheduleWithFixedDelay(
    () -> new Poller(this::consumeLocally, delivered::countDown).runBatch(1),
    Duration.ofMillis(20));
assertTrue(delivered.await(3, TimeUnit.SECONDS));
future.cancel(false);
scheduler.shutdown();''',
'ScheduledOutboxPollerTest.scheduledWorkerConsumesCommittedRowAndStops',
'The test uses one scheduler thread and a three-second latch bound. It does not measure production poll latency, cross-node claims, durable recovery, or broker acceptance.',
['Do not call a scheduler thread a durable queue.','Do not put unbounded work into a fixed-delay callback.','Do not leave a test-created scheduler running after the assertion.'],
['spring/poller-batch-limit','spring/poller-shutdown','spring/outbox-claim-lease','spring/relay-transaction-boundaries','spring/outbox-relay-state-machine'])

add('spring-production','poller-batch-limit','Spring outbox polling: cap work per tick and measure backlog age',
'A poller batch limit bounds the rows one callback will claim before it yields to the scheduler.',[
('A bounded selection',[
'The fixture inserts three due event rows and invokes runBatch(2). Two rows become DELIVERED and one remains PENDING. A second call handles the last row. The selection orders by event ID and applies LIMIT 2, then each candidate is conditionally claimed before the fake transport runs. The claim statement repeats the due and lease predicates because another worker could change a row after the SELECT.',
'The source kit does not run this test concurrently. A target database may use different locking and query plans. Add an index for state and due time only after measuring representative data, then check fairness when one old event repeatedly fails. [[spring/poller-retry-due|A retry due time]] keeps a failed row from monopolizing every tick.' ]),
('Choose a budget from resources',[
'A batch of two is a small test value, not a recommended production setting. Each callback borrows database connections, allocates rows and may hold a scheduler thread while the transport waits. Cap each remote call and the whole tick. If one event stalls, a fixed-delay schedule pauses subsequent ticks on that thread.',
'Backlog count alone misses aging work. Track the oldest due event, claim latency, delivery latency and dead-row count with bounded metric labels. [[spring/poller-metrics|The measurement lesson]] separates dimensions suitable for metrics from event IDs that belong in diagnostic logs.'])],
'''select event_id from scheduled_outbox
where state = 'PENDING' and next_due <= ?
  and (claim_token is null or lease_until <= ?)
order by event_id limit ?;''',
'ScheduledOutboxPollerTest.onePollProcessesOnlyItsBatchBudget',
'The selection and claim run on H2 with three rows. No production index plan, contention measurement, fairness proof, or multi-node batch benchmark is included.',
['Do not select every pending row into memory.','Do not trust a prior SELECT as ownership.','Do not size a production batch from a three-row test.'],
['spring/scheduled-outbox-worker','spring/poller-retry-due','spring/poller-metrics','spring/outbox-claim-lease'])

add('spring-production','poller-retry-due','Spring scheduled retries: leave failed work pending until its due time',
'A failed transport attempt can remain PENDING while its next_due timestamp prevents immediate reprocessing.',[
('One fake failure, then success',[
'The scheduled fixture gives EVENT-42 a fake transport that throws once. The poller records one failure, clears the claim and sets next_due 80 milliseconds after that failure. A later scheduled tick claims the same event ID, calls the local consumer and acknowledges the row. The test waits for delivery, then checks two transport calls, one failure record and stock changing from 10 to 8 once.',
'The [[spring/relay-retry-schedule|separate logical-clock test]] checks exact due-time boundaries and a capped delay. This scheduled test checks that Spring runs a callback again after a real short wait. It does not prove the scheduler runs exactly at the due timestamp; process load can delay it.' ]),
('Classify before retrying',[
'The fixture treats every RuntimeException as retryable. A deployed adapter must separate temporary transport trouble from invalid payloads, permanent authorization failure and exhausted budgets. Add a maximum elapsed time, a parked state and alerting. Retry with the same event ID because a lost response may hide a committed consumer mutation.',
'The consumer in the fixture writes a unique event marker with stock. [[spring/poller-lost-ack|The lost-acknowledgement check]] shows why that marker matters even when a transport call appears to finish. Do not use sleep inside the callback to delay a retry; persist the due time and release the scheduler thread.'])],
'''catch (RuntimeException transportFailure) {
    jdbc.update("update scheduled_outbox set failures = failures + 1, next_due = ?, claim_token = null, lease_until = null where event_id = ? and claim_token = ?", now + 80, eventId, token);
}''',
'ScheduledOutboxPollerTest.failedTransportWaitsThenRetriesSameEvent',
'The excerpt shortens the checked SQL lease predicate. The test uses a fake exception and a short wall-clock delay; there is no external transport, jitter, error taxonomy or load test.',
['Do not retry a permanent rejection forever.','Do not sleep while holding the polling thread.','Do not create a new event ID for the same retry.'],
['spring/scheduled-outbox-worker','spring/relay-retry-schedule','spring/relay-dead-letter','spring/poller-lost-ack'])

add('spring-data','poller-lost-ack','Spring scheduled relay: recover when the consumer commits before acknowledgement',
'A relay can lose its acknowledgement after the consumer commits, leaving a PENDING event that will be delivered again.',[
('The exact cut point',[
'The test inserts EVENT-61 for four units, calls the local consumer directly and deliberately leaves the outbox row PENDING. The consumer commits an applied_event key and stock changes from 10 to 6. The poller then selects the event, invokes the same consumer again and acknowledges the outbox row. The second consumer invocation hits the unique event key and does not subtract stock again. Final state is DELIVERED, one applied marker, stock 6.',
'This is a controlled cut point, not a process crash. It proves the local duplicate path once the event marker is already present. [[spring/consumer-idempotency|The consumer transaction]] is the guard. [[spring/outbox-claim-lease|The lease token]] only controls who may update the outbox row; it cannot undo a consumer commit.' ]),
('Treat uncertain acknowledgements as ordinary',[
'A real broker publish may succeed even when its acknowledgement is lost. If a relay assumes the timeout means no delivery, it may send the same event again. The event ID should survive retries, and the consumer should store enough state to return a safe duplicate result.',
'The fixture stores both outbox and consumer tables in one H2 database for convenience, though it calls separate transactions. A real consumer can use another database. Integration tests must kill the relay between consumer commit and outbox acknowledgement and verify recovery after restart.'])],
'''consumeLocally("EVENT-61"); // Consumer commits; outbox remains PENDING.
new Poller(this::consumeLocally, () -> {}).runBatch(1);
assertEquals(6, jdbc.queryForObject(
    "select available from stock_balance where sku = 'SKU-29'", Integer.class));''',
'ScheduledOutboxPollerTest.redeliveryAfterLostAcknowledgementDoesNotRepeatStockMutation',
'The test invokes the consumer twice in one process. It has no broker offset, process kill, network partition, separate consumer database or deduplication retention policy.',
['Do not equate a lost acknowledgement with a rolled-back consumer.','Do not reserve an event marker outside the business transaction.','Do not discard a stable event ID when retrying.'],
['spring/consumer-idempotency','spring/outbox-claim-lease','spring/relay-transaction-boundaries','spring/poller-integration-tests'])

add('spring-core','poller-shutdown','Spring TaskScheduler shutdown: stop new polls and account for in-flight work',
'Scheduler shutdown stops future polling callbacks; it does not automatically reverse an external operation already in flight.',[
('The checked lifecycle',[
'The local test initializes one ThreadPoolTaskScheduler, schedules a fixed-delay poller, waits for one delivered event, cancels the returned ScheduledFuture and calls shutdown in a finally block. The cancelled future reports cancelled. This is enough to keep the test from leaving a polling thread behind.',
'The test does not start a graceful deployment drain, wait for a slow transport, renew an expiring lease, or restart after a kill. A callback could be inside a remote publish when the process receives a stop signal. [[spring/outbox-claim-lease|The lease]] must expire or renew; [[spring/poller-lost-ack|the consumer marker]] must handle a retry.' ]),
('Design the stop budget',[
'For a service, stop accepting new claims, allow current callbacks a bounded completion window, and leave unacknowledged rows recoverable. A forced termination may happen at any point. Do not mark work delivered merely because a shutdown hook ran. Configure scheduler lifecycle with the application context and measure drain duration under realistic transport timeouts.',
'A callback that catches every exception without recording state can hide lost work. Keep the row transition, error category and event ID available for operators. [[spring/poller-metrics|Backlog age]] will show stalled recovery after a restart.'])],
'''var future = scheduler.scheduleWithFixedDelay(poller, Duration.ofMillis(20));
try { assertTrue(delivered.await(3, TimeUnit.SECONDS)); }
finally { future.cancel(false); scheduler.shutdown(); }''',
'ScheduledOutboxPollerTest.scheduledWorkerConsumesCommittedRowAndStops',
'The test verifies cancellation and shutdown after one successful callback. It does not assert application-context lifecycle, in-flight timeout handling, process termination or deployment drain.',
['Do not assume cancel(false) interrupts a running callback.','Do not delete a leased row during shutdown.','Do not call one clean test teardown a restart-recovery test.'],
['spring/scheduled-outbox-worker','spring/outbox-claim-lease','spring/poller-lost-ack','spring/poller-integration-tests'])

add('spring-production','poller-metrics','Spring relay metrics: measure backlog without event-ID labels',
'Relay metrics should expose workload and failure trends without creating one time series per event.',[
('Bound the dimensions',[
'Useful values include due-row count, oldest due-row age, claim conflicts, publish attempts, duplicate consumer results, delivered count and dead-row count. Low-cardinality labels can identify environment, outcome class and a small fixed operation set. An event ID, user ID, tenant ID or raw exception message is too unbounded for a metric tag. Put those values in access-controlled logs or traces with retention limits.',
'The existing [[spring/metric-cardinality|metric-cardinality fixture]] checks bounded labels on a separate import path. The scheduled poller fixture does not emit relay metrics. This lesson is an instrumentation contract, not evidence of a live dashboard. Spring Boot uses Micrometer for metrics; choose an export backend only after the service exists.' ]),
('Alert on the work that matters',[
'An empty queue is not automatically healthy: the producer may have stopped writing. Compare accepted commands with outbox inserts and delivered counts. Alert on sustained oldest-due age and dead-row growth, not on every single retry. Record the count of events waiting beyond the service objective.',
'Computing oldest age may require a database query on each scrape. Bound scrape cost with an index, a cached sampling interval or a background aggregate. Verify the value against actual row state during an outage drill. [[spring/poller-batch-limit|Batch limits]] and [[spring/poller-retry-due|due times]] affect the interpretation of that age.'])],
'''// Design sketch; this meter is not installed in the poller fixture.
registry.counter("aitrove.relay.attempts", "outcome", "delivered").increment();''',
'FrameworkBoundaryTest.enumOutcomeBoundsMeterIdentities checks label policy elsewhere in the source kit',
'No relay meter, exporter, dashboard or alert rule is wired. A counter alone cannot show backlog age or prove delivery, and a database scrape needs a measured query plan.',
['Do not use event IDs or raw errors as metric tags.','Do not alert on every retry without a sustained-age signal.','Do not assume an empty queue proves the producer is running.'],
['spring/metric-cardinality','spring/poller-batch-limit','spring/poller-retry-due','spring/relay-dead-letter'])

add('spring-testing','poller-integration-tests','Spring relay integration tests: prove the boundaries H2 cannot',
'A relay integration test must cross the same database and transport boundaries that a deployed worker crosses.',[
('What the local suite proves',[
'ScheduledOutboxPollerTest proves that Spring schedules a callback, the local H2 row is selected and claimed, a fake transport can fail once and retry, a batch cap leaves one row pending, and an already-applied event does not mutate stock twice. OutboxRelayFlowTest separately checks logical due times, parked work and token-fenced acknowledgement. Both suites run in one process.',
'Those facts do not establish two-worker claim fairness, broker persistence, broker redelivery, target-database isolation, shutdown drain or crash recovery. [[spring/scheduled-outbox-worker|The scheduler lesson]] names the first boundary; [[spring/poller-lost-ack|the cut-point lesson]] names the duplicate boundary.' ]),
('Next test matrix',[
'Run two worker instances against the target database. Race claims for the same due row and assert one current token. Add a real transport test: confirm publish, kill the relay before acknowledgement, restart, then assert one business mutation. Inject a lost publish response, slow consumer, permanent payload rejection, expired lease and broker outage. Check row state and metrics after each cut point.',
'Keep test clocks controllable for exact due-time checks, then add a small number of real scheduling tests. Avoid sleeps as the only evidence. Use a latch or observable state with a deadline so failures are bounded and reproducible. The current scheduled fixture uses a latch; it does not replace a process-kill test.'])],
'''mvn -q -Dtest=ScheduledOutboxPollerTest,OutboxRelayFlowTest test''',
'ScheduledOutboxPollerTest and OutboxRelayFlowTest run locally',
'No target database, broker, containerized multi-instance environment, process-kill setup or deployment probe is included in this source kit.',
['Do not report H2 scheduling as broker delivery.','Do not infer cross-node claim safety from one scheduler thread.','Do not use an unbounded wait for an asynchronous assertion.'],
['spring/scheduled-outbox-worker','spring/poller-lost-ack','spring/relay-failure-trace','spring/outbox-relay-service-project'])

add('spring-exercises','scheduled-relay-trace-exercise','Spring exercise: trace two poll ticks and a lost acknowledgement',
'A poll-tick trace asks which outbox and consumer rows survive after retries and an uncertain acknowledgement.',[
('First trace',[
'Insert three due events, each reducing SKU-29 by one. Run a poll with limit two. Expect two DELIVERED rows, one PENDING row and stock 8. Run another poll. Expect all three delivered and stock 7. The checked batch test asserts these states. Now make the first transport call fail before consumer work. The event remains PENDING with one failure and a future due time; a later tick uses the same event ID.',
'[[spring/poller-batch-limit|The batch lesson]] explains why the third row waits. [[spring/poller-retry-due|The retry lesson]] explains why an immediate tick should skip failed work.' ]),
('Second trace',[
'Let the consumer commit EVENT-61 but withhold the relay acknowledgement. Predict stock, applied-event count and outbox state before and after a later poll. The answer is stock 6 and one applied marker throughout; the outbox moves from PENDING to DELIVERED after the duplicate-safe callback.',
'Change one assumption at a time: remove the unique event key, then shorten the lease below transport latency. State which guard fails and what the next test should assert. Run the source-kit tests, then write a separate broker and target-database plan. The local exercise cannot prove that a process survives a real kill.'])],
'''mvn -q -Dtest=ScheduledOutboxPollerTest,OutboxRelayFlowTest test''',
'ScheduledOutboxPollerTest.onePollProcessesOnlyItsBatchBudget and redeliveryAfterLostAcknowledgementDoesNotRepeatStockMutation',
'The exercise uses local H2 rows and a fake callback. There is no hosted judge, broker or deployment environment.',
['Do not count a failed publish as delivered.','Do not change an event ID to make a retry look new.','Do not claim a cut-point simulation is a killed-process recovery test.'],
['spring/poller-batch-limit','spring/poller-retry-due','spring/poller-lost-ack','spring/poller-integration-tests'])

def para(value):
 escaped=html.escape(value)
 return '<p>'+re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',lambda m:'<a href="/'+m[1]+'">'+m[2]+'</a>',escaped)+'</p>'

titles={p:r['title'] for p,r in by_path.items()};titles.update({s['path']:s['title'] for s in specs})
for spec in specs:
 p=spec['path']; assert p not in by_path,p;assert all(x in titles for x in spec['links']),p
 hub=next(r for r in rows if r['type']=='subject' and r['subject']==spec['subject'])
 body=para(spec['opening'])
 for h,paragraphs in spec['sections']:body+='<h2>'+html.escape(h)+'</h2>'+''.join(para(x) for x in paragraphs)
 lang='bash' if spec['code'].startswith('mvn ') else 'sql' if spec['code'].startswith('select ') else 'java'
 body+='<h2>Checked source</h2><pre><code class="language-'+lang+'">'+html.escape(spec['code'].strip(),quote=False)+'</code></pre>'
 body+='<h2>Verification boundary</h2>'+para(spec['proof']+'. The excerpt is shortened or a labelled design sketch; the source kit contains the complete checked fixture.')
 body+='<h2>Costs and limits</h2>'+para(spec['limits'])
 body+='<h3>Common Mistakes</h3><ul>'+''.join('<li>'+html.escape(x)+'</li>' for x in spec['mistakes'])+'</ul>'
 body+='<h2>Read next</h2>'+para(', '.join('[['+x+'|'+titles[x]+']]' for x in spec['links'])+'.')
 row=by_path['spring/if-match-receipt-write'].copy();row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+p)),type='article',path=p,title=spec['title'],summary=spec['opening'],body=body,subject=spec['subject'],difficulty='Intermediate',status='published',tags=['spring','spring-boot','scheduled-relay'],featured=False,sort_order=900+len(rows),published_at=stamp,created_at=stamp,updated_at=stamp)
 row['data']={'subject_root':'spring/spring-boot','section_path':hub['path'],'kind':'tutorial','content_format':'html','reading_minutes':max(4,round(len(re.sub(r'<[^>]+>',' ',body).split())/150)),'author_path':'authors/aitrove-editorial','seo_ready':True,'related':[{'path':x,'title':titles[x]} for x in spec['links']],'framework_version':'Spring Boot 4.0.8 / Spring Framework 7','java_version':'21 source-kit baseline','verification_suite':spec['proof'],'download_path':'/downloads/aitrove-spring-source-kit.zip'}
 rows.append(row);by_path[p]=row

groups={
 'spring-core':('Scheduled work lifecycle',['spring/scheduled-outbox-worker','spring/poller-shutdown']),
 'spring-production':('Polling budgets and signals',['spring/poller-batch-limit','spring/poller-retry-due','spring/poller-metrics']),
 'spring-data':('Duplicate delivery after a lost acknowledgement',['spring/poller-lost-ack']),
 'spring-testing':('Beyond local poller tests',['spring/poller-integration-tests']),
 'spring-exercises':('Scheduled relay trace',['spring/scheduled-relay-trace-exercise']),
}
for subject,(title,paths) in groups.items():
 hub=next(r for r in rows if r['type']=='subject' and r['subject']==subject)
 hub['data']['modules'].append({'title':title,'summary':'Trace scheduled claims, retries and duplicate-safe completion.','lessons':paths})
 hub['updated_at']=stamp
 if '<h2>Section lessons</h2>' in hub['body']:
  links='<ul>'+''.join('<li><a href="/'+p+'">'+html.escape(titles[p])+'</a></li>' for module in hub['data']['modules'] for p in module['lessons'])+'</ul>'
  hub['body']=re.sub(r'(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)',lambda m:m[1]+links+m[2],hub['body'])

reverse={
 'spring/outbox-relay-state-machine':['spring/scheduled-outbox-worker'],
 'spring/relay-retry-schedule':['spring/poller-retry-due'],
 'spring/consumer-idempotency':['spring/poller-lost-ack'],
 'spring/metric-cardinality':['spring/poller-metrics'],
 'spring/outbox-relay-service-project':['spring/poller-integration-tests'],
 'spring/relay-failure-trace':['spring/scheduled-relay-trace-exercise'],
 'spring/async-boundaries':['spring/poller-shutdown'],
}
for p,targets in reverse.items():
 assert p in by_path,p
 row=by_path[p];marker='<h2>Continue with scheduled relay checks</h2>'
 row['body']=row['body'].split(marker)[0]+marker+para('Continue with '+', '.join('[['+x+'|'+titles[x]+']]' for x in targets)+'.')
 row['updated_at']=stamp

quiz=by_path['quizzes/spring-core'];assert len(quiz['data']['questions'])==12
quiz['data']['questions'].extend([
 {'prompt':'What does a fixed-delay poll interval measure?','options':['Time after one callback finishes before the next begins','A hard deadline for each event','The exact broker delivery time'],'answer':0,'explanation':'The next invocation is scheduled after the prior callback completes. Transport time is separate.'},
 {'prompt':'Three events are due and a tick has batch limit two. What should one checked tick leave?','options':['Two delivered and one pending','All three delivered','No rows claimable ever again'],'answer':0,'explanation':'The fixture processes at most two candidates per call; a second call handles the remaining row.'},
 {'prompt':'Why does the claim UPDATE repeat due-time and lease predicates after the SELECT?','options':['Another worker may change the row between selection and claim','It changes SQL syntax highlighting','It makes the broker transactional'],'answer':0,'explanation':'The conditional mutation decides ownership against current row state.'},
 {'prompt':'A fake transport fails once in the scheduled test. What happens next?','options':['The same event ID remains pending until its due time','The row is marked delivered immediately','A new event ID is generated'],'answer':0,'explanation':'The poller increments its failure count, clears the claim and stores a future due time.'},
 {'prompt':'What does cancelling the scheduled future prove?','options':['Future callbacks from that local schedule stop','An in-flight broker publish is rolled back','A crashed service restarts safely'],'answer':0,'explanation':'Cancellation controls this scheduler registration; external work and restart recovery need separate checks.'},
])
quiz['updated_at']=stamp
FILE.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'added':[s['path'] for s in specs],'coreQuizQuestions':len(quiz['data']['questions'])}))
