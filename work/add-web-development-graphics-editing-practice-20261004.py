"""Add connected interactive-graphics and rich-editing practice drafts."""
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
    dict(path='web-tech/accessible-inspection-map-export-project', title='Project: accessible inspection map and export', summary='Build structured region marks with SVG selection, Canvas preview, safe export, and an equivalent text path.', intro='Build an inspection map for case 62 with 47 mark records. Each record has an immutable ID, scene geometry, severity, and a short note. Render a bounded SVG overlay for actionable marks and a separate Canvas layer for a rapidly changing trace. Keep the data in the case model; neither SVG DOM nor Canvas pixels become the sole saved format. The companion list names every actionable region and uses the same selected ID as pointer input. Map pointer coordinates from the current CSS box into scene space, while backing pixels follow a capped device ratio. Resize and redraw without changing saved geometry. Load a private scan through an authorized route. Before offering an annotated bitmap download, prove the Canvas remains origin-clean; an unapproved image origin must leave structured marks intact and offer a permitted fallback. Derived exports have an owner, expiry, and private storage path. Check keyboard selection, focus, zoom, high contrast, and a graphic-disabled flow.', scope=['Select overlapping region 29 through both SVG and text list with the same result.','Resize from 620 to 310 CSS units and preserve scene coordinates.','Fail bitmap export on an unapproved image origin without losing marks.','Verify private export ownership, expiry, and account-switch cleanup.'], code='function selectRegion(selectedFromGraphic, selectedFromList) {\n  return selectedFromGraphic === selectedFromList ? selectedFromGraphic : null;\n}\nconsole.log(selectRegion(29, 29));\n// Output: 29', cost='An SVG node per actionable region adds DOM and accessibility-tree work, while a Canvas trace spends redraw and bitmap memory. A naïve hit test scans O(n) regions per pointer event; measure actual density before indexing. A high-density backing surface can multiply allocation, and export creates another encoded copy. Bound surface area and inspect peak memory on target devices. An equivalent list adds nodes but keeps the task usable when the graphic cannot render or be operated.', failure='Overlap two regions and prove draw order matches hit-test priority. Zoom and resize while one mark is selected; saved coordinates must not drift. Load a cross-origin image without export approval and catch the pixel-read failure. Keep the marks and explain the export path. Switch accounts and inspect decoded images and object URLs. Disable the graphic and use only the list to locate the high-severity seal split; every action must remain available.', checks=['Structured marks survive image or export failure.','Graphic and list share region identity and severity.','Pointer mapping works after resize and zoom.','Private derived files have an expiry path.'], mistakes=['Saving only the rendered bitmap.','Multiplying pointer coordinates by pixel ratio twice.','Calling a visible image exportable without checking origin-clean state.'], related=['web-tech/svg-canvas-scene-model-and-hit-testing','web-tech/canvas-pixel-ratio-and-pointer-coordinates','web-tech/canvas-origin-clean-export-and-private-assets','web-tech/accessible-graphic-controls-and-text-equivalents']),
    dict(path='web-tech/versioned-case-note-editor-project', title='Project: versioned case note editor', summary='Build a bounded rich note with IME-safe input, stable selection, sanitized paste, undo, and conditional autosave.', intro='Build a private case note editor for reviewer 47. The document model allows headings, paragraphs, text, emphasis, and approved links. A contenteditable surface receives browser input, but the saved document is a validated model. Composition input remains visible until committed, and input reconciliation catches edits that beforeinput could not cancel. Selection bookmarks use block ID and offset, then map through inserts, splits, merges, and formatting renders. Paste converts clipboard fragments into the narrow model; it does not store raw HTML, remote images, event attributes, or unsafe links. The server validates the same schema before saving. Group nearby typing into bounded undo steps. Autosave carries document generation, base revision, and idempotency key; a response for generation 6 cannot mark generation 7 saved. A conditional-write conflict preserves both local and server versions for review. Account switch clears private drafts and history. The editor must offer a plain-text path if rich formatting or browser-specific behavior fails.', scope=['Complete an IME composition without losing provisional or committed text.','Apply emphasis across a selection and preserve anchor and focus positions.','Paste unsafe markup, then verify saved and exported content follows one policy.','Receive an old autosave response while a newer generation remains dirty.'], code='function mayShowSaved(sentGeneration, currentGeneration, conflict) {\n  return !conflict && sentGeneration === currentGeneration;\n}\nconsole.log(mayShowSaved(6, 7, false));\n// Output: false', cost='A full snapshot per keystroke costs O(document size times history depth); grouped transactions or capped snapshots reduce memory. Parsing pasted fragments costs O(n) and needs byte and nesting limits. Rebuilding the entire DOM on each input can move the caret and stall typing. Debounced autosave reduces requests but extends unsaved time. Track edit latency, undo bytes, dirty duration, conflicts, and recovery success without collecting note text.', failure='Type through an IME while the editor rerenders and confirm no character is lost. Paste a fragment with an event attribute and unsupported image, then submit the same content directly to the API. Replace a text node during emphasis and verify the caret remains at its model position. Start autosave A, type again, then deliver A last; the editor must remain dirty. Cause a revision conflict and retain both versions. Undo a grouped edit, type a new branch, and confirm redo does not replay the old branch.', checks=['Committed text and saved model agree after composition.','Paste and direct API writes share the same safety policy.','Caret survives model transforms.','A stale save response never clears newer edits.'], mistakes=['Treating live editable DOM as the document authority.','Trusting a client paste filter as server validation.','Letting older autosave acknowledgments erase dirty state.'], related=['web-tech/editable-input-composition-and-document-model','web-tech/selection-bookmarks-and-transaction-mapping','web-tech/paste-import-sanitization-and-link-policy','web-tech/undo-history-autosave-and-revision-conflicts']),
]

for number, project in enumerate(projects, 1):
    assert project['path'] not in by_path
    subprocess.run(['node','--check','--input-type=module'], input=project['code'], text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path['web-tech/case-save-incident-evidence-project'])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + project['path'])), path=project['path'], title=project['title'], summary=project['summary'], sort_order=1240 + number, created_at=stamp, updated_at=stamp, published_at=stamp)
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
    ('What owns a selectable defect mark?', ['A structured region record with a stable ID', 'Only its Canvas pixels', 'Only its current SVG element'], 'Rendering can change or fail while the saved region identity and meaning remain available.'),
    ('When is SVG often a useful choice for an inspection overlay?', ['When a bounded set of meaningful shapes needs individual interaction', 'When millions of changing pixels need redraw each frame', 'When no text equivalent is required'], 'DOM-backed shapes can expose named controls, but density and update frequency still need measurement.'),
    ('What coordinate space should a saved mark use?', ['A defined scene space independent of CSS size and backing pixels', 'The pointer clientX value unchanged', 'Only the device-pixel backing coordinate'], 'A stable scene space survives resize, browser zoom, and display-density changes.'),
    ('What happens after drawing an unapproved cross-origin image onto Canvas?', ['Pixel readback and bitmap export can be blocked', 'The image can no longer be displayed', 'The browser grants export automatically'], 'Visible pixels do not prove the bitmap remains origin-clean for read or export.'),
    ('How should a graphic expose 47 actionable regions?', ['A synchronized set of names and controls outside or within the graphic', 'One generic image label only', 'Color changes without text'], 'Users need the region relationships and actions through a non-visual path tied to the same IDs.'),
    ('Why cap Canvas backing pixels on high-density screens?', ['Surface memory grows with pixel width times height', 'Pointer coordinates stop existing', 'SVG requires the same bitmap allocation'], 'Doubling both bitmap dimensions can roughly quadruple the surface storage before extra buffers.'),
    ('Why is beforeinput insufficient as the only editor update path?', ['Some browser edits are absent or non-cancelable there', 'It always fires after every server save', 'It replaces document validation'], 'Input reconciliation remains necessary for composition, corrections, and other browser editing paths.'),
    ('What should happen during an active IME composition?', ['Keep provisional text and defer destructive normalization', 'Rebuild the entire editable DOM after each provisional character', 'Reject every composition event'], 'Intermediate composition is not the same as a committed document transaction.'),
    ('What survives a formatting render when a DOM text node is replaced?', ['A model bookmark mapped through the transaction', 'The old Range object as a permanent location', 'Only the original pixel position'], 'Block IDs and offsets can map a caret to new nodes after document transforms.'),
    ('How should rich pasted HTML reach storage?', ['Convert it to an allowed model and validate again on the server', 'Store the original fragment for later export', 'Trust the paste because a user initiated it'], 'Clipboard HTML is untrusted, and the API must enforce the same document policy as the editor.'),
    ('When should a save response clear dirty state?', ['Only when it acknowledges the current local generation', 'Whenever any earlier request succeeds', 'Before the server checks the base revision'], 'A late response for generation 6 cannot claim that unsent generation 7 is saved.'),
    ('What does undo reverse in a rich editor?', ['A local edit transaction, not another reviewer’s server write', 'The entire database transaction history', 'Every email already sent from the case'], 'Undo history and server revision conflicts are separate timelines with different ownership.'),
]
quiz_path = 'quizzes/web-development-graphics-editor-decisions'
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path['quizzes/web-development-operations-sync-decisions'])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + quiz_path)), path=quiz_path, title='Web Development: graphics and editor decisions quiz', summary='Twelve explained decisions about scene models, pixel export, equivalent controls, composition, paste, selection, and autosave.', sort_order=1245, created_at=stamp, updated_at=stamp, published_at=stamp)
def quiz_item(number, value):
    prompt, options, explanation = value
    shift = number % 3
    return {'prompt':prompt,'options':options[shift:] + options[:shift], 'answer':(0 - shift) % 3, 'explanation':explanation}
quiz['data'] = {'subject_root':'web-tech/web-technology','section_path':'web-tech/quizzes','content_format':'html','seo_ready':False,'questions':[quiz_item(number, value) for number, value in enumerate(questions)]}
quiz['body'] = p(quiz['summary'] + ' Choose one answer, inspect its explanation, and return to the related boundary.')
quiz['body'] += '<h2>Related lessons</h2><p>' + '; '.join(link(path) for project in projects for path in project['related']) + '.</p>'
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path['web-tech/web-technology/project']
project_hub['data']['modules'][0]['lessons'].extend(project['path'] for project in projects)
project_hub['body'] += '<h2>Graphic and editor projects</h2><ul>' + ''.join('<li>' + link(project['path']) + ' — ' + html.escape(project['summary']) + '</li>' for project in projects) + '</ul>'
project_hub['summary'] = 'Build and verify forty-five projects across browser, API, data, identity, search, rendering, operations, privacy, feature release, GraphQL, compute, peer sessions, motion, regional recovery, graphics, and editing.'
project_hub['updated_at'] = stamp
quiz_hub = by_path['web-tech/quizzes']
quiz_hub['data']['modules'][0]['lessons'].append(quiz_path)
quiz_hub['body'] += '<h2>Graphic and editor checks</h2><p>' + link(quiz_path) + ' — ' + html.escape(quiz['summary']) + '</p>'
quiz_hub['updated_at'] = stamp
for hub_path, project_path in [('web-tech/interactive-graphics-and-canvas-boundaries', projects[0]['path']), ('web-tech/rich-document-editing-and-safe-content', projects[1]['path'])]:
    hub = by_path[hub_path]
    hub['body'] += '<h2>Practice path</h2><p>Build ' + link(project_path) + ' and check decisions in ' + link(quiz_path) + '.</p>'
    hub['updated_at'] = stamp
for entry in entries:
    if entry['type'] != 'article' or entry['data'].get('section_path') not in {'web-tech/interactive-graphics-and-canvas-boundaries','web-tech/rich-document-editing-and-safe-content'}:
        continue
    project_path = projects[0]['path'] if entry['data']['section_path'] == 'web-tech/interactive-graphics-and-canvas-boundaries' else projects[1]['path']
    entry['body'] += '<h2>Connected lessons</h2><p>Build ' + link(project_path) + ' and review ' + link(quiz_path) + '; follow ' + '; '.join(link(path) for path in entry['data']['related']) + '.</p>'
    entry['data']['related'].extend([project_path, quiz_path])
    entry['updated_at'] = stamp
root_entry = by_path['web-tech/web-technology']
root_entry['body'] += '<h2>Graphic and editor practice</h2><p>Apply the tracks with ' + link(projects[0]['path']) + ' and ' + link(projects[1]['path']) + '.</p>'
root_entry['updated_at'] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_projects':len(projects),'new_quizzes':1,'new_questions':len(questions)}))
