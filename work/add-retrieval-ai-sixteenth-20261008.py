"""Add retrieval lessons on diversity, wildcard budgets, and rank metrics."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-retrieval-ai-sixteenth-import-20261008.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "retrieval-ai/"
hub_path = prefix + "retrieval-ai-tutorial"

lessons = [
    {
        "slug": "maximal-marginal-relevance-diversity-and-support-tradeoffs",
        "title": "Maximal marginal relevance: diversify retrieval without losing support",
        "summary": "Select a relevant but less repetitive evidence set, calibrate the novelty penalty and preserve essential corroborating passages.",
        "sections": [
            ("MMR is a second-stage selection rule", "Maximal marginal relevance chooses one result at a time from an already retrieved candidate set. It balances query relevance against similarity to material already selected. With relevance weight lambda, a common form is lambda times query relevance minus one minus lambda times the maximum similarity to any selected result. A high lambda favors the original ranking; a lower one rewards novelty. This does not find passages absent from the candidate pool. If [[retrieval-ai/retrieval-recall-and-reranking|candidate recall]] is weak, tune the first-stage search before applying diversity. Run authorization and deletion filters before this selection rule."),
            ("The two scores need compatible meaning", "A BM25 score can span a different scale from cosine similarity or token overlap. Plugging raw values into the formula makes lambda meaningless. Convert query relevance and passage-passage similarity to stable ranges using judged data, and record the score versions. The example uses bounded relevance values and Jaccard token overlap solely to make the behavior inspectable. A production selector may use embedding similarity, lexical overlap, lineage or a combination. [[retrieval-ai/score-normalization-and-fusion-calibration|Fusion calibration]] explains why numeric scale is a policy, not a label. One duplicate detector should not accidentally penalize unrelated facts that use the same technical vocabulary."),
            ("Diversity is not the same as independent evidence", "Two passages from different documents can repeat one syndicated announcement. Conversely, two passages in one manual can provide distinct facts needed to answer a multi-part question. MMR's similarity penalty is a ranking signal, not proof of source independence. Preserve document revision, lineage and passage identity in the selected packet. [[retrieval-ai/near-duplicate-evidence-and-independent-support|Independent-support checks]] decide whether sources truly corroborate a claim. [[retrieval-ai/retrieval-result-collapse-document-grouping-and-candidate-depth|Document grouping]] is a presentation rule; it should not silently discard a second passage required for an answer."),
            ("Choose the evidence budget deliberately", "The first selected item normally has no novelty penalty. Later selections can trade a small relevance drop for a new angle, but an aggressive penalty may push a weak or unrelated passage into a short context window. Reserve slots for mandatory exact matches and explicitly requested sources before running diversity over the remaining eligible pool. Keep conflicting evidence visible when the user asks for comparison or when active sources disagree. [[retrieval-ai/retrieved-claim-conflicts-authority-and-abstention|Claim-conflict handling]] must see the competing claims rather than receive a falsely tidy packet. Inspect the final ordered context, not merely the selection scores."),
            ("Evaluate both variety and answer support", "Measure unique-parent count, near-duplicate rate and intent coverage at a fixed K, then check whether answer-bearing spans and contradictions survived. A higher diversity number can coexist with lower supported-answer rate. Compare several lambda values under the same first-stage pool and token budget. Log the relevance and novelty component for each chosen passage so a missing citation can be diagnosed. [[retrieval-ai/context-packing-and-evidence-diversity|Context packing]] then assigns actual token slots and may reject a selected item that is too large. MMR improves candidate mix only when the final evidence remains sufficient."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class Passage:
    passage_id: str
    relevance: float
    terms: frozenset[str]
    permitted: bool

def overlap(left: Passage, right: Passage) -> float:
    union = left.terms | right.terms
    return len(left.terms & right.terms) / len(union) if union else 0.0

def select_mmr(candidates: list[Passage], limit: int,
               relevance_weight: float) -> list[Passage]:
    if limit < 0 or not 0 <= relevance_weight <= 1:
        raise ValueError("invalid selection settings")
    remaining = [item for item in candidates if item.permitted]
    if any(not 0 <= item.relevance <= 1 for item in remaining):
        raise ValueError("relevance must be normalized")
    chosen = []
    while remaining and len(chosen) < limit:
        winner = max(remaining, key=lambda item: (
            relevance_weight * item.relevance
            - (1 - relevance_weight) * max(
                (overlap(item, prior) for prior in chosen), default=0.0),
            item.passage_id))
        chosen.append(winner)
        remaining.remove(winner)
    return chosen

hits = [Passage("seal-v3-a", .92, frozenset({"seal", "pressure"}), True),
        Passage("seal-v3-b", .89, frozenset({"seal", "pressure"}), True),
        Passage("pump-81", .78, frozenset({"pump", "inspection"}), True),
        Passage("private-note", .99, frozenset({"seal"}), False)]
assert [hit.passage_id for hit in select_mmr(hits, 2, .6)] == [
    "seal-v3-a", "pump-81"]''',
        "cost": "For N candidates and K selected passages, this direct implementation compares each remaining candidate with every selected item on every round. If token-set comparison costs L, time is O(K squared times N times L) in the worst case and the remaining/chosen lists use O(N + K) space beyond stored terms. Incrementally storing each candidate's maximum similarity to chosen items can reduce repeated work to O(KNL) and O(N) extra state. Pairwise precomputation costs O(N squared times L) time and memory. Keep N bounded, because diversity selection is a reranking step, not a replacement for first-stage retrieval.",
        "mistakes": ["Applying MMR before permission filtering and allowing a private passage to influence public ranking.", "Combining unscaled BM25 and bounded similarity values as if lambda had a stable interpretation.", "Treating a novel result as independent corroboration without checking lineage.", "Optimizing unique-source count while dropping the only passage that supports a required claim."],
        "drill": "For 61 multi-aspect queries, compare three relevance weights at the same top-30 candidate pool and six-passage context budget. Record unique source lineages, supported-answer rate, omitted contradictions and p95 selection time.",
        "related": [prefix + "context-packing-and-evidence-diversity", prefix + "near-duplicate-evidence-and-independent-support", prefix + "retrieval-result-collapse-document-grouping-and-candidate-depth", prefix + "retrieved-claim-conflicts-authority-and-abstention"],
    },
    {
        "slug": "wildcard-prefix-expansion-budgets-and-literal-identifier-safety",
        "title": "Wildcard retrieval: bound prefix expansion and keep identifiers literal",
        "summary": "Control term-dictionary fanout, reject broad patterns and keep expansion behind the same access and query-parsing boundaries as ordinary search.",
        "sections": [
            ("A wildcard expands a query into terms", "A trailing prefix pattern asks a search engine to find indexed terms that start with a given sequence, then search their postings. An infix or leading wildcard can require examining far more of the term dictionary. This differs from [[retrieval-ai/retrieval-autocomplete-suggestions-and-privacy|autocomplete]], which suggests text to a user while typing; a wildcard query actually broadens the candidate set used for ranking or answering. A short pattern can match thousands of terms, creating a large Boolean expansion, latency spike or relevance drift. Treat the expansion as a bounded query-planning operation, not a harmless character in a string."),
            ("Do not run user syntax through an unrestricted parser", "Accept an explicit, small pattern language rather than letting raw user text become a backend regular expression or query-string program. A conservative interface might allow one trailing star after at least three letters and reject leading stars, multiple wildcards, punctuation and overlong tokens. Escape or reject reserved syntax at the trust boundary. [[retrieval-ai/safe-search-query-parsing-and-literal-identifiers|Safe query parsing]] keeps the user's literal request separate from search operators. For part numbers, route to an exact field unless the product has a documented prefix-search mode; a broad expansion of one digit can bring back a different device."),
            ("Expand only within the allowed vocabulary", "An approved term dictionary must reflect tenant scope, published status and current deletion state. Generating a broad global list and filtering retrieved documents later can leak private vocabulary through expansion counts, logs or timing. Apply mandatory filters in the actual search backend as well; an authorized suggestion list alone does not authorize documents. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Corpus lifecycle]] supplies the current eligibility rule. If the expansion limit is exceeded, return a clear request to narrow the prefix instead of silently taking the first few terms, which produces unstable and incomplete results."),
            ("Budget clauses and postings together", "A limit on expanded term count is useful but not sufficient. Ten common expansions can touch more postings than a hundred rare ones. Set a query deadline, clause or automaton complexity cap, and maximum candidate work. Prefix indexes or specialized n-gram fields can reduce lookup cost, but they consume storage and may broaden matching semantics. Record expansion count, estimated postings, execution time and cancellation outcome. [[retrieval-ai/retrieval-deadline-budgets-cancellation-and-partial-result-policy|Deadline budgeting]] must include term expansion, not just document ranking. A timeout should not be disguised as an empty answer."),
            ("Judge recovery against accidental matches", "Create tests for incomplete product names, valid rare codes, short prefixes and patterns containing punctuation. Compare recovered relevant documents with false positives and backend cost. A wildcard branch can complement [[retrieval-ai/retrieval-spelling-correction-and-identifier-preservation|spelling correction]] for exploratory search, but it does not prove that a user intended any particular expanded term. Show the interpreted query when it materially changes results. If the branch feeds an answer, keep the actual matched source span and do not imply that a wildcard match itself supports a factual claim."),
        ],
        "code": '''import re

def expand_prefix(prefix: str, approved_terms: set[str],
                  max_terms: int) -> list[str]:
    if max_terms < 1:
        raise ValueError("positive expansion cap required")
    if not re.fullmatch(r"[a-z]{3,24}", prefix):
        raise ValueError("only bounded lowercase prefixes are supported")
    expanded = sorted(term for term in approved_terms
                      if term.startswith(prefix))
    if len(expanded) > max_terms:
        raise OverflowError("narrow the prefix before searching")
    return expanded

visible_vocabulary = {"sealing", "seal", "sealed", "sensor", "private-seal"}
assert expand_prefix("sea", visible_vocabulary, 3) == [
    "seal", "sealed", "sealing"]
try:
    expand_prefix("s", visible_vocabulary, 3)
except ValueError:
    pass
else:
    raise AssertionError("short prefixes must be rejected")
try:
    expand_prefix("sea", visible_vocabulary, 2)
except OverflowError:
    pass
else:
    raise AssertionError("over-budget expansion must fail")''',
        "cost": "This standard-library demonstration scans V approved vocabulary terms in O(VP) worst-case prefix-comparison work for prefix length P, sorts M matches in O(M log M), and uses O(M) output space. A production ordered term dictionary can seek to a prefix and enumerate matching terms closer to O(log V + M) plus postings work. The toy approved set is already scoped; it does not implement access control or actual document search. A backend must enforce the same authorization at retrieval time and cap work beyond the term dictionary. Rejecting an over-budget expansion is safer than silently truncating its terms.",
        "mistakes": ["Allowing a leading wildcard or unrestricted regular expression over a large text index.", "Truncating expansions to a few alphabetically first terms and presenting the results as complete.", "Expanding from a global vocabulary before applying tenant and deletion rules.", "Treating a serial-number prefix match as an exact device identity."],
        "drill": "Replay 73 prefixes from real search tasks, including two-character strings, rare serials and terms with punctuation. Record expansion count, postings scanned, p95 latency and useful-result rate. Require explicit rejection for patterns above the agreed cost ceiling.",
        "related": [prefix + "safe-search-query-parsing-and-literal-identifiers", prefix + "retrieval-autocomplete-suggestions-and-privacy", prefix + "retrieval-spelling-correction-and-identifier-preservation", prefix + "retrieval-deadline-budgets-cancellation-and-partial-result-policy"],
    },
    {
        "slug": "retrieval-recall-mrr-ndcg-and-unjudged-results",
        "title": "Retrieval metrics: read Recall, MRR and nDCG without hiding misses",
        "summary": "Choose metrics that match the product task, state the judgment set and treat unjudged results as unknown rather than wrong.",
        "sections": [
            ("Metrics answer different questions", "Recall at K asks what fraction of all known relevant evidence appears in the first K results. It matters when a downstream reranker or answer generator needs enough candidates to work with. Reciprocal rank asks how early the first relevant item appears; mean reciprocal rank averages that value across queries. It is useful for a task where one good hit suffices, but it ignores a second missing support passage. Normalized discounted cumulative gain uses graded relevance and discounts lower ranks, so it can distinguish a direct answer from a merely related source. [[retrieval-ai/retrieval-vs-answer-evaluation|Answer evaluation]] remains separate: a good list does not prove a supported answer."),
            ("Define the judged universe and K", "A recall denominator needs the known relevant set for each query. If judgments were pooled only from one old search system, a new system can retrieve an unjudged but valid document; scoring that as irrelevant creates bias. Record document or passage identity, corpus generation, permissions, as-of time and judgment policy. [[retrieval-ai/retrieval-evaluation-labels-and-adjudication|Label adjudication]] establishes those facts. Report the cutoff explicitly: Recall at 20 is not interchangeable with Recall at 5. A query with no relevant evidence needs a separate no-answer evaluation policy rather than a forced zero denominator."),
            ("MRR can reward the wrong release", "Suppose the first result is somewhat relevant, while the only passage supporting a required number is missing. MRR can still be one because it cares only about the first relevant rank under a binary label. If a task requires multiple facts or independent sources, also report answer-span coverage, multi-hop completion or recall of required evidence units. [[retrieval-ai/multi-hop-evidence-chain-and-stop-rules|Multi-hop retrieval]] makes that dependency explicit. Keep a miss ledger with query slices so an average improvement cannot hide a collapse on rare identifiers or filtered tenants."),
            ("nDCG depends on the grade definition", "A graded label might use zero for unrelated, one for contextual, two for partially useful and three for a directly supporting passage. Discounted cumulative gain then rewards high grades near the top; dividing by the ideal possible gain makes scores comparable within the same judged query. But grade policies, gain formula and cutoff must stay fixed across releases. Unjudged results should be reviewed or reported as unknown, not silently mapped to grade zero. [[retrieval-ai/near-duplicate-evidence-and-independent-support|Copied evidence]] may require a separate diversity or lineage measure: nDCG does not automatically penalize repeating the same source."),
            ("Use release slices and uncertainty", "Calculate query-level metrics first, then aggregate by intent, language, corpus age and permission slice. Keep the exact same queries and judgments for a paired comparison, and inspect differences rather than trusting a single global mean. Bootstrap intervals or paired randomization can help separate noise from a real improvement when enough independent queries exist. Do not repeatedly tune on a fixed held-out set until it becomes development data. [[retrieval-ai/retrieval-release-evaluation-and-slice-gates|Release gates]] should specify minimum recall and answer support for protected slices, while an online test monitors latency and user behavior separately."),
        ],
        "code": '''from math import log2

def retrieval_scores(grades: dict[str, int],
                     ranked_ids: list[str], cutoff: int
                     ) -> tuple[float, float, float] | None:
    if cutoff < 1:
        raise ValueError("invalid cutoff")
    window = ranked_ids[:cutoff]
    if len(set(window)) != len(window):
        raise ValueError("repeated result in scored window")
    if any(document_id not in grades for document_id in window):
        raise ValueError("unjudged result in scored window")
    if any(grade < 0 for grade in grades.values()):
        raise ValueError("negative relevance grade")
    relevant = {document_id for document_id, grade in grades.items()
                if grade > 0}
    if not relevant:
        return None  # evaluate no-answer behavior separately
    recall = len(set(window) & relevant) / len(relevant)
    first_rank = next((rank for rank, document_id in
                       enumerate(window, 1) if document_id in relevant), None)
    reciprocal_rank = 1 / first_rank if first_rank else 0.0
    def gain(values: list[int]) -> float:
        return sum((2 ** grade - 1) / log2(rank + 1)
                   for rank, grade in enumerate(values, 1))
    observed = gain([grades[document_id] for document_id in window])
    ideal = gain(sorted(grades.values(), reverse=True)[:cutoff])
    return recall, reciprocal_rank, observed / ideal if ideal else 0.0

grades = {"manual-47": 3, "manual-81": 1, "manual-94": 0}
recall, mrr, ndcg = retrieval_scores(
    grades, ["manual-81", "manual-94", "manual-47"], 2)
assert recall == .5 and mrr == 1.0 and 0 < ndcg < 1''',
        "cost": "For J judged documents and K displayed results, this direct calculation uses O(J log J + K) time because it sorts all judged grades for ideal nDCG and checks the ranked window; its extra space is O(J + K). For many queries, cache each query's ideal gain under an immutable judgment set. Judgment collection and adjudication cost much more than arithmetic. The code rejects unjudged top-K results instead of falsely assigning them zero, but a real evaluation pipeline can queue those results for judging and report the unknown rate. The returned tuple is query-level; macro averages must account for no-answer queries explicitly.",
        "mistakes": ["Reporting Recall at K without stating whether the known relevant set is complete.", "Calling MRR an evidence-coverage metric when only the first relevant hit affects it.", "Treating unjudged new results as irrelevant in an incomplete judgment pool.", "Comparing nDCG values across changed grade scales, corpus generations or cutoffs."],
        "drill": "Score 91 judged questions at K equal to 5 and 20. Report recall, reciprocal rank and graded nDCG per slice, plus the count of unjudged top-K results. Audit ten queries where the metrics disagree and record whether the generated answer has enough support.",
        "related": [prefix + "retrieval-vs-answer-evaluation", prefix + "retrieval-evaluation-labels-and-adjudication", prefix + "retrieval-release-evaluation-and-slice-gates", prefix + "multi-hop-evidence-chain-and-stop-rules"],
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
        "featured": False, "sort_order": 8484 + offset, "status": "published",
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
    row["data"]["modules"].append({"title": "Diversity, wildcard search and ranking metrics", "lessons": new_paths})
    row["body"] += '<h2>Diversity, wildcard search and ranking metrics</h2><ul>' + ''.join(
        f'<li>{link(target)}</li>' for target in new_paths) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "context-packing-and-evidence-diversity": [new_paths[0]],
    prefix + "safe-search-query-parsing-and-literal-identifiers": [new_paths[1]],
    prefix + "retrieval-vs-answer-evaluation": [new_paths[2]],
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
