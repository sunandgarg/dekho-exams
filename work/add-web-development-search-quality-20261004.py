"""Add original application search and quality engineering curriculum."""

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
    dict(path="web-tech/application-search-and-retrieval", title="Application Search and Retrieval",
         summary="Build searchable case records without losing freshness, stable ordering, or access control.",
         overview="A search box is an interface to several contracts at once. The write model owns case truth, the index owns a searchable projection, the query parser owns intent, and authorization owns visibility. A fast result that includes a revoked case is wrong. A perfectly secure result that changes order between pages is hard to use. This track follows one case-inspection service through ingestion, ranking, filters, and permission changes. Every lesson names the tradeoff it introduces and the evidence needed before release.",
         bridges=["web-tech/indexes-and-query-plans", "web-tech/cursor-pagination", "web-tech/record-level-authorization"]),
    dict(path="web-tech/quality-and-capacity-engineering", title="Quality and Capacity Engineering",
         summary="Choose test boundaries, inject failures, check usable screens, and measure load against a budget.",
         overview="A passing test count says little about a web product if the tests do not observe the boundary most likely to fail. Pure rules, database transactions, API contracts, browser tasks, and loaded traffic each reveal different defects. The case-inspection service gives these checks a shared workload: a reviewer searches, opens, edits, and resolves a case while requests sometimes fail and traffic sometimes rises. The objective is a compact evidence set that explains behavior and recovery, not a collection of snapshots that merely repeat the current implementation.",
         bridges=["web-tech/contract-tests-across-boundaries", "web-tech/browser-journey-and-fault-tests", "web-tech/performance-budget-and-layout-stability"]),
]

topics = [
    dict(path="web-tech/search-index-freshness-and-rebuilds", hub=0, title="Search Index Freshness and Rebuilds",
         summary="Define when committed case changes become searchable and how a new index replaces an old one.",
         definition="An application search index is a derived view of records, not the authority for their contents. A case update can commit successfully while the indexing worker is delayed, so search results may lag behind the detail page. Define the allowed lag for each action. Newly published public content may tolerate a short delay; a revoked private case should disappear from results immediately through an independent permission check. Record a monotonically increasing version or update sequence on each case. The indexer can then ignore older events that arrive after newer ones, and a rebuild can compare its catch-up position with the source log before switching readers.",
         case="Case 47 is reassigned from team East to team West while a queue worker is retrying an older update. The old event reaches the search index last and restores an obsolete team label. A reviewer now sees a result that points to a case they cannot open. Store version 62 with the new projection and reject version 61 if it arrives late. When rebuilding the index, write to a separate generation, replay changes committed during the scan, verify counts and representative records, then switch the read alias only after the new generation catches up.",
         code='function acceptIndexEvent(currentVersion, incomingVersion) {\n  if (!Number.isSafeInteger(incomingVersion) || incomingVersion < 1) throw new Error("Invalid version");\n  return currentVersion === null || incomingVersion > currentVersion;\n}\nconsole.log(acceptIndexEvent(62, 61));\nconsole.log(acceptIndexEvent(62, 63));\n// Output: false\n// true', language="javascript",
         implementation="The version guard handles out-of-order delivery but does not make two writes atomic across a database and search service. Use a durable change record, such as an outbox entry committed with the case update, and make the index operation idempotent. Measure lag from source commit to visible search result and alert on sustained growth. During a rebuild, keep the old generation readable until the new one passes reconciliation; retain a rollback handle for the index mapping. Detail reads and permission decisions still come from the authoritative application path.",
         cost="Each write now creates index work and a small version check. A replayable change log and two temporary index generations consume storage during rebuild. The guard itself is O(1), while rebuilding n records costs at least O(n) reads and index writes; the exact wall time depends on tokenization, hardware, and concurrent traffic. A stricter freshness target requires more worker capacity and tighter monitoring. Avoid promising immediate consistency for every search field when the architecture intentionally processes changes after commit.",
         failure="A worker retries version 61 after version 62 and the index accepts both without ordering. Search shows the old assignment for hours because no later update arrives. Another failure happens when a rebuilt generation is switched into service before the tail of the change log is replayed. Test reversed event order and a rebuild under continuous writes. A successful case-detail request is insufficient evidence: compare source versions with index versions and inspect the result from a real search query.",
         drill="Create cases 47 and 62, update each twice, and deliver events in reverse order. Record source and indexed versions after each attempt. Start a rebuild while another update commits; do not switch readers until the generation contains that update. Measure the oldest unindexed event age, not only queue length. Finally revoke access and verify a stale index entry cannot produce a visible result for the former team.",
         decision="Use a derived index when retrieval needs justify it, but design versioning, reconciliation, and permission checks before promising search freshness.",
         checks=["Deliver older events after newer ones and verify the indexed version never goes backward.", "Rebuild under active writes and compare source and indexed versions before switching readers.", "Revoke a case and confirm stale indexed metadata does not reveal it to the former team."],
         mistakes=["Treating the index as the sole source of case truth.", "Switching a rebuilt index before replaying writes from the rebuild window.", "Monitoring worker success while ignoring visible indexing lag."],
         related=["web-tech/indexes-and-query-plans", "web-tech/idempotent-write-requests", "web-tech/record-level-authorization"]),
    dict(path="web-tech/search-query-normalization-and-ranking", hub=0, title="Search Query Normalization and Ranking",
         summary="Interpret query text deliberately, rank useful results, and keep a stable tie-breaker.",
         definition="A search query is more than a string comparison. Normalize whitespace and case for the fields where that behavior is useful, cap the input length, and decide how quotes, prefixes, punctuation, and empty searches behave. The server must not treat user text as a raw query language unless advanced syntax is an intentional feature with limits. Ranking also needs a product rule: an exact case identifier might outrank a title match, while a title match might outrank a note-body match. Relevance scores can tie or shift after reindexing; add a stable secondary key so two equal results do not swap places between requests.",
         case="A reviewer searches for case 47 by number while another searches for a damaged lift label. The first should reach the exact record quickly; the second needs descriptive matches, not fifty notes where the word appears once in boilerplate. Rank identifier matches above title matches, then sort equal-scored results by an immutable case ID. Show a result excerpt only from approved, escaped fields. Record several representative queries and expected top results as acceptance data. Relevance is an editorial and product decision, not a database default that can be assumed correct.",
         code='function normalizeCaseQuery(rawQuery) {\n  if (typeof rawQuery !== "string") throw new Error("Query must be text");\n  const normalized = rawQuery.trim().replace(/\\s+/gu, " ");\n  if (normalized.length > 96) throw new Error("Query too long");\n  return normalized.toLocaleLowerCase("en");\n}\nconsole.log(normalizeCaseQuery("  Lift   47  "));\n// Output: lift 47', language="javascript",
         implementation="The snippet establishes one small input contract; it does not implement tokenization or ranking. Language-aware case folding may need a different locale policy, and identifiers should not be stemmed like prose. A database full-text facility can supply token matching, while an explicit score expression can combine exact ID, title, and body signals. Keep score math and tie-breakers testable. Reject queries that consume excessive work, and make empty input a documented browse or zero-result state rather than running an expensive accidental scan.",
         cost="Normalization scans the query once, O(q) in its length, and bounded q keeps that cost predictable. Ranking m candidate records costs at least O(m) score work, often with additional sort cost up to O(m log m) unless an index or search engine can provide an ordered top-k plan. Richer relevance can improve finding cases but makes explanations and pagination harder. Measure top-result quality on real tasks and query latency together; a scoring change that improves one benchmark may hurt another query class.",
         failure="An unbounded query with repeated operators triggers expensive parsing, while the UI treats a timeout as no matches. Separately, equal-ranked cases reorder between page requests because there is no stable secondary key. Add a bounded input contract, return a distinct search error, and include case ID in the sort. Test exact ID, punctuation, mixed case, empty input, and ties. Do not copy raw query text into a log or a result snippet when it may contain private information.",
         drill="Write ten search tasks from the case workflow: exact ID, title phrase, short misspelling, punctuation, and a query with no useful tokens. For each, define whether it should match and what should lead. Run the set after each ranking change and record both top-three results and query duration. Repeat the equal-score case across pages and deployments to expose unstable ordering. Keep the test set free of real private notes.",
         decision="Define a small query grammar and an explicit relevance policy, then evaluate both usefulness and response cost with representative tasks.",
         checks=["Normalize repeated whitespace and reject overlong or non-text input.", "Verify exact ID and title matches outrank weak body matches for the chosen task set.", "Repeat tied-score queries and confirm stable ordering by immutable ID."],
         mistakes=["Passing untrusted text directly into a raw query expression.", "Assuming a search engine default score matches product tasks.", "Sorting only by a score that can tie or change during pagination."],
         related=["web-tech/search-index-freshness-and-rebuilds", "web-tech/form-server-validation", "web-tech/cursor-pagination"]),
    dict(path="web-tech/search-filters-and-result-cursors", hub=0, title="Search Filters and Result Cursors",
         summary="Bind filters and sort order to a cursor so moving through results stays coherent.",
         definition="A result cursor identifies where to continue a specific ordered search. It is not merely a page number and should not be accepted after the user changes the query, filters, or sort. For a score-based order, the cursor needs the last score and a stable unique tie-breaker. It should also bind the normalized query and filter set, directly or through a server-side reference, so a cursor from one search cannot silently continue another. A bounded result window avoids returning an entire index hit set to the browser. Decide what happens when the index changes between pages: a live feed may allow shifts, while an audit task may need a snapshot.",
         case="Reviewer 29 filters open cases in region North, then changes the region to South while a request for the next North page is still running. If the old cursor is reused, the list skips or repeats cases in the new region. The UI must clear pagination state when any search dimension changes and ignore a late response from the old search. The server independently validates the cursor against the active query and filter values. A stable case ID breaks score ties so two records with equal relevance do not trade positions.",
         code='function cursorMatchesSearch(cursor, normalizedQuery, region, status) {\n  return cursor.query === normalizedQuery && cursor.region === region &&\n    cursor.status === status && Number.isSafeInteger(cursor.lastCaseId);\n}\nconsole.log(cursorMatchesSearch({ query: "lift", region: "north", status: "open", lastCaseId: 47 }, "lift", "south", "open"));\n// Output: false', language="javascript",
         implementation="The illustration checks binding but is not a complete cursor format. Production cursors should be opaque to clients and authenticated or stored server-side so callers cannot alter positions or filters. Apply authorization and filter predicates before selecting the page; fetching an unrestricted page and hiding rows afterward can produce short pages and leak aggregate information. Return the next cursor only when more authorized results exist. Keep the sorting tuple and cursor decoding under version control so a changed ranking formula does not misread older cursors.",
         cost="Seek pagination can avoid the skip work of large offsets, but a compound score and ID sort needs index or search-engine support. Each page returns O(k) records for page size k; authorization and ranking may inspect more candidates. A snapshot improves consistency but costs state or storage and can retain outdated results. Expiring a cursor is simpler, though users may need to restart a search. Cap page size and cursor age, and measure how many candidates are evaluated to deliver one authorized page.",
         failure="The UI preserves an old cursor after a filter change, and the backend accepts it because it only decodes lastCaseId. A case disappears from the result set and the user thinks the region has no more work. Another service filters unauthorized hits after limiting, returning three items on a twenty-item page even when more allowed results exist. Bind cursor to search dimensions and apply permission predicates before page selection. Test filter changes, tied scores, expiry, and records inserted between pages.",
         drill="Search for lift, filter North/open, advance one page, then switch to South/open before the earlier request completes. Verify that the old response cannot replace the new page. Alter each cursor dimension and expect rejection or restart. Seed equal scores around a page boundary and check for duplicates or omissions. Revoke access to one record in the middle and measure whether the next page still fills with authorized results when enough remain.",
         decision="Use a cursor when ordered result sets can grow large, and bind it to the complete query context with a defined change policy.",
         checks=["Change query, region, status, and sort independently; old cursors must not continue the new search.", "Page across equal-score records without duplicates or gaps.", "Revoke an in-range record and verify page selection still follows permission rules."],
         mistakes=["Reusing a cursor after filters change.", "Encoding only an offset or case ID for a relevance-ordered result set.", "Hiding unauthorized records after limiting the page."],
         related=["web-tech/cursor-pagination", "web-tech/react-effects-and-request-races", "web-tech/record-level-authorization"]),
    dict(path="web-tech/search-permissions-and-private-results", hub=0, title="Search Permissions and Private Results",
         summary="Apply record authorization inside retrieval and prevent snippets, counts, and suggestions from leaking.",
         definition="Search authorization must cover the whole response, not only the link opened after a result click. Titles, snippets, total counts, facets, autocomplete suggestions, and timing can all reveal that a private record exists. A search index often holds stale permission fields because membership changes separately from content. Define the security source of truth, then make query-time filtering or a trusted permission join part of result selection. Recheck access when the detail route opens and before mutations. If a search backend uses document-level rules, test their role-combination behavior and ensure application permissions map to those rules correctly.",
         case="Team East loses access to case 47 at noon. The case's indexed title remains until a worker catches up. At 12:01, an East reviewer searches for the equipment name. A detail-page 403 prevents reading the record, but a search card that displays its title and excerpt still discloses information. The query path must exclude it using current rights; counts and suggestions must use the same scope. A shared link to the former result should still return a permission decision from the primary service.",
         code='function visibleCaseResults(candidates, allowedCaseIds) {\n  return candidates.filter(caseRecord => allowedCaseIds.has(caseRecord.caseId))\n    .map(caseRecord => ({ caseId: caseRecord.caseId, title: caseRecord.title }));\n}\nconsole.log(visibleCaseResults([{ caseId: 47, title: "Pump" }, { caseId: 62, title: "Lift" }], new Set([62])));\n// Output: [ { caseId: 62, title: \'Lift\' } ]', language="javascript",
         implementation="This small function demonstrates a projection after an authorization decision; a production search must apply the visibility constraint before ranking, pagination, facets, and counts. Otherwise it can leak totals and produce sparse pages. The allowed set cannot be taken from a client claim. Derive it from the authenticated principal, current team membership, and record policy, preferably as a query predicate or secure search role. If fine-grained joins are expensive, consider an authorized candidate window followed by controlled refill, while keeping a hard cap and no private aggregate signals.",
         cost="Checking every candidate after a broad search can be expensive and may expose page shape. Permission-aware indexing or query filters improve retrieval but add update work when membership changes. Query-time joins to the authoritative store provide fresher decisions with database and network cost. Choose according to the sensitivity of records and the required revocation speed; benchmark worst-case teams with few allowed hits. A cache of permissions needs a short, explicit lifetime and invalidation route for revocation, not an indefinite success entry.",
         failure="A developer filters visible cards but leaves the unfiltered total count and autocomplete endpoint. The team can infer private case activity even though detail routes reject access. In another failure, two roles combine unexpectedly in the search service and one grants broader visibility than intended. Test one user with multiple roles, revocation during an active session, empty authorized result sets, and a stale index. Inspect all response fields and suggestions, not only the rendered cards.",
         drill="Create two teams and seed cases with distinctive titles. Remove one team membership while keeping the search index stale. Search, request suggestions, inspect facets and totals, follow an old result link, and try a mutation. No private title or count should appear, and each authoritative route should deny the old member. Repeat with a user holding two roles. Record query work and refill behavior so the secure path is also usable under sparse visibility.",
         decision="Treat search as a protected read API. Apply current permissions before any result-derived content is exposed.",
         checks=["Revoke access while indexed content remains stale and inspect cards, snippets, counts, facets, and suggestions.", "Combine roles and verify the intended visibility intersection or union explicitly.", "Open and mutate a formerly visible case; both routes must recheck current authority."],
         mistakes=["Relying on detail-page authorization while search exposes private metadata.", "Filtering cards but returning unfiltered counts or suggestions.", "Caching permission results without a revocation strategy."],
         related=["web-tech/record-level-authorization", "web-tech/search-index-freshness-and-rebuilds", "web-tech/search-filters-and-result-cursors"]),
    dict(path="web-tech/test-boundaries-and-evidence-selection", hub=1, title="Test Boundaries and Evidence Selection",
         summary="Place checks where each failure can be observed rather than repeating one assertion at every layer.",
         definition="A test boundary is the real interface a check exercises: a pure rule, a database transaction, an HTTP contract, or a browser task. Moving closer to a real system catches wiring failures but adds setup and slower execution. Choose evidence from the risk. A pure permission predicate deserves fast table tests, yet an API still needs a test proving the authenticated user and stored record reach that predicate correctly. A browser journey should verify one meaningful reviewer task and its accessible feedback, rather than restating every branch already covered by lower-level checks.",
         case="The case service approves a status transition from open to resolved only after a reviewer note is saved. A unit test of the transition rule passes. The HTTP handler, however, writes the status before the note and a database error leaves the case resolved without evidence. A transaction-level test catches this state violation; an API test catches status codes and response shape. A browser task then confirms the reviewer sees a clear result and can retry safely. Each check answers a different question, so a suite of only unit tests cannot replace the others.",
         code='function mayResolveCase(caseRecord) {\n  return caseRecord.status === "open" && caseRecord.reviewNotes.length > 0;\n}\nconsole.log(mayResolveCase({ status: "open", reviewNotes: ["Valve checked"] }));\n// Output: true', language="javascript",
         implementation="Keep pure rules independent of transport for cheap edge-case coverage. At the transaction boundary, use a real test database with rollback or isolated fixtures so commit behavior is observed. At the API boundary, send an authenticated request and inspect status, body, and stored outcome. Use browser automation for the smallest set of user tasks that can fail through layout, focus, routing, or response handling. A test double can be useful for a remote service, but it should not invent a contract different from the actual integration.",
         cost="Pure tests run quickly and can cover many combinations; database and browser checks consume more setup and machine time. The right mix is not a fixed pyramid ratio. It follows failure cost and boundary uncertainty. Too many broad browser tests can make a release gate slow and brittle, while too few leave wiring and interaction defects unseen. Record what each test protects and remove redundant checks when another boundary supplies stronger evidence. Keep a small critical path suite fast enough to run on every change.",
         failure="A handler is refactored to save the note after committing the resolved status. Pure tests still pass because the rule never sees partial writes. A UI snapshot also passes because it mocks a successful response. The defect reaches production and cannot be repaired by a visual comparison. Add a transaction test that injects the note-write failure and asserts the record remains open. Keep the UI check for visible recovery, where it provides evidence the transaction test cannot.",
         drill="List five possible failures in the resolve workflow: invalid transition, missing transaction, wrong HTTP status, stale UI message, and inaccessible error feedback. Assign the cheapest boundary that can actually observe each one. Write one failing test per boundary, then remove duplicate assertions that only mirror internal code. Review the suite after a refactor and ask whether each failure would still turn a test red. That question matters more than aggregate pass count.",
         decision="Select tests by observable risk and boundary, then keep only the repetition that catches a distinct class of defect.",
         checks=["Fail the note write and verify the transaction preserves the prior case state.", "Exercise an authenticated API request and inspect both response and stored result.", "Complete one browser task with keyboard and error feedback checks."],
         mistakes=["Calling a pure rule test proof of transaction atomicity.", "Mocking the handler response in the only browser journey.", "Counting tests without naming the failure each one can detect."],
         related=["web-tech/contract-tests-across-boundaries", "web-tech/transactions-and-concurrent-writes", "web-tech/browser-journey-and-fault-tests"]),
    dict(path="web-tech/deterministic-test-doubles-and-fault-injection", hub=1, title="Deterministic Test Doubles and Fault Injection",
         summary="Control failure timing without erasing the integration behavior the product depends on.",
         definition="A test double replaces a dependency for one check. It is useful when a remote service is slow, costly, or hard to make fail on command. The risk is a double that always returns a convenient success and hides real status, timing, or payload behavior. Define the observed contract first, then make the double expose the same meaningful states: success, rejection, timeout, retryable failure, and duplicate delivery where relevant. Use a deferred response to control order in race tests. Keep a separate contract check against the real boundary so the double does not become an alternate specification.",
         case="A browser route fetches case 47, then case 62. In normal development both responses finish quickly, so the stale-result bug rarely appears. A deferred transport can resolve 62 first, then 47, every time. The assertion should check that the panel stays on 62 and that an old error cannot replace the current route's state. For a webhook, a different double can deliver the same event twice and check idempotency. The shared idea is controlled uncertainty; the exact script depends on the contract being tested.",
         code='function deferredResponse() {\n  let release;\n  const promise = new Promise(resolve => { release = resolve; });\n  return { promise, release };\n}\nconst case47 = deferredResponse();\nconst case62 = deferredResponse();\ncase62.release({ caseId: 62 });\ncase47.release({ caseId: 47 });\nconsole.log((await case62.promise).caseId);\n// Output: 62', language="javascript",
         implementation="The deferred helper controls completion order and can be extended with reject and abort paths. Do not insert arbitrary sleeps into a race test: fixed delays are slow and can still fail unpredictably on a loaded machine. Assert after both promises settle and make the current route identity part of the observed state. For HTTP integrations, record real status and payload expectations in contract fixtures and refresh them under review when a provider changes. Keep one environment-level smoke check for authentication, headers, and network behavior that a local double cannot cover.",
         cost="A deferred helper has constant setup work and uses memory for outstanding promises until they settle. More elaborate doubles cost maintenance: every simulated state is another behavior to keep aligned with reality. Fault injection in a test database or controlled staging service can give stronger evidence but costs setup and cleanup. Use the simplest control that exposes the target failure. A long suite full of sleeps and random retries spends time without making failures easier to reproduce or explain.",
         failure="A route test mocks fetch with an immediate resolved object, so it never sees old request completion. In production, a slow case 47 response overwrites case 62. The team adds a hundred-millisecond sleep but the test is flaky because completion order still varies. Replace the sleep with explicit deferred responses, run both orders, and fail the old request after the route changes. Also test cleanup on unmount. Keep a real API contract check so the artificial response shape cannot drift unnoticed.",
         drill="Write a transport double with named controls for resolve, reject, and abort. Start requests for cases 47 and 62, settle them in both orders, and record the visible case ID and error state after each step. Inject a timeout for the current request and an error for the obsolete one. Then run one request through the actual HTTP handler with raw JSON to verify that the double's fields and status assumptions still match the service.",
         decision="Use deterministic doubles for timing and rare failures, and pair them with a separate check of the real integration contract.",
         checks=["Resolve current and obsolete requests in both orders without sleeps.", "Reject the obsolete request and confirm it cannot replace the current error or success state.", "Compare double payloads and statuses with a real API boundary check."],
         mistakes=["Using arbitrary delays to provoke races.", "Mocking away every integration check with invented success objects.", "Testing only the success callback while an obsolete error path remains active."],
         related=["web-tech/react-effects-and-request-races", "web-tech/contract-tests-across-boundaries", "web-tech/idempotent-write-requests"]),
    dict(path="web-tech/accessibility-and-visual-regression-checks", hub=1, title="Accessibility and Visual Regression Checks",
         summary="Check task usability, keyboard behavior, and stable layout with evidence beyond a screenshot.",
         definition="A visual comparison can detect unexpected layout changes, missing elements, and clipped content. It cannot prove that a control has an accessible name, that focus reaches an error, or that a live region announces a result. Combine a small set of stable screenshots with semantic and keyboard assertions tied to the task. Capture the same viewport, content, fonts, and motion state each run; otherwise image differences become noise. Test real error and loading states, not only the polished successful page. Human review remains useful for meaning, reading order, contrast in context, and whether the workflow is understandable.",
         case="The case review page receives a CSS change. A screenshot catches that the Save button is pushed below the viewport, but it cannot tell that the validation message is not connected to the note field. A keyboard task reveals that focus jumps to the page header after submit and the reviewer never hears the error. Check both: a visual baseline for critical layouts and assertions for label, described error, focus destination, and status announcement. Test at narrow width and with long translated text, where layout failures are likely to appear.",
         code='const expectedWorkflow = {\n  fieldName: "Inspection note",\n  errorText: "Add a note before resolving",\n  focusTarget: "inspection-note",\n  statusText: "Case 47 remains open"\n};\nconsole.log(expectedWorkflow.focusTarget);\n// Output: inspection-note', language="javascript",
         implementation="The object is a review contract, not an automated audit by itself. In a browser test, locate the field by its accessible name, submit an empty note, assert that the error is associated with the field, and inspect the focused element. Then capture a screenshot in a fixed environment. Prefer role and name selectors over private CSS classes so the test follows user-facing semantics. Suppress only known nondeterministic visuals, such as a clock, with an explicit reason; do not mask the entire panel that the test is supposed to protect.",
         cost="Screenshots can create large artifacts and review noise after intentional design changes. Semantic assertions run faster and pinpoint behavior, but cannot see every visual defect. Browser runs cost more than a pure test, so reserve them for critical workflows and state variants. Stabilizing fonts, viewport, and data reduces false positives. A human review of a handful of changed baselines costs attention but is preferable to automatic acceptance of a broken layout. Accessibility tools catch many patterns, yet task testing is still needed for flow and feedback.",
         failure="A snapshot update is accepted because every image changed after a font upgrade. The same change clips the error text at narrow width, and a focus bug makes the message hard to find. A pipeline that blindly refreshes baselines records the defect as the new normal. Review diffs at the relevant viewports, assert that the error remains visible, and run the keyboard journey. Keep test data long enough to expose wrapping; a one-word note rarely exercises the layout boundary.",
         drill="Submit the review form empty with mouse and keyboard. Check accessible name, field error association, focus, and status announcement. Capture stable screenshots for narrow and wide viewports before and after a deliberate CSS break. Identify which failure each kind of check catches and which it misses. Change the language to a longer label and repeat. Do not claim a passing automated check proves every assistive technology experience; document any manual review needed for the task.",
         decision="Pair visual checks with semantic and keyboard assertions for a few important states, then review baseline changes as product changes.",
         checks=["Submit an invalid note and verify label, error association, focus, and status feedback.", "Compare stable narrow and wide screenshots with long content.", "Review intentional baseline changes rather than automatically accepting every diff."],
         mistakes=["Treating screenshot equality as an accessibility test.", "Masking the region whose layout could fail.", "Refreshing baselines without inspecting the changed task state."],
         related=["web-tech/accessible-names-and-native-controls", "web-tech/accessible-feedback-and-keyboard", "web-tech/browser-journey-and-fault-tests"]),
    dict(path="web-tech/load-tests-and-capacity-budgets", hub=1, title="Load Tests and Capacity Budgets",
         summary="Model a realistic request mix and stop a release when latency or errors cross agreed limits.",
         definition="A load test asks how a system behaves under a stated arrival pattern, not how fast one isolated request can complete. Describe the journey mix, active users or arrival rate, test data, warm-up, and duration. Record latency distributions, error rate, saturation signals, and the operation that slows first. A capacity budget is a decision boundary agreed before running the test: for example, a search route may need to serve 47 requests per second for several minutes while preserving a selected tail-latency and error target. The numbers are product-specific hypotheses to verify, not universal standards.",
         case="After search launches, the case service sees bursts from shift changes. A test that repeatedly requests one cached case detail page reports a reassuring average. Real users search, filter, open cases, and save notes; those paths compete for database connections and index capacity. Build a mix that reflects these actions, seed enough cases to make the search index meaningful, and ramp arrivals to the expected burst. Watch high-percentile search latency, write failure rate, queue lag, CPU, and connection use. Stop when errors rise or the agreed budget is breached.",
         code='function withinCapacityBudget(result) {\n  return result.requestsPerSecond >= 47 && result.p95Milliseconds <= 420 &&\n    result.errorFraction < 0.01;\n}\nconsole.log(withinCapacityBudget({ requestsPerSecond: 49, p95Milliseconds: 390, errorFraction: 0.004 }));\n// Output: true', language="javascript",
         implementation="The function evaluates one report against an illustrative budget; a real test must measure the report with an instrumented runner and a stable environment. Separate offered load from completed throughput so overload cannot appear successful because the service simply drops work. Use open arrival models when the question is an external request rate, and user-loop models when the question is a population performing tasks with think time. Tag search, detail, and write operations so one cheap route cannot hide a slow critical route in the aggregate.",
         cost="A serious run consumes compute, test data, and engineer analysis time. Small smoke loads can run in a release pipeline; longer capacity studies belong in a controlled environment that resembles production enough to expose shared bottlenecks. Ramp slowly to distinguish steady behavior from cold starts, then include a short burst and recovery period. Higher concurrency may increase queueing faster than throughput. The test must not use private production records or send artificial writes into a live customer environment without a planned boundary.",
         failure="A report checks mean latency only. Most search requests complete quickly, but one in twenty waits several seconds after the connection pool saturates. The average still looks acceptable, and the release proceeds. Add a tail-latency threshold and inspect pool wait time, database plans, and index lag under the same request mix. Another common error is a closed-loop script that slows its own request generation as the server slows, masking overload. Compare offered and completed rates and rerun after a targeted change.",
         drill="Seed a nonprivate case dataset with varied titles and permissions. Define a mixed workload of search, detail, and note writes, then state throughput, tail latency, and error limits before the run. Ramp to 47 requests per second, hold, spike briefly, and observe recovery. Capture per-operation results and resource saturation. Repeat after one index or pool change and compare the same workload. If the environment differs from production, write down the limits of the conclusion.",
         decision="Tie capacity claims to a measured workload and explicit thresholds; a fast average from one cached route is not release evidence.",
         checks=["Measure offered and completed traffic with per-operation latency and error rates.", "Apply a predeclared tail-latency and error budget during sustained load and burst recovery.", "Inspect resource saturation and indexing lag before attributing a slow route to application code."],
         mistakes=["Using only mean latency as a release gate.", "Testing one cached request instead of the user journey mix.", "Letting a slowed closed-loop client silently reduce offered traffic."],
         related=["web-tech/performance-budget-and-layout-stability", "web-tech/indexes-and-query-plans", "web-tech/observability-and-recovery"]),
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
                 tags=["web-tech", "web-development"], sort_order=1800 + sort_order,
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

for path, targets in {
    "web-tech/data-persistence": [hubs[0]["path"]],
    "web-tech/integration-and-verification": [hubs[1]["path"]],
    "web-tech/indexes-and-query-plans": [topics[0]["path"], topics[1]["path"]],
    "web-tech/cursor-pagination": [topics[2]["path"]],
    "web-tech/record-level-authorization": [topics[3]["path"]],
    "web-tech/contract-tests-across-boundaries": [topics[4]["path"], topics[5]["path"]],
    "web-tech/browser-journey-and-fault-tests": [topics[6]["path"]],
    "web-tech/performance-budget-and-layout-stability": [topics[7]["path"]],
}.items():
    entry = by_path[path]
    entry["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": len(hubs), "new_lessons": len(topics)}))
