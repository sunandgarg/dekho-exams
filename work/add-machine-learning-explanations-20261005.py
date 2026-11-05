"""Add original model explanation and feasibility lessons."""
from ml_fixture_writer_20261005 import publish_batch

lessons = []


def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='machine-learning/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))


add('correlated-feature-permutation-audit',
    'Correlated feature permutation audit',
    'Permutation importance measures a fitted model’s score change when one input is disrupted; correlated inputs can mask reliance or create implausible records.', [
    ('Name the inspected quantity', 'A pump follow-up model uses vibration amplitude and a derived vibration severity band. If both encode nearly the same information, shuffling amplitude alone may barely change accuracy because severity remains. A small single-feature importance is not evidence that vibration is irrelevant. [[machine-learning/permutation-importance-on-held-out-data|Held-out permutation importance]] supplies the baseline procedure.'),
    ('Measure groups before individual fields', 'For strongly related fields, permute the group together using the same row mapping. This asks how much predictive performance depends on their combined information. Repeat mappings and show the spread of score changes; one small shuffled sample can give an unstable rank. Use validation rows that were not used to fit the model or choose its settings.'),
    ('Respect real combinations', 'An unrestricted shuffle can pair high vibration with a severity band that means low vibration. The model was never intended to score such combinations. Grouped permutation preserves the two-field relation within donor rows, but it can still pair them with incompatible operating conditions. A conditional shuffle within equipment family may reduce that issue while changing the question to within-family importance.'),
    ('Separate reliance from cause', 'If the model score drops after shuffling a field, the model used information correlated with that field. It does not show that changing the physical pump reading would change failure risk or that technicians should alter that reading. [[causal-inference/confounder-graph-and-covariate-timing|Causal timing]] is a different analysis.'),
    ('Compare policy-relevant slices', 'Run the audit by depot, equipment age and sensor revision. A field can be useful overall yet act as a brittle site marker. Pair explanation changes with held-out error and missingness checks; a compelling chart cannot rescue a model that misses failures. [[machine-learning/explanation-stability-and-fidelity|Stability checks]] bound the claim.')],
    '''inspection_rows = [
    {"vibration": 2.2, "severity": "low", "equipment": "pump-A"},
    {"vibration": 6.8, "severity": "high", "equipment": "pump-A"},
    {"vibration": 3.1, "severity": "low", "equipment": "pump-B"},
    {"vibration": 7.4, "severity": "high", "equipment": "pump-B"},
]

def grouped_swap_within_equipment(rows):
    by_equipment = {}
    for row in rows:
        by_equipment.setdefault(row["equipment"], []).append(row)
    changed = []
    for group in by_equipment.values():
        donors = list(reversed(group))
        for recipient, donor in zip(group, donors):
            changed.append({**recipient, "vibration": donor["vibration"],
                            "severity": donor["severity"]})
    return changed

changed_rows = grouped_swap_within_equipment(inspection_rows)
assert len(changed_rows) == 4
assert all((row["vibration"] >= 5) == (row["severity"] == "high") for row in changed_rows)
assert changed_rows[0]["equipment"] == "pump-A"''',
    'One grouped shuffle is O(N) expected time and O(N) memory for N rows. Repeating it R times and scoring a model costs O(R times model inference over N rows). The example preserves two-field consistency only; a full conditional permutation needs a defensible conditioning scheme and enough support in every stratum.',
    ['Do not interpret a low individual score as proof a correlated signal is unused.', 'Do not claim the shuffle estimates a causal effect.', 'Do not hide synthetic, out-of-support combinations created by the perturbation.'],
    ['machine-learning/partial-dependence-ice-and-support','machine-learning/feasible-counterfactual-review','machine-learning/explanation-stability-and-fidelity','machine-learning/model-explanation-release-project'])


add('partial-dependence-ice-and-support',
    'Partial dependence, ICE curves and support limits',
    'Partial dependence averages a model’s predictions after setting one feature to chosen values; ICE keeps the per-record paths visible, including disagreement hidden by the average.', [
    ('Inspect the model response', 'For a pump follow-up predictor, set inlet temperature to several plausible values and score each held-out pump again. The average of those scores at each value is a partial-dependence curve. An individual conditional expectation curve is the sequence for one pump. Neither is a physical experiment: the model receives edited records, and the real pump may not attain those combinations.'),
    ('Look behind a flat average', 'One equipment type may show rising predicted risk with heat while another shows falling risk because of a learned interaction or data defect. The average can look flat. Plot or tabulate a small set of ICE paths and group summaries before describing a global effect. [[machine-learning/group-error-gaps-and-policy-audit|Group error review]] should accompany the response curve.'),
    ('Mark unsupported feature combinations', 'Temperature and pressure may covary under normal operation. Replacing temperature while leaving pressure fixed can create points absent from training. Restrict the grid to observed support within equipment and operating mode, or flag the unsupported regions explicitly. This changes what the curve can say and may leave few valid records. [[machine-learning/covariate-shift-and-support-overlap|Support overlap]] is the adjacent deployment check.'),
    ('Keep time and units stable', 'Only vary a feature that would be available when the prediction runs. Use the same preprocessing, units and model version used in serving. A curve from a later sensor revision can look smooth while describing the wrong scale. [[machine-learning/prediction-time-feature-availability|Prediction-time availability]] remains necessary even for diagnostic plots.'),
    ('Do not turn response into advice', 'A model score falling at a lower synthetic temperature does not prove cooling the equipment will lower failure risk. Operators need a causal or engineering assessment before acting. [[machine-learning/feasible-counterfactual-review|Counterfactual review]] puts action constraints on what-if scenarios.')],
    '''pump_records = [
    {"asset": "pump-47", "temperature": 54, "pressure": 22},
    {"asset": "pump-62", "temperature": 59, "pressure": 28},
]
temperature_grid = (48, 56, 64)

def illustrative_risk(record):
    return min(1.0, max(0.0, 0.015 * record["temperature"]
                         + 0.006 * record["pressure"] - 0.6))

ice = {record["asset"]: [illustrative_risk({**record, "temperature": setting})
                         for setting in temperature_grid]
       for record in pump_records}
partial_dependence = [sum(ice[asset][index] for asset in ice) / len(ice)
                      for index in range(len(temperature_grid))]
assert len(ice["pump-47"]) == 3
assert all(left < right for left, right in zip(partial_dependence, partial_dependence[1:]))
assert round(partial_dependence[1], 3) == 0.39''',
    'A grid of G values over N records requires O(G times N) model predictions and O(G times N) storage if every ICE path is retained. Streaming a partial-dependence average reduces storage to O(G). The linear scorer here is intentionally simple; support checks and per-slice plots are essential with a fitted nonlinear model.',
    ['Do not call a partial-dependence slope a causal treatment effect.', 'Do not trust an average curve when individual paths disagree.', 'Do not ignore feature combinations absent from the observed operating range.'],
    ['machine-learning/correlated-feature-permutation-audit','machine-learning/feasible-counterfactual-review','machine-learning/explanation-stability-and-fidelity','machine-learning/model-explanation-release-project'])


add('feasible-counterfactual-review',
    'Feasible counterfactual explanations for model decisions',
    'A model counterfactual is an edited input that changes a prediction; a useful operational explanation must also respect immutability, feasible transitions and action authority.', [
    ('Define the decision boundary', 'A pump is routed for manual inspection when its predicted follow-up risk exceeds a fixed threshold. A counterfactual search asks which allowed input changes cross that model threshold. It explains the model’s local behavior under edited inputs. It does not predict what will happen if a technician performs an action, unless that action’s causal effect was separately established.'),
    ('Lock immutable and nonactionable fields', 'Equipment family, depot history and past failure count cannot be edited as suggested repairs. A physically mutable reading may still not be under the technician’s control. Define an allowlist of approved actions, ranges, direction constraints and dependencies from engineering policy before searching. [[causal-inference/estimand-and-counterfactual-unit|Causal estimands]] are needed for claims about actual outcomes.'),
    ('Keep changes coherent', 'Lowering a synthetic temperature while leaving a dependent alarm state unchanged may produce an impossible record. Either update linked features through a validated system model or reject the proposed edit. The code considers only an approved inspection interval and reports an edited score; it makes no claim about true failure prevention. [[machine-learning/partial-dependence-ice-and-support|Support checks]] apply here too.'),
    ('Rank proposals by real cost', 'The numerically smallest edit may require a costly shutdown, while a slightly larger edit may be safe and routine. Score candidates by feasibility, time, parts, authority and uncertainty. Offer an abstention if no approved action crosses the model boundary. Do not fabricate recourse just because the interface expects one.'),
    ('Test explanations across slices', 'Measure the fraction of decisions with a feasible explanation, the size and cost of edits, and whether proposals remain valid after model retraining. Inspect rare equipment and small depots, where the model may be poorly supported. [[machine-learning/explanation-stability-and-fidelity|Stability review]] records that drift.')],
    '''inspection_case = {"asset": "pump-47", "temperature": 64, "pressure": 27,
                   "equipment_family": "centrifugal"}
approved_temperature_settings = (64, 62, 60, 58)
decision_threshold = 0.52

def risk_score(case):
    return min(1.0, max(0.0, 0.013 * case["temperature"]
                         + 0.004 * case["pressure"] - 0.38))

def feasible_model_edit(case, settings, threshold):
    for setting in settings:
        if setting > case["temperature"] or setting < 58:
            continue
        candidate = {**case, "temperature": setting}
        if risk_score(candidate) < threshold:
            return candidate
    return None

proposal = feasible_model_edit(inspection_case, approved_temperature_settings, decision_threshold)
assert risk_score(inspection_case) > decision_threshold
assert proposal is not None and proposal["temperature"] == 60
assert proposal["equipment_family"] == inspection_case["equipment_family"]''',
    'Checking A approved edits costs O(A times model inference) time and O(1) candidate storage as written. Search over many coupled fields can grow combinatorially, so constraints and candidate pruning matter. A feasible model edit is still a diagnostic artifact; verifying real-world action effects requires engineering or causal evidence.',
    ['Do not present an edited model input as a guaranteed intervention outcome.', 'Do not change immutable history or dependent fields inconsistently.', 'Do not force an explanation when no approved edit exists.'],
    ['machine-learning/correlated-feature-permutation-audit','machine-learning/partial-dependence-ice-and-support','machine-learning/explanation-stability-and-fidelity','machine-learning/model-explanation-release-project'])


add('explanation-stability-and-fidelity',
    'Explanation stability and fidelity under model updates',
    'An explanation must be tied to a specific model, input and method version; similar decisions should not acquire contradictory narratives from harmless perturbations.', [
    ('Version the complete explanation path', 'Store the model checkpoint, feature transform, explanation method, reference data and decision threshold with each generated artifact. A new checkpoint can preserve predictions while changing feature attributions. Comparing explanations without those versions creates a false audit trail. [[machine-learning/champion-challenger-shadow-comparison|Champion–challenger review]] offers a model comparison frame.'),
    ('Measure local fidelity', 'A surrogate explanation should reproduce the model’s nearby predictions on valid, in-support perturbations. A clean linear chart fitted on impossible combinations is not a faithful account of the model’s actual operating region. The code checks agreement between a declared model and a simple local surrogate on approved temperature settings; it is an arithmetic test, not a general explanation method.'),
    ('Perturb only benign inputs', 'Repeat an explanation after small measurement noise, stable image crops or different shuffle seeds that should not change the decision. Track top-feature overlap and whether the recommended action changes. A dramatic change may indicate unstable fitting, correlated features or a decision near the threshold. [[machine-learning/correlated-feature-permutation-audit|Grouped perturbation]] helps interpret one cause.'),
    ('Do not reward a plausible story', 'Operators may prefer concise reasons that fit prior beliefs. An explanation audit needs measurable fidelity, feasible actions, consistency and error outcomes, not subjective comfort alone. Keep model error and calibration next to the explanation. [[machine-learning/probability-calibration|Calibration]] asks whether risk numbers deserve action.'),
    ('Separate prediction from action evidence', 'Even a stable and faithful account of what the model uses is not proof that manipulating the named feature improves the real outcome. If the interface proposes a repair, require a separate approved action pathway. [[machine-learning/feasible-counterfactual-review|Feasibility review]] is the minimum filter.')],
    '''approved_temperatures = (58, 60, 62, 64)

def deployed_model(temperature):
    return 0.013 * temperature - 0.272

def local_surrogate(temperature):
    return 0.0131 * temperature - 0.278

def maximum_local_error(settings):
    return max(abs(deployed_model(setting) - local_surrogate(setting))
               for setting in settings)

error = maximum_local_error(approved_temperatures)
assert round(error, 4) == 0.0004
assert error < 0.01
model_versions = {"checkpoint": "round-11", "features": "v4",
                  "explanation": "local-linear-v2", "threshold": 0.52}
assert len(model_versions) == 4''',
    'Evaluating a surrogate on P local points costs O(P) model calls and O(1) storage if errors stream. Repeated explanation runs across records, seeds and model versions can multiply inference cost considerably. A low fidelity error on one tiny range does not establish global reliability or causal meaning.',
    ['Do not compare explanation outputs without model and method versions.', 'Do not call a persuasive narrative faithful without checking predictions.', 'Do not turn a stable attribution into a repair recommendation without action evidence.'],
    ['machine-learning/correlated-feature-permutation-audit','machine-learning/partial-dependence-ice-and-support','machine-learning/feasible-counterfactual-review','machine-learning/model-explanation-release-project'])


add('model-explanation-release-project',
    'Project: release review for pump-risk explanations',
    'An explanation release must state what the output describes, test its stability and support, and prevent model what-if scenarios from masquerading as repair instructions.', [
    ('Freeze the prediction contract', 'A repair depot model routes pumps for manual review. Record the target event, prediction clock, feature and model versions, threshold, affected sites and operational owner. Keep a later-period holdout for model error and explanation checks. The explanation surface is visible only after a prediction exists; it cannot compensate for poor calibration or unsafe false negatives.'),
    ('Compare multiple views', 'Use grouped held-out permutation importance for correlated sensors, ICE paths for approved temperature ranges, and a local model-fidelity check near the displayed case. Each answers a different question. [[machine-learning/correlated-feature-permutation-audit|Permutation]], [[machine-learning/partial-dependence-ice-and-support|ICE]] and [[machine-learning/explanation-stability-and-fidelity|fidelity]] should not be collapsed into one “top reason.”'),
    ('Audit actions separately', 'The user interface may show an approved inspection step, but a synthetic feature edit is not evidence that changing equipment state prevents failure. Test immutability, coupled sensor rules, action authority and no-solution behavior. [[machine-learning/feasible-counterfactual-review|Counterfactual feasibility]] defines those gates.'),
    ('Inspect bad and unstable cases', 'Sample false negatives, rare pump families, new sensor revisions and predictions near the threshold. Ask whether the explanation remains consistent under harmless measurement changes and whether unsupported combinations were scored. Compare before and after retraining with version stamps. A pooled fidelity average may hide a dangerous slice.'),
    ('Make a narrow promotion decision', 'The illustrative gate holds a release that passes local fidelity but contains an unsupported what-if scenario. A passed gate would authorize a controlled shadow review, not a guarantee that users will make better decisions. Keep the prior interface and model version available for rollback.')],
    '''explanation_packet = {
    "model_error_checked_by_site": True,
    "grouped_importance_reviewed": True,
    "ice_support_violations": 1,
    "local_fidelity_error": 0.008,
    "immutable_fields_locked": True,
    "no_solution_path_tested": True,
    "versioned_artifacts_retained": True,
}

def explanation_release_gate(packet):
    holds = []
    if not packet["model_error_checked_by_site"] or packet["local_fidelity_error"] > 0.02:
        holds.append("model error or fidelity")
    if not packet["grouped_importance_reviewed"] or packet["ice_support_violations"]:
        holds.append("unsupported explanation")
    if not all(packet[key] for key in (
        "immutable_fields_locked", "no_solution_path_tested", "versioned_artifacts_retained"
    )):
        holds.append("action or rollback controls")
    return "hold: " + ", ".join(holds) if holds else "eligible for shadow review"

assert explanation_release_gate(explanation_packet) == "hold: unsupported explanation"''',
    'The gate is O(1). Producing its evidence requires held-out model scoring, repeated perturbations, support checks, human review of proposed actions and rollback drills. Explanation generation can add request latency and storage; measure those costs on the actual interface path before promotion.',
    ['Do not publish a model what-if as a verified repair action.', 'Do not approve attractive explanations while predictive error regresses.', 'Do not lose the model, feature, threshold and method versions needed to reproduce an explanation.'],
    ['machine-learning/correlated-feature-permutation-audit','machine-learning/partial-dependence-ice-and-support','machine-learning/feasible-counterfactual-review','machine-learning/explanation-stability-and-fidelity','machine-learning/federated-release-review-project'])


publish_batch(
    lessons,
    module_title='Model explanations and action limits',
    module_summary='Audit correlated features, what-if curves, feasible edits and explanation fidelity before showing reasons to operators.',
    project_heading='Pump-risk explanation release review',
    crosslinks=[
        ('machine-learning/permutation-importance-on-held-out-data', lessons[0]['path']),
        ('machine-learning/group-error-gaps-and-policy-audit', lessons[1]['path']),
        ('causal-inference/estimand-and-counterfactual-unit', lessons[2]['path']),
        ('machine-learning/probability-calibration', lessons[3]['path']),
        ('machine-learning/federated-release-review-project', lessons[4]['path']),
    ],
    sort_start=6100,
)
