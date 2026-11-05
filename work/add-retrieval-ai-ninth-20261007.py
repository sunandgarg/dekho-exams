"""Add original retrieval lessons for calibration, feedback, consent and freshness."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-retrieval-ai-ninth-import-20261007.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "retrieval-ai/"
hub_path = prefix + "retrieval-ai-tutorial"

lessons = [
    {
        "slug": "score-normalization-and-fusion-calibration",
        "title": "Score normalization: combine retrievers without inventing certainty",
        "summary": "Normalize lexical and vector rankings for fusion, then validate separately whether fused scores predict useful evidence.",
        "sections": [
            ("Keep score meanings separate", "A lexical score, a vector similarity and a cross-encoder score are produced by different computations. Their raw values do not share a common unit, and even one retriever's range can shift with query length, corpus size or model version. Adding them directly lets the largest numeric scale dominate the merged ranking. Reciprocal-rank fusion avoids raw score arithmetic, while a weighted linear blend requires a stated normalization rule. Neither result is automatically a probability that the passage supports the answer. [[retrieval-ai/hybrid-search-and-reciprocal-rank-fusion|Hybrid fusion]] explains the candidate merge; this lesson covers the meaning and limits of its numeric scores."),
            ("Normalize inside the candidate window", "For a given query, min-max scaling maps the observed lowest and highest candidate scores to zero and one. It is easy to inspect, but it depends on the candidate window: adding a single outlier changes every scaled value. A constant-score list needs a defined fallback rather than division by zero. L2 normalization and rank-based methods have different behavior. Select one with judged queries, keep its configuration version, and never compare a min-max value from one query to another as if both were calibrated relevance probabilities."),
            ("Apply eligibility before blending", "Permission, tenant, revision and source-status filters are hard constraints. If an unauthorized record gets a high fused score and is removed only after top-K truncation, it can displace the answer-bearing record. Build separate eligible lexical and vector candidate lists, normalize within the eligible window, then fuse. Missing candidates need an explicit default contribution; they should not be assigned a fabricated high score merely to keep each branch represented. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Corpus permissions]] must remain independent of ranking math."),
            ("Calibrate support on labeled evidence", "A fused score can order passages well yet be a poor threshold for abstention. To decide whether to answer, collect judged query-passage pairs and measure supported-answer precision at candidate thresholds by domain, language and source. Calibrate a decision rule against that labeled set, then test it on held-out queries. Recalibrate after changing an encoder, lexical analyzer, candidate window or normalization method. [[retrieval-ai/evidence-bound-answer-and-abstention|Evidence-bound answers]] should use support checks, not a raw similarity cutoff that happened to work on a few examples."),
            ("Monitor score drift with release slices", "Record the per-query lexical and vector score distributions, overlap between branches, fused top-K stability and the number of abstentions. A new corpus of short titles can raise lexical scores without improving evidence. An embedding update can narrow cosine-score spread while retrieval recall falls. Compare judged slices and score histograms against one fixed corpus snapshot before release. If the fusion change improves average ranking but loses exact-ID questions, keep a hard exact-ID path. [[retrieval-ai/retrieval-release-evaluation-and-slice-gates|Release gates]] should expose that regression."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class BranchScore:
    passage_id: str
    lexical: float | None
    vector: float | None

def scale(values: list[float]) -> dict[float, float]:
    if not values:
        return {}
    low, high = min(values), max(values)
    return {value: (value - low) / (high - low) if high > low else 1.0
            for value in values}

def fused_rank(candidates: list[BranchScore]) -> list[tuple[str, float]]:
    lexical = scale([item.lexical for item in candidates if item.lexical is not None])
    vector = scale([item.vector for item in candidates if item.vector is not None])
    ranked = [(item.passage_id,
               .6 * lexical.get(item.lexical, 0.0)
               + .4 * vector.get(item.vector, 0.0))
              for item in candidates]
    return sorted(ranked, key=lambda pair: (-pair[1], pair[0]))

passages = [BranchScore("pump-p47-manual", 13.0, .82),
            BranchScore("pump-p47-note", 4.0, .78),
            BranchScore("pump-p48-manual", 2.0, .54)]
assert fused_rank(passages)[0][0] == "pump-p47-manual"
assert scale([.47, .47]) == {.47: 1.0}''',
        "cost": "For C eligible candidates, finding per-branch extrema and scoring each item costs O(C) time; sorting the merged result costs O(C log C) time and O(C) working space. Min-max values are defined only relative to the observed window. Training a support threshold costs additional judged labels and must be repeated when branch distributions change. Filter eligibility before this work so a high-scoring forbidden candidate cannot consume the window.",
        "mistakes": ["Adding raw lexical and vector scores as if they had a shared scale.", "Treating a fused score of 0.8 as an 80 percent chance of answer support.", "Normalizing before removing ineligible documents that can distort the range.", "Using a constant-score branch without defining how it contributes."],
        "drill": "Run 47 labeled questions through rank fusion and two score normalizers. For each, record recall at 12, supported top-one precision, outlier sensitivity and exact-identifier misses.",
        "related": [prefix + "hybrid-search-and-reciprocal-rank-fusion", prefix + "evidence-bound-answer-and-abstention", prefix + "lexical-analyzers-field-scoring-and-identifier-safety", prefix + "retrieval-release-evaluation-and-slice-gates"],
    },
    {
        "slug": "click-feedback-position-bias-and-offline-evaluation",
        "title": "Click feedback: correct exposure bias before tuning retrieval",
        "summary": "Use logged exposure probabilities and judged evidence to keep clicks from reinforcing the ranking that produced them.",
        "sections": [
            ("A click is an observation, not a label", "Search logs record what users were shown and what they clicked. A top-ranked result is usually examined more often than a lower-ranked result, so more clicks do not prove greater relevance. Snippet wording, device layout, query ambiguity and a satisfied user who never clicks can alter behavior as well. Keep impressions, rank positions, query class and click outcomes together. Do not label every unclicked result irrelevant, because it may never have been seen. [[retrieval-ai/retrieval-evaluation-labels-and-adjudication|Judged relevance labels]] remain the anchor for measuring whether retrieved evidence truly answers a question."),
            ("Log the policy that chose the result", "Offline comparison of two rankings needs to know how likely the logging policy was to show each observed result in that position. Randomized or carefully designed interleaving traffic can provide such propensities, but changing the order of high-stakes evidence merely to collect data can be unacceptable. Record policy version and selection probability at impression time; reconstructing it later from final rankings is fragile. A target policy must have support wherever it assigns probability, otherwise logged data cannot estimate its behavior there. [[retrieval-ai/retrieval-traces-and-incident-debugging|Retrieval traces]] give each exposure its candidate and policy identity."),
            ("Estimate with bounded weights", "Inverse-propensity weighting gives greater weight to observations that were unlikely under the logging policy but likely under the target policy. Very small logging probabilities produce high-variance estimates, so define a floor or clip and report the resulting bias-variance tradeoff. Keep query-level confidence intervals and do not call an offline score a guaranteed online gain. A tiny code sample can demonstrate the arithmetic; real deployment evaluation needs a randomized logging design and careful outcome definition. [[retrieval-ai/retrieval-release-evaluation-and-slice-gates|Release evaluation]] should compare offline evidence with judged slices before any traffic change."),
            ("Avoid feedback loops", "If a retriever promotes what was clicked yesterday, those results get more exposure today and may collect still more clicks. New or niche documents receive little data and can be unfairly buried. Keep some exploration within safe, eligible candidate sets, cap how quickly behavior changes ranking weights and audit exposure by source and topic. Never use clicks to bypass permission or source-trust filters. [[retrieval-ai/corpus-poisoning-trust-tiers-and-evidence-admission|Evidence admission]] must happen before any learned click signal is applied."),
            ("Evaluate the outcome that matters", "A click on a plausible but stale snippet can be worse than no click. Combine behavioral signals with supported-answer judgments, abandonment, reformulation and task-completion measures. Segment by mobile versus desktop, head versus rare queries and new versus established documents. Check for a ranking that improves click-through while reducing answer-bearing passage recall or increasing unsupported claims. Preserve a fixed holdout set and an escape path to the previous ranking policy if a monitored slice degrades."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class LoggedExposure:
    query_id: str
    clicked: bool
    logged_probability: float
    target_probability: float

def propensity_weighted_clicks(events: list[LoggedExposure]) -> float:
    if not events:
        raise ValueError("evaluation needs impressions")
    total = 0.0
    for event in events:
        if not 0 < event.logged_probability <= 1:
            raise ValueError("invalid logging probability")
        if not 0 <= event.target_probability <= 1:
            raise ValueError("invalid target probability")
        total += float(event.clicked) * event.target_probability / event.logged_probability
    return total / len(events)

impressions = [LoggedExposure("seal-pressure-1", True, .5, .25),
               LoggedExposure("seal-pressure-2", False, .5, .75)]
assert propensity_weighted_clicks(impressions) == .25''',
        "cost": "Computing this illustrative inverse-propensity estimate costs O(E) time for E logged impressions and O(1) extra space. Collection and storage costs grow with impressions, policy metadata and retention period. Low logging probabilities increase estimator variance; clipping reduces that variance but changes the estimate. Use the code as an arithmetic contract, not as a complete causal evaluation design or a substitute for judged relevance and online safety checks.",
        "mistakes": ["Treating an unclicked low-ranked result as a negative relevance label.", "Estimating a target policy where the logging policy never exposed its candidates.", "Ignoring very large inverse-propensity weights and their variance.", "Optimizing click-through while answer support and source trust get worse."],
        "drill": "Design 31 judged queries with two safe ranking policies. Log impressions, positions, policy probabilities and support labels; compare raw clicks with weighted estimates and report uncertainty by query slice.",
        "related": [prefix + "retrieval-evaluation-labels-and-adjudication", prefix + "retrieval-release-evaluation-and-slice-gates", prefix + "retrieval-traces-and-incident-debugging", prefix + "corpus-poisoning-trust-tiers-and-evidence-admission"],
    },
    {
        "slug": "personalized-retrieval-consent-and-memory-boundaries",
        "title": "Personalized retrieval: preferences never grant access",
        "summary": "Apply explicit user preferences only after access checks, with clear consent, cache isolation and deletion behavior.",
        "sections": [
            ("Separate preference from permission", "Personalized retrieval can rank eligible material using a reader's chosen topics, reading level or current project. That preference cannot make an unauthorized document eligible. First apply tenant, group and document lifecycle filters from the active authenticated session; only then adjust the rank of remaining candidates. A model's guess about a user's role is not an access token. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Corpus permissions]] define the hard boundary; personalization operates inside it."),
            ("Collect only useful state", "Store explicit preference fields with their purpose, consent state and expiration. A recent query may be useful for one follow-up without becoming permanent memory. Do not silently turn private questions or retrieved passages into a lasting user profile. Let the user inspect, correct or clear preference state, and make the default search path useful with no personalization at all. [[retrieval-ai/conversational-query-rewrite-and-constraint-carryover|Conversation rewriting]] may carry a short-lived entity or constraint, but it should not import unrelated history into a new search."),
            ("Isolate caches and embeddings", "A result cache keyed only by query text can leak personalized ranks or even snippets across accounts. Include identity scope, authorization version, preference version and corpus generation where those affect output, or decline to cache the result. User-specific embeddings create another derived-data copy that must be covered by retention and deletion rules. If consent is withdrawn, stop using the feature immediately and invalidate cached outputs. [[retrieval-ai/permission-aware-cache-and-conversation-turns|Permission-aware caches]] provide the same discipline for nonpersonalized conversation turns."),
            ("Keep explanations specific", "When personalization changes order, show a concise reason such as 'your selected Java topic' rather than implying the top document is more authoritative. User preferences can help choose among equally eligible tutorials, but they should not override exact identifiers, current policy revision or evidence support. A strong preference for one source can create a narrow view that misses contradictory material, so diversify when the task calls for comparison. [[retrieval-ai/context-packing-and-evidence-diversity|Evidence diversity]] helps prevent a preference filter from hiding necessary counterevidence."),
            ("Test consent transitions", "Build cases for opt-in, opt-out, changed group membership, preference deletion, shared devices and two users with the same query. Verify that unauthorized documents never enter candidates, personalized ranks disappear after opt-out and no cached response crosses an identity boundary. Measure whether personalization improves task completion or merely raises clicks on familiar material. Review long-tail users separately; sparse history can make the model's inferred interests unstable."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class ReaderContext:
    tenant: str
    groups: frozenset[str]
    consent: bool
    preferred_topic: str | None

@dataclass(frozen=True)
class SearchDocument:
    document_id: str
    tenant: str
    required_group: str
    topic: str
    relevance: float

def ranked_for_reader(reader: ReaderContext,
                      documents: list[SearchDocument]) -> list[str]:
    allowed = [document for document in documents
               if document.tenant == reader.tenant
               and document.required_group in reader.groups]
    return [document.document_id for document in sorted(
        allowed,
        key=lambda document: (-(document.relevance + (
            .1 if reader.consent and document.topic == reader.preferred_topic else 0)),
            document.document_id))]

reader = ReaderContext("north", frozenset({"engineers"}), True, "maintenance")
documents = [SearchDocument("pump-p47", "north", "engineers", "maintenance", .72),
             SearchDocument("salary-plan", "north", "finance", "maintenance", .99),
             SearchDocument("pump-p48", "south", "engineers", "maintenance", .97)]
assert ranked_for_reader(reader, documents) == ["pump-p47"]
assert ranked_for_reader(ReaderContext("north", reader.groups, False, None), documents) == ["pump-p47"]''',
        "cost": "Filtering and sorting N candidates costs O(N log N) time and O(N) working space in this small implementation. An index should apply tenant and group constraints before ranking to avoid scanning ineligible documents. Per-user state and cache keys increase storage cardinality, so set retention limits and avoid caching low-reuse private results. Preference boosts should be evaluated separately from authorization and evidence support.",
        "mistakes": ["Using a predicted role or preferred topic as an access grant.", "Caching personalized snippets under only the query text.", "Keeping query history after a user withdraws personalization consent.", "Letting a preference boost hide a newer or contradictory source."],
        "drill": "Create 29 two-user scenarios with shared queries, group changes and opt-out events. Verify no cross-user snippet appears, then measure whether explicit preferences improve supported task completion.",
        "related": [prefix + "corpus-permissions-and-document-lifecycle", prefix + "permission-aware-cache-and-conversation-turns", prefix + "conversational-query-rewrite-and-constraint-carryover", prefix + "context-packing-and-evidence-diversity"],
    },
    {
        "slug": "index-watermarks-freshness-slos-and-stale-answer-policy",
        "title": "Index watermarks: measure what the retriever has actually seen",
        "summary": "Use per-source progress markers to distinguish a fresh source document from an index that has not applied its latest update.",
        "sections": [
            ("Define freshness at the serving boundary", "A document's edited-at timestamp says when its source changed, not when lexical, vector and metadata indexes became ready to serve that change. Track source event offsets and the highest contiguous offset applied to each serving component. A gap matters: processing event 94 while event 93 failed does not make 94 a safe watermark. Expose the minimum ready offset across components required for the query. [[retrieval-ai/incremental-ingestion-idempotency-and-delete-races|Incremental ingestion]] supplies the event ordering and retry contract behind that marker."),
            ("Give queries a required freshness", "A historical how-to question may tolerate a short index delay; an access-revocation or active incident question may not. Express the requirement as a source offset, snapshot token or bounded age tied to a documented source clock. If the serving watermark is behind, wait only within the request budget, then use an explicit stale-answer policy: return a labeled older snapshot, query an authoritative live source, or abstain. Do not quietly answer from stale evidence while presenting it as current. [[retrieval-ai/evidence-bound-answer-and-abstention|Abstention]] is the correct result when freshness is required and cannot be established."),
            ("Keep deletes in the same progress model", "Deletion and permission revocation are not ordinary updates. A vector may linger after the document disappears from the source; a cache can still hold its snippet. Track a revocation watermark for every serving path that could expose the material and require it to reach the requested offset. Quarantine or deny a known revoked document immediately, even if rebuilding the full index takes longer. [[retrieval-ai/freshness-deletion-and-index-swap|Deletion controls]] must cover the source, index and caches, not just a database flag."),
            ("Measure lag by source and slice", "An average ingestion delay hides one stuck partition. Report p95 and maximum lag, oldest unapplied event age, contiguous watermark and count of failed events by source. The query trace should show the freshness requirement and the watermarks actually used. Alert on lag that threatens the service target, not merely on high queue depth. A queue can be empty while a poison event is parked in a dead-letter path and the watermark is frozen. [[retrieval-ai/retrieval-traces-and-incident-debugging|Traces]] connect stale answers to the precise lagging component."),
            ("Test races with a fixed answer contract", "Replay an update, a delete and a permission withdrawal while lexical and vector ingestion advance at different rates. Ask the same question before and after each watermark crosses the required offset. The answer may change only when a coherent serving view is ready; it must never reveal a revoked passage. Include event retries and out-of-order delivery. [[retrieval-ai/snapshot-consistent-multi-index-retrieval|Snapshot consistency]] chooses a coherent generation once each component advertises progress."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class IndexProgress:
    component: str
    source_offset: int
    visible_offset: int
    revocation_offset: int

def ready_for_answer(progress: list[IndexProgress], required_offset: int,
                     must_cover_revocations: bool = True) -> bool:
    if not progress or required_offset < 0:
        return False
    return all(state.visible_offset >= required_offset
               and (not must_cover_revocations
                    or state.revocation_offset >= required_offset)
               for state in progress)

components = [IndexProgress("lexical", 93, 93, 93),
              IndexProgress("vector", 93, 92, 93)]
assert not ready_for_answer(components, 93)
assert ready_for_answer(components, 92)
components[1] = IndexProgress("vector", 93, 93, 93)
assert ready_for_answer(components, 93)''',
        "cost": "A readiness check scans S serving components in O(S) time and O(1) extra space. Maintaining contiguous watermarks takes durable offset tracking and retry state per partition. A strict freshness target can increase latency or abstention when one component lags; measure those effects against the value of a current answer. Never trade away revocation checks to improve an apparent freshness score.",
        "mistakes": ["Using source edited-at time as proof that the vector index has applied an update.", "Advancing a watermark past an unprocessed event gap.", "Treating a delete as complete when a cached passage can still be served.", "Reporting only average lag while one partition is stuck."],
        "drill": "Simulate 37 ordered source events with two dropped updates and one revocation. Record each component watermark and verify exactly when a current answer becomes eligible.",
        "related": [prefix + "incremental-ingestion-idempotency-and-delete-races", prefix + "freshness-deletion-and-index-swap", prefix + "snapshot-consistent-multi-index-retrieval", prefix + "retrieval-traces-and-incident-debugging"],
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
        "featured": False, "sort_order": 8457 + offset, "status": "published",
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
    row["data"]["modules"].append({"title": "Score calibration, feedback, consent and freshness", "lessons": new_paths})
    row["body"] += '<h2>Score calibration, feedback, consent and freshness</h2><ul>' + ''.join(
        f'<li>{link(target)}</li>' for target in new_paths) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "hybrid-search-and-reciprocal-rank-fusion": [new_paths[0]],
    prefix + "retrieval-evaluation-labels-and-adjudication": [new_paths[1]],
    prefix + "permission-aware-cache-and-conversation-turns": [new_paths[2]],
    prefix + "incremental-ingestion-idempotency-and-delete-races": [new_paths[3]],
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
