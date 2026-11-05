"""Add original annotation and synthetic-data curricula to local AI & Data previews."""
import datetime
import html
import json
from pathlib import Path
import re
import uuid

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
rows = [row for row in rows if not row['path'].startswith(('data-annotation/', 'synthetic-data/'))]
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
lessons = []

def add(path, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path=path, title=title, summary=summary, sections=sections,
                        code=code, cost=cost, mistakes=mistakes, related=related))

add('data-annotation/label-unit-taxonomy-and-guidelines',
    'Label contracts: decision unit, taxonomy and review rules',
    'A label is a recorded decision about a specified unit, at a specified time, under a versioned rule set.', [
    ('Fix the decision unit', 'For receipt extraction, decide whether a reviewer labels an entire receipt, one line item or one field. A field-level “merchant missing” label cannot be compared with a receipt-level “unreadable” label without an explicit mapping. Record the document version, crop or field span, event time and reviewer view. [[computer-vision/annotation-geometry-and-quality|Geometry quality]] belongs in this contract when images are involved.'),
    ('Write a usable taxonomy', 'Separate positive, negative, unknown and not-applicable states. Unknown means the evidence cannot settle the question; it is not a negative outcome. Give each class inclusion rules, exclusions and a counterexample. A policy that says “mark suspicious receipts” leaves reviewers to invent different thresholds. Tie every label to a guideline revision so the same fixture can be replayed under a later policy.'),
    ('Control what reviewers see', 'Hide downstream model scores and final business outcomes when those facts would bias a primary annotation. If a reviewer must see a model suggestion, store that as assisted review and measure it separately. Mask unnecessary personal data. [[privacy-aware-ml/threat-model-and-data-minimization|Data minimization]] makes the review process safer and keeps the decision tied to evidence actually available at labeling time.'),
    ('Try boundary cases', 'Create one clean receipt, one cropped total, one duplicate scan and one receipt whose total is ambiguous because a discount line is cut off. Require a class and reason for each. Run two guideline versions and list precisely which labels change. If a change cannot be explained by a rule, the taxonomy is incomplete or the evidence presented to reviewers differs.')],
    'LABELS = {"accepted", "rejected", "unknown", "not_applicable"}\n\ndef valid_review(review):\n    return (review["label"] in LABELS\n            and bool(review["guideline_version"])\n            and bool(review["receipt_id"])\n            and bool(review["evidence_revision"]))',
    'Contract validation is O(1) per review and O(N) for N reviews. Keeping evidence and guideline revisions increases storage, but prevents silent reinterpretation of historical labels when a policy changes.',
    ['Do not merge unknown into the negative class.', 'Do not change a guideline without recording its version.', 'Do not label a crop as if the reviewer saw the whole document.'],
    ['data-annotation/annotator-assignment-and-blinding','data-annotation/adjudication-and-gold-set-versioning','computer-vision/annotation-geometry-and-quality','privacy-aware-ml/threat-model-and-data-minimization'])

add('data-annotation/annotator-assignment-and-blinding',
    'Annotator assignment: coverage, blinding and independent review',
    'Assignment rules decide which items receive independent judgment and whether reviewers are exposed to the same bias.', [
    ('Sample before routing', 'Select an audit sample from the incoming population before a model confidence filter or a reviewer queue changes it. Stratify by document source, image quality and expected rarity, and retain selection probabilities. A queue containing only low-confidence receipts is useful for fixing difficult cases, but cannot estimate overall label accuracy. [[applied-statistics/population-estimand-and-sampling-frame|Population and sampling frame]] define what the audit can claim.'),
    ('Keep independent passes independent', 'Assign two reviewers to the same item without showing the first answer to the second. Rotate reviewer pairs so one specialist does not monopolize a source. Record assignment time, reviewer role, guideline version and whether an AI suggestion was displayed. If assisted reviews are operationally necessary, reserve an independent blind set to measure suggestion-induced agreement.'),
    ('Protect access and capacity', 'A reviewer should see the least data needed for the question. Remove account identifiers unless they determine the label, and use stable pseudonymous item IDs for joins. Budget enough repeated items to estimate reviewer consistency, but not so many that repeat recognition dominates. A capacity cap by reviewer prevents a single person’s interpretation from defining the apparent ground truth.'),
    ('Exercise assignment fairness', 'Suppose 47 receipts arrive from three scanners and 12 require duplicate review. Pick duplicate reviews across all scanner sources and image-quality bands. Check that no reviewer is assigned both independent passes for one receipt. Then add a specialist-only scanner and state that its quality estimate cannot be generalized to other scanners without overlap or a separate sample.')],
    'def independent_pairs(assignments):\n    by_receipt = {}\n    for assignment in assignments:\n        by_receipt.setdefault(assignment["receipt_id"], set()).add(assignment["reviewer_id"])\n    return {receipt_id for receipt_id, reviewers in by_receipt.items()\n            if len(reviewers) >= 2}',
    'Grouping A assignments costs O(A) expected time and O(R) space for R distinct receipts. Balanced scheduling needs source and reviewer-capacity indexes; the audit sample must preserve its original selection probabilities.',
    ['Do not call model-filtered queues representative audits.', 'Do not expose the first judgment during an independent second pass.', 'Do not ignore source coverage when assigning specialist reviewers.'],
    ['data-annotation/label-unit-taxonomy-and-guidelines','data-annotation/agreement-and-disagreement-review','applied-statistics/population-estimand-and-sampling-frame','machine-learning/group-and-time-validation'])

add('data-annotation/agreement-and-disagreement-review',
    'Inter-reviewer agreement: what the percentage hides',
    'Agreement measures consistency between reviewers; it does not establish that either reviewer is correct.', [
    ('Compute on paired units', 'Compare reviewers only when they judged the same evidence revision under the same guideline version. Count exact matches and build a confusion table by label pair. If 44 of 47 decisions match, raw agreement is 44 divided by 47, about 93.6%; it says nothing about which three were right. [[data-annotation/label-unit-taxonomy-and-guidelines|The unit contract]] must remain identical across the pair.'),
    ('Inspect prevalence', 'If nearly every receipt is accepted, two reviewers can agree often by repeatedly choosing accepted. Report class prevalence, per-class disagreement and an adjudicated error sample beside the overall percentage. Chance-adjusted statistics can add context but depend on their own assumptions and should not replace a dispute review. Sparse classes may need wider intervals and more targeted annotation before a stable estimate is possible.'),
    ('Turn disputes into cases', 'Group disagreements by reason: unreadable evidence, ambiguous policy, missing context or reviewer mistake. A disputed item should keep both independent judgments, the evidence revision and a review trail. If a guideline changes because of the dispute, do not silently rewrite every earlier answer. [[data-annotation/adjudication-and-gold-set-versioning|Adjudication]] determines the current reference label and preserves its provenance.'),
    ('Probe a failure mode', 'Create 47 paired receipt judgments: 40 accepted matches, four rejected matches and three disagreements. The raw result is 44/47. Now move all three disagreements into the rare rejected class. The headline percentage stays high while the class of operational interest becomes unreliable. Report this slice and collect more independently reviewed rejected candidates.')],
    'def exact_agreement(paired_reviews):\n    comparable = [pair for pair in paired_reviews\n                  if pair["same_evidence"] and pair["same_guideline"]]\n    if not comparable:\n        return None\n    matches = sum(left == right for left, right in\n                  ((pair["first_label"], pair["second_label"]) for pair in comparable))\n    return matches / len(comparable)',
    'A pass over P pairs costs O(P) time and O(1) auxiliary space for the scalar percentage. A label-pair confusion table uses O(K²) space for K labels; review time grows with disputed cases rather than all pairs.',
    ['Do not interpret agreement as accuracy.', 'Do not pair judgments from different evidence or guideline versions.', 'Do not hide rare-class disagreement behind an overall percentage.'],
    ['data-annotation/annotator-assignment-and-blinding','data-annotation/adjudication-and-gold-set-versioning','data-annotation/label-drift-and-audit-sampling','applied-statistics/cluster-bootstrap-and-standard-error'])

add('data-annotation/adjudication-and-gold-set-versioning',
    'Adjudication and gold sets: versioned reference decisions',
    'A reference set should contain reviewed decisions with reasons and history, not a mutable spreadsheet of final answers.', [
    ('Define who decides', 'When two reviewers disagree, a third reviewer can inspect both reasons while making a documented final decision. Escalate policy gaps to a guideline owner rather than forcing a binary choice. Record whether the decision is evidence-based, policy-based or unresolved. A majority vote is not sufficient when all reviewers saw the same misleading crop or misunderstood the same rule.'),
    ('Freeze evaluation versions', 'Publish a gold-set version with item IDs, evidence revisions, guideline version, adjudication outcomes and exclusions. A model evaluation must name that version. If an item is corrected later, create a new version and report the delta; changing labels in place makes historic model comparisons impossible. [[machine-learning/group-and-time-validation|Validation boundaries]] still apply: near-duplicate receipts cannot be split across training and a final test.'),
    ('Review disagreement clusters', 'Sample adjudicated items by scanner source and label class. A reviewer may be consistently wrong for a specific receipt layout, while the aggregate agreement looks fine. Keep the original reviews visible to authorized auditors. Repeated disagreements of the same type signal that the guideline needs a sharper boundary or the interface needs more evidence, not that more voting is automatically useful.'),
    ('Run a correction drill', 'Freeze 47 items as gold version 3. A later scan reveals two totals were cropped and one class rule was applied incorrectly. Publish version 4 with those three item-level corrections and reasons, then rerun a held-out model against both versions. The reported score difference should identify label corrections separately from a model change.')],
    'def gold_delta(previous, current):\n    return {receipt_id: (previous.get(receipt_id), current.get(receipt_id))\n            for receipt_id in previous.keys() | current.keys()\n            if previous.get(receipt_id) != current.get(receipt_id)}',
    'Comparing G item IDs costs O(G) expected time and O(D) output space for D changes. Versioned evidence and decisions consume more storage, but make test-score changes and label corrections auditable.',
    ['Do not overwrite a frozen gold set in place.', 'Do not resolve a policy ambiguity by unexplained majority vote.', 'Do not mix near duplicates between model training and final evaluation.'],
    ['data-annotation/agreement-and-disagreement-review','data-annotation/active-learning-and-selection-bias','machine-learning/group-and-time-validation','mlops/drift-delayed-label-monitoring'])

add('data-annotation/active-learning-and-selection-bias',
    'Active-learning queues: uncertainty, coverage and selection bias',
    'Model uncertainty can prioritize review effort, but selected labels describe the selected queue unless a separate sample supports wider claims.', [
    ('Choose an acquisition rule', 'Select candidates by calibrated uncertainty, disagreement among models or expected operational value. Deduplicate near-identical receipts before allocation so a scanner burst does not consume the budget. Reserve slots for random exploration and under-covered sources. [[machine-learning/probability-calibration|Calibration]] matters if a score is interpreted as uncertainty; low confidence may also reflect a shifted scanner or missing input.'),
    ('Preserve inclusion information', 'Log the acquisition score, queue policy, model version, source stratum and probability of selection when randomized. Without those fields, an evaluated model may appear to improve simply because the next training batch contained unusually difficult cases. The final held-out test must remain untouched by the selection loop. [[applied-statistics/population-estimand-and-sampling-frame|The sampling frame]] limits any population-level performance statement.'),
    ('Balance learning and auditing', 'The active queue is built to improve the model. A blinded random audit is built to estimate current quality. Budget and report them separately even if the same reviewers operate both workflows. Review false negatives from production after their labels mature, but do not leak those outcomes into a prospective test whose prediction time preceded them.'),
    ('Simulate a cycle', 'A queue has 47 receipts: 20 uncertain, 12 from a new scanner and 15 routine. With 12 review slots, choose six uncertain, three new-scanner and three randomized routine items. Record the rule and inclusion route for every chosen item. Refit only on reviewed labels, then evaluate on a frozen future batch rather than on the acquired queue.')],
    'def select_review_queue(scored_receipts, review_slots):\n    ranked = sorted(scored_receipts,\n                    key=lambda receipt: (-receipt["uncertainty"], receipt["receipt_id"]))\n    chosen = []\n    seen_sources = set()\n    for receipt in ranked:\n        if len(chosen) == review_slots:\n            break\n        if receipt["source"] not in seen_sources:\n            chosen.append(receipt["receipt_id"])\n            seen_sources.add(receipt["source"])\n    chosen_ids = set(chosen)\n    for receipt in ranked:\n        if len(chosen) == review_slots:\n            break\n        if receipt["receipt_id"] not in chosen_ids:\n            chosen.append(receipt["receipt_id"])\n            chosen_ids.add(receipt["receipt_id"])\n    return chosen',
    'Sorting N candidates costs O(N log N) time and O(N) space. The snippet demonstrates a deterministic ranking with source coverage; a real audit needs a separate randomized sampler and logged inclusion probabilities.',
    ['Do not evaluate population quality on an uncertainty-selected queue.', 'Do not let duplicate scans exhaust the review budget.', 'Do not use the final test set to drive acquisition.'],
    ['data-annotation/annotator-assignment-and-blinding','data-annotation/label-drift-and-audit-sampling','machine-learning/probability-calibration','applied-statistics/population-estimand-and-sampling-frame'])

add('data-annotation/label-drift-and-audit-sampling',
    'Label drift: delayed outcomes and sampled quality audits',
    'A label pipeline can degrade when the source mix, guideline, interface or outcome delay changes.', [
    ('Separate three changes', 'A new receipt layout changes evidence; an updated rejection policy changes the meaning of a label; and a slower refund process delays ground truth. Monitor these separately. Compare reviewer disagreement, unknown rates and adjudication reasons by source and week. [[mlops/drift-delayed-label-monitoring|Delayed-label monitoring]] explains why a current cohort may look clean simply because its failures have not arrived.'),
    ('Audit a stable frame', 'Sample from all eligible receipts before escalation or model routing. Retain source, date, guideline and selection probability so a weighted estimate can be constructed for the intended population. Oversample rare scanner types for diagnosis, but weight or report them separately when estimating overall error. Do not mix an investigation sample with an independent audit in one headline metric.'),
    ('Account for reviewer fatigue', 'Measure time per decision, repeated-item consistency and disagreement by reviewer shift. A spike in unknown labels may reflect worse images or exhausted reviewers. Rotate audit items and periodically recheck blinded stable fixtures, but avoid making them so recognizable that reviewers memorize answers. Escalate recurring rule gaps to the guideline owner with examples and a proposed revision.'),
    ('Run an alarm review', 'Suppose unknown labels climb from 4 of 47 to 13 of 47 after a new scanner deployment. Check evidence availability, assignment mix and guideline version before declaring model drift. Pull a source-stratified blind sample, adjudicate disagreements and report whether the new scanner changed the item population, image quality or reviewer interpretation.')],
    'def unknown_rate(review_rows, source):\n    selected = [review for review in review_rows if review["source"] == source]\n    if not selected:\n        return None\n    return sum(review["label"] == "unknown" for review in selected) / len(selected)',
    'A source-filtered pass costs O(N) time and O(N) space in this simple form; streaming counters reduce space to O(S) for S sources. Confidence bounds and population weighting need the audit design and sampling probabilities.',
    ['Do not confuse late outcomes with a true zero-error cohort.', 'Do not combine targeted investigations with random audits without labeling the samples.', 'Do not attribute every disagreement spike to the model.'],
    ['data-annotation/agreement-and-disagreement-review','data-annotation/active-learning-and-selection-bias','mlops/drift-delayed-label-monitoring','anomaly-detection/incident-unit-and-label-contract'])

add('data-annotation/receipt-review-labeling-project',
    'Project: build a receipt-labeling and adjudication packet',
    'Build a small but auditable review pipeline with independent judgments, dispute resolution and a frozen evaluation set.', [
    ('Prepare evidence and rules', 'Create 47 synthetic receipt records across three scanner sources with clean, cropped and duplicated cases. Give each an immutable ID, evidence revision and event timestamp. Write a four-state taxonomy with inclusion and exclusion rules. The receipts are a controlled fixture for exercising the workflow, not a claim that generated examples represent live traffic. [[data-annotation/label-unit-taxonomy-and-guidelines|The label contract]] should be readable without a model score.'),
    ('Assign and adjudicate', 'Randomly select an audit set from the full fixture and route a separate hard-case queue. Give 12 items two blind reviews by distinct reviewers. Retain each raw decision, confidence, reason and guideline version. Adjudicate conflicts with a recorded policy or evidence reason; leave truly unresolved items unknown. Compare overall and per-class agreement without treating agreement as accuracy.'),
    ('Freeze and evaluate', 'Version the adjudicated gold set. Hold out a source and later time period for a simple classifier or rule system; duplicate scans must stay in one split. Report coverage, unknown rate and errors by scanner. Revise three labels under a new guideline and show the exact gold-set diff. [[data-annotation/adjudication-and-gold-set-versioning|A frozen reference]] makes the comparison reproducible.'),
    ('Deliver the audit trail', 'Submit the fixture generator, rules, assignment ledger, original labels, adjudication log, gold versions, evaluation script and a one-page error review. Include one item that changed because the evidence revision changed and another that changed because the policy changed. State which sample supports a population estimate and which sample was only used to improve the model.')],
    'def review_packet_complete(packet):\n    required = {"guideline_version", "assignment_ledger", "raw_reviews",\n                "adjudications", "gold_version", "split_manifest"}\n    return required <= packet.keys() and all(packet[field] for field in required)',
    'Packet field validation is O(1) for a fixed contract. Generating and checking R reviews costs O(R); adjudication work is driven by disagreements and policy gaps, while duplicate-aware splitting requires a group index.',
    ['Do not reuse the hard-case queue as an unbiased final test.', 'Do not discard pre-adjudication reviewer decisions.', 'Do not report a changed score without the gold-set version.'],
    ['data-annotation/label-unit-taxonomy-and-guidelines','data-annotation/adjudication-and-gold-set-versioning','data-annotation/label-drift-and-audit-sampling','synthetic-data/generation-purpose-and-fidelity-contract'])

add('synthetic-data/generation-purpose-and-fidelity-contract',
    'Synthetic-data contracts: purpose, units and fidelity',
    'Generated records are useful only relative to a declared task, data unit and set of properties they must preserve.', [
    ('Name the use', 'A receipt fixture for testing a parser needs valid field formats and intentionally malformed edge cases. A dataset for estimating model utility needs relationships that resemble the target population. Those uses impose different fidelity requirements. Write the intended unit, schema, consumers and prohibited claims before generating anything. [[data-science/dataset-grain-and-join-cardinality|Dataset grain]] prevents a generated line item from being mistaken for a whole receipt.'),
    ('Separate methods', 'Rule-based generators make constraints explicit and are good for pipeline tests. A model fitted to real data may better match some correlations, yet can reproduce training examples or carry inherited bias. A simulator models mechanisms and interventions but can be wrong about its assumptions. None of these methods makes output automatically private, realistic or suitable for a held-out evaluation.'),
    ('Declare fidelity checks', 'List properties by priority: field validity, missingness, temporal order, cross-field logic, rare-case coverage and relationships relevant to the downstream task. A single similarity score cannot prove all of them. Keep generated and original rows marked by provenance through every transformation. [[synthetic-data/utility-and-holdout-evaluation|Utility tests]] should be chosen for the actual consumer, not because a generated histogram looks convincing.'),
    ('Test a mismatch', 'Generate 47 receipts with plausible totals but no discounts, then run a parser that fails on discounted totals. The fixture passes basic schema validation yet misses the important failure mode. Add a discounted scenario and assert tax, subtotal and total reconcile. Record which new cases were added and which claims remain untested; avoid declaring overall production coverage from this one fixture.')],
    'def receipt_total(subtotal_cents, discount_cents, tax_cents):\n    if min(subtotal_cents, discount_cents, tax_cents) < 0:\n        raise ValueError("negative component")\n    if discount_cents > subtotal_cents:\n        raise ValueError("discount exceeds subtotal")\n    return subtotal_cents - discount_cents + tax_cents',
    'The arithmetic check is O(1) per receipt. Generating N rows costs at least O(N) time and storage; fidelity evaluation adds scans, group summaries and task-specific tests that may dominate generation.',
    ['Do not claim a schema-valid fixture represents production.', 'Do not equate generated records with privacy protection.', 'Do not forget the use case when choosing fidelity metrics.'],
    ['synthetic-data/schema-and-relational-integrity','synthetic-data/rare-case-simulation-and-coverage','data-science/dataset-grain-and-join-cardinality','privacy-aware-ml/threat-model-and-data-minimization'])

add('synthetic-data/schema-and-relational-integrity',
    'Synthetic relational data: keys, chronology and integrity',
    'A generated table collection must satisfy the relationships its consumers expect, not just the type of each column.', [
    ('Model the graph of records', 'A receipt has one merchant and multiple line items; a refund refers to an existing payment. Define primary keys, foreign keys, cardinality, uniqueness and required fields before generation. Generate parent entities first and child rows second, or use a joint method with explicit constraints. [[data-engineering/source-contract-and-raw-landing|Source contracts]] help identify the fields downstream joins rely on.'),
    ('Check event order', 'Receipt creation, payment, settlement and refund form a temporal sequence, with exceptions such as delayed settlement. Use explicit event time and recorded time when simulating retries or corrections. A refund before any payment can be a deliberate bad record in a quarantine test, but should be labeled as such; otherwise the fixture quietly teaches a pipeline to accept impossible histories.'),
    ('Preserve enough correlation', 'Independent random columns often produce implausible combinations even when each marginal distribution looks correct. A large basket may correlate with price and tax; a scanner source may correlate with image quality. Encode relationships required by the test and measure whether they hold. Be careful: fitting those relationships from sensitive real records can create disclosure risk, so the privacy gate remains separate.'),
    ('Break it on purpose', 'Create 47 payments, 52 receipt rows and six refunds. Insert one orphan refund, one duplicate payment ID and one refund timestamp before its payment. The integrity gate should reject exactly those deliberate exceptions. Save a clean version as a parser test and the broken version as a quarantine test, with scenario labels explaining why each bad record exists.')],
    'def invalid_refunds(payments, refunds):\n    payment_time = {payment["payment_id"]: payment["paid_at"] for payment in payments}\n    return [refund["refund_id"] for refund in refunds\n            if refund["payment_id"] not in payment_time\n            or refund["refunded_at"] < payment_time[refund["payment_id"]]]',
    'Building a payment index costs O(P) expected time and space; validating R refunds costs O(R) expected time and O(B) space for B invalid IDs. Real databases should enforce keys transactionally as well as in fixture checks.',
    ['Do not generate child rows before their referenced parents exist.', 'Do not confuse a deliberate corrupt fixture with a clean training record.', 'Do not trust individually plausible columns to form plausible rows.'],
    ['synthetic-data/generation-purpose-and-fidelity-contract','synthetic-data/rare-case-simulation-and-coverage','data-engineering/quality-quarantine-and-reconciliation','data-engineering/event-time-and-late-arrivals'])

add('synthetic-data/rare-case-simulation-and-coverage',
    'Rare-case simulation: scenario coverage and domain gap',
    'Controlled synthetic scenarios expose specific failure modes, but their frequency and appearance need not match live traffic.', [
    ('Build a scenario matrix', 'List combinations that matter to the consumer: cropped totals, duplicate uploads, mixed tax rates, delayed refunds and scanner-specific blur. Mark expected behavior for each, including rejection and manual review. Pair ordinary cases with extreme values so a parser is not tuned only to the spectacular failures. [[data-annotation/label-unit-taxonomy-and-guidelines|Label rules]] should classify every generated scenario without using its generator tag as a shortcut.'),
    ('Vary causes, not just values', 'Changing a price from 47 to 48 tests one numeric range. Changing whether a discount applies before tax tests logic. Model source-specific missingness, order changes and retries when those mechanisms cause real failures. Hold some generator templates out of development tests; otherwise a model can memorize the synthetic style and appear to generalize while failing on a new scanner.'),
    ('Quantify coverage honestly', 'Report how many scenarios exist, which constraints they hit and which consumers passed them. Distinguish scenario coverage from population prevalence. A generated set with 30% refunds may be excellent for exercising refund logic yet useless for estimating the true refund rate. [[synthetic-data/utility-and-holdout-evaluation|Real holdout evaluation]] is needed before making a claim about deployment performance.'),
    ('Run an adversarial batch', 'Generate 47 receipts: 20 ordinary, nine discounted, eight scanned twice, six with delayed refunds and four with cropped totals. Test a pipeline for duplicate handling, reconciliation and manual-review routing. Then replace the text template and scanner dimensions while keeping the same semantic scenarios. A large score drop reveals template dependence rather than a new business rule.')],
    'def scenario_counts(generated_rows):\n    counts = {}\n    for receipt in generated_rows:\n        scenario = receipt["scenario"]\n        counts[scenario] = counts.get(scenario, 0) + 1\n    return counts',
    'Counting N generated rows costs O(N) time and O(S) space for S scenarios. Exhaustive combinations grow multiplicatively with independent factors, so prioritize by risk and known incident patterns.',
    ['Do not treat scenario proportions as real prevalence.', 'Do not test only against the same templates used during development.', 'Do not use a generator tag as an input feature for the model being evaluated.'],
    ['synthetic-data/schema-and-relational-integrity','synthetic-data/utility-and-holdout-evaluation','data-annotation/label-unit-taxonomy-and-guidelines','anomaly-detection/incident-unit-and-label-contract'])

add('synthetic-data/utility-and-holdout-evaluation',
    'Synthetic-data utility: downstream tests on an untouched holdout',
    'Utility is measured by the decision or workflow the generated data supports, using real outcomes that generation never saw.', [
    ('Define comparison arms', 'Train or tune the same downstream model on real-only, generated-only and mixed data where policy permits. Keep model architecture, feature pipeline and evaluation horizon fixed. A generated dataset may improve rare-case recall while lowering calibration or performance on ordinary traffic. Report that tradeoff rather than reducing it to one score. [[machine-learning/group-and-time-validation|Group and time splits]] protect the real holdout from repeated receipt templates.'),
    ('Keep the holdout independent', 'Choose a later time period or unseen source before generator fitting and parameter tuning. Do not use its errors to rewrite the generator repeatedly and still call it untouched. If the holdout is used for iteration, create a new final evaluation set. Record generator version, training-data cutoff and any filters that could move real observations into the synthetic training source.'),
    ('Check more than marginals', 'Compare constraints, joint relationships, missingness and task metrics by subgroup. Histograms can agree while a merchant-tax dependency is inverted. For a parser, compare field accuracy and manual-review burden; for forecasting, compare error by horizon and source. [[synthetic-data/rare-case-simulation-and-coverage|Scenario tests]] identify known failures, but they cannot measure unknown real-world shifts.'),
    ('Work through a result', 'Suppose a generated-only parser recovers 42 of 47 fields in a new-scanner holdout while a real-only baseline recovers 44. The generated set still may be useful if it catches a refund edge case, but do not claim general improvement. Inspect errors, confidence and support counts. Keep a predeclared release threshold so a selectively reported slice cannot override the full result.')],
    'def accuracy_by_source(predictions):\n    totals = {}\n    correct = {}\n    for result in predictions:\n        source = result["source"]\n        totals[source] = totals.get(source, 0) + 1\n        correct[source] = correct.get(source, 0) + int(result["predicted"] == result["actual"])\n    return {source: correct[source] / count for source, count in totals.items()}',
    'Grouping N predictions costs O(N) time and O(S) space for S sources. Training and evaluation costs depend on the downstream model; repeated holdout use adds statistical selection cost even when runtime is cheap.',
    ['Do not evaluate on records used to fit or tune the generator.', 'Do not substitute visual similarity for downstream utility.', 'Do not hide subgroup regressions behind a pooled metric.'],
    ['synthetic-data/generation-purpose-and-fidelity-contract','synthetic-data/memorization-and-disclosure-risk','machine-learning/group-and-time-validation','data-visualization/distribution-and-outlier-displays'])

add('synthetic-data/memorization-and-disclosure-risk',
    'Synthetic-data privacy: copies, nearest neighbors and disclosure',
    'Generated output can repeat sensitive source records; a synthetic label is not a privacy guarantee.', [
    ('Start with the threat model', 'Name who receives the data, what auxiliary facts they might know and what disclosure would harm a person or organization. Exact copies are easy to find, but a near copy with a changed ID can still reveal sensitive attributes. Very rare combinations may be identifying even when names are removed. [[privacy-aware-ml/threat-model-and-data-minimization|Threat modeling]] determines which checks and access controls are relevant.'),
    ('Run several checks', 'Compare generated rows with training records for exact duplicates and task-appropriate near neighbors. Inspect rare combinations, memorized free text and subgroup disclosure. Measure utility separately so privacy controls are not justified by a useless output. A distance threshold alone is not proof of safety: the metric may miss semantic similarity or external linkage through quasi-identifiers.'),
    ('Know the guarantee boundary', 'A formally private training procedure can offer a stated bound under defined assumptions and accounting; an ordinary generator with filters cannot claim that bound. Even with a formal guarantee, released samples may be unsuitable for a particular use or may contain harmful patterns. Preserve restricted training inputs, generator versions, audit outcomes and approval records. [[synthetic-data/reproducibility-and-release-gates|Release gates]] should fail closed when a check has not run.'),
    ('Check a disguised copy', 'Take a sensitive training receipt, change only its generated receipt ID and append it to an otherwise plausible release. An exact full-row comparison misses the copy, while a comparison on stable content fields catches it. Then test an unusual merchant-date-total combination. Document what each check detects and which linkage risks remain outside the test.')],
    'def duplicate_content_keys(training_rows, generated_rows):\n    keys = {tuple(row[field] for field in ("merchant", "day", "total_cents"))\n            for row in training_rows}\n    return [row["synthetic_id"] for row in generated_rows\n            if tuple(row[field] for field in ("merchant", "day", "total_cents")) in keys]',
    'Hashing T training keys and checking G generated rows costs O(T + G) expected time, O(T + D) space for D matches. Near-neighbor checks can cost much more and depend heavily on the similarity definition.',
    ['Do not call de-identified or generated data automatically private.', 'Do not rely on exact full-row equality alone.', 'Do not claim a formal privacy guarantee without a mechanism and accounted parameters.'],
    ['synthetic-data/utility-and-holdout-evaluation','synthetic-data/reproducibility-and-release-gates','privacy-aware-ml/threat-model-and-data-minimization','privacy-aware-ml/privacy-budget-and-safe-release'])

add('synthetic-data/reproducibility-and-release-gates',
    'Synthetic-data releases: seeds, manifests and rejection gates',
    'A generated dataset should be traceable to a versioned method and released only after declared checks pass.', [
    ('Record the full recipe', 'Store generator code revision, configuration, seed, schema version, training-source cutoff, constraint rules and any postprocessing. A seed helps reproduce a deterministic test fixture, but a seeded pseudorandom generator is not a privacy mechanism. If a learned model has nondeterministic training, record the environment and artifact hash as well. [[data-engineering/backfill-publication-boundary|Publication boundaries]] prevent partial versions from leaking into consumers.'),
    ('Gate distinct risks', 'Run schema and relational checks, scenario coverage, downstream utility against an untouched holdout, disclosure review and access-policy checks. A failure in any required gate blocks release; a high utility score cannot cancel a privacy failure. Capture counts of rejected rows and reasons, not only a pass flag. Manual approval should reference the exact dataset checksum being approved.'),
    ('Plan withdrawal', 'Publish a manifest that names the dataset version, intended consumers, expiry or review date and rollback location. If a later disclosure test finds a problematic near copy, withdraw that version and invalidate downstream caches or training runs as policy requires. Keep an incident trace linking the generated row to the generator and source cohort without exposing sensitive source records in public reports.'),
    ('Rebuild and compare', 'Generate 47 receipt rows twice with the same recipe and verify checksums match in the deterministic fixture case. Change the tax constraint and confirm a new version and checksum appear. Force one orphan refund and one source-copy match; both gates should block publication while preserving a diagnostic report. The release decision must name the exact failed checks.')],
    'def release_allowed(gate_results):\n    required = {"schema", "relationships", "coverage", "utility", "disclosure"}\n    return required <= gate_results.keys() and all(gate_results[name] for name in required)',
    'Checking a fixed set of gates is O(1). Computing a checksum and scanning N rows is O(N) time; model training, subgroup evaluation and near-copy analysis usually dominate the actual release cost.',
    ['Do not mistake a seed for a privacy guarantee.', 'Do not approve one checksum and publish another.', 'Do not leave downstream consumers on a withdrawn dataset version.'],
    ['synthetic-data/schema-and-relational-integrity','synthetic-data/utility-and-holdout-evaluation','synthetic-data/memorization-and-disclosure-risk','data-engineering/backfill-publication-boundary'])

add('synthetic-data/receipt-pipeline-simulator-project',
    'Project: simulate a receipt pipeline and prove its limits',
    'Construct a reproducible receipt-event fixture, test downstream behavior, and produce an honest utility and disclosure report.', [
    ('Specify the recipe', 'Define merchants, receipts, line items, payments and refunds with stable keys and temporal rules. Generate 47 receipt events across three scanner sources, including discounts, duplicates, late settlements and cropped totals. Mark every event with a scenario and generator version. [[synthetic-data/schema-and-relational-integrity|Relational checks]] should reject orphan refunds and impossible chronology before the clean fixture is published.'),
    ('Exercise the pipeline', 'Feed the clean and intentionally broken versions through a parser or event pipeline. Assert idempotent handling of repeated receipt IDs, correction after a late event and reconciliation of subtotal, discount, tax and total. The broken fixture should quarantine its labeled exceptions rather than silently succeeding. Compare outcomes across a second set of unseen text templates to expose dependence on the generator’s style.'),
    ('Evaluate utility and privacy', 'Choose an untouched real holdout if access is authorized; otherwise state that deployment utility remains unverified. Compare a baseline with a synthetic-assisted workflow by source and scenario, reporting support counts and errors. Test for exact content matches and near-copy candidates against any restricted training input. [[synthetic-data/memorization-and-disclosure-risk|A disclosure review]] is required before a release containing learned outputs.'),
    ('Package the evidence', 'Deliver code, seed, configuration, input manifest, dataset checksum, schema report, scenario matrix, pipeline assertions, holdout definition, utility table and disclosure findings. Force one failed gate and show that publication is blocked. Include a withdrawal procedure for a previously released version. A reviewer should reproduce one ordinary receipt and one late-refund correction from the same versioned recipe.')],
    'def reconcile_receipt(receipt):\n    expected = receipt["subtotal_cents"] - receipt["discount_cents"] + receipt["tax_cents"]\n    return receipt["total_cents"] == expected and receipt["discount_cents"] <= receipt["subtotal_cents"]',
    'Reconciling one receipt is O(1); processing N events and indexing IDs is O(N) expected time and space. Real utility and disclosure checks add model evaluation and neighbor searches beyond this fixture-level assertion.',
    ['Do not present simulated results as measured production behavior.', 'Do not release rows from a failed privacy or integrity gate.', 'Do not omit scenario and generator versions from the packet.'],
    ['synthetic-data/generation-purpose-and-fidelity-contract','synthetic-data/utility-and-holdout-evaluation','synthetic-data/reproducibility-and-release-gates','streaming-analytics/idempotent-sink-and-replay'])

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
 'data-annotation': {
     'root':'data-annotation/data-annotation-tutorial', 'name':'Data Annotation & Label Quality',
     'summary':'Specify label rules, independent review, agreement, adjudication, active-learning selection and ongoing audits.',
     'groups':[('Label and assign', ['label-unit-taxonomy-and-guidelines','annotator-assignment-and-blinding','agreement-and-disagreement-review']),
               ('Resolve and monitor', ['adjudication-and-gold-set-versioning','active-learning-and-selection-bias','label-drift-and-audit-sampling'])],
     'project':'receipt-review-labeling-project',
     'foundation':['applied-statistics/applied-statistics-tutorial','machine-learning/machine-learning-tutorial'],
     'neighbors':['computer-vision/computer-vision-tutorial','synthetic-data/synthetic-data-tutorial']},
 'synthetic-data': {
     'root':'synthetic-data/synthetic-data-tutorial', 'name':'Synthetic Data & Simulation',
     'summary':'Create controlled fixtures while checking relational validity, rare-case coverage, real-world utility and disclosure risk.',
     'groups':[('Design and generate', ['generation-purpose-and-fidelity-contract','schema-and-relational-integrity','rare-case-simulation-and-coverage']),
               ('Evaluate and release', ['utility-and-holdout-evaluation','memorization-and-disclosure-risk','reproducibility-and-release-gates'])],
     'project':'receipt-pipeline-simulator-project',
     'foundation':['data-engineering/data-engineering-tutorial','privacy-aware-ml/privacy-aware-ml-tutorial'],
     'neighbors':['data-annotation/data-annotation-tutorial','streaming-analytics/streaming-analytics-tutorial']},
}

for config in subject_config.values():
    titles[config['root']] = config['name'] + ' Tutorial'
    titles[config['root'] + '/project'] = config['name'] + ': Projects'

for slug, config in subject_config.items():
    root_path = config['root']
    project_hub_path = root_path + '/project'
    modules = [{'title':group_title, 'summary':'Read in order and test the failure cases.',
                'lessons':[slug + '/' + lesson_name for lesson_name in lesson_names]}
               for group_title, lesson_names in config['groups']]
    project_path = slug + '/' + config['project']
    modules.append({'title':'Apply your knowledge', 'lessons':[project_path]})
    all_paths = [path for module in modules for path in module['lessons']]
    tabs = [{'title':config['name'], 'path':root_path}, {'title':'Projects', 'path':project_hub_path}]
    hub_body = ('<p>' + html.escape(config['summary']) + '</p><h2>Learning path</h2>' + links(all_paths)
                + '<h2>Connected foundations</h2><p>Use these data and evaluation contracts before the project.</p>'
                + links(config['foundation']) + '<h2>Further paths</h2>' + links(config['neighbors'])
                + '<h2>Practice</h2>' + links([project_hub_path]))
    hub = make_row(root_path, titles[root_path], config['summary'], hub_body,
                   'subject', slug, root_path, root_path, 10800 if slug == 'data-annotation' else 10900,
                   {'modules':modules, 'resource_tabs':tabs})
    project_body = ('<p>Apply the ' + html.escape(config['name']) + ' curriculum to an auditable project.</p>'
                    '<h2>Project brief</h2>' + links([project_path])
                    + '<h2>Required concepts</h2>' + links(all_paths[:-1])
                    + '<h2>Completion standard</h2><p>Submit runnable work, a manifest, measured results and documented failure cases.</p>')
    project_hub = make_row(project_hub_path, titles[project_hub_path],
                           'A checked project for the ' + config['name'] + ' curriculum.', project_body,
                           'subject', slug + '-project', project_hub_path, root_path,
                           10801 if slug == 'data-annotation' else 10901,
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
                       11000 + index,
                       {'kind':'project' if is_project else 'tutorial',
                        'reading_minutes':max(5, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                        'author_path':'authors/aitrove-editorial',
                        'verification_suite':'Editorial and syntax review; project inputs needed for runtime checks',
                        'related':[{'path':path,'title':titles[path]} for path in item['related']]})
    rows.append(article)
    by_path[item['path']] = article

for source, target in [
    ('computer-vision/annotation-geometry-and-quality','data-annotation/label-unit-taxonomy-and-guidelines'),
    ('machine-learning/group-and-time-validation','data-annotation/adjudication-and-gold-set-versioning'),
    ('mlops/drift-delayed-label-monitoring','data-annotation/label-drift-and-audit-sampling'),
    ('anomaly-detection/incident-unit-and-label-contract','data-annotation/active-learning-and-selection-bias'),
    ('data-science/dataset-grain-and-join-cardinality','synthetic-data/generation-purpose-and-fidelity-contract'),
    ('data-engineering/quality-quarantine-and-reconciliation','synthetic-data/schema-and-relational-integrity'),
    ('privacy-aware-ml/threat-model-and-data-minimization','synthetic-data/memorization-and-disclosure-risk'),
    ('data-visualization/distribution-and-outlier-displays','synthetic-data/utility-and-holdout-evaluation'),
]:
    row = by_path[source]
    anchor = '<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in row['body']:
        row['body'] += anchor
        if row['type'] == 'article':
            row['data']['related'].append({'path':target,'title':titles[target]})
        row['updated_at'] = stamp

for source, target in [
    ('computer-vision/computer-vision-tutorial','data-annotation/data-annotation-tutorial'),
    ('applied-statistics/applied-statistics-tutorial','data-annotation/data-annotation-tutorial'),
    ('data-engineering/data-engineering-tutorial','synthetic-data/synthetic-data-tutorial'),
    ('privacy-aware-ml/privacy-aware-ml-tutorial','synthetic-data/synthetic-data-tutorial'),
]:
    row = by_path[source]
    anchor = '<p><strong>Continue into another subject:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in row['body']:
        row['body'] += anchor
        row['updated_at'] = stamp

assert len({row['path'] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_articles':len(lessons), 'new_subject_hubs':4, 'crosslinks_from_existing':12}))
