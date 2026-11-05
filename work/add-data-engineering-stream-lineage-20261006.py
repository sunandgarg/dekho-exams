"""Publish bounded-join and column-impact Data Engineering paths."""
from de_batch_publisher import publish

JOIN = 'Bounded stream joins and replay state'
LINEAGE = 'Column lineage and impact evidence'
LESSONS = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    assert len(sections) == 5
    LESSONS.append(dict(path='data-engineering/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add('interval-join-state-horizon-and-watermark-skew', 'Interval-join state horizons and watermark skew',
    'A stream join needs a finite event-time search interval and a retention rule that cannot evict a match while the other input may still deliver it.', [
    ('Write the match interval precisely', 'A payment at time P can match a risk signal from P minus 47 minutes through P plus 8 minutes. Put both bounds in the contract and say whether endpoints are inclusive. A key match alone has no natural stopping point; state grows until an explicit horizon or cleanup policy removes it. [[data-engineering/stream-table-join-and-reference-versions|A stream-to-table version lookup]] has a different state model and should not be substituted for a two-stream interval join without checking semantics.'),
    ('Use both progress signals', 'An event-time watermark from the payment stream cannot prove the risk stream has finished sending older signals. Track progress per input and per partition. The join may release a stored payment only after the risk-side watermark passes the latest matching risk time plus any agreed lateness. A stalled partition can hold state for longer than the configured time interval; measure this operational lag separately from the logical matching horizon.'),
    ('Separate lateness from TTL', 'A state TTL is a memory and storage control, often measured from processing-time access or write. It is not necessarily the event-time rule that determines whether a record can still join. If TTL is shorter than interval plus allowed lateness and observed skew, a valid late counterpart can arrive after the first side has vanished. The job may emit a false unmatched result while all source events are present. [[data-engineering/watermark-retention-and-late-corrections|Late-correction policy]] determines what to do after the accepted horizon closes.'),
    ('Test asymmetric arrival', 'Send one payment first and its matching signal just before the risk watermark passes the upper bound. Then reverse arrival order. Also hold one risk partition idle while other partitions advance, and send a counterpart outside the interval that must never match. Inspect state size, late-drop count and unmatched-output count. A single happy-path interleaving cannot prove the cleanup timer is safe.'),
    ('Bound the state budget', 'Estimate state bytes from active keys, records per key, serialized bytes and checkpoint overhead. A busy merchant may hold many payments under one key; partition-level averages hide that pressure. Apply explicit per-key or workload admission limits where product semantics allow, and send over-limit input to a controlled recovery path rather than silently truncating it. Alert when watermark lag makes the planned state budget unattainable.')],
    '''from datetime import datetime, timedelta, timezone

payment_time = datetime(2026, 10, 6, 10, 47, tzinfo=timezone.utc)
earliest_signal = payment_time - timedelta(minutes=47)
latest_signal = payment_time + timedelta(minutes=8)

def signal_matches(payment_at, signal_at):
    return (payment_at - timedelta(minutes=47)
            <= signal_at <= payment_at + timedelta(minutes=8))

def may_evict_payment(payment_at, risk_watermark, allowed_lateness):
    return risk_watermark > payment_at + timedelta(minutes=8) + allowed_lateness

assert signal_matches(payment_time, earliest_signal)
assert signal_matches(payment_time, latest_signal)
assert not signal_matches(payment_time, latest_signal + timedelta(seconds=1))
assert not may_evict_payment(payment_time, latest_signal, timedelta(minutes=3))
assert may_evict_payment(payment_time, latest_signal + timedelta(minutes=4), timedelta(minutes=3))''',
    'An indexed keyed join probes matching records in expected O(M) time for M candidates under one key, while active state grows with the records retained across both inputs. Checkpoint bytes and restore time grow with that state. A shorter TTL saves storage but can invalidate accepted matches; a longer one raises checkpoint and backpressure cost. Measure both against an explicit lateness contract.',
    ['Do not use one stream watermark as proof that the other side is complete.', 'Do not confuse processing-time TTL with the event-time match horizon.', 'Do not silently drop a hot key because its state exceeded an average-key budget.'],
    ['data-engineering/stream-table-join-and-reference-versions', 'data-engineering/watermark-retention-and-late-corrections', 'data-engineering/keyed-state-checkpoints-and-recovery', 'data-engineering/join-replay-output-identity-and-recovery', 'data-engineering/payment-risk-interval-join-project'], JOIN)

add('join-replay-output-identity-and-recovery', 'Join replay output identity and recovery',
    'After a checkpoint restore or late correction, the same logical match must have a stable identity so the sink can replace it instead of counting it twice.', [
    ('Identify the relationship', 'A match between payment revision 2 and signal revision 4 is a different result from the same payment joined to an earlier signal revision. Define a pair identity from both source IDs, both revisions and the join-rule version. Do not use only processing timestamp or task attempt ID. A sink can then upsert the identical result after replay while retaining a deliberate new result when one side changes. [[data-engineering/event-envelope-identity-and-tombstones|Event identity]] supplies the source-level foundation.'),
    ('Checkpoint both inputs and state', 'A successful checkpoint must tie the payment offset, risk offset, keyed join state and sink commit to one recovery boundary. If a worker restores old state but starts one source too far ahead, it can permanently miss a match; if it restarts too far behind without deduplication, it can emit the match twice. Record positions in the [[data-engineering/replay-manifest-and-audit-trail|replay manifest]] and verify the sink generation that acknowledged them.'),
    ('Give unmatched output a lifecycle', 'An outer join may emit a provisional payment-without-signal result. If an accepted late signal arrives before the horizon, retract or replace the provisional output, then publish the matched result under a distinct logical identity. A sink that only appends cannot represent this correction safely. State whether consumers see provisional rows, final rows or both, and test those semantics under replay.'),
    ('Rebuild beyond retained state', 'A correction older than the live join TTL cannot be reconstructed by increasing TTL after the fact. Replay both raw streams into a separate candidate from the oldest required source positions, or compute the affected interval in a bounded batch. Validate keys and totals against the current result, then switch the serving generation atomically. [[data-engineering/backfill-publication-boundary|Backfill publication]] avoids mixing the candidate with live output.'),
    ('Inject recovery faults', 'Crash after writing output but before checkpoint acknowledgement. Restart and prove that the sink still contains one logical match. Then expire state and introduce a valid historical correction; the live path must route it to replay instead of inventing an unmatched result. Record source positions, state snapshot, output IDs, provisional retractions and final counts for each attempt.')],
    '''import hashlib

def match_identity(payment_id, payment_revision, signal_id, signal_revision, rule_version):
    pieces = (payment_id, str(payment_revision), signal_id,
              str(signal_revision), rule_version)
    payload = "|".join(f"{len(piece)}:{piece}" for piece in pieces)
    return hashlib.sha256(payload.encode()).hexdigest()

matched_id = match_identity("pay-47", 2, "risk-83", 4, "interval-v3")
replayed_id = match_identity("pay-47", 2, "risk-83", 4, "interval-v3")
revised_id = match_identity("pay-47", 3, "risk-83", 4, "interval-v3")
assert matched_id == replayed_id
assert revised_id != matched_id''',
    'Computing one identity is O(B) time for B encoded identifier bytes and O(B) temporary space. The sink needs an index or merge key to deduplicate outputs; stateful retractions and retained source streams add storage. A full replay costs both source scans and candidate writes, so reserve it for intervals that can no longer be repaired from live retained state.',
    ['Do not build a result key from the worker attempt or wall-clock timestamp.', 'Do not append a new match while leaving an obsolete provisional result active.', 'Do not assume expired join state can be recovered from a newer checkpoint alone.'],
    ['data-engineering/interval-join-state-horizon-and-watermark-skew', 'data-engineering/event-envelope-identity-and-tombstones', 'data-engineering/keyed-state-checkpoints-and-recovery', 'data-engineering/backfill-publication-boundary', 'data-engineering/payment-risk-interval-join-project'], JOIN)

add('payment-risk-interval-join-project', 'Project: recover a payment-risk interval join',
    'Implement a bounded two-stream join that keeps accepted late matches, prevents replay duplicates and routes expired corrections through a candidate rebuild.', [
    ('Specify the workload', 'Create 470 payment events and risk signals keyed by merchant. Use a 47-minute look-back and 8-minute look-ahead, with three minutes of accepted lateness. Put several events under one hot merchant, a signal exactly on each interval endpoint and a counterpart one second outside. Define whether unmatched payments are provisional or only final. [[data-engineering/interval-join-state-horizon-and-watermark-skew|The horizon lesson]] supplies the eviction rule.'),
    ('Build with observable state', 'Track watermarks separately for payment and risk inputs, keyed record counts, bytes, checkpoint size and late drops. Buffer each side only while the opposite side can still send an accepted match. Simulate an idle risk partition that delays cleanup. Reject an implementation that evicts from a fixed wall-clock timer merely because the payment record has aged.'),
    ('Exercise replay identity', 'Assign stable pair IDs using source IDs, revisions and join-rule version. Crash after the sink receives one match but before checkpoint completion. Restore the recorded source positions and state, replay, and show exactly one current sink row for that logical pair. If a signal revision changes, publish the new pair and retire the old one under the documented correction policy. [[data-engineering/join-replay-output-identity-and-recovery|Replay identity]] is verified at the sink.'),
    ('Repair an old correction', 'Expire the live state, then deliver a correction for a payment older than the horizon. Send it to a dated replay queue rather than forcing it through the current join. Rebuild both inputs for the affected interval into a candidate, compare pair keys and merchant totals, then atomically publish the corrected generation. Keep the last-good generation readable until validation passes.'),
    ('Submit measurable proof', 'Provide endpoint tests, asymmetric-arrival trace, idle-partition trace, hot-key state peak, checkpoint metadata, crash/replay output IDs, provisional retractions and historical-rebuild diff. Include one intentionally too-short TTL run and show the missing valid match it causes. A green job status without these result checks is insufficient.')],
    '''from datetime import datetime, timedelta, timezone

payments = {"pay-47": ("merchant-29", datetime(2026, 10, 6, 10, 47, tzinfo=timezone.utc))}
signals = {"risk-83": ("merchant-29", datetime(2026, 10, 6, 10, 52, tzinfo=timezone.utc)),
           "risk-84": ("merchant-61", datetime(2026, 10, 6, 10, 51, tzinfo=timezone.utc))}

def candidate_pairs(payment_events, risk_events):
    return {(payment_id, signal_id)
            for payment_id, (payment_merchant, payment_at) in payment_events.items()
            for signal_id, (signal_merchant, signal_at) in risk_events.items()
            if payment_merchant == signal_merchant
            and payment_at - timedelta(minutes=47) <= signal_at
            <= payment_at + timedelta(minutes=8)}

first_attempt = candidate_pairs(payments, signals)
replayed_attempt = candidate_pairs(payments, signals)
sink_pairs = first_attempt | replayed_attempt
assert sink_pairs == {("pay-47", "risk-83")}
assert len(sink_pairs) == 1''',
    'The reference scans P × S pairs; a keyed time-indexed operator narrows probes to eligible records under each key but retains both sides until their horizons close. State bytes, checkpoint duration and sink merge cost rise with active keys and skew. Historical rebuilds require extra scans and candidate storage, so measure frequency separately from the live path.',
    ['Do not test only payment-first arrival order.', 'Do not accept two sink rows for one pair after a crash and replay.', 'Do not silently discard a correction simply because live state has expired.'],
    ['data-engineering/interval-join-state-horizon-and-watermark-skew', 'data-engineering/join-replay-output-identity-and-recovery', 'data-engineering/keyed-state-checkpoints-and-recovery', 'data-engineering/replay-manifest-and-audit-trail', 'data-engineering/streaming-risk-ledger-project'], JOIN, True)

add('direct-and-indirect-column-lineage', 'Direct and indirect column lineage',
    'A column can shape an output by supplying its value or by deciding which rows survive, and an impact graph should distinguish those two roles.', [
    ('Trace values and selection separately', 'For a revenue total, payment amount is a direct value input. Payment status may only decide which rows enter the sum; it is still an indirect dependency. A dataset-level edge between payments and revenue misses this distinction. Model each output field with source-field edges labelled as value, filter, join, grouping or ordering effects. [[data-engineering/pipeline-lineage-and-impact-analysis|Dataset lineage]] remains the outer graph, while field edges answer what a column change can affect.'),
    ('Include join and grouping keys', 'A region label in a report may come from a dimension table, yet payment region ID decides which dimension row joins. A change to either can move an amount between groups without changing the amount itself. Record the join key as an indirect dependency of the grouped total and the display label as a direct dependency of the output label. Do not infer that every column in every joined table affects every output field.'),
    ('Describe transformations honestly', 'A pass-through customer ID, a rounded currency conversion and a count of customers have different propagation properties. Record transformation kind and whether a masking step occurred, but do not mark hashing as irreversible protection without considering the input domain. A computed constant has no value-source edge, though a WHERE clause can still change whether its row exists. If SQL parsing cannot resolve a stored procedure or user function, mark the field relation unknown rather than fabricating confidence.'),
    ('Bind edges to a release', 'A view definition can change while an earlier table snapshot remains in use. Attach lineage edges to the transform revision and committed output generation; failed attempts do not become parents of the current answer. [[data-engineering/run-scoped-lineage-and-release-evidence|Run evidence]] lets an operator move from a published result to the actual code and input versions instead of to only a planned DAG.'),
    ('Test impact queries', 'Ask which outputs are affected if the payment status domain gains a new value. The graph should include the revenue total even though status contributes no numeric bytes. Ask which outputs are affected by renaming an unused ingestion field; they should not appear unless the field is propagated. Use hand-reviewed SQL fixtures to measure missed and spurious edges before relying on the graph for change approval.')],
    '''field_edges = {
    "mart.revenue_cents": {
        ("payments.amount_cents", "value"),
        ("payments.status", "filter"),
        ("payments.region_id", "join"),
    },
    "mart.region_name": {
        ("regions.name", "value"),
        ("payments.region_id", "join"),
    },
}

def impacted_outputs(source_field, edges):
    return {output for output, dependencies in edges.items()
            if any(field == source_field for field, _ in dependencies)}

assert impacted_outputs("payments.status", field_edges) == {"mart.revenue_cents"}
assert impacted_outputs("payments.region_id", field_edges) == {
    "mart.revenue_cents", "mart.region_name"}''',
    'For E stored field edges, a linear impact query is O(E) time and O(O) result space for O affected outputs. An inverse index improves repeated lookups but adds update and storage cost. Capturing full field relations across many transforms can grow much faster than table-level lineage; retain only verified edges and an explicit unknown state where extraction is incomplete.',
    ['Do not omit filter or join fields just because they do not supply output values.', 'Do not infer every source column affects every destination column.', 'Do not treat an unparseable transform as proof of no dependency.'],
    ['data-engineering/pipeline-lineage-and-impact-analysis', 'data-engineering/run-scoped-lineage-and-release-evidence', 'data-engineering/schema-compatibility-and-consumer-rollout', 'data-engineering/column-lineage-coverage-and-sensitive-change-gates', 'data-engineering/payment-column-impact-audit-project'], LINEAGE)

add('column-lineage-coverage-and-sensitive-change-gates', 'Column-lineage coverage and sensitive-change gates',
    'A field-impact graph is useful only when its coverage is visible and a sensitive source-field change cannot bypass unresolved paths.', [
    ('State what was observed', 'Report the number of published output fields, fields with verified edges, fields with inferred edges and fields whose transform remains opaque. Coverage is measured against actual published schema, not merely the SQL files the parser could read. A graph that omits a notebook, stored procedure or generated query can look tidy while missing the most important path. [[data-engineering/direct-and-indirect-column-lineage|Field lineage]] needs a confidence label on each edge.'),
    ('Walk both directions', 'For a proposed input change, traverse forward to outputs and consumers. For a suspicious output, traverse backward to candidate inputs and run generations. Keep direct and indirect paths visible; a consent flag used only in a filter can still alter a published customer count. Join against [[data-engineering/contract-to-test-compilation-and-negative-fixtures|contract rules]] to see which tests protect affected fields and which outputs have no explicit assertion.'),
    ('Gate sensitive changes', 'If a source field is classified as restricted, a new downstream edge must trigger access and masking review before release. Do not assume that a hashed value is safe for every consumer or that an aggregate cannot disclose a small group. If the path reaches an unknown transform, pause automatic approval for that branch and route it to an owner. [[data-engineering/lineage-metadata-minimization|Metadata minimization]] also limits who may inspect detailed paths and partition values.'),
    ('Compare graph to execution', 'A static parser may claim a column is used, but a runtime branch can be disabled for one release. Record the transform revision and actual successful run alongside static edges. Sample selected output values and candidate input versions where policy allows, without placing raw records in the broad catalog. A failed candidate can inform debugging but must not replace lineage for the currently published snapshot.'),
    ('Exercise a change request', 'Rename a harmless unused field, alter a payment amount column and add a consent condition. The impact query should return different sets and reasons. Intentionally hide one transform from the extractor: coverage must fall and the sensitive-change gate must fail closed for the affected path. Store reviewer decision, unknown edges, test results and final committed generation for later audit.')],
    '''published_fields = {
    "mart.revenue_cents", "mart.customer_count", "mart.region_name"
}
verified_edges = {"mart.revenue_cents", "mart.customer_count"}
unknown_transform_fields = {"mart.region_name"}

def lineage_gate(outputs, verified, unknown, sensitive_change):
    uncovered = outputs - verified
    if sensitive_change and (uncovered or unknown):
        return {"approved": False, "uncovered": uncovered | unknown}
    return {"approved": True, "uncovered": uncovered}

result = lineage_gate(published_fields, verified_edges,
                      unknown_transform_fields, sensitive_change=True)
assert result["approved"] is False
assert result["uncovered"] == {"mart.region_name"}''',
    'Coverage comparison is O(F) expected time and O(U) output state for F published fields and U uncovered fields. Forward and backward graph traversals cost O(V + E) in the inspected subgraph. Collecting verified field edges, running review gates and retaining run-specific evidence add metadata work, but prevent a high-confidence label from hiding an unobserved transform.',
    ['Do not report coverage only over fields a parser happened to recognize.', 'Do not treat unknown lineage as an empty dependency set.', 'Do not grant a sensitive change solely because the displayed output field is aggregated.'],
    ['data-engineering/direct-and-indirect-column-lineage', 'data-engineering/lineage-metadata-minimization', 'data-engineering/data-classification-and-access-boundaries', 'data-engineering/dataset-ownership-and-change-approval', 'data-engineering/payment-column-impact-audit-project'], LINEAGE)

add('payment-column-impact-audit-project', 'Project: audit a payment column change across a mart',
    'Build a field-level impact graph for a regional payment mart, expose an opaque transform and gate a sensitive source-column change with evidence.', [
    ('Model the pipeline', 'Create a raw payments feed, cleaned payments table, region dimension and revenue mart. Include output fields for regional revenue, customer count and region name. Give amount a direct aggregation edge, status a filter edge, region ID a join and group edge, and name a direct label edge. Pin each published dataset generation and transform revision. [[data-engineering/direct-and-indirect-column-lineage|The field relation model]] should distinguish changing values from changing row membership.'),
    ('Build impact queries', 'Implement forward lookup from source field to every reachable output and consumer, then backward lookup from one suspicious output to input fields and committed runs. Change payment status from a two-value domain to a three-value domain and show why it affects a revenue total even though status is not summed. Rename an unused landing field and show that it has no verified path into the mart.'),
    ('Expose the blind spot', 'Route the customer-count calculation through a stored procedure or opaque transform that the extractor cannot parse. Mark the output unknown, decrease coverage and require owner review before a sensitive field change. Do not invent all-to-all edges just to hide uncertainty. [[data-engineering/column-lineage-coverage-and-sensitive-change-gates|The coverage gate]] should identify the precise unresolved output and its owner.'),
    ('Test the release', 'Add a restricted customer identifier to the cleaned feed and attempt to propagate a derived identifier into the mart. Check field classification, access policy, masking review and small-group release rule. Simulate a failed candidate run, then a successful one; only the successful output generation becomes current lineage. Record a query result before and after the status change to validate the declared indirect edge.'),
    ('Deliver an audit trail', 'Submit the graph, edge types, coverage denominator, unknown-transform report, forward and backward query outputs, test results, access decision, failed and successful run IDs and final generation. Include one deliberately missing filter edge and show the impact query failing its reviewed fixture. A polished graph with an invisible blind spot does not pass this project.')],
    '''edges = {
    "clean.amount_cents": {"raw.amount_cents"},
    "clean.status": {"raw.status"},
    "mart.revenue_cents": {"clean.amount_cents", "clean.status"},
    "mart.customer_count": {"UNKNOWN:customer_counter"},
}

def downstream_fields(source_field, dependencies):
    reached = {source_field}
    frontier = [source_field]
    while frontier:
        current = frontier.pop()
        for output_field, inputs in dependencies.items():
            if current in inputs and output_field not in reached:
                reached.add(output_field)
                frontier.append(output_field)
    return reached - {source_field}

assert downstream_fields("raw.status", edges) == {
    "clean.status", "mart.revenue_cents"}
assert "mart.customer_count" not in downstream_fields("raw.status", edges)''',
    'The simple traversal scans E edges for each visited field and can cost O(V × E) without an inverse index; building that index reduces traversal to O(V + E) time and space for the affected graph. Field-level evidence and run versions add storage. Use them to focus review and tests, while keeping sensitive field paths restricted to authorized operators.',
    ['Do not treat a filter-only status column as irrelevant to revenue.', 'Do not publish a sensitive derived identifier before access review.', 'Do not convert an opaque transform into an asserted no-impact result.'],
    ['data-engineering/direct-and-indirect-column-lineage', 'data-engineering/column-lineage-coverage-and-sensitive-change-gates', 'data-engineering/run-scoped-lineage-and-release-evidence', 'data-engineering/data-classification-and-access-boundaries', 'data-engineering/governed-customer-mart-project'], LINEAGE, True)


CROSSLINKS = [
    ('data-engineering/stream-table-join-and-reference-versions', 'data-engineering/interval-join-state-horizon-and-watermark-skew'),
    ('data-engineering/watermark-retention-and-late-corrections', 'data-engineering/interval-join-state-horizon-and-watermark-skew'),
    ('data-engineering/event-envelope-identity-and-tombstones', 'data-engineering/join-replay-output-identity-and-recovery'),
    ('data-engineering/keyed-state-checkpoints-and-recovery', 'data-engineering/join-replay-output-identity-and-recovery'),
    ('data-engineering/streaming-risk-ledger-project', 'data-engineering/payment-risk-interval-join-project'),
    ('data-engineering/backfill-publication-boundary', 'data-engineering/payment-risk-interval-join-project'),
    ('data-engineering/pipeline-lineage-and-impact-analysis', 'data-engineering/direct-and-indirect-column-lineage'),
    ('data-engineering/schema-compatibility-and-consumer-rollout', 'data-engineering/direct-and-indirect-column-lineage'),
    ('data-engineering/lineage-metadata-minimization', 'data-engineering/column-lineage-coverage-and-sensitive-change-gates'),
    ('data-engineering/dataset-ownership-and-change-approval', 'data-engineering/column-lineage-coverage-and-sensitive-change-gates'),
    ('data-engineering/governed-customer-mart-project', 'data-engineering/payment-column-impact-audit-project'),
    ('data-engineering/run-scoped-lineage-and-release-evidence', 'data-engineering/payment-column-impact-audit-project'),
]


if __name__ == '__main__':
    publish(LESSONS, (JOIN, LINEAGE), CROSSLINKS,
            'aitrove-data-engineering-stream-lineage-import-20261006.json', 7930)
