"""Add Angular application boundaries as original Web Development lessons."""
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


hub_path = "web-tech/angular-signals-and-delivery-boundaries"
hub_title = "Angular Signals and Delivery Boundaries"
topics = [
    dict(
        slug="angular-signal-sources-computed-views-and-effect-scope",
        title="Angular Signal Sources, Computed Views, and Effect Scope",
        summary="Derive queue views from source signals and reserve effects for external systems with cleanup.",
        concept="An Angular writable signal represents application state that a component can update. A computed signal reads source signals and produces a cached, read-only result; when its dependencies change, Angular invalidates the result and calculates it on the next read. An effect also tracks signal reads, but its job is to synchronize with an external system, not to copy one signal into another. Copying filtered rows and counts through effects introduces intermediate states and can create update loops. Signals can hold objects whose nested contents are still mutable JavaScript values, so a read-only signal reference does not make every field immutable. A reliable design declares which data owns the truth and how new snapshots replace old ones.",
        case="A permit queue has a cases signal, search signal, visibleRows signal, and visibleCount signal. Two effects propagate updates through the chain. When reviewer 47 types while a new batch arrives, one effect updates rows and the second has not yet updated count; a stale summary briefly appears above the list. Another effect writes a browser storage preference on every visible-row change, sending a large private dataset to local storage even though only the phrase should persist. The revised queue stores the authorized case snapshot and phrase as source signals, derives rows and count with computed signals, and uses a narrowly scoped storage effect for the small preference alone after confirming that browser storage is available.",
        implementation="Start with the data contract: an authorized server snapshot, a local phrase, a selected case ID, and pending approvals. Put these in writable signals at their appropriate owner. Derive filtered rows and count from the snapshot and phrase; a computed getter must remain pure and must not send requests, mutate inputs, or write storage. Use immutable snapshot replacement when the server sends changes so a nested mutation cannot bypass the declared update boundary. If storage synchronization is required, create an effect in a valid injection context and register cleanup for any timer or external subscription it starts. Do not use an effect merely to push one signal value into another. For an expensive filter, measure recomputation and rendered rows separately before adding a search index, worker, or view window. Make the server authoritative for permissions; a phrase only narrows an already authorized list.",
        cost="A linear filter over 47,000 cases takes O(n) work when its inputs change and may allocate O(n) references. Computed caching saves repeated reads while dependencies stay stable, but it cannot make every changed phrase cheap. An index consumes memory and maintenance time. A worker can avoid blocking the main thread but adds transfer, cancellation, and sequencing work. Effects have scheduling and lifecycle costs; an effect that repeatedly copies state can cause extra change detection and confusing error traces. Measure input delay, filter duration, count consistency, and allocated result size on a modest device. Prefer a bounded output event over storing the whole permitted case snapshot in browser storage.",
        failure="Type a new phrase during a server snapshot replacement and assert rows and count agree in the same visible state. Read the computed rows twice without changing dependencies and inspect whether filtering ran only once. Replace case 62 with a new record and verify the new status appears; then deliberately mutate a nested object without signal update to expose the ownership rule. Block local storage and verify the queue still works. Mount and destroy the component while an effect owns a timer, then prove cleanup prevents a later write. Clear the phrase and check that only the server-authorized cases return.",
        drill="Begin with 47 permit cases and grow to 47,000. Measure the filter and the DOM render separately. Replace the effect-driven visibleRows and visibleCount with two computed values that depend on the same source snapshot. Save only a small search preference, with a storage failure path. Insert a new permitted case while the reviewer types and record whether count and rows still agree. Add an intentional nested mutation as a negative test, then replace the snapshot correctly. Decide when the measured cost warrants an index or windowed list, including its memory budget.",
        decision="Keep source state writable, derived views computed, and effects restricted to work outside Angular state.",
        code='import { Component, computed, signal } from "@angular/core";\n\ntype PermitSummary = { id: number; title: string };\n\n@Component({\n  selector: "permit-search",\n  standalone: true,\n  template: `<input type="search" aria-label="Find permit"\n    [value]="phrase()" (input)="setPhrase($event)">\n    <p>{{ visibleCount() }} permitted cases</p>`\n})\nexport class PermitSearchComponent {\n  readonly cases = signal<readonly PermitSummary[]>([]);\n  readonly phrase = signal("");\n  readonly visibleCases = computed(() => {\n    const needle = this.phrase().trim().toLocaleLowerCase();\n    return this.cases().filter(permitCase => permitCase.title.toLocaleLowerCase().includes(needle));\n  });\n  readonly visibleCount = computed(() => this.visibleCases().length);\n  setPhrase(event: Event): void {\n    this.phrase.set((event.target as HTMLInputElement).value);\n  }\n}',
        checks=["Rows and count derive from the same source snapshot.", "A computed getter has no external side effect.", "Storage failure does not change authorized content."],
        mistakes=["Copying one signal into another through an effect.", "Mutating nested data without an explicit signal update.", "Persisting a private case snapshot when only a display preference is needed."],
        related=["web-tech/vue-source-state-computed-views-and-large-snapshots", "web-tech/application-search-and-retrieval"],
    ),
    dict(
        slug="angular-component-input-output-and-row-identity",
        title="Angular Component Input, Output, and Row Identity",
        summary="Keep records parent-owned, emit commands from children, and track repeated rows by immutable identity.",
        concept="A component input supplies data from its parent; an output reports an event back to the owner. Those directions are easy to blur when a child receives a mutable object and changes a nested field directly. The user may see an optimistic status that no parent mutation record can undo. In a repeated list, Angular needs a stable tracking expression to associate rendered views with records. An index is stable only if the collection never reorders or inserts ahead of a row. A case ID carries identity across those operations. A private note editor has its own lifetime: its draft can belong to the selected case, survive navigation under that ID, or be intentionally discarded. The view structure must match that decision.",
        case="A reviewer opens case 47 and types an internal note. A new case arrives ahead of it in a queue rendered with position tracking. The editor view is reused at another position, and its input appears next to case 62. A card component also sets permitCase.status to approved before a server response arrives; when approval fails, the list and detail view disagree. The repaired queue tracks rows by case ID, makes the card emit an approval request, and lets the parent own pending state and reconciliation. The note editor reads and writes a draft store indexed by case ID, so switching records cannot give case 81 the text from case 47.",
        implementation="Define a component contract with a required case input and an approval output carrying a stable case ID. The card does not mutate the case object, even if the input type allows nested JavaScript mutation. The parent generates an operation identity, marks the case pending, calls the server, and updates from the authoritative response or restores the previous status on failure. In the queue template, track each case by its immutable ID. Keep draft text in a map whose keys are case IDs if drafts must survive switching, and clear it on submission, logout, or expiry. If drafts should be discarded, create a fresh editor state at selection change and test focus behavior. Avoid keying every row by a random value: that recreates views and loses input on every update. Test an insert, reverse sort, filter, rapid double click, and failed approval.",
        cost="Stable tracking lets Angular reuse the correct row views instead of rebuilding them after every reorder. A draft map uses O(d) memory for d retained drafts and needs privacy-aware cleanup. A pending operation map uses O(p) for p in-flight approvals. Copying an array or replacing one case costs work proportional to the chosen data structure, but it provides a clear before/after state for rollback and verification. Recreating a heavy editor on selection change can reset focus and subscriptions; preserving every editor keeps more memory alive. Measure queue update time and draft retention under realistic case counts, then choose the smallest component lifetime boundary consistent with ownership.",
        failure="Type a note for case 47, insert case 29 at the top, reverse sort, and verify the note still belongs to 47. Switch to case 81 and back, then check the declared preservation rule. Change an unrelated toolbar label and confirm the note does not reset. Reject a case 62 approval and ensure all status displays agree with the server. Click Approve twice rapidly; the parent should apply its pending or idempotency gate. Sign out with private drafts open and check that no draft appears in the next account. Remove a case during an in-flight response and prevent its result from changing another record.",
        drill="Build four row cards and a selected-case editor. Track 29, 47, 62, and 81 by ID and instrument view creation count. Let a card emit approval without changing its input. Insert case 17, sort descending, switch editor selection, and reject one approval. Record every draft owner and pending operation after each step. Compare stable-ID tracking with position tracking under the same sequence. Choose a draft expiry rule and prove account switch clears private text. Measure view churn and focus changes alongside correctness.",
        decision="The parent owns case state and commits commands; a row's tracking identity is its stable case ID.",
        code='import { Component, input, output } from "@angular/core";\n\ntype PermitSummary = { id: number; title: string; status: string };\n\n@Component({\n  selector: "permit-card",\n  standalone: true,\n  template: `<p>{{ permitCase().title }}: {{ permitCase().status }}</p>\n    <button type="button" (click)="requestApproval()">Approve</button>`\n})\nexport class PermitCardComponent {\n  readonly permitCase = input.required<PermitSummary>();\n  readonly approvalRequested = output<{ caseId: number }>();\n  requestApproval(): void {\n    this.approvalRequested.emit({ caseId: this.permitCase().id });\n  }\n}\n\n// Parent template: @for (permitCase of cases(); track permitCase.id) {\n//   <permit-card [permitCase]="permitCase"\n//     (approvalRequested)="approve($event.caseId)" />\n// }',
        checks=["Approval is emitted without child mutation of a record input.", "A reordered row retains its case identity and draft owner.", "A failed mutation restores one authoritative status."],
        mistakes=["Tracking a changing queue by position.", "Changing a nested input object inside the child.", "Using fresh random tracking values on each render."],
        related=["web-tech/react-component-identity-and-keyed-draft-lifetime", "web-tech/vue-props-emits-and-keyed-editor-ownership"],
    ),
    dict(
        slug="angular-httpclient-streams-and-stale-detail-requests",
        title="Angular HttpClient Streams and Stale Detail Requests",
        summary="Switch detail reads with selection identity and keep mutation retries out of a broad interceptor.",
        concept="Angular HttpClient returns an observable describing a request. A subscription starts the request; separate subscriptions to a cold HTTP observable can cause separate backend calls. When selected case IDs form a stream, a newer selection should replace the previous detail read. A switching operator can unsubscribe the prior inner request and subscribe to the current one. That is useful for read-only detail loading, not a general retry or cancellation rule for writes. Unsubscribing can stop client work, yet an upstream server may already have processed a request. Mutation idempotency and authorization still belong to server-owned contracts. The UI must also distinguish pending, missing, forbidden, transport failure, and stale response.",
        case="A permit detail panel opens case 47, then case 81 while the first request is slow. Two independent subscriptions race; case 47 returns last and overwrites the case 81 panel. A global interceptor retries every failed request, including approval POSTs; after an approval commits but its response is lost, a retry creates another notification. The revised detail loader switches reads by selected ID and emits a pending state for the active selection. The approval path uses a stable operation ID and a server-owned deduplication result. The interceptor applies only rules that are safe for its route class, not a blanket mutation replay. The server checks case-level permission on every detail and approval call.",
        implementation="Create one selected-ID stream and map it to a typed detail request. Use a switching operator so selection change unsubscribes the previous read; handle null selection without a network call. Put pending, success, and error into a state tagged with the selected ID, so old content is never shown beneath a new heading. Validate the response ID because a TypeScript generic on HttpClient is a compile-time promise, not a runtime parser. Treat 403 as permission failure, 404 as absence when appropriate, and network failure as a retryable transport condition only if the user action allows it. Share a subscribed result deliberately if several UI consumers need it, rather than accidentally issuing duplicate HTTP requests. Keep approval POSTs outside generic read retry logic. Give each mutation an operation identity and let the server return the previous result on replay. Test sign-out, route change, rapid selection, and lost responses.",
        cost="A switching read can save browser work, but rapid selections may still start several requests before cancellation reaches the network. Sharing one result reduces duplicate calls but needs explicit cache lifetime and account scope. State tagging adds a small object per transition and prevents private content confusion. Validation costs work proportional to payload size; it is essential when trust crosses the network. An interceptor may centralize deadlines and authentication yet can hide retries and amplify an incident if it treats writes like reads. Measure backend request count, canceled bytes, stale publish attempts, and the full user task. A low client error rate cannot prove exactly-once mutation effects.",
        failure="Select 47 then 81, return 81 first, and make a mock transport ignore unsubscribe for 47; the view still must not publish case 47 beneath case 81. Subscribe to the same HttpClient observable twice and confirm two backend calls unless sharing was deliberate. Return a 403, a 404, malformed JSON with a wrong case ID, and a transport error; each must map to the correct state. Commit an approval, drop its response, and verify a broad interceptor does not blindly replay it as a new write. Sign out during loading and ensure the old private response cannot enter another account's view.",
        drill="Build a detail stream for IDs 47, 62, and 81. Use delays of 620, 81, and 47 milliseconds and select the IDs quickly. Record request start, unsubscribe, response, and visible case ID. Add a second subscriber and count network calls before deciding where a shared observable belongs. Give the approval POST a stable operation ID and simulate a lost response after commit. Compare the server audit events before and after a deliberate retry. Write an error table for 403, 404, invalid payload, abort, and offline transport.",
        decision="Switch read requests with selection; classify write retries through an explicit server idempotency contract.",
        code='import { Injectable, inject } from "@angular/core";\nimport { HttpClient, HttpErrorResponse } from "@angular/common/http";\nimport { Observable, of } from "rxjs";\nimport { catchError, map, startWith, switchMap } from "rxjs/operators";\n\ntype PermitDetail = { id: number; title: string };\ntype DetailState =\n  | { kind: "idle" }\n  | { kind: "loading"; caseId: number }\n  | { kind: "ready"; caseId: number; detail: PermitDetail }\n  | { kind: "error"; caseId: number; status: number };\n\n@Injectable()\nexport class PermitDetailReader {\n  private readonly http = inject(HttpClient);\n  forSelection(selectedCaseId$: Observable<number | null>): Observable<DetailState> {\n    return selectedCaseId$.pipe(switchMap(caseId => {\n      if (caseId === null) return of({ kind: "idle" } as DetailState);\n      return this.http.get<PermitDetail>(`/api/permits/${caseId}`).pipe(\n        map(detail => {\n          if (!detail || detail.id !== caseId || typeof detail.title !== "string") {\n            throw new Error("Invalid permit detail");\n          }\n          return { kind: "ready", caseId, detail } as DetailState;\n        }),\n        catchError(error => of({\n          kind: "error", caseId,\n          status: error instanceof HttpErrorResponse ? error.status : 0\n        } as DetailState)),\n        startWith({ kind: "loading", caseId } as DetailState)\n      );\n    }));\n  }\n}',
        checks=["Only the currently selected case can appear in detail state.", "Separate subscriptions do not accidentally duplicate backend reads.", "Approval mutations are not retried by a generic read policy."],
        mistakes=["Treating an HttpClient type argument as runtime validation.", "Using a broad interceptor to retry every failed POST.", "Leaving old private detail under a new selection while loading."],
        related=["web-tech/request-deadlines-retries-and-backoff", "web-tech/vue-watch-cleanup-and-stale-request-ownership"],
    ),
    dict(
        slug="angular-ssr-hydration-and-private-transfer-state",
        title="Angular SSR Hydration and Private Transfer State",
        summary="Preserve server/client DOM agreement while isolating user-specific data and transfer caches.",
        concept="Server rendering sends HTML before the browser application starts. Hydration attempts to reuse that DOM by matching the client's first component tree to the server's structure. A browser-only branch, direct DOM mutation, invalid HTML nesting, or different initial data can break the match. A server-rendered app also needs request-scoped user data: sharing a mutable singleton or caching private responses across accounts can leak another reviewer's case. Transfer of previously fetched data can prevent an immediate duplicate request after hydration, but it must not include forbidden records or cross account boundaries. The first-render contract covers markup, data, and cache scope together.",
        case="The server renders a permit queue with 47 authorized cases. The browser reads a local display limit during initial component evaluation and renders 29, so hydration sees different rows. A legacy chart directive adds an extra DOM node before hydration, changing the expected structure. Meanwhile a shared server cache keeps a prior reviewer's selected case under a URL-only key. The repair uses a per-request authorized snapshot, defers the local limit until the browser has attached to the server DOM, and moves chart manipulation to a lifecycle point that cannot alter hydration's expected tree. Private transfer data is either excluded or keyed and cleared within the exact account and request boundary. The first browser view shows the same permitted 47 cases before personalization narrows it.",
        implementation="Create server-side application state for each request and resolve the viewer's permission before rendering private data. Keep the initial component tree deterministic: identical case snapshot, stable IDs, consistent formatting, and valid HTML structure on server and client. Do not read window, local storage, or viewport state during server evaluation. Apply browser-only preferences after hydration and explain the visible update. Audit direct DOM writes from chart libraries and custom directives; isolate them behind a safe lifecycle or a client-only boundary when required. Inspect the framework's transfer-cache policy for requests with credentials and private response headers. A cache key based only on a path is insufficient for per-user case data. Never solve a private-data mismatch by serializing extra cases to every visitor. Compare the initial HTML, first browser tree, and later personalized tree separately.",
        cost="Hydration saves DOM reconstruction work but requires agreement that can be harder with browser-dependent widgets. A client-only chart avoids a mismatch but delays that chart until scripts run. An authorized transfer snapshot increases response size and private-data exposure if its scope is wrong; excluding it may cause a repeat fetch. Request-scoped state uses initialization CPU and memory but prevents cross-user leakage. A post-hydration preference update can move rows and focus, so test its effect on usability. Measure server time, HTML bytes, hydration errors, duplicate requests, and layout changes under slow script loading. A quiet console is insufficient if forbidden data entered the transfer payload.",
        failure="Render two reviewers on the same server worker and inspect both HTML and transferred data for cross-request case IDs. Hydrate with a browser display limit of 29 while the server sent 47; first output must match, then the preference may apply. Disable scripts and verify the server HTML still communicates the permitted queue. Insert an extra DOM node through a chart directive before hydration and confirm the regression check catches it. Use a different browser time zone for a displayed date and check stable first formatting. Return a private response marked noncacheable and ensure no shared transfer cache serves it to another account.",
        drill="Make two authorized snapshots for reviewers 47 and 81. Render both concurrently, then search their HTML and boot payloads for the other's private case ID. Compare the server DOM with the first browser DOM under a stored row limit and a different time zone. Delay JavaScript, then activate a browser-only chart and record whether it causes a structural mismatch. Audit one HttpClient transfer-cache path for credentials, response cache policy, and account scope. Decide whether it should be transferred, refetched after hydration, or rendered as a neutral shell.",
        decision="Hydrate the same authorized tree the server sent; private transfer data must stay inside the viewer's request boundary.",
        code='import { Component, afterNextRender, computed, input, signal } from "@angular/core";\n\ntype PermitSnapshot = { caseCount: number };\n\n@Component({\n  selector: "permit-queue-header",\n  standalone: true,\n  template: `<p>{{ visibleCount() }} permitted cases</p>`\n})\nexport class PermitQueueHeaderComponent {\n  readonly snapshot = input.required<PermitSnapshot>();\n  private readonly savedLimit = signal<number | null>(null);\n  readonly visibleCount = computed(() => {\n    const count = this.snapshot().caseCount;\n    const limit = this.savedLimit();\n    return limit === null ? count : Math.min(count, limit);\n  });\n  constructor() {\n    afterNextRender(() => {\n      try {\n        const stored = window.localStorage.getItem("permit-visible-limit");\n        if (stored === null) return;\n        const limit = Number(stored);\n        if (Number.isInteger(limit) && limit >= 0) this.savedLimit.set(limit);\n      } catch { /* Retain the authorized server count. */ }\n    });\n  }\n}',
        checks=["Server HTML and initial browser tree use the same permitted snapshot.", "Two server requests never share private case state or transfer data.", "Browser-only code cannot mutate the DOM before hydration matches it."],
        mistakes=["Reading local storage during initial server/client render.", "Sharing a URL-keyed private transfer cache across accounts.", "Calling hydration recovery a substitute for fixing a structural mismatch."],
        related=["web-tech/react-hydration-and-stable-first-render", "web-tech/vue-server-rendering-and-hydration-stability"],
    ),
]

assert hub_path not in by_path and len(topics) == 4
hub = copy.deepcopy(by_path["web-tech/production-signals-and-incident-decisions"])
hub.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + hub_path)), path=hub_path, title=hub_title,
           summary="Use signal state, stable component identity, safe HTTP streams, and request-scoped hydration contracts.",
           sort_order=3670, created_at=stamp, updated_at=stamp, published_at=stamp)
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
    subprocess.run([str(root / "node_modules/.bin/esbuild"), "--loader=ts", "--format=esm"],
                   input=topic["code"], text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path["web-tech/trace-context-across-request-and-job"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                 title=topic["title"], summary=topic["summary"], sort_order=3671 + number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    related = [hub_path] + ["web-tech/" + other["slug"] for other in topics if other is not topic] + topic["related"]
    body = p(topic["concept"]) + "<h2>Working case</h2>" + p(topic["case"])
    body += '<h2>Implementation boundary</h2><pre><code class="language-typescript">' + html.escape(topic["code"], quote=False) + "</code></pre>" + p(topic["implementation"])
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
hub["body"] = p("An Angular permit queue crosses four boundaries: derived signals must agree, cards must not commit parent records, selected-case reads must not publish stale detail, and server HTML must match a private first browser view. The lessons make each owner and failure visible so a correct-looking interface cannot hide duplicate writes or cross-user state.")
hub["body"] += "<h2>Topics in this track</h2><ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
hub["body"] += "<h2>Prerequisite paths</h2><p>" + "; ".join(link(path) for path in ["web-tech/frontend-application-architecture", "web-tech/api-mutation-and-failure-contracts", "web-tech/server-rendering-and-client-data-flow"]) + ".</p>"
curriculum = by_path["web-tech/web-technology"]
curriculum["data"]["modules"].append({"title": hub_title, "summary": hub["summary"], "lessons": [hub_path] + ["web-tech/" + topic["slug"] for topic in topics]})
curriculum["body"] += "<h2>" + link(hub_path) + "</h2>" + p(hub["summary"]) + "<ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
curriculum["updated_at"] = stamp
crosslinks = {
    "web-tech/react-state-and-rendering-boundaries": [hub_path],
    "web-tech/vue-reactivity-and-component-boundaries": [hub_path],
    "web-tech/request-deadlines-retries-and-backoff": ["web-tech/angular-httpclient-streams-and-stale-detail-requests"],
    "web-tech/server-rendering-and-client-data-flow": ["web-tech/angular-ssr-hydration-and-private-transfer-state"],
    "web-tech/application-search-and-retrieval": ["web-tech/angular-signal-sources-computed-views-and-effect-scope"],
}
for path, targets in crosslinks.items():
    assert path in by_path, path
    by_path[path]["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    by_path[path]["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": 1, "new_lessons": 4, "prose_words": {topic["slug"]: len(re.findall(r"\b[\w'-]+\b", " ".join(str(topic[key]) for key in ("concept", "case", "implementation", "cost", "failure", "drill", "decision", "summary")))) for topic in topics}}))
