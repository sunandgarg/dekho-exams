"""Add original synthetic-control and effect-transfer Data Science lessons."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
slugs = (
    'synthetic-control-donor-eligibility-and-pre-fit',
    'synthetic-control-weight-search-and-prediction',
    'synthetic-control-placebo-and-fit-ratio',
    'synthetic-control-donor-and-window-sensitivity',
    'target-population-standardization-for-branch-effects',
    'single-branch-policy-transfer-review-project',
)
new_paths = {'data-science/' + slug for slug in slugs}
rows = [row for row in rows if row['path'] not in new_paths]
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
lessons = []

def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='data-science/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))

add('synthetic-control-donor-eligibility-and-pre-fit',
    'Synthetic-control donor eligibility and pre-fit',
    'A synthetic control builds a comparison trajectory from untreated units, but the donor set and the quality of pre-intervention fit must be audited before a post-intervention gap is interpreted.', [
    ('Define the treated unit and clock', 'Suppose one service branch begins a routing policy in July. The outcome is the monthly share of tickets that miss a service deadline, with an unchanged denominator rule. Freeze January through June as the fitting window and July through September as the evaluation window. The treatment unit is the entire branch. A neighboring branch that starts training in June is already contaminated even if its feature flag remains off. [[data-science/branch-month-panel-and-rollout-clock|The rollout clock]] should record training, launch and outcome dates separately.'),
    ('Make donor eligibility a design decision', 'Candidate branches must remain untreated throughout the evaluation window and be outside plausible spillover paths. They also need the same outcome definition, complete pre-period records and no branch-specific reporting migration. Similar-looking outcome lines alone do not make a donor valid. A branch with a common queue shared with the treated branch may inherit the policy effect; using it as a donor would pull the counterfactual toward the observed outcome. [[data-science/spillover-aware-comparison-pool|The exposure screen]] gives a practical exclusion rule.'),
    ('Look at the trajectory before optimization', 'Plot or inspect each candidate and the treated branch over the full fitting window. If the treated branch has a sharp pre-policy jump that no convex combination of donors can reproduce, a tiny post gap is not reassuring. A stable level match with a different slope is also weak. The pre-period should contain enough operational variation to test tracking, not merely two convenient points.'),
    ('Use explicit support checks', 'The implementation below checks a frozen eligibility record, a complete monthly grid and a common cutoff. It refuses a donor with treatment, known indirect exposure or missing months. It does not decide whether unmeasured shocks are shared. Preserve the exclusion reasons; donor selection after seeing the post-policy result turns a design choice into an outcome search. [[data-science/synthetic-control-weight-search-and-prediction|Weight fitting]] begins only after this gate.'),
    ('Know what the design can and cannot answer', 'The post-policy difference compares one branch with a modeled untreated path. A causal claim still needs no anticipation, no interference into donors and a credible claim that the donor combination would have tracked this branch without the policy. The fitted pre-period is evidence about that claim, not proof. With a single treated branch, the result concerns that branch and time span; moving to a new branch requires a separate [[data-science/target-population-standardization-for-branch-effects|transfer argument]].')],
    '''def eligible_donors(monthly_rates, donor_status, pre_months, post_months):
    if not pre_months or not post_months or max(pre_months) >= min(post_months):
        raise ValueError("invalid intervention clock")
    required = set(pre_months) | set(post_months)
    approved = []
    rejected = {}
    for branch, status in donor_status.items():
        reasons = []
        if status["treated"] or status["indirect_exposure"]:
            reasons.append("policy exposure")
        if status["definition_changed"]:
            reasons.append("outcome definition changed")
        if any((branch, month) not in monthly_rates for month in required):
            reasons.append("incomplete monthly grid")
        if reasons:
            rejected[branch] = reasons
        else:
            approved.append(branch)
    return sorted(approved), rejected

rates = {(branch, month): .14 + month / 100
         for branch in ("West", "South", "Harbor") for month in range(1, 10)}
status = {"West": {"treated": False, "indirect_exposure": False,
                   "definition_changed": False},
          "South": {"treated": False, "indirect_exposure": True,
                    "definition_changed": False},
          "Harbor": {"treated": False, "indirect_exposure": False,
                     "definition_changed": False}}
approved, rejected = eligible_donors(rates, status, range(1, 7), range(7, 10))
assert approved == ["Harbor", "West"]
assert rejected["South"] == ["policy exposure"]''',
    'For D candidates and T months, membership checks cost O(D × T) expected time and O(D) output space beyond the input panel. The real cost is collecting treatment, queue and measurement histories; a fast scan cannot validate an undocumented donor.',
    ['Do not choose donors after seeing the estimated post-policy gap.', 'Do not use a branch exposed through a shared queue as an untreated donor.', 'Do not treat close pre-period fit as proof of the missing counterfactual.'],
    ['data-science/synthetic-control-weight-search-and-prediction','data-science/synthetic-control-placebo-and-fit-ratio','data-science/spillover-aware-comparison-pool','data-science/single-branch-policy-transfer-review-project'])

add('synthetic-control-weight-search-and-prediction',
    'Synthetic-control weight search and prediction',
    'Synthetic-control weights are nonnegative and sum to one; they are fitted on pre-intervention data and then held fixed to predict the untreated post-intervention path.', [
    ('Fit a path, not an impressive result', 'A branch starts the routing policy after June. The treated branch has a six-month breach-rate series, and two eligible donors have the same six months plus three later months. For each candidate weight, form a weighted donor rate in every pre-policy month and score its squared tracking error. The code searches weights from zero to one in steps of 0.01. It never consults the treated branch’s post-policy values while selecting weights. [[data-science/synthetic-control-donor-eligibility-and-pre-fit|Donor eligibility]] must be settled first.'),
    ('Understand the convex constraint', 'Two donor weights that are nonnegative and sum to one keep the synthetic path inside the donors’ monthly range. That avoids extrapolation through negative weights, but it may leave poor fit when the treated branch sits outside the donor envelope. Adding more donors can improve apparent fit while increasing design sensitivity. A large donor pool with a short pre-period can produce a fragile match even under the convex rule.'),
    ('Separate the gap from the causal claim', 'Once weights are frozen, predict each post-policy month from donor outcomes and calculate observed minus synthetic. A negative gap means fewer breaches than predicted under the chosen construction. It is not automatically a policy effect: an unrelated staffing change or a donor-side shock could create the same pattern. Retain the full monthly gap sequence and the pre-fit error. A single averaged number hides reversals and delayed effects.'),
    ('Keep preprocessing outside the outcome window', 'If seasonality, ticket mix or a reporting change matters, define transformations using pre-policy information and apply them consistently. Do not normalize by the full-series mean; that leaks post-policy information into the fit. Do not fill missing pre-period rates with post-period values. Where donor outcomes are counts and denominators differ, decide whether the target is a rate or a count before fitting.'),
    ('Treat the grid search as a teaching implementation', 'The two-donor search below makes the constraint and held-out prediction visible. A larger production design needs a constrained optimizer, a clearly specified feature or outcome weighting rule and a reproducible tie-break. Document the software inputs and the fit window. [[data-science/synthetic-control-placebo-and-fit-ratio|Placebo comparisons]] and [[data-science/synthetic-control-donor-and-window-sensitivity|sensitivity reruns]] can then probe whether the gap is distinctive or design-dependent.')],
    '''def fit_two_donor_control(treated_pre, donor_pre, donor_post):
    if len(donor_pre) != 2 or set(donor_pre) != set(donor_post):
        raise ValueError("exactly two aligned donors required")
    names = sorted(donor_pre)
    if not treated_pre or any(len(donor_pre[name]) != len(treated_pre)
                              for name in names):
        raise ValueError("incomplete pre-period")
    if len({len(donor_post[name]) for name in names}) != 1:
        raise ValueError("misaligned post-period")
    candidates = []
    for step in range(101):
        first_weight = step / 100
        weights = {names[0]: first_weight, names[1]: 1 - first_weight}
        predicted_pre = [sum(weights[name] * donor_pre[name][month]
                             for name in names) for month in range(len(treated_pre))]
        mse = sum((observed - predicted) ** 2
                  for observed, predicted in zip(treated_pre, predicted_pre)) / len(treated_pre)
        candidates.append((mse, step, weights))
    mse, _, weights = min(candidates)
    predicted_post = [sum(weights[name] * donor_post[name][month]
                          for name in names)
                      for month in range(len(donor_post[names[0]]))]
    return weights, mse, predicted_post

treated_pre = [.21, .20, .18, .19]
donor_pre = {"West": [.18, .18, .17, .17],
             "South": [.24, .22, .19, .21]}
donor_post = {"West": [.19, .18], "South": [.22, .21]}
weights, pre_mse, expected_without_policy = fit_two_donor_control(
    treated_pre, donor_pre, donor_post)
post_gaps = [observed - expected for observed, expected
             in zip([.13, .12], expected_without_policy)]
assert abs(sum(weights.values()) - 1) < 1e-12
assert all(weight >= 0 for weight in weights.values())
assert len(post_gaps) == 2 and all(gap < 0 for gap in post_gaps)''',
    'With G candidate weights, P pre-period months, Q post-period months and two donors, grid search costs O(G × P + Q) time and O(G + Q) space here. Full constrained optimization with D donors has a different solver cost; storing and checking the panel can dominate either algorithm.',
    ['Do not use treated post-policy outcomes to choose weights or scaling.', 'Do not interpret a negative gap as causal without reviewing concurrent shocks.', 'Do not hide poor pre-fit behind a post-period average.'],
    ['data-science/synthetic-control-donor-eligibility-and-pre-fit','data-science/synthetic-control-placebo-and-fit-ratio','data-science/synthetic-control-donor-and-window-sensitivity','data-science/single-branch-policy-transfer-review-project'])

add('synthetic-control-placebo-and-fit-ratio',
    'Synthetic-control placebos and fit ratios',
    'A placebo-in-space check repeats a fixed synthetic-control procedure on untreated units and compares post-period departures only among units with usable pre-period fit.', [
    ('Repeat the procedure, not only the arithmetic', 'For each eligible donor branch, pretend it received the policy at the real intervention date. Remove that branch from its own donor pool, refit weights using only its pre-policy data and calculate its post-policy gap. The originally treated branch should not be smuggled into placebo donor pools after treatment. This turns the placebo into a test of whether the observed gap is unusual under the same workflow, rather than a comparison with convenient static lines. [[data-science/synthetic-control-weight-search-and-prediction|The fit procedure]] must be identical across runs.'),
    ('Compare pre and post error on the same scale', 'Root mean squared prediction error, or RMSPE, summarizes the size of a gap sequence. The post/pre RMSPE ratio highlights units that track well before the policy date and depart afterward. A branch with almost zero pre-error can have an enormous ratio from a small absolute post shift, so inspect both errors and the actual outcome scale. Also compare the treated branch’s pre-fit to placebo pre-fits before ranking ratios.'),
    ('Gate poor matches before ranking', 'The teaching code accepts precomputed observed and predicted paths from independently refitted runs. It filters placebos whose pre-RMSPE exceeds twice the treated unit’s pre-RMSPE. That threshold is a disclosed diagnostic rule, not a universal scientific cutoff. If few placebos remain, the rank is coarse and sensitive to exclusions. Report the total candidate count, accepted count and every exclusion, including treatment or spillover in a placebo branch.'),
    ('Read the rank with restraint', 'An observed ratio larger than every accepted placebo ratio suggests the treated branch is unusual in this donor set. It is not automatically a randomization p-value: branches may not have been exchangeably assigned treatment. Geography, volume and management selection can affect which branch received the policy and how it evolves. A placebo ranking cannot rescue a poor donor design. [[data-science/assignment-aware-permutation-test-for-branches|Assignment-aware tests]] need an actual assignment mechanism.'),
    ('Inspect patterns, not just one statistic', 'Draw or list the treated and placebo gaps over time. A sudden treated departure at launch supports a different story from a divergence already underway during training. Check a fake intervention date in the true pre-period as another diagnostic, but keep that date outside anticipation. [[data-science/negative-control-and-placebo-rollout-checks|Negative controls]] probe a different failure route; neither check validates every assumption.')],
    '''from math import sqrt

def rmspe(observed, predicted):
    if not observed or len(observed) != len(predicted):
        raise ValueError("aligned nonempty paths required")
    return sqrt(sum((actual - expected) ** 2
                    for actual, expected in zip(observed, predicted)) / len(observed))

def comparable_fit_ratios(refitted_paths, treated_branch, fit_limit=2.0):
    if treated_branch not in refitted_paths or fit_limit <= 0:
        raise ValueError("invalid treated branch or limit")
    errors = {}
    for branch, paths in refitted_paths.items():
        pre = rmspe(paths["pre_observed"], paths["pre_predicted"])
        post = rmspe(paths["post_observed"], paths["post_predicted"])
        if pre == 0:
            raise ValueError("zero pre-fit error needs separate handling")
        errors[branch] = (pre, post)
    treated_pre = errors[treated_branch][0]
    accepted = {branch: post / pre for branch, (pre, post) in errors.items()
                if branch == treated_branch or pre <= fit_limit * treated_pre}
    rejected = sorted(set(errors) - set(accepted))
    return accepted, rejected

paths = {"North": {"pre_observed": [.20, .19], "pre_predicted": [.19, .18],
                   "post_observed": [.12, .11], "post_predicted": [.19, .18]},
         "West": {"pre_observed": [.16, .17], "pre_predicted": [.15, .16],
                  "post_observed": [.18, .19], "post_predicted": [.17, .18]},
         "Harbor": {"pre_observed": [.22, .23], "pre_predicted": [.18, .19],
                    "post_observed": [.24, .25], "post_predicted": [.20, .21]}}
ratios, rejected = comparable_fit_ratios(paths, "North")
assert set(ratios) == {"North", "West"} and rejected == ["Harbor"]
assert ratios["North"] > ratios["West"]''',
    'Given U independently refitted units and T observations each, computing diagnostics is O(U × T) time and O(U) space. Re-fitting each unit is much more costly and can change the donor pool; the displayed function deliberately starts after those fits and cannot substitute for them.',
    ['Do not call an observational placebo rank an exact randomization p-value.', 'Do not compare a poorly fitted placebo with a well-fitted treated unit without disclosing pre-fit.', 'Do not reuse treated post-policy outcomes as placebo donors.'],
    ['data-science/synthetic-control-weight-search-and-prediction','data-science/synthetic-control-donor-and-window-sensitivity','data-science/negative-control-and-placebo-rollout-checks','data-science/single-branch-policy-transfer-review-project'])

add('synthetic-control-donor-and-window-sensitivity',
    'Synthetic-control donor and window sensitivity',
    'A sensitivity audit repeats the full pre-period fit after defensible donor or time-window changes and reports how much the estimated post-policy gap moves.', [
    ('Prespecify plausible perturbations', 'One donor may have changed staffing, another may be unusually large, and the earliest months may use a different ticket classification. Freeze a short list of defensible reruns before reading their post-policy effects: drop each major donor in turn, start the fit two months later, and exclude a known outage month. Record the reason for each change. A post hoc search for the most favorable gap is selection, not sensitivity analysis. [[data-science/synthetic-control-donor-eligibility-and-pre-fit|The donor gate]] supplies documented exclusion reasons.'),
    ('Refit weights on every rerun', 'Dropping a donor while retaining the old weights leaves a weight vector that no longer sums to one. Changing the pre-period while retaining weights ignores the alternative design. Rebuild the eligible donor set, refit under the same constraint and recompute both pre-error and post gap. For a two-donor teaching model, deleting one donor leaves a single-donor comparator; that result can be informative but may fit poorly.'),
    ('Report fit beside effect', 'A gap can grow when pre-fit deteriorates. The code below records one candidate result per declared design and rejects any design lacking a fitted pre-error or post gap. The displayed range is a design-sensitivity range, not a confidence interval and not a probability statement. If only the poorly fitting designs show a strong effect, the operational conclusion should be narrower. [[data-science/synthetic-control-placebo-and-fit-ratio|The placebo lesson]] discusses comparable fit across units.'),
    ('Distinguish instability from invalidity', 'A donor deletion that changes the sign may identify a donor-specific shock, a narrow donor envelope or a branch that carries most of the pre-fit. Investigate operations and measurement history; do not automatically discard the offending design. Conversely, stable signs across a small handpicked set do not establish causality. Shared shocks, anticipation and interference may affect every rerun in the same direction.'),
    ('Tie the window to the rollout process', 'A branch may prepare staff before the formal launch. Treating those preparation months as untreated fitting data can bend weights toward an already affected trajectory. Prefer the last clearly unexposed month as the cutoff, then test reasonable earlier cutoffs. An unusually short pre-period reduces the evidence that a donor mix tracks the branch. [[data-science/event-time-pretrend-and-support-audit|Event-time support]] helps locate such problems.')],
    '''def summarize_design_sensitivity(design_results, maximum_pre_error):
    if maximum_pre_error <= 0 or not design_results:
        raise ValueError("invalid design audit")
    accepted = {}
    rejected = {}
    for design_name, result in design_results.items():
        pre_error = result["pre_rmspe"]
        post_gap = result["mean_post_gap"]
        if pre_error < 0:
            raise ValueError("negative fit error")
        if pre_error > maximum_pre_error:
            rejected[design_name] = "pre-fit exceeds declared limit"
        else:
            accepted[design_name] = post_gap
    if not accepted:
        raise ValueError("no design has acceptable pre-fit")
    return min(accepted.values()), max(accepted.values()), rejected

# Each row is the output of a complete, separate constrained refit.
reruns = {"all_eligible": {"pre_rmspe": .008, "mean_post_gap": -.052},
          "drop_west": {"pre_rmspe": .011, "mean_post_gap": -.041},
          "later_start": {"pre_rmspe": .009, "mean_post_gap": -.047},
          "drop_harbor": {"pre_rmspe": .026, "mean_post_gap": -.018}}
low, high, excluded = summarize_design_sensitivity(reruns, .015)
assert (low, high) == (-.052, -.041)
assert excluded == {"drop_harbor": "pre-fit exceeds declared limit"}''',
    'Summarizing R completed reruns is O(R) time and O(R) output space. The expensive operation is R independent refits, each over its donor count and pre-period length. Predefining a small audit set controls both compute and the risk of selecting a pleasing result.',
    ['Do not remove a donor and reuse weights fitted with that donor present.', 'Do not describe the rerun range as a confidence interval.', 'Do not hide designs that failed a declared pre-fit gate.'],
    ['data-science/synthetic-control-donor-eligibility-and-pre-fit','data-science/synthetic-control-weight-search-and-prediction','data-science/synthetic-control-placebo-and-fit-ratio','data-science/single-branch-policy-transfer-review-project'])

add('target-population-standardization-for-branch-effects',
    'Target-population standardization for branch effects',
    'Standardization transports stratum-specific effect estimates to a target population by weighting them with the target population’s stratum shares, provided every target stratum has credible effect support.', [
    ('Name the target before averaging', 'A policy effect measured across mostly high-volume urban branches may be used to plan a rollout dominated by smaller regional branches. The source average answers the source-mix question. The target decision needs an average under the target mix. Write down the intended branches, calendar period, outcome definition and intervention version before applying weights. [[data-science/sampling-frame-and-coverage-error|Sampling-frame coverage]] matters: branches missing from the target roster cannot enter the calculation.'),
    ('Partition on effect modifiers', 'Use pre-policy attributes that plausibly change the effect, such as branch volume and queue architecture, rather than arbitrary labels. Estimate an effect within every required stratum, then multiply by the target share and sum. In the teaching fixture, urban branches have an estimated breach-rate change of -0.05, regional branches -0.02, and the target mix is 30% urban and 70% regional. The transported average is -0.029, not the source average of -0.044 when the source mix is 80% urban.'),
    ('Distinguish sampling weights from causal identification', 'The arithmetic cannot repair a biased stratum effect. Within each stratum, the original causal design must still support an effect, and the treatment and outcome must mean the same thing in source and target. Transport also assumes the chosen strata capture the effect modifiers that differ between populations. If unrecorded queue design changes the effect, reweighting urban and regional shares alone may fail. [[causal-inference/overlap-and-weighting-diagnostics|Overlap diagnostics]] address a related support problem.'),
    ('Make missing support a hard stop', 'If the target includes remote branches but the source study has none, assigning a remote effect from an urban estimate is extrapolation. The code raises on an unsupported target stratum rather than silently renormalizing the observed strata. Small strata with noisy estimates need uncertainty carried through the weighted sum; the fixture only demonstrates point-estimate arithmetic. An uncertainty interval needs source-estimate covariance or a resampling design that preserves the study units.'),
    ('Do not transfer a single-unit effect by arithmetic alone', 'A synthetic-control study of one branch supplies one branch-specific contrast, not stratum effects for urban and regional branches. You cannot feed that lone gap into both cells and claim population transport. Gather effects or a defended model across branches, or label the projection a scenario with explicit assumptions. [[data-science/single-branch-policy-transfer-review-project|The review project]] separates the local finding from the rollout decision.')],
    '''def standardized_effect(effect_by_stratum, target_share):
    if not target_share or any(share < 0 for share in target_share.values()):
        raise ValueError("invalid target shares")
    if abs(sum(target_share.values()) - 1) > 1e-12:
        raise ValueError("target shares must sum to one")
    unsupported = {stratum for stratum, share in target_share.items()
                   if share > 0 and stratum not in effect_by_stratum}
    if unsupported:
        raise ValueError("unsupported target strata: " + ", ".join(sorted(unsupported)))
    return sum(target_share[stratum] * effect_by_stratum[stratum]
               for stratum in target_share if target_share[stratum] > 0)

estimated_effects = {"urban": -.05, "regional": -.02}
source_mix = {"urban": .80, "regional": .20}
target_mix = {"urban": .30, "regional": .70}
source_average = standardized_effect(estimated_effects, source_mix)
target_average = standardized_effect(estimated_effects, target_mix)
assert abs(source_average - (-.044)) < 1e-12
assert abs(target_average - (-.029)) < 1e-12''',
    'For S strata, validation and the weighted sum cost O(S) expected time and O(S) space for the support set. Estimating defensible stratum effects, tracking target composition and propagating uncertainty are the substantial costs.',
    ['Do not treat reweighting as a cure for confounded stratum effects.', 'Do not renormalize away a target stratum with no source support.', 'Do not turn one treated branch’s effect into a population estimate by relabeling it.'],
    ['data-science/sampling-frame-and-coverage-error','data-science/stratified-sampling-and-design-weights','data-science/subgroup-distribution-and-aggregation-reversal','data-science/single-branch-policy-transfer-review-project'])

add('single-branch-policy-transfer-review-project',
    'Project: review a single-branch policy and its transfer',
    'Build a release packet that separates a branch-specific synthetic-control result from a decision to extend the policy to a differently composed branch population.', [
    ('Frame two decisions', 'The first question is whether the July routing policy changed North’s breach rate through September relative to a credible untreated path. The second is whether leadership should expect the same effect in a later group of branches. These are not interchangeable. Record the local unit, launch date, rate numerator and denominator, target branches and intended rollout date before touching weights. [[data-science/branch-month-panel-and-rollout-clock|The panel clock]] supplies the raw timing contract.'),
    ('Assemble the local design', 'Create an eligibility ledger for every potential donor: treatment status, shared-queue exposure, measurement changes and missing months. Freeze donors and fitting dates. Fit nonnegative weights that sum to one using pre-policy outcomes only, then store pre-fit error, monthly post gaps and an average gap. Show the untreated donor trajectories beside the treated branch. A convincing-looking post gap with weak pre-fit remains an unresolved design, not a success. [[data-science/synthetic-control-donor-eligibility-and-pre-fit|The donor gate]] and [[data-science/synthetic-control-weight-search-and-prediction|fit lesson]] define the checks.'),
    ('Run falsification and sensitivity checks', 'Refit placebo units using their own eligible pools, disclose the pre-fit threshold and compare accepted fit ratios. Rerun declared donor exclusions and fitting windows, storing both fit and gap for every result. Keep a log of branches excluded because they share queues with North. A sensitivity range is not an interval estimate. A placebo rank is not a design-based p-value when the routing policy was not randomly assigned. [[data-science/synthetic-control-placebo-and-fit-ratio|Placebos]] and [[data-science/synthetic-control-donor-and-window-sensitivity|reruns]] answer different questions.'),
    ('Create a separate transfer file', 'List the target population’s pre-policy branch mix and the attributes that might alter the policy effect. A single North estimate does not populate every target stratum. Mark the transfer estimate unavailable until defensible effects exist for each target group, or produce a labeled scenario with a stated assumed range. Never present the local synthetic-control gap as a guaranteed network-wide benefit. [[data-science/target-population-standardization-for-branch-effects|Standardization]] applies only after that support exists.'),
    ('Write a decision note with stop conditions', 'The executable gate below confirms that the required artifacts exist and that target strata have effect support. It does not infer causality from booleans. The review note should state whether the local effect is supported, which assumptions remain contestable, and whether transfer is currently estimable. If the donor pool collapses, pre-fit is unacceptable or the target mix includes an unsupported stratum, stop at a descriptive or scenario result. [[data-science/staggered-branch-rollout-audit-project|The broader rollout project]] covers multiple adoption cohorts.')],
    '''def policy_transfer_gate(local_artifacts, target_share, effect_by_stratum):
    required = {"donor_ledger", "frozen_pre_window", "pre_rmspe",
                "monthly_post_gaps", "placebo_log", "sensitivity_log"}
    missing = sorted(required - set(local_artifacts))
    if missing:
        raise ValueError("missing local artifacts: " + ", ".join(missing))
    if local_artifacts["pre_rmspe"] < 0 or not local_artifacts["monthly_post_gaps"]:
        raise ValueError("invalid local fit record")
    if abs(sum(target_share.values()) - 1) > 1e-12:
        raise ValueError("invalid target composition")
    unsupported = sorted(stratum for stratum, share in target_share.items()
                         if share > 0 and stratum not in effect_by_stratum)
    return {"local_packet_complete": True,
            "transfer_estimable": not unsupported,
            "unsupported_target_strata": unsupported}

packet = {"donor_ledger": ["West", "Harbor"], "frozen_pre_window": [1, 6],
          "pre_rmspe": .008, "monthly_post_gaps": [-.05, -.06, -.04],
          "placebo_log": ["West", "Harbor"],
          "sensitivity_log": ["drop_west", "later_start"]}
review = policy_transfer_gate(packet, {"urban": .3, "regional": .7},
                              {"urban": -.05})
assert review == {"local_packet_complete": True,
                  "transfer_estimable": False,
                  "unsupported_target_strata": ["regional"]}''',
    'The gate costs O(A + S) expected time and O(S) output space for A artifact keys and S target strata. Running placebo refits and sensitivity designs is much more expensive. A complete packet only makes the evidence reviewable; it cannot turn unsupported transfer into an estimate.',
    ['Do not equate a complete evidence packet with causal proof.', 'Do not quote a population effect when required target strata have no supported estimates.', 'Do not conceal donor exclusions, failed pre-fit or unfavorable reruns.'],
    ['data-science/synthetic-control-donor-eligibility-and-pre-fit','data-science/synthetic-control-weight-search-and-prediction','data-science/synthetic-control-placebo-and-fit-ratio','data-science/synthetic-control-donor-and-window-sensitivity','data-science/target-population-standardization-for-branch-effects'])

assert len(lessons) == len(new_paths) == 6
titles = {path: row['title'] for path, row in by_path.items()}
titles.update({item['path']: item['title'] for item in lessons})

def prose(value):
    return re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',
                  lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                  html.escape(value))

def links(targets):
    return '<ul>' + ''.join('<li><a href="/' + target + '">' + html.escape(titles[target]) + '</a></li>'
                            for target in targets) + '</ul>'

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
               difficulty='Advanced', tags=['ai-data', 'data-science'], potd_date=None,
               featured=False, sort_order=13700 + index, status='published', published_at=stamp,
               created_at=stamp, updated_at=stamp,
               data={'subject_root':root_path,
                     'section_path':project_hub_path if is_project else root_path,
                     'content_format':'html', 'seo_ready':True,
                     'kind':'project' if is_project else 'tutorial',
                     'reading_minutes':max(5, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                     'author_path':'authors/aitrove-editorial',
                     'verification_suite':'Editorial, code and internal-link checks',
                     'related':[{'path':target, 'title':titles[target]} for target in item['related']]})
    rows.append(row)
    by_path[path] = row

tutorial_paths = ['data-science/' + slug for slug in slugs[:5]]
project_path = 'data-science/' + slugs[-1]
hub = by_path[root_path]
module_title = 'Synthetic controls and effect transfer'
if not any(module['title'] == module_title for module in hub['data']['modules']):
    hub['data']['modules'].insert(-1, {'title':module_title,
                                      'summary':'Audit donors, fitted counterfactuals and the population to which a local effect may apply.',
                                      'lessons':tutorial_paths})
apply_module = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
if project_path not in apply_module['lessons']:
    apply_module['lessons'].append(project_path)
if '<h2>' + module_title + '</h2>' not in hub['body']:
    hub['body'] += '<h2>' + module_title + '</h2>' + links(tutorial_paths)
    hub['body'] += '<h2>Single-branch policy transfer review</h2>' + links([project_path])
hub['updated_at'] = stamp

project_hub = by_path[project_hub_path]
if project_path not in project_hub['data']['modules'][0]['lessons']:
    project_hub['data']['modules'][0]['lessons'].append(project_path)
if '<h2>Single-branch policy transfer review</h2>' not in project_hub['body']:
    project_hub['body'] += '<h2>Single-branch policy transfer review</h2>' + links([project_path])
project_hub['updated_at'] = stamp

for source, target in [
    ('data-science/spillover-aware-comparison-pool', tutorial_paths[0]),
    ('data-science/branch-month-panel-and-rollout-clock', tutorial_paths[1]),
    ('data-science/negative-control-and-placebo-rollout-checks', tutorial_paths[2]),
    ('data-science/leave-one-branch-out-effect-stability', tutorial_paths[3]),
    ('data-science/stratified-sampling-and-design-weights', tutorial_paths[4]),
    ('data-science/small-rollout-and-spillover-review-project', project_path),
]:
    source_row = by_path[source]
    anchor = '<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in source_row['body']:
        source_row['body'] += anchor
        source_row['data'].setdefault('related', []).append({'path':target, 'title':titles[target]})
        source_row['updated_at'] = stamp

assert len({row['path'] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_articles':len(lessons), 'new_projects':1, 'crosslinks_from_existing':6}))
