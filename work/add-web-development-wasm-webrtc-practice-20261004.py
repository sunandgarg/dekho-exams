"""Add connected browser compute and peer session practice drafts."""
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
    dict(path='web-tech/local-scan-analysis-worker-project', title='Project: bounded local scan analysis', summary='Deliver a versioned Wasm worker with memory limits, stale-result protection, and explicit fallback.', intro='Build a private document-review editor for reviewer 29. It loads a pinned processing module only after the reviewer chooses local analysis. A selected 47-megabyte scan stays in the browser unless the reviewer explicitly chooses a separate server path. The adapter validates dimensions, allocates bounded tiles, copies input into linear memory, copies output back before release, and refreshes any typed view after ordinary memory growth. Run processing in one worker. Each job carries a generation; if scan 62 replaces scan 47, the older result cannot overwrite the current editor. A cancellation request stops work between tiles, while a stuck synchronous export can be isolated by terminating its worker. Preserve the selected file and typed notes if binary delivery, compilation, worker startup, or allocation fails. A JavaScript fallback must produce the same output contract. Compare complete task latency, main-thread long tasks, peak memory, and fallback rate on a low-memory device before accepting the binary path.', scope=['Pin adapter and binary versions and test a content-type or compilation failure.','Exercise memory growth, an allocation failure, and cleanup after cancellation.','Send two jobs in reverse completion order and keep only the latest selection.','Compare cold and warm total task time against the JavaScript fallback.'], code='function visibleResult(activeGeneration, candidateGeneration, bytesReady) {\n  return bytesReady && activeGeneration === candidateGeneration;\n}\nconsole.log(visibleResult(62, 47, true));\n// Output: false', cost='The inner transform can be fast while download, decode, byte copies, and worker startup dominate user time. Tile processing costs O(n) bytes and bounds peak allocation; it does not eliminate the source and output buffers. One worker limits contention but can queue work. A transfer avoids a copy only when the sender can give up ownership. Track the whole interaction and retained bytes rather than a microbenchmark of one exported function.', failure='Block the module request after a file is chosen and verify the editor preserves the file. Force a stale adapter version and show the fallback, not a blank panel. Grow memory between tile calls and refresh the view. Start scan 47, then scan 62; deliver scan 47 last and verify it is ignored. Crash the worker while a tile is allocated, then leave the page and inspect whether the worker, object URL, and buffer references have been released.', checks=['No unconsented upload occurs in the local path.','Old jobs cannot replace a newer result.','Failure keeps the review form recoverable.','Measured total time and memory justify the module.'], mistakes=['Timing only an exported function.','Retaining a typed view after memory growth.','Assuming a cancellation message interrupts synchronous native work.'], related=['web-tech/wasm-loading-artifact-and-fallback-contract','web-tech/wasm-linear-memory-ownership-and-copy-cost','web-tech/wasm-worker-jobs-cancellation-and-result-order','web-tech/wasm-capabilities-isolation-and-performance-budget']),
    dict(path='web-tech/private-peer-consultation-project', title='Project: private peer consultation', summary='Build an authorized audio room with bounded signaling, relay recovery, and durable server notes.', intro='Build a consultation for reviewers 29 and 47 on case 62. The room checks current case membership before either browser subscribes to signaling and before each forwarded offer, answer, or candidate. A signal envelope includes room, sender, recipient, generation, message type, and a bounded payload. Old generations are ignored after reconnect. The user starts an audio-only capture from an explicit control; a denied prompt leaves typed notes available. Each acquired local track stops on leave, revocation, failed setup, and page navigation. Configure scoped relay credentials so a network without a direct path can still connect. Show a timed recovery attempt and then a text fallback when media cannot recover. A data channel carries small ephemeral pointer hints with a queue cap and coalescing. Actual case notes use the authorized server API with revision and idempotency rules, so they survive peer closure. Keep media bytes, private case text, and raw network addresses out of routine signaling logs.', scope=['Deny a removed reviewer both subscription and a late candidate message.','Test a late answer from an older generation and a relay-only network.','Stop every local audio track after setup failure or explicit leave.','Throttle the data channel and keep durable notes in the server record.'], code='function admitRoomSignal(memberAllowed, activeGeneration, messageGeneration) {\n  return memberAllowed && activeGeneration === messageGeneration;\n}\nconsole.log(admitRoomSignal(false, 6, 6));\n// Output: false', cost='Signaling messages are small but candidate bursts and repeated retries need caps. Relay traffic costs bandwidth proportional to call duration and media rate, so measure relay share and capacity. Audio capture spends device power even if no peer connects; stop it promptly. Pointer hints can outnumber useful frames, so coalesce replaceable events and limit queued bytes. Measure setup time, leave-to-stop delay, restart success, and note-save conflicts without logging media or private annotations.', failure='Reject room ID guessing, a revoked reviewer, and generation 5 messages after generation 6 starts. Deny microphone permission and verify the text path still works. Block direct candidates and prove the relay path. Expire relay credentials and make recovery stop at its budget. Send 62 pointer hints into a slow connection and keep buffered bytes under the cap. Save a case note, close both tabs, and reload: the note must remain in the authorized server record.', checks=['Room membership is enforced on each signal.','Local tracks stop on every terminal path.','Relay failure has a bounded fallback.','Peer messages never substitute for durable case writes.'], mistakes=['Using a room ID as an access grant.','Calling offer-answer exchange a connected call.','Treating a queued hint as a saved case note.'], related=['web-tech/media-capture-consent-and-track-lifecycle','web-tech/webrtc-signaling-room-auth-and-offer-order','web-tech/webrtc-ice-turn-fallback-and-session-recovery','web-tech/data-channel-backpressure-and-peer-state']),
]

for number, project in enumerate(projects, 1):
    assert project['path'] not in by_path
    subprocess.run(['node','--check','--input-type=module'], input=project['code'], text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path['web-tech/case-save-incident-evidence-project'])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + project['path'])), path=project['path'], title=project['title'], summary=project['summary'], sort_order=1220 + number, created_at=stamp, updated_at=stamp, published_at=stamp)
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
    ('When should a rarely used binary analyzer load?', ['When the user starts that workflow, with a tested fallback', 'Before every visitor sees the home page', 'Only after it has already produced a result'], 'A lazy versioned artifact avoids charging unrelated visits and makes failure recovery explicit.'),
    ('What must happen after ordinary Wasm memory grows?', ['Acquire a fresh typed view before reading bytes', 'Keep every old view indefinitely', 'Assume pointers become permanent IDs'], 'An ordinary growth can replace the backing buffer, leaving old views detached.'),
    ('Why can Wasm lose to JavaScript on a small task?', ['Startup and boundary copies can outweigh inner-loop gains', 'JavaScript never supports typed arrays', 'Wasm cannot run in workers'], 'Compare the entire user task, including download, compilation, and data movement.'),
    ('How should a UI handle an old worker result?', ['Compare its job generation with the current selection', 'Always display the last result to arrive', 'Erase the current file before checking'], 'Cancellation may not interrupt a synchronous export; the UI must reject stale output.'),
    ('Does every Wasm deployment need cross-origin isolation?', ['No; shared-memory browser builds have extra requirements', 'Yes, even for a single-threaded module', 'No browser can use shared memory'], 'A regular single-threaded module can run without the isolation needed for shared-memory use.'),
    ('What does a module sandbox establish?', ['Limited host capabilities, not correctness or case authorization', 'Correct business output for any input', 'Permission to read any case'], 'The host chooses imports and still validates inputs, results, and access.'),
    ('What must be checked before a reviewer joins private call signaling?', ['Current room and case membership', 'Only possession of a guessed room number', 'Only microphone permission'], 'Device permission and application room authorization are separate decisions.'),
    ('What does an offer-answer exchange prove?', ['Descriptions were exchanged, not that media is flowing', 'A direct path always exists', 'Every participant remains authorized forever'], 'ICE still needs a viable network path, and room rights can change before media flows.'),
    ('Why might a TURN relay be needed?', ['A direct candidate path can fail on restrictive networks', 'It guarantees no bandwidth cost', 'It replaces all signaling authorization'], 'Relay capacity is an ordinary part of call reliability and must be budgeted.'),
    ('What should happen when the consultation ends?', ['Stop owned local tracks and close channel and connection', 'Hide the preview and leave capture active', 'Wait for a remote peer to release local hardware'], 'Capture lifetime must end locally even when signaling or remote state fails.'),
    ('How should a slow data channel affect pointer hints?', ['Cap buffered bytes and coalesce replaceable positions', 'Queue every movement without a limit', 'Treat a queued send as a saved note'], 'Ephemeral hints should not exhaust memory or pretend to be durable state.'),
    ('Where should a durable case note commit?', ['Through the authorized revisioned server write', 'Only inside the peer data channel', 'In an unaudited signaling log'], 'The authorized server remains the record of truth after either peer leaves or loses connectivity.'),
]
quiz_path = 'quizzes/web-development-browser-compute-peer-sessions'
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path['quizzes/web-development-operations-sync-decisions'])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + quiz_path)), path=quiz_path, title='Web Development: browser compute and peer sessions quiz', summary='Twelve explained decisions about module cost, memory, workers, room access, relay, capture, and peer state.', sort_order=1225, created_at=stamp, updated_at=stamp, published_at=stamp)
def quiz_item(number, value):
    prompt, options, explanation = value
    shift = number % 3
    return {'prompt':prompt,'options':options[shift:] + options[:shift], 'answer':(0 - shift) % 3, 'explanation':explanation}
quiz['data'] = {'subject_root':'web-tech/web-technology','section_path':'web-tech/quizzes','content_format':'html','seo_ready':False,'questions':[quiz_item(number, value) for number, value in enumerate(questions)]}
quiz['body'] = p(quiz['summary'] + ' Choose one answer, inspect its explanation, and return to the related decision boundary.')
quiz['body'] += '<h2>Related lessons</h2><p>' + '; '.join(link(path) for project in projects for path in project['related']) + '.</p>'
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path['web-tech/web-technology/project']
project_hub['data']['modules'][0]['lessons'].extend(project['path'] for project in projects)
project_hub['body'] += '<h2>Browser compute and peer projects</h2><ul>' + ''.join('<li>' + link(project['path']) + ' — ' + html.escape(project['summary']) + '</li>' for project in projects) + '</ul>'
project_hub['summary'] = 'Build and verify forty-one projects across browser, API, data, identity, search, rendering, operations, privacy, feature release, GraphQL, browser compute, and peer sessions.'
project_hub['updated_at'] = stamp
quiz_hub = by_path['web-tech/quizzes']
quiz_hub['data']['modules'][0]['lessons'].append(quiz_path)
quiz_hub['body'] += '<h2>Browser compute and peer checks</h2><p>' + link(quiz_path) + ' — ' + html.escape(quiz['summary']) + '</p>'
quiz_hub['updated_at'] = stamp
for hub_path, project_path in [('web-tech/webassembly-and-browser-compute', projects[0]['path']), ('web-tech/webrtc-and-peer-media-sessions', projects[1]['path'])]:
    hub = by_path[hub_path]
    hub['body'] += '<h2>Practice path</h2><p>Build ' + link(project_path) + ' and check decisions in ' + link(quiz_path) + '.</p>'
    hub['updated_at'] = stamp
for entry in entries:
    if entry['type'] != 'article' or entry['data'].get('section_path') not in {'web-tech/webassembly-and-browser-compute','web-tech/webrtc-and-peer-media-sessions'}:
        continue
    project_path = projects[0]['path'] if entry['data']['section_path'] == 'web-tech/webassembly-and-browser-compute' else projects[1]['path']
    entry['body'] += '<h2>Connected lessons</h2><p>Build ' + link(project_path) + ' and review ' + link(quiz_path) + '; follow ' + '; '.join(link(path) for path in entry['data']['related']) + '.</p>'
    entry['data']['related'].extend([project_path, quiz_path])
    entry['updated_at'] = stamp
root_entry = by_path['web-tech/web-technology']
root_entry['body'] += '<h2>Browser compute and peer practice</h2><p>Apply the two tracks with ' + link(projects[0]['path']) + ' and ' + link(projects[1]['path']) + '.</p>'
root_entry['updated_at'] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_projects':len(projects),'new_quizzes':1,'new_questions':len(questions)}))
