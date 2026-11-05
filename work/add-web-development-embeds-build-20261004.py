"""Add original embedded-interface and frontend-build curriculum entries."""

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
    return '<a href="/' + html.escape(path, quote=True) + '">' + html.escape(by_path[path]["title"]) + "</a>"


hubs = [
    {
        "path": "web-tech/embedded-interfaces-and-cross-window-contracts",
        "title": "Embedded Interfaces and Cross-Window Contracts",
        "summary": "Constrain frames and popups, then exchange small typed messages across explicit origins and lifetimes.",
        "overview": "An embedded interface is a separate document with its own origin, lifecycle, storage behavior, and failure modes. Treat the frame as an integration boundary rather than a child component. This track follows a private inspection report that opens a supplier viewer and receives a selected reference. It covers frame capabilities, message validation, channel lifetimes, popup returns, and a usable fallback when embedding is blocked. The host keeps authority over case data; the embedded document receives only the minimum context for the current task.",
        "bridges": ["web-tech/embedding-and-browser-capability-headers", "web-tech/privacy-aware-external-integrations"],
    },
    {
        "path": "web-tech/frontend-build-and-artifact-integrity",
        "title": "Frontend Build and Artifact Integrity",
        "summary": "Pin dependency resolution, review install behavior, and deploy a coherent set of hashed assets.",
        "overview": "A frontend release is more than a source commit. It includes the resolved dependency tree, install-time code, build configuration, emitted files, and cache behavior after deployment. This track follows a case dashboard that must load the same reviewed application in two regions and survive a rollback. It covers locked installs, dependency admission, browser asset integrity, and atomic manifest rollout. Each lesson separates evidence that a build is repeatable from evidence that a particular artifact is safe to execute.",
        "bridges": ["web-tech/ci-release-gates", "web-tech/dependency-integrity-and-update-window"],
    },
]

topics = [
    {
        "hub": 0,
        "slug": "frame-sandbox-capabilities-and-fallback",
        "title": "Frame Sandbox, Capabilities, and Fallback",
        "summary": "Give an embedded document only the browser powers its task requires and preserve a non-frame path.",
        "concept": "An iframe loads a separate document. Same-origin policy limits direct DOM access across origins, while sandbox tokens and permission policy control what that document may do. These controls answer different questions: origin separation limits reads, sandbox limits actions, and permission policy limits selected browser features. None authenticates a user or authorizes access to a case. Define the embedded feature as a task with a narrow input and output before selecting frame attributes. A blocked frame must not become a blocked report.",
        "case": "A supplier viewer displays one attachment for case 62. The host page sends only a short-lived attachment reference, never the full case record or a long-lived session token. The viewer needs script execution to render pages, but it does not need top-level navigation, popups, downloads, camera, or microphone. The host also exposes an ordinary link to a server-generated accessible preview. If the viewer origin is down or an enterprise policy blocks frames, reviewer 47 can still read the attachment summary and continue the report.",
        "implementation": "Serve the viewer from a distinct origin when its code has a different trust owner. This viewer needs allow-scripts and allow-same-origin so messages carry its real origin; keep top-level navigation and popup powers absent. Without allow-same-origin, a sandboxed frame has an opaque origin serialized as null, so the host cannot check a specific sender origin or target that origin exactly. Never grant both script and same-origin tokens to an untrusted frame served from the host's own origin and assume the sandbox still isolates it. Set an explicit frame title, a bounded size, and a loading state with a timeout. Keep attachment authorization on the server and expire references independently of frame lifetime. The load event is not proof that the viewer succeeded, so require a small ready message before removing fallback instructions.",
        "cost": "Each frame is another document with network requests, script memory, layout work, and potentially separate storage. Lazy loading can defer that cost, but a frame near the current task may become late to respond. Count requests and retained memory with a realistic attachment, then cap concurrent viewers. The fallback preview costs an extra rendering path; that cost is justified only if it remains tested and available. Security review must track the exact sandbox tokens because one added token can change the power of every future viewer release.",
        "failure": "The viewer changes its route after loading. The frame load event fires, but the expected page does not initialize, leaving a blank rectangle and no way forward. Another failure grants both script and same-origin powers to a same-origin frame, weakening the assumed sandbox boundary. Simulate an unavailable origin, a blocked permission, an oversized document, a malicious top-navigation attempt, and a user who cannot operate the viewer with a pointer. Check that the host keeps its own case state and that the preview link still works.",
        "drill": "Document the viewer's exact allowed actions in a review record. Load case 62 with a valid reference and reject the same reference after expiry. Disable frame execution and use the server preview. Attempt a top-level redirect from the viewer and verify that the host does not move. Compare request and memory cost with one and four open attachments, then set a concurrency rule backed by those measurements.",
        "decision": "Treat the frame as an optional, separately owned capability; the host and server retain case authority.",
        "code": "function viewerCapabilities(requested) {\n  const permitted = new Set(['allow-scripts', 'allow-same-origin']);\n  return requested.filter(capability => permitted.has(capability));\n}\nconsole.log(viewerCapabilities(['allow-scripts', 'allow-same-origin', 'allow-top-navigation', 'allow-downloads']).join(','));\n// Output: allow-scripts,allow-same-origin",
        "checks": ["The server rejects expired attachment references.", "Frame failure leaves a usable preview path.", "The browser blocks unapproved top-level navigation."],
        "mistakes": ["Treating the frame load event as successful application readiness.", "Granting every sandbox token to avoid integration work.", "Sending the full case record to a viewer that needs one attachment."],
        "related": ["web-tech/embedded-widget-storage-and-fallback", "web-tech/private-asset-download-revocation-and-expiry"],
    },
    {
        "hub": 0,
        "slug": "postmessage-origin-source-schema-and-replay",
        "title": "Cross-Window Messages: Origin, Source, Schema, and Replay",
        "summary": "Accept a frame message only from the expected document and only for the current interaction.",
        "concept": "Window messaging crosses a document boundary by sending structured data to a Window reference. A sender chooses a target origin; a receiver checks the message origin and, when it has one, the expected source window. Neither check validates the message body or grants permission for the requested operation. Model messages as versioned commands with a small allowlist, size limit, and correlation ID. A message is an input from another execution context, even when both teams work on the same product.",
        "case": "The supplier viewer posts that attachment reference 47 was selected. The host expects a message from the viewer's exact origin and the current iframe window. It also expects protocol version 3, a selection command, the active request ID, and an attachment ID in the case's allowed set. A different tab can send a message to the host, and the viewer can be replaced by a later navigation. Neither message should update the report. The host does not echo private report text back merely because a frame asks for it.",
        "implementation": "When sending, specify the exact recipient origin. This contract assumes the distinct-origin frame retains its real origin; an opaque sandbox origin appears as null and cannot be checked against a unique sender origin. On receipt, compare event.origin with the configured origin string without adding a path or trailing slash, and compare event.source with the current frame reference. Validate a plain-data schema before reading nested fields. A request ID ties a response to the active selection; retire IDs after use so a late message cannot repeat the action. Recheck authorization on the host server before changing durable state. If the frame navigates, invalidate outstanding requests and establish a fresh handshake. Never turn message text into HTML or script. Log a rejection category without storing payloads.",
        "cost": "A fixed-size message and map lookup are O(1) for a bounded schema. Validating a large object or recursively cloning it can consume memory and block the main thread, so limit depth and bytes at the protocol boundary. Keeping pending requests forever leaks timers and closures; expire them. Versioning adds a little coordination work, but it lets host and viewer roll out at different times without silently treating unknown fields as authority. Measure rejection rates during rollout without recording the sensitive attachment ID in analytics.",
        "failure": "The host checks only the payload type. A promotional frame sends the same command shape and selects an unrelated attachment. A second build checks origin but accepts a response for an old request after the reviewer has switched cases. Reproduce both cases, then attempt an object with an unexpected array, a very long string, and a missing protocol version. Each should be ignored. Also test the intended viewer after it reloads and after the host changes cases; the valid path must reestablish a fresh request instead of reusing old state.",
        "drill": "Generate two frame references in a test rig. Send the same selection payload from each and show that only the expected source can pass. Change the active request ID and replay the earlier response. Reject an attachment ID absent from the current case's allowlist. Then deploy a version-4 viewer against a version-3 host and confirm the host reports an unsupported protocol state with a manual selection fallback.",
        "decision": "The receiver validates origin, source, shape, correlation, and server authority as separate gates.",
        "code": "function acceptViewerMessage(event, expectedSource, pendingRequest) {\n  const message = event.data;\n  return event.origin === 'https://viewer.inspection.test' && event.source === expectedSource &&\n    message?.version === 3 && message?.type === 'attachment-selected' &&\n    message?.requestId === pendingRequest && Number.isInteger(message?.attachmentId);\n}\nconst viewerWindow = {};\nconsole.log(acceptViewerMessage({ origin: 'https://viewer.inspection.test', source: viewerWindow, data: { version: 3, type: 'attachment-selected', requestId: 'r47', attachmentId: 62 } }, viewerWindow, 'r47'));\n// Output: true",
        "checks": ["Wrong origin and wrong source are each rejected.", "Stale request IDs cannot repeat a selection.", "Server authorization still decides durable changes."],
        "mistakes": ["Using a wildcard target origin for private messages.", "Treating a matching origin as a valid schema.", "Keeping a request ID active after case change."],
        "related": ["web-tech/embedding-and-browser-capability-headers", "web-tech/object-level-authorization-for-reads-and-writes"],
    },
    {
        "hub": 0,
        "slug": "messagechannel-lifetime-and-request-correlation",
        "title": "MessageChannel Lifetime and Request Correlation",
        "summary": "Use a dedicated port for a bounded conversation and close it when the frame changes or the task ends.",
        "concept": "A MessageChannel creates two linked ports. A host can transfer one port to a frame, leaving subsequent traffic on that connection rather than on a global window message listener. The port does not make an untrusted frame safe: the initial transfer still needs an exact target origin, and every application message still needs schema and authority checks. Its benefit is ownership of a conversation. Give each channel a task ID, a state machine, a timeout, and an explicit close rule.",
        "case": "Reviewer 47 asks a document viewer for page 29 of a private attachment. The host creates a port pair and transfers one end after the viewer declares readiness. The viewer sends a page-ready response, then small progress updates while preparing accessible text. If the reviewer closes the attachment or switches cases, the host closes its port and cancels the server request. A late progress message is ignored. Another viewer instance gets a new channel; it cannot inherit the old task's authority simply by occupying the same frame element.",
        "implementation": "Keep the channel in an owner object tied to the currently mounted viewer and attachment reference. Establish the first handshake over window messaging with origin and source checks, then transfer a port with an exact target origin. Define states such as waiting, active, completed, canceled, and expired. Each message carries a task ID, version, type, and bounded payload. Close both available endpoints during teardown and remove handlers and timers. A port can outlive a frame's visible DOM if references remain, so navigation and account switch must trigger cleanup. Server requests still verify the current user and attachment; a port is not a bearer credential.",
        "cost": "A channel reduces unrelated global-message traffic and makes cleanup observable, but each live task holds ports, handlers, buffers, and possibly workers. Set a small maximum for concurrent tasks and progress frequency. A progress event for every decoded line can overwhelm the main thread; coalesce updates at a useful cadence. A correlation map lookup is O(1) on average, while retained messages and unfinished promises grow with unresolved tasks. Track active channels, timeouts, and cancellation completion, then test the limits on slow devices.",
        "failure": "The viewer reloads but the host keeps the old port and marks the new viewer ready because it reuses the same iframe node. Page-ready from task 29 arrives after task 30 has started, and the host shows the wrong attachment. Force a reload during transfer, close the report before the first response, and switch accounts while progress is pending. In each case, the old channel must close and no old payload may appear. The new task must request a fresh port and fresh server authorization.",
        "drill": "Model the channel owner as an object with task ID and state. Start task 29, cancel it, and then deliver its completion message. The state reducer must leave the current task unchanged. Start task 30 and count the active ports before and after teardown. Add a timeout and a manual retry control. Confirm that a failed transfer does not hide the attachment's ordinary preview link.",
        "decision": "Use ports for a scoped conversation, not as a substitute for message validation or server permission.",
        "code": "function applyViewerProgress(currentTask, incoming) {\n  if (currentTask.state !== 'active' || incoming.taskId !== currentTask.id) return currentTask;\n  return { ...currentTask, completedPages: Math.min(incoming.completedPages, currentTask.totalPages) };\n}\nconsole.log(applyViewerProgress({ id: 30, state: 'active', completedPages: 2, totalPages: 47 }, { taskId: 29, completedPages: 47 }).completedPages);\n// Output: 2",
        "checks": ["Port count returns to baseline after viewer teardown.", "Late task messages do not change the current attachment.", "A failed channel leaves the preview path usable."],
        "mistakes": ["Leaving transferred ports alive after a route change.", "Treating the port object as proof of user authorization.", "Sending unbounded progress events for every decoded unit."],
        "related": ["web-tech/workers-messages-transfer-and-cancellation", "web-tech/stream-cancellation-and-partial-result-contract"],
    },
    {
        "hub": 0,
        "slug": "popup-handoff-return-and-window-ownership",
        "title": "Popup Handoff, Return, and Window Ownership",
        "summary": "Separate a user-initiated external handoff from the server-confirmed result and its fallback route.",
        "concept": "A popup is another top-level document, not an extension of the opener's state. Browsers may block a popup without a user gesture; navigation can change its origin after opening; an opener relationship can expose more than the workflow needs. Use a popup only when the user benefits from keeping the host task visible. Define a full-page redirect or ordinary link for blocked windows. Treat a message from the returning window as a hint to refresh server state, never as proof that a transaction completed.",
        "case": "A reviewer opens a supplier confirmation window for attachment 62. The host records a one-use handoff ID and displays a pending state. The supplier may send a completion hint, but the host asks its own server for the status of that handoff before marking the attachment verified. If the popup is blocked, the reviewer follows a same-task redirect link. If the popup closes early, the host offers retry or cancel without discarding the case note. The callback contains no full report and no long-lived secret.",
        "implementation": "Start the window from an explicit click and record the handoff on the server before opening it. Scope the return to a short-lived ID tied to the user's current case and expire it after use. If messaging is part of the flow, check exact origin, source, version, and ID; then query server status. Avoid unnecessary opener access by using a redirect-based return or an isolation choice compatible with the integration. Detect a blocked popup by the opening result and show the redirect route. Poll only within a bounded interval, stop on account switch, and restore focus to the initiating control when the task ends. Keep the final server write idempotent.",
        "cost": "Popup polling consumes requests while the supplier is idle. Use a modest interval, visible pending state, and a clear timeout; an event hint can shorten the wait but cannot replace a verified read. A second window also creates attention and accessibility costs, so compare task completion against a full-page redirect before adopting it. One-use handoff records require storage and expiry jobs; the storage cost is small, but orphaned records and retries must have defined cleanup. Measure completion rate, blocked-window fallback use, and stale pending duration without logging private case contents.",
        "failure": "The supplier window sends a success message for handoff 29 while the host now shows handoff 30. If the host trusts the message, it marks the wrong attachment complete. Test that mismatch, a blocked popup, a window closed without return, an expired callback, and a duplicated server result. Also test keyboard and screen-reader focus after the popup closes. The host should never change durable case state from the message alone, and a retry should not create two supplier confirmations.",
        "drill": "Create handoff 29, switch to case 30, and deliver the old completion hint. Confirm that the host performs no status update for case 30. Repeat with a valid hint and let the server return pending, then completed. Block window opening and finish through the redirect route. Count polling requests until timeout, and verify that closing the host page does not leave an unlimited polling job running.",
        "decision": "Let the server settle the handoff; the popup only helps the user reach and return from it.",
        "code": "function mayRefreshHandoff(activeHandoff, returnHint) {\n  return activeHandoff.status === 'pending' && returnHint.handoffId === activeHandoff.id;\n}\nconsole.log(mayRefreshHandoff({ id: 30, status: 'pending' }, { handoffId: 29 }));\n// Output: false",
        "checks": ["A blocked popup has a complete redirect route.", "Return hints trigger verified status reads only.", "Expired and duplicate handoffs cannot settle another case."],
        "mistakes": ["Calling a popup message the final server result.", "Opening a window outside a user action and hiding the blocked state.", "Polling indefinitely after navigation or account switch."],
        "related": ["web-tech/hosted-checkout-session-and-browser-return", "web-tech/navigation-history-and-page-lifecycle"],
    },
    {
        "hub": 1,
        "slug": "locked-dependency-resolution-and-clean-installs",
        "title": "Locked Dependency Resolution and Clean Installs",
        "summary": "Make the reviewed source tree resolve the same package graph in continuous integration.",
        "concept": "A package manifest expresses intended dependencies; a lockfile records the resolved graph and integrity metadata for an install. A clean-install command checks the manifest against that lock and refuses to rewrite it when they disagree. This makes dependency resolution repeatable within the same package manager and configuration. It does not prove that every package is safe, that install scripts are harmless, or that two operating systems emit identical bundles. Track the toolchain and install flags alongside the lockfile.",
        "case": "A case dashboard build passes on a developer laptop but fails in release validation after a transitive parser update. The team commits the lockfile with the manifest and pins the package manager version used by CI. A new dependency request changes both files in one reviewed change, with a recorded reason and bundle impact. The release job uses a clean install and rejects a manifest-only edit. Reviewer 47 sees the same dashboard behavior in staging that was tested for case 62, rather than a package graph resolved hours later from a broad version range.",
        "implementation": "Commit the manifest and lockfile together. In CI, use the package manager's frozen or clean-install mode with a pinned toolchain and the same relevant configuration as development. Check that the selected workspace and optional dependencies match the target deployment. Maintain a short update window: propose version changes, inspect transitive movement, run affected tests, and record any exception. Do not edit lockfile integrity fields by hand or rely on a locally cached node_modules directory as release evidence. Store the resolved graph digest with the build record so an incident can identify which packages actually reached a release.",
        "cost": "A clean install often downloads more than an incremental developer install, but it removes hidden local state from release validation. Caching package archives can reduce time without caching an unverified installed tree. The lockfile can be large; review tooling should highlight added packages, lifecycle scripts, license changes, and unexpected registries instead of asking reviewers to read every hash. Hashing the manifest and lockfile is O(file size); resolving and installing the graph is dominated by package count, archive transfer, and filesystem work.",
        "failure": "A release job runs a non-frozen install and silently rewrites the lockfile before bundling. The source commit no longer describes the deployed graph. Another job pins package versions but uses a different install flag, changing peer resolution. Reproduce a manifest-lock mismatch and require the job to fail before the build starts. Test a cold cache, a corrupted archive, a missing optional dependency on the target platform, and a new package with an install script. Each outcome needs an explicit failure or reviewed exception, never a quiet fallback to an unrecorded graph.",
        "drill": "Change the declared parser range without updating the lockfile and run the release install; it should stop. Then update the lock in a separate review and compare added packages, scripts, and output size. Build from two clean workspaces with the same toolchain and configuration, compare artifact manifests, and explain any byte difference. Record a rollback target with its dependency graph digest rather than only the branch name.",
        "decision": "A lockfile fixes resolution for review; release evidence also includes toolchain, configuration, and emitted artifacts.",
        "code": "function lockMatchesManifest(manifest, lock) {\n  return Object.entries(manifest.dependencies).every(([name, range]) => lock.packages[name]?.requested === range);\n}\nconsole.log(lockMatchesManifest({ dependencies: { 'case-parser': '^4.7.0' } }, { packages: { 'case-parser': { requested: '^4.6.0' } } }));\n// Output: false",
        "checks": ["A manifest-lock mismatch fails before bundling.", "Build records include package-manager version and graph digest.", "Cold-cache release installation follows the same locked graph."],
        "mistakes": ["Treating a lockfile as a safety audit.", "Reusing an unexplained local installed tree for a release.", "Updating the manifest while leaving the lockfile stale."],
        "related": ["web-tech/ci-release-gates", "web-tech/dependency-integrity-and-update-window"],
    },
    {
        "hub": 1,
        "slug": "dependency-admission-scripts-and-provenance",
        "title": "Dependency Admission, Install Scripts, and Provenance",
        "summary": "Review new package authority and build-time code before it enters the release graph.",
        "concept": "A dependency is executable code in the browser bundle, the build machine, or both. Package metadata, signatures, provenance statements, and vulnerability feeds provide different evidence. A signature can indicate that bytes match a registry record; provenance can describe a publishing route; neither proves the code is harmless. Install lifecycle scripts may run before tests and can read CI environment data. Admit a dependency by its task, publisher history, transitive graph, scripts, permissions, license, and update plan.",
        "case": "The dashboard team considers a compact document renderer for case 62. Its published archive adds 47 transitive packages and a postinstall script. The feature needs only one file format and can instead use an existing server preview. The team records the bundle cost, build-time script behavior, and maintenance owner before deciding. If they keep the package, CI runs with a token scope that cannot publish, then verifies the release artifact. A clean vulnerability report alone does not approve the package because new or targeted compromises may have no advisory.",
        "implementation": "For each new direct dependency, capture why it is needed and inspect its resolved transitive additions. Check whether install scripts run, what they do, and what secrets or network endpoints the build job can reach. Reduce CI token scope and isolate untrusted build steps where practical. Verify package integrity and available signatures or provenance, but treat missing attestations as a risk signal to investigate rather than a universal proof of compromise. Triage advisories by reachable code path and deployment context; record a deadline and compensating control for exceptions. Review updates in bounded batches so a failure can be traced to a small graph change.",
        "cost": "Manual admission costs engineering time, especially for a broad graph, so focus deep review on new and changed packages and automate inventory collection. A dependency with a small compressed bundle can still run a broad install script or bring server-side risk. Conversely, a large package may be safe enough but expensive for users on slow connections. Measure build time, browser bytes, parse time, and maintenance load. The inventory itself should be retained per release to support incident response without storing build secrets.",
        "failure": "A dependency update introduces a postinstall command that reads an environment token, while the normal browser tests still pass. Another package has a known advisory in code never reached by the application; a blanket failure with no triage blocks release without reducing the actual risk. Simulate both cases in a review exercise. Confirm that the build job has least-privilege credentials, unexpected scripts are surfaced, and an exception states the affected version, reason, owner, and expiry. A compromised archive must never be accepted because its version number matches the manifest.",
        "drill": "Compare two lockfile revisions for the renderer request. Count new packages and detect new lifecycle scripts. Build a minimal feature without the renderer, then with it, and record browser byte and parse changes. For one advisory, trace whether the vulnerable path is included and callable in the deployed bundle. For one unsigned package, document the remaining evidence rather than labeling it automatically safe or unsafe.",
        "decision": "Approve dependency authority from several independent signals and keep the release graph small enough to inspect.",
        "code": "function admissionNeedsReview(change) {\n  return change.newPackages > 0 || change.newInstallScripts > 0 || change.publisherChanged;\n}\nconsole.log(admissionNeedsReview({ newPackages: 47, newInstallScripts: 1, publisherChanged: false }));\n// Output: true",
        "checks": ["New install scripts appear in the change review.", "CI credentials expose only required operations.", "Advisory exceptions have an owner and expiry."],
        "mistakes": ["Calling a clean advisory scan proof of safety.", "Ignoring code that runs during installation because it is not bundled.", "Adding a package without a maintenance owner."],
        "related": ["web-tech/dependency-integrity-and-update-window", "web-tech/telemetry-shapes-redaction-and-cardinality"],
    },
    {
        "hub": 1,
        "slug": "external-asset-integrity-and-module-resolution",
        "title": "External Asset Integrity and Module Resolution",
        "summary": "Pin the browser bytes of external scripts and keep module resolution tied to a reviewed release.",
        "concept": "A browser may fetch JavaScript or CSS from another origin after the HTML document arrives. An integrity value lets the browser compare received bytes against an expected digest before executing or applying the asset. Cross-origin integrity also needs a compatible CORS response. An import map controls how module specifiers resolve in a document, but it is not a general rule for workers or ordinary script src attributes. These mechanisms protect different steps; neither replaces a content security policy, dependency review, or a coherent deployment manifest.",
        "case": "The case dashboard loads a reviewed charting module from an external asset host. The release manifest records its exact URL and digest. If the asset host serves altered bytes, the browser refuses that module and the dashboard shows a text summary for the affected chart. The import map points the named chart module to the reviewed release path and is shipped before application modules use it. A worker that processes scan thumbnails has its own explicit module URL; the team does not assume the document import map governs the worker.",
        "implementation": "Generate integrity metadata from the final deployed asset bytes, after minification and any transformation. Pair external script or style fetches with the appropriate CORS setting and test the response headers in the target environment. Keep import-map entries and their asset paths in the same release unit as the HTML that uses them. If the platform supports integrity metadata in an import map, verify that exact behavior in the browser targets; otherwise pin external modules through a build or direct element integrity contract. A failed asset needs a visible fallback, not a silent missing chart. Treat unexpected CDN redirects and mutable URLs as release failures.",
        "cost": "Digest comparison is linear in downloaded bytes and normally small beside transfer and parsing, but every external request adds latency and failure surface. A self-hosted immutable asset may reduce cross-origin complexity while moving bandwidth and patch ownership to your service. Import maps can simplify module names but add a deployment coordination point: a stale HTML document may resolve a name to an asset removed by a newer release. Retain old hashed assets for the maximum supported document lifetime, and measure failed loads before cleanup.",
        "failure": "A CDN optimizer rewrites the file after the team computed its digest. The browser blocks the chart module, while the rest of the case page continues. Another release updates the import map but deletes the previous hashed module before open tabs refresh. Reproduce a mismatched digest, a missing CORS header, a stale open tab, and a worker import that ignores the document map. The page should state which function is unavailable and keep the text report usable. Rollback must restore a matching HTML-map-asset set.",
        "drill": "Build release 47 with a hashed chart asset and record its digest. Mutate one byte in a test server response; prove that the browser blocks execution and shows the text fallback. Serve release 48 HTML while retaining release 47 assets, then remove one old asset in staging to observe open-tab behavior. Record how long old assets must remain and which telemetry proves they are no longer requested.",
        "decision": "Bind external browser bytes and module paths to one reviewed release, with an explicit failure path.",
        "code": "function assetMatchesRelease(asset, release) {\n  return asset.releaseId === release.id && release.integrityByPath[asset.path] === asset.integrity;\n}\nconsole.log(assetMatchesRelease({ releaseId: 47, path: '/assets/chart-47.js', integrity: 'sha384-approved' }, { id: 47, integrityByPath: { '/assets/chart-47.js': 'sha384-approved' } }));\n// Output: true",
        "checks": ["Changed bytes fail the integrity check in a browser test.", "A missing chart leaves a text equivalent.", "Open tabs can still fetch their release's hashed assets."],
        "mistakes": ["Computing a digest before a CDN rewrites the file.", "Assuming an import map changes worker imports.", "Deleting old hashed assets during a rolling release."],
        "related": ["web-tech/content-negotiation-and-compression-contracts", "web-tech/accessible-graphic-controls-and-text-equivalents"],
    },
    {
        "hub": 1,
        "slug": "artifact-manifest-rollout-and-rollback-coherence",
        "title": "Artifact Manifest, Rollout, and Rollback Coherence",
        "summary": "Promote an immutable frontend artifact with its asset list and keep older documents loadable.",
        "concept": "A frontend deployment is a set of related bytes: HTML, JavaScript, CSS, worker files, images, and sometimes an import map. A source commit alone does not identify the exact set served to users. Build once, record a manifest of digests, and promote that artifact between environments. Give immutable assets content-based names and serve HTML with an appropriate revalidation policy. A rollback must restore the compatible document and server contract while retaining assets requested by already open tabs.",
        "case": "Release 47 of the case dashboard works in two regions. Release 48 adds a new report panel and moves a worker file. During a staged rollout, some users keep release-47 HTML open while a regional cache serves release-48 assets. The deployment process preserves all release-47 hashed files, publishes release-48 files first, then switches the HTML pointer. If error rates rise, operators switch the document pointer back to release 47 without deleting either asset set. A release record names both the asset manifest and the API compatibility window.",
        "implementation": "Produce the manifest from final build output, including paths, byte sizes, digests, and toolchain identity. Upload immutable assets before changing the document or edge pointer. Verify every manifest path from each target region and check that the response bytes match the digest. Keep HTML short-lived or revalidated so new navigation can pick up the current pointer; do not apply the same cache rule to hashed assets. Design API changes to serve both current and still-open client builds during the rollout window. Revoke an old asset only after observing no supported clients request it or after a stated maximum lifetime has passed.",
        "cost": "Retaining two or more releases consumes storage, but usually much less than the cost of broken sessions. The manifest check is O(number of emitted assets) requests if done naively; sample or batch checks while ensuring every critical entry is covered. An overly long HTML cache can hold users on an old build, while an overly short hashed-asset cache wastes bandwidth. Track failed chunk loads, mixed-version API errors, rollback time, and oldest active client version. A service worker may add another cache layer and must be included in the rehearsal.",
        "failure": "A deployment switches HTML before uploading a lazy-loaded chunk to one region. The first page paints correctly, but opening the report panel fails. Another rollback restores HTML while a worker still points at a removed file. Rehearse both failures across a cold browser and an open tab. Verify the old and new manifests during promotion, after rollback, and after cache propagation. The operator must be able to identify exactly which digest is missing, rather than diagnosing a generic blank page.",
        "drill": "Construct manifest 47 with an entry for the report panel, then publish manifest 48 with one new chunk. Before flipping the pointer, simulate a missing regional object and require the promotion gate to stop. After promotion, keep a release-47 tab open and trigger its lazy load. Roll back to 47 while a release-48 tab remains open, then verify both clients can load their remaining assets and call a compatible API.",
        "decision": "Promote one immutable artifact set; switch the document pointer only after every required asset is available.",
        "code": "function mayPromote(manifest, availablePaths) {\n  return manifest.assets.every(asset => availablePaths.has(asset.path));\n}\nconsole.log(mayPromote({ assets: [{ path: '/assets/case-47.js' }, { path: '/assets/report-47.js' }] }, new Set(['/assets/case-47.js'])));\n// Output: false",
        "checks": ["Every manifest asset exists before the HTML pointer changes.", "An old open tab can lazy-load after the new release.", "Rollback restores compatible HTML and API behavior."],
        "mistakes": ["Rebuilding separately in staging and production.", "Treating a successful first paint as proof all lazy chunks exist.", "Deleting old assets as soon as a new HTML pointer is live."],
        "related": ["web-tech/ci-release-gates", "web-tech/regional-routing-static-and-private-cache-boundaries"],
    },
]

assert len(hubs) == 2 and len(topics) == 8
for number, hub in enumerate(hubs):
    path = hub["path"]
    assert path not in by_path
    entry = copy.deepcopy(by_path["web-tech/production-signals-and-incident-decisions"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                 title=hub["title"], summary=hub["summary"], sort_order=2940 + number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": path,
                     "content_format": "html", "seo_ready": False, "modules": [],
                     "resource_tabs": [{"title": "Web Development", "path": "web-tech/web-technology"},
                                       {"title": "Projects", "path": "web-tech/web-technology/project"},
                                       {"title": "Quizzes", "path": "web-tech/quizzes"}]}
    entries.append(entry)
    by_path[path] = entry

for number, topic in enumerate(topics):
    path = "web-tech/" + topic["slug"]
    assert path not in by_path
    subprocess.run(["node", "--check", "--input-type=module"], input=topic["code"],
                   text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path["web-tech/trace-context-across-request-and-job"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                 title=topic["title"], summary=topic["summary"], sort_order=2950 + number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    hub_path = hubs[topic["hub"]]["path"]
    related = [hub_path] + ["web-tech/" + item["slug"] for item in topics
                            if item["hub"] == topic["hub"] and item["slug"] != topic["slug"]] + topic["related"]
    body = p(topic["concept"]) + "<h2>Working case</h2>" + p(topic["case"])
    body += '<h2>Implementation boundary</h2><pre><code class="language-javascript">' + html.escape(topic["code"], quote=False) + "</code></pre>" + p(topic["implementation"])
    body += "<h2>Cost and boundaries</h2>" + p(topic["cost"]) + "<h2>Failure trace</h2>" + p(topic["failure"])
    body += "<h2>Verification</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in topic["checks"]) + "</ul>"
    body += "<h2>Practice drill</h2>" + p(topic["drill"]) + "<h2>Decision note</h2>" + p(topic["decision"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in topic["mistakes"]) + "</ul>"
    entry["body"] = body
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": hub_path,
                     "content_format": "html", "seo_ready": False, "kind": "tutorial",
                     "author_path": "authors/aitrove-editorial", "reading_minutes": 7, "related": related}
    entries.append(entry)
    by_path[path] = entry

for number, hub in enumerate(hubs):
    group = [item for item in topics if item["hub"] == number]
    entry = by_path[hub["path"]]
    entry["data"]["modules"] = [{"title": hub["title"], "summary": hub["summary"],
                                  "lessons": ["web-tech/" + item["slug"] for item in group]}]
    entry["body"] = p(hub["overview"]) + "<h2>Topics in this track</h2><ul>" + "".join(
        "<li>" + link("web-tech/" + item["slug"]) + " — " + html.escape(item["summary"]) + "</li>" for item in group) + "</ul>"
    entry["body"] += "<h2>Prerequisite paths</h2><p>" + "; ".join(link(path) for path in hub["bridges"]) + ".</p>"
    entry["body"] += "<h2>Neighbor track</h2><p>" + link(hubs[1 - number]["path"]) + ".</p>"

root_entry = by_path["web-tech/web-technology"]
for number, hub in enumerate(hubs):
    group = [item for item in topics if item["hub"] == number]
    root_entry["data"]["modules"].append({"title": hub["title"], "summary": hub["summary"],
                                           "lessons": [hub["path"]] + ["web-tech/" + item["slug"] for item in group]})
    root_entry["body"] += "<h2>" + link(hub["path"]) + "</h2>" + p(hub["summary"]) + "<ul>" + "".join(
        "<li>" + link("web-tech/" + item["slug"]) + " — " + html.escape(item["summary"]) + "</li>" for item in group) + "</ul>"
root_entry["updated_at"] = stamp

crosslinks = {
    "web-tech/embedding-and-browser-capability-headers": [hubs[0]["path"], "web-tech/frame-sandbox-capabilities-and-fallback"],
    "web-tech/embedded-widget-storage-and-fallback": ["web-tech/postmessage-origin-source-schema-and-replay"],
    "web-tech/hosted-checkout-session-and-browser-return": ["web-tech/popup-handoff-return-and-window-ownership"],
    "web-tech/cross-tab-invalidation-and-version-checks": ["web-tech/messagechannel-lifetime-and-request-correlation"],
    "web-tech/ci-release-gates": [hubs[1]["path"], "web-tech/artifact-manifest-rollout-and-rollback-coherence"],
    "web-tech/dependency-integrity-and-update-window": ["web-tech/locked-dependency-resolution-and-clean-installs", "web-tech/dependency-admission-scripts-and-provenance"],
    "web-tech/module-splitting-and-interaction-budget": ["web-tech/external-asset-integrity-and-module-resolution"],
    "web-tech/regional-routing-static-and-private-cache-boundaries": ["web-tech/artifact-manifest-rollout-and-rollback-coherence"],
}
for path, targets in crosslinks.items():
    entry = by_path[path]
    entry["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": len(hubs), "new_lessons": len(topics),
                  "prose_words": {topic["slug"]: len(re.findall(r"\b[\w'-]+\b", " ".join(str(value) for key, value in topic.items() if key not in {"code", "checks", "mistakes", "related"}))) for topic in topics}}))
