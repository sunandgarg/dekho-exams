"""Add extension boundary project and decision quiz."""
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

lessons = [
    'web-tech/extension-host-permissions-and-user-invocation',
    'web-tech/content-script-isolation-and-dom-mutation',
    'web-tech/extension-background-events-and-durable-state',
    'web-tech/extension-message-contracts-and-page-data-boundary',
]
project_path = 'web-tech/permit-checklist-browser-helper-project'
quiz_path = 'quizzes/web-development-extension-boundary-decisions'
assert project_path not in by_path and quiz_path not in by_path
code = "function helperRequestAllowed(message, sender, access) {\n  return sender.origin === 'https://permits.internal.test' && access.userInvoked &&\n    access.hostGranted && message.type === 'open-checklist' &&\n    /^CASE-[0-9]{2,6}$/.test(message.caseId) && Number.isInteger(message.revision) &&\n    message.revision >= 0 && typeof message.requestId === 'string' &&\n    message.requestId.length > 0 && message.requestId.length <= 96 &&\n    JSON.stringify(message).length <= 2048 &&\n    Object.keys(message).every(key => ['type', 'caseId', 'revision', 'requestId'].includes(key));\n}\nconsole.log(helperRequestAllowed({ type: 'open-checklist', caseId: 'CASE-47', revision: 29, requestId: 'r-63', uploadTo: 'outside' }, { origin: 'https://permits.internal.test' }, { userInvoked: true, hostGranted: true }));\n// Output: false"
subprocess.run(['node', '--check', '--input-type=module'], input=code, text=True, capture_output=True, check=True)
project = copy.deepcopy(by_path['web-tech/case-save-incident-evidence-project'])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + project_path)), path=project_path,
               title='Project: permit checklist browser helper',
               summary='Build a narrow-permission extension that reads one case, survives worker restart, and validates every message.',
               sort_order=1319, created_at=stamp, updated_at=stamp, published_at=stamp)
project['data'] = {'subject_root': 'web-tech/web-technology', 'section_path': 'web-tech/web-technology/project',
                   'content_format': 'html', 'seo_ready': False, 'kind': 'project',
                   'author_path': 'authors/aitrove-editorial', 'reading_minutes': 8, 'related': lessons}
project['body'] = p('Build a browser helper for municipal permit reviewers. A reviewer presses the toolbar control while viewing case 47. The helper checks the tab origin and user action, requests only the needed host access, then injects a content script that extracts the case ID, due date, and status from one known page container. A denied grant still leaves a manual case-ID path. The helper does not inspect unrelated tabs or send full page HTML to a service. The content adapter validates one unambiguous case card, places a small labeled panel with text nodes, and disconnects observers on route change. It cannot change the host form or send a checklist without another explicit action. Messages from the content script to the background handler use a versioned type, request ID, case ID, and revision. The handler checks runtime sender metadata and rejects stale tabs, extra destinations, unknown types, and oversized payloads. It asks the server to authorize the actual case. The popup can close at any time; the background handler may stop while idle. Before starting a checklist write, the helper stores a scoped operation key and later reconciles the server status after restart. A lost response reuses the same key so it cannot make a second checklist. The local store retains only minimal pending metadata and expires it under a policy. Sign-out removes private local data and makes replay require a fresh session. The release review inventories requested browser permissions, supported portal versions, and a rollback action if the adapter fails after a site update.')
project['body'] += '<h2>Build contract</h2><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in [
    'An unrelated or lookalike site cannot trigger injection or a checklist.',
    'An ambiguous DOM extraction fails visibly without a guessed case.',
    'The background handler recovers one operation after popup close or restart.',
    'Messages never grant broader server access than the signed-in reviewer has.',
]) + '</ul>'
project['body'] += '<h2>Implementation checkpoint</h2><pre><code class="language-javascript">' + html.escape(code, quote=False) + '</code></pre>'
project['body'] += p('The checkpoint rejects a message with an unexpected upload destination. In the actual extension, sender origin and tab identity come from runtime metadata, not a payload field. The message parser should cap encoded size before shape validation. Validation is O(B) for B message bytes, bounded at 2 KiB; a DOM adapter is O(N) over its selected container of N nodes, not the whole document. Pending local operations take O(P) space for P unfinished tasks. Server authorization and idempotency remain independent checks even when all local predicates pass.')
project['body'] += '<h2>Failure drill</h2>' + p('Open a similar-looking hostname, deny the optional host grant, add a hidden duplicate case card, change the portal locale, and fire 83 rapid DOM mutations. Confirm the helper either extracts one valid case or stops with a visible manual route, while no duplicate panels or observers remain. Send a forged page message and a content-script message with an extra destination; neither may invoke server work. Close the popup after the server accepts a write but before its response arrives. Restart the browser, reload operation metadata, and reconcile rather than creating a second checklist. Revoke the reviewer on the server before a retry and require denial. Sign out, inspect extension storage, and confirm private page text was not retained. Test keyboard operation, panel focus, and the host form after each injected update.')
project['body'] += '<h2>Acceptance checks</h2><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in [
    'Permission denial still allows manual case entry.',
    'One supported page yields one accessible panel and one unambiguous case.',
    'Worker interruption and response loss do not duplicate a checklist.',
    'Unexpected message fields and stale senders fail before privileged work.',
]) + '</ul>'
project['body'] += '<h3>Common Mistakes</h3><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in [
    'Requesting all-site access for a user-invoked portal action.',
    'Trusting extracted page text because it came from an isolated content script.',
    'Using a background global variable as durable operation state.',
]) + '</ul>'
project['body'] += '<h2>Related lessons</h2><p>' + '; '.join(link(path) for path in lessons) + '.</p>'
entries.append(project)
by_path[project_path] = project

questions = [
    ('What does host permission authorize?', ['Extension access to a permitted page origin, not server case access', 'Every tenant record on the server', 'Permanent access to every browser tab'], 'The browser grant scopes where the helper may inspect or change pages. The server must still authorize each private record action.'),
    ('What is a suitable route when optional host access is denied?', ['Manual case entry that preserves the user task', 'Reading another tab without permission', 'A permanent all-sites grant'], 'Optional access can be refused. A manual entry path lets a reviewer complete the checklist without forcing broad page access.'),
    ('What should happen on a lookalike portal hostname?', ['Reject before content-script injection', 'Treat its page text as a valid case', 'Send it to the server for implicit trust'], 'Exact intended origin checks prevent a similar hostname from receiving privileged page behavior.'),
    ('Does an isolated content script make page text trustworthy?', ['No; page-controlled DOM remains untrusted data', 'Yes, every DOM string becomes extension authority', 'Only when a hidden input contains the case ID'], 'Execution isolation limits script-variable collisions. It does not stop the host page from changing nodes and values the extension reads.'),
    ('How should repeated content-script insertion behave?', ['Produce one panel with cleaned-up observers', 'Append a new panel for each injection', 'Overwrite the host form'], 'Route changes and repeated injections are normal. An idempotent adapter and lifecycle cleanup prevent duplicate UI and work.'),
    ('What should ambiguous case extraction do?', ['Stop the derived action and show a visible fallback', 'Pick the first hidden field', 'Guess from the URL fragment'], 'A wrong case ID can cross permission and data boundaries. Ambiguity should not become a silent selection.'),
    ('Why persist a checklist operation ID?', ['Background memory and popup state may disappear', 'It grants indefinite server permission', 'It makes all browser events synchronous'], 'Event-driven background handlers and popups can close. A durable ID lets the helper reconcile an admitted server operation.'),
    ('What follows an ambiguous lost server response?', ['Read status and retry only with the same scoped key if needed', 'Start a second write under a fresh key', 'Mark success locally without checking'], 'The server may have committed before the response was lost. Reconciliation and key reuse prevent duplicate checklists.'),
    ('Which sender field should a privileged handler trust?', ['Runtime-provided sender context after validation', 'An origin string written into the message body', 'The visible page title'], 'A page or content script can write arbitrary payload fields. The handler must use the runtime sender context and current tab state.'),
    ('How should a message with an extra upload destination be handled?', ['Reject it before privileged work', 'Forward it as a harmless option', 'Open the destination automatically'], 'A narrow message schema prevents a generic relay from turning a case helper into an outbound data path.'),
    ('Can a valid local message skip server authorization?', ['No; the real case and session need current server checks', 'Yes, host access is enough', 'Yes, if the case ID has valid syntax'], 'Local checks cannot grant tenant permission. The server owns the private record and must mediate every write or result read.'),
    ('What should sign-out do to pending helper data?', ['Remove private local data and require fresh authorization before replay', 'Keep page text forever for convenience', 'Silently complete all queued writes'], 'A changed account invalidates assumptions behind cached operations. Minimal metadata and fresh access checks keep replay tied to the right user.'),
]
quiz = copy.deepcopy(by_path['quizzes/web-development-graphics-editor-decisions'])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + quiz_path)), path=quiz_path,
            title='Web Development: extension boundary decisions quiz',
            summary='Twelve explained decisions about host grants, untrusted DOM, worker restart, message checks, and server access.',
            sort_order=1320, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz['data'] = {'subject_root': 'web-tech/web-technology', 'section_path': 'web-tech/quizzes',
                'content_format': 'html', 'seo_ready': False,
                'questions': [{'prompt': prompt, 'options': options[number % 3:] + options[:number % 3],
                               'answer': (-number) % 3, 'explanation': explanation}
                              for number, (prompt, options, explanation) in enumerate(questions)]}
quiz['body'] = p(quiz['summary'] + ' Choose one answer, read its explanation, and test the corresponding boundary.')
quiz['body'] += '<h2>Related lessons</h2><p>' + '; '.join(link(path) for path in lessons) + '.</p>'
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path['web-tech/web-technology/project']
project_hub['data']['modules'][0]['lessons'].append(project_path)
project_hub['body'] += '<h2>Browser extension project</h2><p>' + link(project_path) + ' — ' + html.escape(project['summary']) + '</p>'
project_hub['summary'] = 'Build and verify fifty-six projects across browser, API, data, identity, media, extension trust, and production workflows.'
project_hub['updated_at'] = stamp
quiz_hub = by_path['web-tech/quizzes']
quiz_hub['data']['modules'][0]['lessons'].append(quiz_path)
quiz_hub['body'] += '<h2>Browser extension checks</h2><p>' + link(quiz_path) + ' — ' + html.escape(quiz['summary']) + '</p>'
quiz_hub['updated_at'] = stamp
hub = by_path['web-tech/browser-extension-trust-and-lifecycle']
hub['body'] += '<h2>Practice path</h2><p>Build ' + link(project_path) + ' and check decisions in ' + link(quiz_path) + '.</p>'
hub['updated_at'] = stamp
for lesson_path in lessons:
    lesson = by_path[lesson_path]
    lesson['body'] += '<h2>Connected practice</h2><p>Build ' + link(project_path) + ' and review ' + link(quiz_path) + '.</p>'
    lesson['data']['related'].extend([project_path, quiz_path])
    lesson['updated_at'] = stamp
root_entry = by_path['web-tech/web-technology']
root_entry['body'] += '<h2>Browser extension practice</h2><p>Apply this track with ' + link(project_path) + '.</p>'
root_entry['updated_at'] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_projects': 1, 'new_quizzes': 1, 'new_questions': len(questions)}))
