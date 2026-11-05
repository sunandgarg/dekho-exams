"""Add four original retrieval lessons and link them into the existing course."""
import ast
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-retrieval-ai-fifth-import-20261007.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "retrieval-ai/"
hub_path = prefix + "retrieval-ai-tutorial"

lessons = [
    {
        "slug": "multilingual-retrieval-and-entity-preservation",
        "title": "Multilingual retrieval without losing names, units or permissions",
        "summary": "Search across languages while preserving exact entities and measuring answer support in the language of the source.",
        "sections": [
            ("Treat language as a retrieval constraint", "Multilingual retrieval finds evidence when the question and the answer-bearing document use different languages or scripts. A Hindi request for a pump's pressure limit might need an English maintenance sheet. Translate or encode the request for candidate generation, but retain the original request and its entity spans. A translated product name can become a common noun; a model number or unit can be silently changed. Keep the original tokens beside any expansion so the exact identifier remains searchable. [[retrieval-ai/query-expansion-guardrails-and-drift-tests|Expansion tests]] should fail when an alias changes the requested entity."),
            ("Use two candidate paths", "A multilingual vector index can find semantically related passages across languages; an exact or transliterated term index can recover names and part numbers that an embedding misses. Merge bounded candidate lists, then rank the original passages. Transliteration is a controlled alias for a named entity, not a general translation engine. Store aliases with locale, entity ID and review status. If two entities share the same Roman spelling, an alias must not erase that ambiguity. [[retrieval-ai/hybrid-search-and-reciprocal-rank-fusion|Hybrid merging]] gives a practical way to combine the two paths without pretending their raw scores are comparable."),
            ("Preserve the source's meaning", "Retrieve source text, revision, locale and passage ID together. A translated display excerpt may help the reader, but the citation must still point to the original passage. Numbers, negation, effective dates and units require explicit checks across the translation boundary. Do not answer a question in the user's language from a passage whose translation has inverted 'must not' or converted 47 psi into 47 kPa. [[retrieval-ai/claim-level-citation-and-support-checks|Claim-level support]] is judged against the source, not against a fluent paraphrase."),
            ("Filter before mixing languages", "Tenant permissions, document status and jurisdiction apply to every language variant. A public English summary is not evidence that a private Spanish appendix can be searched or surfaced. Deduplicate translations by source lineage only after access filtering; separate independently authored statements even if they are translated similarly. Track source revision across language copies because a translated page may lag behind the original. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Corpus lifecycle]] determines which variant is eligible."),
            ("Evaluate language pairs, not one average", "Build judged queries for each query-language and document-language pair, including mixed-script queries, transliterated names, similar identifiers and documents with no valid answer. Report candidate recall, supported answer rate and entity preservation per pair. A strong English-English score can hide total failure on Hindi-English or Arabic-English searches. Review wrong answers with both original and translated passages. If no reviewer can establish the meaning of the source, mark support unknown rather than accepting the answer by fluency."),
        ],
        "code": '''from dataclasses import dataclass
import unicodedata

@dataclass(frozen=True)
class ServicePassage:
    passage_id: str
    tenant: str
    locale: str
    text: str
    entity_id: str

def normalized(text: str) -> str:
    return unicodedata.normalize("NFKC", text).casefold()

def exact_entity_candidates(passages: list[ServicePassage], tenant: str,
                            requested_entity: str, aliases: dict[str, str]) -> list[str]:
    entity_id = aliases.get(normalized(requested_entity))
    if entity_id is None:
        return []
    return [passage.passage_id for passage in passages
            if passage.tenant == tenant and passage.entity_id == entity_id]

service_notes = [ServicePassage("sheet-en-r4", "north", "en",
                                "Pump P-47 relief limit is 83 kPa.", "pump-p47"),
                 ServicePassage("sheet-hi-r2", "south", "hi",
                                "P-47 limit is 99 kPa.", "pump-p47")]
reviewed_aliases = {normalized("पी-47"): "pump-p47", normalized("P-47"): "pump-p47"}
assert exact_entity_candidates(service_notes, "north", "पी-47", reviewed_aliases) == ["sheet-en-r4"]
assert exact_entity_candidates(service_notes, "north", "P-48", reviewed_aliases) == []''',
        "cost": "The transparent candidate scan costs O(N) time over N passages and O(K) output space for K eligible matches. A production entity index keyed by tenant and entity ID reduces lookup work but requires reviewed aliases and refreshes when documents change. A second multilingual vector path adds index storage and query latency; measure its incremental supported recall by language pair before accepting the cost.",
        "mistakes": ["Treating transliteration as an unambiguous entity identifier.", "Dropping the original query after translation and losing exact numbers or negation.", "Citing only a generated translation rather than the source passage.", "Reporting one aggregate recall score across uneven language pairs."],
        "drill": "Build 53 questions across three query languages and two document languages. Include twelve mixed-script identifiers and eight restricted passages. Record entity preservation, authorized candidate recall and supported answers for every language pair.",
        "related": [prefix + "query-expansion-guardrails-and-drift-tests", prefix + "hybrid-search-and-reciprocal-rank-fusion", prefix + "claim-level-citation-and-support-checks", prefix + "corpus-permissions-and-document-lifecycle"],
    },
    {
        "slug": "code-repository-retrieval-by-symbol-and-revision",
        "title": "Code repository retrieval by symbol, call site and commit",
        "summary": "Find implementation evidence in a changing repository without confusing symbol matches, generated files and stale revisions.",
        "sections": [
            ("Index code as code", "Code repository retrieval searches declarations, call sites, configuration and tests as related but distinct evidence. A question about how InvoiceLedger.post records a refund needs the method body and perhaps its caller; a README mentioning the same method is insufficient. Parse source into language-aware symbols with file path, line span and commit ID. Preserve surrounding imports and enclosing class for interpretation. [[retrieval-ai/chunk-identity-and-context-boundaries|Stable chunk identity]] helps trace a symbol across index rebuilds, but a changed body must receive a new revision identity."),
            ("Use the repository graph carefully", "Exact symbol search should usually run before semantic search for named functions, exception types or environment keys. Then collect bounded callers, callees and tests to explain behavior. A call graph is only an approximation in languages with reflection, runtime dispatch, generated code or dependency injection. Do not claim a path is unreachable because a static extractor missed it. [[retrieval-ai/knowledge-graph-retrieval-and-edge-provenance|Edge provenance]] should identify whether an edge came from parsing, a build artifact or a test trace."),
            ("Bind every result to a revision", "Branch names move. A result retrieved from main yesterday may contradict today's implementation. Store commit, file hash and language in the index; include the commit in the answer trace. For a question about a deployment, use the deployed commit rather than the latest default branch. For a historical bug, retrieve the failing revision and a candidate fix separately. [[retrieval-ai/temporal-retrieval-as-of-validity-and-conflicts|Temporal evidence]] is particularly important when a config flag changed between releases."),
            ("Respect boundaries and noise", "Filter repositories and paths by permission before presenting symbol names or snippets. Skip vendored libraries, generated files and copied lockfile text unless the question specifically concerns them. Merge duplicate definitions only when lineage and revision match. Keep tests accessible as evidence of intended behavior, but do not treat a passing test as proof that every production call follows the same path. [[retrieval-ai/near-duplicate-evidence-and-independent-support|Duplicate handling]] should not collapse a test and implementation into one source."),
            ("Judge answer-bearing spans", "Create questions about exact symbols, renamed methods, inherited calls, generated bindings, stale commits and behavior described only by a caller. Measure whether the correct file and line span entered the candidate set, whether the required call path was retrieved, and whether the final explanation cited the right revision. A high lexical hit on a symbol name is not a supported answer if its body never entered context. Keep line links pinned to commit hashes so they remain valid after later edits."),
        ],
        "code": '''import ast
from dataclasses import dataclass

@dataclass(frozen=True)
class CodeSymbol:
    name: str
    path: str
    commit: str
    first_line: int
    last_line: int

def python_symbols(source: str, path: str, commit: str) -> list[CodeSymbol]:
    tree = ast.parse(source, filename=path)
    symbols: list[CodeSymbol] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(CodeSymbol(node.name, path, commit, node.lineno, node.end_lineno))
        elif isinstance(node, ast.ClassDef):
            for method in node.body:
                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols.append(CodeSymbol(f"{node.name}.{method.name}", path,
                                              commit, method.lineno, method.end_lineno))
    return symbols

ledger_source = "class InvoiceLedger:\\n    def post_refund(self, amount):\\n        return -amount\\n"
found = python_symbols(ledger_source, "billing/ledger.py", "c47e2a")
assert found == [CodeSymbol("InvoiceLedger.post_refund", "billing/ledger.py", "c47e2a", 2, 3)]''',
        "cost": "AST extraction visits O(S) syntax nodes and stores O(M) symbols for M declarations. An exact symbol index is cheap to query but misses indirect behavior; graph expansion can grow rapidly with call depth, so cap neighbors and inspect the highest-value paths first. Parsing each changed file once per commit is cheaper than rescanning the full repository on every question.",
        "mistakes": ["Answering from a README when the question asks what code actually executes.", "Mixing snippets from different commits in one behavior claim.", "Assuming a static call graph captures reflective or injected calls.", "Indexing vendored and generated code as if it were the repository's own implementation."],
        "drill": "Index 47 source files at two commits. Judge 41 questions about named methods, indirect callers and renamed symbols; report correct commit, symbol span and supported call-path coverage separately.",
        "related": [prefix + "chunk-identity-and-context-boundaries", prefix + "knowledge-graph-retrieval-and-edge-provenance", prefix + "temporal-retrieval-as-of-validity-and-conflicts", prefix + "source-extraction-and-passage-provenance"],
    },
    {
        "slug": "audio-video-retrieval-with-timecoded-evidence",
        "title": "Audio and video retrieval with timecoded evidence",
        "summary": "Retrieve a precise spoken or visual moment while retaining timestamps, speakers and media-version identity.",
        "sections": [
            ("Make time part of the passage ID", "Audio and video retrieval uses timed segments, transcript words and sometimes frame descriptions as searchable evidence. A transcript paragraph without a start and end time cannot support a jump to the original recording. Store media asset ID, version, track, speaker label, start and end milliseconds on every segment. Re-captioning or editing the recording changes the time map; keep the old version rather than silently reusing stale links. [[retrieval-ai/multimodal-retrieval-and-asset-identity|Asset identity]] must survive storage moves but change when the underlying cut changes."),
            ("Separate modalities in candidate generation", "Transcript search works for spoken terms; frame descriptions or image embeddings may find a visual action with no spoken mention. Run each path within a budget, then combine candidates using calibrated ranks and overlap rules. A camera view of a valve does not prove that the narrator's pressure number belongs to that valve. Preserve which modality supplied each clue. [[retrieval-ai/federated-retrieval-source-budgets-and-merging|Federated budgets]] prevent one long transcript from consuming every result slot."),
            ("Account for timing errors", "Automatic speech recognition can mishear part numbers, names and negation. Speaker diarization can swap labels after cross-talk. Store word-level confidence or review status where available, and include a small playback margin around candidate spans. Avoid letting margins turn a thirty-second citation into an unrelated ten-minute clip. When the spoken answer is uncertain, retrieve nearby segments or abstain rather than silently repairing the transcript. [[retrieval-ai/evidence-bound-answer-and-abstention|Abstention]] should remain available after a high ranking score."),
            ("Check the answer at playback time", "A timestamp is a pointer, not proof. The final claim should be checked against the media span and any displayed text within it. For a question about who approved a release, both speaker attribution and the words of approval matter. If the text says 'not approved', a frame showing a green button cannot reverse it. Keep transcript and frame citations separate when both are needed. [[retrieval-ai/claim-level-citation-and-support-checks|Support checks]] must inspect the exact moment behind each claim."),
            ("Evaluate with time tolerance", "Judge answer-bearing intervals, not just media IDs. Measure whether the right asset entered the candidate set, whether an overlapping interval appeared in the top window, and whether the final answer cited a span narrow enough to inspect. Include edits, repeated phrases, noisy speech, overlapping speakers and purely visual evidence. Report timing error and missing-evidence abstention separately. A result that finds the correct meeting but points nine minutes late should fail the timestamp test."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class MediaSegment:
    asset_id: str
    version: str
    start_ms: int
    end_ms: int
    speaker: str
    transcript: str

def timed_matches(segments: list[MediaSegment], asset_id: str,
                  version: str, phrase: str) -> list[tuple[int, int, str]]:
    matches = []
    for segment in segments:
        if segment.start_ms < 0 or segment.end_ms <= segment.start_ms:
            raise ValueError("invalid media interval")
        if segment.asset_id == asset_id and segment.version == version \\
                and phrase.casefold() in segment.transcript.casefold():
            matches.append((segment.start_ms, segment.end_ms, segment.speaker))
    return matches

meeting = [MediaSegment("release-briefing", "cut-3", 83000, 97000,
                        "release-lead", "The patch remains blocked."),
           MediaSegment("release-briefing", "cut-2", 79000, 93000,
                        "release-lead", "The patch is approved.")]
assert timed_matches(meeting, "release-briefing", "cut-3", "blocked") == [
    (83000, 97000, "release-lead")]
assert timed_matches(meeting, "release-briefing", "cut-3", "approved") == []''',
        "cost": "The baseline scans S segments in O(S) time and stores O(K) matches. A transcript term index narrows spoken candidates; visual embeddings add frame-sampling, index storage and ranking costs. Higher sampling density improves access to brief events but increases storage and search work. Evaluate timestamp recall against that cost, rather than indexing every frame by default.",
        "mistakes": ["Returning a meeting title without a timecoded supporting span.", "Mixing transcript timestamps from one cut with video from another.", "Treating noisy automatic captions as verified words.", "Using a visual match to assert a speaker's words without checking the audio."],
        "drill": "Judge 39 questions over six edited recordings. Include repeated phrases, overlapping speakers and silent visual events; measure asset recall, interval overlap, speaker accuracy and cited-span width.",
        "related": [prefix + "multimodal-retrieval-and-asset-identity", prefix + "source-extraction-and-passage-provenance", prefix + "claim-level-citation-and-support-checks", prefix + "federated-retrieval-source-budgets-and-merging"],
    },
    {
        "slug": "hard-negative-mining-and-false-negative-audits",
        "title": "Hard-negative mining without training against true answers",
        "summary": "Choose informative retrieval distractors while auditing labels, lineage and split leakage before model training.",
        "sections": [
            ("Define the negative precisely", "A hard negative is a passage that resembles a relevant answer but does not satisfy the query. For a request for pump P-47's current relief limit, an old revision or P-48's limit may be informative distractors. A second valid P-47 passage is a false negative even if the judgment file omitted it. Before mining, specify query intent, time boundary, tenant and what counts as support. [[retrieval-ai/retrieval-evaluation-labels-and-adjudication|Judgment labels]] should allow multiple positives and an uncertain state; a missing label is not proof of irrelevance."),
            ("Mine from several candidate pools", "Lexical search yields near-word matches; dense retrieval yields semantic neighbors; a reranker can find subtle confusions. Sample within authorized, training-eligible corpora and record which model and index version produced each candidate. Balance easy and hard distractors so training does not only distinguish almost-identical policies. A candidate that is too hard may actually be another answer, especially when multiple documents repeat the same fact. [[retrieval-ai/near-duplicate-evidence-and-independent-support|Lineage checks]] help distinguish a copied positive from a real contradiction."),
            ("Audit false negatives before training", "Compare each mined candidate with all known positives by document lineage, answer entity, valid interval and evidence span. Flag near-identical answers and ambiguous cases for human review. Do not automatically turn every high-scoring unlabeled passage into a negative. If the corpus has a corrected revision, the old passage may be a legitimate negative for a current-policy query but a positive for an as-of query. [[retrieval-ai/temporal-retrieval-as-of-validity-and-conflicts|Temporal eligibility]] belongs in the label, not only the search filter."),
            ("Prevent split leakage", "A test question and a training question can differ in wording while pointing to the same source paragraph. Split by source lineage or entity family when the evaluation asks for transfer to unseen material. Keep mined examples from a fixed training snapshot; a later corpus refresh must not add evaluation positives to the training pool. Log query ID, passage ID, source revision, mine score, decision and reviewer. [[retrieval-ai/retrieval-release-evaluation-and-slice-gates|Release gates]] should compare held-out supported recall, not training loss alone."),
            ("Measure the cost of hardness", "Run an ablation with the same query set and candidate budget: baseline negatives, reviewed hard negatives, and mixed difficulty. Track false-negative audit rate, candidate recall, top-k judged relevance and answer support on held-out slices. If mining improves ranking for common queries but harms a rare language or recent-policy slice, do not ship the aggregate gain as universal. Keep a small manual audit of top-ranked new negatives after each mining cycle; retriever changes alter which mistakes are selected next."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class MinedPassage:
    passage_id: str
    tenant: str
    lineage: str
    entity_id: str
    label: str
    score: float

def reviewed_negatives(candidates: list[MinedPassage], tenant: str,
                       positive_lineages: set[str], entity_id: str) -> list[str]:
    selected = [candidate for candidate in candidates
                if candidate.tenant == tenant and candidate.label == "negative"
                and candidate.lineage not in positive_lineages
                and candidate.entity_id != entity_id]
    return [candidate.passage_id for candidate in
            sorted(selected, key=lambda item: item.score, reverse=True)]

pool = [MinedPassage("pump-48", "plant-a", "manual-48", "pump-p48", "negative", .94),
        MinedPassage("copied-p47", "plant-a", "manual-47", "pump-p47", "negative", .99),
        MinedPassage("unreviewed", "plant-a", "manual-52", "pump-p52", "unknown", .96),
        MinedPassage("private", "plant-b", "manual-49", "pump-p49", "negative", .98)]
assert reviewed_negatives(pool, "plant-a", {"manual-47"}, "pump-p47") == ["pump-48"]''',
        "cost": "Filtering N mined candidates costs O(N log N) time because the sample sorts by score, with O(N) extra space; a bounded top-k heap can reduce sorting work when N is large. The expensive part is creating and auditing labels: retrieval calls, cross-source comparisons and human adjudication. Spend that budget on candidates likely to change a decision, not on repeated copies of the same mistake.",
        "mistakes": ["Treating every unlabeled retrieved passage as a negative.", "Mining a copied positive into the negative pool because it has a new URL.", "Letting test-source lineages enter the training candidate pool.", "Judging the mining run only by training loss or one aggregate retrieval score."],
        "drill": "Mine 79 candidates for 23 queries from lexical and dense pools. Review ambiguous matches, split by document lineage, and compare held-out top-five relevance and supported-answer rate before accepting the new negatives.",
        "related": [prefix + "retrieval-evaluation-labels-and-adjudication", prefix + "near-duplicate-evidence-and-independent-support", prefix + "temporal-retrieval-as-of-validity-and-conflicts", prefix + "retrieval-release-evaluation-and-slice-gates"],
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
        "featured": False, "sort_order": 8441 + offset, "status": "published",
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
    row["data"]["modules"].append({"title": "Language, code, media and training data", "lessons": new_paths})
    row["body"] += '<h2>Language, code, media and training data</h2><ul>' + ''.join(
        f'<li>{link(target)}</li>' for target in new_paths) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "query-expansion-guardrails-and-drift-tests": [new_paths[0]],
    prefix + "knowledge-graph-retrieval-and-edge-provenance": [new_paths[1]],
    prefix + "multimodal-retrieval-and-asset-identity": [new_paths[2]],
    prefix + "retrieval-evaluation-labels-and-adjudication": [new_paths[3]],
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
