"""Add original metric-learning and embedding retrieval lessons."""
from ml_fixture_writer_20261005 import publish_batch

lessons = []


def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='machine-learning/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))


add('embedding-pair-contract-and-identity-split',
    'Embedding pairs, identity labels and leakage-safe splits',
    'Metric learning trains a representation from similarity relationships, so the definition of a positive pair and the split unit are part of the model contract.', [
    ('Decide what “same” means', 'A component-inspection team wants to retrieve photos of the same seal defect, not every photo of the same metal part. Two images are positive only when an adjudicated defect identity matches. Shared batch number or camera station alone is not enough; those fields may correlate with a defect and create a shortcut. Record whether the target is exact defect instance, defect family or interchangeable repair procedure before generating pairs.'),
    ('Make negatives genuinely negative', 'A pair with different labels is not automatically a useful negative. One label may be missing, two defects may share a repair, or the same component may appear under different IDs after intake. Sample reviewed negatives and retain an “uncertain” state rather than forcing all unverified pairs apart. [[machine-learning/weak-label-rules-coverage-and-conflicts|Weak-label conflicts]] are relevant when IDs are assembled from several systems.'),
    ('Split by physical identity and time', 'All photographs of the same physical component must stay on one side of a train/test boundary. Otherwise near-duplicate views make held-out retrieval look better than new-component performance. If cameras or lighting change over time, keep a later-period test and report results by station. [[machine-learning/group-and-time-validation|Group and time validation]] supplies the general rule.'),
    ('Define the gallery at prediction time', 'A query image is compared with a gallery of known examples. Store gallery revision, eligibility rules, encoder version and feature extraction time. Test queries must not have their own duplicate in the gallery unless duplicate recognition is the stated product task. [[machine-learning/prediction-time-feature-availability|Feature availability]] remains a hard boundary.'),
    ('Count independent identities', 'Ten thousand nearly identical frames from one faulty part are not ten thousand independent positive examples. Report identities, source batches, positive pairs and uncertain labels separately. A per-image train/test split can produce a large metric that has little meaning for unseen equipment. [[machine-learning/metric-learning-release-project|The release review]] carries these counts.')],
    '''inspection_photos = [
    {"photo": "seal-47-front", "component": "seal-47", "defect": "cut-edge", "captured": 912},
    {"photo": "seal-47-side", "component": "seal-47", "defect": "cut-edge", "captured": 915},
    {"photo": "seal-83-front", "component": "seal-83", "defect": "surface-pit", "captured": 926},
    {"photo": "seal-91-front", "component": "seal-91", "defect": None, "captured": 937},
]

def pair_relation(first, second):
    if first["defect"] is None or second["defect"] is None:
        return "unknown"
    if first["component"] == second["component"]:
        return "same-component"  # Exclude from unseen-component evaluation.
    return "positive" if first["defect"] == second["defect"] else "negative"

assert pair_relation(inspection_photos[0], inspection_photos[1]) == "same-component"
assert pair_relation(inspection_photos[0], inspection_photos[2]) == "negative"
assert pair_relation(inspection_photos[0], inspection_photos[3]) == "unknown"''',
    'Pair classification is O(1) per candidate pair, but enumerating every pair across N photos costs O(N squared) time and storage if materialized. Keep identity metadata and sample pairs within training folds. Adjudicating ambiguous defects is often more expensive than computing distances, yet it determines whether the geometry means anything.',
    ['Do not define similarity by a field that is merely easy to collect.', 'Do not place views of one physical component in both training and test.', 'Do not turn missing defect labels into verified negatives.'],
    ['machine-learning/triplet-margin-and-normalized-embeddings','machine-learning/hard-negative-mining-and-false-negatives','machine-learning/embedding-retrieval-recall-and-collapse','machine-learning/metric-learning-release-project'])


add('triplet-margin-and-normalized-embeddings',
    'Triplet margin and normalized embedding geometry',
    'A triplet objective asks an anchor to be closer to a reviewed positive than a reviewed negative by a chosen margin in one declared distance space.', [
    ('Fix the distance convention', 'A component image encoder maps each photo to a vector. This lesson uses Euclidean distance between unit-normalized vectors; squared distance and cosine similarity would change the numeric margin and gradients. Normalize consistently at training and serving. An encoder version change invalidates stored gallery vectors unless the gallery is rebuilt. [[machine-learning/embedding-pair-contract-and-identity-split|Pair identity]] comes before choosing the loss.'),
    ('Read the loss as a constraint', 'For anchor a, positive p and negative n, triplet loss is the maximum of zero and distance(a,p) minus distance(a,n) plus margin. Zero means that triplet already meets the margin; it does not prove the full gallery is separated. A larger margin can force unnecessary distortion when defect families overlap or labels are noisy. Tune it only on development identities.'),
    ('Separate objective from retrieval quality', 'A decreasing training loss can come from repeated easy identities or collapse in one slice. Evaluate whether a new component query retrieves a correct defect-family neighbor from a realistic gallery, and inspect false matches that would trigger the wrong repair. [[machine-learning/embedding-retrieval-recall-and-collapse|Recall and collapse checks]] address that operational question.'),
    ('Use real encoder training for deployment', 'The code computes normalized two-dimensional vectors and one loss value. It is a geometry check, not a trainable neural model. A production encoder needs batching, augmentation tied to allowed transformations, checkpoint selection, and paired source/target error analysis. [[machine-learning/pretrained-encoder-target-contract|The encoder contract]] handles input and target alignment.'),
    ('Watch invariances', 'Color and lighting augmentation can help if defect identity should remain stable. It can also erase a color-specific heat mark that technicians need. Every augmentation is a claim that transformed images preserve the label. Test that claim with inspected pairs before making it part of training.')],
    '''from math import sqrt

def unit_vector(embedding):
    length = sqrt(sum(value * value for value in embedding))
    if length == 0:
        raise ValueError("zero embedding has no direction")
    return tuple(value / length for value in embedding)

def euclidean(first, second):
    return sqrt(sum((left - right) ** 2 for left, right in zip(first, second)))

anchor = unit_vector((3.0, 4.0))
positive = unit_vector((3.2, 3.8))
negative = unit_vector((-4.0, 3.0))
margin = 0.35
triplet_loss = max(0.0, euclidean(anchor, positive) - euclidean(anchor, negative) + margin)
assert len(anchor) == len(positive) == len(negative) == 2
assert triplet_loss == 0.0
assert round(euclidean(anchor, positive), 3) < round(euclidean(anchor, negative), 3)''',
    'Normalization and two distances cost O(D) time for D vector dimensions and O(D) output storage. Full encoder training costs far more and scales with triplets, image decode and backpropagation. Precomputing gallery vectors saves repeated encoder calls but requires a versioned rebuild when weights or preprocessing change.',
    ['Do not mix normalized gallery vectors with raw query vectors.', 'Do not treat zero triplet loss as proof of high retrieval recall.', 'Do not choose a margin from the final test identities.'],
    ['machine-learning/embedding-pair-contract-and-identity-split','machine-learning/hard-negative-mining-and-false-negatives','machine-learning/embedding-retrieval-recall-and-collapse','machine-learning/metric-learning-release-project'])


add('hard-negative-mining-and-false-negatives',
    'Hard-negative mining without false-negative shortcuts',
    'Hard-negative mining selects close, reviewed nonmatches for training; the closest unverified neighbor can be a mislabeled positive or a duplicate.', [
    ('Why random negatives run out', 'Once an encoder separates different part families, random unrelated photographs satisfy the margin and contribute zero triplet loss. Nearby negatives teach finer distinctions, such as edge cuts versus surface pits on similar seals. The useful comparison is difficult because of visual resemblance, not because a missing label made it appear different. [[machine-learning/triplet-margin-and-normalized-embeddings|Triplet geometry]] makes the margin visible.'),
    ('Mine inside the training boundary', 'Choose candidate negatives from training identities only, using an encoder checkpoint produced without validation or test identities. Refresh the mining pool at a declared cadence because the closest neighbors change during training. If an image pair was adjudicated only after a test failure, keep the test untouched and record that new label for a later cycle.'),
    ('Prefer semi-hard before extreme', 'A semi-hard negative is farther from the anchor than the positive but still within the margin. It violates the desired separation without being the nearest possible image. The absolute closest negative can be a duplicate, mislabeled positive or unstable outlier. Inspect that tail and cap how many pairs one identity can contribute.'),
    ('Audit false negatives', 'Review a sample of mined negatives with defect specialists. Track disagreement and the share that become positives after adjudication. Wrong negatives push equivalent repairs apart; training loss may still fall while retrieval becomes less useful. [[machine-learning/embedding-pair-contract-and-identity-split|The label contract]] must preserve uncertain relationships.'),
    ('Measure cost and coverage', 'A batch with B examples offers O(B squared) candidate comparisons. Full-gallery mining may require an index build and much more memory; approximate search can miss candidates. Record which identities and defect families supplied hard pairs, then measure new-identity retrieval by slice rather than trusting training loss alone.')],
    '''from math import sqrt

anchor = (0.0, 0.0)
positive = (0.30, 0.0)
reviewed_candidates = [
    {"photo": "seal-83", "distance": 0.46, "relation": "negative"},
    {"photo": "seal-91", "distance": 0.12, "relation": "unknown"},
    {"photo": "valve-62", "distance": 1.38, "relation": "negative"},
]

def semi_hard_negatives(candidates, positive_distance, margin):
    if margin <= 0:
        raise ValueError("positive margin required")
    return [candidate["photo"] for candidate in candidates
            if candidate["relation"] == "negative"
            and positive_distance < candidate["distance"] < positive_distance + margin]

selected = semi_hard_negatives(reviewed_candidates, sqrt(sum(value * value for value in positive)), 0.40)
assert selected == ["seal-83"]
assert "seal-91" not in selected''',
    'The filter is O(B) for B provided candidates; producing all within-batch distances is O(B squared times D) time for D dimensions and O(B squared) storage if retained. Index-based mining trades build and memory cost for faster queries. Human adjudication of close pairs is a separate cost and should be budgeted before scaling the mining process.',
    ['Do not mine negatives from validation or test identities.', 'Do not assume the nearest unverified image is a true negative.', 'Do not let one frequent identity fill most hard-negative slots.'],
    ['machine-learning/embedding-pair-contract-and-identity-split','machine-learning/triplet-margin-and-normalized-embeddings','machine-learning/embedding-retrieval-recall-and-collapse','machine-learning/exact-vs-approximate-neighbor-audit'])


add('embedding-retrieval-recall-and-collapse',
    'Embedding retrieval recall and collapse checks',
    'Evaluate an embedding against a frozen gallery and unseen queries, measuring correct-neighbor retrieval and whether the representation keeps useful spread.', [
    ('Choose the query and gallery roles', 'A held-out seal image is the query. The gallery contains eligible, versioned reference photos available when the query arrives. Define success as at least one correct defect-family reference in the first K results, not merely a close vector. Exclude the same physical component from the gallery when the product must generalize to new components. [[machine-learning/embedding-pair-contract-and-identity-split|Identity splits]] make that requirement testable.'),
    ('Report both hit rate and false match cost', 'Recall at K counts queries with a relevant neighbor in the first K. For an operational decision, also count high-scoring wrong repairs, no-match abstentions and performance by camera, defect rarity and part type. A model may raise recall by returning many uncertain neighbors while increasing manual review. [[machine-learning/selective-prediction-and-review-capacity|Selective prediction]] frames the action threshold.'),
    ('Look for collapse', 'If vectors converge to nearly the same location, triplet selection and retrieval become uninformative. Track nonduplicate pair distances, per-dimension spread and the fraction of query vectors with near-tied nearest neighbors. Low variance alone is not conclusive for every architecture; inspect it alongside recall and a random-encoder baseline.'),
    ('Keep exact search as an oracle', 'Before selecting an approximate index, brute-force distances over a manageable frozen gallery provide a reference neighbor list. The encoder can still be wrong; exact search only answers whether the index reproduces the encoder’s choices. [[machine-learning/exact-vs-approximate-neighbor-audit|The index audit]] compares those lists and full-path latency.'),
    ('Preserve version compatibility', 'Query and gallery embeddings must use the same encoder and preprocessing. A rolling model deployment can mix versions if index swap and application rollout are not coordinated. Stamp each vector, query and result with encoder and gallery versions; reject incompatible combinations or route to a matching index. [[retrieval-ai/freshness-deletion-and-index-swap|Index swap lifecycle]] covers the adjacent data path.')],
    '''from math import dist

gallery = {
    "cut-reference": {"vector": (0.12, 0.08), "defect": "edge-cut", "component": "seal-83"},
    "pit-reference": {"vector": (0.86, 0.81), "defect": "surface-pit", "component": "seal-91"},
    "wear-reference": {"vector": (0.54, 0.31), "defect": "abrasion", "component": "seal-62"},
}
queries = [
    {"vector": (0.15, 0.10), "defect": "edge-cut", "component": "seal-47"},
    {"vector": (0.82, 0.78), "defect": "surface-pit", "component": "seal-24"},
]

def exact_recall_at_one(test_queries, references):
    hits = 0
    for query in test_queries:
        eligible = [(name, item) for name, item in references.items()
                    if item["component"] != query["component"]]
        if not eligible:
            raise ValueError("empty eligible gallery")
        winner = min(eligible, key=lambda pair: dist(query["vector"], pair[1]["vector"]))
        hits += winner[1]["defect"] == query["defect"]
    return hits / len(test_queries)

assert exact_recall_at_one(queries, gallery) == 1.0''',
    'Exact retrieval costs O(Q times G times D) for Q queries, G gallery vectors and D dimensions; storage is O(G times D). An approximate index can reduce query latency but introduces its own build, memory and neighbor-recall costs. The tiny example proves only the arithmetic path, not model quality on real defect images.',
    ['Do not leave duplicates of the query component in an unseen-component gallery.', 'Do not use index agreement with exact search as the only quality metric.', 'Do not mix encoder versions between query and gallery vectors.'],
    ['machine-learning/embedding-pair-contract-and-identity-split','machine-learning/triplet-margin-and-normalized-embeddings','machine-learning/exact-vs-approximate-neighbor-audit','machine-learning/metric-learning-release-project'])


add('exact-vs-approximate-neighbor-audit',
    'Exact versus approximate nearest-neighbor audit',
    'Approximate nearest-neighbor retrieval trades some exact-neighbor agreement for latency and memory; measure that trade on the same frozen embedding gallery.', [
    ('Define two different recalls', 'Neighbor recall at K asks whether an approximate index returns the exact index’s top-K vector IDs. Task recall at K asks whether those results include a correct defect-family reference. They can move differently because the encoder’s nearest vector may itself be wrong. Report both. [[machine-learning/embedding-retrieval-recall-and-collapse|Embedding retrieval evaluation]] defines the task-level metric.'),
    ('Benchmark the actual serving shape', 'Measure index build time, resident memory, p50 and p95 query latency, and concurrent throughput on deployment hardware. Include vector loading, eligibility filtering, deletion state and any exact rerank stage. One parameter setting may be fast on a small gallery and poor after a tenfold growth in reference photos. [[machine-learning/model-inference-budget-and-device-profile|Device profiling]] sets the measurement boundary.'),
    ('Treat permissions and deletion as correctness', 'A retrieved photo may be withdrawn, superseded or restricted. Filter at the serving boundary and ensure deletion propagates to the index. If filtering removes many approximate hits, oversample before the final top K and measure recall after filtering. [[retrieval-ai/freshness-deletion-and-index-swap|Index lifecycle]] is part of correctness, not housekeeping.'),
    ('Build a paired audit', 'For each held-out query, store exact top-K IDs and approximate top-K IDs from the same gallery and encoder version. Count overlap, then compute task recall on both lists. Slice by rare defect, camera and gallery age. The code audits two small result packets; no specific indexing library is required.'),
    ('Choose an operating point, not an index name', 'Keep only candidates that meet minimum task recall, permission checks and latency budget. Among them, compare memory and rebuild time. Record the parameter setting so a future rebuild can reproduce it. [[machine-learning/metric-learning-release-project|The release project]] makes the decision explicit.')],
    '''reference_results = {
    "seal-47": ["cut-a", "cut-b", "wear-c"],
    "seal-24": ["pit-d", "pit-e", "wear-c"],
}
candidate_results = {
    "seal-47": ["cut-a", "wear-c", "cut-b"],
    "seal-24": ["wear-c", "pit-d", "pit-e"],
}

def neighbor_recall_at_k(reference, candidate, cutoff):
    if cutoff < 1 or reference.keys() != candidate.keys():
        raise ValueError("paired queries and positive cutoff required")
    fractions = []
    for query_id, exact_ids in reference.items():
        expected = set(exact_ids[:cutoff])
        observed = set(candidate[query_id][:cutoff])
        if len(expected) != cutoff:
            raise ValueError("reference list shorter than cutoff")
        fractions.append(len(expected & observed) / cutoff)
    return sum(fractions) / len(fractions)

assert neighbor_recall_at_k(reference_results, candidate_results, 2) == 0.5
assert neighbor_recall_at_k(reference_results, candidate_results, 3) == 1.0''',
    'Paired top-K overlap costs O(Q times K) expected time and O(K) temporary memory per query. Constructing the exact oracle still costs O(Q times G times D). Approximate search adds index construction, RAM and update costs that this overlap function does not measure; profile the full path before promotion.',
    ['Do not call exact-neighbor overlap task accuracy.', 'Do not compare indexes built from different gallery or encoder versions.', 'Do not measure retrieval before eligibility filtering and then claim the result is safe to serve.'],
    ['machine-learning/embedding-pair-contract-and-identity-split','machine-learning/hard-negative-mining-and-false-negatives','machine-learning/embedding-retrieval-recall-and-collapse','machine-learning/metric-learning-release-project'])


add('metric-learning-release-project',
    'Project: release review for visual part matching',
    'A visual matching release needs verified pair labels, an identity-disjoint test, retrieval quality, index quality and a safe no-match path.', [
    ('Assemble the evaluation packet', 'A workshop wants technicians to find precedent images for a photographed seal defect. Freeze the defect rubric, component identity map, camera-period split, query set, gallery snapshot and encoder version. Keep views of each physical component on one side of the split. Document which examples were uncertain or adjudicated. [[machine-learning/embedding-pair-contract-and-identity-split|The pair contract]] prevents label shortcuts.'),
    ('Train against a credible baseline', 'Compare a fixed pretrained encoder with the trained triplet encoder using the same gallery and test identities. Inspect the chosen margin, mining refresh policy and reviewed false-negative rate. A model with lower triplet loss can still retrieve the wrong defect. [[machine-learning/triplet-margin-and-normalized-embeddings|Triplet loss]] and [[machine-learning/hard-negative-mining-and-false-negatives|mining]] explain the training boundary.'),
    ('Evaluate quality in layers', 'Measure exact-search task recall at 1 and 5, high-confidence wrong-repair rate, no-match rate and rare-defect slices. Then compare the approximate index to exact search on the frozen vectors, reporting neighbor recall and task recall after permission filters. [[machine-learning/embedding-retrieval-recall-and-collapse|Task recall]] and [[machine-learning/exact-vs-approximate-neighbor-audit|index recall]] cannot be collapsed into one score.'),
    ('Test serving and rollback', 'Benchmark photo decode, encoder inference, index search, permission check and result rendering under peak load. Simulate a withdrawn reference and an encoder/gallery version mismatch. Keep a deterministic fallback that offers no unsafe repair instruction when confidence is low. [[retrieval-ai/freshness-deletion-and-index-swap|Index lifecycle]] describes the swap and deletion path.'),
    ('Record a reasoned decision', 'The sample gate below holds a candidate with a rare-defect regression even though its pooled task recall and latency pass. A later shadow period should validate logging and version coherence before a controlled rollout. Preserve previous encoder and gallery artifacts until rollback has been exercised.')],
    '''release_packet = {
    "task_recall_at_1": 0.84,
    "rare_defect_recall_at_1": 0.61,
    "exact_neighbor_recall_at_5": 0.97,
    "high_confidence_wrong_repair_rate": 0.008,
    "p95_full_path_ms": 139,
    "identity_disjoint_test": True,
    "permission_and_deletion_tested": True,
    "encoder_gallery_versions_match": True,
    "rollback_artifacts_kept": True,
}

def visual_match_release_gate(packet):
    holds = []
    if packet["task_recall_at_1"] < 0.82 or packet["rare_defect_recall_at_1"] < 0.68:
        holds.append("task recall by slice")
    if packet["exact_neighbor_recall_at_5"] < 0.95:
        holds.append("index agreement")
    if packet["high_confidence_wrong_repair_rate"] > 0.01 or packet["p95_full_path_ms"] > 145:
        holds.append("error or latency budget")
    if not all(packet[key] for key in (
        "identity_disjoint_test", "permission_and_deletion_tested",
        "encoder_gallery_versions_match", "rollback_artifacts_kept"
    )):
        holds.append("release controls")
    return "hold: " + ", ".join(holds) if holds else "eligible for shadow review"

assert visual_match_release_gate(release_packet) == "hold: task recall by slice"''',
    'The gate is O(1); gathering the packet requires annotation review, encoder training, exact and approximate retrieval, full-path benchmarks and a deletion test. The example thresholds are local acceptance rules, not universal defaults. A shadow pass can reveal serving faults but does not prove field repair outcomes.',
    ['Do not promote from training loss or pooled recall alone.', 'Do not compare an approximate index with an exact oracle built from another encoder version.', 'Do not skip no-match, permission, deletion or rollback behavior.'],
    ['machine-learning/embedding-pair-contract-and-identity-split','machine-learning/triplet-margin-and-normalized-embeddings','machine-learning/hard-negative-mining-and-false-negatives','machine-learning/embedding-retrieval-recall-and-collapse','machine-learning/exact-vs-approximate-neighbor-audit','machine-learning/ranking-release-review-project'])


publish_batch(
    lessons,
    module_title='Metric learning and embedding retrieval',
    module_summary='Define similarity, train and mine reviewed pairs, audit exact retrieval, then measure index and serving tradeoffs.',
    project_heading='Visual part-matching release review',
    crosslinks=[
        ('machine-learning/frozen-embedding-linear-probe', lessons[0]['path']),
        ('multimodal-ai/alignment-negatives-and-shared-embeddings', lessons[1]['path']),
        ('machine-learning/active-learning-uncertainty-and-diversity', lessons[2]['path']),
        ('machine-learning/nearest-neighbor-distance-and-local-support', lessons[3]['path']),
        ('retrieval-ai/freshness-deletion-and-index-swap', lessons[4]['path']),
        ('machine-learning/ranking-release-review-project', lessons[5]['path']),
    ],
    sort_start=5900,
)
