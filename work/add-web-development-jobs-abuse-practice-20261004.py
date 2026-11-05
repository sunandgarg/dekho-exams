"""Add projects and quiz for background workflow reliability and public-endpoint abuse."""
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
        'path': 'web-tech/permit-report-job-recovery-project',
        'title': 'Project: permit report job recovery',
        'summary': 'Admit one report, survive duplicate workers, quarantine old payloads, and expose honest cancel state.',
        'hub': 'web-tech/background-workflow-reliability',
        'intro': 'Build a report workflow for case 47 at revision 29. The browser sends one idempotency key and receives a durable job ID plus an authorized status path. It does not receive a fake finished report. A repeated request with the same tenant, requester, revision, and payload returns the same job; a key reused for changed content returns a conflict. Commit the job row with an outbox intent so a crash between database commit and queue send cannot lose the work. The worker may receive a message more than once. It checks a stable effect ledger before creating the artifact or sending a completion notice. An expired lease can start a second worker, but only the current guarded state transition publishes the result. The status resource names queued, running, succeeded, failed, canceled, or partially canceled as separate outcomes. A private result link appears only after success and is checked against current record permission on access. An old-schema payload that cannot run moves to quarantine after bounded attempts without blocking healthy jobs. Replay retains its job and effect identity, rechecks current authorization, and records operator approval. A nightly digest of report completions uses a tenant and time-window claim; overlap coalesces instead of sending two messages. Cancellation stops future work at checkpoints, while a notice already sent remains visible as an escaped effect. The operator can initiate a corrective notice with its own ID. The UI distinguishes accepted work from server-confirmed completion in every path.',
        'scope': ['Map duplicate admissions to one job or a conflict.', 'Make queue redelivery and lease expiry safe for business effects.', 'Quarantine permanent failures with controlled replay.', 'Expose cancellation, schedule overlap, and already-published effects honestly.'],
        'code': "function mayPublishJob(job, effectLedger) {\n  const effectKey = `${job.id}:${job.resultRevision}`;\n  return job.claimVersion === job.currentVersion && !job.cancelRequested && !effectLedger.has(effectKey);\n}\nconsole.log(mayPublishJob({ id: 84, resultRevision: 29, claimVersion: 5, currentVersion: 5, cancelRequested: false }, new Set(['84:29'])));\n// Output: false",
        'cost': 'An indexed idempotency record and effect ledger add reads and retention storage, but prevent duplicate report CPU, storage, and provider sends. Rendering is O(report bytes) plus database work. Polling status every second from 83 tabs can become unnecessary load, so pause hidden tabs and use a bounded interval. Quarantine and replay add operator work; monitor oldest item age and failure class. A tenant claim reduces overlap while potentially delaying a large tenant. Limit catch-up windows after an outage rather than releasing an unbounded backlog. Measure queue age, duplicate delivery, duplicate effect count, cancel latency, and report completion by tenant.',
        'failure': 'Crash after writing the job row but before queue publication; the outbox must relay it. Crash again after artifact write and before acknowledgement; redelivery must leave one artifact and one notice. Let a lease expire with two workers active, then verify only the current claim can publish. Submit an unsupported schema and show quarantine after the chosen attempts, while 46 valid jobs continue. Replay the item twice and require one effect. Revoke the requester before result access. Cancel while rendering, then after a notice is sent; report the distinct outcomes. Pause the scheduler for two days and verify bounded catch-up rather than a burst of every missed tick.',
        'checks': ['One admission identity produces one report effect.', 'A job can move from accepted to a visible terminal failure.', 'Poison work does not block valid jobs and replay is audited.', 'Cancellation never claims to undo an escaped notice.'],
        'mistakes': ['Acknowledging a message before durable state commits.', 'Giving a queued job a completed label.', 'Replaying quarantined work with a new effect identity.'],
        'related': ['web-tech/job-admission-idempotency-and-status-resource', 'web-tech/worker-leases-retries-and-duplicate-effects', 'web-tech/poison-job-quarantine-and-replay-control', 'web-tech/scheduled-job-overlap-cancel-and-compensation'],
    },
    {
        'path': 'web-tech/public-permit-abuse-control-project',
        'title': 'Project: public permit endpoint abuse controls',
        'summary': 'Protect recovery, search, and export without disclosing accounts or blocking shared-office reviewers.',
        'hub': 'web-tech/abuse-resistant-public-endpoints',
        'intro': 'Build abuse controls for a permit portal used from home, shared municipal offices, and an embedded review station. Public recovery requests return one generic response shape whether an account exists or not; delivery occurs asynchronously so the request path does not expose a simple timing split. Identity, source, and provider-spend budgets prevent a distributed client from making unlimited mail requests. A reviewer who is limited gets a safe help route, and recovery tokens remain short-lived and single-use. Search requests carry bounded page size, filter count, execution time, and tenant concurrency before database work starts. A large export becomes a job with a status path instead of an unbounded synchronous request. A challenge may be offered for suspicious expensive actions, but it does not override record permission or the tenant budget. The UI includes an accessible alternate process for people who cannot complete a visual challenge. The rules store only bounded decision categories in routine telemetry. A new export rule rolls out to a small cohort with measured legitimate task completion, appeals, and resource use. If 83 reviewers behind one address are blocked, the team can disable that rule version while keeping base authorization and work limits active. The project has an operator record for each rule: owner, version, exposure, thresholds, stop action, and short raw-signal retention. An automatic block count is never presented as proof of success by itself.',
        'scope': ['Keep known and unknown recovery identities publicly indistinguishable.', 'Bound both request rate and actual compute, bytes, and provider spend.', 'Make challenges action-scoped with an accessible alternative.', 'Stage and roll back a mistaken rule without dropping base protection.'],
        'code': "function admitPermitExport(request) {\n  if (!request.recordAuthorized) return 'deny';\n  if (request.tenantCostRemaining < request.estimatedCost) return 'defer';\n  if (request.challengeRequired && !request.challengePassed) return 'challenge';\n  return 'admit';\n}\nconsole.log(admitPermitExport({ recordAuthorized: true, tenantCostRemaining: 19, estimatedCost: 31, challengeRequired: false, challengePassed: false }));\n// Output: defer",
        'cost': 'A request counter is O(1), but reliable enforcement across distributed servers has storage and consistency costs. Search admission takes O(filter count) after a hard filter bound; the expensive query must still have a timeout and result-byte limit. Third-party sends incur direct charges. Challenges add abandonment and sometimes vendor script weight. Telemetry needs bounded categories rather than raw case IDs or device histories. Measure legitimate completion, false-positive appeals, provider charges, database CPU, queue age, and ordinary case-read latency under 83 parallel expensive requests.',
        'failure': 'Compare public recovery responses for a known and unknown address across body, status, and repeated timings. Send 83 requests from one network against distinct accounts, then distribute requests to one account from multiple networks; limits should cover both. Request huge search pages and nested filters, then verify denial before database work. Trigger a challenge with a screen reader, complete its alternative, and still require the tenant export budget. Block the challenge vendor script and preserve the help path. Roll out a new rule that catches a shared-office network, watch legitimate completion fall, and disable only that rule. Review logs for private tokens, raw search text, and signal retention expiry.',
        'checks': ['Recovery behavior does not reveal account existence.', 'Work budgets bind parallel and expensive operations.', 'Challenge success does not waive authorization or cost limits.', 'False positives trigger a narrow, auditable rollback.'],
        'mistakes': ['Relying only on an IP counter.', 'Adding a puzzle to every task without an alternate route.', 'Calling a rule successful because blocks increased.'],
        'related': ['web-tech/account-recovery-enumeration-and-throttle-policy', 'web-tech/expensive-request-work-budgets-and-shed-load', 'web-tech/human-challenges-accessible-alternatives-and-signal-retention', 'web-tech/abuse-decision-telemetry-and-false-positive-rollback'],
    },
]

for number, project in enumerate(projects, 1):
    assert project['path'] not in by_path
    subprocess.run(['node', '--check', '--input-type=module'], input=project['code'], text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path['web-tech/case-save-incident-evidence-project'])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + project['path'])), path=project['path'],
                 title=project['title'], summary=project['summary'], sort_order=1310 + number,
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
    ('What does accepting a report job mean?', ['A durable intent exists, not that the report is finished', 'The private result is ready for anyone with the ID', 'The worker has already sent a notice'], 'An accepted operation needs a stable status path; later worker and provider failures can still change its terminal outcome.'),
    ('What should the same idempotency key with changed payload produce?', ['A conflict rather than a second effect', 'A second report with the same job ID', 'An automatic overwrite of the first payload'], 'The server binds a key to its scoped payload. Reusing it for different business input cannot silently change the admitted operation.'),
    ('Why can a worker receive a job twice?', ['A crash or lease expiry can expose the message again', 'The browser always sends two requests', 'A unique database index guarantees duplicate delivery'], 'A queue lease is temporary. The business effect needs its own stable identity and durable deduplication boundary.'),
    ('What belongs in a poison-job path?', ['Bounded attempts, minimal failure data, and controlled replay', 'Unlimited retries ahead of healthy jobs', 'A new job identity for every replay'], 'Permanent failures should leave the normal retry loop while retaining enough audited context for safe repair or an honest loss outcome.'),
    ('What does canceling after an email send guarantee?', ['Only future work can stop; the sent message remains an escaped effect', 'The recipient mailbox is erased', 'The queue can always reverse external effects'], 'Cancellation and compensation are separate actions. A sent notice cannot be treated as though it never happened.'),
    ('How should overlapping scheduled runs be handled?', ['With a declared skip, coalesce, queue, or parallel policy', 'By assuming the older run always finishes first', 'By launching every missed tick at once'], 'A schedule makes work eligible. Ownership and catch-up limits decide what happens when runs overlap or the scheduler recovers.'),
    ('What leaks account existence on recovery?', ['Different public status, timing, or response shape', 'A generic visible message with otherwise matched behavior', 'An internal delivery intent unavailable to the requester'], 'A visible generic message alone is insufficient if an observer can distinguish known and unknown identities by other public signals.'),
    ('What must an expensive search budget include?', ['Work shape, result size, time, and aggregate concurrency', 'Only requests per minute', 'Only the browser viewport width'], 'A low request rate can still exhaust CPU or provider spend when one call fans out or returns unbounded data.'),
    ('What follows a passed human challenge?', ['The same authorization and business budgets still apply', 'All future actions are trusted', 'A tenant export limit is removed'], 'A challenge is one signal for one action, not a permission grant or permanent exemption from resource limits.'),
    ('What is needed when a visual challenge blocks a user?', ['An accessible alternative with accountable review', 'A requirement to use a different device', 'An unlimited allowlist for the whole network'], 'Abuse controls should preserve a real task path for people who cannot complete a particular challenge format.'),
    ('How should a new abuse rule be judged?', ['By abuse reduction and legitimate task completion together', 'By block count alone', 'By the number of collected device fingerprints'], 'False positives can make a rule appear effective while denying real reviewers. Compare outcomes with a denominator and observation window.'),
    ('What should rollback of one mistaken rule preserve?', ['Base record authorization and work budgets', 'The mistaken rule at full exposure', 'No protection of any kind'], 'A narrow kill action removes the new rule layer while retaining independent access checks and resource controls.'),
]
quiz_path = 'quizzes/web-development-jobs-abuse-decisions'
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path['quizzes/web-development-graphics-editor-decisions'])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + quiz_path)), path=quiz_path,
            title='Web Development: jobs and abuse decisions quiz',
            summary='Twelve explained decisions about job admission, duplicate work, quarantine, recovery, request budgets, and false positives.',
            sort_order=1315, created_at=stamp, updated_at=stamp, published_at=stamp)

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
project_hub['body'] += '<h2>Background work and abuse projects</h2><ul>' + ''.join(
    '<li>' + link(project['path']) + ' — ' + html.escape(project['summary']) + '</li>' for project in projects) + '</ul>'
project_hub['summary'] = 'Build and verify fifty-three projects across browser, API, data, identity, search, rendering, operations, privacy, deployment, offline storage, components, background work, and abuse controls.'
project_hub['updated_at'] = stamp
quiz_hub = by_path['web-tech/quizzes']
quiz_hub['data']['modules'][0]['lessons'].append(quiz_path)
quiz_hub['body'] += '<h2>Background work and abuse checks</h2><p>' + link(quiz_path) + ' — ' + html.escape(quiz['summary']) + '</p>'
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
root_entry['body'] += '<h2>Background work and abuse practice</h2><p>Apply the tracks with ' + link(projects[0]['path']) + ' and ' + link(projects[1]['path']) + '.</p>'
root_entry['updated_at'] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_projects': len(projects), 'new_quizzes': 1, 'new_questions': len(questions)}))
