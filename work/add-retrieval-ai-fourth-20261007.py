"""Add original retrieval lessons on structure, ranking, time and duplication."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-retrieval-ai-fourth-import-20261007.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "retrieval-ai/"
hub_path = prefix + "retrieval-ai-tutorial"

lessons = [
    {
        "slug": "hierarchical-retrieval-and-parent-child-evidence",
        "title": "Hierarchical retrieval: find a section before selecting its evidence",
        "summary": "Route through document structure while keeping answer citations on the smallest passage that actually proves the claim.",
        "sections": [
            ("Index two useful levels", "Hierarchical retrieval searches a document tree before choosing answer-bearing passages. A maintenance manual's chapter heading may say 'hydraulic pressure', while the relevant sentence appears in a child paragraph about pump P-47. Store a parent summary and child passages with stable IDs, revision and access label. The parent helps locate the right region; the child proves the claim. A heading alone is not evidence for a numeric limit. [[retrieval-ai/chunk-identity-and-context-boundaries|Chunk identity]] should preserve the original section path rather than replacing it with a generated synopsis."),
            ("Route with reversible decisions", "A top-level search can choose candidate manuals, then section headings, then paragraphs. Keep more than one plausible branch when the query is ambiguous, and record each routing decision in the trace. If the first branch fails an evidence test, a bounded sibling search can recover a missed section. Do not let a model invent a chapter name or crawl indefinitely. [[retrieval-ai/corrective-retrieval-and-bounded-retry|Corrective retrieval]] needs a named failure and a fixed search budget, not an open-ended promise to look harder."),
            ("Apply permissions at both levels", "A parent section might be visible while a child appendix is restricted. Filtering only the parent can expose child text; filtering only the child can reveal restricted section names through the navigation path. Bind tenant, role and revision to every node. If a parent is revoked, descendant eligibility must be recomputed or removed. An index generation should publish its tree and its passage store together, so a parent does not point to a child from an older revision. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Document lifecycle]] rules still govern tree traversal."),
            ("Avoid parent dominance", "Long section summaries can match many queries and crowd out precise passages. Allocate a small number of candidate parents, then a separate child window per parent; finally merge child passages with diversity controls. The result should carry its route and its actual supporting span. If the answer requires two sections, preserve both branches instead of concatenating one chapter's unrelated paragraphs. [[retrieval-ai/context-packing-and-evidence-diversity|Context packing]] should count evidence coverage, not just total tokens."),
            ("Judge routing and support separately", "Evaluation should report whether the right document was found, whether the right section survived routing, whether the supporting child reached the candidate window, and whether the answer cited it. Include misleading headings, appendices, renamed chapters, cross-section questions and restricted child nodes. A router may have high document recall but poor child recall. Preserve first-loss traces to locate that gap before changing the model or the prompt."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class PassageNode:
    passage_id: str
    parent_id: str
    tenant: str
    revision: str
    text: str

def children_for_section(nodes: list[PassageNode], section_id: str,
                         tenant: str, revision: str, term: str) -> list[str]:
    return [node.passage_id for node in nodes
            if node.parent_id == section_id and node.tenant == tenant
            and node.revision == revision and term.casefold() in node.text.casefold()]

manual = [PassageNode("pump-47-limit", "hydraulics-r3", "plant-a", "r3",
                      "Pump P-47 relief limit is 83 kPa."),
          PassageNode("pump-47-old", "hydraulics-r2", "plant-a", "r2",
                      "Pump P-47 relief limit is 71 kPa."),
          PassageNode("private-limit", "hydraulics-r3", "plant-b", "r3",
                      "Pump P-47 relief limit is 99 kPa.")]
assert children_for_section(manual, "hydraulics-r3", "plant-a", "r3", "83 kPa") == [
    "pump-47-limit"]
assert children_for_section(manual, "hydraulics-r3", "plant-a", "r3", "99 kPa") == []''',
        "cost": "This transparent child scan is O(N) time for N nodes and O(K) space for K matches. A production index keyed by parent, tenant and revision reduces the eligible scan, but tree traversal adds parent-search and child-search latency. Keep branch count and depth bounded; broad hierarchies can cost more than one flat retrieval call without improving support.",
        "mistakes": ["Citing a section summary that does not contain the claimed number.", "Pruning every branch except the first plausible heading.", "Applying access control to a parent but not its children.", "Publishing a parent tree and child passages from different document revisions."],
        "drill": "Index 23 manuals with three levels each. Judge 37 queries, including misleading headings and restricted appendices; report document, section and child-passage recall separately.",
        "related": [prefix + "chunk-identity-and-context-boundaries", prefix + "context-packing-and-evidence-diversity", prefix + "corrective-retrieval-and-bounded-retry", "knowledge-graphs/query-paths-and-answer-boundaries"],
    },
    {
        "slug": "late-interaction-ranking-and-token-budget",
        "title": "Late-interaction retrieval: score token matches without one-vector blur",
        "summary": "Compare multi-vector passage ranking with single-vector search while accounting for storage, candidate pruning and token-level false matches.",
        "sections": [
            ("Keep token evidence visible", "A single vector compresses a whole passage into one representation. Late-interaction ranking keeps multiple token vectors for the query and passage, then combines their best token-level matches. This can preserve a rare part number alongside broad topic words. It is a ranking signal, not a proof that a passage answers the question: matching 'P-47', 'pressure' and 'limit' in separate sentences could still miss the requested limit. [[retrieval-ai/claim-level-citation-and-support-checks|Claim support]] must inspect the actual text after ranking."),
            ("Separate candidate generation from scoring", "Scoring every passage token against every query token is expensive. First build a candidate set with lexical or approximate vector search, apply tenant and revision filters, then run token-level scoring on a bounded window. If the correct passage never enters that window, late interaction cannot rescue it. [[retrieval-ai/filtered-ann-recall-and-latency|Filtered candidate recall]] and [[retrieval-ai/reranker-candidate-window-and-budget|reranker window size]] should be measured before debating score formulas."),
            ("Explain the aggregation", "One simple late-interaction score takes each query token's best similarity to any passage token and sums those maxima. It rewards coverage of query terms while allowing different passage tokens to satisfy them. Normalize or calibrate for query length when comparing across questions; within one query, ranking scores can be compared directly. Stop words, duplicated tokens and template boilerplate can distort results. A document containing twenty copies of a part label should not gain twenty independent votes from one query term."),
            ("Budget memory and CPU", "Multi-vector passages consume more index space than a single vector per passage. Token pruning, low-precision storage and candidate caps reduce cost, but each can reduce recall. Measure bytes per passage, index build time, p95 query latency and judged passage recall together. Keep encoder version and tokenization version on the index; a query encoded with a different vocabulary or model revision can change rankings without any corpus update. [[retrieval-ai/embedding-space-version-and-migration|Embedding migrations]] need paired tests."),
            ("Test the hard queries", "Include near-identical part numbers, terms scattered across unrelated sections, long passages, short passages and one genuinely absent answer. Report candidate recall, rank after late interaction, and final support separately. A high ranking score for a passage with all query words but no answer is an expected failure mode to catch, not a reason to weaken the citation check."),
        ],
        "code": '''from math import sqrt

def cosine(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = sqrt(sum(value * value for value in left))
    right_norm = sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        raise ValueError("zero-length token vector")
    return numerator / (left_norm * right_norm)

def token_coverage(query_tokens: list[tuple[float, ...]],
                   passage_tokens: list[tuple[float, ...]]) -> float:
    if not query_tokens or not passage_tokens:
        raise ValueError("empty token sequence")
    return sum(max(cosine(query, passage) for passage in passage_tokens)
               for query in query_tokens)

pressure_query = [(1.0, 0.0), (0.0, 1.0)]
complete_passage = [(1.0, 0.0), (0.0, 1.0)]
partial_passage = [(1.0, 0.0), (1.0, 0.0)]
assert token_coverage(pressure_query, complete_passage) == 2.0
assert token_coverage(pressure_query, partial_passage) == 1.0''',
        "cost": "For Q query tokens, P passage tokens and D vector dimensions, direct scoring costs O(QPD) time and O(1) extra space beyond the vectors. For C candidates, multiply that work by C. Index storage grows with passage token count rather than passage count alone, so use a candidate stage and measure the cost of any compression or token pruning.",
        "mistakes": ["Running token-level scoring over the entire corpus without a candidate bound.", "Treating token coverage as proof that the passage states the requested fact.", "Mixing encoder or tokenizer revisions between query and index.", "Ignoring storage growth when comparing against a single-vector baseline."],
        "drill": "Judge 49 part-number questions with close distractors. Compare a single-vector baseline and a bounded token-level reranker on candidate recall, supported top-one answers, index bytes and p95 latency.",
        "related": [prefix + "filtered-ann-recall-and-latency", prefix + "reranker-candidate-window-and-budget", prefix + "embedding-space-version-and-migration", prefix + "claim-level-citation-and-support-checks"],
    },
    {
        "slug": "temporal-retrieval-as-of-validity-and-conflicts",
        "title": "Temporal retrieval: answer as-of questions from valid evidence",
        "summary": "Distinguish when a fact was true from when it was indexed, and resolve overlapping revisions before producing a dated answer.",
        "sections": [
            ("Store two clocks", "Temporal retrieval answers questions about a specified point in time. A policy may be valid from 1 March to 30 June yet ingested on 4 March. Valid time describes when the policy applies; system time describes when the search system learned or changed it. Conflating the two makes historical answers wrong after a late upload or backdated correction. Record both intervals and the source revision. [[retrieval-ai/freshness-deletion-and-index-swap|Index freshness]] explains availability, while valid time determines which fact belongs in the answer."),
            ("Parse the user's time boundary", "An as-of question needs a date, time zone and boundary convention. 'On 30 June' may mean any instant that day; an interval ending at midnight on 30 June may already be invalid then. Choose half-open intervals consistently: start inclusive, end exclusive. If the user gives only a month, do not quietly pick its last day for a rule that changed mid-month. Ask for a date or return the change range. [[retrieval-ai/query-intent-and-retrieval-routing|Query routing]] should preserve the time constraint across every retrieval leg."),
            ("Filter before ranking", "Restrict candidates to the requested valid-time interval and authorized corpus before semantic ranking. A newer policy is often lexically similar and may rank above the old one even when the user asks about last year. An answer must cite the applicable revision and the effective interval. For a comparison across dates, retrieve each date separately and keep the two evidence sets distinct. A revision's publication timestamp is not a substitute for its effective timestamp."),
            ("Resolve overlap explicitly", "Two active records may cover the same instant because of a correction, overlapping jurisdiction or bad source data. Prefer a documented supersession rule only if the source provides one. Otherwise report the conflict with both citations and abstain from a single definitive value. A deletion may remove public availability without erasing the historical audit record; retrieval policy decides whether that archived evidence remains eligible. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Access control]] applies even to historical answers."),
            ("Judge temporal slices", "Build cases just before and after effective boundaries, retroactive corrections, delayed ingestion, unknown end dates, conflicting overlaps and no eligible history. Measure valid-revision recall and answer support separately from plain passage recall. A search that finds the right policy family but the wrong revision should fail the dated slice. Keep the corpus generation in the judgment so a changing source does not invalidate the comparison."),
        ],
        "code": '''from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class PolicyRevision:
    revision: str
    tenant: str
    valid_from: date
    valid_until: date | None
    refund_days: int

def applicable_policy(revisions: list[PolicyRevision], tenant: str,
                      as_of: date) -> PolicyRevision | None:
    matches = [policy for policy in revisions if policy.tenant == tenant
               and policy.valid_from <= as_of
               and (policy.valid_until is None or as_of < policy.valid_until)]
    if len(matches) > 1:
        raise ValueError("overlapping eligible policy revisions")
    return matches[0] if matches else None

policies = [PolicyRevision("r3", "north", date(2026, 3, 1), date(2026, 7, 1), 47),
            PolicyRevision("r4", "north", date(2026, 7, 1), None, 29),
            PolicyRevision("private", "south", date(2026, 3, 1), None, 83)]
assert applicable_policy(policies, "north", date(2026, 6, 30)).refund_days == 47
assert applicable_policy(policies, "north", date(2026, 7, 1)).refund_days == 29
assert applicable_policy(policies, "north", date(2026, 2, 28)) is None''',
        "cost": "The example scans R revisions in O(R) time and stores O(M) matches, where M is the number valid at the requested instant. A database interval index and tenant key can reduce candidate reads. Store valid-time and ingestion-time metadata separately; two extra timestamps are cheap compared with an unsupported historical answer.",
        "mistakes": ["Using ingestion time as the policy's effective date.", "Treating an interval end as inclusive in one service and exclusive in another.", "Returning the newest revision for every historical question.", "Silently choosing one of two overlapping eligible revisions."],
        "drill": "Create 61 dated questions around four policy transitions, including six backdated corrections and five overlaps. Require explicit ambiguity when the source cannot determine the applicable revision.",
        "related": [prefix + "freshness-deletion-and-index-swap", prefix + "query-intent-and-retrieval-routing", prefix + "retrieval-evaluation-labels-and-adjudication", prefix + "corpus-permissions-and-document-lifecycle"],
    },
    {
        "slug": "near-duplicate-evidence-and-independent-support",
        "title": "Near-duplicate retrieval: collapse copies without hiding independent evidence",
        "summary": "Deduplicate copied passages by lineage and revision while preserving genuinely independent sources for corroboration.",
        "sections": [
            ("Separate copies from corroboration", "A retrieval result can contain a policy paragraph copied into twelve team notes. Twelve hits are not twelve independent confirmations. Store document lineage, source owner, passage hash and revision so the system can group copies. Exact hashes catch byte-identical text; normalized hashes catch whitespace and formatting changes; semantic similarity can suggest near duplicates for review. A separate independent bulletin stating the same limit may be valuable corroboration and should not disappear merely because its wording is similar. [[retrieval-ai/source-extraction-and-passage-provenance|Provenance]] decides which case applies."),
            ("Collapse at the right boundary", "Group near duplicates after access filtering. A user who can see the public manual but not a private support note must not see the private note's title or existence in the collapsed result. Within an eligible group, choose an authoritative active revision and retain a list of permitted copies for audit. Do not pick a superseded revision only because it has a higher lexical score. [[retrieval-ai/freshness-deletion-and-index-swap|Revision rules]] take precedence over ranking."),
            ("Protect the candidate window", "Repeated template text can consume most of top-k, leaving no room for another document needed to answer the question. Collapse copies before context selection and reserve slots for distinct source lineages. Track both raw hit count and independent-lineage count in traces; a result of 20 hits from one copied memo is effectively one source. [[retrieval-ai/context-packing-and-evidence-diversity|Evidence diversity]] should be measured at lineage level rather than URL count."),
            ("Choose a conservative similarity rule", "A shared heading and two similar sentences do not prove two passages are duplicates. Numeric values, negations, dates and identifiers can differ while the rest of the text matches. Treat changes in those fields as blockers to automatic collapse. For uncertain pairs, keep both or flag them for review. False merging removes possible contradictions; false separation mostly wastes context. This asymmetry argues for conservative thresholds and explicit field checks."),
            ("Test both errors", "Create copied passages, lightly reformatted copies, stale revisions and independently authored confirmations. Measure duplicate-group purity and answer-bearing passage recall after collapse. Include two near-identical policies whose refund windows differ and a copied note with a missing negation. The system should retain both contradictory policies for resolution, not merge them into a false consensus. [[retrieval-ai/retrieval-evaluation-labels-and-adjudication|Judged sets]] need lineage labels to make this visible."),
        ],
        "code": '''import re
from dataclasses import dataclass

@dataclass(frozen=True)
class EvidenceCopy:
    passage_id: str
    tenant: str
    lineage: str
    revision: int
    text: str

def normalize_copy(text: str) -> str:
    return re.sub(r"\\s+", " ", text.casefold()).strip()

def collapse_copies(passages: list[EvidenceCopy], tenant: str) -> list[EvidenceCopy]:
    chosen: dict[tuple[str, str], EvidenceCopy] = {}
    for passage in passages:
        if passage.tenant != tenant:
            continue
        key = (passage.lineage, normalize_copy(passage.text))
        if key not in chosen or passage.revision > chosen[key].revision:
            chosen[key] = passage
    return list(chosen.values())

copies = [EvidenceCopy("manual-r2", "north", "manual-47", 2, "Limit: 47 days"),
          EvidenceCopy("manual-r3", "north", "manual-47", 3, "Limit:  47 days"),
          EvidenceCopy("notice-r1", "north", "notice-83", 1, "Limit: 47 days"),
          EvidenceCopy("private-r4", "south", "manual-47", 4, "Limit: 47 days")]
assert {hit.passage_id for hit in collapse_copies(copies, "north")} == {
    "manual-r3", "notice-r1"}''',
        "cost": "The hash-based baseline scans N passages in O(NL) time for average passage length L and stores O(U) groups for U unique lineage-text pairs. Semantic near-duplicate detection adds candidate-pair and review cost; avoid an O(N squared) all-pairs scan on a large corpus by blocking on lineage, source type or approximate fingerprints first.",
        "mistakes": ["Counting copied team notes as independent evidence.", "Grouping before access checks and exposing restricted source metadata.", "Merging passages that differ in a number, negation or effective date.", "Keeping the highest-ranked stale copy instead of the active revision."],
        "drill": "Make 79 passages across 12 lineages with exact copies, formatting changes, copied notes and three contradictory revisions. Verify that collapse preserves all independent answer-bearing sources and no restricted metadata leaks.",
        "related": [prefix + "context-packing-and-evidence-diversity", prefix + "source-extraction-and-passage-provenance", prefix + "temporal-retrieval-as-of-validity-and-conflicts", prefix + "retrieval-evaluation-labels-and-adjudication"],
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
        "featured": False, "sort_order": 8437 + offset, "status": "published",
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
    row["data"]["modules"].append({"title": "Structure, ranking and time", "lessons": new_paths})
    row["body"] += '<h2>Structure, ranking and time</h2><ul>' + ''.join(
        f'<li>{link(target)}</li>' for target in new_paths) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "chunk-identity-and-context-boundaries": [new_paths[0]],
    prefix + "reranker-candidate-window-and-budget": [new_paths[1]],
    prefix + "freshness-deletion-and-index-swap": [new_paths[2]],
    prefix + "context-packing-and-evidence-diversity": [new_paths[0], new_paths[3]],
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
