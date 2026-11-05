"""Add original retrieval lessons on IVF, term coverage, and claim conflicts."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-retrieval-ai-fifteenth-import-20261008.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "retrieval-ai/"
hub_path = prefix + "retrieval-ai-tutorial"

lessons = [
    {
        "slug": "ivf-centroid-training-probe-budgets-and-recall",
        "title": "IVF vector search: train centroids, budget probes, measure misses",
        "summary": "Use an inverted-file vector index when partition scans beat a full scan, and evaluate the recall cost of probing fewer cells.",
        "sections": [
            ("IVF partitions vector space", "An inverted-file vector index assigns each stored embedding to a coarse centroid and keeps a posting list for each centroid. At query time, it finds nearby centroids and scans only their lists. The number of lists is commonly called nlist; the number searched for one query is nprobe. Fewer probes reduce candidate distance calculations but can miss a nearest vector assigned to a neighboring cell. This is an approximate candidate-generation decision, not an answer-quality guarantee. Compare results with exact search under the same [[retrieval-ai/vector-similarity-metrics-normalization-and-rank-changes|vector metric and normalization contract]] before drawing conclusions about recall."),
            ("Train on the distribution you intend to serve", "Coarse centroids need representative training vectors from the corpus and embedding model that will actually populate the index. Training only on the first ingestion batch, one language or one high-volume tenant can leave later material in badly balanced cells. Record model revision, dimension, metric, normalization, sample selection and training seed with the index generation. If the embedding distribution changes enough, a fixed centroid set can produce long lists or poor recall even when index size stays constant. [[retrieval-ai/embedding-space-version-and-migration|Embedding migrations]] should rebuild and evaluate the coarse assignment alongside the stored vectors."),
            ("Probe count trades work for recall", "With a small nprobe, a query scans few lists and risks missing candidates near cell boundaries. A larger nprobe visits more lists, costs more CPU and memory bandwidth, and usually improves recall until gains flatten. If nprobe approaches every list, an uncompressed IVFFlat search approaches an exhaustive vector scan while adding coarse-routing overhead. An IVF index with compressed payloads can still differ from an exact flat index because compression changes distances. [[retrieval-ai/vector-quantization-recall-and-exact-reranking|Quantization and exact reranking]] should be measured as a separate source of error rather than folded into the probe-count result."),
            ("Filters and skew alter the effective budget", "A query restricted to one tenant or status may have few eligible vectors in the first probed cells. Some backends filter before vector search, others overfetch and filter afterward; the two plans have different recall and latency behavior. List imbalance also matters: probing four huge cells may scan more vectors than probing eight small ones. Measure eligible candidate count, list-size distribution, probes visited, p95 latency and exact top-K recall by filter slice. [[retrieval-ai/filtered-ann-recall-and-latency|Filtered ANN tests]] expose an apparently fast configuration that returns too few authorized results. Never compensate for a failed permission filter by searching a broader scope."),
            ("Use a release gate, not a magic nprobe", "Select several probe budgets and compare them against exact top-K results on representative queries: common intents, rare terms, new content, multilingual requests and difficult filter combinations. Record both passage recall and downstream supported-answer rate. The best value can differ by index size, hardware and query slice, but per-query adaptation needs a clear ceiling so tail latency remains bounded. [[retrieval-ai/hnsw-candidate-budgets-and-ann-recall-curves|HNSW candidate budgets]] have a related speed-versus-recall shape but use a different search structure. Review both index memory and build time before deciding that IVF is preferable to a graph or flat index."),
        ],
        "code": '''from math import dist

def probe_cells(query: tuple[float, ...],
                centroids: dict[str, tuple[float, ...]],
                postings: dict[str, list[tuple[str, tuple[float, ...]]]],
                nprobe: int, limit: int) -> list[tuple[str, float]]:
    if not query or nprobe < 1 or limit < 1 or nprobe > len(centroids):
        raise ValueError("invalid query or search budget")
    if any(len(vector) != len(query) for vector in centroids.values()):
        raise ValueError("centroid dimension mismatch")
    cells = sorted(centroids, key=lambda cell: (dist(query, centroids[cell]), cell))
    candidates = []
    for cell in cells[:nprobe]:
        for document_id, vector in postings.get(cell, []):
            if len(vector) != len(query):
                raise ValueError("passage dimension mismatch")
            candidates.append((document_id, dist(query, vector)))
    return sorted(candidates, key=lambda item: (item[1], item[0]))[:limit]

centroids = {"west": (0.0, 0.0), "east": (8.0, 0.0)}
postings = {"west": [("manual-47", (2.5, 0.0))],
            "east": [("manual-81", (4.1, 0.0))]}
query = (3.95, 0.0)
assert probe_cells(query, centroids, postings, 1, 1)[0][0] == "manual-47"
assert probe_cells(query, centroids, postings, 2, 2)[0][0] == "manual-81"''',
        "cost": "For C centroids, the toy code scores and sorts all centroids in O(CD + C log C) time for D dimensions, then scores M vectors in the selected lists in O(MD) and sorts them in O(M log M). It uses O(C + M) temporary space. Real implementations use trained coarse quantizers, compressed lists and efficient top-K selection, but the fundamental probe-versus-recall tradeoff remains. The demonstration does not train centroids or enforce filters; those are production responsibilities. Log actual scanned-vector count, because nprobe alone hides cell-size skew.",
        "mistakes": ["Training centroids on vectors from an old embedding model or an unrepresentative tenant.", "Reporting ANN recall against another approximate index instead of an exact baseline.", "Assuming the same nprobe scans the same amount of work for every filtered query.", "Attributing compressed-distance errors entirely to the IVF probe setting."],
        "drill": "Train one IVF generation on a stratified corpus sample, then test 93 judged queries at four probe budgets. Report exact top-12 recall, eligible-candidate counts, list-size skew and p95 latency by tenant and language. Repeat after the next substantial ingestion wave.",
        "related": [prefix + "filtered-ann-recall-and-latency", prefix + "vector-quantization-recall-and-exact-reranking", prefix + "embedding-space-version-and-migration", prefix + "hnsw-candidate-budgets-and-ann-recall-curves"],
    },
    {
        "slug": "lexical-term-coverage-boolean-clauses-and-zero-term-safety",
        "title": "Lexical term coverage: require enough words without losing valid hits",
        "summary": "Treat term-coverage thresholds as a candidate rule, keep authorization separate and define what happens when analysis removes every query token.",
        "sections": [
            ("Term coverage is a retrieval gate", "A lexical query with several terms can use an all-terms rule, an any-term rule or a threshold between them. All terms can miss a useful document when one word is absent or stemmed differently. Any term can return a large set of weak matches dominated by a common word. A minimum-term threshold requires a chosen number of optional clauses to match before a passage becomes a candidate. The threshold controls eligibility, not just score. [[retrieval-ai/bm25-term-saturation-length-normalization-and-field-tuning|BM25]] ranks the surviving lexical candidates; it cannot rescue a relevant document removed by a too-strict coverage rule."),
            ("Separate required constraints from optional evidence", "Tenant, access level, deletion state and document type are hard filters with independent authority. They must never be converted into optional text clauses to raise recall. Likewise, a quoted part number or a user-requested exact phrase may be mandatory even when descriptive words are optional. Parse the query into typed constraints and text clauses before applying a threshold. [[retrieval-ai/safe-search-query-parsing-and-literal-identifiers|Literal query parsing]] prevents punctuation and quotation marks from being silently rewritten into broad term matches. A rule such as 'two of three text words' cannot replace an exact serial-number check."),
            ("Analyzer output determines the denominator", "Minimum-should-match settings act on the clauses produced after analysis, not necessarily on the number of words typed by the user. Stopword removal, stemming and multi-term synonyms can change clause counts or group clauses differently. A query reduced to zero terms needs an explicit policy: return no lexical matches, route to another safe branch or ask for clarification. A match-all fallback can turn a blank or stopword-only query into a costly full-corpus request and may expose unrelated navigation results. [[retrieval-ai/lexical-analyzers-field-scoring-and-identifier-safety|Analyzer contracts]] must be versioned with the query policy."),
            ("Test short and long queries separately", "A two-word query requiring both words can be much stricter than a six-word query requiring four. Fixed percentages also round differently at small clause counts, so write out the exact rule per length. Evaluate rare identifiers, negation, spelling mistakes and long natural-language questions as distinct slices. Start with a bounded lexical candidate pool and measure recall before reranking. [[retrieval-ai/retrieval-recall-and-reranking|Candidate recall]] is the upper bound on what a downstream reranker can recover. If recall falls, broaden optional term coverage or add a semantic branch without weakening mandatory filters."),
            ("Keep operators explicit in diagnostics", "A broad OR query is often useful for candidate generation, while an AND query can be appropriate for a narrow technical phrase. Neither is a universal default. Log analyzed clauses, required filters, threshold, candidate count and the ranker's winning terms so an engineer can explain why a page appeared. A user-visible advanced query language should escape reserved syntax rather than treating arbitrary user text as executable query operators. [[retrieval-ai/phrase-proximity-retrieval-and-token-position-contracts|Phrase matching]] applies when order matters; term coverage alone cannot establish adjacency or source support."),
        ],
        "code": '''import re

STOPWORDS = {"a", "of", "the"}

def lexical_candidates(query: str, passages: dict[str, str],
                       required_terms: set[str], minimum_optional: int
                       ) -> list[tuple[str, int]]:
    optional_terms = set(re.findall(r"[a-z0-9]+", query.casefold()))
    required = {term.casefold() for term in required_terms}
    optional_terms -= required
    optional_terms -= STOPWORDS
    if not optional_terms and not required:
        return []
    if minimum_optional < 0 or minimum_optional > len(optional_terms):
        raise ValueError("invalid optional-term threshold")
    matches = []
    for passage_id, text in passages.items():
        words = set(re.findall(r"[a-z0-9]+", text.casefold()))
        if not required <= words:
            continue
        coverage = len(words & optional_terms)
        if coverage >= minimum_optional:
            matches.append((passage_id, coverage))
    return sorted(matches, key=lambda item: (-item[1], item[0]))

passages = {"note-47": "Pressure seal replacement for pump P47",
            "note-81": "Pressure regulator inspection for pump P81",
            "note-94": "Seal inventory for pump P47"}
assert lexical_candidates("pressure seal", passages, {"p47"}, 1) == [
    ("note-47", 2), ("note-94", 1)]
assert lexical_candidates("the", passages, set(), 0) == []
assert lexical_candidates("", passages, set(), 0) == []''',
        "cost": "For N passages with T total tokens and Q query terms, this direct scan takes O(T + NQ) expected time for tokenization and set intersections and O(Q + maximum passage vocabulary plus output) extra space per passage if processed sequentially. A real inverted index intersects required postings and counts optional postings without scanning every document. This example intentionally omits authorization and stemming; its tiny stopword set only illustrates the zero-term policy. Apply a separate mandatory permission filter before returning candidates. A zero-term query returns no hits rather than scanning everything.",
        "mistakes": ["Treating access-control conditions as optional clauses when trying to improve recall.", "Applying a percentage threshold to raw input words instead of analyzed clauses.", "Allowing a zero-term query to fall through to an unbounded match-all search.", "Assuming a document containing enough terms also contains the requested phrase or supports the answer."],
        "drill": "Build 79 queries across one-word identifiers, two-word technical phrases and longer questions. Compare all-term, any-term and length-aware thresholds on authorized candidate recall at 30, false-match rate and lexical execution cost. Include stopword-only and quoted-identifier cases.",
        "related": [prefix + "bm25-term-saturation-length-normalization-and-field-tuning", prefix + "safe-search-query-parsing-and-literal-identifiers", prefix + "phrase-proximity-retrieval-and-token-position-contracts", prefix + "retrieval-recall-and-reranking"],
    },
    {
        "slug": "retrieved-claim-conflicts-authority-and-abstention",
        "title": "Conflicting retrieved claims: compare scope before choosing an answer",
        "summary": "Represent claims with units, time, source revision and authority; resolve only explicit precedence and abstain when evidence still conflicts.",
        "sections": [
            ("High rank cannot settle a factual conflict", "Two retrieved passages can disagree while both are topically relevant. One may state a retired pressure limit, another a current limit, or both may describe different machines with similar names. Embedding similarity and BM25 score measure retrieval fit, not truth. Before answering, extract the exact claim, subject, unit, scope, valid time and source revision from each candidate. Then distinguish a real contradiction from a comparison of different periods or entities. [[retrieval-ai/temporal-retrieval-as-of-validity-and-conflicts|Temporal retrieval]] handles as-of questions; this lesson handles the remaining conflict after scope has been aligned."),
            ("Preserve the evidence chain", "Keep every competing claim tied to a stable passage ID, document version and accessible source span. A summary that strips those identifiers can merge incompatible facts into a plausible but unsupported sentence. The answer layer should know whether a value came from a signed operating procedure, a field note or a user comment, and whether the source is current for the requested asset. [[retrieval-ai/source-extraction-and-passage-provenance|Passage provenance]] supplies the chain; [[retrieval-ai/claim-level-citation-and-support-checks|claim support checks]] confirm that the final wording matches a cited span. Never present the model's synthesis as a new source."),
            ("Precedence needs an explicit policy", "A policy may prefer an approved revision of an operating manual over an older superseded revision for a specific plant. It should not prefer a source merely because the document is newer or its vector score is higher. A later discussion post may be less authoritative than an older still-valid standard. Encode precedence by source type, approval status, entity scope and validity interval, then test it with known cases. If two active approved sources disagree at the same scope, leave the conflict visible and escalate. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Document lifecycle]] determines whether a source is even eligible for this decision."),
            ("Normalize values before declaring disagreement", "Numerical claims require units, tolerances and measurement conditions. A value in kilopascals and one in bars can be equivalent after conversion; a temperature setpoint and a maximum safety limit are different predicates despite sharing a number. Preserve the original text and compute a normalized comparison only when the conversion rule is known. Do not erase ranges, qualifiers or uncertainty. The example compares exact normalized values under one subject and predicate; a production system also needs approved unit conversions and tolerance bands. [[retrieval-ai/table-retrieval-and-numeric-cell-context|Numeric cell context]] prevents a table header from being dropped while extracting a value."),
            ("Abstention is a valid result", "If conflicting eligible sources cannot be resolved by an approved rule, return a concise conflict report with both source spans and the missing decision, or ask a domain owner. Do not average incompatible limits or pick the first result. A bounded follow-up search may find a superseding revision, but stop after a stated budget and avoid turning repeated retrieval into manufactured certainty. [[retrieval-ai/corrective-retrieval-and-bounded-retry|Corrective retrieval]] controls that retry; [[retrieval-ai/evidence-bound-answer-and-abstention|evidence-bound answering]] defines the final refusal to assert an unsupported value. Track unresolved-conflict rate alongside answer accuracy during release testing."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class Claim:
    asset_id: str
    predicate: str
    value_kpa: int
    valid_from: int
    valid_until: int | None
    approved: bool
    passage_id: str

def resolve_limit(claims: list[Claim], asset_id: str, as_of: int
                  ) -> tuple[int | None, list[str]]:
    eligible = [claim for claim in claims
                if claim.asset_id == asset_id
                and claim.predicate == "maximum_pressure"
                and claim.approved and claim.valid_from <= as_of
                and (claim.valid_until is None or as_of < claim.valid_until)]
    if not eligible:
        return None, []
    readings = {claim.value_kpa for claim in eligible}
    sources = sorted(claim.passage_id for claim in eligible)
    if len(readings) != 1:
        return None, sources
    return readings.pop(), sources

claims = [Claim("pump-47", "maximum_pressure", 620, 100, None,
                True, "manual-v3-p6"),
          Claim("pump-47", "maximum_pressure", 590, 100, None,
                True, "bulletin-12-p2"),
          Claim("pump-47", "maximum_pressure", 570, 20, 100,
                True, "retired-v1-p4")]
assert resolve_limit(claims, "pump-47", 123) == (
    None, ["bulletin-12-p2", "manual-v3-p6"])
assert resolve_limit(claims, "pump-47", 55) == (570, ["retired-v1-p4"])''',
        "cost": "Filtering C extracted claims takes O(C) time; sorting E eligible passage IDs costs O(E log E) and requires O(E) memory. Claim extraction, unit normalization, source validation and additional retrieval are separate costs. This example abstains when two active approved claims disagree and does not implement an authority hierarchy. A production resolver must log policy version, source revisions and scope, and must reject missing or uncertain units rather than silently treating them as comparable. More retrieval can increase the chance of finding a superseding source but also consumes latency and can surface new conflicts.",
        "mistakes": ["Choosing the higher-ranked passage as truth when two eligible sources disagree.", "Comparing numbers without units, predicate and operating conditions.", "Discarding source revision or passage identity during answer synthesis.", "Averaging two incompatible safety limits instead of reporting the unresolved conflict."],
        "drill": "Assemble 53 asset-limit questions with superseded revisions, equivalent converted units, conflicting current approvals and wrong-asset distractors. Measure correct resolution, false certainty and source-span accuracy; require abstention for unresolved active conflicts.",
        "related": [prefix + "temporal-retrieval-as-of-validity-and-conflicts", prefix + "source-extraction-and-passage-provenance", prefix + "claim-level-citation-and-support-checks", prefix + "evidence-bound-answer-and-abstention"],
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
        "featured": False, "sort_order": 8481 + offset, "status": "published",
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
    row["data"]["modules"].append({"title": "IVF search, lexical coverage and claim conflicts", "lessons": new_paths})
    row["body"] += '<h2>IVF search, lexical coverage and claim conflicts</h2><ul>' + ''.join(
        f'<li>{link(target)}</li>' for target in new_paths) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "filtered-ann-recall-and-latency": [new_paths[0]],
    prefix + "safe-search-query-parsing-and-literal-identifiers": [new_paths[1]],
    prefix + "temporal-retrieval-as-of-validity-and-conflicts": [new_paths[2]],
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
