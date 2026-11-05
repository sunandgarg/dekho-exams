"""Add original component-contract and browser-compatibility curriculum entries."""
import copy
import datetime
import html
import json
import re
import subprocess
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
entries = json.loads(fixture.read_text())
by_path = {entry['path']: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()

def p(value):
    return '<p>' + html.escape(value) + '</p>'

def link(path):
    assert path in by_path, path
    return '<a href="/' + html.escape(path, quote=True) + '">' + html.escape(by_path[path]['title']) + '</a>'

hubs = [
    {
        'path': 'web-tech/web-component-contracts-and-interoperability',
        'title': 'Web Component Contracts and Interoperability',
        'summary': 'Ship custom elements whose lifecycle, projected content, forms, and styling remain usable across host applications.',
        'overview': 'A custom element is a browser-owned integration point, not just a reusable markup fragment. Its host can arrive before its definition, move between containers, receive new attributes, and participate in forms or assistive-technology navigation. This track follows a shared case-review control embedded in three host applications. It treats upgrade timing, event boundaries, form submission, and styling as contracts that an integrator can test without reaching into private component internals.',
        'bridges': ['web-tech/web-components-and-shadow-boundaries', 'web-tech/component-boundaries-and-state'],
    },
    {
        'path': 'web-tech/progressive-browser-compatibility',
        'title': 'Progressive Browser Compatibility',
        'summary': 'Keep a useful task path while adding newer browser capabilities under a measured support policy.',
        'overview': 'Browser support is an application decision tied to actual users, embedded web views, assistive technology, and release economics. A compatibility badge cannot prove that a workflow works on a low-end phone or with keyboard input. This track begins with a plain case-review submission, then adds optional interaction and export capabilities. It covers feature probes, selective polyfills, a device test matrix, and retirement of older paths after measured adoption.',
        'bridges': ['web-tech/integration-and-verification', 'web-tech/browser-capabilities-and-permission-lifecycle'],
    },
]

topics = [
    {
        'hub': 0, 'slug': 'custom-element-upgrade-and-reconnection', 'title': 'Custom Element Upgrade and Reconnection',
        'summary': 'Handle pre-definition markup, observed attributes, repeated connection, and host-driven moves without duplicate side effects.',
        'concept': 'Custom element upgrade is the moment a matching element acquires the registered class and its lifecycle behavior. Markup can exist before the definition script arrives; a server-rendered case status must therefore remain legible while the element is still unknown to the browser. Registration happens once per name and registry. An observed attribute may be delivered as part of upgrade, before the first useful connection. Connection can happen repeatedly as a framework moves or replaces nodes. Constructors establish internal state; document-dependent work belongs after connection.',
        'case': 'A permit dashboard renders case 47 as a status label inside a case-status-card tag. The page can submit the review even if the component bundle fails. Later, the definition arrives and attaches its controls. The host changes the status attribute from pending to returned, then moves the card into a filtered list. A careless connected callback adds another listener and another polling timer. After three moves, one click sends three requests. The contract must keep the visible label correct before upgrade and perform only one active subscription while connected.',
        'implementation': 'Treat attributes as input and internal rendering as a projection, not as the only source of truth. Make connection idempotent: create listeners and observers only when absent, and release them on disconnection. If a framework removes a node and creates another, do not transfer hidden mutable state without an explicit key. Avoid assuming that a move is always a permanent removal; the host may reconnect immediately. Do not fetch privileged data in the constructor because attributes, parent context, and ownership can still change. An event emitted after disconnection should be ignored by the host if the case selection has changed.',
        'cost': 'Registration cost is small per element name, but each live instance may retain event handlers, an observer, cached records, and a timer. A list of n case cards can turn one polling interval into n network loops. Replace polling with one host-owned data source when many cards share the same case feed. Attribute updates should be O(1) for a bounded status field; replacing an entire shadow tree per change can discard focus and expand work with subtree size. Measure upgrade delay and listener counts in a long-lived dashboard.',
        'failure': 'Render the page with the component script blocked. The status and server submission must remain usable. Then register the element after markup exists and confirm that its initial attribute is processed. Connect, disconnect, and reconnect the same node four times while counting network requests and event listeners. Change the case ID during a delayed response; the old result must not paint the new case. Simulate duplicate registration from two bundles and require the loader to avoid defining the same name twice. Move the card during a keyboard action and confirm focus is still understandable.',
        'drill': 'Build a component for statuses pending, returned, and cleared. Leave its initial label in light DOM. Upgrade after a delayed script load, change the status twice, move it between lists, and remove it. Instrument active subscriptions and prove the count returns to zero. Repeat with a host that replaces rather than moves the node. The host contract should state which attributes are stable, which events are emitted, and what happens before definition.',
        'decision': 'A reusable element needs a readable pre-upgrade state and a lifecycle that tolerates repeated connection.',
        'code': "function shouldAttachCaseFeed(state) {\n  return state.connected && !state.feedAttached && state.caseId !== null;\n}\nconsole.log(shouldAttachCaseFeed({ connected: true, feedAttached: true, caseId: 47 }));\n// Output: false",
        'checks': ['Pre-upgrade markup has a usable label.', 'A reconnect leaves exactly one active feed.', 'An old case response cannot update a new case.'],
        'mistakes': ['Registering the same custom element name twice.', 'Starting timers every time connectedCallback runs.', 'Replacing focused content on every attribute update.'],
        'related': ['web-tech/hydration-and-deterministic-first-render', 'web-tech/cooperative-main-thread-scheduling'],
    },
    {
        'hub': 0, 'slug': 'shadow-slots-events-and-focus-contract', 'title': 'Shadow Slots, Events, and Focus Contracts',
        'summary': 'Define projected content ownership, event crossing, and focus behavior at a shadow boundary.',
        'concept': 'A shadow root scopes internal markup and styling, but the host still owns light-DOM children assigned to slots. An event from an internal control can cross the shadow boundary only when its propagation and composed settings permit it. Outside listeners may see a retargeted host rather than the internal node. Slot assignment can change without the host being rebuilt. These are API decisions. A consumer should not need to query internal nodes to discover selected case state or operate the control.',
        'case': 'A shared case-review panel accepts a heading, an action label, and a help link from the page. One host replaces the help link after a permission change; another reorders panels while the reviewer is using a keyboard. The component must not clone the supplied link and then forget updates. It emits a case-select event carrying a stable case ID, but no private note text. An analytics listener outside the shadow root receives the event; a local keydown inside does not become an application command unless the component deliberately emits one.',
        'implementation': 'Document named slots and fallback content. Observe slot changes only for work that depends on assigned nodes, and avoid rewriting the host-owned nodes. Emit a task event with bubbles and composed set when outside application code needs it; include a small immutable detail object and let the host perform authorization. Internal implementation events stay internal. Restore focus to a meaningful control after closing an internal overlay. Test the composed path rather than relying on an internal selector from host code. An open root aids integration tests, but it is not a security boundary; a closed root is not a data-protection mechanism either.',
        'cost': 'Slot assignment and a small custom event are cheap. Work performed on every slotchange may not be: scanning all descendants across n mounted panels can become O(total projected nodes) per update. Cache only stable derived information and invalidate it when slot content changes. Retaining old assigned nodes in a component field can keep detached private content in memory. Focus restoration requires a stable owner reference, which should be cleared when the host removes the panel. Monitor event volume when pointer movement or progress updates cross the boundary.',
        'failure': 'Replace a slotted help link while the panel remains mounted. Its current destination must appear without rebuilding the panel. Fire a composed case-select event and prove the host receives the correct case ID, while a deliberately internal event does not escape. Move focus into an overlay, remove the panel, and ensure no detached node receives focus afterward. Try keyboard, touch, and a screen reader; visual slot placement alone cannot prove reading order. Change the selected account and reject an old case-select event from an inactive panel.',
        'drill': 'Create a panel with title and actions slots. Supply a server-rendered title and a normal link as fallback content. Replace the action slot during a permission change, then emit a versioned selection event. Record the event detail seen by the host and keep private note text out of it. With JavaScript disabled, the title and link should still be useful; with JavaScript enabled, focus and event behavior should remain predictable after the panel moves.',
        'decision': 'Slots share presentation space, while events and focus define the actual integration boundary.',
        'code': "function caseSelectEvent(caseId) {\n  return new CustomEvent('case-select', { bubbles: true, composed: true, detail: { caseId } });\n}\nconst selection = caseSelectEvent(47);\nconsole.log(selection.bubbles && selection.composed && selection.detail.caseId === 47);\n// Output: true",
        'checks': ['Host-owned slot nodes can change without a rebuild.', 'Only intentional events cross the shadow boundary.', 'Focus never returns to a removed panel.'],
        'mistakes': ['Reading an internal button by selector from the host.', 'Sending private record text in event detail.', 'Treating a closed shadow root as access control.'],
        'related': ['web-tech/complex-accessible-interactions', 'web-tech/postmessage-origin-source-schema-and-replay'],
    },
    {
        'hub': 0, 'slug': 'form-associated-custom-control-and-native-fallback', 'title': 'Form-Associated Custom Controls and Native Fallback',
        'summary': 'Make a shared decision control submit, validate, reset, and recover with a plain-form path.',
        'concept': 'A visual custom element does not automatically behave like a native form control. A form-associated custom element can use ElementInternals to contribute a value and validity state to its owning form. The submitted value, user-visible state, disabled state, reset behavior, and restoration behavior are separate contracts. For a task that can be expressed with a native select or radio group, the native control is often the better baseline. A component layer should improve interaction without making a permit decision depend on script execution.',
        'case': 'Reviewers choose approve, return, or defer on case 62. One application submits a standard HTML form; another wraps the choice in a custom element to show policy help. The first implementation writes only a styled label and never calls setFormValue. Reviewers see approve, but the server receives no decision. Another version sends display text instead of the stable decision code. A restart restores the label but not the value. A plain server-rendered select can carry the same name and options when the advanced control is unavailable.',
        'implementation': 'Start with a normal named input and server validation. If the custom form control is warranted, set formAssociated on the autonomous element, attach internals, and call setFormValue whenever the normalized decision changes. Set validity and a focus target for errors. Handle form reset and disabled state explicitly, then test browser restoration behavior. Do not create duplicate successful controls with the same name when a fallback select remains in the form; hide or disable one submission path intentionally. The server still validates that the selected code is allowed for the current reviewer and case.',
        'cost': 'Normalizing a three-value decision is O(1), while a custom control adds lifecycle code, accessibility testing, and browser integration work. Each validation change can trigger layout and announcement work if it replaces error nodes. Keep error text stable and update only when state changes. A custom element may add bundle bytes to every review screen, so lazy loading must preserve a usable plain form during delay or failure. Measure failed submissions and keyboard completion, not just whether the enhanced widget paints.',
        'failure': 'Submit the page before the component definition loads and verify the server receives a valid decision through the native path. Activate the enhanced control and submit each option; inspect the actual FormData value, not the visible label. Reset the form and confirm the value, selected appearance, and validity all agree. Disable the field and verify it no longer submits. Corrupt a decision code in the request and require server rejection. Reopen a partially completed form after navigation and verify restored state or an explicit prompt to choose again.',
        'drill': 'Build a case-decision field with approve, return, and defer. Define stable codes separate from the labels shown to reviewers. Provide a server-rendered select first. If the component takes over, check that exactly one named successful control contributes to submission. Try a missing value, reset, disabled fieldset, browser back navigation, and a keyboard-only run. Record whether every route sends the same stable code to the server.',
        'decision': 'Form participation is an end-to-end value contract; appearance cannot stand in for submitted state.',
        'code': "function normalizeCaseDecision(value) {\n  const allowed = new Set(['approve', 'return', 'defer']);\n  return allowed.has(value) ? value : null;\n}\nconsole.log(normalizeCaseDecision('approved'));\n// Output: null",
        'checks': ['FormData contains one stable decision code.', 'Reset, disabled, and error states agree with the UI.', 'The server rejects unauthorized decisions.'],
        'mistakes': ['Assuming a shadow input submits through the outer form.', 'Submitting both fallback and enhanced controls.', 'Treating client validity as server authorization.'],
        'related': ['web-tech/forms-and-data-entry-workflows', 'web-tech/form-server-validation'],
    },
    {
        'hub': 0, 'slug': 'shadow-style-tokens-parts-and-shared-sheets', 'title': 'Shadow Style Tokens, Parts, and Shared Sheets',
        'summary': 'Expose deliberate theme hooks while keeping internal selectors and stylesheet ownership stable.',
        'concept': 'Shadow styling isolates internal selectors, but component appearance still needs an intentional contract with host pages. Inherited CSS custom properties can carry design tokens; named parts can expose selected internal surfaces for external styling. A constructed stylesheet may be shared among shadow roots in the same document, so changing that sheet affects every adopter. That is useful for global theme updates and dangerous for one-instance overrides. Styling hooks should name user-facing roles rather than private DOM structure.',
        'case': 'A permit platform embeds the same decision card in a bright field interface and a dark operations console. The host supplies spacing and contrast tokens, while the card exposes a summary part for a small set of host adjustments. The first implementation copies a full stylesheet into every card, creating repeated parse and memory work. A second implementation mutates one shared stylesheet to change only case 47; all 83 cards change color. The public theme contract needs per-host values for local changes and a shared sheet only for genuinely global rules.',
        'implementation': 'Define defaults inside the component so it remains legible in an unknown host. Read inherited custom properties with safe fallback values, and document any named parts as stable API. Use one constructed sheet for static rules when target browsers support it; create that sheet in the same document as its adopting roots. Avoid interpolating user content into CSS rules or custom properties without a constrained mapping. Treat contrast, forced colors, zoom, and reduced motion as behavior checks, not as palette screenshots. If constructed sheets are unavailable, a small style element or native fallback can preserve the essential interface.',
        'cost': 'A shared static stylesheet can avoid parsing the same rules for every instance, while per-host custom property changes usually limit the effect to one subtree. Replacing rules on a shared sheet can trigger style recalculation for every adopting root. With n mounted cards, a global theme change may touch O(n) components and cause layout or paint work. Large token sets also increase the compatibility surface between teams. Measure style recalculation, component mount time, and the result on a low-end device before adopting a styling API across a library.',
        'failure': 'Mount 83 cards, override a token on one host, and confirm the other cards keep their values. Change the shared sheet once and confirm the global rule updates all intended instances. Attempt to adopt a sheet created in a different document and require the component to fall back without hiding the decision. Turn on forced colors and high zoom; the selected state must remain visible without relying on color alone. Remove a host token and verify the component default. Rename a part in a test release and catch the host integration break.',
        'drill': 'Build a decision-card theme contract with two inherited tokens and one named part. Give the operations console a local surface color while field cards keep their defaults. Simulate an unsupported constructed-sheet path and render the same content with a style element. Run a keyboard and contrast review, then compare mount cost for one card and a list of 83. Document which hooks are stable and which selectors remain private.',
        'decision': 'Expose a small styling API that expresses intent, and keep shared stylesheet mutation reserved for global changes.',
        'code': "function chooseCardTheme(hostTokens) {\n  return { surface: hostTokens.surface ?? '#f4f2eb', accent: hostTokens.accent ?? '#365a7a' };\n}\nconsole.log(chooseCardTheme({ surface: '#242833' }).accent);\n// Output: #365a7a",
        'checks': ['A local token changes only its own card.', 'A missing token retains a readable default.', 'Forced colors and zoom keep selection discernible.'],
        'mistakes': ['Changing a shared sheet for one instance.', 'Publishing internal selectors as an accidental API.', 'Treating shadow styles as a complete accessibility solution.'],
        'related': ['web-tech/cascade-layers-and-design-token-ownership', 'web-tech/reduced-motion-and-rendering-budget'],
    },
]
topics.extend([
    {
        'hub': 1, 'slug': 'feature-probes-and-functional-fallbacks', 'title': 'Feature Probes and Functional Fallbacks',
        'summary': 'Gate enhancements on actual capabilities while preserving a server-owned completion path.',
        'concept': 'Feature detection asks whether a specific operation is available in the current environment. It is more useful than guessing support from a browser name, yet presence alone does not guarantee permission, correct behavior, or a usable result. A progressive task starts with a functioning path that does not need the optional capability. The enhancement may improve speed or comfort, but the user must still be able to finish the case if the capability is absent, blocked, or fails halfway through.',
        'case': 'An inspector exports case 47 after reviewing it. A plain server endpoint returns a download. On devices with a suitable file picker, the app offers Save to folder. One build checks that the picker function exists and then replaces the download button. The picker is present but the user cancels it, the permission is denied, or a managed web view blocks it. The export disappears. The right boundary keeps the server download as the ordinary path and treats direct file saving as an optional branch with an explicit return path.',
        'implementation': 'Probe the exact API at the point of use and handle exceptions from invocation separately. Keep the server export authorization, content type, and filename policy independent of the browser branch. A probe for one method cannot establish support for the entire workflow: writing, closing, and error recovery may fail later. When the capability needs user activation, invoke it in the direct interaction path rather than after an unrelated asynchronous delay. Make cancellation a distinct user choice and do not label it as an application error. If an enhancement is security-sensitive, keep its fallback aligned with the same server permission checks.',
        'cost': 'A capability probe is O(1); the expensive work is implementing and maintaining two task paths. A server export consumes network bytes and may duplicate a client-side save, but it preserves completion across browsers. A failed picker can leave a partial file, so write to a temporary destination where the API permits and communicate completion only after close succeeds. Track attempted and completed exports by path without logging private filenames. A fallback that is never exercised in release tests will rot even if its code remains present.',
        'failure': 'Run with the file picker missing, then present but throwing, then present but canceled. In each state, the authorized server download must remain available. Simulate a failed stream close after several chunks; the UI must not show a successful export. Change the account during export and reject the old response. Disable JavaScript and verify the normal link still starts the server path. On a touch device, make sure the optional picker is invoked from a direct gesture. Check keyboard focus after each cancellation and error.',
        'drill': 'Implement a case export button with a normal server link and a separate Save to folder action only when a probe succeeds. Use a 47-record export with a generated revision ID. Test capability absence, user cancellation, storage denial, network interruption, and a completed file. Record which path actually finished, not which path was merely offered. Keep the server endpoint as the authority for record scope on both paths.',
        'decision': 'A capability probe selects an enhancement; it does not replace the baseline task or prove later operations will succeed.',
        'code': "function exportActions(capabilities) {\n  return capabilities.filePicker ? ['server-download', 'save-to-folder'] : ['server-download'];\n}\nconsole.log(exportActions({ filePicker: false }).join(','));\n// Output: server-download",
        'checks': ['The baseline export works without script.', 'Picker cancellation leaves a completion path.', 'A partial write never produces a success state.'],
        'mistakes': ['Replacing the baseline link when an API exists.', 'Treating a user cancellation as successful export.', 'Using a browser-name string as a permission check.'],
        'related': ['web-tech/file-ingestion-and-private-asset-lifecycle', 'web-tech/browser-capabilities-and-permission-lifecycle'],
    },
    {
        'hub': 1, 'slug': 'polyfill-cost-and-target-browser-policy', 'title': 'Polyfill Cost and Target Browser Policy',
        'summary': 'Choose supported environments, optional code, and fallback behavior without shipping unused weight to everyone.',
        'concept': 'A polyfill supplies a missing API or behavior with additional code. It cannot make an unsupported language syntax parse in an old engine after that engine has already rejected the bundle. Compatibility work therefore spans syntax transformation, API availability, CSS behavior, and task testing. A support policy names browser families, versions, embedded web views, and minimum device constraints from actual product usage. A broad compatibility label is only an input to that policy, not proof that the complete application works.',
        'case': 'The permit dashboard introduces a new date-formatting feature. One team bundles a large compatibility package into the first screen for every reviewer, even though only the report export path uses the feature. The initial download grows for thousands of users. Another team removes the package entirely because the API appears in current desktop browsers, but a municipal embedded web view cannot render report dates. Both errors come from treating compatibility as a yes-or-no property of a browser rather than a measured task contract.',
        'implementation': 'List the specific missing feature and the affected workflow. Keep parse compatibility in the build target before a runtime check can execute. Load an API polyfill only where needed, after a cheap feature probe, and verify that it preserves expected behavior rather than merely defining a property. If the missing behavior is small and optional, use a simpler native fallback instead of a full package. Pin and review the dependency as production code. Test bundled and unbundled paths in each supported engine, including the oldest web view still in policy. Document a date to revisit the fallback, but do not remove it on a guess.',
        'cost': 'A lazy polyfill moves bytes off the initial path, but introduces a later request, parse work, and failure mode. If n users load the app and only a fraction f opens export, initial bytes saved are roughly n times the deferred package size minus export-path fetches; cache behavior changes the real cost. Compatibility branches also increase test combinations. Measure first interaction, export completion, parse time, and support volume. Avoid shipping a polyfill whose dependency cost exceeds the value of the enhanced behavior for the supported audience.',
        'failure': 'Load the initial dashboard on a supported low-end phone and inspect whether export-only code is absent. Open export and verify the optional package arrives only when needed. Block that package request; the report should use a simpler date representation or an explicit fallback, not a blank screen. Run the build in an engine that cannot parse a newer operator and confirm the configured transform or alternate bundle prevents a startup syntax error. Verify an old embedded web view against the actual report workflow, not only a feature list.',
        'drill': 'Define a support matrix for desktop, mobile, and embedded reviewers. Choose one report feature with a missing browser API. Record the before and after initial bundle bytes, optional request bytes, and export completion on three environments. Simulate the polyfill request failing. Keep a short decision record that names the owner, the supported versions, the fallback, and the evidence required before removal.',
        'decision': 'Compatibility is a task-level budget and support contract, not a package that should load on every page.',
        'code': "function shouldLoadReportPolyfill(environment) {\n  return environment.reportOpened && !environment.hasDateFormatRange;\n}\nconsole.log(shouldLoadReportPolyfill({ reportOpened: false, hasDateFormatRange: false }));\n// Output: false",
        'checks': ['The build parses in every supported engine.', 'Optional code stays off the initial path.', 'A failed polyfill request leaves a usable report.'],
        'mistakes': ['Expecting a runtime polyfill to fix syntax parsing.', 'Loading export-only code for every visitor.', 'Assuming a support badge includes embedded web views.'],
        'related': ['web-tech/frontend-build-and-artifact-integrity', 'web-tech/performance-budget-and-layout-stability'],
    },
    {
        'hub': 1, 'slug': 'cross-browser-input-and-device-contracts', 'title': 'Cross-Browser Input and Device Contracts',
        'summary': 'Test task completion through keyboard, touch, composition, assistive technology, and low-end hardware.',
        'concept': 'A browser test matrix is a set of user tasks across engines, input modes, and devices, not a collection of screenshots. Rendering can look identical while focus, composition, pointer capture, scrolling, download, or permission timing behaves differently. Automated checks can cover stable contracts; actual devices and assistive technology still matter for paths tied to hardware and operating-system behavior. The matrix should reflect the product audience and risk, then shrink or grow as evidence changes.',
        'case': 'A reviewer updates case 62 on a laptop and an older phone. Desktop pointer tests pass. On the phone, an on-screen keyboard covers the final Save control; in a keyboard-only run, focus jumps to a removed element after a filter changes; during East Asian text composition, an input handler submits an incomplete note. A screenshot suite misses all three. The release team needs a task path: open the case, enter a note, choose a decision, save, and confirm the server revision in the supported environments.',
        'implementation': 'Define observable outcomes for each task: a valid server revision, a visible error on failure, and preserved user input when the save cannot complete. Cover representative browser engines, mobile and desktop, keyboard and pointer or touch, and any required screen-reader combinations. Add a composition-state test for text entry and a visual-viewport test when the keyboard appears. Use automation for deterministic focus order, network faults, and form state, while reserving real-device sessions for permission prompts, platform controls, and assistive-technology behavior. Record exact browser and OS versions with failures. Do not convert one passing emulator run into a device claim.',
        'cost': 'A full Cartesian product of engines, devices, input methods, and network states is too large. Choose a risk-weighted set: every critical save path on each supported engine, then targeted combinations for known platform boundaries. If there are e engines and t critical tasks, a base pass is O(e times t); add focused tests for hardware-specific behavior rather than every possible pair. Keep test fixtures small enough to run per release, and inspect flaky tests as evidence of timing or state ownership problems instead of hiding them with retries.',
        'failure': 'Enter a multilingual note while composition is active and press a shortcut; the app must not submit partial text. Resize the visual viewport with an on-screen keyboard and keep Save reachable. Change a filter while the focused card disappears and move focus to a predictable destination. Simulate a delayed save response after the user switches cases, then reject the stale update. Run the same task through a screen reader and record the announced status. Repeat on the lowest supported device, observing input delay and memory pressure.',
        'drill': 'Write a matrix for the case-save journey with three browser engines, one embedded web view, two input modes, and one low-end phone. Pick a small release gate instead of every combination. For each row, capture task result, browser version, input method, server revision, and any focus or announcement failure. Turn one observed problem into a regression check and retain a manual device check where automation cannot reproduce it reliably.',
        'decision': 'The release gate should prove that people can finish the task, not merely that the page renders.',
        'code': "function mustRunSaveJourney(target) {\n  return target.supported && (target.engineGate || target.deviceBoundary);\n}\nconsole.log(mustRunSaveJourney({ supported: true, engineGate: false, deviceBoundary: true }));\n// Output: true",
        'checks': ['The save result is verified against server state.', 'Keyboard and composition paths retain correct input.', 'Actual device checks cover platform-bound behavior.'],
        'mistakes': ['Treating screenshots as interaction tests.', 'Testing only the newest desktop engine.', 'Retrying flaky focus tests until they pass.'],
        'related': ['web-tech/dialog-focus-and-interruption-boundary', 'web-tech/visual-viewport-keyboard-and-focused-input'],
    },
    {
        'hub': 1, 'slug': 'capability-rollout-and-fallback-retirement', 'title': 'Capability Rollout and Fallback Retirement',
        'summary': 'Release optional browser paths gradually and remove old branches only after task-level evidence.',
        'concept': 'A capability rollout introduces a newer browser path without immediately removing the prior way to complete a task. The policy has three independent gates: browser ability, product exposure, and current user authorization. Feature detection cannot grant access to a private export, and a release flag cannot make an unsupported API work. Retiring a fallback is a migration with an owner, evidence, and a reversal path, because old tabs and embedded environments may outlive the deploy that changed the code.',
        'case': 'The permit service adds client-side PDF preview for case 47. A staged release exposes it to a subset of reviewers, but a device with the required browser APIs can still fail because its memory is low. One team removes the server preview after the first successful desktop trial. Support then finds that embedded review stations still depend on it. The team must keep server rendering available until target environments complete real review tasks and failure rates remain acceptable over the agreed observation window.',
        'implementation': 'Evaluate the server-side exposure flag and record authorization first, then probe the local API. Keep old and new paths tied to the same case revision so output cannot silently diverge. Record anonymous outcome categories: offered, started, completed, canceled, failed, and fallback used. Avoid collecting document bytes in telemetry. A kill action should disable the new path without needing a fresh client bundle, while the fallback remains available. Before retirement, inspect active client versions, embedded web views, support cases, and completion by environment. Publish a compatibility window and a rollback plan for old tabs.',
        'cost': 'Maintaining two paths adds code, testing, and server capacity. Removing the fallback saves those costs only after its users have another reliable route. If the new preview uses O(document bytes) memory in the browser, a low-end device may fail even when the API exists. Run a memory and latency budget with realistic 47-page documents, and keep server rendering for devices that exceed it. Telemetry cardinality should be bounded to route and outcome classes rather than individual case IDs.',
        'failure': 'Enable the preview for one test cohort and force a browser memory failure halfway through rendering. The reviewer must return to the server preview without losing the case revision or selected page. Disable the feature flag while a tab is open and ensure the next attempt follows the old path. Deliver a response from a prior case after navigation; it must not paint the current case. Then simulate an older tab requesting an asset after rollout and rollback. Before removing server preview, run the task on every supported station and review fallback-use counts.',
        'drill': 'Write a rollout record for a new case preview with a named owner, exposure stages, completion target, error threshold, and stop action. Keep both routes for an observation period measured by active client versions rather than calendar time alone. Exercise permission denial, API absence, memory failure, and flag rollback. At retirement review, show task completion across device classes and a plan to restore the fallback if a hidden dependency appears.',
        'decision': 'A fallback earns retirement through observed task completion and recoverability, not through a browser support label.',
        'code': "function previewPath(release, environment) {\n  if (!release.authorized || !release.enabled || !environment.previewApi) return 'server-preview';\n  return environment.memoryBudgetMb >= 256 ? 'client-preview' : 'server-preview';\n}\nconsole.log(previewPath({ authorized: true, enabled: true }, { previewApi: true, memoryBudgetMb: 128 }));\n// Output: server-preview",
        'checks': ['Capability, exposure, and authorization are separate gates.', 'A kill action leaves the old path usable.', 'Fallback removal requires evidence from supported stations.'],
        'mistakes': ['Removing the fallback after a desktop-only trial.', 'Equating API presence with enough device memory.', 'Recording private case IDs in rollout telemetry.'],
        'related': ['web-tech/feature-release-and-experiment-controls', 'web-tech/artifact-manifest-rollout-and-rollback-coherence'],
    },
])

assert len(hubs) == 2 and len(topics) == 8
for number, hub in enumerate(hubs):
    path = hub['path']
    assert path not in by_path
    entry = copy.deepcopy(by_path['web-tech/production-signals-and-incident-decisions'])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + path)), path=path,
                 title=hub['title'], summary=hub['summary'], sort_order=3010 + number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    entry['data'] = {'subject_root': 'web-tech/web-technology', 'section_path': path,
                     'content_format': 'html', 'seo_ready': False, 'modules': [],
                     'resource_tabs': [{'title': 'Web Development', 'path': 'web-tech/web-technology'},
                                       {'title': 'Projects', 'path': 'web-tech/web-technology/project'},
                                       {'title': 'Quizzes', 'path': 'web-tech/quizzes'}]}
    entries.append(entry)
    by_path[path] = entry

for number, topic in enumerate(topics):
    path = 'web-tech/' + topic['slug']
    assert path not in by_path
    subprocess.run(['node', '--check', '--input-type=module'], input=topic['code'],
                   text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path['web-tech/trace-context-across-request-and-job'])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'aitrove:' + path)), path=path,
                 title=topic['title'], summary=topic['summary'], sort_order=3020 + number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    hub_path = hubs[topic['hub']]['path']
    related = [hub_path] + ['web-tech/' + item['slug'] for item in topics
                            if item['hub'] == topic['hub'] and item['slug'] != topic['slug']] + topic['related']
    body = p(topic['concept']) + '<h2>Working case</h2>' + p(topic['case'])
    body += '<h2>Implementation boundary</h2><pre><code class="language-javascript">' + html.escape(topic['code'], quote=False) + '</code></pre>' + p(topic['implementation'])
    body += '<h2>Cost and boundaries</h2>' + p(topic['cost']) + '<h2>Failure trace</h2>' + p(topic['failure'])
    body += '<h2>Verification</h2><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in topic['checks']) + '</ul>'
    body += '<h2>Practice drill</h2>' + p(topic['drill']) + '<h2>Decision note</h2>' + p(topic['decision'])
    body += '<h3>Common Mistakes</h3><ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in topic['mistakes']) + '</ul>'
    entry['body'] = body
    entry['data'] = {'subject_root': 'web-tech/web-technology', 'section_path': hub_path,
                     'content_format': 'html', 'seo_ready': False, 'kind': 'tutorial',
                     'author_path': 'authors/aitrove-editorial', 'reading_minutes': 7, 'related': related}
    entries.append(entry)
    by_path[path] = entry

for topic in topics:
    entry = by_path['web-tech/' + topic['slug']]
    entry['body'] += '<h2>Related lessons</h2><p>' + '; '.join(link(target) for target in entry['data']['related']) + '.</p>'

for number, hub in enumerate(hubs):
    group = [item for item in topics if item['hub'] == number]
    entry = by_path[hub['path']]
    entry['data']['modules'] = [{'title': hub['title'], 'summary': hub['summary'],
                                 'lessons': ['web-tech/' + item['slug'] for item in group]}]
    entry['body'] = p(hub['overview']) + '<h2>Topics in this track</h2><ul>' + ''.join(
        '<li>' + link('web-tech/' + item['slug']) + ' — ' + html.escape(item['summary']) + '</li>' for item in group) + '</ul>'
    entry['body'] += '<h2>Prerequisite paths</h2><p>' + '; '.join(link(path) for path in hub['bridges']) + '.</p>'
    entry['body'] += '<h2>Neighbor track</h2><p>' + link(hubs[1 - number]['path']) + '.</p>'

root_entry = by_path['web-tech/web-technology']
for number, hub in enumerate(hubs):
    group = [item for item in topics if item['hub'] == number]
    root_entry['data']['modules'].append({'title': hub['title'], 'summary': hub['summary'],
                                          'lessons': [hub['path']] + ['web-tech/' + item['slug'] for item in group]})
    root_entry['body'] += '<h2>' + link(hub['path']) + '</h2>' + p(hub['summary']) + '<ul>' + ''.join(
        '<li>' + link('web-tech/' + item['slug']) + ' — ' + html.escape(item['summary']) + '</li>' for item in group) + '</ul>'
root_entry['updated_at'] = stamp

crosslinks = {
    'web-tech/web-components-and-shadow-boundaries': [hubs[0]['path'], 'web-tech/custom-element-upgrade-and-reconnection'],
    'web-tech/component-boundaries-and-state': ['web-tech/shadow-slots-events-and-focus-contract'],
    'web-tech/form-server-validation': ['web-tech/form-associated-custom-control-and-native-fallback'],
    'web-tech/cascade-layers-and-design-token-ownership': ['web-tech/shadow-style-tokens-parts-and-shared-sheets'],
    'web-tech/browser-capabilities-and-permission-lifecycle': [hubs[1]['path'], 'web-tech/feature-probes-and-functional-fallbacks'],
    'web-tech/frontend-build-and-artifact-integrity': ['web-tech/polyfill-cost-and-target-browser-policy'],
    'web-tech/integration-and-verification': ['web-tech/cross-browser-input-and-device-contracts'],
    'web-tech/feature-release-and-experiment-controls': ['web-tech/capability-rollout-and-fallback-retirement'],
}
for path, targets in crosslinks.items():
    entry = by_path[path]
    entry['body'] += '<h2>Further connections</h2><p>' + '; '.join(link(target) for target in targets) + '.</p>'
    entry['updated_at'] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_hubs': len(hubs), 'new_lessons': len(topics), 'prose_words': {
    topic['slug']: len(re.findall(r"\b[\w'-]+\b", ' '.join(str(topic[key]) for key in
        ('concept', 'case', 'implementation', 'cost', 'failure', 'drill', 'decision', 'summary')))) for topic in topics}}))
