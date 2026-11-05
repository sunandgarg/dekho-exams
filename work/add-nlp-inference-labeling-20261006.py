"""Add claim inference and reviewed data acquisition to NLP."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
I = 'Entailment and contradiction checks'
A = 'Active annotation and adjudication'
lessons = [
    {
        'path': N + 'nli-premise-hypothesis-and-evidence-contract',
        'title': 'Textual entailment: premise, hypothesis and evidence boundaries',
        'module': I, 'project': False,
        'summary': 'Similarity is not entailment. A claim about a completed refund needs source evidence that supports completion, not merely a passage containing the same order ID.',
        'sections': [
            ('Name the two texts', 'The premise is a versioned source passage; the hypothesis is the claim being checked. Entailment means the premise supports the hypothesis under the task policy, contradiction means it supports an incompatible statement, and neutral means neither follows. A sentence about “refund requested” is neutral to “refund completed,” even if the phrases are close in an embedding space. Preserve document revision, speaker and time with each pair. [[natural-language-processing/document-summary-evidence-contract|Summary evidence]] depends on this distinction.'),
            ('Define the scope of inference', 'A premise can be insufficient because the relevant fact lives in another paragraph, or because the source itself is ambiguous. Keep a separate retrieval-evidence label so a neutral model output is not automatically interpreted as “the fact is false.” Include negation, quantities, temporal qualifiers, ownership and modal verbs in the audit set. Annotate the minimal source span that justifies a non-neutral label. If reviewers cannot agree, mark the case disputed rather than forcing a training class.'),
            ('Avoid shortcut labels', 'Models can exploit lexical overlap and domain templates. Build counterexamples where the same identifiers appear with opposite status or where the relation direction reverses. Split by incident, document family and time. If a template sentence appears in both train and final audit, apparent performance may come from memorizing its wording. [[natural-language-processing/grouped-temporal-text-validation|Grouped temporal validation]] applies to premise-hypothesis pairs just as it does to ticket classifiers.'),
            ('Gate operational use', 'Report per-class precision and recall, unsupported-claim false negatives, abstention coverage and error slices. An entailment score is a screening signal, not automatic proof. Require the source span to round-trip, the revision to be current and access to be authorized. For high-impact claims, route ambiguous scores to a reviewer. [[natural-language-processing/claim-conflict-and-temporal-review|Conflict review]] adds corrections and time; the [[natural-language-processing/incident-claim-verification-project|project]] tests the full chain.'),
        ],
        'code': '''def inference_record(premise_id, premise_revision, hypothesis, label, evidence_span):
    if label not in {"entails", "contradicts", "neutral"}:
        raise ValueError("unknown inference label")
    if not premise_id or not premise_revision or not hypothesis.strip():
        raise ValueError("source and claim are required")
    if label != "neutral" and evidence_span is None:
        raise ValueError("non-neutral label needs source evidence")
    return {"premise_id": premise_id, "revision": premise_revision,
            "hypothesis": hypothesis, "label": label, "evidence_span": evidence_span}

claim = inference_record("incident-47", "note-v3", "The retry completed.",
                         "entails", (12, 27))
assert claim["label"] == "entails"
''',
        'cost': 'The record validator is O(1) time and space apart from copying the claim. Checking many hypotheses against many passages can be O(c·p) model calls for c claims and p passages; retrieval should narrow candidates, but report its recall before claiming verifier quality. Human adjudication of ambiguous cases is the main editorial cost. Keep evidence and access checks even if they add serving latency.',
        'mistakes': ['Treating semantically similar text as proof of a claim.', 'Interpreting neutral as a contradiction or as a false fact.', 'Letting a non-neutral label through without a source span.', 'Evaluating only clean pairs while ignoring retrieval and revision failures.'],
        'related': [N + 'claim-conflict-and-temporal-review', N + 'incident-claim-verification-project', N + 'document-summary-evidence-contract', N + 'qa-answerability-and-calibration', N + 'grouped-temporal-text-validation'],
    },
    {
        'path': N + 'claim-conflict-and-temporal-review',
        'title': 'Review claim conflicts across time and source revisions',
        'module': I, 'project': False,
        'summary': 'Two passages can both be accurate records of what was believed at different times. A verifier must distinguish superseded claims from live contradictions.',
        'sections': [
            ('Identify the source state', 'An incident log may say at 14:07 that the queue is healthy and at 14:47 that the queue is saturated. Those statements can describe a change, not an inconsistency. Another note might retract an earlier diagnosis. Store observed time, publication time, author, revision and explicit retraction links. A claim about the current state needs the latest authorized evidence, not simply the highest-scoring text match. [[natural-language-processing/nli-premise-hypothesis-and-evidence-contract|The inference contract]] defines what each passage supports in isolation.'),
            ('Classify the disagreement', 'Mark pairs as compatible change, genuine conflict, supersession or unresolved ambiguity. A model that sees opposing words without timestamps may overreport contradiction. Conversely, a new statement does not automatically supersede an older one if it refers to a different system or scope. Review entity identity and affected product version. Preserve both quotes and their offsets for audit, with restricted access where needed.'),
            ('Prioritize harmful conflicts', 'A wrong amount, owner or mitigation status deserves a higher review priority than a stylistic difference. Build reviewed examples with numeric shifts, negation, uncertain causes and source corrections. Report false accepted current claims, missed conflicts and unnecessary review volume. Split by incident and time to keep copied updates together. Automated overlap metrics cannot establish which assertion is authoritative.'),
            ('Return a cautious result', 'The checker should return current-supported, superseded, conflicting or needs-review with the relevant source revisions. It must not silently select the newest timestamp if trust levels differ or the latest note is a quoted rumor. A reviewer can resolve the dispute and attach a decision record. [[natural-language-processing/summary-claim-verification-and-review|Summary claim review]] uses that record when drafting a handoff, while the [[natural-language-processing/incident-claim-verification-project|project]] exercises the state model.'),
        ],
        'code': '''def claim_status(evidence_rows):
    approved = [row for row in evidence_rows if row["reviewed"]]
    if not approved:
        return "needs-review"
    latest_time = max(row["observed_at"] for row in approved)
    current = [row for row in approved if row["observed_at"] == latest_time]
    positions = {row["position"] for row in current}
    if len(positions) > 1:
        return "conflicting"
    return "current-supported" if positions == {"supports"} else "current-refuted"

evidence = [{"observed_at": 1407, "position": "refutes", "reviewed": True},
            {"observed_at": 1447, "position": "supports", "reviewed": True}]
assert claim_status(evidence) == "current-supported"
''',
        'cost': 'Scanning r reviewed evidence rows is O(r) time and O(r) temporary space in this simple implementation; a database can index claim key and observation time. Time order alone is not authority, so a production reviewer must also inspect provenance and retraction links. Measure disputed-claim queue age and false current assertions, not just classifier speed.',
        'mistakes': ['Calling a time-evolving status a logical contradiction.', 'Assuming the latest message is always authoritative.', 'Dropping superseded evidence and losing the correction trail.', 'Publishing a confident claim while same-time reviewed sources conflict.'],
        'related': [N + 'nli-premise-hypothesis-and-evidence-contract', N + 'incident-claim-verification-project', N + 'summary-claim-verification-and-review', N + 'coreference-chains-and-mention-identity', N + 'grouped-temporal-text-validation'],
    },
    {
        'path': N + 'incident-claim-verification-project',
        'title': 'Project: verify incident claims against reviewed source revisions',
        'module': I, 'project': True,
        'summary': 'Build a claim-review service that checks supporting spans, flags temporal conflict and never turns a high similarity score into an approved fact.',
        'sections': [
            ('Define the question', 'At shift handoff an agent writes “The callback retry completed at 14:47.” The service must say whether current authorized incident evidence supports that exact claim, contradicts it or leaves it unresolved. Return source revisions, offsets, observed times and review state. An unsupported claim is a draft requiring human action, not a fact with a lower confidence number.'),
            ('Assemble the audit set', 'Use reviewed incident claims with negation, quantity changes, mistaken identities, explicit retractions and multiple source versions. Keep all notes from one incident together when splitting; reserve later incidents for final audit. Store the minimal evidence span for each non-neutral label. [[natural-language-processing/nli-premise-hypothesis-and-evidence-contract|The premise-hypothesis contract]] defines labels; [[natural-language-processing/claim-conflict-and-temporal-review|temporal review]] resolves multi-source status.'),
            ('Measure the full route', 'Retrieve permitted passages first, then score premise-claim pairs and apply current-revision policy. Report evidence retrieval recall, per-label errors, false accepted claims, conflicts sent to review and access failures. Compare a deterministic status-rule baseline with a learned inference model. A classifier that scores well on gold passages but misses later corrections fails the operational release gate.'),
            ('Connect the handoff', 'Only reviewed current-supported claims may enter an automatically prepared incident summary. Keep disputed claims in a restricted queue with their source windows and decision history. Invalidate an approved status when the underlying revision is retired. The [[natural-language-processing/incident-handoff-summary-project|handoff summary project]] consumes the accepted claim ledger, but still requires a human signoff on the final text.'),
        ],
        'code': '''def publishable_claim(inference_label, source_current, source_authorized,
                      reviewer_approved, conflicting_current_sources):
    return (inference_label == "entails" and source_current
            and source_authorized and reviewer_approved
            and not conflicting_current_sources)

assert publishable_claim("entails", True, True, True, False)
assert not publishable_claim("entails", True, True, True, True)
''',
        'cost': 'The final gate is O(1) time and space. Retrieval, inference and adjudication dominate cost; track each stage separately. Source updates can invalidate earlier approvals, so cache claim status only with source revision and review version. A larger model cannot compensate for missing evidence or stale access checks.',
        'mistakes': ['Publishing a claim because one retrieved passage uses similar words.', 'Ignoring a later correction in a separate note.', 'Treating current access as permanent for cached evidence.', 'Measuring model labels but not end-to-end false accepted claims.'],
        'related': [N + 'nli-premise-hypothesis-and-evidence-contract', N + 'claim-conflict-and-temporal-review', N + 'incident-handoff-summary-project', N + 'qa-answerability-and-calibration', N + 'incident-runbook-search-project'],
    },
    {
        'path': N + 'active-learning-sampling-and-coverage',
        'title': 'Active learning for text: uncertainty, diversity and coverage',
        'module': A, 'project': False,
        'summary': 'Labeling only the least-confident tickets can waste reviewers on duplicates and miss confident systematic errors. Balance uncertainty with coverage.',
        'sections': [
            ('State the acquisition goal', 'The goal is not to find hard examples in the abstract. It may be to improve rare intent recall, identify new entity forms or reduce multilingual routing errors. Choose a sampling unit—conversation, document or span—and a review budget. Keep the final audit set out of acquisition. Store model version, score, selected reason and eligible pool snapshot so later evaluation can explain why a case entered training.'),
            ('Mix sampling strategies', 'Uncertainty sampling surfaces borderline cases, but a model can be confidently wrong on an unseen product. Add random samples to estimate population error and diversity samples to cover new channels, languages and features. Group near duplicates before selection; otherwise a large outage can fill the queue with almost identical tickets. Within a language slice, reserve capacity for rare but consequential labels. [[natural-language-processing/classification-slices-and-abstention|Slice evaluation]] identifies where coverage is weak.'),
            ('Control the feedback loop', 'Reviewers should not see the model label as an unquestioned answer. Capture independent decisions for a small overlap set, adjudicate disagreements and log uncertainty. Do not feed a corrected label into training before its policy version and source consent are recorded. A queue full of difficult ambiguous cases may raise disagreement without improving a deployed model. Measure marginal error reduction against a random-sampling baseline after each batch.'),
            ('Keep evaluation independent', 'Split by conversation and time before selecting review candidates. Evaluate on a frozen recent holdout that acquisition cannot alter. Report error by slice and review hours consumed, not merely overall accuracy after adding more labels. [[natural-language-processing/annotation-disagreement-and-label-policy|Disagreement review]] decides whether a sample has a usable label, and the [[natural-language-processing/text-label-acquisition-project|project]] implements the queue.'),
        ],
        'code': '''def select_review_cases(candidates, quota):
    if quota < 1:
        raise ValueError("review quota must be positive")
    selected, seen_conversations = [], set()
    ranked = sorted(candidates, key=lambda row: (-row["priority"], row["case_id"]))
    for candidate in ranked:
        if candidate["conversation_id"] in seen_conversations:
            continue
        selected.append(candidate["case_id"])
        seen_conversations.add(candidate["conversation_id"])
        if len(selected) == quota:
            break
    return selected

pool = [{"case_id": "case-47", "conversation_id": "thread-k", "priority": 0.93},
        {"case_id": "case-48", "conversation_id": "thread-k", "priority": 0.89},
        {"case_id": "case-82", "conversation_id": "thread-m", "priority": 0.81}]
assert select_review_cases(pool, 2) == ["case-47", "case-82"]
''',
        'cost': 'Sorting n candidates is O(n log n) time and O(n) output or sort space; one pass then enforces conversation diversity. Scoring all unlabeled cases may cost far more than selection itself, so batch or sample the pool with a recorded policy. The scarce resource is reviewer time. Compare improvement per reviewed hour against random selection, and retain random audit samples to detect confident blind spots.',
        'mistakes': ['Filling the queue with duplicates from one conversation.', 'Selecting only uncertain cases and missing confident model errors.', 'Training on final audit examples after reviewers label them.', 'Treating an adjudication dispute as a clean training label.'],
        'related': [N + 'annotation-disagreement-and-label-policy', N + 'text-label-acquisition-project', N + 'classification-slices-and-abstention', N + 'grouped-temporal-text-validation', N + 'corpus-identity-and-label-policy'],
    },
    {
        'path': N + 'annotation-disagreement-and-label-policy',
        'title': 'Adjudicate text labels before they become training truth',
        'module': A, 'project': False,
        'summary': 'Reviewer disagreement can expose a vague taxonomy, a missing context window or a genuinely ambiguous message. Keep those causes distinct.',
        'sections': [
            ('Preserve independent judgments', 'For a sample of messages, collect at least two independent labels with policy version and reviewer ID. Do not show one reviewer the other’s answer before the initial decision. Compare intent, span boundary and relation labels separately. A high agreement score on the dominant “other” label can hide poor agreement on a rare critical category. Store disagreement reasons and the exact original text revision.'),
            ('Fix policy before relabeling', 'If reviewers disagree about whether “refund pending” belongs to billing or returns, revise the taxonomy with explicit inclusion and exclusion cases. If they disagree about a code-switched phrase, provide context or mark it unresolved. Do not force a majority vote when the policy lacks a defensible answer. Record the adjudicator’s decision, rationale and effective policy version. [[natural-language-processing/corpus-identity-and-label-policy|Corpus contracts]] define the upstream identity of each label.'),
            ('Measure label debt', 'Track unresolved count, disagreement rate by category and source channel, turnaround time and the fraction of training rows created under retired policies. A model trained across incompatible taxonomies can appear to have noisy examples when the real problem is mixed definitions. Before retraining, migrate or exclude old labels intentionally. Keep the final evaluation labels reviewed under one frozen policy, otherwise model comparisons are not meaningful.'),
            ('Close the acquisition loop', 'Use disagreements to refine guidelines and choose targeted review, but retain a random sample to estimate true traffic. After a policy update, recheck a fixed set of hard examples and measure whether agreement improved. The [[natural-language-processing/active-learning-sampling-and-coverage|sampling lesson]] chooses cases; the [[natural-language-processing/text-label-acquisition-project|acquisition project]] keeps their provenance and adjudication state.'),
        ],
        'code': '''def adjudication_state(first_label, second_label, policy_version):
    if not policy_version:
        raise ValueError("label policy version is required")
    if first_label is None or second_label is None:
        return "awaiting-independent-review"
    if first_label == second_label:
        return "agreed"
    return "needs-adjudication"

assert adjudication_state("refund", "billing", "policy-v7") == "needs-adjudication"
assert adjudication_state("refund", "refund", "policy-v7") == "agreed"
''',
        'cost': 'This state check is O(1) time and space. Double-labeling every example roughly doubles first-pass human effort, so use a planned overlap sample and targeted high-risk categories. Adjudication cost rises when taxonomy language is vague. Measure review minutes per accepted label and downstream error reduction rather than optimizing agreement by collapsing useful classes.',
        'mistakes': ['Calling majority vote ground truth when policy is ambiguous.', 'Mixing labels from incompatible policy versions.', 'Reporting overall agreement while rare critical labels disagree.', 'Showing reviewers the model suggestion without measuring anchoring effects.'],
        'related': [N + 'active-learning-sampling-and-coverage', N + 'text-label-acquisition-project', N + 'corpus-identity-and-label-policy', N + 'span-offset-annotation', N + 'grouped-temporal-text-validation'],
    },
    {
        'path': N + 'text-label-acquisition-project',
        'title': 'Project: build a versioned text-label acquisition queue',
        'module': A, 'project': True,
        'summary': 'Create a review queue that balances uncertain, diverse and random cases, captures independent labels and admits only adjudicated records to training.',
        'sections': [
            ('Define the queue contract', 'Each candidate carries case identity, conversation group, capture time, channel, reviewed slice if known, model version and selection reason. The final audit set is excluded before scoring. Allocate a budget for uncertainty, coverage of rare slices and random traffic. Group near duplicates by conversation so one event cannot consume the whole batch. Keep raw text visible only to authorized reviewers.'),
            ('Review and adjudicate', 'Assign independent reviewers to an overlap sample and collect labels under one explicit policy version. If they disagree, route the case to an adjudicator with the original context and both rationales. Ambiguous or unresolved cases stay out of supervised training until the policy defines their treatment. [[natural-language-processing/annotation-disagreement-and-label-policy|Disagreement policy]] governs this step; [[natural-language-processing/active-learning-sampling-and-coverage|sampling design]] governs intake.'),
            ('Release a dataset revision', 'Write an immutable manifest of accepted case IDs, source revisions, label policy, reviewers and split assignment. Check that no conversation crosses train and audit and that training excludes withheld or unconsented data. Evaluate the model after each acquisition batch on the same frozen holdout; report improvement per reviewer hour and slices that remain weak. Do not call a larger dataset better if its labels are less consistent.'),
            ('Watch the workflow', 'Monitor queue age, disagreement rate, duplicate selection, accepted-label yield, random-sample error and model gains. A highly uncertain pool can be intrinsically ambiguous, so decreasing yield is a signal to revise the taxonomy. Maintain a rollback to the prior dataset and model. Retention and deletion policies must remove raw review text and derived training copies when required.'),
        ],
        'code': '''def admit_training_record(review_record):
    required = {"case_id", "source_revision", "policy_version", "split", "label"}
    if not required <= set(review_record):
        raise ValueError("review record lacks lineage")
    if review_record.get("state") != "adjudicated" or review_record["split"] != "train":
        return False
    if not review_record.get("use_permitted", False):
        return False
    return True

record = {"case_id": "case-47", "source_revision": "v3", "policy_version": "p7",
          "split": "train", "label": "refund", "state": "adjudicated", "use_permitted": True}
assert admit_training_record(record)
''',
        'cost': 'Admission is O(f) time for f record fields and O(1) extra space. Queue scoring can be costly, but reviewer time and source retention dominate the budget. Track accepted labels per reviewer hour, not just candidates displayed. A strict lineage check adds a small amount of work and prevents silent leakage of audit examples or unpermitted text into training.',
        'mistakes': ['Sending held-out audit cases into the acquisition queue.', 'Treating a submitted label as adjudicated training truth.', 'Omitting policy version or source revision from a dataset export.', 'Measuring model gain without accounting for reviewer time and duplicate selection.'],
        'related': [N + 'active-learning-sampling-and-coverage', N + 'annotation-disagreement-and-label-policy', N + 'corpus-identity-and-label-policy', N + 'grouped-temporal-text-validation', N + 'privacy-safe-ticket-pipeline-project'],
    },
]
crosslinks = [
    (N + 'document-summary-evidence-contract', N + 'nli-premise-hypothesis-and-evidence-contract'),
    (N + 'summary-claim-verification-and-review', N + 'claim-conflict-and-temporal-review'),
    (N + 'incident-handoff-summary-project', N + 'incident-claim-verification-project'),
    (N + 'classification-slices-and-abstention', N + 'active-learning-sampling-and-coverage'),
    (N + 'corpus-identity-and-label-policy', N + 'annotation-disagreement-and-label-policy'),
    (N + 'grouped-temporal-text-validation', N + 'text-label-acquisition-project'),
    (N + 'nli-premise-hypothesis-and-evidence-contract', N + 'claim-conflict-and-temporal-review'),
    (N + 'active-learning-sampling-and-coverage', N + 'annotation-disagreement-and-label-policy'),
]

if __name__ == '__main__':
    publish(lessons, (I, A), crosslinks,
            'aitrove-nlp-inference-labeling-import-20261006.json', 4760,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
