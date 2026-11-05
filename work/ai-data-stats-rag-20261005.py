"""Add Applied Statistics and retrieval-based AI curricula to AI Trove preview."""
import datetime
import html
import json
from pathlib import Path
import re
import uuid

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
rows = [row for row in rows if not row['path'].startswith(('applied-statistics/', 'retrieval-ai/'))]
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()

def prose(value):
    return re.sub(r'\[\[([^|]+)\|([^\]]+)\]',
                  lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                  html.escape(value))

lessons = [
 dict(path='applied-statistics/population-estimand-and-sampling-frame', title='Population, estimand and sampling frame: name the quantity before calculating',
      summary='An analysis needs a target population, an exact quantity and a sampling process that can observe that population.',
      sections=[
       ('State the target', 'A receipt-review rate might mean all receipts submitted in September, only those eligible for manual review, or only those with a completed decision. These are different populations. Define the event window, eligibility rule, unit and numerator before writing a query. [[data-science/metric-denominator-and-cohort|Metric denominators]] turn a vague business question into a reproducible count.'),
       ('Describe the observation path', 'The sampling frame is the set of units that could enter the dataset. If mobile submissions are missing during an outage, the observed frame omits them; a tiny standard error cannot repair that bias. Record coverage by channel, region and time. A convenience sample of reviewed receipts can estimate properties of reviewed receipts, but not necessarily all submissions.'),
       ('Check dependence', 'One customer may submit several receipts, and one receipt may create multiple events. Decide whether the unit is customer, receipt or event. If units are clustered, treating every row as independent understates uncertainty. [[applied-statistics/cluster-bootstrap-and-standard-error|Clustered uncertainty]] keeps repeated observations together.'),
       ('Make exclusions visible', 'Produce a flow of counts from raw submissions to eligible units, observed outcomes and final analysis rows. Reconcile missing IDs and late outcomes. Test a duplicated receipt and an outage day. If the sample changes because a late outcome arrives, version the analysis cutoff rather than silently replacing yesterday’s denominator.')],
      code='def eligible_receipts(records, window_start, window_end):\n    selected = {}\n    for receipt in records:\n        if not window_start <= receipt.submitted_at < window_end:\n            continue\n        if receipt.receipt_id in selected:\n            raise ValueError("receipt appears more than once")\n        selected[receipt.receipt_id] = receipt\n    return list(selected.values())',language='python',
      cost='A scan is O(N) over source rows; a dictionary for uniqueness uses O(K) memory for K eligible receipts. Recording exclusions adds storage but prevents a precise estimate of the wrong population.',
      mistakes=['Do not treat a convenience sample as the entire target population.', 'Do not count receipt events as independent receipts.', 'Do not let late outcomes change a historical denominator without a version.'],
      related=['applied-statistics/distribution-quantiles-and-outlier-policy','applied-statistics/cluster-bootstrap-and-standard-error','data-science/metric-denominator-and-cohort','data-science/dataset-grain-and-join-cardinality']),
 dict(path='applied-statistics/distribution-quantiles-and-outlier-policy', title='Distribution summaries: report tails and define the outlier policy',
      summary='A mean alone can hide a skewed process; quantiles, missingness and an explicit outlier rule show what the data contains.',
      sections=[
       ('Inspect the shape first', 'Receipt-review delay can have a low median and a long tail from tickets held over a weekend. Report count, missing count, median and upper quantiles beside the mean. A histogram or empirical distribution can reveal modes from different workflows. [[data-science/exploratory-analysis-without-peeking|Exploration]] belongs on the development partition when the summary will guide model decisions.'),
       ('Separate invalid from extreme', 'A negative delay may signal a clock or join error; a 19-day delay may be valid but operationally important. Quarantine impossible records under a documented rule. Do not trim valid extremes merely because they make a dashboard look worse. If a capped metric is useful, present the uncapped distribution and the cap count too.'),
       ('Choose a stable comparison', 'When comparing two periods, keep the same eligibility, units and time-zone boundaries. A change in channel mix can shift the overall mean while each channel remains stable. Show per-channel counts and summaries before attributing the movement to a process change. [[applied-statistics/population-estimand-and-sampling-frame|The sampling frame]] can change without any underlying service change.'),
       ('Check the calculation', 'Use a tiny fixture with delays of 3, 4, 5, 6 and 47 hours. Its mean is 13 hours and median is 5 hours, so either value alone tells a different story. Verify the quantile method used by the implementation and keep it fixed across reports. Record missing and excluded values separately.')],
      code='from statistics import mean, median\n\ndef review_delay_summary(delays_hours):\n    valid = [value for value in delays_hours if value is not None and value >= 0]\n    rejected = sum(value is not None and value < 0 for value in delays_hours)\n    if not valid:\n        raise ValueError("no valid review delays")\n    ordered = sorted(valid)\n    upper_index = min(len(ordered) - 1, int(0.9 * len(ordered)))\n    return {"count": len(valid), "missing": delays_hours.count(None),\n            "rejected": rejected, "mean": mean(valid),\n            "median": median(valid), "upper_observation": ordered[upper_index]}',language='python',
      cost='Sorting N delays for quantiles costs O(N log N) time and O(N) memory; streaming mean and count use O(1) memory. Approximate quantiles save memory but need an error contract.',
      mistakes=['Do not discard a valid tail value because it is inconvenient.', 'Do not compare means across different channel mixes without showing composition.', 'Do not hide rejected records inside a missing count.'],
      related=['applied-statistics/population-estimand-and-sampling-frame','applied-statistics/confidence-interval-coverage','data-science/exploratory-analysis-without-peeking','data-science/missing-data-policy']),
 dict(path='applied-statistics/cluster-bootstrap-and-standard-error', title='Standard error and cluster bootstrap: resample the independent unit',
      summary='Uncertainty depends on the unit that was sampled; repeated receipts from one customer should move together in a bootstrap resample.',
      sections=[
       ('Find the independent unit', 'If customers generate multiple receipts, the rows are correlated. Resampling individual receipts pretends every row arrived independently and can make an interval too narrow. Resample customers, carrying all their eligible receipts into each draw. If assignment or sampling happened at store level, the store may be the correct cluster instead. [[applied-statistics/population-estimand-and-sampling-frame|The estimand]] determines how clusters contribute to the final rate.'),
       ('Implement a paired statistic', 'For each bootstrap draw, sample clusters with replacement and recompute the statistic from all selected records. A customer drawn twice contributes twice. Keep a fixed seed and record the number of draws. A percentile interval describes the resampling distribution under this design; it does not repair a biased sampling frame or missing outcomes.'),
       ('Watch small-cluster limits', 'A dataset with thousands of receipts but only six stores has little independent store-level information. More bootstrap draws do not create more stores. Report cluster count and size distribution. For very few clusters, use a design-specific method or mark the interval unstable. [[applied-statistics/confidence-interval-coverage|Coverage interpretation]] depends on the repeated-sampling procedure, not on a single computed interval.'),
       ('Validate with a fixture', 'Create four customers with two receipts each, and make one customer’s outcomes unusually poor. Compare row and customer resampling. The customer-based distribution should reflect that customer entering zero, one or multiple times. Test a customer with no valid outcome and state whether it stays in the denominator.')],
      code='import random\n\ndef customer_bootstrap_rate(rows_by_customer, draws=1500, seed=47):\n    customer_ids = list(rows_by_customer)\n    if len(customer_ids) < 2 or any(not values for values in rows_by_customer.values()):\n        raise ValueError("need two customers with observed outcomes")\n    generator = random.Random(seed)\n    estimates = []\n    for _ in range(draws):\n        sampled = [generator.choice(customer_ids) for _ in customer_ids]\n        outcomes = [outcome for customer_id in sampled\n                    for outcome in rows_by_customer[customer_id]]\n        estimates.append(sum(outcomes) / len(outcomes))\n    return sorted(estimates)',language='python',
      cost='With B draws and N total rows per draw, a direct implementation costs O(BN) time plus O(B) stored estimates. Aggregate per-cluster successes and counts first to reduce repeated row traversal.',
      mistakes=['Do not resample rows when customers were the independent units.', 'Do not confuse more bootstrap draws with more independent data.', 'Do not ignore clusters with missing outcomes silently.'],
      related=['applied-statistics/confidence-interval-coverage','applied-statistics/population-estimand-and-sampling-frame','data-science/bootstrap-interval-interpretation','applied-statistics/randomization-unit-and-experiment-design']),
 dict(path='applied-statistics/confidence-interval-coverage', title='Confidence intervals: interpret coverage and precision honestly',
      summary='A confidence interval describes the long-run behavior of a construction method under its sampling assumptions.',
      sections=[
       ('Interpret the method', 'A 95% interval procedure should cover a fixed population quantity in about 95% of repeated samples when its assumptions hold. The already-computed interval either contains that quantity or does not; the confidence percentage is not a posterior probability assigned to this one interval. [[data-science/bootstrap-interval-interpretation|Bootstrap interpretation]] supplies a concrete resampling example.'),
       ('Separate width from validity', 'More independent observations often narrow an interval. They do not fix selection bias, measurement errors or a misdefined denominator. A very narrow interval around a review rate based only on successfully processed tickets can be precisely wrong for all submissions. Report coverage, unit count and major exclusions beside endpoints.'),
       ('Use the right resampling unit', 'If customers or stores create correlated observations, construct uncertainty around those clusters. If the statistic is a ratio, recompute the numerator and denominator in every resample rather than averaging row-level ratios. [[applied-statistics/cluster-bootstrap-and-standard-error|Cluster bootstrap]] makes this distinction explicit.'),
       ('Check decisions at the boundary', 'Suppose a release requires review rate below 0.14. An estimate of 0.12 with an upper interval endpoint of 0.17 does not establish the release criterion. State whether the rule uses the point estimate or a conservative bound before seeing data. Do not switch the confidence level after observing the result.')],
      code='def interval_release_decision(lower_bound, upper_bound, maximum_rate):\n    if not 0 <= lower_bound <= upper_bound <= 1:\n        raise ValueError("invalid rate interval")\n    if not 0 <= maximum_rate <= 1:\n        raise ValueError("invalid rate limit")\n    return {"passes_upper_bound_rule": upper_bound < maximum_rate,\n            "interval": (lower_bound, upper_bound)}',language='python',
      cost='A parametric interval can be O(N) after sufficient summaries; a bootstrap costs repeated O(N) statistic evaluations. The dominant risk is often invalid sampling assumptions rather than compute.',
      mistakes=['Do not say the fixed parameter has a 95% chance of lying in a frequentist interval.', 'Do not treat narrow width as proof of unbiased sampling.', 'Do not choose a bound rule after seeing the endpoints.'],
      related=['applied-statistics/cluster-bootstrap-and-standard-error','applied-statistics/hypothesis-test-and-effect-size','data-science/bootstrap-interval-interpretation','applied-statistics/receipt-review-experiment-project']),
]

lessons.extend([
 dict(path='applied-statistics/hypothesis-test-and-effect-size', title='Hypothesis tests: pair the decision rule with an effect size',
      summary='A test asks whether data conflict with a specified null process; the observed difference and its uncertainty answer the practical question.',
      sections=[
       ('Specify the question first', 'For a proposed review workflow, define the outcome, unit, direction and smallest useful change. State the null process and significance level before results arrive. A p-value is computed under that null; it is not the probability the null is true. A small p-value can accompany a trivial effect in a large dataset, while a useful effect may remain uncertain in a small one.'),
       ('Use assignment structure', 'A permutation test swaps labels only where exchangeability is justified. If stores were randomized, shuffle store assignments rather than individual receipts. If the same customer was observed before and after, use a paired statistic or a design-specific model. [[applied-statistics/randomization-unit-and-experiment-design|Randomization units]] determine valid comparison mechanics.'),
       ('Report magnitude and precision', 'Show the treated and control rates, absolute difference, interval and counts. A 1.2 percentage-point reduction may matter differently at 400 versus four million monthly receipts. [[applied-statistics/confidence-interval-coverage|Intervals]] show uncertainty in the magnitude; a binary significance label cannot replace them.'),
       ('Exercise a null fixture', 'Create two groups with the same outcomes but different row order and confirm the statistic is zero. Then inject a known change and check its sign. Verify that a test cannot run on empty groups, missing outcomes or a post-hoc slice chosen because it looked favorable.')],
      code='from itertools import chain\n\ndef rate_difference(treatment, control):\n    if len(treatment) == 0 or len(control) == 0:\n        raise ValueError("both groups require observed outcomes")\n    if any(value not in (0, 1) for value in chain(treatment, control)):\n        raise ValueError("outcomes must be binary")\n    return sum(treatment) / len(treatment) - sum(control) / len(control)\n\nobserved_difference = rate_difference(treatment_outcomes, control_outcomes)',language='python',
      cost='Calculating a rate difference is O(N). A permutation test with B resamples costs O(BN) in a direct implementation. The inferential validity depends more on assignment and missingness than on the speed of arithmetic.',
      mistakes=['Do not call a p-value the probability the null is true.', 'Do not omit the effect size and group denominators.', 'Do not shuffle receipt rows when assignment happened by store.'],
      related=['applied-statistics/randomization-unit-and-experiment-design','applied-statistics/multiple-comparisons-and-stopping-rule','applied-statistics/confidence-interval-coverage','data-science/metric-denominator-and-cohort']),
 dict(path='applied-statistics/randomization-unit-and-experiment-design', title='Experiment design: assign the right unit and guard against interference',
      summary='An experiment needs a stable assignment unit, eligible population, exposure rule and outcome window before traffic is divided.',
      sections=[
       ('Choose the assignment unit', 'If reviewers share a queue, assigning individual receipts to two workflows can create interference: one treatment changes wait time for controls. Randomize at reviewer, queue or store level when necessary, then analyze uncertainty at that level. A customer-level assignment may be required when the same customer submits several receipts. [[applied-statistics/cluster-bootstrap-and-standard-error|Cluster uncertainty]] follows the design.'),
       ('Define exposure', 'A unit assigned to treatment may never see the new workflow. State whether the primary estimate compares assigned groups or only those exposed. Filtering to exposed users after randomization can reintroduce selection bias. Keep assignment events, exposure events and outcome windows separate. Record when a unit can enter or leave the experiment.'),
       ('Protect concurrent changes', 'A marketing campaign, outage or policy update during the test can change receipt mix. Random assignment balances many differences in expectation, but operational incidents still need tracking. Decide whether to pause, extend or analyze incident periods under a written rule. [[applied-statistics/population-estimand-and-sampling-frame|The target population]] should match the rollout population.'),
       ('Run integrity checks', 'Before reading outcomes, verify stable allocation by unit, no duplicate assignments, balanced pre-treatment characteristics and correct exposure logging. Simulate a customer with two receipts and a store crossing the rollout boundary. Both receipts must receive the intended consistent assignment if customer is the unit.')],
      code='import hashlib\n\ndef assign_review_variant(customer_id, experiment_key):\n    if not customer_id:\n        raise ValueError("customer identity required")\n    assignment_key = f"{experiment_key}:{customer_id}".encode("utf-8")\n    bucket = int.from_bytes(hashlib.sha256(assignment_key).digest()[:4], "big")\n    return "new-review" if bucket % 2 == 0 else "current-review"',language='python',
      cost='Stable hashing is O(length of assignment key) per unit. Cluster assignment reduces the number of independent units and may require a longer experiment than receipt-level assignment.',
      mistakes=['Do not change assignment per request for the same unit.', 'Do not analyze only exposed units without naming the selection problem.', 'Do not ignore shared-queue interference.'],
      related=['applied-statistics/hypothesis-test-and-effect-size','applied-statistics/cluster-bootstrap-and-standard-error','applied-statistics/multiple-comparisons-and-stopping-rule','applied-statistics/receipt-review-experiment-project']),
 dict(path='applied-statistics/multiple-comparisons-and-stopping-rule', title='Multiple comparisons and peeking: protect a predeclared decision rule',
      summary='Testing many outcomes, segments or interim snapshots raises false-positive risk unless the comparison family and stopping rule are planned.',
      sections=[
       ('Name the comparison family', 'A team may inspect review rate, delay, cost and 20 product slices, then highlight the one favorable result. Each test offers another chance to see noise. Choose a primary outcome and planned guardrails before launch. For a family of confirmatory comparisons, use a stated correction or joint decision rule. Exploratory slices are useful for diagnosis but should be labeled as exploratory.'),
       ('Choose when to stop', 'Repeatedly checking an ordinary fixed-sample p-value and stopping at the first low value breaks its nominal error interpretation. Predeclare a sample size or use a valid sequential design. An operational safety stop is separate: a severe incident can halt a test, but should not be rebranded as statistical success. [[applied-statistics/randomization-unit-and-experiment-design|Experiment design]] fixes the assignment clock.'),
       ('Retain effect size', 'A correction can make significance harder to reach; it does not change the observed effect. Report estimated changes and intervals alongside adjusted decisions. A practically harmful guardrail should matter even if it narrowly misses a significance threshold. [[applied-statistics/hypothesis-test-and-effect-size|Effect-size reporting]] keeps the interpretation anchored in work impact.'),
       ('Audit the analysis plan', 'Store primary metric, family of tests, correction, planned end condition and exclusion policy under a versioned experiment ID. Run a fixture with several identical null segments and ensure the report does not elevate the smallest p-value as if it had been the sole planned test.')],
      code='def bonferroni_decisions(p_values_by_metric, family_alpha=0.05):\n    if not p_values_by_metric or not 0 < family_alpha < 1:\n        raise ValueError("invalid comparison family or alpha")\n    if any(not 0 <= value <= 1 for value in p_values_by_metric.values()):\n        raise ValueError("invalid p-value")\n    per_test_limit = family_alpha / len(p_values_by_metric)\n    return {metric: value <= per_test_limit\n            for metric, value in p_values_by_metric.items()}',language='python',
      cost='A simple correction is O(M) for M planned tests. Its conservatism can increase required sample size; unplanned repeated looks create interpretation cost that extra compute cannot fix.',
      mistakes=['Do not select the best-looking slice after seeing results and call it confirmatory.', 'Do not stop at the first ordinary p-value below a threshold.', 'Do not hide effect sizes behind adjusted significance labels.'],
      related=['applied-statistics/hypothesis-test-and-effect-size','applied-statistics/randomization-unit-and-experiment-design','applied-statistics/receipt-review-experiment-project','data-science/exploratory-analysis-without-peeking']),
 dict(path='applied-statistics/receipt-review-experiment-project', title='Project: evaluate a receipt-review workflow without changing the question midstream',
      summary='Design a review-workflow experiment with a fixed population, assignment unit, primary rate, uncertainty method and stopping rule.',
      sections=[
       ('Write the analysis contract', 'Define eligible receipts, assignment unit, outcome window, primary metric and smallest useful improvement before simulating treatment. Include an outage day, a repeated customer and delayed outcomes in the fixture. State whether analysis compares assigned or exposed units. [[applied-statistics/population-estimand-and-sampling-frame|Population definition]] is the first deliverable.'),
       ('Check randomization and data', 'Use a stable hash assignment, then verify no unit appears in both variants. Reconcile raw, excluded, pending and measured outcomes. Report group counts and pre-treatment balance. If assignment happened by customer, calculate uncertainty by customer rather than pretending each receipt is independent. [[applied-statistics/cluster-bootstrap-and-standard-error|Cluster resampling]] supplies the uncertainty exercise.'),
       ('Apply a frozen rule', 'Estimate the difference in review rates and its interval. Compare the result with the declared improvement target and guardrails. Show a predeclared end condition and label exploratory slices separately. [[applied-statistics/multiple-comparisons-and-stopping-rule|Multiplicity]] must be addressed before inspecting a collection of favorable segments.'),
       ('Submit a decision record', 'Provide fixture, analysis code, manifest, outcome counts, interval, assumption checks and a one-page decision. Include a failure drill: duplicate assignment, missing store partition or immature label must block a clean result. A chart without numerator, denominator and exclusion counts does not complete the project.')],
      code='def experiment_integrity(assignments, outcomes):\n    variant_by_customer = {}\n    for customer_id, variant in assignments:\n        previous = variant_by_customer.setdefault(customer_id, variant)\n        if previous != variant:\n            raise ValueError("customer assigned to both variants")\n    known_customers = set(variant_by_customer)\n    if any(customer_id not in known_customers for customer_id in outcomes):\n        raise ValueError("outcome without assignment")\n    return len(known_customers)',language='python',
      cost='Assignment integrity is O(N) time and O(K) memory for N events and K customers. Cluster bootstrap adds repeated computation; documenting excluded and pending outcomes adds modest storage.',
      mistakes=['Do not change the primary metric after viewing the result.', 'Do not treat pending outcomes as failures.', 'Do not report receipt-level precision for customer-level assignment.'],
      related=['applied-statistics/population-estimand-and-sampling-frame','applied-statistics/randomization-unit-and-experiment-design','applied-statistics/confidence-interval-coverage','applied-statistics/multiple-comparisons-and-stopping-rule']),
])

lessons.extend([
 dict(path='retrieval-ai/retrieval-vs-answer-evaluation', title='RAG evaluation: separate retrieval recall from answer support',
      summary='A retrieval-based answer can fail because evidence was missed, misused or unavailable; evaluate each boundary with different tests.',
      sections=[
       ('Build judged questions', 'Write questions from real user intents with allowed corpus revision, required passage IDs and expected answer or no-answer state. Include exact identifiers, paraphrases, conflicting policies and queries outside the corpus. Keep an untouched final set after tuning chunking, retrieval and prompts. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Document versions]] make an evaluation item reproducible.'),
       ('Score retrieval first', 'Check whether all required evidence fits inside the selected context budget. A relevant passage at rank 40 is effectively absent when only six passages reach generation. Report recall by query type and access scope. If evidence is missing, changing answer wording will not fix the root cause. [[retrieval-ai/retrieval-recall-and-reranking|Retrieval choices]] should be tested against the same judged set.'),
       ('Score answers separately', 'When supporting passages were present, inspect factual claims against those passages, scope, no-answer behavior and conflicting-evidence handling. An answer can be fluent yet unsupported. Automated graders can prioritize review, but sample manual judgments and disagreement checks are needed for high-impact claims. Track evidence IDs and answer status in the result.'),
       ('Keep an error ledger', 'For each failure, classify missing corpus content, permission filter, chunk boundary, rank, context truncation, generation misuse or unsupported assertion. This assigns repairs to the right stage. Re-run the same frozen questions after one change at a time; otherwise a score movement cannot be attributed.')],
      code='def retrieval_recall_at_budget(required_ids, ranked_ids, budget):\n    if budget <= 0:\n        raise ValueError("context budget must be positive")\n    required = set(required_ids)\n    if not required:\n        raise ValueError("use a no-answer test for zero required passages")\n    returned = set(ranked_ids[:budget])\n    return len(required & returned) / len(required)\n\ncase_result = retrieval_recall_at_budget(judged_passage_ids, ranked_passage_ids, 6)',language='python',
      cost='Checking one case uses O(R+B) time for R required IDs and B returned IDs. Building high-quality judged sets costs expert review; that cost is necessary to know which stage changed.',
      mistakes=['Do not use answer fluency as a retrieval metric.', 'Do not count a passage beyond the context budget as retrieved evidence.', 'Do not tune on the final evaluation set repeatedly.'],
      related=['retrieval-ai/retrieval-recall-and-reranking','retrieval-ai/evidence-bound-answer-and-abstention','retrieval-ai/chunk-identity-and-context-boundaries','prompt-engineering/evaluation-data-leakage']),
 dict(path='retrieval-ai/prompt-injection-and-tool-boundary', title='Retrieved text as untrusted data: keep instructions and tools separate',
      summary='A retrieved passage may contain instructions aimed at the model; its text must not gain authority to change tool use or access policy.',
      sections=[
       ('Name the trust levels', 'The user request and application instructions have different roles from handbook passages. A document can contain an imperative such as “ignore prior rules” as ordinary data, or as an attack planted by someone who edits the corpus. Do not promote that text into system instructions. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Permission checks]] must happen before a passage reaches any model or tool.'),
       ('Restrict actions outside language', 'A prompt can ask a model to ignore a passage, but prompt wording alone cannot enforce authorization or tool limits. Give the answer component only read capabilities needed for its task. Validate tool arguments and destination allowlists in application code. A retrieved passage should never decide which user, tenant or document scope the server searches.'),
       ('Preserve suspicious evidence safely', 'Log passage ID and a bounded diagnostic reason when hostile instructions are detected; avoid echoing private text into broad logs. Keep an incident fixture with a forged policy update and a request to expose another department’s handbook. The expected result is no unauthorized retrieval or action, regardless of answer fluency.'),
       ('Test in stages', 'Run permission tests with retrieval alone, then answer tests with a hostile passage inserted, then tool-call tests under a constrained stub. A system that simply refuses every question is not useful; measure legitimate answer completion alongside attack resistance. [[retrieval-ai/retrieval-vs-answer-evaluation|Layered evaluation]] prevents one success measure from hiding another failure.')],
      code='def validate_retrieval_request(principal, requested_scope, allowed_scopes):\n    if requested_scope not in allowed_scopes.get(principal, set()):\n        raise PermissionError("retrieval scope is not authorized")\n    return {"principal": principal, "scope": requested_scope}\n\ndef validate_tool_action(action_name, allowed_actions):\n    if action_name not in allowed_actions:\n        raise PermissionError("answer component cannot perform that action")',language='python',
      cost='Authorization lookup is usually O(1) to O(log P) for P policy entries; comprehensive attack testing costs curated fixtures and review time. External tool side effects have far higher cost than a few checks.',
      mistakes=['Do not treat retrieved prose as trusted instructions.', 'Do not rely on a prompt to enforce authorization.', 'Do not grant write tools to a read-only answer feature.'],
      related=['retrieval-ai/corpus-permissions-and-document-lifecycle','retrieval-ai/evidence-bound-answer-and-abstention','retrieval-ai/retrieval-vs-answer-evaluation','prompt-engineering/prompt-injection-red-team']),
 dict(path='retrieval-ai/freshness-deletion-and-index-swap', title='Index freshness: publish complete revisions and remove stale chunks',
      summary='Index updates need a versioned build, deletion handling and an atomic reader switch so answers never mix policy generations.',
      sections=[
       ('Build a candidate generation', 'When the support handbook changes, parse and index the new revision under a candidate generation. Keep the current generation serving while the candidate is incomplete. Validate document counts, active revisions, permissions and representative retrieval questions, then switch the reader pointer. [[data-engineering/backfill-publication-boundary|Backfill publication]] uses the same complete-before-visible idea.'),
       ('Propagate deletion', 'A revoked policy can remain in an embedding index, lexical index or answer cache. Track document-to-chunk lineage so removal reaches every derived store. If a deletion cannot be completed promptly, deny access to the document ID at query time while reindexing catches up. Do not rely on an old vector disappearing merely because its source file was removed.'),
       ('Choose freshness guarantees', 'Record ingestion lag, last successful index generation and maximum acceptable age. An urgent policy correction may require a synchronous block on old content; a routine edit may tolerate a short lag. Communicate when the answer feature is stale or unavailable rather than silently serving a superseded rule. [[retrieval-ai/evidence-bound-answer-and-abstention|No-answer behavior]] can be safer during a gap.'),
       ('Drill a partial failure', 'Fail one document during candidate indexing. The current generation should remain visible, the candidate should not publish, and an operator should see the rejected document and reason. Then revoke a permission and confirm query-time filtering blocks the old chunk before the next full rebuild.')],
      code='def publish_index(candidate, current_pointer, required_documents):\n    if (set(candidate["document_ids"]) != set(required_documents)\n            or len(candidate["document_ids"]) != len(set(candidate["document_ids"]))):\n        raise ValueError("index generation is incomplete")\n    if candidate["failed_chunks"] or not candidate["permission_checks_passed"]:\n        raise ValueError("index generation failed checks")\n    previous_generation = current_pointer.read()\n    if not current_pointer.compare_and_swap(previous_generation, candidate["generation_id"]):\n        raise RuntimeError("index pointer changed during publish")\n    return previous_generation',language='python',
      cost='A full rebuild reads O(C) corpus content and creates O(K) chunks, embeddings and index entries. A pointer switch is cheap; storing two generations temporarily increases storage and build cost.',
      mistakes=['Do not expose a partial candidate index.', 'Do not forget answer caches when deleting content.', 'Do not wait for full reindexing to revoke access.'],
      related=['retrieval-ai/corpus-permissions-and-document-lifecycle','retrieval-ai/chunk-identity-and-context-boundaries','retrieval-ai/support-policy-answer-project','data-engineering/backfill-publication-boundary']),
 dict(path='retrieval-ai/support-policy-answer-project', title='Project: answer support-policy questions with permission-aware evidence',
      summary='Build a small internal policy answer system that keeps revisions and permissions intact, measures retrieval, and abstains when evidence is missing.',
      sections=[
       ('Prepare the corpus', 'Create a fixture of current, retired and restricted handbook pages. Include two policies with similar headings and one exception sentence. Record document ID, revision, effective window and allowed department scope. Chunk without separating the exception from its rule. [[retrieval-ai/corpus-permissions-and-document-lifecycle|The corpus contract]] and [[retrieval-ai/chunk-identity-and-context-boundaries|chunk identity]] are required deliverables.'),
       ('Build and judge retrieval', 'Implement a lexical baseline and a second retrieval signal. Create judged questions for exact code, paraphrase, two-section and no-answer cases. Report required-passage recall at the context budget, not only an end-to-end answer score. A restricted page should never appear for an unauthorized principal. [[retrieval-ai/retrieval-vs-answer-evaluation|Layered evaluation]] guides the report.'),
       ('Constrain the answer', 'Return an answer state and internal evidence IDs. Reject a claim without an available supporting passage and abstain on stale or conflicting policy. Add a hostile passage that asks for another department’s content; application-level permission and tool checks must still hold. [[retrieval-ai/prompt-injection-and-tool-boundary|Trust boundaries]] are a project acceptance test.'),
       ('Prove update behavior', 'Replace one current policy and delete another. Build a candidate index, deliberately fail one chunk, and show that the old complete generation remains active while revoked access is blocked. Submit fixture, scripts, judged set, metric counts, error ledger, latency budget and failure-case output. A fluent demo answer alone does not complete the exercise.')],
      code='def check_policy_project(answer, retrieved_ids, principal_allowed_ids):\n    evidence_ids = set(answer["evidence_ids"])\n    if not evidence_ids.issubset(set(retrieved_ids)):\n        raise ValueError("answer names unseen evidence")\n    if not evidence_ids.issubset(set(principal_allowed_ids)):\n        raise PermissionError("answer exposes restricted evidence")\n    if answer["status"] == "answered" and not evidence_ids:\n        raise ValueError("unsupported answer")\n    return True',language='python',
      cost='Index construction scales with corpus size and embedding work; each query adds retrieval, optional reranking and generation latency. Keep p95 by stage and temporary storage for index generations in the project report.',
      mistakes=['Do not count restricted passages as valid retrieval hits.', 'Do not accept an answer with evidence IDs absent from its context.', 'Do not publish a partly rebuilt index.'],
      related=['retrieval-ai/corpus-permissions-and-document-lifecycle','retrieval-ai/retrieval-vs-answer-evaluation','retrieval-ai/prompt-injection-and-tool-boundary','retrieval-ai/freshness-deletion-and-index-swap']),
])

lessons.extend([
 dict(path='retrieval-ai/corpus-permissions-and-document-lifecycle', title='Retrieval corpus contracts: identity, permissions and document lifecycle',
      summary='A retrieval system must know which document revision a passage came from and who may read it before indexing begins.',
      sections=[
       ('Treat documents as governed records', 'An internal support handbook may contain policy pages, drafts and retired procedures. Assign stable document ID, revision, effective time, owner and visibility scope. Do not merge a current policy with a superseded one merely because both mention the same product. [[data-engineering/source-contract-and-raw-landing|The source contract]] should preserve an immutable copy for replay and audit.'),
       ('Carry permissions into the index', 'Every indexed passage inherits the document’s authorization policy. Retrieval must filter candidates for the current user before a passage can enter the model context or a cache. Filtering only after generation is too late. Test two employees with different scopes against the same question and confirm neither receives inaccessible passages, even in suggestions or logs.'),
       ('Model deletion and replacement', 'A document removal should invalidate all derived chunks, embeddings and cached answers tied to that revision. An update should produce a new revision, then switch the visible index generation after the new representation is complete. [[retrieval-ai/freshness-deletion-and-index-swap|Index publication]] prevents readers from seeing a half-updated corpus.'),
       ('Audit a complete path', 'For a retrieved passage, trace document ID, revision, chunk ID, permissions and index generation. Add fixtures for an expired policy, revoked access and an identical title in two departments. A keyword match is not evidence that the user may read the result.')],
      code='def visible_passages(passages, principal_scopes, query_time):\n    permitted = []\n    for passage in passages:\n        if not passage.active_from <= query_time:\n            continue\n        if passage.active_until and query_time >= passage.active_until:\n            continue\n        if not passage.allowed_scopes.intersection(principal_scopes):\n            continue\n        permitted.append(passage)\n    return permitted',language='python',
      cost='Filtering K candidate passages is O(K) in this example; indexed permission filters can reduce work earlier. Retaining revisions consumes storage but supports correct deletion, audit and rollback.',
      mistakes=['Do not filter permissions only after generation.', 'Do not leave retired policy chunks searchable.', 'Do not use a title as a stable document identity.'],
      related=['retrieval-ai/chunk-identity-and-context-boundaries','retrieval-ai/freshness-deletion-and-index-swap','retrieval-ai/prompt-injection-and-tool-boundary','data-engineering/source-contract-and-raw-landing']),
 dict(path='retrieval-ai/chunk-identity-and-context-boundaries', title='Chunking documents: preserve section identity and answer boundaries',
      summary='A chunk is a retrievable unit with text, document revision and structural context; its boundaries affect both recall and evidence quality.',
      sections=[
       ('Split on meaning first', 'A policy heading and its exception should remain connected. Blind fixed-character windows may separate the rule from a qualifying sentence and cause a plausible but wrong answer. Prefer section or paragraph boundaries, then enforce a size limit. Carry heading path, document ID, revision and exact offsets. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Document identity]] remains attached to every chunk.'),
       ('Budget overlap deliberately', 'Small chunks improve pinpoint retrieval but can lose context. Large chunks carry context but consume more prompt budget and may rank by unrelated words. Overlap helps at boundaries but creates near duplicates. Count distinct parent documents in the final context so four overlapping chunks do not crowd out another necessary policy.'),
       ('Preserve reproducibility', 'Version parser, normalization, chunking parameters and embedding model together. If extraction from a PDF changes line order, a stable document revision can still produce different chunks. Store a content hash and offset or section identifier for each passage. An answer audit should resolve exactly the passage the model saw, not today’s edited page.'),
       ('Test difficult structure', 'Create a table-like policy with a footnote, a long section and two near-identical headings. Check that the exception stays retrievable with the rule. Verify each chunk respects its input limit and can be mapped back to an exact document revision. [[retrieval-ai/retrieval-recall-and-reranking|Retrieval evaluation]] will show whether the chosen boundaries help real questions.')],
      code='import hashlib\nimport json\n\ndef make_chunk_id(document_id, revision, section_path, text):\n    identity = json.dumps([document_id, revision, section_path, text], ensure_ascii=False)\n    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]\n\nchunk_record = {"chunk_id": make_chunk_id(document_id, revision, section_path, passage_text),\n                "document_id": document_id, "revision": revision,\n                "section": section_path, "text": passage_text}',language='python',
      cost='Parsing and splitting C characters is at least O(C); embedding every chunk adds model cost proportional to chunk count and length. Overlap raises both index size and query-context duplication.',
      mistakes=['Do not separate an exception from the rule it qualifies.', 'Do not lose document revision and offsets when storing chunks.', 'Do not let overlapping chunks monopolize the context.'],
      related=['retrieval-ai/corpus-permissions-and-document-lifecycle','retrieval-ai/retrieval-recall-and-reranking','retrieval-ai/evidence-bound-answer-and-abstention','natural-language-processing/unicode-tokenization-boundary']),
 dict(path='retrieval-ai/retrieval-recall-and-reranking', title='Retrieval design: compare lexical, semantic and reranked candidates',
      summary='A retrieval stage must find relevant permitted passages before generation; different query types need different matching signals.',
      sections=[
       ('Start from query failures', 'A user may ask about a precise invoice code or a paraphrased policy. Exact terms favor lexical search; paraphrases may benefit from semantic similarity. Combine candidates under a fixed budget and rerank them using the actual query. Do not assume one embedding score represents answer correctness. [[retrieval-ai/chunk-identity-and-context-boundaries|Chunk design]] changes what either retriever can find.'),
       ('Filter before ranking output', 'Apply tenant and document permissions at retrieval time. Deduplicate overlapping chunks and cap the number of passages from one parent document. Preserve passage IDs and revisions in the ranked result. A reranker that receives forbidden text has already crossed the access boundary, even if the final response hides it.'),
       ('Measure retrieval directly', 'Build questions with judged supporting passage IDs, including exact-code, paraphrase, multi-section and unanswerable cases. Report recall at the context budget and rank position of the first required passage. A generation failure cannot be diagnosed if retrieval evidence was never measured. [[retrieval-ai/retrieval-vs-answer-evaluation|Layered evaluation]] separates these stages.'),
       ('Control latency', 'Retrieve a broader candidate set cheaply, then rerank a smaller set. Measure lexical, vector and reranking time separately. A higher recall may not justify doubling p95 latency if the answer task rarely needs the added passages; decide under a stated service budget.')],
      code='def combine_candidates(lexical_hits, semantic_hits, allowed_ids, limit=12):\n    if limit <= 0:\n        raise ValueError("candidate limit must be positive")\n    scores, passages = {}, {}\n    for hits in (lexical_hits, semantic_hits):\n        for rank, passage in enumerate(hits, start=1):\n            if passage.chunk_id not in allowed_ids:\n                continue\n            scores[passage.chunk_id] = scores.get(passage.chunk_id, 0) + 1 / (60 + rank)\n            passages[passage.chunk_id] = passage\n    ranked_ids = sorted(scores, key=scores.__getitem__, reverse=True)\n    selected, per_document = [], {}\n    for chunk_id in ranked_ids:\n        passage = passages[chunk_id]\n        if per_document.get(passage.document_id, 0) >= 2:\n            continue\n        selected.append(passage)\n        per_document[passage.document_id] = per_document.get(passage.document_id, 0) + 1\n        if len(selected) == limit:\n            break\n    return selected',language='python',
      cost='Merging L lexical and S semantic hits uses O(L+S) expected hash work, then O(K log K) sorting for K unique hits. Reranking adds query-passage model cost per candidate.',
      mistakes=['Do not infer answer quality from vector similarity alone.', 'Do not expose forbidden text to a reranker.', 'Do not skip retrieval recall checks and blame generation for missing evidence.'],
      related=['retrieval-ai/chunk-identity-and-context-boundaries','retrieval-ai/retrieval-vs-answer-evaluation','retrieval-ai/evidence-bound-answer-and-abstention','retrieval-ai/corpus-permissions-and-document-lifecycle']),
 dict(path='retrieval-ai/evidence-bound-answer-and-abstention', title='Grounded answers: require passage support and a no-answer path',
      summary='An answer should be tied to retrieved permitted passages, with a visible refusal when evidence is missing or conflicting.',
      sections=[
       ('Bound the answer to evidence', 'Pass only the user question and selected permitted passages into the answer step. Ask for claims tied to passage IDs, then verify those IDs were present in the context. A model can still write unsupported claims, so evidence IDs are an audit aid, not automatic proof. [[retrieval-ai/retrieval-vs-answer-evaluation|Answer evaluation]] must inspect claim support separately from retrieval success.'),
       ('Define an abstention rule', 'No passage, stale policy or conflicting versions should trigger a no-answer or escalation path. Do not fill gaps with general model memory when the product promises a handbook answer. A question can be answerable in the world yet absent from this authorized corpus. The system should say that the available material does not establish the answer.'),
       ('Handle conflict explicitly', 'Two active policies may disagree across product regions. Preserve region, effective date and revision metadata in context; ask for missing scope if needed. Do not pick the first high-ranked text and suppress the conflict. [[retrieval-ai/corpus-permissions-and-document-lifecycle|Corpus lifecycle]] should prevent retired rules from masquerading as current ones.'),
       ('Test short unsupported claims', 'Create a question whose top chunk mentions the topic but not the requested fee, and ensure the answer abstains instead of inventing a number. Add one question requiring two sections; both passage IDs should be represented. Inspect whether the final text makes a stronger claim than the cited passages support.')],
      code='def validate_answer_evidence(answer, retrieved_chunk_ids):\n    cited = set(answer["evidence_ids"])\n    available = set(retrieved_chunk_ids)\n    if not cited and answer["status"] == "answered":\n        raise ValueError("answered without evidence")\n    if not cited.issubset(available):\n        raise ValueError("answer cites unavailable passage")\n    if answer["status"] not in ("answered", "no-answer", "needs-scope"):\n        raise ValueError("unknown answer state")\n    return True',language='python',
      cost='Checking E cited IDs against K retrieved IDs is O(E+K) time and O(K) memory. Generation usually dominates latency and token cost; abstention saves unsupported downstream decisions.',
      mistakes=['Do not treat a cited passage ID as proof that every claim is supported.', 'Do not answer from general memory when the corpus lacks evidence.', 'Do not hide conflicting active policies.'],
      related=['retrieval-ai/retrieval-vs-answer-evaluation','retrieval-ai/retrieval-recall-and-reranking','retrieval-ai/prompt-injection-and-tool-boundary','retrieval-ai/support-policy-answer-project']),
])

assert len(lessons) == 16
assert len({item['path'] for item in lessons}) == len(lessons)
titles = {path: row['title'] for path, row in by_path.items()}
titles.update({item['path']: item['title'] for item in lessons})

def links(paths):
    return '<ul>' + ''.join('<li><a href="/' + path + '">' + html.escape(titles[path]) + '</a></li>' for path in paths) + '</ul>'

def article_body(item):
    parts = ['<p>' + html.escape(item['summary']) + '</p>']
    for heading, paragraph in item['sections']:
        parts.extend(('<h2>' + html.escape(heading) + '</h2>', '<p>' + prose(paragraph) + '</p>'))
    parts.extend(('<h2>Implementation</h2>', '<pre><code class="language-' + item['language'] + '">' + html.escape(item['code']) + '</code></pre>',
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
 'applied-statistics': {
     'root':'applied-statistics/applied-statistics-tutorial', 'name':'Applied Statistics',
     'summary':'Make defensible data decisions by defining populations, measuring uncertainty and planning experiments before reading results.',
     'groups':[('Population and variation', ['population-estimand-and-sampling-frame','distribution-quantiles-and-outlier-policy','cluster-bootstrap-and-standard-error','confidence-interval-coverage']),
               ('Testing and decisions', ['hypothesis-test-and-effect-size','randomization-unit-and-experiment-design','multiple-comparisons-and-stopping-rule'])],
     'project':'receipt-review-experiment-project',
     'foundation':['data-science/data-science-for-beginners','machine-learning/machine-learning-tutorial']},
 'retrieval-ai': {
     'root':'retrieval-ai/retrieval-ai-tutorial', 'name':'Retrieval-Based AI',
     'summary':'Build permission-aware document answers with versioned chunks, measured retrieval, grounded responses and safe index updates.',
     'groups':[('Corpus and retrieval', ['corpus-permissions-and-document-lifecycle','chunk-identity-and-context-boundaries','retrieval-recall-and-reranking']),
               ('Answers and operations', ['evidence-bound-answer-and-abstention','retrieval-vs-answer-evaluation','prompt-injection-and-tool-boundary','freshness-deletion-and-index-swap'])],
     'project':'support-policy-answer-project',
     'foundation':['natural-language-processing/nlp-tutorial','prompt-engineering/prompt-engineering']},
}

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
                + links(config['foundation']) + '<h2>Practice</h2>' + links([project_hub_path]))
    hub = make_row(root_path, titles[root_path], config['summary'], hub_body,
                   'subject', slug, root_path, root_path, 8200 if slug == 'applied-statistics' else 8300,
                   {'modules':modules, 'resource_tabs':tabs})
    project_body = ('<p>Apply the ' + html.escape(config['name']) + ' curriculum to a checked project.</p>'
                    '<h2>Project brief</h2>' + links([project_path])
                    + '<h2>Required concepts</h2>' + links(all_paths[:-1])
                    + '<h2>Completion standard</h2><p>Submit runnable work, a data or document manifest, measured results and failure-case evidence.</p>')
    project_hub = make_row(project_hub_path, titles[project_hub_path],
                           'A checked project for the ' + config['name'] + ' curriculum.', project_body,
                           'subject', slug + '-project', project_hub_path, root_path,
                           8201 if slug == 'applied-statistics' else 8301,
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
                       8400 + index,
                       {'kind':'project' if is_project else 'tutorial',
                        'reading_minutes':max(5, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                        'author_path':'authors/aitrove-editorial',
                        'verification_suite':'Editorial and syntax review; project inputs needed for runtime checks',
                        'related':[{'path':path,'title':titles[path]} for path in item['related']]})
    rows.append(article)
    by_path[item['path']] = article

for source, target in [
    ('data-science/metric-denominator-and-cohort','applied-statistics/population-estimand-and-sampling-frame'),
    ('data-science/bootstrap-interval-interpretation','applied-statistics/cluster-bootstrap-and-standard-error'),
    ('machine-learning/group-and-time-validation','applied-statistics/randomization-unit-and-experiment-design'),
    ('machine-learning/decision-threshold-and-cost','applied-statistics/hypothesis-test-and-effect-size'),
    ('natural-language-processing/text-serving-contract','retrieval-ai/corpus-permissions-and-document-lifecycle'),
    ('prompt-engineering/prompt-injection-red-team','retrieval-ai/prompt-injection-and-tool-boundary'),
    ('data-engineering/backfill-publication-boundary','retrieval-ai/freshness-deletion-and-index-swap'),
]:
    row = by_path[source]
    anchor = '<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in row['body']:
        row['body'] += anchor
        row['data']['related'].append({'path':target,'title':titles[target]})
        row['updated_at'] = stamp

assert len({row['path'] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_articles':len(lessons), 'new_subject_hubs':4, 'crosslinks_from_existing':7}))
