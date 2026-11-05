"""Add projects and a decision quiz for browser capabilities and mobile layouts."""
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
    dict(path='web-tech/field-intake-capability-fallback-project', title='Project: field intake with capability fallbacks', summary='Build optional camera, place, copy, and share actions without making permission a prerequisite for case intake.', intro='Build an intake form for a field case numbered 47. The operator can capture a photo, choose a file, add an approximate place, type that place manually, copy a case identifier, and share a review link. None of those browser capabilities may be requested on initial page load. Each request follows an explicit button action, has a pending and rejected state, and leaves a useful manual path. The photo preview must stop every live media track after capture or cancellation. A late camera permission approval after route leave must also release its stream. Location data has an accuracy and age policy, and the form never presents a wide-radius estimate as an exact address. The submitted file and location still pass server-side validation and authorization. A private review link must not grant access merely because it was shared.', scope=['Test allowed, denied, dismissed, unsupported, and operating-system-blocked capability paths.','Cancel or leave during a pending camera request, then inspect every track and object URL after resolution.','Compare recent and stale location readings; preserve manual place entry and approved retention scope.','Reject clipboard and share calls deliberately and verify usable selectable content and access-controlled links.'], code='function intakePath(cameraAllowed, locationAllowed) {\n  return { media: cameraAllowed ? "capture" : "file-picker", place: locationAllowed ? "review-estimate" : "manual-place" };\n}\nconsole.log(JSON.stringify(intakePath(false, true)));\n// Output: {"media":"file-picker","place":"review-estimate"}', cost='The capability check itself is O(1); media decoding uses space related to image size, and a live camera or location watch uses device resources until released. Avoid keeping multiple full-resolution copies of each preview. Measure task completion and recovery time for each rejected path, not just the fraction of granted prompts. Server checks add work proportional to the bytes and fields submitted; that cost is required because a browser-generated file is still untrusted. A manual path adds a small interface burden but allows the work to finish without device access.', failure='Request all capabilities when the form mounts; the test should flag that behavior immediately. Grant camera permission after leaving the route and check that no track remains active. Deny location and confirm the place field still saves. Return a position with a wide accuracy radius and confirm the operator must review it. Reject clipboard write and confirm the UI never says Copied; the identifier remains selectable. Share a link to another account and verify that opening it triggers a normal server access decision. Force an upload rejection and check that temporary media and pending states are cleaned up.', checks=['No optional capability is requested before its named user action.','Every media track and temporary preview is released after terminal transitions.','Denied and unsupported branches still permit a valid case submission.','Shared or copied identifiers do not bypass server authorization.'], mistakes=['Using permission grant as proof that capture or upload succeeded.','Leaving a camera stream open after a canceled form.','Treating approximate coordinates as a verified address.','Showing clipboard success before the write resolves.'], related=['web-tech/permission-request-timing-and-manual-fallback','web-tech/camera-microphone-capture-and-track-cleanup','web-tech/geolocation-accuracy-cancellation-and-retention','web-tech/clipboard-and-share-activation-fallbacks']),
    dict(path='web-tech/mobile-review-overlay-and-scroll-project', title='Project: mobile review overlay and scroll', summary='Keep a case-review feed, menu, modal editor, and reorder controls usable with touch, keyboard, and on-screen keyboard.', intro='Build a mobile case-review screen with a long activity feed, row action menu, modal note editor, and three reorderable evidence cards. The action menu must not clip inside the feed or rely on ever-larger z-index values. The note editor is modal: focus moves inside, background interaction follows the modal contract, Escape and a visible close control work, and focus returns to the invoking button. New activity appears without stealing a reviewer’s reading position. A New events control offers deliberate movement to the latest item. The evidence cards have Move up and Move down actions; drag can be an extra path, but cancellation cannot save a partial order. When the on-screen keyboard opens, the active field and save action remain reachable at zoomed and small sizes.', scope=['Test clipping and paint order inside transformed and overflow-scrolling ancestors.','Insert delayed images and new events while a reviewer reads old history; preserve a stable anchor.','Cancel a touch drag and compare its result with keyboard and button reorder paths.','Open the note editor with software and hardware keyboards, zoom, rotation, and route transitions.'], code='function applyReorder(evidenceIds, fromIndex, toIndex, canceled) {\n  if (canceled) return evidenceIds;\n  const nextIds = [...evidenceIds];\n  nextIds.splice(toIndex, 0, ...nextIds.splice(fromIndex, 1));\n  return nextIds;\n}\nconsole.log(applyReorder([47, 62, 89], 0, 2, true).join(","));\n// Output: 47,62,89', cost='A reorder copies O(n) identifiers when committed, while pointer movement should update only a lightweight preview. Holding thousands of feed rows increases DOM memory and layout work; list windowing may reduce cost but makes focus and anchoring harder to preserve. Overlay positioning can trigger layout if it measures on every scroll frame, so batch reads and writes and remove listeners when closed. Record scroll displacement, modal focus return, field visibility, and interaction latency in addition to visual screenshots. A single desktop pass cannot verify keyboard or touch behavior.', failure='Place the action menu under an overflow-clipped ancestor and raise z-index repeatedly; it must still be fixed at the correct placement boundary. Open the modal, scroll the feed, then close and confirm background scroll and focus return. Insert an image above the current event without reserved space; the current item should remain identifiable. Set touch-action none on the entire feed and see whether normal panning survives. Cancel a drag via pointercancel and confirm the server receives no mutation. Focus the last note field with a small visual viewport and confirm Save remains reachable. Repeat open and close to catch stale listeners.', checks=['Menus and modals have correct painting, dismissal, and focus behavior.','New content does not seize the reading position.','Reorder has equivalent button and keyboard paths with cancel rollback.','Focused fields and actions remain reachable with the on-screen keyboard.'], mistakes=['Trying to solve clipping with a large z-index.','Auto-following every new event while the reader is in history.','Making drag the only reorder mechanism.','Using a fixed modal height that hides actions under the keyboard.'], related=['web-tech/stacking-context-top-layer-and-overlay-contract','web-tech/scroll-containers-anchoring-and-chaining','web-tech/pointer-gesture-touch-action-and-alternate-control','web-tech/visual-viewport-keyboard-and-focused-input']),
]

for number, project in enumerate(projects, 1):
    assert project['path'] not in by_path
    subprocess.run(['node','--check','--input-type=module'], input=project['code'], text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path['web-tech/case-save-incident-evidence-project'])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + project['path'])), path=project['path'], title=project['title'], summary=project['summary'], sort_order=1170 + number, created_at=stamp, updated_at=stamp, published_at=stamp)
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
    ('When should the case form request camera access?', ['After the operator selects a capture action', 'Immediately when the dashboard loads', 'Only after the server accepts a completed case'], 'The permission has a clear purpose when capture is chosen. A manual file path still allows the case to proceed after denial.'),
    ('Does a granted browser permission prove the device can capture?', ['No; hardware, operating-system settings, and runtime errors can still stop capture', 'Yes; granted means a usable stream always follows', 'Yes; it also validates the uploaded file'], 'Permission state is one input. The actual capability call can still fail, and submitted bytes still require server validation.'),
    ('What must happen to media tracks after capture or cancel?', ['Stop every active track, including tracks returned after a late approval', 'Remove only the preview element', 'Leave tracks open until the browser closes'], 'A preview is separate from a live stream. Tracks must be stopped on terminal and stale-request paths to release devices.'),
    ('How should a wide-radius location estimate appear?', ['As an uncertain area the operator can review or replace manually', 'As a verified street address', 'As proof the operator visited the case site'], 'Coordinates carry uncertainty and time. A wide accuracy radius cannot establish an exact address or physical presence.'),
    ('What should a one-time place selection use?', ['A bounded one-shot request or a watch that is reliably cleared', 'A permanent background watch by default', 'A location request on every page visit'], 'The work needs one reading. A continuing watch adds repeated callbacks, privacy exposure, and battery cost unless explicitly required.'),
    ('When may a Copy button announce success?', ['After the clipboard write resolves', 'As soon as the user presses the button', 'Whenever a clipboard method exists'], 'A write can reject because of activation or permission conditions. False success can cause the user to paste stale content.'),
    ('Why can a menu still clip at a very large z-index?', ['An ancestor stacking or overflow boundary can still constrain it', 'The browser caps z-index at three digits', 'The menu text is too long'], 'A child cannot escape an ancestor clipping context merely by increasing its local paint order. Placement strategy must address the boundary.'),
    ('What distinguishes the note editor modal from a small menu?', ['The modal blocks background interaction and needs a focus return contract', 'The modal always has more text', 'The menu cannot use a close button'], 'Modality is an interaction behavior. Opening and closing the editor must manage focus and background access, not just paint order.'),
    ('What should happen when new feed events arrive during history reading?', ['Preserve the reader’s place and offer deliberate movement to new events', 'Always jump to the newest event', 'Remove old events immediately'], 'Automatic movement can destroy reading context. A stable anchor and New events control allow the reviewer to choose when to move.'),
    ('How should a canceled pointer reorder behave?', ['Restore the previous committed order and send no mutation', 'Commit the preview position', 'Disable the Move up and Move down buttons'], 'Pointer cancellation can occur during browser scrolling or interruption. Temporary gesture state must not become a committed update.'),
    ('Where should touch-action restrictions go for an optional drag?', ['On a narrow deliberate drag handle, with alternate controls', 'Across the entire feed', 'On every button in the form'], 'Broad restrictions can interfere with panning and zoom. The page remains usable when drag is optional and confined.'),
    ('What is the first layout goal when the mobile keyboard opens?', ['Keep the focused field and its actions reachable in visible space', 'Assume the layout viewport always shrinks', 'Pin every control to a fixed pixel height'], 'Keyboard behavior differs by device. Flexible scrolling and tested focus visibility matter more than one assumed keyboard dimension.'),
]

quiz_path = 'quizzes/web-development-browser-capability-and-viewport-decisions'
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path['quizzes/web-development-operations-sync-decisions'])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + quiz_path)), path=quiz_path, title='Web Development: browser capability and viewport decisions quiz', summary='Twelve explained decisions about permission, capture, location, sharing, overlays, scrolling, gestures, and keyboards.', sort_order=1175, created_at=stamp, updated_at=stamp, published_at=stamp)

def question_item(index, item):
    prompt, options, explanation = item
    shift = index % 3
    return {'prompt':prompt,'options':options[shift:] + options[:shift], 'answer':(0 - shift) % 3, 'explanation':explanation}

quiz['data'] = {'subject_root':'web-tech/web-technology','section_path':'web-tech/quizzes','content_format':'html','seo_ready':False,'questions':[question_item(number, item) for number, item in enumerate(questions)]}
quiz['body'] = p(quiz['summary'] + ' Choose an answer, inspect the explanation, and revisit the relevant lesson.')
quiz['body'] += '<h2>Related lessons</h2><p>' + '; '.join(link(item) for project in projects for item in project['related']) + '.</p>'
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path['web-tech/web-technology/project']
project_hub['data']['modules'][0]['lessons'].extend(item['path'] for item in projects)
project_hub['body'] += '<h2>Capability and viewport projects</h2><ul>' + ''.join('<li>' + link(item['path']) + ' — ' + html.escape(item['summary']) + '</li>' for item in projects) + '</ul>'
project_hub['summary'] = 'Build and verify thirty projects across browser, API, data, identity, search, quality, rendering, forms, navigation, delivery, streaming, accessibility, operations, synchronization, authorization, privacy, offline, live, capability, and viewport contracts.'
project_hub['updated_at'] = stamp
quiz_hub = by_path['web-tech/quizzes']
quiz_hub['data']['modules'][0]['lessons'].append(quiz_path)
quiz_hub['body'] += '<h2>Capability and viewport checks</h2><p>' + link(quiz_path) + ' — ' + html.escape(quiz['summary']) + '</p>'
quiz_hub['updated_at'] = stamp

for hub_path, project_path in [('web-tech/browser-capabilities-and-permission-lifecycle', projects[0]['path']), ('web-tech/overlays-scroll-and-mobile-viewport', projects[1]['path'])]:
    hub = by_path[hub_path]
    hub['body'] += '<h2>Practice path</h2><p>Build ' + link(project_path) + ' and check decisions in ' + link(quiz_path) + '.</p>'
    hub['updated_at'] = stamp
for entry in entries:
    if entry['type'] != 'article' or entry['data'].get('section_path') not in {'web-tech/browser-capabilities-and-permission-lifecycle', 'web-tech/overlays-scroll-and-mobile-viewport'}:
        continue
    project_path = projects[0]['path'] if entry['data']['section_path'] == 'web-tech/browser-capabilities-and-permission-lifecycle' else projects[1]['path']
    entry['body'] += '<h2>Apply and check</h2><p>Build ' + link(project_path) + ' and review ' + link(quiz_path) + '.</p>'
    entry['data']['related'].extend([project_path, quiz_path])
    entry['updated_at'] = stamp
root_entry = by_path['web-tech/web-technology']
root_entry['body'] += '<h2>Capability and viewport practice</h2><p>Apply the device and mobile interaction contracts with ' + link(projects[0]['path']) + ' and ' + link(projects[1]['path']) + '.</p>'
root_entry['updated_at'] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_projects':len(projects), 'new_quizzes':1, 'new_questions':len(questions)}))
