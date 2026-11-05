"""Add original retrieval lessons on sparse search, sharding, paging and chunks."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-retrieval-ai-tenth-import-20261007.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "retrieval-ai/"
hub_path = prefix + "retrieval-ai-tutorial"

lessons = [
    {
        "slug": "learned-sparse-retrieval-term-weights-and-index-cost",
        "title": "Learned sparse retrieval: weighted terms without dense-vector search",
        "summary": "Understand weighted token expansion, inverted-list execution, exact-term safeguards and the real storage cost of sparse semantic search.",
        "sections": [
            ("Represent meaning as weighted terms", "Learned sparse retrieval maps a query and a passage to small sets of vocabulary terms with nonzero weights. A model may assign weight to a related term that never appeared literally in the passage. That expansion can bridge wording differences while retaining an inverted-index execution path. It is not ordinary keyword search: the weights and extra terms come from a model, so their meaning depends on its training data and version. It is also not a dense embedding, where nearly every vector coordinate is populated. [[retrieval-ai/lexical-analyzers-field-scoring-and-identifier-safety|Lexical analysis]] remains valuable for exact strings that a model might split or suppress."),
            ("Build postings for nonzero coordinates", "At index time, write each nonzero passage coordinate to a posting list keyed by vocabulary term, with passage ID and weight. At query time, visit only lists for nonzero query coordinates and accumulate the products of query and passage weights. A term absent from either side contributes zero. Pruning tiny weights can reduce disk and query work, but aggressive pruning can remove the only bridge for a rare question. Measure posting-list length, index bytes and recall at a fixed latency target before choosing a pruning threshold."),
            ("Keep identifiers on a literal path", "A model-generated term for an equipment family must not replace an exact serial number, ticket ID or regulatory clause. Preserve raw identifiers in a separately analyzed field, route identifier-heavy queries through a literal match, and fuse its candidates with the learned sparse list. Keep authorization and document-status filters before final ranking. [[retrieval-ai/hybrid-search-and-reciprocal-rank-fusion|Hybrid fusion]] can combine branches without pretending that BM25 and sparse-model scores share one scale. A model expansion is a recall aid; it is never permission to rewrite a user's stated identifier."),
            ("Version both sides of the match", "Query and passage term weights must come from compatible model and vocabulary versions. If the query encoder changes while old passage postings remain, the same term ID may have a different role or weight distribution. Store model and tokenizer IDs with the index generation, and switch serving traffic only after a complete compatible build. A dual-index migration allows comparison of labeled query slices before cutover. [[retrieval-ai/embedding-space-version-and-migration|Embedding migrations]] follow the same generation discipline even though the storage format differs."),
            ("Evaluate where expansion helps and hurts", "Build judged slices for paraphrases, abbreviations, rare identifiers, multilingual text and adversarial keyword stuffing. Compare learned sparse retrieval against a lexical baseline and a dense branch at the same candidate budget, measuring recall, latency, index size and unsupported-answer rate. Inspect which expansion coordinates caused a false positive; human-readable terms make diagnosis possible, but a readable term does not prove semantic correctness. An answer still needs source evidence and a [[retrieval-ai/claim-level-citation-and-support-checks|claim-level support check]]."),
        ],
        "code": '''from collections import defaultdict

def sparse_candidates(query_weights: dict[str, float],
                      passage_weights: dict[str, dict[str, float]],
                      allowed_ids: set[str]) -> list[tuple[str, float]]:
    postings = defaultdict(list)
    for passage_id, weights in passage_weights.items():
        if passage_id not in allowed_ids:
            continue
        for term, weight in weights.items():
            if weight > 0:
                postings[term].append((passage_id, weight))
    scores = defaultdict(float)
    for term, query_weight in query_weights.items():
        if query_weight <= 0:
            continue
        for passage_id, passage_weight in postings.get(term, ()):
            scores[passage_id] += query_weight * passage_weight
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))

passages = {"pump-p47": {"seal": .8, "leak": .4},
            "pump-p48": {"seal": .2, "motor": .9},
            "private-plan": {"seal": 1.0}}
ranked = sparse_candidates({"seal": .6, "leak": .3}, passages,
                           {"pump-p47", "pump-p48"})
assert ranked == [("pump-p47", .6), ("pump-p48", .12)]''',
        "cost": "For an already built index, query work is proportional to the total posting entries visited for nonzero query terms, plus sorting or top-K selection over scored candidates. The demonstration rebuilds postings in O(W) time and O(W) space for W nonzero passage weights; a production index stores them once and pays that cost during ingestion. Model inference, larger expanded vocabularies and long posting lists can dominate latency. Compare end-to-end cost, not just the dot product.",
        "mistakes": ["Calling model expansion a verified synonym dictionary.", "Pruning weights solely for index size without a rare-query recall test.", "Mixing query and passage encoders from incompatible generations.", "Letting an expanded term outrank a required exact identifier or bypass access filters."],
        "drill": "On 43 judged maintenance questions, compare lexical, learned sparse and fused top-12 recall. Keep separate slices for serial IDs, paraphrases and terms seen in only one manual revision; report p95 latency and index bytes alongside recall.",
        "related": [prefix + "lexical-analyzers-field-scoring-and-identifier-safety", prefix + "hybrid-search-and-reciprocal-rank-fusion", prefix + "score-normalization-and-fusion-calibration", prefix + "embedding-space-version-and-migration"],
    },
    {
        "slug": "retrieval-shard-fanout-replicas-and-partial-results",
        "title": "Retrieval shards: fanout, replica lag and incomplete top-K results",
        "summary": "Route queries across shards, merge local candidates and make partial failure visible instead of presenting an incomplete answer as complete.",
        "sections": [
            ("Split a corpus without splitting the answer contract", "A sharded index places different documents on different serving units. A coordinator asks each relevant shard for local top-K candidates and merges them into a global top-K. This distributes storage and search work, but a query that fans out to every shard can become slower as the shard count rises. Tenant-aware or time-aware routing may reduce fanout when its key is a real query constraint. Routing by guessed topic is dangerous: one mistaken guess can make the answer-bearing shard invisible. [[retrieval-ai/federated-retrieval-source-budgets-and-merging|Federated retrieval]] handles unlike sources; shard fanout concerns partitions of one logical index."),
            ("Merge with stable identity", "Each shard returns a score, a stable passage ID, its index generation and the applied authorization scope. The coordinator must compare scores only when every shard uses the same model, scoring rules and compatible index generation. It then sorts by score and a deterministic tie key, deduplicates repeated passages, and clips to the requested count. One shard returning K candidates is sufficient for a global top-K when scores are comparable and each shard has the same eligibility filter; returning fewer can discard a candidate that belongs in the global result."),
            ("Replicas improve availability, not automatic freshness", "A replica can answer a read while a primary is unavailable, but it may lag behind an update or permission withdrawal. Query routing should select only a replica that has applied the required source offset and revocation watermark; otherwise wait within budget, use an eligible replica, or fail closed. A generic 'healthy' check does not establish the freshness needed by this query. [[retrieval-ai/index-watermarks-freshness-slos-and-stale-answer-policy|Index watermarks]] state what each serving copy has actually applied."),
            ("Treat a missing shard as missing evidence", "If one of four required shards times out, the coordinator cannot claim that its top result is the best document in the corpus. For low-stakes exploratory search it may return explicitly labeled partial results; for an answer requiring complete policy coverage, abstention or retry is safer. Log shard IDs, generations, missing partitions, timeout budgets and candidate counts. Never hide a partial result behind a normal 200 response without a machine-readable completeness field. [[retrieval-ai/evidence-bound-answer-and-abstention|Evidence-bound answers]] should refuse to synthesize a confident claim from a known incomplete search."),
            ("Size and test the fanout budget", "More small shards increase coordinator work, per-shard overhead and the chance that at least one request misses its deadline. Fewer large shards can create memory pressure and longer recovery. Benchmark representative query slices as shard count, replica count and local candidate window change. Inject a slow shard, one stale replica and a node loss; verify that global ranking is stable when complete and that the incomplete path reports precisely what was missed. [[retrieval-ai/retrieval-traces-and-incident-debugging|Retrieval traces]] should make this diagnosis possible without replaying private query text."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class ShardReply:
    shard_id: str
    generation: int
    candidates: tuple[tuple[str, float], ...]

def merge_complete(replies: list[ShardReply], required_shards: set[str],
                   generation: int, limit: int) -> list[tuple[str, float]]:
    if limit < 1 or {reply.shard_id for reply in replies} != required_shards:
        raise ValueError("incomplete shard set")
    if any(reply.generation != generation for reply in replies):
        raise ValueError("mixed index generations")
    best: dict[str, float] = {}
    for reply in replies:
        for passage_id, score in reply.candidates:
            best[passage_id] = max(best.get(passage_id, float("-inf")), score)
    return sorted(best.items(), key=lambda item: (-item[1], item[0]))[:limit]

responses = [ShardReply("north", 47, (("pump-p47", .82),)),
             ShardReply("south", 47, (("pump-p48", .71),))]
assert merge_complete(responses, {"north", "south"}, 47, 1) == [("pump-p47", .82)]
try:
    merge_complete(responses[:1], {"north", "south"}, 47, 1)
except ValueError:
    pass
else:
    raise AssertionError("missing shard was accepted")''',
        "cost": "With S shards each returning at most K candidates, this simple merge reads O(SK) entries, stores O(SK) unique IDs and sorts them in O(SK log(SK)) time. A bounded heap can reduce ranking work when SK is large. Network latency is controlled by the slowest required shard, not the average shard; replicas consume extra storage and indexing capacity. Reducing fanout is useful only if routing cannot exclude eligible evidence.",
        "mistakes": ["Treating a missing shard as an empty shard.", "Merging scores from different model or index generations as if comparable.", "Reading from a stale replica after a permission withdrawal.", "Increasing shard count without measuring coordinator and tail-latency costs."],
        "drill": "Partition 59 documents across three shards. Remove one reply and delay another, then verify complete top-K ordering, generation checks and explicit partial-result behavior under a fixed latency budget.",
        "related": [prefix + "federated-retrieval-source-budgets-and-merging", prefix + "snapshot-consistent-multi-index-retrieval", prefix + "index-watermarks-freshness-slos-and-stale-answer-policy", prefix + "retrieval-traces-and-incident-debugging"],
    },
    {
        "slug": "stable-search-pagination-point-in-time-and-cursors",
        "title": "Stable search pagination: point-in-time views and safe cursors",
        "summary": "Page through ranked results without duplicates or omissions while the corpus changes, and bind a cursor to the query and permission scope.",
        "sections": [
            ("Why offsets drift", "An offset asks for positions in the current ranking. If a document is inserted, deleted or reranked between page one and page two, those positions move: one hit may repeat and another may never be shown. Deep offsets also force an engine to inspect or hold many skipped hits. A cursor instead records the final sort key seen on the prior page, and a point-in-time view pins the index snapshot for the series. [[retrieval-ai/snapshot-consistent-multi-index-retrieval|Snapshot consistency]] covers the same idea across multiple indexes; pagination applies it across successive requests."),
            ("Choose a total order", "Sort by relevance plus a stable unique ID, or by timestamp plus ID for chronological browsing. Score alone is insufficient because many documents can tie. The next page requests records after the last full sort tuple, using the same query, filters, model and index view. If score computation changes midstream, the cursor cannot preserve a stable order. Keep the requested page size bounded and use a deterministic direction for every field."),
            ("Bind the cursor to authorization", "A cursor is user-supplied input, even if the server created it earlier. Include a query fingerprint, tenant or principal scope, permission version, index snapshot ID, last sort tuple and expiry; sign it to detect alteration. On resume, recheck current permissions as well as the pinned snapshot, because a point-in-time view must not preserve access to a document after revocation. Do not place private query text or secrets in a merely encoded cursor. [[retrieval-ai/permission-aware-cache-and-conversation-turns|Permission-aware caches]] face the same identity and revision problem."),
            ("Budget snapshot lifetime", "Holding a point-in-time view retains old index state while users page. Set a short keep-alive, close it when finished where supported, and return an explicit restart response after expiry. A refreshed snapshot can change the result order; silently replacing one mid-cursor defeats the contract. For exports, use a separate bounded job with checkpointing rather than leaving an interactive cursor open for hours. Document whether counts and facets correspond to the pinned view or a new live query."),
            ("Test writes and revocations between pages", "Create tied scores, fetch one page, insert a high-ranked hit, delete a middle hit and revoke access to another. The next page should neither duplicate a previously returned ID nor reveal the revoked one; an expired cursor should fail clearly. Run the same test across replicas if the backend can route successive pages differently. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Document lifecycle]] takes priority over pagination convenience."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class SearchHit:
    passage_id: str
    score: float
    tenant: str

def page_after(hits: list[SearchHit], tenant: str, page_size: int,
               last_key: tuple[float, str] | None = None
               ) -> tuple[list[SearchHit], tuple[float, str] | None]:
    if not 1 <= page_size <= 47:
        raise ValueError("invalid page size")
    ordered = sorted((hit for hit in hits if hit.tenant == tenant),
                     key=lambda hit: (-hit.score, hit.passage_id))
    if last_key is not None:
        ordered = [hit for hit in ordered
                   if (-hit.score, hit.passage_id) > last_key]
    selected = ordered[:page_size]
    next_key = (-selected[-1].score, selected[-1].passage_id) if selected else None
    return selected, next_key

snapshot = [SearchHit("pump-p47", .91, "north"),
            SearchHit("pump-p48", .91, "north"),
            SearchHit("pump-p49", .76, "north"),
            SearchHit("private-plan", .99, "south")]
first, cursor = page_after(snapshot, "north", 2)
second, _ = page_after(snapshot, "north", 2, cursor)
assert [hit.passage_id for hit in first + second] == ["pump-p47", "pump-p48", "pump-p49"]''',
        "cost": "This in-memory demonstration filters and sorts N hits on every page in O(N log N) time and O(N) space. A search engine can seek after the indexed sort tuple without rescanning all prior results, but maintaining a point-in-time view retains segment state and has a lifetime cost. The tuple shown is only the inner seek key; a public API must sign and scope its serialized cursor and enforce expiration plus fresh authorization before serving it.",
        "mistakes": ["Using offset pagination on a frequently updated ranking and assuming positions stay fixed.", "Sorting by score alone when tied scores can reorder.", "Treating base64 encoding as cursor integrity or confidentiality.", "Allowing an old snapshot to bypass a new access revocation."],
        "drill": "Fetch 11 pages from a fixed judged snapshot while inserting, deleting and revoking documents in the live corpus. Verify exact-once IDs for still-authorized results and a clear failure when the snapshot expires.",
        "related": [prefix + "snapshot-consistent-multi-index-retrieval", prefix + "corpus-permissions-and-document-lifecycle", prefix + "permission-aware-cache-and-conversation-turns", prefix + "retrieval-evaluation-labels-and-adjudication"],
    },
    {
        "slug": "chunk-boundary-overlap-and-answer-span-evaluation",
        "title": "Chunk boundaries: test whether the answer survives the split",
        "summary": "Tune passage size and overlap against answer-span recall, citation precision, duplicate context and indexing cost.",
        "sections": [
            ("Chunking is a retrieval decision", "A chunk is the smallest passage the index can return, so its boundaries determine what a retriever can prove. Splitting a procedure between a warning and the step it qualifies may produce a passage that looks relevant but is unsafe alone. Keeping an entire handbook as one chunk dilutes a precise answer and consumes context. Start with source structure: headings, paragraphs, table rows and transcript time ranges. Preserve parent document and revision identity so the original location remains auditable. [[retrieval-ai/chunk-identity-and-context-boundaries|Chunk identity]] defines stable IDs and citation boundaries after a split."),
            ("Treat overlap as a measured tradeoff", "Overlap repeats material across adjacent chunks and can rescue an answer span crossing a fixed window. It also increases token storage, embedding work, candidate duplication and the chance that the same source is mistaken for independent support. A fixed percentage is not a guarantee: a table header, a negation or a section title may fall outside both useful windows. Prefer structure-aware boundaries; use overlap only where judged cases show a gain. [[retrieval-ai/near-duplicate-evidence-and-independent-support|Duplicate evidence]] must be collapsed before citing corroboration."),
            ("Record exact answer spans", "For each judged query, annotate the source document, revision and minimal answer-bearing span, including qualifiers that change the claim. After chunking, ask whether at least one eligible returned chunk contains that full span. Measure answer-span recall at K, citation precision and the fraction of retrieved tokens that are duplicate overlap. This is more informative than measuring whether any chunk from the right document was returned. An answer can mention the right manual while omitting the limit value or exception that makes the result useful."),
            ("Use parent context without losing provenance", "A small child chunk can retrieve accurately; a larger parent section can supply the surrounding condition. Keep the child's offset and the parent's revision, then expand context within a strict token budget. Never merge text across documents or policy revisions just because their headings match. For tables, keep header labels and units with each row. [[retrieval-ai/hierarchical-retrieval-and-parent-child-evidence|Parent-child retrieval]] describes the serving pattern, while [[retrieval-ai/table-retrieval-and-numeric-cell-context|table retrieval]] covers row-level evidence."),
            ("Run controlled chunking experiments", "Hold corpus, queries, embedding model, retriever settings and K constant while changing only the splitting rule. Compare section-aware windows, fixed token windows and minimal overlap on the same answer-span labels. Inspect misses by document type: code blocks, tables, scanned PDFs and incident timelines behave differently. Count extra index entries and ingest time, not just recall. A higher recall score that doubles repeated context and citation confusion can worsen the final answer. [[retrieval-ai/retrieval-release-evaluation-and-slice-gates|Release gates]] should require both evidence quality and acceptable cost."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class PassageWindow:
    document_id: str
    start: int
    end: int

def windows(document_id: str, token_count: int, size: int,
            overlap: int) -> list[PassageWindow]:
    if token_count < 0 or size < 1 or not 0 <= overlap < size:
        raise ValueError("invalid chunk settings")
    result = []
    step = size - overlap
    for start in range(0, token_count, step):
        end = min(start + size, token_count)
        result.append(PassageWindow(document_id, start, end))
        if end == token_count:
            break
    return result

def span_is_complete(chunks: list[PassageWindow], document_id: str,
                     answer_start: int, answer_end: int) -> bool:
    return any(chunk.document_id == document_id
               and chunk.start <= answer_start
               and answer_end <= chunk.end for chunk in chunks)

plain = windows("pump-p47-v3", 83, 30, 0)
with_overlap = windows("pump-p47-v3", 83, 30, 12)
assert not span_is_complete(plain, "pump-p47-v3", 24, 35)
assert span_is_complete(with_overlap, "pump-p47-v3", 24, 35)
assert with_overlap[-1].end == 83''',
        "cost": "For T tokens, window size C and overlap O, the number of windows is roughly T divided by C minus O, so index entries and embedding work rise as overlap approaches C. The example emits windows in O(W) time and O(W) space for W windows; checking one answer span costs O(W) time. Actual tokenizer counts, structural parsing, retrieval and reranking add further cost. Keep offsets in the tokenization version used to build the index, or citations will drift after reprocessing.",
        "mistakes": ["Selecting chunk size from model limits alone without measuring complete answer spans.", "Counting overlapping copies of one passage as independent evidence.", "Splitting a table value away from its unit or header.", "Changing tokenizer or parser without rebuilding offsets and citation IDs."],
        "drill": "Annotate 53 answer spans across prose, tables and procedures. Compare three splitting policies at the same top-12 budget; report complete-span recall, duplicated retrieved tokens, index size and citation errors.",
        "related": [prefix + "chunk-identity-and-context-boundaries", prefix + "hierarchical-retrieval-and-parent-child-evidence", prefix + "table-retrieval-and-numeric-cell-context", prefix + "near-duplicate-evidence-and-independent-support"],
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
        "featured": False, "sort_order": 8461 + offset, "status": "published",
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
    row["data"]["modules"].append({"title": "Sparse search, sharding, stable paging and chunk boundaries", "lessons": new_paths})
    row["body"] += '<h2>Sparse search, sharding, stable paging and chunk boundaries</h2><ul>' + ''.join(
        f'<li>{link(target)}</li>' for target in new_paths) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "lexical-analyzers-field-scoring-and-identifier-safety": [new_paths[0]],
    prefix + "federated-retrieval-source-budgets-and-merging": [new_paths[1]],
    prefix + "snapshot-consistent-multi-index-retrieval": [new_paths[2]],
    prefix + "chunk-identity-and-context-boundaries": [new_paths[3]],
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
