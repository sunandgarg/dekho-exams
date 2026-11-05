"""Add four independent Retrieval AI tutorials and reciprocal links."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-retrieval-ai-twelfth-import-20261007.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "retrieval-ai/"
hub_path = prefix + "retrieval-ai-tutorial"

lessons = [
    {
        "slug": "faceted-retrieval-counts-and-permission-safe-filters",
        "title": "Faceted retrieval: trustworthy counts under permission filters",
        "summary": "Compute evidence-type and revision facets from the authorized result set without leaking restricted document counts.",
        "sections": [
            ("A facet describes the candidate set", "A facet groups search matches by a field such as document type, plant, revision or language. It is a navigation control, not a relevance score. If a query returns maintenance notes and incident reports, a type facet tells the reader how many eligible documents of each kind remain. Define whether counts apply before or after a selected facet: both are useful, but silently mixing them makes the interface inconsistent. For a retrieval answer, the same metadata can steer [[retrieval-ai/query-intent-and-retrieval-routing|query routing]] toward a source type without replacing the relevance judgment."),
            ("Authorize before counting", "Count only documents the requester may see at this moment. A hidden document must not appear in a facet count even if its text never appears in results; a count of one can reveal that a confidential investigation exists. Apply tenant, document-status and access filters before aggregation, then compute buckets from the filtered candidate set. If permissions change, invalidate cached counts with the search result. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Document lifecycle]] includes deletion and revocation, both of which change counts."),
            ("Keep a stable counting unit", "One source manual may produce 70 chunks, while a short incident note produces one. Counting passages would suggest 70 manuals unless the interface clearly labels the unit as passages. For a document-type facet, deduplicate by source document ID and revision policy first; for an answer-span facet, passage counts may be appropriate. Decide whether two revisions are separate documents or one current logical document. The decision should match the result list and citations. [[retrieval-ai/chunk-identity-and-context-boundaries|Chunk identity]] provides the parent IDs required for correct grouping."),
            ("Choose fields and cardinality deliberately", "Use exact metadata values for facets; analyzed body text is a poor source of category keys. A plant name may contain punctuation that a full-text analyzer splits, and a free-form document title can create nearly one bucket per record. Cap visible buckets and expose a separate search within a high-cardinality facet when needed. Distributed top buckets can have approximate counts if shards truncate their local candidates. When exact counts drive a legal or operational decision, use a compatible exact aggregation path and report its extra cost. [[retrieval-ai/retrieval-shard-fanout-replicas-and-partial-results|Shard failures]] must make counts incomplete rather than silently authoritative."),
            ("Test facets alongside ranking", "Create judged searches with multiple document types, one restricted record, duplicate chunks and an old revision. Verify that results, counts and selected filters all share the same authorized snapshot. A user selecting a facet should see a result set that equals the stated count under the same query, subject to pagination and any explicit approximate-count label. Do not compute counts from only the top-K ranked hits unless the UI says top-K: that measures the preview window, not all eligible matches. [[retrieval-ai/stable-search-pagination-point-in-time-and-cursors|Stable pagination]] keeps the same filter and snapshot across pages."),
        ],
        "code": '''from collections import Counter
from dataclasses import dataclass

@dataclass(frozen=True)
class EvidenceRecord:
    document_id: str
    passage_id: str
    tenant: str
    kind: str
    current: bool

def document_facets(records: list[EvidenceRecord], tenant: str,
                    matching_passages: set[str]) -> dict[str, int]:
    visible_documents = {}
    for record in records:
        if record.tenant != tenant or not record.current:
            continue
        if record.passage_id not in matching_passages:
            continue
        visible_documents[record.document_id] = record.kind
    return dict(Counter(visible_documents.values()))

records = [
    EvidenceRecord("manual-p47", "m47-a", "north", "manual", True),
    EvidenceRecord("manual-p47", "m47-b", "north", "manual", True),
    EvidenceRecord("incident-83", "i83-a", "north", "incident", True),
    EvidenceRecord("private-12", "p12-a", "south", "incident", True),
    EvidenceRecord("retired-4", "r4-a", "north", "manual", False),
]
counts = document_facets(records, "north", {r.passage_id for r in records})
assert counts == {"manual": 1, "incident": 1}''',
        "cost": "For P matched passage records, this demonstration takes O(P) time and O(D) space for D distinct visible documents. A production index can aggregate metadata without loading every passage, but exact distinct-document counts and high-cardinality fields can consume memory and network work across shards. Count only after authorization. The example's tenant check is a teaching stand-in; a real service must also enforce per-document access and current revocation state before the bucket stage.",
        "mistakes": ["Counting chunks while labeling the number as documents.", "Computing facet buckets before access filtering.", "Treating counts from the top-K preview as all query matches.", "Showing exact-looking counts after a shard timed out or returned truncated buckets."],
        "drill": "Index 89 passages from 23 documents with two revisions and four restricted records. Compare facet counts with an independently authorized document list, then remove a shard and confirm the UI marks counts incomplete.",
        "related": [prefix + "corpus-permissions-and-document-lifecycle", prefix + "chunk-identity-and-context-boundaries", prefix + "retrieval-shard-fanout-replicas-and-partial-results", prefix + "stable-search-pagination-point-in-time-and-cursors"],
    },
    {
        "slug": "multi-tenant-retrieval-isolation-and-shard-routing",
        "title": "Multi-tenant retrieval: isolate indexes, routes and noisy neighbors",
        "summary": "Choose shared or separate indexes using permission boundaries, shard fanout, tenant size and deletion requirements.",
        "sections": [
            ("Tenant filtering is a security boundary", "A multi-tenant retriever serves several organizations from one application. Every query, suggestion, cache entry and evidence citation must carry the authenticated tenant, regardless of any tenant value typed into the search box. A filter added after candidate generation may already be too late if the vector backend explores or logs unauthorized candidates. Where supported, constrain the index or shard search before ranking and recheck document permissions before returning evidence. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Corpus permissions]] still apply within a tenant; tenancy alone is not document authorization."),
            ("Choose an index layout from workload facts", "A separate index per tenant gives a clear deletion and capacity boundary, but thousands of tiny indexes can waste metadata, shards and warm memory. A shared index with an indexed tenant key reduces per-tenant overhead; it demands strict filtering and makes one large tenant a possible noisy neighbor. A hybrid layout puts large or regulated tenants in their own indexes and small tenants in a shared pool. Document the migration path for a tenant that grows. Do not choose the layout from row count alone: query volume, vector memory, update rate and retention policy matter."),
            ("Use routing to limit work, not to grant access", "Routing records for one tenant to a subset of shards can reduce query fanout, but a routing key is not an authorization check. A malicious or mistaken client can provide another key unless the server derives it from the authenticated identity. Very large tenants may overload one shard, so size routing buckets and rebalance with measured limits. Queries across allowed shared collections may need several shard keys and an explicit merge policy. [[retrieval-ai/retrieval-shard-fanout-replicas-and-partial-results|Shard fanout]] explains the latency and partial-result behavior once a request crosses partitions."),
            ("Keep generations and caches tenant-scoped", "A lexical index migration, vector model upgrade or deletion replay may finish for one tenant before another. Record generation and watermark per tenant, not as a misleading global number. Cache keys need tenant, permission revision, query, filters and index generation; otherwise a cached answer can cross an access boundary after a cutover. [[retrieval-ai/permission-aware-cache-and-conversation-turns|Permission-aware caching]] provides the full revocation contract. Trace storage deserves the same isolation as the content index because raw queries may contain private identifiers."),
            ("Test failures that look like success", "Seed two tenants with the same document title but different contents. Search by title, use autocomplete, paginate and revoke a document while holding a cursor. None of the surfaces should disclose the other tenant's title, count or snippet. Then send a burst from the large tenant and measure the smaller tenant's p95 latency to expose noisy-neighbor effects. Test deletion and rollback too; a tenant moved to a new index must not leave an older copy searchable. [[retrieval-ai/retrieval-index-alias-cutover-and-rollback|Index cutovers]] need this per-tenant deletion proof."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class TenantPassage:
    tenant: str
    passage_id: str
    words: frozenset[str]

def authorized_candidates(passages: list[TenantPassage],
                          authenticated_tenant: str,
                          query_words: set[str]) -> list[str]:
    return sorted(passage.passage_id for passage in passages
                  if passage.tenant == authenticated_tenant
                  and passage.words & query_words)

index = [
    TenantPassage("north", "north-p47", frozenset({"seal", "limit"})),
    TenantPassage("south", "south-p47", frozenset({"seal", "contract"})),
]
assert authorized_candidates(index, "north", {"seal"}) == ["north-p47"]
assert authorized_candidates(index, "south", {"seal"}) == ["south-p47"]''',
        "cost": "The list scan takes O(N) time for N passages and O(K) output space for K authorized matches. An indexed tenant partition or routed shard narrows the scanned candidates, but per-tenant indexes add fixed metadata and operational cost. The example shows the invariant that the tenant comes from authentication; it does not provide a secure search index. Enforce the same tenant scope at suggestion, aggregation, cache and citation boundaries, then measure tail latency under competing tenants.",
        "mistakes": ["Trusting a tenant ID supplied in a search parameter.", "Using routing as the only permission check.", "Moving a tenant between indexes without replaying deletions and clearing old caches.", "Testing average latency only while one tenant saturates a shared shard."],
        "drill": "Populate two tenants with 41 similarly named documents. Exercise search, facets, suggestions, pagination, rollback and deletion; assert zero cross-tenant IDs while one tenant generates five times the query load.",
        "related": [prefix + "corpus-permissions-and-document-lifecycle", prefix + "retrieval-shard-fanout-replicas-and-partial-results", prefix + "permission-aware-cache-and-conversation-turns", prefix + "retrieval-index-alias-cutover-and-rollback"],
    },
    {
        "slug": "retrieval-autocomplete-suggestions-and-privacy",
        "title": "Retrieval autocomplete: useful suggestions without query leaks",
        "summary": "Build prefix suggestions from approved vocabulary, bind them to access scope and prevent private search histories from surfacing.",
        "sections": [
            ("Suggestion sources have different risks", "An autocomplete menu may suggest known document titles, curated subject labels or popular past queries. Titles and labels can be approved at publication; raw query logs can contain names, account IDs and confidential incidents. Never turn query logs into public suggestions merely because the terms are frequent. Start with an approved catalog and a clear deletion path. If popularity is used, apply privacy review and minimum aggregation thresholds before a phrase enters the suggestion index. [[retrieval-ai/safe-search-query-parsing-and-literal-identifiers|Safe query parsing]] still handles the submitted search after the user accepts or edits a suggestion."),
            ("Filter at candidate generation", "A suggestion can leak a restricted document before the user submits a search. Build tenant-scoped suggestion collections or apply an authorization filter inside the suggestion query and recheck access before display. A site-specific prefix should never enumerate another site's vocabulary. Permission revisions and document deletion must invalidate suggestion caches. If a backend's completion feature cannot enforce the needed access boundary, do not index private titles in it. [[retrieval-ai/multi-tenant-retrieval-isolation-and-shard-routing|Tenant isolation]] covers the surrounding index and routing choices."),
            ("Match intent without damaging identifiers", "For ordinary words, prefix and infix matching help when the user types the middle of a title. For serials and codes, preserve punctuation and case-normalization rules that fit the identifier scheme; a generic tokenizer may split P-47/AC into unrelated fragments. Rank suggestions by exact prefix, approved category and currentness before popularity. A suggestion is a proposed query, not an answer. Display its source type so a document title is not confused with a verified fact. [[retrieval-ai/lexical-analyzers-field-scoring-and-identifier-safety|Lexical identifier safety]] provides the corresponding search behavior."),
            ("Bound work at typing speed", "Autocomplete runs for partial inputs, so it can issue many requests per user. Require a meaningful minimum prefix, debounce client requests, cancel stale responses and cap returned items. The server must still rate-limit and enforce length limits because clients can bypass the browser. A trie, edge n-gram index or specialized completion structure can avoid scanning the full vocabulary. Compare its memory and rebuild cost with observed traffic; a small approved catalog may work with a simple sorted prefix scan."),
            ("Evaluate visibility and usefulness separately", "Test suggestions for common prefixes, typos, IDs, multilingual scripts and document removals. Verify that a restricted title never appears in another tenant's menu, network response or analytics log. Measure acceptance and downstream search success by query slice, but do not treat acceptance as relevance proof: prominent suggestions can influence what users choose. [[retrieval-ai/click-feedback-position-bias-and-offline-evaluation|Position bias]] applies to menus too. A suggestion that raises clicks while suppressing rare but valid queries can make retrieval worse."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class ApprovedSuggestion:
    text: str
    tenant: str
    current: bool

def suggest(prefix: str, authenticated_tenant: str,
            catalog: list[ApprovedSuggestion], limit: int = 5) -> list[str]:
    normalized = prefix.strip().casefold()
    if len(normalized) < 3 or not 1 <= limit <= 8:
        return []
    matches = (item.text for item in catalog
               if item.tenant == authenticated_tenant and item.current
               and item.text.casefold().startswith(normalized))
    return sorted(set(matches), key=lambda value: (len(value), value))[:limit]

catalog = [
    ApprovedSuggestion("Pump P-47 seal guide", "north", True),
    ApprovedSuggestion("Pump P-48 pressure limits", "north", True),
    ApprovedSuggestion("Pump P-47 incident", "south", True),
    ApprovedSuggestion("Pump P-42 retired", "north", False),
]
assert suggest("Pump P-4", "north", catalog) == [
    "Pump P-47 seal guide", "Pump P-48 pressure limits"]''',
        "cost": "This demonstration scans A approved suggestions in O(A) time and uses O(M) memory for M matched strings before sorting them in O(M log M) time. A prefix index can reduce lookup work, but consumes storage and must track updates and revocations. The same current authorization check remains necessary after lookup. Client-side debouncing reduces normal request volume, not server-side abuse; rate limits and minimum prefix length must be enforced by the service.",
        "mistakes": ["Building public suggestions directly from raw search logs.", "Filtering restricted suggestions only after returning them to the browser.", "Assuming browser autocomplete settings protect server-side query history.", "Letting a generic tokenizer strip significant punctuation from product IDs."],
        "drill": "Create 74 approved titles, 12 removed titles and two tenant scopes. Test 20 prefixes, including punctuation-heavy IDs and a restricted unique prefix; inspect both response payloads and logs for leaks.",
        "related": [prefix + "safe-search-query-parsing-and-literal-identifiers", prefix + "lexical-analyzers-field-scoring-and-identifier-safety", prefix + "multi-tenant-retrieval-isolation-and-shard-routing", prefix + "click-feedback-position-bias-and-offline-evaluation"],
    },
    {
        "slug": "hnsw-candidate-budgets-and-ann-recall-curves",
        "title": "HNSW retrieval: candidate budgets, graph cost and recall curves",
        "summary": "Tune approximate vector search against an exact baseline while separating construction, traversal and filter effects.",
        "sections": [
            ("Approximate search trades work for missed neighbors", "An HNSW index connects vectors in a layered graph so a search can follow promising neighbors instead of scoring every vector. The returned top-K is approximate: a closer vector may remain unexplored. Increasing the search candidate budget often improves recall but adds distance computations, memory traffic and tail latency. The exact baseline is a full similarity scan over the eligible corpus. A graph result should be measured against that baseline using the same embedding version and permission filters. [[retrieval-ai/filtered-ann-recall-and-latency|Filtered ANN]] covers the additional difficulty of finding neighbors after an access or metadata filter."),
            ("Separate build knobs from query knobs", "The graph connection limit controls how many edges a node retains, while a construction search width controls how broadly neighbors are considered as the index is built. Larger values can improve connectivity but raise memory and ingestion work. The query-time candidate budget controls exploration for one search; changing it does not rebuild a poor graph. Implementations use different parameter names and defaults, so record the actual backend version and settings with each benchmark. [[retrieval-ai/embedding-space-version-and-migration|Embedding version]] must be held fixed while tuning the graph."),
            ("Measure recall by query slice", "For each judged query, compare approximate top-K IDs with exact top-K IDs and compute overlap or labeled relevant-document recall. Include dense clusters, rare outliers, near duplicates and recently inserted vectors. Report p50 and p95 latency, distance computations, graph bytes and index build time for each budget. An average score can hide a recall collapse on filtered or rare-identifier queries. If vectors are quantized, isolate compression loss by comparing exact search on compressed vectors with exact search on original vectors. [[retrieval-ai/vector-quantization-recall-and-exact-reranking|Quantization]] is a separate source of error."),
            ("Do not confuse global recall with authorized recall", "An unrestricted graph can find nearby documents that a user cannot view. Removing them after top-K may leave too few eligible hits. Raise the exploration budget, use an engine with filter-aware traversal, or search a suitable tenant partition; benchmark each choice at a fixed latency cap. The final result must pass a fresh authorization check even when traversal used an authorized partition. [[retrieval-ai/multi-tenant-retrieval-isolation-and-shard-routing|Tenant layout]] changes both recall and security boundaries."),
            ("Use a controlled sweep, then freeze a gate", "Sweep several search budgets while keeping corpus, queries, model, K and hardware fixed. Reject settings that fail a minimum recall slice or p95 latency budget. Re-run after large ingestion batches, graph rebuilds and backend upgrades, because segment layout and deleted-node patterns can change traversal. Use a smaller candidate budget only when measured savings matter and the lost evidence is acceptable. [[retrieval-ai/retrieval-release-evaluation-and-slice-gates|Release gates]] should capture that decision rather than one attractive benchmark chart."),
        ],
        "code": '''from math import sqrt

def cosine(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = sqrt(sum(value * value for value in left))
    right_norm = sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        raise ValueError("zero vector has no cosine similarity")
    return numerator / (left_norm * right_norm)

def exact_top_k(query: tuple[float, ...],
                vectors: dict[str, tuple[float, ...]],
                allowed_ids: set[str], k: int) -> list[str]:
    if k < 1 or not query or not all(len(v) == len(query) for v in vectors.values()):
        raise ValueError("invalid vector dimensions or K")
    scored = [(item_id, cosine(query, vector))
              for item_id, vector in vectors.items() if item_id in allowed_ids]
    return [item_id for item_id, _ in sorted(
        scored, key=lambda item: (-item[1], item[0]))[:k]]

vectors = {"pump-p47": (.9, .1), "pump-p48": (.5, .5),
           "pump-p49": (.1, .9), "private-plan": (1.0, 0.0)}
gold = exact_top_k((1.0, .1), vectors,
                   {"pump-p47", "pump-p48", "pump-p49"}, 2)
approximate = ["pump-p48", "pump-p47"]
recall_at_two = len(set(gold) & set(approximate)) / len(gold)
assert gold == ["pump-p47", "pump-p48"]
assert recall_at_two == 1.0''',
        "cost": "For N eligible vectors of dimension D, the exact baseline takes O(ND + N log N) time with full sorting and O(N) space for scores; top-K selection can reduce the ranking term. HNSW typically visits far fewer vectors, but its practical work depends on graph connectivity, candidate budget, filtering and segment layout rather than a universal constant bound. The code computes an exact benchmark, not an HNSW implementation. The candidate list represents output from an ANN engine and must be obtained from that engine in a real sweep.",
        "mistakes": ["Calling a larger query budget a fix for an incompatible embedding version.", "Measuring overlap against an unrestricted exact baseline when users have access filters.", "Reporting only average latency while p95 degrades.", "Attributing quantization errors to graph traversal without a separate exact comparison."],
        "drill": "For 97 labeled queries, sweep four candidate budgets with K fixed at 12. Report exact-overlap recall and judged recall by tenant and rare-query slice, plus p95 latency, build time and graph memory.",
        "related": [prefix + "filtered-ann-recall-and-latency", prefix + "vector-quantization-recall-and-exact-reranking", prefix + "embedding-space-version-and-migration", prefix + "retrieval-release-evaluation-and-slice-gates"],
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
        "featured": False, "sort_order": 8469 + offset, "status": "published",
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
    row["data"]["modules"].append({"title": "Facets, tenant isolation, suggestions and graph search", "lessons": new_paths})
    row["body"] += '<h2>Facets, tenant isolation, suggestions and graph search</h2><ul>' + ''.join(
        f'<li>{link(target)}</li>' for target in new_paths) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "chunk-identity-and-context-boundaries": [new_paths[0]],
    prefix + "corpus-permissions-and-document-lifecycle": [new_paths[1]],
    prefix + "safe-search-query-parsing-and-literal-identifiers": [new_paths[2]],
    prefix + "filtered-ann-recall-and-latency": [new_paths[3]],
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
