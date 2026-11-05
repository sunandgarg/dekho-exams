"""Add corpus-family leakage and contrastive evaluation modules to NLP."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
F = 'Corpus families and evaluation leakage'
C = 'Contrastive text evaluation'

lessons = [
    {
        'path': N + 'near-duplicate-text-families-and-review',
        'title': 'Near-duplicate text families: detect overlap without erasing meaning',
        'module': F, 'project': False,
        'summary': 'A corpus can contain revised, quoted and templated copies of one document. Group likely relatives before measuring generalization, while keeping distinct claims separate.',
        'sections': [
            ('Define the family, not just the string', 'An incident ticket may be copied into a handoff, amended after a deployment and quoted in a later support reply. Exact hashes find identical bytes but miss these relatives. Store document ID, origin ID, revision ID, quoted source spans, capture time and access policy. A text-family ID means that examples share enough origin or content that a model could memorize one while being tested on another. It does not mean their labels or factual claims are equal. [[natural-language-processing/corpus-identity-and-label-policy|Corpus identity]] supplies the provenance that a similarity score cannot recover.'),
            ('Generate candidates conservatively', 'Normalize only for candidate discovery. Token shingles and Jaccard overlap can flag edited copies, while exact hashes cheaply identify identical text. Keep the original bytes and offsets for review. A shared footer can make unrelated tickets look alike; a changed negation can make nearly identical tickets mean opposite things. Compare substantive spans, templates and source lineage before merging families. [[natural-language-processing/paraphrase-equivalence-and-hard-negatives|Paraphrase review]] asks whether meaning is preserved, a different question from whether two records should be separated during evaluation.'),
            ('Review connected components', 'Pairwise similarity is not transitive. If ticket A resembles B and B resembles C, a connected-component rule may group A with C even when their claims conflict. Use components as split-safety candidates, record the edges that joined them and review unusually large or mixed-label groups. When lineage is known, prefer it to a text threshold. A family can include conflicting versions because the split rule prevents memorization; the label policy must still evaluate each revision on its own terms.'),
            ('Measure the audit itself', 'Report exact duplicates, candidate near-duplicates, reviewer-confirmed families and cross-split family overlap. Slice by source, language, template and date. Inspect false joins, especially boilerplate-heavy documents, and missed joins after OCR or translation. [[natural-language-processing/family-aware-text-split-and-contamination|Family-aware splitting]] uses the audited IDs; the [[natural-language-processing/text-family-leakage-audit-project|project]] turns them into a release gate.'),
        ],
        'code': '''import re

def word_shingles(document_text, width=3):
    if width < 1:
        raise ValueError("width must be positive")
    tokens = re.findall(r"\\w+", document_text.casefold())
    if not tokens:
        return set()
    if len(tokens) < width:
        return {tuple(tokens)}
    return {tuple(tokens[index:index + width])
            for index in range(len(tokens) - width + 1)}

def shingle_overlap(left_text, right_text):
    left = word_shingles(left_text)
    right = word_shingles(right_text)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)

original = "Gateway west rejected retry for request 47 after timeout"
revision = "Gateway west rejected retry for request 47 after timeout again"
unrelated = "Billing north confirmed refund for invoice 82"
assert shingle_overlap(original, revision) > shingle_overlap(original, unrelated)
assert shingle_overlap("", revision) == 0.0
''',
        'cost': 'Building shingles takes O(n) time and space for n tokens. Comparing two shingle sets takes expected O(n + m) time and space, but comparing every pair in a corpus is O(d²) for d documents before token cost. Block by lineage, service or a candidate index at scale. This lexical signal neither proves shared origin nor licenses deletion of a contradictory revision.',
        'mistakes': ['Treating an exact hash as a complete near-duplicate audit.', 'Collapsing two revisions into one label when their instructions conflict.', 'Joining records only because they share a long template footer.', 'Discarding original text and offsets after normalization.'],
        'related': [N + 'family-aware-text-split-and-contamination', N + 'text-family-leakage-audit-project', N + 'corpus-identity-and-label-policy', N + 'paraphrase-cluster-transitivity-review', N + 'semantic-document-diff-and-claim-types'],
    },
    {
        'path': N + 'family-aware-text-split-and-contamination',
        'title': 'Family-aware text splits and evaluation contamination',
        'module': F, 'project': False,
        'summary': 'Assign related text records to one evaluation partition and audit every outside corpus that a model may have seen.',
        'sections': [
            ('Split at the right unit', 'A random row split is unsafe when one ticket appears as an original, a corrected export and a copied handoff. Assign the complete text family to training, validation or test. Preserve document-level labels and revision dates inside the group; sharing a family does not make every version interchangeable. [[natural-language-processing/near-duplicate-text-families-and-review|Family review]] establishes the grouping evidence. [[natural-language-processing/grouped-temporal-text-validation|Grouped temporal validation]] adds the harder requirement that a held-out event is later than the training data.'),
            ('Freeze the evaluation boundary', 'Record split policy version, family registry version, corpus snapshot and model training sources. A fixed hash of family ID gives repeatable assignment, but it does not enforce time order, language balance or incident isolation by itself. Choose the unit from the question being tested: generalization to new tickets, new incidents, new organizations or future releases may require different groups. Report how many examples and families land in each partition; a tiny minority slice can disappear under an otherwise valid split.'),
            ('Look beyond the labeled table', 'Contamination can arrive through pretraining, retrieval indexes, synthetic examples, prompt libraries or test examples used during tuning. Keep a manifest of accessible corpora and known benchmark exports. Search for exact and near-duplicate test spans in those sources, then classify exposure by where and when it occurred. A match is evidence for review, not automatic proof that the model memorized the answer. If training provenance is unavailable, state that limit in the evaluation report instead of claiming a clean split.'),
            ('Gate future refreshes', 'When a new revision joins an existing family, inherit its partition or quarantine it until the registry is corrected. Recheck every training and retrieval source before adding an evaluation set. Track cross-partition family count, near-duplicate rate and untraceable source count. The [[natural-language-processing/text-family-leakage-audit-project|leakage audit project]] includes a failed refresh that must be held before its score is reported.'),
        ],
        'code': '''import hashlib

def partition_for_family(family_id):
    if not family_id:
        raise ValueError("family_id is required")
    digest = hashlib.sha256(family_id.encode("utf-8")).digest()
    bucket = int.from_bytes(digest[:8], "big") % 100
    if bucket < 70:
        return "train"
    if bucket < 85:
        return "validation"
    return "test"

records = [
    {"document_id": "ticket-47", "family_id": "incident-west-47"},
    {"document_id": "handoff-82", "family_id": "incident-west-47"},
]
assignments = {record["document_id"]: partition_for_family(record["family_id"])
               for record in records}
assert assignments["ticket-47"] == assignments["handoff-82"]
assert partition_for_family("incident-west-47") == assignments["ticket-47"]
''',
        'cost': 'Hashing a family ID costs O(k) time for its k encoded bytes and O(1) additional application space, apart from the encoded input. Assigning d records costs O(total family-ID bytes) time and O(d) space if assignments are retained. A hash partition is deterministic, not a guarantee of temporal validity, slice balance or zero exposure to external corpora.',
        'mistakes': ['Splitting revisions of one ticket across training and test.', 'Calling a deterministic hash split temporally valid without checking dates.', 'Ignoring retrieval and synthetic corpora when auditing test exposure.', 'Moving an evaluation record into training after seeing its score.'],
        'related': [N + 'near-duplicate-text-families-and-review', N + 'text-family-leakage-audit-project', N + 'grouped-temporal-text-validation', N + 'weak-label-conflict-and-audit-splits', N + 'text-feedback-loop-and-shadow-audit'],
    },
    {
        'path': N + 'text-family-leakage-audit-project',
        'title': 'Project: audit ticket families before publishing a text classifier score',
        'module': F, 'project': True,
        'summary': 'Find copied ticket families, hold a contaminated evaluation run and report a score whose split boundary can be inspected.',
        'sections': [
            ('Define the release question', 'A support classifier is being scored on a new ticket export. The same incident appears as ticket 47, a later corrected reply and handoff 82. The evaluation should estimate performance on unseen incidents, so these records must share one family and one partition. Include an unrelated ticket that repeats the standard footer and a revision that reverses a rollback instruction. [[natural-language-processing/near-duplicate-text-families-and-review|Near-duplicate review]] identifies candidates without equating their labels.'),
            ('Build the manifest', 'Capture origin IDs, revision IDs, timestamps, access flags, export batches and source hashes. Generate lexical candidate edges, review each edge with source lineage and retain a reason for accepted or rejected family membership. Freeze a family registry and snapshot the training, validation and test manifests. A reviewer should be able to trace any scored document back to its raw record and its split decision without reading another team’s private tickets.'),
            ('Detect contamination before scoring', 'Check whether a family occurs in more than one partition. Search the training corpus, retrieval index and synthetic example store for test-family matches. Quarantine uncertain matches rather than silently deleting them. The code below tests the partition invariant; a production audit also needs source manifests and a review queue for near-duplicate candidates. [[natural-language-processing/family-aware-text-split-and-contamination|Family splitting]] prevents one known leakage path, while external-corpus checks cover the others.'),
            ('Release a bounded claim', 'Report per-family and per-document metrics, unseen-incident slice size, contamination findings and any untraceable training source. If one family crosses partitions, hold the score, repair the split and retrain before retesting. Do not present a cleaned test score from the same model if it was tuned on the old test cases. Re-run [[natural-language-processing/classification-slices-and-abstention|slice and abstention evaluation]] after the boundary is repaired.'),
        ],
        'code': '''def cross_partition_families(records):
    partitions_by_family = {}
    for record in records:
        family_id = record["family_id"]
        partition = record["partition"]
        partitions_by_family.setdefault(family_id, set()).add(partition)
    return {family_id: sorted(partitions)
            for family_id, partitions in partitions_by_family.items()
            if len(partitions) > 1}

manifest = [
    {"family_id": "incident-west-47", "partition": "train"},
    {"family_id": "incident-west-47", "partition": "test"},
    {"family_id": "billing-north-82", "partition": "test"},
]
assert cross_partition_families(manifest) == {
    "incident-west-47": ["test", "train"]}
manifest[1]["partition"] = "train"
assert cross_partition_families(manifest) == {}
''',
        'cost': 'Scanning d records takes expected O(d) time and O(f) space for f families. Sorting partitions for conflicting families adds a small per-family cost; the full corpus search for unknown near-duplicates is separate and can dominate runtime. A passing family check says nothing about missing lineage, inaccessible pretraining data or label mistakes.',
        'mistakes': ['Publishing the headline score despite a cross-partition family.', 'Deleting a conflicting record without preserving its audit trail.', 'Using the same held-out cases to tune and then certify the model.', 'Reporting document count while hiding the number of independent incident families.'],
        'related': [N + 'near-duplicate-text-families-and-review', N + 'family-aware-text-split-and-contamination', N + 'grouped-temporal-text-validation', N + 'classification-slices-and-abstention', N + 'annotation-disagreement-and-label-policy'],
    },
    {
        'path': N + 'contrast-edit-operations-and-gold-label-contract',
        'title': 'Contrastive text cases: minimal edits and gold-label contracts',
        'module': C, 'project': False,
        'summary': 'A contrast case changes a small, reviewed part of a text to test a specific model decision. Store the edit, scope and expected outcome as separate evidence.',
        'sections': [
            ('Specify the decision under test', 'A model may route “refund approved” correctly but also route “refund not approved” as approval. A contrast case changes one local condition so reviewers can inspect the decision boundary. Not every edit should flip the label: punctuation, harmless word order or a reviewed paraphrase may need the same outcome. Record task, base case ID, changed span, edit operator, original and edited gold labels, reviewer and rationale. [[natural-language-processing/predicate-argument-roles-and-negation-scope|Negation scope]] helps explain why a small token change can reverse an operational instruction.'),
            ('Control what else changes', 'A negation test should not also change service, environment and timestamp. Keep protected identifiers and evidence spans fixed unless the test explicitly concerns them. A changed number might cross a policy threshold; merely replacing 47 with 82 does not guarantee a label flip unless the policy states that boundary. Review both texts independently to avoid anchoring the new label on the original. [[natural-language-processing/quantity-span-unit-and-range-contract|Quantity extraction]] preserves the value and unit needed for threshold cases.'),
            ('Keep provenance and ambiguity', 'Store immutable base and edited text, offsets in the original representation and the annotation policy version. If the revised sentence is ambiguous, mark it unresolved rather than forcing a label. A reviewer can reject an edit if it accidentally changes two claims or creates impossible context. Cross-language or OCR edits need their own offset and normalization policies. [[natural-language-processing/span-offset-annotation|Offset annotation]] keeps a reproducible link from the review record to the changed characters.'),
            ('Measure pairs, not just examples', 'Ordinary accuracy can hide a classifier that gives the same answer to both sides of a contrast. Report base accuracy, edited accuracy and whether the relationship between predictions matches the relationship between gold labels. Slice by operator: negation, quantity, entity swap, temporal shift and paraphrase. The [[natural-language-processing/contrast-pair-consistency-and-error-taxonomy|pairwise audit]] interprets those measures; the [[natural-language-processing/runbook-contrast-release-project|project]] applies them before release.'),
        ],
        'code': '''def reviewed_edit(base_case, old_span, new_span, edited_label, reviewer_id):
    source_text = base_case["text"]
    if not old_span or source_text.count(old_span) != 1 or not reviewer_id:
        raise ValueError("edit span must be unique and reviewed")
    changed_text = source_text.replace(old_span, new_span, 1)
    if changed_text == source_text:
        raise ValueError("edit did not change the text")
    return {"base_id": base_case["case_id"], "base_label": base_case["label"],
            "edited_text": changed_text, "edited_label": edited_label,
            "old_span": old_span, "new_span": new_span,
            "reviewer_id": reviewer_id}

base = {"case_id": "runbook-47", "text": "Rollback is approved for gateway west.",
        "label": "approved"}
contrast = reviewed_edit(base, "is approved", "is not approved",
                         "blocked", "reviewer-82")
assert contrast["edited_text"] == "Rollback is not approved for gateway west."
assert contrast["base_label"] != contrast["edited_label"]
''',
        'cost': 'Counting and replacing one span scan a text of n characters, so construction is O(n) time and O(n) space for the new string. Human review dominates cost when edits must preserve realistic context and verified labels. Unique substring matching is a small demonstration; production annotation should store explicit character spans and validate them against immutable text revisions.',
        'mistakes': ['Assuming every minimal edit should reverse the label.', 'Changing multiple facts while calling the case a single-variable test.', 'Inferring the new gold label from model output.', 'Losing the base text and annotation-policy version after an edit.'],
        'related': [N + 'contrast-pair-consistency-and-error-taxonomy', N + 'runbook-contrast-release-project', N + 'predicate-argument-roles-and-negation-scope', N + 'numeric-claim-calculation-and-evidence', N + 'span-offset-annotation'],
    },
    {
        'path': N + 'contrast-pair-consistency-and-error-taxonomy',
        'title': 'Contrast-pair consistency: sensitivity, invariance and failure types',
        'module': C, 'project': False,
        'summary': 'Evaluate whether predictions change when meaning changes and remain stable when meaning does not. Pair-level results reveal failures hidden by aggregate accuracy.',
        'sections': [
            ('Separate two promises', 'A sensitivity case changes a gold decision: inserting “not” may turn approval into a block. An invariance case changes surface form while preserving the reviewed decision: “roll back” and “rollback” might be equivalent in a specific policy context. Both require human-checked labels. A model that flips every prediction appears sensitive but fails invariance; a model that never flips appears stable but misses changed meaning. [[natural-language-processing/contrast-edit-operations-and-gold-label-contract|Contrast construction]] records the intended relation for each pair.'),
            ('Score the whole pair', 'Report correctness on each side and relation correctness for the pair. Relation correctness alone is insufficient: both predictions can be wrong yet preserve a same-label relation. Conversely, if the gold labels differ and only one prediction is right, the model may still flip. Maintain separate counts for base-only error, edited-only error, both wrong with expected relation and relation failure. This makes remediation concrete: collect better negation examples, fix threshold interpretation or revisit annotation policy.'),
            ('Inspect correlated cases', 'Several edits from one base document are not independent observations. Aggregate by base case or incident as well as by edit, and keep train/test family boundaries. A large batch of trivial paraphrases should not drown out rare negation failures. Compare per-operator scores and confidence changes; a correct label with confidence collapse may still trigger a review or abstention path. [[natural-language-processing/classification-slices-and-abstention|Abstention policy]] should be tested on both members, not only on easy originals.'),
            ('Use failures as regression fixtures', 'Pin approved contrast cases by corpus revision and model version. Re-run them after data, model, prompt or retrieval changes. A failure can arise from retrieval returning an old passage rather than the classifier itself; preserve retrieved evidence and intermediate outputs for diagnosis. The [[natural-language-processing/runbook-contrast-release-project|release project]] holds a deployment if a policy-critical contrast pair fails, even when average accuracy rises.'),
        ],
        'code': '''def pair_report(contrast_pairs):
    correct_sides = 0
    correct_relations = 0
    for pair in contrast_pairs:
        correct_sides += pair["base_prediction"] == pair["base_label"]
        correct_sides += pair["edited_prediction"] == pair["edited_label"]
        gold_same = pair["base_label"] == pair["edited_label"]
        predicted_same = pair["base_prediction"] == pair["edited_prediction"]
        correct_relations += gold_same == predicted_same
    return {"side_accuracy": correct_sides / (2 * len(contrast_pairs)),
            "relation_accuracy": correct_relations / len(contrast_pairs)} if contrast_pairs else {
                "side_accuracy": None, "relation_accuracy": None}

pairs = [{"base_label": "approved", "edited_label": "blocked",
          "base_prediction": "approved", "edited_prediction": "approved"},
         {"base_label": "approved", "edited_label": "approved",
          "base_prediction": "approved", "edited_prediction": "approved"}]
assert pair_report(pairs) == {"side_accuracy": 0.75,
                             "relation_accuracy": 0.5}
assert pair_report([]) == {"side_accuracy": None, "relation_accuracy": None}
''',
        'cost': 'Scoring p pairs takes O(p) time and O(1) additional space when only aggregate counters are retained. Diagnostic slices and per-base aggregation require O(p) stored outcomes. The example treats all pairs equally; a release gate should weight policy-critical operators explicitly and report their counts rather than hide them in a single mean.',
        'mistakes': ['Calling a same-prediction pair correct when the gold decision changes.', 'Using relation accuracy alone when both sides can be wrong.', 'Counting many edits of one incident as independent test incidents.', 'Ignoring a critical negation failure because overall accuracy improved.'],
        'related': [N + 'contrast-edit-operations-and-gold-label-contract', N + 'runbook-contrast-release-project', N + 'classification-slices-and-abstention', N + 'nli-premise-hypothesis-and-evidence-contract', N + 'grouped-temporal-text-validation'],
    },
    {
        'path': N + 'runbook-contrast-release-project',
        'title': 'Project: gate a runbook answer release with contrast cases',
        'module': C, 'project': True,
        'summary': 'Create reviewed negation, threshold and paraphrase pairs for operational answers, then hold a release when a changed instruction receives the old decision.',
        'sections': [
            ('Define the operational risk', 'A runbook answer system recommends rollback actions. An old passage permits rollback after 47 minutes; a revision requires 82 minutes and adds a production-only block. Build cases that distinguish the versions and environments. Include a harmless paraphrase that should preserve the answer. The goal is not merely to raise average answer accuracy: it is to catch a system that repeats an obsolete permission when a small policy change matters. [[natural-language-processing/semantic-document-diff-and-claim-types|Semantic revision review]] establishes which claims changed.'),
            ('Freeze the contrast set', 'Store base and edited passages, user question, environment, source revision, expected decision and reviewer rationale. Include negation flips, threshold crossings, unchanged paraphrases and distractor text from another service. Keep all variants of an incident in one evaluation family. Review the expected labels without seeing model predictions. [[natural-language-processing/contrast-edit-operations-and-gold-label-contract|Edit contracts]] prevent a test from quietly changing several variables at once.'),
            ('Exercise the full answer path', 'Run retrieval and answer generation against the correct active runbook revision. Capture retrieved passage IDs, generated decision, confidence or abstention state and any citation spans used internally for verification. A model may fail because it retrieves a stale index entry, misses the negation or attaches the right answer to the wrong environment. Diagnose each layer, then re-run every pair after a fix. [[natural-language-processing/revision-dependency-invalidation-and-reindex|Dependency invalidation]] removes stale derived answers before release.'),
            ('Hold or release with evidence', 'Mark negation and production-block pairs as mandatory. A release passes only if every mandatory prediction matches its reviewed label and no required case is missing. Report operator-level pair consistency, base and edited accuracy, reviewer disputes and source-revision coverage. Keep a visible unresolved state for ambiguous cases rather than forcing an approval. [[natural-language-processing/contrast-pair-consistency-and-error-taxonomy|Pairwise reporting]] explains why the gate failed.'),
        ],
        'code': '''def runbook_release_gate(required_cases, expected_decisions, predictions):
    missing = sorted(case_id for case_id in required_cases
                     if case_id not in expected_decisions or case_id not in predictions)
    wrong = sorted(case_id for case_id in required_cases
                   if case_id in expected_decisions and case_id in predictions
                   and predictions[case_id] != expected_decisions[case_id])
    return {"state": "hold" if missing or wrong else "ready",
            "missing": missing, "wrong": wrong}

required = {"negation-47", "threshold-82", "paraphrase-91"}
expected = {"negation-47": "blocked", "threshold-82": "blocked",
            "paraphrase-91": "approved"}
predicted = {"negation-47": "blocked", "threshold-82": "approved",
             "paraphrase-91": "approved"}
assert runbook_release_gate(required, expected, predicted) == {
    "state": "hold", "missing": [], "wrong": ["threshold-82"]}
predicted["threshold-82"] = "blocked"
assert runbook_release_gate(required, expected, predicted)["state"] == "ready"
''',
        'cost': 'Checking r required cases takes expected O(r) time plus O(r log r) in the worst case for sorted failure IDs, with O(r) space for those lists. Retrieval, answer generation and human adjudication have separate costs. A passing gate covers only the reviewed cases and active source revision; monitor real traffic and repeat the audit after any policy or index change.',
        'mistakes': ['Testing only the original passage and omitting its changed counterpart.', 'Letting a correct paraphrase score offset a failed mandatory negation case.', 'Running contrast cases against an old retrieval index.', 'Marking an absent prediction as correct or silently dropping the case.'],
        'related': [N + 'contrast-edit-operations-and-gold-label-contract', N + 'contrast-pair-consistency-and-error-taxonomy', N + 'semantic-document-diff-and-claim-types', N + 'runbook-revision-impact-review-project', N + 'generated-claim-evidence-and-unanswered-state'],
    },
]

crosslinks = [
    (N + 'paraphrase-cluster-transitivity-review', N + 'near-duplicate-text-families-and-review'),
    (N + 'grouped-temporal-text-validation', N + 'family-aware-text-split-and-contamination'),
    (N + 'text-label-acquisition-project', N + 'text-family-leakage-audit-project'),
    (N + 'predicate-argument-roles-and-negation-scope', N + 'contrast-edit-operations-and-gold-label-contract'),
    (N + 'generation-evaluation-and-regression-slices', N + 'contrast-pair-consistency-and-error-taxonomy'),
    (N + 'runbook-revision-impact-review-project', N + 'runbook-contrast-release-project'),
]

if __name__ == '__main__':
    publish(lessons, (F, C), crosslinks,
            'aitrove-nlp-leakage-contrast-import-20261006.json', 4854,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
