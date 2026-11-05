"""Add multimodal AI and privacy-aware ML to the local AI & Data preview."""
import datetime
import html
import json
from pathlib import Path
import re
import uuid

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
rows = [row for row in rows if not row['path'].startswith(('multimodal-ai/', 'privacy-aware-ml/'))]
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
lessons = []

def add(path, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path=path, title=title, summary=summary, sections=sections,
                        code=code, cost=cost, mistakes=mistakes, related=related))

add('multimodal-ai/paired-record-and-consent-contract',
    'Multimodal data contract: paired records, identity and consent',
    'A multimodal example is a governed relationship among media items, labels and a target decision, not merely files sharing a directory.', [
    ('Define the pair', 'AI Trove could link a receipt image to its extracted text and a reviewer’s description. Give each asset an immutable media ID, parent receipt ID, capture time, source and transform version. A filename is not an identity contract: resizes and retries can produce several files for one receipt. [[computer-vision/image-unit-label-and-consent|Image-unit rules]] should determine whether the training unit is a receipt, page or crop.'),
    ('Record alignment', 'The text must correspond to the same receipt image and, for multipage documents, the same page or region. Store alignment method and confidence; do not silently pair records by row order after a missing upload. A corrected OCR result should keep a link to the earlier version so a historical prediction can be reconstructed. The target label must stay distinct from the text used as model input.'),
    ('Respect availability and permission', 'A user may permit a receipt image for a specific workflow but not indefinite training reuse. Track permitted purpose, retention deadline and deletion state for each asset and derived representation. A text transcript can contain the same sensitive fields as the image. [[mlops/inference-logging-privacy|Inference logging]] must obey those limits, including when a model emits intermediate descriptions.'),
    ('Test a broken pair', 'Create image I-47 with OCR T-47, then insert a late text row T-48 for a different receipt. A positional join should fail the fixture; a keyed join should retain the correct pair. Add a deleted image whose cached text remains, and require the resulting training example to be excluded until the deletion policy is resolved.')],
    'def paired_receipts(images, texts):\n    text_by_receipt = {row["receipt_id"]: row for row in texts}\n    return [(image, text_by_receipt[image["receipt_id"]])\n            for image in images\n            if image["receipt_id"] in text_by_receipt\n            and image["consent_ok"] and text_by_receipt[image["receipt_id"]]["consent_ok"]]',
    'A keyed join costs O(I + T) expected time and O(T + P) memory for I images, T text rows and P accepted pairs. The simple map assumes one text version per receipt; production joins need version and page keys plus duplicate checks.',
    ['Do not pair modalities by file order or display name.', 'Do not treat derived OCR as exempt from the source asset’s permission.', 'Do not allow a target label to enter the input text.'],
    ['multimodal-ai/media-preprocessing-and-alignment','multimodal-ai/fusion-and-missing-modality','computer-vision/image-unit-label-and-consent','mlops/inference-logging-privacy'])

add('multimodal-ai/media-preprocessing-and-alignment',
    'Media preprocessing: image geometry, text spans and time alignment',
    'Preprocessing must preserve the coordinates and timing needed to explain which evidence came from which media item.', [
    ('Keep coordinate transforms', 'If a receipt image is rotated, cropped or resized, save the transform so OCR boxes can be mapped back to original pixels. A model may read the correct characters yet attach them to the wrong line after a coordinate mistake. [[computer-vision/pixel-geometry-and-preprocessing|Pixel geometry]] should be tested with corner points and boxes, not only a visual preview.'),
    ('Normalize text deliberately', 'Record OCR engine version, Unicode normalization and tokenization policy. Do not strip currency symbols, decimal separators or negative signs from payment totals. Preserve raw and normalized text separately, with offsets that can point to the source image. A normalization change can shift token boundaries and invalidate region-level annotations even when the visible sentence appears similar.'),
    ('Align asynchronous streams', 'For audio or video, timestamps connect words, frames and speaker turns. Specify clock origin and allowed skew; one second of drift can move a spoken instruction onto the wrong frame. Missing segments should remain explicit. A blank transcript is different from a verified silent segment, and a duplicated frame must not become independent evidence.'),
    ('Run a fixture', 'Use a receipt image rotated 90 degrees with a total box near the bottom edge, plus OCR text whose amount is 47.80. Map the transformed box back and verify it overlaps the original amount. Add a missing text segment and one OCR correction; the training row should identify which text version was available at prediction time.')],
    'def shift_media_times(media_rows, clock_offset_ms):\n    return [{**row, "aligned_ms": row["source_ms"] + clock_offset_ms}\n            for row in media_rows]',
    'Timestamp alignment is O(N) time and O(N) output space for N segments. Image warps cost proportional to pixel count; storing both original and transformed coordinates increases metadata but enables audit and error localization.',
    ['Do not discard geometry after resizing or rotating an image.', 'Do not normalize away characters that determine a financial amount.', 'Do not interpret missing text as confirmed silence.'],
    ['multimodal-ai/paired-record-and-consent-contract','multimodal-ai/cross-modal-retrieval-and-ranking','computer-vision/pixel-geometry-and-preprocessing','natural-language-processing/nlp-tutorial'])

add('multimodal-ai/alignment-negatives-and-shared-embeddings',
    'Cross-modal representation: positive pairs, negatives and shared space',
    'A shared embedding can rank related image and text records only when pair identity and comparison candidates are trustworthy.', [
    ('Choose positives', 'An image and its verified receipt text form a positive pair. Two crops from one receipt may share the parent identity but should not automatically be treated as distinct independent examples. Track duplicate scans and near-identical documents so a train-test split does not place copies on both sides. [[multimodal-ai/paired-record-and-consent-contract|Pair identity]] precedes any contrastive objective.'),
    ('Build plausible negatives', 'A random unrelated receipt is an easy negative. A useful evaluation asks whether a model can distinguish two receipts from the same merchant with similar totals and layout. Do not label a candidate negative if it could be another valid description of the same asset. Record the candidate-generation rule because retrieval scores change with the pool.'),
    ('Control representation versions', 'An image encoder and text encoder must write vectors into one compatible space under a known model version. Replacing only the text encoder can make existing image vectors incomparable. Normalize vectors consistently if cosine similarity is the chosen measure. A vector with no provenance is unsafe for debugging or deletion, even if the nearest-neighbor search still returns a result.'),
    ('Test a ranking', 'Pair image I-47 with text T-47, then include T-48 from the same merchant and T-93 from another merchant. The correct text should rank first under the tested model, but the evaluation should also show the margin to T-48. Repeat with a blurred image; a low margin should be visible rather than presented as a certain match.')],
    'from math import sqrt\n\ndef cosine_score(image_vector, text_vector):\n    if len(image_vector) != len(text_vector) or not image_vector:\n        return None\n    image_norm = sqrt(sum(value * value for value in image_vector))\n    text_norm = sqrt(sum(value * value for value in text_vector))\n    if image_norm == 0 or text_norm == 0:\n        return None\n    return sum(left * right for left, right in zip(image_vector, text_vector)) / (image_norm * text_norm)',
    'One similarity score costs O(D) time and O(1) auxiliary space for vector dimension D. Scoring C candidates directly costs O(C times D); an index reduces search work but adds build, versioning and recall checks.',
    ['Do not treat every unpaired item as a verified negative.', 'Do not compare vectors produced by incompatible encoder versions.', 'Do not split duplicate assets across training and evaluation.'],
    ['multimodal-ai/paired-record-and-consent-contract','multimodal-ai/cross-modal-retrieval-and-ranking','retrieval-ai/retrieval-ai-tutorial','computer-vision/grouped-evaluation-and-shift'])

add('multimodal-ai/fusion-and-missing-modality',
    'Multimodal fusion: choose a baseline and handle absent channels',
    'Combining image and text signals should beat strong single-channel baselines while remaining defined when one channel fails.', [
    ('Start with separate models', 'Measure an image-only and a text-only receipt classifier before joining their signals. A late-fusion baseline can average calibrated scores with fixed weights, which makes each contribution inspectable. Early feature fusion may capture interactions, but it also couples preprocessing and can amplify a mislabeled pair. [[multimodal-ai/paired-record-and-consent-contract|Pair quality]] limits every fusion method.'),
    ('Define missing behavior', 'OCR may fail on a folded receipt; an image may be withheld while approved text remains. Specify image-only, text-only and no-evidence routes explicitly. Do not fill a missing embedding with zeros and call it a genuine observation unless the model was trained and tested with that convention. Record modality availability and fallback rate by document type.'),
    ('Check calibration and dominance', 'If one model produces scores near 0.99 and another near 0.6, a naive average can let scale rather than evidence determine the result. Calibrate on held-out data, inspect disagreement cases and compare fusion against the stronger single-modality model. [[machine-learning/probability-calibration|Calibration checks]] matter before an alert threshold uses the combined score.'),
    ('Rehearse failure modes', 'Use a receipt with a clear image but empty OCR, another with legible text but a blocked image, and a third whose image and text refer to different receipt IDs. The first two should take declared fallbacks; the mismatched pair should be rejected before scoring. Report cost and latency for every route, since running two encoders can exceed the request budget.')],
    'def late_fusion(image_score, text_score, image_weight=0.55):\n    if image_score is None:\n        return text_score\n    if text_score is None:\n        return image_score\n    return image_weight * image_score + (1 - image_weight) * text_score',
    'Score fusion is O(1) time and space after encoders run. Image and text encoding often dominate latency and memory; a missing-channel fallback can save work, but only if routing happens before the unused encoder is invoked.',
    ['Do not assume a zero vector means the same thing as missing media.', 'Do not celebrate fusion without comparing it with each single-channel baseline.', 'Do not average uncalibrated scores and infer equal evidence.'],
    ['multimodal-ai/alignment-negatives-and-shared-embeddings','multimodal-ai/evaluation-slices-and-evidence-traces','machine-learning/probability-calibration','computer-vision/augmentation-and-serving-parity'])

add('multimodal-ai/cross-modal-retrieval-and-ranking',
    'Cross-modal retrieval: candidate pools, ranking and versioned indexes',
    'Image-to-text or text-to-image retrieval is a ranking task whose result depends on candidate eligibility, index freshness and duplicate control.', [
    ('Define the query', 'A reviewer may use an image crop to find the matching receipt transcript. Query and candidate are different media types, but the answer still needs a parent receipt ID, page alignment and a permitted-use check. A withdrawn image or text asset must be filtered before ranking, even if its embedding remains in a reproducibility snapshot. [[retrieval-ai/retrieval-ai-tutorial|Retrieval design]] separates candidate supply from final ranking.'),
    ('Build a hard pool', 'Measure recall against candidates from similar merchants, layouts and totals, not only random unrelated receipts. If the true transcript is absent from the index, the ranker cannot recover it. Report index coverage and candidate recall before top-K accuracy. Deduplicate multiple OCR versions or define which version is eligible; otherwise several near-copies can occupy the entire result list.'),
    ('Version the index', 'Record both encoder versions, vector normalization, index build cutoff and deletion-filter version. A new text encoder requires compatible image vectors or a planned dual-index transition. [[multimodal-ai/alignment-negatives-and-shared-embeddings|Shared-space compatibility]] is measurable: replay fixed query pairs and compare rank and score distributions before switching traffic.'),
    ('Inspect one query', 'For image I-47, return the correct transcript at rank two behind a same-merchant near-duplicate. The report should show candidate IDs, scores, duplicate group and why the top result was wrong. Rebuild the index after deleting that near-duplicate and confirm the deletion gate acts immediately, even before full reindexing finishes.')],
    'def recall_at_k(ranked_candidate_ids, relevant_ids, limit):\n    if limit < 1:\n        raise ValueError("limit must be positive")\n    relevant = set(relevant_ids)\n    if not relevant:\n        return None\n    return len(set(ranked_candidate_ids[:limit]) & relevant) / len(relevant)',
    'Top-K recall costs O(K + R) time and space for R relevant candidates. Exact scoring over C D-dimensional vectors costs O(C times D); approximate indexes trade build cost and possible recall loss for faster search.',
    ['Do not score a ranker when the correct item was never indexed.', 'Do not serve a withdrawn asset because its vector still exists.', 'Do not compare embeddings from incompatible model versions.'],
    ['multimodal-ai/alignment-negatives-and-shared-embeddings','multimodal-ai/evaluation-slices-and-evidence-traces','retrieval-ai/retrieval-ai-tutorial','recommendation-systems/candidate-retrieval-and-eligibility'])

add('multimodal-ai/evaluation-slices-and-evidence-traces',
    'Multimodal evaluation: subgroup failures and evidence traceability',
    'A pooled score can conceal failures on low-quality images, missing text, rare layouts and misleading media pairs.', [
    ('Split by parent asset', 'All crops, pages and OCR versions from one receipt belong in the same evaluation group. Otherwise near-copies leak into training and make the test look easier than production. Keep a later time period for final review and check whether merchants, templates or camera devices shifted. [[computer-vision/grouped-evaluation-and-shift|Grouped evaluation]] should be applied to every modality sharing an underlying entity.'),
    ('Report modality slices', 'Measure image-only, text-only, both-present, low-light, multilingual text and missing-channel subsets with counts. A combined average dominated by clear single-page receipts says little about folded or multipage failures. For retrieval, include candidate recall, rank quality and index coverage; for classification, include calibration and threshold costs. Do not convert an undefined small slice into a confident pass.'),
    ('Trace the evidence', 'For a wrong total, show the original image region, transform version, OCR span, text normalization and model outputs that led to the decision. If the system emits a summary, distinguish extracted facts from inferred descriptions. [[multimodal-ai/media-preprocessing-and-alignment|Coordinate and span preservation]] allows a reviewer to identify whether the error began in data alignment, extraction or fusion.'),
    ('Gate a release', 'Set acceptable error and latency limits by workflow before inspecting the test set. Add a fixture whose OCR says 47.80 while the image visibly contains 47.30, plus one missing image. The evaluation should identify disagreement and fallback route, not average the conflicting evidence into a plausible but false total. Keep the final test untouched during threshold selection.')],
    'def group_by_parent(media_rows):\n    groups = {}\n    for row in media_rows:\n        groups.setdefault(row["parent_receipt_id"], []).append(row["media_id"])\n    return groups',
    'Grouping N media rows is O(N) expected time and O(N) space. Detailed evidence traces add storage and access controls, but they cut investigation time and make deletion or correction of a bad source record possible.',
    ['Do not split crops or OCR versions from one receipt across train and test.', 'Do not report only a pooled score when missing-modality cases matter.', 'Do not state an inferred description as if it were extracted evidence.'],
    ['multimodal-ai/fusion-and-missing-modality','multimodal-ai/receipt-image-text-project','computer-vision/grouped-evaluation-and-shift','data-visualization/uncertainty-and-small-sample-display'])

add('multimodal-ai/receipt-image-text-project',
    'Project: audit an image-and-text receipt matcher',
    'Build a small cross-modal receipt matcher with versioned pairs, a missing-channel fallback and a reviewer trace for every error.', [
    ('Prepare the packet', 'Create receipt image and OCR text records with media IDs, parent receipt IDs, page numbers, transform versions and consent status. Include two near-duplicate receipts from the same merchant, an OCR correction, a missing image, a withdrawn asset and one intentionally mismatched pair. [[multimodal-ai/paired-record-and-consent-contract|Pair validation]] should reject the mismatch and withdrawal before embedding or scoring.'),
    ('Establish baselines', 'Implement a text-only exact-field baseline and an image-only or metadata baseline before combining signals. For the cross-modal path, use fixed provided vectors or a chosen encoder and record both encoder versions. Score candidates with normalized similarity and a permitted-asset filter. Compare the combined route against the strongest single-channel baseline on the same held-out receipt groups.'),
    ('Evaluate the hard cases', 'Use parent-receipt grouping and a later test period. Report candidate coverage, recall at three, near-duplicate errors, missing-channel fallback rate and latency. A correct result with the wrong page alignment is still a failure if the workflow needs an evidence region. Inspect at least one low-margin match and one case where OCR disagrees with the image.'),
    ('Submit a trace', 'Provide raw fixture, pairing rules, transform manifest, vector version, index snapshot, ranked candidate IDs and a reviewer packet for each failure. Delete one asset after index construction and prove that the serving filter excludes it immediately. State which steps are simple fixture oracles and which would require a real image or text encoder in deployment.')],
    'def eligible_matches(candidate_rows, withdrawn_media_ids):\n    withdrawn = set(withdrawn_media_ids)\n    return [row for row in candidate_rows\n            if row["media_id"] not in withdrawn and row["consent_ok"]]',
    'Filtering C candidates is O(C + W) expected time and O(C + W) memory for W withdrawn IDs. Encoder and index costs vary by implementation; measure those separately instead of attributing a fast fixture filter to the complete system.',
    ['Do not pair records by list position.', 'Do not include duplicate receipt crops in separate evaluation splits.', 'Do not return a withdrawn asset from a stale index.'],
    ['multimodal-ai/cross-modal-retrieval-and-ranking','multimodal-ai/evaluation-slices-and-evidence-traces','computer-vision/receipt-quality-project','retrieval-ai/retrieval-ai-tutorial'])

add('privacy-aware-ml/threat-model-and-data-minimization',
    'Privacy-aware ML: threat model, data minimization and purpose',
    'A privacy claim needs a defined adversary, protected unit, data flow and retention boundary before a technique can be evaluated.', [
    ('Name the protected unit', 'For an AI Trove lesson model, protecting a learner may mean preventing an observer from inferring that learner’s activity from a released model. That differs from preventing an internal operator from viewing raw events or another tenant from receiving a feature. Write the adversary’s access: public model outputs, logs, shared gradients or database queries. [[mlops/inference-logging-privacy|Inference logging]] is one part of the exposure path.'),
    ('Reduce collection first', 'List the fields required for the decision and avoid copying unrelated profile details into training. Replace raw text with a task-specific signal where the loss is acceptable; cap retention and keep a deletion key. A hashed learner ID is still a persistent linkable identifier, not automatic anonymity. Separate collection permission, training permission and publication of aggregate results.'),
    ('Trace derivatives', 'A raw lesson event may generate a warehouse row, feature vector, embedding, training set, model checkpoint and diagnostic log. Inventory those descendants before promising deletion or restricted reuse. [[feature-stores/feature-view-version-and-lineage|Feature lineage]] and model manifests should identify the version and purpose of each derivative without placing sensitive values in the manifest itself.'),
    ('Test a policy boundary', 'Create one learner who permits feed personalization but opts out of model training. Their request-time state may serve the allowed feed while their events are absent from the training extract. Add a withdrawn learner and verify the online feature key, cached vector and future batch inputs are excluded under the defined policy. A reviewer should see which artifacts remain and why.')],
    'def training_eligible(events):\n    return [event for event in events\n            if event["training_permission"] and not event["withdrawn"]\n            and event["purpose"] == "lesson-recommendation"]',
    'Filtering N events is O(N) time and O(A) output memory for A allowed events. The real cost is maintaining permission and deletion state consistently across derived datasets; a row filter alone is not a privacy guarantee.',
    ['Do not call a hashed stable ID anonymous.', 'Do not reuse data for training merely because it was collected for serving.', 'Do not promise deletion before inventorying derived artifacts.'],
    ['privacy-aware-ml/privacy-unit-and-contribution-bounds','privacy-aware-ml/deletion-lineage-and-release-controls','mlops/inference-logging-privacy','feature-stores/feature-view-version-and-lineage'])

add('privacy-aware-ml/privacy-unit-and-contribution-bounds',
    'Privacy units and bounded contribution: count people, not events',
    'A privacy analysis must specify whether it protects one event, one account or an entire person’s contributions across time.', [
    ('Select the neighbor relation', 'If one learner can create 400 events, protecting one event says little about that learner’s complete activity. A learner-level neighboring dataset differs by all allowed events for one learner. Define the protection unit before selecting a mechanism or quoting a privacy parameter. [[privacy-aware-ml/threat-model-and-data-minimization|The threat model]] should make that choice relevant to a real observer.'),
    ('Bound contributions', 'For a weekly completion count, cap each learner at one qualifying contribution to that week’s released statistic, then define how many weeks can be released. A per-week cap does not by itself bound a learner’s total contribution across a long series. Apply the bound before aggregation; deleting extra rows after publishing a noisy output does not repair the sensitivity calculation.'),
    ('Control identifiers', 'Deduplication requires a stable learner key inside the protected computation, even if the published output omits it. Do not expose the key in logs or sample outputs. If one person can hold multiple accounts, an account-level unit may fail to match the intended person-level protection; state that limit explicitly rather than claiming a broader guarantee.'),
    ('Run a fixture', 'Learner L-47 completes three lessons in one week and L-48 completes one. Under a one-contribution-per-learner weekly count, the bounded count is two, not four. Add L-47 in the next week and decide whether the release protects each week independently or the learner across both weeks; the answer changes the accounting plan.')],
    'def bounded_weekly_count(completion_rows, week_id):\n    learners = {row["learner_id"] for row in completion_rows\n                if row["week_id"] == week_id and row["qualifies"]}\n    return len(learners)',
    'A pass over N events costs O(N) expected time and O(U) memory for U distinct learners in the week. This code enforces one weekly count per learner; it does not add noise or establish differential privacy by itself.',
    ['Do not describe event-level protection as person-level protection.', 'Do not ignore repeated contributions across released periods.', 'Do not present deduplication alone as a private release mechanism.'],
    ['privacy-aware-ml/threat-model-and-data-minimization','privacy-aware-ml/privacy-budget-and-safe-release','applied-statistics/population-estimand-and-sampling-frame','data-engineering/idempotent-load-and-checkpoint'])

add('privacy-aware-ml/privacy-budget-and-safe-release',
    'Private aggregate releases: sensitivity, budget and query control',
    'A private-release design needs bounded input influence, an approved mechanism and accounting for every disclosed result.', [
    ('Separate clipping from release', 'Contribution bounding sets how much one protected unit can change a statistic; it is not the final release. A mechanism may add calibrated randomness under a defined privacy guarantee, but the guarantee depends on the protected unit, sensitivity, mechanism, parameters and all earlier releases. [[privacy-aware-ml/privacy-unit-and-contribution-bounds|The contribution contract]] must be reviewed before any budget number is meaningful.'),
    ('Track composition', 'Repeatedly querying the same underlying population can spend additional privacy budget, even when each result looks harmless. Register each approved query with a purpose, dataset version, protected unit, mechanism, budget cost and release ID. Do not answer an unregistered analyst query and then add its cost to the ledger afterward. Releasing the same already-approved noisy result again is different from drawing a fresh answer.'),
    ('Protect small groups', 'A group with very few learners may produce a noisy but still misleading or unstable statistic. Combine formal accounting with product rules for minimum support, output review and a clear uncertainty statement. Do not treat a group-size threshold alone as a mathematical privacy guarantee. Suppression decisions themselves can reveal information if they depend on sensitive counts without a designed mechanism.'),
    ('Rehearse the ledger', 'Give a weekly completion dashboard an approved budget of 1.2 units under its chosen accounting model. Reserve 0.35 for one release and 0.40 for another; a third request costing 0.50 must be rejected because the total would exceed 1.2. This arithmetic ledger is only a control-plane illustration, not a complete differential-privacy implementation.')],
    'def reserve_release_budget(spent, requested, approved_limit):\n    if requested <= 0 or spent < 0 or approved_limit <= 0:\n        raise ValueError("invalid budget state")\n    if spent + requested > approved_limit:\n        return None\n    return spent + requested',
    'A ledger reservation is O(1) time and space, but concurrent requests require an atomic transaction. The code does not implement a privacy mechanism; production guarantees need reviewed sensitivity, randomness and composition accounting.',
    ['Do not claim clipping or minimum group size alone proves differential privacy.', 'Do not issue fresh noisy answers outside the release ledger.', 'Do not treat a bookkeeping function as a privacy guarantee.'],
    ['privacy-aware-ml/privacy-unit-and-contribution-bounds','privacy-aware-ml/membership-risk-and-evaluation','applied-statistics/confidence-interval-coverage','data-visualization/uncertainty-and-small-sample-display'])

add('privacy-aware-ml/federated-updates-and-aggregation-risk',
    'Federated training: local data, update leakage and aggregation boundaries',
    'Keeping raw data on devices reduces central collection but does not make model updates harmless or training automatically private.', [
    ('Define the federation', 'A learner device could update a small preference model locally and send a clipped update to a coordinator. Record which clients are eligible, how rounds are sampled and what minimum cohort size is required. A device may disconnect midway; accepted updates and aggregation weights must be explicit. A server that sees each raw update may infer information from it even though it never received the underlying events.'),
    ('Bound and protect updates', 'Clipping limits the effect of an extreme update and can support a reviewed privacy mechanism, but clipping alone is not a privacy guarantee. Secure aggregation can restrict what the coordinator sees, subject to its protocol and trust assumptions. Differential privacy requires additional accounting if claimed. [[privacy-aware-ml/privacy-unit-and-contribution-bounds|The privacy unit]] may be one client, one account or one person; those are not interchangeable.'),
    ('Handle uneven clients', 'Highly active devices may produce many examples while others have few. Weighting by local row count can let large clients dominate and may reveal size information. Compare equal-client and capped-example weighting, then test utility by client segment. Communication cost, battery use and dropouts affect participation; a model trained on only reliable devices can underperform for the excluded population.'),
    ('Test a round', 'Simulate three clients with update values 0.4, 0.6 and 9.0. Clip each to a magnitude of 1.0 before averaging, so the aggregate is about 0.67 rather than 3.33. Drop one client before final aggregation and record the new denominator. This toy scalar test verifies clipping and aggregation math, not protection against update reconstruction.')],
    'def clipped_mean_update(client_updates, clip_limit):\n    if clip_limit <= 0 or not client_updates:\n        raise ValueError("invalid aggregation input")\n    clipped = [max(-clip_limit, min(clip_limit, value)) for value in client_updates]\n    return sum(clipped) / len(clipped)',
    'Aggregating C scalar updates costs O(C) time and O(C) temporary space here. Real model vectors cost O(C times D) work for D parameters, plus network transfer and protocol overhead; local-only data does not remove those costs.',
    ['Do not claim federated training is private merely because raw rows stay local.', 'Do not ignore client dropout or unequal participation.', 'Do not label clipping as a complete leakage defense.'],
    ['privacy-aware-ml/threat-model-and-data-minimization','privacy-aware-ml/privacy-budget-and-safe-release','mlops/retraining-trigger-and-challenger','machine-learning/group-and-time-validation'])

add('privacy-aware-ml/membership-risk-and-evaluation',
    'Model leakage evaluation: membership risk, memorization and limits',
    'A privacy review should test what an adversary can infer from the released interface and state what the test does not cover.', [
    ('Set attacker access', 'A public scoring endpoint, a downloadable model and an internal embedding index expose different information. Specify query limits, output granularity and whether the attacker knows a learner’s candidate record. A confidence score with many decimal places can reveal more than a coarse decision. [[privacy-aware-ml/threat-model-and-data-minimization|The threat model]] determines which attack simulation is relevant.'),
    ('Use held-out comparisons', 'A simple membership probe compares model behavior on training and genuinely held-out records matched by time and population. Large performance gaps can be a warning of memorization, but they do not prove a particular record leaked. Conversely, a weak probe does not prove safety against stronger attacks. Keep the audit data separate from the model-selection loop.'),
    ('Examine rare records', 'Unusual receipt text, uncommon names or a learner’s distinctive sequence may be reproduced by a generative model or close neighbor search. Test canary-like synthetic strings under a controlled procedure, with no real sensitive text in public reports. Review logging, caches and retrieval indexes as well as model weights; leakage can come from surrounding systems.'),
    ('Report defensible findings', 'Compare attack success with a population-aware baseline, provide confidence intervals and state query budget. If a membership probe reaches 58 percent accuracy against a balanced 50 percent baseline, report the sample size and uncertainty rather than declaring a universal breach. Record what interface was tested and what remains untested before a release decision.')],
    'def membership_probe_accuracy(predicted_membership, actual_membership):\n    if len(predicted_membership) != len(actual_membership) or not actual_membership:\n        return None\n    correct = sum(predicted == actual for predicted, actual\n                  in zip(predicted_membership, actual_membership))\n    return correct / len(actual_membership)',
    'Scoring N probe cases costs O(N) time and O(1) auxiliary space. A real attack evaluation may require many model queries and strict test access controls; its result is evidence about the tested interface, not a proof of overall privacy.',
    ['Do not interpret one weak attack as proof of safety.', 'Do not publish real sensitive canaries in an audit report.', 'Do not ignore retrieval indexes and logs when reviewing model leakage.'],
    ['privacy-aware-ml/privacy-budget-and-safe-release','privacy-aware-ml/deletion-lineage-and-release-controls','mlops/inference-logging-privacy','machine-learning/group-and-time-validation'])

add('privacy-aware-ml/deletion-lineage-and-release-controls',
    'Privacy operations: deletion lineage, access gates and release review',
    'A deletion or withdrawal request must reach the data path and its derivatives without silently breaking model reproducibility claims.', [
    ('Map the dependency chain', 'Record which raw events feed feature views, training snapshots, vector indexes, checkpoints and diagnostic logs. A withdrawn learner may be removed from future training while an earlier released model still reflects aggregate influence; state that distinction plainly. [[feature-stores/backfill-delete-and-publication|Feature deletion gates]] must outrank stale materialization jobs so a replay cannot resurrect a key.'),
    ('Control access by purpose', 'Permit only approved training jobs to read learner events and only approved serving paths to read request-time features. Log access to sensitive datasets without copying values into logs. A project owner should review retention and export behavior when a new model family is introduced, since embeddings and free-text outputs can preserve details differently from simple count features.'),
    ('Test withdrawal races', 'Withdraw learner L-47 while a batch export and online cache refresh are running. New training manifests must exclude the learner, the online key must be invalidated, and the pending worker must not republish it. Attach a deletion version or tombstone to every publication boundary. Do not use rollback to restore a key that is no longer permitted.'),
    ('Gate a model release', 'Review permission coverage, data minimization, derivative inventory, leakage tests, output controls and unresolved deletion requests. Record an owner and a concrete response for each exception. [[mlops/model-registry-promotion-gates|Model promotion]] should fail when the input policy is unknown, even if predictive quality improves. A review packet must distinguish tested controls from assumptions.')],
    'def allowed_training_ids(learner_rows, withdrawn_ids):\n    withdrawn = set(withdrawn_ids)\n    return {row["learner_id"] for row in learner_rows\n            if row["learner_id"] not in withdrawn and row["training_permission"]}',
    'Filtering N learner rows costs O(N + W) expected time and O(N + W) memory for W withdrawn IDs. Distributed deletion requires durable tombstones, cache invalidation and downstream lineage checks beyond this fixture-level filter.',
    ['Do not promise a withdrawal erased influence from an already released model without a defined remedy.', 'Do not let rollback revive a forbidden feature key.', 'Do not store sensitive feature values in access or audit logs.'],
    ['privacy-aware-ml/threat-model-and-data-minimization','privacy-aware-ml/membership-risk-and-evaluation','feature-stores/backfill-delete-and-publication','mlops/model-registry-promotion-gates'])

add('privacy-aware-ml/learner-aggregate-release-project',
    'Project: design a bounded learner-activity release',
    'Build a controlled weekly learning aggregate with explicit permission, bounded contribution, a release ledger and deletion tests.', [
    ('Create the protected packet', 'Define learner as the protected unit and weekly qualifying completion as the statistic. Include several events from one learner, a withdrawn learner, an opted-out learner and a duplicate event. Record training and aggregate-release permissions separately. [[privacy-aware-ml/privacy-unit-and-contribution-bounds|Contribution bounds]] should reduce one learner to at most one weekly contribution under the chosen contract.'),
    ('Separate controls from guarantees', 'Implement deduplication, permission filtering and a transactional release-budget reservation. Use an approved privacy mechanism if the project claims differential privacy; otherwise label the output a bounded internal aggregate without a formal guarantee. Document sensitivity, unit, composition and the number of planned releases before any external publication. The fixture code below is an eligibility check, not a private mechanism.'),
    ('Exercise operations', 'Issue two planned ledger reservations and reject a third that exceeds the approved limit. Repeat a request using the same release ID and return the existing approved result rather than drawing a fresh answer. Withdraw learner L-47 during a batch run and verify the tombstone prevents a stale worker from restoring that learner in the next snapshot.'),
    ('Submit a review packet', 'Deliver threat model, field inventory, purpose rules, lineage map, bounded-count fixture, budget ledger, deletion-race test and utility report. If using a formal privacy library, include its mechanism configuration and independently reviewed accounting output. State what a membership probe did and did not test. No deployment claim should exceed the evidence in the packet.')],
    'def eligible_learner_count(event_rows, withdrawn_ids):\n    withdrawn = set(withdrawn_ids)\n    learners = {row["learner_id"] for row in event_rows\n                if row["learner_id"] not in withdrawn\n                and row["aggregate_permission"] and row["qualifies"]}\n    return len(learners)\n\nassert eligible_learner_count([{"learner_id": "L-47", "aggregate_permission": True, "qualifies": True},\n                               {"learner_id": "L-47", "aggregate_permission": True, "qualifies": True}], set()) == 1',
    'A scan over N events costs O(N + W) expected time and O(U + W) memory for U eligible learners and W withdrawals. The result is bounded by one contribution per learner in this fixture; it is not differentially private without a reviewed release mechanism.',
    ['Do not call a bounded raw count differentially private.', 'Do not permit an unregistered fresh release after the budget is spent.', 'Do not let a stale batch republish a withdrawn learner.'],
    ['privacy-aware-ml/privacy-unit-and-contribution-bounds','privacy-aware-ml/privacy-budget-and-safe-release','privacy-aware-ml/deletion-lineage-and-release-controls','mlops/receipt-triage-release-project'])

assert len(lessons) == 14
assert len({item['path'] for item in lessons}) == len(lessons)
titles = {path: row['title'] for path, row in by_path.items()}
titles.update({item['path']: item['title'] for item in lessons})

def prose(value):
    return re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',
                  lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                  html.escape(value))

def links(paths):
    return '<ul>' + ''.join('<li><a href="/' + path + '">' + html.escape(titles[path]) + '</a></li>' for path in paths) + '</ul>'

def article_body(item):
    parts = ['<p>' + html.escape(item['summary']) + '</p>']
    for heading, paragraph in item['sections']:
        parts.extend(('<h2>' + html.escape(heading) + '</h2>', '<p>' + prose(paragraph) + '</p>'))
    parts.extend(('<h2>Implementation</h2>', '<pre><code class="language-python">' + html.escape(item['code']) + '</code></pre>',
                  '<h2>Performance and operating cost</h2>', '<p>' + html.escape(item['cost']) + '</p>',
                  '<h3>Common Mistakes</h3>', '<ul>' + ''.join('<li>' + html.escape(mistake) + '</li>' for mistake in item['mistakes']) + '</ul>',
                  '<h2>Read next</h2>', links(item['related'])))
    return ''.join(parts)

def make_row(path, title, summary, body, entry_type, subject, section_path, root_path, order, metadata):
    return dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://aitrove.in/' + path)), type=entry_type,
                path=path, title=title, summary=summary, body=body, category='AI & Data',
                subject=subject, difficulty='Intermediate', tags=['ai-data', subject], potd_date=None,
                featured=False, sort_order=order, status='published', published_at=stamp,
                created_at=stamp, updated_at=stamp,
                data={'subject_root':root_path, 'section_path':section_path,
                      'content_format':'html', 'seo_ready':True, **metadata})

subject_config = {
 'multimodal-ai': {
     'root':'multimodal-ai/multimodal-ai-tutorial', 'name':'Multimodal AI',
     'summary':'Connect image and text evidence with validated pairs, compatible representations, missing-channel fallbacks and traceable evaluation.',
     'groups':[('Data and representation', ['paired-record-and-consent-contract','media-preprocessing-and-alignment','alignment-negatives-and-shared-embeddings']),
               ('Fusion and review', ['fusion-and-missing-modality','cross-modal-retrieval-and-ranking','evaluation-slices-and-evidence-traces'])],
     'project':'receipt-image-text-project',
     'foundation':['computer-vision/computer-vision-tutorial','natural-language-processing/nlp-tutorial'],
     'neighbors':['retrieval-ai/retrieval-ai-tutorial','privacy-aware-ml/privacy-aware-ml-tutorial']},
 'privacy-aware-ml': {
     'root':'privacy-aware-ml/privacy-aware-ml-tutorial', 'name':'Privacy-Aware ML',
     'summary':'Define protected units and threats, bound contributions, review release accounting and test data-lineage controls.',
     'groups':[('Protection contract', ['threat-model-and-data-minimization','privacy-unit-and-contribution-bounds','privacy-budget-and-safe-release']),
               ('Training and operations', ['federated-updates-and-aggregation-risk','membership-risk-and-evaluation','deletion-lineage-and-release-controls'])],
     'project':'learner-aggregate-release-project',
     'foundation':['machine-learning/machine-learning-tutorial','mlops/mlops-tutorial'],
     'neighbors':['feature-stores/feature-stores-tutorial','multimodal-ai/multimodal-ai-tutorial']},
}

for config in subject_config.values():
    titles[config['root']] = config['name'] + ' Tutorial'
    titles[config['root'] + '/project'] = config['name'] + ': Projects'

for slug, config in subject_config.items():
    root_path = config['root']
    project_hub_path = root_path + '/project'
    modules = [{'title':group_title, 'summary':'Read in order and run the failure checks.',
                'lessons':[slug + '/' + lesson_name for lesson_name in lesson_names]}
               for group_title, lesson_names in config['groups']]
    project_path = slug + '/' + config['project']
    modules.append({'title':'Apply your knowledge', 'lessons':[project_path]})
    all_paths = [path for module in modules for path in module['lessons']]
    tabs = [{'title':config['name'], 'path':root_path}, {'title':'Projects', 'path':project_hub_path}]
    hub_body = ('<p>' + html.escape(config['summary']) + '</p><h2>Learning path</h2>' + links(all_paths)
                + '<h2>Connected foundations</h2><p>Use the earlier data and model boundaries as prerequisites.</p>'
                + links(config['foundation']) + '<h2>Further paths</h2>' + links(config['neighbors'])
                + '<h2>Practice</h2>' + links([project_hub_path]))
    hub = make_row(root_path, titles[root_path], config['summary'], hub_body,
                   'subject', slug, root_path, root_path, 10200 if slug == 'multimodal-ai' else 10300,
                   {'modules':modules, 'resource_tabs':tabs})
    project_body = ('<p>Apply the ' + html.escape(config['name']) + ' curriculum to a checked project.</p>'
                    '<h2>Project brief</h2>' + links([project_path])
                    + '<h2>Required concepts</h2>' + links(all_paths[:-1])
                    + '<h2>Completion standard</h2><p>Submit runnable work, a data manifest, measured results and failure-case evidence.</p>')
    project_hub = make_row(project_hub_path, titles[project_hub_path],
                           'A checked project for the ' + config['name'] + ' curriculum.', project_body,
                           'subject', slug + '-project', project_hub_path, root_path,
                           10201 if slug == 'multimodal-ai' else 10301,
                           {'modules':[{'title':'Projects','lessons':[project_path]}], 'resource_tabs':tabs})
    rows.extend((hub, project_hub))
    by_path[root_path] = hub
    by_path[project_hub_path] = project_hub

for index, item in enumerate(lessons):
    slug = item['path'].split('/')[0]
    root_path = subject_config[slug]['root']
    is_project = item['path'].endswith('-project')
    section_path = root_path + '/project' if is_project else root_path
    body = article_body(item)
    article = make_row(item['path'], item['title'], item['summary'], body, 'article',
                       slug + '-project' if is_project else slug, section_path, root_path,
                       10400 + index,
                       {'kind':'project' if is_project else 'tutorial',
                        'reading_minutes':max(5, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                        'author_path':'authors/aitrove-editorial',
                        'verification_suite':'Editorial and syntax review; project inputs needed for runtime checks',
                        'related':[{'path':path,'title':titles[path]} for path in item['related']]})
    rows.append(article)
    by_path[item['path']] = article

for source, target in [
    ('computer-vision/image-unit-label-and-consent','multimodal-ai/paired-record-and-consent-contract'),
    ('computer-vision/pixel-geometry-and-preprocessing','multimodal-ai/media-preprocessing-and-alignment'),
    ('retrieval-ai/retrieval-ai-tutorial','multimodal-ai/cross-modal-retrieval-and-ranking'),
    ('machine-learning/probability-calibration','multimodal-ai/fusion-and-missing-modality'),
    ('mlops/inference-logging-privacy','privacy-aware-ml/threat-model-and-data-minimization'),
    ('feature-stores/backfill-delete-and-publication','privacy-aware-ml/deletion-lineage-and-release-controls'),
    ('mlops/model-registry-promotion-gates','privacy-aware-ml/deletion-lineage-and-release-controls'),
    ('data-science/data-science-for-beginners','privacy-aware-ml/privacy-unit-and-contribution-bounds'),
]:
    row = by_path[source]
    anchor = '<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in row['body']:
        row['body'] += anchor
        if row['type'] == 'article':
            row['data']['related'].append({'path':target,'title':titles[target]})
        row['updated_at'] = stamp

for source, target in [
    ('computer-vision/computer-vision-tutorial','multimodal-ai/multimodal-ai-tutorial'),
    ('natural-language-processing/nlp-tutorial','multimodal-ai/multimodal-ai-tutorial'),
    ('mlops/mlops-tutorial','privacy-aware-ml/privacy-aware-ml-tutorial'),
    ('feature-stores/feature-stores-tutorial','privacy-aware-ml/privacy-aware-ml-tutorial'),
]:
    row = by_path[source]
    anchor = '<p><strong>Continue into another subject:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in row['body']:
        row['body'] += anchor
        row['updated_at'] = stamp

assert len({row['path'] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_articles':len(lessons), 'new_subject_hubs':4, 'crosslinks_from_existing':12}))
