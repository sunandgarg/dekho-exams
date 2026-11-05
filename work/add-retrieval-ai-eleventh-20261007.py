"""Publish four original Retrieval AI lessons with reciprocal navigation."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-retrieval-ai-eleventh-import-20261007.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "retrieval-ai/"
hub_path = prefix + "retrieval-ai-tutorial"

lessons = [
    {
        "slug": "safe-search-query-parsing-and-literal-identifiers",
        "title": "Safe search query parsing: operators, filters and literal identifiers",
        "summary": "Parse a small search grammar without allowing user text to become backend query syntax or corrupting exact identifiers.",
        "sections": [
            ("Separate user text from query instructions", "A search box receives untrusted text. Some users want literal terms; others want a quoted phrase or a field filter. Treating every colon, quote or minus sign as an operator makes part numbers and copied error messages disappear. Sending the entire string to an engine's strict query-language parser also exposes backend syntax and brittle error behavior. Define a small public grammar and compile it to typed backend clauses. Keep [[retrieval-ai/lexical-analyzers-field-scoring-and-identifier-safety|literal identifier matching]] available even when the ordinary text analyzer stems or splits words."),
            ("Write down the grammar before the parser", "For a maintenance archive, allow plain words, double-quoted phrases and one filter of the form site:plant-a. Make the allowed filter names explicit. Put bounds on query bytes, phrase length and operator count before parsing; a syntactically valid query can still consume excessive work. Reject unknown filters rather than silently treating them as authorization. A site filter narrows a search; it cannot grant access to a plant the user is forbidden to see. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Corpus permissions]] must be applied by the server independently of the query."),
            ("Compile to data, never to a concatenated query string", "The backend should receive structured term, phrase and filter values. It should escape or parameterize them using its own API, not string interpolation into a query-language expression. If an external search service accepts only a query string, encode literal tokens with that service's documented escaping rules and test metacharacters end to end. Do not reuse SQL quoting rules for search-engine syntax. Parse errors should be explicit and safe: show the offending span without echoing private backend diagnostics. [[retrieval-ai/query-expansion-guardrails-and-drift-tests|Query expansion]] is a separate, measured step after the literal request is preserved."),
            ("Preserve exact tokens and interpretation", "Store the raw query, parsed clauses, parser version and final backend request in a protected trace. A serial such as P-47/AC may need both a raw keyword field and a normalized text field; the slash and hyphen should not accidentally become operators. Search analytics can group equivalent grammar versions, but never rewrite a user's identifier into a guessed synonym without retaining an exact branch. When a result seems wrong, [[retrieval-ai/retrieval-traces-and-incident-debugging|retrieval traces]] reveal whether the parser, analyzer, filter or ranker changed the request."),
            ("Test the contract at its boundaries", "Build a table of valid and invalid requests: empty input, unmatched quotes, doubled filters, Unicode letters, copied stack traces, 47-word inputs and punctuation-heavy IDs. Check that forbidden sites stay excluded even when the user asks for them. Compare parsed intent with human judgments on realistic query logs after redacting personal data. A permissive fallback that sends a malformed query directly to the engine defeats the parser; return a clear error or treat the whole input as literal text according to one documented rule."),
        ],
        "code": '''import re
from dataclasses import dataclass

@dataclass(frozen=True)
class SearchRequest:
    terms: tuple[str, ...]
    phrases: tuple[str, ...]
    site: str | None

TOKEN = re.compile(r'"[^"\\n]{1,80}"|[^\\s"]+')
SITE = re.compile(r"site:([a-z0-9][a-z0-9-]{0,31})$", re.I)

def parse_search(raw_query: str, allowed_sites: set[str]) -> SearchRequest:
    if len(raw_query.encode("utf-8")) > 384:
        raise ValueError("query too long")
    terms, phrases, site = [], [], None
    remaining = TOKEN.sub("", raw_query).strip()
    if remaining:
        raise ValueError("unmatched quote or unsupported syntax")
    for token in TOKEN.findall(raw_query):
        if token.startswith('"'):
            phrases.append(token[1:-1])
        elif token.startswith("site:"):
            match = SITE.fullmatch(token)
            if match is None or site is not None:
                raise ValueError("invalid site filter")
            site = match.group(1).lower()
            if site not in allowed_sites:
                raise ValueError("site not available")
        else:
            terms.append(token)
    if not terms and not phrases:
        raise ValueError("query needs search text")
    if len(terms) + len(phrases) > 47:
        raise ValueError("too many clauses")
    return SearchRequest(tuple(terms), tuple(phrases), site)

request = parse_search('P-47/AC "seal pressure" site:plant-a', {"plant-a"})
assert request.terms == ("P-47/AC",)
assert request.phrases == ("seal pressure",)
assert request.site == "plant-a"''',
        "cost": "For N query characters, tokenization and parsing take O(N) time and O(N) space. The backend's cost depends on posting-list size, phrase positions, filters and top-K ranking; parsing is rarely the expensive part. The demonstration describes a deliberately narrow grammar, not a full search-language parser. Its caller must still enforce tenant authorization and compile the typed values through the backend's safe query API.",
        "mistakes": ["Passing raw user text to a strict backend query-language parser.", "Using a user-supplied site filter as an access-control decision.", "Dropping punctuation from an exact serial number before literal matching.", "Silently falling back to unrestricted search after a syntax error."],
        "drill": "Collect 63 redacted archive queries containing IDs, quotes and filters. Label each intended interpretation, then test parser acceptance, exact-token retention and permission enforcement before comparing top-12 recall.",
        "related": [prefix + "lexical-analyzers-field-scoring-and-identifier-safety", prefix + "query-expansion-guardrails-and-drift-tests", prefix + "corpus-permissions-and-document-lifecycle", prefix + "retrieval-traces-and-incident-debugging"],
    },
    {
        "slug": "search-snippets-highlighting-offsets-and-redaction",
        "title": "Search snippets: highlighting, offsets and safe evidence previews",
        "summary": "Build snippets from the correct source revision, escape text safely and keep private spans out of previews.",
        "sections": [
            ("A snippet is a provenance claim", "A search result preview tells a reader why a passage matched. Its words must come from the same authorized source revision as the link and citation. Reconstructing a snippet from a model summary can make the result appear to contain text it never held. Preserve source offsets during [[retrieval-ai/source-extraction-and-passage-provenance|source extraction]], together with document ID, revision and field name. Render the original passage around a matched span; label transformed text when OCR or normalization means the display differs from the source."),
            ("Choose a window that retains the qualifier", "A 30-character window around a matched number may omit its unit, negation or date. Expand to a sentence, table row or bounded section when structure is available. Limit output length, then mark truncation. For a query about a pressure limit, showing only the number is misleading if the next sentence says it applies only during startup. The [[retrieval-ai/claim-level-citation-and-support-checks|claim support check]] should inspect the full evidence, not a clipped snippet. A preview is navigation help, not proof by itself."),
            ("Escape before adding markup", "Source documents may contain HTML, scripts or text that looks like tags. Escape source text first, then insert only controlled highlighting markup around measured spans. Offset units matter: byte offsets, Unicode code-point indices and UTF-16 units are different. If the highlighter measures one representation and the renderer slices another, a match can move into the wrong word or break an encoded character. A safe renderer either uses offsets in its own string representation or converts them explicitly."),
            ("Redact under the current permission scope", "A result can be searchable without every field being previewable. Mask personal data, secrets and restricted spans before selecting or rendering windows; highlight offsets then need recalculation against the redacted text. Cache previews only with a permission scope and source revision, and invalidate them when a document is deleted or access changes. Redaction is not achieved by hiding markup with CSS: the private text must never be sent to the browser. [[retrieval-ai/permission-aware-cache-and-conversation-turns|Permission-aware caching]] covers the same revocation boundary."),
            ("Evaluate both safety and usefulness", "Judge whether a preview contains the answer-bearing phrase, relevant unit and limiting condition; also test whether it contains any restricted span. Include OCR artifacts, right-to-left text, emoji and strings such as angle brackets in the corpus. Compare snippet usefulness and render latency at a fixed window budget. Generating broad previews for every candidate before top-K selection can waste work; fetch and render only results that survive ranking. [[retrieval-ai/ocr-layout-reading-order-and-confidence|OCR layout]] changes what a nearby text window actually means."),
        ],
        "code": '''from html import escape

def highlighted_preview(source_text: str, match_start: int,
                        match_end: int, radius: int = 47) -> str:
    if not 0 <= match_start < match_end <= len(source_text):
        raise ValueError("invalid match span")
    if not 0 <= radius <= 160:
        raise ValueError("invalid radius")
    start = max(0, match_start - radius)
    end = min(len(source_text), match_end + radius)
    before = escape(source_text[start:match_start])
    matched = escape(source_text[match_start:match_end])
    after = escape(source_text[match_end:end])
    return ("…" if start else "") + before + "<strong>" + matched + "</strong>" + after + ("…" if end < len(source_text) else "")

passage = "Pump P-47: <script> is literal text. Seal limit is 28 kPa."
start = passage.index("28 kPa")
preview = highlighted_preview(passage, start, start + len("28 kPa"))
assert "<script>" not in preview
assert "&lt;script&gt;" in preview
assert "<strong>28 kPa</strong>" in preview''',
        "cost": "For a selected preview window of W characters, escaping and concatenation take O(W) time and O(W) space. Locating a match can be O(N) in an N-character passage without stored offsets; the example's index call has that cost. Index-time term vectors or stored offsets trade storage and ingest work for faster highlighting. Apply redaction before this function; escaped private text is still private text. The example emits controlled strong tags only after escaping source characters.",
        "mistakes": ["Inserting raw source text into HTML and highlighting it afterward.", "Using offsets from a normalized or redacted string against the original source.", "Showing a numeric hit without its unit or limiting condition.", "Caching a preview beyond a permission change or document revision."],
        "drill": "Annotate 37 result previews across HTML-like text, OCR and restricted fields. Require the answer span plus qualifier in allowed previews, zero leaked restricted spans and correct source revision after an update.",
        "related": [prefix + "source-extraction-and-passage-provenance", prefix + "claim-level-citation-and-support-checks", prefix + "permission-aware-cache-and-conversation-turns", prefix + "ocr-layout-reading-order-and-confidence"],
    },
    {
        "slug": "retrieval-index-alias-cutover-and-rollback",
        "title": "Index alias cutovers: switch retrieval generations without mixed results",
        "summary": "Build and verify a new index before switching readers, retain rollback and check cross-index compatibility.",
        "sections": [
            ("Treat each index build as a generation", "An index generation is an immutable serving candidate with a corpus snapshot, parser settings, analyzer configuration and model version. Updating a live index in place can mix old and new representations. Instead, build generation B while readers use A, replay changes until B reaches an acceptable [[retrieval-ai/index-watermarks-freshness-slos-and-stale-answer-policy|ingestion watermark]], and verify it before cutover. An alias or routing pointer lets the application switch the serving generation as one operation. The pointer is small; rebuilding the index is the costly work."),
            ("Check compatibility across every retrieval branch", "A retrieval service may read a lexical index, vector index, metadata store and citation store for one answer. Changing only one alias can produce a passage ID that the other stores cannot resolve, or a query vector encoded with the wrong model. Record a manifest of compatible generations and switch that manifest atomically at the application boundary. [[retrieval-ai/snapshot-consistent-multi-index-retrieval|Multi-index snapshots]] explain why a single consistent view matters; [[retrieval-ai/embedding-space-version-and-migration|embedding migration]] covers vector-specific compatibility."),
            ("Gate the switch on observed evidence", "Compare the candidate generation on labeled slices for exact identifiers, paraphrases, deleted documents, access restrictions and fresh updates. Inspect top-K recall, unsupported claims, p95 latency and index size. A green aggregate can hide a severe loss for rare serial-number queries. Run shadow traffic with identical authorization filters and no user-visible answers, then compare traces under a fixed sample budget. Keep a minimum freshness condition so the new index does not silently omit the last ingestion window."),
            ("Switch once and keep rollback bounded", "Before cutover, pin in-flight requests to one generation. Change the alias or manifest pointer atomically, then start new requests on B. Retain A until rollback tests, cache invalidation and a short monitoring period complete. Reversing the pointer is a rollback only if A can still serve current permissions and deletion rules. A deleted document must not reappear after a rollback; apply tombstones to both generations or use a central authoritative filter. [[retrieval-ai/incremental-ingestion-idempotency-and-delete-races|Delete races]] become more important during dual writes."),
            ("Audit the generation used by each answer", "Log the serving manifest ID, corpus watermark and relevant model versions with each retrieval trace and citation. If an incident spans a cutover, those fields distinguish an index defect from a changed query distribution. Test partial failures: a stale replica, failed alias update and cache entry from A should never make one answer combine A and B without an explicit compatibility rule. An index alias is a routing device, not evidence that data or permissions are correct."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class IndexGeneration:
    name: str
    corpus_revision: int
    model_revision: str
    checked: bool

def choose_generation(current: IndexGeneration,
                      candidate: IndexGeneration,
                      required_corpus_revision: int,
                      query_model_revision: str) -> IndexGeneration:
    if not candidate.checked:
        raise ValueError("candidate has not passed release checks")
    if candidate.corpus_revision < required_corpus_revision:
        raise ValueError("candidate is behind the freshness gate")
    if candidate.model_revision != query_model_revision:
        raise ValueError("query and passage models differ")
    return candidate

active = IndexGeneration("lexical-a", 81, "encoder-r4", True)
next_index = IndexGeneration("lexical-b", 87, "encoder-r4", True)
selected = choose_generation(active, next_index, 85, "encoder-r4")
assert selected.name == "lexical-b"
assert active.name == "lexical-a"''',
        "cost": "The gate shown uses O(1) time and space; index construction remains proportional to corpus size and token or vector count. Dual generations temporarily raise storage, ingestion and validation cost. Actual pointer updates need a backend operation that is atomic for readers, plus a consistent application manifest when several indexes are involved. The code models a gate, not a distributed alias update or a substitute for live permission checks.",
        "mistakes": ["Switching a lexical index and vector index independently without a compatibility manifest.", "Treating a successful alias update as proof the candidate contains recent deletions.", "Deleting the prior generation before rollback and in-flight requests are finished.", "Using a rollback that restores documents whose access has since been revoked."],
        "drill": "Build two generations from 113 documents and replay three changes, including a deletion. Verify a freshness gate, a failed candidate, an atomic pointer switch, in-flight request pinning and a rollback that does not reveal the deleted record.",
        "related": [prefix + "snapshot-consistent-multi-index-retrieval", prefix + "embedding-space-version-and-migration", prefix + "index-watermarks-freshness-slos-and-stale-answer-policy", prefix + "incremental-ingestion-idempotency-and-delete-races"],
    },
    {
        "slug": "retrieval-drift-monitoring-and-shadow-evaluation",
        "title": "Retrieval drift: monitor query slices and shadow a candidate safely",
        "summary": "Detect changes in retrieval quality without confusing clicks with labels or exposing shadow results to users.",
        "sections": [
            ("Drift is a change in the contract, not one number", "Retrieval drift appears when query wording, corpus coverage, permissions, parser behavior or model representations change enough that relevant evidence is no longer found. A stable aggregate click rate can hide a severe miss for a low-volume query class. Define slices such as serial identifiers, recent procedures, multilingual requests and no-answer questions. Track corpus and index freshness alongside result behavior so a stale source is not mistaken for ranking drift. [[retrieval-ai/retrieval-release-evaluation-and-slice-gates|Release gates]] set initial quality thresholds; monitoring tests whether those assumptions still hold."),
            ("Use signals with different levels of trust", "Labeled answer-bearing passages give direct recall measurements but are expensive and slow to update. Unlabeled operational signals include zero-result rate, filter rejection, latency, candidate overlap and sudden changes in query length. These indicate where to investigate; they do not prove relevance. Clicks are shaped by result position and interface design, so they cannot be treated as ground-truth judgments. [[retrieval-ai/click-feedback-position-bias-and-offline-evaluation|Click bias]] needs explicit correction or a separate human review path."),
            ("Shadow candidates within the same security boundary", "A shadow run sends a sampled query to the current and candidate retrievers, then shows only the current result to the user. Both branches must apply the same current permission filters and secret-handling rules. Log bounded, redacted comparisons rather than raw private queries. Record index, model and parser versions; otherwise a changed score distribution cannot be attributed. Compare result IDs, answer-bearing span recall on labeled traffic and latency at the same candidate budget. Do not call a shadow winner from score magnitude alone when scoring scales differ."),
            ("Set alert thresholds by slice and baseline", "Use a fixed evaluation set for regression checks and a rolling operational baseline for distribution changes. A threshold should include minimum traffic, a window and an action: inspect, pause rollout or roll back. For rare slices, low sample count can make a weekly rate noisy; report numerator and denominator, not only a percentage. A sudden zero-result increase may be caused by a permission policy change, an ingestion delay or new user vocabulary. [[retrieval-ai/retrieval-traces-and-incident-debugging|Traces]] help separate these causes."),
            ("Close the loop with adjudicated cases", "When an alert fires, sample misses, attach source revision and permission context, and have reviewers identify the expected evidence or mark the query unanswerable. Add stable cases to the judged set, then test a proposed parser, index or ranking change against old and new slices. [[retrieval-ai/counterfactual-retrieval-tests-and-distractor-resilience|Counterfactual tests]] expose whether the change merely overfits familiar examples. Keep evaluation data versioned; otherwise an apparent gain may come from changed labels rather than a better retriever."),
        ],
        "code": '''from collections import defaultdict

def slice_recall(records: list[tuple[str, bool, bool]],
                 minimum_cases: int = 3) -> dict[str, tuple[int, int]]:
    counts = defaultdict(lambda: [0, 0])
    for query_slice, has_judged_answer, answer_found in records:
        if not has_judged_answer:
            continue
        counts[query_slice][1] += 1
        counts[query_slice][0] += int(answer_found)
    return {name: (hits, total) for name, (hits, total) in counts.items()
            if total >= minimum_cases}

judgments = [
    ("serial-id", True, True), ("serial-id", True, False),
    ("serial-id", True, True), ("recent-policy", True, True),
    ("recent-policy", True, True), ("recent-policy", True, True),
    ("recent-policy", False, False),
]
report = slice_recall(judgments)
assert report == {"serial-id": (2, 3), "recent-policy": (3, 3)}''',
        "cost": "For Q judged queries, this single-pass slice calculation takes O(Q) time and O(S) space for S slices. Running two retrievers in shadow can nearly double retrieval compute for sampled traffic, plus trace storage and review work; sample deliberately and cap latency impact. The example reports counts instead of a bare percentage and excludes no-answer cases from answer-recall. Evaluate abstention separately, because excluding no-answer cases does not make false answers harmless.",
        "mistakes": ["Calling clicks a relevance label without accounting for position and presentation.", "Comparing raw scores from different ranking models as if their scales matched.", "Shadowing a candidate without the current permission filters.", "Triggering a rollback from a tiny slice sample without examining its counts and source context."],
        "drill": "Shadow 71 redacted queries across four named slices. Compare candidate overlap and judged recall, report counts with p95 latency and freshness, then adjudicate five disagreements before deciding on a rollout.",
        "related": [prefix + "retrieval-release-evaluation-and-slice-gates", prefix + "click-feedback-position-bias-and-offline-evaluation", prefix + "retrieval-traces-and-incident-debugging", prefix + "counterfactual-retrieval-tests-and-distractor-resilience"],
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
        "featured": False, "sort_order": 8465 + offset, "status": "published",
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
    row["data"]["modules"].append({"title": "Query safety, snippets, index cutovers and drift", "lessons": new_paths})
    row["body"] += '<h2>Query safety, snippets, index cutovers and drift</h2><ul>' + ''.join(
        f'<li>{link(target)}</li>' for target in new_paths) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "lexical-analyzers-field-scoring-and-identifier-safety": [new_paths[0]],
    prefix + "source-extraction-and-passage-provenance": [new_paths[1]],
    prefix + "embedding-space-version-and-migration": [new_paths[2]],
    prefix + "retrieval-release-evaluation-and-slice-gates": [new_paths[3]],
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
