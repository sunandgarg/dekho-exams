"""Add projects and quiz for component contracts and progressive browser support."""
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
    {
        'path': 'web-tech/case-decision-web-component-project',
        'title': 'Project: interoperable case-decision control',
        'summary': 'Build a form-capable case decision element that survives late upgrade, host moves, and theme changes.',
        'hub': 'web-tech/web-component-contracts-and-interoperability',
        'intro': 'Build a case-decision control used by two permit-review applications. Start with a server-rendered select named decision for case 47 so the review can be submitted before the custom element definition loads. The optional element presents policy help and a clearer selected state. It receives the case ID and current decision as attributes, accepts a slotted heading and help link, and emits one case-decision event with only the stable code and case ID. Its public names, event version, and styling hooks are documented. The host validates authorization and persists the decision. The component does not fetch private case text or treat an event as permission. When enhanced, an autonomous form-associated element writes one value through ElementInternals; the fallback control must no longer be a second successful control. The component handles reset, disabled state, and invalid selection. It starts any subscriptions only while connected, makes setup idempotent, and releases listeners on removal. If the host moves the same node, a reconnect must not double-submit. Styling uses two inherited tokens and a named summary part, with defaults that remain readable in an unfamiliar host. A shared static stylesheet is used only for global rules. The first application may theme one card without changing the others. The project succeeds when the server receives the same stable code from the plain and enhanced paths, not merely when the element looks correct.',
        'scope': ['Submit one stable code through both the plain and enhanced paths.', 'Keep slotted content and events usable without internal selectors.', 'Survive delayed definition, repeated connection, and host replacement.', 'Preserve focus and visible state through reset, errors, and theme changes.'],
        'code': "function acceptedDecision(caseRecord, eventDetail) {\n  const allowed = new Set(['approve', 'return', 'defer']);\n  return eventDetail.version === 2 && eventDetail.caseId === caseRecord.id &&\n    allowed.has(eventDetail.code) && caseRecord.editable;\n}\nconsole.log(acceptedDecision({ id: 47, editable: true }, { version: 2, caseId: 62, code: 'approve' }));\n// Output: false",
        'cost': 'A three-choice decision is O(1) to validate locally; the server check is still required. The extra component bundle, shadow tree, and integration tests add weight relative to a native select. In a list of n cases, one listener or observer per card consumes O(n) resources. A per-card polling loop is a larger network and battery cost, so prefer one host-owned feed. A shared sheet avoids repeated static CSS parsing, but changing its rules can invalidate styles across every adopter. Record bundle size, mount time for 83 cards, keyboard completion, and failed submissions before replacing the plain form as the default path.',
        'failure': 'Block the component script and submit from the native select. Load the definition late, then submit again and inspect FormData for exactly one decision field. Change the selected case while a delayed event is in flight and reject its stale case ID. Move the element four times; prove there is still one active listener and one server mutation per click. Replace the slotted help link without rebuilding the card. Reset and disable the form, then test a server-rejected choice. Check focus after an error and after the card is removed. Apply a local dark theme to one of 83 cards; the other cards must retain their values. Run keyboard and screen-reader checks rather than assuming shadow markup is usable.',
        'checks': ['One named field reaches the server with a stable code.', 'The pre-upgrade and failed-script paths can finish the review.', 'Moving the element does not multiply subscriptions or mutations.', 'The host can theme one card and operate it without private selectors.'],
        'mistakes': ['Leaving both enhanced and fallback controls successful.', 'Assuming a composed event grants server authority.', 'Using the shadow root as a privacy boundary.'],
        'related': ['web-tech/custom-element-upgrade-and-reconnection', 'web-tech/shadow-slots-events-and-focus-contract', 'web-tech/form-associated-custom-control-and-native-fallback', 'web-tech/shadow-style-tokens-parts-and-shared-sheets'],
    },
    {
        'path': 'web-tech/progressive-case-export-release-project',
        'title': 'Project: progressive case export release',
        'summary': 'Ship an optional local-save path with a server fallback, selective compatibility code, and a device release gate.',
        'hub': 'web-tech/progressive-browser-compatibility',
        'intro': 'Build a case-export release for reviewer 62. The ordinary server-rendered link downloads an authorized case report and works without client script. An optional Save to folder action appears when the browser exposes the required file API and the rollout flag is enabled. The server still checks record authorization and issues a versioned export; neither the browser probe nor the flag changes permission. A canceled picker leaves the normal download available. A partial write is not called complete. The report path also uses a date formatter that needs optional compatibility code in one supported embedded web view. Load that code only when a report is opened on a device that lacks the native method, and keep a plain date fallback when the optional request fails. The build target must parse in every supported engine before runtime checks can start. Define a browser and device policy from real reviewer usage, including a low-end phone and the embedded station. Run the complete open, export, and confirm journey using keyboard and touch; test text composition when notes precede export. Roll out to a small cohort, record bounded outcome categories, and retain the server path through an observation window. A kill action must disable Save to folder without waiting for another client deploy. Retire the server path only after supported devices finish the same task and the team has a reversal plan.',
        'scope': ['Preserve an authorized download when script, picker, or optional code fails.', 'Keep optional compatibility bytes off the initial dashboard path.', 'Verify exports by completion and server revision across target devices.', 'Roll back the enhancement without removing the existing task path.'],
        'code': "function chooseCaseExport(release, device) {\n  if (!release.authorized) return 'deny';\n  if (!release.folderSaveEnabled || !device.filePicker) return 'server-download';\n  return 'offer-both';\n}\nconsole.log(chooseCaseExport({ authorized: true, folderSaveEnabled: true }, { filePicker: false }));\n// Output: server-download",
        'cost': 'The feature probe is O(1), while file writing and download transfer cost O(report bytes). Deferred compatibility code saves initial parse and transfer work for people who never open a report, but adds a later request and another failure path. Two export routes also require two sets of completion, cancellation, and cleanup tests. Measure initial bundle bytes, optional code bytes, report completion rate, export latency, and peak memory on the lowest supported device. A support matrix that tests every possible combination is too expensive; gate each critical task on supported engines and add targeted device and input cases for platform boundaries.',
        'failure': 'Disable JavaScript and confirm the server link still downloads case 62. Present the file picker but have it throw, deny permission, cancel, and fail on close; none of those states may claim a finished local file. Block the optional formatter package in the embedded station and keep dates legible. Use an engine that rejects an untransformed syntax feature to test the build target. Open a 47-page report on a low-memory phone and take the server path if client preview fails. Switch accounts during a delayed export response and reject stale case data. Flip the release kill switch while an older tab remains open, then verify its next export uses the server route. Keep outcome logs free of case IDs and report bytes.',
        'checks': ['The baseline task works without JavaScript.', 'Optional code loads only on the report path that needs it.', 'Success is recorded after completed bytes and matching revision.', 'A kill action and old-tab path preserve export access.'],
        'mistakes': ['Equating API presence with an export guarantee.', 'Shipping optional compatibility code on every dashboard view.', 'Removing the server route after one desktop trial.'],
        'related': ['web-tech/feature-probes-and-functional-fallbacks', 'web-tech/polyfill-cost-and-target-browser-policy', 'web-tech/cross-browser-input-and-device-contracts', 'web-tech/capability-rollout-and-fallback-retirement'],
    },
]

for number, project in enumerate(projects, 1):
    assert project['path'] not in by_path
    subprocess.run(['node', '--check', '--input-type=module'], input=project['code'], text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path['web-tech/case-save-incident-evidence-project'])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + project['path'])), path=project['path'],
                 title=project['title'], summary=project['summary'], sort_order=1290 + number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    entry['data'] = {'subject_root': 'web-tech/web-technology', 'section_path': 'web-tech/web-technology/project',
                     'content_format': 'html', 'seo_ready': False, 'kind': 'project',
                     'author_path': 'authors/aitrove-editorial', 'reading_minutes': 8, 'related': project['related']}
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
    ('What must work before a custom element definition arrives?', ['The baseline task and meaningful server-rendered content', 'Only the component animation', 'Only its internal shadow selectors'], 'An unknown custom element can be rendered before registration. The core case task should remain usable while enhancement code loads or fails.'),
    ('What is required on repeated component connection?', ['Idempotent setup and release of active resources', 'A fresh polling timer each time', 'A new registry definition for the same name'], 'Moving or reconnecting a node can repeat lifecycle callbacks. Duplicate listeners and timers create repeated mutations and retained work.'),
    ('When should a component event cross a shadow boundary?', ['When the documented host contract needs it', 'For every internal keydown', 'Only when it contains private note text'], 'A composed and bubbling task event can reach the host, while internal interaction events should stay inside unless explicitly part of the API.'),
    ('What does an open shadow root guarantee?', ['Access for integration and inspection, not private-data security', 'Server authorization', 'That all host styles apply to internal nodes'], 'Shadow visibility changes DOM access patterns. It does not protect secrets or replace permission checks on server operations.'),
    ('How does a custom control contribute a form value?', ['Through a form association contract and current submitted value', 'By displaying a label in shadow markup', 'By dispatching any click event'], 'The outer form needs a successful control value. Visual selection alone can leave FormData empty or stale.'),
    ('What should happen to a fallback control after enhancement?', ['Exactly one named successful control should submit', 'Both paths should submit the same name', 'The fallback must be removed before script loads'], 'Two successful controls with one name can produce ambiguous values; the plain path must still exist during failed or delayed enhancement.'),
    ('When is a shared constructed stylesheet suitable?', ['For rules intended to change across every adopter', 'For one card override by mutating the shared sheet', 'As a data-protection boundary'], 'A shared sheet affects all roots that adopt it. Per-host tokens are a better contract for local visual changes.'),
    ('What does a feature probe establish?', ['That an API appears available now, not that the whole task succeeds', 'That the user granted permission', 'That the server authorized the record'], 'Presence checks do not cover invocation failure, cancellation, write completion, or private record authorization.'),
    ('Can a runtime polyfill repair syntax an engine cannot parse?', ['No; parse compatibility belongs in the build target or alternate bundle', 'Yes, after the parser throws', 'Only when a file picker exists'], 'The engine must parse the bundle before a polyfill can run. Syntax and missing runtime APIs are different compatibility boundaries.'),
    ('What belongs in a browser test gate?', ['Completed user tasks across supported engines and input modes', 'Matching screenshots alone', 'The newest desktop browser only'], 'Focus, composition, touch, save state, and platform permissions can fail even when the static layout looks identical.'),
    ('What does a release flag do for an unsupported browser?', ['It controls exposure but cannot add a missing capability', 'It grants permission to private records', 'It guarantees enough device memory'], 'Capability, exposure, and authorization are separate checks; each can block an enhanced path for a different reason.'),
    ('When can a fallback be retired?', ['After supported environments show task completion and a reversal plan exists', 'After one desktop demonstration', 'As soon as the new API appears in a browser table'], 'Retirement should follow measured task outcomes, active-client windows, and a path to restore the old behavior if hidden users remain.'),
]
quiz_path = 'quizzes/web-development-components-compatibility-decisions'
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path['quizzes/web-development-graphics-editor-decisions'])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + quiz_path)), path=quiz_path,
            title='Web Development: components and compatibility quiz',
            summary='Twelve explained decisions about component contracts, forms, styling, feature probes, testing, and fallback retirement.',
            sort_order=1295, created_at=stamp, updated_at=stamp, published_at=stamp)

def quiz_item(number, value):
    prompt, options, explanation = value
    shift = number % 3
    return {'prompt': prompt, 'options': options[shift:] + options[:shift],
            'answer': (0 - shift) % 3, 'explanation': explanation}

quiz['data'] = {'subject_root': 'web-tech/web-technology', 'section_path': 'web-tech/quizzes',
                'content_format': 'html', 'seo_ready': False,
                'questions': [quiz_item(number, value) for number, value in enumerate(questions)]}
quiz['body'] = p(quiz['summary'] + ' Choose one answer and inspect the explanation before testing the related contract.')
quiz['body'] += '<h2>Related lessons</h2><p>' + '; '.join(link(path) for project in projects for path in project['related']) + '.</p>'
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path['web-tech/web-technology/project']
project_hub['data']['modules'][0]['lessons'].extend(project['path'] for project in projects)
project_hub['body'] += '<h2>Component and compatibility projects</h2><ul>' + ''.join(
    '<li>' + link(project['path']) + ' — ' + html.escape(project['summary']) + '</li>' for project in projects) + '</ul>'
project_hub['summary'] = 'Build and verify fifty-one projects across browser, API, data, identity, search, rendering, operations, privacy, deployment, offline storage, key custody, components, and compatibility.'
project_hub['updated_at'] = stamp
quiz_hub = by_path['web-tech/quizzes']
quiz_hub['data']['modules'][0]['lessons'].append(quiz_path)
quiz_hub['body'] += '<h2>Component and compatibility checks</h2><p>' + link(quiz_path) + ' — ' + html.escape(quiz['summary']) + '</p>'
quiz_hub['updated_at'] = stamp

for project in projects:
    hub = by_path[project['hub']]
    hub['body'] += '<h2>Practice path</h2><p>Build ' + link(project['path']) + ' and check decisions in ' + link(quiz_path) + '.</p>'
    hub['updated_at'] = stamp
    for lesson_path in project['related']:
        lesson = by_path[lesson_path]
        lesson['body'] += '<h2>Connected practice</h2><p>Build ' + link(project['path']) + ' and review ' + link(quiz_path) + '.</p>'
        lesson['data']['related'].extend([project['path'], quiz_path])
        lesson['updated_at'] = stamp
root_entry = by_path['web-tech/web-technology']
root_entry['body'] += '<h2>Component and compatibility practice</h2><p>Apply the tracks with ' + link(projects[0]['path']) + ' and ' + link(projects[1]['path']) + '.</p>'
root_entry['updated_at'] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_projects': len(projects), 'new_quizzes': 1, 'new_questions': len(questions)}))
