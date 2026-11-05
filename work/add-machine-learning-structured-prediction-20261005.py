"""Add original structured-prediction tutorials and a release project."""
from ml_fixture_writer_20261005 import publish_batch

lessons = []


def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='machine-learning/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))


add('sequence-label-contract-and-token-alignment',
    'Sequence-label contracts and token alignment',
    'A token label is meaningful only when the text offsets, tokenization version and span rules agree with the annotation contract.', [
    ('Define a span in the source text', 'A claims-intake model extracts policy IDs and incident dates from adjuster notes. Store each gold field as character offsets and a type, with a rule for inclusive start and exclusive end. Word tokens are a training representation, not the source of truth. The string “Policy ZX-47” might be split into several model pieces, but the requested output remains one policy span. A change in Unicode normalization can shift offsets; version that step with the corpus.'),
    ('Pick a label scheme deliberately', 'A BIO scheme marks the beginning and inside of each entity, with O outside. It assumes flat, nonoverlapping spans; a policy ID inside a larger address field may require another representation. Declare whether adjacent same-type spans are separate and whether punctuation belongs to the entity. The tagger should reject records that cannot be expressed under the chosen scheme rather than silently dropping an annotation.'),
    ('Align subwords without multiplying evidence', 'A tokenizer may divide “ZX-47” into multiple pieces. One defensible training rule labels only the first piece and excludes the remaining pieces from loss; another propagates adjusted labels across pieces. Choose one rule and preserve a map from each piece to source offsets. Scoring must reconstruct original spans, never count three subword decisions as three separate policy IDs.'),
    ('Split by claim and event time', 'Notes from one claim often repeat the same identifiers. Put all notes for a claim in one split and reserve later claims for the final test. A random note split lets the model memorize IDs or templates. [[machine-learning/group-and-time-validation|Group and time validation]] provides the boundary.'),
    ('Audit annotation disagreement', 'Some dates are ambiguous: “next Friday” may be a mention without a resolvable calendar date. Keep span detection separate from normalization, adjudicate disagreements and retain an unknown state. Do not force every text mention into a date value. A later [[machine-learning/span-level-evaluation-and-error-taxonomy|span evaluation]] needs these rules.')],
    '''note = "Policy ZX-47 was renewed on 18 June."
gold_spans = [(7, 12, "POLICY_ID"), (28, 35, "DATE")]

def validate_spans(text, spans):
    previous_end = 0
    for start, end, field_type in sorted(spans):
        if not (0 <= previous_end <= start < end <= len(text)):
            raise ValueError("invalid or overlapping span")
        if not field_type or not text[start:end].strip():
            raise ValueError("empty field")
        previous_end = end
    return [text[start:end] for start, end, _ in spans]

assert validate_spans(note, gold_spans) == ["ZX-47", "18 June"]''',
    'Validating S sorted spans costs O(S log S) for sorting and O(S) thereafter; storing offsets costs O(S). Tokenization and encoder inference add length-dependent cost. More detailed annotation contracts raise labeling effort but prevent hidden disagreements from being counted as model errors.',
    ['Do not score raw subword labels as if they were original-text spans.', 'Do not silently discard overlapping annotations.', 'Do not random-split repeated notes from one claim.'],
    ['machine-learning/constrained-sequence-decoding','machine-learning/span-level-evaluation-and-error-taxonomy','machine-learning/structured-output-confidence-and-review','machine-learning/structured-extraction-release-project'])


add('constrained-sequence-decoding',
    'Constrained sequence decoding and valid label paths',
    'Independent token choices can form an impossible tag sequence; decoding over allowed transitions chooses a consistent path from local evidence.', [
    ('State the transition rules', 'In BIO tagging, I-DATE cannot begin a sequence or follow B-POLICY_ID. It must continue a DATE span. A local classifier may still assign I-DATE the highest score to the first token. Editing invalid predictions afterward can change boundaries unpredictably. Explicit transition constraints make the contract visible before scoring.'),
    ('Compare local and global choices', 'A linear-chain decoder adds an emission score for each token label and a transition score between neighboring labels. Viterbi-style recurrence retains the best predecessor for every possible current label. The final path can differ from per-token argmax because a slightly weaker local label may permit a much stronger valid sequence. The compact code below enumerates paths for only three tokens; production decoding uses a recurrence.'),
    ('Keep restrictions tied to the task', 'Hard constraints prevent illegal BIO transitions, but they cannot verify that a detected date is real or that a policy ID exists in the account system. An overly narrow label grammar can suppress valid unusual formats. Test unusual note templates and multilingual punctuation against the [[machine-learning/sequence-label-contract-and-token-alignment|span contract]].'),
    ('Separate decoding from probability claims', 'The score of the best path is not automatically a calibrated probability. If a reviewer needs confidence, calculate a defined sequence or span uncertainty measure and validate it on later notes. [[machine-learning/structured-output-confidence-and-review|Selective review]] handles ambiguous extractions.'),
    ('Measure latency by sequence length', 'With T tokens and K labels, a dense first-order recurrence costs O(TK²) time. Long notes or many field types can make constrained decoding material even when encoder inference dominates on short notes. Profile complete intake latency rather than quoting only neural forward time.')],
    '''from itertools import product

labels = ("O", "B-POLICY", "I-POLICY")
emissions = [
    {"O": 0.1, "B-POLICY": 0.8, "I-POLICY": 0.9},
    {"O": 0.1, "B-POLICY": 0.2, "I-POLICY": 0.9},
    {"O": 0.8, "B-POLICY": 0.1, "I-POLICY": 0.2},
]

def valid_path(path):
    return all(tag != "I-POLICY" or
               (position > 0 and path[position - 1] in {"B-POLICY", "I-POLICY"})
               for position, tag in enumerate(path))

def decode_short_sequence(scores):
    candidates = (path for path in product(labels, repeat=len(scores))
                  if valid_path(path))
    return max(candidates,
               key=lambda path: sum(scores[position][tag]
                                    for position, tag in enumerate(path)))

assert decode_short_sequence(emissions) == ("B-POLICY", "I-POLICY", "O")''',
    'The toy enumeration is O(K^T) and exists only to expose the constraint. A Viterbi recurrence is O(TK²) time, with O(TK) backpointer memory; sparse allowed transitions can lower practical work. Compute these costs in addition to tokenization and encoder latency.',
    ['Do not deploy exhaustive path enumeration for real notes.', 'Do not call the highest-scoring path probability calibrated.', 'Do not assume legal BIO syntax means the extracted field is factually valid.'],
    ['machine-learning/sequence-label-contract-and-token-alignment','machine-learning/span-level-evaluation-and-error-taxonomy','machine-learning/structured-output-confidence-and-review','machine-learning/structured-extraction-release-project'])


add('span-level-evaluation-and-error-taxonomy',
    'Span-level evaluation and extraction error taxonomy',
    'Token accuracy can hide missing or shifted entities. Evaluate exact spans, field types and the downstream action that consumes them.', [
    ('Score exact matches first', 'A predicted policy span is correct only when its start, end and field type match the adjudicated gold span under an exact-match contract. A one-character boundary shift can still be useful to a reviewer, but it is not an exact extraction. Report precision, recall and F1 by field with denominators. Do not merge unlabeled or disputed mentions into O without an annotation rule.'),
    ('Show the disagreement type', 'Break errors into missed spans, extra spans, boundary shifts, wrong type and repeated-mention confusion. For date extraction, normalization to a calendar value is a separate stage; a correct text span with a wrong normalized date must remain visible. The example counts exact matches and preserves unmatched spans for review.'),
    ('Keep token scores as diagnostics', 'Token accuracy can look high when most tokens are O. It helps identify local alignment trouble but does not answer whether the intake system found a policy ID. The correct unit is often a claim-level field: did the system retrieve the right policy identifier anywhere in the note set? State both span and claim-level results when both matter.'),
    ('Use paired and sliced comparisons', 'Evaluate two model versions on the same later claims. Break results by note length, depot, note template and OCR quality, with support counts. A decoder change can improve aggregate F1 yet lower recall on handwritten scans. [[machine-learning/constrained-sequence-decoding|Valid paths]] are only one part of quality.'),
    ('Follow the action', 'A missed incident date might delay a claim; a false policy ID could attach it to the wrong account. Set separate minimum recall or precision for each field and connect those limits to manual review volume. [[machine-learning/structured-output-confidence-and-review|Review thresholds]] decide which uncertain records need a person.')],
    '''gold = {(7, 12, "POLICY_ID"), (28, 35, "DATE")}
predicted = {(7, 12, "POLICY_ID"), (28, 34, "DATE")}

def exact_span_metrics(expected, actual):
    matched = len(expected & actual)
    precision = matched / len(actual) if actual else 0.0
    recall = matched / len(expected) if expected else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1,
            "missed": expected - actual, "extra": actual - expected}

scores = exact_span_metrics(gold, predicted)
assert scores["precision"] == 0.5
assert scores["recall"] == 0.5
assert (28, 35, "DATE") in scores["missed"]''',
    'With hashed spans, exact matching is O(G + P) expected time and O(G + P) memory for G gold and P predicted spans. Claim-level matching and adjudication cost more because repeated mentions and normalized values must be reconciled. Keep those costs visible in evaluation planning.',
    ['Do not report token accuracy as the only extraction metric.', 'Do not silently repair malformed gold labels during scoring.', 'Do not count a correctly located but wrongly typed span as exact.'],
    ['machine-learning/sequence-label-contract-and-token-alignment','machine-learning/constrained-sequence-decoding','machine-learning/structured-output-confidence-and-review','machine-learning/structured-extraction-release-project'])


add('structured-output-confidence-and-review',
    'Structured-output confidence and selective review',
    'A field extractor should route uncertain or conflicting spans to review under a measured capacity budget instead of presenting every decoded path as equally certain.', [
    ('Define the decision unit', 'The intake team may need one accepted policy ID per claim, not a probability for each token. Multiple candidate IDs, an unreadable scan or a policy mismatch can make the whole claim uncertain even when one span has a high local score. Aggregate at the field or claim level and state which mistakes the reviewer can correct.'),
    ('Calibrate on held-out development claims', 'A decoder path score is affected by note length and label transitions. It should not be read directly as a 0–1 probability. If the model offers a field confidence, compare predicted confidence bins with observed exact-match rates on development claims, then reserve later claims for final evaluation. Thresholds must be chosen before seeing final-test outcomes.'),
    ('Budget review capacity explicitly', 'A threshold that sends 40% of claims to people may exceed the daily queue. Report coverage, exact-match quality among auto-accepted claims and error rate among reviewed claims at several candidate thresholds. The code uses a declared confidence cutoff and a conflict flag; its scores are sample inputs, not calibrated model outputs.'),
    ('Guard rare failure modes', 'A high average confidence can hide errors on OCR-damaged notes, unfamiliar ID prefixes or translated text. Set a hard route-to-review rule for these conditions when evidence is too sparse to trust learned confidence. [[machine-learning/span-level-evaluation-and-error-taxonomy|Error slices]] show where exceptions are needed.'),
    ('Keep feedback out of the final test', 'Reviewer corrections can form later training data after provenance and label checks. They cannot be fed back into the same evaluation window and then treated as an independent test. Version the model, review policy and adjudication rules together for rollback.')],
    '''claim_candidates = [
    {"claim": "case-47", "confidence": 0.93, "conflicting_ids": False},
    {"claim": "case-62", "confidence": 0.78, "conflicting_ids": False},
    {"claim": "case-83", "confidence": 0.96, "conflicting_ids": True},
]

def route_claims(candidates, minimum_confidence):
    decisions = {}
    for candidate in candidates:
        decisions[candidate["claim"]] = (
            "review" if candidate["conflicting_ids"] or
            candidate["confidence"] < minimum_confidence else "auto_accept")
    return decisions

routes = route_claims(claim_candidates, 0.88)
assert routes == {"case-47": "auto_accept", "case-62": "review", "case-83": "review"}''',
    'Routing C claims costs O(C) time and O(C) output storage. Calibration and threshold selection require held-out labeled claims, while manual review imposes a capacity and turnaround cost. Budget model inference and reviewer time together; a low compute bill can hide a large queue.',
    ['Do not treat raw decoder scores as calibrated probabilities.', 'Do not pick a threshold from the untouched final test.', 'Do not ignore review capacity when proposing abstention.'],
    ['machine-learning/sequence-label-contract-and-token-alignment','machine-learning/constrained-sequence-decoding','machine-learning/span-level-evaluation-and-error-taxonomy','machine-learning/structured-extraction-release-project'])


add('structured-extraction-release-project',
    'Project: release review for claims-note field extraction',
    'A structured extraction release requires stable span annotations, valid decoding, field-level tests and a review path for uncertain claims.', [
    ('Lock the contract', 'The service extracts policy IDs and incident dates from claims notes at intake. Store original-text offsets, field types, note normalization and a rule for repeated mentions. Exclude notes whose gold annotation cannot be represented by the chosen flat-span scheme until they have been adjudicated. Keep all notes from one claim in one split and reserve later claims as an untouched test. [[machine-learning/sequence-label-contract-and-token-alignment|Alignment rules]] are versioned with the labels.'),
    ('Compare decoding choices', 'Train a local token model and a constrained sequence decoder over the same encoder emissions. Reject illegal BIO paths, but inspect whether constraints hide unusual valid formats. Do not compare a new decoder on one test cohort with an old model on another. [[machine-learning/constrained-sequence-decoding|Sequence constraints]] must be checked against the actual annotation grammar.'),
    ('Score fields and actions', 'Report exact span precision and recall per field, boundary errors, wrong-type errors and claim-level policy match. Include OCR and note-template slices with counts. A correct policy ID with an incorrect incident date is a mixed result, not a fully correct claim. [[machine-learning/span-level-evaluation-and-error-taxonomy|Span scoring]] keeps the causes distinct.'),
    ('Plan the review queue', 'Calibrate field confidence on development claims, define an auto-accept threshold and route conflicts to staff. Measure accepted coverage and false linkage risk under daily queue capacity. Test the full path from OCR through decoder and review ticket creation. [[machine-learning/structured-output-confidence-and-review|Selective review]] defines that boundary.'),
    ('Make the release call', 'The sample packet below holds release because policy-ID recall misses a declared minimum despite a manageable review queue and valid paths. Preserve the old extraction route, analyze missed OCR cases and rerun the fixed evaluation after a new candidate is trained. The final test must remain untouched for the next genuine release decision.')],
    '''release_packet = {
    "annotation_contract_versioned": True,
    "invalid_bio_paths": 0,
    "policy_id_recall": 0.89,
    "minimum_policy_id_recall": 0.92,
    "review_cases_per_day": 41,
    "review_capacity_per_day": 54,
    "full_path_p95_ms": 142,
    "maximum_p95_ms": 175,
}

def review_extraction_release(packet):
    blockers = []
    if not packet["annotation_contract_versioned"]:
        blockers.append("annotation contract missing")
    if packet["invalid_bio_paths"]:
        blockers.append("invalid output paths")
    if packet["policy_id_recall"] < packet["minimum_policy_id_recall"]:
        blockers.append("policy-ID recall below minimum")
    if packet["review_cases_per_day"] > packet["review_capacity_per_day"]:
        blockers.append("review capacity exceeded")
    if packet["full_path_p95_ms"] > packet["maximum_p95_ms"]:
        blockers.append("latency budget exceeded")
    return {"release": not blockers, "blockers": blockers}

decision = review_extraction_release(release_packet)
assert decision == {"release": False,
                    "blockers": ["policy-ID recall below minimum"]}''',
    'The packet gate is O(1). The meaningful cost lies in annotation adjudication, token-level training, O(TK²) constrained decoding per note, paired field evaluation and staff review. Profile p95 of the full OCR-to-ticket path on production-like hardware and note lengths.',
    ['Do not approve a path because BIO syntax alone is valid.', 'Do not optimize aggregate F1 while a high-cost field misses its minimum.', 'Do not promise a review route beyond staffed capacity.'],
    ['machine-learning/sequence-label-contract-and-token-alignment','machine-learning/constrained-sequence-decoding','machine-learning/span-level-evaluation-and-error-taxonomy','machine-learning/structured-output-confidence-and-review','machine-learning/group-and-time-validation'])


publish_batch(
    lessons,
    module_title='Structured prediction and field extraction',
    module_summary='Align source spans, decode legal sequences and evaluate claims-note fields at the action level.',
    project_heading='Claims-note structured extraction release project',
    crosslinks=[
        ('machine-learning/group-and-time-validation', 'machine-learning/sequence-label-contract-and-token-alignment'),
        ('machine-learning/decision-threshold-and-cost', 'machine-learning/structured-output-confidence-and-review'),
        ('machine-learning/model-inference-budget-and-device-profile', 'machine-learning/constrained-sequence-decoding'),
        ('machine-learning/multilabel-schema-and-unknown-targets', 'machine-learning/span-level-evaluation-and-error-taxonomy'),
    ],
    sort_start=6500,
)
