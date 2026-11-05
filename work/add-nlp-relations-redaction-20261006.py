"""Add discourse extraction and privacy controls to the NLP catalog."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
D = 'Discourse and relation extraction'
P = 'Privacy-aware text processing'

lessons = [
    {
        'path': N + 'coreference-chains-and-mention-identity',
        'title': 'Coreference chains: track mentions without guessing identity',
        'module': D, 'project': False,
        'summary': 'A document may call the same service “the gateway,” “it” and “that component.” Link mentions within the document before making cross-document identity claims.',
        'sections': [
            ('Mention identity is local', 'A mention is a span in a specific source revision. A coreference chain groups mentions that refer to one discourse entity in that source. It is not a global database identity. In “The gateway retried the charge. It timed out,” “It” may mean the gateway or the charge operation; a model should preserve uncertainty when context does not resolve it. Record span offsets, chain ID, confidence and adjudication version. [[natural-language-processing/span-offset-annotation|Span-offset annotation]] provides the source coordinate system.'),
            ('Separate coreference from entity linking', 'Coreference answers whether two mentions in this text refer together. Entity linking asks whether a mention maps to a known catalog record. An internal service called “Atlas” may share its name with several products; do not merge chains across incidents by surface string. First build document-local chains, then link a chain to a catalog ID using context and a candidate list. Keep NIL as an explicit result when none fits. A wrong global link can poison later [[natural-language-processing/relation-extraction-provenance|relation extraction]] more than an unresolved pronoun does.'),
            ('Annotate difficult discourse', 'Review pronouns, shortened names, nominal phrases, plural references and quoted text. Mark genuinely ambiguous cases separately rather than forcing agreement. Split evaluation by source document or incident; copied paragraphs in both train and test will overstate generalization. Score mention detection and chain linking separately. A system can find every pronoun yet attach them to the wrong named entity, so inspect chain-level errors with the original context.'),
            ('Keep provenance through changes', 'A corrected document revision can shift every offset. Store mention records with revision IDs and recompute spans only after a verified mapping. Never let chain IDs silently survive a rewrite. In production, show the source sentence and antecedent when a resolved entity drives a downstream action. The [[natural-language-processing/entity-relation-ledger-project|relation ledger project]] uses that record to avoid turning a weak pronoun guess into a firm operational fact.'),
        ],
        'code': '''def validate_mentions(source_text, mentions):
    chain_members = {}
    for mention in mentions:
        start, end = mention["start"], mention["end"]
        if not 0 <= start < end <= len(source_text):
            raise ValueError("mention is outside the source revision")
        if source_text[start:end] != mention["surface"]:
            raise ValueError("mention no longer matches the source")
        chain_members.setdefault(mention["chain_id"], []).append((start, end))
    return chain_members

incident_note = "The gateway retried. It failed."
mentions = [{"start": 4, "end": 11, "surface": "gateway", "chain_id": "c47"},
            {"start": 21, "end": 23, "surface": "It", "chain_id": "c47"}]
assert len(validate_mentions(incident_note, mentions)["c47"]) == 2
''',
        'cost': 'Validation is O(m + selected characters) time and O(m) space for m mentions. Candidate antecedent search can approach O(m²) if every mention is compared with every earlier mention; prune by sentence distance and compatible type only after measuring recall on long documents. Global entity linking adds catalog retrieval cost. Store NIL and ambiguity rates because faster forced linking can increase expensive downstream corrections.',
        'mistakes': ['Treating a shared name as proof of global identity.', 'Counting mention detection as successful coreference.', 'Reusing offsets after the source revision changes.', 'Forcing one antecedent where the document leaves the reference ambiguous.'],
        'related': [N + 'span-offset-annotation', N + 'relation-extraction-provenance', N + 'entity-relation-ledger-project', N + 'entity-decoding-and-span-evaluation', 'knowledge-graphs/knowledge-graphs-tutorial'],
    },
    {
        'path': N + 'relation-extraction-provenance',
        'title': 'Relation extraction with direction, negation and evidence',
        'module': D, 'project': False,
        'summary': 'Two entities appearing in one sentence do not prove a relationship. Store direction, time, negation and the supporting span with each extracted edge.',
        'sections': [
            ('Define a typed relation contract', 'An incident note might state “Service Delta depends on Queue K” or “Queue K no longer feeds Service Delta.” The entity pair alone is insufficient. Define allowed subject and object types, relation direction, effective time, negation and confidence. A relation is an assertion about a source revision, not a permanent graph fact. Reject arguments outside the allowed type set. [[natural-language-processing/entity-decoding-and-span-evaluation|Exact entity spans]] must be checked before relation scoring.'),
            ('Construct examples without leakage', 'Annotate the minimal evidence span that supports the relation and mark explicit no-relation pairs. Include near misses: co-occurring names, quoted historical architecture, hypothetical changes and negated dependencies. Review entity coreference first when the relation uses “it” or “the processor.” Split by incident, document and time so the same configuration sentence cannot appear in both training and audit. A model that memorizes service pairs will otherwise look accurate without reading the relation words.'),
            ('Evaluate both stages', 'Report entity recall, pair candidate recall, relation precision and end-to-end edge F1. An edge is correct only when subject, predicate, object, direction and evidence revision match the reviewed record. Partial entity overlap is not enough if it changes which system owns an action. Track errors caused by coreference separately from relation classification. The [[natural-language-processing/coreference-chains-and-mention-identity|coreference path]] defines when a mention can be promoted to a catalog identity.'),
            ('Publish as a reversible assertion', 'Write edges to a staging ledger with source digest and review state. If the source retracts a claim, mark the edge superseded instead of silently deleting audit history. Require human approval for high-impact dependencies or ownership claims. A graph query should distinguish “observed in source,” “reviewed current” and “retired.” The [[natural-language-processing/entity-relation-ledger-project|applied ledger]] makes those states visible; [[knowledge-graphs/knowledge-graphs-tutorial|knowledge graph foundations]] cover later graph use.'),
        ],
        'code': '''def relation_assertion(subject, predicate, object_id, evidence, allowed_types):
    subject_id, subject_type = subject
    target_id, target_type = object_id
    if (subject_type, predicate, target_type) not in allowed_types:
        raise ValueError("relation type or direction is not allowed")
    if not evidence["source_revision"] or not evidence["quote"].strip():
        raise ValueError("source evidence is required")
    return {"subject": subject_id, "predicate": predicate,
            "object": target_id, "evidence": evidence, "state": "staged"}

allowed = {("SERVICE", "DEPENDS_ON", "QUEUE")}
edge = relation_assertion(("service-delta", "SERVICE"), "DEPENDS_ON",
    ("queue-k", "QUEUE"), {"source_revision": "note-v7", "quote": "Delta depends on K"}, allowed)
assert edge["state"] == "staged"
''',
        'cost': 'Contract validation is constant time per proposed edge with a hashed type set, aside from copying evidence text. Generating all entity pairs is O(e²) for e entities in a document; sentence windows and type constraints reduce candidates but can miss cross-sentence relations. Measure candidate recall before celebrating a faster classifier. Store source digests and staged edges to support revocation without losing provenance.',
        'mistakes': ['Inferring a relation from co-occurrence alone.', 'Dropping negation or swapping subject and object.', 'Scoring relation labels only on gold entity pairs.', 'Publishing a graph edge without source revision and retirement state.'],
        'related': [N + 'coreference-chains-and-mention-identity', N + 'entity-relation-ledger-project', N + 'entity-decoding-and-span-evaluation', N + 'grouped-temporal-text-validation', 'knowledge-graphs/knowledge-graphs-tutorial'],
    },
    {
        'path': N + 'entity-relation-ledger-project',
        'title': 'Project: build a reviewed entity-relation ledger from incident notes',
        'module': D, 'project': True,
        'summary': 'Extract service dependencies from incident notes while preserving mention chains, evidence revisions and a human path for disputed edges.',
        'sections': [
            ('The ledger boundary', 'The product team wants to ask which services depended on a queue during an incident. Do not insert model output directly into the authoritative service catalog. Create a ledger of proposed assertions with source document revision, entity mentions, relation direction, effective time and review state. A “not stated” result is valid. Restrict the relation vocabulary to operational questions the reviewer can actually verify.'),
            ('Prepare reviewed documents', 'Capture incident notes before any cleanup that shifts character offsets. Annotate service and queue spans, local mention chains, candidate catalog IDs and relation evidence. Include negated and superseded statements. Group notes from the same incident in one split and reserve later incidents for final audit. Reviewers should settle whether “it” refers to the service or the queue before labeling the edge. Follow [[natural-language-processing/coreference-chains-and-mention-identity|mention identity]] and [[natural-language-processing/relation-extraction-provenance|relation provenance]] in that order.'),
            ('Gate the extraction', 'Evaluate every stage, including exact entity spans, chain links, catalog links, candidate pair coverage and end-to-end reviewed edges. Set separate thresholds for false dependencies and missed dependencies; they have different costs. Send ambiguous pronouns, unknown catalog identities and negated assertions to review. Compare a simple rule baseline against the trained model. A gain in classifier F1 does not justify release if candidate generation loses rare cross-sentence edges.'),
            ('Operate revisions', 'A reviewer can approve, reject or supersede an assertion. On a document revision, new proposed edges point to the new source digest; old approved edges remain in history but may be retired from the current graph view. Audit queries must filter state and time. Keep raw incident note permissions attached to evidence snippets. The published ledger exposes structured facts only to users authorized for the underlying documents.'),
        ],
        'code': '''def current_approved_edges(assertions, visible_source_revisions):
    return [assertion for assertion in assertions
            if assertion["state"] == "approved"
            and assertion["source_revision"] in visible_source_revisions
            and assertion.get("superseded_by") is None]

ledger = [
    {"edge_id": "edge-47", "state": "approved", "source_revision": "note-v7", "superseded_by": None},
    {"edge_id": "edge-48", "state": "staged", "source_revision": "note-v8", "superseded_by": None},
]
assert [row["edge_id"] for row in current_approved_edges(ledger, {"note-v7"})] == ["edge-47"]
''',
        'cost': 'The in-memory view scan is O(n) time for n assertions and O(v) output space for v visible current edges. A database should index review state, source revision and supersession for larger ledgers. Extraction candidate generation and human adjudication dominate production cost. Measure review queue age and false approved edges, not only model throughput, before promoting extracted relations into a graph view.',
        'mistakes': ['Writing predicted edges directly into the authoritative catalog.', 'Dropping old edge history when a note is corrected.', 'Showing evidence text to users who lack source access.', 'Evaluating only the relation classifier while ignoring coreference and entity linking errors.'],
        'related': [N + 'coreference-chains-and-mention-identity', N + 'relation-extraction-provenance', N + 'support-entity-extraction-project', 'knowledge-graphs/knowledge-graphs-tutorial', N + 'text-serving-contract'],
    },
    {
        'path': N + 'pii-detection-and-redaction-boundary',
        'title': 'PII detection and redaction on original text offsets',
        'module': P, 'project': False,
        'summary': 'A text pipeline should identify personal data before broad logging or model calls, but redaction must preserve auditability and avoid pretending detection is complete.',
        'sections': [
            ('Define what requires protection', 'Names, emails, account numbers and addresses have different risks and formats. Start with a data inventory tied to the actual workflow, then specify which fields must be removed, tokenized or retained for an authorized purpose. A regex can find some structured values, while a trained span model may find contextual names and addresses. Neither can guarantee complete detection. Make a reviewed sample that includes punctuation, mixed scripts, OCR noise and copied signatures. [[natural-language-processing/bio-labels-and-subword-alignment|Entity labels]] and [[natural-language-processing/entity-decoding-and-span-evaluation|exact-span metrics]] are useful foundations.'),
            ('Detect before transforming', 'Run detectors against the captured original representation and produce typed half-open offsets. If normalization is needed for matching, maintain a verified mapping back to the original text. Merge overlapping detections under a written priority policy; otherwise replacing an inner email span first can invalidate an outer address span. Apply replacements from right to left so earlier offsets stay valid. Keep an irreversible public display separate from a restricted evidence store. Never write the raw value into ordinary metrics or error logs.'),
            ('Choose a replacement contract', 'A fixed token such as [EMAIL] is suitable when exact recovery is unnecessary. Stable pseudonyms can preserve within-case joins, but they may reveal repeated identities across cases; scope them narrowly and protect the mapping. A replacement changes text length and all later offsets, so downstream annotations must refer either to the original or to a new mapped version. Annotate which representation every model consumes. [[natural-language-processing/unicode-tokenization-boundary|Unicode boundaries]] matter when names contain combining marks.'),
            ('Measure missed exposure', 'Report per-type recall, false-positive redactions, overlap conflicts and the volume sent for manual review. A single missed account number can matter more than several harmless over-redactions. Evaluate end-to-end exposure at every sink: analytics logs, search index, model input, generated summary and exported file. If the detector or mapping fails, fail closed for a sensitive sink. The [[natural-language-processing/redaction-audit-and-retention|audit path]] defines how to watch the result.'),
        ],
        'code': '''def redact_original_text(message, spans):
    ordered = sorted(spans, key=lambda span: (span[0], span[1]))
    previous_end = 0
    for start, end, label in ordered:
        if not (0 <= start < end <= len(message)) or start < previous_end:
            raise ValueError("invalid or overlapping redaction spans")
        if not label.isidentifier():
            raise ValueError("invalid replacement label")
        previous_end = end
    redacted = message
    for start, end, label in reversed(ordered):
        redacted = redacted[:start] + f"[{label}]" + redacted[end:]
    return redacted

ticket = "Write to mila@local.test about case 47."
assert redact_original_text(ticket, [(9, 24, "EMAIL")]) == "Write to [EMAIL] about case 47."
''',
        'cost': 'Sorting s spans takes O(s log s). With immutable Python strings, repeated replacement can copy up to O(n·s) characters for an n-character message; a single streaming join reduces this to O(n + s) after sorting for high-volume use. Detection cost varies by regex and model. Report missed exposure on reviewed samples and sink-level leaks; latency alone cannot justify a weaker detector for sensitive text.',
        'mistakes': ['Assuming a regex or NER model finds every personal value.', 'Replacing left to right with offsets from the original text.', 'Logging raw detector inputs when an exception occurs.', 'Reusing original annotations against a redacted string without remapping.'],
        'related': [N + 'redaction-audit-and-retention', N + 'privacy-safe-ticket-pipeline-project', N + 'span-offset-annotation', N + 'unicode-tokenization-boundary', N + 'entity-decoding-and-span-evaluation'],
    },
    {
        'path': N + 'redaction-audit-and-retention',
        'title': 'Audit redacted text flows, retention and re-identification risk',
        'module': P, 'project': False,
        'summary': 'Redaction is a pipeline property. Verify every output sink, retention window and access path instead of trusting one transformed string.',
        'sections': [
            ('Trace the data path', 'A ticket may reach intake logs, a classifier, a search index, a summarizer, a debugging trace and a training export. Map each sink with its purpose, permitted fields, retention time and access role. Decide whether it receives original, tokenized or fully redacted text. Apply the policy before a network call or log write. A downstream service must not accidentally receive the original because it subscribed to an early event. [[natural-language-processing/pii-detection-and-redaction-boundary|Detection and redaction]] handles the string; this contract handles the system around it.'),
            ('Retain only what can be justified', 'A restricted evidence store may need an original ticket for customer support, while aggregate metrics rarely do. Store the minimum copy count, encrypt where required by the existing platform, and attach deletion to a stable case identity. A pseudonym mapping is sensitive data and needs its own retention period. Deleting a visible ticket but leaving its embedding, cache key or training export can defeat the policy. Include derived data in the deletion manifest.'),
            ('Test the failure path', 'Inject synthetic canary values into a controlled test ticket and follow them through logs, indexes and exports. Assert they appear only in sinks explicitly allowed to hold originals. Test detector timeout, malformed UTF-8, overlapping spans and an unknown label type. For a sensitive sink, a failed detector must stop or quarantine the request. A success-shaped redaction response on detector failure is unsafe. Review false positives too: hiding a product code can remove the information needed to route a case.'),
            ('Watch re-identification by context', 'A message with names removed may still expose a person through a rare role, location and timestamp. Evaluate combinations of remaining attributes, not just obvious identifiers. Report policy version, redaction detector version, sink inventory version and sampled leak findings. If a new sink is added, run the tests before enabling it. The [[natural-language-processing/privacy-safe-ticket-pipeline-project|ticket pipeline project]] combines these checks with NLP serving.'),
        ],
        'code': '''def allow_sink_payload(payload, sink_policy):
    unknown_fields = set(payload) - set(sink_policy["allowed_fields"])
    if unknown_fields:
        raise ValueError(f"fields not allowed at sink: {sorted(unknown_fields)}")
    if sink_policy["requires_redaction"] and payload.get("representation") != "redacted":
        raise ValueError("sink requires redacted representation")
    return dict(payload)

analytics_policy = {"allowed_fields": {"case_id", "representation", "queue"},
                    "requires_redaction": True}
assert allow_sink_payload({"case_id": "case-47", "representation": "redacted",
                           "queue": "returns"}, analytics_policy)["queue"] == "returns"
''',
        'cost': 'Policy validation is O(f) time and O(f) copied space for f payload fields. System cost comes from duplicate storage, deletion propagation and canary scans. Track the number of copies per case and the age of the oldest undeleted derivative. An allowlist is intentionally strict: a new field causes a visible failure until a reviewer updates the sink contract.',
        'mistakes': ['Checking only the user-facing page while raw text remains in logs.', 'Deleting source tickets but retaining derived embeddings indefinitely.', 'Treating a stable pseudonym as anonymous data.', 'Adding a sink without an allowlist and canary test.'],
        'related': [N + 'pii-detection-and-redaction-boundary', N + 'privacy-safe-ticket-pipeline-project', N + 'text-serving-contract', N + 'support-entity-extraction-project', 'privacy-aware-ml/privacy-aware-ml-tutorial'],
    },
    {
        'path': N + 'privacy-safe-ticket-pipeline-project',
        'title': 'Project: enforce a privacy-safe support-text pipeline',
        'module': P, 'project': True,
        'summary': 'Route support text through detection, redaction, classification and deletion controls with a testable contract for every data sink.',
        'sections': [
            ('Define the path and owner', 'A customer submits a ticket that may contain an email, address and order reference. The support desk requires the original inside a restricted case system; analytics and model evaluation receive only approved representations. List every sink, purpose, access role and retention window. Assign an owner to changes in the sink list. Do not begin by training a detector: first remove needless copies of raw text.'),
            ('Build the redaction boundary', 'Capture original text in the authorized store, run structured patterns and a reviewed contextual span detector, resolve overlaps, then create a redacted representation. Version the detector and offset policy. Quarantine a case if detection fails before an unrestricted sink. Test examples with mixed scripts, combining marks, several addresses and a false-positive product code. [[natural-language-processing/pii-detection-and-redaction-boundary|The redaction contract]] describes exact offsets and replacements.'),
            ('Gate every output', 'Enforce field allowlists at analytics, search, debugging and training-export boundaries. Put synthetic canary values in a controlled ticket and verify they appear only where originals are authorized. Run deletion end to end, including caches, indexes and derived datasets; retain an audit of deletion completion without retaining the deleted text. [[natural-language-processing/redaction-audit-and-retention|Sink audit and retention]] supplies the test matrix.'),
            ('Measure useful and safe behavior', 'Report PII recall by type on reviewed data, false redaction rate, failed-closed volume, queue-routing quality and deletion lag. Sample production failures under restricted access. A redaction policy that destroys every order reference may satisfy a leak check but break support. Keep the order ID only in the restricted workflow or replace it with a scoped surrogate where needed. Release detector, classifier and sink policy as one reviewed bundle with a rollback plan.'),
        ],
        'code': '''def route_ticket_payload(case_id, original_text, redacted_text, sink_policies):
    if not case_id or not original_text or not redacted_text:
        raise ValueError("case and both representations are required")
    outbound = {}
    for sink_name, policy in sink_policies.items():
        if policy == "restricted-original":
            outbound[sink_name] = {"case_id": case_id, "text": original_text,
                                   "representation": "original"}
        elif policy == "redacted-only":
            outbound[sink_name] = {"case_id": case_id, "text": redacted_text,
                                   "representation": "redacted"}
        else:
            raise ValueError("unknown sink policy")
    return outbound

delivery = route_ticket_payload("case-47", "Email mila@local.test",
    "Email [EMAIL]", {"case_store": "restricted-original", "analytics": "redacted-only"})
assert delivery["analytics"]["text"] == "Email [EMAIL]"
''',
        'cost': 'Routing copies each representation once per configured sink, so local work is O(s·n) in the worst case for s sinks and n text characters. Actual cost includes detector inference, protected storage, deletion propagation and restricted review. Measure p95 intake latency alongside leak findings and deletion lag. For large fan-out, avoid needless payload duplication, but never replace explicit sink policies with an implicit shared raw event.',
        'mistakes': ['Sending a raw event to all subscribers and relying on each to redact it.', 'Keeping originals in broad analytics because support needs originals elsewhere.', 'Treating canary tests as a substitute for reviewed PII recall.', 'Forgetting caches and vector indexes during deletion.'],
        'related': [N + 'pii-detection-and-redaction-boundary', N + 'redaction-audit-and-retention', N + 'support-entity-extraction-project', N + 'text-serving-contract', 'privacy-aware-ml/privacy-aware-ml-tutorial'],
    },
]

crosslinks = [
    (N + 'span-offset-annotation', N + 'coreference-chains-and-mention-identity'),
    (N + 'entity-decoding-and-span-evaluation', N + 'relation-extraction-provenance'),
    (N + 'support-entity-extraction-project', N + 'entity-relation-ledger-project'),
    (N + 'unicode-tokenization-boundary', N + 'pii-detection-and-redaction-boundary'),
    (N + 'text-serving-contract', N + 'privacy-safe-ticket-pipeline-project'),
    (N + 'coreference-chains-and-mention-identity', N + 'relation-extraction-provenance'),
    (N + 'relation-extraction-provenance', N + 'entity-relation-ledger-project'),
    (N + 'pii-detection-and-redaction-boundary', N + 'redaction-audit-and-retention'),
    (N + 'redaction-audit-and-retention', N + 'privacy-safe-ticket-pipeline-project'),
]

if __name__ == '__main__':
    publish(lessons, (D, P), crosslinks,
            'aitrove-nlp-relations-redaction-import-20261006.json', 4720,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
