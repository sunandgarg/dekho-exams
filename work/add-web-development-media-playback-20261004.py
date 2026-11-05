"""Add original on-demand media playback and delivery lessons."""
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

hub_path = 'web-tech/on-demand-media-playback-and-delivery'
hub_title = 'On-Demand Media Playback and Delivery'
topics = [
    {
        'slug': 'media-player-source-and-load-state',
        'title': 'Media Player Source and Load State',
        'summary': 'Choose a usable source, expose playback failures, and budget eager media loading.',
        'concept': 'A media element is a stateful client, not a decorative box around a file. It selects a source, fetches enough data to identify tracks, decodes frames, buffers ahead, and reports readiness and failure through separate states. A page should offer explicit controls and a nonmedia path to the same essential information. Preload is a hint rather than a download guarantee, and audible autoplay cannot be a prerequisite for understanding the page. Source choice must account for actual encoded tracks as well as container names. A successful HTTP response can still carry bytes the browser cannot decode.',
        'case': 'A field reviewer opens case 47 on a metered connection. Its inspection clip is 83 MiB, but the reviewer only needs to read the finding. The page renders the report and a poster first, asks for no full clip download during initial navigation, and shows a play control. A browser that cannot decode the preferred encode can choose a compatible alternative; if both sources fail, the reviewer can open a transcript and an authorized download. A failed play promise or a stalled stream receives an actionable message instead of a blank black rectangle. Switching from case 47 to case 63 releases the old player and its listeners.',
        'implementation': 'Keep native controls unless a custom interface can reproduce keyboard, captions, speed, volume, focus, and error behavior. Order source candidates by product policy, but verify the target browser can actually play them in a device test. Use a stable poster with dimensions so loading does not shift surrounding controls. Do not require autoplay. On an explicit play action, handle a rejected play attempt, loading state, waiting state, ended state, and error state as distinct outcomes. Make an essential transcript available without requiring media playback. Use a preload policy based on the page task, not an unconditional eager fetch. Remove event listeners and stop old playback when a route changes; a stale player should not continue speaking over the next case. If the clip is private, every source and fallback request still needs authorization.',
        'cost': 'For a clip of B bytes, transferring the whole asset is O(B) network and cache use, even if the user watches only a few seconds. Metadata loading can still request some media bytes, so measure actual transfer rather than assuming a hint forces a fixed amount. Decode consumes CPU, memory, and battery that vary with resolution, codec, and device. A poster adds its own request but can keep the initial page useful while the clip is idle. Limit parallel media players and stop hidden playback where product behavior permits. Measure initial page bytes, play-start delay, stall time, decode failure, transcript use, and bytes delivered per minute actually watched.',
        'failure': 'Block the first source format and verify the alternative works. Return a valid container with an unsupported video track and require a visible error path. Reject the play attempt and preserve an accessible manual control. Throttle the network after playback starts and show waiting without claiming the clip ended. Open the page on a metered device and confirm the first paint does not fetch the entire 83 MiB clip. Change routes while audio is playing and verify it stops. Disable script and confirm the report and transcript remain available. Inspect keyboard and screen-reader access to native controls, source error text, and the transcript path.',
        'drill': 'Build a case page with a poster, two encoded source candidates, a transcript, and an authorized fallback download for case 47. Load it with playback untouched and record transferred media bytes. Then press play, record time to first frame, force the first source to fail, and inspect the second. Move to case 63 during audio playback and count active media elements and event listeners. Simulate a rejected play promise. Report the user-facing state and whether the essential finding remained available throughout.',
        'decision': 'Media playback enriches a report; the report remains understandable when a source, decode, or play request fails.',
        'code': "function playerMessage(state) {\n  if (state.error) return 'Playback unavailable; open the transcript';\n  if (state.waiting) return 'Waiting for more video data';\n  return state.ended ? 'Clip finished' : 'Ready to play';\n}\nconsole.log(playerMessage({ error: true, waiting: false, ended: false }));\n// Output: Playback unavailable; open the transcript",
        'checks': ['The first page load does not fetch an entire unused clip.', 'Decode and play failures have visible fallback paths.', 'Old media stops on route change.'],
        'mistakes': ['Making audible autoplay the only entry to content.', 'Assuming a file extension proves codec support.', 'Replacing native controls without restoring their behavior.'],
        'related': ['web-tech/accessible-content-and-media', 'web-tech/browser-parse-load-and-render'],
    },
    {
        'slug': 'media-byte-ranges-seeking-and-version-identity',
        'title': 'Media Byte Ranges, Seeking, and Version Identity',
        'summary': 'Return coherent partial responses so a player can seek without mixing asset revisions.',
        'concept': 'Seeking into a large file usually asks for a portion of its bytes rather than a new copy of the whole file. A byte-range request names a start and optional end; the server must validate bounds against the selected immutable media representation. A satisfiable single range is a partial response with the exact range and total length. An unsatisfiable request reports the current total length without returning arbitrary bytes. The response body, range metadata, content type, validator, and authorization decision must all describe the same asset revision. If a transcoded file changes beneath a player, fragments from two versions can no longer form a coherent clip.',
        'case': 'Reviewer 47 jumps to minute 6 of a 391 MiB inspection recording. The browser requests bytes near a keyframe. The delivery service finds the exact immutable rendition and serves only the requested interval. During a background re-encode, a new rendition appears under a new identity rather than replacing the bytes being watched. The player can continue fetching ranges from the old rendition until its authorization or retention window ends. If the reviewer loses case permission, a later range request is denied even though earlier bytes were buffered. A signed delivery path, if used, is short-lived and bound to the case, rendition, and viewer policy.',
        'implementation': 'Parse only the range forms the service intends to support; reject malformed or excessive multipart requests before allocating work. Resolve the file identity and length before interpreting a range. For a valid single interval, send the exact slice with matching partial status and range metadata; never claim a full response while sending a fragment. Keep one immutable rendition ID per encode, with a validator tied to those bytes. When a client resumes conditionally, a changed validator should cause a full coherent response or an explicit restart rather than mixed fragments. Enforce case access on every request or on a narrowly scoped delivery grant whose expiry and revocation behavior is documented. Test proxy and object-storage behavior, because an origin implementation can be correct while an intermediary strips or rewrites range metadata.',
        'cost': 'Serving a requested interval of R bytes takes O(R) transfer and streaming work instead of O(B) for the full B-byte file. Parsing a bounded single range is O(1); unrestricted multipart ranges can amplify response assembly and should be capped. Frequent tiny seeks create request overhead, while very large read-ahead wastes bandwidth. Cacheable immutable renditions lower repeated origin reads but require a deliberate policy for private objects. A validator lookup and authorization check add latency to each range; design index and grant paths around measured load. Track partial-response correctness, seek-to-frame time, origin bytes, cache hits, rejected ranges, and permission revocations observed during playback.',
        'failure': 'Request the first 47 bytes, the last 63 bytes, and a range starting beyond the file length. Verify status, body length, and range metadata for each. Ask for a range with a stale validator after a new encode and ensure the response is coherent for one version. Change the asset while a proxy cache holds an old fragment; the rendition key must prevent mixed bytes. Revoke permission between two seeks and deny the second. Send a range list with thousands of spans and stop it before assembly. Confirm a browser can seek backward and forward through the actual deployed proxy, not only a local route handler.',
        'drill': 'Publish a 391 MiB clip as rendition 29 and map the authorized case to it. Ask for bytes 4700 through 4762 and assert that exactly 63 bytes return, with a total length matching rendition 29. Publish rendition 30, then ask for the old interval with a stale conditional validator. Observe whether the client restarts or continues one immutable version. Revoke access, repeat the range, and inspect denial. Compare full-file transfer with the bytes needed for a seek-heavy reviewer session.',
        'decision': 'A seek succeeds only when every partial response is authorized and belongs to one immutable asset revision.',
        'code': "function singleByteRange(start, end, total) {\n  if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end < start || end >= total) return null;\n  return { start, end, length: end - start + 1, total };\n}\nconsole.log(singleByteRange(4700, 4762, 391000000).length);\n// Output: 63",
        'checks': ['Partial body and metadata agree on length.', 'A new encode has a new immutable identity.', 'Revocation is enforced on later range requests.'],
        'mistakes': ['Returning partial bytes with a full-response status.', 'Changing bytes behind a stable rendition URL.', 'Treating earlier buffer access as permanent permission.'],
        'related': ['web-tech/http-delivery-and-cache-ownership', 'web-tech/private-asset-download-revocation-and-expiry'],
    },
    {
        'slug': 'adaptive-media-buffer-and-fallback-policy',
        'title': 'Adaptive Media Buffer and Fallback Policy',
        'summary': 'Bound segment buffering and choose a playable rendition without blocking the whole page.',
        'concept': 'Adaptive delivery separates a recording into short media segments at several quality levels. A player may select a lower rendition when throughput or decode capacity falls, then change again as conditions improve. The choice is a policy based on observed buffer and playback, not a promise that one bandwidth measurement predicts the future. A browser-managed media source needs careful append order and memory limits. Some devices or browsers may not support a chosen playback path; the product needs a direct file or alternate rendition fallback. The transcript must remain independent of the adaptive player.',
        'case': 'A reviewer watches pump station 29 from a train. The connection alternates between 1.8 and 7.4 megabits per second. Starting at the highest rendition drains the buffer before the first minute, so the player begins with a moderate version, monitors playable seconds ahead, and switches down after a sustained stall. Later it raises quality cautiously. The clip is a case record, not a continuous broadcast; every segment belongs to a versioned manifest. The viewer can pause, seek, and read a transcript without waiting for the adaptive code. If that code cannot initialize, a supported direct source remains available.',
        'implementation': 'Keep the manifest, segment addresses, codec description, and rendition revision consistent. Before appending a segment, check that the media source is open, the buffer is not already updating, and the selected rendition can be decoded. Wait for append completion before issuing another append. Bound forward and backward buffer duration; remove old buffered ranges at safe points so long sessions do not exhaust browser memory. React to quota errors by reducing buffer and quality rather than retrying the same append in a tight loop. Use actual playback progress, not fetch completion alone, to judge whether a switch helped. Provide a deterministic fallback path when media-source support, codec support, or a segment fetch fails. A custom player still needs keyboard controls, captions, visible errors, and a transcript.',
        'cost': 'Let S be fetched segment bytes and N the number of segments. Download and append work is O(S + N) plus decoder cost; retained buffered media is bounded by configured duration rather than the entire recording. More renditions multiply encoding and storage cost, while shorter segments increase manifest and request overhead. An eager high-quality choice can spend bandwidth on frames never watched. Too little buffer creates stalls under jitter. Measure startup time, rebuffering seconds per watch minute, rendition changes, bytes per watched minute, quota errors, and fallback use across target devices. Keep these metrics coarse enough to avoid turning detailed viewing history into routine tracking.',
        'failure': 'Start playback on a device that cannot decode the high rendition and verify a lower or direct source works. Fail one segment request mid-clip and keep the page responsive while the player retries within a bound or falls back. Force buffer quota exhaustion and confirm old ranges are released or playback degrades without an append loop. Pause for 20 minutes and check that the player does not fetch the entire 391 MiB recording. Seek far ahead and ensure stale segment requests cannot append into the new timeline. Disable media-source support and verify a transcript plus playable alternative remain. Test captions and keyboard controls after each fallback.',
        'drill': 'Build three renditions for case 47 with a versioned manifest and a direct-file fallback. Emulate a 1.8 megabit connection, then 7.4, then a short complete outage. Record startup delay, buffer seconds, quality decisions, fetched bytes, and quota behavior. Seek from minute 2 to minute 6 while an old segment is in flight; reject the stale append. Disable the adaptive path and complete the same review using the fallback and transcript. Inspect whether any error leaves the player spinning indefinitely.',
        'decision': 'Adaptive playback is useful when it reduces stalls and wasted bytes on the target devices; a bounded fallback remains part of the contract.',
        'code': "function renditionFor(bufferSeconds, stalled, available) {\n  if (stalled || bufferSeconds < 4) return available.low;\n  return bufferSeconds > 18 ? available.high : available.medium;\n}\nconsole.log(renditionFor(2, false, { low: '360p', medium: '540p', high: '900p' }));\n// Output: 360p",
        'checks': ['Segment appends are serialized and bounded.', 'A quota error does not create an infinite retry loop.', 'Unsupported devices retain a usable fallback.'],
        'mistakes': ['Buffering an entire recording for a short review.', 'Appending while the media buffer is updating.', 'Removing native controls without testing the replacement.'],
        'related': ['web-tech/media-and-live-updates', 'web-tech/stream-backpressure-and-bounded-work'],
    },
    {
        'slug': 'private-media-session-cache-and-timed-text',
        'title': 'Private Media Session, Cache, and Timed Text',
        'summary': 'Keep clips, segments, captions, and transcripts under one permission and revision policy.',
        'concept': 'A private clip is rarely one object. It may have a poster, several renditions, a manifest, many segments, caption tracks, and a transcript. Every object can reveal case information, so the authorization inventory must cover each route. A public CDN cache key cannot safely ignore user or grant scope for private material. Conversely, a narrowly scoped signed path can support efficient delivery if expiry, leakage, and revocation behavior are explicit. Timed text is part of the media revision; captions that describe an older cut can mislead a reviewer just as a mismatched video segment can.',
        'case': 'Case 47 contains an inspection recording with captions at revision 29. After editing, the video becomes revision 30, but the old caption file remains cached at a stable address. Reviewer 63 sees words at the wrong moments and interprets a repair as unfinished. Meanwhile, a shared cache serves a poster from a private case to a different account. The fix assigns a versioned identity to video, poster, caption, and transcript together, then checks the viewer’s case permission before issuing a delivery grant. A new revision gets new cache keys. The UI exposes the caption language and transcript revision instead of silently mixing old text with new frames.',
        'implementation': 'Create a manifest record that lists the current clip revision and every derived asset ID. When publishing a new cut, validate caption cue timing, language labels, transcript content, and poster against that cut before making it current. Deliver private assets through an authorization check or a short-lived grant bound to one asset family and requester context. Decide whether grant revocation must take effect immediately or at expiry, and do not claim stronger revocation than the delivery path provides. Put no private filenames or case text in public cache keys or response headers. Choose cache directives separately for public and private assets, and test the CDN with two accounts. Offer captions and a text transcript without forcing a video download; a caption file alone does not describe important visual information that has no speech.',
        'cost': 'Each rendition, caption language, poster, and transcript adds storage proportional to its own bytes. Revisioned names reduce mixed-cache risk but leave old objects that need a retention and cleanup policy. Checking authorization for every small segment increases origin traffic; scoped grants can reduce that cost while introducing an expiry window. Caption validation is O(C) for C cues, with checks for ordering, overlaps under the chosen policy, and duration bounds. Track private cache misses, denied asset requests, stale revision reports, caption selection, and transcript usage. Avoid collecting exact viewing positions in routine analytics unless the product has a clear need and retention rule.',
        'failure': 'Request the clip manifest as an unauthorized account, then request a guessed segment, poster, caption, and transcript address; all must follow the same private policy. Change video revision while leaving an old caption path in a cache and confirm the new manifest cannot reference it. Expire a grant midway through playback and show a clear renewal or denial state without silently exposing future segments. Revoke case access and measure the maximum remaining grant lifetime. Serve malformed timed text and avoid presenting it as a correct caption. Compare transcript content with the edited cut, including relevant non-speech visual events. Test cache behavior across two tenants that happen to use similar case IDs.',
        'drill': 'Publish a private 7-minute clip for case 47 with two renditions, a poster, English captions, and a descriptive transcript at revision 29. Edit the recording to revision 30 and intentionally leave one old caption file. The publish gate should refuse the mismatched asset family. Issue a 63-second delivery grant, switch accounts, and attempt direct requests for all five asset types. Review which bytes remain reachable after access revocation and document the grant window honestly. Test a text-only route that opens the transcript without a media request.',
        'decision': 'A private media experience is a versioned family of assets with one explicit access rule, not an isolated video URL.',
        'code': "function sameMediaRevision(manifest) {\n  return [manifest.poster, manifest.captions, manifest.transcript].every(\n    asset => asset.revision === manifest.video.revision\n  );\n}\nconsole.log(sameMediaRevision({ video: { revision: 30 }, poster: { revision: 30 }, captions: { revision: 29 }, transcript: { revision: 30 } }));\n// Output: false",
        'checks': ['Every derived asset follows the case access policy.', 'Video and timed text publish under one revision.', 'Cache and grant behavior is tested across accounts.'],
        'mistakes': ['Guarding the video while leaving captions public.', 'Reusing a stable private asset URL across revisions.', 'Claiming immediate revocation for an unexpired independent grant.'],
        'related': ['web-tech/accessible-content-and-media', 'web-tech/file-ingestion-and-private-asset-lifecycle'],
    },
]

assert hub_path not in by_path and len(topics) == 4
hub = copy.deepcopy(by_path['web-tech/production-signals-and-incident-decisions'])
hub.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + hub_path)), path=hub_path,
           title=hub_title, summary='Serve and play large media with coherent seeks, bounded buffers, private asset access, and matching timed text.',
           sort_order=3080, created_at=stamp, updated_at=stamp, published_at=stamp)
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
                 title=topic['title'], summary=topic['summary'], sort_order=3081 + number,
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
hub['body'] = p('A media player crosses document, transport, decode, permission, and accessibility boundaries. This track follows an inspection clip through initial loading, seek requests, adaptive buffering, and a private asset family that includes captions and a transcript. Each part needs a usable failure state. The report remains available when playback is unsupported, and a private segment remains private even if its manifest was previously loaded.')
hub['body'] += '<h2>Topics in this track</h2><ul>' + ''.join('<li>' + link('web-tech/' + topic['slug']) + ' — ' + html.escape(topic['summary']) + '</li>' for topic in topics) + '</ul>'
hub['body'] += '<h2>Prerequisite paths</h2><p>' + '; '.join(link(path) for path in ['web-tech/media-and-live-updates', 'web-tech/http-delivery-and-cache-ownership', 'web-tech/accessible-content-and-media']) + '.</p>'
root_entry = by_path['web-tech/web-technology']
root_entry['data']['modules'].append({'title': hub_title, 'summary': hub['summary'],
                                      'lessons': [hub_path] + ['web-tech/' + topic['slug'] for topic in topics]})
root_entry['body'] += '<h2>' + link(hub_path) + '</h2>' + p(hub['summary']) + '<ul>' + ''.join('<li>' + link('web-tech/' + topic['slug']) + ' — ' + html.escape(topic['summary']) + '</li>' for topic in topics) + '</ul>'
root_entry['updated_at'] = stamp
crosslinks = {
    'web-tech/media-and-live-updates': [hub_path, 'web-tech/media-player-source-and-load-state'],
    'web-tech/http-delivery-and-cache-ownership': ['web-tech/media-byte-ranges-seeking-and-version-identity'],
    'web-tech/stream-backpressure-and-bounded-work': ['web-tech/adaptive-media-buffer-and-fallback-policy'],
    'web-tech/accessible-content-and-media': ['web-tech/private-media-session-cache-and-timed-text'],
}
for path, targets in crosslinks.items():
    by_path[path]['body'] += '<h2>Further connections</h2><p>' + '; '.join(link(target) for target in targets) + '.</p>'
    by_path[path]['updated_at'] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_hubs': 1, 'new_lessons': 4, 'prose_words': {
    topic['slug']: len(re.findall(r"\b[\w'-]+\b", ' '.join(str(topic[key]) for key in
        ('concept', 'case', 'implementation', 'cost', 'failure', 'drill', 'decision', 'summary')))) for topic in topics}}))
