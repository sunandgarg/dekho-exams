"""Extend the local AI & Data preview with experimentation and feature-store paths."""
import datetime
import html
import json
from pathlib import Path
import re
import uuid

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
rows = [row for row in rows if not row['path'].startswith(('online-experimentation/', 'feature-stores/'))]
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
lessons = []

def add(path, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path=path, title=title, summary=summary, sections=sections,
                        code=code, cost=cost, mistakes=mistakes, related=related))

add('online-experimentation/decision-estimand-and-randomization-unit',
    'Experiment contract: decision, estimand and assignment unit',
    'An online experiment estimates an effect for a declared population, outcome and assignment unit; changing any one changes the question.', [
    ('Write the release question', 'AI Trove could compare two lesson recommendation policies for active learners. The decision is whether to ship the new policy; the primary outcome might be a qualifying lesson completion within seven days of assignment. Specify whether the effect is among all eligible learners or only people who opened the feed. [[applied-statistics/population-estimand-and-sampling-frame|The population and estimand]] must precede a dashboard query.'),
    ('Choose an independent unit', 'Assign by stable learner ID if the same learner can return on several devices. Randomizing each page view causes a person to encounter both variants and changes the estimand to a page-view effect. If a classroom shares lessons and decisions, classroom assignment may be safer, but cluster correlation reduces effective sample size. Keep the unit, salt, allocation and assignment version in an immutable manifest.'),
    ('Define eligibility before treatment', 'A learner is eligible based on facts known before policy exposure: account state, locale and a stable consent rule. Do not exclude learners after assignment because the new feed loaded slowly or returned an empty slate. Those failures are part of the effect. Record assignment once, then log every later eligibility or suppression decision separately so the intention-to-treat population stays recoverable.'),
    ('Exercise the boundary', 'A learner enters on a phone and returns on a laptop; both requests should receive the same variant. A second learner with no eligible lessons still belongs to the assigned population if eligibility was declared at account level. The test packet should make clear whether this empty slate counts as a poor experience, a technical failure or a predeclared exclusion.')],
    'import hashlib\n\ndef assign_variant(learner_id, experiment_salt, treatment_share=0.5):\n    digest = hashlib.sha256(f"{experiment_salt}:{learner_id}".encode()).digest()\n    bucket = int.from_bytes(digest[:8], "big") / (1 << 64)\n    return "treatment" if bucket < treatment_share else "control"',
    'Hash assignment is O(L) time for an ID and salt of length L and O(1) retained state. Stable hashing avoids a lookup on each request, but changing the salt or ID mapping midrun invalidates assignment continuity.',
    ['Do not randomize page views when the effect is defined per learner.', 'Do not remove post-assignment failures from the primary population.', 'Do not change the allocation salt without recording a new experiment version.'],
    ['online-experimentation/exposure-and-event-logging','online-experimentation/sample-ratio-and-aa-diagnostics','applied-statistics/randomization-unit-and-experiment-design','causal-inference/estimand-and-counterfactual-unit'])

add('online-experimentation/exposure-and-event-logging',
    'Experiment telemetry: assignment, exposure and outcome events',
    'Assignment says who was placed in a variant; exposure says who could encounter it; outcome events say what happened afterward.', [
    ('Keep three event families', 'Store assignment with learner, experiment, variant and version. Emit exposure only when the policy actually renders a meaningful feed, and write completion outcomes under their own event ID and event time. A retry may resend any event. [[data-engineering/idempotent-load-and-checkpoint|Idempotent loading]] should collapse retries without erasing legitimate repeated activity.'),
    ('Preserve the primary analysis', 'If the treatment fails before rendering, that failure must not disappear from the assigned-population estimate. Exposure-only analysis answers a narrower question and can be biased because exposure depends on the variant. Report both assignment and exposure counts, with reasons for nonexposure. A server-side flag read is not proof a learner saw the recommendation.'),
    ('Make joins time-aware', 'A completion before assignment cannot be an outcome of the assigned variant. Decide whether a qualifying completion requires a lesson from the feed or any lesson; the former may reflect ranking, the latter overall learning activity. Use event identity, learner identity and an explicit attribution horizon. Late mobile uploads may revise counts, so freeze a maturity cutoff for final reporting.'),
    ('Test duplicate and delayed data', 'Create one assignment, one rendered feed, two deliveries of the same completion event and another completion uploaded after the seven-day reporting cutoff. The duplicate must count once; the late upload may revise a provisional result under the documented correction rule. A treatment rendering failure must remain in the assignment table even when no exposure exists.')],
    'def unique_qualifying_events(events, assigned_at, horizon_end):\n    seen_ids = set()\n    qualifying = []\n    for event in events:\n        if event["event_id"] in seen_ids:\n            continue\n        seen_ids.add(event["event_id"])\n        if assigned_at <= event["occurred_at"] < horizon_end:\n            qualifying.append(event)\n    return qualifying',
    'A pass over N events is O(N) expected time and O(U + Q) memory for U event IDs and Q qualifying events. At scale, durable event keys and partitioned time windows replace an unbounded in-memory set.',
    ['Do not equate a feature-flag read with real exposure.', 'Do not drop failed renders from intention-to-treat analysis.', 'Do not count retried outcome events twice.'],
    ['online-experimentation/decision-estimand-and-randomization-unit','online-experimentation/sample-ratio-and-aa-diagnostics','data-engineering/idempotent-load-and-checkpoint','streaming-analytics/event-time-window-and-boundaries'])

add('online-experimentation/sample-ratio-and-aa-diagnostics',
    'Experiment integrity: sample-ratio mismatch and A/A checks',
    'An allocation mismatch or telemetry asymmetry can invalidate an effect estimate before statistical significance becomes relevant.', [
    ('Compare assigned counts', 'For a 50/50 allocation, assignment counts should fluctuate around equal shares. A large persistent departure can signal a broken hash, a changed eligibility gate or missing logs. Compare observed counts with configured allocation using an appropriate diagnostic and inspect segments. Do not apply the check only to exposed users; variant-dependent rendering can change exposure without changing assignment.'),
    ('Trace the funnel', 'Count eligible, assigned, rendered and outcome-bearing learners by variant and day. A treatment-specific fall from assignment to exposure may indicate page failure rather than reduced interest. Join by stable IDs and investigate data loss before analyzing completions. [[online-experimentation/exposure-and-event-logging|The event contract]] keeps assignment, exposure and outcome roles distinct.'),
    ('Run an A/A rehearsal', 'Before shipping a changed policy, assign two groups that receive identical behavior. Check that event collection, deduplication and metrics behave symmetrically. An A/A run does not prove the product metric will move as expected, but it can expose broken joins, skewed assignment and reporting logic. Keep its analysis procedure fixed before the live comparison.'),
    ('Use a concrete fixture', 'Assign 2,350 learners to control and 2,350 to treatment, then remove 80 treatment exposure events while retaining assignments. The assignment ratio remains equal; the exposure funnel no longer does. An analyst should not repair the exposure gap by excluding the affected treatment learners from the primary effect estimate. Record the missing-render cause.')],
    'def allocation_gap(assignment_rows, expected_treatment_share):\n    total = len(assignment_rows)\n    if total == 0:\n        return None\n    observed = sum(row["variant"] == "treatment" for row in assignment_rows) / total\n    return observed - expected_treatment_share',
    'A count pass is O(N) time and O(1) auxiliary space. A full integrity report adds group-by state for days and segments; every diagnostic needs a known expected allocation and an investigation threshold set before reading results.',
    ['Do not declare a clean experiment from a single pooled assignment count.', 'Do not run the allocation diagnostic only on exposed users.', 'Do not ignore a broken A/A run because the treatment result looks attractive.'],
    ['online-experimentation/exposure-and-event-logging','online-experimentation/metric-denominators-and-guardrails','applied-statistics/randomization-unit-and-experiment-design','data-engineering/quality-quarantine-and-reconciliation'])

add('online-experimentation/metric-denominators-and-guardrails',
    'Experiment metrics: denominators, guardrails and missing outcomes',
    'A metric is a complete counting rule, including population, numerator, denominator, window and missing-data treatment.', [
    ('Specify the primary outcome', 'For seven-day learning progress, use assigned eligible learners as the denominator and learners with at least one qualifying completion as the numerator. If treatment changes feed rendering, using exposed learners in the denominator can hide a failure. State whether multiple completions affect the metric or only the first one. [[online-experimentation/decision-estimand-and-randomization-unit|The estimand]] chooses the correct population.'),
    ('Add protective metrics', 'Track page load failures, empty slates, withdrawal requests and serious latency regressions as guardrails. A higher completion rate does not justify shipping if the feed begins failing for a subgroup. Guardrails need thresholds and owners before launch. A missing metric should stop a decision, not appear as zero harm. Segment results by device and new versus returning learners.'),
    ('Treat ratios with care', 'A click-through ratio can change when the treatment alters the number of displayed lessons, even if learner behavior does not. Define whether clicks are counted per assigned learner, per rendered feed or per displayed item. Report both numerator and denominator by arm so a change in opportunity is visible. Aggregating event-level ratios can overweight highly active learners.'),
    ('Check an example', 'Control assigns 47 learners and 19 complete a lesson; treatment assigns 49 and 23 complete. The raw rates are about 40.4 and 46.9 percent. Now suppose eight treatment learners never receive a feed. Keeping them in the assigned denominator reflects the release experience; excluding them creates an exposure-conditioned result with a different meaning.')],
    'def completion_rate(assigned_ids, completed_ids):\n    assigned = set(assigned_ids)\n    if not assigned:\n        return None\n    return len(assigned & set(completed_ids)) / len(assigned)',
    'Set-based counting costs O(A + C) expected time and space for A assigned and C completed IDs. Warehouse implementations should deduplicate event IDs and learner IDs before aggregation, then preserve numerator and denominator in the result packet.',
    ['Do not switch denominators after seeing a favorable result.', 'Do not interpret missing guardrail telemetry as zero incidents.', 'Do not average per-event ratios when the estimand is per learner.'],
    ['online-experimentation/decision-estimand-and-randomization-unit','online-experimentation/sequential-reads-and-variance-reduction','online-experimentation/ramp-rollback-and-decision-packet','applied-statistics/confidence-interval-coverage'])

add('online-experimentation/sequential-reads-and-variance-reduction',
    'Experiment analysis: repeated looks, precision and pre-period covariates',
    'Analysis timing and variance reduction are design choices; changing them after reading results can turn noise into a launch claim.', [
    ('Fix the read schedule', 'A daily dashboard is useful for harm monitoring, but repeatedly stopping at the first small p-value inflates false-positive risk under a fixed-horizon test. Choose a fixed final horizon or a valid sequential procedure in advance. Keep separate emergency guardrail rules for clear harm. [[applied-statistics/multiple-comparisons-and-stopping-rule|The stopping rule]] belongs in the experiment manifest.'),
    ('Use pre-treatment information', 'A learner’s prior completion rate may reduce variance when included as a covariate measured before assignment. Post-assignment activity is affected by treatment and cannot be used as an ordinary control variable. Freeze the covariate extraction and missing-value rule before the run. Test that the pre-period feature is balanced across assignment arms.'),
    ('Report uncertainty and size', 'Show the estimated difference in completion probability with an interval, sample counts and the smallest effect worth shipping. A statistically detectable gain can still be too small to pay for higher latency. Conversely, a wide interval crossing zero does not prove no effect. Present guardrail uncertainty and subgroup sizes without declaring a winner from every exploratory slice.'),
    ('Run a dry analysis', 'Give each learner a pre-period count and a seven-day outcome, with one missing pre-period value. Fit the planned adjustment on the allowed pre-period signal only. Compare raw and adjusted estimates, then confirm the assigned population and outcome window are identical. If the adjustment greatly changes the sign, inspect missingness and extreme covariate values before trusting it.')],
    'def centered_preperiod_values(values_by_learner):\n    observed = [value for value in values_by_learner.values() if value is not None]\n    if not observed:\n        return {}\n    center = sum(observed) / len(observed)\n    return {learner_id: value - center for learner_id, value in values_by_learner.items()\n            if value is not None}',
    'Centering P observed values costs O(P) time and O(P) space. An adjusted estimator has additional fitting cost and assumptions; evaluate its precision on a rehearsal before adding it to a production decision packet.',
    ['Do not peek each day and apply a fixed-horizon significance rule at every look.', 'Do not adjust for a covariate measured after assignment.', 'Do not call a wide inconclusive interval evidence of no effect.'],
    ['online-experimentation/metric-denominators-and-guardrails','online-experimentation/ramp-rollback-and-decision-packet','applied-statistics/multiple-comparisons-and-stopping-rule','causal-inference/confounder-graph-and-covariate-timing'])

add('online-experimentation/ramp-rollback-and-decision-packet',
    'Experiment rollout: ramp gates, rollback and a reviewable decision',
    'An experiment ends with a reproducible launch decision that includes telemetry integrity, effect size and release risk.', [
    ('Ramp under gates', 'Start with a small allocation that can reveal failures, then expand only after assignment logs, exposure funnel, latency and severe-error guardrails pass. Every ramp stage has its own allocation and time boundary. Mixing ramp stages without recording them can obscure day-of-week and novelty effects. A policy may be safe for a small group yet fail under full candidate volume.'),
    ('Protect continuity', 'Persist learner assignment across ramps unless the design explicitly permits reassignment. If the new policy is rolled back, stop new treatment exposure and record the rollback time while retaining the event stream for outcome maturation. [[mlops/shadow-canary-and-rollback|Canary and rollback practices]] help separate monitoring from the final causal estimate.'),
    ('Write the decision packet', 'Include protocol version, eligibility rule, assignment salt, event definitions, sample-ratio diagnostics, exposure counts, primary effect with interval, guardrails, subgroup counts, missing-label status and deviations. State a ship, revise or stop decision against thresholds chosen before analysis. A reviewer should reconstruct the denominator and one learner’s variant from packet data.'),
    ('Rehearse a failure', 'During a 15 percent ramp, suppose treatment feed errors rise and exposure falls while assignments remain balanced. Roll back based on the predeclared error gate, even if early completions look favorable. Preserve the unexposed assigned learners in the analysis. If the issue is fixed, start a separately versioned run rather than silently continuing the old result.')],
    'def ramp_gate(error_rate, exposure_gap, max_error_rate, max_exposure_gap):\n    return error_rate <= max_error_rate and abs(exposure_gap) <= max_exposure_gap',
    'A gate evaluation is O(1) after counters are computed. Computing counters over N requests is O(N) time with bounded aggregate state; keep raw event lineage because a broken counter can otherwise make the rollback decision unauditable.',
    ['Do not continue a changed treatment under the old experiment version.', 'Do not ship on one favorable metric when a predeclared guardrail fails.', 'Do not erase rollback-era outcomes from the assigned population.'],
    ['online-experimentation/sample-ratio-and-aa-diagnostics','online-experimentation/lesson-feed-experiment-project','mlops/shadow-canary-and-rollback','recommendation-systems/offline-evaluation-and-temporal-split'])

add('online-experimentation/lesson-feed-experiment-project',
    'Project: run a guarded lesson-feed experiment',
    'Design and replay an online comparison of two lesson-feed policies, including assignment, failure handling and a written launch decision.', [
    ('Create the protocol', 'Declare active learners as the population, learner ID as the assignment unit and qualifying seven-day lesson completion as the primary outcome. Set a fixed evaluation horizon, minimum useful gain and latency and empty-slate guardrails. Record an immutable salt and eligibility rule. [[online-experimentation/decision-estimand-and-randomization-unit|The experiment contract]] should let another engineer assign the same learner twice and get the same variant.'),
    ('Build event fixtures', 'Generate assignment, render, completion and error events for both policies, including repeated delivery, one learner switching devices and a treatment-only render failure. Add an outcome arriving after the provisional report. Deduplicate events and produce daily counts for eligible, assigned, exposed and completed learners. Confirm the assigned-population denominator retains the render failure.'),
    ('Analyze and decide', 'Run an A/A integrity check, then the treatment comparison. Report sample-ratio diagnostics, effect and interval, guardrail values, pending outcomes and daily ticket-worthy failures. Test a small ramp gate and a rollback event. Do not tune the metric or fixed-horizon stopping rule after viewing treatment data. Keep exploratory device slices labeled as such.'),
    ('Deliver evidence', 'Submit protocol, assignment function, event schema, replay fixture, analysis code, output packet and decision memo. Include one line-level trace from raw completion event to aggregate numerator and one learner who was assigned but never exposed. The decision memo must say why the launch gate passed or failed, not merely quote a p-value.')],
    'from hashlib import sha256\n\ndef stable_learner_arm(learner_id, salt):\n    digest = sha256(f"{salt}:{learner_id}".encode()).digest()\n    return "B" if int.from_bytes(digest[:8], "big") % 2 else "A"\n\nassert stable_learner_arm("learner-47", "lesson-feed-v2") == stable_learner_arm("learner-47", "lesson-feed-v2")',
    'Assignment costs O(L) time for an identifier of length L and constant retained state. End-to-end replay costs O(E) expected time for E events plus dedup storage; keep the event fixture small but preserve the same counting and correction rules used at scale.',
    ['Do not change learner assignment between devices.', 'Do not exclude failed treatment renders from the primary estimate.', 'Do not treat a provisional late-outcome report as final.'],
    ['online-experimentation/exposure-and-event-logging','online-experimentation/ramp-rollback-and-decision-packet','applied-statistics/receipt-review-experiment-project','recommendation-systems/lesson-feed-project'])

add('feature-stores/entity-feature-and-availability-contract',
    'Feature-store contract: entity keys, event time and availability',
    'A feature is useful only when its entity, computation, timestamp and prediction-time availability are explicit.', [
    ('Define the entity', 'For receipt triage, a merchant risk count may be keyed by merchant ID while a receipt amount is keyed by receipt ID. Joining the former on an unversioned display name can combine unrelated merchants after a rename. Specify key normalization, null policy and one-row-per-key guarantees. [[data-science/dataset-grain-and-join-cardinality|Dataset grain]] still governs a feature store, even when feature retrieval appears to be one API call.'),
    ('Separate clocks', 'An event can occur at 09:00, reach the warehouse at 09:08 and become queryable at 09:14. A model scoring at 09:05 cannot use that value, even if a historical join based only on event time would select it. Store event time, ingestion time and feature availability or materialization time. [[machine-learning/prediction-time-feature-availability|Prediction-time availability]] is a release contract, not a comment in a query.'),
    ('Specify meaning and ownership', 'Give each feature a unit, window, aggregation rule, missing-value meaning, owner, retention period and version. “Merchant failures in 47 hours” must clarify whether retries, rejected receipts or later corrections count. Separate private learner data from public lesson metadata; a convenient shared registry is not permission to expose every feature to every model.'),
    ('Test a late event', 'A receipt submitted at 09:00 but ingested at 09:08 must be absent from a 09:05 prediction. A correction recorded at 10:20 may revise a later snapshot without changing the earlier training example. Create two merchants with the same display name and confirm key-based lookup keeps them separate. A missing entity should produce an explicit missing marker.')],
    'def available_feature(values, entity_id, decision_time):\n    eligible = [value for value in values\n                if value["entity_id"] == entity_id\n                and value["event_at"] <= decision_time\n                and value["available_at"] <= decision_time]\n    return max(eligible, key=lambda value: (value["event_at"], value["available_at"]), default=None)',
    'A list scan costs O(V) time and O(V) temporary memory for V records. An indexed entity and availability-time table can reduce repeated retrieval work, but the chosen value must still obey both the decision cutoff and feature version.',
    ['Do not join entities by a mutable display label.', 'Do not confuse event time with the time a feature became available.', 'Do not publish an unnamed null as if it were a valid zero.'],
    ['feature-stores/historical-point-in-time-join','feature-stores/online-materialization-and-staleness','data-engineering/warehouse-history-asof-join','machine-learning/prediction-time-feature-availability'])

add('feature-stores/historical-point-in-time-join',
    'Historical feature retrieval: point-in-time joins without future leakage',
    'Training rows must retrieve the feature value that would have been visible when each prediction was made.', [
    ('Build entity rows first', 'Create one row per historical decision with entity ID, decision time, label horizon and an immutable row ID. Fetch features against those rows, not against the latest warehouse snapshot. A conventional as-of join chooses a value whose event time precedes the decision, but it must also respect availability time when ingestion lag or backfills exist. [[feature-stores/entity-feature-and-availability-contract|The feature contract]] defines both clocks.'),
    ('Handle ties and corrections', 'Multiple values can share the same event time. Choose by a deterministic correction sequence or availability timestamp and record that rule. A later corrected value should not replace the original in a training row whose decision predates the correction. Set a lookback limit so a 14-month-old value is not silently used as current information.'),
    ('Preserve missingness', 'Some entities have no prior feature. Return null with a missing indicator and declared default behavior instead of borrowing a later value. A missing rate that differs sharply between training and serving may indicate delayed materialization or a bad entity key. [[mlops/feature-training-serving-parity|Parity checks]] should compare both values and missing markers for sampled decisions.'),
    ('Use a two-row fixture', 'Merchant M has a count of 5 available at 08:45, a count of 8 whose event time is 09:00 but availability is 09:12, and decisions at 09:05 and 09:20. The first decision sees 5; the second can see 8. Add a correction available at 10:00 and verify it cannot rewrite the earlier rows.')],
    'def point_in_time_value(feature_rows, entity_id, decision_time):\n    matches = [row for row in feature_rows\n               if row["entity_id"] == entity_id\n               and row["event_at"] <= decision_time\n               and row["available_at"] <= decision_time]\n    return max(matches, key=lambda row: (row["event_at"], row["available_at"]), default=None)',
    'A naive join over R entity rows and F feature rows costs O(R times F). Partitioning by entity and indexing event and availability times reduces candidate scans; materializing historical training sets consumes storage but makes a run reproducible.',
    ['Do not join historical labels to the newest feature row.', 'Do not let a late correction alter an older prediction snapshot.', 'Do not hide absent prior values with a future fill.'],
    ['feature-stores/entity-feature-and-availability-contract','feature-stores/offline-online-parity-and-tests','data-engineering/warehouse-history-asof-join','machine-learning/prediction-time-feature-availability'])

add('feature-stores/feature-view-version-and-lineage',
    'Feature definitions: versioned views, ownership and lineage',
    'A registry is useful when feature definitions are executable contracts with owners, inputs and compatibility rules.', [
    ('Version the computation', 'Changing a 47-hour failure count from event-time windows to ingestion-time windows changes the feature even if its name stays the same. Assign a semantic version or new feature name, record the transform code and input contract, and identify models that consume it. [[mlops/run-manifest-and-artifact-lineage|Model lineage]] must resolve the exact feature definition used for training and inference.'),
    ('Document freshness and type', 'Store entity type, value type, units, allowed nulls, expected range, update cadence and maximum serving age. A count below zero is invalid; an old count may be valid data but unsafe for a live decision. Define whether a feature is batch-computed, stream-updated or request-time. A registry entry should make those retrieval modes obvious to callers.'),
    ('Review access and lifecycle', 'A learner-level feature can contain sensitive behavior. Apply access policy at the feature view and underlying store, retain only what the use case requires, and delete or invalidate values under the relevant policy. Deprecating a view requires finding dependent models and migration dates; deleting the old definition before a historical model can be reproduced breaks auditability.'),
    ('Rehearse an incompatible change', 'Version one count excludes retried receipt events; version two accidentally includes them. Run both against the same fixture and show the mismatch before migration. A model trained on version one should not silently receive version two online. The release packet should include owner approval, parity test and a rollback path to the previous materialization.')],
    'def validate_count_feature(record, max_age_minutes, now_minute):\n    if record["value"] is None or record["value"] < 0:\n        return False\n    return 0 <= now_minute - record["materialized_minute"] <= max_age_minutes',
    'Validation is O(1) per record and O(N) for N records. Registry lookups can be cached, but cache entries must include the definition version; otherwise a deployment can mix a new transform with old validation limits.',
    ['Do not reuse a feature name after changing its meaning.', 'Do not treat a registry as an access-control substitute.', 'Do not delete historical definitions needed to reproduce a released model.'],
    ['feature-stores/entity-feature-and-availability-contract','feature-stores/backfill-delete-and-publication','mlops/run-manifest-and-artifact-lineage','data-engineering/source-contract-and-raw-landing'])

add('feature-stores/online-materialization-and-staleness',
    'Online feature serving: materialization, staleness and fallback',
    'Online retrieval should return a versioned value with its age and a defined response when the feature is absent or stale.', [
    ('Separate stores by workload', 'Historical retrieval scans past entity states for training; online serving needs low-latency reads for current decisions. Materialization copies selected feature values to a serving store under a known cutoff. This is a second publication step, not proof the values are fresh. [[data-engineering/backfill-publication-boundary|An atomic publication boundary]] prevents a partly updated batch from appearing as a complete snapshot.'),
    ('Bound age and latency', 'Set an age limit for each feature based on its decision role. A lesson catalog attribute may tolerate a longer delay than a current fraud signal. At request time, log feature version, value timestamp, age, missing flag and retrieval latency. If the store times out, use a documented fallback or decline the decision; never substitute a silent zero for an unknown risk count.'),
    ('Avoid partial feature vectors', 'A model expecting features from one coherent snapshot can behave unpredictably when one key has the new materialization and another has the old one. Use snapshot IDs or compatible per-view versions in the request contract. If mixed versions are permitted, test them explicitly. [[mlops/feature-training-serving-parity|Training-serving parity]] should include timestamp and default behavior, not merely value equality.'),
    ('Run a stale-key fixture', 'Merchant M has a value 7 materialized at minute 120, and the decision arrives at minute 173 with a maximum age of 47 minutes. The value is stale. A newly registered merchant has no row; return missing with fallback metadata. Simulate one serving timeout and verify the request trace distinguishes missing, stale and unavailable states.')],
    'def online_lookup(feature_by_entity, entity_id, now_minute, max_age_minutes):\n    record = feature_by_entity.get(entity_id)\n    if record is None:\n        return "missing", None\n    age = now_minute - record["materialized_minute"]\n    if age < 0:\n        return "invalid-time", None\n    if age > max_age_minutes:\n        return "stale", None\n    return "ready", record["value"]',
    'A hash-map lookup is O(1) expected time and O(1) request space, while the online store retains O(E) entity records. Network latency, serialization and cache invalidation dominate a real request; measure tail latency and stale-key rate.',
    ['Do not equate successful lookup with fresh data.', 'Do not collapse missing, stale and timeout into the same zero default.', 'Do not publish a partly refreshed vector without a compatibility rule.'],
    ['feature-stores/entity-feature-and-availability-contract','feature-stores/offline-online-parity-and-tests','feature-stores/backfill-delete-and-publication','mlops/feature-training-serving-parity'])

add('feature-stores/offline-online-parity-and-tests',
    'Feature parity: compare historical replay with online observations',
    'A shared feature name does not guarantee that training and serving compute the same value at the same decision time.', [
    ('Sample real decisions', 'Log entity ID, decision timestamp, online feature value, definition version, snapshot ID and missing state for a privacy-approved sample. Reconstruct the same decision from the historical store using its availability cutoff. Compare both value and null status. [[feature-stores/historical-point-in-time-join|The historical join]] must use the actual decision time, not the day the audit runs.'),
    ('Classify mismatches', 'Differences can come from late input, transform versions, entity-key normalization, rounding, TTL, correction policy or materialization lag. Count each cause separately. An aggregate parity percentage can hide a severe mismatch among new merchants or one high-risk segment. Report age distribution and misses alongside exact or tolerance-based value comparisons.'),
    ('Test boundary cases', 'Include a late event, a duplicate delivery, a deleted entity, a null value and an online timeout. The audit should show which cases are expected divergence and which are defects. A model may have an allowed freshness window, but the test must not declare any amount of delay acceptable after observing the result.'),
    ('Set a release gate', 'Run parity checks before promoting a model or changing a feature view. If the mismatch exceeds the predeclared tolerance, block promotion and attach a reproducible case with raw event IDs and both transform versions. [[mlops/model-registry-promotion-gates|Promotion gates]] should include feature health, because a sound model can fail when its input contract drifts.')],
    'def parity_mismatches(online_values, replay_values):\n    mismatches = []\n    for decision_id, online_record in online_values.items():\n        replay_record = replay_values.get(decision_id)\n        if replay_record != online_record:\n            mismatches.append(decision_id)\n    return mismatches',
    'Comparing D decision records costs O(D) expected time and O(M) output space for M mismatches when both sides are keyed. Replaying features may cost far more; use bounded samples and preserve enough lineage to reproduce each mismatch.',
    ['Do not compare online now with an unrelated historical timestamp.', 'Do not report parity without null and freshness comparisons.', 'Do not waive a severe subgroup mismatch behind a strong pooled rate.'],
    ['feature-stores/historical-point-in-time-join','feature-stores/online-materialization-and-staleness','mlops/feature-training-serving-parity','mlops/model-registry-promotion-gates'])

add('feature-stores/backfill-delete-and-publication',
    'Feature operations: backfills, deletion and atomic publication',
    'Correcting historical features and removing entities require controlled publication so training and serving do not read half-complete state.', [
    ('Recompute in isolation', 'Build a corrected feature snapshot into a separate version, preserving the old snapshot for comparison. Reconcile entity counts, missing rates, value distributions and several decision-time examples before switching readers. A backfill can repair a historical data error, but it must not make that repaired value appear available before it was actually known in a past online decision. [[data-engineering/backfill-publication-boundary|The publication boundary]] separates computation from visibility.'),
    ('Handle deletion explicitly', 'If an entity is withdrawn or data must be removed, delete or invalidate its online key, cached value and future historical retrieval under the applicable policy. A deletion tombstone must outrank a delayed materialization job; otherwise replay can resurrect the entity. Track downstream training datasets and model artifacts that may require separate retention or remediation decisions.'),
    ('Plan rollback', 'Version the source offsets, transform, feature view and online materialization together. If a new snapshot fails parity or freshness checks, return to the last approved snapshot while keeping deletion gates active. A rollback cannot revive a record that must remain withdrawn. [[feature-stores/offline-online-parity-and-tests|Parity evidence]] belongs in the switch decision.'),
    ('Exercise a race', 'Start building version 48 while version 47 serves. Delete merchant M, then let an old worker try to publish M from its stale batch. The serving layer must retain the tombstone. Add a correction to another merchant and confirm the new snapshot appears only after validation. A request trace should identify one coherent snapshot version.')],
    'def publishable_entities(candidate_values, deleted_entity_ids):\n    deleted = set(deleted_entity_ids)\n    return {entity_id: value for entity_id, value in candidate_values.items()\n            if entity_id not in deleted}',
    'Filtering E entities is O(E + D) expected time and O(E + D) memory for D tombstones. Durable systems need transactional or versioned publication plus deletion precedence, not merely this in-memory filter.',
    ['Do not publish partially reconciled backfill output.', 'Do not allow a delayed worker to resurrect a deleted entity.', 'Do not roll back a privacy deletion with an older feature snapshot.'],
    ['feature-stores/feature-view-version-and-lineage','feature-stores/online-materialization-and-staleness','data-engineering/backfill-publication-boundary','data-engineering/cdc-replay-and-deletes'])

add('feature-stores/receipt-triage-feature-project',
    'Project: build a point-in-time receipt-triage feature service',
    'Build a small offline and online feature path for merchant receipt triage, then prove historical availability and serving parity.', [
    ('Write contracts and fixture', 'Define a merchant key, a 47-hour rejected-receipt count and a last-submission-age feature. Give raw events event time, ingestion time, immutable event ID and correction version. Add a late event, a retry, a renamed merchant, a deletion and a new merchant with no history. [[feature-stores/entity-feature-and-availability-contract|The feature contract]] must state units, missing policy, owner and prediction cutoff.'),
    ('Build historical retrieval', 'Create decision rows at two times for each merchant. Retrieve only values whose event and availability times meet each decision cutoff, with deterministic tie handling. Show one row where a late event would leak if only event time were checked. Compare your output with a deliberately naive latest-value join and explain the difference for a specific decision ID.'),
    ('Serve and validate', 'Materialize a versioned online snapshot. Return value, age, version and missing or stale status for each request. Add a TTL, deletion gate and rollback path. Sample request traces and replay the corresponding historical decisions; report exact parity, missing-state parity and mismatch reasons. Use a small fixture, but keep the same cutoff logic in the replay and serving code.'),
    ('Deliver a release packet', 'Submit schema, transform, fixture, decision rows, backfill manifest, parity report and one deletion-race test. State the expected cost of each retrieval mode and the operational response to an online timeout. A reviewer should be able to reconstruct one training row and one online response from raw events and version IDs.')],
    'def latest_visible_count(records, merchant_id, decision_minute):\n    eligible = [record for record in records\n                if record["merchant_id"] == merchant_id\n                and record["event_minute"] <= decision_minute\n                and record["available_minute"] <= decision_minute]\n    latest = max(eligible, key=lambda record: (record["event_minute"], record["available_minute"]), default=None)\n    return None if latest is None else latest["count"]',
    'A fixture scan costs O(F) time and O(F) temporary space for F feature records per decision. A production historical join needs indexed partitions or a batch retrieval plan; online lookup needs bounded latency and versioned publication.',
    ['Do not train from a feature value that arrived after the decision.', 'Do not make a deleted merchant reappear during rollback.', 'Do not mark stale online data as fresh because the key exists.'],
    ['feature-stores/historical-point-in-time-join','feature-stores/offline-online-parity-and-tests','feature-stores/backfill-delete-and-publication','mlops/receipt-triage-release-project'])

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
 'online-experimentation': {
     'root':'online-experimentation/online-experimentation-tutorial', 'name':'Online Experimentation',
     'summary':'Ship measured changes with stable assignment, faithful exposure telemetry, integrity checks and predeclared release gates.',
     'groups':[('Design and instrument', ['decision-estimand-and-randomization-unit','exposure-and-event-logging','sample-ratio-and-aa-diagnostics']),
               ('Analyze and release', ['metric-denominators-and-guardrails','sequential-reads-and-variance-reduction','ramp-rollback-and-decision-packet'])],
     'project':'lesson-feed-experiment-project',
     'foundation':['applied-statistics/applied-statistics-tutorial','causal-inference/causal-inference-tutorial'],
     'neighbors':['recommendation-systems/recommendation-systems-tutorial','feature-stores/feature-stores-tutorial']},
 'feature-stores': {
     'root':'feature-stores/feature-stores-tutorial', 'name':'Feature Stores',
     'summary':'Build versioned feature definitions, point-in-time historical retrieval and online serving with measurable parity.',
     'groups':[('Define and retrieve', ['entity-feature-and-availability-contract','historical-point-in-time-join','feature-view-version-and-lineage']),
               ('Serve and operate', ['online-materialization-and-staleness','offline-online-parity-and-tests','backfill-delete-and-publication'])],
     'project':'receipt-triage-feature-project',
     'foundation':['data-engineering/data-engineering-tutorial','machine-learning/machine-learning-tutorial'],
     'neighbors':['mlops/mlops-tutorial','online-experimentation/online-experimentation-tutorial']},
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
                + '<h2>Connected foundations</h2><p>Use the earlier measurement and data contracts as prerequisites.</p>'
                + links(config['foundation']) + '<h2>Further paths</h2>' + links(config['neighbors'])
                + '<h2>Practice</h2>' + links([project_hub_path]))
    hub = make_row(root_path, titles[root_path], config['summary'], hub_body,
                   'subject', slug, root_path, root_path, 9800 if slug == 'online-experimentation' else 9900,
                   {'modules':modules, 'resource_tabs':tabs})
    project_body = ('<p>Apply the ' + html.escape(config['name']) + ' curriculum to a checked project.</p>'
                    '<h2>Project brief</h2>' + links([project_path])
                    + '<h2>Required concepts</h2>' + links(all_paths[:-1])
                    + '<h2>Completion standard</h2><p>Submit runnable work, a data manifest, measured results and failure-case evidence.</p>')
    project_hub = make_row(project_hub_path, titles[project_hub_path],
                           'A checked project for the ' + config['name'] + ' curriculum.', project_body,
                           'subject', slug + '-project', project_hub_path, root_path,
                           9801 if slug == 'online-experimentation' else 9901,
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
                       10000 + index,
                       {'kind':'project' if is_project else 'tutorial',
                        'reading_minutes':max(5, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                        'author_path':'authors/aitrove-editorial',
                        'verification_suite':'Editorial and syntax review; project inputs needed for runtime checks',
                        'related':[{'path':path,'title':titles[path]} for path in item['related']]})
    rows.append(article)
    by_path[item['path']] = article

for source, target in [
    ('applied-statistics/randomization-unit-and-experiment-design','online-experimentation/decision-estimand-and-randomization-unit'),
    ('applied-statistics/multiple-comparisons-and-stopping-rule','online-experimentation/sequential-reads-and-variance-reduction'),
    ('causal-inference/assignment-balance-and-noncompliance','online-experimentation/sample-ratio-and-aa-diagnostics'),
    ('recommendation-systems/lesson-feed-project','online-experimentation/lesson-feed-experiment-project'),
    ('data-engineering/warehouse-history-asof-join','feature-stores/historical-point-in-time-join'),
    ('mlops/feature-training-serving-parity','feature-stores/offline-online-parity-and-tests'),
    ('machine-learning/prediction-time-feature-availability','feature-stores/entity-feature-and-availability-contract'),
    ('data-engineering/backfill-publication-boundary','feature-stores/backfill-delete-and-publication'),
]:
    row = by_path[source]
    anchor = '<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in row['body']:
        row['body'] += anchor
        if row['type'] == 'article':
            row['data']['related'].append({'path':target,'title':titles[target]})
        row['updated_at'] = stamp

for source, target in [
    ('applied-statistics/applied-statistics-tutorial','online-experimentation/online-experimentation-tutorial'),
    ('causal-inference/causal-inference-tutorial','online-experimentation/online-experimentation-tutorial'),
    ('data-engineering/data-engineering-tutorial','feature-stores/feature-stores-tutorial'),
    ('mlops/mlops-tutorial','feature-stores/feature-stores-tutorial'),
]:
    row = by_path[source]
    anchor = '<p><strong>Continue into another subject:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in row['body']:
        row['body'] += anchor
        row['updated_at'] = stamp

assert len({row['path'] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_articles':len(lessons), 'new_subject_hubs':4, 'crosslinks_from_existing':12}))
