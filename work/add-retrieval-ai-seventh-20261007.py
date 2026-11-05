"""Add original retrieval lessons for images, event windows, entities and tests."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
packet = root / "work/aitrove-retrieval-ai-seventh-import-20261007.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
prefix = "retrieval-ai/"
hub_path = prefix + "retrieval-ai-tutorial"

lessons = [
    {
        "slug": "image-region-retrieval-and-visual-grounding",
        "title": "Image-region retrieval: cite the object, not merely the image",
        "summary": "Retrieve a bounded visual region and preserve its asset version, crop coordinates and supporting labels.",
        "sections": [
            ("Index regions with their parent asset", "Image-region retrieval searches a part of an image that can support a specific claim. A maintenance photo may show several pumps, warning tags and gauges; an image-level match for 'P-47 gauge' says little about which gauge carries the reading. Store asset ID, version, image dimensions, region coordinates and any reviewed label. A crop is not an independent source: it inherits access rules and revision from the parent image. [[retrieval-ai/multimodal-retrieval-and-asset-identity|Asset identity]] prevents a crop coordinate from silently pointing at a replacement photograph."),
            ("Generate and score candidates", "Regions can come from reviewed annotations, object proposals or a grid of crops. Search their labels and visual representations, then cap the candidate window before expensive inspection. Overlapping proposals for one object should not consume every slot. Group them by parent asset and approximate overlap, retaining a precise box when evidence supports it. A predicted label is a search hint, not proof that the pictured valve is P-47. [[retrieval-ai/near-duplicate-evidence-and-independent-support|Duplicate control]] helps keep copied crops from masquerading as independent sightings."),
            ("Ground the claim spatially", "The answer should point to a region whose visible pixels support it. A caption outside the crop may identify the object, but the caption and image need separate provenance. If the query asks whether a red lockout tag is attached, a close crop of the tag alone might hide whether it is attached to the requested pump. Keep enough surrounding context to verify the relationship without turning the citation into the whole image. [[retrieval-ai/claim-level-citation-and-support-checks|Claim support]] must inspect the crop and its parent context."),
            ("Account for transformations", "Resizing, rotation and cropping change coordinates. Store boxes in a stable source coordinate system and record any display transform; never reuse pixel positions on a newly cropped image without mapping them. Check privacy masks at the source and crop levels. A face blurred in the full image can reappear if an unredacted original is cropped and served separately. Reject regions whose bounds fall outside the asset or whose version mismatches the current display. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Lifecycle rules]] include withdrawing all derived crops after an asset is removed."),
            ("Evaluate region-level evidence", "Judge both parent-image recall and region overlap with the answer-bearing object. Include small objects, similar gauges, partially occluded labels, repeated components and misleading captions. A system that finds the correct photo but draws a box around the wrong gauge should fail. Track unsupported confident labels and missing-evidence abstentions separately. Measure the cost of finer crops against their improvement in supported claims, rather than indexing thousands of near-identical patches without a clear gain."),
        ],
        "code": '''from dataclasses import dataclass

@dataclass(frozen=True)
class ImageRegion:
    asset_id: str
    version: str
    width: int
    height: int
    box: tuple[int, int, int, int]
    label: str

def checked_region(region: ImageRegion, expected_version: str) -> tuple[float, float, float, float]:
    if region.version != expected_version:
        raise ValueError("asset version mismatch")
    left, top, right, bottom = region.box
    if region.width <= 0 or region.height <= 0 or not (0 <= left < right <= region.width):
        raise ValueError("invalid horizontal bounds")
    if not 0 <= top < bottom <= region.height:
        raise ValueError("invalid vertical bounds")
    return (left / region.width, top / region.height,
            right / region.width, bottom / region.height)

gauge = ImageRegion("plant-photo-47", "v3", 1200, 800,
                    (240, 160, 600, 560), "P-47 pressure gauge")
assert checked_region(gauge, "v3") == (.2, .2, .5, .7)
try:
    checked_region(gauge, "v2")
except ValueError:
    pass
else:
    raise AssertionError("stale crop accepted")''',
        "cost": "Validating one region is O(1) time and space. A full image with R proposed regions needs storage and embedding work proportional to R, plus overlap grouping if many proposals duplicate the same object. Candidate generation can be bounded by asset and region counts; visual inspection is the costly stage. Keep source-resolution crops only for regions that survive retrieval and access checks.",
        "mistakes": ["Citing an image when the requested object is not identifiable within it.", "Using crop coordinates from a different image version.", "Treating a detector's label as verified identity.", "Serving an unredacted crop of a redacted parent asset."],
        "drill": "Judge 41 questions over 23 photographs containing repeated gauges, tags and valves. Score asset recall, region overlap and claim support; require rejection of stale-version boxes.",
        "related": [prefix + "multimodal-retrieval-and-asset-identity", prefix + "ocr-layout-reading-order-and-confidence", prefix + "claim-level-citation-and-support-checks", prefix + "near-duplicate-evidence-and-independent-support"],
    },
    {
        "slug": "event-window-retrieval-and-gap-semantics",
        "title": "Event-window retrieval: answer from complete time slices",
        "summary": "Retrieve logs and measurements with explicit event time, observation time, window bounds and missing-data behavior.",
        "sections": [
            ("Define the clock and window", "Event-window retrieval finds records that occurred in a requested interval, not merely records indexed recently. A query about pump P-47 alarms between 09:00 and 09:30 must use event time; observation time describes when the collector received a record. Late arrivals and device clock drift can make those differ. Store both clocks, source ID, event ID and a normalized time zone. Use half-open windows so adjacent intervals do not count the same event twice. [[retrieval-ai/temporal-retrieval-as-of-validity-and-conflicts|Temporal retrieval]] supplies the same boundary discipline for document validity, but event streams have additional lateness and completeness issues."),
            ("Join events by stable identity", "A trace ID, asset ID or incident ID can join logs from several services. Free-text similarity between two error messages is not sufficient to claim they describe the same incident. Apply tenant and asset filters before joining, then retain each event's source and original timestamp. A repeated warning may be a retry of one operation or many separate failures; deduplicate only with a stable event or request identity. [[retrieval-ai/near-duplicate-evidence-and-independent-support|Duplicate evidence]] rules keep retries from inflating a count."),
            ("Treat gaps as unknown", "No retrieved alarm is not proof that no alarm occurred. The collector may have been offline, the index may lag, or the query may cover a shard not searched. Record source watermarks and missing intervals. When a window is incomplete, report the covered interval and abstain from a global zero count. A late event can change a previously computed result; either revise the answer or pin it to a snapshot and explain the cutoff. [[retrieval-ai/freshness-deletion-and-index-swap|Freshness controls]] should expose that cutoff in the trace."),
            ("Separate retrieval from aggregation", "Retrieve the eligible events first, then compute counts, maxima or sequences deterministically. A p95 latency claim requires enough samples and an explicit percentile method; a single high value is not the percentile. For a sequence question, preserve ordering by event time and break ties with stable IDs. Apply units and sampling rates before combining sensor readings. [[retrieval-ai/table-retrieval-and-numeric-cell-context|Numeric context]] is as important for telemetry as it is for a table cell."),
            ("Evaluate late and partial data", "Build cases with out-of-order arrivals, clock skew, duplicate retries, collector outages, overlapping windows and no matching events. Judge event recall, window-boundary correctness, join identity, completeness detection and final answer support separately. A high recall score on available records can still mask an incorrect 'nothing happened' answer when a source is missing. Keep both query time and data snapshot in the evaluation record so later backfills do not silently change the expected result."),
        ],
        "code": '''from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True)
class AlarmEvent:
    event_id: str
    tenant: str
    asset_id: str
    occurred_at: datetime
    observed_at: datetime

def window_events(events: list[AlarmEvent], tenant: str, asset_id: str,
                  start: datetime, end: datetime) -> list[str]:
    if start.tzinfo is None or end.tzinfo is None or end <= start:
        raise ValueError("window needs ordered aware datetimes")
    seen: set[str] = set()
    selected: list[str] = []
    for event in sorted(events, key=lambda item: (item.occurred_at, item.event_id)):
        if event.tenant == tenant and event.asset_id == asset_id \\
                and start <= event.occurred_at < end and event.event_id not in seen:
            seen.add(event.event_id)
            selected.append(event.event_id)
    return selected

utc = timezone.utc
event_time = datetime(2026, 10, 7, 9, 17, tzinfo=utc)
alarms = [AlarmEvent("alarm-47", "north", "P-47", event_time,
                     datetime(2026, 10, 7, 9, 39, tzinfo=utc)),
          AlarmEvent("alarm-47", "north", "P-47", event_time,
                     datetime(2026, 10, 7, 9, 40, tzinfo=utc))]
assert window_events(alarms, "north", "P-47",
                     datetime(2026, 10, 7, 9, 0, tzinfo=utc),
                     datetime(2026, 10, 7, 9, 30, tzinfo=utc)) == ["alarm-47"]''',
        "cost": "Sorting N events costs O(N log N) time and O(N) space in the example; an index ordered by tenant, asset and event time narrows production windows. Watermarks and coverage records add modest metadata but are necessary for trustworthy zero-result answers. Wider windows increase scanned events and aggregation cost, so apply a query limit and stream large results.",
        "mistakes": ["Filtering by collector arrival time when the question asks when an event occurred.", "Calling an incomplete window empty.", "Counting duplicate retries as independent alarms.", "Using naive local timestamps across a daylight-saving boundary."],
        "drill": "Build 67 events over three assets with delayed arrivals and two collector gaps. Judge 31 window questions, requiring correct half-open boundaries and an explicit incomplete-data result where coverage is missing.",
        "related": [prefix + "temporal-retrieval-as-of-validity-and-conflicts", prefix + "freshness-deletion-and-index-swap", prefix + "near-duplicate-evidence-and-independent-support", prefix + "retrieval-traces-and-incident-debugging"],
    },
    {
        "slug": "entity-linking-aliases-and-ambiguous-mentions",
        "title": "Entity linking for retrieval: resolve aliases before searching facts",
        "summary": "Map mentions to stable entity IDs while retaining ambiguity, alias provenance and out-of-catalog behavior.",
        "sections": [
            ("Separate mention from identity", "Entity linking maps a surface mention in a query to a canonical entity ID. 'P-47' might identify a pump in one plant and a permit in another; spelling alone is not identity. Store type, tenant, site, active interval and reviewed aliases with each entity. Preserve the original mention in the search trace, and do not replace it with a canonical ID until context establishes the match. [[retrieval-ai/multilingual-retrieval-and-entity-preservation|Multilingual retrieval]] may supply transliterated aliases, but an alias can still be shared by distinct entities."),
            ("Generate candidates then decide", "Exact alias search produces candidates. Type constraints, nearby words, site and time narrow them; semantic similarity can rank the remainder. Keep a no-match outcome for an unknown entity instead of forcing every mention onto the closest catalog entry. If two candidates remain plausible, ask for a clarifier or search both as explicitly separate interpretations. [[retrieval-ai/conversational-query-rewrite-and-constraint-carryover|Conversation state]] can supply an antecedent, but an old assistant answer is not authoritative identity evidence."),
            ("Carry identity through evidence", "After linking, retrieve passages tagged with the stable entity ID and current authorization scope. A document can mention several entities, so a page-level tag may be too coarse: the cited span must actually refer to the selected entity. If an entity is renamed, maintain alias history and effective dates rather than rewriting old documents. If IDs are merged or split, preserve the mapping event; otherwise historical citations can point to a different object. [[retrieval-ai/chunk-identity-and-context-boundaries|Chunk identity]] and entity identity solve different problems and both belong in the trace."),
            ("Guard against alias poisoning", "User-submitted content may claim that an unrelated part number is an alias for a restricted asset. Accept aliases only from reviewed catalog changes, not from retrieved passages or prompt text. Apply access checks to candidate IDs and to their associated documents; even an ambiguous candidate list can leak a private device name. Normalize Unicode carefully, but do not erase distinctions that matter in identifiers. [[retrieval-ai/prompt-injection-and-tool-boundary|Tool boundaries]] keep source text from changing the resolver's catalog."),
            ("Evaluate more than top-one accuracy", "Judge exact aliases, spelling changes, transliterations, shared names, unknown entities and historical renames. Measure candidate recall, correct-ID selection, abstention for unknown mentions, and downstream supported answers. A top-one metric alone rewards a resolver that confidently guesses on every unknown name. Track entity type and language slices separately. Review cases where linking is correct but the retrieved passage refers to a different entity in the same document; that is an evidence-span error, not a linking success."),
        ],
        "code": '''from dataclasses import dataclass
import unicodedata

@dataclass(frozen=True)
class CatalogEntity:
    entity_id: str
    tenant: str
    kind: str
    site: str
    aliases: tuple[str, ...]

def alias_key(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold().strip()

def resolve_entity(catalog: list[CatalogEntity], tenant: str, kind: str,
                   site: str, mention: str) -> str | None:
    matches = [entry.entity_id for entry in catalog
               if entry.tenant == tenant and entry.kind == kind and entry.site == site
               and alias_key(mention) in {alias_key(alias) for alias in entry.aliases}]
    if len(matches) > 1:
        raise ValueError("ambiguous alias; request clarification")
    return matches[0] if matches else None

catalog = [CatalogEntity("pump-47-north", "north", "pump", "plant-a", ("P-47", "Pump 47")),
           CatalogEntity("permit-47-north", "north", "permit", "plant-a", ("P-47",)),
           CatalogEntity("pump-47-south", "south", "pump", "plant-b", ("P-47",))]
assert resolve_entity(catalog, "north", "pump", "plant-a", "P-47") == "pump-47-north"
assert resolve_entity(catalog, "north", "pump", "plant-a", "P-48") is None''',
        "cost": "The transparent scan checks N catalog entries and up to A aliases per entry, costing O(NA) time with temporary alias sets. An alias index keyed by normalized mention, tenant and type reduces candidate lookup, but it must update atomically with catalog changes. Preserve multiple candidates until context resolves them; forcing one ID can be cheaper per query but costlier in downstream incorrect answers.",
        "mistakes": ["Treating a shared alias as a globally unique entity ID.", "Forcing unknown mentions onto the nearest catalog item.", "Letting retrieved text edit the trusted alias catalog.", "Tagging a whole document as support when its cited span refers to another entity."],
        "drill": "Create 83 mentions across two tenants and three entity types, including 17 ambiguous aliases and nine unknowns. Score correct IDs, ambiguity handling, unknown abstention and supported downstream passages.",
        "related": [prefix + "multilingual-retrieval-and-entity-preservation", prefix + "conversational-query-rewrite-and-constraint-carryover", prefix + "chunk-identity-and-context-boundaries", prefix + "prompt-injection-and-tool-boundary"],
    },
    {
        "slug": "counterfactual-retrieval-tests-and-distractor-resilience",
        "title": "Counterfactual retrieval tests: change one fact and trace the failure",
        "summary": "Probe retrieval and answer support with controlled evidence edits, plausible distractors and first-loss diagnosis.",
        "sections": [
            ("Change one controlled variable", "A counterfactual retrieval test alters an evidence fact while keeping the rest of the query and corpus stable. Replace a pump limit of 83 kPa with 67 kPa in a synthetic revision, or swap the relevant entity ID, then check whether retrieval and the answer respond to that change. The point is to expose reliance on memorized or distracting text. Use synthetic, clearly isolated fixtures; never mutate a production source or present a test revision as a real policy. [[retrieval-ai/retrieval-release-evaluation-and-slice-gates|Release evaluation]] can run these cases as a separate judged slice."),
            ("Keep labels and access coherent", "When a fact changes, update the gold passage, expected answer, revision metadata and all copied evidence that derives from it. Leave unrelated passages unchanged. A distractor can be highly similar yet invalid because its entity, date, tenant or negation differs. If the counterfactual version conflicts with a legitimate original left in the same eligible corpus, the expected behavior may be conflict reporting, not a forced new number. [[retrieval-ai/near-duplicate-evidence-and-independent-support|Lineage controls]] help distinguish an accidental duplicate from independent contradictory evidence."),
            ("Locate the first loss", "Trace whether the edited passage enters the lexical or vector candidate pool, survives filters and reranking, reaches the context window, and supports the final claim. A wrong answer with the correct passage in context is an answer-use failure; a correct answer after the passage was excluded may indicate memorization or leakage. Do not call both failures 'retrieval quality'. [[retrieval-ai/retrieval-traces-and-incident-debugging|Retrieval traces]] should carry candidate IDs and score stages so the first bad decision is visible."),
            ("Probe distractors without gaming them", "Vary one failure mode at a time: wrong part number, old revision, copied note, negated sentence, unit mismatch or unauthorized source. Include a genuinely unanswerable case. A model might pass a simple value swap but fail when the old value appears in a top-ranked stale document. Keep distractor language natural and the target question unchanged. Avoid test cases whose answer is visible in the file name or test label. [[retrieval-ai/hard-negative-mining-and-false-negative-audits|Hard-negative audits]] keep distractors from accidentally becoming valid answers."),
            ("Report stability and sensitivity", "The system should remain stable when irrelevant text changes and change when the supporting fact changes. Measure candidate recall, supported top-one answer, contradiction detection and abstention for each perturbation type. Compare against the same corpus snapshot and model versions. A pass rate that averages easy no-op edits with hard entity swaps obscures the actual weakness; keep per-perturbation slices. Review a sample of failures manually to confirm that the synthetic edit did not create an unintended second answer."),
        ],
        "code": '''from dataclasses import dataclass, replace

@dataclass(frozen=True)
class EvidenceRecord:
    passage_id: str
    entity_id: str
    revision: str
    value_kpa: int

def answer_limit(records: list[EvidenceRecord], entity_id: str,
                 revision: str) -> int | None:
    matches = [record.value_kpa for record in records
               if record.entity_id == entity_id and record.revision == revision]
    if len(matches) > 1:
        raise ValueError("conflicting eligible evidence")
    return matches[0] if matches else None

original = EvidenceRecord("manual-p47-r4", "pump-p47", "r4", 83)
distractor = EvidenceRecord("manual-p48-r4", "pump-p48", "r4", 83)
edited = replace(original, value_kpa=67)
assert answer_limit([original, distractor], "pump-p47", "r4") == 83
assert answer_limit([edited, distractor], "pump-p47", "r4") == 67
assert answer_limit([distractor], "pump-p47", "r4") is None''',
        "cost": "Creating a synthetic variant costs O(C) for C copied records and running the baseline scan costs O(C) time with O(K) match space. The real expense is repeated retrieval and answer generation across perturbation suites. Keep fixtures small and deterministic for every commit, then run a wider judged sample before a release. Store only synthetic values in test logs so a reviewer cannot confuse them with production facts.",
        "mistakes": ["Changing a value without changing its expected answer and revision label.", "Leaving an eligible original passage that makes the edited answer ambiguous.", "Calling a memorized correct answer a retrieval success when evidence never entered context.", "Averaging all perturbation types into one score that hides a severe slice failure."],
        "drill": "Construct 47 synthetic question variants across value, entity, negation, date and permission edits. Record the first pipeline stage that loses the required evidence and whether the final answer changes only when it should.",
        "related": [prefix + "retrieval-release-evaluation-and-slice-gates", prefix + "retrieval-traces-and-incident-debugging", prefix + "hard-negative-mining-and-false-negative-audits", prefix + "claim-level-citation-and-support-checks"],
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
        "featured": False, "sort_order": 8449 + offset, "status": "published",
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
    row["data"]["modules"].append({"title": "Visual evidence, event windows and test probes", "lessons": new_paths})
    row["body"] += '<h2>Visual evidence, event windows and test probes</h2><ul>' + ''.join(
        f'<li>{link(target)}</li>' for target in new_paths) + '</ul>'
    row["updated_at"] = stamp
    changed.append(row)

incoming = {
    prefix + "multimodal-retrieval-and-asset-identity": [new_paths[0]],
    prefix + "temporal-retrieval-as-of-validity-and-conflicts": [new_paths[1]],
    prefix + "multilingual-retrieval-and-entity-preservation": [new_paths[2]],
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
