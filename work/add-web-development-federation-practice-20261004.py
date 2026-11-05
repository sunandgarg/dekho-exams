"""Add a federated sign-in project and assessment drafts."""
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

hub_path='web-tech/federated-identity-and-session-lifecycle'
lessons=['web-tech/authorization-code-pkce-and-callback-binding','web-tech/id-token-verification-and-stable-account-identity',
         'web-tech/refresh-token-rotation-and-app-session-boundary','web-tech/federated-account-linking-logout-and-revocation']
project_path='web-tech/federated-permit-reviewer-sign-in-project'
assert project_path not in by_path
project=copy.deepcopy(by_path['web-tech/case-intake-end-to-end-project'])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'aitrove:'+project_path)),path=project_path,
 title='Project: federated permit reviewer sign-in',summary='Build a two-provider sign-in flow with one-use callbacks, verified identity, controlled renewal, and safe linking.',
 sort_order=3210,created_at=stamp,updated_at=stamp,published_at=stamp)
project['data']={'subject_root':'web-tech/web-technology','section_path':'web-tech/web-technology/project',
 'content_format':'html','seo_ready':False,'kind':'project','author_path':'authors/aitrove-editorial',
 'reading_minutes':9,'related':[hub_path]+lessons}
project['body']=p('Build the permit-reviewer sign-in path for two configured identity issuers. A reviewer may open both sign-in choices in separate tabs. The app must associate each callback with exactly one initiating browser session and must create a local session only after verifying an identity assertion addressed to this application. Reviewer 47 can access organization 6, while reviewer 62 belongs to organization 9; shared email text cannot merge their accounts. The project includes session renewal, local sign-out, and an explicit ceremony for adding a second provider. Use a maintained identity library for signatures and protocol messages. The small checkpoint below illustrates only local account-key construction; it is not a token verifier.')
project['body']+='<h2>Build contract</h2><ul>'+''.join('<li>'+html.escape(item)+'</li>' for item in [
 'Store one expiring attempt per state with browser-session identity, issuer, verifier, nonce, and redirect URI; consume it atomically before code exchange.',
 'Verify signature and required identity claims through a trusted provider configuration, then map issuer and subject to a local account without email auto-merge.',
 'Give browser clients revocable app sessions, coordinate token renewal, require current record permission, and make linking and unlinking explicit account actions.'])+'</ul>'
project['body']+='<h2>Implementation checkpoint</h2><pre><code class="language-javascript">'+html.escape('function sameExternalIdentity(left, right) {\n  return left.issuer === right.issuer && left.subject === right.subject;\n}\nconsole.log(sameExternalIdentity({ issuer: "issuer-6", subject: "reviewer-47" }, { issuer: "issuer-9", subject: "reviewer-47" }));\n// Output: false',quote=False)+'</code></pre>'
project['body']+='<h2>Cost and boundaries</h2>'+p('Each login holds O(1) short-lived attempt state and performs a token-endpoint round trip. Active app sessions add bounded storage and a lookup on protected requests. A unique issuer-and-subject index keeps account mapping efficient; a per-token-family renewal lock prevents 47 simultaneous browser requests from spending the same rotating token. Measure provider calls per renewal, callback failures by category, local logout-to-denial time, and account-link conflicts. Keep raw codes, verifiers, tokens, and private profile claims out of routine logs. A passing local sign-in test says nothing about organization 6 case authorization unless a direct API test checks it.')
project['body']+='<h2>Failure drill</h2>'+p('Complete two tab callbacks in reverse order, replay one callback, and attempt a wrong-issuer exchange. Supply an expired or wrong-audience identity token through the verifier test fixture. Give two subjects the same email, then try to link one already owned by another account. Expire the access token while 47 protected requests arrive and confirm one coordinated refresh. Finally remove reviewer 47 from organization 6, sign out while remote logout is unavailable, and retry a case read from an old tab and a restored page. Each failure must produce a narrow, recoverable result without opening a private record.')
project['body']+='<h2>Acceptance checks</h2><ul>'+''.join('<li>'+html.escape(item)+'</li>' for item in [
 'Only matching unconsumed attempts reach the configured token endpoint.',
 'Wrong signature, issuer, audience, time, or nonce never creates a local session.',
 'Email collision, occupied external identity, stale link, and last-method unlink have explicit outcomes.',
 'Local sign-out and membership removal deny private reads even when provider logout or refresh fails.'])+'</ul>'
project['body']+='<h3>Common Mistakes</h3><ul><li>Assuming OAuth code exchange alone proves the user identity.</li><li>Using an email address as the unique account key.</li><li>Claiming provider-wide logout when only the app session ended.</li></ul>'
project['body']+='<h2>Related lessons</h2><p>'+'; '.join(link(path) for path in project['data']['related'])+'.</p>'
entries.append(project);by_path[project_path]=project

quiz_path='quizzes/web-development-federated-identity-session-contracts'
assert quiz_path not in by_path
questions=[
 ('What binds a returned authorization code to the initiating client?', ['The profile email','The matching PKCE code verifier','The display name'],1,'The code challenge was derived from a verifier kept by the initiating client; the exchange must present that verifier.'),
 ('Which value binds a callback to a specific browser login attempt?', ['State stored with that attempt','The provider logo','The case ID'],0,'An opaque one-use state value connects the redirect to the initiating attempt and browser session.'),
 ('A callback is replayed after a successful exchange. What happens?', ['Create another session','Exchange the code again','Reject the consumed attempt'],2,'Attempt state must be consumed once; replay must not issue another local session.'),
 ('A token body decodes as JSON. Is that proof of identity?', ['Yes, if it has an email','No; signature and contextual claims still need verification','Only when the name matches'],1,'Decoding is not cryptographic validation, and the token must be intended for the configured issuer and client.'),
 ('Which pair should identify a federated account link?', ['Issuer and subject','Email and picture','Audience and display name'],0,'The issuer-subject pair is the stable external identity key for the local account mapping.'),
 ('A valid identity token has the wrong audience. What is the result?', ['Create a read-only account','Ask the browser to fix it','Reject it for this app'],2,'A token addressed to another client cannot establish this application session.'),
 ('Two tabs try one rotating refresh token at once. What helps?', ['Store more copies in local storage','Coordinate one refresh per token family','Ignore the second tab forever'],1,'Serialization prevents parallel spends of one rotating token and gives waiting requests a consistent outcome.'),
 ('Reviewer membership is revoked while their provider token remains valid. What governs a case read?', ['Current local permission policy','The provider token alone','The old page button'],0,'Identity and local record authorization have different lifetimes and checks.'),
 ('May matching email addresses automatically merge two provider subjects?', ['Yes if both are verified','Yes if they share a domain','No; require an explicit safe linking ceremony'],2,'An email collision or reassignment is not consent to merge local histories.'),
 ('When should a link callback be accepted?', ['After any account signs in','Only for the initiating current account and verified fresh provider result','If the browser still has the URL'],1,'The link target, current session, one-use state, and verified external identity must agree.'),
 ('Remote provider logout times out. What can the app still guarantee?', ['Its own session is invalidated','Every device is signed out','All provider tokens are revoked'],0,'Local logout owns the app session; remote provider sessions are separate.'),
 ('Why block unlinking the last usable sign-in method?', ['It makes token exchange slower','It changes the user email','It can leave the account without a recovery path'],2,'The app should require another working credential or defined recovery path before removal.'),
]
quiz=copy.deepcopy(by_path['quizzes/web-development-browser-contracts'])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'aitrove:'+quiz_path)),path=quiz_path,
 title='Web Development: federated identity and session contracts quiz',
 summary='Twelve explained decisions about callbacks, identity claims, renewal, account links, and logout.',
 sort_order=3211,created_at=stamp,updated_at=stamp,published_at=stamp)
quiz['data']={'subject_root':'web-tech/web-technology','section_path':'web-tech/quizzes','content_format':'html','seo_ready':False,
              'questions':[{'prompt':prompt,'options':options,'answer':answer,'explanation':explanation} for prompt,options,answer,explanation in questions]}
quiz['body']=p(quiz['summary']+' Choose a response, inspect its explanation, and revisit the lesson that owns that boundary.')
quiz['body']+='<h2>Related lessons</h2><p>'+'; '.join(link(path) for path in [hub_path]+lessons+[project_path])+'.</p>'
entries.append(quiz);by_path[quiz_path]=quiz
project_hub=by_path['web-tech/web-technology/project']
project_hub['data']['modules'][0]['lessons'].append(project_path)
project_hub['body']+='<h2>Federated identity project</h2><p>'+link(project_path)+' — '+html.escape(project['summary'])+'</p>'
project_hub['updated_at']=stamp
quiz_hub=by_path['web-tech/quizzes']
quiz_hub['data']['modules'][0]['lessons'].append(quiz_path)
quiz_hub['body']+='<h2>Federated identity check</h2><p>'+link(quiz_path)+' — '+html.escape(quiz['summary'])+'</p>'
quiz_hub['updated_at']=stamp
hub=by_path[hub_path]
hub['body']+='<h2>Practice and check</h2><p>Build '+link(project_path)+' and test the boundaries in '+link(quiz_path)+'.</p>'
hub['updated_at']=stamp
for path in lessons:
    entry=by_path[path]
    entry['body']+='<h2>Apply and check</h2><p>Build '+link(project_path)+' and review '+link(quiz_path)+'.</p>'
    entry['data']['related'].extend([project_path,quiz_path])
    entry['updated_at']=stamp
root_entry=by_path['web-tech/web-technology']
root_entry['body']+='<h2>Federated identity practice</h2><p>'+link(project_path)+'; '+link(quiz_path)+'.</p>'
root_entry['updated_at']=stamp
fixture.write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'new_projects':1,'new_quizzes':1,'new_questions':len(questions),'answer_positions':{str(i):sum(q[2]==i for q in questions) for i in range(3)}}))
