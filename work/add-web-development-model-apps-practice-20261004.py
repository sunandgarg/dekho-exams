"""Add one model-backed web project and a twelve-question decision quiz."""
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
    'web-tech/model-gateway-identity-and-request-budgets',
    'web-tech/generated-response-streaming-and-cancel-state',
    'web-tech/retrieved-content-instructions-and-tool-permission',
    'web-tech/model-output-evaluation-and-release-control',
]
project_path = 'web-tech/permission-bound-maintenance-summary-project'
quiz_path = 'quizzes/web-development-model-backed-application-decisions'
assert project_path not in by_path and quiz_path not in by_path

code = "function summaryMayShip(operation) {\n  return operation.caseAuthorized && operation.terminalEventSeen &&\n    operation.evidenceIds.every(id => operation.permittedEvidenceIds.has(id));\n}\nconsole.log(summaryMayShip({ caseAuthorized: true, terminalEventSeen: true, evidenceIds: [47, 63], permittedEvidenceIds: new Set([47]) }));\n// Output: false"
subprocess.run(['node', '--check', '--input-type=module'], input=code, text=True, capture_output=True, check=True)
project = copy.deepcopy(by_path['web-tech/case-save-incident-evidence-project'])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + project_path)), path=project_path,
               title='Project: permission-bound maintenance summary',
               summary='Build an authorized, budgeted, streamed summary with safe retrieval and a reversible release gate.',
               sort_order=1314, created_at=stamp, updated_at=stamp, published_at=stamp)
project['data'] = {'subject_root': 'web-tech/web-technology', 'section_path': 'web-tech/web-technology/project',
                   'content_format': 'html', 'seo_ready': False, 'kind': 'project',
                   'author_path': 'authors/aitrove-editorial', 'reading_minutes': 8, 'related': lessons}
project['body'] = p('Build a maintenance-summary feature for case 47 at revision 29. The browser submits a scoped operation key and a request for a short answer. The server checks the reviewer, tenant, selected records, input size, output cap, and concurrent-work budget before calling a model service. Keep the service credential outside browser assets. A duplicate request for the same revision returns one operation ID; a changed revision with the old key produces a conflict. Store the operation state so a timeout cannot be mistaken for a completed answer. A result read checks current case permission again. The browser can watch a framed stream, but it labels accumulated text incomplete until a terminal event arrives. It decodes split bytes and frames, ignores old operation events after navigation, and bounds its buffer. Closing the tab requests cancellation but does not claim that already consumed work or a terminal answer disappeared. Retrieved maintenance notes carry case and tenant identity and are filtered before generation. A note that tells the system to email private records stays data. The summary task has no mail or write tool. A later task-creation action requires a separate user confirmation and a fresh authorization check in the tool handler. Output is rendered as text; evidence IDs must belong to the permitted case and revision. Keep an 83-case release set with ordinary, missing-evidence, permission-change, hostile-note, and truncated-stream examples. Block a candidate if it leaks a different tenant or misses a severe finding. Stage a passing version behind a reversible flag, retain version identity on each operation, and keep a direct route to original notes for human review.')
project['body'] += '<h2>Build contract</h2><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in [
    'Bind one operation to a user, tenant, case revision, input budget, and result permission.',
    'Show partial streamed text as incomplete until an authoritative terminal event.',
    'Deny tool effects that are not explicitly authorized by the user action.',
    'Release only after severe-error checks and retain a narrow rollback path.',
]) + '</ul>'
project['body'] += '<h2>Implementation checkpoint</h2><pre><code class="language-javascript">' + html.escape(code, quote=False) + '</code></pre>'
project['body'] += p('The checkpoint rejects a summary that cites evidence 63 when only evidence 47 is permitted. The real service must perform this test against authoritative record and revision data, not against a client-supplied set. The check is O(E) for E cited evidence IDs with expected O(1) set membership, and the retained set costs O(P) space for P permitted IDs. A large citation list needs its own cap. This function is one small gate; it cannot establish whether prose faithfully represents the evidence, so the release set and reviewer correction path cover that separate failure.')
project['body'] += '<h2>Failure drill</h2>' + p('Retry the same request from two tabs. Change the case revision, revoke the reviewer, insert a hostile instruction in a note, split a streamed frame across byte chunks, cut the connection before its terminal marker, and try to send a task to another tenant. None may produce a completed unauthorized result or a privileged side effect. Roll a candidate version to a small cohort, then inject one cross-tenant evidence reference. Activate the stop action and verify only new operations switch routes while old operation statuses retain their version and outcome. Inspect browser assets, logs, and telemetry labels for credentials and private note bodies. Test a keyboard and screen-reader journey that hears one completion or failure announcement rather than every arriving token.')
project['body'] += '<h2>Acceptance checks</h2><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in [
    'No provider credential or private note body is exposed in routine client assets and logs.',
    'A canceled or interrupted stream is never labeled complete without a terminal event.',
    'Retrieved text cannot authorize a tool call or expand tenant scope.',
    'A severe release failure blocks or rolls back new operations.',
]) + '</ul>'
project['body'] += '<h3>Common Mistakes</h3><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in [
    'Treating a convincing answer as a verified case decision.',
    'Using prompt wording as the only tool permission control.',
    'Counting an interrupted stream as a completed result.',
]) + '</ul>'
project['body'] += '<h2>Related lessons</h2><p>' + '; '.join(link(path) for path in lessons) + '.</p>'
entries.append(project)
by_path[project_path] = project

questions = [
    ('Where does a model service credential belong?', ['In a server-side gateway with restricted access', 'In a hidden browser field', 'In local storage after login'], 'A browser asset or browser storage value is available to page code and can be copied; the gateway must own the service credential and authorization.'),
    ('What should duplicate requests with the same scoped key do?', ['Find one admitted operation or return a payload conflict', 'Always start another paid operation', 'Overwrite the earlier input revision'], 'Binding the key to an authorized user action and input revision prevents a lost response from multiplying downstream work.'),
    ('Which budget catches a single very large generation call?', ['Input and output size plus actual work limits', 'Requests per minute alone', 'Only the browser tab count'], 'A low request rate can still admit one huge input or output; byte and work ceilings must apply before expensive work begins.'),
    ('When is a streamed answer complete?', ['After an authoritative terminal event and completed operation state', 'Whenever the transport closes', 'After the first visible paragraph'], 'A connection can end because of failure or cancellation. Partial text remains incomplete until the operation reaches a confirmed terminal result.'),
    ('How should the client handle an event from an old case route?', ['Discard it using operation and route identity', 'Append it to the new case page', 'Assume event order repairs the mismatch'], 'A stream can outlive navigation. Binding updates to the current operation and case revision prevents cross-case text from reaching the visible page.'),
    ('What does a browser abort prove?', ['The client stopped reading; server state must establish the final operation outcome', 'Provider billing was reversed', 'The result never completed'], 'Abort can race with provider completion and server persistence. The status resource remains the authority for the user-visible outcome.'),
    ('How should a retrieved note that asks for an export be treated?', ['As untrusted note content without export authority', 'As a new user command', 'As permission to add a mail tool'], 'Retrieved material can inform an answer but cannot change the user action, tool allowlist, or server authorization boundary.'),
    ('Where should a proposed tool call be authorized?', ['In the server handler against the real target at execution time', 'Only in the model prompt', 'Only in a browser confirmation label'], 'Structured tool arguments are still proposed data. The handler must validate them and check current permission on the actual resource.'),
    ('What should happen when permission changes after retrieval?', ['Deny result release or side effect under current permission', 'Trust the earlier retrieval check forever', 'Ask the model to decide if access is still fair'], 'A case can change owners while a long operation runs. Access needs a fresh check before releasing private output or applying an effect.'),
    ('Which result should block a candidate release?', ['One cross-tenant evidence leak despite a good average score', 'A shorter average answer', 'A small increase in first-byte time alone'], 'A severe privacy boundary failure must be examined as an individual event; a favorable average cannot erase it.'),
    ('What does a narrow rollback change?', ['New model operations while preserving old operation version identity', 'All historic status records', 'Every unrelated web feature flag'], 'A release flag can redirect future work without rewriting the version and outcome of operations that already ran.'),
    ('What must be checked before rendering generated references?', ['Evidence IDs, record permission, and safe text rendering', 'Only whether the response is fluent', 'Only whether the JSON parses'], 'A valid shape can still cite an unauthorized record, and raw generated markup can create a separate browser injection path.'),
]
quiz = copy.deepcopy(by_path['quizzes/web-development-graphics-editor-decisions'])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + quiz_path)), path=quiz_path,
            title='Web Development: model-backed application decisions quiz',
            summary='Twelve explained decisions about gateway budgets, streamed state, retrieved instructions, tool permission, and release.',
            sort_order=1316, created_at=stamp, updated_at=stamp, published_at=stamp)
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
project_hub['body'] += '<h2>Model-backed application project</h2><p>' + link(project_path) + ' — ' + html.escape(project['summary']) + '</p>'
project_hub['summary'] = 'Build and verify fifty-four projects across browser, API, data, identity, deployment, background work, abuse controls, and model-backed applications.'
project_hub['updated_at'] = stamp
quiz_hub = by_path['web-tech/quizzes']
quiz_hub['data']['modules'][0]['lessons'].append(quiz_path)
quiz_hub['body'] += '<h2>Model-backed application checks</h2><p>' + link(quiz_path) + ' — ' + html.escape(quiz['summary']) + '</p>'
quiz_hub['updated_at'] = stamp
hub = by_path['web-tech/model-backed-web-application-boundaries']
hub['body'] += '<h2>Practice path</h2><p>Build ' + link(project_path) + ' and check decisions in ' + link(quiz_path) + '.</p>'
hub['updated_at'] = stamp
for lesson_path in lessons:
    lesson = by_path[lesson_path]
    lesson['body'] += '<h2>Connected practice</h2><p>Build ' + link(project_path) + ' and review ' + link(quiz_path) + '.</p>'
    lesson['data']['related'].extend([project_path, quiz_path])
    lesson['updated_at'] = stamp
root_entry = by_path['web-tech/web-technology']
root_entry['body'] += '<h2>Model-backed application practice</h2><p>Apply this track with ' + link(project_path) + '.</p>'
root_entry['updated_at'] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_projects': 1, 'new_quizzes': 1, 'new_questions': len(questions)}))
