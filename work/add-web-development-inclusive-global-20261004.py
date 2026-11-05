"""Extend the Web Development fixtures with original inclusive and global delivery lessons."""

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
    dict(path="web-tech/inclusive-interface-engineering", title="Inclusive Interface Engineering",
         summary="Design named controls, predictable focus, recoverable forms, and layouts that survive zoom and motion preferences.",
         overview="An inclusive interface preserves the task when pointer, viewport, vision, hearing, or motion assumptions change. Native elements supply useful behavior, but dialogs, validation cycles, and responsive layouts still need deliberate recovery paths. These lessons trace a case-review workflow through control names, interruption, error correction, and display constraints. An automated score alone cannot prove that the entire task works.",
         bridges=["web-tech/accessible-feedback-and-keyboard", "web-tech/form-server-validation", "web-tech/responsive-interaction-contract"]),
    dict(path="web-tech/internationalization-and-content-delivery", title="Internationalization and Content Delivery",
         summary="Keep messages, locale-sensitive values, mixed-direction text, and localized routes consistent.",
         overview="Internationalization moves language and presentation choices to explicit boundaries. A case system can store one timestamp and one reimbursement while showing both to readers in different locales. Its routes and help content may also exist in several languages. The lessons separate message identity, value formatting, text direction, and translation publication so a copy edit cannot change a business record or strand an old link.",
         bridges=["web-tech/locale-and-time-zone-boundaries", "web-tech/canonical-route-identity", "web-tech/server-rendered-static-and-client-rendered-pages"]),
]

topics = [
    dict(path="web-tech/accessible-names-and-native-controls", hub=hubs[0]["path"], title="Accessible Names and Native Controls",
         summary="Keep a control's visible purpose aligned with its programmatic name and native behavior.",
         definition="An accessible name is the short label by which a control is identified to assistive technology. Native links, buttons, and inputs already carry known roles and keyboard behavior. A styled generic container does not acquire that contract when a click handler is added. Repeated actions also need target context: forty identical 'Open' labels say little in a case queue. The name should describe the action and record, while the visible text and programmatic name should stay aligned as copy changes.",
         case="A queue holds 47 inspection cases. Each row has one icon to open details and one to remove a draft. Pointer users infer the target from proximity, but a keyboard or speech-input user encounters dozens of indistinguishable controls. Make detail navigation a real link with a destination. Make removal a button, and give the action enough case context to identify it. After removal, focus must move to another meaningful place instead of falling out of the list.",
         code='<li><a href="/cases/47">Open case 47: stairwell inspection</a><button type="button" aria-label="Remove draft case 47">Remove</button></li>',
         language="html", implementation="The link expresses navigation and still works without client JavaScript. The button expresses an action in the current view. Its extra label may drift from visible copy, so production code should derive both from the same record and translation key. A result message and focus destination belong to the same interaction; choosing the element alone does not make deletion understandable. If the row disappears, focus the next row action or a stable queue heading before announcing success.",
         cost="Native controls remove much custom keyboard code. Context-rich names still require stable record titles and editorial care: very long names slow listening, while generic ones hide the target. Automated checks catch missing names but do not judge whether the whole queue makes sense. Test the first, middle, and last item with a keyboard and screen reader. That takes more time than inspecting markup, yet it also finds incorrect destinations and focus loss for every user.",
         failure="The team ships a polished trash icon with no name. A keyboard user hears only 'button'; activating it removes a neighboring draft, then Tab jumps to browser chrome because the focused node was deleted. Two separate faults occurred. Fix the name and the post-action focus path. Re-run the task from a fresh page through deletion and into the next item, because a static scanner cannot prove recovery behavior.",
         drill="Try the queue with CSS disabled, then with client JavaScript disabled. Navigation should remain a meaningful link, while a removal action should fail honestly if it needs a server round trip. Inspect names and roles without using icon position as a clue. Repeat with long translated titles, because a name that works for short English text may become slow or clipped elsewhere.",
         decision="Choose the native element from the action's meaning before styling it. An action is not a fake URL, and navigation is not a click-only container.",
         checks=["Inspect names and roles for several repeated rows without relying on icon position.", "Complete open and remove tasks using only the keyboard, including focus after deletion.", "Disable client script and confirm navigation still reaches the intended case."],
         mistakes=["Using placeholder text as the only persistent label.", "Giving every repeated action the same name.", "Replacing a link or button with a clickable generic container."],
         related=["web-tech/accessible-feedback-and-keyboard", "web-tech/dom-events-progressive-enhancement", "web-tech/component-boundaries-and-state"]),
    dict(path="web-tech/dialog-focus-and-interruption-boundary", hub=hubs[0]["path"], title="Dialog Focus and Interruption Boundary",
         summary="Open a modal task with a clear name, contained focus, and a reliable return path.",
         definition="A modal dialog interrupts the current task and temporarily owns keyboard focus. Its lifecycle includes a trigger, an appropriate initial focus target, contained interaction, cancellation, and a sensible return destination. A native dialog opened with showModal supplies much of the containment behavior. The application still chooses focus, names the dialog, handles server outcomes, and plans for a trigger that might disappear after success. A visual overlay alone does not create a modal interaction.",
         case="Reviewer 29 selects 'Archive case 47'. A confirmation appears after a network delay. If focus stays on the row behind it, keyboard users can activate another action under the overlay, while screen-reader users may never hear the warning. Name the case and consequence in the dialog. Cancel must preserve it. If the server rejects the archive because another reviewer locked the case, the dialog must show a recoverable error rather than closing as though the archive succeeded.",
         code='const dialog = document.querySelector("#archive-dialog");\nconst trigger = document.querySelector("#archive-case-47");\ntrigger.addEventListener("click", () => { dialog.showModal(); dialog.querySelector("#cancel-archive").focus(); });\ndialog.addEventListener("close", () => { if (trigger.isConnected) trigger.focus(); });',
         language="javascript", implementation="The code starts focus on the safe cancellation action. Production markup still needs a visible heading connected to the dialog's name, explicit confirm and cancel controls, and a server error presentation. If the case row is removed after success, the old trigger cannot receive focus; choose the next case action or queue heading first. If the endpoint rejects the archive, keep the dialog open and direct attention to a message that explains the next step.",
         cost="A modal adds branches for cancel, confirm, Escape, server rejection, and removal of its trigger. Focus operations themselves are cheap, but the state machine costs maintenance as the page changes. Use an inline confirmation when interruption is unnecessary. For a consequential destructive choice, a modal may be warranted. Native dialog behavior avoids hand-written focus traps, although real browser and assistive-technology task tests remain necessary.",
         failure="A custom overlay is displayed with CSS while its background controls remain interactive. The next Tab reaches a hidden queue link; Enter opens case 62 behind the overlay. The reviewer thinks the archive confirmation was activated and cannot account for the route change. Use behavior that makes the rest of the document unavailable, then verify forward and reverse tabbing, Escape, confirmation, and a rejected request. A screenshot will not expose this defect.",
         drill="Run the dialog after changing the queue with a filter. The trigger may be replaced while the modal is open, so a simple saved DOM reference can become stale. Decide the focus destination from current state on close, not from an assumption that the old row survives. Test a slow response and a double-click as well; neither should create two archives or allow the dialog to vanish before its result is known.",
         decision="Use a modal only when the decision deserves an interruption. Native dialog behavior is a starting point, not a substitute for result and focus recovery.",
         checks=["Open from a keyboard trigger and verify heading, initial focus, containment, and Escape.", "Cancel and confirm; inspect focus after both, including when the row disappears.", "Force the archive endpoint to reject the action and verify an announced, actionable error."],
         mistakes=["Showing an overlay without disabling background interaction.", "Returning focus to a removed trigger.", "Closing on every response, including failed destructive actions."],
         related=["web-tech/accessible-feedback-and-keyboard", "web-tech/record-level-authorization", "web-tech/browser-journey-and-fault-tests"]),
    dict(path="web-tech/form-errors-and-recovery-paths", hub=hubs[0]["path"], title="Form Errors and Recovery Paths",
         summary="Keep rejected submissions understandable, located, and recoverable without discarding good input.",
         definition="A form error is part of the interaction contract, not merely a red border. The person needs to know which value failed, why it failed, and how to correct it, while valid input remains available. Browser constraints can help, but server validation remains authoritative for business and permission rules. A useful error links a message to its field, provides a summary when several fields fail, and directs focus to a recovery point. Temporary request failures must be distinguished from invalid input; retyping a field will not repair an unavailable service.",
         case="A case intake form accepts location, inspection date, severity, and notes. Reviewer 29 submits an impossible date and a location reserved by another team. The client catches the date; the server returns a conflict for location. If the page wipes the notes and says only 'Invalid submission', the reviewer must reconstruct work and cannot tell what to change. Retain values, attach separate messages, summarize failures, and permit resubmission after clear correction.",
         code='<label for="inspection-date">Inspection date</label><input id="inspection-date" name="inspectionDate" aria-invalid="true" aria-describedby="inspection-date-error" value="31 April"><p id="inspection-date-error">Enter a real calendar date.</p>',
         language="html", implementation="The visible label supplies a stable name, while the referenced message describes the correction. The error state belongs only to a field that currently failed. A full implementation preserves other values, builds a summary linking to invalid fields, and focuses that summary after a rejected submission when several errors need scanning. Server responses should carry stable error codes; English prose is display content, not a machine identifier. Treat conflicts and permission failures separately from syntax validation.",
         cost="Field errors require a mapping from server codes to controls and translated messages. That mapping adds maintenance whenever fields change, but prevents vague global errors from driving repeated attempts. Validation on every keystroke can create noise or network load; validate at meaningful points such as submit or completed field edits. Preserve entered values through a slow round trip and server-rendered return. Test recovery from a failed input, not only a pristine form.",
         failure="The server rejects an unassigned case ID, but the client maps every failure to the date field. A reviewer changes the date three times, receives the same error, and abandons the task. The interface has lied about the failure class. Keep transport, validation, conflict, and permission results distinct. Show a field message only when that field can be corrected. If access is missing, explain the boundary without exposing another team's private record.",
         drill="Test a rejected submission with a long note and an uploaded-file selection. The browser may not permit restoring a file input after navigation, so explain that limitation and keep other values. Test a translated error whose length wraps across lines, then use keyboard focus to reach the summary and each field. Finally simulate a retry that succeeds and confirm that stale errors disappear when the server accepts the corrected data.",
         decision="Represent error types at the API boundary. Correct a value, retry a temporary failure, and request access are different paths and need different copy.",
         checks=["Submit two invalid fields and verify summary, field descriptions, and retained notes.", "Simulate a timeout and verify the page does not blame a field value.", "Correct one field, resubmit, and confirm stale error state clears only after a new result."],
         mistakes=["Showing error color without text.", "Replacing all input with an empty form after rejection.", "Mapping permission and transport failures to arbitrary fields."],
         related=["web-tech/form-server-validation", "web-tech/api-evolution-and-compatibility", "web-tech/accessible-feedback-and-keyboard"]),
    dict(path="web-tech/reflow-zoom-and-motion-preferences", hub=hubs[0]["path"], title="Reflow, Zoom, and Motion Preferences",
         summary="Keep the task available when text grows, the viewport narrows, or motion is reduced.",
         definition="Responsive behavior is more than device breakpoints. A task must remain usable when a person zooms, enlarges text, changes orientation, or requests less motion. Reflow lets ordinary reading content rearrange without page-level horizontal scanning; some data views may need a bounded two-dimensional region. Focus indicators and errors must remain visible under sticky headers and animated panels. Reduced-motion preferences should remove nonessential movement while keeping state changes understandable.",
         case="The queue fits a wide laptop, but at 200 percent zoom its fixed filter bar pushes the archive control beyond the viewport. A slide-in result panel moves every time a filter changes. Reviewer 29 cannot reach the action without horizontal scrolling, and repeated motion makes filtering uncomfortable. Wrap the controls, bound horizontal overflow to any truly wide table, and switch the result panel to an immediate change when reduced motion is requested.",
         code='.case-filters { display: flex; flex-wrap: wrap; gap: 0.75rem; }\n.case-filters > * { min-width: min(100%, 14rem); }\n.case-result { transition: transform 180ms ease; }\n@media (prefers-reduced-motion: reduce) { .case-result { transition: none; } }',
         language="css", implementation="The controls follow available width instead of clipping the last action. The width rule prevents an individual control from exceeding a narrow container. The motion query removes decoration, not the changed result; text and focus order must still explain what happened. Include long labels and errors in layout tests. If a data table truly needs two axes, identify its scroll region and keep page navigation outside it.",
         cost="Wrapping controls makes the screen taller, so sticky elements and anchors need retesting. Long translated labels can grow cards and change scroll position; that is acceptable when reading order remains clear. Reducing transitions may save paint work, but an abrupt state change still needs a status cue. One emulator width misses combinations of zoom, text size, and expanded content. Include them in a small release matrix rather than trusting a single screenshot.",
         failure="The queue cards wrap at a narrow width, yet a fixed-width confirmation dialog remains wider than the zoomed viewport. Focus lands on a button physically offscreen. The page is labeled responsive because the initial queue passed. That measured the wrong unit: archiving includes the dialog and its failure state. Test the full journey with long translated copy, then adjust maximum width and internal overflow so the decision is visible.",
         drill="Check browser zoom separately from a narrow window: the effective CSS viewport and text metrics may differ. Inspect keyboard focus after a filter updates, after a dialog opens, and after an error appears. Test the reduced-motion setting while a progress indicator runs; keep useful progress information even if its animation stops. Recheck at least one landscape viewport, because a sticky header can consume most of the height.",
         decision="Test the task, not the initial screen. A layout passes when the person can reach the control, read the result, and recover under chosen display settings.",
         checks=["At 200 percent zoom, filter and archive without page-level horizontal scroll.", "Enable reduced motion and confirm state changes remain understandable.", "Increase text size and use long labels; inspect focus in filter, dialog, and error states."],
         mistakes=["Treating a mobile breakpoint as proof zoom works.", "Hiding overflow while a required control sits outside the viewport.", "Removing both motion and the only cue that a result changed."],
         related=["web-tech/responsive-interaction-contract", "web-tech/performance-budget-and-layout-stability", "web-tech/browser-journey-and-fault-tests"]),
    dict(path="web-tech/message-catalog-contracts-and-fallback", hub=hubs[1]["path"], title="Message Catalog Contracts and Fallback",
         summary="Treat translated strings as versioned interface data with stable keys and visible missing-message behavior.",
         definition="A message catalog maps a stable interface key to text in a selected language. The key names product meaning, not the English sentence, because copy can change without changing the action. Messages may contain named variables, plurals, or select cases, and translators need context about where each appears. Fallback is a product rule for a missing translation, not permission to show a raw internal key or silently mix languages. A release should know which messages are required and how noncritical omissions will be reported.",
         case="Reviewer 29 switches the interface to Hindi while examining case 47. The queue switches, but a new archive confirmation has no Hindi message. Concatenating an English verb with a translated suffix can break word order. Store the whole phrase as one translatable message with a named case-title value. A missing low-risk label might use an explicit fallback language and report the key to editors; a missing destructive confirmation can instead block the locale release. The choice must be visible in the delivery plan.",
         code='const messages = { en: { "case.archiveConfirm": "Archive {caseTitle}?" }, hi: { "case.archiveConfirm": "{caseTitle} को संग्रहित करें?" } };\nfunction archivePrompt(locale, caseTitle) {\n  const template = messages[locale]?.["case.archiveConfirm"] ?? messages.en["case.archiveConfirm"];\n  return template.replace("{caseTitle}", caseTitle);\n}',
         language="javascript", implementation="This small function keeps the sentence together and uses one named placeholder. It is not a full plural, gender, escaping, or rich-text engine; a larger site should use a maintained message-format facility. Render case titles as text, never as a string injected into HTML. Validate placeholders so a translation cannot drop required values. Cache catalogs by locale and content version, then invalidate them when translated copy changes, or a new component may load an old catalog.",
         cost="Catalogs add per-locale assets and editorial review. Splitting them by route can reduce the initial transfer, but a late fetch may flash the wrong language or leave a control unlabeled. Build-time key and placeholder checks make missing messages cheaper to repair. Runtime fallback helps continuity, yet mixed-language text may be unacceptable for a legal or destructive decision. Record missing keys without logging private case titles. Catalog storage is usually small beside the ongoing cost of translating without context.",
         failure="Code renames an archive key while the Hindi file keeps the old one. English tests pass, but the Hindi button visibly renders 'case.archiveSubmit'. A screenshot from the default locale misses the defect. Compare required keys and placeholders across shipped catalogs, then exercise the actual archive route in every supported locale. Runtime fallback remains a defense against a missed translation, not proof that the locale is ready.",
         drill="Create a test catalog that omits a low-risk tooltip, then another that omits the archive confirmation. The first should follow the documented fallback; the second should fail the release gate if the product treats it as mandatory. Replace a placeholder name in one locale and verify that validation catches it. Also test a case title containing angle brackets to confirm it is rendered as text rather than markup.",
         decision="Support a small set of languages completely for critical tasks. A language selector is not evidence that the account and recovery flows are translated.",
         checks=["Remove a noncritical key and verify fallback and missing-key reporting.", "Remove a required placeholder and verify catalog validation fails before release.", "Test long case titles in every supported locale and inspect meaning and layout."],
         mistakes=["Concatenating translated sentence fragments.", "Using English copy as a key that changes with punctuation.", "Exposing raw internal keys as user-facing fallback."],
         related=["web-tech/locale-and-time-zone-boundaries", "web-tech/component-boundaries-and-state", "web-tech/reflow-zoom-and-motion-preferences"]),
    dict(path="web-tech/currency-date-and-time-zone-presentation", hub=hubs[1]["path"], title="Currency, Date, and Time-Zone Presentation",
         summary="Keep canonical values separate from locale-sensitive display and explicit time-zone policy.",
         definition="Locale formatting changes a value's representation, not the value. Store an instant or a domain-specific local date according to the event, then choose locale and time zone at the display boundary. Store money as currency code plus exact minor units or a precise decimal representation; a formatted symbol is not a currency identifier. Browser locale utilities format presentation, but they do not decide which zone governs a deadline or convert one currency into another. Those are separate business rules.",
         case="An inspection closes at 18:30 in a regional office while reviewer 29 views it from another zone. Storing only '18:30' without zone or date makes a daylight-saving transition ambiguous. Keep the governing zone and a resolved instant for the deadline. The screen may show the reader's local time alongside the office zone. A reimbursement of 4,725 minor units in INR is a different record value; changing the interface language cannot turn it into a different amount or currency.",
         code='const closedAt = new Date("2026-10-04T13:00:00Z");\nconst localTime = new Intl.DateTimeFormat("en-IN", { dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Kolkata" }).format(closedAt);\nconst amount = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(47.25);',
         language="javascript", implementation="The snippet formats a known instant and display amount for one reader. It does not parse an ambiguous local time, settle a reimbursement, or convert currency. Keep arithmetic in exact units appropriate to the domain, and convert only for presentation. Reuse formatter instances when rendering many rows. When the reader changes locale, reformat the canonical value instead of parsing a string already displayed on the page. Exports and APIs should carry the original value and currency code.",
         cost="Constructing a formatter for each of hundreds of queue rows wastes CPU; reuse one per locale, zone, and format policy. Recording the governing zone adds a small field that prevents expensive deadline corrections. Currency conversion, if offered, needs a rate source and time; it must not be smuggled into formatting. Tests should cover daylight-saving transitions and more than one numbering system. Formatting cost is small next to a wrong deadline or payout.",
         failure="An exporter parses the display string '04/10/2026'. One reader means October 4 and another April 10, so the case lands in the wrong reporting period. The display was never a storage contract. Export the canonical date or instant with its explicit zone, then format for the recipient. A related mistake is treating a currency symbol as a unique code; several currencies share a symbol. Preserve the actual code in machine-facing data.",
         drill="Store one instant and render it in two viewer zones; the strings should differ while the underlying timestamp remains identical. Test an office deadline during a skipped or repeated local clock time, because choosing the wrong side of the transition can change the rule. Change language without changing the amount or currency code. Finally export the record and confirm it contains machine values rather than rendered display strings.",
         decision="Ask which clock governs the event before formatting it. A meeting, legal deadline, and creation timestamp can need different rules even if all look like dates on the page.",
         checks=["Render one instant in two zones and verify both map to the same stored value.", "Test a deadline at a daylight-saving transition, including repeated time.", "Change language while keeping currency code and exact stored amount fixed."],
         mistakes=["Parsing localized display text as source of truth.", "Treating formatting as currency conversion.", "Applying viewer zone to a deadline governed by another office."],
         related=["web-tech/locale-and-time-zone-boundaries", "web-tech/data-persistence", "web-tech/field-and-lab-performance-evidence"]),
    dict(path="web-tech/right-to-left-and-mixed-direction-content", hub=hubs[1]["path"], title="Right-to-Left and Mixed-Direction Content",
         summary="Declare page direction and isolate unknown text so identifiers and prose remain legible together.",
         definition="Text direction belongs to a writing system and content run, not to a visual flip of the whole page. An Arabic interface may set a right-to-left base direction while case identifiers, Latin names, and URLs remain left-to-right inside it. The browser handles much ordering, but unknown user text beside punctuation can still appear in the wrong sequence. Declare page language and direction, isolate unknown-direction strings, and use logical CSS properties so spacing follows writing direction without duplicating every component rule.",
         case="A localized queue shows an Arabic sentence followed by case ID C-47 and a Latin reviewer name. Without isolation, digits and punctuation may appear on unexpected sides, making the ID hard to verify or copy. The alert also uses a left border and left margin, which point the wrong way after the page direction changes. Set page language and direction, isolate the inserted strings, and use border-inline-start and padding-inline-start rather than mirroring pixels by hand.",
         code='<html lang="ar" dir="rtl"><p>المراجع: <bdi>Reviewer 29</bdi> — <bdi>C-47</bdi></p></html>\n<style>.case-alert { border-inline-start: 0.25rem solid; padding-inline-start: 1rem; }</style>',
         language="html", implementation="The fragment demonstrates document direction, language, and isolation; a production page still needs a full document structure. The bdi element lets a name or identifier choose its base direction without surrounding punctuation joining its run. For unknown-direction input, a suitable dir setting can help while typing. Keep machine identifiers as stored strings and verify copy-paste: visual ordering must not change underlying bytes or the search key.",
         cost="Logical CSS properties reduce duplicate left and right rules, but migration needs review of icons, charts, timelines, and controls whose direction carries meaning. Some navigation arrows reverse; a logo or playback symbol may follow a different rule. Language and direction can vary inside one record, so screenshots alone are weak. Include native-language review of mixed-script content and verify keyboard selection and copy-paste. The main cost is editorial and test coverage, not runtime computation.",
         failure="A global CSS transform flips the application for Arabic. Text appears mirrored, case digits look wrong, and a status icon points the opposite way though its meaning did not change. Developers patch components with more transforms, producing inconsistent behavior. Return to semantic direction and logical layout rules. Isolate mixed strings and decide icon direction by meaning. A screenshot can hide a broken copy-paste or screen-reader order, so test those interactions directly.",
         drill="Insert three names: Arabic only, Latin only, and a mixed-script name with punctuation. Render each beside a case ID and number. Tab through controls, select the ID, and paste it into search. The search should match the canonical record, even if visual ordering differs. Repeat with a narrow viewport and inspect whether logical spacing follows the page direction without moving unrelated status icons.",
         decision="Set direction at the document or content boundary and isolate exceptions. Avoid a global visual mirror that changes text and controls under different semantic rules.",
         checks=["Render Arabic text with Latin names and mixed-digit IDs; inspect punctuation and reading order.", "Copy a displayed ID into search and verify it matches the stored identifier.", "Audit logical spacing, icons, and focus order in both directions at narrow width."],
         mistakes=["Assuming interface language and text direction are one field.", "Mirroring the whole page with CSS transforms.", "Leaving unknown-direction names beside punctuation without isolation."],
         related=["web-tech/locale-and-time-zone-boundaries", "web-tech/responsive-interaction-contract", "web-tech/accessible-names-and-native-controls"]),
    dict(path="web-tech/localized-route-and-translation-release", hub=hubs[1]["path"], title="Localized Routes and Translation Release",
         summary="Publish language-specific pages without losing identity, old links, or editorial readiness.",
         definition="A localized route identifies one language representation while preserving the underlying content identity. Route selection, declared language, navigation, and translation status must agree. Locale prefixes are simple to parse, but the server needs a rule for missing translations, a default language, and old slug redirects. Automatically redirecting every visitor from a request header can prevent sharing a chosen language URL. When content changes, publish each translation only when its facts and task instructions match current product behavior.",
         case="An English photo-upload guide changes its maximum accepted file size, but its translation still states the old limit. A reader arrives through a saved localized URL and follows outdated instructions. The route returns successfully, so a crawl reports no error, yet the content contract is broken. Tie translated pages to source revision and readiness state. Keep an old translation with an update queue, fall back to current content, or hold the feature for that locale according to risk; do not hide the decision in routing code.",
         code='const pages = new Map([["upload-photos", { en: "/en/guides/upload-photos", hi: "/hi/guides/photos" }]]);\nfunction pageFor(contentId, locale) { const routes = pages.get(contentId); return routes ? (routes[locale] ?? routes.en) : null; }',
         language="javascript", implementation="The map separates content identity from localized slug. It demonstrates one fallback but does not dictate every product's redirect rule: the site may offer a language choice or return a deliberate missing-page result when translation is absent. Preserve old slugs in a redirect table. Generate internal links from content identity and locale, selecting a current translation when one exists. Declare the actual page language; changing only the URL prefix does not translate the body or make its instructions current.",
         cost="Each localized page adds review, route aliases, link variants, and cache entries. Pre-rendering every locale can lengthen builds and invalidate more pages after shared changes. Stable content IDs limit migrations when slugs are edited; revision metadata exposes stale translations before release. Language negotiation on every request complicates caching, while explicit locale URLs are easier to share and test. Storage for revisions and redirects is small compared with the cost of publishing wrong safety instructions.",
         failure="An editor renames a Hindi slug and removes the old path. Bookmarks and messages now lead to a missing page. Another internal link from a Hindi guide opens English content while retaining a Hindi language label. Readers lose context, and assistive technology may pronounce text incorrectly. Keep a redirect, generate links from stable identity plus chosen locale, and verify the HTML language declaration. Check translated upload instructions against the current limit before declaring the page ready.",
         drill="Change a localized slug in a staging dataset and follow an old saved link. It should reach the new route without a loop. Advance the source guide revision while leaving one translation behind; the release check should flag it. Open every locale route directly, follow a related lesson, and inspect both destination language and displayed body. Do not count a translated title attached to an English body as a successful locale route.",
         decision="Publish a translated route when its content is ready, not when a catalog happens to contain its title. Keep identity, editorial state, and fallback visible to maintainers.",
         checks=["Open locale routes directly and inspect declared language, heading, and related links.", "Rename a slug and verify old URL redirects without looping.", "Advance source revision and verify stale translations are flagged before publication."],
         mistakes=["Assuming a locale prefix means the body is translated.", "Deleting old slugs without redirects.", "Serving outdated instructions under a healthy status code."],
         related=["web-tech/canonical-route-identity", "web-tech/internal-link-architecture", "web-tech/sitemap-and-index-control"]),
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
                 tags=["web-tech", "web-development"], sort_order=1400 + sort_order,
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
    "web-tech/quality-and-release": [hubs[0]["path"]],
    "web-tech/frontend-application-architecture": [hubs[1]["path"]],
    "web-tech/accessible-feedback-and-keyboard": [topics[0]["path"], topics[1]["path"], topics[2]["path"]],
    "web-tech/responsive-interaction-contract": [topics[3]["path"], topics[6]["path"]],
    "web-tech/locale-and-time-zone-boundaries": [topics[4]["path"], topics[5]["path"], topics[6]["path"]],
    "web-tech/canonical-route-identity": [topics[7]["path"]],
    "web-tech/browser-journey-and-fault-tests": [topics[1]["path"], topics[3]["path"]],
}.items():
    entry = by_path[path]
    entry["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": len(hubs), "new_lessons": len(topics),
                  "web_development_routes": sum(entry["path"].startswith("web-tech/") for entry in entries)}))
