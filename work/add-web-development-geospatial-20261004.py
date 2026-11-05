"""Add original geospatial interface lessons to Web Development."""
import copy
import datetime
import html
import json
import re
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

hub_path = 'web-tech/geospatial-web-interfaces-and-spatial-queries'
hub_title = 'Geospatial Web Interfaces and Spatial Queries'
topics = [
    {
        'slug': 'coordinate-validation-projection-and-antimeridian',
        'title': 'Coordinate Validation, Projection, and the Antimeridian',
        'summary': 'Keep latitude, longitude, map projection, and geographic distance in their own units.',
        'concept': 'A geographic point needs an explicit coordinate order and reference system. Latitude is bounded by the poles; longitude wraps around the globe. A screen map applies a projection, so equal pixel gaps are not equal ground distances everywhere. Coordinates in degrees must not be passed to a distance function that expects meters without a defined conversion or geographic type. A rectangular viewport crossing the antimeridian is two longitude intervals rather than one ordinary increasing interval. Server and browser must agree about these representations before filtering records or placing markers.',
        'case': 'A facilities team stores a pump inspection at latitude 13.036 and longitude 77.610. A client sends [longitude, latitude], but an API decoder reads [latitude, longitude]; the point appears thousands of kilometers away while both numbers still fit plausible numeric ranges. Another facility near longitude 179.7 appears to vanish when the map pans across the antimeridian because the query assumes west is always less than east. The revised contract uses named latitude and longitude fields, validates ranges, records the coordinate reference system, and splits a crossing viewport into two longitude predicates. The map label reports approximate distance rather than pretending a projected pixel measurement is a survey result.',
        'implementation': 'Use named fields at application boundaries and one documented point order inside geometry libraries. Reject nonfinite values, latitudes outside -90 through 90, and longitudes outside -180 through 180. Decide whether longitude 180 and -180 are normalized to one identity before deduplicating. Carry the geometry reference system with stored values and transform explicitly for rendering. When filtering a viewport, split an antimeridian crossing into west-to-180 and -180-to-east; do not swap endpoints to make the numbers increasing. Use geodesic or geography-aware distance for meter-based nearby results and state the measurement approximation. Check that a point is authorized before returning it, since a valid coordinate is still private case data. Avoid printing exact coordinates in public error messages.',
        'cost': 'Validation is O(1) per point and O(N) for N imported points. A coordinate transform is O(N) before indexing, so precompute or index the stored form used by common queries where appropriate. A naive scan of all facilities for each viewport is O(N) per pan and becomes expensive as the catalog grows. Indexed bounding filters reduce candidates but may need exact post-filtering, especially near a seam or projection edge. Precision increases storage and privacy exposure without always improving the task. Measure rejected coordinates, transformed records, query candidates, out-of-viewport markers, and distance disagreement in representative regions.',
        'failure': 'Swap latitude and longitude for a point where both values fit legal ranges and verify a contract test catches the order mismatch. Send NaN, infinity, and a latitude of 96; reject before storage. Query a viewport from longitude 178 to -177 and confirm facilities on both sides of the seam appear. Compare a distance label at two latitudes for the same projected pixel gap and avoid using pixels as meters. Import a geometry with an unexpected reference system and require explicit transformation. Ask for a private facility point as another tenant and deny it even though its coordinates are otherwise valid.',
        'drill': 'Define a point payload for pump 47 with latitude 13.036, longitude 77.610, and a declared geographic reference system. Import 63 valid and 7 malformed records. Query a viewport that crosses the antimeridian and count records on each side. Compute a nearby label through a meter-aware service rather than screen pixels. Pan the map while a stale viewport request remains in flight; discard its markers after the new viewport identity wins.',
        'decision': 'Coordinates are data with units and order; a map projection is only one display of that data.',
        'code': "function validFacilityPoint(point) {\n  return Number.isFinite(point.latitude) && Number.isFinite(point.longitude) &&\n    point.latitude >= -90 && point.latitude <= 90 &&\n    point.longitude >= -180 && point.longitude <= 180;\n}\nconsole.log(validFacilityPoint({ latitude: 96, longitude: 77.610 }));\n// Output: false",
        'checks': ['Coordinate order is named and contract-tested.', 'A crossing viewport includes both sides of the seam.', 'Distance units are explicit and not inferred from pixels.'],
        'mistakes': ['Treating longitude and latitude as interchangeable tuple positions.', 'Using degree differences as meters.', 'Sorting antimeridian bounds into one ordinary interval.'],
        'related': ['web-tech/geolocation-accuracy-cancellation-and-retention', 'web-tech/typed-frontend-and-component-platform'],
    },
    {
        'slug': 'map-viewport-tiles-and-request-lifecycle',
        'title': 'Map Viewport Tiles and Request Lifecycle',
        'summary': 'Load only visible map work and stop stale requests when the viewport changes.',
        'concept': 'A tiled map covers a viewport with small image or vector regions at a chosen zoom. The tile identity contains a zoom level and grid coordinates; a style revision and data revision may also be needed in the cache key. Panning or zooming starts new requests while older ones are still in flight. The client must avoid presenting old tiles or markers as current results, and it must bound prefetch and memory. A map is a view over facilities, not the only route to the facility list or task controls.',
        'case': 'An inspector pans from district 47 to district 63 on a slow connection. Twenty tile requests from the first district finish after the second is visible, and an old facility query paints markers over the new area. The map client tags each viewport request with a sequence and cancels or ignores earlier work. It retains a modest tile cache for recent pans but does not prefetch an entire state at high zoom. When the tile service fails, the case list still names facilities and lets the inspector open each record. The interface offers zoom controls reachable from a keyboard and keeps selected facility state in a stable URL.',
        'implementation': 'Calculate visible tile IDs from viewport bounds and zoom under the chosen tiling scheme. Clamp supported zoom and latitude to the projection’s valid region; do not issue invalid tile coordinates. Deduplicate requests shared across adjacent views. Attach a viewport generation to both tile and facility-query responses, and render only data matching the latest generation. Abort work that no longer has consumers where the transport permits it. Bound speculative neighbor tiles, outstanding requests, and decoded tile memory. Cache keys include style and dataset revision so a changed road label or private overlay does not reuse stale content. Treat a private facility overlay differently from public base tiles: every marker query needs tenant scope and record authorization. Provide a list view using the same filtered result set.',
        'cost': 'For V visible tiles and P prefetched neighbors, network request count is O(V + P); decoded image memory grows with retained tile pixels, not just compressed transfer bytes. A small LRU cache saves nearby pans but competes with the rest of the page for memory. Vector styling can move work from the server to client CPU; raster tiles move more rendering work upstream. An unbounded marker query can return O(N) facilities for N stored points, so cap results and use viewport filtering. Measure tile request count per pan, canceled requests, cache hit rate, decoded memory, marker freshness, and task completion when the tile layer fails.',
        'failure': 'Pan rapidly between three districts under network throttling. Old tile and marker responses must not repaint a new viewport. Zoom beyond the supported level and require a bounded fallback. Change map style revision and verify stale styled tiles are not reused. Block the tile service entirely and finish a facility search through the list. Return thousands of private markers and enforce a result cap with a visible count or refinement path. Turn off script and verify the page still has a route to the case list. Test zoom and selection with keyboard focus, screen magnification, and reduced bandwidth.',
        'drill': 'Render a case map at zoom 12 with a cache budget of 47 tiles and a maximum of 8 simultaneous requests. Pan from district 47 to 63 before any first-view request completes. Tag each response with its viewport generation and count discarded stale results. Switch style revision 29 to 30 and inspect cache keys. Deny tile network access, then select a facility from the list and open its case route. Record bytes and decoded-memory estimates for the pan sequence.',
        'decision': 'Viewport identity owns what appears on the map; old network success is not permission to repaint a new view.',
        'code': "function belongsToViewport(response, current) {\n  return response.generation === current.generation &&\n    response.styleRevision === current.styleRevision;\n}\nconsole.log(belongsToViewport({ generation: 47, styleRevision: 29 }, { generation: 63, styleRevision: 29 }));\n// Output: false",
        'checks': ['Late responses cannot repaint a newer viewport.', 'Tile cache keys change with style or data revision.', 'The facility list still works when tiles fail.'],
        'mistakes': ['Prefetching an unbounded area at high zoom.', 'Reusing private overlay data across tenants.', 'Treating a successful stale request as current UI state.'],
        'related': ['web-tech/search-query-normalization-and-ranking', 'web-tech/navigation-history-and-page-lifecycle'],
    },
    {
        'slug': 'nearby-spatial-search-and-tenant-filter',
        'title': 'Nearby Spatial Search and Tenant Filter',
        'summary': 'Use indexed candidate selection, exact distance checks, and authorization in one query contract.',
        'concept': 'A nearby search combines a point, radius, and visibility rule. The radius has units; the stored geometry has a reference system; the results belong to a tenant and a permission scope. An index can narrow candidate facilities before an exact distance check. Calculating distance for every row and sorting the entire table is wasteful at scale. The server must cap radius, result count, and query time. A map viewport can suggest the search center but cannot decide which private facilities the caller may see.',
        'case': 'A district reviewer searches for pumps within 2,900 meters of an inspection site. The table contains 830,000 facility points across several tenants. A naive query computes distance for every row, then filters tenant after the fact, consuming CPU and risking leakage through counts. The revised endpoint authenticates the reviewer, applies tenant and record visibility inside the candidate query, uses a spatial index-aware radius predicate, orders only the bounded candidate set, and returns a stable cursor. The response carries an approximate distance and a documented unit. A client request for a 900-kilometer radius is rejected before database work.',
        'implementation': 'Validate finite center coordinates and radius before constructing SQL. Define the geographic type and meter semantics at the database boundary; do not compare an angular degree difference with a meter radius. Put tenant and authorization predicates in the query that selects candidates, not only in application code after rows have been fetched. Use an index-aware radius predicate and inspect the actual query plan for representative data. Cap radius and returned rows; if a user needs a region-wide view, use a different aggregated endpoint. Stable ordering needs a secondary key after distance so pagination does not duplicate equal-distance facilities. A changing facility set can still shift pages, so document snapshot or cursor behavior. Return only fields needed for map and list, keeping private coordinates out of unrelated telemetry.',
        'cost': 'Without an index, a radius filter is O(N) distance evaluations for N facilities. With a useful spatial and tenant strategy, the database narrows candidates, then pays O(K) or O(K log K) work for K matches depending on ordering and limit. Performance depends on density, radius, index selectivity, and permission joins; a theoretical index does not guarantee a fast plan. Exact distance sorting over a huge radius may still be costly. Measure candidates visited, rows returned, p95 latency, CPU, tenant predicate selectivity, and denied oversized radii. Cache only with tenant, permission, center precision, radius, and data revision considered.',
        'failure': 'Send a radius expressed in kilometers where the endpoint expects meters and require schema rejection or explicit conversion. Request an infinite or negative radius. Search near a tenant boundary and verify no other tenant’s point, count, or timing-derived list detail is disclosed. Add many dense facilities at the same distance and page through results without duplicates. Remove the spatial index in a staging database and compare plans and latency. Revoke a reviewer while their next-page cursor is waiting and deny the continuation. Ask for a huge radius and confirm it is blocked before an expensive scan.',
        'drill': 'Store 83,000 synthetic facilities across three tenants. Query a 2,900-meter circle centered on case 47 and cap results at 63. Compare a full distance scan to an index-aware candidate predicate using the database plan and measured latency. Add two facilities tied on distance and verify stable cursor order. Switch tenant between pages and reject the old cursor. Report exact returned count, candidate count, query time, and whether any private location entered routine logs.',
        'decision': 'The nearby endpoint owns units, work limits, and permission; the map supplies only a requested view.',
        'code': "function validNearbyRequest(query) {\n  return Number.isFinite(query.latitude) && Number.isFinite(query.longitude) &&\n    query.latitude >= -90 && query.latitude <= 90 &&\n    query.longitude >= -180 && query.longitude <= 180 &&\n    Number.isFinite(query.radiusMeters) && query.radiusMeters > 0 && query.radiusMeters <= 2900;\n}\nconsole.log(validNearbyRequest({ latitude: 13.036, longitude: 77.610, radiusMeters: 900000 }));\n// Output: false",
        'checks': ['Radius units and input bounds are enforced.', 'Tenant scope enters the candidate query.', 'Pagination remains stable for tied distances.'],
        'mistakes': ['Calculating distance over every table row.', 'Filtering tenant after fetching candidates.', 'Caching private results by center alone.'],
        'related': ['web-tech/data-persistence', 'web-tech/authorization-and-tenant-boundaries'],
    },
    {
        'slug': 'location-consent-precision-and-map-alternatives',
        'title': 'Location Consent, Precision, and Map Alternatives',
        'summary': 'Ask for device location only when useful and keep a keyboard-ready list route.',
        'concept': 'Device location is an optional input with uncertain accuracy and a privacy cost. A browser may deny the request, return a cached position, time out, or provide a point too imprecise for the intended action. A map can show a neighborhood while the application still needs an exact facility selected by ID. Location permission must follow a clear user action, and a continuous watch must stop when its task ends. A text search and ordered facility list give people a route through the same workflow without granting location or using pointer gestures.',
        'case': 'A reviewer wants the nearest pump inspection while standing at station 47. The site asks for high-accuracy location on first load and silently stores every update. A reviewer on a shared tablet declines, and the page leaves only an empty map. The revised page begins with a district search and list of authorized facilities. A button requests location to suggest a starting area, explaining that accuracy may vary. If the reported accuracy radius is 1,900 meters, it does not auto-select a pump 47 meters away; it shows candidate facilities and asks the reviewer to choose by name and case ID. The location watch ends when the page closes or the reviewer stops using it.',
        'implementation': 'Do not request location until the user chooses a nearby task. Bound timeout and maximum accepted age. Inspect the returned accuracy value and show uncertainty in the interface; it is not proof that a named facility was visited. Store only the precision and duration needed for the product task, or avoid storage when the position only centers a map. Stop active watchers on route change, sign-out, and explicit stop. If permission is denied or unavailable, retain district search, address entry, and the authorized list. Give map pins meaningful labels and keep equivalent actions in list rows with keyboard focus and visible state. A result count and selected facility name belong outside the map canvas, where assistive technology can read them. Avoid autoplay-like repeated prompts after denial.',
        'cost': 'A single location request costs device power and latency; high-accuracy continuous watching can cost much more over time. A location update that triggers a nearby query every second also costs network and database work, so debounce by time and meaningful movement. A list with N authorized results costs O(N) to render unless paginated or virtualized with an accessible strategy. The privacy cost of retaining exact coordinates grows with time and population even when byte storage is small. Measure permission denial, fallback completion, accuracy bands, watcher lifetime, query count per session, and keyboard/list completion. Do not use raw path histories as a routine success metric.',
        'failure': 'Deny location and complete the same facility-opening task with district search. Return a stale cached position, a timeout, and a 1,900-meter accuracy radius; none should silently select one pump. Start a watch, change routes, and verify it is cleared. Keep the browser page open but backgrounded and inspect unnecessary updates and queries. Use keyboard only to select a facility from the list and return from its detail page. Turn off tiles and complete through text. Revoke case permission between map render and list selection, then deny the record open. Inspect logs and storage for exact coordinates after the stated retention window.',
        'drill': 'Implement a nearby suggestion for case 47 with an optional location button. Use a 5-second timeout, a 60-second maximum cached age, and a 1,900-meter accuracy test that requires manual facility selection. Simulate denial, timeout, low accuracy, and a valid point. In each case, open an authorized facility from a keyboard-ready list. Start a watch for an active field session, then end the session and count remaining callbacks and server searches. Document what location data, if any, is retained.',
        'decision': 'Location may narrow a search; the user and server still decide which facility record may be opened.',
        'code': "function maySuggestExactFacility(position, facility) {\n  return position.accuracyMeters <= 47 && facility.distanceMeters <= 47 &&\n    facility.authorized;\n}\nconsole.log(maySuggestExactFacility({ accuracyMeters: 1900 }, { distanceMeters: 47, authorized: true }));\n// Output: false",
        'checks': ['Location denial leaves a complete text workflow.', 'Low accuracy cannot auto-select a facility.', 'Active watches stop when the task ends.'],
        'mistakes': ['Requesting precise location on initial page load.', 'Treating a position estimate as proof of site presence.', 'Making map pins the only action controls.'],
        'related': ['web-tech/geolocation-accuracy-cancellation-and-retention', 'web-tech/accessible-inspection-map-export-project'],
    },
]

assert hub_path not in by_path and len(topics) == 4
hub = copy.deepcopy(by_path['web-tech/production-signals-and-incident-decisions'])
hub.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + hub_path)), path=hub_path,
           title=hub_title, summary='Handle coordinate units, viewport tiles, indexed nearby search, and location alternatives in web maps.',
           sort_order=3100, created_at=stamp, updated_at=stamp, published_at=stamp)
hub['data'] = {'subject_root': 'web-tech/web-technology', 'section_path': hub_path,
               'content_format': 'html', 'seo_ready': False, 'modules': [],
               'resource_tabs': [{'title': 'Web Development', 'path': 'web-tech/web-technology'},
                                 {'title': 'Projects', 'path': 'web-tech/web-technology/project'},
                                 {'title': 'Quizzes', 'path': 'web-tech/quizzes'}]}
entries.append(hub)
by_path[hub_path] = hub
for number, topic in enumerate(topics):
    path = 'web-tech/' + topic['slug']
    assert path not in by_path
    subprocess.run(['node', '--check', '--input-type=module'], input=topic['code'], text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path['web-tech/trace-context-across-request-and-job'])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + path)), path=path,
                 title=topic['title'], summary=topic['summary'], sort_order=3101 + number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    related = [hub_path] + ['web-tech/' + item['slug'] for item in topics if item is not topic] + topic['related']
    body = p(topic['concept']) + '<h2>Working case</h2>' + p(topic['case'])
    body += '<h2>Implementation boundary</h2><pre><code class="language-javascript">' + html.escape(topic['code'], quote=False) + '</code></pre>' + p(topic['implementation'])
    body += '<h2>Cost and boundaries</h2>' + p(topic['cost']) + '<h2>Failure trace</h2>' + p(topic['failure'])
    body += '<h2>Verification</h2><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in topic['checks']) + '</ul>'
    body += '<h2>Practice drill</h2>' + p(topic['drill']) + '<h2>Decision note</h2>' + p(topic['decision'])
    body += '<h3>Common Mistakes</h3><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in topic['mistakes']) + '</ul>'
    entry['body'] = body
    entry['data'] = {'subject_root': 'web-tech/web-technology', 'section_path': hub_path,
                     'content_format': 'html', 'seo_ready': False, 'kind': 'tutorial',
                     'author_path': 'authors/aitrove-editorial', 'reading_minutes': 8, 'related': related}
    entries.append(entry)
    by_path[path] = entry
for topic in topics:
    entry = by_path['web-tech/' + topic['slug']]
    entry['body'] += '<h2>Related lessons</h2><p>' + '; '.join(link(target) for target in entry['data']['related']) + '.</p>'
hub['data']['modules'] = [{'title': hub_title, 'summary': hub['summary'],
                           'lessons': ['web-tech/' + topic['slug'] for topic in topics]}]
hub['body'] = p('A web map is a view over coordinate, query, permission, and interaction contracts. This track follows facility inspections through point validation, tiled viewport changes, nearby search, and optional device location. It preserves a text list when location is denied or tiles fail, and it keeps the server responsible for private facility scope.')
hub['body'] += '<h2>Topics in this track</h2><ul>' + ''.join('<li>' + link('web-tech/' + topic['slug']) + ' — ' + html.escape(topic['summary']) + '</li>' for topic in topics) + '</ul>'
hub['body'] += '<h2>Prerequisite paths</h2><p>' + '; '.join(link(path) for path in ['web-tech/geolocation-accuracy-cancellation-and-retention', 'web-tech/application-search-and-retrieval', 'web-tech/inclusive-interface-engineering']) + '.</p>'
root_entry = by_path['web-tech/web-technology']
root_entry['data']['modules'].append({'title': hub_title, 'summary': hub['summary'],
                                      'lessons': [hub_path] + ['web-tech/' + topic['slug'] for topic in topics]})
root_entry['body'] += '<h2>' + link(hub_path) + '</h2>' + p(hub['summary']) + '<ul>' + ''.join('<li>' + link('web-tech/' + topic['slug']) + ' — ' + html.escape(topic['summary']) + '</li>' for topic in topics) + '</ul>'
root_entry['updated_at'] = stamp
crosslinks = {
    'web-tech/geolocation-accuracy-cancellation-and-retention': [hub_path, 'web-tech/location-consent-precision-and-map-alternatives'],
    'web-tech/interactive-graphics-and-canvas-boundaries': ['web-tech/map-viewport-tiles-and-request-lifecycle'],
    'web-tech/search-query-normalization-and-ranking': ['web-tech/nearby-spatial-search-and-tenant-filter'],
    'web-tech/accessible-inspection-map-export-project': ['web-tech/coordinate-validation-projection-and-antimeridian'],
}
for path, targets in crosslinks.items():
    by_path[path]['body'] += '<h2>Further connections</h2><p>' + '; '.join(link(target) for target in targets) + '.</p>'
    by_path[path]['updated_at'] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_hubs': 1, 'new_lessons': 4, 'prose_words': {
    topic['slug']: len(re.findall(r"\b[\w'-]+\b", ' '.join(str(topic[key]) for key in
        ('concept', 'case', 'implementation', 'cost', 'failure', 'drill', 'decision', 'summary')))) for topic in topics}}))
