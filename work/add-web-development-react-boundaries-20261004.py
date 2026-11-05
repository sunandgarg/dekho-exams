"""Add original React state and rendering lessons to Web Development drafts."""
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


hub_path = "web-tech/react-state-and-rendering-boundaries"
hub_title = "React State and Rendering Boundaries"
topics = [
    dict(
        slug="react-component-identity-and-keyed-draft-lifetime",
        title="React Component Identity and Keyed Draft Lifetime",
        summary="Choose stable component keys according to the lifetime of a user's draft, not list position.",
        concept="React associates local state with a component's position, type, and key in the rendered tree. That means two visually similar panels can carry different drafts, and the same panel can keep a draft after its displayed record changes if its identity did not change. Keys are not a visual sorting aid. They tell React which child is which across renders. A record identifier is usually stable enough for a case row; an array index is not when rows are inserted, sorted, or filtered. Deliberately changing a key can reset a form, but doing that on every render destroys user input and focus. The design question is whose work the state belongs to and when that work should end.",
        case="A permit reviewer edits the private note for case 47 while the queue is sorted by age. A new urgent case enters at the top. The list uses positions as keys, so a draft note and its expanded state appear beside another case after reordering. Elsewhere, a detail panel is reused for case 62 without a new key, leaving the case 47 comment in the case 62 form. One defect preserves state for the wrong entity; the other loses association when positions move. The corrected queue uses case IDs as row keys. The editor subtree uses the selected case ID as its identity when switching cases should discard the previous local draft, while a separate saved-draft store retains any work that must survive navigation.",
        implementation="Write a state-lifetime table before changing keys: row selection, temporary input, persisted draft, request result, and focus. Keep each row keyed by an immutable server identifier, not by its current index, status, or randomly generated value. Put a keyed editor at the boundary where changing cases must create a fresh state instance. If switching away must preserve unsent text, save it under the case ID first and hydrate the new editor from that owned store; a key alone is not a persistence strategy. Avoid defining a component function inside another render function, because its function identity changes and can reset state unexpectedly. Test insertion, filtering, sort reversal, case switch, and browser back. In each test, assert both the visible record ID and the draft's owner, not merely that some text remains.",
        cost="Stable keys make reconciliation cheaper and avoid accidental remounts, but a deliberately keyed subtree remounts all descendants and can restart expensive widgets, focus, and effects. A saved-draft map adds memory proportional to active drafts and needs an expiry or submission cleanup rule. Keeping every hidden editor mounted to preserve state avoids remount cost but retains its resources and may run unnecessary effects. Choose the smallest subtree whose lifetime truly changes, then measure render work on a long queue. There is no useful universal key such as a timestamp: changing it every time makes every update a new component. A changing key should reflect a real ownership change.",
        failure="Insert a case ahead of the currently edited row, reverse sorting, and filter out then restore that row. The draft must remain associated with its case or be intentionally stored elsewhere. Switch the detail panel from case 47 to case 62 with an unfinished note and verify the new form does not silently display the old case's text. Change an unrelated toolbar label; the editor must not reset. Remove a row while a request for it is pending and ensure its response cannot write into another row's state. Repeat with keyboard focus inside the editor, since an unexpected remount can erase the caret even when text is restored.",
        drill="Build a review queue containing cases 47, 62, and 81. Enter a note under case 47, then insert case 29 at the top, sort descending, and hide case 62. Record the case ID associated with every draft after each action. Next switch the detail editor to case 81 and decide whether the old draft should be persisted or discarded. State which subtree receives a case ID key and why. Add a test where a status badge changes without replacing the editor. Compare remount counts and focus behavior before and after the key change.",
        decision="A key expresses state ownership; use it only where the entity or intended lifetime changes.",
        code='import { useState } from "react";\n\nfunction PermitQueue({ cases, selectedCaseId }) {\n  const selectedCase = cases.find((permitCase) => permitCase.id === selectedCaseId);\n  return (\n    <section>\n      <ul>{cases.map((permitCase) => <li key={permitCase.id}>{permitCase.title}</li>)}</ul>\n      {selectedCase && <CaseNoteEditor key={selectedCase.id} permitCase={selectedCase} />}\n    </section>\n  );\n}\n\nfunction CaseNoteEditor({ permitCase }) {\n  const [note, setNote] = useState("");\n  return <label>Note for {permitCase.id}<textarea value={note} onChange={(event) => setNote(event.target.value)} /></label>;\n}',
        checks=["Rows keep their draft owner after insert, sort, and filter.", "A deliberate case change resets only the intended editor subtree.", "An unrelated parent update does not erase text or focus."],
        mistakes=["Using an array index as a key for a reorderable queue.", "Generating a fresh random key on every render.", "Assuming a key saves an unsent draft for later recovery."],
        related=["web-tech/react-effects-and-request-races", "web-tech/autosave-draft-recovery-and-conflicts"],
    ),
    dict(
        slug="react-derived-state-and-event-ownership",
        title="React Derived State and Event Ownership",
        summary="Calculate render data from current inputs and put user-command effects in their event path.",
        concept="An effect is for synchronizing React with an external system. It is a poor place to copy one state value into another or compute a filtered list from current props. That copy renders an out-of-date intermediate state, adds another update, and creates another place where the values can disagree. Derived values should be calculated during render when cheap, or memoized when a measured expensive calculation depends on stable inputs. A user command such as submitting an approval belongs in the event path that knows why it happened. An effect that watches a status flag cannot reliably tell whether the change came from a user click, restored data, or a background refresh.",
        case="A permit queue keeps all cases, a search phrase, filtered cases, and a visible count in separate state variables. An effect rebuilds filtered cases after the input changes; another effect updates the count. The UI briefly shows the new phrase beside the old count, and a network refresh can race with both effects. An approval effect watches an 'approved' boolean and posts a mutation when it turns true. Restoring a saved view with that flag can post the approval again. The rewrite stores source cases and the phrase, derives the visible list and count in the render, and sends the mutation only in the explicit approval command with a stable operation ID.",
        implementation="Identify source state: server snapshot, local search phrase, selected case, and pending operation. Derive filtered rows and count from those sources in one render. If filtering 47,000 rows is expensive, measure it, then memoize using the source list and search phrase as dependencies; memoization is a cache, not a correctness mechanism. Normalize the phrase once and use a stable comparison rule. Keep network mutation in the click handler or an action boundary, validate the server response, and update authoritative state when it returns. Do not make an effect infer a user intent from a boolean. Real external synchronization, such as subscribing to a browser event, still belongs in an effect with cleanup. For fetching when the selected case changes, handle cancellation and stale responses as a separate request race.",
        cost="Deriving values during render uses CPU on each relevant render but removes extra state updates and drift. Memoization stores a prior result and dependency comparison; it can add complexity without benefit on small lists. A large filter may need indexing, a worker, or a deferred render, each with its own data-copy and scheduling cost. An explicit event mutation makes the effect count predictable and gives one place for idempotency and error handling. Measure render duration and count redundant requests. Do not turn every calculation into a memo by habit; first establish that the cost matters on target devices.",
        failure="Type a phrase while a new server snapshot arrives. The rows and count must correspond to the same render, not to two effect updates at different times. Restore a view with an approved status flag; no approval request should be emitted without a user command. Click Approve twice quickly and verify the operation identity and pending state prevent duplicate effects. Simulate a rejected approval and keep the visible record consistent with the server. Switch the selected case while its detail fetch is in flight and reject the stale result. Repeat with an empty list and a phrase containing mixed case or whitespace.",
        drill="Start with 47 permit cases, a phrase field, and a derived count. Remove the stored filtered-list and count states. Measure render time before introducing a memo; then expand to 47,000 records and decide whether the cost justifies one. Add an approval button whose handler sends a stable operation ID to the server. Replay a restored approved record, a background snapshot refresh, a double click, and a failed request. Count actual approval network calls. Write down which effect remains for a genuine external subscription and its cleanup event.",
        decision="If a value can be calculated from current render inputs, do not synchronize a second copy of it.",
        code='import { useMemo, useState } from "react";\n\nfunction PermitSearch({ cases, onApprove }) {\n  const [phrase, setPhrase] = useState("");\n  const visibleCases = useMemo(() => {\n    const needle = phrase.trim().toLocaleLowerCase();\n    return cases.filter((permitCase) => permitCase.title.toLocaleLowerCase().includes(needle));\n  }, [cases, phrase]);\n  return (\n    <section>\n      <input type="search" aria-label="Find a permit" value={phrase} onChange={(event) => setPhrase(event.target.value)} />\n      <p>{visibleCases.length} cases</p>\n      {visibleCases.map((permitCase) => <button type="button" key={permitCase.id} onClick={() => onApprove(permitCase.id)}>Approve {permitCase.title}</button>)}\n    </section>\n  );\n}',
        checks=["Visible rows and count come from the same source inputs.", "A restored status never fires a command mutation.", "An effect exists only where an external system needs synchronization."],
        mistakes=["Copying filtered rows into state with an effect.", "Posting an approval because a boolean happened to change.", "Adding memoization before measuring a render bottleneck."],
        related=["web-tech/react-effects-and-request-races", "web-tech/interaction-latency-traces-and-main-thread-contention"],
    ),
    dict(
        slug="react-urgent-input-and-transition-work",
        title="React Urgent Input and Transition Work",
        summary="Keep the input controlled with an urgent update while allowing an expensive result view to lag safely.",
        concept="A search box and its expensive result grid do not have the same urgency. Keystrokes should update the controlled input immediately; recalculating thousands of rows can be marked as lower-priority rendering work. A transition tells React that certain state updates may be interrupted and resumed around urgent work. It does not make a slow filter algorithm faster, and it does not move JavaScript computation to another thread. The transition's pending indicator is a UI state, not proof that network work completed or that a result is authoritative. If server requests accompany the query, request identity and stale-response handling remain separate problems.",
        case="The permit search view redraws 47,000 records as a reviewer types. The input visibly stalls because every character and result update share an expensive render path. The team keeps the input text in urgent state and starts a transition for the query driving the list. The text now follows each keystroke, while a pending message states that the list is catching up. A second problem appears: a previous network search returns after a newer one and replaces the results. Transition priority does not order responses, so the request layer rejects that stale result by generation. A third check confirms the same screen on a slower tablet and with an assistive technology announcement that does not repeat on every intermediate render.",
        implementation="Separate the displayed input value from the query that drives the costly view. Update the input directly in the change handler, then schedule the result-query update inside a transition. Keep the pending state near the results, where users can understand why the list lags; do not make the text box itself appear unresponsive. If filtering is synchronous and very expensive, measure it because a transition cannot preempt an individual blocking JavaScript call. Consider indexing or a worker for heavy computation. If fetching results, give each request a generation or abort controller and accept only the latest relevant response. Do not put the controlled text input's own state update inside a transition. Verify that a pending view still has a valid accessible label, and that empty or stale results are not misrepresented as current.",
        cost="Transitions can improve responsiveness by letting urgent rendering win, but discarded work may be repeated and total CPU may rise. Keeping two query values adds a clear lag state that the UI must explain. A worker adds message transfer cost and a cancellation path; indexing adds memory. Field measurements should separate input delay from result completion and compare both. A pending label that flashes for every tiny update can be noisy, so test with realistic typing speed and data volume. React scheduling is not a substitute for bounding list size or using a virtualized view when rendering tens of thousands of rows dominates.",
        failure="Type 29 then 47 quickly and confirm the input shows the latest phrase even while the result grid still reflects an earlier query. Delay the older network response until after the newer one; it must not overwrite current results. Put a deliberately slow synchronous calculation before the transition call and observe that the keyboard can still freeze; priority cannot interrupt code already occupying the thread. Clear the phrase during a pending result render and ensure the final list matches the empty query. Test keyboard and screen-reader use so pending text describes the result state without announcing stale counts as final.",
        drill="Build a search screen with 47,000 permit summaries. Record input delay and time to settled results before changes. Put the input state update in the urgent path and the result query update in a transition. Add a pending label adjacent to results. Simulate two responses arriving out of order with generation numbers 62 and 81; only the current generation may update the list. Compare a pure synchronous filter, a measured index, and a worker computation to identify when transition scheduling alone is insufficient. Capture the input value, pending state, result query, and visible count after each keystroke.",
        decision="Use transition priority for render scheduling, and separately solve expensive computation and stale network results.",
        code='import { useId, useState, useTransition } from "react";\n\nfunction PermitSearchBox({ onQueryChange }) {\n  const resultStateId = useId();\n  const [inputText, setInputText] = useState("");\n  const [isPending, startTransition] = useTransition();\n  function handleChange(event) {\n    const nextText = event.target.value;\n    setInputText(nextText);\n    startTransition(() => onQueryChange(nextText));\n  }\n  return <label>Search permits<input type="search" value={inputText} onChange={handleChange} aria-describedby={resultStateId} /><span id={resultStateId}>{isPending ? "Updating results" : "Results current"}</span></label>;\n}',
        checks=["Typing remains urgent while result rendering may lag.", "Out-of-order network responses cannot replace newer results.", "A blocking calculation is measured separately from React scheduling."],
        mistakes=["Putting the controlled input's own update inside a transition.", "Assuming transitions move filtering to a background thread.", "Treating pending render state as confirmation of a server result."],
        related=["web-tech/cooperative-main-thread-scheduling", "web-tech/react-effects-and-request-races"],
    ),
    dict(
        slug="react-hydration-and-stable-first-render",
        title="React Hydration and Stable First Render",
        summary="Make server markup and the first client render agree before using browser-only data.",
        concept="Hydration attaches client behavior to HTML already produced by the server. The first client render must describe the same content the server sent. Differences from locale formatting, time, random IDs, browser storage, viewport checks, or inconsistent data snapshots are correctness problems, not harmless console noise. A client may see the server HTML before the bundle loads; a mismatched first render can replace or mis-associate visible content and events. Framework routers may orchestrate hydration, but they cannot make an unstable component's first output deterministic. State the boundary between serialized server data and browser-only enhancement, then validate it under slow loading and differing device settings.",
        case="A permit dashboard server-renders a queue count of 47. The browser reads a local filter preference during render and immediately computes 29; hydration warns and the count changes before the user interacts. A timestamp uses the server's time zone while the browser uses another, so each row has different text. The team passes a versioned server snapshot into the first client render and displays exactly that count and a stable time representation. After hydration, an effect reads the saved filter preference and updates the view as a deliberate second state. The UI labels that change, and the server remains authoritative for case access; a local preference cannot make hidden cases available.",
        implementation="Capture the exact data snapshot used by the server render and serialize it safely for the client. Use the same snapshot and stable formatting rules on the initial client pass. Avoid reading window, local storage, current time, random values, or viewport state inside the first render path if the server cannot produce the same result. For browser-only preferences, initialize a neutral state that matches the server HTML, then apply the preference after hydration with an effect or a framework-supported client boundary. When a stable identifier is needed for controls, use an approach designed to agree across server and client render order rather than ad hoc randomness. Fix markup mismatches at their source; suppressing a warning is a narrow escape for truly unavoidable text differences, not a general repair. Test slow script delivery and a disabled-script view for the useful server content.",
        cost="Keeping a serialized snapshot adds response bytes and requires escaping and data-minimization rules. A second client pass for browser-only preferences can visibly change content and adds render work, so limit it to data that genuinely cannot be known on the server. A client-only island avoids one mismatch but withholds that part of the page until JavaScript arrives. Stable formatting may sacrifice a locally formatted first instant; a later enhancement can personalize it. Measure hydration duration, mismatch reports, layout changes, and time until controls work. The right goal is consistent initial meaning and usable progressive content, not merely a clean console.",
        failure="Render the dashboard on a server in one time zone and hydrate in a browser configured for another. The first text must match. Store a filter preference that hides 18 of 47 cases and verify that the first client render still agrees with the server, followed by an intentional filtered state. Delay JavaScript and check that the initial HTML remains understandable. Remove JavaScript and ensure the server output still exposes the permitted queue summary. Change the serialized snapshot version and verify the client does not silently attach to incompatible markup. Test an injected random ID to confirm the mismatch check catches it.",
        drill="Create a server snapshot containing 47 cases, a version, and a stable displayed time. Render the queue header on the server and inspect its HTML. Hydrate with that same snapshot while the browser has a different local preference and time zone. Record the first client text and the later preference update separately. Add one intentionally unstable value, observe the mismatch, then remove its render-time source. Decide which data can be safely serialized, which should be fetched later, and what users see if the script never loads.",
        decision="The first client render must share the server's data and formatting contract; personalize only after that boundary.",
        code='import { useEffect, useState } from "react";\n\nfunction PermitQueueHeader({ initialSnapshot }) {\n  const [savedLimit, setSavedLimit] = useState(null);\n  useEffect(() => {\n    try {\n      const savedValue = window.localStorage.getItem("permit-visible-limit");\n      if (savedValue === null) return;\n      const parsedLimit = Number(savedValue);\n      if (Number.isInteger(parsedLimit) && parsedLimit >= 0) setSavedLimit(parsedLimit);\n    } catch {\n      setSavedLimit(null);\n    }\n  }, []);\n  const visibleCount = savedLimit === null ? initialSnapshot.caseCount : Math.min(initialSnapshot.caseCount, savedLimit);\n  return <p>{visibleCount} permitted cases</p>;\n}',
        checks=["Server HTML and first client text use the same snapshot.", "Browser-only preferences apply after hydration, with a visible state change.", "Useful permitted content remains in the server output when scripts are delayed."],
        mistakes=["Reading local storage or current time inside the first render.", "Silencing every hydration warning without correcting the mismatch.", "Serializing private data merely to avoid a later request."],
        related=["web-tech/server-rendering-and-client-data-flow", "web-tech/navigation-history-and-page-lifecycle"],
    ),
]

assert hub_path not in by_path and len(topics) == 4
hub = copy.deepcopy(by_path["web-tech/production-signals-and-incident-decisions"])
hub.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + hub_path)), path=hub_path, title=hub_title,
           summary="Own component state by entity, derive render data, schedule slow updates, and keep hydration stable.",
           sort_order=3650, created_at=stamp, updated_at=stamp, published_at=stamp)
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
    subprocess.run([str(root / "node_modules/.bin/esbuild"), "--loader=jsx", "--format=esm"],
                   input=topic["code"], text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path["web-tech/trace-context-across-request-and-job"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                 title=topic["title"], summary=topic["summary"], sort_order=3651 + number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    related = [hub_path] + ["web-tech/" + other["slug"] for other in topics if other is not topic] + topic["related"]
    body = p(topic["concept"]) + "<h2>Working case</h2>" + p(topic["case"])
    body += '<h2>Implementation boundary</h2><pre><code class="language-jsx">' + html.escape(topic["code"], quote=False) + "</code></pre>" + p(topic["implementation"])
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
hub["body"] = p("React behavior follows ownership and timing boundaries. This track covers the lifetime of a case draft, source state versus derived display, urgent typing versus expensive results, and the first render shared by server and browser. Each lesson traces a production failure and asks what must remain stable when data, route, or user input changes.")
hub["body"] += "<h2>Topics in this track</h2><ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
hub["body"] += "<h2>Prerequisite paths</h2><p>" + "; ".join(link(path) for path in ["web-tech/frontend-application-architecture", "web-tech/react-effects-and-request-races", "web-tech/server-rendering-and-client-data-flow"]) + ".</p>"
curriculum = by_path["web-tech/web-technology"]
curriculum["data"]["modules"].append({"title": hub_title, "summary": hub["summary"], "lessons": [hub_path] + ["web-tech/" + topic["slug"] for topic in topics]})
curriculum["body"] += "<h2>" + link(hub_path) + "</h2>" + p(hub["summary"]) + "<ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
curriculum["updated_at"] = stamp
crosslinks = {
    "web-tech/react-effects-and-request-races": [hub_path, "web-tech/react-derived-state-and-event-ownership"],
    "web-tech/autosave-draft-recovery-and-conflicts": ["web-tech/react-component-identity-and-keyed-draft-lifetime"],
    "web-tech/cooperative-main-thread-scheduling": ["web-tech/react-urgent-input-and-transition-work"],
    "web-tech/server-rendering-and-client-data-flow": ["web-tech/react-hydration-and-stable-first-render"],
    "web-tech/browser-performance-diagnosis-and-measurement": ["web-tech/react-urgent-input-and-transition-work"],
}
for path, targets in crosslinks.items():
    assert path in by_path, path
    by_path[path]["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    by_path[path]["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": 1, "new_lessons": 4, "prose_words": {topic["slug"]: len(re.findall(r"\b[\w'-]+\b", " ".join(str(topic[key]) for key in ("concept", "case", "implementation", "cost", "failure", "drill", "decision", "summary")))) for topic in topics}}))
