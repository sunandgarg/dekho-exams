"""Add linked release-control and GraphQL API practice drafts."""
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
    dict(path='web-tech/assignment-panel-release-experiment-project', title='Project: assignment panel release experiment', summary='Stage a feature flag, prove the old path after new writes, and audit experiment exposure.', intro='Build a staged release for the case-review assignment panel. The service evaluates a versioned flag for stable reviewer IDs, exposes the new panel to staff and then a bounded cohort, and returns one resolved variant to the browser. Every assignment mutation still checks current case and tenant authorization. Reviewer 29 may see the new panel while reviewer 47 sees the old one, yet both use the same revisioned write contract. Define a safe evaluation default when configuration is unavailable. Write a stop rule for save failures and latency, then rehearse disabling the panel after new-form data exists. The old form must read those cases. For a separate experiment, assign a stable unit, record exposure only when either panel actually renders, and join an approved completion metric without private case fields. Check group balance, crossover, missing events, and errors before interpreting any result. When the release decision is settled, remove the temporary branch and ruleset while retaining the named emergency control.', scope=['Evaluate the same reviewer across refresh, tabs, and devices, with a tested configuration-outage default.','Call the mutation endpoint directly as a reviewer without case rights; the flag must not grant access.','Create cases through the new form, turn the release off, and read them through the old form.','Compare control and treatment exposure at the same render point and detect missing or crossed assignments.'], code='function releaseDecision(failureCount, attemptCount, maximumRate) {\n  return attemptCount && failureCount / attemptCount > maximumRate ? "stop" : "continue";\n}\nconsole.log(releaseDecision(7, 47, 0.1));\n// Output: stop', cost='Local evaluation is near O(1), while a remote flag lookup or refresh adds latency and a failure path. Supporting two forms doubles part of the test surface and requires state compatibility during rollout. Exposure logging adds records proportional to eligible rendered sessions, so minimize context and deduplicate repeated renders. The experiment needs enough data and a fixed observation rule before interpreting results; a tiny cohort may establish safety without supporting a business conclusion. Monitor variant-specific save errors, latency, config age, exposure joins, and the time required to stop the new path.', failure='Set the flag to new in a browser header and call updateCase as reviewer 47 without permission; the server must reject it. Disable the new panel after reviewer 29 writes a new field and confirm the old form still opens the case. Suspend a tab during a kill action and try to submit its stale form; server evaluation must enforce the off state. Crash only the treatment before exposure logging and detect group imbalance rather than reading a biased metric. Finally remove the release flag and test offline clients, old stored values, and queued jobs.', checks=['Release exposure never replaces current object authorization.','The off path handles data created while the release was on.','Experiment groups have stable units and equivalent exposure points.','Temporary flag code and rules have a reviewed retirement path.'], mistakes=['Calling a percentage rollout an experiment without data-quality checks.','Assuming a flag turn-off reverses completed writes.','Leaving an old path and remote rule after the decision is final.'], related=['web-tech/feature-flag-evaluation-scope-and-safe-default','web-tech/gradual-rollout-kill-switch-and-state-compatibility','web-tech/experiment-assignment-exposure-and-metric-integrity','web-tech/flag-telemetry-audit-and-retirement']),
    dict(path='web-tech/tenant-safe-graphql-case-api-project', title='Project: tenant-safe GraphQL case API', summary='Build a typed case graph with request-local batching, query budgets, idempotent mutations, and stable cursors.', intro='Build a GraphQL case view for reviewer 29 in organization 6. The schema exposes cases, owners, and activity with honest nullability for older unassigned cases. An additive field replaces an older owner label while old operation documents remain valid during migration. Querying 47 cases with owner names must not issue 47 separate owner service calls; a request-local loader batches and restores key order, with tenant and permission scope in its lookup. The endpoint admits only bounded work: aliases, depth, list page sizes, and weighted fields count toward a request budget. A known operation ID can narrow public traffic but never grants object access. updateCase takes expected revision and a stable idempotency key, records one write and one outbox intent, and returns a typed conflict when the revision is stale. The activity connection pages by event time plus immutable ID so ties do not drop rows.', scope=['Query historical null owner data and keep old client operations valid during schema change.','Batch 47 owner lookups without sharing loader results across tenant requests.','Reject wide aliases, missing pagination limits, and over-budget work before running resolvers.','Repeat a mutation and page equal-timestamp activity across concurrent inserts without duplicate writes or missing rows.'], code='function queryAdmitted(parentCount, requestedItems, maximumItems) {\n  return requestedItems <= maximumItems && parentCount * requestedItems <= 940;\n}\nconsole.log(queryAdmitted(23, 47, 40));\n// Output: false', cost='Schema validation and cost scoring are O(m) in the operation document, while nested list execution can multiply result counts across levels. A request-local batch changes 47 backend round trips into a bounded set of calls but still moves O(n) owner records and needs ordered results. Keyset pagination can use an index to read O(log n plus k) work for k results, whereas deep offset scans may grow with skipped rows. Idempotency adds a small keyed record and a transaction. Monitor estimated versus actual cost, backend calls, denial counts, mutation conflicts, and page gaps.', failure='Declare owner non-null and query a historical case with no owner; observe error propagation and fix the schema contract. Return batched owner rows in another order and ensure the loader restores requested keys. Run reviewer 29 and reviewer 62 concurrently with a shared owner ID; no cache value may cross tenant scope. Send 600 shallow aliases and confirm admission rejects before resolution. Retry updateCase after a timeout and verify one effective write. Page two activity records with equal timestamps using only time as a cursor, detect the missing row, and add the immutable ID tie-breaker.', checks=['Old schema operations and historical records obey declared nullability.','Batch caches stay inside one authorized request.','Document cost and pagination bounds apply before resolver work.','Mutation and cursor rules survive retries and equal sort values.'], mistakes=['Assuming a typed schema is an access policy.','Using a process-global loader for tenant data.','Reading HTTP success as proof a domain mutation applied.'], related=['web-tech/graphql-schema-nullability-and-evolution','web-tech/graphql-resolver-batching-and-tenant-scope','web-tech/graphql-operation-cost-and-admission','web-tech/graphql-mutation-errors-and-pagination-contracts']),
]

for number, project in enumerate(projects, 1):
    assert project['path'] not in by_path
    subprocess.run(['node','--check','--input-type=module'], input=project['code'], text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path['web-tech/case-save-incident-evidence-project'])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + project['path'])), path=project['path'], title=project['title'], summary=project['summary'], sort_order=1210 + number, created_at=stamp, updated_at=stamp, published_at=stamp)
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
    ('What does a feature flag decide?', ['Which behavior a defined context sees, not which private object it may access', 'Whether a user is authorized for every case', 'Whether a mutation transaction committed'], 'Release exposure and object authorization are separate decisions. The server must check current case rights on every data operation.'),
    ('What should a service do when remote flag configuration is unavailable?', ['Use a documented, tested safe default', 'Trust a client-supplied variant header', 'Grant the new mutation to everyone'], 'A fallback must preserve core work and security. Server and browser should share one resolved decision for a request.'),
    ('Why test the old path after the new path has written data?', ['Turning a flag off does not undo stored state', 'The browser cache is always empty', 'A flag automatically migrates the database'], 'New writes can leave data the old code cannot read. Compatibility must be proved before staged exposure.'),
    ('What makes a rollout stop rule useful?', ['A named metric, threshold, owner, and observed response path', 'Only an arbitrary percentage', 'Only an optimistic launch date'], 'Staged exposure needs a measured condition for advancing or stopping, plus a verified way to disable new work.'),
    ('What is an experiment exposure?', ['A comparable moment when an eligible unit can encounter its assigned variant', 'Any assignment stored in a table', 'Only a treatment-specific click'], 'The exposure point must be equivalent across control and treatment so the measured groups remain comparable.'),
    ('Why inspect sample-ratio mismatch before reading an experiment result?', ['Persistent imbalance may reveal assignment or logging defects', 'It proves the treatment is better', 'It replaces the primary metric'], 'An unexpected allocation can make groups incomparable. The cause should be investigated before interpreting outcome differences.'),
    ('What does GraphQL field nullability control?', ['The response contract and propagation when a field lacks a value', 'Authorization for every record', 'Whether a database index exists'], 'A non-null promise can null a larger parent selection on resolver failure; old data and downstream faults must fit the declared contract.'),
    ('How should a resolver loader cache be scoped for private case data?', ['To the authenticated request and tenant or permission context', 'As one global process cache', 'Only by numeric owner ID across all tenants'], 'Request-local loaders reduce N-plus-one calls without reusing a private result across another actor or tenant.'),
    ('Why must a batch loader restore requested key order?', ['Backend rows can arrive in another order and otherwise attach to wrong parents', 'GraphQL sorts every database result automatically', 'It removes the need for authorization'], 'A batch API returns results aligned to input keys. Reordering and missing-key handling prevent incorrect case-owner associations.'),
    ('Which query budget catches 600 shallow aliases?', ['A breadth or weighted-cost bound in addition to depth', 'Only a maximum depth of four', 'Only an HTTP request-count limit'], 'A shallow document can still perform extensive resolver work. Admission needs document, breadth, list, and cost limits.'),
    ('What does an HTTP success response prove for a GraphQL mutation?', ['Only transport completion; inspect domain result and errors', 'That the write committed', 'That no field-level errors exist'], 'A response can contain data and errors or a typed conflict. The client must inspect the mutation outcome before clearing user input.'),
    ('What prevents equal-timestamp events from disappearing between cursor pages?', ['An immutable tie-breaker in the sort and cursor', 'A timestamp-only cursor', 'An unbounded list'], 'Stable keyset pagination needs a total order. Event time plus a unique ID distinguishes records with identical timestamps.'),
]

quiz_path = 'quizzes/web-development-release-graphql-decisions'
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path['quizzes/web-development-operations-sync-decisions'])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + quiz_path)), path=quiz_path, title='Web Development: release and GraphQL decisions quiz', summary='Twelve explained decisions about flag scope, experiment evidence, GraphQL work limits, resolvers, and mutations.', sort_order=1215, created_at=stamp, updated_at=stamp, published_at=stamp)

def quiz_item(number, value):
    prompt, options, explanation = value
    shift = number % 3
    return {'prompt':prompt,'options':options[shift:] + options[:shift], 'answer':(0 - shift) % 3, 'explanation':explanation}

quiz['data'] = {'subject_root':'web-tech/web-technology','section_path':'web-tech/quizzes','content_format':'html','seo_ready':False,'questions':[quiz_item(number, value) for number, value in enumerate(questions)]}
quiz['body'] = p(quiz['summary'] + ' Choose one answer, inspect the explanation, and revisit the related decision boundary.')
quiz['body'] += '<h2>Related lessons</h2><p>' + '; '.join(link(path) for project in projects for path in project['related']) + '.</p>'
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path['web-tech/web-technology/project']
project_hub['data']['modules'][0]['lessons'].extend(project['path'] for project in projects)
project_hub['body'] += '<h2>Release and GraphQL projects</h2><ul>' + ''.join('<li>' + link(project['path']) + ' — ' + html.escape(project['summary']) + '</li>' for project in projects) + '</ul>'
project_hub['summary'] = 'Build and verify thirty-nine projects across browser, API, data, identity, search, quality, rendering, forms, navigation, delivery, streaming, accessibility, operations, synchronization, authorization, privacy, offline, live, capability, viewport, content, notification, passkey, checkout, private files, email, feature release, and GraphQL contracts.'
project_hub['updated_at'] = stamp
quiz_hub = by_path['web-tech/quizzes']
quiz_hub['data']['modules'][0]['lessons'].append(quiz_path)
quiz_hub['body'] += '<h2>Release and GraphQL checks</h2><p>' + link(quiz_path) + ' — ' + html.escape(quiz['summary']) + '</p>'
quiz_hub['updated_at'] = stamp
for hub_path, project_path in [('web-tech/feature-release-and-experiment-controls', projects[0]['path']), ('web-tech/graphql-query-and-resolver-boundaries', projects[1]['path'])]:
    hub = by_path[hub_path]
    hub['body'] += '<h2>Practice path</h2><p>Build ' + link(project_path) + ' and check decisions in ' + link(quiz_path) + '.</p>'
    hub['updated_at'] = stamp
for entry in entries:
    if entry['type'] != 'article' or entry['data'].get('section_path') not in {'web-tech/feature-release-and-experiment-controls','web-tech/graphql-query-and-resolver-boundaries'}:
        continue
    project_path = projects[0]['path'] if entry['data']['section_path'] == 'web-tech/feature-release-and-experiment-controls' else projects[1]['path']
    entry['body'] += '<h2>Apply and check</h2><p>Build ' + link(project_path) + ' and review ' + link(quiz_path) + '.</p>'
    entry['data']['related'].extend([project_path, quiz_path])
    entry['updated_at'] = stamp
root_entry = by_path['web-tech/web-technology']
root_entry['body'] += '<h2>Release and GraphQL practice</h2><p>Apply the rollout and query contracts with ' + link(projects[0]['path']) + ' and ' + link(projects[1]['path']) + '.</p>'
root_entry['updated_at'] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_projects':len(projects),'new_quizzes':1,'new_questions':len(questions)}))
