"""Add geospatial search project and decision quiz."""
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
    'web-tech/coordinate-validation-projection-and-antimeridian',
    'web-tech/map-viewport-tiles-and-request-lifecycle',
    'web-tech/nearby-spatial-search-and-tenant-filter',
    'web-tech/location-consent-precision-and-map-alternatives',
]
project_path = 'web-tech/authorized-facility-map-and-nearby-search-project'
quiz_path = 'quizzes/web-development-geospatial-decisions'
assert project_path not in by_path and quiz_path not in by_path
code = "function facilityQueryAllowed(query, reviewer) {\n  return reviewer.tenantId === query.tenantId && Number.isFinite(query.latitude) &&\n    Number.isFinite(query.longitude) && query.latitude >= -90 && query.latitude <= 90 &&\n    query.longitude >= -180 && query.longitude <= 180 &&\n    Number.isFinite(query.radiusMeters) && query.radiusMeters > 0 && query.radiusMeters <= 2900;\n}\nconsole.log(facilityQueryAllowed({ tenantId: 63, latitude: 13.036, longitude: 77.610, radiusMeters: 2900 }, { tenantId: 47 }));\n// Output: false"
subprocess.run(['node', '--check', '--input-type=module'], input=code, text=True, capture_output=True, check=True)
project = copy.deepcopy(by_path['web-tech/case-save-incident-evidence-project'])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + project_path)), path=project_path,
               title='Project: authorized facility map and nearby search',
               summary='Build a tenant-scoped facility map with correct coordinates, indexed radius search, and a complete text route.',
               sort_order=1321, created_at=stamp, updated_at=stamp, published_at=stamp)
project['data'] = {'subject_root': 'web-tech/web-technology', 'section_path': 'web-tech/web-technology/project',
                   'content_format': 'html', 'seo_ready': False, 'kind': 'project',
                   'author_path': 'authors/aitrove-editorial', 'reading_minutes': 8, 'related': lessons}
project['body'] = p('Build a facility search for municipal inspectors. Case 47 has a stored point at latitude 13.036 and longitude 77.610. The API names both coordinates, validates their ranges, and records the reference system. The browser uses a projected tiled map only for display; distance labels come from a meter-aware server query. A viewport crossing the antimeridian becomes two longitude intervals. Facility markers and the parallel result list come from one authorized query. The server applies tenant and record visibility while selecting candidates with an index-aware radius predicate, caps radius at 2,900 meters, caps results at 63, and uses a stable tie-breaker for pagination. The map requests only visible tiles plus a bounded neighbor area. Every response is tagged with viewport generation and style revision; old pan responses cannot repaint a newer view. Private overlay data never enters a public tile cache key. A reviewer can search by district or case ID and open a facility without device location, tiles, pointer dragging, or script. A clearly named button may request location to center the view, but poor accuracy never chooses a facility automatically. A continuous watch stops when the active field task ends. The result page reports the selection and count outside the map and offers keyboard zoom and list controls. The project documents coordinate retention, query limits, and the actual task outcome when a tile provider or location permission fails.')
project['body'] += '<h2>Build contract</h2><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in [
    'Coordinate order and units are explicit at the API and query boundaries.',
    'Late viewport responses cannot replace current tiles or markers.',
    'Nearby search is indexed, bounded, and tenant-scoped before result release.',
    'Text search and list selection complete the task without map or location.',
]) + '</ul>'
project['body'] += '<h2>Implementation checkpoint</h2><pre><code class="language-javascript">' + html.escape(code, quote=False) + '</code></pre>'
project['body'] += p('The checkpoint blocks a query when the requested tenant differs from the reviewer. In production, tenant identity comes from the authenticated server session and the geometry query includes record-level policy; a client field cannot choose the tenant. Basic validation is O(1). Spatial query cost depends on indexed candidates K rather than scanning all N stored facilities, but a broad or dense radius still needs a work limit. Tile traffic is O(V + P) for V visible and P prefetched tiles, with decoded-memory limits independent of compressed transfer size. Location watches and exact coordinate retention need their own lifecycle and privacy review.')
project['body'] += '<h2>Failure drill</h2>' + p('Swap coordinate fields, send a latitude of 96, and query a viewport from longitude 178 to -177. Reject malformed points and include both sides of the seam. Pan between three districts while throttled; old tile and facility responses must be ignored. Change style revision and inspect cache keys. Search from another tenant with the same center and require different authorized results. Ask for a huge radius, then simulate 83,000 dense points and inspect the query plan and latency. Tie two facilities on distance and page without duplicate rows. Deny device location, return a stale position, then return a 1,900-meter accuracy radius; none should block district search or auto-select a pump. Clear a location watch on route change. Disable tile loading and complete the facility-opening task through keyboard and list controls.')
project['body'] += '<h2>Acceptance checks</h2><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in [
    'Invalid coordinates and meter units cannot silently produce a plausible wrong map.',
    'A stale pan response never replaces the current view.',
    'Tenant filters bind nearby candidates, counts, and pagination.',
    'A location denial or tile outage leaves an accessible facility route.',
]) + '</ul>'
project['body'] += '<h3>Common Mistakes</h3><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in [
    'Interpreting degrees or map pixels as meters.',
    'Filtering tenant only after a broad database scan.',
    'Treating an imprecise device point as proof of facility presence.',
]) + '</ul>'
project['body'] += '<h2>Related lessons</h2><p>' + '; '.join(link(path) for path in lessons) + '.</p>'
entries.append(project)
by_path[project_path] = project

questions = [
    ('Why name latitude and longitude in an API payload?', ['To avoid silent coordinate-order swaps', 'To remove server validation', 'To guarantee meter distance'], 'Both values can be numerically plausible when swapped. Named fields and a declared reference system make the contract testable.'),
    ('What does a viewport crossing the antimeridian require?', ['Two longitude intervals or equivalent seam-aware logic', 'Sorting west and east into one ordinary interval', 'Dropping points near longitude 180'], 'A west bound above the east bound can mean the viewport crosses the globe seam rather than having invalid coordinates.'),
    ('Can projected pixel distance be used as ground meters?', ['Not without a defined geographic conversion', 'Always, at every latitude', 'Only after rounding to whole pixels'], 'Projection scale varies by place. The server should use a unit-aware geographic distance operation for nearby results.'),
    ('What should happen to a tile response from an old pan?', ['Discard it when its generation does not match the current viewport', 'Paint it over new markers', 'Change the map back to the old viewport'], 'Network completion order is not user intent. The current viewport identity decides which tiles and markers belong on screen.'),
    ('What belongs in a tile cache key after a style change?', ['The style or data revision along with tile coordinates', 'Only the facility count', 'Only the browser tab ID'], 'Reusing a coordinate-only key after a style or dataset change can display stale tiles over a new result set.'),
    ('What is the fallback when tile requests fail?', ['An authorized facility list with equivalent open actions', 'A permanently empty page', 'A requirement to grant precise location'], 'The map is one view over the results. The task should remain available through text and keyboard controls.'),
    ('Where does tenant filtering belong in nearby search?', ['Inside candidate selection and the server permission path', 'Only after all facilities are sent to the browser', 'Only in a map marker style'], 'A broad scan or response can expose private points and counts. Tenant scope must bind the query and result release.'),
    ('Why cap a nearby radius?', ['A very broad circle can force large scans and result sorts', 'Because all maps have one fixed scale', 'To bypass authorization checks'], 'An indexed predicate reduces work, but a huge or dense search can still produce many candidates and expensive ordering.'),
    ('How can equal-distance results page consistently?', ['Use a stable secondary key after distance', 'Shuffle ties on each request', 'Rely on the map pin order'], 'Two rows can share a distance. A deterministic tie-breaker keeps cursors from duplicating or skipping them.'),
    ('When should a page request device location?', ['After a clear user action for a nearby task', 'On every page load', 'Whenever map tiles finish loading'], 'Location is optional and sensitive. District search should remain available without the browser permission prompt.'),
    ('What does a 1,900-meter accuracy radius mean for a pump 47 meters away?', ['Do not auto-select; show candidates for user choice', 'The device proves the user is at that pump', 'Round accuracy down to 47 meters'], 'An uncertain position cannot establish which nearby facility the reviewer intends to inspect.'),
    ('What happens to a continuous location watch after the task?', ['Clear it and stop unnecessary queries', 'Keep it running across sign-out', 'Store every exact coordinate forever'], 'A watch consumes resources and may expose movement. Its lifetime should follow the active user task and retention policy.'),
]
quiz = copy.deepcopy(by_path['quizzes/web-development-graphics-editor-decisions'])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + quiz_path)), path=quiz_path,
            title='Web Development: geospatial decisions quiz',
            summary='Twelve explained decisions about coordinates, map tiles, nearby search, tenant filters, and location alternatives.',
            sort_order=1322, created_at=stamp, updated_at=stamp, published_at=stamp)
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
project_hub['body'] += '<h2>Geospatial search project</h2><p>' + link(project_path) + ' — ' + html.escape(project['summary']) + '</p>'
project_hub['summary'] = 'Build and verify fifty-seven projects across browser, API, data, identity, media, extensions, and geospatial workflows.'
project_hub['updated_at'] = stamp
quiz_hub = by_path['web-tech/quizzes']
quiz_hub['data']['modules'][0]['lessons'].append(quiz_path)
quiz_hub['body'] += '<h2>Geospatial checks</h2><p>' + link(quiz_path) + ' — ' + html.escape(quiz['summary']) + '</p>'
quiz_hub['updated_at'] = stamp
hub = by_path['web-tech/geospatial-web-interfaces-and-spatial-queries']
hub['body'] += '<h2>Practice path</h2><p>Build ' + link(project_path) + ' and check decisions in ' + link(quiz_path) + '.</p>'
hub['updated_at'] = stamp
for lesson_path in lessons:
    lesson = by_path[lesson_path]
    lesson['body'] += '<h2>Connected practice</h2><p>Build ' + link(project_path) + ' and review ' + link(quiz_path) + '.</p>'
    lesson['data']['related'].extend([project_path, quiz_path])
    lesson['updated_at'] = stamp
root_entry = by_path['web-tech/web-technology']
root_entry['body'] += '<h2>Geospatial practice</h2><p>Apply this track with ' + link(project_path) + '.</p>'
root_entry['updated_at'] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_projects': 1, 'new_quizzes': 1, 'new_questions': len(questions)}))
