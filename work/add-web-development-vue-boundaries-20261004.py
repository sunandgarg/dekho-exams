"""Add original Vue application-state and rendering lessons."""
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


def p(value):
    return "<p>" + html.escape(value) + "</p>"


def link(path):
    assert path in by_path, path
    return '<a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a>"


hub_path = "web-tech/vue-reactivity-and-component-boundaries"
hub_title = "Vue Reactivity and Component Boundaries"
topics = [
    dict(
        slug="vue-source-state-computed-views-and-large-snapshots",
        title="Vue Source State, Computed Views, and Large Snapshots",
        summary="Keep one reactive source of truth, derive views with computed values, and bound large immutable data costs.",
        concept="A Vue ref or reactive object represents state whose changes can trigger dependent work. A computed value derives a result from the reactive values it reads and caches that result until those dependencies change. This makes it a good home for a filtered queue or count, but not for an asynchronous request or an impure mutation. Storing source cases, filtered cases, and count as three independently writable values creates a synchronization problem that the framework cannot solve automatically. Reactivity also has a cost. Deeply tracking every property of a very large, immutable server snapshot adds proxy work that may bring no benefit if updates always replace the whole snapshot. The choice is not between reactive and nonreactive everything; it is to make each ownership and update boundary explicit.",
        case="A permit dashboard receives a 47,000-case search snapshot. Its component keeps a mutable array, a second filtered array, and a separate count. A watcher copies the filtered data after each phrase change, and a later watcher updates the count. The UI occasionally displays 62 visible cases beside 81 rows when a replacement snapshot arrives between the two updates. The team retains one server snapshot and one search phrase, then derives filtered cases and count from the same computed result. Because the snapshot is replaced as a unit, the team evaluates shallow storage for the large immutable collection; they do not silently mutate one nested case in place and expect that shallow storage to report it.",
        implementation="Inventory which values are authoritative: the server snapshot, phrase, selected case ID, and pending operation. Put the source values in refs and compute filtered rows from snapshot plus phrase. Compute count from those rows rather than running a second filter. Keep the computed getter pure: no network request, log submission, or state write. If a snapshot contains tens of thousands of immutable objects and every update replaces it, a shallow ref can avoid deep conversion overhead. That choice requires immutable replacement when a record changes; document it in the data layer and test it. If individual nested fields are edited in place, a deeply reactive structure may be appropriate, though it has tracking cost. Measure both update frequency and filtering cost before introducing indexes, worker computation, or windowed rendering. A method that reads current reactive state on every render may be fine for cheap work; a computed value is especially useful when the same expensive result has several consumers.",
        cost="Filtering all 47,000 records is O(n) per invalidation and stores a result array of up to O(n) references. Computed caching avoids rerunning when its reactive dependencies stay unchanged; it does not make a changed search phrase free. A shallow ref reduces nested tracking but requires O(n) or targeted structural copying for immutable replacements, depending on the data shape. An index adds memory and maintenance work; a worker adds transfer or sharing costs. A count stored independently uses little memory but risks correctness drift. Measure update-to-visible time, dependency invalidation frequency, and heap retention on a modest device rather than choosing a strategy from row count alone.",
        failure="Replace the server snapshot while a phrase is active and assert rows and count agree in one render. Change a case status through the documented replacement path and verify the computed result updates. Mutate a nested object under shallow storage as a deliberate negative test; the absence of an update should reveal the contract breach. Type a phrase that matches nothing, clear it, and switch to a new snapshot without resetting the input. Profile a 47,000-row update and distinguish filter computation from DOM rendering. Confirm that reading the computed value twice without changed dependencies does not duplicate the filter work.",
        drill="Create 47 permit records first, then expand to 47,000. Keep one server snapshot and one search phrase. Derive visible cases and count, then make two UI consumers read the same computed result. Replace case 62 with a new object and record whether the view changes. Compare a deep ref and a shallow ref using the same immutable replacement flow. Measure filter time and rendered row count separately. State when an index or windowed list becomes necessary, and record the memory overhead of each choice.",
        decision="Store authoritative inputs once; derive views from them, and choose shallow tracking only with immutable replacement discipline.",
        code='import { computed, shallowRef, ref } from "vue";\n\nexport function usePermitSearch(initialCases) {\n  const caseSnapshot = shallowRef(initialCases);\n  const phrase = ref("");\n  const visibleCases = computed(() => {\n    const needle = phrase.value.trim().toLocaleLowerCase();\n    return caseSnapshot.value.filter((permitCase) => permitCase.title.toLocaleLowerCase().includes(needle));\n  });\n  const visibleCount = computed(() => visibleCases.value.length);\n  function replaceSnapshot(nextCases) { caseSnapshot.value = nextCases; }\n  return { phrase, visibleCases, visibleCount, replaceSnapshot };\n}',
        checks=["Visible rows and count derive from one source snapshot.", "A shallow snapshot changes through replacement, not nested mutation.", "Filtering and DOM rendering costs are measured separately."],
        mistakes=["Keeping derived rows and count as separately writable state.", "Doing network work inside a computed getter.", "Mutating a nested record in a shallow ref and expecting notification."],
        related=["web-tech/application-search-and-retrieval", "web-tech/browser-performance-diagnosis-and-measurement"],
    ),
    dict(
        slug="vue-watch-cleanup-and-stale-request-ownership",
        title="Vue Watch Cleanup and Stale Request Ownership",
        summary="Attach each fetch to the watched identity and cancel or reject work when that identity changes.",
        concept="A watcher is useful when a reactive value must synchronize with something outside Vue, such as a network request. It is not needed to copy a computed value into another ref. When a selected case changes, the old fetch may finish after the new one and overwrite the correct detail. The watcher must own both the request and its invalidation cleanup. Aborting an HTTP request is helpful, but it is not an authority check: a response may already be delivered or a downstream operation may continue. A generation guard ensures that only the current selection publishes data. Cleanup should be registered before asynchronous work yields, so a rapid selection change has a cancellation path from the start.",
        case="A reviewer opens case 47, then immediately opens case 81. The first detail request is slow and returns last. Without cleanup, the panel heading says 81 while the body shows case 47's confidential note. The team watches the selected ID, creates one controller and generation for each run, registers cleanup immediately, and clears the old detail while loading the new one. A result may publish only if it still owns the current generation and case ID. The server also checks case-level authorization on each request; no frontend cancellation rule grants access. When the component unmounts, the watcher stops and its active request is cleaned up.",
        implementation="Watch a specific reactive source rather than an entire mutable object whose incidental fields change. In the callback, allocate an AbortController and register the cleanup synchronously using the watch callback's cleanup argument. Increment or capture a generation token before starting the fetch. Mark the detail pending and clear or explicitly label the previous content so the UI cannot misattribute it. After the response and parse, check the current generation and selected ID before assigning the result; treat an abort as cancellation, not as an error banner. Handle HTTP errors and malformed payloads separately, because fetch only rejects for transport failures and cancellation. If requests depend on account identity as well as case ID, watch both and invalidate when either changes. Use a server-owned permission check for private data. Test rapid selection, logout, unmount, and network failures.",
        cost="One watcher creates at most one active request per selection in the ordinary path, but rapid selection can start several requests before abort propagates. A generation counter is O(1) state and comparison; its purpose is correctness, not server work cancellation. Aborting may save bandwidth and browser parsing yet cannot roll back a server-side mutation. Keeping previous detail visible reduces flicker but risks showing the wrong record unless it is clearly labeled. Clearing it avoids ambiguity but creates a loading interval. Measure request count, aborted bytes where available, stale-result rejections, and time to current detail; avoid logging private note content to diagnose a race.",
        failure="Delay case 47 until after case 81 returns and ensure case 47 cannot publish. Switch 47 to 81 to 62 quickly, then unmount; every old request should be invalidated, even if a mock ignores abort. Sign out while case 62 is loading and verify the result cannot enter the next user's view. Return a 403 for one case and a malformed successful body for another; neither should be mistaken for a generic offline failure. Try a response that completes just before cleanup and verify the generation check still reflects the current selection. Confirm that the watcher does not refetch because a presentational field changed.",
        drill="Build a detail loader for selected cases 47, 62, and 81. Script response delays of 620, 81, and 47 milliseconds, then select them in that order. Record start, cleanup, abort, parse, and publication for each generation. State what the panel displays while pending and after 403, transport failure, and sign-out. Run the same sequence with an abort-ignoring transport stub; the final body must still belong to the final selected case. Count duplicate requests caused by watching a broad object rather than just identity fields.",
        decision="A watcher owns external work and its cleanup; the current identity alone may publish a result.",
        code='import { ref, watch } from "vue";\n\nexport function usePermitDetail(selectedCaseId) {\n  const detail = ref(null);\n  const error = ref(null);\n  let generation = 0;\n  watch(selectedCaseId, (caseId, _previous, onCleanup) => {\n    const activeGeneration = ++generation;\n    const controller = new AbortController();\n    onCleanup(() => {\n      controller.abort();\n      if (generation === activeGeneration) generation++;\n    });\n    detail.value = null;\n    error.value = null;\n    if (caseId === null) return;\n    fetch(`/api/permits/${encodeURIComponent(caseId)}`, { signal: controller.signal })\n      .then(async (response) => {\n        if (!response.ok) throw new Error(`Permit detail failed: ${response.status}`);\n        const payload = await response.json();\n        if (!payload || String(payload.id) !== String(caseId)) throw new Error("Unexpected permit detail");\n        return payload;\n      })\n      .then((payload) => { if (activeGeneration === generation && selectedCaseId.value === caseId) detail.value = payload; })\n      .catch((failure) => { if (failure.name !== "AbortError" && activeGeneration === generation) error.value = failure; });\n  }, { immediate: true });\n  return { detail, error };\n}',
        checks=["A stale request cannot publish after selection changes.", "Cleanup is registered before asynchronous work begins.", "HTTP, transport, abort, and invalid-payload failures remain distinct."],
        mistakes=["Using abort as the only stale-result guard.", "Watching broad mutable state and refetching on irrelevant changes.", "Leaving old private detail under a new case heading."],
        related=["web-tech/fetch-status-and-abort", "web-tech/authorization-and-tenant-boundaries"],
    ),
    dict(
        slug="vue-props-emits-and-keyed-editor-ownership",
        title="Vue Props, Emits, and Keyed Editor Ownership",
        summary="Keep parent-owned records immutable to children and make draft lifetime follow a case identity.",
        concept="Props flow from a parent into a child. Vue prevents replacing a prop binding inside the child, but a nested object can still be mutated through its reference unless the application enforces a stronger ownership rule. That hidden mutation makes optimistic edits, rollback, and server reconciliation difficult to reason about. A child should emit a proposed command or value change; the owning parent decides whether and when source state changes. Component keys also define identity during list updates. A row index is unstable under sorting and insertion, and a detail editor that stays mounted for a different case may keep a private draft from the old one. Decide which state belongs to the case, which belongs to the user's session, and which can be discarded.",
        case="A permit card receives a case object as a prop. Its button directly changes case.status to approved before the server answers. When the server rejects, another part of the dashboard still sees the mutated object, but no rollback record exists. A queue sort then inserts case 29 ahead of case 47; index keys reuse editor instances and a private draft appears under the wrong case. The revised card emits an approval request containing the case ID. The parent owns pending, success, and rejection state. Rows use immutable case IDs as keys, and the selected editor key changes with the case ID. If the product must preserve unsent notes, the parent stores them by case ID before the editor remounts.",
        implementation="Declare the child's props and emitted events as part of its public contract. Treat object props as read-only throughout the nested graph even if JavaScript permits mutation. Emit a command with the stable case ID and let the parent create an operation identity, apply a pending state, call the server, and reconcile the authoritative response. For a two-way editable field, use an explicit value/update event contract rather than mutating an object prop. Key queue rows by immutable case ID. Key the smallest editor subtree by selected case ID when switching should reset its local form state. Keep a separate draft map if notes must survive switching, and erase it on submission, account change, or expiry. Test both row reorder and detail switch. Do not generate a fresh random key on every render, which remounts the child unnecessarily.",
        cost="Events make ownership clear but add a parent handler and require an error result path. A pending operation map uses O(p) memory for p active mutations; saved drafts use O(d) for d retained case drafts. Keying a subtree on case change remounts its descendants and can reset focus, subscriptions, and expensive widgets. Keeping every editor alive to avoid remounts retains far more resources. The smallest keyed boundary usually balances the two, but measure it under real form complexity. Immutable case replacement may copy an array or map path, yet that cost buys a reliable before/after state for rollback and tests. Never accept a local visual approval as evidence of a committed server operation.",
        failure="Reject an approval and verify every display returns to the server-owned status. Insert and sort rows while case 47's note is open; the note must not move to case 62. Switch to case 81 and verify the case 47 note is either stored under 47 or discarded by the declared rule. Change an unrelated toolbar label and check that the editor does not reset. Sign out and ensure private draft state is cleared. Fire two approval commands rapidly and inspect the parent's pending gate or idempotency identity. Remove a row while its request is in flight and reject a late result targeted at a different account.",
        drill="Create a parent queue with case IDs 29, 47, 62, and 81. Make a card child display status and emit an approval command without mutating the case object. Put a private note in the selected editor. Insert case 17, reverse sort, switch selection, and trigger a failed approval. Record the owner of every draft and pending operation after each step. Measure whether keying the entire queue or just the editor causes more remount work. State the draft retention period and the logout cleanup rule.",
        decision="Children propose changes; the record owner commits them, and keys follow stable entity identity.",
        code='import { defineComponent, h } from "vue";\n\nexport const PermitCard = defineComponent({\n  props: { permitCase: { type: Object, required: true } },\n  emits: ["approve"],\n  setup(props, { emit }) {\n    return () => h("button", {\n      type: "button",\n      onClick: () => emit("approve", { caseId: props.permitCase.id })\n    }, `Approve ${props.permitCase.title}`);\n  }\n});\n\n// Parent template: <PermitCard v-for="permitCase in cases"\n//   :key="permitCase.id" :permit-case="permitCase"\n//   @approve="handleApprovalRequest" />\n// Editor template: <CaseNoteEditor :key="selectedCaseId"\n//   :case-id="selectedCaseId" />',
        checks=["A child cannot silently commit a nested prop mutation.", "Rows and drafts remain tied to case IDs after reordering.", "A server rejection restores one authoritative status."],
        mistakes=["Mutating a nested object prop because Vue allows the JavaScript assignment.", "Using array positions as keys in a reorderable queue.", "Keying the whole page when only the case editor should reset."],
        related=["web-tech/vue-source-state-computed-views-and-large-snapshots", "web-tech/autosave-draft-recovery-and-conflicts"],
    ),
    dict(
        slug="vue-server-rendering-and-hydration-stability",
        title="Vue Server Rendering and Hydration Stability",
        summary="Keep per-request state isolated and make the first browser render agree with server HTML.",
        concept="Server rendering produces HTML before the browser executes application code. Hydration then associates that HTML with the client component tree. The initial client output must match the server's structure and data. Browser-only values such as local storage, viewport width, random IDs, and local time zones can break that agreement if read during the first render. There is another boundary on the server: module-level mutable state may be shared across requests in a long-running process. A private case selected by one request must not become the next request's default through a singleton ref. Create application state per request, serialize only the permitted initial snapshot, and apply browser-only preferences after mount.",
        case="A permit app exports a module-level selectedCaseId ref. Reviewer 47 requests the server-rendered page, then reviewer 81 arrives on the same server worker. The second HTML response can inherit 47's selected case before its own data loads. The browser then reads a saved filter from local storage while computing the first view, making its count disagree with the server HTML. The corrected server path creates a fresh app and state container for each request, loads only that reviewer's permitted data, and serializes a versioned snapshot. The first browser render uses that snapshot. After mount, a saved display preference changes the view as a separate, visible update. Authorization remains server-owned.",
        implementation="Construct refs, stores, and request caches inside a factory invoked for each server request. Do not put user-specific mutable state in a process-wide module singleton. Fetch and authorize server data before rendering the route, then serialize the minimum snapshot needed for the first client pass with safe HTML escaping. Give the browser the same version and initial values. Keep render-time code free of window and document access because the server has no browser globals. When local storage or viewport data is necessary, read it after mount and handle access failure. Use stable formatting for dates and IDs on both sides; convert to local time as a later enhancement if the server cannot know the user's zone. Validate HTML structure too: browser parser repairs invalid nesting before hydration sees it. Treat mismatch warnings as defects to investigate, even if the framework can recover by discarding nodes.",
        cost="Creating state per request prevents cross-user leakage but adds initialization work and requires careful disposal of request-scoped resources. Snapshot serialization increases response bytes and may expose data if the server includes fields not authorized for the viewer. Post-mount personalization adds a second render and can move content, so keep the initial view useful and the transition clear. Rendering nothing on the server avoids some mismatch cases but loses the value of server HTML on slow networks. Measure response size, server render time, mismatch count, hydration time, and visible shifts. A small saved display preference is not permission to send a large private case object to the browser.",
        failure="Run two simultaneous server requests for different reviewers on the same worker and verify neither response contains the other's selected ID or note. Hydrate in a browser with a different time zone and a saved filter; compare the first browser text with server HTML before the preference applies. Delay JavaScript and confirm that the server output is still useful. Disable local storage access and ensure the page keeps the permitted server snapshot. Insert intentionally invalid nested markup and verify a mismatch check catches browser parser repair. Change the serialized snapshot version and reject incompatible boot data rather than attaching behavior to a different record.",
        drill="Build a per-request app factory with two authorized permit snapshots: one for reviewer 47 and another for reviewer 81. Render them concurrently, then inspect the resulting HTML and serialized boot data for cross-request state. Hydrate one page with local storage set to show only 29 records, and record the server count, first client count, and post-mount count. Repeat with a different browser time zone and blocked storage. Document which data must match at hydration, which data can arrive later, and which fields must never be serialized for another user.",
        decision="Each server request owns its state; the first client render reuses its permitted snapshot before browser preferences apply.",
        code='import { ref, onMounted } from "vue";\n\n// Call inside setup in a fresh app instance for each server request.\nexport function usePermitPageState(initialSnapshot) {\n  const caseCount = ref(initialSnapshot.caseCount);\n  const selectedCaseId = ref(initialSnapshot.selectedCaseId);\n  function applyBrowserPreference() {\n    try {\n      const savedValue = window.localStorage.getItem("permit-visible-limit");\n      if (savedValue === null) return;\n      const parsedLimit = Number(savedValue);\n      if (Number.isInteger(parsedLimit) && parsedLimit >= 0) {\n        caseCount.value = Math.min(initialSnapshot.caseCount, parsedLimit);\n      }\n    } catch { /* Keep the server snapshot visible. */ }\n  }\n  onMounted(applyBrowserPreference);\n  return { caseCount, selectedCaseId };\n}',
        checks=["Two requests in one server worker cannot share private state.", "Server HTML and first client render use the same authorized snapshot.", "Blocked browser storage does not erase permitted content."],
        mistakes=["Exporting user-specific mutable refs from a server module.", "Reading browser-only values during the first render.", "Treating hydration recovery as proof that mismatched markup is harmless."],
        related=["web-tech/server-rendering-and-client-data-flow", "web-tech/react-hydration-and-stable-first-render"],
    ),
]

assert hub_path not in by_path and len(topics) == 4
hub = copy.deepcopy(by_path["web-tech/production-signals-and-incident-decisions"])
hub.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + hub_path)), path=hub_path, title=hub_title,
           summary="Own reactive sources, cancel stale work, protect component contracts, and preserve server/client agreement.",
           sort_order=3660, created_at=stamp, updated_at=stamp, published_at=stamp)
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
    subprocess.run(["node", "--check", "--input-type=module"], input=topic["code"], text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path["web-tech/trace-context-across-request-and-job"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                 title=topic["title"], summary=topic["summary"], sort_order=3661 + number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    related = [hub_path] + ["web-tech/" + other["slug"] for other in topics if other is not topic] + topic["related"]
    body = p(topic["concept"]) + "<h2>Working case</h2>" + p(topic["case"])
    body += '<h2>Implementation boundary</h2><pre><code class="language-javascript">' + html.escape(topic["code"], quote=False) + "</code></pre>" + p(topic["implementation"])
    body += "<h2>Cost and boundaries</h2>" + p(topic["cost"]) + "<h2>Failure trace</h2>" + p(topic["failure"])
    body += "<h2>Verification</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in topic["checks"]) + "</ul>"
    body += "<h2>Practice drill</h2>" + p(topic["drill"]) + "<h2>Decision note</h2>" + p(topic["decision"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in topic["mistakes"]) + "</ul>"
    entry["body"] = body
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": hub_path, "content_format": "html",
                     "seo_ready": False, "kind": "tutorial", "author_path": "authors/aitrove-editorial",
                     "reading_minutes": 8, "related": related}
    entries.append(entry)
    by_path[path] = entry

for topic in topics:
    entry = by_path["web-tech/" + topic["slug"]]
    entry["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in entry["data"]["related"]) + ".</p>"

hub["data"]["modules"] = [{"title": hub_title, "summary": hub["summary"],
                           "lessons": ["web-tech/" + topic["slug"] for topic in topics]}]
hub["body"] = p("A Vue application can be correct at the component level and still show the wrong case after a request race, an index-key reorder, or a server/client state mismatch. This track ties reactive derivation, watcher cleanup, component ownership, and request-scoped server state into one review queue. Each lesson states the data owner and the event that ends its lifetime.")
hub["body"] += "<h2>Topics in this track</h2><ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
hub["body"] += "<h2>Prerequisite paths</h2><p>" + "; ".join(link(path) for path in ["web-tech/frontend-application-architecture", "web-tech/react-state-and-rendering-boundaries", "web-tech/server-rendering-and-client-data-flow"]) + ".</p>"
curriculum = by_path["web-tech/web-technology"]
curriculum["data"]["modules"].append({"title": hub_title, "summary": hub["summary"], "lessons": [hub_path] + ["web-tech/" + topic["slug"] for topic in topics]})
curriculum["body"] += "<h2>" + link(hub_path) + "</h2>" + p(hub["summary"]) + "<ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
curriculum["updated_at"] = stamp
crosslinks = {
    "web-tech/react-state-and-rendering-boundaries": [hub_path],
    "web-tech/fetch-status-and-abort": ["web-tech/vue-watch-cleanup-and-stale-request-ownership"],
    "web-tech/autosave-draft-recovery-and-conflicts": ["web-tech/vue-props-emits-and-keyed-editor-ownership"],
    "web-tech/server-rendering-and-client-data-flow": ["web-tech/vue-server-rendering-and-hydration-stability"],
    "web-tech/browser-performance-diagnosis-and-measurement": ["web-tech/vue-source-state-computed-views-and-large-snapshots"],
}
for path, targets in crosslinks.items():
    assert path in by_path, path
    by_path[path]["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    by_path[path]["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": 1, "new_lessons": 4, "prose_words": {topic["slug"]: len(re.findall(r"\b[\w'-]+\b", " ".join(str(topic[key]) for key in ("concept", "case", "implementation", "cost", "failure", "drill", "decision", "summary")))) for topic in topics}}))
