"""Add original retrieval lessons on metrics, correction, tombstones and deadlines."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-retrieval-ai-thirteenth-import-20261007.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "retrieval-ai/"
hub_path = prefix + "retrieval-ai-tutorial"

lessons = [
    {
        "slug": "vector-similarity-metrics-normalization-and-rank-changes",
        "title": "Vector similarity metrics: normalization changes the ranking",
        "summary": "Choose cosine, inner product or L2 from the embedding contract and test exact rankings before building an ANN index.",
        "sections": [
            ("The metric is part of the embedding contract", "A vector index needs a comparison rule. Cosine similarity compares direction after accounting for vector length; inner product combines direction and magnitude; Euclidean distance measures geometric separation. None is universally best for retrieval. An embedding model may assume normalized outputs or use vector length as a signal. If that contract changes, the same passage vectors can rank differently even when their dimensions match. Record the metric, normalization rule, model revision and dimension together. [[retrieval-ai/embedding-space-version-and-migration|Embedding migrations]] should reject an index whose metric or normalization rule differs from the serving query encoder."),
            ("Normalize both sides when cosine is the goal", "For nonzero unit vectors, the inner product equals cosine similarity. Squared L2 distance then equals two minus twice the inner product, so all three produce equivalent orderings when applied consistently to those unit vectors. That equivalence does not hold when only queries are normalized or when passage magnitudes vary. Normalize vectors before indexing and before querying if the backend implements cosine through inner product. A zero vector cannot be normalized; reject it and inspect the encoder pipeline rather than silently inserting it."),
            ("Compare exact scores before ANN tuning", "An approximate index can miss a neighbor because of graph traversal, quantization or filters. First run exact search under the intended metric; then compare ANN results to that baseline at a fixed K and permission scope. Otherwise a rank change caused by accidental normalization may be blamed on a candidate budget. [[retrieval-ai/hnsw-candidate-budgets-and-ann-recall-curves|HNSW budgets]] affect exploration, while [[retrieval-ai/vector-quantization-recall-and-exact-reranking|quantization]] affects stored precision. Keep these experiments separate."),
            ("Do not mix metric scores across branches", "An L2 distance is smaller when better; cosine and inner product are larger when better. Their numeric scales differ and may vary by model or collection. A hybrid ranker cannot add raw values from these branches and expect a meaningful order. Convert each branch to a common calibrated signal using judged data, or combine ranks while keeping branch score interpretation intact. [[retrieval-ai/score-normalization-and-fusion-calibration|Fusion calibration]] handles this final step. A threshold learned for cosine cannot be copied to an inner-product index without reevaluation."),
            ("Test distributions and exceptions", "Measure exact top-K recall on paraphrases, rare identifiers and out-of-domain text; compare score distributions before setting any answer threshold. Include zero vectors, NaNs, dimension mismatches and vectors whose magnitudes differ sharply. Check whether the embedding provider normalizes outputs at each version, but verify actual stored vectors rather than relying on a name. If magnitude is useful, cosine may discard a valuable signal. If magnitude is accidental, inner product may let unusually large vectors dominate. The decision belongs to measured retrieval quality, not a formula alone."),
        ],
        "code": '''from math import isfinite, sqrt

def scores(query: tuple[float, ...], passage: tuple[float, ...]
           ) -> tuple[float, float, float]:
    if not query or len(query) != len(passage):
        raise ValueError("dimension mismatch")
    if not all(isfinite(value) for value in query + passage):
        raise ValueError("non-finite coordinate")
    query_norm = sqrt(sum(value * value for value in query))
    passage_norm = sqrt(sum(value * value for value in passage))
    if query_norm == 0 or passage_norm == 0:
        raise ValueError("zero vector")
    dot = sum(left * right for left, right in zip(query, passage))
    squared_l2 = sum((left - right) ** 2
                     for left, right in zip(query, passage))
    return dot, dot / (query_norm * passage_norm), squared_l2

query = (1.0, 0.0)
aligned = (4.0, 0.0)
nearby = (1.0, .3)
assert scores(query, aligned)[0] > scores(query, nearby)[0]
assert scores(query, aligned)[1] > scores(query, nearby)[1]
assert scores(query, aligned)[2] > scores(query, nearby)[2]''',
        "cost": "Computing any one score for D-dimensional vectors takes O(D) time and O(1) extra space. Exact ranking across N passages takes O(ND) score work plus top-K selection or sorting; normalization can be precomputed at ingestion but still costs O(D) per new vector. ANN reduces comparisons at the cost of approximate recall and index memory. The example deliberately shows that inner product and cosine favor the long aligned vector while L2 favors the shorter nearby one; those are different ranking contracts, not a contradiction.",
        "mistakes": ["Normalizing queries but leaving indexed passages unnormalized when expecting cosine order.", "Comparing a smaller-is-better L2 distance directly with larger-is-better cosine scores.", "Changing metric settings without rebuilding or validating the indexed vectors.", "Passing zero, non-finite or wrong-dimensional vectors into a search index."],
        "drill": "On 67 judged queries, compare exact cosine, inner-product and L2 top-12 results under one embedding version. Report per-slice recall and vector norm distributions before selecting the production metric.",
        "related": [prefix + "embedding-space-version-and-migration", prefix + "hnsw-candidate-budgets-and-ann-recall-curves", prefix + "vector-quantization-recall-and-exact-reranking", prefix + "score-normalization-and-fusion-calibration"],
    },
    {
        "slug": "retrieval-spelling-correction-and-identifier-preservation",
        "title": "Spelling correction in retrieval: suggest a fix, preserve the original",
        "summary": "Recover ordinary misspellings without silently rewriting part numbers, names or exact-match evidence.",
        "sections": [
            ("Correction is a candidate branch", "A misspelled word can create a zero-result query even when the right document is indexed. A correction service proposes alternatives from a controlled vocabulary; it does not establish what the user intended. Search the original text first or alongside a suggested form, then present the correction explicitly when it changes results. A silent rewrite can retrieve the wrong part or person. [[retrieval-ai/safe-search-query-parsing-and-literal-identifiers|Safe query parsing]] defines the user's literal request; correction must preserve that record for tracing and evaluation."),
            ("Protect identifier-shaped tokens", "Maintenance IDs, invoice numbers, code symbols and legal clauses often differ by one character. Edit distance would call them close, but their meaning may be unrelated. Route tokens with digits, punctuation or recognized identifier patterns through exact fields, with correction disabled unless a domain-specific alias registry says otherwise. Ordinary words can be considered for correction after a lexical miss. [[retrieval-ai/lexical-analyzers-field-scoring-and-identifier-safety|Identifier-safe lexical search]] protects the corresponding index fields. Keep case and punctuation rules consistent with each identifier family."),
            ("Generate and rank alternatives conservatively", "Edit distance is a candidate generator, not a relevance score. Limit candidate vocabulary by language, source status and permission scope, then use term frequency and contextual fit only within that allowed set. One edit in a short word may be more dangerous than two edits in a long word. Correct at most a bounded number of tokens so a long noisy query does not explode into combinations. The [[retrieval-ai/query-expansion-guardrails-and-drift-tests|query expansion guardrail]] applies: record which branch added a candidate and what evidence it returned."),
            ("Choose the display contract", "If the original search has strong exact matches, do not replace it. If correction produces better results, label them as results for the corrected text and offer a one-click return to the original. Show one or a few alternatives, not a hidden substitution chain. For a retrieval-based answer, a candidate corrected query still needs claim-level source support; higher result count alone does not justify an answer. [[retrieval-ai/evidence-bound-answer-and-abstention|Evidence-bound answering]] can abstain when both branches fail."),
            ("Evaluate false corrections explicitly", "Build separate test slices for typos, rare names, serial numbers, multilingual terms and already-valid but uncommon words. Count successful recovery and harmful rewrites, not just suggestion acceptance. A model can over-correct rare valid terms toward popular words, especially after popularity ranking. Test newly added vocabulary and deleted documents, because a correction index can lag the retrieval index. A suggestion pointing to removed or forbidden content is still a leak. [[retrieval-ai/retrieval-autocomplete-suggestions-and-privacy|Private autocomplete]] has the same vocabulary and permission boundary."),
        ],
        "code": '''import re

IDENTIFIER = re.compile(r"(?=.*[0-9])[A-Za-z0-9/-]{3,}$")

def edit_distance(left: str, right: str) -> int:
    previous = list(range(len(right) + 1))
    for row_number, left_char in enumerate(left, 1):
        current = [row_number]
        for column_number, right_char in enumerate(right, 1):
            current.append(min(current[-1] + 1,
                               previous[column_number] + 1,
                               previous[column_number - 1]
                               + (left_char != right_char)))
        previous = current
    return previous[-1]

def suggest_spelling(token: str, approved_terms: set[str]) -> str | None:
    if IDENTIFIER.fullmatch(token) or len(token) < 4:
        return None
    candidates = [(edit_distance(token.casefold(), term.casefold()), term)
                  for term in approved_terms]
    close = sorted((distance, term) for distance, term in candidates
                   if distance == 1)
    return close[0][1] if close else None

assert suggest_spelling("presure", {"pressure", "seal"}) == "pressure"
assert suggest_spelling("P-47/AC", {"P-48/AC"}) is None
assert suggest_spelling("seal", {"seal"}) is None''',
        "cost": "The two-row edit-distance routine uses O(LR) time and O(R) space for token lengths L and R. Scanning V approved terms multiplies that work by V; a production dictionary uses length buckets, prefix indexes or a specialized candidate structure before exact distance checks. Preserve the original query branch so the suggestion can be rejected. The example returns one candidate only and does not implement contextual ranking, authorization or a search engine.",
        "mistakes": ["Silently replacing a user's serial number with the nearest popular code.", "Treating edit distance alone as proof of intended meaning.", "Building the suggestion dictionary from restricted or deleted content.", "Measuring only recovered queries while ignoring harmful corrections of valid rare words."],
        "drill": "Label 81 queries: ordinary typos, rare valid terms, multilingual words and one-character-different IDs. Measure recovered top-12 recall and harmful-rewrite rate with the original branch retained.",
        "related": [prefix + "safe-search-query-parsing-and-literal-identifiers", prefix + "lexical-analyzers-field-scoring-and-identifier-safety", prefix + "query-expansion-guardrails-and-drift-tests", prefix + "retrieval-autocomplete-suggestions-and-privacy"],
    },
    {
        "slug": "retrieval-index-tombstones-compaction-and-delete-proof",
        "title": "Retrieval tombstones: compact indexes without reviving deleted evidence",
        "summary": "Distinguish logical deletion from physical reclamation and verify that a compacted generation preserves current access rules.",
        "sections": [
            ("Deletion has two clocks", "A source can be removed from search results before its bytes are physically reclaimed. A logical tombstone marks it ineligible; segment merge or full index rebuild later removes obsolete postings and vector entries. A privacy or compliance request cannot wait for compaction before stopping disclosure. Enforce deletion in the authoritative eligibility layer immediately, then track physical reclamation under a separate deadline. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Document lifecycle]] defines the access decision; compaction changes storage and performance, not the authority of that decision."),
            ("Rebuild from authoritative live records", "A compactor must read a consistent source snapshot plus all later delete and update events up to a recorded watermark. Copying only old index entries can revive a document that was deleted while the build ran. Stable document IDs and revision numbers make replay idempotent. When the candidate generation catches up, compare its active-ID set against the authoritative source and tombstone ledger before traffic moves. [[retrieval-ai/incremental-ingestion-idempotency-and-delete-races|Ingestion delete races]] explain why event order and repeated deliveries must be accounted for."),
            ("Graph and lexical cleanup are different operations", "An inverted index may retain deleted postings until a segment merge. An ANN graph can retain unreachable or masked nodes and may need a backend-specific rebuild to recover memory and search quality. Do not assume an index force-merge command handles vector graph layout exactly as it handles text postings. Measure deleted-record ratio, storage bytes, candidate visits and recall on an exact baseline before scheduling maintenance. [[retrieval-ai/hnsw-candidate-budgets-and-ann-recall-curves|HNSW recall curves]] can show whether stale graph structure affects retrieval."),
            ("Cut over with a deletion proof", "A new compacted generation is not ready because its build job succeeded. It must pass source-count checks, sampled document hashes, permission tests, delete proofs and a freshness watermark. Pin in-flight requests, then switch the serving pointer to the verified generation. Retain rollback only if the old generation still applies current tombstones and access filters. [[retrieval-ai/retrieval-index-alias-cutover-and-rollback|Alias cutovers]] describe the pointer operation; the deletion proof guards what that pointer exposes."),
            ("Schedule physical work without hiding failures", "Merge or rebuild work consumes I/O, CPU and temporary disk. Running it on every delete can harm ingestion and p95 query latency; never running it can inflate storage and graph traversal. Set thresholds from measured delete ratio, disk headroom and latency, and keep a separate deadline for permanent erasure when required. If a build fails halfway, keep the current serving generation and its tombstone filter. Observability should report both eligibility latency and bytes remaining, because a zero-result query does not prove physical deletion."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class SourceRevision:
    document_id: str
    revision: int
    text: str

def compact(source_rows: list[SourceRevision],
            deleted_ids: set[str]) -> dict[str, SourceRevision]:
    active = {}
    for row in source_rows:
        if row.document_id in deleted_ids:
            continue
        current = active.get(row.document_id)
        if current is None or row.revision > current.revision:
            active[row.document_id] = row
    assert not active.keys() & deleted_ids
    return active

history = [SourceRevision("pump-p47", 1, "old seal rule"),
           SourceRevision("pump-p47", 2, "current seal rule"),
           SourceRevision("private-plan", 1, "restricted plan")]
generation = compact(history, {"private-plan"})
assert generation["pump-p47"].revision == 2
assert "private-plan" not in generation''',
        "cost": "Scanning R source revisions takes O(R) time and O(D) memory for D retained documents; writing a real index adds tokenization, embedding, posting and graph-build costs. A tombstone lookup can be near constant time with a suitable set, but maintaining it across every serving path has operational cost. The example assumes one authoritative delete set at a fixed snapshot. A production build must replay later changes and verify a watermark before cutover; physical byte removal depends on the backend's storage lifecycle.",
        "mistakes": ["Waiting for physical compaction before suppressing a deleted document in search.", "Building from stale source snapshots without replaying newer tombstones.", "Assuming a clean query result proves the underlying bytes were erased.", "Rolling back to a generation that lacks current deletion and permission filters."],
        "drill": "Create 123 source revisions, delete eight during a rebuild and replay out-of-order updates. Compare active IDs with the authoritative ledger before and after cutover; inspect disk bytes and top-12 recall separately.",
        "related": [prefix + "corpus-permissions-and-document-lifecycle", prefix + "incremental-ingestion-idempotency-and-delete-races", prefix + "retrieval-index-alias-cutover-and-rollback", prefix + "hnsw-candidate-budgets-and-ann-recall-curves"],
    },
    {
        "slug": "retrieval-deadline-budgets-cancellation-and-partial-result-policy",
        "title": "Retrieval deadlines: cancel optional work and label incomplete evidence",
        "summary": "Divide a request deadline across retrieval stages, prevent queued work from outliving the user and make partial results explicit.",
        "sections": [
            ("One request has one deadline", "A retrieval-based answer may run query parsing, lexical search, vector search, reranking, evidence packing and generation. Giving each stage its own full timeout can multiply the user's wait. Start with one end-to-end deadline and pass the remaining time to every downstream operation. Reserve time for mandatory authorization and evidence checks; optional reranking can be skipped when the budget is nearly spent. [[retrieval-ai/reranker-candidate-window-and-budget|Reranker budgeting]] handles the quality cost of a smaller or absent rerank stage."),
            ("Admission control comes before expensive work", "If the system is saturated, admitting every request can increase queueing delay for all users. Cap concurrent expensive branches, reject or shed excess optional work and return a clear retryable status when the required search cannot finish. A cancellation signal should reach the search backend and any embedding call, not merely stop waiting in the frontend while the work continues. Record queue delay separately from execution time. [[retrieval-ai/retrieval-shard-fanout-replicas-and-partial-results|Shard fanout]] shows how one slow branch can dominate the tail."),
            ("Required evidence is not optional", "A timeout in one shard or source may leave an apparently plausible top-K list that omits the only relevant document. Decide in advance whether partial results may be displayed for navigation, and label coverage when they are. Do not feed an incomplete candidate set into a confident answer without an explicit support and abstention policy. An authorization timeout should fail closed; it cannot be treated like an optional reranker. [[retrieval-ai/evidence-bound-answer-and-abstention|Evidence-bound answering]] sets the final response rule."),
            ("Budget stages by their tail behavior", "Allocate deadlines using measured p95 and p99 latency per stage and query slice, not a uniform split. A rare filtered vector query may need more candidate exploration than a common lexical query. If optional work is skipped, log the decision, residual candidate count and index generation so later evaluation can separate quality changes from model changes. A fixed budget should be revisited after corpus growth, shard movement or a new embedding model. [[retrieval-ai/retrieval-traces-and-incident-debugging|Retrieval traces]] hold those facts."),
            ("Exercise slow and failed branches", "Simulate a delayed shard, an overloaded embedding service, a cancelled client and a permission store that does not respond. Verify that backend jobs stop, partial evidence is labeled, and private data never crosses a failed authorization boundary. Test retries with idempotency: a user retry must not create duplicate ingestion or repeated paid work. An end-to-end timeout is an operating contract, not a substitute for measuring actual answer support and recall under degraded conditions."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class RetrievalStage:
    name: str
    estimated_ms: int
    required: bool

def plan_budget(stages: list[RetrievalStage], total_ms: int
                ) -> tuple[list[str], list[str]]:
    if total_ms <= 0:
        raise ValueError("deadline must be positive")
    remaining = total_ms
    run, skipped = [], []
    for stage in stages:
        if stage.estimated_ms < 0:
            raise ValueError("negative stage estimate")
        if stage.estimated_ms > remaining:
            if stage.required:
                raise TimeoutError(f"required stage lacks budget: {stage.name}")
            skipped.append(stage.name)
            continue
        run.append(stage.name)
        remaining -= stage.estimated_ms
    return run, skipped

pipeline = [RetrievalStage("authorization", 19, True),
            RetrievalStage("lexical", 31, True),
            RetrievalStage("vector", 39, True),
            RetrievalStage("rerank", 47, False)]
assert plan_budget(pipeline, 99) == (
    ["authorization", "lexical", "vector"], ["rerank"])''',
        "cost": "Planning S stages takes O(S) time and O(S) output space. The example uses estimates, not actual timing or cancellation; a real service computes remaining time from a monotonic deadline and passes it to backend calls. Skipping an optional stage saves its work but may reduce ranking quality. Backend cancellation, concurrency limits and bounded queues are needed to stop abandoned work from consuming capacity. Treat missing required evidence or authorization as a failure, not as a fast answer.",
        "mistakes": ["Giving every downstream stage the full request timeout.", "Stopping the HTTP wait while backend queries continue to run.", "Treating a timed-out authorization check as permission to proceed.", "Presenting incomplete shard results as if the full corpus was searched."],
        "drill": "Replay 59 queries with injected delays at authorization, vector search and reranking. Record p95 latency, cancellation success, skipped stages and answer support; require explicit failure for missing mandatory work.",
        "related": [prefix + "reranker-candidate-window-and-budget", prefix + "retrieval-shard-fanout-replicas-and-partial-results", prefix + "evidence-bound-answer-and-abstention", prefix + "retrieval-traces-and-incident-debugging"],
    },
]

new_paths = [prefix + lesson["slug"] for lesson in lessons]
assert len(set(new_paths)) == len(new_paths)
assert not set(new_paths) & by_path.keys()
titles = {path: row["title"] for path, row in by_path.items()}
titles.update(zip(new_paths, (lesson["title"] for lesson in lessons)))
pattern = re.compile(r"\[\[([^|\]]+)\|([^\]]+)\]\]")

def render(value: str) -> str:
    parts = []
    start = 0
    for match in pattern.finditer(value):
        parts.append(html.escape(value[start:match.start()]))
        path, label = match.groups()
        if path not in titles:
            raise ValueError(f"broken internal link: {path}")
        parts.append(f'<a href="/{html.escape(path, quote=True)}">{html.escape(label)}</a>')
        start = match.end()
    return "".join(parts) + html.escape(value[start:])

def link(path: str) -> str:
    if path not in titles:
        raise ValueError(f"broken related link: {path}")
    return f'<a href="/{html.escape(path, quote=True)}">{html.escape(titles[path])}</a>'

def body_for(lesson: dict) -> str:
    body = f'<p>{render(lesson["summary"])}</p>'
    for heading, paragraph in lesson["sections"]:
        body += f'<h2>{html.escape(heading)}</h2><p>{render(paragraph)}</p>'
    body += '<h2>Worked contract</h2><pre><code class="language-python">' + html.escape(lesson["code"]) + '</code></pre>'
    body += '<h2>Performance and operating cost</h2><p>' + render(lesson["cost"]) + '</p>'
    body += '<h3>Common Mistakes</h3><ul>' + ''.join(f'<li>{render(value)}</li>' for value in lesson["mistakes"]) + '</ul>'
    body += '<h2>Validation drill</h2><p>' + render(lesson["drill"]) + '</p>'
    body += '<h2>Read next</h2><ul>' + ''.join(f'<li>{link(path)}</li>' for path in lesson["related"]) + '</ul>'
    return body

changed = []
for offset, lesson in enumerate(lessons):
    path = new_paths[offset]
    body = body_for(lesson)
    row = {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
        "type": "article", "path": path, "title": lesson["title"],
        "summary": lesson["summary"], "body": body, "category": "AI & Data",
        "subject": "retrieval-ai", "difficulty": "Advanced",
        "tags": ["ai-data", "retrieval-ai", "tutorial"], "potd_date": None,
        "featured": False, "sort_order": 8473 + offset, "status": "published",
        "published_at": stamp, "created_at": stamp, "updated_at": stamp,
        "data": {"subject_root": hub_path, "section_path": hub_path,
                 "content_format": "html", "seo_ready": True, "kind": "tutorial",
                 "reading_minutes": max(6, round(len(re.sub('<[^>]+>', ' ', body).split()) / 180)),
                 "author_path": "authors/aitrove-editorial",
                 "verification_suite": "Executable standard-library example and editorial review",
                 "related": [{"path": target, "title": titles[target]} for target in lesson["related"]]},
    }
    rows.append(row)
    by_path[path] = row
    changed.append(row)

for path in (hub_path, "retrieval-ai"):
    row = by_path[path]
    row["data"]["modules"].append({"title": "Vector metrics, spelling, compaction and deadlines", "lessons": new_paths})
    row["body"] += '<h2>Vector metrics, spelling, compaction and deadlines</h2><ul>' + ''.join(
        f'<li>{link(target)}</li>' for target in new_paths) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "hnsw-candidate-budgets-and-ann-recall-curves": [new_paths[0]],
    prefix + "safe-search-query-parsing-and-literal-identifiers": [new_paths[1]],
    prefix + "incremental-ingestion-idempotency-and-delete-races": [new_paths[2]],
    prefix + "reranker-candidate-window-and-budget": [new_paths[3]],
}
for source, targets in incoming.items():
    row = by_path[source]
    row["body"] += '<h2>Continue this retrieval path</h2><ul>' + ''.join(
        f'<li>{link(target)}</li>' for target in targets) + '</ul>'
    related = row["data"].setdefault("related", [])
    known = {value["path"] for value in related}
    related.extend({"path": target, "title": titles[target]} for target in targets if target not in known)
    row["updated_at"] = stamp
    changed.append(row)

assert len({row["path"] for row in rows}) == len(rows)
changed = list({row["path"]: row for row in changed}.values())
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
packet.write_text(json.dumps(changed, ensure_ascii=False, indent=2) + "\n")
print(f"Added {len(lessons)} lessons; publication packet has {len(changed)} entries: {packet}")
