"""Add original browser performance diagnosis lessons and internal connections."""
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


hub_path = "web-tech/browser-performance-diagnosis-and-measurement"
hub_title = "Browser Performance Diagnosis and Measurement"
topics = [
    dict(
        slug="field-performance-observation-and-sample-contracts",
        title="Field Performance Observation and Sample Contracts",
        summary="Collect browser timing entries with explicit support, sampling, privacy, and interpretation rules.",
        concept="A performance entry is an observation made by a browser, not a complete account of a user's task. Navigation, resource, paint, and custom marks describe different clocks and phases. Some entry types are unavailable in a given browser; some useful early entries arrive before application instrumentation starts. Collection must check support, request buffered entries when supported, and define exactly which event belongs to a page view. Field data should be grouped by route class, device class, and release rather than treated as one universal number. A fast median can conceal a painful tail. Conversely, a small slow sample can reflect a particular network or device rather than a widespread regression. Keep a stable definition of the denominator and track missing measurements as a first-class signal.",
        case="An inspection portal records load duration only after its application bundle executes. The first paint has already happened, so the dashboard silently excludes early navigation work. A new map page appears fast in the aggregate because its visitors mostly use desktop computers, while field inspectors on modest phones wait for a late route chunk. Team 47 first compares device and route cohorts, then records whether each entry type exists and whether the observer saw buffered entries. The report shows sample size and missingness beside each percentile. An address, case identifier, and full asset URL are omitted from the event payload; route class and coarse connection context are enough to locate the regression.",
        implementation="Define a measurement contract before installing observers: name, unit, start and end condition, route classification, release identifier, sample rate, and retention period. Ask the browser which entry types it supports. Observe each supported type with the appropriate buffered configuration and disconnect observers on page teardown. For custom operations, use marks around the actual user-visible work and clear marks after measurement. Limit the number of resource entries collected, because image-rich pages can generate many of them. Cross-origin resources may expose limited timing detail unless their owners explicitly allow it. Do not infer that a zero field means instantaneous work; it can mean unavailable data. Sample consistently by a stable random decision for a page view, and keep the sampling fraction in the event so rates can be interpreted. Validate results against a controlled trace before shipping a dashboard.",
        cost="Observer callbacks add work and retained entries consume memory. Sending every entry from every visit can create a telemetry traffic problem and reveal sensitive routes. A small sample reduces expense but raises uncertainty for uncommon pages. Compare p50 and p95 within comparable cohorts; only compare periods with compatible definitions. Estimate collection cost as sampled page views times entries per view times serialized payload size, then budget both client and ingestion overhead. A missing-observer counter is cheaper than pretending unsupported browsers had perfect results. Treat percentiles computed from tiny cohorts as provisional, and never put personal information in metric names.",
        failure="Turn off support for one entry type in a test setup and verify collection reports absence instead of a fabricated zero. Start the observer after initial paint and check whether buffered delivery preserves the early entry. Load 62 cross-origin images and confirm the payload cap remains bounded. Move from a case page to the map and prove route attribution follows the intended page-view boundary. Block telemetry transport and ensure form submission still works. Compare a release with 47 samples against one with thousands; the dashboard must show sample counts and avoid a confident claim from the smaller set.",
        drill="Instrument a permit search route and an inspection map as separate cohorts. Write an event schema with release, route class, entry type, elapsed milliseconds, supported flag, sample fraction, and collection timestamp. Collect in a browser that has navigation and paint entries, then simulate one without the paint entry. Inspect a late-installed observer, a blocked upload, a cross-origin image, and two route transitions. Produce a table of p50, p95, sample count, and missing count; explain one case where the aggregate improves while the mobile-map cohort becomes slower.",
        decision="A measurement is useful only when its collection boundary and missing-data behavior are explicit.",
        code='function eligibleTimingTypes(supportedTypes, requestedTypes) {\n  const supported = new Set(supportedTypes);\n  return requestedTypes.filter((entryType) => supported.has(entryType));\n}\nconsole.log(eligibleTimingTypes(["navigation", "paint"], ["paint", "resource", "navigation"]).join(","));\n// Output: paint,navigation',
        checks=["Unsupported entries are marked missing, never measured as zero.", "Each timing event has route, release, unit, and sampling definition.", "Telemetry failure does not block the user task."],
        mistakes=["Comparing percentiles from different device mixes without cohorts.", "Sending private case paths or complete resource URLs as metric names.", "Assuming an observer installed after startup sees all prior entries."],
        related=["web-tech/production-signals-and-incident-decisions", "web-tech/browser-execution-and-resource-lifecycle"],
    ),
    dict(
        slug="interaction-latency-traces-and-main-thread-contention",
        title="Interaction Latency Traces and Main-Thread Contention",
        summary="Break a slow interaction into queueing, handler, and presentation time before changing code.",
        concept="A click can feel late even when its handler is short. The browser may be finishing another task before the handler starts, or it may run the handler promptly and then spend time computing layout and presenting the next frame. Diagnose an interaction as three intervals: input delay, event-handler processing, and presentation delay. The boundaries are observable in a detailed performance trace, but a single metric alone does not identify the guilty function. Long tasks elsewhere on the main thread increase queueing; synchronous JavaScript inside the handler increases processing; expensive style, layout, paint, or heavy DOM work after the handler increases presentation delay. The fix follows the largest interval, not the most familiar optimization tip.",
        case="A reviewer taps Approve and sees the button change 310 milliseconds later. A developer shortens a 14-millisecond handler but the interaction remains slow. A trace shows 190 milliseconds waiting behind a bulk filter operation, 14 milliseconds in the handler, and 106 milliseconds preparing the next frame. The approval request itself is asynchronous and does not account for the local delay. The team splits the filter work into bounded units, gives the approval button an immediate state change, and reduces a large summary panel update. They then repeat the trace under a slow CPU profile and while the filter runs, because an idle desktop trace had hidden the contention.",
        implementation="Capture a representative slow interaction with its preceding main-thread tasks, handler stack, and next visual frame. Label the user action and route. First identify the largest interval. If input delay dominates, remove unnecessary recurring work or divide work into chunks that permit input to run. If processing dominates, measure expensive synchronous parsing, validation, and loops inside the handler; move nonessential work after feedback or into a worker when the data-transfer cost is acceptable. If presentation dominates, inspect style recalculation, layout, DOM size, and paint work caused by the state change. A handler that schedules microtasks repeatedly may still hold the thread before a frame can render; yielding needs a real opportunity for rendering, not merely another promise callback. Keep optimistic UI tied to a clear rollback contract when a server mutation later fails.",
        cost="More scheduled chunks increase coordination overhead and may lengthen total compute time even as the page becomes responsive. Worker handoff copies or transfers data and adds cancellation and ownership rules. Immediate feedback can improve perceived response, but an incorrect optimistic result has an error-recovery cost. Measure both the worst user interaction and throughput of the background operation. Record trace conditions: device, CPU setting, data size, competing task, and visible state. A percentile without the route and interaction name can hide a small but important approval path. Avoid treating a synthetic idle trace as proof that field input delay is solved.",
        failure="Run a 190-millisecond unrelated task immediately before the approval click; the handler may still measure 14 milliseconds while the user waits. Replace that task with many chained microtasks and verify a frame can actually render after the proposed yield. Force a server rejection after immediate approval feedback and confirm the button and audit state return to an accurate condition. Apply the same trace on a large case list and a short one; a fix that only works on the short list is incomplete. Disable a worker mid-computation and check cancellation, stale result handling, and cleanup.",
        drill="Take three traces of the Approve action: idle, while a 47,000-record filter runs, and during a summary-panel update. Annotate input delay, handler duration, and presentation delay for each. Keep the network request out of the local paint calculation. Choose one intervention for each dominant interval and predict its cost. Re-run with a modest CPU profile and with keyboard activation, since a click-only improvement may leave another input path slow. Record whether visible confirmation occurs before or after server commit and what the failure view says.",
        decision="Change the interval that consumes the time; a shorter handler does not cure queueing or slow paint.",
        code='function interactionBudget(inputDelayMs, handlerMs, presentationMs, limitMs) {\n  const totalMs = inputDelayMs + handlerMs + presentationMs;\n  return { totalMs, withinBudget: totalMs <= limitMs };\n}\nconsole.log(JSON.stringify(interactionBudget(190, 14, 106, 240)));\n// Output: {"totalMs":310,"withinBudget":false}',
        checks=["The trace separates delay before handlers from work inside them.", "A frame is allowed to render after a claimed yield.", "Immediate feedback has a defined server-failure correction."],
        mistakes=["Optimizing handler code while input delay dominates.", "Assuming a resolved promise gives the browser a paint opportunity.", "Reporting only an idle desktop interaction trace."],
        related=["web-tech/event-loop-tasks-microtasks-and-paint", "web-tech/cooperative-main-thread-scheduling"],
    ),
    dict(
        slug="retained-dom-memory-and-lifecycle-investigation",
        title="Retained DOM Memory and Lifecycle Investigation",
        summary="Find roots retaining removed views and verify that cleanup survives repeated route cycles.",
        concept="A removed element is not necessarily reclaimable. A listener, observer, timer callback, closure, map entry, or debugging reference can keep an object graph reachable after the view disappears. The browser garbage collector follows reachability, not a developer's sense that a component is finished. A rising heap graph is not by itself a leak: caches warm, assets decode, collection happens irregularly, and tooling can retain inspected objects. Reproduce a fixed route cycle, compare retained objects after collection, and inspect paths from an unexpected object to a root. The important question is which owner should release that reference and at what lifecycle event.",
        case="An inspection portal opens a photo detail panel and closes it 47 times. Each panel registers a resize observer, a key handler, and a temporary object URL for a private image. The DOM node leaves the page, yet a global array of callbacks still points to its closure; decoded images and listeners accumulate. The tab grows slower after each case. A heap snapshot shows detached panels retained by the callback array. The fix gives the panel one disposal function, removes the handler, disconnects the observer, revokes the object URL after the image no longer needs it, and removes the callback reference. The team repeats the same route cycle before and after the fix, allowing collection between snapshots.",
        implementation="Define ownership when acquiring a resource. The code that registers a listener must know when to remove it; an observer needs disconnect; an interval needs cancellation; an object URL needs revocation after its consumer finishes; an asynchronous callback needs a stale-view guard or abort path. Do not revoke an image URL while the image still needs it, and do not assume removing a DOM node unregisters global handlers. In a component system, use its teardown lifecycle, but inspect the actual closures because a library hook cannot clean an unrelated global registry. Record one stable user path, take a baseline snapshot, repeat the path several times, request collection when profiling, and compare counts of retained panel objects and detached nodes. Inspect retaining paths before deleting a suspected cache: a bounded cache may be intentional while an unbounded closure array is not.",
        cost="Profiling can pause a page and distort timings, so use it for diagnosis rather than field telemetry. Cleanup adds lifecycle code and can create use-after-dispose bugs if requests finish late. Aborting work early may save memory and bandwidth but requires a distinct canceled result for the UI. A bounded cache trades memory for fewer network or decode operations; choose a cap and eviction rule based on measured reuse. Compare retained size after equivalent cycles, not total heap at unrelated moments. A plateau after warmup can be healthy. A steady slope in retained detached views after forced collection deserves investigation.",
        failure="Open and close the photo panel 47 times, then compare snapshots and inspect the retaining path for any remaining detached panel. Keep DevTools console clear because inspected values can themselves remain reachable. Close a panel while its image request is in flight; the eventual callback must not append to a dead view. Close it before the image renders and verify the object URL is revoked at a safe point. Repeat after a route transition and a browser back action. Disable the cleanup once as a control; a test that cannot distinguish the known leak from the fixed behavior is not useful.",
        drill="Create a resource ledger for the photo panel: listener target, observer target, timer identifier, object URL, request controller, and callback registry. Write the acquisition and release event for each. Run a baseline, five warmup cycles, then 47 measured cycles. Count detached nodes and retained panel instances after comparable collection points. Trace one unexpected object back to a root and explain why that root exists. Add a late image response and a navigation-away case; the panel must stay disposed without breaking another active panel.",
        decision="Release resources at the owner boundary, and prove the retained graph stops growing across repeated cycles.",
        code='function createDisposer() {\n  const cleanupTasks = [];\n  return { add(task) { cleanupTasks.push(task); }, dispose() { while (cleanupTasks.length) cleanupTasks.pop()(); } };\n}\nconst panelLifetime = createDisposer();\npanelLifetime.add(() => console.log("observer-disconnected"));\npanelLifetime.dispose();\n// Output: observer-disconnected',
        checks=["Equivalent route cycles are compared after warmup and collection.", "Every acquired browser resource has one release owner.", "Late asynchronous results cannot revive a disposed view."],
        mistakes=["Calling every rising heap chart a leak.", "Removing DOM nodes while leaving global callbacks alive.", "Revoking an object URL before its consumer is finished."],
        related=["web-tech/browser-memory-and-resource-lifecycles", "web-tech/browser-capabilities-and-permission-lifecycle"],
    ),
    dict(
        slug="layout-paint-regressions-and-containment-decisions",
        title="Layout, Paint Regressions, and Containment Decisions",
        summary="Measure render work caused by DOM changes before applying containment or batching reads and writes.",
        concept="JavaScript can be fast while the page still misses a frame. A DOM or style change can invalidate layout, then a geometry read can force the browser to calculate it immediately. Repeating write-read pairs across many rows multiplies the work. Paint may remain expensive even when layout is contained, especially with large images, filters, or broad visual changes. Separate style, layout, and paint time in a trace, then map each expensive interval to the exact change that caused it. CSS containment tells the browser where a subtree can be treated more independently, but its modes also alter sizing, positioning, or clipping behavior. It is an architectural choice, not an automatic switch for every component.",
        case="A permit table displays 620 rows. On each status update, code changes a badge class and immediately reads the row width before moving to the next row. A profile records repeated layout calculations and a visible pause. The team gathers required widths first, performs badge writes second, and avoids measuring unchanged rows. They consider containment for independently sized table cards, but a popover anchored inside one card is clipped when paint containment is applied. The final design keeps a measurable row boundary without clipping the popover, which is rendered in the page's overlay layer. The fix is accepted only after checking keyboard focus and small-screen layout.",
        implementation="Record a performance trace during the actual status update with enough rows to expose the regression. Mark the application action and inspect style recalculation, layout, and paint separately. Search for geometry reads such as bounding-rectangle queries that follow style writes in the same loop. Batch all necessary reads before writes when the geometry can be reused, or compute positions from existing state rather than asking layout repeatedly. If a large independent region still causes broad invalidation, test a narrow containment mode and validate its semantic consequences. Layout containment can change the containing block for positioned descendants; paint containment can clip overflow; size containment needs a deliberate size. Use content skipping only where offscreen content and accessibility behavior have been tested. Compare trace work and user-visible rendering after the change, not only JavaScript function duration.",
        cost="Batching reduces repeated layout work but may require storing measurements and makes code harder when writes truly depend on fresh geometry. Containment can reduce invalidation outside a region, yet incorrect size assumptions cause jumps or cropped content. Offscreen rendering controls can improve large pages while complicating scroll-to-target and focus behavior. Track affected element count, layout count, layout time, paint time, and frame outcome at representative viewport widths. A single fast frame does not prove a frequent update is cheap. Quantify total update time under a burst of 47 status changes, and ensure a popover or tooltip remains visible.",
        failure="Alternate a badge write and width read across 620 rows; verify the baseline trace shows repeated layout work. Move the reads before writes and confirm the result values remain correct after font loading and responsive reflow. Apply paint containment to a card with an overflowing menu and inspect whether it becomes clipped. Resize the viewport, zoom text, and move by keyboard to a row that was initially offscreen. Trigger 47 updates in quick succession and look for stale measurement data. If layout time falls but paint time rises, investigate the paint cause instead of declaring victory from one metric.",
        drill="Build a table with 620 permit records and one anchored action menu. Record a trace for a status burst, labeling geometry reads, class writes, layout passes, and paints. Produce two versions: write-read per row and batched reads followed by writes. Measure both after fonts settle and at two viewport widths. Try only the containment mode justified by independence of the row cards. Capture a keyboard-open menu and a zoomed layout as acceptance evidence. State when cached widths must be invalidated and how the update will behave if a font arrives late.",
        decision="Use the trace to locate render cost, then choose batching or containment with its visible side effects tested.",
        code='function layoutPassEstimate(rowCount, writeThenReadEachRow) {\n  return writeThenReadEachRow ? rowCount : 1;\n}\nconsole.log(layoutPassEstimate(620, true) - layoutPassEstimate(620, false));\n// Output: 619',
        checks=["The trace separates JavaScript, layout, and paint work.", "Containment preserves overlay, focus, and responsive behavior.", "Measurements remain valid after font and viewport changes."],
        mistakes=["Alternating style writes and geometry reads in a long loop.", "Applying paint containment where menus must overflow.", "Calling a faster handler a rendering fix without inspecting frames."],
        related=["web-tech/css-layout-and-interface-systems", "web-tech/complex-accessible-interactions"],
    ),
]

assert hub_path not in by_path and len(topics) == 4
hub = copy.deepcopy(by_path["web-tech/production-signals-and-incident-decisions"])
hub.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + hub_path)), path=hub_path, title=hub_title,
           summary="Measure browser timing, slow interactions, retained views, and render cost with explicit evidence.",
           sort_order=3640, created_at=stamp, updated_at=stamp, published_at=stamp)
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
                 title=topic["title"], summary=topic["summary"], sort_order=3641 + number,
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
hub["body"] = p("Browser performance work begins with a trace tied to a user action. This track connects field timing collection, interaction latency, retained memory, and rendering cost. Each lesson asks what was measured, what the browser was doing, and what changed after a fix; the goal is a repeatable decision rather than an isolated score.")
hub["body"] += "<h2>Topics in this track</h2><ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
hub["body"] += "<h2>Prerequisite paths</h2><p>" + "; ".join(link(path) for path in ["web-tech/browser-execution-and-resource-lifecycle", "web-tech/production-signals-and-incident-decisions", "web-tech/quality-and-capacity-engineering"]) + ".</p>"
curriculum = by_path["web-tech/web-technology"]
curriculum["data"]["modules"].append({"title": hub_title, "summary": hub["summary"], "lessons": [hub_path] + ["web-tech/" + topic["slug"] for topic in topics]})
curriculum["body"] += "<h2>" + link(hub_path) + "</h2>" + p(hub["summary"]) + "<ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
curriculum["updated_at"] = stamp
crosslinks = {
    "web-tech/production-signals-and-incident-decisions": [hub_path, "web-tech/field-performance-observation-and-sample-contracts"],
    "web-tech/event-loop-tasks-microtasks-and-paint": ["web-tech/interaction-latency-traces-and-main-thread-contention"],
    "web-tech/browser-memory-and-resource-lifecycles": ["web-tech/retained-dom-memory-and-lifecycle-investigation"],
    "web-tech/cooperative-main-thread-scheduling": ["web-tech/interaction-latency-traces-and-main-thread-contention"],
    "web-tech/css-layout-and-interface-systems": ["web-tech/layout-paint-regressions-and-containment-decisions"],
}
for path, targets in crosslinks.items():
    assert path in by_path, path
    by_path[path]["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    by_path[path]["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": 1, "new_lessons": 4, "prose_words": {topic["slug"]: len(re.findall(r"\b[\w'-]+\b", " ".join(str(topic[key]) for key in ("concept", "case", "implementation", "cost", "failure", "drill", "decision", "summary")))) for topic in topics}}))
