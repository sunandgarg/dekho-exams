"""Add low-resource language and noisy-document modules to NLP."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
L = 'Low-resource language adaptation'
O = 'Noisy OCR text and document intake'

lessons = [
    {
        'path': N + 'low-resource-label-budget-and-transfer-boundary',
        'title': 'Low-resource NLP: label budgets and transfer boundaries',
        'module': L, 'project': False,
        'summary': 'When reviewed examples are scarce, a borrowed model is a starting point. Its vocabulary, labels and failure pattern still need a local audit.',
        'sections': [
            ('Name the scarce resource', 'A language may have abundant unlabeled text but few reviewed intent labels; another may have labels yet lack a tokenizer that handles its script. Count usable examples by intent, dialect, source channel and time period before choosing transfer. Decide whether the target is routing, entity extraction or search. Those tasks need different labels and error costs. [[natural-language-processing/corpus-identity-and-label-policy|Corpus identity]] fixes the ownership and version of the examples.'),
            ('Start with a local baseline', 'Test a lexical ruleset and a multilingual pretrained model on the same frozen, native-language audit. Do not translate the audit into a high-resource language and call the result target-language accuracy. Preserve the original script, spelling and code-switching. If a model was trained on web text, verify performance on terse product complaints and local abbreviations. Record tokenizer unknowns, clipped inputs and the amount of human correction needed.'),
            ('Spend labels by failure cost', 'Allocate a fixed review budget across common traffic and rare high-impact cases. Sample uncertain predictions, but reserve some random examples to detect blind spots that uncertainty sampling misses. Keep customer and conversation groups intact across train and audit. Borrowed English labels may not map cleanly to local expressions; revise the policy with native-language reviewers before training. [[natural-language-processing/annotation-disagreement-and-label-policy|Disagreement review]] captures unresolved meaning.'),
            ('Set a reject path', 'Calibrate per-language and per-intent thresholds on reviewed data. When a rare language or script lacks evidence, return a manual route rather than forcing the nearest English intent. Report per-slice precision, recall, reject rate and review workload. [[natural-language-processing/low-resource-augmentation-and-slice-audit|Augmentation and slice audit]] addresses new examples; the [[natural-language-processing/multilingual-intent-adaptation-project|project]] puts the boundary into service.'),
        ],
        'code': '''def route_with_language_floor(prediction, reviewed_support, minimum_examples):
    if minimum_examples < 1:
        raise ValueError("minimum_examples must be positive")
    language = prediction["language"]
    if reviewed_support.get(language, 0) < minimum_examples:
        return "manual-review", "insufficient-language-audit"
    if prediction["confidence"] < prediction["threshold"]:
        return "manual-review", "low-intent-confidence"
    return prediction["intent"], "reviewed-language-route"

case = {"language": "locale-k", "intent": "refund", "confidence": 0.91,
        "threshold": 0.78}
assert route_with_language_floor(case, {"locale-k": 14}, 21)[0] == "manual-review"
''',
        'cost': 'The gate is O(1) average lookup time and space per request. Annotation cost grows with the number of language, intent and channel slices, not merely corpus size. A shared model may lower serving cost but increase review burden on underserved slices. Report that burden alongside automated accuracy and latency.',
        'mistakes': ['Calling a translated evaluation set native-language evidence.', 'Pooling all languages into one accuracy number.', 'Assuming a shared label has the same meaning across locales.', 'Auto-routing a language with too few reviewed examples.'],
        'related': [N + 'low-resource-augmentation-and-slice-audit', N + 'multilingual-intent-adaptation-project', N + 'multilingual-calibration-and-fallback', N + 'annotation-disagreement-and-label-policy', N + 'grouped-temporal-text-validation'],
    },
    {
        'path': N + 'low-resource-augmentation-and-slice-audit',
        'title': 'Low-resource augmentation: provenance, label drift and slice audit',
        'module': L, 'project': False,
        'summary': 'Synthetic variants can widen training coverage, but they cannot replace independent native-language evidence.',
        'sections': [
            ('Record origin before generation', 'Every generated sentence needs a parent example, transformation type, source language, policy version and reviewer decision. Keep all descendants of one parent in one split. Otherwise a paraphrase can sit in training while its near-identical parent sits in the audit, creating a false gain. Treat translation and back-translation as candidate generators, not proof that the original intent survived. [[natural-language-processing/paraphrase-equivalence-and-hard-negatives|Paraphrase equivalence]] explains why changed negation or amounts matter.'),
            ('Screen label preservation', 'Check protected entities, numbers, negation, modality and action target before a synthetic variant gets a label. A fluent sentence can reverse “refund not received” into “refund received.” Native-language reviewers should inspect a stratified sample, especially rare intents and mixed-script cases. Reject or relabel a variant when the intent changes. Keep synthetic and human-authored counts separate so a large generated pool does not masquerade as broad real coverage.'),
            ('Run ablations against the same audit', 'Train the baseline, transfer model and augmented model under the same held-out groups and time window. Report performance on untouched native-language messages, not only transformed examples. Break results out by dialect, script, channel and rare intent; compare false automation with manual review volume. If augmentation improves the dominant label but harms a critical rare request, stop the release or narrow the rule.'),
            ('Maintain the data boundary', 'A new label policy invalidates inherited synthetic labels until they are reviewed. Delete descendants when a parent is removed under retention policy. Track what percentage of training rows derive from each source and cap repeated variants from one customer event. [[natural-language-processing/active-learning-sampling-and-coverage|Active learning]] can direct the next human-label budget; the [[natural-language-processing/multilingual-intent-adaptation-project|applied project]] measures whether that spending helps.'),
        ],
        'code': '''def assign_grouped_split(records, held_out_parent_ids):
    result = {"train": [], "audit": []}
    for record in records:
        parent_id = record.get("parent_id", record["record_id"])
        destination = "audit" if parent_id in held_out_parent_ids else "train"
        result[destination].append(record["record_id"])
    return result

rows = [{"record_id": "case-47"},
        {"record_id": "variant-47-a", "parent_id": "case-47"},
        {"record_id": "case-82"}]
split = assign_grouped_split(rows, {"case-47"})
assert split["audit"] == ["case-47", "variant-47-a"]
''',
        'cost': 'The split pass is O(n) average time and O(n) output space for n records. Generation and native review dominate cost; multiple synthetic children from one parent add little independent evidence. Measure quality gain per reviewed parent and per serving language, including the added manual-review queue, before scaling generation.',
        'mistakes': ['Putting synthetic children and their parent in different splits.', 'Assuming fluent translated text preserved the original label.', 'Reporting only aggregate gains while a rare intent regresses.', 'Keeping generated descendants after deletion of the source example.'],
        'related': [N + 'low-resource-label-budget-and-transfer-boundary', N + 'multilingual-intent-adaptation-project', N + 'paraphrase-equivalence-and-hard-negatives', N + 'active-learning-sampling-and-coverage', N + 'grouped-temporal-text-validation'],
    },
    {
        'path': N + 'multilingual-intent-adaptation-project',
        'title': 'Project: adapt a support-intent router with scarce local labels',
        'module': L, 'project': True,
        'summary': 'Create a language-aware router that uses transfer where it helps and hands off cases without enough native-language evidence.',
        'sections': [
            ('Define the release decision', 'A support team has reviewed examples for three language slices and a small new-locale queue. The router may assign a known intent only when its language-specific audit clears a floor; otherwise it creates a manual-review item with the original message intact. An inferred intent never authorizes a payment or account action. Keep a reason code so agents know whether the handoff came from low confidence, scant evidence or a disputed label.'),
            ('Build the corpus', 'Group conversations and customers before splitting. Keep the final audit native, recent and untouched by generation. Annotate ambiguous terms with local reviewers and record disagreements. Compare a lexical baseline, a shared multilingual model and a small adapted model under one label policy. [[natural-language-processing/low-resource-label-budget-and-transfer-boundary|The transfer boundary]] sets the support floor; [[natural-language-processing/low-resource-augmentation-and-slice-audit|augmentation controls]] prevent misleading gains.'),
            ('Choose thresholds by queue cost', 'For each language and critical intent, estimate wrong-route rate against the manual-review volume produced by a threshold. Include rare billing and access cases even when their support count is low. Shadow-route traffic before automating; sample both confident and rejected cases for review. A model that saves agent time on common requests may still be unacceptable if it misroutes a rare high-cost request.'),
            ('Ship and monitor', 'Version model, tokenizer, label map and thresholds together. Show original text to authorized reviewers, not a translation-only substitute. Monitor intent precision, reject rate, false automation and queue age by language. On drift, fall back to manual routing for the affected slice rather than rolling back every language. Retain deletion and privacy controls for both original and generated training examples.'),
        ],
        'code': '''def propose_intent_route(case, audit_floor, threshold_by_language):
    language = case["language"]
    if case["reviewed_examples"] < audit_floor:
        return {"route": "manual", "reason": "audit-floor"}
    threshold = threshold_by_language.get(language)
    if threshold is None or case["score"] < threshold:
        return {"route": "manual", "reason": "uncertain"}
    return {"route": case["intent"], "reason": "reviewed-slice"}

sample = {"language": "locale-k", "reviewed_examples": 23,
          "score": 0.86, "intent": "order-status"}
assert propose_intent_route(sample, 20, {"locale-k": 0.82})["route"] == "order-status"
''',
        'cost': 'The gate is O(1) per case; model inference and human handoff dominate runtime and operating cost. Track minutes spent per manual case, not just model request latency. One shared model may be economical, but a per-language audit and reject policy are still required before it can route customer work.',
        'mistakes': ['Letting the model act on an account after classifying an intent.', 'Using translated audit text in place of native messages.', 'Setting one threshold for every language from pooled accuracy.', 'Counting synthetic variants as independent reviewed cases.'],
        'related': [N + 'low-resource-label-budget-and-transfer-boundary', N + 'low-resource-augmentation-and-slice-audit', N + 'multilingual-calibration-and-fallback', N + 'ticket-routing-project', N + 'dialogue-handoff-and-action-gates'],
    },
    {
        'path': N + 'ocr-text-geometry-and-offset-identity',
        'title': 'OCR text identity: geometry, reading order and offsets',
        'module': O, 'project': False,
        'summary': 'Extracted text is a hypothesis tied to an image region. Preserve that tie before using words in search, entity extraction or decisions.',
        'sections': [
            ('Keep the page as evidence', 'For each line or token, store document revision, page number, bounding region, OCR text and recognizer version. Reading order is not guaranteed by y-coordinate alone: columns, tables and footnotes can interleave. Preserve the image and a structured block graph; a flattened paragraph is a derived view. If an agent corrects the text, keep both OCR output and the reviewed revision. [[natural-language-processing/span-offset-annotation|Span offsets]] must refer to a named representation.'),
            ('Do not equate characters across views', 'OCR may turn “O” into “0,” omit punctuation or split a word at a line break. Downstream token offsets in corrected text cannot be applied to the OCR string without an alignment map. Record the original block IDs that produced each normalized span. For tables, keep row and column relationships rather than joining every cell into one sentence. A total beside a date should not become an invented amount-date phrase.'),
            ('Use geometry to review errors', 'Show a reviewer the source crop alongside the extracted field. A text-only correction can hide whether the wrong number came from a neighboring line. Validate page and box bounds before cropping. A rotated scan, faint print or mixed handwriting should be flagged for manual inspection when field confidence is low. The [[natural-language-processing/ocr-confidence-and-field-review|field review policy]] turns these signals into an abstain decision.'),
            ('Evaluate the downstream task', 'Character error rate is useful, but it does not tell whether a specific invoice amount or ID is wrong. Measure exact-field accuracy, misplaced spans, table association errors and correction time by document type. Keep scans from one document family in one split. The [[natural-language-processing/document-intake-ocr-project|intake project]] carries page evidence through to a reviewed field.'),
        ],
        'code': '''def make_ocr_span(page_text, start, end, page_number, box):
    if not 0 <= start < end <= len(page_text):
        raise ValueError("span falls outside OCR text")
    if page_number < 1 or len(box) != 4 or any(not 0 <= value <= 1 for value in box):
        raise ValueError("invalid page or normalized box")
    return {"text": page_text[start:end], "start": start, "end": end,
            "page": page_number, "box": tuple(box)}

span = make_ocr_span("Invoice ZX-47 total 2847", 8, 13, 2,
                     (0.14, 0.21, 0.31, 0.25))
assert span["text"] == "ZX-47" and span["page"] == 2
''',
        'cost': 'The validation and slice copy cost O(length of span) time and space. Layout analysis and image recognition dominate compute, while page crops increase evidence storage. Do not discard geometry merely to save a small metadata field; without it, reviewers cannot trace a wrong value to its source region.',
        'mistakes': ['Treating flattened OCR text as the only document representation.', 'Applying corrected-text offsets to raw OCR output.', 'Joining table cells in arbitrary reading order.', 'Approving a critical number without viewing its source crop.'],
        'related': [N + 'ocr-confidence-and-field-review', N + 'document-intake-ocr-project', N + 'span-offset-annotation', N + 'unicode-tokenization-boundary', N + 'entity-decoding-and-span-evaluation'],
    },
    {
        'path': N + 'ocr-confidence-and-field-review',
        'title': 'OCR field review: confidence, consistency and abstention',
        'module': O, 'project': False,
        'summary': 'A high line score is not a guarantee that a critical amount is right. Review policy belongs to each field and workflow.',
        'sections': [
            ('Calibrate by field and source', 'OCR systems may return confidence for words, lines or extracted fields. These are different events. A line can be readable while a table relationship is wrong; a field can have a plausible shape while the digit is mistaken. Collect reviewed examples by scan quality and document layout, then estimate field correctness at each score range. Use a separate threshold for critical values such as invoice amount or bank reference. Do not describe a raw score as a calibrated probability without evidence.'),
            ('Combine independent checks', 'Validate syntax, expected value ranges, duplicate occurrences and cross-field relationships. A checksum can reject an impossible identifier, but passing one does not prove the value was read from the right box. When two occurrences disagree, show both source crops. Never overwrite the extracted value with a guessed correction without preserving the original. [[natural-language-processing/ocr-text-geometry-and-offset-identity|Geometry and offset identity]] let a reviewer inspect the actual image.'),
            ('Route uncertainty to people', 'Return accept, review or reject with reason codes. Reject an invalid page reference or missing evidence; review low-confidence critical fields and conflicting totals. For a noncritical searchable phrase, a lower threshold may be tolerable if it cannot trigger an external action. Track reviewer changes and false accepts separately. A conservative system can be useful even when many documents need review, if it reduces transcription time without automating wrong amounts.'),
            ('Monitor incoming documents', 'Watch field accuracy, review fraction, time to resolution and error rate by template, scanner and language. New forms or rotated photos change the distribution. Shadow-test a new OCR model against the same reviewed pages before switching. A removed document should remove its extracted text, crops and downstream search records. [[natural-language-processing/document-intake-ocr-project|The intake project]] bundles these controls.'),
        ],
        'code': '''def decide_ocr_field(field, critical_thresholds):
    if not field.get("source_box") or not field.get("source_revision"):
        return "reject", "missing-source-evidence"
    if not field["syntax_valid"]:
        return "review", "invalid-format"
    threshold = critical_thresholds.get(field["kind"], 0.72)
    if field["confidence"] < threshold or field.get("conflict", False):
        return "review", "uncertain-field"
    return "accept", "reviewed-policy"

amount = {"kind": "amount", "confidence": 0.91,
          "syntax_valid": True, "source_box": (0.2, 0.3, 0.4, 0.4),
          "source_revision": "scan-47"}
assert decide_ocr_field(amount, {"amount": 0.95})[0] == "review"
''',
        'cost': 'The gate is O(1) time and space per field. Maintaining calibrated thresholds takes reviewed documents from each important layout and source slice. Human review is the main operating cost; report false accept rate against review volume, rather than claiming that a single higher threshold is always better.',
        'mistakes': ['Applying a line-level score as a field-level guarantee.', 'Accepting a high-score amount from the wrong table row.', 'Discarding original OCR output after an agent correction.', 'Setting one threshold for every field and document template.'],
        'related': [N + 'ocr-text-geometry-and-offset-identity', N + 'document-intake-ocr-project', N + 'entity-decoding-and-span-evaluation', N + 'pii-detection-and-redaction-boundary', N + 'classification-slices-and-abstention'],
    },
    {
        'path': N + 'document-intake-ocr-project',
        'title': 'Project: review OCR fields in a document-intake queue',
        'module': O, 'project': True,
        'summary': 'Build a document queue that keeps image evidence, extracted values and every correction tied to the same source revision.',
        'sections': [
            ('Define what may be automated', 'An intake service reads an uploaded invoice and proposes vendor, invoice ID and amount. It may populate a review form, but it does not approve a payment. Store a source revision for the image, block geometry, raw OCR output and corrected field. Let a reviewer open the exact crop and resolve conflicts. The final accepted value must carry the reviewer decision and original evidence reference.'),
            ('Assemble a representative audit', 'Sample different templates, scans, photos, rotated pages, low contrast and multiple languages. Have reviewers label field values and source boxes, including missing fields and wrong-row decoys. Group repeated vendor templates and near-identical documents across splits. Measure exact-field accuracy, abstention and review time; a character-level score alone misses financially important digit errors. [[natural-language-processing/ocr-text-geometry-and-offset-identity|The geometry contract]] preserves traceability.'),
            ('Implement the handoff', 'Validate OCR block bounds, extract field candidates and run syntax and consistency checks. Propose an accept only if field-specific audit policy permits it; otherwise display original crop and candidate to a reviewer. [[natural-language-processing/ocr-confidence-and-field-review|The field gate]] separates low confidence from missing source evidence. Record a correction as a new reviewed value, never as a silent mutation of raw OCR.'),
            ('Release and retire', 'Compare model versions on a frozen set before shadow rollout. Monitor errors by layout and upload channel. If a new template produces conflicting totals, route that slice to review. On source deletion, remove raw image, OCR text, crops, embeddings and derived index records under the retention policy. Keep only permitted aggregate metrics after deletion.'),
        ],
        'code': '''def record_field_review(raw_value, proposed_value, source_revision,
                        reviewer_id, decision):
    if decision not in {"accept", "correct", "reject"}:
        raise ValueError("unknown review decision")
    if not source_revision or not reviewer_id:
        raise ValueError("review requires evidence and reviewer")
    accepted = proposed_value if decision in {"accept", "correct"} else None
    return {"raw": raw_value, "accepted": accepted,
            "source_revision": source_revision, "reviewer": reviewer_id,
            "decision": decision}

review = record_field_review("2847", "2847", "scan-47", "agent-82", "accept")
assert review["accepted"] == "2847" and review["raw"] == "2847"
''',
        'cost': 'The review record is O(1) for field metadata plus O(value length) copying. Image processing, storage and human review dominate. Retaining crops alongside images adds bytes but reduces the cost of tracing a contested field. Measure correction time and false accepted amounts before optimizing extraction throughput.',
        'mistakes': ['Using OCR text alone as payment approval.', 'Overwriting raw evidence with a corrected value.', 'Auditing only clean scans from one template.', 'Deleting a source image while leaving extracted text and vectors searchable.'],
        'related': [N + 'ocr-text-geometry-and-offset-identity', N + 'ocr-confidence-and-field-review', N + 'pii-detection-and-redaction-boundary', N + 'redaction-audit-and-retention', N + 'support-entity-extraction-project'],
    },
]

crosslinks = [
    (N + 'corpus-identity-and-label-policy', N + 'low-resource-label-budget-and-transfer-boundary'),
    (N + 'active-learning-sampling-and-coverage', N + 'low-resource-augmentation-and-slice-audit'),
    (N + 'multilingual-calibration-and-fallback', N + 'multilingual-intent-adaptation-project'),
    (N + 'span-offset-annotation', N + 'ocr-text-geometry-and-offset-identity'),
    (N + 'entity-decoding-and-span-evaluation', N + 'ocr-confidence-and-field-review'),
    (N + 'redaction-audit-and-retention', N + 'document-intake-ocr-project'),
]

if __name__ == '__main__':
    publish(lessons, (L, O), crosslinks,
            'aitrove-nlp-lowresource-ocr-import-20261006.json', 4782,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
