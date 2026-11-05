"""Add original Data Science lessons on staggered operational rollouts."""
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
    'branch-month-panel-and-rollout-clock',
    'cohort-time-difference-in-differences',
    'event-time-pretrend-and-support-audit',
    'spillover-aware-comparison-pool',
    'branch-cluster-bootstrap-for-rollout-effects',
    'staggered-branch-rollout-audit-project',
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

add('branch-month-panel-and-rollout-clock',
    'Branch-month panels and the rollout clock',
    'A rollout panel contains one outcome per stable unit and period, plus the first period that unit was exposed to the intervention.', [
    ('Choose the observational unit', 'Suppose a support organization introduces a new triage screen branch by branch. The outcome is the monthly rate of cases breaching a service target, measured from cases created in each month. One row represents one branch and one arrival month. Counting activity events instead would give busy branches more rows without changing the number of rollout units. Define the eligible case population, denominator and reporting cutoff before assembling the panel. [[data-science/dataset-grain-and-join-cardinality|Grain and cardinality]] guard the join.'),
    ('Record first exposure, not latest configuration', 'A branch receives the screen on a particular month. Store the first month the branch actually used it and retain the operational evidence for that date. A current configuration flag joined backward makes pre-rollout months appear treated. The teaching audit below derives treatment from a fixed adoption map and rejects a panel row that claims exposure before adoption. If a branch later disables the screen, the absorbing-treatment design no longer fits; record the stop and choose a different analysis.'),
    ('Make the calendar explicit', 'A missing branch-month can mean no eligible cases, delayed ingestion, a closed branch or a broken extraction. Those states are not interchangeable with a measured zero breach rate. The audit requires a complete set of requested periods for each branch; a production dataset can instead document justified exclusions and their effect on the estimand. A branch entering after the study began has no pre-period history for early adoption comparisons. [[data-science/cohort-entry-and-survivorship-bias|Cohort entry]] matters here too.'),
    ('Separate assignment and measurement clocks', 'A rollout approved on the twentieth may first affect arrivals on the twenty-first, while the monthly outcome mixes earlier and later cases. Define whether that month is a partial-exposure transition to exclude, split or model. A status correction entered later should not silently change the historical adoption date. Freeze outcome extracts and policy logs for each analysis version.'),
    ('Check support before estimating', 'Tabulate how many branches adopt in each period, how many never adopt, and which months are available both before and after each adoption. An effect for the earliest cohort three months later needs comparison branches still untreated at that later month. A regression cannot create that support. [[data-science/cohort-time-difference-in-differences|Cohort-time contrasts]] use this panel after it passes the clock checks.')],
    '''def audit_branch_panel(panel_rows, first_use_month, required_months):
    expected = {(branch_id, month)
                for branch_id in first_use_month for month in required_months}
    observed = set()
    for branch_id, month, breach_rate, treated_flag in panel_rows:
        key = (branch_id, month)
        if key in observed or branch_id not in first_use_month:
            raise ValueError("duplicate row or unknown branch")
        if not 0 <= breach_rate <= 1 or treated_flag not in (0, 1):
            raise ValueError("invalid metric or exposure")
        adoption = first_use_month[branch_id]
        expected_flag = int(adoption is not None and month >= adoption)
        if treated_flag != expected_flag:
            raise ValueError("exposure contradicts first-use month")
        observed.add(key)
    if observed != expected:
        raise ValueError("missing or extra branch-month")
    return {"branches": len(first_use_month), "rows": len(panel_rows)}

adoption = {"North": 3, "West": None}
panel = [("North", 1, .18, 0), ("North", 2, .17, 0),
         ("North", 3, .12, 1), ("West", 1, .16, 0),
         ("West", 2, .15, 0), ("West", 3, .15, 0)]
assert audit_branch_panel(panel, adoption, [1, 2, 3]) == {
    "branches": 2, "rows": 6}''',
    'Checking R rows and B branches across M required months costs O(R + B × M) expected time and O(R + B × M) space for key sets. Large panels should enforce a unique branch-period key at ingestion and retain a separate audit of missing cells.',
    ['Do not backfill the current treatment flag into pre-rollout months.', 'Do not turn an absent branch-month into a zero outcome.', 'Do not call a partially exposed transition month fully treated without a stated rule.'],
    ['data-science/cohort-time-difference-in-differences','data-science/event-time-pretrend-and-support-audit','data-science/spillover-aware-comparison-pool','data-science/staggered-branch-rollout-audit-project'])

add('cohort-time-difference-in-differences',
    'Cohort-time difference-in-differences for staggered adoption',
    'A cohort-time contrast compares the change for branches first treated in period g with the change for branches still untreated at the comparison period t.', [
    ('State which effect is requested', 'For branches first using triage in month three, ask how their month-four breach rate changed relative to month two, beyond the change among branches untreated through month four. This is a cohort-three, time-four contrast. Its population is branches that adopted in month three, not every branch that will ever adopt. [[causal-inference/estimand-and-counterfactual-unit|The causal estimand]] fixes whose effect is under discussion.'),
    ('Use a clean comparison pool', 'A never-treated branch can serve as a control. A branch scheduled to adopt in month five can also serve at month four if it has not anticipated treatment and is otherwise comparable. A branch already treated in month two cannot be a month-four untreated control. The code deliberately forms the control set with first use after the post month or no use at all. With a month-two baseline and month-four outcome, treated branches improved four percentage points more than their controls in the fixture.'),
    ('Do not let the formula supply assumptions', 'The observed difference equals a causal effect only under a defendable parallel-trends condition for the untreated potential outcome, along with no anticipation, stable measurement and no relevant spillovers. Pre-period similarities help assess plausibility but cannot prove the unobserved counterfactual. The rollout may target branches whose breach rate was already improving or worsening. Record assignment rules and branch staffing changes before fitting.'),
    ('Avoid one pooled coefficient by habit', 'When adoption dates differ and effects vary by cohort or time since adoption, a simple two-way fixed-effects treatment coefficient can mix comparisons that use already-treated branches as controls. Compute supported cohort-time effects first, inspect them, then specify how to average them using transparent weights. Do not average estimates from different months without stating whether each branch or each eligible case gets equal weight. [[data-science/event-time-pretrend-and-support-audit|Event-time audits]] display how support changes across lags.'),
    ('Treat this code as a ledger calculation', 'The function needs a complete, already validated panel and returns a simple difference of branch means. It does not adjust for covariates, compute standard errors or establish parallel trends. A release analysis needs a maintained staggered-adoption method and uncertainty at the assignment unit. [[data-science/branch-cluster-bootstrap-for-rollout-effects|Cluster resampling]] illustrates why branch-level dependence must be respected.')],
    '''def cohort_time_change(panel, adoption_month, cohort_month, before_month, after_month):
    if not before_month < cohort_month <= after_month:
        raise ValueError("invalid comparison months")
    treated = [branch for branch, month in adoption_month.items()
               if month == cohort_month]
    controls = [branch for branch, month in adoption_month.items()
                if month is None or month > after_month]
    if not treated or not controls:
        raise ValueError("no supported treated or control group")
    def average_change(branches):
        changes = []
        for branch in branches:
            changes.append(panel[(branch, after_month)] - panel[(branch, before_month)])
        return sum(changes) / len(changes)
    return average_change(treated) - average_change(controls)

first_use = {"North": 3, "East": 3, "West": None, "South": 5}
breaches = {("North", 2): .21, ("North", 4): .16,
            ("East", 2): .19, ("East", 4): .15,
            ("West", 2): .17, ("West", 4): .18,
            ("South", 2): .14, ("South", 4): .15}
estimate = cohort_time_change(breaches, first_use, 3, 2, 4)
assert abs(estimate - (-.055)) < 1e-12''',
    'For B branches, selecting groups and computing mean changes is O(B) time and O(B) temporary space. Indexing a raw R-row panel into the dictionary first costs O(R) expected time and space. Statistical uncertainty and assumptions are outside this arithmetic check.',
    ['Do not use an already-treated branch as an untreated comparison.', 'Do not present a cohort-time calculation as causal without examining trends and selection.', 'Do not collapse heterogeneous cohort effects into one coefficient without explicit weights.'],
    ['data-science/branch-month-panel-and-rollout-clock','data-science/event-time-pretrend-and-support-audit','data-science/spillover-aware-comparison-pool','data-science/branch-cluster-bootstrap-for-rollout-effects','data-science/staggered-branch-rollout-audit-project'])

add('event-time-pretrend-and-support-audit',
    'Event-time pre-trends and support for a staggered rollout',
    'An event-time audit aligns periods relative to first treatment and reports which untreated comparisons exist for each lead and lag.', [
    ('Anchor each cohort before treatment', 'For month-four adopters, use month three as a pre-treatment reference. Compare their change from month three to months one and two against branches untreated through the inspected month. A lead at month two is not an effect of triage; it is a diagnostic contrast. In the fixture, treated and comparison branches have matching two-point pre-period changes, so both lead contrasts are zero. That arithmetic does not prove that the next untreated trend would also match.'),
    ('Keep comparison eligibility tied to time', 'A branch adopting in month six can be untreated in month five but not in month seven. Reusing its month-seven observed outcome as an untreated counterfactual contaminates the event-time plot. The code uses never-treated branches for a small transparent fixture; a fuller estimator can use not-yet-treated branches while they remain eligible. Show the number of treated and comparison units beside every plotted point. [[data-science/cohort-time-difference-in-differences|Cohort-time estimation]] defines the post-period contrast.'),
    ('A quiet lead is weak evidence when noise is large', 'An insignificant pre-period test can arise because there are few branches, noisy rates or short history. Do not interpret a wide interval around zero as proof of parallel trends. Report the effect size that pre-period data could reasonably rule out and examine operational reasons that trends might diverge. Conversely, selecting only cohorts with visually flat pre-trends after inspecting the data changes the study population and can bias later estimates.'),
    ('Avoid mechanical event-study regression', 'With staggered rollout and different cohort effects, a conventional two-way fixed-effects lead-lag regression can produce apparent pre-period movements influenced by effects in other cohorts. This lesson computes explicit cohort-level contrasts instead. A production event-study estimator must state its comparison set, reference period, weighting and uncertainty method. A lead can also reflect anticipation when branches train staff before formal launch; keep training dates in the rollout log.'),
    ('Recognize changing support', 'Long lags are often observed only for early adopters, so a month-six event-time point may describe a different mix of branches than a month-one point. Do not read the shape as a single branch trajectory unless the cohort composition is held fixed or shown. [[data-science/spillover-aware-comparison-pool|Spillover checks]] can shrink the eligible control set further. If none remain, mark the lag unsupported rather than extrapolating.')],
    '''def event_time_contrasts(panel, treated_branches, control_branches,
                             adoption_month, reference_month, months):
    if reference_month >= adoption_month or not treated_branches or not control_branches:
        raise ValueError("invalid event-time design")
    def group_mean(branches, month):
        return sum(panel[(branch, month)] for branch in branches) / len(branches)
    baseline_gap = (group_mean(treated_branches, reference_month) -
                    group_mean(control_branches, reference_month))
    return {month - adoption_month:
            (group_mean(treated_branches, month) -
             group_mean(control_branches, month)) - baseline_gap
            for month in months}

rates = {("North", 1): .50, ("North", 2): .48,
         ("North", 3): .46, ("North", 4): .41,
         ("West", 1): .44, ("West", 2): .42,
         ("West", 3): .40, ("West", 4): .38}
contrasts = event_time_contrasts(rates, ["North"], ["West"],
                                 adoption_month=4, reference_month=3,
                                 months=[1, 2, 4])
assert all(abs(contrasts[lead]) < 1e-12 for lead in (-3, -2))
assert abs(contrasts[0] - (-.03)) < 1e-12''',
    'With K requested months and T treated plus C comparison branches, direct lookups cost O(K × (T + C)) time and O(K) output space. A larger study should cache cohort-period means and attach uncertainty plus support counts to every contrast.',
    ['Do not call a nonsignificant lead proof of parallel trends.', 'Do not let already-treated branches become untreated controls at later lags.', 'Do not hide the loss of comparison support at long event times.'],
    ['data-science/branch-month-panel-and-rollout-clock','data-science/cohort-time-difference-in-differences','data-science/spillover-aware-comparison-pool','data-science/branch-cluster-bootstrap-for-rollout-effects','data-science/staggered-branch-rollout-audit-project'])

add('spillover-aware-comparison-pool',
    'Spillover-aware comparison pools for branch rollouts',
    'A branch that has not received an intervention may still be exposed through shared staff, customers or routing, so untreated status alone may not make it a clean control.', [
    ('Map the possible pathways', 'A new triage screen at North may route overflow to West, train agents who later cover West, or change customer behavior across both. A West branch-month marked untreated can then have a changed breach rate. The no-interference assumption behind a simple branch comparison is doubtful. Before estimating, map shared queues, staffing rotations and service regions using records from before rollout. [[causal-inference/confounder-graph-and-covariate-timing|A causal graph]] helps separate baseline relationships from effects of the rollout.'),
    ('Construct an exposure rule', 'The small routine below treats a branch as indirectly exposed in a month if any listed neighbor has already adopted. It excludes those branches from the untreated comparison pool while keeping never-treated, unexposed branches. In the fixture, West is adjacent to a treated North branch and is excluded; South is remote and remains eligible. This is a screening rule, not proof that all spillover paths were captured.'),
    ('Do not erase the population silently', 'Removing exposed controls changes the population represented by the estimate. If most branches share one routing network, there may be no clean controls after rollout. Report counts by direct treatment, indirect exposure and neither at each month. Consider a different estimand, such as the total network effect, or a design with more independent networks. A narrower clean comparison can be more honest than a precise-looking estimate from contaminated controls.'),
    ('Avoid post-treatment geography', 'A customer network rebuilt from traffic after triage launched can already reflect the intervention. Defining neighbors from that network may select controls using post-treatment behavior. Freeze the exposure map using pre-rollout operations and then test sensitivity to plausible wider connections. Shared staffing logs after rollout can be used to audit actual contamination, but should not be quietly used to redefine the original design without documenting the change.'),
    ('Check indirect outcomes separately', 'If West receives overflow, its breach rate may rise. That is an effect of North’s rollout, not evidence that the triage screen failed within North. A direct-effect analysis that excludes West and a separate spillover analysis of West answer different questions. [[data-science/cohort-time-difference-in-differences|Cohort-time contrasts]] should name which one they estimate. Once exposure is network-wide, branch-level confidence intervals may miss correlated shocks; [[data-science/branch-cluster-bootstrap-for-rollout-effects|cluster inference]] needs the correct independent unit.')],
    '''def clean_controls(first_use_month, adjacency, evaluation_month):
    if evaluation_month <= 0:
        raise ValueError("invalid evaluation month")
    branches = set(first_use_month)
    if set(adjacency) != branches:
        raise ValueError("incomplete adjacency map")
    for branch, neighbors in adjacency.items():
        if not set(neighbors) <= branches or branch in neighbors:
            raise ValueError("invalid neighbor list")
    directly_treated = {
        branch for branch, first_month in first_use_month.items()
        if first_month is not None and first_month <= evaluation_month}
    indirectly_exposed = {
        branch for branch, neighbors in adjacency.items()
        if branch not in directly_treated and set(neighbors) & directly_treated}
    return branches - directly_treated - indirectly_exposed, indirectly_exposed

first_use = {"North": 3, "West": None, "South": None}
neighbors = {"North": ["West"], "West": ["North"], "South": []}
controls, spillover = clean_controls(first_use, neighbors, 4)
assert controls == {"South"}
assert spillover == {"West"}''',
    'For B branches and E listed neighbor links, the screening rule is O(B + E) expected time and O(B + E) space including input adjacency. Building a defensible exposure map and measuring hidden shared queues are the substantive costs.',
    ['Do not call a branch unexposed only because it lacks the new screen.', 'Do not define control neighbors from a network created after rollout.', 'Do not keep a precise estimate when the clean comparison pool is empty.'],
    ['data-science/branch-month-panel-and-rollout-clock','data-science/cohort-time-difference-in-differences','data-science/event-time-pretrend-and-support-audit','data-science/branch-cluster-bootstrap-for-rollout-effects','data-science/staggered-branch-rollout-audit-project'])

add('branch-cluster-bootstrap-for-rollout-effects',
    'Branch-cluster bootstrap for a rollout contrast',
    'A branch-cluster bootstrap resamples entire branches, preserving each branch’s repeated monthly outcomes while quantifying sampling variation in a specified rollout contrast.', [
    ('Use the assignment unit', 'The triage screen is assigned to branches, not individual cases or months. Outcomes from the same branch share staff, demand and management decisions across time. Resampling branch-month rows independently breaks that dependence and can make an effect look more precise than it is. The code starts from one pre-to-post change per branch, then resamples treated branches and clean comparison branches separately. [[data-science/cohort-time-difference-in-differences|The cohort-time contrast]] defines which two months enter.'),
    ('Keep design groups intact', 'A treated branch remains treated in every resample draw; a control branch remains a control. Resampling within groups maintains the designed group sizes for a simple conditional teaching interval. Each draw averages treated changes, averages control changes, and subtracts them. The fixture has more than one branch per group so variation is visible, although six branches are far too few for confident coverage claims.'),
    ('Read the interval narrowly', 'The percentile endpoints describe variation under this case of branch sampling and frozen pre/post changes. They do not incorporate uncertainty about whether parallel trends holds, whether exposure spilled across branches, or whether adoption was assigned for an unmeasured reason. If a policy was assigned to regions containing several branches, the independent unit may be the region rather than the branch. A branch bootstrap cannot repair a design with only one independent treated region.'),
    ('Beware few-cluster inference', 'Standard cluster-adjusted intervals and simple bootstrap percentiles can perform badly with very few treated clusters. Report the number of treated and comparison clusters prominently and seek an inference method suited to that design. Do not make a significance claim merely because a teaching interval excludes zero. Predefine the target effect, comparison set and inference plan before inspecting the outcome. [[data-science/event-time-pretrend-and-support-audit|Pre-trend checks]] are separate design evidence.'),
    ('Preserve the full pipeline when necessary', 'This routine conditions on calculated branch changes. If the released estimate uses propensity weighting, cohort-time aggregation or sample exclusions learned from data, a full uncertainty analysis must repeat the appropriate steps inside each resample. Document whether interval variability covers only the final contrast or the entire estimation pipeline. [[data-science/staggered-branch-rollout-audit-project|The audit project]] records that boundary.')],
    '''import random

def branch_change_interval(treated_changes, control_changes,
                           repetitions=600, seed=71):
    if len(treated_changes) < 2 or len(control_changes) < 2 or repetitions < 100:
        raise ValueError("insufficient clusters or resamples")
    def contrast(treated, control):
        return sum(treated) / len(treated) - sum(control) / len(control)
    generator = random.Random(seed)
    estimates = sorted(contrast(
        generator.choices(treated_changes, k=len(treated_changes)),
        generator.choices(control_changes, k=len(control_changes)))
        for _ in range(repetitions))
    return contrast(treated_changes, control_changes), (
        estimates[int(.025 * repetitions)], estimates[int(.975 * repetitions)])

treated_branch_changes = [-.06, -.04, -.07]
control_branch_changes = [.01, .00, .02]
effect, interval = branch_change_interval(
    treated_branch_changes, control_branch_changes)
assert abs(effect - (-.06666666666666667)) < 1e-12
assert interval[0] <= effect <= interval[1]''',
    'For B resamples and C branches, direct recomputation costs O(B × C + B log B) time and O(B + C) space. Resampling full branch trajectories adds their monthly rows to each draw. Computational speed does not solve a small number of independent assignment units.',
    ['Do not resample branch-month rows independently.', 'Do not imply that a bootstrap interval validates parallel trends.', 'Do not use a many-cluster approximation when only a few treated clusters exist.'],
    ['data-science/cohort-time-difference-in-differences','data-science/event-time-pretrend-and-support-audit','data-science/spillover-aware-comparison-pool','data-science/staggered-branch-rollout-audit-project'])

add('staggered-branch-rollout-audit-project',
    'Project: audit a staggered support-branch rollout',
    'Build a reproducible policy-review packet for a triage screen introduced to support branches in different months.', [
    ('Freeze the branch-month contract', 'Take the monthly service-breach rate among cases created at each branch as the outcome. Save numerator, denominator, month, branch ID and extraction cutoff, and keep the first actual-use month from a separate rollout log. Define how partial launch months, branch closures and missing reports are handled. [[data-science/branch-month-panel-and-rollout-clock|The panel audit]] checks unique rows and exposure timing before effects are calculated.'),
    ('Estimate supported cohort-time comparisons', 'For each adoption cohort and later month with enough follow-up, use the last pre-adoption month as a baseline and compare with branches not yet treated at the later month. Store which branches entered each comparison and why others were excluded. Do not pool every cohort-time cell before examining its support and business meaning. [[data-science/cohort-time-difference-in-differences|The contrast lesson]] supplies an inspectable arithmetic check.'),
    ('Challenge the design', 'Plot explicit pre-period contrasts by adoption cohort and show their uncertainty and branch counts. Record any rollout anticipation, staffing changes, case-routing changes or metric-definition changes. Build a pre-rollout shared-queue map; exclude indirectly exposed controls in the direct-effect analysis and report how many remain. [[data-science/event-time-pretrend-and-support-audit|Event-time checks]] and [[data-science/spillover-aware-comparison-pool|spillover screens]] are necessary but not proofs.'),
    ('Report branch-level uncertainty', 'Resample or otherwise account for repeated outcomes at the assignment unit. If only a few independent treated regions exist, obtain an inference design suited to that fact rather than relying on a routine branch bootstrap. Show both the effect estimate and the number of independent treated and comparison units. [[data-science/branch-cluster-bootstrap-for-rollout-effects|The bootstrap lesson]] is a teaching calculation for adequate independent clusters.'),
    ('Make the conclusion conditional', 'The review packet names the target branch cohort, comparison dates, treatment definition, parallel-trend rationale, spillover rule, uncertainty method and all unsupported cohort-time cells. The compact gate below catches missing rollout support and missing panel rows. It cannot establish a causal claim by itself. If support or assumptions fail, report descriptive changes instead of an effect estimate.')],
    '''def rollout_review_gate(panel, first_use_month, pre_month,
                            post_month, treated_cohort):
    if not pre_month < treated_cohort <= post_month:
        raise ValueError("invalid study periods")
    treated = {branch for branch, month in first_use_month.items()
               if month == treated_cohort}
    controls = {branch for branch, month in first_use_month.items()
                if month is None or month > post_month}
    if not treated or not controls:
        raise ValueError("no cohort or clean comparison")
    missing = [(branch, month) for branch in treated | controls
               for month in (pre_month, post_month)
               if (branch, month) not in panel]
    if missing:
        raise ValueError("missing required branch-month")
    def mean_change(branches):
        return sum(panel[branch, post_month] - panel[branch, pre_month]
                   for branch in branches) / len(branches)
    return {"treated_branches": len(treated),
            "comparison_branches": len(controls),
            "descriptive_contrast": mean_change(treated) - mean_change(controls)}

adoption = {"North": 3, "East": 3, "West": None, "South": 5}
breaches = {("North", 2): .21, ("North", 4): .16,
            ("East", 2): .19, ("East", 4): .15,
            ("West", 2): .17, ("West", 4): .18,
            ("South", 2): .14, ("South", 4): .15}
review = rollout_review_gate(breaches, adoption, 2, 4, 3)
assert review["treated_branches"] == 2
assert review["comparison_branches"] == 2
assert abs(review["descriptive_contrast"] - (-.055)) < 1e-12''',
    'For B branches, a complete dictionary-backed gate costs O(B) expected time and O(B) space for group and missing-key sets. Full estimation, event-time plots and branch-level inference cost more. No computational check can create a counterfactual when the comparison design is unsupported.',
    ['Do not report a causal effect merely because the descriptive contrast is nonzero.', 'Do not drop exposed comparison branches without reporting the resulting population.', 'Do not hide missing branch-months or a weak cluster count.'],
    ['data-science/branch-month-panel-and-rollout-clock','data-science/cohort-time-difference-in-differences','data-science/event-time-pretrend-and-support-audit','data-science/spillover-aware-comparison-pool','data-science/branch-cluster-bootstrap-for-rollout-effects'])

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
               featured=False, sort_order=13500 + index, status='published', published_at=stamp,
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
module_title = 'Staggered rollout analysis'
if not any(module['title'] == module_title for module in hub['data']['modules']):
    hub['data']['modules'].insert(-1, {'title':module_title,
                                      'summary':'Build branch-month panels, compare adoption cohorts, inspect pre-trends and spillovers, then report branch-level uncertainty.',
                                      'lessons':tutorial_paths})
apply_module = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
if project_path not in apply_module['lessons']:
    apply_module['lessons'].append(project_path)
if '<h2>' + module_title + '</h2>' not in hub['body']:
    hub['body'] += '<h2>' + module_title + '</h2>' + links(tutorial_paths)
    hub['body'] += '<h2>Staggered branch rollout audit</h2>' + links([project_path])
hub['updated_at'] = stamp

project_hub = by_path[project_hub_path]
if project_path not in project_hub['data']['modules'][0]['lessons']:
    project_hub['data']['modules'][0]['lessons'].append(project_path)
if '<h2>Staggered branch rollout audit</h2>' not in project_hub['body']:
    project_hub['body'] += '<h2>Staggered branch rollout audit</h2>' + links([project_path])
project_hub['updated_at'] = stamp

for source, target in [
    ('data-science/dataset-grain-and-join-cardinality', tutorial_paths[0]),
    ('causal-inference/difference-in-differences-and-trends', tutorial_paths[1]),
    ('causal-inference/sensitivity-and-placebo-checks', tutorial_paths[2]),
    ('causal-inference/confounder-graph-and-covariate-timing', tutorial_paths[3]),
    ('data-science/bootstrap-interval-interpretation', tutorial_paths[4]),
    ('causal-inference/lesson-panel-effect-project', project_path),
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
