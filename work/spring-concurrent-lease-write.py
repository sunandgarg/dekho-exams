"""Add original Spring outbox concurrency and renewal lessons from H2 checks."""
from __future__ import annotations
import datetime,html,json,pathlib,re,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1];FILE=ROOT/'src/data/fixtures.json'
rows=json.loads(FILE.read_text());by_path={x['path']:x for x in rows};stamp=datetime.datetime.now(datetime.UTC).isoformat()
specs=[
 ('spring/concurrent-outbox-claim','Spring outbox claim race: one conditional UPDATE wins',
 'A conditional claim UPDATE gives an outbox row one current owner when two workers race for it on the same database.',[
  ('The local race',[
   'ConcurrentOutboxLeaseTest opens a separate H2 connection for each worker through DriverManagerDataSource. Two threads wait on a start latch, then issue the same guarded UPDATE for EVENT-81 with different tokens. Exactly one UPDATE reports one changed row; the other reports zero. The row stores the winner token. The test has a finite wait for worker readiness and results, so a stalled thread fails the test rather than hanging it.',
   'This covers one H2 row and one two-thread race. H2 may lock and isolate differently from PostgreSQL, MySQL or another target database. The assertion is a contract to rerun in the deployment database, not evidence that every engine has identical throughput or contention behavior. [[spring/outbox-claim-lease|The lease lesson]] explains expiry; [[spring/poller-batch-limit|the batch lesson]] explains why a preceding SELECT does not grant ownership.' ]),
  ('Protect the claim after selection',[
   'Both workers may read the event ID before either changes the row. The winner is decided by the UPDATE predicate, not by which thread ran SELECT first. Guard state and expiry in the mutation itself. If no row changes, the worker must not publish that event. Do not fabricate a successful claim by using the selected row as proof.',
   'At scale, measure lock waits, deadlocks and selection plans with due rows and multiple processes. Batching with SKIP LOCKED can improve contention on some engines but changes fairness and syntax; the checked H2 SQL uses no such feature. [[spring/poller-integration-tests|The integration plan]] names the target-database checks still required.'])],
 '''update lease_event set claim_token = ?, lease_until = ?
where event_id = 'EVENT-81' and state = 'PENDING'
  and (claim_token is null or lease_until <= ?);''',
 'ConcurrentOutboxLeaseTest.twoConcurrentConnectionsYieldOneCurrentClaim',
 'The test uses two H2 connections and one row. It does not run two service processes, a broker, target-database isolation variants, or a sustained load test.',
 ['Do not publish an event after a zero-row claim.','Do not treat a SELECT as a lock unless the database query explicitly guarantees it.','Do not generalize an H2 winner test to another engine without rerunning it.'],
 ['spring/outbox-claim-lease','spring/poller-batch-limit','spring/poller-integration-tests','spring/relay-transaction-boundaries']),
 ('spring/outbox-lease-renewal','Spring outbox lease renewal: extend only the current owner',
 'Lease renewal extends a worker claim only when its token still owns an unexpired row and the new deadline moves forward.',[
  ('The checked sequence',[
   'Worker A claims EVENT-81 from logical time 100 to 150. A renewal from worker B fails. A renewal from A to 140 also fails because it would shorten the lease. A can extend it to 200 while the claim is still live. Worker B cannot claim at 160. At 200, A can no longer renew; B reclaims to 260. A stays stale, and only B can extend the lease to 300.',
   'The UPDATE checks the token, PENDING state, current lease greater than now and current lease shorter than the proposed deadline. [[spring/outbox-claim-lease|The acknowledgement lesson]] uses the same ownership idea when a worker finishes. Renewal is useful only if the worker can report progress and stop when it loses ownership.' ]),
  ('Do not confuse renewal with remote fencing',[
   'This token fences the H2 row, not a broker publish already started by A. A slow A may finish its remote call after B takes over. The downstream [[spring/consumer-idempotency|event-ID ledger]] still needs to reject duplicate business work. On a real service, schedule renewal before expiry with a measured safety margin, bounded clock assumptions and a maximum processing deadline.',
   'The checked test uses caller-supplied logical time and no background renewal task. It does not cover a pause during garbage collection, network partitions, skewed worker clocks, or concurrent renewal on the deployment database. [[spring/poller-shutdown|Shutdown]] must leave unacknowledged work recoverable if renewal stops.'])],
 '''update lease_event set lease_until = ?
where event_id = 'EVENT-81' and state = 'PENDING' and claim_token = ?
  and lease_until > ? and lease_until < ?;''',
 'ConcurrentOutboxLeaseTest.renewalRequiresCurrentUnexpiredTokenAndLongerDeadline',
 'The test covers sequential H2 renewal with logical timestamps. It does not install a renewal timer, coordinate host clocks, or prove a remote side effect is fenced.',
 ['Do not renew with only an event ID.','Do not let a stale worker extend a replacement owner’s lease.','Do not assume an extended database lease cancels a duplicate publish.'],
 ['spring/concurrent-outbox-claim','spring/outbox-claim-lease','spring/consumer-idempotency','spring/poller-shutdown'])
]

def para(s):
 esc=html.escape(s)
 return '<p>'+re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',lambda m:'<a href="/'+m[1]+'">'+m[2]+'</a>',esc)+'</p>'

titles={p:x['title'] for p,x in by_path.items()};titles.update({x[0]:x[1] for x in specs})
hub=by_path['spring/data-transactions']
for path,title,opening,sections,code,proof,limits,mistakes,links in specs:
 assert path not in by_path and all(p in titles for p in links),path
 body=para(opening)
 for h,ps in sections:body+='<h2>'+html.escape(h)+'</h2>'+''.join(para(p) for p in ps)
 body+='<h2>Checked source</h2><pre><code class="language-sql">'+html.escape(code.strip(),quote=False)+'</code></pre>'
 body+='<h2>Verification boundary</h2>'+para(proof+' in the downloadable Spring source kit. The excerpt is shortened; the kit contains the complete checked SQL.')
 body+='<h2>Costs and limits</h2>'+para(limits)
 body+='<h3>Common Mistakes</h3><ul>'+''.join('<li>'+html.escape(x)+'</li>' for x in mistakes)+'</ul>'
 body+='<h2>Read next</h2>'+para(', '.join('[['+p+'|'+titles[p]+']]' for p in links)+'.')
 row=by_path['spring/if-match-receipt-write'].copy();row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),type='article',path=path,title=title,summary=opening,body=body,subject='spring-data',difficulty='Intermediate',status='published',tags=['spring','spring-boot','outbox'],featured=False,sort_order=900+len(rows),published_at=stamp,created_at=stamp,updated_at=stamp)
 row['data']={'subject_root':'spring/spring-boot','section_path':hub['path'],'kind':'tutorial','content_format':'html','reading_minutes':max(4,round(len(re.sub(r'<[^>]+>',' ',body).split())/150)),'author_path':'authors/aitrove-editorial','seo_ready':True,'related':[{'path':p,'title':titles[p]} for p in links],'framework_version':'Spring Boot 4.0.8 / Spring Framework 7','java_version':'21 source-kit baseline','verification_suite':proof,'download_path':'/downloads/aitrove-spring-source-kit.zip'}
 rows.append(row);by_path[path]=row
hub['data']['modules'].append({'title':'Concurrent claims and renewal','summary':'Check current ownership before claiming or extending a lease.','lessons':[x[0] for x in specs]});hub['updated_at']=stamp
if '<h2>Section lessons</h2>' in hub['body']:
 links='<ul>'+''.join('<li><a href="/'+p+'">'+html.escape(titles[p])+'</a></li>' for m in hub['data']['modules'] for p in m['lessons'])+'</ul>'
 hub['body']=re.sub(r'(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)',lambda m:m[1]+links+m[2],hub['body'])
for path,targets in {'spring/outbox-claim-lease':['spring/concurrent-outbox-claim','spring/outbox-lease-renewal'],'spring/poller-integration-tests':['spring/concurrent-outbox-claim'],'spring/poller-shutdown':['spring/outbox-lease-renewal']}.items():
 row=by_path[path];marker='<h2>Continue with lease race checks</h2>'
 row['body']=row['body'].split(marker)[0]+marker+para('Continue with '+', '.join('[['+p+'|'+titles[p]+']]' for p in targets)+'.');row['updated_at']=stamp
quiz=by_path['quizzes/spring-core'];assert len(quiz['data']['questions'])==17
quiz['data']['questions'].extend([
 {'prompt':'Two H2 workers select the same pending event. Which operation decides the current claim owner?','options':['The conditional UPDATE result','The earlier SELECT result','The worker thread name'],'answer':0,'explanation':'Only the guarded mutation checks current state and returns one changed row to the winner.'},
 {'prompt':'Worker A’s lease expires and B reclaims the event. May A renew it afterward?','options':['No, its token is stale','Yes, if it proposes a later deadline','Yes, if it still has the event payload'],'answer':0,'explanation':'Renewal requires the current token and an unexpired current lease.'},
]);quiz['updated_at']=stamp
FILE.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'added':[x[0] for x in specs],'coreQuizQuestions':len(quiz['data']['questions'])}))
