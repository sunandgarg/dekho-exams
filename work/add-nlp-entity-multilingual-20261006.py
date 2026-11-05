"""Add two applied NLP learning paths to the local catalog."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
entity = 'Entity extraction and sequence labels'
multi = 'Multilingual text operations'

lessons = [
    {
        'path': N + 'bio-labels-and-subword-alignment',
        'title': 'BIO labels and subword alignment for entity extraction',
        'module': entity, 'project': False,
        'summary': 'A token classifier can report high accuracy while losing the exact order number a support agent needs. Define span and subword ownership before training.',
        'sections': [
            ('The annotation is a span, not a token list', 'A return request may contain “order AX-47” in a longer sentence. Store the original message, the entity type, and half-open character offsets that select AX-47. Token labels are a derived training view. They depend on the tokenizer version, which means they can change when vocabulary or normalization changes even though the human annotation did not. Keep the character span as the durable record. [[natural-language-processing/span-offset-annotation|Span-offset annotation]] explains the boundary contract; [[natural-language-processing/unicode-tokenization-boundary|Unicode and tokenization]] covers why a display character and a code-point offset need careful handling.'),
            ('BIO transition rules', 'B-ORDER begins an order identifier, I-ORDER continues it, and O means that the token is outside any tracked span. An I-ORDER after O is malformed under a strict BIO contract. An I-ADDRESS after B-ORDER is malformed too. Choose a policy: reject invalid labels during dataset intake, or repair them at inference with a documented decoder. Silent repair during training hides annotation defects. Adjacent entities of the same type need a fresh B tag. Otherwise two order identifiers can collapse into one prediction.'),
            ('Subwords and ignored positions', 'A tokenizer may split AX-47 into several pieces. If the annotation is word-level, assign its label to the first subword and mark the remaining pieces as ignored for loss and metric calculation, or adopt a full-subword labeling policy and keep it consistent everywhere. Special tokens and padding also need ignored targets. The ignored value is a training convention, not an entity class. Record tokenizer digest, label map, alignment policy, maximum length and truncation policy with each trained checkpoint. Recompute derived labels when that bundle changes.'),
            ('Audit the boundary cases', 'Create a small fixed set covering punctuation attached to IDs, two adjacent IDs, mixed scripts, whitespace-only messages, truncated tails and spans ending at the last character. Check that every training label can be projected back to the exact original substring. A row that cannot round-trip should be quarantined. This is more useful than a larger set of easy examples. Feed the resulting labels through [[natural-language-processing/entity-decoding-and-span-evaluation|span decoding and evaluation]] before using them in [[natural-language-processing/support-entity-extraction-project|the extraction project]].'),
        ],
        'code': '''def align_first_subword(word_labels, subword_to_word):
    aligned = []
    previous_word = None
    for word_index in subword_to_word:
        if word_index is None:
            aligned.append(-100)
        elif word_index != previous_word:
            if not 0 <= word_index < len(word_labels):
                raise ValueError("subword points outside the annotated words")
            aligned.append(word_labels[word_index])
        else:
            aligned.append(-100)
        previous_word = word_index
    return aligned

order_labels = ["O", "B-ORDER", "O"]
piece_owners = [None, 0, 1, 1, 2, None]
assert align_first_subword(order_labels, piece_owners) == [
    -100, "O", "B-ORDER", -100, "O", -100
]
''',
        'cost': 'Alignment is O(t) time and O(t) output space for t subword positions. Training memory is governed mainly by model activations and sequence length; doubling the maximum length can increase attention work roughly fourfold for full attention. Truncation can erase a labeled span, so report the discarded-span rate and reject or window those rows. At serving time, tokenization and offset mapping must use the same version as training.',
        'mistakes': ['Treating a continuation subword as a second entity occurrence.', 'Scoring ignored positions as if they were O labels.', 'Normalizing text after offsets have been recorded without rebuilding the alignment.', 'Allowing an illegal I tag to pass through the training set silently.'],
        'related': [N + 'span-offset-annotation', N + 'unicode-tokenization-boundary', N + 'entity-decoding-and-span-evaluation', N + 'support-entity-extraction-project', N + 'corpus-identity-and-label-policy'],
    },
    {
        'path': N + 'entity-decoding-and-span-evaluation',
        'title': 'Decode entities and evaluate exact spans, not token accuracy',
        'module': entity, 'project': False,
        'summary': 'A model that tags most words O can look excellent while failing every entity request. Decode spans on the original text and score what downstream code consumes.',
        'sections': [
            ('Decode against the source message', 'The model emits labels over tokens or subwords. The consumer needs typed character spans. Walk the ordered token offsets; open a span on B-TYPE, extend it only on I-TYPE of the same type, and close it on O or a new B. Validate that offsets are monotonic and inside the unmodified source string. Store start inclusive and end exclusive. This avoids punctuation guesses when extracting “ZX-47,” an address with a combining mark, or a reference followed by a newline. [[natural-language-processing/bio-labels-and-subword-alignment|BIO alignment]] determines which subword predictions are eligible for decoding.'),
            ('Count the right errors', 'Compare predicted and reviewed triples of type, start, and end. Exact match rewards only a correct label with both boundaries correct. Count true positives, false positives and false negatives across the evaluation set before calculating micro precision and recall. Also report per-type and per-language recall. Token accuracy and partial overlap can be useful diagnostics, but neither should be the release gate if the downstream system copies exact substrings into a case record. Boundary errors are operational errors.'),
            ('Abstention and overlap', 'Some entity types legitimately overlap: a shipping address may contain a postal code. A flat BIO sequence cannot represent both simultaneously. Either define a single priority type, train separate heads, or use a span model. The choice belongs in the annotation policy. Confidence needs calibration at the extracted-span level if low-confidence entities trigger manual review. The score of one token alone is a poor proxy for a multi-token span. See [[natural-language-processing/classification-slices-and-abstention|classification slices and abstention]] for a related release boundary.'),
            ('Make failure review reproducible', 'Keep an immutable evaluation manifest with message identity, language slice, annotation version, tokenizer version and model digest. For each failure, show the original text with gold and predicted offsets; do not log raw personal data into a general dashboard. Separately count malformed transitions, truncated spans, zero-width spans and cross-type overlaps. A changed threshold can alter precision without changing the model, so version the threshold as part of [[natural-language-processing/text-serving-contract|the serving contract]].'),
        ],
        'code': '''def exact_span_counts(gold_by_message, predicted_by_message):
    true_positive = false_positive = false_negative = 0
    message_ids = set(gold_by_message) | set(predicted_by_message)
    for message_id in message_ids:
        gold = set(gold_by_message.get(message_id, ()))
        predicted = set(predicted_by_message.get(message_id, ()))
        true_positive += len(gold & predicted)
        false_positive += len(predicted - gold)
        false_negative += len(gold - predicted)
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    return {"precision": precision, "recall": recall,
            "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0}

reviewed = {"case-47": {("ORDER", 14, 19), ("POSTCODE", 30, 36)}}
model_output = {"case-47": {("ORDER", 14, 19), ("POSTCODE", 30, 35)}}
assert exact_span_counts(reviewed, model_output)["f1"] == 0.5
''',
        'cost': 'With hashable span triples, evaluation takes O(g + p) expected time and O(g + p) space for g gold and p predicted spans. A decoder over t token offsets takes O(t) time. Report input length and throughput per language because token expansion can make one language materially slower than another. Keep sensitive text out of aggregate metric stores; retain restricted samples only for adjudication.',
        'mistakes': ['Using token accuracy as the only extraction metric.', 'Accepting a nearly correct boundary as exact match.', 'Merging adjacent same-type entities without a new B tag.', 'Reporting a single aggregate score when one rare entity type has collapsed.'],
        'related': [N + 'bio-labels-and-subword-alignment', N + 'span-offset-annotation', N + 'support-entity-extraction-project', N + 'classification-slices-and-abstention', N + 'text-serving-contract'],
    },
    {
        'path': N + 'support-entity-extraction-project',
        'title': 'Project: ship an auditable support-entity extractor',
        'module': entity, 'project': True,
        'summary': 'Build an extraction release that produces typed spans, survives tokenization changes and rejects uncertain identifiers before they enter a support workflow.',
        'sections': [
            ('The operational contract', 'The support desk receives refund messages containing an order ID, purchase date or delivery postcode. The extractor returns original-text offsets, entity type, confidence and model bundle version. It never edits an order based only on a guessed span. Define a no-entity result and an abstain result separately: the former says the model found none, while the latter says the message needs review. Match the label policy to [[natural-language-processing/corpus-identity-and-label-policy|the corpus contract]] before collecting examples.'),
            ('Build and split the corpus', 'Annotate character spans on the captured original text. Version guidelines for punctuation and copied email headers; adjudicate conflicting reviews and keep the adjudication reason. Group messages by conversation and customer, then split by capture time so repeated order IDs or copied text cannot leak across train and test. Freeze a small difficult holdout with code-switching, copied signatures and OCR-like substitutions. The split must be independent of tokenization. [[natural-language-processing/grouped-temporal-text-validation|Grouped temporal validation]] gives the reusable split rule.'),
            ('Train, decode and release', 'Derive BIO targets from the frozen span records, mask non-first subwords according to [[natural-language-processing/bio-labels-and-subword-alignment|the alignment contract]], then decode predictions against original offsets. Publish micro exact-span F1, per-type recall, false identifier rate and human-review volume. Block release if any required entity type falls below its reviewed threshold, even if aggregate F1 rises. Keep a sparse baseline for comparison; neural complexity should pay for itself with fewer costly errors. [[natural-language-processing/entity-decoding-and-span-evaluation|Exact-span evaluation]] supplies the scoring unit.'),
            ('Operate the endpoint', 'Package tokenizer files, label order, model digest, calibration data, maximum input length and abstention threshold as one version. Reject unrecognized versions and strings whose spans cannot round-trip. Return only the minimum extracted fields needed by the desk. Maintain a restricted sample review queue for production mistakes, and never train on a corrected label until its annotation version and consent policy are recorded. Connect the endpoint to [[natural-language-processing/text-serving-contract|text serving]] and keep a rollback bundle.'),
        ],
        'code': '''def validate_extraction(message, entities, allowed_types):
    validated = []
    for entity in entities:
        entity_type, start, end, extracted_text = entity
        if entity_type not in allowed_types:
            raise ValueError("unknown entity type")
        if not (0 <= start < end <= len(message)):
            raise ValueError("entity offset outside original message")
        if message[start:end] != extracted_text:
            raise ValueError("entity text does not round-trip")
        validated.append({"type": entity_type, "start": start,
                          "end": end, "text": extracted_text})
    return validated

message = "Refund order ZX-47, please."
assert validate_extraction(message, [("ORDER", 13, 18, "ZX-47")], {"ORDER"})[0]["start"] == 13
''',
        'cost': 'Validation scans e extracted entities and compares their selected substrings, for O(e + total selected characters) time and O(e) output records. Model inference usually dominates latency; measure p95 by message length and language, not only overall average. Human review has a real queue cost: estimate it from abstention rate and arrival volume before choosing a threshold. Archive evaluation summaries without unrestricted raw ticket bodies.',
        'mistakes': ['Annotating normalized text while serving offsets into the original message.', 'Counting a missing entity and an abstention as the same response.', 'Splitting copied conversations across train and test.', 'Shipping a model without its exact tokenizer and label map.'],
        'related': [N + 'bio-labels-and-subword-alignment', N + 'entity-decoding-and-span-evaluation', N + 'grouped-temporal-text-validation', N + 'text-serving-contract', N + 'multilingual-ticket-routing-project'],
    },
    {
        'path': N + 'script-profile-and-code-switching-boundary',
        'title': 'Script profiles and code-switching boundaries in text intake',
        'module': multi, 'project': False,
        'summary': 'A support message can mix Latin text, Devanagari text, product codes and emoji. Intake must preserve that mixture and avoid treating script as a language label.',
        'sections': [
            ('Script is an observation, language is an inference', 'A message such as “Return ऑर्डर ZX-47” contains Latin and Devanagari letters, but neither script count nor a keyboard setting proves the writer’s language. Loanwords, transliteration and quoted product names break simple rules. Record a script profile as an intake signal only. If routing requires a language label, use reviewed data with an explicit unknown class and an abstention path. Never discard a message because a heuristic says it is outside the supported set.'),
            ('Preserve identity and offsets', 'Store the original bytes with a decoding policy, then a decoded string used for annotation. Keep normalization choices explicit: NFC can change the number or arrangement of code points, and case folding can change string length. Do not record offsets in one representation and apply them to another. Track the transform version and keep an offset map if a normalized view is unavoidable. [[natural-language-processing/unicode-tokenization-boundary|Unicode and tokenization]] and [[natural-language-processing/span-offset-annotation|span annotations]] describe the linked contracts.'),
            ('Find where a classifier is blind', 'Evaluate at message, conversation and embedded-span levels. A language detector may return English for a sentence that contains a Hindi complaint and an English product name. Segment-level detection can help analysis, but short segments are less reliable. Review error slices for Romanized Hindi, mixed numerals, script switches near entity boundaries and pasted signatures. Keep repeated conversations together in the split. [[natural-language-processing/grouped-temporal-text-validation|Grouped temporal splits]] avoid a misleading score on near-duplicate messages.'),
            ('Decide the handoff', 'A script profile can route a message to a multilingual model or a specialist review queue. It should not authorize a high-impact action. Log the chosen route, confidence band, model version and whether a human corrected it. For an unsupported mix, respond with abstention rather than force a low-confidence class. This feeds [[natural-language-processing/multilingual-calibration-and-fallback|multilingual calibration]] and the [[natural-language-processing/multilingual-ticket-routing-project|routing project]].'),
        ],
        'code': '''import unicodedata

def script_profile(message):
    counts = {"latin": 0, "devanagari": 0, "other_letters": 0}
    for character in message:
        if not character.isalpha():
            continue
        unicode_name = unicodedata.name(character, "")
        if unicode_name.startswith("LATIN "):
            counts["latin"] += 1
        elif unicode_name.startswith("DEVANAGARI "):
            counts["devanagari"] += 1
        else:
            counts["other_letters"] += 1
    return counts

observed = script_profile("Return ऑर्डर ZX-47")
assert observed["latin"] > 0 and observed["devanagari"] > 0
''',
        'cost': 'The scan is O(n) time for n Unicode code points and O(1) counters for this fixed set of script buckets. A complete script inventory would require more buckets. Unicode name lookup adds per-character overhead; cache or batch only if profiling shows intake latency matters. Script counts are cheap compared with model inference, but their uncertainty is high. Measure routing accuracy on reviewed mixed-script messages rather than trusting the counters.',
        'mistakes': ['Equating Devanagari with Hindi or Latin with English.', 'Stripping accents or non-Latin characters before annotation.', 'Changing normalization without regenerating offset maps.', 'Treating a short mixed-script fragment as a reliable language decision.'],
        'related': [N + 'unicode-tokenization-boundary', N + 'span-offset-annotation', N + 'multilingual-calibration-and-fallback', N + 'multilingual-ticket-routing-project', N + 'grouped-temporal-text-validation'],
    },
    {
        'path': N + 'multilingual-calibration-and-fallback',
        'title': 'Calibrate multilingual text decisions and fallback routes',
        'module': multi, 'project': False,
        'summary': 'A shared classifier score is not equally trustworthy across languages. Evaluate each reviewed slice and send uncertain messages to a defined fallback.',
        'sections': [
            ('One threshold rarely serves every slice', 'A ticket router may assign the right queue to 91% of reviewed English tickets but only 62% of Romanized Hindi tickets. An aggregate score can conceal this gap if most traffic is English. Store reviewed language and script-mix slices separately from model guesses. Compare confidence against correctness within each slice, with support counts and uncertainty. Do not tune thresholds against the final test set. [[natural-language-processing/classification-slices-and-abstention|Classification slices]] gives the base measurement pattern.'),
            ('Calibrate against held-out decisions', 'Fit a calibration map or thresholds on a validation set that is separate from training and final audit data. Group messages by conversation and time before splitting; otherwise repeated phrasing gives optimistic probabilities. Estimate coverage, selective accuracy, wrong-queue cost and human-review volume for each candidate threshold. A threshold is part of the deployed decision rule, so a threshold change requires review even when weights remain the same. [[natural-language-processing/grouped-temporal-text-validation|Grouped temporal validation]] defines the separation.'),
            ('Choose the safe branch', 'A route can be automatic only when the score and slice policy permit it. Otherwise send to a specialist queue with the original text and a reason code, such as unsupported language mix or low margin between queues. Unknown language is not the same as low confidence; a message can be confidently misclassified when the model has never seen its dialect. Add an out-of-distribution review sample and monitor correction rates after release. The intake hints in [[natural-language-processing/script-profile-and-code-switching-boundary|script profiling]] may select a review workflow, but they must not masquerade as a validated language detector.'),
            ('Monitor the moving distribution', 'Track traffic counts, automatic coverage, error on reviewed samples and backlog by language and script slice. A sudden rise in mixed-script tickets may reflect a campaign, a product launch or a changed input channel. Sample some high-confidence auto-routes for review; otherwise you only observe labels for abstained tickets and underestimate errors. Freeze the label taxonomy and model bundle in [[natural-language-processing/text-serving-contract|the serving contract]].'),
        ],
        'code': '''def route_with_abstention(scores, thresholds, reviewed_slice):
    if not scores:
        return "manual-review", "no-scores"
    selected_queue = max(scores, key=scores.get)
    threshold = thresholds.get(reviewed_slice)
    if threshold is None:
        return "manual-review", "unsupported-slice"
    if scores[selected_queue] < threshold:
        return "manual-review", "below-threshold"
    return selected_queue, "automatic"

queue_scores = {"returns": 0.78, "billing": 0.13, "delivery": 0.09}
assert route_with_abstention(queue_scores, {"mixed-reviewed": 0.82}, "mixed-reviewed") == (
    "manual-review", "below-threshold"
)
''',
        'cost': 'Selecting the highest score is O(k) time for k queues and O(1) extra space. Calibration is an offline fit; serving a threshold lookup is constant time. The expensive part is review capacity: expected manual cases equal arrival volume multiplied by abstention rate. Report that forecast by slice, then compare it with the observed queue. Avoid very fine slice thresholds when support is too small; use a broader fallback until more reviewed examples exist.',
        'mistakes': ['Treating raw softmax output as calibrated probability.', 'Optimizing every threshold on the final audit holdout.', 'Assuming a high score proves the message is in a supported language.', 'Measuring accuracy only on automatically accepted tickets.'],
        'related': [N + 'classification-slices-and-abstention', N + 'script-profile-and-code-switching-boundary', N + 'multilingual-ticket-routing-project', N + 'grouped-temporal-text-validation', N + 'text-serving-contract'],
    },
    {
        'path': N + 'multilingual-ticket-routing-project',
        'title': 'Project: route multilingual tickets with measured abstention',
        'module': multi, 'project': True,
        'summary': 'Ship a support router that keeps mixed-language input intact, measures each reviewed slice and sends uncertain requests to a staffed queue.',
        'sections': [
            ('Define the decision first', 'The endpoint chooses returns, billing or delivery for a support ticket. It may also return manual-review with a reason. A case does not disappear when language is unknown. Capture the original message, conversation identity, arrival time, channel and reviewed queue. Add a separate reviewed language and script-mix label for evaluation; never infer a gold language from the model’s own prediction. Record who can see raw ticket text and where it is retained.'),
            ('Prepare a hard audit set', 'Keep conversations, copied replies and repeated product IDs in one split. Reserve recent messages as the final audit. Within that set, ask reviewers to identify Romanized Hindi, mixed Devanagari and English, pasted English signatures, emoji-heavy short tickets and unsupported languages. The audit needs enough examples in each slice to support a claim; if it does not, report uncertainty and route that slice for review. Use [[natural-language-processing/script-profile-and-code-switching-boundary|script profiling]] only as an observable input characteristic.'),
            ('Compare candidate systems', 'Train a sparse baseline and a multilingual model against the same split and taxonomy. Compare per-queue recall, wrong-queue cost, automatic coverage and reviewed-slice errors. A more complex model earns deployment only if it improves the operational decision after its latency and review costs are counted. Tune thresholds on validation data, then freeze them before final audit. Follow [[natural-language-processing/multilingual-calibration-and-fallback|calibration and fallback]] rather than selecting a single score that flatters the average.'),
            ('Release and keep watching', 'The serving bundle must identify tokenizer, model, label order, thresholds and policy version. For every decision, store an audit record without exposing raw text to general logs. Review a random sample of confident automatic routes and all abstentions; otherwise correction data is selected by the old policy. Track shift in traffic composition and staff queue time. If a slice degrades, lower automatic coverage for that slice and roll back the bundle when needed. Connect this project to [[natural-language-processing/ticket-routing-project|the first ticket-routing project]] and [[natural-language-processing/text-serving-contract|the serving contract]].'),
        ],
        'code': '''def audit_routing(decisions):
    by_slice = {}
    for decision in decisions:
        reviewed_slice = decision["reviewed_slice"]
        stats = by_slice.setdefault(reviewed_slice, {"total": 0, "automatic": 0, "correct": 0})
        stats["total"] += 1
        if decision["reason"] == "automatic":
            stats["automatic"] += 1
            stats["correct"] += decision["predicted_queue"] == decision["reviewed_queue"]
    return {reviewed_slice: {
        "coverage": stats["automatic"] / stats["total"],
        "selective_accuracy": stats["correct"] / stats["automatic"] if stats["automatic"] else None,
        "reviewed_cases": stats["total"],
    } for reviewed_slice, stats in by_slice.items()}

audit_rows = [
    {"reviewed_slice": "mixed", "reason": "automatic", "predicted_queue": "returns", "reviewed_queue": "returns"},
    {"reviewed_slice": "mixed", "reason": "below-threshold", "predicted_queue": None, "reviewed_queue": "billing"},
]
assert audit_routing(audit_rows)["mixed"]["coverage"] == 0.5
''',
        'cost': 'The audit pass is O(n) time and O(s) space for n reviewed decisions and s slices. Model inference and staff review dominate live cost; report p95 latency per script mix and expected review cases per hour. Selective accuracy excludes abstentions by definition, so publish coverage next to it. A slice with no automatic decisions has undefined selective accuracy, not a perfect score.',
        'mistakes': ['Using model-predicted language as the evaluation ground truth.', 'Reporting selective accuracy without coverage.', 'Allowing automated routing for an unsupported slice because its score is high.', 'Learning only from abstained tickets and missing confident errors.'],
        'related': [N + 'script-profile-and-code-switching-boundary', N + 'multilingual-calibration-and-fallback', N + 'ticket-routing-project', N + 'text-serving-contract', N + 'support-entity-extraction-project'],
    },
]

crosslinks = [
    (N + 'span-offset-annotation', N + 'bio-labels-and-subword-alignment'),
    (N + 'unicode-tokenization-boundary', N + 'script-profile-and-code-switching-boundary'),
    (N + 'corpus-identity-and-label-policy', N + 'support-entity-extraction-project'),
    (N + 'grouped-temporal-text-validation', N + 'multilingual-ticket-routing-project'),
    (N + 'classification-slices-and-abstention', N + 'multilingual-calibration-and-fallback'),
    (N + 'text-serving-contract', N + 'support-entity-extraction-project'),
    (N + 'ticket-routing-project', N + 'multilingual-ticket-routing-project'),
    (N + 'bio-labels-and-subword-alignment', N + 'entity-decoding-and-span-evaluation'),
    (N + 'entity-decoding-and-span-evaluation', N + 'support-entity-extraction-project'),
    (N + 'script-profile-and-code-switching-boundary', N + 'multilingual-calibration-and-fallback'),
    (N + 'multilingual-calibration-and-fallback', N + 'multilingual-ticket-routing-project'),
]

if __name__ == '__main__':
    publish(lessons, (entity, multi), crosslinks,
            'aitrove-nlp-entity-multilingual-import-20261006.json', 4700,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
