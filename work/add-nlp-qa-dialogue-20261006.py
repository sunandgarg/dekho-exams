"""Add answerability and dialogue-state content to NLP."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
Q = 'Question answering and evidence'
C = 'Dialogue state and handoff'
lessons = [
    {
        'path': N + 'extractive-qa-span-and-window-contract',
        'title': 'Extractive QA: answer spans, context windows and no-answer cases',
        'module': Q, 'project': False,
        'summary': 'An answer reader should return the exact source span or abstain. Long documents, repeated phrases and missing evidence make that contract harder than selecting two token positions.',
        'sections': [
            ('Define the answer object', 'Store question, source document revision, supporting passage, half-open answer offsets and an answerability label. An extractive answer must select bytes or characters from the original representation agreed by the corpus policy; token start and end are a temporary model view. A question can have several correct spans or no answer in the supplied context. Do not mark a plausible outside fact as correct when the retrieved document does not say it. [[natural-language-processing/span-offset-annotation|Span annotation]] supplies the source coordinate contract.'),
            ('Window long context deliberately', 'A reader has a bounded token budget. Split a long document into overlapping windows and keep each window’s mapping to original offsets. During training, a window without the gold answer is a no-answer window even if another window contains it. At inference, compare candidates across windows under a calibrated rule and deduplicate identical spans. A narrow stride can lose an answer at a boundary; a large overlap adds latency and correlated false positives. Save the window policy with the model bundle.'),
            ('Separate retrieval from reading', 'The reader cannot recover an answer absent from retrieved passages. Measure retrieval recall at candidate depth, answerable-case span F1 and no-answer precision separately. A strong reader score on gold passages can conceal a weak search stage. Use [[natural-language-processing/incident-runbook-search-project|runbook retrieval]] to provide permitted candidate passages and [[natural-language-processing/hybrid-ranking-and-access-filters|access filtering]] before any reader sees private text.'),
            ('Audit the hard questions', 'Include repeated numbers, two dates, negated instructions, table-like text, outdated revisions and questions requiring several passages. Exact match is strict and useful for identifiers; token overlap can diagnose near misses but cannot certify an amount or date. A source-span answer should travel with document revision and confidence. [[natural-language-processing/qa-answerability-and-calibration|Answerability calibration]] decides when to return it, while the [[natural-language-processing/runbook-question-answering-project|project]] tests the whole path.'),
        ],
        'code': '''def answer_from_source(source_text, start, end, expected=None):
    if not 0 <= start < end <= len(source_text):
        raise ValueError("answer span outside source")
    answer = source_text[start:end]
    if expected is not None and answer != expected:
        raise ValueError("answer no longer matches source revision")
    return {"answer": answer, "start": start, "end": end}

runbook = "The callback retry limit is 47 attempts."
assert answer_from_source(runbook, 28, 39, "47 attempts")["answer"] == "47 attempts"
''',
        'cost': 'Span validation is O(a) time to copy an a-character answer and O(a) output space. With w context windows, reader inference costs roughly w model passes; overlap raises both w and duplicate-candidate work. Retrieval and access checks add latency before reading begins. Measure p95 per question length and document length, plus the fraction of answerable questions whose evidence never reached the reader.',
        'mistakes': ['Scoring the reader only on passages guaranteed to contain an answer.', 'Assigning an answer to a window that does not contain its gold span.', 'Returning a plausible fact from model memory when the source is silent.', 'Dropping source revision or original offsets from the answer object.'],
        'related': [N + 'qa-answerability-and-calibration', N + 'runbook-question-answering-project', N + 'span-offset-annotation', N + 'incident-runbook-search-project', N + 'hybrid-ranking-and-access-filters'],
    },
    {
        'path': N + 'qa-answerability-and-calibration',
        'title': 'QA answerability: calibrate abstention and evidence quality',
        'module': Q, 'project': False,
        'summary': 'A high-scoring span may answer the wrong question. Compare it with a no-answer option and the quality of the retrieved evidence before replying.',
        'sections': [
            ('Distinguish three failures', 'The collection may lack the answer, retrieval may miss an existing passage, or the reader may misread a good passage. These failures require different fixes. Label answerability relative to a frozen source snapshot, and separately label whether the retrieved candidate set contains a supporting passage. A no-answer response is valid when evidence is absent; a missed retrieval is a pipeline defect. [[natural-language-processing/extractive-qa-span-and-window-contract|The span contract]] defines what a positive answer must point to.'),
            ('Calibrate the decision', 'Fit a threshold on validation questions that includes answerable and unanswerable cases. Compare the best span score with a no-answer score or other calibrated evidence feature, according to the reader design. Do not interpret a raw model logit as a probability. Report coverage, exact-answer precision, unsupported-answer rate and correctly abstained cases at several thresholds. If the cost of a wrong operational instruction is high, require stronger evidence or a human handoff.'),
            ('Check the source itself', 'A retrieved passage can mention the right terms yet not answer the question. Verify that the selected span is inside an authorized, current source revision and that the surrounding sentence supports the requested relation. “Retry limit is 47” does not answer “how many retries have already happened?” Consider contradictory passages and later corrections. The [[natural-language-processing/document-summary-evidence-contract|evidence contract]] shows why a citation-like pointer does not by itself prove entailment.'),
            ('Slice the error budget', 'Evaluate rare identifiers, ambiguous questions, multi-hop questions, obsolete runbooks and mixed-language phrasing separately. Keep questions from the same incident in one split. Review a sample of confident answers and abstentions after release to avoid learning only from complaints. If source access changes, invalidate cached answers or recheck authorization. The [[natural-language-processing/runbook-question-answering-project|runbook QA project]] applies these checks to a support workflow.'),
        ],
        'code': '''def answer_decision(best_span_score, no_answer_score, evidence_current,
                    evidence_authorized, margin=0.17):
    if not evidence_current or not evidence_authorized:
        return "abstain", "invalid-evidence"
    if best_span_score - no_answer_score < margin:
        return "abstain", "insufficient-margin"
    return "answer", "reviewed-threshold-passed"

assert answer_decision(0.69, 0.61, True, True) == (
    "abstain", "insufficient-margin"
)
''',
        'cost': 'The decision gate is O(1) time and space. Calibration requires reviewed questions and repeated scoring across candidate thresholds; that offline cost is small relative to labeling hard no-answer cases. At serving time, authorization and freshness checks may add lookup latency but cannot be skipped. Report wrong-answer cost, abstention volume and manual follow-up time with model throughput.',
        'mistakes': ['Calling a raw score a calibrated probability.', 'Treating retrieval failure as a valid unanswerable question.', 'Answering from a stale or unauthorized passage.', 'Reporting accuracy on answered questions without coverage and unsupported-answer rate.'],
        'related': [N + 'extractive-qa-span-and-window-contract', N + 'runbook-question-answering-project', N + 'document-summary-evidence-contract', N + 'classification-slices-and-abstention', N + 'hybrid-ranking-and-access-filters'],
    },
    {
        'path': N + 'runbook-question-answering-project',
        'title': 'Project: answer runbook questions with source spans and abstention',
        'module': Q, 'project': True,
        'summary': 'Build a runbook assistant that returns an authorized, current source span for a direct question and says when the available documents do not answer it.',
        'sections': [
            ('Write the response contract', 'The on-call engineer asks for a retry limit, owner or rollback condition. The response contains answer text, source title, document revision, original offsets and a current-access check. If the source does not state the answer, return a no-answer result and a search link. Do not fabricate a procedure or merge two contradictory versions into one instruction. The user must be able to inspect the evidence.'),
            ('Prepare retrieval and reader data', 'Index active runbooks under their revision and permissions. Assemble reviewed questions with exact supporting spans plus unanswerable questions, outdated-version traps and near-miss passages. Group related incidents and copied runbook sections before splitting. [[natural-language-processing/incident-runbook-search-project|Runbook search]] supplies candidate passages; [[natural-language-processing/extractive-qa-span-and-window-contract|the span reader]] validates output against original text.'),
            ('Gate both stages', 'Measure retrieval recall at the reader depth, exact-span accuracy on evidence-present questions, unsupported-answer rate, no-answer precision and authorization failures. Tune abstention on validation data; freeze thresholds for the final audit. A reader improvement that relies on feeding it gold passages does not qualify as an end-to-end gain. [[natural-language-processing/qa-answerability-and-calibration|Answerability calibration]] determines when to stop.'),
            ('Operate a changing corpus', 'Rebuild or update search indexes when runbooks change, invalidate answers tied to retired revisions and preserve rollback. Recheck document permissions for cached results. Sample confident answers for human review and collect cases where the engineer had to search manually. Keep query logs under the incident retention policy; raw questions may contain secrets. A stale answer should become unavailable even if its text still appears in an old cache.'),
        ],
        'code': '''def packaged_answer(source_text, source_revision, start, end, authorized):
    if not authorized:
        return {"state": "abstain", "reason": "access-denied"}
    if not source_revision or not 0 <= start < end <= len(source_text):
        return {"state": "abstain", "reason": "invalid-source-span"}
    return {"state": "answer", "text": source_text[start:end],
            "source_revision": source_revision, "start": start, "end": end}

source = "Retry limit: 47 attempts."
assert packaged_answer(source, "runbook-v7", 13, 24, True)["text"] == "47 attempts"
''',
        'cost': 'Packaging is O(a) time and space for an a-character answer. End-to-end latency combines index lookup, permission filtering, reader windows and source revalidation. Cache permitted results only with revision and access scope in the key. Track abstention and stale-cache prevention as first-class outcomes; lowering latency by skipping freshness checks can produce a worse operational system.',
        'mistakes': ['Returning a snippet from a retired runbook as current guidance.', 'Caching by question text alone across users with different permissions.', 'Testing the reader only with gold passages.', 'Treating a source pointer as proof the selected words answer the actual question.'],
        'related': [N + 'extractive-qa-span-and-window-contract', N + 'qa-answerability-and-calibration', N + 'incident-runbook-search-project', N + 'hybrid-ranking-and-access-filters', N + 'document-summary-evidence-contract'],
    },
    {
        'path': N + 'dialogue-state-slots-and-corrections',
        'title': 'Dialogue state: apply slot updates, corrections and deletions',
        'module': C, 'project': False,
        'summary': 'A support conversation changes state over several turns. A later correction must replace an earlier slot without erasing the evidence trail.',
        'sections': [
            ('Represent state explicitly', 'A refund conversation may track intent, order reference, requested action and confirmation status. Store each slot with value, source turn, confidence and validation state. Separate the user’s assertion from a verified account lookup. An order ID spoken earlier is not necessarily current after “Sorry, I meant ZX-82.” The state reducer needs set, clear and unchanged operations; treating every absent slot as clear would erase context on ordinary turns.'),
            ('Interpret corrections in context', 'A turn can negate an earlier choice, revise a value or refer back with “that one.” Annotate the operation and its target slot before updating state. If the referent is ambiguous, ask a clarifying question and leave the previous value unconfirmed. [[natural-language-processing/coreference-chains-and-mention-identity|Mention identity]] helps with references, while [[natural-language-processing/support-entity-extraction-project|entity extraction]] supplies candidate IDs. Neither should silently authorize a refund.'),
            ('Evaluate the whole conversation', 'Measure exact joint state at each turn, per-slot accuracy, correction success and harmful state persistence. A single early mistake can carry forward, so also score the immediate update independent of accumulated state. Split by full conversation and customer, not individual turns. Include interruptions, repeated values, mixed languages and agent handoffs. A state that looks correct at the final turn may have triggered a wrong action earlier.'),
            ('Version the handoff', 'Package ontology, slot schema, reducer policy, model and validation rules. A schema change needs a migration or a reset with clear user communication. Keep an event log of state updates and reviewer corrections under restricted access. The [[natural-language-processing/dialogue-handoff-and-action-gates|handoff lesson]] turns state into a gated action, and the [[natural-language-processing/refund-conversation-state-project|project]] tests a complete support exchange.'),
        ],
        'code': '''def apply_slot_update(state, slot_name, operation, value=None):
    next_state = dict(state)
    if operation == "unchanged":
        return next_state
    if operation == "clear":
        next_state.pop(slot_name, None)
    elif operation == "set" and value is not None:
        next_state[slot_name] = value
    else:
        raise ValueError("invalid slot update")
    return next_state

first = apply_slot_update({}, "order_id", "set", "ZX-47")
corrected = apply_slot_update(first, "order_id", "set", "ZX-82")
assert corrected["order_id"] == "ZX-82" and first["order_id"] == "ZX-47"
''',
        'cost': 'Copying a state dictionary is O(s) time and space for s slots; this is acceptable for a small support ontology and preserves previous snapshots for audit. A long-running conversation may accumulate more event records than active slots, so cap or archive history under retention rules without losing correction provenance. Model inference and clarification turns dominate user-facing latency.',
        'mistakes': ['Clearing a slot because the next turn did not mention it.', 'Keeping an old order reference after an explicit correction.', 'Treating a model-extracted value as account-verified.', 'Scoring only the final state while ignoring harmful interim decisions.'],
        'related': [N + 'dialogue-handoff-and-action-gates', N + 'refund-conversation-state-project', N + 'coreference-chains-and-mention-identity', N + 'support-entity-extraction-project', N + 'grouped-temporal-text-validation'],
    },
    {
        'path': N + 'dialogue-handoff-and-action-gates',
        'title': 'Dialogue handoff: gate actions on verified state and uncertainty',
        'module': C, 'project': False,
        'summary': 'A conversation state is a hypothesis about user intent. External actions need verified fields, authorization and an explicit confirmation boundary.',
        'sections': [
            ('Separate understanding from execution', 'The assistant may infer that a customer wants a refund, but intent classification is not permission to issue one. Mark slots as asserted, extracted, verified or disputed. Verify order ownership and refund eligibility through the authorized system, then ask for confirmation of the exact action. A high model score cannot replace the account check. [[natural-language-processing/dialogue-state-slots-and-corrections|The slot reducer]] tracks which value is current; this lesson decides whether it is actionable.'),
            ('Design a clear handoff', 'Escalation should carry a concise state snapshot, source turn IDs, open questions, verification results and why automation stopped. Do not dump an unfiltered conversation into a broad queue. If a human changes a slot, record the correction as a new event rather than overwriting history. The next model turn must see that correction or abstain; otherwise the assistant may repeat a rejected guess. Preserve the original user wording behind role-based access.'),
            ('Test the failure paths', 'Exercise account mismatch, corrected order ID, multiple orders, ambiguous pronouns, unsupported language mix, expired eligibility and interrupted confirmation. Evaluate wrong-action rate, missed useful handoff, repeated clarification loops and time to human resolution. A state tracker can score well on slots while still acting too early. [[natural-language-processing/classification-slices-and-abstention|Abstention]] and [[natural-language-processing/multilingual-calibration-and-fallback|multilingual fallback]] provide related guardrails.'),
            ('Operate with versioned policy', 'Store dialogue model, slot schema, action rules and tool permissions as one release bundle. Changes to an API authorization rule should invalidate cached verification even if the text model is unchanged. Audit every external action with the confirmed state and policy version, not raw model text alone. The [[natural-language-processing/refund-conversation-state-project|refund project]] provides an end-to-end rehearsal before enabling any live action.'),
        ],
        'code': '''def refund_action_gate(state, order_verified, eligible, confirmed):
    if state.get("intent") != "refund":
        return "handoff", "intent-not-confirmed"
    if not state.get("order_id") or not order_verified:
        return "handoff", "order-not-verified"
    if not eligible:
        return "handoff", "eligibility-unconfirmed"
    if not confirmed:
        return "ask-confirmation", "action-not-confirmed"
    return "ready-for-authorized-tool", "all-gates-passed"

assert refund_action_gate({"intent": "refund", "order_id": "ZX-82"},
                          True, True, False)[0] == "ask-confirmation"
''',
        'cost': 'This policy gate is O(1) time and space. Verification calls, human handoff and waiting for user confirmation dominate latency. Measure wrong-action prevention and resolution time, not only turn-level state accuracy. Cache verification cautiously: ownership or eligibility can change, and a stale positive response should not permit an external action.',
        'mistakes': ['Calling an external refund tool after intent detection alone.', 'Passing a handoff without source turn IDs or unresolved questions.', 'Reusing verification after the customer changes the order ID.', 'Allowing a model update to change action policy without a separate review.'],
        'related': [N + 'dialogue-state-slots-and-corrections', N + 'refund-conversation-state-project', N + 'classification-slices-and-abstention', N + 'multilingual-calibration-and-fallback', N + 'text-serving-contract'],
    },
    {
        'path': N + 'refund-conversation-state-project',
        'title': 'Project: track a refund conversation with correction-safe handoff',
        'module': C, 'project': True,
        'summary': 'Build a support conversation flow that remembers corrected order references, asks when uncertain and never issues an action without verification and confirmation.',
        'sections': [
            ('Define the conversation', 'A customer asks about a refund, first names order ZX-47, then corrects it to ZX-82. The system must retain the correction event, make ZX-82 current and treat both as unverified until an authorized lookup. A customer-visible response may explain the next step but cannot claim a refund is complete. The output includes current state, verification status, pending question and handoff reason.'),
            ('Build reviewed turns', 'Annotate full multi-turn cases with slot updates, explicit corrections, pronoun references and confirmation events. Include copied agent messages, mixed languages and multiple orders. Split by conversation and customer before training or evaluation; a single turn in both sets would leak the answer. [[natural-language-processing/dialogue-state-slots-and-corrections|The state contract]] defines set, clear and unchanged; [[natural-language-processing/support-entity-extraction-project|entity extraction]] supplies candidate identifiers.'),
            ('Rehearse action gates', 'Replay each reviewed case turn by turn. Compare joint state, correction success, unnecessary clarification rate and any wrong-action attempt. Stub the verification tool so tests can simulate ownership failure and ineligible refunds without touching customer accounts. A case passes only if no external action occurs until the current order is verified and the customer confirms. [[natural-language-processing/dialogue-handoff-and-action-gates|The handoff gate]] makes that condition explicit.'),
            ('Release with review', 'Deploy the state model, schema and policy together. Keep an audit trail of state changes and tool decisions under support access controls. Route unresolved references and unsupported language mixes to an agent with a concise evidence-backed summary. Review a sample of successful automated cases as well as handoffs. An increase in completed conversations is not a win if the wrong-action rate rises.'),
        ],
        'code': '''def replay_order_correction(events):
    state = {}
    for event in events:
        if event["operation"] == "set-order":
            state = {**state, "order_id": event["value"], "verified": False}
        elif event["operation"] == "verify-order":
            if state.get("order_id") != event["value"]:
                raise ValueError("verification is for an old order")
            state["verified"] = True
    return state

turns = [{"operation": "set-order", "value": "ZX-47"},
         {"operation": "set-order", "value": "ZX-82"},
         {"operation": "verify-order", "value": "ZX-82"}]
assert replay_order_correction(turns) == {"order_id": "ZX-82", "verified": True}
''',
        'cost': 'Replay is O(t) time for t turn events and O(s) active state for s slots; retained audit history is O(t). The expensive steps are verification calls and human resolution, so measure p95 tool latency and handoff completion time. Keep validation strict even if it adds a turn: a wrong refund has a different cost from a delayed but correct reply.',
        'mistakes': ['Verifying an earlier order after the customer corrected it.', 'Treating a model answer as confirmation from the customer.', 'Evaluating each turn independently instead of replaying a whole case.', 'Logging the entire conversation into an unrestricted metrics stream.'],
        'related': [N + 'dialogue-state-slots-and-corrections', N + 'dialogue-handoff-and-action-gates', N + 'support-entity-extraction-project', N + 'multilingual-ticket-routing-project', N + 'privacy-safe-ticket-pipeline-project'],
    },
]
crosslinks = [
    (N + 'span-offset-annotation', N + 'extractive-qa-span-and-window-contract'),
    (N + 'incident-runbook-search-project', N + 'runbook-question-answering-project'),
    (N + 'document-summary-evidence-contract', N + 'qa-answerability-and-calibration'),
    (N + 'coreference-chains-and-mention-identity', N + 'dialogue-state-slots-and-corrections'),
    (N + 'support-entity-extraction-project', N + 'refund-conversation-state-project'),
    (N + 'classification-slices-and-abstention', N + 'dialogue-handoff-and-action-gates'),
    (N + 'extractive-qa-span-and-window-contract', N + 'qa-answerability-and-calibration'),
    (N + 'dialogue-state-slots-and-corrections', N + 'dialogue-handoff-and-action-gates'),
]

if __name__ == '__main__':
    publish(lessons, (Q, C), crosslinks,
            'aitrove-nlp-qa-dialogue-import-20261006.json', 4750,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
