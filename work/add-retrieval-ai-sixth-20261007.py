"""Publish original Retrieval AI lessons on OCR, place, databases and dialogue."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-retrieval-ai-sixth-import-20261007.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "retrieval-ai/"
hub_path = prefix + "retrieval-ai-tutorial"

lessons = [
    {
        "slug": "ocr-layout-reading-order-and-confidence",
        "title": "OCR retrieval: preserve reading order, page regions and uncertainty",
        "summary": "Index scanned documents as positioned evidence rather than flattening columns, captions and doubtful characters into one text stream.",
        "sections": [
            ("Keep the page geometry", "OCR retrieval searches text extracted from scans while preserving where each token appeared. The page image is the source; recognized text is a fallible interpretation. Store document revision, page number, bounding box, block type, reading-order position and extraction confidence with each passage. A two-column safety sheet can interleave warnings with unrelated specifications if its text is flattened by coordinate order alone. [[retrieval-ai/source-extraction-and-passage-provenance|Extraction provenance]] should let a reviewer reopen the precise image region behind a candidate."),
            ("Reconstruct blocks before chunks", "Detect headings, paragraphs, footnotes, tables and captions as separate blocks, then connect them in a plausible reading order. A caption can belong to a diagram beside it rather than the paragraph directly above it. Chunk within a block or a justified parent section; crossing column boundaries can invent a sentence that was never printed. Keep alternative reading-order hypotheses when a page is ambiguous. [[retrieval-ai/hierarchical-retrieval-and-parent-child-evidence|Hierarchical retrieval]] can route by section while leaving the cited evidence on the original page region."),
            ("Handle uncertain characters", "A scan may confuse P-47 with P-41 or 83 kPa with 88 kPa. Record character- or token-level confidence when the OCR engine provides it. Exact-match retrieval of identifiers should search the recognized string and, within a bounded error budget, reviewed alternatives. Do not silently replace low-confidence digits with a fluent guess. For a numeric answer, require the number and unit to be legible in the image or verified by an independent source. [[retrieval-ai/table-retrieval-and-numeric-cell-context|Numeric cell context]] matters even when the table was recognized correctly."),
            ("Separate search from support", "OCR text is useful for candidate generation, but an answer citing a scan needs a page and a region. A high ranking score cannot validate an illegible number. If a candidate's decisive token is below the review threshold, send the region to a human or abstain. Preserve redaction masks in both OCR text and image crops; otherwise a search result might expose text that the displayed image hides. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Permission rules]] apply to page metadata and crops as well as text."),
            ("Judge image-grounded retrieval", "Build queries for split columns, rotated labels, handwriting, captions, tables, near-identical part numbers and pages with no answer. Score page recall, region overlap, reading-order integrity and final claim support separately. A system that finds the correct PDF but cites the wrong column should fail. Record OCR engine and layout model versions so a model upgrade can be compared on exactly the same scanned pages. Review regressions on low-resolution and multilingual slices rather than accepting one aggregate score."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class PageBlock:
    document_id: str
    page: int
    column: int
    order: int
    confidence: float
    text: str

def ordered_evidence(blocks: list[PageBlock], document_id: str,
                     minimum_confidence: float) -> list[PageBlock]:
    if not 0 <= minimum_confidence <= 1:
        raise ValueError("confidence threshold outside [0, 1]")
    eligible = [block for block in blocks if block.document_id == document_id
                and block.confidence >= minimum_confidence]
    return sorted(eligible, key=lambda block: (block.page, block.column, block.order))

scan = [PageBlock("manual-r4", 3, 2, 1, .97, "Pump P-47 limit: 83 kPa"),
        PageBlock("manual-r4", 3, 1, 1, .99, "Hydraulic system"),
        PageBlock("manual-r4", 3, 2, 2, .44, "Unclear value: 88?"),
        PageBlock("manual-r3", 3, 2, 1, .99, "Pump P-47 limit: 71 kPa")]
assert [block.text for block in ordered_evidence(scan, "manual-r4", .85)] == [
    "Hydraulic system", "Pump P-47 limit: 83 kPa"]''',
        "cost": "Sorting B blocks costs O(B log B) time and O(B) output space. OCR and layout inference cost far more than the ordering operation, so cache extraction by document hash and model version. Crops, coordinates and alternate transcripts add storage. Higher-resolution rescans can improve evidence quality but increase processing and review cost; target them at low-confidence answer-bearing regions.",
        "mistakes": ["Concatenating two columns into a fabricated sentence.", "Treating an OCR guess for a digit as verified evidence.", "Citing only a PDF title when the answer lives in one page region.", "Redacting the image but leaving its recognized text searchable."],
        "drill": "Scan 47 pages with columns, tables and captions. Judge 37 questions and require page-region overlap, correct number and unit, and an abstention when the decisive characters remain uncertain.",
        "related": [prefix + "source-extraction-and-passage-provenance", prefix + "hierarchical-retrieval-and-parent-child-evidence", prefix + "table-retrieval-and-numeric-cell-context", prefix + "claim-level-citation-and-support-checks"],
    },
    {
        "slug": "geospatial-retrieval-radius-boundaries-and-evidence",
        "title": "Geospatial retrieval: combine meaning, distance and jurisdiction",
        "summary": "Find nearby eligible evidence with explicit coordinate systems, radius limits and geographic provenance.",
        "sections": [
            ("Define what the location means", "Geospatial retrieval finds records whose physical coverage matters to the query. 'Show repair notices near station P-47' could mean notices located at a point, assets within a radius, or policies applying to a jurisdiction polygon. Those are different predicates. Store geometry type, coordinate reference system, accuracy, valid interval and source identity with the record. A document mentioning a city name is not necessarily located there. [[retrieval-ai/query-intent-and-retrieval-routing|Query routing]] should distinguish place intent from a text-only mention before choosing a spatial operation."),
            ("Filter space before semantic rank", "Apply tenant permission, active revision and geographic eligibility before semantic ranking. A nearby restricted maintenance ticket should not appear in a result count, map marker or generated answer. Use an indexed radius predicate for point proximity, then compute exact distance for candidates; use containment or intersection for coverage areas. Do not compare raw latitude-longitude degree differences with a radius in meters. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Corpus permissions]] remain part of the spatial query, not a presentation-layer patch."),
            ("Keep uncertainty visible", "A geocoded address may identify a street rather than a building. A device location can drift; a service district boundary can change. Store location accuracy and boundary version, and avoid a definitive inside/outside claim when an uncertainty circle crosses the edge. For a 'within 2 km' question, state whether distance is straight-line, walking route or drive time. The retrieval result should include the location source and the calculated distance, so the claim can be checked. [[retrieval-ai/temporal-retrieval-as-of-validity-and-conflicts|Temporal retrieval]] governs historical boundaries."),
            ("Combine place and text without score confusion", "A spatial index can return a bounded set of eligible records, after which lexical or vector ranking identifies the relevant notice. For broad areas, text search may produce candidates first, followed by exact geometry checks. Choose order from selectivity and cost, but keep both filters mandatory. Ranking a notice highly cannot make an out-of-area record eligible. Do not merge kilometers and semantic similarity into one unexplained scalar. [[retrieval-ai/federated-retrieval-source-budgets-and-merging|Source budgets]] can reserve results across nearby notices and region-wide rules."),
            ("Test boundaries, not just centers", "Judge cases on both sides of a district border, exactly at the radius, with missing coordinates, stale geocodes, overlapping regions and different tenant scopes. Report eligible-record recall separately from relevance and answer support. Include a named location that appears in a document body but lies outside its service area. A system that finds the right topic and wrong jurisdiction must fail even if its prose sounds plausible. Capture geometry version and distance method in the evaluation trace."),
        ],
        "code": '''from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt

@dataclass(frozen=True)
class ServiceNotice:
    notice_id: str
    tenant: str
    latitude: float
    longitude: float
    text: str

def distance_km(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    if any(not -90 <= lat <= 90 for lat in (lat_a, lat_b)):
        raise ValueError("invalid latitude")
    if any(not -180 <= lon <= 180 for lon in (lon_a, lon_b)):
        raise ValueError("invalid longitude")
    north = radians(lat_b - lat_a)
    east = radians(lon_b - lon_a)
    arc = sin(north / 2) ** 2 + cos(radians(lat_a)) * cos(radians(lat_b)) * sin(east / 2) ** 2
    return 2 * 6371.0088 * asin(min(1.0, sqrt(arc)))

def nearby(notices: list[ServiceNotice], tenant: str,
           latitude: float, longitude: float, radius_km: float) -> list[str]:
    if radius_km < 0:
        raise ValueError("negative radius")
    return [notice.notice_id for notice in notices if notice.tenant == tenant
            and distance_km(latitude, longitude, notice.latitude, notice.longitude) <= radius_km]

notices = [ServiceNotice("pump-47", "north", 28.6139, 77.2090, "Valve inspection"),
           ServiceNotice("pump-83", "north", 28.7041, 77.1025, "Valve inspection"),
           ServiceNotice("private", "south", 28.6139, 77.2090, "Valve inspection")]
assert nearby(notices, "north", 28.6139, 77.2090, 2) == ["pump-47"]''',
        "cost": "The transparent scan costs O(N) distance calculations and O(K) output space for K matches. A spatial index narrows large corpora before exact distance checks; maintaining it adds storage and write work. Haversine computes a spherical straight-line approximation, not route distance or polygon coverage. Use a geography-aware database predicate for production radius searches and measure boundary errors where accuracy matters.",
        "mistakes": ["Comparing coordinate degrees directly with kilometers.", "Treating a place name in text as a verified record location.", "Filtering geography after showing restricted candidate metadata.", "Ignoring location uncertainty near a boundary."],
        "drill": "Prepare 61 notices across two districts with five missing geocodes and seven boundary cases. Compare point-radius and jurisdiction queries, reporting eligible recall, false inclusions and supported location claims.",
        "related": [prefix + "query-intent-and-retrieval-routing", prefix + "corpus-permissions-and-document-lifecycle", prefix + "temporal-retrieval-as-of-validity-and-conflicts", prefix + "federated-retrieval-source-budgets-and-merging"],
    },
    {
        "slug": "schema-aware-database-retrieval-and-row-provenance",
        "title": "Database retrieval: link a question to schema and trace the rows",
        "summary": "Retrieve structured answers with approved query plans, row-level permissions and verifiable source identifiers.",
        "sections": [
            ("Retrieve a schema contract first", "Database retrieval maps a question to tables, columns, joins and filters before reading rows. A request for unpaid invoices from branch 47 should identify invoice status, branch ID and billing date; an embedding over column descriptions may help discover candidates but cannot define the final join. Store approved schema descriptions, key relationships and field meanings. A column named amount may be gross, net or settled. [[retrieval-ai/query-intent-and-retrieval-routing|Intent routing]] should distinguish a row lookup from a policy explanation or a calculation."),
            ("Keep query generation bounded", "Treat a proposed SQL query as untrusted input. Constrain it to an allowlisted read-only view or a small set of approved query templates. Bind values as parameters, cap rows and time, and reject mutations or cross-tenant joins. Parsing a generated string for the word SELECT alone is not a security boundary; database permissions and row-level security must enforce scope. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Access control]] belongs at the data source as well as in the retrieval layer."),
            ("Carry row provenance into the answer", "Return primary keys, source table or view, query template version, data snapshot and effective filters with each result. An aggregate such as '47 unpaid invoices' needs a traceable query and the population definition, not merely a plausible sentence. If a join multiplies rows, count distinct invoice IDs or fix the join before answering. For a cell-level claim, identify both the row and column. [[retrieval-ai/table-retrieval-and-numeric-cell-context|Table evidence]] requires the unit and row context that make a number meaningful."),
            ("Separate retrieval from computation", "A row set may require arithmetic after retrieval, but that computation should be deterministic and reviewable. Currency conversion needs an explicit rate and as-of date; a missing rate should cause a partial answer or abstention. A result that combines transactional rows with a document policy needs separate citations to each source. [[retrieval-ai/multi-hop-evidence-chain-and-stop-rules|Evidence chains]] should show which source supplies the rule and which supplies the transaction facts."),
            ("Evaluate query and result failures", "Judge schema linking, authorized row recall, predicate accuracy, join cardinality and final answer support separately. Include duplicate line items, soft-deleted records, null status, renamed columns and time-zone boundaries. A syntactically valid query can be semantically wrong: selecting posted_at instead of due_at may produce credible but incorrect overdue counts. Compare the executed query and returned row IDs against a reviewed reference set; do not grade only the final prose."),
        ],
        "code": '''import sqlite3

connection = sqlite3.connect(":memory:")
connection.execute("CREATE TABLE invoices (invoice_id TEXT PRIMARY KEY, tenant TEXT, branch INTEGER, status TEXT, amount_cents INTEGER)")
connection.executemany("INSERT INTO invoices VALUES (?, ?, ?, ?, ?)", [
    ("INV-47", "north", 47, "unpaid", 8300),
    ("INV-48", "north", 47, "paid", 4700),
    ("INV-49", "south", 47, "unpaid", 9900),
])

def unpaid_invoices(tenant: str, branch: int) -> list[tuple[str, int]]:
    return connection.execute(
        "SELECT invoice_id, amount_cents FROM invoices "
        "WHERE tenant = ? AND branch = ? AND status = ? ORDER BY invoice_id LIMIT 83",
        (tenant, branch, "unpaid"),
    ).fetchall()

assert unpaid_invoices("north", 47) == [("INV-47", 8300)]
connection.close()''',
        "cost": "With an index on tenant, branch and status, a selective lookup can avoid scanning every invoice; the exact cost depends on the planner and row count. The in-memory example is tiny, but a production read needs a row cap, execution timeout and query plan check. Materializing R result rows costs O(R) memory; stream large exports rather than placing them in an answer context.",
        "mistakes": ["Executing free-form generated SQL with broad database privileges.", "Using a similarly named amount column without checking its business definition.", "Counting joined line items as distinct invoices.", "Omitting row IDs and filter values from an aggregate's audit trace."],
        "drill": "Create 43 questions against invoices, payments and branch tables. Include duplicate line items, nulls and two tenants. Require matching row IDs, approved schema paths, correct aggregate populations and no cross-tenant disclosure.",
        "related": [prefix + "query-intent-and-retrieval-routing", prefix + "table-retrieval-and-numeric-cell-context", prefix + "multi-hop-evidence-chain-and-stop-rules", prefix + "corpus-permissions-and-document-lifecycle"],
    },
    {
        "slug": "conversational-query-rewrite-and-constraint-carryover",
        "title": "Conversational retrieval: rewrite the follow-up without changing its scope",
        "summary": "Resolve references in a dialogue while carrying only the constraints that still apply to the current search turn.",
        "sections": [
            ("Make the current turn searchable", "Conversational retrieval turns a context-dependent follow-up into a standalone search request. After 'What is the P-47 limit in revision r4?', 'What about the old one?' may refer to the same pump and a prior revision. A rewrite should capture that relation without inventing a date or unit. Keep the raw user text, the selected antecedent and the resolved query in the trace. [[retrieval-ai/query-intent-and-retrieval-routing|Query routing]] should use the resolved intent only after checking that the reference is unambiguous."),
            ("Carry constraints with expiration", "Tenant identity and authorization come from the active session, never from an earlier answer string. Topic, entity and date constraints may carry forward for one turn, but they can also be overridden. 'Now compare P-48' replaces P-47; 'in the south plant' changes place but must not grant access to south-plant records. Track each constraint's origin, confidence and scope, then apply explicit user changes before searching. [[retrieval-ai/permission-aware-cache-and-conversation-turns|Conversation caches]] need the resulting permission and constraint identity in their keys."),
            ("Ask when reference resolution is unsafe", "'What about that one?' may point to two passages from the previous answer. Picking one silently can produce a well-cited answer to the wrong question. Clarify when multiple antecedents remain plausible, or search both only if a comparison was requested and permissions allow both. Do not use the last retrieved passage as the default referent merely because it was ranked first. A bounded clarification step is cheaper than a confident but irrelevant retrieval. [[retrieval-ai/evidence-bound-answer-and-abstention|Abstention]] also applies to unresolved dialogue state."),
            ("Prevent answer contamination", "The previous assistant answer may be wrong, incomplete or injected. Rewrites should rely on authenticated conversation metadata and user turns, then retrieve fresh source evidence. Do not copy a previous answer's unsupported number into the next query as though it were a fact. When the user asks 'why did that change?', retrieve both applicable revisions and compare their cited text. [[retrieval-ai/temporal-retrieval-as-of-validity-and-conflicts|Temporal retrieval]] preserves the two evidence sets rather than blending old and new values."),
            ("Judge turn-by-turn retrieval", "Evaluate follow-ups with pronouns, topic switches, corrections, permission changes, long gaps and contradictory prior answers. Score resolved entity and constraints before measuring passage recall and final support. A system can retrieve the correct passage for a wrong rewrite by luck; that should not hide the rewrite defect. Store the conversation turn ID and corpus generation in the trace. When a user revokes or changes scope, previously cached passages must not reappear in later turns."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class SearchTurn:
    entity: str | None
    revision: str | None
    tenant: str

def resolve_follow_up(previous: SearchTurn, current_text: str,
                      active_tenant: str) -> SearchTurn:
    text = current_text.casefold()
    if "p-48" in text:
        entity = "P-48"
    elif "p-47" in text:
        entity = "P-47"
    elif "old one" in text and previous.entity:
        entity = previous.entity
    else:
        raise ValueError("ambiguous entity; ask for clarification")
    revision = "previous" if "old one" in text else None
    return SearchTurn(entity, revision, active_tenant)

last_turn = SearchTurn("P-47", "r4", "north")
assert resolve_follow_up(last_turn, "What about the old one?", "north") == SearchTurn(
    "P-47", "previous", "north")
assert resolve_follow_up(last_turn, "Now compare P-48", "north") == SearchTurn(
    "P-48", None, "north")''',
        "cost": "The example resolves one turn in O(L) time for text length L and O(1) additional state. A production resolver may inspect a bounded window of T turns, increasing work with that window and with each retrieval retry. Avoid feeding the entire dialogue into every search when only an explicit entity and recent correction are needed. Record and evaluate clarification frequency as part of latency and success.",
        "mistakes": ["Carrying an old entity after the user explicitly switched topics.", "Treating a prior assistant answer as a verified source for the next query.", "Taking tenant access from dialogue text instead of the active session.", "Resolving an ambiguous pronoun to the first-ranked passage without asking."],
        "drill": "Write 59 multi-turn queries with corrections, topic changes and ambiguous references. Record rewrite accuracy, authorized passage recall and final support, and require clarification for turns with no unique antecedent.",
        "related": [prefix + "query-intent-and-retrieval-routing", prefix + "permission-aware-cache-and-conversation-turns", prefix + "temporal-retrieval-as-of-validity-and-conflicts", prefix + "evidence-bound-answer-and-abstention"],
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
        "featured": False, "sort_order": 8445 + offset, "status": "published",
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
    row["data"]["modules"].append({"title": "Scans, geography, records and dialogue", "lessons": new_paths})
    row["body"] += '<h2>Scans, geography, records and dialogue</h2><ul>' + ''.join(
        f'<li>{link(target)}</li>' for target in new_paths) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "source-extraction-and-passage-provenance": [new_paths[0]],
    prefix + "query-intent-and-retrieval-routing": [new_paths[1], new_paths[3]],
    prefix + "table-retrieval-and-numeric-cell-context": [new_paths[2]],
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
