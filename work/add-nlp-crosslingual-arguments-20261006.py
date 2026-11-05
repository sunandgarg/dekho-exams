"""Add cross-language retrieval and argument-structure modules to NLP."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
L = 'Cross-language retrieval and evidence'
A = 'Argument structure and target stance'

lessons = [
    {
        'path': N + 'cross-language-query-document-contract',
        'title': 'Cross-language retrieval: query, document and locale contracts',
        'module': L, 'project': False,
        'summary': 'A query and a relevant document can use different languages. Preserve intent, protected identifiers and document provenance through retrieval.',
        'sections': [
            ('Separate user language from evidence language', 'A support engineer may ask in Hindi for the rollback limit while the runbook is written in English. Record query language, requested answer language, document language and service scope separately. Do not infer that a shared script means a shared language, or that an English identifier should be translated. Keep the raw query and its normalized form tied to one request ID. [[natural-language-processing/script-profile-and-code-switching-boundary|Code-switching policy]] matters when one sentence combines a local-language question with an English service name.'),
            ('Protect operational terms', 'Service IDs, error codes, release tags and command names must survive translation or cross-language embedding. A translated phrase can be fluent yet point to the wrong service. Represent protected terms as typed slots and validate that every candidate query retains them. Keep a glossary version for domain terms whose ordinary-language meaning differs from their operational meaning. [[natural-language-processing/translation-placeholder-and-terminology-contract|Translation placeholders]] provide the same safeguard when producing a localized reply.'),
            ('Keep multiple retrieval routes inspectable', 'Candidate generation may combine a translated query, a multilingual embedding and exact matches for protected identifiers. Store which route produced each candidate and the version of its index or model. Access filters must run before a passage is exposed to ranking or answer generation. A translated query is a proposal, not a replacement for the original user intent. If language detection is uncertain, search under several plausible language hypotheses and preserve that uncertainty for review.'),
            ('Test actual cross-language relevance', 'Create query-document judgments where the query and evidence use different languages. Include false friends, untranslated product names, mixed-script tickets and documents whose wording changed between revisions. Measure recall before ranking and final relevance by language pair and service. A high monolingual score does not establish cross-language quality. The [[natural-language-processing/cross-language-ranking-and-evidence-review|ranking audit]] verifies that a retrieved passage supports the requested answer rather than merely sharing a translated keyword.'),
        ],
        'code': '''def prepare_retrieval_request(raw_query, query_language, answer_language,
                              protected_terms, translated_candidates):
    if not raw_query.strip() or not query_language or not answer_language:
        raise ValueError("query and language codes are required")
    accepted = [candidate for candidate in translated_candidates
                if all(term in candidate for term in protected_terms)]
    return {"raw_query": raw_query, "query_language": query_language,
            "answer_language": answer_language,
            "protected_terms": tuple(sorted(protected_terms)),
            "candidate_queries": accepted,
            "state": "ready" if accepted else "review"}

request = prepare_retrieval_request(
    "gateway-west ka rollback limit kya hai?", "hi", "hi",
    {"gateway-west"},
    ["What is the rollback limit for gateway-west?",
     "What is the rollback limit for the gateway?"])
assert request["candidate_queries"] == [
    "What is the rollback limit for gateway-west?"]
assert request["state"] == "ready"
''',
        'cost': 'Validating c candidates against p protected terms takes O(c × p × n) in the worst case for candidate length n with simple substring checks. Translation, embedding and index search have their own costs. The example is an admission check, not a translation engine; production matching should use typed slots and boundary-aware validation so one identifier cannot accidentally match inside another.',
        'mistakes': ['Translating a service ID as ordinary prose.', 'Dropping the original query after translation.', 'Evaluating only same-language query-document pairs.', 'Ranking restricted passages before access policy is applied.'],
        'related': [N + 'cross-language-ranking-and-evidence-review', N + 'multilingual-runbook-search-project', N + 'script-profile-and-code-switching-boundary', N + 'translation-placeholder-and-terminology-contract', N + 'hybrid-ranking-and-access-filters'],
    },
    {
        'path': N + 'cross-language-ranking-and-evidence-review',
        'title': 'Cross-language ranking and source-language evidence review',
        'module': L, 'project': False,
        'summary': 'Rank foreign-language passages against a query while keeping a verifiable path back to the original source text.',
        'sections': [
            ('Judge the source passage', 'A translated snippet may be easier to read, but the evidence is the original passage at a particular revision. Store its source-language span, document ID, access level and retrieval score. A localized display can accompany the passage, yet it must not silently replace the source text during verification. [[natural-language-processing/passage-revision-and-index-audit|Passage revision auditing]] prevents an answer from relying on a stale translation of an updated runbook.'),
            ('Separate recall from ranking', 'If the relevant foreign-language document never enters the candidate set, reranking cannot recover it. Measure candidate recall at the chosen depth, then rank quality over the same judgments. Compare translated-query, multilingual-vector and exact-ID routes by language pair. Merge candidates by document and passage identity; do not mistake two translations of one passage for two independent sources. [[natural-language-processing/hybrid-ranking-and-access-filters|Hybrid ranking]] supplies a useful baseline, but the cross-language judgment set must contain meaning-based relevance rather than keyword overlap alone.'),
            ('Verify support before answering', 'The top passage can mention the right service while contradicting the query premise. Check the requested environment, time, version and action against the original span. Record whether the answer is directly supported, requires multiple passages or remains unanswered. If no reviewer can verify the source language, route the result to a qualified reviewer or abstain. [[natural-language-processing/generated-claim-evidence-and-unanswered-state|Evidence contracts]] prevent a fluent localized answer from becoming unsupported advice.'),
            ('Report uneven performance', 'Aggregate scores can hide failure for a low-volume language pair. Report candidate recall, rank positions, verified answer support and abstention by query language, document language, service and script pattern. Include code-switched queries and translated terms with several domain meanings. The [[natural-language-processing/multilingual-runbook-search-project|multilingual search project]] gates answers on source passage identity and language-aware review, not merely on a cosine score.'),
        ],
        'code': '''def first_relevant_rank(ranked_passage_ids, judged_relevant_ids):
    for rank, passage_id in enumerate(ranked_passage_ids, start=1):
        if passage_id in judged_relevant_ids:
            return rank
    return None

def reciprocal_rank_by_pair(evaluations):
    totals = {}
    for case in evaluations:
        language_pair = (case["query_language"], case["document_language"])
        rank = first_relevant_rank(case["ranked_passages"],
                                   set(case["relevant_passages"]))
        score, count = totals.get(language_pair, (0.0, 0))
        totals[language_pair] = (score + (1 / rank if rank else 0.0), count + 1)
    return {pair: score / count for pair, (score, count) in totals.items()}

cases = [{"query_language": "hi", "document_language": "en",
          "ranked_passages": ["gateway-47", "runbook-82"],
          "relevant_passages": ["runbook-82"]}]
assert reciprocal_rank_by_pair(cases) == {("hi", "en"): 0.5}
assert first_relevant_rank(["gateway-47"], {"runbook-82"}) is None
''',
        'cost': 'For q cases with k ranked passages each, scoring takes O(q × k) time and O(q) space in the worst case for per-pair aggregates, excluding relevance-set creation. Reciprocal rank measures placement of the first judged relevant passage, not whether an answer is supported or whether every source language has adequate coverage. Keep those checks separate.',
        'mistakes': ['Treating a localized snippet as the canonical evidence.', 'Reporting reranking quality without candidate recall.', 'Counting two translations of one passage as independent support.', 'Accepting a top hit that names the service but misses the environment or revision.'],
        'related': [N + 'cross-language-query-document-contract', N + 'multilingual-runbook-search-project', N + 'hybrid-ranking-and-access-filters', N + 'passage-revision-and-index-audit', N + 'generated-claim-evidence-and-unanswered-state'],
    },
    {
        'path': N + 'multilingual-runbook-search-project',
        'title': 'Project: answer a local-language question from a foreign-language runbook',
        'module': L, 'project': True,
        'summary': 'Retrieve an authorized runbook passage across languages, verify its original wording and return an answer only when the evidence supports it.',
        'sections': [
            ('Define the case', 'A Hindi-speaking operator asks for the rollback limit of gateway-west. The current runbook passage is in English; an older translated note has a different threshold. Keep query and answer language explicit, preserve the service ID and index the runbook by passage revision. The test includes a code-switched question, a restricted appendix and an unrelated gateway-east result. [[natural-language-processing/cross-language-query-document-contract|The request contract]] prevents protected terms from disappearing in a translated candidate.'),
            ('Build judged evidence', 'Annotators mark relevant source spans and exact revision IDs before seeing the system output. Include paraphrased English passages, mixed-script ticket summaries and a passage that quotes an obsolete limit. Group translations and copies by source family so evaluation does not treat them as independent documents. Freeze the judgment set by language pair and service. A reviewer must distinguish relevance to the question from support for a particular numeric answer.'),
            ('Stage search and verification', 'Generate candidates using the raw query, a reviewed translation and a multilingual representation. Enforce access policy before ranking. Deduplicate by canonical passage ID, record which route found each candidate and verify the top evidence against its source-language text. If the source language cannot be verified or the passage is stale, answer with a visible unresolved state. [[natural-language-processing/cross-language-ranking-and-evidence-review|Ranking review]] separates candidate recall from claim support.'),
            ('Gate the release', 'Report recall, first relevant rank, answer support, identifier preservation, stale-passage errors and abstention by language pair. Test the old note and current passage in the same fixture. Release only when a supported answer traces to an authorized current span. The code below checks the final evidence contract; it does not pretend to translate text or decide relevance. [[natural-language-processing/translation-evaluation-and-locale-slices|Locale evaluation]] covers the wording of the final response.'),
        ],
        'code': '''def answer_from_verified_passage(candidate, requested_service,
                                 active_revision, allowed_access):
    if candidate["access_level"] not in allowed_access:
        return {"state": "unanswered", "reason": "access"}
    if candidate["service_id"] != requested_service:
        return {"state": "unanswered", "reason": "service-mismatch"}
    if candidate["revision_id"] != active_revision or not candidate["verified"]:
        return {"state": "unanswered", "reason": "unverified-source"}
    return {"state": "supported", "source_passage_id": candidate["passage_id"],
            "source_language": candidate["language"],
            "answer_value": candidate["reviewed_answer_value"]}

passage = {"passage_id": "runbook-west-82", "language": "en",
           "access_level": "operations", "service_id": "gateway-west",
           "revision_id": "runbook-r8", "verified": True,
           "reviewed_answer_value": "82 minutes"}
assert answer_from_verified_passage(passage, "gateway-west", "runbook-r8",
                                    {"operations"})["answer_value"] == "82 minutes"
assert answer_from_verified_passage(passage, "gateway-east", "runbook-r8",
                                    {"operations"})["state"] == "unanswered"
''',
        'cost': 'The final evidence check is O(1) expected time and space for fixed-size fields and an access set. End-to-end cost includes translation or embedding, candidate retrieval, ranking and human source review. A verified passage does not automatically make every paraphrase of its contents correct; the localized answer still needs claim-level checking.',
        'mistakes': ['Answering from a stale translated note when the source runbook changed.', 'Returning a restricted appendix because it ranked first.', 'Inferring an answer from a passage that merely mentions the service.', 'Hiding uncertainty when no reviewer can verify the source language.'],
        'related': [N + 'cross-language-query-document-contract', N + 'cross-language-ranking-and-evidence-review', N + 'translation-evaluation-and-locale-slices', N + 'runbook-question-answering-project', N + 'passage-revision-and-index-audit'],
    },
    {
        'path': N + 'argument-unit-claim-premise-and-evidence-boundary',
        'title': 'Argument units: claims, premises and evidence spans',
        'module': A, 'project': False,
        'summary': 'Extract what a document argues as typed spans and relations, rather than treating every confident sentence as supported evidence.',
        'sections': [
            ('Choose an annotation unit', 'A change proposal can state “Extend the timeout to 82 minutes,” then cite an incident count as its reason. The recommendation is a claim; the count is a potential premise or evidence span. Record offsets, speaker, document revision and unit type. A sentence can contain more than one unit, while a premise can span sentences. Keep the exact source text so a reviewer can challenge a model’s extraction. [[natural-language-processing/span-offset-annotation|Span contracts]] prevent normalized text from drifting away from the document that was annotated.'),
            ('Separate roles from truth', 'Calling a sentence evidence means that it is offered to support or attack a claim; it does not certify that the statistic is correct. Store the evidence source, measurement window and verification state separately. Likewise, a claim may be quoted by an author who rejects it. Mark attribution and quotation boundaries before assigning the author a stance. [[natural-language-processing/implicit-relations-and-attribution-review|Attribution review]] guards against converting a quoted objection into the proposal owner’s view.'),
            ('Build typed relations', 'Connect premise and claim IDs with support, attack or unresolved links. Do not infer a support edge from proximity alone: “82 incidents occurred” may be a background fact, not a reason for raising a timeout. A relation can cross paragraph boundaries and may depend on a missing assumption. Preserve reviewer rationale and source revision for each edge. [[natural-language-processing/nli-premise-hypothesis-and-evidence-contract|NLI evidence]] tests entailment, while argument relations represent how a writer uses one unit in an argument; those are related but not identical decisions.'),
            ('Audit missing structure', 'Evaluate span boundaries, unit type, relation direction, attribution and evidence verification separately. Include proposals that give no reason, contain competing reasons or cite a disproven metric. A graph with every sentence connected can look complete while inventing support. The [[natural-language-processing/target-specific-stance-and-argument-relations|target stance lesson]] adds the position each speaker takes; the [[natural-language-processing/incident-change-argument-map-project|project]] checks whether a release summary respects the map.'),
        ],
        'code': '''def argument_unit(document_id, revision_id, source_text, start, end,
                  unit_type, speaker_id):
    allowed = {"claim", "premise", "evidence"}
    if unit_type not in allowed or not (0 <= start < end <= len(source_text)):
        raise ValueError("invalid argument span or type")
    if not document_id or not revision_id or not speaker_id:
        raise ValueError("source identity and speaker are required")
    return {"document_id": document_id, "revision_id": revision_id,
            "start": start, "end": end, "text": source_text[start:end],
            "unit_type": unit_type, "speaker_id": speaker_id}

proposal = "Extend the gateway-west timeout to 82 minutes."
unit = argument_unit("change-47", "r3", proposal, 0, len(proposal),
                     "claim", "operator-82")
assert unit["text"] == proposal
assert unit["unit_type"] == "claim"
''',
        'cost': 'Validating the span bounds is O(1); slicing a unit of s characters takes O(s) time and space for the copied text. A real annotation store also needs versioned offsets and relation indexing. This example records an offered role, not factual verification of the unit or automatic discovery of its boundaries.',
        'mistakes': ['Calling an offered statistic verified evidence without checking its source.', 'Assuming one sentence always equals one argument unit.', 'Assigning a quoted objection to the quoting author.', 'Drawing a support edge from sentence proximity alone.'],
        'related': [N + 'target-specific-stance-and-argument-relations', N + 'incident-change-argument-map-project', N + 'span-offset-annotation', N + 'implicit-relations-and-attribution-review', N + 'nli-premise-hypothesis-and-evidence-contract'],
    },
    {
        'path': N + 'target-specific-stance-and-argument-relations',
        'title': 'Target-specific stance and support-or-attack relations',
        'module': A, 'project': False,
        'summary': 'A stance belongs to a speaker, target and time. Represent disagreement explicitly instead of substituting sentiment or treating every objection as opposition to the whole proposal.',
        'sections': [
            ('Bind stance to an explicit target', '“The latency result is good, but the rollback plan is unsafe” has positive language about one result and opposition to a different plan. Store stance toward a specific proposal or claim ID, speaker, source span and time. Labels can include support, oppose, mixed, neutral and unresolved under a documented policy. Sentiment is not a reliable shortcut for stance: criticism of a failure can support a proposed fix. [[natural-language-processing/aspect-sentiment-target-and-negation-policy|Aspect sentiment]] supplies a related target notion but answers a different question.'),
            ('Keep relation direction and scope', 'A premise may attack a subclaim without rejecting the top-level change. Connect typed unit IDs using directed support or attack edges and record which target each edge addresses. Distinguish an author’s own argument from a quoted opponent or hypothetical case. If a sentence names two services, do not transfer its stance from gateway-west to gateway-east. [[natural-language-processing/argument-unit-claim-premise-and-evidence-boundary|Argument units]] establish stable source spans for those relations.'),
            ('Handle disagreement and change', 'Two reviewers may disagree on whether “needs more tests” is opposition or conditional support. Keep the disputed label and rationale rather than manufacturing consensus. A speaker can change position after new incident evidence; time and revision belong in the record. A later support statement should not erase earlier opposition from the audit. [[natural-language-processing/annotation-disagreement-and-label-policy|Disagreement policy]] helps separate unclear writing from inconsistent annotator instructions.'),
            ('Evaluate the map', 'Measure target identification, stance by target, edge precision and attribution errors. Slice by quoted speech, negation, multi-target sentences and implicit premises. Review every proposed support edge that would be used in an automated decision summary. The [[natural-language-processing/incident-change-argument-map-project|project]] gates a change-review summary on a map that identifies who argued for what, why and under which runbook revision.'),
        ],
        'code': '''def record_stance(speaker_id, target_claim_id, stance, source_unit_id,
                  observed_at):
    allowed = {"support", "oppose", "mixed", "neutral", "unresolved"}
    if stance not in allowed:
        raise ValueError("unknown stance")
    if not all((speaker_id, target_claim_id, source_unit_id, observed_at)):
        raise ValueError("stance needs speaker, target, source and time")
    return {"speaker_id": speaker_id, "target_claim_id": target_claim_id,
            "stance": stance, "source_unit_id": source_unit_id,
            "observed_at": observed_at}

latency_view = record_stance("reviewer-47", "latency-claim-82", "support",
                             "unit-91", "2026-09-27T09:00:00Z")
rollback_view = record_stance("reviewer-47", "rollback-claim-82", "oppose",
                              "unit-92", "2026-09-27T09:00:00Z")
assert latency_view["stance"] != rollback_view["stance"]
assert latency_view["target_claim_id"] != rollback_view["target_claim_id"]
''',
        'cost': 'Creating one validated stance record is O(1) time and space for fixed-size references. Building a graph for u units and e relations takes O(u + e) storage and at least O(u + e) ingestion time. The example enforces identity fields; a reviewer must still establish whether the source span expresses the recorded position.',
        'mistakes': ['Using whole-document sentiment as stance on a particular claim.', 'Turning a criticism of one premise into opposition to every proposal.', 'Dropping quotation and speaker attribution.', 'Overwriting an earlier stance when a reviewer changes position later.'],
        'related': [N + 'argument-unit-claim-premise-and-evidence-boundary', N + 'incident-change-argument-map-project', N + 'aspect-sentiment-target-and-negation-policy', N + 'annotation-disagreement-and-label-policy', N + 'claim-conflict-and-temporal-review'],
    },
    {
        'path': N + 'incident-change-argument-map-project',
        'title': 'Project: build a reviewable argument map for an incident change',
        'module': A, 'project': True,
        'summary': 'Extract a proposed operational change, supporting and opposing reasons, target-specific stances and unresolved evidence before writing a release summary.',
        'sections': [
            ('Set the review task', 'A proposal raises gateway-west rollback waiting time to 82 minutes. One operator cites incident counts; another accepts the latency result but disputes the rollback procedure. The review output must not flatten those positions into one positive or negative label. Preserve the proposal revision, speaker turns and exact source spans. [[natural-language-processing/argument-unit-claim-premise-and-evidence-boundary|Argument units]] separate the proposed action from reasons offered for and against it.'),
            ('Annotate the fixture', 'Include a claim, a supporting metric, an objection to a subclaim, a quoted old policy and a later correction. Reviewers tag unit boundaries, relation direction, speaker, target, time and evidence-verification status. Add an ambiguous “needs more testing” note that should remain unresolved. Freeze the annotation policy and adjudicate disagreements before scoring; otherwise the system can appear wrong simply because target scope shifted between reviewers.'),
            ('Construct the map', 'Store nodes as immutable document-revision spans and edges as directed support or attack relations. Keep target-specific stance records separate from evidence truth checks. A cited incident count is not confirmed merely because it supports a claim in the writer’s argument. Check the metric against the underlying incident ledger before a release summary uses it. [[natural-language-processing/target-specific-stance-and-argument-relations|Stance records]] preserve conditional support and explicit opposition.'),
            ('Gate the summary', 'A release summary can include a claim only when its source revision is current, its support relation is reviewable and any numeric evidence it relies on has been verified. Otherwise mark it unresolved and show the reason to the reviewer. Report missed objections, false support edges, attribution mistakes and unsupported numeric claims. The code below checks a tiny final gate; it does not infer argument structure from raw prose. [[natural-language-processing/summary-claim-verification-and-review|Summary verification]] checks the wording after the map is approved.'),
        ],
        'code': '''def releasable_claims(claims, current_revision):
    accepted = []
    held = []
    for claim in claims:
        reasons = []
        if claim["revision_id"] != current_revision:
            reasons.append("stale-revision")
        if not claim["relation_reviewed"]:
            reasons.append("unreviewed-relation")
        if claim["uses_numeric_evidence"] and not claim["evidence_verified"]:
            reasons.append("unverified-number")
        (held if reasons else accepted).append(
            {"claim_id": claim["claim_id"], "reasons": reasons})
    return {"accepted": accepted, "held": held}

claims = [
    {"claim_id": "change-47", "revision_id": "r8",
     "relation_reviewed": True, "uses_numeric_evidence": True,
     "evidence_verified": False},
    {"claim_id": "change-82", "revision_id": "r8",
     "relation_reviewed": True, "uses_numeric_evidence": False,
     "evidence_verified": False},
]
result = releasable_claims(claims, "r8")
assert result["held"] == [{"claim_id": "change-47",
                            "reasons": ["unverified-number"]}]
assert result["accepted"] == [{"claim_id": "change-82", "reasons": []}]
''',
        'cost': 'The final gate scans c claims in O(c) time and uses O(c) space for its returned decisions. Span extraction, relation labeling, evidence checks and adjudication add separate work. A passing gate only says the recorded fields meet the policy; the team must still review whether those fields faithfully describe the source text.',
        'mistakes': ['Equating a cited metric with verified evidence.', 'Summarizing a quoted objection as the proposal owner’s position.', 'Treating support for a latency result as support for the rollback plan.', 'Releasing a claim from an obsolete proposal revision.'],
        'related': [N + 'argument-unit-claim-premise-and-evidence-boundary', N + 'target-specific-stance-and-argument-relations', N + 'summary-claim-verification-and-review', N + 'numeric-claim-calculation-and-evidence', N + 'claim-conflict-and-temporal-review'],
    },
]

crosslinks = [
    (N + 'multilingual-calibration-and-fallback', N + 'cross-language-query-document-contract'),
    (N + 'hybrid-ranking-and-access-filters', N + 'cross-language-ranking-and-evidence-review'),
    (N + 'incident-runbook-search-project', N + 'multilingual-runbook-search-project'),
    (N + 'relation-extraction-provenance', N + 'argument-unit-claim-premise-and-evidence-boundary'),
    (N + 'aspect-sentiment-target-and-negation-policy', N + 'target-specific-stance-and-argument-relations'),
    (N + 'incident-claim-verification-project', N + 'incident-change-argument-map-project'),
]

if __name__ == '__main__':
    publish(lessons, (L, A), crosslinks,
            'aitrove-nlp-crosslingual-arguments-import-20261006.json', 4860,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
