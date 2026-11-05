"""Add Next.js App Router boundaries, practice, and assessment drafts."""
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


hub_path = "web-tech/nextjs-app-router-delivery-boundaries"
hub_title = "Next.js App Router Delivery Boundaries"
topics = [
    dict(
        slug="nextjs-server-client-component-and-data-boundary",
        title="Next.js Server and Client Component Data Boundary",
        summary="Keep private reads on the server and send a small, serializable interaction model to the browser.",
        concept="An App Router page and layout render as Server Components unless a client boundary is declared. Server code can read private services and render data without shipping that code as browser JavaScript. A Client Component can own input state, event handlers, and browser APIs. Crossing from server to client is a data-delivery boundary: its props must be serializable for React and may be visible in page or navigation payloads. A secret environment value, a database handle, or an unauthorized case record does not become safe because it was passed from a server file. Mark a small interactive leaf as client code and pass only the permitted fields it needs. The owner of authorization remains server-side.",
        case="A city permit page shows 47 cases for reviewer 81. The page fetches the authorized list on the server, but a developer marks the whole page as a Client Component to support one search box. That pulls a large component subtree into the browser bundle and tempts a second client fetch. Another developer passes the complete permit service object as a prop, which cannot be serialized and contains methods and private fields. The repair leaves the page server-rendered, narrows the response to IDs, titles, and statuses the reviewer may see, and places only the filter control and rows in a Client Component. The server still checks access to detail and mutation routes separately.",
        implementation="Draw the boundary around the smallest interactive unit. The server page obtains reviewer identity, queries permitted cases, and maps each case to a plain transfer shape. Do not send secrets, database clients, raw errors, or records beyond the authorized first page. Put the search input and its local phrase inside a client component, then derive visible rows from those transferred cases. If the list may contain 47,000 records, return a bounded page and query the server for more rather than serializing the whole corpus. A client component may render a server component as a child through composition, but that does not grant client code direct access to server-only modules. Inspect build output and response payloads after changing a boundary.",
        cost="A server component removes its module code from the browser bundle, yet its rendered content and selected props still consume response bytes. A client island adds hydration JavaScript and memory for its state. A 47-case first page is cheap to transfer; 47,000 full records may dominate time to first useful interaction even when the server query is fast. Filtering n transferred cases is O(n) per changed phrase and may allocate O(n) results. Overly large client boundaries expand the shipped dependency graph. Overly fragmented boundaries can complicate prop contracts. Measure browser bytes, server latency, serialization size, and input response before changing the split.",
        failure="Inspect the HTML and server component payload for an unauthorized case ID and a server secret. Confirm neither appears. Switch from reviewer 81 to reviewer 47 on the same server worker and verify their lists do not mix. Remove JavaScript and ensure the first permitted page remains readable. Check that the search box hydrates from the same initial cases the server rendered. Insert a browser-only date formatter and deliberately force a first-render mismatch, then replace it with a stable server display value or delayed personalization. Compare bundle size before and after moving the search leaf behind a client boundary.",
        drill="Build a permit index that returns 47 authorized summaries for reviewer 81. Keep identity and repository calls server-side. Define a transfer type containing only ID, title, and status, pass it to a client filter, and display a count derived from the local phrase. Scan the output payload for an extra private field. Add a second reviewer whose case set is disjoint and run concurrent requests. Change the search leaf into a whole-page client boundary as a negative experiment, record added browser bytes and duplicate fetches, then restore the smaller boundary.",
        decision="Fetch and authorize on the server; move only the interaction and its minimal serializable data across the client boundary.",
        code='''import 'server-only';
import PermitFilter from './PermitFilter';
import { requireReviewer, permitRepository } from './services';

export default async function PermitPage() {
  const reviewer = await requireReviewer();
  const permitted = await permitRepository.firstPage(reviewer.id, 47);
  const summaries = permitted.map(permitCase => ({
    id: permitCase.id,
    title: permitCase.title,
    status: permitCase.status
  }));
  return <PermitFilter initialCases={summaries} />;
}''',
        checks=["Only authorized plain fields cross into the browser payload.", "A small client component owns the search interaction.", "Two reviewer requests cannot share private case data."],
        mistakes=["Marking an entire server page client-side for one input.", "Passing a service object or secret as a client prop.", "Equating server execution with automatic response privacy."],
        related=["web-tech/react-state-and-rendering-boundaries", "web-tech/sveltekit-request-scoped-load-and-hydration-state"],
    ),
    dict(
        slug="nextjs-cache-scope-and-private-read-invalidation",
        title="Next.js Cache Scope and Private Read Invalidation",
        summary="Separate public reusable data from viewer-specific reads and verify freshness after a mutation.",
        concept="An App Router request can encounter several caches: application data reuse, rendered route output, browser navigation state, and upstream HTTP caches. Each has a different owner and expiry rule. Next.js caching controls have changed across versions and project configurations, so a path name alone does not prove a read is fresh or shared safely. Public permit category labels may be reused across visitors. A reviewer-specific queue may not be stored under a key that ignores identity and permission version. A successful mutation can update the database while a browser still displays a previously rendered segment. Decide which cached representation is invalidated, when the current view refreshes, and what stale interval the product accepts.",
        case="Reviewer 47 approves case 62. The database stores approved, yet the queue still shows pending because a rendered route was reused after the action. Another reviewer opens the same path and briefly receives case 62 from a shared data cache keyed only by URL. The fix is not a blanket purge. The public category list can retain a longer lifetime, while the private queue read runs in the request's authorization context or uses a key that encodes the full visibility boundary. The mutation invalidates the affected queue path or data entry and the client refreshes its view when needed. A response must never be shared across accounts merely to save one query.",
        implementation="Inventory each read by owner: public, tenant-wide, reviewer-specific, or mutation-specific. For private data, resolve identity before querying and keep the read outside an unsafe shared cache. For reusable public data, choose an explicit lifetime and invalidation route supported by the deployed Next.js version and its cache configuration. Connect an approval to the representation that becomes stale, then revalidate or refresh that representation after the database commits. Do not revalidate before the transaction finishes. A browser's current navigation state may still need a refresh; test the user-visible result, not just a server API call. Record cache keys, audience, maximum staleness, and failure behavior in a small table maintained with the application.",
        cost="Fresh private reads increase database work per request. Shared public cache entries reduce that work but add invalidation and storage cost. A broad path purge can cause a thundering herd after one mutation; narrow invalidation limits the work but is easier to get wrong. Stale reads can mislead a reviewer into repeating an action or treating an approved case as pending. Cache-key entropy grows when identity and permission versions are included, reducing reuse but preserving isolation. Measure read rate, hit rate, invalidation delay, database load, and the time until the reviewer sees the committed state. An apparently high cache hit rate is not a success if it crosses permission boundaries.",
        failure="Warm a private queue under reviewer 47, then request the same path as reviewer 81; scan both payloads for cross-account IDs. Approve case 62 and immediately revisit the queue through a client transition, hard reload, and second browser tab. All should converge within the stated freshness window. Temporarily fail invalidation after commit and verify the UI exposes stale state rather than silently claiming success. Change a public category label and confirm its cache refresh does not evict every private queue. Run a burst of approvals and inspect whether broad invalidation drives a database spike.",
        drill="Classify three reads: public permit types, reviewer queue summaries, and one private case detail. Write their audiences and acceptable stale windows. Implement the private queue through a request-scoped repository call and keep the public list under an explicit reusable policy. Simulate an approval and record the database commit time, invalidation time, and first refreshed browser view. Repeat with two reviewers on the same path. Deliberately key a test cache only by URL to reproduce cross-user leakage, then remove that configuration. Record query count and cache hits under a moderate burst.",
        decision="Cache only across viewers who are allowed to share the representation; invalidate after commit and verify the current browser view.",
        code='''import 'server-only';
import { requireReviewer, permitRepository } from './services';

export async function loadReviewerQueue() {
  const reviewer = await requireReviewer();
  return permitRepository.listAuthorized({
    reviewerId: reviewer.id,
    limit: 47
  });
}

// This request-owned read must not be wrapped in a URL-only shared cache.''',
        checks=["Private cache entries cannot cross reviewer permissions.", "A committed approval refreshes the visible queue within the declared window.", "Public cache invalidation does not purge unrelated private data."],
        mistakes=["Assuming all framework caches have one invalidation rule.", "Caching a private response by route path alone.", "Revalidating before a write commits or failing to refresh the current view."],
        related=["web-tech/application-cache-consistency-and-capacity", "web-tech/http-delivery-and-cache-ownership"],
    ),
    dict(
        slug="nextjs-server-functions-validation-and-operation-identity",
        title="Next.js Server Functions, Validation, and Operation Identity",
        summary="Treat a server function as a public mutation entry point with permission and replay controls.",
        concept="A server function can receive a form submission and run mutation code on the server, but its arguments remain untrusted input. The function is an entry point, not proof that the caller may approve any case ID it submits. A correct approval reads authenticated identity on the server, validates fields, checks case permission, and commits through a service with an operation ID. Form submission can occur twice or lose its response after the database commits. A unique token per logical user intent, retained across retry, allows the server to return the prior result rather than applying a second effect. Path or data revalidation follows a successful commit so the queue can show the new authoritative status.",
        case="Reviewer 81 submits approval for case 62. The database transition succeeds, but the browser connection fails and the page still shows a pending button. A second submit with a fresh token sends another notification. A different reviewer changes the hidden case field to 47 and receives success because the function trusts form data. The repair checks the current session and case-level authority on each call, validates a stable operation token, and makes the approval plus deduplication record atomic. A replay of the same token returns the previous approved result. Only after commit does the function revalidate the affected queue, and the client displays the returned state rather than assuming the click succeeded.",
        implementation="Define the function in a server-only module. Parse FormData with exact type and format checks; a FormData value can be a string or File, and an empty string must not become a valid identifier. Resolve reviewer identity inside the call. The repository service verifies permission and performs the transaction under a uniqueness rule for operation ID and reviewer. Bound the token lifetime and require a new token only for a genuinely new intent. Return or surface validation and conflict results without echoing private details. After commit, revalidate the affected path or tag using the API matching the project's Next.js cache model. Keep the form usable before client JavaScript, then add pending and retry UI that preserves the same token after a lost response.",
        cost="A permission check and deduplication transaction add work to each write. Retaining m operation IDs costs O(m) storage and an index, but it prevents duplicate audit events and notifications. Revalidation can fan out to many readers; a broad path invalidation may cause a burst of database reads. An optimistic button state can improve responsiveness but needs rollback and must never be presented as server confirmation. The form payload is small; the expensive parts are lock contention on a case, downstream notifications, and stale cache repair. Measure logical approvals versus HTTP submissions, conflict frequency, time to confirmed status, and revalidation fanout.",
        failure="Submit the form with JavaScript disabled. Send an empty case ID, decimal, negative ID, File in place of a string, expired operation ID, and unauthorized case. None may mutate the database. Commit an approval, drop the response, and replay the same token; inspect one status transition and one notification. Submit a new token for the already approved case and verify the domain conflict rule. Race two reviewers with permission to approve the same case and confirm one authoritative outcome. Fail revalidation after commit and verify the UI can still recover by loading the committed record.",
        drill="Create an approval form for case 62 and a server function that receives its FormData. Add exact parsing, session lookup, permission check, and a service call with an operation ID. Build a fake transactional service that records IDs, returns prior results on replay, and rejects conflicting second intents. Simulate response loss and a double click. Measure mutation count and notification count separately. Then verify the queue view after revalidation and a hard reload. Record the expected user message for validation, forbidden, conflict, and transport failure, without exposing another reviewer's case.",
        decision="A server function is a mutation boundary; authorize, validate, deduplicate, commit, then refresh the affected view.",
        code='''\"use server\";
import { revalidatePath } from 'next/cache';
import { requireReviewer, permitService } from './services';

export async function approvePermit(formData: FormData) {
  const caseField = formData.get('caseId');
  const tokenField = formData.get('operationId');
  if (typeof caseField !== 'string' || !/^[1-9]\\d{0,8}$/.test(caseField) ||
      typeof tokenField !== 'string' || !/^[a-zA-Z0-9-]{20,80}$/.test(tokenField)) {
    return { kind: 'invalid' as const };
  }
  const reviewer = await requireReviewer();
  const result = await permitService.approveOnce({
    reviewerId: reviewer.id, caseId: Number(caseField), operationId: tokenField
  });
  if (result.kind === 'approved') revalidatePath('/permits');
  return result;
}''',
        checks=["Every call checks server identity and case-level permission.", "A repeated token maps to one committed operation.", "The affected view refreshes only after a successful commit."],
        mistakes=["Trusting a hidden case field or client-disabled button.", "Generating a new operation ID for a retry of the same intent.", "Assuming revalidation itself is a database transaction."],
        related=["web-tech/api-mutation-and-failure-contracts", "web-tech/sveltekit-form-actions-validation-and-mutation-replay"],
    ),
    dict(
        slug="nextjs-streaming-suspense-and-error-recovery",
        title="Next.js Streaming, Suspense, and Error Recovery",
        summary="Place slow data behind a meaningful fallback while keeping failures and private payloads within scope.",
        concept="Streaming lets the server send a ready part of a route while slower work continues behind a Suspense boundary. A route loading file can provide a fallback for the segment; a nested Suspense boundary can isolate one slower panel. The fallback is real user interface, not a performance metric: it must explain what is pending, reserve reasonable layout space, and avoid announcing a false completed state. A server render can still fail after the first chunk has been sent, so an error boundary and retry path need deliberate ownership. Streaming also does not relax permission checks. A slow private metrics panel must be authorized before its data is emitted, and the visible shell must not imply that missing data is zero.",
        case="A permit dashboard renders a heading and filter quickly, but a compliance metrics query takes 1.8 seconds. Without a boundary, the whole route waits and the reviewer sees no progress. A generic skeleton wrapped around the entire page hides an already available case list and loses focus on client transition. The repair keeps the authorized queue in the ready shell and puts only metrics behind a nested Suspense fallback with stable dimensions. When metrics fail, the panel shows an error with a retry route rather than a permanent spinner. The shell never renders metrics from a prior reviewer while the new request is pending.",
        implementation="Separate the fast, independently useful content from the slow server component. Fetch only data needed for the ready shell before rendering it; start unrelated reads early when possible rather than creating a serial waterfall. Put slow metrics behind a nested Suspense boundary and use a descriptive fallback that has the panel's expected dimensions. Keep labels and controls accessible even while content is pending. Define error handling at the segment or component boundary appropriate to the failure. Do not catch every error and replace it with an empty successful dataset; distinguish permission denial, temporary service failure, and a real zero value. Verify the initial chunk, later chunk, client transition, and no-script response under slow and failed metrics.",
        cost="Streaming improves when useful content can arrive, but it does not reduce the actual CPU or query time of a slow component. Each boundary adds server coordination, payload chunks, and possible layout changes. A fallback that is too high in the tree can hide content that is already ready; boundaries placed around tiny fragments can increase complexity without meaningful progress. An oversized client shell may still require browser JavaScript before interaction. Measure time to first byte, first useful content, final panel completion, layout shift, and task completion. A fast fallback that stays visible for 1.8 seconds may still be a poor experience if it blocks the reviewer's next action.",
        failure="Delay metrics for 1.8 seconds and verify the queue appears while the panel remains pending. Fail metrics after the shell has streamed; the page should not loop on a spinner or silently display zero. Switch from reviewer 47 to 81 during a slow transition and inspect the shell and panel for stale private values. Disable scripts and verify the server response contains a meaningful queue and eventual metrics or failure state. Trigger a pending form mutation while metrics stream and ensure its status does not get conflated with the metrics fallback. Test keyboard focus through fallback replacement and check that dimensions prevent a large shift.",
        drill="Build a permit dashboard with a fast case queue and a slow authorized metrics panel. Add a nested Suspense fallback that names the panel and keeps its expected height. Use a controlled 1.8-second delay and capture the shell arrival, metric arrival, and focus behavior. Then throw a metrics error and implement a recoverable panel state. Run two concurrent reviewers and inspect all streamed chunks for cross-user data. Move the boundary around the whole page as a negative experiment, compare first useful content, and restore the smallest useful boundary.",
        decision="Stream a genuinely useful shell and isolate slow, authorized work behind a bounded fallback and recoverable error path.",
        code='''import { Suspense } from 'react';
import { requireReviewer, permitRepository } from './services';

async function PermitMetrics({ reviewerId }: { reviewerId: string }) {
  const metrics = await permitRepository.metricsForReviewer(reviewerId);
  return <p>{metrics.pending} cases need review</p>;
}

export default async function PermitDashboard() {
  const reviewer = await requireReviewer();
  const cases = await permitRepository.firstPage(reviewer.id, 47);
  return <>
    <h2>Permit queue</h2>
    <p>{cases.length} cases in this page</p>
    <Suspense fallback={<p>Loading review metrics...</p>}>
      <PermitMetrics reviewerId={reviewer.id} />
    </Suspense>
  </>;
}''',
        checks=["The useful queue shell appears before the slow panel completes.", "Failed metrics show a recoverable state, not a false zero.", "All streamed chunks remain authorized for the current reviewer."],
        mistakes=["Wrapping the entire page in a fallback for one slow panel.", "Treating a loading fallback as an error recovery plan.", "Displaying stale private metrics during reviewer transition."],
        related=["web-tech/streaming-and-large-data-interfaces", "web-tech/react-hydration-and-stable-first-render"],
    ),
]

assert hub_path not in by_path and len(topics) == 4
hub = copy.deepcopy(by_path["web-tech/production-signals-and-incident-decisions"])
hub.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + hub_path)), path=hub_path,
           title=hub_title, summary="Own client transfer, private cache freshness, mutation replay, and streamed failure boundaries.",
           sort_order=3690, created_at=stamp, updated_at=stamp, published_at=stamp)
hub["data"] = {"subject_root": "web-tech/web-technology", "section_path": hub_path, "content_format": "html", "seo_ready": False,
               "modules": [], "resource_tabs": [{"title": "Web Development", "path": "web-tech/web-technology"},
                                                {"title": "Projects", "path": "web-tech/web-technology/project"},
                                                {"title": "Quizzes", "path": "web-tech/quizzes"}]}
entries.append(hub)
by_path[hub_path] = hub

for number, topic in enumerate(topics):
    path = "web-tech/" + topic["slug"]
    assert path not in by_path
    language = "tsx" if "<" in topic["code"] and ("<Permit" in topic["code"] or "<>" in topic["code"]) else "typescript"
    subprocess.run([str(root / "node_modules/.bin/esbuild"), "--loader=" + ("tsx" if language == "tsx" else "ts"), "--format=esm"],
                   input=topic["code"], text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path["web-tech/trace-context-across-request-and-job"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                 title=topic["title"], summary=topic["summary"], sort_order=3691 + number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    related = [hub_path] + ["web-tech/" + other["slug"] for other in topics if other is not topic] + topic["related"]
    body = paragraph(topic["concept"]) + "<h2>Working case</h2>" + paragraph(topic["case"])
    body += '<h2>Implementation boundary</h2><pre><code class="language-' + language + '">' + html.escape(topic["code"], quote=False) + "</code></pre>" + paragraph(topic["implementation"])
    body += "<h2>Cost and boundaries</h2>" + paragraph(topic["cost"]) + "<h2>Failure trace</h2>" + paragraph(topic["failure"])
    body += "<h2>Verification</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in topic["checks"]) + "</ul>"
    body += "<h2>Practice drill</h2>" + paragraph(topic["drill"]) + "<h2>Decision note</h2>" + paragraph(topic["decision"])
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
hub["body"] = paragraph("A Next.js permit review app crosses distinct boundaries when private server data reaches an interactive leaf, a cached queue becomes stale, a form mutates a case, and a slow panel streams after the shell. Each lesson defines the owner and failure response so rendering speed does not conceal a permission or replay error.")
hub["body"] += "<h2>Topics in this track</h2><ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
hub["body"] += "<h2>Prerequisite paths</h2><p>" + "; ".join(link(path) for path in ["web-tech/react-state-and-rendering-boundaries", "web-tech/http-delivery-and-cache-ownership", "web-tech/api-mutation-and-failure-contracts"]) + ".</p>"
curriculum = by_path["web-tech/web-technology"]
curriculum["data"]["modules"].append({"title": hub_title, "summary": hub["summary"],
                                       "lessons": [hub_path] + ["web-tech/" + topic["slug"] for topic in topics]})
curriculum["body"] += "<h2>" + link(hub_path) + "</h2>" + paragraph(hub["summary"]) + "<ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
curriculum["updated_at"] = stamp
crosslinks = {
    "web-tech/react-state-and-rendering-boundaries": [hub_path],
    "web-tech/server-rendering-and-client-data-flow": ["web-tech/nextjs-server-client-component-and-data-boundary"],
    "web-tech/application-cache-consistency-and-capacity": ["web-tech/nextjs-cache-scope-and-private-read-invalidation"],
    "web-tech/api-mutation-and-failure-contracts": ["web-tech/nextjs-server-functions-validation-and-operation-identity"],
    "web-tech/streaming-and-large-data-interfaces": ["web-tech/nextjs-streaming-suspense-and-error-recovery"],
}
for path, targets in crosslinks.items():
    by_path[path]["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    by_path[path]["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": 1, "new_lessons": 4,
                  "prose_words": {topic["slug"]: len(re.findall(r"\b[\w'-]+\b", " ".join(str(topic[key]) for key in ("concept", "case", "implementation", "cost", "failure", "drill", "decision", "summary")))) for topic in topics}}))
