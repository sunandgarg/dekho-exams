"""Add linked passkey and checkout practice to local Web Development drafts."""
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
    dict(path='web-tech/passkey-account-lifecycle-project', title='Project: passkey account lifecycle', summary='Build registration, sign-in, credential removal, and recovery around server-verified challenges.', intro='Build a case-review account flow for reviewer 29, who uses a laptop and a shared workstation. The server issues one-use challenges scoped to registration or sign-in, verifies the returned assertion with a maintained WebAuthn implementation, and binds registration to the signed-in account that requested it. A credential ID resolves to exactly one account. After a verified sign-in, object permissions are still checked on each case route. The interface offers a visible fallback when the browser has no credential or the prompt is canceled. Settings show enrolled credentials and require recent assurance before adding or removing one. Removing a credential takes effect at the authoritative lookup even if another browser already holds a challenge. Losing every credential enters a separate recovery workflow with abuse controls and current authorization checks.', scope=['Register two credentials and reject account switches, expired challenges, replay, wrong origin, and duplicate IDs.','Sign in with one verified assertion, then prove a valid session does not bypass case authorization.','Cancel a prompt and finish through the approved fallback with keyboard and focus checks.','Remove one credential after step-up, attempt reuse, then exercise last-credential and full-loss recovery paths.'], code='function credentialUsable(record, challenge) {\n  return record.active && !challenge.used && challenge.actorId === record.actorId;\n}\nconsole.log(credentialUsable({ actorId: 29, active: false }, { actorId: 29, used: false }));\n// Output: false', cost='A credential lookup and challenge-state check are near O(1) with indexed IDs. Public-key verification has bounded cryptographic cost, while multiple credentials add small records and a settings surface. Recovery introduces support and abuse-review work; leaving it untested turns a lost phone into a locked account. Track challenge replay, origin rejection, canceled prompts, credential removal delay, and recovery completion. The small cost of a fresh verification step is justified for account-changing operations, but the product should measure unnecessary prompts.', failure='Replay a registration response and confirm no new credential is stored. Start registration as reviewer 29, switch to reviewer 62, then submit the result; the account binding must fail. Change the origin in a sign-in response and verify no session appears. Remove a passkey while a sign-in prompt is open and finish the prompt; the removed credential must fail. Cancel a prompt on the shared workstation and confirm the fallback remains usable without exposing whether a named account exists. Complete recovery and inspect tenant permissions and old sessions.', checks=['Challenges bind to one actor and purpose and are consumed once.','A signature, origin, and relying-party scope are verified before sign-in.','Credential removal and recovery follow current authorization and assurance policy.','Missing credentials leave a usable independent sign-in route.'], mistakes=['Treating browser prompt success as server authentication.','Attaching a credential using a client-supplied account ID.','Leaving a removed credential active in cached lookup state.'], related=['web-tech/passkey-registration-challenge-and-credential-binding','web-tech/passkey-assertion-origin-and-signature-verification','web-tech/passkey-conditional-sign-in-and-fallback','web-tech/passkey-management-recovery-and-step-up']),
    dict(path='web-tech/checkout-reconciliation-project', title='Project: checkout reconciliation', summary='Build a server-priced order, hosted payment attempt, verified event handler, and partial-refund ledger.', intro='Build the payment path for equipment order 47. Three pressure sleeves, one inspection seal, and delivery total 17,200 minor units under the selected currency rules. The browser proposes product IDs and quantities; the server validates catalog and stock, prices the order, and persists the accepted snapshot. A hosted checkout session is bound to that snapshot and an idempotent attempt key. Returning to the application shows the server order state, even when the provider event has not arrived. The webhook handler validates raw-body signature and provider scope, checks amount and currency, records event IDs, and writes one paid transition with one fulfillment intent. A reconciliation job uses the same transition if a webhook is delayed or lost. A partial refund of 4,700 units remains pending until provider confirmation, after which the ledger shows 12,500 net captured units without deleting the original capture.', scope=['Tamper with the browser total and verify the provider still receives the accepted server amount.','Refresh and retry hosted checkout without uncontrolled payable attempts; forge the return URL and confirm it cannot mark paid.','Deliver duplicate, reordered, wrong-amount, and missing webhook events; ensure one effective fulfillment.','Request partial and concurrent refunds, inject a failed refund, and reconcile ledger entries with provider state.'], code='function remainingCapturedMinor(capturedMinor, completedRefundMinor) {\n  return capturedMinor - completedRefundMinor;\n}\nconsole.log(remainingCapturedMinor(17200, 4700));\n// Output: 12500', cost='Pricing is O(n) for n order lines plus catalog and policy lookups. A unique payment attempt and event ID add small indexed records; fulfillment through an outbox adds a worker step but survives crashes between capture and shipment. Reconciliation uses provider reads and should back off for old or resolved attempts. A payment ledger grows with each movement, so balance reads can scan O(k) movements or use a transactional summary that is regularly reconciled. Track pending age, duplicate events, mismatched amounts, over-refund rejections, and one-order-to-one-shipment behavior.', failure='Send a browser request claiming a 200-unit total for order 47; the server must reject or ignore it. Open the success route without paying and confirm status remains pending. Deliver one signed capture event twice, then an older authorization event: the order remains captured and only one fulfillment key is emitted. Crash after the provider confirms payment but before the local write, then let reconciliation recover it. Start two 12,500-unit refunds concurrently; only an amount within the remaining 17,200 may be reserved. If a refund later fails, restore the correctly reserved balance without erasing the capture.', checks=['Order and provider amount match a persisted, currency-aware snapshot.','Browser return cannot authorize fulfillment.','Duplicate or reordered provider events cannot duplicate shipment.','Refund reservations and confirmed ledger movements never exceed capture.'], mistakes=['Using the browser total or return query as payment truth.','Acknowledging a webhook before durable state is recorded.','Treating a refund request as a settled refund.'], related=['web-tech/server-priced-order-snapshot-and-money-units','web-tech/hosted-checkout-session-and-browser-return','web-tech/payment-webhook-reconciliation-and-idempotent-fulfillment','web-tech/refunds-reversals-and-payment-ledger-state']),
]

for number, project in enumerate(projects, 1):
    assert project['path'] not in by_path
    subprocess.run(['node','--check','--input-type=module'], input=project['code'], text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path['web-tech/case-save-incident-evidence-project'])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + project['path'])), path=project['path'], title=project['title'], summary=project['summary'], sort_order=1190 + number, created_at=stamp, updated_at=stamp, published_at=stamp)
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
    ('What binds a new passkey to an account?', ['A fresh server challenge scoped to the signed-in actor and verified response', 'A browser-supplied account ID', 'A successful browser prompt alone'], 'Registration is an account mutation. The server verifies its challenge, origin, relying-party data, and original account context before storing the public key.'),
    ('When may an application create a passkey sign-in session?', ['After the server verifies the assertion with the stored public key and one-use challenge', 'When the browser opens an authenticator prompt', 'When a username matches a credential label'], 'The browser transports an assertion but cannot certify it. Signature, challenge, origin, and credential checks precede session creation.'),
    ('What should happen when a browser has no usable passkey?', ['Offer a clear, independent approved sign-in or recovery path', 'Keep the form hidden until a prompt resolves', 'Assume the account does not exist'], 'Credential absence is not an account verdict. A tested fallback avoids lockout while retaining separate server checks and abuse controls.'),
    ('What should removing a credential change?', ['Future authoritative credential lookups must reject that ID', 'Only the settings label', 'All case permissions become permanent'], 'A removed credential must stop authenticating, including after a challenge was issued. Case authorization remains a separate current policy.'),
    ('Who determines the amount sent to checkout?', ['The server from accepted catalog and order rules', 'A hidden browser field', 'The return-page query string'], 'The client proposes cart contents. Server pricing and a persisted order snapshot prevent a modified request from lowering the provider amount.'),
    ('Why record a currency-aware order snapshot?', ['To preserve the accepted exact amount and rules across later catalog changes', 'To avoid validating stock', 'To let a browser rewrite tax after payment'], 'The snapshot fixes the payable contract at a named transition. Currency units and rounding rules must remain explicit.'),
    ('What does a hosted checkout success return prove?', ['Only that a browser visited a return route', 'That funds settled', 'That a shipment must begin'], 'Return parameters can be forged or arrive before provider confirmation. The page displays server status rather than changing money state.'),
    ('How should a retry after an uncertain session-creation response work?', ['Reuse or reconcile a stable attempt and idempotency key', 'Create a new payable session on every refresh', 'Mark the order paid'], 'A remote session may have been created before a timeout. Stable keys and reconciliation prevent several live attempts for one order.'),
    ('What must a webhook handler verify before a paid transition?', ['Raw signature plus account, payment, amount, currency, and order relation', 'Only the event label', 'Only that the browser returned'], 'Provider events are untrusted until their signature and relationship to the local order are checked under the integration contract.'),
    ('How can fulfillment survive a crash after capture?', ['Commit the paid transition and unique fulfillment intent together', 'Ship inside a browser callback', 'Ignore provider retries'], 'An atomic state and outbox write preserves work through crashes. A unique fulfillment key makes worker retries effective only once.'),
    ('How should two concurrent partial refunds be bounded?', ['Reserve from the remaining captured balance in one transaction', 'Let each request read the original capture independently', 'Use a floating-point display total'], 'Concurrent requests can exceed capture if they both read an old balance. Exact units and transactional reservation enforce the limit.'),
    ('What does a provider-accepted refund request mean?', ['A pending movement until final provider confirmation', 'The original capture should be deleted', 'The order was never fulfilled'], 'Refund initiation and settlement are separate states. The ledger retains capture and fulfillment history and records final outcomes independently.'),
]

quiz_path = 'quizzes/web-development-passkey-checkout-decisions'
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path['quizzes/web-development-operations-sync-decisions'])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + quiz_path)), path=quiz_path, title='Web Development: passkey and checkout decisions quiz', summary='Twelve explained decisions about passkey assurance, server pricing, provider evidence, fulfillment, and refunds.', sort_order=1195, created_at=stamp, updated_at=stamp, published_at=stamp)

def quiz_item(number, value):
    prompt, options, explanation = value
    shift = number % 3
    return {'prompt':prompt,'options':options[shift:] + options[:shift], 'answer':(0 - shift) % 3, 'explanation':explanation}

quiz['data'] = {'subject_root':'web-tech/web-technology','section_path':'web-tech/quizzes','content_format':'html','seo_ready':False,'questions':[quiz_item(number, value) for number, value in enumerate(questions)]}
quiz['body'] = p(quiz['summary'] + ' Choose one answer, inspect the explanation, and revisit the related trust boundary.')
quiz['body'] += '<h2>Related lessons</h2><p>' + '; '.join(link(path) for project in projects for path in project['related']) + '.</p>'
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path['web-tech/web-technology/project']
project_hub['data']['modules'][0]['lessons'].extend(project['path'] for project in projects)
project_hub['body'] += '<h2>Passkey and checkout projects</h2><ul>' + ''.join('<li>' + link(project['path']) + ' — ' + html.escape(project['summary']) + '</li>' for project in projects) + '</ul>'
project_hub['summary'] = 'Build and verify thirty-five projects across browser, API, data, identity, search, quality, rendering, forms, navigation, delivery, streaming, accessibility, operations, synchronization, authorization, privacy, offline, live, capability, viewport, content, notification, passkey, and checkout contracts.'
project_hub['updated_at'] = stamp
quiz_hub = by_path['web-tech/quizzes']
quiz_hub['data']['modules'][0]['lessons'].append(quiz_path)
quiz_hub['body'] += '<h2>Passkey and checkout checks</h2><p>' + link(quiz_path) + ' — ' + html.escape(quiz['summary']) + '</p>'
quiz_hub['updated_at'] = stamp
for hub_path, project_path in [('web-tech/passkeys-and-account-assurance', projects[0]['path']), ('web-tech/checkout-and-payment-state', projects[1]['path'])]:
    hub = by_path[hub_path]
    hub['body'] += '<h2>Practice path</h2><p>Build ' + link(project_path) + ' and check decisions in ' + link(quiz_path) + '.</p>'
    hub['updated_at'] = stamp
for entry in entries:
    if entry['type'] != 'article' or entry['data'].get('section_path') not in {'web-tech/passkeys-and-account-assurance','web-tech/checkout-and-payment-state'}:
        continue
    project_path = projects[0]['path'] if entry['data']['section_path'] == 'web-tech/passkeys-and-account-assurance' else projects[1]['path']
    entry['body'] += '<h2>Apply and check</h2><p>Build ' + link(project_path) + ' and review ' + link(quiz_path) + '.</p>'
    entry['data']['related'].extend([project_path, quiz_path])
    entry['updated_at'] = stamp
root_entry = by_path['web-tech/web-technology']
root_entry['body'] += '<h2>Passkey and checkout practice</h2><p>Apply the account and payment contracts with ' + link(projects[0]['path']) + ' and ' + link(projects[1]['path']) + '.</p>'
root_entry['updated_at'] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_projects':len(projects),'new_quizzes':1,'new_questions':len(questions)}))
