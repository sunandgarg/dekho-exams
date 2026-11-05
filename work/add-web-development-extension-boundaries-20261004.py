"""Add original browser-extension engineering lessons to Web Development."""
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

hub_path = 'web-tech/browser-extension-trust-and-lifecycle'
hub_title = 'Browser Extension Trust and Lifecycle'
topics = [
    {
        'slug': 'extension-host-permissions-and-user-invocation',
        'title': 'Extension Host Permissions and User Invocation',
        'summary': 'Give an extension access only to the site and action its user requested.',
        'concept': 'An extension permission is a capability granted by the browser, not a substitute for application authorization. Host access decides where an extension may read or modify pages; API permissions decide which browser services it may use. A narrow action can often start from a user gesture on the active tab, while an always-on feature may require an explicit host grant. Neither permission makes private page data safe to transmit elsewhere. The extension should describe what it reads, what it stores, and what changes when a grant is withdrawn. Its server still authenticates any submitted operation.',
        'case': 'A municipal reviewer installs a helper that extracts the case number from the currently open permit page and opens a local checklist. The first version asks for access to every site at installation, although it only needs the permit portal after the reviewer presses its toolbar control. That scope would allow the extension to inspect unrelated email and banking pages. The revised design requests temporary access to the selected tab for the action and keeps a separately explained optional grant for reviewers who want automatic highlighting on the permit portal. It does not read other tabs, and it does not ship page content to a service by default.',
        'implementation': 'List each browser API and host pattern beside the user task that needs it. Put the smallest required set in the base manifest; declare optional access only for features that can genuinely operate without it. Ask at the moment the task is clear, then handle denial as a normal state with an alternate manual case-ID entry. Check that the active tab is on an allowed origin before injecting a content script. A temporary grant can disappear when the tab changes or permission is revoked, so recheck before each privileged operation. Keep the server-side case access check even if the extension has host permission. Avoid wildcard host patterns for convenience. Version the permission inventory and review it before every release; a new dependency should not silently expand the extension’s data reach.',
        'cost': 'A permissions check is small, but broad host access has a large trust and review cost. Always-on scripts run on more pages, consume memory and CPU, and may read data unrelated to the intended task. An on-demand script pays startup time only when invoked. Optional permission prompts add friction, so measure completed checklists and denials without collecting full visited URLs. Storage of grant preferences is O(H) for H host choices, but the privacy cost depends on which hosts are visible. Track injected page count, failure on unsupported pages, permission revocations, and task completion. A server request adds network latency and must be charged to the signed-in reviewer, not to the presence of an extension.',
        'failure': 'Open a bank page, press the helper control, and require refusal before injection. Deny optional portal access, then complete the checklist through manual case-ID entry. Grant access, open a case, revoke the grant, and repeat the action; no old content script should send new private data. Switch from a permitted portal origin to a lookalike host and require refusal. Sign out of the portal while the browser permission remains; the server must deny a private checklist operation. Update the extension with a new host pattern and inspect the permission warning and review record. Run on a low-memory browser with many tabs and compare idle CPU to the action-only version.',
        'drill': 'Build a case helper for permit case 47. Declare one narrow portal host as optional and use a user-invoked active-tab path for one-time extraction. Model three states: no grant, temporary action grant, and persistent portal grant. Test a valid portal, an impostor hostname, and an unrelated page. Revoke each grant while the tab remains open. Record whether any case text leaves the device and how a reviewer finishes the checklist when a grant is denied.',
        'decision': 'Browser permission bounds where the helper may act; the task and server permission still bound what it may do.',
        'code': "function mayReadActiveCase(action) {\n  return action.userInvoked && action.hostGranted &&\n    action.tabOrigin === 'https://permits.internal.test';\n}\nconsole.log(mayReadActiveCase({ userInvoked: true, hostGranted: true, tabOrigin: 'https://permits.internal.test.evil' }));\n// Output: false",
        'checks': ['Unrelated and lookalike sites do not receive an injection.', 'Denied permission has a usable manual route.', 'Server access is checked independently of host permission.'],
        'mistakes': ['Requesting every host for a one-site feature.', 'Treating a browser grant as a server session.', 'Keeping an injected page active after permission revocation.'],
        'related': ['web-tech/browser-capabilities-and-permission-lifecycle', 'web-tech/authorization-and-tenant-boundaries'],
    },
    {
        'slug': 'content-script-isolation-and-dom-mutation',
        'title': 'Content Script Isolation and DOM Mutation',
        'summary': 'Read page data as untrusted input and keep extension UI stable as the document changes.',
        'concept': 'A content script runs near a web page and can inspect or change its DOM, but its code has a different trust and lifecycle boundary from the page’s own scripts. The page can alter labels, insert deceptive nodes, and reorder elements between reads. An isolated execution world reduces direct JavaScript variable collisions; it does not make page text trustworthy. The script must identify the exact origin and page structure it supports, read only the fields needed for its feature, and place extension UI without taking over the host page’s controls. A page update or single-page navigation can invalidate every selector.',
        'case': 'The case helper highlights overdue inspections on a permit page. A document update renames the visible date label and adds a hidden duplicate input. A broad text query now reads the hidden value and marks the wrong case overdue. Another site has a similar CSS class name, but it is not the permit portal. The extension confines injection to the portal origin, locates the case record through a stable attribute and nearby semantic label, validates the case number and date, then displays its own compact panel. If structure validation fails, it shows an unavailable state and directs the reviewer to the original page instead of guessing.',
        'implementation': 'Treat selectors as an adapter to one page contract, not a universal parser. Validate extracted fields before they enter extension storage or a message. Read text with safe DOM APIs and write extension text through text nodes; do not interpret page-provided markup as extension UI. Namespace injected nodes and make insertion idempotent so route changes or repeated execution do not create duplicate panels. Observe only the container needed for changes, debounce expensive re-reads, and disconnect observers when the tab or route leaves scope. Do not modify the host form’s values or submit on the user’s behalf without a separate explicit action. Keep focus order, labels, and keyboard access intact. Test the real page’s responsive and localization variants; translated labels can break brittle text selectors.',
        'cost': 'A full document scan is O(N) for N DOM nodes, and a mutation observer that reparses the page on every change can become O(N × M) across M mutations. Scope queries to a stable container, cap observed work, and batch changes. Injected panels add DOM and style cost to a page the extension does not own. A tiny adapter can fail after a site release, so monitor extraction failures by adapter version without retaining private page text. Measure time from user action to panel, observer callback count, duplicate insertion rate, and failure by supported page version. The fallback is safer than silently using a stale selector.',
        'failure': 'Insert a hidden duplicate case ID and require the adapter to reject ambiguity. Change the locale, date format, and case card order while the extension is open. Repeat injection three times and confirm one panel remains. Trigger 83 rapid DOM mutations and inspect observer work; it must stay bounded. Add markup that looks like extension instructions and verify it is treated as text. Remove the target container and show a visible unavailable state without altering the host form. Use keyboard only to reach the panel, return to page content, and submit the original form. Move within the site without a full reload and verify observers and old data are cleaned up.',
        'drill': 'Implement one adapter for a case 47 page at revision 29. Extract only the case ID, due date, and status. Require an unambiguous container and typed values. Inject a panel with a stable marker, then simulate two route changes and 83 mutation callbacks. Record the number of reads, panels, and active observers. Replace the case ID node with attacker-written text and prove the helper neither renders HTML nor sends it as an instruction.',
        'decision': 'The host page is a data source the extension does not control; selector failure must stop the derived action.',
        'code': "function validCaseCard(card) {\n  return /^CASE-[0-9]{2,6}$/.test(card.caseId) &&\n    card.matches === 1 && Number.isFinite(Date.parse(card.dueDate));\n}\nconsole.log(validCaseCard({ caseId: 'CASE-47', matches: 2, dueDate: '2026-10-04' }));\n// Output: false",
        'checks': ['Ambiguous and hidden duplicates cannot decide a case.', 'Repeated injection creates one panel.', 'Page strings reach text sinks only.'],
        'mistakes': ['Assuming isolation makes page text trusted.', 'Scanning the whole DOM after every mutation.', 'Changing a host form without a separate user action.'],
        'related': ['web-tech/dom-sinks-and-trusted-content', 'web-tech/browser-execution-and-resource-lifecycle'],
    },
    {
        'slug': 'extension-background-events-and-durable-state',
        'title': 'Extension Background Events and Durable State',
        'summary': 'Persist task state across worker shutdown and browser restart without replaying effects.',
        'concept': 'An extension’s background event handler may be loaded when an event arrives and stopped when idle. In-memory variables are therefore a cache, not a durable queue or source of truth. A popup can close before its request finishes, and a content script can disappear when the tab navigates. A long operation needs a stable ID, persisted state, and an explicit owner for retries. Event listeners should be registered where the runtime can find them after restart. A background timer alone is a poor durability guarantee for an important user task.',
        'case': 'A reviewer selects case 47 and asks the helper to save a checklist. The popup closes as soon as the user clicks outside it; the background handler begins a server call, then the browser suspends it. A naive global variable held the request state, so the next click sends another checklist and the reviewer sees two copies. The revised flow creates operation 63 with a scoped idempotency key, stores pending metadata in extension storage, and lets the server own the authoritative completion state. When the handler wakes again, it reloads the operation ID and reconciles with the server before retrying. A completed operation is shown once in the popup.',
        'implementation': 'Keep background handlers short and event-driven. Persist only the minimum operation metadata needed to recover; private case notes should stay on the authorized server or use an explicit local retention rule. Register listeners at module initialization so a new worker can receive events. Tie a popup command to a server operation key and wait for an acknowledgement that identifies durable admission. When a network call fails ambiguously, query status before deciding whether to retry. Distinguish queued, sending, completed, failed, and canceled states. Do not promise that an alarm, port, or open popup will keep a worker alive indefinitely. Recheck user session and case access before replaying after browser restart. Remove or expire old pending records so storage does not grow without bound.',
        'cost': 'A storage read per event and an indexed status lookup add small latency; they prevent duplicate server effects and lost user state. Stored pending operations take O(P) space for P unfinished tasks until expiry. Polling too often from every popup can create unnecessary server load, so use bounded refresh and pause when hidden. A restart can cause several pending tasks to wake together; limit concurrency and backoff. Measure pending age, duplicate admission, completion after restart, storage size, and user-visible unknown outcomes. Avoid treating a local completed flag as stronger evidence than the server’s operation record.',
        'failure': 'Close the popup immediately after submission and reopen it; the status should still be recoverable. Stop the background handler after server admission but before its response arrives, then retry with the same key and require one checklist. Restart the browser with an operation pending, revoke case permission, and deny replay or result access. Let local storage write fail and show an honest uncertain state rather than claiming success. Trigger the same event twice and confirm one effect. Expire a pending record only after its retry window and reconciliation policy. Inspect whether private note text remains in extension storage after sign-out.',
        'drill': 'Save a checklist for case 47 with operation key review-63. Simulate a popup close at 20 milliseconds and background suspension after the server commits. Reopen the helper, reload pending metadata, and reconcile operation 63. Repeat after account sign-out and browser restart. Record every server operation ID and local state transition. Then create 83 pending tasks and verify bounded status refresh, storage cleanup, and no duplicate checklist rows.',
        'decision': 'Extension memory can vanish between events; durable state and idempotent server operations carry the workflow.',
        'code': "function shouldRetryChecklist(local, server) {\n  return local.key === server.key && server.state === 'not-found' &&\n    local.attempts < 3 && local.sessionCurrent;\n}\nconsole.log(shouldRetryChecklist({ key: 'review-63', attempts: 1, sessionCurrent: true }, { key: 'review-63', state: 'completed' }));\n// Output: false",
        'checks': ['Popup closure cannot lose the operation identity.', 'Ambiguous network failure does not create a duplicate.', 'Restart replay rechecks current session and case access.'],
        'mistakes': ['Holding important state only in a global variable.', 'Retrying a server write with a new key.', 'Assuming an event handler stays alive until work completes.'],
        'related': ['web-tech/background-workflow-reliability', 'web-tech/idempotent-write-requests'],
    },
    {
        'slug': 'extension-message-contracts-and-page-data-boundary',
        'title': 'Extension Message Contracts and Page Data Boundary',
        'summary': 'Validate messages between the page, content script, background worker, and server.',
        'concept': 'A message crossing extension contexts is a request from another trust zone, even if every file ships in one package. A web page can influence DOM values and may send page messages; a content script can ask a more privileged background handler to use browser APIs or network access. The handler must verify sender context, message type, size, shape, and intended operation before acting. The extension should send only the data required for the user’s task. A message ID and response contract help distinguish retries from stale tab messages. A claimed origin or case ID inside the payload is not authority.',
        'case': 'The helper reads case 47 from the permitted portal and asks the background worker to open a checklist. A hostile page creates a similar DOM node and sends a forged message requesting an export of case 63. If the worker accepts any message named openChecklist, it can become a bridge from untrusted page content to private service access. The worker accepts only messages from its own content script on a permitted tab, validates a narrow schema, checks that the tab origin and user action match, and still asks the server to authorize case 47. It never accepts arbitrary URLs or attachment bytes in this message path.',
        'implementation': 'Define a small discriminated message set with version, type, request ID, and bounded fields. Reject unknown types, extra privilege-bearing fields, oversized text, and stale tab identities. Use sender metadata supplied by the extension runtime rather than a caller-written sender field. Keep page-to-content-script communication separate from content-script-to-background communication; the page can influence the former and cannot be allowed to impersonate the latter. Validate the server response again before rendering in the popup. If a message can trigger a side effect, require a user action record or confirmation bound to the exact target. Avoid broad relay functions such as fetchAnyUrl or executeCode. Log outcome category and request ID without copying private page text into a general diagnostic stream.',
        'cost': 'Shape validation is O(B) for B message bytes after a strict maximum size check. Sender and permission checks add constant local work; server authorization adds network cost when required. A long-lived port can reduce setup overhead for repeated updates but must handle disconnect and stale tab state. Sending full page HTML multiplies data exposure and serialization cost, while a small case identifier and revision are cheap. Measure rejected message categories, average payload bytes, stale response count, and task completion. A high rejection count can reveal a broken adapter as well as an attack; inspect enough context to tell the difference without retaining raw private documents.',
        'failure': 'Send an allowed type from an unrelated tab and require denial. Add an unknown field requesting external upload and reject the message. Replay a valid message after the tab changes from case 47 to case 63; the old request ID must not affect the new popup. Close the content script while a background response is pending and avoid writing into a stale view. Supply 4 MiB of page text where 2 KiB is permitted; reject before parsing. Forge a page postMessage with the same type label and ensure it cannot reach privileged actions. Change tenant permission on the server and require denial even if the background handler accepted the local message.',
        'drill': 'Define one versioned message for opening a case checklist. Permit case IDs such as CASE-47, a revision number, and a 96-character request ID; cap the encoded message at 2 KiB. Pass it from a content script on the portal to the worker, then ask the server to authorize it. Test an unrelated tab, a forged page message, a stale tab, an extra destination URL, a 4 MiB payload, and a revoked server session. Record the visible error state for each case and verify no private data was sent to a new destination.',
        'decision': 'Every bridge from page data to extension privilege is a protocol that needs sender checks and server permission.',
        'code': "function validChecklistMessage(message, sender) {\n  return sender.origin === 'https://permits.internal.test' &&\n    message.type === 'open-checklist' && /^CASE-[0-9]{2,6}$/.test(message.caseId) &&\n    Number.isInteger(message.revision) && message.revision >= 0 &&\n    typeof message.requestId === 'string' && message.requestId.length > 0 && message.requestId.length <= 96 &&\n    JSON.stringify(message).length <= 2048 &&\n    Object.keys(message).every(key => ['type', 'caseId', 'revision', 'requestId'].includes(key));\n}\nconsole.log(validChecklistMessage({ type: 'open-checklist', caseId: 'CASE-47', revision: 29, requestId: 'r-63', destination: 'outside' }, { origin: 'https://permits.internal.test' }));\n// Output: false",
        'checks': ['Unrelated and stale senders cannot trigger privileged work.', 'Unexpected destinations and large payloads are rejected.', 'Server authorization remains mandatory.'],
        'mistakes': ['Trusting a sender origin written inside the payload.', 'Offering a generic privileged request relay.', 'Treating a runtime message as permission to read another tenant.'],
        'related': ['web-tech/postmessage-origin-source-schema-and-replay', 'web-tech/embedded-interfaces-and-cross-window-contracts'],
    },
]

assert hub_path not in by_path and len(topics) == 4
hub = copy.deepcopy(by_path['web-tech/production-signals-and-incident-decisions'])
hub.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + hub_path)), path=hub_path,
           title=hub_title, summary='Build browser helpers with narrow host access, safe page adapters, recoverable events, and checked messages.',
           sort_order=3090, created_at=stamp, updated_at=stamp, published_at=stamp)
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
                 title=topic['title'], summary=topic['summary'], sort_order=3091 + number,
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
hub['body'] = p('A browser extension can see and alter pages outside its own origin. That capability makes host grants, page selectors, background events, and messages part of one trust design. This track follows a permit checklist helper from the user gesture to an authorized server operation. It makes denial and site changes ordinary states and keeps a page’s text from becoming extension authority.')
hub['body'] += '<h2>Topics in this track</h2><ul>' + ''.join('<li>' + link('web-tech/' + topic['slug']) + ' — ' + html.escape(topic['summary']) + '</li>' for topic in topics) + '</ul>'
hub['body'] += '<h2>Prerequisite paths</h2><p>' + '; '.join(link(path) for path in ['web-tech/browser-security-and-data-stewardship', 'web-tech/embedded-interfaces-and-cross-window-contracts', 'web-tech/background-workflow-reliability']) + '.</p>'
root_entry = by_path['web-tech/web-technology']
root_entry['data']['modules'].append({'title': hub_title, 'summary': hub['summary'],
                                      'lessons': [hub_path] + ['web-tech/' + topic['slug'] for topic in topics]})
root_entry['body'] += '<h2>' + link(hub_path) + '</h2>' + p(hub['summary']) + '<ul>' + ''.join('<li>' + link('web-tech/' + topic['slug']) + ' — ' + html.escape(topic['summary']) + '</li>' for topic in topics) + '</ul>'
root_entry['updated_at'] = stamp
crosslinks = {
    'web-tech/browser-capabilities-and-permission-lifecycle': [hub_path, 'web-tech/extension-host-permissions-and-user-invocation'],
    'web-tech/dom-sinks-and-trusted-content': ['web-tech/content-script-isolation-and-dom-mutation'],
    'web-tech/background-workflow-reliability': ['web-tech/extension-background-events-and-durable-state'],
    'web-tech/postmessage-origin-source-schema-and-replay': ['web-tech/extension-message-contracts-and-page-data-boundary'],
}
for path, targets in crosslinks.items():
    by_path[path]['body'] += '<h2>Further connections</h2><p>' + '; '.join(link(target) for target in targets) + '.</p>'
    by_path[path]['updated_at'] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_hubs': 1, 'new_lessons': 4, 'prose_words': {
    topic['slug']: len(re.findall(r"\b[\w'-]+\b", ' '.join(str(topic[key]) for key in
        ('concept', 'case', 'implementation', 'cost', 'failure', 'drill', 'decision', 'summary')))) for topic in topics}}))
