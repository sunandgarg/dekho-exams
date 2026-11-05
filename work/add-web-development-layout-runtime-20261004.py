"""Add original CSS systems and browser execution lessons."""

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
    dict(path="web-tech/css-layout-and-interface-systems", title="CSS Layout and Interface Systems",
         summary="Choose layout constraints, component queries, cascade ownership, typography, and motion from real content.",
         overview="An interface can pass a single viewport screenshot and still fail when a long case title arrives, a sidebar narrows, a translated label grows, or a user asks for less motion. CSS is a constraint system: intrinsic sizes, container width, cascade order, font metrics, and user preferences all participate. These lessons treat layout rules as product contracts that can be inspected and tested. The case-review interface is the running example, with narrow panels and variable content rather than one fixed mockup.",
         bridges=["web-tech/responsive-interaction-contract", "web-tech/reflow-zoom-and-motion-preferences", "web-tech/component-boundaries-and-state"]),
    dict(path="web-tech/browser-execution-and-resource-lifecycle", title="Browser Execution and Resource Lifecycle",
         summary="Keep interaction work responsive by understanding tasks, workers, yielding, and resource ownership.",
         overview="Browser JavaScript shares a main thread with much of the work needed to respond to input and paint. An expensive parser or endless chain of microtasks can delay a visible update, even when the network is fast. A worker can move computation away from that thread, but messages, copies, cancellation, and cleanup become part of the contract. These lessons follow one case-review route through event ordering, background processing, cooperative work, and disposal when the route changes.",
         bridges=["web-tech/dom-events-progressive-enhancement", "web-tech/react-effects-and-request-races", "web-tech/performance-budget-and-layout-stability"]),
]

topics = [
    dict(path="web-tech/grid-flex-and-intrinsic-size-contracts", hub=0, title="Grid, Flex, and Intrinsic Size Contracts",
         summary="Use layout primitives according to the relationship between regions, then test long content and minimum sizes.",
         definition="Grid describes a two-dimensional relationship between tracks; Flexbox distributes items along one main axis. Neither one makes content automatically fit. An item often carries an automatic minimum size based on its contents, so a long unbroken case identifier can force a panel wider than the available space. Start by naming which dimensions are fixed, flexible, or content-led. Use minmax(0, 1fr) for a grid track that may shrink below its content minimum, and min-width: 0 for a flex or grid item whose contents need to wrap or clip deliberately. Then decide whether wrapping, scrolling, or truncation preserves the user's task.",
         case="The case review page has a queue rail and a detail panel. At a medium width, a long equipment code expands the detail track and pushes the action button beyond the viewport. The screen looks correct with short placeholder titles, so the defect reaches review only after real data loads. Give the detail track a shrinkable minimum, permit text wrapping, and keep the rail at a readable width. Inside the action row, use Flexbox for the buttons because their relationship is one-dimensional. Check zoom and long translated labels before declaring the layout stable.",
         code='.case-shell { display: grid; grid-template-columns: minmax(14rem, 18rem) minmax(0, 1fr); gap: 1.25rem; }\n.case-detail { min-width: 0; }\n.case-title { overflow-wrap: anywhere; }\n.case-actions { display: flex; flex-wrap: wrap; gap: 0.75rem; }\n@media (max-width: 48rem) { .case-shell { grid-template-columns: minmax(0, 1fr); } }', language="css",
         implementation="The outer grid expresses the rail/detail relationship, and the action row uses Flexbox because buttons may wrap along one axis. The media rule changes the page-level arrangement when the full shell no longer fits; the breakpoint is a consequence of content, not a device label. A queue item with a very long token still needs a wrapping policy. Do not add overflow: hidden to the whole page just to hide the defect. It can remove focus outlines, clipped actions, and content that should remain reachable.",
         cost="Grid and Flexbox layout both depend on the number and size of participating elements; changing a track can trigger layout work for descendants. That cost is usually lower than the human cost of a broken screen, but deeply nested measured layouts deserve profiling when updates are frequent. Wrapping a long identifier increases height and may shift content; truncation saves space but needs a way to reveal the full value. A single layout rule should not be optimized in isolation from readability and keyboard access.",
         failure="A developer uses grid-template-columns: 18rem 1fr and assumes the second track can always shrink. Its automatic minimum follows the long title, so horizontal scrolling appears at 400% zoom. Replacing the title with ellipsis hides the complete case identifier that reviewers need to compare. Set the track minimum explicitly, wrap the identifier, and test the action row after its height changes. Inspect scroll width and keyboard focus at narrow and zoomed sizes rather than approving only a screenshot at a wide viewport.",
         drill="Build the rail/detail screen with case IDs of 8, 47, and 120 characters. Compare grid tracks before and after minmax(0, 1fr), then change the action labels to a longer language. Record whether every control remains visible, reachable, and named. Resize the viewport and zoom the page to expose intrinsic-size pressure. If a region truly must scroll, make that a local, labeled scroll area rather than an accidental page-wide overflow.",
         decision="Choose the layout primitive from the relationship between regions, then test intrinsic minimums with the longest realistic content.",
         checks=["Long titles and identifiers wrap without creating page-wide horizontal overflow.", "Actions remain visible and keyboard reachable after the detail track shrinks.", "The rail/detail layout survives narrow width and high zoom with translated labels."],
         mistakes=["Assuming 1fr always shrinks below the content minimum.", "Hiding page overflow to conceal a layout defect.", "Truncating an identifier without a path to its full value."],
         related=["web-tech/responsive-interaction-contract", "web-tech/reflow-zoom-and-motion-preferences", "web-tech/accessible-names-and-native-controls"]),
    dict(path="web-tech/container-queries-for-reusable-panels", hub=0, title="Container Queries for Reusable Panels",
         summary="Adapt a panel to its own space instead of assuming the viewport predicts its width.",
         definition="A viewport media query knows the window size, while a container query can respond to the space a component actually receives. A case summary panel might occupy most of a phone screen, one column of a dashboard, or a narrow drawer on a desktop. The same viewport can therefore place it in very different widths. Mark a suitable ancestor as an inline-size query container and keep a simple stacked default. Add a wider arrangement only when the container has room for the content, not at an arbitrary phone/tablet category. Container size queries style descendants, so the queried element must be inside the declared container.",
         case="The case summary card uses a horizontal status row in the full review page. The same component is reused in a 19rem activity drawer, where its buttons collide, even on a wide monitor. A viewport breakpoint never fires because the monitor is wide. Give the drawer slot a container context and let the card switch to a compact stack according to that slot's inline size. Test it in both hosts and with a longer localized status. The card should not depend on a special class added by each parent route.",
         code='.case-summary-slot { container: case-summary / inline-size; }\n.case-summary { display: grid; gap: 0.75rem; }\n.case-summary__actions { display: flex; flex-wrap: wrap; gap: 0.5rem; }\n@container case-summary (min-width: 34rem) {\n  .case-summary { grid-template-columns: minmax(0, 1fr) auto; align-items: start; }\n}', language="css",
         implementation="The slot, not the card itself, is the named query container. Descendant styles can then respond when the slot crosses the content-derived threshold. Keep the default one-column layout useful if a browser does not apply the query. Name a container when nesting could cause an inner component to accidentally respond to a nearer, unrelated ancestor. A container query does not solve all page layout; the outer shell still needs a viewport or available-space decision for navigation and full-screen regions.",
         cost="Container queries add style evaluation when the container changes size, but the larger maintenance cost is selecting clear ownership boundaries. Too many nested query containers can make it hard to understand which size controls a descendant. A named container and a small set of content-based thresholds keep the rule inspectable. A component reused in several hosts often repays that cost by eliminating route-specific layout overrides. Verify browser targets and retain a usable stacked default for clients without the feature.",
         failure="An engineer puts container-type on .case-summary and writes a query that tries to restyle .case-summary itself. The expected layout never changes because size queries apply to descendants of the container, not the queried element in that form. Another engineer adds a second unnamed container around the card, changing which ancestor the rule reads. Put the context on the slot, use a name, and test both full-page and drawer hosts. Inspect computed styles at widths just below and above the threshold.",
         drill="Render one card inside a wide content region and a narrow side drawer at the same viewport size. Resize only the drawer and verify the card changes layout according to its own space. Add a longer action label and check wrapping near the threshold. Remove container support in a controlled test and confirm the stacked default still works. Then document which ancestor owns the component's width contract so future nesting does not silently change it.",
         decision="Use a container query for reusable pieces whose available space varies independently of the viewport.",
         checks=["The same card adapts in wide and narrow hosts at one unchanged viewport width.", "The stacked default remains usable when the container rule does not apply.", "Named-container behavior remains correct after an additional wrapper is inserted."],
         mistakes=["Using a viewport breakpoint for a component whose host width varies.", "Expecting a container to restyle itself through a descendant query.", "Allowing an unnamed nested container to change the query target silently."],
         related=["web-tech/responsive-interaction-contract", "web-tech/component-boundaries-and-state", "web-tech/web-components-and-shadow-boundaries"]),
    dict(path="web-tech/cascade-layers-and-design-token-ownership", hub=0, title="Cascade Layers and Design Token Ownership",
         summary="Make style precedence explicit and separate shared decisions from component exceptions.",
         definition="The CSS cascade resolves competing declarations using origin, importance, layer, specificity, and source order. A design token is a named custom property that carries a decision such as a spacing step or surface color into several components. Layers help define which group of normal declarations may override another before specificity becomes a fight. Put reset, foundation, component, and utility rules in a known order. Keep tokens near the scope that owns them: a global color may be shared, while a case-card density choice can belong to the card. Remember that unlayered normal author styles can outrank layered normal styles, so a stray rule outside the declared layer plan can defeat it.",
         case="A third-party button stylesheet enters the case dashboard and changes the review action's padding. The team adds an increasingly specific selector to fight it; a later dialog gets the wrong spacing anyway. Put vendor rules in a lower-priority layer, components above them, and a documented utility layer last for deliberate one-off overrides. Expose a compact spacing token for the review toolbar instead of repeating pixel values across the dashboard and drawer. Check focus and contrast after a theme change; changing one token can affect many screens.",
         code='@layer vendor, foundation, components, utilities;\n@layer foundation { :root { --space-review: 0.75rem; --surface-review: #f5f7fa; } }\n@layer components { .case-toolbar { display: flex; gap: var(--space-review); background: var(--surface-review); } }\n@layer utilities { .case-toolbar--compact { --space-review: 0.5rem; } }', language="css",
         implementation="Declare the layer order before importing or writing component rules, and place third-party CSS into its intended layer. The custom property override is scoped to the compact toolbar so it does not change unrelated pages. A token name should describe the decision it controls rather than encode a current value that may later change. Do not use !important as a routine escape from poor ordering. Important declarations have their own cascade behavior, so review them separately rather than assuming the normal layer order explains every result.",
         cost="Custom property resolution and layered style matching are ordinary style work, but a large token graph can be hard to debug when values cascade through many scopes. The main benefit is controlled change: one owned decision can update several related components without copying declarations. The main risk is a token that is too broad, so a harmless-looking update changes an inaccessible surface elsewhere. Test representative states, themes, and focus indicators whenever a shared color, spacing, or motion token changes.",
         failure="An unlayered .case-toolbar rule from a copied stylesheet takes precedence over the layered component rule. Engineers keep raising specificity inside @layer components, but the override remains in place. Inspect the computed style's cascade origin and layer, move the copied rule into its proper layer, and remove the specificity escalation. A second failure is a global spacing token used for both toolbar and error message, so a compact toolbar setting also compresses feedback. Scope the component token and retest both states.",
         drill="Add a vendor rule that changes toolbar padding and a local compact variant. Inspect which declaration wins before and after placing the vendor rule in its layer. Change --space-review at the card scope and verify only the intended region changes. Add an unlayered rule on purpose to see its precedence, then remove it. Review the resulting normal, focused, error, and disabled states in two themes. Record each token's owner and expected consumers.",
         decision="Use layers to state style precedence and tokens to name shared decisions; keep both scoped enough to review their effects.",
         checks=["Vendor, component, and utility declarations resolve in the planned order.", "A compact token override affects the toolbar without changing unrelated feedback.", "Theme changes preserve contrast and focus visibility across representative states."],
         mistakes=["Escalating specificity to fight an unlayered rule.", "Making a component-specific token global without reviewing all consumers.", "Assuming important declarations follow the same precedence as normal ones."],
         related=["web-tech/component-boundaries-and-state", "web-tech/web-components-and-shadow-boundaries", "web-tech/reflow-zoom-and-motion-preferences"]),
    dict(path="web-tech/font-loading-and-motion-fallbacks", hub=0, title="Font Loading and Motion Fallbacks",
         summary="Keep text usable during font loading and preserve meaning when animation is reduced.",
         definition="A font changes more than appearance: its character widths and line metrics can move buttons, headings, and form errors as it arrives. The fallback stack must be readable before the preferred font loads. Choose a font-display behavior from the task and measure the resulting layout shift and text availability, rather than assuming a custom face is free. Motion has a similar contract. Transitions may help show a panel change, but a user preference for reduced motion should keep state changes understandable without a moving effect. The interface must not use animation as the only signal that a case was saved.",
         case="A review page loads a custom font after the case panel appears. The longer loaded glyphs wrap a status label onto a second line, moving the Resolve button under the pointer. Separately, a sliding confirmation banner is the only sign that a note saved; when motion is reduced, the banner disappears before it can be read. Choose a stable fallback with close metrics, reserve space for key controls, and keep persistent text feedback. Reduce the movement while preserving the confirmation and focus destination.",
         code='@font-face { font-family: "Review Sans"; src: url("/fonts/review-sans.woff2") format("woff2"); font-display: swap; }\n.case-review { font-family: "Review Sans", system-ui, sans-serif; }\n.case-confirmation { transition: transform 180ms ease-out; }\n@media (prefers-reduced-motion: reduce) { .case-confirmation { transition: none; } }', language="css",
         implementation="The internal font asset and fallback are explicit. font-display: swap keeps fallback text available while the face loads; it can still shift layout when metrics differ. Inspect the actual typeface pair and adjust design or font metrics if the shift matters. The reduced-motion rule removes this transition but leaves the confirmation content in place. If the application has several animations, audit each one according to its role instead of applying a blanket rule that removes important visibility or progress cues. Keep save status in text and accessibility feedback independent of motion.",
         cost="A font file adds transfer, caching, and render work. Several weights can multiply that cost, so ship only those used by the route and check whether the system stack meets the design need. A swap can improve immediate text visibility at the cost of a later reflow; hiding text until load may avoid that shift but delay reading. Motion effects also cost rendering work, especially when they animate layout-affecting properties. Test interaction response and cumulative movement with cold cache, slower network, and longer localized strings.",
         failure="A visual test runs with the font cached and never sees the fallback state. In the field, first-time reviewers click a button just as the loaded font moves it. A fix that sets the text invisible until font load prevents the misclick but makes the page unreadable on a slow connection. Compare cold and warm loads, choose an appropriate fallback, and reserve stable action space. Then test reduced motion and verify the save message remains present and announced without relying on a slide effect.",
         drill="Clear the font cache and load the review page under a slower network profile. Capture the title and action positions before and after the font arrives. Try a system-font-only variant and compare readability and layout stability. Turn on reduced motion and complete a save; the confirmation must still be visible, readable, and tied to the action. Repeat with a long translated label, since metric differences often appear first in longer strings.",
         decision="Treat font loading and motion as behavior with fallback states, not as decoration added after the interaction contract is complete.",
         checks=["Text remains readable and controls stable enough during a cold font load.", "A save confirmation remains meaningful with reduced motion enabled.", "Long localized labels fit without moving a critical control during interaction."],
         mistakes=["Testing only a cached preferred font.", "Making animation the only save-status signal.", "Hiding all text until a font arrives to avoid a measured layout shift."],
         related=["web-tech/performance-budget-and-layout-stability", "web-tech/reflow-zoom-and-motion-preferences", "web-tech/accessible-feedback-and-keyboard"]),
    dict(path="web-tech/event-loop-tasks-microtasks-and-paint", hub=1, title="Event Loop Tasks, Microtasks, and Paint",
         summary="Know which queued work runs before the browser can respond and paint a changed state.",
         definition="JavaScript on a browser main thread runs one task to completion. Promise reactions and queued microtasks run after the current stack clears, before the browser gets the next opportunity to process another task and render. That ordering explains why a state update followed by heavy synchronous work can leave a loading indicator invisible until the work finishes. It also explains why recursively queueing microtasks can starve rendering: each new microtask joins the checkpoint before the browser moves on. Use microtasks for short ordering needs, not as a way to split CPU-heavy work into paint opportunities.",
         case="A reviewer imports 62 inspection rows. The click handler sets a 'Processing' label, then parses every row synchronously and immediately resolves the operation. On a modest device the label appears only after parsing, making the button seem dead. Moving the parser into a promise callback does not fix it if the callback is still a microtask and performs the same long work. The route needs a separate task boundary, a worker, or chunked processing with yields. The label also needs an accessible status path once it actually renders.",
         code='const order = [];\nsetTimeout(() => { order.push("next task"); console.log(order.join(" / ")); }, 0);\nPromise.resolve().then(() => order.push("microtask"));\norder.push("current task");\n// Output: current task / microtask / next task', language="javascript",
         implementation="The trace shows ordering in a simple runtime; a browser may perform rendering between suitable tasks, but this snippet does not prove that a paint occurred. A real UI check should observe when the processing label becomes visible relative to the import work. Keep synchronous handlers short and measure the slowest devices. If a chain of promise callbacks does CPU work without yielding to a future task, its total duration can still block input. Use a task boundary or a worker when the computation is material.",
         cost="Each task and microtask has scheduling overhead, though the larger cost is the work inside it. Splitting work into tiny units can waste time in scheduling, while one long unit delays input and paint. Measure both total completion time and interaction delay. A short microtask is appropriate for consolidating changes before a checkpoint; a long parser is not. Worker transfer adds another cost that may be worthwhile when it frees the main thread. Do not infer user-visible paint solely from console log order.",
         failure="A developer replaces the parser loop with Promise.resolve().then(parseAllRows) and marks the loading label before it. The import remains unresponsive because parseAllRows runs as one microtask before the next rendering opportunity. Another attempt recursively queues one microtask per row and still starves the loop. Use a worker or yield between bounded chunks to future tasks, then verify a paint and input response during processing. Test an error halfway through so the label does not remain stuck.",
         drill="Create a button that processes 62 rows, sets a visible status, and records time to first paint and time to completion. Compare synchronous parsing, a promise callback, chunked task yields, and a worker. Do not treat the console order as the only evidence. Add a second button and try to activate it during import. The chosen approach should keep the second action responsive while preserving a correct final row count and an error recovery path.",
         decision="Use microtasks for short sequencing, and choose task yields or a worker when work must make room for input and paint.",
         checks=["The expected current-task, microtask, next-task order is reproduced.", "A processing label becomes visible before a long import finishes.", "A separate control responds during import without corrupting the result."],
         mistakes=["Assuming a promise callback moves computation off the main thread.", "Creating an endless microtask chain to split heavy work.", "Equating logged order with an observed browser paint."],
         related=["web-tech/dom-events-progressive-enhancement", "web-tech/performance-budget-and-layout-stability", "web-tech/cooperative-main-thread-scheduling"]),
    dict(path="web-tech/workers-messages-transfer-and-cancellation", hub=1, title="Workers, Messages, Transfer, and Cancellation",
         summary="Move expensive computation off the main thread while keeping messages versioned and route-owned.",
         definition="A dedicated worker runs JavaScript outside the page's main thread and communicates by messages. It does not receive the page DOM, so it is well suited to parsing, summarizing, or transforming data rather than updating visible controls directly. Message payloads are commonly copied with structured cloning; transferable buffers can move ownership instead, after which the sender cannot keep using the transferred buffer. Put a request ID or generation number on each job so an old result cannot overwrite a newer route. Cancellation requires an explicit protocol or worker termination; posting a cancel message cannot interrupt a synchronous worker loop until that loop yields.",
         case="The case page accepts a large local measurement file and computes a preview. Parsing on the main thread makes the note field lag. A worker can process the file bytes and send back a summary for case 47. Before it finishes, the reviewer opens case 62. The page must ignore the old result even if the worker completes successfully. If the bytes are transferred for speed, the main thread must not expect to reread the same buffer after posting it. A new job either uses new bytes or an intentional copy.",
         code='// Page module\nconst parseWorker = new Worker(new URL("./case-parser.worker.js", import.meta.url), { type: "module" });\nlet currentJobId = 0;\nfunction parseCaseBytes(caseBytes) {\n  const jobId = ++currentJobId;\n  parseWorker.postMessage({ jobId, bytes: caseBytes }, [caseBytes]);\n}\nparseWorker.onmessage = event => {\n  if (event.data.jobId !== currentJobId) return;\n  renderCaseSummary(event.data.summary);\n};', language="javascript",
         implementation="The page sketch transfers an ArrayBuffer, not an arbitrary typed-array view, and uses a job ID to reject obsolete results. The worker file must validate message shape, perform bounded parsing, and return either a result or a classified error with the same job ID. Route cleanup should terminate or reuse the worker deliberately and remove stale handlers. A job ID stops old results from changing UI, but it does not stop wasted CPU. If cancellation matters, split worker work into chunks that can receive a cancel message or terminate the worker and recreate it.",
         cost="Creating a worker and loading its module takes time and memory. Structured cloning a large object also takes time and memory; transferring a buffer can avoid the copy but detaches it from the sender. For tiny calculations, the communication overhead may exceed the work itself. Measure total time to usable result as well as main-thread responsiveness. Pooling workers can save startup cost for repeated jobs, yet a pool adds queueing and cancellation rules. Keep one worker until measurement justifies a more complex arrangement.",
         failure="The route reuses one worker but has no job identity. A slow case 47 summary arrives after case 62 and replaces the panel. The team adds an ID check but leaves the transferred caseBytes in a local cache; another action reads the detached buffer and fails. Use current-job checks and an explicit ownership rule for bytes. On route exit, clear handlers or terminate the worker. Test errors and very large files; a valid message envelope does not guarantee the parser can handle unbounded input.",
         drill="Parse the same measurement file on the main thread and in a worker. Record input responsiveness, transfer time, parse time, and peak memory. Start a job for case 47, switch to 62, and confirm no old summary appears. Inspect the sender's buffer after transfer to understand ownership. Trigger a malformed file and confirm the worker returns a bounded error state. Finally leave the route mid-job and verify the worker and message listener are cleaned up.",
         decision="Use a worker when measured computation blocks interaction enough to justify startup and messaging cost; make job identity and data ownership explicit.",
         checks=["An obsolete worker result cannot update a newer case route.", "Transferred input is not reused from the sender after ownership moves.", "Malformed input and route exit release worker resources and show a controlled state."],
         mistakes=["Assuming a worker can directly update DOM controls.", "Posting a cancel message to a worker that never yields and expecting immediate interruption.", "Reusing a transferred buffer after detachment."],
         related=["web-tech/react-effects-and-request-races", "web-tech/typescript-and-runtime-api-boundaries", "web-tech/browser-memory-and-resource-lifecycles"]),
    dict(path="web-tech/cooperative-main-thread-scheduling", hub=1, title="Cooperative Main-Thread Scheduling",
         summary="Split bounded work into tasks so input and rendering can proceed without losing result integrity.",
         definition="Sometimes work must stay near the DOM or is too small to justify a worker, yet it is too large for one uninterrupted task. Cooperative scheduling processes a bounded chunk, yields to a future task, then continues. A timer-based yield is widely available; a scheduling API may offer better continuation priority where supported, but any feature-specific path needs a fallback. Choose chunk size from measured work time, not a fixed item count alone: one record may cost far more than another. Preserve cancellation and result ordering across yields, since the route can change while a batch is paused.",
         case="A review page highlights 62 visible search snippets. Each highlight is short, but processing all in one event handler delays focus response after a filter change. Chunk the work until a small time budget is used, then allow another task and rendering opportunity. If a second filter request arrives, stop the old generation and start again from its own records. Keep the result hidden or explicitly partial until the required pieces are ready, so a user does not mistake half-highlighted matches for a complete search response.",
         code='async function summarizeInChunks(records, isCurrent, consumeRecord) {\n  let checkpoint = performance.now();\n  for (const record of records) {\n    if (!isCurrent()) return false;\n    consumeRecord(record);\n    if (performance.now() - checkpoint >= 12) {\n      await new Promise(resolve => setTimeout(resolve, 0));\n      checkpoint = performance.now();\n    }\n  }\n  return true;\n}', language="javascript",
         implementation="The caller supplies current-generation ownership and record work; the function stops when that owner changes. The 12-millisecond target is an illustrative starting point, not a universal frame budget. Browser timers may be delayed, especially in background tabs, so do not use this loop for a time-critical background guarantee. The function must handle thrown errors and set a final UI state in the caller. If supported scheduling primitives are adopted, feature-detect them and compare real interaction behavior with the timer fallback before claiming improvement.",
         cost="The loop still performs O(n) record work and O(1) additional state besides the caller's results, but each yield adds task scheduling overhead and increases total completion time. Smaller chunks improve input opportunity while extending the work; larger chunks finish sooner but can create long tasks. A browser background tab may throttle timers, making total duration much longer. Measure both time to completion and responsiveness under a realistic record mix. If per-record work is itself too expensive, a worker is a better boundary.",
         failure="A developer writes records.forEach(async record => { await yieldNow(); consumeRecord(record); }) and assumes the outer operation waits. It does not; the UI reports completion while many callbacks are still pending, and errors escape the intended handler. Use a sequential for...of loop and await each yield. Another failure is forgetting generation checks after a yield, so old highlights appear on a new query. Verify cancellation before each record and after any route change.",
         drill="Instrument a list with short and long records. Try chunk targets of 6, 12, and 24 milliseconds and compare response to a second click, total completion time, and output count. Change the active query during a yield and verify the old generation stops. Throw an error in one record and confirm the caller reports failure without claiming a complete list. Repeat in a background tab to document timer behavior rather than assuming the foreground timing applies everywhere.",
         decision="Chunk main-thread work when measured interaction delay warrants it, and keep each resumed batch tied to the current route or task generation.",
         checks=["A second control receives input while a long list is processed.", "Changing the query during a yield stops old work before it writes new UI.", "The caller reports completion only after all records finish and handles errors distinctly."],
         mistakes=["Using forEach with async callbacks as a sequential work loop.", "Yielding after every trivial record without measuring scheduling overhead.", "Continuing stale work after a route change."],
         related=["web-tech/event-loop-tasks-microtasks-and-paint", "web-tech/workers-messages-transfer-and-cancellation", "web-tech/performance-budget-and-layout-stability"]),
    dict(path="web-tech/browser-memory-and-resource-lifecycles", hub=1, title="Browser Memory and Resource Lifecycles",
         summary="Pair every route-owned listener, observer, URL, timer, and worker with a clear disposal path.",
         definition="Browser resources have owners and lifetimes. An event listener, observer, object URL, timer, subscription, or worker can outlive the screen that created it unless the route or component releases it. The result may be repeated handlers, detached DOM retained in memory, stale network work, or a preview image URL that remains allocated after a case closes. Define ownership at creation: the case page owns its scroll observer and preview URL, while a shared application shell may own a connection across routes. Cleanup must be symmetric and safe when a task is interrupted halfway through setup.",
         case="Reviewer 29 opens and closes the same photo preview twenty times. Each opening creates an object URL and a resize observer; neither is released on close. The page still seems functional, but memory rises and later resize events run twenty callbacks. Bind the observer and preview URL to one view lifetime. When the panel closes or changes case, disconnect the observer, revoke the object URL, cancel pending work, and remove listener registrations. Keep the image's source change and URL revocation in a safe order so the visible preview is not invalidated early.",
         code='function mountPreview(previewNode, imageFile) {\n  const previewUrl = URL.createObjectURL(imageFile);\n  const resizeObserver = new ResizeObserver(() => updatePreviewLayout(previewNode));\n  previewNode.src = previewUrl;\n  resizeObserver.observe(previewNode);\n  return () => {\n    resizeObserver.disconnect();\n    previewNode.removeAttribute("src");\n    URL.revokeObjectURL(previewUrl);\n  };\n}', language="javascript",
         implementation="The returned function is the owner cleanup. A production view must call it exactly once when the preview is removed or replaced; it should also handle errors during setup and any pending image decode or worker task. A shared AbortController can manage several event listeners or requests tied to the same view, but not every API accepts an abort signal. Keep explicit cleanup for observers and object URLs. Do not attach a listener directly to every row when one delegated listener on a stable parent meets the interaction need.",
         cost="One observer and one object URL are small, yet leaks accumulate with repeated navigation and large image files. Explicit disposal adds code and test cases, while accidental retention makes long sessions slower and harder to diagnose. A heap snapshot can show detached nodes and retained references; compare after repeated open/close cycles rather than judging one page load. Event delegation can reduce listener count, but a global listener still needs a stable owner and a route-aware callback so it does not act on obsolete UI.",
         failure="A component unmounts its image but leaves the object URL and observer active. Manual testing opens the preview only once, so it passes. A reviewer working all day sees increasing memory use and duplicate layout updates. Reproduce with repeated cycles, inspect observer callbacks and memory retention, then invoke cleanup at the view boundary. Another failure is revoking the URL before the replacement image has loaded, causing a blank preview; sequence replacement and cleanup according to the displayed asset's ownership.",
         drill="Open and close a preview thirty times while recording observer callback count and memory trend. After each close, verify that no callback runs for the former node and that its object URL is revoked. Replace one image without closing the panel and confirm the old URL is released only after the new state owns the display. Add route navigation during image decode, then verify abortable work and observers stop without leaving a broken visible state.",
         decision="Create browser resources with an owner and a disposal path in the same code review; test repeated use, not only first mount.",
         checks=["Thirty open/close cycles do not multiply observer callbacks or retain old preview URLs.", "Replacing a preview releases the old asset without blanking the new one.", "Route exit stops listeners, observers, and pending work tied to that route."],
         mistakes=["Assuming unmounting a DOM node releases every attached resource.", "Revoking an object URL before the displayed image no longer needs it.", "Using a global listener for a route task without route-aware cleanup."],
         related=["web-tech/react-effects-and-request-races", "web-tech/workers-messages-transfer-and-cancellation", "web-tech/safe-file-upload-pipeline"]),
]

assert len(hubs) == 2 and len(topics) == 8
for hub_number in range(2):
    assert sum(topic["hub"] == hub_number for topic in topics) == 4


def add_entry(path, title, summary, entry_type, section_path, sort_order):
    assert path not in by_path, path
    template = "web-tech/getting-started" if entry_type == "article" else "web-tech/web-technology"
    entry = copy.deepcopy(by_path[template])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), type=entry_type,
                 path=path, title=title, summary=summary, category="Web Development",
                 subject="web-tech", difficulty="Intermediate" if entry_type == "article" else None,
                 tags=["web-tech", "web-development"], sort_order=2000 + sort_order,
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
    add_entry(topic["path"], topic["title"], topic["summary"], "article", hubs[topic["hub"]]["path"], 10 + number)

for topic in topics:
    entry = by_path[topic["path"]]
    if topic["language"] == "javascript":
        subprocess.run(["node", "--check", "--input-type=module"], input=topic["code"],
                       text=True, capture_output=True, check=True)
    siblings = [item["path"] for item in topics if item["hub"] == topic["hub"] and item["path"] != topic["path"]]
    related = [hubs[topic["hub"]]["path"]] + siblings + topic["related"]
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
    group = [topic for topic in topics if hubs[topic["hub"]]["path"] == hub["path"]]
    entry["data"]["modules"] = [{"title": hub["title"], "summary": hub["summary"], "lessons": [topic["path"] for topic in group]}]
    entry["data"]["resource_tabs"] = [{"title": "Web Development", "path": "web-tech/web-technology"},
                                       {"title": "Projects", "path": "web-tech/web-technology/project"},
                                       {"title": "Quizzes", "path": "web-tech/quizzes"}]
    entry["body"] = para(hub["overview"])
    entry["body"] += "<h2>Topics in this track</h2><ul>" + "".join(f'<li>{link(topic["path"])} — {html.escape(topic["summary"])}</li>' for topic in group) + "</ul>"
    entry["body"] += "<h2>Prerequisite paths</h2><p>" + "; ".join(link(path) for path in hub["bridges"]) + ".</p>"
    entry["body"] += "<h2>Neighbor track</h2><p>" + link(hubs[0]["path"] if hub == hubs[1] else hubs[1]["path"]) + ".</p>"

root_entry = by_path["web-tech/web-technology"]
for hub in hubs:
    group = [topic for topic in topics if hubs[topic["hub"]]["path"] == hub["path"]]
    root_entry["data"]["modules"].append({"title": hub["title"], "summary": hub["summary"],
                                          "lessons": [hub["path"]] + [topic["path"] for topic in group]})
    root_entry["body"] += f'<h2>{link(hub["path"])}</h2><p>{html.escape(hub["summary"])}</p><ul>' + "".join(
        f'<li>{link(topic["path"])} — {html.escape(topic["summary"])}</li>' for topic in group) + "</ul>"
root_entry["updated_at"] = stamp

for path, targets in {
    "web-tech/frontend-application-architecture": [hubs[0]["path"], hubs[1]["path"]],
    "web-tech/responsive-interaction-contract": [topics[0]["path"], topics[1]["path"]],
    "web-tech/component-boundaries-and-state": [topics[2]["path"]],
    "web-tech/reflow-zoom-and-motion-preferences": [topics[3]["path"]],
    "web-tech/dom-events-progressive-enhancement": [topics[4]["path"]],
    "web-tech/react-effects-and-request-races": [topics[5]["path"], topics[7]["path"]],
    "web-tech/performance-budget-and-layout-stability": [topics[6]["path"]],
}.items():
    entry = by_path[path]
    entry["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": len(hubs), "new_lessons": len(topics)}))
