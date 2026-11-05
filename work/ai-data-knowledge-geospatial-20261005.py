"""Extend AI & Data local previews with knowledge graphs and geospatial analytics."""
import datetime
import html
import json
from pathlib import Path
import re
import uuid

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
rows = [row for row in rows if not row['path'].startswith(('knowledge-graphs/', 'geospatial-analytics/'))]
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
lessons = []

def add(path, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path=path, title=title, summary=summary, sections=sections,
                        code=code, cost=cost, mistakes=mistakes, related=related))

add('knowledge-graphs/entity-identity-and-relation-schema',
    'Knowledge-graph contract: entity identity, relations and claims',
    'A knowledge graph stores typed claims about identified entities; its value depends on stable identity and precise relation meaning.', [
    ('Define the entity boundary', 'AI Trove may represent a lesson, concept, author and course as separate entity types. A lesson title is not its identity because titles change and duplicates exist. Use a stable internal key and a redirect or retirement record when content moves. [[graph-machine-learning/entity-edge-and-snapshot-contract|Graph snapshot rules]] still matter, but a knowledge graph also needs explicit semantics for every claim.'),
    ('Name directed predicates', 'A lesson teaches a concept; a concept is required by a lesson. Those statements point in different directions and should not be stored as one anonymous edge. Define allowed source and target types for each predicate. A page linking to another page does not prove that it teaches the linked concept, so editorial relationships and navigation links belong in separate predicates.'),
    ('Make claims reviewable', 'Each relationship needs a claim ID, evidence record, extraction or editorial method, created time and current status. A machine-extracted claim can be provisional until reviewed. Distinguish absent evidence from a false claim. [[data-engineering/source-contract-and-raw-landing|Raw input lineage]] lets an editor find the exact page version that supported a relation.'),
    ('Exercise a fixture', 'Lesson L-47 teaches concept C-8 and requires C-3. Rename L-47, then verify its ID and claims remain stable. Add a second lesson with the old title and ensure it does not inherit L-47’s edges. Reverse the requires edge and confirm a schema check rejects the type or direction if it no longer matches the declared relation.')],
    'def valid_claim(claim, allowed_relations):\n    relation = allowed_relations.get(claim["predicate"])\n    return relation is not None and (claim["subject_type"], claim["object_type"]) == relation',
    'A predicate validation is O(1) expected time with a relation registry. Validating N claims is O(N), while identity lookup and claim history storage scale with the number of entities, versions and evidence records.',
    ['Do not use a mutable title as an entity key.', 'Do not treat a navigation link as proof of a semantic relation.', 'Do not collapse unknown and false claims into the same state.'],
    ['knowledge-graphs/entity-resolution-and-aliases','knowledge-graphs/provenance-time-and-retraction','graph-machine-learning/entity-edge-and-snapshot-contract','data-engineering/source-contract-and-raw-landing'])

add('knowledge-graphs/entity-resolution-and-aliases',
    'Entity resolution: aliases, merge decisions and reversible identity',
    'Entity resolution joins records referring to the same real entity, but a false merge can corrupt every downstream path.', [
    ('Separate candidates from decisions', 'Two lesson pages with similar names may describe different topics. Generate candidate matches from normalized titles, aliases and subject context, then require stronger evidence such as canonical path history or shared stable ID to merge. Store match score, rule version and reviewer decision. [[knowledge-graphs/entity-identity-and-relation-schema|The identity contract]] must say whether a split or merge changes public paths and historical claims.'),
    ('Keep aliases typed', 'An alias may be a former title, abbreviation, spelling variant or disambiguation label. Do not let an alias become a unique key without checking collisions. A concept named “Java streams” can refer to a language API, while another document uses “stream” for event processing. Subject and relation context can prevent a false match.'),
    ('Make merges reversible', 'Preserve source entity IDs and redirects when merging. If a reviewer later finds the merge wrong, claims must be separable by original evidence rather than copied irreversibly to the surviving node. Track the time each identity decision became active so a historical graph snapshot can be reproduced. [[data-engineering/cdc-replay-and-deletes|Replay and correction rules]] apply to identity events too.'),
    ('Test the collision', 'Create lessons “Streaming in Java” and “Streaming Analytics,” both aliased as “streams.” A title-only resolver would merge them. Require subject and canonical path context, then keep them separate. Add a genuine renamed lesson with two old paths and confirm it resolves to one entity while retaining the old identifiers as audit links.')],
    'def alias_candidates(alias_rows, query_alias, subject):\n    normalized = query_alias.casefold().strip()\n    return [row["entity_id"] for row in alias_rows\n            if row["alias"].casefold().strip() == normalized\n            and row["subject"] == subject]',
    'A scan of A aliases costs O(A) time and O(M) output space for M candidates. Indexing normalized alias plus subject makes lookup faster, but collision review and reversible merge history remain essential.',
    ['Do not merge entities on title similarity alone.', 'Do not assume an alias is globally unique.', 'Do not discard source IDs and evidence during a merge.'],
    ['knowledge-graphs/entity-identity-and-relation-schema','knowledge-graphs/constraint-validation-and-quality','data-engineering/cdc-replay-and-deletes','natural-language-processing/nlp-tutorial'])

add('knowledge-graphs/provenance-time-and-retraction',
    'Knowledge-graph provenance: claim time, evidence and retraction',
    'A graph claim must carry enough history to explain when it was true, when it was known and why it should be trusted.', [
    ('Keep two times', 'A lesson can begin requiring a concept on September 1, while an editor records the change on September 4. Effective time and recorded time answer different questions. A recommendation made on September 2 cannot use a claim recorded on September 4, even if the claim is later backdated. [[time-series/lag-features-and-future-leakage|Availability boundaries]] also apply to graph facts.'),
    ('Attach evidence', 'Store the exact lesson revision, extraction span or editorial decision that supports each claim. A path to a page is insufficient after that page changes. Evidence may be a source record or review ticket ID inside the content system; public tutorial prose need not expose internal evidence. A confidence score should identify the extractor version and calibration set if it controls automatic publication.'),
    ('Retract without erasing', 'When a prerequisite is removed, mark the earlier claim inactive with a retraction event and reason. Do not delete it from historical snapshots used to reconstruct past recommendations. If the original claim was erroneous, record a correction that distinguishes bad historical knowledge from a legitimate curriculum change. [[feature-stores/backfill-delete-and-publication|Versioned publication]] prevents half-updated graphs from reaching readers.'),
    ('Rehearse a correction', 'Claim C-47 becomes effective at minute 120, is recorded at 150, and is retracted at 240. A decision at minute 130 must not see it; one at 180 may; one at 260 must not. Add an evidence revision at 200 and verify the claim’s support points to the correct page version for each decision.')],
    'def visible_claims(claim_rows, decision_minute):\n    return [claim for claim in claim_rows\n            if claim["recorded_minute"] <= decision_minute\n            and claim["effective_minute"] <= decision_minute\n            and (claim["retracted_minute"] is None\n                 or claim["retracted_minute"] > decision_minute)]',
    'A scan of C claims costs O(C) time and O(V) output space for V visible claims. Indexed temporal partitions reduce repeated query work, while immutable claim events increase storage in exchange for reproducibility.',
    ['Do not backdate a newly recorded claim into an old prediction snapshot.', 'Do not erase retracted evidence needed for audit.', 'Do not confuse an erroneous claim with a relationship that later changed.'],
    ['knowledge-graphs/entity-identity-and-relation-schema','knowledge-graphs/query-paths-and-answer-boundaries','time-series/lag-features-and-future-leakage','feature-stores/backfill-delete-and-publication'])

add('knowledge-graphs/constraint-validation-and-quality',
    'Graph validation: type constraints, cardinality and quality gates',
    'A graph load should be rejected when its claims violate declared relation types, identity rules or required evidence fields.', [
    ('Validate shape rules', 'A teaches relation can require a lesson subject and concept object. A published lesson may need exactly one canonical subject, while a concept can have many teaching lessons. Express required properties, allowed types and cardinality in a versioned schema. Some constraints are closed-world editorial rules; others should not be mistaken for universal facts about the world.'),
    ('Check contradictions', 'Two prerequisites may form a cycle even if each claim is individually well typed. A cycle might be permitted for loose “related to” edges but invalid for strict learning order. Identify which predicates require acyclicity and run those checks after ingestion. [[graph-machine-learning/graph-construction-and-degree-skew|Relation direction]] affects both validation and downstream traversal.'),
    ('Measure quality by source', 'Report missing evidence, duplicate claim IDs, invalid targets, orphan entities and unresolved aliases by ingestion source. A high overall pass rate can hide one newly added feed whose claims are nearly all wrong. Quarantine bad claims rather than silently dropping them; preserve the reason and record count for reconciliation with input batches.'),
    ('Test publication', 'Insert a teaches claim from a learner node to a concept node, a duplicate prerequisite ID and a strict-prerequisite cycle among three lessons. The type and duplicate checks should fail before publication; the cycle check should isolate the loop. A clean batch should switch into the serving snapshot only after counts and required relationships reconcile.')],
    'def invalid_typed_claims(claim_rows, allowed_relations):\n    return [claim["claim_id"] for claim in claim_rows\n            if allowed_relations.get(claim["predicate"])\n            != (claim["subject_type"], claim["object_type"])]',
    'Type validation costs O(C) expected time for C claims. Cycle checks on a selected directed subgraph cost O(V + E) time and space; run them only for predicates where a cycle is actually forbidden.',
    ['Do not treat every relation as if it had the same cardinality.', 'Do not publish a batch with silent invalid-claim loss.', 'Do not apply prerequisite cycle rules to ordinary related-to links.'],
    ['knowledge-graphs/entity-resolution-and-aliases','knowledge-graphs/query-paths-and-answer-boundaries','graph-machine-learning/graph-construction-and-degree-skew','data-engineering/quality-quarantine-and-reconciliation'])

add('knowledge-graphs/query-paths-and-answer-boundaries',
    'Graph queries: bounded paths, freshness and evidence-backed answers',
    'A graph query should specify relation semantics, path limits, snapshot time and evidence returned with each answer.', [
    ('Ask a precise question', '“Which lessons prepare a learner for graph models?” can mean direct prerequisites, all transitive prerequisites or lessons teaching required concepts. Those queries are not equivalent. Fix the starting entity, allowed predicates, edge direction and maximum depth. [[knowledge-graphs/entity-identity-and-relation-schema|Typed relations]] prevent a navigation link from entering a prerequisite answer.'),
    ('Bound traversal', 'A concept hub can fan out to thousands of lessons. Traverse only whitelisted predicates and cap depth and returned candidates before ranking. Record why each result was reached, including claim IDs and intermediate entities. A path that exists in the graph is not necessarily a recommended learning order; eligibility, level and freshness still need separate filters.'),
    ('Use a consistent snapshot', 'A query that reads half an updated graph can combine new lesson nodes with old prerequisite claims. Serve a versioned graph snapshot, and apply immediate withdrawal gates to retired pages. [[knowledge-graphs/provenance-time-and-retraction|Claim history]] determines which edges were visible at the question time. Cache keys must include graph version and query policy.'),
    ('Inspect the result', 'For lesson L-47, return two direct prerequisite lessons and one two-hop ancestor. Show the relation path and supporting claim ID for each. Add a high-degree “all concepts” hub and verify it does not flood the answer. Retract one edge and confirm the new snapshot removes its path while the historical snapshot remains reproducible.')],
    'def bounded_prerequisites(start_id, adjacency, max_depth):\n    frontier = {start_id}\n    visited = {start_id}\n    for _ in range(max_depth):\n        next_frontier = set()\n        for lesson_id in frontier:\n            next_frontier.update(adjacency.get(lesson_id, ()))\n        next_frontier -= visited\n        visited.update(next_frontier)\n        frontier = next_frontier\n    visited.remove(start_id)\n    return visited',
    'A bounded traversal visits at most O(V + E) nodes and edges in the reachable subgraph and stores O(V) IDs. Limit depth, fanout and result count for predictable latency on high-degree nodes.',
    ['Do not return a path without its allowed relation meaning.', 'Do not run unbounded traversal over high-degree hubs.', 'Do not combine nodes and claims from different snapshots.'],
    ['knowledge-graphs/provenance-time-and-retraction','knowledge-graphs/graph-grounded-retrieval-and-evaluation','graph-machine-learning/graph-serving-and-cold-nodes','retrieval-ai/retrieval-ai-tutorial'])

add('knowledge-graphs/graph-grounded-retrieval-and-evaluation',
    'Graph-grounded retrieval: candidate recall and unsupported claims',
    'A graph can guide retrieval, but a generated answer still needs evidence for every factual relationship it states.', [
    ('Separate graph from text', 'The graph is a curated index of entity relationships, while lesson passages carry explanations and qualifications. Use a recognized entity to retrieve graph neighbors, then fetch the exact supporting lesson revisions. An extracted edge without verified evidence should not be presented as a fact merely because it appears in a path. [[retrieval-ai/retrieval-ai-tutorial|Retrieval evaluation]] should check candidate supply before judging answer wording.'),
    ('Measure candidate coverage', 'If the correct lesson or evidence claim is absent from the graph, a graph-only retriever cannot recover it. Track entity-linking accuracy, graph candidate recall and passage recall separately. Compare with a text-only baseline; graph expansion can improve disambiguation but may also introduce irrelevant neighbors. Keep a fallback when a new lesson has no graph edges.'),
    ('Audit answer support', 'For each answer statement, record the claim ID, evidence revision and retrieved passage that supports it. If the passage contradicts an older edge, abstain or route to review instead of inventing a reconciliation. [[knowledge-graphs/provenance-time-and-retraction|Claim timing]] matters when a current answer and a historical answer refer to different curriculum versions.'),
    ('Test a conflict', 'Create a graph edge saying lesson A requires concept C, then remove that prerequisite in the latest lesson revision while leaving an old evidence span indexed. A current answer should not assert the requirement. The evaluation should identify stale evidence, not treat the existence of a graph path as a successful grounded answer.')],
    'def supported_claim_ids(answer_claim_ids, evidence_by_claim):\n    return [claim_id for claim_id in answer_claim_ids\n            if claim_id in evidence_by_claim\n            and evidence_by_claim[claim_id]["reviewed"]\n            and evidence_by_claim[claim_id]["current"]]',
    'Checking A proposed claims is O(A) expected time with an evidence index and O(S) output space for S supported claims. Full retrieval adds graph traversal, passage search and version checks; measure each stage independently.',
    ['Do not call a graph path sufficient evidence for a generated statement.', 'Do not hide a missing graph candidate behind fluent answer text.', 'Do not use stale passage revisions for current claims.'],
    ['knowledge-graphs/query-paths-and-answer-boundaries','knowledge-graphs/lesson-prerequisite-graph-project','retrieval-ai/retrieval-ai-tutorial','graph-machine-learning/graph-metrics-and-subgroup-coverage'])

add('knowledge-graphs/lesson-prerequisite-graph-project',
    'Project: publish an evidence-backed lesson knowledge graph',
    'Build a versioned lesson-concept graph that rejects invalid claims and explains every prerequisite path it serves.', [
    ('Create the schema', 'Define lesson and concept entities with immutable IDs, aliases, teaches and requires predicates, allowed source and target types, and a strict prerequisite acyclicity rule. Add claim IDs, effective and recorded times, evidence revision IDs and review status. [[knowledge-graphs/entity-identity-and-relation-schema|The claim contract]] should make a title change harmless and a false merge reversible.'),
    ('Ingest an adversarial fixture', 'Include a renamed lesson, two ambiguous “streams” aliases, duplicate claim delivery, an unreviewed extracted edge, a retracted prerequisite and a three-lesson cycle. Resolve identities with context, quarantine schema violations and preserve all accepted claim history. Produce a validation report with exact counts and reasons rather than dropping difficult rows.'),
    ('Serve bounded answers', 'Implement direct and two-hop prerequisite lookup against a versioned snapshot. Return lesson IDs, relation path, claim IDs and current evidence revision. Apply a withdrawal gate to retired pages. Compare graph candidate recall with a text-only lesson search on a small judged query set, including a new isolated lesson that needs a fallback.'),
    ('Submit a release packet', 'Provide schema, raw fixture, identity decisions, claim ledger, validation output, snapshot manifest, path traces and an error review. Rebuild the historical graph at a prior time and explain why a retracted edge was visible then but not now. A reviewer should reconstruct one served answer from recorded claims and passage versions.')],
    'def accepted_claims(claim_rows, relation_types):\n    return [claim for claim in claim_rows\n            if claim["reviewed"] and relation_types.get(claim["predicate"])\n            == (claim["subject_type"], claim["object_type"])\n            and not claim["withdrawn"]]',
    'Filtering C claims costs O(C) expected time and O(A) output space for A accepted claims. Indexing, cycle validation and historical snapshots add work, but they make answer paths and corrections reproducible.',
    ['Do not publish unreviewed extracted claims as facts.', 'Do not erase retracted claim history.', 'Do not serve a withdrawn lesson from an old graph snapshot.'],
    ['knowledge-graphs/constraint-validation-and-quality','knowledge-graphs/graph-grounded-retrieval-and-evaluation','graph-machine-learning/lesson-prerequisite-graph-project','data-engineering/backfill-publication-boundary'])

add('geospatial-analytics/location-unit-and-coordinate-contract',
    'Geospatial data contract: location units, coordinates and accuracy',
    'A location record needs a known coordinate reference, geometry type, observation time and uncertainty before distance or containment has meaning.', [
    ('Choose the decision unit', 'An operations team may estimate delivery coverage for pickup points. One row can represent a pickup site, delivery event or service zone; joining them without declaring grain multiplies counts. Give each site a stable ID and record whether coordinates describe an entrance, centroid or approximate neighborhood. [[data-science/dataset-grain-and-join-cardinality|Dataset grain]] prevents one busy site from silently dominating a regional report.'),
    ('Validate coordinates', 'Longitude and latitude have different valid ranges and order. A pair (77.25, 28.61) means something different when reversed. Record coordinate reference system and axis order for every source, plus whether values are degrees or projected linear units. Never compute kilometer distances from degree differences. A missing coordinate is not the zero-degree point.'),
    ('Represent accuracy', 'A geocoded address may be accurate to a building, street or city. Store the accuracy class and collection method. An event with a 900-meter uncertainty radius should not be assigned confidently to a narrow delivery zone near its boundary. [[geospatial-analytics/geometry-validation-and-spatial-joins|Spatial joins]] need a policy for boundary and uncertain points rather than a single yes/no flag.'),
    ('Test the contract', 'Create pickup site P-47 at longitude 77.25, latitude 28.61, another with swapped axes, and a third with no coordinates. Reject the swapped record through range or region checks, and preserve the missing record for quality reporting. Add two historical site moves and verify an older delivery joins to the site location valid at its event time.')],
    'def valid_lon_lat(longitude, latitude):\n    return (longitude is not None and latitude is not None\n            and -180 <= longitude <= 180 and -90 <= latitude <= 90)',
    'Coordinate-range validation is O(1) per point and O(N) for N records. Range checks cannot detect every swapped pair because both values may remain legal; region plausibility and source metadata are additional safeguards.',
    ['Do not treat degrees as kilometers.', 'Do not assign a missing coordinate to longitude and latitude zero.', 'Do not assume an address geocode identifies the exact entrance.'],
    ['geospatial-analytics/geometry-validation-and-spatial-joins','geospatial-analytics/distance-and-nearest-service','data-science/dataset-grain-and-join-cardinality','time-series/observation-calendar-and-missing-periods'])

add('geospatial-analytics/geometry-validation-and-spatial-joins',
    'Spatial joins: polygons, boundaries and duplicate matches',
    'A point-in-zone join must handle invalid polygons, shared borders, overlaps and the intended ownership rule.', [
    ('Validate geometry first', 'A zone polygon may self-intersect, omit a ring or use a different coordinate reference from the points. Check geometry validity and transform both sides into a compatible reference before containment tests. A bounding box is only a quick candidate filter; it can include points outside an irregular polygon. [[geospatial-analytics/location-unit-and-coordinate-contract|The coordinate contract]] should determine how transformations are recorded.'),
    ('Choose a border policy', 'A pickup point on the shared edge of two zones can match both under an intersects predicate, neither under strict within, or one under a declared tie-break. Specify the rule based on the business decision. Do not let database row order decide ownership. Keep an unresolved state if uncertainty or overlapping zones prevents a defensible unique assignment.'),
    ('Control duplicate rows', 'One point joined to three overlapping polygons creates three output rows and can inflate delivery totals. Preserve point ID and count matches before aggregation. For coverage reporting, decide whether overlap means multiple eligible zones or a data-quality defect. [[data-engineering/quality-quarantine-and-reconciliation|Reconciliation]] should compare unique input event IDs with unique output event IDs.'),
    ('Use a fixture', 'Create two square zones sharing one edge, one point in the first zone, one on the common edge and one outside both. Verify the declared border rule for each. Add a self-intersecting polygon and quarantine it. A report should show unmatched and multi-match counts, not silently assign every point to the first returned polygon.')],
    'def bounding_box_candidates(points, bounds_by_zone):\n    matches = []\n    for point in points:\n        for zone_id, (west, south, east, north) in bounds_by_zone.items():\n            if west <= point["longitude"] <= east and south <= point["latitude"] <= north:\n                matches.append((point["point_id"], zone_id))\n    return matches',
    'The fixture broad-phase scan costs O(P times Z) time for P points and Z zones, with O(M) output for M candidate pairs. An index can reduce candidate tests; exact polygon predicates must still follow the broad-phase filter.',
    ['Do not use a bounding-box candidate as a confirmed polygon match.', 'Do not let overlapping polygons multiply event counts silently.', 'Do not assign a border point by arbitrary database order.'],
    ['geospatial-analytics/location-unit-and-coordinate-contract','geospatial-analytics/spatial-index-and-serving-freshness','data-engineering/quality-quarantine-and-reconciliation','data-visualization/distribution-and-outlier-displays'])

add('geospatial-analytics/distance-and-nearest-service',
    'Distance and nearest service: metric choice before optimization',
    'The nearest site under straight-line distance may not be the fastest or eligible service point for a real trip.', [
    ('Choose a metric', 'For rough regional filtering, great-circle distance between longitude and latitude points is useful. A delivery-time promise needs a road or transit network plus current service constraints. State units, Earth approximation and whether the distance is from site centroid or entrance. [[geospatial-analytics/location-unit-and-coordinate-contract|Coordinate accuracy]] can dominate the precision of any distance formula.'),
    ('Filter eligibility first', 'A pickup site may be closed, at capacity or outside the customer’s service area. Remove ineligible sites before ranking by distance. If capacity updates arrive late, log the snapshot used for the decision. A nearest result with no available slots is not a useful recommendation. Separate candidate recall from final ranking as in [[recommendation-systems/candidate-retrieval-and-eligibility|candidate retrieval]].'),
    ('Avoid degree arithmetic', 'Longitude degrees cover different physical distances at different latitudes. Squared Euclidean distance on raw degree values is not a reliable kilometer estimate. Project to an appropriate local coordinate system for planar work or use a spherical formula for broad distances. Near the antimeridian, naive longitude subtraction can take the long way around.'),
    ('Check a small case', 'Customer C-47 is near two pickup sites: one is 0.8 kilometers away across a river, another is 1.4 kilometers away by straight line but connected by road. A straight-line filter can nominate both; travel-time ranking should prefer the reachable site when that is the decision target. The final trace should show metric and network snapshot.')],
    'from math import asin, cos, radians, sin, sqrt\n\ndef great_circle_km(lat_a, lon_a, lat_b, lon_b):\n    lat_a, lon_a, lat_b, lon_b = map(radians, (lat_a, lon_a, lat_b, lon_b))\n    delta_lat = lat_b - lat_a\n    delta_lon = lon_b - lon_a\n    arc = sin(delta_lat / 2) ** 2 + cos(lat_a) * cos(lat_b) * sin(delta_lon / 2) ** 2\n    return 12742 * asin(min(1, sqrt(arc)))',
    'One great-circle calculation is O(1) time and space; scoring N eligible sites is O(N). Spatial indexes reduce candidate search, while road-network shortest paths add graph traversal and time-dependent edge costs.',
    ['Do not measure kilometers by subtracting latitude and longitude degrees.', 'Do not rank closed sites and filter them afterward.', 'Do not present straight-line distance as travel time.'],
    ['geospatial-analytics/location-unit-and-coordinate-contract','geospatial-analytics/spatial-index-and-serving-freshness','recommendation-systems/candidate-retrieval-and-eligibility','graph-machine-learning/graph-construction-and-degree-skew'])

add('geospatial-analytics/spatial-index-and-serving-freshness',
    'Spatial serving: indexes, snapshot consistency and stale locations',
    'A location service needs indexed candidate retrieval, explicit freshness and a safe response to moved or withdrawn sites.', [
    ('Index the right geometry', 'Index site points or zone geometries in the same coordinate reference used for the query predicate. A spatial index narrows candidates; it does not replace the exact distance or containment check. A radius query expressed in meters against degree-based geometry can be wrong unless the database type or projection gives the units intended. [[geospatial-analytics/distance-and-nearest-service|The distance contract]] determines the predicate.'),
    ('Version the snapshot', 'A site move changes location and may alter zone membership. Publish a coherent version of site coordinates, operating status and zone boundaries, then log that version with every response. A partial refresh can combine the new site location with an old boundary map. [[data-engineering/backfill-publication-boundary|Atomic publication]] keeps the answer reproducible.'),
    ('Gate withdrawal immediately', 'A closed site should leave results before a large spatial index rebuild finishes. Apply an eligibility filter at serving time and rebuild the index under a versioned process. If the location is stale, return a qualified result or decline the location-sensitive action according to the workflow. Do not silently reuse an old coordinate as current.'),
    ('Rehearse a swap', 'Serve index version 47 while preparing 48. Move site P-47 across a zone border, close site P-48 and update one boundary. Verify every response logs one coherent version and never returns the closed site. If version 48 fails geometry checks, keep version 47 but retain the closure gate.')],
    'def eligible_site_candidates(site_rows, current_version):\n    return [site for site in site_rows\n            if site["snapshot_version"] == current_version and site["open"]\n            and site["latitude"] is not None and site["longitude"] is not None]',
    'Filtering S sites is O(S) time and O(E) output memory for E eligible sites. An indexed service can reduce per-request candidate work, but index builds, stale-key checks and atomic version swaps add operational cost.',
    ['Do not mistake an index hit for an exact spatial match.', 'Do not mix coordinates and boundaries from different snapshots.', 'Do not return a closed site from a stale index.'],
    ['geospatial-analytics/geometry-validation-and-spatial-joins','geospatial-analytics/spatial-holdout-and-leakage','data-engineering/backfill-publication-boundary','feature-stores/online-materialization-and-staleness'])

add('geospatial-analytics/spatial-holdout-and-leakage',
    'Geospatial evaluation: spatial holdouts, leakage and transfer',
    'Nearby records often share conditions, so a random row split can overstate how well a spatial model works in a new area.', [
    ('Split by the deployment question', 'If a delivery-delay model will serve a new district, hold out entire districts or coherent geographic blocks. If it will predict future weeks in known districts, use a time split with enough gap to prevent late outcomes leaking. [[machine-learning/group-and-time-validation|Group and time validation]] can be combined when both geography and time change at deployment.'),
    ('Watch overlap and proxies', 'Adjacent cells may share one road closure, weather event or service center. A model that sees neighboring cells in training can memorize that event. Location IDs, postal codes and coordinates may act as proxies for the held-out area; decide whether those features will be available and meaningful in the new area. Keep a spatial buffer when the test requires independence from nearby training points.'),
    ('Report coverage', 'Measure error by region, density, boundary distance and site age, with counts. A pooled score dominated by dense urban sites says little about remote locations. Track how often candidate retrieval excludes the true service point before evaluating travel-time ranking. [[geospatial-analytics/spatial-index-and-serving-freshness|Index freshness]] can affect both coverage and score.'),
    ('Use a fixture', 'Create sites in three districts and deliveries over four weeks. Train on the first two districts and test on the third, then compare with a random-row split. A large random-split advantage should trigger an overlap investigation rather than a launch claim. Include a border site whose nearest service point lies in another district to test candidate eligibility.')],
    'def held_out_regions(records, test_region_ids):\n    test_regions = set(test_region_ids)\n    train = [row for row in records if row["region_id"] not in test_regions]\n    test = [row for row in records if row["region_id"] in test_regions]\n    return train, test',
    'Partitioning N rows is O(N + R) expected time and O(N + R) memory for R held-out region IDs. Spatial buffer calculations and repeated folds add cost; that cost is justified when random splits answer the wrong deployment question.',
    ['Do not use a random row split for a new-region claim without an overlap check.', 'Do not report only dense-region performance.', 'Do not ignore true candidates missing from the spatial index.'],
    ['geospatial-analytics/location-unit-and-coordinate-contract','geospatial-analytics/aggregation-and-location-privacy','machine-learning/group-and-time-validation','data-visualization/uncertainty-and-small-sample-display'])

add('geospatial-analytics/aggregation-and-location-privacy',
    'Spatial aggregation: exposure, unstable cells and location privacy',
    'A location heatmap should distinguish opportunity from count and avoid disclosing sensitive patterns through tiny cells.', [
    ('Choose the aggregation unit', 'A delivery count by grid cell is not a service-rate measure if cells contain different numbers of active customers. Include exposure such as eligible orders or active sites when interpreting rates. Preserve event identity before assigning cells so retries do not inflate hot spots. [[data-visualization/distribution-and-outlier-displays|Distribution displays]] should show counts and rate denominators alongside color.'),
    ('Handle sparse cells', 'One delayed delivery in a cell with two orders yields a 50 percent delay rate, but that number is unstable. Show support and uncertainty or aggregate to a broader region when the task allows it. Do not smooth a sparse cell into a confident local estimate without showing the smoothing rule. A cell with no observed events can mean zero activity or missing telemetry.'),
    ('Protect location traces', 'Fine-grained repeated coordinates can reveal a person’s routine even without a name. Limit precision and retention to the task, apply access controls, and review whether public aggregate releases need a formal privacy mechanism. [[privacy-aware-ml/threat-model-and-data-minimization|A privacy threat model]] must identify who can see the map and how repeated releases combine. A minimum-count rule alone is not a complete guarantee.'),
    ('Test a release', 'Build cells A and B with 47 and 3 eligible orders. Give B one delayed delivery and a sensitive single address. A public report should not present B’s exact point or 33.3 percent rate as a stable neighborhood fact. Record the aggregation and suppression decision, plus whether the same individual could be isolated across weekly map releases.')],
    'def cell_delay_rates(cell_rows):\n    rates = {}\n    for row in cell_rows:\n        if row["eligible_orders"] > 0:\n            rates[row["cell_id"]] = row["delayed_orders"] / row["eligible_orders"]\n    return rates',
    'Computing C cell rates costs O(C) time and O(C) output space. Rendering many spatial cells adds map and query cost; privacy review also needs to account for repeated releases, not only one static map.',
    ['Do not compare raw counts when cell exposure differs sharply.', 'Do not interpret a tiny denominator as a stable rate.', 'Do not claim coarse cells or a count threshold alone guarantee privacy.'],
    ['geospatial-analytics/spatial-holdout-and-leakage','geospatial-analytics/pickup-coverage-project','privacy-aware-ml/threat-model-and-data-minimization','data-visualization/uncertainty-and-small-sample-display'])

add('geospatial-analytics/pickup-coverage-project',
    'Project: audit pickup-site coverage across changing zones',
    'Build a versioned spatial coverage service and evaluate it on a held-out district with boundary and stale-site cases.', [
    ('Prepare the geometry packet', 'Create pickup sites with stable IDs, longitude and latitude, coordinate reference, accuracy class, open status and effective time. Create zone polygons with version IDs, including two that share a border, one overlap and one invalid polygon. Add deliveries with immutable event IDs and one late location correction. [[geospatial-analytics/location-unit-and-coordinate-contract|The coordinate contract]] determines which records can enter spatial joins.'),
    ('Build the coverage path', 'Validate geometry and transform to a suitable reference for exact zone tests. Use a bounding box only as a candidate filter, then apply an exact predicate with a documented border rule. Filter closed sites before ranking. Compare straight-line candidate distance with a travel-time label if available; do not call the former a route estimate.'),
    ('Evaluate transfer', 'Hold out one district and a later week, reporting candidate recall, assignment conflicts, unmatched deliveries and distance error by region and boundary proximity. Compare with a random-row split to expose spatial leakage. Record support for sparse cells and avoid releasing fine-grained traces in the public summary. [[geospatial-analytics/spatial-holdout-and-leakage|The holdout design]] should match the deployment claim.'),
    ('Submit a serving trace', 'Publish a coherent version of sites and zones, then move one site and close another while the next index builds. Demonstrate that no response mixes versions or returns the closed site. Deliver raw fixture, validation report, query plan, index manifest, evaluation packet and one border-point trace showing the exact tie-break decision.')],
    'def unique_open_site_ids(site_rows, snapshot_version):\n    return {site["site_id"] for site in site_rows\n            if site["snapshot_version"] == snapshot_version\n            and site["open"] and site["latitude"] is not None\n            and site["longitude"] is not None}',
    'The fixture filter costs O(S) time and O(U) space for S site rows and U unique open sites. Exact spatial queries need geometry validation and an index; serving also requires snapshot and withdrawal gates.',
    ['Do not equate a bounding-box hit with polygon membership.', 'Do not rank closed sites or mix snapshot versions.', 'Do not claim new-region quality from only a random-row split.'],
    ['geospatial-analytics/geometry-validation-and-spatial-joins','geospatial-analytics/spatial-index-and-serving-freshness','geospatial-analytics/spatial-holdout-and-leakage','data-engineering/backfill-publication-boundary'])

assert len(lessons) == 14
assert len({item['path'] for item in lessons}) == len(lessons)
titles = {path: row['title'] for path, row in by_path.items()}
titles.update({item['path']: item['title'] for item in lessons})

def prose(value):
    return re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',
                  lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                  html.escape(value))

def links(paths):
    return '<ul>' + ''.join('<li><a href="/' + path + '">' + html.escape(titles[path]) + '</a></li>' for path in paths) + '</ul>'

def article_body(item):
    parts = ['<p>' + html.escape(item['summary']) + '</p>']
    for heading, paragraph in item['sections']:
        parts.extend(('<h2>' + html.escape(heading) + '</h2>', '<p>' + prose(paragraph) + '</p>'))
    parts.extend(('<h2>Implementation</h2>', '<pre><code class="language-python">' + html.escape(item['code']) + '</code></pre>',
                  '<h2>Performance and operating cost</h2>', '<p>' + html.escape(item['cost']) + '</p>',
                  '<h3>Common Mistakes</h3>', '<ul>' + ''.join('<li>' + html.escape(mistake) + '</li>' for mistake in item['mistakes']) + '</ul>',
                  '<h2>Read next</h2>', links(item['related'])))
    return ''.join(parts)

def make_row(path, title, summary, body, entry_type, subject, section_path, root_path, order, metadata):
    return dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://aitrove.in/' + path)), type=entry_type,
                path=path, title=title, summary=summary, body=body, category='AI & Data',
                subject=subject, difficulty='Intermediate', tags=['ai-data', subject], potd_date=None,
                featured=False, sort_order=order, status='published', published_at=stamp,
                created_at=stamp, updated_at=stamp,
                data={'subject_root':root_path, 'section_path':section_path,
                      'content_format':'html', 'seo_ready':True, **metadata})

subject_config = {
 'knowledge-graphs': {
     'root':'knowledge-graphs/knowledge-graphs-tutorial', 'name':'Knowledge Graphs',
     'summary':'Publish typed claims with stable identity, reversible resolution, evidence history, validation and bounded graph queries.',
     'groups':[('Model and ingest', ['entity-identity-and-relation-schema','entity-resolution-and-aliases','provenance-time-and-retraction']),
               ('Validate and answer', ['constraint-validation-and-quality','query-paths-and-answer-boundaries','graph-grounded-retrieval-and-evaluation'])],
     'project':'lesson-prerequisite-graph-project',
     'foundation':['graph-machine-learning/graph-machine-learning-tutorial','data-engineering/data-engineering-tutorial'],
     'neighbors':['retrieval-ai/retrieval-ai-tutorial','geospatial-analytics/geospatial-analytics-tutorial']},
 'geospatial-analytics': {
     'root':'geospatial-analytics/geospatial-analytics-tutorial', 'name':'Geospatial Analytics',
     'summary':'Work with coordinate units, geometry joins, distance, spatial indexes, region holdouts and privacy-aware aggregation.',
     'groups':[('Geometry and metrics', ['location-unit-and-coordinate-contract','geometry-validation-and-spatial-joins','distance-and-nearest-service']),
               ('Serve and evaluate', ['spatial-index-and-serving-freshness','spatial-holdout-and-leakage','aggregation-and-location-privacy'])],
     'project':'pickup-coverage-project',
     'foundation':['data-science/data-science-for-beginners','data-engineering/data-engineering-tutorial'],
     'neighbors':['data-visualization/data-visualization-tutorial','knowledge-graphs/knowledge-graphs-tutorial']},
}

for config in subject_config.values():
    titles[config['root']] = config['name'] + ' Tutorial'
    titles[config['root'] + '/project'] = config['name'] + ': Projects'

for slug, config in subject_config.items():
    root_path = config['root']
    project_hub_path = root_path + '/project'
    modules = [{'title':group_title, 'summary':'Read in order and run the failure checks.',
                'lessons':[slug + '/' + lesson_name for lesson_name in lesson_names]}
               for group_title, lesson_names in config['groups']]
    project_path = slug + '/' + config['project']
    modules.append({'title':'Apply your knowledge', 'lessons':[project_path]})
    all_paths = [path for module in modules for path in module['lessons']]
    tabs = [{'title':config['name'], 'path':root_path}, {'title':'Projects', 'path':project_hub_path}]
    hub_body = ('<p>' + html.escape(config['summary']) + '</p><h2>Learning path</h2>' + links(all_paths)
                + '<h2>Connected foundations</h2><p>Use the earlier graph and data contracts as prerequisites.</p>'
                + links(config['foundation']) + '<h2>Further paths</h2>' + links(config['neighbors'])
                + '<h2>Practice</h2>' + links([project_hub_path]))
    hub = make_row(root_path, titles[root_path], config['summary'], hub_body,
                   'subject', slug, root_path, root_path, 10500 if slug == 'knowledge-graphs' else 10600,
                   {'modules':modules, 'resource_tabs':tabs})
    project_body = ('<p>Apply the ' + html.escape(config['name']) + ' curriculum to a checked project.</p>'
                    '<h2>Project brief</h2>' + links([project_path])
                    + '<h2>Required concepts</h2>' + links(all_paths[:-1])
                    + '<h2>Completion standard</h2><p>Submit runnable work, a data manifest, measured results and failure-case evidence.</p>')
    project_hub = make_row(project_hub_path, titles[project_hub_path],
                           'A checked project for the ' + config['name'] + ' curriculum.', project_body,
                           'subject', slug + '-project', project_hub_path, root_path,
                           10501 if slug == 'knowledge-graphs' else 10601,
                           {'modules':[{'title':'Projects','lessons':[project_path]}], 'resource_tabs':tabs})
    rows.extend((hub, project_hub))
    by_path[root_path] = hub
    by_path[project_hub_path] = project_hub

for index, item in enumerate(lessons):
    slug = item['path'].split('/')[0]
    root_path = subject_config[slug]['root']
    is_project = item['path'].endswith('-project')
    section_path = root_path + '/project' if is_project else root_path
    body = article_body(item)
    article = make_row(item['path'], item['title'], item['summary'], body, 'article',
                       slug + '-project' if is_project else slug, section_path, root_path,
                       10700 + index,
                       {'kind':'project' if is_project else 'tutorial',
                        'reading_minutes':max(5, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                        'author_path':'authors/aitrove-editorial',
                        'verification_suite':'Editorial and syntax review; project inputs needed for runtime checks',
                        'related':[{'path':path,'title':titles[path]} for path in item['related']]})
    rows.append(article)
    by_path[item['path']] = article

for source, target in [
    ('graph-machine-learning/entity-edge-and-snapshot-contract','knowledge-graphs/entity-identity-and-relation-schema'),
    ('graph-machine-learning/graph-construction-and-degree-skew','knowledge-graphs/constraint-validation-and-quality'),
    ('retrieval-ai/retrieval-ai-tutorial','knowledge-graphs/graph-grounded-retrieval-and-evaluation'),
    ('data-engineering/cdc-replay-and-deletes','knowledge-graphs/provenance-time-and-retraction'),
    ('data-science/dataset-grain-and-join-cardinality','geospatial-analytics/location-unit-and-coordinate-contract'),
    ('data-engineering/quality-quarantine-and-reconciliation','geospatial-analytics/geometry-validation-and-spatial-joins'),
    ('machine-learning/group-and-time-validation','geospatial-analytics/spatial-holdout-and-leakage'),
    ('data-visualization/distribution-and-outlier-displays','geospatial-analytics/aggregation-and-location-privacy'),
]:
    row = by_path[source]
    anchor = '<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in row['body']:
        row['body'] += anchor
        if row['type'] == 'article':
            row['data']['related'].append({'path':target,'title':titles[target]})
        row['updated_at'] = stamp

for source, target in [
    ('graph-machine-learning/graph-machine-learning-tutorial','knowledge-graphs/knowledge-graphs-tutorial'),
    ('data-engineering/data-engineering-tutorial','knowledge-graphs/knowledge-graphs-tutorial'),
    ('data-science/data-science-for-beginners','geospatial-analytics/geospatial-analytics-tutorial'),
    ('data-visualization/data-visualization-tutorial','geospatial-analytics/geospatial-analytics-tutorial'),
]:
    row = by_path[source]
    anchor = '<p><strong>Continue into another subject:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in row['body']:
        row['body'] += anchor
        row['updated_at'] = stamp

assert len({row['path'] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_articles':len(lessons), 'new_subject_hubs':4, 'crosslinks_from_existing':12}))
