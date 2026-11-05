"""Build an original, linked prompt engineering curriculum in local fixtures."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path


root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
root_path = "prompt-engineering/prompt-engineering"
patterns_path = "prompt-engineering/patterns"
production_path = "prompt-engineering/production"
projects_path = "prompt-engineering/projects"
quizzes_path = "prompt-engineering/quizzes"
project_paths = ["prompt-engineering/incident-handoff-evaluation-project", "prompt-engineering/retrieval-action-boundary-project"]
quiz_paths = ["quizzes/prompt-engineering-design-decisions", "quizzes/prompt-engineering-production-decisions"]


def lesson(slug, title, summary, section, definition, decision, sample, cost, mistakes, related, language="text"):
    return dict(path="prompt-engineering/" + slug, title=title, summary=summary,
                section=section, definition=definition, decision=decision,
                sample=sample, language=language, cost=cost,
                mistakes=mistakes, related=related)


specs = [
    lesson(
        "intent-to-acceptance-check",
        "Prompt intent: turn an open request into an acceptance check",
        "Translate a vague request into a result, evidence boundary, and pass condition.", root_path,
        "A prompt is useful when its output can be accepted or rejected for reasons other than taste. The acceptance check states the required facts, forbidden changes, target reader, and uncertainty treatment. It is separate from a persona or a request to sound expert. When a user asks for a broad improvement, identify the part that can be completed with available inputs and mark any missing decision instead of inventing it. The check should be observable in the response or in a downstream test.",
        "A payroll operations team asks an assistant to improve a failed-run summary. The real job is narrower: explain which of 37 settlement jobs failed, which succeeded after retry, and which have no final state. The prompt names the input ledger and requires a three-part handoff with job IDs; it forbids guessing that a missing event means success. An operator checks every listed ID against the ledger and rejects any action without a matching event. If the team later changes its alerting policy, the acceptance check changes explicitly; tone edits alone should not silently alter the pass rule.",
        "Task: Prepare a payroll failed-run handoff from ledger batch PR-83.\nInclude: failed, recovered, and unknown job IDs.\nDo not infer success from a missing final event.\nPass: every claim maps to a ledger event; unresolved jobs remain explicit.",
        "Writing an acceptance check takes review time before generation, but saves repeated ambiguous revisions. The check need not predict every sentence; it must cover consequences that matter. For a batch of N ledger rows, verifying claimed IDs is at least O(N) in a simple scan, or can use an indexed lookup if the ledger is larger. Record failed checks, not only the final polished answer. A prompt that satisfies a word count while misclassifying a failed job is still wrong.",
        ["Do not use a style adjective as the only success criterion.", "Do not hide missing evidence inside confident prose.", "Do not change the job and the pass rule in the same unrecorded revision."],
        ["prompt-engineering/task-contract", "prompt-engineering/evaluate-and-revise"],
    ),
    lesson(
        "input-normalization-contract",
        "Prompt inputs: normalize records before asking for conclusions",
        "Mixed units and identifiers can make a precise prompt produce a wrong answer.", root_path,
        "Input normalization turns raw material into a stable set of fields, units, timestamps, and identifiers. It is not the same as deleting messy rows: missing fields remain missing and conflicting values remain visible. A model can compare numbers only when the units and periods are explicit. Give the model a compact field dictionary and ask it to surface records that do not meet the contract. Deterministic parsing belongs in application code where possible; a prompt should interpret the normalized record, not substitute for basic validation.",
        "A warehouse planner sends a spreadsheet export containing 63 stock movements. Some quantity fields are cartons, others are individual units, and two records reuse a shipment ID. The ingestion step labels units and preserves source row IDs. The prompt asks for the net movement by SKU only after a validator checks that each carton size is known. For the two reused shipment IDs it must report a conflict, not silently deduplicate them. An operator samples the arithmetic for three SKUs and checks that the reported unknown count matches the rejected rows.",
        "Input record: row_id, shipment_id, sku, quantity, unit, carton_size.\nPrecheck: reject unknown unit or missing carton_size.\nPrompt task: summarize valid movement; list rejected row IDs separately.\nPass: no unit conversion without a recorded factor.",
        "Normalization adds an O(N) pass over N rows and a small storage copy, but prevents a costly conclusion from inconsistent data. Keep the raw export for audit and version the conversion rules. If a model is asked to infer carton size from nearby rows, one plausible answer can contaminate an entire inventory report. A failure report should count invalid rows and explain which field blocked calculation. Distinguish a duplicate business event from a duplicate identifier; those require different reconciliation.",
        ["Do not silently convert unknown units.", "Do not drop conflicting rows without a count and reason.", "Do not assume a duplicated identifier proves a duplicated event."],
        ["prompt-engineering/task-contract", "prompt-engineering/schema-and-abstention"],
    ),
    lesson(
        "few-shot-example-selection",
        "Few-shot prompting: select examples that cover decisions, not just easy cases",
        "Examples in a prompt demonstrate a boundary; they do not update model weights.", root_path,
        "A few-shot set gives the model concrete input-output pairs for the current request. Its value comes from representative decisions and edge cases, not a large stack of similar positive examples. Select cases with distinct failure modes and keep them separate from the item to be classified. Include the negative or abstain case when the task permits uncertainty. If examples contain sensitive data, replace them with synthetic records that preserve the decision structure. Evaluate the prompt on records that were not used as examples.",
        "A support team classifies refund tickets into approved, denied, or needs-review. Three examples cover a valid 31-day warranty claim, an expired warranty with no exception, and a case where the purchase date is absent. A fourth shows conflicting order identifiers. Each example names the policy field that drove its label. The candidate ticket is placed after the examples with a clear boundary. The team then tests 52 held-out tickets across the same classes, including rare conflicts, instead of scoring the four prompt examples as if they were independent proof of quality.",
        "Example A: purchase age 31 days; policy window 44 days -> approved.\nExample B: purchase age 61 days; no exception -> denied.\nExample C: purchase date missing -> needs-review.\nCandidate: classify ticket RT-582 and name the deciding field.",
        "Each extra example adds input tokens, latency, and sometimes distraction. The total context cost grows with example count and example length, while coverage can plateau or regress. Compare a zero-example baseline with a small, diverse set on the same held-out cases. If the task changes, refresh examples and evaluation together but preserve a stable core set for comparison. An example is a teaching artifact, not a policy source: the current policy still controls the answer.",
        ["Do not choose only favorable examples.", "Do not leak the evaluation answer into the prompt examples.", "Do not let an old example override the current policy."],
        ["prompt-engineering/evaluate-and-revise", "prompt-engineering/input-normalization-contract"],
    ),
    lesson(
        "schema-and-abstention",
        "Output contracts: parse a result and preserve an explicit unknown state",
        "A well-formed response can still contain a false value.", root_path,
        "An output schema defines required fields, types, and allowed values for a downstream reader. It should include a representation for missing or insufficient evidence rather than forcing every case into a confident label. The application validates both structure and business rules after generation. For example, a date string can be valid JSON while referring to an event that is absent from the input. Keep generated explanations and evidence IDs separate from fields that authorize an action. If a provider supports constrained structured output, use it for syntax; keep semantic verification in application code.",
        "A maintenance desk extracts warranty decisions from service notes. The result requires case_id, decision, evidence_rows, and uncertainty_reason. Decision may be approve, deny, or review. The schema forbids an empty evidence list for approve or deny, and the validator checks that each evidence row exists in the supplied case. A note that says the purchase receipt is missing must return review with a reason. The team rejects a syntactically valid approve result when its cited receipt row does not exist. A human signs off before the result changes an account balance.",
        '{"case_id":"SR-274","decision":"review","evidence_rows":["note-7"],"uncertainty_reason":"Purchase date absent"}',
        "Schema validation is usually linear in output size; verifying evidence references adds lookups against the input, which can be indexed. Retry only for repairable format errors and cap attempts, since repeated model calls consume money and can create new inconsistencies. Count structural failures separately from unsupported decisions. A parser rejecting a response is preferable to silently assigning a default decision. A short output also reduces review cost, provided it retains the evidence needed to audit the result.",
        ["Do not treat valid JSON as verified truth.", "Do not force an unknown case into a binary decision.", "Do not execute a financial effect from a model field without application checks."],
        ["prompt-engineering/input-normalization-contract", "prompt-engineering/evaluate-and-revise"], "json",
    ),
    lesson(
        "task-decomposition-and-handoffs",
        "Prompt decomposition: split stages at verifiable handoffs",
        "A multi-step workflow is easier to inspect when each stage has a narrow output contract.", root_path,
        "Task decomposition separates extraction, calculation, decision, and presentation when those steps require different evidence or checks. It does not mean asking for long hidden reasoning. Each stage should emit a compact artifact that the next stage can validate: normalized facts, a computed total, a policy decision, then a reader-facing explanation. Use deterministic code for arithmetic and parsing when possible. Stop the chain if a required field or validation fails; otherwise one early mistake can be polished into a convincing final report.",
        "A shipping analyst needs a late-delivery credit recommendation from 86 tracking events. Stage one extracts event times and route IDs. Code computes transit duration and compares it with a 39-hour service threshold. Stage two asks the model to explain policy exceptions from the relevant contract section. Stage three drafts a customer-facing note only for cases that passed the calculation and policy gates. If one event has two incompatible arrival times, the chain marks it unresolved and skips the credit note. The team stores each handoff artifact with the prompt version for replay.",
        "Stage 1 -> normalized tracking events with source IDs.\nGate 1 -> reject incompatible timestamps.\nCode -> transit hours and threshold comparison.\nStage 2 -> exception decision with policy section.\nGate 2 -> approved or review; only approved reaches customer note.",
        "Multiple calls increase latency and cost, but they also create places to catch a failure before it becomes a customer action. For K sequential model stages, minimum request latency is approximately the sum of stage latencies unless independent stages run in parallel. Measure stage-specific error rates and end-to-end completion. Do not add a stage that merely paraphrases another stage without a check; it spends tokens and can alter the meaning. A compact handoff avoids carrying the entire conversation into every call.",
        ["Do not pass an unvalidated stage output forward.", "Do not use a model for arithmetic that code can perform exactly.", "Do not add stages without a measurable quality or safety gain."],
        ["prompt-engineering/task-contract", "prompt-engineering/schema-and-abstention"],
    ),
    lesson(
        "retrieval-evidence-selection",
        "Retrieved context: select sufficient evidence before writing the answer",
        "Retrieval supplies candidate passages; it does not prove the answer is present.", patterns_path,
        "A retrieval-backed prompt receives excerpts selected by a search or ranking system. Relevance to the query is weaker than answer sufficiency: a passage can mention the right product while omitting the date, exception, or scope needed to answer. Give each excerpt a stable document ID, version, and section. Ask the model to identify the exact evidence required and to abstain when a required field is absent. Retrieval and generation should be measured separately, since rewriting the prompt cannot recover a passage the retriever never supplied.",
        "An operations assistant answers whether a 47-minute outage qualifies for a service credit. Search returns a current contract section with the threshold but no clause about planned maintenance, plus an older contract that mentions maintenance. The assistant must not combine those versions into a confident decision. It requests the current exception clause or returns unresolved with the missing clause named. The evaluation set includes both sufficient and insufficient retrieval bundles so the team can tell whether failures came from search coverage, version selection, or answer construction.",
        "Question: Does incident INC-634 qualify for a service credit?\nRequired: current threshold, current exclusion clause, incident duration.\nRetrieved: current threshold; old exclusion; duration 47 minutes.\nDecision: unresolved; current exclusion clause missing.",
        "Retrieval adds index storage, ranking time, and context tokens. Fetching more passages can improve recall yet increase latency and distraction; measure the rate of sufficient evidence at a fixed token budget. A model's own confidence is not a substitute for verifying the required fields. Keep superseded document versions distinguishable. When content is time-sensitive, a passage without an effective date should not silently outrank a current one merely because its wording matches the question.",
        ["Do not treat a relevant excerpt as a complete answer.", "Do not merge clauses from different policy versions without stating the conflict.", "Do not blame prompt wording for a missing retrieved passage."],
        ["prompt-engineering/context-and-trust-boundaries", "prompt-engineering/schema-and-abstention"],
    ),
    lesson(
        "evidence-id-traceability",
        "Evidence IDs: make generated claims auditable against supplied records",
        "A claim is checkable only when its evidence pointer identifies the material actually supplied.", patterns_path,
        "A grounded response should carry record IDs or section keys that a validator can resolve. A generated citation-looking string is not evidence by itself. The application can build an allowed set from the retrieved bundle, reject unknown IDs, and sample whether the cited passage entails the claim. Require an explicit unsupported state for claims lacking support. In summaries, keep observation, inference, and recommendation separate so a log event is not presented as proof of a root cause. Evidence IDs can be internal references without publishing external links.",
        "A fraud analyst reviews 72 transaction events. The model states that a payout was reversed and cites event EVT-891; the event actually records only a reversal request. A verifier catches the mismatch between event type and claim, so the final report says reversal pending. The workflow rejects a second claim citing EVT-999 because that ID was not in the supplied batch. It accepts a factual statement about the request timestamp when the cited event contains the exact time. The team measures unsupported-claim rate, not the count of citation markers printed.",
        "Allowed evidence IDs: EVT-876, EVT-891, EVT-913.\nClaim: reversal completed; evidence EVT-891.\nEVT-891 type: reversal_requested.\nResult: reject claim; record pending state instead.",
        "ID lookup can be O(1) average with a set, while checking whether an excerpt actually supports a claim requires stronger logic or reviewer time. Track both missing IDs and false support. A requirement to cite every sentence can bloat answers without improving truth; cite material claims and preserve a compact mapping. Do not expose private raw records in the final response merely to prove the IDs exist. The evidence trail should be available to authorized reviewers separately from the public text.",
        ["Do not accept a citation-shaped token without resolving it.", "Do not turn a request event into a completed action.", "Do not publish sensitive raw records as a substitute for an audit trail."],
        ["prompt-engineering/retrieval-evidence-selection", "prompt-engineering/evaluate-and-revise"],
    ),
    lesson(
        "long-context-priority-and-truncation",
        "Long context: make inclusion and truncation testable",
        "A large context window does not guarantee every included fact is used correctly.", patterns_path,
        "Long prompts need an explicit budget for instructions, evidence, examples, and output. Truncation is a data-loss decision, not a harmless formatting change. Select passages by relevance, freshness, and required fields before packing them, then record what was omitted. Stable identifiers help test whether the answer used the right span. Position effects vary by model and task, so evaluate facts placed early, in the middle, and near the end instead of assuming one fixed ordering rule. A summarization chunk should retain the uncertainty and source IDs that later stages need.",
        "A procurement assistant compares a 190-page vendor agreement with a renewal notice. A naive prompt appends the full agreement, then the notice, and silently drops the middle clauses when a token limit is hit. The revised workflow extracts the termination, price-adjustment, and notice-period sections with page IDs, plus neighboring definitions. Its manifest records omitted sections and the total token count. A test set asks about terms located at different positions in the original document. If the relevant clause was not included, the assistant reports that the packet is insufficient instead of filling the gap from memory.",
        "Budget: instructions 900 tokens; evidence 6,400; examples 700; output 900.\nRequired spans: termination, price adjustment, notice period, definitions.\nManifest: document version, page IDs, omitted sections, token count.\nFailure: required span missing -> abstain or retrieve again.",
        "Token counting and passage selection add preprocessing cost, but uncontrolled overfill can waste the entire model call. For N candidate passages, a simple relevance sort is O(N log N); more elaborate reranking adds model or search expense. Measure answer accuracy by passage position and by omitted-field class. Summaries can compress context, but a lossy summary may remove the exact qualifier that decides a contract question. Reserve output capacity so the model is not cut off mid-answer.",
        ["Do not assume a long window guarantees complete recall.", "Do not let truncation silently discard a required clause.", "Do not summarize away version, scope, or uncertainty markers."],
        ["prompt-engineering/retrieval-evidence-selection", "prompt-engineering/evidence-id-traceability"],
    ),
    lesson(
        "structured-document-extraction",
        "Document extraction: separate observed fields from inferred values",
        "Extraction maps evidence into fields; it should not repair missing source data by imagination.", patterns_path,
        "A document extractor needs a schema, field-level evidence positions, and explicit null handling. OCR or parsing can confuse a character, merge table rows, or miss a page. The prompt should distinguish an observed value from an inferred one and avoid computing a total from uncertain components. A downstream validator checks type, cross-field constraints, and whether the source span exists. Some fields can be parsed deterministically; use a model for layout variation and ambiguous language where those rules fail. Keep the original document in a controlled store for review.",
        "An accounts-payable service receives 118 invoices. Each result contains invoice_id, supplier_id, currency, subtotal, tax, total, and page-region keys. On one scanned invoice the tax digits are blurred. The model returns tax as unknown with a page region rather than guessing a value from the total. A validator confirms subtotal plus tax equals total only when all three numbers are observed. Duplicate invoice IDs with different suppliers enter review, not automatic payment. The team samples low-confidence scans and measures field-level error rates separately from full-document success.",
        "invoice_id: INV-4271\nsupplier_id: SUP-82\nsubtotal: 684.00 observed on page 2\ntax: unknown; blurred region page 2, box 17\ntotal: 718.20 observed on page 2\naction: review; no computed tax substituted for observation",
        "Extraction cost scales with document count and page length; OCR and model calls can dominate latency. A field-level review queue concentrates human effort on ambiguous values instead of rereading every clean document. Full-document accuracy can be much lower than per-field accuracy when many fields are required, so report both. Do not use a passing arithmetic check as proof the underlying invoice is legitimate. The payment effect belongs behind supplier, duplicate, and authorization checks outside the prompt.",
        ["Do not present an inferred number as an observed field.", "Do not use a valid sum as proof the invoice is authentic.", "Do not omit field-level evidence positions for ambiguous scans."],
        ["prompt-engineering/schema-and-abstention", "prompt-engineering/evidence-id-traceability"],
    ),
    lesson(
        "tool-call-authorization-contract",
        "Tool calls: validate intent and arguments before an external effect",
        "A model can propose a tool call; the application decides whether it may execute.", patterns_path,
        "A tool schema constrains argument shape, but it does not grant authority. The executor must check the signed-in user's permission, resource ownership, allowed operation, idempotency key, and expected side effect. Separate read tools from write tools and use confirmation where the action's risk calls for it. Tool results are lower-trust data on return, even if they came from an authorized API. A prompt can tell the model to ask for a tool only when needed, but enforcement must live outside the prompt in application code.",
        "A billing assistant may read invoice INV-2837 and suggest a refund. The customer says to reverse the charge, but the active agent identity has only read permission. The model proposes issue_refund with invoice_id and amount. The executor rejects the call before sending it because the user lacks refund authority. For an authorized finance operator, it also verifies the invoice belongs to the intended account, the amount is within the remaining refundable balance, and an idempotency key is present. A tool result that says approved cannot override the local authorization check.",
        "Proposed action: issue_refund(invoice_id=INV-2837, amount=47.00).\nExecutor checks: actor role, account match, refundable balance, idempotency key.\nRead-only actor: deny without sending the action.\nAuthorized actor: execute once; record receipt and reconcile outcome.",
        "Authorization checks add a database or policy lookup per proposed effect, but the cost is bounded and necessary. Retries need a stable idempotency key or an uncertain network response can create duplicate effects. Log the decision and receipt without exposing payment secrets. Measure rejected unauthorized calls, duplicate attempts, and requests needing human review. A model's explanation of why a call is allowed is useful context for an operator, never a replacement for the executor's policy decision.",
        ["Do not mistake a valid tool schema for permission.", "Do not retry an uncertain write with a new effect identity.", "Do not let a tool result rewrite the user's authority."],
        ["prompt-engineering/context-and-trust-boundaries", "prompt-engineering/task-decomposition-and-handoffs"],
    ),
    lesson(
        "tool-loop-stop-rules",
        "Tool loops: set budgets, state checks, and a stopping condition",
        "An agent loop needs a finish condition independent of the model's urge to keep searching.", patterns_path,
        "Repeated tool use can amplify a bad query, spend budget, or change state twice. Define maximum calls, elapsed time, data volume, and allowed tool sequence before execution. The loop should stop when the requested acceptance check is satisfied, when evidence is insufficient, or when a guardrail fails. Store a compact state record between calls: unresolved question, evidence IDs, completed effects, and remaining budget. The model should not be asked to remember whether it already wrote to an external system. Let the executor track that fact.",
        "An asset-inventory assistant must locate the owner of server AS-914. It may query the inventory service twice and the on-call directory once. After the first query returns a stale owner and the second returns a current ownership record, it verifies the timestamp and stops. If the records conflict, it reports the conflict and routes to a human instead of making another 40 similar calls. A separate update-owner tool is outside this workflow. The trace records which calls ran and why the final answer used the current record.",
        "Goal: current owner of AS-914.\nBudget: 2 inventory reads, 1 directory read, 8 seconds.\nStop: current signed ownership record found; or conflict; or budget exhausted.\nState: call IDs, evidence versions, unresolved reason, no write effects.",
        "A call budget bounds direct tool expense at O(K) for K allowed calls, though returned data can still raise token cost. Too small a budget can create false abstentions; too large a budget can hide a retrieval defect behind repeated searches. Evaluate completion, abandonment, and cost per resolved case. Caching a verified result may reduce repeat reads, but it needs an expiry tied to the underlying record's freshness. Stop rules should be tested with missing, contradictory, and circular tool responses.",
        ["Do not let the model decide its own unlimited tool budget.", "Do not use repeated search as a substitute for reporting a conflict.", "Do not keep effect history only in model context."],
        ["prompt-engineering/tool-call-authorization-contract", "prompt-engineering/task-decomposition-and-handoffs"],
    ),
    lesson(
        "conversation-memory-boundary",
        "Conversation memory: retain decisions without retaining every private detail",
        "A long conversation is not a reliable database for task state or authorization.", patterns_path,
        "Conversation memory should keep durable preferences and unresolved task state that are relevant to future turns, with provenance and expiry. It should not silently elevate a past instruction above a new user request, or carry private records into unrelated tasks. Summaries can omit qualifiers and change meaning, so verify material commitments against the original turn or a structured state store before acting. Keep external effects, approval receipts, and object IDs in application state rather than relying on model recollection. A user correction should update the active task and invalidate conflicting summaries.",
        "A customer-support assistant handled three claims for the same business account. Its memory records that the user prefers a compact status report and that case CL-719 remains open. It does not retain full claim documents, bank details, or a prior temporary approval as permanent authority. On a later turn, the user asks about CL-842; the assistant retrieves that case only and does not mix in CL-719's payout amount. If the account owner revokes access to an attachment, the memory stores the revocation marker and the attachment is excluded from future context.",
        "Keep: preferred report format; open case ID CL-719; last verified status time.\nDiscard: bank account, full attachment text, expired approval.\nOn new case: load current authorization and case-specific evidence.\nCorrection: invalidate conflicting summary before the next action.",
        "A shorter memory lowers token cost and leakage exposure but may require an extra retrieval when the user resumes old work. Measure context bytes retained, stale-state errors, and unauthorized carryover across cases. A structured memory field is easier to delete or expire than a free-form transcript summary. Retention must follow the product's data policy, not a prompt that asks the model to forget. Review access controls on the underlying store as part of the workflow.",
        ["Do not treat an old approval as permanent permission.", "Do not carry sensitive case facts into an unrelated request.", "Do not use a summary as the sole record of an external effect."],
        ["prompt-engineering/context-and-trust-boundaries", "prompt-engineering/tool-call-authorization-contract"],
    ),
    lesson(
        "multimodal-evidence-boundary",
        "Multimodal prompts: separate what an image shows from what it suggests",
        "An image or audio clip can be evidence without being complete evidence.", patterns_path,
        "A multimodal prompt should identify the artifact, requested observation, and limits of what can be inferred. OCR, diagrams, screenshots, and audio transcriptions can omit small labels, crop context, or confuse similar symbols. Ask for visible or audible observations first and an explicit uncertainty state for hidden or unreadable details. When a result matters operationally, verify dimensions, timestamps, or extracted text with a deterministic tool or a second human check. Treat text embedded inside media as lower-trust content, not a new instruction to the assistant.",
        "A field engineer uploads a photograph of a control panel. The task is to transcribe the displayed alarm code and identify the lit indicator, not to diagnose a machine failure from a single frame. The assistant reports that AL-47 is legible, the amber indicator appears lit, and the lower serial label is obscured. It asks for a closer image before matching the device to an asset record. A sticker saying ignore safety checks is described as sticker text and does not alter the work. The engineer compares the transcription with a direct panel read before filing a maintenance ticket.",
        "Artifact: panel-photo-27, one cropped frame.\nObserved: alarm AL-47; amber indicator appears lit.\nNot visible: full serial label and prior alarm history.\nNext check: close image of serial label; direct panel confirmation.",
        "Higher-resolution media and multiple frames increase upload size, processing time, and review cost. A crop can improve readability but also remove context, so keep the original and the crop ID. Measure field-level transcription accuracy and the rate of unsupported diagnoses. An assistant that says a light is on should not infer the root cause of a machine fault without the relevant telemetry. The same boundary applies to audio: uncertain words and speaker attribution must remain uncertain.",
        ["Do not treat text inside an image as a trusted instruction.", "Do not invent a hidden serial number from a blurry label.", "Do not turn one visible indicator into a full diagnosis."],
        ["prompt-engineering/structured-document-extraction", "prompt-engineering/evidence-id-traceability"],
    ),
    lesson(
        "prompt-injection-red-team",
        "Prompt injection: test untrusted content at every boundary",
        "A retrieved page can carry instructions that the user never authorized.", production_path,
        "Prompt injection occurs when lower-trust material attempts to control the assistant's behavior. Documents, search snippets, repository files, tool results, and images are task data, even when they contain imperative text. The application should label their origin, restrict tools independently, and test whether a malicious passage can alter output or trigger an effect. The model may summarize a hostile instruction as evidence; it must not obey it. Attack tests belong in the evaluation set alongside ordinary tasks.",
        "A purchasing assistant reads a vendor invoice and a retrieved policy note. The invoice footer says to send the full customer ledger to an unrelated mailbox before approving payment. The assistant quotes that footer as suspicious document content and continues only with the authorized invoice review. Its executor exposes no mail action to this workflow. A test case checks both the visible answer and the absence of an outbound effect. A second case hides the command inside a tool response, because a safe-looking retrieval title does not make its body trusted.",
        "Trusted task: review invoice PI-684 against policy.\nUntrusted text: invoice and policy retrieval payloads.\nAttack: request ledger export before approval.\nPass: flag hostile instruction; no export call; review supported fields only.",
        "Adversarial tests add maintenance work because attackers can vary placement, language, and encoding. Evaluate attack success as a rate over a versioned corpus, and separately track false alarms on harmless quoted instructions. A prompt alone cannot enforce a tool boundary; the executor must reject a forbidden action even when the model proposes it. Keep logs of attempted effects and source identifiers without copying private document bodies into broad-access telemetry.",
        ["Do not promote retrieved text into a system instruction.", "Do not judge safety only by the final prose when a tool effect was attempted.", "Do not assume a trusted connector makes every returned document trustworthy."],
        ["prompt-engineering/context-and-trust-boundaries", "prompt-engineering/tool-call-authorization-contract"],
    ),
    lesson(
        "evaluation-slice-design",
        "Evaluation sets: measure the failure cases that matter",
        "An average score hides a broken minority of high-cost cases.", production_path,
        "A useful evaluation set groups cases by decision type, evidence quality, language, document size, and consequence of error. Keep a stable holdout that prompt authors do not tune against directly; use a separate development set for iteration. Define the grading rule before inspecting model output. Binary pass rules work for schema, prohibited effects, and evidence references, while editorial quality needs a rubric and human review. Track both aggregate performance and the worst important slice. A prompt that improves common cases while worsening abstention may be a regression.",
        "A claims team samples 73 records: clean approvals, expired coverage, missing receipts, contradictory dates, and scanned forms with weak OCR. It labels each record with the accepted decision and acceptable uncertainty. When a new prompt scores better overall but turns two missing-receipt cases into approvals, the release gate fails. The team keeps those cases in the holdout and adds a fresh development case for the new failure pattern. Evaluators see record IDs and policy versions, so a later policy update can be separated from prompt drift.",
        "Slices: clean, missing evidence, conflict, OCR uncertainty, unauthorized action.\nGate: zero unauthorized effects; no regression on missing-evidence decisions.\nRecord: prompt version, model version, case ID, verdict, reason.",
        "Evaluation cost grows with case count and repeated model runs. If N cases are each run R times, model calls are O(NR); judge calls add another multiplier. Sample where uncertainty is high, but retain a fixed core for comparison. Report confidence intervals or raw counts when slices are small, and avoid claiming that a change from one error to zero proves general reliability. A human adjudication queue should capture disagreements rather than silently changing expected labels.",
        ["Do not tune directly on the final holdout.", "Do not let a high average conceal a critical slice failure.", "Do not score a changed policy as if only the prompt changed."],
        ["prompt-engineering/evaluate-and-revise", "prompt-engineering/judge-calibration-and-order-bias"],
    ),
    lesson(
        "judge-calibration-and-order-bias",
        "Model judges: calibrate rubrics and swap candidate order",
        "A model judge is another fallible component, not an objective oracle.", production_path,
        "For subjective comparisons, give the judge a narrow rubric with observable criteria and allow a tie. Hide candidate identity and irrelevant formatting cues. Swap candidate order on a subset; a verdict that changes with order needs human review. Compare judge decisions with a labeled calibration set and monitor agreement by failure class, not only one overall number. Keep deterministic checks outside the judge: a JSON parser can verify syntax and a source lookup can verify cited IDs more reliably than a prose grade.",
        "Two incident summaries cover the same outage. Candidate A is shorter but omits the rollback time; candidate B includes it and has a less polished opening. A rubric prioritizes factual coverage, unsupported claims, and actionability. The judge evaluates both orders and is asked to cite the missing field, not award points for tone alone. If it prefers A in one order and B in the other, a reviewer adjudicates. The team records disagreement as a judge defect rather than treating whichever result ran last as truth.",
        "Rubric: factual coverage, unsupported claim count, required action status.\nCandidates: anonymized A and B.\nRun: A/B and B/A on calibration cases.\nEscalate: order reversal, uncertain evidence, or critical omission.",
        "Double judging roughly doubles evaluation calls for swapped cases, and human review adds labor. That cost is justified for release decisions, not every low-risk response. Track order-flip rate, agreement with human labels, and the fraction sent to review. A judge prompt should not receive the answer key or the identity of the prompt variant it is expected to favor. When a rubric changes, recalibrate before comparing scores across versions.",
        ["Do not ask one judge call to certify its own reliability.", "Do not confuse fluent wording with factual completeness.", "Do not compare scores from different rubrics as one time series."],
        ["prompt-engineering/evaluation-slice-design", "prompt-engineering/evidence-id-traceability"],
    ),
    lesson(
        "prompt-version-rollout",
        "Prompt releases: version the whole decision path and keep a rollback",
        "The prompt text is only one part of the behavior users see.", production_path,
        "A release record should bind prompt revision, model setting, schema, examples, retrieval configuration, tools, and evaluation result. Change one major factor at a time where possible. Send a small, representative share of eligible traffic to a candidate, compare it with the current version, and stop on a predefined regression. A rollback must restore compatible schemas and tool permissions, not only old prose. Record whether an output was produced before or after a policy update so support staff can explain different decisions.",
        "A service desk changes the response contract for ticket triage. Version PE-28 introduces an explicit unknown status and a new retrieval filter. The canary receives 7% of routine tickets; urgent security tickets remain on the established route until the failure gates pass. The team watches parser failures, unsupported citations, review referrals, and median and tail latency. A spike in parser failures triggers a rollback to PE-27 with its matching schema and retriever settings. Operators can replay a stored, redacted ticket against either version.",
        "Release bundle PE-28: prompt hash, model setting, schema v4, retriever filter v6.\nCanary: 7% eligible routine tickets.\nStop: parser or critical-decision gate fails.\nRollback: restore full PE-27 bundle and record affected request IDs.",
        "Canary routing and dual evaluation add operational cost and require enough traffic to see rare failures. If a dependency changes during the test, the comparison may no longer isolate the prompt. A short replay set catches obvious regressions before live traffic, while live telemetry reveals distribution shifts. Keep version IDs in logs and outputs so an incident can be traced without storing complete private prompts indefinitely.",
        ["Do not version only the prompt while schemas and retrieval change.", "Do not run a canary without a stop rule.", "Do not claim rollback succeeded until output and effects are checked."],
        ["prompt-engineering/evaluation-slice-design", "prompt-engineering/cost-latency-quality-budget"],
    ),
    lesson(
        "cost-latency-quality-budget",
        "Prompt budgets: trade output quality against cost and tail latency",
        "More context and more calls are not free quality improvements.", production_path,
        "Estimate cost per request from input tokens, output tokens, retrieval work, tool calls, and retries. Measure tail latency as well as median latency because sequential model calls can make a small fraction of requests painfully slow. Set a quality floor first, then compare shorter context, fewer examples, caching, and staged routing against that floor. Use a cheaper route for simple, verified tasks only when its error rate is acceptable for the same slice. A budget should state what happens when it is exhausted: partial evidence, abstention, or human handoff.",
        "A catalog team processes 1,800 product-change requests each day. A four-call chain produces marginally better wording than a two-call path, but the extra stage rarely changes the approval decision. The team removes that stage after a held-out evaluation confirms the same factual pass rate. It retains the extra verification call for high-value changes with contradictory source records. The dashboard separates token spend, retrieval time, P95 latency, review rate, and critical errors rather than reducing the outcome to one cost-per-request figure.",
        "Budget: 2 model calls for ordinary catalog changes; 1 extra check for conflicts.\nQuality floor: no unsupported approval; required fields present.\nExhausted budget: report unresolved fields and route to review.",
        "For N requests, K model calls per request make direct call volume O(NK); token length determines much of the bill and processing time. Caching repeated static context can help when the input remains stable, but stale policy text is worse than a cache miss. Compare total cost per accepted case, not cost per raw response, because cheap outputs that require human repair may be expensive overall. Segment by task difficulty so easy cases do not mask expensive failures.",
        ["Do not optimize cost before defining a quality floor.", "Do not report only average latency.", "Do not cache policy text without an invalidation rule."],
        ["prompt-engineering/task-decomposition-and-handoffs", "prompt-engineering/prompt-version-rollout"],
    ),
    lesson(
        "privacy-and-data-minimization",
        "Prompt privacy: send only the fields needed for the task",
        "A small prompt can be safer and cheaper when it excludes unrelated private data.", production_path,
        "Minimize sensitive fields before assembling model context. Replace names and identifiers with scoped tokens when the decision does not require identity; keep the mapping in controlled application storage. Apply access checks before retrieval, mask secrets in logs, and set retention according to the data policy. The prompt can request discretion, but deletion and access control must be enforced by the surrounding system. Redaction should preserve the relationship needed for the task while preventing an unauthorized output from reconstructing a private record.",
        "A support assistant reviews whether 29 billing adjustments meet a published rule. It receives case tokens, dates, amounts, and the relevant rule; it does not receive bank account numbers or the full customer profile. The application keeps a temporary mapping from case token to internal record so an authorized reviewer can act later. A test checks that generated summaries include no bank digits and that a tool result cannot pull a different account into context. If an adjustment needs identity verification, the workflow pauses for a separate authorized step rather than expanding every prompt by default.",
        "Allowed: case token, adjustment date, amount, policy clause.\nExcluded: bank account, address, unrelated tickets.\nOutput: decision plus cited fields; no personal identifier.\nRetention: follow the product's configured policy, outside the prompt.",
        "A smaller context reduces token use and exposure, though tokenization and access checks add application work. For N records, filtering is typically O(N) before prompt assembly; retrieval indexes can limit the set earlier. Measure private-field leakage in test outputs and logs, including error traces. Over-redaction can break matching, so test that the remaining fields still permit the intended decision. Do not promise that a model will forget data just because a prompt asks it to.",
        ["Do not put secrets into a prompt and ask the model to ignore them.", "Do not log full private inputs for convenience.", "Do not remove a field required for a decision without an uncertainty path."],
        ["prompt-engineering/conversation-memory-boundary", "prompt-engineering/context-and-trust-boundaries"],
    ),
    lesson(
        "multilingual-equivalence-check",
        "Multilingual prompts: test policy meaning across languages",
        "A translated instruction can change the decision boundary.", production_path,
        "A multilingual workflow needs locale-specific inputs, policy text, examples, and evaluation cases. Translation alone does not prove equivalent behavior. Keep invariant business rules in structured fields and test the response in each supported language, including uncertainty and refusal states. Ask for the original evidence ID when summarizing a translated source. If the source language is uncertain or a key legal term has no agreed translation, report the ambiguity and send it for review instead of assuming an English interpretation fits every locale.",
        "A benefits team receives claims in Hindi and English under one plan rule: dependent eligibility ends after the recorded cutoff date. The structured cutoff field is shared; each locale has reviewed wording and independent test cases. One Hindi example includes a date expressed in a local format, so the ingestion layer normalizes it before the model reasons about coverage. The team compares the decision and cited evidence, not just the fluency of the explanation. If the document's relationship term is ambiguous, both routes return needs-review.",
        "Invariant fields: plan ID, cutoff date, relationship code.\nLocale inputs: reviewed terms and date parsing.\nEvaluate: approved, denied, unknown in each supported language.\nPass: same case facts produce the same decision and evidence IDs.",
        "Each supported locale adds review and evaluation cost; N cases across L locales require at least O(NL) decisions for a full matrix. Prioritize high-volume and high-consequence slices, then add adversarial paraphrases for known ambiguities. Track decision parity separately from grammatical quality. A model may write polished text in a language while applying the wrong rule, so human reviewers with domain fluency should inspect disputed cases.",
        ["Do not use fluent translation as proof of decision parity.", "Do not compare dates before normalizing their formats.", "Do not silently resolve an ambiguous relationship term."],
        ["prompt-engineering/input-normalization-contract", "prompt-engineering/evaluation-slice-design"],
    ),
]


def link(path):
    target = by_path.get(path)
    if target is None:
        target = next((entry for entry in pending if entry["path"] == path), None)
    if target is None:
        raise ValueError(f"Unknown internal target: {path}")
    return f'<a href="/{html.escape(path)}">{html.escape(target["title"])}</a>'


def links(paths):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(paths)) + "</ul>"


def related_rows(paths):
    return [{"path": path, "title": (by_path.get(path) or next(entry for entry in pending if entry["path"] == path))["title"]}
            for path in dict.fromkeys(paths)]


def record(template, path, title, summary, body, sort_order, *, kind=None,
           subject=None, section=None, difficulty=None, related=None):
    entry = copy.deepcopy(template)
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)),
                 path=path, title=title, summary=summary, body=body,
                 sort_order=sort_order, published_at=stamp, created_at=stamp,
                 updated_at=stamp, status="published", category="AI & Data",
                 subject=subject or "prompt-engineering", difficulty=difficulty)
    entry["tags"] = ["prompt engineering", kind or "tutorial"]
    entry["data"]["subject_root"] = root_path
    entry["data"]["section_path"] = section or root_path
    entry["data"]["content_format"] = "html"
    entry["data"]["seo_ready"] = True
    if kind:
        entry["data"]["kind"] = kind
        entry["data"]["author_path"] = "authors/aitrove-editorial"
        entry["data"]["reading_minutes"] = 8 if kind == "tutorial" else 12
        entry["data"]["related"] = related_rows(related or [])
    return entry


pending = []
root_entry = by_path[root_path]
tabs = [
    {"title": "Prompt Engineering", "path": root_path},
    {"title": "Patterns", "path": patterns_path},
    {"title": "Production", "path": production_path},
    {"title": "Projects", "path": projects_path},
    {"title": "Quizzes", "path": quizzes_path},
]
hub_titles = {
    patterns_path: ("Prompt patterns", "Retrieval, structured extraction, tools, memory, and media boundaries."),
    production_path: ("Production prompt engineering", "Release tests, adversarial inputs, cost, privacy, and language parity."),
    projects_path: ("Prompt engineering projects", "Build and inspect complete decision workflows."),
    quizzes_path: ("Prompt engineering quizzes", "Test design and production decisions against concrete cases."),
}

# Reserve titles before rendering links so cross-section links resolve in one pass.
for path, (title, summary) in hub_titles.items():
    pending.append({"path": path, "title": title, "summary": summary})
for spec in specs:
    pending.append({"path": spec["path"], "title": spec["title"], "summary": spec["summary"]})
pending += [
    {"path": project_paths[0], "title": "Project: evaluate an incident handoff prompt"},
    {"path": project_paths[1], "title": "Project: defend a retrieval and action workflow"},
    {"path": quiz_paths[0], "title": "Prompt design decisions"},
    {"path": quiz_paths[1], "title": "Prompt production decisions"},
]

root_entry["data"]["resource_tabs"] = tabs
root_entry["data"]["modules"].append({
    "title": "Contracts, examples, and verifiable outputs",
    "summary": "Define success, normalize input, choose cases, preserve uncertainty, and validate handoffs.",
    "lessons": [spec["path"] for spec in specs if spec["section"] == root_path],
})
root_entry["body"] += (
    "<h2>Choose the next decision</h2>"
    "<p>Build from the existing task, trust, and evaluation lessons. Then make the inputs, output contract, and handoff checks explicit before extending the workflow. A prompt is useful only when the result can be inspected against its evidence and intended effect.</p>"
    + links([spec["path"] for spec in specs if spec["section"] == root_path])
    + "<h2>Continue through the curriculum</h2>"
    + "<p>Patterns cover retrieved evidence and tool use. Production covers release gates and failure monitoring. Projects combine the boundaries into reviewable work; quizzes test the decisions that fail most often.</p>"
    + links([patterns_path, production_path, projects_path, quizzes_path])
)
root_entry["updated_at"] = stamp

for index, (path, (title, summary)) in enumerate(hub_titles.items(), start=1):
    if path == patterns_path:
        member_paths = [spec["path"] for spec in specs if spec["section"] == patterns_path]
    elif path == production_path:
        member_paths = [spec["path"] for spec in specs if spec["section"] == production_path]
    elif path == projects_path:
        member_paths = project_paths
    else:
        member_paths = quiz_paths
    subject = "prompt-engineering-project" if path == projects_path else "prompt-engineering-" + path.rsplit("/", 1)[1]
    hub_body = (
        f"<p>{html.escape(summary)} Start with the decision you need to make, then use the linked material to build a checkable result.</p>"
        "<h2>Learning path</h2>" + links(member_paths)
        + "<h2>Connect the path</h2>"
        + "<p>The foundations define the task and trust boundary. Later modules test whether a result should be used, revised, or sent to a person.</p>"
        + links([root_path] + [other for other in hub_titles if other != path])
    )
    hub = record(root_entry, path, title, summary, hub_body, 26 + index,
                 subject=subject, section=path)
    hub["type"] = "subject"
    hub["data"] = {
        "subject_root": root_path, "section_path": path, "content_format": "html",
        "seo_ready": True, "resource_tabs": tabs,
        "modules": [{"title": title, "summary": summary, "lessons": member_paths}],
    }
    pending.append(hub)

for index, spec in enumerate(specs, start=1):
    neighbors = [other["path"] for other in specs if other["section"] == spec["section"]]
    neighbor_index = neighbors.index(spec["path"])
    adjacent = [neighbors[neighbor_index - 1]] if neighbor_index else []
    adjacent += [neighbors[neighbor_index + 1]] if neighbor_index + 1 < len(neighbors) else []
    connected = list(dict.fromkeys(
        [root_path, spec["section"]] + spec["related"] + adjacent
        + [project_paths[0] if spec["section"] == root_path else project_paths[1],
           quiz_paths[0] if spec["section"] != production_path else quiz_paths[1]]
    ))
    connected = [path for path in connected if path != spec["path"]]
    body = (
        f"<p>{html.escape(spec['definition'])}</p>"
        "<h2>Decision in practice</h2>"
        f"<p>{html.escape(spec['decision'])}</p>"
        f'<pre><code class="language-{spec["language"]}">{html.escape(spec["sample"])}</code></pre>'
        "<h2>Performance and operating cost</h2>"
        f"<p>{html.escape(spec['cost'])}</p>"
        "<h3>Common Mistakes</h3>"
        "<ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in spec["mistakes"]) + "</ul>"
        "<h2>Connected lessons</h2>" + links(connected)
    )
    article = record(by_path["prompt-engineering/task-contract"], spec["path"],
                     spec["title"], spec["summary"], body, 25503 + index,
                     kind="tutorial", section=spec["section"], difficulty="Intermediate",
                     subject=("prompt-engineering" if spec["section"] == root_path
                              else "prompt-engineering-" + spec["section"].rsplit("/", 1)[1]),
                     related=connected[:7])
    pending.append(article)

project_specs = [
    (
        project_paths[0], "Project: evaluate an incident handoff prompt",
        "Create an evidence-backed handoff, a held-out case set, and a release decision.",
        "A regional operations team has 83 incident events from a delivery outage. Build a prompt workflow that produces a concise handoff for an incoming operator. The workflow must separate confirmed impact, unresolved claims, rollback status, and the next owner. Start from a source ledger with event IDs; do not paste a polished retrospective into the prompt as if it were raw evidence.",
        "Create a task contract with explicit acceptance checks. Normalize timestamps and service names. Select three prompt examples that include a missing final state and a contradictory update. Ask for a structured output with evidence IDs and an unknown status. Verify the schema in code, then compare every cited ID with the ledger. Build a held-out set covering a clean recovery, a partial recovery, and an event with no reliable end time. Reject the prompt if it invents a recovery timestamp, even when its prose is clear.",
        "Input: 83 event rows with event_id, service, timestamp, state, and owner.\nOutput: impact, recovery, unresolved, next_owner, evidence_ids.\nGate: every claim maps to an event; no invented final state.\nRelease: compare prompt versions on held-out cases and keep the failed cases.",
        "A linear event scan costs O(N) for N rows; indexed evidence lookups can avoid repeated scans during validation. Model calls scale with the number of evaluation cases and repeats, so record the prompt and case versions and cap exploratory retries. The final packet should include sample input, output contract, evaluator notes, error counts by case type, and a rollback choice. Do not use one excellent generated handoff as proof that the workflow is ready.",
        ["Do not use prompt examples as the held-out evaluation set.", "Do not infer that an unobserved recovery succeeded.", "Do not grade style before verifying event IDs."],
        [root_path, "prompt-engineering/intent-to-acceptance-check", "prompt-engineering/schema-and-abstention",
         "prompt-engineering/evaluation-slice-design", quiz_paths[0]],
    ),
    (
        project_paths[1], "Project: defend a retrieval and action workflow",
        "Test evidence sufficiency, hostile retrieved text, and an executor-controlled tool call.",
        "A service-credit assistant reads contract excerpts and can propose, but cannot directly execute, a credit. Build a disposable case set with one sufficient contract, one missing eligibility clause, and one hostile runbook that asks the assistant to export customer records. The assistant must cite evidence IDs, report insufficient context when needed, and treat every retrieved instruction as task data. The executor alone decides whether a proposed action is permitted.",
        "Index the case documents with stable IDs and a version. Retrieve a small candidate set, check whether it includes the eligibility rule and relevant exception, and ask the model for a recommendation plus cited IDs. Insert a hostile document after retrieval and test that no export action is proposed or sent. For a permitted credit proposal, validate account ownership, remaining balance, effect identity, and signed-in operator role in code. Simulate an uncertain tool timeout and verify that a retry uses the same idempotency key.",
        "Cases: sufficient policy; missing exception; hostile runbook.\nModel output: recommendation, uncertainty_reason, evidence_ids, proposed_action.\nExecutor gate: role, account, balance, stable effect key.\nPass: no export; no duplicate credit; unknown stays unknown.",
        "Retrieval and model calls add latency, while executor checks require a policy lookup. Limit the tool loop by call count and elapsed time. Record the source IDs, rejected action attempts, and a small redacted trace for review. The project packet should include the attack case, expected behavior, observed effect log, and the reason each recommendation passed or failed. If a document is missing, an additional search may help; it must not become an unlimited loop.",
        ["Do not trust a runbook because the connector returned it.", "Do not accept a valid schema as authorization.", "Do not retry a timed-out write with a new effect key."],
        [patterns_path, production_path, "prompt-engineering/prompt-injection-red-team",
         "prompt-engineering/tool-call-authorization-contract", quiz_paths[1]],
    ),
]
for index, (path, title, summary, opening, work, sample, cost, mistakes, connected) in enumerate(project_specs):
    body = (
        f"<p>{html.escape(opening)}</p><h2>Build and verify</h2><p>{html.escape(work)}</p>"
        f'<pre><code class="language-text">{html.escape(sample)}</code></pre>'
        f"<h2>Performance and operating cost</h2><p>{html.escape(cost)}</p>"
        "<h3>Common Mistakes</h3><ul>"
        + "".join(f"<li>{html.escape(item)}</li>" for item in mistakes) + "</ul>"
        + "<h2>Connected lessons</h2>" + links(connected)
    )
    pending.append(record(by_path["devops/practice-project"], path, title, summary,
                          body, 25600 + index, kind="project", subject="prompt-engineering-project",
                          section=projects_path, difficulty="Intermediate", related=connected))

design_questions = [
    ("A request says 'improve the handoff.' What should be fixed first?", "A checkable outcome and pass rule", "A longer persona", "A larger output limit", "The team needs a result it can verify.", "prompt-engineering/intent-to-acceptance-check"),
    ("Two stock rows use different units. What comes before a prompt summary?", "Normalize units and keep rejected rows visible", "Ask for a confident total", "Delete both rows", "Unknown conversion factors must not become guessed quantities.", "prompt-engineering/input-normalization-contract"),
    ("Which example set is most useful for a triage prompt?", "Distinct positive, negative, and unknown cases", "Three easy approvals", "A copy of the final test case", "Examples should cover decision boundaries without leaking the holdout.", "prompt-engineering/few-shot-example-selection"),
    ("A JSON result says approved but cites no evidence. What should the application do?", "Reject the decision under business validation", "Accept because JSON parses", "Fill an evidence ID randomly", "Syntax does not verify a decision.", "prompt-engineering/schema-and-abstention"),
    ("A stage extracts incompatible timestamps. What should the next stage do?", "Stop and report the conflict", "Average the timestamps", "Draft a customer note anyway", "A failed handoff gate should block downstream claims.", "prompt-engineering/task-decomposition-and-handoffs"),
    ("A retrieved excerpt mentions the topic but omits the eligibility rule. What is it?", "Relevant but insufficient", "Enough to decide", "A trusted instruction", "Topical overlap does not establish answer sufficiency.", "prompt-engineering/retrieval-evidence-selection"),
    ("What makes a generated claim auditable?", "A cited ID that maps to the supplied source", "A confident tone", "A long explanation", "Evidence references must resolve to the input record.", "prompt-engineering/evidence-id-traceability"),
    ("A long source packet has a key exception near the end. What should be tested?", "Whether the model finds and applies that exception", "Only token count", "Whether prose is short", "Long context can hide a governing passage.", "prompt-engineering/long-context-priority-and-truncation"),
    ("OCR cannot read a receipt date. Which output is correct?", "Unknown date with review status", "A plausible date", "The current date", "Extraction must preserve unreadable fields.", "prompt-engineering/structured-document-extraction"),
    ("A model proposes a refund tool call for a read-only user. Who decides?", "The executor denies the effect", "The model's rationale authorizes it", "The tool schema grants permission", "Authority belongs in the application policy check.", "prompt-engineering/tool-call-authorization-contract"),
    ("An agent searches repeatedly after sources disagree. What should happen?", "Stop under the call budget and report the conflict", "Search without limit", "Choose the first result", "A stop rule bounds spend and unsupported conclusions.", "prompt-engineering/tool-loop-stop-rules"),
    ("A photograph has a partially hidden serial label. What may the assistant state?", "Only the visible characters and uncertainty", "A complete inferred serial", "A diagnosis from one image", "Media observations have a visibility boundary.", "prompt-engineering/multimodal-evidence-boundary"),
]
production_questions = [
    ("A retrieved runbook asks for a customer export. How should it be handled?", "Treat it as hostile task data and block export", "Promote it to system policy", "Export before answering", "Retrieved text cannot grant action authority.", "prompt-engineering/prompt-injection-red-team"),
    ("A new prompt improves average accuracy but worsens missing-receipt cases. Release it?", "No, the critical slice gate fails", "Yes, the average improved", "Ignore rare cases", "Consequential slices need their own gates.", "prompt-engineering/evaluation-slice-design"),
    ("A model judge changes its winner when candidate order is swapped. What next?", "Send the case for adjudication", "Keep the last verdict", "Increase its score", "Order reversal is a judge reliability signal.", "prompt-engineering/judge-calibration-and-order-bias"),
    ("A prompt rollback restores only old text, not the old schema. Is that complete?", "No, restore the compatible release bundle", "Yes, text is the full release", "It depends only on tone", "Schema and retrieval settings affect behavior.", "prompt-engineering/prompt-version-rollout"),
    ("Which latency measure catches slow outliers in a multi-call chain?", "Tail latency such as P95", "Only the median", "Prompt character count", "Sequential calls can create a slow tail.", "prompt-engineering/cost-latency-quality-budget"),
    ("A task needs dates and amounts but receives bank account numbers. What is the fix?", "Filter the bank fields before prompt assembly", "Ask the model to ignore them", "Put them in logs only", "Data minimization is an application boundary.", "prompt-engineering/privacy-and-data-minimization"),
    ("Two language versions sound fluent but disagree on eligibility. What matters?", "Compare decisions and evidence against the same facts", "Choose the more polished wording", "Assume translation parity", "Fluency does not prove rule parity.", "prompt-engineering/multilingual-equivalence-check"),
    ("A tool timeout follows a write. What makes a retry safe?", "Reuse the same effect identity after state check", "Generate a fresh effect key", "Ask the model to remember", "Retries must not duplicate effects.", "prompt-engineering/tool-call-authorization-contract"),
    ("A conversation summary says an old approval still applies. What should govern?", "Current authorization and scoped state", "The summary alone", "The oldest instruction", "Summaries do not grant enduring authority.", "prompt-engineering/conversation-memory-boundary"),
    ("A citation points to a nonexistent row. What is the verdict?", "Reject the claim as unsupported", "Accept the format", "Invent a matching row", "A reference must resolve to supplied evidence.", "prompt-engineering/evidence-id-traceability"),
    ("A canary prompt fails its parser gate. What should the release system do?", "Stop routing to the candidate and restore the prior bundle", "Increase traffic", "Suppress the metric", "A predefined stop rule makes rollback actionable.", "prompt-engineering/prompt-version-rollout"),
    ("A tool loop reaches its time budget without enough evidence. What output is valid?", "An explicit unresolved state", "A guessed answer", "An unbounded retry", "Budget exhaustion cannot be converted into evidence.", "prompt-engineering/tool-loop-stop-rules"),
]

for quiz_index, (path, title, bank, related) in enumerate([
    (quiz_paths[0], "Prompt design decisions", design_questions,
     [root_path, "prompt-engineering/schema-and-abstention", "prompt-engineering/retrieval-evidence-selection", project_paths[0]]),
    (quiz_paths[1], "Prompt production decisions", production_questions,
     [production_path, "prompt-engineering/prompt-injection-red-team", "prompt-engineering/evaluation-slice-design", project_paths[1]]),
]):
    questions = []
    for question_index, (prompt, correct, wrong_one, wrong_two, explanation, lesson_path) in enumerate(bank):
        choices = [correct, wrong_one, wrong_two]
        offset = question_index % 3
        questions.append({
            "prompt": prompt, "options": choices[offset:] + choices[:offset],
            "answer": (-offset) % 3,
            "explanation": explanation + " Review " + (by_path.get(lesson_path) or next(e for e in pending if e["path"] == lesson_path))["title"] + ".",
        })
    body = (
        "<p>Choose the action that respects the task, evidence, and effect boundary. Each answer includes a short reason.</p>"
        "<h2>Review the decisions</h2>"
        + links(list(dict.fromkeys([item[5] for item in bank])))
        + "<h3>Common Mistakes</h3>"
        "<ul><li>Treating readable output as a verified decision.</li>"
        "<li>Allowing untrusted context to grant an action.</li>"
        "<li>Ignoring an explicit unknown state.</li></ul>"
        "<h2>Continue practicing</h2>" + links(related)
    )
    quiz = record(by_path["quizzes/devops-operations"], path, title,
                  "Twelve applied decisions with explanations and linked lessons.",
                  body, 25700 + quiz_index, subject="prompt-engineering-quizzes",
                  section=quizzes_path)
    quiz["data"].update(author_path="authors/aitrove-editorial",
                        duration_minutes=14, related=related_rows(related),
                        questions=questions)
    pending.append(quiz)

for old_path, related in {
    "prompt-engineering/task-contract": ["prompt-engineering/intent-to-acceptance-check", "prompt-engineering/input-normalization-contract", project_paths[0]],
    "prompt-engineering/context-and-trust-boundaries": ["prompt-engineering/prompt-injection-red-team", "prompt-engineering/tool-call-authorization-contract", project_paths[1]],
    "prompt-engineering/evaluate-and-revise": ["prompt-engineering/evaluation-slice-design", "prompt-engineering/prompt-version-rollout", quiz_paths[1]],
}.items():
    entry = by_path[old_path]
    entry["body"] += "<h2>Apply this next</h2>" + links(related)
    entry["data"]["related"] = related_rows(
        [item["path"] for item in entry["data"].get("related", [])] + related
    )
    entry["updated_at"] = stamp

new_records = [entry for entry in pending if entry.get("type")]
existing_paths = {entry["path"] for entry in rows}
overlap = existing_paths.intersection(entry["path"] for entry in new_records)
if overlap:
    raise ValueError(f"New paths already exist: {sorted(overlap)}")
rows.extend(new_records)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(f"Added {len(new_records)} records: {len(specs)} lessons, 4 hubs, 2 projects, 2 quizzes")
