"""Add original self-supervised representation learning lessons."""
from ml_fixture_writer_20261005 import publish_batch

lessons = []


def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='machine-learning/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))


add('self-supervised-objective-and-view-contract',
    'Self-supervised objectives and valid views',
    'A pretext task draws its training signal from recorded inputs. Its views must preserve the facts needed by the later decision.', [
    ('Start at the decision', 'A warehouse model predicts whether a parcel image needs manual damage review. Unlabeled photographs are plentiful; confirmed damage labels are scarce. Pretraining may teach an encoder useful visual structure, but the goal is better review decisions on later parcels, not a low pretext loss. Define the review clock, parcel identity and target before creating views. [[machine-learning/pretrained-encoder-target-contract|The target contract]] keeps the downstream test honest.'),
    ('Write an invariance rule', 'Two crops of one parcel can form a positive pair only when each retains evidence relevant to damage. A crop that removes a crushed corner changes the answer, so forcing its embedding to match a full photograph can teach the model to ignore the defect. Background color may be harmless for one camera but carry a site cue for another. Inspect pairs by damage type and depot rather than accepting a generic augmentation menu.'),
    ('Separate identity from similarity', 'Two photographs of the same parcel are related, yet their relationship can be weaker than two views of the same photograph when a handler rotates or repacks the parcel. Persist parcel IDs, capture time and transformation settings with every pair. This lets auditors distinguish actual invariance from memorized scanner marks. [[machine-learning/group-and-time-validation|Group and time splits]] must keep one parcel together.'),
    ('Budget the unlabeled pool', 'Unlabeled does not mean unrestricted. Remove unusable images, enforce retention and consent rules, and record the collection period. A pool dominated by one depot can yield a polished pretext metric and poor transfer elsewhere. Compare the later test distribution before paying for long pretraining runs.'),
    ('Use a small visual audit first', 'Generate a fixed sample of paired views and ask whether damage evidence survives in both. A simple metadata gate catches known destructive crops; humans still need to inspect hard cases. Only then compare contrastive and masked objectives. [[machine-learning/contrastive-pairs-and-false-negatives|Pair construction]] and [[machine-learning/masked-reconstruction-target-design|masking]] impose different invariances.')],
    '''view_pairs = [
    {"parcel_id": "dock-47", "left_has_damage": True, "right_has_damage": True,
     "left_capture": "frame-47a", "right_capture": "frame-47b"},
    {"parcel_id": "dock-62", "left_has_damage": True, "right_has_damage": False,
     "left_capture": "frame-62a", "right_capture": "crop-62a"},
]

def eligible_pairs(pairs):
    accepted, rejected = [], []
    for pair in pairs:
        if pair["left_has_damage"] != pair["right_has_damage"]:
            rejected.append(pair["parcel_id"])
        else:
            accepted.append((pair["left_capture"], pair["right_capture"]))
    return accepted, rejected

accepted, rejected = eligible_pairs(view_pairs)
assert accepted == [("frame-47a", "frame-47b")]
assert rejected == ["dock-62"]''',
    'The metadata check costs O(P) time for P pairs and O(P) output storage. Producing two image views roughly doubles augmentation work and may double encoder passes per batch. The expensive check is semantic: evidence survival needs sampled human review and slice-specific failure counts.',
    ['Do not treat every random crop as label-preserving.', 'Do not place different views of one parcel across train and test.', 'Do not equate improved pretext loss with improved damage decisions.'],
    ['machine-learning/contrastive-pairs-and-false-negatives','machine-learning/masked-reconstruction-target-design','machine-learning/representation-collapse-and-linear-probe','machine-learning/self-supervised-pretraining-release-project'])


add('masked-reconstruction-target-design',
    'Masked reconstruction targets and shortcut checks',
    'Masked learning predicts hidden input pieces from visible context; target choice and mask placement decide whether the encoder learns useful structure or an easy shortcut.', [
    ('Choose the prediction unit', 'An image can be divided into patches, a sensor trace into windows, or a transaction row into fields. A decoder predicts withheld units from the visible remainder. For parcel photos, tiny missing patches may be filled from nearby pixels without learning box geometry. Larger missing regions require more context but can erase the very damage signal the downstream task needs. Tune mask size against transfer quality, not reconstruction appearance alone.'),
    ('Keep hidden content hidden', 'A masked field must not re-enter through a duplicate column, deterministic checksum or preprocessing statistic fitted on the whole row. The example hides a numeric sensor field and checks that the visible packet has no copied target. In a learned model, the encoder and decoder interfaces should make the same separation explicit. [[machine-learning/prediction-time-feature-availability|Feature availability]] matters again at downstream use.'),
    ('Separate the reconstruction head', 'The reconstruction decoder can be useful during pretraining without being part of serving. Keep the encoder artifact and its preprocessing manifest; do not assume a visually attractive reconstruction yields discriminative embeddings. A frozen probe and fine-tuning comparison are stronger evidence. [[machine-learning/representation-collapse-and-linear-probe|Probe checks]] inspect transferred features.'),
    ('Watch for task-incompatible masks', 'If a crushed seam occupies a small patch, repeatedly masking that seam while asking the encoder to treat it as predictable normal texture may blunt the feature needed for review. Stratify a labeled audit sample by defect location and mask overlap. Damage labels are used only for this development audit, never to invent pretraining targets on final-test parcels.'),
    ('Measure both loss and transfer', 'Track reconstruction error by patch type, site and camera, then test the frozen representation on later labeled parcels. Hold the downstream split fixed while comparing mask policies. A lower reconstruction error can simply mean the task got easier; it is not proof that a harder business decision improved.')],
    '''sensor_rows = [
    {"parcel_id": "dock-47", "weight_g": 842, "belt_speed": 3.2},
    {"parcel_id": "dock-62", "weight_g": 915, "belt_speed": 3.8},
]

def mask_weight(records):
    training_packets = []
    for record in records:
        visible = {"parcel_id": record["parcel_id"],
                   "belt_speed": record["belt_speed"], "weight_g": None}
        training_packets.append((visible, record["weight_g"]))
    return training_packets

packets = mask_weight(sensor_rows)
assert packets[0][0]["weight_g"] is None
assert packets[0][1] == 842
assert all("weight_copy" not in visible for visible, _ in packets)''',
    'Masking N rows with F fields costs O(NF) time and storage when rows are copied. Image patch reconstruction adds decoder computation during pretraining, while an encoder-only serving path avoids that decoder. Changing mask ratio can change training cost and representation quality; benchmark both.',
    ['Do not call a copied value hidden because its original column is blank.', 'Do not optimize reconstruction loss alone.', 'Do not carry an unnecessary decoder into serving by default.'],
    ['machine-learning/self-supervised-objective-and-view-contract','machine-learning/representation-collapse-and-linear-probe','machine-learning/pretraining-corpus-boundaries-and-provenance','machine-learning/self-supervised-pretraining-release-project'])


add('contrastive-pairs-and-false-negatives',
    'Contrastive pairs, batch negatives and identity collisions',
    'Contrastive training pulls accepted views together and contrasts other views, but a batch member can be a false negative when it shows the same entity or condition.', [
    ('Define positives with care', 'For warehouse images, two valid views of one parcel can be positive. Record their parcel identity and capture interval. A later image may show a newly created tear; that view is not automatically equivalent to an earlier undamaged image. The positive rule follows the [[machine-learning/self-supervised-objective-and-view-contract|view contract]], not the filename pattern.'),
    ('Audit the denominator', 'Contrastive losses often treat other batch items as negatives. Another frame of the same parcel can therefore become a false negative and be pushed away from its sibling. Different parcels with identical damage may also be semantically close, even though instance discrimination treats them as distinct. The code removes known same-parcel collisions; it cannot discover unknown semantic collisions.'),
    ('Do not reward scanner identity', 'If positive images share a barcode or scanner watermark, the encoder can solve the pretext task using those marks while ignoring damage. Crop or redact operational identifiers when safe, and test a barcode-only baseline. If redaction removes real defect evidence, change the capture process or objective rather than claiming clean invariance.'),
    ('Use difficult negatives sparingly', 'Selecting only nearest neighbors as negatives increases the chance of choosing unlabeled examples that genuinely share the target condition. Review hard pairs and monitor false-negative rates by damage type. [[machine-learning/hard-negative-mining-and-false-negatives|Hard-negative review]] supplies an analogous retrieval failure analysis.'),
    ('Compare downstream slices', 'A useful contrastive encoder should help a frozen probe or a carefully tuned downstream model on later parcels, including rare crushed-corner cases and new depots. Evaluate against no-pretraining and masked-reconstruction baselines with the same labeled split. [[machine-learning/representation-collapse-and-linear-probe|Probe design]] makes the comparison accountable.')],
    '''batch = [
    {"view": "47-a", "parcel_id": "dock-47"},
    {"view": "47-b", "parcel_id": "dock-47"},
    {"view": "62-a", "parcel_id": "dock-62"},
    {"view": "83-a", "parcel_id": "dock-83"},
]

def safe_negative_views(anchor, candidates):
    return [candidate["view"] for candidate in candidates
            if candidate["view"] != anchor["view"]
            and candidate["parcel_id"] != anchor["parcel_id"]]

assert safe_negative_views(batch[0], batch) == ["62-a", "83-a"]
assert "47-b" not in safe_negative_views(batch[0], batch)''',
    'For B views, a naive all-pairs similarity matrix costs O(B²) time and memory before encoder work. Filtering known identity collisions can be O(B²) if done per anchor as shown; grouping by identity reduces bookkeeping cost. Large negative pools also raise review and storage costs.',
    ['Do not treat another view of the same entity as a negative.', 'Do not assume an instance-negative is semantically different.', 'Do not hide the cost of larger batches or memory queues.'],
    ['machine-learning/self-supervised-objective-and-view-contract','machine-learning/representation-collapse-and-linear-probe','machine-learning/pretraining-corpus-boundaries-and-provenance','machine-learning/self-supervised-pretraining-release-project'])


add('representation-collapse-and-linear-probe',
    'Representation collapse and frozen linear probes',
    'A low pretraining loss is insufficient; feature spread, simple downstream probes and target-slice results show whether the encoder retained information worth transferring.', [
    ('Inspect variance before training a head', 'An encoder that maps every parcel to nearly the same vector has little useful capacity, even if a training diagnostic looks stable. Check per-dimension spread on held-out unlabeled data and inspect duplicate or near-duplicate rates. This is only a diagnostic: high variance can reflect camera or depot identity rather than damage.'),
    ('Freeze the encoder for a probe', 'Fit a small linear classifier on labeled training embeddings while keeping encoder weights fixed. Tune its regularization and threshold on development data, then evaluate once on later held-out parcels. The frozen probe tests separability with little adaptation. It is not a full replacement for fine-tuning, which may recover information that a linear head cannot use. [[machine-learning/frozen-embedding-linear-probe|Probe setup]] expands the comparison.'),
    ('Compare to simple baselines', 'Use a no-pretraining encoder of the same size and a conventional feature baseline where practical. Keep label budgets identical. If the pretrained encoder wins only after seeing more labeled examples, it does not establish a label-efficiency gain. Plot performance against labeled sample count and include variation across seeds. [[machine-learning/learning-curves-and-training-size-diagnosis|Learning curves]] show the pattern.'),
    ('Test the actual slices', 'Report damage recall, false review rate and calibration by depot, package surface and rare defect. A global probe score can improve while the damaged-corner cohort regresses. Compare the same later-period parcel IDs for every candidate and preserve support counts.'),
    ('Distinguish a diagnostic from a release gate', 'The simple spread check below catches exact coordinate collapse in a toy set. It cannot prove downstream utility or fairness. Release needs a paired downstream test, provenance audit and measured serving cost. [[machine-learning/self-supervised-pretraining-release-project|The project]] combines those gates.')],
    '''embeddings = {
    "dock-47": (0.9, -0.2, 0.4),
    "dock-62": (-0.7, 0.5, 0.1),
    "dock-83": (0.2, 0.1, -0.6),
}

def coordinate_spread(vectors):
    points = list(vectors.values())
    if not points or len({len(point) for point in points}) != 1:
        raise ValueError("nonempty, equal-width vectors required")
    return tuple(max(column) - min(column) for column in zip(*points))

spread = coordinate_spread(embeddings)
assert spread == (1.6, 0.7, 1.0)
assert coordinate_spread({"one": (0.2, 0.2), "two": (0.2, 0.2)}) == (0.0, 0.0)''',
    'Computing coordinate ranges for N vectors of width D costs O(ND) time and O(D) auxiliary memory if streamed. Producing embeddings costs encoder inference over the audit set; a probe adds training cost. Exact collapse is cheap to detect, but meaningful transfer requires labeled holdouts and slice review.',
    ['Do not use feature variance as a substitute for downstream quality.', 'Do not tune the probe on the final test.', 'Do not compare candidates trained with unequal label budgets.'],
    ['machine-learning/self-supervised-objective-and-view-contract','machine-learning/masked-reconstruction-target-design','machine-learning/contrastive-pairs-and-false-negatives','machine-learning/self-supervised-pretraining-release-project'])


add('pretraining-corpus-boundaries-and-provenance',
    'Pretraining corpus boundaries and provenance audit',
    'Self-supervised training uses unlabeled records, but identities, periods and governance rules still determine whether the downstream evaluation is valid.', [
    ('Freeze the test identity list first', 'A later parcel test set must be chosen before pretraining corpus selection. If the same physical parcel contributes unlabeled images to pretraining, an identity-sensitive encoder may appear to transfer while partly recognizing that parcel. Whether transductive exposure is allowed depends on the intended deployment claim; disclose it and use a stricter inductive test for new-parcel claims. [[machine-learning/pretraining-overlap-and-provenance-audit|Overlap auditing]] formalizes the check.'),
    ('Record more than a file hash', 'A resized image and its original can have different byte hashes. Track parcel ID, shipment ID, capture timestamp, depot, camera and derived-image lineage. Exact hashes still catch duplicate files; entity keys catch harder overlaps. The code checks known IDs only and should be paired with near-duplicate image review.'),
    ('Keep every processing fit inside its boundary', 'Pixel normalization, tokenizer construction, vocabulary statistics and augmentation calibration can all learn from a corpus. State which split was used to fit each transform. If final-test images tune transforms, freeze a new untouched test or qualify the claim. [[machine-learning/group-and-time-validation|Validation design]] applies before model fitting, not after it.'),
    ('Respect availability and retention', 'Unlabeled production images can contain personal data, expired retention records or licensed material. The model card should record source, usage rights, deletion handling and derived-artifact policy. These checks are operational requirements even when the objective uses no human labels.'),
    ('Carry the manifest to release', 'Version the source query, exclusion rules, identity keys, transform settings and encoder checkpoint. A downstream score without this lineage cannot be reproduced or compared when the pool changes. Hold release if the overlap count or legal scope is unresolved. [[machine-learning/self-supervised-pretraining-release-project|The release packet]] requires a clean manifest.')],
    '''pretraining_rows = [
    {"asset": "image-47a", "parcel_id": "dock-47", "captured_day": 3},
    {"asset": "image-62a", "parcel_id": "dock-62", "captured_day": 4},
    {"asset": "image-83a", "parcel_id": "dock-83", "captured_day": 6},
]
held_out_parcels = {"dock-83", "dock-94"}

def audit_known_overlap(rows, held_out_ids):
    return sorted({row["parcel_id"] for row in rows
                   if row["parcel_id"] in held_out_ids})

overlap = audit_known_overlap(pretraining_rows, held_out_parcels)
assert overlap == ["dock-83"]
clean_corpus = [row for row in pretraining_rows
                if row["parcel_id"] not in held_out_parcels]
assert len(clean_corpus) == 2''',
    'With a hashed test-ID set, checking N pretraining records costs O(N) expected time and O(T) memory for T held-out identities. Near-duplicate matching costs more and may need embedding retrieval plus manual adjudication. Persisting lineage also adds storage, but prevents ambiguous evaluation claims.',
    ['Do not use different bytes as proof that two images show different parcels.', 'Do not fit preprocessing on final-test records unnoticed.', 'Do not call a corpus reusable without documenting its rights and retention scope.'],
    ['machine-learning/self-supervised-objective-and-view-contract','machine-learning/contrastive-pairs-and-false-negatives','machine-learning/representation-collapse-and-linear-probe','machine-learning/self-supervised-pretraining-release-project'])


add('self-supervised-pretraining-release-project',
    'Project: release review for an unlabeled parcel-image encoder',
    'A release packet connects view validity, corpus lineage, frozen transfer tests and operating cost before an unlabeled-image encoder is accepted for damage review.', [
    ('Freeze the evaluation claim', 'The decision is whether a parcel image should enter manual damage review at intake. Reserve later parcels and new-depot slices before gathering the pretraining pool. Record the amount of labeled data allowed for each candidate. The release claim concerns future parcels, so parcel identity must not cross the pretraining and final-test boundary. [[machine-learning/pretraining-corpus-boundaries-and-provenance|Corpus provenance]] provides the first gate.'),
    ('Build two pretraining candidates', 'For a contrastive candidate, review paired crops to ensure tears and crushed corners remain visible, then filter known same-parcel negatives. For a masked-reconstruction candidate, choose a mask policy that cannot be solved through copied metadata and measure its defect-overlap rate. Compare both with a no-pretraining encoder. [[machine-learning/contrastive-pairs-and-false-negatives|Pair audit]] and [[machine-learning/masked-reconstruction-target-design|mask design]] define the failure modes.'),
    ('Run a fixed downstream protocol', 'Freeze each encoder, fit a linear head on the same labeled training parcels and select thresholds on the same development set. Report per-depot recall, false review volume and confidence intervals or repeated-seed spread with support counts. Fine-tune separately if resources allow, but keep that result distinct from the frozen probe. [[machine-learning/representation-collapse-and-linear-probe|Probe evidence]] tests transfer.'),
    ('Measure serving and rollback', 'Benchmark image decoding, preprocessing and encoder inference together on the target device. Keep the existing damage-review rule available during a shadow phase, record drift in camera mix and false-review load, and state who can disable the new encoder. A smaller pretext loss is not a rollback criterion; downstream slice quality and operating cost are.'),
    ('Make a conditional decision', 'The sample packet holds release because one test parcel overlaps the pretraining corpus, despite acceptable latency and overall recall. Exclude the parcel, rerun the frozen protocol on a clean untouched set and review rare-defect slices before reconsidering. Do not erase the failed audit from the record.')],
    '''release_packet = {
    "unresolved_overlap_ids": ["dock-83"],
    "view_damage_audit_passed": True,
    "rare_defect_recall": 0.81,
    "minimum_rare_defect_recall": 0.79,
    "p95_full_path_ms": 58,
    "maximum_p95_ms": 72,
    "rollback_owner_assigned": True,
}

def review_pretraining_release(packet):
    blockers = []
    if packet["unresolved_overlap_ids"]:
        blockers.append("pretraining and final-test identity overlap")
    if not packet["view_damage_audit_passed"]:
        blockers.append("view audit failed")
    if packet["rare_defect_recall"] < packet["minimum_rare_defect_recall"]:
        blockers.append("rare-defect recall below minimum")
    if packet["p95_full_path_ms"] > packet["maximum_p95_ms"]:
        blockers.append("serving budget exceeded")
    if not packet["rollback_owner_assigned"]:
        blockers.append("rollback owner missing")
    return {"release": not blockers, "blockers": blockers}

decision = review_pretraining_release(release_packet)
assert decision["release"] is False
assert decision["blockers"] == ["pretraining and final-test identity overlap"]''',
    'The packet gate is O(K) in the number of recorded overlap IDs and O(1) for its remaining scalar checks. The release evaluation itself requires multiple encoder training runs, fixed-label probes, identity audits and target-device benchmarks. Set a compute ceiling before comparing candidates.',
    ['Do not approve a model because its pretext metric improved.', 'Do not reuse a contaminated final test after choosing a model from it.', 'Do not omit identity, rare-defect and serving-cost gates from the decision.'],
    ['machine-learning/self-supervised-objective-and-view-contract','machine-learning/masked-reconstruction-target-design','machine-learning/contrastive-pairs-and-false-negatives','machine-learning/representation-collapse-and-linear-probe','machine-learning/pretraining-corpus-boundaries-and-provenance','machine-learning/transfer-learning-release-review-project'])


publish_batch(
    lessons,
    module_title='Self-supervised representations and pretraining audits',
    module_summary='Build unlabeled-data objectives, test transferred representations and review provenance before release.',
    project_heading='Self-supervised parcel-image release project',
    crosslinks=[
        ('machine-learning/pretrained-encoder-target-contract', 'machine-learning/self-supervised-objective-and-view-contract'),
        ('machine-learning/frozen-embedding-linear-probe', 'machine-learning/representation-collapse-and-linear-probe'),
        ('machine-learning/pretraining-overlap-and-provenance-audit', 'machine-learning/pretraining-corpus-boundaries-and-provenance'),
        ('machine-learning/hard-negative-mining-and-false-negatives', 'machine-learning/contrastive-pairs-and-false-negatives'),
        ('machine-learning/transfer-learning-release-review-project', 'machine-learning/self-supervised-pretraining-release-project'),
    ],
    sort_start=6400,
)
