"""Add original Svelte and SvelteKit application-boundary lessons."""
import copy
import datetime
import html
import json
import re
import subprocess
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
by_path = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def paragraph(value):
    return "<p>" + html.escape(value) + "</p>"


def link(path):
    assert path in by_path, path
    return '<a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a>"


hub_path = "web-tech/svelte-reactivity-and-server-boundaries"
hub_title = "Svelte Reactivity and Server Boundaries"
topics = [
    dict(
        slug="svelte-runes-source-state-derived-views-and-effect-cleanup",
        title="Svelte Runes: Source State, Derived Views, and Effect Cleanup",
        summary="Keep editable state distinct from derived queue views and reserve effects for external work.",
        concept="Svelte's $state rune declares reactive local state. For arrays and plain objects it can create deep reactive proxies, while $state.raw treats a value as a replaceable unit. The distinction matters when a server snapshot is large: deep tracking permits granular changes, but a read-only snapshot contract may be clearer and cheaper to reason about when each accepted update replaces the array. $derived calculates a read-only result from state it reads. $effect is for work outside that derivation, such as a browser subscription, and can return cleanup. Copying a filtered list and its count through separate effects adds writable states that can temporarily disagree. The case snapshot and search phrase should own the truth; filtered rows and count should be consequences.",
        case="A permit-review queue receives 47,000 authorized summaries. A search input writes its phrase into one variable, an effect copies matching cases into a second variable, and another effect copies the count into a third. A batch arrives between these steps, leaving the heading at 47 while the rows now reflect a new snapshot. The implementation also stores the entire case array in local storage, exposing private titles and causing long synchronous writes. Replacing the chain with one raw snapshot, one phrase, and derived rows makes the visible relationship explicit. A separate browser effect, if needed, stores only a small nonprivate display preference and cleans up any timer it starts.",
        implementation="Choose a state boundary before choosing a rune. A read-only authorized batch can use $state.raw, with immutable replacement when a case changes. A small locally editable form can use deep $state so field edits remain reactive. Compute visible cases from snapshot and phrase; compute the count from those cases. Keep the derivation pure: no network calls, storage writes, or mutation of the batch while filtering. An effect should own only its external subscription or timer and return a cleanup function that runs before replacement and at teardown. If filtering becomes expensive, first measure changed-phrase cost and DOM row count. Server-side paged search, a worker, or a bounded list solves different bottlenecks; none should be added merely because the array is large. Authorization stays with the server snapshot.",
        cost="A linear search across n summaries takes O(n) time per changed phrase and can allocate O(n) references. Derived caching avoids repeated work when its dependencies have not changed; it cannot make the next changed query constant-time. A raw snapshot avoids deep proxy bookkeeping, but nested mutation will not announce an update, so replacement is part of the contract. A deep proxy supports local field edits and has tracking overhead that grows with the edited graph. A search index costs memory and update work. A timer-based effect that saves a preference adds scheduling and cleanup obligations. Measure input delay, filter duration, rendered-row work, and retained memory separately on the same device.",
        failure="Type while a new authorized batch arrives and assert that the rows and heading describe one snapshot. Edit a nested case field inside a raw batch without replacing it; that negative test should show why the boundary forbids the mutation. Replace the batch and confirm the view updates. Block browser storage and verify search still works. Mount and destroy the queue repeatedly while an effect owns a timer, then confirm no timer writes after teardown. Clear the phrase and verify that only authorized cases return. Finally, render just 47 rows from the 47,000 records and compare search work with DOM work before choosing a server query.",
        drill="Begin with 47 summaries and grow to 47,000. Capture filter time, row-render time, and memory. Use one source batch and one phrase, then derive both matching rows and count. Deliberately insert case 81 while a query is active and check agreement. Replace one summary immutably; do not rely on a nested edit of raw state. Add a display-preference effect with a short timer, verify cleanup during rapid typing, and deny storage access. Write down the threshold at which local filtering stops meeting the input-latency budget and specify the server search contract that would replace it.",
        decision="Use raw replacement for server snapshots, deep state for local edits, derived views for calculations, and effects for external synchronization.",
        code='''<script lang="ts">
  type PermitSummary = { id: number; title: string };
  let { initialCases }: { initialCases: PermitSummary[] } = $props();
  let cases = $state.raw<PermitSummary[]>(initialCases);
  let phrase = $state('');
  let visibleCases = $derived(
    cases.filter(permitCase =>
      permitCase.title.toLocaleLowerCase().includes(phrase.trim().toLocaleLowerCase())
    )
  );
  let visibleCount = $derived(visibleCases.length);
  function replaceCase(updated: PermitSummary) {
    cases = cases.map(permitCase => permitCase.id === updated.id ? updated : permitCase);
  }
</script>
<input aria-label="Find permit" value={phrase}
  oninput={(event) => phrase = event.currentTarget.value} />
<p>{visibleCount} permitted cases</p>
<ul>
  {#each visibleCases as permitCase (permitCase.id)}
    <li>{permitCase.title}</li>
  {/each}
</ul>''',
        checks=["Rows and count depend on one authorized batch and phrase.", "Raw snapshot updates replace the declared value.", "A storage failure never changes the permitted result set."],
        mistakes=["Using effects to copy values that can be derived.", "Expecting a nested edit inside $state.raw to trigger a view update.", "Persisting private case records when only a display preference is needed."],
        related=["web-tech/vue-source-state-computed-views-and-large-snapshots", "web-tech/angular-signal-sources-computed-views-and-effect-scope"],
    ),
    dict(
        slug="svelte-props-callbacks-and-keyed-editor-ownership",
        title="Svelte Props, Callbacks, and Keyed Editor Ownership",
        summary="Declare component commands as callbacks and keep private drafts attached to stable records.",
        concept="A Svelte component receives data through $props. In a modern component contract, an ordinary callback prop can carry a child's command back to the owner. That is a different operation from changing an object prop in place. A parent that owns case status must decide when approval becomes pending, when the server result commits, and how a failure restores the prior value. Repeated rows also need stable identity: a keyed each block associates a view with a case ID when sorting, insertion, and removal change positions. The editor's private draft requires a separate lifetime rule. It may be stored by case ID if switching should preserve it, or reset intentionally when the selected case changes.",
        case="Reviewer 47 types a private note under permit 62. A new urgent case is inserted at the top of a list keyed by position, and the note appears beside permit 81 after view reuse. A child card also changes its received case status directly before the server responds. The approval fails, but no parent mutation record can reconcile the card and the summary. The repaired interface keys rows by stable case IDs, passes an onApprove callback that reports intent, and lets the parent own pending status. A draft map indexed by case ID keeps text attached to permit 62 through sorting; sign-out clears the map because those notes cannot belong to another reviewer.",
        implementation="Type the case prop and callback prop so the child cannot quietly invent a different command payload. In the card, invoke onApprove with the stable ID and leave the record untouched. The parent allocates an operation ID, gates rapid duplicate clicks, sends the server request, and applies the returned status or rollback. Use the case ID as the each-block key, never the current row number or a new random value. For drafts that survive selection, put text in an owner-scoped map keyed by case ID. For drafts that should not survive, put the editor beneath a selected-case key boundary and check that focus reset is acceptable. Both choices need cleanup on successful submission, account switch, and expiry. A callback reports a request; it does not certify that a server mutation succeeded.",
        cost="A keyed list can retain the correct row views through reorderings and avoid tearing down every editor. That saves setup work but also preserves local state, so a draft map uses O(d) memory for d retained cases and needs an expiry policy. A pending-operation map uses O(p) for p in-flight approvals. Replacing a case in an array can take O(n) time; an indexed owner store can reduce lookup work but adds synchronization complexity. Keying an editor by selected ID recreates its component on each switch, which may discard unsent text and change focus. Measure those user-visible effects alongside render work, not only raw update time.",
        failure="Start a draft for case 62, insert case 29, reverse sort, and assert the draft still belongs to 62. Filter 62 out and back in. If drafts are retained by ID, the text should return; if the contract discards them, an explicit notice should explain that choice. Reject an approval after the child reports intent and verify every display returns to the authoritative server state. Double click Approve while one operation is pending and inspect the server audit trail for one logical command. Remove a case before a late response arrives and ensure it cannot mutate a different row. Sign out, sign in as another reviewer, and verify the map is empty.",
        drill="Build four permit cards for IDs 29, 47, 62, and 81. Pass a typed onApprove callback to each card and keep status in the queue owner. Insert case 17, sort descending, type a note, and switch the selected case twice. Reject one approval and then return a late response for a removed case. Record which ID owns each draft and pending operation after each step. Compare a keyed list with a deliberately position-keyed list to expose the failure, then keep only the stable-ID version. Finish with a logout cleanup test and a focus check for the editor lifetime you chose.",
        decision="Pass commands upward, keep server-backed state at its owner, and key repeated views by immutable case identity.",
        code='''<script lang="ts">
  type PermitSummary = { id: number; title: string; status: string };
  let { permitCase, onApprove }: {
    permitCase: PermitSummary;
    onApprove: (caseId: number) => void;
  } = $props();
</script>
<p>{permitCase.title}: {permitCase.status}</p>
<button type="button" onclick={() => onApprove(permitCase.id)}>Approve</button>
<!-- Parent: {#each visibleCases as permitCase (permitCase.id)} -->
<!--   <PermitCard {permitCase} onApprove={requestApproval} /> -->
<!-- {/each} -->''',
        checks=["Child reports an ID but never mutates its record prop.", "Row identity survives insertions and sort changes.", "Private drafts and pending operations are removed at logout."],
        mistakes=["Keying a changing list by index.", "Mutating an object prop to simulate a committed approval.", "Retaining a reviewer draft map across account changes."],
        related=["web-tech/react-component-identity-and-keyed-draft-lifetime", "web-tech/angular-component-input-output-and-row-identity"],
    ),
    dict(
        slug="sveltekit-form-actions-validation-and-mutation-replay",
        title="SvelteKit Form Actions, Validation, and Mutation Replay",
        summary="Keep a normal POST form usable without script and bind approval to server-side identity and operation rules.",
        concept="A SvelteKit form action handles a POST on the server. The form can submit without client JavaScript, while enhancement can improve the in-browser interaction without changing the server's authority. Input validation must happen inside the action, even if the browser has required fields. A form value is untrusted text, not proof that the reviewer owns the case. The action needs authenticated identity from the request context, case-level authorization, a mutation command, and a response that distinguishes validation failure from success. Duplicate submissions remain possible: a button may be clicked twice, a response can be lost after commit, or an intermediary may retry. A stable operation ID and server-owned deduplication define the logical write.",
        case="A reviewer approves permit 62. The server commits the approval, but the connection closes before the response reaches the browser. The reviewer resubmits, and a naive action sends two audit notifications. Another user changes the hidden case ID from 62 to 81 and sees a success message because the action trusted the form field. The repaired action validates the ID and operation token, looks up the signed-in reviewer, checks permission for that exact case, and passes a stable operation ID to a service that returns the prior result on replay. The ordinary form still works when scripts are disabled; an enhanced version may show pending feedback while it waits.",
        implementation="Place the approval action in a server-only page module. Parse and bound every form field, including the case ID and operation ID; do not coerce an empty string into a valid zero-like identifier. Obtain reviewer identity from server locals and return an authentication failure when it is absent. The permit service must verify authority and perform the deduplicated write atomically, not accept a client-provided reviewer ID. Return field-level failure data without echoing secrets or private records. Render a POST form with the named action and explicit submit button. If use:enhance is added, preserve normal form behavior and the action's validation result; avoid replacing errors with an optimistic success panel. A lost response is handled by replaying the same operation ID, not manufacturing a new write.",
        cost="Validation and permission checks add server work on every submission. The deduplication record consumes O(m) storage for m retained operations and needs expiry aligned with the retry window and audit requirements. An atomic approval transaction may contend on one case under concurrent reviewers; decide which winner is authoritative and surface a conflict when needed. A progressively enhanced form ships extra client code and can improve pending feedback, yet the plain POST path remains the reliability baseline. A broad automatic retry of non-idempotent writes can multiply notifications or charges. Measure duplicate logical operations, conflict rate, form completion without script, and accessible error recovery.",
        failure="Submit with JavaScript disabled and verify the server returns a clear result. Send an empty case ID, a decimal, a negative value, an overlarge operation token, and a case belonging to another reviewer. Only a well-formed authorized command may reach the mutation service. Commit approval, drop the response, and replay the same operation ID: one status transition and one notification should remain. Use a new operation ID for a second deliberate action and check the server's conflict rule. Double click on a slow connection and inspect both requests. Enable enhancement and verify it does not hide server validation or prevent normal keyboard submission.",
        drill="Create a permit approval form for case 62 with an operation token. Start with the unenhanced POST, then add a pending state if the baseline passes. Write an action that rejects malformed IDs and missing identity, delegates case permission to a server service, and submits the token for atomic deduplication. Build a test service that records committed operation IDs and returns the previous result on replay. Simulate a lost response after commit, a tampered case field, and two reviewers approving concurrently. Record the resulting status, notification count, and user-visible error for each path.",
        decision="The action validates and authorizes each POST; the server service owns atomic mutation and replay semantics.",
        code='''import { fail } from '@sveltejs/kit';
import type { Actions } from './$types';

export const actions: Actions = {
  approve: async ({ request, locals }) => {
    const reviewer = locals.reviewer;
    if (!reviewer) return fail(401, { message: 'Sign in required' });
    const fields = await request.formData();
    const rawCaseId = fields.get('caseId');
    const operationId = fields.get('operationId');
    if (typeof rawCaseId !== 'string' || !/^[1-9]\\d{0,8}$/.test(rawCaseId) ||
        typeof operationId !== 'string' || !/^[a-zA-Z0-9-]{20,80}$/.test(operationId)) {
      return fail(400, { message: 'Invalid approval request' });
    }
    const result = await locals.permits.approve({
      reviewerId: reviewer.id, caseId: Number(rawCaseId), operationId
    });
    if (result.kind === 'forbidden') return fail(403, { message: 'Access denied' });
    if (result.kind === 'conflict') return fail(409, { message: 'Case changed' });
    return { approvedCaseId: result.caseId };
  }
};''',
        checks=["Unenhanced POST remains usable and reports field errors.", "The action uses server identity and case-level permission.", "A replayed operation ID produces one logical approval."],
        mistakes=["Treating a hidden case ID as authorization.", "Retrying a committed write with a fresh operation ID.", "Letting enhancement bypass the normal server validation path."],
        related=["web-tech/api-mutation-and-failure-contracts", "web-tech/checkout-and-payment-state"],
    ),
    dict(
        slug="sveltekit-request-scoped-load-and-hydration-state",
        title="SvelteKit Request-Scoped Load and Hydration State",
        summary="Pass authorized server data through a request-owned load result and preserve a stable first browser view.",
        concept="A SvelteKit server load function runs for a request and can access server-only identity and data services. It returns serializable data to the page; that result enters HTML or client navigation payloads, so it must contain only information the viewer may receive. A long-running server process also holds module variables between requests. A mutable module-level current reviewer or case list is therefore unsafe for user-specific state. Component instances receive page data through props. Server-rendered markup and the browser's first render need compatible structure and initial values for hydration. Browser storage, viewport size, or local time can legitimately change the later view, but reading them during the first render can produce a mismatch and discard useful server work.",
        case="Reviewer 47 opens a permit queue whose server load returns 47 summaries. A module-level array retains that list. Reviewer 81 arrives on the same worker and sees one of 47's private case titles in the response. Separately, the browser reads a saved 29-row limit before hydration while the server sent 47 rows, so the initial trees disagree. The repair puts permission lookup and list retrieval inside each request's load function, returns only that viewer's allowed summaries, and leaves local display preferences until after the browser has taken over. The first browser view uses the serialized authorized batch and deterministic formatting; a later preference update may narrow it.",
        implementation="Read identity from the request's server context, enforce the permission boundary before fetching summaries, and return only the fields the page needs. Do not write user data to a module-level let, singleton cache keyed only by URL, or shared reactive store. Treat a load result as a response payload, even if a property feels internal. Keep date and number formatting stable between server and first browser render or pass preformatted display strings with a clear locale contract. On the page, take data from props and initialize source state from it. Apply local storage after mount and handle storage denial. If a background refresh arrives, compare account and request generation before replacing private data. Run two simultaneous requests through one worker, inspect both HTML and data payloads, then check the first browser tree under different local settings.",
        cost="Request-scoped fetch and authorization use server CPU and database work per viewer. A shared cache can reduce that cost only when its key and invalidation model include the full visibility boundary; a URL-only key cannot represent reviewer permissions. Serializing 47,000 cases increases HTML or navigation bytes, so return a bounded first page and a cursor for more. Hydration can save DOM reconstruction, but a browser-only branch that changes initial markup may force recovery and shift focus. A post-mount preference update can also move rows; keep the change predictable and test it with keyboard and assistive technology. Measure response size, duplicate fetches, hydration warnings, and cross-user isolation together.",
        failure="Render reviewers 47 and 81 concurrently on one process and scan each response for the other's private IDs. Change the browser's stored limit to 29 and time zone to another region; the first render must still match the server's 47-row response, with personalization after mount. Disable JavaScript and confirm the authorized server page remains readable. Simulate an expired session during a client refresh, then verify old data disappears rather than being copied into a new account's state. Poison a shared URL cache in a test and assert permission prevents its use. Delay a previous account's fetch until after sign-out and reject its result.",
        drill="Build a request-scoped load for a permit queue with two reviewers whose permitted case sets do not overlap. Return a bounded first page, count, and cursor, then render it with deterministic labels. Send concurrent requests through one server worker and compare their serialized payloads. On the client, set a browser-only row limit after mount and record the initial DOM and later personalized DOM separately. Test storage denial, different time zones, sign-out during refresh, and a late previous-account response. Decide whether any cache can be shared; document the identity and permission key it would require.",
        decision="Keep authorization and private data inside each request; hydrate from the same permitted payload before applying browser preferences.",
        code='''import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals }) => {
  const reviewer = locals.reviewer;
  if (!reviewer) error(401, 'Sign in required');
  const firstPage = await locals.permits.listAuthorized({
    reviewerId: reviewer.id, limit: 47
  });
  return {
    caseSummaries: firstPage.cases.map(permitCase => ({
      id: permitCase.id, title: permitCase.title, status: permitCase.status
    })),
    nextCursor: firstPage.nextCursor
  };
};''',
        checks=["Concurrent responses contain only each reviewer's permitted case IDs.", "The first browser tree matches the server's serialized page.", "Account changes reject late private responses and clear local drafts."],
        mistakes=["Keeping a mutable current reviewer in module scope.", "Sending private service objects in a load result.", "Reading browser storage before the first hydrated render."],
        related=["web-tech/server-rendering-and-client-data-flow", "web-tech/angular-ssr-hydration-and-private-transfer-state"],
    ),
]

assert hub_path not in by_path and len(topics) == 4
hub = copy.deepcopy(by_path["web-tech/production-signals-and-incident-decisions"])
hub.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + hub_path)), path=hub_path,
           title=hub_title,
           summary="Use Svelte runes, stable component identity, server form actions, and request-owned page data.",
           sort_order=3680, created_at=stamp, updated_at=stamp, published_at=stamp)
hub["data"] = {"subject_root": "web-tech/web-technology", "section_path": hub_path,
               "content_format": "html", "seo_ready": False, "modules": [],
               "resource_tabs": [{"title": "Web Development", "path": "web-tech/web-technology"},
                                 {"title": "Projects", "path": "web-tech/web-technology/project"},
                                 {"title": "Quizzes", "path": "web-tech/quizzes"}]}
entries.append(hub)
by_path[hub_path] = hub

for number, topic in enumerate(topics):
    path = "web-tech/" + topic["slug"]
    assert path not in by_path
    code = topic["code"]
    script = re.search(r'<script lang="ts">(.*?)</script>', code, re.S)
    parsed = script.group(1) if script else code
    subprocess.run([str(root / "node_modules/.bin/esbuild"), "--loader=ts", "--format=esm"],
                   input=parsed, text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path["web-tech/trace-context-across-request-and-job"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                 title=topic["title"], summary=topic["summary"], sort_order=3681 + number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    related = [hub_path] + ["web-tech/" + other["slug"] for other in topics if other is not topic] + topic["related"]
    language = "svelte" if script else "typescript"
    body = paragraph(topic["concept"]) + "<h2>Working case</h2>" + paragraph(topic["case"])
    body += '<h2>Implementation boundary</h2><pre><code class="language-' + language + '">' + html.escape(code, quote=False) + "</code></pre>" + paragraph(topic["implementation"])
    body += "<h2>Cost and boundaries</h2>" + paragraph(topic["cost"]) + "<h2>Failure trace</h2>" + paragraph(topic["failure"])
    body += "<h2>Verification</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in topic["checks"]) + "</ul>"
    body += "<h2>Practice drill</h2>" + paragraph(topic["drill"]) + "<h2>Decision note</h2>" + paragraph(topic["decision"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in topic["mistakes"]) + "</ul>"
    entry["body"] = body
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": hub_path,
                     "content_format": "html", "seo_ready": False, "kind": "tutorial",
                     "author_path": "authors/aitrove-editorial", "reading_minutes": 8, "related": related}
    entries.append(entry)
    by_path[path] = entry

for topic in topics:
    entry = by_path["web-tech/" + topic["slug"]]
    entry["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in entry["data"]["related"]) + ".</p>"

hub["data"]["modules"] = [{"title": hub_title, "summary": hub["summary"],
                           "lessons": ["web-tech/" + topic["slug"] for topic in topics]}]
hub["body"] = paragraph("A Svelte permit interface crosses four ownership boundaries: source data must produce consistent views, row commands must reach the owner, form writes need server authorization and replay rules, and server page data must remain private to each request. These lessons trace failure through each boundary with one case queue so the contracts can be tested together.")
hub["body"] += "<h2>Topics in this track</h2><ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
hub["body"] += "<h2>Prerequisite paths</h2><p>" + "; ".join(link(path) for path in ["web-tech/frontend-application-architecture", "web-tech/api-mutation-and-failure-contracts", "web-tech/server-rendering-and-client-data-flow"]) + ".</p>"
curriculum = by_path["web-tech/web-technology"]
curriculum["data"]["modules"].append({"title": hub_title, "summary": hub["summary"],
                                       "lessons": [hub_path] + ["web-tech/" + topic["slug"] for topic in topics]})
curriculum["body"] += "<h2>" + link(hub_path) + "</h2>" + paragraph(hub["summary"]) + "<ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
curriculum["updated_at"] = stamp
crosslinks = {
    "web-tech/react-state-and-rendering-boundaries": [hub_path],
    "web-tech/vue-reactivity-and-component-boundaries": [hub_path],
    "web-tech/angular-signals-and-delivery-boundaries": [hub_path],
    "web-tech/api-mutation-and-failure-contracts": ["web-tech/sveltekit-form-actions-validation-and-mutation-replay"],
    "web-tech/server-rendering-and-client-data-flow": ["web-tech/sveltekit-request-scoped-load-and-hydration-state"],
}
for path, targets in crosslinks.items():
    by_path[path]["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    by_path[path]["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": 1, "new_lessons": 4,
                  "prose_words": {topic["slug"]: len(re.findall(r"\b[\w'-]+\b", " ".join(str(topic[key]) for key in ("concept", "case", "implementation", "cost", "failure", "drill", "decision", "summary")))) for topic in topics}}))
