"""Add linked file-ingestion and email-delivery practice drafts."""
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

projects = [
    dict(path='web-tech/private-evidence-file-lifecycle-project', title='Project: private evidence file lifecycle', summary='Build a bounded resumable upload, inspection worker, protected preview, and expiry workflow.', intro='Build file intake for case 47. Reviewer 29 may add up to four evidence files, each within a 23 MiB application limit for ordinary attachments; a separate large-video policy uses an owned resumable session. The browser shows sent-byte progress, but the case page says Processing until storage completion, integrity checks, and inspection finish. The server grants only an opaque pending object key after confirming current case rights and quota. It counts actual bytes, keeps abandoned parts on a cleanup schedule, and prevents a second reviewer from completing the session. The worker validates the full format, applies resource limits to parsing and preview generation, and records accepted or rejected state. Originals and previews stay private. At download, the server checks current case rights again. An assignment change blocks new grants; the retention workflow deletes raw, preview, and staging objects and keeps a deletion marker against restore.', scope=['Bound actual bytes and concurrent sessions before storage; reject cross-tenant and forged object keys.','Resume a timed-out part from authoritative state and distinguish sending, assembling, inspecting, and ready.','Reject malformed or over-expanded content and retry a crashed inspection worker without stale previews.','Revoke current read rights and delete original, derivative, and incomplete storage under one asset inventory.'], code='function assetReady(assembled, inspected, previewReady) {\n  return assembled && inspected === "accepted" && previewReady;\n}\nconsole.log(assetReady(true, "pending", true));\n// Output: false', cost='For n transferred bytes, intake and digest work are O(n); an in-memory receiver also consumes O(n) process memory, which a bounded stream avoids. Splitting n bytes into parts adds metadata and request overhead while reducing retransmission after a failure. Inspection may cost more than transfer when media decoding or archive expansion occurs, so the worker needs CPU, memory, output, and time caps. A proxy download consumes O(n) application egress; brief signed storage grants reduce that cost but leave a bounded revocation window. Track incomplete-part storage, pending age, inspection failures, orphaned derivatives, and denied reads.', failure='Post a 24 MiB ordinary file while declaring 22 MiB, and verify reception stops at the actual cap. Time out after part four is stored, query the session, and resume without duplicating earlier parts. Finish transfer with a mismatched full-object digest and prove no ready asset appears. Crash inspection after a preview write and retry; only the matching source version may be exposed. Revoke reviewer 29’s case rights and attempt original and preview reads. Run expiry, restore old metadata, and confirm the deletion marker prevents reappearance.', checks=['A transferred object remains private until inspection and required outputs pass.','Parts, final object, and derivatives remain bound to one authorized asset.','Current authorization covers every original and preview read.','Expiry removes incomplete and completed storage without revival on restore.'], mistakes=['Equating progress with a usable asset.','Using a browser filename as the storage key.','Protecting an original while exposing its preview.'], related=['web-tech/upload-intake-budgets-and-storage-ownership','web-tech/resumable-transfer-parts-and-integrity','web-tech/file-quarantine-inspection-and-derived-previews','web-tech/private-asset-download-revocation-and-expiry']),
    dict(path='web-tech/account-email-delivery-project', title='Project: account email delivery', summary='Build a durable notice outbox, safe account link, provider feedback loop, and sender rollout check.', intro='Build assignment notices and account recovery mail for the case-review application. Assigning reviewer 29 to case 47 writes assignment revision 6 and one purpose-labeled email intent in the same transaction. A worker claims the intent, checks current recipient eligibility, renders a pinned template revision, and sends through a configured provider with a stable attempt key. The assignment notice excludes private case notes from subject and body. Its link opens the app, where current case authorization decides what the reader can see. A recovery message contains a short-lived purpose-bound token whose GET landing page changes no account state. Provider acceptance, delivery feedback, bounce, and complaint remain distinct states. Verified feedback maps to the application intent; duplicate and old events cannot reverse a terminal result. Optional mail checks the latest preference and suppression state before sending. A sender-domain rollout uses received test messages and a limited cohort before general traffic.', scope=['Crash before and after the assignment commit; prove one durable intent and no notice for rolled-back work.','Simulate provider timeout after acceptance and duplicate worker delivery without creating a second intent.','Open a recovery link with a mail scanner, then submit, replay, and expire the actual action token.','Verify bounce suppression, current preference, message correlation, and sender authentication on received tests.'], code='function sendIntentKey(caseId, revision) {\n  return `assignment:${caseId}:${revision}`;\n}\nconsole.log(sendIntentKey(47, 6));\n// Output: assignment:47:6', cost='One intent write is O(1) and each send consumes a provider request, queue slot, and status record. At scale, fan-out and provider limits govern latency, so worker concurrency needs a ceiling and backoff. A feedback event typically uses an indexed message lookup; storing every full body for diagnostics would grow with volume and expose private links. Authentication checks add small send-time work but require DNS and signing-key operations. Monitor intent age, uncertain attempts, accepted-versus-delivered gap, bounces, complaint rate, and optional sends after a preference change.', failure='Send the assignment email before commit, then roll back; the recipient gets a false notice. Move intent creation into the transaction. Let the provider accept an attempt but drop its response; a worker restart must reconcile the same intent rather than invent a new one. Prefetch a recovery GET and prove no token is consumed. Deliver an old success event after a newer bounce and confirm status does not move backward. Suppress optional mail for a bounced address while retaining the defined account-security recovery path. Inspect logs for address, case note, HTML body, and token leakage.', checks=['One committed assignment maps to one stable message intent.','Email links cannot bypass account and case authorization.','Feedback and suppression states survive duplicate or delayed events.','Sender rollout uses received authentication evidence and restricted telemetry.'], mistakes=['Treating provider acceptance as user reading.','Putting a reset mutation on GET.','Retrying a permanent bounce without a stop rule.'], related=['web-tech/email-intent-outbox-and-idempotent-send','web-tech/email-template-data-and-account-link-boundaries','web-tech/email-provider-events-bounces-and-suppression','web-tech/sender-identity-reputation-and-message-observability']),
]

for number, project in enumerate(projects, 1):
    assert project['path'] not in by_path
    subprocess.run(['node','--check','--input-type=module'], input=project['code'], text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path['web-tech/case-save-incident-evidence-project'])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + project['path'])), path=project['path'], title=project['title'], summary=project['summary'], sort_order=1200 + number, created_at=stamp, updated_at=stamp, published_at=stamp)
    entry['data'] = {'subject_root':'web-tech/web-technology','section_path':'web-tech/web-technology/project','content_format':'html','seo_ready':False,'kind':'project','author_path':'authors/aitrove-editorial','reading_minutes':8,'related':project['related']}
    body = p(project['intro']) + '<h2>Build contract</h2><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in project['scope']) + '</ul>'
    body += '<h2>Implementation checkpoint</h2><pre><code class="language-javascript">' + html.escape(project['code'], quote=False) + '</code></pre>'
    body += '<h2>Cost and boundaries</h2>' + p(project['cost']) + '<h2>Failure drill</h2>' + p(project['failure'])
    body += '<h2>Acceptance checks</h2><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in project['checks']) + '</ul>'
    body += '<h3>Common Mistakes</h3><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in project['mistakes']) + '</ul>'
    body += '<h2>Related lessons</h2><p>' + '; '.join(link(item) for item in project['related']) + '.</p>'
    entry['body'] = body
    entries.append(entry)
    by_path[entry['path']] = entry

questions = [
    ('What does a completed browser upload prove?', ['Only that transport reported completion, not inspection or access approval', 'That the file is safe', 'That every preview is public'], 'Transport, object assembly, inspection, and authorization are distinct states. A ready asset needs the required server checks.'),
    ('Which size should the intake service enforce?', ['Actual received bytes under a server cap', 'Only the browser File.size value', 'Only the declared Content-Length'], 'Clients can omit or misstate their size. A streaming receiver counts actual bytes and stops before exceeding its limit.'),
    ('Who chooses an uploaded object key?', ['The server under a scoped asset session', 'The browser filename', 'Any caller with the case number'], 'A generated key avoids path collisions and cross-tenant key selection. The server binds it to an authorized actor and asset.'),
    ('How should a timed-out multipart part be retried?', ['Reconcile its accepted state under the same owned session', 'Always create a new upload session', 'Assume all parts are durable'], 'The storage service may have accepted the part before a timeout. Querying one session avoids needless copies and inconsistent completion.'),
    ('When may an inspected file become downloadable?', ['After required checks and current read authorization', 'When its extension looks correct', 'When the progress bar reaches 100 percent'], 'Format checks, bounded processing, and access control apply after transfer; neither extension nor progress establishes them.'),
    ('What must retention deletion include?', ['Raw object, staging parts, derivatives, and restore markers', 'Only the asset database row', 'Only the thumbnail'], 'An asset can exist in several storage forms. Removing metadata alone leaves data and risks a later restore exposing it again.'),
    ('When should a business change create an email intent?', ['In the same transaction that commits the change', 'Before the transaction begins', 'Only after the provider reports delivery'], 'An atomic outbox record ensures committed work retains a send intent and rolled-back work does not send a false notice.'),
    ('What should a provider timeout after sending mean?', ['Acceptance is uncertain and the stable intent needs reconciliation', 'The message certainly failed', 'The recipient read it'], 'The remote provider may have accepted the request before the response was lost. A new intent can create duplicate mail.'),
    ('How should a recovery link handle a GET request?', ['Show a read-only landing page and require deliberate final action', 'Reset the account immediately', 'Grant permanent access'], 'Mail scanners may fetch links. A state-changing GET can consume tokens or alter accounts before the recipient acts.'),
    ('What does provider acceptance establish?', ['The provider accepted an attempt, with later delivery still uncertain', 'The person opened the message', 'The address cannot bounce'], 'Accepted, delivered, bounced, and complained-about messages have distinct evidence and timing. None proves human reading.'),
    ('What should a permanent bounce do to optional mail?', ['Stop or suppress further sends under the purpose policy', 'Trigger unlimited retries', 'Remove the underlying case assignment'], 'Repeated sending to a permanently failing address wastes capacity and harms reputation. The business event remains separate.'),
    ('How should a new sending domain be verified?', ['Inspect authentication results on received test messages from the real path', 'Check only that a DNS record exists', 'Send all traffic before observing results'], 'The actual sender, signing domain, and recipient checks must agree. A staged rollout limits the effect of a faulty configuration.'),
]

quiz_path = 'quizzes/web-development-file-email-decisions'
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path['quizzes/web-development-operations-sync-decisions'])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + quiz_path)), path=quiz_path, title='Web Development: file and email delivery decisions quiz', summary='Twelve explained decisions about upload authority, private assets, email intent, account links, and delivery feedback.', sort_order=1205, created_at=stamp, updated_at=stamp, published_at=stamp)

def quiz_item(number, value):
    prompt, options, explanation = value
    shift = number % 3
    return {'prompt':prompt,'options':options[shift:] + options[:shift], 'answer':(0 - shift) % 3, 'explanation':explanation}

quiz['data'] = {'subject_root':'web-tech/web-technology','section_path':'web-tech/quizzes','content_format':'html','seo_ready':False,'questions':[quiz_item(number, value) for number, value in enumerate(questions)]}
quiz['body'] = p(quiz['summary'] + ' Choose one answer, inspect the explanation, and revisit the related lifecycle.')
quiz['body'] += '<h2>Related lessons</h2><p>' + '; '.join(link(path) for project in projects for path in project['related']) + '.</p>'
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path['web-tech/web-technology/project']
project_hub['data']['modules'][0]['lessons'].extend(project['path'] for project in projects)
project_hub['body'] += '<h2>File and email projects</h2><ul>' + ''.join('<li>' + link(project['path']) + ' — ' + html.escape(project['summary']) + '</li>' for project in projects) + '</ul>'
project_hub['summary'] = 'Build and verify thirty-seven projects across browser, API, data, identity, search, quality, rendering, forms, navigation, delivery, streaming, accessibility, operations, synchronization, authorization, privacy, offline, live, capability, viewport, content, notification, passkey, checkout, private files, and email contracts.'
project_hub['updated_at'] = stamp
quiz_hub = by_path['web-tech/quizzes']
quiz_hub['data']['modules'][0]['lessons'].append(quiz_path)
quiz_hub['body'] += '<h2>File and email checks</h2><p>' + link(quiz_path) + ' — ' + html.escape(quiz['summary']) + '</p>'
quiz_hub['updated_at'] = stamp
for hub_path, project_path in [('web-tech/file-ingestion-and-private-asset-lifecycle', projects[0]['path']), ('web-tech/outbound-email-and-delivery-state', projects[1]['path'])]:
    hub = by_path[hub_path]
    hub['body'] += '<h2>Practice path</h2><p>Build ' + link(project_path) + ' and check decisions in ' + link(quiz_path) + '.</p>'
    hub['updated_at'] = stamp
for entry in entries:
    if entry['type'] != 'article' or entry['data'].get('section_path') not in {'web-tech/file-ingestion-and-private-asset-lifecycle','web-tech/outbound-email-and-delivery-state'}:
        continue
    project_path = projects[0]['path'] if entry['data']['section_path'] == 'web-tech/file-ingestion-and-private-asset-lifecycle' else projects[1]['path']
    entry['body'] += '<h2>Apply and check</h2><p>Build ' + link(project_path) + ' and review ' + link(quiz_path) + '.</p>'
    entry['data']['related'].extend([project_path, quiz_path])
    entry['updated_at'] = stamp
root_entry = by_path['web-tech/web-technology']
root_entry['body'] += '<h2>File and email practice</h2><p>Apply the private-asset and delivery contracts with ' + link(projects[0]['path']) + ' and ' + link(projects[1]['path']) + '.</p>'
root_entry['updated_at'] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_projects':len(projects),'new_quizzes':1,'new_questions':len(questions)}))
