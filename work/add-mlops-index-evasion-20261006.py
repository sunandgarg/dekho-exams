"""Add embedding-index migration and inference-evasion operating lessons."""
from de_batch_publisher import publish

M = 'mlops/'
INDEX = 'Embedding index migration and retrieval release'
EVASION = 'Inference evasion monitoring and response'
lessons = [
    {
        'path': M + 'embedding-index-contract-and-rebuild-plan',
        'title': 'Embedding index migration: bind vectors, queries and source revisions',
        'module': INDEX, 'project': False,
        'summary': 'An embedding migration changes the retrieval contract, even when both indexes accept vectors of the same length.',
        'sections': [
            ('Define the contract before rebuilding', 'A repair-manual search service holds service bulletins as chunks. Its existing index uses an older embedding model; a new model changes vector meaning. Record model digest, tokenizer and preprocessing revision, vector dimension, distance metric, normalization policy, chunking revision, source snapshot and metadata filters as one index contract. A dimension match alone cannot prove compatibility. The query encoder must share the document encoder revision for the index receiving the request. [[mlops/generative-release-manifest-and-prompt-model-binding|Generative release binding]] extends that contract to the response model.'),
            ('Rebuild from stable sources', 'Take a source snapshot with document IDs and revision timestamps. Generate chunks and embeddings under the new contract, then write them to a separate collection. Preserve source IDs and chunk lineage so deleted bulletins can be removed from both collections. Count expected and indexed records by source; compare hashes of source revisions at completion. A backfill that finishes while source documents keep changing can still be stale. [[data-engineering/cdc-replay-and-deletes|Change capture]] can supply updates, but the consumer still needs a replayable checkpoint.'),
            ('Carry live updates through the handover', 'Keep the old collection serving. During backfill, either dual-write source changes to both collections or append them to a durable change log and replay them into the new collection before cutover. Put a monotonic source revision in each update. If revision 82 arrives before revision 47, the older update must not replace it. Record deletes as tombstones rather than quietly leaving expired chunks searchable. [[mlops/feature-training-serving-parity|Training-serving parity]] teaches the analogous issue for tabular features.'),
            ('Budget storage and prove completeness', 'An approximate vector index can use far more memory than raw float storage because graph and metadata structures add overhead. Plan for a period with two full indexes and a growing replay log. Publish per-source counts, delete coverage, source-revision lag and rejected vectors. Hold promotion when the new collection lacks an eligible bulletin even if sample queries look good. [[mlops/retrieval-shadow-evaluation-and-alias-cutover|Shadow evaluation]] then measures relevance and latency on a frozen query set before an alias changes.'),
        ],
        'code': '''def index_contract_matches(request, index):
    fields = ("encoder_digest", "dimension", "metric", "normalization",
              "chunk_revision")
    mismatch = [field for field in fields if request.get(field) != index.get(field)]
    return "admit" if not mismatch else "reject:" + ",".join(mismatch)

index = {"encoder_digest": "manual-embed-r47", "dimension": 384,
         "metric": "cosine", "normalization": "unit", "chunk_revision": "r8"}
query = dict(index)
assert index_contract_matches(query, index) == "admit"
assert index_contract_matches({**query, "encoder_digest": "manual-embed-r46"},
                              index) == "reject:encoder_digest"
''',
        'cost': 'The contract check is O(k) time and O(k) temporary space for k fields. Backfill uses O(n × d) embedding work for n chunks of dimension d; two indexes temporarily double base vector storage before index overhead. Query admission is cheap. Embedding generation and index construction dominate migration cost.',
        'mistakes': ['Assuming equal vector dimensions mean equal semantic spaces.', 'Replacing an index in place while old query encoders still serve.', 'Ignoring deletes that occurred during backfill.', 'Comparing corpus counts without source revisions or eligible filters.'],
        'related': [M + 'retrieval-shadow-evaluation-and-alias-cutover', M + 'repair-manual-index-migration-project', M + 'generative-release-manifest-and-prompt-model-binding', M + 'feature-training-serving-parity', M + 'model-artifact-digest-and-safe-loading'],
    },
    {
        'path': M + 'retrieval-shadow-evaluation-and-alias-cutover',
        'title': 'Retrieval release gates: shadow queries and reversible index cutover',
        'module': INDEX, 'project': False,
        'summary': 'A new index must pass relevance, coverage and latency gates before an atomic pointer sends production queries to it.',
        'sections': [
            ('Keep candidate and serving results distinct', 'Send a recorded query sample to both old and new indexes while only the old result reaches users. Keep the query text, client context, eligible-document filters and timestamp fixed for each paired comparison. Do not reuse old embeddings against the new index. Measure result IDs and grades, not raw similarity scores: scores from different embedding spaces are not directly comparable. [[mlops/embedding-index-contract-and-rebuild-plan|The index contract]] binds each query to its own encoder.'),
            ('Choose a useful relevance frame', 'Curate repair questions with judged relevant bulletin IDs, including rare machine variants, newly issued instructions and withdrawn bulletins. Measure recall at the displayed depth, filter correctness, zero-result rate and p95 retrieval latency by cohort. An improvement in average recall cannot excuse returning an obsolete safety step. Include source-revision lag and missing-document counts as independent gates. [[mlops/slice-quality-gates-and-uncertainty|Slice gates]] give the release a way to reject a harmful minority regression.'),
            ('Move one pointer after evidence passes', 'Once the candidate is complete and the update replay has reached the agreed watermark, switch a serving alias or versioned pointer atomically. Keep the old collection available through a soak window, and pin each request to the collection revision it used. Watch relevance proxies, empty results, latency and failures after cutover. If a gate fails, restore the old alias while preserving the new collection for diagnosis. [[mlops/promotion-attestation-and-reversible-pointer|A reversible pointer]] makes the rollback explicit.'),
            ('Avoid a false sense of safety', 'Shadow traffic is not a random sample of all future questions. Protected or infrequent filters may have no shadow coverage, so the judged set must include them. A live user query may reference a bulletin created after the frozen evaluation set; freshness checks cover this gap. Record which cohorts remain untested and use a limited canary before full traffic. [[mlops/repair-manual-index-migration-project|The project]] exercises a stale delete and a relevance regression that an average metric hides.'),
        ],
        'code': '''def retrieval_release_gate(report, limits):
    if report["missing_eligible"] or report["stale_deletes"]:
        return "hold:corpus-integrity"
    if report["rare_variant_recall"] < limits["rare_variant_recall"]:
        return "hold:rare-variant"
    if report["p95_ms"] > limits["p95_ms"]:
        return "hold:latency"
    if report["source_lag"] > limits["source_lag"]:
        return "hold:freshness"
    return "cutover:alias"

limits = {"rare_variant_recall": 0.82, "p95_ms": 47, "source_lag": 2}
report = {"missing_eligible": 0, "stale_deletes": 0,
          "rare_variant_recall": 0.87, "p95_ms": 39, "source_lag": 1}
assert retrieval_release_gate(report, limits) == "cutover:alias"
assert retrieval_release_gate({**report, "stale_deletes": 1}, limits) == \
       "hold:corpus-integrity"
''',
        'cost': 'The gate is O(1) time and space over an aggregated report. Shadowing adds one candidate query per sampled serving query, so read load grows with sample rate. Keeping the old index through the soak window adds storage, but permits a pointer rollback without a second rebuild.',
        'mistakes': ['Comparing similarity scores across unrelated embedding spaces.', 'Treating a high average recall as proof that rare filters are safe.', 'Deleting the old index before the soak window ends.', 'Cutting over with unresolved source lag or stale tombstones.'],
        'related': [M + 'embedding-index-contract-and-rebuild-plan', M + 'repair-manual-index-migration-project', M + 'slice-quality-gates-and-uncertainty', M + 'promotion-attestation-and-reversible-pointer', M + 'generative-evaluation-and-abstention-gates'],
    },
    {
        'path': M + 'repair-manual-index-migration-project',
        'title': 'Project: migrate a repair-manual retrieval index without losing updates',
        'module': INDEX, 'project': True,
        'summary': 'Backfill a second index, replay changes, compare shadow queries and switch a reversible serving alias.',
        'sections': [
            ('Set the migration packet', 'The service retrieves equipment repair bulletins. The incumbent collection and query encoder are revision 46; the candidate uses revision 47. Freeze the eligible bulletin snapshot, define the new encoder, vector dimension, metric and chunker, and preserve document-to-chunk IDs. Select a measured relevance frame that includes obscure equipment variants and withdrawn bulletins. [[mlops/embedding-index-contract-and-rebuild-plan|The contract]] rejects a new query encoder aimed at the old collection.'),
            ('Build while updates continue', 'Backfill candidate chunks from the frozen source snapshot. During the run, bulletin 82 is revised twice and bulletin 47 is withdrawn. Apply live changes by increasing source revision; store a delete tombstone for the withdrawn item. Simulate one delayed old update arriving after the newer version. The replay must keep the latest revision. Compare expected source IDs against indexed IDs and flag the withdrawn ID if it remains eligible. Do not call the backfill complete solely because its worker exited cleanly.'),
            ('Run paired queries and reject a weak slice', 'Replay repair questions against each collection with its matching query encoder. The candidate improves mean recall but misses a rare gearbox variant that incumbent retrieval found. Hold cutover; inspect the chunking and filter field for that variant, rebuild, and repeat the paired test. Also compare p95 retrieval time and fresh-bulletin lag. [[mlops/retrieval-shadow-evaluation-and-alias-cutover|The release gate]] requires the minority slice and corpus integrity to pass.'),
            ('Cut over and rehearse rollback', 'After replay catches up, atomically move the serving alias to the candidate. Record alias revision and source watermark with each request. Inject an empty-result spike for a supported variant and restore the old alias. The new collection remains intact for investigation, and updates keep flowing to both targets until the rollback decision closes. Hand off a release record with the evaluated query set, missing IDs, lag, cost, alias revision and rollback owner.'),
        ],
        'code': '''def apply_bulletin_change(index_state, change):
    current = index_state.get(change["document_id"])
    if current is not None and current["revision"] >= change["revision"]:
        return "ignored:stale"
    index_state[change["document_id"]] = {
        "revision": change["revision"], "deleted": change["deleted"]}
    return "applied"

candidate = {}
assert apply_bulletin_change(candidate, {"document_id": "bulletin-82",
       "revision": 47, "deleted": False}) == "applied"
assert apply_bulletin_change(candidate, {"document_id": "bulletin-82",
       "revision": 46, "deleted": False}) == "ignored:stale"
assert apply_bulletin_change(candidate, {"document_id": "bulletin-47",
       "revision": 82, "deleted": True}) == "applied"
assert candidate["bulletin-47"]["deleted"]
''',
        'cost': 'Each revision check and update is O(1) expected time; state uses O(n) space for n documents, including tombstones. A real backfill also pays O(n × d) embedding work and two-index storage. Dual writes and shadow reads add temporary load. That overhead is bounded by the migration window and makes rollback practical.',
        'mistakes': ['Applying delayed older updates over a newer bulletin.', 'Dropping delete events because the backfill snapshot already completed.', 'Comparing candidate and incumbent with one query encoder.', 'Using average recall to waive a rare-variant failure.'],
        'related': [M + 'embedding-index-contract-and-rebuild-plan', M + 'retrieval-shadow-evaluation-and-alias-cutover', M + 'generative-release-manifest-and-prompt-model-binding', M + 'promotion-attestation-and-reversible-pointer', M + 'slice-quality-gates-and-uncertainty'],
    },
    {
        'path': M + 'inference-evasion-threat-model-and-input-evidence',
        'title': 'Inference-time evasion: threat model and input evidence',
        'module': EVASION, 'project': False,
        'summary': 'An inference evasion attempt changes submitted inputs to obtain a favorable prediction without changing the real-world condition.',
        'sections': [
            ('Separate adversarial behavior from drift', 'A parcel scanner model routes damaged packages for review. An operator can submit altered images or metadata to push a damaged parcel below the review threshold. That is an inference-time manipulation concern, distinct from contaminated training data and ordinary camera drift. Define attacker control over pixels, crop, device metadata, retries and account identity. Record the decision the attacker wants and what evidence the service can actually observe. [[mlops/training-source-admission-and-quarantine|Training-source admission]] addresses a different stage of the lifecycle.'),
            ('Preserve a minimal decision trail', 'Retain a governed request ID, account or device pseudonym, input digest, model revision, preprocessing revision, score band, decision and review outcome where permitted. Keep raw images only under a documented retention policy; an input digest alone cannot explain visual changes. The operational question is whether repeated near-identical submissions from one actor cross the threshold after small edits. [[mlops/inference-request-response-contracts|The response contract]] should pin the decision revision and prevent clients from silently dropping review outcomes.'),
            ('Use multiple weak signals carefully', 'Repeated submissions, rapid score flips for nearly identical images, inconsistent device metadata and a burst of attempts near the threshold can justify a review queue. None alone proves intent: a damaged camera can produce similar patterns. Restrict rate per identity, enforce input schema and image validity, and route uncertain cases to human review. Do not label every threshold crossing as an attack or claim input validation defeats adversarial examples. [[mlops/inference-evasion-monitoring-and-containment|Containment policy]] ties signals to bounded action.'),
            ('Test the same boundary in release reviews', 'Include controlled perturbations of legitimate parcel images in offline evaluation: crop changes, brightness changes and metadata inconsistencies that remain within the allowed capture workflow. Check whether the decision changes when the actual damage condition does not. Report both false negatives and false alerts by camera and parcel type. Limit experiments to authorized test data. [[mlops/parcel-evasion-response-project|The project]] demonstrates that a benign retake can look suspicious and must not be silently blocked.'),
        ],
        'code': '''def classify_submission_pair(previous, current):
    if previous["model_revision"] != current["model_revision"]:
        return "incomparable:model-change"
    if previous["image_digest"] == current["image_digest"]:
        return "duplicate"
    if previous["parcel_id"] != current["parcel_id"]:
        return "different-parcel"
    if abs(previous["score"] - current["score"]) >= 0.27:
        return "review:score-flip"
    return "observe"

first = {"parcel_id": "shipment-82", "model_revision": "scan-r47",
         "image_digest": "sha-a", "score": 0.71}
second = {**first, "image_digest": "sha-b", "score": 0.39}
assert classify_submission_pair(first, second) == "review:score-flip"
assert classify_submission_pair(first, first) == "duplicate"
''',
        'cost': 'Pair classification is O(1) time and space after candidate pairs are selected. Finding pairs across a high-volume stream requires keyed state and bounded retention; a naive all-pairs comparison is O(n²). A review queue imposes human cost, so measure false alerts and time-to-decision before broad enforcement.',
        'mistakes': ['Calling every changed image an evasion attempt.', 'Comparing scores from different model revisions.', 'Keeping raw images indefinitely without a retention rule.', 'Assuming schema checks prevent small visual perturbations.'],
        'related': [M + 'inference-evasion-monitoring-and-containment', M + 'parcel-evasion-response-project', M + 'training-source-admission-and-quarantine', M + 'inference-request-response-contracts', M + 'score-threshold-policy-and-change-control'],
    },
    {
        'path': M + 'inference-evasion-monitoring-and-containment',
        'title': 'Inference evasion response: rate limits, review and reversible containment',
        'module': EVASION, 'project': False,
        'summary': 'Treat suspicious inference patterns as evidence for review, with proportional containment and an explicit release path.',
        'sections': [
            ('Choose a bounded detection window', 'Group submissions by actor and parcel over a short window. Count distinct valid image digests, threshold crossings and attempts with inconsistent metadata. A repeated request with the same digest is a retry, not a new candidate image. A device with poor connectivity can produce many retries, so combine distinctness with score behavior and review context. [[mlops/idempotent-inference-retries-and-quotas|Idempotent retries]] keep the serving record honest; [[mlops/inference-evasion-threat-model-and-input-evidence|the threat model]] states what the actor controls.'),
            ('Separate alert from adverse action', 'A suspicious pattern can trigger step-up review, a temporary rate cap or a hold on automated clearance. Keep a human path for urgent shipments and record the decision owner. Do not ban an account because a heuristic crossed one cutoff. Set expiry and appeal conditions for each hold, and record the model, rule and window revision in the case. [[mlops/human-override-and-adjudication-ledger|The override ledger]] keeps later corrections from disappearing.'),
            ('Measure operational harm', 'Track cases confirmed harmful, cases cleared as legitimate retakes, review queue age, rate-limit impact and damage misses by scanner cohort. If alerts concentrate on one camera generation after a software update, investigate drift before assigning attacker intent. Compare before and after using the same observation frame. [[mlops/drift-delayed-label-monitoring|Delayed-label monitoring]] helps separate an actual outcome change from an early proxy signal.'),
            ('Rehearse rollback and evidence handoff', 'Run an authorized test where a parcel is resubmitted after a harmless lighting change, then a separate test with repeated score flips across distinct images. Ensure the first is not permanently blocked and the second reaches review. If a new rule floods the queue, disable that rule revision and retain cases for inspection. [[mlops/incident-triage-and-evidence-timeline|Incident timelines]] capture the sequence; [[mlops/parcel-evasion-response-project|the project]] ties alerting to a reversible response.'),
        ],
        'code': '''def submission_window_action(events, maximum_distinct, score_span):
    distinct = {event["image_digest"] for event in events}
    if len(distinct) <= maximum_distinct:
        return "serve:normal"
    scores = [event["score"] for event in events]
    if max(scores) - min(scores) < score_span:
        return "observe:retries-or-retakes"
    return "review:temporary-automation-hold"

history = [{"image_digest": "frame-a", "score": 0.72},
           {"image_digest": "frame-b", "score": 0.68},
           {"image_digest": "frame-c", "score": 0.31}]
assert submission_window_action(history, 2, 0.27) == \
       "review:temporary-automation-hold"
assert submission_window_action(history[:2], 2, 0.27) == "serve:normal"
''',
        'cost': 'The window function is O(n) time and O(n) space for n events; a keyed streaming implementation should expire old actor-parcel state. Review costs rise with false alerts, while an aggressive hold can delay legitimate parcels. Tune thresholds using labeled cases and monitor queue capacity; this heuristic cannot prove an attack.',
        'mistakes': ['Counting identical retries as distinct attack attempts.', 'Turning a review signal into an indefinite account ban.', 'Ignoring camera drift that changes scores for innocent retakes.', 'Deploying a new rule without a disable switch and queue budget.'],
        'related': [M + 'inference-evasion-threat-model-and-input-evidence', M + 'parcel-evasion-response-project', M + 'idempotent-inference-retries-and-quotas', M + 'incident-triage-and-evidence-timeline', M + 'drift-delayed-label-monitoring'],
    },
    {
        'path': M + 'parcel-evasion-response-project',
        'title': 'Project: investigate repeated parcel-scanner score flips',
        'module': EVASION, 'project': True,
        'summary': 'Build a small evidence ledger, distinguish retakes from suspicious submissions and exercise a reversible review rule.',
        'sections': [
            ('Define an authorized investigation', 'A parcel scanner clears low-risk packages automatically. In a test cohort, one parcel receives several distinct images with scores on both sides of the damage-review threshold. Pin the model and preprocessing revision, request IDs, image digests, timestamps, camera class and outcome labels. The team has access to test images only under a short retention policy. [[mlops/inference-evasion-threat-model-and-input-evidence|The threat model]] limits claims to what these records support; intent is not directly observed.'),
            ('Sort retries, retakes and candidate manipulation', 'First collapse exact-image retries by digest and request identity. Then group distinct images by parcel and actor within a fixed window. A camera with a faulty flash creates a benign retake and a score shift; a separate sequence with repeated threshold crossings deserves review. Put both into the evidence ledger with reasons, not an attack verdict. Check input validity and metadata consistency without assuming that passing those checks makes an image safe.'),
            ('Apply a proportional policy', 'When the distinct-submission count and score span both exceed approved cutoffs, hold automated clearance for that parcel and send it to a staffed review queue. Keep ingestion open under a rate cap so an operator can provide a better capture. Set a hold expiry and route for appeal. The benign flash retake must clear after review; the unresolved repeated flips stay on temporary hold. [[mlops/inference-evasion-monitoring-and-containment|Containment]] is a reversible workflow, not an automatic accusation.'),
            ('Publish the case packet', 'Report the count of exact retries, distinct images, alert rule revision, review results, false alerts and queue delay. Re-run the case after a model update but keep scores separated by model revision. Rehearse disabling the rule if review age exceeds the service budget. Connect the case to [[mlops/incident-triage-and-evidence-timeline|incident evidence]] and [[mlops/score-threshold-policy-and-change-control|threshold change control]] before any permanent model or policy adjustment.'),
        ],
        'code': '''def parcel_case(events, max_distinct, required_span):
    current_revisions = {event["model_revision"] for event in events}
    if len(current_revisions) != 1:
        return "hold:mixed-model-evidence"
    by_digest = {event["image_digest"]: event for event in events}
    scores = [event["score"] for event in by_digest.values()]
    if len(by_digest) > max_distinct and max(scores) - min(scores) >= required_span:
        return "review:parcel-only"
    return "serve:normal"

cases = [{"model_revision": "scan-r47", "image_digest": "a", "score": 0.72},
         {"model_revision": "scan-r47", "image_digest": "b", "score": 0.69},
         {"model_revision": "scan-r47", "image_digest": "c", "score": 0.34}]
assert parcel_case(cases, 2, 0.27) == "review:parcel-only"
assert parcel_case(cases[:2], 2, 0.27) == "serve:normal"
''',
        'cost': 'The case pass is O(n) time and O(n) space for n events; keyed retention bounds live state. Human review and temporary holds add latency, so the packet must record both investigation value and legitimate-service impact. Keeping only digests reduces raw-image storage but limits later visual analysis.',
        'mistakes': ['Mixing scores from two model revisions in one score-span calculation.', 'Treating an exact retry as a distinct image.', 'Issuing a permanent ban from a threshold-crossing heuristic.', 'Omitting hold expiry and the result of human review.'],
        'related': [M + 'inference-evasion-threat-model-and-input-evidence', M + 'inference-evasion-monitoring-and-containment', M + 'incident-triage-and-evidence-timeline', M + 'score-threshold-policy-and-change-control', M + 'human-override-and-adjudication-ledger'],
    },
]

crosslinks = [
    (M + 'generative-release-manifest-and-prompt-model-binding', M + 'embedding-index-contract-and-rebuild-plan'),
    (M + 'generative-evaluation-and-abstention-gates', M + 'retrieval-shadow-evaluation-and-alias-cutover'),
    (M + 'promotion-attestation-and-reversible-pointer', M + 'repair-manual-index-migration-project'),
    (M + 'training-source-admission-and-quarantine', M + 'inference-evasion-threat-model-and-input-evidence'),
    (M + 'idempotent-inference-retries-and-quotas', M + 'inference-evasion-monitoring-and-containment'),
    (M + 'incident-triage-and-evidence-timeline', M + 'parcel-evasion-response-project'),
]

if __name__ == '__main__':
    publish(lessons, [INDEX, EVASION], crosslinks,
            'aitrove-mlops-index-evasion-import-20261006.json', 6208,
            subject='mlops', hub_path=M + 'mlops-tutorial')
