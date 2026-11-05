"""Add Graph Machine Learning and Anomaly Detection paths to AI Trove preview."""
import datetime
import html
import json
from pathlib import Path
import re
import uuid

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
rows = [row for row in rows if not row['path'].startswith(('graph-machine-learning/', 'anomaly-detection/'))]
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
lessons = []

def add(path, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path=path, title=title, summary=summary, sections=sections,
                        code=code, cost=cost, mistakes=mistakes, related=related))

add('graph-machine-learning/entity-edge-and-snapshot-contract',
    'Graph learning contract: entities, relations and snapshot time',
    'A graph model learns from entities and relationships whose meaning and availability must be fixed at the prediction point.', [
    ('Name the prediction', 'AI Trove might predict which prerequisite lesson a learner should study next. A node could be a lesson, learner or concept, but mixing those types under one anonymous ID makes edges ambiguous. Define a relation such as lesson-requires-concept separately from learner-completed-lesson. [[recommendation-systems/objective-and-interaction-contract|The recommendation objective]] determines which edge is evidence and which is a target.'),
    ('Assign stable identity', 'Canonical lesson paths can identify lesson nodes while an internal learner key identifies a learner under an approved privacy policy. A title change should not create a new lesson node, and a merged page needs an explicit redirect or retirement event. Treat duplicate edges as updates or repeated observations under a declared rule. Direction matters: requires is not the same as required-by.'),
    ('Freeze the snapshot', 'At a recommendation issued on October 5, only edges and node attributes known by that instant may enter features. A completion recorded afterward is a label or future evidence, not past context. Keep edge event time, ingestion time and graph build version. [[time-series/lag-features-and-future-leakage|Availability rules]] apply even when a graph library hides the joins.'),
    ('Check the input fixture', 'Create lesson A requiring concept C and lesson B teaching C. Add a learner who completed B after a historical prediction time; that completion must disappear from the earlier graph snapshot. Include a renamed lesson path and a duplicate edge. A reviewer should identify exactly which nodes and relations are available for the target decision.')],
    'def available_edges(edge_rows, cutoff):\n    retained = {}\n    for edge in edge_rows:\n        if edge["known_at"] >= cutoff:\n            continue\n        key = (edge["source"], edge["relation"], edge["target"])\n        retained[key] = edge\n    return list(retained.values())',
    'Scanning E edges costs O(E) expected time and O(U) memory for U unique relationships. Versioned snapshots consume storage, but they prevent a high offline score built from future edges from being mistaken for a deployable model.',
    ['Do not merge distinct relation types into an unlabeled edge.', 'Do not use a completion edge that arrived after the prediction cutoff.', 'Do not let a page rename create a false new entity.'],
    ['graph-machine-learning/graph-construction-and-degree-skew','graph-machine-learning/temporal-link-split-and-negatives','recommendation-systems/objective-and-interaction-contract','time-series/lag-features-and-future-leakage'])

add('graph-machine-learning/graph-construction-and-degree-skew',
    'Graph construction: direction, duplicates and high-degree nodes',
    'Graph structure is a modeled data contract; adjacency choices affect both the learned signal and the cost of traversal.', [
    ('Represent relation meaning', 'A prerequisite edge from lesson A to lesson B can mean A must precede B, while a learner-to-lesson completion edge has a different direction and time. Do not symmetrize directed relations merely because a library expects undirected input. If reverse edges are added for message passing, give them a separate relation type so the original meaning stays visible.'),
    ('Remove false multiplicity', 'Repeated page views do not necessarily create new learner-lesson relationships. Decide whether an edge represents existence, count or weighted recency. A graph with duplicate edges can amplify one learner’s activity in aggregation. [[graph-machine-learning/entity-edge-and-snapshot-contract|Snapshot identity]] should make retries and genuine repeated behavior distinguishable.'),
    ('Inspect hubs', 'A popular concept node may connect to thousands of lessons. Naive neighborhood expansion from it can dominate memory and drown out rare prerequisite paths. Report degree distribution and isolate suspicious supernodes such as “all lessons.” Neighbor sampling or relation-specific caps control cost, but they can hide useful low-volume links; evaluate that loss.'),
    ('Test a tiny graph', 'Create three lesson nodes, one concept node and four directed edges. Add a duplicate edge and verify unique degree does not change. Reverse one prerequisite and confirm path traversal changes, while a completion edge remains in its own relation. A graph export should preserve isolated lessons as nodes, even when they have no interactions yet.')],
    'def unique_out_neighbors(edge_rows, source_id, relation):\n    return {edge["target"] for edge in edge_rows\n            if edge["source"] == source_id and edge["relation"] == relation}',
    'A scan of E edges costs O(E) time and O(D) memory for D unique matching neighbors. An adjacency index can make repeated lookups closer to O(D), at the cost of O(E) stored edges and careful update handling.',
    ['Do not reverse a prerequisite relation without labeling the reverse direction.', 'Do not let duplicate events inflate degree or message weight silently.', 'Do not report only average degree when a few hubs dominate work.'],
    ['graph-machine-learning/entity-edge-and-snapshot-contract','graph-machine-learning/neighborhood-features-and-message-passing','graph-machine-learning/graph-serving-and-cold-nodes','recommendation-systems/content-collaborative-and-cold-start'])

add('graph-machine-learning/neighborhood-features-and-message-passing',
    'Neighborhood features: aggregate only the graph that existed at prediction time',
    'Message passing updates a node representation from its neighbors; the neighborhood and attributes must obey the same time boundary as the target.', [
    ('Start with a baseline', 'Before training a graph neural network, count eligible prerequisite neighbors or shared concepts and compare that simple score with a content baseline. A learned message-passing layer combines node features with neighbor information, but a two-hop path can already reveal useful curriculum structure. [[recommendation-systems/content-collaborative-and-cold-start|Content features]] offer a fallback when learner edges are sparse.'),
    ('Control the receptive field', 'One layer sees immediate neighbors, two layers can see neighbors of neighbors. High-degree concept nodes make multi-hop expansion grow rapidly. Choose layer count and sampling fanout by the question, not by an arbitrary large network. Track which relation types carry messages and whether a learner can receive information from a future completion edge.'),
    ('Avoid target leakage', 'For link prediction, remove the target learner-lesson edge from the message-passing graph before scoring that pair. Otherwise the model can observe the answer directly. Temporal splits also require later edges to be absent from earlier graph snapshots. [[graph-machine-learning/temporal-link-split-and-negatives|Link evaluation]] must freeze both graph structure and candidate catalog.'),
    ('Test propagation', 'Use a lesson connected to two concept nodes with numeric importance values 2 and 6. Its mean neighbor value is 4. Add a duplicate of the value-6 edge and verify that unique-neighbor aggregation still returns 4. Then move one edge after the prediction time and check the earlier feature changes under the snapshot rule.')],
    'def mean_neighbor_feature(neighbor_ids, feature_by_node):\n    unique_ids = set(neighbor_ids)\n    values = [feature_by_node[node_id] for node_id in unique_ids if node_id in feature_by_node]\n    return None if not values else sum(values) / len(values)',
    'A one-hop aggregation is O(D) for D neighbors; L layers with fanout F can visit up to O(F to the power L) sampled positions per seed before deduplication. Measure actual sampled nodes and memory rather than assuming a deeper network is free.',
    ['Do not leave a target edge in the graph used to predict that edge.', 'Do not count duplicated neighbor IDs as independent evidence.', 'Do not sample more hops than the model can use.'],
    ['graph-machine-learning/graph-construction-and-degree-skew','graph-machine-learning/temporal-link-split-and-negatives','deep-learning/deep-learning-tutorial','recommendation-systems/content-collaborative-and-cold-start'])

add('graph-machine-learning/temporal-link-split-and-negatives',
    'Link prediction evaluation: time splits and honest negative candidates',
    'A link-prediction test ranks future valid relationships against eligible alternatives under a past graph snapshot.', [
    ('Define the target edge', 'Predicting a learner’s next completed lesson differs from predicting any future click or a missing prerequisite in the catalog. Fix the edge type, horizon and eligible candidate set. A learner cannot complete an unpublished lesson, so that path should not enter the negative pool. [[recommendation-systems/offline-evaluation-and-temporal-split|Temporal recommendation evaluation]] has the same catalog-state constraint.'),
    ('Split by time', 'Build training graph edges before a cutoff and reserve later edges as outcomes. For every historical decision, reconstruct node features and neighbors known then. Randomly moving existing edges into a test set can leave later edges in the training graph and turn a future-only relationship into a feature. Keep one final period untouched during model selection.'),
    ('Treat unknown carefully', 'An unobserved learner-lesson pair is not always a true negative; the learner may never have seen the lesson. Negative sampling defines an evaluation comparison, not ground truth for every absent edge. Record sampling method and exposure eligibility. A model can win against easy random negatives yet fail to rank among realistic competing lessons.'),
    ('Exercise candidates', 'At a historical cutoff, create one future positive lesson, one eligible but unchosen lesson and one unpublished lesson. Only the first two can enter the candidate comparison. Verify that the positive edge is absent from the input graph and that a later completion by another learner does not leak into earlier node features.')],
    'def eligible_link_candidates(candidate_paths, published_at_cutoff, completed_paths):\n    return [path for path in candidate_paths\n            if path in published_at_cutoff and path not in completed_paths]',
    'Filtering C candidates costs O(C) expected time with set membership. Reconstructing graph snapshots and scoring K candidates can dominate; cache immutable snapshot IDs but include publication and exposure policy in the cache key.',
    ['Do not treat every absent edge as a confirmed negative preference.', 'Do not leave the target edge in the feature graph.', 'Do not evaluate against items unavailable at the decision time.'],
    ['graph-machine-learning/entity-edge-and-snapshot-contract','graph-machine-learning/neighborhood-features-and-message-passing','graph-machine-learning/graph-metrics-and-subgroup-coverage','recommendation-systems/offline-evaluation-and-temporal-split'])

add('graph-machine-learning/graph-metrics-and-subgroup-coverage',
    'Graph model evaluation: report sparse-node and relation-specific failures',
    'A pooled graph score can hide failures on new nodes, rare relations and small connected components.', [
    ('Separate task metrics', 'Node classification needs class-specific precision and recall, while link prediction needs a ranking metric over a declared candidate set. An accuracy figure for one task cannot stand in for the other. Report candidate construction and horizon beside every link metric. [[graph-machine-learning/temporal-link-split-and-negatives|Negative sampling]] changes the difficulty of the ranking problem.'),
    ('Slice by graph position', 'A high-degree lesson with many interactions may be easy to score, while a newly published lesson with no edges needs a content fallback. Break results out by node degree, age, relation type and connected component size. A single average dominated by popular nodes can justify a release that harms the exact cold-start case the feature was meant to solve.'),
    ('Check retrieval before ranking', 'If candidate generation omits a future-positive lesson, a graph ranker never sees it. Measure candidate recall separately from ordering quality. Also measure catalog coverage and the proportion of recommendations coming from isolated or low-degree nodes. [[recommendation-systems/candidate-retrieval-and-eligibility|Candidate supply]] and graph scoring are separate stages.'),
    ('Test a small slate', 'For a learner with two known relevant eligible lessons, a five-item list containing one gives recall at five of one half. Report the judged-set limitation and the rank of the found item. Repeat for a cold-start learner; if no relevant edge was observed, mark the metric undefined rather than inventing zero relevance.')],
    'def judged_recall_at_k(ranked_paths, relevant_paths, limit):\n    if limit < 1:\n        raise ValueError("limit must be positive")\n    relevant = set(relevant_paths)\n    if not relevant:\n        return None\n    return len(set(ranked_paths[:limit]) & relevant) / len(relevant)',
    'A top-K calculation costs O(K + R) time and space for R judged positives. Computing degree-sliced reports requires O(E) graph aggregation plus scored decisions; record subgroup counts and uncertainty so small slices are not overread.',
    ['Do not mix node-classification accuracy with link-ranking quality.', 'Do not report only high-degree nodes in a graph release review.', 'Do not interpret an undefined no-positive recall as zero.'],
    ['graph-machine-learning/temporal-link-split-and-negatives','graph-machine-learning/graph-serving-and-cold-nodes','recommendation-systems/candidate-retrieval-and-eligibility','data-visualization/uncertainty-and-small-sample-display'])

add('graph-machine-learning/graph-serving-and-cold-nodes',
    'Graph serving: handle new nodes, edge deletion and snapshot swaps',
    'A graph model in production needs a stable snapshot, an eligibility gate and a useful route for entities absent from its embeddings.', [
    ('Version the graph', 'Store graph build ID, node-feature version, edge cutoff, model version and catalog snapshot with each recommendation. A new completion event should not partly update an embedding cache while the graph index remains old. Build and validate a new snapshot, then switch serving atomically. [[data-engineering/backfill-publication-boundary|Publication boundaries]] are as important here as in warehouse backfills.'),
    ('Cover cold nodes', 'A new lesson may have no collaborative edges. Use reviewed subject and prerequisite metadata or an editorial fallback instead of returning no result or a random embedding. Record fallback rate and its outcomes. [[graph-machine-learning/graph-metrics-and-subgroup-coverage|Sparse-node slices]] reveal whether the fallback is actually helping.'),
    ('Honor deletion', 'A withdrawn lesson must disappear from recommendations immediately even if it remains in a model artifact for reproducibility. Apply a serving-time eligibility gate, and schedule rebuild or deletion under the retention policy. Removing a learner’s history may require invalidating graph features and cached neighborhoods; do not treat a deleted edge as an ordinary negative preference.'),
    ('Rehearse a swap', 'Serve graph version 47 while building version 48. Include a newly published lesson, a withdrawn lesson and one deleted learner edge. Verify every response logs one coherent version and never returns the withdrawn lesson. If the new index fails health checks, restore version 47 while preserving the withdrawal gate.')],
    'def serve_graph_candidates(paths, published_paths, completed_paths):\n    return [path for path in paths\n            if path in published_paths and path not in completed_paths]',
    'Filtering C candidates is O(C) expected time. Graph rebuild and embedding generation may be expensive; a versioned swap controls consistency, while the serving-time gate limits stale-index exposure at modest per-request cost.',
    ['Do not serve a withdrawn node because it remains in a model artifact.', 'Do not combine embeddings and graph edges from incompatible snapshots.', 'Do not return an empty feed for every cold-start node.'],
    ['graph-machine-learning/graph-metrics-and-subgroup-coverage','graph-machine-learning/lesson-prerequisite-graph-project','recommendation-systems/content-collaborative-and-cold-start','data-engineering/backfill-publication-boundary'])

add('graph-machine-learning/lesson-prerequisite-graph-project',
    'Project: evaluate a lesson-prerequisite graph recommender',
    'Build a small versioned lesson graph and test whether it improves a next-lesson decision without leaking future edges.', [
    ('Create the graph packet', 'Define lesson, concept and learner nodes with typed directed edges for teaches, requires and completed. Give every edge known-at time and event identity. Include one duplicate, one newly published lesson, one withdrawn lesson and a learner completion after the historical decision cutoff. [[graph-machine-learning/entity-edge-and-snapshot-contract|The snapshot contract]] decides what a model can observe.'),
    ('Establish baselines', 'First rank eligible lessons by shared prerequisite concepts and a simple editorial route. Then implement a one-hop or two-hop neighborhood feature; a graph neural network is optional only if the simpler baseline leaves a measured gap. Deduplicate neighbors and cap high-degree expansion. [[graph-machine-learning/neighborhood-features-and-message-passing|Message passing]] must not include the target completion edge.'),
    ('Evaluate honestly', 'Use later completion edges as positives and build eligible negative candidates under the past catalog snapshot. Report candidate recall, ranking recall at five and coverage by new versus established lessons. Do not call every unexposed pair a negative. Keep the newest period untouched while choosing graph features or fanout.'),
    ('Submit release evidence', 'Deliver schema, graph versions, split IDs, code, model or rule manifest, subgroup scores and a serving trace. Assert that the withdrawn lesson is gated out, the new lesson has a fallback, and version swap or rollback preserves coherent responses. A reviewer should reconstruct one recommendation from the logged graph and candidate IDs.')],
    'def prerequisite_overlap(required_concepts, learned_concepts):\n    required = set(required_concepts)\n    learned = set(learned_concepts)\n    if not required:\n        return 1.0\n    return len(required & learned) / len(required)\n\nassert prerequisite_overlap({"data-grain", "time-split"}, {"data-grain"}) == 0.5',
    'Set overlap costs O(R + L) time and space for R required and L learned concepts. Full graph serving adds neighborhood and ranking cost; measure its gain over this baseline before accepting a larger graph index and retraining process.',
    ['Do not let a future completion enter a past graph snapshot.', 'Do not treat an unpublished lesson as a negative candidate.', 'Do not deploy without a withdrawal gate and cold-node fallback.'],
    ['graph-machine-learning/temporal-link-split-and-negatives','graph-machine-learning/graph-serving-and-cold-nodes','recommendation-systems/lesson-feed-project','data-engineering/backfill-publication-boundary'])

add('anomaly-detection/incident-unit-and-label-contract',
    'Anomaly detection contract: incidents, observations and delayed labels',
    'An unusual measurement is a candidate for investigation; an incident requires a separate operational definition and evidence.', [
    ('Choose the decision unit', 'AI Trove might watch submitted receipts by tenant and hour. One low hourly count is an observation, while an incident may span several hours and related tenants. State whether the system ranks observations, opens tickets or identifies incident episodes. If retries duplicate receipts, counting them as fresh submissions creates a false baseline. [[streaming-analytics/event-contract-and-partition-key|The event contract]] fixes identity and partition before scoring.'),
    ('Define exposure and context', 'A tenant with scheduled maintenance, a holiday closure or a new launch has a different expected volume from a mature tenant on an ordinary weekday. Preserve the calendar, active-tenant status and source health as context available when the alert fires. A missing feed cannot be interpreted as zero receipts until a separate ingestion check confirms that the source was live.'),
    ('Keep labels separate', 'An analyst may confirm an incident days after the first alert. Store observed time, alert time, investigation time, label time and incident ID. A rejected alert is not automatically a normal observation if investigation never occurred. [[mlops/drift-delayed-label-monitoring|Delayed outcome monitoring]] should report the still-unreviewed population rather than quietly excluding it.'),
    ('Test the record', 'Construct a 47-receipt hour, an unexpected 4-receipt hour, and a missing hour from a stalled feed. Only the second can be called a low-volume candidate without more evidence. Link two consecutive candidates to one incident ID and verify that episode-level metrics count one incident, not two independent true positives.')],
    'def incident_candidates(hour_rows, expected_floor):\n    return [row for row in hour_rows\n            if row["source_healthy"] and row["count"] is not None\n            and row["count"] < expected_floor[row["tenant_id"]]]',
    'Scanning N hourly records costs O(N) expected time with indexed tenant thresholds and O(A) output memory for A candidates. Episode grouping adds state by tenant and alert window; measure both point alerts and distinct investigations.',
    ['Do not label a missing feed as a measured zero.', 'Do not count several alerts from one incident as separate successful detections.', 'Do not treat an unreviewed alert as a confirmed false positive.'],
    ['anomaly-detection/contextual-seasonal-baseline','anomaly-detection/rare-event-backtest-and-delayed-labels','streaming-analytics/event-contract-and-partition-key','mlops/drift-delayed-label-monitoring'])

add('anomaly-detection/contextual-seasonal-baseline',
    'Contextual anomaly baselines: seasonality, exposure and missing periods',
    'A useful anomaly score compares an observation with the expectation for its own context, not with one global average.', [
    ('Segment the calendar', 'Compare Monday morning with comparable Monday mornings before comparing it with Saturday night. Include a known release or holiday marker only when that marker was available at the decision point. Thin segments need a broader fallback and an uncertainty range; a perfectly fitted mean from two prior hours creates noisy alerts. [[time-series/observation-calendar-and-missing-periods|The observation calendar]] determines which periods genuinely existed.'),
    ('Separate count from opportunity', 'Thirty receipts may be normal for a tenant with 40 active users and alarming for one with 4,000. Use an exposure measure such as active sessions or eligible orders when it is reliable and timely. If exposure is missing or late, report that condition explicitly. A ratio with a near-zero denominator can explode even when the numerator is ordinary.'),
    ('Score residuals', 'A residual is observed volume minus expected volume. A scale-adjusted residual can compare tenants of different sizes, but the scale must be estimated from past comparable periods and bounded away from zero. Keep the raw count and expected count alongside the score so an investigator can explain the alert without decoding a model embedding.'),
    ('Run a fixture', 'Use prior comparable counts of 43, 47, 45 and 49; their median is 46. A new count of 5 has residual minus 41. A missing observation has no residual. Add a holiday marker with a separate history of 6 and 8, and check that a new count of 5 is much less surprising in that context.')],
    'from statistics import median\n\ndef contextual_residual(observed_count, comparable_counts):\n    if observed_count is None or not comparable_counts:\n        return None\n    expected_count = median(comparable_counts)\n    return observed_count - expected_count',
    'Finding the median of H comparable observations is O(H log H) time with a sort-based implementation and O(H) memory. Precomputed seasonal summaries reduce request cost, but their version and cutoff must be recorded with each alert.',
    ['Do not turn a missing period into an observed zero.', 'Do not compare dissimilar calendar periods through one global threshold.', 'Do not divide by an exposure measure that is late, zero or untrusted.'],
    ['anomaly-detection/incident-unit-and-label-contract','anomaly-detection/score-threshold-and-alert-budget','time-series/observation-calendar-and-missing-periods','data-visualization/distribution-and-outlier-displays'])

add('anomaly-detection/score-threshold-and-alert-budget',
    'Anomaly thresholds: rank evidence within an alert budget',
    'The threshold is an operating decision: it trades missed incidents against investigation load and repeated pages.', [
    ('Set a capacity constraint', 'If a team can investigate 12 new tenant incidents a day, an alert rule producing 90 tickets is unusable even if its point-level recall looks high. Define the daily budget, response hours and severity tiers before choosing a percentile. A critical source outage can bypass the ordinary queue, but that exception needs a separate rule and owner.'),
    ('Rank with interpretable evidence', 'Combine contextual residual, source health, duration and affected tenant count in a score whose components can be inspected. A lower count is not always worse: five receipts against an expectation of eight differs from five against 460. [[anomaly-detection/contextual-seasonal-baseline|The contextual baseline]] gives the score its meaning. Calibrate the threshold on a historical period that predates the held-out test.'),
    ('Measure the whole queue', 'Report alert volume, unique incident count, confirmation fraction, time to first alert and missed confirmed incidents. Show the distribution by tenant size and region so a single noisy group does not consume the queue. The threshold should be reviewed when workload changes, but do not retune it against the final test period after seeing the outcome.'),
    ('Exercise a fixed budget', 'Given candidate severities 0.94, 0.72, 0.66 and 0.31 with capacity two, the selected alerts are the first two after applying eligibility and deduplication. If both top scores belong to the same ongoing incident, the second investigation slot should remain available to the next distinct incident.')],
    'def select_alerts(candidates, capacity):\n    if capacity < 0:\n        raise ValueError("capacity cannot be negative")\n    if capacity == 0:\n        return []\n    ranked = sorted(candidates, key=lambda item: item["severity"], reverse=True)\n    selected = []\n    seen_incidents = set()\n    for candidate in ranked:\n        incident_key = candidate["incident_key"]\n        if incident_key not in seen_incidents:\n            seen_incidents.add(incident_key)\n            selected.append(candidate)\n        if len(selected) == capacity:\n            break\n    return selected',
    'Sorting N candidates costs O(N log N) time and O(N) memory. Streaming top-K selection can reduce retained candidates to O(K), but deduplication and severity updates still need an incident-state policy.',
    ['Do not choose a threshold using the final held-out period.', 'Do not confuse point-level precision with distinct-ticket workload.', 'Do not page repeatedly for one unresolved incident.'],
    ['anomaly-detection/contextual-seasonal-baseline','anomaly-detection/triage-feedback-and-deduplication','anomaly-detection/rare-event-backtest-and-delayed-labels','data-visualization/uncertainty-and-small-sample-display'])

add('anomaly-detection/rare-event-backtest-and-delayed-labels',
    'Rare-event backtests: delayed labels, windows and incident recall',
    'A backtest must replay what the detector knew at each decision and distinguish unreviewed alerts from confirmed non-incidents.', [
    ('Replay by decision time', 'For each hour, rebuild the baseline from earlier complete periods only, apply source-health state known then, and use the threshold selected on an older development window. A random split of hourly rows lets later seasonal behavior and corrected labels leak backward. [[time-series/rolling-origin-backtest-and-gap|Rolling-origin evaluation]] gives a more honest sequence of decisions.'),
    ('Judge incidents as episodes', 'Match alerts to confirmed incident windows under a written tolerance, such as first detection within 47 minutes of onset. Count each incident once even when it generates many low-count hours. Report lead time, missed incidents, duplicate pages and investigation volume; pointwise accuracy is dominated by the many normal hours and tells little about response value.'),
    ('Handle incomplete labels', 'A recently fired alert may still be under review. Mark it pending and exclude it from a confirmed precision denominator while still showing its count. Mature only those decisions whose label-delay window has elapsed. [[anomaly-detection/incident-unit-and-label-contract|The label contract]] keeps outcome date separate from event date, preventing silent survivorship bias.'),
    ('Test late confirmation', 'Create an alert on day 6 and a confirmed incident label on day 9. A report run on day 7 should show the alert pending; a report run on day 10 can credit the detection. Add an uninvestigated alert from day 6 and ensure it does not become a false positive merely because no label arrived.')],
    'def mature_alert_labels(alert_rows, report_day, review_delay_days):\n    mature = []\n    pending = []\n    for alert in alert_rows:\n        if alert["day"] + review_delay_days <= report_day and alert["reviewed"]:\n            mature.append(alert)\n        else:\n            pending.append(alert)\n    return mature, pending',
    'A pass over A alerts costs O(A) time and O(A) output space. Episode matching can cost more when windows overlap; index incidents by tenant and time, and preserve the matching rule with every reported metric.',
    ['Do not calculate accuracy over overwhelmingly normal hours as the sole result.', 'Do not call pending or uninvestigated alerts false positives.', 'Do not use a threshold or baseline fitted on the held-out incident window.'],
    ['anomaly-detection/incident-unit-and-label-contract','anomaly-detection/score-threshold-and-alert-budget','time-series/rolling-origin-backtest-and-gap','mlops/drift-delayed-label-monitoring'])

add('anomaly-detection/drift-vs-incident-and-source-health',
    'Anomaly operations: distinguish drift, incidents and broken inputs',
    'A detector should report when its input contract fails before interpreting that failure as a change in real-world behavior.', [
    ('Check source health first', 'Watch event ingestion lag, missing partitions, deduplication rate and schema errors alongside the business metric. A quiet receipt stream caused by a failed collector needs an ingestion alert, not a claim that customers stopped buying. [[streaming-analytics/monitoring-lag-and-batch-parity|Stream parity checks]] can identify when the online count diverges from a corrected batch view.'),
    ('Separate time scales', 'An incident may be a sudden local departure; drift is a sustained change in the baseline or population. A planned rollout can move volume without being either a failure or a healthy permanent shift. Maintain an event log of releases and calendar changes, and require a deliberate baseline update after investigation instead of allowing every new value to teach the detector immediately.'),
    ('Track detector health', 'Plot scores, alert rate, pending-label fraction and baseline age by tenant. If one segment stops producing alerts while its source becomes stale, that is not improved accuracy. Monitor fallbacks for newly active tenants and changes in exposure quality. [[mlops/drift-delayed-label-monitoring|Model monitoring]] should join outcome data only when it matures.'),
    ('Rehearse three scenarios', 'Simulate a genuine 80 percent receipt drop with healthy ingestion, an ingestion halt with unknown business volume, and a gradual planned expansion. The first should enter incident triage, the second source-health triage, and the third a baseline-review workflow. Record which evidence made each route possible at decision time.')],
    'def classify_volume_signal(source_healthy, observed, baseline, planned_change):\n    if not source_healthy or observed is None:\n        return "source-health"\n    if planned_change:\n        return "baseline-review"\n    if observed < baseline * 0.2:\n        return "incident-candidate"\n    return "ordinary"',
    'Each classification is O(1) time and space after baseline lookup. Health metrics need their own timely collection path; a detector cannot reliably diagnose a broken source using only the source it is watching.',
    ['Do not translate a stale source into a business anomaly.', 'Do not absorb an active incident into the baseline automatically.', 'Do not assume a falling alert rate proves performance improved.'],
    ['anomaly-detection/contextual-seasonal-baseline','anomaly-detection/triage-feedback-and-deduplication','streaming-analytics/monitoring-lag-and-batch-parity','mlops/drift-delayed-label-monitoring'])

add('anomaly-detection/triage-feedback-and-deduplication',
    'Anomaly triage: deduplicate, explain and close the feedback loop',
    'The useful output is an investigation packet with enough context to act, a stable incident key and a recorded disposition.', [
    ('Group related alerts', 'Group by tenant, metric and overlapping time window before paging. Keep the strongest score and the first-seen time; attach later observations to the same open incident. A grouping key that is too broad can hide separate outages, while one that includes every hour creates a new ticket each time. [[anomaly-detection/score-threshold-and-alert-budget|Alert capacity]] should be measured after this grouping.'),
    ('Show the evidence', 'Include observed count, baseline, comparable periods, source-health status, exposure and relevant release marker. Explain what the score measured, not just that a model emitted 0.93. The packet should reveal whether a tenant has only a few historical comparison periods and whether a missing upstream partition changes the interpretation.'),
    ('Record disposition', 'Let an investigator mark confirmed incident, expected behavior, source failure or unresolved, with event IDs and a review timestamp. Retain reason and label delay. Feed reviewed outcomes into the next threshold review only after a frozen evaluation run; immediately training on operator feedback can bias the detector toward cases that happened to be investigated.'),
    ('Test replay and reopening', 'Send three consecutive hourly alerts with the same incident key, then replay the middle event. The ticket count should remain one. Resolve it, then send a new candidate after the configured quiet interval and check that a new incident opens with a distinct ID. A source-failure disposition should reach source owners without altering a business baseline.')],
    'def new_incident_alerts(alert_rows):\n    earliest_by_key = {}\n    for alert in alert_rows:\n        key = alert["incident_key"]\n        if key not in earliest_by_key or alert["observed_at"] < earliest_by_key[key]["observed_at"]:\n            earliest_by_key[key] = alert\n    return list(earliest_by_key.values())',
    'Deduplicating A alerts is O(A) expected time and O(I) memory for I incident keys. A production key needs a time-bounded state store and a reopen policy; indefinitely retaining every key would grow without limit.',
    ['Do not page on each observation in one continuing incident.', 'Do not train immediately on selectively reviewed tickets.', 'Do not hide the raw observation and source status behind a score.'],
    ['anomaly-detection/score-threshold-and-alert-budget','anomaly-detection/drift-vs-incident-and-source-health','anomaly-detection/rare-event-backtest-and-delayed-labels','data-visualization/distribution-and-outlier-displays'])

add('anomaly-detection/receipt-volume-alert-project',
    'Project: build and audit a receipt-volume anomaly queue',
    'Build a replayable hourly detector that distinguishes low volume, missing input and one incident that triggers repeated observations.', [
    ('Prepare the fixture', 'Create two tenants with different ordinary hourly volume, weekday patterns and active-session exposure. Add a real low-volume episode, one planned closure, a duplicate receipt event, a missing partition and a collector outage. Give each event an ID, event time and ingestion time. [[anomaly-detection/incident-unit-and-label-contract|The decision contract]] determines which records are observations and which can become incident labels.'),
    ('Build two baselines', 'Start with a comparable-weekday median and then test an exposure-adjusted rate with a documented denominator floor. Preserve source health and baseline version for each decision. Do not convert missing hours to zero. Report the raw count, expected count, residual and score so a reviewer can replay one alert without relying on an opaque dashboard.'),
    ('Replay and score', 'Choose the alert threshold on an earlier period under a fixed daily investigation budget; reserve a later period for the final backtest. Group repeated low hours into one incident ticket. Report incident recall, detection delay, confirmed precision on matured labels, pending labels and daily ticket count. Slice by tenant size and record the result for the planned closure separately.'),
    ('Hand off a working queue', 'Provide event fixture, calendar, baseline code, replay command, alert packet, triage dispositions and a source-health dashboard. Assert that the duplicate event does not raise the count, the collector outage routes to source health, and a replay does not open a second ticket. Document one threshold change with its expected queue impact.')],
    'def distinct_receipts(event_rows):\n    receipt_ids = set()\n    for event in event_rows:\n        if event["type"] == "submitted":\n            receipt_ids.add(event["receipt_id"])\n    return len(receipt_ids)\n\nassert distinct_receipts([{"type": "submitted", "receipt_id": "r-47"},\n                          {"type": "submitted", "receipt_id": "r-47"}]) == 1',
    'A pass over N events costs O(N) expected time and O(U) memory for U distinct receipt IDs. Durable replay safety requires a bounded or persistent dedup ledger; the in-memory set is only the project oracle for a fixed fixture.',
    ['Do not count a retried receipt twice.', 'Do not score an absent partition as a confirmed zero.', 'Do not tune the alert rule on the final backtest period.'],
    ['anomaly-detection/contextual-seasonal-baseline','anomaly-detection/rare-event-backtest-and-delayed-labels','anomaly-detection/drift-vs-incident-and-source-health','streaming-analytics/receipt-event-pipeline-project'])

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
 'graph-machine-learning': {
     'root':'graph-machine-learning/graph-machine-learning-tutorial', 'name':'Graph Machine Learning',
     'summary':'Model typed relationships with historical graph snapshots, honest link tests, sparse-node evaluation and consistent serving.',
     'groups':[('Graph data contracts', ['entity-edge-and-snapshot-contract','graph-construction-and-degree-skew','neighborhood-features-and-message-passing']),
               ('Evaluate and serve', ['temporal-link-split-and-negatives','graph-metrics-and-subgroup-coverage','graph-serving-and-cold-nodes'])],
     'project':'lesson-prerequisite-graph-project',
     'foundation':['machine-learning/machine-learning-tutorial','recommendation-systems/recommendation-systems-tutorial'],
     'neighbors':['anomaly-detection/anomaly-detection-tutorial','mlops/mlops-tutorial']},
 'anomaly-detection': {
     'root':'anomaly-detection/anomaly-detection-tutorial', 'name':'Anomaly Detection',
     'summary':'Build contextual detectors with incident labels, alert budgets, delayed-outcome backtests and an explainable triage queue.',
     'groups':[('Define and score', ['incident-unit-and-label-contract','contextual-seasonal-baseline','score-threshold-and-alert-budget']),
               ('Evaluate and operate', ['rare-event-backtest-and-delayed-labels','drift-vs-incident-and-source-health','triage-feedback-and-deduplication'])],
     'project':'receipt-volume-alert-project',
     'foundation':['time-series/time-series-tutorial','streaming-analytics/streaming-analytics-tutorial'],
     'neighbors':['graph-machine-learning/graph-machine-learning-tutorial','data-visualization/data-visualization-tutorial']},
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
                + '<h2>Connected foundations</h2><p>Use prior data and model contracts as prerequisites.</p>'
                + links(config['foundation']) + '<h2>Further paths</h2>' + links(config['neighbors'])
                + '<h2>Practice</h2>' + links([project_hub_path]))
    hub = make_row(root_path, titles[root_path], config['summary'], hub_body,
                   'subject', slug, root_path, root_path, 9500 if slug == 'graph-machine-learning' else 9600,
                   {'modules':modules, 'resource_tabs':tabs})
    project_body = ('<p>Apply the ' + html.escape(config['name']) + ' curriculum to a checked project.</p>'
                    '<h2>Project brief</h2>' + links([project_path])
                    + '<h2>Required concepts</h2>' + links(all_paths[:-1])
                    + '<h2>Completion standard</h2><p>Submit runnable work, a data manifest, measured results and failure-case evidence.</p>')
    project_hub = make_row(project_hub_path, titles[project_hub_path],
                           'A checked project for the ' + config['name'] + ' curriculum.', project_body,
                           'subject', slug + '-project', project_hub_path, root_path,
                           9501 if slug == 'graph-machine-learning' else 9601,
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
                       9700 + index,
                       {'kind':'project' if is_project else 'tutorial',
                        'reading_minutes':max(5, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                        'author_path':'authors/aitrove-editorial',
                        'verification_suite':'Editorial and syntax review; project inputs needed for runtime checks',
                        'related':[{'path':path,'title':titles[path]} for path in item['related']]})
    rows.append(article)
    by_path[item['path']] = article

for source, target in [
    ('recommendation-systems/candidate-retrieval-and-eligibility','graph-machine-learning/graph-metrics-and-subgroup-coverage'),
    ('recommendation-systems/content-collaborative-and-cold-start','graph-machine-learning/graph-serving-and-cold-nodes'),
    ('time-series/forecast-monitoring-and-retraining','anomaly-detection/drift-vs-incident-and-source-health'),
    ('streaming-analytics/monitoring-lag-and-batch-parity','anomaly-detection/drift-vs-incident-and-source-health'),
    ('data-visualization/distribution-and-outlier-displays','anomaly-detection/contextual-seasonal-baseline'),
    ('mlops/drift-delayed-label-monitoring','anomaly-detection/rare-event-backtest-and-delayed-labels'),
]:
    row = by_path[source]
    anchor = '<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in row['body']:
        row['body'] += anchor
        if row['type'] == 'article':
            row['data']['related'].append({'path':target,'title':titles[target]})
        row['updated_at'] = stamp

for source, target in [
    ('recommendation-systems/recommendation-systems-tutorial','graph-machine-learning/graph-machine-learning-tutorial'),
    ('machine-learning/machine-learning-tutorial','graph-machine-learning/graph-machine-learning-tutorial'),
    ('time-series/time-series-tutorial','anomaly-detection/anomaly-detection-tutorial'),
    ('streaming-analytics/streaming-analytics-tutorial','anomaly-detection/anomaly-detection-tutorial'),
]:
    row = by_path[source]
    anchor = '<p><strong>Continue into another subject:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in row['body']:
        row['body'] += anchor
        row['updated_at'] = stamp

assert len({row['path'] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_articles':len(lessons), 'new_subject_hubs':4, 'crosslinks_from_existing':10}))
