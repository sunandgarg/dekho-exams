"""Add API migration project and assessment drafts."""
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
hub_path='web-tech/api-contract-evolution-and-client-migration'
lessons=['web-tech/response-shape-evolution-and-unknown-values','web-tech/api-version-selection-and-representation-scope',
         'web-tech/deprecation-sunset-and-consumer-evidence','web-tech/consumer-contract-matrix-and-expand-contract-release']
project_path='web-tech/permit-api-client-migration-project'
assert project_path not in by_path
project=copy.deepcopy(by_path['web-tech/case-intake-end-to-end-project'])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'aitrove:'+project_path)),path=project_path,
 title='Project: permit API client migration',summary='Move case status and duration contracts across two browser releases and a monthly integration.',
 sort_order=3310,created_at=stamp,updated_at=stamp,published_at=stamp)
project['data']={'subject_root':'web-tech/web-technology','section_path':'web-tech/web-technology/project',
 'content_format':'html','seo_ready':False,'kind':'project','author_path':'authors/aitrove-editorial',
 'reading_minutes':9,'related':[hub_path]+lessons}
project['body']=p('Migrate a permit case API while release 47 remains cached in browsers, release 63 rolls out by region, and district 29 runs a monthly export. The old representation reports durationHours and three case statuses. The new representation uses durationMinutes and introduces awaiting-evidence. Build one domain case loader with current permission checks, then wrap it in two explicit representation adapters. A new server must coexist with an old client before any field is removed. The old client must show a safe read-only state for an unfamiliar status. The project ends only after a full consumer cycle and a reversible old-route shutdown drill.')
project['body']+='<h2>Build contract</h2><ul>'+''.join('<li>'+html.escape(item)+'</li>' for item in [
 'Define both response shapes, units, null rules, error behavior, version selection, and version-aware cache identity.',
 'Run release-47 and release-63 clients against old, expanded, and contracted server fixtures; include mixed-region rollout and rollback.',
 'Track daily and monthly consumer use, announce old-route retirement, and rehearse a reversible shutdown without bypassing permission checks.'])+'</ul>'
project['body']+='<h2>Implementation checkpoint</h2><pre><code class="language-javascript">'+html.escape('function durationForClient(minutes, clientVersion) {\n  if (clientVersion === "v1" && minutes % 60 === 0) return { durationHours: minutes / 60 };\n  if (clientVersion === "v2") return { durationMinutes: minutes };\n  throw new Error("Unsupported duration representation");\n}\nconsole.log(JSON.stringify(durationForClient(180, "v2")));\n// Output: {"durationMinutes":180}',quote=False)+'</code></pre>'
project['body']+='<h2>Cost and boundaries</h2>'+p('The two adapters add O(N) serialization work for an N-record page, while a mixed-version cache lowers hit rate. Keep domain authorization shared so the old API cannot become a permission bypass. A full client-server test matrix has O(C × S) combinations for C supported clients and S active server phases; a stated support window keeps that number bounded. The monthly job sets the observation period for retirement. Measure actual calls by client identity, old-route error rate, status-decoder failures, response bytes, and rollback time. Store no tokens or private record IDs in the migration dashboard.')
project['body']+='<h2>Failure drill</h2>'+p('Deploy the new client to region A while region B still returns only the old shape. The new client must stay readable or wait behind a rollout gate. Change an old field from hours to minutes without renaming it and verify a contract test blocks the release. Send awaiting-evidence to release 47; its Close action must be unavailable. Mix version-selected responses behind one cache key and catch the wrong representation. Retire v1 after a short quiet period, then run district 29’s monthly export; the drill should reveal why a full cycle and a registered owner matter. Roll back the route toggle and confirm both versions still enforce current case permission.')
project['body']+='<h2>Acceptance checks</h2><ul>'+''.join('<li>'+html.escape(item)+'</li>' for item in [
 'Both supported clients show safe state and correct duration units in every active server phase.',
 'Version-selected responses cannot cross a shared cache or pagination cursor boundary.',
 'A monthly consumer receives migration notice and passes its replacement export test.',
 'A revoked reviewer is denied through every version before and after rollback.'])+'</ul>'
project['body']+='<h3>Common Mistakes</h3><ul><li>Testing only the latest client and server together.</li><li>Changing field meaning without a new representation.</li><li>Equating deprecation notice with a safe shutdown.</li></ul>'
project['body']+='<h2>Related lessons</h2><p>'+'; '.join(link(path) for path in project['data']['related'])+'.</p>'
entries.append(project);by_path[project_path]=project

quiz_path='quizzes/web-development-api-contract-migration'
assert quiz_path not in by_path
questions=[
 ('A new server emits a new status enum member. What must the oldest supported client do?', ['Treat it as open','Use a safe unknown state','Silently remove the case'],1,'A new member can break an old exhaustive decoder; the fallback must avoid unjustified actions.'),
 ('Which change clearly alters a field contract?', ['Changing durationHours to mean minutes','Adding a documented optional field','Adding an unrelated route'],0,'A familiar name with a changed unit silently changes meaning and needs a distinct representation.'),
 ('Can an API remove an old required field when the latest bundle passes?', ['Yes, deployments are atomic','Yes, if the server builds','No; supported cached and offline clients may still need it'],2,'The supported client lifetime, not the latest rollout, governs contraction.'),
 ('What should two API versions share?', ['A mutable response shape','Current domain and permission policy','Independent authorization rules'],1,'Thin adapters may differ in representation, but current object-level permission must be common.'),
 ('A version is selected in a request header. What cache concern follows?', ['The cache must distinguish representations by that selector','The cache can key on case ID alone','Caching is impossible'],0,'A response that varies with version selection needs a cache identity that reflects the selector.'),
 ('Why reject a v2 cursor on a v1 list when cursor meaning differs?', ['It reduces SQL cost','It hides all records','It prevents an incompatible page boundary'],2,'A cursor encodes ordering and scope assumptions that may be version-specific.'),
 ('What does deprecation tell a consumer?', ['The route is already off','New dependencies should avoid it while current behavior remains','The schema changed immediately'],1,'Deprecation is a lifecycle signal, not an instant change in resource behavior.'),
 ('Why is a seven-day quiet period weak evidence for a monthly export?', ['The job has not completed a full usage cycle','Headers cannot be sent','The route is public'],0,'A low-frequency consumer can be invisible during a shorter observation window.'),
 ('Which telemetry field should be excluded from migration metrics?', ['A coarse client cohort','A registered integration identity','A raw authorization token'],2,'Consumer counting does not require credentials in labels or logs. Use trusted client identity and coarse cohorts.'),
 ('What does an expand-contract rollout test first?', ['Old and new clients against intermediate server phases','Only the final server against the newest client','Only schema text'],0,'Intermediate phases are observable during regional rollout and cached-client overlap.'),
 ('Two dual-written fields disagree. What is needed?', ['Keep both as independent truth','A canonical writer and divergence check','Return whichever serializes first'],1,'Independent truth lets rollback or old clients read stale values. Pick one canonical source and compare adapters.'),
 ('A supported old client fails against one active region. What is the release result?', ['Proceed because another region passed','Hide the region in monitoring','Stop or adjust rollout until the active matrix is safe'],2,'Every supported client can meet every active server phase unless routing guarantees otherwise.'),
]
quiz=copy.deepcopy(by_path['quizzes/web-development-browser-contracts'])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'aitrove:'+quiz_path)),path=quiz_path,
 title='Web Development: API contract migration quiz',
 summary='Twelve explained choices about response evolution, versions, retirement, and release matrices.',
 sort_order=3311,created_at=stamp,updated_at=stamp,published_at=stamp)
quiz['data']={'subject_root':'web-tech/web-technology','section_path':'web-tech/quizzes','content_format':'html','seo_ready':False,
 'questions':[{'prompt':prompt,'options':options,'answer':answer,'explanation':explanation} for prompt,options,answer,explanation in questions]}
quiz['body']=p(quiz['summary']+' Check one answer at a time and return to the linked lesson for a failed boundary.')
quiz['body']+='<h2>Related lessons</h2><p>'+'; '.join(link(path) for path in [hub_path]+lessons+[project_path])+'.</p>'
entries.append(quiz);by_path[quiz_path]=quiz
project_hub=by_path['web-tech/web-technology/project']
project_hub['data']['modules'][0]['lessons'].append(project_path)
project_hub['body']+='<h2>API migration project</h2><p>'+link(project_path)+' — '+html.escape(project['summary'])+'</p>'
project_hub['updated_at']=stamp
quiz_hub=by_path['web-tech/quizzes']
quiz_hub['data']['modules'][0]['lessons'].append(quiz_path)
quiz_hub['body']+='<h2>API migration check</h2><p>'+link(quiz_path)+' — '+html.escape(quiz['summary'])+'</p>'
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
root_entry['body']+='<h2>API migration practice</h2><p>'+link(project_path)+'; '+link(quiz_path)+'.</p>'
root_entry['updated_at']=stamp
fixture.write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'new_projects':1,'new_quizzes':1,'new_questions':len(questions),'answer_positions':{str(i):sum(q[2]==i for q in questions) for i in range(3)}}))
