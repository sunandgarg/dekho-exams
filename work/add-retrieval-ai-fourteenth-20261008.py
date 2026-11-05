"""Publish four original lessons on lexical ranking and retrieval recovery."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-retrieval-ai-fourteenth-import-20261008.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "retrieval-ai/"
hub_path = prefix + "retrieval-ai-tutorial"

lessons = [
    {
        "slug": "bm25-term-saturation-length-normalization-and-field-tuning",
        "title": "BM25 ranking: tune term saturation and document length by field",
        "summary": "Understand why repeated terms stop adding much score, why long fields are discounted and how to test lexical settings against judged queries.",
        "sections": [
            ("BM25 scores terms within a field", "BM25 is a lexical ranking function built from term frequency, document frequency and field length. A query term receives more weight when it is uncommon in the indexed corpus; repeated occurrences in one document help, but their marginal gain shrinks. A length factor limits the advantage of a long document that mentions many terms by chance. The exact implementation depends on the search backend, its analyzer, field mapping and shard statistics. Do not treat a BM25 score as a probability or compare it directly with an embedding cosine score. [[retrieval-ai/score-normalization-and-fusion-calibration|Fusion calibration]] needs a separate contract for combining those branches."),
            ("Separate title and body behavior", "A short title and a long manual chapter should not share an unquestioned relevance policy. A repeated word in the chapter is less surprising than the same word in the title, while a title may contain only three useful tokens. Tune fields separately and establish whether title boosts, body norms and exact identifier fields serve different intents. [[retrieval-ai/lexical-analyzers-field-scoring-and-identifier-safety|Field scoring and identifier safety]] covers the mapping boundary: a serial number belongs in an exact field even when nearby descriptive words use BM25. Otherwise a nearly matching serial can outscore the literal one."),
            ("What the two controls actually change", "The parameter k1 controls term-frequency saturation. A larger k1 lets repeated appearances continue contributing for longer; a smaller one reaches a plateau sooner. The parameter b controls the strength of field-length normalization, from no length adjustment at zero to full adjustment at one. Both interact with average field length and the analyzer's token stream. If you change stemming, stopwords or synonym expansion, the underlying frequencies and lengths change too. Hold the analyzer fixed while testing k1 and b, then retest after an analyzer revision. [[retrieval-ai/retrieval-drift-monitoring-and-shadow-evaluation|Shadow evaluation]] can expose unintended ranking movement."),
            ("Use judged queries, not one convincing result", "Build query slices for brief titles, long procedures, rare exact terms, repeated boilerplate and misspelled language. Compare recall at the candidate cutoff, nDCG after ranking and the downstream answer support rate. Repeated footer text can inflate term counts; remove it at extraction or use a separate low-weight field before adjusting k1 to compensate. Watch the rank of a passage that contains the entire answer once versus a long page that repeats one query word many times. [[retrieval-ai/retrieval-evaluation-labels-and-adjudication|Judged labels]] make the comparison inspectable rather than anecdotal."),
            ("Keep the scoring boundary visible", "The example below computes a small-corpus BM25 term score so the parameter effect is observable. It is not a substitute for your engine's explain output: production engines may use field-specific norms, shard-local statistics, overlap-token rules or different treatment of query-term frequency. Record the index generation, analyzer revision, field, k1 and b with every experiment. Run the same permissions and filters in both variants. Otherwise a relevance regression may actually be a candidate-set change. If BM25 recall is weak for paraphrases, add a vector branch and judge its contribution; do not force lexical tuning to solve semantic mismatch."),
        ],
        "code": '''from collections import Counter
from math import log

def bm25_rank(query: str, manuals: dict[str, str],
              k1: float = 1.3, b: float = 0.68) -> list[tuple[str, float]]:
    if not manuals or k1 <= 0 or not 0 <= b <= 1:
        raise ValueError("invalid corpus or BM25 settings")
    tokens = {manual_id: text.casefold().split()
              for manual_id, text in manuals.items()}
    average_length = sum(map(len, tokens.values())) / len(tokens)
    query_terms = set(query.casefold().split())
    scores = []
    for manual_id, words in tokens.items():
        counts = Counter(words)
        length_factor = 1 - b + b * len(words) / average_length
        score = 0.0
        for term in query_terms:
            document_frequency = sum(term in other for other in tokens.values())
            if not document_frequency or not counts[term]:
                continue
            idf = log(1 + (len(tokens) - document_frequency + .5)
                      / (document_frequency + .5))
            score += idf * counts[term] * (k1 + 1) / (
                counts[term] + k1 * length_factor)
        scores.append((manual_id, score))
    return sorted(scores, key=lambda item: (-item[1], item[0]))

manuals = {"pump-47": "seal pressure service",
           "pump-81": "seal seal seal inventory inventory inventory"}
ranked = bm25_rank("seal pressure", manuals)
assert ranked[0][0] == "pump-47"
assert ranked[0][1] > ranked[1][1]''',
        "cost": "This deliberately small implementation tokenizes T total words in O(T) time and stores O(T) tokens. It scans all N documents for document frequency inside every document/query-term pair, so scoring takes O(N squared times Q plus T) time for Q distinct query terms; sorting adds O(N log N). A real inverted index stores document frequency once and scores only candidate postings. Field norms and postings use storage, while larger candidate windows increase latency. Tune on measured queries before spending search capacity on a larger window.",
        "mistakes": ["Treating a BM25 score as a calibrated probability or adding it directly to a vector score.", "Tuning k1 to hide repeated footer text instead of cleaning the indexed field.", "Changing the analyzer and BM25 parameters in the same evaluation run.", "Applying body-field length settings to short titles and exact identifiers without separate tests."],
        "drill": "For 83 judged maintenance queries, compare two k1/b pairs while holding tokenization and filters fixed. Report candidate recall at 24, nDCG at 8 and the number of exact identifiers displaced. Inspect at least ten individual ranking explanations before release.",
        "related": [prefix + "lexical-analyzers-field-scoring-and-identifier-safety", prefix + "score-normalization-and-fusion-calibration", prefix + "retrieval-evaluation-labels-and-adjudication", prefix + "hybrid-search-and-reciprocal-rank-fusion"],
    },
    {
        "slug": "phrase-proximity-retrieval-and-token-position-contracts",
        "title": "Phrase and proximity retrieval need a token-position contract",
        "summary": "Store positions when word order matters, keep analyzer behavior consistent and test phrase boundaries before using matches as evidence.",
        "sections": [
            ("A term match forgets order", "A record-level inverted index can find documents containing both words but cannot tell whether they occur together. A phrase query needs token positions, or a slower scan of candidate text. A proximity query also asks how far apart matching terms may be. These are materially different retrieval contracts: a maintenance note about a pressure seal and a note about pressure testing a different seal may share terms without containing the requested phrase. [[retrieval-ai/lexical-analyzers-field-scoring-and-identifier-safety|Lexical field mappings]] should declare which fields retain positions and which remain exact identifiers."),
            ("Index-time positions must match query analysis", "Lowercasing, punctuation splitting, stemming, synonyms and stopword removal affect the position stream. If stopwords are removed, preserving their position gaps avoids treating two formerly separated words as adjacent. Query analysis must apply the intended counterpart of the index analyzer; mismatched tokenization can make a visible phrase unsearchable. Synonyms with multiple tokens need explicit position handling, not a string replacement that loses order. For code, part numbers and quoted literals, an exact subfield may be safer than a linguistic analyzer. [[retrieval-ai/safe-search-query-parsing-and-literal-identifiers|Literal query parsing]] keeps quotation marks from becoming accidental broad search."),
            ("Scope positions to an evidence unit", "A phrase must not cross from one field into another or from one unrelated document chunk into the next. Store positions within a field and keep a stable document or passage identity alongside them. If a long manual is split into passages, a phrase at the split boundary can be missed; controlled overlap or parent-document verification can recover it. [[retrieval-ai/chunk-boundary-overlap-and-answer-span-evaluation|Chunk boundary tests]] quantify that tradeoff. Conversely, concatenating unrelated fragments can manufacture a phrase that no source actually says. Show the source span that matched before using it in an answer."),
            ("Proximity is not proof of a relationship", "Allowing a few positions between terms can improve recall for expressions such as 'seal at high pressure', but a wide window may join terms from separate clauses or opposite statements. Decide whether order matters, define an explicit distance or slop policy, and test negation and section boundaries. Backends differ in how they count a transposition or removed stopword; copy neither a numeric setting nor an intuition between engines without fixtures. [[retrieval-ai/claim-level-citation-and-support-checks|Claim support checks]] still have to read the actual sentence. A positional hit is only a retrieval signal."),
            ("Measure the storage and latency price", "Positions increase posting size compared with document-only or frequency-only indexing. Phrase evaluation first intersects candidate postings, then checks compatible positions; common terms and wide proximity windows can still be expensive. Keep the phrase field narrow when possible and add budgets for broad queries. Compare exact phrase recall, near-phrase recall and false joins on judged queries. A high match count may mean the analyzer removed discriminating tokens. Inspect the position stream and original character offsets separately; token positions locate a term order, whereas offsets locate text for highlighting. [[retrieval-ai/search-snippets-highlighting-offsets-and-redaction|Snippet offsets]] have their own redaction rules."),
        ],
        "code": '''import re
from collections import defaultdict

def tokenize(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", value.casefold())

def positional_index(notes: dict[str, str]
                     ) -> dict[str, dict[str, list[int]]]:
    postings = defaultdict(lambda: defaultdict(list))
    for note_id, text in notes.items():
        for position, term in enumerate(tokenize(text)):
            postings[term][note_id].append(position)
    return postings

def exact_phrase(postings: dict, phrase: str) -> set[str]:
    terms = tokenize(phrase)
    if not terms:
        return set()
    candidates = set(postings.get(terms[0], {}))
    for term in terms[1:]:
        candidates &= set(postings.get(term, {}))
    return {note_id for note_id in candidates
            if any(all(start + offset in postings[term][note_id]
                       for offset, term in enumerate(terms))
                   for start in postings[terms[0]][note_id])}

notes = {"work-47": "Inspect the pressure seal before restart",
         "work-81": "Seal the valve after pressure testing"}
postings = positional_index(notes)
assert exact_phrase(postings, "pressure seal") == {"work-47"}
assert exact_phrase(postings, "seal pressure") == set()''',
        "cost": "Building positions for T tokens takes O(T) time and O(T) posting entries. This simple phrase check intersects document sets and then scans first-term positions; list membership is linear, so a document with many repeated terms can require O(P times Q times P) work for P first-term positions and Q phrase terms. Production engines use ordered or compressed positional postings and merge walks to avoid those repeated linear membership checks. Indexing offsets as well as positions raises storage further. Phrase query cost should be measured on common-term and long-field slices.",
        "mistakes": ["Assuming a document-level term intersection proves that the words form a phrase.", "Removing stopwords while collapsing the position gaps they occupied.", "Allowing a phrase to span unrelated chunks or fields.", "Treating a proximity hit as proof that the retrieved sentence supports an answer."],
        "drill": "Create 71 phrase queries that include punctuation, stopwords, part numbers, negation and a passage boundary. Compare exact matches against the visible source text, then measure false joins when allowing one and three extra positions.",
        "related": [prefix + "lexical-analyzers-field-scoring-and-identifier-safety", prefix + "safe-search-query-parsing-and-literal-identifiers", prefix + "chunk-boundary-overlap-and-answer-span-evaluation", prefix + "search-snippets-highlighting-offsets-and-redaction"],
    },
    {
        "slug": "retrieval-result-collapse-document-grouping-and-candidate-depth",
        "title": "Collapse retrieval results by document without losing the best passage",
        "summary": "Group passage hits by a stable parent ID, budget enough candidates for distinct documents and keep permission filtering ahead of grouping.",
        "sections": [
            ("Passage rank is not document rank", "A long source can contribute many similar passages to the top results. If the interface promises a set of documents but displays every passage separately, one manual may occupy the entire first page. Result collapse selects one representative hit per stable parent document, commonly the highest-ranked eligible passage. That improves source variety for browsing, but it can hide a second passage from the same document that contains another required fact. [[retrieval-ai/context-packing-and-evidence-diversity|Evidence packing]] should retain supporting spans when answer generation needs them even if navigation shows one card per document."),
            ("Filter before choosing representatives", "Permission and deletion checks apply to every candidate passage before grouping. A private high-score passage must not be selected as the document representative, and its existence must not leak through group counts or 'more from this document' links. Use a tenant-scoped document key where IDs can collide across tenants. A representative should carry its passage ID, source revision and the exact score branch that produced it. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Corpus permissions]] and [[retrieval-ai/retrieval-index-tombstones-compaction-and-delete-proof|delete tombstones]] remain authoritative even when a grouping API operates inside the search engine."),
            ("Candidate depth sets the diversity ceiling", "Collapsing a top-12 passage pool cannot return twelve documents if ten passages came from one manual. Retrieve deeper, group, then take the requested number of distinct parents, or use a backend feature that performs collapse before final top-K selection. Oversampling has a latency cost and no fixed multiplier guarantees diversity for every query. Track unique-parent count at several candidate depths. If a rare document never entered the pool, post-processing cannot recover it. [[retrieval-ai/reranker-candidate-window-and-budget|Reranker windows]] need the same distinction between passage count and unique-source count."),
            ("Choose a deterministic representative", "Within a group, rank by the retrieval score or a reranked score under one stable policy, then break ties by passage ID or source order. Keep the original passage score visible to diagnostics. When multiple passages from the same source answer different aspects, offer an explicit expansion rather than quietly merging fragments into one invented excerpt. Near-duplicate documents from distinct parents require a separate duplicate policy. [[retrieval-ai/near-duplicate-evidence-and-independent-support|Independent support]] explains why two copies of the same text are not two independent sources. Collapse is for presentation and candidate allocation; it does not establish source independence."),
            ("Counts and pagination require a contract", "A result count before collapse may describe passages, not distinct documents. Facet counts can also reflect the uncollapsed set, depending on the backend. Label the unit in the UI and avoid promising an exact number of groups unless you compute it. Paginating grouped hits needs a stable sort and a consistent index view; a changing candidate pool can repeat or skip documents. [[retrieval-ai/stable-search-pagination-point-in-time-and-cursors|Point-in-time pagination]] sets that boundary. Evaluate grouped recall and answer support alongside visual variety, because hiding duplicate cards is useful only when important evidence remains reachable."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class PassageHit:
    tenant_id: str
    document_id: str
    passage_id: str
    score: float
    permitted: bool

def distinct_documents(hits: list[PassageHit], limit: int
                       ) -> list[PassageHit]:
    if limit < 0:
        raise ValueError("negative result limit")
    best = {}
    for hit in hits:
        if not hit.permitted:
            continue
        key = (hit.tenant_id, hit.document_id)
        current = best.get(key)
        if current is None or (-hit.score, hit.passage_id) < (
                -current.score, current.passage_id):
            best[key] = hit
    return sorted(best.values(), key=lambda hit: (
        -hit.score, hit.tenant_id, hit.document_id, hit.passage_id))[:limit]

hits = [PassageHit("plant-a", "manual-47", "p2", .81, True),
        PassageHit("plant-a", "manual-47", "p4", .88, True),
        PassageHit("plant-a", "manual-81", "p1", .95, False),
        PassageHit("plant-a", "manual-94", "p3", .76, True)]
chosen = distinct_documents(hits, 2)
assert [(hit.document_id, hit.passage_id) for hit in chosen] == [
    ("manual-47", "p4"), ("manual-94", "p3")]''',
        "cost": "For C candidate passages, grouping takes O(C) expected time and O(G) space for G eligible parent groups; sorting those groups costs O(G log G). The code assumes the caller already fetched candidates and made permission decisions. A deeper candidate pool increases search, transport and rerank costs, while backend inner-hit expansion may issue additional searches. Measure distinct-parent yield at each depth and keep a latency budget. If authorization is unavailable, fail closed before this function rather than treating an absent permission as true.",
        "mistakes": ["Collapsing before permission checks and leaking the identity of a private document.", "Fetching only K passages and assuming K distinct parent documents will remain.", "Reporting raw passage hit counts as distinct-document counts.", "Discarding other passages from a parent when the answer requires evidence from more than one span."],
        "drill": "Construct 64 queries whose top 30 passages include repeated manuals and near duplicates. Compare document recall at 8, unique-parent yield and answer support before and after grouping; inject one forbidden highest-scoring passage per test group.",
        "related": [prefix + "context-packing-and-evidence-diversity", prefix + "near-duplicate-evidence-and-independent-support", prefix + "stable-search-pagination-point-in-time-and-cursors", prefix + "corpus-permissions-and-document-lifecycle"],
    },
    {
        "slug": "retrieval-index-backup-restore-and-relevance-proof",
        "title": "Restore a retrieval index with schema, deletion and relevance proofs",
        "summary": "Treat a backup as a candidate generation: verify its metadata, replay later changes and test search quality before cutover.",
        "sections": [
            ("A snapshot is not an answer-ready index", "A backup can preserve index bytes while still being too old, mapped to the wrong embedding model or missing the latest permission and deletion events. Define recovery point and recovery time objectives for the retrieval service, then name every component needed to meet them: source documents, lexical and vector indexes, analyzers, embedding version, access-control state, aliases and change logs. An index archive alone cannot prove that restored results are safe. [[retrieval-ai/embedding-space-version-and-migration|Embedding version contracts]] must match the query encoder before vector traffic returns."),
            ("Capture a consistent generation", "Record an index generation ID, source watermark, schema revision, tokenizer or analyzer revision, embedding dimension, metric and document count with the backup. Use the backend's supported snapshot mechanism rather than copying live index files while writers are active. Protect the backup repository and test that its credentials and keys are available during recovery. A snapshot taken before an ingestion event is valid only if later events can be replayed from a durable log. [[retrieval-ai/index-watermarks-freshness-slos-and-stale-answer-policy|Watermarks]] show what the restored service has and has not seen."),
            ("Restore beside production first", "Restore into a separate generation or name so the current serving alias remains unchanged. Verify manifest checksums and active document IDs, then replay updates and tombstones through the target watermark. A stale backup must not revive a deleted document, even temporarily. Apply the current permission policy and compare source revisions, not just document totals; equal counts can conceal one missing and one duplicated record. [[retrieval-ai/retrieval-index-tombstones-compaction-and-delete-proof|Deletion proof]] is mandatory before the target accepts user queries. The old serving generation remains available until cutover checks pass."),
            ("Run retrieval and access canaries", "A restored index may open successfully but rank badly because field norms, vector metric, analyzers or reranker inputs changed. Run exact identifier queries, phrase queries, filtered ANN probes and judged answer-support tests under the restored generation. Include forbidden-document canaries and intentionally deleted IDs. Compare top-K overlap and important slices against the last known good release, while allowing expected freshness changes after replay. [[retrieval-ai/retrieval-release-evaluation-and-slice-gates|Release gates]] define minimum quality; a green cluster status is not a relevance proof."),
            ("Switch, observe, and rehearse", "Move the serving alias only after eligibility, freshness and quality checks pass. Pin or finish in-flight requests so a single answer does not combine evidence from different generations. Keep a rollback target only if it also applies the current tombstones and permissions; an unsafe rollback is not a recovery path. [[retrieval-ai/retrieval-index-alias-cutover-and-rollback|Alias cutover]] covers the pointer switch. Rehearse restore regularly, measuring time to first safe query, missing-event replay duration and storage headroom. A backup that has never been restored is an untested assumption."),
        ],
        "code": '''from dataclasses import dataclass
from hashlib import sha256

@dataclass(frozen=True)
class IndexedRecord:
    document_id: str
    revision: int
    content_digest: str

@dataclass(frozen=True)
class RestoreManifest:
    source_watermark: int
    schema_revision: str
    embedding_revision: str
    active_digest: str

def active_digest(records: list[IndexedRecord],
                  deleted_ids: set[str]) -> str:
    active = [record for record in records
              if record.document_id not in deleted_ids]
    keys = [(record.document_id, record.revision, record.content_digest)
            for record in active]
    if len({key[0] for key in keys}) != len(keys):
        raise ValueError("duplicate active document")
    payload = "\\n".join(f"{item[0]}:{item[1]}:{item[2]}"
                       for item in sorted(keys))
    return sha256(payload.encode()).hexdigest()

def verify_restore(records: list[IndexedRecord],
                   manifest: RestoreManifest, deleted_ids: set[str],
                   required_watermark: int) -> None:
    if manifest.source_watermark < required_watermark:
        raise ValueError("event replay is incomplete")
    if (manifest.schema_revision != "schema-7" or
            manifest.embedding_revision != "encoder-4"):
        raise ValueError("incompatible retrieval contract")
    if any(record.document_id in deleted_ids for record in records):
        raise ValueError("deleted document remains in index")
    if active_digest(records, deleted_ids) != manifest.active_digest:
        raise ValueError("restored content differs from manifest")

restored = [IndexedRecord("manual-47", 3, "sha-47")]
manifest = RestoreManifest(219, "schema-7", "encoder-4",
                           active_digest(restored, set()))
verify_restore(restored, manifest, {"withdrawn-81"}, 219)''',
        "cost": "Sorting N active record descriptors for the digest takes O(N log N) time and O(N) memory; a backend can use ordered scans and streaming hashes to reduce extra memory. Snapshot creation, transfer, replay and vector reconstruction have separate I/O and CPU costs that depend on the engine. The code checks metadata and a manifest digest but does not perform storage-level restore, cryptographic signature verification, authorization or relevance tests. Those remain required gates before alias cutover. Track both recovery time and the age of the latest safe recovered watermark.",
        "mistakes": ["Copying a live index directory as if it were an atomic backup.", "Restoring old data without replaying later deletions and permission changes.", "Checking document counts but not IDs, revisions, schema and model compatibility.", "Switching the serving alias before access canaries and judged retrieval tests pass."],
        "drill": "Restore a backup from 47 ingestion events before the current watermark into a separate generation. Replay those events, delete seven records, run permission canaries and 39 judged queries, and record the time until the restored service can answer safely.",
        "related": [prefix + "retrieval-index-alias-cutover-and-rollback", prefix + "index-watermarks-freshness-slos-and-stale-answer-policy", prefix + "retrieval-index-tombstones-compaction-and-delete-proof", prefix + "retrieval-release-evaluation-and-slice-gates"],
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
        "featured": False, "sort_order": 8477 + offset, "status": "published",
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
    row["data"]["modules"].append({"title": "Lexical ranking, result grouping and recovery", "lessons": new_paths})
    row["body"] += '<h2>Lexical ranking, result grouping and recovery</h2><ul>' + ''.join(
        f'<li>{link(target)}</li>' for target in new_paths) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "lexical-analyzers-field-scoring-and-identifier-safety": [new_paths[0], new_paths[1]],
    prefix + "context-packing-and-evidence-diversity": [new_paths[2]],
    prefix + "retrieval-index-alias-cutover-and-rollback": [new_paths[3]],
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
