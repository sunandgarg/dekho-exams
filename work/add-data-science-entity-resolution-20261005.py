"""Add original record-linkage lessons to the Data Science path."""
import datetime
import html
import json
from pathlib import Path
import re
import uuid

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
slugs = (
    'identifier-normalization-and-exact-linkage',
    'blocking-and-candidate-recall',
    'match-scores-and-human-review-bands',
    'entity-merge-lineage-and-metric-impact',
    'customer-identity-resolution-project',
)
new_paths = {'data-science/' + slug for slug in slugs}
rows = [row for row in rows if row['path'] not in new_paths]
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
lessons = []

def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='data-science/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost,
                        mistakes=mistakes, related=related))

add('identifier-normalization-and-exact-linkage',
    'Identifier normalization and exact linkage without false merges',
    'Exact joins are reliable only when identifier meaning and normalization rules are documented for both sources.', [
    ('Start with namespace and issuer', 'An account ID from a retail platform and an account ID from a support platform may share the value 047 while naming different people. A join key needs the issuing system or tenant as well as the local ID. Preserve raw ID, source, canonical ID and normalization version. [[data-science/dataset-grain-and-join-cardinality|Join-grain checks]] should fail when a supposedly one-to-one account link multiplies case rows.'),
    ('Normalize only proven equivalences', 'Trimming accidental outer whitespace may be safe for a source that documents whitespace as padding. Case folding may be safe for a source that guarantees case-insensitive IDs. Removing leading zeros is unsafe when CUS-047 and CUS-47 can be distinct. Email addresses need particular care: provider-specific punctuation or tags cannot be stripped as a universal rule. Keep the raw field so a future correction can reconstruct the link.'),
    ('Separate identity from contact', 'A shared household phone number or shipping address does not establish one customer. A person can also change email while preserving account identity. Use a stable issued ID when available, then keep contact fields as evidence rather than replacing identity with them. [[data-science/product-event-contract-and-identity|Product event identity]] may use a session or actor ID; record linkage must declare when that actor is believed to be the same entity across systems.'),
    ('Measure exact-link gaps', 'After an exact join, count left-only, right-only, one-to-one and one-to-many keys. Inspect nulls and reused IDs by source and time. If 2,047 order accounts and 1,910 support accounts are present, the overlap size alone says little without a clear eligible window and namespace. A missing match can mean no support case, an unobserved account mapping or a key-format error; do not classify all unmatched rows as faults.'),
    ('Test adversarial fixtures', 'Include CUS-047 and CUS-47, mixed-case IDs from a documented case-insensitive source, and the same local number in two tenants. Assert only the intended equivalences. If source rules differ, canonicalization must take the source contract as an argument, not apply one global string-cleaning function.')],
    'def canonical_account_key(source, tenant, raw_account_id):\n    if raw_account_id is None or not str(raw_account_id).strip():\n        raise ValueError("account ID required")\n    account_id = str(raw_account_id).strip()\n    if source == "retail_v2":\n        account_id = account_id.casefold()  # Issuer documents case-insensitive IDs.\n    elif source != "support_v1":\n        raise ValueError("unknown account namespace")\n    return source, tenant, account_id\n\nassert canonical_account_key("retail_v2", "north", " CUS-047 ") == ("retail_v2", "north", "cus-047")\nassert canonical_account_key("support_v1", "north", "CUS-047") != canonical_account_key("support_v1", "north", "CUS-47")',
    'Canonicalizing N records costs O(N) time and O(N) key storage. Hash joins on canonical keys have O(N + M) expected time for two sources, but collision audits and one-to-many checks must be retained before any downstream aggregation.',
    ['Do not remove leading zeros without an issuer rule that makes them insignificant.', 'Do not treat contact fields as stable person identity.', 'Do not join local IDs from different namespaces without the source and tenant.'],
    ['data-science/blocking-and-candidate-recall','data-science/match-scores-and-human-review-bands','data-science/dataset-grain-and-join-cardinality','data-science/customer-identity-resolution-project'])

add('blocking-and-candidate-recall',
    'Blocking for record linkage: reduce comparisons without hiding true matches',
    'Blocking limits candidate comparisons to plausible groups; a missed block can make a true link impossible to recover.', [
    ('Calculate the comparison problem', 'Two files of 36,000 and 41,000 customer records would create roughly 1.48 billion cross-file pairs if every row were compared with every other row. Candidate generation narrows the search by keys such as verified postal district or a stable transaction token. The score stage can only judge candidates it receives. [[data-science/identifier-normalization-and-exact-linkage|Exact linkage]] should remove proven matches first.'),
    ('Use several defensible passes', 'One pass might block on postal district plus the first two letters of a normalized family name. Another can use a verified phone hash where policy allows it. A single misspelled surname or moved address will defeat the first pass, so union candidates from independent passes and deduplicate pair IDs. Do not use a sensitive attribute merely because it improves a benchmark; the data-use contract still governs.'),
    ('Measure candidate recall on labeled pairs', 'Build a reviewed set of true matches that includes spelling changes, moves, missing fields and shared-household contacts. Candidate recall is the number of known true pairs generated divided by all known true pairs in that test set. This number does not prove recall for the whole population if the reviewed sample is unrepresentative. [[data-science/stratified-sampling-and-design-weights|Audit sampling]] can deliberately cover rare error modes.'),
    ('Inspect block sizes and skew', 'A block containing half the dataset saves little work and may exhaust memory, while thousands of singleton blocks may hide too many links. Report candidate pairs per pass, duplicate pairs across passes, maximum block size and reviewed-pair recall by subgroup. If a postcode is missing, define a fallback rather than placing all missing records in one enormous block.'),
    ('Keep the candidate boundary explicit', 'A pair excluded by blocking is not a negative match decision. In the result ledger, distinguish never compared, compared and rejected, compared and accepted, and sent for review. This matters when a new blocking strategy changes measured customer counts: it changes the opportunity to match, not necessarily the underlying population.')],
    'from collections import defaultdict\n\ndef postcode_candidates(left_customers, right_customers):\n    right_blocks = defaultdict(list)\n    for customer in right_customers:\n        key = (customer["postal_district"], customer["surname_key"][:2])\n        if all(key):\n            right_blocks[key].append(customer["record_id"])\n    candidates = set()\n    for customer in left_customers:\n        key = (customer["postal_district"], customer["surname_key"][:2])\n        if all(key):\n            candidates.update((customer["record_id"], right_id)\n                              for right_id in right_blocks[key])\n    return candidates\n\nassert postcode_candidates(\n    [{"record_id": "ret-47", "postal_district": "N4", "surname_key": "mehta"}],\n    [{"record_id": "sup-83", "postal_district": "N4", "surname_key": "mehra"}],\n) == {("ret-47", "sup-83")}',
    'Building blocks is O(L + R) expected time and space for L left and R right records. Emitting pairs costs O(P) for P candidates, where a large block still produces a quadratic number of pairs in that block. Monitor P and maximum block size, not only input row counts.',
    ['Do not call a pair a nonmatch merely because the blocker never generated it.', 'Do not report recall from a test set containing only easy exact matches.', 'Do not put every missing-key record into one unbounded comparison block.'],
    ['data-science/identifier-normalization-and-exact-linkage','data-science/match-scores-and-human-review-bands','data-science/precision-budget-and-effective-sample-size','data-science/customer-identity-resolution-project'])

add('match-scores-and-human-review-bands',
    'Match scores and review bands: separate similarity from identity',
    'A similarity score ranks candidate pairs; it is not automatically the probability that two records name the same entity.', [
    ('Specify fields and failures', 'For each generated pair, compare source-issued tokens, normalized name, address and verified contact information under explicit data-use rules. A shared address has different evidential value for a single-occupant account than for a household. Missing information is not disagreement. Record which fields were unavailable, which agreed and which conflicted. [[data-science/blocking-and-candidate-recall|Candidate generation]] determines the pairs this stage can see.'),
    ('Choose bands from reviewed cases', 'Set a high-confidence acceptance band, a low-confidence rejection band and a middle band for human review. Evaluate false merges and missed links separately because their costs differ: a false merge can expose one customer’s history to another, while a missed link can split one customer’s orders across two rows. The thresholds belong to a versioned policy and should be checked on a held-out reviewed set, including shared-family and name-change cases.'),
    ('Do not overread the number', 'A score of 0.83 from a hand-weighted rule is not an 83% chance of a match. Even a calibrated probability depends on the candidate population and review-label quality. If the blocker changes, the mix of candidate pairs changes too, and an old threshold may no longer have the same precision. [[machine-learning/probability-calibration|Calibration]] is relevant only when a probabilistic score and valid review labels are available.'),
    ('Protect reviewer independence', 'Present reviewers with enough evidence to decide, but avoid exposing a proposed score if it will anchor judgment. Record independent decisions, disagreement, adjudication and an uncertain outcome when evidence is insufficient. Do not force ambiguous household records into a binary class. [[data-annotation/annotator-assignment-and-blinding|Blinded review]] can reveal systematic disagreement before a merge policy is released.'),
    ('Check one awkward pair', 'Two records share a surname and postal district but have different first names and distinct verified account tokens. A name-similarity feature may still score high, yet the token conflict should block automatic acceptance. The policy needs explicit hard conflicts, not just a weighted total. Keep pair-level reasons so an analyst can explain why the same-looking address did not produce a merge.')],
    'def review_band(pair_evidence):\n    if pair_evidence["verified_token_conflict"]:\n        return "reject"\n    weighted_fields = ((0.45, pair_evidence["verified_token_agreement"]),\n                       (0.35, pair_evidence["name_similarity"]),\n                       (0.20, pair_evidence["address_similarity"]))\n    available = [(weight, value) for weight, value in weighted_fields\n                 if value is not None]\n    if not available:\n        return "review"\n    score = sum(weight * value for weight, value in available) / sum(\n        weight for weight, _ in available)\n    if score >= 0.91 and pair_evidence["verified_token_agreement"] == 1:\n        return "accept"\n    if score <= 0.38:\n        return "reject"\n    return "review"\n\nassert review_band({"verified_token_conflict": True,\n                    "verified_token_agreement": 0,\n                    "name_similarity": 0.97,\n                    "address_similarity": 1.0}) == "reject"\nassert review_band({"verified_token_conflict": False,\n                    "verified_token_agreement": None,\n                    "name_similarity": 0.97,\n                    "address_similarity": 1.0}) == "review"',
    'Scoring P candidate pairs with a fixed number of fields costs O(P) time and O(1) auxiliary space per pair. Producing explanations and review queues requires O(P) storage; reviewer time dominates for pairs in the middle band. This illustrative score is a policy rule, not a calibrated probability.',
    ['Do not interpret an arbitrary similarity score as a match probability.', 'Do not auto-merge pairs with a documented hard conflict because their soft fields agree.', 'Do not evaluate thresholds only on the same reviewed cases used to choose them.'],
    ['data-science/blocking-and-candidate-recall','data-science/entity-merge-lineage-and-metric-impact','data-annotation/annotator-assignment-and-blinding','data-science/customer-identity-resolution-project'])

add('entity-merge-lineage-and-metric-impact',
    'Entity merge lineage: show how identity decisions change metrics',
    'A merged entity graph changes denominators, histories and permissions; every released version needs a traceable decision path.', [
    ('Review clusters, not only edges', 'If A matches B and B matches C, a transitive grouping step places A, B and C together even if A and C have a strong conflict. Pair acceptance is therefore not the last quality gate. Inspect component size, contradictory tokens and cross-tenant membership before publishing a cluster. [[data-science/match-scores-and-human-review-bands|Pair review]] supplies approved edges, but a cluster policy must decide whether their transitive closure is valid.'),
    ('Version stable entity IDs', 'An entity ID should identify the released cluster under a declared resolution version. Keep source record IDs and a mapping from each to its entity ID. When a false merge is split, retain old-to-new lineage rather than overwriting all history. A metric computed under release 4 may count 46 customers while release 5 counts 47 from the same raw orders. Both results can be reproducible if the identity release is pinned.'),
    ('Recompute downstream rates', 'Repeat-purchase rate uses distinct customers as its denominator. A false merge can create an apparent repeat buyer by combining two people’s first orders; a missed link can hide a repeat buyer as two one-time buyers. After any material merge revision, recompute affected counts and publish the difference by reason. [[data-science/retention-cohort-and-maturity|Retention cohorts]] may also shift because the first-purchase date for a merged entity changes.'),
    ('Protect access boundaries', 'Entity resolution can join records that previously lived in separate privacy or tenant scopes. A technically plausible match is not authorization to reveal combined histories. Preserve purpose, consent and access checks at the resolved-entity layer, then test a false-merge rollback. [[privacy-aware-ml/threat-model-and-data-minimization|Data minimization]] remains relevant even when the use case is analysis rather than model training.'),
    ('Release with a diff', 'For each new identity version, report linked and unlinked record counts, cluster-size distribution, accepted-edge reasons, manual review volume, split and merge counts, and downstream metric restatements. Quarantine giant or contradictory components. A reviewer should trace one customer count from source rows through pair decisions to the published entity mapping.')],
    'def entity_components(record_ids, approved_links):\n    parent = {record_id: record_id for record_id in record_ids}\n    def find(record_id):\n        while parent[record_id] != record_id:\n            parent[record_id] = parent[parent[record_id]]\n            record_id = parent[record_id]\n        return record_id\n    for left_id, right_id in approved_links:\n        if left_id not in parent or right_id not in parent:\n            raise ValueError("approved link references an unknown record")\n        parent[find(right_id)] = find(left_id)\n    components = {}\n    for record_id in record_ids:\n        components.setdefault(find(record_id), set()).add(record_id)\n    return list(components.values())\n\nassert entity_components(["ret-7", "sup-7", "ret-9"],\n                         [("ret-7", "sup-7")]) == [{"ret-7", "sup-7"}, {"ret-9"}]',
    'With path compression, building components from N records and E approved links is near O(N + E) in practice and uses O(N) memory. Cluster-level conflict checks add comparisons within components; they are necessary before a transitive merge is trusted.',
    ['Do not assume two approved pair links imply a safe three-record cluster.', 'Do not overwrite old entity mappings without a release lineage.', 'Do not let a plausible match bypass tenant or consent boundaries.'],
    ['data-science/match-scores-and-human-review-bands','data-science/retention-cohort-and-maturity','data-science/dataset-grain-and-join-cardinality','data-science/customer-identity-resolution-project'])

add('customer-identity-resolution-project',
    'Project: resolve customer records and audit the metric restatement',
    'Build a versioned customer mapping from two systems, with candidate recall, review decisions, cluster checks and a repeat-purchase diff.', [
    ('Construct two imperfect sources', 'Create 47 retail account records and 39 support records. Include a moved customer, a changed family name, two members of one household, reused local IDs in different tenants, one missing postal district and a repeated event ID. Provide a small adjudicated set of known matches and known nonmatches, including difficult cases. Raw records must remain available. [[data-science/identifier-normalization-and-exact-linkage|Namespace rules]] determine exact matches.'),
    ('Generate candidates in passes', 'Resolve exact issued tokens first. Then produce candidate pairs from two independent blocking keys and deduplicate pair IDs. Report pair count, maximum block size and recall against the reviewed true-match set. Include a true match missed by one pass but caught by the other. A known match missed by both is a blocker failure, not a scoring failure. [[data-science/blocking-and-candidate-recall|The blocking lesson]] sets that audit.'),
    ('Review and release clusters', 'Run a versioned score rule with hard conflicts. Put ambiguous pairs in a reviewer queue and keep review evidence. Build components only from approved edges, then fail components with contradictory verified tokens or mixed tenants. Give each released component a stable versioned entity ID. [[data-science/entity-merge-lineage-and-metric-impact|Merge lineage]] must support a later split.'),
    ('Show the analytical consequence', 'Compute distinct buyers and repeat-purchase rate from the same frozen order table under identity release A and release B. Report added, removed and changed entity assignments and the exact numerator and denominator difference. A false household merge should create a detectable artificial repeat buyer; correcting it should restate the metric with an explanation, not silently change a dashboard.'),
    ('Deliver proof of reproducibility', 'Save raw fixtures, canonicalization rules, candidate pairs, reviewed labels, approved edges, cluster conflicts, released mappings, metric outputs, code revision and snapshot cutoff. Add assertions for tenant isolation, candidate recall on the reviewed set and exact reconciliation of all source record IDs into either a released entity or a documented unresolved state.')],
    'def repeat_buyer_count(order_rows, entity_by_account):\n    orders_by_entity = {}\n    for order in order_rows:\n        entity_id = entity_by_account[order["account_id"]]\n        orders_by_entity.setdefault(entity_id, set()).add(order["order_id"])\n    return sum(len(order_ids) >= 2 for order_ids in orders_by_entity.values())\n\norders = [{"account_id": "ret-17", "order_id": "ord-41"},\n          {"account_id": "ret-18", "order_id": "ord-42"}]\nassert repeat_buyer_count(orders, {"ret-17": "person-A", "ret-18": "person-B"}) == 0\nassert repeat_buyer_count(orders, {"ret-17": "person-A", "ret-18": "person-A"}) == 1',
    'The final metric scan costs O(O) expected time and space for O orders. Candidate generation can still create quadratic work within large blocks; pair review, cluster validation and privacy checks dominate the operating cost. Preserve an identity-release key with every published metric.',
    ['Do not score pairs that blocking never generated and call them rejected.', 'Do not publish a transitive cluster without checking contradictions.', 'Do not compare repeat rates across identity releases without a restatement ledger.'],
    ['data-science/identifier-normalization-and-exact-linkage','data-science/blocking-and-candidate-recall','data-science/match-scores-and-human-review-bands','data-science/entity-merge-lineage-and-metric-impact'])

assert len(lessons) == len(new_paths) == 5
assert {item['path'] for item in lessons} == new_paths
titles = {path: row['title'] for path, row in by_path.items()}
titles.update({item['path']: item['title'] for item in lessons})

def prose(value):
    return re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',
                  lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                  html.escape(value))

def links(paths):
    return '<ul>' + ''.join('<li><a href="/' + path + '">' + html.escape(titles[path]) + '</a></li>'
                            for path in paths) + '</ul>'

def article_body(item):
    parts = ['<p>' + html.escape(item['summary']) + '</p>']
    for heading, paragraph in item['sections']:
        parts.extend(('<h2>' + html.escape(heading) + '</h2>', '<p>' + prose(paragraph) + '</p>'))
    parts.extend(('<h2>Implementation</h2>',
                  '<pre><code class="language-python">' + html.escape(item['code']) + '</code></pre>',
                  '<h2>Performance and operating cost</h2>', '<p>' + html.escape(item['cost']) + '</p>',
                  '<h3>Common Mistakes</h3>',
                  '<ul>' + ''.join('<li>' + html.escape(mistake) + '</li>' for mistake in item['mistakes']) + '</ul>',
                  '<h2>Read next</h2>', links(item['related'])))
    return ''.join(parts)

root_path = 'data-science/data-science-for-beginners'
project_hub_path = root_path + '/project'
for index, item in enumerate(lessons):
    is_project = item['path'].endswith('-project')
    body = article_body(item)
    path = item['path']
    row = dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://aitrove.in/' + path)),
               type='article', path=path, title=item['title'], summary=item['summary'], body=body,
               category='AI & Data', subject='data-science-project' if is_project else 'data-science',
               difficulty='Intermediate', tags=['ai-data', 'data-science'], potd_date=None,
               featured=False, sort_order=12100 + index, status='published', published_at=stamp,
               created_at=stamp, updated_at=stamp,
               data={'subject_root':root_path,
                     'section_path':project_hub_path if is_project else root_path,
                     'content_format':'html', 'seo_ready':True,
                     'kind':'project' if is_project else 'tutorial',
                     'reading_minutes':max(5, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                     'author_path':'authors/aitrove-editorial',
                     'verification_suite':'Editorial and syntax review; project inputs needed for runtime checks',
                     'related':[{'path':target, 'title':titles[target]} for target in item['related']]})
    rows.append(row)
    by_path[path] = row

tutorial_paths = ['data-science/' + slug for slug in slugs[:4]]
project_path = 'data-science/' + slugs[-1]
hub = by_path[root_path]
module_paths = {path for module in hub['data']['modules'] for path in module['lessons']}
if not set(tutorial_paths).issubset(module_paths):
    hub['data']['modules'].insert(-1, {'title':'Record linkage and entity resolution',
                                      'summary':'Preserve namespaces, evaluate candidate coverage and review merge effects.',
                                      'lessons':tutorial_paths})
apply_module = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
if project_path not in apply_module['lessons']:
    apply_module['lessons'].append(project_path)
if '<h2>Record linkage and entity resolution</h2>' not in hub['body']:
    hub['body'] += ('<h2>Record linkage and entity resolution</h2>' + links(tutorial_paths)
                    + '<h2>Customer identity project</h2>' + links([project_path]))
hub['updated_at'] = stamp

project_hub = by_path[project_hub_path]
if project_path not in project_hub['data']['modules'][0]['lessons']:
    project_hub['data']['modules'][0]['lessons'].append(project_path)
if '<h2>Customer identity project</h2>' not in project_hub['body']:
    project_hub['body'] += '<h2>Customer identity project</h2>' + links([project_path])
project_hub['updated_at'] = stamp

for source, target in [
    ('data-science/dataset-grain-and-join-cardinality', tutorial_paths[0]),
    ('data-science/product-event-contract-and-identity', tutorial_paths[0]),
    ('data-science/stratified-sampling-and-design-weights', tutorial_paths[1]),
    ('data-annotation/annotator-assignment-and-blinding', tutorial_paths[2]),
    ('machine-learning/probability-calibration', tutorial_paths[2]),
    ('data-science/retention-cohort-and-maturity', tutorial_paths[3]),
    ('data-science/reproducible-analysis-snapshot', tutorial_paths[3]),
]:
    source_row = by_path[source]
    anchor = '<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in source_row['body']:
        source_row['body'] += anchor
        if source_row['type'] == 'article':
            source_row['data'].setdefault('related', []).append({'path':target, 'title':titles[target]})
        source_row['updated_at'] = stamp

assert len({row['path'] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_articles':len(lessons), 'new_projects':1, 'crosslinks_from_existing':7}))
