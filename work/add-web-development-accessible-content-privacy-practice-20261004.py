"""Add accessible-content and privacy-integration projects and quiz."""
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
    dict(path='web-tech/accessible-inspection-report-project', title='Project: accessible inspection report', summary='Publish a report whose images, chart, clip, and route structure remain useful without sight, sound, color, or pointer hover.', intro='Build an inspection report for case 47 with a photo of a cracked valve, a four-week district chart, and a short procedure clip. The photo’s alternative must convey the crack where that fact is not already stated; repeated decorative artwork gets an empty alternative, and an image-only zoom action names the action. The chart’s summary and values derive from the same filtered data revision as its visual bars. The procedure clip has reviewed captions, a descriptive transcript, and controls that can be reached and operated with a keyboard. The report uses meaningful headings, distinct navigation landmarks, and a skip path. Client-side navigation into the report sets a useful title and focus target. The case authorization rule applies equally to text equivalents, media tracks, and chart values.', scope=['Write the task each visual or audio element supports, then test it with that sensory channel unavailable.','Change a chart filter and revision; assert that the graphic, result sentence, and data list agree.','Recut the video and ensure old captions or transcripts cannot be published as current.','Use keyboard and assistive-technology navigation across direct load, client route change, error, and back navigation.'], code='function mediaAndChartReady(reportRevision, chartRevision, captionRevision) {\n  return reportRevision === chartRevision && reportRevision === captionRevision;\n}\nconsole.log(mediaAndChartReady(8, 8, 7));\n// Output: false', cost='Generating a text view of n chart records costs O(n) time and output space, while an image alternative is constant-sized per placement. A long report may need paged data or an export so the equivalent does not become a wall of numbers. Captions and transcripts add editorial and version-review work; playback transfer remains dominated by media bytes. Semantic landmarks have negligible runtime cost, but moving focus on every re-render can disrupt users, so apply it only on meaningful route arrival. Track mismatched revisions, keyboard task completion, and unauthorized access attempts to equivalent routes.', failure='Remove the photo and ask a reviewer to locate the crack. If the text path cannot support the decision, revise it. Disable chart color and hover and ask which district crossed its threshold. Change the filter without updating the summary and ensure a test detects the mismatch. Publish a video revision with an older caption track and expect a release failure. Put the clip behind case authorization while leaving transcript access public and verify that the security check rejects it. Finally move from search to the report with keyboard only; focus must land on a present route target.', checks=['Photo and action alternatives convey purpose without repetitive noise.','Chart text and visual values share filter, revision, and access scope.','Reviewed media alternatives match the published clip.','Landmarks, skip path, title, and focus support every route state.'], mistakes=['Using one file-level alternative regardless of context.','Calling a chart accessible when it only says chart.','Treating generated captions as reviewed technical instructions.','Leaving focus on an unmounted search result.'], related=['web-tech/image-alternatives-by-purpose','web-tech/chart-and-diagram-text-equivalents','web-tech/captions-transcripts-and-media-controls','web-tech/landmarks-headings-and-skip-paths']),
    dict(path='web-tech/privacy-safe-support-and-measurement-project', title='Project: privacy-safe support and measurement', summary='Gate optional vendor paths, minimize event schemas, and enforce preference changes across tabs and jobs.', intro='Build a case-review page with an optional support widget and a product-measurement event for Export starts. Inventory every external request before and after the widget opens, including requests initiated by vendor code. The core review flow must complete when the vendor is blocked. The widget cannot rely on unrestricted third-party cookies, and its fallback opens a controlled top-level support path or local contact route. The host does not pass a session token or raw case note into a frame message. The optional event carries only an approved name, coarse route class, release, and outcome. A preference change stops new optional event creation, clears or suppresses queued batches under the product policy, and reaches other tabs and server jobs within a stated bound. Previously transferred data is handled according to the approved retention contract, not described as remotely retractable.', scope=['Capture request graphs on signed-out and private routes, before and after support activation.','Block vendor network and storage access; verify case review, save, and support fallback outcomes.','Reject unknown event fields, private notes, raw URLs, and reviewer identifiers before queuing.','Change preference across active and suspended tabs, offline replay, and a running server job; measure enforcement delay.'], code='function optionalMeasurementAllowed(preference, eventVersion) {\n  return preference.enabled && preference.version === eventVersion;\n}\nconsole.log(optionalMeasurementAllowed({ enabled: false, version: 9 }, 8));\n// Output: false', cost='Each external script adds transfer, parse, and execution cost; on-demand loading can avoid that work for people who never request support. Event validation is O(k) for k fields, and clearing n queued optional events is O(n). Rechecking a server-backed preference on every event adds reads, so a bounded cache or version invalidation may be appropriate if its delay matches the product promise. Request inventories take review time because vendor destinations may change independently of application code. Measure unexpected hosts, bytes, long tasks, denied widget starts, event leakage, and preference propagation delay.', failure='Load support on page start and inspect whether a private case route reaches the vendor before user action. Block third-party storage and confirm the widget does not loop forever or block the case form. Send an unexpected caseNote property through the event builder and confirm the schema rejects it. Queue events in two tabs, change the preference in one, suspend the other, then wake it and inspect outgoing requests. Let a server job start before the preference change and ensure its later optional sends follow the defined cutoff. Replace the widget frame origin in a test and verify no host credential is posted.', checks=['Observed external requests have a named purpose, owner, and allowed data contract.','Vendor failure and blocked storage do not block the primary task.','Event payloads reject private or unknown fields before transfer.','Preference changes stop optional sends across tabs and server paths within the stated bound.'], mistakes=['Trusting a package list instead of observing runtime requests.','Passing a host token to an embedded widget.','Disabling a dashboard while leaving event collection active.','Assuming a sleeping tab has received a broadcast.'], related=['web-tech/third-party-request-and-script-inventory','web-tech/optional-analytics-event-boundaries','web-tech/embedded-widget-storage-and-fallback','web-tech/preference-change-propagation-and-audit']),
]

for number, project in enumerate(projects, 1):
    assert project['path'] not in by_path
    subprocess.run(['node','--check','--input-type=module'], input=project['code'], text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path['web-tech/case-save-incident-evidence-project'])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + project['path'])), path=project['path'], title=project['title'], summary=project['summary'], sort_order=1180 + number, created_at=stamp, updated_at=stamp, published_at=stamp)
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
    ('What determines useful alternative text for a report image?', ['Its purpose in that placement and the missing decision fact', 'The image filename alone', 'A fixed description copied to every route'], 'The same file can perform different roles. Write the action or information a reader needs in that context, and avoid repeating nearby text.'),
    ('How should a purely decorative separator be represented?', ['With an explicit empty alternative', 'With the words decorative blue separator', 'Without deciding whether it has meaning'], 'A decorative image adds no task information. An empty alternative lets assistive technology skip it rather than reading noise or a filename.'),
    ('What is needed beyond a short label for a complex chart?', ['A synchronized text path to its key result and values', 'Only a colorful legend', 'Only a hover tooltip'], 'A short label identifies the visual but cannot answer detailed comparison questions. Text must match the chart filter, revision, and access scope.'),
    ('Why should chart text and bars use one normalized data revision?', ['So filters and updates cannot leave them contradicting each other', 'So the image file downloads faster', 'So authorization checks can be skipped'], 'Manually maintained equivalents drift after a data change. Shared data and revision checks keep the visual and text answers consistent.'),
    ('What belongs in captions for a procedure clip?', ['Speech and meaningful non-speech sounds with timing', 'Only the clip title', 'Only a list of visible objects'], 'Timed captions carry the audio information needed to follow the clip. Essential silent visual actions need a descriptive path as well.'),
    ('When must a clip’s transcript or captions be reviewed again?', ['When the media revision changes in a way that can affect content or timing', 'Only when the page color changes', 'Never once they were generated'], 'A recut can alter wording, time cues, and visual actions. Version checks prevent old tracks from appearing current.'),
    ('What does a skip path solve?', ['Repeated navigation before the main content for keyboard users', 'Every form validation problem', 'The need for headings'], 'A working skip control lets a person bypass repeated page chrome. It complements meaningful landmarks and headings rather than replacing them.'),
    ('What should happen to focus after client-side route arrival?', ['Move or announce it at a present, meaningful route target', 'Leave it on a removed link', 'Move it on every background data refresh'], 'Route changes need an arrival cue. A focus effect tied to every render can be disruptive, so bind it to navigation completion.'),
    ('How can a team discover unexpected vendor data paths?', ['Inspect runtime requests across routes and interactions', 'Read only the package manifest', 'Assume an iframe sends nothing'], 'Vendor code may load more resources, pixels, or beacons. The observed request graph exposes destinations and payloads that source search can miss.'),
    ('When should an optional analytics choice be enforced?', ['Before event construction, storage, and transfer', 'Only when a dashboard is viewed', 'Only after a batch reaches the vendor'], 'Suppressing display does not undo collection. The current approved choice must control optional event creation and delivery.'),
    ('What if an embedded support widget lacks third-party cookie access?', ['Provide an independent top-level or local support fallback', 'Send the host session token to the frame', 'Block the case form until it signs in'], 'Embedded storage is not a stable login assumption. The primary task remains usable, and a fallback avoids transferring host credentials.'),
    ('What must a preference change cover beyond the visible tab?', ['Other tabs, queued events, server jobs, and later sessions at the chosen scope', 'Only the setting label', 'Only requests started before the change'], 'The preference is a versioned policy decision. Sleeping tabs and background work can otherwise continue optional sends after the user changes it.'),
]

quiz_path = 'quizzes/web-development-accessible-content-privacy-decisions'
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path['quizzes/web-development-operations-sync-decisions'])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + quiz_path)), path=quiz_path, title='Web Development: accessible content and privacy decisions quiz', summary='Twelve explained decisions about image and media meaning, page structure, external requests, analytics, embeds, and preferences.', sort_order=1185, created_at=stamp, updated_at=stamp, published_at=stamp)

def item(number, value):
    prompt, options, explanation = value
    shift = number % 3
    return {'prompt':prompt,'options':options[shift:] + options[:shift], 'answer':(0 - shift) % 3, 'explanation':explanation}

quiz['data'] = {'subject_root':'web-tech/web-technology','section_path':'web-tech/quizzes','content_format':'html','seo_ready':False,'questions':[item(number, value) for number, value in enumerate(questions)]}
quiz['body'] = p(quiz['summary'] + ' Choose one answer, inspect the explanation, and revisit the relevant boundary.')
quiz['body'] += '<h2>Related lessons</h2><p>' + '; '.join(link(path) for project in projects for path in project['related']) + '.</p>'
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path['web-tech/web-technology/project']
project_hub['data']['modules'][0]['lessons'].extend(project['path'] for project in projects)
project_hub['body'] += '<h2>Accessible content and privacy projects</h2><ul>' + ''.join('<li>' + link(project['path']) + ' — ' + html.escape(project['summary']) + '</li>' for project in projects) + '</ul>'
project_hub['summary'] = 'Build and verify thirty-two projects across browser, API, data, identity, search, quality, rendering, forms, navigation, delivery, streaming, accessibility, operations, synchronization, authorization, privacy, offline, live, capability, viewport, and content contracts.'
project_hub['updated_at'] = stamp
quiz_hub = by_path['web-tech/quizzes']
quiz_hub['data']['modules'][0]['lessons'].append(quiz_path)
quiz_hub['body'] += '<h2>Accessible content and privacy checks</h2><p>' + link(quiz_path) + ' — ' + html.escape(quiz['summary']) + '</p>'
quiz_hub['updated_at'] = stamp
for hub_path, project_path in [('web-tech/accessible-content-and-media', projects[0]['path']), ('web-tech/privacy-aware-external-integrations', projects[1]['path'])]:
    hub = by_path[hub_path]
    hub['body'] += '<h2>Practice path</h2><p>Build ' + link(project_path) + ' and check decisions in ' + link(quiz_path) + '.</p>'
    hub['updated_at'] = stamp
for entry in entries:
    if entry['type'] != 'article' or entry['data'].get('section_path') not in {'web-tech/accessible-content-and-media','web-tech/privacy-aware-external-integrations'}:
        continue
    project_path = projects[0]['path'] if entry['data']['section_path'] == 'web-tech/accessible-content-and-media' else projects[1]['path']
    entry['body'] += '<h2>Apply and check</h2><p>Build ' + link(project_path) + ' and review ' + link(quiz_path) + '.</p>'
    entry['data']['related'].extend([project_path, quiz_path])
    entry['updated_at'] = stamp
root_entry = by_path['web-tech/web-technology']
root_entry['body'] += '<h2>Accessible content and privacy practice</h2><p>Apply the content and external-data contracts with ' + link(projects[0]['path']) + ' and ' + link(projects[1]['path']) + '.</p>'
root_entry['updated_at'] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_projects':len(projects),'new_quizzes':1,'new_questions':len(questions)}))
