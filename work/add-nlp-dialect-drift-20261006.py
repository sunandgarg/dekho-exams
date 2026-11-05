"""Add dialect-aware evaluation and text-drift operations."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
F = 'Dialect-aware evaluation and annotation'
D = 'Text drift and feedback-loop controls'

lessons = [
    {
        'path': N + 'dialect-slices-and-label-disagreement',
        'title': 'Dialect-aware NLP audits: slices and label disagreement',
        'module': F, 'project': False,
        'summary': 'A model can confuse a writing variety with a label. Audit the task decision by language variety without guessing a person’s identity.',
        'sections': [
            ('Define the task before the slice', 'For support routing, the target is the customer’s request, not whether wording resembles a preferred register. Specify the intended label policy with examples in the writing varieties the product actually receives. Do not infer a customer’s race or identity from dialect markers. If a slice is needed for quality review, use consented or appropriately governed labels, and report sample sizes and uncertainty. [[natural-language-processing/annotation-disagreement-and-label-policy|Reviewer disagreement]] is part of the evidence.'),
            ('Separate distribution from error', 'A different mix of intents can change aggregate accuracy even when the model makes the same conditional errors. Measure false positive and false negative rates for comparable labels within each sufficiently supported slice. Review minimal pairs where the operational intent stays fixed while wording varies, but do not claim a synthetic rewrite fully represents a community’s speech. Preserve original messages and source context for native-language review.'),
            ('Examine the annotation process', 'Reviewers may interpret slang, reclaimed terms or terse code-switched messages differently. Record rationale, policy version and unresolved cases instead of collapsing every disagreement to a majority vote. A model trained on a disputed label inherits that policy decision. Ask qualified reviewers to examine borderline cases, and separate model errors from annotation ambiguity. [[natural-language-processing/low-resource-label-budget-and-transfer-boundary|Low-resource label budgets]] affect which slices can be assessed.'),
            ('Choose a release response', 'Report per-slice precision, recall, reject rate, review burden and the largest error gaps with intervals. If one slice lacks evidence, route uncertain cases to review rather than declare parity. A threshold change can reduce false positives while increasing missed requests; make that tradeoff explicit. [[natural-language-processing/dialect-audit-release-and-privacy|The release gate]] controls the data boundary, and the [[natural-language-processing/multilingual-support-quality-project|project]] tests it.'),
        ],
        'code': '''def slice_error_counts(records, slice_name):
    selected = [row for row in records if row["audit_slice"] == slice_name]
    if not selected:
        return {"supported": False, "count": 0}
    false_positive = sum(row["predicted"] and not row["reviewed"]
                         for row in selected)
    false_negative = sum(not row["predicted"] and row["reviewed"]
                         for row in selected)
    return {"supported": True, "count": len(selected),
            "false_positive": false_positive, "false_negative": false_negative}

audit = [{"audit_slice": "variety-k", "predicted": True, "reviewed": False},
         {"audit_slice": "variety-k", "predicted": False, "reviewed": True}]
assert slice_error_counts(audit, "variety-k")["false_positive"] == 1
''',
        'cost': 'Scanning n reviewed rows is O(n) time and O(n) temporary space for a selected slice in this direct implementation. Streaming counters would use O(1) extra space. The expensive part is obtaining trustworthy reviewed examples and resolving policy disagreements, not computing rates. Never publish a tiny slice as a stable performance estimate.',
        'mistakes': ['Using dialect markers as a proxy for personal identity.', 'Comparing pooled accuracy when intent mix differs across slices.', 'Treating a synthetic spelling rewrite as complete dialect evidence.', 'Hiding reviewer disagreement behind a single label.'],
        'related': [N + 'dialect-audit-release-and-privacy', N + 'multilingual-support-quality-project', N + 'annotation-disagreement-and-label-policy', N + 'multilingual-calibration-and-fallback', N + 'classification-slices-and-abstention'],
    },
    {
        'path': N + 'dialect-audit-release-and-privacy',
        'title': 'Dialect audit release gates and privacy boundaries',
        'module': F, 'project': False,
        'summary': 'Quality slices can expose a model’s blind spots without turning sensitive linguistic information into a serving-time identity guess.',
        'sections': [
            ('Separate audit metadata from serving', 'A quality team may hold governed slice annotations for evaluation, while the production router only receives the message features needed for its task. Avoid attaching a permanent dialect label to a customer profile. Restrict raw text and reviewer notes, apply retention limits and report aggregate outcomes only when sample sizes are meaningful. A missing slice label should remain missing, not be inferred as a default category.'),
            ('Specify the release criterion', 'Set minimum reviewed support and acceptable error ceilings for important intent slices. Report intervals rather than false precision from a few cases. Check both false positive and false negative changes when thresholds move. A global improvement does not compensate for a severe regression on a supported variety. If a slice lacks support, require a manual path and a plan to collect consented examples rather than inventing a pass result.'),
            ('Review interventions', 'Possible fixes include clearer label policy, more representative reviewed examples, targeted calibration or better abstention. Validate each on the same held-out set and watch for regressions elsewhere. Removing words associated with one variety can also erase real task information; evaluate the downstream request, not just a proxy metric. [[natural-language-processing/dialect-slices-and-label-disagreement|Slice construction]] supplies the baseline.'),
            ('Maintain the audit', 'Retest after tokenizer, model, label policy or channel changes. Version slice definitions and reviewer instructions so results are comparable. Keep corrections and disagreements, then examine their effect on the model only after policy review. The [[natural-language-processing/multilingual-support-quality-project|applied project]] checks quality without exposing customer-level linguistic labels in normal operations.'),
        ],
        'code': '''def release_slice_gate(slice_metrics, minimum_count, max_false_rate):
    if slice_metrics["reviewed_count"] < minimum_count:
        return "needs-review-data"
    if not 0 <= max_false_rate <= 1:
        raise ValueError("false-rate ceiling must be within [0, 1]")
    if slice_metrics["false_positive_rate"] > max_false_rate:
        return "hold-release"
    return "eligible-for-review"

metrics = {"reviewed_count": 47, "false_positive_rate": 0.09}
assert release_slice_gate(metrics, 30, 0.12) == "eligible-for-review"
''',
        'cost': 'The gate is O(1), but each added slice needs reviewed examples and statistical care. Too many tiny intersections can produce noisy apparent gaps and privacy risk. Preselect meaningful slices, report counts and use a human release review; the code cannot certify fairness from one threshold.',
        'mistakes': ['Serving inferred dialect labels as customer attributes.', 'Calling a slice safe from a handful of reviewed messages.', 'Improving one error rate while hiding the opposite error.', 'Changing slice definitions between model comparisons.'],
        'related': [N + 'dialect-slices-and-label-disagreement', N + 'multilingual-support-quality-project', N + 'low-resource-label-budget-and-transfer-boundary', N + 'classification-slices-and-abstention', N + 'redaction-audit-and-retention'],
    },
    {
        'path': N + 'multilingual-support-quality-project',
        'title': 'Project: audit support routing across language varieties',
        'module': F, 'project': True,
        'summary': 'Create a governed quality review for support-intent routing, with explicit disagreement and a safe fallback for unsupported slices.',
        'sections': [
            ('Set the scope', 'The support router predicts operational intent, not a writer’s identity or education. A separate restricted audit samples messages across language varieties that the service actually receives. Reviewers label request intent and note disputed interpretations under one policy. Serving does not persist a dialect profile. Uncertain cases go to an authorized agent rather than a forced queue.'),
            ('Build the reviewed set', 'Select consented or appropriately governed examples, group conversation families and preserve original wording. Include local abbreviations, code-switching, negation and messages with identical intent expressed differently. Record reviewer disagreements before adjudication. [[natural-language-processing/dialect-slices-and-label-disagreement|Slice design]] avoids proxy-identity claims; [[natural-language-processing/dialect-audit-release-and-privacy|the gate]] controls sample support and privacy.'),
            ('Compare policy changes', 'Measure per-intent precision and recall, false routing, abstention and agent time by supported slice. Compare a baseline and revised model on the same frozen audit. Inspect whether a threshold change simply shifts errors into manual review. The team should see severe mistakes with their source context, not only averages, while broad reports suppress tiny groups.'),
            ('Operate and retire data', 'Version model, taxonomy and slice definition. Review drift after channel or tokenizer changes. Keep raw audit messages under limited access and retention; delete derived examples when required. If an audit slice fails the release criterion, hold the affected locale or channel rollout until a revised model or policy passes review. Do not silently fall back to a high-resource language prediction.'),
        ],
        'code': '''def quality_route(prediction, supported_locales, thresholds):
    locale = prediction.get("declared_locale")
    if locale not in supported_locales:
        return {"state": "agent-review", "reason": "insufficient-audit"}
    if prediction["score"] < thresholds[locale]:
        return {"state": "agent-review", "reason": "uncertain-intent"}
    return {"state": "proposed", "intent": prediction["intent"]}

case = {"declared_locale": "locale-k", "score": 0.84,
        "intent": "delivery"}
assert quality_route(case, {"locale-k"}, {"locale-k": 0.81})["state"] == "proposed"
''',
        'cost': 'The routing gate is O(1) per case and uses a declared locale; detailed linguistic slices remain in the restricted audit. Annotation, adjudication and agent review dominate cost. Track wrong routes and manual load together before enabling more automation.',
        'mistakes': ['Turning a quality-audit slice into a permanent customer trait.', 'Using translated messages as the only evidence for local writing.', 'Suppressing small-slice uncertainty to claim a release pass.', 'Removing the agent fallback because aggregate accuracy rose.'],
        'related': [N + 'dialect-slices-and-label-disagreement', N + 'dialect-audit-release-and-privacy', N + 'multilingual-ticket-routing-project', N + 'low-resource-label-budget-and-transfer-boundary', N + 'annotation-disagreement-and-label-policy'],
    },
    {
        'path': N + 'text-drift-signals-and-label-delay',
        'title': 'Text drift: input shifts, delayed labels and real errors',
        'module': D, 'project': False,
        'summary': 'New words and changed message length are warning signals. They do not prove the router’s decisions have become wrong.',
        'sections': [
            ('Separate input from outcome', 'Monitor observable changes at intake: language mix, token lengths, unknown terms, channel distribution and abstention. Actual routing errors require reviewed labels, which may arrive days later. A keyword spike can reflect a product launch while model precision stays steady; a stable vocabulary can hide a changed meaning of “hold.” Keep distinct dashboards for input shift, delayed quality and user impact. [[natural-language-processing/grouped-temporal-text-validation|Temporal validation]] gives a baseline for comparison.'),
            ('Avoid logging raw private text', 'Count approved aggregate features and sample restricted messages for human review only under policy. Do not put customer names, order IDs or full transcripts into ordinary metrics. Keep windows, model version, tokenizer version and source channel explicit. If a classifier begins rejecting more messages, investigate whether the mix changed or the threshold bundle changed. [[natural-language-processing/text-serving-contract|Serving contracts]] should carry those versions.'),
            ('Account for label delay', 'An agent’s final queue may be an imperfect proxy for the correct intent, and it is not available at prediction time. Define when a reviewed outcome is mature enough for comparison. Use event time for intake cohorts and avoid mixing recent unlabeled cases with older fully reviewed ones. Report sample counts and pending outcomes. A model must not train on its own unverified routes as if they were independent truth.'),
            ('Trigger investigation, not blind retraining', 'Set alerts on sustained shifts and quality ceilings, then inspect representative errors by slice. Retrain only after the label policy, data provenance and audit show a real need. A rollback may be safer when a new model or tokenizer caused the change. [[natural-language-processing/text-feedback-loop-and-shadow-audit|Feedback controls]] cover learning from outcomes; the [[natural-language-processing/support-text-drift-project|project]] runs the monitoring workflow.'),
        ],
        'code': '''def drift_window(window, minimum_count, unknown_rate_ceiling):
    if window["count"] < minimum_count:
        return "insufficient-volume"
    if window["unknown_term_rate"] > unknown_rate_ceiling:
        return "investigate-input-shift"
    if window["reviewed_count"] < minimum_count:
        return "await-reviewed-outcomes"
    return "inspect-quality-metrics"

recent = {"count": 240, "unknown_term_rate": 0.19,
          "reviewed_count": 42}
assert drift_window(recent, 100, 0.15) == "investigate-input-shift"
''',
        'cost': 'The per-window gate is O(1); aggregating n requests is O(n) time and bounded metric storage when labels and windows are fixed. Reviewed labels and root-cause analysis dominate cost. Do not retrain merely because an inexpensive signal moved; compare against mature outcomes and the cost of a wrong route.',
        'mistakes': ['Calling a vocabulary change proof of prediction failure.', 'Comparing recent unlabeled traffic with older reviewed traffic as equals.', 'Logging raw customer messages into monitoring metrics.', 'Training on the model’s own routes as ground truth.'],
        'related': [N + 'text-feedback-loop-and-shadow-audit', N + 'support-text-drift-project', N + 'grouped-temporal-text-validation', N + 'text-serving-contract', N + 'classification-slices-and-abstention'],
    },
    {
        'path': N + 'text-feedback-loop-and-shadow-audit',
        'title': 'Text feedback loops: correction provenance and shadow audits',
        'module': D, 'project': False,
        'summary': 'Agent corrections can improve a model, but a production workflow also changes what gets reviewed and therefore what enters training.',
        'sections': [
            ('Record the decision path', 'For each ticket, keep model proposal, confidence, policy version, agent action, correction reason and review time as separate events. An agent might leave an incorrect route untouched because the next queue handles it; “not corrected” is not the same as “correct.” If the model auto-routes easy cases, the reviewed pool becomes harder and no longer represents incoming traffic. [[natural-language-processing/active-learning-sampling-and-coverage|Acquisition coverage]] helps design a review sample.'),
            ('Reserve independent review', 'Randomly sample a small governed share of confident and abstained cases for independent labeling, in addition to normal agent corrections. Keep the fixed final audit out of training and threshold tuning. Group repeated customer events before splits. A shadow model should score the same intake records as production without changing their routes; compare it only after mature independent labels arrive.'),
            ('Admit corrections carefully', 'A correction must carry source text revision and current label policy. Exclude labels created solely by a model’s previous decision or by a downstream queue that encodes the answer. Review taxonomy migrations and disputed cases before training. [[natural-language-processing/weak-label-conflict-and-audit-splits|Weak-label audits]] provide a parallel provenance check. Delete training derivatives if the underlying ticket is removed under retention rules.'),
            ('Compare operating outcomes', 'Track independently reviewed precision and recall, disagreement, abstention, queue age and rework. Evaluate old and shadow models on the same cohort. If a new model lowers manual reviews by routing risky cases incorrectly, the apparent efficiency gain is false. [[natural-language-processing/support-text-drift-project|The drift project]] ties this audit to release and rollback decisions.'),
        ],
        'code': '''def admit_agent_correction(record, current_policy):
    if record["policy_version"] != current_policy:
        return False
    if record["source_revision"] != record["reviewed_revision"]:
        return False
    if record["review_origin"] not in {"independent", "agent-correction"}:
        return False
    return record["reviewed_label"] is not None

correction = {"policy_version": "labels-r8", "source_revision": "note-r47",
              "reviewed_revision": "note-r47", "review_origin": "independent",
              "reviewed_label": "refund"}
assert admit_agent_correction(correction, "labels-r8")
''',
        'cost': 'Admission is O(1) per reviewed record; maintaining an independent sample costs reviewer time. Shadow inference can temporarily double model calls, but it separates measured improvement from intervention effects. A small representative review stream is often worth more than a large pile of unverified production outcomes.',
        'mistakes': ['Treating “agent did not correct it” as a positive label.', 'Evaluating only cases the model chose to abstain from.', 'Training on model-generated labels without independent review.', 'Mixing policy versions after a taxonomy update.'],
        'related': [N + 'text-drift-signals-and-label-delay', N + 'support-text-drift-project', N + 'active-learning-sampling-and-coverage', N + 'weak-label-conflict-and-audit-splits', N + 'annotation-disagreement-and-label-policy'],
    },
    {
        'path': N + 'support-text-drift-project',
        'title': 'Project: monitor support-text drift without a feedback trap',
        'module': D, 'project': True,
        'summary': 'Detect input shifts, wait for mature reviewed outcomes and compare a shadow router before changing production.',
        'sections': [
            ('Set the monitoring boundary', 'The production router emits a proposal, reject reason and model bundle version. Aggregate intake language, channel, length and unknown-term signals without logging unrestricted text. A restricted audit store receives a governed sample for independent review. The alerting service may request investigation, but it cannot automatically retrain and deploy from one shifted metric.'),
            ('Build a credible baseline', 'Choose stable historical windows with mature reviewed labels and record traffic mix. Include launch periods, channel changes, copied templates and rare high-cost intents. Group related tickets during evaluation. [[natural-language-processing/text-drift-signals-and-label-delay|Input and delayed-label separation]] prevents a recent unlabeled week from looking falsely healthy; [[natural-language-processing/text-feedback-loop-and-shadow-audit|feedback controls]] preserve independent evidence.'),
            ('Investigate and shadow', 'When unknown terms or abstention rise, inspect restricted sampled cases and determine whether a product term, tokenizer or user intent changed. Compare a candidate model in shadow mode on the same intake cohort. Wait for independent reviewed outcomes before deciding. Report false routes, reject rate, reviewer time and queue age by relevant slice. A new model must pass the fixed audit and current traffic audit.'),
            ('Release or roll back', 'Version text preprocessing, model, taxonomy and thresholds together. Promote only after review of high-cost failures; keep a prior bundle for rollback. If traffic changes again, recheck the same metrics rather than assuming a one-time fix. Retention deletion must propagate to raw audit samples and derived training rows, while aggregate counts remain policy-compliant.'),
        ],
        'code': '''def candidate_release_decision(baseline, shadow, minimum_reviews):
    if shadow["reviewed_count"] < minimum_reviews:
        return "wait-for-labels"
    if shadow["wrong_route_rate"] > baseline["wrong_route_rate"]:
        return "hold-release"
    if shadow["review_minutes"] > baseline["review_minutes"]:
        return "investigate-workload"
    return "eligible-for-review"

baseline = {"wrong_route_rate": 0.08, "review_minutes": 470}
shadow = {"reviewed_count": 180, "wrong_route_rate": 0.06,
          "review_minutes": 430}
assert candidate_release_decision(baseline, shadow, 120) == "eligible-for-review"
''',
        'cost': 'The decision gate is O(1); shadow inference and independent labels create temporary extra cost. The calculation does not replace statistical analysis or risk review. Compare mature cohorts and high-cost mistakes before promoting a model, because a cheaper queue can hide more rework elsewhere.',
        'mistakes': ['Automatically retraining after a keyword spike.', 'Comparing shadow and production on different traffic cohorts.', 'Using agent silence as proof that a route was correct.', 'Keeping deleted tickets in a shadow training copy.'],
        'related': [N + 'text-drift-signals-and-label-delay', N + 'text-feedback-loop-and-shadow-audit', N + 'ticket-routing-project', N + 'active-learning-sampling-and-coverage', N + 'privacy-safe-ticket-pipeline-project'],
    },
]

crosslinks = [
    (N + 'annotation-disagreement-and-label-policy', N + 'dialect-slices-and-label-disagreement'),
    (N + 'low-resource-label-budget-and-transfer-boundary', N + 'dialect-audit-release-and-privacy'),
    (N + 'multilingual-ticket-routing-project', N + 'multilingual-support-quality-project'),
    (N + 'grouped-temporal-text-validation', N + 'text-drift-signals-and-label-delay'),
    (N + 'active-learning-sampling-and-coverage', N + 'text-feedback-loop-and-shadow-audit'),
    (N + 'ticket-routing-project', N + 'support-text-drift-project'),
]

if __name__ == '__main__':
    publish(lessons, (F, D), crosslinks,
            'aitrove-nlp-dialect-drift-import-20261006.json', 4812,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
