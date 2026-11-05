"""Add original aspect-sentiment and topic-monitoring lessons."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
A = 'Aspect-level sentiment decisions'
T = 'Topic discovery and drift'
lessons = [
    {
        'path': N + 'aspect-sentiment-target-and-negation-policy',
        'title': 'Aspect sentiment: bind opinions to targets and negation',
        'module': A, 'project': False,
        'summary': 'A customer can praise delivery and criticize billing in one message. A single positive label loses the action the product team needs.',
        'sections': [
            ('Define the annotation unit', 'Store a tuple of document revision, aspect target span, opinion span, polarity and reviewer status. An aspect may be explicit (“billing”) or implied by a phrase such as “charged twice”; document which kinds are allowed. A message-level label is a separate annotation. Do not let an inferred overall mood overwrite a concrete complaint. The offsets must select the captured original text, following [[natural-language-processing/span-offset-annotation|the span contract]], even when a normalized view is used for features.'),
            ('Scope negation and contrast', '“The refund was not slow” is not a negative opinion about refunds; “the refund was slow, but the agent was helpful” contains two targets and different orientations. Annotate the cue, its scope and the target it modifies. A keyword list that counts slow without its negator will invert the first judgment. Sarcasm and quotation require an uncertainty label or review path, not an invented confidence boost. Preserve punctuation and clause boundaries through [[natural-language-processing/unicode-tokenization-boundary|text intake]].'),
            ('Make the label policy operable', 'Define positive, negative, neutral, mixed and not-applicable with examples from the product domain. Neutral means an opinion is present without clear polarity; not-applicable means no opinion about that aspect was expressed. Reviewers should mark a cancellation request as an intent, not automatically negative sentiment. Separate customer-authored words from copied agent replies and templates. Group repeated conversations during evaluation so a boilerplate sentence cannot appear on both sides of a split.'),
            ('Evaluate the relation, not just the words', 'A prediction is useful only if it attaches the right polarity to the right aspect. Report target detection recall, exact target span F1 and polarity accuracy conditional on a correctly matched target, plus end-to-end tuple F1. Review failures on negation, comparative statements, code-switching and multi-aspect messages. Follow [[natural-language-processing/aspect-sentiment-calibration-and-slices|calibration and slice evaluation]] before using a score to prioritize a queue. The [[natural-language-processing/product-feedback-aspect-project|feedback project]] turns the annotation contract into a release test.'),
        ],
        'code': '''def validate_opinion(message, opinion):
    target_start, target_end = opinion["target_span"]
    cue_start, cue_end = opinion["opinion_span"]
    for start, end in ((target_start, target_end), (cue_start, cue_end)):
        if not 0 <= start < end <= len(message):
            raise ValueError("opinion offset outside original message")
    if opinion["polarity"] not in {"positive", "negative", "neutral", "mixed"}:
        raise ValueError("unknown polarity")
    return message[target_start:target_end], message[cue_start:cue_end]

review = "Billing is slow, support is helpful."
assert validate_opinion(review, {"target_span": (0, 7), "opinion_span": (11, 15),
                                 "polarity": "negative"}) == ("Billing", "slow")
''',
        'cost': 'Span validation is O(a) operations for a annotated aspect records plus the characters copied for selected spans. A pair model may score each aspect against each candidate opinion; unconstrained pairing is O(a·o) for a targets and o opinion phrases. Cap pairs with reviewed boundaries and measure candidate recall. The expensive operating cost is disagreement review, so track how often polarity or target scope needs adjudication.',
        'mistakes': ['Using one overall sentiment label when the message has conflicting aspects.', 'Counting a negated keyword as an ordinary negative cue.', 'Treating absence of an opinion as neutral sentiment.', 'Evaluating polarity without checking whether it was attached to the correct target.'],
        'related': [N + 'aspect-sentiment-calibration-and-slices', N + 'product-feedback-aspect-project', N + 'span-offset-annotation', N + 'classification-slices-and-abstention', N + 'unicode-tokenization-boundary'],
    },
    {
        'path': N + 'aspect-sentiment-calibration-and-slices',
        'title': 'Aspect sentiment calibration across product and language slices',
        'module': A, 'project': False,
        'summary': 'A high polarity score can still be wrong for rare aspects, mixed-language feedback or copied text. Measure the tuple decision in each reviewed slice.',
        'sections': [
            ('Separate model confidence from routing confidence', 'An aspect extractor may identify “delivery” with high confidence while a polarity model hesitates. A joint action should depend on both, not the larger of the two. Calibrate the probability of a correct aspect-polarity tuple on held-out reviewed cases. A score learned from popular product features may not transfer to a new feature with only a few labels. For unsupported slices, abstain and collect review rather than silently borrowing a threshold from the largest slice.'),
            ('Choose the split before thresholds', 'Keep customer conversations and copied reviews together, and reserve later messages for final audit. Fit calibration on validation data only. For each candidate threshold, count accepted tuples, correct accepted tuples, missed negative feedback and review volume. A different threshold for every tiny segment will overfit; group sparse slices under one conservative fallback. [[natural-language-processing/grouped-temporal-text-validation|Grouped temporal validation]] protects the audit from duplicate language.'),
            ('Inspect costly failures', 'Product teams usually care about a missed severe complaint more than a mild false alarm, but the cost must be written down rather than guessed. Report per-aspect recall, wrong-target assignments, false negative complaints, automatic coverage and calibration error with support counts. Split multi-aspect, negated, sarcastic, translated and Romanized messages. [[natural-language-processing/script-profile-and-code-switching-boundary|Script profiling]] can describe input mix; it cannot provide the reviewed language label.'),
            ('Turn scores into a decision contract', 'Return tuples with target offsets and a decision state: automatic, reviewed-needed or unsupported. Record the model, annotation, threshold and tokenizer versions together. If an aspect has no reviewed support, route it to a human queue. Sample some high-confidence automatic results for post-release review, or selective labels will hide confident errors. The contract extends [[natural-language-processing/classification-slices-and-abstention|classification abstention]] to multi-target text and feeds the [[natural-language-processing/product-feedback-aspect-project|applied feedback workflow]].'),
        ],
        'code': '''def aspect_decision(aspect_score, polarity_score, aspect_threshold,
                    polarity_threshold, reviewed_slice):
    if reviewed_slice is None:
        return "manual-review", "unreviewed-slice"
    if not all(0 <= score <= 1 for score in (aspect_score, polarity_score)):
        raise ValueError("scores must be probabilities")
    if aspect_score < aspect_threshold:
        return "manual-review", "uncertain-target"
    if polarity_score < polarity_threshold:
        return "manual-review", "uncertain-polarity"
    return "automatic", "both-gates-passed"

assert aspect_decision(0.93, 0.61, 0.82, 0.74, "billing-reviewed") == (
    "manual-review", "uncertain-polarity"
)
''',
        'cost': 'The decision gate is O(1) time and space per tuple. Calibration fitting, model inference and manual review dominate total cost; estimate review cases as arrival volume times abstention rate for each slice. High selective accuracy with low coverage may simply move work to humans. Report both figures and the reviewed support count before claiming a release improved operations.',
        'mistakes': ['Using the aspect score as a proxy for polarity correctness.', 'Tuning thresholds on the final audit set.', 'Assigning an unsupported aspect the English-majority threshold.', 'Reporting accepted-case accuracy while hiding review volume and missed complaints.'],
        'related': [N + 'aspect-sentiment-target-and-negation-policy', N + 'product-feedback-aspect-project', N + 'classification-slices-and-abstention', N + 'grouped-temporal-text-validation', N + 'multilingual-calibration-and-fallback'],
    },
    {
        'path': N + 'product-feedback-aspect-project',
        'title': 'Project: turn mixed product feedback into reviewed aspect signals',
        'module': A, 'project': True,
        'summary': 'Ship a feedback pipeline that separates delivery, billing and support opinions, keeps uncertain tuples for review and reports what the model misses.',
        'sections': [
            ('Write the product question', 'A weekly product review needs to know which feature caused complaints, not whether a whole ticket sounds unhappy. Define three initial aspects—delivery, billing and support—and permit “other” when none fits. An output is a set of target-polarity tuples with source offsets, model version and review state. It is not a customer-risk score. Establish who may inspect raw text and how long examples are retained.'),
            ('Build a reviewed corpus', 'Capture original customer messages, exclude agent templates from customer opinion labels and group all replies from one case. Annotate target spans, opinion cues and negation scope; adjudicate mixed statements and quotations. Freeze a later-time audit set with at least one sufficiently reviewed sample for each aspect and language mix. Where support is thin, state that the slice is unverified. [[natural-language-processing/aspect-sentiment-target-and-negation-policy|The target and negation policy]] supplies the annotation contract.'),
            ('Compare and gate systems', 'Start with a sparse text baseline for each aspect, then test a contextual candidate on the same split. Measure exact tuple F1, severe-complaint recall, incorrect target rate and manual-review volume. Calibrate scores on validation cases and freeze thresholds before final audit. Route unreviewed aspects to review. [[natural-language-processing/aspect-sentiment-calibration-and-slices|The calibration lesson]] turns scores into safe decisions; [[natural-language-processing/multilingual-ticket-routing-project|multilingual routing]] covers related fallback design.'),
            ('Operate the weekly report', 'Publish counts only for reviewed or accepted tuples and show sample size beside every percentage. A changed product taxonomy requires relabeling, not merely renaming a chart. Monitor corrections from a random sample of high-confidence results and from abstentions. Keep raw examples in a restricted review queue, not in the general dashboard. Compare week-to-week movement only after checking whether traffic mix, channel or label policy changed.'),
        ],
        'code': '''def weekly_aspect_counts(decisions):
    counts = {}
    for decision in decisions:
        if decision["state"] not in {"reviewed", "automatic"}:
            continue
        key = (decision["aspect"], decision["polarity"])
        counts[key] = counts.get(key, 0) + 1
    return counts

feedback = [
    {"aspect": "delivery", "polarity": "negative", "state": "reviewed"},
    {"aspect": "support", "polarity": "positive", "state": "automatic"},
    {"aspect": "billing", "polarity": "negative", "state": "manual-review"},
]
assert weekly_aspect_counts(feedback) == {
    ("delivery", "negative"): 1, ("support", "positive"): 1
}
''',
        'cost': 'The aggregation is O(n) time and O(a·p) space in the worst case for n decisions, a aspects and p polarities. Model inference and review are the recurring costs; report processing latency and estimated cases awaiting review. Weekly counts are not population estimates if the accepted set is selected by a threshold. Present coverage and traffic mix with the counts to avoid false trend claims.',
        'mistakes': ['Publishing a change in complaint percentage without checking traffic composition.', 'Counting unreviewed low-confidence tuples as facts.', 'Treating customer text and copied agent replies as the same speaker.', 'Assuming a product taxonomy change preserves historical comparability.'],
        'related': [N + 'aspect-sentiment-target-and-negation-policy', N + 'aspect-sentiment-calibration-and-slices', N + 'grouped-temporal-text-validation', N + 'multilingual-ticket-routing-project', N + 'support-entity-extraction-project'],
    },
    {
        'path': N + 'topic-discovery-corpus-and-model-selection',
        'title': 'Topic discovery: corpus boundaries, model choice and human labels',
        'module': T, 'project': False,
        'summary': 'A topic model can organize thousands of tickets, but a coherent cluster is not automatically a product issue or a stable taxonomy.',
        'sections': [
            ('Decide what a topic should represent', 'For support triage, the unit may be one customer problem rather than one reply. Strip quoted prior messages only when their removal is auditable; otherwise the same boilerplate dominates every topic. Keep case identity, product version, language, channel and capture time. Choose whether the purpose is exploration, routing or trend reporting. A model trained for exploration does not become a production classifier merely because its top terms look readable. [[natural-language-processing/corpus-identity-and-label-policy|Corpus identity]] defines the row boundary.'),
            ('Compare representations', 'Count-based latent topics, sparse matrix factorization and embedding clusters answer different questions. Sparse methods expose characteristic terms and often make version comparison easier; embedding clusters can group paraphrases but may also join unrelated intents with similar wording. Fit vocabulary or encoder only within the training boundary. Try a no-model baseline of existing support tags before adding complexity. Separate rare security or billing cases from a broad “other” cluster so size does not hide importance.'),
            ('Give topics human meaning', 'Top words are diagnostics, not labels. Sample representative and hard-edge tickets for each candidate topic and ask reviewers to name its shared issue, mark mixed clusters and flag sensitive terms. Store the model version, reviewed label, sample IDs and uncertainty. A topic number such as 7 is local to a fit and must not be used as a permanent business key. The [[natural-language-processing/topic-alignment-and-drift-review|drift review]] establishes how to compare later fits without pretending IDs are stable.'),
            ('Test usefulness', 'Use held-out tickets to evaluate assignment stability, reviewer agreement, coverage of actionable themes and separation of unrelated cases. Coherence can help reject unreadable term lists, but it cannot establish product usefulness alone. Slice by language and channel; boilerplate or transliteration can become a “topic” of its own. The [[natural-language-processing/support-theme-monitoring-project|monitoring project]] makes these checks part of an editorial workflow, rather than publishing automated labels as facts.'),
        ],
        'code': '''from collections import Counter

def representative_terms(documents, stop_terms, top_k=5):
    if top_k < 1:
        raise ValueError("top_k must be positive")
    term_counts = Counter()
    for document in documents:
        term_counts.update(term for term in document.lower().split()
                           if term not in stop_terms and len(term) > 2)
    return [term for term, _ in term_counts.most_common(top_k)]

tickets = ["gateway callback retry", "callback retry duplicate", "gateway timeout"]
assert representative_terms(tickets, {"the"}, 2) == ["gateway", "callback"]
''',
        'cost': 'Counting terms is O(total tokens) time and O(v) space for vocabulary size v. Matrix factorization or clustering adds repeated passes over documents and may scale with vocabulary, embedding dimension and topic count. A larger topic count can improve apparent fit while producing tiny uninterpretable clusters. Budget reviewer time for representative and boundary examples; that cost decides whether discovery yields a usable taxonomy.',
        'mistakes': ['Treating a model-local topic number as a stable category.', 'Naming a topic from its five highest-weight words without reading cases.', 'Fitting vocabulary on the final time-split audit set.', 'Equating statistical coherence with operational usefulness.'],
        'related': [N + 'topic-alignment-and-drift-review', N + 'support-theme-monitoring-project', N + 'corpus-identity-and-label-policy', N + 'sparse-text-baseline', N + 'grouped-temporal-text-validation'],
    },
    {
        'path': N + 'topic-alignment-and-drift-review',
        'title': 'Topic drift: align changing clusters before reporting trends',
        'module': T, 'project': False,
        'summary': 'A retrained topic model can swap topic numbers, split a theme or merge two themes. Compare reviewed content and assignments before announcing a trend.',
        'sections': [
            ('Do not compare raw IDs', 'Topic 4 this month has no guaranteed relationship with Topic 4 last month. Keep a frozen anchor set of tickets and score both models on it. Compare representative examples, characteristic terms and assignment overlap for candidate alignments. A high overlap is evidence for continuity, not proof: two broad topics may both cover a common template while diverging on rare incidents. Record split, merge and new-theme events explicitly.'),
            ('Separate real movement from pipeline changes', 'A rise in “refund delay” may reflect more complaints, a new classification policy, a changed support channel or a tokenizer update. Preserve model, preprocessing and corpus manifests. Estimate trend on a fixed labeled definition when possible; if not, state that the series has a break. Slice by language and product release because a newly added channel can shift the entire corpus mix. [[natural-language-processing/topic-discovery-corpus-and-model-selection|Topic discovery]] explains why exploratory clusters need reviewed names.'),
            ('Review the alignment', 'Match candidate old-new topics using overlap on the same anchor tickets and a reviewer’s judgment of the central issue. Do not force a one-to-one map: allow many-to-one merges and one-to-many splits. Keep low-confidence alignments in an “unresolved” bucket until more examples are reviewed. Reuse the same annotated anchor set across versions only while its cases remain representative. Refresh it with a logged policy and keep the older benchmark for regression comparison.'),
            ('Publish cautious metrics', 'Report volume, share of eligible tickets, reviewer agreement, topic coverage and the fraction left unresolved. Attach a series version to every plotted point. A business-facing statement should distinguish “more tickets arrived” from “the model reassigned tickets.” Give reviewers the top changed examples, not only a similarity score. The [[natural-language-processing/support-theme-monitoring-project|support-theme project]] uses these gates before a weekly dashboard changes.'),
        ],
        'code': '''def overlap_matrix(old_assignments, new_assignments):
    if set(old_assignments) != set(new_assignments):
        raise ValueError("compare models on the same anchor tickets")
    overlap = {}
    for ticket_id, old_topic in old_assignments.items():
        pair = (old_topic, new_assignments[ticket_id])
        overlap[pair] = overlap.get(pair, 0) + 1
    return overlap

previous = {"case-47": "retry", "case-82": "retry", "case-91": "refund"}
current = {"case-47": "callback", "case-82": "callback", "case-91": "refunds"}
assert overlap_matrix(previous, current)[("retry", "callback")] == 2
''',
        'cost': 'The overlap pass is O(n) time and O(p) space for n anchor tickets and p observed old-new topic pairs. A dense matching algorithm over all old and new topics can cost more, but the reviewer burden is often larger. Keep the anchor set bounded and representative; a tiny set gives fast but unstable alignment. Report its support count and unresolved rate with every trend chart.',
        'mistakes': ['Plotting topic ID 4 across retrains as one continuous issue.', 'Forcing one-to-one alignment when a theme has split.', 'Calling a changed assignment distribution a customer trend without checking traffic mix.', 'Hiding unresolved alignments from the dashboard denominator.'],
        'related': [N + 'topic-discovery-corpus-and-model-selection', N + 'support-theme-monitoring-project', N + 'grouped-temporal-text-validation', N + 'script-profile-and-code-switching-boundary', N + 'text-embedding-pair-and-version-contract'],
    },
    {
        'path': N + 'support-theme-monitoring-project',
        'title': 'Project: publish a reviewed support-theme monitor',
        'module': T, 'project': True,
        'summary': 'Build a weekly topic monitor that distinguishes a real rise in a support problem from a new model version, channel or vocabulary.',
        'sections': [
            ('Define the report', 'Support leads need the most common actionable issues by product area, with a short list of new or rising themes. Decide the eligible ticket population and what one counted case means. Exclude duplicate replies rather than counting the same problem twice. Preserve product, language, channel and capture time as analysis dimensions. Do not put raw sensitive text into an unrestricted dashboard; show only reviewed excerpts behind access control.'),
            ('Build candidate themes', 'Start with existing support tags and a sparse baseline, then compare a topic model or embedding clustering on the same frozen corpus. Review representative tickets and cluster edges. Name only themes that reviewers can define consistently; keep mixed and unresolved clusters visible. [[natural-language-processing/topic-discovery-corpus-and-model-selection|Corpus and model choice]] explains why a readable word list is not enough. Freeze an anchor set of difficult tickets for the next model update.'),
            ('Guard the trend line', 'When retraining, assign old and new models to the anchor set. Review splits, merges and unresolved mappings before joining time series. If label policy, channel mix or language coverage changes, start a new series or annotate the break. [[natural-language-processing/topic-alignment-and-drift-review|Alignment and drift review]] supplies that version contract. Compare raw volume and rate per eligible tickets so a surge in overall support traffic does not masquerade as a new issue.'),
            ('Publish with review capacity', 'The weekly package contains reviewed theme names, support counts, representative examples for authorized leads and a confidence note for each trend. A human approves the new-theme list; the model proposes candidates. Monitor reviewer disagreement, theme coverage, unresolved volume and time spent per review. If a rare high-impact topic is swallowed by a broad cluster, maintain a targeted rule or classifier alongside discovery.'),
        ],
        'code': '''def theme_share(theme_counts, eligible_cases):
    if eligible_cases <= 0:
        raise ValueError("eligible case count must be positive")
    if any(count < 0 for count in theme_counts.values()):
        raise ValueError("theme counts cannot be negative")
    return {theme: count / eligible_cases for theme, count in theme_counts.items()}

weekly = theme_share({"callback-retry": 47, "refund-delay": 23}, 940)
assert weekly["callback-retry"] == 0.05
''',
        'cost': 'Calculating shares is O(t) time and O(t) output space for t reviewed themes. Training and periodic reassignment dominate compute, while human naming and alignment dominate editorial cost. Track the fraction of cases assigned to no useful theme; a small, stable dashboard can look healthy while coverage collapses. Use the same denominator policy for every reported week.',
        'mistakes': ['Counting every reply as an independent customer problem.', 'Joining retrained topic IDs without reviewed alignment.', 'Reporting raw volume as a rising share of support demand.', 'Dropping unresolved clusters so theme coverage looks stronger.'],
        'related': [N + 'topic-discovery-corpus-and-model-selection', N + 'topic-alignment-and-drift-review', N + 'grouped-temporal-text-validation', N + 'product-feedback-aspect-project', N + 'privacy-safe-ticket-pipeline-project'],
    },
]
crosslinks = [
    (N + 'classification-slices-and-abstention', N + 'aspect-sentiment-calibration-and-slices'),
    (N + 'span-offset-annotation', N + 'aspect-sentiment-target-and-negation-policy'),
    (N + 'multilingual-calibration-and-fallback', N + 'product-feedback-aspect-project'),
    (N + 'sparse-text-baseline', N + 'topic-discovery-corpus-and-model-selection'),
    (N + 'grouped-temporal-text-validation', N + 'support-theme-monitoring-project'),
    (N + 'aspect-sentiment-target-and-negation-policy', N + 'aspect-sentiment-calibration-and-slices'),
    (N + 'topic-discovery-corpus-and-model-selection', N + 'topic-alignment-and-drift-review'),
]

if __name__ == '__main__':
    publish(lessons, (A, T), crosslinks,
            'aitrove-nlp-sentiment-topics-import-20261006.json', 4730,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
