"""Publish original distributed-execution and warehouse-modeling lessons."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'src/data/fixtures.json'
HUB = 'data-engineering/data-engineering-tutorial'
PROJECT_HUB = HUB + '/project'
LESSONS = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    LESSONS.append(dict(path='data-engineering/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add('shuffle-boundaries-and-local-combiners', 'Shuffle boundaries and local combiners',
    'A distributed shuffle redistributes records by key so each reducer can see all values for its assigned keys.', [
    ('Find the network boundary', 'A row filter or projection can run inside each input partition. Grouping receipts by account cannot: one account may appear on 47 workers, so partial results must meet at a shared reducer. Mark that boundary in the execution plan and count bytes crossing it. [[data-engineering/partition-planning-and-skew|Table partition design]] helps reads; it does not guarantee the compute engine has already colocated every grouping key.'),
    ('Reduce before transfer', 'For associative operations such as integer sum, each mapper can collapse many receipt rows into one account subtotal before the shuffle. If a worker reads 83 lines for one account, it can send one subtotal. The reducer combines those subtotals. An average needs both sum and count; averaging mapper averages gives the wrong answer when mapper sizes differ.'),
    ('Keep exactness in the reduction law', 'A combiner must be safe under arbitrary partitioning and repeated merge order. Integer addition works within its range. Distinct counts do not combine by summing counts because the same ID can occur on several workers. Use an exact set when bounded, or an explicitly approximate sketch when the product accepts error. Document overflow and decimal rounding for financial totals.'),
    ('Observe the plan, not a slogan', 'Record input rows, mapper output records, shuffle bytes, reducer spill and longest task duration. If local combining barely reduces bytes because most keys appear once per partition, the added CPU may not be worthwhile. Large reducers can spill to disk even when total cluster memory looks free; [[data-engineering/skewed-keys-and-salted-aggregation|hot-key analysis]] explains why.'),
    ('Make reruns comparable', 'Pin the input snapshot, code revision and partitioning configuration when comparing a tuned job with its baseline. A later source correction can change both byte volume and result. Validate the output count and checksum through [[data-engineering/replay-manifest-and-audit-trail|a replay manifest]], then change one execution variable at a time.')],
    '''from collections import defaultdict

receipt_partitions = [
    [("acct-47", 4300), ("acct-47", 2700), ("acct-83", 1900)],
    [("acct-47", 1200), ("acct-83", 900)],
]

def local_subtotals(partitions):
    partials = []
    for partition in partitions:
        subtotal = defaultdict(int)
        for account_id, amount_cents in partition:
            subtotal[account_id] += amount_cents
        partials.extend(subtotal.items())
    return partials

shuffled = local_subtotals(receipt_partitions)
assert len(shuffled) == 4
assert sum(amount for account, amount in shuffled if account == "acct-47") == 8200''',
    'Reading N rows is O(N) time; local maps hold O(Kp) keys per partition. If there are P partitions and K keys, the network sends at most P × K partials rather than N rows, although it can send nearly N when keys rarely repeat. The reducer still needs memory or spill space for its assigned key groups.',
    ['Do not average partial averages without their counts.', 'Do not assume a table partition removes a compute shuffle.', 'Do not tune from wall time alone while spill and correctness are unmeasured.'],
    ['data-engineering/partition-planning-and-skew', 'data-engineering/skewed-keys-and-salted-aggregation', 'data-engineering/broadcast-join-and-build-side-limits', 'data-engineering/distributed-invoice-rollup-project', 'data-engineering/replay-manifest-and-audit-trail'], 'Distributed execution and data movement')

add('broadcast-join-and-build-side-limits', 'Broadcast joins and build-side limits',
    'A broadcast join copies a bounded lookup relation to workers so large fact partitions can join locally without shuffling the fact side.', [
    ('Choose by measured bytes', 'A merchant lookup with 240 records may be small in source storage but much larger after deserialization or expansion. Measure the encoded and in-memory size, then enforce a cap before broadcasting. A join hint is a request to the planner, not proof that the chosen plan fits executor memory. Inspect the executed plan and task memory profile.'),
    ('Check cardinality first', 'One lookup row per merchant key is required when each order line should remain one row. If the lookup contains two active records for the same merchant, broadcasting makes the wrong multiplication faster. Reject duplicate business keys or first resolve a temporal version using [[data-engineering/warehouse-history-asof-join|an as-of rule]]. Check source and result row counts.'),
    ('Account for missing keys', 'A left join should preserve every fact, including a merchant not present in the lookup. Represent the unresolved member explicitly rather than silently dropping that order. A later lookup correction may require a targeted repair. [[data-engineering/late-arriving-dimensions-and-fact-repair|Late dimension repair]] owns that lifecycle.'),
    ('Understand the cost switch', 'Broadcasting B bytes to W workers costs roughly B × W network and memory exposure. Shuffling a large fact of F bytes may cost far more, but broadcasting a growing table can cause driver or executor failure. A sampled byte estimate, a safety margin and a fallback shuffle strategy are more reliable than a fixed row-count threshold.'),
    ('Test under skew', 'Broadcast can remove fact-side movement for the join, but a downstream group-by may still concentrate one account on a reducer. Treat the join and aggregate as separate plan stages. Compare output keys, unmatched facts, shuffle bytes and p95 task duration before publishing the change.')],
    '''merchant_rows = [
    {"merchant_id": "m-47", "region": "north"},
    {"merchant_id": "m-83", "region": "west"},
]
order_lines = [
    {"line_id": "line-47", "merchant_id": "m-47", "amount_cents": 7300},
    {"line_id": "line-48", "merchant_id": "m-99", "amount_cents": 1200},
]

def enrich_orders(facts, lookup_rows):
    lookup = {row["merchant_id"]: row["region"] for row in lookup_rows}
    if len(lookup) != len(lookup_rows):
        raise ValueError("merchant lookup key is not unique")
    return [{**fact, "region": lookup.get(fact["merchant_id"], "unknown")}
            for fact in facts]

enriched = enrich_orders(order_lines, merchant_rows)
assert len(enriched) == len(order_lines)
assert enriched[1]["region"] == "unknown"''',
    'Building the lookup takes O(B) time and space for B lookup rows; probing F fact rows takes O(F) expected time locally. In a cluster, each worker retains its own copy, so aggregate memory approaches W × B. Missing-key and duplicate-key checks protect correctness independently of the planner choice.',
    ['Do not broadcast from a row-count guess without a byte and memory cap.', 'Do not let duplicate lookup keys multiply financial facts.', 'Do not claim the entire job is shuffle-free because one join is local.'],
    ['data-engineering/shuffle-boundaries-and-local-combiners', 'data-engineering/skewed-keys-and-salted-aggregation', 'data-engineering/late-arriving-dimensions-and-fact-repair', 'data-engineering/distributed-invoice-rollup-project', 'data-engineering/warehouse-history-asof-join'], 'Distributed execution and data movement')

add('skewed-keys-and-salted-aggregation', 'Skewed keys and salted aggregation',
    'A skewed key sends a disproportionate share of records to one task, making that task set the runtime and spill risk of the stage.', [
    ('Measure the heavy tail', 'A cluster can report 70% idle capacity while one reducer handles 63% of invoice rows for an umbrella account. Inspect per-task input bytes, spill and duration, then compare key frequency from the actual interval. The mean partition size hides the long tail. [[data-engineering/partition-planning-and-skew|Storage skew]] and execution skew are related but measured at different boundaries.'),
    ('Salt a decomposable calculation', 'For an associative sum, spread a heavy account across several deterministic subkeys derived from immutable invoice ID, compute partial sums, then merge them by the original account. The salt must be stable on retry. Random salt changes task assignment and makes incident replay harder, even if the final integer sum happens to match.'),
    ('Keep the identity intact', 'Salting is an execution detail, not a new business key. The published table still has one row per account and day. After merging salts, assert uniqueness at that grain and reconcile total cents with the unsalted input. A distinct-customer count cannot be repaired by adding salted distinct counts because the same customer may occur in several salts.'),
    ('Compare alternatives', 'Adaptive skew handling, a broadcast lookup, preaggregation, or separate treatment of a small set of heavy keys may be simpler. Salting every key adds an extra grouping stage and can worsen small jobs. Begin with the executed plan and tune only the measured bottleneck; [[data-engineering/shuffle-boundaries-and-local-combiners|local combiners]] may cut traffic before any salting.'),
    ('Bound the split', 'Eight salt buckets can reduce one reducer input, but they also create eight partial states and a second merge. Choose a bucket count from the heavy key size and target task size. Monitor the largest salted bucket, not just the average, because poor hash distribution or a low-cardinality event ID can preserve skew.')],
    '''from collections import defaultdict
from hashlib import sha256

invoice_lines = [
    {"invoice_id": "inv-47", "account": "parent-9", "cents": 4200},
    {"invoice_id": "inv-48", "account": "parent-9", "cents": 3100},
    {"invoice_id": "inv-49", "account": "parent-9", "cents": 1800},
]

def salted_totals(lines, buckets=4):
    partial = defaultdict(int)
    for line in lines:
        salt = int.from_bytes(sha256(line["invoice_id"].encode()).digest()[:4], "big") % buckets
        partial[(line["account"], salt)] += line["cents"]
    merged = defaultdict(int)
    for (account, _salt), cents in partial.items():
        merged[account] += cents
    return dict(merged)

assert salted_totals(invoice_lines) == {"parent-9": 9100}''',
    'Hashing N invoice IDs and summing values is O(N) expected time, with O(K × S) partial state for K heavy keys and S salts. The second grouping adds shuffle and task overhead. This only helps when it lowers the largest task enough to outweigh that overhead.',
    ['Do not salt a non-decomposable metric and sum its partial answers.', 'Do not publish salted keys as customer identities.', 'Do not select bucket count from averages while the largest task still spills.'],
    ['data-engineering/shuffle-boundaries-and-local-combiners', 'data-engineering/partition-planning-and-skew', 'data-engineering/broadcast-join-and-build-side-limits', 'data-engineering/distributed-invoice-rollup-project', 'data-engineering/fact-grain-and-measure-additivity'], 'Distributed execution and data movement')

add('task-retries-and-atomic-partition-output', 'Task retries and atomic partition output',
    'A distributed task can run more than once, so its candidate files and publication step must prevent duplicate or partial output.', [
    ('Assume repeated attempts', 'A worker may write a file and lose its completion acknowledgement. The scheduler retries on another worker; both attempts can now exist. If a reader lists every file in a directory, it may count the partition twice. Assign each attempt a private path and publish only one accepted attempt through a manifest or transactional table commit.'),
    ('Separate compute from commit', 'A task result is a candidate until the coordinator validates it. Capture task identity, attempt ID, input snapshot, row count and digest. The commit layer selects one accepted attempt per task and publishes a single generation pointer. [[data-engineering/lakehouse-snapshot-and-atomic-commit|Snapshot publication]] keeps readers on the last complete generation while the new one is checked.'),
    ('Make cleanup conservative', 'An abandoned attempt file is not necessarily safe to delete while its writer or a delayed coordinator is still active. Use an age threshold beyond the maximum attempt lifetime, then compare files against all live manifests. Log the proposed deletions before applying them. [[data-engineering/compaction-retention-and-replay-horizon|Retention rules]] must cover retry and rollback windows.'),
    ('Reconcile at the output grain', 'For a daily invoice partition, check one row per invoice line or one row per account-day according to the declared target grain. Validate row count and total cents against the pinned input. A successful task state does not prove all expected partitions committed. [[data-engineering/quality-quarantine-and-reconciliation|Quality gates]] should precede the final pointer update.'),
    ('Inject the uncertain outcome', 'Test a failure after the file write and before acknowledgement. Two candidate attempts should appear, yet the published manifest should contain exactly one for that task. Rerun from the same input snapshot and compare the canonical output digest; a new source snapshot is a new run, not an idempotent retry.')],
    '''task_attempts = [
    {"task": "day-47-part-2", "attempt": 1, "file": "candidate-a", "valid": True},
    {"task": "day-47-part-2", "attempt": 2, "file": "candidate-b", "valid": True},
    {"task": "day-47-part-3", "attempt": 1, "file": "candidate-c", "valid": True},
]

def accepted_manifest(attempts):
    accepted = {}
    for attempt in sorted(attempts, key=lambda row: (row["task"], row["attempt"])):
        if attempt["valid"]:
            accepted.setdefault(attempt["task"], attempt["file"])
    return accepted

manifest = accepted_manifest(task_attempts)
assert manifest == {"day-47-part-2": "candidate-a", "day-47-part-3": "candidate-c"}
assert "candidate-b" not in manifest.values()''',
    'Sorting A attempt records costs O(A log A) and the manifest uses O(T) space for T logical tasks. A production coordinator may use keyed storage instead, but still needs durable conflict handling. Candidate files temporarily increase storage; that is preferable to silently publishing two attempts.',
    ['Do not expose candidate directories as committed datasets.', 'Do not equate one successful attempt with one accepted output.', 'Do not delete unreferenced files before in-flight attempts are ruled out.'],
    ['data-engineering/lakehouse-snapshot-and-atomic-commit', 'data-engineering/dag-intervals-and-idempotent-tasks', 'data-engineering/quality-quarantine-and-reconciliation', 'data-engineering/distributed-invoice-rollup-project', 'data-engineering/replay-manifest-and-audit-trail'], 'Distributed execution and data movement')

add('distributed-invoice-rollup-project', 'Project: release a distributed invoice rollup',
    'Build an account-day invoice rollup that handles skew, bounded lookups, task retries and one atomic publication boundary.', [
    ('Define the release unit', 'A finance consumer reads one total per account and event day from an immutable source snapshot. Input invoice lines carry invoice ID, account, merchant ID, day and integer cents. The merchant lookup has one row per key and a measured broadcast size. Write the target grain and uniqueness assertion before selecting a compute framework.'),
    ('Build the execution plan', 'Filter invalid lines into quarantine, enrich valid lines with the bounded merchant lookup, locally combine cents, and salt only the observed heavy account. Merge salts back to account-day. Capture mapper output count, shuffle bytes, largest reducer bytes and unmatched merchant count. [[data-engineering/shuffle-boundaries-and-local-combiners|Combining]] and [[data-engineering/skewed-keys-and-salted-aggregation|salting]] solve different parts of the plan.'),
    ('Publish once', 'Write candidate partition files under run and attempt IDs. Validate one row per target key, input-to-output total cents and completeness of every expected partition. A coordinator publishes one manifest referencing accepted files. A reader pinned to the previous manifest must never see half the new rollup. [[data-engineering/task-retries-and-atomic-partition-output|Attempt selection]] prevents duplicate output after a lost acknowledgement.'),
    ('Inject failures', 'Duplicate a merchant lookup key and confirm the run stops before enrichment. Kill one task after its candidate file appears, then retry and verify only one accepted file. Make the heavy account hold 61% of rows and compare p95 task time with and without salting; preserve identical totals and target keys.'),
    ('Deliver evidence', 'Include the source and lookup contracts, a physical plan before and after tuning, measured task distributions, one published manifest, a reconciliation report and an exact retry from pinned inputs. If the production engine changes its plan through adaptive execution, record the executed plan rather than only the submitted SQL.')],
    '''from collections import defaultdict

invoice_lines = [
    {"id": "inv-47", "account": "acct-47", "day": 47, "cents": 3200},
    {"id": "inv-48", "account": "acct-47", "day": 47, "cents": 4700},
    {"id": "inv-83", "account": "acct-83", "day": 47, "cents": 2100},
]

def release_totals(lines):
    if len({line["id"] for line in lines}) != len(lines):
        raise ValueError("duplicate invoice identity")
    totals = defaultdict(int)
    for line in lines:
        totals[(line["account"], line["day"])] += line["cents"]
    if sum(totals.values()) != sum(line["cents"] for line in lines):
        raise ValueError("reconciliation failed")
    return dict(totals)

assert release_totals(invoice_lines)[("acct-47", 47)] == 7900''',
    'The local reference calculation is O(N) expected time and O(A) memory for N lines and A account-day keys. A distributed release also pays for shuffle bytes, attempt files, validation scans and manifest storage. Tune to the slowest task and preserve the same published result.',
    ['Do not optimize away duplicate-key checks to make a join faster.', 'Do not compare plans from different input snapshots as if only code changed.', 'Do not let task attempts write directly into the reader-visible partition.'],
    ['data-engineering/shuffle-boundaries-and-local-combiners', 'data-engineering/broadcast-join-and-build-side-limits', 'data-engineering/skewed-keys-and-salted-aggregation', 'data-engineering/task-retries-and-atomic-partition-output', 'data-engineering/lakehouse-snapshot-and-atomic-commit'], 'Distributed execution and data movement', True)

add('fact-grain-and-measure-additivity', 'Fact grain and measure additivity',
    'A fact grain states what one row represents; a measure is additive only across dimensions where summing preserves its business meaning.', [
    ('Declare a row before the schema', 'A payment fact may be one row per captured payment, not per order or customer. An order with two captures must therefore have two payment rows. Store the stable capture ID and test its uniqueness. Joining order lines directly to captures creates a many-to-many multiplication unless each side is reduced to a compatible grain. [[data-science/dataset-grain-and-join-cardinality|Join cardinality]] is an executable contract.'),
    ('Classify measures by direction', 'Captured cents can be summed across customers and days if corrections and currency are handled consistently. An end-of-day account balance can be summed across accounts for one day, but summing balances across days double-counts the same money; it is semi-additive. A conversion rate is a ratio and cannot be summed at all. Store numerator and denominator at a clear grain.'),
    ('Separate transactions from snapshots', 'An event fact records that something happened at a time. A periodic snapshot records state at a cutoff. Mixing them in one table invites a dashboard to add balances to transaction amounts. If both are needed, publish separate fact tables with distinct names, keys and time columns. [[data-engineering/replay-manifest-and-audit-trail|The run manifest]] should name the cutoff for each snapshot.'),
    ('Handle corrections explicitly', 'A captured payment may later be reversed. Choose whether the fact contains a signed reversal event or a mutable current status, and define how finance totals use it. A silent overwrite can make last month change with no trace. A new correcting event retains the transaction trail but demands a clear netting rule. [[data-engineering/cdc-replay-and-deletes|CDC]] carries the source mutation; the mart defines its analytical meaning.'),
    ('Prove totals at two grains', 'Reconcile source captures to fact rows by capture ID, then aggregate fact cents by day and compare with the authorized ledger for the same cutoff and currency. Test a split capture, a reversal and a zero-activity day. A row-count match alone cannot detect duplicated amounts or wrong signs.')],
    '''captures = [
    {"capture_id": "cap-47", "order_id": "ord-9", "day": 47, "cents": 4200},
    {"capture_id": "cap-48", "order_id": "ord-9", "day": 47, "cents": 1700},
    {"capture_id": "rev-49", "order_id": "ord-9", "day": 48, "cents": -900},
]

def net_cents_by_day(rows):
    if len({row["capture_id"] for row in rows}) != len(rows):
        raise ValueError("capture grain violated")
    totals = {}
    for row in rows:
        totals[row["day"]] = totals.get(row["day"], 0) + row["cents"]
    return totals

assert net_cents_by_day(captures) == {47: 5900, 48: -900}''',
    'One pass over N captures takes O(N) expected time and O(D + N) memory for D days plus the uniqueness set. Warehouse aggregation may push this work into the query engine, but a badly chosen grain creates incorrect results regardless of compute speed.',
    ['Do not sum periodic balances across dates.', 'Do not join facts at incompatible grains without a cardinality rule.', 'Do not call a rate an additive fact or average rates without denominators.'],
    ['data-engineering/conformed-dimensions-and-surrogate-keys', 'data-engineering/late-arriving-dimensions-and-fact-repair', 'data-engineering/semantic-metric-contract-and-reconciliation', 'data-engineering/revenue-mart-release-project', 'data-science/dataset-grain-and-join-cardinality'], 'Warehouse models and metric contracts')

add('conformed-dimensions-and-surrogate-keys', 'Conformed dimensions and surrogate keys',
    'A conformed dimension gives related facts one governed definition of an entity and its attributes, while surrogate keys identify warehouse rows independently of source identifiers.', [
    ('Resolve identity before sharing it', 'Two source systems can both call a customer 47. Never join on that bare value. Carry source namespace and source customer ID through landing, map them to a governed customer identity, then apply an explicit merge or separation rule. Ambiguous matches belong in a review queue. [[data-science/identifier-normalization-and-exact-linkage|Exact linkage]] shows why a convenient string match can create false merges.'),
    ('Keep the warehouse key stable', 'A generated customer dimension key can remain stable even when the source changes its display name or ID format. For a Type 2 history, each valid version receives a separate surrogate key while the durable business identity groups versions. Facts use the version key valid at their event time. [[data-engineering/warehouse-history-asof-join|The as-of join]] supplies the selection rule.'),
    ('Conform only what is truly shared', 'The finance and support marts might agree on customer identity and home region but disagree on account status at different cutoffs. Put shared definitions in one conformed dimension; keep mart-specific classifications separate or versioned. A shared column name without a common business rule is a false contract.'),
    ('Track unknowns deliberately', 'A fact can arrive before its customer dimension. Map it to a governed unknown member and retain the natural source key for later repair. Do not reuse one unknown row to imply all such facts came from the same customer. [[data-engineering/late-arriving-dimensions-and-fact-repair|The repair process]] must update the fact reference without changing the fact measure.'),
    ('Audit version ranges', 'For each durable identity, effective intervals must not overlap; if the product demands full temporal coverage, detect gaps too. Preserve the previous version when a new one begins. Validate that every fact maps to exactly one version at its event timestamp, then compare historical reports before and after migration.')],
    '''customer_versions = [
    {"source": "billing", "source_id": "47", "dim_key": 701, "start": 40, "end": 50},
    {"source": "billing", "source_id": "47", "dim_key": 702, "start": 50, "end": None},
    {"source": "support", "source_id": "47", "dim_key": 903, "start": 40, "end": None},
]

def dimension_key(versions, source, source_id, event_day):
    matches = [row for row in versions
               if row["source"] == source and row["source_id"] == source_id
               and row["start"] <= event_day
               and (row["end"] is None or event_day < row["end"])]
    if len(matches) != 1:
        raise ValueError("dimension lookup must resolve exactly one version")
    return matches[0]["dim_key"]

assert dimension_key(customer_versions, "billing", "47", 51) == 702
assert dimension_key(customer_versions, "support", "47", 51) == 903''',
    'This small scan is O(V) per fact for V dimension versions; a warehouse should index or partition by namespaced business key and effective range. Durable identity mapping and version history add storage, but prevent false joins and historical relabeling.',
    ['Do not merge identical source IDs from unrelated systems.', 'Do not reuse one version surrogate key after an attribute change that requires history.', 'Do not assume shared column names imply shared business meaning.'],
    ['data-engineering/warehouse-history-asof-join', 'data-engineering/late-arriving-dimensions-and-fact-repair', 'data-engineering/fact-grain-and-measure-additivity', 'data-engineering/revenue-mart-release-project', 'data-science/identifier-normalization-and-exact-linkage'], 'Warehouse models and metric contracts')

add('late-arriving-dimensions-and-fact-repair', 'Late-arriving dimensions and fact repair',
    'A late-arriving dimension is an entity description that becomes available after facts referencing that entity have already reached the warehouse.', [
    ('Keep the fact visible without inventing attributes', 'An invoice event for merchant m-99 can be complete even when the merchant catalog is delayed. Publish the fact with an explicit unknown dimension key and retain the source merchant key. Do not assign it to a nearby merchant name; that turns missing reference data into a false assertion. [[data-engineering/dependency-readiness-and-source-freshness|Readiness policy]] decides whether the mart may publish with unknowns.'),
    ('Distinguish absent from invalid', 'A source identifier that is well formed but not yet in a completed dimension snapshot is late; one that violates the source contract is invalid. Set an age or count threshold for unresolved facts. Quarantine impossible identifiers, but route plausible late facts to a repair queue. Record the source snapshot and first-seen time so the operator can distinguish delivery lag from permanent drift.'),
    ('Repair references, not measures', 'When the merchant row arrives, select the version valid for each fact event timestamp and replace the unknown surrogate key. Preserve invoice ID, cents and event time. If the dimension has multiple historical versions, resolving every fact to the current version corrupts earlier regional totals. [[data-engineering/conformed-dimensions-and-surrogate-keys|Versioned keys]] make that choice explicit.'),
    ('Avoid double publication', 'A repair job should update or atomically replace targeted fact rows under their stable grain. Appending corrected copies produces two facts unless all consumers filter old generations. Pin the input facts and dimension snapshot; validate unresolved count falls and total invoice cents stays unchanged. [[data-engineering/lakehouse-snapshot-and-atomic-commit|Snapshot commit]] shields readers from a half-repaired mart.'),
    ('Retain an audit trail', 'Record the old key, new key, affected fact IDs, dimension version and repair run ID. A downstream report may need restatement because grouping changed even though total cents did not. Link that restatement to [[data-engineering/replay-manifest-and-audit-trail|the manifest]] and notify owners through lineage rather than silently replacing history.')],
    '''UNKNOWN_MERCHANT = 0
fact_rows = [
    {"invoice_id": "inv-47", "merchant_source": "m-99", "merchant_key": 0, "event_day": 47, "cents": 5800},
    {"invoice_id": "inv-83", "merchant_source": "m-31", "merchant_key": 331, "event_day": 47, "cents": 2100},
]
merchant_versions = [
    {"merchant_source": "m-99", "start": 40, "end": 50, "dim_key": 991},
]

def matching_version(versions, merchant_source, event_day):
    matches = [row["dim_key"] for row in versions
               if row["merchant_source"] == merchant_source
               and row["start"] <= event_day < row["end"]]
    if len(matches) > 1:
        raise ValueError("overlapping merchant versions")
    return matches[0] if matches else UNKNOWN_MERCHANT

def repair_merchant_keys(facts, versions):
    repaired = []
    for fact in facts:
        updated = dict(fact)
        if updated["merchant_key"] == UNKNOWN_MERCHANT:
            updated["merchant_key"] = matching_version(
                versions, updated["merchant_source"], updated["event_day"])
        repaired.append(updated)
    return repaired

fixed = repair_merchant_keys(fact_rows, merchant_versions)
assert fixed[0]["merchant_key"] == 991
assert sum(row["cents"] for row in fixed) == sum(row["cents"] for row in fact_rows)''',
    'Scanning N candidate facts is O(N) expected time with a keyed dimension lookup and O(N) output space. In production, target only unresolved keys and use a version-aware index; repeated full-table repair scans waste compute. Restatement work can exceed the key update itself.',
    ['Do not guess a dimension from a similar name.', 'Do not point old facts to the dimension version current today.', 'Do not append repaired facts beside the old generation.'],
    ['data-engineering/conformed-dimensions-and-surrogate-keys', 'data-engineering/warehouse-history-asof-join', 'data-engineering/fact-grain-and-measure-additivity', 'data-engineering/semantic-metric-contract-and-reconciliation', 'data-engineering/revenue-mart-release-project'], 'Warehouse models and metric contracts')

add('semantic-metric-contract-and-reconciliation', 'Semantic metric contracts and reconciliation',
    'A metric contract fixes the numerator, denominator, grain, time basis, filters and source version so different reports compute the same number.', [
    ('Define the measure as an operation', 'A payment success rate could divide successful capture attempts by eligible attempts, distinct orders, or unique customers. Those are different metrics. State the event unit, which statuses count, whether retries are separate attempts, how reversals appear and which event-time window applies. [[data-science/metric-denominator-and-cohort|Denominator design]] should be versioned with the same care as a source schema.'),
    ('Preserve components', 'Store or expose the additive numerator and denominator; compute the ratio after aggregation. If one region has 3 successes from 4 attempts and another has 27 from 36, the combined rate is 30 from 40, not the unweighted mean of 75% and 75% by coincidence. Unequal rates reveal the error immediately. Do not add or average published percentages without their weights.'),
    ('Choose one clock', 'An event-time daily rate may change when late payment responses arrive. Define a cutoff and correction window. A processing-time report answers a different question. Attach the source snapshot and metric definition version to exported results so an analyst can reproduce the observed value. [[data-engineering/event-time-and-late-arrivals|Late-arrival policy]] controls restatement.'),
    ('Reconcile each boundary', 'Count source attempts, excluded tests, eligible attempts, successful attempts and published metric rows. Require the categories to balance at their stated grain. Compare warehouse components with the source ledger for the same interval and snapshot. If a dimension repair reassigns a region, total attempts should stay fixed while regional buckets change.'),
    ('Release a contract test', 'Use a fixture containing an approved capture, a declined capture, a retry, a reversed capture and an ineligible test event. Assert both component counts and final ratio. Fail publication when eligibility or join cardinality changes unexpectedly. [[data-engineering/pipeline-slos-and-error-budgets|The pipeline SLO]] should require a usable metric, not merely a completed query.')],
    '''payment_attempts = [
    {"id": "pay-47", "eligible": True, "success": True},
    {"id": "pay-48", "eligible": True, "success": False},
    {"id": "pay-49", "eligible": True, "success": True},
    {"id": "test-50", "eligible": False, "success": True},
]

def success_components(attempts):
    if len({row["id"] for row in attempts}) != len(attempts):
        raise ValueError("duplicate attempt identity")
    eligible = [row for row in attempts if row["eligible"]]
    return sum(row["success"] for row in eligible), len(eligible)

successful, eligible = success_components(payment_attempts)
assert (successful, eligible) == (2, 3)
def success_rate(attempts):
    numerator, denominator = success_components(attempts)
    return None if denominator == 0 else numerator / denominator

assert success_rate(payment_attempts) == 2 / 3
assert success_rate([]) is None''',
    'Scanning N attempts takes O(N) expected time and O(N) memory for identity validation. The ratio calculation is O(1), but computing it from an incorrectly joined or stale cohort is still wrong. Retaining component counts and versions adds modest storage and major audit value.',
    ['Do not average regional rates without eligible-attempt weights.', 'Do not substitute distinct orders for capture attempts without a definition change.', 'Do not publish a metric without its cutoff and source version.'],
    ['data-engineering/fact-grain-and-measure-additivity', 'data-engineering/conformed-dimensions-and-surrogate-keys', 'data-engineering/late-arriving-dimensions-and-fact-repair', 'data-engineering/revenue-mart-release-project', 'data-science/metric-denominator-and-cohort'], 'Warehouse models and metric contracts')

add('revenue-mart-release-project', 'Project: release a reconciled revenue mart',
    'Build an invoice and payment mart with declared fact grain, versioned customer identities, late-dimension repair and one metric contract.', [
    ('Write the contract', 'Use one fact row per capture event and a stable capture ID. Carry signed cents, event time, source position, customer source namespace and natural key. A customer dimension has a durable identity plus surrogate keys for historical versions. State which time the revenue report uses and whether reversal events net against the original day or the reversal day.'),
    ('Build the load', 'Land raw captures, deduplicate by capture ID and source position, resolve the dimension version valid at capture time, and stage the fact table. Use an explicit unknown member for late customers. Reconcile accepted plus quarantined records with the source interval and compare signed cents before publication. [[data-engineering/fact-grain-and-measure-additivity|The grain contract]] prevents many-to-many joins from inflating revenue.'),
    ('Define a consumer metric', 'Publish net captured cents and eligible attempt counts as components, then calculate payment success rate from those components. Keep metric version, source snapshot, cutoff and currency rule beside the release. [[data-engineering/semantic-metric-contract-and-reconciliation|The metric contract]] should identify a reversal and an ineligible test event unambiguously.'),
    ('Inject change and lateness', 'Create two captures for one order, reverse part of one capture, then deliver a customer region change whose effective time falls between the two. Delay the customer dimension for one capture. Verify that its fact remains visible under unknown, a later repair changes only its dimension key, and the total cents remain identical.'),
    ('Prove the release', 'Supply source and target schemas, grain and key assertions, as-of lookup tests, the unresolved-member queue, reconciliation by day and currency, a metric fixture, and two versioned snapshots before and after repair. The consumer should see one complete version at a time. Record an operator path for a source correction that arrives after the normal window.')],
    '''captures = [
    {"capture_id": "cap-47", "customer": "cust-7", "day": 47, "cents": 6100},
    {"capture_id": "cap-48", "customer": "cust-7", "day": 47, "cents": 2400},
    {"capture_id": "rev-49", "customer": "cust-7", "day": 48, "cents": -1100},
]

def revenue_release(rows):
    if len({row["capture_id"] for row in rows}) != len(rows):
        raise ValueError("capture grain violated")
    by_day = {}
    for row in rows:
        by_day[row["day"]] = by_day.get(row["day"], 0) + row["cents"]
    assert sum(by_day.values()) == sum(row["cents"] for row in rows)
    return by_day

assert revenue_release(captures) == {47: 8500, 48: -1100}''',
    'The reference aggregation is O(N) expected time and O(N + D) memory for N captures and D days. A production mart also pays for version-aware dimension lookups, validation, retained snapshots and restatements. Fast queries do not compensate for an undefined grain or unreconciled source.',
    ['Do not collapse two captures into one order row without a written measure rule.', 'Do not overwrite old region history when the customer moves.', 'Do not silently suppress a fact just because its dimension is late.'],
    ['data-engineering/fact-grain-and-measure-additivity', 'data-engineering/conformed-dimensions-and-surrogate-keys', 'data-engineering/late-arriving-dimensions-and-fact-repair', 'data-engineering/semantic-metric-contract-and-reconciliation', 'data-engineering/lakehouse-snapshot-and-atomic-commit'], 'Warehouse models and metric contracts', True)


def publish():
    rows = json.loads(FIXTURE.read_text())
    new_paths = {item['path'] for item in LESSONS}
    assert len(new_paths) == len(LESSONS)
    rows = [row for row in rows if row['path'] not in new_paths]
    by_path = {row['path']: row for row in rows}
    titles = {path: row['title'] for path, row in by_path.items()}
    titles.update({item['path']: item['title'] for item in LESSONS})
    now = datetime.datetime.now(datetime.UTC).isoformat()

    def prose(value):
        return re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',
                      lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                      html.escape(value))

    def link_list(targets):
        return '<ul>' + ''.join('<li><a href="/' + target + '">' +
                              html.escape(titles[target]) + '</a></li>' for target in targets) + '</ul>'

    changed = set(new_paths) | {HUB, PROJECT_HUB}
    for index, item in enumerate(LESSONS):
        body = '<p>' + html.escape(item['summary']) + '</p>'
        for heading, paragraph in item['sections']:
            body += '<h2>' + html.escape(heading) + '</h2><p>' + prose(paragraph) + '</p>'
        body += ('<h2>Implementation</h2><pre><code class="language-python">' +
                 html.escape(item['code']) + '</code></pre>' +
                 '<h2>Performance and operating cost</h2><p>' + html.escape(item['cost']) +
                 '</p><h3>Common Mistakes</h3><ul>' +
                 ''.join('<li>' + html.escape(mistake) + '</li>' for mistake in item['mistakes']) +
                 '</ul><h2>Read next</h2>' + link_list(item['related']))
        path = item['path']
        row = dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://aitrove.in/' + path)),
                   type='article', path=path, title=item['title'], summary=item['summary'], body=body,
                   category='AI & Data', subject='data-engineering-project' if item['project'] else 'data-engineering',
                   difficulty='Advanced', tags=['ai-data', 'data-engineering'], potd_date=None,
                   featured=False, sort_order=7840 + index, status='published',
                   published_at=now, created_at=now, updated_at=now,
                   data={'subject_root': HUB, 'section_path': PROJECT_HUB if item['project'] else HUB,
                         'content_format': 'html', 'seo_ready': True,
                         'kind': 'project' if item['project'] else 'tutorial',
                         'reading_minutes': max(5, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                         'author_path': 'authors/aitrove-editorial',
                         'verification_suite': 'Editorial, code and internal-link checks',
                         'related': [{'path': target, 'title': titles[target]} for target in item['related']]})
        rows.append(row)
        by_path[path] = row

    hub = by_path[HUB]
    project_hub = by_path[PROJECT_HUB]
    hub['summary'] = 'Design replayable pipelines, distributed processing, versioned tables and reconciled warehouse metrics.'
    hub['body'] = re.sub(r'^<p>.*?</p>', '<p>' + hub['summary'] + '</p>', hub['body'], count=1)
    modules = ['Distributed execution and data movement', 'Warehouse models and metric contracts']
    for module_title in modules:
        lesson_paths = [item['path'] for item in LESSONS if item['module'] == module_title and not item['project']]
        project_paths = [item['path'] for item in LESSONS if item['module'] == module_title and item['project']]
        assert len(lesson_paths) == 4 and len(project_paths) == 1
        if not any(module['title'] == module_title for module in hub['data']['modules']):
            hub['data']['modules'].insert(-1, {'title': module_title,
                                               'summary': 'Run the implementation and failure checks before the project.',
                                               'lessons': lesson_paths})
        practice = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
        if project_paths[0] not in practice['lessons']:
            practice['lessons'].append(project_paths[0])
        if '<h2>' + module_title + '</h2>' not in hub['body']:
            hub['body'] += '<h2>' + module_title + '</h2>' + link_list(lesson_paths)
            hub['body'] += '<h2>' + ('Distributed invoice rollup' if module_title.startswith('Distributed') else 'Revenue mart release') + '</h2>' + link_list(project_paths)
        if project_paths[0] not in project_hub['data']['modules'][0]['lessons']:
            project_hub['data']['modules'][0]['lessons'].append(project_paths[0])
        if project_paths[0] not in project_hub['body']:
            project_hub['body'] += '<h2>' + ('Distributed invoice rollup' if module_title.startswith('Distributed') else 'Revenue mart release') + '</h2>' + link_list(project_paths)
    hub['updated_at'] = now
    project_hub['updated_at'] = now

    crosslinks = [
        ('data-engineering/partition-planning-and-skew', 'data-engineering/shuffle-boundaries-and-local-combiners'),
        ('data-engineering/parquet-row-groups-and-column-pruning', 'data-engineering/task-retries-and-atomic-partition-output'),
        ('data-engineering/schema-compatibility-and-consumer-rollout', 'data-engineering/conformed-dimensions-and-surrogate-keys'),
        ('data-engineering/warehouse-history-asof-join', 'data-engineering/late-arriving-dimensions-and-fact-repair'),
        ('data-engineering/quality-quarantine-and-reconciliation', 'data-engineering/semantic-metric-contract-and-reconciliation'),
        ('data-engineering/lakehouse-snapshot-and-atomic-commit', 'data-engineering/task-retries-and-atomic-partition-output'),
        ('data-engineering/replay-manifest-and-audit-trail', 'data-engineering/revenue-mart-release-project'),
        ('data-engineering/billing-pipeline-operations-project', 'data-engineering/revenue-mart-release-project'),
        ('data-engineering/versioned-order-lake-release-project', 'data-engineering/distributed-invoice-rollup-project'),
        ('data-science/dataset-grain-and-join-cardinality', 'data-engineering/fact-grain-and-measure-additivity'),
        ('data-science/metric-denominator-and-cohort', 'data-engineering/semantic-metric-contract-and-reconciliation'),
        ('streaming-analytics/idempotent-sink-and-replay', 'data-engineering/task-retries-and-atomic-partition-output'),
    ]
    for source, target in crosslinks:
        changed.add(source)
        row = by_path[source]
        anchor = ('<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' +
                  html.escape(titles[target]) + '</a>.</p>')
        if anchor not in row['body']:
            row['body'] += anchor
            row['data'].setdefault('related', []).append({'path': target, 'title': titles[target]})
            row['updated_at'] = now
            changed.add(source)
    assert len({row['path'] for row in rows}) == len(rows)
    FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
    import_path = ROOT / 'work/aitrove-data-engineering-execution-warehouse-import-20261006.json'
    import_path.write_text(json.dumps([by_path[path] for path in sorted(changed)], ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'new_articles': len(LESSONS), 'new_projects': 2,
                      'crosslinks': len(crosslinks), 'import_rows': len(changed),
                      'import_path': str(import_path)}))


if __name__ == '__main__':
    publish()
