"""Extend NLP with search and source-grounded summarization paths."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
R = 'Semantic retrieval for text collections'
S = 'Source-grounded summarization'

lessons = [
    {
        'path': N + 'text-embedding-pair-and-version-contract',
        'title': 'Text embeddings: pair labels, hard negatives and versioned vectors',
        'module': R, 'project': False,
        'summary': 'A semantic search model learns the retrieval task only when its positive and negative pairs reflect what the user needs, and the stored vectors match the active encoder.',
        'sections': [
            ('Define relevance at the request level', 'Suppose an engineer searches “payment callback received twice” and needs the runbook that explains duplicate delivery. A positive pair is a query with a passage that resolves that request, not merely one containing the same product word. A negative pair is a reviewed non-answer. Record the query, source document revision, passage boundaries, reviewer decision and reason. Multiple passages may be relevant. Avoid assigning every unclicked result a negative label: it might have been unseen, below the fold or withheld by access controls. [[natural-language-processing/corpus-identity-and-label-policy|Corpus identity and label policy]] applies to search judgments too.'),
            ('Mine difficult negatives carefully', 'Random unrelated passages teach very little after the first training stage. Add near-miss negatives: a runbook for a similar callback, a stale version or a passage that mentions the same error code without resolution. Check them with reviewers because a supposedly negative passage may answer the query. Keep documents and near duplicates in one train or test group; otherwise a copied paragraph in both splits inflates retrieval quality. [[natural-language-processing/grouped-temporal-text-validation|Grouped temporal validation]] is the split boundary.'),
            ('Treat vectors as a derived index', 'The stored vector is a function of passage text, chunk policy, normalization, encoder weights and pooling rule. If any changes, rebuild or segregate the index. Mixing old and new embeddings can produce rankings that look plausible but are meaningless. Record the source revision and an encoder digest beside every vector. Keep an index alias that can move atomically after validation, and retain the prior version for rollback. Exact identifiers still need lexical matching; dense similarity alone can miss a rare incident code.'),
            ('Measure retrieval before generation', 'Evaluate recall at a fixed candidate depth, mean reciprocal rank for first useful hit, and failures by query type. Use a time-split audit with queries written after the candidate documents were available. Report “no relevant document” cases separately; forcing a plausible hit is a product error. These measurements feed [[natural-language-processing/hybrid-ranking-and-access-filters|hybrid ranking]] and the [[natural-language-processing/incident-runbook-search-project|runbook project]], while [[retrieval-ai/retrieval-ai-tutorial|retrieval systems]] cover the broader architecture.'),
        ],
        'code': '''from hashlib import sha256

def vector_record(document_id, revision, passage, encoder_digest, embedding):
    if not passage.strip() or not embedding:
        raise ValueError("passage and embedding are required")
    passage_digest = sha256(passage.encode("utf-8")).hexdigest()
    return {"document_id": document_id, "revision": revision,
            "passage_digest": passage_digest, "encoder_digest": encoder_digest,
            "embedding": tuple(float(value) for value in embedding)}

indexed = vector_record("runbook-47", "rev-3", "Retry the callback once.",
                        "encoder-2026-10", [0.31, -0.42, 0.18])
assert indexed["document_id"] == "runbook-47"
''',
        'cost': 'Encoding n passages costs n model calls and stores O(n·d) vector numbers for dimension d, before index overhead. A brute-force query scores O(n·d); an approximate index trades memory and recall for lower query latency. Index rebuilds are batch operations and must finish before the alias moves. Track encoder cost, candidate recall and exact-code misses together, because cheaper vectors can be more expensive if they increase failed searches.',
        'mistakes': ['Treating unclicked results as verified negatives.', 'Mixing embeddings from two encoder versions in one searchable index.', 'Splitting near-duplicate documents between train and audit sets.', 'Reporting only average similarity instead of relevance at a fixed candidate depth.'],
        'related': [N + 'hybrid-ranking-and-access-filters', N + 'incident-runbook-search-project', N + 'grouped-temporal-text-validation', N + 'corpus-identity-and-label-policy', 'retrieval-ai/retrieval-ai-tutorial'],
    },
    {
        'path': N + 'hybrid-ranking-and-access-filters',
        'title': 'Hybrid text ranking with access filters and reranking',
        'module': R, 'project': False,
        'summary': 'Keyword and embedding results solve different failures. Combine them only after access filtering, then rerank candidates against the actual query.',
        'sections': [
            ('Start with the authorized corpus', 'A search service can rank a private incident note perfectly and still be wrong if the requester cannot read it. Apply tenant and document permissions before candidates reach the user or a generation model. If an index cannot enforce prefiltering, verify every candidate against a current authorization source before returning it, and refill from a deeper candidate pool. Postfiltering can reduce recall; log that separately. Never let a cached answer bypass a changed access policy.'),
            ('Keep exact and semantic signals', 'Lexical retrieval handles literal error codes, product names and rare identifiers. Dense retrieval can connect paraphrases, such as “charged twice” with a passage about duplicate capture. Each can fail alone. Fetch a bounded list from both, deduplicate by document revision and passage ID, and combine rank positions rather than raw scores whose scales differ. A reciprocal-rank formula is a straightforward baseline. The rank constant and candidate depth are tuning parameters, not universal numbers. [[natural-language-processing/text-embedding-pair-and-version-contract|Embedding pairs]] determine whether the dense side has learned the task.'),
            ('Rerank a small candidate set', 'A query-passage reranker reads both together and can resolve finer relations than a precomputed vector. Its cost grows with candidate count and text length, so invoke it only on the authorized merged list. Preserve original scores and the reason each passage entered the list for failure review. Truncate carefully: removing the sentence that contains the answer can make a correct candidate look irrelevant. Keep a lexical fallback when the embedding service or reranker times out.'),
            ('Evaluate the whole decision', 'Use reviewed queries with relevant document IDs, allowed user identities and a declared “no answer” state. Report recall at candidate depth before reranking, rank of first useful hit after reranking, access violations, p95 latency and fallback rate. A retrieval change that lifts rank while exposing one unauthorized passage is a failed release. The [[natural-language-processing/incident-runbook-search-project|runbook search project]] makes these checks a deployment gate.'),
        ],
        'code': '''def reciprocal_rank_fusion(lexical_ids, semantic_ids, allowed_ids, rank_constant=47):
    if rank_constant <= 0:
        raise ValueError("rank constant must be positive")
    fused = {}
    for candidate_list in (lexical_ids, semantic_ids):
        seen_in_list = set()
        for rank, document_id in enumerate(candidate_list, start=1):
            if document_id not in allowed_ids or document_id in seen_in_list:
                continue
            seen_in_list.add(document_id)
            fused[document_id] = fused.get(document_id, 0.0) + 1 / (rank_constant + rank)
    return sorted(fused, key=lambda document_id: (-fused[document_id], document_id))

ranked = reciprocal_rank_fusion(["public-47", "private-19"],
                                ["public-47", "public-82"], {"public-47", "public-82"})
assert ranked == ["public-47", "public-82"]
''',
        'cost': 'For l lexical and d dense candidate IDs, fusion is O(l + d + u log u) time for u unique authorized candidates and O(u) space. A cross-encoder reranker adds roughly one model pass per candidate, so cap its list and measure tail latency. Permission checks may dominate if performed one document at a time; batch them without weakening current-user authorization. Refresh authorization on cached results when memberships change.',
        'mistakes': ['Adding raw lexical and cosine scores without calibration.', 'Filtering private passages only after they have entered a generated answer.', 'Treating a high-ranked passage as proof that an answer exists.', 'Ignoring the drop in recall caused by permission filtering or truncation.'],
        'related': [N + 'text-embedding-pair-and-version-contract', N + 'incident-runbook-search-project', 'retrieval-ai/retrieval-ai-tutorial', N + 'text-serving-contract', N + 'grouped-temporal-text-validation'],
    },
    {
        'path': N + 'incident-runbook-search-project',
        'title': 'Project: release an incident-runbook search service',
        'module': R, 'project': True,
        'summary': 'Build a search endpoint that finds a permitted runbook revision, explains ranking failures and refuses to claim an answer when the collection has none.',
        'sections': [
            ('The result contract', 'An on-call engineer searches for a failure symptom and receives a ranked list of passages with document title, revision, owner, last-reviewed time and permission-safe link. Return a no-result state if nothing passes relevance and authorization. A search hit is not an instruction to execute a fix. Preserve the exact query and result IDs for audit, but avoid placing incident secrets into broad telemetry. Decide what freshness means before indexing: a retired runbook should never outrank an active replacement because it has more matching words.'),
            ('Assemble the collection', 'Chunk at document structure boundaries so a passage retains its prerequisite and warning. Give each chunk a stable ID tied to document revision and offsets. Build lexical and dense indexes from the same authorized snapshot, using [[natural-language-processing/text-embedding-pair-and-version-contract|a versioned embedding contract]]. Create reviewed queries from incident tickets after the relevant runbook revision existed. Include literal error codes, paraphrases, stale revisions, no-answer queries and restricted documents. Group duplicated incidents in one split.'),
            ('Rank, filter and test', 'Retrieve bounded lexical and dense candidates, enforce access rights, fuse their ranks and rerank the small merged list. Run permission tests with several user roles, including a user who recently lost access. Compute recall before and after filtering; do not hide a poor index behind a strong reranker. Set release gates for useful-hit rank, no-answer precision, authorization failures and latency. [[natural-language-processing/hybrid-ranking-and-access-filters|Hybrid ranking]] defines the decision sequence.'),
            ('Roll over safely', 'Build the new index under a fresh version, run the same audit queries, and atomically move the alias when checks pass. Keep the previous index for rollback. Record every source deletion and permission change; a delayed index refresh must not expose revoked content. Watch for high no-result rates on a new product line and collect reviewed queries for the next update. The broader [[retrieval-ai/retrieval-ai-tutorial|retrieval learning path]] covers generation after retrieval, but this service should work as search first.'),
        ],
        'code': '''def release_gate(metrics):
    required = {"authorized": True, "candidate_recall_at_20": 0.88,
                "no_answer_precision": 0.81, "p95_ms": 430}
    missing = set(required) - set(metrics)
    if missing:
        raise ValueError(f"missing release metrics: {sorted(missing)}")
    return (metrics["authorized"] is True
            and metrics["candidate_recall_at_20"] >= required["candidate_recall_at_20"]
            and metrics["no_answer_precision"] >= required["no_answer_precision"]
            and metrics["p95_ms"] <= required["p95_ms"])

audit = {"authorized": True, "candidate_recall_at_20": 0.91,
         "no_answer_precision": 0.84, "p95_ms": 396}
assert release_gate(audit)
''',
        'cost': 'Index storage scales with text postings plus O(n·d) vector values for n passages of dimension d. Query latency combines two retrieval calls, batched permission checks and bounded reranking; measure the slowest stage separately. A fixed candidate depth limits cost but may miss relevant text, so publish recall at that exact depth. Reindexing should happen off the serving alias to keep query latency stable.',
        'mistakes': ['Indexing old and new revisions without a freshness rule.', 'Treating a relevant but unauthorized runbook as a successful hit.', 'Moving an alias before no-answer and access tests pass.', 'Claiming a generated fix is grounded solely because search returned a passage.'],
        'related': [N + 'text-embedding-pair-and-version-contract', N + 'hybrid-ranking-and-access-filters', 'retrieval-ai/retrieval-ai-tutorial', N + 'grouped-temporal-text-validation', N + 'document-summary-evidence-contract'],
    },
    {
        'path': N + 'document-summary-evidence-contract',
        'title': 'Document summaries with sentence-level evidence contracts',
        'module': S, 'project': False,
        'summary': 'A fluent summary can insert a false date or owner. Require every operational claim to point back to a source passage and mark unsupported claims for review.',
        'sections': [
            ('Choose the summary job', 'A handoff summary for an incident differs from an abstract for a report. Define audience, maximum length, required fields, prohibited inferences and the source snapshot. For a support handoff, a good contract might require customer impact, confirmed cause, current mitigation and unresolved questions. If a field is absent in source material, write “not recorded” instead of filling it with a likely value. The choice of extractive or generated text follows from this contract, not from a preference for a model family.'),
            ('Attach evidence to claims', 'Split a candidate summary into claims or sentences and associate each with one or more source spans. A claim about a time, count, person or cause needs exact supporting text from the correct revision. A citation marker alone is insufficient if the passage does not entail the statement. Keep source IDs, revision IDs and offsets in the internal representation; render a reader-friendly reference only after validation. [[natural-language-processing/span-offset-annotation|Span offsets]] provide the mechanical link, and [[natural-language-processing/entity-decoding-and-span-evaluation|entity evaluation]] highlights where a single character error can change meaning.'),
            ('Separate coverage from faithfulness', 'A summary can be perfectly faithful yet omit the only action item. Conversely, it can cover every topic while inventing a resolution. Judge both: did the summary include required facts, and are its stated facts supported? Surface contradictions and temporal order separately. Automated similarity metrics are useful screens but cannot alone establish factual support, especially for short numeric changes. Review a stratified sample of summaries and hard cases with a rubric before release.'),
            ('Handle long sources', 'For a long incident log, select relevant windows with timestamps and speaker identity before drafting. Ensure the selected windows include later corrections: an early hypothesis may be explicitly disproved. Preserve the source order so “mitigation attempted” cannot become “mitigation succeeded.” If no window contains enough evidence, abstain or request a human summary. The [[natural-language-processing/summary-claim-verification-and-review|claim verification path]] turns that decision into a check, and the [[natural-language-processing/incident-handoff-summary-project|project]] uses it in a release workflow.'),
        ],
        'code': '''def validate_evidence_spans(source_text, claims):
    checked = []
    for claim in claims:
        supports = claim.get("support_spans", ())
        if not supports:
            raise ValueError("summary claim lacks source evidence")
        for start, end, expected in supports:
            if not 0 <= start < end <= len(source_text):
                raise ValueError("source span is out of range")
            if source_text[start:end] != expected:
                raise ValueError("source evidence changed")
        checked.append(claim["text"])
    return checked

source = "Callback retry completed at 14:47."
assert validate_evidence_spans(source, [{"text": "The retry completed.",
    "support_spans": [(9, 24, "retry completed")]}])
''',
        'cost': 'Span validation takes O(c + total evidence characters) time and O(c) output space for c claims. Model generation is often the dominant cost, especially when long source windows are passed repeatedly. Select windows once, cap input length, and measure how often selection omits a later correction. This mechanical validator confirms that cited text exists; it cannot prove that the claim follows from that text, so human review remains a release gate for consequential summaries.',
        'mistakes': ['Treating fluent wording as evidence of correctness.', 'Accepting any source span as support without checking the claim’s meaning.', 'Summarizing an early hypothesis after a later correction disproved it.', 'Measuring only overlap with a reference summary and missing unsupported claims.'],
        'related': [N + 'summary-claim-verification-and-review', N + 'incident-handoff-summary-project', N + 'span-offset-annotation', N + 'entity-decoding-and-span-evaluation', N + 'text-serving-contract'],
    },
    {
        'path': N + 'summary-claim-verification-and-review',
        'title': 'Verify summary claims, corrections and human-review triggers',
        'module': S, 'project': False,
        'summary': 'A summary checker should catch unsupported claims, changed quantities and superseded statements, while admitting when automated checks cannot decide.',
        'sections': [
            ('Build a claim ledger', 'Represent each sentence as a claim with type, source revision, supporting span and validation status. Numbers, dates, names and causal verbs deserve special attention. Compare extracted values against cited passages, but do not assume identical words prove entailment: “deployment paused” does not mean “deployment failed.” Record a distinct unsupported state rather than silently deleting a claim. [[natural-language-processing/document-summary-evidence-contract|The evidence contract]] defines what each row must carry.'),
            ('Track correction order', 'Operational logs contain revisions. A later entry may reverse an earlier cause, change an impact count or close an action. Keep timestamps and authority of each statement, not just the document order. A summary should identify the latest confirmed state and preserve uncertainty where entries conflict. If the source provides no adjudication, route the claim to a reviewer. This is a temporal interpretation problem, not a string-matching problem.'),
            ('Evaluate the validator itself', 'Create a reviewed audit set with supported, unsupported, contradictory and unanswerable claims. Include entity swaps, date shifts, negation and misleading quotations. Measure false negatives for harmful unsupported claims and false positives that create unnecessary review work. Split by incident and time. An automated entailment score is a candidate signal, not an oracle; measure calibration by claim type before setting a threshold. [[natural-language-processing/classification-slices-and-abstention|Slice evaluation]] and [[natural-language-processing/grouped-temporal-text-validation|grouped validation]] both apply.'),
            ('Make review actionable', 'Return a reason and the exact source window for each flagged claim. A reviewer needs to see whether the evidence is missing, contradicted or merely ambiguous. Keep their correction linked to the candidate and source version. Publish a summary only after all mandatory claims pass the chosen policy; otherwise retain a draft or an extractive fallback. Feed reviewed failures into [[natural-language-processing/incident-handoff-summary-project|the handoff project]], not straight into a training set without label checks.'),
        ],
        'code': '''def claim_release_status(claims, required_claim_types):
    seen = set()
    for claim in claims:
        if claim["status"] != "supported":
            return "manual-review"
        seen.add(claim["type"])
    return "publish" if required_claim_types <= seen else "manual-review"

reviewed_claims = [
    {"type": "impact", "status": "supported"},
    {"type": "mitigation", "status": "supported"},
]
assert claim_release_status(reviewed_claims, {"impact", "mitigation"}) == "publish"
assert claim_release_status(reviewed_claims, {"impact", "cause"}) == "manual-review"
''',
        'cost': 'The gate scans c claims in O(c) time and stores O(t) claim types for t distinct types. Automated claim verification may require a model call per sentence or batch, which can dominate cost and latency. Batch compatible claims, but keep source references separated so evidence cannot cross documents. Monitor review load, false-negative rate for critical fields and drift in source length; each changes the true operating cost.',
        'mistakes': ['Using a lexical match as proof of entailment.', 'Ignoring negation or a later correction in the same source.', 'Letting an unsupported optional sentence pass because mandatory fields exist.', 'Reporting validator accuracy without separating costly false negatives.'],
        'related': [N + 'document-summary-evidence-contract', N + 'incident-handoff-summary-project', N + 'classification-slices-and-abstention', N + 'grouped-temporal-text-validation', N + 'entity-decoding-and-span-evaluation'],
    },
    {
        'path': N + 'incident-handoff-summary-project',
        'title': 'Project: publish evidence-backed incident handoff summaries',
        'module': S, 'project': True,
        'summary': 'Turn an incident timeline into a short handoff that preserves confirmed facts, corrections, open questions and source evidence.',
        'sections': [
            ('The handoff request', 'At shift change, the responder needs confirmed customer impact, current mitigation, owner and the next unresolved action. Set a word budget and a mandatory-field policy. Input can include chat excerpts, ticket updates and a runbook revision. Snapshot the accessible source set at generation time and record which responder may read it. A summary must not reveal a restricted note to someone who can see only the public incident log.'),
            ('Prepare the timeline', 'Normalize event timestamps to one time base while preserving original strings, speaker IDs and document revisions. Mark explicit retractions and corrections. Select windows that include the latest confirmed state, not only the first high-similarity hits. Test on timelines with duplicated updates, contradictory cause guesses, a late rollback and an empty owner field. The previous [[natural-language-processing/incident-runbook-search-project|runbook search project]] can retrieve useful context, but a search hit still needs permission and claim review.'),
            ('Generate and verify', 'Draft a concise structured summary, then split it into claims. Require source offsets for every factual statement and manual review for unsupported, contradictory or missing mandatory fields. Check quantities and dates separately because tiny changes have large operational effects. Compare against an extractive baseline built from confirmed timeline sentences. Record factual support, required-field coverage, review burden and editing time. [[natural-language-processing/document-summary-evidence-contract|The evidence contract]] and [[natural-language-processing/summary-claim-verification-and-review|claim review]] define the gates.'),
            ('Release with a rollback path', 'Publish only a reviewed revision with a source snapshot digest. When an incident update invalidates the summary, mark it stale and generate a new draft; do not quietly mutate a signed-off handoff. The recipient should see freshness and unresolved questions. Restrict raw source snippets in logs, and retain the prior signed-off revision for audit. A model upgrade must replay the hard timeline set before it replaces the current bundle.'),
        ],
        'code': '''from hashlib import sha256

def handoff_record(incident_id, source_revisions, claims, required_types):
    if not source_revisions or not required_types:
        raise ValueError("source revisions and required types are mandatory")
    if any(claim["status"] != "supported" for claim in claims):
        return {"incident_id": incident_id, "status": "manual-review"}
    observed = {claim["type"] for claim in claims}
    if not required_types <= observed:
        return {"incident_id": incident_id, "status": "manual-review"}
    manifest = "|".join(sorted(source_revisions)).encode("utf-8")
    return {"incident_id": incident_id, "status": "ready-for-signoff",
            "source_digest": sha256(manifest).hexdigest()}

handoff = handoff_record("incident-47", ["timeline-v4", "runbook-v7"],
                         [{"type": "impact", "status": "supported"}], {"impact"})
assert handoff["status"] == "ready-for-signoff"
''',
        'cost': 'The local gate is O(c + r log r) time for c claims and r revision identifiers, with O(r) manifest space. Reading, selecting and generating over long timelines is far more expensive; measure p95 processing time and human signoff time separately. A source digest proves which revision IDs were declared, not that the content is faithful. Keep versioned source snapshots and a manual signoff trail for the actual factual check.',
        'mistakes': ['Treating “ready for signoff” as automatic publication.', 'Losing a later correction while shortening the source window.', 'Allowing a restricted runbook passage into a widely visible summary.', 'Updating a signed-off handoff without a new revision and review.'],
        'related': [N + 'document-summary-evidence-contract', N + 'summary-claim-verification-and-review', N + 'incident-runbook-search-project', N + 'text-serving-contract', N + 'ticket-routing-project'],
    },
]

crosslinks = [
    (N + 'corpus-identity-and-label-policy', N + 'text-embedding-pair-and-version-contract'),
    (N + 'grouped-temporal-text-validation', N + 'text-embedding-pair-and-version-contract'),
    (N + 'text-serving-contract', N + 'hybrid-ranking-and-access-filters'),
    (N + 'span-offset-annotation', N + 'document-summary-evidence-contract'),
    (N + 'classification-slices-and-abstention', N + 'summary-claim-verification-and-review'),
    (N + 'text-embedding-pair-and-version-contract', N + 'hybrid-ranking-and-access-filters'),
    (N + 'hybrid-ranking-and-access-filters', N + 'incident-runbook-search-project'),
    (N + 'document-summary-evidence-contract', N + 'summary-claim-verification-and-review'),
    (N + 'summary-claim-verification-and-review', N + 'incident-handoff-summary-project'),
    (N + 'incident-runbook-search-project', N + 'incident-handoff-summary-project'),
]

if __name__ == '__main__':
    publish(lessons, (R, S), crosslinks,
            'aitrove-nlp-retrieval-summarization-import-20261006.json', 4710,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
