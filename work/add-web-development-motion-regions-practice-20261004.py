"""Add linked motion and multi-region practice drafts."""
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
    dict(path='web-tech/case-board-motion-and-route-project', title='Project: case board motion and route continuity', summary='Move cards and open details without making animation own state, focus, or history.', intro='Build a case-review board with queue columns, a detail route, and an activity panel. Assignment changes use a revisioned server response; the DOM and accessible column name update from that result. A short effect may illustrate the move, but cancelling it cannot undo the assignment or leave the card in an old column. Own at most one scripted animation handle per case, cancel stale handles on a newer revision, and release them when the board unmounts. The detail route may use a view transition when available, but URL, heading, focus, scroll, and back navigation must work with the effect skipped. Use a reduced-motion path that changes state immediately and announces the outcome in text. A bulk reassignment of 62 cases should not launch 62 expensive effects; summarize the change and measure frame time on a dense board. Keep the visual state accurate when a save fails, a route fetch returns late, or a user opens another case before the first effect completes.', scope=['Close a panel before its entrance ends and preserve correct hidden and focus state.','Cancel a stale card animation after a newer revision and release its handle on unmount.','Open a case route with and without view-transition support, preserving history and focus.','Compare dense-board frame time with a reduced-motion bulk update.'], code='function cardMotionAllowed(reducedMotion, changedCards, maximumActive) {\n  return !reducedMotion && changedCards <= maximumActive;\n}\nconsole.log(cardMotionAllowed(false, 62, 12));\n// Output: false', cost='Motion code may be constant-time for one card while painting, snapshot memory, and layer count grow with affected surfaces. Measuring layout during each frame can block input. Keep simultaneous effects bounded and compare the full board on target devices. A plain route path saves animation work but still requires focus and scroll decisions. Track active handles, skipped effects, dropped frames, and time until the new detail is operable.', failure='Disable animation and check that panel state and focus still change. Rapidly open and close the activity panel, then open case 47 while case 62 loads slowly. Deliver case 62 last and prove it cannot replace the newest route. Give two visible cards the same transition name and verify fallback. Cancel a card handle during unmount, then confirm no stale completion callback changes the new board. Deny a save and announce the rollback without relying on movement alone.', checks=['Semantic state reaches its final value without motion.','Latest revision and destination win interrupted work.','Keyboard focus and back navigation survive skipped effects.','The dense-board rendering budget is measured.'], mistakes=['Using an animation finish event to commit a route.','Leaving obsolete handles attached to removed cards.','Removing the only state cue when reduced motion is active.'], related=['web-tech/css-motion-state-and-interruption','web-tech/web-animations-lifecycle-and-cancellation','web-tech/view-transition-navigation-focus-and-fallback','web-tech/reduced-motion-and-rendering-budget']),
    dict(path='web-tech/two-region-case-service-recovery-project', title='Project: two-region case service recovery', summary='Design regional read freshness, single-writer failover, private cache scope, and placement evidence.', intro='Design a case-review service with readers in regions 29 and 47 and one authoritative write region. Public hashed assets can be served near users, but a private case response must remain bound to authenticated tenant rights and never be shared by URL alone. A save returns a revision token. If a nearby replica is behind that revision, the next read waits within a bound, routes to the writer, or reports a pending state; it must not silently replace the editor with stale data. A recovery drill promotes a second region only after old writers are fenced and possible unreplicated writes are recorded. Browser retries reuse idempotency keys, while queued email and export work resume from durable intents after reconciliation. Map where scans, derivatives, caches, logs, backups, and support exports reside. Tenant placement policy applies to the recovery destination as well as normal requests. The project is an architecture and failure test; service guarantees must be checked against the selected database and network provider.', scope=['Warm a cache as one tenant and verify a second tenant cannot read the response.','Save revision 47 while a replica remains at 46 and exercise the freshness fallback.','Promote generation 7 while rejecting generation 6 writers and reconciling retries.','Inventory private data, derived files, telemetry, backups, and allowed recovery regions.'], code='function readFromReplica(appliedRevision, requiredRevision, regionAllowed) {\n  return regionAllowed && appliedRevision >= requiredRevision;\n}\nconsole.log(readFromReplica(46, 47, true));\n// Output: false', cost='Public caching can reduce asset latency; private freshness checks may add a cross-region hop or bounded wait. A passive second region consumes storage and drill effort; an active one adds compute and harder coordination. Asynchronous replication creates a possible loss window at failover, so record lag and accepted write generations. A regional placement rule can lower cache efficiency and restrict recovery choices. Measure user-visible stale reads, fallback-to-writer share, promotion time, replay count, and unclassified private data flows.', failure='Try a private URL warmed under another tenant, then shift edge traffic and repeat. Stop replication at revision 46 after the writer acknowledges 47; verify the client does not show 46 as final. Leave an old batch worker alive after promotion and assert its writes fail. Replay a timed-out save using the original key and inspect the outbox before sending email again. Attempt recovery into a region disallowed for the tenant and inspect logs and temporary exports for stray private content.', checks=['Private responses never cross permission scope.','Post-save reads meet a named freshness contract.','One writer generation owns mutations after failover.','Placement inventory covers derivatives and recovery copies.'], mistakes=['Treating nearest edge as the database authority.','Using a traffic switch as the only writer fence.','Assuming one regional database setting covers logs and backups.'], related=['web-tech/regional-routing-static-and-private-cache-boundaries','web-tech/replica-lag-read-your-write-and-version-cursors','web-tech/regional-failover-fencing-and-replay','web-tech/regional-data-location-and-operational-evidence']),
]

for number, project in enumerate(projects, 1):
    assert project['path'] not in by_path
    subprocess.run(['node','--check','--input-type=module'], input=project['code'], text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path['web-tech/case-save-incident-evidence-project'])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + project['path'])), path=project['path'], title=project['title'], summary=project['summary'], sort_order=1230 + number, created_at=stamp, updated_at=stamp, published_at=stamp)
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
    ('What owns whether a case panel is open?', ['Application and semantic DOM state', 'A transitionend event alone', 'The opacity value at one frame'], 'The visual transition follows committed state. Skipped or interrupted motion must leave the panel operable.'),
    ('When should an older card animation be cancelled?', ['When a newer revision supersedes its target', 'Only after the tab closes', 'Never, because effects cannot overlap'], 'A stale handle or completion callback must not apply visual state after a newer assignment arrives.'),
    ('What should a skipped view transition skip?', ['Only the animation, not the route or DOM update', 'The URL and history change', 'All focus and content updates'], 'Navigation data, URL, heading, and focus must work even when the visual effect is unsupported or skipped.'),
    ('How should a reduced-motion board show reassignment?', ['Update the column and provide a clear status cue without travel', 'Hide the change until a hover', 'Remove the status text with the animation'], 'The user still needs to know where the card moved and whether the server accepted the change.'),
    ('Why profile a dense board instead of one moving card?', ['Rendering cost grows with affected surfaces and active layers', 'Every transform always causes layout', 'One card proves all devices will meet budget'], 'A single-card microbenchmark cannot price a bulk update or a low-memory tablet.'),
    ('What is a safe role for a visual finish callback?', ['Optional cleanup guarded by current state', 'The only place to commit a write', 'A replacement for router history'], 'A cancelled or skipped effect may not finish normally, so core state cannot depend on its completion.'),
    ('Which response can be broadly shared at an edge?', ['A public immutable asset with a suitable cache key', 'A private case detail keyed only by URL', 'A tenant export archive'], 'Public artifacts and authenticated records have different cache ownership and access rules.'),
    ('What should a reader do after saving revision 47 if its replica has 46?', ['Use the defined freshness fallback or report pending', 'Silently render 46 as current', 'Reset the client minimum version to 46'], 'A recent write needs a read path that does not silently erase the user’s committed revision.'),
    ('Why is a traffic shift insufficient for failover?', ['Old workers may still write without fencing', 'DNS is a database transaction', 'Traffic routing always synchronizes replicas'], 'Write authority must be transferred explicitly, including workers that do not follow browser traffic.'),
    ('What can asynchronous replication leave behind at promotion?', ['Acknowledged writes not yet present in the recovery copy', 'A guarantee of zero recovery-point loss', 'No need for replay identity'], 'A promotion drill must record lag and reconcile uncertain writes against durable identities.'),
    ('Where can private data escape a regional database setting?', ['Caches, derivatives, logs, exports, and backups', 'Only a CSS bundle', 'Nowhere once the database is configured'], 'A location decision applies to the full private-data lifecycle, not one storage service.'),
    ('What must a recovery destination satisfy for a restricted tenant?', ['The tenant’s permitted placement policy', 'Only a low network latency', 'Only a warm public asset cache'], 'Failover routing must preserve the same data-location decision used during ordinary operation.'),
]
quiz_path = 'quizzes/web-development-motion-region-decisions'
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path['quizzes/web-development-operations-sync-decisions'])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + quiz_path)), path=quiz_path, title='Web Development: motion and regional state decisions quiz', summary='Twelve explained decisions about animation state, navigation fallback, private caching, replica freshness, and failover.', sort_order=1235, created_at=stamp, updated_at=stamp, published_at=stamp)
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
project_hub['body'] += '<h2>Motion and regional recovery projects</h2><ul>' + ''.join('<li>' + link(project['path']) + ' — ' + html.escape(project['summary']) + '</li>' for project in projects) + '</ul>'
project_hub['summary'] = 'Build and verify forty-three projects across browser, API, data, identity, search, rendering, operations, privacy, feature release, GraphQL, browser compute, peer sessions, motion, and regional recovery.'
project_hub['updated_at'] = stamp
quiz_hub = by_path['web-tech/quizzes']
quiz_hub['data']['modules'][0]['lessons'].append(quiz_path)
quiz_hub['body'] += '<h2>Motion and regional recovery checks</h2><p>' + link(quiz_path) + ' — ' + html.escape(quiz['summary']) + '</p>'
quiz_hub['updated_at'] = stamp
for hub_path, project_path in [('web-tech/motion-and-view-change-contracts', projects[0]['path']), ('web-tech/multi-region-web-state-and-recovery', projects[1]['path'])]:
    hub = by_path[hub_path]
    hub['body'] += '<h2>Practice path</h2><p>Build ' + link(project_path) + ' and check decisions in ' + link(quiz_path) + '.</p>'
    hub['updated_at'] = stamp
for entry in entries:
    if entry['type'] != 'article' or entry['data'].get('section_path') not in {'web-tech/motion-and-view-change-contracts','web-tech/multi-region-web-state-and-recovery'}:
        continue
    project_path = projects[0]['path'] if entry['data']['section_path'] == 'web-tech/motion-and-view-change-contracts' else projects[1]['path']
    entry['body'] += '<h2>Connected lessons</h2><p>Build ' + link(project_path) + ' and review ' + link(quiz_path) + '; follow ' + '; '.join(link(path) for path in entry['data']['related']) + '.</p>'
    entry['data']['related'].extend([project_path, quiz_path])
    entry['updated_at'] = stamp
root_entry = by_path['web-tech/web-technology']
root_entry['body'] += '<h2>Motion and regional recovery practice</h2><p>Apply the tracks with ' + link(projects[0]['path']) + ' and ' + link(projects[1]['path']) + '.</p>'
root_entry['updated_at'] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_projects':len(projects),'new_quizzes':1,'new_questions':len(questions)}))
