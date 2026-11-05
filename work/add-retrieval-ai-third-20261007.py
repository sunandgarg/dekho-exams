"""Publish four original Retrieval AI lessons with curriculum links."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-retrieval-ai-third-import-20261007.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "retrieval-ai/"
hub_path = prefix + "retrieval-ai-tutorial"

lessons = [
    {
        "slug": "knowledge-graph-retrieval-and-edge-provenance",
        "title": "Knowledge graph retrieval: prove every edge in the path",
        "summary": "Use entity links to find candidate evidence while retaining the passage, relation type, revision and access rule that made each edge valid.",
        "sections": [
            ("Define the graph's evidence contract", "Graph retrieval stores entities and typed relations so a question can follow connections that text similarity misses. Consider a service case linked to a replacement part, which is linked to a supplier bulletin. A bare edge saying that a case uses a part is insufficient: the edge also needs the source passage, relation type, effective time, extraction method and tenant. The graph is a navigation index, not an authority separate from its documents. [[retrieval-ai/source-extraction-and-passage-provenance|Passage provenance]] lets a reviewer inspect the statement behind each edge."),
            ("Resolve entities before traversal", "An identifier can be reused across tenants, and two supplier names can refer to one organization. Resolve an entity only within its namespace and permitted source set. Keep aliases as attributed claims rather than overwriting the canonical node. For an ambiguous name, return candidate entities with their disambiguating attributes; do not silently merge them. A false merge makes every later traversal look plausible. Exact identifiers should remain exact even when a semantic retriever proposes a near match."),
            ("Bound traversal and evidence assembly", "Start from an authorized seed, expand only allowed relation types, cap hop count and degree, and reject a route if any edge lacks an active supporting passage. A popular supplier node may have thousands of neighbors; unrestricted breadth-first traversal can dominate latency and swamp the answer with irrelevant paths. Score the path by the weakest required edge and the question's relation sequence. [[retrieval-ai/multi-hop-evidence-chain-and-stop-rules|Multi-hop stop rules]] should halt when the requested join is proven or the search budget expires."),
            ("Treat updates as graph operations", "A document deletion must remove or invalidate all edges supported solely by that revision. If another active passage also supports an edge, the edge may survive with that other provenance. Keep an edge-to-passage reverse map to make revocation prompt. During a rebuild, compare node and edge counts by tenant, then test a set of known paths and forbidden paths before swapping the graph generation. [[retrieval-ai/incremental-ingestion-idempotency-and-delete-races|Versioned ingestion]] prevents an old event from reviving a revoked relation."),
            ("Judge paths, not fluent answers", "Create questions with known seed nodes, expected relation sequences and expected supporting passages. Report seed resolution, edge recall, valid-path recall and final claim support separately. Include a shared-name trap, a stale edge, a missing middle relation, a high-degree hub and a cross-tenant decoy. If the result uses a correct answer reached through unsupported edges, mark the path wrong: the route will fail on the next corpus revision."),
        ],
        "code": '''from collections import deque
from dataclasses import dataclass

@dataclass(frozen=True)
class SupportedEdge:
    source: str
    target: str
    relation: str
    tenant: str
    passage_id: str

def evidence_paths(edges: list[SupportedEdge], start: str, goal: str,
                   tenant: str, allowed: tuple[str, ...], degree_cap: int = 24):
    adjacency: dict[str, list[SupportedEdge]] = {}
    for edge in edges:
        if edge.tenant == tenant and edge.passage_id:
            adjacency.setdefault(edge.source, []).append(edge)
    frontier = deque([(start, ())])
    while frontier:
        node, path = frontier.popleft()
        if len(path) == len(allowed):
            if node == goal:
                return path
            continue
        candidates = [edge for edge in adjacency.get(node, ())
                      if edge.relation == allowed[len(path)]]
        for edge in candidates[:degree_cap]:
            if edge.target not in {start, *(part.target for part in path)}:
                frontier.append((edge.target, path + (edge,)))
    return ()

links = [SupportedEdge("case-47", "part-83", "uses", "north", "case-r2"),
         SupportedEdge("part-83", "bulletin-29", "covered-by", "north", "notice-r4"),
         SupportedEdge("part-83", "bulletin-91", "covered-by", "south", "private-r3")]
path = evidence_paths(links, "case-47", "bulletin-29", "north",
                      ("uses", "covered-by"))
assert [edge.passage_id for edge in path] == ["case-r2", "notice-r4"]
assert evidence_paths(links, "case-47", "bulletin-91", "north",
                      ("uses", "covered-by")) == ()''',
        "cost": "Building the in-memory adjacency map costs O(E) time and space for E eligible edges. A bounded traversal can still examine up to the degree cap raised to the hop count; keep both limits small and index relation plus tenant in persistent storage. The example returns the first valid path, not the globally best path, and production ranking needs judged evidence quality.",
        "mistakes": ["Treating an extracted relation as fact after its supporting passage was deleted.", "Merging two tenants' same-named entities into one node.", "Allowing a high-degree node to expand without a cap.", "Citing only the final bulletin when the answer depends on two edges."],
        "drill": "Construct 43 questions against a small case-part-bulletin graph. Remove six supporting passages and verify that the affected paths disappear, while paths with independent support remain.",
        "related": [prefix + "multi-hop-evidence-chain-and-stop-rules", prefix + "source-extraction-and-passage-provenance", prefix + "corpus-permissions-and-document-lifecycle", prefix + "claim-level-citation-and-support-checks"],
    },
    {
        "slug": "corrective-retrieval-and-bounded-retry",
        "title": "Corrective retrieval: retry only when evidence is insufficient",
        "summary": "Diagnose a weak retrieval result, choose a specific repair, and stop before retries turn into unsupported answer fishing.",
        "sections": [
            ("Separate absence from weak ranking", "Corrective retrieval is a controlled second search after a first result fails an evidence check. It is not a request to regenerate an answer until one sounds convincing. A missing exact case ID suggests indexing or filter trouble; a correct passage outside the reranker window suggests candidate-window trouble; a passage in context that does not support the claim suggests answer validation trouble. [[retrieval-ai/retrieval-traces-and-incident-debugging|Stage traces]] reveal which repair has a chance to work."),
            ("Define a sufficiency test", "For a question asking whether order OR-47 qualified for a refund on a stated date, require evidence for the order state, applicable policy revision and date condition. A high similarity score alone does not satisfy those slots. Use deterministic checks for exact IDs, active revisions and permission scope; use a judged support check where meaning cannot be reduced to a field match. Record the missing slot and the retrieved passage IDs before another search begins."),
            ("Pick one bounded repair", "If vocabulary differs, run a constrained [[retrieval-ai/query-expansion-guardrails-and-drift-tests|query expansion]]. If the required passage was cut before reranking, enlarge that stage's candidate window within its latency budget. If the corpus lacks the source, ask for clarification or abstain; searching unrelated collections is not a repair. Keep the original constraints on every attempt, including tenant, negation, identifier and date. Maximum attempts should be part of the application contract, not left to a model's willingness to continue."),
            ("Compare attempts against the same target", "Log route, corpus generation, repair reason, new candidate IDs and sufficiency outcome per attempt. A retry counts as useful only if it introduces eligible support that the first attempt lacked. Repeated retrieval of the same passages is an exhaustion signal. If two eligible sources contradict one another, stop and present the conflict with dates; another paraphrase may merely hide it. [[retrieval-ai/evidence-bound-answer-and-abstention|Abstention]] remains an acceptable final result."),
            ("Evaluate repair yield", "Build a set with first-pass successes, fixable vocabulary misses, candidate-window misses, truly missing evidence and contradictions. Measure recovered supported answers, extra retrieval calls, p95 latency and false-answer rate. A policy that retries every request can raise latency with no quality gain. The target is recovery on the fixable slice while keeping no-answer cases unanswered."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class Attempt:
    passage_ids: frozenset[str]
    covered_slots: frozenset[str]
    route: str

def decide_repair(attempts: list[Attempt], required_slots: frozenset[str],
                  max_attempts: int = 2) -> str:
    latest = attempts[-1]
    if required_slots <= latest.covered_slots:
        return "answer with evidence"
    if len(attempts) >= max_attempts:
        return "abstain: budget exhausted"
    if any(latest.passage_ids == prior.passage_ids for prior in attempts[:-1]):
        return "abstain: repeated candidates"
    if latest.route == "literal":
        return "retry with constrained synonyms"
    return "abstain: no justified repair"

needed = frozenset({"order", "policy", "date"})
first = Attempt(frozenset({"order-47-r2"}), frozenset({"order"}), "literal")
second = Attempt(frozenset({"order-47-r2", "policy-83-r4"}), needed, "synonym")
assert decide_repair([first], needed) == "retry with constrained synonyms"
assert decide_repair([first, second], needed) == "answer with evidence"
assert decide_repair([first, first], needed) == "abstain: budget exhausted"''',
        "cost": "The decision function scans prior attempts in O(AK) time in the worst case for A attempts and K passage IDs per attempt; the deliberately small attempt cap keeps that bounded. The real cost is another retrieval and possible rerank call, so track added p95 latency and recovered answers together. Slot coverage must be derived from verified evidence rather than a model's untested self-rating.",
        "mistakes": ["Retrying because the answer sounded uncertain, without identifying a missing evidence slot.", "Dropping an exact identifier or authorization filter in a rewrite.", "Calling a second search successful when it returns the same unsupported passages.", "Continuing after two eligible sources contradict each other."],
        "drill": "Label 55 requests by first-loss stage and whether a repair exists. Allow one corrective attempt; count supported recoveries, unchanged candidates and false answers separately.",
        "related": [prefix + "retrieval-traces-and-incident-debugging", prefix + "query-expansion-guardrails-and-drift-tests", prefix + "retrieval-release-evaluation-and-slice-gates", prefix + "evidence-bound-answer-and-abstention"],
    },
    {
        "slug": "retrieval-evaluation-labels-and-adjudication",
        "title": "Retrieval evaluation labels: build a trustworthy judged set",
        "summary": "Create passage-level judgments with time, permission and disagreement rules so release scores mean the same thing across runs.",
        "sections": [
            ("Define the unit of judgment", "A retrieval test needs a question, corpus snapshot, principal scope, answerable state and one or more supporting passage IDs. Labeling only a final answer string loses the evidence path: two passages may express the same value, but only one may be active for the query date or visible to the principal. Include the exact fact or relation each passage supports. [[retrieval-ai/claim-level-citation-and-support-checks|Claim-level support]] can then be checked without treating a merely related document as a positive hit."),
            ("Collect questions from distinct failures", "Sample real query shapes only where consent and access rules allow it. Add exact-ID requests, paraphrases, two-hop joins, table calculations, time-bounded questions, revoked documents, ambiguous names and no-answer cases. Synthetic queries are useful for rare traps, but they should be reviewed against an actual corpus snapshot. Keep a held-out set that prompt and ranker tuning cannot see. Otherwise the next release may memorize the test's wording instead of improving retrieval."),
            ("Make disagreement visible", "Two reviewers should independently judge a difficult slice. If one marks a passage relevant because it mentions the same topic while the other requires the answer-bearing sentence, the rubric is incomplete. Record both labels and a resolution reason; do not silently average them. A third reviewer can adjudicate disputed examples. Store the rubric version with each label, because changing 'relevant' from topical to supporting changes every reported metric."),
            ("Lock the evaluation context", "A query that was answerable on Monday may be unanswerable after a Tuesday deletion. Freeze or identify the corpus generation, permission policy and query-as-of time for each run. When the source changes, create a new judgment revision instead of overwriting the old one. [[retrieval-ai/freshness-deletion-and-index-swap|Generation swaps]] and [[retrieval-ai/corpus-permissions-and-document-lifecycle|access rules]] are part of the test context, not incidental metadata."),
            ("Report slices with uncertainty", "Measure recall at the candidate window, recall after reranking, citation support and abstention accuracy by question family. A single mean hides a catastrophic permission regression in a small slice. For a tiny slice, show counts along with percentages rather than implying precision the data cannot support. Attach first-loss traces for every regression; that makes adjudication and repair practical instead of a debate over one aggregate score."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class Judgment:
    question_id: str
    corpus_generation: str
    visible_passages: frozenset[str]
    supporting_passages: frozenset[str]
    candidate_passages: tuple[str, ...]

def recall_at_window(judgments: list[Judgment]) -> tuple[int, int]:
    found = eligible = 0
    for judgment in judgments:
        gold = judgment.supporting_passages & judgment.visible_passages
        if not gold:
            continue
        eligible += 1
        found += bool(gold & set(judgment.candidate_passages))
    return found, eligible

cases = [Judgment("q-47", "g-8", frozenset({"policy-r3"}),
                  frozenset({"policy-r3"}), ("policy-r3", "memo-r2")),
         Judgment("q-48", "g-8", frozenset({"memo-r2"}),
                  frozenset({"private-r7"}), ("private-r7",)),
         Judgment("q-49", "g-8", frozenset({"manual-r4"}),
                  frozenset({"manual-r4"}), ("notice-r1",))]
assert recall_at_window(cases) == (1, 2)''',
        "cost": "This simple metric scans each candidate list once, O(C) time for C total candidates, and builds temporary sets up to the window size. Human labeling and adjudication dominate cost. The example excludes questions with no eligible supporting passage; report those separately as no-answer and permission slices rather than burying them in recall.",
        "mistakes": ["Treating a topical passage as if it supported the requested fact.", "Changing the corpus or permission scope while comparing two releases.", "Discarding reviewer disagreement instead of fixing the rubric.", "Reporting only a pooled metric that conceals no-answer or restricted-document failures."],
        "drill": "Label 72 questions in six families, including 12 no-answer cases. Double-label 18 difficult examples and adjudicate disagreements before comparing two retrieval releases on the same corpus generation.",
        "related": [prefix + "retrieval-release-evaluation-and-slice-gates", prefix + "retrieval-traces-and-incident-debugging", prefix + "claim-level-citation-and-support-checks", prefix + "corpus-permissions-and-document-lifecycle"],
    },
    {
        "slug": "federated-retrieval-source-budgets-and-merging",
        "title": "Federated retrieval: search multiple stores without losing policy or time budgets",
        "summary": "Coordinate independent search sources, preserve each source's access checks, and merge evidence without pretending their scores share a scale.",
        "sections": [
            ("Keep source ownership explicit", "Federated retrieval sends a query to more than one store: perhaps a policy index, a ticket database and a table catalog. Each adapter must enforce the caller's authorization under that store's rules, and the coordinator must not infer that permission in one store grants access in another. Return source ID, passage ID, revision, eligibility and match route with every hit. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Corpus access]] belongs at the source boundary as well as the final response boundary."),
            ("Budget each leg", "Give the whole request a deadline and each source a smaller timeout. A slow table catalog should not stall a simple policy answer until the client disconnects. Cancel or ignore work after the deadline, and mark the result as partial. Partial results can support an answer only if all required evidence slots are covered; a missing source may require a clear abstention. The timeout policy should be visible in [[retrieval-ai/retrieval-traces-and-incident-debugging|retrieval traces]] so a missing document is not mistaken for a ranking failure."),
            ("Merge identities, not raw scores", "A cosine score of 0.79 and a lexical score of 11.4 are not comparable magnitudes. Deduplicate by stable source-and-passage identity, then use per-source rank, calibrated relevance or a judged fusion rule. Record which source returned each duplicate and why a candidate survived. [[retrieval-ai/hybrid-search-and-reciprocal-rank-fusion|Rank fusion]] offers a baseline when adapters expose rankings but not aligned probabilities. Keep source diversity when the answer needs both a ticket and a policy."),
            ("Handle source-specific freshness", "One source may have a fresh transaction row while another holds yesterday's indexed document. Store source revision and observed-at time on every hit; do not present their join as a single current snapshot unless the application defines consistency semantics. For a question about historical eligibility, apply the requested as-of time to each adapter. If one store cannot answer as-of queries, say which part is unavailable rather than silently reading its current state."),
            ("Test partial and contradictory outcomes", "Run evaluations where every source succeeds, one times out, a source returns forbidden hits, two stores disagree on a revision, and one store returns an exact ID absent elsewhere. Measure required-evidence coverage, p95 latency and per-source failure rates. A high overall recall score does not excuse a coordinator that leaks a restricted hit or hides a missing source behind a confident answer."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class SearchHit:
    source: str
    passage_id: str
    tenant: str
    rank: int
    text: str

def merge_hits(source_hits: dict[str, list[SearchHit]], tenant: str,
               per_source_cap: int = 3) -> list[SearchHit]:
    eligible = []
    for source, hits in source_hits.items():
        ranked = sorted((hit for hit in hits if hit.source == source
                         and hit.tenant == tenant), key=lambda hit: hit.rank)
        eligible.extend(ranked[:per_source_cap])
    seen: set[tuple[str, str]] = set()
    merged = []
    for hit in sorted(eligible, key=lambda item: (item.rank, item.source)):
        identity = (hit.source, hit.passage_id)
        if identity not in seen:
            seen.add(identity)
            merged.append(hit)
    return merged

results = {"policy": [SearchHit("policy", "refund-r4", "north", 1, "47 days"),
                      SearchHit("policy", "refund-r4", "north", 2, "duplicate")],
           "tickets": [SearchHit("tickets", "case-83", "south", 1, "private"),
                       SearchHit("tickets", "case-47", "north", 2, "eligible")]}
assert [(hit.source, hit.passage_id) for hit in merge_hits(results, "north")] == [
    ("policy", "refund-r4"), ("tickets", "case-47")]
assert all(hit.tenant == "north" for hit in merge_hits(results, "north"))''',
        "cost": "For N returned hits, filtering and sorting costs O(N log N) time and O(N) space. Concurrent source calls can lower wall time toward the slowest successful leg, but only with explicit deadlines and a shared request budget. This example does not execute network calls or enforce source authorization; production adapters must perform their own checks before returning candidates.",
        "mistakes": ["Sorting raw scores from unrelated retrieval engines as if they were calibrated.", "Letting a single slow adapter consume the entire request deadline.", "Assuming an aggregator-side filter replaces authorization in each source.", "Answering as though all stores were current when their revisions differ."],
        "drill": "Federate three mocked stores over 38 judged questions. Inject timeouts, duplicate hits, stale revisions and cross-tenant decoys; count partial results and unsupported final answers independently.",
        "related": [prefix + "hybrid-search-and-reciprocal-rank-fusion", prefix + "permission-aware-cache-and-conversation-turns", prefix + "retrieval-traces-and-incident-debugging", prefix + "retrieval-evaluation-labels-and-adjudication"],
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
        "featured": False, "sort_order": 8433 + offset, "status": "published",
        "published_at": stamp, "created_at": stamp, "updated_at": stamp,
        "data": {"subject_root": hub_path, "section_path": hub_path,
                 "content_format": "html", "seo_ready": True, "kind": "tutorial",
                 "reading_minutes": max(6, round(len(re.sub('<[^>]+>', ' ', body).split()) / 180)),
                 "author_path": "authors/aitrove-editorial",
                 "verification_suite": "Executable standard-library example and editorial review",
                 "related": [{"path": target, "title": titles[target]} for target in item["related"]]},
    }
    rows.append(row)
    by_path[path] = row
    changed.append(row)

for path in (hub_path, "retrieval-ai"):
    row = by_path[path]
    row["data"]["modules"].append({"title": "Graph, correction and evaluation", "lessons": new_paths})
    row["body"] += '<h2>Graph, correction and evaluation</h2><ul>' + ''.join(
        f'<li>{link(target)}</li>' for target in new_paths) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "multi-hop-evidence-chain-and-stop-rules": [new_paths[0]],
    prefix + "retrieval-traces-and-incident-debugging": [new_paths[1], new_paths[2]],
    prefix + "retrieval-release-evaluation-and-slice-gates": [new_paths[2]],
    prefix + "hybrid-search-and-reciprocal-rank-fusion": [new_paths[3]],
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
