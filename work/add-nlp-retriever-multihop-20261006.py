"""Add retrieval-label and multi-step evidence modules to NLP."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
R = 'Retriever training evidence and negatives'
M = 'Multi-step questions and evidence paths'

lessons = [
    {
        'path': N + 'retrieval-positive-pair-identity-and-revision',
        'title': 'Retrieval positives: query intent, passage identity and revision',
        'module': R, 'project': False,
        'summary': 'A positive query-passage pair should carry evidence for the requested answer at a known source revision, not merely share terms with the query.',
        'sections': [
            ('Define the relevance judgment', 'A query about gateway-west rollback time may retrieve a page that mentions the service but discusses alert thresholds. That page is topically related and still not an answer-bearing positive. Record the query ID, intent, service, environment, passage ID, source revision, judged answer span and reviewer decision. A passage can be relevant for one query and irrelevant for another. [[natural-language-processing/hybrid-ranking-and-access-filters|Hybrid ranking]] can find candidates, but it cannot supply gold relevance labels by itself.'),
            ('Keep source identity stable', 'Store the canonical passage ID separately from its current text and revision. A corrected runbook may keep the same section path while changing a numeric limit; the old positive judgment must not be reused blindly. Preserve prior judgments for audit and mark them stale until a reviewer checks the new revision. [[natural-language-processing/passage-revision-and-index-audit|Passage revision auditing]] carries the source change into the index; pair labels must follow the same change.'),
            ('Distinguish passage support from answer correctness', 'A relevant passage may require a second passage to answer a compound question. Label direct support, partial support and non-support separately. Attach exact evidence spans and policy context. Do not mark a passage positive because a generated answer sounds plausible; judge the passage before seeing the generated answer. [[natural-language-processing/generated-claim-evidence-and-unanswered-state|Claim evidence contracts]] require the final answer to point back to support that actually exists.'),
            ('Audit the training set', 'Sample positives by query type, source language, service and revision. Check whether protected or restricted passages entered the training export. Group repeated queries and revised passages into families before splitting. Measure disagreement on borderline judgments and how often a passage is labeled positive for one revision but not another. The [[natural-language-processing/retrieval-negative-review-and-false-negative-risk|negative review]] uses these positive labels to avoid training against a passage that also answers the question.'),
        ],
        'code': '''def reviewed_positive_pair(query, passage, evidence_start, evidence_end):
    if query["service_id"] != passage["service_id"]:
        raise ValueError("query and passage service differ")
    if not passage["revision_id"] or not passage["passage_id"]:
        raise ValueError("source identity is required")
    if not (0 <= evidence_start < evidence_end <= len(passage["text"])):
        raise ValueError("invalid evidence span")
    return {"query_id": query["query_id"],
            "passage_id": passage["passage_id"],
            "revision_id": passage["revision_id"],
            "evidence": passage["text"][evidence_start:evidence_end]}

query = {"query_id": "rollback-47", "service_id": "gateway-west"}
passage = {"passage_id": "runbook-82", "revision_id": "r8",
           "service_id": "gateway-west", "text": "Wait 82 minutes before rollback."}
pair = reviewed_positive_pair(query, passage, 5, 15)
assert pair["evidence"] == "82 minutes"
assert pair["revision_id"] == "r8"
''',
        'cost': 'Bounds and identity checks are O(1) for fixed-size metadata; copying an evidence span of s characters costs O(s) time and space. Human relevance review and passage retrieval dominate real collection cost. This function validates a reviewed span but cannot determine whether that span actually answers the query.',
        'mistakes': ['Calling a passage positive because it contains the same service name.', 'Reusing an old relevance label after a threshold changed.', 'Taking a model-generated answer as proof of passage support.', 'Training on restricted passage text without access review.'],
        'related': [N + 'retrieval-negative-review-and-false-negative-risk', N + 'runbook-retriever-label-audit-project', N + 'hybrid-ranking-and-access-filters', N + 'passage-revision-and-index-audit', N + 'generated-claim-evidence-and-unanswered-state'],
    },
    {
        'path': N + 'retrieval-negative-review-and-false-negative-risk',
        'title': 'Retrieval negatives: hard candidates and false-negative risk',
        'module': R, 'project': False,
        'summary': 'A high-ranked unjudged passage is a useful review candidate, not automatically a negative training label.',
        'sections': [
            ('Start from what is known', 'A hard negative looks relevant to the retriever yet does not satisfy the query. The gateway-east rollback section may resemble a gateway-west answer while referring to the wrong service. That is a defensible negative after review. An unjudged gateway-west passage might answer the query in different words; forcing it into the negative class trains the retriever to suppress useful evidence. Keep judged negatives, unjudged candidates and known positives as separate states. [[natural-language-processing/retrieval-positive-pair-identity-and-revision|Positive-pair identity]] anchors the known answer-bearing passages.'),
            ('Review candidate origin', 'Mine candidates from the current retriever, lexical search and nearby sections of the same runbook. Record score, source revision, access level, language and why the passage was nominated. Exclude exact copies and known positive families before labeling; route semantic near-matches to a reviewer. A candidate from a later runbook revision can be a valid future positive rather than a safe negative for an old query. [[natural-language-processing/near-duplicate-text-families-and-review|Text-family review]] catches copied or revised answer spans.'),
            ('Guard the optimization signal', 'Compare query and candidate under the same service, environment, version and requested action. Do not equate absence from a sparse judgment set with non-relevance. A false negative is particularly harmful when it is a strong answer-bearing passage, because training pushes it away from the query. Keep a small pool of randomly sampled negatives for coverage and review the difficult ones more carefully. Label uncertainty explicitly rather than pretending every mined candidate has a binary truth.'),
            ('Evaluate after mining', 'Freeze an independent judgment set before tuning the retriever. Measure recall of all judged positives, errors on hard negatives and the fraction of mined candidates later found relevant. Slice by language pair, service and source revision. A rising training score can coexist with worse retrieval if false negatives accumulate. The [[natural-language-processing/runbook-retriever-label-audit-project|label audit project]] blocks a training export when an answer-bearing passage appears in both positive and negative roles.'),
        ],
        'code': '''def negative_review_queue(query_id, candidates, positive_family_ids,
                          allowed_access):
    queue = []
    for candidate in candidates:
        if candidate["access_level"] not in allowed_access:
            continue
        if candidate["family_id"] in positive_family_ids:
            continue
        if candidate["judgment"] == "positive":
            continue
        queue.append({"query_id": query_id,
                      "passage_id": candidate["passage_id"],
                      "state": "review-needed"})
    return queue

candidates = [
    {"passage_id": "runbook-82", "family_id": "rollback-west",
     "access_level": "operations", "judgment": "unjudged"},
    {"passage_id": "runbook-91", "family_id": "rollback-east",
     "access_level": "operations", "judgment": "unjudged"},
]
queue = negative_review_queue("rollback-47", candidates,
                              {"rollback-west"}, {"operations"})
assert queue == [{"query_id": "rollback-47", "passage_id": "runbook-91",
                  "state": "review-needed"}]
''',
        'cost': 'Scanning c candidates takes expected O(c) time with O(c) output space. The function only proposes review candidates; it does not issue negative labels. Candidate mining through an index, source-family comparison and human adjudication carry separate costs that rise with corpus size and language coverage.',
        'mistakes': ['Treating every unjudged search result as a negative.', 'Pushing a copied positive passage away because it has a different URL.', 'Mining from a newer revision while ignoring changed answer truth.', 'Letting access-restricted candidates leak into a training export.'],
        'related': [N + 'retrieval-positive-pair-identity-and-revision', N + 'runbook-retriever-label-audit-project', N + 'near-duplicate-text-families-and-review', N + 'cross-language-ranking-and-evidence-review', N + 'grouped-temporal-text-validation'],
    },
    {
        'path': N + 'runbook-retriever-label-audit-project',
        'title': 'Project: audit runbook retrieval pairs before training',
        'module': R, 'project': True,
        'summary': 'Build a versioned query-passage training manifest, review difficult negatives and hold an export when an answer-bearing family is mislabeled.',
        'sections': [
            ('Specify the retrieval job', 'A runbook retriever must find the current gateway-west rollback instruction for several question forms. Collect reviewed query-passage positives with exact source spans and revisions. Mine confusing gateway-east, obsolete and non-answer sections as candidate negatives. Do not train from the final answer alone; the passage judgment is the unit the retriever learns. [[natural-language-processing/retrieval-positive-pair-identity-and-revision|Positive-pair contracts]] keep the label tied to a source revision.'),
            ('Build a review fixture', 'Include paraphrased questions, code-switched queries, copied runbook sections and a changed numeric threshold. Give reviewers the original passage, service and environment without displaying the model’s proposed label. Record positive, negative or unresolved, plus a reason. Family IDs connect copies and revisions; a negative for one query may be positive for another. Split by incident and source family before comparing model changes. [[natural-language-processing/family-aware-text-split-and-contamination|Family-aware splits]] prevent an almost identical passage from leaking across evaluation partitions.'),
            ('Enforce manifest invariants', 'Check that no query-family pair is both positive and negative in the same source revision. Reject empty positive sets and unresolved candidates presented as labeled negatives. Enforce access policy before exporting text. The example gate catches direct contradictions; human review is still required to find a relevant passage the judgment set missed. [[natural-language-processing/retrieval-negative-review-and-false-negative-risk|Negative review]] keeps high-ranked unknowns in a queue until a decision is supported.'),
            ('Report a bounded result', 'Evaluate candidate recall, first relevant rank and hard-negative errors on a frozen, independently judged set. Report false-negative corrections and reviewer disagreement. Hold training if the label manifest contradicts itself or contains restricted text. After repair, train and re-evaluate without tuning against the held-out judgments. The released artifact includes manifest version, corpus snapshot, index version and known coverage limits.'),
        ],
        'code': '''def retrieval_manifest_conflicts(labels):
    judgments = {}
    for row in labels:
        key = (row["query_id"], row["family_id"], row["revision_id"])
        if row["label"] not in {"positive", "negative", "unresolved"}:
            raise ValueError("unknown retrieval label")
        judgments.setdefault(key, set()).add(row["label"])
    return {key: sorted(values) for key, values in judgments.items()
            if "positive" in values and "negative" in values}

labels = [
    {"query_id": "rollback-47", "family_id": "runbook-west",
     "revision_id": "r8", "label": "positive"},
    {"query_id": "rollback-47", "family_id": "runbook-west",
     "revision_id": "r8", "label": "negative"},
]
assert retrieval_manifest_conflicts(labels) == {
    ("rollback-47", "runbook-west", "r8"): ["negative", "positive"]}
labels[1]["label"] = "unresolved"
assert retrieval_manifest_conflicts(labels) == {}
''',
        'cost': 'Checking n label rows takes expected O(n) time and O(n) space for grouped judgments; sorting the small conflicting label sets adds bounded work here. A contradiction-free manifest may still contain false negatives, missing positives or access violations, so this is one release check rather than a complete relevance audit.',
        'mistakes': ['Exporting unresolved candidates as negatives.', 'Ignoring contradictory labels for the same query-family revision.', 'Evaluating with copied runbook sections in both training and test.', 'Claiming the manifest is clean only because its explicit conflicts were removed.'],
        'related': [N + 'retrieval-positive-pair-identity-and-revision', N + 'retrieval-negative-review-and-false-negative-risk', N + 'family-aware-text-split-and-contamination', N + 'hybrid-ranking-and-access-filters', N + 'runbook-question-answering-project'],
    },
    {
        'path': N + 'multi-step-question-decomposition-and-slot-dependencies',
        'title': 'Multi-step questions: decompose answer slots and dependencies',
        'module': M, 'project': False,
        'summary': 'A compound question can require several facts from different passages. Represent the needed slots and their dependency order before writing an answer.',
        'sections': [
            ('Identify the missing facts', '“Which rollback rule applies to the service that failed after the second retry?” requires an event-to-service fact and then a service-to-rule fact. Searching only the whole sentence can retrieve a plausible rule for the wrong service. Define answer slots for event identity, service ID, active runbook revision and rollback rule. Mark which slot depends on another. [[natural-language-processing/dialogue-state-slots-and-corrections|Dialogue slots]] record user-provided state; a multi-step question plan also records evidence needed from documents.'),
            ('Bound each subquestion', 'Each step should state its input facts, retrieval scope and output type. The first may resolve a log event to gateway-west; the second may search gateway-west runbook passages under the active revision. Keep inferred facts as proposed until a source span verifies them. Do not let an early guess silently become a hard filter that prevents finding the correct later evidence. [[natural-language-processing/log-template-constant-variable-boundary|Log event identity]] can supply the first link in an operational case.'),
            ('Detect cycles and missing steps', 'A plan with a missing prerequisite cannot produce a supported final answer. A cycle such as “resolve service from rule” and “resolve rule from service” needs a new anchor or a broader search, not repeated blind retrieval. Keep plan revisions and reviewer edits so failures are attributable. A fixed maximum number of steps limits cost, but it should not convert an incomplete answer into a confident one. The code below checks whether every declared dependency is present and orders steps when possible.'),
            ('Test the decomposition', 'Evaluate slot coverage, dependency correctness, source support for each step and final answer accuracy separately. Include one-hop distractors that look answer-ready and cases where the second passage contradicts the first. [[natural-language-processing/multi-passage-claim-aggregation-and-conflict|Multi-passage conflict review]] handles disagreements among retrieved facts; the [[natural-language-processing/multi-step-evidence-chain-and-join-identity|chain contract]] ensures that a seemingly complete path actually joins on the same entity and revision.'),
        ],
        'code': '''def ordered_question_steps(dependencies):
    remaining = {step: set(parents) for step, parents in dependencies.items()}
    unknown = set().union(*remaining.values()) - remaining.keys() if remaining else set()
    if unknown:
        raise ValueError("unknown prerequisite: " + ", ".join(sorted(unknown)))
    ordered = []
    while remaining:
        ready = sorted(step for step, parents in remaining.items() if not parents)
        if not ready:
            raise ValueError("cyclic question plan")
        for step in ready:
            ordered.append(step)
            del remaining[step]
        for parents in remaining.values():
            parents.difference_update(ready)
    return ordered

plan = {"resolve_event": set(), "identify_service": {"resolve_event"},
        "lookup_rule": {"identify_service"}}
assert ordered_question_steps(plan) == [
    "resolve_event", "identify_service", "lookup_rule"]
''',
        'cost': 'This compact implementation scans remaining steps repeatedly and can take O(s² + e) time for s steps and e dependencies, with O(s + e) space. Plans are usually short; a queue-based topological sort is preferable if hundreds of steps are expected. The order check does not prove that any subquestion has correct evidence.',
        'mistakes': ['Searching a compound question as if one passage must answer every part.', 'Using an unverified first-step guess to filter later search.', 'Treating a cyclic plan as evidence that the question was answered.', 'Reporting a final answer while a required slot remains unresolved.'],
        'related': [N + 'multi-step-evidence-chain-and-join-identity', N + 'incident-multihop-answer-audit-project', N + 'dialogue-state-slots-and-corrections', N + 'log-template-constant-variable-boundary', N + 'multi-passage-claim-aggregation-and-conflict'],
    },
    {
        'path': N + 'multi-step-evidence-chain-and-join-identity',
        'title': 'Multi-step evidence chains: join identity, revision and access',
        'module': M, 'project': False,
        'summary': 'Several individually relevant passages form an answer only when their entities, scope and source revisions connect correctly.',
        'sections': [
            ('Treat the path as a typed join', 'A log passage can identify gateway-west as the failed service. A runbook passage can give gateway-west a rollback rule. The shared service ID is the join key; a similar service name or translated label is not enough. Record the entity type, normalized ID, source span and revision on each edge. [[natural-language-processing/entity-link-version-and-merge-review|Entity-link versioning]] protects the join if aliases or service ownership change.'),
            ('Preserve scope across hops', 'An incident may be in production while a runbook passage applies only to staging. A correct service join can still yield a wrong answer when environment, region, time or access policy differs. Validate these fields at each transition. A passage from a restricted appendix cannot be used to compose a public answer simply because the first passage was public. [[natural-language-processing/hybrid-ranking-and-access-filters|Access filtering]] belongs before evidence assembly as well as before final display.'),
            ('Avoid path laundering', 'Two passages may each look credible while the connection between them is inferred without support. Store the exact edge claim and evidence span that justifies it. If a link depends on a guessed alias or outdated revision, mark the chain unresolved. Do not let answer generation smooth over a missing middle step. [[natural-language-processing/generated-claim-evidence-and-unanswered-state|Unanswered states]] are necessary when the available passages do not connect.'),
            ('Evaluate entire chains', 'Measure passage recall, edge correctness, complete-chain support and final answer accuracy. Include distractor chains that share one entity but differ on environment or revision. A metric based only on whether the final number matches may reward a lucky guess or memorized rule. The [[natural-language-processing/incident-multihop-answer-audit-project|incident project]] requires a traceable path from event to service to current rule.'),
        ],
        'code': '''def join_incident_to_rule(event_fact, rule_fact, active_revision,
                          allowed_access):
    if event_fact["service_id"] != rule_fact["service_id"]:
        return {"state": "unresolved", "reason": "service-join"}
    if event_fact["environment"] != rule_fact["environment"]:
        return {"state": "unresolved", "reason": "environment-scope"}
    if rule_fact["revision_id"] != active_revision:
        return {"state": "unresolved", "reason": "stale-rule"}
    if rule_fact["access_level"] not in allowed_access:
        return {"state": "unresolved", "reason": "access"}
    return {"state": "supported", "service_id": event_fact["service_id"],
            "rule_passage_id": rule_fact["passage_id"]}

event = {"service_id": "gateway-west", "environment": "production"}
rule = {"service_id": "gateway-west", "environment": "production",
        "revision_id": "r8", "access_level": "operations",
        "passage_id": "runbook-82"}
assert join_incident_to_rule(event, rule, "r8", {"operations"}) == {
    "state": "supported", "service_id": "gateway-west",
    "rule_passage_id": "runbook-82"}
assert join_incident_to_rule(event, {**rule, "environment": "staging"},
                             "r8", {"operations"})["state"] == "unresolved"
''',
        'cost': 'Checking one fixed two-hop join takes O(1) expected time and space. For many candidate passages, pairwise joins can be O(a × b); indexing by typed entity and scope reduces candidate work. This gate checks recorded metadata, not whether either passage was extracted correctly or whether the rule text truly supports an answer.',
        'mistakes': ['Joining similar names without a canonical service ID.', 'Combining a production event with a staging-only rule.', 'Using one restricted hop in a public answer.', 'Scoring only the final answer while ignoring a broken evidence edge.'],
        'related': [N + 'multi-step-question-decomposition-and-slot-dependencies', N + 'incident-multihop-answer-audit-project', N + 'entity-link-version-and-merge-review', N + 'multi-passage-claim-aggregation-and-conflict', N + 'generated-claim-evidence-and-unanswered-state'],
    },
    {
        'path': N + 'incident-multihop-answer-audit-project',
        'title': 'Project: audit a multi-step incident answer from event to rule',
        'module': M, 'project': True,
        'summary': 'Resolve an incident event to a service, join that service to the active runbook rule and release an answer only when each hop has reviewed evidence.',
        'sections': [
            ('State the question', 'An operator asks which rollback rule applies to the service whose retry failed after a second attempt. One log identifies the event; a separate service registry resolves the service; the current runbook supplies the rule. Include a gateway-east distractor, a staging-only rule and an old gateway-west revision. The system must preserve each join rather than selecting a plausible rollback number from memory. [[natural-language-processing/multi-step-question-decomposition-and-slot-dependencies|Question decomposition]] names the required facts before retrieval.'),
            ('Create the evidence fixture', 'Reviewers mark source spans for the retry event, canonical service ID, environment and active rule. Record document IDs, revisions, access levels and every edge claim. Include a case where the service alias is ambiguous and a case where the current runbook is unavailable; both should stay unanswered. Freeze a set of complete and broken chains before adjusting retrieval or answer prompts. A final-answer-only benchmark cannot distinguish a correct chain from a lucky guess.'),
            ('Trace and gate the path', 'Retrieve each step under the policy for its source. Verify the event-to-service link, then the service-to-rule link under the active revision. Reject a chain if any required edge lacks a reviewed source span or if scopes disagree. [[natural-language-processing/multi-step-evidence-chain-and-join-identity|Evidence-chain checks]] cover identity and scope; [[natural-language-processing/claim-conflict-and-temporal-review|temporal review]] handles conflicting current and historical statements.'),
            ('Release a bounded answer', 'Report per-hop recall, correct joins, complete-chain support, answer correctness and abstention. Inspect every failed path and preserve its evidence IDs for repair. The final response should name its source passage internally and reflect the current rule, while an unresolved case should say which hop could not be verified. The code below enforces the last step on an already reviewed chain; retrieval and reading remain separate tests.'),
        ],
        'code': '''def release_chain_answer(required_steps, verified_steps,
                         answer_value, answer_passage_id):
    missing = sorted(set(required_steps) - set(verified_steps))
    if missing or not answer_value or not answer_passage_id:
        return {"state": "unanswered", "missing_steps": missing}
    return {"state": "supported", "answer_value": answer_value,
            "answer_passage_id": answer_passage_id}

required = {"retry_event", "service_identity", "active_rule"}
verified = {"retry_event", "service_identity"}
assert release_chain_answer(required, verified, "82 minutes",
                            "runbook-82") == {
    "state": "unanswered", "missing_steps": ["active_rule"]}
verified.add("active_rule")
assert release_chain_answer(required, verified, "82 minutes",
                            "runbook-82")["state"] == "supported"
''',
        'cost': 'Comparing r required steps with verified steps takes expected O(r + v) time and O(r + v) space for set copies, plus O(r log r) sorting when steps are missing. Retrieval and human evidence review dominate end-to-end cost. An apparently complete step list is insufficient unless each step is tied to a valid, current, authorized span.',
        'mistakes': ['Returning a memorized rule without resolving the service.', 'Calling a chain complete after finding only the event and service.', 'Combining evidence from incompatible environments.', 'Hiding an unresolved join behind a fluent answer.'],
        'related': [N + 'multi-step-question-decomposition-and-slot-dependencies', N + 'multi-step-evidence-chain-and-join-identity', N + 'event-order-and-timeline-conflicts', N + 'runbook-question-answering-project', N + 'claim-conflict-and-temporal-review'],
    },
]

crosslinks = [
    (N + 'passage-revision-and-index-audit', N + 'retrieval-positive-pair-identity-and-revision'),
    (N + 'hybrid-ranking-and-access-filters', N + 'retrieval-negative-review-and-false-negative-risk'),
    (N + 'runbook-retriever-label-audit-project', N + 'multi-step-question-decomposition-and-slot-dependencies'),
    (N + 'long-document-evidence-index-and-coverage', N + 'multi-step-question-decomposition-and-slot-dependencies'),
    (N + 'entity-link-version-and-merge-review', N + 'multi-step-evidence-chain-and-join-identity'),
    (N + 'runbook-question-answering-project', N + 'incident-multihop-answer-audit-project'),
]

if __name__ == '__main__':
    publish(lessons, (R, M), crosslinks,
            'aitrove-nlp-retriever-multihop-import-20261006.json', 4866,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
