"""Add spatial-lake and executable-contract Data Engineering lessons."""
from de_batch_publisher import publish

SPATIAL = 'Spatial lake layout and exact joins'
CONTRACTS = 'Executable data contracts and release gates'
LESSONS = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    assert len(sections) == 5
    LESSONS.append(dict(path='data-engineering/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add('spatial-cell-resolution-and-hotspot-layout', 'Spatial cell resolution and hotspot layout',
    'A grid key makes location data easier to prune, but choosing one cell resolution for every city can replace a full scan with thousands of tiny files and one overloaded downtown cell.', [
    ('Start with the question, not the grid', 'Map the actual predicates: a city dashboard reads days of events inside several neighborhoods, while a proximity alert reads a small radius around one point. Keep event time as an independent partition key because time filters usually eliminate more history than a spatial key. Add a coarse cell identifier for physical ordering or clustering, then measure files and bytes scanned for the real query shapes. [[data-engineering/partition-planning-and-skew|Partition planning]] explains why a column is not automatically a good directory boundary.'),
    ('Set resolution against file size', 'A finer grid yields tighter candidate sets, but it also increases partition count and small-file pressure. Count events, bytes and reader frequency per cell at several resolutions. The right resolution is one that prunes enough irrelevant data while leaving each active cell with files large enough for efficient scans. Keep sparse cells together where the table format allows it; do not create a directory for every empty possible cell.'),
    ('Plan for uneven density', 'A downtown cell can receive 47 times the traffic of a rural cell. Splitting every cell more finely to fix one hotspot wastes metadata elsewhere. Use time slices, bounded salt buckets or an adaptive subdivision for the hot area, but document how a reader expands that layout back into a complete candidate set. [[data-engineering/skewed-keys-and-salted-aggregation|Skew handling]] also matters when events are shuffled for downstream aggregation.'),
    ('Keep the exact geometry', 'A cell identifier is an index candidate, not the location itself. A radius can cross cell edges; a polygon can touch many cells without containing every point in them. Retain the original coordinates and coordinate reference assumptions, select all potentially intersecting cells and apply an exact point-in-polygon or distance predicate afterward. The coarse filter may over-read, but it must never discard a true match.'),
    ('Check the release boundary', 'When a location correction moves an event from one cell to another, the old placement must disappear from the current generation before the new placement is published. Compare stable event IDs, cell counts and query results across the two generations. A single corrected point can otherwise appear twice near a boundary. Keep the older snapshot for the replay period and record which grid version produced each published key.')],
    '''from collections import Counter

traffic_by_cell = Counter({"downtown-47": 47000, "suburb-48": 960,
                           "rural-49": 125})
target_events_per_file = 8000

def planned_files(events_per_cell, target_size):
    return {cell: max(1, (events + target_size - 1) // target_size)
            for cell, events in events_per_cell.items()}

plan = planned_files(traffic_by_cell, target_events_per_file)
assert plan == {"downtown-47": 6, "suburb-48": 1, "rural-49": 1}
assert sum(traffic_by_cell.values()) == 48085''',
    'Counting N events by cell takes O(N) expected time and O(C) state for C populated cells. Planning files from those counts is O(C). Real query cost also includes metadata listing and scanning every selected file; excessively fine cells raise both file count and compaction work. Compare end-to-end latency and bytes scanned, not cell count alone.',
    ['Do not treat a grid cell as an exact distance or polygon answer.', 'Do not partition so finely that most cells contain one tiny file.', 'Do not repair a hotspot by changing the grid without a versioned migration plan.'],
    ['data-engineering/partition-planning-and-skew', 'data-engineering/skewed-keys-and-salted-aggregation', 'data-engineering/parquet-row-groups-and-column-pruning', 'data-engineering/spatial-candidate-and-exact-predicate-join', 'data-engineering/delivery-zone-spatial-lake-project'], SPATIAL)

add('spatial-candidate-and-exact-predicate-join', 'Spatial candidate and exact-predicate joins',
    'A spatial join should use cheap coarse tests to limit candidates, then evaluate the true geometry predicate on every candidate that survives.', [
    ('Separate filter from answer', 'Suppose a delivery zone covers a curved district. A bounding rectangle and cell cover are fast to index, but both include places outside the district. First match events against the zone bounding boxes or intersecting cells; only then run the exact geometry test. Report candidate pairs and accepted pairs separately. An approximation is useful when it saves work, but a candidate false positive must not become a published delivery-zone assignment.'),
    ('Include the boundary cells', 'Do not index a polygon only by cells whose centers lie inside it. Narrow portions and border strips can disappear entirely. Build a conservative cover of every cell intersecting the polygon, or expand the search with a verified neighbor rule. After the exact predicate, choose whether a point on the border belongs to one zone, both zones or neither. The ownership rule belongs in the dataset contract, not an accidental library default.'),
    ('Control duplicate matches', 'Overlapping sales territories can legitimately yield two matches for one event. A dispatch zone may require exactly one winner with a deterministic priority and effective-date rule. Never hide overlaps with an arbitrary first row from an unordered join. [[data-engineering/fact-grain-and-measure-additivity|Fact grain]] determines whether one event can contribute to more than one output total; validate that rule before aggregation.'),
    ('Version the shapes', 'A boundary revision changes historical assignments even if no event moved. Store a shape version and effective interval, then join each event to the version valid for its business time or explicitly reprocess affected history. A current map polygon cannot explain an older daily total. Record input event generation, zone-set generation and output generation in the [[data-engineering/run-scoped-lineage-and-release-evidence|release evidence]].'),
    ('Measure selectivity and skew', 'Count the ratio of candidate pairs to exact matches, exact predicate CPU time, cells scanned and the hottest zone. If the coarse cover returns nearly every shape, it is not reducing work. If one dense zone dominates, subdivide it or process its candidates in bounded shards. Reconcile the final set by stable event ID, zone ID and shape version to catch losses at cell edges.')],
    '''# Coordinates are in one local projected plane for this small fixture.
events = {"delivery-47": (4, 3), "delivery-48": (8, 8)}
zones = {"zone-west": [(0, 0), (6, 0), (0, 6)],
         "zone-east": [(7, 7), (12, 7), (12, 12), (7, 12)]}

def inside_polygon(point, vertices):
    east, north = point
    inside = False
    for index, (start_east, start_north) in enumerate(vertices):
        end_east, end_north = vertices[index - 1]
        if (start_north > north) != (end_north > north):
            crossing = start_east + (north - start_north) * (end_east - start_east) / (end_north - start_north)
            if east < crossing:
                inside = not inside
    return inside

def zone_matches(event_points, zone_polygons):
    candidates, matches = [], []
    for delivery_id, point in event_points.items():
        for zone_id, polygon in zone_polygons.items():
            easts, norths = zip(*polygon)
            if min(easts) <= point[0] <= max(easts) and min(norths) <= point[1] <= max(norths):
                candidates.append((delivery_id, zone_id))
                if inside_polygon(point, polygon):
                    matches.append((delivery_id, zone_id))
    return candidates, matches

candidate_pairs, exact_pairs = zone_matches(events, zones)
assert candidate_pairs == [("delivery-47", "zone-west"), ("delivery-48", "zone-east")]
assert exact_pairs == [("delivery-48", "zone-east")]''',
    'A naive join costs O(E × Z) bounding checks for E events and Z zones; an indexed cell or rectangle lookup reduces candidate generation toward the number of actual nearby pairs. Exact predicate cost grows with candidate count and polygon complexity. Building a cover adds storage and update work when boundaries change, so track both false-positive rate and missed-match tests.',
    ['Do not publish bounding-box matches as exact polygon matches.', 'Do not omit intersecting border cells just because their centers are outside.', 'Do not collapse legitimate overlapping-zone matches without a documented winner rule.'],
    ['data-engineering/spatial-cell-resolution-and-hotspot-layout', 'data-engineering/fact-grain-and-measure-additivity', 'data-engineering/run-scoped-lineage-and-release-evidence', 'data-engineering/quality-quarantine-and-reconciliation', 'data-engineering/delivery-zone-spatial-lake-project'], SPATIAL)

add('delivery-zone-spatial-lake-project', 'Project: publish a boundary-safe delivery-zone lake',
    'Build a versioned location dataset whose grid layout stays efficient and whose zone assignments survive edge cases, corrections and shape revisions.', [
    ('Construct the data and contract', 'Create 480 delivery events across three days, including a dense city cell, several sparse rural cells, a point on a zone border and two events with corrected coordinates. Define the coordinate order, supported range, event identity and border ownership rule. Keep a raw copy of rejected coordinates so they can be repaired without inventing a location. [[data-engineering/source-contract-and-raw-landing|The source contract]] is the first validation boundary.'),
    ('Choose and measure layout', 'Compare two grid resolutions with the same time partitions. Record populated cells, average and p95 files per cell, small-file count and bytes scanned for three user queries: one neighborhood, one cross-border radius and one full-city daily aggregate. Give the dense cell a bounded split while keeping sparse cells compact. A resolution that wins only the tiny neighborhood query may still be worse overall.'),
    ('Build exact assignment', 'Generate conservative zone candidates from cell covers or bounding boxes, then run an exact geometry predicate. Plant a false-positive candidate inside a zone rectangle but outside its actual polygon and prove it is rejected. Test the point on the border according to the contract. If two zones overlap, either keep two rows with an explicit multi-membership grain or choose the deterministic priority winner.'),
    ('Replay corrections and shape versions', 'Move one event across a cell and zone boundary, then publish a corrected generation. The old placement must disappear from the current view while remaining queryable through the retained snapshot. Change one polygon effective next day and prove that the earlier day keeps its old assignment. [[data-engineering/lakehouse-snapshot-and-atomic-commit|The atomic snapshot]] prevents readers from seeing only half the move.'),
    ('Deliver a proof bundle', 'Provide the layouts, query costs, candidate-to-exact ratios, border fixtures, duplicate-ID check, old and new assignment sets, input and shape generations, and one failed publish attempt. Show that every accepted event appears in the correct output multiplicity. A map screenshot alone cannot prove no delivery vanished between adjacent cells.')],
    '''raw_deliveries = {"delivery-47": (4, 3), "delivery-48": (8, 8),
                  "delivery-49": (5, 4)}
old_cells = {delivery_id: (int(lon // 4), int(lat // 4))
             for delivery_id, (lon, lat) in raw_deliveries.items()}
corrected_deliveries = {**raw_deliveries, "delivery-49": (9, 4)}
new_cells = {delivery_id: (int(lon // 4), int(lat // 4))
             for delivery_id, (lon, lat) in corrected_deliveries.items()}

assert old_cells["delivery-49"] == (1, 1)
assert new_cells["delivery-49"] == (2, 1)
assert set(old_cells) == set(new_cells)  # move, not duplicate''',
    'Assigning N points to coarse cells is O(N) time and O(N) output state. Exact spatial joining adds candidate generation, polygon checks and versioned output storage. Two resolution trials and retained snapshots increase temporary storage, but reveal whether reduced scan bytes outweigh extra metadata and correction work before the layout becomes a production dependency.',
    ['Do not use a cell-center-only polygon cover.', 'Do not leave the old cell assignment live after a coordinate correction.', 'Do not recompute historical zone totals with an unversioned current polygon.'],
    ['data-engineering/spatial-cell-resolution-and-hotspot-layout', 'data-engineering/spatial-candidate-and-exact-predicate-join', 'data-engineering/lakehouse-snapshot-and-atomic-commit', 'data-engineering/quality-quarantine-and-reconciliation', 'data-engineering/replay-manifest-and-audit-trail'], SPATIAL, True)

add('contract-to-test-compilation-and-negative-fixtures', 'Contract-to-test compilation and negative fixtures',
    'A data contract earns its place in a pipeline when each declared field and rule becomes an executable check with a known failure example.', [
    ('Compile from one declared contract', 'Put column names, types, null policy, key grain, accepted ranges and ownership in a versioned contract. Generate compatible schema checks and data tests from that document instead of maintaining a separate handwritten list that can drift. A column marked required should fail on a missing field and on a null value; those are different failure modes. [[data-engineering/schema-compatibility-and-consumer-rollout|Schema rollout]] still decides when a new rule can reach consumers.'),
    ('Match rule to enforcement layer', 'A storage engine may enforce not-null and uniqueness, but support differs by engine and table format. Run a capability check before treating a declared constraint as physical protection. Row-level predicates, reference checks and cross-table totals usually need query tests. Place cheap structural checks before expensive scans, then run business checks on the candidate release. The contract is a specification; the test result is the evidence.'),
    ('Generate negative fixtures', 'For each rule, create at least one violating record or batch: missing amount, null payment ID, repeated ID, invalid currency and amount outside the accepted interval. Verify each fixture fails for the intended reason. A test suite that passes the current happy-path data can be disconnected from the actual candidate, misconfigured or silently disabled. A controlled failure proves its wiring.'),
    ('Preserve grain and versions', 'Uniqueness must use the business key at the declared grain, perhaps payment ID plus revision, rather than a convenient row number. Name contract version, candidate generation and test runner revision in each result. If the upstream system starts sending a new optional field, do not reject it unless the compatibility policy calls for exact schemas. [[data-engineering/schema-registry-transitive-compatibility|Transitive compatibility]] matters for consumers that skip versions.'),
    ('Budget validation work', 'A full duplicate scan can be costly on a huge history table. Run deterministic checks on changed partitions at each release and schedule broader audits for older data, provided the publication contract permits that split. Sampled validation cannot prove uniqueness. Keep an explicit rule coverage report showing declared rules, generated tests, enforcement locations and unimplemented rules; never mark a partial compiler as complete.')],
    '''payment_contract = {
    "required": ("payment_id", "currency", "amount_cents"),
    "currencies": {"INR", "USD"},
    "minimum_cents": -470000,
    "maximum_cents": 470000,
}

def validate_payment(payment, contract):
    errors = []
    for field in contract["required"]:
        if field not in payment or payment[field] is None:
            errors.append("required:" + field)
    if payment.get("currency") not in contract["currencies"]:
        errors.append("currency")
    amount = payment.get("amount_cents")
    if amount is not None and (not isinstance(amount, int) or isinstance(amount, bool)):
        errors.append("amount_type")
    elif isinstance(amount, int) and not contract["minimum_cents"] <= amount <= contract["maximum_cents"]:
        errors.append("amount_range")
    return errors

valid_payment = {"payment_id": "pay-47", "currency": "INR", "amount_cents": 2375}
assert validate_payment(valid_payment, payment_contract) == []
assert "required:payment_id" in validate_payment({**valid_payment, "payment_id": None}, payment_contract)''',
    'For N records and R simple field rules, direct validation is O(N × R) time and O(F) error output for F failures. Uniqueness and reference checks add key state or index probes. Generating tests reduces drift but cannot make an unsupported database constraint enforceable. Record scan bytes and gate duration alongside failure coverage.',
    ['Do not infer a declared database constraint is enforced on every engine.', 'Do not test only valid rows; verify a negative fixture fails for each rule.', 'Do not declare unique grain using a surrogate row number that is always unique.'],
    ['data-engineering/source-contract-and-raw-landing', 'data-engineering/schema-compatibility-and-consumer-rollout', 'data-engineering/schema-registry-transitive-compatibility', 'data-engineering/contract-gate-severity-and-release-evidence', 'data-engineering/payment-feed-contract-gate-project'], CONTRACTS)

add('contract-gate-severity-and-release-evidence', 'Contract gate severity and release evidence',
    'A candidate dataset should not become the current answer until its required checks pass and any permitted exceptions have named owners and expiry.', [
    ('Separate reject from observe', 'A missing business key or mismatched money total can block publication. A mild distribution shift may warn while the candidate is still usable; an intermediate rule may require a narrow, approved exception. Give each contract rule an owner, severity, scope and threshold before execution. Do not downgrade a failing rule merely to push a late batch through. [[data-engineering/correction-aware-quality-alerts|Correction-aware alerts]] help distinguish a legitimate backfill from a broken source.'),
    ('Bind evidence to the candidate', 'A green test from yesterday is not proof for today’s files. Store candidate generation, contract version, input generations, test runner revision, counts and failure samples in a restricted report. Advance the public pointer only if the report belongs to that exact candidate and every blocking rule passes. [[data-engineering/replay-manifest-and-audit-trail|A replay manifest]] should make the same result reproducible later.'),
    ('Handle exceptions as data', 'Sometimes a source cannot repair a known issue before an agreed deadline. Record a narrowly scoped exception with a rule ID, affected interval, owner, reason and expiration. The gate may apply it only to those rows and that candidate generation. An expired exception fails closed. Keep the original failure count visible so an exception does not make the data appear clean.'),
    ('Test consumers, not only tables', 'A table may pass its schema checks while a dependent dashboard misinterprets a new status value. Include selected consumer queries and metric controls in the release gate for high-impact fields. Verify row policies and masks after a contract change; a new column can escape a broad projection. [[data-engineering/row-policy-and-column-mask-tests|Access tests]] and output tests inspect different failure surfaces.'),
    ('Prove rollback behavior', 'Plant a duplicate payment ID and verify that the candidate stays unpublished while the previous generation serves requests. Repair the duplicate, rerun all applicable checks and then move the pointer atomically. Publish the failure and success evidence under separate attempt IDs. A retry must not reuse a passing result produced for another candidate, even when the scheduled interval is the same.')],
    '''from datetime import date

checks = [
    {"rule": "payment_key_unique", "severity": "block", "passed": True},
    {"rule": "country_mix_shift", "severity": "waivable", "passed": False},
]
exception = {"rule": "country_mix_shift", "owner": "payments-ops",
             "expires": date(2026, 10, 7), "candidate": "payments-47"}

def publishable(results, candidate, exceptions, today):
    for result in results:
        if result["passed"] or result["severity"] == "warn":
            continue
        if result["severity"] == "block":
            return False
        if not (result["severity"] == "waivable"
                and exceptions["rule"] == result["rule"]
                and exceptions["candidate"] == candidate
                and exceptions["owner"]
                and today <= exceptions["expires"]):
            return False
    return True

assert publishable(checks, "payments-47", exception, date(2026, 10, 6))
assert not publishable(checks, "payments-47", exception, date(2026, 10, 8))
assert not publishable([{**checks[0], "passed": False}], "payments-47", exception, date(2026, 10, 6))''',
    'Evaluating R rule results is O(R) time and O(B) state for B blocking failures. The expensive part is producing each result against the candidate data, especially full-key and cross-table reconciliations. Persisting immutable evidence costs storage but prevents a stale pass report from authorizing a different release. Gate time belongs in the pipeline freshness budget.',
    ['Do not reuse a passing report for a different candidate generation.', 'Do not let an exception survive beyond its approved interval and owner.', 'Do not move the serving pointer while a blocking rule still fails.'],
    ['data-engineering/contract-to-test-compilation-and-negative-fixtures', 'data-engineering/quality-quarantine-and-reconciliation', 'data-engineering/correction-aware-quality-alerts', 'data-engineering/replay-manifest-and-audit-trail', 'data-engineering/payment-feed-contract-gate-project'], CONTRACTS)

add('payment-feed-contract-gate-project', 'Project: ship a payment feed with executable contract gates',
    'Turn one payment-feed contract into negative-fixture tests, candidate-specific release evidence and a rollback-safe serving pointer.', [
    ('Write a concrete contract', 'Define payment ID, revision, customer reference, currency, amount in minor units and effective timestamp. Specify the unique grain as payment ID plus revision and state whether a reversal may carry a negative amount. Name two consumer totals that must reconcile. Add field ownership and contract version. [[data-engineering/contract-to-test-compilation-and-negative-fixtures|The compiler]] should emit structural and row checks from this one declaration.'),
    ('Prove tests are wired', 'Load 470 valid payments and create separate negative fixtures for a null ID, duplicate ID plus revision, unsupported currency, invalid amount and missing timestamp. Each fixture must fail the intended rule; passing valid data alone is not evidence. Record which rules run in the warehouse, which run in a validation job and which remain unimplemented. An unimplemented blocking rule stops the release.'),
    ('Construct candidate evidence', 'Build a candidate table without replacing the current pointer. Run key checks, amount totals, null and range checks, and one dependent dashboard query against that candidate. Attach the candidate generation, contract version, runner revision and input positions to the report. Insert a late correction, rerun the checks and prove that the totals change only once. [[data-engineering/idempotent-load-and-checkpoint|Idempotent loading]] is necessary but does not replace result reconciliation.'),
    ('Exercise failure and exception paths', 'Plant one duplicate that blocks publication. Keep the previous generation serving. Separately plant a waivable country-mix rule failure and approve a narrow, time-limited exception with owner and interval. Show that the exception does not suppress the duplicate failure. Expire it and prove that the same rule can no longer be waived. Retain both failed reports.'),
    ('Publish and hand over', 'Repair the duplicate, rerun the full candidate suite and advance the pointer atomically. Query the consumer endpoint and match its generation to the passing report. Submit the contract, generated-rule map, negative-fixture matrix, failure and success reports, exception record, pointer trace, totals and rollback drill. A dashboard that looks correct without a candidate-bound proof does not pass this project.')],
    '''payments = [
    ("pay-47", 1, 2375), ("pay-48", 1, 6400),
    ("pay-49", 1, -125),
]

def payment_gate(records):
    identities = [(payment_id, revision) for payment_id, revision, _ in records]
    if len(identities) != len(set(identities)):
        return {"passed": False, "reason": "duplicate_identity"}
    return {"passed": True, "net_cents": sum(cents for _, _, cents in records)}

assert payment_gate(payments) == {"passed": True, "net_cents": 8650}
assert payment_gate(payments + [("pay-47", 1, 2375)])["reason"] == "duplicate_identity"''',
    'The reference duplicate check uses O(N) expected time and O(N) key space for N payments. Full production checks also scan changed data, join reference sets and run consumer queries; record those bytes and elapsed times separately. A candidate and last-good generation require temporary storage, but allow a failed batch to be rejected without interrupting readers.',
    ['Do not generate tests from a different contract version than the candidate expects.', 'Do not suppress a blocking duplicate with a warning exception.', 'Do not advance the public pointer before the exact candidate passes.'],
    ['data-engineering/contract-to-test-compilation-and-negative-fixtures', 'data-engineering/contract-gate-severity-and-release-evidence', 'data-engineering/payment-quality-release-project', 'data-engineering/idempotent-load-and-checkpoint', 'data-engineering/replay-manifest-and-audit-trail'], CONTRACTS, True)


CROSSLINKS = [
    ('data-engineering/partition-planning-and-skew', 'data-engineering/spatial-cell-resolution-and-hotspot-layout'),
    ('data-engineering/skewed-keys-and-salted-aggregation', 'data-engineering/spatial-cell-resolution-and-hotspot-layout'),
    ('data-engineering/fact-grain-and-measure-additivity', 'data-engineering/spatial-candidate-and-exact-predicate-join'),
    ('data-engineering/quality-quarantine-and-reconciliation', 'data-engineering/spatial-candidate-and-exact-predicate-join'),
    ('data-engineering/lakehouse-snapshot-and-atomic-commit', 'data-engineering/delivery-zone-spatial-lake-project'),
    ('data-engineering/external-telemetry-catalog-project', 'data-engineering/delivery-zone-spatial-lake-project'),
    ('data-engineering/source-contract-and-raw-landing', 'data-engineering/contract-to-test-compilation-and-negative-fixtures'),
    ('data-engineering/schema-registry-transitive-compatibility', 'data-engineering/contract-to-test-compilation-and-negative-fixtures'),
    ('data-engineering/correction-aware-quality-alerts', 'data-engineering/contract-gate-severity-and-release-evidence'),
    ('data-engineering/row-policy-and-column-mask-tests', 'data-engineering/contract-gate-severity-and-release-evidence'),
    ('data-engineering/payment-quality-release-project', 'data-engineering/payment-feed-contract-gate-project'),
    ('data-engineering/replay-manifest-and-audit-trail', 'data-engineering/payment-feed-contract-gate-project'),
]


if __name__ == '__main__':
    publish(LESSONS, (SPATIAL, CONTRACTS), CROSSLINKS,
            'aitrove-data-engineering-spatial-contracts-import-20261006.json', 7920)
