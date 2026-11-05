"""Add semantic-role and hierarchical routing learning paths."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
R = 'Semantic roles and event arguments'
H = 'Hierarchical multi-label text routing'

lessons = [
    {
        'path': N + 'predicate-argument-roles-and-negation-scope',
        'title': 'Predicate arguments: actors, targets and negation scope',
        'module': R, 'project': False,
        'summary': 'A sentence can name an action without asserting that it happened. Extract the predicate, participants and scope before recording an event.',
        'sections': [
            ('Define the event frame', '“The gateway did not retry the charge” contains an actor, action and target, but it denies the action. Store the predicate span, actor span, target span, polarity, modality and source revision. An event frame is a statement made in text, not proof the system performed it. In “the charge was retried by the gateway,” grammatical subject and actor differ. [[natural-language-processing/dependency-tree-contract-and-token-alignment|Dependency structure]] can propose arguments, while [[natural-language-processing/span-offset-annotation|offsets]] preserve what was said.'),
            ('Mark scope, not just trigger words', 'Negation may cover one predicate while leaving another affirmative: “The worker did not send a receipt but logged the payment.” A sentence-level negative flag would erase the logging event. “May retry” describes possibility, not a completed action. Annotators need a policy for conditional clauses, quotations, reported claims and uncertain pronouns. Keep a distinct reported-by field where the speaker is not the actor.'),
            ('Validate participants and identity', 'Link candidate actors and targets only after their spans and roles are stable. “Atlas” may be a service or dashboard, so a guessed catalog ID should not silently overwrite a mention. [[natural-language-processing/entity-link-candidates-and-nil-decision|Entity linking]] can return NIL. When a document is edited, invalidate affected frames and downstream relations. A role label tied to an outdated tokenization must be regenerated rather than shifted by hand.'),
            ('Evaluate as a frame', 'Measure predicate detection, argument span boundaries, role assignment and polarity separately. Then score whether the full frame supports the intended incident decision. A model can get actor and target right but miss “not,” reversing the outcome. Hold entire incidents out during audit. The [[natural-language-processing/role-frame-decoding-and-provenance|frame decoder]] checks structure; the [[natural-language-processing/incident-action-frame-project|project]] stages these records for review.'),
        ],
        'code': '''def event_frame(predicate, actor, target, polarity, source_revision):
    if not source_revision or polarity not in {"affirmed", "negated", "uncertain"}:
        raise ValueError("invalid frame evidence")
    if not predicate or not actor or not target:
        raise ValueError("missing argument")
    return {"predicate": predicate, "actor": actor, "target": target,
            "polarity": polarity, "source_revision": source_revision}

frame = event_frame("retry", "gateway", "charge ZX-47",
                    "negated", "note-r47")
assert frame["polarity"] == "negated"
''',
        'cost': 'The frame check is O(1) for fixed fields; copying text spans costs their combined length. Sequence labeling or parsing cost grows with sentence length, and cross-sentence coreference adds another pass. Human review should focus on polarity and action-target errors because they can reverse an incident decision even when most spans are correct.',
        'mistakes': ['Treating every mentioned action as completed.', 'Attaching sentence-level negation to the wrong predicate.', 'Using grammatical subject as actor in passive clauses.', 'Replacing mention text with an uncertain catalog ID.'],
        'related': [N + 'role-frame-decoding-and-provenance', N + 'incident-action-frame-project', N + 'dependency-tree-contract-and-token-alignment', N + 'entity-link-candidates-and-nil-decision', N + 'claim-conflict-and-temporal-review'],
    },
    {
        'path': N + 'role-frame-decoding-and-provenance',
        'title': 'Role frames: decoding constraints and evidence revisions',
        'module': R, 'project': False,
        'summary': 'Independent span scores can form an impossible event. Decode a consistent frame and keep its supporting text revision.',
        'sections': [
            ('Decode under simple constraints', 'A candidate frame needs one predicate span, role spans inside the source sentence and a polarity value. Reject spans outside the sentence and roles assigned to the same characters when policy forbids overlap. One sentence can contain multiple predicates; do not force all arguments onto the first verb. Link a pronoun to a prior mention only when the coreference decision is reviewed or sufficiently supported. [[natural-language-processing/coreference-chains-and-mention-identity|Coreference chains]] are a separate hypothesis.'),
            ('Keep provenance granular', 'Store source document, revision, sentence offsets, predicate span and argument spans. If a model emits an inferred actor absent from the sentence, mark it as inferred rather than extractive. A downstream relation should reference the exact frame version, not just its text. [[natural-language-processing/relation-extraction-provenance|Relation provenance]] prevents an edge from surviving after its support disappears.'),
            ('Resolve competing frames', 'Two decoders may disagree about whether “before rollback” modifies deployment or alarm. Keep alternative proposals and a reason for review; a high average score does not make the ambiguity vanish. Review contradictions with the event timeline, including negated actions and speculative plans. Do not automatically merge two frames merely because they share an actor and verb; targets and time can differ.'),
            ('Measure useful correctness', 'Report exact full-frame accuracy, polarity errors, omitted predicates and wrong arguments by source channel. Compare a parser baseline with a trained decoder on the same incident-grouped audit. Include passive voice, conjunction, quotation and multi-event sentences. The [[natural-language-processing/incident-action-frame-project|applied project]] uses a conservative release gate for operational action frames.'),
        ],
        'code': '''def validate_role_spans(sentence, predicate_span, role_spans):
    length = len(sentence)
    spans = {"predicate": predicate_span, **role_spans}
    for role, (start, end) in spans.items():
        if not 0 <= start < end <= length:
            raise ValueError(f"{role} span outside sentence")
    return {role: sentence[start:end]
            for role, (start, end) in spans.items()}

line = "Gateway retried charge ZX-47."
roles = validate_role_spans(line, (8, 15),
                            {"actor": (0, 7), "target": (16, 28)})
assert roles["predicate"] == "retried" and roles["actor"] == "Gateway"
''',
        'cost': 'Checking r span coordinates takes O(r) time, while extracting text copies O(total span length) characters. Decoding all candidate combinations can grow quickly when each role has many spans, so prune by sentence and predicate before scoring. Track full-frame error and reviewer time, rather than optimizing token-level accuracy alone.',
        'mistakes': ['Assembling the highest-scoring role spans without validating their relation.', 'Losing the source revision after a frame is stored.', 'Treating an inferred actor as verbatim text.', 'Evaluating only role tokens and missing a wrong complete event.'],
        'related': [N + 'predicate-argument-roles-and-negation-scope', N + 'incident-action-frame-project', N + 'coreference-chains-and-mention-identity', N + 'relation-extraction-provenance', N + 'event-order-and-timeline-conflicts'],
    },
    {
        'path': N + 'incident-action-frame-project',
        'title': 'Project: extract reviewable action frames from incidents',
        'module': R, 'project': True,
        'summary': 'Stage who did what to which system, with negation and evidence, before an action appears in an incident timeline.',
        'sections': [
            ('Choose the operational question', 'Responders need to distinguish an attempted rollback from a completed rollback. The extractor proposes action frames from notes; a reviewer confirms critical ones before they enter the timeline. Each frame includes actor, predicate, target, polarity, modality and source offsets. It does not authorize a production action. Preserve the note revision so a corrected sentence can invalidate its old frame.'),
            ('Build hard examples', 'Annotate passive voice, quoted plans, negated retries, simultaneous actions and pronouns that refer to earlier services. Include similar deployments from separate incidents. Group all notes from one incident before splitting. [[natural-language-processing/predicate-argument-roles-and-negation-scope|The frame contract]] defines the labels; [[natural-language-processing/role-frame-decoding-and-provenance|the decoder]] checks that extracted arguments are grounded.'),
            ('Compare and stage', 'Start with a dependency-based baseline and compare a learned extractor on the same audit. Score full frames and costly polarity mistakes, not only token spans. Show uncertain actor links and conflicting frames to a reviewer with surrounding text. Link approved frames to [[natural-language-processing/event-order-and-timeline-conflicts|timeline relations]] only after their source revision and identity scope are checked.'),
            ('Operate safely', 'Version tokenizer, parser, role labels and catalog snapshot together. Monitor missed rollbacks, false completed actions, reviewer corrections and stale frames after note edits. Delete derived frames when a note is removed under retention policy. If a new model increases wrong-polarity frames, revert the model bundle while retaining the reviewer audit.'),
        ],
        'code': '''def stage_action_frame(frame, note_revision):
    if frame["source_revision"] != note_revision:
        return {"state": "stale", "reason": "note-revised"}
    if frame["polarity"] != "affirmed" or frame["modality"] != "actual":
        return {"state": "review", "reason": "not-confirmed-action"}
    return {"state": "review", "reason": "confirm-operational-action"}

candidate = {"source_revision": "r47", "polarity": "negated",
             "modality": "actual", "predicate": "retry"}
assert stage_action_frame(candidate, "r47")["reason"] == "not-confirmed-action"
''',
        'cost': 'The gate is O(1) time per frame; extracting and reviewing action spans costs more. A conservative review queue may handle more frames, but it prevents a denied or merely planned action from being entered as completed. Measure incident-level false action rate alongside extraction throughput.',
        'mistakes': ['Writing an extracted action directly into an incident record.', 'Ignoring negation or modality when building a timeline.', 'Keeping frames tied to an edited note revision.', 'Joining similar actions from unrelated incidents.'],
        'related': [N + 'predicate-argument-roles-and-negation-scope', N + 'role-frame-decoding-and-provenance', N + 'incident-timeline-review-project', N + 'entity-relation-ledger-project', N + 'claim-conflict-and-temporal-review'],
    },
    {
        'path': N + 'hierarchical-label-contract-and-ancestor-closure',
        'title': 'Hierarchical labels: parent closure and multi-label meaning',
        'module': H, 'project': False,
        'summary': 'A ticket can belong to several branches of a taxonomy. Child labels require their parents, but parent-only cases remain valid.',
        'sections': [
            ('Define the taxonomy as versioned data', 'A support ticket might be tagged Billing → Refund and also Account → Access. A flat single-choice target loses one issue. Store stable label IDs, parent links, effective dates and a policy for parent-only labels. The displayed name may change without changing the ID. Do not infer that every parent has exactly one child; “Billing” may be the most specific supported answer. [[natural-language-processing/corpus-identity-and-label-policy|The general label contract]] defines provenance for reviewed examples.'),
            ('Close predicted paths deliberately', 'If a model predicts Refund, add Billing to the output set, or reject the inconsistent prediction under the task policy. Do not count an inferred parent as separately observed evidence. A graph taxonomy may permit multiple parents, so traverse all ancestors and detect cycles before release. Keep predicted labels, derived ancestors and reviewer labels distinguishable. This matters when analytics count how many tickets were explicitly about Billing versus inherited from a child.'),
            ('Calibrate by branch', 'Rare leaves have few examples and can be confused with common siblings. Use thresholds by branch and allow a parent-only or review outcome when child evidence is weak. Compare precision and recall at each depth, exact path accuracy and wrong-branch cost. A model that predicts broad parents well may still route specialist queues badly. [[natural-language-processing/hierarchical-thresholds-and-taxonomy-migration|Threshold and migration review]] covers release changes.'),
            ('Evaluate across changes', 'Group related conversations before splitting. Audit label co-occurrence, child-parent consistency and disagreement on parent-only cases. A taxonomy revision can change training targets even if text is unchanged; freeze the version during model comparison. The [[natural-language-processing/multilabel-support-routing-project|applied routing project]] tests a ticket with two valid branches and a costly false specialist handoff.'),
        ],
        'code': '''def close_ancestors(predicted_labels, parent_by_label):
    result = set(predicted_labels)
    frontier = list(predicted_labels)
    while frontier:
        label = frontier.pop()
        parent = parent_by_label.get(label)
        if parent is not None and parent not in result:
            result.add(parent)
            frontier.append(parent)
    return result

parents = {"refund": "billing", "billing": "support",
           "access": "account", "account": "support"}
assert close_ancestors({"refund", "access"}, parents) == {
    "refund", "billing", "access", "account", "support"}
''',
        'cost': 'Ancestor closure visits each reachable label once, O(v + e) time and O(v) space for v labels and e parent links. Validate the taxonomy for cycles before serving; a visited set prevents this code from looping but does not make a cyclic taxonomy meaningful. Model inference and specialist review dominate routing cost.',
        'mistakes': ['Forcing a ticket into one leaf when two issues are present.', 'Treating a derived parent as an independent model prediction.', 'Rejecting valid parent-only cases because no child was selected.', 'Comparing model scores across different taxonomy versions.'],
        'related': [N + 'hierarchical-thresholds-and-taxonomy-migration', N + 'multilabel-support-routing-project', N + 'corpus-identity-and-label-policy', N + 'classification-slices-and-abstention', N + 'weak-label-functions-and-abstention'],
    },
    {
        'path': N + 'hierarchical-thresholds-and-taxonomy-migration',
        'title': 'Hierarchical routing: branch thresholds and taxonomy migrations',
        'module': H, 'project': False,
        'summary': 'The threshold for a rare specialist queue should reflect its error cost. A label-tree change is a data migration, not just a UI rename.',
        'sections': [
            ('Use branch-level decisions', 'A broad Billing score may be reliable while the Refund versus Chargeback distinction remains uncertain. Emit Billing and request review instead of inventing a leaf. Set thresholds using held-out reviewed tickets and the cost of wrong specialist routing. A global cutoff can over-route a rare leaf or reject too many common cases. Keep the model score, threshold bundle and final label reason with each decision.'),
            ('Treat split and merge as migrations', 'When a queue splits, old examples may map to several new leaves; do not relabel them automatically from the former parent. When two labels merge, preserve the historical IDs and policy used at the time. Stage a migration with affected row counts and a reviewed sample. The current taxonomy must be acyclic and have known parents. [[natural-language-processing/hierarchical-label-contract-and-ancestor-closure|Ancestor closure]] supplies the serving invariant.'),
            ('Audit several kinds of error', 'Score branch precision, leaf precision, ancestor coverage, parent-only abstentions and actual routing outcomes. Compare latency and reviewer minutes. An apparent exact-path gain can come from predicting only common parents; a leaf gain can hide worse top-level routing. Slice by language and channel, and group repeat customer events across splits. [[natural-language-processing/multilingual-calibration-and-fallback|Multilingual calibration]] affects branch thresholds.'),
            ('Release with rollback', 'Version model, tokenizer, taxonomy graph, label display names and thresholds as one bundle. Replay a fixed audit when any part changes. Shadow-route traffic, inspect new branch conflicts and retain the old bundle for rollback. Update reports with a clear mapping from historical to current IDs rather than rewriting the past. The [[natural-language-processing/multilabel-support-routing-project|project]] exercises the staged migration.'),
        ],
        'code': '''def route_hierarchy(parent_score, child_scores, parent_cutoff,
                    child_cutoffs):
    if parent_score < parent_cutoff:
        return {"state": "review", "labels": []}
    accepted = [label for label, score in child_scores.items()
                if score >= child_cutoffs[label]]
    return {"state": "proposed", "labels": accepted or ["billing"]}

decision = route_hierarchy(0.91, {"refund": 0.62, "chargeback": 0.41},
                           0.75, {"refund": 0.82, "chargeback": 0.86})
assert decision["labels"] == ["billing"]
''',
        'cost': 'Checking c child scores takes O(c) time and O(c) output space. The code illustrates one branch; production routing must apply the graph and thresholds to every eligible branch. Human review cost grows where specialist decisions are uncertain, so monitor parent-only rate and wrong-leaf rate together.',
        'mistakes': ['Applying one threshold to every specialist leaf.', 'Rewriting old labels after a taxonomy split without review.', 'Measuring only exact path accuracy and hiding wrong top-level routes.', 'Serving a new taxonomy with model outputs trained on old IDs.'],
        'related': [N + 'hierarchical-label-contract-and-ancestor-closure', N + 'multilabel-support-routing-project', N + 'classification-slices-and-abstention', N + 'multilingual-calibration-and-fallback', N + 'annotation-disagreement-and-label-policy'],
    },
    {
        'path': N + 'multilabel-support-routing-project',
        'title': 'Project: route multi-issue tickets through a label hierarchy',
        'module': H, 'project': True,
        'summary': 'Propose all supported support queues, retain parent-only outcomes and stage taxonomy changes before agents receive new routes.',
        'sections': [
            ('Define the decision', 'A ticket can request a refund while reporting an account lockout. The service should propose both branches when evidence supports them, while leaving uncertain specialist leaves at the parent or sending the case for review. It cannot execute account or payment changes. Return label IDs, ancestor paths, score bundle, taxonomy revision and reason for each chosen or withheld leaf.'),
            ('Build a reviewed corpus', 'Sample single-issue, multi-issue and ambiguous cases, including repeated conversations and rare high-cost queues. Reviewers annotate independent branches and parent-only labels under one frozen taxonomy. Group customer events before splitting. [[natural-language-processing/hierarchical-label-contract-and-ancestor-closure|The label contract]] makes child-parent consistency explicit, and [[natural-language-processing/hierarchical-thresholds-and-taxonomy-migration|migration review]] handles taxonomy updates.'),
            ('Compare operating costs', 'Start with a flat baseline and compare a hierarchy-aware model using the same audit. Score branch precision, leaf recall, wrong specialist handoff, parent-only review rate and agent time. Report per-language performance. A model that returns every plausible queue may have high recall and unusable workload; cap routes under a written policy and show uncertainty instead of flooding teams.'),
            ('Release and correct', 'Shadow-route first. Version model, taxonomy and thresholds together, then review conflicts and high-confidence wrong routes. Preserve historical labels when queues merge or split. A reviewer correction should update the ticket decision and a separate learning record; do not silently rewrite the original prediction. On drift, revert the affected bundle and route uncertain cases to agents.'),
        ],
        'code': '''def admit_routing_labels(labels, parent_by_label, active_labels):
    unknown = set(labels) - active_labels
    if unknown:
        return {"state": "review", "reason": "retired-label"}
    complete = set(labels)
    frontier = list(labels)
    while frontier:
        parent = parent_by_label.get(frontier.pop())
        if parent and parent not in complete:
            complete.add(parent)
            frontier.append(parent)
    return {"state": "proposed", "labels": sorted(complete)}

parents = {"refund": "billing", "billing": "support",
           "access": "account", "account": "support"}
result = admit_routing_labels({"refund", "access"}, parents,
                              set(parents) | {"support"})
assert result["state"] == "proposed" and "billing" in result["labels"]
''',
        'cost': 'The graph walk is O(v + e) over reached labels and parent links, with O(v) space for the result. Model inference and cross-team review dominate cost. Measure how often extra routes actually help resolve the ticket; adding labels without improving resolution can make agents do more work.',
        'mistakes': ['Dropping the second issue because the classifier expects one label.', 'Sending an uncertain leaf directly to a specialist queue.', 'Losing taxonomy revision from stored predictions.', 'Training on corrected labels without preserving the original prediction.'],
        'related': [N + 'hierarchical-label-contract-and-ancestor-closure', N + 'hierarchical-thresholds-and-taxonomy-migration', N + 'ticket-routing-project', N + 'multilingual-ticket-routing-project', N + 'annotation-disagreement-and-label-policy'],
    },
]

crosslinks = [
    (N + 'dependency-tree-contract-and-token-alignment', N + 'predicate-argument-roles-and-negation-scope'),
    (N + 'relation-extraction-provenance', N + 'role-frame-decoding-and-provenance'),
    (N + 'incident-timeline-review-project', N + 'incident-action-frame-project'),
    (N + 'classification-slices-and-abstention', N + 'hierarchical-label-contract-and-ancestor-closure'),
    (N + 'multilingual-calibration-and-fallback', N + 'hierarchical-thresholds-and-taxonomy-migration'),
    (N + 'ticket-routing-project', N + 'multilabel-support-routing-project'),
]

if __name__ == '__main__':
    publish(lessons, (R, H), crosslinks,
            'aitrove-nlp-roles-hierarchy-import-20261006.json', 4806,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
