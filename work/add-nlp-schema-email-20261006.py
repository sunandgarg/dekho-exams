"""Add evidence-bound extraction and email-thread provenance modules to NLP."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
E = 'Evidence-bound structured extraction'
M = 'Email thread provenance'

lessons = [
    {
        'path': N + 'schema-bound-field-extraction-and-source-spans',
        'title': 'Schema-bound extraction: typed fields and exact source spans',
        'module': E, 'project': False,
        'summary': 'Extract a document into typed fields whose values can be traced to exact source spans; a well-formed object alone is not evidence.',
        'sections': [
            ('Define fields before decoding', 'A change request may mention a service, requested window and approval status in different paragraphs. Define each field’s meaning, type, cardinality and allowed null state before a model reads the text. A “window” can mean start time, end time or a duration, so one loose string field is inadequate. Keep schema version with every extraction. [[natural-language-processing/time-expression-anchor-and-zone-contract|Time anchors and zones]] are needed before a local time can become a scheduled instant.'),
            ('Bind values to evidence', 'Require every asserted value to carry a character span into the immutable source revision. A valid span must be within bounds and the captured text must support the value; the latter needs semantic review when normalization changes form. For example, the value “47 minutes” may be normalized to a duration, but the source phrase and unit must remain available. An empty field means missing, not false. A model can emit perfect JSON with a fabricated value, so syntax validation cannot replace evidence checks. [[natural-language-processing/span-offset-annotation|Span annotation]] supplies the offset convention.'),
            ('Handle repeated and conflicting mentions', 'A document may list a proposed window and later a revised window. Preserve both candidates with section, author and revision context instead of taking the first match. Decide which mention is active through an explicit document policy; unresolved conflicts should block downstream scheduling. Nested tables and OCR reading order can separate a label from its value, so offsets should refer to the extracted source representation and its revision, not a casually normalized string. [[natural-language-processing/table-cell-header-scope-and-reading-order|Table scope]] covers that case.'),
            ('Evaluate per field and per document', 'Report exact-span match, normalized-value correctness, missing-field precision, conflict detection and document-level completeness. A record with four correct fields and one invented approval is not releasable. Slice by document template, OCR quality and field frequency. Keep a blind test set with unseen services and changed layouts; otherwise the extractor may memorize a template. The [[natural-language-processing/extraction-repair-and-conflict-states|repair lesson]] shows how to hold invalid output, and the [[natural-language-processing/change-request-extraction-project|project]] tests a release boundary.'),
        ],
        'code': '''def validate_evidence_fields(source_text, extracted, allowed_fields):
    errors = []
    for field_name, field_value in extracted.items():
        if field_name not in allowed_fields:
            errors.append((field_name, "unknown-field"))
            continue
        start, end = field_value["span"]
        if not 0 <= start < end <= len(source_text):
            errors.append((field_name, "bad-span"))
        elif source_text[start:end] != field_value["evidence"]:
            errors.append((field_name, "span-mismatch"))
    return errors

request_text = "Service gateway-west. Window: 47 minutes."
start = request_text.index("gateway-west")
record = {"service": {"value": "gateway-west", "span":
                      (start, start + len("gateway-west")),
                      "evidence": "gateway-west"}}
assert validate_evidence_fields(request_text, record, {"service"}) == []
assert validate_evidence_fields(request_text,
                                {"approval": record["service"]},
                                {"service"}) == [("approval", "unknown-field")]
''',
        'cost': 'For f fields, the loop is O(f) plus the cost of slicing and comparing evidence text; total copied character work is O(e) across e evidence characters. The example checks span integrity and a field allowlist, not whether the quoted words semantically justify the normalized value. That check remains a separate review step.',
        'mistakes': ['Treating valid JSON as proof that each value appears in the document.', 'Converting a missing field into a false approval.', 'Losing offsets when text is cleaned or OCR is rerun.', 'Taking the first timestamp when a later revision replaces it.'],
        'related': [N + 'extraction-repair-and-conflict-states', N + 'change-request-extraction-project', N + 'span-offset-annotation', N + 'time-expression-anchor-and-zone-contract', N + 'table-cell-header-scope-and-reading-order'],
    },
    {
        'path': N + 'extraction-repair-and-conflict-states',
        'title': 'Extraction validation: repair limits and conflicting values',
        'module': E, 'project': False,
        'summary': 'Separate missing, malformed, unsupported and conflicting field states, then repair only what the source can justify.',
        'sections': [
            ('Make failure states explicit', 'An extractor can return a malformed object, a valid object with missing required fields, or two plausible values for one field. These are different failures. Preserve a state per field: found, missing, conflicting or unsupported. A value is unsupported when the source span does not substantiate the interpretation. Do not turn a missing approval into “approved” to satisfy a required schema. [[natural-language-processing/schema-bound-field-extraction-and-source-spans|Schema-bound extraction]] gives each candidate a source span before repair begins.'),
            ('Repair against the source, not the previous guess', 'A retry may fix a formatting error, but repeated model calls can also invent a plausible value. Limit retries and provide the original document plus the validator’s specific error. Reject a repair that changes evidence without a new valid span. If two versions of a window are present, the correct action may be human review rather than asking the model to choose. Keep each attempt, model version and validation result for audit. The review queue should show the competing phrases side by side.'),
            ('Apply document policy before release', 'Required fields depend on the workflow. A search index may accept a partial record, while a scheduler must hold a change request without a verified service and window. Define these gates outside the model prompt and version them. Conflicting values can be resolved only by a trusted rule, such as a signed amendment superseding a draft; mere recency in a concatenated text block is not enough. [[natural-language-processing/revision-dependency-invalidation-and-reindex|Revision invalidation]] shows why a corrected field must update dependent outputs.'),
            ('Measure repair harm', 'Track format-repair success separately from semantic correction. Count newly hallucinated fields, evidence-span changes, reviewer overrides and downstream release errors. Evaluate adversarial cases with duplicated labels, negated approval, obsolete sections and OCR noise. A high document completion rate can hide dangerous false positives. In the [[natural-language-processing/change-request-extraction-project|change-request project]], a record with conflicting windows must be held even if every field is syntactically present.'),
        ],
        'code': '''REQUIRED_FIELDS = {"service", "window_start", "approval"}

def extraction_release_state(field_states):
    unknown = set(field_states) - REQUIRED_FIELDS
    if unknown:
        return {"state": "review", "reason": "unknown-fields"}
    missing = REQUIRED_FIELDS - set(field_states)
    if missing:
        return {"state": "review", "reason": "missing-fields",
                "fields": sorted(missing)}
    if any(state == "conflicting" for state in field_states.values()):
        return {"state": "review", "reason": "conflicting-values"}
    if any(state != "found" for state in field_states.values()):
        return {"state": "review", "reason": "unsupported-value"}
    return {"state": "ready-for-evidence-review"}

states = {"service": "found", "window_start": "found",
          "approval": "conflicting"}
assert extraction_release_state(states)["reason"] == "conflicting-values"
assert extraction_release_state({**states, "approval": "found"})["state"] == \
    "ready-for-evidence-review"
''',
        'cost': 'With f field states, set creation and inspection take expected O(f) time and O(f) space. Retry inference cost depends on document length and model calls; cap attempts and preserve source spans. The ready state only advances to evidence review, because field-state labels alone cannot prove semantic correctness.',
        'mistakes': ['Retrying until the model invents a required field.', 'Calling a conflicting value merely missing.', 'Treating the latest paragraph as authoritative without document policy.', 'Using schema completeness as the only release metric.'],
        'related': [N + 'schema-bound-field-extraction-and-source-spans', N + 'change-request-extraction-project', N + 'revision-dependency-invalidation-and-reindex', N + 'summary-claim-verification-and-review', N + 'ocr-confidence-and-field-review'],
    },
    {
        'path': N + 'change-request-extraction-project',
        'title': 'Project: extract change requests with field-level evidence',
        'module': E, 'project': True,
        'summary': 'Build a change-request intake that captures source spans, detects revisions and blocks scheduling until required fields are verified.',
        'sections': [
            ('Build the corpus', 'Prepare fictional change requests for gateway-west and archive-east with a service identifier, requested window, risk note and approval wording. Include a draft followed by a correction, a negated approval and an OCR copy that swaps two digits. Annotate exact spans in immutable document revisions, normalized field values and field states. Group versions of the same request in one evaluation split. [[natural-language-processing/schema-bound-field-extraction-and-source-spans|Field evidence]] provides the annotation contract.'),
            ('Implement the pipeline', 'Parse document structure, propose values under a fixed schema, validate types and spans, then compare repeated mentions for conflict. Keep both the source phrase and the normalized value. A local timestamp needs a zone and date; a bare “next Friday” needs a reference date and may remain unresolved. Pass malformed outputs through one bounded repair attempt only when the validator can name a fix. [[natural-language-processing/extraction-repair-and-conflict-states|Repair states]] distinguish that from semantic disagreement.'),
            ('Gate downstream scheduling', 'Release a record to human scheduling review only after the source revision, service, window and approval evidence are present and not conflicting. A negative statement such as “approval pending” must not be normalized to approved. The code below checks release prerequisites; the actual approval interpretation and reviewer signature must come from the workflow’s trusted policy. Store a decision ledger that ties each field to its source and reviewer.'),
            ('Evaluate end to end', 'Report per-field value accuracy, source-span fidelity, false approval rate, conflict recall, held-record rate and human correction time. Score the final scheduled record, not just the extractor output. A single false approval should be visible even when most fields are correct. Re-run the corpus after schema or OCR changes and invalidate downstream records whose supporting span changed.'),
        ],
        'code': '''def admit_change_request(record):
    required = ("source_revision", "service_id", "window_utc",
                "approval_evidence", "reviewer_id")
    missing = [name for name in required if not record.get(name)]
    if missing:
        return {"state": "hold", "reason": "missing", "fields": missing}
    if record.get("field_conflict"):
        return {"state": "hold", "reason": "conflict"}
    if record["approval_evidence"]["state"] != "approved":
        return {"state": "hold", "reason": "approval-not-verified"}
    return {"state": "review-ready", "service_id": record["service_id"]}

request = {"source_revision": "change-r7", "service_id": "gateway-west",
           "window_utc": "2026-10-12T03:47:00Z",
           "approval_evidence": {"state": "pending"},
           "reviewer_id": "reviewer-82", "field_conflict": False}
assert admit_change_request(request)["reason"] == "approval-not-verified"
assert admit_change_request({**request, "approval_evidence":
                             {"state": "approved"}})["state"] == "review-ready"
''',
        'cost': 'The fixed-field admission gate takes O(1) time and space. Extracting and reviewing a document scales with its text length, number of candidate spans and human exceptions. A review-ready state is not an instruction to schedule work; it means a trusted reviewer can inspect the evidence-bound record.',
        'mistakes': ['Calling “approval pending” an approval.', 'Mixing fields from two revisions into one record.', 'Dropping the source spans after normalization.', 'Evaluating only individual fields while ignoring unsafe final records.'],
        'related': [N + 'schema-bound-field-extraction-and-source-spans', N + 'extraction-repair-and-conflict-states', N + 'time-expression-anchor-and-zone-contract', N + 'ocr-confidence-and-field-review', N + 'incident-claim-verification-project'],
    },
    {
        'path': N + 'email-quote-boundaries-and-author-attribution',
        'title': 'Email threads: quote boundaries and authored-text attribution',
        'module': M, 'project': False,
        'summary': 'Separate newly authored text from copied history so summaries and classifiers do not assign an old statement to the current sender.',
        'sections': [
            ('A thread is a set of messages, not one document', 'An email reply often embeds earlier messages. If the whole body is treated as the current sender’s words, a classifier can count the same complaint several times or attribute a previous promise to the wrong person. Preserve message ID, parent ID, sender, recipient, timestamp and MIME part before text analysis. Quote depth and forwarded-message markers are evidence about provenance, not the business content itself. [[natural-language-processing/coreference-chains-and-mention-identity|Mention identity]] helps when replies use “that change” or “it” without repeating the subject.'),
            ('Separate new text conservatively', 'Plain-text replies may prefix copied lines with a greater-than marker; HTML mail can use blockquote markup, tables or client-specific wrappers. Some users answer inline inside an old quote. A parser should mark spans as authored, quoted, signature or uncertain rather than delete all text after the first quote. Keep source offsets and a link to the original message. The small example below handles only plain-text line prefixes and intentionally leaves other formats for review. [[natural-language-processing/document-sections-and-passage-boundaries|Section boundaries]] provide a related document-segmentation pattern.'),
            ('Attribute claims to original senders', 'A copied sentence remains evidence of the earlier sender’s statement. The current sender may endorse it, reject it or merely include it for context. Those are separate speech acts. Resolve attribution using message lineage, not position in a flattened string. Quoted text can be useful for retrieval, but it should not count as a fresh commitment. [[natural-language-processing/speech-act-intent-and-commitment-boundaries|Commitment boundaries]] distinguish a request from a promise.'),
            ('Test messy mail', 'Evaluate top-posted, bottom-posted and inline replies; forwarded messages; signatures; mobile footers; HTML-only bodies; and broken parent headers. Measure authored-span precision, quote recall, speaker attribution and downstream decision accuracy. A high quote-removal score can still fail if the one fresh line inside an old block is erased. The [[natural-language-processing/email-correction-and-decision-state|correction lesson]] consumes these attributed messages, and the [[natural-language-processing/support-email-decision-ledger-project|project]] audits the final state.'),
        ],
        'code': '''def plain_text_authorship(body):
    segments = []
    for line_number, line in enumerate(body.splitlines(), start=1):
        stripped = line.lstrip()
        if not stripped:
            role = "blank"
        elif stripped.startswith(">"):
            role = "quoted"
        else:
            role = "authored-or-uncertain"
        segments.append({"line": line_number, "role": role, "text": line})
    return segments

reply = "The window is now 03:47 UTC.\\n> The window is 02:47 UTC."
parts = plain_text_authorship(reply)
assert [part["role"] for part in parts] == [
    "authored-or-uncertain", "quoted"]
assert parts[1]["text"].startswith(">")
''',
        'cost': 'Scanning n characters takes O(n) time and O(n) output space because the code retains each line. It is a deliberately limited plain-text heuristic. MIME parsing, HTML quote wrappers, inline replies and signatures require separate rules or review; a non-quoted line is not automatically authenticated as a new statement.',
        'mistakes': ['Assigning all copied text to the latest sender.', 'Deleting everything after the first quote marker.', 'Ignoring MIME parts and message IDs.', 'Treating a forwarded claim as a fresh commitment.'],
        'related': [N + 'email-correction-and-decision-state', N + 'support-email-decision-ledger-project', N + 'speech-act-intent-and-commitment-boundaries', N + 'document-sections-and-passage-boundaries', N + 'coreference-chains-and-mention-identity'],
    },
    {
        'path': N + 'email-correction-and-decision-state',
        'title': 'Email thread state: corrections, commitments and stale claims',
        'module': M, 'project': False,
        'summary': 'Track which attributed reply changed a decision without letting quoted history or message order alone overwrite active facts.',
        'sections': [
            ('Model the decision as a ledger', 'A support thread can contain a proposed maintenance window, a correction, an acknowledgement and a later cancellation. Summarizing all four as one current plan is wrong. Record each authored claim as an event with message ID, sender, field, value, intent and timestamp. Link corrections to the claim they supersede. Quoted history remains attached to its original event. [[natural-language-processing/email-quote-boundaries-and-author-attribution|Quote attribution]] must run before the ledger is built.'),
            ('Require explicit correction scope', 'The words “change it to 03:47” only update a window if “it” can be resolved to the relevant proposal. A later email about another service must not overwrite the first service’s state. Define a subject key from trusted ticket ID and service ID. A correction must name or unambiguously refer to a prior field. Otherwise, retain both claims and ask a reviewer. [[natural-language-processing/conversation-repair-and-clarification-state|Conversation repair]] gives a broader model for unresolved references.'),
            ('Separate evidence from authorization', 'A customer may request a different time; an operator may accept it; a scheduler may still need a formal approval. The ledger should represent these as different states rather than infer approval from recency. Role comes from authenticated mail identity and workflow policy, not a signature block inside the message. Avoid silently accepting an attached forwarded message as authority. [[natural-language-processing/trusted-action-gate-and-retrieval-audit|Trusted action gates]] cover the move from text interpretation to external action.'),
            ('Evaluate state at cutoffs', 'Ask what was known after each message, not only at the end of the thread. Test out-of-order delivery, duplicate Message-IDs, late forwards, withdrawn commitments and two parallel subjects. Measure correction-link accuracy, active-state accuracy and unsafe approval assertions. An automatic summary can be helpful even when action is held. The [[natural-language-processing/support-email-decision-ledger-project|project]] implements a conservative release check.'),
        ],
        'code': '''def current_window(events, ticket_id):
    active = None
    for event in events:
        if event["ticket_id"] != ticket_id or event["provenance"] != "authored":
            continue
        if event["field"] != "window_utc":
            continue
        if event["intent"] == "propose":
            active = {"state": "proposed", "value": event["value"],
                      "message_id": event["message_id"]}
        elif event["intent"] == "correct" and active and \
                event["supersedes"] == active["message_id"]:
            active = {"state": "corrected", "value": event["value"],
                      "message_id": event["message_id"]}
    return active or {"state": "unresolved"}

thread = [{"ticket_id": "ticket-47", "provenance": "authored",
           "field": "window_utc", "intent": "propose", "value": "02:47Z",
           "message_id": "mail-47", "supersedes": None},
          {"ticket_id": "ticket-47", "provenance": "authored",
           "field": "window_utc", "intent": "correct", "value": "03:47Z",
           "message_id": "mail-82", "supersedes": "mail-47"}]
assert current_window(thread, "ticket-47")["value"] == "03:47Z"
assert current_window(thread[:1], "ticket-47")["value"] == "02:47Z"
''',
        'cost': 'For m events, the scan takes O(m) time and O(1) extra space. It assumes an already verified event order, unique message IDs and resolved correction targets. Production handling must detect duplicates, out-of-order arrivals and conflicting parallel proposals before relying on an active state.',
        'mistakes': ['Letting a quoted older time replace a fresh correction.', 'Treating the last email as approved simply because it is last.', 'Applying a correction to another ticket or service.', 'Flattening event history so reviewers cannot reconstruct the state at a cutoff.'],
        'related': [N + 'email-quote-boundaries-and-author-attribution', N + 'support-email-decision-ledger-project', N + 'conversation-repair-and-clarification-state', N + 'speech-act-intent-and-commitment-boundaries', N + 'trusted-action-gate-and-retrieval-audit'],
    },
    {
        'path': N + 'support-email-decision-ledger-project',
        'title': 'Project: reconstruct a support email decision ledger',
        'module': M, 'project': True,
        'summary': 'Parse a support thread into attributed events, link corrections and hold any decision whose authority or reference remains uncertain.',
        'sections': [
            ('Prepare the fixture', 'Create a fictional support thread about ticket-47: an initial 02:47 UTC window, a customer request to move it, an operator correction to 03:47 UTC and an old time quoted in the final reply. Add a forwarded message and an inline reply inside a quotation. Store source MIME, message IDs, parent links, sender identities and delivery timestamps. Annotate authored, quoted and uncertain spans before marking speech acts. [[natural-language-processing/email-quote-boundaries-and-author-attribution|Quote boundaries]] prevent copied text from becoming a new event.'),
            ('Build the ledger', 'Create events for proposal, request, correction, acknowledgement and withdrawal. Require each correction to name a field and a prior event it supersedes. Keep a versioned decision record at every message cutoff; this exposes when a summary would have been wrong at that time. Thread order alone is not authority. Use trusted identity and role policy to decide who can approve an operational change. [[natural-language-processing/email-correction-and-decision-state|Decision state]] supplies the event semantics.'),
            ('Release conservatively', 'The code below admits only a verified current decision with an explicit authorized acknowledgement. A statement labeled uncertain, a quote or a customer request cannot satisfy the approval gate. Keep a human-readable explanation tied to message IDs and source spans. This project does not send email or schedule a change; it produces a review record for a separate trusted workflow.'),
            ('Test the outcome', 'Report authored-span accuracy, attribution errors, correction-link errors, active-window accuracy and false approved decisions. Re-run the test with duplicate and out-of-order messages. Compare the final ledger to reviewer annotations at each cutoff, not only one end-of-thread summary. Inspect every false approval individually because it has a larger operational cost than a held but valid request.'),
        ],
        'code': '''def release_email_decision(state, authorized_senders):
    if state.get("window_status") != "resolved":
        return {"state": "hold", "reason": "window-unresolved"}
    acknowledgement = state.get("acknowledgement", {})
    if acknowledgement.get("provenance") != "authored":
        return {"state": "hold", "reason": "quoted-acknowledgement"}
    if acknowledgement.get("sender_id") not in authorized_senders:
        return {"state": "hold", "reason": "sender-scope"}
    if acknowledgement.get("window_utc") != state.get("window_utc"):
        return {"state": "hold", "reason": "stale-acknowledgement"}
    return {"state": "review-ready", "window_utc": state["window_utc"]}

decision = {"window_status": "resolved", "window_utc": "03:47Z",
            "acknowledgement": {"provenance": "authored",
                                "sender_id": "operator-82",
                                "window_utc": "03:47Z"}}
assert release_email_decision(decision, {"operator-82"})["state"] == \
    "review-ready"
assert release_email_decision({**decision, "acknowledgement":
                               {**decision["acknowledgement"],
                                "provenance": "quoted"}},
                              {"operator-82"})["state"] == "hold"
''',
        'cost': 'With a hash-backed sender set, this final gate is expected O(1) time and space. MIME parsing and event reconstruction scale with thread size, while human review handles uncertain attribution. A review-ready ledger is not an email or scheduling action; that action requires its own authenticated controls.',
        'mistakes': ['Allowing a quoted acknowledgement to pass as current authorization.', 'Trusting a signature block for sender identity.', 'Checking the latest timestamp without checking what the sender actually accepted.', 'Evaluating only the final summary and missing earlier wrong states.'],
        'related': [N + 'email-quote-boundaries-and-author-attribution', N + 'email-correction-and-decision-state', N + 'speech-act-intent-and-commitment-boundaries', N + 'incident-handoff-summary-project', N + 'trusted-action-gate-and-retrieval-audit'],
    },
]

crosslinks = [
    (N + 'span-offset-annotation', N + 'schema-bound-field-extraction-and-source-spans'),
    (N + 'ocr-confidence-and-field-review', N + 'extraction-repair-and-conflict-states'),
    (N + 'incident-claim-verification-project', N + 'change-request-extraction-project'),
    (N + 'document-sections-and-passage-boundaries', N + 'email-quote-boundaries-and-author-attribution'),
    (N + 'conversation-repair-and-clarification-state', N + 'email-correction-and-decision-state'),
    (N + 'incident-handoff-summary-project', N + 'support-email-decision-ledger-project'),
]

if __name__ == '__main__':
    publish(lessons, (E, M), crosslinks,
            'aitrove-nlp-schema-email-import-20261006.json', 4890,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
