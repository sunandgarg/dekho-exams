"""Add original accessibility-review and product-analytics prompt curricula."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
lookup = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
subject_root = "prompt-engineering/prompt-engineering"
applications = "prompt-engineering/applications"
production = "prompt-engineering/production"
projects = "prompt-engineering/projects"
quizzes = "prompt-engineering/quizzes"

clusters = [
    {
        "label": "Accessibility review",
        "tag": "accessibility review",
        "order": 32100,
        "project": "prompt-engineering/harbor-booking-accessibility-review-project",
        "project_title": "Project: review Harbor booking access across states",
        "quiz": "quizzes/prompt-engineering-accessibility-review",
        "quiz_title": "Accessibility review prompt decisions",
        "intro": "A prompt can organize a review of observable interface states. It cannot infer keyboard behavior, spoken output, or conformance from a still image. Record the tested build and state, inspect native semantics and actual interactions, then send reproducible findings to an owner. Harbor Dispatch is a fictional booking interface used throughout these lessons.",
        "case": "Harbor Dispatch has a booking form, a confirmation dialog, and 47 queued jobs in its test dataset. The reviewer records build B-47, uses a keyboard to open and close the dialog, tests a failed form submission, and checks a narrow viewport. The initial finding is specific: after closing the dialog with Escape, focus moves to the page top rather than returning to the button that opened it. A screenshot alone could not establish that failure. The release decision waits for a repair and a repeat of the same steps.",
        "sample": "Build B-47 | booking form | test account without private data\nOpen dialog with keyboard; close with Escape\nObserved: focus at page top\nExpected: focus returns to opening button\nFinding: reproducible; owner and retest required",
        "cost": "Walking N focusable controls is O(N) interaction steps, and recording S meaningful interface states adds O(S) review records. Automated checks can scan markup quickly, but keyboard, zoom, and spoken feedback still require human verification. Save only the evidence needed to reproduce a finding; an unbounded transcript of every control makes the handoff slower to inspect.",
        "mistakes": ["Do not claim accessibility from a screenshot alone.", "Do not treat a model's suggested fix as a verified repair.", "Do not release a finding without the tested build and interaction steps."],
        "specs": [
            {
                "slug": "accessibility-prompt-page-state-evidence-contract",
                "title": "Accessibility prompts: identify the tested page state",
                "section": applications,
                "summary": "Pin the build, route, viewport, interaction state, and available evidence before asking for a finding.",
                "definition": "An accessibility review prompt needs a state contract: build identifier, route, viewport, zoom level, language, authentication state, interaction path, and evidence type. A DOM snapshot, accessibility tree, screenshot, and recorded keyboard trace answer different questions. Ask the model to label direct observations separately from hypotheses and untested behavior. The reviewer must reproduce an interactive claim in the browser. Without a stable state, a later fix can be judged against a different interface than the one that failed.",
                "case": "Harbor's booking form has an idle state and a failed-submit state. A screenshot of the idle form shows the visible labels, but it says nothing about where focus lands after validation or whether an error is announced. The reviewer captures build B-47, the failed-submit path, a keyboard trace, and the resulting DOM. The prompt may ask which evidence is missing; it must return 'untested' for spoken output until a screen-reader check occurs.",
                "sample": "Route: /booking; build: B-47\nState: failed submit with required pickup code blank\nEvidence: DOM snapshot + keyboard trace\nNot observed: screen-reader announcement\nOutput: observation | hypothesis | test still needed",
                "cost": "Capturing S states costs O(S) records and at least O(S) manual transitions; comparing DOM snapshots can cost O(N) in the number of nodes per state. Recording one stable state contract per finding is cheaper than retesting an ambiguous report. Keep sensitive account data out of traces and attach the minimum route and control labels needed to reproduce the issue.",
                "mistakes": ["Do not infer spoken behavior from pixels.", "Do not omit build or state when reporting a failure.", "Do not label an untested concern as an observed defect."],
                "related": ["prompt-engineering/ui-visual-and-accessibility-release-gate", "prompt-engineering/evidence-id-traceability"],
            },
            {
                "slug": "accessibility-prompt-semantics-name-role-and-value",
                "title": "Accessibility prompts: check semantics and control names",
                "section": applications,
                "summary": "Review native structure and the exposed name, role, and state of each control.",
                "definition": "A visual label is not proof of an accessible name. Supply a DOM or accessibility-tree excerpt and ask the model to compare the visible control with its exposed name, role, value, and state. Prefer native form controls, links, headings, and landmarks because they carry interaction behavior the browser already knows. Custom semantics need runtime checks. The prompt should locate missing or conflicting names, but the reviewer confirms how a real control is announced and operated rather than grading a static HTML fragment in isolation.",
                "case": "The Harbor dialog has a visible cross icon with a click handler. Its DOM uses a plain span, so it is absent from the tab sequence and lacks a button role and name. The proposed repair uses a button with a concise 'Close booking dialog' name, then tests the keyboard path and spoken label. The reviewer also checks that the form's pickup-code label points to its input, not merely sits next to it visually.",
                "sample": "Control: dialog close icon\nVisible purpose: close booking dialog\nObserved DOM: span with click handler\nExpected: native button; exposed name; keyboard operation\nVerify: accessibility tree and live interaction",
                "cost": "Inspecting N controls is O(N) review work, while fixing a shared component may remove the same defect from many routes. A static scan is inexpensive but cannot prove the component's behavior after state changes. Group duplicate findings by component only after checking that each affected instance has the same cause and repair path.",
                "mistakes": ["Do not use a clickable span where a button is required.", "Do not assume adjacent text labels a field.", "Do not add a second conflicting name to a correctly named native control."],
                "related": ["prompt-engineering/semantic-structure-output-gate", "prompt-engineering/ui-visual-and-accessibility-release-gate"],
            },
            {
                "slug": "accessibility-prompt-keyboard-focus-dialog-path",
                "title": "Accessibility prompts: test keyboard and dialog focus paths",
                "section": applications,
                "summary": "Trace focus entry, movement, dismissal, and return through each interactive state.",
                "definition": "A keyboard review prompt should name the starting control, input sequence, expected focus target, and exit path. Test Tab, Shift+Tab, activation, Escape where the component promises dismissal, and visible focus indication. A modal task may need focus containment while open and a deliberate return target when closed. Do not ask a model to infer a focus sequence from DOM order alone when scripts change focus at runtime. Record the observed active element after every meaningful transition.",
                "case": "The Harbor reviewer opens the confirmation dialog from the 'Review booking' button, tabs through two actions, then presses Escape. The dialog closes, but focus jumps to the top of the page. The finding names the opener and final active element, so an engineer can reproduce it. A repair that only adds a visible outline would miss the lost-focus path; the reviewer repeats the full sequence after the code change.",
                "sample": "Start: Review booking button\nEnter: activate; focus moves into dialog\nMove: Tab across dialog actions\nExit: Escape\nObserved focus: page top; expected: Review booking button",
                "cost": "A linear focus walk across N interactive elements takes O(N) key presses; checking multiple state paths multiplies that cost by the number of paths. Capture a short trace at transition boundaries rather than every incidental keystroke. A shared dialog fix is still subject to regression checks on every distinct opener and close action.",
                "mistakes": ["Do not equate DOM order with observed runtime focus order.", "Do not leave focus inside a hidden dialog.", "Do not mark a dialog fixed after testing only pointer dismissal."],
                "related": ["prompt-engineering/ui-visual-and-accessibility-release-gate", "prompt-engineering/evaluation-slice-design"],
            },
            {
                "slug": "accessibility-prompt-form-error-and-status-path",
                "title": "Accessibility prompts: connect form errors and status changes",
                "section": production,
                "summary": "Make validation repair and asynchronous feedback perceivable in the tested flow.",
                "definition": "An error-review prompt should pair each failed field with its label, current value state, visible error, programmatic relationship, and focus or announcement behavior. Separate client-side validation from a server response, because each can fail differently. Status text that changes after submission also needs an observable notification path without stealing focus without reason. The model can draft a field-by-field checklist. It cannot establish that a message is heard until the actual interface is tested with its intended assistive technology.",
                "case": "Harbor rejects a blank pickup code. The red border is visible, but the input has no text error connected to it. A reviewer records the exact failed-submit state and asks for a repair that exposes a readable message and associates it with the field. After the change, they test keyboard focus, field description, and the server-delay status. The screenshot remains supporting evidence, not the sole pass criterion.",
                "sample": "Field: pickup code; state: blank on submit\nObserved: red border; no linked text error\nRepair target: visible instruction + programmatic association\nRetest: focus, field description, server status\nUnverified until tested: spoken output",
                "cost": "Reviewing F fields across E error states costs O(FE) checks in the worst case. A reusable form component can reduce implementation work, but it does not remove the need to test distinct server errors and field combinations. Keep test values synthetic and preserve the response code so a later reviewer can reproduce the same branch.",
                "mistakes": ["Do not rely on red color as the only error signal.", "Do not attach an error message to the wrong field.", "Do not treat a visible status as proof that it was announced."],
                "related": ["prompt-engineering/semantic-structure-output-gate", "prompt-engineering/ui-visual-and-accessibility-release-gate"],
            },
            {
                "slug": "accessibility-prompt-contrast-color-and-alt-purpose",
                "title": "Accessibility prompts: measure contrast and describe image purpose",
                "section": production,
                "summary": "Separate measurable color pairs from text alternatives that depend on context.",
                "definition": "A contrast prompt needs the actual foreground and background colors for each rendered state, including hover, disabled, and error states where they matter. A screenshot estimate is not a color measurement; overlays and gradients can change the effective pair. Text alternatives require the image's function in context. A linked logo may need the destination name, while a decorative mark should not repeat nearby text. Ask the model to list measurements and purpose judgments separately so neither masquerades as a complete accessibility audit.",
                "case": "Harbor's pickup warning uses muted orange text on a light card. The reviewer samples the computed foreground and the effective card background, checks the measured ratio against the team's applicable criterion, and records the values. The delivery-map icon beside 'Pickup zone' adds no information and should not force a repeated announcement. A different map image showing the actual pickup zone needs an alternative that communicates the location or an equivalent text description.",
                "sample": "Warning state: inspect computed foreground/background pair\nMeasure: actual rendered colors, not screenshot estimate\nDecorative icon: avoid repeated name\nInformational map: provide location meaning in text\nVerdict: only after criterion and context are checked",
                "cost": "Measuring C color pairs is O(C) checks; inspecting I images for purpose is O(I) human judgments. Gradient and overlay states may require several samples per component. A prompt can prepare the inventory, but a single measured pair and one alt-text pattern cannot cover every state or image role.",
                "mistakes": ["Do not estimate a pass from a screenshot.", "Do not give every image the same generic alternative.", "Do not ignore state-dependent colors."],
                "related": ["prompt-engineering/chart-prompt-accessibility-and-render-review", "prompt-engineering/ui-visual-and-accessibility-release-gate"],
            },
            {
                "slug": "accessibility-prompt-zoom-reflow-and-viewport-check",
                "title": "Accessibility prompts: inspect zoom and reflow states",
                "section": production,
                "summary": "Test content and controls at narrow widths and enlarged text without guessing from desktop layout.",
                "definition": "A reflow prompt should fix the viewport width, zoom or text enlargement, route, language, and interface state before reviewing the result. Ask for clipped content, horizontal scrolling where reading should remain vertical, overlapping controls, hidden error text, and lost functionality. A desktop screenshot cannot prove that a form works at a narrow width. The reviewer should also check long localized labels and the opened dialog, since a page that reflows at rest may fail after validation or expansion.",
                "case": "At a narrow viewport, Harbor's booking form displays the pickup-code error below the fold. That is acceptable if it remains reachable and linked; however, the opened confirmation dialog has a fixed width and its final action falls outside the visible area. The reviewer records viewport, zoom, dialog state, and the blocked action. The engineer repairs the layout, then retests with the same conditions and a longer translated button label.",
                "sample": "Route /booking | build B-47\nViewport: 320 CSS px | zoom: 200%\nState: confirmation dialog open\nObserved: final action clipped and unreachable\nRetest: same state plus long translated label",
                "cost": "For V viewport settings and S states, the direct test matrix is O(VS) render-and-interaction checks. Prioritize states that can hide a required action, then sample shared components across routes. Automated screenshots help compare layout changes, but a reviewer must still verify that clipped controls can be reached and operated.",
                "mistakes": ["Do not test only the idle desktop page.", "Do not call every horizontal scroll a failure without considering the content type.", "Do not close a reflow issue from a screenshot without trying the action."],
                "related": ["prompt-engineering/ui-visual-and-accessibility-release-gate", "prompt-engineering/multilingual-equivalence-check"],
            },
            {
                "slug": "accessibility-prompt-finding-severity-and-retest-gate",
                "title": "Accessibility prompts: write reproducible findings and retest fixes",
                "section": production,
                "summary": "Turn an observation into a bounded finding with impact, owner, and repeatable verification.",
                "definition": "An accessibility finding should contain the tested build and state, reproduction steps, observed result, expected user outcome, affected task, evidence, confidence, proposed owner, and retest result. Severity reflects the task impact and available workaround, not how dramatic a screenshot looks. Group repeated instances when they share a cause, yet keep enough instances to confirm the repair. A model may format a finding and suggest likely causes; it must not mark a fix verified merely because a code diff appears plausible.",
                "case": "The Harbor dialog focus jump blocks a keyboard user's return to the booking button after Escape. The report names the opener, the dialog state, the final active element, and the expected return. The team assigns the shared dialog component owner. Once repaired, the reviewer repeats the same keyboard sequence on the booking route and another route using that dialog. Only the observed retest changes the finding to resolved.",
                "sample": "Finding A-47 | build B-47 | booking confirmation\nSteps: open by keyboard; Escape to close\nObserved: focus at page top\nExpected: return to opener\nOwner: dialog component; status: open until retest",
                "cost": "Formatting K findings from a reviewed evidence ledger is O(K), while retesting each affected path adds real interaction time. Consolidation can reduce duplicate tickets but can also hide route-specific behavior, so keep an instance list. Short, precise reproduction steps usually save more engineer time than an exhaustive prose audit with no clear pass condition.",
                "mistakes": ["Do not assign severity from visual appearance alone.", "Do not claim a repair passed because the code changed.", "Do not omit the impacted user task or retest path."],
                "related": ["prompt-engineering/ui-visual-and-accessibility-release-gate", "prompt-engineering/report-claim-ledger-and-number-reconciliation"],
            },
        ],
        "backlinks": [
            ("prompt-engineering/ui-visual-and-accessibility-release-gate", 0),
            ("prompt-engineering/semantic-structure-output-gate", 1),
            ("prompt-engineering/evaluation-slice-design", 2),
            ("prompt-engineering/chart-prompt-accessibility-and-render-review", 4),
        ],
        "questions": [
            ("What must accompany a Harbor accessibility finding?", "The tested build, state, steps, and observed result", "Only a screenshot", "Only a suggested code change", "A finding needs enough context to reproduce the same state."),
            ("Can a screenshot establish a screen-reader announcement?", "No, spoken output needs a live check", "Yes, if the text is visible", "Yes, when the contrast looks high", "Pixels do not expose spoken behavior."),
            ("What should the dialog close icon be?", "A named, operable button", "A span with a click handler", "An image with no action", "Native controls provide expected keyboard behavior."),
            ("Which focus result fails after Escape?", "Focus moves to the page top", "Focus returns to the opener", "Focus remains visible on the opener", "The reviewer recorded a lost return target."),
            ("How should a blank pickup-code error be conveyed?", "Visible text associated with the field", "A red border alone", "A silent console message", "The person needs a readable repair instruction."),
            ("Does visible status text prove it was announced?", "No, verify with the intended interaction", "Yes, always", "Only if it is orange", "Visible and spoken feedback are different observations."),
            ("How should warning contrast be checked?", "Measure the effective rendered color pair", "Judge one screenshot by eye", "Use the design token name only", "The rendered foreground and background govern the measurement."),
            ("What should a decorative icon next to identical text do?", "Avoid repeating the nearby text", "Announce a generic image label", "Announce its file name", "The icon adds no new meaning in that context."),
            ("Which reflow state needs review?", "The opened dialog at a narrow viewport and zoom", "Only the idle desktop page", "Only the header image", "Interactive states can clip required controls."),
            ("When may a focus finding be marked resolved?", "After reproducing the repaired keyboard path", "When a developer says it is fixed", "When a diff looks plausible", "Observed retest closes the evidence loop."),
            ("What is an appropriate severity input?", "Impact on completing the user task and workaround", "Size of the screenshot", "Length of the finding title", "Severity follows task impact."),
            ("How does the prompt treat an untested concern?", "Label it as untested and request a check", "Report it as a confirmed failure", "Discard it silently", "Observation and hypothesis must remain separate."),
        ],
    },
    {
        "label": "Product analytics",
        "tag": "product analytics",
        "order": 32200,
        "project": "prompt-engineering/meridian-signup-funnel-review-project",
        "project_title": "Project: reconcile Meridian's signup funnel",
        "quiz": "quizzes/prompt-engineering-product-analytics",
        "quiz_title": "Product analytics prompt decisions",
        "intro": "A product-analytics prompt should preserve metric definitions, event lineage, eligibility, identity, and time windows. It can explain a validated table and suggest checks. It cannot turn raw event volume into a user count or infer causation from a descriptive funnel. Meridian Parcel is a fictional product used throughout these lessons.",
        "case": "Meridian records 5,170 raw signup-start events. After removing 470 duplicate deliveries by event ID, 4,700 eligible unique users remain for the chosen window. Of those users, 2,820 complete signup within the defined period, giving a 60% funnel rate. The mobile group has 2,350 starts and 1,175 completions, or 50%; desktop also has 2,350 starts but 1,645 completions, or 70%. The prompt must preserve these denominators and show a product hypothesis as a hypothesis, not a causal verdict.",
        "sample": "Raw start events: 5,170; duplicate event deliveries: 470\nEligible unique starts: 4,700\nMobile: 1,175 / 2,350 = 50%\nDesktop: 1,645 / 2,350 = 70%\nAll: 2,820 / 4,700 = 60%\nCause of gap: unknown without further evidence",
        "cost": "Deduplicating N events by stable event ID is O(N) expected time and O(N) memory; grouping U eligible users by platform is O(U) with a small number of counters. The expensive part is proving that the event contract and identity rules mean what the labels claim. Preserve a reproducible query and its input snapshot so the memo can be rerun after an instrumentation repair.",
        "mistakes": ["Do not use 5,170 raw event deliveries as the eligible-user denominator.", "Do not average the two platform percentages when segment sizes differ.", "Do not call a platform gap a proven design cause."],
        "specs": [
            {
                "slug": "analytics-prompt-metric-and-event-contract",
                "title": "Analytics prompts: define the metric and event contract",
                "section": applications,
                "summary": "Name the unit, eligibility, event trigger, completion rule, and time window before generating a chart.",
                "definition": "A product metric is a rule over observations, not a label on a dashboard. The prompt should specify the business question, analysis unit, inclusion and exclusion rules, event names, trigger points, identity key, completion window, and denominator. Ask the model to return unresolved definitions before analysis. Instrumentation can fire on page render, button press, or a confirmed server action; those are not interchangeable. Keep the contract version with the output so a later event rename or trigger change does not silently rewrite the historical series.",
                "case": "Meridian asks whether signup is easier on mobile. 'Signup start' originally fires on page load, including refreshes, while 'signup complete' fires after server confirmation. The analyst changes the question to eligible unique users who start and then complete within the chosen window. The event contract identifies the start trigger, completion trigger, platform at start, and stable user identity. The model can expose this mismatch before anyone plots a rate.",
                "sample": "Unit: eligible unique user\nStart: confirmed entry to signup flow\nComplete: server-confirmed account creation\nWindow: 24 hours after each start\nPlatform: value at first eligible start",
                "cost": "Validating E event definitions is O(E) contract review, while a full record scan is O(N) for N events. The extra definition work prevents a fast but meaningless chart. A model may propose a contract, yet engineering must verify that actual emitters follow it on every client and that server-confirmed outcomes are recorded exactly as intended.",
                "mistakes": ["Do not divide a server completion count by page-render events without an identity rule.", "Do not leave the completion window implicit.", "Do not rename an event without recording a version break."],
                "related": ["prompt-engineering/dataset-intake-column-contract", "prompt-engineering/aggregate-denominator-reconciliation"],
            },
            {
                "slug": "analytics-prompt-identity-dedup-and-late-events",
                "title": "Analytics prompts: reconcile identities, duplicates, and late arrivals",
                "section": applications,
                "summary": "Count people only after event deliveries and identity changes have been reconciled.",
                "definition": "An event stream may retry delivery, arrive out of order, and change identity when an anonymous visitor signs in. A prompt for analysis should name the deduplication key, identity-stitching policy, late-arrival cutoff, and treatment of missing keys. The model can flag suspicious count gaps, but deterministic processing must perform the merge and record what was excluded. A unique event ID removes retry duplicates; it does not by itself establish a unique person. Keep the raw count, deduplicated event count, and eligible-user count as separate ledger lines.",
                "case": "Meridian sees 5,170 raw signup-start deliveries. An event-ID pass removes 470 retry copies, leaving 4,700 start events in this synthetic dataset. The analyst then verifies that each represents one eligible user under the chosen identity policy; only then can 4,700 be called unique starts. A late completion arriving after the reporting cutoff is held for the next run or handled by a documented restatement rule, not quietly inserted into a published denominator.",
                "sample": "Raw deliveries 5,170\nRetry copies by stable event ID 470\nDeduplicated starts 4,700\nIdentity review: 4,700 eligible unique users in this packet\nLate arrivals: cutoff and restatement rule recorded",
                "cost": "Hash-based deduplication of N events is O(N) expected time and O(N) memory. Sorting by event time is O(N log N) when ordered session reconstruction is required. Identity stitching can be much harder if keys are missing or reused, so the report must state its confidence and exclusions rather than claiming exact user counts from an arbitrary event total.",
                "mistakes": ["Do not equate unique events with unique people without checking identity.", "Do not silently mix late events into a locked report.", "Do not discard every event with a missing key without recording the exclusion."],
                "related": ["prompt-engineering/input-normalization-contract", "prompt-engineering/aggregate-denominator-reconciliation"],
            },
            {
                "slug": "analytics-prompt-funnel-eligibility-and-order",
                "title": "Analytics prompts: enforce funnel eligibility and event order",
                "section": applications,
                "summary": "Count completions only for users who entered the defined step and met its window.",
                "definition": "A funnel rate requires a declared start population, ordered steps, completion deadline, and rules for repeated attempts. The numerator must be a subset of the denominator. Ask the model to inspect whether a table satisfies those invariants, then compute the rate outside free text. A completion event before the chosen start, or a completion from an excluded account, cannot be included merely because its name matches. Choose whether the unit is user, session, or attempt and keep it constant through every step.",
                "case": "For Meridian's 4,700 eligible unique starts, 2,820 users complete within 24 hours. The rate is 2,820/4,700, or 60%. A second signup attempt by the same person stays under the documented user-level rule rather than creating another person. A completion recorded after 24 hours is excluded from this rate but may appear in a separately named longer-window measure. The model's summary must carry the window and unit beside 60%.",
                "sample": "Denominator: 4,700 eligible unique starting users\nNumerator: 2,820 of those users complete within 24 hours\nRate: 2,820 / 4,700 = 60%\nInvariant: completion users are a subset of starting users\nRepeat attempt: handled by user-level rule",
                "cost": "A hash join of start and completion records by user ID is O(N) expected time and O(U) memory for N events and U users. An ordered multi-step funnel may need O(N log N) sorting. The prompt's word count is negligible compared with the cost of getting event order and eligibility wrong; test those invariants before generating a polished chart.",
                "mistakes": ["Do not count completions from users outside the start set.", "Do not switch from users to attempts mid-funnel.", "Do not omit the 24-hour completion window."],
                "related": ["prompt-engineering/aggregate-denominator-reconciliation", "prompt-engineering/deterministic-calculation-gates"],
            },
            {
                "slug": "analytics-prompt-cohort-window-and-time-zone",
                "title": "Analytics prompts: pin cohort windows and time zones",
                "section": production,
                "summary": "Keep membership, exposure, and observation periods stable across comparisons.",
                "definition": "A cohort is defined by a membership event and a time boundary. Prompting for a retention or conversion comparison must identify that event, the time zone used for bucketing, the observation horizon, data cutoff, and how incomplete cohorts are marked. A calendar-day label and a rolling 24-hour window answer different questions. Never compare a mature cohort with a recent cohort whose users have not had equal time to complete. The model can draft a cohort table schema, but the timestamp conversion and eligibility calculation belong in tested code.",
                "case": "Meridian's report closes at midnight in the reporting time zone. A signup started at 23:50 may complete shortly after midnight while still falling within its personal 24-hour window. If the analyst buckets starts by local day but cuts completions at the same midnight, the final cohort is incomplete. The release table marks that cohort provisional until all users have had the full 24 hours plus the documented late-arrival allowance.",
                "sample": "Membership: first eligible signup start\nBucket: reporting-zone calendar date\nOutcome: complete within personal 24-hour window\nCutoff: end of outcome window plus late-arrival allowance\nRecent cohort: provisional, not compared as mature",
                "cost": "Bucketing N events after timestamp normalization is O(N); joining each user's outcome is O(N) expected time with an indexed identity map. Waiting for a mature window delays publication but avoids a false decline. Store UTC instants and the reporting-zone rule so a daylight-saving transition or boundary event can be replayed consistently.",
                "mistakes": ["Do not compare an immature cohort with a fully observed cohort.", "Do not confuse local calendar days with rolling 24-hour windows.", "Do not erase the reporting time zone from the chart caption."],
                "related": ["prompt-engineering/locale-formatting-structured-values", "prompt-engineering/dataset-intake-column-contract"],
            },
            {
                "slug": "analytics-prompt-read-only-query-and-reconciliation",
                "title": "Analytics prompts: review read-only queries and totals",
                "section": production,
                "summary": "Constrain generated queries, test joins, and reconcile outputs before explanation.",
                "definition": "A query-writing prompt should state the schema, allowed read-only tables, row-level privacy constraints, metric contract, and expected checks. Treat generated SQL as a proposal. Review joins for accidental multiplication, verify unique keys, limit scanned dates, and compare grouped totals with a separately computed control. Do not execute an unrestricted query against production simply because the model supplied it. The final explanation should consume a locked result table, not improvise arithmetic or silently change filters between versions.",
                "case": "Meridian's platform query reports 2,350 eligible mobile starts and 2,350 desktop starts. Their sum matches 4,700. It reports 1,175 and 1,645 completions, summing to 2,820. A careless join against a device-history table could duplicate users who changed devices; the analyst first assigns platform at each user's first eligible start, then checks one row per user before grouping. The query remains read-only and uses a bounded reporting interval.",
                "sample": "Mobile starts 2,350 + desktop starts 2,350 = 4,700\nMobile completes 1,175 + desktop completes 1,645 = 2,820\nKey check: one row per eligible user before grouping\nQuery scope: read-only, bounded date interval\nRelease: totals reconciled to control",
                "cost": "A bounded scan is O(N) in relevant rows; hash aggregation is O(N) expected time and O(G) memory for G groups. A bad many-to-many join can inflate intermediate rows far beyond N, making both cost and conclusions wrong. Validate cardinality and scan scope before asking the model to interpret the output.",
                "mistakes": ["Do not run generated SQL without reviewing joins and permissions.", "Do not accept segment sums that fail to match the control total.", "Do not group raw retry deliveries as unique users."],
                "related": ["prompt-engineering/deterministic-calculation-gates", "prompt-engineering/report-claim-ledger-and-number-reconciliation"],
            },
            {
                "slug": "analytics-prompt-segment-gap-and-causal-restraint",
                "title": "Analytics prompts: explain segment gaps without inventing causes",
                "section": production,
                "summary": "Separate a measured difference from a mechanism or intervention claim.",
                "definition": "A segment comparison needs the same eligibility, identity, event definition, and observation window on both sides. Ask the model to report counts and rates, identify possible measurement or composition differences, and propose targeted checks. A descriptive gap is not proof of a design defect or of the effect of a planned fix. Seasonality, device mix, acquisition channels, missing events, and changed instrumentation are plausible alternatives. The memo should rank next tests by information value and leave the causal field unresolved until stronger evidence exists.",
                "case": "Meridian's mobile signup rate is 1,175/2,350, or 50%; desktop is 1,645/2,350, or 70%. The gap is 20 percentage points. The analyst can investigate mobile form errors, client event loss, traffic sources, and version exposure, but the numbers alone do not show which mechanism is responsible. A product proposal to shorten the mobile form is a testable hypothesis, not a result already supported by this table.",
                "sample": "Mobile: 1,175 / 2,350 = 50%\nDesktop: 1,645 / 2,350 = 70%\nDifference: 20 percentage points\nObserved: segment gap\nUnknown: cause and effect of a proposed form change",
                "cost": "Comparing two grouped rates is O(1) arithmetic after an O(N) data preparation pass. Investigating confounders costs additional slices, logging checks, and often a controlled study. Keep a compact hypothesis ledger so the model does not repeat a single attractive explanation as fact across successive reports.",
                "mistakes": ["Do not call the 20-point gap a proven mobile form defect.", "Do not hide the two 2,350-person denominators.", "Do not compare segments built with different identity rules."],
                "related": ["prompt-engineering/study-effect-measure-and-denominator-check", "prompt-engineering/report-claim-ledger-and-number-reconciliation"],
            },
            {
                "slug": "analytics-prompt-decision-memo-and-monitoring-gate",
                "title": "Analytics prompts: turn a metric packet into a bounded decision",
                "section": production,
                "summary": "Ship a decision memo with traceable figures, uncertainties, owner, and follow-up measure.",
                "definition": "An analytics memo should carry the metric contract version, source snapshot, denominator ledger, segment table, data-quality checks, uncertainty, decision owner, and proposed next observation. Prompt the model to draft claims only from locked figures and to name what cannot yet be inferred. A release gate should fail if a segment total does not reconcile, an immature cohort is presented as final, or a hypothesis becomes a causal claim. If a product change proceeds, define its success measure before exposure and monitor instrumentation health alongside outcome metrics.",
                "case": "Meridian's memo states that 2,820 of 4,700 eligible starting users completed within 24 hours. It reports 50% mobile and 70% desktop, with a 20-point gap. The decision is to inspect mobile errors and event delivery, then design a controlled test for a shorter form if the measurement holds. The memo does not say the new form will improve conversion. An owner records the query snapshot and schedules a recheck after the last cohort matures.",
                "sample": "Claim: 2,820 / 4,700 = 60% within 24 hours\nSegments: mobile 50%; desktop 70%; gap 20 points\nDecision: inspect errors and event delivery\nHypothesis: shorter form may help; unproven\nGate: totals, cohort maturity, and owner verified",
                "cost": "Reconciling C claims with an indexed result ledger is O(C) lookups plus review time; monitoring N new events is O(N) processing. A concise decision memo reduces repeated analytical work when it stores the contract and query version. Do not optimize for a persuasive narrative at the expense of reproducibility or a clear unknown state.",
                "mistakes": ["Do not publish a causal headline from an observational funnel.", "Do not omit a query or metric version from the handoff.", "Do not set a success target after viewing the intervention result."],
                "related": ["prompt-engineering/report-claim-ledger-and-number-reconciliation", "prompt-engineering/evaluation-slice-design"],
            },
        ],
        "backlinks": [
            ("prompt-engineering/dataset-intake-column-contract", 0),
            ("prompt-engineering/input-normalization-contract", 1),
            ("prompt-engineering/aggregate-denominator-reconciliation", 2),
            ("prompt-engineering/deterministic-calculation-gates", 4),
            ("prompt-engineering/study-effect-measure-and-denominator-check", 5),
            ("prompt-engineering/report-claim-ledger-and-number-reconciliation", 6),
        ],
        "questions": [
            ("What is Meridian's analysis unit?", "Eligible unique user", "Raw event delivery", "Device-history row", "The metric contract fixes the unit before calculation."),
            ("Which signup completion is counted?", "Server-confirmed completion within 24 hours of start", "Any page view", "A completion at any future date", "The outcome trigger and window are explicit."),
            ("What does event-ID deduplication remove?", "470 retry copies from 5,170 deliveries", "470 eligible people", "All late completions", "Delivery retries are not separate events."),
            ("What must be checked before calling 4,700 a user count?", "Identity and eligibility after event deduplication", "The chart color", "The prompt length", "Unique events alone do not prove unique people."),
            ("What is the all-platform completion rate?", "2,820 / 4,700 = 60%", "2,820 / 5,170 = 60%", "4,700 / 2,820 = 60%", "The numerator uses eligible starters as its denominator."),
            ("How are repeat attempts treated in this funnel?", "By the declared user-level rule", "As new people automatically", "They are never recorded", "The analysis unit must remain constant."),
            ("What makes the newest daily cohort provisional?", "Some users lack a full outcome window and late-arrival allowance", "It has a date label", "It includes mobile users", "Equal observation time is needed for comparison."),
            ("What is the mobile completion rate?", "1,175 / 2,350 = 50%", "1,175 / 4,700 = 50%", "2,350 / 1,175 = 50%", "The segment rate uses its own eligible starts."),
            ("What is the desktop completion rate?", "1,645 / 2,350 = 70%", "1,645 / 4,700 = 70%", "2,350 / 1,645 = 70%", "The desktop numerator and denominator use the same rule."),
            ("What is the observed platform gap?", "20 percentage points; cause unknown", "20% relative and proven design defect", "No gap", "The two rates differ, but the mechanism is not established."),
            ("What guards a segment query against inflated totals?", "Check one row per eligible user and reconcile group sums", "Use an unrestricted join", "Ask the model to estimate counts", "Cardinality and totals must be checked."),
            ("What may the decision memo recommend?", "Investigate error and event delivery, then test a form change", "Declare the shorter form proven", "Hide immature cohorts", "The packet supports an investigation and hypothesis."),
        ],
    },
]

new_paths = []
for cluster in clusters:
    paths = ["prompt-engineering/" + spec["slug"] for spec in cluster["specs"]]
    new_paths.extend(paths + [cluster["project"], cluster["quiz"]])
assert len(new_paths) == len(set(new_paths))
assert not set(new_paths) & lookup.keys()
titles = {entry["path"]: entry["title"] for entry in entries}
for cluster in clusters:
    titles.update({"prompt-engineering/" + spec["slug"]: spec["title"] for spec in cluster["specs"]})
    titles[cluster["project"]] = cluster["project_title"]
    titles[cluster["quiz"]] = cluster["quiz_title"]


def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(paths):
    return "<ul>" + "".join("<li>" + link(path) + "</li>" for path in dict.fromkeys(paths)) + "</ul>"


def related(paths):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(paths)]


def article(path, title, summary, body, section, order, connections, tag, kind="tutorial"):
    row = copy.deepcopy(lookup["prompt-engineering/evaluation-slice-design"])
    subjects = {applications: "prompt-engineering-applications", production: "prompt-engineering-production", projects: "prompt-engineering-project"}
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path, title=title,
               summary=summary, body=body, subject=subjects[section], difficulty="Advanced",
               tags=["prompt engineering", tag], sort_order=order,
               status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"].update(kind=kind, reading_minutes=11 if kind == "tutorial" else 18,
                       author_path="authors/aitrove-editorial", subject_root=subject_root,
                       section_path=section, content_format="html", seo_ready=True,
                       related=related(connections))
    return row


new_rows = []
for cluster in clusters:
    paths = ["prompt-engineering/" + spec["slug"] for spec in cluster["specs"]]
    for index, (path, spec) in enumerate(zip(paths, cluster["specs"])):
        connections = [spec["section"], subject_root] + spec["related"] + [other for other in paths if other != path] + [cluster["project"], cluster["quiz"]]
        body = ("<p>" + html.escape(spec["definition"]) + "</p>"
                + "<h2>Operational case</h2><p>" + html.escape(spec["case"]) + "</p>"
                + '<pre><code class="language-text">' + html.escape(spec["sample"], quote=False) + "</code></pre>"
                + "<h2>Performance and review cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
                + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in spec["mistakes"]) + "</ul>"
                + "<h2>Connected lessons</h2>" + links(connections))
        new_rows.append(article(path, spec["title"], spec["summary"], body, spec["section"], cluster["order"] + index * 10, connections, cluster["tag"]))

    project_connections = paths + [cluster["quiz"], "prompt-engineering/evaluation-slice-design", "prompt-engineering/report-claim-ledger-and-number-reconciliation"]
    project_body = ("<p>" + html.escape(cluster["intro"]) + "</p>"
                    + "<h2>Review the packet</h2><p>" + html.escape(cluster["case"]) + "</p>"
                    + '<pre><code class="language-text">' + html.escape(cluster["sample"], quote=False) + "</code></pre>"
                    + "<h2>Performance and review cost</h2><p>" + html.escape(cluster["cost"]) + "</p>"
                    + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in cluster["mistakes"]) + "</ul>"
                    + "<h2>Related lessons</h2>" + links(project_connections))
    new_rows.append(article(cluster["project"], cluster["project_title"], "Apply the full " + cluster["label"].lower() + " evidence contract to a fictional product packet.", project_body, projects, cluster["order"] + 80, project_connections, cluster["tag"], "project"))

    quiz = copy.deepcopy(lookup["quizzes/prompt-engineering-security-alert-triage"])
    quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + cluster["quiz"])), path=cluster["quiz"],
                title=cluster["quiz_title"], summary="Test evidence, calculations, boundaries, and release decisions in " + cluster["label"].lower() + ".",
                body="<p>Choose the decision supported by the recorded evidence.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([cluster["project"], applications, production, quizzes]),
                sort_order=cluster["order"] + 90, status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
    quiz["data"].update(subject_root=subject_root, section_path=quizzes, content_format="html",
                        author_path="authors/aitrove-editorial", seo_ready=True, duration_minutes=12,
                        related=related(paths + [cluster["project"]]),
                        questions=[{"prompt": prompt,
                                    "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                    "answer": (-index) % 3, "explanation": explanation}
                                   for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(cluster["questions"])])
    new_rows.append(quiz)

    for hub_path, selected, title, summary in [
        (applications, paths[:3], cluster["label"] + " inputs", "Define the evidence and analysis unit before producing findings."),
        (production, paths[3:], cluster["label"] + " review", "Verify state, arithmetic, and release boundaries."),
        (projects, [cluster["project"]], cluster["label"] + " project", "Apply the lesson sequence to a fictional packet."),
        (quizzes, [cluster["quiz"]], cluster["label"] + " decisions", "Test the boundaries of the packet."),
    ]:
        hub = lookup[hub_path]
        hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
        hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [cluster["project"], cluster["quiz"]])
        hub["updated_at"] = stamp
    lookup[subject_root]["body"] += "<h2>" + html.escape(cluster["label"] + " prompts") + "</h2><p>Follow the evidence from intake to a bounded decision.</p>" + links(paths + [cluster["project"], cluster["quiz"]])
    lookup[subject_root]["updated_at"] = stamp

    for old_path, new_index in cluster["backlinks"]:
        entry = lookup[old_path]
        entry["body"] += "<p><strong>Continue with:</strong> " + link(paths[new_index]) + ".</p>"
        entry["data"]["related"] = related([item["path"] for item in entry["data"].get("related", [])] + [paths[new_index]])
        entry["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newLessons": 14, "newProjects": 2, "newQuizzes": 2, "newPaths": [entry["path"] for entry in new_rows]}))
