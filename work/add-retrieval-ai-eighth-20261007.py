"""Add original retrieval lessons for analyzers, compression, snapshots and corpus trust."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-retrieval-ai-eighth-import-20261007.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "retrieval-ai/"
hub_path = prefix + "retrieval-ai-tutorial"

lessons = [
    {
        "slug": "lexical-analyzers-field-scoring-and-identifier-safety",
        "title": "Lexical retrieval: analyzers, fields and exact identifiers",
        "summary": "Keep text analysis and exact identifiers separate so keyword retrieval finds the right record without changing its identity.",
        "sections": [
            ("Define an analyzer contract", "A lexical analyzer converts source text and query text into comparable terms. Character cleanup, tokenization, case handling, stop words and synonym expansion all affect which documents can enter the candidate set. Record the analyzer version alongside the index; otherwise a query may be analyzed differently from the stored text after a configuration change. A simple token list is useful for an experiment, but a production inverted index also stores postings, field identity and often positions for phrase matching. [[retrieval-ai/hybrid-search-and-reciprocal-rank-fusion|Hybrid retrieval]] only benefits from its lexical arm when that arm can actually find the required term."),
            ("Do not normalize away identifiers", "A part number such as P-47 is an identity constraint, not a bag of words. If punctuation splitting turns it into P and 47, a document about pump P-48 and drawing 47 can appear relevant. Store the canonical part ID in a keyword field with a deliberately narrow normalizer, and filter on it before ranking free text. Preserve the original display form for citations. Likewise, tenant, revision and document status belong in typed fields rather than prose. [[retrieval-ai/entity-linking-aliases-and-ambiguous-mentions|Entity linking]] may resolve aliases, but it must not silently replace a verified identifier with a nearby one."),
            ("Score fields for their job", "A match in a reviewed title can deserve more weight than the same term buried in an attachment, but a title boost is not a permission or authority signal. Production BM25-style scoring accounts for term frequency, rarity and field length; field boosts then express how the application values each field. Apply hard eligibility filters first. Evaluate title-only, body-only and identifier-only queries separately so one tuned score does not hide a severe miss. [[retrieval-ai/reranker-candidate-window-and-budget|Reranking]] cannot recover a document that lexical candidate generation excluded."),
            ("Treat synonyms as a release change", "Search-time synonyms may improve recall for a controlled vocabulary, yet broad expansion can replace a specific engineering term with a general word and flood the candidate window. Test both index and search analysis with golden token streams, especially multiword synonyms, units and abbreviations. Version the rule set and record which rule produced an expanded term in the trace. Keep exact identity filters outside synonym expansion. [[retrieval-ai/query-expansion-guardrails-and-drift-tests|Expansion drift tests]] should catch queries that begin retrieving a different asset family after a new synonym is deployed."),
            ("Measure candidate failure before answer failure", "Build judged queries with misspellings, plural forms, hyphenated identifiers, long titles and repeated boilerplate. Measure eligible recall at the lexical candidate boundary and compare it with downstream supported answers. Inspect misses by analyzer version and field. A correct answer that came from a vector candidate does not prove the lexical index is healthy. During a migration, run old and new analyzers on the same snapshot and retain the old path until the new one passes the required slices."),
        ],
        "code": '''from collections import Counter
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class ManualRecord:
    document_id: str
    part_id: str
    title: str
    body: str

def terms(text: str) -> Counter[str]:
    return Counter(re.findall(r"[a-z0-9]+", text.casefold()))

def rank_manuals(records: list[ManualRecord], query: str,
                 required_part_id: str) -> list[tuple[str, int]]:
    query_terms = terms(query)
    scores = []
    for record in records:
        if record.part_id.casefold() != required_part_id.casefold():
            continue
        title_terms, body_terms = terms(record.title), terms(record.body)
        score = sum(min(count, title_terms[term]) * 4
                    + min(count, body_terms[term])
                    for term, count in query_terms.items())
        if score:
            scores.append((record.document_id, score))
    return sorted(scores, key=lambda item: (-item[1], item[0]))

manuals = [
    ManualRecord("pump-p47-r4", "P-47", "P-47 seal pressure", "inspect the seal"),
    ManualRecord("pump-p48-r4", "P-48", "P-48 seal pressure", "drawing 47"),
]
assert rank_manuals(manuals, "seal pressure", "P-47") == [("pump-p47-r4", 9)]
assert rank_manuals(manuals, "seal pressure", "P-49") == []''',
        "cost": "Building an inverted index is proportional to the indexed term count and stores postings in addition to source text. The standard-library demonstration scans N records with L terms each, costing O(NL) time and O(N) result space; it is intentionally a contract check, not a replacement for an inverted index or BM25. A keyword filter narrows the eligible set before ranking, while broader synonym rules increase postings visited and candidate pressure.",
        "mistakes": ["Using a text analyzer for an exact part ID or tenant key.", "Changing query tokenization without testing compatibility with indexed terms.", "Treating a title boost as proof that a document is authoritative.", "Measuring only final answer quality while the lexical candidate pool loses required evidence."],
        "drill": "Create 53 queries covering hyphens, aliases, plurals, units and title/body conflicts. Compare old and new analyzer token streams, exact-ID recall and eligible recall at the candidate boundary.",
        "related": [prefix + "hybrid-search-and-reciprocal-rank-fusion", prefix + "entity-linking-aliases-and-ambiguous-mentions", prefix + "query-expansion-guardrails-and-drift-tests", prefix + "retrieval-recall-and-reranking"],
    },
    {
        "slug": "vector-quantization-recall-and-exact-reranking",
        "title": "Vector compression: spend memory without losing the answer",
        "summary": "Measure how compressed vectors change candidate recall, then recover ordering with exact reranking where the budget permits.",
        "sections": [
            ("Separate storage from ranking quality", "A dense index can store full precision vectors or compressed codes. Product quantization and related codecs reduce per-vector storage by representing a vector with learned codebook entries, but the distance computed from a code is approximate. A smaller index does not automatically mean a better service: a support document that falls out of the candidate set cannot be rescued by the language model. Keep the original vector ID, embedding-model version and source revision alongside each compressed code. [[retrieval-ai/embedding-space-version-and-migration|Embedding migration]] must rebuild or isolate incompatible spaces."),
            ("Budget the entire resident index", "A 768-dimensional float32 vector uses 3,072 raw bytes before IDs, graph edges, partition metadata or replicas. A 48-byte code plus an eight-byte ID looks much smaller, but codebooks, coarse centroids, filtering structures and a raw-vector store for reranking still consume memory. Estimate each component against the actual number of vectors and replicas. If exact reranking reads remote raw vectors, account for that I/O in tail latency. [[retrieval-ai/filtered-ann-recall-and-latency|Filtered ANN]] can lose still more candidates after permission or category constraints narrow the search space."),
            ("Use two stages deliberately", "Retrieve a larger candidate set using compressed distances, apply eligibility filters, then compute exact similarity on the surviving vectors before final ranking. The second stage corrects ordering errors only when the correct item survived stage one. Increasing the approximate candidate count raises memory reads and exact-score work; it is not a free recall fix. Keep the rerank window tied to latency and access budgets. [[retrieval-ai/reranker-candidate-window-and-budget|Candidate-window design]] makes this trade measurable rather than setting one global top-K by habit."),
            ("Train codes on representative data", "A codebook trained on general prose may compress rare part numbers, source code or other specialized content poorly. Sample from the production distribution without including restricted documents in an unsafe shared training artifact. Evaluate queries by domain, language, document length and freshly added content. Rebuild when the embedding distribution changes enough to shift recall, and compare the new index with a full-precision baseline over the same corpus snapshot. A score difference across codec versions is not directly interpretable as a relevance change."),
            ("Gate on supported evidence", "Measure exact-neighbor recall, answer-bearing passage recall, supported-answer rate, p95 latency and resident bytes together. A codec that preserves average neighbor recall but drops the only passage for safety-critical questions should fail its release slice. Record whether a miss arose in coarse partition selection, code distance, filter application or reranking. Keep a rollback index or a staged rollout until those failures are understood. [[retrieval-ai/retrieval-release-evaluation-and-slice-gates|Release gates]] should include both quality and resource limits."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class VectorCandidate:
    passage_id: str
    approximate_distance: float
    exact_distance: float

def exact_rerank(candidates: list[VectorCandidate], width: int) -> list[str]:
    if width < 1:
        raise ValueError("candidate width must be positive")
    shortlist = sorted(candidates, key=lambda item: item.approximate_distance)[:width]
    return [item.passage_id for item in sorted(
        shortlist, key=lambda item: (item.exact_distance, item.passage_id))]

def storage_bytes(vectors: int, dimension: int, code_bytes: int) -> tuple[int, int]:
    return vectors * dimension * 4, vectors * (code_bytes + 8)

candidates = [
    VectorCandidate("seal-procedure-r4", .18, .08),
    VectorCandidate("seal-catalog-r2", .09, .13),
]
assert exact_rerank(candidates, 2)[0] == "seal-procedure-r4"
assert exact_rerank(candidates, 1)[0] == "seal-catalog-r2"
assert storage_bytes(2_700_000, 768, 48) == (8_294_400_000, 151_200_000)''',
        "cost": "For C retrieved candidates, sorting the approximate stage costs O(C log C), then sorting W shortlisted candidates costs O(W log W), with O(C) working space in this demonstration. Real ANN engines avoid a full corpus sort and add codec decoding and coarse-search costs. The byte calculation excludes codebooks, centroids, graph links, filtering metadata, replicas and any full-precision rerank store; measure those separately before committing to an index size.",
        "mistakes": ["Reporting code bytes as total index memory.", "Assuming exact reranking can restore a relevant item absent from the shortlist.", "Training compression on a corpus unlike the one served.", "Comparing approximate distances from different codecs as if they shared a calibrated scale."],
        "drill": "For 61 judged queries, compare full precision, compressed top-1 and compressed top-12 followed by exact reranking. Record the first lost answer-bearing passage, resident memory and p95 latency per domain.",
        "related": [prefix + "filtered-ann-recall-and-latency", prefix + "embedding-space-version-and-migration", prefix + "reranker-candidate-window-and-budget", prefix + "retrieval-release-evaluation-and-slice-gates"],
    },
    {
        "slug": "snapshot-consistent-multi-index-retrieval",
        "title": "Snapshot-consistent retrieval across changing indexes",
        "summary": "Pin lexical, vector and permission views to a compatible generation before merging evidence or paginating results.",
        "sections": [
            ("Choose an answer-time snapshot", "A retrieval request can span lexical postings, a vector index, metadata storage and a permission service. Each may refresh at a different time. If a document revision enters vector search before its permission update reaches the filter, combining the newest result from every component can create an answer that no coherent system state ever contained. Select a generation or snapshot token that all required components can serve. If one is behind, wait within a bounded budget, fall back to an older common generation, or abstain. [[retrieval-ai/temporal-retrieval-as-of-validity-and-conflicts|Temporal validity]] answers which revision was true at a requested time; snapshot consistency answers which revision the search system actually observed."),
            ("Carry generation through each stage", "Attach generation, document revision, tenant and source ID to candidates, reranker inputs and final citations. A merged list with two revisions of one document is not merely a ranking issue; the reader may be shown mutually incompatible facts. Keep tombstones and permission revocations in the same generation discipline. A cached result must include its snapshot and authorization scope, or it may outlive the state it claims to represent. [[retrieval-ai/permission-aware-cache-and-conversation-turns|Permission-aware caching]] handles the authorization half of this contract."),
            ("Paginate a frozen view", "Offset pagination over a changing index can duplicate or skip documents when new records arrive between page requests. A point-in-time search view and a stable sort key let later pages continue the same result set. Expire the view deliberately and return a restart signal rather than silently switching generations halfway through. A user-facing search may tolerate a short-lived snapshot, while an audit export may need a longer frozen manifest and repeatable IDs. [[retrieval-ai/retrieval-traces-and-incident-debugging|Retrieval traces]] should record snapshot token and page cursor for reconstruction."),
            ("Handle mixed-generation failures", "During a blue-green index swap, query both old and new read paths against the same judged questions before activating the new generation. If vector generation 48 is ready but lexical generation 47 is still serving, a generation-48 hybrid answer is premature. A retry is useful only when the lag is expected to clear within the request budget. Never downgrade permission revocation to an old snapshot just to keep an answer available. Security-critical revocations require current authorization even if content indexes remain pinned. [[retrieval-ai/freshness-deletion-and-index-swap|Index swap controls]] govern when a new generation becomes safe to serve."),
            ("Test observable consistency", "Inject updates between candidate fetch, reranking and pagination. Include a deleted document, a permission withdrawal, a content revision and a vector rebuild that completes later than the lexical refresh. Check that every returned citation resolves to the claimed revision and that all pages share one snapshot. Measure waiting time and abstention separately; an apparently fast system that silently mixes generations has traded correctness for latency without declaring it."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class IndexView:
    name: str
    ready_generation: int

@dataclass(frozen=True)
class SearchHit:
    document_id: str
    revision: str
    generation: int
    source_index: str

def merge_snapshot(views: list[IndexView], hits: list[SearchHit],
                   generation: int) -> dict[str, str]:
    if not views or any(view.ready_generation < generation for view in views):
        raise ValueError("requested generation is not ready everywhere")
    allowed_sources = {view.name for view in views}
    revisions: dict[str, str] = {}
    for hit in hits:
        if hit.source_index not in allowed_sources or hit.generation > generation:
            continue
        previous = revisions.setdefault(hit.document_id, hit.revision)
        if previous != hit.revision:
            raise ValueError("conflicting document revisions in one snapshot")
    return revisions

views = [IndexView("lexical", 48), IndexView("vector", 47)]
hits = [SearchHit("pump-p47", "r4", 47, "lexical"),
        SearchHit("pump-p47", "r4", 47, "vector"),
        SearchHit("pump-p47", "r5", 48, "lexical")]
assert merge_snapshot(views, hits, 47) == {"pump-p47": "r4"}
try:
    merge_snapshot(views, hits, 48)
except ValueError:
    pass
else:
    raise AssertionError("mixed-generation read was accepted")''',
        "cost": "The demonstration scans V component views and H hits in O(V + H) time with O(H) revision space. A real point-in-time view can retain old index segments and add storage pressure for its lifetime; waiting for the slowest component adds tail latency. Limit snapshot duration, expose timeouts and monitor generation lag. A permission revocation must still be checked against current policy even when content retrieval uses an older coherent generation.",
        "mistakes": ["Merging the latest response from each index without a shared generation.", "Using an old permission snapshot after access was revoked.", "Changing generation between search result pages without telling the client.", "Dropping revision IDs before citations are assembled."],
        "drill": "Replay 43 synthetic updates across two indexes and a permission view. Verify citation revisions, page continuity, revocation handling and bounded fallback when one index lags.",
        "related": [prefix + "temporal-retrieval-as-of-validity-and-conflicts", prefix + "freshness-deletion-and-index-swap", prefix + "permission-aware-cache-and-conversation-turns", prefix + "retrieval-traces-and-incident-debugging"],
    },
    {
        "slug": "corpus-poisoning-trust-tiers-and-evidence-admission",
        "title": "Corpus poisoning: admit evidence before ranking it",
        "summary": "Keep adversarial or unreviewed corpus additions from becoming authoritative evidence merely because they rank well.",
        "sections": [
            ("Separate relevance from authority", "Corpus poisoning changes what the retriever can find. An attacker may add a plausible document that repeats the query terms, cites a fake update or embeds a misleading number, without writing an explicit instruction to the assistant. A high similarity score says the passage resembles the question; it says nothing about who published it or whether its claim is approved. Admit evidence through trusted ingestion metadata before ranking it for a consequential answer. [[retrieval-ai/prompt-injection-and-tool-boundary|Prompt-injection controls]] handle instructions inside retrieved text, but a false factual claim can be dangerous even when it contains no command."),
            ("Assign trust at ingestion", "Capture source owner, collection, reviewer state, document signature or checksum, import channel and revision lineage outside the document body. A sentence inside the document claiming to be 'official' is not proof of authority. Give user uploads and external feeds a lower trust tier until their content is reviewed or corroborated under policy. Apply tenant and lifecycle rules before any trust comparison. [[retrieval-ai/source-extraction-and-passage-provenance|Passage provenance]] should let an investigator trace an answer back to the exact admitted source and revision."),
            ("Guard candidate admission", "A poisoned page can still consume the top candidate slots even if a downstream generator refuses its claims. Filter or partition sources by trust tier, then set candidate budgets so lower-trust material cannot crowd out the approved corpus. For exploratory search, show unreviewed material with a clear status; for a policy or safety answer, require an approved evidence tier. If a trusted source and an unreviewed source disagree, do not average their text or choose the one with the more fluent explanation. [[retrieval-ai/context-packing-and-evidence-diversity|Context packing]] should preserve source diversity without confusing diversity with authority."),
            ("Detect suspicious change patterns", "Watch for a burst of new documents that all answer the same rare question, unusual repetition of identifiers, copied authority language, and content whose owner cannot be verified. These signals are review triggers, not automatic proof of attack. Compare new-corpus and previous-corpus answers on stable judged queries, and record which admitted document changed each answer. Quarantine a source by source ID or ingest batch, then rebuild affected candidate stores and caches. [[retrieval-ai/incremental-ingestion-idempotency-and-delete-races|Ingestion controls]] should make quarantine and deletion repeatable."),
            ("Evaluate the admission boundary", "Test harmless user uploads, misleading but relevant documents, forged update notices and contradictions between two approved sources. Judge whether the system finds authorized evidence, labels uncertainty and abstains when approved evidence conflicts. A detector that blocks every new document may reduce attack success while destroying useful recall. Review false positives by source tier and query slice. [[retrieval-ai/counterfactual-retrieval-tests-and-distractor-resilience|Counterfactual tests]] can reveal when an answer changes only because a low-trust passage was introduced."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class EvidenceCandidate:
    source_id: str
    policy_key: str
    value: str
    similarity: float
    verified_origin: bool
    approved_for_answers: bool

def admitted_value(candidates: list[EvidenceCandidate], policy_key: str) -> str | None:
    eligible = [candidate for candidate in candidates
                if candidate.policy_key == policy_key
                and candidate.verified_origin
                and candidate.approved_for_answers]
    values = {candidate.value for candidate in eligible}
    if len(values) > 1:
        raise ValueError("approved sources conflict; require review")
    return next(iter(values)) if values else None

records = [
    EvidenceCandidate("signed-manual-r4", "pump-p47-limit", "83 kPa", .71, True, True),
    EvidenceCandidate("unreviewed-upload-9", "pump-p47-limit", "67 kPa", .99, False, False),
]
assert admitted_value(records, "pump-p47-limit") == "83 kPa"
assert admitted_value(records, "unknown-policy") is None''',
        "cost": "Admission scans C candidates in O(C) time and stores at most O(C) distinct admitted values. In production, source status should usually be indexed so unapproved material is excluded before expensive retrieval and reranking. Provenance verification, review queues and quarantine rebuilds add operational cost, but accepting a high-scoring forged source can corrupt every downstream answer that cites it. Keep metadata server-controlled and audit changes to approval state.",
        "mistakes": ["Reading an 'official' label from document text as if it were verified metadata.", "Letting low-trust candidates fill the entire top-K window before filtering.", "Assuming a prompt-injection detector also catches false factual claims.", "Picking one of two conflicting approved claims solely by similarity score."],
        "drill": "Add 37 synthetic unreviewed documents to a judged corpus. Record which enter the candidate pool, which are admitted for answers, how many legitimate passages are displaced and whether conflicts trigger review.",
        "related": [prefix + "prompt-injection-and-tool-boundary", prefix + "source-extraction-and-passage-provenance", prefix + "context-packing-and-evidence-diversity", prefix + "counterfactual-retrieval-tests-and-distractor-resilience"],
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
        "featured": False, "sort_order": 8453 + offset, "status": "published",
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
    row["data"]["modules"].append({"title": "Lexical scoring, compression, snapshots and trust", "lessons": new_paths})
    row["body"] += '<h2>Lexical scoring, compression, snapshots and trust</h2><ul>' + ''.join(
        f'<li>{link(target)}</li>' for target in new_paths) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "hybrid-search-and-reciprocal-rank-fusion": [new_paths[0]],
    prefix + "filtered-ann-recall-and-latency": [new_paths[1]],
    prefix + "freshness-deletion-and-index-swap": [new_paths[2]],
    prefix + "prompt-injection-and-tool-boundary": [new_paths[3]],
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
