"""Add live case board project and assessment drafts."""
import copy
import datetime
import html
import json
import uuid
from pathlib import Path

root=Path(__file__).resolve().parents[1]
fixture=root/'src/data/fixtures.json'
entries=json.loads(fixture.read_text())
by_path={entry['path']:entry for entry in entries}
stamp=datetime.datetime.now(datetime.UTC).isoformat()
def p(value):return '<p>'+html.escape(value)+'</p>'
def link(path):
    assert path in by_path,path
    return '<a href="/'+html.escape(path,quote=True)+'">'+html.escape(by_path[path]['title'])+'</a>'
hub_path='web-tech/realtime-connection-and-event-delivery'
lessons=['web-tech/websocket-handshake-session-and-channel-authorization','web-tech/event-sequence-replay-and-gap-reconciliation',
 'web-tech/socket-fanout-backpressure-and-slow-consumers','web-tech/presence-expiry-heartbeats-and-connection-drain']
project_path='web-tech/live-permit-case-board-project'
assert project_path not in by_path
project=copy.deepcopy(by_path['web-tech/case-intake-end-to-end-project'])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'aitrove:'+project_path)),path=project_path,
 title='Project: live permit case board',summary='Build an authorized case channel with replay, bounded fanout, expiring presence, and deploy-safe reconnect.',
 sort_order=3510,created_at=stamp,updated_at=stamp,published_at=stamp)
project['data']={'subject_root':'web-tech/web-technology','section_path':'web-tech/web-technology/project',
 'content_format':'html','seo_ready':False,'kind':'project','author_path':'authors/aitrove-editorial',
 'reading_minutes':9,'related':[hub_path]+lessons}
project['body']=p('Build a live board for permit case 29. Reviewer 47 belongs to organization 6; reviewer 62 cannot view that case. The browser opens one secure socket, subscribes to the case after the server checks current permission, and receives committed case versions. If the connection drops, it reauthenticates and asks for replay; an expired cursor triggers a fresh authorized snapshot. A mobile reviewer may fall behind a burst, so the server caps queued bytes and lets that client recover durable state rather than buffering indefinitely. Presence indicates recent activity and expires when a sleeping device stops sending evidence. A rolling deployment must drain old connections without losing committed events.')
project['body']+='<h2>Build contract</h2><ul>'+''.join('<li>'+html.escape(item)+'</li>' for item in [
 'Validate browser origin and session at upgrade, then authorize every private subscribe or mutation message against the current case.',
 'Persist versioned case changes before fanout; deduplicate events, reconcile gaps, and deny replay after permission revocation.',
 'Cap queue bytes and message size, expire presence leases, and reconnect with jitter after a bounded server drain.'])+'</ul>'
project['body']+='<h2>Implementation checkpoint</h2><pre><code class="language-javascript">'+html.escape('function nextCaseStep(currentVersion, eventVersion) {\n  if (eventVersion <= currentVersion) return "ignore-old";\n  return eventVersion === currentVersion + 1 ? "apply" : "load-snapshot";\n}\nconsole.log(nextCaseStep(47, 49));\n// Output: load-snapshot',quote=False)+'</code></pre>'
project['body']+='<h2>Cost and boundaries</h2>'+p('For S subscribers, publishing one event requires O(S) delivery attempts unless a broker changes the distribution path. Memory must remain bounded per connection; a 63-kilobyte queue cap across 900 sockets is already a material budget. Durable replay storage grows with retained events, while presence heartbeats add traffic proportional to connection count and interval. Measure publish-to-display latency, queue bytes, replay depth, gap frequency, revoked-event delay, false-presence duration, and reconnection surge during deployment. Keep full private messages and session material out of broad logs. A socket result is a delivery attempt; the committed case record remains the source of truth.')
project['body']+='<h2>Failure drill</h2>'+p('Try an unauthorized browser origin with a valid cookie, then a valid connection that subscribes to a foreign-tenant case. Revoke reviewer 47 while a connection stays open and publish a private event. Deliver version 49 before 48, duplicate version 50, and expire the replay cursor; the final board must match an authorized snapshot. Throttle one recipient during a burst of 63 updates per second and confirm its queue stays bounded while fast recipients continue. Sleep a laptop without a close frame and watch presence expire. Drain a node with 900 active clients; clients reconnect with jitter, current permission, and no missing durable changes.')
project['body']+='<h2>Acceptance checks</h2><ul>'+''.join('<li>'+html.escape(item)+'</li>' for item in [
 'Unauthorized origins, sessions, and channel requests receive no private events.',
 'Reordered, duplicate, missing, and expired-history events converge on current case state.',
 'One slow consumer cannot grow memory without bound or block fast consumers.',
 'Presence expiry and rolling drain do not become edit locks or erase committed changes.'])+'</ul>'
project['body']+='<h3>Common Mistakes</h3><ul><li>Checking permission only when the socket opens.</li><li>Treating arrival order as the case version order.</li><li>Keeping an unlimited queue for slow connections.</li></ul>'
project['body']+='<h2>Related lessons</h2><p>'+'; '.join(link(path) for path in project['data']['related'])+'.</p>'
entries.append(project);by_path[project_path]=project

quiz_path='quizzes/web-development-realtime-delivery-contracts'
assert quiz_path not in by_path
questions=[
 ('Does an allowed browser Origin prove the user identity?', ['Yes, always','No; authenticate the session too','Only for private channels'],1,'Origin validation helps prevent unwanted browser sites, but a nonbrowser client can send that field and still needs identity checks.'),
 ('A signed-in socket asks for a foreign-tenant case. What decides admission?', ['Current object permission','The connection age','The user-supplied tenant field'],0,'A valid connection is not a grant for every case; the server must authorize each private channel.'),
 ('A reviewer loses case access while the socket remains open. What must stop?', ['Only button display','Only new HTTP requests','Future private case events'],2,'Revocation has to reach active channel membership within a measured bound, not just the next page load.'),
 ('Case version 49 arrives when the page holds 47. What is the safe response?', ['Apply 49 and assume 48','Replay or load a current snapshot','Set the version back to 46'],1,'A version gap means the client cannot infer the missing change from arrival order alone.'),
 ('A duplicate version 50 arrives after 50 was applied. What should happen?', ['Ignore the duplicate','Apply every side effect again','Delete version 49'],0,'Stable event identity and version checks prevent duplicate delivery from duplicating UI or effects.'),
 ('A replay cursor is older than retained history. What should the server or client do?', ['Return an empty feed as proof of no change','Guess the missing events','Signal the gap and load an authorized snapshot'],2,'A retained log cannot reconstruct events it no longer holds; a current snapshot closes the gap.'),
 ('One recipient accumulates queued bytes during a burst. What should be bounded?', ['Only its screen width','Its per-connection queue and message age','The case title length'],1,'An unbounded send queue can consume memory and leave that recipient far behind current state.'),
 ('Which message may be dropped under a documented slow-consumer policy?', ['An ephemeral presence hint','A promised durable case comment','A committed audit change with no replay'],0,'Ephemeral hints can expire; durable history requires storage-backed recovery if live delivery fails.'),
 ('Why can fanout cost grow with subscriber count?', ['Every browser shares one memory buffer','The browser sends the event','Each subscriber needs a delivery attempt'],2,'One published event can cause a send or queue operation for every subscribed connection.'),
 ('A device sleeps without sending a close frame. How should presence behave?', ['Expire after its lease','Stay online forever','Lock editing for everyone'],0,'Presence is time-bounded evidence and must not become a durable fact or edit permission.'),
 ('What should a server instance do before rolling socket shutdown?', ['Kill storage first','Stop new upgrades and drain existing connections','Delete event history'],1,'A bounded drain gives clients a chance to reconnect while committed event history remains available.'),
 ('After reconnect, which policy governs access to missed case events?', ['The old connection permission','The cursor string alone','Current session and case authorization'],2,'A replay cursor does not grant access after logout or record reassignment; permission must be checked again.'),
]
quiz=copy.deepcopy(by_path['quizzes/web-development-browser-contracts'])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'aitrove:'+quiz_path)),path=quiz_path,
 title='Web Development: realtime delivery contracts quiz',
 summary='Twelve explained choices about socket admission, replay, slow consumers, and presence expiry.',
 sort_order=3511,created_at=stamp,updated_at=stamp,published_at=stamp)
quiz['data']={'subject_root':'web-tech/web-technology','section_path':'web-tech/quizzes','content_format':'html','seo_ready':False,
 'questions':[{'prompt':prompt,'options':options,'answer':answer,'explanation':explanation} for prompt,options,answer,explanation in questions]}
quiz['body']=p(quiz['summary']+' Choose an answer, inspect its explanation, and return to the related lesson for a missed boundary.')
quiz['body']+='<h2>Related lessons</h2><p>'+'; '.join(link(path) for path in [hub_path]+lessons+[project_path])+'.</p>'
entries.append(quiz);by_path[quiz_path]=quiz
project_hub=by_path['web-tech/web-technology/project']
project_hub['data']['modules'][0]['lessons'].append(project_path)
project_hub['body']+='<h2>Realtime board project</h2><p>'+link(project_path)+' — '+html.escape(project['summary'])+'</p>'
project_hub['updated_at']=stamp
quiz_hub=by_path['web-tech/quizzes']
quiz_hub['data']['modules'][0]['lessons'].append(quiz_path)
quiz_hub['body']+='<h2>Realtime delivery check</h2><p>'+link(quiz_path)+' — '+html.escape(quiz['summary'])+'</p>'
quiz_hub['updated_at']=stamp
hub=by_path[hub_path]
hub['body']+='<h2>Practice and check</h2><p>Build '+link(project_path)+' and review '+link(quiz_path)+'.</p>'
hub['updated_at']=stamp
for path in lessons:
    entry=by_path[path]
    entry['body']+='<h2>Apply and check</h2><p>Build '+link(project_path)+' and review '+link(quiz_path)+'.</p>'
    entry['data']['related'].extend([project_path,quiz_path])
    entry['updated_at']=stamp
root_entry=by_path['web-tech/web-technology']
root_entry['body']+='<h2>Realtime delivery practice</h2><p>'+link(project_path)+'; '+link(quiz_path)+'.</p>'
root_entry['updated_at']=stamp
fixture.write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'new_projects':1,'new_quizzes':1,'new_questions':len(questions),'answer_positions':{str(i):sum(q[2]==i for q in questions) for i in range(3)}}))
