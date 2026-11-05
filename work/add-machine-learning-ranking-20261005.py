"""Add original query-aware learning-to-rank lessons to the ML curriculum."""
from ml_fixture_writer_20261005 import publish_batch

lessons = []


def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='machine-learning/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))


add('ranking-query-group-and-label-contract',
    'Ranking query groups and relevance labels',
    'A learning-to-rank record represents a candidate within a query group; relevance, eligibility and feature time must be defined at that group’s decision point.', [
    ('Define one decision event', 'For a maintenance manual search, a query group is one technician request at one timestamp with its eligible candidate pages. The same page can appear under many requests, but it is not the evaluation unit. Record the request ID, query text version, candidate-set version, document revision and time each feature was available. A later repair outcome cannot become a feature for an earlier search. [[machine-learning/prediction-time-feature-availability|Prediction-time availability]] applies to ranking too.'),
    ('Separate relevance from exposure', 'A page marked relevant by a reviewer answers the information need under a stated rubric. A clicked page only tells you that a result was displayed and selected under a particular layout. Unshown pages are not negative labels. If reviewers judge only displayed results, the label pool inherits the existing ranker’s blind spots. [[recommendation-systems/implicit-feedback-and-exposure-bias|Exposure bias]] is the adjoining problem.'),
    ('Keep group boundaries intact', 'Training and validation must not put candidates from the same request into different folds. For a future search deployment, split by request time and embargo cases whose judgments mature after the cutoff. If the same incident appears repeatedly, group those requests again by incident when leakage across repeated queries is plausible. [[machine-learning/group-and-time-validation|Group and time validation]] gives the broader split rule.'),
    ('Choose a meaningful label scale', 'A four-level rubric might mean 0 is unsafe or irrelevant, 1 offers background only, 2 identifies the repair step, and 3 gives the approved procedure with the correct equipment. Reviewers need examples of borderline grades and an adjudication path. Do not silently convert a click into grade 3; behavior and editorial relevance answer different questions.'),
    ('Record the candidate denominator', 'A reranker cannot recover a relevant page absent from the retrieved set. Keep candidate recall and ranker quality as separate numbers, along with permission-filter failures and missing document revisions. [[retrieval-ai/retrieval-recall-and-reranking|Retrieval recall and reranking]] describes the upstream boundary; [[machine-learning/ranking-serving-budget-and-candidate-recall|serving review]] measures it.')],
    '''requests = [
    {"request_id": "pump-47", "timestamp": 912, "document_id": "seal-a7", "grade": 3, "feature_ready": 903},
    {"request_id": "pump-47", "timestamp": 912, "document_id": "parts-b4", "grade": 1, "feature_ready": 909},
    {"request_id": "valve-62", "timestamp": 938, "document_id": "isolation-c9", "grade": 2, "feature_ready": 923},
]

def validate_ranking_records(records):
    by_request = {}
    for record in records:
        if record["grade"] not in (0, 1, 2, 3):
            raise ValueError("grade outside approved rubric")
        if record["feature_ready"] > record["timestamp"]:
            raise ValueError("future feature in search request")
        by_request.setdefault(record["request_id"], set())
        if record["document_id"] in by_request[record["request_id"]]:
            raise ValueError("duplicate candidate in request")
        by_request[record["request_id"]].add(record["document_id"])
    return {request_id: len(documents) for request_id, documents in by_request.items()}

assert validate_ranking_records(requests) == {"pump-47": 2, "valve-62": 1}''',
    'Validation takes O(N) expected time and O(N) memory for N candidate records. Stored group IDs, document revisions and feature timestamps add ingestion cost, but they make leakage and denominator audits possible. Full query groups must remain together during training, evaluation and distributed processing.',
    ['Do not split rows at random while keeping candidates from one request on both sides.', 'Do not treat an unshown document as an observed negative.', 'Do not use a feature produced after the request timestamp.'],
    ['machine-learning/pairwise-ranking-loss-and-ties','machine-learning/ndcg-at-k-per-query-evaluation','machine-learning/ranking-click-position-bias-and-support','machine-learning/ranking-serving-budget-and-candidate-recall'])


add('pairwise-ranking-loss-and-ties',
    'Pairwise ranking loss, ties and useful comparisons',
    'Pairwise learning compares differently graded candidates within the same query group; equal-grade pairs and cross-query pairs do not express the desired ordering.', [
    ('Train on within-request preferences', 'When an approved seal-repair page has grade 3 and a parts index has grade 1 for the same request, the ranker should assign the repair page a larger score. Scores need not be calibrated probabilities. The code computes logistic loss on a small, declared set of preferred pairs. It deliberately skips tied grades and never pairs pages from different requests.'),
    ('Know what the objective optimizes', 'A pairwise logistic objective penalizes reversed and uncertain comparisons, but it does not directly optimize the whole displayed list. Its gradient can improve a pair below the fold that no technician sees. A list-aware method may weight swaps near the top more heavily. [[machine-learning/ndcg-at-k-per-query-evaluation|NDCG at a cutoff]] measures the result at the decision surface.'),
    ('Control pair explosion', 'A request with M candidates can yield O(M squared) ordered comparisons. Sample within the query, retain positive and negative grade coverage, and record the sampling rule. Long requests should not dominate training merely because they generate more pairs; normalize or weight at query level. The number of effective pairs matters more than raw row count.'),
    ('Handle ties and contradictory labels', 'Two pages with the same adjudicated grade are not ordered by that rubric. If reviewers disagree, retain the adjudication history or a distribution rather than inventing a preference. Repeated near-identical pages may need deduplication before pair construction, because otherwise a training set can overrepresent one procedure revision.'),
    ('Keep the baseline honest', 'Compare against a stable heuristic such as exact equipment match followed by document freshness. Optimize model settings only on development requests, then evaluate once on untouched later requests. [[machine-learning/hyperparameter-search-and-untouched-test|Untouched testing]] protects the final comparison; [[machine-learning/ranking-release-review-project|the release project]] joins it with serving cost.')],
    '''from math import exp, log1p

search_candidates = [
    {"request": "pump-47", "document": "seal-a7", "grade": 3, "score": 1.9},
    {"request": "pump-47", "document": "parts-b4", "grade": 1, "score": 0.4},
    {"request": "pump-47", "document": "check-c2", "grade": 1, "score": 0.7},
    {"request": "valve-62", "document": "isolation-c9", "grade": 2, "score": 0.3},
]

def preferred_pair_losses(candidates):
    groups = {}
    for candidate in candidates:
        groups.setdefault(candidate["request"], []).append(candidate)
    losses = []
    for group in groups.values():
        for first_index, first in enumerate(group):
            for second in group[first_index + 1:]:
                if first["grade"] == second["grade"]:
                    continue
                better, worse = (first, second) if first["grade"] > second["grade"] else (second, first)
                margin = better["score"] - worse["score"]
                losses.append(log1p(exp(-margin)))
    return losses

losses = preferred_pair_losses(search_candidates)
assert len(losses) == 2
assert all(0 < loss < log1p(1) for loss in losses)''',
    'Grouping takes O(N) expected time and O(N) memory. Enumerating every pair costs O(sum of group-size squared) time and O(P) memory if all P losses are retained; stream or sample pairs for large requests. Training costs depend on the chosen scorer, and pair count does not equal the number of independent search events.',
    ['Do not form a preference from equal grades.', 'Do not compare scores from unrelated query groups as if the labels shared one scale.', 'Do not let a handful of long queries determine the objective by pair count alone.'],
    ['machine-learning/ranking-query-group-and-label-contract','machine-learning/ndcg-at-k-per-query-evaluation','machine-learning/ranking-serving-budget-and-candidate-recall','machine-learning/ranking-release-review-project'])


add('ndcg-at-k-per-query-evaluation',
    'NDCG at K with a declared query denominator',
    'NDCG at K compares discounted gain in the displayed top K against the best ordering available in each judged query group.', [
    ('Define gain and discount first', 'For graded maintenance-page relevance, use gain 2 to the grade minus 1 and divide each position by log base 2 of rank plus one. A grade-3 page at position one contributes more than the same page at position five. This is a business-weighted metric choice, not a universal truth. Declare K, gain mapping and whether unjudged pages are excluded or treated separately before scoring.'),
    ('Normalize within each request', 'Compute the ideal discounted gain from the same judged candidate set, then divide observed gain by that ideal. Requests with no positive grade have zero ideal gain; assign a documented policy, such as excluding them from NDCG and reporting their count separately. Silently assigning zero can turn a change in no-answer traffic into a ranking regression.'),
    ('Aggregate without losing traffic shape', 'A macro mean gives each request equal weight; a traffic-weighted mean gives repeated request types more weight. Both can be useful, but they answer different questions. Show the number of eligible requests and slices for rare equipment, document age and permission groups. [[machine-learning/group-error-gaps-and-policy-audit|Group error audits]] explain why pooled gains can conceal unacceptable gaps.'),
    ('Watch candidate-set changes', 'If one ranker is evaluated over a larger candidate pool, its ideal denominator may differ. Hold candidate retrieval fixed for a pure reranker comparison. When retrieval and ranking both change, show candidate recall and end-to-end metrics together. [[retrieval-ai/retrieval-vs-answer-evaluation|Retrieval versus answer evaluation]] separates related layers.'),
    ('Pair offline quality with an operational outcome', 'A higher NDCG at 5 may still increase time to reach the approved procedure if snippets are poor or the first result is stale. Use a later controlled release to assess task completion, safety and latency. [[online-experimentation/metric-denominators-and-guardrails|Metric denominators and guardrails]] provide the experiment contract.')],
    '''from math import log2

def ndcg_at_k(ordered_grades, cutoff):
    if cutoff < 1 or any(grade < 0 for grade in ordered_grades):
        raise ValueError("valid cutoff and nonnegative grades required")
    def discounted_gain(grades):
        return sum((2 ** grade - 1) / log2(position + 2)
                   for position, grade in enumerate(grades[:cutoff]))
    ideal = discounted_gain(sorted(ordered_grades, reverse=True))
    if ideal == 0:
        return None  # Track no-positive groups outside the mean.
    return discounted_gain(ordered_grades) / ideal

search_grades = {"pump-47": [1, 3, 0, 2], "valve-62": [2, 0, 1]}
scores = [ndcg_at_k(grades, 3) for grades in search_grades.values()]
macro_ndcg = sum(scores) / len(scores)
assert 0 < macro_ndcg < 1
assert ndcg_at_k([0, 0], 3) is None
assert ndcg_at_k([3, 2, 1], 3) == 1.0''',
    'Sorting each group of M candidates for its ideal order takes O(M log M) time; scoring the observed top K takes O(K) time. Across requests, memory can be O(M) per streamed group. Store the group count, empty-ideal count and candidate-pool version with the aggregate so a later comparison is interpretable.',
    ['Do not flatten all candidates into one global ranking before calculating NDCG.', 'Do not hide no-positive requests by silently changing the denominator.', 'Do not compare rerankers on different candidate pools without measuring upstream recall.'],
    ['machine-learning/ranking-query-group-and-label-contract','machine-learning/pairwise-ranking-loss-and-ties','machine-learning/ranking-serving-budget-and-candidate-recall','machine-learning/ranking-release-review-project'])


add('ranking-click-position-bias-and-support',
    'Click position bias and support for ranking evaluation',
    'Search clicks are affected by result position and exposure, so they cannot be treated as direct relevance labels without an observation model and adequate support.', [
    ('Log what could be seen', 'A technician can click only a displayed result, and a result at the top is more likely to be examined. Keep the presented order, candidate IDs, snippet version, device, session and displayed timestamp. A click event without its display context cannot distinguish relevance from visibility. [[online-experimentation/exposure-and-event-logging|Exposure logging]] defines a related product-event contract.'),
    ('Separate the estimands', 'Editorial relevance asks whether a manual page answers a request. Click probability asks whether someone selects it under a particular interface and rank. Successful repair may require a later verified outcome. These signals should be reported separately; otherwise a model can optimize for attention-grabbing snippets while sending technicians to less useful instructions.'),
    ('Randomization needs guardrails', 'Small controlled swaps among safe, eligible candidates can estimate position effects. Do not randomize safety-critical procedures into an unreviewed first position. Log the assignment probability and the exact eligible set for every randomized display. If a target policy chooses a page in contexts never exposed by the logging policy, counterfactual evaluation cannot identify its outcome from those logs. [[machine-learning/contextual-bandit-action-logging-and-support|Bandit support]] spells out the condition.'),
    ('Inspect weights before trusting a correction', 'Inverse-propensity weighting divides an observed outcome by its display probability. Tiny probabilities produce high-variance estimates; clipping changes the estimand and must be disclosed. Report the effective sample size and a sensitivity range, not just a corrected mean. The code audits weights from a made-up randomized logging packet; it does not prove unbiased relevance.'),
    ('Retain a human-judged test set', 'A fixed, independently judged query set can reveal regressions caused by click-derived labels and changing UI placement. Refresh it when the document corpus changes, and keep the old set for a stability trend. [[machine-learning/ndcg-at-k-per-query-evaluation|Per-query NDCG]] and [[machine-learning/ranking-release-review-project|release review]] use that set.')],
    '''display_events = [
    {"request": "pump-47", "rank": 1, "clicked": 1, "display_probability": 0.50},
    {"request": "valve-62", "rank": 2, "clicked": 0, "display_probability": 0.25},
    {"request": "motor-83", "rank": 3, "clicked": 1, "display_probability": 0.20},
]

def weight_diagnostics(events):
    if not events or any(not 0 < event["display_probability"] <= 1 for event in events):
        raise ValueError("positive logged probabilities required")
    weights = [1 / event["display_probability"] for event in events]
    effective_count = sum(weights) ** 2 / sum(weight * weight for weight in weights)
    weighted_click_rate = sum(weight * event["clicked"] for weight, event in zip(weights, events)) / sum(weights)
    return effective_count, weighted_click_rate, max(weights)

effective_count, corrected_rate, largest_weight = weight_diagnostics(display_events)
assert round(effective_count, 3) == 2.689
assert round(corrected_rate, 3) == 0.636
assert largest_weight == 5.0''',
    'The weight audit uses O(N) time and O(N) temporary memory as written; streaming sums reduces memory to O(1). Randomized logging consumes user traffic and operational review capacity. Weighting only addresses the modeled exposure process; unlogged eligibility, snippet changes and missing outcomes can still bias the estimate.',
    ['Do not label every unclicked or unshown page irrelevant.', 'Do not use inverse weights when display probabilities were not logged or are zero.', 'Do not treat a high corrected click rate as proof of safe task completion.'],
    ['machine-learning/ranking-query-group-and-label-contract','machine-learning/ndcg-at-k-per-query-evaluation','machine-learning/ranking-serving-budget-and-candidate-recall','machine-learning/ranking-release-review-project'])


add('ranking-serving-budget-and-candidate-recall',
    'Ranking serving budget and candidate recall',
    'A reranker orders retrieved candidates; its useful ceiling is set by upstream recall, eligibility filters and the latency budget of the entire request.', [
    ('Measure the retrieval ceiling', 'For each independently judged maintenance query, ask whether at least one grade-2-or-better page entered the candidate pool. If no relevant page is present, no downstream ordering model can place one first. Report candidate recall by equipment family, document age and permission class, with the size of each retrieved set. [[retrieval-ai/retrieval-recall-and-reranking|Candidate retrieval]] is a separate system decision.'),
    ('Keep permissions in the path', 'Some documents may be relevant but not allowed for a given crew. Eligibility checks belong before ranking and again at final rendering if permissions can change. A ranker must not learn from fields a viewer cannot access. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Corpus permissions]] describe the lifecycle requirement; a model score never grants access.'),
    ('Budget full-path latency', 'Measure query parsing, candidate retrieval, feature lookup, model scoring, permission recheck and render time on the serving device. A 24-millisecond scorer can still make a 170-millisecond request miss a 150-millisecond target. Record p50, p95, timeout and cold-cache behavior at realistic concurrency. [[machine-learning/model-inference-budget-and-device-profile|Device profiling]] provides the measurement discipline.'),
    ('Bound feature cost', 'Precompute document-only features when their revision changes. Compute query-document interaction features only for the eligible top candidates, and use a declared fallback when a feature service times out. Do not insert a missing value that carries hidden knowledge of label availability. Validate feature freshness and queueing when deciding whether a larger model is worth deploying.'),
    ('Design fallback before rollout', 'If the ranker fails, use a known safe heuristic that still enforces permissions and freshness. Log which path served each request and compare task outcomes separately. The fallback has its own quality and latency profile; it cannot be dismissed because a healthy-model benchmark passes. [[machine-learning/ranking-release-review-project|The project]] makes this a promotion gate.')],
    '''judged_requests = [
    {"request": "pump-47", "eligible_relevant": {"seal-a7"}, "retrieved": ["seal-a7", "parts-b4"]},
    {"request": "valve-62", "eligible_relevant": {"isolation-c9"}, "retrieved": ["parts-b4", "check-c2"]},
    {"request": "motor-83", "eligible_relevant": {"bearing-d5"}, "retrieved": ["bearing-d5", "motor-e2"]},
]

def candidate_recall(requests):
    with_positive = [request for request in requests if request["eligible_relevant"]]
    if not with_positive:
        raise ValueError("no judged positive requests")
    found = sum(bool(request["eligible_relevant"] & set(request["retrieved"]))
                for request in with_positive)
    return found, len(with_positive), found / len(with_positive)

found, eligible, recall = candidate_recall(judged_requests)
assert (found, eligible) == (2, 3)
assert round(recall, 3) == 0.667
stage_latency_ms = {"retrieval": 48, "features": 31, "scoring": 24, "render": 57}
assert sum(stage_latency_ms.values()) == 160  # Above a 150 ms request budget.''',
    'Candidate recall calculation is O(total retrieved IDs) expected time with temporary sets. Scoring cost grows with candidate count and feature work, while end-to-end latency includes retrieval and rendering. A timeout fallback, permission recheck and cold-cache measurement can each add cost absent from a model-only benchmark.',
    ['Do not claim a reranker fixes missing candidates.', 'Do not use model scores to bypass document eligibility or permissions.', 'Do not report scorer latency as if it were the user-visible request latency.'],
    ['machine-learning/ranking-query-group-and-label-contract','machine-learning/ndcg-at-k-per-query-evaluation','machine-learning/ranking-click-position-bias-and-support','machine-learning/ranking-release-review-project'])


add('ranking-release-review-project',
    'Project: release review for maintenance-search ranking',
    'A ranking release decision combines query-level relevance, candidate recall, exposure quality, permission checks and full-path latency under one dated evaluation contract.', [
    ('Freeze the decision packet', 'A municipal maintenance team wants to improve manual search. Record the candidate-index snapshot, query-log period, relevance rubric, adjudication sample, eligible document revisions and request split before tuning. The baseline is the current equipment-match rule. The candidate is a pairwise ranker. Keep the final later-period test unread until model and cutoff selection finish. [[machine-learning/ranking-query-group-and-label-contract|The query contract]] is the input specification.'),
    ('Build a two-layer scorecard', 'First measure whether retrieval brings at least one relevant eligible page into each judged request. Then, on identical candidate sets, compare NDCG at 3 and top-result grade by equipment slice. Report no-positive requests separately. A ranking gain with lower candidate recall is not a clean win. [[machine-learning/ndcg-at-k-per-query-evaluation|NDCG]] and [[machine-learning/ranking-serving-budget-and-candidate-recall|candidate recall]] supply the calculations.'),
    ('Audit the behavioral data', 'If clicks trained the candidate, inspect displayed-position logs, assignment probabilities, effective sample size and the proportion of unexposed documents. A manually judged holdout remains the primary offline relevance check. Do not convert historical clicks into a causal claim. [[machine-learning/ranking-click-position-bias-and-support|The bias audit]] explains the limitation.'),
    ('Test operational failure paths', 'Run permission tests against revoked documents, stale index revisions and a feature-service timeout. Benchmark p95 full-path latency under peak request concurrency, not only scorer time. Exercise the fallback heuristic and log fallback rates. An unsafe result at the top is a release blocker even if aggregate NDCG improves.'),
    ('Make the release decision explicit', 'A shadow period can detect logging and latency faults without changing visible order. If it passes, a small randomized rollout can assess repair completion, time to approved instruction and safety guardrails with a predeclared stop rule. [[online-experimentation/ramp-rollback-and-decision-packet|Rollout governance]] covers that step. The code below is a gate over a sample review packet, not a substitute for human inspection.')],
    '''review = {
    "candidate_recall": 0.91,
    "ndcg_at_3_delta": 0.034,
    "rare_equipment_ndcg_delta": -0.012,
    "p95_full_path_ms": 148,
    "permission_failures": 0,
    "fallback_exercised": True,
    "click_propensity_audited": True,
    "rollback_snapshot_retained": True,
}

def ranking_release_gate(packet):
    blockers = []
    if packet["candidate_recall"] < 0.90:
        blockers.append("candidate recall")
    if packet["ndcg_at_3_delta"] <= 0 or packet["rare_equipment_ndcg_delta"] < 0:
        blockers.append("ranking quality by slice")
    if packet["p95_full_path_ms"] > 150:
        blockers.append("request latency")
    if packet["permission_failures"] or not all(packet[key] for key in (
        "fallback_exercised", "click_propensity_audited", "rollback_snapshot_retained"
    )):
        blockers.append("operational controls")
    return "hold: " + ", ".join(blockers) if blockers else "eligible for controlled rollout"

assert ranking_release_gate(review) == "hold: ranking quality by slice"''',
    'The gate itself is O(1); assembling its inputs requires human relevance judgments, query-level metrics, permission tests, realistic serving benchmarks and controlled traffic. A passing offline gate is permission to consider a measured rollout, not proof of improved field outcomes. Preserve the previous index and ranker artifacts until rollback has been exercised.',
    ['Do not promote on a pooled NDCG gain while rare equipment queries regress.', 'Do not use click-only labels as independent proof of relevance.', 'Do not start a rollout before permission, fallback and rollback paths are tested.'],
    ['machine-learning/ranking-query-group-and-label-contract','machine-learning/pairwise-ranking-loss-and-ties','machine-learning/ndcg-at-k-per-query-evaluation','machine-learning/ranking-click-position-bias-and-support','machine-learning/ranking-serving-budget-and-candidate-recall','retrieval-ai/retrieval-recall-and-reranking'])


publish_batch(
    lessons,
    module_title='Learning to rank and search relevance',
    module_summary='Define query groups and judgments, train useful pairs, measure the top of each list, audit clicks and release within serving limits.',
    project_heading='Maintenance-search ranking release review',
    crosslinks=[
        ('retrieval-ai/retrieval-recall-and-reranking', lessons[0]['path']),
        ('machine-learning/hyperparameter-search-and-untouched-test', lessons[1]['path']),
        ('recommendation-systems/offline-evaluation-and-temporal-split', lessons[2]['path']),
        ('machine-learning/contextual-bandit-action-logging-and-support', lessons[3]['path']),
        ('retrieval-ai/corpus-permissions-and-document-lifecycle', lessons[4]['path']),
        ('online-experimentation/ramp-rollback-and-decision-packet', lessons[5]['path']),
    ],
    sort_start=5800,
)
