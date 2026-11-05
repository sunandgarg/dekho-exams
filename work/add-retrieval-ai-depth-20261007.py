"""Add original Retrieval AI lessons and a small publication packet."""
import datetime
import html
import json
from pathlib import Path
import re
import uuid

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "src/data/fixtures.json"
OUTPUT = ROOT / "work/aitrove-retrieval-ai-depth-import-20261007.json"
rows = json.loads(FIXTURE.read_text())
by_path = {row["path"]: row for row in rows}
assert len(by_path) == len(rows)
stamp = datetime.datetime.now(datetime.UTC).isoformat()
R = "retrieval-ai/"
HUB = R + "retrieval-ai-tutorial"
PROJECT_HUB = HUB + "/project"

lessons = [
    dict(
        slug="query-intent-and-retrieval-routing",
        title="Retrieval query routing: preserve exact constraints before search",
        summary="Route identifiers, policy questions and aggregate requests to the right evidence path without rewriting away the user's constraints.",
        sections=[
            ("Classify the request before reformulation", "A question containing case ID AX-47 and an exact error string needs a literal lookup; a paraphrase of a policy may need semantic retrieval. A count of cases by week belongs to a governed query over structured data. Treat these as different jobs. Extract the requested output, exact tokens, tenant scope and time boundary first. A reformulator may add synonyms, but it cannot replace AX-47 with a more common case or turn a count into a prose summary. [[retrieval-ai/retrieval-recall-and-reranking|Candidate retrieval]] starts after this contract is fixed."),
            ("Keep routing observable", "Record the selected path and the reason: exact ID, natural-language passage, structured aggregation, or mixed evidence. Run lexical and semantic search in parallel for mixed requests, then merge permitted candidates. A vector match can help find related language, but it cannot establish that a literal identifier was present. If a required identifier is absent from the result, reject that candidate even when its embedding score is high. A SQL query must use an approved metric definition; generated SQL is not a substitute for permission checks."),
            ("Handle ambiguous follow-ups", "For ‘What changed after that?’, resolve ‘that’ from the current conversation only when a single permitted document identity is clear. Carry the resolved ID, revision and time window into the new query. If two incidents were discussed, ask which one the user means. Never copy a previous user's context or a past authorization decision into a new session. [[retrieval-ai/permission-aware-cache-and-conversation-turns|Conversation boundaries]] need the same rigor as document permissions."),
            ("Evaluate the router as a component", "Create a labeled set with identifiers, paraphrases, mixed questions, unsupported aggregates and ambiguous follow-ups. Count wrong-route decisions separately from search misses. An exact-search route can fail because the identifier was parsed incorrectly; a semantic route can fail because its candidate pool omitted the answer. Store the original query beside the routed form so reviewers can see what changed. Include at least one question where no source is eligible and require the no-answer path."),
        ],
        code='''def route_support_query(question: str, case_ids: set[str]) -> dict[str, object]:
    import re
    requested_ids = set(re.findall(r"\\bAX-\\d+\\b", question.upper()))
    unknown_ids = requested_ids - case_ids
    if unknown_ids:
        return {"route": "no_match", "ids": sorted(unknown_ids)}
    if re.search(r"\\b(count|how many|per week)\\b", question.lower()):
        return {"route": "aggregate", "ids": sorted(requested_ids)}
    if requested_ids:
        return {"route": "hybrid_exact_first", "ids": sorted(requested_ids)}
    return {"route": "semantic", "ids": []}

known_cases = {"AX-47", "AX-63"}
assert route_support_query("Why did AX-47 retry?", known_cases)["route"] == "hybrid_exact_first"
assert route_support_query("Count AX-63 cases per week", known_cases)["route"] == "aggregate"
assert route_support_query("Explain AX-91", known_cases)["route"] == "no_match"''',
        cost="Routing costs O(q + m) time for query length q and m extracted IDs in this small example. The expensive work is downstream: two search legs, an aggregation or a clarification turn. Log wrong-route rates by query family and cap simultaneous searches; a cheap router that silently drops an exact constraint wastes the entire answer pipeline.",
        mistakes=["Treating an embedding score as proof of an exact case-ID match.", "Rewriting a user-specified date or identifier without retaining the original constraint.", "Sending an aggregate question to passage search and inventing a count from snippets.", "Resolving an ambiguous follow-up from a different session."],
        drill="Build 47 labeled queries: 12 exact IDs, 12 paraphrases, 11 mixed requests, six aggregates and six ambiguous follow-ups. Report route accuracy for each family and inspect every false route before changing a threshold.",
        related=[R + "hybrid-search-and-reciprocal-rank-fusion", R + "permission-aware-cache-and-conversation-turns", R + "retrieval-recall-and-reranking", "natural-language-processing/retrieval-positive-pair-identity-and-revision"],
    ),
    dict(
        slug="source-extraction-and-passage-provenance",
        title="Document extraction: preserve passage provenance through OCR and parsing",
        summary="Turn source files into searchable passages while retaining the page, section, revision and extraction quality needed to verify an answer.",
        sections=[
            ("Define the extracted record", "A text string alone is not a source. Each passage needs document ID, immutable revision ID, page or section, span offsets when available, extraction method, language and access label. A PDF policy may contain a scanned page, two-column layout and a table whose cells change meaning when read in the wrong order. Store the source file hash and parser version so a changed extraction can be rebuilt without pretending the document itself changed. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Corpus identity]] is the parent contract."),
            ("Separate clean text from uncertain text", "Parse machine-readable text first. Route image-only pages to OCR, and mark uncertain spans rather than silently normalizing them into authoritative policy. A table value of 47 under ‘hours’ is different from 47 under ‘days’; flattening the headers can invert a support rule. Keep table headers with row text or represent the table as structured cells. Human review should focus on low-confidence pages that answer high-impact questions, not every document equally."),
            ("Retain location through cleanup", "Whitespace normalization, header removal and dehyphenation can improve search. They also shift character offsets. Maintain a map from cleaned spans back to source-page coordinates or stable section IDs. When the answer cites a passage, the reader should land on the source location that actually supports the claim. If an OCR run changes, rebuild the chunk IDs and invalidate answers tied to old offsets. [[retrieval-ai/claim-level-citation-and-support-checks|Citation integrity]] depends on this map."),
            ("Gate ingestion with concrete failures", "Feed the parser a missing page, duplicate footer, rotated scan, repeated table header and an inaccessible file. Reject a document if its required metadata or access label is absent. Record page count, extracted character count, empty pages and confidence distribution. A parser yielding text is not evidence that it preserved meaning. Compare a reviewed sample of passages against the original page, especially around headings, tables and footnotes."),
        ],
        code='''from dataclasses import dataclass
from hashlib import sha256

@dataclass(frozen=True)
class ExtractedPassage:
    document_id: str
    revision_id: str
    page: int
    section: str
    text: str
    source_sha256: str

def passage_record(document_id: str, revision_id: str, page: int,
                   section: str, text: str, source_bytes: bytes) -> ExtractedPassage:
    if page < 1 or not document_id or not revision_id or not section or not text.strip():
        raise ValueError("incomplete extraction provenance")
    return ExtractedPassage(document_id, revision_id, page, section,
                            text.strip(), sha256(source_bytes).hexdigest())

source = b"Policy r8 page 4"
passage = passage_record("refund-policy", "r8", 4, "Exceptions", " 47 hours ", source)
assert passage.page == 4 and passage.text == "47 hours"
assert passage.source_sha256 == sha256(source).hexdigest()''',
        cost="Extraction is O(B) in source bytes before OCR; OCR cost also depends on page count and resolution. Provenance adds small metadata per passage, while page images and offset maps add storage. Budget retries by document, not an unbounded queue. Measure empty-page rate and reviewed semantic errors separately from parser throughput.",
        mistakes=["Treating OCR output as exact text without a confidence or review path.", "Dropping table headers or section titles before chunking.", "Reusing offsets after normalization changes the text.", "Indexing a passage when its access label or revision is missing."],
        drill="Extract a 23-page policy with a two-column page, one rotated scan and a table. Check five answer-bearing passages against their original page and record which parser change would invalidate each citation.",
        related=[R + "chunk-identity-and-context-boundaries", R + "claim-level-citation-and-support-checks", R + "corpus-permissions-and-document-lifecycle", "natural-language-processing/long-document-evidence-index-and-coverage"],
    ),
    dict(
        slug="embedding-space-version-and-migration",
        title="Embedding migrations: keep query and document vectors in one space",
        summary="Version embedding models, dimensions and normalization rules as one index contract, then cut over only after query parity checks.",
        sections=[
            ("Record the vector contract", "An embedding is meaningful only relative to the model and preprocessing that produced it. Store model ID, revision, vector dimension, distance metric, text normalization and any title-prefix policy beside each index generation. A query vector from model B must not be compared to document vectors from model A merely because both have 768 coordinates. Even identical dimensions do not imply shared geometry. [[machine-learning/embedding-retrieval-recall-and-collapse|Embedding diagnostics]] belong before promotion."),
            ("Build a separate generation", "Create a new index rather than overwriting old vectors in place. Re-embed every active, permitted document revision; index tombstones and access metadata at the same time. Reject vectors with non-finite values, wrong dimensions or an empty source span. Keep the old index available while the new one is validated. If the model changes its tokenizer or input prefix, capture that too; a silent query-side change can look like an index outage."),
            ("Compare on the same judgments", "Run a frozen query set against old and candidate indexes with the same permission snapshot. Report recall at the candidate cutoff, first relevant rank, exact-ID failures and latency by query family. A higher average similarity is not evidence of better retrieval because score scales move with models. Inspect newly missed answer-bearing passages, especially minority languages and long documents. [[retrieval-ai/retrieval-release-evaluation-and-slice-gates|Release gates]] turn this comparison into a decision."),
            ("Switch and recover", "Point readers to one versioned alias only after the candidate is complete and validated. Include the generation ID in result metadata and cache keys. Keep the previous alias target for a rollback window, then retire it under the corpus deletion policy. A rollback must restore matching query encoder and document index together. A mixed pair can return plausible neighbors while quietly losing relevant evidence."),
        ],
        code='''from dataclasses import dataclass
from math import isfinite

@dataclass(frozen=True)
class VectorContract:
    model_revision: str
    dimensions: int
    metric: str

def accept_vector(values: list[float], query_contract: VectorContract,
                  index_contract: VectorContract) -> tuple[float, ...]:
    if query_contract != index_contract:
        raise ValueError("query and index vector contracts differ")
    if len(values) != index_contract.dimensions or not all(map(isfinite, values)):
        raise ValueError("invalid vector")
    return tuple(values)

active = VectorContract("receipt-embed-r8", 3, "cosine")
assert accept_vector([0.2, 0.4, 0.8], active, active) == (0.2, 0.4, 0.8)
try:
    accept_vector([0.2, 0.4, 0.8], VectorContract("receipt-embed-r9", 3, "cosine"), active)
except ValueError:
    pass
else:
    raise AssertionError("mixed embedding generations were accepted")''',
        cost="Validating one d-dimensional vector takes O(d) time and O(d) output space here. Re-embedding N passages costs N model calls plus index construction and temporarily doubles vector storage during overlap. Migration planning should include that peak, query encoder rollout, cache invalidation and a measured rollback window.",
        mistakes=["Assuming equal vector dimensions imply compatible embedding spaces.", "Replacing document vectors before deploying the matching query encoder.", "Comparing raw similarity scores across model versions as if they shared a scale.", "Deleting the previous generation before rollback and permission tests pass."],
        drill="Take 83 judged queries with identifier, paraphrase and multilingual slices. Build a candidate index under a new model revision, verify dimension and access metadata, then record recall and latency deltas before moving the alias.",
        related=[R + "filtered-ann-recall-and-latency", R + "retrieval-release-evaluation-and-slice-gates", R + "freshness-deletion-and-index-swap", "machine-learning/embedding-retrieval-recall-and-collapse"],
    ),
    dict(
        slug="filtered-ann-recall-and-latency",
        title="Filtered vector search: measure ANN recall inside the permitted set",
        summary="Approximate nearest-neighbor speed is useful only if access filters and candidate limits still surface relevant permitted passages.",
        sections=[
            ("Name the reference set", "Approximate nearest-neighbor search trades some exact-neighbor recall for latency and memory behavior. Evaluate it against an exact search over the same eligible documents, query embedding and distance metric. If the exact baseline includes another tenant's records, its recall number is meaningless for a permission-filtered product. Apply tenant, revision and document-state filters before ranking, or use an index layout whose filtering semantics are proven. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Access policy]] is a hard eligibility rule."),
            ("Test selective filters", "A broad tenant with millions of passages and a small tenant with 47 passages may exercise different search paths. Some engines prefilter the graph; others use postfiltering or adaptive methods. Postfiltering the global top K can return zero permitted results even when a perfect permitted answer exists just outside K. Ask the engine what it actually does, then test the behavior. A filter that removes forbidden hits after they have already entered prompt assembly is too late."),
            ("Separate relevance from system recall", "Measure exact top-K overlap to quantify approximation loss, then judge whether answer-bearing passages remain in the candidate pool. A candidate can differ from the exact top K yet still answer the question; conversely, excellent vector overlap can miss a literal error code. Compare by tenant size, filter selectivity, language and document length. [[retrieval-ai/hybrid-search-and-reciprocal-rank-fusion|Hybrid retrieval]] can recover some exact-token cases but is not a repair for access leakage."),
            ("Set a latency budget with an exit", "Tune search breadth and K on a fixed judged set while measuring p50 and p95 latency. Keep a limit on vector comparisons, rerank candidates and total response time. When filtered ANN returns too few candidates, a bounded exact fallback may be reasonable for a small eligible set. Do not retry forever with a larger global K: that raises cost and can still miss the allowed island. Record when fallback runs, so an index regression is not hidden by the safety net."),
        ],
        code='''def recall_at_k(returned_ids: list[str], exact_ids: list[str], k: int) -> float:
    if k < 1 or len(exact_ids) < k:
        raise ValueError("invalid recall cutoff")
    permitted_reference = set(exact_ids[:k])
    return len(set(returned_ids[:k]) & permitted_reference) / k

exact_permitted = ["west-r8-p4", "west-r8-p9", "west-r8-p2"]
ann_permitted = ["west-r8-p4", "west-r8-p2", "west-r8-p11"]
assert recall_at_k(ann_permitted, exact_permitted, 3) == 2 / 3

def allowed_candidates(candidates: list[dict], tenant_id: str) -> list[dict]:
    return [passage for passage in candidates if passage["tenant_id"] == tenant_id
            and passage["state"] == "active"]

assert allowed_candidates([{"tenant_id": "west", "state": "active"},
                           {"tenant_id": "east", "state": "active"}], "west") == [
                               {"tenant_id": "west", "state": "active"}]''',
        cost="An exact scan costs O(Nd) distance work for N eligible d-dimensional vectors; an ANN index aims to reduce query work but adds build time, memory and tuning. The filter check shown costs O(K) over returned candidates and does not replace index-side authorization. Report recall and latency together at the production filter distribution.",
        mistakes=["Computing ANN recall against a reference set that includes forbidden documents.", "Postfiltering only the global top K and calling an empty result a true no-answer.", "Treating vector-neighbor overlap as answer-bearing passage recall.", "Using an unbounded retry or exact fallback on a large tenant."],
        drill="Create a large and a small tenant with overlapping language. Compare exact and ANN top-8 within each tenant, then revoke one document and prove it cannot appear in candidates, reranker inputs or citations.",
        related=[R + "embedding-space-version-and-migration", R + "hybrid-search-and-reciprocal-rank-fusion", R + "retrieval-release-evaluation-and-slice-gates", "deep-learning/retrieval-index-version-and-candidate-parity"],
    ),
    dict(
        slug="hybrid-search-and-reciprocal-rank-fusion",
        title="Hybrid retrieval: fuse exact terms and semantic candidates by rank",
        summary="Run lexical and vector retrieval over the same permitted revision set, then fuse ranks without pretending their raw scores are comparable.",
        sections=[
            ("Keep both candidate paths honest", "A user may ask for a named status code and its meaning in different words. Keyword search protects exact strings, version tags and identifiers; dense retrieval helps with paraphrases. Each leg must apply the same tenant, document-state and revision constraints before its results reach fusion. If one leg indexes stale policy or ignores a revocation, its high rank cannot be made safe by later scoring. [[retrieval-ai/filtered-ann-recall-and-latency|Filtered ANN]] tests the semantic leg independently."),
            ("Fuse ranks, then inspect the result", "Reciprocal rank fusion awards a candidate one divided by a rank constant plus its position in each list. A passage appearing in both lists receives contributions from both. This avoids adding an unbounded keyword score to a cosine similarity on a different scale. It discards score margins, so a clear lexical winner and a weak lexical hit can be treated as neighboring ranks. Compare fusion against each leg on judged questions, particularly exact-ID queries."),
            ("Preserve identity while deduplicating", "The key is a stable passage identity tied to document revision, not only display text. Two copied sections from different policies may have identical wording but different owners or effective dates. Deduplicate the same passage returned by both legs, then group near-duplicates for context selection rather than erasing provenance. [[retrieval-ai/context-packing-and-evidence-diversity|Evidence packing]] decides how many passages from one document belong in the prompt."),
            ("Tune the window, not the formula alone", "Each leg contributes only the candidates it retrieved. A fusion constant cannot recover a passage absent from both top-K lists. Measure candidate recall while changing lexical depth, vector depth and fusion constant; track p95 latency and reranker input size. If exact identifiers are mandatory, apply a hard exact-match gate before or after fusion according to the query contract, not an arbitrary score threshold on the fused rank."),
        ],
        code='''from collections import defaultdict

def reciprocal_rank_fusion(lexical: list[str], semantic: list[str],
                           rank_constant: int = 37) -> list[str]:
    if rank_constant < 1:
        raise ValueError("rank constant must be positive")
    scores = defaultdict(float)
    for ranking in (lexical, semantic):
        for position, passage_id in enumerate(dict.fromkeys(ranking), start=1):
            scores[passage_id] += 1 / (rank_constant + position)
    return sorted(scores, key=lambda passage_id: (-scores[passage_id], passage_id))

keyword_hits = ["policy-r8-ax47", "policy-r8-refunds", "guide-r3"]
vector_hits = ["policy-r8-refunds", "policy-r8-ax47", "manual-r6"]
ranking = reciprocal_rank_fusion(keyword_hits, vector_hits)
assert ranking[:2] == ["policy-r8-ax47", "policy-r8-refunds"]
assert len(ranking) == 4''',
        cost="Fusion scans L + V ranked candidates and stores at most their union, so expected O(L + V) score work and O(U) memory, followed by O(U log U) sorting. It adds almost no model cost, while running two retrieval legs may double search traffic. Bound both depths and measure whether extra recall justifies their latency.",
        mistakes=["Adding raw keyword and vector scores without a tested normalization rule.", "Fusing candidates from different permission or index generations.", "Deduplicating by text and losing document ownership or revision.", "Tuning the fusion constant while the needed passage never enters either list."],
        drill="Judge 63 queries split across exact identifiers, paraphrases and mixed language. Compare keyword-only, vector-only and fused recall at 12; record the extra latency and every newly missed exact-token query.",
        related=[R + "query-intent-and-retrieval-routing", R + "reranker-candidate-window-and-budget", R + "context-packing-and-evidence-diversity", R + "retrieval-recall-and-reranking"],
    ),
]

lessons.extend([
    dict(
        slug="reranker-candidate-window-and-budget",
        title="Reranking: spend model budget on a bounded candidate window",
        summary="Rerank a diverse, permitted candidate set and measure whether the added cost moves answer-bearing passages into view.",
        sections=[
            ("Find before sorting", "A reranker can reorder candidates; it cannot recover an answer omitted by first-stage search. Freeze a judged set and measure candidate recall at the exact window passed to the reranker. Include identifiers, paraphrases, negative questions and long documents. If recall is weak, repair routing before paying for a bigger ranker. [[retrieval-ai/hybrid-search-and-reciprocal-rank-fusion|Hybrid retrieval]] can supply a stronger starting window."),
            ("Budget the input", "Set a maximum candidate count, passage length and total scoring budget. A 47-passage window at 1,400 tokens each can cost more than the final answer. Truncate at sentence or section boundaries while retaining title and source identity. Test long queries and the largest eligible tenant. On timeout, fall back to first-stage order with a degraded-mode signal; do not disguise a timeout as no evidence."),
            ("Keep eligibility outside the model", "Filter access, active revision and deletion state before scoring. A reranker should never see forbidden material, even if final selection would discard it. A high relevance score says nothing about truth, freshness or permission. Winning passages still need [[retrieval-ai/claim-level-citation-and-support-checks|claim support checks]]."),
            ("Measure rank movement", "Track first relevant rank, context-cutoff recall and answer support with and without reranking. Report by query family; a ranker may improve paraphrases while pushing exact IDs down. Retain candidate IDs, truncation details and model revision so regressions can be reproduced."),
        ],
        code='''def bounded_rerank_window(candidates: list[dict], tenant_id: str,
                          limit: int = 12) -> list[dict]:
    if limit < 1:
        raise ValueError("candidate limit must be positive")
    selected, seen = [], set()
    for passage in candidates:
        if passage["tenant_id"] != tenant_id or passage["state"] != "active":
            continue
        identity = (passage["document_id"], passage["revision_id"], passage["span_id"])
        if identity not in seen:
            selected.append(passage)
            seen.add(identity)
        if len(selected) == limit:
            break
    return selected

candidate = {"tenant_id": "west", "state": "active", "document_id": "policy",
             "revision_id": "r8", "span_id": "p4"}
assert bounded_rerank_window([candidate, candidate, {**candidate, "tenant_id": "east"}],
                             "west", 2) == [candidate]''',
        cost="Selecting K eligible passages from N candidates takes O(N) time and O(K) space. Pairwise reranking costs roughly one model evaluation per candidate, so compute grows with K and passage length. Cap both, measure p95, and separate first-stage recall from reranker gain.",
        mistakes=["Increasing the reranker window when the answer is absent from all first-stage hits.", "Scoring a forbidden passage before access filtering.", "Truncating away the sentence that carries the answer.", "Calling a timeout fallback a successful rerank."],
        drill="Use 91 judged questions. Compare first-stage and reranked first relevant rank at windows of 8, 16 and 32; record p95 latency and exact-ID regressions before choosing a window.",
        related=[R + "hybrid-search-and-reciprocal-rank-fusion", R + "context-packing-and-evidence-diversity", R + "retrieval-release-evaluation-and-slice-gates", R + "retrieval-recall-and-reranking"],
    ),
    dict(
        slug="context-packing-and-evidence-diversity",
        title="Context packing: retain independent evidence under a token cap",
        summary="Select passages by answer coverage, document diversity and provenance instead of filling the prompt with near-duplicates.",
        sections=[
            ("Reserve the evidence budget", "Allocate tokens for instructions, question, response and citations before retrieved text. Each passage needs title, revision, section and citation identity. A long high-ranked section can crowd out a short exception that changes the answer. Pack by paragraphs or table rows, not a cut through a condition. [[retrieval-ai/chunk-identity-and-context-boundaries|Chunk boundaries]] determine what can be selected intact."),
            ("Prevent one revision from monopolizing context", "Near-duplicate chunks often rank together. Limit repeated passages from one revision unless the question needs several clauses. Prefer a second independent source when it adds a missing fact, but do not force diversity at the cost of the sole answer-bearing span. Deduplicate the same passage identity across lexical and vector legs; copied text in separate revisions retains separate provenance."),
            ("Preserve contradictions", "When permitted sources disagree, packing must not hide the newer statement just because it ranked lower. Include effective dates and revision labels so the answer can explain the conflict or abstain. Test exceptions, date boundaries and footnotes. Packet quality is whether it contains every fact needed, not its average similarity score."),
            ("Inspect the packet actually sent", "Store candidate IDs, included IDs, exclusions and token counts. Compare generated claims with this exact packet, not the entire index. If support is absent, a fluent answer still fails. [[retrieval-ai/claim-level-citation-and-support-checks|Claim checks]] decide whether to cite, revise or abstain."),
        ],
        code='''def pack_passages(candidates: list[dict], token_budget: int,
                  per_revision_limit: int = 2) -> list[dict]:
    if token_budget < 1 or per_revision_limit < 1:
        raise ValueError("positive limits required")
    selected, spent, per_revision = [], 0, {}
    for passage in candidates:
        revision = (passage["document_id"], passage["revision_id"])
        if per_revision.get(revision, 0) >= per_revision_limit:
            continue
        if spent + passage["tokens"] > token_budget:
            continue
        selected.append(passage)
        spent += passage["tokens"]
        per_revision[revision] = per_revision.get(revision, 0) + 1
    return selected

ranked = [{"document_id": "policy", "revision_id": "r8", "tokens": 33},
          {"document_id": "policy", "revision_id": "r8", "tokens": 41},
          {"document_id": "faq", "revision_id": "r3", "tokens": 29}]
packet = pack_passages(ranked, 67, 1)
assert len(packet) == 2 and sum(p["tokens"] for p in packet) == 62''',
        cost="This bounded pass costs O(K) time and O(D) counters for K candidates and D revisions. Tokenization and model context cost dominate. Greedy packing can miss a better combination; add measured coverage-aware selection only if judged queries expose that ceiling.",
        mistakes=["Spending the whole context window on passages and leaving no response budget.", "Suppressing a newer contradiction because its score is lower.", "Confusing duplicate text with duplicate source identity.", "Citing a passage that was retrieved but not included in the final packet."],
        drill="For 37 questions, label required facts and revisions. Pack under a 540-token evidence budget and measure how often all facts survive, especially exceptions and conflicts.",
        related=[R + "reranker-candidate-window-and-budget", R + "claim-level-citation-and-support-checks", R + "chunk-identity-and-context-boundaries", "prompt-engineering/retrieval-context-packet-coverage-and-claim-mapping"],
    ),
    dict(
        slug="claim-level-citation-and-support-checks",
        title="Claim-level citations: verify each answer against its passage",
        summary="Bind each factual claim to a permitted, current passage and reject citations that are merely related to the topic.",
        sections=[
            ("Split answers into testable claims", "‘Refunds arrive in 47 hours and managers can extend the window’ contains two claims. Each needs support from the selected evidence packet. A policy-title citation is too broad when its quoted span states only the first clause. Keep claim and passage IDs together. Distinguish direct support, contradiction, insufficient evidence and facts supplied by the user. [[retrieval-ai/evidence-bound-answer-and-abstention|Abstention]] is correct when a required claim lacks support."),
            ("Check passage identity", "The cited span must belong to an active permitted revision and have been included in the generator context. Resolve it to a readable page or section. A valid-looking ID for a retired revision is insufficient. [[retrieval-ai/source-extraction-and-passage-provenance|Extraction provenance]] supplies the source location."),
            ("Test support rather than overlap", "A passage about refund windows may omit the 47-hour value. ‘Up to 47 hours’ does not justify ‘always within 47 hours.’ Numbers, negation, dates and exceptions deserve explicit checks. An entailment model can triage cases, but its confidence alone does not prove support; keep a human-judged sample."),
            ("Fail clearly", "Remove or qualify unsupported claims and regenerate from the same permitted packet. If the core question remains unanswered, state which part cannot be verified. Log the unsupported claim and citation ID without putting private source text in public telemetry. Count unsupported-claim rate separately from retrieval misses."),
        ],
        code='''def validate_claim_citations(claims: list[dict], packet_ids: set[str],
                             active_ids: set[str]) -> list[str]:
    failures = []
    for claim in claims:
        cited = set(claim["citations"])
        if not cited or not cited <= packet_ids or not cited <= active_ids:
            failures.append(claim["claim_id"])
        elif claim["support"] != "supported":
            failures.append(claim["claim_id"])
    return failures

claims = [{"claim_id": "hours", "citations": ["policy-r8-p4"], "support": "supported"},
          {"claim_id": "extension", "citations": ["policy-r8-p4"], "support": "insufficient"}]
assert validate_claim_citations(claims, {"policy-r8-p4"}, {"policy-r8-p4"}) == ["extension"]''',
        cost="Identity checking takes O(C + E) expected time for C claims and E citation edges, with O(C) failure output. Semantic support review is costlier and may need model calls or human adjudication. Sample high-impact claims first; do not hide unsupported claims in an average answer score.",
        mistakes=["Accepting a citation because its document title matches the topic.", "Using a retired passage or one absent from the final context packet.", "Treating ‘up to’ and ‘always’ as equivalent.", "Reporting retrieval recall as proof of answer support."],
        drill="Write 29 answers with a numeric claim, an exception and a distractor citation each. Mark support from the exact packet and count unsupported claims that survive automation.",
        related=[R + "source-extraction-and-passage-provenance", R + "evidence-bound-answer-and-abstention", R + "retrieval-vs-answer-evaluation", R + "context-packing-and-evidence-diversity"],
    ),
])

lessons.extend([
    dict(
        slug="permission-aware-cache-and-conversation-turns",
        title="Retrieval caches and conversation turns: recheck access every time",
        summary="Prevent cached evidence and follow-up questions from crossing tenant, principal or document-revision boundaries.",
        sections=[
            ("Key on authorization context", "A cache entry keyed by query text alone is unsafe. Include tenant, principal or authorization scope, policy version, corpus generation, query normalization and retrieval configuration. Even then, a revoked document can invalidate an old answer before TTL expires. Revalidate cached passage IDs against current access and deletion state, or invalidate them on revocation. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Document lifecycle]] defines the invalidation event."),
            ("Carry resolved conversation state", "A follow-up like ‘What about the other case?’ needs a specific, permitted antecedent. Store document and revision IDs, not an indiscriminate replay of previous passages. Recheck access before reuse. If two antecedents fit, ask for clarification. A conversation ID is not an authorization token; shared browser sessions and role changes expose that mistake."),
            ("Separate candidate and answer caches", "Cached candidates depend on index generation, access scope and search configuration. A cached final answer also depends on the prompt, model, evidence packet and answer policy. Give these caches separate lifetimes. Never serve a final answer whose citations no longer resolve, and avoid storing user secrets in a shared cache."),
            ("Prove revocation works", "Test identical query text from two tenants, role change mid-session, document deletion and index swap. Each must produce only a newly permitted answer or an explicit no-answer. Log cache hit, authorization recheck and corpus generation without private text in metric labels. [[retrieval-ai/freshness-deletion-and-index-swap|Index swaps]] need matching invalidation."),
        ],
        code='''from hashlib import sha256

def retrieval_cache_key(tenant_id: str, principal_id: str, policy_revision: str,
                        corpus_generation: str, query: str) -> str:
    fields = (tenant_id, principal_id, policy_revision, corpus_generation,
              " ".join(query.casefold().split()))
    if any(not field for field in fields):
        raise ValueError("incomplete cache scope")
    return sha256("\\x1f".join(fields).encode("utf-8")).hexdigest()

base = retrieval_cache_key("west", "analyst-47", "acl-r8", "index-r8", " AX-47 status ")
assert base != retrieval_cache_key("east", "analyst-47", "acl-r8", "index-r8", "AX-47 status")
assert base != retrieval_cache_key("west", "analyst-47", "acl-r9", "index-r8", "AX-47 status")''',
        cost="Key construction is O(q) for query length q. Rechecking K cached passage IDs is O(K) plus authorization lookup cost. That recheck adds latency but prevents stale permissions from leaking. If it becomes expensive, use a policy-version or revocation index with a measured freshness bound.",
        mistakes=["Caching by query text without tenant or principal scope.", "Assuming TTL handles emergency revocation.", "Using previous-turn passages after the user's role changes.", "Serving a cached answer after its citations disappear."],
        drill="Run the same 19 questions as two principals with different access. Revoke a document after a warm cache and prove no old passage, claim or citation appears next.",
        related=[R + "query-intent-and-retrieval-routing", R + "corpus-permissions-and-document-lifecycle", R + "freshness-deletion-and-index-swap", R + "prompt-injection-and-tool-boundary"],
    ),
    dict(
        slug="retrieval-release-evaluation-and-slice-gates",
        title="Retrieval release gates: evaluate slices before changing an index",
        summary="Promote a retriever only after judged recall, support, access and latency checks pass for distinct query families.",
        sections=[
            ("Freeze the comparison", "Store query, permitted corpus snapshot, expected answer-bearing passage IDs, acceptable abstention and query family. Run current and candidate versions against the same access snapshot. Keep exact IDs, paraphrases, multilingual queries, long documents, stale revisions and no-answer cases separate. A global average can rise while one small tenant loses its only correct passage. [[retrieval-ai/retrieval-vs-answer-evaluation|Retrieval and answer quality]] remain separate measurements."),
            ("Measure decisions", "For each query, measure answer-bearing candidate recall, required-fact survival in the final packet, first relevant rank and unsupported answer claims. Record p95 latency and forbidden-passage exposure; the latter must stay at zero. Some questions have no answer, so abstention matters. Compare equal cutoffs and token budgets across versions."),
            ("Set slice floors before testing", "Write thresholds before seeing candidate results. A release may require no access violations, no decline in exact-ID recall and a bounded p95 increase while accepting a defined paraphrase improvement. Such thresholds are product policies, not universal constants. Inspect every newly failed query and retain it for regression work."),
            ("Canary and recover", "After offline gates pass, send a small permitted traffic slice to the candidate alias and watch latency, empty-result rate and citation resolution before widening. Record encoder, extraction, corpus, filter and ranker revisions. Rollback query encoder and index alias together. [[retrieval-ai/embedding-space-version-and-migration|Embedding migrations]] fail quietly when only one half is reverted."),
        ],
        code='''def release_decision(current: dict, candidate: dict) -> tuple[bool, list[str]]:
    failures = []
    if candidate["access_violations"] != 0:
        failures.append("access violation")
    if candidate["exact_id_recall"] < current["exact_id_recall"]:
        failures.append("exact-ID recall regression")
    if candidate["answer_support"] < current["answer_support"]:
        failures.append("answer support regression")
    if candidate["p95_ms"] > current["p95_ms"] + 47:
        failures.append("latency budget exceeded")
    return not failures, failures

baseline = {"access_violations": 0, "exact_id_recall": .94,
            "answer_support": .91, "p95_ms": 168}
candidate = {"access_violations": 0, "exact_id_recall": .95,
             "answer_support": .92, "p95_ms": 199}
assert release_decision(baseline, candidate) == (True, [])
assert release_decision(baseline, {**candidate, "access_violations": 1})[0] is False''',
        cost="Evaluation of Q queries and K candidates costs at least O(QK) identity work, plus search, rerank and answer calls. Keep a small smoke set for each change and a broader judged set before promotion. The 47 ms allowance in this example is product-specific; choose a measured budget for the actual service.",
        mistakes=["Promoting on one average while an important tenant slice regresses.", "Changing the judged corpus between baseline and candidate runs.", "Reporting answer quality without candidate recall or access exposure.", "Rolling back the index while leaving the new query encoder active."],
        drill="Build 120 judged questions across six slices. Compare two generations at identical top-12 and 600-token packet limits, list newly failed queries and record the rollback target.",
        related=[R + "embedding-space-version-and-migration", R + "filtered-ann-recall-and-latency", R + "claim-level-citation-and-support-checks", R + "retrieval-vs-answer-evaluation"],
    ),
    dict(
        slug="hybrid-search-release-gate-project",
        title="Project: ship a permission-aware hybrid retrieval release gate",
        summary="Build a small corpus, two search legs, rank fusion, evidence packing and a failing release gate with reproducible checks.",
        sections=[
            ("Define the corpus and questions", "Create 83 passages from policy revisions, case notes and help articles. Give every passage an immutable ID, tenant, document revision, state and source location. Add two tenants, one revoked passage, duplicated wording in two revisions and one table-like exception. Write 47 judged questions across exact IDs, paraphrases, mixed intent, no-answer and conflicting-revision cases. Keep judgments outside the search implementation."),
            ("Implement a transparent baseline", "Start with a simple token-based lexical ranker and a precomputed semantic ranking supplied as data. Both legs must filter tenant and active state before fusion. Use [[retrieval-ai/hybrid-search-and-reciprocal-rank-fusion|rank fusion]] with stable passage identity; show each leg's rank and the final order for a query. Add a bounded [[retrieval-ai/context-packing-and-evidence-diversity|context packet]] and store included IDs. This project tests retrieval logic without requiring paid model calls."),
            ("Break it deliberately", "Remove an access filter from one leg and demonstrate that the test fails before a private passage reaches fusion. Swap in a stale revision and verify rejection. Make a candidate absent from both lists and show that reranking cannot recover it. Generate one unsupported numeric claim and prove [[retrieval-ai/claim-level-citation-and-support-checks|citation validation]] catches it. Each failure should name its query and passage IDs."),
            ("Gate the release", "Compare baseline and candidate on answer-bearing recall at 12, first relevant rank, forbidden exposures, packet fact coverage and p95 local query latency. Write a release decision that refuses any exposure or exact-ID regression. Package corpus manifest, judgment set, executable checks, measured output and rollback target. A screenshot of a plausible answer is not completion evidence."),
        ],
        code='''def release_gate(rows: list[dict]) -> dict[str, object]:
    if not rows:
        raise ValueError("judged queries required")
    exposed = [row["query_id"] for row in rows if row["forbidden_seen"]]
    missed = [row["query_id"] for row in rows
              if row["exact_id_query"] and not row["answer_passage_found"]]
    return {"promote": not (exposed or missed), "exposed": exposed,
            "missed_exact_ids": missed}

checks = [{"query_id": "q-47", "forbidden_seen": False,
           "exact_id_query": True, "answer_passage_found": True},
          {"query_id": "q-63", "forbidden_seen": True,
           "exact_id_query": False, "answer_passage_found": True}]
assert release_gate(checks) == {"promote": False, "exposed": ["q-63"],
                                "missed_exact_ids": []}''',
        cost="For Q judged rows the gate scans O(Q) time and uses O(Q) failure space. Building lexical rankings naively across N passages costs O(QN) token comparisons; production indexes avoid that scan. Keep this project small enough to inspect each failure, then scale only after the contracts are proved.",
        mistakes=["Treating a high fused rank as permission to show a passage.", "Judging only answers and omitting candidate recall.", "Testing the same queries used to hand-tune every threshold without a held-out slice.", "Calling the project complete before deletion and rollback checks pass."],
        drill="Deliver a repository folder with the 83-passage manifest, 47 questions, runnable gate, failure log and a one-page promotion decision. Revoke one passage after building the index and rerun all checks.",
        related=[R + "query-intent-and-retrieval-routing", R + "hybrid-search-and-reciprocal-rank-fusion", R + "retrieval-release-evaluation-and-slice-gates", R + "support-policy-answer-project"],
        kind="project",
    ),
])

new_paths = {R + lesson["slug"] for lesson in lessons}
assert len(new_paths) == len(lessons)
assert not new_paths.intersection(by_path), "new article path already exists"
titles = {path: row["title"] for path, row in by_path.items()}
titles.update({R + lesson["slug"]: lesson["title"] for lesson in lessons})
link_pattern = re.compile(r"\[\[([^|\]]+)\|([^\]]+)\]\]")


def render(text: str) -> str:
    pieces = []
    start = 0
    for match in link_pattern.finditer(text):
        pieces.append(html.escape(text[start:match.start()]))
        path, label = match.groups()
        if path not in titles:
            raise ValueError(f"broken internal link: {path}")
        pieces.append(f'<a href="/{html.escape(path, quote=True)}">{html.escape(label)}</a>')
        start = match.end()
    pieces.append(html.escape(text[start:]))
    return "".join(pieces)


def link(path: str) -> str:
    if path not in titles:
        raise ValueError(f"broken related link: {path}")
    return f'<a href="/{html.escape(path, quote=True)}">{html.escape(titles[path])}</a>'


def body_for(lesson: dict) -> str:
    sections = [f'<p>{render(lesson["summary"])}</p>']
    for heading, paragraph in lesson["sections"]:
        sections.extend((f'<h2>{html.escape(heading)}</h2>', f'<p>{render(paragraph)}</p>'))
    sections.extend((
        '<h2>Worked contract</h2>',
        '<pre><code class="language-python">' + html.escape(lesson["code"]) + '</code></pre>',
        '<h2>Performance and operating cost</h2>',
        f'<p>{render(lesson["cost"])}</p>',
        '<h3>Common Mistakes</h3>',
        '<ul>' + ''.join(f'<li>{render(mistake)}</li>' for mistake in lesson["mistakes"]) + '</ul>',
        '<h2>Validation drill</h2>',
        f'<p>{render(lesson["drill"])}</p>',
        '<h2>Read next</h2>',
        '<ul>' + ''.join(f'<li>{link(path)}</li>' for path in lesson["related"]) + '</ul>',
    ))
    return ''.join(sections)


changed = []
for offset, lesson in enumerate(lessons):
    path = R + lesson["slug"]
    is_project = lesson.get("kind") == "project"
    row = {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
        "type": "article", "path": path, "title": lesson["title"],
        "summary": lesson["summary"], "body": body_for(lesson),
        "category": "AI & Data", "subject": "retrieval-ai-project" if is_project else "retrieval-ai",
        "difficulty": "Advanced", "tags": ["ai-data", "retrieval-ai", "project" if is_project else "tutorial"],
        "potd_date": None, "featured": False, "sort_order": 8416 + offset,
        "status": "published", "published_at": stamp, "created_at": stamp, "updated_at": stamp,
        "data": {
            "subject_root": HUB,
            "section_path": PROJECT_HUB if is_project else HUB,
            "content_format": "html", "seo_ready": True,
            "kind": "project" if is_project else "tutorial",
            "reading_minutes": max(6, round(len(re.sub('<[^>]+>', ' ', body_for(lesson)).split()) / 180)),
            "author_path": "authors/aitrove-editorial",
            "verification_suite": "Executable standard-library example and editorial review",
            "related": [{"path": related, "title": titles[related]} for related in lesson["related"]],
        },
    }
    rows.append(row)
    by_path[path] = row
    changed.append(row)


def add_hub_module(hub_path: str, title: str, paths: list[str]) -> None:
    hub = by_path[hub_path]
    hub["data"]["modules"].append({"title": title, "lessons": paths})
    hub["body"] += '<h2>' + html.escape(title) + '</h2><ul>' + ''.join(
        f'<li>{link(path)}</li>' for path in paths) + '</ul>'
    hub["updated_at"] = stamp
    changed.append(hub)


tutorial_paths = [R + item["slug"] for item in lessons if item.get("kind") != "project"]
project_paths = [R + item["slug"] for item in lessons if item.get("kind") == "project"]
add_hub_module(HUB, "Extraction, routing and index contracts", tutorial_paths[:4])
add_hub_module(HUB, "Ranking, context and answer support", tutorial_paths[4:8])
add_hub_module(HUB, "Operations and release gates", tutorial_paths[8:])
add_hub_module(R.rstrip('/'), "Advanced retrieval engineering", tutorial_paths)
add_hub_module(PROJECT_HUB, "Release-gate project", project_paths)
root_projects = by_path[R.rstrip('/')]["data"]["modules"]
next(module for module in root_projects if module["title"] == "Apply the ideas")["lessons"].extend(project_paths)

incoming = {
    R + "retrieval-recall-and-reranking": [tutorial_paths[4], tutorial_paths[5]],
    R + "chunk-identity-and-context-boundaries": [tutorial_paths[1], tutorial_paths[6]],
    R + "retrieval-vs-answer-evaluation": [tutorial_paths[9]],
    R + "evidence-bound-answer-and-abstention": [tutorial_paths[7]],
    R + "prompt-injection-and-tool-boundary": [tutorial_paths[8]],
    R + "freshness-deletion-and-index-swap": [tutorial_paths[2], tutorial_paths[9]],
    "natural-language-processing/retrieval-positive-pair-identity-and-revision": [tutorial_paths[9]],
    "prompt-engineering/retrieval-context-packet-coverage-and-claim-mapping": [tutorial_paths[6], tutorial_paths[7]],
}
for source, targets in incoming.items():
    row = by_path[source]
    row["body"] += '<h2>Continue the retrieval workflow</h2><ul>' + ''.join(
        f'<li>{link(path)}</li>' for path in targets) + '</ul>'
    related = row["data"].setdefault("related", [])
    known = {item["path"] for item in related}
    related.extend({"path": path, "title": titles[path]} for path in targets if path not in known)
    row["updated_at"] = stamp
    changed.append(row)

assert len({row["path"] for row in rows}) == len(rows)
changed = list({row["path"]: row for row in changed}.values())
assert len({row["path"] for row in changed}) == len(changed)
FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
OUTPUT.write_text(json.dumps(changed, ensure_ascii=False, indent=2) + "\n")
print(f"Added {len(lessons)} Retrieval AI articles; import packet has {len(changed)} entries: {OUTPUT}")
