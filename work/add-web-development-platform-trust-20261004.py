"""Add original typed frontend and platform trust lessons to the Web Development track."""

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


def link(path):
    assert path in by_path, path
    return f'<a href="/{html.escape(path, quote=True)}">{html.escape(by_path[path]["title"])}</a>'


def para(value):
    return f"<p>{html.escape(value)}</p>"


hubs = [
    dict(path="web-tech/typed-frontend-and-component-platform", title="Typed Frontend and Component Platform",
         summary="Validate external data, tame async UI work, choose component boundaries, and budget loaded code.",
         overview="A component model helps organize browser code, but it cannot certify data arriving over a network or guarantee that the latest response wins. Types describe what code expects; runtime checks establish what arrived. Effects must stop work tied to an obsolete screen. Encapsulated components can reduce style collisions while introducing focus and theming obligations. Loading code only when needed can improve first use while shifting cost to a later interaction. These lessons treat each boundary as a measurable decision.",
         bridges=["web-tech/component-boundaries-and-state", "web-tech/fetch-status-and-abort", "web-tech/server-rendered-static-and-client-rendered-pages"]),
    dict(path="web-tech/browser-security-and-data-stewardship", title="Browser Security and Data Stewardship",
         summary="Set embedding and capability limits, guard DOM sinks, pin dependencies, and keep telemetry lean.",
         overview="A web service can validate requests and still leak through an embedded page, an unsafe DOM sink, a changed remote script, or a log that keeps too much case data. Browser response controls, output handling, dependency review, and telemetry policy address different failure paths. None replaces authorization. The lessons make these boundaries concrete with a case-review application, staged rollout checks, and explicit notes about what a small snippet cannot enforce alone.",
         bridges=["web-tech/output-escaping-and-csp", "web-tech/environment-config-and-secrets", "web-tech/observability-and-recovery"]),
]

topics = [
    dict(path="web-tech/typescript-and-runtime-api-boundaries", hub=hubs[0]["path"], title="TypeScript and Runtime API Boundaries",
         summary="Treat parsed network data as unknown until its required shape is checked at runtime.",
         definition="A TypeScript type describes an expectation during development; it does not alter the bytes received by fetch or validate JSON after compilation. A type assertion can silence a compiler warning while preserving a malformed value at runtime. Put a narrow decoder at the network boundary, starting with unknown, and return a domain object only after required fields have been checked. Keep optional fields genuinely optional and reject values that would make a screen or mutation unsafe. The decoder is also a place to translate a wire version into an internal model without leaking transport details through every component.",
         case="The case API previously returned {caseId, status}. A staged server release adds a reviewCount and accidentally sends it as a string for one account. A component casts the response to CaseSummary and adds one; the visible badge becomes '471' instead of 48. A runtime boundary should reject or normalize the unexpected value according to a written contract. It should also keep the original response available only in a bounded diagnostic channel that does not copy private notes into logs. The route then shows a recoverable data error rather than an invented count.",
         code='type CaseSummary = { caseId: number; status: "open" | "closed"; reviewCount: number };\nfunction decodeCaseSummary(rawCaseResponse: unknown): CaseSummary {\n  if (typeof rawCaseResponse !== "object" || rawCaseResponse === null) throw new Error("Invalid case response");\n  const record = rawCaseResponse as Record<string, unknown>;\n  if (typeof record.caseId !== "number" || !Number.isInteger(record.caseId) || record.caseId <= 0) throw new Error("Invalid case ID");\n  if (typeof record.reviewCount !== "number" || !Number.isInteger(record.reviewCount) || record.reviewCount < 0) throw new Error("Invalid review count");\n  if (record.status !== "open" && record.status !== "closed") throw new Error("Invalid case status");\n  return { caseId: record.caseId, status: record.status, reviewCount: record.reviewCount };\n}',
         language="typescript", implementation="The decoder checks only fields this screen needs. A production boundary may also cap string lengths, validate nested arrays, and identify a response version. It must not accept a numeric string just because a loose comparison succeeds. Separate decoding from authorization: a well-formed case can still belong to another account. A maintained schema library can reduce repeated checks, but it does not decide which coercions are safe for this domain. Model decode errors distinctly from network and permission errors so the interface can choose the right recovery path.",
         cost="Validation scans the fields and collections it inspects, so a list response costs O(n) in the number of records plus any nested content. That CPU cost is usually modest next to a network request, but decoding a huge payload repeatedly can be wasteful; paginate and validate once at the boundary. Strict rejection increases visibility of server regressions but may temporarily block an old client when the API changes. Add compatibility tests and an explicit fallback policy rather than replacing every decoder with an unsafe cast. Type inference remains useful inside the trusted portion of the application.",
         failure="A backend renames reviewCount to reviews without coordinating release. The frontend assertion still compiles, but rendering treats undefined as a valid count and displays a blank badge. A unit test with hand-authored typed fixtures passes because it never parses the actual response. Run contract tests against raw JSON from old and new server versions, then verify the route displays a specific error or compatible value. The incident is a data-contract failure, not a TypeScript failure.",
         drill="Feed the decoder null, a list, a missing status, a numeric string, and an unknown future status. State which inputs should be rejected and which extra fields should be ignored. Then test the route with the real response parser rather than a pretyped object. If a compatibility adapter is added, keep it at this boundary so components do not each invent different fallbacks for the same field.",
         decision="Use static types for local reasoning and runtime checks for untrusted data. One cannot stand in for the other at a network or storage boundary.",
         checks=["Parse a valid old and new response as raw JSON and verify the intended internal shape.", "Reject null, arrays, numeric strings, and unsupported status values with clear errors.", "Show a recoverable route state after a decode failure without leaking private response content."],
         mistakes=["Casting response.json() directly to a trusted domain type.", "Letting each component coerce a malformed field differently.", "Logging the entire rejected response with private case notes."],
         related=["web-tech/api-evolution-and-compatibility", "web-tech/form-server-validation", "web-tech/contract-tests-across-boundaries"]),
    dict(path="web-tech/react-effects-and-request-races", hub=hubs[0]["path"], title="React Effects and Request Races",
         summary="Tie asynchronous work to the current route and stop stale results from replacing new state.",
         definition="An effect connects a rendered component to an external system such as a network request, subscription, or browser event. When its dependencies change, the previous connection must be cleaned up before the next one takes ownership. A fetch started for one case can finish after the user opens another case. If its result is applied unconditionally, the page may show the wrong record under the new URL. An AbortController can stop a request that is no longer needed, while an identity or generation check prevents an already-completed callback from committing stale data.",
         case="Reviewer 29 opens case 47, then immediately selects case 62. The request for case 62 finishes first and paints its details. The slower case 47 response arrives later and overwrites the panel while the URL still says 62. The bug appears only on variable networks, so local testing with cached responses misses it. Tie the effect to caseId, abort the prior request during cleanup, and test both completion orders. The server still must authorize both requests; cancellation is a UI consistency tool, not access control.",
         code='function useCaseDetails(caseId) {\n  const [details, setDetails] = React.useState(null);\n  React.useEffect(() => {\n    const controller = new AbortController();\n    setDetails(null);\n    fetch(`/api/cases/${caseId}`, { signal: controller.signal })\n      .then(response => { if (!response.ok) throw new Error("Case load failed"); return response.json(); })\n      .then(result => { if (!controller.signal.aborted) setDetails(result); })\n      .catch(error => { if (!controller.signal.aborted && error.name !== "AbortError") setDetails({ error: true }); });\n    return () => controller.abort();\n  }, [caseId]);\n  return details;\n}',
         language="javascript", implementation="The sketch resets the visible state when the case changes and aborts the previous request. A real hook should validate the response, avoid updating an obsolete state from any error branch, and expose loading, not-found, permission, and retry states separately. Route-level data loading or a maintained request cache may handle deduplication, server rendering, and stale responses more efficiently than hand-written effects. If an effect subscribes to live events, cleanup must unsubscribe as well. Keep dependency lists honest rather than suppressing them to avoid reruns.",
         cost="Unneeded requests consume bandwidth and server work even if their responses are ignored; cancellation can reduce that cost but may arrive after the server has already done its work. Fetching from a mounted child can create a parent-then-child waterfall and delay useful content. Route loaders or prefetching can move data work earlier. Each custom effect adds branches for response order, abort, error, and unmount, so use it where the external connection truly belongs to the component. Measure route latency before adding another cache layer.",
         failure="A developer removes caseId from the effect dependencies to stop duplicate loading. The hook now keeps showing case 47 when the route changes to 62. Another version keeps caseId in dependencies but never cleans up, so the old request wins a race. Both fixes treat the effect as a one-time callback instead of a connection tied to current input. Restore correct dependencies and cleanup, then simulate slow and fast responses in both orders.",
         drill="Use a test transport that resolves case 62 before case 47. Confirm that the panel and URL agree after both promises settle. Repeat with a rejected old request and verify its catch handler cannot replace the new case's state. Leave the route before either request finishes and confirm no stale update occurs. If the route framework already loads data, compare its behavior and remove the custom effect when it duplicates that mechanism.",
         decision="Prefer route or framework data loading when it already solves cache and ordering. For a local effect, make setup and cleanup symmetrical and guard every completion path.",
         checks=["Switch 47 to 62 with the first request deliberately slower, then reverse completion order.", "Unmount during a request and verify cleanup prevents a stale update.", "Force old and current requests to fail separately and inspect the visible error owner."],
         mistakes=["Suppressing a dependency to hide rerenders.", "Guarding success but not the error callback against stale work.", "Treating AbortController as a server-side authorization control."],
         related=["web-tech/browser-routing-and-history", "web-tech/fetch-status-and-abort", "web-tech/browser-journey-and-fault-tests"]),
    dict(path="web-tech/web-components-and-shadow-boundaries", hub=hubs[0]["path"], title="Web Components and Shadow Boundaries",
         summary="Use custom elements for stable reuse while planning styling, focus, events, and form behavior.",
         definition="A custom element is a browser-defined component with a registered tag and lifecycle. Shadow DOM can isolate its internal markup and styles from unrelated page rules. That isolation is useful when a case-status badge must appear in several applications, but it is not a security boundary and does not supply accessibility automatically. The host still needs a documented property and event contract. If the component contains interaction, keyboard behavior, names, focus, and form participation need deliberate design. A framework component may be simpler when reuse remains inside one application.",
         case="An inspection badge is embedded in the review dashboard and a separate administrative portal. Each host has different CSS, and global selectors repeatedly change the badge's color or spacing. A small custom element can keep its internal layout stable while exposing status as an attribute. The host still needs a way to style approved themes and receive status-change events. If the badge grows into a button, the component must expose a clear name and test focus across the shadow boundary; encapsulation alone does not make it usable.",
         code='class CaseStatusBadge extends HTMLElement {\n  static observedAttributes = ["status"];\n  constructor() { super(); this.attachShadow({ mode: "open" }); }\n  connectedCallback() { this.render(); }\n  attributeChangedCallback() { this.render(); }\n  render() {\n    const status = this.getAttribute("status") === "closed" ? "Closed" : "Open";\n    this.shadowRoot.textContent = status;\n  }\n}\ncustomElements.define("case-status-badge", CaseStatusBadge);',
         language="javascript", implementation="The example uses textContent so a status attribute cannot become executable markup. It is intentionally plain: production markup could include scoped styles and a named part for theming. Document which attributes trigger updates and whether a change emits an event; do not make host code reach into private nodes. If a form-associated control is required, use the browser's form association mechanism or a native input, not an invisible proxy that loses labels. Check server rendering and upgrade timing if the component appears in critical initial content.",
         cost="Registration and upgrade add JavaScript to a page that may otherwise need none. Shadow styles are separate assets or inline bytes, and repeated instances can multiply work if each injects large markup. One small badge is cheap; a hundred rich widgets may not be. The isolated tree makes some host selectors and tests less direct, so expose a small supported styling API and task-level checks. A custom element earns its cost when it serves several hosts with a stable contract, not merely because it can wrap a span.",
         failure="The dashboard theme changes text color, but the shadow badge keeps low-contrast text because it does not inherit the intended token. The team reaches inside each shadowRoot to patch the style, coupling both applications to private markup. A later component update renames the node and breaks both hosts. Expose a documented CSS custom property or part for supported theming, then test contrast and language in each host. Treat a closed shadow root as encapsulation, not a reason to skip accessibility review.",
         drill="Embed the badge in two pages with conflicting global CSS. Verify its status text stays correct, and change the status attribute after connection to test lifecycle updates. Add a documented theme token and check contrast in both hosts. Then evaluate whether the component still helps if the second host is removed; a local framework component may have lower maintenance cost when reuse disappears.",
         decision="Choose a web component when cross-application reuse and a stable host contract justify its upgrade and styling costs. Keep ordinary page markup ordinary when they do not.",
         checks=["Mount the element in two hosts with conflicting CSS and verify status and approved theming.", "Change status after connection and verify text updates without HTML injection.", "Test focus and name explicitly if the component later gains an interactive action."],
         mistakes=["Treating Shadow DOM as a security sandbox.", "Reaching into private nodes from host code as a styling API.", "Assuming a custom interactive element inherits native button behavior."],
         related=["web-tech/component-boundaries-and-state", "web-tech/accessible-names-and-native-controls", "web-tech/output-escaping-and-csp"]),
    dict(path="web-tech/module-splitting-and-interaction-budget", hub=hubs[0]["path"], title="Module Splitting and Interaction Budget",
         summary="Load optional code near the task that needs it without making the first interaction wait blindly.",
         definition="A module split moves some JavaScript from the initial bundle to a later request. That can reduce parse and execution work for visitors who never use an optional feature. It also creates a new loading boundary when the feature is opened. A good split follows a user task: the case list should not eagerly parse the image-annotation editor, but clicking 'Annotate' should not leave a blank panel while code downloads. Prefetching after clear intent, a progress state, an error path, and a retry policy keep the new boundary honest.",
         case="Only a small share of reviewers annotate inspection photos, yet every case-list visitor downloads the editor package. The list feels slow on modest phones. Move the editor to an on-demand module and keep the list functional without it. When a reviewer opens image 61, show a useful loading state and fetch the module. A failed chunk request must offer retry or a plain-text note alternative; otherwise the optimization has exchanged a slower page for an unusable critical action.",
         code='async function openPhotoEditor(imageId) {\n  const openButton = document.querySelector("#open-photo-editor");\n  openButton.disabled = true;\n  try {\n    const { mountEditor } = await import("./photo-editor.js");\n    await mountEditor({ imageId, container: document.querySelector("#editor-panel") });\n  } finally { openButton.disabled = false; }\n}',
         language="javascript", implementation="The split defers the editor module until activation. A production path should catch download and mount errors, display a retry or alternate workflow, and avoid repeated imports caused by rapid clicks. The browser typically caches the loaded module, but a deployed release can remove old chunk names while an old tab remains open; a chunk failure may require a controlled refresh after preserving unsaved work. Keep a small visible placeholder and measure time from activation to usable editor, not only initial bundle size.",
         cost="The initial route saves transfer, parse, and execution work proportional to the deferred module. The first editor use pays an extra network round trip and evaluation cost. Splitting every small component can create request overhead and complex failure handling; group code by meaningful tasks. Prefetching can hide latency after a hover or route intent, but it consumes bandwidth for people who never open the editor. Compare actual task completion and interaction delay across devices before deciding the boundary is worthwhile.",
         failure="The initial bundle shrinks, so a lab score improves. On a slow connection, the first annotation click waits several seconds and the panel stays empty. An old tab then requests a chunk deleted by a new deployment and fails permanently. Track the editor-open journey, provide progress and a recovery route, and keep compatible assets during rollout where possible. A smaller file does not by itself prove a better interaction.",
         drill="Measure initial list load and first editor-open time separately. Repeat on a warm cache, a cold slow connection, and an old tab after deployment. Simulate a rejected module request and verify the reviewer can retry or save a plain note without losing the case context. Remove any prefetch rule that consumes bandwidth without materially improving the first useful editor interaction.",
         decision="Split by optional task, then budget both sides of the boundary: first-page cost and first-use delay. Optimize the workflow, not a bundle-size number alone.",
         checks=["Compare initial list parse cost before and after the editor split.", "Measure time from activation to usable editor on a cold slow connection.", "Force chunk failure in an old tab and verify recovery preserves context."],
         mistakes=["Splitting tiny modules until request overhead dominates.", "Showing no progress while a deferred action loads.", "Dropping old chunks immediately while open tabs still reference them."],
         related=["web-tech/performance-budget-and-layout-stability", "web-tech/field-and-lab-performance-evidence", "web-tech/ci-release-gates"]),
    dict(path="web-tech/embedding-and-browser-capability-headers", hub=hubs[1]["path"], title="Embedding and Browser Capability Headers",
         summary="Constrain framing, referrer disclosure, and browser features with response policy that matches the route.",
         definition="A browser response can declare which other pages may frame it, what referrer detail leaves during navigation, and which browser features are available to the document or its frames. These policies protect different surfaces. A frame restriction can reduce clickjacking exposure for a private case screen; a referrer policy can limit case-path leakage; a feature policy can deny capabilities the application does not use. None proves a request is authorized, and one header value does not fit every route. Set policy at the server or edge, then verify the actual response sent for the target page and its error states.",
         case="A private inspection page contains case 47 in its path and an Archive button. A partner portal needs to embed a public status widget, but the private page must never be framed by an unrelated site. If one global allowlist admits the partner origin everywhere, the private page can be placed inside an attacker-controlled layout. Separate the widget route from private routes and give each a deliberate framing policy. A referrer restriction also prevents a full private path from being sent to unrelated destinations opened from the page.",
         code="Content-Security-Policy: frame-ancestors 'none'\nReferrer-Policy: strict-origin-when-cross-origin\nPermissions-Policy: camera=(), microphone=(), geolocation=()",
         language="http", implementation="These are example response lines for a private page, not an entire security configuration. If a public widget must be framed, its own route needs a narrower explicit framing rule. Test a real response because a CDN, framework, or error handler can override headers. Some headers have browser support or syntax details that change over time; stage restrictive changes and observe failures before enforcing them broadly. Policy also belongs with navigation and resource behavior: the page may still leak data through an application endpoint if authorization is wrong.",
         cost="Headers are cheap to transmit and interpret, but policy design consumes testing time. A too-strict frame rule can break an approved partner widget; a too-wide one can expose private controls. Referrer detail can help diagnostics, but retaining private path data outside the site carries avoidable exposure. Capability restrictions can reveal an undocumented browser feature dependency when deployed. Roll out by route group, inspect response headers in production-like environments, and monitor reports or partner journeys before broadening exceptions.",
         failure="The private page has a frame rule, but its 403 error page is served by another handler without that rule. An attacker embeds the error route and uses its login control as part of a deceptive page. The primary route test passed because it checked only a successful response. Verify policy on redirect and error paths as well. A second failure is using a wildcard frame source to satisfy one partner. Give the partner a dedicated widget surface instead of weakening the private application.",
         drill="Capture headers from an authenticated case route, an unauthenticated redirect, a not-found page, and a public widget. Try framing each from an approved and unapproved origin in a controlled test. Open a link to another site and inspect how much of the case URL becomes a referrer. Remove one browser capability and exercise the workflow that may depend on it; if the task breaks, revise the route-specific policy rather than silently dropping the header everywhere.",
         decision="Write route-specific browser policy from actual embedding and feature needs. Keep server authorization as a separate mandatory check.",
         checks=["Inspect actual headers on success, redirect, and error responses for private routes.", "Attempt approved and unapproved framing for the public widget and private case page.", "Check cross-site referrer behavior without exposing a private case path."],
         mistakes=["Treating browser headers as a substitute for record authorization.", "Opening a global frame exception for one widget.", "Testing only the happy-path response headers."],
         related=["web-tech/output-escaping-and-csp", "web-tech/record-level-authorization", "web-tech/cors-and-cross-origin-requests"]),
    dict(path="web-tech/dom-sinks-and-trusted-content", hub=hubs[1]["path"], title="DOM Sinks and Trusted Content",
         summary="Render untrusted strings as text and tightly control the rare path that needs authored HTML.",
         definition="A DOM sink is an API that interprets a string as markup, script, or another active format. Putting a case note into textContent displays its characters; putting the same note into innerHTML asks the browser to parse tags and attributes. The latter can create script execution paths if untrusted input is not correctly sanitized for that context. Framework escaping helps for ordinary text interpolation but can be bypassed by raw-HTML features. A content policy and Trusted Types can add enforcement in supporting browsers, yet neither makes an unsafe sanitizer safe. Start by asking whether markup is needed at all.",
         case="Reviewer 29 writes a note containing angle brackets to describe a damaged <pipe> label. The note is later shown in a live review panel. If the client assigns it to innerHTML, the browser may treat it as markup, and a malicious collaborator can craft a note with active content. The correct ordinary-note path assigns text. If editors later need a restricted rich-text field, separate that field from plain notes, parse and sanitize with a maintained allowlist, and review links and embedded media deliberately.",
         code='function renderCaseNote(noteRegion, caseNote) {\n  noteRegion.textContent = caseNote;\n}\nrenderCaseNote(document.querySelector("#case-note"), "Damaged <pipe> at level 47");',
         language="javascript", implementation="The example never asks the browser to interpret the note as HTML. A production component should also keep the note's visible line breaks and length limits consistent with the storage contract. Do not decode entities and then pass the result to a markup sink. If rich HTML is an approved product need, use a maintained sanitizer, a narrow set of elements and attributes, and a Trusted Types policy where supported; test links, URLs, and nested content. Treat any bypass method in a rendering framework as an explicit review point.",
         cost="Text rendering is simple and avoids sanitizer maintenance. Rich text adds parsing, policy review, and compatibility costs: a sanitizer update can change stored content presentation, while an overly broad policy can allow active URLs or event handlers. A strict browser policy can surface unsafe legacy code during rollout, requiring inventory and migration. The performance cost is usually small for short notes, but sanitizing long documents on every render is avoidable; define where the approved transformation occurs and cache the safe representation only under a versioned policy.",
         failure="A developer replaces textContent with innerHTML so line breaks appear automatically. A note that once displayed literally now creates an element with an event handler. A successful unit test using ordinary text does not catch it. Test hostile input through the full save-and-render path, including a reload and live update. Restore text rendering and use CSS or explicit text nodes for line breaks. Do not mark the note 'trusted' merely because it came back from the application's own database.",
         drill="Insert plain angle brackets, an HTML-looking link, an event-handler attribute, and an encoded entity into a note. Save it, reload, and inspect the DOM: each should remain text. Then search the codebase for markup sinks and list the few routes that genuinely need rich content. For those, document the sanitizer policy and test the exact allowed and rejected constructs. A browser policy report can help find missed sinks, but it is not an excuse to ship one permissive default policy.",
         decision="Default to text. Permit rich markup only through a named, reviewed content boundary with tests for the actual allowed subset.",
         checks=["Save and reload HTML-looking note text; confirm it remains text in the DOM.", "Audit raw-markup escape hatches and document every approved use.", "Test allowed and rejected constructs when a rich-text field is introduced."],
         mistakes=["Using innerHTML for simple line breaks.", "Trusting content because it came from the application's database.", "Creating a Trusted Types policy that simply returns unsanitized input."],
         related=["web-tech/output-escaping-and-csp", "web-tech/safe-file-upload-pipeline", "web-tech/web-components-and-shadow-boundaries"]),
    dict(path="web-tech/dependency-integrity-and-update-window", hub=hubs[1]["path"], title="Dependency Integrity and Update Window",
         summary="Keep browser dependencies reproducible and review the code that changes between releases.",
         definition="A web dependency enters the product through a package manager, a remote script, a build plugin, or a copied asset. A lockfile makes an install reproducible from approved versions, but it does not prove that a package is safe. A remote script may change without a repository commit unless its bytes are pinned or self-hosted. Treat each update as a code change: identify where the dependency executes, which browser capabilities it receives, what new transitive packages arrive, and how to roll back if behavior changes. Security advisories are one input to review, not a complete safety verdict.",
         case="The case dashboard uses a chart library only on the monthly report route. A minor package update adds a transitive analytics module that reads the page URL. If the report URL contains a case identifier, the new behavior crosses a privacy boundary. Review the lockfile diff and built network requests before deploying. Load the chart only on the route that uses it, and keep the dependency out of private case pages. For a truly external script, use a pinned integrity value or a controlled self-hosted asset rather than trusting a mutable URL.",
         code='npm ci\nnpm ls --all --depth=0\nnpm run build',
         language="bash", implementation="The commands install exact lockfile resolutions, show top-level dependency state, and build the product; they do not audit transitive behavior by themselves. Review the lockfile change, package provenance, install scripts, license obligations, and browser network activity for sensitive routes. Run the application tests after updating because type checks cannot detect every runtime change. If a CDN script is unavoidable, record its approved bytes and configure integrity with the exact digest; do not paste a made-up hash into markup.",
         cost="Reviewing dependency changes costs engineer time, so group routine updates into a regular window instead of letting them age indefinitely. Large update batches are harder to bisect when a regression appears; keep them small enough to attribute failures. Exact lockfile installs improve reproducibility but still require a trusted registry and build environment. Self-hosting can reduce remote-change risk while adding asset maintenance. Route-level code loading saves initial bytes when a library is optional, but the first use still needs an interaction budget and failure state.",
         failure="A development machine uses a stale installed module, while continuous integration resolves a newly changed transitive package because the lockfile was not committed. The build succeeds but a private route starts sending a request to an unapproved host. Reproduce from a clean lockfile install, inspect network requests, and roll back the dependency change. Do not respond by suppressing the request in one browser; the package and release boundary must be corrected.",
         drill="Update one dependency in a branch. Record direct and transitive lockfile changes, build from a clean installation, and exercise its route with network inspection. Deliberately break the remote asset and verify a usable fallback. If a vulnerability scanner reports an issue, confirm whether the affected code is reachable in the shipped bundle and apply the smallest safe update; do not assume a clean scan proves absence of risk.",
         decision="Treat dependency upgrades as reviewable releases. Reproducibility, provenance, route scope, and rollback matter more than a single package version number.",
         checks=["Rebuild from a clean lockfile install and compare the produced route behavior.", "Inspect new transitive packages and browser requests on private routes.", "Test a failed optional remote asset and a rollback of its update."],
         mistakes=["Assuming a lockfile is a security audit.", "Embedding a mutable external script without byte pinning or control.", "Updating many unrelated packages without a practical rollback path."],
         related=["web-tech/ci-release-gates", "web-tech/module-splitting-and-interaction-budget", "web-tech/release-smoke-and-rollback"]),
    dict(path="web-tech/telemetry-minimization-and-retention", hub=hubs[1]["path"], title="Telemetry Minimization and Retention",
         summary="Record operational signals without turning logs into a second store of private case content.",
         definition="Telemetry describes system behavior through events, traces, and measurements. Its fields should answer a specific operational question, not copy arbitrary request bodies for possible future use. A case application needs to know that a route failed, how often, at what stage, and whether the failure affected a release. It rarely needs the note text, password, recovery token, full case URL, or session identifier in a log. Define an allowlist of event categories and fields, a retention period, access controls, and a deletion path before enabling collection broadly.",
         case="A reviewer cannot open case 47 after a release. Engineers need to distinguish a route failure, a permission denial, and a decoder error. A trace containing a short request correlation ID, route class, error class, deployment version, and timing may be enough. Copying the entire case JSON would expose notes to every log reader and retain them far beyond the case's lifecycle. If support needs to inspect one record, it should use an authorized product path with a separate audit trail rather than repurposing telemetry as a private-data export.",
         code='function operationEvent(errorKind, requestId, releaseId) {\n  const allowed = new Set(["route_failure", "permission_denied", "decode_failure"]);\n  if (!allowed.has(errorKind)) throw new Error("Unknown event category");\n  return { event: errorKind, routeClass: "case_detail", requestId, releaseId };\n}',
         language="javascript", implementation="The function emits only an approved category and coarse route class. The caller must still ensure requestId is short-lived and cannot be used to recover a session or a case from logs alone. Keep raw URLs, query strings, headers, and request bodies out of default logging middleware unless a narrowly authorized diagnostic need exists. Apply retention to the storage system, not only to a document. Aggregated counts can often remain longer than individual traces; the product's actual policy determines the boundary.",
         cost="An allowlist reduces log volume and exposure, but may leave less context during an unusual incident. Add a temporary diagnostic field only with an owner, scope, expiry, and access review. High-cardinality identifiers can make metrics expensive, so use coarse route classes for dashboards and short-lived correlation IDs for traces. Deletion and retention jobs consume operational effort; test that they actually remove data from primary storage and relevant backups according to policy. More telemetry is not automatically more useful if responders cannot find the signal they need.",
         failure="An error middleware writes req.url and req.body for every failed API call. A recovery endpoint now places a token in the URL, and a case-note endpoint sends private text in the body. A single outage fills logs with secrets and records that outlive the application data. Replace broad dumps with classified events, rotate exposed credentials where needed, restrict access to the affected logs, and verify the retention and deletion path. A successful alert does not justify collecting the sensitive payload.",
         drill="List each field in a proposed case-load event and explain the operational question it answers. Remove fields that do not change triage. Trigger permission, decode, and network failures and confirm logs contain only category, route class, release, timing, and an approved correlation value. Search the log stream for a test recovery token and test note; neither should appear. Finally advance the retention clock in a test environment and verify deletion, not just a configuration setting.",
         decision="Define telemetry from incident questions backward and keep a field only when it changes a response. Operational visibility should not create a shadow copy of private content.",
         checks=["Trigger several failure classes and inspect actual emitted fields, not just logger calls.", "Search logs for injected test token, session value, and case note; none should appear.", "Verify retention and deletion behavior in storage with a test event past its lifetime."],
         mistakes=["Logging entire request or response objects on failure.", "Using private case IDs as unbounded metric labels.", "Writing a retention policy without testing deletion from the log store."],
         related=["web-tech/observability-and-recovery", "web-tech/account-recovery-and-session-revocation", "web-tech/field-and-lab-performance-evidence"]),
]

assert len(hubs) == 2 and len(topics) == 8
for hub in hubs:
    assert sum(topic["hub"] == hub["path"] for topic in topics) == 4


def add_entry(path, title, summary, entry_type, section_path, sort_order):
    assert path not in by_path, path
    template = "web-tech/getting-started" if entry_type == "article" else "web-tech/web-technology"
    entry = copy.deepcopy(by_path[template])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), type=entry_type,
                 path=path, title=title, summary=summary, category="Web Development",
                 subject="web-tech", difficulty="Intermediate" if entry_type == "article" else None,
                 tags=["web-tech", "web-development"], sort_order=1600 + sort_order,
                 status="published", created_at=stamp, updated_at=stamp, published_at=stamp, body="")
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": section_path,
                     "content_format": "html", "seo_ready": False}
    if entry_type == "article":
        entry["data"].update(kind="tutorial", author_path="authors/aitrove-editorial", reading_minutes=8)
    entries.append(entry)
    by_path[path] = entry
    return entry


for number, hub in enumerate(hubs):
    add_entry(hub["path"], hub["title"], hub["summary"], "subject", hub["path"], number)
for number, topic in enumerate(topics):
    add_entry(topic["path"], topic["title"], topic["summary"], "article", topic["hub"], 10 + number)

for topic in topics:
    entry = by_path[topic["path"]]
    if topic["language"] == "javascript":
        subprocess.run(["node", "--check", "--input-type=module"], input=topic["code"],
                       text=True, capture_output=True, check=True)
    related = [topic["hub"]] + [item["path"] for item in topics if item["hub"] == topic["hub"] and item["path"] != topic["path"]] + topic["related"]
    body = para(topic["definition"])
    body += "<h2>Working case</h2>" + para(topic["case"])
    body += f'<h2>Implementation boundary</h2><pre><code class="language-{topic["language"]}">' + html.escape(topic["code"], quote=False) + "</code></pre>"
    body += para(topic["implementation"])
    body += "<h2>Cost and boundaries</h2>" + para(topic["cost"])
    body += "<h2>Failure trace</h2>" + para(topic["failure"])
    body += "<h2>Verification</h2><ul>" + "".join(f"<li>{html.escape(check)}</li>" for check in topic["checks"]) + "</ul>"
    body += "<h2>Practice drill</h2>" + para(topic["drill"])
    body += "<h2>Decision note</h2>" + para(topic["decision"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in topic["mistakes"]) + "</ul>"
    body += "<h2>Connected lessons</h2><p>" + "; ".join(link(path) for path in related) + ".</p>"
    entry["body"] = body
    entry["data"].update(related=related, reading_minutes=max(6, round(len(re.findall(r"\b\w+\b", re.sub(r"<[^>]+>", " ", body))) / 155)))

for hub in hubs:
    entry = by_path[hub["path"]]
    group = [topic for topic in topics if topic["hub"] == hub["path"]]
    entry["data"]["modules"] = [{"title": hub["title"], "summary": hub["summary"],
                                 "lessons": [topic["path"] for topic in group]}]
    entry["data"]["resource_tabs"] = [
        {"title": "Web Development", "path": "web-tech/web-technology"},
        {"title": "Projects", "path": "web-tech/web-technology/project"},
        {"title": "Quizzes", "path": "web-tech/quizzes"}]
    entry["body"] = para(hub["overview"])
    entry["body"] += "<h2>Topics in this track</h2><ul>" + "".join(f'<li>{link(topic["path"])} — {html.escape(topic["summary"])}</li>' for topic in group) + "</ul>"
    entry["body"] += "<h2>Prerequisite paths</h2><p>" + "; ".join(link(path) for path in hub["bridges"]) + ".</p>"
    entry["body"] += "<h2>Neighbor track</h2><p>" + link(hubs[0]["path"] if hub == hubs[1] else hubs[1]["path"]) + ".</p>"

root_entry = by_path["web-tech/web-technology"]
for hub in hubs:
    group = [topic for topic in topics if topic["hub"] == hub["path"]]
    root_entry["data"]["modules"].append({"title": hub["title"], "summary": hub["summary"],
                                         "lessons": [hub["path"]] + [topic["path"] for topic in group]})
    root_entry["body"] += f'<h2>{link(hub["path"])}</h2><p>{html.escape(hub["summary"])}</p><ul>' + "".join(
        f'<li>{link(topic["path"])} — {html.escape(topic["summary"])}</li>' for topic in group) + "</ul>"
root_entry["updated_at"] = stamp

for path, targets in {
    "web-tech/frontend-application-architecture": [hubs[0]["path"]],
    "web-tech/state-and-trust": [hubs[1]["path"]],
    "web-tech/api-evolution-and-compatibility": [topics[0]["path"]],
    "web-tech/component-boundaries-and-state": [topics[1]["path"], topics[2]["path"]],
    "web-tech/performance-budget-and-layout-stability": [topics[3]["path"]],
    "web-tech/output-escaping-and-csp": [topics[4]["path"], topics[5]["path"]],
    "web-tech/ci-release-gates": [topics[6]["path"]],
    "web-tech/observability-and-recovery": [topics[7]["path"]],
}.items():
    entry = by_path[path]
    entry["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": len(hubs), "new_lessons": len(topics),
                  "web_development_routes": sum(entry["path"].startswith("web-tech/") for entry in entries)}))
