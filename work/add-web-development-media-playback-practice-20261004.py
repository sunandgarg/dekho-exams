"""Add private media playback project and twelve-question quiz."""
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
    'web-tech/media-player-source-and-load-state',
    'web-tech/media-byte-ranges-seeking-and-version-identity',
    'web-tech/adaptive-media-buffer-and-fallback-policy',
    'web-tech/private-media-session-cache-and-timed-text',
]
project_path = 'web-tech/private-inspection-clip-playback-project'
quiz_path = 'quizzes/web-development-media-playback-decisions'
assert project_path not in by_path and quiz_path not in by_path
code = "function canServeClipAsset(request, manifest) {\n  return request.caseAuthorized && request.assetRevision === manifest.videoRevision &&\n    manifest.assetIds.has(request.assetId) && request.grantExpiresAt > request.now;\n}\nconsole.log(canServeClipAsset({ caseAuthorized: true, assetRevision: 29, assetId: 'caption-47', grantExpiresAt: 63, now: 47 }, { videoRevision: 30, assetIds: new Set(['caption-47']) }));\n// Output: false"
subprocess.run(['node', '--check', '--input-type=module'], input=code, text=True, capture_output=True, check=True)
project = copy.deepcopy(by_path['web-tech/case-save-incident-evidence-project'])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + project_path)), path=project_path,
               title='Project: private inspection clip playback',
               summary='Build a reviewable clip player with coherent seeks, bounded buffering, private assets, captions, and fallback.',
               sort_order=1317, created_at=stamp, updated_at=stamp, published_at=stamp)
project['data'] = {'subject_root': 'web-tech/web-technology', 'section_path': 'web-tech/web-technology/project',
                   'content_format': 'html', 'seo_ready': False, 'kind': 'project',
                   'author_path': 'authors/aitrove-editorial', 'reading_minutes': 8, 'related': lessons}
project['body'] = p('Build a private inspection clip page for case 47. The report and a descriptive transcript load first; an 83 MiB clip does not have to download before the reviewer can read the finding. Provide native media controls, a poster with dimensions, captions, and a playable direct source. A separate adaptive path may choose between three rendition levels. It measures stalls and available buffer, switches quality conservatively, and caps retained media. A browser without that path still plays the direct source or opens the transcript. The service publishes each clip cut as an immutable revision with matching renditions, poster, captions, and transcript. A seek requests a byte interval from one revision and receives an exact partial body and range metadata. An invalid interval is rejected without fetching arbitrary bytes. A re-encode creates a new identity; the active player cannot mix old and new fragments. Access to the manifest, direct file, segment, poster, caption, and transcript follows one case permission policy. If delivery grants are used, record their expiry and revocation limit honestly. The browser handles blocked play, stalled transfer, decode failure, ended state, and route changes. A private error never exposes the case file name to an unauthorized account. The project must work when script fails, when a source format is unavailable, when the adaptive buffer reaches quota, and when a reviewer loses permission midway through playback.')
project['body'] += '<h2>Build contract</h2><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in [
    'Keep essential report and transcript content available before or without media playback.',
    'Serve correct, immutable byte ranges and reject malformed seeks.',
    'Bound segment fetching and buffered media while retaining a direct source fallback.',
    'Apply one revision and access policy to every derived clip asset.',
]) + '</ul>'
project['body'] += '<h2>Implementation checkpoint</h2><pre><code class="language-javascript">' + html.escape(code, quote=False) + '</code></pre>'
project['body'] += p('The checkpoint denies an old caption revision even while the requester still has case access. The server must resolve the asset family and permission from authoritative storage, not from fields the browser supplies. Expected set membership is O(1), with O(A) space for A manifest asset IDs; actual delivery remains O(R) for R requested bytes. A short grant lowers repeated authorization calls but leaves a defined exposure window after revocation. Retention must remove old renditions and caption copies only after active references and review obligations are accounted for.')
project['body'] += '<h2>Failure drill</h2>' + p('Load the report on a metered connection and record media bytes before pressing play. Reject autoplay, fail the first codec, then start playback from the alternative. Seek to minute 6 and verify response status, body length, range bounds, and immutable rendition key through the deployed proxy. Start a second seek while the first segment is in flight and prevent its stale append. Force buffer quota exhaustion, release old ranges, and preserve controls. Publish revision 30 with captions from revision 29 and block the release. Switch accounts and try the manifest, segment, poster, caption, and transcript directly. Revoke access during playback and measure what an unexpired grant can still reach. Close the page while audio plays and verify it stops. Test captions, keyboard controls, transcript access, and all visible failure messages with assistive technology.')
project['body'] += '<h2>Acceptance checks</h2><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in [
    'Initial reading does not require an 83 MiB download.',
    'Seek responses and asset revision identity stay coherent.',
    'An unsupported or quota-limited player has a tested fallback.',
    'No derived asset bypasses private case permission.',
]) + '</ul>'
project['body'] += '<h3>Common Mistakes</h3><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in [
    'Testing only the video file while leaving timed text or posters public.',
    'Assuming a metadata preload hint guarantees a fixed transfer size.',
    'Mixing cached fragments from two encoded revisions.',
]) + '</ul>'
project['body'] += '<h2>Related lessons</h2><p>' + '; '.join(link(path) for path in lessons) + '.</p>'
entries.append(project)
by_path[project_path] = project

questions = [
    ('What must remain usable if a clip cannot play?', ['The essential report and a descriptive transcript', 'Only a spinner', 'An automatic full-file download'], 'Playback can fail because of transport or decode support. The user still needs a text route to the finding and any relevant visual detail.'),
    ('What does a media preload setting guarantee?', ['It is a hint, so actual transferred bytes must be measured', 'Exactly one metadata packet', 'That the whole file is cached'], 'The browser controls fetching details. An application should measure the real page and media transfer on target devices.'),
    ('What should a rejected play request do?', ['Leave an explicit manual control and visible state', 'Mark the clip ended', 'Retry audible autoplay forever'], 'Playback may be blocked or fail. The page must keep a usable user action and a fallback instead of presenting false completion.'),
    ('What response represents a valid single byte interval?', ['A partial response with matching bounds, length, and body', 'A full status with only fragment bytes', 'An interval from a different rendition'], 'The declared interval and returned bytes must refer to one immutable media representation or the player cannot seek reliably.'),
    ('What happens when a requested range starts beyond the asset?', ['Reject it with the current asset length', 'Return bytes from the next file', 'Silently serve the whole clip as a fragment'], 'An out-of-bounds interval has no bytes to serve. The response should make the valid total length clear without fabricating data.'),
    ('Why give a re-encode a new rendition identity?', ['To prevent cached fragments from different byte versions mixing', 'To avoid all cache entries', 'To make the caption language change automatically'], 'A stable address whose bytes change can leave a player combining old and new fragments across seeks and caches.'),
    ('What should an adaptive player do after buffer quota failure?', ['Release safe old ranges or choose a fallback within a bound', 'Append the same bytes in a tight loop', 'Download every rendition fully'], 'A browser buffer has limits. Repeated append without reducing retained media cannot repair the quota condition.'),
    ('What should quality selection consider?', ['Observed playback, buffer, and device capability', 'Only the highest advertised network speed', 'Only the poster size'], 'Throughput varies and decode support differs. Stall and buffer evidence is more useful than a single optimistic bandwidth value.'),
    ('What happens if media-source support is absent?', ['Use a tested direct source or transcript path', 'Hide the entire report', 'Require an unrelated browser extension'], 'A feature-dependent player needs a usable alternative on the actual target browser and device.'),
    ('Which objects need private case policy?', ['Manifest, segments, poster, captions, transcript, and direct file', 'Only the first video URL', 'Only the visible poster'], 'Derived assets can reveal private case information even when the main video route is guarded.'),
    ('What does a short-lived delivery grant imply after revocation?', ['Previously issued access may persist until expiry under that design', 'Every cached byte vanishes immediately', 'The grant becomes a permanent permission'], 'Independent grants reduce checks but create a bounded revocation window that the product must state and test.'),
    ('When may a new edited clip become current?', ['After its video and timed text assets match one revision', 'As soon as one video segment uploads', 'While captions still describe the prior cut'], 'Captions and transcripts tied to an older cut can mislead a reviewer. Publish the asset family as one coherent revision.'),
]
quiz = copy.deepcopy(by_path['quizzes/web-development-graphics-editor-decisions'])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + quiz_path)), path=quiz_path,
            title='Web Development: media playback decisions quiz',
            summary='Twelve explained decisions about source failure, seeks, buffers, private media, captions, and revision identity.',
            sort_order=1318, created_at=stamp, updated_at=stamp, published_at=stamp)
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
project_hub['body'] += '<h2>Media playback project</h2><p>' + link(project_path) + ' — ' + html.escape(project['summary']) + '</p>'
project_hub['summary'] = 'Build and verify fifty-five projects across browser, API, data, identity, deployment, model-backed features, and private media playback.'
project_hub['updated_at'] = stamp
quiz_hub = by_path['web-tech/quizzes']
quiz_hub['data']['modules'][0]['lessons'].append(quiz_path)
quiz_hub['body'] += '<h2>Media playback checks</h2><p>' + link(quiz_path) + ' — ' + html.escape(quiz['summary']) + '</p>'
quiz_hub['updated_at'] = stamp
hub = by_path['web-tech/on-demand-media-playback-and-delivery']
hub['body'] += '<h2>Practice path</h2><p>Build ' + link(project_path) + ' and check decisions in ' + link(quiz_path) + '.</p>'
hub['updated_at'] = stamp
for lesson_path in lessons:
    lesson = by_path[lesson_path]
    lesson['body'] += '<h2>Connected practice</h2><p>Build ' + link(project_path) + ' and review ' + link(quiz_path) + '.</p>'
    lesson['data']['related'].extend([project_path, quiz_path])
    lesson['updated_at'] = stamp
root_entry = by_path['web-tech/web-technology']
root_entry['body'] += '<h2>Media playback practice</h2><p>Apply this track with ' + link(project_path) + '.</p>'
root_entry['updated_at'] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_projects': 1, 'new_quizzes': 1, 'new_questions': len(questions)}))
