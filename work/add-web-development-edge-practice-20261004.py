"""Add edge and origin project plus assessment drafts."""
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
hub_path='web-tech/edge-runtime-and-origin-boundaries'
lessons=['web-tech/edge-request-normalization-and-origin-trust','web-tech/edge-compute-budgets-and-upstream-fanout',
 'web-tech/edge-cache-locality-invalidation-and-private-scope','web-tech/edge-origin-write-routing-and-consistency']
project_path='web-tech/edge-permit-case-delivery-project'
assert project_path not in by_path
project=copy.deepcopy(by_path['web-tech/case-intake-end-to-end-project'])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'aitrove:'+project_path)),path=project_path,
 title='Project: edge permit case delivery',summary='Put a bounded edge layer before public map assets and private case operations without weakening origin authority.',
 sort_order=3410,created_at=stamp,updated_at=stamp,published_at=stamp)
project['data']={'subject_root':'web-tech/web-technology','section_path':'web-tech/web-technology/project',
 'content_format':'html','seo_ready':False,'kind':'project','author_path':'authors/aitrove-editorial',
 'reading_minutes':9,'related':[hub_path]+lessons}
project['body']=p('Build a thin edge layer for a permit portal with public district map tiles and private case 29. The browser may request tiles from several regions, while case writes belong to one authoritative origin. Reviewer 47 has access to organization 6 but not organization 9. Canonicalize request paths, remove viewer-supplied internal headers, and keep object authorization at origin. The edge has a strict upstream-call budget and must return a usable case summary when an optional thumbnail fails. Public tiles use versioned URLs; private case images bypass shared caches. A save reports committed state only after origin evidence and gives the next read a minimum version.')
project['body']+='<h2>Build contract</h2><ul>'+''.join('<li>'+html.escape(item)+'</li>' for item in [
 'Reject ambiguous paths, forged forwarding context, and direct-origin requests that lack protected identity.',
 'Cap upstream fanout, elapsed time, and buffered bytes; fail closed when permission lookup fails while allowing optional image fallback.',
 'Test public tile revision across two edge locations, private cache bypass, idempotent origin writes, and read-after-write version behavior.'])+'</ul>'
project['body']+='<h2>Implementation checkpoint</h2><pre><code class="language-javascript">'+html.escape('function responseMayUsePublicCache(responseClass, authorized) {\n  return responseClass === "versioned-public-tile" && !authorized;\n}\nconsole.log(responseMayUsePublicCache("private-case-image", true));\n// Output: false',quote=False)+'</code></pre>'
project['body']+='<h2>Cost and boundaries</h2>'+p('Path normalization costs O(L) for path length L. With F upstream calls and R retries, a careless edge route can generate O(F × R) origin work for each browser request. Cache variants consume storage per revision and language, while a mixed private key risks disclosure. Compare full browser-to-response p95 latency with a regional origin baseline; a nearby edge is not a win when it waits on distant services. Measure subrequests, bytes buffered, public hit rate by location, stale revision age, private cache bypass, duplicate effects, and the longest post-write stale read. Do not put private paths or tokens into broad cache and telemetry keys.')
project['body']+='<h2>Failure drill</h2>'+p('Send encoded separators and a forged tenant header, then call origin directly. Slow the assignment service beyond its deadline and fail an optional thumbnail. Warm two edge locations with style revision 29, purge only one, then release revision 30 under distinct URLs. Change reviewer 47 permission after the edge has made a routing decision; origin must deny case 29. Commit a held-state write, lose its response, and retry with the same key. Return an old version from the nearest replica and show a pending state or route to fresh data. Promote a second origin while the first returns and prove only one can accept further writes.')
project['body']+='<h2>Acceptance checks</h2><ul>'+''.join('<li>'+html.escape(item)+'</li>' for item in [
 'No viewer-supplied proxy field can grant origin access, and private reads use current object policy.',
 'An optional service failure does not hide a successful authorized case summary.',
 'Public cache revisions are location-safe; private representations cannot cross accounts.',
 'One retried mutation yields one committed effect, and a stale read is never presented as the final saved state.'])+'</ul>'
project['body']+='<h3>Common Mistakes</h3><ul><li>Calling a local purge a global invalidation.</li><li>Returning save success before origin commit.</li><li>Assuming edge proximity compensates for unbounded distant fanout.</li></ul>'
project['body']+='<h2>Related lessons</h2><p>'+'; '.join(link(path) for path in project['data']['related'])+'.</p>'
entries.append(project);by_path[project_path]=project

quiz_path='quizzes/web-development-edge-origin-contracts'
assert quiz_path not in by_path
questions=[
 ('A viewer sends an internal tenant header to the edge. What should happen?', ['Forward it unchanged','Strip or overwrite it before protected origin handling','Use it as a session'],1,'An ordinary viewer header is not trusted context; the edge must construct protected origin metadata itself.'),
 ('Where must current case-level permission still be checked?', ['At the authoritative origin boundary','Only in the browser menu','Only when a cache miss occurs'],0,'The origin owns the record and must deny a stale or forged edge decision before releasing private bytes.'),
 ('Edge and origin decode one path differently. What is the safe result?', ['Use whichever route is public','Retry with more decoding','Reject the ambiguous request'],2,'A request must not cross two different route identities; a shared canonical rule or rejection prevents policy disagreement.'),
 ('An edge handler calls a distant database for every request. What determines its value?', ['Only edge CPU time','Full request latency and dependency cost','The number of edge locations'],1,'Moving the first hop closer cannot remove the later distant database trip or fanout cost.'),
 ('An optional thumbnail times out while case authorization succeeds. What should the page do?', ['Show the case with a thumbnail fallback','Grant extra access','Report the whole case as unauthorized'],0,'An optional visual dependency can fail separately; the authorized case summary should remain usable.'),
 ('Permission lookup fails. What may the edge return for a private case?', ['Cached private bytes','A public copy','A denial or unavailable state'],2,'An unknown permission result cannot be turned into an allowed private response.'),
 ('A cache delete runs in one edge location. What can it prove?', ['Every location is empty','Only the documented local scope was cleared','All browser caches cleared'],1,'Cache API behavior may be local; global invalidation needs its own tested mechanism or versioned identity.'),
 ('Which asset is easiest to cache across regions?', ['A public tile with a revisioned URL','A private reviewer note','A signed-in case image under one shared key'],0,'A revisioned public tile has stable identity and no per-user permission decision.'),
 ('A response varies by language but the cache key ignores language. What risk follows?', ['Lower storage only','More CPU only','One visitor may receive the wrong representation'],2,'Every input that changes response representation needs a matching cache identity or bypass rule.'),
 ('When can the edge report a mutation as committed?', ['When it queues the request','After authoritative durable commit evidence','As soon as the browser sends it'],1,'Receipt or queue admission is different from a durable origin write; responses must name the actual state.'),
 ('A retry follows a lost response after a successful write. What prevents two effects?', ['A stable idempotency identity at the owner','A new random key each retry','A stale edge cache'],0,'The owner can recognize the repeated operation and return its recorded outcome without repeating the side effect.'),
 ('A read replica returns version 47 after a version-48 save. What should the UI do?', ['Show 47 as final','Delete version 48','Wait, route to fresh data, or show pending state'],2,'A post-write read must not present an older version as the committed result the user just saved.'),
]
quiz=copy.deepcopy(by_path['quizzes/web-development-browser-contracts'])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'aitrove:'+quiz_path)),path=quiz_path,
 title='Web Development: edge and origin contracts quiz',
 summary='Twelve explained choices about edge request trust, budgets, caching, and authoritative writes.',
 sort_order=3411,created_at=stamp,updated_at=stamp,published_at=stamp)
quiz['data']={'subject_root':'web-tech/web-technology','section_path':'web-tech/quizzes','content_format':'html','seo_ready':False,
 'questions':[{'prompt':prompt,'options':options,'answer':answer,'explanation':explanation} for prompt,options,answer,explanation in questions]}
quiz['body']=p(quiz['summary']+' Choose a response, inspect its explanation, and reopen the linked lesson for that boundary.')
quiz['body']+='<h2>Related lessons</h2><p>'+'; '.join(link(path) for path in [hub_path]+lessons+[project_path])+'.</p>'
entries.append(quiz);by_path[quiz_path]=quiz
project_hub=by_path['web-tech/web-technology/project']
project_hub['data']['modules'][0]['lessons'].append(project_path)
project_hub['body']+='<h2>Edge and origin project</h2><p>'+link(project_path)+' — '+html.escape(project['summary'])+'</p>'
project_hub['updated_at']=stamp
quiz_hub=by_path['web-tech/quizzes']
quiz_hub['data']['modules'][0]['lessons'].append(quiz_path)
quiz_hub['body']+='<h2>Edge and origin check</h2><p>'+link(quiz_path)+' — '+html.escape(quiz['summary'])+'</p>'
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
root_entry['body']+='<h2>Edge and origin practice</h2><p>'+link(project_path)+'; '+link(quiz_path)+'.</p>'
root_entry['updated_at']=stamp
fixture.write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'new_projects':1,'new_quizzes':1,'new_questions':len(questions),'answer_positions':{str(i):sum(q[2]==i for q in questions) for i in range(3)}}))
