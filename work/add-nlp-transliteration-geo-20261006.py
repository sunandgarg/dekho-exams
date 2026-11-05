"""Add cross-script identity and geographic-language modules to NLP."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
T = 'Cross-script name identity'
G = 'Geographic language grounding'

lessons = [
    {
        'path': N + 'transliteration-variants-and-name-identity',
        'title': 'Transliteration variants are candidates, not identity',
        'module': T, 'project': False,
        'summary': 'Treat names written in another script as versioned candidate evidence; a similar rendering does not establish that two records describe one entity.',
        'sections': [
            ('Separate the written form from the entity', 'Transliteration maps a name between writing systems. It does not translate an organization, prove a legal identity or guarantee a unique spelling. A vendor registered as “सारिका” might appear as “Sarika” in one import and “Saarika” in another. Keep the source spelling, script, language tag, span offsets and record identifier. Do not replace the original with a Latin rendering. [[natural-language-processing/unicode-normalization-and-source-offsets|Unicode and offset contracts]] explain why a cleaned display string must still point back to the exact source bytes.'),
            ('Generate several plausible forms', 'A candidate generator may combine an owner-approved alias table, a transliteration model and script-specific normalization. Record which process produced each form and its version. Candidate recall matters at this stage; precision comes later. A single top-ranked transliteration is a poor join key because vowels, aspirated consonants, abbreviations and regional conventions can create several spellings. Search by alias within an authorized entity catalog, then retain all plausible IDs until context is checked. [[natural-language-processing/entity-link-candidates-and-nil-decision|Entity linking with a NIL decision]] supplies the broader candidate contract.'),
            ('Control collision and access', 'Names can be homographs across scripts and companies can share a trading name. A normalized match can also cross a tenant boundary if the lookup table ignores scope. Restrict candidates to the caller’s permitted catalog before ranking. Require another independent clue such as a registered identifier, city or owner record for a consequential merge. Unknown or competing candidates should remain unresolved. The [[natural-language-processing/transliteration-evidence-and-collision-review|collision lesson]] turns this into a review decision.'),
            ('Measure the downstream task', 'Evaluate candidate recall, unique-link precision, false merges and NIL decisions by script pair, entity type and spelling family. A single reference spelling can mark a valid alternate rendering wrong, so score the eventual entity lookup as well as the surface form. Split test data by entity family; otherwise a model may memorize the same organization under another spelling. Compare results against a source-script exact-match baseline. The [[natural-language-processing/vendor-cross-script-linkage-project|project]] puts these checks into an intake workflow.'),
        ],
        'code': '''def alias_candidates(source_name, source_script, permitted_ids, alias_rows):
    matches = []
    for alias in alias_rows:
        if alias["script"] != source_script:
            continue
        if alias["written_name"] != source_name:
            continue
        if alias["entity_id"] not in permitted_ids:
            continue
        matches.append({"entity_id": alias["entity_id"],
                        "alias_version": alias["version"]})
    return matches

aliases = [{"script": "Deva", "written_name": "सारिका",
            "entity_id": "vendor-47", "version": "alias-r4"},
           {"script": "Deva", "written_name": "सारिका",
            "entity_id": "vendor-82", "version": "alias-r4"}]
found = alias_candidates("सारिका", "Deva", {"vendor-47", "vendor-82"}, aliases)
assert {row["entity_id"] for row in found} == {"vendor-47", "vendor-82"}
assert alias_candidates("सारिका", "Deva", {"vendor-47"}, aliases) == [found[0]]
''',
        'cost': 'The simple scan takes O(a) time and O(k) output space for a aliases and k permitted matches. An index on script and written form avoids scanning the whole catalog. This example only finds approved exact aliases; a transliteration model would propose additional forms, never authorize an entity merge.',
        'mistakes': ['Collapsing every spelling into a single irreversible canonical string.', 'Using the first Latin rendering as a primary key.', 'Ranking candidates before applying tenant scope.', 'Measuring only character similarity while ignoring false entity merges.'],
        'related': [N + 'transliteration-evidence-and-collision-review', N + 'vendor-cross-script-linkage-project', N + 'entity-link-candidates-and-nil-decision', N + 'unicode-normalization-and-source-offsets', N + 'cross-language-query-document-contract'],
    },
    {
        'path': N + 'transliteration-evidence-and-collision-review',
        'title': 'Cross-script linkage: contextual evidence and collision review',
        'module': T, 'project': False,
        'summary': 'Resolve transliteration candidates with independent record evidence, explicit ties and a reversible review trail.',
        'sections': [
            ('Rank identities, not strings', 'The same written name can belong to two vendors. A transliteration score measures whether spellings correspond, not whether the business records are identical. Compare permitted candidates using stable evidence: tax registration, verified account number, city, service history or an owner-approved alias. Give each feature a provenance and freshness date. Avoid counting three copied aliases as three independent clues. [[natural-language-processing/transliteration-variants-and-name-identity|Variant generation]] should hand over a candidate set, not an automatic winner.'),
            ('Define a tie and a NIL path', 'A decision policy should be able to say “no listed entity” and “two plausible entities.” If the best candidate is only slightly ahead of another, hold for review. If the name looks close but a verified identifier conflicts, reject the link. Choose thresholds on a held-out set containing same-name businesses, script variants and unseen entities. [[natural-language-processing/entity-link-version-and-merge-review|Entity merge review]] covers corrections when a previously accepted identity is later challenged.'),
            ('Make decisions reversible', 'Store the source record, candidate IDs, field evidence, alias model version, reviewer and decision. Keep a merge operation separate from candidate retrieval. If a reviewer corrects a link, update dependent search indexes and derived reports, while preserving the original text and historical decision. Scope each candidate lookup to authorized records; a high score cannot bypass access policy. A confidence value without the compared candidate set is hard to audit.'),
            ('Test against costly errors', 'Count false merges separately from missed matches. A missed match creates extra review work; a false merge can combine invoices, permissions or personal data from different organizations. Test recent aliases, short names, punctuation loss and copied addresses. Slice by source script and region because aggregate accuracy can hide a failing subgroup. The [[natural-language-processing/vendor-cross-script-linkage-project|vendor intake project]] requires an explicit review state when evidence is tied.'),
        ],
        'code': '''def choose_vendor(candidate_rows, minimum_score=3, margin=2):
    ranked = sorted(candidate_rows,
                    key=lambda row: (-row["evidence_score"], row["entity_id"]))
    if not ranked or ranked[0]["evidence_score"] < minimum_score:
        return {"state": "nil"}
    if len(ranked) > 1 and ranked[0]["evidence_score"] - \
            ranked[1]["evidence_score"] < margin:
        return {"state": "review", "candidate_ids":
                [row["entity_id"] for row in ranked[:2]]}
    return {"state": "linked", "entity_id": ranked[0]["entity_id"]}

vendors = [{"entity_id": "vendor-47", "evidence_score": 5},
           {"entity_id": "vendor-82", "evidence_score": 4}]
assert choose_vendor(vendors)["state"] == "review"
assert choose_vendor([{**vendors[1], "evidence_score": 1}, vendors[0]]) == {
    "state": "linked", "entity_id": "vendor-47"}
assert choose_vendor([])["state"] == "nil"
''',
        'cost': 'Sorting c candidates costs O(c log c) time and O(c) space. The toy score is an input, not a trustworthy model output: production evidence needs calibrated weights, conflict rules, access filtering and reviewer logs before a link changes records.',
        'mistakes': ['Calling two copied aliases independent evidence.', 'Using a raw similarity score as proof of legal identity.', 'Dropping the runner-up candidate from audit logs.', 'Applying a merge before a reviewer can inspect conflicting identifiers.'],
        'related': [N + 'transliteration-variants-and-name-identity', N + 'vendor-cross-script-linkage-project', N + 'entity-link-version-and-merge-review', N + 'multilingual-calibration-and-fallback', N + 'cross-document-mention-chain-revision-and-access'],
    },
    {
        'path': N + 'vendor-cross-script-linkage-project',
        'title': 'Project: link vendor names across scripts without false merges',
        'module': T, 'project': True,
        'summary': 'Build a scoped intake review that retains source-script names, generates candidates and refuses a merge when independent evidence is weak.',
        'sections': [
            ('Assemble the fixture', 'Prepare vendor records with Devanagari and Latin name variants, two businesses that share a short trading name, an unseen business and one stale address. Include a tenant boundary. Each incoming mention needs a source text offset, document revision, script label and permitted candidate set. Use fictional identifiers and consistent field values. [[natural-language-processing/transliteration-variants-and-name-identity|Variant generation]] supplies recall without pretending that the first spelling is authoritative.'),
            ('Write the gold decision', 'For every intake record, annotate linked, NIL or review. A reviewer should explain which independent field resolved a tie: a verified registration number can support a link, while a copied address alone cannot. Freeze the annotation policy and keep corrections by version. Split evaluation by underlying vendor rather than name string so a variant of one vendor cannot leak across train and test. Measure reviewer disagreement as a policy signal, not just model noise.'),
            ('Implement an admission boundary', 'Lookup may produce several candidates, but the project must only admit candidates inside the authenticated tenant. A matching alias outside that set remains inaccessible. Reject a proposed merge when a verified identifier conflicts, even if the transliterated name looks perfect. The code below represents the final admission check; [[natural-language-processing/transliteration-evidence-and-collision-review|collision review]] supplies the ranking and tie state before this check.'),
            ('Release by error cost', 'Report candidate recall, linked precision, false merges, NIL accuracy, review volume and median reviewer time. Inspect each false merge with its source text and evidence trail. Re-run the fixture after alias updates and test that earlier links remain stable or are explicitly invalidated. Do not silently overwrite billing or access records during a name reconciliation; a project can ship candidate suggestions before it ships automated merges.'),
        ],
        'code': '''def admit_vendor_link(decision, registration, tenant_vendor_ids):
    if decision.get("state") != "linked":
        return {"state": "hold", "reason": "unresolved-link"}
    vendor_id = decision["entity_id"]
    if vendor_id not in tenant_vendor_ids:
        return {"state": "deny", "reason": "tenant-scope"}
    expected = registration.get(vendor_id)
    if expected is None or expected != decision.get("registration_id"):
        return {"state": "hold", "reason": "identifier-conflict"}
    return {"state": "admitted", "entity_id": vendor_id}

registration = {"vendor-47": "reg-47", "vendor-82": "reg-82"}
proposal = {"state": "linked", "entity_id": "vendor-47",
            "registration_id": "reg-47"}
assert admit_vendor_link(proposal, registration, {"vendor-47"})["state"] == \
    "admitted"
assert admit_vendor_link({**proposal, "registration_id": "reg-82"},
                         registration, {"vendor-47"})["state"] == "hold"
''',
        'cost': 'With hash-backed sets and maps, this admission check is expected O(1) time and space per proposal. Candidate generation and evidence review cost more and depend on catalog size. The snippet verifies a supplied identifier; production must authenticate its source and ensure the registry is current before changing any record.',
        'mistakes': ['Letting a name match merge records across tenants.', 'Using one gold spelling as the only accepted rendering.', 'Treating an unresolved tie as a low-confidence link instead of review.', 'Mutating billing records before measuring false merges.'],
        'related': [N + 'transliteration-variants-and-name-identity', N + 'transliteration-evidence-and-collision-review', N + 'entity-link-candidates-and-nil-decision', N + 'entity-link-version-and-merge-review', N + 'grouped-temporal-text-validation'],
    },
    {
        'path': N + 'toponym-candidates-and-spatial-relation-frames',
        'title': 'Place mentions: toponym candidates and spatial relation frames',
        'module': G, 'project': False,
        'summary': 'Extract place candidates and the relation between them before assigning coordinates to a natural-language location description.',
        'sections': [
            ('A place name is not a coordinate', '“North of Cedar Depot” contains a named anchor and a relation. It does not provide a single point. A place name can refer to several facilities, and “north of” may mean a broad area whose extent depends on task and map scale. Capture mention offsets, anchor candidates, relation type and any explicit distance or unit. Keep unknown extent as unknown. [[natural-language-processing/entity-link-candidates-and-nil-decision|Entity candidate linking]] gives a suitable NIL state for absent facilities.'),
            ('Build a typed frame', 'Represent the target, anchor, relation and constraints separately. For “within 3 kilometres of Cedar Depot,” the numeric radius is explicit; for “near Cedar Depot,” it is not. Do not invent a radius from the word “near.” In a sentence with two anchors, attach each relation to the correct phrase rather than applying it to the entire document. [[natural-language-processing/dependency-tree-contract-and-token-alignment|Dependency alignment]] helps preserve which noun phrase a preposition modifies.'),
            ('Use context to narrow anchors', 'A gazetteer may hold two Cedar Depots in different districts. Document region, facility type and neighboring place mentions can narrow the candidate set. Avoid using the incident’s desired outcome as evidence for the anchor; that would bias resolution. Store gazetteer version, selected feature ID and geographic type. A precise coordinate for the wrong depot is worse than an unresolved mention. The [[natural-language-processing/spatial-scope-uncertainty-and-map-resolution|scope lesson]] discusses geometry after candidate resolution.'),
            ('Evaluate the whole frame', 'Score mention span, place ID, relation type, distance value and unit separately. Then evaluate the resolved region against a human-reviewed map fixture. A system can recognize both place names yet reverse “east of” into “west of.” Include direction, containment, border, route-distance and ambiguous “near” cases. The [[natural-language-processing/field-report-location-grounding-project|field report project]] prevents unresolved descriptions from being turned into misleading pins.'),
        ],
        'code': '''def location_frame(anchor_name, relation, distance_km, gazetteer):
    candidates = gazetteer.get(anchor_name, [])
    if len(candidates) != 1:
        return {"state": "review", "reason": "ambiguous-anchor",
                "candidate_ids": [item["place_id"] for item in candidates]}
    if relation == "within" and distance_km is not None and distance_km > 0:
        return {"state": "bounded", "anchor_id": candidates[0]["place_id"],
                "radius_km": distance_km}
    return {"state": "review", "reason": "unbounded-relation"}

places = {"Cedar Depot": [{"place_id": "depot-47"}]}
assert location_frame("Cedar Depot", "within", 3, places) == {
    "state": "bounded", "anchor_id": "depot-47", "radius_km": 3}
assert location_frame("Cedar Depot", "near", None, places)["state"] == \
    "review"
''',
        'cost': 'The dictionary lookup is expected O(1); emitting c candidate IDs costs O(c) time and space. Actual gazetteer search, geometry and map rendering have separate costs. The snippet returns a typed frame, not a computed boundary or a claim that an incident occurred inside it.',
        'mistakes': ['Assigning a coordinate to the word “north” without an extent.', 'Choosing the first gazetteer match when names repeat.', 'Treating “near” as a fixed radius without a declared policy.', 'Testing place-name recognition while ignoring reversed spatial relations.'],
        'related': [N + 'spatial-scope-uncertainty-and-map-resolution', N + 'field-report-location-grounding-project', N + 'entity-link-candidates-and-nil-decision', N + 'dependency-tree-contract-and-token-alignment', N + 'quantity-span-unit-and-range-contract'],
    },
    {
        'path': N + 'spatial-scope-uncertainty-and-map-resolution',
        'title': 'Spatial language: scope, uncertainty and map resolution',
        'module': G, 'project': False,
        'summary': 'Keep qualitative location phrases as uncertain regions and distinguish a resolved anchor from a verified target location.',
        'sections': [
            ('Carry the relation through resolution', 'A map pin is a point estimate. “South of the rail yard” is a directional region, and “between the yard and the clinic” depends on two anchors and an unstated corridor width. Preserve the original phrase and its relation frame even after selecting anchor IDs. If the product needs a point for display, mark it as an approximation and avoid using it for eligibility or emergency dispatch. [[natural-language-processing/toponym-candidates-and-spatial-relation-frames|Toponym frames]] keep the anchor distinct from the target.'),
            ('Separate precision from certainty', 'A gazetteer can provide coordinates with many decimal places for an anchor while the described event remains vaguely located. Store anchor resolution confidence, relation interpretation confidence and geographic extent separately. A location may be certain at district level but unresolved at street level. Expose this distinction in downstream filtering and maps. Do not convert uncertainty into false precision through rounding or a default centroid.'),
            ('Choose geometry only under policy', 'An explicit “within 3 kilometres” can become a distance test once coordinate system, Earth-distance method and measurement convention are defined. “Near” requires a task-specific policy or a clarification. Polygon containment requires a boundary version and a choice about points on the edge. Beware of degrees-versus-metres errors and antimeridian crossings. The small code sample below checks whether a numeric-distance query is admissible; it intentionally leaves geodesic computation to a spatial service.'),
            ('Audit geographic errors', 'Create fixtures for duplicate place names, outdated facilities, nested regions, border points, ambiguous directions and missing anchors. Score whether the system asks for clarification when appropriate, not just distance error after it guesses a point. Review the errors by region and document style. A correct anchor with the wrong relation can send a responder to the wrong side of a facility. The [[natural-language-processing/field-report-location-grounding-project|field report project]] tests the release boundary.'),
        ],
        'code': '''def admit_spatial_filter(frame, allowed_anchor_ids, maximum_radius_km):
    if frame.get("state") != "bounded":
        return {"state": "review", "reason": "uncertain-extent"}
    if frame.get("anchor_id") not in allowed_anchor_ids:
        return {"state": "deny", "reason": "anchor-scope"}
    radius = frame.get("radius_km")
    if isinstance(radius, bool) or not isinstance(radius, (int, float)) or \
            not 0 < radius <= maximum_radius_km:
        return {"state": "review", "reason": "radius-policy"}
    return {"state": "eligible", "anchor_id": frame["anchor_id"],
            "radius_km": radius}

bounded = {"state": "bounded", "anchor_id": "depot-47", "radius_km": 3}
assert admit_spatial_filter(bounded, {"depot-47"}, 7)["state"] == "eligible"
assert admit_spatial_filter({**bounded, "radius_km": True},
                            {"depot-47"}, 7)["state"] == "review"
''',
        'cost': 'With a hash-backed anchor set this gate takes expected O(1) time and space. Computing geodesic distances or intersecting polygons is a separate operation whose cost depends on the spatial index and candidate count. Eligibility here does not certify that a target lies inside a region.',
        'mistakes': ['Displaying a vague relation as a precise event pin.', 'Confusing anchor-coordinate precision with event-location certainty.', 'Comparing geographic degrees to a radius in kilometres.', 'Ignoring boundary versions when checking containment.'],
        'related': [N + 'toponym-candidates-and-spatial-relation-frames', N + 'field-report-location-grounding-project', N + 'quantity-span-unit-and-range-contract', N + 'time-expression-anchor-and-zone-contract', N + 'entity-link-version-and-merge-review'],
    },
    {
        'path': N + 'field-report-location-grounding-project',
        'title': 'Project: ground field-report locations without false map pins',
        'module': G, 'project': True,
        'summary': 'Parse field-report place descriptions into candidate anchors and bounded regions, then hold ambiguous directions and distances for review.',
        'sections': [
            ('Create the field-report corpus', 'Use synthetic reports such as “within 3 kilometres of Cedar Depot” and “near Cedar Depot.” Add two facilities with the same name in different districts, a renamed clinic, a border case and a direction relative to a route. Annotate source spans, anchor ID, relation, numeric value, unit, geographic type and whether a map filter is allowed. Keep the report text and the gazetteer snapshot. [[natural-language-processing/toponym-candidates-and-spatial-relation-frames|Frame extraction]] provides the first reviewable representation.'),
            ('Implement staged resolution', 'Identify place spans, retrieve authorized gazetteer candidates, resolve only with independent context and parse the relation. Translate an explicit distance to a typed value under a unit policy. Do not accept “near” as a radius and do not turn “north of” into a single point. The code below checks the final release state; a spatial service must still perform the actual distance test with a declared coordinate system. [[natural-language-processing/spatial-scope-uncertainty-and-map-resolution|Spatial scope]] sets that boundary.'),
            ('Review answer and display behavior', 'For every report, compare the chosen anchor and represented extent against the annotated fixture. Inspect map output for false precision: an unresolved report should show a text description and review marker, not a precise pin. Separate extraction error, wrong gazetteer match, wrong relation and geometry error. Test that users cannot query a restricted facility through a place alias.'),
            ('Set a release gate', 'Report candidate recall, anchor-link precision, relation accuracy, bounded-region correctness and the percentage correctly held for clarification. Add human review of a sample of accepted regions. A location workflow can release text indexing before automated spatial filtering if the latter has unresolved ambiguity. Record every gazetteer update that changes an existing report’s resolved anchor so map results can be recomputed deliberately.'),
        ],
        'code': '''def release_location_record(report, permitted_place_ids):
    if report.get("relation_state") != "bounded":
        return {"state": "text-only", "reason": "unresolved-relation"}
    anchor_id = report.get("anchor_id")
    if anchor_id not in permitted_place_ids:
        return {"state": "hold", "reason": "anchor-scope"}
    if not report.get("gazetteer_version") or not report.get("source_span"):
        return {"state": "hold", "reason": "missing-provenance"}
    return {"state": "region-ready", "anchor_id": anchor_id,
            "gazetteer_version": report["gazetteer_version"]}

report = {"relation_state": "bounded", "anchor_id": "depot-47",
          "gazetteer_version": "gazetteer-r7", "source_span": [19, 30]}
assert release_location_record(report, {"depot-47"})["state"] == \
    "region-ready"
assert release_location_record({**report, "relation_state": "vague"},
                               {"depot-47"})["state"] == "text-only"
''',
        'cost': 'The final release check is expected O(1) time and space with a hash-backed place set. Candidate retrieval, linguistic parsing and spatial filtering dominate system cost. “Region-ready” only authorizes the next spatial computation; it must not be rendered as a verified point location.',
        'mistakes': ['Drawing a pin at the anchor rather than representing the described area.', 'Guessing a radius for a vague relation.', 'Losing the gazetteer version needed to revisit old reports.', 'Scoring only toponym detection while ignoring relation errors.'],
        'related': [N + 'toponym-candidates-and-spatial-relation-frames', N + 'spatial-scope-uncertainty-and-map-resolution', N + 'entity-link-candidates-and-nil-decision', N + 'quantity-span-unit-and-range-contract', N + 'incident-timeline-review-project'],
    },
]

crosslinks = [
    (N + 'entity-link-candidates-and-nil-decision', N + 'transliteration-variants-and-name-identity'),
    (N + 'cross-language-query-document-contract', N + 'transliteration-evidence-and-collision-review'),
    (N + 'entity-link-version-and-merge-review', N + 'vendor-cross-script-linkage-project'),
    (N + 'dependency-paths-for-relation-candidates', N + 'toponym-candidates-and-spatial-relation-frames'),
    (N + 'quantity-span-unit-and-range-contract', N + 'spatial-scope-uncertainty-and-map-resolution'),
    (N + 'incident-timeline-review-project', N + 'field-report-location-grounding-project'),
]

if __name__ == '__main__':
    publish(lessons, (T, G), crosslinks,
            'aitrove-nlp-transliteration-geo-import-20261006.json', 4884,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
