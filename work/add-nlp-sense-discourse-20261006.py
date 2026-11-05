"""Add operational word-sense and discourse-relation lessons."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
S = 'Lexical sense and domain ambiguity'
D = 'Discourse relations and evidence flow'

lessons = [
    {
        'path': N + 'domain-word-sense-inventory-and-nil',
        'title': 'Domain word senses: inventory, abstention and new meanings',
        'module': S, 'project': False,
        'summary': 'A term can denote different operational concepts inside one company. Name the senses before training a classifier or joining search results.',
        'sections': [
            ('Define senses at the decision boundary', 'In support logs, “charge” may mean a card debit, stored battery energy or an instruction to bill. A dictionary entry is too broad for deciding whether a billing runbook should appear. Assign stable sense IDs with short definitions, inclusion rules, exclusions and two independently written examples. Include the downstream action each sense permits. The [[natural-language-processing/lemma-pos-and-domain-term-contract|lemma and part-of-speech contract]] identifies a word form; it does not decide which meaning a particular use carries.'),
            ('Keep an explicit unknown state', 'Do not force every occurrence into the current inventory. A new product can introduce a meaning that was absent when labels were collected; the phrase “reserve charge” could name a feature rather than a payment. Return NIL with the observed span, context, candidate scores and inventory version. Route repeated NIL cases to a reviewer, who can create a new sense or correct a bad candidate. The [[natural-language-processing/entity-link-candidates-and-nil-decision|entity-link NIL decision]] is related, but identifies a referent rather than a lexical meaning.'),
            ('Version the inventory like a schema', 'Splitting a broad PAYMENT sense into CARD_DEBIT and ACCOUNT_CREDIT changes old training labels and search filters. Store an immutable inventory version on annotations, indexes and predictions. Define a mapping for migration, and leave ambiguous old rows unresolved when evidence is insufficient. Evaluate the new inventory on a frozen sample before reindexing. Rewriting historical labels in place makes earlier quality reports irreproducible and may silently change what a saved search returns.'),
            ('Audit impact, not just agreement', 'Sample high-frequency terms, rare meanings, negated spans and language variants. Count NIL rate, wrong-sense retrieval joins and reviewer disagreements by business workflow. A sense model with high overall accuracy can still surface a billing article for a battery incident if the common sense dominates evaluation. [[natural-language-processing/hybrid-ranking-and-access-filters|Hybrid retrieval]] should retain sense evidence as one feature while preserving document access rules. An uncertain meaning should not bypass those rules.'),
        ],
        'code': '''SENSES = {
    "charge": {
        "payment-debit": {"card", "invoice", "refund"},
        "battery-energy": {"battery", "voltage", "charger"},
    }
}

def sense_candidates(term, context_tokens):
    context = set(context_tokens)
    scores = [(sense_id, len(context & clues))
              for sense_id, clues in SENSES.get(term, {}).items()]
    if not scores:
        return {"state": "nil", "candidates": []}
    best = max(score for _, score in scores)
    winners = [sense_id for sense_id, score in scores if score == best]
    if best == 0 or len(winners) != 1:
        return {"state": "review", "candidates": winners}
    return {"state": "proposed", "sense_id": winners[0]}

assert sense_candidates("charge", ["card", "refund"])["sense_id"] == "payment-debit"
assert sense_candidates("charge", ["card", "battery"])["state"] == "review"
''',
        'cost': 'The small illustrative scorer compares s senses against c context tokens, taking O(s × c) time in the worst case and O(c + s) temporary space. A production system may use indexed features or a learned ranker. This code is a review-oriented baseline, not a calibrated probability; measure the cost of wrong retrieval separately from the cost of abstention.',
        'mistakes': ['Treating a lemma as a complete sense label.', 'Silently mapping unseen meanings to the most frequent sense.', 'Changing sense definitions without versioning old annotations.', 'Measuring only overall accuracy when a rare meaning triggers costly actions.'],
        'related': [N + 'sense-decision-context-and-versioning', N + 'support-term-disambiguation-project', N + 'lemma-pos-and-domain-term-contract', N + 'entity-link-candidates-and-nil-decision', N + 'hybrid-ranking-and-access-filters'],
    },
    {
        'path': N + 'sense-decision-context-and-versioning',
        'title': 'Sense decisions: context windows, policy versions and review',
        'module': S, 'project': False,
        'summary': 'The useful context for a word may sit outside its sentence. Make the evidence window and decision policy reproducible.',
        'sections': [
            ('Capture the occurrence, not just the word', 'A ticket title says “hold,” while the message body says “release the authorization after capture.” The intended meaning concerns a payment hold, not a deployment pause. Record the word span, document revision, local sentence, permitted neighboring fields and workflow metadata available at decision time. Do not use a final agent tag assigned later: that would leak the answer into training. [[natural-language-processing/span-offset-annotation|Span offsets]] make each reviewed occurrence recoverable after annotation.'),
            ('Set a bounded evidence window', 'A fixed token window is cheap, but it may cut off a definition in the preceding heading or include an unrelated quotation. Compare sentence-only, section-scoped and structured-field contexts on a reviewed set. Keep the winning window policy with the model version. When a document crosses a section boundary, avoid borrowing clues from the next incident. [[natural-language-processing/document-sections-and-passage-boundaries|Passage boundaries]] determine which neighboring text can reasonably support a decision.'),
            ('Separate candidate ranking from release', 'Generate plausible senses and rank them against the recorded context. Release a sense only when its score clears the policy threshold and beats the runner-up by the required margin. Otherwise retain candidates and request review; confidence is not evidence if the score has not been calibrated on the current domain. A new inventory version can add candidates and change the margin. [[natural-language-processing/domain-word-sense-inventory-and-nil|Inventory rules]] govern the NIL state.'),
            ('Test stability after a vocabulary shift', 'Re-run a frozen audit after a product launch, renamed queue or documentation rewrite. Break down errors by source field and term, not solely by model average. Keep reviewed examples from before and after the change so a threshold adjustment does not improve one term by harming another. When sense labels drive search, compare retrieval mistakes and access-filter compliance end to end. Human corrections need an audit trail with original prediction, source revision and reviewer policy.'),
        ],
        'code': '''def decide_sense(ranked, minimum_score, minimum_margin, inventory_version):
    if not ranked:
        return {"state": "nil", "inventory": inventory_version}
    ordered = sorted(ranked, key=lambda candidate: candidate["score"], reverse=True)
    lead = ordered[0]
    runner_up = ordered[1]["score"] if len(ordered) > 1 else 0.0
    if lead["score"] < minimum_score or lead["score"] - runner_up < minimum_margin:
        return {"state": "review", "inventory": inventory_version,
                "candidates": [candidate["sense_id"] for candidate in ordered]}
    return {"state": "proposed", "inventory": inventory_version,
            "sense_id": lead["sense_id"]}

ranked = [{"sense_id": "payment-hold", "score": 0.82},
          {"sense_id": "deploy-hold", "score": 0.47}]
assert decide_sense(ranked, 0.75, 0.20, "sense-r4")["sense_id"] == "payment-hold"
''',
        'cost': 'Sorting s candidates costs O(s log s) time and O(s) space; a two-best scan would make the decision O(s). Context construction costs O(c) for c inspected tokens. The larger operating cost is maintaining reviewed, domain-specific cases whenever the vocabulary or sense policy changes. A threshold chosen on stale examples can make a cheap classifier expensive in downstream search errors.',
        'mistakes': ['Using post-resolution metadata as context for an intake decision.', 'Treating an uncalibrated model score as a probability of correctness.', 'Letting context cross into an unrelated document section.', 'Overwriting the original prediction when a reviewer changes the sense.'],
        'related': [N + 'domain-word-sense-inventory-and-nil', N + 'support-term-disambiguation-project', N + 'document-sections-and-passage-boundaries', N + 'span-offset-annotation', N + 'annotation-disagreement-and-label-policy'],
    },
    {
        'path': N + 'support-term-disambiguation-project',
        'title': 'Project: disambiguate support terms before runbook search',
        'module': S, 'project': True,
        'summary': 'Stage sense decisions for ambiguous support vocabulary, then test whether the correct runbook remains visible without false joins.',
        'sections': [
            ('Define the release boundary', 'A support search receives “charge failed after swap” and must distinguish a failed card debit from battery charging. It may rank documents, but it must not execute refunds, change a device or bypass access filters. Create a small inventory for charge, hold and retry with stable IDs, exclusions and NIL. Reviewers annotate exact spans and document revisions. The [[natural-language-processing/domain-word-sense-inventory-and-nil|sense inventory]] provides the label contract.'),
            ('Build difficult evaluation cases', 'Collect tickets and runbook excerpts from billing, hardware and deployment queues. Include short titles, copied text, quotations, negated statements and cases where the decisive clue is in a section heading. Split by incident and copied template so near-duplicates do not inflate quality. Freeze the inventory version and reviewer guidelines. Keep an independent holdout with examples of new meanings and ambiguous cases that should abstain rather than force a label.'),
            ('Stage the search decision', 'Produce candidates with the text span and allowed context. Apply a margin policy, retaining NIL and review states. Pass a proposed sense to ranking as an auditable feature, while enforcing document ACLs before results appear. Compare sense-aware ranking with the existing search baseline; never hide the only correct runbook solely because the classifier was uncertain. [[natural-language-processing/sense-decision-context-and-versioning|Context and version policy]] fixes what each model saw.'),
            ('Measure the user-visible error', 'Report top-result relevance, wrong-domain results, correct-runbook recall, NIL rate, reviewer time and errors on rare senses. Slice by term, queue and document age. Shadow the change before rollout, then sample failures after vocabulary updates. Retain source, prediction and reviewer correction so a new sense definition can be tested against old cases. Roll back the ranking feature if wrong-domain results rise, even when sense accuracy appears stable.'),
        ],
        'code': '''def rank_runbooks(query_sense, candidates, allowed_document_ids):
    visible = [candidate for candidate in candidates
               if candidate["document_id"] in allowed_document_ids]
    ranked = sorted(visible,
                    key=lambda candidate: (
                        candidate["base_score"] +
                        (0.17 if query_sense == candidate["sense_id"] else 0.0)),
                    reverse=True)
    return [candidate["document_id"] for candidate in ranked]

runbooks = [{"document_id": "billing-47", "base_score": 0.61,
             "sense_id": "payment-debit"},
            {"document_id": "device-82", "base_score": 0.69,
             "sense_id": "battery-energy"}]
assert rank_runbooks("payment-debit", runbooks, {"billing-47", "device-82"})[0] == "billing-47"
assert rank_runbooks("payment-debit", runbooks, {"device-82"}) == ["device-82"]
''',
        'cost': 'Filtering n candidates and sorting the visible set costs O(n log n) time and O(n) space. Sense detection and reviewer handling add separate costs. The fixed boost is illustrative and needs validation against the frozen holdout; it is not a substitute for access control. Track whether uncertain queries lose the right result rather than celebrating a higher average ranking score.',
        'mistakes': ['Applying a sense boost before enforcing document access.', 'Suppressing all results when a word has no confident sense.', 'Using tickets from one incident on both sides of evaluation.', 'Treating improved label accuracy as proof that search improved.'],
        'related': [N + 'domain-word-sense-inventory-and-nil', N + 'sense-decision-context-and-versioning', N + 'hybrid-ranking-and-access-filters', N + 'morphology-aware-support-search-project', N + 'incident-runbook-search-project'],
    },
    {
        'path': N + 'discourse-units-and-relation-scope',
        'title': 'Discourse units: relation labels and evidence scope',
        'module': D, 'project': False,
        'summary': 'A relation such as contrast or cause connects claims, not arbitrary adjacent sentences. Preserve the two spans and the source of the link.',
        'sections': [
            ('Segment before naming a relation', '“The queue drained, but retries remained high” contains two claims and an explicit contrast. Store each argument span, its document revision and the connective span. A sentence can contain several units; a paragraph can also support a relation across sentence boundaries. Do not assume punctuation determines the boundary. [[natural-language-processing/document-sections-and-passage-boundaries|Document section boundaries]] prevent an incident note from being connected to the next unrelated case.'),
            ('Keep relation types distinct', 'Contrast says the claims differ in an expected dimension. Cause says one event produced another. Temporal order only says one happened before another. Elaboration adds detail without changing the underlying claim. Attribution records who made a statement, including uncertainty. One pair may carry more than one plausible relation; preserve separate proposals and evidence rather than forcing a single exclusive label. [[natural-language-processing/event-order-and-timeline-conflicts|Event-order logic]] can validate temporal edges without pretending they are causal.'),
            ('Track the evidence direction', '“Rollback followed the alarm” states order, not proof that the alarm caused rollback. For an explicit causal connective, record which argument is the stated cause and which is the effect; the arrow matters. If the source merely quotes an operator’s hypothesis, attribution must remain attached to the edge. A model-generated causal relation cannot turn a quoted suspicion into an established incident fact. [[natural-language-processing/relation-extraction-provenance|Relation provenance]] stores its supporting span and revision.'),
            ('Evaluate spans and relations separately', 'Measure unit boundaries, relation class, direction, attribution and unsupported causal edges on reviewed documents. A system may select the right label while attaching it to the wrong clause. Include multi-clause status updates, corrections and documents with repeated service names. Reviewers should see source text beside every proposed edge. The [[natural-language-processing/incident-discourse-map-project|discourse-map project]] uses this distinction in an incident handoff.'),
        ],
        'code': '''def relation_edge(left_span, right_span, label, evidence_span, revision):
    if not left_span or not right_span or not evidence_span or not revision:
        raise ValueError("both arguments, evidence and revision are required")
    if label not in {"contrast", "cause", "temporal", "elaboration", "attribution"}:
        raise ValueError("unknown relation label")
    return {"left": left_span, "right": right_span, "label": label,
            "evidence": evidence_span, "source_revision": revision}

edge = relation_edge("queue drained", "retries remained high", "contrast",
                     "but", "update-r47")
assert edge["label"] == "contrast"
''',
        'cost': 'Constructing one edge is O(1); segmenting n tokens is at least O(n). Naively comparing all u units produces O(u²) candidate pairs, so restrict candidates with document and section boundaries before classifying. Human review cost rises sharply for causal edges because a wrong causal claim can distort remediation. Track unsupported-cause rate separately from ordinary relation accuracy.',
        'mistakes': ['Treating “after” as proof of causality.', 'Joining claims from different incident sections.', 'Dropping the speaker on a quoted hypothesis.', 'Reporting relation accuracy without checking argument boundaries.'],
        'related': [N + 'implicit-relations-and-attribution-review', N + 'incident-discourse-map-project', N + 'relation-extraction-provenance', N + 'event-order-and-timeline-conflicts', N + 'document-sections-and-passage-boundaries'],
    },
    {
        'path': N + 'implicit-relations-and-attribution-review',
        'title': 'Implicit discourse relations: uncertainty and attribution',
        'module': D, 'project': False,
        'summary': 'Adjacent claims often lack a connective. A plausible reading is a hypothesis until the source or reviewer supports it.',
        'sections': [
            ('Recognize the missing connective', 'An update says “The cache was flushed. Errors stopped.” A reader may infer cause, sequence or both, yet neither sentence explicitly states the flush caused recovery. Mark the relation as implicit and retain both source spans. Candidate relations can coexist; do not turn an automatic choice into a single asserted fact. [[natural-language-processing/discourse-units-and-relation-scope|Discourse units]] define the arguments that a relation proposal connects.'),
            ('Require stronger evidence for cause', 'A temporal sequence is cheaper to assert than a causal explanation. For incident summaries, require an explicit source claim, a corroborating investigation or reviewer approval before promoting an implicit causal edge. If the evidence supports only order, write the order. Preserve a status such as proposed, reviewed or rejected and the reason for promotion. This avoids converting fluent language into false certainty. [[natural-language-processing/summary-claim-verification-and-review|Summary claim checks]] should reject a causal sentence lacking an accepted edge.'),
            ('Carry speaker and negation', '“Mira suspected the retry change caused the spike; the trace did not confirm it” contains a hypothesis and a later denial of confirmation. The speaker and negation scope matter more than surface proximity. Link each relation proposal to who asserted it and when. A later correction may supersede a statement but should not erase it from the audit trail. [[natural-language-processing/predicate-argument-roles-and-negation-scope|Predicate roles and negation]] help identify what exactly was denied.'),
            ('Test abstention as a feature', 'Review cases with missing connectives, contradictory status updates, copied quotations and multiple possible relations. Score unsupported causal assertions, accepted relation recall, attribution errors and reviewer workload. An abstention is useful when a downstream handoff would otherwise present conjecture as fact. Calibrate thresholds on incident-scoped splits rather than random sentences, which often repeat the same template and overstate accuracy.'),
        ],
        'code': '''def stage_implicit_relation(left, right, relation, evidence_kind, speaker):
    if relation == "cause" and evidence_kind not in {"explicit-source", "reviewed-investigation"}:
        return {"state": "review", "relation": relation,
                "reason": "causal-evidence-missing", "speaker": speaker}
    return {"state": "proposed", "relation": relation,
            "arguments": (left, right), "speaker": speaker}

claim = stage_implicit_relation("cache flushed", "errors stopped",
                                "cause", "adjacency-only", "Mira")
assert claim["state"] == "review"
order = stage_implicit_relation("cache flushed", "errors stopped",
                                "temporal", "adjacency-only", "Mira")
assert order["state"] == "proposed"
''',
        'cost': 'This release gate is O(1) per proposal, while producing candidate pairs can reach O(u²) for u discourse units without section pruning. Reviewing every plausible causal edge is costly; prioritize edges that would enter published summaries. The illustrative gate checks evidence type rather than evidence truth, so independent human review remains part of the release path.',
        'mistakes': ['Promoting adjacency to causality without evidence.', 'Removing attribution from an operator hypothesis.', 'Ignoring a later denial of the proposed explanation.', 'Evaluating on random sentences from the same incident template.'],
        'related': [N + 'discourse-units-and-relation-scope', N + 'incident-discourse-map-project', N + 'summary-claim-verification-and-review', N + 'predicate-argument-roles-and-negation-scope', N + 'generated-claim-evidence-and-unanswered-state'],
    },
    {
        'path': N + 'incident-discourse-map-project',
        'title': 'Project: build a reviewable incident discourse map',
        'module': D, 'project': True,
        'summary': 'Connect incident claims with contrast, order and cautiously reviewed cause, then generate a handoff that preserves uncertainty.',
        'sections': [
            ('Define the handoff contract', 'An incident handoff must tell the next responder what happened, what was claimed and what remains uncertain. Ingest versioned updates with authors and timestamps. Segment them into claim units, then attach relation proposals with evidence spans. Keep quoted hypotheses attributed. The map can inform a draft summary, but only reviewed causal edges may become causal prose. [[natural-language-processing/discourse-units-and-relation-scope|Unit and relation scope]] fixes the graph shape.'),
            ('Construct a difficult case set', 'Include a deployment followed by an alarm, a cache flush followed by recovery, a correction that retracts an earlier explanation and two parallel incidents with similar terms. Mark explicit connectives, implicit relation candidates, speaker attribution and negation. Group all updates from one incident in the same evaluation split. Reviewers should label when the evidence supports only order, even if the causal story sounds convincing. [[natural-language-processing/implicit-relations-and-attribution-review|Implicit relation policy]] prevents automatic promotion.'),
            ('Build the staged map', 'Each node stores source revision, span and speaker; each edge stores relation label, direction, evidence and review state. Reject cross-incident edges unless a human explicitly links the incidents. When a note is revised, mark derived edges stale and ask for revalidation. Surface conflicting edges side by side instead of selecting the higher model score. A handoff generator should receive only active, access-permitted nodes and the accepted relations relevant to its audience.'),
            ('Verify the released handoff', 'Compare the draft with the source map line by line for omitted critical events, unsupported cause, missing attribution and stale revisions. Report these errors and reviewer minutes, alongside relation-label precision. Shadow the workflow on resolved incidents before using it during a live response. If evidence is insufficient, the handoff should state the observed order and unresolved cause. Preserve the original updates for audit and incident-scoped rollback.'),
        ],
        'code': '''def handoff_edges(edges, allowed_incident, active_revision):
    accepted = []
    for edge in edges:
        if edge["incident_id"] != allowed_incident:
            continue
        if edge["source_revision"] != active_revision:
            continue
        if edge["relation"] == "cause" and edge["review_state"] != "accepted":
            continue
        accepted.append(edge)
    return accepted

edges = [{"incident_id": "inc-47", "source_revision": "r3",
          "relation": "temporal", "review_state": "proposed"},
         {"incident_id": "inc-47", "source_revision": "r3",
          "relation": "cause", "review_state": "review"}]
assert [edge["relation"] for edge in handoff_edges(edges, "inc-47", "r3")] == ["temporal"]
''',
        'cost': 'Filtering e edges is O(e) time and O(e) output space. Candidate extraction and human review dominate the full workflow; a dense all-pairs candidate stage grows quadratically in claim units. Keep section and incident boundaries early. Measure unsupported causal statements in the final handoff, since a correct graph that is rendered as stronger prose still fails the user.',
        'mistakes': ['Publishing a causal edge that has only adjacency evidence.', 'Combining claims from different incidents because service names match.', 'Keeping an edge active after its source note is revised.', 'Evaluating graph labels while ignoring the generated handoff wording.'],
        'related': [N + 'discourse-units-and-relation-scope', N + 'implicit-relations-and-attribution-review', N + 'incident-handoff-summary-project', N + 'incident-timeline-review-project', N + 'summary-claim-verification-and-review'],
    },
]

crosslinks = [
    (N + 'lemma-pos-and-domain-term-contract', N + 'domain-word-sense-inventory-and-nil'),
    (N + 'entity-link-candidates-and-nil-decision', N + 'domain-word-sense-inventory-and-nil'),
    (N + 'document-sections-and-passage-boundaries', N + 'sense-decision-context-and-versioning'),
    (N + 'morphology-aware-support-search-project', N + 'support-term-disambiguation-project'),
    (N + 'relation-extraction-provenance', N + 'discourse-units-and-relation-scope'),
    (N + 'event-order-and-timeline-conflicts', N + 'discourse-units-and-relation-scope'),
    (N + 'summary-claim-verification-and-review', N + 'implicit-relations-and-attribution-review'),
    (N + 'incident-handoff-summary-project', N + 'incident-discourse-map-project'),
]

if __name__ == '__main__':
    publish(lessons, (S, D), crosslinks,
            'aitrove-nlp-sense-discourse-import-20261006.json', 4818,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
