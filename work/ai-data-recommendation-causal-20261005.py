"""Add recommendation and causal-inference curricula to the local AI Trove preview."""
import datetime
import html
import json
from pathlib import Path
import re
import uuid

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
rows = [row for row in rows if not row['path'].startswith(('recommendation-systems/', 'causal-inference/'))]
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
lessons = []

def add(path, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path=path, title=title, summary=summary, sections=sections,
                        code=code, cost=cost, mistakes=mistakes, related=related))

add('recommendation-systems/objective-and-interaction-contract',
    'Recommendation objective and interaction log: define what success means',
    'A recommender orders eligible items for a user or context according to a declared outcome and observation process.', [
    ('Choose the outcome', 'AI Trove might recommend the next lesson after a reader finishes one. A click is easy to record but can reward misleading titles; a completed lesson or later quiz attempt may be more useful. State the decision point, eligible population, prediction window and primary outcome before selecting an algorithm. [[data-science/metric-denominator-and-cohort|Metric denominators]] must count actual opportunities to see a recommendation.'),
    ('Log the opportunity', 'An interaction record needs an anonymous or authorized learner key, item key, timestamp, placement, rank, policy version and whether the item was displayed. A missing click after an impression differs from an item that was never shown. Record the recommendation slate and eligibility snapshot so evaluation can reconstruct what the policy could have chosen. [[recommendation-systems/implicit-feedback-and-exposure-bias|Exposure bias]] begins at this boundary.'),
    ('Respect lifecycle rules', 'A completed lesson, unpublished draft or age-inappropriate resource should not be recommended merely because it has a high model score. Keep publication and progress state outside the training label. Define deletion and consent behavior for the interaction log, especially when a learner removes history. Aggregate reporting can use less identity detail than per-user serving.'),
    ('Test a fixture', 'Give one learner two displayed lessons, one click and one completion. The click-through rate is one of two impressions; completion is one of two impressions or one of one clicks, depending on the predeclared metric. Neither denominator is interchangeable. Add an undelivered candidate and verify it does not become a negative example.')],
    'def impression_metrics(records):\n    shown = [record for record in records if record["displayed"]]\n    if not shown:\n        return {"ctr": None, "completion_per_impression": None}\n    return {"ctr": sum(record["clicked"] for record in shown) / len(shown),\n            "completion_per_impression": sum(record["completed"] for record in shown) / len(shown)}',
    'A scan over N logged decisions costs O(N) time and O(N) memory here because it retains shown rows; streaming sums use O(1) memory. The larger operating cost is logging a complete, privacy-bounded exposure record without losing rank and policy identity.',
    ['Do not treat an unshown item as a disliked item.', 'Do not optimize clicks without checking the learning outcome.', 'Do not serve unpublished or ineligible content because a score is high.'],
    ['recommendation-systems/candidate-retrieval-and-eligibility','recommendation-systems/implicit-feedback-and-exposure-bias','data-science/metric-denominator-and-cohort','mlops/inference-logging-privacy'])

add('recommendation-systems/candidate-retrieval-and-eligibility',
    'Candidate retrieval: separate broad discovery from hard eligibility',
    'Candidate generation reduces a large catalog to a tractable set, but eligibility must still be enforced before anything is served.', [
    ('Combine candidate sources', 'A lesson feed can draw from prerequisites, related subjects, recently updated material and broad popularity. Each source can nominate item IDs with a source label. Deduplicate by canonical path before ranking; otherwise the same lesson can occupy several positions. [[recommendation-systems/content-collaborative-and-cold-start|Cold-start routes]] need a nonbehavioral source so new lessons enter the pool.'),
    ('Apply hard gates early', 'Exclude unpublished pages, completed lessons when the product requires novelty, and content outside the learner’s accessible curriculum. A model score is not a permission grant. Recheck at serving time because publication or access state can change after a batch index is built. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Document lifecycle]] has the same stale-index problem.'),
    ('Measure candidate recall', 'If a relevant future lesson never appears in the candidate pool, the ranker cannot recover it. Evaluate retrieval recall on held-out, eligible outcomes while separating missing judgment from irrelevant item. Report coverage by new items, sparse learners and subject areas. A pool of only popular Java lessons may score well overall while starving AI & Data discoveries.'),
    ('Bound latency and fallback', 'Cap each source and the final union, and document what happens when a personalized source times out. A fallback can use prerequisite and editorial paths, but must obey the same eligibility rules. Test duplicate nominations, a deleted page and an empty pool. An empty eligible set should return an explicit state rather than reintroducing barred items.')],
    'def eligible_candidates(nominations, published_paths, completed_paths, limit=60):\n    if limit < 1:\n        raise ValueError("limit must be positive")\n    selected = []\n    seen = set()\n    for lesson_path in nominations:\n        if lesson_path in seen or lesson_path not in published_paths or lesson_path in completed_paths:\n            continue\n        seen.add(lesson_path)\n        selected.append(lesson_path)\n        if len(selected) == limit:\n            break\n    return selected',
    'M nominations require O(M) expected time and O(K) memory for K retained paths. Hard-gate checks are O(1) expected with sets; a remote permission check changes the latency budget and may need a versioned local cache plus final validation.',
    ['Do not treat the ranker as an eligibility filter.', 'Do not count duplicate nominations as extra catalog coverage.', 'Do not hide recall losses behind ranking metrics.'],
    ['recommendation-systems/ranking-diversity-and-serving-constraints','recommendation-systems/offline-evaluation-and-temporal-split','recommendation-systems/content-collaborative-and-cold-start','retrieval-ai/corpus-permissions-and-document-lifecycle'])

add('recommendation-systems/implicit-feedback-and-exposure-bias',
    'Implicit feedback: distinguish preference from what the system exposed',
    'Clicks and completions are observations under a serving policy, not direct measurements of every item a learner might like.', [
    ('Read the signal carefully', 'A click can reflect position, title wording or current task rather than lasting preference. A completion can be missing because the learner had no time. Define positive events and their windows, then keep displayed-but-unclicked items separate from never-displayed items. [[recommendation-systems/objective-and-interaction-contract|The interaction contract]] determines which comparisons are even observable.'),
    ('Account for position', 'An item at rank one is more likely to be noticed than an equally useful item at rank eight. Training a ranker on raw clicks can reinforce the old policy’s favorites. Log rank and policy version, evaluate by placement, and reserve controlled exploration only where the product can tolerate it. Do not call every low-ranked omission a negative preference.'),
    ('Avoid duplicate events', 'One learner may click the same lesson repeatedly after a slow load. Deduplicate according to a defined session or impression ID, while retaining the original event audit trail. If completion arrives late, label the original impression using a fixed outcome window and version the result. [[time-series/observation-calendar-and-missing-periods|Late-outcome policy]] keeps offline labels stable.'),
    ('Inspect a counterexample', 'Suppose a policy displayed one lesson 47 times at rank one and another once at rank eight. Their raw click totals cannot establish which is intrinsically better. Report per-impression rates, positions and uncertainty; even those are observational unless exposure was assigned under a design that supports causal comparison.')],
    'def unique_clicks(events):\n    clicked_impressions = set()\n    for event in events:\n        if event["type"] == "click":\n            clicked_impressions.add(event["impression_id"])\n    return clicked_impressions',
    'Deduplicating N events with a set costs O(N) expected time and O(U) memory for U clicked impressions. A production event pipeline needs durable event IDs and retention rules; reducing data volume without preserving exposure metadata can make later evaluation invalid.',
    ['Do not label an unseen lesson as a negative example.', 'Do not interpret a raw click count without rank and impression count.', 'Do not collapse repeated events before defining the impression identity.'],
    ['recommendation-systems/objective-and-interaction-contract','recommendation-systems/offline-evaluation-and-temporal-split','causal-inference/assignment-balance-and-noncompliance','time-series/observation-calendar-and-missing-periods'])

add('recommendation-systems/content-collaborative-and-cold-start',
    'Content and collaborative signals: give sparse learners a real fallback',
    'Content similarity uses item attributes; collaborative signals use patterns of interaction across learners, and both inherit catalog and exposure limits.', [
    ('Build content features', 'Represent each lesson with stable subject, difficulty, prerequisite and concept tags. A new lesson can enter content retrieval before it has clicks, provided those attributes are reviewed. Similarity should not ignore progression: two lessons on the same subject may be redundant if one is already complete. [[recommendation-systems/candidate-retrieval-and-eligibility|Candidate sources]] should record why they nominated an item.'),
    ('Use behavioral evidence conditionally', 'Collaborative signals can discover cross-subject paths that metadata misses, but sparse learners and new lessons have weak history. Set a minimum evidence threshold and switch to a declared fallback below it. A global popularity fallback can still suppress niche subjects; diversify it with curriculum paths and current-page context. Do not pretend a cold-start rank is personalized.'),
    ('Prevent feature leakage', 'For offline tests, construct item metadata and learner history as they existed at the recommendation time. A lesson published after the held-out click cannot be an earlier candidate. Future completion events must not enter a past learner profile. [[recommendation-systems/offline-evaluation-and-temporal-split|Temporal evaluation]] should replay both history and catalog state.'),
    ('Check a sparse fixture', 'A new learner with no history opens a data-engineering article. The feed should still provide eligible prerequisite or related lessons. A new retrieval lesson with reviewed metadata but no impressions should be considered by content retrieval. A withdrawn article must disappear immediately even if a collaborative model assigns it a high score.')],
    'def recommendation_source(history_count, metadata_ready, minimum_events=4):\n    if history_count < 0 or minimum_events < 1:\n        raise ValueError("invalid history threshold")\n    if history_count >= minimum_events:\n        return "collaborative_plus_content" if metadata_ready else "collaborative"\n    return "content_context" if metadata_ready else "editorial_prerequisite"',
    'A threshold decision is O(1). Content similarity against C catalog items and F features can be O(CF) without an index; collaborative training adds matrix or embedding storage. Measure the incremental benefit before accepting the extra serving and maintenance cost.',
    ['Do not claim a no-history fallback is personalized.', 'Do not train past profiles from future completion events.', 'Do not leave new or niche lessons outside every candidate source.'],
    ['recommendation-systems/candidate-retrieval-and-eligibility','recommendation-systems/ranking-diversity-and-serving-constraints','recommendation-systems/offline-evaluation-and-temporal-split','data-engineering/data-engineering-tutorial'])

add('recommendation-systems/ranking-diversity-and-serving-constraints',
    'Ranking and re-ranking: balance relevance with coverage and curriculum rules',
    'A ranker orders eligible candidates; a final pass enforces slate-level constraints that item scores alone cannot express.', [
    ('Score comparable candidates', 'If several candidate sources produce their own scores, those values may be on incompatible scales. A common ranker can use context, item features and candidate-source identity, then calibrate against observed outcomes. Evaluate the declared learning metric rather than assuming a higher click probability is enough. [[recommendation-systems/objective-and-interaction-contract|Outcome choice]] controls the ranking objective.'),
    ('Construct the slate', 'Five individually high-scoring lessons can all cover the same concept. Add a simple diversity rule, such as at most two items from one subject in a five-item slate, and record when it is relaxed. A prerequisite gate is harder than a diversity preference. Apply hard constraints before optimizing soft ones, and surface the reason when no valid slate exists.'),
    ('Keep freshness and safety', 'Fresh material may need a discovery slot, but recency alone does not prove relevance. Remove withdrawn pages at request time and cap exposure of a new lesson until quality signals arrive. [[recommendation-systems/candidate-retrieval-and-eligibility|Candidate eligibility]] and serving-time validation are both needed if the index is stale.'),
    ('Check tradeoffs', 'Make a fixture with four high-scoring lessons from one subject and two slightly lower-scoring lessons from another. A three-item slate with a two-per-subject cap must include at least one from the second subject. Report relevance cost and subject coverage alongside the final order. An apparently diverse slate that repeats the same prerequisite is not useful diversity.')],
    'def capped_subject_slate(ranked_items, slate_size=3, per_subject_cap=2):\n    if slate_size < 1 or per_subject_cap < 1:\n        raise ValueError("slate limits must be positive")\n    selected = []\n    counts = {}\n    for item in ranked_items:\n        subject = item["subject"]\n        if counts.get(subject, 0) >= per_subject_cap:\n            continue\n        selected.append(item)\n        counts[subject] = counts.get(subject, 0) + 1\n        if len(selected) == slate_size:\n            break\n    return selected',
    'This pass costs O(K) time and O(S) state for K ranked candidates and S encountered subjects. More complex slate optimization can be expensive; start with explicit hard gates and measurable simple constraints before introducing a learned re-ranker.',
    ['Do not compare uncalibrated scores from unrelated candidate sources.', 'Do not apply a soft diversity preference in place of a hard access rule.', 'Do not maximize slate variety while hiding relevance loss.'],
    ['recommendation-systems/candidate-retrieval-and-eligibility','recommendation-systems/offline-evaluation-and-temporal-split','recommendation-systems/lesson-feed-project','retrieval-ai/retrieval-recall-and-reranking'])

add('recommendation-systems/offline-evaluation-and-temporal-split',
    'Offline recommendation evaluation: replay catalog and learner state in time',
    'An offline score is interpretable only for items that were eligible and observable under the logged policy.', [
    ('Split by decision time', 'Choose a cutoff, train on earlier interactions and score later recommendation decisions. Freeze learner history, item metadata and publication state at each origin. Randomly splitting clicks can leak a learner’s future completion into past predictions. [[time-series/lag-features-and-future-leakage|Temporal feature rules]] apply to recommenders as much as forecasts.'),
    ('Measure stages separately', 'Candidate recall asks whether later-positive eligible lessons entered the pool. Ranking measures such as recall at five assess order within that pool. Catalog coverage and new-item coverage show whether a policy repeatedly promotes only a small set. Keep a no-history cohort separate because its fallback differs from the learned route.'),
    ('Respect missing judgments', 'A held-out click is a known positive, but an unclicked or unexposed lesson is not necessarily irrelevant. Offline top-k metrics can reward the previous exposure pattern. Report that limit and run a controlled online experiment when a serving change matters. [[causal-inference/assignment-balance-and-noncompliance|Assignment design]] is needed to estimate the effect of the new policy.'),
    ('Audit a fixture', 'For a learner with two known relevant lessons, a five-item slate containing one of them has recall at five of one half under the declared judged set. Verify that a lesson published after the decision is excluded from both candidate pool and metric denominator. Count how many evaluated decisions have no judged eligible positive.')],
    'def recall_at_k(ranked_paths, relevant_paths, k):\n    if k < 1:\n        raise ValueError("k must be positive")\n    relevant = set(relevant_paths)\n    if not relevant:\n        return None\n    return len(set(ranked_paths[:k]) & relevant) / len(relevant)',
    'A top-k recall computation costs O(k + R) time and space for R known relevant items. Replaying N historical decisions can dominate because each needs a time-correct eligibility snapshot; store compact catalog versions to keep evaluation reproducible.',
    ['Do not random-split one learner’s time-ordered events.', 'Do not label every unobserved item irrelevant.', 'Do not report only ranking metrics when candidate recall or catalog coverage is poor.'],
    ['recommendation-systems/implicit-feedback-and-exposure-bias','recommendation-systems/lesson-feed-project','recommendation-systems/candidate-retrieval-and-eligibility','causal-inference/assignment-balance-and-noncompliance'])

add('recommendation-systems/lesson-feed-project',
    'Project: build a guarded next-lesson recommender',
    'Build a small next-lesson feed that logs impressions, enforces publication rules and compares a candidate policy with a baseline.', [
    ('Prepare the manifest', 'Create a catalog with paths, subject, prerequisites, publication state and effective time. Add learner progress and an impression log with rank, click, completion and policy version. Include a new lesson with no interactions, a learner with no history and a withdrawn page. [[recommendation-systems/objective-and-interaction-contract|The outcome contract]] must name the metric window and denominator.'),
    ('Assemble the feed', 'Nominate candidates from current-page concepts, prerequisites and an interaction-based route when history supports it. Deduplicate, apply hard eligibility and rank a short slate. Cap repeated subjects, then validate publication state again before serving. Keep an explicit empty state if no candidate survives. [[recommendation-systems/ranking-diversity-and-serving-constraints|Slate constraints]] must be visible in the submitted trace.'),
    ('Evaluate without hindsight', 'Use a chronological split and reconstruct learner history and catalog state at each decision. Report candidate recall, recall at five, catalog coverage and outcome rates for sparse learners separately. Do not turn undelivered candidates into negatives. Compare with a simple editorial-prerequisite baseline, and describe what offline logs cannot establish about a new policy’s causal effect.'),
    ('Submit checks', 'Deliver code, synthetic fixture, state manifest, example slate traces and a short release decision. Assert that the withdrawn page never appears, the cold-start learner receives a valid fallback and duplicate nominations occupy one slot. Include a privacy/deletion case and a recorded rollback path. [[mlops/shadow-canary-and-rollback|Canary and rollback]] should gate any real serving change.')],
    'def safe_lesson_slate(nominations, published_paths, completed_paths, limit=5):\n    if limit < 1:\n        raise ValueError("limit must be positive")\n    selected = []\n    seen = set()\n    for lesson_path in nominations:\n        if lesson_path in seen or lesson_path not in published_paths or lesson_path in completed_paths:\n            continue\n        seen.add(lesson_path)\n        selected.append(lesson_path)\n        if len(selected) >= limit:\n            break\n    return selected\n\nassert safe_lesson_slate(["ai/first", "ai/first", "ai/retired"], {"ai/first"}, set()) == ["ai/first"]',
    'A simple nomination filter is O(M) expected time with O(K) retained state; ranking K items is usually O(K log K). The project’s real cost lies in time-correct logging and catalog snapshots, which must be budgeted before a learned model is added.',
    ['Do not let an offline score override publication state.', 'Do not infer dislike from lack of exposure.', 'Do not ship without a cold-start and rollback path.'],
    ['recommendation-systems/candidate-retrieval-and-eligibility','recommendation-systems/offline-evaluation-and-temporal-split','recommendation-systems/content-collaborative-and-cold-start','mlops/shadow-canary-and-rollback'])

add('causal-inference/estimand-and-counterfactual-unit',
    'Causal estimands: name the unit, treatment and missing counterfactual',
    'A causal effect compares outcomes under two treatment states for the same target units, although each unit reveals only one state at a time.', [
    ('Specify the decision', 'Suppose AI Trove considers a new lesson recommendation panel. Define treatment as exposure to the new panel, the unit as learner or session, the outcome as a completed lesson within seven days and the eligible population before looking at results. An average effect for all eligible learners differs from the effect among those who clicked. [[applied-statistics/population-estimand-and-sampling-frame|Sampling and estimands]] keep that distinction visible.'),
    ('Recognize the missing value', 'For one learner, we can observe completion after the new panel or after the old panel, not both at the same time. The unobserved alternative is the counterfactual. A before-and-after difference for the same learner also mixes treatment with time, fatigue or changing catalog content. Identification requires a design that supplies a credible comparison group.'),
    ('Separate assignment from receipt', 'If a learner is assigned the new panel but never loads the page, the assigned-group effect and the effect among exposed users answer different questions. Assignment is fixed by design; exposure can depend on engagement. [[causal-inference/assignment-balance-and-noncompliance|Intention-to-treat analysis]] protects the original random comparison when take-up is incomplete.'),
    ('Create a decision contract', 'Write the population window, treatment version, unit, primary outcome, follow-up duration and exclusions. Include an interference check: a shared ranking cache might let one group alter the other’s recommendations. Test two sessions from one learner so the unit does not silently change when the same person returns.')],
    'def completion_effect(treated_outcomes, control_outcomes):\n    if not treated_outcomes or not control_outcomes:\n        raise ValueError("both assigned groups need outcomes")\n    if any(value not in (0, 1) for value in treated_outcomes + control_outcomes):\n        raise ValueError("completion outcomes must be binary")\n    return (sum(treated_outcomes) / len(treated_outcomes)\n            - sum(control_outcomes) / len(control_outcomes))',
    'Computing a difference in two observed group means is O(N) time and O(1) extra space. That arithmetic is cheap; the hard work is defining the estimand and defending why the group contrast represents the missing counterfactual.',
    ['Do not call a before-and-after difference a treatment effect without a comparison design.', 'Do not switch from assigned users to clickers without changing the estimand.', 'Do not treat two sessions from one learner as independent units by default.'],
    ['causal-inference/confounder-graph-and-covariate-timing','causal-inference/assignment-balance-and-noncompliance','applied-statistics/population-estimand-and-sampling-frame','applied-statistics/randomization-unit-and-experiment-design'])

add('causal-inference/confounder-graph-and-covariate-timing',
    'Confounders and covariate timing: adjust only for variables with a valid role',
    'A covariate can help, harm or change a causal analysis depending on when it was measured and what caused it.', [
    ('Draw the assumed paths', 'Prior learner activity can influence whether a person encounters the new panel and whether they complete lessons. It is a plausible pre-treatment confounder in observational data. By contrast, clicking the new panel occurs after treatment and may mediate its effect. Adjusting for that click can remove part of the effect being estimated. Record causal assumptions before selecting features.'),
    ('Check timestamps', 'A “last seven days of activity” feature measured after panel launch contains treatment-period behavior. Freeze covariates at or before assignment and keep a source-availability timestamp. [[time-series/lag-features-and-future-leakage|Causal feature timing]] shares the same future-information boundary as forecasting, though its purpose is identification rather than prediction.'),
    ('Avoid collider selection', 'Suppose both motivation and panel quality influence whether a learner opens a follow-up survey. An analysis restricted to survey respondents can create a spurious relationship between motivation and treatment even if assignment was random. Prefer outcome collection for all assigned units, and report missingness by group rather than quietly filtering to complete cases.'),
    ('Make the graph testable', 'List each variable, its measurement time, proposed role and whether it enters the adjustment set. Include prior activity, treatment assignment, panel click, completion and survey response. A reviewer should reject a post-treatment click used as a baseline covariate and ask how missing completions will be handled. [[causal-inference/assignment-balance-and-noncompliance|Assignment checks]] do not fix outcome selection bias.')],
    'def pre_assignment_covariates(covariates, assigned_at):\n    accepted = {}\n    for name, record in covariates.items():\n        if record["measured_at"] >= assigned_at:\n            raise ValueError(f"{name} was measured after assignment")\n        accepted[name] = record["value"]\n    return accepted',
    'Screening V covariates costs O(V) time and O(V) output space. The computational cost of a fitted adjustment model depends on its form, but no amount of fitting can identify an unmeasured confounder from timestamps alone.',
    ['Do not adjust for a mediator as though it were a baseline confounder.', 'Do not select only survey respondents without assessing selection.', 'Do not infer a causal graph from a correlation matrix.'],
    ['causal-inference/estimand-and-counterfactual-unit','causal-inference/overlap-and-weighting-diagnostics','causal-inference/sensitivity-and-placebo-checks','time-series/lag-features-and-future-leakage'])

add('causal-inference/assignment-balance-and-noncompliance',
    'Randomized assignment: check balance and retain every assigned unit',
    'Randomization supports a causal comparison when assignment, exposure, outcomes and interference follow the declared design.', [
    ('Lock the unit', 'If a learner can return from multiple devices, assign by stable learner key rather than page view. Record assignment once and keep it fixed. Shared family accounts or classroom sessions can create interference, so decide whether the cluster should instead be a classroom. [[applied-statistics/randomization-unit-and-experiment-design|The randomization unit]] also governs uncertainty calculations.'),
    ('Inspect sample ratios', 'Compare observed assigned counts with the intended allocation, including missing and excluded units. A large imbalance may indicate a routing or logging defect. Baseline covariate checks can catch an implementation error, but a favorable balance table does not prove perfect randomization, and a small chance difference does not justify reshuffling outcomes after the fact.'),
    ('Keep noncompliers', 'Some learners assigned the new panel may not see it because they leave before rendering. The primary intention-to-treat comparison keeps them in their assigned group. Restricting analysis to exposed learners conditions on post-assignment behavior. Report exposure rates and diagnose failures separately. [[causal-inference/estimand-and-counterfactual-unit|The estimand]] changes if a treatment-received effect is later sought.'),
    ('Exercise a release fixture', 'Assign 47 learners to the new panel and 53 to control under a 50/50 plan. Compare outcome collection and exposure counts for both groups. Add a duplicate assignment event and a learner with missing completion status. The analysis should keep one assigned record, flag the missing outcome and avoid silently replacing it with a zero.')],
    'def assigned_group_rates(assigned_rows):\n    groups = {"treatment": {"assigned": 0, "observed": []},\n              "control": {"assigned": 0, "observed": []}}\n    seen_learners = set()\n    for row in assigned_rows:\n        learner_id = row["learner_id"]\n        if learner_id in seen_learners or row["group"] not in groups:\n            raise ValueError("duplicate learner or unknown group")\n        seen_learners.add(learner_id)\n        group = groups[row["group"]]\n        group["assigned"] += 1\n        if row["completed"] is not None:\n            if row["completed"] not in (0, 1):\n                raise ValueError("invalid completion outcome")\n            group["observed"].append(row["completed"])\n    return {name: {"assigned": group["assigned"],\n                   "missing": group["assigned"] - len(group["observed"]),\n                   "observed_rate": (sum(group["observed"]) / len(group["observed"])\n                                     if group["observed"] else None)}\n            for name, group in groups.items()}',
    'Scanning N assignment rows costs O(N) expected time and O(N) state for uniqueness and observed outcomes. The function exposes missing groups as None; a full study must also report missing-outcome counts by assignment and assess their effect on the decision.',
    ['Do not analyze only learners who actually saw the panel as the primary randomized contrast.', 'Do not merge duplicate assignment events into extra learners.', 'Do not hide group-specific missing outcomes.'],
    ['causal-inference/estimand-and-counterfactual-unit','causal-inference/sensitivity-and-placebo-checks','applied-statistics/randomization-unit-and-experiment-design','recommendation-systems/implicit-feedback-and-exposure-bias'])

add('causal-inference/overlap-and-weighting-diagnostics',
    'Observational overlap and weighting: know where the data can compare',
    'An observational treatment contrast requires plausible exchangeability and enough comparable treated and untreated units.', [
    ('Limit the claim', 'Suppose early adopters choose the new lesson panel while others remain on the old one. Prior activity, course stage and device may affect both selection and completion. A propensity model estimates treatment probability from pre-treatment covariates; it does not make assignment random. Unmeasured motivation can still bias the effect. [[causal-inference/confounder-graph-and-covariate-timing|Covariate roles]] must be argued before modeling.'),
    ('Inspect common support', 'If every advanced learner adopts and no beginner does, the data cannot compare both treatments within those groups. Plot or summarize treatment probabilities by group and trim only under a predeclared target-population rule. Report how many units are removed and how the estimand changes. A model that outputs probabilities near zero or one is warning about weak overlap.'),
    ('Bound unstable weights', 'Inverse-probability weighting gives large influence to rare treatment assignments. A treated learner with estimated probability 0.01 has weight 100 under a simple treatment weight. Report weight distribution and effective sample size. Truncating weights may stabilize estimates but introduces a new analysis choice; set and report the threshold before reading the effect.'),
    ('Use a diagnostic fixture', 'Create probabilities 0.42, 0.57 and 0.01 for treated units. The last should trigger a support warning, not a quiet high-confidence estimate. Separate balance diagnostics before and after weighting. Refit no propensity feature measured after treatment and perform an unmeasured-confounding sensitivity check before drawing a causal conclusion.')],
    'def treatment_weights(treated_flags, treatment_probabilities, minimum_probability=0.05):\n    if len(treated_flags) != len(treatment_probabilities) or not 0 < minimum_probability < 0.5:\n        raise ValueError("invalid paired inputs or support threshold")\n    weights = []\n    for treated, probability in zip(treated_flags, treatment_probabilities):\n        if treated not in (0, 1) or not minimum_probability <= probability <= 1 - minimum_probability:\n            raise ValueError("weak overlap or invalid treatment probability")\n        weights.append(1 / probability if treated else 1 / (1 - probability))\n    return weights',
    'Computing N weights is O(N) time and O(N) output space. Propensity fitting can be much more expensive, but high effective weight concentration is a statistical limit that faster training cannot repair.',
    ['Do not call propensity adjustment randomization.', 'Do not hide units removed for weak overlap.', 'Do not interpret a highly weighted estimate without weight and balance diagnostics.'],
    ['causal-inference/confounder-graph-and-covariate-timing','causal-inference/sensitivity-and-placebo-checks','causal-inference/difference-in-differences-and-trends','applied-statistics/population-estimand-and-sampling-frame'])

add('causal-inference/difference-in-differences-and-trends',
    'Difference-in-differences: compare changes under a defended trend assumption',
    'A two-group, two-period difference-in-differences contrast subtracts the control change from the treated change.', [
    ('State the comparison', 'Imagine the panel launches in one academy but not another. Record the launch date, affected learners, outcome window and unit. If completion rises from 0.30 to 0.43 in the treated academy and from 0.28 to 0.34 in control, the two-period contrast is 0.07, or seven percentage points. That number is causal only under assumptions, especially that untreated trends would otherwise have evolved similarly.'),
    ('Inspect earlier periods', 'Plot several prelaunch periods using the same outcome definition and cohort rule. Divergent earlier movement weakens the parallel-trends story; similar earlier movement supports scrutiny but cannot prove the unobserved postlaunch counterfactual. [[time-series/observation-calendar-and-missing-periods|Calendar and missing-period rules]] must be shared across groups. A concurrent curriculum overhaul in one academy can break the comparison.'),
    ('Watch changing composition', 'A surge of new learners after launch changes the treated group even if the panel has no effect. Report cohort mix, attrition and eligibility before and after in both academies. If treatment starts at different times across many groups, a simple two-period formula or unexamined pooled regression may target a different weighted effect. Keep the lesson’s formula to its stated design.'),
    ('Challenge the design', 'Construct a placebo launch date before the real one and calculate the same contrast. A large placebo movement should prompt investigation. Also test a group unaffected by the panel but exposed to the same tracking changes. [[causal-inference/sensitivity-and-placebo-checks|Placebo checks]] are evidence about plausibility, not proof of parallel trends.')],
    'def two_period_difference_in_differences(treated_before, treated_after, control_before, control_after):\n    rates = (treated_before, treated_after, control_before, control_after)\n    if any(not 0 <= rate <= 1 for rate in rates):\n        raise ValueError("completion rates must be between zero and one")\n    return (treated_after - treated_before) - (control_after - control_before)\n\nassert round(two_period_difference_in_differences(0.30, 0.43, 0.28, 0.34), 2) == 0.07',
    'The four-rate contrast is O(1) after group-period aggregation; building rates from N learner records is O(N). Computation is not the main limit: parallel trends, stable composition and concurrent changes determine whether the contrast is interpretable.',
    ['Do not treat a pretrend plot as proof of the unobserved counterfactual.', 'Do not ignore group composition changes after launch.', 'Do not apply the two-period formula to staggered adoption without revisiting the estimand.'],
    ['causal-inference/estimand-and-counterfactual-unit','causal-inference/sensitivity-and-placebo-checks','time-series/observation-calendar-and-missing-periods','applied-statistics/hypothesis-test-and-effect-size'])

add('causal-inference/sensitivity-and-placebo-checks',
    'Sensitivity and placebo checks: state how the causal claim could fail',
    'A credible causal analysis records assumptions and probes them with checks that could contradict the proposed explanation.', [
    ('List threats explicitly', 'Unmeasured motivation can confound panel adoption; missing outcomes can differ by assignment; one academy can change curriculum during the test. A single p-value does not answer these threats. Write a threat-to-check table before analysis and keep the primary effect estimate separate from diagnostic results. [[causal-inference/confounder-graph-and-covariate-timing|The causal graph]] identifies where adjustment helps and where it cannot.'),
    ('Use negative controls', 'A panel shown today should not affect a completion outcome recorded last month. If the analysis reports an effect on that pre-treatment outcome, it may be detecting group differences or timestamp errors. Choose a negative-control outcome only when there is a defensible reason treatment cannot affect it. Its failure is informative; its success does not establish the main effect.'),
    ('Bound missing outcomes', 'Suppose 6 of 47 treated learners and 2 of 53 controls have unknown seven-day status. Compute best- and worst-case completion rates under plausible missing-status assignments, or use a justified missingness model. Report the range alongside the complete-case estimate. [[causal-inference/assignment-balance-and-noncompliance|Assigned-unit accounting]] makes such bounds possible.'),
    ('Report decision sensitivity', 'Vary a predeclared overlap cutoff or observation window and show whether the sign and practical conclusion persist. A result that appears only after one favorable slice deserves a narrower claim. If a placebo launch also yields a similar effect, hold the release decision and inspect data and concurrent interventions before asserting causality.')],
    'def binary_rate_bounds(observed_successes, observed_count, assigned_count):\n    if not 0 <= observed_successes <= observed_count <= assigned_count or assigned_count == 0:\n        raise ValueError("invalid assigned-unit counts")\n    missing = assigned_count - observed_count\n    return observed_successes / assigned_count, (observed_successes + missing) / assigned_count',
    'Binary missing-outcome bounds cost O(1) after counts are available. Repeating an estimator over S defensible specifications costs roughly S times one fit; preregister the set so compute is not used to search for a preferred answer.',
    ['Do not present a passed placebo as proof of no confounding.', 'Do not discard missing assigned units from the study population.', 'Do not choose sensitivity settings after seeing which produce significance.'],
    ['causal-inference/overlap-and-weighting-diagnostics','causal-inference/difference-in-differences-and-trends','causal-inference/lesson-panel-effect-project','applied-statistics/multiple-comparisons-and-stopping-rule'])

add('causal-inference/lesson-panel-effect-project',
    'Project: review the effect of a new lesson recommendation panel',
    'Produce a causal review packet for a panel change, distinguishing randomized evidence from observational and before-after comparisons.', [
    ('Freeze the question', 'Define the learner as assignment unit, the panel version as treatment and seven-day lesson completion as outcome. State the eligible population, follow-up cutoff, interference risk and primary intention-to-treat estimand. Build a fixture with assigned treatment and control learners, exposure flags, prior activity and missing outcomes. [[causal-inference/estimand-and-counterfactual-unit|The target effect]] must be fixed before reading the completion counts.'),
    ('Audit assignment and outcomes', 'Check duplicate learner keys, group counts, exposure imbalance and outcome collection by assigned group. Compute the completion-rate difference with all observed assigned units and give bounds for unknown outcomes. Do not quietly analyze only users who clicked the panel. [[causal-inference/assignment-balance-and-noncompliance|Noncompliance]] belongs in a separate report.'),
    ('Compare weaker designs', 'Construct a naive exposed-versus-unexposed estimate and a simple before-after estimate from the same fixture. Explain how motivation and time can move them away from the randomized contrast. If using a difference-in-differences comparison, inspect prelaunch trends and concurrent changes rather than treating its formula as automatic causal proof.'),
    ('Submit an evidence packet', 'Include the assignment manifest, timestamped covariates, exclusion ledger, count reconciliation, estimate and uncertainty method, placebo or negative-control check, and a short release decision. A reviewer should reproduce every numerator and denominator. Report where evidence ends: a result for eligible learners this month does not automatically transfer to every learner or later catalog version.')],
    'def assigned_completion_difference(treatment, control):\n    if not treatment or not control:\n        raise ValueError("both assigned groups are required")\n    if any(outcome not in (0, 1) for outcome in treatment + control):\n        raise ValueError("resolve or bound missing outcomes separately")\n    return sum(treatment) / len(treatment) - sum(control) / len(control)\n\nassert assigned_completion_difference([1, 0, 1], [0, 0, 1]) == 1 / 3',
    'Computing the observed contrast is O(N) time. Reconciliation and clustered uncertainty can require additional passes or resampling; preserve the immutable assignment ledger so later corrections do not rewrite which group a learner belonged to.',
    ['Do not substitute a clicker-only comparison for the assigned-group effect.', 'Do not use post-treatment clicks as baseline adjustment variables.', 'Do not publish a causal claim without a stated identification design and missing-outcome account.'],
    ['causal-inference/assignment-balance-and-noncompliance','causal-inference/sensitivity-and-placebo-checks','causal-inference/difference-in-differences-and-trends','recommendation-systems/lesson-feed-project'])

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
 'recommendation-systems': {
     'root':'recommendation-systems/recommendation-systems-tutorial', 'name':'Recommendation Systems',
     'summary':'Design a guarded recommendation feed with explicit exposure data, candidate coverage, sparse-user fallbacks and temporal evaluation.',
     'groups':[('Signals and candidate supply', ['objective-and-interaction-contract','candidate-retrieval-and-eligibility','implicit-feedback-and-exposure-bias','content-collaborative-and-cold-start']),
               ('Ranking and assessment', ['ranking-diversity-and-serving-constraints','offline-evaluation-and-temporal-split'])],
     'project':'lesson-feed-project',
     'foundation':['machine-learning/machine-learning-tutorial','retrieval-ai/retrieval-ai-tutorial'],
     'neighbors':['causal-inference/causal-inference-tutorial','time-series/time-series-tutorial']},
 'causal-inference': {
     'root':'causal-inference/causal-inference-tutorial', 'name':'Causal Inference',
     'summary':'Define causal effects, defend comparison designs and test the assumptions behind intervention decisions.',
     'groups':[('Question and design', ['estimand-and-counterfactual-unit','confounder-graph-and-covariate-timing','assignment-balance-and-noncompliance']),
               ('Observational designs and scrutiny', ['overlap-and-weighting-diagnostics','difference-in-differences-and-trends','sensitivity-and-placebo-checks'])],
     'project':'lesson-panel-effect-project',
     'foundation':['applied-statistics/applied-statistics-tutorial','time-series/time-series-tutorial'],
     'neighbors':['recommendation-systems/recommendation-systems-tutorial','data-visualization/data-visualization-tutorial']},
}

for config in subject_config.values():
    titles[config['root']] = config['name'] + ' Tutorial'
    titles[config['root'] + '/project'] = config['name'] + ': Projects'

for slug, config in subject_config.items():
    root_path = config['root']
    project_hub_path = root_path + '/project'
    titles[root_path] = config['name'] + ' Tutorial'
    titles[project_hub_path] = config['name'] + ': Projects'
    modules = [{'title':group_title, 'summary':'Read in order and run the failure checks.',
                'lessons':[slug + '/' + lesson_name for lesson_name in lesson_names]}
               for group_title, lesson_names in config['groups']]
    project_path = slug + '/' + config['project']
    modules.append({'title':'Apply your knowledge', 'lessons':[project_path]})
    all_paths = [path for module in modules for path in module['lessons']]
    tabs = [{'title':config['name'], 'path':root_path}, {'title':'Projects', 'path':project_hub_path}]
    hub_body = ('<p>' + html.escape(config['summary']) + '</p><h2>Learning path</h2>' + links(all_paths)
                + '<h2>Connected foundations</h2><p>Use the earlier data and model boundaries as prerequisites.</p>'
                + links(config['foundation']) + '<h2>Further paths</h2>' + links(config['neighbors'])
                + '<h2>Practice</h2>' + links([project_hub_path]))
    hub = make_row(root_path, titles[root_path], config['summary'], hub_body,
                   'subject', slug, root_path, root_path, 8800 if slug == 'recommendation-systems' else 8900,
                   {'modules':modules, 'resource_tabs':tabs})
    project_body = ('<p>Apply the ' + html.escape(config['name']) + ' curriculum to a checked project.</p>'
                    '<h2>Project brief</h2>' + links([project_path])
                    + '<h2>Required concepts</h2>' + links(all_paths[:-1])
                    + '<h2>Completion standard</h2><p>Submit runnable work, a data manifest, measured results and failure-case evidence.</p>')
    project_hub = make_row(project_hub_path, titles[project_hub_path],
                           'A checked project for the ' + config['name'] + ' curriculum.', project_body,
                           'subject', slug + '-project', project_hub_path, root_path,
                           8801 if slug == 'recommendation-systems' else 8901,
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
                       9000 + index,
                       {'kind':'project' if is_project else 'tutorial',
                        'reading_minutes':max(5, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                        'author_path':'authors/aitrove-editorial',
                        'verification_suite':'Editorial and syntax review; project inputs needed for runtime checks',
                        'related':[{'path':path,'title':titles[path]} for path in item['related']]})
    rows.append(article)
    by_path[item['path']] = article

for source, target in [
    ('machine-learning/decision-threshold-and-cost','recommendation-systems/objective-and-interaction-contract'),
    ('retrieval-ai/retrieval-recall-and-reranking','recommendation-systems/candidate-retrieval-and-eligibility'),
    ('mlops/inference-logging-privacy','recommendation-systems/implicit-feedback-and-exposure-bias'),
    ('time-series/lag-features-and-future-leakage','recommendation-systems/offline-evaluation-and-temporal-split'),
    ('applied-statistics/population-estimand-and-sampling-frame','causal-inference/estimand-and-counterfactual-unit'),
    ('applied-statistics/randomization-unit-and-experiment-design','causal-inference/assignment-balance-and-noncompliance'),
    ('applied-statistics/multiple-comparisons-and-stopping-rule','causal-inference/sensitivity-and-placebo-checks'),
    ('time-series/observation-calendar-and-missing-periods','causal-inference/difference-in-differences-and-trends'),
]:
    row = by_path[source]
    anchor = '<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in row['body']:
        row['body'] += anchor
        row['data']['related'].append({'path':target,'title':titles[target]})
        row['updated_at'] = stamp

for source, target in [
    ('machine-learning/machine-learning-tutorial','recommendation-systems/recommendation-systems-tutorial'),
    ('retrieval-ai/retrieval-ai-tutorial','recommendation-systems/recommendation-systems-tutorial'),
    ('applied-statistics/applied-statistics-tutorial','causal-inference/causal-inference-tutorial'),
    ('time-series/time-series-tutorial','causal-inference/causal-inference-tutorial'),
]:
    row = by_path[source]
    anchor = '<p><strong>Continue into another subject:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in row['body']:
        row['body'] += anchor
        row['updated_at'] = stamp

assert len({row['path'] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_articles':len(lessons), 'new_subject_hubs':4, 'crosslinks_from_existing':12}))
