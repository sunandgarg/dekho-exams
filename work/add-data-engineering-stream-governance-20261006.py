"""Create original, linked Data Engineering lessons for the live CMS."""
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
STREAM = 'Streaming state and recovery'
GOVERN = 'Governance, access and cost'
LESSONS = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    assert len(sections) == 5
    LESSONS.append(dict(path='data-engineering/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add('keyed-state-checkpoints-and-recovery', 'Keyed state, checkpoints and recovery',
    'A stateful stream operator remembers values by key; a checkpoint binds that state to an input position so recovery can replay consistently.', [
    ('Define the state boundary', 'A payment-risk counter is keyed by account, not by worker. The engine may move account 47 to another worker after scaling, so the counter must be restorable independently of process memory. Record the input offsets, keyed state and operator version as one recoverable point. [[data-engineering/idempotent-load-and-checkpoint|Batch checkpoints]] follow the same replay principle, although stream state persists across many windows.'),
    ('Treat a checkpoint as a consistent cut', 'A checkpoint cannot pair state that has processed event 83 with a source offset that resumes at event 79; replay would count four events twice. In-flight records and channel alignment matter when operators receive multiple inputs. An unaligned mode can store those in-flight buffers, trading checkpoint speed under backpressure for larger snapshots. Measure completion time and snapshot bytes together.'),
    ('Separate engine recovery from sink effects', 'A restored counter may be exact while an external notification sent just before failure is repeated. Use a transactional sink tied to checkpoint completion or an idempotency key derived from business event identity. [[streaming-analytics/idempotent-sink-and-replay|Idempotent sinks]] explain that boundary. Do not promise end-to-end exactly once from an engine checkpoint alone.'),
    ('Plan state growth and migration', 'A key that never expires remains in a keyed store indefinitely. Set time-to-live from business retention and late-event policy, then document what happens when a dormant key returns. Serializer or schema changes can make an old checkpoint unreadable. Rehearse restore from a retained snapshot before the release, including a rescale to a different worker count.'),
    ('Exercise failure between checkpoints', 'Feed a pinned event log, capture a checkpoint after event 47, process event 48, then stop the worker before the next checkpoint. Recover from event 47 and assert the published output has one effect for event 48. Also test corrupted state, a missing checkpoint file and an incompatible serializer; each needs an explicit stop or rollback path.')],
    '''events = [("acct-47", "evt-47", 1200), ("acct-47", "evt-48", 900)]

def apply_events(state, seen, records):
    totals = dict(state)
    identities = set(seen)
    for account_id, event_id, cents in records:
        if event_id in identities:
            continue
        totals[account_id] = totals.get(account_id, 0) + cents
        identities.add(event_id)
    return totals, identities

checkpoint_state, checkpoint_seen = apply_events({}, set(), events[:1])
recovered_state, recovered_seen = apply_events(checkpoint_state, checkpoint_seen, events[1:])
assert recovered_state == {"acct-47": 2100}
assert apply_events(recovered_state, recovered_seen, events[1:])[0] == recovered_state''',
    'Processing N records takes O(N) expected time; keyed totals occupy O(K) memory for K active accounts and deduplication occupies O(E) for retained event identities. A real engine stores this state outside the Python process. Checkpoint I/O and restore duration grow with state size and buffered records, so retention and snapshot cadence are operating decisions.',
    ['Do not restart from a source offset newer than the restored state.', 'Do not call an external side effect exactly once without a sink protocol.', 'Do not change state serialization without a restore rehearsal.'],
    ['data-engineering/event-time-and-late-arrivals', 'data-engineering/idempotent-load-and-checkpoint', 'data-engineering/stream-backpressure-and-catch-up-budget', 'data-engineering/streaming-risk-ledger-project', 'streaming-analytics/idempotent-sink-and-replay'], STREAM)

add('watermark-retention-and-late-corrections', 'Watermark retention and late corrections',
    'A watermark states how far event time has probably advanced; retention defines when an old window can no longer accept ordinary corrections.', [
    ('Use event time as the grouping key', 'A card authorization created on day 47 may reach the processor on day 49. Grouping by arrival day changes the question the metric answers. Keep event time, arrival time and source identity separately. [[data-engineering/event-time-and-late-arrivals|Event-time policy]] defines when a window first emits, but that first result need not be final.'),
    ('Choose allowed lateness from evidence', 'Measure the distribution of arrival delay by source and incident class. A watermark lag of 36 hours could cover routine network delays but not a three-day source outage. State the promise: routine updates before the cutoff, explicit correction after it. A larger delay reduces ordinary restatements but holds more open state and delays final reporting.'),
    ('Retain enough to make corrections coherent', 'Window state, deduplication IDs and source positions need compatible horizons. If window state lasts 60 hours but event IDs expire after 24, a retransmitted record can be counted again while the window is still open. [[data-engineering/compaction-retention-and-replay-horizon|Retention planning]] must include recovery, replay and legal boundaries, not only the dashboard delay.'),
    ('Publish revisions with identity', 'A correction after a provisional result should replace the same account-window key with a higher revision or publish a versioned snapshot. Appending a second total without a revision contract makes readers sum both. Keep prior and revised totals, reason, source event ID and publication time in the audit record. Send very late events to a repair path rather than discarding them silently.'),
    ('Test the edge of the cutoff', 'Build fixtures for an on-time event, one just before the watermark, one just after it and a duplicate. Assert the expected revision number and exact cents. Then restore from a checkpoint before the late record and replay; the published revision must be the same. A test that only checks aggregate totals misses duplicate revision rows.')],
    '''from collections import defaultdict

records = [
    {"id": "auth-47", "account": "acct-47", "event_hour": 47, "arrival_hour": 48, "cents": 3100},
    {"id": "auth-48", "account": "acct-47", "event_hour": 47, "arrival_hour": 50, "cents": 700},
]

def window_total(events, cutoff_hour):
    accepted = [row for row in events if row["arrival_hour"] <= cutoff_hour]
    if len({row["id"] for row in accepted}) != len(accepted):
        raise ValueError("duplicate authorization identity")
    totals = defaultdict(int)
    for row in accepted:
        totals[(row["account"], row["event_hour"])] += row["cents"]
    return dict(totals)

assert window_total(records, 49) == {("acct-47", 47): 3100}
assert window_total(records, 50) == {("acct-47", 47): 3800}''',
    'A keyed pass costs O(N) expected time and O(K + N) memory here, including duplicate validation. In production, open windows and retained identities scale with throughput multiplied by the retention horizon. Extending the watermark by one day can materially increase state, checkpoint bytes and recovery time; measure each before changing the promise.',
    ['Do not treat a first window emission as immutable unless the contract says so.', 'Do not expire deduplication state before a window can still be corrected.', 'Do not append a revised total as a second additive fact.'],
    ['data-engineering/event-time-and-late-arrivals', 'data-engineering/keyed-state-checkpoints-and-recovery', 'data-engineering/compaction-retention-and-replay-horizon', 'data-engineering/streaming-risk-ledger-project', 'data-engineering/replay-manifest-and-audit-trail'], STREAM)

add('stream-table-join-and-reference-versions', 'Stream-table joins and reference versions',
    'A stream-table join enriches each event with reference data, but correctness depends on which version of that data the event is allowed to see.', [
    ('Choose a time rule before joining', 'A current-value lookup answers what the merchant category is now. A temporal lookup answers what it was when a payment occurred. Both are valid for different products. For historical risk analysis, use event time and a version interval; otherwise a merchant recategorization can rewrite past cohorts during replay. [[data-engineering/warehouse-history-asof-join|An as-of join]] has the same requirement in a warehouse.'),
    ('Make update order explicit', 'The event stream and reference change stream can arrive in either order. A payment at hour 47 may be processed before the category update effective at hour 46 reaches this worker. Choose to wait for reference completeness, emit unknown and repair later, or use a bounded temporal store with delayed finalization. The choice changes latency, state and historical accuracy.'),
    ('Reject overlapping versions', 'For one merchant, version intervals should be half-open and non-overlapping. If two rows match one event time, enrichment must fail or quarantine the key, never arbitrarily choose whichever arrived last. Preserve source namespace and stable merchant identity. [[data-engineering/conformed-dimensions-and-surrogate-keys|Conformed identity]] prevents two systems with the same numeric ID from merging.'),
    ('Control fanout and missing matches', 'A join intended to yield one output per payment can multiply records when a lookup key has duplicate active rows. Assert output count equals input count and record the unresolved-reference rate. A valid but late dimension can use an explicit unknown member and later repair. Invalid keys should be quarantined, not guessed from a display name.'),
    ('Rehearse a historical correction', 'Deliver category A, a payment, then category B with an effective time before the payment. Under a temporal contract, a repair may revise the payment enrichment; under an immutable-at-first-seen contract, it should not. Publish the selected rule and its audit trail so readers can explain why a cohort moved.')],
    '''versions = [
    {"merchant": "m-47", "start": 40, "end": 48, "category": "retail"},
    {"merchant": "m-47", "start": 48, "end": None, "category": "marketplace"},
]
payments = [{"id": "pay-47", "merchant": "m-47", "event_hour": 47}]

def category_at_time(payment, reference_rows):
    matches = [row["category"] for row in reference_rows
               if row["merchant"] == payment["merchant"]
               and row["start"] <= payment["event_hour"]
               and (row["end"] is None or payment["event_hour"] < row["end"])]
    if len(matches) != 1:
        raise ValueError("reference version is missing or overlaps")
    return matches[0]

assert category_at_time(payments[0], versions) == "retail"''',
    'The reference scan is O(V) per event for V versions; an indexed temporal store reduces lookup work but stores each retained version until its supported replay horizon ends. Stream output still needs a one-to-one cardinality check. Waiting for reference completeness costs latency; optimistic output costs repair work and versioned publication.',
    ['Do not use the current reference row when historical truth is required.', 'Do not let duplicate active versions multiply events.', 'Do not hide a missing reference behind a guessed category.'],
    ['data-engineering/warehouse-history-asof-join', 'data-engineering/late-arriving-dimensions-and-fact-repair', 'data-engineering/watermark-retention-and-late-corrections', 'data-engineering/streaming-risk-ledger-project', 'data-engineering/conformed-dimensions-and-surrogate-keys'], STREAM)

add('stream-backpressure-and-catch-up-budget', 'Stream backpressure and catch-up budget',
    'Backpressure appears when a downstream stage consumes slower than upstream arrival; backlog grows until capacity, latency or retention runs out.', [
    ('Measure the rate mismatch', 'If a source emits 1,700 records per second and the sink sustains 1,300, backlog grows by about 400 per second. A 720,000-record backlog then needs more than mere parity to clear. At 2,100 per second of sustainable processing against 1,700 new records, net catch-up is 400 per second, or 30 minutes. Use measured sustained rates, not a brief peak benchmark.'),
    ('Find the slow boundary', 'Inspect source lag, per-operator busy time, output buffer occupancy, checkpoint duration, sink acknowledgements and largest keyed partition. A slow sink can make every upstream operator look busy because flow control propagates backward. [[data-engineering/skewed-keys-and-salted-aggregation|Hot keys]] can create the same symptom on one task. Scale the actual bottleneck or reduce its work.'),
    ('Budget for recovery', 'A consumer that only matches normal arrival rate can never catch up after an outage. Specify maximum tolerated lag and outage duration, then reserve enough spare throughput to drain backlog within that window. Include restore time before useful processing resumes. Source retention must exceed outage plus catch-up plus a safety margin, or the missing records will expire.'),
    ('Avoid destructive emergency fixes', 'Increasing parallelism can help only when partitions, keys and downstream service limits allow it. Disabling checkpoints may improve momentary throughput but removes a reliable recovery point. Dropping events to make a dashboard green violates the data contract. Shed optional enrichment or route overflow to a durable queue only if the consumer explicitly accepts that behavior.'),
    ('Verify under a realistic incident', 'Throttle the sink, let lag accumulate for a measured interval, then restore capacity. Plot backlog slope before and after, checkpoint completion time and event-time freshness. Compare the actual catch-up time with the calculation. If one input partition saturates, adding workers alone may leave the slope unchanged.')],
    '''def catch_up_seconds(backlog_records, incoming_per_second, processing_per_second):
    spare = processing_per_second - incoming_per_second
    if backlog_records < 0 or incoming_per_second < 0 or spare <= 0:
        raise ValueError("catch-up needs positive spare throughput")
    return backlog_records / spare

assert catch_up_seconds(720_000, 1_700, 2_100) == 1_800
assert catch_up_seconds(24_000, 500, 700) == 120''',
    'The estimate is O(1) arithmetic but assumes stable rates. In a real pipeline, processing capacity changes with key distribution, checkpoint load and sink throttling. Backlog consumes broker storage; open windows and deduplication state consume stream storage. Track both, and recalculate from observed net drain rather than treating a one-time capacity test as a guarantee.',
    ['Do not interpret upstream busy time as proof the upstream stage is slow.', 'Do not plan recovery with zero spare throughput.', 'Do not disable checkpoints or drop records without a written loss contract.'],
    ['data-engineering/keyed-state-checkpoints-and-recovery', 'data-engineering/pipeline-slos-and-error-budgets', 'data-engineering/failure-classification-and-retry-budget', 'data-engineering/streaming-risk-ledger-project', 'data-engineering/skewed-keys-and-salted-aggregation'], STREAM)

add('streaming-risk-ledger-project', 'Project: release a recoverable streaming risk ledger',
    'Build a payment-risk ledger that joins historical merchant categories, revises late windows and recovers without duplicate published effects.', [
    ('Write the consumer contract', 'Each payment has a globally unique event ID, account ID, merchant ID, integer cents, event time and arrival time. Publish one account-hour total and risk count with a revision number. State the watermark delay, state retention and maximum backlog age. Merchant category must match the version effective at payment time, not the category visible when the replay runs.'),
    ('Build recoverable state', 'Key totals by account and event hour. Persist source position, deduplication identities, open-window state and reference versions in a consistent checkpoint. Write output candidates under a stable account-hour-revision key, then commit through a sink that rejects repeated keys. [[data-engineering/keyed-state-checkpoints-and-recovery|Checkpoint design]] protects the state; [[streaming-analytics/idempotent-sink-and-replay|sink identity]] protects reader-visible effects.'),
    ('Handle disorder and corrections', 'Emit a provisional window, then send a valid late payment before the allowed cutoff and publish revision two. Send another payment beyond ordinary retention; route it to a signed repair request rather than silently dropping it. Deliver an effective-dated merchant change after a payment and verify the historical join follows the declared temporal rule.'),
    ('Inject pressure and failure', 'Throttle the sink until lag reaches a known backlog, restore capacity and measure net drain. Kill a worker after output candidate creation but before checkpoint completion; recover from the previous checkpoint and assert one committed revision per key. Test a duplicate payment ID, overlapping merchant versions and a state serializer mismatch. The last case must stop safely.'),
    ('Deliver release evidence', 'Provide source and output schemas, watermark and retention policy, a checkpoint/restore transcript, temporal-join fixtures, revision history, backlog calculation, sink idempotency proof and reconciliation of accepted, quarantined and repaired events. Record the exact source positions and code revision so the release is reproducible.')],
    '''events = [
    {"id": "pay-47", "account": "acct-8", "hour": 47, "cents": 2600},
    {"id": "pay-48", "account": "acct-8", "hour": 47, "cents": 900},
]

def ledger_snapshot(records):
    seen = set()
    totals = {}
    for row in records:
        if row["id"] in seen:
            continue
        seen.add(row["id"])
        key = (row["account"], row["hour"])
        totals[key] = totals.get(key, 0) + row["cents"]
    return totals

assert ledger_snapshot(events + events[:1]) == {("acct-8", 47): 3500}''',
    'The reference pass costs O(N) expected time and O(E + K) state for retained identities and active account-hour keys. Production cost also includes checkpoint I/O, temporal-reference versions, broker backlog, output revisions and repair work. Keep a retention limit that covers expected disorder without allowing unbounded state growth.',
    ['Do not call a provisional result final.', 'Do not replay an external side effect without its idempotency identity.', 'Do not equate restored process health with caught-up event-time freshness.'],
    ['data-engineering/keyed-state-checkpoints-and-recovery', 'data-engineering/watermark-retention-and-late-corrections', 'data-engineering/stream-table-join-and-reference-versions', 'data-engineering/stream-backpressure-and-catch-up-budget', 'data-engineering/replay-manifest-and-audit-trail'], STREAM, True)

add('data-classification-and-access-boundaries', 'Data classification and access boundaries',
    'Classification labels data by sensitivity and allowed use; access boundaries turn those labels into enforceable permissions at each pipeline stage.', [
    ('Classify the fields actually stored', 'A payments pipeline may carry account ID, merchant ID, card token, postal code and derived risk score. Classify raw values, joinable pseudonyms and aggregates separately. A hashed account ID may still identify someone when the mapping is available or the input space is small. Record the purpose, retention and authorized readers for every sensitive field, not only the table name.'),
    ('Keep raw and serving zones distinct', 'Landing stores the minimum source payload needed for replay under restricted roles. Transformation workers receive only the fields needed for their task; an analytics mart publishes approved columns and aggregates. [[data-engineering/source-contract-and-raw-landing|Raw landing]] should not become a broad query playground. Limit export, temporary tables, logs and failed-record queues too, since those paths often copy sensitive values.'),
    ('Bind permission to identity and purpose', 'Grant access to service identities and named job roles, then map human users to reviewed groups. Avoid shared credentials that erase accountability. A pipeline operator may need to inspect health and row counts without reading full payment identifiers. A data steward may approve a new use but should not have to run the compute job. Separation makes incident review possible.'),
    ('Propagate labels through derivations', 'A joined table inherits the sensitivity of its inputs unless the derivation provably removes it for the authorized use. Small group counts can reveal an individual even when direct identifiers are absent. Keep lineage from source fields to output fields, and require a new access review when a new join or export makes previously separate attributes linkable. [[data-engineering/pipeline-lineage-and-impact-analysis|Lineage]] provides the dependency map.'),
    ('Verify denial as well as approval', 'Test that an approved report role can read its aggregate, that an analyst role cannot read raw account IDs, and that an operations role sees logs with values redacted. Record which identity ran the test and which policy version applied. A permission policy is incomplete until the denied paths are exercised.')],
    '''FIELD_POLICY = {
    "account_id": {"class": "restricted", "roles": {"risk_service"}},
    "merchant_region": {"class": "internal", "roles": {"risk_service", "analyst"}},
    "daily_count": {"class": "aggregate", "roles": {"risk_service", "analyst"}},
}

def permitted_fields(role, requested):
    denied = [name for name in requested if role not in FIELD_POLICY[name]["roles"]]
    if denied:
        raise PermissionError("requested fields exceed role policy")
    return requested

assert permitted_fields("analyst", ["merchant_region", "daily_count"])
try:
    permitted_fields("analyst", ["account_id"])
except PermissionError:
    pass
else:
    raise AssertionError("restricted field was exposed")''',
    'A set-membership check takes O(F) time for F requested fields and O(F) policy metadata. Real access controls add identity lookup, policy evaluation, audit writes and possibly query rewriting. Denying an unauthorized scan early is cheaper than filtering sensitive records after they have already moved to a less trusted stage.',
    ['Do not treat a hash as automatically anonymous.', 'Do not forget logs, exports and quarantine tables when classifying data.', 'Do not rely on a role name without testing both allowed and denied queries.'],
    ['data-engineering/row-policy-and-column-mask-tests', 'data-engineering/pipeline-lineage-and-impact-analysis', 'data-engineering/deletion-propagation-and-erasure-proof', 'data-engineering/governed-customer-mart-project', 'data-engineering/source-contract-and-raw-landing'], GOVERN)

add('row-policy-and-column-mask-tests', 'Row policy and column mask tests',
    'A row policy limits which records an identity can read; a column mask changes the value it sees, so both need tests at the consumer query boundary.', [
    ('State the intended visibility', 'A regional support analyst may see only customers assigned to their region, with account token masked. A finance service may read all regions but only the aggregate billing amount. Write this as an identity-by-field matrix, including null and unknown region cases. An unassigned customer should not become visible merely because the policy comparison returns an unexpected null value.'),
    ('Test through the same query path', 'A unit test of a masking expression cannot prove the BI connection, view ownership and role mapping apply it. Execute representative SELECTs as each real role against the published view. Verify allowed row IDs, denied row IDs and exact masked values. Then try a join, export and materialized copy if those paths are available to the role.'),
    ('Guard policy inputs', 'If an administrator can edit the analyst-to-region mapping, that mapping is part of the security boundary. Version it, review changes and test a user moved between regions. Default-deny when membership is absent or ambiguous. A policy that reads a mutable lookup can produce different historical query results; retain audit evidence of the mapping used.'),
    ('Account for derived exposure', 'Masking a direct account token is insufficient if a combination of postal code, event time and rare merchant makes the person identifiable. Review derived columns and small cohorts under the same classification rules. [[data-engineering/data-classification-and-access-boundaries|The classification contract]] decides which joins and exports are allowed, while the row and mask policies enforce the resulting boundary.'),
    ('Recheck after schema changes', 'Adding a new sensitive column can bypass an explicit mask list if the view uses wildcard selection. Require an allowlist of exposed fields and run policy tests as part of the release gate. Confirm that an authorized role still sees the values it needs; over-masking can break operations and create unsafe workarounds.')],
    '''customers = [
    {"id": "cust-47", "region": "north", "token": "tok-4731"},
    {"id": "cust-83", "region": "west", "token": "tok-8394"},
]

def support_view(rows, assigned_region):
    return [{"id": row["id"], "region": row["region"], "token": "[masked]"}
            for row in rows if assigned_region is not None
            and row["region"] == assigned_region]

assert support_view(customers, "north") == [
    {"id": "cust-47", "region": "north", "token": "[masked]"}]
assert support_view(customers, None) == []''',
    'A full in-memory scan is O(N) time and O(R) output for N rows and R authorized rows. A database may push row filters into indexed access, but complex policy functions can prevent pruning or add per-row work. Benchmark the authorized query plan without weakening the policy, and test the actual database role rather than only this reference function.',
    ['Do not test masking only through an administrator connection.', 'Do not make unknown region membership mean all regions.', 'Do not expose newly added columns through wildcard views.'],
    ['data-engineering/data-classification-and-access-boundaries', 'data-engineering/dataset-ownership-and-change-approval', 'data-engineering/governed-customer-mart-project', 'data-engineering/pipeline-lineage-and-impact-analysis', 'data-engineering/deletion-propagation-and-erasure-proof'], GOVERN)

add('dataset-ownership-and-change-approval', 'Dataset ownership and change approval',
    'A dataset owner accepts its meaning, access and change process; a pipeline maintainer owns the job that computes it, and consumers own their use of it.', [
    ('Name the decision makers', 'For a customer mart, record a business owner for field meaning, a steward for classification, a technical maintainer for pipeline health and a security approver for new sensitive access. One person can fill several roles in a small team, but each decision still needs an accountable name. An unowned table should not silently become a production dependency.'),
    ('Make the contract reviewable', 'Store row grain, keys, update cadence, freshness target, null meaning, correction policy, allowed uses and retention beside the dataset. Link the upstream sources and known consumers through [[data-engineering/pipeline-lineage-and-impact-analysis|lineage]]. A consumer should be able to determine whether a changed field is safe without searching chat history or reverse engineering a dashboard query.'),
    ('Classify changes by effect', 'A new optional field may be backward-compatible for readers but still change classification or cost. Renaming a key, altering its grain or changing a metric denominator is a breaking semantic change even if the schema remains valid. [[data-engineering/schema-compatibility-and-consumer-rollout|Schema rollout]] handles code compatibility; owner approval covers business meaning and access.'),
    ('Stage a measurable migration', 'Publish the proposed contract and sample output, notify known consumers, run old and new calculations on the same pinned input, and record count or metric differences. Set a dual-read or deprecation window when needed. Promotion requires named approval, validation evidence and a rollback pointer. A pass from automated tests alone cannot approve a new use of sensitive data.'),
    ('Keep evidence after release', 'Attach change ID, approving roles, input snapshot, code revision, access-policy revision and consumer communication to the release manifest. If a downstream report changes, the operator can explain whether the cause was new source data, a model change or a policy change. [[data-engineering/replay-manifest-and-audit-trail|Replay manifests]] provide the technical half of that explanation.')],
    '''required_approvals = {
    "grain_change": {"business_owner", "technical_maintainer"},
    "new_sensitive_field": {"data_steward", "security_approver"},
}

def release_approved(change_type, signed_roles):
    required = required_approvals[change_type]
    return required.issubset(set(signed_roles))

assert not release_approved("new_sensitive_field", ["data_steward"])
assert release_approved("new_sensitive_field", ["data_steward", "security_approver"])''',
    'An approval membership check is O(A) for A signed roles and needs little memory; the significant cost is the dual-run, consumer testing and retained release evidence. That cost should be proportional to impact. Automate discovery and comparison so humans review the meaning and authorized use, rather than manually repeating deterministic checks.',
    ['Do not equate schema compatibility with semantic compatibility.', 'Do not let a maintainer approve a new sensitive use by default.', 'Do not discard the contract version once a migration finishes.'],
    ['data-engineering/schema-compatibility-and-consumer-rollout', 'data-engineering/pipeline-lineage-and-impact-analysis', 'data-engineering/data-classification-and-access-boundaries', 'data-engineering/governed-customer-mart-project', 'data-engineering/replay-manifest-and-audit-trail'], GOVERN)

add('pipeline-cost-attribution-and-right-sizing', 'Pipeline cost attribution and right-sizing',
    'Cost attribution ties compute, storage, transfer and retries to a dataset release so a faster pipeline is not mistaken for a cheaper one.', [
    ('Define a unit of work', 'For a daily customer mart, cost per accepted million rows or per published partition is more useful than a monthly warehouse bill. Capture input bytes, output bytes, worker time, storage generations, network transfer and reruns by job and dataset ID. A large cost can be justified when data volume rises; a rising unit cost with stable volume signals inefficiency.'),
    ('Separate baseline from incident spend', 'A retry storm can double compute while producing one release. Attribute all attempts to that release rather than charging only the successful run. Include quarantine reprocessing, backfills and retained snapshots. [[data-engineering/failure-classification-and-retry-budget|Retry budgets]] prevent transient faults from silently becoming the main cost driver.'),
    ('Locate the expensive boundary', 'Column pruning can avoid reading unused Parquet fields; partition pruning avoids irrelevant time ranges; a local combiner reduces shuffle bytes. Each changes a different bill component. [[data-engineering/parquet-row-groups-and-column-pruning|Read pruning]] and [[data-engineering/shuffle-boundaries-and-local-combiners|shuffle reduction]] should be measured on the same pinned input and query plan. Buying more workers before locating the bottleneck may only make the mistake more expensive.'),
    ('Right-size without missing the deadline', 'Downsizing a job may cut hourly compute but extend runtime beyond an agreed freshness SLO, while extreme parallelism can raise setup, shuffle and sink contention. Compare cost, p95 completion and largest task memory over several representative intervals. Keep a capacity margin for a backfill or a larger day. The cheapest successful run is not always the cheapest reliable service.'),
    ('Verify bill-to-release mapping', 'Require every billable job and storage prefix to carry a dataset or shared-platform tag. Reconcile tagged cost with provider totals and track an unattributed bucket. A tag on the coordinator alone misses workers and intermediate storage. Review estimates against bills, then revise the per-unit model; it is an instrument, not an invoice.')],
    '''runs = [
    {"release": "mart-47", "attempt": 1, "compute_cents": 390, "rows": 0},
    {"release": "mart-47", "attempt": 2, "compute_cents": 470, "rows": 240_000},
]

def cost_per_million_accepted(rows):
    spent = sum(row["compute_cents"] for row in rows)
    accepted = sum(row["rows"] for row in rows)
    if accepted <= 0:
        raise ValueError("no accepted output")
    return spent * 1_000_000 / accepted

assert round(cost_per_million_accepted(runs), 2) == 3583.33''',
    'Aggregating R run records takes O(R) time and O(1) additional memory. The larger cost model needs provider billing exports, storage inventory and usage tags, which can lag real time. Sample query and task metrics at a resolution that explains the bill, and avoid retaining high-cardinality telemetry indefinitely merely to optimize a small pipeline.',
    ['Do not ignore failed attempts when pricing one successful release.', 'Do not optimize hourly rate while freshness and catch-up fail.', 'Do not treat untagged spend as zero.'],
    ['data-engineering/parquet-row-groups-and-column-pruning', 'data-engineering/shuffle-boundaries-and-local-combiners', 'data-engineering/pipeline-slos-and-error-budgets', 'data-engineering/governed-customer-mart-project', 'data-engineering/failure-classification-and-retry-budget'], GOVERN)

add('governed-customer-mart-project', 'Project: release a governed customer mart',
    'Release a customer analytics mart with declared field sensitivity, tested row policies, named approvals and measurable cost per published row.', [
    ('Specify the product boundary', 'The mart has one row per customer and reporting day, with region, eligible-order count and net captured cents. Raw landing retains namespaced customer IDs under a restricted role; analysts see regional aggregates and masked tokens. Record field classifications, allowed uses, retention, consumer roles and the business owner before creating the serving view.'),
    ('Build and reconcile the release', 'Pin source snapshots, deduplicate captures by stable ID, resolve the dimension version valid at event time and aggregate at the declared grain. Reconcile source and mart cents by day, then publish one immutable snapshot. [[data-engineering/fact-grain-and-measure-additivity|Grain rules]] prevent capture multiplication. Keep quarantine counts and unresolved customer keys visible to the operator.'),
    ('Test permissions as consumers', 'Query the actual serving view as north-region analyst, west-region analyst, finance service and an unauthorized identity. Assert exact allowed row IDs, masked token values and denied access to raw landing. Try a join and export path available to each role. [[data-engineering/row-policy-and-column-mask-tests|Policy tests]] must fail when a new sensitive field appears without an explicit allowlist decision.'),
    ('Approve and cost the change', 'Introduce a new postal-zone field and run classification review before exposing it. The business owner approves its meaning; the steward and security approver decide access. Compare old and new output on the same input and retain a rollback pointer. Attribute compute attempts, storage generations and validation scans to this release, then report cost per accepted million rows.'),
    ('Deliver audit evidence', 'Provide the source contract, data classification matrix, role-query transcript, field lineage, signed change record, reconciliation report, cost attribution and snapshot manifest. Simulate a denied analyst query and a failed compute attempt; neither should leak raw data or disappear from the cost ledger. Record who can authorize a repair or rollback.')],
    '''captures = [
    {"id": "cap-47", "customer": "cust-7", "region": "north", "cents": 5200},
    {"id": "cap-48", "customer": "cust-8", "region": "west", "cents": 1700},
]

def regional_mart(rows):
    identities = set()
    totals = {}
    for row in rows:
        if row["id"] in identities:
            raise ValueError("duplicate capture")
        identities.add(row["id"])
        totals[row["region"]] = totals.get(row["region"], 0) + row["cents"]
    return totals

assert regional_mart(captures) == {"north": 5200, "west": 1700}''',
    'The reference aggregation takes O(N) expected time and O(N + G) memory for N captures and G regions because it checks identities. Production cost includes versioned joins, access-policy evaluation, release validation, retained snapshots and failed attempts. Report cost against accepted output and keep policy tests in the release gate even when their scans add expense.',
    ['Do not publish a new derived identifier before classifying it.', 'Do not validate permissions with an administrator account.', 'Do not price only the final successful compute attempt.'],
    ['data-engineering/data-classification-and-access-boundaries', 'data-engineering/row-policy-and-column-mask-tests', 'data-engineering/dataset-ownership-and-change-approval', 'data-engineering/pipeline-cost-attribution-and-right-sizing', 'data-engineering/revenue-mart-release-project'], GOVERN, True)


def publish():
    rows = json.loads(FIXTURE.read_text())
    new_paths = {item['path'] for item in LESSONS}
    assert len(new_paths) == len(LESSONS) == 10
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
                   featured=False, sort_order=7860 + index, status='published',
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
    hub['summary'] = 'Build replayable, governed data products: streaming state, temporal joins, access policies, cost and release evidence.'
    hub['body'] = re.sub(r'^<p>.*?</p>', '<p>' + hub['summary'] + '</p>', hub['body'], count=1)
    for module_title in (STREAM, GOVERN):
        lesson_paths = [item['path'] for item in LESSONS if item['module'] == module_title and not item['project']]
        project_paths = [item['path'] for item in LESSONS if item['module'] == module_title and item['project']]
        assert len(lesson_paths) == 4 and len(project_paths) == 1
        if not any(module['title'] == module_title for module in hub['data']['modules']):
            hub['data']['modules'].insert(-1, {'title': module_title,
                                               'summary': 'Work through the failure and release checks, then complete the project.',
                                               'lessons': lesson_paths})
        practice = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
        if project_paths[0] not in practice['lessons']:
            practice['lessons'].append(project_paths[0])
        if '<h2>' + module_title + '</h2>' not in hub['body']:
            hub['body'] += '<h2>' + module_title + '</h2>' + link_list(lesson_paths)
            hub['body'] += '<h2>' + ('Streaming risk ledger' if module_title == STREAM else 'Governed customer mart') + '</h2>' + link_list(project_paths)
        if project_paths[0] not in project_hub['data']['modules'][0]['lessons']:
            project_hub['data']['modules'][0]['lessons'].append(project_paths[0])
        if project_paths[0] not in project_hub['body']:
            project_hub['body'] += '<h2>' + ('Streaming risk ledger' if module_title == STREAM else 'Governed customer mart') + '</h2>' + link_list(project_paths)
    hub['updated_at'] = now
    project_hub['updated_at'] = now

    crosslinks = [
        ('data-engineering/event-time-and-late-arrivals', 'data-engineering/watermark-retention-and-late-corrections'),
        ('data-engineering/idempotent-load-and-checkpoint', 'data-engineering/keyed-state-checkpoints-and-recovery'),
        ('data-engineering/warehouse-history-asof-join', 'data-engineering/stream-table-join-and-reference-versions'),
        ('data-engineering/pipeline-slos-and-error-budgets', 'data-engineering/stream-backpressure-and-catch-up-budget'),
        ('data-engineering/billing-pipeline-operations-project', 'data-engineering/streaming-risk-ledger-project'),
        ('data-engineering/source-contract-and-raw-landing', 'data-engineering/data-classification-and-access-boundaries'),
        ('data-engineering/schema-compatibility-and-consumer-rollout', 'data-engineering/dataset-ownership-and-change-approval'),
        ('data-engineering/pipeline-lineage-and-impact-analysis', 'data-engineering/row-policy-and-column-mask-tests'),
        ('data-engineering/parquet-row-groups-and-column-pruning', 'data-engineering/pipeline-cost-attribution-and-right-sizing'),
        ('data-engineering/revenue-mart-release-project', 'data-engineering/governed-customer-mart-project'),
        ('streaming-analytics/idempotent-sink-and-replay', 'data-engineering/keyed-state-checkpoints-and-recovery'),
        ('data-science/dataset-grain-and-join-cardinality', 'data-engineering/governed-customer-mart-project'),
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
    assert len({row['path'] for row in rows}) == len(rows)
    FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
    import_path = ROOT / 'work/aitrove-data-engineering-stream-governance-import-20261006.json'
    import_path.write_text(json.dumps([by_path[path] for path in sorted(changed)], ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'new_articles': len(LESSONS), 'new_projects': 2,
                      'crosslinks': len(crosslinks), 'import_rows': len(changed),
                      'import_path': str(import_path)}))


if __name__ == '__main__':
    publish()
