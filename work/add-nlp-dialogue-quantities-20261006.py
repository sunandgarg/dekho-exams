"""Add dialogue-act and numeric-language lessons to NLP."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
D = 'Dialogue acts, repair and commitments'
Q = 'Quantities, units and numeric claims'

lessons = [
    {
        'path': N + 'speech-act-intent-and-commitment-boundaries',
        'title': 'Speech acts: requests, reports and commitments in support dialogue',
        'module': D, 'project': False,
        'summary': 'The same action words can report an event, request help or promise future work. Classify the utterance function before updating workflow state.',
        'sections': [
            ('Label the act, not just the subject', '“Please roll back the gateway” is a request; “we rolled back the gateway” reports a past action; “I will roll it back” is a proposed commitment. All three mention rollback, so an intent classifier that sees only topic words will collapse them. Record speaker, turn ID, act, target span, tense and source revision. [[natural-language-processing/dialogue-state-slots-and-corrections|Dialogue state]] can use the act to update pending tasks without mistaking a report for authorization.'),
            ('Use preceding turns as evidence', '“Yes, do that” depends on an earlier proposal; alone, it has no safe action target. Attach it to a specific antecedent turn and verify who is authorized to approve that action. A customer asking for an account change does not mean the assistant may execute it. If the prior turn is missing or ambiguous, keep the act unresolved. [[natural-language-processing/coreference-chains-and-mention-identity|Reference chains]] help identify “that,” but a resolved pronoun still does not confer permission.'),
            ('Keep commitment and execution apart', 'An agent’s promise to investigate is a commitment, not proof that the investigation happened. Track promised action, owner, due condition and later completion evidence as separate records. A bot should never mark a task complete merely because it generated “I’ll check.” If a speaker retracts a commitment, preserve both turns and the retraction relation. [[natural-language-processing/discourse-units-and-relation-scope|Discourse relations]] can represent correction and contrast without rewriting history.'),
            ('Evaluate downstream mistakes', 'Score act labels, target-turn links, unauthorized action attempts, missing commitments and false completion. Include short acknowledgments, reported speech, sarcasm, copied transcripts and overlapping speaker turns. Separate classification quality from workflow safety: a mostly correct model may still trigger a costly action on one wrongly classified report. The [[natural-language-processing/support-commitment-audit-project|commitment audit project]] stages high-risk acts for review before any external action.'),
        ],
        'code': '''def stage_dialogue_act(turn_id, speaker, act, target_turn=None):
    allowed = {"request", "report", "commitment", "approval", "unresolved"}
    if not turn_id or not speaker or act not in allowed:
        raise ValueError("turn, speaker and valid act are required")
    if act == "approval" and not target_turn:
        return {"state": "review", "reason": "approval-target-missing"}
    return {"state": "proposed", "turn_id": turn_id,
            "speaker": speaker, "act": act, "target_turn": target_turn}

assert stage_dialogue_act("turn-47", "agent-82", "report")["act"] == "report"
assert stage_dialogue_act("turn-91", "customer-47", "approval")["state"] == "review"
''',
        'cost': 'The staging check is O(1) per turn. Linking a turn to one of h earlier turns can be O(h) without an index, while model inference has its own cost. Human review should focus on acts that can create an external commitment or action. A label is evidence about language use, not authorization from an account system.',
        'mistakes': ['Treating every action verb as an instruction to execute.', 'Marking a promised task complete without later evidence.', 'Accepting “yes” without a uniquely identified prior proposal.', 'Reporting act accuracy while ignoring unauthorized workflow transitions.'],
        'related': [N + 'conversation-repair-and-clarification-state', N + 'support-commitment-audit-project', N + 'dialogue-state-slots-and-corrections', N + 'dialogue-handoff-and-action-gates', N + 'coreference-chains-and-mention-identity'],
    },
    {
        'path': N + 'conversation-repair-and-clarification-state',
        'title': 'Conversation repair: corrections, clarification and unresolved targets',
        'module': D, 'project': False,
        'summary': 'A correction changes a prior claim, not the original transcript. Keep the target turn and the remaining uncertainty visible.',
        'sections': [
            ('Identify the repair target', 'A customer says “the east worker failed,” then “sorry, I meant the west worker.” The second turn repairs a specific entity in the first. Store both turns, the repaired span, replacement span and speaker. Do not globally replace every occurrence of east in the conversation. If several earlier turns mention a worker, ask which one was corrected. [[natural-language-processing/span-offset-annotation|Span offsets]] anchor the change to the original wording.'),
            ('Distinguish correction from new information', '“The worker failed again” may add another event rather than retract the first failure. A repair signal, target and compatible context should support the edit. Keep the old claim as superseded with its reason, rather than deleting it from the audit. A partial correction might change only a time or region while leaving the action intact. [[natural-language-processing/claim-conflict-and-temporal-review|Claim conflict review]] helps detect when two active statements cannot both be used.'),
            ('Ask a narrow clarification when needed', 'If the user writes “not that one,” the referent may be unclear. Preserve candidate targets and ask a question naming the alternatives; do not select the nearest noun by default. Clarification is a dialogue act with a pending answer, not a random new intent. When a reply arrives, link it to the open question and update only the affected slot. [[natural-language-processing/dialogue-state-slots-and-corrections|The slot contract]] maintains those pending values.'),
            ('Measure repair quality over turns', 'Test corrected entity, quantity, date and action, plus cases where a later turn is not a correction. Score target identification, preserved unaffected fields, false repairs and clarification burden. Group whole conversations before splitting evaluation. A system that overwrites the first message may appear correct in final-state scoring while losing the evidence needed to explain a disputed support action. The [[natural-language-processing/support-commitment-audit-project|audit project]] checks repair before commitments are staged.'),
        ],
        'code': '''def apply_turn_repair(turns, target_turn_id, field, replacement, repair_turn_id):
    if target_turn_id not in turns:
        return {"state": "clarify", "reason": "target-turn-missing"}
    previous = turns[target_turn_id]
    if field not in previous:
        return {"state": "clarify", "reason": "field-not-in-target"}
    updated = {**previous, field: replacement}
    return {"state": "proposed-repair", "target_turn": target_turn_id,
            "repair_turn": repair_turn_id, "before": previous, "after": updated}

turns = {"turn-47": {"service": "worker-east", "action": "failed"}}
repair = apply_turn_repair(turns, "turn-47", "service", "worker-west", "turn-82")
assert repair["after"]["service"] == "worker-west"
assert turns["turn-47"]["service"] == "worker-east"
''',
        'cost': 'A hash-map target lookup and shallow field copy are expected O(1) for a fixed-size turn record, or O(f) for f fields. Discovering the intended target from a long history may require O(h) candidate inspection. Retaining both versions costs storage, but prevents a correction from silently erasing the basis of earlier decisions.',
        'mistakes': ['Globally replacing a corrected word throughout the conversation.', 'Treating every later disagreement as a correction of the nearest turn.', 'Deleting the original claim after applying a repair.', 'Updating an authorized action before an ambiguous repair is resolved.'],
        'related': [N + 'speech-act-intent-and-commitment-boundaries', N + 'support-commitment-audit-project', N + 'dialogue-state-slots-and-corrections', N + 'span-offset-annotation', N + 'claim-conflict-and-temporal-review'],
    },
    {
        'path': N + 'support-commitment-audit-project',
        'title': 'Project: audit support commitments and conversation repairs',
        'module': D, 'project': True,
        'summary': 'Track requests, promises and corrections in support conversations without turning proposed language into an authorized action.',
        'sections': [
            ('Set the workflow boundary', 'A customer reports a failed gateway and asks for a retry-policy change. An agent promises to investigate, then corrects the affected region. The system may stage a task and a proposed correction; it may not modify production policy from text alone. Store speaker, turn, source revision, act, target and authorization state. [[natural-language-processing/speech-act-intent-and-commitment-boundaries|Speech-act policy]] separates request, report, promise and approval.'),
            ('Construct conversations that break shortcuts', 'Include “yes” without a clear target, quoted promises, agent reports of completed work, a customer correction after several similar turns and an ASR transcript with overlapping speakers. Group each full conversation in one evaluation split. Reviewers mark the act, target, repaired field and whether the speaker had authority. Add a case where a generated assistant promise is never carried out; the task must remain open until separate completion evidence arrives.'),
            ('Stage commitments and repairs', 'Classify turns with history, but keep unresolved targets in a clarification queue. Apply a repair as a proposed overlay that preserves the old claim. Create a commitment record only when an identified speaker makes a definite promise, and keep it distinct from the operational action. Before any external change, check account authorization through the real action service. [[natural-language-processing/conversation-repair-and-clarification-state|Repair state]] ensures a corrected region does not rewrite unrelated history.'),
            ('Release on workflow safety', 'Measure false commitments, missed promises, wrong repair targets, unsupported completion and unauthorized action attempts. Review the final task queue and conversation transcript side by side. Shadow the workflow before enabling task creation. If an ambiguous short acknowledgment begins closing tasks, roll back the act policy and inspect affected conversations. A good label score cannot excuse an incorrect account or production change.'),
        ],
        'code': '''def stage_commitment(act, speaker_role, target_action, authorized):
    if act != "commitment":
        return {"state": "no-commitment"}
    if not target_action:
        return {"state": "clarify", "reason": "action-target-missing"}
    if speaker_role != "agent" or not authorized:
        return {"state": "review", "reason": "authority-unverified"}
    return {"state": "task-proposed", "action": target_action,
            "completed": False}

task = stage_commitment("commitment", "agent", "inspect gateway-west logs", True)
assert task == {"state": "task-proposed",
                "action": "inspect gateway-west logs", "completed": False}
assert stage_commitment("report", "agent", "inspect logs", True)["state"] == "no-commitment"
''',
        'cost': 'This staging gate is O(1) per turn. Linking targets and checking authority against external systems add latency; do not replace them with a language-model score. Human review cost should be concentrated on ambiguous commitments and corrections that affect actions. Track cost per correctly staged task and false-completion rate, not just classification throughput.',
        'mistakes': ['Executing a production change because text was classified as a commitment.', 'Marking a task done when only a promise was recorded.', 'Accepting approval from a speaker without checking account authority.', 'Erasing the original region after a correction.'],
        'related': [N + 'speech-act-intent-and-commitment-boundaries', N + 'conversation-repair-and-clarification-state', N + 'dialogue-handoff-and-action-gates', N + 'refund-conversation-state-project', N + 'support-call-transcript-review-project'],
    },
    {
        'path': N + 'quantity-span-unit-and-range-contract',
        'title': 'Quantities in text: value, unit, range and source span',
        'module': Q, 'project': False,
        'summary': 'A number is not a metric until its unit, entity, time window and source are known. Parse those fields before comparing claims.',
        'sections': [
            ('Bind the value to what it measures', '“47 retries in 82 minutes” contains a count and a duration. Store each value with its unit, source span, associated service and observation window. Do not treat the duration as a second retry count. “About 47” is approximate; “under 47” is an upper bound; “47–82” is a range. These need distinct comparison rules. [[natural-language-processing/time-expression-anchor-and-zone-contract|Time anchors]] are required when a quantity refers to a relative window.'),
            ('Preserve locale and written form', 'A decimal separator, grouping mark or percent sign can be misread across locales. Keep the exact source string and declared locale before parsing. Avoid binary floating-point for money or a threshold that demands decimal exactness. A unit such as ms versus s changes scale, while “requests” versus “failed requests” changes the measured population. A parser should abstain on unknown units rather than silently assuming a familiar one.'),
            ('Normalize only under a declared policy', 'Convert between compatible units with an explicit factor and version. Do not compare bytes with requests, or percentages with counts lacking denominators. If one source reports an interval and another a point estimate, preserve that distinction through aggregation. [[natural-language-processing/table-cell-header-scope-and-reading-order|Table headers]] may supply the unit when the cell holds only a bare number; record the header as part of its evidence.'),
            ('Audit extraction and interpretation', 'Score numeric span, unit, comparator, entity, window and derived value separately. Include OCR confusions, negatives, ranges, approximations, percentages and units that look alike. A system can read “47” correctly but attach it to the wrong service or time period. Reviewers should see the original phrase and any conversion step. The [[natural-language-processing/incident-numeric-claim-review-project|numeric claim project]] tests the full path from text to answer.'),
        ],
        'code': '''from decimal import Decimal

UNIT_TO_SECONDS = {"s": Decimal("1"), "min": Decimal("60")}

def duration_seconds(raw_value, unit, source_span):
    if unit not in UNIT_TO_SECONDS or not source_span:
        return {"state": "review", "reason": "unit-or-source-missing"}
    value = Decimal(raw_value)
    if value < 0:
        return {"state": "review", "reason": "negative-duration"}
    return {"state": "normalized", "seconds": value * UNIT_TO_SECONDS[unit],
            "original": raw_value, "unit": unit, "source_span": source_span}

assert duration_seconds("82", "min", "82 minutes")["seconds"] == Decimal("4920")
assert duration_seconds("47", "requests", "47 requests")["state"] == "review"
''',
        'cost': 'A dictionary unit lookup and decimal conversion of d digits cost at least O(d) time and space. Parsing n characters of text is at least O(n). Unit normalization is cheap relative to correcting wrong entity or time-window links, so measure those errors separately. The example handles two duration units, not arbitrary physical dimensions.',
        'mistakes': ['Comparing counts and percentages without a denominator.', 'Assuming a bare number has the unit used by another document.', 'Discarding “about,” “under” or a range marker.', 'Using binary floating-point when exact decimal thresholds matter.'],
        'related': [N + 'numeric-claim-calculation-and-evidence', N + 'incident-numeric-claim-review-project', N + 'time-expression-anchor-and-zone-contract', N + 'table-cell-header-scope-and-reading-order', N + 'ocr-confidence-and-field-review'],
    },
    {
        'path': N + 'numeric-claim-calculation-and-evidence',
        'title': 'Numeric claims: denominators, calculations and evidence chains',
        'module': Q, 'project': False,
        'summary': 'A percentage or trend sentence needs the right numerator, denominator, time window and calculation trace, not merely two nearby numbers.',
        'sections': [
            ('Define the calculation before selecting values', '“Failures fell by 20%” is ambiguous between a relative decrease and a 20-point drop in a percentage rate. Write the intended operation and required fields first. For a failure rate, the numerator is failed requests and the denominator is eligible requests from the same service and window. Do not divide by total traffic from another region. [[natural-language-processing/quantity-span-unit-and-range-contract|Quantity spans]] keep each input attached to its unit and source.'),
            ('Track each input and transformation', 'An answer should carry both source spans, their document revisions, normalized units, formula and final rounding policy. Decimal arithmetic makes a displayed value reproducible, but it cannot make wrong inputs correct. If one input is approximate or OCR uncertain, mark the result as uncertain. [[natural-language-processing/ocr-confidence-and-field-review|OCR review]] should resolve a doubtful digit before it enters a published comparison.'),
            ('Handle conflicting and missing evidence', 'Two active notes may disagree about the number of requests in the same window. Stage a conflict with both sources rather than choosing the latest-looking number by default. A missing denominator means the rate is unanswered, not zero. If a metric is sampled, a direct ratio of reported counts may not estimate the full population. [[natural-language-processing/multi-passage-claim-aggregation-and-conflict|Multi-passage conflict handling]] prevents a fluent answer from hiding incompatible claims.'),
            ('Evaluate the statement a reader sees', 'Check input selection, operation, unit conversion, rounding, wording and evidence links separately. Include “increase from” versus “increase by,” percentage points, zero denominators and windows that touch midnight. Ask reviewers whether the final sentence says exactly what the calculation supports. The [[natural-language-processing/incident-numeric-claim-review-project|applied project]] requires the output to show its calculation, not just a polished trend statement.'),
        ],
        'code': '''from decimal import Decimal, ROUND_HALF_UP

def failure_rate(failed_requests, eligible_requests, evidence_ids):
    failures = Decimal(failed_requests)
    total = Decimal(eligible_requests)
    if total <= 0 or failures < 0 or failures > total or len(evidence_ids) != 2:
        return {"state": "review", "reason": "invalid-input-or-evidence"}
    percent = (failures * Decimal("100") / total).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {"state": "calculated", "percent": percent,
            "evidence_ids": tuple(evidence_ids)}

result = failure_rate("47", "235", ["failures-47", "traffic-82"])
assert result["percent"] == Decimal("20.00")
assert failure_rate("47", "0", ["failures-47", "traffic-82"])["state"] == "review"
''',
        'cost': 'Decimal parsing and arithmetic scale with input digit length d rather than being truly constant-time for unbounded numbers; evidence validation is O(1) for the two expected IDs. Document retrieval and human verification dominate end-to-end cost. Retain the arithmetic trace so a changed source can invalidate a derived claim instead of leaving an old percentage in circulation.',
        'mistakes': ['Calling a percentage-point change a relative percent change.', 'Using numerator and denominator from different windows.', 'Replacing a missing denominator with zero.', 'Publishing a calculated rate without input evidence IDs.'],
        'related': [N + 'quantity-span-unit-and-range-contract', N + 'incident-numeric-claim-review-project', N + 'multi-passage-claim-aggregation-and-conflict', N + 'summary-claim-verification-and-review', N + 'ocr-confidence-and-field-review'],
    },
    {
        'path': N + 'incident-numeric-claim-review-project',
        'title': 'Project: review numeric claims in incident summaries',
        'module': Q, 'project': True,
        'summary': 'Extract operational quantities, calculate a supported rate and keep an incident summary from overstating uncertain or mismatched measurements.',
        'sections': [
            ('Define the decision boundary', 'An incident draft says “gateway-west failures reached 20%.” The system must find failed and eligible request counts for the same environment and time window, calculate the rate, and show both source spans. It can stage the sentence for a reviewer; it cannot invent a denominator or suppress a conflicting update. [[natural-language-processing/quantity-span-unit-and-range-contract|The quantity contract]] keeps raw values, units and uncertainty attached to their sources.'),
            ('Build a difficult case set', 'Collect status notes, runbook tables and OCR screenshots with counts, durations, ratios and ranges. Add two regions, a correction of an earlier count, a blank denominator and a percentage-point comparison. Group all updates from one incident in one evaluation split. Reviewers mark the exact inputs, formula, window and whether the proposed sentence is supported. An easy arithmetic set is insufficient if the hard problem is selecting the right measurements.'),
            ('Stage calculations with lineage', 'Parse numeric candidates, bind them to service and window, then require compatible units. Reject a denominator that comes from another environment or revision. Calculate with decimal arithmetic and save the formula plus evidence IDs. If active sources conflict, return a review state with both claims. [[natural-language-processing/numeric-claim-calculation-and-evidence|Calculation lineage]] lets a correction invalidate a previously derived percentage. The summary generator receives only reviewed numeric claims.'),
            ('Measure the released claim', 'Report wrong input selection, unit errors, zero-denominator handling, incorrect rounding, unsupported trend wording and reviewer time. Check the final sentence against the calculation, because “rose to 20%” and “rose by 20%” are not equivalent. Shadow the process on resolved incidents before release. Keep source revisions and the previous calculation policy so a bad parser update can be rolled back without erasing earlier evidence.'),
        ],
        'code': '''from decimal import Decimal

def stage_incident_rate(failed, eligible, same_scope, source_ids):
    if not same_scope or len(source_ids) != 2:
        return {"state": "review", "reason": "scope-or-evidence-mismatch"}
    failed_count = Decimal(failed)
    eligible_count = Decimal(eligible)
    if eligible_count <= 0 or not 0 <= failed_count <= eligible_count:
        return {"state": "review", "reason": "invalid-counts"}
    return {"state": "proposed", "rate": failed_count / eligible_count,
            "source_ids": tuple(source_ids)}

claim = stage_incident_rate("47", "235", True,
                            ["incident-47-failed", "incident-47-total"])
assert claim["rate"] == Decimal("0.2")
assert stage_incident_rate("47", "235", False, ["a", "b"])["state"] == "review"
''',
        'cost': 'The scope gate is O(1); decimal work grows with the number of digits. Finding and validating source counts is the expensive NLP and review step. Measure the share of proposed claims accepted without correction, plus the rate of unsupported published statements. A fast calculation cannot compensate for a numerator drawn from the wrong incident.',
        'mistakes': ['Using correct arithmetic on counts from different scopes.', 'Converting an uncertain OCR number into a precise published percentage.', 'Confusing “rose to” with “rose by” in the final sentence.', 'Failing to invalidate a rate when one source note is corrected.'],
        'related': [N + 'quantity-span-unit-and-range-contract', N + 'numeric-claim-calculation-and-evidence', N + 'incident-handoff-summary-project', N + 'summary-claim-verification-and-review', N + 'support-table-evidence-project'],
    },
]

crosslinks = [
    (N + 'dialogue-state-slots-and-corrections', N + 'speech-act-intent-and-commitment-boundaries'),
    (N + 'dialogue-handoff-and-action-gates', N + 'conversation-repair-and-clarification-state'),
    (N + 'refund-conversation-state-project', N + 'support-commitment-audit-project'),
    (N + 'time-expression-anchor-and-zone-contract', N + 'quantity-span-unit-and-range-contract'),
    (N + 'summary-claim-verification-and-review', N + 'numeric-claim-calculation-and-evidence'),
    (N + 'incident-handoff-summary-project', N + 'incident-numeric-claim-review-project'),
]

if __name__ == '__main__':
    publish(lessons, (D, Q), crosslinks,
            'aitrove-nlp-dialogue-quantities-import-20261006.json', 4842,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
