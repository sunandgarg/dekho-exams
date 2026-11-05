"""Add an opt-in alert project and twelve explained push decisions."""
import copy
import datetime
import html
import json
import subprocess
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
entries = json.loads(fixture.read_text())
by_path = {entry['path']: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()

def p(value):
    return '<p>' + html.escape(value) + '</p>'

def link(path):
    assert path in by_path, path
    return '<a href="/' + html.escape(path, quote=True) + '">' + html.escape(by_path[path]['title']) + '</a>'

project = dict(path='web-tech/private-urgent-assignment-alert-project', title='Project: private urgent assignment alerts', summary='Build opt-in push alerts with account-bound subscriptions, safe text, expiry, and an authorized inbox.', intro='Build urgent assignment alerts for reviewers 29 and 62 in separate organizations. A settings action explains the purpose before requesting browser permission; a current product preference decides whether the category is enabled. Denial leaves the in-app assignment inbox fully usable. The server binds each push subscription to a verified actor, tenant, and device record, ignoring forged identity fields from the browser. A shared tablet must not receive reviewer 29’s alerts after reviewer 62 signs in. The outgoing payload says New urgent assignment without case details that could appear on a lock screen. Clicking opens a safe route and fetches current assignments under server authorization. An outbox alert has one logical ID and a short expiry; the sender rechecks current preference and assignment before every attempt. If a case is reassigned, the stale alert is canceled. A push-service accepted response is recorded as Accepted, never as a proven display or read.', scope=['Test the permission request after a named settings action and verify the inbox after denial or missing API support.','Register twice, forge account and tenant fields, then switch users on one browser and inspect subscription ownership.','Inspect exact push payload, lock-screen text, click route, and current authorization after sign-out or reassignment.','Fail push-service requests, expire an alert, replay the outbox, and verify one logical alert plus a durable inbox record.'], code='function alertCanAttempt(alert, current) {\n  return current.now < alert.expiresAt && current.reviewerId === alert.reviewerId && current.optedIn;\n}\nconsole.log(alertCanAttempt({ expiresAt: 80, reviewerId: 29 }, { now: 47, reviewerId: 62, optedIn: true }));\n// Output: false', cost='For d devices the sender makes at least O(d) attempted deliveries per alert, with bounded retries adding further work. An indexed subscription lookup is approximately O(1), while a shared-device audit needs an explicit account-binding lifecycle. The in-app inbox retains current assignments under the product’s approved policy and remains queryable when push is unavailable. Short alert expiry lowers stale-notification risk but may miss a temporarily disconnected device; the inbox supplies the recovery path. Measure invalid endpoint cleanup, queue age, stale cancellations, opt-out latency, and inbox access. Do not calculate a delivered rate from push-service acceptance alone.', failure='Request permission on page load and verify the test rejects that flow. Deny it and check the inbox still works. Try to bind reviewer 29’s endpoint to reviewer 62 through a forged POST; the server must ignore or reject the claim. Send an alert with the raw private case title and inspect the lock-screen output; the payload allowlist should fail the build. Sign out before clicking and verify the route does not reveal case 47. Reassign the case before a retry and confirm cancellation. Return an invalid endpoint response and remove its binding. Repeat the worker with the same event ID and confirm no duplicate logical alert appears.', checks=['Browser permission and product preference both gate alerts without gating the inbox.','Each subscription follows current verified account and device scope.','Payload and click paths reveal no private case data without authorization.','Expired and superseded alerts stop, and telemetry does not invent confirmed delivery.'], mistakes=['Equating browser permission with ongoing product opt-in.','Trusting a client-supplied account ID when saving a subscription.','Putting private case text in a lock-screen message.','Retrying stale alerts and calling Accepted a read receipt.'], related=['web-tech/notification-opt-in-and-channel-preference','web-tech/push-subscription-account-binding-and-rotation','web-tech/private-notification-payload-and-click-routing','web-tech/push-delivery-retries-expiry-and-inbox-fallback'])

assert project['path'] not in by_path
subprocess.run(['node','--check','--input-type=module'], input=project['code'], text=True, capture_output=True, check=True)
entry = copy.deepcopy(by_path['web-tech/case-save-incident-evidence-project'])
entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + project['path'])), path=project['path'], title=project['title'], summary=project['summary'], sort_order=1191, created_at=stamp, updated_at=stamp, published_at=stamp)
entry['data'] = {'subject_root':'web-tech/web-technology','section_path':'web-tech/web-technology/project','content_format':'html','seo_ready':False,'kind':'project','author_path':'authors/aitrove-editorial','reading_minutes':8,'related':project['related']}
body = p(project['intro']) + '<h2>Build contract</h2><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in project['scope']) + '</ul>'
body += '<h2>Implementation checkpoint</h2><pre><code class="language-javascript">' + html.escape(project['code'], quote=False) + '</code></pre>'
body += '<h2>Cost and boundaries</h2>' + p(project['cost']) + '<h2>Failure drill</h2>' + p(project['failure'])
body += '<h2>Acceptance checks</h2><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in project['checks']) + '</ul>'
body += '<h3>Common Mistakes</h3><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in project['mistakes']) + '</ul>'
body += '<h2>Related lessons</h2><p>' + '; '.join(link(path) for path in project['related']) + '.</p>'
entry['body'] = body
entries.append(entry)
by_path[entry['path']] = entry

questions = [
    ('When should urgent-alert permission be requested?', ['After a person chooses the named alert feature in settings', 'On the first page load', 'Whenever an in-app assignment arrives'], 'A relevant user action explains the purpose. Permission denial must not prevent access to the authorized assignment inbox.'),
    ('Does browser permission Granted enable every alert category?', ['No; a current product preference must also allow the category', 'Yes; it replaces product settings', 'Yes; it overrides a later opt-out'], 'Browser permission is a technical gate. Product opt-in controls the continuing decision about which useful alerts may be sent.'),
    ('What remains available after notification permission is denied?', ['The authorized in-app assignment inbox', 'Only a blank error page', 'An unrestricted push endpoint'], 'Push is a timely signal, not the durable record of work. The inbox keeps assignments discoverable without browser permission.'),
    ('Where should subscription ownership come from?', ['The verified server session and current tenant context', 'A userId field submitted by the browser', 'The endpoint hostname'], 'A client can forge identity fields. The server must bind the capability to trusted actor and tenant scope.'),
    ('How should a push endpoint be treated?', ['As a sensitive delivery capability with limited logging and access', 'As a harmless public profile URL', 'As a password that can never rotate'], 'Knowledge of a subscription endpoint can enable unwanted sends. Protect it, avoid ordinary logs, and plan expiry and replacement.'),
    ('What should happen on a shared device after account switch?', ['Deactivate the old account binding before a new authorized registration', 'Send both accounts to the same endpoint forever', 'Assume cookie deletion unbinds the server record'], 'A subscription outlives page state unless its server binding changes. Shared-device account crossover can expose alerts.'),
    ('What information is safe for a lock-screen alert about a private case?', ['A generic assignment cue with no private title or note', 'The full case note because transport is encrypted', 'A signed download URL for the case file'], 'Encrypted transport does not hide text shown by the operating system. Fetch private detail only after an authorized click.'),
    ('What does a notification click prove?', ['Only navigation intent, not current permission to view a case', 'That the case is still assigned to the same reviewer', 'That the person read every detail'], 'The destination must check current sign-in and object authorization because ownership can change after the alert was sent.'),
    ('What should a push-service accepted response mean in telemetry?', ['The service accepted an attempt, not confirmed display or reading', 'The device displayed and the person read it', 'The inbox record may be deleted'], 'Push services do not give an end-to-end human read guarantee. Status names must reflect the observation actually made.'),
    ('How should a worker handle a reassigned case before retry?', ['Cancel the superseded alert after a current-state check', 'Send the old alert because it was queued earlier', 'Increase retry count without checking ownership'], 'A delayed alert for an old reviewer can confuse users and reveal prior private assignment state.'),
    ('What bounds retries for a time-sensitive alert?', ['An expiry deadline, current preference, and error classification', 'An infinite loop until one device wakes', 'Only a large queue capacity'], 'A stale urgent message can be harmful. Retry transient failures within a useful lifetime and retire invalid subscriptions.'),
    ('What supplies recovery when a device misses push?', ['The current authorized in-app inbox', 'A claim that push always arrives', 'A public copy of the private case'], 'The inbox is queryable under current permissions and stays useful when devices are offline, subscriptions expire, or push is disabled.'),
]

quiz_path = 'quizzes/web-development-push-notification-decisions'
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path['quizzes/web-development-operations-sync-decisions'])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + quiz_path)), path=quiz_path, title='Web Development: push notification decisions quiz', summary='Twelve explained decisions about opt-in alerts, subscription ownership, private payloads, expiry, and inbox recovery.', sort_order=1195, created_at=stamp, updated_at=stamp, published_at=stamp)

def item(number, value):
    prompt, options, explanation = value
    shift = number % 3
    return {'prompt':prompt,'options':options[shift:] + options[:shift],'answer':(0 - shift) % 3,'explanation':explanation}

quiz['data'] = {'subject_root':'web-tech/web-technology','section_path':'web-tech/quizzes','content_format':'html','seo_ready':False,'questions':[item(number, value) for number, value in enumerate(questions)]}
quiz['body'] = p(quiz['summary'] + ' Choose one answer, inspect the explanation, and revisit the relevant lesson.')
quiz['body'] += '<h2>Related lessons</h2><p>' + '; '.join(link(path) for path in project['related']) + '.</p>'
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path['web-tech/web-technology/project']
project_hub['data']['modules'][0]['lessons'].append(project['path'])
project_hub['body'] += '<h2>Notification delivery project</h2><p>' + link(project['path']) + ' — ' + html.escape(project['summary']) + '</p>'
project_hub['summary'] = 'Build and verify thirty-three projects across browser, API, data, identity, search, quality, rendering, forms, navigation, delivery, streaming, accessibility, operations, synchronization, authorization, privacy, offline, live, capability, viewport, content, and notification contracts.'
project_hub['updated_at'] = stamp
quiz_hub = by_path['web-tech/quizzes']
quiz_hub['data']['modules'][0]['lessons'].append(quiz_path)
quiz_hub['body'] += '<h2>Notification delivery checks</h2><p>' + link(quiz_path) + ' — ' + html.escape(quiz['summary']) + '</p>'
quiz_hub['updated_at'] = stamp
hub = by_path['web-tech/web-push-and-notification-delivery']
hub['body'] += '<h2>Practice path</h2><p>Build ' + link(project['path']) + ' and check decisions in ' + link(quiz_path) + '.</p>'
hub['updated_at'] = stamp
for page in entries:
    if page['type'] != 'article' or page['data'].get('section_path') != hub['path']:
        continue
    page['body'] += '<h2>Apply and check</h2><p>Build ' + link(project['path']) + ' and review ' + link(quiz_path) + '.</p>'
    page['data']['related'].extend([project['path'],quiz_path])
    page['updated_at'] = stamp
root_entry = by_path['web-tech/web-technology']
root_entry['body'] += '<h2>Notification delivery practice</h2><p>Apply the opt-in and delivery contract with ' + link(project['path']) + '.</p>'
root_entry['updated_at'] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_projects':1,'new_quizzes':1,'new_questions':len(questions)}))
