"""Extend NLP with temporal extraction and weak-label operations."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
T = 'Temporal language and incident timelines'
W = 'Weak labels and source-aware training'

lessons = [
    {
        'path': N + 'time-expression-anchor-and-zone-contract',
        'title': 'Time expressions: anchors, zones and unresolved dates',
        'module': T, 'project': False,
        'summary': '“Tomorrow” is not a date until its message time and local zone are known. Preserve the phrase, anchor and uncertainty together.',
        'sections': [
            ('Treat time as a claim with context', 'A support note written at 23:47 may say “tomorrow,” while a reply posted minutes later comes from another time zone. Store the source span, message timestamp, claimed local zone and speaker before normalizing anything. Prefer an explicitly supplied zone over an account default, and mark the source of that choice. Never infer a zone merely from a language. [[natural-language-processing/span-offset-annotation|Span identity]] keeps a normalized date tied to its original phrase.'),
            ('Separate point, interval and duration', '“At 08:30” is a time of day, “for 47 minutes” is a duration, and “through Friday” describes an interval endpoint. These must not share one date field. An unresolved weekday may refer to the next occurrence or a past one, depending on tense and reporting policy. Store a resolution state when the anchor is missing, rather than inventing midnight. Daylight-saving transitions can make a local wall time ambiguous or nonexistent; preserve the local expression and require an explicit offset decision.'),
            ('Resolve with a policy, not a guess', 'For relative phrases, apply a documented rule to the message timestamp in the stated zone. Record the rule version and the normalized result. For historical reports, distinguish event time from report time: “the gateway failed yesterday” was reported today. If the source was edited, recompute the result from the new source revision. [[natural-language-processing/event-order-and-timeline-conflicts|Timeline relations]] can then compare events without discarding their evidence.'),
            ('Audit temporal errors by impact', 'Measure exact date agreement, zone errors, unresolved rate and downstream event-order reversals. Include midnight, month-end, daylight-saving changes and cross-zone handoffs in the audit. A system can extract the word “tomorrow” perfectly yet resolve it to the wrong calendar day. The [[natural-language-processing/incident-timeline-review-project|incident timeline project]] tests that end-to-end behavior.'),
        ],
        'code': '''from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def resolve_tomorrow(message_timestamp, zone_name):
    if message_timestamp.tzinfo is None:
        raise ValueError("message timestamp needs an offset")
    local_date = message_timestamp.astimezone(ZoneInfo(zone_name)).date()
    return local_date + timedelta(days=1)

reported_at = datetime.fromisoformat("2026-10-06T18:17:00+00:00")
assert resolve_tomorrow(reported_at, "Asia/Kolkata").isoformat() == "2026-10-07"
''',
        'cost': 'Zone conversion and date arithmetic are O(1) for each resolved phrase; extraction over n characters is at least O(n). Zone database updates can change historical interpretation, so store the resolved value and transform version. Human review cost concentrates on missing zones and ambiguous local times; track that queue separately from ordinary extraction latency.',
        'mistakes': ['Resolving relative dates against processing time instead of message time.', 'Treating duration as an event timestamp.', 'Dropping the source phrase after computing a date.', 'Inferring a time zone from the script or language of a message.'],
        'related': [N + 'event-order-and-timeline-conflicts', N + 'incident-timeline-review-project', N + 'span-offset-annotation', N + 'relation-extraction-provenance', N + 'claim-conflict-and-temporal-review'],
    },
    {
        'path': N + 'event-order-and-timeline-conflicts',
        'title': 'Event order: evidence, partial timelines and contradictions',
        'module': T, 'project': False,
        'summary': 'A report can establish that one event preceded another without providing either exact timestamp. Keep a partial order and its evidence.',
        'sections': [
            ('Extract events before connecting them', 'Represent each event with an actor, action, source span, document revision and optional time interval. “The queue recovered after the retry policy changed” supplies an ordering relation but no clock reading. Record BEFORE, AFTER, OVERLAP or UNKNOWN as a relation between event IDs, with the sentence that supports it. Do not convert a model score into a factual timestamp. [[natural-language-processing/relation-extraction-provenance|Relation provenance]] explains why evidence belongs on each edge.'),
            ('Check the graph for impossible order', 'Before adding an edge, test whether it would make a cycle in an otherwise strict BEFORE graph. A cycle may be caused by extraction error, a revised incident note or two people describing different event scopes. Flag the conflict and keep both claims for review. Do not silently remove the lower-scoring claim: its source might be a signed correction. Treat OVERLAP separately, since forcing overlapping intervals into a strict sequence invents order.'),
            ('Handle revisions and uncertain anchors', 'A later status update may replace “recovered at 09:20” with “still failing at 09:20.” Keep both source revisions and mark which is current. Compare event identity, not just similar verbs; separate a canary deployment from the full rollout. Relative time normalization uses [[natural-language-processing/time-expression-anchor-and-zone-contract|anchor and zone policy]]. When a temporal phrase cannot be grounded, an ordering statement can still be useful if its source evidence remains clear.'),
            ('Evaluate the timeline people see', 'Score event span detection, relation accuracy, contradiction detection and the final timeline independently. A system can score well on pair relations but omit a critical rollback. Group updates from the same incident across splits and review temporal conflicts as cases, not isolated sentences. The [[natural-language-processing/incident-timeline-review-project|project]] stages a timeline rather than presenting it as settled fact.'),
        ],
        'code': '''def would_create_cycle(before_edges, earlier, later):
    if earlier == later:
        return True
    next_events = {}
    for source, target in before_edges:
        next_events.setdefault(source, set()).add(target)
    frontier = [later]
    seen = set()
    while frontier:
        event_id = frontier.pop()
        if event_id == earlier:
            return True
        if event_id not in seen:
            seen.add(event_id)
            frontier.extend(next_events.get(event_id, ()))
    return False

known = [("deploy-47", "alarm-82"), ("alarm-82", "rollback-91")]
assert would_create_cycle(known, "rollback-91", "deploy-47")
assert not would_create_cycle(known, "deploy-47", "recovery-120")
''',
        'cost': 'Building adjacency and searching reachable events takes O(v + e) time and space for v events and e strict-order edges. Repeating that test for many proposed edges is expensive; a maintained topological index may help at scale. The code checks graph consistency, not whether a source statement is true. Human conflict review remains necessary.',
        'mistakes': ['Assigning a precise time to a statement that only gives order.', 'Discarding contradictory source evidence after a model picks one edge.', 'Treating overlapping events as a strict before-after chain.', 'Ignoring event identity when a note describes a canary and a full rollout.'],
        'related': [N + 'time-expression-anchor-and-zone-contract', N + 'incident-timeline-review-project', N + 'claim-conflict-and-temporal-review', N + 'relation-extraction-provenance', N + 'document-summary-evidence-contract'],
    },
    {
        'path': N + 'incident-timeline-review-project',
        'title': 'Project: stage an evidence-backed incident timeline',
        'module': T, 'project': True,
        'summary': 'Extract time phrases and event order from incident updates, then ask a reviewer to resolve conflicts before a timeline is published.',
        'sections': [
            ('Set the workflow', 'Incident responders need a sequence of deployment, alarm, rollback and recovery. Each source update has its own author, revision and timestamp. The service proposes event nodes with exact source spans, then edges with supporting text. It may display UNKNOWN order and unresolved local time. A reviewer accepts or corrects the staged timeline; model output never rewrites the source log.'),
            ('Construct difficult cases', 'Include updates filed after midnight, cross-zone handoffs, “yesterday” statements, delayed reports and corrections that reverse an earlier claim. Add parallel incidents with similar service names so the extraction system cannot join unrelated events. Group all updates for one incident before splitting the audit. [[natural-language-processing/time-expression-anchor-and-zone-contract|Time grounding]] handles relative phrases; [[natural-language-processing/event-order-and-timeline-conflicts|event order]] handles partial relations.'),
            ('Stage, validate and review', 'Extract candidate events and time phrases, resolve only those with sufficient anchors and check the strict-order graph for cycles. Flag a conflict with both evidence spans and source revisions. Show reviewer edits as an overlay rather than mutating the original claim. A corrected note invalidates derived event edges from the old revision. Keep one incident-scoped timeline version for rollback and reproducibility.'),
            ('Measure release quality', 'Report missed critical events, wrong dates, reversed relations, unresolved count and reviewer time. A clean-looking timeline with an omitted rollback is worse than a clearly partial one. Shadow the system on recent incidents before using it for handoff reports. Access controls on the incident must carry through to every timeline node, quotation and cached view.'),
        ],
        'code': '''def stage_timeline_edge(earlier, later, source_revision, cycle_check):
    if not source_revision:
        raise ValueError("source revision is required")
    if cycle_check(earlier, later):
        return {"state": "review", "reason": "ordering-conflict",
                "source_revision": source_revision}
    return {"state": "proposed", "earlier": earlier, "later": later,
            "source_revision": source_revision}

proposal = stage_timeline_edge("deploy-47", "alarm-82", "note-r7",
                               lambda earlier, later: False)
assert proposal["state"] == "proposed"
''',
        'cost': 'The staging wrapper is O(1) apart from the supplied graph check, which can scan O(v + e) events and edges. Extraction and reviewer inspection dominate cost. Keep timeline edits scoped to one incident so a late correction does not require reprocessing the entire corpus, and measure wrong-order incidents rather than only edge throughput.',
        'mistakes': ['Publishing an extracted timeline without human review of conflicts.', 'Using the processing timestamp for every relative expression.', 'Merging events from incidents with similar wording.', 'Dropping the old note revision when an event is corrected.'],
        'related': [N + 'time-expression-anchor-and-zone-contract', N + 'event-order-and-timeline-conflicts', N + 'incident-handoff-summary-project', N + 'claim-conflict-and-temporal-review', N + 'entity-relation-ledger-project'],
    },
    {
        'path': N + 'weak-label-functions-and-abstention',
        'title': 'Weak label functions: coverage, conflict and abstention',
        'module': W, 'project': False,
        'summary': 'Rules derived from text patterns or metadata can accelerate labeling, but they produce noisy proposals rather than reviewed truth.',
        'sections': [
            ('Define each rule as a source', 'A label function might recognize a refund phrase or a routing queue tag. It should return one taxonomy label or abstain, plus a reason and rule version. Do not force a default label when its evidence is absent. Separate functions built from customer text from functions built from downstream agent actions; the latter may encode the answer and leak future information into training. [[natural-language-processing/corpus-identity-and-label-policy|The label policy]] defines the allowed target labels.'),
            ('Measure the label matrix', 'Compute each function’s coverage, overlap and conflicts on the unlabeled pool, then compare its precision on a small independently reviewed set. A rule that fires on nearly everything may inflate coverage while adding no useful signal. Correlated rules are not independent votes: two phrases copied from one template may make the same mistake. Retain the full function outputs with source IDs so an error can be traced to a rule, not just a final consensus label.'),
            ('Keep abstention useful', 'Some records will receive no vote or incompatible votes. Route a sample to human review, especially high-cost intents. An automatic tie-breaker based on alphabetical label order is not defensible. Track unresolved coverage by language, channel and time, since a stable overall rate can hide a new cohort with no useful functions. [[natural-language-processing/weak-label-conflict-and-audit-splits|Conflict audits]] decide whether a training label is admissible.'),
            ('Separate training labels from evaluation', 'Never evaluate against labels generated by the same functions used to train. Freeze a human-reviewed audit and group related conversations before splitting. Compare a manual-label baseline, weak labels and a mixed system on that audit. Report false automation and review burden, not merely how many extra rows were labeled. The [[natural-language-processing/weakly-supervised-ticket-triage-project|ticket project]] applies these gates.'),
        ],
        'code': '''def combine_rule_votes(votes):
    active = [label for label in votes if label is not None]
    if not active:
        return None, "no-coverage"
    unique = set(active)
    if len(unique) > 1:
        return None, "conflict"
    return active[0], "unanimous-proposal"

assert combine_rule_votes(["refund", None, "refund"]) == (
    "refund", "unanimous-proposal")
assert combine_rule_votes(["refund", "delivery"])[1] == "conflict"
''',
        'cost': 'Combining r votes is O(r) time and O(r) space in this straightforward implementation. More elaborate label models add fitting cost and assumptions about rule dependence. The main saving is reviewer time, but that saving disappears if noisy training labels create wrong production routes. Sample both unanimous and conflicting cases for audit.',
        'mistakes': ['Treating rule output as human-reviewed ground truth.', 'Counting correlated template rules as independent evidence.', 'Assigning a default label to every abstention.', 'Evaluating on labels created by the same rules.'],
        'related': [N + 'weak-label-conflict-and-audit-splits', N + 'weakly-supervised-ticket-triage-project', N + 'annotation-disagreement-and-label-policy', N + 'active-learning-sampling-and-coverage', N + 'classification-slices-and-abstention'],
    },
    {
        'path': N + 'weak-label-conflict-and-audit-splits',
        'title': 'Weak-label audits: correlated rules and split leakage',
        'module': W, 'project': False,
        'summary': 'The same template can trigger several rules and appear in both train and test. Audit these dependencies before claiming a gain.',
        'sections': [
            ('Trace every vote to evidence', 'A weakly labeled row needs rule IDs, rule revisions, source fields, conflict state and the text revision they saw. A billing keyword and a billing queue tag may both point to “refund,” but the queue tag might have been set after the final outcome. Exclude future metadata from a model that will predict at message arrival. Keep an explicit feature cutoff timestamp. [[natural-language-processing/weak-label-functions-and-abstention|The function contract]] defines a vote and abstention.'),
            ('Audit correlation and error', 'Inspect rule overlap and shared failure cases on reviewed data. If several rules are variants of one template, their agreement does not multiply confidence. Measure precision for each rule, for the combined proposal and for the abstained set. Review high-impact conflicts as cases, preserving disagreement reasons. A rule with strong overall precision may fail on code-switched text or negated requests; report those slices rather than hiding them in a pooled average.'),
            ('Build a clean holdout', 'Group messages by customer event, incident and reused template before splitting. Remove synthetic descendants and near duplicates from the opposite split. The final audit must be labeled independently of the weak functions, with a frozen policy version. If the same downstream queue tag generated labels and appears as an input feature, the validation is contaminated even with separate tickets. [[natural-language-processing/grouped-temporal-text-validation|Grouped temporal validation]] supplies the broader split design.'),
            ('Gate retraining and rollback', 'Version each function and its source schema. A new queue process or message template changes rule behavior, so monitor coverage, conflicts and reviewer precision after release. Retrain only when the new label matrix and independent audit both pass. Keep the previous model and label set so a bad rule update can be reversed. The [[natural-language-processing/weakly-supervised-ticket-triage-project|applied project]] makes these checks operational.'),
        ],
        'code': '''def weak_label_row_allowed(row, arrival_time):
    if row["text_revision"] != row["rule_text_revision"]:
        return False
    if row["feature_available_at"] > arrival_time:
        return False
    return row["consensus"] is not None and not row["conflict"]

candidate = {"text_revision": "r47", "rule_text_revision": "r47",
             "feature_available_at": 12, "consensus": "refund",
             "conflict": False}
assert weak_label_row_allowed(candidate, 17)
assert not weak_label_row_allowed({**candidate, "feature_available_at": 19}, 17)
''',
        'cost': 'The admission gate is O(1) per row. Comparing every pair of rule outputs for correlation is O(r²) across r functions before sampling; for a modest rule set this can be cheaper than deploying a complex label model. A clean independent holdout costs human review, but it prevents cheap generated labels from producing an expensive false confidence.',
        'mistakes': ['Using a post-resolution queue field to predict the intake route.', 'Placing copied messages on both sides of the split.', 'Assuming several highly correlated votes prove correctness.', 'Retiring a rule without tracking which training labels it created.'],
        'related': [N + 'weak-label-functions-and-abstention', N + 'weakly-supervised-ticket-triage-project', N + 'grouped-temporal-text-validation', N + 'annotation-disagreement-and-label-policy', N + 'low-resource-augmentation-and-slice-audit'],
    },
    {
        'path': N + 'weakly-supervised-ticket-triage-project',
        'title': 'Project: stage weakly labeled support-ticket triage',
        'module': W, 'project': True,
        'summary': 'Use auditable rules to propose intake labels, compare them with independent review and keep uncertain tickets in the agent queue.',
        'sections': [
            ('Set the decision boundary', 'At ticket arrival, the service may propose a routing intent; it cannot change a payment, account or customer record. Use only fields available at that moment. Each rule emits a label or abstention, reason and version. Preserve the original message and a record of all votes, including conflicts. The final label may be reviewed and corrected by an agent. [[natural-language-processing/weak-label-functions-and-abstention|Rule functions]] provide the proposal contract.'),
            ('Collect and split cases', 'Choose tickets from several channels and language slices, including negated requests and copied response templates. Group all messages from one customer event before splitting. Have agents independently label a held-out set under one policy. Do not use a queue tag assigned later as either a weak-label source or input feature at intake. [[natural-language-processing/weak-label-conflict-and-audit-splits|The audit boundary]] screens both rule votes and train/test groups.'),
            ('Compare three paths', 'Measure a small manual-only baseline, a rule-vote proposal and a model trained with admitted weak labels. Keep thresholds fixed on a separate validation set. Report per-intent precision, false route rate, abstention, agent queue age and the share of training rows from each rule family. A larger training set is only valuable if independent held-out decisions improve without hiding risk in the reject queue.'),
            ('Release with traceable rollback', 'Shadow-route first. Store model, taxonomy, rule set and feature cutoff as one version. Inspect confident wrong proposals as well as conflicts. If a rule begins firing on a new template or a channel’s false route rate rises, disable that rule and return its cases to review while rebuilding affected training rows. A ticket deletion must remove the raw message and any derived training copy.'),
        ],
        'code': '''def triage_proposal(rule_votes, allowed_labels):
    active = [vote for vote in rule_votes if vote is not None]
    if not active:
        return {"state": "review", "reason": "no-coverage"}
    if any(vote not in allowed_labels for vote in active):
        return {"state": "review", "reason": "retired-label"}
    if len(set(active)) != 1:
        return {"state": "review", "reason": "rule-conflict"}
    return {"state": "proposed", "intent": active[0]}

proposal = triage_proposal(["delivery", None, "delivery"],
                           {"delivery", "refund"})
assert proposal == {"state": "proposed", "intent": "delivery"}
''',
        'cost': 'Scanning r votes takes O(r) time and O(r) temporary space. Training on weak labels may reduce manual labeling, but rule maintenance and auditing still cost people-hours. Track cost per correctly routed ticket after review, not the number of generated labels. An abstention that reaches an agent safely is preferable to a wrong automatic route.',
        'mistakes': ['Sending a weak label directly to an irreversible action.', 'Training on metadata that only exists after agent resolution.', 'Claiming success from the volume of newly labeled rows.', 'Leaving retired-rule rows in the next training build.'],
        'related': [N + 'weak-label-functions-and-abstention', N + 'weak-label-conflict-and-audit-splits', N + 'ticket-routing-project', N + 'active-learning-sampling-and-coverage', N + 'privacy-safe-ticket-pipeline-project'],
    },
]

crosslinks = [
    (N + 'span-offset-annotation', N + 'time-expression-anchor-and-zone-contract'),
    (N + 'claim-conflict-and-temporal-review', N + 'event-order-and-timeline-conflicts'),
    (N + 'incident-handoff-summary-project', N + 'incident-timeline-review-project'),
    (N + 'corpus-identity-and-label-policy', N + 'weak-label-functions-and-abstention'),
    (N + 'grouped-temporal-text-validation', N + 'weak-label-conflict-and-audit-splits'),
    (N + 'ticket-routing-project', N + 'weakly-supervised-ticket-triage-project'),
]

if __name__ == '__main__':
    publish(lessons, (T, W), crosslinks,
            'aitrove-nlp-temporal-weaklabels-import-20261006.json', 4788,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
