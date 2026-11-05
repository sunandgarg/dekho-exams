"""Add original large-data and advanced interaction lessons to AI Trove drafts."""

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


def para(value):
    return f"<p>{html.escape(value)}</p>"


def link(path):
    assert path in by_path, path
    return f'<a href="/{html.escape(path, quote=True)}">{html.escape(by_path[path]["title"])}</a>'


hubs = [
    dict(path="web-tech/streaming-and-large-data-interfaces", title="Streaming and Large Data Interfaces",
         summary="Process large responses incrementally with bounded memory, cancellation, and honest completion states.",
         overview="A response body can arrive in pieces, and those pieces need not align with records or even character boundaries. Streaming permits useful work before the entire response arrives, but it shifts responsibility to framing, backpressure, cancellation, and partial-failure handling. A download has a related problem: copying a large file into browser memory just to trigger Save can defeat server streaming. These lessons follow a case activity feed and an evidence export through the complete byte-to-interface path, with explicit limits on memory and incomplete results.",
         bridges=["web-tech/fetch-status-and-abort", "web-tech/browser-execution-and-resource-lifecycle", "web-tech/accepted-operations-and-status-resources"]),
    dict(path="web-tech/complex-accessible-interactions", title="Complex Accessible Interactions",
         summary="Choose native semantics where possible and define focus, keyboard, and pointer alternatives for custom controls.",
         overview="A complex interface can look efficient while becoming unusable to a keyboard or assistive-technology user. Read-only records need clear row and column relationships; an editable grid needs an additional keyboard mode. Search suggestions need a stable active option and a clear way to leave the popup. Dragging a priority card needs a non-drag route to the same action. Async notifications need to identify what changed without stealing focus or repeating an entire panel. The case-review workspace ties these behaviors to one set of real tasks.",
         bridges=["web-tech/accessible-names-and-native-controls", "web-tech/dialog-focus-and-interruption-boundary", "web-tech/form-errors-and-recovery-paths"]),
]

topics = [
    dict(hub=0, path="web-tech/incremental-response-framing-and-utf8", title="Incremental Response Framing and UTF-8",
         summary="Decode and frame streamed records without assuming network chunks match lines or characters.",
         definition="A streamed response arrives as byte chunks chosen by transport and buffering, not by record boundaries. A newline-delimited JSON feed can split one record over several chunks or put several records in one chunk. UTF-8 characters can also span byte boundaries. Use a streaming decoder, retain an incomplete text tail, and parse only complete frames. Define a maximum frame size and a final-tail rule: a missing terminating newline may still contain one complete record, or the protocol may require the server to end every frame with a delimiter. Check the HTTP status and declared media type before reading. A stream is one-shot; do not call response.json() after consuming its body unless a deliberate clone was made before reading.",
         case="The case 47 activity feed sends 62 records as newline-delimited JSON. A network chunk ends halfway through the word 'reviewed', and another splits a Hindi note between UTF-8 bytes. A parser that runs JSON.parse on each chunk fails unpredictably or replaces characters. Decode bytes across chunk boundaries, append text to a bounded tail, and emit records only after a newline. A malformed line should carry its record position into an error state rather than silently disappearing. The interface may show accepted earlier records, but it must not call the whole feed complete if later parsing fails.",
         code='function splitCompleteLines(previousTail, textChunk) {\n  const pieces = (previousTail + textChunk).split("\\n");\n  return { lines: pieces.slice(0, -1), tail: pieces.at(-1) };\n}\nconst first = splitCompleteLines("", "{\\\"caseId\\\":47");\nconst second = splitCompleteLines(first.tail, "}\\n{\\\"caseId\\\":62}\\n");\nconsole.log(second.lines.length, second.tail.length);\n// Output: 2 0',
         implementation="The helper models text framing after a TextDecoderStream or stateful TextDecoder has handled partial UTF-8 bytes. The production reader should check response.ok, acquire the stream once, pass decoded text through the splitter, parse complete lines with try/catch, and enforce a maximum tail size before appending unbounded input. Record sequence numbers help detect a missing frame even when every received line parses. Decide whether to parse a nonempty tail at end-of-stream according to the server protocol, and close or cancel the reader when the route no longer owns it.",
         cost="For n total bytes, decoding and framing are O(n) time, with O(m) working memory for the largest permitted incomplete frame plus retained results. Calling response.text() first also costs O(n) memory for the full body. Repeated string concatenation of a large unbounded tail can become expensive, which is another reason to cap frame length. JSON parsing remains proportional to each record's size. Streaming helps first-result latency, but rendering every record immediately can still block the main thread; batch UI commits or move heavy transforms to a worker when measurements justify it.",
         failure="An implementation assumes each read() result is one JSON object. Tests use small local responses and pass, but production buffering splits a single record into two reads and the page reports a parse error. Another implementation decodes each byte chunk independently and corrupts a multibyte character at the split. Treat transport chunks as arbitrary, use a streaming text decoder, and test every possible split in a short fixture. If the server closes after half a record, expose a partial-feed failure and keep the last confirmed sequence visible.",
         drill="Construct a two-record feed and split its bytes after every possible offset, including inside a multibyte note. Confirm that all splits produce the same records. Send two records in one chunk and one record across three chunks. Omit the last newline and compare behavior under the chosen protocol. Grow one line past its limit and verify the reader stops with a bounded error. Insert malformed JSON at record 29 and confirm the UI labels prior records as partial rather than complete.",
         decision="Treat chunks as arbitrary bytes; decode continuously, frame explicitly, and bound the unfinished record.",
         checks=["Every byte split yields the same two parsed records.", "An incomplete final frame has a documented outcome.", "A malformed or oversized record cannot become silent success."],
         mistakes=["Parsing each network chunk as one complete record.", "Decoding UTF-8 bytes independently at each chunk.", "Allowing an unfinished line to grow without a limit."],
         related=["web-tech/fetch-status-and-abort", "web-tech/sse-and-websocket-choice", "web-tech/workers-messages-transfer-and-cancellation"]),
    dict(hub=0, path="web-tech/stream-backpressure-and-bounded-work", title="Stream Backpressure and Bounded Work",
         summary="Match reading speed to processing capacity instead of accumulating an unbounded queue.",
         definition="Backpressure is the mechanism that prevents a fast producer from overwhelming a slower consumer. A stream pipeline can propagate demand when each stage waits for the next stage to accept work. Application code breaks that property if it reads all chunks immediately and starts unlimited asynchronous processing. Await a bounded sink, cap queued bytes or records, and decide what to do when the downstream UI is slow. Dropping data is acceptable only for a protocol that explicitly permits it; a financial or audit feed needs ordered complete records or a visible gap. Use a single reader owner and cancel it when the page leaves.",
         case="A case activity feed sends 47,000 events. Parsing is quick, but each event triggers a database lookup in an enrichment service and a DOM update. A loop that calls enrich(event) without awaiting it accumulates thousands of promises and keeps every payload in memory. Limit concurrent enrichments, preserve sequence when results complete out of order, and commit visible rows in batches. If the user switches to case 62, abort the fetch and stop processing case 47's queued work. The server should also stop production when the connection closes if it can observe cancellation.",
         code='function withinQueueBudget(queuedBytes, nextBytes, maximumBytes) {\n  return queuedBytes + nextBytes <= maximumBytes;\n}\nconsole.log(withinQueueBudget(6200, 4700, 10000));\n// Output: false',
         implementation="The predicate expresses a byte limit; actual backpressure requires control flow that pauses reads or waits for a sink. For a ReadableStream pipeline, use a TransformStream or an awaited read/process loop so downstream readiness can influence upstream pulls. A manual queue needs both a maximum item count and a maximum byte count because one item may be huge. An event source that cannot pause must have a documented overflow policy, such as closing and resuming from a sequence token. Keep errors, cancellation, and completion distinct, and do not report completion while background tasks still run.",
         cost="Processing n records remains O(n) work, while a bounded queue of q records uses O(q) memory rather than O(n). A smaller q protects memory but may reduce throughput if processing stalls; a larger q absorbs bursts but increases latency and retention. Concurrent enrichment adds capacity only until the backend or browser saturates. Measure peak queue bytes, time to first usable batch, total completion, and responsiveness under a slow consumer. A single oversized frame should be rejected or separately handled, not admitted merely because queue item count is low.",
         failure="The reader awaits response.body, then schedules each record with an async callback inside forEach. The outer function returns success immediately while thousands of callbacks remain pending. Memory rises and errors become detached from the feed state. Replace it with an awaited loop or bounded worker pool, and attach every task to the current route generation. Another failure is a queue limit measured only in records: one 40 MB record consumes most available memory while the count remains one. Enforce byte and frame limits together.",
         drill="Feed 47,000 small records through a slow sink and record peak queued bytes. Double the sink delay; memory should stay near the configured bound while completion time grows. Add one oversized record and verify explicit rejection. Switch routes halfway through and confirm old work stops without writing into the new view. Make record 29 fail and verify that the stream reports partial failure, not a completed feed. Compare sequential processing with bounded concurrency and document any order-repair mechanism.",
         decision="Let consumer readiness govern reads, and bound both item count and bytes wherever work is queued.",
         checks=["Peak queue memory stays within a documented bound under a slow sink.", "Completion waits for all accepted records to settle.", "Route changes prevent obsolete results from reaching the new view."],
         mistakes=["Launching unawaited work for every streamed record.", "Bounding item count while ignoring byte size.", "Treating a dropped audit record as normal completion."],
         related=["web-tech/cooperative-main-thread-scheduling", "web-tech/workers-messages-transfer-and-cancellation", "web-tech/browser-memory-and-resource-lifecycles"]),
    dict(hub=0, path="web-tech/stream-cancellation-and-partial-result-contract", title="Stream Cancellation and Partial-Result Contract",
         summary="Separate a completed feed from an aborted or truncated one, and make retry position explicit.",
         definition="A stream can end normally, fail mid-body, or be cancelled because the user left its route. Those outcomes are not interchangeable. An AbortController can stop a fetch and its body consumption, but a server may have already produced or committed work. Attach a request identity and last confirmed sequence to the client state. On retry, use a server-supported cursor or replay token rather than appending a new stream blindly. Deduplicate repeated events by stable ID, and detect gaps when sequence numbers jump. If the feed has no resumable protocol, clear partial rows or label them explicitly until a full reread succeeds.",
         case="The case 47 feed renders 29 activity items, then the connection drops before the server's final marker. The page still has useful partial data, but it cannot claim 'All activity loaded'. The retry asks from sequence 30 if the server supports that cursor; if sequence 29 is replayed, the client deduplicates it. Switching to case 62 aborts the 47 reader, invalidates its generation, and prevents a late error from replacing case 62's loading state. A transport abort does not erase accepted server mutations elsewhere in the system.",
         code='function feedOutcome(lastSequence, expectedFinalSequence, wasAborted) {\n  if (wasAborted) return "cancelled";\n  return lastSequence === expectedFinalSequence ? "complete" : "partial";\n}\nconsole.log(feedOutcome(29, 62, false));\n// Output: partial',
         implementation="The helper uses a known final sequence for illustration; real feeds may use a terminal frame, total count, or server-issued cursor. A reader loop should catch AbortError separately from network and parse failures, release its reader lock, and mark only the current request generation. Preserve the last confirmed event ID for a supported resume path, but validate authorization and filter identity on the resumed request. Dedupe by event ID and check monotonic sequence; repeated IDs are not extra events. Never present a partial export or report as if it were a certified complete dataset.",
         cost="Tracking a last sequence is O(1) state, but deduping a long resumed feed may require a set of up to O(n) IDs or a bounded window when the server guarantees order. Full replay costs O(n) transfer and parsing; cursor resume reduces that cost if the server keeps a reliable replay window. Abort can save browser work and some server work, but not necessarily every already-started operation. A clear partial-state UI costs design effort and is necessary when users make decisions from the feed. Measure resume success and duplicate rates under forced disconnects.",
         failure="A catch block handles every rejection as 'Nothing found'. A dropped connection after 29 rows now looks like an empty successful search on retry, hiding evidence. Distinguish HTTP error, body failure, parse failure, abort, and normal terminal frame. Another defect appends replayed events without ID checks; sequence 29 appears twice and a reviewer counts it as two actions. Use stable event IDs and verify a cursor belongs to the same case and filter before accepting it.",
         drill="Stream 62 ordered events and cut the connection after event 29. Verify a visible partial state and a retry action; resume with event 29 deliberately replayed and confirm one copy remains. Remove event 31 from the replay and ensure a gap is reported. Abort during a route switch and check that case 62's state is untouched. Send an unauthorized retry cursor and confirm the server denies it. Repeat without a resume feature to verify the UI performs a full reread or clears partial data honestly.",
         decision="Name normal completion, failure, and user cancellation separately; resume only from a server-defined position.",
         checks=["A truncated feed cannot display a complete status.", "Replay does not duplicate event IDs or hide sequence gaps.", "A late abort or failure cannot alter a later route."],
         mistakes=["Calling every stream error an empty successful result.", "Retrying by append without a cursor and deduplication plan.", "Assuming abort reverses work already accepted by the server."],
         related=["web-tech/fetch-status-and-abort", "web-tech/live-update-reconnect-and-order", "web-tech/request-deadlines-retries-and-backoff"]),
    dict(hub=0, path="web-tech/large-export-download-and-integrity", title="Large Export Download and Integrity",
         summary="Keep large exports out of browser memory when possible and verify a resumed artifact's identity.",
         definition="A large export often begins as a server job rather than an immediate response. The server can prepare an artifact, expose a status resource, then let the browser download it as a normal file response. That path avoids converting the whole artifact into a JavaScript Blob merely to trigger Save, which can duplicate large bytes in memory. If the product supports resume, byte-range requests must refer to one immutable artifact version; an ETag or server-issued artifact ID protects against stitching bytes from different revisions. The server should set a safe filename, content type, length where known, and an expiry policy. A client must not call a download complete merely because an export job reached Ready.",
         case="Reviewer 29 requests a 740 MB case evidence export. Building it takes 47 seconds, so the API returns a job ID and a status route. When Ready, the UI offers a normal download link that streams the artifact; it does not fetch the whole file into an ArrayBuffer. The connection fails halfway. A resumed request is allowed only if the artifact ID and validator match the original bytes. If the server rebuilt the export from changed case data, start a new download rather than appending a new revision to the old half-file. Expired artifacts require a new job.",
         code='function mayResumeExport(saved, current) {\n  return saved.artifactId === current.artifactId && saved.etag === current.etag;\n}\nconsole.log(mayResumeExport({ artifactId: "case-47-v6", etag: "a9" }, { artifactId: "case-47-v7", etag: "b1" }));\n// Output: false',
         implementation="The comparison captures identity, while actual range support requires correct server responses and client handling. Keep export job authorization tied to the requesting account and case; a guessed artifact path must not bypass that check. Provide a normal anchor or browser navigation for download when possible, and let server headers describe the file. For a custom download manager, validate Content-Range, total length, and validator before appending bytes. Clean up temporary artifacts on expiry and report whether a cancelled client transfer also cancels server preparation, since those lifetimes can differ.",
         cost="Generating an export of b bytes takes at least O(b) output work and storage or transfer, while buffering it fully in browser JavaScript can add O(b) heap or Blob memory. A streamed download keeps application memory closer to a bounded chunk size, subject to browser and server implementation. Resumable ranges save repeated transfer after failure but add validator, storage-retention, and bookkeeping cost. Expiring artifacts too quickly forces costly rebuilds; retaining them too long increases storage and privacy exposure. Measure peak browser memory, preparation time, transfer restart bytes, and cleanup lag.",
         failure="The UI fetches the 740 MB response, calls arrayBuffer(), creates a Blob, and builds an object URL. On a memory-constrained device the tab crashes before the save dialog appears. Use a normal download response or bounded streaming destination when supported. A second failure appends a resumed range from a new export revision because the filename matches. Compare immutable artifact identity and validator; reject mixed versions and restart. If status says Ready but the download returns an access denial, show a specific error instead of a false completion banner.",
         drill="Generate a large test export and compare browser memory for arrayBuffer buffering versus a normal download. Interrupt halfway, then attempt resume with the same artifact ID and with a changed validator. The latter must restart. Expire the artifact and ensure the status route explains how to create a new one. Try a second account's artifact ID and verify denial. Cancel preparation before Ready and confirm whether temporary files are removed or finish under a documented retention policy.",
         decision="Let the server own artifact production and identity; let the browser download bounded bytes without duplicating the whole file in application memory.",
         checks=["A large download does not require a full JavaScript buffer.", "Range resume rejects bytes from a changed artifact.", "Artifact access and expiry stay tied to the requesting account."],
         mistakes=["Calling a Ready job a completed download.", "Buffering a huge response solely to trigger Save.", "Resuming by filename without an immutable artifact validator."],
         related=["web-tech/accepted-operations-and-status-resources", "web-tech/safe-file-upload-pipeline", "web-tech/record-level-authorization"]),
    dict(hub=1, path="web-tech/data-table-versus-interactive-grid", title="Data Table Versus Interactive Grid",
         summary="Use native table relationships for reading and add grid keyboard behavior only when cells are truly interactive.",
         definition="A read-only table and an interactive grid solve different tasks. A native table exposes row, column, and header relationships that support browsing and comparison; it does not require every cell to become a keyboard stop. A grid is a composite widget for directional keyboard movement and often editing or selection. Adding grid roles without implementing its focus and key behavior creates a broken contract. Start with a table for case status, owner, and date. If cells contain editable controls, define how arrow keys move between cells, how Enter or F2 enters edit mode, how Escape leaves it, and how Tab exits the composite. Keep visible focus and selected state distinct.",
         case="The operations queue has 62 rows and four columns. Reviewers only read most cells and open a case from one link, so a native table with clear column headers is enough. A later bulk-edit view allows changing status inside cells. That view may justify a grid, but every keyboard route must be designed and tested. If every cell becomes a Tab stop, reaching the next control can take hundreds of presses. If arrow keys are captured while editing text, a reviewer cannot move the caret. Choose one focus model and state transitions before attaching roles.",
         code='function shouldUseInteractiveGrid({ editableCells, directionalSelection }) {\n  return editableCells || directionalSelection;\n}\nconsole.log(shouldUseInteractiveGrid({ editableCells: false, directionalSelection: false }));\n// Output: false',
         implementation="The code is a decision gate, not an accessibility implementation. For a read-only view, render a semantic table with headers and a link or button where an action exists. For an interactive grid, manage one Tab entry point and directional movement inside it; update focus and active-cell state together. When editing a text cell, hand arrow keys back to the text control until the user exits edit mode. Announce row and column context, preserve a stable active cell when data refreshes, and avoid virtualizing the focused row out of the DOM. Test the complete keyboard path with a screen reader rather than relying only on an automated role check.",
         cost="Rendering n rows with c cells is O(n × c) DOM nodes; virtualization can reduce mounted nodes but complicates row positions, focus, and assistive-technology context. A native table has low interaction-code cost. A grid adds state, key handling, and test cases for edit mode, selection, and data refresh. That expense is justified by frequent cell-level operations, not by a desire for a spreadsheet appearance. Measure task time and keyboard effort with real row counts; reducing DOM work while losing the active cell is not an improvement.",
         failure="A developer changes a table's outer role to grid and assumes screen readers will infer spreadsheet behavior. Arrow keys still scroll the page, while every nested button remains a separate Tab stop. Implement the grid contract or remove the role. Another defect occurs when a live sort removes the focused cell; focus falls to the document body and the next key acts elsewhere. Preserve active row and column identity through updates, or move focus to a clear fallback and announce that the row changed.",
         drill="Build a read-only 62-row queue with a real table and one case link per row. Test row and column announcements and count Tab stops. Then add an editable status cell and specify entry, editing, commit, cancel, and exit keys before considering a grid. Sort while the active cell is focused and verify a stable fallback. Render only a window of rows in a separate experiment, then test whether the active row remains mounted and total row context remains understandable.",
         decision="Use a table for comparison and reserve a grid for a real cell-level keyboard workflow you are prepared to implement.",
         checks=["Read-only rows retain correct header relationships.", "Grid mode has a documented entry, edit, and exit path.", "Sorting or virtualization does not discard focus silently."],
         mistakes=["Adding role=grid without directional keyboard behavior.", "Making every cell a Tab stop in a large table.", "Capturing arrow keys while an input needs them for text editing."],
         related=["web-tech/accessible-names-and-native-controls", "web-tech/accessible-feedback-and-keyboard", "web-tech/search-filters-and-result-cursors"]),
    dict(hub=1, path="web-tech/combobox-suggestions-and-active-option", title="Combobox Suggestions and Active Option",
         summary="Keep input editing intact while suggestions announce a stable active option and commit path.",
         definition="An editable combobox pairs a text input with a suggestion popup. It is more than a filtered list: the input needs a label, an expanded state, a relationship to the popup, a stable active option, and keyboard behavior for opening, moving, accepting, and dismissing suggestions. In a common pattern, DOM focus stays on the input while aria-activedescendant points to the active option. The referenced option must exist in the mounted popup and its ID must remain stable for the duration of that state. Down Arrow moves through available suggestions; Escape closes the popup; Enter accepts the active choice. Ordinary text-editing keys must keep their platform behavior.",
         case="A reviewer assigns case 47 to a colleague by typing a name. Suggestions arrive asynchronously, and the highlighted person changes after a newer query. The input currently says 'Ari', but an older 'Ar' request returns and replaces the popup. The active option ID now points to an unmounted row; a screen reader receives no useful suggestion. Tie results to the current query generation, keep the active index within bounds, and clear the active descendant when the list closes. A pointer click and keyboard Enter must commit the same person ID, not just the visible label.",
         code='function nextOptionIndex(current, direction, count) {\n  if (count === 0) return -1;\n  return Math.min(count - 1, Math.max(0, current + direction));\n}\nconsole.log(nextOptionIndex(1, 1, 3));\n// Output: 2',
         implementation="The index helper handles bounds; the component still needs a real label, input semantics, popup ownership, and a stable option-ID scheme. On query change, invalidate old results and decide whether to reset selection or preserve it only when the same option remains. Keep DOM focus on the input in the active-descendant model, and do not prevent default for printable keys or caret movement. Set expanded state only while the popup is actually visible. Announce result count sparingly; updating a live region on every keystroke can drown out the typed text. Provide a simple native selection alternative if the data set is small enough.",
         cost="Filtering n local options is O(n) per query; server search trades that work for network requests and ordering races. Rendering all n options can become expensive, but virtualizing the active option out of the DOM breaks the active-descendant reference. Keep a bounded result count or ensure the active item stays mounted. A debounce reduces requests but increases feedback delay. Accessibility work adds state transitions and testing time, which is why a native select or datalist may be preferable when its behavior meets the product need.",
         failure="The popup is hidden visually, but aria-expanded remains true and aria-activedescendant points to an option that was removed. Keyboard focus remains in the input while assistive technology expects a suggestion that no longer exists. Clear both states together on Escape or result replacement. Another implementation steals DOM focus into the list and breaks text editing; choose one focus model and test it. A delayed old response must not replace the latest query's suggestions or the selected person ID.",
         drill="Type 'Ar', then 'Ari', and return the first request last. Confirm the popup still represents 'Ari'. Use Down Arrow, Up Arrow, Enter, Escape, Tab, Home, and End while checking that text editing remains possible. Delete all text and verify the active descendant is cleared when no options remain. Select by pointer and keyboard and compare submitted person IDs. Shrink results while the final option is active; focus should move to a valid mounted option or return to the input clearly.",
         decision="Implement one focus model completely and keep active option, popup visibility, and current query in agreement.",
         checks=["The active-descendant target exists whenever it is referenced.", "Escape closes suggestions without losing the input's text-editing path.", "Old search results cannot replace a newer active list."],
         mistakes=["Using a listbox role without maintaining input and popup state.", "Referencing an unmounted active option after filtering.", "Stealing focus from an editable input on every arrow key."],
         related=["web-tech/asynchronous-field-validation-races", "web-tech/search-query-normalization-and-ranking", "web-tech/accessible-feedback-and-keyboard"]),
    dict(hub=1, path="web-tech/reorder-controls-without-dragging", title="Reorder Controls Without Dragging",
         summary="Give priority changes a keyboard and single-pointer path that uses the same ordered mutation.",
         definition="Dragging can make reordering appear direct, but it is not a complete input contract. Provide a way to select an item and move it without holding a pointer down, and make the same operation available from the keyboard. Up and Down buttons, a move-to-position selector, or choose-item-then-target mode can express the action. The underlying mutation should accept a stable item ID and destination, not a DOM index that shifts when filtering or concurrent edits occur. Announce the new position and keep focus on the moved item or its control. A server-side version check is needed if multiple reviewers can reorder the same queue.",
         case="A reviewer moves case 47 above case 62 in the priority queue. Pointer drag works on a large monitor, but a user with limited dexterity cannot hold and move the pointer accurately. Add Move up and Move down buttons, and offer a click-then-target path when many positions exist. A keyboard user can operate those controls and hears 'Case 47, position 3 of 12' after the move. If another reviewer changed the queue while this action was in flight, the server rejects the stale ordering version and returns the current order for repair.",
         code='function moveCase(order, caseId, destinationIndex) {\n  const remaining = order.filter(id => id !== caseId);\n  remaining.splice(destinationIndex, 0, caseId);\n  return remaining;\n}\nconsole.log(moveCase([47, 62, 93], 47, 1).join(","));\n// Output: 62,47,93',
         implementation="The array transformation is a client-side ordering step; validate the destination range, item membership, and queue version at the server before persisting. Both drag and button paths should call the same mutation function. Keep button labels contextual, such as 'Move case 47 up', and disable only impossible moves at list boundaries while preserving clear position feedback. After success, place focus predictably; after a conflict, restore or reconcile the current order and explain the change. A single-pointer alternative must not require dragging even if a keyboard route also exists.",
         cost="Filtering and inserting in an array of n IDs is O(n) time and O(n) additional memory for the new order. Persisting the entire order can be expensive for a long queue; a rank key or neighbor-based command may reduce payload but adds conflict and compaction concerns. Extra controls occupy space, yet they remove a hard input barrier. Measure completion time with keyboard, touch, and pointer, not only drag speed. Frequent reorder announcements should stay concise so assistive technology does not repeat the whole queue.",
         failure="The UI stores only source and destination DOM indexes. A filter removes a row between drag start and drop, so the wrong case moves. Use stable IDs and a queue version. Another implementation supplies keyboard controls but no single-pointer alternative to dragging; a touch user who cannot drag still has no way to choose a destination. Provide explicit buttons or a selection mode reachable by one or more taps, and verify the same server mutation receives the intended item ID.",
         drill="Reorder a 12-case list with keyboard only, then with taps that never hold a pointer down. Move the first and last items and inspect disabled boundary controls. Filter the list mid-operation and verify the selected stable ID still identifies the right case. Apply a concurrent reorder from a second session before saving; the first client must show a conflict and updated positions. Keep focus on case 47's control after a successful move and announce its new position once.",
         decision="Treat drag as one optional gesture over an ID-based reorder command that also has keyboard and non-drag pointer controls.",
         checks=["Every drag action has a keyboard and non-drag pointer route.", "A filtered list cannot cause the wrong item to move.", "Focus and position feedback follow the moved case."],
         mistakes=["Persisting DOM indexes instead of stable item IDs.", "Offering keyboard support but no non-drag pointer path.", "Moving focus to the document body after reordering."],
         related=["web-tech/accessible-names-and-native-controls", "web-tech/conditional-writes-and-lost-update-prevention", "web-tech/accessible-feedback-and-keyboard"]),
    dict(hub=1, path="web-tech/async-status-announcements-and-focus", title="Async Status Announcements and Focus",
         summary="Report background results without stealing focus or repeatedly announcing an entire region.",
         definition="An asynchronous update needs a communication policy. A short nonurgent status can be announced through a polite live region; a blocking error may need an alert or direct focus on an error summary. Neither choice should be applied mechanically. A live region announces changed text, so replacing a whole panel can cause excessive speech or no useful announcement depending on timing. Keep the region mounted, update a concise message when a meaningful state changes, and avoid repeating identical messages for every network tick. Focus should remain where the person is working unless a route transition or error recovery requires a deliberate move.",
         case="Reviewer 29 resolves case 47 while typing a note in another panel. The server accepts the status change; the page should say 'Case 47 resolved' once, but leave focus in the note field. A conflict is different: the attempted action did not complete, so an error summary should identify the case and offer a route to the conflicting field or latest record. A progress stream sending 62 updates per second should not announce each percentage. Coalesce progress to meaningful thresholds and show persistent visible text for anyone who misses a spoken update.",
         code='function announcementFor(state, caseId) {\n  if (state === "saved") return `Case ${caseId} saved`;\n  if (state === "conflict") return `Case ${caseId} changed elsewhere`;\n  return "";\n}\nconsole.log(announcementFor("conflict", 47));\n// Output: Case 47 changed elsewhere',
         implementation="The function yields short messages; the UI decides which mounted region owns them. Use a polite region for completed background work that does not require immediate interruption, and a focused error summary when the user must fix a failed submission. Avoid making a whole list live; announce only the status change. Keep messages visually present and programmatically associated with the affected control. If the same text must be announced again after a later action, ensure there is an actual state change rather than forcing a rapid empty-then-filled trick that may be unreliable across assistive technologies.",
         cost="Generating a short message is O(1), while rerendering or announcing n changing rows can create O(n) DOM and speech work. Throttling progress reduces announcements but may leave a brief gap between internal and spoken state; that is acceptable when a persistent visual status remains accurate. Moving focus has a larger human cost than its computational cost, especially during typing. Test with a screen reader and keyboard under real network delays, including success, timeout, conflict, and route change. Automated checks can verify attributes but cannot judge whether the announcement rate is usable.",
         failure="A developer adds aria-live to the entire activity list. Every streamed row causes the screen reader to repeat unrelated content while the reviewer types. Another developer focuses the success toast after every save, moving the caret out of the note field. Replace both with a stable, small status region and preserve focus for routine success. For a blocking error, move focus to a concise summary only after the failed operation is known, and provide a clear way back to the field. Cancel stale announcements from a prior route generation.",
         drill="Save case 47 while typing in a note field and verify focus and caret remain. Trigger a version conflict and inspect the error summary, its associated controls, and focus order. Stream 62 progress updates and count spoken messages; the result should be bounded and meaningful. Switch routes before the old request completes and confirm no old status is announced on the new page. Repeat with a screen reader and without one to ensure the persistent visible status carries the same outcome.",
         decision="Announce the smallest meaningful state change and move focus only when the person's next action requires it.",
         checks=["Routine success leaves keyboard focus in the active task.", "A blocking error has a discoverable recovery path.", "Rapid progress updates do not flood the live region."],
         mistakes=["Making an entire changing list a live region.", "Stealing focus for routine success notifications.", "Announcing stale results after a route change."],
         related=["web-tech/accessible-feedback-and-keyboard", "web-tech/form-errors-and-recovery-paths", "web-tech/react-effects-and-request-races"]),
]

assert len(hubs) == 2 and len(topics) == 8
assert [sum(topic["hub"] == hub for topic in topics) for hub in (0, 1)] == [4, 4]


def add_entry(path, title, summary, entry_type, section_path, order):
    assert path not in by_path, path
    template = "web-tech/getting-started" if entry_type == "article" else "web-tech/web-technology"
    entry = copy.deepcopy(by_path[template])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), type=entry_type,
                 path=path, title=title, summary=summary, category="Web Development",
                 subject="web-tech", difficulty="Intermediate" if entry_type == "article" else None,
                 tags=["web-tech", "web-development"], sort_order=2300 + order,
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
    subprocess.run(["node", "--check", "--input-type=module"], input=topic["code"],
                   text=True, capture_output=True, check=True)
    siblings = [item["path"] for item in topics if item["hub"] == topic["hub"] and item["path"] != topic["path"]]
    related = [hubs[topic["hub"]]["path"]] + siblings + topic["related"]
    body = para(topic["definition"])
    body += "<h2>Working case</h2>" + para(topic["case"])
    body += '<h2>Implementation boundary</h2><pre><code class="language-javascript">' + html.escape(topic["code"], quote=False) + "</code></pre>"
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

crosslinks = {
    "web-tech/fetch-status-and-abort": [hubs[0]["path"], topics[0]["path"], topics[2]["path"]],
    "web-tech/cooperative-main-thread-scheduling": [topics[1]["path"]],
    "web-tech/live-update-reconnect-and-order": [topics[2]["path"]],
    "web-tech/accepted-operations-and-status-resources": [topics[3]["path"]],
    "web-tech/accessible-names-and-native-controls": [hubs[1]["path"], topics[4]["path"], topics[6]["path"]],
    "web-tech/accessible-feedback-and-keyboard": [topics[5]["path"], topics[7]["path"]],
    "web-tech/search-query-normalization-and-ranking": [topics[5]["path"]],
    "web-tech/conditional-writes-and-lost-update-prevention": [topics[6]["path"]],
}
for path, targets in crosslinks.items():
    entry = by_path[path]
    entry["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": len(hubs), "new_lessons": len(topics)}))
