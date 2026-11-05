"""Add original Data Science lessons on small rollouts and spillovers."""
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
    'assignment-aware-permutation-test-for-branches',
    'leave-one-branch-out-effect-stability',
    'direct-and-indirect-rollout-exposure-map',
    'spillover-difference-in-differences-contrast',
    'negative-control-and-placebo-rollout-checks',
    'small-rollout-and-spillover-review-project',
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

add('assignment-aware-permutation-test-for-branches',
    'Assignment-aware permutation tests for a few branches',
    'A branch-level randomization test compares an observed treatment contrast with the contrasts possible under the actual assignment rule and a sharp no-effect null.', [
    ('Recover the assignment mechanism', 'Suppose five eligible branches entered a lottery that selected exactly two to receive a triage screen in April. Under a sharp null that the screen changed no branch outcome, the observed before-to-after change for each branch would be the same under every allowed assignment. Enumerate the ten possible treated pairs and calculate the treated-minus-control change for each. The observed pair is one member of that set. If executives selected branches because their breach rates were rising, uniform reassignment is fictional and the resulting number is not an exact randomization p-value. [[data-science/branch-month-panel-and-rollout-clock|The rollout log]] should retain assignment rules.'),
    ('Keep the unit intact', 'The lottery acts on branches. Do not shuffle monthly rows or cases independently; that breaks the treatment unit and repeated-outcome structure. The fixture uses one change per branch after the branch-month panel has been audited. Its observed contrast is the strongest negative contrast among the ten allowed pairs, so a two-sided tail contains one assignment and has probability 0.10. A small assignment space limits attainable p-values regardless of how impressive the raw rate difference looks.'),
    ('State the tested null', 'The code checks a sharp null of no effect on any branch. It does not estimate a confidence interval for an average effect or test a vague claim that the average effect is zero. Under heterogeneous effects those are different questions. A two-sided statistic also needs a prespecified direction or absolute-value rule. Do not adjust the tail after seeing the sign. For staggered or stratified lotteries, enumerate only assignments the design actually allowed, preserving cohort sizes and restrictions.'),
    ('Do not turn observational placebo assignments into a lottery', 'In a nonrandom rollout, recomputing the statistic over other branches can reveal whether the observed branch is unusually extreme, but exchangeability requires an argument. Different baseline trends, branch sizes and rollout priorities can destroy it. Report such a calculation as a sensitivity diagnostic, not design-based exact inference. [[data-science/leave-one-branch-out-effect-stability|Branch influence]] is another diagnostic when a few units drive the result.'),
    ('Tie the output to action', 'The operational packet should show the branch changes, observed contrast, allowed assignment count, null, statistic and smallest attainable tail probability. If there are too few independent assignments to distinguish a policy-relevant effect, say so. No method manufactures information that was never in the rollout. [[data-science/small-rollout-and-spillover-review-project|The review project]] keeps this limitation visible.')],
    '''from itertools import combinations

def assignment_test(branch_changes, treated_branches):
    branches = sorted(branch_changes)
    treated = set(treated_branches)
    if not treated or treated == set(branches) or not treated <= set(branches):
        raise ValueError("invalid treated set")
    def contrast(selected):
        selected = set(selected)
        control = set(branches) - selected
        treated_mean = sum(branch_changes[branch] for branch in selected) / len(selected)
        control_mean = sum(branch_changes[branch] for branch in control) / len(control)
        return treated_mean - control_mean
    observed = contrast(treated)
    possible = [contrast(candidate) for candidate in combinations(branches, len(treated))]
    extreme = sum(abs(value) >= abs(observed) - 1e-12 for value in possible)
    return observed, extreme / len(possible), len(possible)

branch_changes = {"North": -.07, "East": -.05, "West": .01,
                  "South": .00, "Central": .02}
observed, tail_probability, assignments = assignment_test(
    branch_changes, {"North", "East"})
assert assignments == 10
assert abs(observed - (-.07)) < 1e-12
assert abs(tail_probability - .1) < 1e-12''',
    'Enumerating every assignment costs O(C(B,T) × B) time and O(C(B,T)) space for B branches and T treated branches. Larger lotteries require a design-preserving sample of assignments. The limiting factor with few branches is assignment support, not computation.',
    ['Do not call a permutation p-value exact when rollout assignment was not exchangeable.', 'Do not shuffle cases when branches received treatment.', 'Do not confuse a sharp no-effect test with uncertainty for an average effect.'],
    ['data-science/leave-one-branch-out-effect-stability','data-science/direct-and-indirect-rollout-exposure-map','data-science/negative-control-and-placebo-rollout-checks','data-science/small-rollout-and-spillover-review-project'])

add('leave-one-branch-out-effect-stability',
    'Leave-one-branch-out stability for rollout effects',
    'A leave-one-branch-out check recalculates a fixed rollout contrast after removing each entire branch to show whether one assignment unit determines the result.', [
    ('Inspect influence at the treatment unit', 'A breach-rate effect may look stable across thousands of cases while resting on only three treated branches. If one branch had a system outage or a large staffing change, the pooled contrast may reflect that branch. Remove each whole branch in turn, recompute the treated-minus-control mean change, and compare the range with the full contrast. Do not remove isolated monthly rows from a branch; the treatment and correlated measurements belong together. [[data-science/branch-cluster-bootstrap-for-rollout-effects|Branch resampling]] uses the same unit for a different purpose.'),
    ('Keep the estimand fixed as far as possible', 'This teaching check takes already selected treated and comparison branches and one pre-to-post change per branch. Removing a branch changes the finite set being averaged, so the result is an influence diagnostic rather than a new estimate of the original population effect. If a real design uses cohort weights, reweighting, or a comparison set selected from a network, state whether those steps are recomputed after each removal.'),
    ('Read sign changes as a warning', 'The fixture has three treated and three control branches. Its full contrast is negative, and each leave-one-out estimate remains negative. That does not prove causal validity; a common trend violation could move every treated branch together. If the sign flips after deleting one branch, inspect its data lineage, baseline trajectory and assignment rationale before releasing a single summary. Record branch counts beside every estimate.'),
    ('Avoid a false interval label', 'The minimum and maximum leave-one-out estimates are not a confidence interval. They have no automatic coverage guarantee and do not account for shared shocks across branches. With one treated branch, deleting it leaves no treated group, so this diagnostic is unavailable. A few-treated design may need assignment-based inference if a real lottery exists, or a clearly limited descriptive analysis if not. [[data-science/assignment-aware-permutation-test-for-branches|Assignment tests]] explain the boundary.'),
    ('Connect outliers to operations', 'A branch with a sharp change may be a true part of the treatment effect or may have changed the measurement system. Do not delete it merely because it is influential. Compare incident logs, denominator changes and pre-rollout trends, then present the full result and sensitivity together. [[data-science/small-rollout-and-spillover-review-project|The review packet]] records any exclusion rationale.')],
    '''def leave_one_branch_out(treated_changes, control_changes):
    if len(treated_changes) < 2 or len(control_changes) < 2:
        raise ValueError("need at least two branches per group")
    if set(treated_changes) & set(control_changes):
        raise ValueError("branch appears in both groups")
    def contrast(treated, control):
        return (sum(treated.values()) / len(treated) -
                sum(control.values()) / len(control))
    full = contrast(treated_changes, control_changes)
    revisions = {}
    for branch in treated_changes:
        remaining = {key: value for key, value in treated_changes.items()
                     if key != branch}
        revisions[branch] = contrast(remaining, control_changes)
    for branch in control_changes:
        remaining = {key: value for key, value in control_changes.items()
                     if key != branch}
        revisions[branch] = contrast(treated_changes, remaining)
    return full, revisions

treated = {"North": -.06, "East": -.04, "Central": -.07}
comparison = {"West": .01, "South": .00, "Harbor": .02}
full_effect, without_branch = leave_one_branch_out(treated, comparison)
assert abs(full_effect - (-.06666666666666667)) < 1e-12
assert len(without_branch) == 6
assert all(value < 0 for value in without_branch.values())''',
    'For B branches, the direct dictionary-copy implementation is O(B²) time and O(B) transient space per removal, plus O(B) output. Cached group sums reduce calculation to O(B) total time. Diagnostic design and branch-level data review dominate compute cost.',
    ['Do not label the leave-one-out range a confidence interval.', 'Do not drop an influential branch without an evidence-based exclusion rule.', 'Do not interpret stable signs as proof of parallel trends.'],
    ['data-science/assignment-aware-permutation-test-for-branches','data-science/branch-cluster-bootstrap-for-rollout-effects','data-science/negative-control-and-placebo-rollout-checks','data-science/small-rollout-and-spillover-review-project'])

add('direct-and-indirect-rollout-exposure-map',
    'Direct and indirect exposure maps for branch rollouts',
    'An exposure map classifies each branch-period by its own rollout status and the rollout status of branches connected to it before outcomes are compared.', [
    ('Define the interference boundary', 'North receives a triage screen in April. West shares staff and an overflow queue with North, so West may change even without the screen. A map built from pre-rollout staffing and routing records assigns each branch one of three states in a month: direct treatment, indirect exposure through a treated neighbor, or neither. This does not prove the map captures every channel. [[data-science/spillover-aware-comparison-pool|The comparison-pool lesson]] excludes indirectly exposed controls when estimating a direct contrast.'),
    ('Keep the two effects distinct', 'A direct effect compares a branch with the screen against an otherwise comparable branch without the screen under a specified neighbor-exposure condition. An indirect effect compares untreated branches exposed to treated neighbors with untreated branches whose neighbors are also untreated. The populations, assumptions and actions differ. A rise in West’s breach rate caused by overflow would be an indirect effect, not a failure of North’s local workflow. Do not call one pooled treated-versus-untreated number both effects.'),
    ('Freeze the network before assignment', 'The example uses an adjacency list created from pre-rollout operations. If a new queue route appears after the screen launches, using that later network to choose controls can condition on a consequence of treatment. Retain the pre-period map and separately audit actual post-rollout routing. A branch with several treated neighbors may need an exposure intensity rather than a binary flag; choose that mapping before inspecting outcomes.'),
    ('Verify coverage and changes', 'For each month, count direct, indirect and unexposed branches. Every branch should occupy exactly one class. If all possible controls become indirectly exposed, a direct-effect comparison against unexposed branches has no support. A branch can move from unexposed to indirect when its neighbor adopts; its own adoption later moves it to direct. [[data-science/spillover-difference-in-differences-contrast|The spillover contrast]] uses the untreated categories only.'),
    ('Do not assume a map identifies causality', 'Indirect exposure may be correlated with branch size, geography or staffing. Estimation needs a comparison trend argument or an assignment design, plus a stable outcome definition and no spillovers beyond the mapped boundary. Shared region shocks may make branches dependent even if the adjacency list has no edge. Report the map’s construction date and units with uncertain connections.')],
    '''def rollout_exposure(first_use_month, neighbors, month):
    if month <= 0 or set(first_use_month) != set(neighbors):
        raise ValueError("invalid month or incomplete network")
    branches = set(first_use_month)
    if any(branch in linked or not set(linked) <= branches
           for branch, linked in neighbors.items()):
        raise ValueError("invalid neighbor list")
    treated = {branch for branch, first_use in first_use_month.items()
               if first_use is not None and first_use <= month}
    exposure = {}
    for branch, linked in neighbors.items():
        if branch in treated:
            exposure[branch] = "direct"
        elif set(linked) & treated:
            exposure[branch] = "indirect"
        else:
            exposure[branch] = "unexposed"
    return exposure

first_use = {"North": 4, "West": None, "South": None, "Harbor": 6}
network = {"North": ["West"], "West": ["North"],
           "South": [], "Harbor": []}
states = rollout_exposure(first_use, network, 5)
assert states == {"North": "direct", "West": "indirect",
                  "South": "unexposed", "Harbor": "unexposed"}''',
    'For B branches and E neighbor links, classification costs O(B + E) expected time and O(B) output space beyond the input map. A large routing network needs versioned adjacency storage and an audit of cross-boundary connections.',
    ['Do not infer that a branch is unexposed only from its own feature flag.', 'Do not build the primary comparison network from post-rollout traffic.', 'Do not combine direct and indirect effects without naming a new estimand.'],
    ['data-science/spillover-aware-comparison-pool','data-science/spillover-difference-in-differences-contrast','data-science/negative-control-and-placebo-rollout-checks','data-science/small-rollout-and-spillover-review-project'])

add('spillover-difference-in-differences-contrast',
    'A spillover difference-in-differences contrast',
    'A spillover contrast compares outcome changes for untreated branches that became indirectly exposed with changes for untreated branches that remained unexposed.', [
    ('Set a narrow target', 'For April through June, ask whether untreated branches sharing a queue with newly treated North changed their breach rate differently from untreated branches outside that queue network. This is a contrast about indirect exposure among branches without the screen. It is not the effect of giving North the screen. [[data-science/direct-and-indirect-rollout-exposure-map|The exposure map]] determines groups using pre-rollout connections.'),
    ('Use the same pre and post windows', 'For each branch, calculate June minus March breach rate, then subtract the mean change among still-unexposed branches from the mean change among indirectly exposed branches. In the fixture, exposed branches rise by 0.04 on average while unexposed branches rise by 0.005, giving a descriptive spillover contrast of 0.035. A positive value means a larger increase in service breaches for the exposed group under this outcome definition.'),
    ('Defend the counterfactual', 'A causal reading requires that the groups would have had comparable untreated changes absent neighboring rollout, along with no anticipation and no spillovers into the supposedly unexposed group. The exposed branches may sit near a demand surge or receive staffing changes at the same time. Examine pre-rollout trends, routing records and stable denominators. [[data-science/event-time-pretrend-and-support-audit|Pre-trend auditing]] cannot prove an unobserved post-rollout trend but may reveal a clear mismatch.'),
    ('Keep exposure separate from own treatment', 'A branch that adopts the screen during the post period is not part of either untreated group. Exclude it or use a richer design that models both paths. The code accepts group membership already determined for the study window and rejects overlap, but it does not reconstruct monthly exposure or adjust for changing membership. If West becomes indirectly exposed only halfway through April, a whole-quarter label hides timing. [[data-science/branch-month-panel-and-rollout-clock|The panel clock]] handles transitions explicitly.'),
    ('Interpret support honestly', 'Show branch counts and case denominators for each group, not only the rate contrast. If there is one exposed branch and one unexposed branch, the statistic is inspectable but uncertainty and generalization are weak. If all branches share one network, consider a design at the network level or a different estimand. [[data-science/small-rollout-and-spillover-review-project|The review project]] treats empty support as a stop condition.')],
    '''def untreated_spillover_change(branch_rates, indirectly_exposed,
                                     unexposed, before_month, after_month):
    exposed = set(indirectly_exposed)
    comparison = set(unexposed)
    if not exposed or not comparison or exposed & comparison:
        raise ValueError("unsupported exposure groups")
    if before_month >= after_month:
        raise ValueError("invalid comparison window")
    def average_change(branches):
        return sum(branch_rates[(branch, after_month)] -
                   branch_rates[(branch, before_month)]
                   for branch in branches) / len(branches)
    return average_change(exposed) - average_change(comparison)

rates = {("West", 3): .16, ("West", 6): .21,
         ("East", 3): .18, ("East", 6): .21,
         ("South", 3): .15, ("South", 6): .16,
         ("Harbor", 3): .14, ("Harbor", 6): .14}
spillover_change = untreated_spillover_change(
    rates, {"West", "East"}, {"South", "Harbor"}, 3, 6)
assert abs(spillover_change - .035) < 1e-12''',
    'For E indirectly exposed and C unexposed branches, dictionary-backed calculation costs O(E + C) expected time and O(E + C) space for group sets. Rebuilding exposure from a network adds its own graph scan. The main constraint is credible comparison support.',
    ['Do not include directly treated branches in either untreated group.', 'Do not call the contrast causal without a defended no-spillover counterfactual trend.', 'Do not ignore partial-period exposure or an empty comparison group.'],
    ['data-science/direct-and-indirect-rollout-exposure-map','data-science/spillover-aware-comparison-pool','data-science/event-time-pretrend-and-support-audit','data-science/negative-control-and-placebo-rollout-checks','data-science/small-rollout-and-spillover-review-project'])

add('negative-control-and-placebo-rollout-checks',
    'Negative-control outcomes and placebo rollout checks',
    'A falsification check repeats a prespecified comparison where the intervention should have no effect, looking for evidence of a broken design or measurement process.', [
    ('Choose a control outcome for a reason', 'A support triage screen may affect breach rate but should not change an archived hardware inventory count recorded through a separate system. If both jump at rollout, an organization-wide reporting change or another concurrent policy may be present. An outcome is a valid negative control only when there is a defensible reason the triage screen cannot affect it, while the suspected bias would affect both. Do not choose an arbitrary unrelated metric merely because it returns a reassuring zero.'),
    ('Apply the same contrast', 'The fixture computes a two-group, two-period difference-in-differences contrast for the breach rate and for a separately specified control outcome. The breach contrast is negative; the negative-control contrast is zero. This is a calculation check. A zero on one small control metric does not prove parallel trends, no spillovers or accurate treatment dates. [[data-science/cohort-time-difference-in-differences|The rollout contrast]] explains the group-time target.'),
    ('Placebo dates need clean pre-periods', 'A second test can pretend rollout happened earlier, using only periods before any actual adoption or anticipation. A nonzero placebo contrast may reveal preexisting divergence, but the chosen fake date and outcome window must be fixed before searching many alternatives. Using a period when staff were already training on the new screen is not a clean placebo. [[data-science/event-time-pretrend-and-support-audit|Event-time leads]] offer a related diagnostic with support counts.'),
    ('Interpret a failed check carefully', 'A negative-control effect may mean confounding, a measurement change, an unexpected real pathway or random variation. Audit the control metric’s data pipeline and outcome eligibility before declaring the primary result invalid. Conversely, repeated null placebo findings do not supply the missing counterfactual; they eliminate some specific failure stories. Keep all planned tests in the review packet, including those that do not flatter the effect estimate.'),
    ('Keep scope and uncertainty aligned', 'With few branches, a control-outcome estimate near zero can still have a wide interval. Show group counts, actual contrasts and data lineage rather than turning a nonsignificant p-value into evidence of no bias. If branches share routing, a supposedly unaffected outcome could move through spillovers. [[data-science/direct-and-indirect-rollout-exposure-map|The exposure map]] helps identify that possibility.')],
    '''def two_group_change(treated_before, treated_after,
                         control_before, control_after):
    return ((treated_after - treated_before) -
            (control_after - control_before))

service_breach = two_group_change(.20, .13, .18, .17)
hardware_inventory = two_group_change(.30, .31, .29, .30)
assert abs(service_breach - (-.06)) < 1e-12
assert abs(hardware_inventory) < 1e-12

planned_checks = {"service_breach": service_breach,
                  "hardware_inventory_control": hardware_inventory}
assert set(planned_checks) == {"service_breach", "hardware_inventory_control"}''',
    'Each two-period contrast is O(1) time and space after cohort rates are computed. With M planned outcomes, calculation is O(M); data lineage and dependence-aware uncertainty are the expensive parts. Searching many controls or dates increases false reassurance unless the plan is frozen.',
    ['Do not pick a control outcome solely because its estimated effect is zero.', 'Do not use post-training periods as a pre-rollout placebo.', 'Do not interpret a nonsignificant falsification test as proof of validity.'],
    ['data-science/assignment-aware-permutation-test-for-branches','data-science/leave-one-branch-out-effect-stability','data-science/direct-and-indirect-rollout-exposure-map','data-science/spillover-difference-in-differences-contrast','data-science/small-rollout-and-spillover-review-project'])

add('small-rollout-and-spillover-review-project',
    'Project: review a small branch rollout with spillovers',
    'Produce a policy packet that distinguishes direct rollout effects, indirect exposure, assignment-based evidence and design diagnostics.', [
    ('Reconstruct the rollout decision', 'Start with branch-month breach numerator and denominator, first-use date, eligible branch list and the actual rule that selected rollout branches. If a lottery selected two of five eligible branches, preserve its assignment restrictions. If management selected branches by need, record that instead and do not present a uniform permutation test as exact inference. [[data-science/assignment-aware-permutation-test-for-branches|Assignment-aware testing]] has a narrow design requirement.'),
    ('Map exposure before looking at outcomes', 'Build a pre-rollout network from shared queues and staffing. Classify every branch-month as directly treated, indirectly exposed or unexposed. Report uncertain connections and how a broader map changes group counts. Estimate a direct contrast using clean controls and a separate indirect contrast among untreated branches only. [[data-science/direct-and-indirect-rollout-exposure-map|Exposure classes]] and [[data-science/spillover-difference-in-differences-contrast|the spillover contrast]] answer different questions.'),
    ('Test whether one branch drives the story', 'Recompute the primary contrast after omitting each assignment unit, retain all planned negative controls and pre-rollout placebo windows, and show the treated and comparison branch counts. A leave-one-out range is a diagnostic, not a confidence interval. A failed negative control is a reason to investigate, not a command to delete that metric. [[data-science/leave-one-branch-out-effect-stability|Influence checks]] and [[data-science/negative-control-and-placebo-rollout-checks|falsification checks]] belong beside the main result.'),
    ('State the inference limit', 'When a genuine restricted lottery exists, calculate the randomization distribution under its sharp no-effect null. With observational selection or few independent regions, use an inference method suited to the assignment structure and avoid automatic significance claims from ordinary branch bootstraps. Record the smallest attainable randomization tail probability where relevant. [[data-science/branch-cluster-bootstrap-for-rollout-effects|Cluster uncertainty]] does not fix a weak assignment design.'),
    ('Make publication conditional', 'The release packet names the target population, periods, adoption groups, exposure rule, comparison support, trend evidence, falsification outcomes, branch influence and uncertainty scope. The gate below checks unique branches, disjoint exposure categories and at least one clean comparison. It does not prove causal identification. If the map leaves no unexposed branch, state that the direct comparison is unsupported.')],
    '''def small_rollout_gate(first_use_month, exposure_status, evaluation_month):
    if evaluation_month <= 0 or set(first_use_month) != set(exposure_status):
        raise ValueError("branch coverage mismatch")
    valid = {"direct", "indirect", "unexposed"}
    if any(status not in valid for status in exposure_status.values()):
        raise ValueError("unknown exposure status")
    for branch, first_use in first_use_month.items():
        adopted = first_use is not None and first_use <= evaluation_month
        if adopted != (exposure_status[branch] == "direct"):
            raise ValueError("exposure contradicts adoption month")
    direct = {branch for branch, status in exposure_status.items()
              if status == "direct"}
    indirect = {branch for branch, status in exposure_status.items()
                if status == "indirect"}
    unexposed = {branch for branch, status in exposure_status.items()
                 if status == "unexposed"}
    if not direct or not unexposed:
        raise ValueError("unsupported direct comparison")
    return {"direct": len(direct), "indirect": len(indirect),
            "unexposed": len(unexposed),
            "indirect_comparison_ready": bool(indirect)}

adoption = {"North": 4, "West": None, "South": None, "Harbor": None}
exposure = {"North": "direct", "West": "indirect",
            "South": "unexposed", "Harbor": "unexposed"}
review = small_rollout_gate(adoption, exposure, 5)
assert review == {"direct": 1, "indirect": 1,
                  "unexposed": 2, "indirect_comparison_ready": True}''',
    'The gate scans B branches in O(B) expected time and O(B) space for classification sets. Full network reconstruction, trend comparison and design-specific inference add separate costs. A fast gate is not a causal approval certificate.',
    ['Do not represent a management-selected rollout as a randomized lottery.', 'Do not merge indirect and unexposed branches into one control label.', 'Do not publish a causal effect if the comparison set or assignment assumptions are unsupported.'],
    ['data-science/assignment-aware-permutation-test-for-branches','data-science/leave-one-branch-out-effect-stability','data-science/direct-and-indirect-rollout-exposure-map','data-science/spillover-difference-in-differences-contrast','data-science/negative-control-and-placebo-rollout-checks'])

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
               featured=False, sort_order=13600 + index, status='published', published_at=stamp,
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
module_title = 'Small rollout inference and spillovers'
if not any(module['title'] == module_title for module in hub['data']['modules']):
    hub['data']['modules'].insert(-1, {'title':module_title,
                                      'summary':'Inspect assignment support, influential branches and indirect exposure before claiming a rollout effect.',
                                      'lessons':tutorial_paths})
apply_module = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
if project_path not in apply_module['lessons']:
    apply_module['lessons'].append(project_path)
if '<h2>' + module_title + '</h2>' not in hub['body']:
    hub['body'] += '<h2>' + module_title + '</h2>' + links(tutorial_paths)
    hub['body'] += '<h2>Small rollout and spillover review</h2>' + links([project_path])
hub['updated_at'] = stamp

project_hub = by_path[project_hub_path]
if project_path not in project_hub['data']['modules'][0]['lessons']:
    project_hub['data']['modules'][0]['lessons'].append(project_path)
if '<h2>Small rollout and spillover review</h2>' not in project_hub['body']:
    project_hub['body'] += '<h2>Small rollout and spillover review</h2>' + links([project_path])
project_hub['updated_at'] = stamp

for source, target in [
    ('data-science/branch-cluster-bootstrap-for-rollout-effects', tutorial_paths[0]),
    ('data-science/cohort-time-difference-in-differences', tutorial_paths[1]),
    ('data-science/spillover-aware-comparison-pool', tutorial_paths[2]),
    ('data-science/direct-and-indirect-rollout-exposure-map', tutorial_paths[3]),
    ('causal-inference/sensitivity-and-placebo-checks', tutorial_paths[4]),
    ('data-science/staggered-branch-rollout-audit-project', project_path),
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
