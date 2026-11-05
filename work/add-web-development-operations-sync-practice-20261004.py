"""Add production-diagnosis and synchronization projects with explained quiz."""
import copy
import datetime
import html
import json
import subprocess
import uuid
from pathlib import Path
root=Path(__file__).resolve().parents[1]
fixture=root/'src/data/fixtures.json'
entries=json.loads(fixture.read_text())
by_path={entry['path']:entry for entry in entries}
stamp=datetime.datetime.now(datetime.UTC).isoformat()
def p(value): return '<p>'+html.escape(value)+'</p>'
def link(path):
    assert path in by_path,path
    return '<a href="/'+html.escape(path,quote=True)+'">'+html.escape(by_path[path]['title'])+'</a>'

projects=[
 dict(path='web-tech/case-save-incident-evidence-project',title='Project: case-save incident evidence',summary='Instrument a complete case save, derive a user-facing SLO, and rehearse containment with a queue backlog.',
 intro='Build an evidence path for case 47 from browser submit through API acceptance, queue handoff, worker receipt, and final visible state. Propagate trace context through the queued message, but keep a separate durable operation ID for retries and business decisions. The incoming trace header is untrusted and never authorizes access. Define one eligible case-save operation and count it good only after the final state is visible within its deadline. Build a bounded metric label set and an allowlisted structured event; neither may include raw note text or reviewer email. Simulate release 29 accepting 62 writes while the receipt worker fails. A responder must see the real user impact, choose a reversible containment action, check compatibility before rollback, and verify both new saves and pending jobs after recovery.',
 scope=['Join browser, API, and worker evidence with trace context plus a stable operation ID; prove collector loss does not change write acceptance.','Define the good, bad, and pending states for the case-save journey, deduplicate retries, and alert on sustained budget spend with a low-volume guard.','Inspect final telemetry exports for private content and bound metric labels to route template, release, and outcome category.','Record a first-impact and containment timeline; check queue-message and schema compatibility before rollback, then verify backlog repair.'],
 code='function journeyOutcome(receipt, deadlineExceeded) {\n  if (receipt === "visible") return "good";\n  return deadlineExceeded ? "bad" : "pending";\n}\nconsole.log(journeyOutcome("queued", false));\n// Output: pending',
 cost='For n case saves, a bounded event per transition uses O(n) record volume; tracing every internal span raises cost with span count and requires a sampling policy. Metric series should depend on a bounded number of route, release, and outcome combinations rather than grow with n case IDs. A queue backlog consumes storage while contained, but deleting it loses accepted work. A rollback may be fast only if old code can read messages and data written by the new release. Measure time to detect, time to contain, final operation completeness, and telemetry overhead under a synthetic burst. A quiet error chart after containment is insufficient when accepted jobs remain unresolved.',
 failure='Send a forged trace header and prove it cannot select an account. Drop the collector, then verify the case-save contract still works while telemetry loss is visible. Return 202 for 62 writes and fail the worker: an HTTP-success indicator must not mark those journeys good. Add a case ID to a metric label and watch series count grow under 47,000 unique cases; remove it. Put a private note marker in an exception and check that no exported signal contains it. Roll back to a worker that cannot decode the new message and confirm the runbook blocks the action. Drain pending work and reconcile every accepted operation.',
 checks=['A complete operation can be traced without trusting a caller identifier for authorization.','Pending and failed terminal jobs reduce the user-journey indicator despite an API 202 response.','Telemetry export excludes private payloads and metric cardinality stays bounded.','Containment and rollback decisions include message compatibility and backlog verification.'],
 mistakes=['Calling API acceptance a finished user task.','Keeping a private request body in a trace or exception event.','Rolling back code before checking queued-message compatibility.','Closing the incident while accepted jobs are still pending.'],
 related=['web-tech/trace-context-across-request-and-job','web-tech/user-journey-slos-and-burn-alerts','web-tech/telemetry-shapes-redaction-and-cardinality','web-tech/incident-containment-and-evidence-timeline','web-tech/accepted-operations-and-status-resources']),
 dict(path='web-tech/multi-tab-offline-case-review-project',title='Project: multi-tab offline case review',summary='Keep edits, snapshots, and collaboration signals coherent across two tabs, disconnection, and replay.',
 intro='Build a case-47 review workspace used in two tabs and one intermittently connected device. Tab A saves version 7 while Tab B holds an unsaved note based on version 6. A same-origin message gives Tab B an invalidation hint, not the new private record; Tab B fetches a current authorized snapshot without overwriting its note. An offline status change enters a bounded outbox as operation op-47 and remains Queued until server acceptance. A lost response causes replay with the same idempotency key. A stale version becomes Conflicted and retains the local intent. The live queue starts from a snapshot tied to a server cursor, applies deduplicated deltas, and fetches a new snapshot on a gap or expired replay window. Editing presence expires after missing heartbeats and never grants a lock.',
 scope=['Send scoped cross-tab invalidation hints, revalidate on focus after missed messages, and keep unsaved fields separate from fetched server state.','Persist a bounded account-scoped outbox with stable operation IDs, version preconditions, retry limits, and distinct accepted, conflicted, and rejected outcomes.','Bridge snapshot to change stream through a server cursor; detect duplicate, gap, expiry, filter change, and account change.','Test expiring presence separately from server write versions and expose a same-field conflict repair view.'],
 code='function outboxState(responseStatus) {\n  if (responseStatus === 412) return "conflicted";\n  if (responseStatus === 403) return "rejected";\n  return responseStatus >= 200 && responseStatus < 300 ? "accepted" : "retry-later";\n}\nconsole.log(outboxState(412));\n// Output: conflicted',
 cost='The outbox and retained case snapshots use O(n) device storage for n pending or cached records; cap both item count and total bytes, and plan for browser eviction. Snapshot refresh costs O(m) transfer for m records, while a valid delta stream costs O(d) for d changes since the cursor. Presence heartbeats create traffic proportional to active editors and can expand sharply if every update is broadcast to every participant. Cross-tab hints are cheap but can trigger duplicate fetches across many tabs; coalesce repeated versions. Measure stale-window duration, replay age, duplicate suppression, gap recovery time, and the number of unsaved edits retained through a conflict.',
 failure='Save in Tab A while Tab B has unsaved text. A direct broadcast of the whole case must not replace Tab B’s note. Close Tab B before the next change; reopening it must revalidate without receiving the missed message. Lose the server response after a committed write and verify replay makes one audit entry. Cause a 412 and ensure the edit does not claim Saved. Omit a delta sequence and require a fresh snapshot rather than a silently stale queue. Put one editor to sleep; presence must expire without blocking another editor. Move the device clock and confirm it cannot win a server version conflict.',
 checks=['Unsaved local text survives cross-tab invalidation and a version conflict.','A replayed offline operation creates at most one server mutation.','An expired or mismatched cursor triggers a fresh scoped snapshot.','Presence expires without acting as an edit lock or authorization grant.'],
 mistakes=['Assuming a browser channel is a durable message queue.','Creating a new idempotency key after a lost response.','Keeping a delta cursor across a filter or account change.','Treating presence or client timestamps as the write authority.'],
 related=['web-tech/cross-tab-invalidation-and-version-checks','web-tech/offline-outbox-idempotency-and-replay','web-tech/snapshot-delta-cursor-and-gap-recovery','web-tech/collaborative-conflicts-and-presence-expiry','web-tech/conditional-writes-and-lost-update-prevention'])
]
for index,project in enumerate(projects,1):
    assert project['path'] not in by_path
    subprocess.run(['node','--check','--input-type=module'],input=project['code'],text=True,capture_output=True,check=True)
    entry=copy.deepcopy(by_path['web-tech/streamed-case-activity-and-export-project'])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'aitrove:'+project['path'])),path=project['path'],title=project['title'],summary=project['summary'],sort_order=1140+index,created_at=stamp,updated_at=stamp,published_at=stamp)
    entry['data']={'subject_root':'web-tech/web-technology','section_path':'web-tech/web-technology/project','content_format':'html','seo_ready':False,'kind':'project','author_path':'authors/aitrove-editorial','reading_minutes':8,'related':project['related']}
    body=p(project['intro'])+'<h2>Build contract</h2><ul>'+''.join('<li>'+html.escape(x)+'</li>' for x in project['scope'])+'</ul>'
    body+='<h2>Implementation checkpoint</h2><pre><code class="language-javascript">'+html.escape(project['code'],quote=False)+'</code></pre>'
    body+='<h2>Cost and boundaries</h2>'+p(project['cost'])+'<h2>Failure drill</h2>'+p(project['failure'])
    body+='<h2>Acceptance checks</h2><ul>'+''.join('<li>'+html.escape(x)+'</li>' for x in project['checks'])+'</ul>'
    body+='<h3>Common Mistakes</h3><ul>'+''.join('<li>'+html.escape(x)+'</li>' for x in project['mistakes'])+'</ul>'
    body+='<h2>Related lessons</h2><p>'+'; '.join(link(x) for x in project['related'])+'.</p>'
    entry['body']=body
    entries.append(entry);by_path[entry['path']]=entry

questions=[
 ('What links a queued worker attempt to the original user action?', ['Propagated trace context plus a separate durable operation ID','A case note placed in every span','An authorization decision based on the trace ID'], 'Trace context helps correlate work across boundaries. A stable business operation ID persists across retries and remains available when tracing is sampled or unavailable.'),
 ('Does an incoming trace identifier authorize a case write?', ['No, it is untrusted correlation data','Yes, if it has the expected length','Yes, if a worker can read it'], 'Correlation headers can be supplied by callers. The server must authenticate and authorize every write independently of tracing metadata.'),
 ('When is an accepted asynchronous case save good for a completion SLO?', ['After its final state is visible within the chosen deadline','Immediately after the API returns 202','As soon as the queue receives a message'], 'A user-journey indicator should measure the completed task, not only initial acceptance. Pending and failed terminal jobs need distinct treatment.'),
 ('Which metric label set stays bounded as case volume grows?', ['Route template, release, and outcome category','Case ID, email, and raw URL','Unique operation ID and note text'], 'Bounded categories keep metric-series count manageable. Detailed identifiers belong, if needed, in access-controlled short-retention events rather than metric labels.'),
 ('What must be checked before rolling back a receipt worker?', ['Whether old code can read current messages and data','Only whether the error chart is green','Only whether the previous binary exists'], 'Rollback can worsen an incident if the previous consumer cannot decode messages or schema changes produced by the current release.'),
 ('What proves recovery after a queue-worker failure?', ['Fresh user journeys and terminal outcomes for the existing backlog','No new HTTP 500s for one minute','A quiet alert after writes are paused'], 'Containment can stop new errors while leaving accepted operations unresolved. Recovery evidence must include pending work and the exact failed journey.'),
 ('What should a cross-tab message contain after a private case changes?', ['A scoped invalidation hint followed by an authorized server read','The entire private case record as permanent truth','A new authorization token for the receiving tab'], 'Browser messages are transient. A narrow hint preserves unsaved edits and prompts a current server read under the receiving tab’s authorization.'),
 ('How does a tab recover from a message missed while it was closed?', ['Revalidate on return or before a sensitive write','Assume all broadcasts were retained','Reuse its old version forever'], 'Same-origin browser channels are not durable logs. Focus and route return are opportunities to fetch current server state.'),
 ('What happens after an offline write commits but its response is lost?', ['Replay the same stable idempotency key','Create a fresh key for every retry','Mark it rejected without asking the server'], 'A stable operation identity lets the server return the original result and avoid duplicate audit entries or notifications after an uncertain response.'),
 ('What should a queued edit show after a 412 response?', ['Conflicted with local intent retained for review','Saved because connectivity returned','Queued forever with automatic retries'], 'A version precondition failure is a conflict, not a transient network problem. Preserve the local edit and compare it with the current server state.'),
 ('What should the client do when a live delta sequence has a gap?', ['Fetch a new scoped snapshot or supported replay range','Silently skip the missing change','Reuse a cursor from another filter'], 'A missing delta can make the view incorrect. Resume only from a valid server position and rebuild from a fresh snapshot when history is unavailable.'),
 ('Does an active presence indicator lock the record?', ['No; presence expires and durable writes still require server versions','Yes, until the browser sends a perfect disconnect event','Yes, if the device clock is ahead'], 'Presence is an advisory short-lived signal. Exclusive ownership needs a separate server lease, and concurrent writes require a versioned conflict policy.')
]
quiz_path='quizzes/web-development-operations-sync-decisions'
assert quiz_path not in by_path
quiz=copy.deepcopy(by_path['quizzes/web-development-streams-interactions-decisions'])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'aitrove:'+quiz_path)),path=quiz_path,title='Web Development: operations and sync decisions quiz',summary='Twelve explained decisions about traces, SLOs, telemetry, containment, tabs, offline replay, cursors, and presence.',sort_order=1145,created_at=stamp,updated_at=stamp,published_at=stamp)
def question(index,item):
    prompt,options,explanation=item
    shift=index%3
    return {'prompt':prompt,'options':options[shift:]+options[:shift],'answer':(0-shift)%3,'explanation':explanation}
quiz['data']={'subject_root':'web-tech/web-technology','section_path':'web-tech/quizzes','content_format':'html','seo_ready':False,'questions':[question(i,item) for i,item in enumerate(questions)]}
quiz['body']=p(quiz['summary']+' Choose an answer, inspect its explanation, and revisit the affected contract.')
quiz['body']+='<h2>Related lessons</h2><p>'+'; '.join(link(x) for project in projects for x in project['related'][:4])+'.</p>'
entries.append(quiz);by_path[quiz_path]=quiz
project_hub=by_path['web-tech/web-technology/project']
project_hub['data']['modules'][0]['lessons'].extend(x['path'] for x in projects)
project_hub['body']+='<h2>Operations and synchronization projects</h2><ul>'+''.join('<li>'+link(x['path'])+' — '+html.escape(x['summary'])+'</li>' for x in projects)+'</ul>'
project_hub['summary']='Build and verify twenty-six projects across browser, API, data, identity, search, quality, rendering, forms, navigation, delivery, streaming, accessibility, operations, synchronization, privacy, offline, live, and release contracts.'
project_hub['updated_at']=stamp
quiz_hub=by_path['web-tech/quizzes']
quiz_hub['data']['modules'][0]['lessons'].append(quiz_path)
quiz_hub['body']+='<h2>Operations and synchronization checks</h2><p>'+link(quiz_path)+' — '+html.escape(quiz['summary'])+'</p>'
quiz_hub['updated_at']=stamp
for hub_path,project_path in [('web-tech/production-signals-and-incident-decisions',projects[0]['path']),('web-tech/cross-tab-and-offline-data-coordination',projects[1]['path'])]:
    hub=by_path[hub_path]
    hub['body']+='<h2>Practice path</h2><p>Build '+link(project_path)+' and check decisions in '+link(quiz_path)+'.</p>'
    hub['updated_at']=stamp
for entry in entries:
    if entry['type']!='article' or entry['data'].get('section_path') not in {'web-tech/production-signals-and-incident-decisions','web-tech/cross-tab-and-offline-data-coordination'}:continue
    project_path=projects[0]['path'] if entry['data']['section_path']=='web-tech/production-signals-and-incident-decisions' else projects[1]['path']
    entry['body']+='<h2>Apply and check</h2><p>Build '+link(project_path)+' and review '+link(quiz_path)+'.</p>'
    entry['data']['related'].extend([project_path,quiz_path]);entry['updated_at']=stamp
root_entry=by_path['web-tech/web-technology']
root_entry['body']+='<h2>Operations and sync practice</h2><p>Apply the production and data-coordination contracts with '+link(projects[0]['path'])+' and '+link(projects[1]['path'])+'.</p>'
root_entry['updated_at']=stamp
fixture.write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'new_projects':len(projects),'new_quizzes':1,'new_questions':len(questions)}))
