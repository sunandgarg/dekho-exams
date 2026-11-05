"""Add the next original Retrieval AI lesson packet."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-retrieval-ai-next-import-20261007.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "retrieval-ai/"
hub_path = prefix + "retrieval-ai-tutorial"

lessons = [
    {
        "slug": "multi-hop-evidence-chain-and-stop-rules",
        "title": "Multi-hop retrieval: build evidence chains with bounded searches",
        "summary": "Answer questions whose facts sit in separate documents without letting a plausible first hit become an unsupported final answer.",
        "sections": [
            ("Represent the missing link", "A multi-hop question needs two or more supported joins. A support ticket may name shipment SH-47, while the carrier notice names only its dispatch batch. First retrieve the ticket and extract its batch ID. Then search that exact ID in the permitted carrier corpus. Keep each edge as a tuple of source passage, extracted entity, target passage and match rule. The final answer must cite both ends of the join. [[retrieval-ai/claim-level-citation-and-support-checks|Claim support]] should reject a chain whose second edge is only a semantic resemblance."),
            ("Search in a fixed budget", "Give each hop its own candidate limit, time limit and permission filter. The planner can propose the next lookup, but application code should validate the proposed identifier against the preceding passage before executing it. Stop after a bounded number of hops; a loop between two documents is a failed search, not deeper reasoning. If the first document names two batches, branch into two explicit chains and keep their evidence separate until a source disambiguates them."),
            ("Preserve uncertainty", "The chain may support that SH-47 belongs to batch BX-83 and that BX-83 was delayed. It does not prove the customer's delivery date changed unless a permitted source states that consequence. Distinguish a missing edge from a contradictory edge. Missing means the lookup exhausted its budget; contradictory means two eligible sources disagree and require revision or time resolution. [[retrieval-ai/evidence-bound-answer-and-abstention|Abstention]] is the correct output when a required edge has no evidence."),
            ("Evaluate the joins", "Judgments should name the expected intermediate entity and answer-bearing passages, not only the answer text. Record success at hop one, success at hop two, chain precision and final claim support independently. A fluent answer can hide a bad join. Include decoy IDs with similar spelling, revoked passages, duplicate entity names across tenants and an answer that requires three documents. A single overall accuracy score will obscure which hop fails."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class Evidence:
    passage_id: str
    tenant: str
    entity_id: str
    linked_id: str

def trace_shipment(shipment_id: str, tenant: str,
                   tickets: list[Evidence], notices: list[Evidence]) -> list[tuple[str, str]]:
    chains = []
    for ticket in tickets:
        if ticket.tenant != tenant or ticket.entity_id != shipment_id:
            continue
        for notice in notices:
            if notice.tenant == tenant and notice.entity_id == ticket.linked_id:
                chains.append((ticket.passage_id, notice.passage_id))
    return chains

tickets = [Evidence("ticket-47-r2", "north", "SH-47", "BX-83")]
notices = [Evidence("notice-83-r4", "north", "BX-83", "late"),
           Evidence("notice-83-private", "south", "BX-83", "cancelled")]
assert trace_shipment("SH-47", "north", tickets, notices) == [
    ("ticket-47-r2", "notice-83-r4")]
assert trace_shipment("SH-47", "south", tickets, notices) == []''',
        "cost": "The transparent nested-loop baseline costs O(TN) time for T tickets and N notices and O(C) space for C chains. Index notices by tenant and entity to reduce the join to O(T + N + C) build-and-probe time. Each extra retrieval hop adds latency and new failure opportunities, so cap depth and branch count before generation.",
        "mistakes": ["Using a model-generated intermediate ID that is absent from the cited passage.", "Combining passages from different tenants because the entity text matches.", "Claiming a downstream consequence that neither source states.", "Allowing repeated hops to search indefinitely."],
        "drill": "Create 37 questions: 19 valid two-hop chains, six ambiguous branches, five missing second edges, four decoy IDs and three revoked intermediates. Report first-hop and full-chain recall separately.",
        "related": [prefix + "query-intent-and-retrieval-routing", prefix + "claim-level-citation-and-support-checks", prefix + "permission-aware-cache-and-conversation-turns", prefix + "retrieval-release-evaluation-and-slice-gates"],
    },
    {
        "slug": "table-retrieval-and-numeric-cell-context",
        "title": "Table retrieval: keep numeric cells attached to their labels",
        "summary": "Retrieve tabular evidence without losing row keys, column units, revision dates or the calculation needed for an answer.",
        "sections": [
            ("Treat a cell as a qualified fact", "The value 47 has no useful meaning alone. A searchable fact needs table ID, revision, row key, column name, unit, effective period and access label. Store a compact row rendering for discovery, but preserve typed cells for comparison and arithmetic. A question about the West queue's 47-hour target must not match a North queue row or a 47-day retention policy. [[retrieval-ai/source-extraction-and-passage-provenance|Extraction provenance]] should point back to the original table location."),
            ("Separate discovery from computation", "Use lexical or semantic search to locate a candidate table, then execute an approved operation over its typed rows. Do not derive a total by reading the top few text snippets; omitted rows silently bias the result. Exact row and column filters should run before aggregation. If the requested metric is not defined, ask for the metric rather than inventing a sum. Record the row IDs used so the answer can be audited after a table revision."),
            ("Handle headers and units", "Merged headings, repeated page headers and blank cells need explicit parsing rules. A blank value can mean unknown, not zero. A percentage column cannot be summed like a count, and a currency column cannot be combined across currencies without a declared conversion rule. If a table changes from hours to minutes in a new revision, the retrieval layer must not silently mix both. [[retrieval-ai/freshness-deletion-and-index-swap|Index swaps]] should move the searchable row text and typed table together."),
            ("Test answer coverage", "Judged queries should include an exact cell lookup, a filter plus sum, a percentage with denominator, a missing cell and a superseded revision. Evaluate table discovery separately from calculation correctness. A system that retrieves the right table but adds the wrong rows still fails. For each calculated answer, retain the operation, selected row keys, table revision and resulting value."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class QueueRow:
    region: str
    week: int
    resolved: int | None
    revision: str

def resolved_total(rows: list[QueueRow], region: str, weeks: set[int],
                   revision: str) -> int:
    selected = [row for row in rows if row.region == region
                and row.week in weeks and row.revision == revision]
    if len(selected) != len(weeks) or any(row.resolved is None for row in selected):
        raise ValueError("incomplete table coverage")
    if len({row.week for row in selected}) != len(selected):
        raise ValueError("duplicate row key")
    return sum(row.resolved for row in selected if row.resolved is not None)

queue_rows = [QueueRow("West", 31, 47, "r8"),
              QueueRow("West", 32, 29, "r8"),
              QueueRow("North", 31, 81, "r8")]
assert resolved_total(queue_rows, "West", {31, 32}, "r8") == 76
try:
    resolved_total(queue_rows, "West", {31, 33}, "r8")
except ValueError:
    pass
else:
    raise AssertionError("missing week was accepted")''',
        "cost": "The baseline scans N rows in O(N) time and stores O(K) selected rows. A typed index on revision, region and week avoids a full scan in a large warehouse; query cost then depends on matching rows and index lookup. Preserve row lineage even if it adds metadata, because a wrong numeric answer is harder to diagnose than a slow lookup.",
        "mistakes": ["Embedding isolated numeric cells without their row and column labels.", "Treating blank cells as zero during aggregation.", "Summing a top-k snippet sample instead of the full filtered table.", "Combining rows from different revisions or units."],
        "drill": "Build a 29-row queue table with two revisions and three regions. Answer 12 cell questions and eight aggregate questions. Make two cells blank and one row duplicated; require explicit errors for both cases.",
        "related": [prefix + "source-extraction-and-passage-provenance", prefix + "query-intent-and-retrieval-routing", prefix + "claim-level-citation-and-support-checks", "data-engineering/schema-compatibility-and-consumer-rollout"],
    },
    {
        "slug": "multimodal-retrieval-and-asset-identity",
        "title": "Multimodal retrieval: connect images, OCR and text to one asset identity",
        "summary": "Search image-bearing documents while keeping captions, OCR text, crop coordinates and permissions tied to the exact source revision.",
        "sections": [
            ("Define the asset graph", "A diagram may have a text caption, OCR labels, a surrounding paragraph and a visual embedding. Give all views one immutable asset revision, then store their own modality and location. A match in OCR is evidence for visible words, not for a visual relation that OCR cannot read. A visual similarity match locates candidate images; it does not prove that two valves have the same operating limit. [[retrieval-ai/source-extraction-and-passage-provenance|Source provenance]] must survive the modality change."),
            ("Retrieve and fuse carefully", "Text queries can search captions and OCR; image queries can use visual embeddings. Fuse candidate asset IDs only after permission and revision checks. Preserve the match route in the result: caption, OCR, surrounding text or image similarity. This matters when a reviewer asks why a drawing ranked first. Rerank with the full question and a bounded set of candidate assets, not a collection of detached crop embeddings."),
            ("Resolve the cited region", "An answer about a label in the upper-left crop should cite that region and its parent page. Store normalized crop coordinates and the original image dimensions so a viewer can highlight the right area. If preprocessing rotates or resizes the image, transform coordinates back before presenting them. A citation to an entire manual page may be too broad when the claim depends on a tiny annotation. [[retrieval-ai/claim-level-citation-and-support-checks|Support checks]] should confirm the cited modality can prove the claim."),
            ("Measure modality-specific misses", "Maintain query slices for exact OCR strings, paraphrased captions, visual resemblance and questions requiring both text and image. Evaluate candidate recall by modality and asset revision. A high combined score can conceal that OCR systematically misses rotated labels. Keep a no-answer slice where a visually similar image lacks the requested label, and require the system to say so."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class AssetView:
    asset_id: str
    revision: str
    tenant: str
    modality: str
    content: str

def find_label(views: list[AssetView], label: str, tenant: str,
               active_revisions: dict[str, str]) -> list[str]:
    return sorted({view.asset_id for view in views
                   if view.tenant == tenant and view.modality == "ocr"
                   and active_revisions.get(view.asset_id) == view.revision
                   and label.casefold() in view.content.casefold()})

views = [AssetView("pump-47", "r3", "plant-a", "ocr", "Outlet 47 kPa"),
         AssetView("pump-47", "r2", "plant-a", "ocr", "Outlet 73 kPa"),
         AssetView("pump-47", "r3", "plant-b", "ocr", "Outlet 47 kPa")]
assert find_label(views, "47 kPa", "plant-a", {"pump-47": "r3"}) == ["pump-47"]
assert find_label(views, "73 kPa", "plant-a", {"pump-47": "r3"}) == []''',
        "cost": "The sample scans V views in O(V) time and uses O(A) result space for A matching assets. Production retrieval can index each modality, but storage and embedding work grow with the number of views and crops. Set crop limits and deduplicate near-identical renders; otherwise one document can flood the candidate window.",
        "mistakes": ["Using visual similarity as proof of a printed numeric label.", "Returning a crop without its parent asset and revision.", "Mixing a fresh caption with OCR from an old image revision.", "Showing a broad page citation when only one crop supports the answer."],
        "drill": "Index 17 diagrams with captions and OCR, including three rotated scans and two superseded revisions. Judge exact-label, visual and mixed queries separately; verify every cited crop opens at the correct page and coordinates.",
        "related": [prefix + "source-extraction-and-passage-provenance", prefix + "context-packing-and-evidence-diversity", prefix + "claim-level-citation-and-support-checks", prefix + "filtered-ann-recall-and-latency"],
    },
    {
        "slug": "incremental-ingestion-idempotency-and-delete-races",
        "title": "Incremental retrieval ingestion: replay events without reviving deleted passages",
        "summary": "Apply document revisions, permission changes and deletions safely when source events arrive late, twice or out of order.",
        "sections": [
            ("Make the event contract explicit", "Each source event needs tenant, document ID, monotonic source version, action and a stable event ID. The index writer should compare versions before replacing passages. At-least-once delivery means duplicate events are normal; processing the same revision twice must yield the same searchable state. A late upsert for version 6 cannot restore a document deleted at version 8. [[retrieval-ai/freshness-deletion-and-index-swap|Index freshness]] depends on this ordering rule."),
            ("Separate removal from embedding work", "Delete and permission-revocation events should invalidate answer caches and remove eligible passages promptly. A new revision may take longer because extraction and embeddings run asynchronously. During that interval, either keep an explicitly permitted old revision under a defined policy or mark the document unavailable. Do not show a half-written revision whose metadata and vectors disagree. Publish the new generation only after all required passages and filters are ready."),
            ("Retain a tombstone", "A tombstone records the latest delete version even after the vector rows are removed. Without it, a replayed old upsert can recreate a deleted passage. Keep the tombstone until upstream retention guarantees make older events impossible, and test that guarantee rather than guessing. A permission change also needs a versioned marker; it may be independent of content revision and should not wait for re-embedding."),
            ("Observe lag and recovery", "Measure event age at application, pending extraction count, index generation and deletion-to-unavailability delay. Replay a durable event log into a staging index, compare eligible document sets, then atomically switch the alias. [[retrieval-ai/embedding-space-version-and-migration|Encoder migrations]] need the same generation boundary. A process restart should resume from a checkpoint without losing the version guard."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class DocumentEvent:
    document_id: str
    version: int
    action: str
    text: str = ""

def apply_event(state: dict[str, tuple[int, str | None]],
                event: DocumentEvent) -> None:
    current_version = state.get(event.document_id, (-1, None))[0]
    if event.version <= current_version:
        return
    if event.action == "delete":
        state[event.document_id] = (event.version, None)
    elif event.action == "upsert" and event.text.strip():
        state[event.document_id] = (event.version, event.text)
    else:
        raise ValueError("invalid document event")

index_state: dict[str, tuple[int, str | None]] = {}
apply_event(index_state, DocumentEvent("policy-47", 8, "delete"))
apply_event(index_state, DocumentEvent("policy-47", 6, "upsert", "old policy"))
apply_event(index_state, DocumentEvent("policy-47", 8, "delete"))
assert index_state["policy-47"] == (8, None)''',
        "cost": "The version guard is O(1) expected time per event with a hash map and O(D) state for D documents. Extraction and embedding dominate CPU and queue time. Tombstones consume storage, but deleting them too early risks data resurrection. Report end-to-end publication lag and revocation lag separately.",
        "mistakes": ["Deleting vector rows without retaining the latest source version.", "Assuming queue delivery is exactly once or ordered across partitions.", "Waiting for slow re-embedding before enforcing a permission revocation.", "Publishing metadata for a new revision before its passage set is complete."],
        "drill": "Replay 53 events with duplicates, delayed upserts, revisions and deletes into an empty index. Shuffle events while preserving per-document source versions; assert that eligible final documents and tombstones match the source of truth.",
        "related": [prefix + "freshness-deletion-and-index-swap", prefix + "corpus-permissions-and-document-lifecycle", prefix + "embedding-space-version-and-migration", prefix + "permission-aware-cache-and-conversation-turns"],
    },
    {
        "slug": "retrieval-traces-and-incident-debugging",
        "title": "Retrieval traces: locate the stage that lost the answer",
        "summary": "Trace routing, filtering, candidate generation, reranking and context packing so a failed answer can be explained and repaired.",
        "sections": [
            ("Record stage boundaries", "A single total latency and final answer are not enough. Give each query a trace ID and record route, index generation, encoder revision, allowed corpus scope, candidate counts, reranker cutoff, context IDs and answer citations. Keep the original query in a protected audit store when policy permits; avoid putting private text, user IDs or document contents into metric labels. [[retrieval-ai/query-intent-and-retrieval-routing|Routing]] and [[retrieval-ai/context-packing-and-evidence-diversity|packing]] need separate spans."),
            ("Name the first failing stage", "If the answer-bearing passage is absent from candidate retrieval, changing the prompt will not fix it. If it appears at rank 12 but the reranker receives only eight, the candidate window is the failure. If it reaches the context packet but the model cites another passage, investigate answer synthesis and support checking. Diagnose against a judged passage ID, not a vague statement that search felt poor."),
            ("Keep traces safe and bounded", "Trace metadata can itself expose sensitive document names or tenant relationships. Hash or redact identifiers in broad telemetry, reserve full IDs for access-controlled debugging, and apply retention limits. Sample routine traffic, but retain all permission denials, deletion races and release-gate failures under an approved policy. A trace with every passage text can cost more to store than the retrieved context and may violate the source's access boundary."),
            ("Use paired comparisons", "Replay a fixed query against current and candidate releases with the same corpus snapshot and permission scope. Diff each stage: route, top-k identities, filters, rerank order, context selection and citations. This isolates a changed encoder from a changed index or prompt. [[retrieval-ai/retrieval-release-evaluation-and-slice-gates|Release gates]] should attach these traces to failures so a rollback decision has evidence."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class RetrievalTrace:
    expected_passage: str
    candidates: tuple[str, ...]
    reranked: tuple[str, ...]
    context: tuple[str, ...]
    cited: tuple[str, ...]

def first_loss(trace: RetrievalTrace) -> str:
    stages = (("candidate retrieval", trace.candidates),
              ("reranking", trace.reranked),
              ("context packing", trace.context),
              ("answer citation", trace.cited))
    for stage_name, passage_ids in stages:
        if trace.expected_passage not in passage_ids:
            return stage_name
    return "supported path"

incident = RetrievalTrace("policy-47-r3", ("policy-47-r3", "memo-29"),
                          ("memo-29",), ("memo-29",), ("memo-29",))
assert first_loss(incident) == "reranking"
assert first_loss(RetrievalTrace("missing", (), (), (), ())) == "candidate retrieval"''',
        "cost": "Finding the first loss scans at most the four recorded stage lists, O(K) time for K total IDs and O(1) extra space. A full trace pipeline adds serialization, storage and review cost proportional to captured candidates. Sample successful queries and store compact IDs; preserve richer traces for judged failures under access control.",
        "mistakes": ["Blaming generation when the answer passage never entered candidate retrieval.", "Logging private passage text or principal IDs in broad metric labels.", "Comparing releases against different corpus snapshots.", "Recording only final scores and losing stage identities."],
        "drill": "Create 41 judged traces with deliberate failures at each stage. Produce a count by first-loss stage and inspect one trace from each category before changing any retrieval parameter.",
        "related": [prefix + "retrieval-release-evaluation-and-slice-gates", prefix + "reranker-candidate-window-and-budget", prefix + "context-packing-and-evidence-diversity", prefix + "claim-level-citation-and-support-checks"],
    },
    {
        "slug": "query-expansion-guardrails-and-drift-tests",
        "title": "Query expansion: add recall terms without changing the user's question",
        "summary": "Use controlled synonyms and subqueries while retaining exact IDs, exclusions, dates and authorization scope.",
        "sections": [
            ("Split immutable constraints from optional terms", "Parse exact identifiers, quoted phrases, exclusions, tenant scope and time bounds before expansion. Keep those constraints attached to every generated subquery. A query for case AX-47 after September must not turn into a general query about delayed cases. Expansion is useful for vocabulary mismatch: ‘chargeback’ may appear as ‘payment dispute’ in a permitted document. It is not permission to relax an exact case ID. [[retrieval-ai/query-intent-and-retrieval-routing|Routing]] should decide whether expansion is needed at all."),
            ("Bound candidates and weights", "Start with a small, reviewed synonym list or a validated reformulator. Search the original query as one leg and each expansion as a separate leg, then merge by passage ID. Preserve which leg found each candidate. Weight the original query and exact-match leg so a broad synonym cannot bury the literal target. [[retrieval-ai/hybrid-search-and-reciprocal-rank-fusion|Rank fusion]] is a useful merge baseline because score scales from different legs are not directly comparable."),
            ("Reject drift", "A proposed rewrite fails when it drops an identifier, changes a number, reverses a negation, broadens a tenant, or shifts a date interval. Compare parsed constraints before executing the rewrite. Some vocabulary changes are context dependent: ‘hold’ can mean a payment hold or warehouse hold. For ambiguous terms, retrieve with both senses only inside the authorized corpus and let evidence disambiguate; otherwise ask the user."),
            ("Measure value by query family", "Expansion should improve recall for jargon and paraphrase queries without harming exact-ID precision or latency. Build paired judgments with original-only and expanded runs. Report newly found answer passages, false positives, average additional calls and p95 latency. Retain a no-answer set; a system that answers more questions by matching unrelated synonyms has not improved. [[retrieval-ai/retrieval-traces-and-incident-debugging|Traces]] should expose which expansion introduced each candidate."),
        ],
        "code": '''import re

def safe_expansions(question: str, synonyms: dict[str, tuple[str, ...]]) -> list[str]:
    required_ids = set(re.findall(r"\\bAX-\\d+\\b", question.upper()))
    variants = [question]
    for term, replacements in synonyms.items():
        if not re.search(rf"\\b{re.escape(term)}\\b", question, re.IGNORECASE):
            continue
        for replacement in replacements[:2]:
            candidate = re.sub(rf"\\b{re.escape(term)}\\b", replacement,
                               question, count=1, flags=re.IGNORECASE)
            if required_ids <= set(re.findall(r"\\bAX-\\d+\\b", candidate.upper())):
                variants.append(candidate)
    return variants[:4]

variants = safe_expansions("AX-47 chargeback status",
                           {"chargeback": ("payment dispute", "card dispute")})
assert variants == ["AX-47 chargeback status",
                    "AX-47 payment dispute status", "AX-47 card dispute status"]
assert all("AX-47" in variant for variant in variants)''',
        "cost": "For Q query characters and at most S reviewed replacements, this small implementation scans O(SQ) time and stores at most four variants. Search cost can grow roughly with the number of variants, so cap expansion count and parallel calls. This demonstration protects exact IDs only; production validation must also compare negations, dates, tenant scope and other parsed constraints before dispatch.",
        "mistakes": ["Replacing an exact identifier with a likely-looking related identifier.", "Dropping ‘not’ or a date bound while rewriting.", "Merging scores from different search legs as if their scales were equal.", "Celebrating recall gains without measuring no-answer false positives."],
        "drill": "Judge 61 requests across exact IDs, jargon synonyms, negations, date bounds and no-answer cases. Compare original-only search with a maximum of three expanded variants; reject any rewrite that changes parsed constraints.",
        "related": [prefix + "query-intent-and-retrieval-routing", prefix + "hybrid-search-and-reciprocal-rank-fusion", prefix + "retrieval-traces-and-incident-debugging", prefix + "retrieval-release-evaluation-and-slice-gates"],
    },
]

new_paths = [prefix + item["slug"] for item in lessons]
assert len(set(new_paths)) == len(new_paths)
assert not set(new_paths) & by_path.keys()
titles = {path: row["title"] for path, row in by_path.items()}
titles.update(zip(new_paths, (item["title"] for item in lessons)))
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

def body_for(item: dict) -> str:
    body = f'<p>{render(item["summary"])}</p>'
    for heading, paragraph in item["sections"]:
        body += f'<h2>{html.escape(heading)}</h2><p>{render(paragraph)}</p>'
    body += '<h2>Worked contract</h2><pre><code class="language-python">' + html.escape(item["code"]) + '</code></pre>'
    body += '<h2>Performance and operating cost</h2><p>' + render(item["cost"]) + '</p>'
    body += '<h3>Common Mistakes</h3><ul>' + ''.join(f'<li>{render(value)}</li>' for value in item["mistakes"]) + '</ul>'
    body += '<h2>Validation drill</h2><p>' + render(item["drill"]) + '</p>'
    body += '<h2>Read next</h2><ul>' + ''.join(f'<li>{link(path)}</li>' for path in item["related"]) + '</ul>'
    return body

changed = []
for offset, item in enumerate(lessons):
    path = new_paths[offset]
    body = body_for(item)
    row = {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
        "type": "article", "path": path, "title": item["title"],
        "summary": item["summary"], "body": body, "category": "AI & Data",
        "subject": "retrieval-ai", "difficulty": "Advanced",
        "tags": ["ai-data", "retrieval-ai", "tutorial"], "potd_date": None,
        "featured": False, "sort_order": 8427 + offset, "status": "published",
        "published_at": stamp, "created_at": stamp, "updated_at": stamp,
        "data": {"subject_root": hub_path, "section_path": hub_path,
                 "content_format": "html", "seo_ready": True, "kind": "tutorial",
                 "reading_minutes": max(6, round(len(re.sub('<[^>]+>', ' ', body).split()) / 180)),
                 "author_path": "authors/aitrove-editorial",
                 "verification_suite": "Executable standard-library example and editorial review",
                 "related": [{"path": path, "title": titles[path]} for path in item["related"]]},
    }
    rows.append(row)
    by_path[path] = row
    changed.append(row)

for path, title in ((hub_path, "Evidence beyond plain passages"),
                    ("retrieval-ai", "Evidence beyond plain passages")):
    row = by_path[path]
    row["data"]["modules"].append({"title": title, "lessons": new_paths})
    row["body"] += '<h2>' + html.escape(title) + '</h2><ul>' + ''.join(
        f'<li>{link(target)}</li>' for target in new_paths) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "claim-level-citation-and-support-checks": new_paths[:3],
    prefix + "source-extraction-and-passage-provenance": new_paths[1:3],
    prefix + "freshness-deletion-and-index-swap": [new_paths[3]],
    prefix + "retrieval-release-evaluation-and-slice-gates": new_paths[3:],
    prefix + "query-intent-and-retrieval-routing": [new_paths[0], new_paths[5]],
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
