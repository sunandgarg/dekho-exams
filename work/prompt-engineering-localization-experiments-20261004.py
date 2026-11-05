"""Add original localization-QA and product-experiment prompt curricula."""

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
        "label": "Localization QA",
        "tag": "localization quality",
        "order": 32300,
        "project": "prompt-engineering/harbor-notice-localization-review-project",
        "project_title": "Project: review Harbor's localized delivery notices",
        "quiz": "quizzes/prompt-engineering-localization-qa",
        "quiz_title": "Localization QA prompt decisions",
        "intro": "Review a fictional Harbor Parcel release packet containing 47 notice strings for a second locale. The prompt organizes checks, but the translation engine, browser, and language reviewer decide whether the actual product behaves correctly. Five distinct keys fail for different reasons; the other 42 pass this packet's checks. A clean English preview does not establish that the localized release is ready.",
        "case": "Key HP-07 drops a required delivery-window placeholder; HP-12 lacks a needed plural form for the selected locale; HP-18 places a Latin parcel identifier in right-to-left text without reliable isolation; HP-29 renders a delivery instant with an ambiguous date label; and HP-41 is clipped at narrow width. The reviewer locks the catalog version, locale, route, and test data, assigns each failure to a component or message owner, and retests all five. The release stays blocked until the actual rendered paths and language review pass. None of the five failures is repaired merely by rewriting a summary.",
        "sample": "Catalog H-47: 47 keys; 42 pass; 5 distinct failed keys\nHP-07 placeholder | HP-12 plural | HP-18 mixed direction\nHP-29 date rendering | HP-41 narrow-width clipping\nRelease: blocked pending owner repair and rendered retest",
        "cost": "A first pass over N message keys is O(N); rendering L locales across S important states adds O(LS) review cases, with more cases for plural and viewport boundaries. Human language review remains a separate cost because syntactic parity does not establish meaning. Preserve the five key IDs and exact render states so the follow-up check is targeted rather than an unbounded reread of every string.",
        "mistakes": ["Do not call 42 passing keys a releasable packet while five required keys fail.", "Do not replace actual locale rendering with a model's translation confidence.", "Do not close a finding until the affected route and state are retested."],
        "specs": [
            {
                "slug": "localization-prompt-locale-message-contract",
                "title": "Localization prompts: define the locale and message contract",
                "section": applications,
                "summary": "Pin target locale, catalog version, message purpose, and review state before translating.",
                "definition": "A localization prompt should state the target language and region, catalog version, message key, product state, audience, terminology owner, and output format. A locale label is not a license to guess business meaning: the same word can name a delivery slot, a storage window, or a browser window. Provide enough UI context and keep the source string beside its key. Ask the model to mark ambiguous terms for a language reviewer instead of choosing a fluent but unsupported interpretation. The final artifact is a versioned candidate, not a verified translation.",
                "case": "Harbor has 47 delivery-notice keys in catalog H-47. HP-07 concerns the time range a recipient may choose before confirming delivery, not the period a parcel stays at a collection point. The request supplies the screen, control purpose, locale, and variable schema. The model flags 'window' as ambiguous until the product owner confirms the intended action. That short clarification protects every later translation and avoids a misleading notice on the confirmation screen.",
                "sample": "Catalog H-47 | key HP-07 | state: before delivery confirmation\nAudience: recipient | target locale: ar-EG\nMeaning of window: selectable delivery time range\nVariables: {deliveryWindow} | unresolved terms: stop for review",
                "cost": "Inspecting N keys against a context ledger is O(N) review work; a shared glossary reduces repeated interpretation but still needs version control. Adding context fields costs a small amount of prompt space and prevents expensive retranslation. Keep sensitive recipient data out of examples, and use synthetic parcel details when demonstrating the rendered message.",
                "mistakes": ["Do not translate an ambiguous product term without its screen context.", "Do not mix catalog versions in one approval packet.", "Do not treat a model candidate as language review."],
                "related": ["prompt-engineering/translation-glossary-placeholder-contract", "prompt-engineering/multilingual-equivalence-check"],
            },
            {
                "slug": "localization-prompt-placeholder-and-plural-branches",
                "title": "Localization prompts: preserve variables and plural branches",
                "section": applications,
                "summary": "Compare message structure before judging the phrasing of a localized string.",
                "definition": "A message can sound natural yet fail at runtime because a required variable disappeared or a plural branch is missing. Give the model the message schema, variable types, and supported categories, then require a structural diff before language review. Placeholder names are application contracts; they are not free words to translate. Plural selection belongs to the locale-aware message engine, not an English singular-versus-other shortcut invented in prose. Test representative boundary counts in the actual engine and keep the rendered result in the review packet.",
                "case": "Harbor's HP-07 candidate omits {deliveryWindow}, so the notice cannot show the selected time. HP-12 has a count-dependent message but lacks a category the selected locale requires. The reviewer first catches the missing variable and branch by comparing parsed message structures, then renders several count values to inspect grammar and layout. A model may propose repairs, but the catalog parser and language reviewer must accept them before the key moves to pass.",
                "sample": "HP-07 required: {deliveryWindow}; candidate: missing\nHP-12 required: locale-specific plural branches; candidate: incomplete\nGate 1: parse and compare message structure\nGate 2: render boundary counts and review language",
                "cost": "Parsing N message patterns is O(total pattern length); set comparison of V placeholders is O(V) expected time per key. Rendering several count cases per plural message adds a small, deliberate test matrix. This is cheaper than discovering a blank runtime value after publication, and it keeps linguistic judgment separate from deterministic structure checks.",
                "mistakes": ["Do not translate placeholder identifiers.", "Do not infer every locale's plural behavior from English.", "Do not approve a structurally valid message without rendered language review."],
                "related": ["prompt-engineering/translation-glossary-placeholder-contract", "prompt-engineering/locale-formatting-structured-values"],
            },
            {
                "slug": "localization-prompt-bidirectional-identifier-isolation",
                "title": "Localization prompts: test mixed-direction identifiers",
                "section": applications,
                "summary": "Keep parcel IDs, names, and punctuation readable inside right-to-left notices.",
                "definition": "A right-to-left interface can contain left-to-right identifiers and user-entered names. The prompt should preserve the identifier bytes, state the base direction, and ask for the rendered ordering to be checked in context. String reversal is not localization. Markup or component behavior must isolate a mixed-direction token where needed; punctuation around it may otherwise appear in a confusing position. A text-only model can suggest test cases, but the browser render and assistive interaction determine whether the actual notice remains intelligible.",
                "case": "HP-18 places parcel code PK-47A next to right-to-left notice text. In the first build, punctuation appears detached from the code in one message state. Harbor keeps the code unchanged and repairs the component's direction handling around the inserted value. The reviewer checks the short code, a longer code, and a recipient name with mixed-script characters. The fix is accepted only after those values render correctly in the actual notice surface.",
                "sample": "HP-18 | base direction: right-to-left\nInserted token: PK-47A, exact bytes retained\nObserved: adjacent punctuation rendered ambiguously\nRepair target: isolate inserted token in the component\nRetest: short, long, and mixed-script values",
                "cost": "Testing K inserted-token shapes over S message states costs O(KS) render checks. Most code changes are in one shared component, but each distinct insertion context still needs a check. A screenshot can document visual order; keyboard selection and spoken behavior may require separate inspection when they affect the user task.",
                "mistakes": ["Do not reverse the identifier characters.", "Do not assume a translated string fixes component direction handling.", "Do not test only one short Latin code."],
                "related": ["prompt-engineering/mixed-language-intent-and-reply-locale", "prompt-engineering/ui-visual-and-accessibility-release-gate"],
            },
            {
                "slug": "localization-prompt-typed-date-number-and-unit-rendering",
                "title": "Localization prompts: render typed dates, numbers, and units",
                "section": production,
                "summary": "Keep the underlying value separate from its locale-specific display text.",
                "definition": "A model should not retype a timestamp, quantity, or currency amount into a locale-looking string and then use that string as data. Give it a typed value, its unit or time zone, the target locale, and the intended display role. The application formatter performs rendering; the prompt reviews the result and flags ambiguous labels. A date-only delivery promise differs from an instant in time, and a currency symbol without a code may be unclear across regions. Preserve the machine value and the rendered value together for audit.",
                "case": "HP-29 shows a delivery instant with a numeric date that could be read in two orders. Harbor retains the underlying timestamp and reporting time zone, then asks the formatter to render a target-locale label. The review compares that label with the schedule confirmation and checks whether the day boundary changed correctly. It does not ask a model to guess an instant from an ambiguous source string. A count of 47 parcels likewise stays numeric until the display layer formats it.",
                "sample": "HP-29 input: typed delivery instant + explicit time zone\nDisplay: target-locale date and time from formatter\nAudit: retain instant and rendered label together\nReject: ambiguous numeric date parsed by guesswork",
                "cost": "Formatting N independent values is O(N) application work; testing boundary instants adds a small fixed set per time zone. Keeping typed source fields costs storage but prevents repeated parse errors. The review prompt should spend its tokens on display ambiguities and missing context, not on manual recalculation the runtime can perform consistently.",
                "mistakes": ["Do not parse an ambiguous date without an explicit source format.", "Do not use localized display text as a stored numeric value.", "Do not drop the time zone from an instant-based promise."],
                "related": ["prompt-engineering/locale-formatting-structured-values", "prompt-engineering/input-normalization-contract"],
            },
            {
                "slug": "localization-prompt-terminology-tone-and-human-review",
                "title": "Localization prompts: reconcile terminology and tone",
                "section": production,
                "summary": "Keep product terms consistent while allowing a language reviewer to resolve meaning.",
                "definition": "A glossary is a decision record, not a command to replace every occurrence of a word mechanically. Give each term its concept, product context, approved rendering, prohibited alternatives, and version. Ask the model to flag inconsistencies and awkward register, then route disputed cases to a native language reviewer with the screen and action attached. A support notice, error, and marketing line may require different tone even when they share terminology. The reviewer should approve the meaning and user action, not merely grammatical smoothness.",
                "case": "Harbor uses one approved term for a delivery time range in confirmation notices. A candidate for a failed-delivery message uses a word that instead suggests storage duration. The model flags the glossary conflict; the language reviewer checks the screen and adjusts the message so the recipient understands the next action. The product owner updates the glossary decision for future keys. HP-07 remains blocked until its placeholder and meaning both pass.",
                "sample": "Concept: selectable delivery time range\nCatalog: H-47 | affected: HP-07 and related notices\nModel output: terminology conflict flagged\nHuman decision: approved wording with screen context\nGlossary version: recorded before release",
                "cost": "Comparing N strings to a glossary of indexed terms is O(N) passes plus the cost of disputed-case review. False positives occur when one surface uses a term in a different sense, so a human decides those cases. The glossary reduces future rework only if each approved change is versioned and propagated to all affected strings.",
                "mistakes": ["Do not enforce a glossary term without its concept and context.", "Do not treat fluent grammar as proof of correct product meaning.", "Do not close a dispute without recording the reviewer decision."],
                "related": ["prompt-engineering/translation-glossary-placeholder-contract", "prompt-engineering/multilingual-equivalence-check"],
            },
            {
                "slug": "localization-prompt-pseudolocale-layout-and-input-matrix",
                "title": "Localization prompts: use pseudolocale and real layout checks",
                "section": production,
                "summary": "Find hard-coded text and clipped controls before and after translation review.",
                "definition": "Pseudolocalization can expose text baked into a component, length assumptions, and untranslated fragments before language review. A prompt can specify test states and turn screenshots into candidate findings, but the rendered interface decides whether controls remain readable and operable. Test long labels, narrow widths, zoom, form errors, and dialogs. Do not confuse a pseudolocale pass with a real locale pass: the latter still needs script, direction, plural, input-method, and language checks. Record the viewport and state for every clipping report.",
                "case": "Harbor's HP-41 notice fits in the default desktop card but clips its final action at a narrow viewport after translation. A pseudolocale had already warned that the button width was fixed. The reviewer captures the real localized build at the failing width and traces the hidden action through keyboard focus. The component owner changes wrapping and sizing; the reviewer repeats the state with a long recipient name rather than approving a static screenshot alone.",
                "sample": "HP-41 | state: delivery notice with final action\nViewport: narrow; zoom and long name included\nObserved: action clipped by fixed-width card\nRepair: component wraps without hiding the action\nRetest: real locale plus keyboard operation",
                "cost": "A matrix of V viewport settings, S states, and L locales requires O(VSL) targeted render checks. Shared component tests reduce repetition but do not replace a real translated page review. Prioritize states with required actions and known long strings; a huge screenshot set without interaction evidence can still miss a blocked task.",
                "mistakes": ["Do not call a pseudolocale pass a language approval.", "Do not inspect only desktop idle state.", "Do not accept an action that is visible but cannot be operated."],
                "related": ["prompt-engineering/accessibility-prompt-zoom-reflow-and-viewport-check", "prompt-engineering/cross-locale-evaluation-slice"],
            },
            {
                "slug": "localization-prompt-catalog-diff-and-release-retest",
                "title": "Localization prompts: gate release on catalog and rendered retests",
                "section": production,
                "summary": "Reconcile key coverage, owners, and fixed states before approving a locale.",
                "definition": "A localization release packet needs the source and target catalog versions, changed-key list, placeholder and plural checks, language-review status, rendered-state evidence, open defects, and named approval. The prompt may summarize that packet, but it must not convert missing checks into a pass. Count distinct failed keys, not screenshots or repeated observations, and preserve each finding's owner and retest path. A fix to a shared renderer can close several failures only after every affected state is checked against the same release build.",
                "case": "Harbor's H-47 packet has 47 keys. Forty-two pass, while HP-07, HP-12, HP-18, HP-29, and HP-41 each fail a different gate. A reviewer assigns the first two to message owners, mixed direction and clipping to component owners, and date ambiguity to the formatter owner. After repairs, the packet records the new catalog and build versions plus retest evidence for all five. Until then, the localized release remains blocked regardless of a polished summary.",
                "sample": "H-47: 47 keys = 42 pass + 5 failed distinct keys\nOpen: HP-07, HP-12, HP-18, HP-29, HP-41\nRequired: owner, fixed build, rendered retest, language review\nDecision now: do not release the locale",
                "cost": "Set comparison between source and target catalogs is O(N) expected time for N keys; retesting F failed keys adds at least O(F) targeted checks. A release ledger saves time by narrowing inspection to changed and affected states, but shared-component changes still warrant broader regression samples. No prompt wording can replace missing runtime or language evidence.",
                "mistakes": ["Do not count five screenshots of one defect as five distinct failed keys.", "Do not approve a locale with an untested required action.", "Do not omit the catalog and build versions from a retest receipt."],
                "related": ["prompt-engineering/cross-locale-evaluation-slice", "prompt-engineering/release-regression-gate"],
            },
        ],
        "backlinks": [
            ("prompt-engineering/translation-glossary-placeholder-contract", 0),
            ("prompt-engineering/multilingual-equivalence-check", 1),
            ("prompt-engineering/mixed-language-intent-and-reply-locale", 2),
            ("prompt-engineering/locale-formatting-structured-values", 3),
            ("prompt-engineering/cross-locale-evaluation-slice", 5),
            ("prompt-engineering/release-regression-gate", 6),
        ],
        "questions": [
            ("What must a localization request identify?", "Target locale, catalog version, key, and product state", "Only the source sentence", "Only a desired word count", "Meaning depends on where the message appears."),
            ("What makes HP-07 fail?", "It omits the required delivery-window variable", "It contains a parcel code", "It uses a narrow card", "The message cannot render its required value."),
            ("How is HP-12 checked?", "Parse branches and render representative counts in the locale engine", "Use English singular rules", "Count source words", "Plural structure and language both need review."),
            ("How should PK-47A appear in right-to-left text?", "Keep the code bytes and isolate the inserted token", "Reverse the code characters", "Remove its letters", "The identifier must remain exact while direction is handled by the component."),
            ("What should HP-29 retain?", "Typed instant, time zone, and rendered label", "Only an ambiguous numeric string", "Only a screenshot", "The display must be traceable to its underlying value."),
            ("Who resolves a disputed product term?", "A language reviewer using the screen context", "The model alone", "The glossary search count", "Product meaning requires contextual review."),
            ("What can a pseudolocale reveal?", "Hard-coded text and layout length assumptions", "Final translation quality", "The exact spoken result", "Synthetic expansion is a layout probe."),
            ("What fails for HP-41?", "A required action clips at narrow width", "Its placeholder is missing", "The count is duplicated", "The rendered state hides the final action."),
            ("How many H-47 keys fail?", "Five distinct keys", "Forty-two", "Forty-seven", "47 equals 42 passing plus five failed keys."),
            ("Does a fluent candidate prove the locale is ready?", "No, runtime and language review remain", "Yes, always", "Only if it is short", "Fluency does not test structure or interaction."),
            ("What closes a repaired finding?", "A retest on the fixed catalog and build", "A rewritten status paragraph", "An unverified patch", "The affected state must be observed again."),
            ("What is Harbor's current release decision?", "Block the locale until all five failures are resolved", "Release because 42 pass", "Ignore the clipped action", "Required failures remain open."),
        ],
    },
    {
        "label": "Product experiments",
        "tag": "product experimentation",
        "order": 32400,
        "project": "prompt-engineering/aster-signup-experiment-review-project",
        "project_title": "Project: review Aster's signup experiment",
        "quiz": "quizzes/prompt-engineering-product-experiments",
        "quiz_title": "Product experiment prompt decisions",
        "intro": "Review a fictional Aster Console signup experiment with two assigned groups of 4,800 users each. The prompt may draft analysis from a locked packet, but it must preserve the randomization unit, outcome window, logging checks, and planned decision rule. A descriptive difference is not a license to ship while exposure records and a support-ticket guardrail remain unresolved.",
        "case": "Control has 2,304 signup completions within 24 hours, or 48% of 4,800 assigned users. Treatment has 2,496, or 52%; the observed difference is 4 percentage points. The exposure ledger contains 4,600 control and 4,500 treatment records, fewer than assigned in both groups, so the team investigates logging and eligibility before interpreting the effect. Support-ticket counts are 96/4,800 (2%) in control and 144/4,800 (3%) in treatment. The packet contains no checked uncertainty estimate or confirmed reason for the logging gap. The current decision is hold, repair the evidence path, and rerun the locked analysis.",
        "sample": "Assigned: control 4,800; treatment 4,800\n24h completions: 2,304/4,800 = 48%; 2,496/4,800 = 52%\nObserved difference: +4 percentage points\nExposure records: 4,600 control; 4,500 treatment; investigate\nSupport tickets: 96/4,800 = 2%; 144/4,800 = 3%\nDecision: hold pending data-quality and guardrail review",
        "cost": "Reconstructing N assignment and outcome records is O(N) expected time with an identity map; auditing several metrics and slices multiplies review work. More prose cannot compensate for a broken exposure ledger or an unplanned decision threshold. Store the randomization key, query version, observation cutoff, and investigation outcome so a later run can reproduce the same comparison.",
        "mistakes": ["Do not call a four-point observed difference a proven improvement without validated inference.", "Do not change the denominator from assigned users to logged exposures mid-analysis.", "Do not hide the higher support-ticket rate when discussing rollout."],
        "specs": [
            {
                "slug": "experiment-prompt-hypothesis-unit-and-exposure-contract",
                "title": "Experiment prompts: fix hypothesis, unit, and exposure",
                "section": applications,
                "summary": "State what changes, who is randomized, and when an assignment becomes exposure.",
                "definition": "An experiment prompt should name the product hypothesis, control behavior, treatment behavior, assignment unit, eligibility rule, exposure event, outcome window, and intended decision. Randomizing a user while measuring sessions can produce repeated correlated rows if the analysis forgets the user key. Assignment is not exposure: a person can be assigned but never load the changed surface, or the exposure log can fail. Keep these populations separate and decide the primary analysis rule before examining results. The model can expose missing definitions, but it cannot repair inconsistent assignment IDs by persuasive wording.",
                "case": "Aster tests a shorter signup form. The randomization unit is an eligible user at signup entry; the treatment is the shortened form, while control retains the current form. There are 4,800 assigned users per arm. Exposure logs contain only 4,600 control and 4,500 treatment records. The analyst does not switch to logged exposure as the denominator merely to make the treatment look stronger. They investigate logging before accepting an effect claim.",
                "sample": "Hypothesis: shorter form may change 24h signup completion\nUnit: eligible assigned user at signup entry\nAssigned: 4,800 control; 4,800 treatment\nExposure logs: 4,600 and 4,500; reason unknown\nPrimary unit and window: frozen before analysis",
                "cost": "Mapping N assignments to exposure and outcome rows is O(N) expected time and O(N) memory. Defining the unit early prevents a more expensive reinterpretation after the result is known. A model can draft a contract checklist, but instrumentation and assignment-service logs must be inspected independently when their populations disagree.",
                "mistakes": ["Do not use sessions as independent users without a declared rule.", "Do not equate assignment with confirmed exposure.", "Do not choose the denominator after seeing the outcome."],
                "related": ["prompt-engineering/analytics-prompt-metric-and-event-contract", "prompt-engineering/online-prompt-experiment-stop-rules"],
            },
            {
                "slug": "experiment-prompt-assignment-balance-and-srm-investigation",
                "title": "Experiment prompts: investigate assignment and exposure imbalance",
                "section": applications,
                "summary": "Check configured split, assigned counts, and logged exposure before reading outcomes.",
                "definition": "The prompt should request the configured allocation, unique assigned-unit counts, identity exclusions, and exposure-log counts for each arm. An apparent sample-ratio mismatch is a data-quality symptom; it is not automatically a product effect or a verdict about randomization. Use a prespecified statistical check where the experiment platform supports one, but first inspect duplicate IDs, bot filters, missing events, and variant-specific logging. Do not declare a formal mismatch from two numbers without the allocation rule and check result. Keep the investigation outcome attached to the analysis packet.",
                "case": "Aster intended a 1:1 assignment and observes exactly 4,800 unique assigned users in each arm. That count alone does not validate exposure logging: the recorded exposures are 4,600 and 4,500. The model lists plausible failure paths, such as variant-specific event loss or different eligibility at the surface. An engineer checks the emitters and the analyst verifies identity filters. Until the discrepancy is explained, the effect memo remains provisional.",
                "sample": "Configured assignment 1:1\nObserved assigned 4,800 : 4,800\nLogged exposure 4,600 : 4,500\nStatus: investigate missing or unequal exposure records\nDo not label a formal SRM without the planned check",
                "cost": "Counting N unique assignments and exposures with hashed IDs is O(N) expected time and O(N) memory. Additional joins across client and server logs can dominate the investigation cost. Automated alerts are useful triage, but a reviewer must establish whether the mismatch comes from assignment, filtering, or telemetry before interpreting the outcome table.",
                "mistakes": ["Do not read the outcome delta before resolving a serious data-quality flag.", "Do not treat equal assigned counts as proof every user saw the intended surface.", "Do not call an unequal log count a formal statistical mismatch without its test."],
                "related": ["prompt-engineering/analytics-prompt-identity-dedup-and-late-events", "prompt-engineering/analytics-prompt-read-only-query-and-reconciliation"],
            },
            {
                "slug": "experiment-prompt-primary-metric-guardrail-and-plan-freeze",
                "title": "Experiment prompts: freeze the primary metric and guardrails",
                "section": applications,
                "summary": "Declare one decision metric, harm checks, and observation window before launch.",
                "definition": "An experiment plan should define a primary metric, its unit and denominator, guardrails for likely harms, minimum run or observation window, analysis method, and decision threshold before assignment begins. The model can draft the plan and identify missing fields, but a human owner approves it. An unplanned metric discovered after looking at many outcomes is exploratory, not the same evidence as a preregistered primary measure. Guardrails are part of the release decision even when the primary metric moves in the hoped-for direction.",
                "case": "Aster's primary outcome is signup completion within 24 hours per assigned eligible user. Its support-ticket rate is a guardrail because a shorter form may omit needed guidance. The packet later shows 48% versus 52% completion and 2% versus 3% support tickets. Those numbers are descriptive until the approved analysis and data-quality checks run. Aster cannot rewrite the plan to ignore support tickets after seeing the increase.",
                "sample": "Primary: 24h completion / assigned eligible users\nGuardrail: support tickets / assigned eligible users\nAnalysis and decision threshold: locked before launch\nExploratory slices: labeled separately\nPlan changes: versioned, not silently backdated",
                "cost": "Checking M planned metrics across N assigned users is O(MN) in a naive scan or O(N+M) with a prepared per-user fact table and indexed aggregates. Planning is cheap compared with arguing over a favorable post hoc metric. Keep the frozen plan and every later amendment visible in the review packet.",
                "mistakes": ["Do not select a primary metric after seeing all outcomes.", "Do not omit a plausible harm measure from the decision.", "Do not confuse an exploratory slice with a planned confirmatory test."],
                "related": ["prompt-engineering/analytics-prompt-metric-and-event-contract", "prompt-engineering/study-effect-measure-and-denominator-check"],
            },
            {
                "slug": "experiment-prompt-missing-outcomes-and-unit-reconciliation",
                "title": "Experiment prompts: reconcile missing outcomes by assigned unit",
                "section": production,
                "summary": "Keep assigned users visible when exposure or outcome logging is incomplete.",
                "definition": "Missing events can arise from product behavior, delayed ingestion, client loss, or a broken emitter. A prompt for experiment analysis should request a disposition table by assigned arm: assigned IDs, exposure records, outcome records, late arrivals, exclusions, and reasons. A missing outcome is not always a failure to complete; that interpretation requires a trusted server-side outcome path and an observation window that has matured. Avoid a complete-case comparison that silently drops users with missing telemetry, because missingness may differ by variant.",
                "case": "Aster sees 4,800 assigned users in each arm but fewer exposure logs. The team verifies whether 24-hour completion comes from a server-confirmed account record rather than the same incomplete client channel. It lists missing exposure IDs by variant and checks whether those users have outcomes. If the missingness is variant-specific, the analyst cannot simply use 4,600 and 4,500 as clean observed populations. The memo holds the uncertainty until the data path is understood.",
                "sample": "Arm ledger: assigned | exposure logged | outcome observed\nControl: 4,800 | 4,600 | verify server outcome path\nTreatment: 4,800 | 4,500 | verify server outcome path\nLate records and exclusions: count with reasons\nAnalysis status: provisional while missingness unresolved",
                "cost": "Joining N assignment IDs with outcome and exposure tables is O(N) expected time with indexed keys and O(N) memory for the reconciliation ledger. Missingness review can require engineering traces rather than another aggregate query. Preserve the assigned population in the packet even if some events cannot yet be classified.",
                "mistakes": ["Do not treat every absent client event as a real noncompletion.", "Do not compare only complete telemetry rows without checking variant bias.", "Do not hide late-arrival and exclusion counts."],
                "related": ["prompt-engineering/analytics-prompt-identity-dedup-and-late-events", "prompt-engineering/analytics-prompt-cohort-window-and-time-zone"],
            },
            {
                "slug": "experiment-prompt-effect-uncertainty-and-multiple-looks",
                "title": "Experiment prompts: separate effect size from uncertainty",
                "section": production,
                "summary": "Report the observed difference, then apply the planned inference method outside prose.",
                "definition": "A treatment-control difference is a descriptive estimate. An experiment claim also needs the planned uncertainty method, randomization and data-quality checks, observation cutoff, and handling of repeated looks or many tested outcomes. Have code calculate the effect and its uncertainty from a locked dataset; the model should explain the result without fabricating a confidence interval or p-value. If the team repeatedly checks results and stops at the first favorable number, an ordinary one-time test no longer has its advertised error behavior. Preserve the planned stopping rule and all reviewed looks.",
                "case": "Aster's assigned-user rates are 2,304/4,800 = 48% for control and 2,496/4,800 = 52% for treatment. The observed difference is four percentage points. The packet does not include a checked interval or a completed exposure-log investigation, so the model may report the descriptive numbers but cannot claim a verified lift. Aster also records when interim reviews occurred; it does not present the most favorable day as the final planned readout.",
                "sample": "Control 2,304 / 4,800 = 48%\nTreatment 2,496 / 4,800 = 52%\nObserved difference = +4 percentage points\nChecked interval or test result: absent\nInference claim: withheld",
                "cost": "Computing two rates from validated counters is O(1); preparing the per-user table is O(N) for N assigned users. Uncertainty calculations depend on the prespecified design and may be more complex when units are clustered or outcomes are correlated. The prompt should keep the arithmetic and inference artifacts separate so a reviewer can reproduce each one.",
                "mistakes": ["Do not invent a confidence interval from an aggregate summary.", "Do not equate four percentage points with statistical certainty.", "Do not hide repeated interim looks."],
                "related": ["prompt-engineering/study-effect-measure-and-denominator-check", "prompt-engineering/online-prompt-experiment-stop-rules"],
            },
            {
                "slug": "experiment-prompt-heterogeneity-and-guardrail-investigation",
                "title": "Experiment prompts: investigate slices and guardrail movement",
                "section": production,
                "summary": "Treat subgroup stories as exploratory unless the comparison was planned and checked.",
                "definition": "Segmenting an experiment after a surprising result can help diagnose a mechanism, but every extra slice offers another chance to see noise. A prompt should distinguish prespecified subgroups from exploratory investigations, keep denominators and assignment rules on both sides, and record whether the slice was chosen before or after outcome review. A guardrail movement deserves its own validity and practical-impact check. Do not dismiss a possible harm solely because the primary metric improved; the joint release decision must consider both.",
                "case": "Aster has 96 support tickets among 4,800 control users, or 2%, and 144 among 4,800 treatment users, or 3%. The observed guardrail difference is one percentage point. The analyst checks ticket taxonomy, duplicate reports, attribution window, and whether form confusion could explain the movement. A model may suggest a mobile slice, but unless it was planned, that slice is exploratory and cannot rescue a blocked rollout by itself.",
                "sample": "Support guardrail: control 96/4,800 = 2%\nTreatment 144/4,800 = 3%\nObserved difference: +1 percentage point\nInvestigate taxonomy, duplicates, window, and mechanism\nPost hoc slices: exploratory labels retained",
                "cost": "Scanning N ticket records and assignment IDs is O(N) expected time with indexed joins; K subgroup analyses can multiply compute and review costs. The more important cost is interpretive: many unplanned slices make one attractive story easy to find. Keep a slice ledger and require a separate confirmation plan for a new subgroup hypothesis.",
                "mistakes": ["Do not ignore the higher ticket rate because completion increased.", "Do not promote a post hoc subgroup story to the primary result.", "Do not compare ticket counts without the assigned-user denominators."],
                "related": ["prompt-engineering/analytics-prompt-segment-gap-and-causal-restraint", "prompt-engineering/aggregate-denominator-reconciliation"],
            },
            {
                "slug": "experiment-prompt-rollout-decision-and-reproducible-packet",
                "title": "Experiment prompts: gate rollout on a reproducible packet",
                "section": production,
                "summary": "Make the ship, hold, or revert decision traceable to the frozen plan and verified logs.",
                "definition": "A final experiment memo should include the plan version, assignment and exposure counts, outcome definitions, data-quality investigations, effect and uncertainty artifacts, guardrails, open issues, decision owner, and follow-up monitoring. Prompt the model to draft only from that locked packet. A persuasive headline cannot substitute for a verified exposure path or a guardrail review. If a staged rollout is approved later, record its audience, duration, stop conditions, and monitoring ownership before changing traffic. The current decision may be hold even when the observed primary difference is favorable.",
                "case": "Aster's packet shows a four-point descriptive completion advantage for treatment, but its exposure records are incomplete and treatment support tickets are one point higher. The approved memo does not call the shorter form successful. The owner holds rollout, checks exposure emitters and ticket classification, recomputes the planned analysis, and reviews uncertainty before any traffic change. A later approval would need a separate staged rollout record and monitoring receipt.",
                "sample": "Primary descriptive difference: +4 percentage points\nExposure discrepancy: unresolved\nSupport guardrail: +1 percentage point in treatment\nDecision: hold; verify logs and harm signal\nFuture rollout: only after new reviewed packet",
                "cost": "Reconciling C memo claims against indexed tables is O(C) lookups plus review time; staged monitoring processes N new events in O(N). The packet prevents repeated debate over which numbers were used. Do not let the model fill missing uncertainty or approval fields with plausible text merely to complete a template.",
                "mistakes": ["Do not ship from a favorable descriptive rate alone.", "Do not erase the unresolved exposure discrepancy.", "Do not imply a staged rollout occurred without its receipt."],
                "related": ["prompt-engineering/analytics-prompt-decision-memo-and-monitoring-gate", "prompt-engineering/report-claim-ledger-and-number-reconciliation"],
            },
        ],
        "backlinks": [
            ("prompt-engineering/online-prompt-experiment-stop-rules", 0),
            ("prompt-engineering/analytics-prompt-metric-and-event-contract", 1),
            ("prompt-engineering/evaluation-slice-design", 2),
            ("prompt-engineering/analytics-prompt-identity-dedup-and-late-events", 3),
            ("prompt-engineering/study-effect-measure-and-denominator-check", 4),
            ("prompt-engineering/analytics-prompt-segment-gap-and-causal-restraint", 5),
            ("prompt-engineering/analytics-prompt-decision-memo-and-monitoring-gate", 6),
        ],
        "questions": [
            ("What is Aster's randomization unit?", "Eligible user at signup entry", "Each page view", "Each support ticket", "The unit is fixed before assignment."),
            ("Are assignment and exposure identical?", "No, logged exposure can be missing after assignment", "Yes, always", "Only in treatment", "The two populations need separate ledgers."),
            ("What do 4,600 and 4,500 describe?", "Logged exposures needing investigation", "Assigned users", "24-hour completions", "They are lower than the 4,800 assigned per arm."),
            ("Can the log gap be called formal sample-ratio mismatch now?", "Not without the planned allocation check and investigation", "Yes, from unequal numbers alone", "No data check is needed", "A formal label requires its configured statistical check."),
            ("What is Aster's primary metric?", "24-hour completions per assigned eligible user", "Tickets per screenshot", "Any favorable slice", "The plan fixes unit, outcome, and window."),
            ("What is control's completion rate?", "2,304 / 4,800 = 48%", "2,304 / 4,600 = 48%", "2,304 / 9,600 = 48%", "The planned denominator is assigned eligible users."),
            ("What is treatment's completion rate?", "2,496 / 4,800 = 52%", "2,496 / 4,500 = 52%", "4,800 / 2,496 = 52%", "The same assigned-user rule applies to treatment."),
            ("What is the observed primary difference?", "+4 percentage points, with inference still unverified", "+4% proven causal improvement", "No difference", "The rates differ, but validated inference is absent."),
            ("How should missing client outcomes be treated?", "Reconcile against the trusted server path and window", "Always call them failures", "Drop those users silently", "Missing telemetry is not automatically user behavior."),
            ("What is treatment's support-ticket rate?", "144 / 4,800 = 3%", "144 / 9,600 = 3%", "96 / 4,800 = 3%", "The guardrail uses assigned treatment users."),
            ("May a post hoc mobile slice override the primary result?", "No, keep it exploratory and plan confirmation", "Yes, if it looks favorable", "Yes, without a denominator", "Unplanned slices do not replace the frozen decision plan."),
            ("What is the current rollout decision?", "Hold while logging and guardrail concerns are investigated", "Ship immediately", "Hide the ticket result", "The evidence packet has unresolved release gates."),
        ],
    },
]

new_paths = []
for cluster in clusters:
    new_paths += ["prompt-engineering/" + spec["slug"] for spec in cluster["specs"]]
    new_paths += [cluster["project"], cluster["quiz"]]
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
    new_rows.append(article(cluster["project"], cluster["project_title"], "Apply the full " + cluster["label"].lower() + " evidence contract to a fictional release packet.", project_body, projects, cluster["order"] + 80, project_connections, cluster["tag"], "project"))

    quiz = copy.deepcopy(lookup["quizzes/prompt-engineering-security-alert-triage"])
    quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + cluster["quiz"])), path=cluster["quiz"],
                title=cluster["quiz_title"], summary="Test evidence, calculations, boundaries, and release decisions in " + cluster["label"].lower() + ".",
                body="<p>Choose the decision supported by the recorded packet.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([cluster["project"], applications, production, quizzes]),
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
